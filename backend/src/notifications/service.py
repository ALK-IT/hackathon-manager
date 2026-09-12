import uuid

from src.auth.models import User
from src.notifications.exceptions import NotificationNotFoundError
from src.notifications.models import Notification
from src.notifications.repository import NotificationRepository

STATUS_CHANGED_KIND = "registration_status_changed"


class NotificationService:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    async def notify_status_changed(
        self,
        *,
        user_id: int,
        hackathon_name: str,
        hackathon_public_id: uuid.UUID,
        status: str,
    ) -> Notification:
        """Stage a status notification in the caller's transaction."""
        status_copy = {
            "accepted": (
                "Zgłoszenie zaakceptowane",
                f"Twoje zgłoszenie na {hackathon_name} zostało zaakceptowane.",
            ),
            "rejected": (
                "Zgłoszenie odrzucone",
                f"Twoje zgłoszenie na {hackathon_name} zostało odrzucone.",
            ),
        }
        title, message = status_copy[status]
        notification = Notification(
            user_id=user_id,
            kind=STATUS_CHANGED_KIND,
            title=title,
            message=message,
            target_url=f"/hackathons/{hackathon_public_id}",
        )
        self.repository.add(notification)
        return notification

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
