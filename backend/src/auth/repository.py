import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: uuid.UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.public_id == public_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        statement = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.scalars(statement)
        return list(result.all())

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def update(self, user: User) -> User:
        await self.session.flush()
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()
