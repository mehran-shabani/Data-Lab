"""Health check and version endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter

from ..config import settings

router = APIRouter()


@router.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {
        "status": "ok",
        "time": datetime.now(UTC).isoformat(),
    }


@router.get("/version")
async def version():
    """Version information endpoint."""
    return {
        "backend": settings.APP_VERSION,
        "web": "0.1.0",  # Will be synchronized with web version
    }
