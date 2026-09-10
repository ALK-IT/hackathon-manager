from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.hackathon_tasks.repository import TaskRepository
from src.hackathon_tasks.service import TaskService
from src.hackathons.repository import HackathonRepository
from src.registration.repository import RegistrationRepository
from src.teams.repository import TeamRepository


def get_task_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TaskService:
    return TaskService(
        TaskRepository(session),
        HackathonRepository(session),
        RegistrationRepository(session),
        TeamRepository(session),
    )
