import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from src.auth.config import (
    get_access_token_expire_minutes,
    get_jwt_secret_key,
    get_refresh_token_expire_days,
)
from src.auth.constants import (
    ACCESS_TOKEN_TYPE,
    JWT_ALGORITHM,
    REFRESH_SESSION_PREFIX,
    REFRESH_TOKEN_TYPE,
    REVOKED_ACCESS_TOKEN_PREFIX,
)
from src.auth.exceptions import InvalidAccessTokenError

password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hash.hash("not-a-real-user-password")


@dataclass(frozen=True)
class AccessTokenPayload:
    subject: uuid.UUID
    expires_at: datetime
    session_id: uuid.UUID | None


@dataclass(frozen=True)
class RefreshTokenPayload:
    subject: uuid.UUID
    expires_at: datetime
    session_id: uuid.UUID


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, password_hash_value: str) -> bool:
    return password_hash.verify(password, password_hash_value)


def create_access_token(
    subject: uuid.UUID | str,
    *,
    session_id: uuid.UUID | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(UTC)
    session_id = session_id or uuid.uuid4()
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=get_access_token_expire_minutes())
    )
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": expires_at,
        "token_type": ACCESS_TOKEN_TYPE,
        "sid": str(session_id),
    }
    return jwt.encode(payload, get_jwt_secret_key(), algorithm=JWT_ALGORITHM)


def create_refresh_token(
    subject: uuid.UUID | str,
    *,
    session_id: uuid.UUID,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(UTC)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(days=get_refresh_token_expire_days())
    )
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": expires_at,
        "token_type": REFRESH_TOKEN_TYPE,
        "sid": str(session_id),
    }
    return jwt.encode(payload, get_jwt_secret_key(), algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        get_jwt_secret_key(),
        algorithms=[JWT_ALGORITHM],
        options={"require": ["sub", "exp"]},
    )


def decode_access_token_payload(token: str) -> AccessTokenPayload:
    try:
        payload = _decode_token(token)
        token_type = payload.get("token_type", ACCESS_TOKEN_TYPE)
        if token_type != ACCESS_TOKEN_TYPE:
            raise ValueError("Unexpected token type")
        subject = uuid.UUID(payload["sub"])
        expires_at = datetime.fromtimestamp(payload["exp"], UTC)
        session_id = uuid.UUID(payload["sid"]) if "sid" in payload else None
        return AccessTokenPayload(
            subject=subject,
            expires_at=expires_at,
            session_id=session_id,
        )
    except (InvalidTokenError, KeyError, OSError, OverflowError, TypeError, ValueError) as exc:
        raise InvalidAccessTokenError from exc


def decode_refresh_token(token: str) -> RefreshTokenPayload:
    try:
        payload = _decode_token(token)
        if payload.get("token_type") != REFRESH_TOKEN_TYPE:
            raise ValueError("Unexpected token type")
        return RefreshTokenPayload(
            subject=uuid.UUID(payload["sub"]),
            expires_at=datetime.fromtimestamp(payload["exp"], UTC),
            session_id=uuid.UUID(payload["sid"]),
        )
    except (InvalidTokenError, KeyError, OSError, OverflowError, TypeError, ValueError) as exc:
        raise InvalidAccessTokenError from exc


def decode_access_token(token: str) -> uuid.UUID:
    return decode_access_token_payload(token).subject


def revoked_access_token_key(token: str) -> str:
    token_digest = sha256(token.encode()).hexdigest()
    return f"{REVOKED_ACCESS_TOKEN_PREFIX}{token_digest}"


def refresh_session_key(session_id: uuid.UUID) -> str:
    return f"{REFRESH_SESSION_PREFIX}{session_id}"
