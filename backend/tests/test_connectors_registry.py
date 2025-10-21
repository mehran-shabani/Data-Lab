"""Tests for connector registry."""

import uuid

import pytest

from apps.connectors.impl_graphql import GraphQLConnector
from apps.connectors.impl_mongodb import MongoDBConnector
from apps.connectors.impl_postgres import PostgresConnector
from apps.connectors.impl_rest import RestConnector
from apps.connectors.impl_s3 import S3Connector
from apps.connectors.registry import get_supported_types, make_connector


def test_get_supported_types():
    """Test getting supported connector types."""
    types = get_supported_types()
    assert "POSTGRES" in types
    assert "REST" in types
    assert "MONGODB" in types
    assert "GRAPHQL" in types
    assert "S3" in types


def test_make_postgres_connector():
    """Test creating PostgreSQL connector."""
    conf = {"host": "localhost", "port": 5432, "database": "test", "username": "user", "password": "pass"}
    org_id = uuid.uuid4()
    ds_id = uuid.uuid4()
    
    connector = make_connector("POSTGRES", conf, org_id, ds_id)
    
    assert isinstance(connector, PostgresConnector)
    assert connector.org_id == org_id
    assert connector.ds_id == ds_id


def test_make_rest_connector():
    """Test creating REST connector."""
    conf = {"base_url": "https://api.example.com", "auth_type": "NONE"}
    org_id = uuid.uuid4()
    ds_id = uuid.uuid4()
    
    connector = make_connector("REST", conf, org_id, ds_id)
    
    assert isinstance(connector, RestConnector)
    assert connector.org_id == org_id
    assert connector.ds_id == ds_id


def test_make_mongodb_connector():
    """Test creating MongoDB connector."""
    conf = {"uri": "mongodb://localhost:27017", "db": "testdb"}
    org_id = uuid.uuid4()
    ds_id = uuid.uuid4()
    
    connector = make_connector("MONGODB", conf, org_id, ds_id)
    
    assert isinstance(connector, MongoDBConnector)
    assert connector.org_id == org_id
    assert connector.ds_id == ds_id


def test_make_graphql_connector():
    """Test creating GraphQL connector."""
    conf = {"base_url": "https://api.example.com/graphql", "auth_type": "NONE", "timeout_ms": 4000}
    org_id = uuid.uuid4()
    ds_id = uuid.uuid4()
    
    connector = make_connector("GRAPHQL", conf, org_id, ds_id)
    
    assert isinstance(connector, GraphQLConnector)
    assert connector.org_id == org_id
    assert connector.ds_id == ds_id


def test_make_s3_connector():
    """Test creating S3 connector."""
    conf = {
        "endpoint": "https://s3.amazonaws.com",
        "bucket": "test-bucket",
        "access_key": "key",
        "secret_key": "secret",
        "use_path_style": False,
    }
    org_id = uuid.uuid4()
    ds_id = uuid.uuid4()
    
    connector = make_connector("S3", conf, org_id, ds_id)
    
    assert isinstance(connector, S3Connector)
    assert connector.org_id == org_id
    assert connector.ds_id == ds_id


def test_make_connector_unsupported_type():
    """Test creating connector with unsupported type."""
    conf = {}
    org_id = uuid.uuid4()
    ds_id = uuid.uuid4()
    
    with pytest.raises(ValueError, match="Unsupported connector type"):
        make_connector("UNKNOWN", conf, org_id, ds_id)
