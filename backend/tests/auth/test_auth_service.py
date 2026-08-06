import uuid
from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.auth.dependencies import get_current_user
from src.auth.exceptions import EmailAlreadyRegisteredError, InvalidAccessTokenError
from src.auth.schemas import UserCreate
from src.auth.service import TokenService, UserService
from src.auth.utils import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_access_token_payload,
    decode_refresh_token,
    hash_password,
    refresh_session_key,
    revoked_access_token_key,
    verify_password,
)


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


def test_refresh_token_cannot_be_used_as_access_token():
    token = create_refresh_token(
        uuid.uuid4(),
        session_id=uuid.uuid4(),
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)


def test_access_token_cannot_be_used_as_refresh_token():
    token = create_access_token(uuid.uuid4())

    with pytest.raises(InvalidAccessTokenError):
        decode_refresh_token(token)


async def test_logout_revokes_token_until_it_expires(mocker):
    cache = mocker.Mock()
    cache.set = mocker.AsyncMock()
    cache.delete = mocker.AsyncMock()
    service = TokenService(cache)
    token = create_access_token(uuid.uuid4(), expires_delta=timedelta(seconds=60))
    session_id = decode_access_token_payload(token).session_id

    await service.revoke(token)

    cache.set.assert_awaited_once()
    key, value = cache.set.await_args.args
    ttl_seconds = cache.set.await_args.kwargs["ex"]
    assert key == revoked_access_token_key(token)
    assert token not in key
    assert value == "1"
    assert 1 <= ttl_seconds <= 60
    cache.delete.assert_awaited_once_with(refresh_session_key(session_id))


async def test_token_revocation_is_read_from_cache(mocker):
    cache = mocker.Mock()
    cache.exists = mocker.AsyncMock(return_value=1)
    service = TokenService(cache)
    token = "access-token"

    assert await service.is_revoked(token)
    cache.exists.assert_awaited_once_with(revoked_access_token_key(token))


async def test_revoked_token_is_rejected_by_current_user_dependency(mocker):
    token_service = mocker.Mock()
    token_service.is_revoked = mocker.AsyncMock(return_value=True)
    user_service = mocker.Mock()
    user_service.get_by_public_id = mocker.AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("revoked-token", user_service, token_service)

    assert exc_info.value.status_code == 401
    user_service.get_by_public_id.assert_not_awaited()


async def test_token_pair_is_issued_and_refresh_session_is_stored(mocker):
    cache = mocker.Mock()
    cache.set = mocker.AsyncMock()
    service = TokenService(cache)
    public_id = uuid.uuid4()

    tokens = await service.issue_token_pair(public_id)

    access_payload = decode_access_token_payload(tokens.access_token)
    refresh_payload = decode_refresh_token(tokens.refresh_token)
    assert access_payload.subject == public_id
    assert refresh_payload.subject == public_id
    assert access_payload.session_id == refresh_payload.session_id
    assert tokens.access_expires_in == 30 * 60
    assert tokens.refresh_expires_in == 7 * 24 * 60 * 60
    cache.set.assert_awaited_once_with(
        refresh_session_key(refresh_payload.session_id),
        "1",
        ex=tokens.refresh_expires_in,
    )


async def test_refresh_token_is_rotated_only_once(mocker):
    public_id = uuid.uuid4()
    session_id = uuid.uuid4()
    token = create_refresh_token(
        public_id,
        session_id=session_id,
    )
    cache = mocker.Mock()
    cache.getdel = mocker.AsyncMock(side_effect=["1", None])
    service = TokenService(cache)

    assert await service.consume_refresh_token(token) == public_id

    with pytest.raises(InvalidAccessTokenError):
        await service.consume_refresh_token(token)

    assert cache.getdel.await_count == 2
    cache.getdel.assert_awaited_with(refresh_session_key(session_id))


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
