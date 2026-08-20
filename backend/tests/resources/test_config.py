import pytest
from cryptography.fernet import Fernet

from src.resources.config import validate_resource_configuration


def test_resource_configuration_accepts_valid_fernet_key(monkeypatch):
    monkeypatch.setenv("RESOURCE_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))

    validate_resource_configuration()


def test_resource_configuration_rejects_missing_key(monkeypatch):
    monkeypatch.delenv("RESOURCE_ENCRYPTION_KEY", raising=False)

    with pytest.raises(RuntimeError, match="must be configured"):
        validate_resource_configuration()


def test_resource_configuration_rejects_invalid_key(monkeypatch):
    monkeypatch.setenv("RESOURCE_ENCRYPTION_KEY", "invalid-key")

    with pytest.raises(RuntimeError, match="must be valid ASCII Fernet key"):
        validate_resource_configuration()
