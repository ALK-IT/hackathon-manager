import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base

if TYPE_CHECKING:
    from src.auth.models import User
    from src.hackathons.models import Hackathon


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

    user: Mapped["User"] = relationship(back_populates="registrations")

    hackathon_id: Mapped[int] = mapped_column(ForeignKey("hackathons.id", ondelete="CASCADE"))

    hackathon: Mapped["Hackathon"] = relationship(back_populates="registrations")

    answers: Mapped[list["RegistrationAnswer"]] = relationship(
        back_populates="registration",
        cascade="all, delete-orphan",
        passive_deletes=True,
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
