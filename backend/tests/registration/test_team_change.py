import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.registration.dependencies import get_registration_service
from src.registration.models import (
    Registration,
    RegistrationAnswer,
    RegistrationQuestion,
    RegistrationStatus,
)
from src.resources.models import Resource, ResourceAssignment, ResourceItem
from src.teams.exceptions import TeamFullError
from src.teams.models import Team
from src.teams.schemas import TeamChangeRequest
from tests.registration.test_registration_endpoints import create_hackathon, create_user


@pytest.fixture
async def setup_teams(session):
    owner = await create_user(session, "owner@example.com")
    user = await create_user(session, "member@example.com")
    hackathon = await create_hackathon(session, owner, max_team_size=1)
    old = Team(name="Old", join_code="OLD12345", hackathon_id=hackathon.id)
    new = Team(name="New", join_code="NEW12345", hackathon_id=hackathon.id)
    session.add_all([old, new])
    await session.flush()
    registration = Registration(
        user=user, hackathon=hackathon, team=old, status=RegistrationStatus.ACCEPTED
    )
    session.add(registration)
    await session.commit()
    return user, hackathon, old, new, registration


async def test_change_preserves_registration_and_deletes_empty_team(
    session, api_client, force_authenticate, setup_teams
):
    user, hackathon, old, new, registration = setup_teams
    old_id, registration_id, public_id = old.id, registration.id, registration.public_id
    force_authenticate(user)
    response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/registrations/me/team",
        json={"join_code": " new12345 "},
    )
    assert response.status_code == 204
    await session.refresh(registration)
    assert registration.id == registration_id
    assert registration.public_id == public_id
    assert registration.status == RegistrationStatus.ACCEPTED
    assert registration.team_id == new.id
    assert await session.scalar(select(Team.id).where(Team.id == old_id)) is None


@pytest.mark.parametrize(
    "case,status,code",
    [
        ("started", 409, "TEAM_CHANGE_LOCKED"),
        ("pending", 403, "REGISTRATION_NOT_ACCEPTED"),
        ("rejected", 403, "REGISTRATION_NOT_ACCEPTED"),
        ("disabled", 409, "TEAMS_DISABLED"),
        ("full", 409, "TEAM_FULL"),
        ("other_hackathon", 404, "TEAM_NOT_FOUND"),
        ("missing", 404, "TEAM_NOT_FOUND"),
        ("deleted", 404, "HACKATHON_NOT_FOUND"),
    ],
)
async def test_rejected_changes_are_atomic(
    session, api_client, force_authenticate, setup_teams, case, status, code
):
    user, hackathon, old, new, registration = setup_teams
    if case == "started":
        hackathon.start_date = datetime.now(UTC) - timedelta(seconds=1)
        hackathon.registration_deadline = hackathon.start_date - timedelta(hours=1)
        hackathon.registration_opens_at = hackathon.registration_deadline - timedelta(hours=1)
    elif case in {"pending", "rejected"}:
        registration.status = RegistrationStatus(case)
    elif case == "disabled":
        hackathon.teams_enabled = False
    elif case == "full":
        other = await create_user(session, "other@example.com")
        session.add(
            Registration(
                user=other, hackathon=hackathon, team=new, status=RegistrationStatus.PENDING
            )
        )
    elif case == "other_hackathon":
        other = await create_hackathon(session, user)
        new.hackathon_id = other.id
    elif case == "deleted":
        hackathon.is_deleted = True
    await session.commit()
    old_id = old.id
    force_authenticate(user)
    response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/registrations/me/team",
        json={"join_code": "BAD12345" if case == "missing" else new.join_code},
    )
    assert response.status_code == status
    assert response.json()["error_code"] == code
    await session.refresh(registration)
    assert registration.team_id == old_id


async def test_same_team_is_noop_even_when_full(session, setup_teams):
    user, hackathon, old, _, registration = setup_teams
    await get_registration_service(session, AsyncMock()).change_team(
        hackathon.public_id, TeamChangeRequest(join_code=old.join_code), user
    )
    assert registration.team_id == old.id


async def test_two_changes_cannot_take_last_place(session, setup_teams):
    user, hackathon, _, new, _ = setup_teams
    other = await create_user(session, "second@example.com")
    session.add(Registration(user=other, hackathon=hackathon, status=RegistrationStatus.ACCEPTED))
    await session.commit()
    factory = async_sessionmaker(session.bind, expire_on_commit=False)

    async def change(user):
        async with factory() as worker:
            try:
                await get_registration_service(worker, AsyncMock()).change_team(
                    hackathon.public_id, TeamChangeRequest(join_code=new.join_code), user
                )
                return "ok"
            except TeamFullError:
                return "full"

    assert sorted(await asyncio.wait_for(asyncio.gather(change(user), change(other)), 10)) == [
        "full",
        "ok",
    ]


async def test_anonymous_cannot_change_team(api_client, setup_teams):
    _, hackathon, _, new, _ = setup_teams
    response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/registrations/me/team",
        json={"join_code": new.join_code},
    )
    assert response.status_code == 401


async def test_missing_registration_cannot_change_another_users_team(
    session, api_client, force_authenticate, setup_teams
):
    _, hackathon, old, new, registration = setup_teams
    outsider = await create_user(session, "outsider@example.com")
    await session.commit()
    old_id = old.id
    force_authenticate(outsider)
    response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}/registrations/me/team",
        json={"join_code": new.join_code},
    )
    assert response.status_code == 404
    assert response.json()["error_code"] == "REGISTRATION_NOT_FOUND"
    await session.refresh(registration)
    assert registration.team_id == old_id


async def test_preserves_answers_audit_and_old_team_resource_history(session, setup_teams):
    user, hackathon, old, new, registration = setup_teams
    question = RegistrationQuestion(hackathon_id=hackathon.id, content="Question")
    session.add(question)
    await session.flush()
    answer = RegistrationAnswer(
        registration_id=registration.id, question_id=question.id, content="Answer"
    )
    resource = Resource(
        hackathon_id=hackathon.id,
        name="Access",
        type="key",
        distribution_mode="manual",
        target="team",
    )
    item = ResourceItem(resource=resource, encrypted_value="test-ciphertext", is_assigned=True)
    assignment = ResourceAssignment(resource_item=item, team_id=old.id, assigned_by_id=user.id)
    registration.status_changed_at = datetime.now(UTC)
    registration.status_changed_by_id = user.id
    changed_at = registration.status_changed_at
    session.add_all([answer, assignment])
    await session.commit()
    old_id = old.id
    await get_registration_service(session, AsyncMock()).change_team(
        hackathon.public_id, TeamChangeRequest(join_code=new.join_code), user
    )
    await session.refresh(answer)
    await session.refresh(assignment)
    assert answer.content == "Answer"
    assert registration.status_changed_at == changed_at
    assert registration.status_changed_by_id == user.id
    assert assignment.team_id == old_id
    assert await session.scalar(select(Team.id).where(Team.id == old_id)) == old_id
