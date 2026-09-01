import os
from functools import cache

from cryptography.fernet import Fernet


def get_resource_encryption_key() -> bytes:
    value = os.environ.get("RESOURCE_ENCRYPTION_KEY", "")
    if not value:
        raise RuntimeError("RESOURCE_ENCRYPTION_KEY must be configured")
    try:
        key = value.encode("ascii")
        Fernet(key)
        return key
    except (UnicodeEncodeError, ValueError) as exc:
        raise RuntimeError("RESOURCE_ENCRYPTION_KEY must be valid ASCII Fernet key") from exc


@cache
def get_resource_fernet() -> Fernet:
    return Fernet(get_resource_encryption_key())


def validate_resource_configuration() -> None:
    get_resource_fernet()
