"""
Audit log retention policy configuration API endpoints.

This module provides endpoints for managing the audit log retention policy,
including viewing the current retention period and updating it to comply with
organizational and regulatory requirements (e.g., SOC 2, ISO 27001, GDPR).
"""
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import yaml

from config import get_settings
from config.audit import log_config_change
from config.validation import validate_config
from models.config_change import ConfigChangeAction
from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class AuditRetentionPolicyResponse(BaseModel):
    """Response model for audit retention policy."""

    retention_days: int = Field(..., description="Current audit log retention period in days")
    environment: str = Field(..., description="Current environment")
    description: str = Field(..., description="Human-readable description of the retention period")


class AuditRetentionPolicyUpdate(BaseModel):
    """Request model for updating audit retention policy."""

    retention_days: int = Field(
        ...,
        ge=1,
        le=3650,
        description="Audit log retention period in days (90 days, 365 days/1 year, or 2555 days/7 years)"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for changing the retention policy"
    )


def _get_retention_description(days: int) -> str:
    """
    Get human-readable description for retention period.

    Args:
        days: Retention period in days

    Returns:
        Human-readable description
    """
    if days == 90:
        return "90 days (3 months) - Standard retention"
    elif days == 365:
        return "365 days (1 year) - Extended retention"
    elif days >= 2555:
        return "2555+ days (7+ years) - Long-term compliance retention"
    elif days < 90:
        return f"{days} days - Short-term retention"
    else:
        return f"{days} days - Custom retention period"


@router.get(
    "/",
    response_model=AuditRetentionPolicyResponse,
    tags=["Audit Retention"],
)
async def get_audit_retention_policy() -> JSONResponse:
    """
    Get the current audit log retention policy.

    This endpoint retrieves the current audit log retention period
    configured for the system. The retention period determines how long
    audit logs are kept before being eligible for cleanup.

    Common retention periods:
    - 90 days: Standard retention for most organizations
    - 365 days (1 year): Extended retention for compliance
    - 2555 days (7 years): Long-term retention for strict regulatory compliance

    Returns:
        JSON response with current retention period in days

    Raises:
        HTTPException(500): If configuration retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/audit/retention")
        >>> response.json()
        {
            "retention_days": 90,
            "environment": "production",
            "description": "90 days (3 months) - Standard retention"
        }
    """
    try:
        logger.info("Retrieving audit log retention policy")

        settings = get_settings()
        retention_days = settings.audit_log_retention_days
        environment = settings.environment

        response_data = {
            "retention_days": retention_days,
            "environment": environment,
            "description": _get_retention_description(retention_days),
        }

        logger.info(f"Current audit retention policy: {retention_days} days ({environment})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving audit retention policy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit retention policy: {str(e)}",
        ) from e


@router.put(
    "/",
    response_model=AuditRetentionPolicyResponse,
    tags=["Audit Retention"],
)
async def update_audit_retention_policy(
    request: AuditRetentionPolicyUpdate,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update the audit log retention policy.

    This endpoint updates the audit log retention period for the current
    environment. The change is persisted to the environment-specific
    configuration file and logged to the configuration audit trail.

    Supported retention periods:
    - 90 days: Standard retention (SOC 2 Type I)
    - 365 days (1 year): Extended retention (SOC 2 Type II)
    - 2555 days (7 years): Long-term retention (ISO 27001, financial compliance)

    Args:
        request: Request body with new retention period
        http_request: FastAPI Request object for audit context
        db: Database session

    Returns:
        JSON response with updated retention period

    Raises:
        HTTPException(400): If retention_days is invalid
        HTTPException(500): If update fails

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/audit/retention",
        ...     json={
        ...         "retention_days": 365,
        ...         "reason": "SOC 2 Type II compliance requirement"
        ...     }
        ... )
        >>> response.json()
        {
            "retention_days": 365,
            "environment": "production",
            "description": "365 days (1 year) - Extended retention"
        }
    """
    try:
        logger.info(f"Updating audit retention policy to {request.retention_days} days")

        # Get current settings
        settings = get_settings()
        old_retention_days = settings.audit_log_retention_days
        environment = settings.environment

        # Validate retention period
        if request.retention_days < 1 or request.retention_days > 3650:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid retention period: {request.retention_days}. "
                       f"Must be between 1 and 3650 days.",
            )

        # Common retention periods validation
        recommended_periods = [90, 365, 2555]
        if request.retention_days not in recommended_periods:
            logger.warning(
                f"Non-standard retention period: {request.retention_days} days. "
                f"Recommended: {recommended_periods}"
            )

        # Update the environment-specific config file
        config_file = _get_config_file_path(environment)
        await _update_config_file(config_file, "audit_log_retention_days", request.retention_days)

        # Log the configuration change to audit trail
        await log_config_change(
            db=db,
            action_type=ConfigChangeAction.VALUE_UPDATED,
            config_key="audit_log_retention_days",
            config_path="audit.retention.days",
            environment=environment,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("User-Agent"),
            before_value={"retention_days": old_retention_days},
            after_value={"retention_days": request.retention_days},
            change_reason=request.reason or "Audit retention policy updated via API",
            metadata={
                "old_description": _get_retention_description(old_retention_days),
                "new_description": _get_retention_description(request.retention_days),
            },
        )

        # Note: In production, you would typically reload the settings here
        # For now, we'll return the new value but the change requires app restart
        # to take full effect in the running application

        response_data = {
            "retention_days": request.retention_days,
            "environment": environment,
            "description": _get_retention_description(request.retention_days),
        }

        logger.info(
            f"Successfully updated audit retention policy from {old_retention_days} "
            f"to {request.retention_days} days"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating audit retention policy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update audit retention policy: {str(e)}",
        ) from e


def _get_config_file_path(environment: str) -> str:
    """
    Get the path to the environment-specific config file.

    Args:
        environment: Environment name (development, staging, production)

    Returns:
        Absolute path to the config file
    """
    # Determine config file name based on environment
    config_filename = f"config.{environment}.yml"

    # Get backend directory path
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(backend_dir, "config")
    config_file = os.path.join(config_dir, config_filename)

    return config_file


async def _update_config_file(file_path: str, key: str, value: any) -> None:
    """
    Update a configuration value in a YAML file.

    Args:
        file_path: Path to the YAML config file
        key: Configuration key to update
        value: New value for the configuration key

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
        IOError: If file write fails
    """
    try:
        # Read current config
        if not os.path.exists(file_path):
            logger.warning(f"Config file not found: {file_path}, creating new file")
            config_data = {}
        else:
            with open(file_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}

        # Update the value
        config_data[key] = value

        # Write back to file
        with open(file_path, 'w') as f:
            yaml.dump(
                config_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        logger.info(f"Updated {key}={value} in {file_path}")

    except Exception as e:
        logger.error(f"Failed to update config file {file_path}: {e}", exc_info=True)
        raise
