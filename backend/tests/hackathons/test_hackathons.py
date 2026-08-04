import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from src.auth.dependencies import get_current_user
from src.auth.models import User, UserRole
from src.hackathons.dependencies import get_hackathon_service
from src.hackathons.exceptions import (
    AdminRequiredError,
    HackathonNotFoundError,
    HackathonPermissionDeniedError,
    InvalidConfirmNameError,
    InvalidDateRangeError,
    InvalidTeamSizeError,
    RegistrationAlreadyClosedError,
    RegistrationAlreadyOpenError,
)
from src.hackathons.models import Hackathon
from src.hackathons.schemas import HackathonCreate, HackathonUpdate
from src.hackathons.service import HackathonService
from src.main import app

NOW = datetime(2026, 9, 1, 10, tzinfo=UTC)


def make_user(*, user_id: int = 1, role: UserRole = UserRole.USER) -> User:
    user = User(
        name=f"User {user_id}",
        email=f"user{user_id}@example.com",
        password_hash="hashed-password",
        role=role,
    )
    user.id = user_id
    user.public_id = uuid.uuid4()
    user.created_at = NOW
    return user


def make_hackathon(
    *,
    organizer: User,
    registration_open: bool = False,
    co_organizers: list[User] | None = None,
) -> Hackathon:
    hackathon = Hackathon(
        name="Hackathon AI",
        description="Build something useful",
        start_date=NOW + timedelta(days=1),
        end_date=NOW + timedelta(days=2),
        registration_open=registration_open,
        capacity=100,
        max_team_size=4,
        organizer=organizer,
        organizer_id=organizer.id,
        co_organizers=co_organizers or [],
    )
    hackathon.id = 1
    hackathon.public_id = uuid.uuid4()
    hackathon.is_deleted = False
    hackathon.deleted_at = None
    hackathon.created_at = NOW
    hackathon.updated_at = NOW
    return hackathon


@pytest.fixture
def create_data() -> HackathonCreate:
    return HackathonCreate(
        name="  Hackathon AI  ",
        description="  Build something useful  ",
        start_date=NOW + timedelta(days=1),
        end_date=NOW + timedelta(days=2),
        capacity=100,
        max_team_size=4,
    )


def test_create_schema_normalizes_text(create_data):
    assert create_data.name == "Hackathon AI"
    assert create_data.description == "Build something useful"


def test_create_schema_rejects_invalid_date_range():
    with pytest.raises(ValidationError):
        HackathonCreate(
            name="Hackathon AI",
            start_date=NOW,
            end_date=NOW,
            max_team_size=4,
        )


def test_create_schema_rejects_team_size_greater_than_capacity():
    with pytest.raises(ValidationError):
        HackathonCreate(
            name="Hackathon AI",
            start_date=NOW,
            end_date=NOW + timedelta(days=1),
            capacity=3,
            max_team_size=4,
        )


def test_create_schema_rejects_datetime_without_timezone():
    with pytest.raises(ValidationError):
        HackathonCreate(
            name="Hackathon AI",
            start_date=NOW.replace(tzinfo=None),
            end_date=(NOW + timedelta(days=1)).replace(tzinfo=None),
            max_team_size=4,
        )


def test_update_schema_rejects_empty_payload():
    with pytest.raises(ValidationError):
        HackathonUpdate()


def test_update_schema_allows_removing_capacity():
    data = HackathonUpdate(capacity=None)

    assert data.model_dump(exclude_unset=True) == {"capacity": None}


async def test_admin_can_create_hackathon(mocker, create_data):
    repository = mocker.Mock()
    repository.add = mocker.AsyncMock()
    repository.commit = mocker.AsyncMock()
    repository.rollback = mocker.AsyncMock()
    service = HackathonService(repository)
    admin = make_user(role=UserRole.ADMIN)

    hackathon = await service.create_hackathon(create_data, admin)

    assert hackathon.organizer is admin
    assert hackathon.name == "Hackathon AI"
    assert hackathon.registration_open is False
    repository.add.assert_awaited_once_with(hackathon)
    repository.commit.assert_awaited_once_with()
    repository.rollback.assert_not_awaited()


async def test_regular_user_cannot_create_hackathon(mocker, create_data):
    repository = mocker.Mock()
    service = HackathonService(repository)

    with pytest.raises(AdminRequiredError):
        await service.create_hackathon(create_data, make_user())

    repository.add.assert_not_called()


async def test_list_returns_hackathons_accessible_to_user(mocker):
    user = make_user()
    accessible = [make_hackathon(organizer=user)]
    repository = mocker.Mock()
    repository.list_accessible = mocker.AsyncMock(return_value=accessible)
    service = HackathonService(repository)

    result = await service.list_hackathons(user)

    assert result == accessible
    repository.list_accessible.assert_awaited_once_with(user.id)


async def test_get_returns_not_found_when_hackathon_is_not_visible(mocker):
    repository = mocker.Mock()
    repository.get_visible_by_public_id = mocker.AsyncMock(return_value=None)
    service = HackathonService(repository)

    with pytest.raises(HackathonNotFoundError):
        await service.get_hackathon(uuid.uuid4(), make_user())


async def test_owner_can_update_hackathon(mocker):
    owner = make_user(role=UserRole.ADMIN)
    hackathon = make_hackathon(organizer=owner)
    repository = mocker.Mock()
    repository.get_active_by_public_id = mocker.AsyncMock(return_value=hackathon)
    repository.commit = mocker.AsyncMock()
    repository.refresh_updated_at = mocker.AsyncMock()
    service = HackathonService(repository)

    result = await service.update_hackathon(
        hackathon.public_id,
        HackathonUpdate(name="  Updated Hackathon  ", capacity=None),
        owner,
    )

    assert result.name == "Updated Hackathon"
    assert result.capacity is None
    repository.commit.assert_awaited_once_with()
    repository.refresh_updated_at.assert_awaited_once_with(hackathon)


async def test_update_validates_values_merged_with_current_model(mocker):
    owner = make_user(role=UserRole.ADMIN)
    hackathon = make_hackathon(organizer=owner)
    repository = mocker.Mock()
    repository.get_active_by_public_id = mocker.AsyncMock(return_value=hackathon)
    service = HackathonService(repository)

    with pytest.raises(InvalidDateRangeError):
        await service.update_hackathon(
            hackathon.public_id,
            HackathonUpdate(start_date=hackathon.end_date + timedelta(hours=1)),
            owner,
        )


async def test_co_organizer_cannot_update_hackathon(mocker):
    owner = make_user(user_id=1, role=UserRole.ADMIN)
    co_organizer = make_user(user_id=2)
    hackathon = make_hackathon(organizer=owner, co_organizers=[co_organizer])
    repository = mocker.Mock()
    repository.get_active_by_public_id = mocker.AsyncMock(return_value=hackathon)
    service = HackathonService(repository)

    with pytest.raises(HackathonPermissionDeniedError):
        await service.update_hackathon(
            hackathon.public_id,
            HackathonUpdate(name="Forbidden update"),
            co_organizer,
        )


async def test_delete_requires_exact_confirmed_name(mocker):
    owner = make_user(role=UserRole.ADMIN)
    hackathon = make_hackathon(organizer=owner)
    repository = mocker.Mock()
    repository.get_active_by_public_id = mocker.AsyncMock(return_value=hackathon)
    repository.commit = mocker.AsyncMock()
    service = HackathonService(repository)

    with pytest.raises(InvalidConfirmNameError):
        await service.delete_hackathon(hackathon.public_id, "hackathon ai", owner)

    repository.commit.assert_not_awaited()


async def test_delete_marks_hackathon_as_deleted(mocker):
    owner = make_user(role=UserRole.ADMIN)
    hackathon = make_hackathon(organizer=owner)
    repository = mocker.Mock()
    repository.get_active_by_public_id = mocker.AsyncMock(return_value=hackathon)
    repository.commit = mocker.AsyncMock()
    service = HackathonService(repository)

    await service.delete_hackathon(hackathon.public_id, hackathon.name, owner)

    assert hackathon.is_deleted is True
    assert hackathon.deleted_at is not None
    repository.commit.assert_awaited_once_with()


async def test_registration_state_transitions(mocker):
    owner = make_user(role=UserRole.ADMIN)
    hackathon = make_hackathon(organizer=owner)
    repository = mocker.Mock()
    repository.get_active_by_public_id = mocker.AsyncMock(return_value=hackathon)
    repository.commit = mocker.AsyncMock()
    service = HackathonService(repository)

    await service.open_registration(hackathon.public_id, owner)
    assert hackathon.registration_open is True

    with pytest.raises(RegistrationAlreadyOpenError):
        await service.open_registration(hackathon.public_id, owner)

    await service.close_registration(hackathon.public_id, owner)
    assert hackathon.registration_open is False

    with pytest.raises(RegistrationAlreadyClosedError):
        await service.close_registration(hackathon.public_id, owner)


@pytest.fixture
def api_service(mocker):
    service = mocker.Mock()
    service.list_hackathons = mocker.AsyncMock(return_value=[])
    service.create_hackathon = mocker.AsyncMock()
    service.get_hackathon = mocker.AsyncMock()
    service.update_hackathon = mocker.AsyncMock()
    service.delete_hackathon = mocker.AsyncMock()
    service.open_registration = mocker.AsyncMock()
    service.close_registration = mocker.AsyncMock()
    return service


@pytest.fixture
async def api_client(api_service):
    admin = make_user(role=UserRole.ADMIN)

    async def override_current_user():
        return admin

    def override_hackathon_service():
        return api_service

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_hackathon_service] = override_hackathon_service

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client, admin

    app.dependency_overrides.clear()


async def test_create_endpoint_returns_expected_response(api_client, api_service):
    client, admin = api_client
    hackathon = make_hackathon(organizer=admin)
    api_service.create_hackathon.return_value = hackathon

    response = await client.post(
        "/api/hackathons",
        json={
            "name": "Hackathon AI",
            "description": "Build something useful",
            "start_date": "2026-09-02T10:00:00Z",
            "end_date": "2026-09-03T10:00:00Z",
            "capacity": 100,
            "max_team_size": 4,
        },
    )

    assert response.status_code == 201
    assert response.json()["public_id"] == str(hackathon.public_id)
    assert response.json()["access_level"] == "owner"
    assert response.json()["organizer"]["public_id"] == str(admin.public_id)


async def test_list_endpoint_marks_co_organizer_access(api_client, api_service):
    client, current_user = api_client
    owner = make_user(user_id=2, role=UserRole.ADMIN)
    hackathon = make_hackathon(organizer=owner, co_organizers=[current_user])
    api_service.list_hackathons.return_value = [hackathon]

    response = await client.get("/api/hackathons")

    assert response.status_code == 200
    assert response.json()[0]["access_level"] == "co_organizer"


async def test_list_endpoint_requires_access_token(api_client):
    client, _admin = api_client
    app.dependency_overrides.pop(get_current_user)

    response = await client.get("/api/hackathons")

    assert response.status_code == 401


async def test_regular_user_create_endpoint_returns_admin_required(api_client, api_service):
    client, _admin = api_client
    regular_user = make_user()

    async def override_regular_user():
        return regular_user

    app.dependency_overrides[get_current_user] = override_regular_user

    response = await client.post(
        "/api/hackathons",
        json={
            "name": "Hackathon AI",
            "start_date": "2026-09-02T10:00:00Z",
            "end_date": "2026-09-03T10:00:00Z",
            "max_team_size": 4,
        },
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "ADMIN_REQUIRED"
    api_service.create_hackathon.assert_not_awaited()


async def test_validation_error_has_stable_contract(api_client):
    client, _admin = api_client

    response = await client.post(
        "/api/hackathons",
        json={
            "name": "Hackathon AI",
            "start_date": "2026-09-02T10:00:00Z",
            "end_date": "2026-09-03T10:00:00Z",
            "max_team_size": 4,
            "organizer_id": 123,
        },
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (AdminRequiredError(), 403, "ADMIN_REQUIRED"),
        (HackathonNotFoundError(), 404, "HACKATHON_NOT_FOUND"),
        (HackathonPermissionDeniedError(), 403, "PERMISSION_DENIED"),
        (InvalidDateRangeError(), 422, "INVALID_DATE_RANGE"),
        (InvalidTeamSizeError(), 422, "INVALID_TEAM_SIZE"),
        (InvalidConfirmNameError(), 400, "INVALID_CONFIRM_NAME"),
        (RegistrationAlreadyOpenError(), 409, "REGISTRATION_ALREADY_OPEN"),
        (RegistrationAlreadyClosedError(), 409, "REGISTRATION_ALREADY_CLOSED"),
    ],
)
async def test_hackathon_errors_use_shared_api_contract(
    api_client,
    api_service,
    error,
    expected_status,
    expected_code,
):
    client, _admin = api_client
    api_service.get_hackathon.side_effect = error

    response = await client.get(f"/api/hackathons/{uuid.uuid4()}")

    assert response.status_code == expected_status
    assert response.json() == {
        "error_code": expected_code,
        "detail": error.detail,
    }


def test_hackathon_openapi_documents_shared_error_models():
    responses = app.openapi()["paths"]["/api/hackathons/{public_id}"]["get"]["responses"]

    assert responses["404"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse"
    }
    validation_schema = responses["422"]["content"]["application/json"]["schema"]
    assert validation_schema["anyOf"] == [
        {"$ref": "#/components/schemas/ErrorResponse"},
        {"$ref": "#/components/schemas/ValidationErrorResponse"},
    ]


async def test_delete_endpoint_returns_no_content(api_client, api_service):
    client, _admin = api_client
    public_id = uuid.uuid4()

    response = await client.request(
        "DELETE",
        f"/api/hackathons/{public_id}",
        json={"confirm_name": "Hackathon AI"},
    )

    assert response.status_code == 204
    assert response.content == b""
    api_service.delete_hackathon.assert_awaited_once()
