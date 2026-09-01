import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, query_expression, relationship

from src.models import Base

if TYPE_CHECKING:
    from src.auth.models import User
    from src.hackathons.models import Hackathon
    from src.registration.models import Registration
    from src.teams.models import Team


class Resource(Base):
    __tablename__ = "resources"
    __table_args__ = (Index("ix_resources_public_id", "public_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    hackathon_id: Mapped[int] = mapped_column(
        ForeignKey("hackathons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    distribution_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    target: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    item_count: Mapped[int] = query_expression()

    hackathon: Mapped["Hackathon"] = relationship(back_populates="resources")
    items: Mapped[list["ResourceItem"]] = relationship(
        back_populates="resource", cascade="all, delete-orphan", passive_deletes=True
    )
    audit_logs: Mapped[list["ResourceAuditLog"]] = relationship(
        back_populates="resource", cascade="all, delete-orphan", passive_deletes=True
    )


class ResourceItem(Base):
    __tablename__ = "resource_items"
    __table_args__ = (Index("ix_resource_items_public_id", "public_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)
    is_assigned: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    resource: Mapped["Resource"] = relationship(back_populates="items")
    assignments: Mapped[list["ResourceAssignment"]] = relationship(
        back_populates="resource_item", cascade="all, delete-orphan", passive_deletes=True
    )


class ResourceAssignment(Base):
    __tablename__ = "resource_assignments"
    __table_args__ = (
        CheckConstraint(
            "(registration_id IS NOT NULL AND team_id IS NULL) OR "
            "(registration_id IS NULL AND team_id IS NOT NULL)",
            name="ck_resource_assignments_exactly_one_recipient",
        ),
        UniqueConstraint("resource_item_id", name="uq_resource_assignment_item"),
        Index("ix_resource_assignments_public_id", "public_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    resource_item_id: Mapped[int] = mapped_column(
        ForeignKey("resource_items.id", ondelete="CASCADE"), index=True, nullable=False
    )
    registration_id: Mapped[int | None] = mapped_column(
        ForeignKey("registrations.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    assigned_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    resource_item: Mapped["ResourceItem"] = relationship(back_populates="assignments")
    registration: Mapped["Registration | None"] = relationship(
        back_populates="resource_assignments"
    )
    team: Mapped["Team | None"] = relationship(back_populates="resource_assignments")
    assigned_by: Mapped["User"] = relationship(back_populates="resource_assignments_created")


class ResourceAuditLog(Base):
    __tablename__ = "resource_audit_logs"
    __table_args__ = (Index("ix_resource_audit_logs_public_id", "public_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    resource: Mapped["Resource"] = relationship(back_populates="audit_logs")
    user: Mapped["User"] = relationship(back_populates="resource_audit_logs")
