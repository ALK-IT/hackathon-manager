import uuid
from datetime import datetime

from sqlalchemy import false, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.hackathon_tasks.models import HackathonTask, TaskSubmission
from src.hackathons.models import Hackathon


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_hackathon_id(
        self,
        hackathon_id: int,
        *,
        visible_before: datetime | None = None,
    ) -> list[HackathonTask]:
        statement = select(HackathonTask).where(HackathonTask.hackathon_id == hackathon_id)
        if visible_before is not None:
            statement = statement.where(HackathonTask.visible_from <= visible_before)
        result = await self.session.scalars(
            statement.order_by(
                HackathonTask.visible_from, HackathonTask.created_at, HackathonTask.id
            )
        )
        return list(result.all())

    async def list_with_team_submission(
        self,
        hackathon_id: int,
        team_id: int | None,
        *,
        visible_before: datetime,
    ) -> list[tuple[HackathonTask, TaskSubmission | None]]:
        submission_join = (
            (TaskSubmission.task_id == HackathonTask.id) & (TaskSubmission.team_id == team_id)
            if team_id is not None
            else false()
        )
        result = await self.session.execute(
            select(HackathonTask, TaskSubmission)
            .outerjoin(TaskSubmission, submission_join)
            .where(
                HackathonTask.hackathon_id == hackathon_id,
                HackathonTask.visible_from <= visible_before,
            )
            .options(
                selectinload(TaskSubmission.team),
                selectinload(TaskSubmission.submitted_by),
            )
            .order_by(HackathonTask.visible_from, HackathonTask.created_at, HackathonTask.id)
        )
        return list(result.tuples().all())

    async def get_by_public_id_and_hackathon(
        self,
        task_public_id: uuid.UUID,
        hackathon_public_id: uuid.UUID,
    ) -> HackathonTask | None:
        result = await self.session.scalars(
            select(HackathonTask)
            .join(HackathonTask.hackathon)
            .where(
                HackathonTask.public_id == task_public_id,
                Hackathon.public_id == hackathon_public_id,
                Hackathon.is_deleted.is_(False),
            )
            .options(selectinload(HackathonTask.hackathon).selectinload(Hackathon.co_organizers))
        )
        return result.unique().one_or_none()

    async def get_submission(
        self,
        task_id: int,
        team_id: int,
    ) -> TaskSubmission | None:
        result = await self.session.scalars(
            select(TaskSubmission)
            .where(
                TaskSubmission.task_id == task_id,
                TaskSubmission.team_id == team_id,
            )
            .options(
                selectinload(TaskSubmission.team),
                selectinload(TaskSubmission.submitted_by),
            )
        )
        return result.one_or_none()

    async def list_submissions(self, task_id: int) -> list[TaskSubmission]:
        result = await self.session.scalars(
            select(TaskSubmission)
            .where(TaskSubmission.task_id == task_id)
            .options(
                selectinload(TaskSubmission.team),
                selectinload(TaskSubmission.submitted_by),
            )
            .order_by(TaskSubmission.updated_at.desc(), TaskSubmission.id)
        )
        return list(result.all())

    async def add_task(self, task: HackathonTask) -> HackathonTask:
        self.session.add(task)
        await self.session.flush()
        return task

    async def add_submission(self, submission: TaskSubmission) -> TaskSubmission:
        self.session.add(submission)
        await self.session.flush()
        return submission

    async def delete_task(self, task: HackathonTask) -> None:
        await self.session.delete(task)
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def refresh_updated_at(self, instance: HackathonTask | TaskSubmission) -> None:
        await self.session.refresh(instance, attribute_names=["updated_at"])
