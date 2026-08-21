from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient

from src.auth.models import User, UserRole
from src.hackathons.dependencies import get_hackathon_service
from src.hackathons.service import HackathonService
from src.main import app
from tests.hackathons.factories import (
    HackathonFactory,
    UserFactory,
    make_hackathon,
    make_user,
)


@pytest.fixture
def user_factory() -> UserFactory:
    return make_user


@pytest.fixture
def admin_user(user_factory: UserFactory) -> User:
    return user_factory(role=UserRole.ADMIN)


@pytest.fixture
def regular_user(user_factory: UserFactory) -> User:
    return user_factory(role=UserRole.USER)


@pytest.fixture
def hackathon_factory() -> HackathonFactory:
    return make_hackathon


@pytest.fixture
def mock_hackathon_service(mocker) -> HackathonService:
    service = mocker.Mock(spec=HackathonService)
    service.list_hackathons = mocker.AsyncMock(return_value=[])
    service.list_managed_hackathons = mocker.AsyncMock(return_value=[])
    service.create_hackathon = mocker.AsyncMock()
    service.get_hackathon = mocker.AsyncMock()
    service.update_hackathon = mocker.AsyncMock()
    service.delete_hackathon = mocker.AsyncMock()
    service.add_co_organizer = mocker.AsyncMock()
    service.open_registration = mocker.AsyncMock()
    service.close_registration = mocker.AsyncMock()
    return service


@pytest.fixture
async def hackathon_client(
    api_client: AsyncClient,
    force_authenticate,
    admin_user: User,
    mock_hackathon_service: HackathonService,
) -> AsyncIterator[AsyncClient]:
    force_authenticate(admin_user)
    app.dependency_overrides[get_hackathon_service] = lambda: mock_hackathon_service

    try:
        yield api_client
    finally:
        app.dependency_overrides.pop(get_hackathon_service, None)
