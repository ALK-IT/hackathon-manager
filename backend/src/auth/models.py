import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base

if TYPE_CHECKING:
    from src.hackathons.models import Hackathon
    from src.registration.models import Registration


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, name="user_role"),
        default=UserRole.USER,
        nullable=False,
    )
    registrations: Mapped[list["Registration"]] = relationship(
        back_populates="user",
        foreign_keys="Registration.user_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    organized_hackathons: Mapped[list["Hackathon"]] = relationship(
        back_populates="organizer",
        foreign_keys="Hackathon.organizer_id",
    )
    co_organized_hackathons: Mapped[list["Hackathon"]] = relationship(
        secondary="hackathon_co_organizers",
        back_populates="co_organizers",
    )
