"""
Audit alert configuration endpoints for managing alert rules.

This module provides endpoints for configuring alert rules that monitor
suspicious audit log patterns, including failed logins, bulk data exports,
permission changes, and unusual activity patterns.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.audit_alert_config import AuditAlertConfig, AlertType, AlertSeverity

logger = logging.getLogger(__name__)

router = APIRouter()


class AuditAlertConfigItem(BaseModel):
    """Single audit alert configuration item."""

    id: str = Field(..., description="Alert configuration ID")
    name: str = Field(..., description="Human-readable name for the alert rule")
    alert_type: str = Field(..., description="Type of alert to monitor")
    description: Optional[str] = Field(None, description="Detailed description of the alert")
    enabled: bool = Field(..., description="Whether this alert rule is active")
    severity: str = Field(..., description="Severity level of the alert")
    organization_id: Optional[str] = Field(None, description="Organization this rule applies to")
    threshold: int = Field(..., description="Numeric threshold that triggers the alert")
    time_window_minutes: int = Field(..., description="Time window in minutes for threshold evaluation")
    action_types: Optional[List[str]] = Field(None, description="List of action types to monitor")
    recipients: Optional[dict] = Field(None, description="Notification recipients configuration")
    alert_config: Optional[dict] = Field(None, description="Additional alert-specific configuration")
    cooldown_minutes: int = Field(..., description="Minutes to wait before sending another alert")
    last_triggered_at: Optional[str] = Field(None, description="When this alert was last triggered")
    trigger_count: int = Field(..., description="Number of times this alert has been triggered")
    created_by: Optional[str] = Field(None, description="User who created this alert rule")
    updated_by: Optional[str] = Field(None, description="User who last updated this alert rule")
    created_at: str = Field(..., description="When the rule was created")
    updated_at: str = Field(..., description="When the rule was last updated")


class AuditAlertConfigsResponse(BaseModel):
    """Response model for audit alert configurations list."""

    alert_configs: List[AuditAlertConfigItem] = Field(..., description="List of alert configurations")
    total_count: int = Field(..., description="Total number of alert configs matching the filters")


@router.get(
    "/",
    response_model=AuditAlertConfigsResponse,
    tags=["Audit Alerts"],
)
async def get_audit_alert_configs(
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of configs to return"),
    offset: int = Query(0, ge=0, description="Number of configs to skip for pagination"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get audit alert configurations with filtering options.

    This endpoint retrieves alert rules that monitor suspicious audit log patterns,
    including failed logins, bulk data exports, permission changes, and unusual
    activity patterns.

    Configs are returned in reverse chronological order (newest first).

    Args:
        alert_type: Optional filter for specific alert type
        enabled: Optional filter for enabled/disabled status
        severity: Optional filter for severity level
        organization_id: Optional filter for organization
        limit: Maximum number of configs to return (default: 100, max: 1000)
        offset: Number of configs to skip for pagination (default: 0)
        db: Database session

    Returns:
        JSON response with list of alert configurations and total count

    Raises:
        HTTPException(400): If alert_type or severity is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/audit/alerts/?limit=10")
        >>> response.json()
        {
            "alert_configs": [
                {
                    "id": "alert-config-1",
                    "name": "Failed Login Monitor",
                    "alert_type": "failed_logins",
                    "description": "Alerts on multiple failed login attempts",
                    "enabled": true,
                    "severity": "warning",
                    "organization_id": "org-1",
                    "threshold": 5,
                    "time_window_minutes": 10,
                    "action_types": ["login_failed"],
                    "recipients": {"emails": ["admin@example.com"]},
                    "alert_config": {},
                    "cooldown_minutes": 60,
                    "last_triggered_at": null,
                    "trigger_count": 0,
                    "created_by": "user-1",
                    "updated_by": null,
                    "created_at": "2026-01-31T10:30:00Z",
                    "updated_at": "2026-01-31T10:30:00Z"
                }
            ],
            "total_count": 1
        }
    """
    try:
        logger.info(
            f"Fetching audit alert configs - alert_type: {alert_type}, enabled: {enabled}, "
            f"severity: {severity}, organization_id: {organization_id}"
        )

        # Build base query
        query = select(AuditAlertConfig)

        # Apply filters
        if alert_type:
            # Validate alert type
            valid_types = [t.value for t in AlertType]
            if alert_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid alert_type: {alert_type}. "
                           f"Valid types are: {', '.join(valid_types)}",
                )
            query = query.where(AuditAlertConfig.alert_type == alert_type)

        if enabled is not None:
            query = query.where(AuditAlertConfig.enabled == enabled)

        if severity:
            # Validate severity
            valid_severities = [s.value for s in AlertSeverity]
            if severity not in valid_severities:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid severity: {severity}. "
                           f"Valid severities are: {', '.join(valid_severities)}",
                )
            query = query.where(AuditAlertConfig.severity == severity)

        if organization_id:
            try:
                org_uuid = UUID(organization_id)
                query = query.where(AuditAlertConfig.organization_id == org_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid organization_id format: {organization_id}",
                )

        # Order by created_at descending (newest first) and apply pagination
        query = query.order_by(AuditAlertConfig.created_at.desc()).limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        alert_configs = result.scalars().all()

        # Build response data
        configs_data = []
        for config in alert_configs:
            configs_data.append({
                "id": str(config.id),
                "name": config.name,
                "alert_type": config.alert_type.value,
                "description": config.description,
                "enabled": config.enabled,
                "severity": config.severity.value,
                "organization_id": str(config.organization_id) if config.organization_id else None,
                "threshold": config.threshold,
                "time_window_minutes": config.time_window_minutes,
                "action_types": config.action_types,
                "recipients": config.recipients,
                "alert_config": config.alert_config,
                "cooldown_minutes": config.cooldown_minutes,
                "last_triggered_at": config.last_triggered_at,
                "trigger_count": config.trigger_count,
                "created_by": str(config.created_by) if config.created_by else None,
                "updated_by": str(config.updated_by) if config.updated_by else None,
                "created_at": config.created_at.isoformat(),
                "updated_at": config.updated_at.isoformat(),
            })

        response_data = {
            "alert_configs": configs_data,
            "total_count": len(configs_data),
        }

        logger.info(f"Retrieved {len(configs_data)} audit alert configs")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit alert configs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit alert configs: {str(e)}",
        ) from e


class AlertTypesResponse(BaseModel):
    """Response model for available alert types."""

    alert_types: List[str] = Field(..., description="List of available alert types")


@router.get(
    "/types",
    response_model=AlertTypesResponse,
    tags=["Audit Alerts"],
)
async def get_alert_types() -> JSONResponse:
    """
    Get available audit alert types.

    This endpoint returns a list of all valid alert types that can be used
    for configuring alert rules.

    Returns:
        JSON response with list of alert types

    Examples:
        >>> import requests
        >>> response = requests.get("/api/audit/alerts/types")
        >>> response.json()
        {
            "alert_types": [
                "failed_logins",
                "multiple_login_locations",
                "suspicious_login",
                "bulk_data_export",
                "sensitive_data_access",
                "excessive_data_queries",
                "permission_changes",
                "role_changes",
                "user_deleted",
                "user_created",
                "configuration_changes",
                "backup_operations",
                "system_settings_changed",
                "ip_blocked",
                "session_hijacking",
                "unusual_activity_pattern"
            ]
        }
    """
    try:
        logger.info("Fetching available audit alert types")

        alert_types = [t.value for t in AlertType]

        response_data = {
            "alert_types": alert_types,
        }

        logger.info(f"Retrieved {len(alert_types)} alert types")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving alert types: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alert types: {str(e)}",
        ) from e


class AlertSeveritiesResponse(BaseModel):
    """Response model for available alert severities."""

    severities: List[str] = Field(..., description="List of available severity levels")


@router.get(
    "/severities",
    response_model=AlertSeveritiesResponse,
    tags=["Audit Alerts"],
)
async def get_alert_severities() -> JSONResponse:
    """
    Get available alert severity levels.

    This endpoint returns a list of all valid severity levels that can be used
    for configuring alert rules.

    Returns:
        JSON response with list of severity levels

    Examples:
        >>> import requests
        >>> response = requests.get("/api/audit/alerts/severities")
        >>> response.json()
        {
            "severities": [
                "info",
                "warning",
                "error",
                "critical"
            ]
        }
    """
    try:
        logger.info("Fetching available alert severity levels")

        severities = [s.value for s in AlertSeverity]

        response_data = {
            "severities": severities,
        }

        logger.info(f"Retrieved {len(severities)} severity levels")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving alert severities: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alert severities: {str(e)}",
        ) from e
