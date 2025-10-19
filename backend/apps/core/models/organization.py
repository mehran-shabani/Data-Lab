"""Organization model for multi-tenancy."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class Organization(Base):
    """Organization model for multi-tenant architecture."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    memberships: Mapped[list["Membership"]] = relationship(  # noqa: F821
        "Membership", back_populates="organization", cascade="all, delete-orphan"
    )
    datasources: Mapped[list["DataSource"]] = relationship(  # noqa: F821
        "DataSource", back_populates="organization", cascade="all, delete-orphan"
    )
    tools: Mapped[list["Tool"]] = relationship(  # noqa: F821
        "Tool", back_populates="organization", cascade="all, delete-orphan"
    )
    mcp_servers: Mapped[list["MCPServer"]] = relationship(  # noqa: F821
        "MCPServer", back_populates="organization", cascade="all, delete-orphan"
    )
    policies: Mapped[list["Policy"]] = relationship(  # noqa: F821
        "Policy", back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, plan={self.plan})>"
