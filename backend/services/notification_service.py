"""
Notification Service for real-time user notifications

This module provides a comprehensive notification system with support for:
- Creating notifications of various types
- Aggregating notifications to prevent spam
- Delivering notifications via multiple channels (in-app, email, WebSocket)
- Managing user notification preferences
- Tracking delivery status and retry logic

The service coordinates between the database models, Celery background tasks,
and WebSocket broadcasters to deliver notifications in real-time.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Notification, NotificationPreference, NotificationType
from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)

# Global notification service instance
_notification_service: Optional["NotificationService"] = None


class NotificationService:
    """
    Service for creating, aggregating, and delivering notifications.

    This service provides methods for managing the complete notification lifecycle:
    - Creating notifications with proper type, recipient, and content
    - Aggregating similar notifications to prevent spam
    - Checking user preferences before delivery
    - Marking notifications as read/unread
    - Querying notifications with filters

    Attributes:
        None (service is stateless)

    Example:
        >>> service = NotificationService()
        >>> notification = await service.create_notification(
        ...     db=session,
        ...     recipient_id=user_uuid,
        ...     notification_type=NotificationType.CANDIDATE_STAGE_CHANGED,
        ...     title="Candidate Moved to Interview",
        ...     message="John Doe has been moved to the interview stage",
        ...     candidate_id=candidate_uuid,
        ...     vacancy_id=vacancy_uuid
        ... )
    """

    # Aggregation time window (seconds)
    # Notifications of the same type within this window will be aggregated
    AGGREGATION_WINDOW = 300  # 5 minutes

    # Maximum notifications to aggregate into one
    MAX_AGGREGATION_COUNT = 10

    def __init__(self):
        """Initialize the notification service."""
        logger.info("NotificationService initialized")

    async def create_notification(
        self,
        db: AsyncSession,
        recipient_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        candidate_id: Optional[UUID] = None,
        vacancy_id: Optional[UUID] = None,
        action_url: Optional[str] = None,
        check_preferences: bool = True,
        aggregate: bool = True,
    ) -> Optional[Notification]:
        """
        Create a new notification.

        This method creates a notification record in the database after checking
        user preferences. If aggregation is enabled, it may group this notification
        with similar recent notifications instead of creating a duplicate.

        Args:
            db: Database session
            recipient_id: UUID of the recipient (recruiter/user)
            notification_type: Type of notification from NotificationType enum
            title: Short title for the notification
            message: Detailed message content
            data: Optional JSON data with additional context
            candidate_id: Optional related candidate UUID
            vacancy_id: Optional related vacancy UUID
            action_url: Optional URL for the notification's action link
            check_preferences: Whether to check user preferences before creating
            aggregate: Whether to aggregate similar notifications

        Returns:
            Created Notification object, or None if preferences block delivery
            or if aggregated into existing notification

        Raises:
            ValueError: If recipient_id is invalid
            Exception: For database errors
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Check user preferences if enabled
            if check_preferences:
                can_deliver = await self._check_user_preferences(
                    db, recipient_id, notification_type
                )
                if not can_deliver:
                    logger.info(
                        f"Notification blocked by preferences: "
                        f"user={recipient_id}, type={notification_type}"
                    )
                    return None

            # Try to aggregate with existing notifications if enabled
            if aggregate:
                aggregated = await self._try_aggregate_notification(
                    db,
                    recipient_id,
                    notification_type,
                    candidate_id,
                    vacancy_id,
                    title,
                    message,
                )
                if aggregated:
                    logger.info(
                        f"Notification aggregated into existing: "
                        f"user={recipient_id}, type={notification_type}"
                    )
                    return aggregated

            # Create new notification
            notification = Notification(
                recipient_id=recipient_id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data or {},
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                action_url=action_url,
                is_read=False,
                delivery_failed=False,
                retry_count=0,
            )

            db.add(notification)
            await db.commit()
            await db.refresh(notification)

            # Record metrics
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._record_creation_metrics(notification_type, duration_ms, success=True)

            logger.info(
                f"Notification created: id={notification.id}, "
                f"type={notification_type}, recipient={recipient_id}"
            )

            return notification

        except Exception as e:
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            self._record_creation_metrics(notification_type, duration_ms, success=False)

            logger.error(
                f"Error creating notification: {e}",
                exc_info=True,
            )
            raise

    async def get_notifications(
        self,
        db: AsyncSession,
        recipient_id: UUID,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """
        Get notifications for a recipient with optional filters.

        Args:
            db: Database session
            recipient_id: UUID of the recipient
            unread_only: If True, only return unread notifications
            notification_type: Optional filter by notification type
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip (for pagination)

        Returns:
            List of Notification objects ordered by created_at DESC
        """
        try:
            query = select(Notification).where(Notification.recipient_id == recipient_id)

            if unread_only:
                query = query.where(Notification.is_read == False)

            if notification_type:
                query = query.where(Notification.notification_type == notification_type)

            query = query.order_by(Notification.created_at.desc())
            query = query.limit(limit).offset(offset)

            result = await db.execute(query)
            notifications = result.scalars().all()

            logger.debug(
                f"Retrieved {len(notifications)} notifications for user={recipient_id}"
            )

            return list(notifications)

        except Exception as e:
            logger.error(f"Error getting notifications: {e}", exc_info=True)
            return []

    async def get_unread_count(self, db: AsyncSession, recipient_id: UUID) -> int:
        """
        Get the count of unread notifications for a recipient.

        Args:
            db: Database session
            recipient_id: UUID of the recipient

        Returns:
            Number of unread notifications
        """
        try:
            query = select(Notification).where(
                and_(
                    Notification.recipient_id == recipient_id,
                    Notification.is_read == False,
                )
            )

            result = await db.execute(query)
            count = len(result.scalars().all())

            return count

        except Exception as e:
            logger.error(f"Error getting unread count: {e}", exc_info=True)
            return 0

    async def mark_as_read(
        self,
        db: AsyncSession,
        notification_id: UUID,
        recipient_id: UUID,
    ) -> Optional[Notification]:
        """
        Mark a notification as read.

        Args:
            db: Database session
            notification_id: UUID of the notification to mark as read
            recipient_id: UUID of the recipient (for authorization)

        Returns:
            Updated Notification object, or None if not found

        Raises:
            ValueError: If notification doesn't belong to recipient
        """
        try:
            query = select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.recipient_id == recipient_id,
                )
            )

            result = await db.execute(query)
            notification = result.scalar_one_or_none()

            if not notification:
                logger.warning(
                    f"Notification not found: id={notification_id}, "
                    f"user={recipient_id}"
                )
                return None

            # Update as read
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)

            await db.commit()
            await db.refresh(notification)

            logger.info(f"Notification marked as read: id={notification_id}")

            return notification

        except Exception as e:
            logger.error(f"Error marking notification as read: {e}", exc_info=True)
            raise

    async def mark_all_as_read(
        self,
        db: AsyncSession,
        recipient_id: UUID,
        notification_type: Optional[NotificationType] = None,
    ) -> int:
        """
        Mark all notifications as read for a recipient.

        Args:
            db: Database session
            recipient_id: UUID of the recipient
            notification_type: Optional filter by notification type

        Returns:
            Number of notifications marked as read
        """
        try:
            query = (
                update(Notification)
                .where(
                    and_(
                        Notification.recipient_id == recipient_id,
                        Notification.is_read == False,
                    )
                )
                .values(is_read=True, read_at=datetime.now(timezone.utc))
            )

            if notification_type:
                query = query.where(Notification.notification_type == notification_type)

            result = await db.execute(query)
            await db.commit()

            count = result.rowcount

            logger.info(
                f"Marked {count} notifications as read for user={recipient_id}"
            )

            return count or 0

        except Exception as e:
            logger.error(f"Error marking all as read: {e}", exc_info=True)
            return 0

    async def delete_notification(
        self,
        db: AsyncSession,
        notification_id: UUID,
        recipient_id: UUID,
    ) -> bool:
        """
        Delete a notification.

        Args:
            db: Database session
            notification_id: UUID of the notification to delete
            recipient_id: UUID of the recipient (for authorization)

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If notification doesn't belong to recipient
        """
        try:
            query = delete(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.recipient_id == recipient_id,
                )
            )

            result = await db.execute(query)
            await db.commit()

            deleted = result.rowcount > 0

            if deleted:
                logger.info(f"Notification deleted: id={notification_id}")
            else:
                logger.warning(
                    f"Notification not found for deletion: id={notification_id}"
                )

            return deleted

        except Exception as e:
            logger.error(f"Error deleting notification: {e}", exc_info=True)
            raise

    async def get_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all notification preferences for a user.

        Args:
            db: Database session
            user_id: UUID of the user

        Returns:
            Dictionary mapping notification types to their preferences
        """
        try:
            query = select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )

            result = await db.execute(query)
            preferences = result.scalars().all()

            prefs_dict = {}
            for pref in preferences:
                prefs_dict[pref.notification_type] = {
                    "email_enabled": pref.email_enabled,
                    "in_app_enabled": pref.in_app_enabled,
                    "push_enabled": pref.push_enabled,
                    "sms_enabled": pref.sms_enabled,
                    "digest_frequency": pref.digest_frequency,
                }

            return prefs_dict

        except Exception as e:
            logger.error(f"Error getting user preferences: {e}", exc_info=True)
            return {}

    async def update_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_type: str,
        preferences: Dict[str, Any],
    ) -> Optional[NotificationPreference]:
        """
        Update or create notification preferences for a user.

        Args:
            db: Database session
            user_id: UUID of the user
            notification_type: Type of notification
            preferences: Dictionary of preferences to update:
                - email_enabled: bool
                - in_app_enabled: bool
                - push_enabled: bool
                - sms_enabled: bool
                - digest_frequency: str (optional)

        Returns:
            Updated or created NotificationPreference object
        """
        try:
            # Get existing preference
            query = select(NotificationPreference).where(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.notification_type == notification_type,
                )
            )

            result = await db.execute(query)
            pref = result.scalar_one_or_none()

            if pref:
                # Update existing
                if "email_enabled" in preferences:
                    pref.email_enabled = preferences["email_enabled"]
                if "in_app_enabled" in preferences:
                    pref.in_app_enabled = preferences["in_app_enabled"]
                if "push_enabled" in preferences:
                    pref.push_enabled = preferences["push_enabled"]
                if "sms_enabled" in preferences:
                    pref.sms_enabled = preferences["sms_enabled"]
                if "digest_frequency" in preferences:
                    pref.digest_frequency = preferences["digest_frequency"]

                await db.commit()
                await db.refresh(pref)

                logger.info(
                    f"Updated notification preference: "
                    f"user={user_id}, type={notification_type}"
                )
            else:
                # Create new
                pref = NotificationPreference(
                    user_id=user_id,
                    notification_type=notification_type,
                    email_enabled=preferences.get("email_enabled", True),
                    in_app_enabled=preferences.get("in_app_enabled", True),
                    push_enabled=preferences.get("push_enabled", False),
                    sms_enabled=preferences.get("sms_enabled", False),
                    digest_frequency=preferences.get("digest_frequency"),
                )

                db.add(pref)
                await db.commit()
                await db.refresh(pref)

                logger.info(
                    f"Created notification preference: "
                    f"user={user_id}, type={notification_type}"
                )

            return pref

        except Exception as e:
            logger.error(f"Error updating preferences: {e}", exc_info=True)
            raise

    async def aggregate_notifications(
        self,
        db: AsyncSession,
        recipient_id: UUID,
        notification_type: NotificationType,
        time_window_seconds: int = AGGREGATION_WINDOW,
    ) -> List[Dict[str, Any]]:
        """
        Aggregate notifications of the same type within a time window.

        This method groups similar notifications to prevent spam and reduce noise.
        For example, multiple "new candidate" notifications can be aggregated
        into a single "5 new candidates" notification.

        Args:
            db: Database session
            recipient_id: UUID of the recipient
            notification_type: Type of notification to aggregate
            time_window_seconds: Time window in seconds to look back

        Returns:
            List of aggregated notification groups with counts and details
        """
        try:
            # Calculate time threshold
            threshold = datetime.now(timezone.utc).replace(
                microsecond=0
            ) - __import__("datetime").timedelta(seconds=time_window_seconds)

            # Query unread notifications of the type within time window
            query = select(Notification).where(
                and_(
                    Notification.recipient_id == recipient_id,
                    Notification.notification_type == notification_type,
                    Notification.is_read == False,
                    Notification.created_at >= threshold,
                )
            ).order_by(Notification.created_at.desc())

            result = await db.execute(query)
            notifications = result.scalars().all()

            if not notifications:
                return []

            # Group by related entities (candidate_id, vacancy_id)
            groups: Dict[tuple, List[Notification]] = {}
            for notif in notifications:
                key = (notif.candidate_id, notif.vacancy_id)
                if key not in groups:
                    groups[key] = []
                groups[key].append(notif)

            # Build aggregation result
            aggregated = []
            for key, group_notifs in groups.items():
                candidate_id, vacancy_id = key

                # Get the most recent notification as the primary
                primary = group_notifs[0]

                aggregated.append(
                    {
                        "notification_type": notification_type,
                        "count": len(group_notifs),
                        "title": primary.title,
                        "message": primary.message,
                        "candidate_id": str(candidate_id) if candidate_id else None,
                        "vacancy_id": str(vacancy_id) if vacancy_id else None,
                        "action_url": primary.action_url,
                        "created_at": primary.created_at.isoformat()
                        if primary.created_at
                        else None,
                        "oldest_created_at": group_notifs[-1].created_at.isoformat()
                        if group_notifs[-1].created_at
                        else None,
                    }
                )

            logger.info(
                f"Aggregated {len(notifications)} notifications into {len(aggregated)} groups "
                f"for user={recipient_id}, type={notification_type}"
            )

            return aggregated

        except Exception as e:
            logger.error(f"Error aggregating notifications: {e}", exc_info=True)
            return []

    async def _check_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_type: NotificationType,
    ) -> bool:
        """
        Check if user has enabled in-app notifications for this type.

        Args:
            db: Database session
            user_id: UUID of the user
            notification_type: Type of notification to check

        Returns:
            True if notification should be delivered, False if blocked
        """
        try:
            query = select(NotificationPreference).where(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.notification_type == notification_type.value,
                )
            )

            result = await db.execute(query)
            pref = result.scalar_one_or_none()

            # If no preference exists, default to enabled
            if pref is None:
                return True

            # Check in_app preference
            return pref.in_app_enabled

        except Exception as e:
            logger.error(f"Error checking preferences: {e}", exc_info=True)
            # Default to enabled on error
            return True

    async def _try_aggregate_notification(
        self,
        db: AsyncSession,
        recipient_id: UUID,
        notification_type: NotificationType,
        candidate_id: Optional[UUID],
        vacancy_id: Optional[UUID],
        title: str,
        message: str,
    ) -> Optional[Notification]:
        """
        Try to aggregate this notification with an existing one.

        Args:
            db: Database session
            recipient_id: UUID of the recipient
            notification_type: Type of notification
            candidate_id: Optional related candidate UUID
            vacancy_id: Optional related vacancy UUID
            title: Notification title
            message: Notification message

        Returns:
            Existing notification if aggregated, None if should create new
        """
        try:
            # Calculate time threshold
            threshold = datetime.now(timezone.utc).replace(
                microsecond=0
            ) - __import__("datetime").timedelta(seconds=self.AGGREGATION_WINDOW)

            # Query for recent similar unread notifications
            query = select(Notification).where(
                and_(
                    Notification.recipient_id == recipient_id,
                    Notification.notification_type == notification_type,
                    Notification.is_read == False,
                    Notification.created_at >= threshold,
                )
            ).order_by(Notification.created_at.desc())

            result = await db.execute(query)
            existing = result.scalars().first()

            # If found a recent similar notification, return it for aggregation
            if existing:
                # Update the message to indicate multiple notifications
                if existing.data is None:
                    existing.data = {}
                existing.data["aggregate_count"] = existing.data.get("aggregate_count", 1) + 1
                existing.data["last_message"] = message

                await db.commit()
                await db.refresh(existing)

                return existing

            return None

        except Exception as e:
            logger.error(f"Error in aggregation check: {e}", exc_info=True)
            return None

    def _record_creation_metrics(
        self,
        notification_type: NotificationType,
        duration_ms: float,
        success: bool,
    ) -> None:
        """
        Record notification creation metrics.

        Args:
            notification_type: Type of notification created
            duration_ms: Time taken to create notification
            success: Whether creation was successful
        """
        try:
            registry = get_metrics_registry()
            registry.record_notification_event(
                notification_type=notification_type.value,
                action="created",
                success=success,
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.debug(f"Failed to record metrics: {e}")


def get_notification_service() -> NotificationService:
    """
    Get or create the global notification service instance.

    Returns:
        NotificationService singleton instance
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
