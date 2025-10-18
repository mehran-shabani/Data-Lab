"""Application configuration using Pydantic Settings."""

import logging
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = Field(default="Farda MCP")
    APP_VERSION: str = Field(default="0.1.0")
    APP_ENV: Literal["local", "ci", "prod"] = Field(default="local")

    # Database
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/farda_mcp")

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000", "http://localhost:8080"])

    # Authentication & JWT
    AUTH_SECRET: str = Field(default="dev-secret-key-change-in-production")
    AUTH_ACCESS_TTL_MIN: int = Field(default=60)
    ALGORITHM: str = Field(default="HS256")

    # OIDC Configuration (for production)
    OIDC_ISSUER: str | None = Field(default=None)
    OIDC_CLIENT_ID: str | None = Field(default=None)
    OIDC_CLIENT_SECRET: str | None = Field(default=None)
    OIDC_REDIRECT_URI: str | None = Field(default=None)

    # Secrets Management (Envelope Encryption)
    SECRETS_MASTER_KEY: str | None = Field(default=None)

    @field_validator("OIDC_ISSUER", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET", "OIDC_REDIRECT_URI")
    @classmethod
    def validate_oidc_in_prod(cls, v, info):
        """Validate OIDC configuration in production."""
        # Note: This validator runs per field, so we'll do the full check in __init__
        return v

    def __init__(self, **kwargs):
        """Initialize settings and validate OIDC config in production."""
        super().__init__(**kwargs)

        # Check OIDC completeness in production
        if self.APP_ENV == "prod":
            oidc_fields = [
                self.OIDC_ISSUER,
                self.OIDC_CLIENT_ID,
                self.OIDC_CLIENT_SECRET,
                self.OIDC_REDIRECT_URI,
            ]
            if not all(oidc_fields):
                logger.warning(
                    "APP_ENV is 'prod' but OIDC configuration is incomplete. "
                    "OIDC endpoints will return 503. Please set all OIDC_* environment variables."
                )

    def is_oidc_configured(self) -> bool:
        """Check if OIDC is fully configured."""
        return all(
            [
                self.OIDC_ISSUER,
                self.OIDC_CLIENT_ID,
                self.OIDC_CLIENT_SECRET,
                self.OIDC_REDIRECT_URI,
            ]
        )


settings = Settings()
