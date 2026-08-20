import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.hackathons.models import Hackathon
from src.resources.models import Resource, ResourceItem


class ResourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_hackathon(self, public_id: uuid.UUID) -> Hackathon | None:
        return await self.session.scalar(
            select(Hackathon).where(
                Hackathon.public_id == public_id,
                Hackathon.is_deleted.is_(False),
            )
        )

    async def get_resource(
        self, hackathon_public_id: uuid.UUID, resource_public_id: uuid.UUID
    ) -> Resource | None:
        result = await self.session.execute(
            select(Resource)
            .join(Resource.hackathon)
            .where(
                Hackathon.public_id == hackathon_public_id,
                Hackathon.is_deleted.is_(False),
                Resource.public_id == resource_public_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_items(self, resource_id: int) -> int:
        return int(
            await self.session.scalar(
                select(func.count(ResourceItem.id)).where(ResourceItem.resource_id == resource_id)
            )
            or 0
        )

    async def create_resource(self, resource: Resource) -> Resource:
        self.session.add(resource)
        await self.session.flush()
        return resource

    async def create_items(self, items: list[ResourceItem]) -> list[ResourceItem]:
        self.session.add_all(items)
        await self.session.flush()
        return items

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
