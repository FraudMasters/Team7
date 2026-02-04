"""
Unit Tests for TOTP Service

This test module verifies the core TOTP functionality including
secret generation, code verification, provisioning URI generation,
and backup code generation.
"""
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

from services.totp_service import TOTPService, get_totp_service
import pyotp


class TestTOTPServiceInitialization:
    """Test suite for TOTP service initialization."""

    def test_initialization_with_defaults(self):
        """Test TOTP service initialization with default settings."""
        service = TOTPService()

        assert service.issuer == "AgentHR"
        assert service.digits == 6
        assert service.period == 30
        assert service.algorithm == "SHA1"
        assert service.backup_codes_count == 10

    def test_initialization_with_custom_config(self):
        """Test TOTP service initialization with custom configuration."""
        service = TOTPService(
            issuer="CustomApp",
            digits=8,
            period=60,
            algorithm="SHA256",
            backup_codes_count=15,
        )

        assert service.issuer == "CustomApp"
        assert service.digits == 8
        assert service.period == 60
        assert service.algorithm == "SHA256"
        assert service.backup_codes_count == 15

    def test_initialization_with_sha512(self):
        """Test TOTP service initialization with SHA512 algorithm."""
        service = TOTPService(algorithm="SHA512")

        assert service.algorithm == "SHA512"
        assert service._get_digest() is not None


class TestSecretGeneration:
    """Test suite for TOTP secret generation."""

    def test_generate_secret_default_length(self):
        """Test secret generation with default length."""
        service = TOTPService()
        secret = service.generate_secret()

        assert secret is not None
        assert len(secret) >= 16
        assert isinstance(secret, str)

    def test_generate_secret_custom_length(self):
        """Test secret generation with custom length."""
        service = TOTPService()

        # Test minimum length
        secret = service.generate_secret(length=16)
        assert len(secret) >= 16

        # Test maximum length
        secret = service.generate_secret(length=64)
        assert len(secret) >= 64

    def test_generate_secret_invalid_length_too_short(self):
        """Test that invalid length raises ValueError."""
        service = TOTPService()

        with pytest.raises(ValueError) as exc_info:
            service.generate_secret(length=8)

        assert "between 16 and 64" in str(exc_info.value).lower()

    def test_generate_secret_invalid_length_too_long(self):
        """Test that invalid length raises ValueError."""
        service = TOTPService()

        with pytest.raises(ValueError) as exc_info:
            service.generate_secret(length=100)

        assert "between 16 and 64" in str(exc_info.value).lower()

    def test_generate_secret_unique(self):
        """Test that generated secrets are unique."""
        service = TOTPService()

        secrets = [service.generate_secret() for _ in range(100)]

        # All secrets should be unique
        assert len(set(secrets)) == 100


class TestCodeVerification:
    """Test suite for TOTP code verification."""

    def test_verify_code_valid_current(self):
        """Test verification with current valid code."""
        service = TOTPService()
        secret = service.generate_secret()

        # Get current valid code
        totp = pyotp.TOTP(secret, digits=6, period=30)
        current_code = totp.now()

        assert service.verify_code(secret, current_code) is True

    def test_verify_code_invalid(self):
        """Test verification with invalid code."""
        service = TOTPService()
        secret = service.generate_secret()

        assert service.verify_code(secret, "000000") is False
        assert service.verify_code(secret, "123456") is False
        assert service.verify_code(secret, "invalid") is False

    def test_verify_code_with_time_window(self):
        """Test verification with time window for clock skew."""
        service = TOTPService()
        secret = service.generate_secret()

        # Get current valid code
        totp = pyotp.TOTP(secret, digits=6, period=30)
        current_code = totp.now()

        # Verify with different time windows
        assert service.verify_code(secret, current_code, valid_window=0) is True
        assert service.verify_code(secret, current_code, valid_window=1) is True
        assert service.verify_code(secret, current_code, valid_window=2) is True

    def test_verify_code_empty_secret(self):
        """Test verification fails with empty secret."""
        service = TOTPService()

        assert service.verify_code("", "123456") is False

    def test_verify_code_empty_code(self):
        """Test verification fails with empty code."""
        service = TOTPService()
        secret = service.generate_secret()

        assert service.verify_code(secret, "") is False

    def test_verify_code_invalid_format(self):
        """Test verification fails with non-digit code."""
        service = TOTPService()
        secret = service.generate_secret()

        assert service.verify_code(secret, "abcdef") is False
        assert service.verify_code(secret, "12-34-56") is False

    def test_verify_code_invalid_length(self):
        """Test verification fails with wrong length code."""
        service = TOTPService(digits=6)
        secret = service.generate_secret()

        # Too short
        assert service.verify_code(secret, "12345") is False

        # Too long
        assert service.verify_code(secret, "1234567") is False

    def test_verify_code_with_whitespace(self):
        """Test verification handles whitespace correctly."""
        service = TOTPService()
        secret = service.generate_secret()

        totp = pyotp.TOTP(secret, digits=6, period=30)
        current_code = totp.now()

        # Should handle whitespace
        assert service.verify_code(secret, f" {current_code} ") is True
        assert service.verify_code(secret, f"{current_code[:3]} {current_code[3:]}") is True

    def test_verify_code_with_8_digits(self):
        """Test verification with 8-digit codes."""
        service = TOTPService(digits=8)
        secret = service.generate_secret()

        totp = pyotp.TOTP(secret, digits=8, period=30)
        current_code = totp.now()

        assert service.verify_code(secret, current_code) is True


class TestProvisioningURI:
    """Test suite for provisioning URI generation."""

    def test_generate_provisioning_uri_basic(self):
        """Test basic provisioning URI generation."""
        service = TOTPService()
        secret = service.generate_secret()

        uri = service.generate_provisioning_uri(
            secret=secret,
            identifier="test@example.com",
        )

        assert uri is not None
        assert "otpauth://totp/" in uri
        assert "test@example.com" in uri
        assert secret in uri
        assert "AgentHR" in uri

    def test_generate_provisioning_uri_with_name(self):
        """Test provisioning URI with custom name."""
        service = TOTPService()
        secret = service.generate_secret()

        uri = service.generate_provisioning_uri(
            secret=secret,
            identifier="test@example.com",
            name="John Doe",
        )

        assert "test@example.com" in uri

    def test_generate_provisioning_uri_custom_issuer(self):
        """Test provisioning URI with custom issuer."""
        service = TOTPService(issuer="CustomApp")
        secret = service.generate_secret()

        uri = service.generate_provisioning_uri(
            secret=secret,
            identifier="test@example.com",
        )

        assert "CustomApp" in uri

    def test_generate_provisioning_uri_empty_secret(self):
        """Test that empty secret raises ValueError."""
        service = TOTPService()

        with pytest.raises(ValueError) as exc_info:
            service.generate_provisioning_uri(
                secret="",
                identifier="test@example.com",
            )

        assert "empty" in str(exc_info.value).lower()

    def test_generate_provisioning_uri_empty_identifier(self):
        """Test that empty identifier raises ValueError."""
        service = TOTPService()
        secret = service.generate_secret()

        with pytest.raises(ValueError) as exc_info:
            service.generate_provisioning_uri(
                secret=secret,
                identifier="",
            )

        assert "empty" in str(exc_info.value).lower()

    def test_generate_provisioning_uri_with_special_characters(self):
        """Test provisioning URI with special characters in identifier."""
        service = TOTPService()
        secret = service.generate_secret()

        uri = service.generate_provisioning_uri(
            secret=secret,
            identifier="user+test@example.com",
        )

        assert "otpauth://totp/" in uri


class TestBackupCodes:
    """Test suite for backup code generation."""

    def test_generate_backup_codes_default_count(self):
        """Test backup code generation with default count."""
        service = TOTPService()

        codes = service.generate_backup_codes()

        assert len(codes) == 10
        assert all(isinstance(code, str) for code in codes)
        assert all(len(code) == 14 for code in codes)  # XXXX-XXXX-XXXX

    def test_generate_backup_codes_custom_count(self):
        """Test backup code generation with custom count."""
        service = TOTPService()

        codes = service.generate_backup_codes(count=5)
        assert len(codes) == 5

        codes = service.generate_backup_codes(count=15)
        assert len(codes) == 15

    def test_generate_backup_codes_invalid_count_too_few(self):
        """Test that too few codes raises ValueError."""
        service = TOTPService()

        with pytest.raises(ValueError) as exc_info:
            service.generate_backup_codes(count=3)

        assert "between 5 and 20" in str(exc_info.value).lower()

    def test_generate_backup_codes_invalid_count_too_many(self):
        """Test that too many codes raises ValueError."""
        service = TOTPService()

        with pytest.raises(ValueError) as exc_info:
            service.generate_backup_codes(count=25)

        assert "between 5 and 20" in str(exc_info.value).lower()

    def test_generate_backup_codes_unique(self):
        """Test that generated backup codes are unique."""
        service = TOTPService()

        codes = service.generate_backup_codes(count=10)

        # All codes should be unique
        assert len(set(codes)) == 10

    def test_generate_backup_codes_format(self):
        """Test that backup codes have correct format."""
        service = TOTPService()

        codes = service.generate_backup_codes(count=10)

        for code in codes:
            # Format: XXXX-XXXX-XXXX
            parts = code.split('-')
            assert len(parts) == 3
            assert all(len(part) == 4 for part in parts)
            assert all(part.isalnum() for part in parts)

    def test_validate_backup_code_format_valid(self):
        """Test backup code format validation with valid codes."""
        service = TOTPService()

        assert service.validate_backup_code_format("AB12-CD34-EF56") is True
        assert service.validate_backup_code_format("1234-5678-9012") is True
        assert service.validate_backup_code_format("AAAA-BBBB-CCCC") is True

    def test_validate_backup_code_format_invalid(self):
        """Test backup code format validation with invalid codes."""
        service = TOTPService()

        assert service.validate_backup_code_format("") is False
        assert service.validate_backup_code_format("invalid") is False
        assert service.validate_backup_code_format("AB12-CD34") is False  # Too short
        assert service.validate_backup_code_format("AB12-CD34-EF56-GH78") is False  # Too long
        assert service.validate_backup_code_format("ab12-cd34-ef56") is False  # Lowercase


class TestGetCurrentCode:
    """Test suite for getting current TOTP code (testing/debugging)."""

    def test_get_current_code_valid(self):
        """Test getting current valid code."""
        service = TOTPService()
        secret = service.generate_secret()

        current_code = service.get_current_code(secret)

        assert current_code is not None
        assert len(current_code) == 6
        assert current_code.isdigit()

        # Should verify correctly
        assert service.verify_code(secret, current_code) is True

    def test_get_current_code_empty_secret(self):
        """Test that empty secret raises ValueError."""
        service = TOTPService()

        with pytest.raises(ValueError) as exc_info:
            service.get_current_code("")

        assert "empty" in str(exc_info.value).lower()


class TestHealthCheck:
    """Test suite for TOTP service health check."""

    def test_health_check_healthy(self):
        """Test health check returns healthy status."""
        service = TOTPService()

        health = service.health_check()

        assert health["status"] == "healthy"
        assert health["configured"] is True
        assert health["issuer"] == "AgentHR"
        assert health["digits"] == 6
        assert health["period"] == 30
        assert health["algorithm"] == "SHA1"
        assert health["backup_codes_count"] == 10
        assert health["error"] is None

    def test_health_check_with_custom_config(self):
        """Test health check reflects custom configuration."""
        service = TOTPService(
            issuer="CustomApp",
            digits=8,
            period=60,
            algorithm="SHA256",
        )

        health = service.health_check()

        assert health["status"] == "healthy"
        assert health["issuer"] == "CustomApp"
        assert health["digits"] == 8
        assert health["period"] == 60
        assert health["algorithm"] == "SHA256"


class TestSingleton:
    """Test suite for singleton pattern."""

    def test_get_totp_service_singleton(self):
        """Test that get_totp_service returns singleton instance."""
        # Reset global service
        import services.totp_service
        services.totp_service._totp_service = None

        service1 = get_totp_service()
        service2 = get_totp_service()

        assert service1 is service2


class TestAlgorithmSupport:
    """Test suite for TOTP algorithm support."""

    def test_sha1_algorithm(self):
        """Test SHA1 algorithm support."""
        service = TOTPService(algorithm="SHA1")

        secret = service.generate_secret()
        totp = pyotp.TOTP(secret, digits=6, period=30, digest=service._get_digest())
        code = totp.now()

        assert service.verify_code(secret, code) is True

    def test_sha256_algorithm(self):
        """Test SHA256 algorithm support."""
        service = TOTPService(algorithm="SHA256")

        secret = service.generate_secret()
        totp = pyotp.TOTP(secret, digits=6, period=30, digest=service._get_digest())
        code = totp.now()

        assert service.verify_code(secret, code) is True

    def test_sha512_algorithm(self):
        """Test SHA512 algorithm support."""
        service = TOTPService(algorithm="SHA512")

        secret = service.generate_secret()
        totp = pyotp.TOTP(secret, digits=6, period=30, digest=service._get_digest())
        code = totp.now()

        assert service.verify_code(secret, code) is True

    def test_invalid_algorithm(self):
        """Test that invalid algorithm raises ValueError."""
        service = TOTPService()

        # Manually set invalid algorithm to test error handling
        service.algorithm = "INVALID"

        with pytest.raises(ValueError) as exc_info:
            service._get_digest()

        assert "unsupported" in str(exc_info.value).lower()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_verify_code_with_padding(self):
        """Test verification handles Base32 padding correctly."""
        service = TOTPService()

        # Generate secret and verify it works
        secret = service.generate_secret()
        totp = pyotp.TOTP(secret, digits=6, period=30)
        code = totp.now()

        assert service.verify_code(secret, code) is True

    def test_provisioning_uri_with_unicode(self):
        """Test provisioning URI with unicode characters."""
        service = TOTPService()
        secret = service.generate_secret()

        # Should handle unicode in name
        uri = service.generate_provisioning_uri(
            secret=secret,
            identifier="test@example.com",
            name="Jöhn Döe",
        )

        assert "otpauth://totp/" in uri

    def test_backup_codes_all_unique_across_generations(self):
        """Test that multiple generations produce unique codes."""
        service = TOTPService()

        codes1 = set(service.generate_backup_codes(count=10))
        codes2 = set(service.generate_backup_codes(count=10))

        # Probability of collision is extremely low
        # But we check that at least most codes are different
        intersection = codes1 & codes2
        assert len(intersection) < 3  # At most 2 collisions expected
