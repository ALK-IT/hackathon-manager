import uuid
from dataclasses import dataclass

from src.auth.models import User
from src.resources.crypto import encrypt_value
from src.resources.exceptions import (
    ResourceItemNotFoundError,
    ResourceItemUnavailableError,
    ResourceNotFoundError,
    ResourcePermissionError,
    ResourceRecipientNotFoundError,
    ResourceTargetMismatchError,
)
from src.resources.models import Resource, ResourceAssignment, ResourceItem
from src.resources.repository import ResourceRepository
from src.resources.schemas import (
    ResourceAssignmentCreate,
    ResourceCreate,
)


@dataclass(frozen=True)
class ResourceImportResult:
    resource: Resource
    imported_count: int


class ResourceService:
    def __init__(self, repository: ResourceRepository):
        self.repository = repository

    async def _get_owned_hackathon(self, hackathon_public_id: uuid.UUID, current_user: User):
        hackathon = await self.repository.get_hackathon(hackathon_public_id)
        if hackathon is None:
            raise ResourceNotFoundError()
        is_co_organizer = any(
            co_organizer.id == current_user.id for co_organizer in hackathon.co_organizers
        )
        if hackathon.organizer_id != current_user.id and not is_co_organizer:
            raise ResourcePermissionError()
        return hackathon

    async def create_resource(
        self,
        hackathon_public_id: uuid.UUID,
        data: ResourceCreate,
        current_user: User,
    ) -> Resource:
        hackathon = await self._get_owned_hackathon(hackathon_public_id, current_user)
        resource = Resource(
            hackathon_id=hackathon.id,
            name=data.name.strip(),
            type=data.type,
            distribution_mode=data.distribution_mode,
            target=data.target,
            resource_metadata=data.metadata,
        )
        resource.item_count = 0
        try:
            await self.repository.create_resource(resource)
            await self.repository.commit()
        except Exception:
            await self.repository.rollback()
            raise
        return resource

    async def import_items(
        self,
        hackathon_public_id: uuid.UUID,
        resource_public_id: uuid.UUID,
        values: list[str],
        current_user: User,
    ) -> ResourceImportResult:
        await self._get_owned_hackathon(hackathon_public_id, current_user)
        resource = await self.repository.get_resource(hackathon_public_id, resource_public_id)
        if resource is None:
            raise ResourceNotFoundError()
        items = [
            ResourceItem(resource_id=resource.id, encrypted_value=encrypt_value(value))
            for value in values
        ]
        try:
            await self.repository.create_items(items)
            await self.repository.commit()
        except Exception:
            await self.repository.rollback()
            raise
        resource.item_count += len(items)
        return ResourceImportResult(
            resource=resource,
            imported_count=len(items),
        )

    async def assign_item(
        self,
        hackathon_public_id: uuid.UUID,
        resource_public_id: uuid.UUID,
        data: ResourceAssignmentCreate,
        current_user: User,
    ) -> ResourceAssignment:
        hackathon = await self._get_owned_hackathon(hackathon_public_id, current_user)
        resource = await self.repository.get_resource(hackathon_public_id, resource_public_id)
        if resource is None:
            raise ResourceNotFoundError()

        item = await self.repository.get_item_for_update(
            resource.id,
            data.resource_item_public_id,
        )
        if item is None:
            raise ResourceItemNotFoundError()
        if item.is_assigned or item.is_revoked:
            raise ResourceItemUnavailableError()

        registration = None
        team = None
        if resource.target == "individual":
            if data.registration_public_id is None:
                raise ResourceTargetMismatchError()
            registration = await self.repository.get_registration(
                hackathon.id,
                data.registration_public_id,
            )
            if registration is None:
                raise ResourceRecipientNotFoundError()
        elif resource.target == "team":
            if data.team_public_id is None:
                raise ResourceTargetMismatchError()
            team = await self.repository.get_team(hackathon.id, data.team_public_id)
            if team is None:
                raise ResourceRecipientNotFoundError()
        else:
            raise ResourceTargetMismatchError()

        assignment = ResourceAssignment(
            resource_item=item,
            registration=registration,
            team=team,
            assigned_by=current_user,
        )
        item.is_assigned = True
        try:
            await self.repository.create_assignment(assignment)
            await self.repository.commit()
        except Exception:
            await self.repository.rollback()
            raise

        return assignment
