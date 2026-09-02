import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.attendance.dependencies import get_attendance_service
from src.attendance.schemas import (
    CheckInRequest,
    CheckInResponse,
    SessionCreateRequest,
    SessionCreateResponse,
)
from src.attendance.service import AttendanceService
from src.auth.dependencies import get_current_user
from src.auth.models import User

router = APIRouter(prefix="/api", tags=["attendance"])


@router.post(
    "/hackathons/{hackathon_public_id}/check-in-sessions",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_check_in_session(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
    data: SessionCreateRequest,
):
    result = await service.create_session(hackathon_public_id, current_user, data)
    return SessionCreateResponse(
        public_id=result.session.public_id,
        token=result.token,
        expires_at=result.session.expires_at,
        is_active=result.session.is_active,
    )


@router.put(
    "/hackathons/{hackathon_public_id}/check-ins/me",
    response_model=CheckInResponse,
    status_code=status.HTTP_200_OK,
)
async def update_check_in_session(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
    data: CheckInRequest,
) -> CheckInResponse:
    result = await service.join_session(hackathon_public_id, current_user, data)
    return CheckInResponse(
        public_id=result.public_id,
        checked_in_at=result.checked_in_at,
    )
