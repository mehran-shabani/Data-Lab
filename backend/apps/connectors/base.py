"""Base abstraction for DataSource connectors."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class Connector(ABC):
    """Abstract base class for DataSource connectors.
    
    Each connector implementation must provide:
    - ping(): Test connectivity to the data source
    - sample(): Execute a lightweight sample query/operation
    - close(): Clean up resources
    """

    def __init__(self, conf: dict[str, Any], org_id: UUID, ds_id: UUID):
        """Initialize connector with configuration and context.
        
        Args:
            conf: Decrypted connection configuration
            org_id: Organization ID (for metrics/logging)
            ds_id: DataSource ID (for metrics/circuit-breaker)
        """
        self.conf = conf
        self.org_id = org_id
        self.ds_id = ds_id

    @abstractmethod
    async def ping(self) -> tuple[bool, str]:
        """Test connectivity to the data source.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        pass

    @abstractmethod
    async def sample(self, params: dict[str, Any]) -> Any:
        """Execute a lightweight sample query/operation.
        
        Args:
            params: Query/operation parameters (connector-specific)
            
        Returns:
            Result data (connector-specific format)
            
        Raises:
            ValueError: If params are invalid
            Exception: If operation fails
        """
        pass

    async def close(self) -> None:
        """Clean up resources (override if needed).
        
        Default implementation does nothing.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(org_id={self.org_id}, ds_id={self.ds_id})>"
