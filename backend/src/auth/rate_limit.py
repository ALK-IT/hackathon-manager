import hashlib
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from src.auth.client import get_client_ip
from src.auth.config import (
    RATE_LIMIT_WINDOW,
    AuthRateLimitSettings,
    get_login_rate_limit_settings,
    get_refresh_rate_limit_settings,
    get_register_rate_limit_settings,
    get_verify_email_rate_limit_settings,
)
from src.auth.exceptions import RateLimitError
from src.auth.service import TokenService
from src.cache import get_cache
from src.common.errors import RateLimitedError
from src.common.rate_limit import SlidingWindowRateLimiter

SettingsProvider = Callable[[], AuthRateLimitSettings]
RateLimitDependency = Callable[[Request, Redis], Awaitable[None]]


def get_client_identifier(request: Request) -> str:
    client_ip = get_client_ip(request)
    return hashlib.sha256(client_ip.encode("utf-8")).hexdigest()


async def enforce_rate_limits(
    token_service: TokenService,
    request: Request,
    scope: str,
    *,
    identifier: str | None = None,
    ip_limit: int | None = None,
    identifier_limit: int | None = None,
) -> None:
    try:
        if ip_limit is not None:
            await token_service.enforce_rate_limit(
                f"{scope}:ip",
                get_client_ip(request),
                ip_limit,
                RATE_LIMIT_WINDOW,
            )
        if identifier is not None and identifier_limit is not None:
            await token_service.enforce_rate_limit(
                f"{scope}:identifier",
                identifier,
                identifier_limit,
                RATE_LIMIT_WINDOW,
            )
    except RateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again later.",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc


def create_rate_limit_dependency(
    namespace: str,
    settings_provider: SettingsProvider,
) -> RateLimitDependency:
    async def enforce_rate_limit(
        request: Request,
        cache: Annotated[Redis, Depends(get_cache)],
    ) -> None:
        settings = settings_provider()
        limiter = SlidingWindowRateLimiter(
            cache=cache,
            namespace=namespace,
            limit=settings.requests,
            window_seconds=settings.window_seconds,
        )
        allowed, retry_after = await limiter.consume_with_retry_after(
            get_client_identifier(request)
        )
        if not allowed:
            raise RateLimitedError(retry_after)

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
