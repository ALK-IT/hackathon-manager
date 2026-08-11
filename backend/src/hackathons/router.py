from typing import Annotated

from fastapi import APIRouter, Depends

from src.hackathons.dependencies import get_hackathon_service
from src.hackathons.schemas import HackathonRead
from src.hackathons.service import HackathonService

router = APIRouter(prefix="/api/hackathons", tags=["hackathons"])


@router.get("", response_model=list[HackathonRead])
async def list_hackathons(
    service: Annotated[HackathonService, Depends(get_hackathon_service)],
) -> list[dict]:
    return await service.list_hackathons()
