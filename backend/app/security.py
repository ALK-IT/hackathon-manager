import os
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hash.hash("not-a-real-user-password")


class InvalidAccessTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, password_hash_value: str) -> bool:
    return password_hash.verify(password, password_hash_value)


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


def create_access_token(
    subject: uuid.UUID | str,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(UTC)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=get_access_token_expire_minutes())
    )
    payload = {"sub": str(subject), "iat": now, "exp": expires_at}
    return jwt.encode(payload, get_jwt_secret_key(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret_key(),
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        return uuid.UUID(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise InvalidAccessTokenError from exc
