"""DataSource model for managing external data connections."""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Enum, ForeignKey, Index, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class DataSourceType(str, enum.Enum):
    """Supported DataSource types."""

    POSTGRES = "POSTGRES"
    REST = "REST"


class DataSource(Base):
    """DataSource model for multi-tenant data connections.

    Stores encrypted connection configurations using envelope encryption.
    - connection_config_enc: Encrypted JSON config (encrypted with data_key)
    - data_key_enc: Encrypted data key (encrypted with master key from ENV)
    """

    __tablename__ = "datasources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[DataSourceType] = mapped_column(
        Enum(DataSourceType, name="datasource_type"), nullable=False
    )
    connection_config_enc: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False, comment="Encrypted connection config with data key"
    )
    data_key_enc: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False, comment="Encrypted data key with master key"
    )
    schema_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="datasources"
    )
    tools: Mapped[list["Tool"]] = relationship(  # noqa: F821
        "Tool", back_populates="datasource", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_datasources_org_id", "org_id"),
        Index("ix_datasources_org_id_name", "org_id", "name", unique=True),
    )

    def __repr__(self) -> str:
        return f"<DataSource(id={self.id}, name={self.name}, type={self.type.value}, org_id={self.org_id})>"
