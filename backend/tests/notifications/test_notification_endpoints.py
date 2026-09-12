from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.notifications.models import Notification
from tests.conftest import ForceAuthenticate


def make_user(email: str) -> User:
    return User(name=email.split("@", 1)[0], email=email, password_hash="hashed-password")


async def test_list_returns_only_authenticated_users_notifications(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    owner = make_user("owner@example.com")
    other_user = make_user("other@example.com")
    session.add_all([owner, other_user])
    await session.flush()
    session.add_all(
        [
            Notification(user_id=owner.id, kind="test", title="Owner", message="Private"),
            Notification(user_id=other_user.id, kind="test", title="Other", message="Visible"),
        ]
    )
    await session.commit()
    force_authenticate(other_user)

    response = await api_client.get("/api/notifications")

    assert response.status_code == 200
    body = response.json()
    assert [item["title"] for item in body["items"]] == ["Other"]
    assert body["unread_count"] == 1
    assert "id" not in body["items"][0]
    assert "user_id" not in body["items"][0]


async def test_user_cannot_mark_another_users_notification_read(
    api_client: AsyncClient,
    session: AsyncSession,
    force_authenticate: ForceAuthenticate,
):
    owner = make_user("owner@example.com")
    other_user = make_user("other@example.com")
    session.add_all([owner, other_user])
    await session.flush()
    notification = Notification(
        user_id=owner.id,
        kind="test",
        title="Owner only",
        message="Private",
    )
    session.add(notification)
    await session.commit()
    force_authenticate(other_user)

    response = await api_client.patch(f"/api/notifications/{notification.public_id}/read")

    assert response.status_code == 404
    assert response.json()["error_code"] == "NOTIFICATION_NOT_FOUND"
    await session.refresh(notification)
    assert notification.read_at is None
