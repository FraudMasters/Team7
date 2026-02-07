"""
Tests for RateLimitService with token bucket algorithm.

Tests cover token bucket serialization, refill logic,
tiered rate limits, IP blocking, and error handling.
"""
import json
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from services.rate_limit_service import (
    RateLimitService,
    RateLimitTier,
    RateLimitResult,
    TokenBucket,
)


class TestTokenBucketSerialization:
    """Tests for token bucket serialization and deserialization."""

    def test_serialize_bucket(self):
        """Test serializing token bucket to JSON bytes."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=50.0,
            last_refill=1234567890.0,
            max_tokens=100.0,
            refill_rate=1.67,
        )

        result = service._serialize_bucket(bucket)

        assert isinstance(result, bytes)
        data = json.loads(result.decode("utf-8"))
        assert data["current_tokens"] == 50.0
        assert data["last_refill"] == 1234567890.0
        assert data["max_tokens"] == 100.0
        assert data["refill_rate"] == 1.67

    def test_deserialize_bucket(self):
        """Test deserializing JSON bytes to token bucket."""
        service = RateLimitService(enabled=False)
        data = json.dumps({
            "current_tokens": 75.5,
            "last_refill": 1234567890.0,
            "max_tokens": 100.0,
            "refill_rate": 2.5,
        }).encode("utf-8")

        result = service._deserialize_bucket(data)

        assert isinstance(result, TokenBucket)
        assert result.current_tokens == 75.5
        assert result.last_refill == 1234567890.0
        assert result.max_tokens == 100.0
        assert result.refill_rate == 2.5

    def test_deserialize_invalid_json(self):
        """Test deserializing invalid JSON raises ValueError."""
        service = RateLimitService(enabled=False)
        data = b"invalid json"

        with pytest.raises(ValueError):
            service._deserialize_bucket(data)

    def test_deserialize_missing_keys(self):
        """Test deserializing JSON with missing keys raises ValueError."""
        service = RateLimitService(enabled=False)
        data = json.dumps({"current_tokens": 50.0}).encode("utf-8")

        with pytest.raises(ValueError):
            service._deserialize_bucket(data)

    def test_serialize_deserialize_roundtrip(self):
        """Test that serialize/deserialize roundtrip preserves data."""
        service = RateLimitService(enabled=False)
        original = TokenBucket(
            current_tokens=33.33,
            last_refill=9876543210.0,
            max_tokens=200.0,
            refill_rate=5.0,
        )

        serialized = service._serialize_bucket(original)
        deserialized = service._deserialize_bucket(serialized)

        assert deserialized.current_tokens == original.current_tokens
        assert deserialized.last_refill == original.last_refill
        assert deserialized.max_tokens == original.max_tokens
        assert deserialized.refill_rate == original.refill_rate


class TestTokenBucketRefill:
    """Tests for token bucket refill logic."""

    def test_refill_no_elapsed_time(self):
        """Test refill when no time has elapsed."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=50.0,
            last_refill=time.time(),
            max_tokens=100.0,
            refill_rate=1.0,
        )
        current_time = bucket.last_refill

        result = service._refill_bucket(bucket, current_time)

        assert result.current_tokens == 50.0
        assert result.last_refill == current_time

    def test_refill_one_second(self):
        """Test refill after one second."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=50.0,
            last_refill=time.time(),
            max_tokens=100.0,
            refill_rate=10.0,  # 10 tokens per second
        )
        current_time = bucket.last_refill + 1.0

        result = service._refill_bucket(bucket, current_time)

        assert result.current_tokens == 60.0  # 50 + 10
        assert result.last_refill == current_time

    def test_refill_capped_at_max(self):
        """Test that refill is capped at max_tokens."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=95.0,
            last_refill=time.time(),
            max_tokens=100.0,
            refill_rate=10.0,
        )
        current_time = bucket.last_refill + 1.0

        result = service._refill_bucket(bucket, current_time)

        assert result.current_tokens == 100.0  # Capped at max
        assert result.last_refill == current_time

    def test_refill_fractional_tokens(self):
        """Test refill with fractional tokens."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=50.0,
            last_refill=time.time(),
            max_tokens=100.0,
            refill_rate=1.67,  # Non-integer rate
        )
        current_time = bucket.last_refill + 1.0

        result = service._refill_bucket(bucket, current_time)

        assert result.current_tokens == pytest.approx(51.67, rel=0.01)

    def test_refill_empty_bucket(self):
        """Test refill from empty bucket."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=0.0,
            last_refill=time.time(),
            max_tokens=100.0,
            refill_rate=50.0,
        )
        current_time = bucket.last_refill + 1.0

        result = service._refill_bucket(bucket, current_time)

        assert result.current_tokens == 50.0

    def test_refill_multiple_seconds(self):
        """Test refill after multiple seconds."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=20.0,
            last_refill=time.time(),
            max_tokens=100.0,
            refill_rate=5.0,
        )
        current_time = bucket.last_refill + 10.0

        result = service._refill_bucket(bucket, current_time)

        assert result.current_tokens == 70.0  # 20 + (5 * 10)


class TestBuildKey:
    """Tests for _build_key method."""

    def test_build_user_key(self):
        """Test building user rate limit key."""
        service = RateLimitService(enabled=False)
        result = service._build_key("user", "12345")
        assert result == f"{service.key_prefix}:user:12345"

    def test_build_ip_key(self):
        """Test building IP rate limit key."""
        service = RateLimitService(enabled=False)
        result = service._build_key("ip", "192.168.1.1")
        assert result == f"{service.key_prefix}:ip:192.168.1.1"

    def test_build_org_key(self):
        """Test building org rate limit key."""
        service = RateLimitService(enabled=False)
        result = service._build_key("org", "org_123")
        assert result == f"{service.key_prefix}:org:org_123"

    def test_key_consistency(self):
        """Test that same inputs produce same key."""
        service = RateLimitService(enabled=False)
        key1 = service._build_key("user", "123")
        key2 = service._build_key("user", "123")
        assert key1 == key2

    def test_key_uniqueness(self):
        """Test that different inputs produce different keys."""
        service = RateLimitService(enabled=False)
        key1 = service._build_key("user", "123")
        key2 = service._build_key("ip", "123")
        key3 = service._build_key("user", "456")
        assert key1 != key2 != key3


class TestGetLimitForTier:
    """Tests for _get_limit_for_tier method."""

    def test_anonymous_tier(self):
        """Test getting limit for anonymous tier."""
        service = RateLimitService(enabled=False)
        result = service._get_limit_for_tier(RateLimitTier.ANONYMOUS)
        assert result == (20, 60)  # 20 requests per minute

    def test_user_tier(self):
        """Test getting limit for user tier."""
        service = RateLimitService(enabled=False)
        result = service._get_limit_for_tier(RateLimitTier.USER)
        assert result == (100, 60)  # 100 requests per minute

    def test_org_admin_tier(self):
        """Test getting limit for org_admin tier."""
        service = RateLimitService(enabled=False)
        result = service._get_limit_for_tier(RateLimitTier.ORG_ADMIN)
        assert result == (300, 60)  # 300 requests per minute

    def test_admin_tier(self):
        """Test getting limit for admin tier."""
        service = RateLimitService(enabled=False)
        result = service._get_limit_for_tier(RateLimitTier.ADMIN)
        assert result == (1000, 60)  # 1000 requests per minute

    def test_default_tier(self):
        """Test that user tier is default for unknown tier."""
        service = RateLimitService(enabled=False)
        # Create a mock tier that's not in DEFAULT_LIMITS
        mock_tier = Mock()
        mock_tier.value = "unknown"
        result = service._get_limit_for_tier(mock_tier)
        # Should fall back to USER tier
        assert result == (100, 60)


class TestCheckRateLimit:
    """Tests for check_rate_limit method."""

    def test_first_request_allowed(self):
        """Test that first request is always allowed."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.get.return_value = None
        service.redis_client.setex.return_value = True

        result = service.check_rate_limit("user", "123", RateLimitTier.USER)

        assert result.allowed is True
        assert result.remaining == 99  # 100 - 1
        assert result.limit == 100
        assert result.tier == RateLimitTier.USER
        assert result.retry_after is None

    def test_subsequent_request_allowed(self):
        """Test that subsequent request is allowed when tokens available."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=50.0,
            last_refill=time.time(),
            max_tokens=100.0,
            refill_rate=100.0 / 60.0,
        )

        service.redis_client = MagicMock()
        service.redis_client.get.return_value = service._serialize_bucket(bucket)
        service.redis_client.ttl.return_value = 60
        service.redis_client.setex.return_value = True

        result = service.check_rate_limit("user", "123", RateLimitTier.USER)

        assert result.allowed is True
        assert result.remaining == 49  # 50 - 1
        assert result.retry_after is None

    def test_rate_limit_exceeded(self):
        """Test that request is blocked when tokens exhausted."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=0.5,  # Not enough for cost=1
            last_refill=time.time(),
            max_tokens=100.0,
            refill_rate=100.0 / 60.0,
        )

        service.redis_client = MagicMock()
        service.redis_client.get.return_value = service._serialize_bucket(bucket)

        result = service.check_rate_limit("user", "123", RateLimitTier.USER)

        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after is not None
        assert result.retry_after > 0

    def test_custom_cost(self):
        """Test rate limit check with custom cost."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=10.0,
            last_refill=time.time(),
            max_tokens=100.0,
            refill_rate=100.0 / 60.0,
        )

        service.redis_client = MagicMock()
        service.redis_client.get.return_value = service._serialize_bucket(bucket)
        service.redis_client.ttl.return_value = 60
        service.redis_client.setex.return_value = True

        result = service.check_rate_limit("user", "123", RateLimitTier.USER, cost=5)

        assert result.allowed is True
        assert result.remaining == 5  # 10 - 5

    def test_custom_cost_exceeds_tokens(self):
        """Test that custom cost exceeding tokens is blocked."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=3.0,
            last_refill=time.time(),
            max_tokens=100.0,
            refill_rate=100.0 / 60.0,
        )

        service.redis_client = MagicMock()
        service.redis_client.get.return_value = service._serialize_bucket(bucket)

        result = service.check_rate_limit("user", "123", RateLimitTier.USER, cost=5)

        assert result.allowed is False

    def test_anonymous_tier_limits(self):
        """Test rate limiting with anonymous tier."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.get.return_value = None
        service.redis_client.setex.return_value = True

        result = service.check_rate_limit("ip", "192.168.1.1", RateLimitTier.ANONYMOUS)

        assert result.allowed is True
        assert result.limit == 20  # Anonymous limit
        assert result.remaining == 19

    def test_admin_tier_limits(self):
        """Test rate limiting with admin tier."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.get.return_value = None
        service.redis_client.setex.return_value = True

        result = service.check_rate_limit("user", "admin", RateLimitTier.ADMIN)

        assert result.allowed is True
        assert result.limit == 1000  # Admin limit
        assert result.remaining == 999

    def test_disabled_rate_limiting(self):
        """Test that requests are allowed when rate limiting is disabled."""
        service = RateLimitService(enabled=False)

        result = service.check_rate_limit("user", "123", RateLimitTier.USER)

        assert result.allowed is True
        assert result.remaining == -1  # Unlimited
        assert result.limit == -1  # Unlimited
        assert result.retry_after is None

    def test_redis_error_fail_open(self):
        """Test that Redis error causes fail-open (allows request)."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.get.side_effect = RedisError("Connection failed")

        result = service.check_rate_limit("user", "123", RateLimitTier.USER)

        # Should fail open - allow the request
        assert result.allowed is True
        assert result.remaining == -1

    def test_token_refill_between_requests(self):
        """Test that tokens are refilled between requests."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=10.0,
            last_refill=time.time() - 1.0,  # 1 second ago
            max_tokens=100.0,
            refill_rate=10.0,  # 10 tokens per second
        )

        service.redis_client = MagicMock()
        service.redis_client.get.return_value = service._serialize_bucket(bucket)
        service.redis_client.ttl.return_value = 60
        service.redis_client.setex.return_value = True

        result = service.check_rate_limit("user", "123", RateLimitTier.USER)

        # Should have refilled 10 tokens: 10 + 10 - 1 = 19
        assert result.allowed is True
        assert result.remaining == 19


class TestResetRateLimit:
    """Tests for reset_rate_limit method."""

    def test_reset_existing_limit(self):
        """Test resetting an existing rate limit."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.delete.return_value = 1

        result = service.reset_rate_limit("user", "123")

        assert result is True
        service.redis_client.delete.assert_called_once()

    def test_reset_nonexistent_limit(self):
        """Test resetting a nonexistent rate limit."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.delete.return_value = 0

        result = service.reset_rate_limit("user", "123")

        assert result is False

    def test_reset_when_disabled(self):
        """Test reset when rate limiting is disabled."""
        service = RateLimitService(enabled=False)
        service.redis_client = None

        result = service.reset_rate_limit("user", "123")

        assert result is False

    def test_reset_redis_error(self):
        """Test reset handles Redis errors gracefully."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.delete.side_effect = RedisError("Connection failed")

        result = service.reset_rate_limit("user", "123")

        assert result is False


class TestGetRateLimitStatus:
    """Tests for get_rate_limit_status method."""

    def test_get_existing_status(self):
        """Test getting status for existing rate limit."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=50.0,
            last_refill=time.time(),
            max_tokens=100.0,
            refill_rate=100.0 / 60.0,
        )

        service.redis_client = MagicMock()
        service.redis_client.get.return_value = service._serialize_bucket(bucket)

        result = service.get_rate_limit_status("user", "123", RateLimitTier.USER)

        assert result is not None
        assert result["current_tokens"] == 50.0
        assert result["max_tokens"] == 100.0
        assert result["namespace"] == "user"
        assert result["identifier"] == "123"
        assert result["tier"] == "user"

    def test_get_nonexistent_status(self):
        """Test getting status for nonexistent rate limit."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.get.return_value = None

        result = service.get_rate_limit_status("user", "123", RateLimitTier.USER)

        assert result is None

    def test_get_status_when_disabled(self):
        """Test getting status when rate limiting is disabled."""
        service = RateLimitService(enabled=False)
        service.redis_client = None

        result = service.get_rate_limit_status("user", "123", RateLimitTier.USER)

        assert result is None

    def test_get_status_with_refill(self):
        """Test that status includes refilled tokens."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=50.0,
            last_refill=time.time() - 1.0,  # 1 second ago
            max_tokens=100.0,
            refill_rate=10.0,
        )

        service.redis_client = MagicMock()
        service.redis_client.get.return_value = service._serialize_bucket(bucket)

        result = service.get_rate_limit_status("user", "123", RateLimitTier.USER)

        # Should show refilled tokens
        assert result["current_tokens"] == 60.0  # 50 + 10


class TestIPBlocking:
    """Tests for IP blocking functionality."""

    def test_is_ip_blocked_not_blocked(self):
        """Test checking an IP that is not blocked."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.exists.return_value = 0

        result = service.is_ip_blocked("192.168.1.1")

        assert result is False

    def test_is_ip_blocked_blocked(self):
        """Test checking an IP that is blocked."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.exists.return_value = 1

        result = service.is_ip_blocked("192.168.1.1")

        assert result is True

    def test_is_ip_blocked_when_disabled(self):
        """Test IP blocking when rate limiting is disabled."""
        service = RateLimitService(enabled=False)
        service.redis_client = None

        result = service.is_ip_blocked("192.168.1.1")

        assert result is False

    def test_block_ip_success(self):
        """Test successfully blocking an IP."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.setex.return_value = True

        result = service.block_ip("192.168.1.1", duration=3600, reason="DDoS attack")

        assert result is True
        service.redis_client.setex.assert_called_once()

    def test_block_ip_default_duration(self):
        """Test blocking IP with default duration."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.setex.return_value = True

        result = service.block_ip("192.168.1.1")

        assert result is True
        # Verify setex was called with IP_BLOCK_DURATION (3600)
        call_args = service.redis_client.setex.call_args
        assert call_args[0][1] == service.IP_BLOCK_DURATION

    def test_block_ip_when_disabled(self):
        """Test blocking IP when rate limiting is disabled."""
        service = RateLimitService(enabled=False)
        service.redis_client = None

        result = service.block_ip("192.168.1.1")

        assert result is False

    def test_block_ip_redis_error(self):
        """Test blocking IP handles Redis errors."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.setex.side_effect = RedisError("Connection failed")

        result = service.block_ip("192.168.1.1")

        assert result is False

    def test_unblock_ip_success(self):
        """Test successfully unblocking an IP."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.delete.return_value = 1

        result = service.unblock_ip("192.168.1.1")

        assert result is True
        service.redis_client.delete.assert_called_once()

    def test_unblock_ip_not_blocked(self):
        """Test unblocking an IP that is not blocked."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.delete.return_value = 0

        result = service.unblock_ip("192.168.1.1")

        assert result is False

    def test_unblock_ip_when_disabled(self):
        """Test unblocking IP when rate limiting is disabled."""
        service = RateLimitService(enabled=False)
        service.redis_client = None

        result = service.unblock_ip("192.168.1.1")

        assert result is False


class TestHealthCheck:
    """Tests for health_check method."""

    def test_health_check_healthy(self):
        """Test health check when Redis is healthy."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.ping.return_value = True
        service.redis_client.scan_iter.return_value = iter([])

        result = service.health_check()

        assert result["status"] == "healthy"
        assert result["connected"] is True
        assert result["enabled"] is True
        assert result["key_count"] == 0
        assert result["blocked_ip_count"] == 0
        assert result["error"] is None

    def test_health_check_with_keys(self):
        """Test health check counts existing keys."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.ping.return_value = True

        # Mock rate limit keys
        rate_limit_keys = [
            f"{service.key_prefix}:user:1",
            f"{service.key_prefix}:user:2",
            f"{service.key_prefix}:ip:192.168.1.1",
        ]
        # Mock blocked IPs
        blocked_keys = [
            f"{service.key_prefix}:blocked:10.0.0.1",
        ]

        service.redis_client.scan_iter.side_effect = [
            iter(rate_limit_keys),
            iter(blocked_keys),
        ]

        result = service.health_check()

        assert result["status"] == "healthy"
        assert result["key_count"] == 3
        assert result["blocked_ip_count"] == 1

    def test_health_check_disabled(self):
        """Test health check when rate limiting is disabled."""
        service = RateLimitService(enabled=False)
        service.redis_client = None
        service.enabled = False

        result = service.health_check()

        assert result["status"] == "unhealthy"
        assert result["connected"] is False
        assert result["enabled"] is False
        assert result["error"] == "Rate limiting is disabled"

    def test_health_check_redis_error(self):
        """Test health check when Redis has an error."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.ping.side_effect = RedisError("Connection failed")

        result = service.health_check()

        assert result["status"] == "unhealthy"
        assert result["error"] is not None

    def test_health_check_ping_failure(self):
        """Test health check when ping fails."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.ping.return_value = False

        result = service.health_check()

        assert result["status"] == "unhealthy"
        assert result["connected"] is False


class TestClose:
    """Tests for close method."""

    def test_close_connection(self):
        """Test closing Redis connection."""
        service = RateLimitService(enabled=False)
        mock_client = MagicMock()
        service.redis_client = mock_client

        service.close()

        mock_client.close.assert_called_once()
        assert service.redis_client is None

    def test_close_no_connection(self):
        """Test closing when no connection exists."""
        service = RateLimitService(enabled=False)
        service.redis_client = None

        service.close()

        # Should not raise an error
        assert service.redis_client is None

    def test_close_handles_error(self):
        """Test that close handles errors gracefully."""
        service = RateLimitService(enabled=False)
        mock_client = MagicMock()
        mock_client.close.side_effect = Exception("Close error")
        service.redis_client = mock_client

        service.close()

        # Should still set redis_client to None despite error
        assert service.redis_client is None


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_zero_cost_request(self):
        """Test rate limit check with zero cost."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.get.return_value = None
        service.redis_client.setex.return_value = True

        result = service.check_rate_limit("user", "123", RateLimitTier.USER, cost=0)

        assert result.allowed is True
        # Should still deduct 0 tokens

    def test_very_large_cost(self):
        """Test rate limit check with very large cost."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=1000.0,
            last_refill=time.time(),
            max_tokens=1000.0,
            refill_rate=1000.0 / 60.0,
        )

        service.redis_client = MagicMock()
        service.redis_client.get.return_value = service._serialize_bucket(bucket)

        result = service.check_rate_limit("user", "123", RateLimitTier.USER, cost=10000)

        assert result.allowed is False

    def test_multiple_namespaces(self):
        """Test that different namespaces don't interfere."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.get.return_value = None
        service.redis_client.setex.return_value = True

        result1 = service.check_rate_limit("user", "123", RateLimitTier.USER)
        result2 = service.check_rate_limit("ip", "123", RateLimitTier.ANONYMOUS)

        # Both should be allowed (different namespaces)
        assert result1.allowed is True
        assert result2.allowed is True

    def test_unicode_identifier(self):
        """Test rate limit with unicode identifier."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.get.return_value = None
        service.redis_client.setex.return_value = True

        result = service.check_rate_limit("user", "用户123", RateLimitTier.USER)

        assert result.allowed is True

    def test_very_long_identifier(self):
        """Test rate limit with very long identifier."""
        service = RateLimitService(enabled=False)
        service.redis_client = MagicMock()
        service.redis_client.get.return_value = None
        service.redis_client.setex.return_value = True

        long_id = "a" * 1000
        result = service.check_rate_limit("user", long_id, RateLimitTier.USER)

        assert result.allowed is True

    def test_concurrent_request_simulation(self):
        """Test that tokens are properly tracked with rapid requests."""
        service = RateLimitService(enabled=False)
        bucket = TokenBucket(
            current_tokens=100.0,
            last_refill=time.time(),
            max_tokens=100.0,
            refill_rate=100.0 / 60.0,
        )

        service.redis_client = MagicMock()
        service.redis_client.get.return_value = service._serialize_bucket(bucket)
        service.redis_client.ttl.return_value = 60
        service.redis_client.setex.return_value = True

        # Simulate 10 rapid requests
        for i in range(10):
            result = service.check_rate_limit("user", "123", RateLimitTier.USER)
            if i < 10:
                assert result.allowed is True

        # Last request should show 90 remaining (100 - 10)
        assert result.remaining == 90


class TestRateLimitTierEnum:
    """Tests for RateLimitTier enum."""

    def test_tier_values(self):
        """Test that tier enum values are correct."""
        assert RateLimitTier.ANONYMOUS.value == "anonymous"
        assert RateLimitTier.USER.value == "user"
        assert RateLimitTier.ORG_ADMIN.value == "org_admin"
        assert RateLimitTier.ADMIN.value == "admin"

    def test_tier_comparison(self):
        """Test that tier enum comparison works."""
        tier1 = RateLimitTier.USER
        tier2 = RateLimitTier.USER
        tier3 = RateLimitTier.ADMIN

        assert tier1 == tier2
        assert tier1 != tier3


class TestRateLimitResult:
    """Tests for RateLimitResult dataclass."""

    def test_result_creation(self):
        """Test creating a rate limit result."""
        result = RateLimitResult(
            allowed=True,
            remaining=50,
            reset_at=1234567890,
            retry_after=None,
            limit=100,
            tier=RateLimitTier.USER,
        )

        assert result.allowed is True
        assert result.remaining == 50
        assert result.reset_at == 1234567890
        assert result.retry_after is None
        assert result.limit == 100
        assert result.tier == RateLimitTier.USER

    def test_blocked_result(self):
        """Test creating a blocked result."""
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            reset_at=1234567890,
            retry_after=60,
            limit=100,
            tier=RateLimitTier.USER,
        )

        assert result.allowed is False
        assert result.retry_after == 60


class TestTokenBucket:
    """Tests for TokenBucket dataclass."""

    def test_bucket_creation(self):
        """Test creating a token bucket."""
        bucket = TokenBucket(
            current_tokens=50.0,
            last_refill=1234567890.0,
            max_tokens=100.0,
            refill_rate=1.67,
        )

        assert bucket.current_tokens == 50.0
        assert bucket.last_refill == 1234567890.0
        assert bucket.max_tokens == 100.0
        assert bucket.refill_rate == 1.67

    def test_bucket_immutable(self):
        """Test that token bucket fields can be modified."""
        bucket = TokenBucket(
            current_tokens=50.0,
            last_refill=1234567890.0,
            max_tokens=100.0,
            refill_rate=1.67,
        )

        # Dataclasses are mutable by default
        bucket.current_tokens = 75.0
        assert bucket.current_tokens == 75.0
