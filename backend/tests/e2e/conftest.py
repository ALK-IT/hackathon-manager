import os
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from urllib.parse import urlsplit, urlunsplit

import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import from_url
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.auth.models import User, UserRole
from src.auth.utils import hash_password
from src.cache import get_cache
from src.database import get_session
from src.main import app
from tests.e2e.helpers import E2EAccount

AccountFactory = Callable[..., Awaitable[E2EAccount]]


def _test_redis_url() -> str:
    configured_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    parsed = urlsplit(configured_url)
    return urlunsplit((parsed.scheme, parsed.netloc, "/15", parsed.query, parsed.fragment))


@pytest.fixture(autouse=True)
async def isolated_e2e_cache(monkeypatch) -> AsyncIterator[None]:
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "e2e-secret-key-with-at-least-32-characters",  # gitleaks:allow
    )
    cache = from_url(_test_redis_url(), decode_responses=True)
    await cache.flushdb()
    app.dependency_overrides[get_cache] = lambda: cache

    try:
        yield
    finally:
        app.dependency_overrides.pop(get_cache, None)
        await cache.flushdb()
        await cache.aclose()


@pytest.fixture
async def e2e_client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    if session.bind is None:
        raise RuntimeError("The E2E database session has no engine binding")

    request_session_factory = async_sessionmaker(session.bind, expire_on_commit=False)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with request_session_factory() as request_session:
            yield request_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_session, None)


async def _login(
    client: AsyncClient,
    *,
    public_id: str,
    name: str,
    email: str,
    password: str,
) -> E2EAccount:
    response = await client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return E2EAccount(
        public_id=public_id,
        name=name,
        email=email,
        password=password,
        access_token=response.json()["access_token"],
    )


@pytest.fixture
def account_factory(e2e_client: AsyncClient, session: AsyncSession) -> AccountFactory:
    async def create_account(
        *,
        name: str,
        email: str,
        password: str = "password123",
    ) -> E2EAccount:
        register_response = await e2e_client.post(
            "/api/auth/register",
            json={"name": name, "email": email, "password": password},
        )
        assert register_response.status_code == 201
        user = await session.scalar(select(User).where(User.email == email))
        assert user is not None
        user.email_verified_at = datetime.now(UTC)
        await session.commit()
        return await _login(
            e2e_client,
            public_id=register_response.json()["public_id"],
            name=name,
            email=email,
            password=password,
        )

    return create_account


@pytest.fixture
async def admin_account(
    session: AsyncSession,
    e2e_client: AsyncClient,
) -> E2EAccount:
    password = "password123"
    admin = User(
        name="E2E Admin",
        email="e2e-admin@example.com",
        password_hash=hash_password(password),
        email_verified_at=datetime.now(UTC),
        role=UserRole.ADMIN,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return await _login(
        e2e_client,
        public_id=str(admin.public_id),
        name=admin.name,
        email=admin.email,
        password=password,
    )
