import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.hackathons.models import Hackathon


def _validate_timezone(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Datetime must include a timezone")
    return value


class HackathonCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    start_date: datetime
    end_date: datetime
    capacity: int | None = Field(default=None, ge=1)
    max_team_size: int = Field(ge=1)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_timezone(cls, value: datetime) -> datetime:
        return _validate_timezone(value)

    @model_validator(mode="after")
    def validate_ranges(self) -> "HackathonCreate":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be later than start_date")
        if self.capacity is not None and self.max_team_size > self.capacity:
            raise ValueError("max_team_size cannot be greater than capacity")
        return self


class HackathonUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    start_date: datetime | None = None
    end_date: datetime | None = None
    capacity: int | None = Field(default=None, ge=1)
    max_team_size: int | None = Field(default=None, ge=1)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            return _validate_timezone(value)
        return value

    @model_validator(mode="after")
    def validate_update(self) -> "HackathonUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        nullable_fields = {"name", "description", "start_date", "end_date", "max_team_size"}
        if any(
            field in self.model_fields_set and getattr(self, field) is None
            for field in nullable_fields
        ):
            raise ValueError("Only capacity can be set to null")

        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date <= self.start_date
        ):
            raise ValueError("end_date must be later than start_date")
        if (
            self.capacity is not None
            and self.max_team_size is not None
            and self.max_team_size > self.capacity
        ):
            raise ValueError("max_team_size cannot be greater than capacity")
        return self


class HackathonDeleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm_name: str = Field(min_length=1, max_length=200)

    @field_validator("confirm_name", mode="before")
    @classmethod
    def normalize_confirm_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    name: str


class HackathonAccessLevel(str, Enum):
    OWNER = "owner"
    CO_ORGANIZER = "co_organizer"
    VIEWER = "viewer"


def _get_access_level(hackathon: Hackathon, user_id: int) -> HackathonAccessLevel:
    if hackathon.organizer_id == user_id:
        return HackathonAccessLevel.OWNER
    if any(co_organizer.id == user_id for co_organizer in hackathon.co_organizers):
        return HackathonAccessLevel.CO_ORGANIZER
    return HackathonAccessLevel.VIEWER


class HackathonListItem(BaseModel):
    public_id: uuid.UUID
    name: str
    start_date: datetime
    end_date: datetime
    registration_open: bool
    capacity: int | None
    max_team_size: int
    access_level: HackathonAccessLevel

    @classmethod
    def from_hackathon(cls, hackathon: Hackathon, user_id: int) -> "HackathonListItem":
        return cls(
            public_id=hackathon.public_id,
            name=hackathon.name,
            start_date=hackathon.start_date,
            end_date=hackathon.end_date,
            registration_open=hackathon.registration_open,
            capacity=hackathon.capacity,
            max_team_size=hackathon.max_team_size,
            access_level=_get_access_level(hackathon, user_id),
        )


class HackathonRead(HackathonListItem):
    description: str
    organizer: UserSummary
    co_organizers: list[UserSummary]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_hackathon(cls, hackathon: Hackathon, user_id: int) -> "HackathonRead":
        return cls(
            public_id=hackathon.public_id,
            name=hackathon.name,
            description=hackathon.description,
            start_date=hackathon.start_date,
            end_date=hackathon.end_date,
            registration_open=hackathon.registration_open,
            capacity=hackathon.capacity,
            max_team_size=hackathon.max_team_size,
            organizer=UserSummary.model_validate(hackathon.organizer),
            co_organizers=[
                UserSummary.model_validate(co_organizer) for co_organizer in hackathon.co_organizers
            ],
            access_level=_get_access_level(hackathon, user_id),
            created_at=hackathon.created_at,
            updated_at=hackathon.updated_at,
        )


class HackathonRegistrationStateRead(BaseModel):
    public_id: uuid.UUID
    registration_open: bool
