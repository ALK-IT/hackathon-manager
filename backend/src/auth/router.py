from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.config import get_auth_cookie_samesite, get_auth_cookie_secure
from src.auth.constants import REFRESH_TOKEN_COOKIE_NAME
from src.auth.dependencies import (
    get_current_user,
    get_token_service,
    get_user_service,
    optional_oauth2_scheme,
    unauthorized_exception,
)
from src.auth.exceptions import EmailAlreadyRegisteredError, InvalidAccessTokenError
from src.auth.models import User
from src.auth.schemas import TokenResponse, UserCreate, UserRead
from src.auth.service import IssuedTokenPair, TokenService, UserService

router = APIRouter(prefix="/api/auth", tags=["auth"])


def token_response(response: Response, tokens: IssuedTokenPair) -> TokenResponse:
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=tokens.refresh_token,
        max_age=tokens.refresh_expires_in,
        httponly=True,
        secure=get_auth_cookie_secure(),
        samesite=get_auth_cookie_samesite(),
        path="/api/auth",
    )
    return TokenResponse(
        access_token=tokens.access_token,
        expires_in=tokens.access_expires_in,
    )


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
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> TokenResponse:
    user = await service.authenticate(form_data.username, form_data.password)
    if user is None:
        raise unauthorized_exception()

    return token_response(response, await token_service.issue_token_pair(user.public_id))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    refresh_token: Annotated[
        str | None,
        Cookie(alias=REFRESH_TOKEN_COOKIE_NAME, include_in_schema=False),
    ] = None,
) -> TokenResponse:
    if refresh_token is None:
        raise unauthorized_exception()

    try:
        public_id = await token_service.consume_refresh_token(refresh_token)
    except InvalidAccessTokenError as exc:
        raise unauthorized_exception() from exc

    user = await service.get_by_public_id(public_id)
    if user is None:
        raise unauthorized_exception()

    return token_response(response, await token_service.issue_token_pair(user.public_id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    token_service: Annotated[TokenService, Depends(get_token_service)],
    token: Annotated[str | None, Depends(optional_oauth2_scheme)],
    refresh_token: Annotated[
        str | None,
        Cookie(alias=REFRESH_TOKEN_COOKIE_NAME, include_in_schema=False),
    ] = None,
) -> None:
    if token is not None:
        try:
            await token_service.revoke(token)
        except InvalidAccessTokenError:
            pass

    if refresh_token is not None:
        try:
            await token_service.revoke_refresh_token(refresh_token)
        except InvalidAccessTokenError:
            pass

    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        path="/api/auth",
        secure=get_auth_cookie_secure(),
        samesite=get_auth_cookie_samesite(),
    )


@router.get("/me", response_model=UserRead)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
