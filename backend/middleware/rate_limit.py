"""
Rate limiting middleware using Redis for distributed rate limiting.

This module provides a FastAPI middleware for rate limiting API requests
based on API keys with configurable quotas. Uses Redis for distributed
rate limiting with sliding window algorithm.

Supports multiple rate limit windows:
- requests_per_minute: Short-term burst protection
- requests_per_hour: Medium-term usage limits
- requests_per_day: Long-term daily quotas

Rate limits are stored in Redis with automatic expiration.
"""
import hashlib
import logging
from typing import Any, Dict, Optional

from fastapi import Request, Response, status, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from redis.asyncio import Redis, ConnectionPool

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global Redis connection pool
_redis_pool: Optional[ConnectionPool] = None


def get_redis_pool() -> ConnectionPool:
    """
    Get or create the Redis connection pool.

    Returns:
        Redis connection pool

    Example:
        >>> pool = get_redis_pool()
        >>> redis = Redis(connection_pool=pool)
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info(f"Created Redis connection pool: {settings.redis_url[:30]}...")
    return _redis_pool


async def get_redis_client() -> Redis:
    """
    Get a Redis client from the connection pool.

    Returns:
        Redis client instance

    Example:
        >>> redis = await get_redis_client()
        >>> await redis.set("key", "value")
    """
    pool = get_redis_pool()
    return Redis(connection_pool=pool)


async def close_redis_pool():
    """
    Close the Redis connection pool.

    Should be called during application shutdown.

    Example:
        >>> await close_redis_pool()
    """
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None
        logger.info("Redis connection pool closed")


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256 for Redis key generation.

    Args:
        api_key: The API key to hash

    Returns:
        The SHA-256 hash of the API key as a hex string

    Example:
        >>> key = "test_key_12345"
        >>> hashed = hash_api_key(key)
        >>> len(hashed)
        64
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_rate_limit_key(key_hash: str, window: str) -> str:
    """
    Generate Redis key for rate limit counter.

    Args:
        key_hash: Hashed API key
        window: Rate limit window (minute, hour, day)

    Returns:
        Redis key string

    Example:
        >>> key = get_rate_limit_key("abc123", "minute")
        >>> "rate_limit:abc123:minute"
    """
    return f"rate_limit:{key_hash}:{window}"


async def check_rate_limit(
    redis: Redis,
    key_hash: str,
    window: str,
    limit: int,
    window_seconds: int,
) -> Dict[str, Any]:
    """
    Check if request is within rate limit using sliding window.

    Args:
        redis: Redis client
        key_hash: Hashed API key
        window: Rate limit window (minute, hour, day)
        limit: Maximum requests allowed in the window
        window_seconds: Window size in seconds

    Returns:
        Dictionary with:
        - allowed: bool indicating if request is allowed
        - remaining: number of requests remaining
        - reset_time: timestamp when window resets
        - current_count: current request count

    Example:
        >>> result = await check_rate_limit(redis, "abc123", "minute", 60, 60)
        >>> if not result["allowed"]:
        ...     print("Rate limit exceeded")
    """
    redis_key = get_rate_limit_key(key_hash, window)

    # Get current count
    current_count = await redis.get(redis_key)
    current_count = int(current_count) if current_count else 0

    # Get TTL for reset time calculation
    ttl = await redis.ttl(redis_key)
    reset_time = None
    if ttl > 0:
        from time import time
        reset_time = int(time() + ttl)

    # Check if limit exceeded
    if current_count >= limit:
        return {
            "allowed": False,
            "remaining": 0,
            "reset_time": reset_time,
            "current_count": current_count,
        }

    # Increment counter
    new_count = await redis.incr(redis_key)

    # Set expiration if this is the first request in the window
    if new_count == 1:
        await redis.expire(redis_key, window_seconds)

    # Calculate remaining requests
    remaining = max(0, limit - new_count)

    return {
        "allowed": True,
        "remaining": remaining,
        "reset_time": reset_time,
        "current_count": new_count,
    }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI using Redis.

    This middleware checks API key rate limits before allowing requests
    to proceed. It supports multiple rate limit windows and returns
    appropriate HTTP headers indicating rate limit status.

    Rate limits are checked in order: minute -> hour -> day
    If any limit is exceeded, the request is rejected.

    Attributes:
        app: The ASGI application
        default_limits: Default rate limits for unauthenticated requests
        exclude_paths: List of paths to exclude from rate limiting

    Example:
        >>> app = FastAPI()
        >>> app.add_middleware(RateLimitMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        default_limits: Optional[Dict[str, int]] = None,
        exclude_paths: Optional[list[str]] = None,
    ) -> None:
        """
        Initialize the rate limiting middleware.

        Args:
            app: The ASGI application
            default_limits: Default rate limits for requests without API keys
                           Format: {"requests_per_minute": 60, ...}
            exclude_paths: List of path prefixes to exclude from rate limiting
        """
        super().__init__(app)
        self.default_limits = default_limits or {
            "requests_per_minute": 20,
            "requests_per_hour": 100,
            "requests_per_day": 1000,
        }
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/ready",
            "/favicon.ico",
            "/static",
        ]
        logger.info(
            f"RateLimitMiddleware initialized - default limits: {self.default_limits}"
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request through rate limiting middleware.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            HTTP response with rate limit headers

        Raises:
            HTTPException(429): If rate limit is exceeded
        """
        # Check if path should be excluded
        if any(
            request.url.path.startswith(path) for path in self.exclude_paths
        ):
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key", "")

        # If no API key, use IP address as identifier
        if not api_key:
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            else:
                client_ip = request.client.host if request.client else "unknown"
            identifier = client_ip
            limits = self.default_limits
        else:
            identifier = api_key
            # Get rate limits from API key (stored in request state by auth middleware)
            # For now, use default limits
            # TODO: Query database for API key rate limits
            limits = self.default_limits

        # Hash the identifier
        key_hash = hash_api_key(identifier)

        # Get Redis client
        redis = await get_redis_client()

        # Check rate limits
        rate_limit_results = {}
        overall_allowed = True
        exceeded_window = None

        # Check per-minute limit
        if "requests_per_minute" in limits:
            result = await check_rate_limit(
                redis,
                key_hash,
                "minute",
                limits["requests_per_minute"],
                60,  # 60 seconds
            )
            rate_limit_results["minute"] = result
            if not result["allowed"]:
                overall_allowed = False
                exceeded_window = "minute"

        # Check per-hour limit (only if minute limit passed)
        if overall_allowed and "requests_per_hour" in limits:
            result = await check_rate_limit(
                redis,
                key_hash,
                "hour",
                limits["requests_per_hour"],
                3600,  # 3600 seconds = 1 hour
            )
            rate_limit_results["hour"] = result
            if not result["allowed"]:
                overall_allowed = False
                exceeded_window = "hour"

        # Check per-day limit (only if hour limit passed)
        if overall_allowed and "requests_per_day" in limits:
            result = await check_rate_limit(
                redis,
                key_hash,
                "day",
                limits["requests_per_day"],
                86400,  # 86400 seconds = 24 hours
            )
            rate_limit_results["day"] = result
            if not result["allowed"]:
                overall_allowed = False
                exceeded_window = "day"

        # Get the most restrictive limit for headers
        minute_result = rate_limit_results.get("minute", {})
        hour_result = rate_limit_results.get("hour", {})
        day_result = rate_limit_results.get("day", {})

        # If rate limit exceeded, return 429
        if not overall_allowed:
            logger.warning(
                f"Rate limit exceeded for {identifier[:8]}... - window: {exceeded_window}"
            )

            retry_after = 60
            reset_time = None

            if exceeded_window == "minute" and minute_result.get("reset_time"):
                reset_time = minute_result["reset_time"]
                retry_after = max(1, reset_time - int(__import__("time").time()))
            elif exceeded_window == "hour" and hour_result.get("reset_time"):
                reset_time = hour_result["reset_time"]
                retry_after = max(1, reset_time - int(__import__("time").time()))
            elif exceeded_window == "day" and day_result.get("reset_time"):
                reset_time = day_result["reset_time"]
                retry_after = max(1, reset_time - int(__import__("time").time()))

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "window": exceeded_window,
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limits.get(f"requests_per_{exceeded_window}", 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time) if reset_time else "",
                },
            )

        # Process the request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit-Minute"] = str(
            limits.get("requests_per_minute", 0)
        )
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            minute_result.get("remaining", 0)
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(
            limits.get("requests_per_hour", 0)
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            hour_result.get("remaining", 0)
        )
        response.headers["X-RateLimit-Limit-Day"] = str(
            limits.get("requests_per_day", 0)
        )
        response.headers["X-RateLimit-Remaining-Day"] = str(
            day_result.get("remaining", 0)
        )

        return response


__all__ = [
    "RateLimitMiddleware",
    "get_redis_pool",
    "get_redis_client",
    "close_redis_pool",
    "check_rate_limit",
    "hash_api_key",
]
