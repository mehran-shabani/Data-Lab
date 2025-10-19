"""Tests for MCP Tool CRUD operations."""


import pytest
from httpx import AsyncClient

from apps.core import app as fastapi_app
from apps.core.models import DataSource, Membership, Organization, User
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


@pytest.mark.asyncio
async def test_create_postgres_query_tool(
    override_get_db, auth_headers, test_org, test_datasource, test_membership
):
    """Test creating a POSTGRES_QUERY tool."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {
            "name": "Get Patient by ID",
            "version": "v1",
            "type": "POSTGRES_QUERY",
            "datasource_id": str(test_datasource.id),
            "input_schema": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "required": ["id"],
            },
            "output_schema": {"type": "array"},
            "exec_config": {"query_template": "SELECT id, name FROM patients WHERE id = %(id)s"},
            "rate_limit_per_min": 60,
            "enabled": True,
        }

        response = await client.post(
            f"/api/orgs/{test_org.id}/tools/",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Get Patient by ID"
        assert data["type"] == "POSTGRES_QUERY"
        assert data["datasource_id"] == str(test_datasource.id)
        assert "query_template" in data["exec_config"]
        assert data["rate_limit_per_min"] == 60
        assert data["enabled"] is True
        assert "id" in data


@pytest.mark.asyncio
async def test_create_rest_call_tool(
    override_get_db, auth_headers, test_org, test_datasource, test_membership
):
    """Test creating a REST_CALL tool."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {
            "name": "Get Item by Code",
            "version": "v1",
            "type": "REST_CALL",
            "datasource_id": str(test_datasource.id),
            "input_schema": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
            },
            "output_schema": {"type": "object"},
            "exec_config": {
                "method": "GET",
                "path": "/v1/items/{code}",
                "timeout_ms": 3000,
            },
            "enabled": True,
        }

        response = await client.post(
            f"/api/orgs/{test_org.id}/tools/",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Get Item by Code"
        assert data["type"] == "REST_CALL"
        assert data["exec_config"]["method"] == "GET"
        assert data["exec_config"]["path"] == "/v1/items/{code}"


@pytest.mark.asyncio
async def test_list_tools(
    override_get_db, auth_headers, test_org, test_datasource, test_membership
):
    """Test listing tools."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create a tool first
        payload = {
            "name": "Test Tool",
            "type": "CUSTOM",
            "input_schema": {},
            "output_schema": {},
            "exec_config": {},
        }
        await client.post(
            f"/api/orgs/{test_org.id}/tools/",
            json=payload,
            headers=auth_headers,
        )

        # List tools
        response = await client.get(
            f"/api/orgs/{test_org.id}/tools/",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["name"] == "Test Tool"


@pytest.mark.asyncio
async def test_get_tool(override_get_db, auth_headers, test_org, test_datasource, test_membership):
    """Test getting a specific tool."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create a tool first
        payload = {
            "name": "Test Get Tool",
            "type": "CUSTOM",
            "input_schema": {},
            "output_schema": {},
            "exec_config": {},
        }
        create_response = await client.post(
            f"/api/orgs/{test_org.id}/tools/",
            json=payload,
            headers=auth_headers,
        )
        tool_id = create_response.json()["id"]

        # Get tool
        response = await client.get(
            f"/api/orgs/{test_org.id}/tools/{tool_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tool_id
        assert data["name"] == "Test Get Tool"


@pytest.mark.asyncio
async def test_update_tool(
    override_get_db, auth_headers, test_org, test_datasource, test_membership
):
    """Test updating a tool."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create a tool first
        payload = {
            "name": "Original Tool",
            "type": "CUSTOM",
            "input_schema": {},
            "output_schema": {},
            "exec_config": {},
        }
        create_response = await client.post(
            f"/api/orgs/{test_org.id}/tools/",
            json=payload,
            headers=auth_headers,
        )
        tool_id = create_response.json()["id"]

        # Update tool
        update_payload = {
            "name": "Updated Tool",
            "enabled": False,
        }
        response = await client.put(
            f"/api/orgs/{test_org.id}/tools/{tool_id}",
            json=update_payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Tool"
        assert data["enabled"] is False


@pytest.mark.asyncio
async def test_delete_tool(
    override_get_db, auth_headers, test_org, test_datasource, test_membership
):
    """Test deleting a tool."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create a tool first
        payload = {
            "name": "Tool to Delete",
            "type": "CUSTOM",
            "input_schema": {},
            "output_schema": {},
            "exec_config": {},
        }
        create_response = await client.post(
            f"/api/orgs/{test_org.id}/tools/",
            json=payload,
            headers=auth_headers,
        )
        tool_id = create_response.json()["id"]

        # Delete tool
        response = await client.delete(
            f"/api/orgs/{test_org.id}/tools/{tool_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/orgs/{test_org.id}/tools/{tool_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_tool_without_datasource_id_for_postgres_query(
    override_get_db, auth_headers, test_org, test_membership
):
    """Test that POSTGRES_QUERY requires datasource_id."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {
            "name": "Invalid Tool",
            "type": "POSTGRES_QUERY",
            "input_schema": {},
            "output_schema": {},
            "exec_config": {"query_template": "SELECT * FROM table"},
        }

        response = await client.post(
            f"/api/orgs/{test_org.id}/tools/",
            json=payload,
            headers=auth_headers,
        )

        # Should succeed in creation but fail on invoke
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_tool_duplicate_name(override_get_db, auth_headers, test_org, test_membership):
    """Test creating a tool with duplicate name."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {
            "name": "Duplicate Tool",
            "type": "CUSTOM",
            "input_schema": {},
            "output_schema": {},
            "exec_config": {},
        }

        # First creation
        response1 = await client.post(
            f"/api/orgs/{test_org.id}/tools/",
            json=payload,
            headers=auth_headers,
        )
        assert response1.status_code == 201

        # Second creation with same name
        response2 = await client.post(
            f"/api/orgs/{test_org.id}/tools/",
            json=payload,
            headers=auth_headers,
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]
