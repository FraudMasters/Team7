"""
Session service for managing user sessions and authentication state.

This module provides session management functionality including session creation,
validation, revocation, and cleanup. It supports multiple concurrent sessions per
user with device tracking, IP logging, and remote logout capabilities.

The session service supports:
- Creating sessions with device fingerprinting and IP tracking
- Validating sessions with expiration and idle timeout checking
- Revoking individual sessions or all user sessions
- Listing active sessions with device information
- Automatic cleanup of expired and idle sessions
- Session activity tracking for security monitoring
- Configurable timeout types (idle, absolute, remember-me)
- Session statistics and configuration management
- Graceful handling of database errors

Session token format: Cryptographically secure random string (256-bit)
Session TTL: Configurable with multiple timeout strategies
  - Idle timeout: Revoke sessions after inactivity (default: 30 minutes)
  - Absolute timeout: Maximum session lifetime (default: 24 hours)
  - Remember-me: Extended sessions for persistent login (default: 30 days)
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
    automatic database management, security best practices, comprehensive
    error handling, and configurable timeout strategies.

    Attributes:
        default_ttl_hours: Default session time-to-live in hours
        cleanup_batch_size: Number of sessions to delete per cleanup batch
        max_sessions_per_user: Maximum active sessions per user (0 = unlimited)
        idle_timeout_minutes: Inactivity timeout in minutes (default: 30)
        absolute_timeout_hours: Absolute session timeout in hours (default: 24)
        remember_me_ttl_days: Remember-me session TTL in days (default: 30)

    Example:
        >>> service = SessionService()
        >>> # Create a regular session
        >>> session = await service.create_session(
        ...     user_id="user-123",
        ...     user_agent="Mozilla/5.0...",
        ...     ip_address="192.168.1.1"
        ... )
        >>> # Create a remember-me session
        >>> session = await service.create_session(
        ...     user_id="user-123",
        ...     user_agent="Mozilla/5.0...",
        ...     ip_address="192.168.1.1",
        ...     remember_me=True
        ... )
        >>> # Validate session (checks idle timeout)
        >>> is_valid = await service.validate_session(session.token)
        >>> # Get session statistics
        >>> stats = await service.get_session_statistics(user_id="user-123")
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

    # Session timeout types
    TIMEOUT_TYPE_IDLE = "idle"  # Inactivity timeout
    TIMEOUT_TYPE_ABSOLUTE = "absolute"  # Absolute expiration
    TIMEOUT_TYPE_REMEMBER_ME = "remember_me"  # Extended timeout

    def __init__(
        self,
        default_ttl_hours: Optional[int] = None,
        cleanup_batch_size: Optional[int] = None,
        max_sessions_per_user: Optional[int] = None,
        idle_timeout_minutes: Optional[int] = None,
        absolute_timeout_hours: Optional[int] = None,
        remember_me_ttl_days: Optional[int] = None,
    ) -> None:
        """
        Initialize the session service with configuration.

        Args:
            default_ttl_hours: Default session TTL in hours (defaults to 24)
            cleanup_batch_size: Sessions to delete per cleanup batch (defaults to 100)
            max_sessions_per_user: Max active sessions per user (defaults to 10)
            idle_timeout_minutes: Inactivity timeout in minutes (defaults to 30)
            absolute_timeout_hours: Absolute session timeout in hours (defaults to 24)
            remember_me_ttl_days: Remember-me session TTL in days (defaults to 30)
        """
        settings = get_settings()

        self.default_ttl_hours = default_ttl_hours or 24
        self.cleanup_batch_size = cleanup_batch_size or 100
        self.max_sessions_per_user = max_sessions_per_user or 10
        self.idle_timeout_minutes = idle_timeout_minutes or 30
        self.absolute_timeout_hours = absolute_timeout_hours or 24
        self.remember_me_ttl_days = remember_me_ttl_days or 30

        logger.info(
            f"SessionService initialized (ttl={self.default_ttl_hours}h, "
            f"max_sessions={self.max_sessions_per_user}, "
            f"idle_timeout={self.idle_timeout_minutes}m, "
            f"absolute_timeout={self.absolute_timeout_hours}h, "
            f"remember_me_ttl={self.remember_me_ttl_days}d)"
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
        remember_me: bool = False,
        timeout_type: Optional[str] = None,
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
            remember_me: Whether to create a long-lived "remember me" session
            timeout_type: Timeout type (idle, absolute, remember_me) - auto-determined if None

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
            ...     ip_address="192.168.1.1",
            ...     remember_me=True
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

        # Determine timeout type
        if timeout_type is None:
            if remember_me:
                timeout_type = self.TIMEOUT_TYPE_REMEMBER_ME
            else:
                timeout_type = self.TIMEOUT_TYPE_ABSOLUTE

        # Calculate expiration based on timeout type
        if ttl_hours:
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        elif timeout_type == self.TIMEOUT_TYPE_REMEMBER_ME:
            expires_at = datetime.utcnow() + timedelta(days=self.remember_me_ttl_days)
        elif timeout_type == self.TIMEOUT_TYPE_ABSOLUTE:
            expires_at = datetime.utcnow() + timedelta(hours=self.absolute_timeout_hours)
        else:
            expires_at = datetime.utcnow() + timedelta(hours=self.default_ttl_hours)

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

    def _is_session_idle_expired(self, session: SessionModel) -> bool:
        """
        Check if session has exceeded idle timeout.

        Args:
            session: Session object to check

        Returns:
            True if session has been idle too long, False otherwise

        Example:
            >>> service = SessionService()
            >>> session = await service.get_session("token")
            >>> if service._is_session_idle_expired(session):
            ...     print("Session is idle expired")
        """
        if not session.last_activity_at:
            return False

        idle_duration = datetime.utcnow() - session.last_activity_at
        idle_threshold = timedelta(minutes=self.idle_timeout_minutes)

        return idle_duration > idle_threshold

    async def validate_session(self, token: str, check_idle_timeout: bool = True) -> bool:
        """
        Validate a session token.

        Checks if the session exists, is active, not expired, and not idle.
        Also updates last_activity_at timestamp.

        Args:
            token: Session token to validate
            check_idle_timeout: Whether to check for idle timeout (default: True)

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

        # Check if session is valid (active and not expired)
        if not session.is_valid():
            reason = "revoked" if not session.is_active else "expired"
            logger.debug(f"Session validation failed: session is {reason}")
            return False

        # Check idle timeout
        if check_idle_timeout and self._is_session_idle_expired(session):
            logger.debug(f"Session {session.id} validation failed: idle timeout")
            # Revoke the session due to idle timeout
            await self.revoke_session(token, reason=self.REASON_TIMEOUT)
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

    async def cleanup_idle_sessions(self) -> int:
        """
        Revoke sessions that have exceeded the idle timeout.

        Returns:
            Number of sessions revoked

        Example:
            >>> service = SessionService()
            >>> revoked = await service.cleanup_idle_sessions()
            >>> print(f"Revoked {revoked} idle sessions")
        """
        idle_threshold = datetime.utcnow() - timedelta(minutes=self.idle_timeout_minutes)

        async with async_session_maker() as db:
            try:
                # Find idle sessions
                result = await db.execute(
                    select(SessionModel)
                    .where(
                        and_(
                            SessionModel.is_active == True,
                            SessionModel.last_activity_at < idle_threshold,
                        )
                    )
                )
                idle_sessions = result.scalars().all()

                # Revoke idle sessions
                revoked_count = 0
                for session in idle_sessions:
                    session.is_active = False
                    session.revoked_at = datetime.utcnow()
                    session.revoke_reason = self.REASON_TIMEOUT
                    db.add(session)
                    revoked_count += 1

                await db.commit()

                if revoked_count > 0:
                    logger.info(
                        f"Cleanup: revoked {revoked_count} idle sessions "
                        f"(idle_timeout={self.idle_timeout_minutes}m)"
                    )

                return revoked_count

            except Exception as e:
                await db.rollback()
                logger.error(f"Error cleaning up idle sessions: {e}", exc_info=True)
                return 0

    async def cleanup_expired(self, older_than_hours: int = 1) -> int:
        """
        Delete expired and revoked sessions from the database.

        Also revokes idle sessions before deletion.

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

        # First, revoke idle sessions
        await self.cleanup_idle_sessions()

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

    def get_session_config(self) -> Dict[str, Any]:
        """
        Get current session service configuration.

        Returns:
            Dictionary with current configuration values

        Example:
            >>> service = SessionService()
            >>> config = service.get_session_config()
            >>> print(config["idle_timeout_minutes"])
        """
        return {
            "default_ttl_hours": self.default_ttl_hours,
            "idle_timeout_minutes": self.idle_timeout_minutes,
            "absolute_timeout_hours": self.absolute_timeout_hours,
            "remember_me_ttl_days": self.remember_me_ttl_days,
            "max_sessions_per_user": self.max_sessions_per_user,
            "cleanup_batch_size": self.cleanup_batch_size,
        }

    async def get_session_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive session statistics.

        Args:
            user_id: Optional user ID to filter statistics (None for global stats)

        Returns:
            Dictionary with session statistics

        Example:
            >>> service = SessionService()
            >>> stats = await service.get_session_statistics(user_id="user-123")
            >>> print(stats["active_sessions"])
        """
        async with async_session_maker() as db:
            try:
                # Build base query
                base_query = select(SessionModel)
                if user_id:
                    base_query = base_query.where(SessionModel.user_id == user_id)

                # Get all sessions
                result = await db.execute(base_query)
                sessions = result.scalars().all()

                # Calculate idle sessions
                idle_threshold = datetime.utcnow() - timedelta(minutes=self.idle_timeout_minutes)
                idle_sessions = sum(
                    1 for s in sessions
                    if s.is_active and s.last_activity_at < idle_threshold
                )

                stats = {
                    "user_id": user_id,
                    "total_sessions": len(sessions),
                    "active_sessions": sum(1 for s in sessions if s.is_active),
                    "revoked_sessions": sum(1 for s in sessions if not s.is_active),
                    "expired_sessions": sum(1 for s in sessions if s.is_expired()),
                    "idle_sessions": idle_sessions,
                    "device_types": {},
                    "locations": {},
                }

                # Device distribution
                for session in sessions:
                    device_type = session.device_type or "unknown"
                    stats["device_types"][device_type] = stats["device_types"].get(device_type, 0) + 1

                # Location distribution
                for session in sessions:
                    if session.location:
                        stats["locations"][session.location] = stats["locations"].get(session.location, 0) + 1

                logger.debug(f"Session statistics computed: {stats}")
                return stats

            except Exception as e:
                logger.error(f"Error computing session statistics: {e}", exc_info=True)
                return {
                    "user_id": user_id,
                    "error": str(e),
                }

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
            "idle_sessions": 0,
            "total_sessions": 0,
            "config": self.get_session_config(),
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

                # Count idle sessions
                idle_threshold = datetime.utcnow() - timedelta(minutes=self.idle_timeout_minutes)
                stmt = select(SessionModel).where(
                    and_(
                        SessionModel.is_active == True,
                        SessionModel.last_activity_at < idle_threshold,
                    )
                )
                idle_result = await db.execute(stmt)
                result["idle_sessions"] = len(idle_result.scalars().all())

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
