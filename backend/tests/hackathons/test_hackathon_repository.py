from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.hackathons.models import Hackathon
from src.hackathons.repository import HackathonRepository
from src.registration.models import Registration, RegistrationStatus
from tests.hackathons.factories import NOW


async def persist_user(
    session: AsyncSession,
    *,
    email: str,
    role: UserRole = UserRole.USER,
) -> User:
    user = User(
        name=email.split("@")[0],
        email=email,
        password_hash="hashed-password",
        role=role,
    )
    session.add(user)
    await session.flush()
    return user


def make_hackathon(
    organizer: User,
    *,
    name: str,
    created_offset: int = 0,
    is_deleted: bool = False,
    registration_open: bool = True,
    start_date: datetime | None = None,
    registration_opens_at: datetime | None = None,
    registration_deadline: datetime | None = None,
    co_organizers: list[User] | None = None,
) -> Hackathon:
    current_time = datetime.now(UTC)
    effective_start_date = start_date or current_time + timedelta(days=7)
    effective_deadline = registration_deadline or effective_start_date - timedelta(hours=48)
    effective_opens_at = registration_opens_at or min(
        current_time - timedelta(hours=1),
        effective_deadline - timedelta(hours=1),
    )
    return Hackathon(
        organizer=organizer,
        co_organizers=co_organizers or [],
        name=name,
        description="Description",
        start_date=effective_start_date,
        end_date=effective_start_date + timedelta(days=1),
        registration_opens_at=effective_opens_at,
        registration_deadline=effective_deadline,
        registration_open=registration_open,
        capacity=100,
        max_team_size=4,
        is_deleted=is_deleted,
        deleted_at=NOW if is_deleted else None,
        created_at=NOW + timedelta(minutes=created_offset),
        updated_at=NOW,
    )


async def test_repository_adds_and_reads_hackathon(session: AsyncSession):
    owner = await persist_user(
        session,
        email="owner@example.com",
        role=UserRole.ADMIN,
    )
    hackathon = make_hackathon(owner, name="Hackathon AI")
    repository = HackathonRepository(session)

    await repository.add(hackathon)
    await repository.commit()

    result = await repository.get_owned_by_public_id(hackathon.public_id, owner.id)
    assert result is hackathon
    assert result.organizer is owner
    assert result.co_organizers == []


async def test_list_active_without_filters_returns_all_non_deleted_hackathons(
    session: AsyncSession,
):
    current_user = await persist_user(session, email="current@example.com")
    other_owner = await persist_user(
        session,
        email="owner@example.com",
        role=UserRole.ADMIN,
    )
    unrelated_user = await persist_user(session, email="unrelated@example.com")
    owned = make_hackathon(
        current_user,
        name="Owned",
        created_offset=1,
    )
    co_organized = make_hackathon(
        other_owner,
        name="Co-organized",
        created_offset=2,
        co_organizers=[current_user],
    )
    unrelated = make_hackathon(
        unrelated_user,
        name="Unrelated",
        created_offset=3,
    )
    deleted = make_hackathon(
        current_user,
        name="Deleted",
        created_offset=4,
        is_deleted=True,
    )
    scheduled = make_hackathon(
        current_user,
        name="Scheduled",
        created_offset=5,
        registration_opens_at=datetime.now(UTC) + timedelta(days=1),
    )
    expired = make_hackathon(
        current_user,
        name="Expired",
        created_offset=6,
        registration_opens_at=datetime.now(UTC) - timedelta(days=2),
        registration_deadline=datetime.now(UTC) - timedelta(days=1),
    )
    manually_closed = make_hackathon(
        current_user,
        name="Manually closed",
        created_offset=7,
        registration_open=False,
    )
    session.add_all(
        [
            owned,
            co_organized,
            unrelated,
            deleted,
            scheduled,
            expired,
            manually_closed,
        ]
    )
    await session.commit()
    repository = HackathonRepository(session)

    result = await repository.list_active()

    assert [hackathon for hackathon, _status in result] == [
        manually_closed,
        expired,
        scheduled,
        unrelated,
        co_organized,
        owned,
    ]
    assert all(status is None for _hackathon, status in result)
    assert result[4][0].co_organizers == [current_user]


async def test_list_active_filters_upcoming_hackathons(session: AsyncSession):
    owner = await persist_user(session, email="owner@example.com")
    current_time = datetime.now(UTC)
    upcoming = make_hackathon(
        owner,
        name="Upcoming",
        created_offset=1,
        start_date=current_time + timedelta(days=2),
    )
    started = make_hackathon(
        owner,
        name="Started",
        created_offset=2,
        start_date=current_time - timedelta(days=1),
    )
    deleted = make_hackathon(
        owner,
        name="Deleted upcoming",
        created_offset=3,
        start_date=current_time + timedelta(days=3),
        is_deleted=True,
    )
    session.add_all([upcoming, started, deleted])
    await session.commit()
    repository = HackathonRepository(session)

    assert await repository.list_active(upcoming=True) == [(upcoming, None)]
    assert await repository.list_active(upcoming=False) == [(started, None)]


async def test_list_active_filters_effective_registration_state(session: AsyncSession):
    owner = await persist_user(session, email="owner@example.com")
    current_time = datetime.now(UTC)
    opened = make_hackathon(owner, name="Open", created_offset=1)
    scheduled = make_hackathon(
        owner,
        name="Scheduled",
        created_offset=2,
        registration_opens_at=current_time + timedelta(days=1),
    )
    expired = make_hackathon(
        owner,
        name="Expired",
        created_offset=3,
        registration_opens_at=current_time - timedelta(days=2),
        registration_deadline=current_time - timedelta(days=1),
    )
    manually_closed = make_hackathon(
        owner,
        name="Manually closed",
        created_offset=4,
        registration_open=False,
    )
    deleted = make_hackathon(
        owner,
        name="Deleted open",
        created_offset=5,
        is_deleted=True,
    )
    session.add_all([opened, scheduled, expired, manually_closed, deleted])
    await session.commit()
    repository = HackathonRepository(session)

    assert await repository.list_active(registration_open=True) == [(opened, None)]
    assert await repository.list_active(registration_open=False) == [
        (manually_closed, None),
        (expired, None),
        (scheduled, None),
    ]


async def test_list_active_returns_only_current_users_registration_status(
    session: AsyncSession,
):
    current_user = await persist_user(session, email="current@example.com")
    other_user = await persist_user(session, email="other@example.com")
    owner = await persist_user(
        session,
        email="owner@example.com",
        role=UserRole.ADMIN,
    )
    hackathon = make_hackathon(owner, name="AI Hackathon")
    session.add(hackathon)
    await session.flush()
    session.add_all(
        [
            Registration(
                user=current_user,
                hackathon=hackathon,
                status=RegistrationStatus.ACCEPTED,
            ),
            Registration(
                user=other_user,
                hackathon=hackathon,
                status=RegistrationStatus.REJECTED,
            ),
        ]
    )
    await session.commit()
    repository = HackathonRepository(session)

    assert await repository.list_active(user_id=current_user.id) == [
        (hackathon, RegistrationStatus.ACCEPTED)
    ]
    assert await repository.list_active(user_id=other_user.id) == [
        (hackathon, RegistrationStatus.REJECTED)
    ]
    assert await repository.list_active() == [(hackathon, None)]


async def test_list_managed_returns_only_owned_and_co_organized_hackathons(
    session: AsyncSession,
):
    current_user = await persist_user(session, email="current@example.com")
    owner = await persist_user(
        session,
        email="owner@example.com",
        role=UserRole.ADMIN,
    )
    unrelated = await persist_user(session, email="unrelated@example.com")
    owned = make_hackathon(current_user, name="Owned", created_offset=1)
    co_organized = make_hackathon(
        owner,
        name="Co-organized",
        created_offset=2,
        co_organizers=[current_user],
    )
    unrelated_hackathon = make_hackathon(
        unrelated,
        name="Unrelated",
        created_offset=3,
    )
    deleted = make_hackathon(
        current_user,
        name="Deleted",
        created_offset=4,
        is_deleted=True,
    )
    session.add_all([owned, co_organized, unrelated_hackathon, deleted])
    await session.commit()
    repository = HackathonRepository(session)

    result = await repository.list_managed_by_user(current_user.id)

    assert result == [co_organized, owned]


async def test_get_active_returns_non_deleted_hackathon(session: AsyncSession):
    owner = await persist_user(
        session,
        email="owner@example.com",
        role=UserRole.ADMIN,
    )
    hackathon = make_hackathon(owner, name="Hackathon AI")
    session.add(hackathon)
    await session.commit()
    repository = HackathonRepository(session)

    assert await repository.get_active_by_public_id(hackathon.public_id) is hackathon


async def test_get_owned_hides_hackathon_from_other_users(session: AsyncSession):
    owner = await persist_user(
        session,
        email="owner@example.com",
        role=UserRole.ADMIN,
    )
    unrelated = await persist_user(session, email="unrelated@example.com")
    hackathon = make_hackathon(owner, name="Hackathon AI")
    session.add(hackathon)
    await session.commit()
    repository = HackathonRepository(session)

    assert await repository.get_owned_by_public_id(hackathon.public_id, unrelated.id) is None


async def test_get_owned_hides_soft_deleted_hackathon(session: AsyncSession):
    owner = await persist_user(
        session,
        email="owner@example.com",
        role=UserRole.ADMIN,
    )
    deleted = make_hackathon(
        owner,
        name="Deleted",
        is_deleted=True,
    )
    session.add(deleted)
    await session.commit()
    repository = HackathonRepository(session)

    assert await repository.get_owned_by_public_id(deleted.public_id, owner.id) is None
    assert await repository.get_active_by_public_id(deleted.public_id) is None


async def test_repository_rolls_back_uncommitted_hackathon(session: AsyncSession):
    owner = await persist_user(
        session,
        email="owner@example.com",
        role=UserRole.ADMIN,
    )
    hackathon = make_hackathon(owner, name="Uncommitted")
    repository = HackathonRepository(session)

    await repository.add(hackathon)
    public_id = hackathon.public_id
    await repository.rollback()

    result = await session.scalar(select(Hackathon).where(Hackathon.public_id == public_id))
    assert result is None
