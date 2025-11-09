"""
Circuit Breaker Pattern Implementation
Protects against cascading failures from blockchain connection issues.
"""

import logging
import time
from enum import Enum
from typing import Optional, Callable, Any
from datetime import datetime, timedelta
from functools import wraps
import redis

from exceptions import CircuitBreakerOpenError, BlockchainError

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 30,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker configuration.

        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes needed to close from half-open
            timeout_seconds: Seconds to wait before transitioning to half-open
            expected_exception: Exception type to catch (defaults to all exceptions)
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.expected_exception = expected_exception


class CircuitBreaker:
    """
    Circuit breaker implementation with Redis-backed state.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing if service recovered, limited requests allowed

    Flow:
    CLOSED -> OPEN (after failure_threshold failures)
    OPEN -> HALF_OPEN (after timeout_seconds)
    HALF_OPEN -> CLOSED (after success_threshold successes)
    HALF_OPEN -> OPEN (on any failure)
    """

    def __init__(
        self,
        name: str,
        redis_client: redis.Redis,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Unique name for this circuit breaker
            redis_client: Redis client for state storage
            config: Circuit breaker configuration
        """
        self.name = name
        self.redis = redis_client
        self.config = config or CircuitBreakerConfig()

        logger.info(
            f"🔌 CircuitBreaker '{name}' initialized: "
            f"failure_threshold={self.config.failure_threshold}, "
            f"timeout={self.config.timeout_seconds}s"
        )

    def _get_state_key(self) -> str:
        """Get Redis key for circuit state."""
        return f"circuit_breaker:{self.name}:state"

    def _get_failure_count_key(self) -> str:
        """Get Redis key for failure count."""
        return f"circuit_breaker:{self.name}:failures"

    def _get_success_count_key(self) -> str:
        """Get Redis key for success count."""
        return f"circuit_breaker:{self.name}:successes"

    def _get_last_failure_key(self) -> str:
        """Get Redis key for last failure timestamp."""
        return f"circuit_breaker:{self.name}:last_failure"

    def get_state(self) -> CircuitState:
        """
        Get current circuit state.

        Returns:
            Current circuit state
        """
        state = self.redis.get(self._get_state_key())
        if state is None:
            return CircuitState.CLOSED
        return CircuitState(state.decode() if isinstance(state, bytes) else state)

    def _set_state(self, state: CircuitState):
        """Set circuit state."""
        self.redis.set(self._get_state_key(), state.value)
        logger.info(f"🔌 Circuit '{self.name}' state changed to {state.value}")

    def _get_failure_count(self) -> int:
        """Get current failure count."""
        count = self.redis.get(self._get_failure_count_key())
        return int(count) if count else 0

    def _increment_failure_count(self) -> int:
        """Increment and return failure count."""
        count = self.redis.incr(self._get_failure_count_key())
        self.redis.set(self._get_last_failure_key(), str(time.time()))
        return count

    def _reset_failure_count(self):
        """Reset failure count."""
        self.redis.delete(self._get_failure_count_key())

    def _get_success_count(self) -> int:
        """Get current success count."""
        count = self.redis.get(self._get_success_count_key())
        return int(count) if count else 0

    def _increment_success_count(self) -> int:
        """Increment and return success count."""
        return self.redis.incr(self._get_success_count_key())

    def _reset_success_count(self):
        """Reset success count."""
        self.redis.delete(self._get_success_count_key())

    def _should_attempt_reset(self) -> bool:
        """
        Check if enough time has passed to attempt reset.

        Returns:
            True if timeout has elapsed since last failure
        """
        last_failure = self.redis.get(self._get_last_failure_key())
        if last_failure is None:
            return True

        last_failure_time = float(last_failure)
        time_since_failure = time.time() - last_failure_time

        return time_since_failure >= self.config.timeout_seconds

    def _on_success(self):
        """Handle successful call."""
        state = self.get_state()

        if state == CircuitState.HALF_OPEN:
            success_count = self._increment_success_count()
            logger.debug(f"🔌 Circuit '{self.name}' success in HALF_OPEN: {success_count}/{self.config.success_threshold}")

            if success_count >= self.config.success_threshold:
                # Enough successes, close the circuit
                self._set_state(CircuitState.CLOSED)
                self._reset_failure_count()
                self._reset_success_count()
                logger.info(f"✅ Circuit '{self.name}' recovered and CLOSED")

        elif state == CircuitState.CLOSED:
            # In closed state, reset failure count on success
            self._reset_failure_count()

    def _on_failure(self, exception: Exception):
        """Handle failed call."""
        state = self.get_state()

        if state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately opens circuit
            self._set_state(CircuitState.OPEN)
            self._reset_success_count()
            self._increment_failure_count()
            logger.warning(f"⚠️  Circuit '{self.name}' failed in HALF_OPEN, reopening")

        elif state == CircuitState.CLOSED:
            failure_count = self._increment_failure_count()
            logger.warning(
                f"⚠️  Circuit '{self.name}' failure {failure_count}/{self.config.failure_threshold}: {exception}"
            )

            if failure_count >= self.config.failure_threshold:
                # Too many failures, open the circuit
                self._set_state(CircuitState.OPEN)
                logger.error(f"🔴 Circuit '{self.name}' OPENED after {failure_count} failures")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function through circuit breaker.

        Args:
            func: Function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result of function call

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception from the function call
        """
        state = self.get_state()

        # Check if circuit is open
        if state == CircuitState.OPEN:
            if self._should_attempt_reset():
                # Timeout elapsed, try half-open
                self._set_state(CircuitState.HALF_OPEN)
                self._reset_success_count()
                logger.info(f"🟡 Circuit '{self.name}' attempting recovery (HALF_OPEN)")
            else:
                # Still in timeout, reject call
                raise CircuitBreakerOpenError(
                    service_name=self.name,
                    details={
                        "failure_count": self._get_failure_count(),
                        "state": state.value
                    }
                )

        # Attempt the call
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except self.config.expected_exception as e:
            self._on_failure(e)
            raise

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to wrap function with circuit breaker.

        Usage:
            @circuit_breaker
            def my_function():
                ...
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)

        return wrapper

    def get_status(self) -> dict:
        """
        Get circuit breaker status for monitoring.

        Returns:
            Dictionary with circuit breaker status
        """
        state = self.get_state()
        failure_count = self._get_failure_count()
        success_count = self._get_success_count()

        last_failure = self.redis.get(self._get_last_failure_key())
        last_failure_time = None
        time_since_failure = None

        if last_failure:
            last_failure_time = float(last_failure)
            time_since_failure = time.time() - last_failure_time

        return {
            "name": self.name,
            "state": state.value,
            "failure_count": failure_count,
            "success_count": success_count,
            "failure_threshold": self.config.failure_threshold,
            "success_threshold": self.config.success_threshold,
            "timeout_seconds": self.config.timeout_seconds,
            "last_failure_time": datetime.fromtimestamp(last_failure_time).isoformat() if last_failure_time else None,
            "time_since_failure_seconds": round(time_since_failure, 2) if time_since_failure else None,
            "should_attempt_reset": self._should_attempt_reset()
        }

    def reset(self):
        """
        Manually reset circuit breaker to closed state.
        Use with caution - typically for administrative purposes only.
        """
        self._set_state(CircuitState.CLOSED)
        self._reset_failure_count()
        self._reset_success_count()
        self.redis.delete(self._get_last_failure_key())
        logger.warning(f"⚠️  Circuit '{self.name}' manually reset to CLOSED")


# Global circuit breakers registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """
    Get circuit breaker by name.

    Args:
        name: Circuit breaker name

    Returns:
        CircuitBreaker instance or None
    """
    return _circuit_breakers.get(name)


def register_circuit_breaker(
    name: str,
    redis_client: redis.Redis,
    config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """
    Register a new circuit breaker.

    Args:
        name: Unique name for circuit breaker
        redis_client: Redis client
        config: Circuit breaker configuration

    Returns:
        CircuitBreaker instance
    """
    if name in _circuit_breakers:
        logger.warning(f"Circuit breaker '{name}' already registered")
        return _circuit_breakers[name]

    circuit_breaker = CircuitBreaker(name, redis_client, config)
    _circuit_breakers[name] = circuit_breaker
    return circuit_breaker


def get_all_circuit_breakers() -> dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    return _circuit_breakers.copy()


def get_all_statuses() -> dict[str, dict]:
    """
    Get status of all circuit breakers.

    Returns:
        Dictionary mapping circuit breaker names to their status
    """
    return {
        name: cb.get_status()
        for name, cb in _circuit_breakers.items()
    }


# Decorator for easier usage
def circuit_breaker(
    name: str,
    redis_client: Optional[redis.Redis] = None,
    config: Optional[CircuitBreakerConfig] = None
):
    """
    Decorator to apply circuit breaker to a function.

    Args:
        name: Circuit breaker name
        redis_client: Redis client (uses existing if not provided)
        config: Circuit breaker configuration

    Usage:
        @circuit_breaker("my_service")
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Get or create circuit breaker
        cb = get_circuit_breaker(name)
        if cb is None:
            if redis_client is None:
                raise ValueError(f"Redis client required for new circuit breaker '{name}'")
            cb = register_circuit_breaker(name, redis_client, config)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)

        return wrapper

    return decorator
