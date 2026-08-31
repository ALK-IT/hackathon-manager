import pytest
from pydantic import ValidationError

from src.resources.schemas import (
    MAX_RESOURCE_METADATA_BYTES,
    ResourceCreate,
    ResourceItemsImport,
)


def make_resource_create(metadata: dict) -> ResourceCreate:
    return ResourceCreate(
        name="Credits",
        type="api_key",
        target="individual",
        metadata=metadata,
    )


def test_resource_create_accepts_metadata_at_size_limit():
    metadata = {"value": "x" * (MAX_RESOURCE_METADATA_BYTES - len('{"value":""}'))}

    data = make_resource_create(metadata)

    assert data.metadata == metadata


def test_resource_create_rejects_metadata_over_size_limit():
    metadata = {"value": "x" * (MAX_RESOURCE_METADATA_BYTES - len('{"value":""}') + 1)}

    with pytest.raises(ValidationError, match="Resource metadata cannot exceed"):
        make_resource_create(metadata)


def test_resource_create_counts_metadata_size_in_utf8_bytes():
    metadata = {"value": "ą" * MAX_RESOURCE_METADATA_BYTES}

    with pytest.raises(ValidationError, match="Resource metadata cannot exceed"):
        make_resource_create(metadata)


def test_resource_items_import_accepts_limit_values():
    data = ResourceItemsImport(values=["x" * 4096] * 100)

    assert len(data.values) == 100
    assert len(data.values[0]) == 4096


def test_resource_items_import_rejects_more_than_100_values():
    with pytest.raises(ValidationError):
        ResourceItemsImport(values=["secret"] * 101)


def test_resource_items_import_rejects_value_longer_than_4096_characters():
    with pytest.raises(ValidationError):
        ResourceItemsImport(values=["x" * 4097])
