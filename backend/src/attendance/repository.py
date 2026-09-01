from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.attendance.models import CheckInSession


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

    async def create_session(self, check_in_session: CheckInSession) -> CheckInSession:
        self.session.add(check_in_session)
        await self.session.flush()
        return check_in_session

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

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
