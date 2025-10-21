"""Service layer for DataSource management with encryption and connectivity checks."""

import logging
import time
from typing import Any
from uuid import UUID

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
    DataSourceCreateGraphQL,
    DataSourceCreateMongoDB,
    DataSourceCreatePostgres,
    DataSourceCreateRest,
    DataSourceCreateS3,
    DataSourceTestCheck,
    DataSourceUpdate,
    DataSourceUpdateGraphQL,
    DataSourceUpdateMongoDB,
    DataSourceUpdatePostgres,
    DataSourceUpdateRest,
    DataSourceUpdateS3,
)

from .metrics import metrics_registry
from .registry import make_connector
from .repo import DataSourceRepository
from .resilience import CircuitBreakerOpen, circuit_breaker_registry

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
        """Check connectivity for a saved DataSource using connector.

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
        
        try:
            connector = make_connector(datasource.type.value, config, org_id, datasource_id)
            start_time = time.time()
            
            try:
                ok, details = await connector.ping()
                latency_ms = (time.time() - start_time) * 1000
                
                # Record metrics
                metrics_registry.record_call(org_id, datasource_id, latency_ms, ok)
                
                # Update circuit breaker state in metrics
                breaker = circuit_breaker_registry.get_breaker(org_id, datasource_id)
                metrics_registry.update_state(org_id, datasource_id, breaker.state.value)
                
                return ok, details
            finally:
                await connector.close()
                
        except CircuitBreakerOpen as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"Connectivity check failed for ds_id={datasource_id}: {e}", exc_info=True)
            return False, f"Unexpected error: {str(e)}"

    async def check_connectivity_draft(self, payload: DataSourceTestCheck) -> tuple[bool, str]:
        """Check connectivity for a draft DataSource (without saving).

        Args:
            payload: Test check payload.

        Returns:
            Tuple of (ok: bool, details: str).
        """
        config = self._payload_to_config(payload)
        
        # Use dummy IDs for draft checks (no metrics recorded)
        from uuid import uuid4
        dummy_org_id = uuid4()
        dummy_ds_id = uuid4()
        
        try:
            connector = make_connector(payload.type, config, dummy_org_id, dummy_ds_id)
            
            try:
                ok, details = await connector.ping()
                return ok, details
            finally:
                await connector.close()
                
        except CircuitBreakerOpen as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"Draft connectivity check failed: {e}", exc_info=True)
            return False, f"Unexpected error: {str(e)}"

    # ===== Private Helper Methods =====

    def _payload_to_config(self, payload: DataSourceCreate | DataSourceTestCheck) -> dict[str, Any]:
        """Convert payload to connection config dict.

        Args:
            payload: Create or test check payload.

        Returns:
            Connection config as dict.
        """
        if isinstance(payload, (DataSourceCreatePostgres,)) or (hasattr(payload, "dsn") and hasattr(payload, "host")):
            if hasattr(payload, "dsn") and payload.dsn:
                return {"dsn": payload.dsn}
            else:
                return {
                    "host": payload.host,
                    "port": payload.port or 5432,
                    "database": payload.database,
                    "username": payload.username,
                    "password": payload.password,
                }
        elif isinstance(payload, (DataSourceCreateRest,)) or (hasattr(payload, "base_url") and not hasattr(payload, "uri") and not hasattr(payload, "bucket")):
            return {
                "base_url": payload.base_url,
                "auth_type": payload.auth_type,
                "headers": payload.headers or {},
                "api_key": payload.api_key,
                "bearer_token": payload.bearer_token,
                "timeout_ms": getattr(payload, "timeout_ms", 10000),
            }
        elif isinstance(payload, (DataSourceCreateMongoDB,)) or hasattr(payload, "uri"):
            return {
                "uri": payload.uri,
                "db": payload.db,
                "collection": payload.collection,
                "timeout_ms": getattr(payload, "timeout_ms", 3000),
            }
        elif isinstance(payload, (DataSourceCreateGraphQL,)):
            return {
                "base_url": payload.base_url,
                "auth_type": payload.auth_type,
                "headers": payload.headers or {},
                "api_key": payload.api_key,
                "bearer_token": payload.bearer_token,
                "timeout_ms": payload.timeout_ms,
            }
        elif isinstance(payload, (DataSourceCreateS3,)) or hasattr(payload, "bucket"):
            return {
                "endpoint": payload.endpoint,
                "region": payload.region,
                "bucket": payload.bucket,
                "access_key": payload.access_key,
                "secret_key": payload.secret_key,
                "use_path_style": payload.use_path_style,
                "timeout_ms": getattr(payload, "timeout_ms", 4000),
            }
        else:
            raise ValueError(f"Unsupported payload type: {type(payload)}")

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
        elif isinstance(payload, DataSourceUpdateMongoDB):
            return any(
                [
                    payload.uri is not None,
                    payload.db is not None,
                    payload.collection is not None,
                    payload.timeout_ms is not None,
                ]
            )
        elif isinstance(payload, DataSourceUpdateGraphQL):
            return any(
                [
                    payload.base_url is not None,
                    payload.auth_type is not None,
                    payload.headers is not None,
                    payload.api_key is not None,
                    payload.bearer_token is not None,
                    payload.timeout_ms is not None,
                ]
            )
        elif isinstance(payload, DataSourceUpdateS3):
            return any(
                [
                    payload.endpoint is not None,
                    payload.region is not None,
                    payload.bucket is not None,
                    payload.access_key is not None,
                    payload.secret_key is not None,
                    payload.use_path_style is not None,
                    payload.timeout_ms is not None,
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

        elif isinstance(payload, DataSourceUpdateMongoDB):
            if payload.uri is not None:
                updated_config["uri"] = payload.uri
            if payload.db is not None:
                updated_config["db"] = payload.db
            if payload.collection is not None:
                updated_config["collection"] = payload.collection
            if payload.timeout_ms is not None:
                updated_config["timeout_ms"] = payload.timeout_ms

        elif isinstance(payload, DataSourceUpdateGraphQL):
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
            if payload.timeout_ms is not None:
                updated_config["timeout_ms"] = payload.timeout_ms

        elif isinstance(payload, DataSourceUpdateS3):
            if payload.endpoint is not None:
                updated_config["endpoint"] = payload.endpoint
            if payload.region is not None:
                updated_config["region"] = payload.region
            if payload.bucket is not None:
                updated_config["bucket"] = payload.bucket
            if payload.access_key is not None:
                updated_config["access_key"] = payload.access_key
            if payload.secret_key is not None:
                updated_config["secret_key"] = payload.secret_key
            if payload.use_path_style is not None:
                updated_config["use_path_style"] = payload.use_path_style
            if payload.timeout_ms is not None:
                updated_config["timeout_ms"] = payload.timeout_ms

        return updated_config

    # ===== New Connector Methods =====

    async def sample_datasource(
        self, org_id: UUID, datasource_id: UUID, params: dict[str, Any]
    ) -> Any:
        """Execute sample query/operation on DataSource.

        Args:
            org_id: Organization ID.
            datasource_id: DataSource ID.
            params: Query/operation parameters (connector-specific).

        Returns:
            Sample result.

        Raises:
            ValueError: If datasource not found.
        """
        datasource = await self.repo.get_by_id(org_id, datasource_id)
        if not datasource:
            raise ValueError("DataSource not found")

        config = await self.load_connection_config(org_id, datasource_id)
        
        try:
            connector = make_connector(datasource.type.value, config, org_id, datasource_id)
            start_time = time.time()
            
            try:
                result = await connector.sample(params)
                latency_ms = (time.time() - start_time) * 1000
                
                # Record metrics
                success = result.get("ok", True) if isinstance(result, dict) else True
                metrics_registry.record_call(org_id, datasource_id, latency_ms, success)
                
                # Update circuit breaker state
                breaker = circuit_breaker_registry.get_breaker(org_id, datasource_id)
                metrics_registry.update_state(org_id, datasource_id, breaker.state.value)
                
                return result
            finally:
                await connector.close()
                
        except CircuitBreakerOpen as e:
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"Sample failed for ds_id={datasource_id}: {e}", exc_info=True)
            raise

    def get_datasource_metrics(self, org_id: UUID, datasource_id: UUID) -> dict[str, Any]:
        """Get metrics for a DataSource.

        Args:
            org_id: Organization ID.
            datasource_id: DataSource ID.

        Returns:
            Metrics dict.
        """
        metrics = metrics_registry.get_metrics(org_id, datasource_id)
        return metrics.to_dict()

    async def get_org_health_summary(self, org_id: UUID) -> list[dict[str, Any]]:
        """Get health summary for all DataSources in an organization.

        Args:
            org_id: Organization ID.

        Returns:
            List of health summaries.
        """
        datasources = await self.list_datasources(org_id, skip=0, limit=1000)
        all_metrics = metrics_registry.get_all_for_org(org_id)
        
        health_summary = []
        for ds in datasources:
            metrics = all_metrics.get(ds.id)
            
            if metrics:
                ok = metrics.state != "OPEN" and (
                    metrics.last_ok_ts is not None and
                    (metrics.last_err_ts is None or metrics.last_ok_ts > metrics.last_err_ts)
                )
            else:
                ok = None  # Unknown (never tested)
            
            health_summary.append({
                "ds_id": str(ds.id),
                "name": ds.name,
                "type": ds.type.value,
                "ok": ok,
                "state": metrics.state if metrics else "UNKNOWN",
                "last_ok_ts": metrics.last_ok_ts if metrics else None,
                "last_err_ts": metrics.last_err_ts if metrics else None,
            })
        
        return health_summary
