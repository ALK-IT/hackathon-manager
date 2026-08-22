import uuid
from types import SimpleNamespace

import pytest

from src.auth.models import User
from src.registration.models import Registration
from src.resources.crypto import decrypt_value
from src.resources.exceptions import (
    ResourceItemNotFoundError,
    ResourceItemUnavailableError,
    ResourceNotFoundError,
    ResourcePermissionError,
    ResourceRecipientNotFoundError,
    ResourceTargetMismatchError,
)
from src.resources.models import Resource, ResourceItem
from src.resources.schemas import ResourceAssignmentCreate, ResourceCreate
from src.resources.service import ResourceService
from src.teams.models import Team


def make_user(user_id: int = 1) -> User:
    user = User(name=f"User {user_id}", email=f"user-{user_id}@example.com", password_hash="hash")
    user.id = user_id
    return user


def make_hackathon(*, organizer_id: int = 1, co_organizer_ids: tuple[int, ...] = ()):
    return SimpleNamespace(
        id=10,
        organizer_id=organizer_id,
        co_organizers=[SimpleNamespace(id=user_id) for user_id in co_organizer_ids],
    )


def make_resource(*, target: str = "individual") -> Resource:
    resource = Resource(
        id=20,
        hackathon_id=10,
        name="API keys",
        type="api_key",
        distribution_mode="manual",
        target=target,
        resource_metadata={},
    )
    resource.item_count = 0
    return resource


@pytest.fixture
def repository(mocker):
    repository = mocker.Mock()
    repository.get_hackathon = mocker.AsyncMock()
    repository.get_resource = mocker.AsyncMock()
    repository.get_item_for_update = mocker.AsyncMock()
    repository.get_registration = mocker.AsyncMock()
    repository.get_team = mocker.AsyncMock()
    repository.create_resource = mocker.AsyncMock()
    repository.create_items = mocker.AsyncMock()
    repository.create_assignment = mocker.AsyncMock()
    repository.commit = mocker.AsyncMock()
    repository.rollback = mocker.AsyncMock()
    return repository


@pytest.fixture
def service(repository):
    return ResourceService(repository)


async def test_create_resource_normalizes_name_and_commits(service, repository):
    repository.get_hackathon.return_value = make_hackathon()
    data = ResourceCreate(name="  Credits  ", type="api_key", target="individual")

    result = await service.create_resource(uuid.uuid4(), data, make_user())

    assert result.name == "Credits"
    assert result.hackathon_id == 10
    assert result.item_count == 0
    repository.create_resource.assert_awaited_once_with(result)
    repository.commit.assert_awaited_once_with()
    repository.rollback.assert_not_awaited()


@pytest.mark.parametrize(
    ("hackathon", "error_type"),
    [(None, ResourceNotFoundError), (make_hackathon(organizer_id=99), ResourcePermissionError)],
)
async def test_create_resource_rejects_missing_hackathon_or_outsider(
    service, repository, hackathon, error_type
):
    repository.get_hackathon.return_value = hackathon

    with pytest.raises(error_type):
        await service.create_resource(
            uuid.uuid4(),
            ResourceCreate(name="Credits", type="api_key", target="individual"),
            make_user(),
        )

    repository.create_resource.assert_not_awaited()


async def test_co_organizer_can_create_resource(service, repository):
    repository.get_hackathon.return_value = make_hackathon(organizer_id=99, co_organizer_ids=(1,))

    await service.create_resource(
        uuid.uuid4(),
        ResourceCreate(name="Credits", type="api_key", target="team"),
        make_user(),
    )

    repository.create_resource.assert_awaited_once()


async def test_import_items_encrypts_values_updates_count_and_commits(service, repository):
    repository.get_hackathon.return_value = make_hackathon()
    resource = make_resource()
    resource.item_count = 3
    repository.get_resource.return_value = resource

    result = await service.import_items(
        uuid.uuid4(), resource.public_id, ["secret-one", "secret-two"], make_user()
    )

    items = repository.create_items.await_args.args[0]
    assert [decrypt_value(item.encrypted_value) for item in items] == [
        "secret-one",
        "secret-two",
    ]
    assert all(item.resource_id == resource.id for item in items)
    assert result.imported_count == 2
    assert result.resource.item_count == 5
    repository.commit.assert_awaited_once_with()


async def test_import_items_rejects_unknown_resource(service, repository):
    repository.get_hackathon.return_value = make_hackathon()
    repository.get_resource.return_value = None

    with pytest.raises(ResourceNotFoundError):
        await service.import_items(uuid.uuid4(), uuid.uuid4(), ["secret"], make_user())

    repository.create_items.assert_not_awaited()


@pytest.mark.parametrize("method", ["create_resource", "create_items", "create_assignment"])
async def test_write_failures_are_rolled_back(service, repository, method):
    repository.get_hackathon.return_value = make_hackathon()
    repository.get_resource.return_value = make_resource()
    item = ResourceItem(id=30, resource_id=20, encrypted_value="secret")
    repository.get_item_for_update.return_value = item
    repository.get_registration.return_value = Registration(id=40)
    getattr(repository, method).side_effect = RuntimeError("database failed")

    with pytest.raises(RuntimeError, match="database failed"):
        if method == "create_resource":
            await service.create_resource(
                uuid.uuid4(),
                ResourceCreate(name="Credits", type="api_key", target="individual"),
                make_user(),
            )
        elif method == "create_items":
            await service.import_items(uuid.uuid4(), uuid.uuid4(), ["secret"], make_user())
        else:
            await service.assign_item(
                uuid.uuid4(),
                uuid.uuid4(),
                ResourceAssignmentCreate(
                    resource_item_public_id=uuid.uuid4(),
                    registration_public_id=uuid.uuid4(),
                ),
                make_user(),
            )

    repository.rollback.assert_awaited_once_with()
    repository.commit.assert_not_awaited()


@pytest.mark.parametrize("state", ["missing", "assigned", "revoked"])
async def test_assign_item_rejects_missing_or_unavailable_item(service, repository, state):
    repository.get_hackathon.return_value = make_hackathon()
    resource = make_resource()
    repository.get_resource.return_value = resource
    if state == "missing":
        repository.get_item_for_update.return_value = None
        expected_error = ResourceItemNotFoundError
    else:
        repository.get_item_for_update.return_value = ResourceItem(
            resource_id=resource.id,
            encrypted_value="secret",
            is_assigned=state == "assigned",
            is_revoked=state == "revoked",
        )
        expected_error = ResourceItemUnavailableError

    with pytest.raises(expected_error):
        await service.assign_item(
            uuid.uuid4(),
            resource.public_id,
            ResourceAssignmentCreate(
                resource_item_public_id=uuid.uuid4(),
                registration_public_id=uuid.uuid4(),
            ),
            make_user(),
        )

    repository.create_assignment.assert_not_awaited()


@pytest.mark.parametrize(
    ("target", "recipient_field"),
    [("individual", "team_public_id"), ("team", "registration_public_id")],
)
async def test_assign_item_rejects_recipient_type_mismatch(
    service, repository, target, recipient_field
):
    repository.get_hackathon.return_value = make_hackathon()
    resource = make_resource(target=target)
    repository.get_resource.return_value = resource
    repository.get_item_for_update.return_value = ResourceItem(
        resource_id=resource.id, encrypted_value="secret"
    )
    data = ResourceAssignmentCreate(
        resource_item_public_id=uuid.uuid4(), **{recipient_field: uuid.uuid4()}
    )

    with pytest.raises(ResourceTargetMismatchError):
        await service.assign_item(uuid.uuid4(), resource.public_id, data, make_user())


@pytest.mark.parametrize("target", ["individual", "team"])
async def test_assign_item_rejects_unknown_recipient(service, repository, target):
    repository.get_hackathon.return_value = make_hackathon()
    resource = make_resource(target=target)
    repository.get_resource.return_value = resource
    repository.get_item_for_update.return_value = ResourceItem(
        resource_id=resource.id, encrypted_value="secret"
    )
    repository.get_registration.return_value = None
    repository.get_team.return_value = None
    field = "registration_public_id" if target == "individual" else "team_public_id"

    with pytest.raises(ResourceRecipientNotFoundError):
        await service.assign_item(
            uuid.uuid4(),
            resource.public_id,
            ResourceAssignmentCreate(resource_item_public_id=uuid.uuid4(), **{field: uuid.uuid4()}),
            make_user(),
        )


@pytest.mark.parametrize("target", ["individual", "team"])
async def test_assign_item_creates_assignment_and_marks_item_assigned(service, repository, target):
    user = make_user()
    repository.get_hackathon.return_value = make_hackathon()
    resource = make_resource(target=target)
    item = ResourceItem(id=30, resource_id=resource.id, encrypted_value="secret")
    repository.get_resource.return_value = resource
    repository.get_item_for_update.return_value = item
    if target == "individual":
        recipient = Registration(id=40)
        repository.get_registration.return_value = recipient
        data = ResourceAssignmentCreate(
            resource_item_public_id=uuid.uuid4(), registration_public_id=uuid.uuid4()
        )
    else:
        recipient = Team(id=50)
        repository.get_team.return_value = recipient
        data = ResourceAssignmentCreate(
            resource_item_public_id=uuid.uuid4(), team_public_id=uuid.uuid4()
        )

    result = await service.assign_item(uuid.uuid4(), resource.public_id, data, user)

    assert result.resource_item is item
    assert result.assigned_by is user
    assert result.registration is (recipient if target == "individual" else None)
    assert result.team is (recipient if target == "team" else None)
    assert item.is_assigned is True
    repository.create_assignment.assert_awaited_once_with(result)
    repository.commit.assert_awaited_once_with()
