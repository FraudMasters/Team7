"""
Rate limiter utility with Redis backend and in-memory fallback.

This module provides a flexible rate limiting solution using the sliding window
counter algorithm. It supports both Redis-backed distributed rate limiting and
an in-memory fallback for development/testing environments.

The rate limiter is designed for:
- API endpoint protection against DoS attacks
- Tiered rate limiting for different operation types
- Graceful degradation when Redis is unavailable
- Thread-safe operation in async contexts

Example:
    >>> from utils.rate_limiter import RateLimiter
    >>> limiter = RateLimiter(storage='memory')
    >>> allowed, info = limiter.is_allowed('user:123', limit=10, window=60)
    >>> if allowed:
    ...     # Process request
    ...     pass
    >>> else:
    ...     retry_after = info.get('retry-after')
    ...     # Return 429 with retry-after header
"""
import logging
import time
import threading
from collections import defaultdict
from typing import Dict, Any, Tuple, Optional, List

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimiter:
    """
    Rate limiter using sliding window algorithm with Redis or in-memory storage.

    This class provides thread-safe rate limiting with configurable storage backends.
    The sliding window algorithm provides accurate rate limiting by tracking request
    timestamps within a rolling time window.

    Storage Options:
        - 'redis': Use Redis for distributed rate limiting (production)
        - 'memory': Use in-memory storage for single-instance rate limiting (development)

    Thread Safety:
        The rate limiter uses thread-local locks for in-memory storage and Redis
        connection pooling for thread-safe Redis operations.

    Args:
        redis_url: Optional Redis connection URL (defaults to settings.redis_url)
        storage: Storage backend - 'redis' or 'memory' (defaults to settings.rate_limit_storage)

    Raises:
        ValueError: If storage type is not 'redis' or 'memory'

    Example:
        >>> limiter = RateLimiter(storage='memory')
        >>> allowed, info = limiter.is_allowed('ip:192.168.1.1', limit=60, window=60)
        >>> print(f"Allowed: {allowed}, Remaining: {info.get('remaining')}")
        Allowed: True, Remaining: 59
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        storage: Optional[str] = None,
    ) -> None:
        """
        Initialize the rate limiter with specified storage backend.

        Args:
            redis_url: Optional Redis URL (defaults to settings.redis_url)
            storage: Storage type - 'redis' or 'memory' (defaults to settings.rate_limit_storage)
        """
        if redis_url is None:
            redis_url = settings.redis_url
        if storage is None:
            storage = settings.rate_limit_storage

        if storage not in ('redis', 'memory'):
            raise ValueError(f"storage must be 'redis' or 'memory', got '{storage}'")

        self.storage = storage
        self.redis_url = redis_url

        # In-memory storage: {key: [timestamp1, timestamp2, ...]}
        self._memory_store: Dict[str, List[float]] = defaultdict(list)
        self._memory_lock = threading.Lock()

        # Redis client (lazy initialization)
        self._redis_client = None

        logger.info(f"RateLimiter initialized with storage={storage}")

    def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a request is allowed under the rate limit.

        This method implements the sliding window algorithm:
        1. Retrieve previous request timestamps for the key
        2. Remove timestamps outside the current window
        3. Count remaining timestamps
        4. If count < limit, allow the request and record the timestamp
        5. Otherwise, deny and calculate retry-after time

        Args:
            key: Unique identifier for the rate limit bucket (e.g., 'ip:127.0.0.1')
            limit: Maximum number of requests allowed within the window
            window: Time window in seconds

        Returns:
            Tuple of (allowed, info) where:
                - allowed: True if request is allowed, False otherwise
                - info: Dictionary with:
                    - 'remaining': Number of requests remaining in window (if allowed)
                    - 'reset': Unix timestamp when window resets
                    - 'retry-after': Seconds until retry is allowed (if denied)
                    - 'limit': The rate limit that was applied
                    - 'window': The window size in seconds

        Example:
            >>> limiter = RateLimiter(storage='memory')
            >>> allowed, info = limiter.is_allowed('user:123', limit=5, window=60)
            >>> if allowed:
            ...     print(f"Request allowed, {info['remaining']} remaining")
            ... else:
            ...     print(f"Rate limited, retry after {info['retry-after']}s")
        """
        try:
            if self.storage == 'redis':
                return self._check_redis(key, limit, window)
            else:
                return self._check_memory(key, limit, window)
        except Exception as e:
            logger.error(f"Error checking rate limit for key={key}: {e}", exc_info=True)
            # Fail open - allow request if rate limiter fails
            return True, {
                'remaining': limit,
                'reset': int(time.time()) + window,
                'limit': limit,
                'window': window,
                'error': str(e),
            }

    def _check_redis(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check rate limit using Redis sorted set (sliding window).

        Uses Redis sorted sets with timestamps as scores for O(log N) operations.
        The sorted set automatically keeps timestamps in sorted order for efficient
        window-based queries.

        Args:
            key: Rate limit bucket identifier
            limit: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            Tuple of (allowed, info) dict with rate limit status

        Example:
            >>> limiter = RateLimiter(storage='redis')
            >>> allowed, info = limiter._check_redis('ip:1.2.3.4', limit=10, window=60)
            >>> (allowed, info.get('remaining', 0))
            (True, 9)
        """
        try:
            import redis

            # Lazy initialization of Redis client
            if self._redis_client is None:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    max_connections=settings.redis_cache_max_connections,
                )

            # Generate Redis key with prefix
            redis_key = f"{settings.redis_cache_key_prefix}:ratelimit:{key}"
            current_time = time.time()
            window_start = current_time - window

            # Remove old entries outside the window
            self._redis_client.zremrangebyscore(redis_key, 0, window_start)

            # Count current requests in window
            current_count = self._redis_client.zcard(redis_key)

            if current_count < limit:
                # Add current request timestamp
                self._redis_client.zadd(redis_key, {str(current_time): current_time})

                # Set expiry to prevent stale keys
                self._redis_client.expire(redis_key, window + 1)

                remaining = limit - (current_count + 1)
                reset_time = int(current_time) + window

                logger.debug(
                    f"Rate limit check passed for key={key}: "
                    f"{current_count + 1}/{limit} used, {remaining} remaining"
                )

                return True, {
                    'remaining': remaining,
                    'reset': reset_time,
                    'limit': limit,
                    'window': window,
                }
            else:
                # Rate limit exceeded - calculate retry_after
                # Get the oldest timestamp in the window
                oldest_timestamps = self._redis_client.zrange(
                    redis_key, 0, 0, withscores=True
                )

                if oldest_timestamps:
                    oldest_timestamp = oldest_timestamps[0][1]
                    retry_after = max(0, int(oldest_timestamp + window - current_time))
                else:
                    retry_after = window

                logger.debug(
                    f"Rate limit exceeded for key={key}: "
                    f"{current_count}/{limit} used, retry after {retry_after}s"
                )

                return False, {
                    'retry-after': retry_after,
                    'reset': int(current_time) + retry_after,
                    'limit': limit,
                    'window': window,
                }

        except Exception as e:
            logger.error(f"Redis rate limit check failed for key={key}: {e}", exc_info=True)
            # Fall back to in-memory if Redis fails
            logger.info("Falling back to in-memory rate limiter")
            return self._check_memory(key, limit, window)

    def _check_memory(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check rate limit using in-memory storage (sliding window).

        Thread-safe implementation using locks. Uses a list of timestamps
        per key with cleanup of expired timestamps on each request.

        Args:
            key: Rate limit bucket identifier
            limit: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            Tuple of (allowed, info) dict with rate limit status

        Example:
            >>> limiter = RateLimiter(storage='memory')
            >>> allowed, info = limiter._check_memory('user:123', limit=5, window=60)
            >>> (allowed, info.get('remaining', 0))
            (True, 4)
        """
        current_time = time.time()
        window_start = current_time - window

        with self._memory_lock:
            # Get or create timestamp list for this key
            timestamps = self._memory_store[key]

            # Remove timestamps outside the current window (in-place)
            # Using list comprehension to filter out old timestamps
            valid_timestamps = [ts for ts in timestamps if ts > window_start]
            self._memory_store[key] = valid_timestamps

            current_count = len(valid_timestamps)

            if current_count < limit:
                # Add current request timestamp
                self._memory_store[key].append(current_time)

                remaining = limit - (current_count + 1)
                reset_time = int(current_time) + window

                logger.debug(
                    f"Rate limit check passed for key={key}: "
                    f"{current_count + 1}/{limit} used, {remaining} remaining"
                )

                return True, {
                    'remaining': remaining,
                    'reset': reset_time,
                    'limit': limit,
                    'window': window,
                }
            else:
                # Rate limit exceeded - calculate retry_after
                # Find the oldest timestamp in the window
                oldest_timestamp = min(valid_timestamps) if valid_timestamps else current_time
                retry_after = max(0, int(oldest_timestamp + window - current_time))

                logger.debug(
                    f"Rate limit exceeded for key={key}: "
                    f"{current_count}/{limit} used, retry after {retry_after}s"
                )

                return False, {
                    'retry-after': retry_after,
                    'reset': int(current_time) + retry_after,
                    'limit': limit,
                    'window': window,
                }

    def reset(self, key: str) -> None:
        """
        Reset the rate limit counter for a specific key.

        This method clears all request history for the given key,
        effectively resetting the rate limit to its initial state.

        Args:
            key: Rate limit bucket identifier to reset

        Example:
            >>> limiter = RateLimiter(storage='memory')
            >>> limiter.is_allowed('user:123', limit=5, window=60)
            (True, {'remaining': 4, ...})
            >>> limiter.reset('user:123')
            >>> limiter.is_allowed('user:123', limit=5, window=60)
            (True, {'remaining': 4, ...})
        """
        try:
            if self.storage == 'redis' and self._redis_client:
                redis_key = f"{settings.redis_cache_key_prefix}:ratelimit:{key}"
                self._redis_client.delete(redis_key)
                logger.info(f"Reset rate limit for key={key} in Redis")
            else:
                with self._memory_lock:
                    if key in self._memory_store:
                        del self._memory_store[key]
                    logger.info(f"Reset rate limit for key={key} in memory")

        except Exception as e:
            logger.error(f"Error resetting rate limit for key={key}: {e}", exc_info=True)

    def get_stats(self, key: str) -> Dict[str, Any]:
        """
        Get current rate limit statistics for a key.

        Returns detailed statistics about the current rate limit state
        without modifying the counter.

        Args:
            key: Rate limit bucket identifier

        Returns:
            Dictionary containing:
                - 'current_count': Number of requests in current window
                - 'limit': Rate limit (if provided)
                - 'window': Window size in seconds (if provided)
                - 'reset': Unix timestamp when window resets
                - 'storage': Storage backend being used

        Example:
            >>> limiter = RateLimiter(storage='memory')
            >>> limiter.is_allowed('user:123', limit=10, window=60)
            (True, {'remaining': 9, ...})
            >>> stats = limiter.get_stats('user:123')
            >>> stats['current_count']
            1
        """
        try:
            current_time = time.time()

            if self.storage == 'redis' and self._redis_client:
                redis_key = f"{settings.redis_cache_key_prefix}:ratelimit:{key}"
                window_start = current_time - 60  # Default window for stats

                # Count requests in default window
                count = self._redis_client.zcount(redis_key, window_start, current_time)

                return {
                    'current_count': count,
                    'window': 60,
                    'reset': int(current_time) + 60,
                    'storage': 'redis',
                }
            else:
                with self._memory_lock:
                    timestamps = self._memory_store.get(key, [])
                    window_start = current_time - 60  # Default window for stats
                    valid_timestamps = [ts for ts in timestamps if ts > window_start]

                    return {
                        'current_count': len(valid_timestamps),
                        'window': 60,
                        'reset': int(current_time) + 60,
                        'storage': 'memory',
                    }

        except Exception as e:
            logger.error(f"Error getting stats for key={key}: {e}", exc_info=True)
            return {
                'current_count': 0,
                'window': 60,
                'reset': int(time.time()) + 60,
                'storage': self.storage,
                'error': str(e),
            }
