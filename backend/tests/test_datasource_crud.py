"""Tests for DataSource CRUD operations."""

import uuid

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
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_membership(db_session, test_user, test_org):
    """Create a test membership."""
    membership = Membership(
        user_id=test_user.id,
        org_id=test_org.id,
        roles=["DATA_STEWARD"],
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
        roles=["DATA_STEWARD"],
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


@pytest.mark.asyncio
async def test_create_postgres_datasource_with_dsn(
    override_get_db, auth_headers, test_org
):
    """Test creating a PostgreSQL DataSource with DSN."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {
            "name": "Test Postgres",
            "type": "POSTGRES",
            "dsn": "postgresql://user:pass@localhost:5432/testdb",
            "schema_version": "v1",
        }

        response = await client.post(
            f"/api/orgs/{test_org.id}/datasources/",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Postgres"
        assert data["type"] == "POSTGRES"
        assert data["schema_version"] == "v1"
        assert "id" in data
        assert "created_at" in data
        # Ensure no secrets in response
        assert "dsn" not in data
        assert "password" not in data


@pytest.mark.asyncio
async def test_create_postgres_datasource_with_explicit_fields(
    override_get_db, auth_headers, test_org
):
    """Test creating a PostgreSQL DataSource with explicit fields."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {
            "name": "Test Postgres Explicit",
            "type": "POSTGRES",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "testuser",
            "password": "testpass",
        }

        response = await client.post(
            f"/api/orgs/{test_org.id}/datasources/",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Postgres Explicit"
        assert data["type"] == "POSTGRES"
        # No secrets in response
        assert "password" not in data


@pytest.mark.asyncio
async def test_create_rest_datasource(override_get_db, auth_headers, test_org):
    """Test creating a REST DataSource."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {
            "name": "Test REST",
            "type": "REST",
            "base_url": "https://api.example.com",
            "auth_type": "API_KEY",
            "api_key": "secret-api-key-123",
            "headers": {"X-Custom": "value"},
        }

        response = await client.post(
            f"/api/orgs/{test_org.id}/datasources/",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test REST"
        assert data["type"] == "REST"
        # No secrets in response
        assert "api_key" not in data
        assert "headers" not in data


@pytest.mark.asyncio
async def test_create_datasource_duplicate_name(
    override_get_db, auth_headers, test_org, db_session
):
    """Test that creating datasource with duplicate name fails."""
    # Create first datasource
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        payload = {
            "name": "Duplicate Name",
            "type": "POSTGRES",
            "dsn": "postgresql://user:pass@localhost:5432/testdb",
        }

        response1 = await client.post(
            f"/api/orgs/{test_org.id}/datasources/",
            json=payload,
            headers=auth_headers,
        )
        assert response1.status_code == 201

        # Try to create second with same name
        response2 = await client.post(
            f"/api/orgs/{test_org.id}/datasources/",
            json=payload,
            headers=auth_headers,
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_datasources(override_get_db, auth_headers, test_org, db_session):
    """Test listing datasources."""
    # Create multiple datasources
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        for i in range(3):
            payload = {
                "name": f"Datasource {i}",
                "type": "POSTGRES",
                "dsn": f"postgresql://user:pass@localhost:5432/db{i}",
            }
            await client.post(
                f"/api/orgs/{test_org.id}/datasources/",
                json=payload,
                headers=auth_headers,
            )

        # List datasources
        response = await client.get(
            f"/api/orgs/{test_org.id}/datasources/",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("name" in ds for ds in data)
        assert all("type" in ds for ds in data)


@pytest.mark.asyncio
async def test_get_datasource(override_get_db, auth_headers, test_org):
    """Test getting a single datasource."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create datasource
        payload = {
            "name": "Get Test",
            "type": "REST",
            "base_url": "https://api.example.com",
            "auth_type": "NONE",
        }
        create_response = await client.post(
            f"/api/orgs/{test_org.id}/datasources/",
            json=payload,
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        ds_id = create_response.json()["id"]

        # Get datasource
        get_response = await client.get(
            f"/api/orgs/{test_org.id}/datasources/{ds_id}",
            headers=auth_headers,
        )

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == ds_id
        assert data["name"] == "Get Test"


@pytest.mark.asyncio
async def test_get_datasource_not_found(override_get_db, auth_headers, test_org):
    """Test getting non-existent datasource returns 404."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/orgs/{test_org.id}/datasources/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_datasource_name(override_get_db, auth_headers, test_org):
    """Test updating datasource name."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create datasource
        payload = {
            "name": "Original Name",
            "type": "POSTGRES",
            "dsn": "postgresql://user:pass@localhost:5432/testdb",
        }
        create_response = await client.post(
            f"/api/orgs/{test_org.id}/datasources/",
            json=payload,
            headers=auth_headers,
        )
        ds_id = create_response.json()["id"]

        # Update name
        update_payload = {
            "type": "POSTGRES",
            "name": "Updated Name",
        }
        update_response = await client.put(
            f"/api/orgs/{test_org.id}/datasources/{ds_id}",
            json=update_payload,
            headers=auth_headers,
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_datasource(override_get_db, auth_headers, test_org):
    """Test deleting a datasource."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create datasource
        payload = {
            "name": "To Delete",
            "type": "POSTGRES",
            "dsn": "postgresql://user:pass@localhost:5432/testdb",
        }
        create_response = await client.post(
            f"/api/orgs/{test_org.id}/datasources/",
            json=payload,
            headers=auth_headers,
        )
        ds_id = create_response.json()["id"]

        # Delete datasource
        delete_response = await client.delete(
            f"/api/orgs/{test_org.id}/datasources/{ds_id}",
            headers=auth_headers,
        )

        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = await client.get(
            f"/api/orgs/{test_org.id}/datasources/{ds_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_org_isolation(override_get_db, test_org, db_session):
    """Test that datasources are isolated per organization."""
    # Create second org
    org2 = Organization(name="Org 2", plan="free")
    db_session.add(org2)
    await db_session.commit()
    await db_session.refresh(org2)

    # Create user for org2
    user2 = User(email="user2@example.com", hashed_password="hashed")
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user2)

    # Create membership for org2
    membership2 = Membership(
        user_id=user2.id,
        org_id=org2.id,
        roles=["DATA_STEWARD"],
    )
    db_session.add(membership2)
    await db_session.commit()

    # Create token for org2
    token2 = create_access_token(
        user_id=user2.id,
        email=user2.email,
        org_id=org2.id,
        roles=["DATA_STEWARD"],
    )
    headers2 = {"Authorization": f"Bearer {token2}"}

    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        # Create datasource in org1
        from apps.core.security import create_access_token as create_token

        user1 = User(email="user1@example.com", hashed_password="hashed")
        db_session.add(user1)
        await db_session.commit()
        await db_session.refresh(user1)

        membership1 = Membership(
            user_id=user1.id,
            org_id=test_org.id,
            roles=["DATA_STEWARD"],
        )
        db_session.add(membership1)
        await db_session.commit()

        token1 = create_token(
            user_id=user1.id,
            email=user1.email,
            org_id=test_org.id,
            roles=["DATA_STEWARD"],
        )
        headers1 = {"Authorization": f"Bearer {token1}"}

        payload = {
            "name": "Org1 DS",
            "type": "POSTGRES",
            "dsn": "postgresql://user:pass@localhost:5432/testdb",
        }
        create_response = await client.post(
            f"/api/orgs/{test_org.id}/datasources/",
            json=payload,
            headers=headers1,
        )
        assert create_response.status_code == 201
        ds_id = create_response.json()["id"]

        # Try to access from org2 - should fail (403)
        get_response = await client.get(
            f"/api/orgs/{test_org.id}/datasources/{ds_id}",
            headers=headers2,
        )
        assert get_response.status_code == 403
