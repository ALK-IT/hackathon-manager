import os
from collections.abc import AsyncIterator, Callable, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.database import get_session, normalize_database_url
from src.main import app
from src.models import Base

ForceAuthenticate = Callable[[User | None], None]


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.fail("TEST_DATABASE_URL must be set to run database tests")

    normalized_test_database_url = normalize_database_url(test_database_url)
    test_database_name = make_url(normalized_test_database_url).database
    if not test_database_name or not test_database_name.endswith("_test"):
        pytest.fail(
            "Refusing to reset a database whose name does not end with '_test'. "
            f"Configured database: {test_database_name!r}"
        )

    engine = create_async_engine(normalized_test_database_url)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as database_session:
        yield database_session

    await engine.dispose()


@pytest.fixture
async def api_client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_session, None)


# Helper function for authentication
@pytest.fixture
def force_authenticate() -> Iterator[ForceAuthenticate]:
    def authenticate(user: User | None) -> None:
        if user is None:
            app.dependency_overrides.pop(get_current_user, None)
            return

        app.dependency_overrides[get_current_user] = lambda: user

    try:
        yield authenticate
    finally:
        app.dependency_overrides.pop(get_current_user, None)
