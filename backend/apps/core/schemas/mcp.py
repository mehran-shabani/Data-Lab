"""Pydantic schemas for MCP Manager."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.mcp_server import MCPServerStatus
from ..models.policy import PolicyEffect, PolicyResourceType
from ..models.tool import ToolType


# ============ Tool Schemas ============
class ToolCreate(BaseModel):
    """Schema for creating a new tool."""

    name: str = Field(..., min_length=1, max_length=200)
    version: str = Field(default="v1", max_length=50)
    type: ToolType
    datasource_id: UUID | None = None
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    exec_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution config: query_template, params_def, path, method, etc.",
    )
    rate_limit_per_min: int | None = Field(default=None, ge=1)
    enabled: bool = True


class ToolUpdate(BaseModel):
    """Schema for updating a tool."""

    name: str | None = Field(None, min_length=1, max_length=200)
    version: str | None = Field(None, max_length=50)
    type: ToolType | None = None
    datasource_id: UUID | None = None
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    exec_config: dict[str, Any] | None = None
    rate_limit_per_min: int | None = Field(None, ge=1)
    enabled: bool | None = None


class ToolOut(BaseModel):
    """Schema for tool output."""

    id: UUID
    org_id: UUID
    name: str
    version: str
    type: ToolType
    datasource_id: UUID | None
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    exec_config: dict[str, Any]
    rate_limit_per_min: int | None
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============ MCP Server Schemas ============
class MCPServerCreate(BaseModel):
    """Schema for creating a new MCP server."""

    name: str = Field(..., min_length=1, max_length=200)


class MCPServerOut(BaseModel):
    """Schema for MCP server output."""

    id: UUID
    org_id: UUID
    name: str
    status: MCPServerStatus
    created_at: datetime
    updated_at: datetime
    plain_api_key: str | None = Field(
        None, description="Only returned on create/rotate, one-time display"
    )

    model_config = {"from_attributes": True}


class MCPServerRotateKeyIn(BaseModel):
    """Schema for rotating MCP server API key."""

    pass  # No input needed, just trigger the rotation


# ============ Policy Schemas ============
class PolicyCreate(BaseModel):
    """Schema for creating a new policy."""

    name: str = Field(..., min_length=1, max_length=200)
    effect: PolicyEffect
    resource_type: PolicyResourceType
    resource_id: UUID
    conditions: dict[str, Any] = Field(
        default_factory=dict,
        description='Optional conditions: {"roles_any_of": ["ORG_ADMIN"]}',
    )
    field_masks: dict[str, Any] | None = Field(
        None, description='Field masking rules: {"remove": ["phone"]}'
    )
    enabled: bool = True


class PolicyUpdate(BaseModel):
    """Schema for updating a policy."""

    name: str | None = Field(None, min_length=1, max_length=200)
    effect: PolicyEffect | None = None
    resource_type: PolicyResourceType | None = None
    resource_id: UUID | None = None
    conditions: dict[str, Any] | None = None
    field_masks: dict[str, Any] | None = None
    enabled: bool | None = None


class PolicyOut(BaseModel):
    """Schema for policy output."""

    id: UUID
    org_id: UUID
    name: str
    effect: PolicyEffect
    resource_type: PolicyResourceType
    resource_id: UUID
    conditions: dict[str, Any]
    field_masks: dict[str, Any] | None
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============ Invoke Schemas ============
class InvokeIn(BaseModel):
    """Schema for tool invocation input."""

    params: dict[str, Any] = Field(
        default_factory=dict, description="Parameters to pass to the tool"
    )


class InvokeOut(BaseModel):
    """Schema for tool invocation output."""

    ok: bool
    data: Any | None = None
    masked: bool = False
    trace_id: str
    error: str | None = None
