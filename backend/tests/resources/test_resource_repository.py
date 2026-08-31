import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.hackathons.models import Hackathon
from src.registration.models import Registration, RegistrationStatus
from src.resources.models import Resource, ResourceAssignment, ResourceItem
from src.resources.repository import ResourceRepository
from src.teams.models import Team


def make_user(email: str) -> User:
    return User(name=email.split("@", maxsplit=1)[0], email=email, password_hash="hash")


def make_hackathon(organizer: User, *, name: str = "Resource Hackathon") -> Hackathon:
    now = datetime.now(UTC)
    return Hackathon(
        organizer=organizer,
        co_organizers=[],
        name=name,
        start_date=now + timedelta(days=2),
        end_date=now + timedelta(days=3),
        registration_opens_at=now - timedelta(hours=1),
        registration_deadline=now + timedelta(days=1),
        registration_open=True,
        max_team_size=4,
    )


def make_resource(hackathon: Hackathon, *, name: str = "API keys") -> Resource:
    return Resource(
        hackathon=hackathon,
        name=name,
        type="api_key",
        distribution_mode="manual",
        target="individual",
        resource_metadata={},
    )


async def test_get_hackathon_loads_co_organizers_and_hides_deleted(session: AsyncSession):
    organizer = make_user("organizer@example.com")
    co_organizer = make_user("co@example.com")
    hackathon = make_hackathon(organizer)
    hackathon.co_organizers.append(co_organizer)
    session.add(hackathon)
    await session.flush()
    repository = ResourceRepository(session)

    result = await repository.get_hackathon(hackathon.public_id)

    assert result is hackathon
    assert result.co_organizers == [co_organizer]

    hackathon.is_deleted = True
    await session.flush()
    assert await repository.get_hackathon(hackathon.public_id) is None


async def test_get_resource_is_scoped_to_active_hackathon_and_counts_items(
    session: AsyncSession,
):
    organizer = make_user("organizer@example.com")
    hackathon = make_hackathon(organizer)
    other_hackathon = make_hackathon(organizer, name="Other")
    resource = make_resource(hackathon)
    resource.items.extend(
        [ResourceItem(encrypted_value="one"), ResourceItem(encrypted_value="two")]
    )
    session.add_all([resource, other_hackathon])
    await session.flush()
    repository = ResourceRepository(session)

    result = await repository.get_resource(hackathon.public_id, resource.public_id)

    assert result is resource
    assert result.item_count == 2
    assert await repository.get_resource(other_hackathon.public_id, resource.public_id) is None

    hackathon.is_deleted = True
    await session.flush()
    assert await repository.get_resource(hackathon.public_id, resource.public_id) is None


async def test_item_registration_and_team_queries_are_scoped(session: AsyncSession):
    organizer = make_user("organizer@example.com")
    participant = make_user("participant@example.com")
    hackathon = make_hackathon(organizer)
    other_hackathon = make_hackathon(organizer, name="Other")
    resource = make_resource(hackathon)
    item = ResourceItem(resource=resource, encrypted_value="secret")
    accepted = Registration(
        hackathon=hackathon,
        user=participant,
        status=RegistrationStatus.ACCEPTED,
    )
    pending = Registration(
        hackathon=hackathon,
        user=make_user("pending@example.com"),
        status=RegistrationStatus.PENDING,
    )
    team = Team(hackathon=hackathon, name="Alpha", join_code="ALPHA001")
    session.add_all([item, accepted, pending, team, other_hackathon])
    await session.flush()
    repository = ResourceRepository(session)

    assert await repository.get_item_for_update(resource.id, item.public_id) is item
    assert await repository.get_item_for_update(resource.id, uuid.uuid4()) is None
    assert await repository.get_registration(hackathon.id, accepted.public_id) is accepted
    assert await repository.get_registration(hackathon.id, pending.public_id) is None
    assert await repository.get_registration(other_hackathon.id, accepted.public_id) is None
    assert await repository.get_team(hackathon.id, team.public_id) is team
    assert await repository.get_team(other_hackathon.id, team.public_id) is None


async def test_list_items_is_scoped_ordered_and_paginated(session: AsyncSession):
    organizer = make_user("organizer@example.com")
    hackathon = make_hackathon(organizer)
    resource = make_resource(hackathon)
    other_resource = make_resource(hackathon, name="Other keys")
    items = [
        ResourceItem(resource=resource, encrypted_value=f"secret-{index}")
        for index in range(3)
    ]
    other_item = ResourceItem(resource=other_resource, encrypted_value="other-secret")
    session.add_all([*items, other_item])
    await session.flush()
    repository = ResourceRepository(session)

    result = await repository.list_items(resource.id, limit=1, offset=1)

    assert result == [items[1]]


async def test_create_methods_flush_entities(session: AsyncSession):
    organizer = make_user("organizer@example.com")
    participant = make_user("participant@example.com")
    hackathon = make_hackathon(organizer)
    registration = Registration(
        hackathon=hackathon,
        user=participant,
        status=RegistrationStatus.ACCEPTED,
    )
    repository = ResourceRepository(session)
    resource = make_resource(hackathon)

    assert await repository.create_resource(resource) is resource
    items = [ResourceItem(resource=resource, encrypted_value="one")]
    assert await repository.create_items(items) is items
    assignment = ResourceAssignment(
        resource_item=items[0], registration=registration, assigned_by=organizer
    )
    assert await repository.create_assignment(assignment) is assignment

    assert resource.id is not None
    assert items[0].id is not None
    assert assignment.id is not None
