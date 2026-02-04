"""
JWT token handler for authentication and authorization.

This module provides utilities for creating and validating JWT tokens
used for user authentication. It supports both access tokens and refresh tokens.

Access tokens are short-lived (default 30 minutes) and used for API authentication.
Refresh tokens are longer-lived (default 7 days) and used to obtain new access tokens.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError

from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


# Token Data Models
class TokenPayload(BaseModel):
    """
    JWT token payload data.

    Attributes:
        sub: User ID (subject)
        exp: Token expiration timestamp
        iat: Token issued at timestamp
        type: Token type (access or refresh)
        email: User's email address
    """

    sub: str
    exp: int
    iat: int
    type: str
    email: str


class TokenData(BaseModel):
    """
    Extracted token data after validation.

    Attributes:
        user_id: User's UUID
        email: User's email
        token_type: Type of token (access or refresh)
    """

    user_id: str
    email: str
    token_type: str


def create_access_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token for a user.

    Args:
        user_id: User's UUID
        email: User's email address
        expires_delta: Optional custom expiration time. If not provided,
                      uses default from settings (30 minutes)

    Returns:
        Encoded JWT access token

    Raises:
        ValueError: If required parameters are missing

    Example:
        >>> token = create_access_token(
        ...     user_id="123e4567-e89b-12d3-a456-426614174000",
        ...     email="user@example.com"
        ... )
    """
    if not user_id or not email:
        logger.error("Cannot create access token: missing user_id or email")
        raise ValueError("user_id and email are required")

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "email": email,
    }

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
        logger.debug(f"Created access token for user {email}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to encode access token: {e}")
        raise


def create_refresh_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token for a user.

    Refresh tokens are longer-lived than access tokens and can be used
    to obtain new access tokens without requiring the user to log in again.

    Args:
        user_id: User's UUID
        email: User's email address
        expires_delta: Optional custom expiration time. If not provided,
                      uses default from settings (7 days)

    Returns:
        Encoded JWT refresh token

    Raises:
        ValueError: If required parameters are missing

    Example:
        >>> token = create_refresh_token(
        ...     user_id="123e4567-e89b-12d3-a456-426614174000",
        ...     email="user@example.com"
        ... )
    """
    if not user_id or not email:
        logger.error("Cannot create refresh token: missing user_id or email")
        raise ValueError("user_id and email are required")

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "email": email,
    }

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
        logger.debug(f"Created refresh token for user {email}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to encode refresh token: {e}")
        raise


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        TokenData containing the decoded information

    Raises:
        JWTError: If token is invalid, expired, or malformed
        ValueError: If token payload is missing required fields

    Example:
        >>> try:
        ...     data = decode_token(token)
        ...     print(f"User ID: {data.user_id}")
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
        logger.warning(f"Failed to decode token: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {e}")
        raise JWTError(f"Token decoding failed: {e}")

    # Validate payload structure
    try:
        token_payload = TokenPayload(**payload)
    except ValidationError as e:
        logger.warning(f"Token payload validation failed: {e}")
        raise ValueError(f"Invalid token payload: {e}")

    # Extract and return token data
    token_data = TokenData(
        user_id=token_payload.sub,
        email=token_payload.email,
        token_type=token_payload.type,
    )

    logger.debug(
        f"Decoded {token_data.token_type} token for user {token_data.email}"
    )
    return token_data


def verify_token_type(token: str, expected_type: str) -> TokenData:
    """
    Decode and verify token type.

    Args:
        token: JWT token to verify
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        TokenData containing the decoded information

    Raises:
        JWTError: If token is invalid, expired, or wrong type
        ValueError: If token payload is missing required fields

    Example:
        >>> try:
        ...     data = verify_token_type(token, "access")
        ...     print(f"Access token valid for user {data.email}")
        ... except JWTError as e:
        ...     print(f"Invalid token: {e}")
    """
    token_data = decode_token(token)

    if token_data.token_type != expected_type:
        logger.warning(
            f"Token type mismatch: expected {expected_type}, got {token_data.token_type}"
        )
        raise JWTError(f"Invalid token type: expected {expected_type}")

    return token_data


def is_token_expired(token: str) -> bool:
    """
    Check if a token is expired without raising an exception.

    Args:
        token: JWT token to check

    Returns:
        True if token is expired, False otherwise

    Example:
        >>> if is_token_expired(token):
        ...     print("Token has expired")
        ... else:
        ...     print("Token is still valid")
    """
    try:
        decode_token(token)
        return False
    except JWTError:
        return True
