import pytest
from cryptography.fernet import Fernet


@pytest.fixture(autouse=True)
def resource_encryption_key(monkeypatch):
    monkeypatch.setenv(
        "RESOURCE_ENCRYPTION_KEY",
        Fernet.generate_key().decode("ascii"),
    )
