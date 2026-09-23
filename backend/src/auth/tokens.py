from fastapi import Response

from src.auth.config import get_auth_cookie_samesite, get_auth_cookie_secure
from src.auth.constants import REFRESH_TOKEN_COOKIE_NAME
from src.auth.schemas import TokenResponse
from src.auth.service import IssuedTokenPair


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
