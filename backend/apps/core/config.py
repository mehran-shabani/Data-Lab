"""Application configuration using Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    APP_ENV: str = Field(default="local")  # local | ci | prod

    # Database
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/farda_mcp")

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000", "http://localhost:8080"])

    # Security (reserved for future prompts)
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)


settings = Settings()
