"""
Celery tasks for automated backup operations

This module provides scheduled and manual backup tasks including:
- Daily automated backups
- Backup cleanup (retention enforcement)
- S3 sync for off-site backups
- Backup integrity verification
- Failure notifications
"""
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

from celery import shared_task
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models.backup import Backup, BackupConfig, BackupType, BackupStatus

# Import backup_service - lazy import to avoid module load errors
import sys
from pathlib import Path

def _get_backup_functions():
    """Lazy import of backup functions."""
    _services_path = Path(__file__).parent.parent / 'services'
    if str(_services_path) not in sys.path:
        sys.path.insert(0, str(_services_path))
    from backup_service import get_backup_service, ensure_backup_dirs
    return get_backup_service, ensure_backup_dirs

# For direct imports compatibility
try:
    from services.backup_service import get_backup_service, ensure_backup_dirs
except (ImportError, ModuleNotFoundError):
    get_backup_service, ensure_backup_dirs = _get_backup_functions

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.backup.daily_backup",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def daily_backup_task(self) -> Dict[str, Any]:
    """
    Scheduled daily backup task.

    Creates a full backup of database, files, and models.
    Configured via Celery beat to run at specified times (default: 2 AM).

    Returns:
        Dictionary with backup results
    """
    logger.info("Starting daily automated backup")

    try:
        # Get backup service
        backup_service = get_backup_service()

        # Create full backup
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"daily_{timestamp}"

        result = backup_service.create_full_backup(
            name=backup_name,
            compression=True,
            incremental=False,  # Daily backups are full
        )

        logger.info(f"Daily backup completed: {backup_name}")

        # Schedule S3 upload if enabled
        # This is done in a separate task for parallel execution
        upload_to_s3_task.delay(result["path"], backup_name)

        return {
            "status": "success",
            "backup_name": backup_name,
            "backup_path": result["path"],
            "size_bytes": result["size_bytes"],
            "elapsed_seconds": result["elapsed_seconds"],
        }

    except Exception as e:
        logger.error(f"Daily backup failed: {e}", exc_info=True)

        # Send notification
        send_backup_failure_notification("daily_backup", str(e))

        # Retry with backoff
        try:
            raise self.retry(exc=e, countdown=300)
        except self.MaxRetriesExceededError:
            logger.error("Daily backup max retries exceeded")
            return {
                "status": "failed",
                "error": str(e),
            }


@shared_task(
    name="tasks.backup.create_backup",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def create_backup_task(
    self,
    backup_type: str = "full",
    name: Optional[str] = None,
    is_incremental: bool = False,
    upload_to_s3: bool = False,
) -> Dict[str, Any]:
    """
    Create a backup of the specified type.

    Args:
        backup_type: Type of backup (database, files, models, full)
        name: Optional name for the backup
        is_incremental: Create incremental backup if possible
        upload_to_s3: Upload to S3 after creation

    Returns:
        Dictionary with backup results
    """
    logger.info(f"Creating {backup_type} backup (incremental={is_incremental})")

    try:
        backup_service = get_backup_service()

        if backup_type == "database":
            result = backup_service.create_database_backup(
                name=name,
                compression=True,
            )
        elif backup_type == "files":
            parent = None
            if is_incremental:
                parent = backup_service.find_parent_backup("files")
            result = backup_service.create_files_backup(
                name=name,
                compression=True,
                incremental=is_incremental,
                parent_backup_path=parent,
            )
        elif backup_type == "models":
            result = backup_service.create_models_backup(
                name=name,
                compression=True,
            )
        else:  # full
            result = backup_service.create_full_backup(
                name=name,
                compression=True,
                incremental=is_incremental,
            )

        response = {
            "status": "success",
            "backup_type": backup_type,
            "backup_path": result["path"],
            "size_bytes": result["size_bytes"],
            "checksum": result["checksum"],
            "elapsed_seconds": result["elapsed_seconds"],
        }

        # Upload to S3 if requested
        if upload_to_s3:
            upload_to_s3_task.delay(result["path"], name or result["path"].split("/")[-1])

        logger.info(f"Backup created successfully: {result['path']}")

        return response

    except Exception as e:
        logger.error(f"Backup creation failed: {e}", exc_info=True)
        send_backup_failure_notification(f"create_{backup_type}", str(e))

        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "error": str(e),
            }


@shared_task(
    name="tasks.backup.cleanup_old_backups",
    bind=True,
)
def cleanup_old_backups_task(self, retention_days: Optional[int] = None) -> Dict[str, Any]:
    """
    Clean up old backups based on retention policy.

    Args:
        retention_days: Days to retain backups (uses default if not specified)

    Returns:
        Dictionary with cleanup results
    """
    logger.info("Starting backup cleanup")

    try:
        backup_service = get_backup_service()

        # Get retention days from config or use default
        if retention_days is None:
            # Could fetch from database config, default to 30
            retention_days = 30

        deleted = backup_service.cleanup_old_backups(
            retention_days=retention_days,
        )

        logger.info(f"Backup cleanup completed: {len(deleted)} backups deleted")

        return {
            "status": "success",
            "deleted_count": len(deleted),
            "deleted_paths": deleted,
            "retention_days": retention_days,
        }

    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    name="tasks.backup.upload_to_s3",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def upload_to_s3_task(
    self,
    backup_path: str,
    backup_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Upload a backup to S3-compatible storage.

    Args:
        backup_path: Path to the backup file
        backup_name: Optional name for the S3 object

    Returns:
        Dictionary with upload results
    """
    logger.info(f"Uploading backup to S3: {backup_path}")

    try:
        # Get S3 configuration from database
        s3_config = get_s3_config()

        if not s3_config.get("enabled"):
            logger.info("S3 backup is disabled, skipping upload")
            return {
                "status": "skipped",
                "reason": "S3 backup disabled",
            }

        backup_service = get_backup_service(s3_config=s3_config)

        s3_key = f"backups/{backup_name}" if backup_name else None
        result = backup_service.upload_to_s3(
            backup_path=backup_path,
            s3_key=s3_key,
        )

        logger.info(f"S3 upload completed: {result['s3_key']}")

        return {
            "status": "success",
            "s3_key": result["s3_key"],
            "bucket": result["bucket"],
            "size_bytes": result["size_bytes"],
        }

    except Exception as e:
        logger.error(f"S3 upload failed: {e}", exc_info=True)

        try:
            raise self.retry(exc=e, countdown=300)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "error": str(e),
            }


@shared_task(
    name="tasks.backup.verify_integrity",
    bind=True,
)
def verify_backup_integrity_task(
    self,
    backup_path: str,
    expected_checksum: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verify the integrity of a backup file.

    Args:
        backup_path: Path to the backup file
        expected_checksum: Expected SHA256 checksum

    Returns:
        Dictionary with verification results
    """
    logger.info(f"Verifying backup integrity: {backup_path}")

    try:
        backup_service = get_backup_service()
        result = backup_service.verify_backup_integrity(
            backup_path=backup_path,
            expected_checksum=expected_checksum,
        )

        if result.get("valid"):
            logger.info(f"Backup integrity verified: {backup_path}")
        else:
            logger.warning(f"Backup integrity check failed: {backup_path}")

        return result

    except Exception as e:
        logger.error(f"Backup verification failed: {e}", exc_info=True)
        return {
            "valid": False,
            "error": str(e),
        }


@shared_task(
    name="tasks.backup.restore_from_backup",
    bind=True,
)
def restore_from_backup_task(
    self,
    backup_path: str,
    backup_type: str = "full",
    create_backup_before: bool = True,
) -> Dict[str, Any]:
    """
    Restore from a backup file.

    Args:
        backup_path: Path to the backup file
        backup_type: Type of restore (full, database, files, models)
        create_backup_before: Create a backup before restoring

    Returns:
        Dictionary with restore results
    """
    logger.info(f"Starting restore from: {backup_path}")

    try:
        backup_service = get_backup_service()

        # Create backup before restore if requested
        if create_backup_before:
            logger.info("Creating pre-restore backup")
            pre_restore_name = f"pre_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            backup_service.create_full_backup(name=pre_restore_name)

        # Perform restore
        if backup_type == "database":
            result = backup_service.restore_database_backup(backup_path)
        elif backup_type == "files":
            result = backup_service.restore_files_backup(backup_path)
        elif backup_type == "models":
            result = backup_service.restore_models_backup(backup_path)
        else:  # full
            result = backup_service.restore_full_backup(backup_path)

        logger.info(f"Restore completed successfully in {result.get('elapsed_seconds', 0):.1f}s")

        return {
            "status": "success",
            "backup_path": backup_path,
            "elapsed_seconds": result.get("elapsed_seconds", 0),
        }

    except Exception as e:
        logger.error(f"Restore failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    name="tasks.backup.sync_all_to_s3",
    bind=True,
)
def sync_all_to_s3_task(self) -> Dict[str, Any]:
    """
    Sync all local backups to S3 storage.

    This task uploads all local backups that haven't been uploaded yet.

    Returns:
        Dictionary with sync results
    """
    logger.info("Starting S3 sync for all backups")

    try:
        s3_config = get_s3_config()

        if not s3_config.get("enabled"):
            return {
                "status": "skipped",
                "reason": "S3 backup disabled",
            }

        backup_service = get_backup_service(s3_config=s3_config)
        local_backups = backup_service.get_backups_list()
        s3_backups = backup_service.list_s3_backups()

        # Track which local backups are already on S3
        s3_keys = {b["s3_key"].split("/")[-1] for b in s3_backups}

        uploaded = []
        skipped = []

        for backup in local_backups:
            backup_name = backup["path"].split("/")[-1]
            if backup_name not in s3_keys:
                try:
                    backup_service.upload_to_s3(
                        backup["path"],
                        s3_key=f"backups/{backup_name}",
                    )
                    uploaded.append(backup["path"])
                except Exception as e:
                    logger.error(f"Failed to upload {backup_name}: {e}")
            else:
                skipped.append(backup["path"])

        logger.info(f"S3 sync completed: {len(uploaded)} uploaded, {len(skipped)} skipped")

        return {
            "status": "success",
            "uploaded_count": len(uploaded),
            "skipped_count": len(skipped),
            "uploaded": uploaded,
        }

    except Exception as e:
        logger.error(f"S3 sync failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }


def get_s3_config() -> Dict[str, Any]:
    """
    Get S3 configuration from environment variables.

    In a full implementation, this would fetch from the database.
    For now, uses environment variables.

    Returns:
        Dictionary with S3 configuration
    """
    return {
        "enabled": os.getenv("BACKUP_S3_ENABLED", "false").lower() == "true",
        "bucket": os.getenv("BACKUP_S3_BUCKET"),
        "endpoint": os.getenv("BACKUP_S3_ENDPOINT"),
        "access_key": os.getenv("BACKUP_S3_ACCESS_KEY"),
        "secret_key": os.getenv("BACKUP_S3_SECRET_KEY"),
        "region": os.getenv("BACKUP_S3_REGION", "us-east-1"),
    }


def send_backup_failure_notification(operation: str, error_message: str) -> None:
    """
    Send notification on backup failure.

    Args:
        operation: Name of the failed operation
        error_message: Error message
    """
    # Get notification email from config
    notification_email = os.getenv("BACKUP_NOTIFICATION_EMAIL")

    if not notification_email:
        logger.warning("No notification email configured")
        return

    # In a full implementation, this would send an email
    # For now, just log the notification
    logger.error(
        f"BACKUP FAILURE NOTIFICATION for {operation}: {error_message} "
        f"(would send to: {notification_email})"
    )

    # TODO: Implement email notification
    # Could use Celery with tasks like:
    # - send_email_task
    # - send_slack_notification
    # - send_webhook_notification


@shared_task(
    name="tasks.backup.health_check",
    bind=True,
)
def backup_health_check_task(self) -> Dict[str, Any]:
    """
    Health check task for the backup system.

    Verifies:
    - Backup directories are accessible
    - Required tools are available (pg_dump, rsync, gzip)
    - Disk space is sufficient

    Returns:
        Dictionary with health check results
    """
    logger.info("Running backup health check")

    results = {
        "status": "healthy",
        "checks": {},
    }

    # Check backup directories
    try:
        ensure_backup_dirs()
        results["checks"]["directories"] = {
            "status": "ok",
            "message": "Backup directories accessible",
        }
    except Exception as e:
        results["checks"]["directories"] = {
            "status": "error",
            "message": str(e),
        }
        results["status"] = "unhealthy"

    # Check required tools
    required_tools = ["pg_dump", "psql", "gzip"]
    for tool in required_tools:
        try:
            subprocess_result = subprocess.run(
                ["which", tool],
                capture_output=True,
                text=True,
            )
            if subprocess_result.returncode == 0:
                results["checks"][tool] = {
                    "status": "ok",
                    "path": subprocess_result.stdout.strip(),
                }
            else:
                results["checks"][tool] = {
                    "status": "missing",
                }
                results["status"] = "unhealthy"
        except Exception as e:
            results["checks"][tool] = {
                "status": "error",
                "message": str(e),
            }

    # Check disk space
    try:
        import shutil
        disk_usage = shutil.disk_usage("./data/backups")
        free_gb = disk_usage.free / (1024**3)

        if free_gb < 1:  # Less than 1GB
            results["checks"]["disk_space"] = {
                "status": "warning",
                "message": f"Low disk space: {free_gb:.1f}GB free",
            }
            if results["status"] == "healthy":
                results["status"] = "warning"
        else:
            results["checks"]["disk_space"] = {
                "status": "ok",
                "message": f"{free_gb:.1f}GB free",
            }
    except Exception as e:
        results["checks"]["disk_space"] = {
            "status": "error",
            "message": str(e),
        }

    logger.info(f"Backup health check completed: {results['status']}")

    return results


# Import subprocess for health check
import subprocess


__all__ = [
    "daily_backup_task",
    "create_backup_task",
    "cleanup_old_backups_task",
    "upload_to_s3_task",
    "verify_backup_integrity_task",
    "restore_from_backup_task",
    "sync_all_to_s3_task",
    "backup_health_check_task",
]
