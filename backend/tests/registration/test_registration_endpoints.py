import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.hackathons.models import Hackathon
from src.main import app
from src.registration.models import (
    Registration,
    RegistrationAnswer,
    RegistrationQuestion,
    RegistrationStatus,
)
from src.teams.models import Team

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
    *,
    max_team_size: int = 4,
    registration_open: bool = True,
    teams_enabled: bool = True,
) -> Hackathon:
    now = datetime.now(UTC)
    start_date = now + timedelta(days=1)
    hackathon = Hackathon(
        organizer=organizer,
        co_organizers=[],
        name="Integration Test Hackathon",
        description="Hackathon used by endpoint integration tests",
        start_date=start_date,
        end_date=start_date + timedelta(days=2),
        registration_opens_at=now - timedelta(hours=1),
        registration_deadline=start_date - timedelta(hours=1),
        registration_open=registration_open,
        capacity=50,
        max_team_size=max_team_size,
        teams_enabled=teams_enabled,
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
        "/api/hackathons/{hackathon_public_id}/questions/bulk",
        "/api/hackathons/{hackathon_public_id}/questions/{question_public_id}",
        "/api/hackathons/{hackathon_public_id}/registrations",
        "/api/hackathons/{hackathon_public_id}/registrations/me",
        "/api/registrations/{registration_public_id}",
        "/api/registrations/{registration_public_id}/status",
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


async def test_admin_creates_many_questions(
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
        f"/api/hackathons/{hackathon.public_id}/questions/bulk",
        json={
            "questions": [
                {"content": "Why do you want to participate?", "is_required": True},
                {"content": "What is your experience?", "is_required": False},
            ]
        },
    )

    assert response.status_code == 201
    assert [question["content"] for question in response.json()] == [
        "Why do you want to participate?",
        "What is your experience?",
    ]
    assert [question["is_required"] for question in response.json()] == [True, False]

    saved_questions = list(
        await session.scalars(
            select(RegistrationQuestion)
            .where(RegistrationQuestion.hackathon_id == hackathon.id)
            .order_by(RegistrationQuestion.id)
        )
    )
    assert [question.content for question in saved_questions] == [
        "Why do you want to participate?",
        "What is your experience?",
    ]


@pytest.mark.parametrize("access_kind", ["organizer", "co_organizer"])
async def test_organizer_and_co_organizer_create_and_delete_question(
    access_kind: str,
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    co_organizer = await create_user(session, "co-organizer@example.com")
    hackathon = await create_hackathon(session, organizer)
    hackathon.co_organizers.append(co_organizer)
    await session.commit()
    current_user = organizer if access_kind == "organizer" else co_organizer
    force_authenticate(current_user)

    create_response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/questions",
        json={"content": "Team experience?", "is_required": False},
    )

    assert create_response.status_code == 201
    question_public_id = uuid.UUID(create_response.json()["public_id"])

    delete_response = await api_client.delete(
        f"/api/hackathons/{hackathon.public_id}/questions/{question_public_id}"
    )

    assert delete_response.status_code == 204
    assert (
        await session.scalar(
            select(RegistrationQuestion).where(RegistrationQuestion.public_id == question_public_id)
        )
        is None
    )


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
    assert (
        await session.scalar(
            select(RegistrationQuestion).where(RegistrationQuestion.public_id == question_public_id)
        )
        is None
    )


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


async def test_participant_lists_registration_questions(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    required_question = await create_question(session, hackathon, content="Why?")
    optional_question = await create_question(
        session,
        hackathon,
        content="Anything else?",
        is_required=False,
    )
    await session.commit()
    force_authenticate(participant)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/questions")

    assert response.status_code == 200
    assert response.json() == [
        {
            "public_id": str(required_question.public_id),
            "content": "Why?",
            "is_required": True,
        },
        {
            "public_id": str(optional_question.public_id),
            "content": "Anything else?",
            "is_required": False,
        },
    ]


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
        select(Registration).where(Registration.public_id == registration_public_id)
    )
    assert registration is not None
    assert registration.user_id == participant.id
    assert registration.hackathon_id == hackathon.id

    answer = await session.scalar(
        select(RegistrationAnswer).where(RegistrationAnswer.registration_id == registration.id)
    )
    assert answer is not None
    assert answer.question_id == question.id
    assert answer.content == "My answer"


async def test_user_cannot_register_when_registration_is_closed(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(
        session,
        organizer,
        registration_open=False,
    )
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
            ],
            "team": {"action": "create", "name": "Byte Buccaneers"},
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "error_code": "REGISTRATION_CLOSED",
        "detail": "Registration for this hackathon is closed.",
    }
    assert await session.scalar(select(Registration.id)) is None
    assert await session.scalar(select(Team.id)) is None


async def test_create_registration_rejects_mass_assignment_fields(
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
            ],
            "user_id": organizer.id,
            "team": {
                "action": "create",
                "name": "Byte Buccaneers",
                "hackathon_id": -1,
            },
        },
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"
    assert await session.scalar(select(Registration.id)) is None
    assert await session.scalar(select(Team.id)) is None


async def test_user_creates_registration_with_new_team(
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
            ],
            "team": {"action": "create", "name": "Byte Buccaneers"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["team"]["name"] == "Byte Buccaneers"
    assert len(body["team"]["join_code"]) == 8

    team = await session.scalar(
        select(Team).where(Team.public_id == uuid.UUID(body["team"]["public_id"]))
    )
    assert team is not None
    assert team.hackathon_id == hackathon.id


async def test_creating_team_retries_join_code_collision(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
    mocker,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    question = await create_question(session, hackathon)
    session.add(
        Team(
            hackathon=hackathon,
            name="Existing Team",
            join_code="COLLIDE1",
        )
    )
    await session.commit()
    mocker.patch(
        "src.teams.service.generate_join_code",
        side_effect=["COLLIDE1", "UNIQUE12"],
    )
    force_authenticate(participant)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={
            "answers": [
                {
                    "question_public_id": str(question.public_id),
                    "content": "My answer",
                }
            ],
            "team": {"action": "create", "name": "Byte Buccaneers"},
        },
    )

    assert response.status_code == 201
    assert response.json()["team"]["join_code"] == "UNIQUE12"
    assert await session.scalar(select(Team).where(Team.join_code == "UNIQUE12")) is not None


async def test_creating_team_returns_domain_error_after_join_code_retries(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
    mocker,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    question = await create_question(session, hackathon)
    session.add(
        Team(
            hackathon=hackathon,
            name="Existing Team",
            join_code="COLLIDE1",
        )
    )
    await session.commit()
    mocker.patch("src.teams.service.generate_join_code", return_value="COLLIDE1")
    force_authenticate(participant)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={
            "answers": [
                {
                    "question_public_id": str(question.public_id),
                    "content": "My answer",
                }
            ],
            "team": {"action": "create", "name": "Byte Buccaneers"},
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "error_code": "TEAM_JOIN_CODE_GENERATION_FAILED",
        "detail": "A unique team join code could not be generated. Please try again.",
    }
    assert await session.scalar(select(Registration.id)) is None


async def test_joining_missing_team_returns_not_found(
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
            ],
            "team": {"action": "join", "join_code": "MISSING1"},
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "error_code": "TEAM_NOT_FOUND",
        "detail": "Team does not exist for this hackathon.",
    }


async def test_join_code_cannot_be_used_for_another_hackathon(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    first_participant = await create_user(session, "first@example.com")
    second_participant = await create_user(session, "second@example.com")
    first_hackathon = await create_hackathon(session, organizer)
    second_hackathon = await create_hackathon(session, organizer)
    first_question = await create_question(session, first_hackathon)
    second_question = await create_question(session, second_hackathon)
    await session.commit()

    force_authenticate(first_participant)
    create_response = await api_client.post(
        f"/api/hackathons/{first_hackathon.public_id}/registrations",
        json={
            "answers": [
                {
                    "question_public_id": str(first_question.public_id),
                    "content": "My answer",
                }
            ],
            "team": {"action": "create", "name": "Byte Buccaneers"},
        },
    )
    assert create_response.status_code == 201
    join_code = create_response.json()["team"]["join_code"]

    force_authenticate(second_participant)
    response = await api_client.post(
        f"/api/hackathons/{second_hackathon.public_id}/registrations",
        json={
            "answers": [
                {
                    "question_public_id": str(second_question.public_id),
                    "content": "My answer",
                }
            ],
            "team": {"action": "join", "join_code": join_code},
        },
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "TEAM_NOT_FOUND"


async def test_joining_full_team_returns_conflict(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    first_participant = await create_user(session, "first@example.com")
    second_participant = await create_user(session, "second@example.com")
    hackathon = await create_hackathon(session, organizer, max_team_size=1)
    question = await create_question(session, hackathon)
    await session.commit()

    payload = {
        "answers": [
            {
                "question_public_id": str(question.public_id),
                "content": "My answer",
            }
        ]
    }
    force_authenticate(first_participant)
    create_response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={
            **payload,
            "team": {"action": "create", "name": "Byte Buccaneers"},
        },
    )
    assert create_response.status_code == 201
    join_code = create_response.json()["team"]["join_code"]

    force_authenticate(second_participant)
    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={
            **payload,
            "team": {"action": "join", "join_code": join_code},
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "error_code": "TEAM_FULL",
        "detail": "Team has reached its maximum number of members.",
    }


async def test_duplicate_team_name_returns_conflict(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    first_participant = await create_user(session, "first@example.com")
    second_participant = await create_user(session, "second@example.com")
    hackathon = await create_hackathon(session, organizer)
    question = await create_question(session, hackathon)
    await session.commit()

    payload = {
        "answers": [
            {
                "question_public_id": str(question.public_id),
                "content": "My answer",
            }
        ],
        "team": {"action": "create", "name": "Byte Buccaneers"},
    }
    force_authenticate(first_participant)
    first_response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json=payload,
    )
    assert first_response.status_code == 201

    force_authenticate(second_participant)
    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json=payload,
    )

    assert response.status_code == 409
    assert response.json() == {
        "error_code": "TEAM_NAME_ALREADY_EXISTS",
        "detail": "A team with this name already exists for this hackathon.",
    }


async def test_creating_team_is_rejected_when_teams_are_disabled(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer, teams_enabled=False)
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
            ],
            "team": {"action": "create", "name": "Byte Buccaneers"},
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "error_code": "TEAMS_DISABLED",
        "detail": "Teams are disabled for this hackathon.",
    }
    assert await session.scalar(select(Registration.id)) is None
    assert await session.scalar(select(Team.id)) is None


async def test_individual_registration_is_allowed_when_teams_are_disabled(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer, teams_enabled=False)
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
            ],
            "team": None,
        },
    )

    assert response.status_code == 201
    assert response.json()["team"] is None


async def test_user_creates_registration_with_multiple_answers(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    required_question = await create_question(
        session,
        hackathon,
        content="Why",
    )
    optional_question = await create_question(
        session,
        hackathon,
        content="What",
        is_required=False,
    )
    await session.commit()
    force_authenticate(participant)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={
            "answers": [
                {
                    "question_public_id": str(required_question.public_id),
                    "content": "noo",
                },
                {
                    "question_public_id": str(optional_question.public_id),
                    "content": "yes",
                },
            ]
        },
    )

    assert response.status_code == 201
    registration_public_id = uuid.UUID(response.json()["public_id"])
    registration = await session.scalar(
        select(Registration).where(Registration.public_id == registration_public_id)
    )
    assert registration is not None

    answers = await session.scalars(
        select(RegistrationAnswer).where(RegistrationAnswer.registration_id == registration.id)
    )
    answers_by_question_id = {answer.question_id: answer.content for answer in answers}
    assert answers_by_question_id == {
        required_question.id: "noo",
        optional_question.id: "yes",
    }


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
    team = Team(
        hackathon=hackathon,
        name="Byte Buccaneers",
        join_code="ABCD1234",
    )
    registration = Registration(user=participant, hackathon=hackathon, team=team)
    session.add(registration)
    await session.commit()
    registration_public_id = registration.public_id
    team_public_id = team.public_id
    force_authenticate(participant)

    response = await api_client.delete(f"/api/registrations/{registration_public_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert (
        await session.scalar(
            select(Registration).where(Registration.public_id == registration_public_id)
        )
        is None
    )
    assert await session.scalar(select(Team).where(Team.public_id == team_public_id)) is None


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


@pytest.mark.parametrize("access_kind", ["admin", "organizer", "co_organizer"])
async def test_authorized_user_lists_registrations_with_answers(
    access_kind: str,
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    co_organizer = await create_user(session, "co-organizer@example.com")
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    hackathon.co_organizers.append(co_organizer)
    question = await create_question(session, hackathon, content="Why participate?")
    registration = Registration(
        user=participant,
        hackathon=hackathon,
        answers=[RegistrationAnswer(question=question, content="To build something useful")],
    )
    session.add(registration)
    await session.commit()

    current_user = {
        "admin": admin,
        "organizer": organizer,
        "co_organizer": co_organizer,
    }[access_kind]
    force_authenticate(current_user)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/registrations")

    assert response.status_code == 200
    assert response.json() == [
        {
            "public_id": str(registration.public_id),
            "status": "pending",
            "team": None,
            "user": {
                "public_id": str(participant.public_id),
                "name": participant.name,
                "email": participant.email,
            },
            "answers": [
                {
                    "content": "To build something useful",
                    "question": {
                        "public_id": str(question.public_id),
                        "content": "Why participate?",
                        "is_required": True,
                    },
                }
            ],
        }
    ]


async def test_regular_user_cannot_list_hackathon_registrations(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    await session.commit()
    force_authenticate(participant)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/registrations")

    assert response.status_code == 403
    assert response.json()["error_code"] == "REGISTRATION_PERMISSION_DENIED"


async def test_participant_gets_own_registration_with_answers(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    question = await create_question(session, hackathon, content="Why participate?")
    registration = Registration(
        user=participant,
        hackathon=hackathon,
        answers=[RegistrationAnswer(question=question, content="To learn")],
    )
    session.add(registration)
    await session.commit()
    force_authenticate(participant)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/registrations/me")

    assert response.status_code == 200
    assert response.json() == {
        "public_id": str(registration.public_id),
        "status": "pending",
        "team": None,
        "user": {
            "public_id": str(participant.public_id),
            "name": participant.name,
            "email": participant.email,
        },
        "answers": [
            {
                "content": "To learn",
                "question": {
                    "public_id": str(question.public_id),
                    "content": "Why participate?",
                    "is_required": True,
                },
            }
        ],
    }


async def test_participant_cannot_get_another_users_registration_as_own(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    outsider = await create_user(session, "outsider@example.com")
    hackathon = await create_hackathon(session, organizer)
    session.add(Registration(user=participant, hackathon=hackathon))
    await session.commit()
    force_authenticate(outsider)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/registrations/me")

    assert response.status_code == 404
    assert response.json()["error_code"] == "REGISTRATION_NOT_FOUND"


@pytest.mark.parametrize("access_kind", ["admin", "organizer", "co_organizer"])
@pytest.mark.parametrize(
    "new_status",
    [RegistrationStatus.ACCEPTED, RegistrationStatus.REJECTED],
)
async def test_authorized_user_updates_registration_status(
    access_kind: str,
    new_status: RegistrationStatus,
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    co_organizer = await create_user(session, "co-organizer@example.com")
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    hackathon.co_organizers.append(co_organizer)
    registration = Registration(user=participant, hackathon=hackathon)
    session.add(registration)
    await session.commit()

    current_user = {
        "admin": admin,
        "organizer": organizer,
        "co_organizer": co_organizer,
    }[access_kind]
    force_authenticate(current_user)

    response = await api_client.patch(
        f"/api/registrations/{registration.public_id}/status",
        json={"status": new_status.value},
    )

    assert response.status_code == 200
    assert response.json() == {
        "public_id": str(registration.public_id),
        "status": new_status.value,
        "team": None,
    }
    await session.refresh(registration)
    assert registration.status is new_status


async def test_regular_user_cannot_update_registration_status(
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
    force_authenticate(participant)

    response = await api_client.patch(
        f"/api/registrations/{registration.public_id}/status",
        json={"status": "accepted"},
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "REGISTRATION_PERMISSION_DENIED"
    await session.refresh(registration)
    assert registration.status is RegistrationStatus.PENDING


async def test_update_registration_status_rejects_pending_value(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, admin)
    registration = Registration(user=participant, hackathon=hackathon)
    session.add(registration)
    await session.commit()
    force_authenticate(admin)

    response = await api_client.patch(
        f"/api/registrations/{registration.public_id}/status",
        json={"status": "pending"},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


async def test_create_registration_requires_authentication(
    api_client: AsyncClient,
):
    response = await api_client.post(
        f"/api/hackathons/{uuid.uuid4()}/registrations",
        json={
            "answers": [
                {
                    "question_public_id": str(uuid.uuid4()),
                    "content": "My answer",
                }
            ],
            "team": {"action": "join", "join_code": "ABCD1234"},
        },
    )

    assert response.status_code == 401
