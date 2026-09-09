import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.attendance.models import CheckIn
from src.auth.schemas import UserRead
from src.registration.models import Registration


class SessionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expires_in_minutes: int = Field(default=15, ge=1, le=60)


class CheckInRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=32, max_length=128)


class CheckInResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    checked_in_at: datetime


class SessionCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    token: str
    expires_at: datetime
    is_active: bool


class CheckInListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    check_in: CheckInResponse
    participant: UserRead
    registration_public_id: uuid.UUID

    @classmethod
    def from_check_in(cls, check_in: CheckIn) -> "CheckInListItemResponse":
        return cls(
            check_in=CheckInResponse.model_validate(check_in),
            participant=UserRead.model_validate(check_in.registration.user),
            registration_public_id=check_in.registration.public_id,
        )


class AttendanceTeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    name: str


class AttendanceParticipantResponse(BaseModel):
    participant: UserRead
    registration_public_id: uuid.UUID
    team: AttendanceTeamResponse | None
    is_present: bool
    checked_in_at: datetime | None

    @classmethod
    def from_registration(cls, registration: Registration) -> "AttendanceParticipantResponse":
        return cls(
            participant=UserRead.model_validate(registration.user),
            registration_public_id=registration.public_id,
            team=(
                AttendanceTeamResponse.model_validate(registration.team)
                if registration.team is not None
                else None
            ),
            is_present=registration.check_in is not None,
            checked_in_at=(
                registration.check_in.checked_in_at if registration.check_in is not None else None
            ),
        )
