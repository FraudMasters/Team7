"""
Redis caching service with connection pooling and serialization.

This module provides a high-performance caching layer using Redis with connection
pooling and automatic serialization/deserialization of complex Python objects.

The cache service supports:
- Connection pooling for efficient Redis connections
- JSON serialization for complex objects
- TTL (Time To Live) management
- Pattern-based cache invalidation
- Health checks and connection monitoring
- Graceful fallback when Redis is unavailable

Cache key format: {prefix}:{namespace}:{key}
Example: agenthr:candidate:12345
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union
from functools import wraps

import redis
from redis import Redis
from redis.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from config import get_settings

logger = logging.getLogger(__name__)

# Global connection pool instance
_connection_pool: Optional[ConnectionPool] = None

# Global cache service instance
_cache_service: Optional["CacheService"] = None


class CacheService:
    """
    Redis caching service with connection pooling and serialization.

    This class provides a high-level interface for caching operations with
    automatic connection pooling, serialization, and error handling.

    Attributes:
        redis_client: Redis client with connection pooling
        enabled: Whether caching is enabled
        key_prefix: Prefix for all cache keys
        default_ttl: Default time-to-live for cache entries

    Example:
        >>> cache = CacheService()
        >>> await cache.set("user:123", {"name": "John"}, ttl=3600)
        >>> user = await cache.get("user:123")
        >>> print(user)  # {"name": "John"}
    """

    # Cache namespaces for organizing keys
    NAMESPACE_CANDIDATE = "candidate"
    NAMESPACE_VACANCY = "vacancy"
    NAMESPACE_MATCH = "match"
    NAMESPACE_ANALYTICS = "analytics"
    NAMESPACE_TAXONOMY = "taxonomy"
    NAMESPACE_SESSION = "session"

    def __init__(
        self,
        redis_url: Optional[str] = None,
        enabled: Optional[bool] = None,
        key_prefix: Optional[str] = None,
        default_ttl: Optional[int] = None,
        max_connections: Optional[int] = None,
    ) -> None:
        """
        Initialize the cache service with connection pooling.

        Args:
            redis_url: Redis connection URL (defaults to settings)
            enabled: Whether caching is enabled (defaults to settings)
            key_prefix: Prefix for cache keys (defaults to settings)
            default_ttl: Default TTL in seconds (defaults to settings)
            max_connections: Max connections in pool (defaults to settings)
        """
        settings = get_settings()

        self.redis_url = redis_url or settings.redis_url
        self.enabled = enabled if enabled is not None else settings.redis_cache_enabled
        self.key_prefix = key_prefix or settings.redis_cache_key_prefix
        self.default_ttl = default_ttl or settings.redis_cache_default_ttl
        self.max_connections = max_connections or settings.redis_cache_max_connections

        self.redis_client: Optional[Redis] = None
        self._initialize_connection()

        logger.info(
            f"CacheService initialized (enabled={self.enabled}, "
            f"prefix={self.key_prefix}, ttl={self.default_ttl}s)"
        )

    def _initialize_connection(self) -> None:
        """
        Initialize Redis connection pool and client.

        Creates a connection pool for efficient connection reuse and
        initializes the Redis client. Handles connection errors gracefully.
        """
        if not self.enabled:
            logger.info("Caching is disabled, skipping Redis connection")
            return

        try:
            # Create connection pool
            global _connection_pool
            if _connection_pool is None:
                _connection_pool = ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=self.max_connections,
                    decode_responses=False,  # We'll handle encoding ourselves
                )
                logger.debug(f"Created Redis connection pool (max={self.max_connections})")

            # Create Redis client from pool
            self.redis_client = Redis(connection_pool=_connection_pool)

            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Caching will be disabled for this session")
            self.enabled = False
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing Redis: {e}", exc_info=True)
            self.enabled = False
            self.redis_client = None

    def _build_key(self, namespace: str, key: str) -> str:
        """
        Build a complete cache key with prefix and namespace.

        Args:
            namespace: Cache namespace (e.g., 'candidate', 'vacancy')
            key: Cache key identifier

        Returns:
            Complete cache key string

        Example:
            >>> cache = CacheService()
            >>> cache._build_key('candidate', '12345')
            'agenthr:candidate:12345'
        """
        return f"{self.key_prefix}:{namespace}:{key}"

    def _serialize(self, value: Any) -> bytes:
        """
        Serialize Python object to JSON bytes.

        Args:
            value: Python object to serialize

        Returns:
            JSON-encoded bytes

        Raises:
            TypeError: If object is not JSON-serializable
        """
        try:
            return json.dumps(value).encode("utf-8")
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize cache value: {e}")
            raise TypeError(f"Value is not JSON-serializable: {e}")

    def _deserialize(self, data: bytes) -> Any:
        """
        Deserialize JSON bytes to Python object.

        Args:
            data: JSON-encoded bytes

        Returns:
            Deserialized Python object

        Raises:
            ValueError: If data is not valid JSON
        """
        try:
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to deserialize cache data: {e}")
            raise ValueError(f"Data is not valid JSON: {e}")

    def get(
        self, namespace: str, key: str, default: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Retrieve a value from cache.

        Args:
            namespace: Cache namespace (e.g., 'candidate', 'vacancy')
            key: Cache key identifier
            default: Default value if key not found

        Returns:
            Cached value or default if not found

        Example:
            >>> cache = CacheService()
            >>> data = cache.get('candidate', '12345')
            >>> if data:
            ...     print(f"Found: {data}")
        """
        if not self.enabled or self.redis_client is None:
            return default

        cache_key = self._build_key(namespace, key)

        try:
            data = self.redis_client.get(cache_key)
            if data is None:
                logger.debug(f"Cache miss: {cache_key}")
                return default

            value = self._deserialize(data)
            logger.debug(f"Cache hit: {cache_key}")
            return value

        except RedisError as e:
            logger.error(f"Error getting cache key {cache_key}: {e}")
            return default
        except Exception as e:
            logger.error(f"Unexpected error getting cache key {cache_key}: {e}", exc_info=True)
            return default

    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store a value in cache with optional TTL.

        Args:
            namespace: Cache namespace (e.g., 'candidate', 'vacancy')
            key: Cache key identifier
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (defaults to instance default_ttl)

        Returns:
            True if successful, False otherwise

        Example:
            >>> cache = CacheService()
            >>> success = cache.set('candidate', '12345', {'name': 'John'}, ttl=3600)
        """
        if not self.enabled or self.redis_client is None:
            logger.debug(f"Caching disabled, skipping set: {namespace}:{key}")
            return False

        cache_key = self._build_key(namespace, key)
        ttl = ttl if ttl is not None else self.default_ttl

        try:
            serialized = self._serialize(value)
            self.redis_client.setex(cache_key, ttl, serialized)
            logger.debug(f"Cached: {cache_key} (ttl={ttl}s)")
            return True

        except (TypeError, ValueError) as e:
            logger.error(f"Error serializing value for {cache_key}: {e}")
            return False
        except RedisError as e:
            logger.error(f"Error setting cache key {cache_key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting cache key {cache_key}: {e}", exc_info=True)
            return False

    def delete(self, namespace: str, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            namespace: Cache namespace
            key: Cache key identifier

        Returns:
            True if key was deleted, False otherwise

        Example:
            >>> cache = CacheService()
            >>> cache.delete('candidate', '12345')
        """
        if not self.enabled or self.redis_client is None:
            return False

        cache_key = self._build_key(namespace, key)

        try:
            result = self.redis_client.delete(cache_key)
            if result > 0:
                logger.debug(f"Deleted: {cache_key}")
                return True
            else:
                logger.debug(f"Key not found for deletion: {cache_key}")
                return False

        except RedisError as e:
            logger.error(f"Error deleting cache key {cache_key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting cache key {cache_key}: {e}", exc_info=True)
            return False

    def delete_pattern(self, namespace: str, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Useful for invalidating groups of related cache entries.

        Args:
            namespace: Cache namespace
            pattern: Key pattern (supports wildcards, e.g., 'vacancy:*')

        Returns:
            Number of keys deleted

        Example:
            >>> cache = CacheService()
            >>> # Invalidate all caches for vacancy 123
            >>> count = cache.delete_pattern('match', 'vacancy:123:*')
        """
        if not self.enabled or self.redis_client is None:
            return 0

        search_pattern = self._build_key(namespace, pattern)

        try:
            # Find all matching keys
            keys = []
            for key in self.redis_client.scan_iter(match=search_pattern):
                keys.append(key)

            # Delete them in bulk
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Deleted {deleted} keys matching pattern: {search_pattern}")
                return deleted

            return 0

        except RedisError as e:
            logger.error(f"Error deleting pattern {search_pattern}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error deleting pattern {search_pattern}: {e}", exc_info=True)
            return 0

    def exists(self, namespace: str, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            namespace: Cache namespace
            key: Cache key identifier

        Returns:
            True if key exists, False otherwise

        Example:
            >>> cache = CacheService()
            >>> if cache.exists('candidate', '12345'):
            ...     print("Candidate is cached")
        """
        if not self.enabled or self.redis_client is None:
            return False

        cache_key = self._build_key(namespace, key)

        try:
            return bool(self.redis_client.exists(cache_key))
        except RedisError as e:
            logger.error(f"Error checking existence of {cache_key}: {e}")
            return False

    def get_many(self, namespace: str, keys: List[str]) -> Dict[str, Any]:
        """
        Retrieve multiple values from cache.

        Args:
            namespace: Cache namespace
            keys: List of cache key identifiers

        Returns:
            Dictionary mapping keys to their cached values

        Example:
            >>> cache = CacheService()
            >>> data = cache.get_many('candidate', ['123', '456', '789'])
            >>> print(data['123'])  # Cached data for candidate 123
        """
        result = {}

        if not self.enabled or self.redis_client is None or not keys:
            return result

        try:
            # Build full cache keys
            cache_keys = [self._build_key(namespace, key) for key in keys]

            # Get values in pipeline
            with self.redis_client.pipeline() as pipe:
                for cache_key in cache_keys:
                    pipe.get(cache_key)
                values = pipe.execute()

            # Deserialize and map back to original keys
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = self._deserialize(value)
                    except (ValueError, json.JSONDecodeError):
                        logger.warning(f"Failed to deserialize cached value for key: {key}")

            logger.debug(f"Retrieved {len(result)}/{len(keys)} keys from cache")

        except RedisError as e:
            logger.error(f"Error getting multiple keys from namespace {namespace}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting multiple keys: {e}", exc_info=True)

        return result

    def set_many(
        self, namespace: str, mapping: Dict[str, Any], ttl: Optional[int] = None
    ) -> int:
        """
        Store multiple values in cache.

        Args:
            namespace: Cache namespace
            mapping: Dictionary mapping keys to values
            ttl: Time-to-live in seconds (defaults to instance default_ttl)

        Returns:
            Number of keys successfully cached

        Example:
            >>> cache = CacheService()
            >>> cache.set_many('candidate', {'123': data1, '456': data2}, ttl=3600)
        """
        if not self.enabled or self.redis_client is None or not mapping:
            return 0

        ttl = ttl if ttl is not None else self.default_ttl
        success_count = 0

        try:
            with self.redis_client.pipeline() as pipe:
                for key, value in mapping.items():
                    cache_key = self._build_key(namespace, key)
                    try:
                        serialized = self._serialize(value)
                        pipe.setex(cache_key, ttl, serialized)
                        success_count += 1
                    except (TypeError, ValueError):
                        logger.warning(f"Skipping non-serializable value for key: {key}")

                pipe.execute()

            logger.debug(f"Cached {success_count}/{len(mapping)} keys in namespace {namespace}")

        except RedisError as e:
            logger.error(f"Error setting multiple keys in namespace {namespace}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error setting multiple keys: {e}", exc_info=True)

        return success_count

    def clear_namespace(self, namespace: str) -> int:
        """
        Clear all keys in a namespace.

        Useful for invalidating entire categories of cached data.

        Args:
            namespace: Cache namespace to clear

        Returns:
            Number of keys deleted

        Example:
            >>> cache = CacheService()
            >>> # Invalidate all analytics caches
            >>> count = cache.clear_namespace('analytics')
        """
        return self.delete_pattern(namespace, "*")

    def health_check(self) -> Dict[str, Any]:
        """
        Check Redis connection health and get cache statistics.

        Returns:
            Dictionary with health status and statistics

        Example:
            >>> cache = CacheService()
            >>> health = cache.health_check()
            >>> print(health)
            {'status': 'healthy', 'connected': True, ...}
        """
        result = {
            "status": "unhealthy",
            "connected": False,
            "enabled": self.enabled,
            "key_count": 0,
            "memory_used": 0,
            "error": None,
        }

        if not self.enabled or self.redis_client is None:
            result["error"] = "Caching is disabled"
            return result

        try:
            # Test connection
            self.redis_client.ping()
            result["connected"] = True

            # Get info
            info = self.redis_client.info("memory")
            result["memory_used"] = info.get("used_memory", 0)

            # Count keys with our prefix
            key_count = 0
            for key in self.redis_client.scan_iter(match=f"{self.key_prefix}:*"):
                key_count += 1
            result["key_count"] = key_count

            result["status"] = "healthy"
            logger.debug(f"Health check: {result}")

        except RedisError as e:
            result["error"] = str(e)
            logger.error(f"Redis health check failed: {e}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Unexpected error during health check: {e}", exc_info=True)

        return result

    def close(self) -> None:
        """
        Close the Redis connection.

        Call this when shutting down the application to cleanly close connections.

        Example:
            >>> cache = CacheService()
            >>> # ... use cache ...
            >>> cache.close()
        """
        if self.redis_client is not None:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self.redis_client = None


def get_cache_service() -> CacheService:
    """
    Get or create global cache service instance.

    Returns:
        Global CacheService instance

    Example:
        >>> cache = get_cache_service()
        >>> cache.set('test', 'key', 'value')
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def invalidate_candidate_cache(candidate_id: str) -> int:
    """
    Invalidate all cache entries related to a specific candidate.

    This removes:
    - Candidate profile cache
    - All candidate list caches that may include this candidate

    Args:
        candidate_id: Candidate/resume UUID

    Returns:
        Number of cache keys invalidated

    Example:
        >>> invalidate_candidate_cache("abc-123-def")
        5
    """
    cache = get_cache_service()
    invalidated = 0

    # Invalidate candidate profile
    if cache.delete(CacheService.NAMESPACE_CANDIDATE, f"profile:{candidate_id}"):
        invalidated += 1

    # Invalidate all candidate list caches (they contain aggregated data)
    # This is a blunt approach but ensures consistency
    invalidated += cache.delete_pattern(CacheService.NAMESPACE_CANDIDATE, "list:*")

    return invalidated


def invalidate_vacancy_cache(vacancy_id: str) -> int:
    """
    Invalidate all cache entries related to a specific vacancy.

    This removes:
    - Candidate lists filtered by this vacancy
    - Match results for this vacancy
    - Ranked candidates for this vacancy

    Args:
        vacancy_id: Vacancy UUID

    Returns:
        Number of cache keys invalidated

    Example:
        >>> invalidate_vacancy_cache("vac-456-ghi")
        3
    """
    cache = get_cache_service()
    invalidated = 0

    # Invalidate candidate lists with this vacancy filter
    invalidated += cache.delete_pattern(CacheService.NAMESPACE_CANDIDATE, "*list:*vacancy:{vacancy_id}*")

    # Invalidate match results for this vacancy
    invalidated += cache.delete_pattern(CacheService.NAMESPACE_MATCH, f"match:*:{vacancy_id}*")

    return invalidated


def invalidate_match_cache(resume_id: str, vacancy_id: Optional[str] = None) -> int:
    """
    Invalidate match result caches for a resume.

    Args:
        resume_id: Resume UUID
        vacancy_id: Optional vacancy UUID to limit invalidation scope

    Returns:
        Number of cache keys invalidated

    Example:
        >>> invalidate_match_cache("abc-123")
        2
        >>> invalidate_match_cache("abc-123", "vac-456")
        1
    """
    cache = get_cache_service()
    invalidated = 0

    if vacancy_id:
        # Invalidate specific match cache
        invalidated += cache.delete_pattern(CacheService.NAMESPACE_MATCH, f"match:{resume_id}:*")
    else:
        # Invalidate all matches for this resume
        invalidated += cache.delete_pattern(CacheService.NAMESPACE_MATCH, f"match:{resume_id}:*")

    return invalidated


def cached(
    namespace: str,
    key_func: Optional[callable] = None,
    ttl: Optional[int] = None,
):
    """
    Decorator for caching function results.

    Args:
        namespace: Cache namespace for the decorated function
        key_func: Function to generate cache key from args (defaults to function name + args)
        ttl: Time-to-live in seconds (defaults to instance default_ttl)

    Example:
        >>> @cached('candidate', ttl=3600)
        >>> def get_candidate_profile(candidate_id: str):
        ...     # Expensive database query
        ...     return db.query(Candidate).filter_by(id=candidate_id).first()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_service()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name and first argument (usually an ID)
                cache_key = f"{func.__name__}:{args[0] if args else 'none'}"

            # Try to get from cache
            cached_value = cache.get(namespace, cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                cache.set(namespace, cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator
