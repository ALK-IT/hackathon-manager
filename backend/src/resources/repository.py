import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload, with_expression

from src.hackathons.models import Hackathon
from src.registration.models import Registration, RegistrationStatus
from src.resources.models import Resource, ResourceAssignment, ResourceItem
from src.teams.models import Team


class ResourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_hackathon(self, public_id: uuid.UUID) -> Hackathon | None:
        return await self.session.scalar(
            select(Hackathon)
            .options(selectinload(Hackathon.co_organizers))
            .where(
                Hackathon.public_id == public_id,
                Hackathon.is_deleted.is_(False),
            )
        )

    async def get_resource(
        self, hackathon_public_id: uuid.UUID, resource_public_id: uuid.UUID
    ) -> Resource | None:
        item_count = (
            select(func.count(ResourceItem.id))
            .where(ResourceItem.resource_id == Resource.id)
            .correlate(Resource)
            .scalar_subquery()
        )
        result = await self.session.execute(
            select(Resource)
            .options(with_expression(Resource.item_count, item_count))
            .join(Resource.hackathon)
            .where(
                Hackathon.public_id == hackathon_public_id,
                Hackathon.is_deleted.is_(False),
                Resource.public_id == resource_public_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_resources(self, hackathon_id: int) -> list[Resource]:
        item_count = (
            select(func.count(ResourceItem.id))
            .where(ResourceItem.resource_id == Resource.id)
            .correlate(Resource)
            .scalar_subquery()
        )
        available_item_count = (
            select(func.count(ResourceItem.id))
            .where(
                ResourceItem.resource_id == Resource.id,
                ResourceItem.is_assigned.is_(False),
                ResourceItem.is_revoked.is_(False),
            )
            .correlate(Resource)
            .scalar_subquery()
        )
        result = await self.session.scalars(
            select(Resource)
            .options(
                with_expression(Resource.item_count, item_count),
                with_expression(Resource.available_item_count, available_item_count),
            )
            .where(Resource.hackathon_id == hackathon_id)
            .order_by(Resource.created_at, Resource.id)
        )
        return list(result.all())

    async def lock_resource(self, resource_id: int) -> None:
        await self.session.scalar(
            select(Resource.id).where(Resource.id == resource_id).with_for_update()
        )

    async def get_item_for_update(
        self,
        resource_id: int,
        item_public_id: uuid.UUID,
    ) -> ResourceItem | None:
        return await self.session.scalar(
            select(ResourceItem)
            .where(
                ResourceItem.resource_id == resource_id,
                ResourceItem.public_id == item_public_id,
            )
            .with_for_update()
        )

    async def list_items(
        self,
        resource_id: int,
        limit: int,
        offset: int,
    ) -> list[ResourceItem]:
        result = await self.session.scalars(
            select(ResourceItem)
            .where(ResourceItem.resource_id == resource_id)
            .order_by(ResourceItem.created_at, ResourceItem.id)
            .limit(limit)
            .offset(offset)
        )
        return list(result.all())

    async def get_registration(
        self,
        hackathon_id: int,
        registration_public_id: uuid.UUID,
    ) -> Registration | None:
        return await self.session.scalar(
            select(Registration).where(
                Registration.hackathon_id == hackathon_id,
                Registration.public_id == registration_public_id,
                Registration.status == RegistrationStatus.ACCEPTED,
            )
        )

    async def get_accepted_registrations(
        self,
        hackathon_id: int,
        registration_public_ids: list[uuid.UUID],
    ) -> list[Registration]:
        result = await self.session.scalars(
            select(Registration).where(
                Registration.hackathon_id == hackathon_id,
                Registration.public_id.in_(registration_public_ids),
                Registration.status == RegistrationStatus.ACCEPTED,
            )
        )
        return list(result.all())

    async def list_active_participant_assignments(
        self,
        resource_id: int,
        registration_ids: list[int] | None = None,
    ) -> list[ResourceAssignment]:
        statement = (
            select(ResourceAssignment)
            .join(ResourceAssignment.resource_item)
            .options(
                joinedload(ResourceAssignment.registration),
                joinedload(ResourceAssignment.resource_item),
            )
            .where(
                ResourceItem.resource_id == resource_id,
                ResourceAssignment.registration_id.is_not(None),
                ResourceAssignment.revoked_at.is_(None),
            )
            .order_by(ResourceAssignment.assigned_at, ResourceAssignment.id)
        )
        if registration_ids is not None:
            statement = statement.where(ResourceAssignment.registration_id.in_(registration_ids))
        result = await self.session.scalars(statement)
        return list(result.unique().all())

    async def get_available_items_for_update(
        self,
        resource_id: int,
        limit: int,
    ) -> list[ResourceItem]:
        result = await self.session.scalars(
            select(ResourceItem)
            .where(
                ResourceItem.resource_id == resource_id,
                ResourceItem.is_assigned.is_(False),
                ResourceItem.is_revoked.is_(False),
            )
            .order_by(ResourceItem.created_at, ResourceItem.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(result.all())

    async def get_team(self, hackathon_id: int, team_public_id: uuid.UUID) -> Team | None:
        return await self.session.scalar(
            select(Team).where(
                Team.hackathon_id == hackathon_id,
                Team.public_id == team_public_id,
            )
        )

    async def create_resource(self, resource: Resource) -> Resource:
        self.session.add(resource)
        await self.session.flush()
        return resource

    async def create_items(self, items: list[ResourceItem]) -> list[ResourceItem]:
        self.session.add_all(items)
        await self.session.flush()
        return items

    async def create_assignment(
        self,
        assignment: ResourceAssignment,
    ) -> ResourceAssignment:
        self.session.add(assignment)
        await self.session.flush()
        return assignment

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
