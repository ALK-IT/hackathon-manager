import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.registration.models import RegistrationStatus
from src.teams.schemas import TeamResponse, TeamSelection


class RegistrationQuestionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=500)
    is_required: bool = True


class RegistrationAnswerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_public_id: uuid.UUID
    content: str = Field(min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Answer cannot be empty")

        return value


class RegistrationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answers: list[RegistrationAnswerCreate] = Field(default_factory=list)
    team: TeamSelection | None = None

    @model_validator(mode="after")
    def validate_unique_questions(self):
        question_ids = [answer.question_public_id for answer in self.answers]

        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Each question can be answered only once")

        return self


class RegistrationStatusChangedByResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    name: str


class RegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    status: RegistrationStatus
    team: TeamResponse | None = None
    status_changed_at: datetime | None
    status_changed_by: RegistrationStatusChangedByResponse | None


class RegistrationStatusUpdate(BaseModel):
    status: Literal[
        RegistrationStatus.ACCEPTED,
        RegistrationStatus.REJECTED,
    ]


class RegistrationUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    name: str
    email: str


class RegistrationQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    content: str
    is_required: bool


class RegistrationAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content: str
    question: RegistrationQuestionResponse


class RegistrationDetailResponse(RegistrationResponse):
    user: RegistrationUserResponse
    answers: list[RegistrationAnswerResponse]


class RegistrationQuestionBulkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[RegistrationQuestionCreate] = Field(min_length=1, max_length=50)
