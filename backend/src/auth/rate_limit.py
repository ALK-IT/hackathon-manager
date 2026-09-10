import hashlib
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis

from src.auth.config import (
    AuthRateLimitSettings,
    get_login_rate_limit_settings,
    get_refresh_rate_limit_settings,
    get_register_rate_limit_settings,
    get_trust_proxy_headers,
    get_verify_email_rate_limit_settings,
)
from src.cache import get_cache
from src.common.errors import RateLimitedError
from src.common.rate_limit import FixedWindowRateLimiter

SettingsProvider = Callable[[], AuthRateLimitSettings]
RateLimitDependency = Callable[[Request, Redis], Awaitable[None]]


def get_client_identifier(request: Request) -> str:
    client_ip = request.client.host if request.client else "unknown-client"
    if get_trust_proxy_headers():
        proxy_ip = request.headers.get("X-Real-IP", "").strip()
        if proxy_ip:
            client_ip = proxy_ip
    return hashlib.sha256(client_ip.encode("utf-8")).hexdigest()


def create_rate_limit_dependency(
    namespace: str,
    settings_provider: SettingsProvider,
) -> RateLimitDependency:
    async def enforce_rate_limit(
        request: Request,
        cache: Annotated[Redis, Depends(get_cache)],
    ) -> None:
        settings = settings_provider()
        limiter = FixedWindowRateLimiter(
            cache=cache,
            namespace=namespace,
            limit=settings.requests,
            window_seconds=settings.window_seconds,
        )
        if not await limiter.consume(get_client_identifier(request)):
            raise RateLimitedError(settings.window_seconds)

    return enforce_rate_limit


enforce_login_rate_limit = create_rate_limit_dependency(
    "auth-login",
    get_login_rate_limit_settings,
)
enforce_register_rate_limit = create_rate_limit_dependency(
    "auth-register",
    get_register_rate_limit_settings,
)
enforce_refresh_rate_limit = create_rate_limit_dependency(
    "auth-refresh",
    get_refresh_rate_limit_settings,
)
enforce_verify_email_rate_limit = create_rate_limit_dependency(
    "auth-verify-email",
    get_verify_email_rate_limit_settings,
)
