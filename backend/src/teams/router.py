import uuid
from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from starlette import status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.teams.dependencies import get_teams_service
from src.teams.schemas import TeamDetailResponse
from src.teams.service import TeamService

router = APIRouter(
    prefix="/api",
    tags=["teams"],
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
