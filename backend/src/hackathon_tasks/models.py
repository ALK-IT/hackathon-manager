import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base

if TYPE_CHECKING:
    from src.auth.models import User
    from src.hackathons.models import Hackathon
    from src.teams.models import Team


class HackathonTask(Base):
    __tablename__ = "hackathon_tasks"
    __table_args__ = (Index("ix_hackathon_tasks_public_id", "public_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    hackathon_id: Mapped[int] = mapped_column(
        ForeignKey("hackathons.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
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

    hackathon: Mapped["Hackathon"] = relationship(back_populates="tasks")
    submissions: Mapped[list["TaskSubmission"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TaskSubmission(Base):
    __tablename__ = "task_submissions"
    __table_args__ = (
        UniqueConstraint("task_id", "team_id", name="uq_task_submission_task_team"),
        Index("ix_task_submissions_public_id", "public_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("hackathon_tasks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    github_url: Mapped[str] = mapped_column(String(500), nullable=False)
    submitted_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
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

    task: Mapped["HackathonTask"] = relationship(back_populates="submissions")
    team: Mapped["Team"] = relationship(back_populates="task_submissions")
    submitted_by: Mapped["User | None"] = relationship(back_populates="task_submissions")
