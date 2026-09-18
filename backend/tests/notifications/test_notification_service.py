import uuid
from types import SimpleNamespace

import pytest

from src.notifications.exceptions import NotificationNotFoundError
from src.notifications.service import STATUS_CHANGED_KIND, NotificationService


@pytest.fixture
def repository(mocker):
    repository = mocker.Mock()
    repository.add = mocker.Mock()
    repository.get_for_user = mocker.AsyncMock()
    repository.mark_read = mocker.AsyncMock()
    repository.mark_all_read = mocker.AsyncMock()
    repository.commit = mocker.AsyncMock()
    repository.rollback = mocker.AsyncMock()
    return repository


@pytest.mark.parametrize(
    ("status", "expected_title", "expected_verb"),
    [
        ("accepted", "Zgłoszenie zaakceptowane", "zaakceptowane"),
        ("rejected", "Zgłoszenie odrzucone", "odrzucone"),
    ],
)
async def test_notify_status_changed_stages_notification_without_committing(
    repository,
    status,
    expected_title,
    expected_verb,
):
    service = NotificationService(repository)
    hackathon_public_id = uuid.uuid4()

    notification = await service.notify_status_changed(
        user_id=42,
        hackathon_name="Hack the Future",
        hackathon_public_id=hackathon_public_id,
        status=status,
    )

    assert notification.user_id == 42
    assert notification.kind == STATUS_CHANGED_KIND
    assert notification.title == expected_title
    assert f"Hack the Future zostało {expected_verb}" in notification.message
    assert notification.target_url == f"/hackathons/{hackathon_public_id}"
    repository.add.assert_called_once_with(notification)
    repository.commit.assert_not_awaited()


async def test_mark_read_scopes_lookup_to_authenticated_user(repository):
    service = NotificationService(repository)
    notification_public_id = uuid.uuid4()
    current_user = SimpleNamespace(id=17)
    repository.get_for_user.return_value = None

    with pytest.raises(NotificationNotFoundError):
        await service.mark_read(notification_public_id, current_user)

    repository.get_for_user.assert_awaited_once_with(notification_public_id, 17)
    repository.mark_read.assert_not_awaited()
    repository.commit.assert_not_awaited()
