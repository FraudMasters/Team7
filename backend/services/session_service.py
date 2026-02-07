"""
Session service for managing user sessions and authentication state.

This module provides session management functionality including session creation,
validation, revocation, and cleanup. It supports multiple concurrent sessions per
user with device tracking, IP logging, and remote logout capabilities.

The session service supports:
- Creating sessions with device fingerprinting and IP tracking
- Validating sessions and checking expiration
- Revoking individual sessions or all user sessions
- Listing active sessions with device information
- Automatic cleanup of expired sessions
- Session activity tracking for security monitoring
- Graceful handling of database errors

Session token format: Cryptographically secure random string (256-bit)
Session TTL: Configurable (default 24 hours)
Device tracking: User-Agent parsing for device type detection
IP location: Optional geolocation from IP address
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models.session import Session as SessionModel

logger = logging.getLogger(__name__)

# Global session service instance
_session_service: Optional["SessionService"] = None


class SessionService:
    """
    Session service for managing user sessions and authentication state.

    This class provides a high-level interface for session operations with
    automatic database management, security best practices, and comprehensive
    error handling.

    Attributes:
        default_ttl_hours: Default session time-to-live in hours
        cleanup_batch_size: Number of sessions to delete per cleanup batch
        max_sessions_per_user: Maximum active sessions per user (0 = unlimited)

    Example:
        >>> service = SessionService()
        >>> # Create a session
        >>> session = await service.create_session(
        ...     user_id="user-123",
        ...     token="jwt-token-here",
        ...     user_agent="Mozilla/5.0...",
        ...     ip_address="192.168.1.1"
        ... )
        >>> # Validate session
        >>> is_valid = await service.validate_session(session.token)
        >>> # Revoke session
        >>> await service.revoke_session(session.token, reason="user_logout")
    """

    # Device type constants
    DEVICE_TYPE_DESKTOP = "desktop"
    DEVICE_TYPE_MOBILE = "mobile"
    DEVICE_TYPE_TABLET = "tablet"
    DEVICE_TYPE_UNKNOWN = "unknown"

    # Revoke reason constants
    REASON_USER_LOGOUT = "user_logout"
    REASON_SECURITY_RESET = "security_reset"
    REASON_ADMIN_ACTION = "admin_action"
    REASON_TIMEOUT = "timeout"
    REASON_SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # Session token length (bytes)
    TOKEN_LENGTH = 32  # 256 bits

    def __init__(
        self,
        default_ttl_hours: Optional[int] = None,
        cleanup_batch_size: Optional[int] = None,
        max_sessions_per_user: Optional[int] = None,
    ) -> None:
        """
        Initialize the session service with configuration.

        Args:
            default_ttl_hours: Default session TTL in hours (defaults to 24)
            cleanup_batch_size: Sessions to delete per cleanup batch (defaults to 100)
            max_sessions_per_user: Max active sessions per user (defaults to 10)
        """
        settings = get_settings()

        self.default_ttl_hours = default_ttl_hours or 24
        self.cleanup_batch_size = cleanup_batch_size or 100
        self.max_sessions_per_user = max_sessions_per_user or 10

        logger.info(
            f"SessionService initialized (ttl={self.default_ttl_hours}h, "
            f"max_sessions={self.max_sessions_per_user})"
        )

    def _generate_token(self) -> str:
        """
        Generate a cryptographically secure session token.

        Returns:
            URL-safe random token string

        Example:
            >>> service = SessionService()
            >>> token = service._generate_token()
            >>> print(len(token))  # 43 characters (base64 of 32 bytes)
        """
        token = secrets.token_urlsafe(self.TOKEN_LENGTH)
        logger.debug(f"Generated session token (length={len(token)})")
        return token

    def _hash_token(self, token: str) -> str:
        """
        Hash a session token for secure storage.

        Uses SHA-256 to create a one-way hash of the token for storage.
        This prevents token leakage if the database is compromised.

        Args:
            token: Plain session token

        Returns:
            SHA-256 hash of the token as hex string

        Example:
            >>> service = SessionService()
            >>> hashed = service._hash_token("my-token")
            >>> print(hashed)  # 64 character hex string
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def _parse_device_type(self, user_agent: Optional[str]) -> str:
        """
        Parse device type from user agent string.

        Args:
            user_agent: User-Agent header value

        Returns:
            Device type: desktop, mobile, tablet, or unknown

        Example:
            >>> service = SessionService()
            >>> service._parse_device_type("Mozilla/5.0 (iPhone; CPU iPhone OS...")
            'mobile'
        """
        if not user_agent:
            return self.DEVICE_TYPE_UNKNOWN

        user_agent_lower = user_agent.lower()

        # Check for mobile devices
        mobile_keywords = ["iphone", "android", "mobile", "opera mini", "windows phone"]
        if any(keyword in user_agent_lower for keyword in mobile_keywords):
            return self.DEVICE_TYPE_MOBILE

        # Check for tablets
        tablet_keywords = ["ipad", "tablet", "kindle"]
        if any(keyword in user_agent_lower for keyword in tablet_keywords):
            return self.DEVICE_TYPE_TABLET

        # Default to desktop
        return self.DEVICE_TYPE_DESKTOP

    def _generate_device_name(self, user_agent: Optional[str]) -> Optional[str]:
        """
        Generate user-friendly device name from user agent.

        Args:
            user_agent: User-Agent header value

        Returns:
            Human-readable device name or None

        Example:
            >>> service = SessionService()
            >>> service._generate_device_name("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            'Chrome on Windows'
        """
        if not user_agent:
            return None

        try:
            # Extract browser
            browser = "Unknown Browser"
            if "Chrome" in user_agent and "Edg" not in user_agent:
                browser = "Chrome"
            elif "Safari" in user_agent and "Chrome" not in user_agent:
                browser = "Safari"
            elif "Firefox" in user_agent:
                browser = "Firefox"
            elif "Edg" in user_agent:
                browser = "Edge"
            elif "Opera" in user_agent:
                browser = "Opera"

            # Extract OS
            os = "Unknown OS"
            if "Windows" in user_agent:
                os = "Windows"
            elif "Macintosh" in user_agent or "Mac OS X" in user_agent:
                os = "macOS"
            elif "Linux" in user_agent:
                os = "Linux"
            elif "iPhone" in user_agent or "iPad" in user_agent:
                os = "iOS"
            elif "Android" in user_agent:
                os = "Android"

            return f"{browser} on {os}"

        except Exception as e:
            logger.warning(f"Error parsing device name: {e}")
            return None

    async def create_session(
        self,
        user_id: str,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        location: Optional[str] = None,
        ttl_hours: Optional[int] = None,
    ) -> Optional[SessionModel]:
        """
        Create a new user session.

        Args:
            user_id: User ID who owns this session
            token: Session token (auto-generated if not provided)
            user_agent: User-Agent header for device fingerprinting
            ip_address: IP address where session was created
            location: Optional location derived from IP
            ttl_hours: Time-to-live in hours (defaults to instance default)

        Returns:
            Created Session object or None if creation failed

        Raises:
            ValueError: If user_id is invalid
            Exception: If database operation fails

        Example:
            >>> service = SessionService()
            >>> session = await service.create_session(
            ...     user_id="user-123",
            ...     user_agent="Mozilla/5.0...",
            ...     ip_address="192.168.1.1"
            ... )
            >>> print(session.device_name)  # "Chrome on Windows"
        """
        if not user_id:
            logger.error("Cannot create session: user_id is required")
            raise ValueError("user_id is required")

        # Generate token if not provided
        if not token:
            token = self._generate_token()

        # Hash token for storage
        token_hash = self._hash_token(token)

        # Calculate expiration
        ttl_hours = ttl_hours or self.default_ttl_hours
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours) if ttl_hours > 0 else None

        # Parse device info
        device_type = self._parse_device_type(user_agent)
        device_name = self._generate_device_name(user_agent)

        async with async_session_maker() as db:
            try:
                # Check max sessions limit
                if self.max_sessions_per_user > 0:
                    result = await db.execute(
                        select(SessionModel)
                        .where(
                            and_(
                                SessionModel.user_id == user_id,
                                SessionModel.is_active == True,
                            )
                        )
                        .order_by(SessionModel.created_at.desc())
                    )
                    active_sessions = result.scalars().all()

                    # Revoke oldest sessions if limit exceeded
                    if len(active_sessions) >= self.max_sessions_per_user:
                        sessions_to_revoke = active_sessions[self.max_sessions_per_user - 1 :]
                        for session in sessions_to_revoke:
                            session.is_active = False
                            session.revoked_at = datetime.utcnow()
                            session.revoke_reason = self.REASON_TIMEOUT

                        logger.info(
                            f"Revoked {len(sessions_to_revoke)} old sessions for user {user_id} "
                            f"(limit: {self.max_sessions_per_user})"
                        )

                # Create new session
                session = SessionModel(
                    user_id=user_id,
                    token=token_hash,
                    device_name=device_name,
                    device_type=device_type,
                    user_agent=user_agent,
                    ip_address=ip_address,
                    location=location,
                    is_active=True,
                    expires_at=expires_at,
                )

                db.add(session)
                await db.commit()
                await db.refresh(session)

                # Store actual token temporarily for response (not stored in DB)
                session._token = token  # type: ignore

                logger.info(
                    f"Created session for user {user_id} "
                    f"(device={device_name}, ip={ip_address}, expires={expires_at})"
                )

                return session

            except Exception as e:
                await db.rollback()
                logger.error(f"Error creating session for user {user_id}: {e}", exc_info=True)
                raise

    async def get_session(self, token: str) -> Optional[SessionModel]:
        """
        Retrieve a session by token.

        Args:
            token: Session token

        Returns:
            Session object or None if not found

        Example:
            >>> service = SessionService()
            >>> session = await service.get_session("session-token")
            >>> if session:
            ...     print(session.device_name)
        """
        token_hash = self._hash_token(token)

        async with async_session_maker() as db:
            try:
                result = await db.execute(
                    select(SessionModel).where(SessionModel.token == token_hash)
                )
                session = result.scalar_one_or_none()

                if session:
                    logger.debug(f"Retrieved session {session.id}")
                else:
                    logger.debug(f"Session not found for token")

                return session

            except Exception as e:
                logger.error(f"Error retrieving session: {e}", exc_info=True)
                return None

    async def validate_session(self, token: str) -> bool:
        """
        Validate a session token.

        Checks if the session exists, is active, and not expired.
        Also updates last_activity_at timestamp.

        Args:
            token: Session token to validate

        Returns:
            True if session is valid, False otherwise

        Example:
            >>> service = SessionService()
            >>> is_valid = await service.validate_session("session-token")
            >>> if is_valid:
            ...     print("Session is valid")
        """
        session = await self.get_session(token)

        if not session:
            logger.debug("Session validation failed: session not found")
            return False

        # Check if session is valid
        if not session.is_valid():
            reason = "revoked" if not session.is_active else "expired"
            logger.debug(f"Session validation failed: session is {reason}")
            return False

        # Update activity timestamp
        async with async_session_maker() as db:
            try:
                session.last_activity_at = datetime.utcnow()
                db.add(session)
                await db.commit()

                logger.debug(f"Session {session.id} validated and activity updated")
                return True

            except Exception as e:
                await db.rollback()
                logger.error(f"Error updating session activity: {e}", exc_info=True)
                return False

    async def revoke_session(
        self,
        token: str,
        reason: str = REASON_USER_LOGOUT,
    ) -> bool:
        """
        Revoke a session by token.

        Args:
            token: Session token to revoke
            reason: Reason for revocation (default: user_logout)

        Returns:
            True if session was revoked, False if not found or already revoked

        Example:
            >>> service = SessionService()
            >>> success = await service.revoke_session(
            ...     "session-token",
            ...     reason="user_logout"
            ... )
        """
        session = await self.get_session(token)

        if not session:
            logger.debug(f"Cannot revoke session: token not found")
            return False

        if not session.is_active:
            logger.debug(f"Session {session.id} already revoked")
            return False

        async with async_session_maker() as db:
            try:
                session.is_active = False
                session.revoked_at = datetime.utcnow()
                session.revoke_reason = reason

                db.add(session)
                await db.commit()

                logger.info(f"Revoked session {session.id} (reason: {reason})")
                return True

            except Exception as e:
                await db.rollback()
                logger.error(f"Error revoking session {session.id}: {e}", exc_info=True)
                return False

    async def revoke_all_sessions(
        self,
        user_id: str,
        reason: str = REASON_SECURITY_RESET,
        exclude_token: Optional[str] = None,
    ) -> int:
        """
        Revoke all sessions for a user.

        Args:
            user_id: User ID whose sessions should be revoked
            reason: Reason for revocation (default: security_reset)
            exclude_token: Optional token to exclude from revocation (current session)

        Returns:
            Number of sessions revoked

        Example:
            >>> service = SessionService()
            >>> # Revoke all sessions except current
            >>> count = await service.revoke_all_sessions(
            ...     user_id="user-123",
            ...     exclude_token="current-token",
            ...     reason="security_reset"
            ... )
        """
        async with async_session_maker() as db:
            try:
                # Build query
                query = select(SessionModel).where(
                    and_(
                        SessionModel.user_id == user_id,
                        SessionModel.is_active == True,
                    )
                )

                # Exclude current session if specified
                if exclude_token:
                    exclude_hash = self._hash_token(exclude_token)
                    query = query.where(SessionModel.token != exclude_hash)

                result = await db.execute(query)
                sessions = result.scalars().all()

                # Revoke all sessions
                revoked_count = 0
                for session in sessions:
                    session.is_active = False
                    session.revoked_at = datetime.utcnow()
                    session.revoke_reason = reason
                    db.add(session)
                    revoked_count += 1

                await db.commit()

                logger.info(
                    f"Revoked {revoked_count} sessions for user {user_id} (reason: {reason})"
                )

                return revoked_count

            except Exception as e:
                await db.rollback()
                logger.error(f"Error revoking sessions for user {user_id}: {e}", exc_info=True)
                return 0

    async def get_active_sessions(self, user_id: str) -> List[SessionModel]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID to get sessions for

        Returns:
            List of active Session objects

        Example:
            >>> service = SessionService()
            >>> sessions = await service.get_active_sessions("user-123")
            >>> for session in sessions:
            ...     print(f"{session.device_name} - {session.ip_address}")
        """
        async with async_session_maker() as db:
            try:
                result = await db.execute(
                    select(SessionModel)
                    .where(
                        and_(
                            SessionModel.user_id == user_id,
                            SessionModel.is_active == True,
                        )
                    )
                    .order_by(SessionModel.last_activity_at.desc())
                )
                sessions = result.scalars().all()

                logger.debug(f"Retrieved {len(sessions)} active sessions for user {user_id}")
                return sessions

            except Exception as e:
                logger.error(f"Error retrieving sessions for user {user_id}: {e}", exc_info=True)
                return []

    async def update_activity(self, token: str) -> bool:
        """
        Update the last activity timestamp for a session.

        Args:
            token: Session token

        Returns:
            True if activity was updated, False if session not found

        Example:
            >>> service = SessionService()
            >>> await service.update_activity("session-token")
        """
        session = await self.get_session(token)

        if not session:
            return False

        async with async_session_maker() as db:
            try:
                session.last_activity_at = datetime.utcnow()
                db.add(session)
                await db.commit()

                logger.debug(f"Updated activity for session {session.id}")
                return True

            except Exception as e:
                await db.rollback()
                logger.error(f"Error updating session activity: {e}", exc_info=True)
                return False

    async def cleanup_expired(self, older_than_hours: int = 1) -> int:
        """
        Delete expired and revoked sessions from the database.

        Args:
            older_than_hours: Only delete sessions that were expired/revoked
                more than this many hours ago (default: 1)

        Returns:
            Number of sessions deleted

        Example:
            >>> service = SessionService()
            >>> deleted = await service.cleanup_expired(older_than_hours=24)
            >>> print(f"Deleted {deleted} expired sessions")
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

        async with async_session_maker() as db:
            try:
                # Delete expired sessions
                stmt = delete(SessionModel).where(
                    and_(
                        SessionModel.expires_at < cutoff_time,
                        SessionModel.expires_at.isnot(None),
                    )
                )
                result = await db.execute(stmt)
                expired_count = result.rowcount

                # Delete revoked sessions
                stmt = delete(SessionModel).where(
                    and_(
                        SessionModel.is_active == False,
                        SessionModel.revoked_at < cutoff_time,
                        SessionModel.revoked_at.isnot(None),
                    )
                )
                result = await db.execute(stmt)
                revoked_count = result.rowcount

                await db.commit()

                total_deleted = expired_count + revoked_count
                logger.info(
                    f"Cleanup: deleted {total_deleted} sessions "
                    f"({expired_count} expired, {revoked_count} revoked)"
                )

                return total_deleted

            except Exception as e:
                await db.rollback()
                logger.error(f"Error cleaning up sessions: {e}", exc_info=True)
                return 0

    async def health_check(self) -> Dict[str, Any]:
        """
        Check session service health and get statistics.

        Returns:
            Dictionary with health status and statistics

        Example:
            >>> service = SessionService()
            >>> health = await service.health_check()
            >>> print(health)
            {'status': 'healthy', 'active_sessions': 42, ...}
        """
        result = {
            "status": "unhealthy",
            "active_sessions": 0,
            "expired_sessions": 0,
            "total_sessions": 0,
            "error": None,
        }

        async with async_session_maker() as db:
            try:
                # Count active sessions
                stmt = select(SessionModel).where(SessionModel.is_active == True)
                active_result = await db.execute(stmt)
                result["active_sessions"] = len(active_result.scalars().all())

                # Count expired sessions
                stmt = select(SessionModel).where(
                    and_(
                        SessionModel.is_active == True,
                        SessionModel.expires_at < datetime.utcnow(),
                        SessionModel.expires_at.isnot(None),
                    )
                )
                expired_result = await db.execute(stmt)
                result["expired_sessions"] = len(expired_result.scalars().all())

                # Count total sessions
                stmt = select(SessionModel)
                total_result = await db.execute(stmt)
                result["total_sessions"] = len(total_result.scalars().all())

                result["status"] = "healthy"
                logger.debug(f"Health check: {result}")

            except Exception as e:
                result["error"] = str(e)
                logger.error(f"Session service health check failed: {e}", exc_info=True)

        return result


def get_session_service() -> SessionService:
    """
    Get or create global session service instance.

    Returns:
        Global SessionService instance

    Example:
        >>> service = get_session_service()
        >>> session = await service.create_session(user_id="user-123")
    """
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
