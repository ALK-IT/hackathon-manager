from src.resources.config import get_resource_fernet


def encrypt_value(value: str) -> str:
    return get_resource_fernet().encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    return get_resource_fernet().decrypt(value.encode()).decode()
