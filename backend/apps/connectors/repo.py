"""Repository for DataSource CRUD operations."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.core.models import DataSource, DataSourceType

logger = logging.getLogger(__name__)


class DataSourceRepository:
    """Repository for DataSource database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        org_id: UUID,
        name: str,
        ds_type: DataSourceType,
        connection_config_enc: bytes,
        data_key_enc: bytes,
        schema_version: str = "v1",
    ) -> DataSource:
        """Create a new DataSource.

        Args:
            org_id: Organization ID.
            name: DataSource name.
            ds_type: DataSource type (POSTGRES or REST).
            connection_config_enc: Encrypted connection config.
            data_key_enc: Encrypted data key.
            schema_version: Schema version.

        Returns:
            Created DataSource instance.
        """
        datasource = DataSource(
            org_id=org_id,
            name=name,
            type=ds_type,
            connection_config_enc=connection_config_enc,
            data_key_enc=data_key_enc,
            schema_version=schema_version,
        )
        self.session.add(datasource)
        await self.session.commit()
        await self.session.refresh(datasource)
        logger.info(
            f"Created DataSource: {datasource.id} (name={datasource.name}, type={datasource.type.value}) for org {org_id}"
        )
        return datasource

    async def get_by_id(self, org_id: UUID, datasource_id: UUID) -> DataSource | None:
        """Get DataSource by ID within an organization.

        Args:
            org_id: Organization ID.
            datasource_id: DataSource ID.

        Returns:
            DataSource instance or None if not found.
        """
        stmt = select(DataSource).where(
            DataSource.id == datasource_id,
            DataSource.org_id == org_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, org_id: UUID, name: str) -> DataSource | None:
        """Get DataSource by name within an organization.

        Args:
            org_id: Organization ID.
            name: DataSource name.

        Returns:
            DataSource instance or None if not found.
        """
        stmt = select(DataSource).where(
            DataSource.name == name,
            DataSource.org_id == org_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_org(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[DataSource]:
        """List all DataSources for an organization.

        Args:
            org_id: Organization ID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of DataSource instances.
        """
        stmt = (
            select(DataSource)
            .where(DataSource.org_id == org_id)
            .order_by(DataSource.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        datasource: DataSource,
        name: str | None = None,
        connection_config_enc: bytes | None = None,
        data_key_enc: bytes | None = None,
    ) -> DataSource:
        """Update a DataSource.

        Args:
            datasource: DataSource instance to update.
            name: New name (optional).
            connection_config_enc: New encrypted config (optional).
            data_key_enc: New encrypted data key (optional).

        Returns:
            Updated DataSource instance.
        """
        if name is not None:
            datasource.name = name
        if connection_config_enc is not None:
            datasource.connection_config_enc = connection_config_enc
        if data_key_enc is not None:
            datasource.data_key_enc = data_key_enc

        await self.session.commit()
        await self.session.refresh(datasource)
        logger.info(f"Updated DataSource: {datasource.id}")
        return datasource

    async def delete(self, datasource: DataSource) -> None:
        """Delete a DataSource.

        Args:
            datasource: DataSource instance to delete.
        """
        datasource_id = datasource.id
        await self.session.delete(datasource)
        await self.session.commit()
        logger.info(f"Deleted DataSource: {datasource_id}")
