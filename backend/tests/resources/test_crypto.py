from cryptography.fernet import Fernet

from src.resources.config import get_resource_fernet
from src.resources.crypto import decrypt_value, encrypt_value


def test_fernet_round_trip_never_returns_plaintext(monkeypatch):
    monkeypatch.setenv("RESOURCE_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))

    encrypted = encrypt_value("secret-api-key")

    assert encrypted != "secret-api-key"
    assert "secret-api-key" not in encrypted
    assert decrypt_value(encrypted) == "secret-api-key"


def test_invalid_fernet_key_is_rejected(monkeypatch):
    monkeypatch.setenv("RESOURCE_ENCRYPTION_KEY", "not-a-fernet-key")

    try:
        encrypt_value("secret")
    except RuntimeError as error:
        assert str(error) == "RESOURCE_ENCRYPTION_KEY must be valid ASCII Fernet key"
    else:
        raise AssertionError("Invalid Fernet key was accepted")


def test_fernet_instance_is_cached():
    first = get_resource_fernet()
    second = get_resource_fernet()

    assert first is second
