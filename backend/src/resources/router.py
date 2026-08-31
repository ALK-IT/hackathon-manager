import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.resources.dependencies import get_resource_service
from src.resources.models import Resource, ResourceAssignment
from src.resources.schemas import (
    ResourceAssignmentCreate,
    ResourceAssignmentResponse,
    ResourceCreate,
    ResourceImportResponse,
    ResourceItemResponse,
    ResourceItemsImport,
    ResourceResponse,
)
from src.resources.service import ResourceImportResult, ResourceService

router = APIRouter(prefix="/api", tags=["resources"])


@router.post(
    "/hackathons/{hackathon_public_id}/resources",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_resource(
    hackathon_public_id: uuid.UUID,
    data: ResourceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> Resource:
    return await service.create_resource(hackathon_public_id, data, current_user)


@router.post(
    "/hackathons/{hackathon_public_id}/resources/{resource_public_id}/items",
    response_model=ResourceImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_resource_items(
    hackathon_public_id: uuid.UUID,
    resource_public_id: uuid.UUID,
    data: ResourceItemsImport,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> ResourceImportResult:
    return await service.import_items(
        hackathon_public_id,
        resource_public_id,
        data.values,
        current_user,
    )


@router.get(
    "/hackathons/{hackathon_public_id}/resources/{resource_public_id}/items",
    response_model=list[ResourceItemResponse],
)
async def list_resource_items(
    hackathon_public_id: uuid.UUID,
    resource_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ResourceItemResponse]:
    items = await service.list_items(
        hackathon_public_id,
        resource_public_id,
        current_user,
        limit,
        offset,
    )
    return [
        ResourceItemResponse(
            public_id=item.public_id,
            resource_public_id=resource_public_id,
            is_assigned=item.is_assigned,
            is_revoked=item.is_revoked,
        )
        for item in items
    ]


@router.post(
    "/hackathons/{hackathon_public_id}/resources/{resource_public_id}/assignments",
    response_model=ResourceAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_resource_item(
    hackathon_public_id: uuid.UUID,
    resource_public_id: uuid.UUID,
    data: ResourceAssignmentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> ResourceAssignment:
    return await service.assign_item(
        hackathon_public_id,
        resource_public_id,
        data,
        current_user,
    )
