import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.attendance.exceptions import AttendancePermissionError
from src.attendance.models import CheckInSession
from src.attendance.repository import AttendanceRepository
from src.attendance.schemas import SessionCreateRequest
from src.auth.models import User
from src.hackathons.access import can_manage_hackathon
from src.hackathons.exceptions import HackathonNotFoundError
from src.hackathons.repository import HackathonRepository


@dataclass(frozen=True)
class SessionCreateResult:
    session: CheckInSession
    token: str


class AttendanceService:
    def __init__(
        self,
        attendance_repository: AttendanceRepository,
        hackathon_repository: HackathonRepository,
    ):
        self.attendance_repository = attendance_repository
        self.hackathon_repository = hackathon_repository

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
