"""Tests for connector metrics."""

import time
import uuid

import pytest

from apps.connectors.metrics import DataSourceMetrics, metrics_registry


def test_datasource_metrics_initialization():
    """Test DataSourceMetrics initialization."""
    metrics = DataSourceMetrics()
    
    assert metrics.calls_total == 0
    assert metrics.errors_total == 0
    assert metrics.avg_latency_ms == 0.0
    assert metrics.p95_ms == 0.0
    assert metrics.last_ok_ts is None
    assert metrics.last_err_ts is None
    assert metrics.state == "CLOSED"


def test_datasource_metrics_record_success():
    """Test recording successful calls."""
    metrics = DataSourceMetrics()
    
    metrics.record_call(100.0, success=True)
    
    assert metrics.calls_total == 1
    assert metrics.errors_total == 0
    assert metrics.avg_latency_ms == 100.0
    assert metrics.last_ok_ts is not None
    assert metrics.last_err_ts is None


def test_datasource_metrics_record_failure():
    """Test recording failed calls."""
    metrics = DataSourceMetrics()
    
    metrics.record_call(50.0, success=False)
    
    assert metrics.calls_total == 1
    assert metrics.errors_total == 1
    assert metrics.avg_latency_ms == 50.0
    assert metrics.last_ok_ts is None
    assert metrics.last_err_ts is not None


def test_datasource_metrics_ema_latency():
    """Test EMA calculation for average latency."""
    metrics = DataSourceMetrics()
    
    # Record multiple calls
    metrics.record_call(100.0, success=True)
    metrics.record_call(200.0, success=True)
    metrics.record_call(150.0, success=True)
    
    # EMA should be between min and max
    assert 100.0 < metrics.avg_latency_ms < 200.0


def test_datasource_metrics_p95_calculation():
    """Test P95 latency calculation."""
    metrics = DataSourceMetrics()
    
    # Record 20 calls with varying latencies
    for i in range(20):
        metrics.record_call(float(i * 10), success=True)
    
    # P95 should be close to 95th percentile
    assert metrics.p95_ms > 150.0  # Approximate


def test_datasource_metrics_to_dict():
    """Test converting metrics to dict."""
    metrics = DataSourceMetrics()
    metrics.record_call(100.0, success=True)
    metrics.state = "CLOSED"
    
    data = metrics.to_dict()
    
    assert data["calls_total"] == 1
    assert data["errors_total"] == 0
    assert data["avg_latency_ms"] == 100.0
    assert data["state"] == "CLOSED"
    assert "last_ok_ts" in data
    assert "last_err_ts" in data
    assert "p95_ms" in data


def test_metrics_registry_get_metrics():
    """Test getting metrics from registry."""
    metrics_registry.clear()
    
    org_id = uuid.uuid4()
    ds_id = uuid.uuid4()
    
    metrics = metrics_registry.get_metrics(org_id, ds_id)
    
    assert isinstance(metrics, DataSourceMetrics)
    assert metrics.calls_total == 0


def test_metrics_registry_record_call():
    """Test recording calls via registry."""
    metrics_registry.clear()
    
    org_id = uuid.uuid4()
    ds_id = uuid.uuid4()
    
    metrics_registry.record_call(org_id, ds_id, 100.0, success=True)
    
    metrics = metrics_registry.get_metrics(org_id, ds_id)
    assert metrics.calls_total == 1
    assert metrics.errors_total == 0


def test_metrics_registry_update_state():
    """Test updating circuit breaker state."""
    metrics_registry.clear()
    
    org_id = uuid.uuid4()
    ds_id = uuid.uuid4()
    
    metrics_registry.update_state(org_id, ds_id, "OPEN")
    
    metrics = metrics_registry.get_metrics(org_id, ds_id)
    assert metrics.state == "OPEN"


def test_metrics_registry_get_all_for_org():
    """Test getting all metrics for an organization."""
    metrics_registry.clear()
    
    org_id = uuid.uuid4()
    ds_id_1 = uuid.uuid4()
    ds_id_2 = uuid.uuid4()
    other_org_id = uuid.uuid4()
    other_ds_id = uuid.uuid4()
    
    # Record calls for multiple datasources
    metrics_registry.record_call(org_id, ds_id_1, 100.0, success=True)
    metrics_registry.record_call(org_id, ds_id_2, 200.0, success=True)
    metrics_registry.record_call(other_org_id, other_ds_id, 300.0, success=True)
    
    # Get all for target org
    org_metrics = metrics_registry.get_all_for_org(org_id)
    
    assert len(org_metrics) == 2
    assert ds_id_1 in org_metrics
    assert ds_id_2 in org_metrics
    assert other_ds_id not in org_metrics


def test_metrics_registry_clear():
    """Test clearing all metrics."""
    metrics_registry.clear()
    
    org_id = uuid.uuid4()
    ds_id = uuid.uuid4()
    
    metrics_registry.record_call(org_id, ds_id, 100.0, success=True)
    
    metrics_registry.clear()
    
    # After clear, metrics should be reset
    metrics = metrics_registry.get_metrics(org_id, ds_id)
    assert metrics.calls_total == 0
