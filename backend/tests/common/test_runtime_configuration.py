import logging

import pytest
from cryptography.fernet import Fernet

from src.auth.config import validate_configuration
from src.resources.config import get_resource_fernet, validate_resource_configuration

LOCAL_JWT_SECRET = "hackathon-manager-local-development-jwt-secret-key-2026"  # gitleaks:allow
LOCAL_RESOURCE_KEY = "9pCSQ_fFpSdZmaSE0l3uR4vNc-KJ9gNJp0stKVSHQX8="  # gitleaks:allow


@pytest.fixture(autouse=True)
def clear_resource_fernet_cache():
    get_resource_fernet.cache_clear()
    yield
    get_resource_fernet.cache_clear()


def configure_known_fallbacks(monkeypatch, environment: str | None) -> None:
    if environment is None:
        monkeypatch.delenv("ENV", raising=False)
    else:
        monkeypatch.setenv("ENV", environment)
    monkeypatch.setenv("JWT_SECRET_KEY", LOCAL_JWT_SECRET)
    monkeypatch.setenv("RESOURCE_ENCRYPTION_KEY", LOCAL_RESOURCE_KEY)


def test_default_environment_rejects_known_jwt_fallback(monkeypatch) -> None:
    configure_known_fallbacks(monkeypatch, environment=None)

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY.*outside ENV=local"):
        validate_configuration()


def test_non_local_environment_rejects_known_encryption_fallback(monkeypatch) -> None:
    configure_known_fallbacks(monkeypatch, environment="production")

    with pytest.raises(RuntimeError, match="RESOURCE_ENCRYPTION_KEY.*outside ENV=local"):
        validate_resource_configuration()


def test_local_environment_warns_about_known_fallbacks(monkeypatch, caplog) -> None:
    configure_known_fallbacks(monkeypatch, environment="local")

    with caplog.at_level(logging.WARNING, logger="src.common.environment"):
        validate_configuration()
        validate_resource_configuration()

    assert "JWT_SECRET_KEY uses a known insecure fallback" in caplog.text
    assert "RESOURCE_ENCRYPTION_KEY uses a known insecure fallback" in caplog.text
    assert LOCAL_JWT_SECRET not in caplog.text
    assert LOCAL_RESOURCE_KEY not in caplog.text


def test_non_local_environment_accepts_unique_secrets_without_warning(monkeypatch, caplog) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "unique-production-test-secret-with-at-least-32-characters",  # gitleaks:allow
    )
    monkeypatch.setenv("RESOURCE_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))

    with caplog.at_level(logging.WARNING, logger="src.common.environment"):
        validate_configuration()
        validate_resource_configuration()

    assert "known insecure fallback" not in caplog.text
