import os

from src.auth.constants import DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES


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


def get_jwt_secret_key() -> str:
    secret_key = os.environ.get("JWT_SECRET_KEY", "")
    if len(secret_key) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 characters")
    return secret_key
