import pytest
from pydantic import ValidationError

from src.resources.schemas import ResourceItemsImport


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
