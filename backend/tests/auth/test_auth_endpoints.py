import uuid
from types import SimpleNamespace

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import InvalidAccessTokenError
from src.auth.models import User
from src.auth.repository import UserRepository
from src.auth.service import IssuedTokenPair
from src.auth.utils import hash_password


async def test_logout_endpoint_returns_no_content(auth_client, mock_token_service, mocker):
    mock_token_service.revoke = mocker.AsyncMock()

    response = await auth_client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer access-token"},
    )

    assert response.status_code == 204
    assert response.content == b""
    mock_token_service.revoke.assert_awaited_once_with("access-token")


async def test_logout_endpoint_rejects_invalid_token(auth_client, mock_token_service, mocker):
    mock_token_service.revoke = mocker.AsyncMock(side_effect=InvalidAccessTokenError)

    response = await auth_client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_refresh_endpoint_rotates_token_pair(
    auth_client_with_user_service,
    mock_token_service,
    mock_user_service,
    mocker,
):
    public_id = uuid.uuid4()
    user = SimpleNamespace(public_id=public_id)
    tokens = IssuedTokenPair(
        access_token="new-access-token",
        refresh_token="new-refresh-token",
        access_expires_in=1800,
        refresh_expires_in=604800,
    )
    mock_token_service.consume_refresh_token = mocker.AsyncMock(return_value=public_id)
    mock_token_service.issue_token_pair = mocker.AsyncMock(return_value=tokens)
    mock_user_service.get_by_public_id.return_value = user

    response = await auth_client_with_user_service.post(
        "/api/auth/refresh",
        json={"refresh_token": "old-refresh-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "token_type": "bearer",
        "expires_in": 1800,
        "refresh_expires_in": 604800,
    }
    mock_token_service.consume_refresh_token.assert_awaited_once_with("old-refresh-token")
    mock_token_service.issue_token_pair.assert_awaited_once_with(public_id)


async def test_register_login_and_me_use_database(auth_client: AsyncClient):
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

    login_response = await auth_client.post(
        "/api/auth/login",
        data={"username": "jan@example.com", "password": "password123"},
    )

    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    me_response = await auth_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert me_response.status_code == 200
    assert uuid.UUID(me_response.json()["public_id"]) == public_id
    assert me_response.json()["email"] == "jan@example.com"


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
