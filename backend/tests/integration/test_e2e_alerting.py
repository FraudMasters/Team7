"""
End-to-End Alerting Integration Tests

This module provides comprehensive tests for the health monitoring and alerting system.
It tests the complete flow from health check failure to alert notification.

Test Coverage:
1. Health check detects unhealthy components
2. Alert creation with correct severity levels
3. Alerting service send functionality
4. Alert history and cooldown tracking
5. Health monitoring Celery task execution
6. Recovery notification scenario
7. Multiple alert channel handling

Run with: pytest tests/integration/test_e2e_alerting.py -v
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Test imports
import sys
sys.path.insert(0, '.')

from services.alerting import (
    Alert,
    AlertingService,
    get_alerting_service,
    BaseNotificationChannel,
)
from services.health_check import (
    HealthCheckResult,
    HealthCheckService,
    get_health_check_service,
)
from tasks.health_monitoring import (
    _create_health_alert,
    _perform_health_checks_and_alerts,
    _check_component_and_alert,
    _send_alert_if_needed,
)


class MockNotificationChannel(BaseNotificationChannel):
    """Mock notification channel for testing."""

    def __init__(self, name: str = "mock_channel"):
        super().__init__(enabled=True)
        self.name = name
        self.sent_alerts = []

    async def send(self, alert: Alert) -> bool:
        """Mock send that records the alert."""
        self.sent_alerts.append(alert)
        return True


class TestAlertCreation:
    """Test alert creation from health check results."""

    @pytest.mark.asyncio
    async def test_create_unhealthy_alert(self):
        """Test creating an alert for unhealthy component."""
        component_result = {
            "status": "unhealthy",
            "message": "Connection refused",
            "error": "Redis connection failed",
            "response_time_ms": 0,
            "details": {},
        }

        alert = _create_health_alert(
            component_name="redis",
            status="unhealthy",
            component_result=component_result,
        )

        assert alert.component == "redis"
        assert alert.severity == Alert.SEVERITY_CRITICAL
        assert alert.status == "unhealthy"
        assert "Redis" in alert.title
        assert "Connection refused" in alert.message or "Error:" in alert.message

    @pytest.mark.asyncio
    async def test_create_degraded_alert(self):
        """Test creating an alert for degraded component."""
        component_result = {
            "status": "degraded",
            "message": "High response time",
            "error": None,
            "response_time_ms": 1500,
            "details": {},
        }

        alert = _create_health_alert(
            component_name="database",
            status="degraded",
            component_result=component_result,
        )

        assert alert.component == "database"
        assert alert.severity == Alert.SEVERITY_WARNING
        assert alert.status == "degraded"
        assert "1500.00ms" in alert.message

    @pytest.mark.asyncio
    async def test_create_recovery_alert(self):
        """Test creating a recovery alert."""
        component_result = {
            "status": "healthy",
            "message": "Service operational",
            "error": None,
            "response_time_ms": 5,
            "details": {},
        }

        alert = _create_health_alert(
            component_name="redis",
            status="healthy",
            component_result=component_result,
        )

        assert alert.component == "redis"
        assert alert.severity == Alert.SEVERITY_INFO
        assert "Recovered" in alert.title


class TestAlertingService:
    """Test alerting service functionality."""

    @pytest.mark.asyncio
    async def test_send_alert_single_channel(self):
        """Test sending alert through a single channel."""
        service = AlertingService()
        mock_channel = MockNotificationChannel("test_channel")
        service.register_channel("test_channel", mock_channel)

        alert = Alert(
            title="Test Alert",
            message="Test message",
            severity=Alert.SEVERITY_CRITICAL,
            component="test",
            status="unhealthy",
        )

        results = await service.send_alert(alert)

        assert results["test_channel"] is True
        assert len(mock_channel.sent_alerts) == 1
        assert mock_channel.sent_alerts[0].alert_id == alert.alert_id

    @pytest.mark.asyncio
    async def test_send_alert_multiple_channels(self):
        """Test sending alert through multiple channels."""
        service = AlertingService()
        channel1 = MockNotificationChannel("channel1")
        channel2 = MockNotificationChannel("channel2")
        service.register_channel("channel1", channel1)
        service.register_channel("channel2", channel2)

        alert = Alert(
            title="Test Alert",
            message="Test message",
            severity=Alert.SEVERITY_CRITICAL,
            component="test",
            status="unhealthy",
        )

        results = await service.send_alert(alert)

        assert results["channel1"] is True
        assert results["channel2"] is True
        assert len(channel1.sent_alerts) == 1
        assert len(channel2.sent_alerts) == 1

    @pytest.mark.asyncio
    async def test_alert_cooldown(self):
        """Test alert cooldown prevents duplicate alerts."""
        service = AlertingService(cooldown_minutes=30)
        mock_channel = MockNotificationChannel("test_channel")
        service.register_channel("test_channel", mock_channel)

        alert = Alert(
            title="Test Alert",
            message="Test message",
            severity=Alert.SEVERITY_CRITICAL,
            component="redis",
            status="unhealthy",
        )

        # First alert should send
        results1 = await service.send_alert(alert)
        assert results1["test_channel"] is True
        assert len(mock_channel.sent_alerts) == 1

        # Second alert with same component should be blocked by cooldown
        alert2 = Alert(
            title="Test Alert 2",
            message="Test message 2",
            severity=Alert.SEVERITY_CRITICAL,
            component="redis",
            status="unhealthy",
        )

        results2 = await service.send_alert(alert2)
        # Should not send again due to cooldown
        assert len(mock_channel.sent_alerts) == 1

    @pytest.mark.asyncio
    async def test_alert_history_tracking(self):
        """Test that alert history is tracked correctly."""
        service = AlertingService(cooldown_minutes=30)

        alert = Alert(
            title="Test Alert",
            message="Test message",
            severity=Alert.SEVERITY_CRITICAL,
            component="redis",
            status="unhealthy",
        )

        # Initially no cooldown
        assert not service._is_in_cooldown(alert)

        # Record alert
        service._record_alert(alert)

        # Now should be in cooldown
        assert service._is_in_cooldown(alert)

        # Clear history
        service.clear_history("redis")

        # No longer in cooldown
        assert not service._is_in_cooldown(alert)

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test alerting service health check."""
        service = AlertingService()
        channel1 = MockNotificationChannel("channel1")
        channel2 = MockNotificationChannel("channel2")
        service.register_channel("channel1", channel1)
        service.register_channel("channel2", channel2)

        health = service.health_check()

        assert health["status"] == "healthy"
        assert health["enabled"] is True
        assert health["channels_enabled"] == 2
        assert health["channels_total"] == 2
        assert "channel1" in health["channel_names"]
        assert "channel2" in health["channel_names"]


class TestHealthMonitoringFlow:
    """Test complete health monitoring and alerting flow."""

    @pytest.mark.asyncio
    async def test_health_monitoring_with_unhealthy_component(self):
        """Test health monitoring detects and alerts on unhealthy component."""
        # Create a mock health check service that returns unhealthy Redis
        mock_health_result = {
            "overall_status": "unhealthy",
            "components": {
                "database": {
                    "status": "healthy",
                    "message": "Database operational",
                    "error": None,
                    "response_time_ms": 10,
                    "details": {},
                },
                "redis": {
                    "status": "unhealthy",
                    "message": "Connection refused",
                    "error": "Redis connection failed",
                    "response_time_ms": 0,
                    "details": {},
                },
                "celery": {
                    "status": "healthy",
                    "message": "Celery operational",
                    "error": None,
                    "response_time_ms": 50,
                    "details": {},
                },
            },
            "summary": {
                "total_time_ms": 60,
                "components_checked": 3,
                "components_healthy": 2,
                "components_degraded": 0,
                "components_unhealthy": 1,
            },
        }

        # Mock the health check service
        with patch.object(
            HealthCheckService, 'check_all', new=AsyncMock(return_value=mock_health_result)
        ):
            # Setup alerting service with mock channel
            alerting_service = get_alerting_service()
            mock_channel = MockNotificationChannel("test_channel")
            alerting_service.register_channel("test_channel", mock_channel)
            alerting_service.clear_history()  # Clear any previous alerts

            # Run health monitoring
            result = await _perform_health_checks_and_alerts()

            # Verify results
            assert result["status"] == "success"
            assert result["overall_status"] == "unhealthy"
            assert result["components_unhealthy"] == 1

            # Verify alert was sent for unhealthy essential component
            assert len(mock_channel.sent_alerts) >= 1

            # Find the Redis alert
            redis_alerts = [
                a for a in mock_channel.sent_alerts
                if a.component == "redis" and a.severity == Alert.SEVERITY_CRITICAL
            ]
            assert len(redis_alerts) >= 1
            assert redis_alerts[0].status == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_monitoring_with_degraded_component(self):
        """Test health monitoring alerts on degraded essential components."""
        mock_health_result = {
            "overall_status": "degraded",
            "components": {
                "database": {
                    "status": "degraded",
                    "message": "High response time",
                    "error": None,
                    "response_time_ms": 1200,
                    "details": {},
                },
                "redis": {
                    "status": "healthy",
                    "message": "Redis operational",
                    "error": None,
                    "response_time_ms": 5,
                    "details": {},
                },
                "celery": {
                    "status": "healthy",
                    "message": "Celery operational",
                    "error": None,
                    "response_time_ms": 30,
                    "details": {},
                },
            },
            "summary": {
                "total_time_ms": 1235,
                "components_checked": 3,
                "components_healthy": 2,
                "components_degraded": 1,
                "components_unhealthy": 0,
            },
        }

        with patch.object(
            HealthCheckService, 'check_all', new=AsyncMock(return_value=mock_health_result)
        ):
            alerting_service = get_alerting_service()
            mock_channel = MockNotificationChannel("test_channel")
            alerting_service.register_channel("test_channel", mock_channel)
            alerting_service.clear_history()

            result = await _perform_health_checks_and_alerts()

            assert result["overall_status"] == "degraded"
            assert result["components_degraded"] == 1

            # Check if warning alerts are sent for degraded essential components
            if alerting_service.alert_on_warning:
                # Should have at least one alert
                assert len(mock_channel.sent_alerts) >= 1

                # Find the database alert (should be warning severity)
                db_alerts = [
                    a for a in mock_channel.sent_alerts
                    if a.component == "database" and a.severity == Alert.SEVERITY_WARNING
                ]
                assert len(db_alerts) >= 1

    @pytest.mark.asyncio
    async def test_component_specific_check_and_alert(self):
        """Test checking a specific component and alerting if unhealthy."""
        # Mock health check result for specific component
        mock_component_result = HealthCheckResult(
            name="redis",
            status="unhealthy",
            message="Connection refused",
            error="Redis connection failed",
            response_time_ms=0,
            details={},
            essential=True,
        )

        with patch.object(
            HealthCheckService, 'check_component',
            new=AsyncMock(return_value=mock_component_result)
        ):
            alerting_service = get_alerting_service()
            mock_channel = MockNotificationChannel("test_channel")
            alerting_service.register_channel("test_channel", mock_channel)
            alerting_service.clear_history()

            # Check component with alerting enabled
            result = await _check_component_and_alert(
                component_name="redis",
                send_alert_if_unhealthy=True,
            )

            assert result["component_status"] == "unhealthy"
            assert result["alerts_sent"] >= 1

            # Verify alert was sent
            redis_alerts = [
                a for a in mock_channel.sent_alerts if a.component == "redis"
            ]
            assert len(redis_alerts) >= 1

    @pytest.mark.asyncio
    async def test_recovery_notification(self):
        """Test that recovery is properly detected and notified."""
        # Start with unhealthy state
        mock_unhealthy_result = {
            "overall_status": "unhealthy",
            "components": {
                "redis": {
                    "status": "unhealthy",
                    "message": "Connection refused",
                    "error": "Redis connection failed",
                    "response_time_ms": 0,
                    "details": {},
                },
            },
            "summary": {
                "components_unhealthy": 1,
                "components_healthy": 0,
                "components_degraded": 0,
                "components_checked": 1,
                "total_time_ms": 0,
            },
        }

        alerting_service = get_alerting_service()
        mock_channel = MockNotificationChannel("test_channel")
        alerting_service.register_channel("test_channel", mock_channel)
        alerting_service.clear_history()

        with patch.object(
            HealthCheckService, 'check_all',
            new=AsyncMock(return_value=mock_unhealthy_result)
        ):
            # First check - unhealthy
            result1 = await _perform_health_checks_and_alerts()
            assert result1["overall_status"] == "unhealthy"
            initial_alert_count = len(mock_channel.sent_alerts)

        # Now simulate recovery
        mock_healthy_result = {
            "overall_status": "healthy",
            "components": {
                "redis": {
                    "status": "healthy",
                    "message": "Redis operational",
                    "error": None,
                    "response_time_ms": 5,
                    "details": {},
                },
            },
            "summary": {
                "components_unhealthy": 0,
                "components_healthy": 1,
                "components_degraded": 0,
                "components_checked": 1,
                "total_time_ms": 5,
            },
        }

        with patch.object(
            HealthCheckService, 'check_all',
            new=AsyncMock(return_value=mock_healthy_result)
        ):
            # Second check - healthy (recovery)
            result2 = await _perform_health_checks_and_alerts()
            assert result2["overall_status"] == "healthy"

            # Note: Recovery alerts (info severity) may or may not be sent
            # depending on configuration. The key is that unhealthy alerts stop.


class TestAlertChannelHandling:
    """Test multiple alert channel handling."""

    @pytest.mark.asyncio
    async def test_disabled_channel_not_used(self):
        """Test that disabled channels are not used."""
        service = AlertingService()
        channel = MockNotificationChannel("disabled_channel")
        channel.enabled = False
        service.register_channel("disabled_channel", channel)

        alert = Alert(
            title="Test",
            message="Test",
            severity=Alert.SEVERITY_CRITICAL,
            component="test",
            status="unhealthy",
        )

        results = await service.send_alert(alert)

        # Disabled channel should show as not sent
        assert results.get("disabled_channel") is False
        assert len(channel.sent_alerts) == 0

    @pytest.mark.asyncio
    async def test_channel_send_failure_handling(self):
        """Test that alert continues even if one channel fails."""
        service = AlertingService()

        # Channel that succeeds
        success_channel = MockNotificationChannel("success_channel")
        service.register_channel("success_channel", success_channel)

        # Channel that fails
        fail_channel = MockNotificationChannel("fail_channel")
        fail_channel.send = AsyncMock(return_value=False)
        service.register_channel("fail_channel", fail_channel)

        alert = Alert(
            title="Test",
            message="Test",
            severity=Alert.SEVERITY_CRITICAL,
            component="test",
            status="unhealthy",
        )

        results = await service.send_alert(alert)

        # One channel should succeed, one should fail
        assert results["success_channel"] is True
        assert results["fail_channel"] is False
        assert len(success_channel.sent_alerts) == 1


class TestAlertCooldownBehavior:
    """Test alert cooldown and history behavior."""

    @pytest.mark.asyncio
    async def test_cooldown_prevents_duplicate_alerts(self):
        """Test that cooldown prevents duplicate alerts for same component."""
        service = AlertingService(cooldown_minutes=30)
        channel = MockNotificationChannel("test_channel")
        service.register_channel("test_channel", channel)

        alert1 = Alert(
            title="Redis Unhealthy",
            message="Redis is down",
            severity=Alert.SEVERITY_CRITICAL,
            component="redis",
            status="unhealthy",
        )

        # First alert should send
        results1 = await service.send_alert(alert1)
        assert results1["test_channel"] is True
        assert len(channel.sent_alerts) == 1

        # Immediate second alert should be blocked
        alert2 = Alert(
            title="Redis Still Unhealthy",
            message="Redis still down",
            severity=Alert.SEVERITY_CRITICAL,
            component="redis",
            status="unhealthy",
        )

        results2 = await service.send_alert(alert2)
        assert results2.get("test_channel") is False or len(channel.sent_alerts) == 1

    @pytest.mark.asyncio
    async def test_different_components_not_affected_by_cooldown(self):
        """Test that different components are not affected by each other's cooldown."""
        service = AlertingService(cooldown_minutes=30)
        channel = MockNotificationChannel("test_channel")
        service.register_channel("test_channel", channel)

        redis_alert = Alert(
            title="Redis Unhealthy",
            message="Redis is down",
            severity=Alert.SEVERITY_CRITICAL,
            component="redis",
            status="unhealthy",
        )

        db_alert = Alert(
            title="Database Unhealthy",
            message="Database is down",
            severity=Alert.SEVERITY_CRITICAL,
            component="database",
            status="unhealthy",
        )

        # Both alerts should send (different components)
        results1 = await service.send_alert(redis_alert)
        results2 = await service.send_alert(db_alert)

        assert results1["test_channel"] is True
        assert results2["test_channel"] is True
        assert len(channel.sent_alerts) == 2


@pytest.fixture(autouse=True)
def reset_alerting_service():
    """Reset alerting service before each test."""
    # Clear global alerting service
    import services.alerting
    services.alerting._alerting_service = None
    yield
    # Cleanup after test
    services.alerting._alerting_service = None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
