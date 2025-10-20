"""Shared SQLAlchemy column type helpers."""

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

# Use PostgreSQL JSONB when available, but fall back to JSON on SQLite (used in tests).
JSONB_COMPAT = JSONB().with_variant(JSON(), "sqlite")
