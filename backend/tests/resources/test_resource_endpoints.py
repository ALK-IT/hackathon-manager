import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.hackathons.models import Hackathon
from src.main import app
from src.registration.models import Registration, RegistrationStatus
from src.resources.crypto import decrypt_value
from src.resources.models import Resource, ResourceAssignment, ResourceItem
from src.teams.models import Team

ForceAuthenticate = Callable[[User | None], None]


async def create_user(session: AsyncSession, email: str) -> User:
    user = User(
        name=email.split("@", maxsplit=1)[0].title(),
        email=f"{uuid.uuid4()}-{email}",
        password_hash="test-password-hash",
    )
    session.add(user)
    await session.flush()
    return user


async def create_hackathon(session: AsyncSession, organizer: User) -> Hackathon:
    now = datetime.now(UTC)
    hackathon = Hackathon(
        organizer=organizer,
        co_organizers=[],
        name="Resource Test Hackathon",
        description="Resource endpoint tests",
        start_date=now + timedelta(days=2),
        end_date=now + timedelta(days=3),
        registration_opens_at=now - timedelta(hours=1),
        registration_deadline=now + timedelta(days=1),
        registration_open=True,
        capacity=50,
        max_team_size=4,
        teams_enabled=True,
    )
    session.add(hackathon)
    await session.flush()
    return hackathon


async def create_resource(
    session: AsyncSession,
    hackathon: Hackathon,
    *,
    target: str,
) -> Resource:
    resource = Resource(
        hackathon=hackathon,
        name="OpenAI API keys",
        type="api_key",
        distribution_mode="manual",
        target=target,
        resource_metadata={"provider": "openai"},
    )
    session.add(resource)
    await session.flush()
    return resource


async def create_item(session: AsyncSession, resource: Resource) -> ResourceItem:
    item = ResourceItem(resource=resource, encrypted_value="encrypted-test-value")
    session.add(item)
    await session.flush()
    return item


async def create_registration(
    session: AsyncSession,
    hackathon: Hackathon,
    participant: User,
    *,
    team: Team | None = None,
    status: RegistrationStatus = RegistrationStatus.ACCEPTED,
) -> Registration:
    registration = Registration(
        hackathon=hackathon,
        user=participant,
        team=team,
        status=status,
    )
    session.add(registration)
    await session.flush()
    return registration


async def create_team(session: AsyncSession, hackathon: Hackathon) -> Team:
    team = Team(
        hackathon=hackathon,
        name=f"Team-{uuid.uuid4().hex[:8]}",
        join_code=uuid.uuid4().hex[:8].upper(),
    )
    session.add(team)
    await session.flush()
    return team


def test_resource_routes_are_registered():
    paths = set(app.openapi()["paths"])

    assert {
        "/api/hackathons/{hackathon_public_id}/resources",
        "/api/hackathons/{hackathon_public_id}/resources/{resource_public_id}/items",
        "/api/hackathons/{hackathon_public_id}/resources/{resource_public_id}/assignments",
        "/api/hackathons/{hackathon_public_id}/resources/{resource_public_id}/participant-assignments",
        "/api/hackathons/{hackathon_public_id}/resources/{resource_public_id}/participant-assignments/{registration_public_id}",
    }.issubset(paths)


async def test_organizer_creates_resource_with_public_contract(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    hackathon = await create_hackathon(session, organizer)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/resources",
        json={
            "name": "OpenAI API keys",
            "type": "api_key",
            "distribution_mode": "manual",
            "target": "individual",
            "metadata": {"provider": "openai"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {
        "public_id",
        "name",
        "type",
        "distribution_mode",
        "target",
        "metadata",
        "item_count",
    }
    assert body["item_count"] == 0
    assert body["metadata"] == {"provider": "openai"}

    resource = await session.scalar(
        select(Resource).where(Resource.public_id == uuid.UUID(body["public_id"]))
    )
    assert resource is not None
    assert resource.hackathon_id == hackathon.id


async def test_organizer_atomically_creates_resource_with_encrypted_items(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    hackathon = await create_hackathon(session, organizer)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/resources",
        json={
            "name": "Warsztatowe klucze API",
            "type": "api_key",
            "target": "individual",
            "values": [" first-secret ", "second-secret"],
        },
    )

    assert response.status_code == 201
    assert response.json()["item_count"] == 2
    assert "first-secret" not in response.text
    assert "second-secret" not in response.text
    resource = await session.scalar(
        select(Resource).where(Resource.public_id == uuid.UUID(response.json()["public_id"]))
    )
    assert resource is not None
    items = list(
        await session.scalars(
            select(ResourceItem)
            .where(ResourceItem.resource_id == resource.id)
            .order_by(ResourceItem.id)
        )
    )
    assert [decrypt_value(item.encrypted_value) for item in items] == [
        "first-secret",
        "second-secret",
    ]


async def test_import_encrypts_every_value_and_never_returns_plaintext(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    hackathon = await create_hackathon(session, organizer)
    resource = await create_resource(session, hackathon, target="individual")
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/items",
        json={"values": [" first-secret ", "second-secret"]},
    )

    assert response.status_code == 201
    assert response.json()["imported_count"] == 2
    assert "first-secret" not in response.text
    assert "second-secret" not in response.text

    items = list(
        await session.scalars(
            select(ResourceItem)
            .where(ResourceItem.resource_id == resource.id)
            .order_by(ResourceItem.id)
        )
    )
    assert [decrypt_value(item.encrypted_value) for item in items] == [
        "first-secret",
        "second-secret",
    ]
    assert all(item.encrypted_value not in {"first-secret", "second-secret"} for item in items)


async def test_organizer_imports_lists_and_assigns_item_using_only_public_api(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    registration = await create_registration(session, hackathon, participant)
    resource = await create_resource(session, hackathon, target="individual")
    await session.commit()
    force_authenticate(organizer)
    items_url = f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/items"

    import_response = await api_client.post(items_url, json={"values": ["secret-api-key"]})
    list_response = await api_client.get(items_url)

    assert import_response.status_code == 201
    assert list_response.status_code == 200
    assert "secret-api-key" not in list_response.text
    items = list_response.json()
    assert len(items) == 1
    assert set(items[0]) == {
        "public_id",
        "resource_public_id",
        "is_assigned",
        "is_revoked",
    }
    assert items[0]["resource_public_id"] == str(resource.public_id)
    assert items[0]["is_assigned"] is False
    assert items[0]["is_revoked"] is False

    assignment_response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/resources/" f"{resource.public_id}/assignments",
        json={
            "resource_item_public_id": items[0]["public_id"],
            "registration_public_id": str(registration.public_id),
        },
    )

    assert assignment_response.status_code == 201

    assigned_items_response = await api_client.get(items_url)
    assert assigned_items_response.status_code == 200
    assert assigned_items_response.json()[0]["is_assigned"] is True


async def test_organizer_lists_resource_inventory(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    hackathon = await create_hackathon(session, organizer)
    resource = await create_resource(session, hackathon, target="individual")
    available_item = await create_item(session, resource)
    assigned_item = await create_item(session, resource)
    assigned_item.is_assigned = True
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.get(f"/api/hackathons/{hackathon.public_id}/resources")

    assert response.status_code == 200
    assert response.json() == [
        {
            "public_id": str(resource.public_id),
            "name": "OpenAI API keys",
            "type": "api_key",
            "distribution_mode": "manual",
            "target": "individual",
            "metadata": {"provider": "openai"},
            "item_count": 2,
            "available_item_count": 1,
        }
    ]
    assert available_item.is_assigned is False


async def test_organizer_assigns_available_items_to_participants_and_lists_assignments(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    first_participant = await create_user(session, "first@example.com")
    second_participant = await create_user(session, "second@example.com")
    hackathon = await create_hackathon(session, organizer)
    first_registration = await create_registration(session, hackathon, first_participant)
    second_registration = await create_registration(session, hackathon, second_participant)
    resource = await create_resource(session, hackathon, target="individual")
    await create_item(session, resource)
    await create_item(session, resource)
    await session.commit()
    force_authenticate(organizer)
    url = (
        f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/"
        "participant-assignments"
    )

    response = await api_client.post(
        url,
        json={
            "registration_public_ids": [
                str(first_registration.public_id),
                str(second_registration.public_id),
            ]
        },
    )

    assert response.status_code == 201
    assert {
        assignment["registration_public_id"] for assignment in response.json()["assignments"]
    } == {str(first_registration.public_id), str(second_registration.public_id)}
    assert response.json()["already_assigned_registration_public_ids"] == []

    repeat_response = await api_client.post(
        url,
        json={"registration_public_ids": [str(first_registration.public_id)]},
    )
    assert repeat_response.status_code == 201
    assert repeat_response.json()["assignments"] == []
    assert repeat_response.json()["already_assigned_registration_public_ids"] == [
        str(first_registration.public_id)
    ]

    list_response = await api_client.get(url)
    assert list_response.status_code == 200
    assert {assignment["registration_public_id"] for assignment in list_response.json()} == {
        str(first_registration.public_id),
        str(second_registration.public_id),
    }


async def test_bulk_assignment_is_atomic_when_pool_has_too_few_items(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    first_participant = await create_user(session, "first@example.com")
    second_participant = await create_user(session, "second@example.com")
    hackathon = await create_hackathon(session, organizer)
    first_registration = await create_registration(session, hackathon, first_participant)
    second_registration = await create_registration(session, hackathon, second_participant)
    resource = await create_resource(session, hackathon, target="individual")
    item = await create_item(session, resource)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/"
        "participant-assignments",
        json={
            "registration_public_ids": [
                str(first_registration.public_id),
                str(second_registration.public_id),
            ]
        },
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "RESOURCE_ITEMS_INSUFFICIENT"
    assignments = list(await session.scalars(select(ResourceAssignment)))
    assert assignments == []
    await session.refresh(item)
    assert item.is_assigned is False


async def test_organizer_revokes_participant_resource_without_reusing_secret(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    registration = await create_registration(session, hackathon, participant)
    resource = await create_resource(session, hackathon, target="individual")
    item = await create_item(session, resource)
    assignment = ResourceAssignment(
        resource_item=item,
        registration=registration,
        assigned_by=organizer,
    )
    item.is_assigned = True
    session.add(assignment)
    await session.commit()
    force_authenticate(organizer)
    url = (
        f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/"
        f"participant-assignments/{registration.public_id}"
    )

    response = await api_client.delete(url)

    assert response.status_code == 204
    await session.refresh(assignment)
    await session.refresh(item)
    assert assignment.revoked_at is not None
    assert item.is_assigned is True
    assert item.is_revoked is True

    repeat_response = await api_client.delete(url)
    assert repeat_response.status_code == 204


async def test_outsider_cannot_list_assign_or_revoke_participant_resources(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    outsider = await create_user(session, "outsider@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    registration = await create_registration(session, hackathon, participant)
    resource = await create_resource(session, hackathon, target="individual")
    await create_item(session, resource)
    await session.commit()
    force_authenticate(outsider)
    assignments_url = (
        f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/"
        "participant-assignments"
    )

    responses = [
        await api_client.get(f"/api/hackathons/{hackathon.public_id}/resources"),
        await api_client.get(assignments_url),
        await api_client.post(
            assignments_url,
            json={"registration_public_ids": [str(registration.public_id)]},
        ),
        await api_client.delete(f"{assignments_url}/{registration.public_id}"),
    ]

    assert [response.status_code for response in responses] == [403, 403, 403, 403]
    assert all(response.json()["error_code"] == "PERMISSION_DENIED" for response in responses)


async def test_co_organizer_can_bulk_assign_participant_resources(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    co_organizer = await create_user(session, "co-organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    hackathon.co_organizers.append(co_organizer)
    registration = await create_registration(session, hackathon, participant)
    resource = await create_resource(session, hackathon, target="individual")
    await create_item(session, resource)
    await session.commit()
    force_authenticate(co_organizer)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/"
        "participant-assignments",
        json={"registration_public_ids": [str(registration.public_id)]},
    )

    assert response.status_code == 201
    assert response.json()["assignments"][0]["registration_public_id"] == str(
        registration.public_id
    )


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
async def test_list_resource_items_validates_pagination(
    query: str,
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    hackathon = await create_hackathon(session, organizer)
    resource = await create_resource(session, hackathon, target="individual")
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.get(
        f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/items?{query}"
    )

    assert response.status_code == 422


@pytest.mark.parametrize("operation", ["create", "import", "list", "assign"])
async def test_outsider_cannot_manage_resources(
    operation: str,
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    outsider = await create_user(session, "outsider@example.com")
    hackathon = await create_hackathon(session, organizer)
    resource = await create_resource(session, hackathon, target="individual")
    item = await create_item(session, resource)
    registration = await create_registration(session, hackathon, outsider)
    await session.commit()
    force_authenticate(outsider)

    if operation == "create":
        response = await api_client.post(
            f"/api/hackathons/{hackathon.public_id}/resources",
            json={"name": "Key", "type": "api_key", "target": "individual"},
        )
    elif operation == "import":
        response = await api_client.post(
            f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/items",
            json={"values": ["secret"]},
        )
    elif operation == "list":
        response = await api_client.get(
            f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/items"
        )
    else:
        response = await api_client.post(
            f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/assignments",
            json={
                "resource_item_public_id": str(item.public_id),
                "registration_public_id": str(registration.public_id),
            },
        )

    assert response.status_code == 403
    assert response.json()["error_code"] == "PERMISSION_DENIED"


@pytest.mark.parametrize("operation", ["create", "import", "list", "assign"])
async def test_co_organizer_can_manage_resources(
    operation: str,
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    co_organizer = await create_user(session, "co-organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    hackathon.co_organizers.append(co_organizer)
    resource = await create_resource(session, hackathon, target="individual")
    item = await create_item(session, resource)
    registration = await create_registration(session, hackathon, participant)
    await session.commit()
    force_authenticate(co_organizer)

    if operation == "create":
        response = await api_client.post(
            f"/api/hackathons/{hackathon.public_id}/resources",
            json={"name": "Key", "type": "api_key", "target": "individual"},
        )
    elif operation == "import":
        response = await api_client.post(
            f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/items",
            json={"values": ["secret"]},
        )
    elif operation == "list":
        response = await api_client.get(
            f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/items"
        )
    else:
        response = await api_client.post(
            f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/assignments",
            json={
                "resource_item_public_id": str(item.public_id),
                "registration_public_id": str(registration.public_id),
            },
        )

    assert response.status_code == (200 if operation == "list" else 201)


async def test_organizer_assigns_item_to_participant_registration(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    registration = await create_registration(session, hackathon, participant)
    resource = await create_resource(session, hackathon, target="individual")
    item = await create_item(session, resource)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/assignments",
        json={
            "resource_item_public_id": str(item.public_id),
            "registration_public_id": str(registration.public_id),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"public_id", "assigned_at", "revoked_at"}
    assert body["revoked_at"] is None
    assignment = await session.scalar(
        select(ResourceAssignment).where(
            ResourceAssignment.public_id == uuid.UUID(body["public_id"])
        )
    )
    assert assignment is not None
    assert assignment.registration_id == registration.id
    assert assignment.team_id is None
    await session.refresh(item)
    assert item.is_assigned is True


async def test_organizer_assigns_item_to_team(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    hackathon = await create_hackathon(session, organizer)
    team = await create_team(session, hackathon)
    resource = await create_resource(session, hackathon, target="team")
    item = await create_item(session, resource)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/assignments",
        json={
            "resource_item_public_id": str(item.public_id),
            "team_public_id": str(team.public_id),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"public_id", "assigned_at", "revoked_at"}
    assignment = await session.scalar(
        select(ResourceAssignment).where(
            ResourceAssignment.public_id == uuid.UUID(body["public_id"])
        )
    )
    assert assignment is not None
    assert assignment.team_id == team.id
    assert assignment.registration_id is None


async def test_assignment_rejects_recipient_that_does_not_match_resource_target(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    registration = await create_registration(session, hackathon, participant)
    resource = await create_resource(session, hackathon, target="team")
    item = await create_item(session, resource)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/assignments",
        json={
            "resource_item_public_id": str(item.public_id),
            "registration_public_id": str(registration.public_id),
        },
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "RESOURCE_TARGET_MISMATCH"


@pytest.mark.parametrize(
    "registration_status",
    [RegistrationStatus.PENDING, RegistrationStatus.REJECTED],
)
async def test_assignment_rejects_registration_that_is_not_accepted(
    registration_status: RegistrationStatus,
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    registration = await create_registration(
        session,
        hackathon,
        participant,
        status=registration_status,
    )
    resource = await create_resource(session, hackathon, target="individual")
    item = await create_item(session, resource)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/assignments",
        json={
            "resource_item_public_id": str(item.public_id),
            "registration_public_id": str(registration.public_id),
        },
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "RESOURCE_RECIPIENT_NOT_FOUND"
    await session.refresh(item)
    assert item.is_assigned is False


async def test_assignment_requires_exactly_one_recipient(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    organizer = await create_user(session, "organizer@example.com")
    hackathon = await create_hackathon(session, organizer)
    resource = await create_resource(session, hackathon, target="individual")
    item = await create_item(session, resource)
    await session.commit()
    force_authenticate(organizer)

    response = await api_client.post(
        f"/api/hackathons/{hackathon.public_id}/resources/{resource.public_id}/assignments",
        json={"resource_item_public_id": str(item.public_id)},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


def test_assignment_model_enforces_exactly_one_recipient():
    constraint_names = {constraint.name for constraint in ResourceAssignment.__table__.constraints}

    assert "ck_resource_assignments_exactly_one_recipient" in constraint_names
    assert "uq_resource_assignment_item" in constraint_names


async def test_assignment_database_rejects_missing_recipient(session: AsyncSession):
    organizer = await create_user(session, "organizer@example.com")
    hackathon = await create_hackathon(session, organizer)
    resource = await create_resource(session, hackathon, target="individual")
    item = await create_item(session, resource)
    assignment = ResourceAssignment(
        resource_item=item,
        assigned_by=organizer,
        registration=None,
        team=None,
    )
    session.add(assignment)

    with pytest.raises(IntegrityError):
        await session.flush()

    await session.rollback()


@pytest.mark.parametrize("recipient_type", ["registration", "team"])
async def test_assignment_prevents_recipient_deletion(
    recipient_type: str,
    session: AsyncSession,
):
    organizer = await create_user(session, "organizer@example.com")
    participant = await create_user(session, "participant@example.com")
    hackathon = await create_hackathon(session, organizer)
    resource = await create_resource(
        session,
        hackathon,
        target="individual" if recipient_type == "registration" else "team",
    )
    item = await create_item(session, resource)

    if recipient_type == "registration":
        recipient = await create_registration(session, hackathon, participant)
        assignment = ResourceAssignment(
            resource_item=item,
            assigned_by=organizer,
            registration=recipient,
        )
    else:
        recipient = await create_team(session, hackathon)
        assignment = ResourceAssignment(
            resource_item=item,
            assigned_by=organizer,
            team=recipient,
        )

    session.add(assignment)
    await session.commit()
    await session.delete(recipient)

    with pytest.raises(IntegrityError):
        await session.flush()

    await session.rollback()
