"""Authentication module - reserved for future implementation."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


async def get_current_user(token: str | None = Depends(oauth2_scheme)):
    """
    Get current authenticated user.

    Reserved for future implementation with full OIDC/JWT + RBAC.
    This is a placeholder for prompt 2.
    """
    # Placeholder - will be implemented in prompt 2
    if token is None:
        return None
    return {"sub": "placeholder-user"}


async def get_current_active_user(current_user=Depends(get_current_user)):
    """Get current active user or raise exception."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return current_user
