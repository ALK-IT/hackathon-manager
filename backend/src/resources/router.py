import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.resources.dependencies import get_resource_service
from src.resources.models import Resource, ResourceAssignment
from src.resources.schemas import (
    MyResourceHackathonResponse,
    MyResourceResponse,
    ResourceAssignmentCreate,
    ResourceAssignmentManageResponse,
    ResourceAssignmentResponse,
    ResourceCreate,
    ResourceImportResponse,
    ResourceItemResponse,
    ResourceItemsImport,
    ResourceResponse,
    ResourceRevealResponse,
)
from src.resources.service import ResourceImportResult, ResourceService

router = APIRouter(prefix="/api", tags=["resources"])


def _manage_assignment_response(assignment: ResourceAssignment) -> ResourceAssignmentManageResponse:
    item = assignment.resource_item
    return ResourceAssignmentManageResponse(
        public_id=assignment.public_id,
        assigned_at=assignment.assigned_at,
        revoked_at=assignment.revoked_at,
        resource_public_id=item.resource.public_id,
        resource_name=item.resource.name,
        resource_item_public_id=item.public_id,
        registration_public_id=(
            assignment.registration.public_id if assignment.registration else None
        ),
        team_public_id=assignment.team.public_id if assignment.team else None,
    )


@router.get("/hackathons/{hackathon_public_id}/resources", response_model=list[ResourceResponse])
async def list_resources(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
):
    return await service.list_resources(hackathon_public_id, current_user)


def _my_resource_response(assignment: ResourceAssignment) -> MyResourceResponse:
    item = assignment.resource_item
    resource = item.resource
    hackathon = resource.hackathon
    return MyResourceResponse(
        public_id=item.public_id,
        name=resource.name,
        type=resource.type,
        target=resource.target,
        metadata=resource.resource_metadata,
        is_revoked=item.is_revoked or assignment.revoked_at is not None,
        hackathon=MyResourceHackathonResponse(
            public_id=hackathon.public_id,
            name=hackathon.name,
        ),
    )


@router.get("/my-resources", response_model=list[MyResourceResponse])
async def list_my_resources(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
    hackathon_public_id: Annotated[uuid.UUID, Query(alias="hackathon")],
) -> list[MyResourceResponse]:
    assignments = await service.list_my_resources(current_user, hackathon_public_id)
    return [_my_resource_response(assignment) for assignment in assignments]


@router.post(
    "/resource-items/{resource_item_public_id}/reveal",
    response_model=ResourceRevealResponse,
)
async def reveal_resource_item(
    resource_item_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
    hackathon_public_id: Annotated[uuid.UUID, Query(alias="hackathon")],
) -> ResourceRevealResponse:
    value = await service.reveal_item(resource_item_public_id, current_user, hackathon_public_id)
    return ResourceRevealResponse(value=value)


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


@router.get(
    "/hackathons/{hackathon_public_id}/resource-assignments",
    response_model=list[ResourceAssignmentManageResponse],
)
async def list_resource_assignments(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
):
    return [
        _manage_assignment_response(item)
        for item in await service.list_assignments(hackathon_public_id, current_user)
    ]


@router.post(
    "/hackathons/{hackathon_public_id}/resource-assignments/{assignment_public_id}/revoke",
    response_model=ResourceAssignmentResponse,
)
async def revoke_resource_assignment(
    hackathon_public_id: uuid.UUID,
    assignment_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
):
    return await service.revoke_assignment(hackathon_public_id, assignment_public_id, current_user)


@router.delete(
    "/hackathons/{hackathon_public_id}/resources/{resource_public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_resource(
    hackathon_public_id: uuid.UUID,
    resource_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
):
    await service.delete_resource(hackathon_public_id, resource_public_id, current_user)
