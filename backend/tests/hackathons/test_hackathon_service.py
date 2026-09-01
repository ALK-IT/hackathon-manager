import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.auth.models import User, UserRole
from src.auth.repository import UserRepository
from src.common.rate_limit import FixedWindowRateLimiter
from src.hackathons.constants import CO_ORGANIZER_SEARCH_RESULT_LIMIT
from src.hackathons.exceptions import (
    AdminRequiredError,
    CoOrganizerAlreadyAssignedError,
    CoOrganizerSearchRateLimitExceededError,
    CoOrganizerUserNotFoundError,
    HackathonNotFoundError,
    InvalidConfirmNameError,
    InvalidDateRangeError,
    InvalidRegistrationDeadlineError,
    InvalidRegistrationWindowError,
    InvalidTeamSizeError,
    OrganizerCannotBeCoOrganizerError,
    RegistrationAlreadyClosedError,
    RegistrationAlreadyOpenError,
    RegistrationDeadlinePassedError,
)
from src.hackathons.repository import HackathonRepository
from src.hackathons.schemas import CoOrganizerAddRequest, HackathonCreate, HackathonUpdate
from src.hackathons.service import HackathonService
from tests.hackathons.factories import NOW, HackathonFactory, UserFactory


class ConstraintViolation(Exception):
    def __init__(self, constraint_name: str):
        self.constraint_name = constraint_name
        super().__init__(constraint_name)


@pytest.fixture
def create_data() -> HackathonCreate:
    return HackathonCreate(
        name="  Hackathon AI  ",
        description="  Build something useful  ",
        start_date=NOW + timedelta(days=1),
        end_date=NOW + timedelta(days=2),
        registration_opens_at=NOW - timedelta(days=2),
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


@pytest.fixture
def user_repository(mocker) -> UserRepository:
    repository = mocker.Mock(spec=UserRepository)
    repository.get_by_public_id = mocker.AsyncMock()
    repository.search_by_name = mocker.AsyncMock(return_value=[])
    return repository


def make_service(
    repository: HackathonRepository,
    user_repository: UserRepository | None = None,
    rate_limiter: FixedWindowRateLimiter | None = None,
) -> HackathonService:
    if rate_limiter is None:
        rate_limiter = Mock(spec=FixedWindowRateLimiter)
        rate_limiter.consume = AsyncMock(return_value=True)
    return HackathonService(
        repository,
        user_repository or Mock(spec=UserRepository),
        rate_limiter,
    )


def test_create_schema_normalizes_text(create_data: HackathonCreate):
    assert create_data.name == "Hackathon AI"
    assert create_data.description == "Build something useful"
    assert create_data.registration_deadline == create_data.start_date - timedelta(hours=48)


def test_create_schema_rejects_invalid_date_range():
    with pytest.raises(ValidationError):
        HackathonCreate(
            name="Hackathon AI",
            start_date=NOW,
            end_date=NOW,
            registration_opens_at=NOW - timedelta(days=3),
            max_team_size=4,
        )


def test_create_schema_rejects_team_size_greater_than_capacity():
    with pytest.raises(ValidationError):
        HackathonCreate(
            name="Hackathon AI",
            start_date=NOW,
            end_date=NOW + timedelta(days=1),
            registration_opens_at=NOW - timedelta(days=3),
            capacity=3,
            max_team_size=4,
        )


def test_create_schema_rejects_datetime_without_timezone():
    with pytest.raises(ValidationError):
        HackathonCreate(
            name="Hackathon AI",
            start_date=NOW.replace(tzinfo=None),
            end_date=(NOW + timedelta(days=1)).replace(tzinfo=None),
            registration_opens_at=NOW - timedelta(days=3),
            max_team_size=4,
        )


def test_create_schema_rejects_deadline_not_before_start():
    with pytest.raises(ValidationError):
        HackathonCreate(
            name="Hackathon AI",
            start_date=NOW + timedelta(days=1),
            end_date=NOW + timedelta(days=2),
            registration_opens_at=NOW - timedelta(days=1),
            registration_deadline=NOW + timedelta(days=1),
            max_team_size=4,
        )


def test_create_schema_rejects_opening_not_before_deadline():
    with pytest.raises(ValidationError):
        HackathonCreate(
            name="Hackathon AI",
            start_date=NOW + timedelta(days=7),
            end_date=NOW + timedelta(days=8),
            registration_opens_at=NOW + timedelta(days=5),
            registration_deadline=NOW + timedelta(days=5),
            max_team_size=4,
        )


def test_update_schema_rejects_empty_payload():
    with pytest.raises(ValidationError):
        HackathonUpdate()


def test_update_schema_allows_only_capacity_to_be_null():
    assert HackathonUpdate(capacity=None).model_dump(exclude_unset=True) == {"capacity": None}

    with pytest.raises(ValidationError):
        HackathonUpdate(name=None)

    with pytest.raises(ValidationError):
        HackathonUpdate(teams_enabled=None)


async def test_admin_can_create_hackathon(
    repository: HackathonRepository,
    admin_user: User,
    create_data: HackathonCreate,
):
    service = make_service(repository)

    hackathon = await service.create_hackathon(create_data, admin_user)

    assert hackathon.organizer is admin_user
    assert hackathon.name == "Hackathon AI"
    assert hackathon.registration_deadline == create_data.start_date - timedelta(hours=48)
    assert hackathon.registration_open is True
    assert hackathon.teams_enabled is True
    repository.add.assert_awaited_once_with(hackathon)
    repository.commit.assert_awaited_once_with()
    repository.rollback.assert_not_awaited()


async def test_regular_user_cannot_create_hackathon(
    repository: HackathonRepository,
    regular_user: User,
    create_data: HackathonCreate,
):
    service = make_service(repository)

    with pytest.raises(AdminRequiredError):
        await service.create_hackathon(create_data, regular_user)

    repository.add.assert_not_awaited()


async def test_create_rolls_back_database_error(
    repository: HackathonRepository,
    admin_user: User,
    create_data: HackathonCreate,
):
    repository.commit.side_effect = SQLAlchemyError("database unavailable")
    service = make_service(repository)

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
    service = make_service(repository)

    assert await service.list_hackathons() == active
    repository.list_active.assert_awaited_once_with(
        upcoming=None,
        registration_open=None,
    )


async def test_list_passes_filters_to_repository(repository: HackathonRepository):
    service = make_service(repository)

    await service.list_hackathons(upcoming=True, registration_open=False)

    repository.list_active.assert_awaited_once_with(
        upcoming=True,
        registration_open=False,
    )


async def test_list_managed_returns_users_owned_and_co_organized_hackathons(
    repository: HackathonRepository,
    regular_user: User,
    hackathon_factory: HackathonFactory,
):
    managed = [hackathon_factory(organizer=regular_user)]
    repository.list_managed_by_user.return_value = managed
    service = make_service(repository)

    assert await service.list_managed_hackathons(regular_user) == managed
    repository.list_managed_by_user.assert_awaited_once_with(regular_user.id)


async def test_get_returns_active_hackathon_to_any_user(
    repository: HackathonRepository,
    regular_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=regular_user)
    repository.get_active_by_public_id.return_value = hackathon
    service = make_service(repository)

    result = await service.get_hackathon(hackathon.public_id)

    assert result is hackathon
    repository.get_active_by_public_id.assert_awaited_once_with(hackathon.public_id)


async def test_get_returns_not_found_when_hackathon_is_not_active(
    repository: HackathonRepository,
    regular_user: User,
):
    repository.get_active_by_public_id.return_value = None
    service = make_service(repository)

    with pytest.raises(HackathonNotFoundError):
        await service.get_hackathon(uuid.uuid4())


async def test_owner_can_update_hackathon(
    repository: HackathonRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    service = make_service(repository)

    result = await service.update_hackathon(
        hackathon.public_id,
        HackathonUpdate(name="  Updated Hackathon  ", capacity=None, teams_enabled=False),
        admin_user,
    )

    assert result.name == "Updated Hackathon"
    assert result.capacity is None
    assert result.teams_enabled is False
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
        (
            lambda hackathon: HackathonUpdate(
                registration_deadline=hackathon.start_date + timedelta(hours=1)
            ),
            InvalidRegistrationDeadlineError,
        ),
        (
            lambda hackathon: HackathonUpdate(
                registration_opens_at=hackathon.registration_deadline + timedelta(hours=1)
            ),
            InvalidRegistrationWindowError,
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
    service = make_service(repository)

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
    service = make_service(repository)

    with pytest.raises(InvalidTeamSizeError):
        await service.update_hackathon(
            hackathon.public_id,
            HackathonUpdate(max_team_size=101),
            admin_user,
        )


async def test_owner_without_admin_role_can_update_registration_window(
    repository: HackathonRepository,
    regular_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=regular_user)
    hackathon.registration_open = False
    new_opens_at = NOW + timedelta(days=1)
    new_deadline = hackathon.start_date - timedelta(hours=24)
    repository.get_owned_by_public_id.return_value = hackathon
    service = make_service(repository)

    result = await service.update_hackathon(
        hackathon.public_id,
        HackathonUpdate(
            registration_opens_at=new_opens_at,
            registration_deadline=new_deadline,
        ),
        regular_user,
    )

    assert result.registration_opens_at == new_opens_at
    assert result.registration_deadline == new_deadline
    assert result.registration_open is True
    repository.get_owned_by_public_id.assert_awaited_once_with(
        hackathon.public_id,
        regular_user.id,
    )
    repository.commit.assert_awaited_once_with()


async def test_co_organizer_cannot_distinguish_unowned_hackathon_from_missing_one(
    repository: HackathonRepository,
    user_factory: UserFactory,
    hackathon_factory: HackathonFactory,
):
    owner = user_factory(user_id=1, role=UserRole.ADMIN)
    co_organizer = user_factory(user_id=2)
    hackathon = hackathon_factory(organizer=owner, co_organizers=[co_organizer])
    repository.get_owned_by_public_id.return_value = None
    service = make_service(repository)

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
    service = make_service(repository)

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
    service = make_service(repository)

    await service.delete_hackathon(hackathon.public_id, hackathon.name, admin_user)

    assert hackathon.is_deleted is True
    assert hackathon.deleted_at is not None
    repository.commit.assert_awaited_once_with()


async def test_owner_can_add_co_organizer(
    repository: HackathonRepository,
    user_repository: UserRepository,
    admin_user: User,
    user_factory: UserFactory,
    hackathon_factory: HackathonFactory,
):
    co_organizer = user_factory(user_id=2)
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    user_repository.get_by_public_id.return_value = co_organizer
    service = make_service(repository, user_repository)
    data = CoOrganizerAddRequest(user_public_id=co_organizer.public_id)

    result = await service.add_co_organizer(hackathon.public_id, data, admin_user)

    assert result is hackathon
    assert hackathon.co_organizers == [co_organizer]
    repository.get_owned_by_public_id.assert_awaited_once_with(
        hackathon.public_id,
        admin_user.id,
    )
    user_repository.get_by_public_id.assert_awaited_once_with(co_organizer.public_id)
    repository.commit.assert_awaited_once_with()
    repository.rollback.assert_not_awaited()


async def test_add_co_organizer_hides_unowned_hackathon_before_user_lookup(
    repository: HackathonRepository,
    user_repository: UserRepository,
    regular_user: User,
):
    repository.get_owned_by_public_id.return_value = None
    service = make_service(repository, user_repository)

    with pytest.raises(HackathonNotFoundError):
        await service.add_co_organizer(
            uuid.uuid4(),
            CoOrganizerAddRequest(user_public_id=uuid.uuid4()),
            regular_user,
        )

    user_repository.get_by_public_id.assert_not_awaited()
    repository.commit.assert_not_awaited()


async def test_add_co_organizer_rejects_missing_user(
    repository: HackathonRepository,
    user_repository: UserRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    user_repository.get_by_public_id.return_value = None
    service = make_service(repository, user_repository)

    with pytest.raises(CoOrganizerUserNotFoundError):
        await service.add_co_organizer(
            hackathon.public_id,
            CoOrganizerAddRequest(user_public_id=uuid.uuid4()),
            admin_user,
        )

    repository.commit.assert_not_awaited()


async def test_add_co_organizer_rejects_owner(
    repository: HackathonRepository,
    user_repository: UserRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    user_repository.get_by_public_id.return_value = admin_user
    service = make_service(repository, user_repository)

    with pytest.raises(OrganizerCannotBeCoOrganizerError):
        await service.add_co_organizer(
            hackathon.public_id,
            CoOrganizerAddRequest(user_public_id=admin_user.public_id),
            admin_user,
        )

    assert hackathon.co_organizers == []
    repository.commit.assert_not_awaited()


async def test_add_co_organizer_rejects_duplicate(
    repository: HackathonRepository,
    user_repository: UserRepository,
    admin_user: User,
    user_factory: UserFactory,
    hackathon_factory: HackathonFactory,
):
    co_organizer = user_factory(user_id=2)
    hackathon = hackathon_factory(
        organizer=admin_user,
        co_organizers=[co_organizer],
    )
    repository.get_owned_by_public_id.return_value = hackathon
    user_repository.get_by_public_id.return_value = co_organizer
    service = make_service(repository, user_repository)

    with pytest.raises(CoOrganizerAlreadyAssignedError):
        await service.add_co_organizer(
            hackathon.public_id,
            CoOrganizerAddRequest(user_public_id=co_organizer.public_id),
            admin_user,
        )

    assert hackathon.co_organizers == [co_organizer]
    repository.commit.assert_not_awaited()


async def test_add_co_organizer_maps_concurrent_duplicate_to_domain_error(
    repository: HackathonRepository,
    user_repository: UserRepository,
    admin_user: User,
    user_factory: UserFactory,
    hackathon_factory: HackathonFactory,
):
    co_organizer = user_factory(user_id=2)
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    user_repository.get_by_public_id.return_value = co_organizer
    repository.commit.side_effect = IntegrityError(
        "INSERT INTO hackathon_co_organizers",
        {},
        ConstraintViolation("hackathon_co_organizers_pkey"),
    )
    service = make_service(repository, user_repository)

    with pytest.raises(CoOrganizerAlreadyAssignedError):
        await service.add_co_organizer(
            hackathon.public_id,
            CoOrganizerAddRequest(user_public_id=co_organizer.public_id),
            admin_user,
        )

    repository.rollback.assert_awaited_once_with()


async def test_add_co_organizer_rolls_back_database_error(
    repository: HackathonRepository,
    user_repository: UserRepository,
    admin_user: User,
    user_factory: UserFactory,
    hackathon_factory: HackathonFactory,
):
    co_organizer = user_factory(user_id=2)
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    user_repository.get_by_public_id.return_value = co_organizer
    repository.commit.side_effect = SQLAlchemyError("database unavailable")
    service = make_service(repository, user_repository)

    with pytest.raises(SQLAlchemyError):
        await service.add_co_organizer(
            hackathon.public_id,
            CoOrganizerAddRequest(user_public_id=co_organizer.public_id),
            admin_user,
        )

    repository.rollback.assert_awaited_once_with()


async def test_owner_can_search_for_co_organizer_candidates(
    repository: HackathonRepository,
    user_repository: UserRepository,
    admin_user: User,
    user_factory: UserFactory,
    hackathon_factory: HackathonFactory,
):
    existing_co_organizer = user_factory(user_id=2)
    candidate = user_factory(user_id=3)
    candidate.name = "Jan Kowalski"
    hackathon = hackathon_factory(
        organizer=admin_user,
        co_organizers=[existing_co_organizer],
    )
    repository.get_owned_by_public_id.return_value = hackathon
    user_repository.search_by_name.return_value = [candidate]
    service = make_service(repository, user_repository)

    result = await service.get_co_organizer_candidates(
        hackathon.public_id,
        admin_user,
        "  jan  ",
    )

    assert result == [candidate]
    service.co_organizer_search_rate_limiter.consume.assert_awaited_once_with(
        str(admin_user.public_id)
    )
    user_repository.search_by_name.assert_awaited_once_with(
        "jan",
        {admin_user.id, existing_co_organizer.id},
        limit=CO_ORGANIZER_SEARCH_RESULT_LIMIT,
    )


async def test_candidate_search_rejects_request_after_rate_limit_is_exceeded(
    repository: HackathonRepository,
    user_repository: UserRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
    mocker,
):
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    rate_limiter = mocker.Mock(spec=FixedWindowRateLimiter)
    rate_limiter.consume = mocker.AsyncMock(return_value=False)
    service = make_service(repository, user_repository, rate_limiter)

    with pytest.raises(CoOrganizerSearchRateLimitExceededError):
        await service.get_co_organizer_candidates(
            hackathon.public_id,
            admin_user,
            "Jan",
        )

    rate_limiter.consume.assert_awaited_once_with(str(admin_user.public_id))
    user_repository.search_by_name.assert_not_awaited()


async def test_candidate_search_hides_unowned_hackathon_before_user_lookup(
    repository: HackathonRepository,
    user_repository: UserRepository,
    regular_user: User,
    mocker,
):
    repository.get_owned_by_public_id.return_value = None
    rate_limiter = mocker.Mock(spec=FixedWindowRateLimiter)
    rate_limiter.consume = mocker.AsyncMock(return_value=True)
    service = make_service(repository, user_repository, rate_limiter)

    with pytest.raises(HackathonNotFoundError):
        await service.get_co_organizer_candidates(
            uuid.uuid4(),
            regular_user,
            "Jan",
        )

    rate_limiter.consume.assert_not_awaited()
    user_repository.search_by_name.assert_not_awaited()


async def test_owner_can_open_and_close_registration(
    repository: HackathonRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(organizer=admin_user)
    repository.get_owned_by_public_id.return_value = hackathon
    service = make_service(repository)

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
    service = make_service(repository)
    open_hackathon = hackathon_factory(organizer=admin_user, registration_open=True)
    open_hackathon.registration_opens_at = datetime.now(UTC) - timedelta(hours=1)
    repository.get_owned_by_public_id.return_value = open_hackathon

    with pytest.raises(RegistrationAlreadyOpenError):
        await service.open_registration(open_hackathon.public_id, admin_user)

    closed_hackathon = hackathon_factory(organizer=admin_user, registration_open=False)
    repository.get_owned_by_public_id.return_value = closed_hackathon

    with pytest.raises(RegistrationAlreadyClosedError):
        await service.close_registration(closed_hackathon.public_id, admin_user)


async def test_registration_cannot_be_opened_after_deadline(
    repository: HackathonRepository,
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    hackathon = hackathon_factory(
        organizer=admin_user,
        registration_deadline=datetime.now(UTC) - timedelta(seconds=1),
    )
    repository.get_owned_by_public_id.return_value = hackathon
    service = make_service(repository)

    with pytest.raises(RegistrationDeadlinePassedError):
        await service.open_registration(hackathon.public_id, admin_user)

    assert hackathon.registration_open is False
    repository.commit.assert_not_awaited()


def test_registration_is_open_only_inside_scheduled_window(
    admin_user: User,
    hackathon_factory: HackathonFactory,
):
    opens_at = NOW
    deadline = NOW + timedelta(days=1)
    hackathon = hackathon_factory(
        organizer=admin_user,
        registration_open=True,
        registration_opens_at=opens_at,
        registration_deadline=deadline,
    )

    assert hackathon.is_registration_open_at(opens_at - timedelta(seconds=1)) is False
    assert hackathon.is_registration_open_at(opens_at) is True
    assert hackathon.is_registration_open_at(deadline) is False
