import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from src.attendance.exceptions import (
    ActiveCheckInSessionConflictError,
    AttendancePermissionError,
    CheckInNotAllowedError,
    InvalidCheckInTokenError,
)
from src.attendance.models import CheckIn, CheckInSession
from src.attendance.schemas import CheckInRequest, SessionCreateRequest
from src.attendance.service import AttendanceService
from src.auth.models import UserRole
from src.registration.models import Registration, RegistrationStatus


@pytest.fixture
def attendance_repository(mocker):
    repository = mocker.Mock()
    repository.deactivate_active_session = mocker.AsyncMock()
    repository.create_check_in_session = mocker.AsyncMock()
    repository.get_valid_session_for_update = mocker.AsyncMock()
    repository.get_check_in_by_registration_id = mocker.AsyncMock()
    repository.get_check_ins_by_hackathon = mocker.AsyncMock(return_value=[])
    repository.get_accepted_registrations_with_attendance = mocker.AsyncMock(return_value=[])
    repository.create_check_in = mocker.AsyncMock()
    repository.commit = mocker.AsyncMock()
    repository.rollback = mocker.AsyncMock()
    return repository


@pytest.fixture
def hackathon_repository(mocker):
    repository = mocker.Mock()
    now = datetime.now(UTC)
    hackathon = SimpleNamespace(
        id=10,
        organizer_id=99,
        co_organizers=[],
        start_date=now - timedelta(hours=1),
        end_date=now + timedelta(hours=1),
    )
    repository.get_active_by_public_id = mocker.AsyncMock(return_value=hackathon)
    repository.get_active_by_public_id_for_update = mocker.AsyncMock(return_value=hackathon)
    return repository


@pytest.fixture
def registration_repository(mocker):
    repository = mocker.Mock()
    repository.get_accepted_by_hackathon_and_user_for_update = mocker.AsyncMock()
    return repository


@pytest.fixture
def attendance_service(
    attendance_repository,
    hackathon_repository,
    registration_repository,
):
    return AttendanceService(
        attendance_repository=attendance_repository,
        hackathon_repository=hackathon_repository,
        registration_repository=registration_repository,
    )


def make_registration() -> Registration:
    return Registration(
        id=30,
        user_id=20,
        hackathon_id=10,
        status=RegistrationStatus.ACCEPTED,
    )


def make_session(token: str) -> CheckInSession:
    return CheckInSession(
        id=40,
        hackathon_id=10,
        token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
        created_by_id=99,
    )


def make_integrity_error(constraint_name: str) -> IntegrityError:
    original_error = RuntimeError("unique constraint violation")
    original_error.constraint_name = constraint_name  # type: ignore[attr-defined]
    return IntegrityError("INSERT", {}, original_error)


async def test_create_session_maps_active_session_constraint_to_conflict(
    attendance_service,
    attendance_repository,
):
    attendance_repository.create_check_in_session.side_effect = make_integrity_error(
        "uq_check_in_sessions_one_active_per_hackathon"
    )

    with pytest.raises(ActiveCheckInSessionConflictError):
        await attendance_service.create_check_in_session(
            uuid.uuid4(),
            SimpleNamespace(id=20, role=UserRole.ADMIN),
            SessionCreateRequest(),
        )

    attendance_repository.rollback.assert_awaited_once_with()
    attendance_repository.commit.assert_not_awaited()


async def test_create_session_does_not_mask_other_integrity_errors(
    attendance_service,
    attendance_repository,
):
    integrity_error = make_integrity_error("different_constraint")
    attendance_repository.create_check_in_session.side_effect = integrity_error

    with pytest.raises(IntegrityError) as exc_info:
        await attendance_service.create_check_in_session(
            uuid.uuid4(),
            SimpleNamespace(id=20, role=UserRole.ADMIN),
            SessionCreateRequest(),
        )

    assert exc_info.value is integrity_error
    attendance_repository.rollback.assert_awaited_once_with()
    attendance_repository.commit.assert_not_awaited()


async def test_check_in_current_user_rejects_user_without_accepted_registration(
    attendance_service,
    attendance_repository,
    registration_repository,
):
    registration_repository.get_accepted_by_hackathon_and_user_for_update.return_value = None

    with pytest.raises(CheckInNotAllowedError):
        await attendance_service.check_in_current_user(
            uuid.uuid4(),
            SimpleNamespace(id=20),
            CheckInRequest(token="a" * 32),
        )

    attendance_repository.get_valid_session_for_update.assert_not_awaited()
    attendance_repository.create_check_in.assert_not_awaited()


async def test_check_in_current_user_rejects_invalid_or_expired_token(
    attendance_service,
    attendance_repository,
    registration_repository,
):
    token = "b" * 32
    registration_repository.get_accepted_by_hackathon_and_user_for_update.return_value = (
        make_registration()
    )
    attendance_repository.get_valid_session_for_update.return_value = None

    with pytest.raises(InvalidCheckInTokenError):
        await attendance_service.check_in_current_user(
            uuid.uuid4(),
            SimpleNamespace(id=20),
            CheckInRequest(token=token),
        )

    call = attendance_repository.get_valid_session_for_update.await_args
    assert call.args[0] == 10
    assert call.args[1] == hashlib.sha256(token.encode("utf-8")).hexdigest()
    attendance_repository.create_check_in.assert_not_awaited()


async def test_check_in_current_user_returns_existing_check_in(
    attendance_service,
    attendance_repository,
    registration_repository,
):
    token = "c" * 32
    registration = make_registration()
    check_in_session = make_session(token)
    existing_check_in = CheckIn(
        id=50,
        public_id=uuid.uuid4(),
        registration=registration,
        session=check_in_session,
        checked_in_at=datetime.now(UTC),
    )
    registration_repository.get_accepted_by_hackathon_and_user_for_update.return_value = (
        registration
    )
    attendance_repository.get_valid_session_for_update.return_value = check_in_session
    attendance_repository.get_check_in_by_registration_id.return_value = existing_check_in

    result = await attendance_service.check_in_current_user(
        uuid.uuid4(),
        SimpleNamespace(id=20),
        CheckInRequest(token=token),
    )

    assert result is existing_check_in
    attendance_repository.create_check_in.assert_not_awaited()
    attendance_repository.commit.assert_not_awaited()


async def test_check_in_current_user_creates_check_in(
    attendance_service,
    attendance_repository,
    registration_repository,
):
    token = "d" * 32
    registration = make_registration()
    check_in_session = make_session(token)
    registration_repository.get_accepted_by_hackathon_and_user_for_update.return_value = (
        registration
    )
    attendance_repository.get_valid_session_for_update.return_value = check_in_session
    attendance_repository.get_check_in_by_registration_id.return_value = None

    result = await attendance_service.check_in_current_user(
        uuid.uuid4(),
        SimpleNamespace(id=20),
        CheckInRequest(token=token),
    )

    assert result.registration is registration
    assert result.session is check_in_session
    attendance_repository.create_check_in.assert_awaited_once_with(result)
    attendance_repository.commit.assert_awaited_once_with()
    attendance_repository.rollback.assert_not_awaited()


async def test_check_in_current_user_rolls_back_repository_error(
    attendance_service,
    attendance_repository,
    registration_repository,
):
    token = "e" * 32
    registration_repository.get_accepted_by_hackathon_and_user_for_update.return_value = (
        make_registration()
    )
    attendance_repository.get_valid_session_for_update.return_value = make_session(token)
    attendance_repository.get_check_in_by_registration_id.return_value = None
    attendance_repository.create_check_in.side_effect = RuntimeError("insert failed")

    with pytest.raises(RuntimeError, match="insert failed"):
        await attendance_service.check_in_current_user(
            uuid.uuid4(),
            SimpleNamespace(id=20),
            CheckInRequest(token=token),
        )

    attendance_repository.rollback.assert_awaited_once_with()
    attendance_repository.commit.assert_not_awaited()


async def test_list_check_ins_rejects_user_without_management_permission(
    attendance_service,
    attendance_repository,
    mocker,
):
    mocker.patch("src.attendance.service.can_manage_hackathon", return_value=False)

    with pytest.raises(AttendancePermissionError):
        await attendance_service.list_check_ins(
            uuid.uuid4(),
            SimpleNamespace(id=20),
        )

    attendance_repository.get_check_ins_by_hackathon.assert_not_awaited()


async def test_list_check_ins_returns_repository_models(
    attendance_service,
    attendance_repository,
    mocker,
):
    checked_in_at = datetime.now(UTC)
    participant = SimpleNamespace(
        public_id=uuid.uuid4(),
        name="Jan Kowalski",
        email="jan@example.com",
        created_at=checked_in_at - timedelta(days=30),
    )
    registration = SimpleNamespace(
        public_id=uuid.uuid4(),
        user=participant,
    )
    check_in = SimpleNamespace(
        public_id=uuid.uuid4(),
        checked_in_at=checked_in_at,
        registration=registration,
    )
    mocker.patch("src.attendance.service.can_manage_hackathon", return_value=True)
    attendance_repository.get_check_ins_by_hackathon.return_value = [check_in]

    result = await attendance_service.list_check_ins(
        uuid.uuid4(),
        SimpleNamespace(id=20),
    )

    assert len(result) == 1
    assert result == [check_in]


async def test_list_attendance_returns_accepted_registrations(
    attendance_service,
    attendance_repository,
    mocker,
):
    registrations = [SimpleNamespace(id=30), SimpleNamespace(id=31)]
    mocker.patch("src.attendance.service.can_manage_hackathon", return_value=True)
    attendance_repository.get_accepted_registrations_with_attendance.return_value = registrations

    result = await attendance_service.list_attendance(
        uuid.uuid4(),
        SimpleNamespace(id=20),
    )

    assert result == registrations
    attendance_repository.get_accepted_registrations_with_attendance.assert_awaited_once_with(10)


async def test_list_attendance_rejects_user_without_management_permission(
    attendance_service,
    attendance_repository,
    mocker,
):
    mocker.patch("src.attendance.service.can_manage_hackathon", return_value=False)

    with pytest.raises(AttendancePermissionError):
        await attendance_service.list_attendance(
            uuid.uuid4(),
            SimpleNamespace(id=20),
        )

    attendance_repository.get_accepted_registrations_with_attendance.assert_not_awaited()
