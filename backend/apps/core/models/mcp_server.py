"""MCPServer model for managing MCP server instances."""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Enum, ForeignKey, Index, LargeBinary, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class MCPServerStatus(str, enum.Enum):
    """MCPServer status."""

    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class MCPServer(Base):
    """MCPServer model for managing MCP server instances.

    Each MCP Server has a unique API key (hashed) for machine-to-machine auth.
    """

    __tablename__ = "mcp_servers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[MCPServerStatus] = mapped_column(
        Enum(MCPServerStatus, name="mcp_server_status"),
        default=MCPServerStatus.ENABLED,
        nullable=False,
    )
    api_key_hash: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False, comment="Hashed API key (bcrypt)"
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="mcp_servers"
    )

    # Indexes
    __table_args__ = (
        Index("ix_mcp_servers_org_id", "org_id"),
        Index("ix_mcp_servers_org_id_name", "org_id", "name", unique=True),
    )

    def __repr__(self) -> str:
        return f"<MCPServer(id={self.id}, name={self.name}, status={self.status.value}, org_id={self.org_id})>"
