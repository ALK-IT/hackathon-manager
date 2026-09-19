import logging
import os
from collections.abc import Iterable

logger = logging.getLogger(__name__)

LOCAL_ENVIRONMENT = "local"
DEFAULT_ENVIRONMENT = "production"

LOCAL_JWT_SECRET_KEY = "hackathon-manager-local-development-jwt-secret-key-2026"
LOCAL_RESOURCE_ENCRYPTION_KEY = "9pCSQ_fFpSdZmaSE0l3uR4vNc-KJ9gNJp0stKVSHQX8="  # gitleaks:allow


def get_environment() -> str:
    return os.environ.get("ENV", DEFAULT_ENVIRONMENT).strip().lower() or DEFAULT_ENVIRONMENT


def validate_runtime_secret(
    variable_name: str,
    values: Iterable[str],
    known_local_values: set[str],
) -> None:
    if not any(value in known_local_values for value in values):
        return

    environment = get_environment()
    if environment != LOCAL_ENVIRONMENT:
        raise RuntimeError(f"{variable_name} uses a known local fallback outside ENV=local")

    logger.warning(
        "%s uses a public local-development fallback; never use it outside ENV=local",
        variable_name,
    )
