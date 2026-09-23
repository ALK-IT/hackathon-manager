import logging
import uuid
from dataclasses import dataclass
from typing import ClassVar

from src.auth.email import EmailDeliveryError, EmailService
from src.notifications.service import NotificationService
from src.registration.models import RegistrationStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegistrationStatusChanged:
    registration_public_id: uuid.UUID
    user_id: int
    recipient_email: str
    hackathon_name: str
    hackathon_public_id: uuid.UUID
    status: RegistrationStatus


class RegistrationStatusChangedHandler:
    """Coordinate every participant-facing channel for a status change."""

    _NOTIFIABLE_STATUSES: ClassVar[frozenset[RegistrationStatus]] = frozenset(
        {RegistrationStatus.ACCEPTED, RegistrationStatus.REJECTED}
    )

    def __init__(
        self,
        notification_service: NotificationService,
        email_service: EmailService,
    ) -> None:
        self.notification_service = notification_service
        self.email_service = email_service

    async def before_commit(self, event: RegistrationStatusChanged) -> None:
        """Stage transactional notification channels before committing the status change."""
        if event.status not in self._NOTIFIABLE_STATUSES:
            return

        await self.notification_service.notify_status_changed(
            user_id=event.user_id,
            hackathon_name=event.hackathon_name,
            hackathon_public_id=event.hackathon_public_id,
            status=event.status.value,
        )

    async def after_commit(self, event: RegistrationStatusChanged) -> None:
        """Deliver external channels after the status change is durable."""
        if event.status not in self._NOTIFIABLE_STATUSES:
            return

        try:
            await self.email_service.send_registration_status_changed(
                event.recipient_email,
                event.hackathon_name,
                str(event.hackathon_public_id),
                event.status.value,
            )
        except EmailDeliveryError:
            logger.warning(
                "Registration status email delivery failed",
                extra={"registration_public_id": str(event.registration_public_id)},
                exc_info=True,
            )
