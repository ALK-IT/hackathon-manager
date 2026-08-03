import uuid

from sqlalchemy.exc import IntegrityError

from src.auth.exceptions import EmailAlreadyRegisteredError
from src.auth.models import User
from src.auth.repository import UserRepository
from src.auth.schemas import UserCreate
from src.auth.utils import DUMMY_PASSWORD_HASH, hash_password, verify_password


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def register(self, data: UserCreate) -> User:
        if await self.repository.get_by_email(data.email) is not None:
            raise EmailAlreadyRegisteredError

        user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
        )

        try:
            await self.repository.create(user)
            await self.repository.commit()
        except IntegrityError as exc:
            await self.repository.rollback()
            raise EmailAlreadyRegisteredError from exc

        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        normalized_email = email.strip().lower()
        user = await self.repository.get_by_email(normalized_email)

        if user is None:
            verify_password(password, DUMMY_PASSWORD_HASH)
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    async def get_by_public_id(self, public_id: uuid.UUID) -> User | None:
        return await self.repository.get_by_public_id(public_id)
