import pytest
from cryptography.fernet import Fernet

from src.resources.config import get_resource_fernet


@pytest.fixture(autouse=True)
def resource_encryption_key(monkeypatch):
    get_resource_fernet.cache_clear()
    monkeypatch.setenv(
        "RESOURCE_ENCRYPTION_KEY",
        Fernet.generate_key().decode("ascii"),
    )
    yield
    get_resource_fernet.cache_clear()
