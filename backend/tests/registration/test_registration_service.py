import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from src.auth.models import User, UserRole
from src.hackathons.exceptions import HackathonNotFoundError
from src.hackathons.models import Hackathon
from src.registration.exceptions import (
    InvalidPermission,
    InvalidRegistrationQuestionError,
    MissingRequiredAnswersError,
    QuestionNotFoundError,
    RegistrationAlreadyExistsError,
    RegistrationClosedError,
    RegistrationNotFoundError,
)
from src.registration.models import Registration, RegistrationQuestion, RegistrationStatus
from src.registration.schema import (
    RegistrationCreate,
    RegistrationQuestionBulkCreate,
    RegistrationQuestionCreate,
)
from src.registration.service import RegistrationQuestionService, RegistrationService


def make_user(
    *,
    user_id: int = 1,
    role: UserRole = UserRole.USER,
):
    return SimpleNamespace(id=user_id, public_id=uuid.uuid4(), role=role)


def make_question(
    *,
    question_id: int = 1,
    is_required: bool = True,
):
    return SimpleNamespace(
        id=question_id,
        public_id=uuid.uuid4(),
        is_required=is_required,
    )


def make_hackathon() -> Hackathon:
    now = datetime.now(UTC)
    start_date = now + timedelta(days=1)
    return Hackathon(
        name="AI Hackathon",
        organizer_id=1,
        start_date=start_date,
        end_date=start_date + timedelta(days=2),
        registration_opens_at=now - timedelta(hours=1),
        registration_deadline=now + timedelta(hours=12),
        max_team_size=4,
    )


def registration_window(*, is_open: bool, hackathon_id: int = 10):
    return SimpleNamespace(
        id=hackathon_id,
        registration_open=is_open,
        is_registration_open_at=lambda: is_open,
    )


def registration_data(*questions) -> RegistrationCreate:
    return RegistrationCreate(
        answers=[
            {
                "question_public_id": question.public_id,
                "content": f"Answer {index}",
            }
            for index, question in enumerate(questions, start=1)
        ]
    )


@pytest.fixture
def question_repository(mocker):
    repository = mocker.Mock()
    repository.get_by_public_id = mocker.AsyncMock()
    repository.get_by_hackathon_public_id = mocker.AsyncMock(return_value=[])
    repository.create = mocker.AsyncMock()
    repository.create_many = mocker.AsyncMock()
    repository.delete = mocker.AsyncMock()
    repository.commit = mocker.AsyncMock()
    repository.rollback = mocker.AsyncMock()
    return repository


@pytest.fixture
def hackathon_repository(mocker):
    repository = mocker.Mock()
    repository.get_active_by_public_id = mocker.AsyncMock()
    return repository


@pytest.fixture
def registration_repository(mocker):
    repository = mocker.Mock()
    repository.get_active_by_public_id = mocker.AsyncMock()
    repository.get_by_hackathon = mocker.AsyncMock(return_value=[])
    repository.get_by_hackathon_and_user = mocker.AsyncMock()
    repository.create = mocker.AsyncMock()
    repository.update_status = mocker.AsyncMock()
    repository.delete = mocker.AsyncMock()
    repository.commit = mocker.AsyncMock()
    repository.rollback = mocker.AsyncMock()
    return repository


@pytest.fixture
def question_service(question_repository, hackathon_repository):
    return RegistrationQuestionService(
        question_repository=question_repository,
        hackathon_repository=hackathon_repository,
    )


@pytest.fixture
def registration_service(
    registration_repository,
    question_repository,
    hackathon_repository,
):
    return RegistrationService(
        registration_repository=registration_repository,
        question_repository=question_repository,
        hackathon_repository=hackathon_repository,
    )


async def test_delete_question_raises_when_question_does_not_exist(
    question_service,
    question_repository,
):
    question_repository.get_by_public_id.return_value = None

    with pytest.raises(QuestionNotFoundError):
        await question_service.delete_question(
            uuid.uuid4(),
            make_user(role=UserRole.ADMIN),
        )

    question_repository.delete.assert_not_awaited()
    question_repository.commit.assert_not_awaited()


async def test_delete_question_rejects_regular_user(
    question_service,
    question_repository,
):
    question_repository.get_by_public_id.return_value = SimpleNamespace(
        hackathon=SimpleNamespace(
            organizer_id=10,
            co_organizers=[SimpleNamespace(id=20)],
        )
    )

    with pytest.raises(InvalidPermission):
        await question_service.delete_question(uuid.uuid4(), make_user())

    question_repository.delete.assert_not_awaited()
    question_repository.commit.assert_not_awaited()


async def test_admin_can_delete_question(
    question_service,
    question_repository,
):
    question = SimpleNamespace(hackathon=SimpleNamespace())
    question_repository.get_by_public_id.return_value = question

    await question_service.delete_question(
        uuid.uuid4(),
        make_user(role=UserRole.ADMIN),
    )

    question_repository.delete.assert_awaited_once_with(question)
    question_repository.commit.assert_awaited_once_with()
    question_repository.rollback.assert_not_awaited()


async def test_delete_question_rolls_back_repository_error(
    question_service,
    question_repository,
):
    error = RuntimeError("delete failed")
    question_repository.get_by_public_id.return_value = SimpleNamespace(hackathon=SimpleNamespace())
    question_repository.delete.side_effect = error

    with pytest.raises(RuntimeError, match="delete failed"):
        await question_service.delete_question(
            uuid.uuid4(),
            make_user(role=UserRole.ADMIN),
        )

    question_repository.rollback.assert_awaited_once_with()
    question_repository.commit.assert_not_awaited()


async def test_create_question_raises_when_hackathon_does_not_exist(
    question_service,
    question_repository,
    hackathon_repository,
):
    hackathon_repository.get_active_by_public_id.return_value = None

    with pytest.raises(HackathonNotFoundError):
        await question_service.create_question(
            uuid.uuid4(),
            RegistrationQuestionCreate(content="Why?"),
            make_user(role=UserRole.ADMIN),
        )

    question_repository.create.assert_not_awaited()


async def test_list_questions_raises_when_hackathon_does_not_exist(
    question_service,
    question_repository,
    hackathon_repository,
):
    hackathon_repository.get_active_by_public_id.return_value = None

    with pytest.raises(HackathonNotFoundError):
        await question_service.list_questions(uuid.uuid4())

    question_repository.get_by_hackathon_public_id.assert_not_awaited()


async def test_user_can_list_registration_questions(
    question_service,
    question_repository,
    hackathon_repository,
):
    hackathon_public_id = uuid.uuid4()
    questions = [make_question()]
    hackathon_repository.get_active_by_public_id.return_value = SimpleNamespace()
    question_repository.get_by_hackathon_public_id.return_value = questions

    result = await question_service.list_questions(hackathon_public_id)

    assert result == questions
    question_repository.get_by_hackathon_public_id.assert_awaited_once_with(hackathon_public_id)


async def test_create_question_rejects_regular_user(
    question_service,
    question_repository,
    hackathon_repository,
):
    hackathon_repository.get_active_by_public_id.return_value = SimpleNamespace(
        organizer_id=10,
        co_organizers=[SimpleNamespace(id=20)],
    )

    with pytest.raises(InvalidPermission):
        await question_service.create_question(
            uuid.uuid4(),
            RegistrationQuestionCreate(content="Why?"),
            make_user(),
        )

    question_repository.create.assert_not_awaited()


@pytest.mark.parametrize("access_kind", ["organizer", "co_organizer"])
async def test_organizer_and_co_organizer_can_create_question(
    access_kind,
    question_service,
    question_repository,
    hackathon_repository,
):
    organizer_id = 10
    co_organizer_id = 20
    current_user = make_user(
        user_id=organizer_id if access_kind == "organizer" else co_organizer_id
    )
    co_organizer = User(
        name="Co-organizer",
        email="co-organizer@example.com",
        password_hash="hashed-password",
    )
    co_organizer.id = co_organizer_id
    hackathon = make_hackathon()
    hackathon.organizer_id = organizer_id
    hackathon.co_organizers = [co_organizer]
    hackathon_repository.get_active_by_public_id.return_value = hackathon
    question_repository.create.side_effect = lambda question: question

    result = await question_service.create_question(
        uuid.uuid4(),
        RegistrationQuestionCreate(content="Why?"),
        current_user,
    )

    assert result.hackathon is hackathon
    question_repository.create.assert_awaited_once_with(result)
    question_repository.commit.assert_awaited_once_with()


@pytest.mark.parametrize("access_kind", ["organizer", "co_organizer"])
async def test_organizer_and_co_organizer_can_delete_question(
    access_kind,
    question_service,
    question_repository,
):
    organizer_id = 10
    co_organizer_id = 20
    current_user = make_user(
        user_id=organizer_id if access_kind == "organizer" else co_organizer_id
    )
    question = SimpleNamespace(
        hackathon=SimpleNamespace(
            organizer_id=organizer_id,
            co_organizers=[SimpleNamespace(id=co_organizer_id)],
        )
    )
    question_repository.get_by_public_id.return_value = question

    await question_service.delete_question(uuid.uuid4(), current_user)

    question_repository.delete.assert_awaited_once_with(question)
    question_repository.commit.assert_awaited_once_with()


async def test_admin_can_create_question(
    question_service,
    question_repository,
    hackathon_repository,
):
    hackathon = make_hackathon()
    hackathon_repository.get_active_by_public_id.return_value = hackathon
    question_repository.create.side_effect = lambda question: question

    result = await question_service.create_question(
        uuid.uuid4(),
        RegistrationQuestionCreate(content="Why?", is_required=False),
        make_user(role=UserRole.ADMIN),
    )

    assert isinstance(result, RegistrationQuestion)
    assert result.content == "Why?"
    assert result.is_required is False
    assert result.hackathon is hackathon
    question_repository.create.assert_awaited_once_with(result)
    question_repository.commit.assert_awaited_once_with()
    question_repository.rollback.assert_not_awaited()


async def test_create_question_rolls_back_repository_error(
    question_service,
    question_repository,
    hackathon_repository,
):
    hackathon_repository.get_active_by_public_id.return_value = make_hackathon()
    question_repository.create.side_effect = RuntimeError("create failed")

    with pytest.raises(RuntimeError, match="create failed"):
        await question_service.create_question(
            uuid.uuid4(),
            RegistrationQuestionCreate(content="Why?"),
            make_user(role=UserRole.ADMIN),
        )

    question_repository.rollback.assert_awaited_once_with()
    question_repository.commit.assert_not_awaited()


async def test_create_registration_raises_when_hackathon_does_not_exist(
    registration_service,
    registration_repository,
    hackathon_repository,
):
    question = make_question()
    hackathon_repository.get_active_by_public_id.return_value = None

    with pytest.raises(HackathonNotFoundError):
        await registration_service.create_registration(
            registration_data(question),
            uuid.uuid4(),
            make_user(),
        )

    registration_repository.create.assert_not_awaited()


async def test_create_registration_rejects_closed_registration(
    registration_service,
    registration_repository,
    question_repository,
    hackathon_repository,
):
    question = make_question()
    hackathon_repository.get_active_by_public_id.return_value = registration_window(is_open=False)

    with pytest.raises(RegistrationClosedError):
        await registration_service.create_registration(
            registration_data(question),
            uuid.uuid4(),
            make_user(),
        )

    question_repository.get_by_hackathon_public_id.assert_not_awaited()
    registration_repository.create.assert_not_awaited()


async def test_list_registrations_raises_when_hackathon_does_not_exist(
    registration_service,
    registration_repository,
    hackathon_repository,
):
    hackathon_repository.get_active_by_public_id.return_value = None

    with pytest.raises(HackathonNotFoundError):
        await registration_service.list_registrations(uuid.uuid4(), make_user())

    registration_repository.get_by_hackathon.assert_not_awaited()


async def test_list_registrations_rejects_user_without_access(
    registration_service,
    registration_repository,
    hackathon_repository,
):
    hackathon_repository.get_active_by_public_id.return_value = SimpleNamespace(
        organizer_id=10,
        co_organizers=[SimpleNamespace(id=20)],
    )

    with pytest.raises(InvalidPermission):
        await registration_service.list_registrations(
            uuid.uuid4(),
            make_user(user_id=30),
        )

    registration_repository.get_by_hackathon.assert_not_awaited()


@pytest.mark.parametrize("access_kind", ["admin", "organizer", "co_organizer"])
async def test_authorized_user_can_list_registrations(
    access_kind,
    registration_service,
    registration_repository,
    hackathon_repository,
):
    organizer_id = 10
    co_organizer_id = 20
    current_user = make_user(user_id=30)
    if access_kind == "admin":
        current_user.role = UserRole.ADMIN
    elif access_kind == "organizer":
        current_user.id = organizer_id
    else:
        current_user.id = co_organizer_id

    hackathon_public_id = uuid.uuid4()
    registrations = [SimpleNamespace(public_id=uuid.uuid4())]
    hackathon_repository.get_active_by_public_id.return_value = SimpleNamespace(
        organizer_id=organizer_id,
        co_organizers=[SimpleNamespace(id=co_organizer_id)],
    )
    registration_repository.get_by_hackathon.return_value = registrations

    result = await registration_service.list_registrations(
        hackathon_public_id,
        current_user,
        limit=25,
        offset=10,
    )

    assert result == registrations
    registration_repository.get_by_hackathon.assert_awaited_once_with(
        hackathon_public_id,
        limit=25,
        offset=10,
    )


async def test_get_my_registration_returns_current_users_registration(
    registration_service,
    registration_repository,
):
    hackathon_public_id = uuid.uuid4()
    current_user = make_user()
    registration = SimpleNamespace(public_id=uuid.uuid4())
    registration_repository.get_by_hackathon_and_user.return_value = registration

    result = await registration_service.get_my_registration(
        hackathon_public_id,
        current_user,
    )

    assert result is registration
    registration_repository.get_by_hackathon_and_user.assert_awaited_once_with(
        hackathon_public_id,
        current_user.public_id,
    )


async def test_get_my_registration_raises_when_registration_does_not_exist(
    registration_service,
    registration_repository,
):
    current_user = make_user()
    registration_repository.get_by_hackathon_and_user.return_value = None

    with pytest.raises(RegistrationNotFoundError):
        await registration_service.get_my_registration(uuid.uuid4(), current_user)


async def test_create_registration_rejects_question_from_another_hackathon(
    registration_service,
    registration_repository,
    question_repository,
    hackathon_repository,
):
    submitted_question = make_question()
    hackathon_repository.get_active_by_public_id.return_value = registration_window(is_open=True)
    question_repository.get_by_hackathon_public_id.return_value = []

    with pytest.raises(InvalidRegistrationQuestionError):
        await registration_service.create_registration(
            registration_data(submitted_question),
            uuid.uuid4(),
            make_user(),
        )

    registration_repository.create.assert_not_awaited()


async def test_create_registration_requires_all_required_answers(
    registration_service,
    registration_repository,
    question_repository,
    hackathon_repository,
):
    required_question = make_question(question_id=1, is_required=True)
    optional_question = make_question(question_id=2, is_required=False)
    hackathon_repository.get_active_by_public_id.return_value = registration_window(is_open=True)
    question_repository.get_by_hackathon_public_id.return_value = [
        required_question,
        optional_question,
    ]

    with pytest.raises(MissingRequiredAnswersError):
        await registration_service.create_registration(
            registration_data(optional_question),
            uuid.uuid4(),
            make_user(),
        )

    registration_repository.create.assert_not_awaited()


async def test_create_registration_builds_answers_and_commits(
    registration_service,
    registration_repository,
    question_repository,
    hackathon_repository,
):
    required_question = make_question(question_id=11, is_required=True)
    optional_question = make_question(question_id=12, is_required=False)
    hackathon = registration_window(is_open=True, hackathon_id=20)
    user = make_user(user_id=30)
    hackathon_repository.get_active_by_public_id.return_value = hackathon
    question_repository.get_by_hackathon_public_id.return_value = [
        required_question,
        optional_question,
    ]
    registration_repository.create.side_effect = lambda registration: registration

    result = await registration_service.create_registration(
        registration_data(required_question, optional_question),
        uuid.uuid4(),
        user,
    )

    assert isinstance(result, Registration)
    assert result.user_id == user.id
    assert result.hackathon_id == hackathon.id
    assert [answer.question_id for answer in result.answers] == [11, 12]
    assert [answer.content for answer in result.answers] == ["Answer 1", "Answer 2"]
    registration_repository.create.assert_awaited_once_with(result)
    registration_repository.commit.assert_awaited_once_with()
    registration_repository.rollback.assert_not_awaited()


async def test_create_registration_maps_integrity_error_and_rolls_back(
    registration_service,
    registration_repository,
    question_repository,
    hackathon_repository,
):
    question = make_question()
    hackathon_repository.get_active_by_public_id.return_value = registration_window(is_open=True)
    question_repository.get_by_hackathon_public_id.return_value = [question]
    registration_repository.create.side_effect = IntegrityError(
        "INSERT INTO registrations",
        {},
        Exception("duplicate registration"),
    )

    with pytest.raises(RegistrationAlreadyExistsError):
        await registration_service.create_registration(
            registration_data(question),
            uuid.uuid4(),
            make_user(),
        )

    registration_repository.rollback.assert_awaited_once_with()
    registration_repository.commit.assert_not_awaited()


async def test_create_registration_rolls_back_unexpected_error(
    registration_service,
    registration_repository,
    question_repository,
    hackathon_repository,
):
    question = make_question()
    hackathon_repository.get_active_by_public_id.return_value = registration_window(is_open=True)
    question_repository.get_by_hackathon_public_id.return_value = [question]
    registration_repository.create.side_effect = RuntimeError("create failed")

    with pytest.raises(RuntimeError, match="create failed"):
        await registration_service.create_registration(
            registration_data(question),
            uuid.uuid4(),
            make_user(),
        )

    registration_repository.rollback.assert_awaited_once_with()
    registration_repository.commit.assert_not_awaited()


async def test_delete_registration_raises_when_registration_does_not_exist(
    registration_service,
    registration_repository,
):
    registration_repository.get_active_by_public_id.return_value = None

    with pytest.raises(RegistrationNotFoundError):
        await registration_service.delete_registration(uuid.uuid4(), make_user())

    registration_repository.delete.assert_not_awaited()


async def test_delete_registration_rejects_user_without_access(
    registration_service,
    registration_repository,
):
    registration_repository.get_active_by_public_id.return_value = SimpleNamespace(
        user_id=10,
        hackathon=SimpleNamespace(
            organizer_id=20,
            co_organizers=[SimpleNamespace(id=30)],
        ),
    )

    with pytest.raises(InvalidPermission):
        await registration_service.delete_registration(
            uuid.uuid4(),
            make_user(user_id=40),
        )

    registration_repository.delete.assert_not_awaited()


@pytest.mark.parametrize("access_kind", ["admin", "organizer", "co_organizer", "owner"])
async def test_authorized_user_can_delete_registration(
    access_kind,
    registration_service,
    registration_repository,
):
    current_user = make_user(user_id=40)
    organizer_id = 20
    co_organizers = [SimpleNamespace(id=30)]
    owner_id = 10

    if access_kind == "admin":
        current_user.role = UserRole.ADMIN
    elif access_kind == "organizer":
        current_user.id = organizer_id
    elif access_kind == "co_organizer":
        current_user.id = co_organizers[0].id
    else:
        current_user.id = owner_id

    registration = SimpleNamespace(
        user_id=owner_id,
        hackathon=SimpleNamespace(
            organizer_id=organizer_id,
            co_organizers=co_organizers,
        ),
    )
    registration_repository.get_active_by_public_id.return_value = registration

    await registration_service.delete_registration(uuid.uuid4(), current_user)

    registration_repository.delete.assert_awaited_once_with(registration)
    registration_repository.commit.assert_awaited_once_with()
    registration_repository.rollback.assert_not_awaited()


async def test_delete_registration_rolls_back_repository_error(
    registration_service,
    registration_repository,
):
    current_user = make_user(user_id=10)
    registration = SimpleNamespace(
        user_id=current_user.id,
        hackathon=SimpleNamespace(organizer_id=20, co_organizers=[]),
    )
    registration_repository.get_active_by_public_id.return_value = registration
    registration_repository.delete.side_effect = RuntimeError("delete failed")

    with pytest.raises(RuntimeError, match="delete failed"):
        await registration_service.delete_registration(uuid.uuid4(), current_user)

    registration_repository.rollback.assert_awaited_once_with()
    registration_repository.commit.assert_not_awaited()


async def test_update_status_raises_when_registration_does_not_exist(
    registration_service,
    registration_repository,
):
    registration_repository.get_active_by_public_id.return_value = None

    with pytest.raises(RegistrationNotFoundError):
        await registration_service.update_status(
            uuid.uuid4(),
            RegistrationStatus.ACCEPTED,
            make_user(role=UserRole.ADMIN),
        )

    registration_repository.update_status.assert_not_awaited()


async def test_update_status_rejects_user_without_access(
    registration_service,
    registration_repository,
):
    registration_repository.get_active_by_public_id.return_value = SimpleNamespace(
        hackathon=SimpleNamespace(
            organizer_id=10,
            co_organizers=[SimpleNamespace(id=20)],
        ),
    )

    with pytest.raises(InvalidPermission):
        await registration_service.update_status(
            uuid.uuid4(),
            RegistrationStatus.ACCEPTED,
            make_user(user_id=30),
        )

    registration_repository.update_status.assert_not_awaited()


@pytest.mark.parametrize("access_kind", ["admin", "organizer", "co_organizer"])
async def test_authorized_user_can_update_status(
    access_kind,
    registration_service,
    registration_repository,
):
    organizer_id = 10
    co_organizer_id = 20
    current_user = make_user(user_id=30)
    if access_kind == "admin":
        current_user.role = UserRole.ADMIN
    elif access_kind == "organizer":
        current_user.id = organizer_id
    else:
        current_user.id = co_organizer_id

    registration = SimpleNamespace(
        status=RegistrationStatus.PENDING,
        hackathon=SimpleNamespace(
            organizer_id=organizer_id,
            co_organizers=[SimpleNamespace(id=co_organizer_id)],
        ),
    )
    registration_repository.get_active_by_public_id.return_value = registration
    registration_repository.update_status.side_effect = (
        lambda item, status, _changed_by: setattr(item, "status", status) or item
    )

    result = await registration_service.update_status(
        uuid.uuid4(),
        RegistrationStatus.ACCEPTED,
        current_user,
    )

    assert result.status is RegistrationStatus.ACCEPTED
    registration_repository.update_status.assert_awaited_once_with(
        registration,
        RegistrationStatus.ACCEPTED,
        current_user,
    )
    registration_repository.commit.assert_awaited_once_with()
    registration_repository.rollback.assert_not_awaited()


async def test_update_status_rolls_back_repository_error(
    registration_service,
    registration_repository,
):
    registration_repository.get_active_by_public_id.return_value = SimpleNamespace(
        hackathon=SimpleNamespace(organizer_id=10, co_organizers=[]),
    )
    registration_repository.update_status.side_effect = RuntimeError("update failed")

    with pytest.raises(RuntimeError, match="update failed"):
        await registration_service.update_status(
            uuid.uuid4(),
            RegistrationStatus.REJECTED,
            make_user(user_id=10),
        )

    registration_repository.rollback.assert_awaited_once_with()
    registration_repository.commit.assert_not_awaited()


async def test_create_many_questions(
    question_service,
    question_repository,
    hackathon_repository,
):
    hackathon_public_id = uuid.uuid4()
    hackathon = make_hackathon()
    hackathon_repository.get_active_by_public_id.return_value = hackathon
    question_repository.create_many.side_effect = lambda questions: questions
    data = RegistrationQuestionBulkCreate(
        questions=[
            RegistrationQuestionCreate(content="Why?", is_required=True),
            RegistrationQuestionCreate(content="Experience?", is_required=False),
        ]
    )

    result = await question_service.create_questions(
        hackathon_public_id,
        data,
        make_user(role=UserRole.ADMIN),
    )

    assert [question.content for question in result] == ["Why?", "Experience?"]
    assert [question.is_required for question in result] == [True, False]
    assert all(question.hackathon is hackathon for question in result)
    hackathon_repository.get_active_by_public_id.assert_awaited_once_with(hackathon_public_id)
    question_repository.create_many.assert_awaited_once_with(result)
    question_repository.commit.assert_awaited_once_with()
    question_repository.rollback.assert_not_awaited()
