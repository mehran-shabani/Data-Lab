"""Tests for MCP Tool invocation with policies and rate limiting."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from apps.core import app as fastapi_app
from apps.core.models import (
    DataSource,
    Membership,
    Organization,
    Policy,
    Tool,
    User,
)
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
    user = User(email="developer@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_membership(db_session, test_user, test_org):
    """Create a test membership with DEVELOPER role."""
    membership = Membership(
        user_id=test_user.id,
        org_id=test_org.id,
        roles=["DEVELOPER"],
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(membership)
    return membership


@pytest.fixture
def dev_token(test_user, test_org):
    """Create a dev token for testing."""
    return create_access_token(
        user_id=test_user.id,
        email=test_user.email,
        org_id=test_org.id,
        roles=["DEVELOPER"],
    )


@pytest.fixture
def auth_headers(dev_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {dev_token}"}


@pytest.fixture(autouse=True)
def set_master_key_env(monkeypatch):
    """Set SECRETS_MASTER_KEY for tests."""
    test_master_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    monkeypatch.setenv("SECRETS_MASTER_KEY", test_master_key)
    import apps.core.crypto

    apps.core.crypto._master_key = None


@pytest.fixture
async def test_datasource(db_session, test_org):
    """Create a test datasource."""
    from apps.core.crypto import (
        encrypt_with_data_key,
        generate_data_key,
        get_master_key,
        wrap_key_with_master,
    )

    # Create encrypted config
    config = {
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "user": "testuser",
        "password": "testpass",
    }
    data_key = generate_data_key()
    config_enc = encrypt_with_data_key(config, data_key)
    master_key = get_master_key()
    data_key_enc = wrap_key_with_master(data_key, master_key)

    from apps.core.models import DataSourceType

    ds = DataSource(
        org_id=test_org.id,
        name="Test DB",
        type=DataSourceType.POSTGRES,
        connection_config_enc=config_enc,
        data_key_enc=data_key_enc,
        schema_version="v1",
    )
    db_session.add(ds)
    await db_session.commit()
    await db_session.refresh(ds)
    return ds


@pytest.fixture
async def test_tool(db_session, test_org, test_datasource):
    """Create a test tool."""
    from apps.core.models import ToolType

    tool = Tool(
        org_id=test_org.id,
        name="Test Tool",
        type=ToolType.CUSTOM,
        datasource_id=test_datasource.id,
        input_schema={},
        output_schema={},
        exec_config={},
        rate_limit_per_min=10,
        enabled=True,
    )
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)
    return tool


@pytest.mark.asyncio
async def test_invoke_custom_tool_success(
    override_get_db, auth_headers, test_org, test_tool, test_membership
):
    """Test successful invocation of CUSTOM tool."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {"params": {"name": "test"}}

        response = await client.post(
            f"/api/orgs/{test_org.id}/tools/{test_tool.id}/invoke",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "trace_id" in data
        assert data["data"]["message"] == "Custom tool executed"


@pytest.mark.asyncio
async def test_invoke_tool_with_deny_policy(
    override_get_db, auth_headers, test_org, test_tool, test_membership, db_session
):
    """Test invocation blocked by DENY policy."""
    from apps.core.models import PolicyEffect, PolicyResourceType

    # Create DENY policy
    policy = Policy(
        org_id=test_org.id,
        name="Deny All",
        effect=PolicyEffect.DENY,
        resource_type=PolicyResourceType.TOOL,
        resource_id=test_tool.id,
        conditions={"roles_any_of": ["DEVELOPER"]},
        enabled=True,
    )
    db_session.add(policy)
    await db_session.commit()

    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {"params": {}}

        response = await client.post(
            f"/api/orgs/{test_org.id}/tools/{test_tool.id}/invoke",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 403
        assert "policy" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_invoke_tool_with_field_masking(
    override_get_db, auth_headers, test_org, test_tool, test_membership, db_session
):
    """Test invocation with field masking policy."""
    from apps.core.models import PolicyEffect, PolicyResourceType

    # Create ALLOW policy with field masks
    policy = Policy(
        org_id=test_org.id,
        name="Allow with Mask",
        effect=PolicyEffect.ALLOW,
        resource_type=PolicyResourceType.TOOL,
        resource_id=test_tool.id,
        conditions={"roles_any_of": ["DEVELOPER"]},
        field_masks={"remove": ["tool_name"]},
        enabled=True,
    )
    db_session.add(policy)
    await db_session.commit()

    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {"params": {}}

        response = await client.post(
            f"/api/orgs/{test_org.id}/tools/{test_tool.id}/invoke",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["masked"] is True
        # tool_name should be removed from response
        assert "tool_name" not in data["data"]


@pytest.mark.asyncio
async def test_invoke_tool_rate_limit_exceeded(
    override_get_db, auth_headers, test_org, test_tool, test_membership
):
    """Test rate limit enforcement."""
    from apps.mcp.ratelimit import get_rate_limiter

    # Reset rate limiter
    limiter = get_rate_limiter()
    limiter.reset(test_org.id, test_tool.id)

    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {"params": {}}

        # Make requests up to rate limit (10 per minute)
        for i in range(10):
            response = await client.post(
                f"/api/orgs/{test_org.id}/tools/{test_tool.id}/invoke",
                json=payload,
                headers=auth_headers,
            )
            assert response.status_code == 200, f"Request {i + 1} should succeed"

        # Next request should be rate limited
        response = await client.post(
            f"/api/orgs/{test_org.id}/tools/{test_tool.id}/invoke",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 429
        assert "سقف فراخوانی" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invoke_disabled_tool(
    override_get_db, auth_headers, test_org, test_tool, test_membership, db_session
):
    """Test invocation of disabled tool."""
    # Disable tool
    test_tool.enabled = False
    await db_session.commit()

    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {"params": {}}

        response = await client.post(
            f"/api/orgs/{test_org.id}/tools/{test_tool.id}/invoke",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_invoke_nonexistent_tool(override_get_db, auth_headers, test_org, test_membership):
    """Test invocation of non-existent tool."""
    from uuid import uuid4

    fake_tool_id = uuid4()

    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {"params": {}}

        response = await client.post(
            f"/api/orgs/{test_org.id}/tools/{fake_tool_id}/invoke",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_invoke_postgres_query_tool_mock(
    override_get_db, auth_headers, test_org, test_datasource, test_membership, db_session
):
    """Test POSTGRES_QUERY tool invocation with mocked DB connection."""
    from apps.core.models import ToolType

    # Create POSTGRES_QUERY tool
    tool = Tool(
        org_id=test_org.id,
        name="Get Patient",
        type=ToolType.POSTGRES_QUERY,
        datasource_id=test_datasource.id,
        input_schema={},
        output_schema={},
        exec_config={"query_template": "SELECT id, name FROM patients WHERE id = %(id)s"},
        rate_limit_per_min=60,
        enabled=True,
    )
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    # Mock psycopg connection
    with patch("psycopg.AsyncConnection.connect") as mock_connect:
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall = AsyncMock(return_value=[(1, "John Doe")])
        mock_cursor.description = [("id",), ("name",)]
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        mock_connect.return_value.__aenter__.return_value = mock_conn

        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            payload = {"params": {"id": 1}}

            response = await client.post(
                f"/api/orgs/{test_org.id}/tools/{tool.id}/invoke",
                json=payload,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["id"] == 1
            assert data["data"][0]["name"] == "John Doe"
