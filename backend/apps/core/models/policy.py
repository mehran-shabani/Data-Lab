"""Policy model for access control and data masking."""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class PolicyEffect(str, enum.Enum):
    """Policy effect."""

    ALLOW = "ALLOW"
    DENY = "DENY"


class PolicyResourceType(str, enum.Enum):
    """Policy resource type."""

    TOOL = "TOOL"
    DATASOURCE = "DATASOURCE"


class Policy(Base):
    """Policy model for access control and field masking.

    Policies can ALLOW or DENY access to resources (tools, datasources)
    based on conditions (e.g., user roles). They can also define field masks
    to redact sensitive data from responses.
    """

    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    effect: Mapped[PolicyEffect] = mapped_column(
        Enum(PolicyEffect, name="policy_effect"), nullable=False
    )
    resource_type: Mapped[PolicyResourceType] = mapped_column(
        Enum(PolicyResourceType, name="policy_resource_type"), nullable=False
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, comment="ID of the tool or datasource"
    )
    conditions: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment='Optional conditions: {"roles_any_of": ["ORG_ADMIN", "DEVELOPER"]}',
    )
    field_masks: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='Field masking rules: {"remove": ["phone", "national_id"]}',
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="policies"
    )

    # Indexes
    __table_args__ = (
        Index("ix_policies_org_id", "org_id"),
        Index("ix_policies_resource_type_resource_id", "resource_type", "resource_id"),
    )

    def __repr__(self) -> str:
        return f"<Policy(id={self.id}, name={self.name}, effect={self.effect.value}, org_id={self.org_id})>"
