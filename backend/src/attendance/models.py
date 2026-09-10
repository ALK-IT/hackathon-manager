import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base

if TYPE_CHECKING:
    from src.auth.models import User
    from src.hackathons.models import Hackathon
    from src.registration.models import Registration


class CheckInSession(Base):
    __tablename__ = "check_in_sessions"
    __table_args__ = (
        Index(
            "uq_check_in_sessions_one_active_per_hackathon",
            "hackathon_id",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    hackathon_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hackathons.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    hackathon: Mapped["Hackathon"] = relationship(back_populates="check_in_sessions")
    created_by: Mapped["User"] = relationship(back_populates="check_in_sessions_created")
    check_ins: Mapped[list["CheckIn"]] = relationship(
        back_populates="session",
        passive_deletes=True,
    )


class CheckIn(Base):
    __tablename__ = "check_ins"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    registration_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("registrations.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    check_in_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("check_in_sessions.id", ondelete="CASCADE"), nullable=False
    )
    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    registration: Mapped["Registration"] = relationship(back_populates="check_in")
    session: Mapped["CheckInSession"] = relationship(back_populates="check_ins")
