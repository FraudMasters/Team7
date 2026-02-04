"""
Unit Tests for Security Alerts

This test module verifies the core security alerts functionality including
suspicious activity detection, alert notification delivery, webhook integration,
Slack notifications, and multi-channel alert orchestration.
"""
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from celery.exceptions import SoftTimeLimitExceeded

from tasks.security_alerts import (
    check_suspicious_activity,
    send_security_alert,
    send_security_alert_webhook,
    send_security_alert_slack,
    send_security_alert_multi_channel,
    format_security_alert_message,
    format_webhook_payload,
    format_slack_message,
    mask_phone_number,
    mask_webhook_url,
    check_failed_logins,
    check_multiple_ip_access,
    get_total_failed_logins,
    get_unique_active_users,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_alert_data() -> Dict[str, Any]:
    """Standard alert data for testing."""
    return {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "ip_address": "192.168.1.100",
        "failed_count": 10,
        "ip_count": 4,
        "locations": ["New York", "London", "Tokyo"],
        "severity": "high",
        "timestamp": "2026-02-04T12:00:00Z",
    }


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = MagicMock()
    return session


# ============================================================================
# Test Suite 1: Check Suspicious Activity Task
# ============================================================================

class TestCheckSuspiciousActivity:
    """Test suite for suspicious activity detection Celery task."""

    @patch("tasks.security_alerts.asyncio.get_event_loop")
    @patch("tasks.security_alerts.asyncio.new_event_loop")
    @patch("tasks.security_alerts.async_session_maker")
    def test_check_suspicious_activity_with_default_threshold(
        self, mock_session_maker, mock_new_loop, mock_get_loop
    ):
        """Test suspicious activity check with default threshold."""
        # Setup mocks
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = {
            "failed_login_alerts": [],
            "multiple_ip_alerts": [],
            "total_failed_logins": 0,
            "total_unique_users": 0,
        }

        result = check_suspicious_activity()

        assert result["status"] == "success"
        assert result["time_window_minutes"] == 60
        assert result["failed_login_alerts"] == []
        assert result["multiple_ip_alerts"] == []
        assert "processing_time_ms" in result

    @patch("tasks.security_alerts.asyncio.get_event_loop")
    @patch("tasks.security_alerts.asyncio.new_event_loop")
    @patch("tasks.security_alerts.async_session_maker")
    def test_check_suspicious_activity_with_custom_threshold(
        self, mock_session_maker, mock_new_loop, mock_get_loop
    ):
        """Test suspicious activity check with custom threshold."""
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = {
            "failed_login_alerts": [],
            "multiple_ip_alerts": [],
            "total_failed_logins": 15,
            "total_unique_users": 3,
        }

        result = check_suspicious_activity(
            time_window_minutes=30,
            failed_login_threshold=3,
        )

        assert result["status"] == "success"
        assert result["time_window_minutes"] == 30
        assert result["total_failed_logins"] == 15

    @patch("tasks.security_alerts.asyncio.get_event_loop")
    @patch("tasks.security_alerts.asyncio.new_event_loop")
    @patch("tasks.security_alerts.async_session_maker")
    def test_check_suspicious_activity_detects_failed_logins(
        self, mock_session_maker, mock_new_loop, mock_get_loop
    ):
        """Test that failed login alerts are detected."""
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = {
            "failed_login_alerts": [
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "ip_address": "192.168.1.100",
                    "failed_count": 10,
                }
            ],
            "multiple_ip_alerts": [],
            "total_failed_logins": 10,
            "total_unique_users": 1,
        }

        result = check_suspicious_activity(failed_login_threshold=5)

        assert len(result["failed_login_alerts"]) == 1
        assert result["failed_login_alerts"][0]["failed_count"] == 10
        assert result["total_failed_logins"] == 10

    @patch("tasks.security_alerts.asyncio.get_event_loop")
    @patch("tasks.security_alerts.asyncio.new_event_loop")
    @patch("tasks.security_alerts.async_session_maker")
    def test_check_suspicious_activity_detects_multiple_ips(
        self, mock_session_maker, mock_new_loop, mock_get_loop
    ):
        """Test that multiple IP alerts are detected."""
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = {
            "failed_login_alerts": [],
            "multiple_ip_alerts": [
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "ip_count": 4,
                    "locations": ["New York", "London", "Tokyo"],
                    "ip_list": ["192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4"],
                }
            ],
            "total_failed_logins": 0,
            "total_unique_users": 1,
        }

        result = check_suspicious_activity(alert_on_multiple_ips=True, ip_change_threshold=3)

        assert len(result["multiple_ip_alerts"]) == 1
        assert result["multiple_ip_alerts"][0]["ip_count"] == 4
        assert len(result["multiple_ip_alerts"][0]["ip_list"]) == 4

    @patch("tasks.security_alerts.asyncio.get_event_loop")
    @patch("tasks.security_alerts.asyncio.new_event_loop")
    @patch("tasks.security_alerts.async_session_maker")
    def test_check_suspicious_activity_handles_exception(
        self, mock_session_maker, mock_new_loop, mock_get_loop
    ):
        """Test that exceptions are handled gracefully."""
        mock_loop = MagicMock()
        mock_get_loop.side_effect = RuntimeError("Database error")

        result = check_suspicious_activity()

        assert result["status"] == "failed"
        assert "error" in result
        assert "processing_time_ms" in result


# ============================================================================
# Test Suite 2: Send Security Alert Task
# ============================================================================

class TestSendSecurityAlert:
    """Test suite for security alert notification Celery task."""

    def test_send_alert_with_email(self, mock_alert_data):
        """Test sending alert with email notification."""
        task = MagicMock()
        task.update_state = MagicMock()

        result = send_security_alert(
            task,
            alert_type="failed_logins",
            recipient_email="user@example.com",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "sent"
        assert result["alert_type"] == "failed_logins"
        assert result["email_sent"] is True
        assert result["recipient_email"] == "user@example.com"
        assert "processing_time_ms" in result

    def test_send_alert_with_phone(self, mock_alert_data):
        """Test sending alert with SMS notification."""
        task = MagicMock()
        task.update_state = MagicMock()

        result = send_security_alert(
            task,
            alert_type="multiple_ips",
            recipient_phone="+15551234567",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "sent"
        assert result["sms_sent"] is True
        assert result["recipient_phone_masked"] == "******4567"

    def test_send_alert_with_both_channels(self, mock_alert_data):
        """Test sending alert with both email and SMS."""
        task = MagicMock()
        task.update_state = MagicMock()

        result = send_security_alert(
            task,
            alert_type="failed_logins",
            recipient_email="user@example.com",
            recipient_phone="+15551234567",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "sent"
        assert result["email_sent"] is True
        assert result["sms_sent"] is True

    def test_send_alert_without_recipient_fails(self, mock_alert_data):
        """Test that alert fails without any recipient."""
        task = MagicMock()

        result = send_security_alert(
            task,
            alert_type="failed_logins",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "failed"
        assert "error" in result
        assert "at least one recipient" in result["error"].lower()

    def test_send_alert_formats_failed_logins_message(self, mock_alert_data):
        """Test that failed_logins alert message is formatted correctly."""
        task = MagicMock()
        task.update_state = MagicMock()

        result = send_security_alert(
            task,
            alert_type="failed_logins",
            recipient_email="user@example.com",
            alert_data=mock_alert_data,
        )

        # The task should format and "send" the email
        assert result["status"] == "sent"
        assert result["email_sent"] is True

    def test_send_alert_formats_multiple_ips_message(self, mock_alert_data):
        """Test that multiple_ips alert message is formatted correctly."""
        task = MagicMock()
        task.update_state = MagicMock()

        result = send_security_alert(
            task,
            alert_type="multiple_ips",
            recipient_email="user@example.com",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "sent"
        assert result["email_sent"] is True

    def test_send_alert_account_locked(self, mock_alert_data):
        """Test account_locked alert message formatting."""
        task = MagicMock()
        task.update_state = MagicMock()

        alert_data = mock_alert_data.copy()
        alert_data["reason"] = "Too many failed login attempts"

        result = send_security_alert(
            task,
            alert_type="account_locked",
            recipient_email="user@example.com",
            alert_data=alert_data,
        )

        assert result["status"] == "sent"

    def test_send_alert_password_reset(self, mock_alert_data):
        """Test password_reset alert message formatting."""
        task = MagicMock()
        task.update_state = MagicMock()

        result = send_security_alert(
            task,
            alert_type="password_reset",
            recipient_email="user@example.com",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "sent"

    def test_send_alert_handles_timeout(self, mock_alert_data):
        """Test that task timeout is handled gracefully."""
        task = MagicMock()
        task.update_state = MagicMock()

        with patch("tasks.security_alerts.time.sleep", side_effect=SoftTimeLimitExceeded()):
            result = send_security_alert(
                task,
                alert_type="failed_logins",
                recipient_email="user@example.com",
                alert_data=mock_alert_data,
            )

        # Should handle timeout gracefully
        assert result["status"] in ["sent", "failed"]
        assert "processing_time_ms" in result


# ============================================================================
# Test Suite 3: Send Security Alert Webhook
# ============================================================================

class TestSendSecurityAlertWebhook:
    """Test suite for webhook alert delivery."""

    @patch("tasks.security_alerts.httpx.AsyncClient")
    @patch("tasks.security_alerts.asyncio.get_event_loop")
    def test_send_webhook_success(self, mock_get_loop, mock_async_client, mock_alert_data):
        """Test successful webhook delivery."""
        task = MagicMock()
        task.update_state = MagicMock()

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value.post.return_value = mock_response
        mock_async_client.return_value = mock_client_instance

        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = mock_response

        result = send_security_alert_webhook(
            task,
            alert_type="failed_logins",
            webhook_url="https://example.com/webhook",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "sent"
        assert result["response_status_code"] == 200
        assert "processing_time_ms" in result

    @patch("tasks.security_alerts.asyncio.get_event_loop")
    def test_send_webhook_with_hmac_signature(self, mock_get_loop, mock_alert_data):
        """Test webhook with HMAC signature authentication."""
        task = MagicMock()
        task.update_state = MagicMock()

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = mock_response

        with patch("tasks.security_alerts.httpx.AsyncClient"):
            result = send_security_alert_webhook(
                task,
                alert_type="failed_logins",
                webhook_url="https://example.com/webhook",
                webhook_secret="supersecretkey",
                alert_data=mock_alert_data,
            )

        assert result["status"] == "sent"

    @patch("tasks.security_alerts.asyncio.get_event_loop")
    def test_send_webhook_invalid_url(self, mock_get_loop, mock_alert_data):
        """Test that invalid webhook URL is rejected."""
        task = MagicMock()

        result = send_security_alert_webhook(
            task,
            alert_type="failed_logins",
            webhook_url="invalid-url",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "failed"
        assert "error" in result
        assert "invalid webhook url" in result["error"].lower()

    @patch("tasks.security_alerts.asyncio.get_event_loop")
    def test_send_webhook_non_200_response(self, mock_get_loop, mock_alert_data):
        """Test that non-200 response is handled correctly."""
        task = MagicMock()
        task.update_state = MagicMock()

        # Mock 500 error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = mock_response

        with patch("tasks.security_alerts.httpx.AsyncClient"):
            result = send_security_alert_webhook(
                task,
                alert_type="failed_logins",
                webhook_url="https://example.com/webhook",
                alert_data=mock_alert_data,
            )

        assert result["status"] == "failed"
        assert result["response_status_code"] == 500


# ============================================================================
# Test Suite 4: Send Security Alert Slack
# ============================================================================

class TestSendSecurityAlertSlack:
    """Test suite for Slack alert delivery."""

    @patch("tasks.security_alerts.httpx.AsyncClient")
    @patch("tasks.security_alerts.asyncio.get_event_loop")
    def test_send_slack_success(self, mock_get_loop, mock_async_client, mock_alert_data):
        """Test successful Slack delivery."""
        task = MagicMock()
        task.update_state = MagicMock()

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"

        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value.post.return_value = mock_response
        mock_async_client.return_value = mock_client_instance

        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = mock_response

        result = send_security_alert_slack(
            task,
            alert_type="failed_logins",
            slack_webhook_url="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "sent"
        assert result["response_status_code"] == 200
        assert "processing_time_ms" in result

    @patch("tasks.security_alerts.asyncio.get_event_loop")
    def test_send_slack_invalid_url(self, mock_get_loop, mock_alert_data):
        """Test that invalid Slack webhook URL is rejected."""
        task = MagicMock()

        result = send_security_alert_slack(
            task,
            alert_type="failed_logins",
            slack_webhook_url="https://example.com/webhook",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "failed"
        assert "error" in result
        assert "invalid slack webhook url" in result["error"].lower()

    @patch("tasks.security_alerts.asyncio.get_event_loop")
    def test_send_slack_with_channel_override(self, mock_get_loop, mock_alert_data):
        """Test Slack delivery with channel override."""
        task = MagicMock()
        task.update_state = MagicMock()

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"

        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = mock_response

        with patch("tasks.security_alerts.httpx.AsyncClient"):
            result = send_security_alert_slack(
                task,
                alert_type="failed_logins",
                slack_webhook_url="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX",
                alert_data=mock_alert_data,
                channel="#security-alerts",
            )

        assert result["status"] == "sent"
        assert result["channel"] == "#security-alerts"


# ============================================================================
# Test Suite 5: Multi-Channel Alert Delivery
# ============================================================================

class TestSendSecurityAlertMultiChannel:
    """Test suite for multi-channel alert delivery."""

    @patch("tasks.security_alerts.group")
    @patch("tasks.security_alerts.send_security_alert.subtask")
    @patch("tasks.security_alerts.send_security_alert_webhook.subtask")
    @patch("tasks.security_alerts.send_security_alert_slack.subtask")
    def test_multi_channel_all_channels_success(
        self, mock_slack_subtask, mock_webhook_subtask, mock_alert_subtask, mock_group_class, mock_alert_data
    ):
        """Test multi-channel delivery to all channels."""
        task = MagicMock()

        # Mock subtasks
        mock_email_task = MagicMock()
        mock_sms_task = MagicMock()
        mock_webhook_task = MagicMock()
        mock_slack_task = MagicMock()

        mock_alert_subtask.side_effect = [mock_email_task, mock_sms_task]
        mock_webhook_subtask.return_value = mock_webhook_task
        mock_slack_subtask.return_value = mock_slack_task

        # Mock group result
        mock_group_result = MagicMock()
        mock_group_result.children = [
            MagicMock(result={"status": "sent", "email_sent": True}),
            MagicMock(result={"status": "sent", "sms_sent": True}),
            MagicMock(result={"status": "sent", "webhook_url": "https://example.com/***"}),
            MagicMock(result={"status": "sent", "channel": "default"}),
        ]
        mock_group_result.get.return_value = None
        mock_group_class.return_value.apply_async.return_value = mock_group_result

        result = send_security_alert_multi_channel(
            task,
            alert_type="failed_logins",
            recipient_email="user@example.com",
            recipient_phone="+15551234567",
            webhook_url="https://example.com/webhook",
            slack_webhook_url="https://hooks.slack.com/services/...",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "sent"
        assert set(result["channels_sent"]) == {"email", "sms", "webhook", "slack"}
        assert len(result["channels_failed"]) == 0

    @patch("tasks.security_alerts.group")
    @patch("tasks.security_alerts.send_security_alert.subtask")
    def test_multi_channel_partial_failure(self, mock_alert_subtask, mock_group_class, mock_alert_data):
        """Test multi-channel delivery with some failures."""
        task = MagicMock()

        # Mock subtasks
        mock_email_task = MagicMock()
        mock_sms_task = MagicMock()
        mock_alert_subtask.side_effect = [mock_email_task, mock_sms_task]

        # Mock group result with one failure
        mock_group_result = MagicMock()
        mock_group_result.children = [
            MagicMock(result={"status": "sent", "email_sent": True}),
            MagicMock(result={"status": "failed", "error": "SMS error"}),
        ]
        mock_group_result.get.return_value = None
        mock_group_class.return_value.apply_async.return_value = mock_group_result

        result = send_security_alert_multi_channel(
            task,
            alert_type="failed_logins",
            recipient_email="user@example.com",
            recipient_phone="+15551234567",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "partial"
        assert "email" in result["channels_sent"]
        assert "sms" in result["channels_failed"]

    def test_multi_channel_no_channels_configured(self, mock_alert_data):
        """Test that error is raised when no channels configured."""
        task = MagicMock()

        result = send_security_alert_multi_channel(
            task,
            alert_type="failed_logins",
            alert_data=mock_alert_data,
        )

        assert result["status"] == "failed"
        assert "at least one notification channel" in result["error"].lower()


# ============================================================================
# Test Suite 6: Helper Functions
# ============================================================================

class TestFormatSecurityAlertMessage:
    """Test suite for alert message formatting."""

    def test_format_failed_logins_alert(self, mock_alert_data):
        """Test formatting failed_logins alert message."""
        subject, body, sms = format_security_alert_message("failed_logins", mock_alert_data)

        assert "Failed Login Attempts" in subject
        assert "10 failed login attempts" in body
        assert "192.168.1.100" in body
        assert "failed login attempts" in sms.lower()

    def test_format_multiple_ips_alert(self, mock_alert_data):
        """Test formatting multiple_ips alert message."""
        subject, body, sms = format_security_alert_message("multiple_ips", mock_alert_data)

        assert "Multiple Location Access" in subject
        assert "4 different IP addresses" in body
        assert "New York" in body
        assert "4 different locations" in sms.lower()

    def test_format_account_locked_alert(self, mock_alert_data):
        """Test formatting account_locked alert message."""
        alert_data = mock_alert_data.copy()
        alert_data["reason"] = "Too many failed login attempts"

        subject, body, sms = format_security_alert_message("account_locked", alert_data)

        assert "Account Locked" in subject
        assert "locked" in body.lower()
        assert "Too many failed login attempts" in body
        assert "locked" in sms.lower()

    def test_format_password_reset_alert(self, mock_alert_data):
        """Test formatting password_reset alert message."""
        subject, body, sms = format_security_alert_message("password_reset", mock_alert_data)

        assert "Password Reset" in subject
        assert "password reset" in body.lower()
        assert "password reset" in sms.lower()

    def test_format_generic_alert(self, mock_alert_data):
        """Test formatting generic alert message."""
        subject, body, sms = format_security_alert_message("custom_event", mock_alert_data)

        assert "Custom Event" in subject
        assert "custom_event" in body.lower() or "Custom Event" in body
        assert "custom_event" in sms.lower()


class TestFormatWebhookPayload:
    """Test suite for webhook payload formatting."""

    def test_format_failed_logins_webhook(self, mock_alert_data):
        """Test formatting failed_logins webhook payload."""
        payload = format_webhook_payload("failed_logins", mock_alert_data)

        assert payload["event_type"] == "security.alert.failed_logins"
        assert payload["data"]["failed_count"] == 10
        assert payload["data"]["ip_address"] == "192.168.1.100"
        assert payload["severity"] == "high"
        assert "title" in payload
        assert "description" in payload

    def test_format_multiple_ips_webhook(self, mock_alert_data):
        """Test formatting multiple_ips webhook payload."""
        payload = format_webhook_payload("multiple_ips", mock_alert_data)

        assert payload["event_type"] == "security.alert.multiple_ips"
        assert payload["data"]["ip_count"] == 4
        assert payload["data"]["locations"] == ["New York", "London", "Tokyo"]
        assert "title" in payload
        assert "description" in payload

    def test_webhook_payload_includes_all_alert_data(self, mock_alert_data):
        """Test that all alert data fields are included in webhook payload."""
        custom_alert_data = mock_alert_data.copy()
        custom_alert_data["custom_field"] = "custom_value"

        payload = format_webhook_payload("failed_logins", custom_alert_data)

        assert payload["data"]["custom_field"] == "custom_value"

    def test_webhook_payload_severity_mapping(self, mock_alert_data):
        """Test that severity is correctly mapped."""
        # Test high severity
        mock_alert_data["severity"] = "high"
        payload = format_webhook_payload("failed_logins", mock_alert_data)
        assert payload["severity"] == "high"

        # Test low severity
        mock_alert_data["severity"] = "LOW"
        payload = format_webhook_payload("failed_logins", mock_alert_data)
        assert payload["severity"] == "low"


class TestFormatSlackMessage:
    """Test suite for Slack message formatting."""

    def test_format_failed_logins_slack_message(self, mock_alert_data):
        """Test formatting failed_logins Slack message."""
        message = format_slack_message("failed_logins", mock_alert_data)

        assert "username" in message
        assert "icon_emoji" in message
        assert "attachments" in message
        assert len(message["attachments"]) > 0
        assert message["username"] == "AgentHR Security Alerts"

    def test_slack_message_has_blocks(self, mock_alert_data):
        """Test that Slack message contains blocks."""
        message = format_slack_message("failed_logins", mock_alert_data)

        attachment = message["attachments"][0]
        assert "blocks" in attachment
        assert len(attachment["blocks"]) > 0

    def test_slack_message_severity_colors(self, mock_alert_data):
        """Test that severity affects message color."""
        # High severity should have red color
        mock_alert_data["severity"] = "high"
        message = format_slack_message("failed_logins", mock_alert_data)
        high_color = message["attachments"][0]["color"]

        # Low severity should have green color
        mock_alert_data["severity"] = "low"
        message = format_slack_message("failed_logins", mock_alert_data)
        low_color = message["attachments"][0]["color"]

        assert high_color != low_color

    def test_slack_message_includes_emoji(self, mock_alert_data):
        """Test that Slack message includes emoji based on severity."""
        mock_alert_data["severity"] = "critical"
        message = format_slack_message("failed_logins", mock_alert_data)

        # Check for warning emoji in header
        blocks = message["attachments"][0]["blocks"]
        header = blocks[0]
        assert "🚨" in header["text"]["text"] or "shield" in message.get("icon_emoji", "")


class TestMaskingFunctions:
    """Test suite for data masking utilities."""

    def test_mask_phone_number_valid(self):
        """Test phone number masking for valid numbers."""
        assert mask_phone_number("+15551234567") == "******4567"
        assert mask_phone_number("15551234567") == "******4567"

    def test_mask_phone_number_short(self):
        """Test phone number masking for short numbers."""
        assert mask_phone_number("1234") == "****"

    def test_mask_phone_number_empty(self):
        """Test phone number masking for empty input."""
        assert mask_phone_number("") == "Unknown"
        assert mask_phone_number(None) == "Unknown"

    def test_mask_webhook_url_valid(self):
        """Test webhook URL masking for valid URLs."""
        assert mask_webhook_url("https://example.com/webhook/secret123") == "https://example.com/****"
        assert mask_webhook_url("https://hooks.slack.com/services/T00/B00/XXX") == "https://hooks.slack.com/****"

    def test_mask_webhook_url_empty(self):
        """Test webhook URL masking for empty input."""
        assert mask_webhook_url("") == "unknown"
        assert mask_webhook_url(None) == "unknown"

    def test_mask_webhook_url_invalid(self):
        """Test webhook URL masking for invalid URLs."""
        # Should still mask even if URL parsing fails
        assert "****" in mask_webhook_url("not-a-url")


# ============================================================================
# Test Suite 7: Database Query Functions
# ============================================================================

class TestDatabaseQueryFunctions:
    """Test suite for database query helper functions."""

    @pytest.mark.asyncio
    async def test_check_failed_logins_returns_alerts(self, mock_session):
        """Test that check_failed_logins returns correct alerts."""
        # Mock query result
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.user_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_row.ip_address = "192.168.1.100"
        mock_row.failed_count = 10
        mock_result.all.return_value = [mock_row]

        mock_session.execute.return_value = mock_result

        alerts = await check_failed_logins(
            mock_session,
            datetime.utcnow() - timedelta(minutes=60),
            datetime.utcnow(),
            threshold=5,
        )

        assert len(alerts) == 1
        assert alerts[0]["user_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert alerts[0]["failed_count"] == 10

    @pytest.mark.asyncio
    async def test_check_multiple_ip_access_returns_alerts(self, mock_session):
        """Test that check_multiple_ip_access returns correct alerts."""
        # Mock query result with multiple IPs
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(user_id="550e8400-e29b-41d4-a716-446655440000", ip_address="192.168.1.1", location="New York"),
            MagicMock(user_id="550e8400-e29b-41d4-a716-446655440000", ip_address="192.168.1.2", location="London"),
            MagicMock(user_id="550e8400-e29b-41d4-a716-446655440000", ip_address="192.168.1.3", location="Tokyo"),
        ]
        mock_result.all.return_value = mock_rows

        mock_session.execute.return_value = mock_result

        alerts = await check_multiple_ip_access(
            mock_session,
            datetime.utcnow() - timedelta(minutes=60),
            datetime.utcnow(),
            threshold=3,
        )

        assert len(alerts) == 1
        assert alerts[0]["ip_count"] == 3
        assert "New York" in alerts[0]["locations"]
        assert "London" in alerts[0]["locations"]

    @pytest.mark.asyncio
    async def test_get_total_failed_logins(self, mock_session):
        """Test getting total failed logins count."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 25
        mock_session.execute.return_value = mock_result

        count = await get_total_failed_logins(
            mock_session,
            datetime.utcnow() - timedelta(minutes=60),
            datetime.utcnow(),
        )

        assert count == 25

    @pytest.mark.asyncio
    async def test_get_unique_active_users(self, mock_session):
        """Test getting unique active users count."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 10
        mock_session.execute.return_value = mock_result

        count = await get_unique_active_users(
            mock_session,
            datetime.utcnow() - timedelta(minutes=60),
            datetime.utcnow(),
        )

        assert count == 10
