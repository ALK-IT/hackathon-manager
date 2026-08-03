from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas import TokenResponse, UserCreate, UserRead
from app.security import (
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    get_access_token_expire_minutes,
)
from app.services.user_service import EmailAlreadyRegisteredError, UserService

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def get_user_service(session: Annotated[AsyncSession, Depends(get_session)]) -> UserService:
    return UserService(UserRepository(session))


def unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email, password, or access token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    try:
        public_id = decode_access_token(token)
    except InvalidAccessTokenError as exc:
        raise unauthorized_exception() from exc

    user = await service.get_by_public_id(public_id)
    if user is None:
        raise unauthorized_exception()
    return user


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    try:
        return await service.register(data)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from exc


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[UserService, Depends(get_user_service)],
) -> TokenResponse:
    user = await service.authenticate(form_data.username, form_data.password)
    if user is None:
        raise unauthorized_exception()

    expires_in = get_access_token_expire_minutes() * 60
    return TokenResponse(
        access_token=create_access_token(user.public_id),
        expires_in=expires_in,
    )


@router.get("/me", response_model=UserRead)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
