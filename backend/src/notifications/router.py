import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.notifications.dependencies import get_notification_service
from src.notifications.schemas import (
    MarkAllReadResponse,
    NotificationListResponse,
    NotificationResponse,
)
from src.notifications.service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> NotificationListResponse:
    items, unread_count = await service.list_for_user(
        current_user,
        limit=limit,
        offset=offset,
    )
    return NotificationListResponse(items=items, unread_count=unread_count)


@router.patch("/{notification_public_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> NotificationResponse:
    return await service.mark_read(notification_public_id, current_user)


@router.post("/read-all", response_model=MarkAllReadResponse)
async def mark_all_notifications_read(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> MarkAllReadResponse:
    updated_count = await service.mark_all_read(current_user)
    return MarkAllReadResponse(updated_count=updated_count)
