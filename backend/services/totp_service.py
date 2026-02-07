"""
TOTP (Time-based One-Time Password) service for two-factor authentication.

This module provides TOTP generation and verification functionality for
implementing two-factor authentication (2FA) using authenticator apps
like Google Authenticator, Authy, or Microsoft Authenticator.

The TOTP service supports:
- Secure secret generation using Base32 encoding
- TOTP code generation and verification
- QR code provisioning URI generation for easy setup
- Backup code generation for recovery scenarios
- Configurable TOTP parameters (digits, period, algorithm)
- Time window validation to account for clock skew
- Security best practices for secret storage and handling

TOTP is an algorithm that computes a one-time password from a shared secret
and the current time, as defined in RFC 6238.
"""
import logging
import secrets
import string
from typing import Dict, List, Optional, Tuple

import pyotp
from pyotp import TOTP

from config import get_settings

logger = logging.getLogger(__name__)

# Global TOTP service instance
_totp_service: Optional["TOTPService"] = None


class TOTPService:
    """
    TOTP (Time-based One-Time Password) service for two-factor authentication.

    This class provides a high-level interface for TOTP operations with
    automatic configuration management, secure secret generation, and
    comprehensive error handling.

    Attributes:
        issuer: Issuer name for TOTP (appears in authenticator apps)
        digits: Number of digits in TOTP codes (typically 6 or 8)
        period: Time period for TOTP validity in seconds (typically 30)
        algorithm: Hash algorithm for TOTP (SHA1, SHA256, SHA512)
        backup_codes_count: Number of backup codes to generate

    Example:
        >>> totp = TOTPService()
        >>> secret = totp.generate_secret()
        >>> uri = totp.generate_provisioning_uri(secret, "user@example.com")
        >>> # User scans QR code from URI with authenticator app
        >>> code = "123456"  # Code from authenticator app
        >>> valid = totp.verify_code(secret, code)
        >>> print(valid)  # True if code matches
    """

    # Supported TOTP algorithms
    ALGORITHM_SHA1 = "SHA1"
    ALGORITHM_SHA256 = "SHA256"
    ALGORITHM_SHA512 = "SHA512"

    def __init__(
        self,
        issuer: Optional[str] = None,
        digits: Optional[int] = None,
        period: Optional[int] = None,
        algorithm: Optional[str] = None,
        backup_codes_count: Optional[int] = None,
    ) -> None:
        """
        Initialize the TOTP service with configuration.

        Args:
            issuer: Issuer name for TOTP (defaults to settings)
            digits: Number of digits in TOTP codes (defaults to settings)
            period: Time period for TOTP validity in seconds (defaults to settings)
            algorithm: Hash algorithm for TOTP (defaults to settings)
            backup_codes_count: Number of backup codes to generate (defaults to settings)
        """
        settings = get_settings()

        self.issuer = issuer or settings.totp_issuer
        self.digits = digits or settings.totp_digits
        self.period = period or settings.totp_period
        self.algorithm = algorithm or settings.totp_algorithm
        self.backup_codes_count = backup_codes_count or settings.totp_backup_codes_count

        logger.info(
            f"TOTPService initialized (issuer={self.issuer}, "
            f"digits={self.digits}, period={self.period}s, algorithm={self.algorithm})"
        )

    def generate_secret(self, length: int = 32) -> str:
        """
        Generate a secure random TOTP secret.

        The secret is encoded in Base32 format for compatibility with
        authenticator apps and TOTP libraries.

        Args:
            length: Number of random bytes to generate (default 32)

        Returns:
            Base32-encoded secret key

        Raises:
            ValueError: If length is not between 16 and 64

        Example:
            >>> totp = TOTPService()
            >>> secret = totp.generate_secret()
            >>> print(secret)  # Base32 string like 'JBSWY3DPEHPK3PXP'
        """
        if not 16 <= length <= 64:
            logger.error(f"Invalid secret length: {length}. Must be between 16 and 64.")
            raise ValueError("Secret length must be between 16 and 64 bytes")

        try:
            # Generate cryptographically secure random bytes
            random_bytes = secrets.token_bytes(length)

            # Encode as Base32 (uppercase, no padding)
            secret = pyotp.base64_to_base32(random_bytes) if hasattr(pyotp, 'base64_to_base32') else \
                     secrets.token_urlsafe(length).upper()[:32].replace('=', '').replace('-', 'X').replace('_', 'Y')

            # Ensure we have a valid Base32 string
            # Use pyotp's random_base32 function if available for better compatibility
            if hasattr(pyotp, 'random_base32'):
                secret = pyotp.random_base32(length=length)
            else:
                # Fallback: generate proper Base32
                secret = secrets.token_hex(length).upper()[:52]

            logger.debug(f"Generated TOTP secret (length={len(secret)})")
            return secret

        except Exception as e:
            logger.error(f"Error generating TOTP secret: {e}", exc_info=True)
            raise

    def verify_code(
        self,
        secret: str,
        code: str,
        valid_window: int = 1,
    ) -> bool:
        """
        Verify a TOTP code against a secret.

        This method validates the provided code and checks if it matches
        the expected TOTP value for the current time window. The valid_window
        parameter allows for clock skew between the client and server.

        Args:
            secret: Base32-encoded TOTP secret
            code: TOTP code to verify (6-8 digit string)
            valid_window: Number of time windows to check before/after (default 1)

        Returns:
            True if code is valid, False otherwise

        Example:
            >>> totp = TOTPService()
            >>> secret = totp.generate_secret()
            >>> # Get current code from authenticator app
            >>> code = "123456"
            >>> if totp.verify_code(secret, code):
            ...     print("Code is valid!")
        """
        if not secret:
            logger.error("Secret is required for TOTP verification")
            return False

        if not code:
            logger.error("Code is required for TOTP verification")
            return False

        # Clean code input (remove spaces, dashes, etc.)
        code = code.strip().replace(" ", "").replace("-", "")

        # Validate code format (must be digits only)
        if not code.isdigit():
            logger.warning(f"Invalid TOTP code format (not digits): {code[:3]}...")
            return False

        # Validate code length
        if len(code) != self.digits:
            logger.warning(
                f"Invalid TOTP code length: {len(code)} (expected {self.digits})"
            )
            return False

        try:
            # Create TOTP object with secret and configuration
            totp = TOTP(
                secret,
                digits=self.digits,
                period=self.period,
                digest=self._get_digest(),
            )

            # Verify code with time window to account for clock skew
            # valid_window=1 means check current, previous, and next time windows
            is_valid = totp.verify(code, valid_window=valid_window)

            if is_valid:
                logger.debug("TOTP code verified successfully")
            else:
                logger.warning("TOTP code verification failed")

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying TOTP code: {e}", exc_info=True)
            return False

    def generate_provisioning_uri(
        self,
        secret: str,
        identifier: str,
        name: Optional[str] = None,
    ) -> str:
        """
        Generate a provisioning URI for QR code registration.

        The provisioning URI is used to generate a QR code that users can
        scan with their authenticator app (Google Authenticator, Authy, etc.)
        to automatically configure the TOTP secret.

        URI format: otpauth://totp/ISSUER:IDENTIFIER?secret=SECRET&issuer=ISSUER&...

        Args:
            secret: Base32-encoded TOTP secret
            identifier: User identifier (email, username, etc.)
            name: Optional display name (defaults to identifier)

        Returns:
            Provisioning URI string (for QR code generation)

        Raises:
            ValueError: If secret or identifier is empty

        Example:
            >>> totp = TOTPService()
            >>> secret = totp.generate_secret()
            >>> uri = totp.generate_provisioning_uri(
            ...     secret,
            ...     "user@example.com",
            ...     "John Doe"
            ... )
            >>> # Generate QR code from URI
            >>> import qrcode
            >>> qrcode.make(uri)
        """
        if not secret:
            logger.error("Secret is required for provisioning URI")
            raise ValueError("TOTP secret cannot be empty")

        if not identifier:
            logger.error("Identifier is required for provisioning URI")
            raise ValueError("Identifier cannot be empty")

        try:
            # Create TOTP object
            totp = TOTP(
                secret,
                digits=self.digits,
                period=self.period,
                digest=self._get_digest(),
            )

            # Generate provisioning URI
            # Format: otpauth://totp/ISSUER:IDENTIFIER?secret=SECRET&issuer=ISSUER
            display_name = name or identifier
            uri = totp.provisioning_uri(
                name=identifier,
                issuer_name=self.issuer,
            )

            logger.debug(f"Generated provisioning URI for: {identifier}")
            return uri

        except Exception as e:
            logger.error(f"Error generating provisioning URI: {e}", exc_info=True)
            raise

    def generate_backup_codes(self, count: Optional[int] = None) -> List[str]:
        """
        Generate secure backup codes for account recovery.

        Backup codes are one-time use codes that users can save and use
        to access their account if they lose access to their authenticator app.
        Each code can only be used once.

        Args:
            count: Number of backup codes to generate (defaults to instance setting)

        Returns:
            List of backup code strings

        Example:
            >>> totp = TOTPService()
            >>> codes = totp.generate_backup_codes()
            >>> print(f"Save these codes: {codes}")
            >>> # User stores codes securely for recovery
        """
        if count is None:
            count = self.backup_codes_count

        if not 5 <= count <= 20:
            logger.error(f"Invalid backup codes count: {count}. Must be between 5 and 20.")
            raise ValueError("Backup codes count must be between 5 and 20")

        try:
            codes = []

            # Generate unique backup codes
            for i in range(count):
                # Generate a 12-character code with hyphens for readability
                # Format: XXXX-XXXX-XXXX
                code_parts = []
                for _ in range(3):
                    # Generate 4 random characters (uppercase letters and digits)
                    part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
                    code_parts.append(part)
                code = '-'.join(code_parts)
                codes.append(code)

            logger.info(f"Generated {len(codes)} backup codes")
            return codes

        except Exception as e:
            logger.error(f"Error generating backup codes: {e}", exc_info=True)
            raise

    def validate_backup_code_format(self, code: str) -> bool:
        """
        Validate the format of a backup code.

        Args:
            code: Backup code string to validate

        Returns:
            True if format is valid, False otherwise

        Example:
            >>> totp = TOTPService()
            >>> totp.validate_backup_code_format("AB12-CD34-EF56")
            True
            >>> totp.validate_backup_code_format("invalid")
            False
        """
        if not code:
            return False

        # Check format: XXXX-XXXX-XXXX (uppercase letters and digits)
        parts = code.split('-')
        if len(parts) != 3:
            return False

        for part in parts:
            if len(part) != 4:
                return False
            if not all(c in string.ascii_uppercase + string.digits for c in part):
                return False

        return True

    def get_current_code(self, secret: str) -> str:
        """
        Get the current TOTP code for a secret (for testing/debugging).

        WARNING: This method should only be used for testing or debugging
        purposes. Never expose TOTP codes in production logs or responses.

        Args:
            secret: Base32-encoded TOTP secret

        Returns:
            Current TOTP code

        Raises:
            ValueError: If secret is empty

        Example:
            >>> totp = TOTPService()
            >>> secret = totp.generate_secret()
            >>> current_code = totp.get_current_code(secret)
            >>> print(f"Current code (for testing): {current_code}")
        """
        if not secret:
            logger.error("Secret is required to get current code")
            raise ValueError("TOTP secret cannot be empty")

        try:
            totp = TOTP(
                secret,
                digits=self.digits,
                period=self.period,
                digest=self._get_digest(),
            )

            code = totp.now()
            logger.debug("Generated current TOTP code (for testing)")

            return code

        except Exception as e:
            logger.error(f"Error getting current TOTP code: {e}", exc_info=True)
            raise

    def _get_digest(self) -> object:
        """
        Get the hash digest function for TOTP.

        Returns:
            Hash function from hashlib for the configured algorithm

        Raises:
            ValueError: If algorithm is not supported
        """
        import hashlib

        algorithm_map = {
            "SHA1": hashlib.sha1,
            "SHA256": hashlib.sha256,
            "SHA512": hashlib.sha512,
        }

        digest = algorithm_map.get(self.algorithm.upper())

        if digest is None:
            logger.error(f"Unsupported TOTP algorithm: {self.algorithm}")
            raise ValueError(
                f"Unsupported algorithm: {self.algorithm}. "
                f"Supported: SHA1, SHA256, SHA512"
            )

        return digest

    def health_check(self) -> Dict[str, any]:
        """
        Check TOTP service health and configuration.

        Returns:
            Dictionary with health status and configuration info

        Example:
            >>> totp = TOTPService()
            >>> health = totp.health_check()
            >>> print(health)
            {'status': 'healthy', 'issuer': 'AgentHR', ...}
        """
        result = {
            "status": "healthy",
            "configured": True,
            "issuer": self.issuer,
            "digits": self.digits,
            "period": self.period,
            "algorithm": self.algorithm,
            "backup_codes_count": self.backup_codes_count,
            "error": None,
        }

        try:
            # Test secret generation
            test_secret = self.generate_secret()
            if not test_secret or len(test_secret) < 16:
                raise ValueError("Secret generation failed")

            # Test code verification
            test_code = self.get_current_code(test_secret)
            if not self.verify_code(test_secret, test_code):
                raise ValueError("Code verification failed")

            logger.debug("TOTP service health check passed")

        except Exception as e:
            result["status"] = "unhealthy"
            result["error"] = str(e)
            logger.error(f"TOTP service health check failed: {e}")

        return result


def get_totp_service() -> TOTPService:
    """
    Get or create global TOTP service instance.

    Returns:
        Global TOTPService instance

    Example:
        >>> totp = get_totp_service()
        >>> secret = totp.generate_secret()
    """
    global _totp_service
    if _totp_service is None:
        _totp_service = TOTPService()
    return _totp_service
