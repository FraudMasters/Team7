"""
Retry decorator with exponential backoff for transient failures.

This module provides a flexible retry decorator that handles transient failures
with configurable exponential backoff, jitter, and exception filtering.
"""
import functools
import logging
import random
import time
from typing import Callable, Type, Tuple, Union, Optional, Any

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
