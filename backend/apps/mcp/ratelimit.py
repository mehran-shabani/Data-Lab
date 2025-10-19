"""Rate limiting module for MCP tool invocations.

In-memory token bucket implementation for MVP.
In production, this should be moved to Redis for distributed rate limiting.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import TypeAlias
from uuid import UUID


RateLimitKey: TypeAlias = tuple[UUID, UUID]  # (org_id, tool_id)


@dataclass
class TokenBucket:
    """Token bucket for rate limiting.

    Implements the token bucket algorithm for rate limiting.
    Tokens are refilled at a constant rate.
    """

    capacity: int  # Maximum number of tokens
    tokens: float  # Current number of tokens
    last_refill: float  # Timestamp of last refill
    refill_rate: float  # Tokens per second

    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume (default: 1)

        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        now = time.time()
        # Refill tokens based on time elapsed
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now

        # Try to consume tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimiter:
    """In-memory rate limiter using token bucket algorithm.

    WARNING: This is a single-process implementation for MVP.
    In production, use Redis-backed rate limiting for distributed systems.
    """

    def __init__(self) -> None:
        """Initialize the rate limiter."""
        self._buckets: dict[RateLimitKey, TokenBucket] = {}
        self._lock = Lock()

    def check_rate_limit(self, org_id: UUID, tool_id: UUID, limit_per_min: int) -> bool:
        """Check if a request is within rate limit.

        Args:
            org_id: Organization ID
            tool_id: Tool ID
            limit_per_min: Rate limit per minute

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        key = (org_id, tool_id)
        refill_rate = limit_per_min / 60.0  # Convert per-minute to per-second

        with self._lock:
            if key not in self._buckets:
                # Create new bucket
                self._buckets[key] = TokenBucket(
                    capacity=limit_per_min,
                    tokens=limit_per_min,
                    last_refill=time.time(),
                    refill_rate=refill_rate,
                )

            bucket = self._buckets[key]
            return bucket.consume(1)

    def reset(self, org_id: UUID, tool_id: UUID) -> None:
        """Reset rate limit for a specific tool (useful for testing).

        Args:
            org_id: Organization ID
            tool_id: Tool ID
        """
        key = (org_id, tool_id)
        with self._lock:
            if key in self._buckets:
                del self._buckets[key]


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance.

    Returns:
        The global RateLimiter instance
    """
    return _rate_limiter
