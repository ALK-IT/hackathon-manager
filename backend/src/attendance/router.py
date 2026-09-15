import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.attendance.dependencies import get_attendance_service
from src.attendance.schemas import (
    AttendanceParticipantListResponse,
    AttendanceParticipantResponse,
    CheckInListItemResponse,
    CheckInListResponse,
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
    result = await service.create_check_in_session(hackathon_public_id, current_user, data)
    return SessionCreateResponse(
        public_id=result.session.public_id,
        token=result.token,
        expires_at=result.session.expires_at,
        is_active=result.session.is_active,
    )


@router.get(
    "/hackathons/{hackathon_public_id}/check-ins",
    response_model=CheckInListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_check_ins(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CheckInListResponse:
    check_ins, total = await service.list_check_ins(
        hackathon_public_id,
        current_user,
        limit=limit,
        offset=offset,
    )
    return CheckInListResponse(
        items=[CheckInListItemResponse.from_check_in(check_in) for check_in in check_ins],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/hackathons/{hackathon_public_id}/attendance",
    response_model=AttendanceParticipantListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_attendance(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AttendanceParticipantListResponse:
    registrations, total = await service.list_attendance(
        hackathon_public_id,
        current_user,
        limit=limit,
        offset=offset,
    )
    return AttendanceParticipantListResponse(
        items=[
            AttendanceParticipantResponse.from_registration(registration)
            for registration in registrations
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.put(
    "/hackathons/{hackathon_public_id}/check-ins/me",
    response_model=CheckInResponse,
    status_code=status.HTTP_200_OK,
)
async def check_in_current_user(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
    data: CheckInRequest,
) -> CheckInResponse:
    result = await service.check_in_current_user(hackathon_public_id, current_user, data)
    return CheckInResponse(
        public_id=result.public_id,
        checked_in_at=result.checked_in_at,
    )
