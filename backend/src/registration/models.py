import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base

if TYPE_CHECKING:
    from src.auth.models import User
    from src.hackathons.models import Hackathon
    from src.teams.models import Team


class RegistrationStatus(str, Enum):
    PENDING = "pending"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class RegistrationQuestion(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id", ondelete="CASCADE"))

    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(String(500))
    is_required: Mapped[bool] = mapped_column(default=True)

    hackathon: Mapped["Hackathon"] = relationship(back_populates="questions")

    answers: Mapped[list["RegistrationAnswer"]] = relationship(
        back_populates="question", passive_deletes=True
    )


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "hackathon_id",
            name="uq_application_user_hackathon",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    status: Mapped[RegistrationStatus] = mapped_column(
        SqlEnum(RegistrationStatus, name="registration_status"),
        default=RegistrationStatus.PENDING,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="registrations",
        foreign_keys=[user_id],
    )

    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id", ondelete="CASCADE"))

    hackathon: Mapped["Hackathon"] = relationship(back_populates="registrations")

    status_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status_changed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    status_changed_by: Mapped["User | None"] = relationship(
        foreign_keys=[status_changed_by_id],
    )

    answers: Mapped[list["RegistrationAnswer"]] = relationship(
        back_populates="registration",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
    )

    team: Mapped["Team | None"] = relationship(
        back_populates="registrations",
    )


class RegistrationAnswer(Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint(
            "registration_id",
            "question_id",
            name="uq_answer_application_question",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    registration_id: Mapped[int] = mapped_column(ForeignKey("registrations.id", ondelete="CASCADE"))

    registration: Mapped["Registration"] = relationship(
        back_populates="answers",
    )

    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))

    question: Mapped["RegistrationQuestion"] = relationship(back_populates="answers")

    content: Mapped[str] = mapped_column(Text)
