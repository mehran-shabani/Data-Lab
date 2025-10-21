"""MongoDB connector implementation."""

import logging
from typing import Any
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorClient

from .base import Connector
from .resilience import circuit_breaker_decorator, with_retry

logger = logging.getLogger(__name__)


class MongoDBConnector(Connector):
    """MongoDB connector with ping and sample operations."""

    def __init__(self, conf: dict[str, Any], org_id: UUID, ds_id: UUID):
        super().__init__(conf, org_id, ds_id)
        self._uri = conf["uri"]
        self._db_name = conf["db"]
        self._collection = conf.get("collection")
        self._timeout_ms = conf.get("timeout_ms", 3000)
        self._client: AsyncIOMotorClient | None = None

    def _get_client(self) -> AsyncIOMotorClient:
        """Get or create MongoDB client."""
        if self._client is None:
            self._client = AsyncIOMotorClient(
                self._uri,
                serverSelectionTimeoutMS=self._timeout_ms,
                connectTimeoutMS=self._timeout_ms,
            )
        return self._client

    @circuit_breaker_decorator
    @with_retry(retries=2, base_ms=250, max_ms=2000)
    async def ping(self) -> tuple[bool, str]:
        """Test MongoDB connectivity with ping command.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            client = self._get_client()
            db = client[self._db_name]
            
            # Execute ping command
            result = await db.command("ping")
            
            if result.get("ok") == 1:
                return True, "MongoDB connection successful"
            else:
                return False, f"Ping command failed: {result}"
                
        except Exception as e:
            logger.warning(f"MongoDB ping failed for ds_id={self.ds_id}: {e}")
            return False, f"Connection failed: {str(e)}"

    @circuit_breaker_decorator
    @with_retry(retries=1, base_ms=250, max_ms=1000)
    async def sample(self, params: dict[str, Any]) -> Any:
        """Execute a sample MongoDB query.
        
        Args:
            params: Should contain:
                - collection: Collection name (optional, uses default from config)
                - filter: Query filter (optional, defaults to {})
                - limit: Number of documents (default: 1)
                
        Returns:
            Sample documents
        """
        try:
            client = self._get_client()
            db = client[self._db_name]
            
            # Determine collection
            coll_name = params.get("collection") or self._collection
            if not coll_name:
                return {
                    "ok": False,
                    "error": "No collection specified. Please provide 'collection' in params or config.",
                }
            
            collection = db[coll_name]
            
            # Build query
            filter_doc = params.get("filter", {})
            limit = min(params.get("limit", 1), 10)  # Cap at 10 for safety
            
            # Execute find
            cursor = collection.find(filter_doc).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
            
            return {
                "ok": True,
                "collection": coll_name,
                "count": len(documents),
                "documents": documents,
            }
            
        except Exception as e:
            logger.warning(f"MongoDB sample failed for ds_id={self.ds_id}: {e}")
            return {"ok": False, "error": str(e)}

    async def close(self) -> None:
        """Close MongoDB client."""
        if self._client:
            self._client.close()
            self._client = None
