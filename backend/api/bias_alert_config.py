"""
Bias Alert Configuration endpoints for managing bias detection alert thresholds.

This module provides endpoints for creating, retrieving, updating, and deleting
bias alert configuration settings that control when and how bias detection alerts
are triggered and delivered.
"""
import logging
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, select

logger = logging.getLogger(__name__)

router = APIRouter()


class BiasAlertConfigCreate(BaseModel):
    """Request model for creating a new bias alert configuration."""

    organization_id: Optional[UUID] = Field(None, description="Organization ID (null for system-wide)")
    alert_type: str = Field(..., description="Type of bias metric (disparate_impact, statistical_parity, sample_size)")
    metric_name: str = Field(..., description="Human-readable name of the metric")
    threshold_value: float = Field(..., description="Threshold value that triggers an alert", ge=0, le=1)
    comparison_operator: str = Field("less_than", description="Operator for threshold comparison")
    severity_level: str = Field("medium", description="Severity level (low, medium, high, critical)")
    is_enabled: bool = Field(True, description="Whether this alert configuration is active")
    notification_enabled: bool = Field(True, description="Whether to send notifications")
    notification_recipients: Optional[List[str]] = Field(None, description="Email addresses or user IDs to notify")
    demographic_groups: Optional[List[str]] = Field(None, description="Demographic groups this applies to")
    applies_to_vacancies: Optional[List[str]] = Field(None, description="Vacancy IDs this applies to")
    alert_frequency: str = Field("immediate", description="Alert frequency (immediate, daily, weekly)")
    cooldown_period_hours: Optional[int] = Field(24, description="Hours before re-triggering same alert")
    auto_acknowledge: bool = Field(False, description="Whether to auto-acknowledge alerts")
    description: Optional[str] = Field(None, description="Description of this alert configuration")
    mitigation_recommendations: Optional[str] = Field(None, description="Suggested actions when alert is triggered")
    custom_message_template: Optional[str] = Field(None, description="Custom message template for notifications")
    metadata: Optional[Dict] = Field(None, description="Additional configuration options")


class BiasAlertConfigUpdate(BaseModel):
    """Request model for updating an existing bias alert configuration."""

    alert_type: Optional[str] = Field(None, description="Type of bias metric")
    metric_name: Optional[str] = Field(None, description="Human-readable name of the metric")
    threshold_value: Optional[float] = Field(None, description="Threshold value that triggers an alert", ge=0, le=1)
    comparison_operator: Optional[str] = Field(None, description="Operator for threshold comparison")
    severity_level: Optional[str] = Field(None, description="Severity level")
    is_enabled: Optional[bool] = Field(None, description="Whether this alert configuration is active")
    notification_enabled: Optional[bool] = Field(None, description="Whether to send notifications")
    notification_recipients: Optional[List[str]] = Field(None, description="Email addresses or user IDs to notify")
    demographic_groups: Optional[List[str]] = Field(None, description="Demographic groups this applies to")
    applies_to_vacancies: Optional[List[str]] = Field(None, description="Vacancy IDs this applies to")
    alert_frequency: Optional[str] = Field(None, description="Alert frequency")
    cooldown_period_hours: Optional[int] = Field(None, description="Hours before re-triggering same alert")
    auto_acknowledge: Optional[bool] = Field(None, description="Whether to auto-acknowledge alerts")
    description: Optional[str] = Field(None, description="Description of this alert configuration")
    mitigation_recommendations: Optional[str] = Field(None, description="Suggested actions when alert is triggered")
    custom_message_template: Optional[str] = Field(None, description="Custom message template for notifications")
    metadata: Optional[Dict] = Field(None, description="Additional configuration options")


class BiasAlertConfigResponse(BaseModel):
    """Response model for bias alert configuration."""

    id: str = Field(..., description="Configuration ID")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    alert_type: str = Field(..., description="Type of bias metric")
    metric_name: str = Field(..., description="Human-readable name of the metric")
    threshold_value: float = Field(..., description="Threshold value that triggers an alert")
    comparison_operator: str = Field(..., description="Operator for threshold comparison")
    severity_level: str = Field(..., description="Severity level")
    is_enabled: bool = Field(..., description="Whether this alert configuration is active")
    notification_enabled: bool = Field(..., description="Whether to send notifications")
    notification_recipients: Optional[List[str]] = Field(None, description="Email addresses or user IDs to notify")
    demographic_groups: Optional[List[str]] = Field(None, description="Demographic groups this applies to")
    applies_to_vacancies: Optional[List[str]] = Field(None, description="Vacancy IDs this applies to")
    alert_frequency: str = Field(..., description="Alert frequency")
    cooldown_period_hours: Optional[int] = Field(None, description="Hours before re-triggering same alert")
    auto_acknowledge: bool = Field(..., description="Whether to auto-acknowledge alerts")
    description: Optional[str] = Field(None, description="Description of this alert configuration")
    mitigation_recommendations: Optional[str] = Field(None, description="Suggested actions when alert is triggered")
    custom_message_template: Optional[str] = Field(None, description="Custom message template for notifications")
    metadata: Optional[Dict] = Field(None, description="Additional configuration options")
    created_at: str = Field(..., description="Timestamp when configuration was created (ISO 8601 format)")
    updated_at: str = Field(..., description="Timestamp when configuration was last updated (ISO 8601 format)")


class BiasAlertConfigListResponse(BaseModel):
    """Response model for list of bias alert configurations."""

    configs: List[BiasAlertConfigResponse] = Field(..., description="List of bias alert configurations")
    total_count: int = Field(..., description="Total number of configurations")


@router.get(
    "",
    response_model=BiasAlertConfigListResponse,
    tags=["Bias Alert Configuration"],
)
async def list_bias_alert_configs(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
) -> JSONResponse:
    """
    Get list of bias alert configurations.

    This endpoint retrieves bias alert configurations from the bias_alert_configs table,
    supporting filtering by organization, alert type, and enabled status.
    Returns configurations in reverse chronological order (most recent first).

    Args:
        organization_id: Optional filter for specific organization
        alert_type: Optional filter for alert type
        is_enabled: Optional filter for enabled status
        limit: Maximum number of records to return (default: 100, max: 1000)

    Returns:
        JSON response with list of bias alert configurations

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/bias-alert-config?alert_type=disparate_impact")
        >>> response.json()
        {
            "configs": [...],
            "total_count": 10
        }
    """
    try:
        logger.info(
            f"Fetching bias alert configurations - organization_id: {organization_id}, "
            f"alert_type: {alert_type}, is_enabled: {is_enabled}"
        )

        from database import get_db
        from models.bias_alert_config import BiasAlertConfig

        configs_list = []
        total_count = 0

        async for db in get_db():
            # Build query
            query = select(BiasAlertConfig)

            # Apply filters
            if organization_id:
                query = query.where(BiasAlertConfig.organization_id == organization_id)

            if alert_type:
                query = query.where(BiasAlertConfig.alert_type == alert_type)

            if is_enabled is not None:
                query = query.where(BiasAlertConfig.is_enabled == is_enabled)

            # Order by created_at descending (most recent first)
            query = query.order_by(desc(BiasAlertConfig.created_at))

            # Get total count
            from sqlalchemy import func
            count_query = select(func.count()).select_from(BiasAlertConfig)
            if organization_id:
                count_query = count_query.where(BiasAlertConfig.organization_id == organization_id)
            if alert_type:
                count_query = count_query.where(BiasAlertConfig.alert_type == alert_type)
            if is_enabled is not None:
                count_query = count_query.where(BiasAlertConfig.is_enabled == is_enabled)

            count_result = await db.execute(count_query)
            total_count = count_result.scalar() or 0

            # Apply limit
            query = query.limit(limit)

            # Execute query
            result = await db.execute(query)
            config_records = result.scalars().all()

            # Transform database records to API response format
            for record in config_records:
                configs_list.append(
                    BiasAlertConfigResponse(
                        id=str(record.id),
                        organization_id=str(record.organization_id) if record.organization_id else None,
                        alert_type=record.alert_type,
                        metric_name=record.metric_name,
                        threshold_value=float(record.threshold_value),
                        comparison_operator=record.comparison_operator,
                        severity_level=record.severity_level,
                        is_enabled=record.is_enabled,
                        notification_enabled=record.notification_enabled,
                        notification_recipients=record.notification_recipients if record.notification_recipients else None,
                        demographic_groups=record.demographic_groups if record.demographic_groups else None,
                        applies_to_vacancies=record.applies_to_vacancies if record.applies_to_vacancies else None,
                        alert_frequency=record.alert_frequency,
                        cooldown_period_hours=record.cooldown_period_hours,
                        auto_acknowledge=record.auto_acknowledge,
                        description=record.description,
                        mitigation_recommendations=record.mitigation_recommendations,
                        custom_message_template=record.custom_message_template,
                        metadata=record.metadata if record.metadata else None,
                        created_at=record.created_at.isoformat(),
                        updated_at=record.updated_at.isoformat(),
                    )
                )

        response_data = BiasAlertConfigListResponse(
            configs=configs_list,
            total_count=total_count,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except Exception as e:
        logger.error(f"Error fetching bias alert configurations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch bias alert configurations: {str(e)}",
        )


@router.get(
    "/{config_id}",
    response_model=BiasAlertConfigResponse,
    tags=["Bias Alert Configuration"],
)
async def get_bias_alert_config(
    config_id: UUID,
) -> JSONResponse:
    """
    Get a specific bias alert configuration by ID.

    Args:
        config_id: UUID of the configuration to retrieve

    Returns:
        JSON response with the bias alert configuration

    Raises:
        HTTPException(404): If configuration not found
        HTTPException(500): If database query fails
    """
    try:
        logger.info(f"Fetching bias alert configuration: {config_id}")

        from database import get_db
        from models.bias_alert_config import BiasAlertConfig

        async for db in get_db():
            query = select(BiasAlertConfig).where(BiasAlertConfig.id == config_id)
            result = await db.execute(query)
            config = result.scalar_one_or_none()

            if not config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bias alert configuration {config_id} not found",
                )

            response_data = BiasAlertConfigResponse(
                id=str(config.id),
                organization_id=str(config.organization_id) if config.organization_id else None,
                alert_type=config.alert_type,
                metric_name=config.metric_name,
                threshold_value=float(config.threshold_value),
                comparison_operator=config.comparison_operator,
                severity_level=config.severity_level,
                is_enabled=config.is_enabled,
                notification_enabled=config.notification_enabled,
                notification_recipients=config.notification_recipients if config.notification_recipients else None,
                demographic_groups=config.demographic_groups if config.demographic_groups else None,
                applies_to_vacancies=config.applies_to_vacancies if config.applies_to_vacancies else None,
                alert_frequency=config.alert_frequency,
                cooldown_period_hours=config.cooldown_period_hours,
                auto_acknowledge=config.auto_acknowledge,
                description=config.description,
                mitigation_recommendations=config.mitigation_recommendations,
                custom_message_template=config.custom_message_template,
                metadata=config.metadata if config.metadata else None,
                created_at=config.created_at.isoformat(),
                updated_at=config.updated_at.isoformat(),
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_data.model_dump(),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bias alert configuration {config_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch bias alert configuration: {str(e)}",
        )


@router.post(
    "",
    response_model=BiasAlertConfigResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Bias Alert Configuration"],
)
async def create_bias_alert_config(
    config_data: BiasAlertConfigCreate,
) -> JSONResponse:
    """
    Create a new bias alert configuration.

    Args:
        config_data: Configuration data for the new alert

    Returns:
        JSON response with the created bias alert configuration

    Raises:
        HTTPException(400): If validation fails
        HTTPException(500): If database operation fails
    """
    try:
        logger.info(f"Creating bias alert configuration: {config_data.alert_type}")

        from database import get_db
        from models.bias_alert_config import BiasAlertConfig

        async for db in get_db():
            # Create new configuration
            new_config = BiasAlertConfig(
                organization_id=config_data.organization_id,
                alert_type=config_data.alert_type,
                metric_name=config_data.metric_name,
                threshold_value=config_data.threshold_value,
                comparison_operator=config_data.comparison_operator,
                severity_level=config_data.severity_level,
                is_enabled=config_data.is_enabled,
                notification_enabled=config_data.notification_enabled,
                notification_recipients=config_data.notification_recipients,
                demographic_groups=config_data.demographic_groups,
                applies_to_vacancies=config_data.applies_to_vacancies,
                alert_frequency=config_data.alert_frequency,
                cooldown_period_hours=config_data.cooldown_period_hours,
                auto_acknowledge=config_data.auto_acknowledge,
                description=config_data.description,
                mitigation_recommendations=config_data.mitigation_recommendations,
                custom_message_template=config_data.custom_message_template,
                metadata=config_data.metadata,
            )

            db.add(new_config)
            await db.commit()
            await db.refresh(new_config)

            response_data = BiasAlertConfigResponse(
                id=str(new_config.id),
                organization_id=str(new_config.organization_id) if new_config.organization_id else None,
                alert_type=new_config.alert_type,
                metric_name=new_config.metric_name,
                threshold_value=float(new_config.threshold_value),
                comparison_operator=new_config.comparison_operator,
                severity_level=new_config.severity_level,
                is_enabled=new_config.is_enabled,
                notification_enabled=new_config.notification_enabled,
                notification_recipients=new_config.notification_recipients if new_config.notification_recipients else None,
                demographic_groups=new_config.demographic_groups if new_config.demographic_groups else None,
                applies_to_vacancies=new_config.applies_to_vacancies if new_config.applies_to_vacancies else None,
                alert_frequency=new_config.alert_frequency,
                cooldown_period_hours=new_config.cooldown_period_hours,
                auto_acknowledge=new_config.auto_acknowledge,
                description=new_config.description,
                mitigation_recommendations=new_config.mitigation_recommendations,
                custom_message_template=new_config.custom_message_template,
                metadata=new_config.metadata if new_config.metadata else None,
                created_at=new_config.created_at.isoformat(),
                updated_at=new_config.updated_at.isoformat(),
            )

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=response_data.model_dump(),
            )

    except Exception as e:
        logger.error(f"Error creating bias alert configuration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bias alert configuration: {str(e)}",
        )


@router.put(
    "/{config_id}",
    response_model=BiasAlertConfigResponse,
    tags=["Bias Alert Configuration"],
)
async def update_bias_alert_config(
    config_id: UUID,
    config_data: BiasAlertConfigUpdate,
) -> JSONResponse:
    """
    Update an existing bias alert configuration.

    Args:
        config_id: UUID of the configuration to update
        config_data: Updated configuration data

    Returns:
        JSON response with the updated bias alert configuration

    Raises:
        HTTPException(404): If configuration not found
        HTTPException(500): If database operation fails
    """
    try:
        logger.info(f"Updating bias alert configuration: {config_id}")

        from database import get_db
        from models.bias_alert_config import BiasAlertConfig

        async for db in get_db():
            query = select(BiasAlertConfig).where(BiasAlertConfig.id == config_id)
            result = await db.execute(query)
            config = result.scalar_one_or_none()

            if not config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bias alert configuration {config_id} not found",
                )

            # Update only provided fields
            update_data = config_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(config, field, value)

            await db.commit()
            await db.refresh(config)

            response_data = BiasAlertConfigResponse(
                id=str(config.id),
                organization_id=str(config.organization_id) if config.organization_id else None,
                alert_type=config.alert_type,
                metric_name=config.metric_name,
                threshold_value=float(config.threshold_value),
                comparison_operator=config.comparison_operator,
                severity_level=config.severity_level,
                is_enabled=config.is_enabled,
                notification_enabled=config.notification_enabled,
                notification_recipients=config.notification_recipients if config.notification_recipients else None,
                demographic_groups=config.demographic_groups if config.demographic_groups else None,
                applies_to_vacancies=config.applies_to_vacancies if config.applies_to_vacancies else None,
                alert_frequency=config.alert_frequency,
                cooldown_period_hours=config.cooldown_period_hours,
                auto_acknowledge=config.auto_acknowledge,
                description=config.description,
                mitigation_recommendations=config.mitigation_recommendations,
                custom_message_template=config.custom_message_template,
                metadata=config.metadata if config.metadata else None,
                created_at=config.created_at.isoformat(),
                updated_at=config.updated_at.isoformat(),
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_data.model_dump(),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bias alert configuration {config_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update bias alert configuration: {str(e)}",
        )


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Bias Alert Configuration"],
)
async def delete_bias_alert_config(
    config_id: UUID,
) -> None:
    """
    Delete a bias alert configuration.

    Args:
        config_id: UUID of the configuration to delete

    Returns:
        No content (204)

    Raises:
        HTTPException(404): If configuration not found
        HTTPException(500): If database operation fails
    """
    try:
        logger.info(f"Deleting bias alert configuration: {config_id}")

        from database import get_db
        from models.bias_alert_config import BiasAlertConfig

        async for db in get_db():
            query = select(BiasAlertConfig).where(BiasAlertConfig.id == config_id)
            result = await db.execute(query)
            config = result.scalar_one_or_none()

            if not config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bias alert configuration {config_id} not found",
                )

            await db.delete(config)
            await db.commit()

            return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bias alert configuration {config_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete bias alert configuration: {str(e)}",
        )
