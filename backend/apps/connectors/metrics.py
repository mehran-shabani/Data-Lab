"""Metrics collection for DataSource connectors."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class DataSourceMetrics:
    """Metrics for a single DataSource."""
    
    calls_total: int = 0
    errors_total: int = 0
    
    # Latency tracking (simple EMA - Exponential Moving Average)
    avg_latency_ms: float = 0.0
    p95_ms: float = 0.0  # Approximate P95 (simplified)
    
    # Recent latencies for P95 calculation (keep last 20)
    _recent_latencies: list[float] = field(default_factory=list)
    
    # Timestamps
    last_ok_ts: float | None = None
    last_err_ts: float | None = None
    
    # Circuit breaker state
    state: str = "CLOSED"
    
    def record_call(self, latency_ms: float, success: bool) -> None:
        """Record a call with latency and success/failure."""
        self.calls_total += 1
        
        if success:
            self.last_ok_ts = time.time()
        else:
            self.errors_total += 1
            self.last_err_ts = time.time()
            
        # Update average latency with EMA (alpha = 0.2)
        if self.avg_latency_ms == 0:
            self.avg_latency_ms = latency_ms
        else:
            alpha = 0.2
            self.avg_latency_ms = alpha * latency_ms + (1 - alpha) * self.avg_latency_ms
            
        # Track recent latencies for P95
        self._recent_latencies.append(latency_ms)
        if len(self._recent_latencies) > 20:
            self._recent_latencies.pop(0)
            
        # Update P95 (simplified: 95th percentile of recent samples)
        if self._recent_latencies:
            sorted_latencies = sorted(self._recent_latencies)
            idx = int(len(sorted_latencies) * 0.95)
            self.p95_ms = sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for API response."""
        return {
            "calls_total": self.calls_total,
            "errors_total": self.errors_total,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "last_ok_ts": self.last_ok_ts,
            "last_err_ts": self.last_err_ts,
            "state": self.state,
        }


class MetricsRegistry:
    """Registry of metrics per (org_id, ds_id)."""
    
    def __init__(self):
        self._metrics: dict[tuple[UUID, UUID], DataSourceMetrics] = defaultdict(DataSourceMetrics)
    
    def get_metrics(self, org_id: UUID, ds_id: UUID) -> DataSourceMetrics:
        """Get metrics for a DataSource."""
        key = (org_id, ds_id)
        return self._metrics[key]
    
    def record_call(self, org_id: UUID, ds_id: UUID, latency_ms: float, success: bool) -> None:
        """Record a call for a DataSource."""
        metrics = self.get_metrics(org_id, ds_id)
        metrics.record_call(latency_ms, success)
    
    def update_state(self, org_id: UUID, ds_id: UUID, state: str) -> None:
        """Update circuit breaker state."""
        metrics = self.get_metrics(org_id, ds_id)
        metrics.state = state
    
    def get_all_for_org(self, org_id: UUID) -> dict[UUID, DataSourceMetrics]:
        """Get all metrics for an organization."""
        result = {}
        for (org, ds_id), metrics in self._metrics.items():
            if org == org_id:
                result[ds_id] = metrics
        return result
    
    def clear(self) -> None:
        """Clear all metrics (for testing)."""
        self._metrics.clear()


# Global registry instance
metrics_registry = MetricsRegistry()
