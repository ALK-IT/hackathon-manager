import os


def get_resource_encryption_key() -> bytes:
    value = os.environ.get("RESOURCE_ENCRYPTION_KEY", "")
    if not value:
        raise RuntimeError("RESOURCE_ENCRYPTION_KEY must be configured")
    try:
        return value.encode()
    except UnicodeEncodeError as exc:
        raise RuntimeError("RESOURCE_ENCRYPTION_KEY must be valid ASCII Fernet key") from exc
