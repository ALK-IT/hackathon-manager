import hashlib
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Request
from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from src.auth.client import get_client_ip
from src.auth.exceptions import InvalidAccessTokenError
from src.auth.utils import decode_access_token_payload
from src.common.errors import ErrorCode
from src.common.rate_limit import SlidingWindowRateLimiter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitPolicy:
    requests: int
    window_seconds: int


@dataclass(frozen=True)
class ApiRateLimitSettings:
    enabled: bool
    read: RateLimitPolicy
    write: RateLimitPolicy
    export: RateLimitPolicy


def _positive_integer(name: str, default: int) -> int:
    raw_value = os.environ.get(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


def _boolean(name: str, default: bool) -> bool:
    raw_value = os.environ.get(name, str(default)).strip().lower()
    if raw_value in {"1", "true", "yes"}:
        return True
    if raw_value in {"0", "false", "no"}:
        return False
    raise RuntimeError(f"{name} must be true or false")


def _policy(prefix: str, default_requests: int, default_window: int = 60) -> RateLimitPolicy:
    return RateLimitPolicy(
        requests=_positive_integer(f"API_RATE_LIMIT_{prefix}_REQUESTS", default_requests),
        window_seconds=_positive_integer(
            f"API_RATE_LIMIT_{prefix}_WINDOW_SECONDS",
            default_window,
        ),
    )


def get_api_rate_limit_settings() -> ApiRateLimitSettings:
    return ApiRateLimitSettings(
        enabled=_boolean("API_RATE_LIMIT_ENABLED", True),
        read=_policy("READ", 240),
        write=_policy("WRITE", 60),
        export=_policy("EXPORT", 10),
    )


def validate_api_rate_limit_configuration() -> None:
    get_api_rate_limit_settings()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _bearer_token(scope: Scope) -> str | None:
    authorization = Headers(scope=scope).get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def _actor_identifier(scope: Scope, client_ip: str) -> str:
    token = _bearer_token(scope)
    if token is not None:
        try:
            subject = decode_access_token_payload(token).subject
        except InvalidAccessTokenError:
            pass
        else:
            return f"user:{_digest(str(subject))}"
    return f"ip:{_digest(client_ip)}"


def _request_policy(
    method: str,
    path: str,
    settings: ApiRateLimitSettings,
) -> tuple[str, RateLimitPolicy]:
    if path.rstrip("/").endswith("/export"):
        return "export", settings.export
    if method in {"GET", "HEAD"}:
        return "read", settings.read
    return "write", settings.write


class ApiRateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        cache: Redis,
        settings_provider: Callable[[], ApiRateLimitSettings] = get_api_rate_limit_settings,
    ) -> None:
        self.app = app
        self.cache = cache
        self.settings_provider = settings_provider

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET").upper()
        path = scope.get("path", "")
        settings = self.settings_provider()
        if not settings.enabled or method == "OPTIONS" or not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        client_ip = get_client_ip(request)
        policy_name, policy = _request_policy(method, path, settings)

        try:
            actor_allowed, actor_retry_after = await SlidingWindowRateLimiter(
                cache=self.cache,
                namespace=f"api-{policy_name}",
                limit=policy.requests,
                window_seconds=policy.window_seconds,
            ).consume_with_retry_after(_actor_identifier(scope, client_ip))
            if not actor_allowed:
                await self._reject(scope, receive, send, actor_retry_after)
                return
        except RedisError:
            # General API traffic remains available during a cache incident. Sensitive auth
            # operations have their own fail-closed rate limits in src.auth.rate_limit.
            logger.exception(
                "API rate limiter unavailable; allowing request",
                extra={"method": method, "path": path},
            )

        await self.app(scope, receive, send)

    @staticmethod
    async def _reject(
        scope: Scope,
        receive: Receive,
        send: Send,
        retry_after: int,
    ) -> None:
        response = JSONResponse(
            status_code=429,
            content={
                "error_code": ErrorCode.RATE_LIMITED,
                "detail": "Too many requests. Try again later.",
            },
            headers={
                "Retry-After": str(retry_after),
                "Cache-Control": "no-store",
            },
        )
        await response(scope, receive, send)
