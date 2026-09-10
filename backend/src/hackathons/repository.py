import uuid

from sqlalchemy import and_, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.models import User
from src.hackathons.models import Hackathon
from src.registration.models import Registration, RegistrationStatus


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
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Hackathon], int]:
        filters = [Hackathon.is_deleted.is_(False)]

        if upcoming is True:
            filters.append(Hackathon.start_date > func.now())
        elif upcoming is False:
            filters.append(Hackathon.start_date <= func.now())

        registration_is_open = and_(
            Hackathon.registration_open.is_(True),
            Hackathon.registration_opens_at <= func.now(),
            Hackathon.registration_deadline > func.now(),
        )

        if registration_open is True:
            filters.append(registration_is_open)
        elif registration_open is False:
            filters.append(not_(registration_is_open))

        total = await self.session.scalar(select(func.count(Hackathon.id)).where(*filters))
        statement = (
            select(Hackathon)
            .where(*filters)
            .options(*self._with_relationships())
            .order_by(Hackathon.created_at.desc(), Hackathon.id.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.scalars(statement)
        return list(result.unique().all()), int(total or 0)

    async def list_active_with_registration_status(
        self,
        user_id: int,
        upcoming: bool | None = None,
        registration_open: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[Hackathon, RegistrationStatus | None]], int]:
        filters = [Hackathon.is_deleted.is_(False)]

        if upcoming is True:
            filters.append(Hackathon.start_date > func.now())
        elif upcoming is False:
            filters.append(Hackathon.start_date <= func.now())

        registration_is_open = and_(
            Hackathon.registration_open.is_(True),
            Hackathon.registration_opens_at <= func.now(),
            Hackathon.registration_deadline > func.now(),
        )
        if registration_open is True:
            filters.append(registration_is_open)
        elif registration_open is False:
            filters.append(not_(registration_is_open))

        total = await self.session.scalar(select(func.count(Hackathon.id)).where(*filters))
        statement = (
            select(Hackathon, Registration.status)
            .outerjoin(
                Registration,
                and_(Registration.hackathon_id == Hackathon.id, Registration.user_id == user_id),
            )
            .where(*filters)
            .options(*self._with_relationships())
            .order_by(Hackathon.created_at.desc(), Hackathon.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.unique().tuples().all()), int(total or 0)

    async def list_managed_by_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Hackathon], int]:
        filters = (
            Hackathon.is_deleted.is_(False),
            or_(
                Hackathon.organizer_id == user_id,
                Hackathon.co_organizers.any(User.id == user_id),
            ),
        )
        total = await self.session.scalar(select(func.count(Hackathon.id)).where(*filters))
        statement = (
            select(Hackathon)
            .where(*filters)
            .options(*self._with_relationships())
            .order_by(Hackathon.created_at.desc(), Hackathon.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(statement)
        return list(result.unique().all()), int(total or 0)

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

    async def get_active_by_public_id_for_update(
        self,
        public_id: uuid.UUID,
    ) -> Hackathon | None:
        statement = (
            select(Hackathon)
            .where(
                Hackathon.public_id == public_id,
                Hackathon.is_deleted.is_(False),
            )
            .with_for_update()
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
