from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def normalize_name(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value


class HackathonCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

    _normalize_name = field_validator("name", mode="before")(normalize_name)


class HackathonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)

    _normalize_name = field_validator("name", mode="before")(normalize_name)

    @field_validator("name")
    @classmethod
    def reject_null_name(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("name cannot be null")
        return value

    @model_validator(mode="after")
    def reject_empty_update(self):
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        return self


class HackathonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
