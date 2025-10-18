"""Common dependencies for API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/dev/login", auto_error=True)


class CurrentUser(BaseModel):
    """Current authenticated user model."""

    user_id: UUID
    email: str
    org_id: UUID
    roles: list[str]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CurrentUser:
    """
    Extract and validate current user from JWT token.

    Args:
        token: JWT access token from Authorization header.

    Returns:
        CurrentUser instance with user information.

    Raises:
        HTTPException: If token is invalid or missing required claims.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)

        # Extract required claims
        user_id_str: str | None = payload.get("sub")
        email: str | None = payload.get("email")
        org_id_str: str | None = payload.get("org_id")
        roles: list[str] | None = payload.get("roles")

        if not all([user_id_str, email, org_id_str, roles]):
            raise credentials_exception

        return CurrentUser(
            user_id=UUID(user_id_str),  # type: ignore
            email=email,  # type: ignore
            org_id=UUID(org_id_str),  # type: ignore
            roles=roles,  # type: ignore
        )

    except (JWTError, ValueError, KeyError) as e:
        raise credentials_exception from e


def require_roles(*required_roles: str):
    """
    Dependency factory to check if user has required roles.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_roles("ORG_ADMIN"))])
        async def admin_only():
            ...

    Args:
        *required_roles: One or more role names that the user must have.

    Returns:
        Dependency function that validates user roles.

    Raises:
        HTTPException: 403 if user doesn't have required roles.
    """

    async def check_roles(current_user: CurrentUser = Depends(get_current_user)):
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(required_roles)}",
            )
        return current_user

    return check_roles


def org_guard(org_id_param: str = "org_id"):
    """
    Dependency factory to ensure user belongs to the requested organization.

    Usage:
        @router.get("/orgs/{org_id}/resource", dependencies=[Depends(org_guard())])
        async def get_resource(org_id: UUID):
            ...

    Args:
        org_id_param: Name of the path parameter containing the org_id (default: "org_id").

    Returns:
        Dependency function that validates organization access.

    Raises:
        HTTPException: 403 if user doesn't belong to the organization.
    """

    async def check_org_access(
        org_id: UUID,
        current_user: CurrentUser = Depends(get_current_user),
    ):
        if current_user.org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you don't belong to this organization",
            )
        return current_user

    return check_org_access


async def get_db_session(
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """Get database session dependency."""
    return db


async def get_optional_user(
    token: str | None = Depends(OAuth2PasswordBearer(tokenUrl="/auth/dev/login", auto_error=False)),
) -> CurrentUser | None:
    """Get optional current user (no error if not authenticated)."""
    if token is None:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None
