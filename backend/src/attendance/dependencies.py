from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.attendance.repository import AttendanceRepository
from src.attendance.service import AttendanceService
from src.database import get_session
from src.hackathons.repository import HackathonRepository
from src.registration.repository import RegistrationRepository


def get_attendance_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AttendanceService:
    return AttendanceService(
        AttendanceRepository(session),
        HackathonRepository(session),
        RegistrationRepository(session),
    )
