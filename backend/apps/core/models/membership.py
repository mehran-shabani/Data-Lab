"""Membership model for user-organization relationships with roles."""

import json
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from ..db import Base


class JSONEncodedList(TypeDecorator):
    """Type decorator to store list as JSON for SQLite compatibility."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        return json.loads(value)


class Membership(Base):
    """Membership model linking users to organizations with roles."""

    __tablename__ = "memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Use ARRAY for PostgreSQL, JSON for SQLite
    roles: Mapped[list[str]] = mapped_column(
        ARRAY(String).with_variant(JSONEncodedList, "sqlite"),
        default=lambda: ["ORG_MEMBER"],
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="memberships")  # noqa: F821
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="memberships"
    )

    def __repr__(self) -> str:
        return f"<Membership(user_id={self.user_id}, org_id={self.org_id}, roles={self.roles})>"
