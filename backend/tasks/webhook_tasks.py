"""
Celery tasks for webhook delivery and retry processing

This module provides webhook-related tasks including:
- Single webhook delivery with retry logic
- Bulk webhook delivery for event broadcasting
- Scheduled retry processing for failed webhooks
- Webhook health checks and cleanup
- Subscription statistics aggregation
- Workflow trigger integration for webhook events
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from celery import shared_task
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models.webhook import (
    WebhookSubscription,
    WebhookDeliveryLog,
    WebhookDeliveryStatus,
    WebhookEventType,
)

# Import webhook_service - lazy import to avoid module load errors
import sys
from pathlib import Path

def _get_webhook_functions():
    """Lazy import of webhook functions."""
    _services_path = Path(__file__).parent.parent / "services"
    if str(_services_path) not in sys.path:
        sys.path.insert(0, str(_services_path))
    from webhook_service import get_webhook_service
    return get_webhook_service

# For direct imports compatibility
try:
    from services.webhook_service import get_webhook_service
except (ImportError, ModuleNotFoundError):
    get_webhook_service = _get_webhook_functions


def _get_workflow_trigger_task():
    """Lazy import of workflow trigger task."""
    _tasks_path = Path(__file__).parent
    if str(_tasks_path) not in sys.path:
        sys.path.insert(0, str(_tasks_path))
    from workflow_tasks import trigger_webhook_workflow_task
    return trigger_webhook_workflow_task

# For direct imports compatibility
try:
    from tasks.workflow_tasks import trigger_webhook_workflow_task
except (ImportError, ModuleNotFoundError):
    trigger_webhook_workflow_task = _get_workflow_trigger_task

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.webhook.deliver_webhook",
    bind=True,
    max_retries=5,
    default_retry_delay=60,
)
def deliver_webhook_task(
    self,
    subscription_id: str,
    event_type: str,
    event_data: Dict[str, Any],
    attempt_count: int = 1,
) -> Dict[str, Any]:
    """
    Deliver a webhook to a single subscription endpoint.

    This task performs the actual HTTP webhook delivery with signature
    generation, retry logic, and status tracking.

    Args:
        self: Celery task instance (bind=True)
        subscription_id: UUID of the webhook subscription
        event_type: Type of event being delivered
        event_data: Event payload data
        attempt_count: Current attempt number (for retries)

    Returns:
        Dictionary with delivery result

    Example:
        >>> from tasks import deliver_webhook_task
        >>> result = deliver_webhook_task.delay(
        ...     subscription_id="abc-123",
        ...     event_type="candidate.created",
        ...     event_data={"id": 123}
        ... )
    """
    import asyncio

    logger.info(
        f"Delivering webhook: {event_type} to subscription {subscription_id} "
        f"(attempt {attempt_count})"
    )

    async def _deliver():
        webhook_service = get_webhook_service()
        return await webhook_service.deliver_webhook(
            subscription_id=subscription_id,
            event_type=event_type,
            event_data=event_data,
            attempt_count=attempt_count,
        )

    try:
        result = asyncio.run(_deliver())
        logger.info(
            f"Webhook delivery successful: {subscription_id} - {event_type}"
        )
        return result

    except Exception as e:
        logger.error(f"Webhook delivery failed: {e}", exc_info=True)

        # Retry with exponential backoff
        try:
            # Exponential backoff: 60s, 120s, 240s, 480s, 960s
            countdown = 60 * (2 ** (attempt_count - 1))
            raise self.retry(exc=e, countdown=countdown)
        except self.MaxRetriesExceededError:
            logger.error(
                f"Webhook delivery max retries exceeded: {subscription_id} - {event_type}"
            )
            return {
                "status": "failed",
                "error": str(e),
                "subscription_id": subscription_id,
                "event_type": event_type,
            }


@shared_task(
    name="tasks.webhook.trigger_event",
    bind=True,
)
def trigger_webhook_event_task(
    self,
    event_type: str,
    event_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Trigger a webhook event to all active subscriptions and associated workflows.

    This task broadcasts an event to all subscribers, creating individual
    delivery tasks for each subscription. Additionally, it triggers any
    workflows that are configured to be triggered by this webhook event.

    Args:
        self: Celery task instance (bind=True)
        event_type: Type of event to trigger
        event_data: Event payload data

    Returns:
        Dictionary with triggering results including webhook and workflow info

    Example:
        >>> from tasks import trigger_webhook_event_task
        >>> result = trigger_webhook_event_task.delay(
        ...     event_type="candidate.created",
        ...     event_data={"id": 123, "name": "John Doe"}
        ... )
    """
    import asyncio

    logger.info(f"Triggering webhook event: {event_type}")

    async def _trigger():
        webhook_service = get_webhook_service()
        subscription_ids = await webhook_service.trigger_webhook(
            event_type=event_type,
            event_data=event_data,
        )

        # Queue individual delivery tasks
        task_ids = []
        for sub_id in subscription_ids:
            task = deliver_webhook_task.delay(
                subscription_id=sub_id,
                event_type=event_type,
                event_data=event_data,
                attempt_count=1,
            )
            task_ids.append(str(task.id))

        return {
            "queued_count": len(subscription_ids),
            "task_ids": task_ids,
        }

    try:
        webhook_result = asyncio.run(_trigger())
        logger.info(
            f"Webhook event triggered: {event_type} - {webhook_result['queued_count']} subscriptions"
        )

        # Trigger workflows that listen to this webhook event
        # This runs asynchronously and doesn't block the webhook delivery
        try:
            workflow_task = _get_workflow_trigger_task()
            workflow_result = workflow_task.delay(
                webhook_event=event_type,
                event_data=event_data,
            )
            logger.info(
                f"Workflow trigger queued for event: {event_type} (task: {workflow_result.id})"
            )
            webhook_result["workflow_task_id"] = str(workflow_result.id)
        except Exception as workflow_error:
            # Log workflow trigger failure but don't fail the webhook delivery
            logger.warning(
                f"Failed to queue workflow trigger for {event_type}: {workflow_error}"
            )
            webhook_result["workflow_error"] = str(workflow_error)

        return webhook_result

    except Exception as e:
        logger.error(f"Webhook event trigger failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "event_type": event_type,
        }


@shared_task(
    name="tasks.webhook.process_retry_queue",
    bind=True,
)
def process_webhook_retry_queue_task(self, limit: int = 100) -> Dict[str, Any]:
    """
    Process pending webhook deliveries for retry.

    This scheduled task retrieves pending webhook deliveries and attempts
    to redeliver them. Should be run periodically (e.g., every minute).

    Args:
        self: Celery task instance (bind=True)
        limit: Maximum number of deliveries to process (default: 100)

    Returns:
        Dictionary with retry processing results

    Example:
        >>> from tasks import process_webhook_retry_queue_task
        >>> result = process_webhook_retry_queue_task.delay()
    """
    import asyncio

    logger.info("Processing webhook retry queue")

    async def _process():
        webhook_service = get_webhook_service()
        pending_deliveries = await webhook_service.get_pending_deliveries(
            limit=limit
        )

        results = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
        }

        for delivery_log in pending_deliveries:
            try:
                await webhook_service.retry_failed_delivery(
                    delivery_log_id=str(delivery_log.id)
                )
                results["processed"] += 1
                if delivery_log.is_successful():
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(
                    f"Failed to retry webhook delivery {delivery_log.id}: {e}"
                )
                results["failed"] += 1

        return results

    try:
        result = asyncio.run(_process())
        logger.info(
            f"Webhook retry queue processed: {result['processed']} deliveries "
            f"({result['succeeded']} succeeded, {result['failed']} failed)"
        )
        return result

    except Exception as e:
        logger.error(f"Webhook retry queue processing failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    name="tasks.webhook.bulk_deliver",
    bind=True,
)
def bulk_deliver_webhooks_task(
    self,
    event_type: str,
    event_data: Dict[str, Any],
    subscription_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Bulk deliver webhooks to multiple subscriptions.

    This task delivers a webhook event to multiple subscriptions in parallel.
    If subscription_ids is not provided, delivers to all active subscriptions
    for the event type.

    Args:
        self: Celery task instance (bind=True)
        event_type: Type of event to deliver
        event_data: Event payload data
        subscription_ids: Optional list of subscription IDs to deliver to

    Returns:
        Dictionary with bulk delivery results

    Example:
        >>> from tasks import bulk_deliver_webhooks_task
        >>> result = bulk_deliver_webhooks_task.delay(
        ...     event_type="candidate.created",
        ...     event_data={"id": 123},
        ...     subscription_ids=["sub-1", "sub-2"]
        ... )
    """
    logger.info(f"Bulk delivering webhook: {event_type}")

    if not subscription_ids:
        # Use trigger event to get all subscriptions
        return trigger_webhook_event_task(event_type=event_type, event_data=event_data)

    # Queue individual delivery tasks
    task_ids = []
    for sub_id in subscription_ids:
        task = deliver_webhook_task.delay(
            subscription_id=sub_id,
            event_type=event_type,
            event_data=event_data,
            attempt_count=1,
        )
        task_ids.append(str(task.id))

    logger.info(
        f"Bulk webhook delivery queued: {len(task_ids)} subscriptions for {event_type}"
    )

    return {
        "status": "queued",
        "event_type": event_type,
        "subscription_count": len(subscription_ids),
        "task_ids": task_ids,
    }


@shared_task(
    name="tasks.webhook.health_check",
    bind=True,
)
def webhook_health_check_task(self) -> Dict[str, Any]:
    """
    Health check task for the webhook system.

    Verifies:
    - Webhook service is operational
    - Active subscriptions count
    - Pending delivery count
    - Recent success rate

    Returns:
        Dictionary with health check results
    """
    import asyncio

    logger.info("Running webhook health check")

    async def _check():
        from sqlalchemy import select, func
        from datetime import datetime, timedelta

        async with async_session_maker() as session:
            # Count active subscriptions
            active_subs = await session.execute(
                select(func.count(WebhookSubscription.id)).where(
                    WebhookSubscription.is_active == True
                )
            )
            active_count = active_subs.scalar() or 0

            # Count pending deliveries
            pending_deliveries = await session.execute(
                select(func.count(WebhookDeliveryLog.id)).where(
                    WebhookDeliveryLog.status.in_(
                        [WebhookDeliveryStatus.PENDING, WebhookDeliveryStatus.RETRYING]
                    )
                )
            )
            pending_count = pending_deliveries.scalar() or 0

            # Calculate success rate (last 24 hours)
            day_ago = datetime.utcnow() - timedelta(days=1)
            stats = await session.execute(
                select(
                    func.count(WebhookDeliveryLog.id).label("total"),
                    func.sum(
                        func.cast(
                            WebhookDeliveryLog.status == WebhookDeliveryStatus.SUCCESS,
                            type_=int,
                        )
                    ).label("success"),
                ).where(WebhookDeliveryLog.created_at >= day_ago)
            )
            stats = stats.one()
            success_rate = (
                (stats.success / stats.total * 100) if stats.total and stats.total > 0 else 100
            )

            return {
                "status": "healthy",
                "active_subscriptions": active_count,
                "pending_deliveries": pending_count,
                "24h_success_rate_percent": round(success_rate, 2),
            }

    try:
        result = asyncio.run(_check())
        logger.info(f"Webhook health check completed: {result['status']}")
        return result

    except Exception as e:
        logger.error(f"Webhook health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@shared_task(
    name="tasks.webhook.cleanup_old_logs",
    bind=True,
)
def cleanup_old_webhook_logs_task(
    self, retention_days: int = 30
) -> Dict[str, Any]:
    """
    Clean up old webhook delivery logs based on retention policy.

    Args:
        self: Celery task instance (bind=True)
        retention_days: Days to retain logs (default: 30)

    Returns:
        Dictionary with cleanup results
    """
    import asyncio

    logger.info(f"Starting webhook log cleanup (retention: {retention_days} days)")

    async def _cleanup():
        from sqlalchemy import delete
        from datetime import datetime, timedelta

        async with async_session_maker() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # Delete old successful delivery logs
            result = await session.execute(
                delete(WebhookDeliveryLog).where(
                    WebhookDeliveryLog.status == WebhookDeliveryStatus.SUCCESS,
                    WebhookDeliveryLog.created_at < cutoff_date,
                )
            )
            deleted_count = result.rowcount

            await session.commit()

            logger.info(f"Webhook log cleanup completed: {deleted_count} logs deleted")

            return {
                "status": "success",
                "deleted_count": deleted_count,
                "retention_days": retention_days,
            }

    try:
        return asyncio.run(_cleanup())

    except Exception as e:
        logger.error(f"Webhook log cleanup failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    name="tasks.webhook.update_subscription_stats",
    bind=True,
)
def update_subscription_stats_task(self, subscription_id: str) -> Dict[str, Any]:
    """
    Update cached statistics for a webhook subscription.

    This task recalculates subscription statistics for monitoring
    and dashboard display.

    Args:
        self: Celery task instance (bind=True)
        subscription_id: UUID of the subscription

    Returns:
        Dictionary with subscription statistics

    Example:
        >>> from tasks import update_subscription_stats_task
        >>> result = update_subscription_stats_task.delay("sub-abc-123")
    """
    import asyncio

    logger.info(f"Updating webhook subscription stats: {subscription_id}")

    async def _update():
        webhook_service = get_webhook_service()
        stats = await webhook_service.get_subscription_stats(subscription_id)
        return stats

    try:
        result = asyncio.run(_update())
        logger.info(f"Webhook subscription stats updated: {subscription_id}")
        return result

    except Exception as e:
        logger.error(
            f"Failed to update webhook subscription stats: {e}", exc_info=True
        )
        return {
            "status": "failed",
            "error": str(e),
            "subscription_id": subscription_id,
        }


@shared_task(
    name="tasks.webhook.redeliver_event",
    bind=True,
    max_retries=3,
)
def redeliver_webhook_event_task(
    self,
    event_type: str,
    event_data: Dict[str, Any],
    subscription_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Redeliver a webhook event.

    This task is used to manually redeliver an event, either to a specific
    subscription or to all active subscribers.

    Args:
        self: Celery task instance (bind=True)
        event_type: Type of event to redeliver
        event_data: Event payload data
        subscription_id: Optional specific subscription to deliver to

    Returns:
        Dictionary with redelivery results

    Example:
        >>> from tasks import redeliver_webhook_event_task
        >>> result = redeliver_webhook_event_task.delay(
        ...     event_type="candidate.created",
        ...     event_data={"id": 123},
        ...     subscription_id="sub-abc-123"
        ... )
    """
    logger.info(f"Redelivering webhook event: {event_type}")

    try:
        if subscription_id:
            # Deliver to specific subscription
            return deliver_webhook_task.delay(
                subscription_id=subscription_id,
                event_type=event_type,
                event_data=event_data,
                attempt_count=1,
            ).get(timeout=30)
        else:
            # Deliver to all subscribers
            return trigger_webhook_event_task.delay(
                event_type=event_type,
                event_data=event_data,
            ).get(timeout=30)

    except Exception as e:
        logger.error(f"Webhook event redelivery failed: {e}", exc_info=True)

        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "error": str(e),
                "event_type": event_type,
            }


__all__ = [
    "deliver_webhook_task",
    "trigger_webhook_event_task",
    "process_webhook_retry_queue_task",
    "bulk_deliver_webhooks_task",
    "webhook_health_check_task",
    "cleanup_old_webhook_logs_task",
    "update_subscription_stats_task",
    "redeliver_webhook_event_task",
]
