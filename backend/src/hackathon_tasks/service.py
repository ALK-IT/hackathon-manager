import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import SQLAlchemyError

from src.auth.models import User
from src.hackathon_tasks.exceptions import (
    TaskNotFoundError,
    TaskPermissionDeniedError,
    TasksNotReleasedError,
    TaskSubmissionClosedError,
    TeamRequiredForSubmissionError,
)
from src.hackathon_tasks.models import HackathonTask, TaskSubmission
from src.hackathon_tasks.repository import TaskRepository
from src.hackathon_tasks.schemas import TaskCreate, TaskSubmissionUpsert, TaskUpdate
from src.hackathons.access import can_manage_hackathon
from src.hackathons.exceptions import HackathonNotFoundError
from src.hackathons.models import Hackathon
from src.hackathons.repository import HackathonRepository
from src.registration.exceptions import RegistrationNotAcceptedError
from src.registration.models import Registration, RegistrationStatus
from src.registration.repository import RegistrationRepository
from src.teams.repository import TeamRepository


class TaskService:
    def __init__(
        self,
        repository: TaskRepository,
        hackathon_repository: HackathonRepository,
        registration_repository: RegistrationRepository,
        team_repository: TeamRepository,
    ) -> None:
        self.repository = repository
        self.hackathon_repository = hackathon_repository
        self.registration_repository = registration_repository
        self.team_repository = team_repository

    async def list_tasks(
        self,
        hackathon_public_id: uuid.UUID,
        current_user: User,
    ) -> list[HackathonTask]:
        hackathon = await self._get_hackathon(hackathon_public_id)
        if not can_manage_hackathon(hackathon, current_user):
            await self._get_accepted_registration(hackathon_public_id, current_user)
            if not hackathon.are_tasks_released_at():
                raise TasksNotReleasedError()
        return await self.repository.list_by_hackathon_id(hackathon.id)

    async def create_task(
        self,
        hackathon_public_id: uuid.UUID,
        data: TaskCreate,
        current_user: User,
    ) -> HackathonTask:
        hackathon = await self._get_managed_hackathon(hackathon_public_id, current_user)
        task = HackathonTask(hackathon_id=hackathon.id, **data.model_dump())
        try:
            await self.repository.add_task(task)
            await self.repository.commit()
            return task
        except SQLAlchemyError:
            await self.repository.rollback()
            raise

    async def update_task(
        self,
        hackathon_public_id: uuid.UUID,
        task_public_id: uuid.UUID,
        data: TaskUpdate,
        current_user: User,
    ) -> HackathonTask:
        await self._get_managed_hackathon(hackathon_public_id, current_user)
        task = await self._get_task(task_public_id, hackathon_public_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        try:
            await self.repository.commit()
            await self.repository.refresh_updated_at(task)
            return task
        except SQLAlchemyError:
            await self.repository.rollback()
            raise

    async def delete_task(
        self,
        hackathon_public_id: uuid.UUID,
        task_public_id: uuid.UUID,
        current_user: User,
    ) -> None:
        await self._get_managed_hackathon(hackathon_public_id, current_user)
        task = await self._get_task(task_public_id, hackathon_public_id)
        try:
            await self.repository.delete_task(task)
            await self.repository.commit()
        except SQLAlchemyError:
            await self.repository.rollback()
            raise

    async def upsert_submission(
        self,
        hackathon_public_id: uuid.UUID,
        task_public_id: uuid.UUID,
        data: TaskSubmissionUpsert,
        current_user: User,
    ) -> TaskSubmission:
        registration = await self._get_accepted_registration(hackathon_public_id, current_user)
        hackathon = registration.hackathon
        if not hackathon.are_tasks_released_at():
            raise TasksNotReleasedError()
        if datetime.now(UTC) >= hackathon.end_date:
            raise TaskSubmissionClosedError()
        if registration.team_id is None:
            raise TeamRequiredForSubmissionError()

        try:
            task = await self._get_task(task_public_id, hackathon_public_id)
            await self.team_repository.get_by_id_for_update(registration.team_id)
            submission = await self.repository.get_submission(task.id, registration.team_id)
            if submission is None:
                submission = TaskSubmission(
                    task_id=task.id,
                    team=registration.team,
                    github_url=data.github_url,
                    submitted_by=current_user,
                )
                await self.repository.add_submission(submission)
            else:
                submission.github_url = data.github_url
                submission.submitted_by = current_user
            await self.repository.commit()
            await self.repository.refresh_updated_at(submission)
            return submission
        except SQLAlchemyError:
            await self.repository.rollback()
            raise

    async def list_submissions(
        self,
        hackathon_public_id: uuid.UUID,
        task_public_id: uuid.UUID,
        current_user: User,
    ) -> list[TaskSubmission]:
        await self._get_managed_hackathon(hackathon_public_id, current_user)
        task = await self._get_task(task_public_id, hackathon_public_id)
        return await self.repository.list_submissions(task.id)

    async def _get_hackathon(self, public_id: uuid.UUID) -> Hackathon:
        hackathon = await self.hackathon_repository.get_active_by_public_id(public_id)
        if hackathon is None:
            raise HackathonNotFoundError()
        return hackathon

    async def _get_managed_hackathon(
        self,
        public_id: uuid.UUID,
        current_user: User,
    ) -> Hackathon:
        hackathon = await self._get_hackathon(public_id)
        if not can_manage_hackathon(hackathon, current_user):
            raise TaskPermissionDeniedError()
        return hackathon

    async def _get_task(
        self,
        task_public_id: uuid.UUID,
        hackathon_public_id: uuid.UUID,
    ) -> HackathonTask:
        task = await self.repository.get_by_public_id_and_hackathon(
            task_public_id,
            hackathon_public_id,
        )
        if task is None:
            raise TaskNotFoundError()
        return task

    async def _get_accepted_registration(
        self,
        hackathon_public_id: uuid.UUID,
        current_user: User,
    ) -> Registration:
        registration = await self.registration_repository.get_by_hackathon_and_user(
            hackathon_public_id,
            current_user.public_id,
        )
        if registration is None or registration.status is not RegistrationStatus.ACCEPTED:
            raise RegistrationNotAcceptedError()
        return registration
