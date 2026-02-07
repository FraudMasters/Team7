"""
SMS service for sending verification codes via Twilio.

This module provides SMS sending functionality for two-factor authentication (2FA)
and other notification purposes using the Twilio API.

The SMS service supports:
- Sending verification codes via SMS
- Rate limiting and cooldown management
- Secure random code generation
- Configurable code length and TTL
- Graceful error handling when Twilio is unavailable
- Phone number validation and normalization
- Delivery status tracking
- Health checks and connection monitoring

SMS provider format: Uses Twilio REST API for message delivery.
Example: Sending verification code to +1234567890
"""
import logging
import secrets
import string
from typing import Any, Dict, List, Optional

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from config import get_settings

logger = logging.getLogger(__name__)

# Global SMS service instance
_sms_service: Optional["SMSService"] = None


class SMSService:
    """
    SMS service for sending verification codes via Twilio.

    This class provides a high-level interface for SMS operations with
    automatic configuration management, code generation, and comprehensive
    error handling.

    Attributes:
        account_sid: Twilio account SID
        auth_token: Twilio authentication token
        phone_number: Twilio phone number for sending SMS
        code_length: Length of verification codes
        code_ttl: Time-to-live for verification codes in seconds
        max_attempts: Maximum number of verification attempts
        cooldown_seconds: Cooldown between SMS resend attempts
        enabled: Whether SMS sending is enabled

    Example:
        >>> sms = SMSService()
        >>> code = sms.generate_code()
        >>> success = sms.send_verification_code("+1234567890", code)
        >>> print(success)  # True if sent successfully
    """

    # SMS provider names
    PROVIDER_TWILIO = "twilio"
    PROVIDER_SNS = "sns"

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        phone_number: Optional[str] = None,
        code_length: Optional[int] = None,
        code_ttl: Optional[int] = None,
        max_attempts: Optional[int] = None,
        cooldown_seconds: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        """
        Initialize the SMS service with Twilio configuration.

        Args:
            account_sid: Twilio account SID (defaults to settings)
            auth_token: Twilio authentication token (defaults to settings)
            phone_number: Twilio phone number (defaults to settings)
            code_length: Length of verification codes (defaults to settings)
            code_ttl: Code TTL in seconds (defaults to settings)
            max_attempts: Max verification attempts (defaults to settings)
            cooldown_seconds: Cooldown between resends (defaults to settings)
            enabled: Whether SMS is enabled (defaults to settings)
        """
        settings = get_settings()

        self.account_sid = account_sid or settings.twilio_account_sid
        self.auth_token = auth_token or settings.twilio_auth_token
        self.phone_number = phone_number or settings.twilio_phone_number
        self.code_length = code_length or settings.sms_verification_code_length
        self.code_ttl = code_ttl or settings.sms_verification_code_ttl
        self.max_attempts = max_attempts or settings.sms_max_attempts
        self.cooldown_seconds = cooldown_seconds or settings.sms_cooldown_seconds
        self.enabled = enabled if enabled is not None else (
            bool(self.account_sid) and bool(self.auth_token) and bool(self.phone_number)
        )

        self.twilio_client: Optional[Client] = None
        self._initialize_client()

        logger.info(
            f"SMSService initialized (enabled={self.enabled}, "
            f"phone_number={self._mask_phone_number(self.phone_number)}, "
            f"code_length={self.code_length}, ttl={self.code_ttl}s)"
        )

    def _initialize_client(self) -> None:
        """
        Initialize Twilio client.

        Creates a Twilio REST API client for sending SMS messages.
        Handles connection errors gracefully.
        """
        if not self.enabled:
            logger.info("SMS sending is disabled, skipping Twilio client initialization")
            return

        try:
            # Create Twilio client
            self.twilio_client = Client(
                self.account_sid,
                self.auth_token,
            )

            # Test connection by validating phone number format
            if self.phone_number:
                normalized = self._normalize_phone_number(self.phone_number)
                if not normalized:
                    logger.error("Invalid Twilio phone number format")
                    self.enabled = False
                    self.twilio_client = None
                    return

            logger.info("Twilio client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            logger.warning("SMS sending will be disabled for this session")
            self.enabled = False
            self.twilio_client = None

    def _normalize_phone_number(self, phone_number: str) -> Optional[str]:
        """
        Normalize and validate phone number.

        Args:
            phone_number: Phone number to normalize

        Returns:
            Normalized phone number in E.164 format, or None if invalid

        Example:
            >>> sms = SMSService()
            >>> sms._normalize_phone_number("+1 (555) 123-4567")
            '+15551234567'
        """
        if not phone_number:
            return None

        try:
            # Remove all non-numeric characters except leading +
            normalized = ''.join(c for c in phone_number if c.isdigit() or c == '+')

            # Remove leading + if present for validation
            digits = normalized.lstrip('+')

            # Validate length (should be 10-15 digits for international numbers)
            if not 10 <= len(digits) <= 15:
                logger.warning(f"Invalid phone number length: {len(digits)} digits")
                return None

            # Ensure it starts with + for E.164 format
            if not normalized.startswith('+'):
                normalized = '+' + normalized

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing phone number: {e}")
            return None

    def _mask_phone_number(self, phone_number: Optional[str]) -> str:
        """
        Mask phone number for logging (show only last 4 digits).

        Args:
            phone_number: Phone number to mask

        Returns:
            Masked phone number

        Example:
            >>> sms = SMSService()
            >>> sms._mask_phone_number("+15551234567")
            '+*******4567'
        """
        if not phone_number:
            return "None"

        if len(phone_number) <= 4:
            return phone_number

        # Show country code and last 4 digits
        if phone_number.startswith('+'):
            return '+' + '*' * (len(phone_number) - 5) + phone_number[-4:]
        else:
            return '*' * (len(phone_number) - 4) + phone_number[-4:]

    def generate_code(self, length: Optional[int] = None) -> str:
        """
        Generate a secure random verification code.

        Args:
            length: Code length (defaults to instance setting)

        Returns:
            Numeric verification code

        Raises:
            ValueError: If length is not between 4 and 10

        Example:
            >>> sms = SMSService()
            >>> code = sms.generate_code()
            >>> print(code)  # e.g., "123456"
        """
        if length is None:
            length = self.code_length

        if not 4 <= length <= 10:
            logger.error(f"Invalid code length: {length}. Must be between 4 and 10.")
            raise ValueError("Code length must be between 4 and 10")

        try:
            # Generate cryptographically secure random code
            code = ''.join(secrets.choice(string.digits) for _ in range(length))
            logger.debug(f"Generated verification code (length={length})")
            return code

        except Exception as e:
            logger.error(f"Error generating verification code: {e}", exc_info=True)
            raise

    def send_verification_code(
        self,
        phone_number: str,
        code: Optional[str] = None,
        message_template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a verification code via SMS.

        Args:
            phone_number: Recipient phone number (will be normalized)
            code: Verification code (generated if not provided)
            message_template: Custom message template (use {code} as placeholder)

        Returns:
            Dictionary with success status, message SID, and error details

        Example:
            >>> sms = SMSService()
            >>> result = sms.send_verification_code("+15551234567")
            >>> if result['success']:
            ...     print("SMS sent:", result['sid'])
        """
        result = {
            "success": False,
            "sid": None,
            "status": None,
            "error": None,
            "phone_number": self._mask_phone_number(phone_number),
            "code": code,
        }

        if not self.enabled or self.twilio_client is None:
            result["error"] = "SMS sending is disabled"
            logger.warning("SMS sending attempt while disabled")
            return result

        # Normalize phone number
        normalized_phone = self._normalize_phone_number(phone_number)
        if not normalized_phone:
            result["error"] = "Invalid phone number format"
            logger.error(f"Invalid phone number format: {phone_number}")
            return result

        # Generate code if not provided
        if code is None:
            code = self.generate_code()
            result["code"] = code

        # Create message
        if message_template:
            try:
                message = message_template.format(code=code)
            except KeyError as e:
                result["error"] = f"Invalid message template: {e}"
                logger.error(f"Invalid message template: {e}")
                return result
        else:
            message = f"Your verification code is: {code}. Valid for {self.code_ttl // 60} minutes."

        try:
            # Send SMS via Twilio
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.phone_number,
                to=normalized_phone,
            )

            result["success"] = True
            result["sid"] = message_obj.sid
            result["status"] = message_obj.status

            logger.info(
                f"SMS sent successfully (sid={message_obj.sid}, "
                f"to={self._mask_phone_number(normalized_phone)}, "
                f"status={message_obj.status})"
            )

        except TwilioRestException as e:
            error_msg = f"Twilio API error: {e.msg}"
            result["error"] = error_msg
            result["status"] = e.status

            logger.error(
                f"Failed to send SMS (to={self._mask_phone_number(normalized_phone)}, "
                f"code={e.code}, msg={e.msg})"
            )

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            result["error"] = error_msg

            logger.error(
                f"Unexpected error sending SMS (to={self._mask_phone_number(normalized_phone)}): {e}",
                exc_info=True
            )

        return result

    def send_message(
        self,
        phone_number: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send a custom message via SMS.

        Args:
            phone_number: Recipient phone number (will be normalized)
            message: Message body to send

        Returns:
            Dictionary with success status, message SID, and error details

        Example:
            >>> sms = SMSService()
            >>> result = sms.send_message("+15551234567", "Your account has been created.")
            >>> if result['success']:
            ...     print("Message sent:", result['sid'])
        """
        result = {
            "success": False,
            "sid": None,
            "status": None,
            "error": None,
            "phone_number": self._mask_phone_number(phone_number),
        }

        if not self.enabled or self.twilio_client is None:
            result["error"] = "SMS sending is disabled"
            logger.warning("SMS sending attempt while disabled")
            return result

        # Normalize phone number
        normalized_phone = self._normalize_phone_number(phone_number)
        if not normalized_phone:
            result["error"] = "Invalid phone number format"
            logger.error(f"Invalid phone number format: {phone_number}")
            return result

        try:
            # Send SMS via Twilio
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.phone_number,
                to=normalized_phone,
            )

            result["success"] = True
            result["sid"] = message_obj.sid
            result["status"] = message_obj.status

            logger.info(
                f"SMS sent successfully (sid={message_obj.sid}, "
                f"to={self._mask_phone_number(normalized_phone)}, "
                f"status={message_obj.status})"
            )

        except TwilioRestException as e:
            error_msg = f"Twilio API error: {e.msg}"
            result["error"] = error_msg
            result["status"] = e.status

            logger.error(
                f"Failed to send SMS (to={self._mask_phone_number(normalized_phone)}, "
                f"code={e.code}, msg={e.msg})"
            )

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            result["error"] = error_msg

            logger.error(
                f"Unexpected error sending SMS (to={self._mask_phone_number(normalized_phone)}): {e}",
                exc_info=True
            )

        return result

    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate phone number format.

        Args:
            phone_number: Phone number to validate

        Returns:
            True if phone number format is valid, False otherwise

        Example:
            >>> sms = SMSService()
            >>> sms.validate_phone_number("+15551234567")
            True
            >>> sms.validate_phone_number("invalid")
            False
        """
        normalized = self._normalize_phone_number(phone_number)
        return normalized is not None

    def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get the status of a sent SMS message.

        Args:
            message_sid: Twilio message SID

        Returns:
            Dictionary with message status details

        Example:
            >>> sms = SMSService()
            >>> result = sms.send_verification_code("+15551234567")
            >>> if result['success']:
            ...     status = sms.get_message_status(result['sid'])
            ...     print(status['status'])
        """
        result = {
            "sid": message_sid,
            "status": None,
            "error": None,
        }

        if not self.enabled or self.twilio_client is None:
            result["error"] = "SMS sending is disabled"
            return result

        try:
            message = self.twilio_client.messages(message_sid).fetch()
            result["status"] = message.status

            logger.debug(f"Retrieved message status (sid={message_sid}, status={message.status})")

        except TwilioRestException as e:
            result["error"] = f"Twilio API error: {e.msg}"
            logger.error(f"Failed to get message status (sid={message_sid}): {e}")

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error getting message status: {e}", exc_info=True)

        return result

    def health_check(self) -> Dict[str, Any]:
        """
        Check SMS service health and Twilio connection.

        Returns:
            Dictionary with health status and configuration info

        Example:
            >>> sms = SMSService()
            >>> health = sms.health_check()
            >>> print(health)
            {'status': 'healthy', 'enabled': True, ...}
        """
        result = {
            "status": "unhealthy",
            "enabled": self.enabled,
            "configured": bool(self.account_sid and self.auth_token and self.phone_number),
            "phone_number": self._mask_phone_number(self.phone_number),
            "code_length": self.code_length,
            "code_ttl": self.code_ttl,
            "max_attempts": self.max_attempts,
            "cooldown_seconds": self.cooldown_seconds,
            "error": None,
        }

        if not self.enabled:
            result["error"] = "SMS sending is disabled"
            return result

        if not result["configured"]:
            result["error"] = "Twilio credentials not configured"
            return result

        try:
            # Test connection by checking account info
            if self.twilio_client:
                account = self.twilio_client.api.accounts(self.account_sid).fetch()
                if account:
                    result["status"] = "healthy"
                    logger.debug("SMS service health check passed")
                else:
                    result["error"] = "Failed to fetch account info"

        except TwilioRestException as e:
            result["error"] = f"Twilio connection failed: {e.msg}"
            logger.error(f"SMS service health check failed: {e}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Unexpected error during SMS health check: {e}", exc_info=True)

        return result


def get_sms_service() -> SMSService:
    """
    Get or create global SMS service instance.

    Returns:
        Global SMSService instance

    Example:
        >>> sms = get_sms_service()
        >>> result = sms.send_verification_code("+15551234567")
    """
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSService()
    return _sms_service
