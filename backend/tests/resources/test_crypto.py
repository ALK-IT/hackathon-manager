import pytest
from cryptography.fernet import Fernet, InvalidToken

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


def test_multiple_keys_encrypt_with_first_and_decrypt_with_old_key(monkeypatch):
    new_key = Fernet.generate_key()
    old_key = Fernet.generate_key()
    old_token = Fernet(old_key).encrypt(b"old-secret").decode()
    monkeypatch.setenv(
        "RESOURCE_ENCRYPTION_KEYS",
        f"{new_key.decode()},{old_key.decode()}",
    )
    get_resource_fernet.cache_clear()

    assert decrypt_value(old_token) == "old-secret"
    new_token = encrypt_value("new-secret")
    assert Fernet(new_key).decrypt(new_token.encode()) == b"new-secret"
    with pytest.raises(InvalidToken):
        Fernet(old_key).decrypt(new_token.encode())


def test_invalid_key_in_key_ring_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "RESOURCE_ENCRYPTION_KEYS",
        f"{Fernet.generate_key().decode()},invalid",
    )
    get_resource_fernet.cache_clear()

    with pytest.raises(RuntimeError, match="RESOURCE_ENCRYPTION_KEYS"):
        encrypt_value("secret")
