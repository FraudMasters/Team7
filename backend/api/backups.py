"""
Backup and restore API endpoints

This module provides REST endpoints for managing backups including:
- Listing backups with filtering
- Creating new backups
- Restoring from backups
- Managing backup configuration
- Verifying backup integrity
- Syncing with S3 storage
"""
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models.backup import Backup, BackupConfig, BackupType, BackupStatus
from schemas.backup import (
    BackupResponse,
    BackupCreate,
    BackupRestoreRequest,
    BackupConfigResponse,
    BackupConfigUpdate,
    BackupStatusResponse,
    BackupVerifyResponse,
    S3Config,
)
from services.backup_service import (
    get_backup_service,
    format_size,
)
from tasks.backup_tasks import (
    create_backup_task,
    restore_from_backup_task,
    upload_to_s3_task,
    sync_all_to_s3_task,
    verify_backup_integrity_task,
    cleanup_old_backups_task,
    backup_health_check_task,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


# Database dependency helpers
async def get_backup_config(db: AsyncSession) -> Optional[BackupConfig]:
    """Get or create backup configuration"""
    result = await db.execute(select(BackupConfig).limit(1))
    config = result.scalar_one_or_none()

    if config is None:
        # Create default config
        config = BackupConfig(
            retention_days=30,
            backup_schedule="0 2 * * *",
            s3_enabled=False,
            enabled=True,
            incremental_enabled=True,
            compression_enabled=True,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return config


def backup_to_response(backup: Backup) -> dict:
    """Convert database Backup model to API response"""
    return {
        "id": str(backup.id),
        "name": backup.name,
        "type": backup.type.value,
        "status": backup.status.value,
        "size_bytes": backup.size_bytes,
        "size_human": format_size(backup.size_bytes) if backup.size_bytes else None,
        "backup_path": backup.backup_path,
        "created_at": backup.created_at.isoformat() if backup.created_at else None,
        "completed_at": backup.completed_at,
        "retention_days": backup.retention_days,
        "expires_at": (
            (backup.created_at + timedelta(days=backup.retention_days)).isoformat()
            if backup.created_at
            else None
        ),
        "checksum": backup.checksum,
        "is_incremental": backup.is_incremental,
        "parent_backup_id": backup.parent_backup_id,
        "s3_uploaded": backup.s3_uploaded,
        "s3_key": backup.s3_key,
        "error_message": backup.error_message,
        "files_count": backup.files_count,
        "tables_count": backup.tables_count,
    }


@router.get(
    "/",
    response_model=List[BackupResponse],
    tags=["Backups"],
)
async def list_backups(
    backup_type: Optional[str] = Query(None, description="Filter by backup type"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all backups with optional filtering.

    Returns a paginated list of backups sorted by creation time (newest first).

    Args:
        backup_type: Optional filter by type (database, files, models, full)
        status_filter: Optional filter by status
        limit: Maximum number of results
        offset: Pagination offset
        db: Database session

    Returns:
        JSON response with list of backups

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/backups/?backup_type=full&limit=10")
        >>> backups = response.json()
    """
    try:
        query = select(Backup).order_by(Backup.created_at.desc())

        if backup_type:
            try:
                backup_type_enum = BackupType(backup_type)
                query = query.filter(Backup.type == backup_type_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid backup type: {backup_type}",
                )

        if status_filter:
            try:
                status_enum = BackupStatus(status_filter)
                query = query.filter(Backup.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}",
                )

        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        backups = result.scalars().all()

        response_data = [backup_to_response(b) for b in backups]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing backups: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}",
        ) from e


@router.post(
    "/",
    response_model=BackupResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Backups"],
)
async def create_backup(
    request: BackupCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new backup.

    Starts an asynchronous backup task and returns immediately.
    The backup will be processed in the background by Celery.

    Args:
        request: Backup creation request
        db: Database session

    Returns:
        JSON response with created backup entry

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Manual backup",
        ...     "type": "full",
        ...     "retention_days": 30,
        ...     "upload_to_s3": true
        ... }
        >>> response = requests.post("http://localhost:8000/api/backups/", json=data)
        >>> backup = response.json()
    """
    try:
        logger.info(f"Creating backup: {request.name}")

        # Validate backup type
        valid_types = ["database", "files", "models", "full"]
        if request.type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid backup type. Must be one of: {', '.join(valid_types)}",
            )

        # Create backup record
        backup = Backup(
            name=request.name,
            type=BackupType(request.type),
            status=BackupStatus.PENDING,
            retention_days=request.retention_days,
            is_incremental=request.is_incremental,
            backup_path="pending",
        )

        db.add(backup)
        await db.commit()
        await db.refresh(backup)

        # Start async backup task
        task = create_backup_task.delay(
            backup_type=request.type,
            name=request.name,
            is_incremental=request.is_incremental,
            upload_to_s3=request.upload_to_s3,
        )

        logger.info(f"Backup task started: {task.id}")

        # Return backup with pending status
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=backup_to_response(backup),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}",
        ) from e


@router.get(
    "/status",
    response_model=BackupStatusResponse,
    tags=["Backups"],
)
async def get_backup_status(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get overall backup system status.

    Returns information about the backup system including:
    - Last successful backup time
    - Total number of backups
    - Total disk usage
    - Recent backups list

    Args:
        db: Database session

    Returns:
        JSON response with backup status

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/backups/status")
        >>> status = response.json()
    """
    try:
        # Get backup configuration
        config = await get_backup_config(db)

        # Get all completed backups
        result = await db.execute(
            select(Backup)
            .where(Backup.status == BackupStatus.COMPLETED)
            .order_by(Backup.created_at.desc())
        )
        completed_backups = result.scalars().all()

        # Calculate total size
        total_size = sum(b.size_bytes or 0 for b in completed_backups)

        # Get recent backups (last 5)
        recent = completed_backups[:5]

        # Get backup service for disk usage
        backup_service = get_backup_service()
        disk_usage = backup_service.get_disk_usage()

        response_data = {
            "enabled": config.enabled,
            "last_backup_at": (
                config.last_backup_at if config.last_backup_at
                else (recent[0].created_at.isoformat() if recent else None)
            ),
            "last_backup_status": config.last_backup_status,
            "total_backups": len(completed_backups),
            "total_size_bytes": total_size,
            "total_size_human": format_size(total_size),
            "next_scheduled_backup": _get_next_scheduled_backup_time(),
            "recent_backups": [backup_to_response(b) for b in recent],
            "disk_usage_bytes": disk_usage["total_bytes"],
            "disk_usage_human": disk_usage["total_human"],
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error getting backup status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup status: {str(e)}",
        ) from e


@router.get(
    "/config",
    response_model=BackupConfigResponse,
    tags=["Backups"],
)
async def get_backup_config_endpoint(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get backup configuration.

    Returns the current backup system configuration including
    retention policy, S3 settings, and schedule.

    Args:
        db: Database session

    Returns:
        JSON response with backup configuration

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/backups/config")
        >>> config = response.json()
    """
    try:
        config = await get_backup_config(db)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "retention_days": config.retention_days,
                "backup_schedule": config.backup_schedule,
                "s3_enabled": config.s3_enabled,
                "s3_bucket": config.s3_bucket,
                "s3_endpoint": config.s3_endpoint,
                "s3_region": config.s3_region,
                "notification_email": config.notification_email,
                "enabled": config.enabled,
                "incremental_enabled": config.incremental_enabled,
                "compression_enabled": config.compression_enabled,
                "last_backup_at": config.last_backup_at,
                "last_backup_status": config.last_backup_status,
            },
        )

    except Exception as e:
        logger.error(f"Error getting backup config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup config: {str(e)}",
        ) from e


@router.put(
    "/config",
    response_model=BackupConfigResponse,
    tags=["Backups"],
)
async def update_backup_config(
    request: BackupConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update backup configuration.

    Updates the backup system configuration. Only fields that are
    provided will be updated; others remain unchanged.

    Args:
        request: Configuration update request
        db: Database session

    Returns:
        JSON response with updated configuration

    Examples:
        >>> import requests
        >>> data = {
        ...     "retention_days": 60,
        ...     "s3_enabled": true,
        ...     "s3_bucket": "my-backup-bucket"
        ... }
        >>> response = requests.put("http://localhost:8000/api/backups/config", json=data)
        >>> config = response.json()
    """
    try:
        config = await get_backup_config(db)

        # Update fields that are provided
        update_data = {}
        if request.retention_days is not None:
            update_data["retention_days"] = request.retention_days
        if request.backup_schedule is not None:
            update_data["backup_schedule"] = request.backup_schedule
        if request.s3_enabled is not None:
            update_data["s3_enabled"] = request.s3_enabled
        if request.s3_bucket is not None:
            update_data["s3_bucket"] = request.s3_bucket
        if request.s3_endpoint is not None:
            update_data["s3_endpoint"] = request.s3_endpoint
        if request.s3_access_key is not None:
            update_data["s3_access_key"] = request.s3_access_key
        if request.s3_secret_key is not None:
            update_data["s3_secret_key"] = request.s3_secret_key
        if request.s3_region is not None:
            update_data["s3_region"] = request.s3_region
        if request.notification_email is not None:
            update_data["notification_email"] = request.notification_email
        if request.enabled is not None:
            update_data["enabled"] = request.enabled
        if request.incremental_enabled is not None:
            update_data["incremental_enabled"] = request.incremental_enabled
        if request.compression_enabled is not None:
            update_data["compression_enabled"] = request.compression_enabled

        if update_data:
            await db.execute(
                update(BackupConfig)
                .where(BackupConfig.id == config.id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(config)

        logger.info(f"Updated backup config: {list(update_data.keys())}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "retention_days": config.retention_days,
                "backup_schedule": config.backup_schedule,
                "s3_enabled": config.s3_enabled,
                "s3_bucket": config.s3_bucket,
                "s3_endpoint": config.s3_endpoint,
                "s3_region": config.s3_region,
                "notification_email": config.notification_email,
                "enabled": config.enabled,
                "incremental_enabled": config.incremental_enabled,
                "compression_enabled": config.compression_enabled,
                "last_backup_at": config.last_backup_at,
                "last_backup_status": config.last_backup_status,
            },
        )

    except Exception as e:
        logger.error(f"Error updating backup config: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update backup config: {str(e)}",
        ) from e


@router.get(
    "/{backup_id}",
    response_model=BackupResponse,
    tags=["Backups"],
)
async def get_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get details of a specific backup.

    Args:
        backup_id: UUID of the backup
        db: Database session

    Returns:
        JSON response with backup details

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/backups/123e4567-e89b-12d3-a456-426614174000")
        >>> backup = response.json()
    """
    try:
        result = await db.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()

        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup not found: {backup_id}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=backup_to_response(backup),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting backup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup: {str(e)}",
        ) from e


@router.post(
    "/{backup_id}/restore",
    tags=["Backups"],
)
async def restore_backup(
    backup_id: str,
    request: BackupRestoreRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Restore from a backup.

    Initiates an asynchronous restore operation. The restore will be
    processed in the background by Celery.

    WARNING: This will replace current data with the backup data.

    Args:
        backup_id: UUID of the backup to restore from
        request: Restore request with options
        db: Database session

    Returns:
        JSON response confirming restore initiation

    Examples:
        >>> import requests
        >>> data = {
        ...     "confirm": true,
        ...     "create_backup_before": true,
        ...     "restore_type": "full"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/backups/123/restore",
        ...     json=data
        ... )
        >>> result = response.json()
    """
    try:
        # Verify backup exists
        result = await db.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()

        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup not found: {backup_id}",
            )

        if backup.status != BackupStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot restore from backup with status: {backup.status.value}",
            )

        if not request.confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="confirm must be True to proceed with restore",
            )

        logger.info(f"Starting restore from backup: {backup_id}")

        # Update backup status
        backup.status = BackupStatus.RESTORING
        await db.commit()

        # Start async restore task
        restore_type = request.restore_type or "full"
        task = restore_from_backup_task.delay(
            backup_path=backup.backup_path,
            backup_type=restore_type,
            create_backup_before=request.create_backup_before,
        )

        logger.info(f"Restore task started: {task.id}")

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "message": "Restore operation started",
                "backup_id": backup_id,
                "task_id": task.id,
                "restore_type": restore_type,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting restore: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start restore: {str(e)}",
        ) from e


@router.delete(
    "/{backup_id}",
    tags=["Backups"],
)
async def delete_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a backup.

    Permanently deletes a backup file and its database record.

    Args:
        backup_id: UUID of the backup to delete
        db: Database session

    Returns:
        JSON response confirming deletion

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/backups/123e4567-e89b-12d3-a456-426614174000")
        >>> result = response.json()
    """
    try:
        result = await db.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()

        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup not found: {backup_id}",
            )

        # Delete file from disk
        backup_service = get_backup_service()
        if backup.backup_path and backup.backup_path != "pending":
            backup_service.delete_backup(backup.backup_path)

        # Delete database record
        await db.execute(delete(Backup).where(Backup.id == backup_id))
        await db.commit()

        logger.info(f"Deleted backup: {backup_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Backup {backup_id} deleted successfully"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backup: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backup: {str(e)}",
        ) from e


@router.post(
    "/{backup_id}/verify",
    response_model=BackupVerifyResponse,
    tags=["Backups"],
)
async def verify_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Verify backup integrity.

    Calculates and verifies the checksum of a backup file.

    Args:
        backup_id: UUID of the backup to verify
        db: Database session

    Returns:
        JSON response with verification results

    Examples:
        >>> import requests
        >>> response = requests.post("http://localhost:8000/api/backups/123/verify")
        >>> result = response.json()
        >>> print(result['valid'])
        True
    """
    try:
        result = await db.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()

        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup not found: {backup_id}",
            )

        if not backup.backup_path or backup.backup_path == "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Backup file not available",
            )

        backup_service = get_backup_service()
        verification = backup_service.verify_backup_integrity(
            backup_path=backup.backup_path,
            expected_checksum=backup.checksum,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "backup_id": backup_id,
                "valid": verification.get("valid", False),
                "checksum_match": verification.get("checksum_match", False),
                "files_intact": verification.get("valid", False),
                "details": verification.get("error") or "Backup integrity verified",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying backup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify backup: {str(e)}",
        ) from e


@router.post(
    "/sync-s3",
    tags=["Backups"],
)
async def sync_s3(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Manually trigger S3 sync for all backups.

    Uploads all local backups that haven't been uploaded to S3 yet.

    Args:
        db: Database session

    Returns:
        JSON response with sync results

    Examples:
        >>> import requests
        >>> response = requests.post("http://localhost:8000/api/backups/sync-s3")
        >>> result = response.json()
    """
    try:
        # Check if S3 is enabled
        config = await get_backup_config(db)

        if not config.s3_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="S3 backup is not enabled",
            )

        # Start sync task
        task = sync_all_to_s3_task.delay()

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "message": "S3 sync task started",
                "task_id": task.id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting S3 sync: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start S3 sync: {str(e)}",
        ) from e


@router.post(
    "/cleanup",
    tags=["Backups"],
)
async def cleanup_backups(
    retention_days: Optional[int] = Query(
        None,
        ge=1,
        le=365,
        description="Retention period in days (uses config default if not specified)"
    ),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Manually trigger cleanup of old backups.

    Deletes backups that exceed the retention period.

    Args:
        retention_days: Days to retain (uses config default if not specified)
        db: Database session

    Returns:
        JSON response with cleanup results

    Examples:
        >>> import requests
        >>> response = requests.post("http://localhost:8000/api/backups/cleanup?retention_days=30")
        >>> result = response.json()
    """
    try:
        # Get retention days from config if not specified
        if retention_days is None:
            config = await get_backup_config(db)
            retention_days = config.retention_days

        # Start cleanup task
        task = cleanup_old_backups_task.delay(retention_days=retention_days)

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "message": f"Cleanup task started for backups older than {retention_days} days",
                "task_id": task.id,
                "retention_days": retention_days,
            },
        )

    except Exception as e:
        logger.error(f"Error starting cleanup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start cleanup: {str(e)}",
        ) from e


def _get_next_scheduled_backup_time() -> Optional[str]:
    """
    Calculate the next scheduled backup time based on configuration.

    Returns:
        ISO format string of next scheduled time or None
    """
    try:
        # Default to daily at 2 AM UTC
        now = datetime.utcnow()
        next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)

        # If 2 AM has passed today, schedule for tomorrow
        if next_run <= now:
            from datetime import timedelta
            next_run += timedelta(days=1)

        return next_run.isoformat()
    except Exception:
        return None


__all__ = ["router"]
