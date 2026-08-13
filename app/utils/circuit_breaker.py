"""
Circuit Breaker Pattern Implementation
Protection against cascade failures and API overload
"""

import time
import threading
import logging
from enum import Enum
from functools import wraps
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing - reject all requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit Breaker implementation to protect against cascade failures.
    
    Args:
        name: Unique identifier for the circuit breaker
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before trying recovery
        success_threshold: Successes needed in HALF_OPEN to close circuit
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0
        self._lock = threading.Lock()
        
        logger.info(f"CircuitBreaker '{name}' initialized (threshold={failure_threshold}, timeout={recovery_timeout}s)")
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state with automatic transition logic"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(f"CircuitBreaker '{self.name}' transitioning to HALF_OPEN")
            return self._state
    
    def record_success(self):
        """Record a successful call"""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(f"CircuitBreaker '{self.name}' CLOSED (recovery successful)")
            else:
                self._failure_count = 0
    
    def record_failure(self):
        """Record a failed call"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"CircuitBreaker '{self.name}' OPEN (failure in HALF_OPEN)")
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(f"CircuitBreaker '{self.name}' OPEN (threshold reached: {self.failure_threshold})")
    
    def allow_request(self) -> bool:
        """Check if a request should be allowed"""
        return self.state != CircuitState.OPEN
    
    def __repr__(self) -> str:
        return f"CircuitBreaker(name='{self.name}', state={self.state.value}, failures={self._failure_count})"


# Global circuit breakers for different services
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create a circuit breaker"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, **kwargs)
    return _circuit_breakers[name]


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    success_threshold: int = 3,
    fallback: Optional[Callable] = None
):
    """
    Decorator to apply circuit breaker protection to a function.
    
    Args:
        name: Unique circuit breaker name
        failure_threshold: Failures before opening
        recovery_timeout: Seconds before trying recovery
        success_threshold: Successes needed to close
        fallback: Optional fallback function
    """
    def decorator(func: Callable) -> Callable:
        cb = get_circuit_breaker(
            name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not cb.allow_request():
                logger.warning(f"CircuitBreaker '{name}' is OPEN - request rejected")
                if fallback:
                    return fallback(*args, **kwargs)
                raise CircuitBreakerOpenError(f"Circuit '{name}' is open")
            
            try:
                result = func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                logger.error(f"CircuitBreaker '{name}' recorded failure: {e}")
                if fallback:
                    return fallback(*args, **kwargs)
                raise
        
        return wrapper
    return decorator


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


# Specific circuit breakers for TSE Analysis services
TSETMC_CIRCUIT = "tsetmc_api"
TGJU_CIRCUIT = "tgju_api"
DATABASE_CIRCUIT = "database"

# Initialize default circuit breakers
get_circuit_breaker(TSETMC_CIRCUIT, failure_threshold=5, recovery_timeout=60)
get_circuit_breaker(TGJU_CIRCUIT, failure_threshold=3, recovery_timeout=30)
get_circuit_breaker(DATABASE_CIRCUIT, failure_threshold=10, recovery_timeout=30)


def get_circuit_status() -> dict:
    """Get status of all circuit breakers"""
    return {
        name: {
            "state": cb.state.value,
            "failure_count": cb._failure_count,
            "last_failure": cb._last_failure_time
        }
        for name, cb in _circuit_breakers.items()
    }
