import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from math import ceil

from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError

from src.auth.config import get_access_token_expire_minutes, get_refresh_token_expire_days
from src.auth.exceptions import EmailAlreadyRegisteredError, InvalidAccessTokenError
from src.auth.models import User
from src.auth.repository import UserRepository
from src.auth.schemas import UserCreate
from src.auth.utils import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    decode_access_token_payload,
    decode_refresh_token,
    hash_password,
    refresh_session_key,
    revoked_access_token_key,
    verify_password,
)


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

    async def issue_token_pair(self, subject: uuid.UUID) -> IssuedTokenPair:
        session_id = uuid.uuid4()
        access_expires_in = get_access_token_expire_minutes() * 60
        refresh_expires_in = get_refresh_token_expire_days() * 24 * 60 * 60
        access_token = create_access_token(subject, session_id=session_id)
        refresh_token = create_refresh_token(subject, session_id=session_id)
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

    async def consume_refresh_token(self, token: str) -> uuid.UUID:
        payload = decode_refresh_token(token)
        session = await self.cache.getdel(refresh_session_key(payload.session_id))
        if session is None:
            raise InvalidAccessTokenError
        return payload.subject
