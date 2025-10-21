"""GraphQL connector implementation."""

import logging
from typing import Any
from uuid import UUID

import httpx

from .base import Connector
from .resilience import circuit_breaker_decorator, with_retry

logger = logging.getLogger(__name__)


class GraphQLConnector(Connector):
    """GraphQL API connector with ping and sample operations."""

    def __init__(self, conf: dict[str, Any], org_id: UUID, ds_id: UUID):
        super().__init__(conf, org_id, ds_id)
        self._base_url = conf["base_url"]
        self._headers = self._build_headers()
        self._timeout = conf.get("timeout_ms", 4000) / 1000.0  # Convert to seconds

    def _build_headers(self) -> dict[str, str]:
        """Build headers with authentication."""
        headers = self.conf.get("headers", {}).copy()
        headers.setdefault("Content-Type", "application/json")
        
        auth_type = self.conf.get("auth_type", "NONE")

        if auth_type == "API_KEY" and self.conf.get("api_key"):
            headers["X-API-Key"] = self.conf["api_key"]
        elif auth_type == "BEARER" and self.conf.get("bearer_token"):
            headers["Authorization"] = f"Bearer {self.conf['bearer_token']}"

        return headers

    @circuit_breaker_decorator
    @with_retry(retries=2, base_ms=250, max_ms=2000)
    async def ping(self) -> tuple[bool, str]:
        """Test GraphQL endpoint with introspection query.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Simple introspection query to test connectivity
            query = {"query": "{ __typename }"}
            
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._base_url,
                    headers=self._headers,
                    json=query,
                )

                if response.status_code == 200:
                    data = response.json()
                    # Check for GraphQL errors
                    if "errors" in data:
                        return False, f"GraphQL errors: {data['errors']}"
                    return True, "GraphQL endpoint reachable"
                else:
                    return False, f"HTTP error (status: {response.status_code})"

        except httpx.TimeoutException:
            return False, "Connection timeout"
        except Exception as e:
            logger.warning(f"GraphQL ping failed for ds_id={self.ds_id}: {e}")
            return False, f"Connection failed: {str(e)}"

    @circuit_breaker_decorator
    @with_retry(retries=1, base_ms=250, max_ms=1000)
    async def sample(self, params: dict[str, Any]) -> Any:
        """Execute a GraphQL query.
        
        Args:
            params: Should contain:
                - query: GraphQL query string (required)
                - variables: Query variables (optional)
                - operationName: Operation name (optional)
                
        Returns:
            GraphQL response
        """
        try:
            query = params.get("query")
            if not query:
                return {"ok": False, "error": "Missing 'query' in params"}

            payload: dict[str, Any] = {"query": query}
            
            if "variables" in params:
                payload["variables"] = params["variables"]
            if "operationName" in params:
                payload["operationName"] = params["operationName"]

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._base_url,
                    headers=self._headers,
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "ok": True,
                        "data": data.get("data"),
                        "errors": data.get("errors"),
                    }
                else:
                    return {
                        "ok": False,
                        "error": f"HTTP {response.status_code}: {response.text[:200]}",
                    }

        except httpx.TimeoutException:
            return {"ok": False, "error": "Request timeout"}
        except Exception as e:
            logger.warning(f"GraphQL sample failed for ds_id={self.ds_id}: {e}")
            return {"ok": False, "error": str(e)}
