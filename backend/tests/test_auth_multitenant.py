"""Tests for authentication and multi-tenancy features."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.core import app
from apps.core.config import settings


@pytest.fixture
def set_local_env(monkeypatch):
    """Set APP_ENV to local for dev login tests."""
    monkeypatch.setattr(settings, "APP_ENV", "local")


@pytest.fixture
def set_prod_env(monkeypatch):
    """Set APP_ENV to prod for OIDC tests."""
    monkeypatch.setattr(settings, "APP_ENV", "prod")
    # Clear OIDC config
    monkeypatch.setattr(settings, "OIDC_ISSUER", None)
    monkeypatch.setattr(settings, "OIDC_CLIENT_ID", None)
    monkeypatch.setattr(settings, "OIDC_CLIENT_SECRET", None)
    monkeypatch.setattr(settings, "OIDC_REDIRECT_URI", None)


@pytest.mark.asyncio
async def test_dev_login_creates_user_and_org(set_local_env, override_get_db):
    """Test that dev login creates user and organization and returns token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = f"test-{uuid4()}@example.com"
        org_name = f"TestOrg-{uuid4()}"

        response = await client.post(
            "/auth/dev/login",
            json={"email": email, "org_name": org_name},
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "org_id" in data
        assert data["access_token"]  # Token is not empty


@pytest.mark.asyncio
async def test_dev_login_not_available_in_prod(set_prod_env):
    """Test that dev login returns 404 in production."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/dev/login",
            json={"email": "test@example.com", "org_name": "TestOrg"},
        )

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_me_endpoint_with_valid_token(set_local_env, override_get_db):
    """Test /me endpoint with valid Bearer token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First, login to get a token
        email = f"test-{uuid4()}@example.com"
        org_name = f"TestOrg-{uuid4()}"

        login_response = await client.post(
            "/auth/dev/login",
            json={"email": email, "org_name": org_name},
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        # Now call /me with the token
        me_response = await client.get(
            "/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert me_response.status_code == 200
        data = me_response.json()

        assert data["email"] == email
        assert "org_id" in data
        assert "roles" in data
        assert "ORG_ADMIN" in data["roles"]


@pytest.mark.asyncio
async def test_me_endpoint_without_token():
    """Test /me endpoint without token returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/me")

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_org_guard_allows_same_org(set_local_env, override_get_db):
    """Test org guard allows access when user belongs to the organization."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login to get token and org_id
        email = f"test-{uuid4()}@example.com"
        org_name = f"TestOrg-{uuid4()}"

        login_response = await client.post(
            "/auth/dev/login",
            json={"email": email, "org_name": org_name},
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        org_id = login_response.json()["org_id"]

        # Call /orgs/{org_id}/whoami with the same org_id
        response = await client.get(
            f"/orgs/{org_id}/whoami",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == email
        assert data["org_id"] == org_id


@pytest.mark.asyncio
async def test_org_guard_denies_different_org(set_local_env, override_get_db):
    """Test org guard denies access when user doesn't belong to the organization."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login to get token
        email = f"test-{uuid4()}@example.com"
        org_name = f"TestOrg-{uuid4()}"

        login_response = await client.post(
            "/auth/dev/login",
            json={"email": email, "org_name": org_name},
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        # Try to access a different org_id
        different_org_id = str(uuid4())
        response = await client.get(
            f"/orgs/{different_org_id}/whoami",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403


@pytest.mark.asyncio
async def test_oidc_well_known_returns_503_without_config(set_prod_env):
    """Test OIDC well-known endpoint returns 503 when OIDC is not configured."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/auth/oidc/.well-known")

        assert response.status_code == 503
        assert "not fully configured" in response.json()["detail"]


@pytest.mark.asyncio
async def test_oidc_well_known_not_available_in_local():
    """Test OIDC well-known endpoint is not available outside production."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/auth/oidc/.well-known")

        assert response.status_code == 503


@pytest.mark.asyncio
async def test_oidc_exchange_returns_503(set_prod_env):
    """Test OIDC exchange endpoint returns 503 (skeleton implementation)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/oidc/exchange",
            json={"code": "test-code", "state": "test-state"},
        )

        assert response.status_code == 503
