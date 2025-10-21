"""Resilience patterns for connector operations (Retry/Backoff/Circuit-Breaker)."""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable
from uuid import UUID

logger = logging.getLogger(__name__)


# ===== Retry with Exponential Backoff =====


async def retry_with_backoff(
    func: Callable,
    *args: Any,
    retries: int = 2,
    base_ms: int = 250,
    max_ms: int = 2000,
    **kwargs: Any
) -> Any:
    """Retry async function with exponential backoff.
    
    Args:
        func: Async function to retry
        *args: Positional arguments for func
        retries: Number of retry attempts (default: 2)
        base_ms: Base delay in milliseconds (default: 250)
        max_ms: Maximum delay in milliseconds (default: 2000)
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from func
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(retries + 1):
        try:
            return await func(*args, **kwargs)
        except (asyncio.TimeoutError, OSError, ConnectionError) as e:
            last_exception = e
            if attempt < retries:
                delay_ms = min(base_ms * (2 ** attempt), max_ms)
                logger.debug(f"Retry attempt {attempt + 1}/{retries} after {delay_ms}ms: {e}")
                await asyncio.sleep(delay_ms / 1000.0)
            else:
                logger.warning(f"All {retries} retries failed: {e}")
                raise
        except Exception as e:
            # Don't retry on non-transient errors
            logger.warning(f"Non-retryable error: {e}")
            raise
    
    if last_exception:
        raise last_exception


def with_retry(retries: int = 2, base_ms: int = 250, max_ms: int = 2000):
    """Decorator for async functions with retry logic.
    
    Usage:
        @with_retry(retries=3, base_ms=500, max_ms=5000)
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await retry_with_backoff(
                func, *args, retries=retries, base_ms=base_ms, max_ms=max_ms, **kwargs
            )
        return wrapper
    return decorator


# ===== Circuit Breaker =====


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"        # Normal operation
    OPEN = "OPEN"            # Failing, reject all requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5          # Failures to open circuit
    success_threshold: int = 2          # Successes to close from half-open
    timeout_seconds: int = 30           # Time to wait before half-open
    

class CircuitBreakerState:
    """State for a single circuit breaker."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: float | None = None
        
    def should_allow_request(self) -> bool:
        """Check if request should be allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if timeout expired
            if self.last_failure_time and (
                time.time() - self.last_failure_time >= self.config.timeout_seconds
            ):
                logger.info("Circuit transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        else:  # HALF_OPEN
            return True
            
    def record_success(self) -> None:
        """Record successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                logger.info("Circuit closing after successful recovery")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            if self.failure_count > 0:
                self.failure_count = 0
                
    def record_failure(self) -> None:
        """Record failed request."""
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit opening again after failure in HALF_OPEN")
            self.state = CircuitState.OPEN
            self.failure_count = self.config.failure_threshold
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                logger.warning(
                    f"Circuit opening after {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN


class CircuitBreakerRegistry:
    """Registry of circuit breakers per (org_id, ds_id)."""
    
    def __init__(self, config: CircuitBreakerConfig | None = None):
        self.config = config or CircuitBreakerConfig()
        self._breakers: dict[tuple[UUID, UUID], CircuitBreakerState] = {}
        
    def get_breaker(self, org_id: UUID, ds_id: UUID) -> CircuitBreakerState:
        """Get or create circuit breaker for datasource."""
        key = (org_id, ds_id)
        if key not in self._breakers:
            self._breakers[key] = CircuitBreakerState(self.config)
        return self._breakers[key]
    
    def clear(self, org_id: UUID | None = None, ds_id: UUID | None = None) -> None:
        """Clear circuit breakers (for testing)."""
        if org_id is None and ds_id is None:
            self._breakers.clear()
        elif org_id and ds_id:
            key = (org_id, ds_id)
            self._breakers.pop(key, None)


# Global registry instance
circuit_breaker_registry = CircuitBreakerRegistry()


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass


async def with_circuit_breaker(
    func: Callable,
    org_id: UUID,
    ds_id: UUID,
    *args: Any,
    **kwargs: Any
) -> Any:
    """Execute function with circuit breaker protection.
    
    Args:
        func: Async function to execute
        org_id: Organization ID
        ds_id: DataSource ID
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from func
        
    Raises:
        CircuitBreakerOpen: If circuit is open
        Exception: From func if it fails
    """
    breaker = circuit_breaker_registry.get_breaker(org_id, ds_id)
    
    if not breaker.should_allow_request():
        raise CircuitBreakerOpen(
            "اتصال موقتاً تعلیق شد؛ چند ثانیه دیگر تلاش کنید."
        )
    
    try:
        result = await func(*args, **kwargs)
        breaker.record_success()
        return result
    except Exception as e:
        breaker.record_failure()
        raise


def circuit_breaker_decorator(func: Callable):
    """Decorator for connector methods with circuit breaker.
    
    Expects self to have org_id and ds_id attributes.
    
    Usage:
        class MyConnector(Connector):
            @circuit_breaker_decorator
            async def ping(self):
                ...
    """
    @wraps(func)
    async def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        return await with_circuit_breaker(
            func, self.org_id, self.ds_id, self, *args, **kwargs
        )
    return wrapper
