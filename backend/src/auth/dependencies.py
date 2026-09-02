from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.email import EmailService
from src.auth.exceptions import InvalidAccessTokenError
from src.auth.models import User
from src.auth.repository import UserRepository
from src.auth.service import TokenService, UserService
from src.auth.utils import decode_access_token_payload
from src.cache import get_cache
from src.database import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def get_user_service(session: Annotated[AsyncSession, Depends(get_session)]) -> UserService:
    return UserService(UserRepository(session))


def get_token_service(
    cache: Annotated[Redis, Depends(get_cache)],
) -> TokenService:
    return TokenService(cache)


def get_email_service() -> EmailService:
    return EmailService()


def unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email, password, or access token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> User:
    return await _get_authenticated_user(token, service, token_service)


async def get_optional_current_user(
    token: Annotated[str | None, Depends(optional_oauth2_scheme)],
    service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> User | None:
    if token is None:
        return None
    return await _get_authenticated_user(token, service, token_service)


async def _get_authenticated_user(
    token: str,
    service: UserService,
    token_service: TokenService,
) -> User:
    if await token_service.is_revoked(token):
        raise unauthorized_exception()

    try:
        payload = decode_access_token_payload(token)
    except InvalidAccessTokenError as exc:
        raise unauthorized_exception() from exc

    user = await service.get_by_public_id(payload.subject)
    if user is None or user.auth_version != payload.auth_version:
        raise unauthorized_exception()
    return user
