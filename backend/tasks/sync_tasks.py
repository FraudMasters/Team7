"""
Celery tasks for integration synchronization.

This module provides Celery tasks for synchronizing data with external HRIS and ATS
platforms including Workday, Greenhouse, Lever, BambooHR, and Ashby. Tasks support
full and incremental syncs, scheduled syncs, error recovery, and retry logic.

Features:
- Full and incremental data synchronization
- Bi-directional sync with external platforms
- Configurable sync schedules per integration
- Error handling with automatic retry
- Sync status tracking and logging
- Progress updates for long-running syncs
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models.integration import Integration, IntegrationType, IntegrationStatus
from models.sync_log import SyncLog, SyncStatus, SyncDirection, SyncType

# Import integration services
import sys
from pathlib import Path

def _get_integration_services():
    """Lazy import of integration services."""
    _services_path = Path(__file__).parent.parent / 'services'
    if str(_services_path) not in sys.path:
        sys.path.insert(0, str(_services_path))
    from integration_service import (
        IntegrationService,
        IntegrationServiceError,
        SyncResult,
        get_integration_service,
        register_integration_service,
    )
    from ats_workday import WorkdayClient
    from ats_greenhouse import GreenhouseClient
    from ats_lever import LeverClient
    from hris_bamboohr import BambooHRClient
    from hris_ashby import AshbyClient
    return (
        IntegrationService,
        IntegrationServiceError,
        SyncResult,
        get_integration_service,
        register_integration_service,
        WorkdayClient,
        GreenhouseClient,
        LeverClient,
        BambooHRClient,
        AshbyClient,
    )

# Try direct imports for normal operation
try:
    from services.integration_service import (
        IntegrationService,
        IntegrationServiceError,
        SyncResult,
        get_integration_service,
        register_integration_service,
    )
    from services.ats_workday import WorkdayClient
    from services.ats_greenhouse import GreenhouseClient
    from services.ats_lever import LeverClient
    from services.hris_bamboohr import BambooHRClient
    from services.hris_ashby import AshbyClient
except (ImportError, ModuleNotFoundError):
    (
        IntegrationService,
        IntegrationServiceError,
        SyncResult,
        get_integration_service,
        register_integration_service,
        WorkdayClient,
        GreenhouseClient,
        LeverClient,
        BambooHRClient,
        AshbyClient,
    ) = _get_integration_services()

logger = logging.getLogger(__name__)
settings = get_settings()


# Mapping of integration types to their client classes
INTEGRATION_CLIENTS = {
    IntegrationType.WORKDAY: WorkdayClient,
    IntegrationType.GREENHOUSE: GreenhouseClient,
    IntegrationType.LEVER: LeverClient,
    IntegrationType.BAMBOOHR: BambooHRClient,
    IntegrationType.ASHBY: AshbyClient,
}


async def create_sync_log(
    integration_id: int,
    sync_type: SyncType,
    direction: SyncDirection,
    status: SyncStatus = SyncStatus.PENDING,
) -> SyncLog:
    """
    Create a sync log entry for tracking sync operations.

    Args:
        integration_id: ID of the integration being synced
        sync_type: Type of sync (full or incremental)
        direction: Direction of sync (push, pull, or bidirectional)
        status: Initial sync status

    Returns:
        Created SyncLog instance
    """
    async with async_session_maker() as session:
        sync_log = SyncLog(
            integration_id=integration_id,
            sync_type=sync_type,
            direction=direction,
            status=status,
            started_at=datetime.utcnow(),
        )
        session.add(sync_log)
        await session.commit()
        await session.refresh(sync_log)
        return sync_log


async def update_sync_log(
    sync_log_id: int,
    status: SyncStatus,
    records_processed: int = 0,
    records_succeeded: int = 0,
    records_failed: int = 0,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Update a sync log entry with results.

    Args:
        sync_log_id: ID of the sync log to update
        status: Final sync status
        records_processed: Total records processed
        records_succeeded: Records successfully synced
        records_failed: Records that failed to sync
        error_message: Error message if sync failed
        metadata: Additional sync metadata
    """
    async with async_session_maker() as session:
        update_data = {
            "status": status,
            "records_processed": records_processed,
            "records_succeeded": records_succeeded,
            "records_failed": records_failed,
            "completed_at": datetime.utcnow(),
        }

        if error_message:
            update_data["error_message"] = error_message

        if metadata:
            update_data["metadata"] = metadata

        # Calculate duration
        sync_log = await session.get(SyncLog, sync_log_id)
        if sync_log and sync_log.started_at:
            duration = (datetime.utcnow() - sync_log.started_at).total_seconds()
            update_data["duration_seconds"] = duration

        await session.execute(
            update(SyncLog)
            .where(SyncLog.id == sync_log_id)
            .values(**update_data)
        )
        await session.commit()


async def get_integration_config(integration_id: int) -> Optional[Integration]:
    """
    Retrieve integration configuration from database.

    Args:
        integration_id: ID of the integration

    Returns:
        Integration instance or None if not found
    """
    async with async_session_maker() as session:
        result = await session.execute(
            select(Integration).where(Integration.id == integration_id)
        )
        return result.scalar_one_or_none()


def create_integration_service(integration: Integration) -> IntegrationService:
    """
    Create an integration service instance for the given integration.

    Args:
        integration: Integration configuration

    Returns:
        IntegrationService instance

    Raises:
        ValueError: If integration type is not supported
    """
    integration_type = integration.integration_type
    client_class = INTEGRATION_CLIENTS.get(integration_type)

    if not client_class:
        raise ValueError(f"Unsupported integration type: {integration_type}")

    # Create service instance
    config = {
        "api_key": integration.api_key,
        "api_secret": integration.api_secret,
        "webhook_secret": integration.webhook_secret,
        "api_url": integration.api_base_url,
        "rate_limit": integration.config.get("rate_limit", 100),
        "rate_limit_window": integration.config.get("rate_limit_window", 60),
    }

    service = client_class(
        organization_id=str(integration.organization_id),
        config=config,
    )

    return service


@shared_task(
    name="tasks.sync.sync_integration",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def sync_integration_task(
    self,
    integration_id: int,
    sync_type: str = "full",
    direction: str = "pull",
    entities: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Synchronize data with an external integration platform.

    This Celery task handles the complete workflow of synchronizing data with
    external HRIS/ATS platforms:
    1. Retrieve integration configuration
    2. Create integration service instance
    3. Create sync log entry for tracking
    4. Perform sync operation (full or incremental)
    5. Update sync log with results
    6. Handle errors and retry logic

    Task Workflow:
    - Full sync: Synchronizes all data (employees, candidates, vacancies)
    - Incremental sync: Synchronizes only changed data since last sync
    - Push: Sends local data to external platform
    - Pull: Fetches data from external platform
    - Bidirectional: Syncs data in both directions

    Args:
        self: Celery task instance (bind=True)
        integration_id: ID of the integration to sync
        sync_type: Type of sync ('full' or 'incremental')
        direction: Direction of sync ('push', 'pull', or 'bidirectional')
        entities: List of entity types to sync (default: all entities)
            Options: 'employees', 'candidates', 'vacancies'

    Returns:
        Dictionary containing sync results:
        - sync_id: ID of the sync log entry
        - status: Final sync status (completed, failed, partial)
        - sync_type: Type of sync performed
        - direction: Direction of sync
        - records_processed: Total records processed
        - records_succeeded: Records successfully synced
        - records_failed: Records that failed to sync
        - duration_seconds: Total sync duration
        - error: Error message (if failed)
        - metadata: Additional sync metadata

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For integration or database errors

    Example:
        >>> from tasks.sync_tasks import sync_integration_task
        >>> task = sync_integration_task.delay(integration_id=1, sync_type="full")
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()

    # Convert string enums to actual enums
    try:
        sync_type_enum = SyncType.FULL if sync_type == "full" else SyncType.INCREMENTAL
        direction_enum = SyncDirection(direction)
    except ValueError as e:
        error_msg = f"Invalid sync_type or direction: {e}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg,
        }

    logger.info(
        f"Starting {sync_type} sync for integration {integration_id} "
        f"(direction: {direction}, entities: {entities})"
    )

    sync_log_id = None

    try:
        # Step 1: Retrieve integration configuration
        integration = None
        try:
            # Run async function in sync context
            import asyncio
            integration = asyncio.run(get_integration_config(integration_id))
        except Exception as e:
            logger.error(f"Failed to retrieve integration {integration_id}: {e}")

        if not integration:
            error_msg = f"Integration {integration_id} not found or disabled"
            logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
            }

        if integration.status != IntegrationStatus.ACTIVE:
            error_msg = f"Integration {integration_id} is not active (status: {integration.status})"
            logger.warning(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
            }

        # Step 2: Create sync log entry
        try:
            sync_log = asyncio.run(create_sync_log(
                integration_id=integration_id,
                sync_type=sync_type_enum,
                direction=direction_enum,
                status=SyncStatus.IN_PROGRESS,
            ))
            sync_log_id = sync_log.id
            logger.info(f"Created sync log {sync_log_id} for integration {integration_id}")
        except Exception as e:
            logger.error(f"Failed to create sync log: {e}")
            # Continue without sync log if creation fails

        # Step 3: Create integration service
        try:
            service = create_integration_service(integration)
            logger.info(f"Created {integration.integration_type.value} service instance")
        except Exception as e:
            error_msg = f"Failed to create integration service: {e}"
            logger.error(error_msg)

            if sync_log_id:
                asyncio.run(update_sync_log(
                    sync_log_id=sync_log_id,
                    status=SyncStatus.FAILED,
                    error_message=error_msg,
                ))

            return {
                "status": "failed",
                "error": error_msg,
                "sync_id": sync_log_id,
            }

        # Step 4: Perform sync operation
        total_processed = 0
        total_succeeded = 0
        total_failed = 0
        all_errors = []

        # Determine which entities to sync
        if entities is None:
            entities = ["employees", "candidates", "vacancies"]

        # Update progress
        progress = {
            "current": 1,
            "total": len(entities),
            "percentage": 0,
            "status": "syncing",
            "message": f"Starting sync for {len(entities)} entity types...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        for idx, entity in enumerate(entities):
            logger.info(f"Syncing {entity} for integration {integration_id}")

            progress = {
                "current": idx + 1,
                "total": len(entities),
                "percentage": int((idx + 1) / len(entities) * 100),
                "status": "syncing",
                "message": f"Syncing {entity}...",
            }
            self.update_state(state="PROGRESS", meta=progress)

            try:
                # Run async sync method
                result = asyncio.run(_sync_entity(
                    service=service,
                    entity=entity,
                    direction=direction_enum,
                    sync_type=sync_type_enum,
                ))

                total_processed += result.get("records_processed", 0)
                total_succeeded += result.get("records_succeeded", 0)
                total_failed += result.get("records_failed", 0)

                if result.get("errors"):
                    all_errors.extend(result["errors"])

                logger.info(
                    f"Synced {entity}: {result.get('records_succeeded', 0)} succeeded, "
                    f"{result.get('records_failed', 0)} failed"
                )

            except Exception as e:
                error_msg = f"Failed to sync {entity}: {e}"
                logger.error(error_msg, exc_info=True)
                all_errors.append(error_msg)
                total_failed += 1

        # Step 5: Determine final status
        duration_seconds = round(time.time() - start_time, 2)

        if total_failed == 0:
            final_status = SyncStatus.COMPLETED
        elif total_succeeded > 0:
            final_status = SyncStatus.PARTIAL
        else:
            final_status = SyncStatus.FAILED

        # Step 6: Update sync log
        if sync_log_id:
            try:
                asyncio.run(update_sync_log(
                    sync_log_id=sync_log_id,
                    status=final_status,
                    records_processed=total_processed,
                    records_succeeded=total_succeeded,
                    records_failed=total_failed,
                    error_message="\n".join(all_errors) if all_errors else None,
                    metadata={
                        "sync_type": sync_type,
                        "direction": direction,
                        "entities": entities,
                        "integration_type": integration.integration_type.value,
                    },
                ))
            except Exception as e:
                logger.error(f"Failed to update sync log: {e}")

        result = {
            "sync_id": sync_log_id,
            "status": final_status.value,
            "sync_type": sync_type,
            "direction": direction,
            "records_processed": total_processed,
            "records_succeeded": total_succeeded,
            "records_failed": total_failed,
            "duration_seconds": duration_seconds,
            "metadata": {
                "entities": entities,
                "integration_type": integration.integration_type.value,
            },
        }

        if all_errors:
            result["errors"] = all_errors

        logger.info(
            f"Sync completed for integration {integration_id}: "
            f"{total_succeeded} succeeded, {total_failed} failed, "
            f"duration: {duration_seconds}s"
        )

        return result

    except SoftTimeLimitExceeded:
        error_msg = f"Sync exceeded maximum time limit for integration {integration_id}"
        logger.error(error_msg)

        if sync_log_id:
            try:
                asyncio.run(update_sync_log(
                    sync_log_id=sync_log_id,
                    status=SyncStatus.FAILED,
                    error_message=error_msg,
                ))
            except Exception:
                pass

        return {
            "status": "failed",
            "error": error_msg,
            "sync_id": sync_log_id,
        }

    except Exception as e:
        error_msg = f"Sync failed for integration {integration_id}: {e}"
        logger.error(error_msg, exc_info=True)

        if sync_log_id:
            try:
                asyncio.run(update_sync_log(
                    sync_log_id=sync_log_id,
                    status=SyncStatus.FAILED,
                    error_message=error_msg,
                ))
            except Exception:
                pass

        # Retry on transient errors
        try:
            raise self.retry(exc=e, countdown=300)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for integration {integration_id}")
            return {
                "status": "failed",
                "error": error_msg,
                "sync_id": sync_log_id,
            }


async def _sync_entity(
    service: IntegrationService,
    entity: str,
    direction: SyncDirection,
    sync_type: SyncType,
) -> Dict[str, Any]:
    """
    Sync a specific entity type using the integration service.

    Args:
        service: Integration service instance
        entity: Entity type ('employees', 'candidates', 'vacancies')
        direction: Direction of sync
        sync_type: Type of sync

    Returns:
        Dictionary with sync results for this entity
    """
    # Map entity names to service methods
    entity_methods = {
        "employees": service.sync_employees,
        "candidates": service.sync_candidates,
        "vacancies": service.sync_vacancies,
    }

    if entity not in entity_methods:
        raise ValueError(f"Unknown entity type: {entity}")

    sync_method = entity_methods[entity]

    # Perform sync
    result = await sync_method(direction=direction)

    return {
        "records_processed": result.records_processed,
        "records_succeeded": result.records_succeeded,
        "records_failed": result.records_failed,
        "errors": result.errors,
    }


@shared_task(
    name="tasks.sync.scheduled_sync",
    bind=True,
    max_retries=2,
    default_retry_delay=300,  # 5 minutes
)
def scheduled_sync_task(
    self,
    integration_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Scheduled sync task for periodic synchronization.

    This task is typically scheduled via Celery Beat to run periodically
    (e.g., every hour, every 6 hours). It triggers sync tasks for all
    active integrations or a specific list of integrations.

    Task Workflow:
    1. Query active integrations (or use provided list)
    2. For each integration, check if sync is due based on schedule
    3. Trigger sync_integration_task for due integrations
    4. Return summary of triggered syncs

    Args:
        self: Celery task instance (bind=True)
        integration_ids: Optional list of integration IDs to sync
            (if not provided, syncs all active integrations)

    Returns:
        Dictionary containing scheduling results:
        - total_integrations: Number of integrations checked
        - triggered_syncs: Number of syncs triggered
        - skipped_syncs: Number of syncs skipped
        - failed: Number of integrations that failed to trigger
        - duration_seconds: Total duration
        - status: Task status

    Example:
        >>> from tasks.sync_tasks import scheduled_sync_task
        >>> task = scheduled_sync_task.delay()
        >>> result = task.get()
        >>> print(result['triggered_syncs'])
        5
    """
    start_time = time.time()
    logger.info("Starting scheduled sync task")

    try:
        # Query active integrations if not provided
        if integration_ids is None:
            async def get_active_integrations():
                async with async_session_maker() as session:
                    result = await session.execute(
                        select(Integration).where(
                            Integration.status == IntegrationStatus.ACTIVE
                        )
                    )
                    return result.scalars().all()

            import asyncio
            integrations = asyncio.run(get_active_integrations())
            integration_ids = [i.id for i in integrations]

        logger.info(f"Checking {len(integration_ids)} integrations for scheduled sync")

        triggered_syncs = []
        skipped_syncs = []
        failed = []

        for integration_id in integration_ids:
            try:
                # Check if sync is due based on last sync time
                async def check_sync_due(int_id: int) -> bool:
                    async with async_session_maker() as session:
                        # Get most recent completed sync
                        result = await session.execute(
                            select(SyncLog)
                            .where(SyncLog.integration_id == int_id)
                            .where(SyncLog.status == SyncStatus.COMPLETED)
                            .order_by(SyncLog.started_at.desc())
                            .limit(1)
                        )
                        last_sync = result.scalar_one_or_none()

                        if not last_sync:
                            return True  # Never synced, sync now

                        # Check if enough time has passed
                        integration = await session.get(Integration, int_id)
                        if not integration:
                            return False

                        sync_interval_hours = integration.config.get("sync_interval_hours", 6)
                        next_sync_time = last_sync.completed_at + timedelta(hours=sync_interval_hours)

                        return datetime.utcnow() >= next_sync_time

                import asyncio
                sync_due = asyncio.run(check_sync_due(integration_id))

                if sync_due:
                    # Trigger sync task
                    sync_integration_task.delay(integration_id=integration_id)
                    triggered_syncs.append(integration_id)
                    logger.info(f"Triggered sync for integration {integration_id}")
                else:
                    skipped_syncs.append(integration_id)
                    logger.debug(f"Skipped sync for integration {integration_id} (not due)")

            except Exception as e:
                logger.error(f"Failed to check/trigger sync for integration {integration_id}: {e}")
                failed.append(integration_id)

        duration_seconds = round(time.time() - start_time, 2)

        result = {
            "total_integrations": len(integration_ids),
            "triggered_syncs": len(triggered_syncs),
            "skipped_syncs": len(skipped_syncs),
            "failed": len(failed),
            "triggered_ids": triggered_syncs,
            "duration_seconds": duration_seconds,
            "status": "completed",
        }

        logger.info(
            f"Scheduled sync task completed: {len(triggered_syncs)} triggered, "
            f"{len(skipped_syncs)} skipped, {len(failed)} failed"
        )

        return result

    except Exception as e:
        logger.error(f"Scheduled sync task failed: {e}", exc_info=True)
        return {
            "total_integrations": 0,
            "triggered_syncs": 0,
            "skipped_syncs": 0,
            "failed": 0,
            "duration_seconds": round(time.time() - start_time, 2),
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    name="tasks.sync.auto_retry_failed_syncs",
    bind=True,
    max_retries=2,
    default_retry_delay=300,  # 5 minutes
)
def auto_retry_failed_syncs_task(
    self,
    hours_ago: int = 24,
    max_retry_count: int = 3,
) -> Dict[str, Any]:
    """
    Automatically retry failed syncs from the specified time period.

    This scheduled task finds failed syncs within the time window and
    automatically retries them. It respects a maximum retry count to avoid
    infinite retry loops for permanently failing syncs.

    Task Workflow:
    1. Query failed syncs from the specified time period
    2. Filter out syncs that have exceeded max retry count
    3. For each eligible failed sync, trigger a retry
    4. Track retry statistics

    Args:
        self: Celery task instance (bind=True)
        hours_ago: Look back period in hours (default: 24)
        max_retry_count: Maximum number of retry attempts (default: 3)

    Returns:
        Dictionary containing auto-retry results:
        - total_failed: Total failed syncs found
        - retried: Number of syncs retried
        - skipped: Number of syncs skipped (too many retries)
        - failed: Number of retries that failed to trigger

    Example:
        >>> from tasks.sync_tasks import auto_retry_failed_syncs_task
        >>> task = auto_retry_failed_syncs_task.delay(hours_ago=24)
        >>> result = task.get()
        >>> print(result['retried'])
        5
    """
    logger.info(f"Starting auto-retry for failed syncs (last {hours_ago} hours)")

    try:
        # Query failed syncs from the specified time period
        async def get_failed_syncs():
            async with async_session_maker() as session:
                cutoff = datetime.utcnow() - timedelta(hours=hours_ago)
                result = await session.execute(
                    select(SyncLog)
                    .where(SyncLog.status == SyncStatus.FAILED)
                    .where(SyncLog.started_at >= cutoff)
                    .order_by(SyncLog.started_at.desc())
                )
                return result.scalars().all()

        import asyncio
        failed_syncs = asyncio.run(get_failed_syncs())

        logger.info(f"Found {len(failed_syncs)} failed syncs in the last {hours_ago} hours")

        retried = []
        skipped = []
        failed = []

        for sync_log in failed_syncs:
            try:
                # Check retry count from metadata
                retry_count = sync_log.metadata.get("retry_count", 0) if sync_log.metadata else 0

                if retry_count >= max_retry_count:
                    logger.warning(
                        f"Skipping sync {sync_log.id} - already retried {retry_count} times"
                    )
                    skipped.append(sync_log.id)
                    continue

                # Trigger retry
                result = sync_integration_task.delay(
                    integration_id=sync_log.integration_id,
                    sync_type=sync_log.sync_type.value,
                    direction=sync_log.direction.value,
                )

                # Update retry count in metadata
                async def update_retry_count():
                    async with async_session_maker() as session:
                        metadata = sync_log.metadata or {}
                        metadata["retry_count"] = retry_count + 1
                        metadata["last_retried_at"] = datetime.utcnow().isoformat()

                        await session.execute(
                            update(SyncLog)
                            .where(SyncLog.id == sync_log.id)
                            .values(metadata=metadata)
                        )
                        await session.commit()

                asyncio.run(update_retry_count())

                retried.append({
                    "sync_log_id": sync_log.id,
                    "integration_id": sync_log.integration_id,
                    "retry_count": retry_count + 1,
                    "new_task_id": result.id,
                })

                logger.info(
                    f"Retried sync {sync_log.id} for integration {sync_log.integration_id} "
                    f"(attempt {retry_count + 1}/{max_retry_count})"
                )

            except Exception as e:
                logger.error(f"Failed to retry sync {sync_log.id}: {e}")
                failed.append({
                    "sync_log_id": sync_log.id,
                    "error": str(e),
                })

        result = {
            "total_failed": len(failed_syncs),
            "retried": len(retried),
            "skipped": len(skipped),
            "failed": len(failed),
            "status": "completed",
        }

        logger.info(
            f"Auto-retry completed: {len(retried)} retried, "
            f"{len(skipped)} skipped, {len(failed)} failed"
        )

        return result

    except Exception as e:
        logger.error(f"Auto-retry task failed: {e}", exc_info=True)

        try:
            raise self.retry(exc=e, countdown=300)
        except self.MaxRetriesExceededError:
            logger.error("Auto-retry max retries exceeded")
            return {
                "total_failed": 0,
                "retried": 0,
                "skipped": 0,
                "failed": 0,
                "status": "failed",
                "error": str(e),
            }


@shared_task(
    name="tasks.sync.retry_failed_sync",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def retry_failed_sync_task(
    self,
    sync_log_id: int,
) -> Dict[str, Any]:
    """
    Retry a failed sync operation.

    This task retries a previously failed sync operation. It retrieves
    the original sync log and attempts to run the sync again with the
    same parameters.

    Task Workflow:
    1. Retrieve the failed sync log entry
    2. Extract sync parameters (integration_id, sync_type, direction)
    3. Trigger new sync with same parameters
    4. Update original sync log with retry reference

    Args:
        self: Celery task instance (bind=True)
        sync_log_id: ID of the failed sync log to retry

    Returns:
        Dictionary containing retry results:
        - original_sync_id: Original sync log ID
        - new_sync_id: New sync log ID
        - status: Retry status
        - error: Error message (if retry failed)

    Example:
        >>> from tasks.sync_tasks import retry_failed_sync_task
        >>> task = retry_failed_sync_task.delay(sync_log_id=123)
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    logger.info(f"Retrying failed sync {sync_log_id}")

    try:
        # Retrieve original sync log
        async def get_sync_log():
            async with async_session_maker() as session:
                return await session.get(SyncLog, sync_log_id)

        import asyncio
        sync_log = asyncio.run(get_sync_log())

        if not sync_log:
            error_msg = f"Sync log {sync_log_id} not found"
            logger.error(error_msg)
            return {
                "original_sync_id": sync_log_id,
                "status": "failed",
                "error": error_msg,
            }

        if sync_log.status != SyncStatus.FAILED:
            error_msg = f"Sync log {sync_log_id} is not in failed status (status: {sync_log.status})"
            logger.warning(error_msg)
            return {
                "original_sync_id": sync_log_id,
                "status": "failed",
                "error": error_msg,
            }

        # Trigger new sync with same parameters
        result = sync_integration_task.delay(
            integration_id=sync_log.integration_id,
            sync_type=sync_log.sync_type.value,
            direction=sync_log.direction.value,
        )

        logger.info(
            f"Retried sync {sync_log_id} for integration {sync_log.integration_id} "
            f"(new task ID: {result.id})"
        )

        return {
            "original_sync_id": sync_log_id,
            "new_task_id": result.id,
            "integration_id": sync_log.integration_id,
            "status": "completed",
            "message": "Sync retry triggered successfully",
        }

    except Exception as e:
        logger.error(f"Failed to retry sync {sync_log_id}: {e}", exc_info=True)

        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                "original_sync_id": sync_log_id,
                "status": "failed",
                "error": str(e),
            }


@shared_task(
    name="tasks.sync.health_check",
    bind=True,
)
def sync_health_check_task(
    self,
    integration_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Health check task for integration sync system.

    This task verifies the health of integration sync system by checking:
    - Integration service availability
    - Database connectivity
    - Recent sync success rate
    - Pending/failed sync counts

    Args:
        self: Celery task instance (bind=True)
        integration_id: Optional specific integration to check

    Returns:
        Dictionary with health check results

    Example:
        >>> from tasks.sync_tasks import sync_health_check_task
        >>> task = sync_health_check_task.delay()
        >>> result = task.get()
        >>> print(result['status'])
        'healthy'
    """
    logger.info("Running sync system health check")

    results = {
        "status": "healthy",
        "checks": {},
    }

    try:
        # Check database connectivity
        async def check_db():
            async with async_session_maker() as session:
                # Simple query to test connection
                if integration_id:
                    result = await session.execute(
                        select(Integration).where(Integration.id == integration_id)
                    )
                else:
                    result = await session.execute(
                        select(Integration).limit(1)
                    )
                return result.scalar_one_or_none() is not None

        import asyncio
        db_ok = asyncio.run(check_db())

        results["checks"]["database"] = {
            "status": "ok" if db_ok else "error",
            "message": "Database connectivity OK" if db_ok else "Database connection failed",
        }

        if not db_ok:
            results["status"] = "unhealthy"

        # Check recent sync stats
        async def get_sync_stats():
            async with async_session_maker() as session:
                # Get syncs from last 24 hours
                cutoff = datetime.utcnow() - timedelta(hours=24)
                result = await session.execute(
                    select(SyncLog).where(SyncLog.started_at >= cutoff)
                )
                syncs = result.scalars().all()

                total = len(syncs)
                completed = sum(1 for s in syncs if s.status == SyncStatus.COMPLETED)
                failed = sum(1 for s in syncs if s.status == SyncStatus.FAILED)

                return {
                    "total": total,
                    "completed": completed,
                    "failed": failed,
                    "success_rate": completed / total if total > 0 else 0,
                }

        sync_stats = asyncio.run(get_sync_stats())

        results["checks"]["sync_stats"] = {
            "status": "ok" if sync_stats["success_rate"] >= 0.8 else "warning",
            "message": f"{sync_stats['completed']}/{sync_stats['total']} syncs succeeded in last 24h",
            "stats": sync_stats,
        }

        if sync_stats["success_rate"] < 0.5:
            results["status"] = "unhealthy"
        elif sync_stats["success_rate"] < 0.8 and results["status"] == "healthy":
            results["status"] = "warning"

        logger.info(f"Sync health check completed: {results['status']}")

        return results

    except Exception as e:
        logger.error(f"Sync health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "checks": {},
            "error": str(e),
        }


@shared_task(
    name="tasks.sync.cleanup_old_sync_logs",
    bind=True,
)
def cleanup_old_sync_logs_task(
    self,
    retention_days: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Clean up old sync logs based on retention policy.

    This task removes old sync logs from the database to prevent
    unlimited growth. Completed syncs older than the retention period
    are deleted, while failed and partial syncs are kept longer for
    troubleshooting.

    Retention Policy:
    - Completed syncs: retention_days (default: 30 days)
    - Partial syncs: 2 * retention_days (default: 60 days)
    - Failed syncs: 3 * retention_days (default: 90 days)

    Args:
        self: Celery task instance (bind=True)
        retention_days: Days to retain completed syncs (default: 30)

    Returns:
        Dictionary with cleanup results:
        - deleted_count: Number of sync logs deleted
        - retention_days: Retention period used
        - status: Task status

    Example:
        >>> from tasks.sync_tasks import cleanup_old_sync_logs_task
        >>> task = cleanup_old_sync_logs_task.delay(retention_days=30)
        >>> result = task.get()
        >>> print(result['deleted_count'])
        150
    """
    logger.info("Starting sync logs cleanup")

    try:
        # Get retention days from config or use default
        if retention_days is None:
            retention_days = 30

        async def cleanup_logs():
            async with async_session_maker() as session:
                # Calculate cutoff dates for different statuses
                completed_cutoff = datetime.utcnow() - timedelta(days=retention_days)
                partial_cutoff = datetime.utcnow() - timedelta(days=retention_days * 2)
                failed_cutoff = datetime.utcnow() - timedelta(days=retention_days * 3)

                # Delete old completed syncs
                completed_result = await session.execute(
                    select(SyncLog)
                    .where(SyncLog.status == SyncStatus.COMPLETED)
                    .where(SyncLog.completed_at < completed_cutoff)
                )
                completed_to_delete = completed_result.scalars().all()

                # Delete old partial syncs
                partial_result = await session.execute(
                    select(SyncLog)
                    .where(SyncLog.status == SyncStatus.PARTIAL)
                    .where(SyncLog.completed_at < partial_cutoff)
                )
                partial_to_delete = partial_result.scalars().all()

                # Delete old failed syncs
                failed_result = await session.execute(
                    select(SyncLog)
                    .where(SyncLog.status == SyncStatus.FAILED)
                    .where(SyncLog.completed_at < failed_cutoff)
                )
                failed_to_delete = failed_result.scalars().all()

                # Combine all to delete
                all_to_delete = completed_to_delete + partial_to_delete + failed_to_delete

                # Delete logs
                for log in all_to_delete:
                    await session.delete(log)

                await session.commit()

                return {
                    "completed_deleted": len(completed_to_delete),
                    "partial_deleted": len(partial_to_delete),
                    "failed_deleted": len(failed_to_delete),
                    "total_deleted": len(all_to_delete),
                }

        import asyncio
        deleted = asyncio.run(cleanup_logs())

        logger.info(
            f"Sync logs cleanup completed: {deleted['total_deleted']} logs deleted "
            f"({deleted['completed_deleted']} completed, "
            f"{deleted['partial_deleted']} partial, "
            f"{deleted['failed_deleted']} failed)"
        )

        return {
            "status": "success",
            "deleted_count": deleted["total_deleted"],
            "breakdown": {
                "completed": deleted["completed_deleted"],
                "partial": deleted["partial_deleted"],
                "failed": deleted["failed_deleted"],
            },
            "retention_days": retention_days,
        }

    except Exception as e:
        logger.error(f"Sync logs cleanup failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "deleted_count": 0,
            "error": str(e),
        }


__all__ = [
    "sync_integration_task",
    "scheduled_sync_task",
    "auto_retry_failed_syncs_task",
    "retry_failed_sync_task",
    "sync_health_check_task",
    "cleanup_old_sync_logs_task",
]
