from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import InvalidAccessTokenError
from src.auth.models import User
from src.auth.repository import UserRepository
from src.auth.service import TokenService, UserService
from src.auth.utils import decode_access_token
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
    if await token_service.is_revoked(token):
        raise unauthorized_exception()

    try:
        public_id = decode_access_token(token)
    except InvalidAccessTokenError as exc:
        raise unauthorized_exception() from exc

    user = await service.get_by_public_id(public_id)
    if user is None:
        raise unauthorized_exception()
    return user
