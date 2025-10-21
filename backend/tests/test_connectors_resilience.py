"""Tests for resilience patterns (Retry/Circuit-Breaker)."""

import asyncio
import uuid

import pytest

from apps.connectors.resilience import (
    CircuitBreakerConfig,
    CircuitBreakerOpen,
    CircuitBreakerState,
    CircuitState,
    circuit_breaker_registry,
    retry_with_backoff,
    with_circuit_breaker,
)


@pytest.mark.asyncio
async def test_retry_with_backoff_success():
    """Test retry with immediate success."""
    call_count = 0
    
    async def succeeds_immediately():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = await retry_with_backoff(succeeds_immediately, retries=2)
    
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_with_backoff_eventual_success():
    """Test retry with eventual success after failures."""
    call_count = 0
    
    async def succeeds_on_third_try():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary error")
        return "success"
    
    result = await retry_with_backoff(succeeds_on_third_try, retries=3, base_ms=10, max_ms=50)
    
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_with_backoff_all_fail():
    """Test retry when all attempts fail."""
    call_count = 0
    
    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Persistent error")
    
    with pytest.raises(ConnectionError, match="Persistent error"):
        await retry_with_backoff(always_fails, retries=2, base_ms=10, max_ms=50)
    
    assert call_count == 3  # Initial + 2 retries


@pytest.mark.asyncio
async def test_retry_no_retry_on_non_transient_error():
    """Test that non-transient errors are not retried."""
    call_count = 0
    
    async def fails_with_value_error():
        nonlocal call_count
        call_count += 1
        raise ValueError("Non-transient error")
    
    with pytest.raises(ValueError, match="Non-transient error"):
        await retry_with_backoff(fails_with_value_error, retries=2, base_ms=10, max_ms=50)
    
    assert call_count == 1  # No retries for ValueError


def test_circuit_breaker_state_closed_allows_request():
    """Test that closed circuit allows requests."""
    config = CircuitBreakerConfig(failure_threshold=3)
    breaker = CircuitBreakerState(config)
    
    assert breaker.state == CircuitState.CLOSED
    assert breaker.should_allow_request() is True


def test_circuit_breaker_opens_after_failures():
    """Test that circuit opens after threshold failures."""
    config = CircuitBreakerConfig(failure_threshold=3)
    breaker = CircuitBreakerState(config)
    
    # Record failures
    for _ in range(3):
        breaker.record_failure()
    
    assert breaker.state == CircuitState.OPEN
    assert breaker.should_allow_request() is False


def test_circuit_breaker_half_open_after_timeout():
    """Test that circuit transitions to half-open after timeout."""
    config = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=0.1)
    breaker = CircuitBreakerState(config)
    
    # Open circuit
    breaker.record_failure()
    breaker.record_failure()
    
    assert breaker.state == CircuitState.OPEN
    assert breaker.should_allow_request() is False
    
    # Wait for timeout
    import time
    time.sleep(0.15)
    
    # Should transition to half-open
    assert breaker.should_allow_request() is True
    assert breaker.state == CircuitState.HALF_OPEN


def test_circuit_breaker_closes_after_successes_in_half_open():
    """Test that circuit closes after successes in half-open state."""
    config = CircuitBreakerConfig(failure_threshold=2, success_threshold=2, timeout_seconds=0.1)
    breaker = CircuitBreakerState(config)
    
    # Open circuit
    breaker.record_failure()
    breaker.record_failure()
    
    # Wait and transition to half-open
    import time
    time.sleep(0.15)
    breaker.should_allow_request()
    
    # Record successes
    breaker.record_success()
    breaker.record_success()
    
    assert breaker.state == CircuitState.CLOSED


def test_circuit_breaker_reopens_on_failure_in_half_open():
    """Test that circuit reopens on failure in half-open state."""
    config = CircuitBreakerConfig(failure_threshold=2, timeout_seconds=0.1)
    breaker = CircuitBreakerState(config)
    
    # Open circuit
    breaker.record_failure()
    breaker.record_failure()
    
    # Wait and transition to half-open
    import time
    time.sleep(0.15)
    breaker.should_allow_request()
    
    # Record failure in half-open
    breaker.record_failure()
    
    assert breaker.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_with_circuit_breaker_success():
    """Test circuit breaker with successful call."""
    org_id = uuid.uuid4()
    ds_id = uuid.uuid4()
    
    # Clear any existing breaker state
    circuit_breaker_registry.clear()
    
    async def succeeds():
        return "success"
    
    result = await with_circuit_breaker(succeeds, org_id, ds_id)
    
    assert result == "success"
    
    breaker = circuit_breaker_registry.get_breaker(org_id, ds_id)
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_with_circuit_breaker_opens_on_failures():
    """Test circuit breaker opens after failures."""
    org_id = uuid.uuid4()
    ds_id = uuid.uuid4()
    
    # Clear any existing breaker state
    circuit_breaker_registry.clear()
    
    async def fails():
        raise ConnectionError("Test error")
    
    # Trigger failures to open circuit
    for _ in range(5):
        with pytest.raises(ConnectionError):
            await with_circuit_breaker(fails, org_id, ds_id)
    
    # Next call should raise CircuitBreakerOpen
    with pytest.raises(CircuitBreakerOpen, match="اتصال موقتاً تعلیق شد"):
        await with_circuit_breaker(fails, org_id, ds_id)


@pytest.mark.asyncio
async def test_circuit_breaker_registry_per_datasource():
    """Test that circuit breakers are tracked per datasource."""
    org_id = uuid.uuid4()
    ds_id_1 = uuid.uuid4()
    ds_id_2 = uuid.uuid4()
    
    # Clear registry
    circuit_breaker_registry.clear()
    
    breaker1 = circuit_breaker_registry.get_breaker(org_id, ds_id_1)
    breaker2 = circuit_breaker_registry.get_breaker(org_id, ds_id_2)
    
    assert breaker1 is not breaker2
    
    # Open first breaker
    for _ in range(5):
        breaker1.record_failure()
    
    assert breaker1.state == CircuitState.OPEN
    assert breaker2.state == CircuitState.CLOSED
