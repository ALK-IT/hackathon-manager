import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient

from src.auth.dependencies import get_email_service, get_token_service, get_user_service
from src.auth.service import IssuedTokenPair
from src.auth.utils import create_access_token, create_refresh_token
from src.main import app


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-with-at-least-32-characters",  # gitleaks:allow
    )


@pytest.fixture
def mock_token_service(mocker):
    service = mocker.Mock()
    service.is_revoked = mocker.AsyncMock(return_value=False)

    async def issue_token_pair(public_id: uuid.UUID, auth_version: int = 0) -> IssuedTokenPair:
        session_id = uuid.uuid4()
        return IssuedTokenPair(
            access_token=create_access_token(
                public_id,
                session_id=session_id,
                auth_version=auth_version,
            ),
            refresh_token=create_refresh_token(
                public_id,
                session_id=session_id,
                auth_version=auth_version,
            ),
            access_expires_in=1800,
            refresh_expires_in=604800,
        )

    service.issue_token_pair = mocker.AsyncMock(side_effect=issue_token_pair)
    service.issue_action_token = mocker.AsyncMock(return_value="a" * 43)
    service.consume_action_token = mocker.AsyncMock()
    service.enforce_rate_limit = mocker.AsyncMock()
    return service


@pytest.fixture
def mock_email_service(mocker):
    service = mocker.Mock()
    service.send_verification = mocker.AsyncMock()
    service.send_password_reset = mocker.AsyncMock()
    return service


@pytest.fixture
def mock_user_service(mocker):
    service = mocker.Mock()
    service.get_by_public_id = mocker.AsyncMock()
    return service


@pytest.fixture
async def auth_client(
    api_client: AsyncClient,
    mock_token_service,
    mock_email_service,
) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_token_service] = lambda: mock_token_service
    app.dependency_overrides[get_email_service] = lambda: mock_email_service

    try:
        yield api_client
    finally:
        app.dependency_overrides.pop(get_token_service, None)
        app.dependency_overrides.pop(get_email_service, None)


@pytest.fixture
async def auth_client_with_user_service(
    auth_client: AsyncClient,
    mock_user_service,
) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    try:
        yield auth_client
    finally:
        app.dependency_overrides.pop(get_user_service, None)
