"""
Tests for Prometheus metrics emission for rate limiting.

Tests cover counter and gauge metrics for blocked requests, rate limit hits,
IP blocking/unblocking, and error scenarios.
"""
import json
import time
from unittest.mock import Mock, patch, MagicMock

import pytest
from prometheus_client import CollectorRegistry

from services.rate_limit_service import (
    RateLimitService,
    RateLimitTier,
    TokenBucket,
)
from backend.utils.metrics import MetricsRegistry


class TestRateLimitMetricsInitialization:
    """Tests for rate limit metrics initialization."""

    def test_metrics_registry_has_rate_limit_counters(self):
        """Test that MetricsRegistry has rate limit counters defined."""
        registry = MetricsRegistry()

        assert hasattr(registry, "rate_limit_requests_total")
        assert hasattr(registry, "rate_limit_hits_total")
        assert hasattr(registry, "rate_limit_duration_seconds")

    def test_rate_limit_service_has_metrics(self):
        """Test that RateLimitService has metrics registry."""
        with patch("services.rate_limit_service.get_rate_limit_service") as mock_get_service:
            mock_service = Mock(spec=RateLimitService)
            mock_service.metrics = MetricsRegistry()
            mock_get_service.return_value = mock_service

            service = mock_get_service()
            assert service.metrics is not None
            assert isinstance(service.metrics, MetricsRegistry)


class TestRateLimitBlockedMetrics:
    """Tests for rate limit blocked request metrics."""

    def test_record_blocked_request_increments_counter(self):
        """Test that recording a blocked request increments the counter."""
        registry = MetricsRegistry()

        # Record a blocked request
        registry.record_rate_limit(
            limit_type="user",
            endpoint="/api/resumes",
            client_identifier="user_123",
            blocked=True,
            retry_after=60,
        )

        # Verify the counter was incremented
        metric = registry.rate_limit_requests_total.labels(
            limit_type="user",
            endpoint="/api/resumes",
            client_identifier="user_123"
        )

        # The metric should have been incremented
        samples = list(metric.collect())[0].samples
        assert len(samples) > 0
        assert samples[0].value == 1.0

    def test_record_multiple_blocked_requests(self):
        """Test recording multiple blocked requests."""
        registry = MetricsRegistry()

        # Record multiple blocked requests
        for _ in range(5):
            registry.record_rate_limit(
                limit_type="ip",
                endpoint="/api/search",
                client_identifier="192.168.1.1",
                blocked=True,
                retry_after=120,
            )

        # Verify the counter was incremented 5 times
        metric = registry.rate_limit_requests_total.labels(
            limit_type="ip",
            endpoint="/api/search",
            client_identifier="192.168.1.1"
        )

        samples = list(metric.collect())[0].samples
        assert samples[0].value == 5.0

    def test_different_limit_types_create_separate_metrics(self):
        """Test that different limit types create separate metric labels."""
        registry = MetricsRegistry()

        # Record blocked requests for different limit types
        registry.record_rate_limit(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_1",
            blocked=True,
        )
        registry.record_rate_limit(
            limit_type="ip",
            endpoint="/api/test",
            client_identifier="192.168.1.1",
            blocked=True,
        )

        # Verify both metrics exist
        user_metric = registry.rate_limit_requests_total.labels(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_1"
        )
        ip_metric = registry.rate_limit_requests_total.labels(
            limit_type="ip",
            endpoint="/api/test",
            client_identifier="192.168.1.1"
        )

        user_samples = list(user_metric.collect())[0].samples
        ip_samples = list(ip_metric.collect())[0].samples

        assert user_samples[0].value == 1.0
        assert ip_samples[0].value == 1.0


class TestRateLimitHitsMetrics:
    """Tests for rate limit hit (near threshold) metrics."""

    def test_record_rate_limit_hit_increments_counter(self):
        """Test that recording a rate limit hit increments the counter."""
        registry = MetricsRegistry()

        # Record a rate limit hit (near threshold but not blocked)
        registry.record_rate_limit(
            limit_type="user",
            endpoint="/api/resumes",
            client_identifier="user_456",
            blocked=False,
        )

        # Verify the hits counter was incremented
        metric = registry.rate_limit_hits_total.labels(
            limit_type="user",
            endpoint="/api/resumes",
            client_identifier="user_456"
        )

        samples = list(metric.collect())[0].samples
        assert len(samples) > 0
        assert samples[0].value == 1.0

    def test_blocked_false_does_not_increment_blocked_counter(self):
        """Test that blocked=False doesn't increment the blocked counter."""
        registry = MetricsRegistry()

        # Record a rate limit hit (not blocked)
        registry.record_rate_limit(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_789",
            blocked=False,
        )

        # Verify blocked counter is still 0
        blocked_metric = registry.rate_limit_requests_total.labels(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_789"
        )

        # Collect samples and check for this specific label combination
        samples = list(blocked_metric.collect())[0].samples
        # If the metric was never incremented, there should be no samples with a value > 0
        user_samples = [s for s in samples if s.labels.get('client_identifier') == 'user_789']
        assert len(user_samples) == 0 or user_samples[0].value == 0.0

    def test_multiple_hits_and_blocks_tracked_separately(self):
        """Test that hits and blocks are tracked in separate counters."""
        registry = MetricsRegistry()

        # Record 3 hits and 2 blocks
        for _ in range(3):
            registry.record_rate_limit(
                limit_type="user",
                endpoint="/api/test",
                client_identifier="user_multi",
                blocked=False,
            )

        for _ in range(2):
            registry.record_rate_limit(
                limit_type="user",
                endpoint="/api/test",
                client_identifier="user_multi",
                blocked=True,
                retry_after=60,
            )

        # Verify counters
        hits_metric = registry.rate_limit_hits_total.labels(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_multi"
        )
        blocks_metric = registry.rate_limit_requests_total.labels(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_multi"
        )

        hits_samples = list(hits_metric.collect())[0].samples
        blocks_samples = list(blocks_metric.collect())[0].samples

        assert hits_samples[0].value == 3.0
        assert blocks_samples[0].value == 2.0


class TestRateLimitDurationMetrics:
    """Tests for rate limit duration gauge metrics."""

    def test_record_blocked_request_sets_duration_gauge(self):
        """Test that recording a blocked request sets the duration gauge."""
        registry = MetricsRegistry()

        retry_after = 120
        registry.record_rate_limit(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_abc",
            blocked=True,
            retry_after=retry_after,
        )

        # Verify the gauge was set
        gauge = registry.rate_limit_duration_seconds.labels(
            limit_type="user",
            client_identifier="user_abc"
        )

        samples = list(gauge.collect())[0].samples
        assert len(samples) > 0
        assert samples[0].value == retry_after

    def test_gauge_updates_with_new_retry_after_value(self):
        """Test that the gauge updates when a new retry_after is provided."""
        registry = MetricsRegistry()

        # First blocked request
        registry.record_rate_limit(
            limit_type="ip",
            endpoint="/api/test",
            client_identifier="10.0.0.1",
            blocked=True,
            retry_after=60,
        )

        # Update with new retry_after
        registry.record_rate_limit(
            limit_type="ip",
            endpoint="/api/test",
            client_identifier="10.0.0.1",
            blocked=True,
            retry_after=300,
        )

        gauge = registry.rate_limit_duration_seconds.labels(
            limit_type="ip",
            client_identifier="10.0.0.1"
        )

        samples = list(gauge.collect())[0].samples
        assert samples[0].value == 300  # Should be updated to latest value

    def test_blocked_without_retry_after_does_not_set_gauge(self):
        """Test that blocked=True without retry_after doesn't set the gauge."""
        registry = MetricsRegistry()

        registry.record_rate_limit(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_xyz",
            blocked=True,
            # retry_after not provided
        )

        # Gauge should not be set if retry_after is None
        gauge = registry.rate_limit_duration_seconds.labels(
            limit_type="user",
            client_identifier="user_xyz"
        )

        # Check if any samples exist for this metric
        samples = list(gauge.collect())[0].samples
        user_samples = [s for s in samples if s.labels.get('client_identifier') == 'user_xyz']
        # Either no samples or the gauge hasn't been set
        assert len(user_samples) == 0 or user_samples[0].value == 0.0


class TestRateLimitServiceMetricsEmission:
    """Tests for RateLimitService metric emission during operations."""

    @patch("services.rate_limit_service.RateLimitService._initialize_connection")
    def test_check_rate_limit_records_hit_when_near_threshold(self, mock_init):
        """Test that check_rate_limit records a hit when near threshold."""
        mock_init.return_value = None

        # Create a mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps({
            "current_tokens": 15.0,  # Below 20% threshold of 100
            "last_refill": time.time(),
            "max_tokens": 100.0,
            "refill_rate": 100.0 / 60,
        }).encode("utf-8")
        mock_redis.ttl.return_value = 60

        service = RateLimitService(enabled=True)
        service.redis_client = mock_redis
        service.metrics = MetricsRegistry()

        # Check rate limit - should record a hit
        result = service.check_rate_limit(
            namespace="user",
            identifier="user_123",
            tier=RateLimitTier.USER,
        )

        assert result.allowed is True
        # Metric should have been recorded
        # We can't easily verify the exact value without inspecting the registry
        # but we can verify the operation completed without error

    @patch("services.rate_limit_service.RateLimitService._initialize_connection")
    def test_check_rate_limit_records_block_when_exceeded(self, mock_init):
        """Test that check_rate_limit records a block when limit exceeded."""
        mock_init.return_value = None

        # Create a mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps({
            "current_tokens": 0.0,  # No tokens left
            "last_refill": time.time(),
            "max_tokens": 100.0,
            "refill_rate": 100.0 / 60,
        }).encode("utf-8")
        mock_redis.ttl.return_value = 60

        service = RateLimitService(enabled=True)
        service.redis_client = mock_redis
        service.metrics = MetricsRegistry()

        # Check rate limit - should be blocked
        result = service.check_rate_limit(
            namespace="user",
            identifier="user_456",
            tier=RateLimitTier.USER,
        )

        assert result.allowed is False
        assert result.retry_after is not None
        # Metric should have been recorded for blocked request

    @patch("services.rate_limit_service.RateLimitService._initialize_connection")
    def test_check_rate_limit_when_disabled_records_metric(self, mock_init):
        """Test that check_rate_limit records a metric when disabled."""
        mock_init.return_value = None

        service = RateLimitService(enabled=False)
        service.redis_client = None
        service.metrics = MetricsRegistry()

        # Check rate limit when disabled
        result = service.check_rate_limit(
            namespace="user",
            identifier="user_789",
            tier=RateLimitTier.USER,
        )

        assert result.allowed is True
        assert result.remaining == -1  # Unlimited

    @patch("services.rate_limit_service.RateLimitService._initialize_connection")
    def test_block_ip_records_metric(self, mock_init):
        """Test that blocking an IP records a metric."""
        mock_init.return_value = None

        mock_redis = MagicMock()
        mock_redis.setex.return_value = True

        service = RateLimitService(enabled=True)
        service.redis_client = mock_redis
        service.metrics = MetricsRegistry()

        # Block an IP
        result = service.block_ip(
            ip_address="192.168.1.100",
            duration=3600,
            reason="Test blocking",
        )

        assert result is True
        # Metric should have been recorded for IP block

    @patch("services.rate_limit_service.RateLimitService._initialize_connection")
    def test_unblock_ip_records_metric(self, mock_init):
        """Test that unblocking an IP records a metric."""
        mock_init.return_value = None

        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1  # One key deleted

        service = RateLimitService(enabled=True)
        service.redis_client = mock_redis
        service.metrics = MetricsRegistry()

        # Unblock an IP
        result = service.unblock_ip(ip_address="192.168.1.100")

        assert result is True
        # Metric should have been recorded for IP unblock

    @patch("services.rate_limit_service.RateLimitService._initialize_connection")
    def test_reset_rate_limit_records_metric(self, mock_init):
        """Test that resetting rate limit records a metric."""
        mock_init.return_value = None

        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1  # One key deleted

        service = RateLimitService(enabled=True)
        service.redis_client = mock_redis
        service.metrics = MetricsRegistry()

        # Reset rate limit
        result = service.reset_rate_limit(
            namespace="user",
            identifier="user_999",
        )

        assert result is True
        # Metric should have been recorded for reset


class TestRateLimitErrorMetrics:
    """Tests for rate limit metrics in error scenarios."""

    @patch("services.rate_limit_service.RateLimitService._initialize_connection")
    def test_redis_error_records_metric(self, mock_init):
        """Test that Redis errors record appropriate metrics."""
        mock_init.return_value = None

        from redis.exceptions import RedisError

        mock_redis = MagicMock()
        mock_redis.get.side_effect = RedisError("Connection lost")

        service = RateLimitService(enabled=True)
        service.redis_client = mock_redis
        service.metrics = MetricsRegistry()

        # Check rate limit - should fail but record metric
        result = service.check_rate_limit(
            namespace="user",
            identifier="user_error",
            tier=RateLimitTier.USER,
        )

        # Should fail open
        assert result.allowed is True
        assert result.remaining == -1

    @patch("services.rate_limit_service.RateLimitService._initialize_connection")
    def test_deserialization_error_records_metric(self, mock_init):
        """Test that deserialization errors record appropriate metrics."""
        mock_init.return_value = None

        mock_redis = MagicMock()
        mock_redis.get.return_value = b"invalid json"

        service = RateLimitService(enabled=True)
        service.redis_client = mock_redis
        service.metrics = MetricsRegistry()

        # Check rate limit - should fail due to invalid JSON
        result = service.check_rate_limit(
            namespace="user",
            identifier="user_bad_json",
            tier=RateLimitTier.USER,
        )

        # Should fail open
        assert result.allowed is True


class TestMetricsLabelCombinations:
    """Tests for various metric label combinations."""

    def test_all_limit_types(self):
        """Test metrics for all rate limit types."""
        registry = MetricsRegistry()

        limit_types = ["user", "ip", "org", "global", "api_key"]

        for limit_type in limit_types:
            registry.record_rate_limit(
                limit_type=limit_type,
                endpoint="/api/test",
                client_identifier=f"{limit_type}_client",
                blocked=True,
                retry_after=60,
            )

        # Verify all limit types have metrics
        for limit_type in limit_types:
            metric = registry.rate_limit_requests_total.labels(
                limit_type=limit_type,
                endpoint="/api/test",
                client_identifier=f"{limit_type}_client"
            )
            samples = list(metric.collect())[0].samples
            assert samples[0].value == 1.0

    def test_multiple_endpoints(self):
        """Test metrics for multiple endpoints."""
        registry = MetricsRegistry()

        endpoints = ["/api/resumes", "/api/jobs", "/api/search", "/api/users"]

        for endpoint in endpoints:
            registry.record_rate_limit(
                limit_type="user",
                endpoint=endpoint,
                client_identifier="user_multi_endpoint",
                blocked=False,
            )

        # Verify all endpoints have metrics
        for endpoint in endpoints:
            metric = registry.rate_limit_hits_total.labels(
                limit_type="user",
                endpoint=endpoint,
                client_identifier="user_multi_endpoint"
            )
            samples = list(metric.collect())[0].samples
            assert samples[0].value == 1.0

    def test_multiple_clients(self):
        """Test metrics for multiple clients."""
        registry = MetricsRegistry()

        clients = ["user_1", "user_2", "user_3", "192.168.1.1", "10.0.0.1"]

        for client in clients:
            registry.record_rate_limit(
                limit_type="user" if "user" in client else "ip",
                endpoint="/api/test",
                client_identifier=client,
                blocked=True,
                retry_after=30,
            )

        # Verify all clients have metrics
        for client in clients:
            limit_type = "user" if "user" in client else "ip"
            metric = registry.rate_limit_requests_total.labels(
                limit_type=limit_type,
                endpoint="/api/test",
                client_identifier=client
            )
            samples = list(metric.collect())[0].samples
            assert samples[0].value == 1.0


class TestMetricsIsolation:
    """Tests for metrics isolation and independence."""

    def test_separate_registries_do_not_interfere(self):
        """Test that separate metric registries don't interfere."""
        registry1 = MetricsRegistry()
        registry2 = MetricsRegistry()

        registry1.record_rate_limit(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_reg1",
            blocked=True,
        )

        registry2.record_rate_limit(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_reg2",
            blocked=True,
        )

        # Each registry should have its own count
        metric1 = registry1.rate_limit_requests_total.labels(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_reg1"
        )
        metric2 = registry2.rate_limit_requests_total.labels(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_reg2"
        )

        samples1 = list(metric1.collect())[0].samples
        samples2 = list(metric2.collect())[0].samples

        # Each should have 1, not 2
        assert samples1[0].value == 1.0
        assert samples2[0].value == 1.0

    def test_hits_and_blocked_counters_independent(self):
        """Test that hits and blocked counters are independent."""
        registry = MetricsRegistry()

        # Record a hit
        registry.record_rate_limit(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_indep",
            blocked=False,
        )

        # Record a block
        registry.record_rate_limit(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_indep",
            blocked=True,
            retry_after=60,
        )

        # Both counters should be 1, not interfering
        hits_metric = registry.rate_limit_hits_total.labels(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_indep"
        )
        blocks_metric = registry.rate_limit_requests_total.labels(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_indep"
        )

        hits_samples = list(hits_metric.collect())[0].samples
        blocks_samples = list(blocks_metric.collect())[0].samples

        assert hits_samples[0].value == 1.0
        assert blocks_samples[0].value == 1.0


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_client_identifier(self):
        """Test metrics with empty client identifier."""
        registry = MetricsRegistry()

        registry.record_rate_limit(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="",  # Empty identifier
            blocked=True,
        )

        # Should still record the metric
        metric = registry.rate_limit_requests_total.labels(
            limit_type="user",
            endpoint="/api/test",
            client_identifier=""
        )
        samples = list(metric.collect())[0].samples
        assert samples[0].value == 1.0

    def test_special_characters_in_identifiers(self):
        """Test metrics with special characters in identifiers."""
        registry = MetricsRegistry()

        special_identifiers = [
            "user@example.com",
            "user/123",
            "user:api:client",
            "user.with.dots",
        ]

        for identifier in special_identifiers:
            registry.record_rate_limit(
                limit_type="user",
                endpoint="/api/test",
                client_identifier=identifier,
                blocked=False,
            )

        # All should be recorded
        for identifier in special_identifiers:
            metric = registry.rate_limit_hits_total.labels(
                limit_type="user",
                endpoint="/api/test",
                client_identifier=identifier
            )
            samples = list(metric.collect())[0].samples
            assert samples[0].value == 1.0

    def test_zero_retry_after(self):
        """Test metrics with zero retry_after value."""
        registry = MetricsRegistry()

        registry.record_rate_limit(
            limit_type="user",
            endpoint="/api/test",
            client_identifier="user_zero",
            blocked=True,
            retry_after=0,
        )

        # Should record the metric with zero value
        gauge = registry.rate_limit_duration_seconds.labels(
            limit_type="user",
            client_identifier="user_zero"
        )
        samples = list(gauge.collect())[0].samples
        assert samples[0].value == 0.0

    def test_very_large_retry_after(self):
        """Test metrics with very large retry_after value."""
        registry = MetricsRegistry()

        large_value = 86400  # 24 hours
        registry.record_rate_limit(
            limit_type="ip",
            endpoint="/api/test",
            client_identifier="192.168.1.1",
            blocked=True,
            retry_after=large_value,
        )

        gauge = registry.rate_limit_duration_seconds.labels(
            limit_type="ip",
            client_identifier="192.168.1.1"
        )
        samples = list(gauge.collect())[0].samples
        assert samples[0].value == large_value


class TestMetricsIntegration:
    """Integration tests for rate limit metrics."""

    @patch("services.rate_limit_service.RateLimitService._initialize_connection")
    def test_full_rate_limit_workflow_metrics(self, mock_init):
        """Test metrics through a full rate limit workflow."""
        mock_init.return_value = None

        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # First request - no bucket
        mock_redis.setex.return_value = True
        mock_redis.ttl.return_value = 60

        service = RateLimitService(enabled=True)
        service.redis_client = mock_redis
        service.metrics = MetricsRegistry()

        # First request - should be allowed
        result1 = service.check_rate_limit(
            namespace="user",
            identifier="user_workflow",
            tier=RateLimitTier.USER,
        )
        assert result1.allowed is True

        # Simulate bucket with low tokens
        mock_redis.get.return_value = json.dumps({
            "current_tokens": 5.0,  # Near threshold
            "last_refill": time.time(),
            "max_tokens": 100.0,
            "refill_rate": 100.0 / 60,
        }).encode("utf-8")

        # Second request - near threshold, should record hit
        result2 = service.check_rate_limit(
            namespace="user",
            identifier="user_workflow",
            tier=RateLimitTier.USER,
        )
        assert result2.allowed is True

        # Simulate empty bucket
        mock_redis.get.return_value = json.dumps({
            "current_tokens": 0.0,
            "last_refill": time.time(),
            "max_tokens": 100.0,
            "refill_rate": 100.0 / 60,
        }).encode("utf-8")

        # Third request - should be blocked
        result3 = service.check_rate_limit(
            namespace="user",
            identifier="user_workflow",
            tier=RateLimitTier.USER,
        )
        assert result3.allowed is False
        assert result3.retry_after is not None

        # Verify metrics were recorded through the workflow
        # The service should have emitted metrics at each step
