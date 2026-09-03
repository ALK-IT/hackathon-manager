import uuid

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload, selectinload, with_expression

from src.hackathons.models import Hackathon
from src.registration.models import Registration, RegistrationStatus
from src.resources.models import Resource, ResourceAssignment, ResourceAuditLog, ResourceItem
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

    async def get_team(self, hackathon_id: int, team_public_id: uuid.UUID) -> Team | None:
        return await self.session.scalar(
            select(Team).where(
                Team.hackathon_id == hackathon_id,
                Team.public_id == team_public_id,
            )
        )

    @staticmethod
    def _is_assigned_to_user(user_id: int):
        individual_registration = aliased(Registration)
        team_registration = aliased(Registration)
        return or_(
            exists(
                select(individual_registration.id).where(
                    individual_registration.id == ResourceAssignment.registration_id,
                    individual_registration.user_id == user_id,
                    individual_registration.status == RegistrationStatus.ACCEPTED,
                    individual_registration.hackathon_id == Resource.hackathon_id,
                )
            ),
            exists(
                select(team_registration.id).where(
                    team_registration.team_id == ResourceAssignment.team_id,
                    team_registration.user_id == user_id,
                    team_registration.status == RegistrationStatus.ACCEPTED,
                    team_registration.hackathon_id == Resource.hackathon_id,
                )
            ),
        )

    @staticmethod
    def _with_resource_context():
        return (
            joinedload(ResourceAssignment.resource_item)
            .joinedload(ResourceItem.resource)
            .joinedload(Resource.hackathon)
        )

    async def list_assignments_for_user(self, user_id: int) -> list[ResourceAssignment]:
        result = await self.session.scalars(
            select(ResourceAssignment)
            .join(ResourceAssignment.resource_item)
            .join(ResourceItem.resource)
            .join(Resource.hackathon)
            .options(self._with_resource_context())
            .where(
                Hackathon.is_deleted.is_(False),
                self._is_assigned_to_user(user_id),
            )
            .order_by(ResourceAssignment.assigned_at, ResourceAssignment.id)
        )
        return list(result.all())

    async def get_assignment_for_user(
        self,
        item_public_id: uuid.UUID,
        user_id: int,
    ) -> ResourceAssignment | None:
        return await self.session.scalar(
            select(ResourceAssignment)
            .join(ResourceAssignment.resource_item)
            .join(ResourceItem.resource)
            .join(Resource.hackathon)
            .options(self._with_resource_context())
            .where(
                ResourceItem.public_id == item_public_id,
                Hackathon.is_deleted.is_(False),
                self._is_assigned_to_user(user_id),
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

    async def create_audit_log(self, audit_log: ResourceAuditLog) -> ResourceAuditLog:
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
