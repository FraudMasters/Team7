"""
Job board integrations API endpoints.

This module provides endpoints for managing job board integrations,
including CRUD operations for integration configurations.
"""
import logging
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.job_board_integration import JobBoardIntegration
from models.import_log import ImportLog, ImportJobStatus
from tasks.import_tasks import poll_job_board

logger = logging.getLogger(__name__)

router = APIRouter()


def _extract_locale(request: Optional[Request]) -> str:
    """
    Extract Accept-Language header from request.

    Args:
        request: The incoming FastAPI request (optional)

    Returns:
        Language code (e.g., 'en', 'ru')
    """
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


# Pydantic models for requests/responses
class JobBoardIntegrationCreate(BaseModel):
    """Request model for creating a job board integration."""

    name: str = Field(..., description="Job board name (e.g., LinkedIn, Indeed)", min_length=1, max_length=100)
    api_endpoint: str = Field(..., description="API endpoint URL for the job board", min_length=1, max_length=500)
    api_key: str = Field(..., description="API key for authentication", min_length=1, max_length=255)
    enabled: bool = Field(True, description="Whether the integration is active")
    config: Optional[dict] = Field(None, description="Additional configuration as JSON")


class JobBoardIntegrationUpdate(BaseModel):
    """Request model for updating a job board integration."""

    name: Optional[str] = Field(None, description="Job board name", min_length=1, max_length=100)
    api_endpoint: Optional[str] = Field(None, description="API endpoint URL", min_length=1, max_length=500)
    api_key: Optional[str] = Field(None, description="API key for authentication", min_length=1, max_length=255)
    enabled: Optional[bool] = Field(None, description="Whether the integration is active")
    config: Optional[dict] = Field(None, description="Additional configuration as JSON")


class JobBoardIntegrationResponse(BaseModel):
    """Response model for job board integration."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Job board name")
    api_endpoint: str = Field(..., description="API endpoint URL")
    api_key: str = Field(..., description="API key (masked)")
    enabled: bool = Field(..., description="Whether the integration is active")
    config: Optional[dict] = Field(None, description="Additional configuration")
    last_sync_at: Optional[str] = Field(None, description="Last successful sync timestamp")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ImportLogResponse(BaseModel):
    """Response model for import log entry."""

    id: str = Field(..., description="Unique identifier")
    job_board_id: Optional[str] = Field(None, description="Job board integration ID")
    job_board_name: Optional[str] = Field(None, description="Job board name")
    status: str = Field(..., description="Import status")
    records_processed: Optional[int] = Field(None, description="Total records processed")
    records_succeeded: Optional[int] = Field(None, description="Successfully imported records")
    records_failed: Optional[int] = Field(None, description="Failed records")
    error_message: Optional[str] = Field(None, description="Error summary if failed")
    error_details: Optional[dict] = Field(None, description="Detailed error information")
    import_metadata: Optional[dict] = Field(None, description="Additional import metadata")
    started_at: Optional[str] = Field(None, description="Import start timestamp")
    completed_at: Optional[str] = Field(None, description="Import completion timestamp")
    retry_count: Optional[int] = Field(None, description="Number of retry attempts")
    created_at: str = Field(..., description="Log creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


def mask_api_key(api_key: str) -> str:
    """
    Mask API key for security in responses.

    Args:
        api_key: The original API key

    Returns:
        Masked API key (e.g., "sk_***1234")
    """
    if not api_key or len(api_key) < 8:
        return "***"
    # Show first 4 characters and last 4 characters, mask the rest
    if len(api_key) <= 12:
        return api_key[:3] + "***" + api_key[-3:]
    return api_key[:4] + "***" + api_key[-4:]


@router.post(
    "/",
    response_model=JobBoardIntegrationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Job Integrations"],
)
async def create_integration(
    request: Request,
    integration_data: JobBoardIntegrationCreate,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Create a new job board integration.

    This endpoint creates a new job board integration configuration
    with the provided API credentials and settings.

    Args:
        request: FastAPI request object (for Accept-Language header)
        integration_data: Integration configuration data
        db: Database session

    Returns:
        JSON response with created integration details

    Raises:
        HTTPException(400): If integration with same name exists
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/integrations",
        ...     json={
        ...         "name": "LinkedIn",
        ...         "api_endpoint": "https://api.linkedin.com/v2",
        ...         "api_key": "sk_1234567890",
        ...         "enabled": True
        ...     }
        ... )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "LinkedIn",
            "api_endpoint": "https://api.linkedin.com/v2",
            "api_key": "sk_1***7890",
            "enabled": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    """
    locale = _extract_locale(request)

    try:
        # Check if integration with same name already exists
        existing_query = select(JobBoardIntegration).where(
            JobBoardIntegration.name == integration_data.name
        )
        existing_result = await db.execute(existing_query)
        existing_integration = existing_result.scalar_one_or_none()

        if existing_integration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Integration with name '{integration_data.name}' already exists",
            )

        # Create new integration
        integration = JobBoardIntegration(
            id=uuid4(),
            name=integration_data.name,
            api_endpoint=integration_data.api_endpoint,
            api_key=integration_data.api_key,
            enabled=integration_data.enabled,
            config=integration_data.config or {},
        )

        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        logger.info(f"Created job board integration: {integration.id} - {integration.name}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(integration.id),
                "name": integration.name,
                "api_endpoint": integration.api_endpoint,
                "api_key": mask_api_key(integration.api_key),
                "enabled": integration.enabled,
                "config": integration.config,
                "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                "created_at": integration.created_at.isoformat() if integration.created_at else None,
                "updated_at": integration.updated_at.isoformat() if integration.updated_at else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job board integration: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create integration: {str(e)}",
        ) from e


@router.get(
    "/",
    tags=["Job Integrations"],
)
async def list_integrations(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List all job board integrations.

    Returns a paginated list of all configured job board integrations.

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of integrations

    Example:
        >>> response = requests.get("http://localhost:8000/api/integrations?limit=10")
        >>> integrations = response.json()
    """
    try:
        query = select(JobBoardIntegration).order_by(
            JobBoardIntegration.created_at.desc()
        ).offset(skip).limit(limit)

        result = await db.execute(query)
        integrations = result.scalars().all()

        integrations_list = []
        for integration in integrations:
            integrations_list.append({
                "id": str(integration.id),
                "name": integration.name,
                "api_endpoint": integration.api_endpoint,
                "api_key": mask_api_key(integration.api_key),
                "enabled": integration.enabled,
                "config": integration.config,
                "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                "created_at": integration.created_at.isoformat() if integration.created_at else None,
                "updated_at": integration.updated_at.isoformat() if integration.updated_at else None,
            })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"integrations": integrations_list, "total": len(integrations_list)},
        )

    except Exception as e:
        logger.error(f"Error listing integrations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list integrations: {str(e)}",
        ) from e


@router.get(
    "/{integration_id}",
    response_model=JobBoardIntegrationResponse,
    tags=["Job Integrations"],
)
async def get_integration(
    request: Request,
    integration_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get a job board integration by ID.

    Args:
        request: FastAPI request object
        integration_id: UUID of the integration
        db: Database session

    Returns:
        JSON response with integration details

    Raises:
        HTTPException(404): If integration not found
        HTTPException(422): If invalid UUID format
    """
    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid integration ID format",
        )

    query = select(JobBoardIntegration).where(JobBoardIntegration.id == integration_uuid)
    result = await db.execute(query)
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "id": str(integration.id),
            "name": integration.name,
            "api_endpoint": integration.api_endpoint,
            "api_key": mask_api_key(integration.api_key),
            "enabled": integration.enabled,
            "config": integration.config,
            "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None,
            "created_at": integration.created_at.isoformat() if integration.created_at else None,
            "updated_at": integration.updated_at.isoformat() if integration.updated_at else None,
        },
    )


@router.put(
    "/{integration_id}",
    response_model=JobBoardIntegrationResponse,
    tags=["Job Integrations"],
)
async def update_integration(
    request: Request,
    integration_id: str,
    integration_data: JobBoardIntegrationUpdate,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Update a job board integration.

    Args:
        request: FastAPI request object
        integration_id: UUID of the integration
        integration_data: Updated integration data
        db: Database session

    Returns:
        JSON response with updated integration details

    Raises:
        HTTPException(404): If integration not found
        HTTPException(400): If name conflict with another integration
        HTTPException(422): If invalid UUID format
    """
    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid integration ID format",
        )

    query = select(JobBoardIntegration).where(JobBoardIntegration.id == integration_uuid)
    result = await db.execute(query)
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )

    try:
        # Update fields if provided
        if integration_data.name is not None:
            # Check for name conflict
            existing_query = select(JobBoardIntegration).where(
                JobBoardIntegration.name == integration_data.name,
                JobBoardIntegration.id != integration_uuid
            )
            existing_result = await db.execute(existing_query)
            existing_integration = existing_result.scalar_one_or_none()

            if existing_integration:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Integration with name '{integration_data.name}' already exists",
                )
            integration.name = integration_data.name

        if integration_data.api_endpoint is not None:
            integration.api_endpoint = integration_data.api_endpoint

        if integration_data.api_key is not None:
            integration.api_key = integration_data.api_key

        if integration_data.enabled is not None:
            integration.enabled = integration_data.enabled

        if integration_data.config is not None:
            integration.config = integration_data.config

        await db.commit()
        await db.refresh(integration)

        logger.info(f"Updated job board integration: {integration_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(integration.id),
                "name": integration.name,
                "api_endpoint": integration.api_endpoint,
                "api_key": mask_api_key(integration.api_key),
                "enabled": integration.enabled,
                "config": integration.config,
                "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                "created_at": integration.created_at.isoformat() if integration.created_at else None,
                "updated_at": integration.updated_at.isoformat() if integration.updated_at else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating integration {integration_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update integration: {str(e)}",
        ) from e


@router.delete(
    "/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Job Integrations"],
)
async def delete_integration(
    request: Request,
    integration_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Delete a job board integration.

    Args:
        request: FastAPI request object
        integration_id: UUID of the integration to delete
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException(404): If integration not found
        HTTPException(422): If invalid UUID format

    Example:
        >>> response = requests.delete("http://localhost:8000/api/integrations/123")
        >>> response.status_code
        204
    """
    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid integration ID format",
        )

    query = select(JobBoardIntegration).where(JobBoardIntegration.id == integration_uuid)
    result = await db.execute(query)
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )

    try:
        await db.delete(integration)
        await db.commit()

        logger.info(f"Deleted job board integration: {integration_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except Exception as e:
        logger.error(f"Error deleting integration {integration_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete integration: {str(e)}",
        ) from e


@router.patch(
    "/{integration_id}/toggle",
    tags=["Job Integrations"],
)
async def toggle_integration(
    request: Request,
    integration_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Toggle a job board integration enabled/disabled status.

    Args:
        request: FastAPI request object
        integration_id: UUID of the integration
        db: Database session

    Returns:
        JSON response with updated integration status

    Raises:
        HTTPException(404): If integration not found
        HTTPException(422): If invalid UUID format
    """
    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid integration ID format",
        )

    query = select(JobBoardIntegration).where(JobBoardIntegration.id == integration_uuid)
    result = await db.execute(query)
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )

    try:
        # Toggle enabled status
        integration.enabled = not integration.enabled
        await db.commit()
        await db.refresh(integration)

        logger.info(f"Toggled integration {integration_id} enabled to {integration.enabled}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(integration.id),
                "enabled": integration.enabled,
                "message": f"Integration {'enabled' if integration.enabled else 'disabled'}",
            },
        )

    except Exception as e:
        logger.error(f"Error toggling integration {integration_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle integration: {str(e)}",
        ) from e


@router.get(
    "/logs",
    tags=["Job Integrations"],
)
async def list_import_logs(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List import logs with pagination and optional status filtering.

    Returns a paginated list of import logs showing the history of job board
    import operations, including successes, failures, and partial imports.

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (default: 50, max: 100)
        status_filter: Optional filter by import status (success, failed, partial, skipped, in_progress)
        db: Database session

    Returns:
        JSON response with list of import logs and total count

    Raises:
        HTTPException(422): If invalid status filter value provided
        HTTPException(500): If database query fails

    Example:
        >>> response = requests.get("http://localhost:8000/api/integrations/logs?limit=10&status_filter=failed")
        >>> logs = response.json()
        >>> logs["total"]
        5
        >>> logs["logs"][0]["status"]
        'failed'
    """
    # Validate limit
    limit = min(limit, 100)

    # Validate status filter if provided
    valid_statuses = {s.value for s in ImportJobStatus}
    if status_filter and status_filter not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{status_filter}'. Valid values: {', '.join(sorted(valid_statuses))}"
        )

    try:
        # Build base query with job board join
        query = (
            select(ImportLog, JobBoardIntegration)
            .outerjoin(JobBoardIntegration, ImportLog.job_board_id == JobBoardIntegration.id)
            .order_by(ImportLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Apply status filter if provided
        if status_filter:
            query = query.where(ImportLog.status == ImportJobStatus(status_filter))

        result = await db.execute(query)
        rows = result.all()

        # Convert to response format
        logs_list = []
        for import_log, job_board in rows:
            logs_list.append({
                "id": str(import_log.id),
                "job_board_id": str(import_log.job_board_id) if import_log.job_board_id else None,
                "job_board_name": job_board.name if job_board else None,
                "status": import_log.status.value if isinstance(import_log.status, ImportJobStatus) else import_log.status,
                "records_processed": import_log.records_processed,
                "records_succeeded": import_log.records_succeeded,
                "records_failed": import_log.records_failed,
                "error_message": import_log.error_message,
                "error_details": import_log.error_details,
                "import_metadata": import_log.import_metadata,
                "started_at": import_log.started_at,
                "completed_at": import_log.completed_at,
                "retry_count": import_log.retry_count,
                "created_at": import_log.created_at.isoformat() if import_log.created_at else None,
                "updated_at": import_log.updated_at.isoformat() if import_log.updated_at else None,
            })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"logs": logs_list, "total": len(logs_list)},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing import logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list import logs: {str(e)}",
        ) from e


@router.post(
    "/{integration_id}/trigger-import",
    tags=["Job Integrations"],
)
async def trigger_manual_import(
    request: Request,
    integration_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Trigger a manual import for a specific job board integration.

    This endpoint manually triggers the poll_job_board Celery task for the specified
    integration, allowing users to import applicants on-demand without waiting for
    the scheduled polling interval.

    Args:
        request: FastAPI request object
        integration_id: UUID of the integration to trigger import for
        db: Database session

    Returns:
        JSON response with task ID and status

    Raises:
        HTTPException(404): If integration not found
        HTTPException(400): If integration is disabled
        HTTPException(422): If invalid UUID format
        HTTPException(500): If task trigger fails

    Example:
        >>> response = requests.post("http://localhost:8000/api/integrations/123/trigger-import")
        >>> result = response.json()
        >>> result["task_id"]
        'abc-123-def'
        >>> result["message"]
        'Import task triggered successfully'
    """
    locale = _extract_locale(request)

    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid integration ID format",
        )

    query = select(JobBoardIntegration).where(JobBoardIntegration.id == integration_uuid)
    result = await db.execute(query)
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )

    if not integration.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot trigger import for disabled integration. Please enable it first.",
        )

    try:
        # Trigger the Celery task asynchronously
        task = poll_job_board.apply_async(
            args=[str(integration.id)],
            kwargs={
                "job_id": None,
                "status_filter": None,
                "from_date": None,
            }
        )

        logger.info(
            f"Triggered manual import for integration {integration_id} "
            f"with Celery task ID: {task.id}"
        )

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "task_id": task.id,
                "integration_id": str(integration.id),
                "integration_name": integration.name,
                "message": "Import task triggered successfully",
                "status": "pending",
            },
        )

    except Exception as e:
        logger.error(f"Error triggering import for integration {integration_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger import task: {str(e)}",
        ) from e
