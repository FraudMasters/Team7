"""
Redis-backed rate limiting service using token bucket algorithm.

This module provides distributed rate limiting using Redis for accurate
rate limit tracking across multiple server instances. The token bucket
algorithm allows for bursts while maintaining a steady rate limit.

The rate limit service supports:
- Token bucket algorithm for smooth rate limiting
- Connection pooling for efficient Redis connections
- Distributed accuracy across multiple instances
- Different limit tiers based on user roles
- IP-based blocking for DDoS protection
- Health checks and connection monitoring
- Prometheus metrics for monitoring rate limiting
- Graceful fallback when Redis is unavailable

Token bucket algorithm:
- Each bucket has a maximum capacity (max_tokens)
- Tokens refill at a steady rate (tokens per second)
- Requests consume tokens from the bucket
- If insufficient tokens, request is rate limited
- Allows bursts up to bucket capacity

Rate limit key format: {prefix}:{namespace}:{identifier}
Example: agenthr:rl:user:12345
"""
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple

import redis
from redis import Redis
from redis.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from config import get_settings
from backend.utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)

# Global connection pool instance (shared with cache service)
_connection_pool: Optional[ConnectionPool] = None

# Global rate limit service instance
_rate_limit_service: Optional["RateLimitService"] = None


class RateLimitTier(Enum):
    """
    Rate limit tiers for different user roles.

    Attributes:
        ANONYMOUS: Unauthenticated users (lowest limit)
        USER: Regular authenticated users
        ORG_ADMIN: Organization administrators
        ADMIN: System administrators (highest limit)
    """
    ANONYMOUS = "anonymous"
    USER = "user"
    ORG_ADMIN = "org_admin"
    ADMIN = "admin"


@dataclass
class RateLimitResult:
    """
    Result of a rate limit check.

    Attributes:
        allowed: Whether the request is allowed
        remaining: Number of requests remaining in the current window
        reset_at: Unix timestamp when the rate limit resets
        retry_after: Seconds to wait before retrying (if not allowed)
        limit: Maximum requests allowed in the window
        tier: Rate limit tier that was applied
    """
    allowed: bool
    remaining: int
    reset_at: int
    retry_after: Optional[int]
    limit: int
    tier: RateLimitTier


@dataclass
class TokenBucket:
    """
    Token bucket state for rate limiting.

    Attributes:
        current_tokens: Current number of tokens in the bucket
        last_refill: Unix timestamp of last token refill
        max_tokens: Maximum capacity of the bucket
        refill_rate: Tokens added per second
    """
    current_tokens: float
    last_refill: float
    max_tokens: float
    refill_rate: float


class RateLimitService:
    """
    Redis-backed rate limiting service using token bucket algorithm.

    This class provides distributed rate limiting with automatic token refill,
    connection pooling, and graceful fallback when Redis is unavailable.

    The token bucket algorithm allows for bursts of traffic while maintaining
    a steady average rate limit. Tokens are refilled continuously at a fixed rate.

    Attributes:
        redis_client: Redis client with connection pooling
        enabled: Whether rate limiting is enabled
        key_prefix: Prefix for all rate limit keys

    Example:
        >>> service = RateLimitService()
        >>> result = service.check_rate_limit("user", "123", tier=RateLimitTier.USER)
        >>> if result.allowed:
        ...     process_request()
        >>> else:
        ...     return Response(status_code=429, headers={"Retry-After": str(result.retry_after)})
    """

    # Rate limit namespaces
    NAMESPACE_USER = "user"
    NAMESPACE_IP = "ip"
    NAMESPACE_ORG = "org"
    NAMESPACE_GLOBAL = "global"

    # Default rate limits (requests per minute)
    DEFAULT_LIMITS = {
        RateLimitTier.ANONYMOUS: (20, 60),  # 20 requests/minute
        RateLimitTier.USER: (100, 60),      # 100 requests/minute
        RateLimitTier.ORG_ADMIN: (300, 60), # 300 requests/minute
        RateLimitTier.ADMIN: (1000, 60),    # 1000 requests/minute
    }

    # IP-based blocking defaults
    IP_BLOCK_THRESHOLD = 100  # requests per minute before IP evaluation
    IP_BLOCK_DURATION = 3600  # seconds (1 hour)

    def __init__(
        self,
        redis_url: Optional[str] = None,
        enabled: Optional[bool] = None,
        key_prefix: Optional[str] = None,
        max_connections: Optional[int] = None,
    ) -> None:
        """
        Initialize the rate limit service with connection pooling.

        Args:
            redis_url: Redis connection URL (defaults to settings)
            enabled: Whether rate limiting is enabled (defaults to True)
            key_prefix: Prefix for rate limit keys (defaults to settings)
            max_connections: Max connections in pool (defaults to settings)
        """
        settings = get_settings()

        self.redis_url = redis_url or settings.redis_url
        # Default to enabled if not specified
        self.enabled = enabled if enabled is not None else True
        # Use a separate prefix for rate limits to avoid conflicts
        self.key_prefix = key_prefix or f"{settings.redis_url.split('/')[-1]}:rl" if hasattr(settings, 'redis_cache_key_prefix') else "agenthr:rl"
        self.max_connections = max_connections or 50

        self.redis_client: Optional[Redis] = None
        self._initialize_connection()

        # Initialize metrics registry
        self.metrics = get_metrics_registry()

        logger.info(
            f"RateLimitService initialized (enabled={self.enabled}, "
            f"prefix={self.key_prefix})"
        )

        # Record initialization metric
        try:
            self.metrics.rate_limit_requests_total.labels(
                limit_type="init",
                endpoint="service_init",
                client_identifier="system"
            ).inc(0)  # Initialize metric with 0
        except Exception as e:
            logger.debug(f"Failed to initialize rate limit metric: {e}")

    def _initialize_connection(self) -> None:
        """
        Initialize Redis connection pool and client.

        Creates a connection pool for efficient connection reuse and
        initializes the Redis client. Handles connection errors gracefully.
        """
        if not self.enabled:
            logger.info("Rate limiting is disabled, skipping Redis connection")
            return

        try:
            # Create or reuse connection pool
            global _connection_pool
            if _connection_pool is None:
                _connection_pool = ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=self.max_connections,
                    decode_responses=False,  # We'll handle encoding ourselves
                )
                logger.debug(f"Created Redis connection pool for rate limiting (max={self.max_connections})")

            # Create Redis client from pool
            self.redis_client = Redis(connection_pool=_connection_pool)

            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established for rate limiting")

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis for rate limiting: {e}")
            logger.warning("Rate limiting will be disabled for this session")
            self.enabled = False
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing Redis for rate limiting: {e}", exc_info=True)
            self.enabled = False
            self.redis_client = None

    def _build_key(self, namespace: str, identifier: str) -> str:
        """
        Build a complete rate limit key with prefix and namespace.

        Args:
            namespace: Rate limit namespace (e.g., 'user', 'ip')
            identifier: Unique identifier (e.g., user ID, IP address)

        Returns:
            Complete rate limit key string

        Example:
            >>> service = RateLimitService()
            >>> service._build_key('user', '12345')
            'agenthr:rl:user:12345'
        """
        return f"{self.key_prefix}:{namespace}:{identifier}"

    def _serialize_bucket(self, bucket: TokenBucket) -> bytes:
        """
        Serialize token bucket to JSON bytes.

        Args:
            bucket: Token bucket to serialize

        Returns:
            JSON-encoded bytes
        """
        return json.dumps({
            "current_tokens": bucket.current_tokens,
            "last_refill": bucket.last_refill,
            "max_tokens": bucket.max_tokens,
            "refill_rate": bucket.refill_rate,
        }).encode("utf-8")

    def _deserialize_bucket(self, data: bytes) -> TokenBucket:
        """
        Deserialize JSON bytes to token bucket.

        Args:
            data: JSON-encoded bytes

        Returns:
            TokenBucket object

        Raises:
            ValueError: If data is not valid JSON
        """
        try:
            obj = json.loads(data.decode("utf-8"))
            return TokenBucket(
                current_tokens=obj["current_tokens"],
                last_refill=obj["last_refill"],
                max_tokens=obj["max_tokens"],
                refill_rate=obj["refill_rate"],
            )
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
            logger.error(f"Failed to deserialize token bucket: {e}")
            raise ValueError(f"Data is not valid token bucket: {e}")

    def _get_limit_for_tier(self, tier: RateLimitTier) -> Tuple[int, int]:
        """
        Get rate limit (requests, window_seconds) for a tier.

        Args:
            tier: Rate limit tier

        Returns:
            Tuple of (max_requests, window_seconds)

        Example:
            >>> service = RateLimitService()
            >>> service._get_limit_for_tier(RateLimitTier.USER)
            (100, 60)
        """
        return self.DEFAULT_LIMITS.get(tier, self.DEFAULT_LIMITS[RateLimitTier.USER])

    def _refill_bucket(self, bucket: TokenBucket, current_time: float) -> TokenBucket:
        """
        Refill tokens in the bucket based on elapsed time.

        Args:
            bucket: Current token bucket state
            current_time: Current Unix timestamp

        Returns:
            Updated token bucket with refilled tokens
        """
        elapsed = current_time - bucket.last_refill
        if elapsed > 0:
            # Add tokens based on elapsed time and refill rate
            new_tokens = elapsed * bucket.refill_rate
            bucket.current_tokens = min(bucket.max_tokens, bucket.current_tokens + new_tokens)
            bucket.last_refill = current_time

        return bucket

    def check_rate_limit(
        self,
        namespace: str,
        identifier: str,
        tier: RateLimitTier = RateLimitTier.USER,
        cost: int = 1,
    ) -> RateLimitResult:
        """
        Check if a request is allowed under rate limits.

        Uses the token bucket algorithm to determine if the request should be
        allowed. Consumes tokens if allowed, and returns rate limit information.

        Args:
            namespace: Rate limit namespace (e.g., 'user', 'ip')
            identifier: Unique identifier (e.g., user ID, IP address)
            tier: Rate limit tier to apply
            cost: Number of tokens to consume (default: 1)

        Returns:
            RateLimitResult with allowance status and rate limit info

        Example:
            >>> service = RateLimitService()
            >>> result = service.check_rate_limit("user", "123", RateLimitTier.USER)
            >>> if result.allowed:
            ...     process_request()
        """
        if not self.enabled or self.redis_client is None:
            # Rate limiting disabled, allow all requests
            # Record metric for monitoring disabled state
            try:
                self.metrics.rate_limit_hits_total.labels(
                    limit_type=namespace,
                    endpoint="rate_limit_disabled",
                    client_identifier=identifier,
                ).inc()
            except Exception as e:
                logger.debug(f"Failed to record disabled metric: {e}")

            return RateLimitResult(
                allowed=True,
                remaining=-1,  # Unlimited
                reset_at=0,
                retry_after=None,
                limit=-1,  # Unlimited
                tier=tier,
            )

        key = self._build_key(namespace, identifier)
        max_requests, window_seconds = self._get_limit_for_tier(tier)

        # Calculate token bucket parameters
        max_tokens = float(max_requests)
        refill_rate = max_tokens / window_seconds  # tokens per second
        current_time = time.time()

        try:
            # Try to get existing bucket
            data = self.redis_client.get(key)

            if data is None:
                # First request, create new bucket
                bucket = TokenBucket(
                    current_tokens=max_tokens - cost,
                    last_refill=current_time,
                    max_tokens=max_tokens,
                    refill_rate=refill_rate,
                )

                # Set with expiration (window + 1 minute buffer)
                ttl = window_seconds + 60
                self.redis_client.setex(key, ttl, self._serialize_bucket(bucket))

                result = RateLimitResult(
                    allowed=True,
                    remaining=int(bucket.current_tokens),
                    reset_at=int(current_time + window_seconds),
                    retry_after=None,
                    limit=max_requests,
                    tier=tier,
                )

                return result

            # Deserialize and refill bucket
            bucket = self._deserialize_bucket(data)
            bucket = self._refill_bucket(bucket, current_time)

            # Check if enough tokens
            if bucket.current_tokens >= cost:
                # Allow request, consume tokens
                bucket.current_tokens -= cost

                # Update in Redis
                remaining_ttl = self.redis_client.ttl(key)
                if remaining_ttl > 0:
                    self.redis_client.setex(key, remaining_ttl, self._serialize_bucket(bucket))

                result = RateLimitResult(
                    allowed=True,
                    remaining=int(bucket.current_tokens),
                    reset_at=int(current_time + window_seconds),
                    retry_after=None,
                    limit=max_requests,
                    tier=tier,
                )

                # Record metric if near rate limit (less than 20% remaining)
                threshold = max_tokens * 0.2
                if bucket.current_tokens < threshold:
                    try:
                        self.metrics.record_rate_limit(
                            limit_type=namespace,
                            endpoint="rate_limit_check",
                            client_identifier=identifier,
                            blocked=False,
                        )
                    except Exception as e:
                        logger.debug(f"Failed to record rate limit metric: {e}")

                return result
            else:
                # Rate limited - calculate retry time
                tokens_needed = cost - bucket.current_tokens
                retry_after = int(tokens_needed / bucket.refill_rate) + 1

                result = RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=int(current_time + retry_after),
                    retry_after=retry_after,
                    limit=max_requests,
                    tier=tier,
                )

                # Record blocked request metric
                try:
                    self.metrics.record_rate_limit(
                        limit_type=namespace,
                        endpoint="rate_limit_check",
                        client_identifier=identifier,
                        blocked=True,
                        retry_after=retry_after,
                    )
                except Exception as e:
                    logger.debug(f"Failed to record rate limit metric: {e}")

                return result

        except RedisError as e:
            logger.error(f"Redis error checking rate limit for {key}: {e}")

            # Record metric for Redis error (fail-open)
            try:
                self.metrics.rate_limit_hits_total.labels(
                    limit_type=namespace,
                    endpoint="redis_error",
                    client_identifier=identifier,
                ).inc()
            except Exception as metric_error:
                logger.debug(f"Failed to record Redis error metric: {metric_error}")

            # Fail open - allow request if Redis fails
            return RateLimitResult(
                allowed=True,
                remaining=-1,
                reset_at=0,
                retry_after=None,
                limit=-1,
                tier=tier,
            )
        except Exception as e:
            logger.error(f"Unexpected error checking rate limit for {key}: {e}", exc_info=True)

            # Record metric for unexpected error (fail-open)
            try:
                self.metrics.rate_limit_hits_total.labels(
                    limit_type=namespace,
                    endpoint="unexpected_error",
                    client_identifier=identifier,
                ).inc()
            except Exception as metric_error:
                logger.debug(f"Failed to record error metric: {metric_error}")

            # Fail open - allow request on error
            return RateLimitResult(
                allowed=True,
                remaining=-1,
                reset_at=0,
                retry_after=None,
                limit=-1,
                tier=tier,
            )

    def reset_rate_limit(self, namespace: str, identifier: str) -> bool:
        """
        Reset rate limit for a specific identifier.

        Removes the rate limit bucket, allowing the identifier to start fresh.

        Args:
            namespace: Rate limit namespace
            identifier: Unique identifier

        Returns:
            True if reset was successful, False otherwise

        Example:
            >>> service = RateLimitService()
            >>> service.reset_rate_limit("user", "123")
        """
        if not self.enabled or self.redis_client is None:
            return False

        key = self._build_key(namespace, identifier)

        try:
            result = self.redis_client.delete(key)
            if result > 0:
                logger.info(f"Reset rate limit for {key}")

                # Record reset metric
                try:
                    self.metrics.rate_limit_requests_total.labels(
                        limit_type=namespace,
                        endpoint="reset_rate_limit",
                        client_identifier=identifier,
                    ).inc()
                except Exception as e:
                    logger.debug(f"Failed to record reset metric: {e}")

                return True
            return False
        except RedisError as e:
            logger.error(f"Error resetting rate limit for {key}: {e}")
            return False

    def get_rate_limit_status(
        self,
        namespace: str,
        identifier: str,
        tier: RateLimitTier = RateLimitTier.USER,
    ) -> Optional[Dict[str, Any]]:
        """
        Get current rate limit status without consuming tokens.

        Args:
            namespace: Rate limit namespace
            identifier: Unique identifier
            tier: Rate limit tier

        Returns:
            Dictionary with current status or None if not found

        Example:
            >>> service = RateLimitService()
            >>> status = service.get_rate_limit_status("user", "123")
            >>> print(status)
            {'current_tokens': 95.0, 'max_tokens': 100.0, ...}
        """
        if not self.enabled or self.redis_client is None:
            return None

        key = self._build_key(namespace, identifier)

        try:
            data = self.redis_client.get(key)
            if data is None:
                return None

            bucket = self._deserialize_bucket(data)
            current_time = time.time()
            bucket = self._refill_bucket(bucket, current_time)

            return {
                "current_tokens": bucket.current_tokens,
                "max_tokens": bucket.max_tokens,
                "refill_rate": bucket.refill_rate,
                "last_refill": bucket.last_refill,
                "namespace": namespace,
                "identifier": identifier,
                "tier": tier.value,
            }

        except (RedisError, ValueError) as e:
            logger.error(f"Error getting rate limit status for {key}: {e}")
            return None

    def is_ip_blocked(self, ip_address: str) -> bool:
        """
        Check if an IP address is currently blocked.

        Args:
            ip_address: IP address to check

        Returns:
            True if IP is blocked, False otherwise

        Example:
            >>> service = RateLimitService()
            >>> if service.is_ip_blocked("192.168.1.1"):
            ...     block_request()
        """
        if not self.enabled or self.redis_client is None:
            return False

        key = f"{self.key_prefix}:blocked:{ip_address}"

        try:
            return bool(self.redis_client.exists(key))
        except RedisError as e:
            logger.error(f"Error checking IP block for {ip_address}: {e}")
            return False

    def block_ip(
        self,
        ip_address: str,
        duration: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Block an IP address for a specified duration.

        Args:
            ip_address: IP address to block
            duration: Block duration in seconds (defaults to IP_BLOCK_DURATION)
            reason: Optional reason for blocking

        Returns:
            True if block was successful, False otherwise

        Example:
            >>> service = RateLimitService()
            >>> service.block_ip("192.168.1.1", duration=3600, reason="DDoS pattern")
        """
        if not self.enabled or self.redis_client is None:
            return False

        key = f"{self.key_prefix}:blocked:{ip_address}"
        duration = duration or self.IP_BLOCK_DURATION

        try:
            # Store block with metadata
            block_data = json.dumps({
                "blocked_at": time.time(),
                "duration": duration,
                "reason": reason,
            })
            self.redis_client.setex(key, duration, block_data.encode("utf-8"))
            logger.warning(f"Blocked IP {ip_address} for {duration}s (reason: {reason})")

            # Record IP block metric
            try:
                self.metrics.record_rate_limit(
                    limit_type="ip_block",
                    endpoint="ip_block",
                    client_identifier=ip_address,
                    blocked=True,
                    retry_after=duration,
                )
            except Exception as e:
                logger.debug(f"Failed to record IP block metric: {e}")

            return True
        except RedisError as e:
            logger.error(f"Error blocking IP {ip_address}: {e}")
            return False

    def unblock_ip(self, ip_address: str) -> bool:
        """
        Remove a block from an IP address.

        Args:
            ip_address: IP address to unblock

        Returns:
            True if unblock was successful, False otherwise

        Example:
            >>> service = RateLimitService()
            >>> service.unblock_ip("192.168.1.1")
        """
        if not self.enabled or self.redis_client is None:
            return False

        key = f"{self.key_prefix}:blocked:{ip_address}"

        try:
            result = self.redis_client.delete(key)
            if result > 0:
                logger.info(f"Unblocked IP {ip_address}")

                # Record unblock metric
                try:
                    self.metrics.rate_limit_requests_total.labels(
                        limit_type="ip_unblock",
                        endpoint="unblock_ip",
                        client_identifier=ip_address,
                    ).inc()
                except Exception as e:
                    logger.debug(f"Failed to record unblock metric: {e}")

                return True
            return False
        except RedisError as e:
            logger.error(f"Error unblocking IP {ip_address}: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """
        Check Redis connection health and get rate limit statistics.

        Returns:
            Dictionary with health status and statistics

        Example:
            >>> service = RateLimitService()
            >>> health = service.health_check()
            >>> print(health)
            {'status': 'healthy', 'connected': True, ...}
        """
        result = {
            "status": "unhealthy",
            "connected": False,
            "enabled": self.enabled,
            "key_count": 0,
            "blocked_ip_count": 0,
            "error": None,
        }

        if not self.enabled or self.redis_client is None:
            result["error"] = "Rate limiting is disabled"
            return result

        try:
            # Test connection
            self.redis_client.ping()
            result["connected"] = True

            # Count rate limit keys
            key_count = 0
            for key in self.redis_client.scan_iter(match=f"{self.key_prefix}:*"):
                key_count += 1
            result["key_count"] = key_count

            # Count blocked IPs
            blocked_count = 0
            for key in self.redis_client.scan_iter(match=f"{self.key_prefix}:blocked:*"):
                blocked_count += 1
            result["blocked_ip_count"] = blocked_count

            result["status"] = "healthy"
            logger.debug(f"Rate limit health check: {result}")

        except RedisError as e:
            result["error"] = str(e)
            logger.error(f"Redis health check failed for rate limiting: {e}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Unexpected error during rate limit health check: {e}", exc_info=True)

        return result

    def close(self) -> None:
        """
        Close the Redis connection.

        Call this when shutting down the application to cleanly close connections.

        Example:
            >>> service = RateLimitService()
            >>> # ... use service ...
            >>> service.close()
        """
        if self.redis_client is not None:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed for rate limiting")
            except Exception as e:
                logger.error(f"Error closing Redis connection for rate limiting: {e}")
            finally:
                self.redis_client = None


def get_rate_limit_service() -> RateLimitService:
    """
    Get or create global rate limit service instance.

    Returns:
        Global RateLimitService instance

    Example:
        >>> service = get_rate_limit_service()
        >>> result = service.check_rate_limit("user", "123")
    """
    global _rate_limit_service
    if _rate_limit_service is None:
        _rate_limit_service = RateLimitService()
    return _rate_limit_service
