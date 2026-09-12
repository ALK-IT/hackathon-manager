import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.auth.models import User
from src.common.sqlalchemy import get_integrity_error_constraint
from src.hackathons.access import can_manage_hackathon
from src.resources.crypto import encrypt_value
from src.resources.exceptions import (
    ResourceItemNotFoundError,
    ResourceItemsInsufficientError,
    ResourceItemUnavailableError,
    ResourceNotFoundError,
    ResourcePermissionError,
    ResourceRecipientNotFoundError,
    ResourceTargetMismatchError,
)
from src.resources.models import Resource, ResourceAssignment, ResourceItem
from src.resources.repository import ResourceRepository
from src.resources.schemas import (
    ResourceAssignmentCreate,
    ResourceCreate,
)


@dataclass(frozen=True)
class ResourceImportResult:
    resource: Resource
    imported_count: int


@dataclass(frozen=True)
class ParticipantResourceAssignmentResult:
    assignments: list[ResourceAssignment]
    already_assigned_registration_public_ids: list[uuid.UUID]


RESOURCE_ITEM_ASSIGNMENT_CONSTRAINT = "uq_resource_assignment_item"


class ResourceService:
    def __init__(self, repository: ResourceRepository):
        self.repository = repository

    async def _get_owned_hackathon(self, hackathon_public_id: uuid.UUID, current_user: User):
        hackathon = await self.repository.get_hackathon(hackathon_public_id)
        if hackathon is None:
            raise ResourceNotFoundError()
        if not can_manage_hackathon(hackathon, current_user):
            raise ResourcePermissionError()
        return hackathon

    async def create_resource(
        self,
        hackathon_public_id: uuid.UUID,
        data: ResourceCreate,
        current_user: User,
    ) -> Resource:
        hackathon = await self._get_owned_hackathon(hackathon_public_id, current_user)
        resource = Resource(
            hackathon_id=hackathon.id,
            name=data.name.strip(),
            type=data.type,
            distribution_mode=data.distribution_mode,
            target=data.target,
            resource_metadata=data.metadata,
        )
        items = [
            ResourceItem(resource=resource, encrypted_value=encrypt_value(value))
            for value in data.values
        ]
        resource.item_count = len(items)
        try:
            await self.repository.create_resource(resource)
            if items:
                await self.repository.create_items(items)
            await self.repository.commit()
        except SQLAlchemyError:
            await self.repository.rollback()
            raise
        return resource

    async def list_resources(
        self,
        hackathon_public_id: uuid.UUID,
        current_user: User,
    ) -> list[Resource]:
        hackathon = await self._get_owned_hackathon(hackathon_public_id, current_user)
        return await self.repository.list_resources(hackathon.id)

    async def import_items(
        self,
        hackathon_public_id: uuid.UUID,
        resource_public_id: uuid.UUID,
        values: list[str],
        current_user: User,
    ) -> ResourceImportResult:
        await self._get_owned_hackathon(hackathon_public_id, current_user)
        resource = await self.repository.get_resource(hackathon_public_id, resource_public_id)
        if resource is None:
            raise ResourceNotFoundError()
        items = [
            ResourceItem(resource_id=resource.id, encrypted_value=encrypt_value(value))
            for value in values
        ]
        try:
            await self.repository.create_items(items)
            await self.repository.commit()
        except SQLAlchemyError:
            await self.repository.rollback()
            raise
        resource.item_count += len(items)
        return ResourceImportResult(
            resource=resource,
            imported_count=len(items),
        )

    async def list_items(
        self,
        hackathon_public_id: uuid.UUID,
        resource_public_id: uuid.UUID,
        current_user: User,
        limit: int,
        offset: int,
    ) -> list[ResourceItem]:
        await self._get_owned_hackathon(hackathon_public_id, current_user)
        resource = await self.repository.get_resource(hackathon_public_id, resource_public_id)
        if resource is None:
            raise ResourceNotFoundError()
        return await self.repository.list_items(resource.id, limit, offset)

    async def assign_item(
        self,
        hackathon_public_id: uuid.UUID,
        resource_public_id: uuid.UUID,
        data: ResourceAssignmentCreate,
        current_user: User,
    ) -> ResourceAssignment:
        hackathon = await self._get_owned_hackathon(hackathon_public_id, current_user)
        resource = await self.repository.get_resource(hackathon_public_id, resource_public_id)
        if resource is None:
            raise ResourceNotFoundError()

        item = await self.repository.get_item_for_update(
            resource.id,
            data.resource_item_public_id,
        )
        if item is None:
            raise ResourceItemNotFoundError()
        if item.is_assigned or item.is_revoked:
            raise ResourceItemUnavailableError()

        registration = None
        team = None
        if resource.target == "individual":
            if data.registration_public_id is None:
                raise ResourceTargetMismatchError()
            registration = await self.repository.get_registration(
                hackathon.id,
                data.registration_public_id,
            )
            if registration is None:
                raise ResourceRecipientNotFoundError()
        elif resource.target == "team":
            if data.team_public_id is None:
                raise ResourceTargetMismatchError()
            team = await self.repository.get_team(hackathon.id, data.team_public_id)
            if team is None:
                raise ResourceRecipientNotFoundError()
        else:
            raise ResourceTargetMismatchError()

        assignment = ResourceAssignment(
            resource_item=item,
            registration=registration,
            team=team,
            assigned_by=current_user,
        )
        item.is_assigned = True
        try:
            await self.repository.create_assignment(assignment)
            await self.repository.commit()
        except IntegrityError as error:
            await self.repository.rollback()
            if get_integrity_error_constraint(error) == RESOURCE_ITEM_ASSIGNMENT_CONSTRAINT:
                raise ResourceItemUnavailableError() from error
            raise
        except SQLAlchemyError:
            await self.repository.rollback()
            raise

        return assignment

    async def list_participant_assignments(
        self,
        hackathon_public_id: uuid.UUID,
        resource_public_id: uuid.UUID,
        current_user: User,
    ) -> list[ResourceAssignment]:
        await self._get_owned_hackathon(hackathon_public_id, current_user)
        resource = await self.repository.get_resource(hackathon_public_id, resource_public_id)
        if resource is None:
            raise ResourceNotFoundError()
        if resource.target != "individual":
            raise ResourceTargetMismatchError()
        return await self.repository.list_active_participant_assignments(resource.id)

    async def assign_participant_resources(
        self,
        hackathon_public_id: uuid.UUID,
        resource_public_id: uuid.UUID,
        registration_public_ids: list[uuid.UUID],
        current_user: User,
    ) -> ParticipantResourceAssignmentResult:
        hackathon = await self._get_owned_hackathon(hackathon_public_id, current_user)
        resource = await self.repository.get_resource(hackathon_public_id, resource_public_id)
        if resource is None:
            raise ResourceNotFoundError()
        if resource.target != "individual":
            raise ResourceTargetMismatchError()

        try:
            await self.repository.lock_resource(resource.id)
            registrations = await self.repository.get_accepted_registrations(
                hackathon.id,
                registration_public_ids,
            )
            registrations_by_public_id = {
                registration.public_id: registration for registration in registrations
            }
            if set(registrations_by_public_id) != set(registration_public_ids):
                raise ResourceRecipientNotFoundError()

            existing_assignments = await self.repository.list_active_participant_assignments(
                resource.id,
                [registration.id for registration in registrations],
            )
            already_assigned_ids = {
                assignment.registration.public_id
                for assignment in existing_assignments
                if assignment.registration is not None
            }
            pending_registrations = [
                registrations_by_public_id[public_id]
                for public_id in registration_public_ids
                if public_id not in already_assigned_ids
            ]
            items = await self.repository.get_available_items_for_update(
                resource.id,
                len(pending_registrations),
            )
            if len(items) != len(pending_registrations):
                raise ResourceItemsInsufficientError()

            assignments = []
            for registration, item in zip(pending_registrations, items, strict=True):
                item.is_assigned = True
                assignment = ResourceAssignment(
                    resource_item=item,
                    registration=registration,
                    assigned_by=current_user,
                )
                await self.repository.create_assignment(assignment)
                assignments.append(assignment)
            await self.repository.commit()
        except (ResourceRecipientNotFoundError, ResourceItemsInsufficientError):
            await self.repository.rollback()
            raise
        except IntegrityError as error:
            await self.repository.rollback()
            if get_integrity_error_constraint(error) == RESOURCE_ITEM_ASSIGNMENT_CONSTRAINT:
                raise ResourceItemUnavailableError() from error
            raise
        except SQLAlchemyError:
            await self.repository.rollback()
            raise

        return ParticipantResourceAssignmentResult(
            assignments=assignments,
            already_assigned_registration_public_ids=[
                public_id
                for public_id in registration_public_ids
                if public_id in already_assigned_ids
            ],
        )

    async def revoke_participant_resource(
        self,
        hackathon_public_id: uuid.UUID,
        resource_public_id: uuid.UUID,
        registration_public_id: uuid.UUID,
        current_user: User,
    ) -> None:
        hackathon = await self._get_owned_hackathon(hackathon_public_id, current_user)
        resource = await self.repository.get_resource(hackathon_public_id, resource_public_id)
        if resource is None:
            raise ResourceNotFoundError()
        if resource.target != "individual":
            raise ResourceTargetMismatchError()

        try:
            await self.repository.lock_resource(resource.id)
            registrations = await self.repository.get_accepted_registrations(
                hackathon.id,
                [registration_public_id],
            )
            if not registrations:
                raise ResourceRecipientNotFoundError()
            assignments = await self.repository.list_active_participant_assignments(
                resource.id,
                [registrations[0].id],
            )
            revoked_at = datetime.now(UTC)
            for assignment in assignments:
                assignment.revoked_at = revoked_at
                assignment.resource_item.is_revoked = True
            await self.repository.commit()
        except ResourceRecipientNotFoundError:
            await self.repository.rollback()
            raise
        except SQLAlchemyError:
            await self.repository.rollback()
            raise
