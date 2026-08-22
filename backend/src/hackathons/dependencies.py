from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User, UserRole
from src.auth.repository import UserRepository
from src.database import get_session
from src.hackathons.exceptions import AdminRequiredError
from src.hackathons.repository import HackathonRepository
from src.hackathons.service import HackathonService


def get_hackathon_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HackathonService:
    return HackathonService(
        HackathonRepository(session),
        UserRepository(session),
    )


async def get_current_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if user.role != UserRole.ADMIN:
        raise AdminRequiredError
    return user
