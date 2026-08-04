
from pydantic import BaseModel, Field, field_validator, model_validator


class RegistrationQuestionCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)
    is_required: bool = True


class RegistrationAnswerCreate(BaseModel):
    question_id: int
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
        question_ids = [answer.question_id for answer in self.answers]

        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Each question can be answered only once")

        return self
