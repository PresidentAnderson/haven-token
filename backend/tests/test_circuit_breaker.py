"""
Tests for Circuit Breaker Pattern
"""

import pytest
import time
from unittest.mock import MagicMock
import redis

from middleware.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerConfig,
    get_circuit_breaker,
    register_circuit_breaker
)
from exceptions import CircuitBreakerOpenError


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = MagicMock(spec=redis.Redis)
    mock.get = MagicMock(return_value=None)
    mock.set = MagicMock(return_value=True)
    mock.incr = MagicMock(return_value=1)
    mock.delete = MagicMock(return_value=True)
    mock.exists = MagicMock(return_value=False)
    return mock


@pytest.fixture
def circuit_breaker_config():
    """Create circuit breaker configuration."""
    return CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=5,
        expected_exception=Exception
    )


@pytest.fixture
def circuit_breaker(mock_redis, circuit_breaker_config):
    """Create CircuitBreaker instance."""
    return CircuitBreaker(
        name="test_circuit",
        redis_client=mock_redis,
        config=circuit_breaker_config
    )


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions."""

    def test_initial_state_is_closed(self, circuit_breaker, mock_redis):
        """Test that initial state is CLOSED."""
        mock_redis.get.return_value = None
        state = circuit_breaker.get_state()
        assert state == CircuitState.CLOSED

    def test_transitions_to_open_after_failures(self, circuit_breaker, mock_redis):
        """Test that circuit opens after threshold failures."""
        mock_redis.get.side_effect = [
            CircuitState.CLOSED.value.encode(),  # Initial state
            "1",  # First failure count
            "2",  # Second failure count
            "3",  # Third failure count
        ]
        mock_redis.incr.side_effect = [1, 2, 3]

        def failing_function():
            raise Exception("Test failure")

        # Should fail and increment counter
        for i in range(3):
            try:
                circuit_breaker.call(failing_function)
            except Exception:
                pass

        # Circuit should be open now
        assert mock_redis.set.called

    def test_open_circuit_blocks_calls(self, circuit_breaker, mock_redis):
        """Test that OPEN circuit blocks calls."""
        mock_redis.get.return_value = CircuitState.OPEN.value.encode()
        mock_redis.set.return_value = True

        def test_function():
            return "success"

        with pytest.raises(CircuitBreakerOpenError):
            circuit_breaker.call(test_function)

    def test_transitions_to_half_open_after_timeout(self, circuit_breaker, mock_redis):
        """Test transition to HALF_OPEN after timeout."""
        # Set up OPEN state with expired timeout
        mock_redis.get.side_effect = [
            CircuitState.OPEN.value.encode(),
            str(time.time() - 10)  # Last failure 10 seconds ago (> 5s timeout)
        ]

        def test_function():
            return "success"

        # Should transition to HALF_OPEN and allow the call
        result = circuit_breaker.call(test_function)
        assert result == "success"

    def test_half_open_closes_after_successes(self, circuit_breaker, mock_redis):
        """Test that HALF_OPEN closes after success threshold."""
        mock_redis.get.return_value = CircuitState.HALF_OPEN.value.encode()
        mock_redis.incr.side_effect = [1, 2]

        def test_function():
            return "success"

        # First success
        circuit_breaker.call(test_function)
        # Second success - should close circuit
        circuit_breaker.call(test_function)

        assert mock_redis.set.called

    def test_half_open_reopens_on_failure(self, circuit_breaker, mock_redis):
        """Test that HALF_OPEN reopens on any failure."""
        mock_redis.get.return_value = CircuitState.HALF_OPEN.value.encode()

        def failing_function():
            raise Exception("Test failure")

        try:
            circuit_breaker.call(failing_function)
        except Exception:
            pass

        # Should set state back to OPEN
        assert mock_redis.set.called


class TestCircuitBreakerCalls:
    """Test circuit breaker function calls."""

    def test_successful_call_returns_result(self, circuit_breaker, mock_redis):
        """Test that successful call returns result."""
        mock_redis.get.return_value = CircuitState.CLOSED.value.encode()

        def test_function(x, y):
            return x + y

        result = circuit_breaker.call(test_function, 2, 3)
        assert result == 5

    def test_failed_call_raises_exception(self, circuit_breaker, mock_redis):
        """Test that failed call raises exception."""
        mock_redis.get.return_value = CircuitState.CLOSED.value.encode()

        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            circuit_breaker.call(failing_function)

    def test_decorator_usage(self, circuit_breaker):
        """Test using circuit breaker as decorator."""
        @circuit_breaker
        def decorated_function(x):
            return x * 2

        # Note: This will use the mocked redis
        result = decorated_function(5)
        assert result == 10


class TestCircuitBreakerStatus:
    """Test circuit breaker status reporting."""

    def test_get_status(self, circuit_breaker, mock_redis):
        """Test getting circuit breaker status."""
        mock_redis.get.side_effect = [
            CircuitState.CLOSED.value.encode(),
            "2",  # failure count
            "0",  # success count
            None  # last failure time
        ]

        status = circuit_breaker.get_status()

        assert status["name"] == "test_circuit"
        assert status["state"] == CircuitState.CLOSED.value
        assert "failure_count" in status
        assert "success_count" in status

    def test_manual_reset(self, circuit_breaker, mock_redis):
        """Test manual circuit breaker reset."""
        circuit_breaker.reset()

        # Should set state to CLOSED
        assert mock_redis.set.called
        # Should reset counters
        assert mock_redis.delete.called


class TestCircuitBreakerRegistry:
    """Test circuit breaker registry."""

    def test_register_circuit_breaker(self, mock_redis, circuit_breaker_config):
        """Test registering a circuit breaker."""
        cb = register_circuit_breaker(
            name="registry_test",
            redis_client=mock_redis,
            config=circuit_breaker_config
        )

        assert cb is not None
        assert cb.name == "registry_test"

    def test_get_registered_circuit_breaker(self, mock_redis, circuit_breaker_config):
        """Test getting a registered circuit breaker."""
        register_circuit_breaker(
            name="get_test",
            redis_client=mock_redis,
            config=circuit_breaker_config
        )

        cb = get_circuit_breaker("get_test")
        assert cb is not None
        assert cb.name == "get_test"

    def test_get_nonexistent_circuit_breaker(self):
        """Test getting nonexistent circuit breaker returns None."""
        cb = get_circuit_breaker("nonexistent")
        assert cb is None


class TestCircuitBreakerConfig:
    """Test circuit breaker configuration."""

    def test_custom_config(self, mock_redis):
        """Test circuit breaker with custom configuration."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=5,
            timeout_seconds=60,
            expected_exception=ValueError
        )

        cb = CircuitBreaker("custom_test", mock_redis, config)

        assert cb.config.failure_threshold == 10
        assert cb.config.success_threshold == 5
        assert cb.config.timeout_seconds == 60
        assert cb.config.expected_exception == ValueError

    def test_default_config(self, mock_redis):
        """Test circuit breaker with default configuration."""
        cb = CircuitBreaker("default_test", mock_redis)

        assert cb.config.failure_threshold == 5
        assert cb.config.success_threshold == 2
        assert cb.config.timeout_seconds == 30
