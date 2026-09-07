import hashlib
import logging
import os

logger = logging.getLogger(__name__)

LOCAL_ENVIRONMENT = "local"
DEFAULT_ENVIRONMENT = "production"


def get_environment() -> str:
    return os.environ.get("ENV", DEFAULT_ENVIRONMENT).strip().lower()


def validate_known_fallback(
    variable_name: str,
    value: str,
    known_fallback_sha256: str,
) -> None:
    value_sha256 = hashlib.sha256(value.encode()).hexdigest()
    if value_sha256 != known_fallback_sha256:
        return

    if get_environment() != LOCAL_ENVIRONMENT:
        raise RuntimeError(
            f"{variable_name} uses a known local-development fallback outside ENV=local"
        )

    logger.warning(
        "%s uses a known insecure fallback; this is allowed only because ENV=local",
        variable_name,
    )
