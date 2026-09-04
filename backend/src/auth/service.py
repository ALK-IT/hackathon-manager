import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from math import ceil
from secrets import token_urlsafe
from typing import Literal

from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError

from src.auth.config import get_access_token_expire_minutes, get_refresh_token_expire_days
from src.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidAccessTokenError,
    InvalidActionTokenError,
    RateLimitError,
)
from src.auth.models import User
from src.auth.repository import UserRepository
from src.auth.schemas import UserCreate
from src.auth.utils import (
    DUMMY_PASSWORD_HASH,
    RefreshTokenPayload,
    create_access_token,
    create_refresh_token,
    decode_access_token_payload,
    decode_refresh_token,
    hash_password,
    refresh_session_key,
    revoked_access_token_key,
    verify_password,
)

ActionTokenKind = Literal["email-verification", "password-reset"]
RATE_LIMIT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return {current, redis.call('TTL', KEYS[1])}
"""
ISSUE_ACTION_TOKEN_SCRIPT = """
local previous_digest = redis.call('GET', KEYS[1])
if previous_digest then
  redis.call('DEL', ARGV[1] .. previous_digest)
end
redis.call('SET', KEYS[2], ARGV[2], 'EX', ARGV[3])
redis.call('SET', KEYS[1], ARGV[4], 'EX', ARGV[3])
return 1
"""
CONSUME_ACTION_TOKEN_SCRIPT = """
local subject = redis.call('GETDEL', KEYS[1])
if not subject then
  return false
end
local user_key = ARGV[1] .. subject
if redis.call('GET', user_key) == ARGV[2] then
  redis.call('DEL', user_key)
end
return subject
"""


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def register(self, data: UserCreate) -> User:
        if await self.repository.get_by_email(data.email) is not None:
            raise EmailAlreadyRegisteredError

        user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
        )

        try:
            await self.repository.create(user)
            await self.repository.commit()
        except IntegrityError as exc:
            await self.repository.rollback()
            raise EmailAlreadyRegisteredError from exc

        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        normalized_email = email.strip().lower()
        user = await self.repository.get_by_email(normalized_email)

        if user is None:
            verify_password(password, DUMMY_PASSWORD_HASH)
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    async def get_by_public_id(self, public_id: uuid.UUID) -> User | None:
        return await self.repository.get_by_public_id(public_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.repository.get_by_email(email.strip().lower())

    async def verify_email(self, public_id: uuid.UUID) -> User | None:
        user = await self.repository.get_by_public_id(public_id)
        if user is None:
            return None
        if user.email_verified_at is None:
            user.email_verified_at = datetime.now(UTC)
            await self.repository.update(user)
            await self.repository.commit()
        return user

    async def reset_password(self, public_id: uuid.UUID, password: str) -> User | None:
        user = await self.repository.get_by_public_id(public_id)
        if user is None:
            return None
        user.password_hash = hash_password(password)
        user.auth_version += 1
        await self.repository.update(user)
        await self.repository.commit()
        return user


@dataclass(frozen=True)
class IssuedTokenPair:
    access_token: str
    refresh_token: str
    access_expires_in: int
    refresh_expires_in: int


class TokenService:
    def __init__(self, cache: Redis):
        self.cache = cache

    async def revoke(self, token: str) -> None:
        payload = decode_access_token_payload(token)
        ttl_seconds = max(1, ceil((payload.expires_at - datetime.now(UTC)).total_seconds()))
        await self.cache.set(revoked_access_token_key(token), "1", ex=ttl_seconds)
        if payload.session_id is not None:
            await self.cache.delete(refresh_session_key(payload.session_id))

    async def is_revoked(self, token: str) -> bool:
        return bool(await self.cache.exists(revoked_access_token_key(token)))

    async def revoke_refresh_token(self, token: str) -> None:
        payload = decode_refresh_token(token)
        await self.cache.delete(refresh_session_key(payload.session_id))

    async def issue_token_pair(
        self,
        subject: uuid.UUID,
        auth_version: int = 0,
    ) -> IssuedTokenPair:
        session_id = uuid.uuid4()
        access_expires_in = get_access_token_expire_minutes() * 60
        refresh_expires_in = get_refresh_token_expire_days() * 24 * 60 * 60
        access_token = create_access_token(
            subject,
            session_id=session_id,
            auth_version=auth_version,
        )
        refresh_token = create_refresh_token(
            subject,
            session_id=session_id,
            auth_version=auth_version,
        )
        await self.cache.set(
            refresh_session_key(session_id),
            "1",
            ex=refresh_expires_in,
        )
        return IssuedTokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_expires_in=access_expires_in,
            refresh_expires_in=refresh_expires_in,
        )

    async def consume_refresh_token(self, token: str) -> RefreshTokenPayload:
        payload = decode_refresh_token(token)
        session = await self.cache.getdel(refresh_session_key(payload.session_id))
        if session is None:
            raise InvalidAccessTokenError
        return payload

    async def issue_action_token(
        self,
        subject: uuid.UUID,
        kind: ActionTokenKind,
        expires_in: int,
    ) -> str:
        raw_token = token_urlsafe(32)
        digest = sha256(raw_token.encode()).hexdigest()
        action_key_prefix = f"auth-action:{kind}:"
        user_key = f"auth-action-user:{kind}:{subject}"
        await self.cache.eval(
            ISSUE_ACTION_TOKEN_SCRIPT,
            2,
            user_key,
            f"{action_key_prefix}{digest}",
            action_key_prefix,
            str(subject),
            expires_in,
            digest,
        )
        return raw_token

    async def consume_action_token(
        self,
        token: str,
        kind: ActionTokenKind,
    ) -> uuid.UUID:
        digest = sha256(token.encode()).hexdigest()
        subject = await self.cache.eval(
            CONSUME_ACTION_TOKEN_SCRIPT,
            1,
            f"auth-action:{kind}:{digest}",
            f"auth-action-user:{kind}:",
            digest,
        )
        if subject is None:
            raise InvalidActionTokenError
        try:
            public_id = uuid.UUID(subject)
        except (TypeError, ValueError) as exc:
            raise InvalidActionTokenError from exc
        return public_id

    async def enforce_rate_limit(
        self,
        scope: str,
        identifier: str,
        limit: int,
        window_seconds: int,
    ) -> None:
        digest = sha256(identifier.strip().lower().encode()).hexdigest()
        key = f"rate-limit:{scope}:{digest}"
        current, ttl = await self.cache.eval(
            RATE_LIMIT_SCRIPT,
            1,
            key,
            window_seconds,
        )
        if int(current) > limit:
            raise RateLimitError(max(1, int(ttl)))
