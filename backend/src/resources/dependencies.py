from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.resources.repository import ResourceRepository
from src.resources.service import ResourceService


def get_resource_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResourceService:
    return ResourceService(ResourceRepository(session))
