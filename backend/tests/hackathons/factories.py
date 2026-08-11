import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from src.auth.models import User, UserRole
from src.hackathons.models import Hackathon

NOW = datetime(2026, 9, 1, 10, tzinfo=UTC)

UserFactory = Callable[..., User]
HackathonFactory = Callable[..., Hackathon]


def make_user(*, user_id: int = 1, role: UserRole = UserRole.USER) -> User:
    user = User(
        name=f"User {user_id}",
        email=f"user{user_id}@example.com",
        password_hash="hashed-password",
        role=role,
    )
    user.id = user_id
    user.public_id = uuid.uuid4()
    user.created_at = NOW
    return user


def make_hackathon(
    *,
    organizer: User,
    registration_open: bool = False,
    co_organizers: list[User] | None = None,
) -> Hackathon:
    hackathon = Hackathon(
        name="Hackathon AI",
        description="Build something useful",
        start_date=NOW + timedelta(days=1),
        end_date=NOW + timedelta(days=2),
        registration_open=registration_open,
        capacity=100,
        max_team_size=4,
        organizer=organizer,
        organizer_id=organizer.id,
        co_organizers=co_organizers or [],
    )
    hackathon.id = 1
    hackathon.public_id = uuid.uuid4()
    hackathon.is_deleted = False
    hackathon.deleted_at = None
    hackathon.created_at = NOW
    hackathon.updated_at = NOW
    return hackathon
