import uuid

from src.auth.models import User
from src.resources.crypto import encrypt_value
from src.resources.exceptions import ResourceNotFoundError, ResourcePermissionError
from src.resources.models import Resource, ResourceItem
from src.resources.repository import ResourceRepository
from src.resources.schemas import ResourceCreate, ResourceImportResponse, ResourceResponse


class ResourceService:
    def __init__(self, repository: ResourceRepository):
        self.repository = repository

    async def _get_owned_hackathon(
        self, hackathon_public_id: uuid.UUID, current_user: User
    ):
        hackathon = await self.repository.get_hackathon(hackathon_public_id)
        if hackathon is None:
            raise ResourceNotFoundError()
        if hackathon.organizer_id != current_user.id:
            raise ResourcePermissionError()
        return hackathon

    async def create_resource(
        self,
        hackathon_public_id: uuid.UUID,
        data: ResourceCreate,
        current_user: User,
    ) -> ResourceResponse:
        hackathon = await self._get_owned_hackathon(hackathon_public_id, current_user)
        resource = Resource(
            hackathon_id=hackathon.id,
            name=data.name.strip(),
            type=data.type,
            distribution_mode=data.distribution_mode,
            target=data.target,
            resource_metadata=data.metadata,
        )
        try:
            await self.repository.create_resource(resource)
            await self.repository.commit()
        except Exception:
            await self.repository.rollback()
            raise
        return await self._to_response(resource)

    async def import_items(
        self,
        hackathon_public_id: uuid.UUID,
        resource_public_id: uuid.UUID,
        values: list[str],
        current_user: User,
    ) -> ResourceImportResponse:
        await self._get_owned_hackathon(hackathon_public_id, current_user)
        resource = await self.repository.get_resource(hackathon_public_id, resource_public_id)
        if resource is None:
            raise ResourceNotFoundError()
        normalized_values = [value.strip() for value in values]
        if any(not value for value in normalized_values):
            raise ValueError("Resource values cannot be empty")
        items = [
            ResourceItem(resource_id=resource.id, encrypted_value=encrypt_value(value))
            for value in normalized_values
        ]
        try:
            await self.repository.create_items(items)
            await self.repository.commit()
        except Exception:
            await self.repository.rollback()
            raise
        return ResourceImportResponse(
            resource=await self._to_response(resource),
            imported_count=len(items),
        )

    async def _to_response(self, resource: Resource) -> ResourceResponse:
        return ResourceResponse(
            public_id=resource.public_id,
            name=resource.name,
            type=resource.type,
            distribution_mode=resource.distribution_mode,
            target=resource.target,
            metadata=resource.resource_metadata,
            item_count=await self.repository.count_items(resource.id),
        )
