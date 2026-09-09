import uuid
from collections.abc import AsyncIterator
from hashlib import sha256

import pytest
from httpx import AsyncClient
from redis.asyncio import Redis

from src.auth.dependencies import get_email_service
from src.auth.exceptions import InvalidActionTokenError
from src.auth.service import TokenService
from src.main import app


class CapturingEmailService:
    def __init__(self) -> None:
        self.verification_tokens: list[str] = []
        self.password_reset_tokens: list[str] = []

    async def send_verification(self, recipient: str, token: str) -> None:
        self.verification_tokens.append(token)

    async def send_password_reset(self, recipient: str, token: str) -> None:
        self.password_reset_tokens.append(token)


async def test_action_token_rotation_and_user_key_cleanup(
    isolated_e2e_cache: Redis,
):
    service = TokenService(isolated_e2e_cache)
    public_id = uuid.uuid4()

    previous_token = await service.issue_action_token(public_id, "password-reset", 1800)
    current_token = await service.issue_action_token(public_id, "password-reset", 1800)
    current_digest = sha256(current_token.encode()).hexdigest()
    user_key = f"auth-action-user:password-reset:{public_id}"

    with pytest.raises(InvalidActionTokenError):
        await service.consume_action_token(previous_token, "password-reset")
    assert await isolated_e2e_cache.get(user_key) == current_digest

    assert await service.consume_action_token(current_token, "password-reset") == public_id
    assert await isolated_e2e_cache.exists(user_key) == 0


@pytest.fixture
async def captured_email_service(
    e2e_client: AsyncClient,
) -> AsyncIterator[CapturingEmailService]:
    service = CapturingEmailService()
    app.dependency_overrides[get_email_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(get_email_service, None)


async def test_email_verification_and_password_reset_flow(
    e2e_client: AsyncClient,
    captured_email_service: CapturingEmailService,
):
    email = "email-flow@example.com"
    old_password = "password123"
    new_password = "new-password123"

    register_response = await e2e_client.post(
        "/api/auth/register",
        json={"name": "Email Flow", "email": email, "password": old_password},
    )
    assert register_response.status_code == 201
    assert len(captured_email_service.verification_tokens) == 1

    verify_response = await e2e_client.post(
        "/api/auth/verify-email",
        json={"token": captured_email_service.verification_tokens[0]},
    )
    assert verify_response.status_code == 200

    forgot_response = await e2e_client.post(
        "/api/auth/forgot-password",
        json={"email": email},
    )
    assert forgot_response.status_code == 202
    assert len(captured_email_service.password_reset_tokens) == 1

    reset_response = await e2e_client.post(
        "/api/auth/reset-password",
        json={
            "token": captured_email_service.password_reset_tokens[0],
            "password": new_password,
            "confirm_password": new_password,
        },
    )
    assert reset_response.status_code == 200

    old_login_response = await e2e_client.post(
        "/api/auth/login",
        data={"username": email, "password": old_password},
    )
    assert old_login_response.status_code == 401

    new_login_response = await e2e_client.post(
        "/api/auth/login",
        data={"username": email, "password": new_password},
    )
    assert new_login_response.status_code == 200
