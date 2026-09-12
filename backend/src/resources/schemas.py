import json
import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ResourceType = Literal["api_key"]
DistributionMode = Literal["manual"]
ResourceTarget = Literal["team", "individual"]
ResourceValue = Annotated[str, Field(min_length=1, max_length=4096)]
MAX_RESOURCE_METADATA_BYTES = 16_384


class ResourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    type: ResourceType
    distribution_mode: DistributionMode = "manual"
    target: ResourceTarget
    metadata: dict = Field(default_factory=dict)
    values: list[ResourceValue] = Field(default_factory=list, max_length=100)

    @field_validator("metadata")
    @classmethod
    def validate_metadata_size(cls, value: dict) -> dict:
        serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(serialized) > MAX_RESOURCE_METADATA_BYTES:
            raise ValueError(f"Resource metadata cannot exceed {MAX_RESOURCE_METADATA_BYTES} bytes")
        return value

    @field_validator("values")
    @classmethod
    def normalize_values(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value]
        if any(not item for item in normalized):
            raise ValueError("Resource values cannot be empty")
        if len(set(normalized)) != len(normalized):
            raise ValueError("Resource values must be unique within an import")
        return normalized


class ResourceItemsImport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    values: list[ResourceValue] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def normalize_values(self) -> "ResourceItemsImport":
        self.values = [value.strip() for value in self.values]
        if any(not value for value in self.values):
            raise ValueError("Resource values cannot be empty")
        if len(set(self.values)) != len(self.values):
            raise ValueError("Resource values must be unique within an import")
        return self


class ResourceAssignmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_item_public_id: uuid.UUID
    registration_public_id: uuid.UUID | None = None
    team_public_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def validate_recipient(self) -> "ResourceAssignmentCreate":
        if (self.registration_public_id is None) == (self.team_public_id is None):
            raise ValueError("Provide exactly one recipient: registration or team")
        return self


class ParticipantResourceAssignmentsCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registration_public_ids: list[uuid.UUID] = Field(min_length=1, max_length=500)

    @field_validator("registration_public_ids")
    @classmethod
    def remove_duplicate_registration_ids(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        return list(dict.fromkeys(value))


class ResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    name: str
    type: str
    distribution_mode: str
    target: str
    metadata: dict = Field(validation_alias="resource_metadata")
    item_count: int


class ResourceInventoryResponse(ResourceResponse):
    available_item_count: int


class ResourceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    resource_public_id: uuid.UUID
    is_assigned: bool
    is_revoked: bool


class ResourceImportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource: ResourceResponse
    imported_count: int


class ResourceAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    assigned_at: datetime
    revoked_at: datetime | None


class ParticipantResourceAssignmentResponse(ResourceAssignmentResponse):
    registration_public_id: uuid.UUID


class ParticipantResourceAssignmentsResponse(BaseModel):
    assignments: list[ParticipantResourceAssignmentResponse]
    already_assigned_registration_public_ids: list[uuid.UUID]
