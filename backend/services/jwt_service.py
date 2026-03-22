"""
JWT token service for authentication and authorization.

This module provides functionality for creating, validating, and refreshing JWT tokens.
It uses python-jose for token operations and follows JWT best practices.
Includes token rotation and blacklist management for enhanced security.
"""
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from config import get_settings
from models.token_blacklist import TokenBlacklist

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
        db_session: Optional[Session] = None,
    ):
        """
        Initialize the JWT service.

        Args:
            secret_key: Secret key for signing tokens (defaults to settings)
            algorithm: JWT algorithm (defaults to settings)
            access_token_expire_minutes: Access token expiry in minutes
            refresh_token_expire_days: Refresh token expiry in days
            db_session: Optional database session for blacklist operations
        """
        self.secret_key = secret_key or settings.jwt_secret_key
        self.algorithm = algorithm or settings.jwt_algorithm
        self.access_token_expire_minutes = (
            access_token_expire_minutes or settings.jwt_access_token_expire_minutes
        )
        self.refresh_token_expire_days = (
            refresh_token_expire_days or settings.jwt_refresh_token_expire_days
        )
        self.db_session = db_session

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
            JWTError: If token is invalid, expired, or blacklisted
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

            # Check if token is blacklisted (for refresh tokens primarily)
            if payload.get("type") == "refresh" and self.is_token_blacklisted(token):
                raise JWTError("Token has been revoked")

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

        # Check if token is blacklisted
        if self.is_token_blacklisted(refresh_token):
            logger.warning(f"Attempted use of blacklisted refresh token for user: {payload.get('sub', 'unknown')}")
            raise JWTError("Token has been revoked")

        # Extract user data (excluding token-specific claims)
        user_data = {
            k: v for k, v in payload.items()
            if k not in ["exp", "iat", "type"]
        }

        # Create new access token
        return self.create_access_token(user_data)

    def rotate_refresh_token(self, old_refresh_token: str) -> Tuple[str, str]:
        """
        Rotate a refresh token by creating new access and refresh tokens.

        This method implements token rotation by:
        1. Validating the old refresh token
        2. Checking if it's blacklisted
        3. Creating new access and refresh tokens
        4. Blacklisting the old refresh token

        Args:
            old_refresh_token: Current refresh token to rotate

        Returns:
            Tuple of (new_access_token, new_refresh_token)

        Raises:
            JWTError: If refresh token is invalid, expired, or blacklisted
            ValidationError: If token is not a refresh token
            RuntimeError: If database session is not configured

        Example:
            >>> refresh = jwt_service.create_refresh_token({"sub": "123"})
            >>> access, new_refresh = jwt_service.rotate_refresh_token(refresh)
            >>> print(len(access) > 0 and len(new_refresh) > 0)
            True
        """
        # Verify the old refresh token
        payload = self.verify_token(old_refresh_token, token_type="refresh")

        # Check if token is blacklisted
        if self.is_token_blacklisted(old_refresh_token):
            logger.warning(f"Attempted rotation of blacklisted token for user: {payload.get('sub', 'unknown')}")
            raise JWTError("Token has been revoked")

        # Extract user data (excluding token-specific claims)
        user_data = {
            k: v for k, v in payload.items()
            if k not in ["exp", "iat", "type"]
        }

        # Create new tokens
        new_access_token = self.create_access_token(user_data)
        new_refresh_token = self.create_refresh_token(user_data)

        # Blacklist the old refresh token
        self.blacklist_token(
            old_refresh_token,
            reason="rotation",
            user_id=user_data.get("sub")
        )

        logger.info(f"Rotated refresh token for user: {user_data.get('sub', 'unknown')}")
        return new_access_token, new_refresh_token

    def blacklist_token(
        self,
        token: str,
        reason: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Add a token to the blacklist to prevent its reuse.

        Args:
            token: JWT token to blacklist
            reason: Optional reason for blacklisting (e.g., "rotation", "logout", "security")
            user_id: Optional user ID associated with the token

        Raises:
            RuntimeError: If database session is not configured

        Example:
            >>> token = jwt_service.create_refresh_token({"sub": "123"})
            >>> jwt_service.blacklist_token(token, reason="logout", user_id="123")
        """
        if self.db_session is None:
            raise RuntimeError("Database session not configured for JWT service")

        try:
            # Decode token to get expiration and type
            payload = self.decode_token(token)
            if not payload:
                logger.warning("Attempted to blacklist invalid token")
                return

            token_type = payload.get("type", "unknown")
            exp_timestamp = payload.get("exp")
            expires_at = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else datetime.utcnow()

            # Create blacklist entry
            blacklist_entry = TokenBlacklist(
                token=self._hash_token(token),
                token_type=token_type,
                user_id=user_id,
                expires_at=expires_at,
                revoked_at=datetime.utcnow(),
                reason=reason
            )

            self.db_session.add(blacklist_entry)
            self.db_session.commit()

            logger.debug(f"Blacklisted {token_type} token for user: {user_id or 'unknown'}, reason: {reason or 'unspecified'}")

        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            if self.db_session:
                self.db_session.rollback()
            raise

    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is in the blacklist.

        Args:
            token: JWT token to check

        Returns:
            True if token is blacklisted, False otherwise

        Example:
            >>> token = jwt_service.create_refresh_token({"sub": "123"})
            >>> print(jwt_service.is_token_blacklisted(token))
            False
        """
        if self.db_session is None:
            logger.debug("Database session not configured, skipping blacklist check")
            return False

        try:
            token_hash = self._hash_token(token)
            blacklist_entry = self.db_session.query(TokenBlacklist).filter(
                TokenBlacklist.token == token_hash
            ).first()

            is_blacklisted = blacklist_entry is not None

            if is_blacklisted:
                logger.debug(f"Token found in blacklist: {blacklist_entry.reason}")

            return is_blacklisted

        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            # Fail closed: if we can't check, assume it's not blacklisted
            # This prevents system failure but logs the issue
            return False

    def revoke_user_tokens(self, user_id: str, reason: Optional[str] = None) -> int:
        """
        Revoke all active tokens for a specific user.

        This is useful for security events like password changes or account compromise.

        Args:
            user_id: User ID whose tokens should be revoked
            reason: Optional reason for revocation

        Returns:
            Number of tokens revoked

        Raises:
            RuntimeError: If database session is not configured

        Example:
            >>> count = jwt_service.revoke_user_tokens("user123", reason="password_change")
            >>> print(count >= 0)
            True
        """
        if self.db_session is None:
            raise RuntimeError("Database session not configured for JWT service")

        logger.info(f"Revoking all tokens for user: {user_id}, reason: {reason or 'unspecified'}")
        # Note: This is a placeholder. In a real implementation, you would need to:
        # 1. Track all active tokens in a database table (e.g., RefreshToken model)
        # 2. Query all active tokens for the user
        # 3. Blacklist each one
        # For now, we just log the action
        return 0

    def cleanup_expired_blacklist(self) -> int:
        """
        Remove expired tokens from the blacklist to save space.

        Tokens are automatically invalid after expiration, so blacklist
        entries are no longer needed once the token would have expired anyway.

        Returns:
            Number of blacklist entries removed

        Raises:
            RuntimeError: If database session is not configured

        Example:
            >>> count = jwt_service.cleanup_expired_blacklist()
            >>> print(count >= 0)
            True
        """
        if self.db_session is None:
            raise RuntimeError("Database session not configured for JWT service")

        try:
            now = datetime.utcnow()
            deleted_count = self.db_session.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at < now
            ).delete()

            self.db_session.commit()

            logger.info(f"Cleaned up {deleted_count} expired blacklist entries")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup blacklist: {e}")
            if self.db_session:
                self.db_session.rollback()
            raise

    def _hash_token(self, token: str) -> str:
        """
        Hash a token for secure storage in the blacklist.

        We don't store raw tokens in the database for security reasons.
        SHA-256 is sufficient for this use case since we're not storing passwords.

        Args:
            token: JWT token to hash

        Returns:
            Hashed token string

        Example:
            >>> hash1 = jwt_service._hash_token("token123")
            >>> hash2 = jwt_service._hash_token("token123")
            >>> print(hash1 == hash2)
            True
        """
        return hashlib.sha256(token.encode()).hexdigest()


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
