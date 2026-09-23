import logging

import pytest

from src.auth.config import validate_configuration
from src.common.runtime_secrets import (
    LOCAL_JWT_SECRET_KEY,
    LOCAL_RESOURCE_ENCRYPTION_KEY,
)
from src.resources.config import get_resource_fernet, validate_resource_configuration


@pytest.fixture(autouse=True)
def clear_resource_fernet_cache():
    get_resource_fernet.cache_clear()
    yield
    get_resource_fernet.cache_clear()


@pytest.mark.parametrize("environment", [None, "production", "staging"])
def test_known_jwt_fallback_is_rejected_outside_local(monkeypatch, environment):
    if environment is None:
        monkeypatch.delenv("ENV", raising=False)
    else:
        monkeypatch.setenv("ENV", environment)
    monkeypatch.setenv("JWT_SECRET_KEY", LOCAL_JWT_SECRET_KEY)

    with pytest.raises(RuntimeError, match="known local fallback outside ENV=local"):
        validate_configuration()


def test_known_resource_fallback_is_rejected_outside_local(monkeypatch):
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.setenv("RESOURCE_ENCRYPTION_KEY", LOCAL_RESOURCE_ENCRYPTION_KEY)
    monkeypatch.delenv("RESOURCE_ENCRYPTION_KEYS", raising=False)

    with pytest.raises(RuntimeError, match="known local fallback outside ENV=local"):
        validate_resource_configuration()


def test_local_fallbacks_emit_startup_warnings(monkeypatch, caplog):
    monkeypatch.setenv("ENV", "local")
    monkeypatch.setenv("JWT_SECRET_KEY", LOCAL_JWT_SECRET_KEY)
    monkeypatch.setenv("RESOURCE_ENCRYPTION_KEY", LOCAL_RESOURCE_ENCRYPTION_KEY)
    monkeypatch.delenv("RESOURCE_ENCRYPTION_KEYS", raising=False)

    with caplog.at_level(logging.WARNING):
        validate_configuration()
        validate_resource_configuration()

    assert "JWT_SECRET_KEY uses a public local-development fallback" in caplog.text
    assert "RESOURCE_ENCRYPTION_KEYS/RESOURCE_ENCRYPTION_KEY uses a public" in caplog.text
