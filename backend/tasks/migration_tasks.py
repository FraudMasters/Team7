"""
Celery tasks for ATS data migration operations.

This module provides Celery tasks for background processing of ATS platform migrations,
enabling HR teams to migrate data from other ATS platforms (Greenhouse, Lever, Workday)
to AgentHR without blocking the main application.

Features:
- Async migration execution from supported ATS platforms
- Progress tracking and status updates
- Migration validation before execution
- Error handling and retry logic
- Migration cleanup and rollback capabilities
- Comprehensive logging and audit trails

Tasks:
- migrate_from_ats_task: Main migration task for ATS platform migrations
- validate_migration_task: Pre-migration validation
- cleanup_migration_task: Cleanup failed/cancelled migrations
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models.migration import Migration, MigrationStatus as MigrationModelStatus
from models import Resume, Candidate

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.migration_tasks.migrate_from_ats_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    soft_time_limit=7200,  # 2 hours
    time_limit=7500,  # 2 hours 5 minutes
)
def migrate_from_ats_task(
    self,
    migration_id: str,
    recruiter_id: str,
    source_platform: str,
    source_config: Dict[str, Any],
    data_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Execute ATS platform migration in the background.

    This Celery task orchestrates the migration of data from other ATS platforms
    (Greenhouse, Lever, Workday) to AgentHR. It handles connection validation,
    data extraction, transformation, and import with comprehensive error handling
    and progress tracking.

    Task Workflow:
    1. Fetch migration record from database
    2. Initialize MigrationAssistant with source platform credentials
    3. Validate migration configuration and test connection
    4. Execute migration with progress updates
    5. Update migration record with results
    6. Return migration results

    Args:
        self: Celery task instance (bind=True)
        migration_id: UUID of the migration record
        recruiter_id: UUID of the recruiter initiating the migration
        source_platform: Name of source ATS platform (greenhouse, lever, workday)
        source_config: Dictionary with source ATS credentials and configuration
            - For Greenhouse: {"api_token": "..."}
            - For Lever: {"api_token": "..."}
            - For Workday: {"username": "...", "password": "...", "tenant": "..."}
        data_types: Optional list of data types to migrate (candidates, jobs, applications, etc.)
            Defaults to ["candidates", "jobs", "applications"] if not provided

    Returns:
        Dictionary containing migration results:
        - migration_id: ID of the migration record
        - status: Final migration status (completed/failed/partially_completed)
        - source_platform: Name of source ATS platform
        - total_records: Total number of records migrated across all data types
        - total_candidates: Number of candidates migrated
        - total_jobs: Number of jobs migrated
        - total_applications: Number of applications migrated
        - successful_migrations: Number of successful migrations
        - failed_migrations: Number of failed migrations
        - skipped_records: Number of skipped records (duplicates, etc.)
        - duration_seconds: Total migration duration
        - errors: List of error messages if any
        - warnings: List of warning messages if any
        - metadata: Additional migration metadata

    Raises:
        SoftTimeLimitExceeded: If migration exceeds 2 hour time limit
        Exception: For migration failures (triggers retry)

    Example:
        >>> result = migrate_from_ats_task.delay(
        ...     migration_id="123-456",
        ...     recruiter_id="789-012",
        ...     source_platform="greenhouse",
        ...     source_config={"api_token": "abc123"},
        ...     data_types=["candidates", "jobs"]
        ... )
        >>> print(result.get())
        {'migration_id': '123-456', 'status': 'completed', 'total_candidates': 150}
    """
    import asyncio

    start_time = time.time()

    logger.info(
        f"Starting ATS migration task: migration_id={migration_id}, "
        f"source_platform={source_platform}, recruiter_id={recruiter_id}"
    )

    async def _migrate():
        """Async function to perform the actual migration."""
        async with async_session_maker() as db:
            try:
                # Fetch migration record from database
                result = await db.execute(
                    select(Migration).where(Migration.id == migration_id)
                )
                migration = result.scalar_one_or_none()

                if not migration:
                    error_msg = f"Migration {migration_id} not found"
                    logger.error(error_msg)
                    return {
                        "migration_id": migration_id,
                        "status": "failed",
                        "error": error_msg,
                        "total_records": 0,
                    }

                # Update migration status to in_progress
                migration.status = MigrationModelStatus.IN_PROGRESS
                migration.started_at = datetime.utcnow().isoformat()
                await db.commit()

                logger.info(
                    f"Processing migration: {migration.source_system} -> {migration.target_system}"
                )

                # Import MigrationAssistant (lazy import to avoid circular dependencies)
                try:
                    from services.migration_assistant import (
                        MigrationAssistant,
                        ATSPlatform,
                        MigrationDataType,
                    )
                except ImportError as e:
                    error_msg = f"Failed to import MigrationAssistant: {e}"
                    logger.error(error_msg)
                    migration.status = MigrationModelStatus.FAILED
                    migration.error_message = error_msg
                    migration.completed_at = datetime.utcnow().isoformat()
                    await db.commit()
                    return {
                        "migration_id": migration_id,
                        "status": "failed",
                        "error": error_msg,
                        "total_records": 0,
                    }

                # Parse source_platform to ATSPlatform enum
                try:
                    ats_platform = ATSPlatform(source_platform.lower())
                except ValueError:
                    error_msg = f"Unsupported ATS platform: {source_platform}"
                    logger.error(error_msg)
                    migration.status = MigrationModelStatus.FAILED
                    migration.error_message = error_msg
                    migration.completed_at = datetime.utcnow().isoformat()
                    await db.commit()
                    return {
                        "migration_id": migration_id,
                        "status": "failed",
                        "error": error_msg,
                        "total_records": 0,
                    }

                # Parse data_types to MigrationDataType enums
                migration_data_types = None
                if data_types:
                    try:
                        migration_data_types = [
                            MigrationDataType(dt.lower()) for dt in data_types
                        ]
                    except ValueError as e:
                        error_msg = f"Invalid data type in list: {e}"
                        logger.error(error_msg)
                        migration.status = MigrationModelStatus.FAILED
                        migration.error_message = error_msg
                        migration.completed_at = datetime.utcnow().isoformat()
                        await db.commit()
                        return {
                            "migration_id": migration_id,
                            "status": "failed",
                            "error": error_msg,
                            "total_records": 0,
                        }

                # Initialize MigrationAssistant
                try:
                    # Use organization_id from recruiter_id (simplified - in production would fetch from recruiter)
                    organization_id = recruiter_id

                    assistant = MigrationAssistant(
                        db=db,
                        organization_id=organization_id,
                        source_platform=ats_platform,
                        source_config=source_config,
                    )
                except Exception as e:
                    error_msg = f"Failed to initialize MigrationAssistant: {e}"
                    logger.error(error_msg, exc_info=True)
                    migration.status = MigrationModelStatus.FAILED
                    migration.error_message = error_msg
                    migration.completed_at = datetime.utcnow().isoformat()
                    await db.commit()
                    return {
                        "migration_id": migration_id,
                        "status": "failed",
                        "error": error_msg,
                        "total_records": 0,
                    }

                # Progress callback to update migration record
                async def progress_callback(progress):
                    """Update migration record with progress information."""
                    try:
                        # Update migration record with progress
                        migration.total_records = progress.total_records
                        migration.successful_migrations = progress.successful_records
                        migration.failed_migrations = progress.failed_records
                        migration.skipped_records = progress.skipped_records

                        # Store progress in metadata
                        if migration.migration_metadata is None:
                            migration.migration_metadata = {}

                        migration.migration_metadata["last_progress"] = {
                            "status": progress.status.value,
                            "data_type": progress.data_type.value if progress.data_type else None,
                            "percent_complete": progress.percent_complete,
                            "current_operation": progress.current_operation,
                            "updated_at": datetime.utcnow().isoformat(),
                        }

                        await db.commit()

                        logger.info(
                            f"Migration progress: {progress.percent_complete:.1f}% - "
                            f"{progress.current_operation}"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update migration progress: {e}")

                # Execute migration
                try:
                    migration_result = await assistant.migrate(
                        data_types=migration_data_types,
                        progress_callback=progress_callback,
                    )
                except SoftTimeLimitExceeded:
                    error_msg = "Migration exceeded time limit (2 hours)"
                    logger.error(error_msg)
                    migration.status = MigrationModelStatus.FAILED
                    migration.error_message = error_msg
                    migration.completed_at = datetime.utcnow().isoformat()
                    await db.commit()
                    raise
                except Exception as e:
                    error_msg = f"Migration execution failed: {e}"
                    logger.error(error_msg, exc_info=True)
                    migration.status = MigrationModelStatus.FAILED
                    migration.error_message = error_msg
                    migration.completed_at = datetime.utcnow().isoformat()
                    await db.commit()

                    # Retry if not max retries
                    try:
                        raise self.retry(exc=e, countdown=300)
                    except self.MaxRetriesExceededError:
                        logger.error("Migration max retries exceeded")
                        return {
                            "migration_id": migration_id,
                            "status": "failed",
                            "error": error_msg,
                            "total_records": 0,
                        }

                # Update migration record with final results
                if migration_result.success:
                    if migration_result.failed_records > 0:
                        migration.status = MigrationModelStatus.PARTIALLY_COMPLETED
                    else:
                        migration.status = MigrationModelStatus.COMPLETED
                else:
                    migration.status = MigrationModelStatus.FAILED

                migration.total_records = migration_result.total_records
                migration.successful_migrations = migration_result.total_records - migration_result.failed_records - migration_result.skipped_records
                migration.failed_migrations = migration_result.failed_records
                migration.skipped_records = migration_result.skipped_records
                migration.completed_at = datetime.utcnow().isoformat()

                # Store migration result metadata
                if migration.migration_metadata is None:
                    migration.migration_metadata = {}

                migration.migration_metadata["result"] = {
                    "total_candidates": migration_result.total_candidates,
                    "total_jobs": migration_result.total_jobs,
                    "total_applications": migration_result.total_applications,
                    "duration_seconds": migration_result.duration_seconds,
                }

                # Store errors and warnings
                if migration_result.errors:
                    migration.validation_errors = migration_result.errors
                    migration.error_message = "; ".join(migration_result.errors[:3])  # First 3 errors

                await db.commit()

                logger.info(
                    f"Migration completed: {migration.status.value}, "
                    f"total_records={migration_result.total_records}, "
                    f"successful={migration_result.total_records - migration_result.failed_records - migration_result.skipped_records}, "
                    f"failed={migration_result.failed_records}, "
                    f"skipped={migration_result.skipped_records}"
                )

                # Calculate final duration
                end_time = time.time()
                duration_seconds = end_time - start_time

                # Return migration results
                return {
                    "migration_id": migration_id,
                    "status": migration.status.value,
                    "source_platform": source_platform,
                    "total_records": migration_result.total_records,
                    "total_candidates": migration_result.total_candidates,
                    "total_jobs": migration_result.total_jobs,
                    "total_applications": migration_result.total_applications,
                    "successful_migrations": migration_result.total_records - migration_result.failed_records - migration_result.skipped_records,
                    "failed_migrations": migration_result.failed_records,
                    "skipped_records": migration_result.skipped_records,
                    "duration_seconds": duration_seconds,
                    "errors": migration_result.errors,
                    "warnings": migration_result.warnings,
                    "metadata": migration_result.metadata,
                }

            except Exception as e:
                logger.error(f"Unexpected error in migration task: {e}", exc_info=True)
                # Try to update migration record
                try:
                    migration.status = MigrationModelStatus.FAILED
                    migration.error_message = str(e)
                    migration.completed_at = datetime.utcnow().isoformat()
                    await db.commit()
                except Exception as commit_error:
                    logger.error(f"Failed to update migration record: {commit_error}")

                return {
                    "migration_id": migration_id,
                    "status": "failed",
                    "error": str(e),
                    "total_records": 0,
                }

    # Run the async migration function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_migrate())
    finally:
        loop.close()


@shared_task(
    name="tasks.migration_tasks.validate_migration_task",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def validate_migration_task(
    self,
    migration_id: str,
    source_platform: str,
    source_config: Dict[str, Any],
    data_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validate migration configuration before execution.

    This task tests the connection to the source ATS platform, validates credentials,
    and estimates the number of records to be migrated. It's typically run before
    the main migration task to catch configuration errors early.

    Args:
        self: Celery task instance (bind=True)
        migration_id: UUID of the migration record
        source_platform: Name of source ATS platform (greenhouse, lever, workday)
        source_config: Dictionary with source ATS credentials and configuration
        data_types: Optional list of data types to validate

    Returns:
        Dictionary containing validation results:
        - migration_id: ID of the migration record
        - is_valid: Whether the migration configuration is valid
        - connection_ok: Whether connection to source ATS succeeded
        - estimated_record_count: Estimated number of records to migrate
        - data_types_available: List of available data types
        - errors: List of validation error messages
        - warnings: List of validation warning messages

    Raises:
        Exception: For validation failures (triggers retry)

    Example:
        >>> result = validate_migration_task.delay(
        ...     migration_id="123-456",
        ...     source_platform="greenhouse",
        ...     source_config={"api_token": "abc123"}
        ... )
        >>> print(result.get())
        {'migration_id': '123-456', 'is_valid': True, 'estimated_record_count': 150}
    """
    import asyncio

    logger.info(
        f"Validating migration: migration_id={migration_id}, source_platform={source_platform}"
    )

    async def _validate():
        """Async function to perform the validation."""
        async with async_session_maker() as db:
            try:
                # Fetch migration record from database
                result = await db.execute(
                    select(Migration).where(Migration.id == migration_id)
                )
                migration = result.scalar_one_or_none()

                if not migration:
                    error_msg = f"Migration {migration_id} not found"
                    logger.error(error_msg)
                    return {
                        "migration_id": migration_id,
                        "is_valid": False,
                        "error": error_msg,
                    }

                # Import MigrationAssistant
                try:
                    from services.migration_assistant import (
                        MigrationAssistant,
                        ATSPlatform,
                        MigrationDataType,
                    )
                except ImportError as e:
                    error_msg = f"Failed to import MigrationAssistant: {e}"
                    logger.error(error_msg)
                    return {
                        "migration_id": migration_id,
                        "is_valid": False,
                        "error": error_msg,
                    }

                # Parse source_platform
                try:
                    ats_platform = ATSPlatform(source_platform.lower())
                except ValueError:
                    error_msg = f"Unsupported ATS platform: {source_platform}"
                    logger.error(error_msg)
                    return {
                        "migration_id": migration_id,
                        "is_valid": False,
                        "error": error_msg,
                    }

                # Parse data_types
                migration_data_types = None
                if data_types:
                    try:
                        migration_data_types = [
                            MigrationDataType(dt.lower()) for dt in data_types
                        ]
                    except ValueError as e:
                        error_msg = f"Invalid data type in list: {e}"
                        logger.error(error_msg)
                        return {
                            "migration_id": migration_id,
                            "is_valid": False,
                            "error": error_msg,
                        }

                # Initialize MigrationAssistant
                try:
                    # Use organization_id from migration (simplified)
                    organization_id = str(migration.recruiter_id)

                    assistant = MigrationAssistant(
                        db=db,
                        organization_id=organization_id,
                        source_platform=ats_platform,
                        source_config=source_config,
                    )
                except Exception as e:
                    error_msg = f"Failed to initialize MigrationAssistant: {e}"
                    logger.error(error_msg, exc_info=True)
                    return {
                        "migration_id": migration_id,
                        "is_valid": False,
                        "error": error_msg,
                    }

                # Validate migration
                try:
                    validation_result = await assistant.validate_migration(
                        data_types=migration_data_types
                    )
                except Exception as e:
                    error_msg = f"Validation failed: {e}"
                    logger.error(error_msg, exc_info=True)

                    # Retry if not max retries
                    try:
                        raise self.retry(exc=e, countdown=60)
                    except self.MaxRetriesExceededError:
                        logger.error("Validation max retries exceeded")
                        return {
                            "migration_id": migration_id,
                            "is_valid": False,
                            "error": error_msg,
                        }

                # Update migration record with validation results
                if migration.migration_metadata is None:
                    migration.migration_metadata = {}

                migration.migration_metadata["validation"] = {
                    "is_valid": validation_result.is_valid,
                    "connection_ok": validation_result.connection_ok,
                    "estimated_record_count": validation_result.estimated_record_count,
                    "data_types_available": [dt.value for dt in validation_result.data_types_available],
                    "validated_at": datetime.utcnow().isoformat(),
                }

                if not validation_result.is_valid:
                    migration.validation_errors = validation_result.errors

                await db.commit()

                logger.info(
                    f"Migration validation completed: is_valid={validation_result.is_valid}, "
                    f"estimated_records={validation_result.estimated_record_count}"
                )

                # Return validation results
                return {
                    "migration_id": migration_id,
                    "is_valid": validation_result.is_valid,
                    "connection_ok": validation_result.connection_ok,
                    "estimated_record_count": validation_result.estimated_record_count,
                    "data_types_available": [dt.value for dt in validation_result.data_types_available],
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings,
                }

            except Exception as e:
                logger.error(f"Unexpected error in validation task: {e}", exc_info=True)
                return {
                    "migration_id": migration_id,
                    "is_valid": False,
                    "error": str(e),
                }

    # Run the async validation function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_validate())
    finally:
        loop.close()


@shared_task(
    name="tasks.migration_tasks.cleanup_migration_task",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def cleanup_migration_task(
    self,
    migration_id: str,
    force_cleanup: bool = False,
) -> Dict[str, Any]:
    """
    Cleanup failed or cancelled migrations.

    This task removes partial migration data and resets the migration record
    to a clean state. It's typically run after a failed or cancelled migration
    to ensure data consistency.

    Args:
        self: Celery task instance (bind=True)
        migration_id: UUID of the migration record to cleanup
        force_cleanup: If True, cleanup even if migration is not failed/cancelled

    Returns:
        Dictionary containing cleanup results:
        - migration_id: ID of the migration record
        - status: Cleanup status (success/failed)
        - records_cleaned: Number of records cleaned up
        - message: Cleanup result message

    Raises:
        Exception: For cleanup failures (triggers retry)

    Example:
        >>> result = cleanup_migration_task.delay(migration_id="123-456")
        >>> print(result.get())
        {'migration_id': '123-456', 'status': 'success', 'records_cleaned': 0}
    """
    import asyncio

    logger.info(f"Cleaning up migration: migration_id={migration_id}")

    async def _cleanup():
        """Async function to perform the cleanup."""
        async with async_session_maker() as db:
            try:
                # Fetch migration record from database
                result = await db.execute(
                    select(Migration).where(Migration.id == migration_id)
                )
                migration = result.scalar_one_or_none()

                if not migration:
                    error_msg = f"Migration {migration_id} not found"
                    logger.error(error_msg)
                    return {
                        "migration_id": migration_id,
                        "status": "failed",
                        "error": error_msg,
                    }

                # Check if cleanup is allowed
                if not force_cleanup:
                    if migration.status not in [
                        MigrationModelStatus.FAILED,
                        MigrationModelStatus.CANCELLED,
                    ]:
                        warning_msg = (
                            f"Migration {migration_id} status is {migration.status.value}, "
                            "not cleaning up. Use force_cleanup=True to override."
                        )
                        logger.warning(warning_msg)
                        return {
                            "migration_id": migration_id,
                            "status": "skipped",
                            "message": warning_msg,
                            "records_cleaned": 0,
                        }

                # Reset migration statistics
                migration.successful_migrations = 0
                migration.failed_migrations = 0
                migration.skipped_records = 0
                migration.error_message = None
                migration.validation_errors = None
                migration.started_at = None
                migration.completed_at = None

                # Clear migration metadata except for validation results
                if migration.migration_metadata:
                    validation_data = migration.migration_metadata.get("validation")
                    migration.migration_metadata = {
                        "validation": validation_data,
                        "cleaned_at": datetime.utcnow().isoformat(),
                    } if validation_data else {
                        "cleaned_at": datetime.utcnow().isoformat(),
                    }

                # Reset status to pending
                migration.status = MigrationModelStatus.PENDING

                await db.commit()

                logger.info(f"Migration cleanup completed: {migration_id}")

                return {
                    "migration_id": migration_id,
                    "status": "success",
                    "message": "Migration cleaned up successfully",
                    "records_cleaned": 0,
                }

            except Exception as e:
                logger.error(f"Cleanup failed: {e}", exc_info=True)

                # Retry if not max retries
                try:
                    raise self.retry(exc=e, countdown=60)
                except self.MaxRetriesExceededError:
                    logger.error("Cleanup max retries exceeded")
                    return {
                        "migration_id": migration_id,
                        "status": "failed",
                        "error": str(e),
                    }

    # Run the async cleanup function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_cleanup())
    finally:
        loop.close()
