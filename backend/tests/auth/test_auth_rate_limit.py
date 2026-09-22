import hashlib

import pytest
from fastapi import Request
from redis.asyncio import Redis

from src.auth.config import AuthRateLimitSettings
from src.auth.rate_limit import (
    create_rate_limit_dependency,
    enforce_rate_limits,
    get_client_identifier,
)
from src.common.errors import RateLimitedError


def test_client_identifier_hashes_request_address(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    request = Request({"type": "http", "client": ("203.0.113.10", 1234)})

    assert get_client_identifier(request) == hashlib.sha256(b"203.0.113.10").hexdigest()


def test_client_identifier_uses_trusted_proxy_header(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")
    request = Request(
        {
            "type": "http",
            "client": ("198.51.100.20", 1234),
            "headers": [(b"x-real-ip", b"203.0.113.10")],
        }
    )

    assert get_client_identifier(request) == hashlib.sha256(b"203.0.113.10").hexdigest()


def test_client_identifier_ignores_untrusted_proxy_header(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    request = Request(
        {
            "type": "http",
            "client": ("198.51.100.20", 12345),
            "headers": [(b"x-real-ip", b"203.0.113.10")],
        }
    )

    assert get_client_identifier(request) == hashlib.sha256(b"198.51.100.20").hexdigest()


async def test_dependency_rejects_request_above_limit(mocker):
    cache = mocker.Mock(spec=Redis)
    cache.register_script.return_value = mocker.AsyncMock(return_value=[0, 17])
    dependency = create_rate_limit_dependency(
        "auth-test",
        lambda: AuthRateLimitSettings(requests=2, window_seconds=60),
    )
    request = Request({"type": "http", "client": ("203.0.113.10", 1234)})

    with pytest.raises(RateLimitedError) as exc_info:
        await dependency(request, cache)

    assert exc_info.value.headers == {"Retry-After": "17"}


async def test_enforce_rate_limits_ignores_untrusted_proxy_header(
    mock_token_service,
    monkeypatch,
):
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    request = Request(
        {
            "type": "http",
            "headers": [(b"x-real-ip", b"203.0.113.10")],
            "client": ("198.51.100.20", 12345),
        }
    )

    await enforce_rate_limits(mock_token_service, request, "login", ip_limit=10)

    mock_token_service.enforce_rate_limit.assert_awaited_once_with(
        "login:ip", "198.51.100.20", 10, 300
    )


async def test_enforce_rate_limits_uses_trusted_proxy_header(
    mock_token_service,
    monkeypatch,
):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")
    request = Request(
        {
            "type": "http",
            "headers": [(b"x-real-ip", b"203.0.113.10")],
            "client": ("198.51.100.20", 12345),
        }
    )

    await enforce_rate_limits(mock_token_service, request, "login", ip_limit=10)

    mock_token_service.enforce_rate_limit.assert_awaited_once_with(
        "login:ip", "203.0.113.10", 10, 300
    )
