"""Router for MCP Manager API."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.deps import (
    CurrentUser,
    get_current_user,
    get_db_session,
    org_guard,
    require_roles,
)
from apps.core.schemas.mcp import (
    InvokeIn,
    InvokeOut,
    MCPServerCreate,
    MCPServerOut,
    PolicyCreate,
    PolicyOut,
    PolicyUpdate,
    ToolCreate,
    ToolOut,
    ToolUpdate,
)

from .service import MCPService

logger = logging.getLogger(__name__)

# Create routers
tools_router = APIRouter(prefix="/orgs/{org_id}/tools", tags=["tools"])
mcp_router = APIRouter(prefix="/orgs/{org_id}/mcp", tags=["mcp"])
policies_router = APIRouter(prefix="/orgs/{org_id}/policies", tags=["policies"])


# ===== Helper Dependencies =====


def get_mcp_service(
    db: AsyncSession = Depends(get_db_session),
) -> MCPService:
    """Get MCP service instance."""
    return MCPService(db)


def require_developer_or_admin():
    """Require either DEVELOPER or ORG_ADMIN role."""
    return require_roles("DEVELOPER", "ORG_ADMIN")


def require_data_steward_or_admin():
    """Require either DATA_STEWARD or ORG_ADMIN role."""
    return require_roles("DATA_STEWARD", "ORG_ADMIN")


# ============ Tools API ============


@tools_router.post(
    "/",
    response_model=ToolOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(org_guard()), Depends(require_developer_or_admin())],
)
async def create_tool(
    org_id: UUID,
    payload: ToolCreate,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> ToolOut:
    """
    Create a new tool.

    Requires: ORG_ADMIN or DEVELOPER role.

    Args:
        org_id: Organization ID from path
        payload: Tool creation payload
        service: MCP service
        current_user: Current authenticated user

    Returns:
        Created Tool

    Raises:
        HTTPException: 400 if validation fails or name conflicts
    """
    try:
        tool = await service.create_tool(org_id, payload)
        return ToolOut.model_validate(tool)
    except ValueError as e:
        logger.warning(f"Tool creation failed for org {org_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error creating Tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Tool",
        ) from e


@tools_router.get(
    "/",
    response_model=list[ToolOut],
    dependencies=[Depends(org_guard()), Depends(require_developer_or_admin())],
)
async def list_tools(
    org_id: UUID,
    skip: int = 0,
    limit: int = 100,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[ToolOut]:
    """
    List all tools for organization.

    Requires: ORG_ADMIN or DEVELOPER role.

    Args:
        org_id: Organization ID from path
        skip: Number of records to skip
        limit: Maximum number of records to return
        service: MCP service
        current_user: Current authenticated user

    Returns:
        List of Tools
    """
    tools = await service.list_tools(org_id, skip, limit)
    return [ToolOut.model_validate(t) for t in tools]


@tools_router.get(
    "/{tool_id}",
    response_model=ToolOut,
    dependencies=[Depends(org_guard()), Depends(require_developer_or_admin())],
)
async def get_tool(
    org_id: UUID,
    tool_id: UUID,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> ToolOut:
    """
    Get tool by ID.

    Requires: ORG_ADMIN or DEVELOPER role.

    Args:
        org_id: Organization ID from path
        tool_id: Tool ID from path
        service: MCP service
        current_user: Current authenticated user

    Returns:
        Tool details

    Raises:
        HTTPException: 404 if tool not found
    """
    tool = await service.get_tool(org_id, tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_id}' not found",
        )
    return ToolOut.model_validate(tool)


@tools_router.put(
    "/{tool_id}",
    response_model=ToolOut,
    dependencies=[Depends(org_guard()), Depends(require_developer_or_admin())],
)
async def update_tool(
    org_id: UUID,
    tool_id: UUID,
    payload: ToolUpdate,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> ToolOut:
    """
    Update a tool.

    Requires: ORG_ADMIN or DEVELOPER role.

    Args:
        org_id: Organization ID from path
        tool_id: Tool ID from path
        payload: Tool update payload
        service: MCP service
        current_user: Current authenticated user

    Returns:
        Updated Tool

    Raises:
        HTTPException: 404 if tool not found, 400 if validation fails
    """
    try:
        tool = await service.update_tool(org_id, tool_id, payload)
        return ToolOut.model_validate(tool)
    except ValueError as e:
        logger.warning(f"Tool update failed for {tool_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error updating Tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Tool",
        ) from e


@tools_router.delete(
    "/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(org_guard()), Depends(require_developer_or_admin())],
)
async def delete_tool(
    org_id: UUID,
    tool_id: UUID,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    """
    Delete a tool.

    Requires: ORG_ADMIN or DEVELOPER role.

    Args:
        org_id: Organization ID from path
        tool_id: Tool ID from path
        service: MCP service
        current_user: Current authenticated user

    Raises:
        HTTPException: 404 if tool not found
    """
    try:
        await service.delete_tool(org_id, tool_id)
    except ValueError as e:
        logger.warning(f"Tool deletion failed for {tool_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@tools_router.post(
    "/{tool_id}/invoke",
    response_model=InvokeOut,
    dependencies=[Depends(org_guard())],
)
async def invoke_tool(
    org_id: UUID,
    tool_id: UUID,
    payload: InvokeIn,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> InvokeOut:
    """
    Invoke a tool with policy enforcement and rate limiting.

    Requires: Valid user token (role-based access via policies).

    Args:
        org_id: Organization ID from path
        tool_id: Tool ID from path
        payload: Invocation parameters
        service: MCP service
        current_user: Current authenticated user

    Returns:
        Invocation result with trace_id

    Raises:
        HTTPException: Various errors (403 policy deny, 429 rate limit, 404 not found)
    """
    return await service.invoke_tool(org_id, tool_id, current_user.user_id, payload)


# ============ MCP Servers API ============


@mcp_router.post(
    "/servers",
    response_model=MCPServerOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(org_guard()), Depends(require_roles("ORG_ADMIN"))],
)
async def create_mcp_server(
    org_id: UUID,
    payload: MCPServerCreate,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> MCPServerOut:
    """
    Create a new MCP server with API key.

    Requires: ORG_ADMIN role.

    Args:
        org_id: Organization ID from path
        payload: MCP server creation payload
        service: MCP service
        current_user: Current authenticated user

    Returns:
        Created MCP Server with plain_api_key (one-time display)

    Raises:
        HTTPException: 400 if name conflicts
    """
    try:
        server, plain_api_key = await service.create_mcp_server(org_id, payload)
        out = MCPServerOut.model_validate(server)
        out.plain_api_key = plain_api_key
        return out
    except ValueError as e:
        logger.warning(f"MCP Server creation failed for org {org_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error creating MCP Server: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create MCP Server",
        ) from e


@mcp_router.get(
    "/servers",
    response_model=list[MCPServerOut],
    dependencies=[Depends(org_guard()), Depends(require_roles("ORG_ADMIN"))],
)
async def list_mcp_servers(
    org_id: UUID,
    skip: int = 0,
    limit: int = 100,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[MCPServerOut]:
    """
    List all MCP servers for organization.

    Requires: ORG_ADMIN role.

    Args:
        org_id: Organization ID from path
        skip: Number of records to skip
        limit: Maximum number of records to return
        service: MCP service
        current_user: Current authenticated user

    Returns:
        List of MCP Servers
    """
    servers = await service.list_mcp_servers(org_id, skip, limit)
    return [MCPServerOut.model_validate(s) for s in servers]


@mcp_router.get(
    "/servers/{server_id}",
    response_model=MCPServerOut,
    dependencies=[Depends(org_guard()), Depends(require_roles("ORG_ADMIN"))],
)
async def get_mcp_server(
    org_id: UUID,
    server_id: UUID,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> MCPServerOut:
    """
    Get MCP server by ID.

    Requires: ORG_ADMIN role.

    Args:
        org_id: Organization ID from path
        server_id: MCP Server ID from path
        service: MCP service
        current_user: Current authenticated user

    Returns:
        MCP Server details

    Raises:
        HTTPException: 404 if server not found
    """
    server = await service.get_mcp_server(org_id, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found",
        )
    return MCPServerOut.model_validate(server)


@mcp_router.post(
    "/servers/{server_id}/rotate-key",
    response_model=MCPServerOut,
    dependencies=[Depends(org_guard()), Depends(require_roles("ORG_ADMIN"))],
)
async def rotate_mcp_server_key(
    org_id: UUID,
    server_id: UUID,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> MCPServerOut:
    """
    Rotate API key for MCP server.

    Requires: ORG_ADMIN role.

    Args:
        org_id: Organization ID from path
        server_id: MCP Server ID from path
        service: MCP service
        current_user: Current authenticated user

    Returns:
        Updated MCP Server with new plain_api_key (one-time display)

    Raises:
        HTTPException: 404 if server not found
    """
    try:
        server, plain_api_key = await service.rotate_mcp_api_key(org_id, server_id)
        out = MCPServerOut.model_validate(server)
        out.plain_api_key = plain_api_key
        return out
    except ValueError as e:
        logger.warning(f"MCP Server key rotation failed for {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@mcp_router.post(
    "/servers/{server_id}/enable",
    response_model=MCPServerOut,
    dependencies=[Depends(org_guard()), Depends(require_roles("ORG_ADMIN"))],
)
async def enable_mcp_server(
    org_id: UUID,
    server_id: UUID,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> MCPServerOut:
    """
    Enable MCP server.

    Requires: ORG_ADMIN role.

    Args:
        org_id: Organization ID from path
        server_id: MCP Server ID from path
        service: MCP service
        current_user: Current authenticated user

    Returns:
        Updated MCP Server

    Raises:
        HTTPException: 404 if server not found
    """
    try:
        server = await service.toggle_mcp_server(org_id, server_id, enable=True)
        return MCPServerOut.model_validate(server)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@mcp_router.post(
    "/servers/{server_id}/disable",
    response_model=MCPServerOut,
    dependencies=[Depends(org_guard()), Depends(require_roles("ORG_ADMIN"))],
)
async def disable_mcp_server(
    org_id: UUID,
    server_id: UUID,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> MCPServerOut:
    """
    Disable MCP server.

    Requires: ORG_ADMIN role.

    Args:
        org_id: Organization ID from path
        server_id: MCP Server ID from path
        service: MCP service
        current_user: Current authenticated user

    Returns:
        Updated MCP Server

    Raises:
        HTTPException: 404 if server not found
    """
    try:
        server = await service.toggle_mcp_server(org_id, server_id, enable=False)
        return MCPServerOut.model_validate(server)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


# ============ Policies API ============


@policies_router.post(
    "/",
    response_model=PolicyOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(org_guard()), Depends(require_data_steward_or_admin())],
)
async def create_policy(
    org_id: UUID,
    payload: PolicyCreate,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> PolicyOut:
    """
    Create a new policy.

    Requires: ORG_ADMIN or DATA_STEWARD role.

    Args:
        org_id: Organization ID from path
        payload: Policy creation payload
        service: MCP service
        current_user: Current authenticated user

    Returns:
        Created Policy

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        policy = await service.create_policy(org_id, payload)
        return PolicyOut.model_validate(policy)
    except ValueError as e:
        logger.warning(f"Policy creation failed for org {org_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error creating Policy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Policy",
        ) from e


@policies_router.get(
    "/",
    response_model=list[PolicyOut],
    dependencies=[Depends(org_guard()), Depends(require_data_steward_or_admin())],
)
async def list_policies(
    org_id: UUID,
    skip: int = 0,
    limit: int = 100,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[PolicyOut]:
    """
    List all policies for organization.

    Requires: ORG_ADMIN or DATA_STEWARD role.

    Args:
        org_id: Organization ID from path
        skip: Number of records to skip
        limit: Maximum number of records to return
        service: MCP service
        current_user: Current authenticated user

    Returns:
        List of Policies
    """
    policies = await service.list_policies(org_id, skip, limit)
    return [PolicyOut.model_validate(p) for p in policies]


@policies_router.get(
    "/{policy_id}",
    response_model=PolicyOut,
    dependencies=[Depends(org_guard()), Depends(require_data_steward_or_admin())],
)
async def get_policy(
    org_id: UUID,
    policy_id: UUID,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> PolicyOut:
    """
    Get policy by ID.

    Requires: ORG_ADMIN or DATA_STEWARD role.

    Args:
        org_id: Organization ID from path
        policy_id: Policy ID from path
        service: MCP service
        current_user: Current authenticated user

    Returns:
        Policy details

    Raises:
        HTTPException: 404 if policy not found
    """
    policy = await service.get_policy(org_id, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy '{policy_id}' not found",
        )
    return PolicyOut.model_validate(policy)


@policies_router.put(
    "/{policy_id}",
    response_model=PolicyOut,
    dependencies=[Depends(org_guard()), Depends(require_data_steward_or_admin())],
)
async def update_policy(
    org_id: UUID,
    policy_id: UUID,
    payload: PolicyUpdate,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> PolicyOut:
    """
    Update a policy.

    Requires: ORG_ADMIN or DATA_STEWARD role.

    Args:
        org_id: Organization ID from path
        policy_id: Policy ID from path
        payload: Policy update payload
        service: MCP service
        current_user: Current authenticated user

    Returns:
        Updated Policy

    Raises:
        HTTPException: 404 if policy not found, 400 if validation fails
    """
    try:
        policy = await service.update_policy(org_id, policy_id, payload)
        return PolicyOut.model_validate(policy)
    except ValueError as e:
        logger.warning(f"Policy update failed for {policy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error updating Policy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Policy",
        ) from e


@policies_router.delete(
    "/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(org_guard()), Depends(require_data_steward_or_admin())],
)
async def delete_policy(
    org_id: UUID,
    policy_id: UUID,
    service: MCPService = Depends(get_mcp_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    """
    Delete a policy.

    Requires: ORG_ADMIN or DATA_STEWARD role.

    Args:
        org_id: Organization ID from path
        policy_id: Policy ID from path
        service: MCP service
        current_user: Current authenticated user

    Raises:
        HTTPException: 404 if policy not found
    """
    try:
        await service.delete_policy(org_id, policy_id)
    except ValueError as e:
        logger.warning(f"Policy deletion failed for {policy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
