"""
Unit Tests for SMS Service

This test module verifies the core SMS service functionality including
code generation, phone number validation, SMS sending, and error handling.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from services.sms_service import SMSService, get_sms_service
from twilio.base.exceptions import TwilioRestException


class TestSMSServiceInitialization:
    """Test suite for SMS service initialization."""

    def test_initialization_with_credentials(self):
        """Test SMS service initialization with Twilio credentials."""
        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        assert service.account_sid == "AC123456789abcdef"
        assert service.auth_token == "token123"
        assert service.phone_number == "+15551234567"
        assert service.enabled is True

    def test_initialization_without_credentials(self):
        """Test SMS service initialization without credentials is disabled."""
        service = SMSService(
            account_sid=None,
            auth_token=None,
            phone_number=None,
        )

        assert service.enabled is False

    def test_initialization_with_partial_credentials(self):
        """Test SMS service with partial credentials is disabled."""
        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token=None,
            phone_number="+15551234567",
        )

        assert service.enabled is False

    def test_initialization_with_custom_config(self):
        """Test SMS service initialization with custom configuration."""
        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
            code_length=8,
            code_ttl=600,
            max_attempts=5,
            cooldown_seconds=120,
        )

        assert service.code_length == 8
        assert service.code_ttl == 600
        assert service.max_attempts == 5
        assert service.cooldown_seconds == 120


class TestPhoneNumberNormalization:
    """Test suite for phone number normalization."""

    def test_normalize_valid_phone_number(self):
        """Test normalization of valid phone number."""
        service = SMSService()

        result = service._normalize_phone_number("+1 (555) 123-4567")

        assert result == "+15551234567"

    def test_normalize_phone_number_without_plus(self):
        """Test normalization adds plus prefix."""
        service = SMSService()

        result = service._normalize_phone_number("15551234567")

        assert result == "+15551234567"

    def test_normalize_phone_number_with_dashes(self):
        """Test normalization removes dashes."""
        service = SMSService()

        result = service._normalize_phone_number("+1-555-123-4567")

        assert result == "+15551234567"

    def test_normalize_phone_number_too_short(self):
        """Test that too short phone numbers return None."""
        service = SMSService()

        result = service._normalize_phone_number("+123456789")

        assert result is None

    def test_normalize_phone_number_too_long(self):
        """Test that too long phone numbers return None."""
        service = SMSService()

        result = service._normalize_phone_number("+1234567890123456")

        assert result is None

    def test_normalize_empty_phone_number(self):
        """Test that empty phone number returns None."""
        service = SMSService()

        result = service._normalize_phone_number("")

        assert result is None

    def test_normalize_phone_number_with_spaces(self):
        """Test normalization removes spaces."""
        service = SMSService()

        result = service._normalize_phone_number("+1 555 123 4567")

        assert result == "+15551234567"


class TestPhoneNumberMasking:
    """Test suite for phone number masking for logs."""

    def test_mask_phone_number_with_plus(self):
        """Test masking phone number with plus prefix."""
        service = SMSService()

        result = service._mask_phone_number("+15551234567")

        assert result == "+*******4567"

    def test_mask_phone_number_without_plus(self):
        """Test masking phone number without plus."""
        service = SMSService()

        result = service._mask_phone_number("15551234567")

        assert result == "*******4567"

    def test_mask_short_phone_number(self):
        """Test masking short phone number."""
        service = SMSService()

        result = service._mask_phone_number("4567")

        assert result == "4567"

    def test_mask_empty_phone_number(self):
        """Test masking empty phone number."""
        service = SMSService()

        result = service._mask_phone_number("")

        assert result == "None"

    def test_mask_none_phone_number(self):
        """Test masking None phone number."""
        service = SMSService()

        result = service._mask_phone_number(None)

        assert result == "None"


class TestCodeGeneration:
    """Test suite for verification code generation."""

    def test_generate_code_default_length(self):
        """Test code generation with default length."""
        service = SMSService(code_length=6)

        code = service.generate_code()

        assert len(code) == 6
        assert code.isdigit()

    def test_generate_code_custom_length(self):
        """Test code generation with custom length."""
        service = SMSService()

        # Test 4-digit code
        code = service.generate_code(length=4)
        assert len(code) == 4
        assert code.isdigit()

        # Test 8-digit code
        code = service.generate_code(length=8)
        assert len(code) == 8
        assert code.isdigit()

    def test_generate_code_invalid_length_too_short(self):
        """Test that too short length raises ValueError."""
        service = SMSService()

        with pytest.raises(ValueError) as exc_info:
            service.generate_code(length=3)

        assert "between 4 and 10" in str(exc_info.value).lower()

    def test_generate_code_invalid_length_too_long(self):
        """Test that too long length raises ValueError."""
        service = SMSService()

        with pytest.raises(ValueError) as exc_info:
            service.generate_code(length=15)

        assert "between 4 and 10" in str(exc_info.value).lower()

    def test_generate_code_unique(self):
        """Test that generated codes are unique."""
        service = SMSService()

        codes = [service.generate_code() for _ in range(100)]

        # With 6 digits (1,000,000 possible values),
        # 100 codes should all be unique
        assert len(set(codes)) == 100


class TestSMS sending:
    """Test suite for SMS sending functionality."""

    @patch('services.sms_service.Client')
    def test_send_verification_code_success(self, mock_client_class):
        """Test successful verification code sending."""
        # Setup mock
        mock_client = Mock()
        mock_message = Mock()
        mock_message.sid = "SM123456789"
        mock_message.status = "queued"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        result = service.send_verification_code("+15559876543", "123456")

        assert result["success"] is True
        assert result["sid"] == "SM123456789"
        assert result["status"] == "queued"
        assert result["error"] is None
        assert result["code"] == "123456"

    @patch('services.sms_service.Client')
    def test_send_verification_code_generates_code(self, mock_client_class):
        """Test that code is generated if not provided."""
        # Setup mock
        mock_client = Mock()
        mock_message = Mock()
        mock_message.sid = "SM123456789"
        mock_message.status = "queued"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        result = service.send_verification_code("+15559876543")

        assert result["success"] is True
        assert result["code"] is not None
        assert len(result["code"]) == 6
        assert result["code"].isdigit()

    @patch('services.sms_service.Client')
    def test_send_verification_code_disabled(self, mock_client_class):
        """Test that sending fails when service is disabled."""
        service = SMSService(
            account_sid=None,
            auth_token=None,
            phone_number=None,
        )

        result = service.send_verification_code("+15559876543", "123456")

        assert result["success"] is False
        assert result["error"] == "SMS sending is disabled"

    @patch('services.sms_service.Client')
    def test_send_verification_code_invalid_phone_number(self, mock_client_class):
        """Test that invalid phone number is rejected."""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        result = service.send_verification_code("invalid", "123456")

        assert result["success"] is False
        assert "invalid phone number" in result["error"].lower()

    @patch('services.sms_service.Client')
    def test_send_verification_code_twilio_error(self, mock_client_class):
        """Test handling of Twilio API errors."""
        # Setup mock to raise TwilioRestException
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        error = TwilioRestException(
            400,
            "http://twilio.com",
            msg="Invalid phone number",
            code=21614,
        )
        mock_client.messages.create.side_effect = error

        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        result = service.send_verification_code("+15559876543", "123456")

        assert result["success"] is False
        assert "twilio api error" in result["error"].lower()

    @patch('services.sms_service.Client')
    def test_send_verification_code_with_custom_message(self, mock_client_class):
        """Test sending verification code with custom message template."""
        # Setup mock
        mock_client = Mock()
        mock_message = Mock()
        mock_message.sid = "SM123456789"
        mock_message.status = "queued"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        result = service.send_verification_code(
            "+15559876543",
            "123456",
            message_template="Your code is: {code}. Don't share it!",
        )

        assert result["success"] is True
        # Verify the message was created with custom template
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert "Your code is: 123456. Don't share it!" in call_kwargs["body"]

    @patch('services.sms_service.Client')
    def test_send_verification_code_invalid_template(self, mock_client_class):
        """Test that invalid message template is handled."""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        result = service.send_verification_code(
            "+15559876543",
            "123456",
            message_template="Invalid template {missing_placeholder}",
        )

        assert result["success"] is False
        assert "invalid message template" in result["error"].lower()


class TestCustomMessageSending:
    """Test suite for custom message sending."""

    @patch('services.sms_service.Client')
    def test_send_message_success(self, mock_client_class):
        """Test successful custom message sending."""
        # Setup mock
        mock_client = Mock()
        mock_message = Mock()
        mock_message.sid = "SM123456789"
        mock_message.status = "queued"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        result = service.send_message("+15559876543", "Your account has been created.")

        assert result["success"] is True
        assert result["sid"] == "SM123456789"
        assert result["status"] == "queued"

    @patch('services.sms_service.Client')
    def test_send_message_disabled(self, mock_client_class):
        """Test that sending fails when service is disabled."""
        service = SMSService(
            account_sid=None,
            auth_token=None,
            phone_number=None,
        )

        result = service.send_message("+15559876543", "Test message")

        assert result["success"] is False
        assert result["error"] == "SMS sending is disabled"


class TestPhoneNumberValidation:
    """Test suite for phone number validation."""

    def test_validate_phone_number_valid(self):
        """Test validation of valid phone numbers."""
        service = SMSService()

        assert service.validate_phone_number("+15551234567") is True
        assert service.validate_phone_number("+44 20 7123 4567") is True
        assert service.validate_phone_number("15551234567") is True

    def test_validate_phone_number_invalid(self):
        """Test validation of invalid phone numbers."""
        service = SMSService()

        assert service.validate_phone_number("invalid") is False
        assert service.validate_phone_number("+1234") is False  # Too short
        assert service.validate_phone_number("") is False


class TestMessageStatus:
    """Test suite for message status checking."""

    @patch('services.sms_service.Client')
    def test_get_message_status_success(self, mock_client_class):
        """Test getting message status successfully."""
        # Setup mock
        mock_client = Mock()
        mock_message = Mock()
        mock_message.status = "delivered"
        mock_client.messages.return_value.fetch.return_value = mock_message
        mock_client_class.return_value = mock_client

        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        result = service.get_message_status("SM123456789")

        assert result["sid"] == "SM123456789"
        assert result["status"] == "delivered"
        assert result["error"] is None

    @patch('services.sms_service.Client')
    def test_get_message_status_disabled(self, mock_client_class):
        """Test that status check fails when service is disabled."""
        service = SMSService(
            account_sid=None,
            auth_token=None,
            phone_number=None,
        )

        result = service.get_message_status("SM123456789")

        assert result["error"] == "SMS sending is disabled"

    @patch('services.sms_service.Client')
    def test_get_message_status_twilio_error(self, mock_client_class):
        """Test handling of Twilio API errors when getting status."""
        # Setup mock to raise TwilioRestException
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        error = TwilioRestException(
            404,
            "http://twilio.com",
            msg="Message not found",
            code=20404,
        )
        mock_client.messages.return_value.fetch.side_effect = error

        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        result = service.get_message_status("SM123456789")

        assert result["error"] is not None
        assert "twilio api error" in result["error"].lower()


class TestHealthCheck:
    """Test suite for SMS service health check."""

    @patch('services.sms_service.Client')
    def test_health_check_healthy(self, mock_client_class):
        """Test health check returns healthy status."""
        # Setup mock
        mock_client = Mock()
        mock_account = Mock()
        mock_client.api.accounts.return_value.fetch.return_value = mock_account
        mock_client_class.return_value = mock_client

        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        health = service.health_check()

        assert health["status"] == "healthy"
        assert health["enabled"] is True
        assert health["configured"] is True
        assert health["error"] is None

    def test_health_check_disabled(self):
        """Test health check when service is disabled."""
        service = SMSService(
            account_sid=None,
            auth_token=None,
            phone_number=None,
        )

        health = service.health_check()

        assert health["status"] == "unhealthy"
        assert health["enabled"] is False
        assert health["error"] == "SMS sending is disabled"

    def test_health_check_incomplete_config(self):
        """Test health check with incomplete configuration."""
        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token=None,
            phone_number="+15551234567",
        )

        health = service.health_check()

        assert health["status"] == "unhealthy"
        assert health["enabled"] is False
        assert "not configured" in health["error"].lower()

    @patch('services.sms_service.Client')
    def test_health_check_connection_error(self, mock_client_class):
        """Test health check with connection error."""
        # Setup mock to raise exception
        mock_client_class.side_effect = Exception("Connection error")

        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        health = service.health_check()

        assert health["status"] == "unhealthy"
        assert health["error"] is not None


class TestSingleton:
    """Test suite for singleton pattern."""

    def test_get_sms_service_singleton(self):
        """Test that get_sms_service returns singleton instance."""
        # Reset global service
        import services.sms_service
        services.sms_service._sms_service = None

        service1 = get_sms_service()
        service2 = get_sms_service()

        assert service1 is service2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch('services.sms_service.Client')
    def test_send_verification_code_empty_phone(self, mock_client_class):
        """Test sending to empty phone number."""
        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        result = service.send_verification_code("", "123456")

        assert result["success"] is False
        assert "invalid phone number" in result["error"].lower()

    @patch('services.sms_service.Client')
    def test_send_message_empty_message(self, mock_client_class):
        """Test sending empty message."""
        # Setup mock
        mock_client = Mock()
        mock_message = Mock()
        mock_message.sid = "SM123456789"
        mock_message.status = "queued"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        service = SMSService(
            account_sid="AC123456789abcdef",
            auth_token="token123",
            phone_number="+15551234567",
        )

        # Empty message should still work (Twilio handles it)
        result = service.send_message("+15559876543", "")

        assert result["success"] is True

    def test_normalize_phone_number_with_unicode(self):
        """Test normalization with unicode characters."""
        service = SMSService()

        # Unicode characters should be removed
        result = service._normalize_phone_number("+1â€ 555â€ 123â€ 4567")

        # After removing non-numeric except +
        assert result is not None
        assert result.startswith("+")
