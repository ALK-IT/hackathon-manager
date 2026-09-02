import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.hackathon_tasks.models import HackathonTask
from src.hackathons.models import Hackathon
from src.main import app
from src.registration.models import Registration, RegistrationStatus
from src.teams.models import Team

ForceAuthenticate = Callable[[User | None], None]


async def create_user(
    session: AsyncSession,
    email: str,
    *,
    role: UserRole = UserRole.USER,
) -> User:
    user = User(
        name=email.split("@", maxsplit=1)[0].title(),
        email=f"{uuid.uuid4()}-{email}",
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
    tasks_released: bool = True,
    ended: bool = False,
) -> Hackathon:
    now = datetime.now(UTC)
    start_date = now - timedelta(hours=1)
    end_date = now - timedelta(minutes=1) if ended else now + timedelta(days=1)
    hackathon = Hackathon(
        organizer=organizer,
        co_organizers=[],
        name="Task Test Hackathon",
        description="Build a useful application.",
        start_date=start_date,
        end_date=end_date,
        registration_opens_at=start_date - timedelta(days=2),
        registration_deadline=start_date - timedelta(days=1),
        registration_open=False,
        capacity=50,
        max_team_size=4,
        teams_enabled=True,
        tasks_released_at=(
            now - timedelta(minutes=1) if tasks_released else now + timedelta(hours=1)
        ),
    )
    session.add(hackathon)
    await session.flush()
    return hackathon


async def create_team_with_participants(
    session: AsyncSession,
    hackathon: Hackathon,
    *participants: User,
) -> Team:
    team = Team(
        hackathon=hackathon,
        name="Byte Buccaneers",
        join_code=uuid.uuid4().hex[:8].upper(),
    )
    session.add(team)
    await session.flush()
    session.add_all(
        [
            Registration(
                user=participant,
                hackathon=hackathon,
                team=team,
                status=RegistrationStatus.ACCEPTED,
            )
            for participant in participants
        ]
    )
    await session.flush()
    return team


def test_task_routes_are_registered():
    paths = set(app.openapi()["paths"])
    assert {
        "/api/hackathons/{hackathon_public_id}/tasks",
        "/api/hackathons/{hackathon_public_id}/tasks/{task_public_id}",
        "/api/hackathons/{hackathon_public_id}/tasks/{task_public_id}/submission",
        "/api/hackathons/{hackathon_public_id}/tasks/{task_public_id}/submissions",
    }.issubset(paths)


async def test_manager_creates_updates_and_deletes_task(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    hackathon = await create_hackathon(session, admin)
    await session.commit()
    force_authenticate(admin)

    create_response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/tasks",
        json={"title": "API", "description": "Build a REST API."},
    )
    assert create_response.status_code == 201
    task_public_id = create_response.json()["public_id"]

    update_response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task_public_id}",
        json={"title": "Public API"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Public API"

    delete_response = await api_client.delete(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task_public_id}"
    )
    assert delete_response.status_code == 204


async def test_regular_user_cannot_create_task(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, admin)
    await session.commit()
    force_authenticate(participant)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/tasks",
        json={"title": "API", "description": "Build a REST API."},
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "TASK_PERMISSION_DENIED"


async def test_accepted_participant_sees_tasks_only_after_release(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, admin, tasks_released=False)
    await create_team_with_participants(session, hackathon, participant)
    session.add(HackathonTask(hackathon=hackathon, title="API", description="Build it."))
    await session.commit()
    force_authenticate(participant)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/tasks")

    assert response.status_code == 403
    assert response.json()["error_code"] == "TASKS_NOT_RELEASED"


async def test_team_members_share_one_submission_and_manager_can_list_it(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    first_member = await create_user(session, "first@example.com")
    second_member = await create_user(session, "second@example.com")
    hackathon = await create_hackathon(session, admin)
    team = await create_team_with_participants(session, hackathon, first_member, second_member)
    task = HackathonTask(hackathon=hackathon, title="API", description="Build it.")
    session.add(task)
    await session.commit()

    force_authenticate(first_member)
    first_response = await api_client.put(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}/submission",
        json={"github_url": "https://github.com/example/first-repo"},
    )
    assert first_response.status_code == 200
    submission_public_id = first_response.json()["public_id"]
    assert first_response.json()["team"]["public_id"] == str(team.public_id)

    force_authenticate(second_member)
    second_response = await api_client.put(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}/submission",
        json={"github_url": "https://www.github.com/example/final-repo/"},
    )
    assert second_response.status_code == 200
    assert second_response.json()["public_id"] == submission_public_id
    assert second_response.json()["github_url"] == "https://github.com/example/final-repo"
    assert second_response.json()["submitted_by"]["public_id"] == str(second_member.public_id)

    force_authenticate(admin)
    list_response = await api_client.get(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}/submissions"
    )
    assert list_response.status_code == 200
    assert [item["public_id"] for item in list_response.json()] == [submission_public_id]


async def test_participant_area_contains_description_tasks_and_team_submission(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, admin)
    await create_team_with_participants(session, hackathon, participant)
    task = HackathonTask(hackathon=hackathon, title="API", description="Build it.")
    session.add(task)
    await session.commit()
    force_authenticate(participant)

    await api_client.put(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}/submission",
        json={"github_url": "https://github.com/example/repo"},
    )
    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/participant-area")

    assert response.status_code == 200
    body = response.json()
    assert body["description"] == hackathon.description
    assert body["tasks"][0]["public_id"] == str(task.public_id)
    assert body["tasks"][0]["submission"]["github_url"] == "https://github.com/example/repo"


async def test_accepted_participant_without_team_cannot_submit(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, admin)
    task = HackathonTask(hackathon=hackathon, title="API", description="Build it.")
    session.add_all(
        [
            task,
            Registration(
                user=participant,
                hackathon=hackathon,
                status=RegistrationStatus.ACCEPTED,
            ),
        ]
    )
    await session.commit()
    force_authenticate(participant)

    response = await api_client.put(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}/submission",
        json={"github_url": "https://github.com/example/repo"},
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "TEAM_REQUIRED_FOR_SUBMISSION"


async def test_submission_rejects_invalid_github_url(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, admin)
    await create_team_with_participants(session, hackathon, participant)
    task = HackathonTask(hackathon=hackathon, title="API", description="Build it.")
    session.add(task)
    await session.commit()
    force_authenticate(participant)

    for invalid_url in ("https://example.com/repo", "https://github.com/example"):
        response = await api_client.put(
            f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}/submission",
            json={"github_url": invalid_url},
        )

        assert response.status_code == 422
        assert response.json()["error_code"] == "VALIDATION_ERROR"


async def test_submission_requires_authentication(api_client: AsyncClient):
    response = await api_client.put(
        f"/api/hackathons/{uuid.uuid4()}/tasks/{uuid.uuid4()}/submission",
        json={"github_url": "https://github.com/example/repo"},
    )

    assert response.status_code == 401
