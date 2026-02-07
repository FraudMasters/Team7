"""
Celery tasks for automated data retention cleanup

This module provides scheduled cleanup tasks for maintaining GDPR compliance
by removing or anonymizing data based on retention policies.
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from services.retention_service import RetentionService

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.retention_cleanup.cleanup_expired_data",
    bind=True,
)
def cleanup_expired_data_task(
    self,
    organization_id: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Clean up expired data based on retention policies.

    This Celery task removes or anonymizes data that has exceeded its retention
    period as defined in data retention policies. This ensures GDPR compliance
    through storage limitation and data minimization.

    Task Workflow:
    1. Get all active retention policies
    2. For each entity type, find entities exceeding retention period
    3. Process retention action (delete, anonymize, archive, flag for review)
    4. Log all actions to audit trail
    5. Return cleanup statistics

    Args:
        self: Celery task instance (bind=True)
        organization_id: Optional organization ID to limit cleanup scope
        dry_run: If True, report what would be deleted without actually deleting

    Returns:
        Dictionary containing cleanup results:
        - status: Task status (success/failed)
        - total_processed: Total entities processed
        - total_succeeded: Total entities successfully processed
        - total_failed: Total entities that failed to process
        - entity_types: Breakdown by entity type
        - processing_time_ms: Total processing time

    Example:
        >>> from tasks.retention_cleanup import cleanup_expired_data_task
        >>> task = cleanup_expired_data_task.delay()
        >>> result = task.get()
        >>> print(result['total_succeeded'])
        1523
    """
    import time
    import asyncio
    start_time = time.time()

    try:
        logger.info(
            f"Starting data retention cleanup "
            f"(org={organization_id}, dry_run={dry_run})"
        )

        # Convert organization_id string to UUID if provided
        org_uuid = UUID(organization_id) if organization_id else None

        # Use async session to perform cleanup
        async def perform_cleanup():
            async with async_session_maker() as session:
                # Create sync session wrapper for RetentionService
                from sqlalchemy.orm import sessionmaker

                # Create a sync session from the async engine
                sync_session = sessionmaker(bind=session.bind)()
                try:
                    # Create retention service
                    retention_service = RetentionService(db_session=sync_session)

                    # Perform cleanup for all entity types
                    cleanup_result = retention_service.cleanup_all_entities(
                        organization_id=org_uuid,
                        user_id=None,  # System task, no user
                        dry_run=dry_run,
                    )

                    return cleanup_result

                finally:
                    sync_session.close()

        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        cleanup_result = loop.run_until_complete(perform_cleanup())

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "status": "success",
            "organization_id": organization_id,
            "dry_run": dry_run,
            "total_processed": cleanup_result.get("total_processed", 0),
            "total_succeeded": cleanup_result.get("total_succeeded", 0),
            "total_failed": cleanup_result.get("total_failed", 0),
            "entity_types": cleanup_result.get("entity_types", {}),
            "processing_time_ms": processing_time_ms,
        }

        logger.info(
            f"Data retention cleanup completed: "
            f"{result['total_succeeded']}/{result['total_processed']} succeeded "
            f"in {processing_time_ms}ms"
        )

        return result

    except Exception as e:
        logger.error(f"Data retention cleanup failed: {e}", exc_info=True)
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "failed",
            "error": str(e),
            "organization_id": organization_id,
            "dry_run": dry_run,
            "processing_time_ms": processing_time_ms,
        }


# Alias for compatibility with verification command
cleanup_expired_data = cleanup_expired_data_task


__all__ = [
    "cleanup_expired_data_task",
    "cleanup_expired_data",
]
