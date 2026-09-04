import logging
from collections.abc import Awaitable
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.config import (
    get_auth_cookie_samesite,
    get_auth_cookie_secure,
    get_trust_proxy_headers,
)
from src.auth.constants import REFRESH_TOKEN_COOKIE_NAME
from src.auth.dependencies import (
    get_current_user,
    get_email_service,
    get_token_service,
    get_user_service,
    optional_oauth2_scheme,
    unauthorized_exception,
)
from src.auth.email import EmailDeliveryError, EmailService
from src.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidAccessTokenError,
    InvalidActionTokenError,
    RateLimitError,
)
from src.auth.models import User
from src.auth.schemas import (
    ActionTokenRequest,
    EmailActionRequest,
    MessageResponse,
    PasswordResetRequest,
    TokenResponse,
    UserCreate,
    UserMeRead,
    UserRead,
)
from src.auth.service import IssuedTokenPair, TokenService, UserService

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)
EMAIL_VERIFICATION_TTL = 24 * 60 * 60
PASSWORD_RESET_TTL = 30 * 60
RATE_LIMIT_WINDOW = 5 * 60


async def deliver_email(send_operation: Awaitable[None]) -> bool:
    try:
        await send_operation
    except EmailDeliveryError:
        logger.warning("Authentication email delivery failed", exc_info=True)
        return False
    return True


async def enforce_rate_limits(
    token_service: TokenService,
    request: Request,
    scope: str,
    *,
    identifier: str | None = None,
    ip_limit: int | None = None,
    identifier_limit: int | None = None,
) -> None:
    try:
        if ip_limit is not None:
            client_ip = request.client.host if request.client else "unknown"
            if get_trust_proxy_headers():
                proxy_ip = request.headers.get("X-Real-IP", "").strip()
                if proxy_ip:
                    client_ip = proxy_ip
            await token_service.enforce_rate_limit(
                f"{scope}:ip",
                client_ip,
                ip_limit,
                RATE_LIMIT_WINDOW,
            )
        if identifier is not None and identifier_limit is not None:
            await token_service.enforce_rate_limit(
                f"{scope}:identifier",
                identifier,
                identifier_limit,
                RATE_LIMIT_WINDOW,
            )
    except RateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again later.",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc


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
    request: Request,
    data: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> User:
    await enforce_rate_limits(
        token_service,
        request,
        "register",
        identifier=str(data.email),
        ip_limit=5,
        identifier_limit=3,
    )
    try:
        user = await service.register(data)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from exc
    token = await token_service.issue_action_token(
        user.public_id,
        "email-verification",
        EMAIL_VERIFICATION_TTL,
    )
    if not await deliver_email(email_service.send_verification(user.email, token)):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account was created, but the verification email could not be sent. Try again later.",
        )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> TokenResponse:
    await enforce_rate_limits(
        token_service,
        request,
        "login",
        ip_limit=10,
    )
    user = await service.authenticate(form_data.username, form_data.password)
    if user is None:
        await enforce_rate_limits(
            token_service,
            request,
            "login",
            identifier=form_data.username,
            identifier_limit=10,
        )
        raise unauthorized_exception()
    if user.email_verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address has not been verified",
        )

    return token_response(
        response,
        await token_service.issue_token_pair(user.public_id, user.auth_version),
    )


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
        payload = await token_service.consume_refresh_token(refresh_token)
    except InvalidAccessTokenError as exc:
        raise unauthorized_exception() from exc

    user = await service.get_by_public_id(payload.subject)
    if user is None or user.auth_version != payload.auth_version:
        raise unauthorized_exception()

    return token_response(
        response,
        await token_service.issue_token_pair(user.public_id, user.auth_version),
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    request: Request,
    data: ActionTokenRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> MessageResponse:
    await enforce_rate_limits(token_service, request, "verify-email", ip_limit=20)
    try:
        public_id = await token_service.consume_action_token(data.token, "email-verification")
    except InvalidActionTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link is invalid or expired",
        ) from exc
    if await service.verify_email(public_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    return MessageResponse(message="Email address verified")


@router.post("/resend-verification", response_model=MessageResponse, status_code=202)
async def resend_verification(
    request: Request,
    data: EmailActionRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> MessageResponse:
    await enforce_rate_limits(
        token_service,
        request,
        "resend-verification",
        identifier=str(data.email),
        ip_limit=5,
        identifier_limit=3,
    )
    user = await service.get_by_email(str(data.email))
    if user is not None and user.email_verified_at is None:
        token = await token_service.issue_action_token(
            user.public_id,
            "email-verification",
            EMAIL_VERIFICATION_TTL,
        )
        await deliver_email(email_service.send_verification(user.email, token))
    return MessageResponse(message="If the account exists, a message has been sent")


@router.post("/forgot-password", response_model=MessageResponse, status_code=202)
async def forgot_password(
    request: Request,
    data: EmailActionRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> MessageResponse:
    await enforce_rate_limits(
        token_service,
        request,
        "forgot-password",
        identifier=str(data.email),
        ip_limit=5,
        identifier_limit=3,
    )
    user = await service.get_by_email(str(data.email))
    if user is not None:
        token = await token_service.issue_action_token(
            user.public_id,
            "password-reset",
            PASSWORD_RESET_TTL,
        )
        await deliver_email(email_service.send_password_reset(user.email, token))
    return MessageResponse(message="If the account exists, a message has been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: Request,
    data: PasswordResetRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> MessageResponse:
    await enforce_rate_limits(token_service, request, "reset-password", ip_limit=20)
    try:
        public_id = await token_service.consume_action_token(data.token, "password-reset")
    except InvalidActionTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset link is invalid or expired",
        ) from exc
    if await service.reset_password(public_id, data.password) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    return MessageResponse(message="Password has been changed")


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


@router.get("/me", response_model=UserMeRead)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
