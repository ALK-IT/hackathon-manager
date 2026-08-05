import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.registration.models import RegistrationQuestion, Registration
from src.models import Base

if TYPE_CHECKING:
    from src.auth.models import User


hackathon_co_organizers = Table(
    "hackathon_co_organizers",
    Base.metadata,
    Column(
        "hackathon_id",
        ForeignKey("hackathons.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "user_id",
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Hackathon(Base):
    __tablename__ = "hackathons"
    __table_args__ = (
        CheckConstraint("end_date > start_date", name="ck_hackathons_date_range"),
        CheckConstraint(
            "capacity IS NULL OR capacity >= 1",
            name="ck_hackathons_capacity_positive",
        ),
        CheckConstraint(
            "max_team_size >= 1",
            name="ck_hackathons_max_team_size_positive",
        ),
        CheckConstraint(
            "capacity IS NULL OR max_team_size <= capacity",
            name="ck_hackathons_team_size_within_capacity",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        index=True,
        nullable=False,
    )
    organizer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registration_open: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_team_size: Mapped[int] = mapped_column(Integer, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organizer: Mapped["User"] = relationship(
        back_populates="organized_hackathons",
        foreign_keys=[organizer_id],
    )
    co_organizers: Mapped[list["User"]] = relationship(
        secondary=hackathon_co_organizers,
        back_populates="co_organized_hackathons",
    )

    questions: Mapped[list["RegistrationQuestion"]] = relationship(
        back_populates="hackathon",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    registrations: Mapped[list["Registration"]] = relationship(
        back_populates="hackathon",
        passive_deletes=True,
    )
