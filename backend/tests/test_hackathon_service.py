import pytest
from redis.asyncio import from_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.cache import REDIS_URL
from app.db import DATABASE_URL
from app.models import Base, Hackathon
from app.repositories.hackathon_repository import HackathonRepository
from app.services.hackathon_service import CACHE_KEY, HackathonService


@pytest.fixture
async def session():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as s:
        s.add(Hackathon(name="Test Hackathon"))
        await s.commit()
        yield s

    await engine.dispose()


@pytest.fixture
async def cache():
    client = from_url(REDIS_URL, decode_responses=True)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


async def test_repository_lists_hackathons(session):
    repo = HackathonRepository(session)
    hackathons = await repo.list_all()
    assert len(hackathons) == 1
    assert hackathons[0].name == "Test Hackathon"


async def test_service_caches_result(session, cache):
    repo = HackathonRepository(session)
    service = HackathonService(repo, cache)

    result = await service.list_hackathons()
    assert result == [{"id": result[0]["id"], "name": "Test Hackathon"}]

    cached_raw = await cache.get(CACHE_KEY)
    assert cached_raw is not None
