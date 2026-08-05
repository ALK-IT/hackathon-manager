import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.registration.models import RegistrationStatus


class RegistrationQuestionCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)
    is_required: bool = True


class RegistrationAnswerCreate(BaseModel):
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
    answers: list[RegistrationAnswerCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_questions(self):
        question_ids = [answer.question_public_id for answer in self.answers]

        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Each question can be answered only once")

        return self


class RegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    status: RegistrationStatus
