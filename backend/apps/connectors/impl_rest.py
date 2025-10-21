"""REST API connector implementation."""

import logging
from typing import Any
from uuid import UUID

import httpx

from .base import Connector
from .resilience import circuit_breaker_decorator, with_retry

logger = logging.getLogger(__name__)


class RestConnector(Connector):
    """REST API connector with ping and sample operations."""

    def __init__(self, conf: dict[str, Any], org_id: UUID, ds_id: UUID):
        super().__init__(conf, org_id, ds_id)
        self._base_url = conf["base_url"]
        self._headers = self._build_headers()
        self._timeout = conf.get("timeout_ms", 10000) / 1000.0  # Convert to seconds

    def _build_headers(self) -> dict[str, str]:
        """Build headers with authentication."""
        headers = self.conf.get("headers", {}).copy()
        auth_type = self.conf.get("auth_type", "NONE")

        if auth_type == "API_KEY" and self.conf.get("api_key"):
            headers["X-API-Key"] = self.conf["api_key"]
        elif auth_type == "BEARER" and self.conf.get("bearer_token"):
            headers["Authorization"] = f"Bearer {self.conf['bearer_token']}"

        return headers

    @circuit_breaker_decorator
    @with_retry(retries=2, base_ms=250, max_ms=2000)
    async def ping(self) -> tuple[bool, str]:
        """Test REST API connectivity with HEAD/GET request.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                # Try HEAD first, fallback to GET
                try:
                    response = await client.head(
                        self._base_url, headers=self._headers, follow_redirects=True
                    )
                except Exception:
                    response = await client.get(
                        self._base_url, headers=self._headers, follow_redirects=True
                    )

                if response.status_code < 500:
                    return True, f"REST API reachable (status: {response.status_code})"
                else:
                    return False, f"REST API returned error (status: {response.status_code})"

        except httpx.TimeoutException:
            return False, "Connection timeout"
        except Exception as e:
            logger.warning(f"REST ping failed for ds_id={self.ds_id}: {e}")
            return False, f"Connection failed: {str(e)}"

    @circuit_breaker_decorator
    @with_retry(retries=1, base_ms=250, max_ms=1000)
    async def sample(self, params: dict[str, Any]) -> Any:
        """Execute a sample REST request.
        
        Args:
            params: Should contain:
                - method: HTTP method (default: GET)
                - path: URL path to append to base_url (default: /)
                - body: Request body for POST/PUT (optional)
                
        Returns:
            Response data
        """
        try:
            method = params.get("method", "GET").upper()
            path = params.get("path", "/")
            body = params.get("body")

            url = self._base_url.rstrip("/") + "/" + path.lstrip("/")

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                if method == "GET":
                    response = await client.get(url, headers=self._headers)
                elif method == "POST":
                    response = await client.post(url, headers=self._headers, json=body)
                elif method == "PUT":
                    response = await client.put(url, headers=self._headers, json=body)
                elif method == "DELETE":
                    response = await client.delete(url, headers=self._headers)
                else:
                    return {"ok": False, "error": f"Unsupported method: {method}"}

                return {
                    "ok": True,
                    "status": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text[:1000],  # Limit response size
                }

        except httpx.TimeoutException:
            return {"ok": False, "error": "Request timeout"}
        except Exception as e:
            logger.warning(f"REST sample failed for ds_id={self.ds_id}: {e}")
            return {"ok": False, "error": str(e)}
