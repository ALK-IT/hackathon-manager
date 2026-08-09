import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.hackathons.models import Hackathon
from src.registration.models import Registration, RegistrationQuestion, RegistrationStatus
from src.registration.repository import RegistrationQuestionRepository, RegistrationRepository


def make_user(
    email: str,
    *,
    role: UserRole = UserRole.USER,
) -> User:
    return User(
        name=email.split("@", maxsplit=1)[0].title(),
        email=email,
        password_hash="hashed-password",
        role=role,
    )


def make_hackathon(
    organizer: User,
    *,
    name: str = "AI Hackathon",
) -> Hackathon:
    start_date = datetime.now(UTC) + timedelta(days=1)
    return Hackathon(
        name=name,
        organizer=organizer,
        start_date=start_date,
        end_date=start_date + timedelta(days=2),
        max_team_size=4,
    )


@pytest.fixture
def organizer() -> User:
    return make_user("organizer@example.com", role=UserRole.ADMIN)


async def test_create_adds_question_and_flushes(
    session: AsyncSession,
    organizer: User,
):
    hackathon = make_hackathon(organizer)
    question = RegistrationQuestion(
        content="Why?",
        is_required=True,
        hackathon=hackathon,
    )
    repository = RegistrationQuestionRepository(session)

    created_question = await repository.create(question)

    assert created_question is question
    assert created_question.id is not None
    assert created_question.hackathon_id == hackathon.id
    assert created_question.hackathon is hackathon


async def test_delete_question(
    session: AsyncSession,
    organizer: User,
):
    question = RegistrationQuestion(
        content="Question",
        is_required=True,
        hackathon=make_hackathon(organizer),
    )
    session.add(question)
    await session.flush()
    question_id = question.id
    repository = RegistrationQuestionRepository(session)

    await repository.delete(question)
    await session.flush()
    result = await session.execute(
        select(RegistrationQuestion).where(RegistrationQuestion.id == question_id)
    )

    assert result.scalar_one_or_none() is None


async def test_get_question_by_public_id(
    session: AsyncSession,
    organizer: User,
):
    question = RegistrationQuestion(
        content="Question",
        is_required=True,
        hackathon=make_hackathon(organizer),
    )
    session.add(question)
    await session.flush()
    repository = RegistrationQuestionRepository(session)

    result = await repository.get_by_public_id(question.public_id)

    assert result is question


async def test_get_question_by_public_id_returns_none_when_missing(
    session: AsyncSession,
):
    repository = RegistrationQuestionRepository(session)

    result = await repository.get_by_public_id(uuid.uuid4())

    assert result is None


async def test_get_questions_by_hackathon_public_id(
    session: AsyncSession,
    organizer: User,
):
    hackathon = make_hackathon(organizer)
    question = RegistrationQuestion(
        content="Why?",
        is_required=True,
        hackathon=hackathon,
    )
    session.add(question)
    await session.flush()
    repository = RegistrationQuestionRepository(session)

    result = await repository.get_by_hackathon_public_id(hackathon.public_id)

    assert result == [question]


async def test_create_registration_assigns_defaults_and_foreign_keys(
    session: AsyncSession,
    organizer: User,
):
    participant = make_user("participant@example.com")
    hackathon = make_hackathon(organizer)
    registration = Registration(user=participant, hackathon=hackathon)
    repository = RegistrationRepository(session)

    created_registration = await repository.create(registration)

    assert created_registration is registration
    assert registration.id is not None
    assert registration.public_id is not None
    assert registration.user_id == participant.id
    assert registration.hackathon_id == hackathon.id
    assert registration.status is RegistrationStatus.PENDING


async def test_get_registrations_by_hackathon(
    session: AsyncSession,
    organizer: User,
):
    participant = make_user("participant@example.com")
    hackathon = make_hackathon(organizer)
    other_hackathon = make_hackathon(organizer, name="Other Hackathon")
    registration = Registration(user=participant, hackathon=hackathon)
    repository = RegistrationRepository(session)
    await repository.create(registration)
    session.add(other_hackathon)
    await session.flush()

    result = await repository.get_by_hackathon(hackathon.public_id)
    empty_result = await repository.get_by_hackathon(other_hackathon.public_id)

    assert result == [registration]
    assert empty_result == []


async def test_get_registration_by_hackathon_and_user(
    session: AsyncSession,
    organizer: User,
):
    participant = make_user("participant@example.com")
    outsider = make_user("outsider@example.com")
    hackathon = make_hackathon(organizer)
    registration = Registration(user=participant, hackathon=hackathon)
    repository = RegistrationRepository(session)
    await repository.create(registration)
    session.add(outsider)
    await session.flush()

    result = await repository.get_by_hackathon_and_user(
        hackathon.public_id,
        participant.public_id,
    )
    missing_result = await repository.get_by_hackathon_and_user(
        hackathon.public_id,
        outsider.public_id,
    )

    assert result is registration
    assert missing_result is None


async def test_get_registration_by_public_id(
    session: AsyncSession,
    organizer: User,
):
    participant = make_user("participant@example.com")
    registration = Registration(
        user=participant,
        hackathon=make_hackathon(organizer),
    )
    repository = RegistrationRepository(session)
    await repository.create(registration)

    result = await repository.get_by_public_id(registration.public_id)
    missing_result = await repository.get_by_public_id(uuid.uuid4())

    assert result is registration
    assert missing_result is None


async def test_delete_registration(
    session: AsyncSession,
    organizer: User,
):
    registration = Registration(
        user=make_user("participant@example.com"),
        hackathon=make_hackathon(organizer),
    )
    repository = RegistrationRepository(session)
    await repository.create(registration)
    public_id = registration.public_id

    await repository.delete(registration)

    assert await repository.get_by_public_id(public_id) is None


async def test_rollback_discards_registration(
    session: AsyncSession,
    organizer: User,
):
    registration = Registration(
        user=make_user("participant@example.com"),
        hackathon=make_hackathon(organizer),
    )
    repository = RegistrationRepository(session)
    await repository.create(registration)
    public_id = registration.public_id

    await repository.rollback()

    assert await repository.get_by_public_id(public_id) is None


async def test_update_status_registration_accepted(session: AsyncSession, organizer: User):
    registration = Registration(
        user=make_user("participant@gmail.com"), hackathon=make_hackathon(organizer)
    )

    repository = RegistrationRepository(session)
    await repository.create(registration)

    assert registration.status == RegistrationStatus.PENDING

    new_status = RegistrationStatus.ACCEPTED

    registration = await repository.update_status(registration, new_status)

    assert registration.status == RegistrationStatus.ACCEPTED


async def test_update_status_registration_rejected(session: AsyncSession, organizer: User):
    registration = Registration(
        user=make_user("participant@gmail.com"), hackathon=make_hackathon(organizer)
    )

    repository = RegistrationRepository(session)
    await repository.create(registration)

    assert registration.status == RegistrationStatus.PENDING

    new_status = RegistrationStatus.REJECTED

    registration = await repository.update_status(registration, new_status)

    assert registration.status == RegistrationStatus.REJECTED
