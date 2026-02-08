"""
Retry decorator with exponential backoff for transient failures.

This module provides a flexible retry decorator that handles transient failures
with configurable exponential backoff, jitter, and exception filtering.
It also includes a circuit breaker pattern for preventing cascading failures.
"""
import functools
import logging
import random
import time
from typing import Callable, Type, Tuple, Union, Optional, Any, Dict

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable:
    """
    Decorator that retries a function with exponential backoff on failure.

    The delay between retries increases exponentially (initial_delay * backoff_factor^attempt).
    Optional jitter adds randomness to prevent thundering herd problems.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        backoff_factor: Multiplier for delay after each attempt (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        jitter: Whether to add random jitter to delays (default: True)
        exceptions: Exception type(s) to catch and retry on (default: Exception)
        on_retry: Optional callback function called on each retry.
                   Receives (exception, attempt_number) as arguments.

    Returns:
        Decorated function that retries on failure with exponential backoff

    Raises:
        The last exception caught if all retries are exhausted

    Example:
        >>> @retry_with_backoff(max_retries=3, initial_delay=0.5)
        ... def fetch_data(url):
        ...     return requests.get(url)
        >>>
        >>> # Custom exception types
        >>> @retry_with_backoff(
        ...     max_retries=5,
        ...     exceptions=(ConnectionError, TimeoutError)
        ... )
        ... def connect_database():
        ...     return db.connect()
        >>>
        >>> # With retry callback
        >>> def log_retry(exc, attempt):
        ...     logger.warning(f"Attempt {attempt} failed: {exc}")
        >>> @retry_with_backoff(on_retry=log_retry)
        ... def process_payment():
        ...     return payment_api.charge()

    Note:
        - Jitter adds +/- 25% randomness to delay to prevent synchronized retries
        - Use specific exception types for better error handling
        - The decorated function's return type is preserved
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    # Don't retry after the last attempt
                    if attempt >= max_retries:
                        logger.error(
                            f"Function '{func.__name__}' failed after {max_retries} retries: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(initial_delay * (backoff_factor ** attempt), max_delay)

                    # Add jitter to prevent thundering herd
                    if jitter:
                        jitter_amount = delay * 0.25  # +/- 25%
                        delay = delay + random.uniform(-jitter_amount, jitter_amount)
                        delay = max(0, delay)  # Ensure non-negative

                    logger.warning(
                        f"Function '{func.__name__}' failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )

                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(e, attempt + 1)
                        except Exception as callback_error:
                            logger.error(f"Retry callback failed: {callback_error}")

                    # Wait before retry
                    time.sleep(delay)

            # Should never reach here, but satisfy type checker
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def async_retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable[[Exception, int], Any]] = None,
) -> Callable:
    """
    Async decorator that retries an async function with exponential backoff.

    This is the async version of retry_with_backoff for use with async/await.
    Uses asyncio.sleep instead of time.sleep for non-blocking delays.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        backoff_factor: Multiplier for delay after each attempt (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        jitter: Whether to add random jitter to delays (default: True)
        exceptions: Exception type(s) to catch and retry on (default: Exception)
        on_retry: Optional async callback function called on each retry.
                   Receives (exception, attempt_number) as arguments.

    Returns:
        Decorated async function that retries on failure with exponential backoff

    Raises:
        The last exception caught if all retries are exhausted

    Example:
        >>> @async_retry_with_backoff(max_retries=3)
        ... async def fetch_api_data(url):
        ...     async with aiohttp.ClientSession() as session:
        ...         async with session.get(url) as response:
        ...             return await response.json()
    """
    import asyncio

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    # Don't retry after the last attempt
                    if attempt >= max_retries:
                        logger.error(
                            f"Async function '{func.__name__}' failed after {max_retries} retries: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(initial_delay * (backoff_factor ** attempt), max_delay)

                    # Add jitter to prevent thundering herd
                    if jitter:
                        jitter_amount = delay * 0.25  # +/- 25%
                        delay = delay + random.uniform(-jitter_amount, jitter_amount)
                        delay = max(0, delay)  # Ensure non-negative

                    logger.warning(
                        f"Async function '{func.__name__}' failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )

                    # Call retry callback if provided
                    if on_retry:
                        try:
                            result = on_retry(e, attempt + 1)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception as callback_error:
                            logger.error(f"Retry callback failed: {callback_error}")

                    # Wait before retry
                    await asyncio.sleep(delay)

            # Should never reach here, but satisfy type checker
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for preventing cascading failures.

    The circuit breaker monitors failures and "opens" the circuit (blocks requests)
    when failures exceed a threshold within a time window. After a timeout, it enters
    a "half-open" state allowing a test request to determine if the service has recovered.

    States:
        - CLOSED: Normal operation, requests pass through
        - OPEN: Circuit is tripped, requests fail fast without executing
        - HALF_OPEN: Test mode, allows one request to check if service recovered

    Args:
        failure_threshold: Number of failures to trigger opening (default: 5)
        timeout_seconds: Seconds to wait before transitioning from OPEN to HALF_OPEN (default: 60)
        success_threshold: Successful calls needed to close circuit from HALF_OPEN (default: 1)

    Example:
        >>> breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=30)
        >>>
        >>> @breaker
        >>> def external_api_call():
        ...     return requests.get("https://api.example.com/data")
        >>>
        >>> # Or use as context manager
        >>> with breaker:
        ...     result = external_api_call()
    """

    # Circuit states
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: float = 60.0,
        success_threshold: int = 1,
    ):
        """
        Initialize the circuit breaker.

        Args:
            failure_threshold: Number of failures to trigger opening
            timeout_seconds: Seconds to wait before transitioning from OPEN to HALF_OPEN
            success_threshold: Successful calls needed to close circuit from HALF_OPEN
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold

        # State tracking
        self._state = self.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0
        self._opened_at = 0

    @property
    def state(self) -> str:
        """Get current circuit state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    @property
    def is_open(self) -> bool:
        """Check if circuit is currently open (blocking requests)."""
        if self._state == self.OPEN:
            # Check if timeout has elapsed
            if time.time() - self._opened_at >= self.timeout_seconds:
                logger.info("Circuit breaker timeout elapsed, transitioning to HALF_OPEN")
                self._state = self.HALF_OPEN
                self._success_count = 0
                return False
            return True
        return False

    def record_success(self):
        """
        Record a successful operation.

        Transitions state:
        - HALF_OPEN -> CLOSED if success threshold reached
        - Resets failure count in CLOSED state
        """
        if self._state == self.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                logger.info("Circuit breaker: success threshold reached, closing circuit")
                self._state = self.CLOSED
                self._failure_count = 0
                self._success_count = 0
        elif self._state == self.CLOSED:
            self._failure_count = max(0, self._failure_count - 1)

    def record_failure(self):
        """
        Record a failed operation.

        Transitions state:
        - CLOSED -> OPEN if failure threshold reached
        - HALF_OPEN -> OPEN on any failure
        """
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == self.HALF_OPEN:
            logger.warning("Circuit breaker: failure in HALF_OPEN state, opening circuit")
            self._state = self.OPEN
            self._opened_at = time.time()
        elif self._state == self.CLOSED:
            if self._failure_count >= self.failure_threshold:
                logger.warning(
                    f"Circuit breaker: failure threshold ({self.failure_threshold}) reached, opening circuit"
                )
                self._state = self.OPEN
                self._opened_at = time.time()

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to use circuit breaker with a function.

        Args:
            func: Function to protect with circuit breaker

        Returns:
            Wrapped function that honors circuit state
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self.execute(func, *args, **kwargs)

        return wrapper

    def execute(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result of function execution

        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
            Exception: Any exception from the decorated function
        """
        if self.is_open:
            raise CircuitBreakerOpenError(
                f"Circuit breaker is OPEN for '{func.__name__}'. "
                f"Last failure: {time.time() - self._last_failure_time:.1f}s ago. "
                f"Timeout: {self.timeout_seconds}s"
            )

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def __enter__(self):
        """Context manager entry - raises if circuit is open."""
        if self.is_open:
            raise CircuitBreakerOpenError(
                f"Circuit breaker is OPEN. "
                f"Timeout: {self.timeout_seconds}s"
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - records success/failure."""
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure()
        return False  # Don't suppress exceptions

    def reset(self):
        """Reset circuit breaker to CLOSED state (for testing/recovery)."""
        logger.info("Circuit breaker: manual reset to CLOSED state")
        self._state = self.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0
        self._opened_at = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics.

        Returns:
            Dictionary with current stats
        """
        return {
            "state": self._state,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "timeout_seconds": self.timeout_seconds,
            "last_failure_time": self._last_failure_time,
            "opened_at": self._opened_at,
            "time_since_open": time.time() - self._opened_at if self._opened_at else 0,
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when attempting to call a function with an open circuit."""

    def __init__(self, message: str = "Circuit breaker is OPEN"):
        self.message = message
        super().__init__(self.message)
