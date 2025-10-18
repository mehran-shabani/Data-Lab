"""Common dependencies for API routes."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_user
from .db import get_db


async def get_db_session(
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """Get database session dependency."""
    return db


async def get_optional_user(
    user: dict | None = Depends(get_current_user),
) -> dict | None:
    """Get optional current user (no error if not authenticated)."""
    return user
