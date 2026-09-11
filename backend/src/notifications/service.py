import uuid

from src.auth.models import User
from src.notifications.exceptions import NotificationNotFoundError
from src.notifications.models import Notification
from src.notifications.repository import NotificationRepository


class NotificationService:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    async def list_for_user(
        self,
        user: User,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[Notification], int]:
        notifications = await self.repository.list_for_user(
            user.id,
            limit=limit,
            offset=offset,
        )
        unread_count = await self.repository.unread_count(user.id)
        return notifications, unread_count

    async def mark_read(self, public_id: uuid.UUID, user: User) -> Notification:
        notification = await self.repository.get_for_user(public_id, user.id)
        if notification is None:
            raise NotificationNotFoundError()

        try:
            notification = await self.repository.mark_read(notification)
            await self.repository.commit()
            return notification
        except Exception:
            await self.repository.rollback()
            raise

    async def mark_all_read(self, user: User) -> int:
        try:
            updated_count = await self.repository.mark_all_read(user.id)
            await self.repository.commit()
            return updated_count
        except Exception:
            await self.repository.rollback()
            raise
