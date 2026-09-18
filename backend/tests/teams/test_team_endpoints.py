import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.hackathons.models import Hackathon

ForceAuthenticate = Callable[[User | None], None]


async def create_user(session: AsyncSession, email: str) -> User:
    user = User(
        name=email.split("@", maxsplit=1)[0].title(),
        email=f"{uuid.uuid4()}-{email}",
        password_hash="test-password-hash",
    )
    session.add(user)
    await session.flush()
    return user


async def create_hackathon(
    session: AsyncSession,
    organizer: User,
    *,
    max_team_size: int = 4,
    teams_enabled: bool = True,
) -> Hackathon:
    now = datetime.now(UTC)
    hackathon = Hackathon(
        organizer=organizer,
        co_organizers=[],
        name=f"Team endpoint test {uuid.uuid4()}",
        description="Team endpoint integration test",
        start_date=now + timedelta(days=1),
        end_date=now + timedelta(days=2),
        registration_opens_at=now - timedelta(hours=1),
        registration_deadline=now + timedelta(hours=12),
        registration_open=True,
        capacity=50,
        max_team_size=max_team_size,
        teams_enabled=teams_enabled,
    )
    session.add(hackathon)
    await session.flush()
    return hackathon


async def test_user_joins_team_through_join_code(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    creator = await create_user(session, "creator@example.com")
    joining_user = await create_user(session, "joining@example.com")
    hackathon = await create_hackathon(session, organizer)
    await session.commit()

    force_authenticate(creator)
    create_response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={"team": {"action": "create", "name": "Byte Buccaneers"}},
    )
    assert create_response.status_code == 201
    join_code = create_response.json()["team"]["join_code"]

    force_authenticate(joining_user)
    join_response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={"team": {"action": "join", "join_code": join_code.lower()}},
    )

    assert join_response.status_code == 201
    assert join_response.json()["team"]["public_id"] == create_response.json()["team"]["public_id"]
    assert join_response.json()["team"]["join_code"] == join_code


async def test_joining_full_team_is_rejected(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    creator = await create_user(session, "creator@example.com")
    joining_user = await create_user(session, "joining@example.com")
    hackathon = await create_hackathon(session, organizer, max_team_size=1)
    await session.commit()

    force_authenticate(creator)
    create_response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={"team": {"action": "create", "name": "Full Team"}},
    )
    assert create_response.status_code == 201
    force_authenticate(joining_user)
    join_response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={
            "team": {
                "action": "join",
                "join_code": create_response.json()["team"]["join_code"],
            }
        },
    )

    assert join_response.status_code == 409
    assert join_response.json()["error_code"] == "TEAM_FULL"


async def test_team_registration_is_rejected_when_teams_are_disabled(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer, teams_enabled=False)
    await session.commit()
    force_authenticate(participant)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={"team": {"action": "create", "name": "Disabled Team"}},
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "TEAMS_DISABLED"


async def test_team_registration_requires_authentication(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    hackathon = await create_hackathon(session, organizer)
    await session.commit()
    force_authenticate(None)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations",
        json={"team": {"action": "join", "join_code": "ABCD1234"}},
    )

    assert response.status_code == 401
