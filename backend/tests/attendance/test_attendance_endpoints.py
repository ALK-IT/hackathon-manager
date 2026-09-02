from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.attendance.models import CheckIn, CheckInSession
from src.auth.models import User, UserRole
from src.hackathons.models import Hackathon
from src.registration.models import Registration, RegistrationStatus


def make_user(*, name: str, email: str, role: UserRole = UserRole.USER) -> User:
    return User(
        name=name,
        email=email,
        password_hash="not-used-in-tests",
        role=role,
    )


def make_hackathon(organizer: User) -> Hackathon:
    now = datetime.now(UTC)
    return Hackathon(
        organizer=organizer,
        name="Attendance Hackathon",
        start_date=now + timedelta(days=1),
        end_date=now + timedelta(days=2),
        registration_opens_at=now - timedelta(days=2),
        registration_deadline=now + timedelta(hours=12),
        registration_open=True,
        max_team_size=4,
    )


async def test_list_check_ins_returns_participants_from_all_sessions(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    now = datetime.now(UTC)
    organizer = make_user(
        name="Organizer",
        email="organizer-attendance@example.com",
        role=UserRole.ADMIN,
    )
    first_participant = make_user(
        name="First Participant",
        email="first-attendance@example.com",
    )
    second_participant = make_user(
        name="Second Participant",
        email="second-attendance@example.com",
    )
    hackathon = make_hackathon(organizer)
    first_registration = Registration(
        user=first_participant,
        hackathon=hackathon,
        status=RegistrationStatus.ACCEPTED,
    )
    second_registration = Registration(
        user=second_participant,
        hackathon=hackathon,
        status=RegistrationStatus.ACCEPTED,
    )
    old_session = CheckInSession(
        hackathon=hackathon,
        token_hash="a" * 64,
        expires_at=now - timedelta(minutes=5),
        is_active=False,
        created_by=organizer,
    )
    active_session = CheckInSession(
        hackathon=hackathon,
        token_hash="b" * 64,
        expires_at=now + timedelta(minutes=15),
        created_by=organizer,
    )
    first_check_in = CheckIn(
        registration=first_registration,
        session=old_session,
        checked_in_at=now - timedelta(minutes=10),
    )
    second_check_in = CheckIn(
        registration=second_registration,
        session=active_session,
        checked_in_at=now,
    )
    session.add_all([first_check_in, second_check_in])
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/check-ins")

    assert response.status_code == 200
    assert [item["participant"]["name"] for item in response.json()] == [
        "First Participant",
        "Second Participant",
    ]
    assert response.json()[0]["registration_public_id"] == str(first_registration.public_id)
    assert response.json()[1]["registration_public_id"] == str(second_registration.public_id)


async def test_list_check_ins_returns_empty_list_when_nobody_checked_in(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    organizer = make_user(
        name="Empty Organizer",
        email="empty-organizer-attendance@example.com",
        role=UserRole.ADMIN,
    )
    hackathon = make_hackathon(organizer)
    session.add(hackathon)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/check-ins")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_check_ins_rejects_user_without_management_permission(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    organizer = make_user(
        name="Protected Organizer",
        email="protected-organizer-attendance@example.com",
        role=UserRole.ADMIN,
    )
    regular_user = make_user(
        name="Outside User",
        email="outside-attendance@example.com",
    )
    hackathon = make_hackathon(organizer)
    session.add_all([hackathon, regular_user])
    await session.commit()
    force_authenticate(regular_user)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/check-ins")

    assert response.status_code == 403
    assert response.json() == {
        "error_code": "PERMISSION_DENIED",
        "detail": "Only hackathon organizers can manage check-in sessions.",
    }
