import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Request
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_optional_current_user
from src.auth.email import EmailDeliveryError
from src.auth.exceptions import InvalidAccessTokenError, RateLimitError
from src.auth.models import User
from src.auth.repository import UserRepository
from src.auth.router import enforce_rate_limits
from src.auth.service import IssuedTokenPair
from src.auth.utils import hash_password


async def test_optional_current_user_allows_missing_token(mocker):
    user_service = mocker.Mock()
    token_service = mocker.Mock()
    token_service.is_revoked = mocker.AsyncMock()

    user = await get_optional_current_user(None, user_service, token_service)

    assert user is None
    token_service.is_revoked.assert_not_awaited()


async def test_optional_current_user_rejects_invalid_token(mocker):
    user_service = mocker.Mock()
    token_service = mocker.Mock()
    token_service.is_revoked = mocker.AsyncMock(return_value=False)

    with pytest.raises(HTTPException) as exc_info:
        await get_optional_current_user("invalid-token", user_service, token_service)

    assert exc_info.value.status_code == 401
    token_service.is_revoked.assert_awaited_once_with("invalid-token")


async def test_logout_endpoint_returns_no_content(auth_client, mock_token_service, mocker):
    mock_token_service.revoke = mocker.AsyncMock()
    mock_token_service.revoke_refresh_token = mocker.AsyncMock()
    auth_client.cookies.set("refresh_token", "refresh-token", path="/api/auth")

    response = await auth_client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer access-token"},
    )

    assert response.status_code == 204
    assert response.content == b""
    assert "refresh_token=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]
    mock_token_service.revoke.assert_awaited_once_with("access-token")
    mock_token_service.revoke_refresh_token.assert_awaited_once_with("refresh-token")


async def test_logout_endpoint_is_idempotent_for_invalid_token(
    auth_client, mock_token_service, mocker
):
    mock_token_service.revoke = mocker.AsyncMock(side_effect=InvalidAccessTokenError)
    mock_token_service.revoke_refresh_token = mocker.AsyncMock()

    response = await auth_client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 204
    assert "Max-Age=0" in response.headers["set-cookie"]


async def test_refresh_endpoint_rotates_token_pair(
    auth_client_with_user_service,
    mock_token_service,
    mock_user_service,
    mocker,
):
    public_id = uuid.uuid4()
    user = SimpleNamespace(public_id=public_id, auth_version=2)
    tokens = IssuedTokenPair(
        access_token="new-access-token",
        refresh_token="new-refresh-token",
        access_expires_in=1800,
        refresh_expires_in=604800,
    )
    payload = SimpleNamespace(subject=public_id, auth_version=2)
    mock_token_service.consume_refresh_token = mocker.AsyncMock(return_value=payload)
    mock_token_service.issue_token_pair = mocker.AsyncMock(return_value=tokens)
    mock_user_service.get_by_public_id.return_value = user

    auth_client_with_user_service.cookies.set(
        "refresh_token",
        "old-refresh-token",
        path="/api/auth",
    )
    response = await auth_client_with_user_service.post("/api/auth/refresh")

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new-access-token",
        "token_type": "bearer",
        "expires_in": 1800,
    }
    assert "refresh_token=new-refresh-token" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    mock_token_service.consume_refresh_token.assert_awaited_once_with("old-refresh-token")
    mock_token_service.issue_token_pair.assert_awaited_once_with(public_id, 2)


async def test_refresh_endpoint_requires_cookie(auth_client_with_user_service):
    response = await auth_client_with_user_service.post("/api/auth/refresh")

    assert response.status_code == 401


async def test_register_verify_login_and_me_use_database(
    auth_client: AsyncClient,
    mock_token_service,
):
    register_response = await auth_client.post(
        "/api/auth/register",
        json={
            "name": "Jan Kowalski",
            "email": "JAN@EXAMPLE.COM",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201
    public_id = uuid.UUID(register_response.json()["public_id"])

    blocked_login_response = await auth_client.post(
        "/api/auth/login",
        data={"username": "jan@example.com", "password": "password123"},
    )
    assert blocked_login_response.status_code == 403

    mock_token_service.consume_action_token.return_value = public_id
    verify_response = await auth_client.post(
        "/api/auth/verify-email",
        json={"token": "a" * 43},
    )
    assert verify_response.status_code == 200

    login_response = await auth_client.post(
        "/api/auth/login",
        data={"username": "jan@example.com", "password": "password123"},
    )

    assert login_response.status_code == 200
    assert "refresh_token" not in login_response.json()
    assert "refresh_token=" in login_response.headers["set-cookie"]
    assert "HttpOnly" in login_response.headers["set-cookie"]
    access_token = login_response.json()["access_token"]

    me_response = await auth_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert me_response.status_code == 200
    assert uuid.UUID(me_response.json()["public_id"]) == public_id
    assert me_response.json()["email"] == "jan@example.com"
    assert me_response.json()["role"] == "user"


async def test_failed_login_counts_both_ip_and_identifier_limits(
    auth_client_with_user_service,
    mock_user_service,
    mock_token_service,
    mocker,
):
    mock_user_service.authenticate = mocker.AsyncMock(return_value=None)

    response = await auth_client_with_user_service.post(
        "/api/auth/login",
        data={"username": "victim@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert mock_token_service.enforce_rate_limit.await_args_list == [
        mocker.call("login:ip", "127.0.0.1", 10, 300),
        mocker.call("login:identifier", "victim@example.com", 10, 300),
    ]


async def test_successful_login_does_not_count_toward_identifier_limit(
    auth_client_with_user_service,
    mock_user_service,
    mock_token_service,
    mocker,
):
    mock_user_service.authenticate = mocker.AsyncMock(
        return_value=SimpleNamespace(
            public_id=uuid.uuid4(),
            auth_version=0,
            email_verified_at=object(),
        )
    )

    response = await auth_client_with_user_service.post(
        "/api/auth/login",
        data={"username": "user@example.com", "password": "correct-password"},
    )

    assert response.status_code == 200
    mock_token_service.enforce_rate_limit.assert_awaited_once_with("login:ip", "127.0.0.1", 10, 300)


async def test_untrusted_x_real_ip_header_is_ignored(
    mock_token_service,
    monkeypatch,
):
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    request = Request(
        {
            "type": "http",
            "headers": [(b"x-real-ip", b"203.0.113.10")],
            "client": ("198.51.100.20", 12345),
        }
    )

    await enforce_rate_limits(mock_token_service, request, "login", ip_limit=10)

    mock_token_service.enforce_rate_limit.assert_awaited_once_with(
        "login:ip", "198.51.100.20", 10, 300
    )


async def test_x_real_ip_header_is_used_when_proxy_headers_are_trusted(
    mock_token_service,
    monkeypatch,
):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")
    request = Request(
        {
            "type": "http",
            "headers": [(b"x-real-ip", b"203.0.113.10")],
            "client": ("198.51.100.20", 12345),
        }
    )

    await enforce_rate_limits(mock_token_service, request, "login", ip_limit=10)

    mock_token_service.enforce_rate_limit.assert_awaited_once_with(
        "login:ip", "203.0.113.10", 10, 300
    )


async def test_forgot_password_does_not_disclose_missing_account(
    auth_client_with_user_service,
    mock_user_service,
    mock_email_service,
    mocker,
):
    mock_user_service.get_by_email = mocker.AsyncMock(return_value=None)

    response = await auth_client_with_user_service.post(
        "/api/auth/forgot-password",
        json={"email": "missing@example.com"},
    )

    assert response.status_code == 202
    mock_email_service.send_password_reset.assert_not_awaited()


async def test_rate_limited_password_reset_returns_retry_after(
    auth_client,
    mock_token_service,
):
    mock_token_service.enforce_rate_limit.side_effect = RateLimitError(60)

    response = await auth_client.post(
        "/api/auth/forgot-password",
        json={"email": "jan@example.com"},
    )

    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"


async def test_resend_verification_sends_a_new_link(
    auth_client_with_user_service,
    mock_user_service,
    mock_token_service,
    mock_email_service,
    mocker,
):
    public_id = uuid.uuid4()
    user = SimpleNamespace(
        public_id=public_id,
        email="jan@example.com",
        email_verified_at=None,
    )
    mock_user_service.get_by_email = mocker.AsyncMock(return_value=user)

    response = await auth_client_with_user_service.post(
        "/api/auth/resend-verification",
        json={"email": "jan@example.com"},
    )

    assert response.status_code == 202
    mock_token_service.issue_action_token.assert_awaited_once_with(
        public_id,
        "email-verification",
        86400,
    )
    mock_email_service.send_verification.assert_awaited_once()


async def test_resend_verification_is_noop_for_verified_account(
    auth_client_with_user_service,
    mock_user_service,
    mock_token_service,
    mock_email_service,
    mocker,
):
    mock_user_service.get_by_email = mocker.AsyncMock(
        return_value=SimpleNamespace(
            public_id=uuid.uuid4(),
            email="jan@example.com",
            email_verified_at=object(),
        )
    )

    response = await auth_client_with_user_service.post(
        "/api/auth/resend-verification",
        json={"email": "jan@example.com"},
    )

    assert response.status_code == 202
    mock_token_service.issue_action_token.assert_not_awaited()
    mock_email_service.send_verification.assert_not_awaited()


async def test_reset_password_consumes_token_and_changes_password(
    auth_client_with_user_service,
    mock_user_service,
    mock_token_service,
    mocker,
):
    public_id = uuid.uuid4()
    mock_token_service.consume_action_token.return_value = public_id
    mock_user_service.reset_password = mocker.AsyncMock(return_value=SimpleNamespace())

    response = await auth_client_with_user_service.post(
        "/api/auth/reset-password",
        json={
            "token": "a" * 43,
            "password": "new-password123",
            "confirm_password": "new-password123",
        },
    )

    assert response.status_code == 200
    mock_token_service.consume_action_token.assert_awaited_once_with(
        "a" * 43,
        "password-reset",
    )
    mock_user_service.reset_password.assert_awaited_once_with(public_id, "new-password123")


async def test_register_endpoint_rejects_duplicate_email(auth_client: AsyncClient):
    payload = {
        "name": "Jan Kowalski",
        "email": "jan@example.com",
        "password": "password123",
    }

    first_response = await auth_client.post("/api/auth/register", json=payload)
    duplicate_response = await auth_client.post("/api/auth/register", json=payload)

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409


async def test_register_reports_verification_email_delivery_failure(
    auth_client: AsyncClient,
    mock_email_service,
):
    mock_email_service.send_verification.side_effect = EmailDeliveryError

    response = await auth_client.post(
        "/api/auth/register",
        json={
            "name": "Mail Failure",
            "email": "mail-failure@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 503


async def test_user_me_information(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate,
):
    organizer = User(
        name="Organizer",
        email="organizer@example.com",
        password_hash=hash_password("password123"),
    )
    participant = User(
        name="Participant",
        email="participant@example.com",
        password_hash=hash_password("password123"),
    )
    repository = UserRepository(session)
    await repository.create(organizer)
    await repository.create(participant)
    await repository.commit()

    force_authenticate(organizer)
    organizer_response = await api_client.get("/api/auth/me")

    force_authenticate(participant)
    participant_response = await api_client.get("/api/auth/me")

    force_authenticate(None)
    anonymous_response = await api_client.get("/api/auth/me")

    assert organizer_response.status_code == 200
    assert organizer_response.json()["email"] == "organizer@example.com"
    assert participant_response.status_code == 200
    assert participant_response.json()["email"] == "participant@example.com"
    assert anonymous_response.status_code == 401
