import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.auth.models import User, UserRole
from src.auth.repository import UserRepository
from src.common.sqlalchemy import get_integrity_error_constraint
from src.hackathons.exceptions import (
    AdminRequiredError,
    CoOrganizerAlreadyAssignedError,
    CoOrganizerUserNotFoundError,
    HackathonNotFoundError,
    InvalidConfirmNameError,
    InvalidDateRangeError,
    InvalidRegistrationDeadlineError,
    InvalidRegistrationWindowError,
    InvalidTeamSizeError,
    OrganizerCannotBeCoOrganizerError,
    RegistrationAlreadyClosedError,
    RegistrationAlreadyOpenError,
    RegistrationDeadlinePassedError,
)
from src.hackathons.models import Hackathon
from src.hackathons.repository import HackathonRepository
from src.hackathons.schemas import CoOrganizerAddRequest, HackathonCreate, HackathonUpdate


class HackathonService:
    def __init__(self, hackathon_repository: HackathonRepository, user_repository: UserRepository):
        self.hackathon_repository = hackathon_repository
        self.user_repository = user_repository

    async def list_hackathons(
        self,
        upcoming: bool | None = None,
        registration_open: bool | None = None,
    ) -> list[Hackathon]:
        return await self.hackathon_repository.list_active(
            upcoming=upcoming,
            registration_open=registration_open,
        )

    async def list_managed_hackathons(self, user: User) -> list[Hackathon]:
        return await self.hackathon_repository.list_managed_by_user(user.id)

    async def create_hackathon(self, data: HackathonCreate, user: User) -> Hackathon:
        if user.role != UserRole.ADMIN:
            raise AdminRequiredError

        hackathon = Hackathon(
            **data.model_dump(),
            organizer=user,
            co_organizers=[],
            registration_open=True,
            is_deleted=False,
        )
        try:
            await self.hackathon_repository.add(hackathon)
            await self.hackathon_repository.commit()
        except SQLAlchemyError:
            await self.hackathon_repository.rollback()
            raise
        return hackathon

    async def get_hackathon(self, public_id: uuid.UUID) -> Hackathon:
        hackathon = await self.hackathon_repository.get_active_by_public_id(public_id)
        if hackathon is None:
            raise HackathonNotFoundError
        return hackathon

    async def update_hackathon(
        self,
        public_id: uuid.UUID,
        data: HackathonUpdate,
        user: User,
    ) -> Hackathon:
        hackathon = await self._get_owned_hackathon(public_id, user)
        changes = data.model_dump(exclude_unset=True)

        start_date = changes.get("start_date", hackathon.start_date)
        end_date = changes.get("end_date", hackathon.end_date)
        capacity = changes.get("capacity", hackathon.capacity)
        max_team_size = changes.get("max_team_size", hackathon.max_team_size)
        registration_deadline = changes.get(
            "registration_deadline",
            hackathon.registration_deadline,
        )
        registration_opens_at = changes.get(
            "registration_opens_at",
            hackathon.registration_opens_at,
        )
        self._validate_ranges(
            start_date,
            end_date,
            registration_opens_at,
            registration_deadline,
            capacity,
            max_team_size,
        )

        for field, value in changes.items():
            setattr(hackathon, field, value)
        if "registration_opens_at" in changes:
            hackathon.registration_open = True

        await self.hackathon_repository.commit()
        await self.hackathon_repository.refresh_updated_at(hackathon)
        return hackathon

    async def delete_hackathon(
        self,
        public_id: uuid.UUID,
        confirm_name: str,
        user: User,
    ) -> None:
        hackathon = await self._get_owned_hackathon(public_id, user)
        if confirm_name != hackathon.name:
            raise InvalidConfirmNameError

        hackathon.is_deleted = True
        hackathon.deleted_at = datetime.now(UTC)
        await self.hackathon_repository.commit()

    async def add_co_organizer(
        self, public_id: uuid.UUID, data: CoOrganizerAddRequest, user: User
    ) -> Hackathon:
        hackathon = await self._get_owned_hackathon(public_id, user)
        co_organizer = await self.user_repository.get_by_public_id(data.user_public_id)

        if co_organizer is None:
            raise CoOrganizerUserNotFoundError

        if any(item.id == co_organizer.id for item in hackathon.co_organizers):
            raise CoOrganizerAlreadyAssignedError

        if co_organizer.id == hackathon.organizer_id:
            raise OrganizerCannotBeCoOrganizerError

        try:
            hackathon.co_organizers.append(co_organizer)
            await self.hackathon_repository.commit()
        except IntegrityError as error:
            await self.hackathon_repository.rollback()

            if get_integrity_error_constraint(error) == "hackathon_co_organizers_pkey":
                raise CoOrganizerAlreadyAssignedError() from error

            raise
        except SQLAlchemyError:
            await self.hackathon_repository.rollback()
            raise
        return hackathon

    async def get_co_organizer_candidates(
        self,
        public_id: uuid.UUID,
        user: User,
        query: str,
    ) -> list[User]:
        hackathon = await self._get_owned_hackathon(public_id, user)
        excluded_user_ids = {
            hackathon.organizer_id,
            *(co_organizer.id for co_organizer in hackathon.co_organizers),
        }
        normalized_query = query.strip()
        if len(normalized_query) < 2:
            return []

        candidates = await self.user_repository.search_by_name(
            normalized_query,
            excluded_user_ids,
        )
        return candidates

    async def open_registration(self, public_id: uuid.UUID, user: User) -> Hackathon:
        hackathon = await self._get_owned_hackathon(public_id, user)
        opened_at = datetime.now(UTC)
        if opened_at >= hackathon.registration_deadline:
            raise RegistrationDeadlinePassedError
        if hackathon.is_registration_open_at(opened_at):
            raise RegistrationAlreadyOpenError

        hackathon.registration_opens_at = opened_at
        hackathon.registration_open = True
        await self.hackathon_repository.commit()
        return hackathon

    async def close_registration(self, public_id: uuid.UUID, user: User) -> Hackathon:
        hackathon = await self._get_owned_hackathon(public_id, user)
        if not hackathon.registration_open:
            raise RegistrationAlreadyClosedError

        hackathon.registration_open = False
        await self.hackathon_repository.commit()
        return hackathon

    async def _get_owned_hackathon(self, public_id: uuid.UUID, user: User) -> Hackathon:
        hackathon = await self.hackathon_repository.get_owned_by_public_id(public_id, user.id)
        if hackathon is None:
            raise HackathonNotFoundError
        return hackathon

    @staticmethod
    def _validate_ranges(
        start_date: datetime,
        end_date: datetime,
        registration_opens_at: datetime,
        registration_deadline: datetime,
        capacity: int | None,
        max_team_size: int,
    ) -> None:
        if end_date <= start_date:
            raise InvalidDateRangeError
        if registration_deadline >= start_date:
            raise InvalidRegistrationDeadlineError
        if registration_opens_at >= registration_deadline:
            raise InvalidRegistrationWindowError
        if capacity is not None and max_team_size > capacity:
            raise InvalidTeamSizeError
