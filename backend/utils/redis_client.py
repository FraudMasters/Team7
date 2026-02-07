"""
Redis client utility for caching and session management.

This module provides a Redis client wrapper for common operations like
storing OAuth state parameters, caching data, and session management.

Features:
- Async Redis client with connection pooling
- OAuth state parameter storage with TTL
- JSON serialization for complex data types
- Error handling and logging
"""
import json
import logging
from typing import Optional, Any
from datetime import timedelta

import redis.asyncio as aioredis
from config import get_settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """
    Get or create the global Redis client instance.

    This function lazily initializes the Redis connection pool on first call
    and reuses the connection for subsequent calls.

    Returns:
        Redis client instance

    Raises:
        RuntimeError: If Redis connection fails

    Example:
        >>> client = await get_redis_client()
        >>> await client.set("key", "value")
        >>> value = await client.get("key")
    """
    global _redis_client

    if _redis_client is None:
        settings = get_settings()

        try:
            # Create async Redis client with connection pooling
            _redis_client = await aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPCNT
                    3: 10,  # TCP_KEEPINTVL
                },
            )

            # Test connection
            await _redis_client.ping()
            logger.info(f"Redis client initialized: {settings.redis_url}")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise RuntimeError(
                f"Redis connection failed: {e}. "
                "Please ensure Redis is running and REDIS_URL is configured."
            ) from e

    return _redis_client


async def close_redis_client() -> None:
    """
    Close the Redis client connection.

    This function should be called on application shutdown to gracefully
    close the Redis connection pool.

    Example:
        >>> # On application shutdown
        >>> await close_redis_client()
    """
    global _redis_client

    if _redis_client is not None:
        try:
            await _redis_client.close()
            logger.info("Redis client closed")
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}")
        finally:
            _redis_client = None


async def store_oauth_state(
    state: str,
    ttl_seconds: int = 600,
) -> bool:
    """
    Store OAuth state parameter in Redis with TTL.

    This function stores the OAuth state parameter to prevent CSRF attacks.
    The state is stored with a limited TTL (default 10 minutes) to ensure
    it can only be used within a short time window.

    Args:
        state: OAuth state parameter to store
        ttl_seconds: Time-to-live in seconds (default: 600 = 10 minutes)

    Returns:
        True if stored successfully, False otherwise

    Example:
        >>> from utils.linkedin_oauth import generate_state
        >>> state = generate_state()
        >>> success = await store_oauth_state(state)
        >>> print(success)
        True
    """
    try:
        client = await get_redis_client()
        key = f"oauth_state:{state}"

        await client.setex(key, ttl_seconds, "1")
        logger.debug(f"Stored OAuth state: {state[:10]}... (TTL: {ttl_seconds}s)")

        return True

    except Exception as e:
        logger.error(f"Failed to store OAuth state: {e}")
        return False


async def verify_oauth_state(state: str) -> bool:
    """
    Verify OAuth state parameter exists in Redis.

    This function checks if the state parameter was previously stored
    and hasn't expired. It also deletes the state after verification
    to prevent replay attacks.

    Args:
        state: OAuth state parameter to verify

    Returns:
        True if state is valid, False otherwise

    Example:
        >>> state = "random-state-123"
        >>> is_valid = await verify_oauth_state(state)
        >>> if is_valid:
        ...     print("State verified, proceed with OAuth flow")
    """
    try:
        client = await get_redis_client()
        key = f"oauth_state:{state}"

        # Check if state exists
        exists = await client.exists(key)

        if exists:
            # Delete state to prevent replay attacks
            await client.delete(key)
            logger.debug(f"OAuth state verified and deleted: {state[:10]}...")
            return True
        else:
            logger.warning(f"OAuth state not found or expired: {state[:10]}...")
            return False

    except Exception as e:
        logger.error(f"Failed to verify OAuth state: {e}")
        return False


async def cache_get(
    key: str,
    default: Optional[Any] = None,
) -> Optional[Any]:
    """
    Get a value from Redis cache.

    Args:
        key: Cache key
        default: Default value if key doesn't exist

    Returns:
        Cached value or default

    Example:
        >>> value = await cache_get("user:123:profile")
        >>> if value:
        ...     print("Cache hit")
    """
    try:
        client = await get_redis_client()
        value = await client.get(key)

        if value is None:
            return default

        # Try to parse as JSON
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    except Exception as e:
        logger.error(f"Failed to get cache value: {e}")
        return default


async def cache_set(
    key: str,
    value: Any,
    ttl_seconds: Optional[int] = None,
) -> bool:
    """
    Set a value in Redis cache.

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized if not a string)
        ttl_seconds: Optional TTL in seconds

    Returns:
        True if set successfully, False otherwise

    Example:
        >>> data = {"name": "John", "age": 30}
        >>> await cache_set("user:123:profile", data, ttl_seconds=3600)
    """
    try:
        client = await get_redis_client()

        # Serialize complex types to JSON
        if not isinstance(value, (str, int, float, bool)):
            value = json.dumps(value)

        if ttl_seconds:
            await client.setex(key, ttl_seconds, value)
        else:
            await client.set(key, value)

        return True

    except Exception as e:
        logger.error(f"Failed to set cache value: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """
    Delete a key from Redis cache.

    Args:
        key: Cache key to delete

    Returns:
        True if deleted, False otherwise

    Example:
        >>> await cache_delete("user:123:profile")
    """
    try:
        client = await get_redis_client()
        await client.delete(key)
        return True

    except Exception as e:
        logger.error(f"Failed to delete cache key: {e}")
        return False


async def cache_exists(key: str) -> bool:
    """
    Check if a key exists in Redis cache.

    Args:
        key: Cache key to check

    Returns:
        True if key exists, False otherwise

    Example:
        >>> exists = await cache_exists("user:123:profile")
    """
    try:
        client = await get_redis_client()
        return await client.exists(key) > 0

    except Exception as e:
        logger.error(f"Failed to check cache key: {e}")
        return False
