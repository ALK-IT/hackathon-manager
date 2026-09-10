from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.hackathons.repository import HackathonRepository
from src.teams.repository import TeamRepository
from src.teams.service import TeamService


def get_teams_service(session: Annotated[AsyncSession, Depends(get_session)]) -> TeamService:
    return TeamService(TeamRepository(session), HackathonRepository(session))
