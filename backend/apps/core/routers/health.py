"""Health check, version, and user info endpoints."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends

from ..config import settings
from ..deps import CurrentUser, get_current_user, org_guard
from ..schemas import CurrentUserResponse

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


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.
    """
    return CurrentUserResponse(
        email=current_user.email,
        org_id=str(current_user.org_id),
        roles=current_user.roles,
    )


@router.get("/orgs/{org_id}/whoami", response_model=CurrentUserResponse)
async def get_org_whoami(
    org_id: UUID,
    current_user: CurrentUser = Depends(org_guard()),
):
    """
    Get current user information with organization guard.

    Requires valid JWT token and ensures the user belongs to the specified organization.
    Returns 403 if the user doesn't belong to the organization.
    """
    return CurrentUserResponse(
        email=current_user.email,
        org_id=str(current_user.org_id),
        roles=current_user.roles,
    )
