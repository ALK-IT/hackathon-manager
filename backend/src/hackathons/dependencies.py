from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User, UserRole
from src.auth.repository import UserRepository
from src.cache import get_cache
from src.common.rate_limit import FixedWindowRateLimiter
from src.database import get_session
from src.hackathons.constants import (
    CO_ORGANIZER_SEARCH_RATE_LIMIT,
    CO_ORGANIZER_SEARCH_RATE_LIMIT_NAMESPACE,
    CO_ORGANIZER_SEARCH_RATE_WINDOW_SECONDS,
)
from src.hackathons.exceptions import AdminRequiredError
from src.hackathons.repository import HackathonRepository
from src.hackathons.service import HackathonService


def get_hackathon_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    cache: Annotated[Redis, Depends(get_cache)],
) -> HackathonService:
    return HackathonService(
        HackathonRepository(session),
        UserRepository(session),
        FixedWindowRateLimiter(
            cache=cache,
            namespace=CO_ORGANIZER_SEARCH_RATE_LIMIT_NAMESPACE,
            limit=CO_ORGANIZER_SEARCH_RATE_LIMIT,
            window_seconds=CO_ORGANIZER_SEARCH_RATE_WINDOW_SECONDS,
        ),
    )


async def get_current_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if user.role != UserRole.ADMIN:
        raise AdminRequiredError
    return user
