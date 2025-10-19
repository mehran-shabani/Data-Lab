"""Tests for DataSource connectivity checks."""

from unittest.mock import AsyncMock, MagicMock, patch

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
async def test_check_postgres_connectivity_draft_success(override_get_db, auth_headers, test_org):
    """Test PostgreSQL connectivity check for draft (without saving)."""
    with patch("psycopg.connect") as mock_connect:
        # Mock successful connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            payload = {
                "type": "POSTGRES",
                "dsn": "postgresql://user:pass@localhost:5432/testdb",
            }

            response = await client.post(
                f"/api/orgs/{test_org.id}/datasources/check",
                json=payload,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
            assert "successful" in data["details"].lower()

            # Verify connection was attempted
            mock_connect.assert_called_once()
            mock_conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_check_postgres_connectivity_draft_failure(override_get_db, auth_headers, test_org):
    """Test PostgreSQL connectivity check failure."""
    with patch("psycopg.connect") as mock_connect:
        # Mock connection failure
        mock_connect.side_effect = Exception("Connection refused")

        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            payload = {
                "type": "POSTGRES",
                "host": "invalid-host",
                "port": 5432,
                "database": "testdb",
                "username": "user",
                "password": "pass",
            }

            response = await client.post(
                f"/api/orgs/{test_org.id}/datasources/check",
                json=payload,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is False
            assert "failed" in data["details"].lower()


@pytest.mark.asyncio
async def test_check_rest_connectivity_draft_success(override_get_db, auth_headers, test_org):
    """Test REST API connectivity check for draft."""
    with patch("httpx.AsyncClient") as mock_client_class:
        # Mock successful REST response
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.head.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            payload = {
                "type": "REST",
                "base_url": "https://api.example.com",
                "auth_type": "NONE",
            }

            response = await client.post(
                f"/api/orgs/{test_org.id}/datasources/check",
                json=payload,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
            assert "reachable" in data["details"].lower()


@pytest.mark.asyncio
async def test_check_rest_connectivity_draft_with_api_key(override_get_db, auth_headers, test_org):
    """Test REST API connectivity check with API key authentication."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.head.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            payload = {
                "type": "REST",
                "base_url": "https://api.example.com",
                "auth_type": "API_KEY",
                "api_key": "secret-key-123",
            }

            response = await client.post(
                f"/api/orgs/{test_org.id}/datasources/check",
                json=payload,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True


@pytest.mark.asyncio
async def test_check_rest_connectivity_draft_failure(override_get_db, auth_headers, test_org):
    """Test REST API connectivity check failure."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.head.side_effect = Exception("Connection timeout")
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            payload = {
                "type": "REST",
                "base_url": "https://invalid-url-that-does-not-exist.com",
                "auth_type": "NONE",
            }

            response = await client.post(
                f"/api/orgs/{test_org.id}/datasources/check",
                json=payload,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is False
            assert "failed" in data["details"].lower()


@pytest.mark.asyncio
async def test_check_saved_datasource_connectivity(override_get_db, auth_headers, test_org):
    """Test connectivity check for a saved datasource."""
    with patch("psycopg.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
            # Create datasource
            create_payload = {
                "name": "Test Postgres",
                "type": "POSTGRES",
                "dsn": "postgresql://user:pass@localhost:5432/testdb",
            }

            create_response = await client.post(
                f"/api/orgs/{test_org.id}/datasources/",
                json=create_payload,
                headers=auth_headers,
            )
            assert create_response.status_code == 201
            ds_id = create_response.json()["id"]

            # Check connectivity
            check_response = await client.post(
                f"/api/orgs/{test_org.id}/datasources/{ds_id}/check",
                headers=auth_headers,
            )

            assert check_response.status_code == 200
            data = check_response.json()
            assert data["ok"] is True
            assert "successful" in data["details"].lower()


@pytest.mark.asyncio
async def test_check_connectivity_datasource_not_found(override_get_db, auth_headers, test_org):
    """Test connectivity check for non-existent datasource."""
    import uuid

    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        fake_id = str(uuid.uuid4())
        response = await client.post(
            f"/api/orgs/{test_org.id}/datasources/{fake_id}/check",
            headers=auth_headers,
        )

        assert response.status_code == 404
