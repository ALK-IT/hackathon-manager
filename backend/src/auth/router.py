from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.config import get_access_token_expire_minutes
from src.auth.dependencies import get_current_user, get_user_service, unauthorized_exception
from src.auth.exceptions import EmailAlreadyRegisteredError
from src.auth.models import User
from src.auth.schemas import TokenResponse, UserCreate, UserRead
from src.auth.service import UserService
from src.auth.utils import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
