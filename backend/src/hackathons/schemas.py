import uuid
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.hackathons.access import HackathonAccessLevel, get_hackathon_access_level
from src.hackathons.models import Hackathon
from src.registration.models import RegistrationStatus

DEFAULT_REGISTRATION_DEADLINE_OFFSET = timedelta(hours=48)


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
    registration_opens_at: datetime
    registration_deadline: datetime | None = None
    capacity: int | None = Field(default=None, ge=1)
    max_team_size: int = Field(ge=1)
    teams_enabled: bool = True
    tasks_released_at: datetime | None = None

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

    @field_validator(
        "start_date",
        "end_date",
        "registration_opens_at",
        "registration_deadline",
        "tasks_released_at",
    )
    @classmethod
    def validate_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            return _validate_timezone(value)
        return value

    @model_validator(mode="after")
    def validate_ranges(self) -> "HackathonCreate":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be later than start_date")
        if self.registration_deadline is None:
            self.registration_deadline = self.start_date - DEFAULT_REGISTRATION_DEADLINE_OFFSET
        elif self.registration_deadline >= self.start_date:
            raise ValueError("registration_deadline must be earlier than start_date")
        if self.registration_opens_at >= self.registration_deadline:
            raise ValueError("registration_opens_at must be earlier than registration_deadline")
        if self.capacity is not None and self.max_team_size > self.capacity:
            raise ValueError("max_team_size cannot be greater than capacity")
        if self.tasks_released_at is None:
            self.tasks_released_at = self.start_date
        elif self.tasks_released_at >= self.end_date:
            raise ValueError("tasks_released_at must be earlier than end_date")
        return self


class HackathonUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_opens_at: datetime | None = None
    registration_deadline: datetime | None = None
    capacity: int | None = Field(default=None, ge=1)
    max_team_size: int | None = Field(default=None, ge=1)
    teams_enabled: bool | None = None
    tasks_released_at: datetime | None = None

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

    @field_validator(
        "start_date",
        "end_date",
        "registration_opens_at",
        "registration_deadline",
        "tasks_released_at",
    )
    @classmethod
    def validate_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            return _validate_timezone(value)
        return value

    @model_validator(mode="after")
    def validate_update(self) -> "HackathonUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        nullable_fields = {
            "name",
            "description",
            "start_date",
            "end_date",
            "registration_opens_at",
            "registration_deadline",
            "max_team_size",
            "teams_enabled",
            "tasks_released_at",
        }
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
            self.registration_deadline is not None
            and self.start_date is not None
            and self.registration_deadline >= self.start_date
        ):
            raise ValueError("registration_deadline must be earlier than start_date")
        if (
            self.registration_opens_at is not None
            and self.registration_deadline is not None
            and self.registration_opens_at >= self.registration_deadline
        ):
            raise ValueError("registration_opens_at must be earlier than registration_deadline")
        if (
            self.capacity is not None
            and self.max_team_size is not None
            and self.max_team_size > self.capacity
        ):
            raise ValueError("max_team_size cannot be greater than capacity")
        if (
            self.tasks_released_at is not None
            and self.end_date is not None
            and self.tasks_released_at >= self.end_date
        ):
            raise ValueError("tasks_released_at must be earlier than end_date")
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


class CoOrganizerAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_public_id: uuid.UUID


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    name: str


class HackathonListItem(BaseModel):
    public_id: uuid.UUID
    name: str
    start_date: datetime
    end_date: datetime
    registration_opens_at: datetime
    registration_deadline: datetime
    registration_open: bool
    capacity: int | None
    max_team_size: int
    teams_enabled: bool
    access_level: HackathonAccessLevel
    my_registration_status: RegistrationStatus | None = None

    @classmethod
    def from_hackathon(
        cls,
        hackathon: Hackathon,
        user_id: int | None,
        my_registration_status: RegistrationStatus | None = None,
    ) -> "HackathonListItem":
        return cls(
            public_id=hackathon.public_id,
            name=hackathon.name,
            start_date=hackathon.start_date,
            end_date=hackathon.end_date,
            registration_opens_at=hackathon.registration_opens_at,
            registration_deadline=hackathon.registration_deadline,
            registration_open=hackathon.is_registration_open_at(),
            capacity=hackathon.capacity,
            max_team_size=hackathon.max_team_size,
            teams_enabled=hackathon.teams_enabled,
            access_level=get_hackathon_access_level(hackathon, user_id),
            my_registration_status=my_registration_status,
        )


class HackathonRead(HackathonListItem):
    description: str
    organizer: UserSummary
    co_organizers: list[UserSummary]
    created_at: datetime
    updated_at: datetime
    tasks_released_at: datetime

    @classmethod
    def from_hackathon(cls, hackathon: Hackathon, user_id: int | None) -> "HackathonRead":
        return cls(
            public_id=hackathon.public_id,
            name=hackathon.name,
            description=hackathon.description,
            start_date=hackathon.start_date,
            end_date=hackathon.end_date,
            registration_opens_at=hackathon.registration_opens_at,
            registration_deadline=hackathon.registration_deadline,
            registration_open=hackathon.is_registration_open_at(),
            capacity=hackathon.capacity,
            max_team_size=hackathon.max_team_size,
            teams_enabled=hackathon.teams_enabled,
            organizer=UserSummary.model_validate(hackathon.organizer),
            co_organizers=[
                UserSummary.model_validate(co_organizer) for co_organizer in hackathon.co_organizers
            ],
            access_level=get_hackathon_access_level(hackathon, user_id),
            created_at=hackathon.created_at,
            updated_at=hackathon.updated_at,
            tasks_released_at=hackathon.tasks_released_at or hackathon.start_date,
        )


class HackathonRegistrationStateRead(BaseModel):
    public_id: uuid.UUID
    registration_opens_at: datetime
    registration_deadline: datetime
    registration_open: bool

    @classmethod
    def from_hackathon(cls, hackathon: Hackathon) -> "HackathonRegistrationStateRead":
        return cls(
            public_id=hackathon.public_id,
            registration_opens_at=hackathon.registration_opens_at,
            registration_deadline=hackathon.registration_deadline,
            registration_open=hackathon.is_registration_open_at(),
        )
