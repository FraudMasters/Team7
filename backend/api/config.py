"""
Configuration management API endpoints.

This module provides endpoints for managing application configuration,
including viewing current config, reloading settings, and viewing
configuration change audit logs.
"""
import logging
import os
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings, reload_settings
from config.validation import validate_config, ConfigurationError
from config.audit import log_config_change
from config.hotreload import (
    detect_setting_changes,
    format_changes_for_logging,
    get_reload_summary,
    is_reloadable,
    validate_reload_safety,
)
from database import get_db
from models.config_change import ConfigChange, ConfigChangeAction

logger = logging.getLogger(__name__)

router = APIRouter()


class TestAuditRequest(BaseModel):
    """Request model for test audit endpoint."""

    test: str = Field(..., description="Test value to log")


class TestAuditResponse(BaseModel):
    """Response model for test audit endpoint."""

    message: str = Field(..., description="Success message")
    logged: bool = Field(..., description="Whether the audit log was created")
    environment: str = Field(..., description="Current environment")


class ConfigChangeItem(BaseModel):
    """Single configuration change item."""

    id: str = Field(..., description="Config change ID")
    action_type: str = Field(..., description="Type of action performed")
    config_key: Optional[str] = Field(None, description="Configuration key that was changed")
    config_path: Optional[str] = Field(None, description="Dot-notation path for nested configs")
    environment: Optional[str] = Field(None, description="Environment where the change occurred")
    user_id: Optional[str] = Field(None, description="User who made the change")
    organization_id: Optional[str] = Field(None, description="Organization where the change occurred")
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    before_value: Optional[dict] = Field(None, description="Configuration value before the change")
    after_value: Optional[dict] = Field(None, description="Configuration value after the change")
    change_reason: Optional[str] = Field(None, description="Reason or explanation for the change")
    metadata: Optional[dict] = Field(None, description="Additional metadata about the change")
    created_at: str = Field(..., description="When the change occurred")


class ConfigChangesResponse(BaseModel):
    """Response model for config changes list."""

    changes: List[ConfigChangeItem] = Field(..., description="List of config changes")
    total_count: int = Field(..., description="Total number of changes matching the filters")


@router.post(
    "/test-audit",
    response_model=TestAuditResponse,
    tags=["Configuration"],
)
async def test_audit_logging(
    request: TestAuditRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Test configuration audit logging.

    This endpoint creates a test configuration change audit log to verify
    that the audit logging system is working correctly.

    Args:
        request: Test request with a value to log
        http_request: FastAPI Request object for context
        db: Database session

    Returns:
        JSON response with success status and logged flag

    Raises:
        HTTPException(500): If audit logging fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/config/test-audit",
        ...     json={"test": "value"}
        ... )
        >>> response.json()
        {
            "message": "Audit log test successful",
            "logged": true,
            "environment": "development"
        }
    """
    try:
        logger.info(f"Testing audit logging with value: {request.test}")

        settings = get_settings()
        environment = settings.environment

        # Log the test audit event
        config_change = await log_config_change(
            db=db,
            action_type=ConfigChangeAction.VALUE_UPDATED,
            config_key="test_audit_key",
            config_path="test.audit",
            environment=environment,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("User-Agent"),
            after_value={"test_value": request.test},
            change_reason="Test audit logging endpoint",
            metadata={"test_mode": True},
        )

        if config_change:
            logger.info(f"Audit log test successful: {config_change.id}")
            response_data = {
                "message": "Audit log test successful",
                "logged": True,
                "environment": environment,
            }
        else:
            logger.warning("Audit log test failed to create log entry")
            response_data = {
                "message": "Audit log test failed to create log entry",
                "logged": False,
                "environment": environment,
            }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error in audit log test: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test audit logging: {str(e)}",
        ) from e


@router.get(
    "/audit-logs",
    response_model=ConfigChangesResponse,
    tags=["Configuration"],
)
async def get_config_audit_logs(
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    config_key: Optional[str] = Query(None, description="Filter by configuration key"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    user_id: Optional[str] = Query(None, description="Filter by user who made the change"),
    start_date: Optional[str] = Query(None, description="Filter logs after this date (ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Filter logs before this date (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip for pagination"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get configuration change audit logs with filtering options.

    This endpoint retrieves configuration change audit logs, including
    value updates, environment changes, hot-reload operations, and other
    configuration-related actions.

    Logs are returned in reverse chronological order (newest first).

    Args:
        action_type: Optional filter for specific action type
        config_key: Optional filter for configuration key
        environment: Optional filter for environment
        user_id: Optional filter for user who made the change
        start_date: Optional filter to only include logs after this date
        end_date: Optional filter to only include logs before this date
        limit: Maximum number of logs to return (default: 100, max: 1000)
        offset: Number of logs to skip for pagination (default: 0)
        db: Database session

    Returns:
        JSON response with list of config changes and total count

    Raises:
        HTTPException(400): If action_type is invalid
        HTTPException(400): If date format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/config/audit-logs?limit=10")
        >>> response.json()
        {
            "changes": [
                {
                    "id": "change-1",
                    "action_type": "value_updated",
                    "config_key": "database_url",
                    "config_path": "database.url",
                    "environment": "production",
                    "user_id": "user-1",
                    "before_value": {"url": "old-db.example.com"},
                    "after_value": {"url": "new-db.example.com"},
                    "change_reason": "Database migration",
                    "created_at": "2026-01-31T10:30:00Z"
                }
            ],
            "total_count": 1
        }
    """
    try:
        logger.info(
            f"Fetching config audit logs - action_type: {action_type}, "
            f"config_key: {config_key}, environment: {environment}"
        )

        # Build base query
        query = select(ConfigChange)

        # Apply filters
        if action_type:
            valid_types = [t.value for t in ConfigChangeAction]
            if action_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid action_type: {action_type}. "
                           f"Valid types are: {', '.join(valid_types)}",
                )
            query = query.where(ConfigChange.action_type == action_type)

        if config_key:
            query = query.where(ConfigChange.config_key == config_key)

        if environment:
            query = query.where(ConfigChange.environment == environment)

        if user_id:
            try:
                user_uuid = UUID(user_id)
                query = query.where(ConfigChange.user_id == user_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid user_id format: {user_id}",
                )

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.where(ConfigChange.created_at >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                )

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.where(ConfigChange.created_at <= end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                )

        # Order by created_at descending (newest first) and apply pagination
        query = query.order_by(ConfigChange.created_at.desc()).limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        config_changes = result.scalars().all()

        # Build response data
        changes_data = []
        for change in config_changes:
            changes_data.append({
                "id": str(change.id),
                "action_type": change.action_type.value,
                "config_key": change.config_key,
                "config_path": change.config_path,
                "environment": change.environment,
                "user_id": str(change.user_id) if change.user_id else None,
                "organization_id": str(change.organization_id) if change.organization_id else None,
                "ip_address": change.ip_address,
                "user_agent": change.user_agent,
                "before_value": change.before_value,
                "after_value": change.after_value,
                "change_reason": change.change_reason,
                "metadata": change.metadata,
                "created_at": change.created_at.isoformat(),
            })

        response_data = {
            "changes": changes_data,
            "total_count": len(changes_data),
        }

        logger.info(f"Retrieved {len(changes_data)} config audit logs")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving config audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve config audit logs: {str(e)}",
        ) from e


class ActionTypesResponse(BaseModel):
    """Response model for available config action types."""

    action_types: List[str] = Field(..., description="List of available action types")


class ConfigReloadResponse(BaseModel):
    """Response model for config reload endpoint."""

    success: bool = Field(..., description="Whether the reload was successful")
    message: str = Field(..., description="Status message")
    changed_count: int = Field(..., description="Number of settings that changed")
    changes: dict = Field(..., description="Settings that changed with before/after values")
    reloadable_count: int = Field(..., description="Total number of reloadable settings")
    environment: str = Field(..., description="Current environment")
    last_reload: str = Field(..., description="Timestamp of the reload")


class ConfigHealthResponse(BaseModel):
    """Response model for config health check endpoint."""

    status: str = Field(..., description="Configuration health status")
    environment: str = Field(..., description="Current environment")
    config_valid: bool = Field(..., description="Whether configuration is valid")
    config_source: str = Field(..., description="Source of configuration (env, file, etc.)")
    reloadable_settings: int = Field(..., description="Number of reloadable settings")
    critical_settings_count: int = Field(..., description="Number of critical settings")


@router.get(
    "/action-types",
    response_model=ActionTypesResponse,
    tags=["Configuration"],
)
async def get_config_action_types() -> JSONResponse:
    """
    Get available configuration change action types.

    This endpoint returns a list of all valid action types that can be used
    for filtering configuration change audit logs.

    Returns:
        JSON response with list of action types

    Examples:
        >>> import requests
        >>> response = requests.get("/api/config/action-types")
        >>> response.json()
        {
            "action_types": [
                "value_updated",
                "value_reset",
                "environment_changed",
                "config_reloaded",
                "config_validated",
                "encrypted_value_updated",
                "secret_rotated",
                "batch_update",
                "batch_rollback",
                "config_file_loaded",
                "config_override_applied",
                "config_validation_failed"
            ]
        }
    """
    try:
        logger.info("Fetching available config action types")

        action_types = [t.value for t in ConfigChangeAction]

        response_data = {
            "action_types": action_types,
        }

        logger.info(f"Retrieved {len(action_types)} config action types")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving config action types: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve config action types: {str(e)}",
        ) from e


@router.get(
    "/health",
    response_model=ConfigHealthResponse,
    tags=["Configuration"],
)
async def config_health_check() -> JSONResponse:
    """
    Configuration health check endpoint.

    Returns the current health status of the application configuration.
    This endpoint can be used by monitoring tools to verify that the
    configuration is loaded correctly and valid.

    Returns:
        JSON response with configuration health status

    Examples:
        >>> import requests
        >>> response = requests.get("/api/config/health")
        >>> response.json()
        {
            "status": "healthy",
            "environment": "development",
            "config_valid": true,
            "config_source": "environment_variables",
            "reloadable_settings": 25,
            "critical_settings_count": 8
        }
    """
    try:
        logger.info("Configuration health check requested")

        settings = get_settings()

        # Validate configuration
        try:
            warnings = validate_config(settings)
            config_valid = True
        except ConfigurationError:
            config_valid = False

        # Get counts
        from config.hotreload import get_reload_summary, get_critical_settings
        summary = get_reload_summary(settings, settings)

        response_data = {
            "status": "healthy" if config_valid else "unhealthy",
            "environment": settings.environment,
            "config_valid": config_valid,
            "config_source": "environment_variables",
            "reloadable_settings": summary["reloadable_count"],
            "critical_settings_count": len(get_critical_settings()),
        }

        logger.info(
            f"Configuration health check - status: {response_data['status']}, "
            f"environment: {response_data['environment']}, "
            f"config_valid: {config_valid}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error during configuration health check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check configuration health: {str(e)}",
        ) from e


@router.post(
    "/reload",
    response_model=ConfigReloadResponse,
    tags=["Configuration"],
)
async def reload_configuration(
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Hot-reload non-critical configuration settings without restarting the service.

    This endpoint reloads configuration from environment variables for non-critical
    settings only. Critical settings (database URL, Redis URL, Celery URLs, etc.)
    cannot be hot-reloaded and require a service restart.

    Non-critical settings that can be reloaded include:
    - Logging level (log_level)
    - File upload limits (max_upload_size_mb, allowed_file_types)
    - Analysis timeouts (analysis_timeout_seconds)
    - LLM parameters (llm_model, llm_temperature, llm_max_tokens)
    - ATS thresholds and weights
    - Backup settings (schedule, retention, S3 config)
    - Audit log retention

    The reload process:
    1. Captures current configuration
    2. Reloads settings from environment variables
    3. Detects which settings changed
    4. Validates that critical settings haven't changed
    5. Logs the configuration change to the audit log

    Args:
        http_request: FastAPI Request object for context
        db: Database session

    Returns:
        JSON response with reload status and changed settings

    Raises:
        HTTPException(400): If critical settings changed (requires restart)
        HTTPException(500): If reload operation fails

    Examples:
        >>> import requests
        >>> response = requests.post("/api/config/reload")
        >>> response.json()
        {
            "success": true,
            "message": "Configuration reloaded successfully",
            "changed_count": 2,
            "changes": {
                "log_level": {"before": "INFO", "after": "DEBUG"},
                "llm_temperature": {"before": 0.1, "after": 0.2}
            },
            "reloadable_count": 25,
            "environment": "development",
            "last_reload": "2026-02-07T12:30:45Z"
        }
    """
    try:
        logger.info("Configuration reload requested")

        # Capture current configuration before reload
        old_settings = get_settings()
        environment = old_settings.environment

        # Reload settings from environment
        new_settings = reload_settings()

        # Validate that critical settings haven't changed
        critical_changes = validate_reload_safety(old_settings, new_settings)
        if critical_changes:
            logger.error(
                f"Cannot hot-reload: critical settings changed: {critical_changes}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Cannot hot-reload configuration",
                    "message": "Critical settings have changed that require a service restart",
                    "critical_settings_changed": critical_changes,
                    "suggestion": "Restart the service to apply these changes",
                },
            )

        # Detect what changed
        changes = detect_setting_changes(old_settings, new_settings)

        # Generate summary
        summary = get_reload_summary(old_settings, new_settings)

        # Get current time for audit log
        from datetime import datetime
        now = datetime.utcnow()

        # Log the configuration reload to audit log
        ip_address, user_agent = None, None
        if http_request.client:
            ip_address = http_request.client.host
        if http_request.headers:
            user_agent = http_request.headers.get("User-Agent")

        # Create change details for audit
        changes_for_audit = {}
        for setting_name, change in changes.items():
            changes_for_audit[setting_name] = {
                "before": str(change["before"]),
                "after": str(change["after"]),
            }

        await log_config_change(
            db=db,
            action_type=ConfigChangeAction.CONFIG_RELOADED,
            config_key="*",
            config_path=None,
            environment=environment,
            ip_address=ip_address,
            user_agent=user_agent,
            after_value={
                "changed_settings": list(changes.keys()),
                "changes": changes_for_audit,
                "reloadable_count": summary["reloadable_count"],
            },
            change_reason="Hot-reload triggered via API",
            metadata={
                "changed_count": len(changes),
                "reload_method": "api",
            },
        )

        # Format changes for logging
        if changes:
            changes_formatted = format_changes_for_logging(changes)
            logger.info(f"Configuration reloaded: {changes_formatted}")
        else:
            logger.info("Configuration reloaded: no changes detected")

        response_data = {
            "success": True,
            "message": "Configuration reloaded successfully"
            if changes
            else "Configuration reloaded: no changes detected",
            "changed_count": len(changes),
            "changes": {
                k: {"before": str(v["before"]), "after": str(v["after"])}
                for k, v in changes.items()
            },
            "reloadable_count": summary["reloadable_count"],
            "environment": environment,
            "last_reload": now.isoformat() + "Z",
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during configuration reload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload configuration: {str(e)}",
        ) from e
