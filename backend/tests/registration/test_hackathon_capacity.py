import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.auth.models import UserRole
from src.hackathons.exceptions import HackathonCapacityFullError
from src.hackathons.repository import HackathonRepository
from src.hackathons.schemas import HackathonUpdate
from src.hackathons.service import HackathonService
from src.registration.dependencies import get_registration_service
from src.registration.models import Registration, RegistrationStatus
from tests.registration.test_registration_endpoints import create_hackathon, create_user


@pytest.fixture
async def capacity_setup(session):
    owner = await create_user(session, "owner@example.com", role=UserRole.ADMIN)
    hackathon = await create_hackathon(session, owner, max_team_size=1)
    hackathon.capacity = 1
    registrations = []
    for index in range(3):
        user = await create_user(session, f"participant{index}@example.com")
        registration = Registration(user=user, hackathon=hackathon)
        session.add(registration)
        registrations.append(registration)
    await session.commit()
    return owner, hackathon, registrations


@pytest.mark.parametrize(
    "initial_status", [RegistrationStatus.PENDING, RegistrationStatus.REJECTED]
)
async def test_full_hackathon_rejects_acceptance(
    session, api_client, force_authenticate, capacity_setup, initial_status
):
    owner, _, registrations = capacity_setup
    registrations[0].status = RegistrationStatus.ACCEPTED
    registrations[1].status = initial_status
    await session.commit()
    target = registrations[1]
    target_id = target.public_id
    force_authenticate(owner)
    response = await api_client.patch(
        f"/api/registrations/{target_id}/status", json={"status": "accepted"}
    )
    assert response.status_code == 409
    assert response.json()["error_code"] == "CAPACITY_FULL"
    await session.refresh(target)
    assert target.status == initial_status
    assert target.status_changed_at is None


async def test_reacceptance_and_rejection_release_capacity(session, capacity_setup):
    owner, hackathon, registrations = capacity_setup
    service = get_registration_service(session, AsyncMock())
    first, second, _ = registrations
    await service.update_status(first.public_id, RegistrationStatus.ACCEPTED, owner)
    await service.update_status(first.public_id, RegistrationStatus.ACCEPTED, owner)
    assert await HackathonRepository(session).count_accepted_registrations(hackathon.id) == 1
    await service.update_status(first.public_id, RegistrationStatus.REJECTED, owner)
    await service.update_status(second.public_id, RegistrationStatus.ACCEPTED, owner)
    assert await HackathonRepository(session).count_accepted_registrations(hackathon.id) == 1


async def test_unlimited_capacity_accepts_all(session, capacity_setup):
    owner, hackathon, registrations = capacity_setup
    hackathon.capacity = None
    await session.commit()
    service = get_registration_service(session, AsyncMock())
    for registration in registrations:
        await service.update_status(registration.public_id, RegistrationStatus.ACCEPTED, owner)
    assert await HackathonRepository(session).count_accepted_registrations(hackathon.id) == 3


async def test_failed_acceptance_does_not_notify(session, capacity_setup):
    owner, _, registrations = capacity_setup
    registrations[0].status = RegistrationStatus.ACCEPTED
    await session.commit()
    email = AsyncMock()
    service = get_registration_service(session, email)
    service.notification_service = AsyncMock()
    with pytest.raises(HackathonCapacityFullError):
        await service.update_status(registrations[1].public_id, RegistrationStatus.ACCEPTED, owner)
    service.notification_service.notify_status_changed.assert_not_awaited()
    email.send_registration_status_changed.assert_not_awaited()


async def test_deleting_accepted_registration_frees_place(session, capacity_setup):
    owner, _, registrations = capacity_setup
    first_id, second_id = (registration.public_id for registration in registrations[:2])
    service = get_registration_service(session, AsyncMock())
    await service.update_status(first_id, RegistrationStatus.ACCEPTED, owner)
    await service.delete_registration(first_id, owner)
    result = await service.update_status(second_id, RegistrationStatus.ACCEPTED, owner)
    assert result.status == RegistrationStatus.ACCEPTED


@pytest.mark.parametrize("capacity,expected", [(1, 409), (2, 200), (3, 200), (None, 200)])
async def test_capacity_update_respects_accepted_count(
    session, api_client, force_authenticate, capacity_setup, capacity, expected
):
    owner, hackathon, registrations = capacity_setup
    hackathon.capacity = 3
    registrations[0].status = RegistrationStatus.ACCEPTED
    registrations[1].status = RegistrationStatus.ACCEPTED
    await session.commit()
    force_authenticate(owner)
    response = await api_client.patch(
        f"/api/hackathons/{hackathon.public_id}", json={"capacity": capacity}
    )
    assert response.status_code == expected
    await session.refresh(hackathon)
    if expected == 409:
        assert response.json()["error_code"] == "CAPACITY_FULL"
        assert hackathon.capacity == 3
    else:
        assert hackathon.capacity == capacity


async def test_full_hackathon_still_allows_pending_registration(
    session, api_client, force_authenticate, capacity_setup
):
    _, hackathon, registrations = capacity_setup
    registrations[0].status = RegistrationStatus.ACCEPTED
    newcomer = await create_user(session, "new@example.com")
    await session.commit()
    force_authenticate(newcomer)
    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/registrations", json={"answers": []}
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


@pytest.mark.parametrize("race", ["accept", "same_registration", "lower_capacity"])
async def test_concurrent_capacity_operations(session, capacity_setup, race):
    owner, hackathon, registrations = capacity_setup
    if race == "lower_capacity":
        hackathon.capacity = 2
        registrations[2].status = RegistrationStatus.ACCEPTED
        await session.commit()
    hackathon_id, public_id = hackathon.id, hackathon.public_id
    owner_id = owner.id
    targets = [registrations[0].public_id, registrations[1].public_id]
    if race == "same_registration":
        targets[1] = targets[0]
    factory = async_sessionmaker(session.bind, expire_on_commit=False)
    ready = [asyncio.Event(), asyncio.Event()]

    async def run(index):
        async with factory() as worker:
            service = get_registration_service(worker, AsyncMock())
            # Preload identity maps before either operation commits.
            user = await worker.get(type(owner), owner_id)
            preloaded = await service.registration_repository.get_active_by_public_id(
                targets[index]
            )
            assert preloaded.status == RegistrationStatus.PENDING
            ready[index].set()
            await ready[1 - index].wait()
            try:
                if race == "lower_capacity" and index == 1:
                    await HackathonService(
                        HackathonRepository(worker), Mock(), Mock()
                    ).update_hackathon(public_id, HackathonUpdate(capacity=1), user)
                else:
                    await service.update_status(targets[index], RegistrationStatus.ACCEPTED, user)
                return "ok"
            except HackathonCapacityFullError:
                return "full"

    results = await asyncio.wait_for(asyncio.gather(run(0), run(1)), timeout=10)
    assert sorted(results) == (["ok", "ok"] if race == "same_registration" else ["full", "ok"])
    await session.refresh(hackathon)
    count = await HackathonRepository(session).count_accepted_registrations(hackathon_id)
    assert count <= hackathon.capacity
    assert count == (2 if race == "lower_capacity" and hackathon.capacity == 2 else 1)


async def test_capacity_lock_does_not_block_new_pending_registration(session, capacity_setup):
    _, hackathon, _ = capacity_setup
    newcomer = await create_user(session, "concurrent@example.com")
    await session.commit()
    hackathon_id, user_id = hackathon.id, newcomer.id
    factory = async_sessionmaker(session.bind, expire_on_commit=False)
    await HackathonRepository(session).get_active_by_public_id_for_update(hackathon.public_id)

    async def insert_pending():
        async with factory() as worker:
            worker.add(Registration(hackathon_id=hackathon_id, user_id=user_id))
            await worker.commit()

    try:
        await asyncio.wait_for(insert_pending(), timeout=5)
    finally:
        await session.rollback()
