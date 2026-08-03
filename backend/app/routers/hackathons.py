from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import get_cache
from app.db import get_session
from app.repositories.hackathon_repository import HackathonRepository
from app.schemas import HackathonRead
from app.services.hackathon_service import HackathonService

router = APIRouter(prefix="/api/hackathons", tags=["hackathons"])


def get_hackathon_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    cache: Annotated[Redis, Depends(get_cache)],
) -> HackathonService:
    return HackathonService(HackathonRepository(session), cache)


@router.get("", response_model=list[HackathonRead])
async def list_hackathons(
    service: Annotated[HackathonService, Depends(get_hackathon_service)],
) -> list[dict]:
    return await service.list_hackathons()
