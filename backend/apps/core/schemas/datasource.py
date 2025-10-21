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


# ===== MongoDB Configuration =====


class MongoDBConfig(BaseModel):
    """MongoDB configuration."""

    uri: str = Field(..., description="MongoDB connection URI (e.g., mongodb+srv://user:pass@host/db)")
    db: str = Field(..., description="Database name", min_length=1)
    collection: str | None = Field(default=None, description="Optional default collection")
    timeout_ms: int = Field(default=3000, ge=100, le=30000, description="Connection timeout in milliseconds")


# ===== GraphQL Configuration =====


class GraphQLConfig(BaseModel):
    """GraphQL API configuration."""

    base_url: str = Field(..., description="GraphQL endpoint URL")
    auth_type: Literal["NONE", "API_KEY", "BEARER"] = Field(default="NONE")
    headers: dict[str, str] | None = Field(default=None)
    api_key: str | None = Field(default=None)
    bearer_token: str | None = Field(default=None)
    timeout_ms: int = Field(default=4000, ge=100, le=30000, description="Request timeout in milliseconds")

    @model_validator(mode="after")
    def validate_auth_fields(self) -> "GraphQLConfig":
        """Validate auth fields based on auth_type."""
        if self.auth_type == "API_KEY" and not self.api_key:
            raise ValueError("api_key is required when auth_type is API_KEY")
        if self.auth_type == "BEARER" and not self.bearer_token:
            raise ValueError("bearer_token is required when auth_type is BEARER")
        return self


# ===== S3/MinIO Configuration =====


class S3Config(BaseModel):
    """S3/MinIO configuration."""

    endpoint: str = Field(..., description="S3 endpoint URL")
    region: str | None = Field(default=None, description="AWS region (optional for MinIO)")
    bucket: str = Field(..., description="Bucket name", min_length=1)
    access_key: str = Field(..., description="Access key ID", min_length=1)
    secret_key: str = Field(..., description="Secret access key", min_length=1)
    use_path_style: bool = Field(default=False, description="Use path-style addressing (required for MinIO)")
    timeout_ms: int = Field(default=4000, ge=100, le=30000, description="Request timeout in milliseconds")


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


class DataSourceCreateMongoDB(DataSourceBase):
    """Schema for creating MongoDB DataSource."""

    type: Literal["MONGODB"] = "MONGODB"
    uri: str = Field(..., description="MongoDB connection URI")
    db: str = Field(..., description="Database name", min_length=1)
    collection: str | None = Field(default=None, description="Optional default collection")
    timeout_ms: int = Field(default=3000, ge=100, le=30000)


class DataSourceCreateGraphQL(DataSourceBase):
    """Schema for creating GraphQL DataSource."""

    type: Literal["GRAPHQL"] = "GRAPHQL"
    base_url: str = Field(..., description="GraphQL endpoint URL")
    auth_type: Literal["NONE", "API_KEY", "BEARER"] = Field(default="NONE")
    headers: dict[str, str] | None = Field(default=None)
    api_key: str | None = Field(default=None)
    bearer_token: str | None = Field(default=None)
    timeout_ms: int = Field(default=4000, ge=100, le=30000)

    @model_validator(mode="after")
    def validate_auth_fields(self) -> "DataSourceCreateGraphQL":
        """Validate auth fields based on auth_type."""
        if self.auth_type == "API_KEY" and not self.api_key:
            raise ValueError("api_key is required when auth_type is API_KEY")
        if self.auth_type == "BEARER" and not self.bearer_token:
            raise ValueError("bearer_token is required when auth_type is BEARER")
        return self


class DataSourceCreateS3(DataSourceBase):
    """Schema for creating S3 DataSource."""

    type: Literal["S3"] = "S3"
    endpoint: str = Field(..., description="S3 endpoint URL")
    region: str | None = Field(default=None)
    bucket: str = Field(..., description="Bucket name", min_length=1)
    access_key: str = Field(..., description="Access key ID", min_length=1)
    secret_key: str = Field(..., description="Secret access key", min_length=1)
    use_path_style: bool = Field(default=False)
    timeout_ms: int = Field(default=4000, ge=100, le=30000)


# Union type for create
DataSourceCreate = Annotated[
    DataSourceCreatePostgres | DataSourceCreateRest | DataSourceCreateMongoDB | DataSourceCreateGraphQL | DataSourceCreateS3,
    Field(discriminator="type")
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


class DataSourceUpdateMongoDB(BaseModel):
    """Schema for updating MongoDB DataSource."""

    type: Literal["MONGODB"] = "MONGODB"
    name: str | None = Field(default=None, min_length=1, max_length=200)
    uri: str | None = Field(default=None)
    db: str | None = Field(default=None)
    collection: str | None = Field(default=None)
    timeout_ms: int | None = Field(default=None, ge=100, le=30000)


class DataSourceUpdateGraphQL(BaseModel):
    """Schema for updating GraphQL DataSource."""

    type: Literal["GRAPHQL"] = "GRAPHQL"
    name: str | None = Field(default=None, min_length=1, max_length=200)
    base_url: str | None = Field(default=None)
    auth_type: Literal["NONE", "API_KEY", "BEARER"] | None = Field(default=None)
    headers: dict[str, str] | None = Field(default=None)
    api_key: str | None = Field(default=None)
    bearer_token: str | None = Field(default=None)
    timeout_ms: int | None = Field(default=None, ge=100, le=30000)


class DataSourceUpdateS3(BaseModel):
    """Schema for updating S3 DataSource."""

    type: Literal["S3"] = "S3"
    name: str | None = Field(default=None, min_length=1, max_length=200)
    endpoint: str | None = Field(default=None)
    region: str | None = Field(default=None)
    bucket: str | None = Field(default=None)
    access_key: str | None = Field(default=None)
    secret_key: str | None = Field(default=None)
    use_path_style: bool | None = Field(default=None)
    timeout_ms: int | None = Field(default=None, ge=100, le=30000)


# Union type for update
DataSourceUpdate = Annotated[
    DataSourceUpdatePostgres | DataSourceUpdateRest | DataSourceUpdateMongoDB | DataSourceUpdateGraphQL | DataSourceUpdateS3,
    Field(discriminator="type")
]


# ===== Output Schema (Public View) =====


class DataSourceOut(BaseModel):
    """Public output schema for DataSource (no secrets)."""

    id: UUID
    name: str
    type: Literal["POSTGRES", "REST", "MONGODB", "GRAPHQL", "S3"]
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


class DataSourceTestCheckMongoDB(BaseModel):
    """Schema for testing MongoDB connection without saving."""

    type: Literal["MONGODB"] = "MONGODB"
    uri: str = Field(..., description="MongoDB connection URI")
    db: str = Field(..., min_length=1)
    collection: str | None = Field(default=None)
    timeout_ms: int = Field(default=3000, ge=100, le=30000)


class DataSourceTestCheckGraphQL(BaseModel):
    """Schema for testing GraphQL connection without saving."""

    type: Literal["GRAPHQL"] = "GRAPHQL"
    base_url: str = Field(..., description="GraphQL endpoint URL")
    auth_type: Literal["NONE", "API_KEY", "BEARER"] = Field(default="NONE")
    headers: dict[str, str] | None = Field(default=None)
    api_key: str | None = Field(default=None)
    bearer_token: str | None = Field(default=None)
    timeout_ms: int = Field(default=4000, ge=100, le=30000)


class DataSourceTestCheckS3(BaseModel):
    """Schema for testing S3 connection without saving."""

    type: Literal["S3"] = "S3"
    endpoint: str = Field(...)
    region: str | None = Field(default=None)
    bucket: str = Field(..., min_length=1)
    access_key: str = Field(..., min_length=1)
    secret_key: str = Field(..., min_length=1)
    use_path_style: bool = Field(default=False)
    timeout_ms: int = Field(default=4000, ge=100, le=30000)


# Union type for test check
DataSourceTestCheck = Annotated[
    DataSourceTestCheckPostgres | DataSourceTestCheckRest | DataSourceTestCheckMongoDB | DataSourceTestCheckGraphQL | DataSourceTestCheckS3,
    Field(discriminator="type")
]
