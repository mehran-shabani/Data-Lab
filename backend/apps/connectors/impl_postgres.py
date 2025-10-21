"""PostgreSQL connector implementation."""

import logging
from typing import Any
from uuid import UUID

import psycopg

from .base import Connector
from .resilience import circuit_breaker_decorator, with_retry

logger = logging.getLogger(__name__)


class PostgresConnector(Connector):
    """PostgreSQL connector with ping and sample operations."""

    def __init__(self, conf: dict[str, Any], org_id: UUID, ds_id: UUID):
        super().__init__(conf, org_id, ds_id)
        self._dsn = self._build_dsn()

    def _build_dsn(self) -> str:
        """Build DSN from config."""
        if "dsn" in self.conf:
            return self.conf["dsn"]
        else:
            return (
                f"postgresql://{self.conf['username']}:{self.conf['password']}"
                f"@{self.conf['host']}:{self.conf.get('port', 5432)}/{self.conf['database']}"
            )

    @circuit_breaker_decorator
    @with_retry(retries=2, base_ms=250, max_ms=2000)
    async def ping(self) -> tuple[bool, str]:
        """Test PostgreSQL connectivity with SELECT 1.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            conn = psycopg.connect(self._dsn, connect_timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            return True, "PostgreSQL connection successful"
        except Exception as e:
            logger.warning(f"PostgreSQL ping failed for ds_id={self.ds_id}: {e}")
            return False, f"Connection failed: {str(e)}"

    @circuit_breaker_decorator
    @with_retry(retries=1, base_ms=250, max_ms=1000)
    async def sample(self, params: dict[str, Any]) -> Any:
        """Execute a simple sample query.
        
        For MVP, returns a simple message. In production, this could:
        - Execute a provided SQL query (with safety checks)
        - Return schema information
        - Return sample rows from a specified table
        
        Args:
            params: Query parameters (currently unused in MVP)
            
        Returns:
            Sample result
        """
        try:
            conn = psycopg.connect(self._dsn, connect_timeout=5)
            cursor = conn.cursor()
            
            # MVP: Just get database version
            cursor.execute("SELECT version()")
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return {
                "ok": True,
                "message": "Sample query successful (MVP limited)",
                "version": result[0] if result else "unknown",
            }
        except Exception as e:
            logger.warning(f"PostgreSQL sample failed for ds_id={self.ds_id}: {e}")
            return {
                "ok": False,
                "error": str(e),
            }
