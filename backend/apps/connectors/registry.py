"""Connector registry for creating connector instances."""

from typing import Any
from uuid import UUID

from .base import Connector
from .impl_graphql import GraphQLConnector
from .impl_mongodb import MongoDBConnector
from .impl_postgres import PostgresConnector
from .impl_rest import RestConnector
from .impl_s3 import S3Connector

# Connector registry mapping type to implementation
CONNECTOR_REGISTRY: dict[str, type[Connector]] = {
    "POSTGRES": PostgresConnector,
    "REST": RestConnector,
    "MONGODB": MongoDBConnector,
    "GRAPHQL": GraphQLConnector,
    "S3": S3Connector,
}


def make_connector(ds_type: str, conf: dict[str, Any], org_id: UUID, ds_id: UUID) -> Connector:
    """Create a connector instance based on type.
    
    Args:
        ds_type: DataSource type (POSTGRES, REST, MONGODB, GRAPHQL, S3)
        conf: Decrypted connection configuration
        org_id: Organization ID
        ds_id: DataSource ID
        
    Returns:
        Connector instance
        
    Raises:
        ValueError: If connector type is not supported
    """
    connector_class = CONNECTOR_REGISTRY.get(ds_type)
    
    if not connector_class:
        raise ValueError(f"Unsupported connector type: {ds_type}")
    
    return connector_class(conf, org_id, ds_id)


def get_supported_types() -> list[str]:
    """Get list of supported connector types.
    
    Returns:
        List of supported type strings
    """
    return list(CONNECTOR_REGISTRY.keys())
