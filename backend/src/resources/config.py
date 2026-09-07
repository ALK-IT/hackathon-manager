import os
from functools import cache

from cryptography.fernet import Fernet

from src.common.environment import validate_known_fallback

LOCAL_RESOURCE_ENCRYPTION_KEY_SHA256 = (
    "3d79bce77a2d62327851d29861cfe1bef11b5addaf4fe8e49459bb9996284664"
)


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
    key = get_resource_encryption_key()
    validate_known_fallback(
        "RESOURCE_ENCRYPTION_KEY",
        key.decode("ascii"),
        LOCAL_RESOURCE_ENCRYPTION_KEY_SHA256,
    )
    get_resource_fernet()
