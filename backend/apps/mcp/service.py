"""Service layer for MCP Manager with tool registry, invocation, and policies."""

import logging
import secrets
import time
import uuid
from typing import Any
from uuid import UUID

import httpx
import psycopg
from fastapi import HTTPException, status
from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.connectors.service import DataSourceService
from apps.core.models import (
    DataSource,
    MCPServer,
    Membership,
    Policy,
    PolicyEffect,
    PolicyResourceType,
    Tool,
    ToolType,
)
from apps.core.schemas.mcp import (
    InvokeIn,
    InvokeOut,
    MCPServerCreate,
    PolicyCreate,
    PolicyUpdate,
    ToolCreate,
    ToolUpdate,
)

from .ratelimit import get_rate_limiter

logger = logging.getLogger(__name__)


class MCPService:
    """Service for MCP Manager business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.rate_limiter = get_rate_limiter()

    # ============ Tool Registry ============

    async def create_tool(self, org_id: UUID, payload: ToolCreate) -> Tool:
        """Create a new tool.

        Args:
            org_id: Organization ID
            payload: Tool creation payload

        Returns:
            Created Tool instance

        Raises:
            ValueError: If tool name already exists or datasource not found
        """
        # Check if name already exists
        stmt = select(Tool).where(Tool.org_id == org_id, Tool.name == payload.name)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError(f"Tool with name '{payload.name}' already exists")

        # Verify datasource exists if provided
        if payload.datasource_id:
            ds_stmt = select(DataSource).where(
                DataSource.org_id == org_id, DataSource.id == payload.datasource_id
            )
            ds_result = await self.session.execute(ds_stmt)
            if not ds_result.scalar_one_or_none():
                raise ValueError(f"DataSource '{payload.datasource_id}' not found")

        # Validate exec_config based on tool type
        self._validate_exec_config(payload.type, payload.exec_config)

        # Create tool
        tool = Tool(
            org_id=org_id,
            name=payload.name,
            version=payload.version,
            type=payload.type,
            datasource_id=payload.datasource_id,
            input_schema=payload.input_schema,
            output_schema=payload.output_schema,
            exec_config=payload.exec_config,
            rate_limit_per_min=payload.rate_limit_per_min,
            enabled=payload.enabled,
        )
        self.session.add(tool)
        await self.session.commit()
        await self.session.refresh(tool)
        return tool

    async def get_tool(self, org_id: UUID, tool_id: UUID) -> Tool | None:
        """Get tool by ID.

        Args:
            org_id: Organization ID
            tool_id: Tool ID

        Returns:
            Tool instance or None
        """
        stmt = select(Tool).where(Tool.org_id == org_id, Tool.id == tool_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tools(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[Tool]:
        """List all tools for organization.

        Args:
            org_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Tool instances
        """
        stmt = select(Tool).where(Tool.org_id == org_id).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_tool(self, org_id: UUID, tool_id: UUID, payload: ToolUpdate) -> Tool:
        """Update a tool.

        Args:
            org_id: Organization ID
            tool_id: Tool ID
            payload: Tool update payload

        Returns:
            Updated Tool instance

        Raises:
            ValueError: If tool not found or validation fails
        """
        tool = await self.get_tool(org_id, tool_id)
        if not tool:
            raise ValueError(f"Tool '{tool_id}' not found")

        # Check name uniqueness if changing
        if payload.name and payload.name != tool.name:
            stmt = select(Tool).where(Tool.org_id == org_id, Tool.name == payload.name)
            result = await self.session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError(f"Tool with name '{payload.name}' already exists")

        # Update fields
        if payload.name is not None:
            tool.name = payload.name
        if payload.version is not None:
            tool.version = payload.version
        if payload.type is not None:
            tool.type = payload.type
        if payload.datasource_id is not None:
            tool.datasource_id = payload.datasource_id
        if payload.input_schema is not None:
            tool.input_schema = payload.input_schema
        if payload.output_schema is not None:
            tool.output_schema = payload.output_schema
        if payload.exec_config is not None:
            self._validate_exec_config(tool.type, payload.exec_config)
            tool.exec_config = payload.exec_config
        if payload.rate_limit_per_min is not None:
            tool.rate_limit_per_min = payload.rate_limit_per_min
        if payload.enabled is not None:
            tool.enabled = payload.enabled

        await self.session.commit()
        await self.session.refresh(tool)
        return tool

    async def delete_tool(self, org_id: UUID, tool_id: UUID) -> None:
        """Delete a tool.

        Args:
            org_id: Organization ID
            tool_id: Tool ID

        Raises:
            ValueError: If tool not found
        """
        tool = await self.get_tool(org_id, tool_id)
        if not tool:
            raise ValueError(f"Tool '{tool_id}' not found")

        await self.session.delete(tool)
        await self.session.commit()

    # ============ MCP Server Management ============

    async def create_mcp_server(
        self, org_id: UUID, payload: MCPServerCreate
    ) -> tuple[MCPServer, str]:
        """Create a new MCP server with API key.

        Args:
            org_id: Organization ID
            payload: MCP server creation payload

        Returns:
            Tuple of (MCPServer instance, plain API key)

        Raises:
            ValueError: If server name already exists
        """
        # Check if name already exists
        stmt = select(MCPServer).where(MCPServer.org_id == org_id, MCPServer.name == payload.name)
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError(f"MCP Server with name '{payload.name}' already exists")

        # Generate API key
        plain_api_key = f"mcp_{secrets.token_urlsafe(32)}"
        api_key_hash = bcrypt.hash(plain_api_key).encode("utf-8")

        # Create server
        server = MCPServer(org_id=org_id, name=payload.name, api_key_hash=api_key_hash)
        self.session.add(server)
        await self.session.commit()
        await self.session.refresh(server)

        return server, plain_api_key

    async def get_mcp_server(self, org_id: UUID, server_id: UUID) -> MCPServer | None:
        """Get MCP server by ID.

        Args:
            org_id: Organization ID
            server_id: MCP Server ID

        Returns:
            MCPServer instance or None
        """
        stmt = select(MCPServer).where(MCPServer.org_id == org_id, MCPServer.id == server_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_mcp_servers(
        self, org_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[MCPServer]:
        """List all MCP servers for organization.

        Args:
            org_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of MCPServer instances
        """
        stmt = select(MCPServer).where(MCPServer.org_id == org_id).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def rotate_mcp_api_key(self, org_id: UUID, server_id: UUID) -> tuple[MCPServer, str]:
        """Rotate API key for MCP server.

        Args:
            org_id: Organization ID
            server_id: MCP Server ID

        Returns:
            Tuple of (updated MCPServer, new plain API key)

        Raises:
            ValueError: If server not found
        """
        server = await self.get_mcp_server(org_id, server_id)
        if not server:
            raise ValueError(f"MCP Server '{server_id}' not found")

        # Generate new API key
        plain_api_key = f"mcp_{secrets.token_urlsafe(32)}"
        api_key_hash = bcrypt.hash(plain_api_key).encode("utf-8")

        server.api_key_hash = api_key_hash
        await self.session.commit()
        await self.session.refresh(server)

        logger.info(f"Rotated API key for MCP Server {server_id} in org {org_id}")
        return server, plain_api_key

    async def toggle_mcp_server(self, org_id: UUID, server_id: UUID, enable: bool) -> MCPServer:
        """Enable or disable MCP server.

        Args:
            org_id: Organization ID
            server_id: MCP Server ID
            enable: True to enable, False to disable

        Returns:
            Updated MCPServer instance

        Raises:
            ValueError: If server not found
        """
        server = await self.get_mcp_server(org_id, server_id)
        if not server:
            raise ValueError(f"MCP Server '{server_id}' not found")

        from apps.core.models.mcp_server import MCPServerStatus

        server.status = MCPServerStatus.ENABLED if enable else MCPServerStatus.DISABLED
        await self.session.commit()
        await self.session.refresh(server)
        return server

    # ============ Policy Management ============

    async def create_policy(self, org_id: UUID, payload: PolicyCreate) -> Policy:
        """Create a new policy.

        Args:
            org_id: Organization ID
            payload: Policy creation payload

        Returns:
            Created Policy instance
        """
        policy = Policy(
            org_id=org_id,
            name=payload.name,
            effect=payload.effect,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            conditions=payload.conditions,
            field_masks=payload.field_masks,
            enabled=payload.enabled,
        )
        self.session.add(policy)
        await self.session.commit()
        await self.session.refresh(policy)
        return policy

    async def get_policy(self, org_id: UUID, policy_id: UUID) -> Policy | None:
        """Get policy by ID.

        Args:
            org_id: Organization ID
            policy_id: Policy ID

        Returns:
            Policy instance or None
        """
        stmt = select(Policy).where(Policy.org_id == org_id, Policy.id == policy_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_policies(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[Policy]:
        """List all policies for organization.

        Args:
            org_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Policy instances
        """
        stmt = select(Policy).where(Policy.org_id == org_id).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_policy(self, org_id: UUID, policy_id: UUID, payload: PolicyUpdate) -> Policy:
        """Update a policy.

        Args:
            org_id: Organization ID
            policy_id: Policy ID
            payload: Policy update payload

        Returns:
            Updated Policy instance

        Raises:
            ValueError: If policy not found
        """
        policy = await self.get_policy(org_id, policy_id)
        if not policy:
            raise ValueError(f"Policy '{policy_id}' not found")

        if payload.name is not None:
            policy.name = payload.name
        if payload.effect is not None:
            policy.effect = payload.effect
        if payload.resource_type is not None:
            policy.resource_type = payload.resource_type
        if payload.resource_id is not None:
            policy.resource_id = payload.resource_id
        if payload.conditions is not None:
            policy.conditions = payload.conditions
        if payload.field_masks is not None:
            policy.field_masks = payload.field_masks
        if payload.enabled is not None:
            policy.enabled = payload.enabled

        await self.session.commit()
        await self.session.refresh(policy)
        return policy

    async def delete_policy(self, org_id: UUID, policy_id: UUID) -> None:
        """Delete a policy.

        Args:
            org_id: Organization ID
            policy_id: Policy ID

        Raises:
            ValueError: If policy not found
        """
        policy = await self.get_policy(org_id, policy_id)
        if not policy:
            raise ValueError(f"Policy '{policy_id}' not found")

        await self.session.delete(policy)
        await self.session.commit()

    # ============ Tool Invocation Pipeline ============

    async def invoke_tool(
        self, org_id: UUID, tool_id: UUID, user_id: UUID, payload: InvokeIn
    ) -> InvokeOut:
        """Invoke a tool with policy enforcement, rate limiting, and auditing.

        Pipeline steps:
        1. Load tool and check enabled
        2. Check policies (DENY -> 403)
        3. Check rate limit
        4. Load datasource if needed
        5. Execute tool
        6. Apply field masking
        7. Audit and metrics

        Args:
            org_id: Organization ID
            tool_id: Tool ID
            user_id: User ID making the request
            payload: Invocation parameters

        Returns:
            InvokeOut with result data

        Raises:
            HTTPException: Various HTTP errors for different failure modes
        """
        trace_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Step 1: Load tool
            tool = await self.get_tool(org_id, tool_id)
            if not tool:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tool '{tool_id}' not found",
                )
            if not tool.enabled:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tool is disabled",
                )

            # Step 2: Check policies
            user_membership = await self._get_user_membership(org_id, user_id)
            policy_result = await self._check_policies(org_id, tool_id, user_membership)
            if not policy_result["allowed"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied by policy: {policy_result['reason']}",
                )

            # Step 3: Rate limiting
            rate_limit = tool.rate_limit_per_min or 60  # Default 60/min
            if not self.rate_limiter.check_rate_limit(org_id, tool_id, rate_limit):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="سقف فراخوانی این ابزار در دقیقه پر شده است.",
                )

            # Step 4: Execute tool
            result_data = await self._execute_tool(tool, payload.params)

            # Step 5: Apply field masking
            masked = False
            if policy_result.get("field_masks"):
                result_data = self._apply_field_masks(result_data, policy_result["field_masks"])
                masked = True

            # Step 6: Audit (simple logging for MVP)
            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"Tool invocation: trace_id={trace_id}, org_id={org_id}, "
                f"tool_id={tool_id}, user_id={user_id}, latency_ms={latency_ms}, ok=True"
            )

            return InvokeOut(ok=True, data=result_data, masked=masked, trace_id=trace_id)

        except HTTPException:
            raise
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Tool invocation failed: trace_id={trace_id}, org_id={org_id}, "
                f"tool_id={tool_id}, user_id={user_id}, latency_ms={latency_ms}, error={str(e)}"
            )
            return InvokeOut(ok=False, trace_id=trace_id, error=str(e))

    # ============ Helper Methods ============

    def _validate_exec_config(self, tool_type: ToolType, exec_config: dict) -> None:
        """Validate exec_config based on tool type.

        Args:
            tool_type: Type of tool
            exec_config: Execution configuration

        Raises:
            ValueError: If exec_config is invalid
        """
        if tool_type == ToolType.POSTGRES_QUERY:
            if "query_template" not in exec_config:
                raise ValueError("POSTGRES_QUERY requires 'query_template' in exec_config")
        elif tool_type == ToolType.REST_CALL:
            required = ["method", "path"]
            missing = [f for f in required if f not in exec_config]
            if missing:
                raise ValueError(f"REST_CALL requires {missing} in exec_config")

    async def _get_user_membership(self, org_id: UUID, user_id: UUID) -> Membership | None:
        """Get user membership in organization."""
        stmt = select(Membership).where(Membership.org_id == org_id, Membership.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _check_policies(
        self, org_id: UUID, tool_id: UUID, membership: Membership | None
    ) -> dict[str, Any]:
        """Check policies for tool access.

        Returns:
            Dict with 'allowed' (bool), 'reason' (str), and 'field_masks' (dict|None)
        """
        # Get all policies for this tool
        stmt = select(Policy).where(
            Policy.org_id == org_id,
            Policy.resource_type == PolicyResourceType.TOOL,
            Policy.resource_id == tool_id,
            Policy.enabled == True,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        policies = list(result.scalars().all())

        if not policies:
            # No policies = allow by default
            return {"allowed": True, "reason": "No policies defined"}

        # Check each policy
        field_masks = None
        for policy in policies:
            # Check conditions (simple role check for MVP)
            if self._policy_conditions_match(policy, membership):
                if policy.effect == PolicyEffect.DENY:
                    return {
                        "allowed": False,
                        "reason": f"Denied by policy '{policy.name}'",
                    }
                elif policy.effect == PolicyEffect.ALLOW:
                    # Collect field masks
                    if policy.field_masks:
                        if field_masks is None:
                            field_masks = {}
                        field_masks.update(policy.field_masks)

        return {"allowed": True, "reason": "Allowed by policy", "field_masks": field_masks}

    def _policy_conditions_match(self, policy: Policy, membership: Membership | None) -> bool:
        """Check if policy conditions match user membership.

        Args:
            policy: Policy to check
            membership: User membership (None if not a member)

        Returns:
            True if conditions match
        """
        conditions = policy.conditions or {}

        # Check roles_any_of condition
        if "roles_any_of" in conditions:
            required_roles = conditions["roles_any_of"]
            if membership and membership.role in required_roles:
                return True
            return False

        # No conditions or conditions not recognized = match
        return True

    async def _execute_tool(self, tool: Tool, params: dict[str, Any]) -> Any:
        """Execute tool based on its type.

        Args:
            tool: Tool to execute
            params: Parameters for execution

        Returns:
            Execution result data

        Raises:
            Exception: Various exceptions based on execution errors
        """
        if tool.type == ToolType.POSTGRES_QUERY:
            return await self._execute_postgres_query(tool, params)
        elif tool.type == ToolType.REST_CALL:
            return await self._execute_rest_call(tool, params)
        elif tool.type == ToolType.CUSTOM:
            return await self._execute_custom(tool, params)
        else:
            raise ValueError(f"Unsupported tool type: {tool.type}")

    async def _execute_postgres_query(self, tool: Tool, params: dict[str, Any]) -> Any:
        """Execute PostgreSQL query with parameterized template.

        Args:
            tool: Tool with POSTGRES_QUERY type
            params: Query parameters

        Returns:
            Query results as list of dicts
        """
        # Load datasource
        if not tool.datasource_id:
            raise ValueError("Tool requires datasource_id for POSTGRES_QUERY")

        ds_service = DataSourceService(self.session)
        config = await ds_service.load_connection_config(tool.org_id, tool.datasource_id)

        # Get query template from exec_config
        query_template = tool.exec_config.get("query_template")
        if not query_template:
            raise ValueError("Missing query_template in exec_config")

        # Execute query with parameters (psycopg parameterized query)
        conn_str = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

        async with await psycopg.AsyncConnection.connect(conn_str) as conn:
            async with conn.cursor() as cur:
                # Use parameterized query with named parameters
                await cur.execute(query_template, params)
                rows = await cur.fetchall()
                columns = [desc[0] for desc in cur.description] if cur.description else []
                return [dict(zip(columns, row, strict=True)) for row in rows]

    async def _execute_rest_call(self, tool: Tool, params: dict[str, Any]) -> Any:
        """Execute REST API call.

        Args:
            tool: Tool with REST_CALL type
            params: Path parameters and query parameters

        Returns:
            API response data
        """
        # Load datasource
        if not tool.datasource_id:
            raise ValueError("Tool requires datasource_id for REST_CALL")

        ds_service = DataSourceService(self.session)
        config = await ds_service.load_connection_config(tool.org_id, tool.datasource_id)

        # Build request
        method = tool.exec_config.get("method", "GET")
        path_template = tool.exec_config.get("path", "/")
        timeout_ms = tool.exec_config.get("timeout_ms", 5000)

        # Replace path parameters
        path = path_template.format(**params)
        url = f"{config['base_url']}{path}"

        # Prepare headers
        headers = config.get("headers", {})

        # Execute request
        async with httpx.AsyncClient(timeout=timeout_ms / 1000.0) as client:
            response = await client.request(method, url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def _execute_custom(self, tool: Tool, params: dict[str, Any]) -> Any:
        """Execute custom tool (MVP: simple echo).

        Args:
            tool: Tool with CUSTOM type
            params: Custom parameters

        Returns:
            Custom result
        """
        # MVP: Simple echo for demonstration
        return {
            "message": "Custom tool executed",
            "tool_name": tool.name,
            "params": params,
        }

    def _apply_field_masks(self, data: Any, field_masks: dict[str, Any]) -> Any:
        """Apply field masking to response data.

        Args:
            data: Response data (dict, list, or primitive)
            field_masks: Field masking rules (e.g., {"remove": ["phone"]})

        Returns:
            Masked data
        """
        remove_fields = field_masks.get("remove", [])
        if not remove_fields:
            return data

        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k not in remove_fields}
        elif isinstance(data, list):
            return [self._apply_field_masks(item, field_masks) for item in data]
        else:
            return data
