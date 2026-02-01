"""
Celery tasks for automated audit log cleanup

This module provides scheduled cleanup tasks for maintaining audit log storage
by removing old log entries based on retention policy.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from celery import shared_task
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models.audit_log import AuditLog

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.audit_cleanup.cleanup_old_audit_logs",
    bind=True,
)
def cleanup_old_audit_logs_task(
    self,
    retention_days: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Clean up old audit logs based on retention policy.

    This Celery task removes audit log entries that are older than the
    specified retention period. This helps maintain database performance
    and storage by automatically removing old log entries.

    Task Workflow:
    1. Determine retention period (from parameter or config)
    2. Calculate cutoff date (current_date - retention_days)
    3. Query count of logs to be deleted
    4. Delete old audit log entries
    5. Return cleanup statistics

    Args:
        self: Celery task instance (bind=True)
        retention_days: Days to retain audit logs (uses config default if not specified)

    Returns:
        Dictionary containing cleanup results:
        - status: Task status (success/failed)
        - deleted_count: Number of audit log entries deleted
        - retention_days: Retention period used
        - cutoff_date: Date threshold used for cleanup
        - processing_time_ms: Total processing time

    Example:
        >>> from tasks.audit_cleanup import cleanup_old_audit_logs_task
        >>> task = cleanup_old_audit_logs_task.delay(retention_days=90)
        >>> result = task.get()
        >>> print(result['deleted_count'])
        1523
    """
    import time
    start_time = time.time()

    try:
        # Get retention days from parameter or config
        if retention_days is None:
            retention_days = settings.audit_log_retention_days

        logger.info(f"Starting audit log cleanup with retention period: {retention_days} days")

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        logger.info(f"Deleting audit logs older than: {cutoff_date.isoformat()}")

        # Use async session to delete old audit logs
        async def perform_cleanup():
            async with async_session_maker() as session:
                # First, count how many logs will be deleted
                count_query = select(AuditLog).where(
                    AuditLog.created_at < cutoff_date
                )
                result = await session.execute(count_query)
                to_delete_count = len(result.scalars().all())

                if to_delete_count == 0:
                    logger.info("No old audit logs to delete")
                    return {
                        "deleted_count": 0,
                        "cutoff_date": cutoff_date.isoformat(),
                    }

                logger.info(f"Found {to_delete_count} audit logs to delete")

                # Delete old audit logs
                delete_query = delete(AuditLog).where(
                    AuditLog.created_at < cutoff_date
                )
                delete_result = await session.execute(delete_query)
                await session.commit()

                logger.info(f"Deleted {delete_result.rowcount} audit log entries")

                return {
                    "deleted_count": delete_result.rowcount,
                    "cutoff_date": cutoff_date.isoformat(),
                }

        # Run the async cleanup
        import asyncio
        try:
            # Get or create event loop
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        cleanup_result = loop.run_until_complete(perform_cleanup())

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "status": "success",
            "deleted_count": cleanup_result["deleted_count"],
            "retention_days": retention_days,
            "cutoff_date": cleanup_result["cutoff_date"],
            "processing_time_ms": processing_time_ms,
        }

        logger.info(
            f"Audit log cleanup completed: {cleanup_result['deleted_count']} entries deleted "
            f"in {processing_time_ms}ms"
        )

        return result

    except Exception as e:
        logger.error(f"Audit log cleanup failed: {e}", exc_info=True)
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "failed",
            "error": str(e),
            "retention_days": retention_days,
            "processing_time_ms": processing_time_ms,
        }


__all__ = [
    "cleanup_old_audit_logs_task",
]
