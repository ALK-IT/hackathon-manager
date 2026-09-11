from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.notifications.repository import NotificationRepository
from src.notifications.service import NotificationService


def get_notification_service(
    session: AsyncSession = Depends(get_session),
) -> NotificationService:
    return NotificationService(NotificationRepository(session))
