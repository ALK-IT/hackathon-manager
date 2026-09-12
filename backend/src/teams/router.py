import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.registration.dependencies import get_registration_service
from src.registration.schema import RegistrationCreate, RegistrationResponse
from src.registration.service import RegistrationService
from src.teams.dependencies import get_teams_service
from src.teams.schemas import TeamDetailResponse
from src.teams.service import TeamService

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


@router.get(
    "/hackathons/{hackathon_public_id}/teams",
    response_model=list[TeamDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_teams(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TeamService, Depends(get_teams_service)],
) -> list[TeamDetailResponse]:
    result = await service.get_all_teams(hackathon_public_id, current_user)
    return [TeamDetailResponse.from_team(team) for team in result]
