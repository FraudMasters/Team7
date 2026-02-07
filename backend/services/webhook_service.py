"""
Webhook delivery service for event notification and retry logic

This module provides webhook functionality including:
- HTTP webhook delivery to subscribed endpoints
- Signature-based payload verification (HMAC-SHA256)
- Exponential backoff retry logic
- Delivery status tracking and logging
- Automatic webhook disabling on repeated failures
"""
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse

import httpx

from config import get_settings
from database import async_session_maker
from models.webhook import (
    WebhookSubscription,
    WebhookDeliveryLog,
    WebhookDeliveryStatus,
    WebhookEventType,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()

# Webhook delivery configuration
DEFAULT_TIMEOUT = 10.0  # seconds
MAX_RETRY_ATTEMPTS = 5
FAILURE_THRESHOLD = 10  # Disable webhook after this many consecutive failures
USER_AGENT = "AgentHR-Webhook/1.0"


class WebhookDeliveryError(Exception):
    """Base exception for webhook delivery errors"""

    pass


class WebhookSignatureError(WebhookDeliveryError):
    """Exception for signature-related errors"""

    pass


class WebhookHTTPError(WebhookDeliveryError):
    """Exception for HTTP-related errors"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def generate_signature(payload: Dict[str, Any], secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload.

    Args:
        payload: JSON-serializable payload dictionary
        secret: Secret key for HMAC signature

    Returns:
        Hexadecimal signature string

    Example:
        >>> signature = generate_signature({"event": "user.created"}, "secret123")
        >>> len(signature)
        64
    """
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def verify_signature(
    payload: Dict[str, Any], signature: str, secret: str
) -> bool:
    """
    Verify HMAC-SHA256 signature for webhook payload.

    Args:
        payload: JSON-serializable payload dictionary
        signature: Signature to verify (hexadecimal string)
        secret: Secret key for HMAC signature

    Returns:
        True if signature is valid, False otherwise

    Example:
        >>> payload = {"event": "user.created"}
        >>> sig = generate_signature(payload, "secret")
        >>> verify_signature(payload, sig, "secret")
        True
    """
    expected_signature = generate_signature(payload, secret)
    return hmac.compare_digest(expected_signature, signature)


def validate_webhook_url(url: str) -> bool:
    """
    Validate that a webhook URL is well-formed and uses HTTPS (or localhost for testing).

    Args:
        url: Webhook URL to validate

    Returns:
        True if URL is valid, False otherwise

    Example:
        >>> validate_webhook_url("https://example.com/webhook")
        True
        >>> validate_webhook_url("ftp://example.com/webhook")
        False
    """
    try:
        result = urlparse(url)
        if not result.scheme or not result.netloc:
            return False

        # Require HTTPS in production, allow HTTP for localhost testing
        if settings.environment == "production":
            if result.scheme != "https":
                return False
        else:
            if result.scheme not in ("http", "https"):
                return False

        return True
    except Exception:
        return False


class WebhookService:
    """
    Service for managing webhook delivery and retry logic.

    This service handles the delivery of webhook events to subscribed endpoints,
    including signature generation, HTTP delivery, retry logic with exponential
    backoff, and failure tracking.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        """
        Initialize webhook service.

        Args:
            session: Optional database session. If not provided, creates a new one.
        """
        self._session = session
        self._own_session = session is None

    async def __aenter__(self):
        """Async context manager entry."""
        if self._own_session:
            self._session = async_session_maker()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._own_session and self._session:
            await self._session.close()

    @property
    def session(self) -> AsyncSession:
        """Get the database session, creating one if needed."""
        if self._session is None:
            self._session = async_session_maker()
            self._own_session = True
        return self._session

    async def deliver_webhook(
        self,
        subscription_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        attempt_count: int = 1,
    ) -> Dict[str, Any]:
        """
        Deliver a webhook to a subscription endpoint.

        Args:
            subscription_id: UUID of the webhook subscription
            event_type: Type of event being delivered
            event_data: Event payload data
            attempt_count: Current attempt number (for retries)

        Returns:
            Dictionary with delivery result

        Raises:
            WebhookDeliveryError: If delivery fails critically
        """
        from models.base import UUIDMixin

        # Fetch subscription
        subscription = await self._get_subscription(subscription_id)
        if not subscription:
            raise WebhookDeliveryError(f"Subscription not found: {subscription_id}")

        if not subscription.is_active:
            raise WebhookDeliveryError(f"Subscription is inactive: {subscription_id}")

        if not subscription.is_subscribed_to(event_type):
            raise WebhookDeliveryError(
                f"Subscription not registered for event: {event_type}"
            )

        # Validate URL
        if not validate_webhook_url(subscription.url):
            raise WebhookDeliveryError(f"Invalid webhook URL: {subscription.url}")

        # Prepare payload
        payload = self._prepare_payload(event_type, event_data)

        # Generate signature if secret is configured
        headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-Webhook-Event": event_type,
            "X-Webhook-Delivery-ID": str(UUIDMixin.generate_uuid()),
            "X-Webhook-Timestamp": str(int(time.time())),
            "X-Webhook-Attempt": str(attempt_count),
        }

        if subscription.secret:
            signature = generate_signature(payload, subscription.secret)
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        # Deliver webhook
        try:
            status_code, response_body, elapsed = await self._send_http_request(
                subscription.url, payload, headers
            )

            # Check for success (2xx status codes)
            if 200 <= status_code < 300:
                await self._record_success(
                    subscription, event_type, event_data, status_code, response_body
                )
                return {
                    "status": "success",
                    "status_code": status_code,
                    "elapsed_seconds": elapsed,
                    "subscription_id": str(subscription_id),
                }
            else:
                # HTTP error but request was delivered
                error_msg = f"HTTP {status_code}: {response_body}"
                await self._record_failure(
                    subscription,
                    event_type,
                    event_data,
                    attempt_count,
                    error_msg,
                    status_code,
                    response_body,
                )
                raise WebhookHTTPError(error_msg, status_code)

        except httpx.TimeoutException as e:
            error_msg = f"Request timeout after {DEFAULT_TIMEOUT}s"
            await self._record_failure(
                subscription, event_type, event_data, attempt_count, error_msg
            )
            raise WebhookDeliveryError(error_msg) from e

        except httpx.RequestError as e:
            error_msg = f"Request failed: {str(e)}"
            await self._record_failure(
                subscription, event_type, event_data, attempt_count, error_msg
            )
            raise WebhookDeliveryError(error_msg) from e

    async def _get_subscription(
        self, subscription_id: str
    ) -> Optional[WebhookSubscription]:
        """Fetch a webhook subscription by ID."""
        from sqlalchemy import select

        result = await self.session.execute(
            select(WebhookSubscription).where(
                WebhookSubscription.id == subscription_id
            )
        )
        return result.scalar_one_or_none()

    def _prepare_payload(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare the webhook payload.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Formatted payload dictionary
        """
        return {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": event_data,
        }

    async def _send_http_request(
        self, url: str, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Tuple[int, Optional[str], float]:
        """
        Send HTTP request to webhook endpoint.

        Args:
            url: Webhook URL
            payload: JSON payload to send
            headers: HTTP headers

        Returns:
            Tuple of (status_code, response_body, elapsed_seconds)
        """
        start_time = time.time()

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
            )

        elapsed = time.time() - start_time

        # Try to get response body
        response_body = None
        try:
            response_body = response.text
        except Exception:
            pass

        return response.status_code, response_body, elapsed

    async def _record_success(
        self,
        subscription: WebhookSubscription,
        event_type: str,
        event_data: Dict[str, Any],
        status_code: int,
        response_body: Optional[str],
    ) -> None:
        """
        Record a successful webhook delivery.

        Args:
            subscription: Webhook subscription
            event_type: Event type delivered
            event_data: Event data delivered
            status_code: HTTP status code
            response_body: Response body from webhook endpoint
        """
        # Update subscription
        subscription.last_delivery_at = datetime.utcnow()
        subscription.failure_count = 0

        # Create delivery log
        log = WebhookDeliveryLog(
            subscription_id=subscription.id,
            event_type=event_type,
            event_data=event_data,
            status=WebhookDeliveryStatus.SUCCESS,
            status_code=status_code,
            response_body=response_body,
            attempt_count=1,
        )

        self.session.add(log)

        try:
            await self.session.commit()
            logger.info(
                f"Webhook delivered successfully: {subscription.url} - {event_type}"
            )
        except Exception as e:
            logger.error(f"Failed to record webhook success: {e}")
            await self.session.rollback()

    async def _record_failure(
        self,
        subscription: WebhookSubscription,
        event_type: str,
        event_data: Dict[str, Any],
        attempt_count: int,
        error_message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> None:
        """
        Record a failed webhook delivery and manage retry logic.

        Args:
            subscription: Webhook subscription
            event_type: Event type being delivered
            event_data: Event data being delivered
            attempt_count: Current attempt number
            error_message: Error message
            status_code: HTTP status code (if applicable)
            response_body: Response body from webhook endpoint (if applicable)
        """
        # Increment subscription failure count
        subscription.failure_count += 1

        # Check if subscription should be disabled
        if subscription.should_disable(threshold=FAILURE_THRESHOLD):
            subscription.is_active = False
            logger.warning(
                f"Webhook subscription disabled due to failures: {subscription.url}"
            )

        # Create or update delivery log
        # Check for existing pending log for this subscription and event
        from sqlalchemy import select

        existing_log = await self.session.execute(
            select(WebhookDeliveryLog).where(
                WebhookDeliveryLog.subscription_id == subscription.id,
                WebhookDeliveryLog.event_type == event_type,
                WebhookDeliveryLog.status.in_(
                    [WebhookDeliveryStatus.PENDING, WebhookDeliveryStatus.RETRYING]
                ),
            ).order_by(WebhookDeliveryLog.created_at.desc())
        )
        existing_log = existing_log.scalar_one_or_none()

        if existing_log and existing_log.should_retry(MAX_RETRY_ATTEMPTS):
            # Update existing log
            existing_log.attempt_count = attempt_count
            existing_log.status = WebhookDeliveryStatus.RETRYING
            existing_log.error_message = error_message
            existing_log.status_code = status_code
            existing_log.response_body = response_body
            existing_log.next_retry_at = existing_log.calculate_next_retry()

            log = existing_log
        else:
            # Create new delivery log
            log = WebhookDeliveryLog(
                subscription_id=subscription.id,
                event_type=event_type,
                event_data=event_data,
                status=WebhookDeliveryStatus.FAILED
                if attempt_count >= MAX_RETRY_ATTEMPTS
                else WebhookDeliveryStatus.RETRYING,
                attempt_count=attempt_count,
                error_message=error_message,
                status_code=status_code,
                response_body=response_body,
                next_retry_at=datetime.utcnow()
                + timedelta(seconds=30 * (2 ** min(attempt_count, 6)))
                if attempt_count < MAX_RETRY_ATTEMPTS
                else None,
            )
            self.session.add(log)

        try:
            await self.session.commit()
            logger.warning(
                f"Webhook delivery failed: {subscription.url} - {event_type} "
                f"(attempt {attempt_count}/{MAX_RETRY_ATTEMPTS}): {error_message}"
            )
        except Exception as e:
            logger.error(f"Failed to record webhook failure: {e}")
            await self.session.rollback()

    async def get_pending_deliveries(self, limit: int = 100) -> List[WebhookDeliveryLog]:
        """
        Get pending webhook deliveries for retry.

        Args:
            limit: Maximum number of deliveries to retrieve

        Returns:
            List of webhook delivery logs pending retry
        """
        from sqlalchemy import select

        now = datetime.utcnow()

        result = await self.session.execute(
            select(WebhookDeliveryLog)
            .where(
                WebhookDeliveryLog.status.in_(
                    [WebhookDeliveryStatus.PENDING, WebhookDeliveryStatus.RETRYING]
                ),
                WebhookDeliveryLog.next_retry_at <= now,
            )
            .order_by(WebhookDeliveryLog.next_retry_at)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def trigger_webhook(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> List[str]:
        """
        Trigger a webhook event to all active subscriptions.

        Args:
            event_type: Type of event to trigger
            event_data: Event payload data

        Returns:
            List of task IDs for the delivery tasks

        Example:
            >>> service = WebhookService()
            >>> task_ids = await service.trigger_webhook("candidate.created", {"id": 123})
        """
        from sqlalchemy import select

        # Find all active subscriptions for this event
        result = await self.session.execute(
            select(WebhookSubscription).where(
                WebhookSubscription.is_active == True,
                WebhookSubscription.events.contains([event_type]),
            )
        )
        subscriptions = result.scalars().all()

        if not subscriptions:
            logger.info(f"No active subscriptions for event: {event_type}")
            return []

        # Create delivery logs and queue tasks
        task_ids = []
        for subscription in subscriptions:
            log = WebhookDeliveryLog(
                subscription_id=subscription.id,
                event_type=event_type,
                event_data=event_data,
                status=WebhookDeliveryStatus.PENDING,
                attempt_count=0,
                next_retry_at=datetime.utcnow(),
            )
            self.session.add(log)

        try:
            await self.session.commit()
            logger.info(
                f"Queued {len(subscriptions)} webhook deliveries for: {event_type}"
            )
        except Exception as e:
            logger.error(f"Failed to queue webhook deliveries: {e}")
            await self.session.rollback()
            return []

        # Return subscription IDs for task processing
        return [str(sub.id) for sub in subscriptions]

    async def retry_failed_delivery(
        self, delivery_log_id: str
    ) -> Dict[str, Any]:
        """
        Retry a failed webhook delivery.

        Args:
            delivery_log_id: UUID of the delivery log to retry

        Returns:
            Dictionary with retry result
        """
        from sqlalchemy import select

        result = await self.session.execute(
            select(WebhookDeliveryLog).where(
                WebhookDeliveryLog.id == delivery_log_id
            )
        )
        log = result.scalar_one_or_none()

        if not log:
            raise WebhookDeliveryError(f"Delivery log not found: {delivery_log_id}")

        if not log.should_retry(MAX_RETRY_ATTEMPTS):
            return {
                "status": "skipped",
                "reason": "Max retry attempts exceeded",
            }

        # Retry the delivery
        attempt_count = log.attempt_count + 1
        return await self.deliver_webhook(
            subscription_id=str(log.subscription_id),
            event_type=log.event_type,
            event_data=log.event_data,
            attempt_count=attempt_count,
        )

    async def get_subscription_stats(
        self, subscription_id: str
    ) -> Dict[str, Any]:
        """
        Get statistics for a webhook subscription.

        Args:
            subscription_id: UUID of the subscription

        Returns:
            Dictionary with subscription statistics
        """
        from sqlalchemy import select, func
        from datetime import timedelta

        subscription = await self._get_subscription(subscription_id)
        if not subscription:
            raise WebhookDeliveryError(f"Subscription not found: {subscription_id}")

        # Get delivery stats
        result = await self.session.execute(
            select(
                func.count(WebhookDeliveryLog.id).label("total"),
                func.sum(
                    func.cast(WebhookDeliveryLog.status == WebhookDeliveryStatus.SUCCESS, type_=Integer)
                ).label("success_count"),
                func.sum(
                    func.cast(WebhookDeliveryLog.status == WebhookDeliveryStatus.FAILED, type_=Integer)
                ).label("failed_count"),
            ).where(WebhookDeliveryLog.subscription_id == subscription_id)
        )
        stats = result.one()

        # Get recent success rate (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await self.session.execute(
            select(
                func.count(WebhookDeliveryLog.id).label("total_week"),
                func.sum(
                    func.cast(WebhookDeliveryLog.status == WebhookDeliveryStatus.SUCCESS, type_=Integer)
                ).label("success_week"),
            ).where(
                WebhookDeliveryLog.subscription_id == subscription_id,
                WebhookDeliveryLog.created_at >= week_ago,
            )
        )
        week_stats = result.one()

        success_rate = (
            (stats.success_count / stats.total * 100) if stats.total > 0 else 0
        )
        week_success_rate = (
            (week_stats.success_week / week_stats.total_week * 100)
            if week_stats.total_week > 0
            else 0
        )

        return {
            "subscription_id": str(subscription_id),
            "url": subscription.url,
            "is_active": subscription.is_active,
            "events": subscription.events,
            "total_deliveries": stats.total or 0,
            "successful_deliveries": stats.success_count or 0,
            "failed_deliveries": stats.failed_count or 0,
            "success_rate_percent": round(success_rate, 2),
            "last_delivery_at": subscription.last_delivery_at.isoformat()
            if subscription.last_delivery_at
            else None,
            "failure_count": subscription.failure_count,
            "week_success_rate_percent": round(week_success_rate, 2),
        }


# Singleton instance getter
def get_webhook_service() -> WebhookService:
    """Get a webhook service instance."""
    return WebhookService()


__all__ = [
    "WebhookService",
    "get_webhook_service",
    "generate_signature",
    "verify_signature",
    "validate_webhook_url",
    "WebhookDeliveryError",
    "WebhookSignatureError",
    "WebhookHTTPError",
]
