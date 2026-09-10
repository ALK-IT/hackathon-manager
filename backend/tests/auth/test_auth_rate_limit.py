import hashlib

import pytest
from fastapi import Request
from redis.asyncio import Redis

from src.auth.config import AuthRateLimitSettings
from src.auth.rate_limit import create_rate_limit_dependency, get_client_identifier
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


async def test_dependency_rejects_request_above_limit(mocker):
    cache = mocker.Mock(spec=Redis)
    cache.set = mocker.AsyncMock(return_value=False)
    cache.incr = mocker.AsyncMock(return_value=3)
    dependency = create_rate_limit_dependency(
        "auth-test",
        lambda: AuthRateLimitSettings(requests=2, window_seconds=60),
    )
    request = Request({"type": "http", "client": ("203.0.113.10", 1234)})

    with pytest.raises(RateLimitedError) as exc_info:
        await dependency(request, cache)

    assert exc_info.value.headers == {"Retry-After": "60"}
