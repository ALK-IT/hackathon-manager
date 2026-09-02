import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.attendance.exceptions import (
    AttendancePermissionError,
    CheckInNotAllowedError,
    InvalidCheckInTokenError,
)
from src.attendance.models import CheckIn, CheckInSession
from src.attendance.repository import AttendanceRepository
from src.attendance.schemas import CheckInRequest, SessionCreateRequest
from src.auth.models import User
from src.hackathons.access import can_manage_hackathon
from src.hackathons.exceptions import HackathonNotFoundError
from src.hackathons.repository import HackathonRepository
from src.registration.repository import RegistrationRepository


@dataclass(frozen=True)
class SessionCreateResult:
    session: CheckInSession
    token: str


class AttendanceService:
    def __init__(
        self,
        attendance_repository: AttendanceRepository,
        hackathon_repository: HackathonRepository,
        registration_repository: RegistrationRepository,
    ):
        self.attendance_repository = attendance_repository
        self.hackathon_repository = hackathon_repository
        self.registration_repository = registration_repository

    async def create_session(
        self,
        hackathon_public_id: uuid.UUID,
        user: User,
        request: SessionCreateRequest,
    ) -> SessionCreateResult:
        hackathon = await self.hackathon_repository.get_active_by_public_id(hackathon_public_id)
        if hackathon is None:
            raise HackathonNotFoundError()
        if not can_manage_hackathon(hackathon, user):
            raise AttendancePermissionError()

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        check_in_session = CheckInSession(
            hackathon=hackathon,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(minutes=request.expires_in_minutes),
            created_by_id=user.id,
        )
        try:
            await self.attendance_repository.deactivate_active_session(hackathon.id)
            await self.attendance_repository.create_session(check_in_session)
            await self.attendance_repository.commit()
        except Exception:
            await self.attendance_repository.rollback()
            raise
        return SessionCreateResult(
            session=check_in_session,
            token=token,
        )

    async def join_session(
        self,
        hackathon_public_id: uuid.UUID,
        user: User,
        request: CheckInRequest,
    ) -> CheckIn:
        hackathon = await self.hackathon_repository.get_active_by_public_id(hackathon_public_id)
        if hackathon is None:
            raise HackathonNotFoundError()
        registration = (
            await self.registration_repository.get_accepted_by_hackathon_and_user_for_update(
                hackathon.id, user.id
            )
        )
        if registration is None:
            raise CheckInNotAllowedError()
        token = request.token
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        check_in_session = await self.attendance_repository.get_valid_session_for_update(
            hackathon.id, token_hash, datetime.now(UTC)
        )
        if check_in_session is None:
            raise InvalidCheckInTokenError()
        check_in = await self.attendance_repository.get_check_in_by_registration_id(registration.id)
        if check_in:
            return check_in
        check_in = CheckIn(
            registration=registration,
            session=check_in_session,
        )
        try:
            await self.attendance_repository.join_session(check_in)
            await self.attendance_repository.commit()
        except Exception:
            await self.attendance_repository.rollback()
            raise
        return check_in
