"""Authentication schemas."""

from pydantic import BaseModel, EmailStr


class DevLoginRequest(BaseModel):
    """Request schema for dev login."""

    email: EmailStr
    org_name: str


class DevLoginResponse(BaseModel):
    """Response schema for dev login."""

    access_token: str
    token_type: str = "bearer"
    org_id: str


class OIDCExchangeRequest(BaseModel):
    """Request schema for OIDC code exchange."""

    code: str
    state: str | None = None


class OIDCConfigResponse(BaseModel):
    """Response schema for OIDC configuration."""

    issuer: str
    client_id: str
    redirect_uri: str


class CurrentUserResponse(BaseModel):
    """Response schema for current user info."""

    email: str
    org_id: str
    roles: list[str]
