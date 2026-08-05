import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.hackathons.models import Hackathon
from src.main import app
from src.registration.models import Registration, RegistrationAnswer, RegistrationQuestion

ForceAuthenticate = Callable[[User | None], None]


async def create_user(
    session: AsyncSession,
    email: str,
    *,
    role: UserRole = UserRole.USER,
) -> User:
    local_part, domain = email.split("@", maxsplit=1)
    unique_email = f"{local_part}-{uuid.uuid4()}@{domain}"
    user = User(
        name=local_part.title(),
        email=unique_email,
        password_hash="test-password-hash",
        role=role,
    )
    session.add(user)
    await session.flush()
    return user


async def create_hackathon(
    session: AsyncSession,
    organizer: User,
) -> Hackathon:
    start_date = datetime.now(UTC) + timedelta(days=1)
    hackathon = Hackathon(
        organizer=organizer,
        name="Integration Test Hackathon",
        description="Hackathon used by endpoint integration tests",
        start_date=start_date,
        end_date=start_date + timedelta(days=2),
        registration_open=True,
        capacity=50,
        max_team_size=4,
    )
    session.add(hackathon)
    await session.flush()
    return hackathon


async def create_question(
    session: AsyncSession,
    hackathon: Hackathon,
    *,
    content: str = "Why do you want to participate?",
    is_required: bool = True,
) -> RegistrationQuestion:
    question = RegistrationQuestion(
        hackathon=hackathon,
        content=content,
        is_required=is_required,
    )
    session.add(question)
    await session.flush()
    return question


def test_registration_routes_are_registered():
    paths = set(app.openapi()["paths"])

    assert {
        "/api/hackathons/{hackathon_public_id}/questions",
        "/api/hackathons/{hackathon_public_id}/questions/{question_public_id}",
        "/api/hackathons/{hackathon_public_id}/registrations",
        "/api/registrations/{registration_public_id}",
    }.issubset(paths)


async def test_admin_creates_question(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(
        session,
        "admin@example.com",
        role=UserRole.ADMIN,
    )
    hackathon = await create_hackathon(session, admin)
    await session.commit()
    force_authenticate(admin)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/questions",
        json={
            "content": "Why do you want to participate?",
            "is_required": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["content"] == "Why do you want to participate?"
    assert body["is_required"] is True

    question = await session.scalar(
        select(RegistrationQuestion).where(
            RegistrationQuestion.public_id == uuid.UUID(body["public_id"])
        )
    )
    assert question is not None
    assert question.hackathon_id == hackathon.id


async def test_create_question_rejects_invalid_payload(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(
        session,
        "admin@example.com",
        role=UserRole.ADMIN,
    )
    hackathon = await create_hackathon(session, admin)
    await session.commit()
    force_authenticate(admin)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/questions",
        json={"content": "", "is_required": True},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"
    questions = await session.scalars(select(RegistrationQuestion))
    assert list(questions) == []


async def test_admin_deletes_question(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(
        session,
        "admin@example.com",
        role=UserRole.ADMIN,
    )
    hackathon = await create_hackathon(session, admin)
    question = await create_question(session, hackathon)
    await session.commit()
    question_public_id = question.public_id
    force_authenticate(admin)

    response = await api_client.delete(
        f"/api/hackathons/{hackathon.public_id}/questions/{question_public_id}"
    )

    assert response.status_code == 204
    assert response.content == b""
    assert await session.scalar(
        select(RegistrationQuestion).where(
            RegistrationQuestion.public_id == question_public_id
        )
    ) is None


async def test_delete_missing_question_returns_not_found(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(
        session,
        "admin@example.com",
        role=UserRole.ADMIN,
    )
    hackathon = await create_hackathon(session, admin)
    await session.commit()
    force_authenticate(admin)

    response = await api_client.delete(
        f"/api/hackathons/{hackathon.public_id}/questions/{uuid.uuid4()}"
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "QUESTION_NOT_FOUND"


async def test_user_creates_registration(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    question = await create_question(session, hackathon)
    await session.commit()
    force_authenticate(participant)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={
            "answers": [
                {
                    "question_public_id": str(question.public_id),
                    "content": "My answer",
                }
            ]
        },
    )

    assert response.status_code == 201
    registration_public_id = uuid.UUID(response.json()["public_id"])
    registration = await session.scalar(
        select(Registration).where(
            Registration.public_id == registration_public_id
        )
    )
    assert registration is not None
    assert registration.user_id == participant.id
    assert registration.hackathon_id == hackathon.id

    answer = await session.scalar(
        select(RegistrationAnswer).where(
            RegistrationAnswer.registration_id == registration.id
        )
    )
    assert answer is not None
    assert answer.question_id == question.id
    assert answer.content == "My answer"


async def test_create_registration_rejects_duplicate_question_answers(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    question = await create_question(session, hackathon)
    await session.commit()
    force_authenticate(participant)
    answer = {
        "question_public_id": str(question.public_id),
        "content": "My answer",
    }

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={"answers": [answer, answer]},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"
    registration = await session.scalar(
        select(Registration).where(
            Registration.user_id == participant.id,
            Registration.hackathon_id == hackathon.id,
        )
    )
    assert registration is None


async def test_owner_deletes_registration(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    registration = Registration(user=participant, hackathon=hackathon)
    session.add(registration)
    await session.commit()
    registration_public_id = registration.public_id
    force_authenticate(participant)

    response = await api_client.delete(
        f"/api/registrations/{registration_public_id}"
    )

    assert response.status_code == 204
    assert response.content == b""
    assert await session.scalar(
        select(Registration).where(
            Registration.public_id == registration_public_id
        )
    ) is None


async def test_delete_missing_registration_returns_not_found(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    user = await create_user(session, "participant@example.com")
    await session.commit()
    force_authenticate(user)

    response = await api_client.delete(f"/api/registrations/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["error_code"] == "REGISTRATION_NOT_FOUND"


async def test_registration_endpoint_requires_authentication(
    api_client: AsyncClient,
):
    response = await api_client.delete(f"/api/registrations/{uuid.uuid4()}")

    assert response.status_code == 401
