from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.attendance.models import CheckIn, CheckInSession
from src.registration.models import Registration, RegistrationStatus


class AttendanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def deactivate_active_session(self, hackathon_id: int) -> None:
        statement = (
            update(CheckInSession)
            .where(CheckInSession.hackathon_id == hackathon_id, CheckInSession.is_active.is_(True))
            .values(is_active=False)
        )
        await self.session.execute(statement)

    async def create_check_in_session(self, check_in_session: CheckInSession) -> CheckInSession:
        self.session.add(check_in_session)
        await self.session.flush()
        return check_in_session

    async def create_check_in(self, check_in: CheckIn) -> CheckIn:
        self.session.add(check_in)
        await self.session.flush()
        return check_in

    async def get_valid_session_for_update(
        self, hackathon_id: int, token_hash: str, checked_at: datetime
    ) -> CheckInSession | None:
        statement = (
            select(CheckInSession)
            .where(
                CheckInSession.hackathon_id == hackathon_id,
                CheckInSession.token_hash == token_hash,
                CheckInSession.is_active.is_(True),
                CheckInSession.expires_at > checked_at,
            )
            .with_for_update()
        )
        return await self.session.scalar(statement)

    async def get_check_in_by_registration_id(self, registration_id: int) -> CheckIn | None:
        statement = select(CheckIn).where(CheckIn.registration_id == registration_id)
        return await self.session.scalar(statement)

    async def get_check_ins_by_hackathon(
        self,
        hackathon_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CheckIn], int]:
        total = await self.session.scalar(
            select(func.count(CheckIn.id))
            .join(CheckIn.registration)
            .where(Registration.hackathon_id == hackathon_id)
        )
        statement = (
            select(CheckIn)
            .join(CheckIn.registration)
            .where(Registration.hackathon_id == hackathon_id)
            .options(selectinload(CheckIn.registration).selectinload(Registration.user))
            .order_by(CheckIn.checked_in_at, CheckIn.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(statement)
        return list(result.all()), int(total or 0)

    async def get_accepted_registrations_with_attendance(
        self,
        hackathon_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Registration], int]:
        filters = (
            Registration.hackathon_id == hackathon_id,
            Registration.status == RegistrationStatus.ACCEPTED,
        )
        total = await self.session.scalar(select(func.count(Registration.id)).where(*filters))
        statement = (
            select(Registration)
            .where(*filters)
            .options(
                selectinload(Registration.user),
                selectinload(Registration.team),
                selectinload(Registration.check_in),
            )
            .order_by(Registration.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(statement)
        return list(result.all()), int(total or 0)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
