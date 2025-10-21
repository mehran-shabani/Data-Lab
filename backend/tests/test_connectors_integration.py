"""Integration tests for connectors with mocks."""

import uuid
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from apps.connectors.impl_graphql import GraphQLConnector
from apps.connectors.impl_mongodb import MongoDBConnector
from apps.connectors.impl_postgres import PostgresConnector
from apps.connectors.impl_rest import RestConnector
from apps.connectors.impl_s3 import S3Connector


@pytest.mark.asyncio
@patch("apps.connectors.impl_postgres.psycopg.connect")
async def test_postgres_connector_ping_success(mock_connect):
    """Test PostgreSQL connector ping with mock."""
    # Mock connection
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    
    # Create connector
    conf = {"host": "localhost", "port": 5432, "database": "test", "username": "user", "password": "pass"}
    connector = PostgresConnector(conf, uuid.uuid4(), uuid.uuid4())
    
    # Test ping
    ok, message = await connector.ping()
    
    assert ok is True
    assert "successful" in message.lower()
    mock_connect.assert_called_once()
    mock_cursor.execute.assert_called_once_with("SELECT 1")


@pytest.mark.asyncio
@patch("apps.connectors.impl_postgres.psycopg.connect")
async def test_postgres_connector_ping_failure(mock_connect):
    """Test PostgreSQL connector ping failure."""
    # Mock connection failure
    mock_connect.side_effect = Exception("Connection refused")
    
    # Create connector
    conf = {"host": "localhost", "port": 5432, "database": "test", "username": "user", "password": "pass"}
    connector = PostgresConnector(conf, uuid.uuid4(), uuid.uuid4())
    
    # Test ping
    ok, message = await connector.ping()
    
    assert ok is False
    assert "failed" in message.lower()


@pytest.mark.asyncio
@patch("apps.connectors.impl_rest.httpx.AsyncClient")
async def test_rest_connector_ping_success(mock_client_class):
    """Test REST connector ping with mock."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.head.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    # Create connector
    conf = {"base_url": "https://api.example.com", "auth_type": "NONE"}
    connector = RestConnector(conf, uuid.uuid4(), uuid.uuid4())
    
    # Test ping
    ok, message = await connector.ping()
    
    assert ok is True
    assert "200" in message


@pytest.mark.asyncio
@patch("apps.connectors.impl_rest.httpx.AsyncClient")
async def test_rest_connector_sample(mock_client_class):
    """Test REST connector sample with mock."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.text = '{"result": "ok"}'
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    # Create connector
    conf = {"base_url": "https://api.example.com", "auth_type": "NONE"}
    connector = RestConnector(conf, uuid.uuid4(), uuid.uuid4())
    
    # Test sample
    result = await connector.sample({"method": "GET", "path": "/test"})
    
    assert result["ok"] is True
    assert result["status"] == 200


@pytest.mark.asyncio
async def test_mongodb_connector_ping_with_mock():
    """Test MongoDB connector ping with mock."""
    # Create connector
    conf = {"uri": "mongodb://localhost:27017", "db": "testdb", "timeout_ms": 3000}
    connector = MongoDBConnector(conf, uuid.uuid4(), uuid.uuid4())
    
    # Mock client
    mock_db = AsyncMock()
    mock_db.command = AsyncMock(return_value={"ok": 1})
    
    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    
    connector._client = mock_client
    
    # Test ping
    ok, message = await connector.ping()
    
    assert ok is True
    assert "successful" in message.lower()


@pytest.mark.asyncio
async def test_mongodb_connector_sample_with_mock():
    """Test MongoDB connector sample with mock."""
    # Create connector
    conf = {"uri": "mongodb://localhost:27017", "db": "testdb", "collection": "users", "timeout_ms": 3000}
    connector = MongoDBConnector(conf, uuid.uuid4(), uuid.uuid4())
    
    # Mock cursor with proper async behavior
    class MockCursor:
        def limit(self, n):
            return self
        
        async def to_list(self, length):
            return [{"_id": "123", "name": "test"}]
    
    mock_cursor = MockCursor()
    
    mock_collection = MagicMock()
    mock_collection.find.return_value = mock_cursor
    
    mock_db = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    
    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    
    connector._client = mock_client
    
    # Test sample
    result = await connector.sample({})
    
    assert result["ok"] is True
    assert result["count"] == 1
    assert result["documents"][0]["_id"] == "123"


@pytest.mark.asyncio
@patch("apps.connectors.impl_graphql.httpx.AsyncClient")
async def test_graphql_connector_ping_success(mock_client_class):
    """Test GraphQL connector ping with mock."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"__typename": "Query"}}
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    # Create connector
    conf = {"base_url": "https://api.example.com/graphql", "auth_type": "NONE", "timeout_ms": 4000}
    connector = GraphQLConnector(conf, uuid.uuid4(), uuid.uuid4())
    
    # Test ping
    ok, message = await connector.ping()
    
    assert ok is True
    assert "reachable" in message.lower()


@pytest.mark.asyncio
@patch("apps.connectors.impl_graphql.httpx.AsyncClient")
async def test_graphql_connector_sample(mock_client_class):
    """Test GraphQL connector sample with mock."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"users": [{"name": "test"}]}}
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    # Create connector
    conf = {"base_url": "https://api.example.com/graphql", "auth_type": "NONE", "timeout_ms": 4000}
    connector = GraphQLConnector(conf, uuid.uuid4(), uuid.uuid4())
    
    # Test sample
    result = await connector.sample({"query": "{ users { name } }"})
    
    assert result["ok"] is True
    assert result["data"] is not None


@pytest.mark.asyncio
async def test_s3_connector_ping_with_mock():
    """Test S3 connector ping with mock."""
    # Create connector
    conf = {
        "endpoint": "https://s3.amazonaws.com",
        "bucket": "test-bucket",
        "access_key": "key",
        "secret_key": "secret",
        "use_path_style": False,
    }
    connector = S3Connector(conf, uuid.uuid4(), uuid.uuid4())
    
    # Mock client
    mock_client = MagicMock()
    mock_client.head_bucket.return_value = {}
    connector._client = mock_client
    
    # Test ping
    ok, message = await connector.ping()
    
    assert ok is True
    assert "accessible" in message.lower()


@pytest.mark.asyncio
async def test_s3_connector_sample_with_mock():
    """Test S3 connector sample with mock."""
    # Create connector
    conf = {
        "endpoint": "https://s3.amazonaws.com",
        "bucket": "test-bucket",
        "access_key": "key",
        "secret_key": "secret",
        "use_path_style": False,
    }
    connector = S3Connector(conf, uuid.uuid4(), uuid.uuid4())
    
    # Mock client
    mock_client = MagicMock()
    mock_client.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "file1.txt", "Size": 100, "LastModified": "2024-01-01T00:00:00Z", "ETag": "abc"},
            {"Key": "file2.txt", "Size": 200, "LastModified": "2024-01-02T00:00:00Z", "ETag": "def"},
        ],
        "IsTruncated": False,
    }
    
    # Mock datetime for isoformat
    from datetime import datetime
    mock_client.list_objects_v2.return_value["Contents"][0]["LastModified"] = datetime.now()
    mock_client.list_objects_v2.return_value["Contents"][1]["LastModified"] = datetime.now()
    
    connector._client = mock_client
    
    # Test sample
    result = await connector.sample({})
    
    assert result["ok"] is True
    assert result["count"] == 2
    assert len(result["objects"]) == 2
