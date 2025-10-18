"""Authentication endpoints and utilities."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db import get_db
from .models import Membership, Organization, User
from .schemas import (
    DevLoginRequest,
    DevLoginResponse,
    OIDCConfigResponse,
    OIDCExchangeRequest,
)
from .security import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/dev/login", response_model=DevLoginResponse)
async def dev_login(
    request: DevLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Dev-only login endpoint for local and CI environments.

    Creates or finds user, organization, and membership, then issues a JWT token.
    Only available when APP_ENV is 'local' or 'ci'.
    """
    # Check if dev login is allowed
    if settings.APP_ENV not in ["local", "ci"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dev login is not available in this environment",
        )

    # Find or create user
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()

    if not user:
        user = User(email=request.email)
        db.add(user)
        await db.flush()
        logger.info(f"Created new user: {user.email}")

    # Find or create organization
    result = await db.execute(select(Organization).where(Organization.name == request.org_name))
    org = result.scalars().first()

    if not org:
        org = Organization(name=request.org_name)
        db.add(org)
        await db.flush()
        logger.info(f"Created new organization: {org.name}")

    # Find or create membership
    result = await db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.org_id == org.id,
        )
    )
    membership = result.scalars().first()

    if not membership:
        membership = Membership(
            user_id=user.id,
            org_id=org.id,
            roles=["ORG_ADMIN"],  # Default role for dev login
        )
        db.add(membership)
        await db.flush()
        logger.info(f"Created membership for {user.email} in {org.name}")

    await db.commit()

    # Create JWT token with claims
    claims = {
        "sub": str(user.id),
        "email": user.email,
        "org_id": str(org.id),
        "roles": membership.roles,
    }

    access_token = create_access_token(claims)

    return DevLoginResponse(
        access_token=access_token,
        token_type="bearer",
        org_id=str(org.id),
    )


@router.get("/oidc/.well-known", response_model=OIDCConfigResponse)
async def oidc_well_known():
    """
    Get OIDC configuration.

    Returns OIDC provider configuration if APP_ENV is 'prod' and all OIDC
    settings are configured. Otherwise returns 503.
    """
    if settings.APP_ENV != "prod":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC is only available in production environment",
        )

    if not settings.is_oidc_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC is not fully configured. Please set all OIDC_* environment variables.",
        )

    return OIDCConfigResponse(
        issuer=settings.OIDC_ISSUER,  # type: ignore
        client_id=settings.OIDC_CLIENT_ID,  # type: ignore
        redirect_uri=settings.OIDC_REDIRECT_URI,  # type: ignore
    )


@router.post("/oidc/exchange")
async def oidc_exchange(request: OIDCExchangeRequest):
    """
    Exchange OIDC authorization code for access token.

    This is a skeleton implementation. In V1, this will:
    1. Exchange the code with the IdP
    2. Verify the ID token
    3. Create/update user and organization
    4. Issue our JWT token

    Currently returns 503 as a placeholder.
    """
    if settings.APP_ENV != "prod":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC is only available in production environment",
        )

    if not settings.is_oidc_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC is not fully configured. Please set all OIDC_* environment variables.",
        )

    # TODO: Implement OIDC code exchange in V1
    # 1. Use httpx to exchange code with IdP
    # 2. Verify ID token signature and claims
    # 3. Extract user info (email, etc.)
    # 4. Create/find user and organization
    # 5. Create membership
    # 6. Issue JWT token

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="OIDC exchange not yet implemented - skeleton only",
    )
