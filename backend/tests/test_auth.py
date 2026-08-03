import uuid
from datetime import timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas import UserCreate
from app.security import (
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.services.user_service import EmailAlreadyRegisteredError, UserService


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-characters")


def test_password_is_hashed_and_can_be_verified():
    password = "correct-horse-battery-staple"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_registration_validates_name_after_trimming():
    with pytest.raises(ValidationError):
        UserCreate(name=" a ", email="a@example.com", password="password123")


def test_access_token_round_trip():
    public_id = uuid.uuid4()

    token = create_access_token(public_id)

    assert decode_access_token(token) == public_id


def test_expired_access_token_is_rejected():
    token = create_access_token(uuid.uuid4(), expires_delta=timedelta(seconds=-1))

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)


async def test_register_hashes_password_and_commits(mocker):
    repository = mocker.Mock()
    repository.get_by_email = mocker.AsyncMock(return_value=None)
    repository.create = mocker.AsyncMock()
    repository.commit = mocker.AsyncMock()
    repository.rollback = mocker.AsyncMock()
    service = UserService(repository)

    user = await service.register(
        UserCreate(name="  Jan Kowalski  ", email="JAN@EXAMPLE.COM", password="password123")
    )

    assert user.name == "Jan Kowalski"
    assert user.email == "jan@example.com"
    assert verify_password("password123", user.password_hash)
    repository.create.assert_awaited_once_with(user)
    repository.commit.assert_awaited_once_with()
    repository.rollback.assert_not_awaited()


async def test_register_rejects_duplicate_email(mocker):
    repository = mocker.Mock()
    repository.get_by_email = mocker.AsyncMock(return_value=SimpleNamespace())
    service = UserService(repository)

    with pytest.raises(EmailAlreadyRegisteredError):
        await service.register(
            UserCreate(name="Jan Kowalski", email="jan@example.com", password="password123")
        )


async def test_authenticate_accepts_correct_password(mocker):
    user = SimpleNamespace(password_hash=hash_password("password123"))
    repository = mocker.Mock()
    repository.get_by_email = mocker.AsyncMock(return_value=user)
    service = UserService(repository)

    result = await service.authenticate(" JAN@EXAMPLE.COM ", "password123")

    assert result is user
    repository.get_by_email.assert_awaited_once_with("jan@example.com")


async def test_authenticate_rejects_wrong_password(mocker):
    user = SimpleNamespace(password_hash=hash_password("password123"))
    repository = mocker.Mock()
    repository.get_by_email = mocker.AsyncMock(return_value=user)
    service = UserService(repository)

    assert await service.authenticate("jan@example.com", "wrong-password") is None
