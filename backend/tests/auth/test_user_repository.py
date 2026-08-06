import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.auth.repository import UserRepository
from src.auth.utils import hash_password


def make_user(email: str, *, name: str = "Jan Kowalski") -> User:
    return User(
        name=name,
        email=email,
        password_hash=hash_password("password123"),
    )


async def test_user_repository_reads_created_user(session: AsyncSession):
    repository = UserRepository(session)
    user = make_user("jan@example.com")

    created_user = await repository.create(user)
    await repository.commit()

    assert created_user is user
    assert user.id is not None
    assert user.public_id is not None
    assert await repository.get_by_email("jan@example.com") is user
    assert await repository.get_by_public_id(user.public_id) is user
    assert user.role is UserRole.USER


async def test_user_repository_returns_none_when_user_does_not_exist(session: AsyncSession):
    repository = UserRepository(session)

    assert await repository.get_by_email("missing@example.com") is None
    assert await repository.get_by_public_id(uuid.uuid4()) is None


async def test_user_repository_lists_users_with_pagination(session: AsyncSession):
    repository = UserRepository(session)
    oldest = make_user("oldest@example.com", name="Oldest")
    middle = make_user("middle@example.com", name="Middle")
    newest = make_user("newest@example.com", name="Newest")
    oldest.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    middle.created_at = datetime(2026, 1, 2, tzinfo=UTC)
    newest.created_at = datetime(2026, 1, 3, tzinfo=UTC)

    for user in (oldest, middle, newest):
        await repository.create(user)
    await repository.commit()

    assert await repository.get_all() == [newest, middle, oldest]
    assert await repository.get_all(skip=1, limit=1) == [middle]


async def test_user_repository_updates_user(session: AsyncSession):
    repository = UserRepository(session)
    user = make_user("jan@example.com")
    await repository.create(user)
    await repository.commit()

    user.name = "Jan Nowak"
    updated_user = await repository.update(user)
    await repository.commit()

    assert updated_user is user
    assert (await repository.get_by_email("jan@example.com")).name == "Jan Nowak"


async def test_user_repository_deletes_user(session: AsyncSession):
    repository = UserRepository(session)
    user = make_user("jan@example.com")
    await repository.create(user)
    await repository.commit()
    public_id = user.public_id

    await repository.delete(user)
    await repository.commit()

    assert await repository.get_by_email("jan@example.com") is None
    assert await repository.get_by_public_id(public_id) is None


async def test_user_repository_rolls_back_uncommitted_user(session: AsyncSession):
    repository = UserRepository(session)
    user = make_user("jan@example.com")

    await repository.create(user)
    await repository.rollback()

    assert await repository.get_by_email("jan@example.com") is None
