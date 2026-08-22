from cryptography.fernet import Fernet

from src.resources.config import get_resource_encryption_key


def encrypt_value(value: str) -> str:
    return Fernet(get_resource_encryption_key()).encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    return Fernet(get_resource_encryption_key()).decrypt(value.encode()).decode()
