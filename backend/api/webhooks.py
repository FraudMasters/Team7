"""
Webhook management endpoints.

This module provides endpoints for:
- Creating webhook subscriptions for event notifications
- Listing and managing webhook subscriptions
- Viewing webhook delivery logs
- Enabling/disabling webhook subscriptions
- Managing webhook secrets for signature verification

Supports comprehensive webhook management with event filtering,
delivery tracking, and retry logic monitoring.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.webhook import (
    WebhookSubscription,
    WebhookDeliveryLog,
    WebhookEventType,
    WebhookDeliveryStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class CreateWebhookSubscriptionRequest(BaseModel):
    """Request model for creating a webhook subscription."""

    url: str = Field(
        ...,
        description="HTTP/HTTPS endpoint URL to receive webhook deliveries",
        min_length=1,
        max_length=2048,
    )
    events: List[str] = Field(
        ...,
        description="List of event types to subscribe to",
        min_length=1,
    )
    secret: Optional[str] = Field(
        None,
        description="Optional HMAC secret for webhook signature verification",
        max_length=255,
    )
    api_key_id: Optional[str] = Field(
        None,
        description="Optional API key ID to associate with this subscription",
    )

    @validator("url")
    def validate_url(cls, v):
        """Validate that URL starts with http:// or https://."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @validator("events")
    def validate_events(cls, v):
        """Validate that all events are valid WebhookEventType values."""
        valid_events = [event.value for event in WebhookEventType]
        for event in v:
            if event not in valid_events:
                raise ValueError(
                    f"Invalid event type: {event}. "
                    f"Valid events are: {', '.join(valid_events)}"
                )
        return v

    @validator("secret")
    def validate_secret(cls, v):
        """Validate secret length if provided."""
        if v is not None and len(v) < 8:
            raise ValueError("Secret must be at least 8 characters long")
        return v


class UpdateWebhookSubscriptionRequest(BaseModel):
    """Request model for updating a webhook subscription."""

    url: Optional[str] = Field(
        None,
        description="HTTP/HTTPS endpoint URL to receive webhook deliveries",
        min_length=1,
        max_length=2048,
    )
    events: Optional[List[str]] = Field(
        None,
        description="List of event types to subscribe to",
        min_length=1,
    )
    secret: Optional[str] = Field(
        None,
        description="HMAC secret for webhook signature verification",
        max_length=255,
    )

    @validator("url")
    def validate_url(cls, v):
        """Validate that URL starts with http:// or https://."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @validator("events")
    def validate_events(cls, v):
        """Validate that all events are valid WebhookEventType values."""
        if v is not None:
            valid_events = [event.value for event in WebhookEventType]
            for event in v:
                if event not in valid_events:
                    raise ValueError(
                        f"Invalid event type: {event}. "
                        f"Valid events are: {', '.join(valid_events)}"
                    )
        return v

    @validator("secret")
    def validate_secret(cls, v):
        """Validate secret length if provided."""
        if v is not None and len(v) < 8:
            raise ValueError("Secret must be at least 8 characters long")
        return v


class WebhookSubscriptionResponse(BaseModel):
    """Response model for webhook subscription creation."""

    id: str = Field(..., description="Subscription UUID")
    url: str = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(..., description="Subscribed event types")
    is_active: bool = Field(..., description="Whether subscription is active")
    api_key_id: Optional[str] = Field(None, description="Associated API key ID")
    last_delivery_at: Optional[str] = Field(None, description="Last successful delivery timestamp")
    failure_count: int = Field(..., description="Number of consecutive failures")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    message: str = Field(..., description="Success message")


class WebhookSubscriptionListItem(BaseModel):
    """Response model for a webhook subscription in list view."""

    id: str = Field(..., description="Subscription UUID")
    url: str = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(..., description="Subscribed event types")
    is_active: bool = Field(..., description="Whether subscription is active")
    api_key_id: Optional[str] = Field(None, description="Associated API key ID")
    last_delivery_at: Optional[str] = Field(None, description="Last successful delivery timestamp")
    failure_count: int = Field(..., description="Number of consecutive failures")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class DeliveryLogInfo(BaseModel):
    """Information about a delivery log entry."""

    id: str = Field(..., description="Delivery log UUID")
    event_type: str = Field(..., description="Event type delivered")
    status: str = Field(..., description="Delivery status")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    attempt_count: int = Field(..., description="Number of delivery attempts")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: str = Field(..., description="Creation timestamp")


class WebhookSubscriptionWithLogs(BaseModel):
    """Response model for webhook subscription with delivery logs."""

    id: str = Field(..., description="Subscription UUID")
    url: str = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(..., description="Subscribed event types")
    is_active: bool = Field(..., description="Whether subscription is active")
    api_key_id: Optional[str] = Field(None, description="Associated API key ID")
    last_delivery_at: Optional[str] = Field(None, description="Last successful delivery timestamp")
    failure_count: int = Field(..., description="Number of consecutive failures")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    recent_deliveries: List[DeliveryLogInfo] = Field(
        default_factory=list,
        description="Recent delivery logs",
    )


class DeliveryLogDetail(BaseModel):
    """Detailed response model for a delivery log entry."""

    id: str = Field(..., description="Delivery log UUID")
    subscription_id: str = Field(..., description="Subscription UUID")
    event_type: str = Field(..., description="Event type delivered")
    event_data: Dict[str, Any] = Field(..., description="Event payload")
    status: str = Field(..., description="Delivery status")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    response_body: Optional[str] = Field(None, description="Response body")
    attempt_count: int = Field(..., description="Number of delivery attempts")
    next_retry_at: Optional[str] = Field(None, description="Next retry timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ToggleSubscriptionResponse(BaseModel):
    """Response model for enabling/disabling subscriptions."""

    id: str = Field(..., description="Subscription UUID")
    is_active: bool = Field(..., description="New active status")
    message: str = Field(..., description="Success message")


@router.post(
    "/subscribe",
    response_model=WebhookSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Webhooks"],
)
async def create_webhook_subscription(
    request: Request,
    subscription_data: CreateWebhookSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new webhook subscription.

    Creates a webhook subscription to receive real-time notifications
    for specified events. The subscription will send HTTP POST requests
    to the provided URL when events occur.

    Args:
        request: FastAPI request object
        subscription_data: Subscription details (url, events, optional secret, optional api_key_id)
        db: Database session

    Returns:
        JSON response with created subscription details

    Raises:
        HTTPException(422): If validation fails
        HTTPException(404): If api_key_id is provided but key not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "url": "https://example.com/webhook",
        ...     "events": ["candidate.created", "stage.changed"]
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/webhooks/subscribe",
        ...     json=data
        ... )
        >>> subscription = response.json()
    """
    try:
        logger.info(
            f"Creating webhook subscription - url: {subscription_data.url}, "
            f"events: {subscription_data.events}"
        )

        # Validate api_key_id if provided
        api_key_uuid = None
        if subscription_data.api_key_id:
            try:
                api_key_uuid = UUID(subscription_data.api_key_id)
                # Verify API key exists
                from models.api_key import APIKey
                api_key_query = select(APIKey).where(APIKey.id == api_key_uuid)
                api_key_result = await db.execute(api_key_query)
                api_key = api_key_result.scalar_one_or_none()
                if not api_key:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"API key not found: {subscription_data.api_key_id}",
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid API key ID format: {subscription_data.api_key_id}",
                )

        # Create the subscription
        new_subscription = WebhookSubscription(
            url=subscription_data.url,
            events=subscription_data.events,
            secret=subscription_data.secret,
            api_key_id=api_key_uuid,
            is_active=True,
            failure_count=0,
        )

        db.add(new_subscription)
        await db.commit()
        await db.refresh(new_subscription)

        logger.info(
            f"Webhook subscription created successfully: {new_subscription.id}"
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(new_subscription.id),
                "url": new_subscription.url,
                "events": new_subscription.events,
                "is_active": new_subscription.is_active,
                "api_key_id": str(new_subscription.api_key_id) if new_subscription.api_key_id else None,
                "last_delivery_at": new_subscription.last_delivery_at.isoformat() if new_subscription.last_delivery_at else None,
                "failure_count": new_subscription.failure_count,
                "created_at": new_subscription.created_at.isoformat() if new_subscription.created_at else None,
                "updated_at": new_subscription.updated_at.isoformat() if new_subscription.updated_at else None,
                "message": "Webhook subscription created successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating webhook subscription: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create webhook subscription: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=List[WebhookSubscriptionListItem],
    tags=["Webhooks"],
)
async def list_webhook_subscriptions(
    request: Request,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all webhook subscriptions.

    Returns a paginated list of webhook subscriptions with their metadata.
    Can be filtered by active status and event type.

    Args:
        request: FastAPI request object
        is_active: Optional filter by active status
        event_type: Optional filter by event type (subscriptions must have this event)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of webhook subscriptions

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all subscriptions
        >>> response = requests.get("http://localhost:8000/api/webhooks/")
        >>> # Get only active subscriptions
        >>> response = requests.get("http://localhost:8000/api/webhooks/?is_active=true")
        >>> # Get subscriptions for specific event
        >>> response = requests.get("http://localhost:8000/api/webhooks/?event_type=candidate.created")
        >>> subscriptions = response.json()
    """
    try:
        logger.info(
            f"Fetching webhook subscriptions - is_active: {is_active}, "
            f"event_type: {event_type}, skip: {skip}, limit: {limit}"
        )

        # Build query
        query = select(WebhookSubscription)

        # Apply filters
        if is_active is not None:
            query = query.where(WebhookSubscription.is_active == is_active)

        if event_type:
            # Filter subscriptions that have this event in their events list
            query = query.where(WebhookSubscription.events.contains([event_type]))

        # Order by most recently created
        query = query.order_by(
            WebhookSubscription.created_at.desc()
        ).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        subscriptions = result.scalars().all()

        # Convert to response format
        subscriptions_list = []
        for sub in subscriptions:
            subscriptions_list.append({
                "id": str(sub.id),
                "url": sub.url,
                "events": sub.events,
                "is_active": sub.is_active,
                "api_key_id": str(sub.api_key_id) if sub.api_key_id else None,
                "last_delivery_at": sub.last_delivery_at.isoformat() if sub.last_delivery_at else None,
                "failure_count": sub.failure_count,
                "created_at": sub.created_at.isoformat() if sub.created_at else None,
                "updated_at": sub.updated_at.isoformat() if sub.updated_at else None,
            })

        logger.info(f"Retrieved {len(subscriptions_list)} webhook subscriptions")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=subscriptions_list,
        )

    except Exception as e:
        logger.error(f"Error listing webhook subscriptions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list webhook subscriptions: {str(e)}",
        ) from e


@router.get(
    "/{subscription_id}",
    response_model=WebhookSubscriptionWithLogs,
    tags=["Webhooks"],
)
async def get_webhook_subscription(
    request: Request,
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific webhook subscription with recent delivery logs.

    Returns details for a specific webhook subscription including
    recent delivery logs for monitoring and debugging.

    Args:
        request: FastAPI request object
        subscription_id: Subscription UUID
        db: Database session

    Returns:
        JSON response with subscription details and recent delivery logs

    Raises:
        HTTPException(400): If subscription_id is not a valid UUID
        HTTPException(404): If subscription not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     f"http://localhost:8000/api/webhooks/{subscription_id}"
        ... )
        >>> subscription = response.json()
    """
    try:
        logger.info(f"Fetching webhook subscription: {subscription_id}")

        # Parse subscription_id as UUID
        try:
            subscription_uuid = UUID(subscription_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription ID format: {subscription_id}",
            )

        # Get the subscription
        query = select(WebhookSubscription).where(
            WebhookSubscription.id == subscription_uuid
        )
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook subscription not found: {subscription_id}",
            )

        # Get recent delivery logs (last 10)
        logs_query = (
            select(WebhookDeliveryLog)
            .where(WebhookDeliveryLog.subscription_id == subscription_uuid)
            .order_by(WebhookDeliveryLog.created_at.desc())
            .limit(10)
        )
        logs_result = await db.execute(logs_query)
        delivery_logs = logs_result.scalars().all()

        # Convert logs to response format
        recent_deliveries = []
        for log in delivery_logs:
            recent_deliveries.append({
                "id": str(log.id),
                "event_type": log.event_type,
                "status": log.status.value,
                "status_code": log.status_code,
                "attempt_count": log.attempt_count,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            })

        subscription_data = {
            "id": str(subscription.id),
            "url": subscription.url,
            "events": subscription.events,
            "is_active": subscription.is_active,
            "api_key_id": str(subscription.api_key_id) if subscription.api_key_id else None,
            "last_delivery_at": subscription.last_delivery_at.isoformat() if subscription.last_delivery_at else None,
            "failure_count": subscription.failure_count,
            "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
            "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
            "recent_deliveries": recent_deliveries,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=subscription_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook subscription {subscription_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get webhook subscription: {str(e)}",
        ) from e


@router.put(
    "/{subscription_id}",
    response_model=WebhookSubscriptionResponse,
    tags=["Webhooks"],
)
async def update_webhook_subscription(
    request: Request,
    subscription_id: str,
    subscription_data: UpdateWebhookSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a webhook subscription.

    Updates the URL, events, or secret of an existing webhook subscription.

    Args:
        request: FastAPI request object
        subscription_id: Subscription UUID
        subscription_data: Updated subscription details
        db: Database session

    Returns:
        JSON response with updated subscription details

    Raises:
        HTTPException(400): If subscription_id is not a valid UUID
        HTTPException(404): If subscription not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "url": "https://example.com/webhook-v2",
        ...     "events": ["candidate.created", "stage.changed", "ranking.updated"]
        ... }
        >>> response = requests.put(
        ...     f"http://localhost:8000/api/webhooks/{subscription_id}",
        ...     json=data
        ... )
        >>> subscription = response.json()
    """
    try:
        logger.info(f"Updating webhook subscription: {subscription_id}")

        # Parse subscription_id as UUID
        try:
            subscription_uuid = UUID(subscription_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription ID format: {subscription_id}",
            )

        # Get the subscription
        query = select(WebhookSubscription).where(
            WebhookSubscription.id == subscription_uuid
        )
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook subscription not found: {subscription_id}",
            )

        # Update fields if provided
        if subscription_data.url is not None:
            subscription.url = subscription_data.url
        if subscription_data.events is not None:
            subscription.events = subscription_data.events
        if subscription_data.secret is not None:
            subscription.secret = subscription_data.secret

        await db.commit()
        await db.refresh(subscription)

        logger.info(f"Webhook subscription updated successfully: {subscription_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(subscription.id),
                "url": subscription.url,
                "events": subscription.events,
                "is_active": subscription.is_active,
                "api_key_id": str(subscription.api_key_id) if subscription.api_key_id else None,
                "last_delivery_at": subscription.last_delivery_at.isoformat() if subscription.last_delivery_at else None,
                "failure_count": subscription.failure_count,
                "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
                "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
                "message": "Webhook subscription updated successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating webhook subscription {subscription_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update webhook subscription: {str(e)}",
        ) from e


@router.delete(
    "/{subscription_id}",
    tags=["Webhooks"],
)
async def delete_webhook_subscription(
    request: Request,
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a webhook subscription.

    Permanently deletes a webhook subscription and all its delivery logs.

    Args:
        request: FastAPI request object
        subscription_id: Subscription UUID
        db: Database session

    Returns:
        JSON response with deletion confirmation

    Raises:
        HTTPException(400): If subscription_id is not a valid UUID
        HTTPException(404): If subscription not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     f"http://localhost:8000/api/webhooks/{subscription_id}"
        ... )
        >>> result = response.json()
    """
    try:
        logger.info(f"Deleting webhook subscription: {subscription_id}")

        # Parse subscription_id as UUID
        try:
            subscription_uuid = UUID(subscription_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription ID format: {subscription_id}",
            )

        # Get the subscription
        query = select(WebhookSubscription).where(
            WebhookSubscription.id == subscription_uuid
        )
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook subscription not found: {subscription_id}",
            )

        # Delete the subscription (cascade will delete delivery logs)
        await db.delete(subscription)
        await db.commit()

        logger.info(f"Webhook subscription deleted successfully: {subscription_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": subscription_id,
                "message": "Webhook subscription deleted successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook subscription {subscription_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete webhook subscription: {str(e)}",
        ) from e


@router.post(
    "/{subscription_id}/disable",
    response_model=ToggleSubscriptionResponse,
    tags=["Webhooks"],
)
async def disable_webhook_subscription(
    request: Request,
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Disable a webhook subscription.

    Disables a webhook subscription without deleting it.
    The subscription will not receive events until re-enabled.

    Args:
        request: FastAPI request object
        subscription_id: Subscription UUID
        db: Database session

    Returns:
        JSON response with disabled subscription details

    Raises:
        HTTPException(400): If subscription_id is not a valid UUID
        HTTPException(404): If subscription not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     f"http://localhost:8000/api/webhooks/{subscription_id}/disable"
        ... )
        >>> result = response.json()
        >>> assert result["is_active"] == False
    """
    try:
        logger.info(f"Disabling webhook subscription: {subscription_id}")

        # Parse subscription_id as UUID
        try:
            subscription_uuid = UUID(subscription_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription ID format: {subscription_id}",
            )

        # Get the subscription
        query = select(WebhookSubscription).where(
            WebhookSubscription.id == subscription_uuid
        )
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook subscription not found: {subscription_id}",
            )

        # Check if already disabled
        if not subscription.is_active:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "id": subscription_id,
                    "is_active": False,
                    "message": "Webhook subscription is already disabled",
                },
            )

        # Disable the subscription
        subscription.is_active = False
        await db.commit()
        await db.refresh(subscription)

        logger.info(f"Webhook subscription disabled successfully: {subscription_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(subscription.id),
                "is_active": subscription.is_active,
                "message": "Webhook subscription disabled successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling webhook subscription {subscription_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable webhook subscription: {str(e)}",
        ) from e


@router.post(
    "/{subscription_id}/enable",
    response_model=ToggleSubscriptionResponse,
    tags=["Webhooks"],
)
async def enable_webhook_subscription(
    request: Request,
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Enable a webhook subscription.

    Enables a previously disabled webhook subscription.
    The subscription will resume receiving events.

    Args:
        request: FastAPI request object
        subscription_id: Subscription UUID
        db: Database session

    Returns:
        JSON response with enabled subscription details

    Raises:
        HTTPException(400): If subscription_id is not a valid UUID
        HTTPException(404): If subscription not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     f"http://localhost:8000/api/webhooks/{subscription_id}/enable"
        ... )
        >>> result = response.json()
        >>> assert result["is_active"] == True
    """
    try:
        logger.info(f"Enabling webhook subscription: {subscription_id}")

        # Parse subscription_id as UUID
        try:
            subscription_uuid = UUID(subscription_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription ID format: {subscription_id}",
            )

        # Get the subscription
        query = select(WebhookSubscription).where(
            WebhookSubscription.id == subscription_uuid
        )
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook subscription not found: {subscription_id}",
            )

        # Check if already enabled
        if subscription.is_active:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "id": subscription_id,
                    "is_active": True,
                    "message": "Webhook subscription is already enabled",
                },
            )

        # Reset failure count and enable the subscription
        subscription.failure_count = 0
        subscription.is_active = True
        await db.commit()
        await db.refresh(subscription)

        logger.info(f"Webhook subscription enabled successfully: {subscription_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(subscription.id),
                "is_active": subscription.is_active,
                "message": "Webhook subscription enabled successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling webhook subscription {subscription_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable webhook subscription: {str(e)}",
        ) from e


@router.get(
    "/{subscription_id}/logs",
    tags=["Webhooks"],
)
async def get_webhook_delivery_logs(
    request: Request,
    subscription_id: str,
    status: Optional[str] = Query(None, description="Filter by delivery status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get delivery logs for a webhook subscription.

    Returns a paginated list of delivery logs for a specific webhook
    subscription, useful for monitoring and debugging.

    Args:
        request: FastAPI request object
        subscription_id: Subscription UUID
        status: Optional filter by delivery status (pending, success, failed, retrying)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of delivery logs

    Raises:
        HTTPException(400): If subscription_id is not a valid UUID
        HTTPException(404): If subscription not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     f"http://localhost:8000/api/webhooks/{subscription_id}/logs"
        ... )
        >>> logs = response.json()
    """
    try:
        logger.info(
            f"Fetching delivery logs for subscription {subscription_id} - "
            f"status: {status}, skip: {skip}, limit: {limit}"
        )

        # Parse subscription_id as UUID
        try:
            subscription_uuid = UUID(subscription_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription ID format: {subscription_id}",
            )

        # Verify subscription exists
        sub_query = select(WebhookSubscription).where(
            WebhookSubscription.id == subscription_uuid
        )
        sub_result = await db.execute(sub_query)
        subscription = sub_result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook subscription not found: {subscription_id}",
            )

        # Build query for delivery logs
        query = select(WebhookDeliveryLog).where(
            WebhookDeliveryLog.subscription_id == subscription_uuid
        )

        # Apply status filter if provided
        if status:
            try:
                status_enum = WebhookDeliveryStatus(status)
                query = query.where(WebhookDeliveryLog.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}. Valid values are: pending, success, failed, retrying",
                )

        # Order by most recently created
        query = query.order_by(
            WebhookDeliveryLog.created_at.desc()
        ).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        logs = result.scalars().all()

        # Convert to response format
        logs_list = []
        for log in logs:
            logs_list.append({
                "id": str(log.id),
                "subscription_id": str(log.subscription_id),
                "event_type": log.event_type,
                "event_data": log.event_data,
                "status": log.status.value,
                "status_code": log.status_code,
                "response_body": log.response_body,
                "attempt_count": log.attempt_count,
                "next_retry_at": log.next_retry_at.isoformat() if log.next_retry_at else None,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "updated_at": log.updated_at.isoformat() if log.updated_at else None,
            })

        logger.info(f"Retrieved {len(logs_list)} delivery logs")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "subscription_id": subscription_id,
                "total_logs": len(logs_list),
                "logs": logs_list,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching delivery logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch delivery logs: {str(e)}",
        ) from e


@router.get(
    "/logs/{log_id}",
    response_model=DeliveryLogDetail,
    tags=["Webhooks"],
)
async def get_delivery_log(
    request: Request,
    log_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific delivery log entry.

    Returns detailed information about a specific webhook delivery attempt,
    including the event payload, response status, and error messages.

    Args:
        request: FastAPI request object
        log_id: Delivery log UUID
        db: Database session

    Returns:
        JSON response with delivery log details

    Raises:
        HTTPException(400): If log_id is not a valid UUID
        HTTPException(404): If delivery log not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     f"http://localhost:8000/api/webhooks/logs/{log_id}"
        ... )
        >>> log = response.json()
    """
    try:
        logger.info(f"Fetching delivery log: {log_id}")

        # Parse log_id as UUID
        try:
            log_uuid = UUID(log_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid log ID format: {log_id}",
            )

        # Get the delivery log
        query = select(WebhookDeliveryLog).where(WebhookDeliveryLog.id == log_uuid)
        result = await db.execute(query)
        log = result.scalar_one_or_none()

        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery log not found: {log_id}",
            )

        log_data = {
            "id": str(log.id),
            "subscription_id": str(log.subscription_id),
            "event_type": log.event_type,
            "event_data": log.event_data,
            "status": log.status.value,
            "status_code": log.status_code,
            "response_body": log.response_body,
            "attempt_count": log.attempt_count,
            "next_retry_at": log.next_retry_at.isoformat() if log.next_retry_at else None,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "updated_at": log.updated_at.isoformat() if log.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=log_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting delivery log {log_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get delivery log: {str(e)}",
        ) from e
