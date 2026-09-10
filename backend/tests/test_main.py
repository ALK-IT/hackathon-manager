from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from src.cache import get_cache
from src.database import get_session
from src.main import app, lifespan

client = TestClient(app)


def call_health(
    *,
    database_error: Exception | None = None,
    redis_error: Exception | None = None,
):
    session = Mock()
    session.execute = AsyncMock(side_effect=database_error)
    cache = Mock()
    cache.ping = AsyncMock(side_effect=redis_error, return_value=True)
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_cache] = lambda: cache
    try:
        response = client.get("/health")
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_cache, None)
    return response, session, cache


def test_health_checks_database_and_redis() -> None:
    response, session, cache = call_health()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "components": {"database": "ok", "redis": "ok"},
    }
    assert str(session.execute.await_args.args[0]) == "SELECT 1"
    cache.ping.assert_awaited_once_with()


def test_health_returns_503_when_database_is_unavailable() -> None:
    response, _, _ = call_health(database_error=SQLAlchemyError("database unavailable"))

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "components": {"database": "unavailable", "redis": "ok"},
    }


def test_health_returns_503_when_redis_is_unavailable() -> None:
    response, _, _ = call_health(redis_error=RedisError("redis unavailable"))

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "components": {"database": "ok", "redis": "unavailable"},
    }


def test_hello_route_is_removed() -> None:
    assert client.get("/api/hello").status_code == 404


def test_expected_routes_are_registered() -> None:
    paths = set(app.openapi()["paths"])

    assert {
        "/health",
        "/api/hackathons",
        "/api/auth/register",
        "/api/auth/login",
        "/api/auth/refresh",
        "/api/auth/logout",
        "/api/auth/me",
    }.issubset(paths)
    assert "/api/hello" not in paths


async def test_lifespan_validates_resource_configuration(monkeypatch) -> None:
    validation_calls = []
    monkeypatch.setattr("src.main.validate_configuration", lambda: None)
    monkeypatch.setattr(
        "src.main.validate_resource_configuration",
        lambda: validation_calls.append(True),
    )

    async with lifespan(app):
        pass

    assert validation_calls == [True]
