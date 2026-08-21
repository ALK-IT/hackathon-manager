import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TeamCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["create"]
    name: str = Field(min_length=1, max_length=200)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class TeamJoinRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["join"]
    join_code: str = Field(min_length=8, max_length=8)

    @field_validator("join_code", mode="before")
    @classmethod
    def validate_join_code(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value


TeamSelection = Annotated[TeamCreateRequest | TeamJoinRequest, Field(discriminator="action")]


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    name: str
    join_code: str
