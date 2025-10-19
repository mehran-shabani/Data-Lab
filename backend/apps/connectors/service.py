"""Service layer for DataSource management with encryption and connectivity checks."""

import logging
from typing import Any
from uuid import UUID

import httpx
import psycopg
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.crypto import (
    decrypt_with_data_key,
    encrypt_with_data_key,
    generate_data_key,
    get_master_key,
    unwrap_key_with_master,
    wrap_key_with_master,
)
from apps.core.models import DataSource, DataSourceType
from apps.core.schemas.datasource import (
    DataSourceCreate,
    DataSourceCreatePostgres,
    DataSourceCreateRest,
    DataSourceTestCheck,
    DataSourceUpdate,
    DataSourceUpdatePostgres,
    DataSourceUpdateRest,
)

from .repo import DataSourceRepository

logger = logging.getLogger(__name__)


class DataSourceService:
    """Service for DataSource business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DataSourceRepository(session)

    async def create_datasource(self, org_id: UUID, payload: DataSourceCreate) -> DataSource:
        """Create a new DataSource with encrypted config.

        Args:
            org_id: Organization ID.
            payload: DataSource creation payload.

        Returns:
            Created DataSource instance.

        Raises:
            ValueError: If datasource name already exists in org.
        """
        # Check if name already exists
        existing = await self.repo.get_by_name(org_id, payload.name)
        if existing:
            raise ValueError(f"DataSource with name '{payload.name}' already exists")

        # Convert payload to connection config dict
        connection_config = self._payload_to_config(payload)

        # Generate data key
        data_key = generate_data_key()

        # Encrypt connection config with data key
        connection_config_enc = encrypt_with_data_key(connection_config, data_key)

        # Wrap data key with master key
        master_key = get_master_key()
        data_key_enc = wrap_key_with_master(data_key, master_key)

        # Create datasource
        ds_type = DataSourceType[payload.type]
        datasource = await self.repo.create(
            org_id=org_id,
            name=payload.name,
            ds_type=ds_type,
            connection_config_enc=connection_config_enc,
            data_key_enc=data_key_enc,
            schema_version=payload.schema_version,
        )

        return datasource

    async def get_datasource(self, org_id: UUID, datasource_id: UUID) -> DataSource | None:
        """Get DataSource by ID.

        Args:
            org_id: Organization ID.
            datasource_id: DataSource ID.

        Returns:
            DataSource instance or None.
        """
        return await self.repo.get_by_id(org_id, datasource_id)

    async def list_datasources(
        self, org_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[DataSource]:
        """List all DataSources for an organization.

        Args:
            org_id: Organization ID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of DataSource instances.
        """
        return await self.repo.list_by_org(org_id, skip, limit)

    async def update_datasource(
        self, org_id: UUID, datasource_id: UUID, payload: DataSourceUpdate
    ) -> DataSource:
        """Update a DataSource.

        Args:
            org_id: Organization ID.
            datasource_id: DataSource ID.
            payload: Update payload.

        Returns:
            Updated DataSource instance.

        Raises:
            ValueError: If datasource not found or type mismatch.
        """
        datasource = await self.repo.get_by_id(org_id, datasource_id)
        if not datasource:
            raise ValueError("DataSource not found")

        # Verify type matches
        if datasource.type.value != payload.type:
            raise ValueError(
                f"Cannot change DataSource type from {datasource.type.value} to {payload.type}"
            )

        # Check if name is being changed and if it conflicts
        if payload.name and payload.name != datasource.name:
            existing = await self.repo.get_by_name(org_id, payload.name)
            if existing:
                raise ValueError(f"DataSource with name '{payload.name}' already exists")

        # Check if sensitive fields are being updated
        needs_re_encryption = self._has_sensitive_updates(payload)

        new_name = payload.name if payload.name else None
        new_config_enc = None
        new_data_key_enc = None

        if needs_re_encryption:
            # Load current config
            current_config = await self.load_connection_config(org_id, datasource_id)

            # Merge updates into current config
            updated_config = self._merge_config_updates(current_config, payload)

            # Re-encrypt with existing data key (or generate new one)
            master_key = get_master_key()
            data_key = unwrap_key_with_master(datasource.data_key_enc, master_key)

            new_config_enc = encrypt_with_data_key(updated_config, data_key)
            # Keep the same data key
            new_data_key_enc = datasource.data_key_enc

        # Update datasource
        updated_ds = await self.repo.update(
            datasource=datasource,
            name=new_name,
            connection_config_enc=new_config_enc,
            data_key_enc=new_data_key_enc,
        )

        return updated_ds

    async def delete_datasource(self, org_id: UUID, datasource_id: UUID) -> None:
        """Delete a DataSource.

        Args:
            org_id: Organization ID.
            datasource_id: DataSource ID.

        Raises:
            ValueError: If datasource not found.
        """
        datasource = await self.repo.get_by_id(org_id, datasource_id)
        if not datasource:
            raise ValueError("DataSource not found")

        await self.repo.delete(datasource)

    async def load_connection_config(self, org_id: UUID, datasource_id: UUID) -> dict[str, Any]:
        """Load and decrypt connection config.

        Args:
            org_id: Organization ID.
            datasource_id: DataSource ID.

        Returns:
            Decrypted connection config as dict.

        Raises:
            ValueError: If datasource not found.
        """
        datasource = await self.repo.get_by_id(org_id, datasource_id)
        if not datasource:
            raise ValueError("DataSource not found")

        # Unwrap data key
        master_key = get_master_key()
        data_key = unwrap_key_with_master(datasource.data_key_enc, master_key)

        # Decrypt config
        connection_config = decrypt_with_data_key(datasource.connection_config_enc, data_key)

        return connection_config

    async def check_connectivity(self, org_id: UUID, datasource_id: UUID) -> tuple[bool, str]:
        """Check connectivity for a saved DataSource.

        Args:
            org_id: Organization ID.
            datasource_id: DataSource ID.

        Returns:
            Tuple of (ok: bool, details: str).
        """
        datasource = await self.repo.get_by_id(org_id, datasource_id)
        if not datasource:
            return False, "DataSource not found"

        config = await self.load_connection_config(org_id, datasource_id)

        if datasource.type == DataSourceType.POSTGRES:
            return await self.check_postgres(config)
        elif datasource.type == DataSourceType.REST:
            return await self.check_rest(config)
        else:
            return False, f"Unknown datasource type: {datasource.type}"

    async def check_connectivity_draft(self, payload: DataSourceTestCheck) -> tuple[bool, str]:
        """Check connectivity for a draft DataSource (without saving).

        Args:
            payload: Test check payload.

        Returns:
            Tuple of (ok: bool, details: str).
        """
        config = self._payload_to_config(payload)

        if payload.type == "POSTGRES":
            return await self.check_postgres(config)
        elif payload.type == "REST":
            return await self.check_rest(config)
        else:
            return False, f"Unknown datasource type: {payload.type}"

    # ===== Private Helper Methods =====

    def _payload_to_config(self, payload: DataSourceCreate | DataSourceTestCheck) -> dict[str, Any]:
        """Convert payload to connection config dict.

        Args:
            payload: Create or test check payload.

        Returns:
            Connection config as dict.
        """
        if isinstance(payload, (DataSourceCreatePostgres,)):
            if payload.dsn:
                return {"dsn": payload.dsn}
            else:
                return {
                    "host": payload.host,
                    "port": payload.port or 5432,
                    "database": payload.database,
                    "username": payload.username,
                    "password": payload.password,
                }
        elif isinstance(payload, (DataSourceCreateRest,)):
            return {
                "base_url": payload.base_url,
                "auth_type": payload.auth_type,
                "headers": payload.headers or {},
                "api_key": payload.api_key,
                "bearer_token": payload.bearer_token,
            }
        else:
            # Handle test check types
            if hasattr(payload, "dsn"):
                if payload.dsn:
                    return {"dsn": payload.dsn}
                else:
                    return {
                        "host": payload.host,
                        "port": payload.port or 5432,
                        "database": payload.database,
                        "username": payload.username,
                        "password": payload.password,
                    }
            else:
                return {
                    "base_url": payload.base_url,
                    "auth_type": payload.auth_type,
                    "headers": payload.headers or {},
                    "api_key": payload.api_key,
                    "bearer_token": payload.bearer_token,
                }

    def _has_sensitive_updates(self, payload: DataSourceUpdate) -> bool:
        """Check if payload contains sensitive field updates.

        Args:
            payload: Update payload.

        Returns:
            True if sensitive fields are being updated.
        """
        if isinstance(payload, DataSourceUpdatePostgres):
            return any(
                [
                    payload.dsn is not None,
                    payload.host is not None,
                    payload.port is not None,
                    payload.database is not None,
                    payload.username is not None,
                    payload.password is not None,
                ]
            )
        elif isinstance(payload, DataSourceUpdateRest):
            return any(
                [
                    payload.base_url is not None,
                    payload.auth_type is not None,
                    payload.headers is not None,
                    payload.api_key is not None,
                    payload.bearer_token is not None,
                ]
            )
        return False

    def _merge_config_updates(
        self, current_config: dict[str, Any], payload: DataSourceUpdate
    ) -> dict[str, Any]:
        """Merge update payload into current config.

        Args:
            current_config: Current decrypted config.
            payload: Update payload.

        Returns:
            Merged config.
        """
        updated_config = current_config.copy()

        if isinstance(payload, DataSourceUpdatePostgres):
            if payload.dsn is not None:
                # If DSN is provided, replace entire config
                updated_config = {"dsn": payload.dsn}
            else:
                # Update individual fields
                if payload.host is not None:
                    updated_config["host"] = payload.host
                if payload.port is not None:
                    updated_config["port"] = payload.port
                if payload.database is not None:
                    updated_config["database"] = payload.database
                if payload.username is not None:
                    updated_config["username"] = payload.username
                if payload.password is not None:
                    updated_config["password"] = payload.password

        elif isinstance(payload, DataSourceUpdateRest):
            if payload.base_url is not None:
                updated_config["base_url"] = payload.base_url
            if payload.auth_type is not None:
                updated_config["auth_type"] = payload.auth_type
            if payload.headers is not None:
                updated_config["headers"] = payload.headers
            if payload.api_key is not None:
                updated_config["api_key"] = payload.api_key
            if payload.bearer_token is not None:
                updated_config["bearer_token"] = payload.bearer_token

        return updated_config

    # ===== Connectivity Check Implementations =====

    async def check_postgres(self, config: dict[str, Any]) -> tuple[bool, str]:
        """Check PostgreSQL connectivity.

        Args:
            config: Connection config dict.

        Returns:
            Tuple of (ok: bool, details: str).
        """
        try:
            if "dsn" in config:
                dsn = config["dsn"]
            else:
                # Build DSN from components
                dsn = (
                    f"postgresql://{config['username']}:{config['password']}"
                    f"@{config['host']}:{config['port']}/{config['database']}"
                )

            # Test connection (synchronous driver for simplicity in MVP)
            conn = psycopg.connect(dsn, connect_timeout=5)
            conn.close()

            return True, "PostgreSQL connection successful"

        except Exception as e:
            logger.warning(f"PostgreSQL connectivity check failed: {e}")
            return False, f"Connection failed: {str(e)}"

    async def check_rest(self, config: dict[str, Any]) -> tuple[bool, str]:
        """Check REST API connectivity.

        Args:
            config: Connection config dict.

        Returns:
            Tuple of (ok: bool, details: str).
        """
        try:
            base_url = config["base_url"]
            auth_type = config.get("auth_type", "NONE")
            headers = config.get("headers", {}).copy()

            # Add authentication headers
            if auth_type == "API_KEY" and config.get("api_key"):
                headers["X-API-Key"] = config["api_key"]
            elif auth_type == "BEARER" and config.get("bearer_token"):
                headers["Authorization"] = f"Bearer {config['bearer_token']}"

            # Test connection with HEAD or GET request
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try HEAD first, fallback to GET
                try:
                    response = await client.head(base_url, headers=headers, follow_redirects=True)
                except Exception:
                    response = await client.get(base_url, headers=headers, follow_redirects=True)

                if response.status_code < 500:
                    return True, f"REST API reachable (status: {response.status_code})"
                else:
                    return False, f"REST API returned error (status: {response.status_code})"

        except httpx.TimeoutException:
            return False, "Connection timeout"
        except Exception as e:
            logger.warning(f"REST connectivity check failed: {e}")
            return False, f"Connection failed: {str(e)}"
