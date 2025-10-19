"""Tool model for MCP tool registry."""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class ToolType(str, enum.Enum):
    """Supported Tool types."""

    POSTGRES_QUERY = "POSTGRES_QUERY"
    REST_CALL = "REST_CALL"
    CUSTOM = "CUSTOM"


class Tool(Base):
    """Tool model for MCP tool registry.

    Each tool represents an executable function that can be invoked.
    Tools can be bound to a DataSource for data access.
    """

    __tablename__ = "tools"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="v1", nullable=False)
    type: Mapped[ToolType] = mapped_column(Enum(ToolType, name="tool_type"), nullable=False)
    datasource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasources.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional DataSource binding",
    )
    input_schema: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, comment="JSON Schema for input validation"
    )
    output_schema: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, comment="JSON Schema for output validation"
    )
    exec_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Execution config: query_template, params_def, path, method, etc.",
    )
    rate_limit_per_min: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Rate limit per minute (NULL = use org plan default)"
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
        "Organization", back_populates="tools"
    )
    datasource: Mapped["DataSource"] = relationship(  # noqa: F821
        "DataSource", back_populates="tools"
    )

    # Indexes
    __table_args__ = (
        Index("ix_tools_org_id", "org_id"),
        Index("ix_tools_org_id_name", "org_id", "name", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Tool(id={self.id}, name={self.name}, type={self.type.value}, org_id={self.org_id})>"
