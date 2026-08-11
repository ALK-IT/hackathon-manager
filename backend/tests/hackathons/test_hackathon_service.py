import json
from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from redis.asyncio import from_url
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache import REDIS_URL
from src.hackathons.constants import CACHE_KEY, CACHE_TTL_SECONDS
from src.hackathons.models import Hackathon
from src.hackathons.repository import HackathonRepository
from src.hackathons.service import HackathonService


@pytest.fixture
async def cache():
    client = from_url(REDIS_URL, decode_responses=True)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.fixture
def hackathons_list():
    hackathons_data = [{"id": 1, "name": "Python Hackathon"}, {"id": 2, "name": "AI Hackathon"}]
    return hackathons_data


async def test_repository_lists_hackathons(session: AsyncSession):
    session.add(Hackathon(name="Test Hackathon"))
    await session.commit()
    repo = HackathonRepository(session)
    hackathons = await repo.list_all()
    assert len(hackathons) == 1
    assert hackathons[0].name == "Test Hackathon"


async def test_service_caches_result(session: AsyncSession, cache):
    session.add(Hackathon(name="Test Hackathon"))
    await session.commit()
    repo = HackathonRepository(session)
    service = HackathonService(repo, cache)

    result = await service.list_hackathons()
    assert result == [{"id": result[0]["id"], "name": "Test Hackathon"}]

    cached_raw = await cache.get(CACHE_KEY)
    assert cached_raw is not None


async def test_list_hackathons_endpoint_uses_test_session(
    api_client: AsyncClient,
    session: AsyncSession,
    cache,
):
    hackathon = Hackathon(name="Test Hackathon")
    session.add(hackathon)
    await session.commit()
    await session.refresh(hackathon)

    response = await api_client.get("/api/hackathons")

    assert response.status_code == 200
    assert response.json() == [{"id": hackathon.id, "name": "Test Hackathon"}]


async def test_list_hackathons_returns_data_from_cache(mocker, hackathons_list):
    cached_data = hackathons_list

    repository = mocker.Mock()
    cache = mocker.Mock()

    cache.get = mocker.AsyncMock()
    cache.set = mocker.AsyncMock()

    cache.get.return_value = json.dumps(cached_data)

    service = HackathonService(repository=repository, cache=cache)

    hackathons = await service.list_hackathons()

    assert cached_data == hackathons
    cache.get.assert_awaited_once_with(CACHE_KEY)
    cache.set.assert_not_awaited()


async def test_list_hackathons_returns_data_from_repository(mocker, hackathons_list):
    database_hackathon = [
        SimpleNamespace(**hackathons_list[0]),
        SimpleNamespace(**hackathons_list[1]),
    ]

    repository = mocker.Mock()
    cache = mocker.Mock()

    cache.get = mocker.AsyncMock(return_value=None)
    cache.set = mocker.AsyncMock()

    repository.list_all = mocker.AsyncMock(return_value=database_hackathon)
    service = HackathonService(repository=repository, cache=cache)
    hackathons = await service.list_hackathons()

    assert hackathons == hackathons_list

    cache.get.assert_awaited_once_with(CACHE_KEY)
    cache.set.assert_awaited_once_with(CACHE_KEY, json.dumps(hackathons_list), ex=CACHE_TTL_SECONDS)

    repository.list_all.assert_awaited_once_with()
