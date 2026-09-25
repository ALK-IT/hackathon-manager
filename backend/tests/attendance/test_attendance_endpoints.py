import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.attendance.models import CheckIn, CheckInSession
from src.auth.models import User, UserRole
from src.hackathons.models import Hackathon
from src.registration.models import Registration, RegistrationStatus
from src.teams.models import Team


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
        start_date=now - timedelta(hours=1),
        end_date=now + timedelta(days=1),
        registration_opens_at=now - timedelta(days=2),
        registration_deadline=now - timedelta(hours=2),
        registration_open=True,
        max_team_size=4,
    )


async def create_registration_context(
    session: AsyncSession,
    *,
    registration_status: RegistrationStatus = RegistrationStatus.ACCEPTED,
) -> tuple[User, User, Hackathon, Registration]:
    organizer = make_user(
        name="Attendance Organizer",
        email="attendance-organizer@example.com",
        role=UserRole.ADMIN,
    )
    participant = make_user(
        name="Attendance Participant",
        email="attendance-participant@example.com",
    )
    hackathon = make_hackathon(organizer)
    registration = Registration(
        user=participant,
        hackathon=hackathon,
        status=registration_status,
    )
    session.add(registration)
    await session.commit()
    return organizer, participant, hackathon, registration


async def create_check_in_session(
    session: AsyncSession,
    *,
    organizer: User,
    hackathon: Hackathon,
    token: str,
    expires_at: datetime | None = None,
) -> CheckInSession:
    check_in_session = CheckInSession(
        hackathon=hackathon,
        token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
        expires_at=expires_at or datetime.now(UTC) + timedelta(minutes=15),
        created_by=organizer,
    )
    session.add(check_in_session)
    await session.commit()
    return check_in_session


@pytest.mark.parametrize(
    ("method", "path_suffix", "payload"),
    [
        ("POST", "check-in-sessions", {"expires_in_minutes": 15}),
        ("PUT", "check-ins/me", {"token": "a" * 32}),
        ("GET", "check-ins", None),
        ("GET", "attendance", None),
    ],
)
async def test_attendance_endpoints_require_authentication(
    api_client,
    method: str,
    path_suffix: str,
    payload: dict | None,
):
    response = await api_client.request(
        method,
        f"/api/hackathons/{uuid.uuid4()}/{path_suffix}",
        json=payload,
    )

    assert response.status_code == 401


async def test_create_check_in_session_returns_token_and_replaces_previous_session(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    organizer, _, hackathon, _ = await create_registration_context(session)
    force_authenticate(organizer)

    first_response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/check-in-sessions",
        json={"expires_in_minutes": 10},
    )
    second_response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/check-in-sessions",
        json={"expires_in_minutes": 20},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["token"] != second_response.json()["token"]
    assert first_response.json()["is_active"] is True
    assert second_response.json()["is_active"] is True

    check_in_sessions = list(
        (
            await session.scalars(
                select(CheckInSession).order_by(CheckInSession.created_at, CheckInSession.id)
            )
        ).all()
    )
    assert len(check_in_sessions) == 2
    assert [item.is_active for item in check_in_sessions] == [False, True]
    assert (
        check_in_sessions[0].token_hash
        == hashlib.sha256(first_response.json()["token"].encode("utf-8")).hexdigest()
    )
    assert (
        check_in_sessions[1].token_hash
        == hashlib.sha256(second_response.json()["token"].encode("utf-8")).hexdigest()
    )
    assert first_response.json()["token"] not in {
        check_in_sessions[0].token_hash,
        check_in_sessions[1].token_hash,
    }


async def test_create_check_in_session_rejects_user_without_management_permission(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    _, participant, hackathon, _ = await create_registration_context(session)
    force_authenticate(participant)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/check-in-sessions",
        json={"expires_in_minutes": 15},
    )

    assert response.status_code == 403
    assert response.json() == {
        "error_code": "PERMISSION_DENIED",
        "detail": "Only hackathon organizers can manage check-in sessions.",
    }
    assert await session.scalar(select(func.count()).select_from(CheckInSession)) == 0


async def test_create_check_in_session_rejects_hackathon_before_start(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    organizer, _, hackathon, _ = await create_registration_context(session)
    now = datetime.now(UTC)
    hackathon.registration_deadline = now + timedelta(hours=12)
    hackathon.start_date = now + timedelta(days=1)
    hackathon.end_date = now + timedelta(days=2)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/check-in-sessions",
        json={"expires_in_minutes": 15},
    )

    assert response.status_code == 409
    assert response.json() == {
        "error_code": "HACKATHON_NOT_IN_PROGRESS",
        "detail": "Check-in is available only while the hackathon is in progress.",
    }
    assert await session.scalar(select(func.count()).select_from(CheckInSession)) == 0


async def test_participant_check_in_is_idempotent(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    organizer, participant, hackathon, registration = await create_registration_context(session)
    token = "valid-attendance-token-value-12345"
    check_in_session = await create_check_in_session(
        session,
        organizer=organizer,
        hackathon=hackathon,
        token=token,
    )
    force_authenticate(participant)

    first_response = await api_client.put(
        f"/api/hackathons/{hackathon.public_id}/check-ins/me",
        json={"token": token},
    )
    second_response = await api_client.put(
        f"/api/hackathons/{hackathon.public_id}/check-ins/me",
        json={"token": token},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json() == first_response.json()
    saved_check_in = await session.scalar(
        select(CheckIn).where(CheckIn.public_id == uuid.UUID(first_response.json()["public_id"]))
    )
    assert saved_check_in is not None
    assert saved_check_in.registration_id == registration.id
    assert saved_check_in.check_in_session_id == check_in_session.id
    assert await session.scalar(select(func.count()).select_from(CheckIn)) == 1


async def test_participant_check_in_rejects_invalid_token(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    organizer, participant, hackathon, _ = await create_registration_context(session)
    await create_check_in_session(
        session,
        organizer=organizer,
        hackathon=hackathon,
        token="valid-attendance-token-value-12345",
    )
    force_authenticate(participant)

    response = await api_client.put(
        f"/api/hackathons/{hackathon.public_id}/check-ins/me",
        json={"token": "invalid-attendance-token-value-123"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error_code": "INVALID_CHECK_IN_TOKEN",
        "detail": "The check-in token is invalid or has expired.",
    }
    assert await session.scalar(select(func.count()).select_from(CheckIn)) == 0


async def test_participant_check_in_rejects_expired_token(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    organizer, participant, hackathon, _ = await create_registration_context(session)
    token = "expired-attendance-token-value-123"
    await create_check_in_session(
        session,
        organizer=organizer,
        hackathon=hackathon,
        token=token,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    force_authenticate(participant)

    response = await api_client.put(
        f"/api/hackathons/{hackathon.public_id}/check-ins/me",
        json={"token": token},
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_CHECK_IN_TOKEN"
    assert await session.scalar(select(func.count()).select_from(CheckIn)) == 0


async def test_participant_check_in_requires_accepted_registration(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    organizer, participant, hackathon, _ = await create_registration_context(
        session,
        registration_status=RegistrationStatus.PENDING,
    )
    token = "valid-attendance-token-value-12345"
    await create_check_in_session(
        session,
        organizer=organizer,
        hackathon=hackathon,
        token=token,
    )
    force_authenticate(participant)

    response = await api_client.put(
        f"/api/hackathons/{hackathon.public_id}/check-ins/me",
        json={"token": token},
    )

    assert response.status_code == 403
    assert response.json() == {
        "error_code": "CHECK_IN_NOT_ALLOWED",
        "detail": "Only participants with an accepted registration can check in.",
    }
    assert await session.scalar(select(func.count()).select_from(CheckIn)) == 0


async def test_participant_check_in_rejects_hackathon_after_end(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    organizer, participant, hackathon, _ = await create_registration_context(session)
    token = "valid-attendance-token-value-12345"
    await create_check_in_session(
        session,
        organizer=organizer,
        hackathon=hackathon,
        token=token,
    )
    now = datetime.now(UTC)
    hackathon.registration_opens_at = now - timedelta(days=4)
    hackathon.registration_deadline = now - timedelta(days=3)
    hackathon.start_date = now - timedelta(days=2)
    hackathon.end_date = now - timedelta(days=1)
    await session.commit()
    force_authenticate(participant)

    response = await api_client.put(
        f"/api/hackathons/{hackathon.public_id}/check-ins/me",
        json={"token": token},
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "HACKATHON_NOT_IN_PROGRESS"
    assert await session.scalar(select(func.count()).select_from(CheckIn)) == 0


async def test_create_check_in_session_validates_expiration_range(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    organizer, _, hackathon, _ = await create_registration_context(session)
    force_authenticate(organizer)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/check-in-sessions",
        json={"expires_in_minutes": 61},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"
    assert await session.scalar(select(func.count()).select_from(CheckInSession)) == 0


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
    assert response.json()["total"] == 2
    assert [item["participant"]["name"] for item in response.json()["items"]] == [
        "First Participant",
        "Second Participant",
    ]
    assert response.json()["items"][0]["registration_public_id"] == str(
        first_registration.public_id
    )
    assert response.json()["items"][1]["registration_public_id"] == str(
        second_registration.public_id
    )


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
    assert response.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


async def test_list_attendance_returns_all_accepted_participants_with_presence(
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    now = datetime.now(UTC)
    organizer = make_user(
        name="Attendance Overview Organizer",
        email="attendance-overview-organizer@example.com",
        role=UserRole.ADMIN,
    )
    present_participant = make_user(
        name="Present Participant",
        email="present-attendance-overview@example.com",
    )
    absent_participant = make_user(
        name="Absent Participant",
        email="absent-attendance-overview@example.com",
    )
    rejected_participant = make_user(
        name="Rejected Participant",
        email="rejected-attendance-overview@example.com",
    )
    hackathon = make_hackathon(organizer)
    team = Team(
        hackathon=hackathon,
        name="Attendance Team",
        join_code="ATTEND01",
    )
    present_registration = Registration(
        user=present_participant,
        hackathon=hackathon,
        team=team,
        status=RegistrationStatus.ACCEPTED,
    )
    absent_registration = Registration(
        user=absent_participant,
        hackathon=hackathon,
        status=RegistrationStatus.ACCEPTED,
    )
    rejected_registration = Registration(
        user=rejected_participant,
        hackathon=hackathon,
        status=RegistrationStatus.REJECTED,
    )
    check_in_session = CheckInSession(
        hackathon=hackathon,
        token_hash="c" * 64,
        expires_at=now + timedelta(minutes=15),
        created_by=organizer,
    )
    check_in = CheckIn(
        registration=present_registration,
        session=check_in_session,
        checked_in_at=now,
    )
    session.add_all([check_in, absent_registration, rejected_registration])
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/attendance")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    response_by_name = {item["participant"]["name"]: item for item in response.json()["items"]}
    assert set(response_by_name) == {"Present Participant", "Absent Participant"}
    assert response_by_name["Present Participant"]["is_present"] is True
    assert response_by_name["Present Participant"]["checked_in_at"] is not None
    assert response_by_name["Present Participant"]["team"]["name"] == "Attendance Team"
    assert response_by_name["Absent Participant"]["is_present"] is False
    assert response_by_name["Absent Participant"]["checked_in_at"] is None
    assert response_by_name["Absent Participant"]["team"] is None


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


@pytest.mark.parametrize(
    "endpoint, expected_total",
    [
        ("attendance", 6),
        ("check-ins", 3),
        ("teams", 3),
    ],
)
async def test_paginated_lists_are_scoped_and_keep_complete_teams(
    endpoint,
    expected_total,
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    owner = make_user(name="Owner", email="owner-pages@example.com")
    hackathon = make_hackathon(owner)
    other_hackathon = make_hackathon(owner)
    now = datetime.now(UTC)
    for event in (hackathon, other_hackathon):
        qr_session = CheckInSession(
            hackathon=event,
            token_hash=uuid.uuid4().hex * 2,
            expires_at=now + timedelta(minutes=15),
            created_by=owner,
        )
        session.add(qr_session)
        for team_name in ("Beta", "Alpha", "Gamma"):
            team = Team(hackathon=event, name=team_name, join_code=uuid.uuid4().hex[:8])
            session.add(team)
            for index in range(3):
                user = make_user(name=f"{team_name} {index}", email=f"{uuid.uuid4()}@example.com")
                registration = Registration(
                    user=user,
                    hackathon=event,
                    team=team,
                    status=(
                        RegistrationStatus.ACCEPTED if index < 2 else RegistrationStatus.REJECTED
                    ),
                )
                session.add(registration)
                if index == 0:
                    session.add(
                        CheckIn(registration=registration, session=qr_session, checked_in_at=now)
                    )
    await session.commit()
    path = f"/api/hackathons/{hackathon.public_id}/{endpoint}"
    session.expunge_all()
    force_authenticate(owner)

    default_response = await api_client.get(path)
    assert default_response.status_code == 200
    default = default_response.json()
    assert default["total"] == expected_total
    assert default["limit"] == 50
    assert default["offset"] == 0
    collected = []
    for offset in range(expected_total):
        response = await api_client.get(path, params={"limit": 1, "offset": offset})
        assert response.status_code == 200
        page = response.json()
        assert page["total"] == expected_total
        assert page["limit"] == 1
        assert page["offset"] == offset
        assert len(page["items"]) == 1
        collected.extend(page["items"])
    assert collected == default["items"]
    key = "public_id" if endpoint == "teams" else "registration_public_id"
    assert len({item[key] for item in collected}) == expected_total
    if endpoint == "teams":
        assert [team["name"] for team in collected] == ["Alpha", "Beta", "Gamma"]
        assert all(len(team["participants"]) == 2 for team in collected)
        assert all("join_code" not in team for team in collected)
    elif endpoint == "attendance":
        assert sum(item["is_present"] for item in collected) == 3
    past_end = await api_client.get(path, params={"offset": 100})
    assert past_end.json() == {"items": [], "total": expected_total, "limit": 50, "offset": 100}


@pytest.mark.parametrize("endpoint", ["attendance", "check-ins", "teams"])
@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": "abc"}])
async def test_paginated_management_lists_validate_query(
    endpoint,
    params,
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    owner = make_user(name="Owner", email="owner-query@example.com")
    session.add(owner)
    await session.commit()
    force_authenticate(owner)
    response = await api_client.get(f"/api/hackathons/{uuid.uuid4()}/{endpoint}", params=params)
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("endpoint", ["attendance", "check-ins", "teams"])
async def test_paginated_management_lists_preserve_permissions(
    endpoint,
    api_client,
    force_authenticate,
    session: AsyncSession,
):
    owner = make_user(name="Owner", email="owner-access@example.com")
    co_organizer = make_user(name="Co", email="co-access@example.com")
    admin = make_user(name="Admin", email="admin-access@example.com", role=UserRole.ADMIN)
    participant = make_user(name="Participant", email="participant-access@example.com")
    hackathon = make_hackathon(owner)
    hackathon.co_organizers = [co_organizer]
    session.add_all([hackathon, admin, participant])
    await session.commit()
    path = f"/api/hackathons/{hackathon.public_id}/{endpoint}"
    response = await api_client.get(path)
    assert response.status_code == 401
    force_authenticate(participant)
    response = await api_client.get(path)
    assert response.status_code == 403
    assert "total" not in response.json()
    for manager in (owner, co_organizer, admin):
        force_authenticate(manager)
        response = await api_client.get(path)
        assert response.status_code == 200
        assert response.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}
    hackathon.is_deleted = True
    await session.commit()
    response = await api_client.get(path)
    assert response.status_code == 404
