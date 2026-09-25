import uuid
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlsplit, urlunsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from src.hackathon_tasks.models import HackathonTask, TaskSubmission


def _normalize_text(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value


class TaskCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2_000)
    max_points: int = Field(ge=1, le=1_000)

    _normalize_name = field_validator("name", mode="before")(_normalize_text)
    _normalize_description = field_validator("description", mode="before")(_normalize_text)


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10_000)
    visible_from: datetime | None = None
    criteria: list[TaskCriterion] = Field(default_factory=list, max_length=20)

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
    criteria: list[TaskCriterion] | None = Field(default=None, max_length=20)

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
    criteria: list[TaskCriterion]
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


class CriterionScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_index: int = Field(ge=0)
    points: Decimal = Field(ge=0, max_digits=8, decimal_places=2)

    @field_serializer("points")
    def serialize_points(self, value: Decimal) -> float:
        return float(value)


class TaskSubmissionEvaluationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_scores: list[CriterionScore] = Field(default_factory=list, max_length=20)
    score: Decimal | None = Field(default=None, ge=0, le=10, max_digits=4, decimal_places=2)
    feedback: str | None = Field(
        default=None,
        min_length=1,
        max_length=10_000,
    )

    @model_validator(mode="after")
    def require_score(self) -> "TaskSubmissionEvaluationUpdate":
        if not self.criterion_scores and self.score is None:
            raise ValueError("criterion_scores are required")
        return self


class TaskSubmissionEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score: float
    criterion_scores: list[CriterionScore]
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
    criteria: list[TaskCriterion]


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


class LeaderboardEntry(BaseModel):
    rank: int
    team_public_id: uuid.UUID
    team_name: str
    total_score: float
    evaluated_tasks: int


class LeaderboardResponse(BaseModel):
    items: list[LeaderboardEntry]


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
            criteria=task.criteria,
            visible_from=task.visible_from,
            created_at=task.created_at,
            updated_at=task.updated_at,
            submission=(
                TaskSubmissionResponse.from_submission(submission)
                if submission is not None
                else None
            ),
        )
