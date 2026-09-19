import os
from functools import cache

from cryptography.fernet import Fernet, MultiFernet


def get_resource_encryption_keys() -> list[bytes]:
    configured = os.environ.get("RESOURCE_ENCRYPTION_KEYS", "").strip()
    values = (
        configured.split(",") if configured else [os.environ.get("RESOURCE_ENCRYPTION_KEY", "")]
    )
    if not values or any(not value.strip() for value in values):
        raise RuntimeError("RESOURCE_ENCRYPTION_KEYS or RESOURCE_ENCRYPTION_KEY must be configured")

    try:
        keys = [value.strip().encode("ascii") for value in values]
        for key in keys:
            Fernet(key)
        return keys
    except (UnicodeEncodeError, ValueError) as exc:
        message = (
            "RESOURCE_ENCRYPTION_KEYS must contain valid ASCII Fernet keys"
            if configured
            else "RESOURCE_ENCRYPTION_KEY must be valid ASCII Fernet key"
        )
        raise RuntimeError(message) from exc


@cache
def get_resource_fernet() -> MultiFernet:
    return MultiFernet([Fernet(key) for key in get_resource_encryption_keys()])


def validate_resource_configuration() -> None:
    get_resource_fernet()
