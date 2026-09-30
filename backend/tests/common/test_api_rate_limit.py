import hashlib

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.auth.utils import create_access_token
from src.common.api_rate_limit import (
    ApiRateLimitMiddleware,
    ApiRateLimitSettings,
    RateLimitPolicy,
    get_api_rate_limit_settings,
)


def settings(*, enabled: bool = True) -> ApiRateLimitSettings:
    return ApiRateLimitSettings(
        enabled=enabled,
        read=RateLimitPolicy(requests=240, window_seconds=60),
        write=RateLimitPolicy(requests=60, window_seconds=60),
        export=RateLimitPolicy(requests=10, window_seconds=60),
    )


def make_app(cache: Redis, configured: ApiRateLimitSettings | None = None) -> FastAPI:
    app = FastAPI()

    @app.get("/api/items")
    async def list_items() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/items")
    async def create_item() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/api/items/export")
    async def export_items() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/health")
    async def health() -> dict[str, bool]:
        return {"ok": True}

    app.add_middleware(
        ApiRateLimitMiddleware,
        cache=cache,
        settings_provider=lambda: configured or settings(),
    )
    return app


async def request(app: FastAPI, method: str, path: str, **kwargs):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        return await client.request(method, path, **kwargs)


def mock_cache(mocker, responses: list[list[int]]) -> tuple[Redis, object]:
    cache = mocker.Mock(spec=Redis)
    script = mocker.AsyncMock(side_effect=responses)
    cache.register_script.return_value = script
    return cache, script


async def test_read_request_consumes_actor_limit(mocker):
    cache, script = mock_cache(mocker, [[1, 0]])

    response = await request(make_app(cache), "GET", "/api/items")

    assert response.status_code == 200
    assert script.await_count == 1
    assert script.await_args_list[0].kwargs["args"] == [60, 240]
    assert script.await_args_list[0].kwargs["keys"][0].startswith("rate-limit:api-read:sliding:ip:")


async def test_write_request_uses_write_policy(mocker):
    cache, script = mock_cache(mocker, [[1, 0]])

    response = await request(make_app(cache), "POST", "/api/items")

    assert response.status_code == 200
    assert script.await_args_list[0].kwargs["args"] == [60, 60]
    assert "rate-limit:api-write:sliding:" in script.await_args_list[0].kwargs["keys"][0]


async def test_export_request_uses_stricter_export_policy(mocker):
    cache, script = mock_cache(mocker, [[1, 0]])

    response = await request(make_app(cache), "GET", "/api/items/export")

    assert response.status_code == 200
    assert script.await_args_list[0].kwargs["args"] == [60, 10]
    assert "rate-limit:api-export:sliding:" in script.await_args_list[0].kwargs["keys"][0]


async def test_authenticated_requests_are_limited_by_verified_user(mocker, monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-with-at-least-32-characters",  # gitleaks:allow
    )
    cache, script = mock_cache(mocker, [[1, 0]])
    subject = "9a6c77db-5daa-43b1-81fd-e9017716d50d"
    token = create_access_token(subject)

    response = await request(
        make_app(cache),
        "GET",
        "/api/items",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    expected_actor = hashlib.sha256(subject.encode()).hexdigest()
    assert script.await_args_list[0].kwargs["keys"] == [
        f"rate-limit:api-read:sliding:user:{expected_actor}"
    ]


async def test_users_sharing_an_ip_have_independent_limits(mocker, monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-with-at-least-32-characters",  # gitleaks:allow
    )
    cache, script = mock_cache(mocker, [[1, 0], [1, 0]])
    app = make_app(cache)

    for subject in (
        "9a6c77db-5daa-43b1-81fd-e9017716d50d",
        "489c620a-d33f-4658-9a95-55b71c524e30",
    ):
        response = await request(
            app,
            "GET",
            "/api/items",
            headers={"Authorization": f"Bearer {create_access_token(subject)}"},
        )
        assert response.status_code == 200

    first_key = script.await_args_list[0].kwargs["keys"][0]
    second_key = script.await_args_list[1].kwargs["keys"][0]
    assert first_key != second_key
    assert ":user:" in first_key
    assert ":user:" in second_key


async def test_limited_request_returns_common_error_and_retry_after(mocker):
    cache, _script = mock_cache(mocker, [[0, 17]])

    response = await request(make_app(cache), "GET", "/api/items")

    assert response.status_code == 429
    assert response.headers["retry-after"] == "17"
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "error_code": "RATE_LIMITED",
        "detail": "Too many requests. Try again later.",
    }


@pytest.mark.parametrize(
    ("method", "path"),
    [("GET", "/health"), ("OPTIONS", "/api/items")],
)
async def test_health_and_preflight_are_not_limited(mocker, method, path):
    cache, script = mock_cache(mocker, [])

    response = await request(make_app(cache), method, path)

    assert response.status_code in {200, 405}
    script.assert_not_awaited()


async def test_disabled_limiter_does_not_touch_redis(mocker):
    cache, script = mock_cache(mocker, [])

    response = await request(make_app(cache, settings(enabled=False)), "GET", "/api/items")

    assert response.status_code == 200
    script.assert_not_awaited()


async def test_general_api_fails_open_when_redis_is_unavailable(mocker):
    cache, script = mock_cache(mocker, [])
    script.side_effect = RedisError("unavailable")

    response = await request(make_app(cache), "GET", "/api/items")

    assert response.status_code == 200


def test_api_rate_limit_defaults(monkeypatch):
    for name in (
        "API_RATE_LIMIT_ENABLED",
        "API_RATE_LIMIT_READ_REQUESTS",
        "API_RATE_LIMIT_WRITE_REQUESTS",
        "API_RATE_LIMIT_EXPORT_REQUESTS",
    ):
        monkeypatch.delenv(name, raising=False)

    configured = get_api_rate_limit_settings()

    assert configured.enabled is True
    assert configured.read.requests == 240
    assert configured.write.requests == 60
    assert configured.export.requests == 10


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("API_RATE_LIMIT_ENABLED", "sometimes"),
        ("API_RATE_LIMIT_READ_REQUESTS", "0"),
        ("API_RATE_LIMIT_WRITE_WINDOW_SECONDS", "invalid"),
    ],
)
def test_api_rate_limit_rejects_invalid_configuration(monkeypatch, name, value):
    monkeypatch.setenv(name, value)

    with pytest.raises(RuntimeError, match=name):
        get_api_rate_limit_settings()
