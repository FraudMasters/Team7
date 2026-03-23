"""
Self-scheduling token generation and validation.

This module provides utilities for creating and validating self-scheduling tokens
that allow candidates to book interview slots. Tokens are JWT-based with expiration
and include candidate, recruiter, and vacancy information.

Tokens are typically sent via email/SMS to candidates and expire after a configurable
time period (default 7 days).
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError

from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


# Token Data Models
class SelfScheduleTokenPayload(BaseModel):
    """
    Self-scheduling token payload data.

    Attributes:
        sub: Candidate ID (subject - Resume ID)
        candidate_id: Candidate's Resume ID (same as sub)
        recruiter_id: Recruiter who sent the invitation
        vacancy_id: Optional job vacancy ID
        exp: Token expiration timestamp
        iat: Token issued at timestamp
        type: Token type (always "self_schedule")
    """

    sub: str
    candidate_id: str
    recruiter_id: str
    vacancy_id: Optional[str] = None
    exp: int
    iat: int
    type: str


class SelfScheduleTokenData(BaseModel):
    """
    Extracted self-scheduling token data after validation.

    Attributes:
        candidate_id: Candidate's Resume UUID
        recruiter_id: Recruiter's UUID
        vacancy_id: Optional job vacancy UUID
        expires_at: When the token expires
        issued_at: When the token was issued
    """

    candidate_id: str
    recruiter_id: str
    vacancy_id: Optional[str] = None
    expires_at: datetime
    issued_at: datetime


def create_self_schedule_token(
    candidate_id: UUID,
    recruiter_id: UUID,
    vacancy_id: Optional[UUID] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a self-scheduling token for a candidate.

    This token allows a candidate to self-schedule an interview from
    available time slots. The token is typically sent via email/SMS.

    Args:
        candidate_id: Candidate's Resume UUID
        recruiter_id: Recruiter's UUID who is offering the interview
        vacancy_id: Optional job vacancy UUID the interview is for
        expires_delta: Optional custom expiration time. If not provided,
                      uses default of 7 days

    Returns:
        Encoded JWT self-scheduling token

    Raises:
        ValueError: If required parameters are missing

    Example:
        >>> from uuid import uuid4
        >>> token = create_self_schedule_token(
        ...     candidate_id=uuid4(),
        ...     recruiter_id=uuid4(),
        ...     vacancy_id=uuid4()
        ... )
        >>> # Send token to candidate via email/SMS
    """
    if not candidate_id or not recruiter_id:
        logger.error("Cannot create self-schedule token: missing candidate_id or recruiter_id")
        raise ValueError("candidate_id and recruiter_id are required")

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to 7 days
        expire = datetime.utcnow() + timedelta(days=7)

    issued_at = datetime.utcnow()

    to_encode = {
        "sub": str(candidate_id),
        "candidate_id": str(candidate_id),
        "recruiter_id": str(recruiter_id),
        "vacancy_id": str(vacancy_id) if vacancy_id else None,
        "exp": expire,
        "iat": issued_at,
        "type": "self_schedule",
    }

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
        logger.info(
            f"Created self-schedule token for candidate {candidate_id} with recruiter {recruiter_id}"
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to encode self-schedule token: {e}")
        raise


def decode_self_schedule_token(token: str) -> SelfScheduleTokenData:
    """
    Decode and validate a self-scheduling token.

    Args:
        token: JWT self-scheduling token to decode

    Returns:
        SelfScheduleTokenData containing the decoded information

    Raises:
        JWTError: If token is invalid, expired, or malformed
        ValueError: If token payload is missing required fields or wrong type

    Example:
        >>> try:
        ...     data = decode_self_schedule_token(token)
        ...     print(f"Candidate ID: {data.candidate_id}")
        ...     print(f"Recruiter ID: {data.recruiter_id}")
        ...     print(f"Expires at: {data.expires_at}")
        ... except JWTError as e:
        ...     print(f"Invalid token: {e}")
    """
    if not token:
        logger.error("Cannot decode token: token is empty")
        raise ValueError("Token cannot be empty")

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as e:
        logger.warning(f"Failed to decode self-schedule token: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error decoding self-schedule token: {e}")
        raise JWTError(f"Token decoding failed: {e}")

    # Validate payload structure
    try:
        token_payload = SelfScheduleTokenPayload(**payload)
    except ValidationError as e:
        logger.warning(f"Self-schedule token payload validation failed: {e}")
        raise ValueError(f"Invalid token payload: {e}")

    # Verify token type
    if token_payload.type != "self_schedule":
        logger.warning(
            f"Token type mismatch: expected 'self_schedule', got '{token_payload.type}'"
        )
        raise ValueError(f"Invalid token type: expected 'self_schedule'")

    # Extract and return token data
    token_data = SelfScheduleTokenData(
        candidate_id=token_payload.candidate_id,
        recruiter_id=token_payload.recruiter_id,
        vacancy_id=token_payload.vacancy_id,
        expires_at=datetime.utcfromtimestamp(token_payload.exp),
        issued_at=datetime.utcfromtimestamp(token_payload.iat),
    )

    logger.debug(
        f"Decoded self-schedule token for candidate {token_data.candidate_id}"
    )
    return token_data


def is_self_schedule_token_expired(token: str) -> bool:
    """
    Check if a self-scheduling token is expired without raising an exception.

    Args:
        token: JWT self-scheduling token to check

    Returns:
        True if token is expired or invalid, False otherwise

    Example:
        >>> if is_self_schedule_token_expired(token):
        ...     print("Token has expired - candidate needs a new link")
        ... else:
        ...     print("Token is still valid")
    """
    try:
        decode_self_schedule_token(token)
        return False
    except (JWTError, ValueError):
        return True


def validate_self_schedule_token(token: str) -> SelfScheduleTokenData:
    """
    Validate a self-scheduling token and return decoded data.

    This is an alias for decode_self_schedule_token() with a more
    descriptive name for validation use cases.

    Args:
        token: JWT self-scheduling token to validate

    Returns:
        SelfScheduleTokenData containing the decoded information

    Raises:
        JWTError: If token is invalid, expired, or malformed
        ValueError: If token payload is missing required fields or wrong type

    Example:
        >>> try:
        ...     data = validate_self_schedule_token(token)
        ...     # Token is valid, proceed with scheduling
        ... except (JWTError, ValueError) as e:
        ...     # Token is invalid or expired
        ...     return {"error": "Invalid or expired scheduling link"}
    """
    return decode_self_schedule_token(token)
