import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from redis.asyncio import from_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.cache import REDIS_URL
from app.db import DATABASE_URL
from app.models import Base, Hackathon
from app.repositories.hackathon_repository import HackathonRepository
from app.schemas import HackathonCreate, HackathonUpdate
from app.services.hackathon_service import CACHE_KEY, CACHE_TTL_SECONDS, HackathonService


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


@pytest.fixture
def hackathons_list():
    hackathons_data = [{"id": 1, "name": "Python Hackathon"}, {"id": 2, "name": "AI Hackathon"}]
    return hackathons_data


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


def test_create_validates_name_after_trimming():
    hackathon = HackathonCreate(name="  Python Hackathon  ")

    assert hackathon.name == "Python Hackathon"


def test_create_rejects_blank_name():
    with pytest.raises(ValidationError):
        HackathonCreate(name="   ")


def test_create_rejects_name_longer_than_200_characters():
    with pytest.raises(ValidationError):
        HackathonCreate(name="x" * 201)


def test_update_rejects_empty_payload():
    with pytest.raises(ValidationError):
        HackathonUpdate()


def test_update_rejects_null_name():
    with pytest.raises(ValidationError):
        HackathonUpdate(name=None)


async def test_repository_creates_updates_and_deletes_hackathon(session):
    repository = HackathonRepository(session)

    created = await repository.create("New Hackathon")
    updated = await repository.update(created.id, "Updated Hackathon")
    deleted = await repository.delete(created.id)

    assert created.id is not None
    assert updated is not None
    assert updated.name == "Updated Hackathon"
    assert deleted is True
    assert await repository.update(created.id, "Missing") is None
    assert await repository.delete(created.id) is False


async def test_create_returns_hackathon_and_invalidates_cache(mocker):
    repository = mocker.Mock()
    repository.create = mocker.AsyncMock(return_value=SimpleNamespace(id=2, name="New Hackathon"))
    cache = mocker.Mock()
    cache.delete = mocker.AsyncMock()
    service = HackathonService(repository, cache)

    result = await service.create_hackathon("New Hackathon")

    assert result == {"id": 2, "name": "New Hackathon"}
    repository.create.assert_awaited_once_with("New Hackathon")
    cache.delete.assert_awaited_once_with(CACHE_KEY)


async def test_update_returns_hackathon_and_invalidates_cache(mocker):
    repository = mocker.Mock()
    repository.update = mocker.AsyncMock(
        return_value=SimpleNamespace(id=2, name="Updated Hackathon")
    )
    cache = mocker.Mock()
    cache.delete = mocker.AsyncMock()
    service = HackathonService(repository, cache)

    result = await service.update_hackathon(2, "Updated Hackathon")

    assert result == {"id": 2, "name": "Updated Hackathon"}
    repository.update.assert_awaited_once_with(2, "Updated Hackathon")
    cache.delete.assert_awaited_once_with(CACHE_KEY)


async def test_update_missing_hackathon_does_not_invalidate_cache(mocker):
    repository = mocker.Mock()
    repository.update = mocker.AsyncMock(return_value=None)
    cache = mocker.Mock()
    cache.delete = mocker.AsyncMock()
    service = HackathonService(repository, cache)

    result = await service.update_hackathon(999, "Updated Hackathon")

    assert result is None
    cache.delete.assert_not_awaited()


async def test_delete_invalidates_cache(mocker):
    repository = mocker.Mock()
    repository.delete = mocker.AsyncMock(return_value=True)
    cache = mocker.Mock()
    cache.delete = mocker.AsyncMock()
    service = HackathonService(repository, cache)

    result = await service.delete_hackathon(2)

    assert result is True
    repository.delete.assert_awaited_once_with(2)
    cache.delete.assert_awaited_once_with(CACHE_KEY)


async def test_delete_missing_hackathon_does_not_invalidate_cache(mocker):
    repository = mocker.Mock()
    repository.delete = mocker.AsyncMock(return_value=False)
    cache = mocker.Mock()
    cache.delete = mocker.AsyncMock()
    service = HackathonService(repository, cache)

    result = await service.delete_hackathon(999)

    assert result is False
    cache.delete.assert_not_awaited()
