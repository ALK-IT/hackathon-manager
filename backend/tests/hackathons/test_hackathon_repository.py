from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.hackathons.models import Hackathon
from src.hackathons.repository import HackathonRepository
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
    registration_opens_at: datetime | None = None,
    registration_deadline: datetime | None = None,
    co_organizers: list[User] | None = None,
) -> Hackathon:
    current_time = datetime.now(UTC)
    start_date = current_time + timedelta(days=7)
    return Hackathon(
        organizer=organizer,
        co_organizers=co_organizers or [],
        name=name,
        description="Description",
        start_date=start_date,
        end_date=current_time + timedelta(days=8),
        registration_opens_at=registration_opens_at or current_time - timedelta(hours=1),
        registration_deadline=registration_deadline or start_date - timedelta(hours=48),
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


async def test_list_active_returns_only_hackathons_with_open_registration_window(
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
        registration_opens_at=datetime.now(UTC) + timedelta(days=1),
    )
    expired = make_hackathon(
        current_user,
        name="Expired",
        registration_opens_at=datetime.now(UTC) - timedelta(days=2),
        registration_deadline=datetime.now(UTC) - timedelta(days=1),
    )
    manually_closed = make_hackathon(
        current_user,
        name="Manually closed",
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

    assert result == [unrelated, co_organized, owned]
    assert result[1].co_organizers == [current_user]


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
