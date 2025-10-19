"""Tests for MCP Server CRUD operations."""

import pytest
from httpx import AsyncClient

from apps.core import app as fastapi_app
from apps.core.models import Membership, Organization, User
from apps.core.security import create_access_token


@pytest.fixture
async def test_org(db_session):
    """Create a test organization."""
    org = Organization(name="Test Org", plan="free")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_user(db_session, test_org):
    """Create a test user."""
    user = User(email="admin@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_membership(db_session, test_user, test_org):
    """Create a test membership with ORG_ADMIN role."""
    membership = Membership(
        user_id=test_user.id,
        org_id=test_org.id,
        roles=["ORG_ADMIN"],
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(membership)
    return membership


@pytest.fixture
def admin_token(test_user, test_org):
    """Create an admin token for testing."""
    return create_access_token(
        user_id=test_user.id,
        email=test_user.email,
        org_id=test_org.id,
        roles=["ORG_ADMIN"],
    )


@pytest.fixture
def auth_headers(admin_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.mark.asyncio
async def test_create_mcp_server(override_get_db, auth_headers, test_org, test_membership):
    """Test creating an MCP server."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {"name": "Test MCP Server"}

        response = await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test MCP Server"
        assert data["status"] == "ENABLED"
        assert "plain_api_key" in data
        assert data["plain_api_key"].startswith("mcp_")
        assert "id" in data


@pytest.mark.asyncio
async def test_create_mcp_server_duplicate_name(
    override_get_db, auth_headers, test_org, test_membership
):
    """Test creating MCP server with duplicate name."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {"name": "Duplicate Server"}

        # First creation
        response1 = await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers",
            json=payload,
            headers=auth_headers,
        )
        assert response1.status_code == 201

        # Second creation with same name
        response2 = await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers",
            json=payload,
            headers=auth_headers,
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_list_mcp_servers(override_get_db, auth_headers, test_org, test_membership):
    """Test listing MCP servers."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create a server first
        payload = {"name": "List Test Server"}
        await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers",
            json=payload,
            headers=auth_headers,
        )

        # List servers
        response = await client.get(
            f"/api/orgs/{test_org.id}/mcp/servers",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # plain_api_key should NOT be in list response
        assert "plain_api_key" not in data[0] or data[0]["plain_api_key"] is None


@pytest.mark.asyncio
async def test_get_mcp_server(override_get_db, auth_headers, test_org, test_membership):
    """Test getting a specific MCP server."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create a server first
        payload = {"name": "Get Test Server"}
        create_response = await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers",
            json=payload,
            headers=auth_headers,
        )
        server_id = create_response.json()["id"]

        # Get server
        response = await client.get(
            f"/api/orgs/{test_org.id}/mcp/servers/{server_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == server_id
        assert data["name"] == "Get Test Server"
        # plain_api_key should NOT be in get response (only on create/rotate)
        assert "plain_api_key" not in data or data["plain_api_key"] is None


@pytest.mark.asyncio
async def test_rotate_mcp_server_key(override_get_db, auth_headers, test_org, test_membership):
    """Test rotating MCP server API key."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create a server first
        payload = {"name": "Rotate Test Server"}
        create_response = await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers",
            json=payload,
            headers=auth_headers,
        )
        server_id = create_response.json()["id"]
        original_key = create_response.json()["plain_api_key"]

        # Rotate key
        response = await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers/{server_id}/rotate-key",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "plain_api_key" in data
        new_key = data["plain_api_key"]
        assert new_key != original_key
        assert new_key.startswith("mcp_")


@pytest.mark.asyncio
async def test_enable_mcp_server(override_get_db, auth_headers, test_org, test_membership):
    """Test enabling MCP server."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create a server
        payload = {"name": "Enable Test Server"}
        create_response = await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers",
            json=payload,
            headers=auth_headers,
        )
        server_id = create_response.json()["id"]

        # Disable first
        await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers/{server_id}/disable",
            headers=auth_headers,
        )

        # Enable
        response = await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers/{server_id}/enable",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ENABLED"


@pytest.mark.asyncio
async def test_disable_mcp_server(override_get_db, auth_headers, test_org, test_membership):
    """Test disabling MCP server."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create a server
        payload = {"name": "Disable Test Server"}
        create_response = await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers",
            json=payload,
            headers=auth_headers,
        )
        server_id = create_response.json()["id"]

        # Disable
        response = await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers/{server_id}/disable",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DISABLED"


@pytest.mark.asyncio
async def test_mcp_server_requires_admin_role(override_get_db, test_org):
    """Test that MCP server operations require ORG_ADMIN role."""
    # Create a user with DEVELOPER role
    from apps.core import app as app

    user = User(email="dev@example.com", hashed_password="hashed")
    from apps.core.db import get_db

    async for db in get_db():
        db.add(user)
        await db.commit()
        await db.refresh(user)

        membership = Membership(
            user_id=user.id,
            org_id=test_org.id,
            roles=["DEVELOPER"],
        )
        db.add(membership)
        await db.commit()
        break

    dev_token = create_access_token(
        user_id=user.id,
        email=user.email,
        org_id=test_org.id,
        roles=["DEVELOPER"],
    )
    dev_headers = {"Authorization": f"Bearer {dev_token}"}

    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {"name": "Test Server"}

        response = await client.post(
            f"/api/orgs/{test_org.id}/mcp/servers",
            json=payload,
            headers=dev_headers,
        )

        # Should be forbidden
        assert response.status_code == 403
