import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.attendance.models import CheckIn, CheckInSession
from src.auth.models import User, UserRole
from src.hackathons.models import Hackathon
from src.registration.models import Registration, RegistrationStatus
from src.teams.models import Team


def make_user():
    return User(name="Summary user", email=f"{uuid.uuid4()}@example.com", password_hash="unused")


def make_hackathon(owner):
    now = datetime.now(UTC)
    return Hackathon(
        organizer=owner,
        co_organizers=[],
        name="Summary",
        description="Test",
        start_date=now - timedelta(hours=1),
        end_date=now + timedelta(hours=1),
        registration_opens_at=now - timedelta(days=3),
        registration_deadline=now - timedelta(days=1),
        max_team_size=4,
    )


@pytest.mark.parametrize("actor", ["owner", "co_organizer", "admin", "outsider", "anonymous"])
async def test_summary_permissions_and_empty_counts(api_client, session, force_authenticate, actor):
    owner = make_user()
    user = owner if actor == "owner" else make_user()
    hackathon = make_hackathon(owner)
    if actor == "co_organizer":
        hackathon.co_organizers.append(user)
    if actor == "admin":
        user.role = UserRole.ADMIN
    session.add_all([hackathon, user])
    await session.commit()
    force_authenticate(None if actor == "anonymous" else user)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/summary")

    if actor == "anonymous":
        assert response.status_code == 401
    elif actor == "outsider":
        assert response.status_code == 403
        assert response.json()["error_code"] == "PERMISSION_DENIED"
    else:
        assert response.status_code == 200
        assert response.json() == {"accepted": 0, "teams": 0, "present": 0, "absent": 0}


@pytest.mark.parametrize("deleted", [False, True])
async def test_summary_missing_or_deleted_hackathon(
    api_client, session, force_authenticate, deleted
):
    owner = make_user()
    hackathon = make_hackathon(owner)
    hackathon.is_deleted = deleted
    session.add(hackathon)
    await session.commit()
    force_authenticate(owner)
    public_id = hackathon.public_id if deleted else uuid.uuid4()
    response = await api_client.get(f"/api/hackathons/{public_id}/summary")
    assert response.status_code == 404
    assert response.json()["error_code"] == "HACKATHON_NOT_FOUND"


async def test_summary_counts_distinct_accepted_teams_and_presence(
    api_client, session, force_authenticate
):
    owner = make_user()
    hackathon = make_hackathon(owner)
    other = make_hackathon(owner)
    teams = [Team(hackathon=hackathon, name=f"Team {i}", join_code=f"TEAM000{i}") for i in range(4)]
    old_session = CheckInSession(
        hackathon=hackathon,
        created_by=owner,
        token_hash="a" * 64,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
        is_active=False,
    )
    active_session = CheckInSession(
        hackathon=hackathon,
        created_by=owner,
        token_hash="b" * 64,
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
        is_active=True,
    )
    other_session = CheckInSession(
        hackathon=other,
        created_by=owner,
        token_hash="c" * 64,
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
        is_active=True,
    )
    session.add_all([hackathon, other, *teams, old_session, active_session, other_session])
    # Two accepted members of the same team must not count as two teams.
    for event, team, status, check_in_session in [
        (hackathon, teams[0], RegistrationStatus.ACCEPTED, old_session),
        (hackathon, teams[0], RegistrationStatus.ACCEPTED, None),
        (hackathon, teams[1], RegistrationStatus.ACCEPTED, active_session),
        (hackathon, None, RegistrationStatus.ACCEPTED, None),
        (hackathon, teams[2], RegistrationStatus.REJECTED, old_session),
        (hackathon, teams[2], RegistrationStatus.PENDING, None),
        (other, None, RegistrationStatus.ACCEPTED, other_session),
    ]:
        registration = Registration(hackathon=event, user=make_user(), team=team, status=status)
        session.add(registration)
        if check_in_session:
            session.add(CheckIn(registration=registration, session=check_in_session))
    await session.commit()
    force_authenticate(owner)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/summary")

    assert response.status_code == 200
    assert response.json() == {"accepted": 4, "teams": 2, "present": 2, "absent": 2}
