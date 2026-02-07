"""
Notifications API endpoints.

This module provides endpoints for:
- Listing notifications for a user
- Creating new notifications
- Marking notifications as read
- Deleting notifications

Supports real-time notification delivery and management for recruiters.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.notification import Notification, NotificationType
from models.notification_preference import NotificationPreference, DigestFrequency
from models.recruiter import Recruiter

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class NotificationListItem(BaseModel):
    """Response model for a notification in list view."""

    id: str = Field(..., description="Unique identifier (notification ID)")
    recipient_id: str = Field(..., description="Recipient recruiter ID")
    notification_type: str = Field(..., description="Type of notification")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")
    is_read: bool = Field(..., description="Whether the notification has been read")
    read_at: Optional[str] = Field(None, description="When the notification was read")
    delivered_at: Optional[str] = Field(None, description="When the notification was delivered")
    candidate_id: Optional[str] = Field(None, description="Related candidate ID if any")
    vacancy_id: Optional[str] = Field(None, description="Related vacancy ID if any")
    action_url: Optional[str] = Field(None, description="URL for the notification action")
    created_at: str = Field(..., description="Creation timestamp")


class CreateNotificationRequest(BaseModel):
    """Request model for creating a notification."""

    recipient_id: str = Field(..., description="Recipient recruiter ID")
    notification_type: str = Field(..., description="Type of notification")
    title: str = Field(..., description="Notification title", max_length=255)
    message: str = Field(..., description="Notification message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")
    candidate_id: Optional[str] = Field(None, description="Related candidate ID if any")
    vacancy_id: Optional[str] = Field(None, description="Related vacancy ID if any")
    action_url: Optional[str] = Field(None, description="URL for the notification action", max_length=500)


class CreateNotificationResponse(BaseModel):
    """Response model for notification creation."""

    id: str = Field(..., description="Notification ID")
    recipient_id: str = Field(..., description="Recipient recruiter ID")
    notification_type: str = Field(..., description="Type of notification")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    is_read: bool = Field(..., description="Whether the notification has been read")
    created_at: str = Field(..., description="Creation timestamp")
    message: str = Field(..., description="Success message")


class MarkReadRequest(BaseModel):
    """Request model for marking notifications as read."""

    notification_ids: List[str] = Field(
        ...,
        description="List of notification IDs to mark as read",
        min_length=1
    )


class MarkReadResponse(BaseModel):
    """Response model for marking notifications as read."""

    total_requested: int = Field(..., description="Total number of notifications requested")
    successful: int = Field(..., description="Number of successfully marked as read")
    failed: int = Field(..., description="Number of notifications that failed")
    results: List[Dict[str, Any]] = Field(..., description="Individual results for each notification")


class UnreadCountResponse(BaseModel):
    """Response model for unread notification count."""

    recipient_id: str = Field(..., description="Recipient recruiter ID")
    unread_count: int = Field(..., description="Number of unread notifications")


class NotificationPreferenceItem(BaseModel):
    """Response model for a notification preference."""

    id: str = Field(..., description="Unique identifier (preference ID)")
    user_id: str = Field(..., description="User ID who owns this preference")
    notification_type: str = Field(..., description="Notification type")
    email_enabled: bool = Field(..., description="Whether email notifications are enabled")
    in_app_enabled: bool = Field(..., description="Whether in-app notifications are enabled")
    push_enabled: bool = Field(..., description="Whether push notifications are enabled")
    sms_enabled: bool = Field(..., description="Whether SMS notifications are enabled")
    digest_frequency: Optional[str] = Field(None, description="Digest frequency (immediate, hourly, daily, weekly, never)")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class NotificationPreferencesResponse(BaseModel):
    """Response model for all notification preferences for a user."""

    user_id: str = Field(..., description="User ID")
    preferences: List[NotificationPreferenceItem] = Field(..., description="List of notification preferences")
    total_preferences: int = Field(..., description="Total number of preferences")


class UpdateNotificationPreferenceRequest(BaseModel):
    """Request model for updating a notification preference."""

    notification_type: str = Field(..., description="Notification type to update")
    email_enabled: Optional[bool] = Field(None, description="Enable email notifications")
    in_app_enabled: Optional[bool] = Field(None, description="Enable in-app notifications")
    push_enabled: Optional[bool] = Field(None, description="Enable push notifications")
    sms_enabled: Optional[bool] = Field(None, description="Enable SMS notifications")
    digest_frequency: Optional[str] = Field(None, description="Digest frequency (immediate, hourly, daily, weekly, never)")


class UpdateNotificationPreferenceResponse(BaseModel):
    """Response model for updating a notification preference."""

    id: str = Field(..., description="Preference ID")
    user_id: str = Field(..., description="User ID")
    notification_type: str = Field(..., description="Notification type")
    email_enabled: bool = Field(..., description="Email notifications enabled")
    in_app_enabled: bool = Field(..., description="In-app notifications enabled")
    push_enabled: bool = Field(..., description="Push notifications enabled")
    sms_enabled: bool = Field(..., description="SMS notifications enabled")
    digest_frequency: Optional[str] = Field(None, description="Digest frequency")
    updated_at: str = Field(..., description="Update timestamp")
    message: str = Field(..., description="Success message")


@router.get(
    "/",
    response_model=List[NotificationListItem],
    tags=["Notifications"],
)
async def list_notifications(
    request: Request,
    recipient_id: str = Query(..., description="Recipient recruiter ID"),
    unread_only: bool = Query(False, description="Filter to only unread notifications"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List notifications for a user.

    Returns a paginated list of notifications for the specified recipient.
    Can be filtered by unread status and notification type.

    Args:
        request: FastAPI request object
        recipient_id: Recruiter UUID to get notifications for
        unread_only: If True, only return unread notifications
        notification_type: Optional filter by notification type
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of notifications

    Raises:
        HTTPException(400): Invalid recipient_id format
        HTTPException(404): Recipient not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all notifications for a user
        >>> response = requests.get(
        ...     "http://localhost:8000/api/notifications/",
        ...     params={"recipient_id": "abc-123-def"}
        ... )
        >>> # Get only unread notifications
        >>> response = requests.get(
        ...     "http://localhost:8000/api/notifications/",
        ...     params={"recipient_id": "abc-123-def", "unreadOnly": True}
        ... )
    """
    try:
        logger.info(
            f"Fetching notifications - recipient_id: {recipient_id}, "
            f"unreadOnly: {unread_only}, notification_type: {notification_type}, "
            f"skip: {skip}, limit: {limit}"
        )

        # Parse recipient_id as UUID
        try:
            recipient_uuid = UUID(recipient_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid recipient_id format: {recipient_id}",
            )

        # Verify recruiter exists
        recruiter_query = select(Recruiter).where(Recruiter.id == recipient_uuid)
        recruiter_result = await db.execute(recruiter_query)
        recruiter = recruiter_result.scalar_one_or_none()

        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient not found: {recipient_id}",
            )

        # Build base query
        query = select(Notification).where(Notification.recipient_id == recipient_uuid)

        # Apply filters
        if unread_only:
            query = query.where(Notification.is_read == False)

        if notification_type:
            query = query.where(Notification.notification_type == notification_type)

        # Order by most recently created and paginate
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        notifications = result.scalars().all()

        # Convert to response format
        notifications_list = []
        for notification in notifications:
            notifications_list.append({
                "id": str(notification.id),
                "recipient_id": str(notification.recipient_id),
                "notification_type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "data": notification.data,
                "is_read": notification.is_read,
                "read_at": notification.read_at.isoformat() if notification.read_at else None,
                "delivered_at": notification.delivered_at.isoformat() if notification.delivered_at else None,
                "candidate_id": str(notification.candidate_id) if notification.candidate_id else None,
                "vacancy_id": str(notification.vacancy_id) if notification.vacancy_id else None,
                "action_url": notification.action_url,
                "created_at": notification.created_at.isoformat() if notification.created_at else None,
            })

        logger.info(f"Retrieved {len(notifications_list)} notifications for recipient {recipient_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=notifications_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list notifications: {str(e)}",
        ) from e


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    tags=["Notifications"],
)
async def get_unread_count(
    recipient_id: str = Query(..., description="Recipient recruiter ID"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get the count of unread notifications for a user.

    Args:
        recipient_id: Recruiter UUID to get unread count for
        db: Database session

    Returns:
        JSON response with unread notification count

    Raises:
        HTTPException(400): Invalid recipient_id format
        HTTPException(404): Recipient not found
        HTTPException(500): If count retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/notifications/unread-count",
        ...     params={"recipient_id": "abc-123-def"}
        ... )
    """
    try:
        logger.info(f"Fetching unread count for recipient: {recipient_id}")

        # Parse recipient_id as UUID
        try:
            recipient_uuid = UUID(recipient_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid recipient_id format: {recipient_id}",
            )

        # Verify recruiter exists
        recruiter_query = select(Recruiter).where(Recruiter.id == recipient_uuid)
        recruiter_result = await db.execute(recruiter_query)
        recruiter = recruiter_result.scalar_one_or_none()

        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient not found: {recipient_id}",
            )

        # Count unread notifications
        count_query = select(func.count(Notification.id)).where(
            and_(
                Notification.recipient_id == recipient_uuid,
                Notification.is_read == False
            )
        )
        count_result = await db.execute(count_query)
        unread_count = count_result.scalar() or 0

        logger.info(f"Unread count for recipient {recipient_id}: {unread_count}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "recipient_id": recipient_id,
                "unread_count": unread_count,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unread count: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread count: {str(e)}",
        ) from e


@router.post(
    "/",
    response_model=CreateNotificationResponse,
    tags=["Notifications"],
)
async def create_notification(
    request: Request,
    notification_data: CreateNotificationRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new notification.

    Creates a new notification for the specified recipient. The notification
    will be delivered according to the user's notification preferences.

    Args:
        request: FastAPI request object
        notification_data: Notification details (recipient_id, type, title, message, etc.)
        db: Database session

    Returns:
        JSON response with created notification details

    Raises:
        HTTPException(400): Invalid data format
        HTTPException(404): Recipient not found
        HTTPException(500): If notification creation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "recipient_id": "abc-123-def",
        ...     "notification_type": "candidate_stage_changed",
        ...     "title": "Candidate moved to interview",
        ...     "message": "John Doe has been moved to the interview stage",
        ...     "candidate_id": "resume-456-ghi"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/notifications/",
        ...     json=data
        ... )
    """
    try:
        logger.info(f"Creating notification for recipient: {notification_data.recipient_id}")

        # Parse recipient_id as UUID
        try:
            recipient_uuid = UUID(notification_data.recipient_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid recipient_id format: {notification_data.recipient_id}",
            )

        # Verify recruiter exists
        recruiter_query = select(Recruiter).where(Recruiter.id == recipient_uuid)
        recruiter_result = await db.execute(recruiter_query)
        recruiter = recruiter_result.scalar_one_or_none()

        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient not found: {notification_data.recipient_id}",
            )

        # Validate notification type
        try:
            notification_type = NotificationType(notification_data.notification_type)
        except ValueError:
            # Allow custom notification types as strings
            notification_type = notification_data.notification_type

        # Parse optional IDs
        candidate_uuid = None
        if notification_data.candidate_id:
            try:
                candidate_uuid = UUID(notification_data.candidate_id)
            except ValueError:
                logger.warning(f"Invalid candidate_id format: {notification_data.candidate_id}")

        vacancy_uuid = None
        if notification_data.vacancy_id:
            try:
                vacancy_uuid = UUID(notification_data.vacancy_id)
            except ValueError:
                logger.warning(f"Invalid vacancy_id format: {notification_data.vacancy_id}")

        # Create notification
        notification = Notification(
            recipient_id=recipient_uuid,
            notification_type=notification_type,
            title=notification_data.title,
            message=notification_data.message,
            data=notification_data.data,
            candidate_id=candidate_uuid,
            vacancy_id=vacancy_uuid,
            action_url=notification_data.action_url,
            is_read=False,
        )

        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        logger.info(
            f"Notification created: {notification.id} for recipient {notification_data.recipient_id}"
        )

        # Broadcast to WebSocket clients
        try:
            from api.websocket import broadcast_notification
            connections = await broadcast_notification(notification)
            if connections > 0:
                logger.info(
                    f"Notification {notification.id} broadcast to {connections} "
                    f"WebSocket connection(s)"
                )
            else:
                logger.debug(
                    f"No active WebSocket connections for user {notification_data.recipient_id}"
                )
        except Exception as broadcast_error:
            # Don't fail the request if broadcast fails
            logger.error(
                f"Failed to broadcast notification {notification.id}: {broadcast_error}",
                exc_info=True
            )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(notification.id),
                "recipient_id": str(notification.recipient_id),
                "notification_type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat() if notification.created_at else None,
                "message": "Notification created successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}",
        ) from e


@router.put(
    "/mark-read",
    response_model=MarkReadResponse,
    tags=["Notifications"],
)
async def mark_notifications_read(
    request: Request,
    mark_data: MarkReadRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Mark multiple notifications as read.

    Marks the specified notifications as read and sets the read_at timestamp.

    Args:
        request: FastAPI request object
        mark_data: List of notification IDs to mark as read
        db: Database session

    Returns:
        JSON response with bulk operation results

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "notification_ids": ["notif-1", "notif-2", "notif-3"]
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8000/api/notifications/mark-read",
        ...     json=data
        ... )
    """
    try:
        logger.info(f"Marking {len(mark_data.notification_ids)} notifications as read")

        results = []
        successful_count = 0
        failed_count = 0

        # Process each notification_id
        for notification_id in mark_data.notification_ids:
            try:
                # Parse notification_id as UUID
                try:
                    notification_uuid = UUID(notification_id)
                except ValueError:
                    results.append({
                        "notification_id": notification_id,
                        "success": False,
                        "message": f"Invalid notification ID format: {notification_id}",
                    })
                    failed_count += 1
                    continue

                # Get the notification
                notification_query = select(Notification).where(
                    Notification.id == notification_uuid
                )
                notification_result = await db.execute(notification_query)
                notification = notification_result.scalar_one_or_none()

                if not notification:
                    results.append({
                        "notification_id": notification_id,
                        "success": False,
                        "message": f"Notification not found: {notification_id}",
                    })
                    failed_count += 1
                    continue

                # Mark as read
                notification.is_read = True
                notification.read_at = datetime.now(timezone.utc)

                await db.commit()

                results.append({
                    "notification_id": notification_id,
                    "success": True,
                    "message": "Notification marked as read",
                })
                successful_count += 1

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error marking notification {notification_id} as read: {e}", exc_info=True)
                results.append({
                    "notification_id": notification_id,
                    "success": False,
                    "message": f"Failed to mark as read: {str(e)}",
                })
                failed_count += 1

        logger.info(
            f"Mark read completed: {successful_count} successful, {failed_count} failed"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total_requested": len(mark_data.notification_ids),
                "successful": successful_count,
                "failed": failed_count,
                "results": results,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mark read operation: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notifications as read: {str(e)}",
        ) from e


@router.delete(
    "/{notification_id}",
    tags=["Notifications"],
)
async def delete_notification(
    request: Request,
    notification_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a notification.

    Permanently deletes the specified notification.

    Args:
        request: FastAPI request object
        notification_id: Notification UUID to delete
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(400): Invalid notification_id format
        HTTPException(404): Notification not found
        HTTPException(500): If deletion fails

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "http://localhost:8000/api/notifications/abc-123-def"
        ... )
    """
    try:
        logger.info(f"Deleting notification: {notification_id}")

        # Parse notification_id as UUID
        try:
            notification_uuid = UUID(notification_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid notification_id format: {notification_id}",
            )

        # Get the notification
        notification_query = select(Notification).where(Notification.id == notification_uuid)
        notification_result = await db.execute(notification_query)
        notification = notification_result.scalar_one_or_none()

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification not found: {notification_id}",
            )

        # Delete the notification
        await db.delete(notification)
        await db.commit()

        logger.info(f"Notification deleted: {notification_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": notification_id,
                "message": "Notification deleted successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}",
        ) from e


@router.get(
    "/preferences",
    response_model=NotificationPreferencesResponse,
    tags=["Notifications"],
)
async def get_notification_preferences(
    request: Request,
    user_id: str = Query(..., description="User ID to get preferences for"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get notification preferences for a user.

    Returns all notification preferences for the specified user, including
    enabled channels and digest frequencies for each notification type.

    Args:
        request: FastAPI request object
        user_id: User UUID to get preferences for
        db: Database session

    Returns:
        JSON response with list of notification preferences

    Raises:
        HTTPException(400): Invalid user_id format
        HTTPException(404): User not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/notifications/preferences",
        ...     params={"user_id": "abc-123-def"}
        ... )
    """
    try:
        logger.info(f"Fetching notification preferences for user: {user_id}")

        # Parse user_id as UUID
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_id format: {user_id}",
            )

        # Verify recruiter exists
        recruiter_query = select(Recruiter).where(Recruiter.id == user_uuid)
        recruiter_result = await db.execute(recruiter_query)
        recruiter = recruiter_result.scalar_one_or_none()

        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        # Get all notification preferences for the user
        preferences_query = select(NotificationPreference).where(
            NotificationPreference.user_id == user_uuid
        )
        preferences_result = await db.execute(preferences_query)
        preferences = preferences_result.scalars().all()

        # Convert to response format
        preferences_list = []
        for preference in preferences:
            preferences_list.append({
                "id": str(preference.id),
                "user_id": str(preference.user_id),
                "notification_type": preference.notification_type,
                "email_enabled": preference.email_enabled,
                "in_app_enabled": preference.in_app_enabled,
                "push_enabled": preference.push_enabled,
                "sms_enabled": preference.sms_enabled,
                "digest_frequency": preference.digest_frequency,
                "created_at": preference.created_at.isoformat() if preference.created_at else None,
                "updated_at": preference.updated_at.isoformat() if preference.updated_at else None,
            })

        logger.info(
            f"Retrieved {len(preferences_list)} notification preferences for user {user_id}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "user_id": user_id,
                "preferences": preferences_list,
                "total_preferences": len(preferences_list),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification preferences: {str(e)}",
        ) from e


@router.put(
    "/preferences",
    response_model=UpdateNotificationPreferenceResponse,
    tags=["Notifications"],
)
async def update_notification_preference(
    request: Request,
    preference_data: UpdateNotificationPreferenceRequest,
    user_id: str = Query(..., description="User ID to update preference for"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update notification preferences for a user.

    Updates the notification preferences for a specific notification type.
    If a preference doesn't exist for the user and notification type, it will
    be created with default values for any unspecified fields.

    Args:
        request: FastAPI request object
        preference_data: Preference updates (notification_type and enabled flags)
        user_id: User UUID to update preferences for
        db: Database session

    Returns:
        JSON response with updated notification preference

    Raises:
        HTTPException(400): Invalid data format
        HTTPException(404): User not found
        HTTPException(500): If update fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "notification_type": "candidate_stage_changed",
        ...     "email_enabled": True,
        ...     "in_app_enabled": True,
        ...     "push_enabled": False,
        ...     "digest_frequency": "immediate"
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8000/api/notifications/preferences",
        ...     params={"user_id": "abc-123-def"},
        ...     json=data
        ... )
    """
    try:
        logger.info(
            f"Updating notification preference for user {user_id}, "
            f"type: {preference_data.notification_type}"
        )

        # Parse user_id as UUID
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_id format: {user_id}",
            )

        # Verify recruiter exists
        recruiter_query = select(Recruiter).where(Recruiter.id == user_uuid)
        recruiter_result = await db.execute(recruiter_query)
        recruiter = recruiter_result.scalar_one_or_none()

        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        # Validate digest frequency if provided
        if preference_data.digest_frequency:
            try:
                DigestFrequency(preference_data.digest_frequency)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid digest_frequency: {preference_data.digest_frequency}. "
                    f"Must be one of: immediate, hourly, daily, weekly, never",
                )

        # Check if preference already exists
        existing_preference_query = select(NotificationPreference).where(
            and_(
                NotificationPreference.user_id == user_uuid,
                NotificationPreference.notification_type == preference_data.notification_type
            )
        )
        existing_result = await db.execute(existing_preference_query)
        preference = existing_result.scalar_one_or_none()

        if preference:
            # Update existing preference
            if preference_data.email_enabled is not None:
                preference.email_enabled = preference_data.email_enabled
            if preference_data.in_app_enabled is not None:
                preference.in_app_enabled = preference_data.in_app_enabled
            if preference_data.push_enabled is not None:
                preference.push_enabled = preference_data.push_enabled
            if preference_data.sms_enabled is not None:
                preference.sms_enabled = preference_data.sms_enabled
            if preference_data.digest_frequency is not None:
                preference.digest_frequency = preference_data.digest_frequency

            await db.commit()
            await db.refresh(preference)

            logger.info(
                f"Updated notification preference {preference.id} "
                f"for user {user_id}, type {preference_data.notification_type}"
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "id": str(preference.id),
                    "user_id": str(preference.user_id),
                    "notification_type": preference.notification_type,
                    "email_enabled": preference.email_enabled,
                    "in_app_enabled": preference.in_app_enabled,
                    "push_enabled": preference.push_enabled,
                    "sms_enabled": preference.sms_enabled,
                    "digest_frequency": preference.digest_frequency,
                    "updated_at": preference.updated_at.isoformat() if preference.updated_at else None,
                    "message": "Notification preference updated successfully",
                },
            )
        else:
            # Create new preference with defaults for unspecified fields
            new_preference = NotificationPreference(
                user_id=user_uuid,
                notification_type=preference_data.notification_type,
                email_enabled=preference_data.email_enabled if preference_data.email_enabled is not None else True,
                in_app_enabled=preference_data.in_app_enabled if preference_data.in_app_enabled is not None else True,
                push_enabled=preference_data.push_enabled if preference_data.push_enabled is not None else False,
                sms_enabled=preference_data.sms_enabled if preference_data.sms_enabled is not None else False,
                digest_frequency=preference_data.digest_frequency,
            )

            db.add(new_preference)
            await db.commit()
            await db.refresh(new_preference)

            logger.info(
                f"Created notification preference {new_preference.id} "
                f"for user {user_id}, type {preference_data.notification_type}"
            )

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "id": str(new_preference.id),
                    "user_id": str(new_preference.user_id),
                    "notification_type": new_preference.notification_type,
                    "email_enabled": new_preference.email_enabled,
                    "in_app_enabled": new_preference.in_app_enabled,
                    "push_enabled": new_preference.push_enabled,
                    "sms_enabled": new_preference.sms_enabled,
                    "digest_frequency": new_preference.digest_frequency,
                    "updated_at": new_preference.updated_at.isoformat() if new_preference.updated_at else None,
                    "message": "Notification preference created successfully",
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification preference: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification preference: {str(e)}",
        ) from e
