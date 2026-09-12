"""Create deterministic development data.

Run after migrations with ``python -m scripts.seed``. The seed is idempotent:
objects use stable public IDs and the script exits when the sample hackathon exists.
"""

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.engine import make_url

import src.all_models  # noqa: F401
from src.auth.models import User, UserRole
from src.auth.utils import hash_password
from src.database import DATABASE_URL, SessionLocal
from src.hackathons.models import Hackathon
from src.registration.models import (
    Registration,
    RegistrationAnswer,
    RegistrationQuestion,
    RegistrationStatus,
)
from src.resources.crypto import encrypt_value
from src.resources.models import Resource, ResourceItem
from src.teams.models import Team

SEED_NAMESPACE = uuid.UUID("891cb683-405c-4528-986d-286540fbcc31")
ADMIN_EMAIL = "admin@local.dev"
ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD", "Admin123!")
PARTICIPANT_PASSWORD = "Participant123!"
LOCAL_DATABASE_HOSTS = {None, "localhost", "127.0.0.1", "postgres"}


def seed_id(name: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, name)


async def get_or_create_user(
    session,
    *,
    name: str,
    email: str,
    password: str,
    email_verified_at: datetime,
    role: UserRole = UserRole.USER,
) -> User:
    user = await session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            public_id=seed_id(f"user:{email}"),
            name=name,
            email=email,
            password_hash=hash_password(password),
            email_verified_at=email_verified_at,
            role=role,
        )
        session.add(user)
    else:
        user.name = name
        user.password_hash = hash_password(password)
        user.email_verified_at = email_verified_at
        user.role = role
    return user


def ensure_local_database() -> None:
    host = make_url(DATABASE_URL).host
    if host not in LOCAL_DATABASE_HOSTS:
        raise RuntimeError(
            "Refusing to seed a non-local database. Run this script only in local development."
        )


async def seed() -> bool:
    now = datetime.now(UTC)
    async with SessionLocal() as session, session.begin():
        admin = await get_or_create_user(
            session,
            name="Local Admin",
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            email_verified_at=now,
            role=UserRole.ADMIN,
        )
        await session.flush()

        participants = [
            await get_or_create_user(
                session,
                name=name,
                email=email,
                password=PARTICIPANT_PASSWORD,
                email_verified_at=now,
            )
            for name, email in (
                ("Anna Participant", "anna@local.dev"),
                ("Jan Participant", "jan@local.dev"),
                ("Ola Participant", "ola@local.dev"),
            )
        ]

        hackathon_public_id = seed_id("hackathon:demo")
        existing = await session.scalar(
            select(Hackathon.id).where(Hackathon.public_id == hackathon_public_id)
        )
        if existing is not None:
            return False

        hackathon = Hackathon(
            public_id=hackathon_public_id,
            organizer=admin,
            name="Hackathon Demo",
            description="Przykładowy hackathon do lokalnego testowania aplikacji.",
            registration_opens_at=now - timedelta(days=1),
            registration_deadline=now + timedelta(days=14),
            start_date=now + timedelta(days=21),
            end_date=now + timedelta(days=23),
            registration_open=True,
            capacity=100,
            max_team_size=4,
            teams_enabled=True,
        )
        questions = [
            RegistrationQuestion(
                public_id=seed_id("question:experience"),
                content="Jakie masz doświadczenie technologiczne?",
                is_required=True,
                hackathon=hackathon,
            ),
            RegistrationQuestion(
                public_id=seed_id("question:expectations"),
                content="Czego oczekujesz od hackathonu?",
                is_required=False,
                hackathon=hackathon,
            ),
        ]
        team = Team(
            public_id=seed_id("team:demo"),
            name="Seed Squad",
            join_code="SEED2026",
            hackathon=hackathon,
        )

        statuses = [
            RegistrationStatus.ACCEPTED,
            RegistrationStatus.PENDING,
            RegistrationStatus.REJECTED,
        ]
        for index, (participant, registration_status) in enumerate(
            zip(participants, statuses, strict=True)
        ):
            registration = Registration(
                public_id=seed_id(f"registration:{participant.email}"),
                user=participant,
                hackathon=hackathon,
                team=team if index < 2 else None,
                status=registration_status,
                status_changed_at=(
                    now if registration_status is not RegistrationStatus.PENDING else None
                ),
                status_changed_by=(
                    admin if registration_status is not RegistrationStatus.PENDING else None
                ),
            )
            registration.answers = [
                RegistrationAnswer(
                    question=questions[0],
                    content=f"Przykładowa odpowiedź uczestnika {participant.name}.",
                ),
                RegistrationAnswer(
                    question=questions[1],
                    content="Nauki, współpracy i zbudowania działającego projektu.",
                ),
            ]
            session.add(registration)

        resource = Resource(
            public_id=seed_id("resource:api-keys"),
            hackathon=hackathon,
            name="Demo API keys",
            type="api_key",
            distribution_mode="manual",
            target="individual",
            resource_metadata={"provider": "demo", "environment": "local"},
        )
        resource.items = [
            ResourceItem(
                public_id=seed_id(f"resource-item:{index}"),
                encrypted_value=encrypt_value(f"demo-api-key-{index:02d}"),
            )
            for index in range(1, 6)
        ]
        session.add_all([hackathon, resource])
        return True


async def main() -> None:
    ensure_local_database()
    created = await seed()
    if created:
        print("Seed data created.")
    else:
        print("Seed data already exists; nothing to create.")
    print("Development login details are documented in README.md.")


if __name__ == "__main__":
    asyncio.run(main())
