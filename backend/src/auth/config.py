import os
from typing import Literal

from src.auth.constants import (
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
    DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS,
)


def get_access_token_expire_minutes() -> int:
    raw_value = os.environ.get(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        str(DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be an integer") from exc
    if value <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero")
    return value


def get_refresh_token_expire_days() -> int:
    raw_value = os.environ.get(
        "REFRESH_TOKEN_EXPIRE_DAYS",
        str(DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS),
    )
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError("REFRESH_TOKEN_EXPIRE_DAYS must be an integer") from exc
    if value <= 0:
        raise RuntimeError("REFRESH_TOKEN_EXPIRE_DAYS must be greater than zero")
    return value


def get_jwt_secret_key() -> str:
    secret_key = os.environ.get("JWT_SECRET_KEY", "")
    if len(secret_key) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 characters")
    return secret_key


def get_auth_cookie_secure() -> bool:
    return os.environ.get("AUTH_COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}


def get_auth_cookie_samesite() -> Literal["lax", "strict", "none"]:
    value = os.environ.get("AUTH_COOKIE_SAMESITE", "lax").lower()
    if value not in {"lax", "strict", "none"}:
        raise RuntimeError("AUTH_COOKIE_SAMESITE must be lax, strict, or none")
    return value


def get_frontend_origins() -> list[str]:
    raw_value = os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173")
    origins = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
    if not origins:
        raise RuntimeError("FRONTEND_ORIGINS must contain at least one origin")
    return origins


def get_frontend_url() -> str:
    return os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")


def get_smtp_host() -> str:
    return os.environ.get("SMTP_HOST", "localhost")


def get_smtp_port() -> int:
    try:
        return int(os.environ.get("SMTP_PORT", "1025"))
    except ValueError as exc:
        raise RuntimeError("SMTP_PORT must be an integer") from exc


def get_smtp_credentials() -> tuple[str | None, str | None]:
    return os.environ.get("SMTP_USERNAME") or None, os.environ.get("SMTP_PASSWORD") or None


def get_smtp_starttls() -> bool:
    return os.environ.get("SMTP_STARTTLS", "false").lower() in {"1", "true", "yes"}


def get_email_from() -> str:
    return os.environ.get("EMAIL_FROM", "no-reply@hackathon-manager.local")


def validate_configuration() -> None:
    get_jwt_secret_key()
    get_auth_cookie_samesite()
    get_frontend_origins()
    get_smtp_port()
