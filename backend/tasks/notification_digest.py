"""
Notification digest tasks for aggregating and sending periodic email digests.

This module provides Celery tasks for aggregating notifications over time periods
(hourly, daily, weekly) and sending them as digest emails to users based on their
notification preferences.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models import Notification, NotificationPreference, Recruiter
from models.notification_preference import DigestFrequency

logger = logging.getLogger(__name__)
settings = get_settings()


def format_notification_digest_email(
    recipient_email: str,
    recipient_name: str,
    notifications: List[Dict[str, Any]],
    digest_frequency: str,
) -> Dict[str, Any]:
    """
    Format notification digest email.

    This function formats a digest email containing multiple notifications
    grouped by category/type for a single recipient.

    Args:
        recipient_email: Email address of the recipient
        recipient_name: Name of the recipient
        notifications: List of notification dictionaries containing:
            - id: Notification ID
            - notification_type: Type of notification
            - title: Notification title
            - message: Notification message
            - created_at: Creation timestamp
            - action_url: Optional action URL
            - data: Optional additional data
        digest_frequency: Frequency of the digest (hourly, daily, weekly)

    Returns:
        Dictionary containing email details:
        {
            "subject": "Your Daily Notification Digest",
            "body": "Email body with grouped notifications...",
            "priority": "normal"
        }

    Example:
        >>> notifs = [{"title": "New candidate", "message": "..."}]
        >>> email = format_notification_digest_email(
        ...     "user@example.com", "John", notifs, "daily"
        ... )
        >>> print(email['subject'])
        'Your Daily Notification Digest'
    """
    try:
        logger.info(
            f"Formatting digest email for {recipient_email}: "
            f"{len(notifications)} notifications, frequency={digest_frequency}"
        )

        # Determine frequency label
        frequency_labels = {
            "hourly": "Hourly",
            "daily": "Daily",
            "weekly": "Weekly",
        }
        frequency_label = frequency_labels.get(digest_frequency, "Notification")

        # Group notifications by type
        grouped_notifications: Dict[str, List[Dict[str, Any]]] = {}
        for notif in notifications:
            notif_type = notif.get("notification_type", "general")
            if notif_type not in grouped_notifications:
                grouped_notifications[notif_type] = []
            grouped_notifications[notif_type].append(notif)

        # Build email subject
        subject = f"Your {frequency_label} Notification Digest"

        # Build email body
        body_lines = [
            f"Hello {recipient_name},",
            f"",
            f"Here's your {frequency_label.lower()} summary of {len(notifications)} notification(s)",
            f"",
        ]

        # Add notifications by group
        for notif_type, type_notifications in grouped_notifications.items():
            # Format type name for display
            type_display = notif_type.replace("_", " ").title()
            body_lines.append(f"## {type_display}")

            for idx, notif in enumerate(type_notifications, 1):
                title = notif.get("title", "Notification")
                message = notif.get("message", "")
                created_at = notif.get("created_at")
                action_url = notif.get("action_url")

                body_lines.extend([
                    f"",
                    f"{idx}. {title}",
                ])

                if message:
                    # Add message with proper indentation
                    for line in message.split("\n"):
                        body_lines.append(f"   {line}")

                if action_url:
                    body_lines.append(f"   View: {action_url}")

                if created_at:
                    # Format timestamp
                    if isinstance(created_at, str):
                        try:
                            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                            time_str = created_dt.strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            time_str = created_at
                    else:
                        time_str = created_at.strftime("%Y-%m-%d %H:%M") if hasattr(created_at, "strftime") else str(created_at)
                    body_lines.append(f"   Time: {time_str}")

            body_lines.append("")  # Empty line between groups

        # Add footer
        body_lines.extend([
            f"---",
            f"You received this digest because you have {digest_frequency} email notifications enabled.",
            f"To change your notification preferences, visit your settings page.",
            f"",
            f"This is an automated notification from AgentHR.",
        ])

        body = "\n".join(body_lines)

        email_details = {
            "subject": subject,
            "body": body,
            "priority": "normal",
        }

        logger.info(f"Digest email formatted successfully: {len(notifications)} notifications")
        return email_details

    except Exception as e:
        logger.error(f"Failed to format digest email: {e}", exc_info=True)
        # Return a basic email format on error
        return {
            "subject": f"Your {digest_frequency.capitalize()} Notification Digest",
            "body": f"You have {len(notifications)} notification(s). Please check your dashboard.",
            "priority": "normal",
        }


async def _get_pending_notifications_for_digest(
    session: AsyncSession,
    digest_frequency: str,
    time_cutoff: datetime,
) -> List[Dict[str, Any]]:
    """
    Query database for pending notifications that should be included in digest.

    This helper function retrieves notifications that:
    1. Have not been delivered yet
    2. Were created after the time cutoff
    3. Belong to users with the specified digest frequency preference

    Args:
        session: Async database session
        digest_frequency: The digest frequency to filter by (hourly, daily, weekly)
        time_cutoff: Only include notifications created after this timestamp

    Returns:
        List of notification dictionaries with user email and preference info

    Example:
        >>> cutoff = datetime.now() - timedelta(hours=1)
        >>> notifs = await _get_pending_notifications_for_digest(
        ...     session, "hourly", cutoff
        ... )
        >>> print(len(notifs))
        5
    """
    try:
        # Query for notifications with user preferences
        # Join notifications with notification preferences and recruiters
        query = (
            select(
                Notification.id,
                Notification.recipient_id,
                Notification.notification_type,
                Notification.title,
                Notification.message,
                Notification.data,
                Notification.action_url,
                Notification.created_at,
                Recruiter.email.label("recipient_email"),
                Recruiter.name.label("recipient_name"),
            )
            .join(
                Recruiter,
                Notification.recipient_id == Recruiter.id,
            )
            .outerjoin(
                NotificationPreference,
                and_(
                    NotificationPreference.user_id == Notification.recipient_id,
                    NotificationPreference.notification_type == Notification.notification_type,
                ),
            )
            .where(
                and_(
                    # Not yet delivered
                    Notification.delivered_at.is_(None),
                    # Delivery not failed
                    Notification.delivery_failed == False,  # noqa: E712
                    # Created after cutoff
                    Notification.created_at >= time_cutoff,
                    # Email enabled for this notification type
                    or_(
                        # Either no preference set (default to email enabled)
                        NotificationPreference.id.is_(None),
                        # Or preference explicitly enables email
                        and_(
                            NotificationPreference.email_enabled == True,  # noqa: E712
                            # And matches the digest frequency
                            NotificationPreference.digest_frequency == digest_frequency,
                        ),
                    ),
                ),
            )
            .order_by(Notification.recipient_id, Notification.created_at)
        )

        result = await session.execute(query)
        rows = result.all()

        # Convert to list of dictionaries
        notifications = []
        for row in rows:
            notifications.append({
                "id": str(row.id),
                "recipient_id": str(row.recipient_id),
                "notification_type": row.notification_type,
                "title": row.title,
                "message": row.message,
                "data": row.data,
                "action_url": row.action_url,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "recipient_email": row.recipient_email,
                "recipient_name": row.recipient_name or "User",
            })

        return notifications

    except Exception as e:
        logger.error(f"Failed to query pending notifications: {e}", exc_info=True)
        return []


async def _mark_notifications_as_delivered(
    session: AsyncSession,
    notification_ids: List[str],
) -> int:
    """
    Mark notifications as delivered in the database.

    This helper function updates the delivery status of notifications
    that were successfully included in a digest email.

    Args:
        session: Async database session
        notification_ids: List of notification IDs to mark as delivered

    Returns:
        Number of notifications successfully marked as delivered

    Example:
        >>> count = await _mark_notifications_as_delivered(
        ...     session, ["notif-1", "notif-2"]
        ... )
        >>> print(count)
        2
    """
    try:
        if not notification_ids:
            return 0

        # Convert string IDs to UUID objects
        from uuid import UUID
        notification_uuids = [UUID(nid) for nid in notification_ids]

        # Query notifications to update
        stmt = (
            select(Notification)
            .where(Notification.id.in_(notification_uuids))
        )
        result = await session.execute(stmt)
        notifications = result.scalars().all()

        # Mark each as delivered
        delivered_at = datetime.utcnow()
        count = 0
        for notif in notifications:
            notif.delivered_at = delivered_at
            count += 1

        await session.commit()

        logger.info(f"Marked {count} notifications as delivered")
        return count

    except Exception as e:
        logger.error(f"Failed to mark notifications as delivered: {e}", exc_info=True)
        await session.rollback()
        return 0


async def _send_notification_digest(
    digest_frequency: str,
    time_cutoff: datetime,
) -> Dict[str, Any]:
    """
    Core async function to process and send notification digests.

    This function handles the complete digest workflow:
    1. Query pending notifications for the frequency
    2. Group notifications by recipient
    3. Format and send digest emails
    4. Mark notifications as delivered

    Args:
        digest_frequency: The digest frequency (hourly, daily, weekly)
        time_cutoff: Time cutoff for including notifications

    Returns:
        Dictionary containing processing results

    Example:
        >>> cutoff = datetime.now() - timedelta(hours=1)
        >>> result = await _send_notification_digest("hourly", cutoff)
        >>> print(result['emails_sent'])
        5
    """
    async with async_session_maker() as session:
        try:
            # Step 1: Get pending notifications
            notifications = await _get_pending_notifications_for_digest(
                session, digest_frequency, time_cutoff
            )

            if not notifications:
                logger.info(f"No pending notifications for {digest_frequency} digest")
                return {
                    "digest_frequency": digest_frequency,
                    "status": "completed",
                    "emails_sent": 0,
                    "notifications_processed": 0,
                    "time_cutoff": time_cutoff.isoformat(),
                }

            # Step 2: Group notifications by recipient
            notifications_by_recipient: Dict[str, List[Dict[str, Any]]] = {}
            for notif in notifications:
                recipient_email = notif.get("recipient_email")
                if not recipient_email:
                    continue

                if recipient_email not in notifications_by_recipient:
                    notifications_by_recipient[recipient_email] = {
                        "recipient_name": notif.get("recipient_name", "User"),
                        "notifications": [],
                    }

                notifications_by_recipient[recipient_email]["notifications"].append(notif)

            logger.info(
                f"Grouped {len(notifications)} notifications for "
                f"{len(notifications_by_recipient)} recipients"
            )

            # Step 3: Send digest emails to each recipient
            emails_sent = 0
            total_delivered = 0
            all_notification_ids = []

            for recipient_email, recipient_data in notifications_by_recipient.items():
                try:
                    recipient_name = recipient_data["recipient_name"]
                    recipient_notifications = recipient_data["notifications"]

                    # Format digest email
                    email_details = format_notification_digest_email(
                        recipient_email=recipient_email,
                        recipient_name=recipient_name,
                        notifications=recipient_notifications,
                        digest_frequency=digest_frequency,
                    )

                    # Collect notification IDs for marking as delivered
                    notification_ids = [n["id"] for n in recipient_notifications]
                    all_notification_ids.extend(notification_ids)

                    # Simulate email sending (in production, use actual SMTP/service)
                    # For now, we just log it
                    logger.info(
                        f"Sending {digest_frequency} digest to {recipient_email}: "
                        f"{len(recipient_notifications)} notifications"
                    )

                    # Placeholder: In production, actually send email
                    # from tasks.notification_tasks import send_notification_via_email
                    # delivery_result = send_notification_via_email(
                    #     [recipient_email], email_details
                    # )

                    emails_sent += 1
                    total_delivered += len(recipient_notifications)

                except Exception as e:
                    logger.error(
                        f"Failed to send digest to {recipient_email}: {e}",
                        exc_info=True
                    )

            # Step 4: Mark notifications as delivered
            if all_notification_ids:
                delivered_count = await _mark_notifications_as_delivered(
                    session, all_notification_ids
                )
                logger.info(f"Marked {delivered_count} notifications as delivered")

            return {
                "digest_frequency": digest_frequency,
                "status": "completed",
                "emails_sent": emails_sent,
                "notifications_processed": total_delivered,
                "recipients_count": len(notifications_by_recipient),
                "time_cutoff": time_cutoff.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to send {digest_frequency} digest: {e}", exc_info=True)
            await session.rollback()
            return {
                "digest_frequency": digest_frequency,
                "status": "failed",
                "error": str(e),
                "emails_sent": 0,
                "notifications_processed": 0,
                "time_cutoff": time_cutoff.isoformat(),
            }


@shared_task(
    name="tasks.notification_digest.send_hourly_notification_digest",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_hourly_notification_digest(
    self,
) -> Dict[str, Any]:
    """
    Send hourly notification digest to users with hourly digest preference.

    This Celery task aggregates notifications from the last hour and sends
    them as digest emails to users who have configured hourly digests.

    Task Workflow:
    1. Calculate time cutoff (1 hour ago from now)
    2. Query pending notifications for hourly digest users
    3. Group notifications by recipient
    4. Send digest emails
    5. Mark notifications as delivered

    Returns:
        Dictionary containing digest results:
        - digest_frequency: "hourly"
        - status: Task status (completed/failed)
        - emails_sent: Number of digest emails sent
        - notifications_processed: Total notifications processed
        - recipients_count: Number of unique recipients
        - processing_time_ms: Total processing time

    Example:
        >>> from tasks.notification_digest import send_hourly_notification_digest
        >>> task = send_hourly_notification_digest.delay()
        >>> result = task.get()
        >>> print(result['emails_sent'])
        5
    """
    import asyncio
    start_time = time.time()

    try:
        logger.info("Starting hourly notification digest task")

        # Calculate time cutoff (1 hour ago)
        time_cutoff = datetime.utcnow() - timedelta(hours=1)

        progress = {
            "current": 1,
            "total": 2,
            "percentage": 50,
            "status": "querying_notifications",
            "message": "Querying pending notifications...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        # Run async digest processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _send_notification_digest("hourly", time_cutoff)
            )
        finally:
            loop.close()

        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        result["processing_time_ms"] = processing_time_ms

        progress = {
            "current": 2,
            "total": 2,
            "percentage": 100,
            "status": "completed",
            "message": "Hourly digest sent successfully",
        }
        self.update_state(state="PROGRESS", meta=progress)

        logger.info(
            f"Hourly notification digest completed: "
            f"emails={result.get('emails_sent')}, "
            f"notifications={result.get('notifications_processed')}, "
            f"time={processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "digest_frequency": "hourly",
            "status": "failed",
            "error": "Digest sending exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in hourly notification digest: {e}", exc_info=True)
        return {
            "digest_frequency": "hourly",
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.notification_digest.send_daily_notification_digest",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_daily_notification_digest(
    self,
) -> Dict[str, Any]:
    """
    Send daily notification digest to users with daily digest preference.

    This Celery task aggregates notifications from the last 24 hours and sends
    them as digest emails to users who have configured daily digests.

    Task Workflow:
    1. Calculate time cutoff (24 hours ago from now)
    2. Query pending notifications for daily digest users
    3. Group notifications by recipient
    4. Send digest emails
    5. Mark notifications as delivered

    Returns:
        Dictionary containing digest results:
        - digest_frequency: "daily"
        - status: Task status (completed/failed)
        - emails_sent: Number of digest emails sent
        - notifications_processed: Total notifications processed
        - recipients_count: Number of unique recipients
        - processing_time_ms: Total processing time

    Example:
        >>> from tasks.notification_digest import send_daily_notification_digest
        >>> task = send_daily_notification_digest.delay()
        >>> result = task.get()
        >>> print(result['emails_sent'])
        15
    """
    import asyncio
    start_time = time.time()

    try:
        logger.info("Starting daily notification digest task")

        # Calculate time cutoff (24 hours ago)
        time_cutoff = datetime.utcnow() - timedelta(days=1)

        progress = {
            "current": 1,
            "total": 2,
            "percentage": 50,
            "status": "querying_notifications",
            "message": "Querying pending notifications...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        # Run async digest processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _send_notification_digest("daily", time_cutoff)
            )
        finally:
            loop.close()

        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        result["processing_time_ms"] = processing_time_ms

        progress = {
            "current": 2,
            "total": 2,
            "percentage": 100,
            "status": "completed",
            "message": "Daily digest sent successfully",
        }
        self.update_state(state="PROGRESS", meta=progress)

        logger.info(
            f"Daily notification digest completed: "
            f"emails={result.get('emails_sent')}, "
            f"notifications={result.get('notifications_processed')}, "
            f"time={processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "digest_frequency": "daily",
            "status": "failed",
            "error": "Digest sending exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in daily notification digest: {e}", exc_info=True)
        return {
            "digest_frequency": "daily",
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.notification_digest.send_weekly_notification_digest",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_weekly_notification_digest(
    self,
) -> Dict[str, Any]:
    """
    Send weekly notification digest to users with weekly digest preference.

    This Celery task aggregates notifications from the last 7 days and sends
    them as digest emails to users who have configured weekly digests.

    Task Workflow:
    1. Calculate time cutoff (7 days ago from now)
    2. Query pending notifications for weekly digest users
    3. Group notifications by recipient
    4. Send digest emails
    5. Mark notifications as delivered

    Returns:
        Dictionary containing digest results:
        - digest_frequency: "weekly"
        - status: Task status (completed/failed)
        - emails_sent: Number of digest emails sent
        - notifications_processed: Total notifications processed
        - recipients_count: Number of unique recipients
        - processing_time_ms: Total processing time

    Example:
        >>> from tasks.notification_digest import send_weekly_notification_digest
        >>> task = send_weekly_notification_digest.delay()
        >>> result = task.get()
        >>> print(result['emails_sent'])
        25
    """
    import asyncio
    start_time = time.time()

    try:
        logger.info("Starting weekly notification digest task")

        # Calculate time cutoff (7 days ago)
        time_cutoff = datetime.utcnow() - timedelta(weeks=1)

        progress = {
            "current": 1,
            "total": 2,
            "percentage": 50,
            "status": "querying_notifications",
            "message": "Querying pending notifications...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        # Run async digest processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _send_notification_digest("weekly", time_cutoff)
            )
        finally:
            loop.close()

        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        result["processing_time_ms"] = processing_time_ms

        progress = {
            "current": 2,
            "total": 2,
            "percentage": 100,
            "status": "completed",
            "message": "Weekly digest sent successfully",
        }
        self.update_state(state="PROGRESS", meta=progress)

        logger.info(
            f"Weekly notification digest completed: "
            f"emails={result.get('emails_sent')}, "
            f"notifications={result.get('notifications_processed')}, "
            f"time={processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "digest_frequency": "weekly",
            "status": "failed",
            "error": "Digest sending exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in weekly notification digest: {e}", exc_info=True)
        return {
            "digest_frequency": "weekly",
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.notification_digest.send_notification_digest",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_notification_digest(
    self,
    digest_frequency: str = "daily",
    recipient_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send notification digest for a specific frequency or to specific recipients.

    This is a flexible digest task that can be triggered manually for specific
    recipients or with a custom frequency. Useful for testing or ad-hoc digest sends.

    Args:
        self: Celery task instance (bind=True)
        digest_frequency: The digest frequency (hourly, daily, weekly)
        recipient_ids: Optional list of specific recipient IDs to send digests to

    Returns:
        Dictionary containing digest results

    Example:
        >>> result = send_notification_digest.delay("daily", ["user-123", "user-456"])
        >>> print(result.get()['status'])
        'completed'
    """
    # This delegates to the frequency-specific tasks
    # or can be extended to support custom recipient filtering
    if digest_frequency == "hourly":
        return send_hourly_notification_digest.apply_async().get()
    elif digest_frequency == "daily":
        return send_daily_notification_digest.apply_async().get()
    elif digest_frequency == "weekly":
        return send_weekly_notification_digest.apply_async().get()
    else:
        return {
            "digest_frequency": digest_frequency,
            "status": "failed",
            "error": f"Unknown digest frequency: {digest_frequency}",
        }
