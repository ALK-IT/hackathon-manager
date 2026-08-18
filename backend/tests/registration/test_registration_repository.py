import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.hackathons.models import Hackathon
from src.registration.models import (
    Registration,
    RegistrationAnswer,
    RegistrationQuestion,
    RegistrationStatus,
)
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
    now = datetime.now(UTC)
    start_date = now + timedelta(days=1)
    return Hackathon(
        name=name,
        organizer=organizer,
        start_date=start_date,
        end_date=start_date + timedelta(days=2),
        registration_opens_at=now - timedelta(hours=1),
        registration_deadline=start_date - timedelta(hours=1),
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


async def test_database_rejects_deleting_question_with_answers(
    session: AsyncSession,
    organizer: User,
):
    participant = make_user("participant@example.com")
    hackathon = make_hackathon(organizer)
    question = RegistrationQuestion(content="Question", is_required=True, hackathon=hackathon)
    registration = Registration(user=participant, hackathon=hackathon)
    registration.answers.append(RegistrationAnswer(question=question, content="Answer"))
    session.add(registration)
    await session.flush()

    with pytest.raises(IntegrityError):
        await session.execute(
            delete(RegistrationQuestion).where(RegistrationQuestion.id == question.id)
        )

    await session.rollback()


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


async def test_get_question_by_public_id_returns_none_for_deleted_hackathon(
    session: AsyncSession,
    organizer: User,
):
    hackathon = make_hackathon(organizer)
    question = RegistrationQuestion(
        content="Question",
        is_required=True,
        hackathon=hackathon,
    )
    session.add(question)
    await session.flush()
    question_public_id = question.public_id
    hackathon.is_deleted = True
    await session.flush()
    repository = RegistrationQuestionRepository(session)

    result = await repository.get_by_public_id(question_public_id)

    assert result is None
    assert (
        await session.scalar(
            select(RegistrationQuestion).where(RegistrationQuestion.public_id == question_public_id)
        )
        is question
    )


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

    result = await repository.get_by_hackathon(hackathon.public_id, limit=50, offset=0)
    empty_result = await repository.get_by_hackathon(
        other_hackathon.public_id,
        limit=50,
        offset=0,
    )

    assert result == [registration]
    assert empty_result == []


async def test_get_registrations_by_hackathon_applies_limit_and_offset(
    session: AsyncSession,
    organizer: User,
):
    hackathon = make_hackathon(organizer)
    registrations = [
        Registration(
            user=make_user(f"participant-{index}@example.com"),
            hackathon=hackathon,
        )
        for index in range(3)
    ]
    repository = RegistrationRepository(session)
    for registration in registrations:
        await repository.create(registration)

    result = await repository.get_by_hackathon(
        hackathon.public_id,
        limit=1,
        offset=1,
    )

    assert result == [registrations[1]]


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


async def test_get_active_registration_by_public_id_excludes_deleted_hackathon(
    session: AsyncSession,
    organizer: User,
):
    hackathon = make_hackathon(organizer)
    registration = Registration(
        user=make_user("participant@example.com"),
        hackathon=hackathon,
    )
    repository = RegistrationRepository(session)
    await repository.create(registration)

    assert await repository.get_active_by_public_id(registration.public_id) is registration

    hackathon.is_deleted = True
    await session.flush()

    assert await repository.get_active_by_public_id(registration.public_id) is None
    assert (
        await session.scalar(
            select(Registration).where(Registration.public_id == registration.public_id)
        )
        is registration
    )


async def test_get_registration_by_public_id_hides_soft_deleted_hackathon(
    session: AsyncSession,
    organizer: User,
):
    participant = make_user("participant@example.com")
    hackathon = make_hackathon(organizer)
    registration = Registration(user=participant, hackathon=hackathon)
    repository = RegistrationRepository(session)
    await repository.create(registration)
    hackathon.is_deleted = True
    await session.flush()

    result = await repository.get_active_by_public_id(registration.public_id)

    assert result is None


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

    assert (
        await session.scalar(select(Registration).where(Registration.public_id == public_id))
        is None
    )


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

    assert (
        await session.scalar(select(Registration).where(Registration.public_id == public_id))
        is None
    )


async def test_update_status_registration_accepted(session: AsyncSession, organizer: User):
    registration = Registration(
        user=make_user("participant@gmail.com"), hackathon=make_hackathon(organizer)
    )

    repository = RegistrationRepository(session)
    await repository.create(registration)

    assert registration.status == RegistrationStatus.PENDING

    new_status = RegistrationStatus.ACCEPTED

    registration = await repository.update_status(registration, new_status, organizer)

    assert registration.status == RegistrationStatus.ACCEPTED
    assert registration.status_changed_at is not None
    assert registration.status_changed_by is organizer


async def test_update_status_registration_rejected(session: AsyncSession, organizer: User):
    registration = Registration(
        user=make_user("participant@gmail.com"), hackathon=make_hackathon(organizer)
    )

    repository = RegistrationRepository(session)
    await repository.create(registration)

    assert registration.status == RegistrationStatus.PENDING

    new_status = RegistrationStatus.REJECTED

    registration = await repository.update_status(registration, new_status, organizer)

    assert registration.status == RegistrationStatus.REJECTED
    assert registration.status_changed_at is not None
    assert registration.status_changed_by is organizer


async def test_create_many_questions(session: AsyncSession, organizer: User):
    hackathon = make_hackathon(organizer)
    questions = [
        RegistrationQuestion(
            content="Why?",
            is_required=True,
            hackathon=hackathon,
        ),
        RegistrationQuestion(
            content="What?",
            is_required=True,
            hackathon=hackathon,
        ),
    ]
    repository = RegistrationQuestionRepository(session)

    result = await repository.create_many(questions)

    assert result == questions
    saved_questions = list(
        await session.scalars(
            select(RegistrationQuestion)
            .where(RegistrationQuestion.hackathon_id == hackathon.id)
            .order_by(RegistrationQuestion.id)
        )
    )
    assert saved_questions == questions
