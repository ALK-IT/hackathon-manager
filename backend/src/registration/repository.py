import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.models import User
from src.hackathons.models import Hackathon
from src.registration.models import (
    Registration,
    RegistrationAnswer,
    RegistrationQuestion,
    RegistrationStatus,
)


class RegistrationQuestionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_hackathon_public_id(
        self,
        hackathon_public_id: uuid.UUID,
    ) -> list[RegistrationQuestion]:
        result = await self.session.execute(
            select(RegistrationQuestion)
            .join(RegistrationQuestion.hackathon)
            .where(Hackathon.public_id == hackathon_public_id)
            .order_by(RegistrationQuestion.id)
        )
        return list(result.scalars().all())

    async def get_by_public_id(
        self,
        question_public_id: uuid.UUID,
    ) -> RegistrationQuestion | None:
        result = await self.session.execute(
            select(RegistrationQuestion)
            .join(RegistrationQuestion.hackathon)
            .where(
                RegistrationQuestion.public_id == question_public_id,
                Hackathon.is_deleted.is_(False),
            )
            .options(
                selectinload(RegistrationQuestion.hackathon).selectinload(Hackathon.co_organizers)
            )
        )

        return result.scalar_one_or_none()

    async def create_many(
        self, questions: list[RegistrationQuestion]
    ) -> list[RegistrationQuestion]:
        self.session.add_all(questions)
        await self.session.flush()

        return questions

    async def create(
        self,
        question: RegistrationQuestion,
    ) -> RegistrationQuestion:
        self.session.add(question)
        await self.session.flush()
        return question

    async def delete(
        self,
        question: RegistrationQuestion,
    ) -> None:
        await self.session.delete(question)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


class RegistrationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_hackathon(
        self,
        hackathon_public_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> list[Registration]:
        result = await self.session.execute(
            select(Registration)
            .join(Registration.hackathon)
            .where(Hackathon.public_id == hackathon_public_id)
            .options(
                selectinload(Registration.hackathon).selectinload(Hackathon.co_organizers),
                selectinload(Registration.user),
                selectinload(Registration.status_changed_by),
                selectinload(Registration.answers).selectinload(RegistrationAnswer.question),
            )
            .order_by(Registration.id)
            .limit(limit)
            .offset(offset)
        )

        return list(result.scalars().all())

    async def get_by_hackathon_and_user(
        self, hackathon_public_id: uuid.UUID, user_public_id: uuid.UUID
    ) -> Registration | None:

        result = await self.session.execute(
            select(Registration)
            .join(Registration.hackathon)
            .join(Registration.user)
            .where(
                Hackathon.public_id == hackathon_public_id,
                Hackathon.is_deleted.is_(False),
                User.public_id == user_public_id,
            )
            .options(
                selectinload(Registration.hackathon).selectinload(Hackathon.co_organizers),
                selectinload(Registration.user),
                selectinload(Registration.status_changed_by),
                selectinload(Registration.answers).selectinload(RegistrationAnswer.question),
            )
        )

        return result.scalar_one_or_none()

    async def get_active_by_public_id(
        self,
        registration_public_id: uuid.UUID,
    ) -> Registration | None:
        result = await self.session.execute(
            select(Registration)
            .join(Registration.hackathon)
            .where(
                Registration.public_id == registration_public_id,
                Hackathon.is_deleted.is_(False),
            )
            .options(
                selectinload(Registration.hackathon).selectinload(Hackathon.co_organizers),
                selectinload(Registration.status_changed_by),
            )
        )

        return result.scalar_one_or_none()

    async def update_status(
        self,
        registration: Registration,
        new_status: RegistrationStatus,
        changed_by: User,
    ) -> Registration:
        registration.status = new_status
        registration.status_changed_at = datetime.now(UTC)
        registration.status_changed_by = changed_by
        await self.session.flush()
        return registration

    async def create(self, registration: Registration) -> Registration:
        self.session.add(registration)
        await self.session.flush()
        return registration

    async def delete(self, registration: Registration) -> None:
        await self.session.delete(registration)
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
