import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.hackathon_tasks.dependencies import get_task_service
from src.hackathon_tasks.models import HackathonTask, TaskSubmission
from src.hackathon_tasks.schemas import (
    TaskCreate,
    TaskResponse,
    TaskSubmissionResponse,
    TaskSubmissionUpsert,
    TaskUpdate,
)
from src.hackathon_tasks.service import TaskService

router = APIRouter(prefix="/api/hackathons/{hackathon_public_id}/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> list[HackathonTask]:
    return await service.list_tasks(hackathon_public_id, current_user)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    hackathon_public_id: uuid.UUID,
    data: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> HackathonTask:
    return await service.create_task(hackathon_public_id, data, current_user)


@router.patch("/{task_public_id}", response_model=TaskResponse)
async def update_task(
    hackathon_public_id: uuid.UUID,
    task_public_id: uuid.UUID,
    data: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> HackathonTask:
    return await service.update_task(hackathon_public_id, task_public_id, data, current_user)


@router.delete("/{task_public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    hackathon_public_id: uuid.UUID,
    task_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> Response:
    await service.delete_task(hackathon_public_id, task_public_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{task_public_id}/submission", response_model=TaskSubmissionResponse)
async def upsert_submission(
    hackathon_public_id: uuid.UUID,
    task_public_id: uuid.UUID,
    data: TaskSubmissionUpsert,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskSubmission:
    return await service.upsert_submission(
        hackathon_public_id,
        task_public_id,
        data,
        current_user,
    )


@router.get("/{task_public_id}/submissions", response_model=list[TaskSubmissionResponse])
async def list_submissions(
    hackathon_public_id: uuid.UUID,
    task_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> list[TaskSubmission]:
    return await service.list_submissions(hackathon_public_id, task_public_id, current_user)
