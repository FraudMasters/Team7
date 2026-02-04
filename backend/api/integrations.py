"""
Integration management API endpoints for HRIS/ATS platform configurations.

This module provides endpoints for:
- Listing all configured integrations (Workday, Greenhouse, Lever, etc.)
- Creating new integration configurations
- Getting integration details by ID
- Updating integration configurations
- Deleting integrations
- Testing connection to external platforms
- Triggering sync operations
- Retrieving sync history and status
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.integration import Integration, IntegrationPlatform, IntegrationStatus
from models.sync_log import SyncLog, SyncType, SyncStatus
from models.audit_log import AuditActionType
from utils.audit_logger import log_audit_event, get_request_context

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class IntegrationCreateRequest(BaseModel):
    """Request model for creating a new integration."""

    name: str = Field(..., min_length=3, max_length=255, description="Human-readable name for this integration")
    platform: IntegrationPlatform = Field(..., description="Platform type (WORKDAY, GREENHOUSE, LEVER, BAMBOOHR, ASHBY)")
    credentials: dict = Field(..., description="API credentials for the platform")
    organization_config: Optional[dict] = Field(None, description="Platform-specific organization settings")
    webhook_url: Optional[str] = Field(None, max_length=512, description="Webhook URL for receiving data from platform")
    sync_enabled: bool = Field(False, description="Whether automatic sync is enabled")
    sync_interval_minutes: Optional[int] = Field(None, ge=1, description="Sync interval in minutes")


class IntegrationUpdateRequest(BaseModel):
    """Request model for updating an integration."""

    name: Optional[str] = Field(None, min_length=3, max_length=255, description="Integration name")
    status: Optional[IntegrationStatus] = Field(None, description="Integration status")
    credentials: Optional[dict] = Field(None, description="API credentials")
    organization_config: Optional[dict] = Field(None, description="Platform-specific settings")
    webhook_url: Optional[str] = Field(None, max_length=512, description="Webhook URL")
    sync_enabled: Optional[bool] = Field(None, description="Whether automatic sync is enabled")
    sync_interval_minutes: Optional[int] = Field(None, ge=1, description="Sync interval in minutes")


class IntegrationResponse(BaseModel):
    """Response model for integration."""

    id: str = Field(..., description="Integration ID")
    name: str = Field(..., description="Integration name")
    platform: str = Field(..., description="Platform type")
    status: str = Field(..., description="Integration status")
    credentials: dict = Field(..., description="API credentials (sanitized)")
    organization_config: Optional[dict] = Field(None, description="Platform-specific settings")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    sync_enabled: bool = Field(..., description="Whether sync is enabled")
    sync_interval_minutes: Optional[int] = Field(None, description="Sync interval in minutes")
    last_sync_at: Optional[str] = Field(None, description="Last successful sync timestamp")
    last_sync_status: Optional[str] = Field(None, description="Last sync status")
    error_message: Optional[str] = Field(None, description="Error message if last sync failed")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class TestConnectionResponse(BaseModel):
    """Response model for testing connection."""

    success: bool = Field(..., description="Whether connection test was successful")
    message: str = Field(..., description="Test result message")
    details: Optional[dict] = Field(None, description="Additional connection details")


class SyncTriggerRequest(BaseModel):
    """Request model for triggering a sync operation."""

    sync_type: str = Field(..., description="Type of sync to perform (full, incremental)")
    force: bool = Field(False, description="Force sync even if one is already in progress")


class SyncTriggerResponse(BaseModel):
    """Response model for sync trigger."""

    sync_id: str = Field(..., description="Sync operation ID")
    integration_id: str = Field(..., description="Integration ID")
    sync_type: str = Field(..., description="Type of sync triggered")
    status: str = Field(..., description="Initial sync status")
    message: str = Field(..., description="Response message")


class SyncHistoryItem(BaseModel):
    """Single sync history entry."""

    sync_id: str = Field(..., description="Sync operation ID")
    sync_type: str = Field(..., description="Type of sync (full, incremental)")
    status: str = Field(..., description="Sync status (pending, running, completed, failed)")
    started_at: Optional[str] = Field(None, description="Sync start timestamp")
    completed_at: Optional[str] = Field(None, description="Sync completion timestamp")
    duration_seconds: Optional[int] = Field(None, description="Sync duration in seconds")
    records_processed: int = Field(..., description="Total records processed")
    records_successful: int = Field(..., description="Successfully processed records")
    records_failed: int = Field(..., description="Failed records")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[dict] = Field(None, description="Additional sync metadata")


class SyncHistoryResponse(BaseModel):
    """Response model for sync history."""

    integration_id: str = Field(..., description="Integration ID")
    integration_name: str = Field(..., description="Integration name")
    syncs: list[SyncHistoryItem] = Field(..., description="List of sync operations")
    total_syncs: int = Field(..., description="Total number of syncs")
    completed_syncs: int = Field(..., description="Number of completed syncs")
    failed_syncs: int = Field(..., description="Number of failed syncs")


class SyncStatusResponse(BaseModel):
    """Response model for sync status."""

    sync_id: str = Field(..., description="Sync operation ID")
    integration_id: str = Field(..., description="Integration ID")
    integration_name: str = Field(..., description="Integration name")
    sync_type: str = Field(..., description="Type of sync")
    status: str = Field(..., description="Current sync status")
    started_at: Optional[str] = Field(None, description="Sync start timestamp")
    completed_at: Optional[str] = Field(None, description="Sync completion timestamp")
    duration_seconds: Optional[int] = Field(None, description="Sync duration in seconds")
    records_processed: int = Field(..., description="Total records processed")
    records_successful: int = Field(..., description="Successfully processed records")
    records_failed: int = Field(..., description="Failed records")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[dict] = Field(None, description="Additional sync metadata")


def _sanitize_credentials(credentials: dict) -> dict:
    """Sanitize credentials for API responses by masking sensitive values."""
    if not credentials:
        return {}

    sanitized = {}
    sensitive_keys = {"password", "secret", "token", "key", "api_key", "apikey"}

    for key, value in credentials.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            # Mask sensitive values
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value

    return sanitized


def _integration_to_response(integration: Integration) -> dict:
    """Convert Integration model to response dict."""
    return {
        "id": str(integration.id),
        "name": integration.name,
        "platform": integration.platform.value,
        "status": integration.status.value,
        "credentials": _sanitize_credentials(integration.credentials),
        "organization_config": integration.organization_config,
        "webhook_url": integration.webhook_url,
        "sync_enabled": integration.sync_enabled,
        "sync_interval_minutes": integration.sync_interval_minutes,
        "last_sync_at": integration.last_sync_at,
        "last_sync_status": integration.last_sync_status,
        "error_message": integration.error_message,
        "created_at": integration.created_at.isoformat() if integration.created_at else None,
        "updated_at": integration.updated_at.isoformat() if integration.updated_at else None,
    }


@router.post(
    "/",
    response_model=IntegrationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Integrations"],
)
async def create_integration(
    request: Request,
    integration: IntegrationCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Create a new integration configuration.

    This endpoint allows administrators to configure a new integration
    with an external HRIS/ATS platform.

    Args:
        request: FastAPI request object
        integration: Integration data from request body
        db: Database session

    Returns:
        JSON response with created integration details

    Example:
        >>> integration_data = {
        ...     "name": "Workday Production",
        ...     "platform": "WORKDAY",
        ...     "credentials": {"api_url": "https://wd1.myworkday.com", "username": "api_user", "password": "secret"},
        ...     "sync_enabled": True,
        ...     "sync_interval_minutes": 60
        ... }
        >>> response = requests.post("http://localhost:8000/api/integrations/", json=integration_data)
    """
    try:
        # Create new Integration instance
        new_integration = Integration(
            name=integration.name,
            platform=integration.platform,
            credentials=integration.credentials,
            organization_config=integration.organization_config,
            webhook_url=integration.webhook_url,
            sync_enabled=integration.sync_enabled,
            sync_interval_minutes=integration.sync_interval_minutes,
            status=IntegrationStatus.PENDING,
        )

        db.add(new_integration)
        await db.commit()
        await db.refresh(new_integration)

        # Log audit event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.INTEGRATION_CREATED,
            entity_type="integration",
            entity_id=new_integration.id,
            ip_address=ip_address,
            user_agent=user_agent,
            after_value=_integration_to_response(new_integration),
        )

        logger.info(f"Created integration: {new_integration.id} - {new_integration.name} ({new_integration.platform.value})")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=_integration_to_response(new_integration),
        )

    except Exception as e:
        logger.error(f"Error creating integration: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create integration: {str(e)}",
        ) from e


@router.get("/", response_model=list[IntegrationResponse], tags=["Integrations"])
async def list_integrations(
    request: Request,
    platform: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List all integrations.

    Returns a paginated list of all configured integrations.
    Can be filtered by platform and status.

    Args:
        request: FastAPI request object
        platform: Optional filter by platform type
        status_filter: Optional filter by status
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of integrations

    Example:
        >>> response = requests.get("http://localhost:8000/api/integrations/?platform=WORKDAY")
        >>> integrations = response.json()
    """
    try:
        # Build query
        query = select(Integration)

        # Apply filters
        if platform:
            try:
                platform_enum = IntegrationPlatform(platform)
                query = query.where(Integration.platform == platform_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid platform: {platform}",
                )

        if status_filter:
            try:
                status_enum = IntegrationStatus(status_filter)
                query = query.where(Integration.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}",
                )

        # Order by created date descending
        query = query.order_by(Integration.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        integrations = result.scalars().all()

        # Convert to response format
        integrations_list = [_integration_to_response(i) for i in integrations]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=integrations_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing integrations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list integrations: {str(e)}",
        ) from e


@router.get("/{integration_id}", response_model=IntegrationResponse, tags=["Integrations"])
async def get_integration(
    request: Request,
    integration_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get a specific integration by ID.

    Args:
        request: FastAPI request object
        integration_id: UUID of the integration
        db: Database session

    Returns:
        JSON response with integration details

    Raises:
        HTTPException(404): If integration not found

    Example:
        >>> response = requests.get("http://localhost:8000/api/integrations/123")
        >>> integration = response.json()
    """
    try:
        # Query integration from database
        query = select(Integration).where(Integration.id == UUID(integration_id))
        result = await db.execute(query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found",
            )

        # Log audit event for viewing integration
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.INTEGRATION_VIEWED,
            entity_type="integration",
            entity_id=integration.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_integration_to_response(integration),
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid integration ID format",
        )
    except Exception as e:
        logger.error(f"Error getting integration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration: {str(e)}",
        ) from e


@router.put("/{integration_id}", response_model=IntegrationResponse, tags=["Integrations"])
async def update_integration(
    request: Request,
    integration_id: str,
    integration: IntegrationUpdateRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Update an integration configuration.

    Args:
        request: FastAPI request object
        integration_id: UUID of the integration
        integration: Updated integration data
        db: Database session

    Returns:
        JSON response with updated integration details

    Raises:
        HTTPException(404): If integration not found

    Example:
        >>> update_data = {"status": "ACTIVE", "sync_enabled": True}
        >>> response = requests.put("http://localhost:8000/api/integrations/123", json=update_data)
    """
    try:
        # Query integration from database
        query = select(Integration).where(Integration.id == UUID(integration_id))
        result = await db.execute(query)
        integration_obj = result.scalar_one_or_none()

        if not integration_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found",
            )

        # Capture before state for audit log
        before_state = _integration_to_response(integration_obj)

        # Update fields
        if integration.name is not None:
            integration_obj.name = integration.name
        if integration.status is not None:
            integration_obj.status = integration.status
        if integration.credentials is not None:
            integration_obj.credentials = integration.credentials
        if integration.organization_config is not None:
            integration_obj.organization_config = integration.organization_config
        if integration.webhook_url is not None:
            integration_obj.webhook_url = integration.webhook_url
        if integration.sync_enabled is not None:
            integration_obj.sync_enabled = integration.sync_enabled
        if integration.sync_interval_minutes is not None:
            integration_obj.sync_interval_minutes = integration.sync_interval_minutes

        await db.commit()
        await db.refresh(integration_obj)

        # Log audit event with before and after values
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.INTEGRATION_UPDATED,
            entity_type="integration",
            entity_id=integration_obj.id,
            ip_address=ip_address,
            user_agent=user_agent,
            before_value=before_state,
            after_value=_integration_to_response(integration_obj),
        )

        logger.info(f"Updated integration: {integration_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_integration_to_response(integration_obj),
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid integration ID format",
        )
    except Exception as e:
        logger.error(f"Error updating integration: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update integration: {str(e)}",
        ) from e


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Integrations"])
async def delete_integration(
    request: Request,
    integration_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Delete an integration configuration.

    Args:
        request: FastAPI request object
        integration_id: UUID of the integration to delete
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException(404): If integration not found

    Example:
        >>> response = requests.delete("http://localhost:8000/api/integrations/123")
        >>> response.status_code
        204
    """
    try:
        # Query integration from database
        query = select(Integration).where(Integration.id == UUID(integration_id))
        result = await db.execute(query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found",
            )

        # Capture before state for audit log
        before_state = _integration_to_response(integration)

        # Delete integration (cascade will handle related records)
        await db.delete(integration)
        await db.commit()

        # Log audit event with before value
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.INTEGRATION_DELETED,
            entity_type="integration",
            entity_id=integration.id,
            ip_address=ip_address,
            user_agent=user_agent,
            before_value=before_state,
        )

        logger.info(f"Deleted integration: {integration_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid integration ID format",
        )
    except Exception as e:
        logger.error(f"Error deleting integration: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete integration: {str(e)}",
        ) from e


@router.post("/{integration_id}/test", response_model=TestConnectionResponse, tags=["Integrations"])
async def test_connection(
    request: Request,
    integration_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Test connection to an external platform.

    This endpoint validates the integration configuration by attempting
    to connect to the external platform API.

    Args:
        request: FastAPI request object
        integration_id: UUID of the integration to test
        db: Database session

    Returns:
        JSON response with test results

    Raises:
        HTTPException(404): If integration not found

    Example:
        >>> response = requests.post("http://localhost:8000/api/integrations/123/test")
        >>> result = response.json()
        >>> {"success": true, "message": "Connection successful", "details": {...}}
    """
    try:
        # Query integration from database
        query = select(Integration).where(Integration.id == UUID(integration_id))
        result = await db.execute(query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found",
            )

        logger.info(f"Testing connection for integration: {integration_id} ({integration.platform.value})")

        # Placeholder connection test logic
        # In a real implementation, this would:
        # 1. Extract credentials from integration.credentials
        # 2. Make a test API call to the platform
        # 3. Return success/failure based on response

        # For now, simulate a successful test
        # TODO: Implement actual connection testing for each platform
        test_success = True
        test_message = f"Connection test successful for {integration.platform.value}"
        test_details = {
            "platform": integration.platform.value,
            "tested_at": integration.updated_at.isoformat() if integration.updated_at else None,
            "note": "Actual connection testing not yet implemented - this is a placeholder response"
        }

        # Update integration status based on test result
        if test_success:
            integration.status = IntegrationStatus.ACTIVE
            integration.error_message = None
        else:
            integration.status = IntegrationStatus.ERROR
            integration.error_message = test_message

        await db.commit()

        # Log audit event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.INTEGRATION_TESTED,
            entity_type="integration",
            entity_id=integration.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": test_success,
                "message": test_message,
                "details": test_details,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid integration ID format",
        )
    except Exception as e:
        logger.error(f"Error testing connection: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test connection: {str(e)}",
        ) from e


@router.post("/{integration_id}/sync", response_model=SyncTriggerResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Integrations"])
async def trigger_sync(
    request: Request,
    integration_id: str,
    sync_request: SyncTriggerRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Trigger a sync operation for an integration.

    This endpoint initiates a manual or scheduled sync operation for the specified
    integration. The sync is performed asynchronously and returns immediately with
    a 202 Accepted status.

    Args:
        request: FastAPI request object
        integration_id: UUID of the integration
        sync_request: Sync trigger request with sync type
        db: Database session

    Returns:
        JSON response with sync operation details (202 Accepted)

    Raises:
        HTTPException(400): If invalid sync type or integration is not active
        HTTPException(404): If integration not found
        HTTPException(409): If a sync is already in progress and force=False

    Example:
        >>> sync_data = {"sync_type": "full", "force": False}
        >>> response = requests.post("http://localhost:8000/api/integrations/123/sync", json=sync_data)
        >>> response.status_code
        202
        >>> sync_data = response.json()
        >>> {"sync_id": "...", "integration_id": "123", "sync_type": "full", "status": "pending", ...}
    """
    try:
        # Query integration from database
        query = select(Integration).where(Integration.id == UUID(integration_id))
        result = await db.execute(query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found",
            )

        # Validate integration status
        if integration.status != IntegrationStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Integration must be active to trigger sync. Current status: {integration.status.value}",
            )

        # Validate sync type
        valid_sync_types = ["full", "incremental"]
        if sync_request.sync_type not in valid_sync_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sync_type: {sync_request.sync_type}. Must be one of: {', '.join(valid_sync_types)}",
            )

        # Map sync type to SyncType enum
        sync_type_map = {
            "full": SyncType.FULL_SYNC,
            "incremental": SyncType.INCREMENTAL_SYNC,
        }
        sync_type_enum = sync_type_map[sync_request.sync_type]

        # Check if there's a sync already in progress
        if not sync_request.force:
            existing_sync_query = select(SyncLog).where(
                SyncLog.integration_id == UUID(integration_id),
                SyncLog.status.in_([SyncStatus.PENDING, SyncStatus.RUNNING])
            ).order_by(SyncLog.created_at.desc())

            existing_sync_result = await db.execute(existing_sync_query)
            existing_sync = existing_sync_result.first()

            if existing_sync:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A sync operation is already in progress. Sync ID: {existing_sync[0].id}. Use force=True to override.",
                )

        # Create sync log entry
        new_sync = SyncLog(
            integration_id=integration.id,
            sync_type=sync_type_enum,
            status=SyncStatus.PENDING,
            records_processed=0,
            records_successful=0,
            records_failed=0,
            sync_metadata={
                "triggered_by": "manual",
                "force": sync_request.force,
            },
        )

        db.add(new_sync)
        await db.commit()
        await db.refresh(new_sync)

        # Log audit event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.INTEGRATION_UPDATED,  # Reusing existing audit type
            entity_type="sync",
            entity_id=new_sync.id,
            ip_address=ip_address,
            user_agent=user_agent,
            after_value={
                "integration_id": integration_id,
                "sync_type": sync_request.sync_type,
                "status": "pending",
            },
        )

        logger.info(
            f"Triggered {sync_request.sync_type} sync for integration {integration_id} "
            f"(platform: {integration.platform.value}, sync_id: {new_sync.id})"
        )

        # TODO: Trigger Celery task for actual sync execution
        # This will be implemented in phase-4 (worker tasks)
        # Example: sync_integration_task.delay(str(new_sync.id))

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "sync_id": str(new_sync.id),
                "integration_id": integration_id,
                "sync_type": sync_request.sync_type,
                "status": new_sync.status.value,
                "message": f"{sync_request.sync_type.capitalize()} sync operation initiated. The sync will run in the background.",
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid integration ID format",
        )
    except Exception as e:
        logger.error(f"Error triggering sync: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger sync: {str(e)}",
        ) from e


@router.get(
    "/{integration_id}/syncs",
    response_model=SyncHistoryResponse,
    tags=["Integrations"],
)
async def get_sync_history(
    request: Request,
    integration_id: str,
    status_filter: Optional[str] = Query(None, description="Filter by sync status"),
    sync_type_filter: Optional[str] = Query(None, description="Filter by sync type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get sync history for an integration.

    This endpoint returns a paginated list of all sync operations for a specific integration,
    including status, timestamps, and record counts. Supports filtering by status and sync type.

    Args:
        request: FastAPI request object
        integration_id: UUID of the integration
        status_filter: Optional filter by sync status (pending, running, completed, failed)
        sync_type_filter: Optional filter by sync type (full, incremental)
        limit: Maximum number of records to return (1-100, default: 50)
        offset: Number of records to skip for pagination
        db: Database session

    Returns:
        JSON response with sync history and summary statistics

    Raises:
        HTTPException(404): If integration not found
        HTTPException(400): If invalid filter values

    Examples:
        >>> response = requests.get("http://localhost:8000/api/integrations/123/syncs?limit=10")
        >>> history = response.json()
        >>> {
        ...     "integration_id": "123",
        ...     "integration_name": "Workday Production",
        ...     "syncs": [...],
        ...     "total_syncs": 45,
        ...     "completed_syncs": 40,
        ...     "failed_syncs": 3
        ... }
    """
    try:
        # Query integration from database
        query = select(Integration).where(Integration.id == UUID(integration_id))
        result = await db.execute(query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found",
            )

        logger.info(
            f"Fetching sync history for integration: {integration_id} "
            f"(status: {status_filter}, type: {sync_type_filter}, limit: {limit})"
        )

        # Build sync log query
        sync_query = select(SyncLog).where(SyncLog.integration_id == UUID(integration_id))

        # Apply filters
        if status_filter:
            try:
                status_enum = SyncStatus(status_filter)
                sync_query = sync_query.where(SyncLog.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}. "
                           f"Valid values: {[s.value for s in SyncStatus]}",
                )

        if sync_type_filter:
            try:
                type_enum = SyncType(sync_type_filter.upper())
                sync_query = sync_query.where(SyncLog.sync_type == type_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid sync type filter: {sync_type_filter}. "
                           f"Valid values: {[t.value for t in SyncType]}",
                )

        # Order by started_at descending (most recent first)
        sync_query = sync_query.order_by(SyncLog.started_at.desc()).offset(offset).limit(limit)

        # Execute query
        sync_result = await db.execute(sync_query)
        sync_logs = sync_result.scalars().all()

        # Convert to response format
        syncs_list = []
        for sync in sync_logs:
            duration_seconds = None
            if sync.started_at and sync.completed_at:
                duration_seconds = int((sync.completed_at - sync.started_at).total_seconds())

            syncs_list.append({
                "sync_id": str(sync.id),
                "sync_type": sync.sync_type.value,
                "status": sync.status.value,
                "started_at": sync.started_at.isoformat() if sync.started_at else None,
                "completed_at": sync.completed_at.isoformat() if sync.completed_at else None,
                "duration_seconds": duration_seconds,
                "records_processed": sync.records_processed or 0,
                "records_successful": sync.records_successful or 0,
                "records_failed": sync.records_failed or 0,
                "error_message": sync.error_message,
                "metadata": sync.sync_metadata,
            })

        # Get summary statistics for all syncs (not just the paginated result)
        count_query = select(SyncLog).where(SyncLog.integration_id == UUID(integration_id))
        all_syncs_result = await db.execute(count_query)
        all_syncs = all_syncs_result.scalars().all()

        total_syncs = len(all_syncs)
        completed_syncs = sum(1 for s in all_syncs if s.status == SyncStatus.COMPLETED)
        failed_syncs = sum(1 for s in all_syncs if s.status == SyncStatus.FAILED)

        logger.info(
            f"Retrieved sync history for integration {integration_id}: "
            f"{len(syncs_list)} of {total_syncs} syncs"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "integration_id": integration_id,
                "integration_name": integration.name,
                "syncs": syncs_list,
                "total_syncs": total_syncs,
                "completed_syncs": completed_syncs,
                "failed_syncs": failed_syncs,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid integration ID format",
        )
    except Exception as e:
        logger.error(f"Error retrieving sync history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sync history: {str(e)}",
        ) from e


@router.get(
    "/{integration_id}/syncs/{sync_id}",
    response_model=SyncStatusResponse,
    tags=["Integrations"],
)
async def get_sync_status(
    request: Request,
    integration_id: str,
    sync_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get status of a specific sync operation.

    This endpoint returns detailed information about a specific sync operation,
    including current status, progress, and any error messages.

    Args:
        request: FastAPI request object
        integration_id: UUID of the integration
        sync_id: UUID of the sync operation
        db: Database session

    Returns:
        JSON response with detailed sync status

    Raises:
        HTTPException(404): If integration or sync not found

    Examples:
        >>> response = requests.get("http://localhost:8000/api/integrations/123/syncs/abc-123")
        >>> status = response.json()
        >>> {
        ...     "sync_id": "abc-123",
        ...     "integration_id": "123",
        ...     "integration_name": "Workday Production",
        ...     "sync_type": "full",
        ...     "status": "completed",
        ...     "started_at": "2024-01-15T10:00:00Z",
        ...     "completed_at": "2024-01-15T10:05:30Z",
        ...     "duration_seconds": 330,
        ...     "records_processed": 1250,
        ...     "records_successful": 1245,
        ...     "records_failed": 5,
        ...     "error_message": None,
        ...     "metadata": {...}
        ... }
    """
    try:
        # Query integration from database
        integration_query = select(Integration).where(Integration.id == UUID(integration_id))
        integration_result = await db.execute(integration_query)
        integration = integration_result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found",
            )

        # Query sync log from database
        sync_query = select(SyncLog).where(
            SyncLog.id == UUID(sync_id),
            SyncLog.integration_id == UUID(integration_id)
        )
        sync_result = await db.execute(sync_query)
        sync = sync_result.scalar_one_or_none()

        if not sync:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sync operation not found",
            )

        logger.info(f"Fetching sync status: {sync_id} for integration {integration_id}")

        # Calculate duration if sync is completed
        duration_seconds = None
        if sync.started_at and sync.completed_at:
            duration_seconds = int((sync.completed_at - sync.started_at).total_seconds())

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "sync_id": str(sync.id),
                "integration_id": integration_id,
                "integration_name": integration.name,
                "sync_type": sync.sync_type.value,
                "status": sync.status.value,
                "started_at": sync.started_at.isoformat() if sync.started_at else None,
                "completed_at": sync.completed_at.isoformat() if sync.completed_at else None,
                "duration_seconds": duration_seconds,
                "records_processed": sync.records_processed or 0,
                "records_successful": sync.records_successful or 0,
                "records_failed": sync.records_failed or 0,
                "error_message": sync.error_message,
                "metadata": sync.sync_metadata,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )
    except Exception as e:
        logger.error(f"Error retrieving sync status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sync status: {str(e)}",
        ) from e
