from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.cache import get_cache
from src.database import get_session
from src.hackathons.repository import HackathonRepository
from src.hackathons.service import HackathonService


def get_hackathon_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    cache: Annotated[Redis, Depends(get_cache)],
) -> HackathonService:
    return HackathonService(HackathonRepository(session), cache)
