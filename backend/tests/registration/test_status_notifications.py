import uuid

import pytest

from src.auth.email import EmailDeliveryError
from src.registration.models import RegistrationStatus
from src.registration.status_notifications import (
    RegistrationStatusChanged,
    RegistrationStatusChangedHandler,
)


@pytest.fixture
def notification_service(mocker):
    service = mocker.Mock()
    service.notify_status_changed = mocker.AsyncMock()
    return service


@pytest.fixture
def email_service(mocker):
    service = mocker.Mock()
    service.send_registration_status_changed = mocker.AsyncMock()
    return service


@pytest.fixture
def handler(notification_service, email_service):
    return RegistrationStatusChangedHandler(notification_service, email_service)


def make_event(status: RegistrationStatus) -> RegistrationStatusChanged:
    return RegistrationStatusChanged(
        registration_public_id=uuid.uuid4(),
        user_id=42,
        recipient_email="participant@example.com",
        hackathon_name="AI Hackathon",
        hackathon_public_id=uuid.uuid4(),
        status=status,
    )


@pytest.mark.parametrize(
    "status",
    [RegistrationStatus.ACCEPTED, RegistrationStatus.REJECTED],
)
async def test_before_commit_stages_in_app_notification(
    handler,
    notification_service,
    status,
):
    event = make_event(status)

    await handler.before_commit(event)

    notification_service.notify_status_changed.assert_awaited_once_with(
        user_id=event.user_id,
        hackathon_name=event.hackathon_name,
        hackathon_public_id=event.hackathon_public_id,
        status=status.value,
    )


@pytest.mark.parametrize(
    "status",
    [RegistrationStatus.ACCEPTED, RegistrationStatus.REJECTED],
)
async def test_after_commit_sends_email(handler, email_service, status):
    event = make_event(status)

    await handler.after_commit(event)

    email_service.send_registration_status_changed.assert_awaited_once_with(
        event.recipient_email,
        event.hackathon_name,
        str(event.hackathon_public_id),
        status.value,
    )


async def test_pending_status_is_not_sent_to_any_channel(
    handler,
    notification_service,
    email_service,
):
    event = make_event(RegistrationStatus.PENDING)

    await handler.before_commit(event)
    await handler.after_commit(event)

    notification_service.notify_status_changed.assert_not_awaited()
    email_service.send_registration_status_changed.assert_not_awaited()


async def test_email_delivery_failure_does_not_fail_status_change(handler, email_service):
    event = make_event(RegistrationStatus.ACCEPTED)
    email_service.send_registration_status_changed.side_effect = EmailDeliveryError()

    await handler.after_commit(event)

    email_service.send_registration_status_changed.assert_awaited_once()
