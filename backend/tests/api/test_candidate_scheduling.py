"""
Tests for candidate self-scheduling token generation and validation.

This module tests the self-scheduling token system, including:
- Token generation with expiration
- Token validation and decoding
- Token expiration detection
- Invalid token handling
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from jose import JWTError

from utils.tokens import (
    create_self_schedule_token,
    decode_self_schedule_token,
    validate_self_schedule_token,
    is_self_schedule_token_expired,
)


class TestTokenGeneration:
    """Test self-scheduling token generation."""

    def test_token_generation(self):
        """Test that tokens are generated successfully with all required data."""
        candidate_id = uuid4()
        recruiter_id = uuid4()
        vacancy_id = uuid4()

        token = create_self_schedule_token(
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
            vacancy_id=vacancy_id,
        )

        # Token should be a non-empty string
        assert token
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically quite long

    def test_token_generation_without_vacancy(self):
        """Test that tokens can be generated without a vacancy_id."""
        candidate_id = uuid4()
        recruiter_id = uuid4()

        token = create_self_schedule_token(
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
            vacancy_id=None,
        )

        # Token should be a non-empty string
        assert token
        assert isinstance(token, str)

    def test_token_generation_with_custom_expiration(self):
        """Test that tokens can be generated with custom expiration."""
        candidate_id = uuid4()
        recruiter_id = uuid4()
        expires_delta = timedelta(days=3)

        token = create_self_schedule_token(
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
            expires_delta=expires_delta,
        )

        # Decode token to verify expiration
        token_data = decode_self_schedule_token(token)

        # Check that expiration is approximately 3 days from now
        expected_expiry = datetime.utcnow() + expires_delta
        time_diff = abs((token_data.expires_at - expected_expiry).total_seconds())

        # Allow 5 second tolerance for test execution time
        assert time_diff < 5

    def test_token_generation_requires_candidate_id(self):
        """Test that token generation fails without candidate_id."""
        with pytest.raises(ValueError, match="candidate_id and recruiter_id are required"):
            create_self_schedule_token(
                candidate_id=None,
                recruiter_id=uuid4(),
            )

    def test_token_generation_requires_recruiter_id(self):
        """Test that token generation fails without recruiter_id."""
        with pytest.raises(ValueError, match="candidate_id and recruiter_id are required"):
            create_self_schedule_token(
                candidate_id=uuid4(),
                recruiter_id=None,
            )


class TestTokenValidation:
    """Test self-scheduling token validation and decoding."""

    def test_token_decoding(self):
        """Test that tokens can be decoded to retrieve original data."""
        candidate_id = uuid4()
        recruiter_id = uuid4()
        vacancy_id = uuid4()

        token = create_self_schedule_token(
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
            vacancy_id=vacancy_id,
        )

        token_data = decode_self_schedule_token(token)

        # Verify all fields are present and correct
        assert token_data.candidate_id == str(candidate_id)
        assert token_data.recruiter_id == str(recruiter_id)
        assert token_data.vacancy_id == str(vacancy_id)
        assert isinstance(token_data.expires_at, datetime)
        assert isinstance(token_data.issued_at, datetime)

    def test_token_validation_alias(self):
        """Test that validate_self_schedule_token is an alias for decode."""
        candidate_id = uuid4()
        recruiter_id = uuid4()

        token = create_self_schedule_token(
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
        )

        # Both should return the same data
        decoded_data = decode_self_schedule_token(token)
        validated_data = validate_self_schedule_token(token)

        assert decoded_data.candidate_id == validated_data.candidate_id
        assert decoded_data.recruiter_id == validated_data.recruiter_id

    def test_invalid_token_raises_error(self):
        """Test that invalid tokens raise JWTError."""
        invalid_token = "invalid.token.here"

        with pytest.raises(JWTError):
            decode_self_schedule_token(invalid_token)

    def test_empty_token_raises_error(self):
        """Test that empty tokens raise ValueError."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            decode_self_schedule_token("")

    def test_tampered_token_raises_error(self):
        """Test that tampered tokens raise JWTError."""
        candidate_id = uuid4()
        recruiter_id = uuid4()

        token = create_self_schedule_token(
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
        )

        # Tamper with the token by changing a character
        tampered_token = token[:-5] + "xxxxx"

        with pytest.raises(JWTError):
            decode_self_schedule_token(tampered_token)


class TestTokenExpiration:
    """Test token expiration detection."""

    def test_valid_token_not_expired(self):
        """Test that newly created tokens are not expired."""
        candidate_id = uuid4()
        recruiter_id = uuid4()

        token = create_self_schedule_token(
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
        )

        assert not is_self_schedule_token_expired(token)

    def test_expired_token_detection(self):
        """Test that expired tokens are detected."""
        candidate_id = uuid4()
        recruiter_id = uuid4()

        # Create token that expires in the past
        token = create_self_schedule_token(
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        assert is_self_schedule_token_expired(token)

    def test_invalid_token_considered_expired(self):
        """Test that invalid tokens are considered expired."""
        invalid_token = "invalid.token.here"

        assert is_self_schedule_token_expired(invalid_token)


class TestTokenFields:
    """Test token field validation and data integrity."""

    def test_token_contains_correct_type(self):
        """Test that token type is set to 'self_schedule'."""
        from jose import jwt
        from config import get_settings

        settings = get_settings()
        candidate_id = uuid4()
        recruiter_id = uuid4()

        token = create_self_schedule_token(
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
        )

        # Decode without validation to check raw payload
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        assert payload["type"] == "self_schedule"

    def test_token_without_vacancy_id_has_none(self):
        """Test that tokens without vacancy_id have None in the field."""
        candidate_id = uuid4()
        recruiter_id = uuid4()

        token = create_self_schedule_token(
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
            vacancy_id=None,
        )

        token_data = decode_self_schedule_token(token)
        assert token_data.vacancy_id is None

    def test_wrong_token_type_raises_error(self):
        """Test that tokens with wrong type are rejected."""
        from jose import jwt
        from config import get_settings
        from datetime import datetime

        settings = get_settings()

        # Create a token with wrong type
        payload = {
            "sub": str(uuid4()),
            "candidate_id": str(uuid4()),
            "recruiter_id": str(uuid4()),
            "vacancy_id": None,
            "exp": datetime.utcnow() + timedelta(days=7),
            "iat": datetime.utcnow(),
            "type": "access",  # Wrong type!
        }

        wrong_type_token = jwt.encode(
            payload,
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )

        with pytest.raises(ValueError, match="Invalid token type"):
            decode_self_schedule_token(wrong_type_token)
