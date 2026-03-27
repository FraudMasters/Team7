"""
Authentication service with password hashing and user management.

This module provides authentication and authorization functionality including
user registration, login, password reset, and email verification. It uses
bcrypt for secure password hashing and integrates with the JWT service for
token generation.

The authentication service supports:
- Secure password hashing with bcrypt
- User registration with email validation
- Login with email/password authentication
- JWT token generation and validation
- Password reset via email tokens
- Email verification flow
- Session management with refresh tokens

Password requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

import bcrypt
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from models import User, Role, RefreshToken, LoginAttempt
from services.jwt_service import JWTService, get_jwt_service

logger = logging.getLogger(__name__)

# Global auth service instance
_auth_service: Optional["AuthService"] = None


class AuthService:
    """
    Authentication service with password hashing and user management.

    This class provides a high-level interface for authentication operations
    including user registration, login, password reset, and token management.

    Attributes:
        jwt_service: JWT service for token operations
        password_min_length: Minimum password length
        password_require_uppercase: Whether password requires uppercase
        password_require_lowercase: Whether password requires lowercase
        password_require_number: Whether password requires numbers
        password_reset_expire_hours: Password reset token expiration

    Example:
        >>> auth = AuthService()
        >>> user = await auth.register_user(db, "john@example.com", "password123", "John")
        >>> tokens = await auth.login_user(db, "john@example.com", "password123")
    """

    # Password requirements
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBER = True

    # Token expiration times
    PASSWORD_RESET_EXPIRE_HOURS = 24
    EMAIL_VERIFICATION_EXPIRE_HOURS = 48

    # Account lockout settings
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_WINDOW_MINUTES = 15
    ACCOUNT_LOCKOUT_DURATION_MINUTES = 30

    def __init__(
        self,
        jwt_service: Optional[JWTService] = None,
        password_min_length: Optional[int] = None,
    ) -> None:
        """
        Initialize the authentication service.

        Args:
            jwt_service: JWT service instance (defaults to global instance)
            password_min_length: Minimum password length requirement
        """
        settings = get_settings()

        self.jwt_service = jwt_service or get_jwt_service()
        self.password_min_length = password_min_length or self.PASSWORD_MIN_LENGTH

        logger.info("AuthService initialized")

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Bcrypt hash of the password

        Raises:
            ValueError: If password doesn't meet requirements

        Example:
            >>> auth = AuthService()
            >>> hashed = auth.hash_password("SecurePass123")
            >>> print(len(hashed) == 60)  # Bcrypt hashes are 60 chars
            True
        """
        # Validate password requirements
        self._validate_password_requirements(password)

        try:
            # Generate salt and hash password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to hash password: {e}")
            raise

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against a bcrypt hash.

        Args:
            password: Plain text password to verify
            hashed_password: Bcrypt hash to compare against

        Returns:
            True if password matches hash, False otherwise

        Example:
            >>> auth = AuthService()
            >>> hashed = auth.hash_password("SecurePass123")
            >>> print(auth.verify_password("SecurePass123", hashed))
            True
            >>> print(auth.verify_password("WrongPass", hashed))
            False
        """
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception as e:
            logger.error(f"Failed to verify password: {e}")
            return False

    def _validate_password_requirements(self, password: str) -> None:
        """
        Validate that password meets security requirements.

        Args:
            password: Password to validate

        Raises:
            ValueError: If password doesn't meet requirements

        Requirements:
            - Minimum 8 characters
            - At least one uppercase letter (if required)
            - At least one lowercase letter (if required)
            - At least one number (if required)
        """
        if len(password) < self.password_min_length:
            raise ValueError(
                f"Password must be at least {self.password_min_length} characters long"
            )

        if self.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")

        if self.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")

        if self.PASSWORD_REQUIRE_NUMBER and not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one number")

    async def register_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        name: str,
        role_name: str = "Recruiter",
    ) -> User:
        """
        Register a new user account.

        Args:
            db: Database session
            email: User's email address (must be unique)
            password: User's password (will be hashed)
            name: User's full name
            role_name: Role name to assign (defaults to "Recruiter")

        Returns:
            Created User object

        Raises:
            ValueError: If email already exists or password is invalid
            RuntimeError: If role doesn't exist

        Example:
            >>> auth = AuthService()
            >>> user = await auth.register_user(
            ...     db, "john@example.com", "SecurePass123", "John Doe"
            ... )
            >>> print(user.email)
            john@example.com
        """
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.warning(f"Registration attempt with existing email: {email}")
            raise ValueError(f"User with email {email} already exists")

        # Hash password
        password_hash = self.hash_password(password)

        # Get role
        result = await db.execute(select(Role).where(Role.name == role_name))
        role = result.scalar_one_or_none()

        if not role:
            logger.error(f"Role not found: {role_name}")
            raise ValueError(f"Role '{role_name}' not found")

        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            role_id=role.id,
            is_active=True,
            email_verified=False,
        )

        db.add(user)
        await db.flush()
        await db.refresh(user)

        logger.info(f"User registered successfully: {user.id}")
        return user

    async def login_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Authenticate a user with email and password.

        Args:
            db: Database session
            email: User's email address
            password: User's password
            ip_address: IP address of the client (for tracking)
            user_agent: User agent string (for tracking)
            location: Optional location derived from IP (for tracking)

        Returns:
            Dictionary with access_token, refresh_token, and user info

        Raises:
            ValueError: If credentials are invalid, user is inactive, or account is locked

        Example:
            >>> auth = AuthService()
            >>> result = await auth.login_user(db, "john@example.com", "password")
            >>> print(result["access_token"])
            eyJ0eXAiOiJKV1QiLCJhbGc...
        """
        # Check if account is locked before proceeding
        await self.check_account_lockout(db, email)

        # Get user
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            # Track failed login attempt for non-existent user
            await self.track_login_attempt(
                db,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason="user_not_found",
                location=location,
            )
            raise ValueError("Invalid email or password")

        # Verify password
        if not self.verify_password(password, user.password_hash):
            logger.warning(f"Login attempt with invalid password for: {email}")
            # Track failed login attempt due to invalid password
            await self.track_login_attempt(
                db,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason="invalid_password",
                user_id=user.id,
                location=location,
            )
            raise ValueError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {email}")
            # Track failed login attempt due to inactive account
            await self.track_login_attempt(
                db,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason="account_disabled",
                user_id=user.id,
                location=location,
            )
            raise ValueError("User account is disabled")

        # Get user role
        result = await db.execute(select(Role).where(Role.id == user.role_id))
        role = result.scalar_one_or_none()

        # Create tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": role.name if role else "Viewer",
        }

        access_token = self.jwt_service.create_access_token(token_data)
        refresh_token = self.jwt_service.create_refresh_token(token_data)

        # Store refresh token in database
        await self._store_refresh_token(
            db,
            user_id=user.id,
            token=refresh_token,
        )

        # Track successful login attempt
        await self.track_login_attempt(
            db,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            user_id=user.id,
            location=location,
        )

        logger.info(f"User logged in successfully: {user.id}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": role.name if role else "Viewer",
                "email_verified": user.email_verified,
            },
        }

    async def refresh_tokens(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> Dict[str, Any]:
        """
        Generate new access token from refresh token.

        Args:
            db: Database session
            refresh_token: Valid refresh token

        Returns:
            Dictionary with new access_token and refresh_token

        Raises:
            ValueError: If refresh token is invalid or expired
            RuntimeError: If refresh token not found in database

        Example:
            >>> auth = AuthService()
            >>> tokens = await auth.refresh_tokens(db, refresh_token)
            >>> print(tokens["access_token"])
            eyJ0eXAiOiJKV1QiLCJhbGc...
        """
        # Verify refresh token
        try:
            payload = self.jwt_service.verify_token(refresh_token, token_type="refresh")
        except JWTError as e:
            logger.warning(f"Invalid refresh token: {e}")
            raise ValueError("Invalid refresh token")

        # Check if refresh token exists in database
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.revoked_at.is_(None),
            )
        )
        token_record = result.scalar_one_or_none()

        if not token_record:
            logger.warning("Refresh token not found in database")
            raise ValueError("Invalid refresh token")

        # Check if token is expired
        if token_record.expires_at < datetime.utcnow():
            logger.warning(f"Refresh token expired: {token_record.id}")
            # Revoke the expired token
            token_record.revoked_at = datetime.utcnow()
            await db.flush()
            raise ValueError("Refresh token has expired")

        # Get user
        result = await db.execute(
            select(User).where(User.id == token_record.user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            logger.warning(f"User not found or inactive for refresh token: {token_record.user_id}")
            raise ValueError("Invalid refresh token")

        # Get user role
        result = await db.execute(select(Role).where(Role.id == user.role_id))
        role = result.scalar_one_or_none()

        # Create new tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": role.name if role else "Viewer",
        }

        access_token = self.jwt_service.create_access_token(token_data)
        new_refresh_token = self.jwt_service.create_refresh_token(token_data)

        # Revoke old refresh token and store new one
        token_record.revoked_at = datetime.utcnow()
        await self._store_refresh_token(
            db,
            user_id=user.id,
            token=new_refresh_token,
        )

        logger.info(f"Tokens refreshed successfully for user: {user.id}")

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def logout_user(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> bool:
        """
        Logout a user by revoking their refresh token.

        Args:
            db: Database session
            refresh_token: Refresh token to revoke

        Returns:
            True if logout successful, False otherwise

        Example:
            >>> auth = AuthService()
            >>> success = await auth.logout_user(db, refresh_token)
            >>> print(success)
            True
        """
        try:
            # Find and revoke the refresh token
            result = await db.execute(
                select(RefreshToken).where(
                    RefreshToken.token == refresh_token,
                    RefreshToken.revoked_at.is_(None),
                )
            )
            token_record = result.scalar_one_or_none()

            if token_record:
                token_record.revoked_at = datetime.utcnow()
                logger.info(f"User logged out, token revoked: {token_record.user_id}")
                return True
            else:
                logger.warning("Logout attempt with non-existent refresh token")
                return False

        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False

    async def create_password_reset_token(
        self,
        db: AsyncSession,
        email: str,
    ) -> str:
        """
        Create a password reset token for a user.

        Args:
            db: Database session
            email: User's email address

        Returns:
            Password reset token

        Raises:
            ValueError: If email not found

        Example:
            >>> auth = AuthService()
            >>> token = await auth.create_password_reset_token(db, "john@example.com")
            >>> print(len(token) > 0)
            True
        """
        # Get user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Password reset requested for non-existent email: {email}")
            raise ValueError("User with this email not found")

        # Create reset token (JWT with user ID and expiration)
        reset_data = {
            "sub": str(user.id),
            "email": user.email,
            "type": "password_reset",
        }

        expire_delta = timedelta(hours=self.PASSWORD_RESET_EXPIRE_HOURS)
        token = self.jwt_service.create_access_token(
            reset_data,
            expires_delta=expire_delta,
        )

        logger.info(f"Password reset token created for user: {user.id}")
        return token

    async def reset_password(
        self,
        db: AsyncSession,
        token: str,
        new_password: str,
    ) -> bool:
        """
        Reset user password using a reset token.

        Args:
            db: Database session
            token: Password reset token
            new_password: New password to set

        Returns:
            True if password reset successful

        Raises:
            ValueError: If token is invalid or expired

        Example:
            >>> auth = AuthService()
            >>> success = await auth.reset_password(db, token, "NewSecurePass123")
            >>> print(success)
            True
        """
        try:
            # Verify reset token
            payload = self.jwt_service.verify_token(token)

            # Check token type
            if payload.get("type") != "password_reset":
                raise ValueError("Invalid token type")

            # Get user ID from token
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token")

            # Get user
            result = await db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"Password reset for non-existent user: {user_id}")
                raise ValueError("User not found")

            # Hash new password
            password_hash = self.hash_password(new_password)

            # Update password
            user.password_hash = password_hash
            await db.flush()

            # Revoke all existing refresh tokens for security
            await db.execute(
                select(RefreshToken).where(
                    RefreshToken.user_id == user.id,
                    RefreshToken.revoked_at.is_(None),
                )
            )
            # Note: In real implementation, you'd update all tokens to set revoked_at

            logger.info(f"Password reset successful for user: {user.id}")
            return True

        except JWTError as e:
            logger.warning(f"Invalid password reset token: {e}")
            raise ValueError("Invalid or expired reset token")

    async def create_email_verification_token(
        self,
        db: AsyncSession,
        email: str,
    ) -> str:
        """
        Create an email verification token.

        Args:
            db: Database session
            email: User's email address

        Returns:
            Email verification token

        Raises:
            ValueError: If email not found

        Example:
            >>> auth = AuthService()
            >>> token = await auth.create_email_verification_token(db, "john@example.com")
            >>> print(len(token) > 0)
            True
        """
        # Get user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Email verification requested for non-existent email: {email}")
            raise ValueError("User with this email not found")

        # Create verification token
        verification_data = {
            "sub": str(user.id),
            "email": user.email,
            "type": "email_verification",
        }

        expire_delta = timedelta(hours=self.EMAIL_VERIFICATION_EXPIRE_HOURS)
        token = self.jwt_service.create_access_token(
            verification_data,
            expires_delta=expire_delta,
        )

        logger.info(f"Email verification token created for user: {user.id}")
        return token

    async def verify_email(
        self,
        db: AsyncSession,
        token: str,
    ) -> bool:
        """
        Verify user email using verification token.

        Args:
            db: Database session
            token: Email verification token

        Returns:
            True if verification successful

        Raises:
            ValueError: If token is invalid or expired

        Example:
            >>> auth = AuthService()
            >>> success = await auth.verify_email(db, token)
            >>> print(success)
            True
        """
        try:
            # Verify token
            payload = self.jwt_service.verify_token(token)

            # Check token type
            if payload.get("type") != "email_verification":
                raise ValueError("Invalid token type")

            # Get user ID from token
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token")

            # Get user
            result = await db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"Email verification for non-existent user: {user_id}")
                raise ValueError("User not found")

            # Mark email as verified
            user.email_verified = True
            await db.flush()

            logger.info(f"Email verified successfully for user: {user.id}")
            return True

        except JWTError as e:
            logger.warning(f"Invalid email verification token: {e}")
            raise ValueError("Invalid or expired verification token")

    async def change_password(
        self,
        db: AsyncSession,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Change user password (requires current password).

        Args:
            db: Database session
            user_id: User's ID
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password changed successfully

        Raises:
            ValueError: If current password is invalid

        Example:
            >>> auth = AuthService()
            >>> success = await auth.change_password(
            ...     db, user_id, "oldpass", "newpass"
            ... )
            >>> print(success)
            True
        """
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Password change requested for non-existent user: {user_id}")
            raise ValueError("User not found")

        # Verify current password
        if not self.verify_password(current_password, user.password_hash):
            logger.warning(f"Invalid current password for user: {user_id}")
            raise ValueError("Current password is incorrect")

        # Hash and update new password
        password_hash = self.hash_password(new_password)
        user.password_hash = password_hash
        await db.flush()

        # Revoke all existing refresh tokens for security
        # Note: In real implementation, you'd update all tokens

        logger.info(f"Password changed successfully for user: {user_id}")
        return True

    async def _store_refresh_token(
        self,
        db: AsyncSession,
        user_id: UUID,
        token: str,
    ) -> RefreshToken:
        """
        Store a refresh token in the database.

        Args:
            db: Database session
            user_id: User's ID
            token: Refresh token string

        Returns:
            Created RefreshToken object
        """
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(
            days=self.jwt_service.refresh_token_expire_days
        )

        # Create refresh token record
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            revoked_at=None,
        )

        db.add(refresh_token)
        await db.flush()

        logger.debug(f"Refresh token stored for user: {user_id}")
        return refresh_token

    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            db: Database session
            user_id: User's ID

        Returns:
            User object or None if not found

        Example:
            >>> auth = AuthService()
            >>> user = await auth.get_user_by_id(db, user_id)
            >>> print(user.email if user else "Not found")
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> Optional[User]:
        """
        Get a user by email.

        Args:
            db: Database session
            email: User's email address

        Returns:
            User object or None if not found

        Example:
            >>> auth = AuthService()
            >>> user = await auth.get_user_by_email(db, "john@example.com")
            >>> print(user.name if user else "Not found")
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def track_login_attempt(
        self,
        db: AsyncSession,
        email: str,
        ip_address: str,
        user_agent: Optional[str],
        success: bool,
        failure_reason: Optional[str] = None,
        user_id: Optional[UUID] = None,
        location: Optional[str] = None,
    ) -> LoginAttempt:
        """
        Track a login attempt for security monitoring and brute force protection.

        Args:
            db: Database session
            email: Email address used in login attempt
            ip_address: IP address of the client
            user_agent: User agent string from the browser/client
            success: Whether the login attempt was successful
            failure_reason: Reason for failure (e.g., "invalid_password", "account_locked")
            user_id: User ID if the account exists
            location: Optional location derived from IP

        Returns:
            Created LoginAttempt object

        Example:
            >>> auth = AuthService()
            >>> attempt = await auth.track_login_attempt(
            ...     db, "john@example.com", "192.168.1.1", "Mozilla/5.0",
            ...     False, "invalid_password"
            ... )
            >>> print(attempt.success)
            False
        """
        try:
            login_attempt = LoginAttempt(
                user_id=user_id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                failure_reason=failure_reason,
                location=location,
            )

            db.add(login_attempt)
            await db.flush()
            await db.refresh(login_attempt)

            if success:
                logger.info(f"Successful login attempt tracked: {email} from {ip_address}")
            else:
                logger.warning(
                    f"Failed login attempt tracked: {email} from {ip_address} "
                    f"(reason: {failure_reason})"
                )

            return login_attempt

        except Exception as e:
            logger.error(f"Error tracking login attempt: {e}")
            raise

    async def is_account_locked(
        self,
        db: AsyncSession,
        email: str,
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Check if an account is currently locked due to too many failed login attempts.

        Args:
            db: Database session
            email: Email address to check

        Returns:
            Tuple of (is_locked, locked_until) where:
                - is_locked: True if account is locked
                - locked_until: Datetime when lockout expires (None if not locked)

        Example:
            >>> auth = AuthService()
            >>> is_locked, locked_until = await auth.is_account_locked(db, "john@example.com")
            >>> if is_locked:
            ...     print(f"Account locked until {locked_until}")
        """
        try:
            # Calculate the time window for checking failed attempts
            window_start = datetime.utcnow() - timedelta(
                minutes=self.LOGIN_ATTEMPT_WINDOW_MINUTES
            )

            # Count failed login attempts within the window
            result = await db.execute(
                select(LoginAttempt)
                .where(
                    LoginAttempt.email == email,
                    LoginAttempt.success == False,
                    LoginAttempt.created_at >= window_start,
                )
                .order_by(LoginAttempt.created_at.desc())
            )
            failed_attempts = result.scalars().all()

            # If we don't have enough failed attempts, account is not locked
            if len(failed_attempts) < self.MAX_LOGIN_ATTEMPTS:
                return False, None

            # Check if there was a successful login after the failed attempts
            # This would reset the lockout
            if failed_attempts:
                oldest_failed_attempt = failed_attempts[-1]
                result = await db.execute(
                    select(LoginAttempt)
                    .where(
                        LoginAttempt.email == email,
                        LoginAttempt.success == True,
                        LoginAttempt.created_at >= oldest_failed_attempt.created_at,
                    )
                    .order_by(LoginAttempt.created_at.desc())
                    .limit(1)
                )
                successful_attempt = result.scalar_one_or_none()

                if successful_attempt:
                    # There was a successful login after the failed attempts
                    return False, None

            # Account is locked - calculate when it will unlock
            # Use the timestamp of the oldest failed attempt in the window
            lockout_start = failed_attempts[-1].created_at
            locked_until = lockout_start + timedelta(
                minutes=self.ACCOUNT_LOCKOUT_DURATION_MINUTES
            )

            # Check if lockout has expired
            if datetime.utcnow() >= locked_until:
                logger.info(f"Account lockout expired for {email}")
                return False, None

            logger.warning(
                f"Account locked for {email} until {locked_until} "
                f"({len(failed_attempts)} failed attempts)"
            )
            return True, locked_until

        except Exception as e:
            logger.error(f"Error checking account lockout: {e}")
            # In case of error, don't lock the account
            return False, None

    async def check_account_lockout(
        self,
        db: AsyncSession,
        email: str,
    ) -> None:
        """
        Check if an account is locked and raise an error if it is.

        Args:
            db: Database session
            email: Email address to check

        Raises:
            ValueError: If account is currently locked

        Example:
            >>> auth = AuthService()
            >>> await auth.check_account_lockout(db, "john@example.com")
            >>> # Raises ValueError if account is locked
        """
        is_locked, locked_until = await self.is_account_locked(db, email)

        if is_locked and locked_until:
            minutes_remaining = int((locked_until - datetime.utcnow()).total_seconds() / 60)
            logger.warning(f"Login attempt blocked for locked account: {email}")
            raise ValueError(
                f"Account is temporarily locked due to too many failed login attempts. "
                f"Please try again in {minutes_remaining} minutes."
            )

    async def check_login_anomalies(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Check for login anomalies for a user.

        This method analyzes recent login attempts to detect suspicious patterns
        such as brute force attacks, credential stuffing, geographic impossibilities,
        and other security concerns.

        Args:
            db: Database session
            user_id: User ID to check
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with anomaly detection results including:
                - has_anomaly: Boolean indicating if anomalies were detected
                - anomalies: List of detected anomalies with details
                - risk_score: Overall risk score (0-100)
                - recommendations: List of recommended actions

        Example:
            >>> auth = AuthService()
            >>> result = await auth.check_login_anomalies(db, user_id)
            >>> if result["has_anomaly"]:
            ...     print(f"Risk score: {result['risk_score']}")
            ...     for rec in result["recommendations"]:
            ...         print(f"- {rec}")
        """
        try:
            # Import here to avoid circular dependency
            from services.session_analytics_service import get_session_analytics_service

            analytics_service = get_session_analytics_service()
            result = await analytics_service.detect_anomaly(str(user_id), days=days)

            # Log high-risk anomalies
            if result.get("risk_score", 0) >= 70:
                logger.error(
                    f"High-risk login anomalies detected for user {user_id}: "
                    f"risk_score={result['risk_score']}, "
                    f"anomalies={len(result.get('anomalies', []))}"
                )
            elif result.get("risk_score", 0) >= 40:
                logger.warning(
                    f"Medium-risk login anomalies detected for user {user_id}: "
                    f"risk_score={result['risk_score']}"
                )

            return result

        except Exception as e:
            logger.error(f"Error checking login anomalies for user {user_id}: {e}", exc_info=True)
            return {
                "has_anomaly": False,
                "anomalies": [],
                "risk_score": 0,
                "recommendations": [],
                "error": str(e),
            }


def get_auth_service() -> AuthService:
    """
    Get or create global authentication service instance.

    Returns:
        Global AuthService instance

    Example:
        >>> auth = get_auth_service()
        >>> user = await auth.register_user(db, email, password, name)
    """
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
        logger.info("AuthService instance created")
    return _auth_service
