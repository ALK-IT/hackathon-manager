import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from src.attendance.exceptions import CheckInNotAllowedError, InvalidCheckInTokenError
from src.attendance.models import CheckIn, CheckInSession
from src.attendance.schemas import CheckInRequest
from src.attendance.service import AttendanceService
from src.registration.models import Registration, RegistrationStatus


@pytest.fixture
def attendance_repository(mocker):
    repository = mocker.Mock()
    repository.get_valid_session_for_update = mocker.AsyncMock()
    repository.get_check_in_by_registration_id = mocker.AsyncMock()
    repository.join_session = mocker.AsyncMock()
    repository.commit = mocker.AsyncMock()
    repository.rollback = mocker.AsyncMock()
    return repository


@pytest.fixture
def hackathon_repository(mocker):
    repository = mocker.Mock()
    repository.get_active_by_public_id = mocker.AsyncMock(return_value=SimpleNamespace(id=10))
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


async def test_join_session_rejects_user_without_accepted_registration(
    attendance_service,
    attendance_repository,
    registration_repository,
):
    registration_repository.get_accepted_by_hackathon_and_user_for_update.return_value = None

    with pytest.raises(CheckInNotAllowedError):
        await attendance_service.join_session(
            uuid.uuid4(),
            SimpleNamespace(id=20),
            CheckInRequest(token="a" * 32),
        )

    attendance_repository.get_valid_session_for_update.assert_not_awaited()
    attendance_repository.join_session.assert_not_awaited()


async def test_join_session_rejects_invalid_or_expired_token(
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
        await attendance_service.join_session(
            uuid.uuid4(),
            SimpleNamespace(id=20),
            CheckInRequest(token=token),
        )

    call = attendance_repository.get_valid_session_for_update.await_args
    assert call.args[0] == 10
    assert call.args[1] == hashlib.sha256(token.encode("utf-8")).hexdigest()
    attendance_repository.join_session.assert_not_awaited()


async def test_join_session_returns_existing_check_in(
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

    result = await attendance_service.join_session(
        uuid.uuid4(),
        SimpleNamespace(id=20),
        CheckInRequest(token=token),
    )

    assert result is existing_check_in
    attendance_repository.join_session.assert_not_awaited()
    attendance_repository.commit.assert_not_awaited()


async def test_join_session_creates_check_in(
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

    result = await attendance_service.join_session(
        uuid.uuid4(),
        SimpleNamespace(id=20),
        CheckInRequest(token=token),
    )

    assert result.registration is registration
    assert result.session is check_in_session
    attendance_repository.join_session.assert_awaited_once_with(result)
    attendance_repository.commit.assert_awaited_once_with()
    attendance_repository.rollback.assert_not_awaited()


async def test_join_session_rolls_back_repository_error(
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
    attendance_repository.join_session.side_effect = RuntimeError("insert failed")

    with pytest.raises(RuntimeError, match="insert failed"):
        await attendance_service.join_session(
            uuid.uuid4(),
            SimpleNamespace(id=20),
            CheckInRequest(token=token),
        )

    attendance_repository.rollback.assert_awaited_once_with()
    attendance_repository.commit.assert_not_awaited()
