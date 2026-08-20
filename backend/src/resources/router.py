import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.resources.dependencies import get_resource_service
from src.resources.schemas import (
    ResourceCreate,
    ResourceImportResponse,
    ResourceItemsImport,
    ResourceResponse,
)
from src.resources.service import ResourceService

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
) -> ResourceResponse:
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
) -> ResourceImportResponse:
    return await service.import_items(
        hackathon_public_id,
        resource_public_id,
        data.values,
        current_user,
    )
