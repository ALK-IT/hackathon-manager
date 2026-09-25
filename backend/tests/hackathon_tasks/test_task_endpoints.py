import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.hackathon_tasks.models import HackathonTask, TaskSubmission
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
        "/api/hackathons/{hackathon_public_id}/task-submissions",
        "/api/hackathons/{hackathon_public_id}/leaderboard",
        "/api/hackathons/{hackathon_public_id}/tasks",
        "/api/hackathons/{hackathon_public_id}/tasks/{task_public_id}",
        "/api/hackathons/{hackathon_public_id}/tasks/{task_public_id}/submission",
        "/api/hackathons/{hackathon_public_id}/tasks/{task_public_id}/submissions",
        "/api/hackathons/{hackathon_public_id}/tasks/{task_public_id}/submissions/{submission_public_id}/evaluation",
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
        json={
            "title": "API",
            "description": "Build a REST API.",
            "visible_from": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
            "criteria": [
                {"name": "Code quality", "description": "Readable code", "max_points": 20}
            ],
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["visible_from"] is not None
    assert create_response.json()["criteria"] == [
        {"name": "Code quality", "description": "Readable code", "max_points": 20}
    ]
    task_public_id = create_response.json()["public_id"]

    update_response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task_public_id}",
        json={
            "title": "Public API",
            "criteria": [{"name": "Security", "description": "", "max_points": 15}],
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["public_id"] == task_public_id
    assert update_response.json()["title"] == "Public API"
    assert update_response.json()["criteria"][0]["name"] == "Security"

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


async def test_user_without_accepted_registration_cannot_list_tasks(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    user = await create_user(session, "user@example.com")
    hackathon = await create_hackathon(session, admin)
    await session.commit()
    force_authenticate(user)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/tasks")

    assert response.status_code == 403
    assert response.json()["error_code"] == "REGISTRATION_NOT_ACCEPTED"


async def test_task_visibility_must_be_before_hackathon_end(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    hackathon = await create_hackathon(session, admin)
    await session.commit()
    force_authenticate(admin)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/tasks",
        json={
            "title": "API",
            "description": "Build a REST API.",
            "visible_from": hackathon.end_date.isoformat(),
        },
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_TASK_VISIBILITY_DATE"


async def test_task_update_rejects_visibility_at_hackathon_end(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    hackathon = await create_hackathon(session, admin)
    task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=datetime.now(UTC),
    )
    session.add(task)
    await session.commit()
    force_authenticate(admin)

    response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}",
        json={"visible_from": hackathon.end_date.isoformat()},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_TASK_VISIBILITY_DATE"


async def test_accepted_participant_sees_only_released_tasks(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, admin)
    await create_team_with_participants(session, hackathon, participant)
    session.add(
        HackathonTask(
            hackathon=hackathon,
            title="API",
            description="Build it.",
            visible_from=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    await session.commit()
    force_authenticate(participant)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/tasks")

    assert response.status_code == 200
    assert response.json() == []


async def test_participant_cannot_submit_before_task_is_released(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, admin)
    await create_team_with_participants(session, hackathon, participant)
    task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=datetime.now(UTC) + timedelta(hours=1),
    )
    session.add(task)
    await session.commit()
    force_authenticate(participant)

    response = await api_client.put(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}/submission",
        json={"github_url": "https://github.com/example/repo"},
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "TASKS_NOT_RELEASED"


async def test_participant_cannot_submit_after_hackathon_has_ended(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, admin, ended=True)
    await create_team_with_participants(session, hackathon, participant)
    task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=hackathon.start_date,
    )
    session.add(task)
    await session.commit()
    force_authenticate(participant)

    response = await api_client.put(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}/submission",
        json={"github_url": "https://github.com/example/repo"},
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "TASK_SUBMISSION_CLOSED"


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
    task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=datetime.now(UTC) - timedelta(minutes=1),
    )
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
    assert [item["public_id"] for item in list_response.json()["items"]] == [submission_public_id]


async def test_manager_evaluates_submission_without_changing_its_author(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer, ended=True)
    team = await create_team_with_participants(session, hackathon, participant)
    task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=datetime.now(UTC) - timedelta(minutes=1),
    )
    submission = TaskSubmission(
        task=task,
        team=team,
        github_url="https://github.com/example/repo",
        submitted_by=participant,
    )
    session.add(submission)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}"
        f"/submissions/{submission.public_id}/evaluation",
        json={"score": 8.75, "feedback": "Solid implementation."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 8.75
    assert body["feedback"] == "Solid implementation."
    assert body["evaluated_by"] == {
        "public_id": str(organizer.public_id),
        "name": organizer.name,
    }
    assert body["evaluated_at"] is not None

    await session.refresh(submission)
    assert submission.score == Decimal("8.75")
    assert submission.feedback == "Solid implementation."
    assert submission.evaluated_by_id == organizer.id
    assert submission.evaluated_at is not None
    assert submission.submitted_by_id == participant.id


async def test_co_organizer_can_evaluate_submission(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com", role=UserRole.ADMIN)
    co_organizer = await create_user(session, "co-organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer, ended=True)
    hackathon.co_organizers.append(co_organizer)
    team = await create_team_with_participants(session, hackathon, participant)
    task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=datetime.now(UTC) - timedelta(minutes=1),
    )
    submission = TaskSubmission(
        task=task,
        team=team,
        github_url="https://github.com/example/repo",
        submitted_by=participant,
    )
    session.add(submission)
    await session.commit()
    force_authenticate(co_organizer)

    response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}"
        f"/submissions/{submission.public_id}/evaluation",
        json={"score": 7.5},
    )

    assert response.status_code == 200
    assert response.json()["evaluated_by"]["public_id"] == str(co_organizer.public_id)


async def test_participant_cannot_evaluate_submission(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    team = await create_team_with_participants(session, hackathon, participant)
    task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=datetime.now(UTC) - timedelta(minutes=1),
    )
    submission = TaskSubmission(
        task=task,
        team=team,
        github_url="https://github.com/example/repo",
        submitted_by=participant,
    )
    session.add(submission)
    await session.commit()
    force_authenticate(participant)

    response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}"
        f"/submissions/{submission.public_id}/evaluation",
        json={"score": 10},
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "TASK_PERMISSION_DENIED"


async def test_evaluation_rejects_submission_from_another_task(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer, ended=True)
    team = await create_team_with_participants(session, hackathon, participant)
    first_task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=datetime.now(UTC) - timedelta(minutes=1),
    )
    second_task = HackathonTask(
        hackathon=hackathon,
        title="Frontend",
        description="Build it too.",
        visible_from=datetime.now(UTC) - timedelta(minutes=1),
    )
    submission = TaskSubmission(
        task=first_task,
        team=team,
        github_url="https://github.com/example/repo",
        submitted_by=participant,
    )
    session.add_all([second_task, submission])
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/tasks/{second_task.public_id}"
        f"/submissions/{submission.public_id}/evaluation",
        json={"score": 8},
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "TASK_SUBMISSION_NOT_FOUND"


@pytest.mark.parametrize("score", [-0.01, 10.01, 1.234])
async def test_evaluation_validates_score(
    score: float,
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com", role=UserRole.ADMIN)
    hackathon = await create_hackathon(session, organizer)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/tasks/{uuid.uuid4()}"
        f"/submissions/{uuid.uuid4()}/evaluation",
        json={"score": score},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


async def test_database_rejects_score_outside_range(
    session: AsyncSession,
):
    organizer = await create_user(session, "organizer@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    team = await create_team_with_participants(session, hackathon, participant)
    task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=datetime.now(UTC) - timedelta(minutes=1),
    )
    submission = TaskSubmission(
        task=task,
        team=team,
        github_url="https://github.com/example/repo",
        submitted_by=participant,
        score=Decimal("10.01"),
    )
    session.add(submission)

    with pytest.raises(IntegrityError):
        await session.commit()

    await session.rollback()


async def test_participant_area_contains_description_tasks_and_team_submission(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    admin = await create_user(session, "admin@example.com", role=UserRole.ADMIN)
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, admin)
    await create_team_with_participants(session, hackathon, participant)
    task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=datetime.now(UTC) - timedelta(minutes=1),
    )
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
    task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=datetime.now(UTC) - timedelta(minutes=1),
    )
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
    task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=datetime.now(UTC) - timedelta(minutes=1),
    )
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


async def test_evaluation_is_not_open_during_hackathon(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    team = await create_team_with_participants(session, hackathon, participant)
    task = HackathonTask(
        hackathon=hackathon,
        title="API",
        description="Build it.",
        visible_from=hackathon.start_date,
    )
    submission = TaskSubmission(
        task=task,
        team=team,
        submitted_by=participant,
        github_url="https://github.com/example/repo",
    )
    session.add(submission)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/tasks/{task.public_id}"
        f"/submissions/{submission.public_id}/evaluation",
        json={"score": 0},
    )
    assert response.status_code == 409
    assert response.json()["error_code"] == "TASK_EVALUATION_NOT_OPEN"
    await session.refresh(submission)
    assert submission.score is None
    assert submission.evaluated_at is None


@pytest.mark.parametrize("access", ["owner", "co_organizer", "admin"])
async def test_manager_lists_only_requested_hackathon_submissions(
    access: str,
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    owner = await create_user(session, "owner@example.com")
    manager = (
        owner
        if access == "owner"
        else await create_user(
            session,
            "manager@example.com",
            role=UserRole.ADMIN if access == "admin" else UserRole.USER,
        )
    )
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, owner, ended=True)
    if access == "co_organizer":
        hackathon.co_organizers.append(manager)
    other_hackathon = await create_hackathon(session, owner, ended=True)
    submissions = []
    for event in (hackathon, other_hackathon):
        team = await create_team_with_participants(session, event, participant)
        for index in range(2):
            task = HackathonTask(
                hackathon=event,
                title=f"Task {index}",
                description="Build it.",
                visible_from=event.start_date,
            )
            submission = TaskSubmission(
                task=task,
                team=team,
                submitted_by=participant,
                github_url="https://github.com/example/repo",
                score=Decimal(0) if index == 0 else None,
                feedback="Needs work." if index == 0 else None,
                evaluated_at=datetime.now(UTC) if index == 0 else None,
                evaluated_by=owner if index == 0 else None,
            )
            session.add(submission)
            if event is hackathon:
                submissions.append(submission)
    await session.commit()
    event_id = hackathon.public_id
    expected_ids = [str(item.public_id) for item in submissions]
    expected_task_ids = [str(item.task.public_id) for item in submissions]
    # Force queries to load relationships rather than reuse objects built by this test.
    session.expunge_all()
    force_authenticate(manager)

    response = await api_client.get(f"/api/hackathons/{event_id}/task-submissions")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    body = response.json()["items"]
    assert [item["public_id"] for item in body] == expected_ids
    assert [item["task"]["public_id"] for item in body] == expected_task_ids
    assert body[0]["evaluation"]["score"] == 0
    assert body[0]["evaluation"]["evaluated_by"]["public_id"] == str(owner.public_id)
    assert body[1]["evaluation"] is None
    assert body[0]["team"]["name"] == "Byte Buccaneers"
    assert "join_code" not in body[0]["team"]

    leaderboard = await api_client.get(
        f"/api/hackathons/{event_id}/leaderboard", params={"limit": 5}
    )
    assert leaderboard.status_code == 200
    assert leaderboard.json()["items"] == [
        {
            "rank": 1,
            "team_public_id": body[0]["team"]["public_id"],
            "team_name": "Byte Buccaneers",
            "total_score": 0.0,
            "evaluated_tasks": 1,
        }
    ]
    visibility = await api_client.patch(
        f"/api/hackathons/{event_id}/leaderboard-visibility", json={"visible": True}
    )
    assert visibility.status_code == 200
    assert visibility.json() == {"visible": True}

    path = f"/api/hackathons/{event_id}/task-submissions"
    page = await api_client.get(path, params={"limit": 1, "offset": 1})
    assert page.json()["total"] == 2
    assert page.json()["limit"] == 1
    assert page.json()["offset"] == 1
    assert [item["public_id"] for item in page.json()["items"]] == expected_ids[1:]
    past_end = await api_client.get(path, params={"offset": 100})
    assert past_end.json()["items"] == []
    assert past_end.json()["total"] == 2
    for evaluated, expected in (("true", expected_ids[:1]), ("false", expected_ids[1:])):
        filtered = await api_client.get(path, params={"evaluated": evaluated})
        assert filtered.status_code == 200
        assert filtered.json()["total"] == 1
        assert [item["public_id"] for item in filtered.json()["items"]] == expected
    filters = {
        "team_public_id": body[0]["team"]["public_id"],
        "task_public_id": expected_task_ids[0],
        "evaluated": "true",
    }
    combined = await api_client.get(path, params=filters)
    assert combined.json()["total"] == 1
    assert combined.json()["items"][0]["public_id"] == expected_ids[0]
    for key in ("team_public_id", "task_public_id"):
        mismatch = await api_client.get(path, params={**filters, key: str(uuid.uuid4())})
        assert mismatch.json()["total"] == 0
        assert mismatch.json()["items"] == []
    foreign_task = await api_client.get(path, params={"task_public_id": str(task.public_id)})
    assert foreign_task.json()["total"] == 0

    task_path = f"/api/hackathons/{event_id}/tasks/{expected_task_ids[0]}/submissions"
    task_page = await api_client.get(task_path, params={"limit": 1})
    assert task_page.status_code == 200
    assert task_page.json()["total"] == 1
    assert task_page.json()["items"][0]["public_id"] == expected_ids[0]
    empty_task_page = await api_client.get(task_path, params={"offset": 1})
    assert empty_task_page.json()["items"] == []
    assert empty_task_page.json()["total"] == 1

    force_authenticate(participant)
    area = await api_client.get(f"/api/hackathons/{event_id}/participant-area")
    assert area.status_code == 200
    assert area.json()["leaderboard_visible_to_participants"] is True
    assert area.json()["tasks"][0]["submission"]["evaluation"]["score"] == 0
    participant_leaderboard = await api_client.get(f"/api/hackathons/{event_id}/leaderboard")
    assert participant_leaderboard.status_code == 200


async def test_hackathon_submissions_access_and_empty_results(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    owner = await create_user(session, "owner@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, owner)
    await create_team_with_participants(session, hackathon, participant)
    await session.commit()
    path = f"/api/hackathons/{hackathon.public_id}/task-submissions"
    response = await api_client.get(path)
    assert response.status_code == 401

    force_authenticate(participant)
    response = await api_client.get(path)
    assert response.status_code == 403
    assert response.json()["error_code"] == "TASK_PERMISSION_DENIED"

    force_authenticate(owner)
    response = await api_client.get(path)
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}
    response = await api_client.get(f"/api/hackathons/{uuid.uuid4()}/task-submissions")
    assert response.status_code == 404
    hackathon.is_deleted = True
    await session.commit()
    response = await api_client.get(path)
    assert response.status_code == 404


@pytest.mark.parametrize("suffix", ["task-submissions", "tasks/{task_id}/submissions"])
@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
async def test_submission_pagination_validation(
    suffix: str,
    params: dict[str, int],
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    owner = await create_user(session, "owner@example.com")
    force_authenticate(owner)
    path = suffix.format(task_id=uuid.uuid4())
    response = await api_client.get(f"/api/hackathons/{uuid.uuid4()}/{path}", params=params)
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "params",
    [
        {"team_public_id": "invalid"},
        {"task_public_id": "invalid"},
        {"evaluated": "invalid"},
    ],
)
async def test_submission_filter_validation(
    params: dict[str, str],
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    owner = await create_user(session, "owner@example.com")
    force_authenticate(owner)
    response = await api_client.get(
        f"/api/hackathons/{uuid.uuid4()}/task-submissions",
        params=params,
    )
    assert response.status_code == 422
