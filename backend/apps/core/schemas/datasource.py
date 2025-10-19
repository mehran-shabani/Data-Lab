"""Pydantic schemas for DataSource management."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

# ===== Base Schemas =====


class DataSourceBase(BaseModel):
    """Base schema for DataSource."""

    name: str = Field(..., min_length=1, max_length=200)
    schema_version: str = Field(default="v1")


# ===== PostgreSQL Configuration =====


class PostgresConfigDSN(BaseModel):
    """PostgreSQL config using DSN string."""

    dsn: str = Field(..., description="PostgreSQL connection string (DSN)")


class PostgresConfigExplicit(BaseModel):
    """PostgreSQL config using explicit fields."""

    host: str = Field(..., min_length=1)
    port: int = Field(default=5432, ge=1, le=65535)
    db: str = Field(..., alias="database", min_length=1)
    user: str = Field(..., alias="username", min_length=1)
    password: str = Field(..., min_length=1)


# ===== REST Configuration =====


class RestConfig(BaseModel):
    """REST API configuration."""

    base_url: str = Field(..., description="Base URL for REST API")
    auth_type: Literal["NONE", "API_KEY", "BEARER"] = Field(default="NONE")
    headers: dict[str, str] | None = Field(default=None)
    api_key: str | None = Field(default=None)
    bearer_token: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_auth_fields(self) -> "RestConfig":
        """Validate auth fields based on auth_type."""
        if self.auth_type == "API_KEY" and not self.api_key:
            raise ValueError("api_key is required when auth_type is API_KEY")
        if self.auth_type == "BEARER" and not self.bearer_token:
            raise ValueError("bearer_token is required when auth_type is BEARER")
        return self


# ===== Create Schemas =====


class DataSourceCreatePostgres(DataSourceBase):
    """Schema for creating PostgreSQL DataSource."""

    type: Literal["POSTGRES"] = "POSTGRES"
    # Either DSN or explicit fields
    dsn: str | None = Field(default=None)
    host: str | None = Field(default=None)
    port: int | None = Field(default=None)
    database: str | None = Field(default=None)
    username: str | None = Field(default=None)
    password: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_postgres_config(self) -> "DataSourceCreatePostgres":
        """Validate that either DSN or explicit fields are provided."""
        has_dsn = self.dsn is not None
        has_explicit = all(
            [
                self.host is not None,
                self.database is not None,
                self.username is not None,
                self.password is not None,
            ]
        )

        if not has_dsn and not has_explicit:
            raise ValueError(
                "Either 'dsn' or all of ('host', 'database', 'username', 'password') must be provided"
            )

        if has_dsn and has_explicit:
            raise ValueError("Provide either 'dsn' or explicit fields, not both")

        return self


class DataSourceCreateRest(DataSourceBase):
    """Schema for creating REST DataSource."""

    type: Literal["REST"] = "REST"
    base_url: str = Field(..., description="Base URL for REST API")
    auth_type: Literal["NONE", "API_KEY", "BEARER"] = Field(default="NONE")
    headers: dict[str, str] | None = Field(default=None)
    api_key: str | None = Field(default=None)
    bearer_token: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_auth_fields(self) -> "DataSourceCreateRest":
        """Validate auth fields based on auth_type."""
        if self.auth_type == "API_KEY" and not self.api_key:
            raise ValueError("api_key is required when auth_type is API_KEY")
        if self.auth_type == "BEARER" and not self.bearer_token:
            raise ValueError("bearer_token is required when auth_type is BEARER")
        return self


# Union type for create
DataSourceCreate = Annotated[
    DataSourceCreatePostgres | DataSourceCreateRest, Field(discriminator="type")
]


# ===== Update Schemas =====


class DataSourceUpdatePostgres(BaseModel):
    """Schema for updating PostgreSQL DataSource."""

    type: Literal["POSTGRES"] = "POSTGRES"
    name: str | None = Field(default=None, min_length=1, max_length=200)
    dsn: str | None = Field(default=None)
    host: str | None = Field(default=None)
    port: int | None = Field(default=None)
    database: str | None = Field(default=None)
    username: str | None = Field(default=None)
    password: str | None = Field(default=None)


class DataSourceUpdateRest(BaseModel):
    """Schema for updating REST DataSource."""

    type: Literal["REST"] = "REST"
    name: str | None = Field(default=None, min_length=1, max_length=200)
    base_url: str | None = Field(default=None)
    auth_type: Literal["NONE", "API_KEY", "BEARER"] | None = Field(default=None)
    headers: dict[str, str] | None = Field(default=None)
    api_key: str | None = Field(default=None)
    bearer_token: str | None = Field(default=None)


# Union type for update
DataSourceUpdate = Annotated[
    DataSourceUpdatePostgres | DataSourceUpdateRest, Field(discriminator="type")
]


# ===== Output Schema (Public View) =====


class DataSourceOut(BaseModel):
    """Public output schema for DataSource (no secrets)."""

    id: UUID
    name: str
    type: Literal["POSTGRES", "REST"]
    schema_version: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===== Connectivity Check =====


class ConnectivityCheckOut(BaseModel):
    """Output schema for connectivity check."""

    ok: bool
    details: str


# ===== Test Check (without persisting) =====


class DataSourceTestCheckPostgres(BaseModel):
    """Schema for testing PostgreSQL connection without saving."""

    type: Literal["POSTGRES"] = "POSTGRES"
    dsn: str | None = Field(default=None)
    host: str | None = Field(default=None)
    port: int | None = Field(default=None)
    database: str | None = Field(default=None)
    username: str | None = Field(default=None)
    password: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_postgres_config(self) -> "DataSourceTestCheckPostgres":
        """Validate that either DSN or explicit fields are provided."""
        has_dsn = self.dsn is not None
        has_explicit = all(
            [
                self.host is not None,
                self.database is not None,
                self.username is not None,
                self.password is not None,
            ]
        )

        if not has_dsn and not has_explicit:
            raise ValueError(
                "Either 'dsn' or all of ('host', 'database', 'username', 'password') must be provided"
            )

        return self


class DataSourceTestCheckRest(BaseModel):
    """Schema for testing REST connection without saving."""

    type: Literal["REST"] = "REST"
    base_url: str = Field(..., description="Base URL for REST API")
    auth_type: Literal["NONE", "API_KEY", "BEARER"] = Field(default="NONE")
    headers: dict[str, str] | None = Field(default=None)
    api_key: str | None = Field(default=None)
    bearer_token: str | None = Field(default=None)


# Union type for test check
DataSourceTestCheck = Annotated[
    DataSourceTestCheckPostgres | DataSourceTestCheckRest, Field(discriminator="type")
]
