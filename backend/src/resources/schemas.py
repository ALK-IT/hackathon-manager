from typing import Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field


ResourceType = Literal["api_key"]
DistributionMode = Literal["manual"]
ResourceTarget = Literal["team", "user", "individual"]


class ResourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    type: ResourceType
    distribution_mode: DistributionMode = "manual"
    target: ResourceTarget
    metadata: dict = Field(default_factory=dict)


class ResourceItemsImport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    values: list[str] = Field(min_length=1, max_length=10_000)


class ResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    name: str
    type: str
    distribution_mode: str
    target: str
    metadata: dict
    item_count: int


class ResourceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: uuid.UUID
    resource_public_id: uuid.UUID
    is_assigned: bool
    is_revoked: bool


class ResourceImportResponse(BaseModel):
    resource: ResourceResponse
    imported_count: int
