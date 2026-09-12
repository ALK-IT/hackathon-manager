import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.resources.dependencies import get_resource_service
from src.resources.models import Resource, ResourceAssignment
from src.resources.schemas import (
    ParticipantResourceAssignmentResponse,
    ParticipantResourceAssignmentsCreate,
    ParticipantResourceAssignmentsResponse,
    ResourceAssignmentCreate,
    ResourceAssignmentResponse,
    ResourceCreate,
    ResourceImportResponse,
    ResourceInventoryResponse,
    ResourceItemResponse,
    ResourceItemsImport,
    ResourceResponse,
)
from src.resources.service import (
    ParticipantResourceAssignmentResult,
    ResourceImportResult,
    ResourceService,
)

router = APIRouter(prefix="/api", tags=["resources"])


def _participant_assignment_response(
    assignment: ResourceAssignment,
) -> ParticipantResourceAssignmentResponse:
    if assignment.registration is None:
        raise ValueError("Participant assignment must have a registration")
    return ParticipantResourceAssignmentResponse(
        public_id=assignment.public_id,
        registration_public_id=assignment.registration.public_id,
        assigned_at=assignment.assigned_at,
        revoked_at=assignment.revoked_at,
    )


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


@router.get(
    "/hackathons/{hackathon_public_id}/resources",
    response_model=list[ResourceInventoryResponse],
)
async def list_resources(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> list[Resource]:
    return await service.list_resources(hackathon_public_id, current_user)


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
    "/hackathons/{hackathon_public_id}/resources/{resource_public_id}/participant-assignments",
    response_model=list[ParticipantResourceAssignmentResponse],
)
async def list_participant_resource_assignments(
    hackathon_public_id: uuid.UUID,
    resource_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> list[ParticipantResourceAssignmentResponse]:
    assignments = await service.list_participant_assignments(
        hackathon_public_id,
        resource_public_id,
        current_user,
    )
    return [_participant_assignment_response(assignment) for assignment in assignments]


@router.post(
    "/hackathons/{hackathon_public_id}/resources/{resource_public_id}/participant-assignments",
    response_model=ParticipantResourceAssignmentsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_participant_resources(
    hackathon_public_id: uuid.UUID,
    resource_public_id: uuid.UUID,
    data: ParticipantResourceAssignmentsCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> ParticipantResourceAssignmentsResponse:
    result: ParticipantResourceAssignmentResult = await service.assign_participant_resources(
        hackathon_public_id,
        resource_public_id,
        data.registration_public_ids,
        current_user,
    )
    return ParticipantResourceAssignmentsResponse(
        assignments=[
            _participant_assignment_response(assignment) for assignment in result.assignments
        ],
        already_assigned_registration_public_ids=(result.already_assigned_registration_public_ids),
    )


@router.delete(
    "/hackathons/{hackathon_public_id}/resources/{resource_public_id}/participant-assignments/"
    "{registration_public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_participant_resource(
    hackathon_public_id: uuid.UUID,
    resource_public_id: uuid.UUID,
    registration_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> Response:
    await service.revoke_participant_resource(
        hackathon_public_id,
        resource_public_id,
        registration_public_id,
        current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
