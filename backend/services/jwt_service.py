"""
JWT token service for authentication and authorization.

This module provides functionality for creating, validating, and refreshing JWT tokens.
It uses python-jose for token operations and follows JWT best practices.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from pydantic import ValidationError

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class JWTService:
    """
    Service for JWT token operations.

    This service handles the creation, validation, and refresh of JWT tokens
    for user authentication. It supports both access tokens (short-lived) and
    refresh tokens (long-lived).

    Attributes:
        secret_key: Secret key used for signing tokens
        algorithm: Encryption algorithm used for token signing
        access_token_expire_minutes: Default access token expiration time
        refresh_token_expire_days: Default refresh token expiration time

    Example:
        >>> jwt_service = JWTService()
        >>> token = jwt_service.create_access_token({"sub": "user123"})
        >>> payload = jwt_service.verify_token(token)
        >>> print(payload["sub"])
        user123
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        access_token_expire_minutes: Optional[int] = None,
        refresh_token_expire_days: Optional[int] = None,
    ):
        """
        Initialize the JWT service.

        Args:
            secret_key: Secret key for signing tokens (defaults to settings)
            algorithm: JWT algorithm (defaults to settings)
            access_token_expire_minutes: Access token expiry in minutes
            refresh_token_expire_days: Refresh token expiry in days
        """
        self.secret_key = secret_key or settings.jwt_secret_key
        self.algorithm = algorithm or settings.jwt_algorithm
        self.access_token_expire_minutes = (
            access_token_expire_minutes or settings.jwt_access_token_expire_minutes
        )
        self.refresh_token_expire_days = (
            refresh_token_expire_days or settings.jwt_refresh_token_expire_days
        )

        if self.secret_key == "change-this-secret-key-in-production":
            logger.warning(
                "Using default JWT secret key - MUST be changed in production!"
            )

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT access token.

        Args:
            data: Payload data to encode in the token (e.g., {"sub": "user_id"})
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT access token

        Raises:
            ValueError: If data is empty or invalid

        Example:
            >>> token = jwt_service.create_access_token({"sub": "123"})
            >>> print(len(token) > 0)
            True
        """
        if not data:
            raise ValueError("Token payload cannot be empty")

        to_encode = data.copy()

        # Calculate expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        # Add standard JWT claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        })

        try:
            encoded_jwt = jwt.encode(
                to_encode,
                self.secret_key,
                algorithm=self.algorithm,
            )
            logger.debug(f"Created access token for subject: {data.get('sub', 'unknown')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise

    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT refresh token.

        Refresh tokens are longer-lived and can be used to obtain new access tokens.

        Args:
            data: Payload data to encode in the token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT refresh token

        Raises:
            ValueError: If data is empty or invalid

        Example:
            >>> token = jwt_service.create_refresh_token({"sub": "123"})
            >>> print(len(token) > 0)
            True
        """
        if not data:
            raise ValueError("Token payload cannot be empty")

        to_encode = data.copy()

        # Calculate expiration time (longer than access tokens)
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=self.refresh_token_expire_days
            )

        # Add standard JWT claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
        })

        try:
            encoded_jwt = jwt.encode(
                to_encode,
                self.secret_key,
                algorithm=self.algorithm,
            )
            logger.debug(f"Created refresh token for subject: {data.get('sub', 'unknown')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise

    def verify_token(self, token: str, token_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token to verify
            token_type: Optional expected token type ("access" or "refresh")

        Returns:
            Decoded token payload

        Raises:
            JWTError: If token is invalid or expired
            ValidationError: If token type doesn't match expected type

        Example:
            >>> token = jwt_service.create_access_token({"sub": "123"})
            >>> payload = jwt_service.verify_token(token)
            >>> print(payload["sub"])
            123
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )

            # Verify token type if specified
            if token_type and payload.get("type") != token_type:
                raise ValidationError(
                    f"Invalid token type: expected '{token_type}', "
                    f"got '{payload.get('type')}'"
                )

            logger.debug(f"Verified token for subject: {payload.get('sub', 'unknown')}")
            return payload

        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            raise
        except ValidationError as e:
            logger.warning(f"Token validation failed: {e}")
            raise

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode a JWT token without verification (for debugging only).

        WARNING: This does not verify the signature. Do not use for authentication.

        Args:
            token: JWT token to decode

        Returns:
            Decoded token payload or None if decoding fails

        Example:
            >>> token = jwt_service.create_access_token({"sub": "123"})
            >>> payload = jwt_service.decode_token(token)
            >>> print(payload["sub"] if payload else None)
            123
        """
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
            )
            return payload
        except Exception as e:
            logger.error(f"Failed to decode token: {e}")
            return None

    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Get the expiration datetime from a token.

        Args:
            token: JWT token

        Returns:
            Expiration datetime or None if token is invalid

        Example:
            >>> token = jwt_service.create_access_token({"sub": "123"})
            >>> expiry = jwt_service.get_token_expiry(token)
            >>> print(expiry > datetime.utcnow())
            True
        """
        try:
            payload = self.verify_token(token)
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)
        except (JWTError, ValidationError):
            pass
        return None

    def is_token_expired(self, token: str) -> bool:
        """
        Check if a token is expired.

        Args:
            token: JWT token

        Returns:
            True if token is expired or invalid, False otherwise

        Example:
            >>> token = jwt_service.create_access_token({"sub": "123"})
            >>> print(jwt_service.is_token_expired(token))
            False
        """
        try:
            expiry = self.get_token_expiry(token)
            if expiry is None:
                return True
            return datetime.utcnow() > expiry
        except Exception:
            return True

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Create a new access token from a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token

        Raises:
            JWTError: If refresh token is invalid or expired
            ValidationError: If token is not a refresh token

        Example:
            >>> refresh = jwt_service.create_refresh_token({"sub": "123"})
            >>> access = jwt_service.refresh_access_token(refresh)
            >>> print(len(access) > 0)
            True
        """
        # Verify the refresh token
        payload = self.verify_token(refresh_token, token_type="refresh")

        # Extract user data (excluding token-specific claims)
        user_data = {
            k: v for k, v in payload.items()
            if k not in ["exp", "iat", "type"]
        }

        # Create new access token
        return self.create_access_token(user_data)


# Global JWT service instance
_jwt_service: Optional[JWTService] = None


def get_jwt_service() -> JWTService:
    """
    Get or create the global JWT service instance.

    Returns:
        JWT service instance

    Example:
        >>> jwt_service = get_jwt_service()
        >>> token = jwt_service.create_access_token({"sub": "test"})
    """
    global _jwt_service
    if _jwt_service is None:
        _jwt_service = JWTService()
        logger.info("JWT service initialized")
    return _jwt_service
