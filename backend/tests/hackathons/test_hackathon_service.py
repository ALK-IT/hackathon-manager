import uuid
from datetime import timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from src.auth.models import User, UserRole
from src.hackathons.exceptions import (
    AdminRequiredError,
    HackathonNotFoundError,
    InvalidConfirmNameError,
    InvalidDateRangeError,
    InvalidTeamSizeError,
    RegistrationAlreadyClosedError,
    RegistrationAlreadyOpenError,
)
from src.hackathons.repository import HackathonRepository
from src.hackathons.schemas import HackathonCreate, HackathonUpdate
from src.hackathons.service import HackathonService
from tests.hackathons.factories import NOW, HackathonFactory, UserFactory


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


@pytest.fixture
def repository(mocker) -> HackathonRepository:
    repository = mocker.Mock(spec=HackathonRepository)
    repository.list_active = mocker.AsyncMock(return_value=[])
    repository.list_managed_by_user = mocker.AsyncMock(return_value=[])
    repository.get_owned_by_public_id = mocker.AsyncMock()
    repository.get_active_by_public_id = mocker.AsyncMock()
    repository.add = mocker.AsyncMock()
    repository.commit = mocker.AsyncMock()
    repository.refresh_updated_at = mocker.AsyncMock()
    repository.rollback = mocker.AsyncMock()
    return repository


def test_create_schema_normalizes_text(create_data: HackathonCreate):
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


def test_update_schema_allows_only_capacity_to_be_null():
    assert HackathonUpdate(capacity=None).model_dump(exclude_unset=True) == {"capacity": None}

    with pytest.raises(ValidationError):
        HackathonUpdate(name=None)


async def test_admin_can_create_hackathon(
    repository: HackathonRepository,
    admin_user: User,
    create_data: HackathonCreate,
):
    service = HackathonService(repository)

    hackathon = await service.create_hackathon(create_data, admin_user)

    assert hackathon.organizer is admin_user
    assert hackathon.name == "Hackathon AI"
    assert hackathon.registration_open is False
    repository.add.assert_awaited_once_with(hackathon)
    repository.commit.assert_awaited_once_with()
    repository.rollback.assert_not_awaited()


async def test_regular_user_cannot_create_hackathon(
    repository: HackathonRepository,
    regular_user: User,
    create_data: HackathonCreate,
):
    service = HackathonService(repository)

    with pytest.raises(AdminRequiredError):
        await service.create_hackathon(create_data, regular_user)

    repository.add.assert_not_awaited()


async def test_create_rolls_back_database_error(
    repository: HackathonRepository,
    admin_user: User,
    create_data: HackathonCreate,
):
    repository.commit.side_effect = SQLAlchemyError("database unavailable")
    service = HackathonService(repository)

    with pytest.raises(SQLAlchemyError):
        await service.create_hackathon(create_data, admin_user)

    repository.rollback.assert_awaited_once_with()


async def test_list_returns_all_active_repository_results(
    repository: HackathonRepository,
    regular_user: User,
    hackathon_factory: HackathonFactory,
):
    active = [hackathon_factory(organizer=regular_user)]
    repository.list_active.return_value = active
    service = HackathonService(repository)

    assert await service.list_hackathons() == active
    repository.list_active.assert_awaited_once_with()


async def test_list_managed_returns_users_owned_and_co_organized_hackathons(
    repository: HackathonRepository,
    regular_user: User,
    hackathon_factory: HackathonFactory,
):
    managed = [hackathon_factory(organizer=regular_user)]
    repository.list_managed_by_user.return_value = managed
    service = HackathonService(repository)

    assert await service.list_managed_hackathons(regular_user) == managed
    repository.list_managed_by_user.assert_awaited_once_with(regular_user.id)


async def test_get_returns_active_hackathon_to_any_user(
    repository: HackathonRepository,
    regular_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=regular_user)
    repository.get_active_by_public_id.return_value = hackathon
    service = HackathonService(repository)

    result = await service.get_hackathon(hackathon.public_id)

    assert result is hackathon
    repository.get_active_by_public_id.assert_awaited_once_with(hackathon.public_id)


async def test_get_returns_not_found_when_hackathon_is_not_active(
    repository: HackathonRepository,
    regular_user: User,
):
    repository.get_active_by_public_id.return_value = None
    service = HackathonService(repository)

    with pytest.raises(HackathonNotFoundError):
        await service.get_hackathon(uuid.uuid4())


async def test_owner_can_update_hackathon(
    repository: HackathonRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    service = HackathonService(repository)

    result = await service.update_hackathon(
        hackathon.public_id,
        HackathonUpdate(name="  Updated Hackathon  ", capacity=None),
        admin_user,
    )

    assert result.name == "Updated Hackathon"
    assert result.capacity is None
    repository.commit.assert_awaited_once_with()
    repository.refresh_updated_at.assert_awaited_once_with(hackathon)


@pytest.mark.parametrize(
    ("update", "expected_exception"),
    [
        (
            lambda hackathon: HackathonUpdate(start_date=hackathon.end_date + timedelta(hours=1)),
            InvalidDateRangeError,
        ),
        (
            lambda _hackathon: HackathonUpdate(capacity=3, max_team_size=4),
            ValidationError,
        ),
    ],
)
async def test_update_rejects_invalid_ranges(
    repository: HackathonRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
    update,
    expected_exception,
):
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    service = HackathonService(repository)

    with pytest.raises(expected_exception):
        await service.update_hackathon(hackathon.public_id, update(hackathon), admin_user)

    repository.commit.assert_not_awaited()


async def test_update_rejects_team_size_larger_than_existing_capacity(
    repository: HackathonRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    service = HackathonService(repository)

    with pytest.raises(InvalidTeamSizeError):
        await service.update_hackathon(
            hackathon.public_id,
            HackathonUpdate(max_team_size=101),
            admin_user,
        )


async def test_co_organizer_cannot_distinguish_unowned_hackathon_from_missing_one(
    repository: HackathonRepository,
    user_factory: UserFactory,
    hackathon_factory: HackathonFactory,
):
    owner = user_factory(user_id=1, role=UserRole.ADMIN)
    co_organizer = user_factory(user_id=2)
    hackathon = hackathon_factory(organizer=owner, co_organizers=[co_organizer])
    repository.get_owned_by_public_id.return_value = None
    service = HackathonService(repository)

    with pytest.raises(HackathonNotFoundError):
        await service.update_hackathon(
            hackathon.public_id,
            HackathonUpdate(name="Forbidden update"),
            co_organizer,
        )

    repository.get_owned_by_public_id.assert_awaited_once_with(
        hackathon.public_id,
        co_organizer.id,
    )


async def test_delete_requires_exact_confirmed_name(
    repository: HackathonRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    service = HackathonService(repository)

    with pytest.raises(InvalidConfirmNameError):
        await service.delete_hackathon(hackathon.public_id, "hackathon ai", admin_user)

    repository.commit.assert_not_awaited()


async def test_delete_marks_hackathon_as_deleted(
    repository: HackathonRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    service = HackathonService(repository)

    await service.delete_hackathon(hackathon.public_id, hackathon.name, admin_user)

    assert hackathon.is_deleted is True
    assert hackathon.deleted_at is not None
    repository.commit.assert_awaited_once_with()


async def test_owner_can_open_and_close_registration(
    repository: HackathonRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    service = HackathonService(repository)

    await service.open_registration(hackathon.public_id, admin_user)
    assert hackathon.registration_open is True

    await service.close_registration(hackathon.public_id, admin_user)
    assert hackathon.registration_open is False
    assert repository.commit.await_count == 2


async def test_registration_rejects_repeated_state(
    repository: HackathonRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    service = HackathonService(repository)
    open_hackathon = hackathon_factory(organizer=admin_user, registration_open=True)
    repository.get_owned_by_public_id.return_value = open_hackathon

    with pytest.raises(RegistrationAlreadyOpenError):
        await service.open_registration(open_hackathon.public_id, admin_user)

    closed_hackathon = hackathon_factory(organizer=admin_user, registration_open=False)
    repository.get_owned_by_public_id.return_value = closed_hackathon

    with pytest.raises(RegistrationAlreadyClosedError):
        await service.close_registration(closed_hackathon.public_id, admin_user)
