import uuid

from sqlalchemy import and_, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.models import User
from src.hackathons.models import Hackathon


class HackathonRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _with_relationships():
        return (
            selectinload(Hackathon.organizer),
            selectinload(Hackathon.co_organizers),
        )

    async def list_active(
        self,
        upcoming: bool | None = None,
        registration_open: bool | None = None,
    ) -> list[Hackathon]:
        statement = select(Hackathon).where(Hackathon.is_deleted.is_(False))

        if upcoming is True:
            statement = statement.where(Hackathon.start_date > func.now())
        elif upcoming is False:
            statement = statement.where(Hackathon.start_date <= func.now())

        registration_is_open = and_(
            Hackathon.registration_open.is_(True),
            Hackathon.registration_opens_at <= func.now(),
            Hackathon.registration_deadline > func.now(),
        )

        if registration_open is True:
            statement = statement.where(registration_is_open)
        elif registration_open is False:
            statement = statement.where(not_(registration_is_open))

        statement = statement.options(*self._with_relationships()).order_by(
            Hackathon.created_at.desc()
        )

        result = await self.session.scalars(statement)
        return list(result.unique().all())

    async def list_managed_by_user(self, user_id: int) -> list[Hackathon]:
        statement = (
            select(Hackathon)
            .where(
                Hackathon.is_deleted.is_(False),
                or_(
                    Hackathon.organizer_id == user_id,
                    Hackathon.co_organizers.any(User.id == user_id),
                ),
            )
            .options(*self._with_relationships())
            .order_by(Hackathon.created_at.desc())
        )
        result = await self.session.scalars(statement)
        return list(result.unique().all())

    async def get_owned_by_public_id(
        self,
        public_id: uuid.UUID,
        organizer_id: int,
    ) -> Hackathon | None:
        statement = (
            select(Hackathon)
            .where(
                Hackathon.public_id == public_id,
                Hackathon.organizer_id == organizer_id,
                Hackathon.is_deleted.is_(False),
            )
            .options(*self._with_relationships())
        )
        result = await self.session.scalars(statement)
        return result.unique().one_or_none()

    async def get_active_by_public_id(
        self,
        public_id: uuid.UUID,
    ) -> Hackathon | None:
        statement = (
            select(Hackathon)
            .where(
                Hackathon.public_id == public_id,
                Hackathon.is_deleted.is_(False),
            )
            .options(*self._with_relationships())
        )
        result = await self.session.scalars(statement)
        return result.unique().one_or_none()

    async def add(self, hackathon: Hackathon) -> None:
        self.session.add(hackathon)
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh_updated_at(self, hackathon: Hackathon) -> None:
        await self.session.refresh(hackathon, attribute_names=["updated_at"])

    async def rollback(self) -> None:
        await self.session.rollback()
