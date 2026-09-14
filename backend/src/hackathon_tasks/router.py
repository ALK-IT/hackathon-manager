import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.hackathon_tasks.dependencies import get_task_service
from src.hackathon_tasks.models import HackathonTask
from src.hackathon_tasks.schemas import (
    TaskCreate,
    TaskResponse,
    TaskSubmissionEvaluationResponse,
    TaskSubmissionEvaluationUpdate,
    TaskSubmissionListResponse,
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
) -> TaskSubmissionResponse:
    submission = await service.upsert_submission(
        hackathon_public_id,
        task_public_id,
        data,
        current_user,
    )
    return TaskSubmissionResponse.from_submission(submission)


@router.get("/{task_public_id}/submissions", response_model=TaskSubmissionListResponse)
async def list_submissions(
    hackathon_public_id: uuid.UUID,
    task_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TaskSubmissionListResponse:
    submissions, total = await service.list_submissions(
        hackathon_public_id, task_public_id, current_user, limit=limit, offset=offset
    )
    return TaskSubmissionListResponse(
        items=[TaskSubmissionResponse.from_submission(submission) for submission in submissions],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/{task_public_id}/submissions/{submission_public_id}/evaluation",
    response_model=TaskSubmissionEvaluationResponse,
)
async def evaluate_submission(
    hackathon_public_id: uuid.UUID,
    task_public_id: uuid.UUID,
    submission_public_id: uuid.UUID,
    data: TaskSubmissionEvaluationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskSubmissionEvaluationResponse:
    result = await service.evaluate_submission(
        hackathon_public_id, task_public_id, submission_public_id, data, current_user
    )
    return TaskSubmissionEvaluationResponse.model_validate(result)
