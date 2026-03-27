"""
Migration wizard API endpoints for ATS data migration.

This module provides REST endpoints for migrating data from other ATS platforms
(Greenhouse, Lever, Workable, Workday) to AgentHR. The wizard guides users through:

1. Connection validation to source ATS
2. Migration preview and data estimation
3. Field mapping configuration
4. Migration execution with progress tracking
5. Migration monitoring and management

Features:
- Multi-platform support (Greenhouse, Lever, Workable, Workday)
- Wizard-based guided migration flow
- Progress tracking and status monitoring
- Field mapping and transformation
- Validation and error reporting
- Partial migration support
"""
import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models.migration import Migration, MigrationStatus as DBMigrationStatus, MigrationType as DBMigrationType

# Import schemas
from schemas.migration import (
    MigrationCreate,
    MigrationUpdate,
    MigrationResponse,
    MigrationListResponse,
    MigrationStatsResponse,
    MigrationValidationError,
    MigrationStartRequest,
    MigrationCancelRequest,
    MigrationFieldMapping,
    MigrationMappingConfig,
    BulkMigrationRequest,
    MigrationPreviewRequest,
    MigrationPreviewResponse,
)

# Import migration service - handle both container and local environments
import sys

IN_CONTAINER = os.path.exists('/app/backend/services')
if IN_CONTAINER:
    if '/app/backend' not in sys.path:
        sys.path.insert(0, '/app/backend')
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

try:
    from services.migration_assistant import (
        MigrationAssistant,
        ATSPlatform,
        MigrationDataType,
    )
except (ImportError, ModuleNotFoundError):
    try:
        from backend.services.migration_assistant import (
            MigrationAssistant,
            ATSPlatform,
            MigrationDataType,
        )
    except (ImportError, ModuleNotFoundError):
        # Define stubs if service not available
        def MigrationAssistant(*args, **kwargs):
            raise NotImplementedError("migration_assistant not available")
        class ATSPlatform:
            GREENHOUSE = "greenhouse"
            LEVER = "lever"
            WORKABLE = "workable"
            WORKDAY = "workday"
        class MigrationDataType:
            CANDIDATES = "candidates"
            JOBS = "jobs"
            APPLICATIONS = "applications"

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


def migration_to_response(migration: Migration) -> dict:
    """Convert database Migration model to API response"""
    progress_percentage = None
    if migration.total_records and migration.total_records > 0:
        processed = migration.successful_migrations + migration.failed_migrations + migration.skipped_records
        progress_percentage = (processed / migration.total_records) * 100

    return {
        "id": str(migration.id),
        "status": migration.status.value,
        "migration_type": migration.migration_type.value,
        "recruiter_id": str(migration.recruiter_id),
        "source_system": migration.source_system,
        "target_system": migration.target_system,
        "source_system_version": migration.source_system_version,
        "total_records": migration.total_records,
        "successful_migrations": migration.successful_migrations,
        "failed_migrations": migration.failed_migrations,
        "skipped_records": migration.skipped_records,
        "error_message": migration.error_message,
        "migration_metadata": migration.migration_metadata,
        "validation_errors": migration.validation_errors,
        "entity_types": migration.entity_types,
        "notes": migration.notes,
        "started_at": migration.started_at,
        "completed_at": migration.completed_at,
        "created_at": migration.created_at.isoformat() if migration.created_at else None,
        "updated_at": migration.updated_at.isoformat() if migration.updated_at else None,
        "progress_percentage": progress_percentage,
    }


@router.post(
    "/validate",
    tags=["Migration Wizard"],
    status_code=status.HTTP_200_OK,
)
async def validate_migration_connection(
    source_system: str = Body(..., description="Source ATS platform (greenhouse, lever, workable, workday)"),
    api_token: Optional[str] = Body(None, description="API token for authentication"),
    username: Optional[str] = Body(None, description="Username (for Workday)"),
    password: Optional[str] = Body(None, description="Password (for Workday)"),
    tenant: Optional[str] = Body(None, description="Tenant ID (for Workday)"),
    organization_id: str = Body(..., description="Organization ID"),
    data_types: Optional[List[str]] = Body(None, description="Data types to validate"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Validate migration connection to source ATS platform.

    This is step 1 of the migration wizard. It tests the connection to the source
    ATS platform, validates credentials, and estimates the number of records
    available for migration.

    Args:
        source_system: Source ATS platform name
        api_token: API token for authentication (Greenhouse, Lever)
        username: Username for authentication (Workday)
        password: Password for authentication (Workday)
        tenant: Tenant ID (Workday)
        organization_id: Organization identifier
        data_types: Optional list of data types to validate
        db: Database session

    Returns:
        JSON response with validation results

    Raises:
        HTTPException(400): If source system is not supported
        HTTPException(401): If authentication fails
        HTTPException(500): If validation fails

    Examples:
        >>> import requests
        >>> response = requests.post('/api/migration/validate', json={
        ...     'source_system': 'greenhouse',
        ...     'api_token': 'your-api-token',
        ...     'organization_id': 'org-123'
        ... })
        >>> result = response.json()
        >>> print(result['is_valid'])
    """
    try:
        # Validate source system
        valid_platforms = [p.value for p in ATSPlatform]
        if source_system.lower() not in valid_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source system. Must be one of: {', '.join(valid_platforms)}",
            )

        # Prepare source config based on platform
        source_config = {}
        if source_system.lower() in ["greenhouse", "lever"]:
            if not api_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"api_token is required for {source_system}",
                )
            source_config["api_token"] = api_token
        elif source_system.lower() == "workday":
            if not all([username, password, tenant]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="username, password, and tenant are required for Workday",
                )
            source_config.update({
                "username": username,
                "password": password,
                "tenant": tenant,
            })

        # Parse data types
        parsed_data_types = None
        if data_types:
            parsed_data_types = [MigrationDataType(dt) for dt in data_types]

        # Create migration assistant and validate
        assistant = MigrationAssistant(
            db=db,
            organization_id=organization_id,
            source_platform=ATSPlatform(source_system.lower()),
            source_config=source_config,
        )

        validation_result = await assistant.validate_migration(
            data_types=parsed_data_types
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "is_valid": validation_result.is_valid,
                "connection_ok": validation_result.connection_ok,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "data_types_available": [
                    dt.value for dt in validation_result.data_types_available
                ],
                "estimated_record_count": validation_result.estimated_record_count,
                "details": validation_result.details,
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Migration validation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )


@router.post(
    "/preview",
    tags=["Migration Wizard"],
    status_code=status.HTTP_200_OK,
)
async def preview_migration_data(
    preview_request: MigrationPreviewRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Preview migration data from source ATS.

    This is step 2 of the migration wizard. It provides a sample of records
    that will be migrated, along with suggested field mappings and validation
    warnings.

    Args:
        preview_request: Preview request parameters
        db: Database session

    Returns:
        JSON response with preview data

    Examples:
        >>> import requests
        >>> response = requests.post('/api/migration/preview', json={
        ...     'source_system': 'greenhouse',
        ...     'entity_types': ['candidates', 'jobs'],
        ...     'sample_size': 5
        ... })
        >>> preview = response.json()
    """
    try:
        # This is a simplified preview - in production would fetch actual sample data
        # from the source ATS platform
        preview_response = {
            "source_system": preview_request.source_system,
            "entity_type": preview_request.entity_types[0] if preview_request.entity_types else "candidates",
            "total_records": 150,  # Placeholder - would fetch from source ATS
            "sample_records": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1-555-0123",
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane.smith@example.com",
                    "phone": "+1-555-0456",
                },
            ],
            "field_mapping_suggestions": [
                {
                    "source_field": "first_name",
                    "target_field": "first_name",
                    "required": True,
                },
                {
                    "source_field": "last_name",
                    "target_field": "last_name",
                    "required": True,
                },
                {
                    "source_field": "email",
                    "target_field": "email",
                    "required": True,
                },
            ],
            "validation_warnings": [
                "2 records have missing phone numbers",
                "5 records may be duplicates based on email",
            ],
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=preview_response,
        )

    except Exception as e:
        logger.error(f"Migration preview failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}",
        )


@router.post(
    "/",
    response_model=MigrationResponse,
    tags=["Migration"],
    status_code=status.HTTP_201_CREATED,
)
async def create_migration(
    migration_create: MigrationCreate,
    recruiter_id: str = Query(..., description="ID of recruiter initiating the migration"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new migration job.

    This is step 3 of the migration wizard. It creates a migration job record
    in the database. The migration will be in PENDING status until started.

    Args:
        migration_create: Migration creation parameters
        recruiter_id: ID of recruiter initiating the migration
        db: Database session

    Returns:
        JSON response with created migration details

    Raises:
        HTTPException(400): If migration parameters are invalid
        HTTPException(500): If migration creation fails

    Examples:
        >>> import requests
        >>> response = requests.post('/api/migration/', json={
        ...     'migration_type': 'full_migration',
        ...     'source_system': 'greenhouse',
        ...     'entity_types': ['candidates', 'jobs']
        ... }, params={'recruiter_id': '123e4567-e89b-12d3-a456-426614174000'})
        >>> migration = response.json()
    """
    try:
        # Validate migration type
        valid_types = [t.value for t in DBMigrationType]
        if migration_create.migration_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid migration type. Must be one of: {', '.join(valid_types)}",
            )

        # Create migration record
        migration = Migration(
            status=DBMigrationStatus.PENDING,
            migration_type=DBMigrationType(migration_create.migration_type),
            recruiter_id=UUID(recruiter_id),
            source_system=migration_create.source_system,
            target_system=migration_create.target_system,
            source_system_version=migration_create.source_system_version,
            entity_types=migration_create.entity_types,
            notes=migration_create.notes,
            migration_metadata=migration_create.migration_metadata or {},
        )

        db.add(migration)
        await db.commit()
        await db.refresh(migration)

        logger.info(
            f"Created migration {migration.id} from {migration.source_system} "
            f"by recruiter {recruiter_id}"
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=migration_to_response(migration),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to create migration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration creation failed: {str(e)}",
        )


@router.get(
    "/",
    response_model=List[MigrationResponse],
    tags=["Migration"],
)
async def list_migrations(
    source_system: Optional[str] = Query(None, description="Filter by source system"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    migration_type: Optional[str] = Query(None, description="Filter by migration type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all migrations with optional filtering.

    Returns a paginated list of migrations sorted by creation time (newest first).

    Args:
        source_system: Optional filter by source system
        status_filter: Optional filter by status
        migration_type: Optional filter by migration type
        limit: Maximum number of results
        offset: Pagination offset
        db: Database session

    Returns:
        JSON response with list of migrations

    Examples:
        >>> import requests
        >>> response = requests.get('/api/migration/?source_system=greenhouse&limit=10')
        >>> migrations = response.json()
    """
    try:
        query = select(Migration).order_by(Migration.created_at.desc())

        if source_system:
            query = query.filter(Migration.source_system == source_system)

        if status_filter:
            try:
                status_enum = DBMigrationStatus(status_filter)
                query = query.filter(Migration.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}",
                )

        if migration_type:
            try:
                type_enum = DBMigrationType(migration_type)
                query = query.filter(Migration.migration_type == type_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid migration type: {migration_type}",
                )

        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        migrations = result.scalars().all()

        response_data = [migration_to_response(m) for m in migrations]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list migrations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list migrations: {str(e)}",
        )


@router.get(
    "/{migration_id}",
    response_model=MigrationResponse,
    tags=["Migration"],
)
async def get_migration(
    migration_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get details of a specific migration.

    Args:
        migration_id: UUID of the migration
        db: Database session

    Returns:
        JSON response with migration details

    Raises:
        HTTPException(400): If migration_id is not a valid UUID
        HTTPException(404): If migration not found

    Examples:
        >>> import requests
        >>> response = requests.get('/api/migration/123e4567-e89b-12d3-a456-426614174000')
        >>> migration = response.json()
    """
    try:
        # Validate UUID
        try:
            migration_uuid = UUID(migration_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid migration ID format: {migration_id}",
            )

        # Fetch migration
        result = await db.execute(
            select(Migration).filter(Migration.id == migration_uuid)
        )
        migration = result.scalar_one_or_none()

        if not migration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration not found: {migration_id}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=migration_to_response(migration),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get migration {migration_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get migration: {str(e)}",
        )


@router.patch(
    "/{migration_id}",
    response_model=MigrationResponse,
    tags=["Migration"],
)
async def update_migration(
    migration_id: str,
    migration_update: MigrationUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a migration's details.

    Args:
        migration_id: UUID of the migration
        migration_update: Update parameters
        db: Database session

    Returns:
        JSON response with updated migration details

    Raises:
        HTTPException(400): If migration_id is invalid or update parameters are invalid
        HTTPException(404): If migration not found
    """
    try:
        # Validate UUID
        try:
            migration_uuid = UUID(migration_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid migration ID format: {migration_id}",
            )

        # Fetch migration
        result = await db.execute(
            select(Migration).filter(Migration.id == migration_uuid)
        )
        migration = result.scalar_one_or_none()

        if not migration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration not found: {migration_id}",
            )

        # Update fields
        update_data = migration_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "status" and value:
                setattr(migration, field, DBMigrationStatus(value))
            else:
                setattr(migration, field, value)

        await db.commit()
        await db.refresh(migration)

        logger.info(f"Updated migration {migration_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=migration_to_response(migration),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to update migration {migration_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update migration: {str(e)}",
        )


@router.delete(
    "/{migration_id}",
    tags=["Migration"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_migration(
    migration_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a migration.

    Args:
        migration_id: UUID of the migration
        db: Database session

    Raises:
        HTTPException(400): If migration_id is not a valid UUID
        HTTPException(404): If migration not found
        HTTPException(409): If migration is in progress
    """
    try:
        # Validate UUID
        try:
            migration_uuid = UUID(migration_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid migration ID format: {migration_id}",
            )

        # Fetch migration
        result = await db.execute(
            select(Migration).filter(Migration.id == migration_uuid)
        )
        migration = result.scalar_one_or_none()

        if not migration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration not found: {migration_id}",
            )

        # Check if migration is in progress
        if migration.status == DBMigrationStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete migration in progress. Cancel it first.",
            )

        # Delete migration
        await db.execute(
            delete(Migration).filter(Migration.id == migration_uuid)
        )
        await db.commit()

        logger.info(f"Deleted migration {migration_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete migration {migration_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete migration: {str(e)}",
        )


@router.post(
    "/{migration_id}/start",
    response_model=MigrationResponse,
    tags=["Migration"],
)
async def start_migration(
    migration_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Start a pending migration.

    This is step 4 of the migration wizard. It triggers the actual migration
    execution. In production, this would dispatch a Celery task for background
    processing.

    Args:
        migration_id: UUID of the migration to start
        db: Database session

    Returns:
        JSON response with updated migration details

    Raises:
        HTTPException(400): If migration_id is invalid
        HTTPException(404): If migration not found
        HTTPException(409): If migration is not in pending status
    """
    try:
        # Validate UUID
        try:
            migration_uuid = UUID(migration_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid migration ID format: {migration_id}",
            )

        # Fetch migration
        result = await db.execute(
            select(Migration).filter(Migration.id == migration_uuid)
        )
        migration = result.scalar_one_or_none()

        if not migration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration not found: {migration_id}",
            )

        # Check if migration is pending
        if migration.status != DBMigrationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Migration is not in pending status. Current status: {migration.status.value}",
            )

        # Update status to in_progress
        migration.status = DBMigrationStatus.IN_PROGRESS
        migration.started_at = datetime.utcnow().isoformat()

        await db.commit()
        await db.refresh(migration)

        # In production, this would dispatch a Celery task:
        # from tasks.migration_tasks import migrate_from_ats_task
        # migrate_from_ats_task.delay(str(migration.id))

        logger.info(f"Started migration {migration_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=migration_to_response(migration),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start migration {migration_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start migration: {str(e)}",
        )


@router.post(
    "/{migration_id}/cancel",
    response_model=MigrationResponse,
    tags=["Migration"],
)
async def cancel_migration(
    migration_id: str,
    cancel_request: Optional[MigrationCancelRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Cancel an in-progress migration.

    Args:
        migration_id: UUID of the migration to cancel
        cancel_request: Optional cancellation parameters
        db: Database session

    Returns:
        JSON response with updated migration details

    Raises:
        HTTPException(400): If migration_id is invalid
        HTTPException(404): If migration not found
        HTTPException(409): If migration cannot be cancelled
    """
    try:
        # Validate UUID
        try:
            migration_uuid = UUID(migration_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid migration ID format: {migration_id}",
            )

        # Fetch migration
        result = await db.execute(
            select(Migration).filter(Migration.id == migration_uuid)
        )
        migration = result.scalar_one_or_none()

        if not migration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration not found: {migration_id}",
            )

        # Check if migration can be cancelled
        if migration.status not in [DBMigrationStatus.PENDING, DBMigrationStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Migration cannot be cancelled. Current status: {migration.status.value}",
            )

        # Update status to cancelled
        migration.status = DBMigrationStatus.CANCELLED
        migration.completed_at = datetime.utcnow().isoformat()

        if cancel_request and cancel_request.reason:
            if not migration.notes:
                migration.notes = f"Cancelled: {cancel_request.reason}"
            else:
                migration.notes += f"\nCancelled: {cancel_request.reason}"

        await db.commit()
        await db.refresh(migration)

        logger.info(f"Cancelled migration {migration_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=migration_to_response(migration),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel migration {migration_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel migration: {str(e)}",
        )


@router.get(
    "/stats/summary",
    response_model=MigrationStatsResponse,
    tags=["Migration Statistics"],
)
async def get_migration_stats(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get migration statistics and summary.

    Returns aggregate statistics for all migrations including counts by status,
    type, source system, and recent migration activity.

    Args:
        db: Database session

    Returns:
        JSON response with migration statistics

    Examples:
        >>> import requests
        >>> response = requests.get('/api/migration/stats/summary')
        >>> stats = response.json()
        >>> print(stats['total_migrations'])
    """
    try:
        # Get total count
        total_result = await db.execute(select(func.count(Migration.id)))
        total_migrations = total_result.scalar() or 0

        # Get counts by status
        status_result = await db.execute(
            select(Migration.status, func.count(Migration.id))
            .group_by(Migration.status)
        )
        by_status = {status.value: count for status, count in status_result}

        # Get counts by type
        type_result = await db.execute(
            select(Migration.migration_type, func.count(Migration.id))
            .group_by(Migration.migration_type)
        )
        by_type = {mtype.value: count for mtype, count in type_result}

        # Get counts by source system
        system_result = await db.execute(
            select(Migration.source_system, func.count(Migration.id))
            .group_by(Migration.source_system)
        )
        by_source_system = {system: count for system, count in system_result}

        # Get aggregate counts
        totals_result = await db.execute(
            select(
                func.sum(Migration.successful_migrations),
                func.sum(Migration.failed_migrations),
                func.sum(Migration.skipped_records),
            )
        )
        totals = totals_result.one()
        total_records_migrated = int(totals[0] or 0)
        total_records_failed = int(totals[1] or 0)
        total_records_skipped = int(totals[2] or 0)

        # Calculate success rate
        total_processed = total_records_migrated + total_records_failed
        success_rate = (total_records_migrated / total_processed * 100) if total_processed > 0 else None

        # Get recent migrations
        recent_result = await db.execute(
            select(Migration)
            .order_by(Migration.created_at.desc())
            .limit(5)
        )
        recent_migrations = [
            migration_to_response(m) for m in recent_result.scalars().all()
        ]

        stats = {
            "total_migrations": total_migrations,
            "by_status": by_status,
            "by_type": by_type,
            "by_source_system": by_source_system,
            "total_records_migrated": total_records_migrated,
            "total_records_failed": total_records_failed,
            "total_records_skipped": total_records_skipped,
            "recent_migrations": recent_migrations,
            "success_rate": success_rate,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=stats,
        )

    except Exception as e:
        logger.error(f"Failed to get migration stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get migration stats: {str(e)}",
        )


@router.get(
    "/field-mappings/{source_system}/{entity_type}",
    tags=["Migration Wizard"],
)
async def get_field_mappings(
    source_system: str,
    entity_type: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get field mapping configuration for a source system and entity type.

    This helps with step 2.5 of the migration wizard - configuring field mappings
    between the source ATS and AgentHR.

    Args:
        source_system: Source ATS platform (greenhouse, lever, workable, workday)
        entity_type: Entity type (candidates, jobs, applications)
        db: Database session

    Returns:
        JSON response with field mapping suggestions

    Examples:
        >>> import requests
        >>> response = requests.get('/api/migration/field-mappings/greenhouse/candidates')
        >>> mappings = response.json()
    """
    try:
        # Validate source system
        valid_platforms = [p.value for p in ATSPlatform]
        if source_system.lower() not in valid_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source system. Must be one of: {', '.join(valid_platforms)}",
            )

        # Validate entity type
        valid_entity_types = [dt.value for dt in MigrationDataType]
        if entity_type.lower() not in valid_entity_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid entity type. Must be one of: {', '.join(valid_entity_types)}",
            )

        # Return default field mappings
        # In production, this would use MigrationAssistant.get_field_mapping()
        mappings = {
            "source_system": source_system,
            "entity_type": entity_type,
            "field_mappings": [
                {
                    "source_field": "first_name",
                    "target_field": "first_name",
                    "transform": None,
                    "required": True,
                    "default_value": None,
                },
                {
                    "source_field": "last_name",
                    "target_field": "last_name",
                    "transform": None,
                    "required": True,
                    "default_value": None,
                },
                {
                    "source_field": "email",
                    "target_field": "email",
                    "transform": None,
                    "required": True,
                    "default_value": None,
                },
                {
                    "source_field": "phone",
                    "target_field": "phone",
                    "transform": None,
                    "required": False,
                    "default_value": None,
                },
            ],
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=mappings,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get field mappings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get field mappings: {str(e)}",
        )
