import uuid
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.hackathon_tasks.models import HackathonTask, TaskSubmission


def _normalize_text(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10_000)
    visible_from: datetime | None = None

    _normalize_title = field_validator("title", mode="before")(_normalize_text)
    _normalize_description = field_validator("description", mode="before")(_normalize_text)

    @field_validator("visible_from")
    @classmethod
    def validate_visible_from(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("visible_from must include a timezone")
        return value


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=10_000)
    visible_from: datetime | None = None

    _normalize_title = field_validator("title", mode="before")(_normalize_text)
    _normalize_description = field_validator("description", mode="before")(_normalize_text)

    @field_validator("visible_from")
    @classmethod
    def validate_visible_from(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("visible_from must include a timezone")
        return value

    @model_validator(mode="after")
    def validate_update(self) -> "TaskUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Task fields cannot be set to null")
        return self


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    title: str
    description: str
    visible_from: datetime
    created_at: datetime
    updated_at: datetime


class TaskSubmissionUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    github_url: str = Field(min_length=1, max_length=500)

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, value: str) -> str:
        value = value.strip()
        parsed = urlsplit(value)
        path_parts = [part for part in parsed.path.split("/") if part]
        if (
            parsed.scheme != "https"
            or parsed.hostname is None
            or parsed.hostname.lower() not in {"github.com", "www.github.com"}
            or len(path_parts) < 2
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError("github_url must be a valid https://github.com URL")
        return urlunsplit(("https", "github.com", parsed.path.rstrip("/"), parsed.query, ""))


class SubmissionUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    name: str


class SubmissionTeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    name: str


class TaskSubmissionEvaluationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: Decimal = Field(ge=0, le=10, max_digits=4, decimal_places=2)
    feedback: str | None = Field(
        default=None,
        min_length=1,
        max_length=10_000,
    )


class TaskSubmissionEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score: float
    feedback: str | None
    evaluated_by: SubmissionUserResponse | None
    evaluated_at: datetime


class TaskSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    github_url: str
    team: SubmissionTeamResponse
    submitted_by: SubmissionUserResponse | None
    created_at: datetime
    updated_at: datetime
    evaluation: TaskSubmissionEvaluationResponse | None

    @classmethod
    def from_submission(cls, submission: TaskSubmission) -> "TaskSubmissionResponse":
        return cls(
            public_id=submission.public_id,
            github_url=submission.github_url,
            team=SubmissionTeamResponse.model_validate(submission.team),
            submitted_by=(
                SubmissionUserResponse.model_validate(submission.submitted_by)
                if submission.submitted_by is not None
                else None
            ),
            created_at=submission.created_at,
            updated_at=submission.updated_at,
            evaluation=(
                TaskSubmissionEvaluationResponse.model_validate(submission)
                if submission.score is not None
                else None
            ),
        )


class SubmissionTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    title: str


class HackathonTaskSubmissionResponse(TaskSubmissionResponse):
    task: SubmissionTaskResponse

    @classmethod
    def from_submission(cls, submission: TaskSubmission) -> "HackathonTaskSubmissionResponse":
        return cls(
            **TaskSubmissionResponse.from_submission(submission).model_dump(),
            task=SubmissionTaskResponse.model_validate(submission.task),
        )


class TaskSubmissionListResponse(BaseModel):
    items: list[TaskSubmissionResponse]
    total: int
    limit: int
    offset: int


class HackathonTaskSubmissionListResponse(BaseModel):
    items: list[HackathonTaskSubmissionResponse]
    total: int
    limit: int
    offset: int


class ParticipantTaskResponse(TaskResponse):
    submission: TaskSubmissionResponse | None = None

    @classmethod
    def from_entities(
        cls,
        task: HackathonTask,
        submission: TaskSubmission | None,
    ) -> "ParticipantTaskResponse":
        return cls(
            public_id=task.public_id,
            title=task.title,
            description=task.description,
            visible_from=task.visible_from,
            created_at=task.created_at,
            updated_at=task.updated_at,
            submission=(
                TaskSubmissionResponse.from_submission(submission)
                if submission is not None
                else None
            ),
        )
