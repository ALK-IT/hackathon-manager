import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.registration.dependencies import get_registration_service
from src.registration.schema import RegistrationCreate, RegistrationResponse
from src.registration.service import RegistrationService

router = APIRouter(prefix="/api", tags=["teams"])


@router.post(
    "/hackathons/{hackathon_public_id}/registrations",
    status_code=status.HTTP_201_CREATED,
    response_model=RegistrationResponse,
)
async def create_registration(
    hackathon_public_id: uuid.UUID,
    data: RegistrationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[RegistrationService, Depends(get_registration_service)],
) -> RegistrationResponse:
    """Create an individual registration or create/join its team.

    The established URL remains unchanged for frontend compatibility. Team
    orchestration now has a dedicated router and OpenAPI tag.
    """
    return await service.create_registration(
        data=data,
        hackathon_public_id=hackathon_public_id,
        current_user=current_user,
    )
