"""
Training pipeline status and metrics endpoints for ML models.

This module provides endpoints for monitoring ML model training pipeline status,
including retrieving training event metrics, pipeline health, and retraining history.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.model_training_event import ModelTrainingEvent
from models.retraining_config import RetrainingConfig

logger = logging.getLogger(__name__)

router = APIRouter()


class TrainingPipelineStatus(BaseModel):
    """Training pipeline status for a model."""

    model_name: str = Field(..., description="Name of the model")
    latest_version: Optional[str] = Field(None, description="Latest trained version")
    training_status: Optional[str] = Field(None, description="Current training status (pending, in_progress, completed, failed)")
    last_training_at: Optional[str] = Field(None, description="Timestamp of last training run")
    last_training_duration: Optional[float] = Field(None, description="Duration of last training run in seconds")
    last_training_metrics: Optional[dict] = Field(None, description="Metrics from last training run")
    is_healthy: bool = Field(..., description="Whether the training pipeline is healthy")
    error_message: Optional[str] = Field(None, description="Error message if training failed")


class TrainingMetrics(BaseModel):
    """Individual training metrics entry."""

    id: str = Field(..., description="Training event ID")
    model_name: str = Field(..., description="Name of the model")
    version: str = Field(..., description="Version identifier")
    training_status: str = Field(..., description="Status of the training run")
    training_duration: Optional[float] = Field(None, description="Duration of training in seconds")
    training_metrics: Optional[dict] = Field(None, description="Training metrics (loss, accuracy, etc.)")
    dataset_info: Optional[dict] = Field(None, description="Dataset information (size, splits, etc.)")
    started_at: Optional[str] = Field(None, description="Timestamp when training started")
    completed_at: Optional[str] = Field(None, description="Timestamp when training completed")
    created_at: str = Field(..., description="Timestamp when training event was created")


class TrainingMetricsListResponse(BaseModel):
    """Response model for training metrics list."""

    metrics: List[TrainingMetrics] = Field(..., description="List of training metrics")
    total_count: int = Field(..., description="Total number of training events")


class PipelineHealthSummary(BaseModel):
    """Summary of overall training pipeline health."""

    total_models: int = Field(..., description="Total number of models tracked")
    active_trainings: int = Field(..., description="Number of currently active training runs")
    failed_trainings: int = Field(..., description="Number of failed training runs in last 24 hours")
    completed_trainings: int = Field(..., description="Number of completed training runs in last 24 hours")
    overall_health: str = Field(..., description="Overall pipeline health status (healthy, degraded, unhealthy)")


class TrainingHistoryEntry(BaseModel):
    """Single entry in training history."""

    date: str = Field(..., description="Date of the training run (ISO 8601 format)")
    model_name: str = Field(..., description="Name of the model")
    version: str = Field(..., description="Version identifier")
    status: str = Field(..., description="Training status")
    duration_seconds: Optional[float] = Field(None, description="Training duration in seconds")
    f1_score: Optional[float] = Field(None, description="F1 score achieved")
    accuracy: Optional[float] = Field(None, description="Accuracy achieved")


class TrainingHistoryResponse(BaseModel):
    """Response model for training history timeline."""

    model_name: str = Field(..., description="Name of the model")
    period_days: int = Field(..., description="Number of days covered by the history")
    history: List[TrainingHistoryEntry] = Field(..., description="Timeline of training events")
    total_entries: int = Field(..., description="Total number of history entries")


class RetrainingPauseRequest(BaseModel):
    """Request model for pausing automated retraining."""

    model_name: str = Field(
        default="global",
        description="Name of the model to pause (default: 'global' for all models)"
    )
    reason: Optional[str] = Field(None, description="Reason for pausing")


class RetrainingResumeRequest(BaseModel):
    """Request model for resuming automated retraining."""

    model_name: str = Field(
        default="global",
        description="Name of the model to resume (default: 'global' for all models)"
    )


class RetrainingConfigResponse(BaseModel):
    """Response model for retraining configuration status."""

    id: str = Field(..., description="Config entry ID")
    model_name: str = Field(..., description="Name of the model")
    paused: bool = Field(..., description="Whether retraining is paused")
    pause_reason: Optional[str] = Field(None, description="Reason for pause")
    paused_by: Optional[str] = Field(None, description="User who paused")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


@router.get(
    "/status",
    response_model=TrainingPipelineStatus,
    tags=["Training Pipeline"],
)
async def get_training_pipeline_status(
    model_name: str = Query(..., description="Model name to get status for"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get training pipeline status for a specific model.

    This endpoint retrieves the current status of the training pipeline for a specified
    model, including the latest training event, its status, and health indicators.

    Args:
        model_name: Name of the model to get status for
        db: Database session

    Returns:
        JSON response with training pipeline status

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/training-pipeline/status?model_name=skill_matching")
        >>> response.json()
        {
            "model_name": "skill_matching",
            "latest_version": "v1.2.0",
            "training_status": "completed",
            "last_training_at": "2024-01-25T10:30:00Z",
            "last_training_duration": 245.5,
            "last_training_metrics": {"f1_score": 0.85, "accuracy": 0.82},
            "is_healthy": true,
            "error_message": null
        }
    """
    try:
        logger.info(f"Fetching training pipeline status for model: {model_name}")

        # Validate model name
        if not model_name or len(model_name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Model name cannot be empty",
            )

        # Get the latest training event for this model
        query = select(ModelTrainingEvent).where(
            ModelTrainingEvent.model_name == model_name
        ).order_by(ModelTrainingEvent.created_at.desc()).limit(1)

        result = await db.execute(query)
        latest_event = result.scalar_one_or_none()

        if not latest_event:
            # No training events found - return empty status
            response_data = {
                "model_name": model_name,
                "latest_version": None,
                "training_status": None,
                "last_training_at": None,
                "last_training_duration": None,
                "last_training_metrics": None,
                "is_healthy": True,  # No events is considered healthy
                "error_message": None,
            }

            logger.info(f"No training events found for model: {model_name}")

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_data,
            )

        # Determine health based on status
        is_healthy = latest_event.training_status in ["completed", "pending"]
        if latest_event.training_status == "failed":
            is_healthy = False

        response_data = {
            "model_name": latest_event.model_name,
            "latest_version": latest_event.version,
            "training_status": latest_event.training_status,
            "last_training_at": latest_event.completed_at or latest_event.started_at,
            "last_training_duration": float(latest_event.training_duration) if latest_event.training_duration is not None else None,
            "last_training_metrics": latest_event.training_metrics,
            "is_healthy": is_healthy,
            "error_message": latest_event.error_message,
        }

        logger.info(
            f"Retrieved training status for model: {model_name}, "
            f"status: {latest_event.training_status}, healthy: {is_healthy}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching training pipeline status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch training pipeline status: {str(e)}",
        ) from e


@router.get(
    "/metrics",
    response_model=TrainingMetricsListResponse,
    tags=["Training Pipeline"],
)
async def get_training_metrics(
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    training_status: Optional[str] = Query(None, description="Filter by training status (pending, in_progress, completed, failed)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get training metrics for ML models.

    This endpoint retrieves training metrics from the model_training_events table,
    supporting filtering by model name and training status. Returns metrics in
    reverse chronological order (most recent first).

    Args:
        model_name: Optional filter for specific model name
        training_status: Optional filter for training status
        limit: Maximum number of records to return (default: 100, max: 1000)
        db: Database session

    Returns:
        JSON response with list of training metrics

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/training-pipeline/metrics?model_name=ranking")
        >>> response.json()
        {
            "metrics": [...],
            "total_count": 50
        }
    """
    try:
        logger.info(
            f"Fetching training metrics - model_name: {model_name}, "
            f"training_status: {training_status}"
        )

        # Build base query
        query = select(ModelTrainingEvent)

        # Apply filters if provided
        if model_name:
            query = query.where(ModelTrainingEvent.model_name == model_name)
        if training_status:
            query = query.where(ModelTrainingEvent.training_status == training_status)

        # Get total count
        count_query = select(func.count()).select_from(ModelTrainingEvent)
        if model_name:
            count_query = count_query.where(ModelTrainingEvent.model_name == model_name)
        if training_status:
            count_query = count_query.where(ModelTrainingEvent.training_status == training_status)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Order by most recently created and apply limit
        query = query.order_by(ModelTrainingEvent.created_at.desc()).limit(limit)

        # Execute query
        result = await db.execute(query)
        training_events = result.scalars().all()

        # Convert to response format
        metrics_list = []
        for event in training_events:
            metrics_list.append({
                "id": str(event.id),
                "model_name": event.model_name,
                "version": event.version,
                "training_status": event.training_status,
                "training_duration": float(event.training_duration) if event.training_duration is not None else None,
                "training_metrics": event.training_metrics,
                "dataset_info": event.dataset_info,
                "started_at": event.started_at,
                "completed_at": event.completed_at,
                "created_at": event.created_at.isoformat() if event.created_at else None,
            })

        response_data = {
            "metrics": metrics_list,
            "total_count": total,
        }

        logger.info(f"Retrieved {len(metrics_list)} training metrics (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error fetching training metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch training metrics: {str(e)}",
        ) from e


@router.get(
    "/health",
    response_model=PipelineHealthSummary,
    tags=["Training Pipeline"],
)
async def get_pipeline_health(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get overall training pipeline health summary.

    This endpoint provides a high-level summary of the training pipeline health,
    including the number of active, failed, and completed training runs.

    Returns:
        JSON response with pipeline health summary

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/training-pipeline/health")
        >>> response.json()
        {
            "total_models": 5,
            "active_trainings": 2,
            "failed_trainings": 0,
            "completed_trainings": 15,
            "overall_health": "healthy"
        }
    """
    try:
        logger.info("Fetching training pipeline health summary")

        from datetime import datetime, timedelta

        # Get distinct model count
        model_query = select(func.count(ModelTrainingEvent.model_name.distinct()))
        model_result = await db.execute(model_query)
        total_models = model_result.scalar() or 0

        # Get active training count (in_progress status)
        active_query = select(func.count()).where(
            ModelTrainingEvent.training_status == "in_progress"
        )
        active_result = await db.execute(active_query)
        active_trainings = active_result.scalar() or 0

        # Calculate time threshold for last 24 hours
        time_threshold = datetime.utcnow() - timedelta(hours=24)

        # Get failed training count in last 24 hours
        failed_query = select(func.count()).where(
            ModelTrainingEvent.training_status == "failed",
            ModelTrainingEvent.created_at >= time_threshold
        )
        failed_result = await db.execute(failed_query)
        failed_trainings = failed_result.scalar() or 0

        # Get completed training count in last 24 hours
        completed_query = select(func.count()).where(
            ModelTrainingEvent.training_status == "completed",
            ModelTrainingEvent.created_at >= time_threshold
        )
        completed_result = await db.execute(completed_query)
        completed_trainings = completed_result.scalar() or 0

        # Determine overall health
        if failed_trainings > 0:
            overall_health = "unhealthy"
        elif active_trainings > 5:  # Arbitrary threshold for "degraded"
            overall_health = "degraded"
        else:
            overall_health = "healthy"

        response_data = {
            "total_models": total_models,
            "active_trainings": active_trainings,
            "failed_trainings": failed_trainings,
            "completed_trainings": completed_trainings,
            "overall_health": overall_health,
        }

        logger.info(
            f"Pipeline health - models: {total_models}, active: {active_trainings}, "
            f"failed: {failed_trainings}, completed: {completed_trainings}, "
            f"overall: {overall_health}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error fetching pipeline health: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pipeline health: {str(e)}",
        ) from e


@router.get(
    "/history",
    response_model=TrainingHistoryResponse,
    tags=["Training Pipeline"],
)
async def get_training_history(
    model_name: str = Query(..., description="Model name to retrieve history for"),
    days: int = Query(30, ge=1, le=365, description="Number of days of history to retrieve (default: 30, max: 365)"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get training history timeline for a model.

    This endpoint retrieves a chronological timeline of training events for a specific model
    over a specified time period. Useful for visualizing model training patterns and
    identifying trends or issues over time.

    Args:
        model_name: Name of the model to retrieve history for
        days: Number of days of history to retrieve (default: 30, max: 365)
        db: Database session

    Returns:
        JSON response with training history timeline

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/training-pipeline/history?model_name=ranking&days=30"
        ... )
        >>> response.json()
        {
            "model_name": "ranking",
            "period_days": 30,
            "history": [
                {
                    "date": "2024-01-01T00:00:00Z",
                    "model_name": "ranking",
                    "version": "v2.1.0",
                    "status": "completed",
                    "duration_seconds": 245.5,
                    "f1_score": 0.85,
                    "accuracy": 0.82
                }
            ],
            "total_entries": 15
        }
    """
    try:
        logger.info(
            f"Fetching training history - model_name: {model_name}, days: {days}"
        )

        # Validate model name
        if not model_name or len(model_name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Model name cannot be empty",
            )

        from datetime import datetime, timedelta

        # Calculate the date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        logger.info(
            f"History date range: {start_date.isoformat()} to {end_date.isoformat()}"
        )

        # Build query for training events within date range
        query = select(ModelTrainingEvent).where(
            ModelTrainingEvent.model_name == model_name,
            ModelTrainingEvent.created_at >= start_date
        ).order_by(ModelTrainingEvent.created_at.asc())

        result = await db.execute(query)
        training_events = result.scalars().all()

        # Convert to history format
        history_list = []
        for event in training_events:
            # Extract metrics from training_metrics JSON
            metrics = event.training_metrics or {}
            f1_score = metrics.get("f1_score")
            accuracy = metrics.get("accuracy")

            history_list.append({
                "date": event.created_at.isoformat() if event.created_at else None,
                "model_name": event.model_name,
                "version": event.version,
                "status": event.training_status,
                "duration_seconds": float(event.training_duration) if event.training_duration is not None else None,
                "f1_score": float(f1_score) if f1_score is not None else None,
                "accuracy": float(accuracy) if accuracy is not None else None,
            })

        response_data = {
            "model_name": model_name,
            "period_days": days,
            "history": history_list,
            "total_entries": len(history_list),
        }

        logger.info(
            f"Retrieved {len(history_list)} history entries "
            f"for model {model_name} over {days} days"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching training history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch training history: {str(e)}",
        ) from e


@router.get(
    "/config/pause-status",
    response_model=RetrainingConfigResponse,
    tags=["Training Pipeline"],
)
async def get_pause_status(
    model_name: str = Query(
        "global",
        description="Model name to check pause status for (default: 'global')"
    ),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get the pause status for automated retraining.

    This endpoint retrieves the current pause status for automated retraining,
    either globally or for a specific model.

    Args:
        model_name: Model name to check (default: 'global')
        db: Database session

    Returns:
        JSON response with pause status

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/training-pipeline/config/pause-status"
        ... )
        >>> response.json()
        {
            "id": "123",
            "model_name": "global",
            "paused": false,
            "pause_reason": null,
            "paused_by": null,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    """
    try:
        logger.info(f"Fetching pause status for model: {model_name}")

        # Try to get existing config
        query = select(RetrainingConfig).where(
            RetrainingConfig.model_name == model_name
        )
        result = await db.execute(query)
        config = result.scalar_one_or_none()

        # If no config exists, create a default one (not paused)
        if not config:
            config = RetrainingConfig(
                model_name=model_name,
                paused=False,
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)

        response_data = {
            "id": str(config.id),
            "model_name": config.model_name,
            "paused": config.paused,
            "pause_reason": config.pause_reason,
            "paused_by": config.paused_by,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        }

        logger.info(
            f"Pause status for {model_name}: paused={config.paused}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error fetching pause status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pause status: {str(e)}",
        ) from e


@router.post("/config/pause", tags=["Training Pipeline"])
async def pause_retraining(
    pause_data: RetrainingPauseRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Pause automated retraining.

    This endpoint pauses automated retraining, either globally or for a specific model.
    Paused models will not trigger automatic retraining until resumed.

    Args:
        pause_data: Pause request with model name and optional reason
        db: Database session

    Returns:
        JSON response confirming pause operation

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "model_name": "global",
        ...     "reason": "Investigating performance issue"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/training-pipeline/config/pause",
        ...     json=data
        ... )
        >>> response.json()
        {
            "message": "Automated retraining paused",
            "model_name": "global",
            "paused": true
        }
    """
    try:
        logger.info(f"Pausing retraining for model: {pause_data.model_name}")

        # Try to get existing config
        query = select(RetrainingConfig).where(
            RetrainingConfig.model_name == pause_data.model_name
        )
        result = await db.execute(query)
        config = result.scalar_one_or_none()

        if config:
            # Update existing config
            config.paused = True
            config.pause_reason = pause_data.reason
            config.paused_by = "admin"  # Could be extracted from auth context
        else:
            # Create new config
            config = RetrainingConfig(
                model_name=pause_data.model_name,
                paused=True,
                pause_reason=pause_data.reason,
                paused_by="admin",
            )
            db.add(config)

        await db.commit()
        await db.refresh(config)

        response_data = {
            "message": "Automated retraining paused",
            "model_name": config.model_name,
            "paused": True,
        }

        logger.info(
            f"Retraining paused for {config.model_name}, "
            f"reason: {pause_data.reason or 'No reason provided'}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error pausing retraining: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause retraining: {str(e)}",
        ) from e


@router.post("/config/resume", tags=["Training Pipeline"])
async def resume_retraining(
    resume_data: RetrainingResumeRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Resume automated retraining.

    This endpoint resumes automated retraining that was previously paused,
    either globally or for a specific model.

    Args:
        resume_data: Resume request with model name
        db: Database session

    Returns:
        JSON response confirming resume operation

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"model_name": "global"}
        >>> response = requests.post(
        ...     "http://localhost:8000/api/training-pipeline/config/resume",
        ...     json=data
        ... )
        >>> response.json()
        {
            "message": "Automated retraining resumed",
            "model_name": "global",
            "paused": false
        }
    """
    try:
        logger.info(f"Resuming retraining for model: {resume_data.model_name}")

        # Try to get existing config
        query = select(RetrainingConfig).where(
            RetrainingConfig.model_name == resume_data.model_name
        )
        result = await db.execute(query)
        config = result.scalar_one_or_none()

        if config:
            # Update existing config
            config.paused = False
            config.pause_reason = None
            config.paused_by = None
        else:
            # Create new config (not paused)
            config = RetrainingConfig(
                model_name=resume_data.model_name,
                paused=False,
            )
            db.add(config)

        await db.commit()
        await db.refresh(config)

        response_data = {
            "message": "Automated retraining resumed",
            "model_name": config.model_name,
            "paused": False,
        }

        logger.info(f"Retraining resumed for {config.model_name}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error resuming retraining: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume retraining: {str(e)}",
        ) from e
