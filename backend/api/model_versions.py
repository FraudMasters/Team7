"""
ML model version management endpoints.

This module provides endpoints for managing machine learning model versions,
including CRUD operations for creating, reading, updating, and deleting model
version entries with A/B testing support and performance metrics.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.ml_model_version import MLModelVersion
from models.model_performance_snapshot import ModelPerformanceSnapshot

logger = logging.getLogger(__name__)

router = APIRouter()


class ModelVersionEntry(BaseModel):
    """Individual model version definition."""

    model_name: str = Field(..., description="Name of the model (e.g., skill_matching, resume_parser)")
    version: str = Field(..., description="Version identifier (e.g., v1.0.0, v2.1.3)")
    is_active: bool = Field(False, description="Whether this model version is currently active")
    is_experiment: bool = Field(False, description="Whether this is an experimental model for A/B testing")
    experiment_config: Optional[dict] = Field(None, description="A/B testing configuration (traffic_percentage, etc.)")
    model_metadata: Optional[dict] = Field(None, description="Model training metadata (algorithm, training_date, etc.)")
    accuracy_metrics: Optional[dict] = Field(None, description="Accuracy metrics (precision, recall, f1_score, etc.)")
    file_path: Optional[str] = Field(None, description="Path to the model file in storage")
    performance_score: Optional[float] = Field(None, description="Overall performance score (0-100)", ge=0, le=100)


class ModelVersionCreate(BaseModel):
    """Request model for creating model versions."""

    models: List[ModelVersionEntry] = Field(..., description="List of model version entries to create")


class ModelVersionUpdate(BaseModel):
    """Request model for updating a model version."""

    version: Optional[str] = Field(None, description="Version identifier")
    is_active: Optional[bool] = Field(None, description="Whether this model version is active")
    is_experiment: Optional[bool] = Field(None, description="Whether this is an experimental model")
    experiment_config: Optional[dict] = Field(None, description="A/B testing configuration")
    model_metadata: Optional[dict] = Field(None, description="Model training metadata")
    accuracy_metrics: Optional[dict] = Field(None, description="Accuracy metrics")
    file_path: Optional[str] = Field(None, description="Path to the model file")
    performance_score: Optional[float] = Field(None, description="Performance score (0-100)", ge=0, le=100)


class ModelVersionResponse(BaseModel):
    """Response model for a single model version entry."""

    id: str = Field(..., description="Unique identifier for the model version")
    model_name: str = Field(..., description="Name of the model")
    version: str = Field(..., description="Version identifier")
    is_active: bool = Field(..., description="Whether this model version is active")
    is_experiment: bool = Field(..., description="Whether this is an experimental model")
    experiment_config: Optional[dict] = Field(None, description="A/B testing configuration")
    model_metadata: Optional[dict] = Field(None, description="Model training metadata")
    accuracy_metrics: Optional[dict] = Field(None, description="Accuracy metrics")
    file_path: Optional[str] = Field(None, description="Path to the model file")
    performance_score: Optional[float] = Field(None, description="Performance score")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ModelVersionListResponse(BaseModel):
    """Response model for listing model versions."""

    models: List[ModelVersionResponse] = Field(..., description="List of model version entries")
    total_count: int = Field(..., description="Total number of entries")


class ModelRetrainRequest(BaseModel):
    """Request model for manual model retraining."""

    model_name: str = Field(..., description="Name of the model to retrain (e.g., ranking, skill_matching)")


class ModelRollbackRequest(BaseModel):
    """Request model for rolling back to a previous model version."""

    model_name: str = Field(..., description="Name of the model to rollback (e.g., ranking, skill_matching)")
    target_version: str = Field(..., description="Target version to rollback to (e.g., v1.0.0)")


class PerformanceMetricPoint(BaseModel):
    """Single performance metric data point for trend charts."""

    timestamp: str = Field(..., description="ISO timestamp of the measurement")
    accuracy: Optional[float] = Field(None, description="Accuracy metric (0-1)")
    precision: Optional[float] = Field(None, description="Precision metric (0-1)")
    recall: Optional[float] = Field(None, description="Recall metric (0-1)")
    f1_score: Optional[float] = Field(None, description="F1 score metric (0-1)")
    ndcg_score: Optional[float] = Field(None, description="NDCG score (0-1)")
    mrr_score: Optional[float] = Field(None, description="MRR score (0-1)")
    sample_count: Optional[int] = Field(None, description="Number of samples in this measurement")


class PerformanceMetricsResponse(BaseModel):
    """Response model for model performance metrics with trend data."""

    model_name: str = Field(..., description="Name of the model")
    active_version: Optional[str] = Field(None, description="Active version identifier")
    current_metrics: dict = Field(..., description="Current aggregated performance metrics")
    trend: List[PerformanceMetricPoint] = Field(..., description="Historical trend data points")
    trend_direction: str = Field(..., description="Overall trend direction (improving, declining, stable)")
    health_score: Optional[float] = Field(None, description="Overall model health score (0-100)")
    alert_status: str = Field(..., description="Current alert status (none, warning, critical)")
    last_updated: Optional[str] = Field(None, description="Timestamp of last update")


class StatisticalTestResultResponse(BaseModel):
    """Response model for individual statistical test results."""

    test_type: str = Field(..., description="Type of statistical test performed")
    statistic: float = Field(..., description="Test statistic value")
    p_value: float = Field(..., description="P-value from the test")
    is_significant: bool = Field(..., description="Whether result is statistically significant")
    significance_level: float = Field(..., description="Significance level (alpha) used")
    confidence_interval: Optional[List[float]] = Field(None, description="95% confidence interval for difference")
    effect_size: Optional[float] = Field(None, description="Effect size measure (Cohen's d or Cramer's V)")
    interpretation: str = Field(..., description="Human-readable interpretation of results")


class ABTestResultsResponse(BaseModel):
    """Response model for A/B test results with statistical significance data."""

    model_name: str = Field(..., description="Name of the model being tested")
    control_model: dict = Field(..., description="Control (active) model details")
    treatment_model: Optional[dict] = Field(None, description="Treatment (experimental) model details")
    control_metrics: dict = Field(..., description="Performance metrics for control model")
    treatment_metrics: Optional[dict] = Field(None, description="Performance metrics for treatment model")
    statistical_tests: List[StatisticalTestResultResponse] = Field(
        ..., description="List of statistical test results"
    )
    winner: str = Field(..., description="Which model performed better (control, treatment, tie, or inconclusive)")
    confidence: float = Field(..., description="Confidence level in the result (0-1)")
    recommendation: str = Field(..., description="Actionable recommendation based on test results")
    sample_sizes: dict = Field(..., description="Sample sizes for each group")
    is_statistically_significant: bool = Field(
        ..., description="Whether any test showed statistical significance"
    )
    timestamp: str = Field(..., description="ISO timestamp of the analysis")


def _format_model_response(model: MLModelVersion) -> dict:
    """Format a MLModelVersion instance as a response dict."""
    return {
        "id": str(model.id),
        "model_name": model.model_name,
        "version": model.version,
        "is_active": model.is_active,
        "is_experiment": model.is_experiment,
        "experiment_config": model.experiment_config,
        "model_metadata": model.model_metadata,
        "accuracy_metrics": model.accuracy_metrics,
        "file_path": model.file_path,
        "performance_score": float(model.performance_score) if model.performance_score is not None else None,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


@router.post(
    "/",
    response_model=ModelVersionListResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Model Versions"],
)
async def create_model_versions(
    request: ModelVersionCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create ML model version entries.

    This endpoint accepts a batch of model version entries for tracking different
    versions of ML models with A/B testing support, validating the data and creating
    database records for each model with performance metrics and configuration.

    Args:
        request: Create request with list of model versions
        db: Database session

    Returns:
        JSON response with created model version entries

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "models": [
        ...         {
        ...             "model_name": "skill_matching",
        ...             "version": "v1.0.0",
        ...             "is_active": True,
        ...             "is_experiment": False,
        ...             "performance_score": 85.5
        ...         }
        ...     ]
        ... }
        >>> response = requests.post("/api/model-versions/", json=data)
        >>> response.json()
        {
            "models": [...],
            "total_count": 1
        }
    """
    try:
        logger.info(f"Creating {len(request.models)} model versions")

        # Validate models list
        if not request.models or len(request.models) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one model version must be provided",
            )

        # Validate model names and versions
        for model in request.models:
            if not model.model_name or len(model.model_name.strip()) == 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Model name cannot be empty",
                )
            if not model.version or len(model.version.strip()) == 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Version cannot be empty",
                )

        # Track created model objects for response
        created_db_models = []
        for model_entry in request.models:
            # Create database record
            db_model = MLModelVersion(
                model_name=model_entry.model_name,
                version=model_entry.version,
                is_active=model_entry.is_active,
                is_experiment=model_entry.is_experiment,
                experiment_config=model_entry.experiment_config,
                model_metadata=model_entry.model_metadata,
                accuracy_metrics=model_entry.accuracy_metrics,
                file_path=model_entry.file_path,
                performance_score=model_entry.performance_score,
            )
            db.add(db_model)
            created_db_models.append(db_model)

        # Flush to get generated IDs and commit
        await db.flush()
        await db.commit()

        # Refresh to get generated timestamps
        created_models = []
        for db_model in created_db_models:
            await db.refresh(db_model)
            created_models.append(_format_model_response(db_model))

        response_data = {
            "models": created_models,
            "total_count": len(created_models),
        }

        logger.info(f"Created {len(created_models)} model versions")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error creating model versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create model versions: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error creating model versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create model versions: {str(e)}",
        ) from e


@router.get("/", tags=["Model Versions"])
async def list_model_versions(
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_experiment: Optional[bool] = Query(None, description="Filter by experiment status"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List model version entries with optional filters.

    Args:
        model_name: Optional model name filter
        is_active: Optional active status filter
        is_experiment: Optional experiment status filter
        db: Database session

    Returns:
        JSON response with list of model version entries

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/model-versions/?model_name=skill_matching")
        >>> response.json()
    """
    try:
        logger.info(
            f"Listing model versions with filters - model_name: {model_name}, "
            f"is_active: {is_active}, is_experiment: {is_experiment}"
        )

        # Build query with filters
        query = select(MLModelVersion)

        if model_name:
            query = query.where(MLModelVersion.model_name == model_name)
        if is_active is not None:
            query = query.where(MLModelVersion.is_active == is_active)
        if is_experiment is not None:
            query = query.where(MLModelVersion.is_experiment == is_experiment)

        # Order by created_at descending
        query = query.order_by(MLModelVersion.created_at.desc())

        result = await db.execute(query)
        models = result.scalars().all()

        # Format response
        response_data = {
            "models": [_format_model_response(m) for m in models],
            "total_count": len(models),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error listing model versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list model versions: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error listing model versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list model versions: {str(e)}",
        ) from e


@router.get("/active", tags=["Model Versions"])
async def get_active_model(
    model_name: str = Query(..., description="Model name to get active version for"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get the active model version for a specific model name.

    Args:
        model_name: Name of the model
        db: Database session

    Returns:
        JSON response with active model version details

    Raises:
        HTTPException(404): If no active model is found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/model-versions/active?model_name=skill_matching")
        >>> response.json()
    """
    try:
        logger.info(f"Getting active model for: {model_name}")

        query = select(MLModelVersion).where(
            MLModelVersion.model_name == model_name,
            MLModelVersion.is_active == True,
        )
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active model found for: {model_name}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_format_model_response(model),
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting active model: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active model: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error getting active model: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active model: {str(e)}",
        ) from e


@router.get("/metrics/{model_name}", tags=["Model Versions"])
async def get_model_performance_metrics(
    model_name: str,
    days: int = Query(7, description="Number of days of historical data to include", ge=1, le=90),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get performance metrics for a model with trend data.

    This endpoint returns current performance metrics and historical trend data
    for the specified model, useful for dashboards and performance monitoring.

    Args:
        model_name: Name of the model to get metrics for (e.g., ranking, skill_matching)
        days: Number of days of historical data to include (default: 7, max: 90)
        db: Database session

    Returns:
        JSON response with current metrics and trend data

    Raises:
        HTTPException(404): If no model is found with the given name
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/model-versions/metrics/ranking")
        >>> response.json()
        {
            "model_name": "ranking",
            "active_version": "v2.1.0",
            "current_metrics": {
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.88,
                "f1_score": 0.85,
                "ndcg_score": 0.91,
                "mrr_score": 0.78
            },
            "trend": [...],
            "trend_direction": "improving",
            "health_score": 85.5,
            "alert_status": "none",
            "last_updated": "2024-01-15T10:30:00Z"
        }
    """
    try:
        logger.info(f"Getting performance metrics for model: {model_name}, days: {days}")

        # Get active model version for this model name
        active_query = select(MLModelVersion).where(
            MLModelVersion.model_name == model_name,
            MLModelVersion.is_active == True,
        )
        active_result = await db.execute(active_query)
        active_model = active_result.scalar_one_or_none()

        if active_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active model found for: {model_name}",
            )

        # Get performance snapshots for trend data
        from datetime import datetime, timedelta, timezone

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Query snapshots for the active model version, ordered by created_at desc
        snapshot_query = (
            select(ModelPerformanceSnapshot)
            .where(
                ModelPerformanceSnapshot.model_version_id == str(active_model.id),
                ModelPerformanceSnapshot.created_at >= cutoff_date,
            )
            .order_by(ModelPerformanceSnapshot.created_at.desc())
            .limit(30)  # Limit to 30 data points for charting
        )
        snapshot_result = await db.execute(snapshot_query)
        snapshots = snapshot_result.scalars().all()

        # Build trend data from snapshots
        trend_data = []
        for snapshot in reversed(snapshots):  # Reverse to get chronological order
            trend_point = {
                "timestamp": snapshot.created_at.isoformat() if snapshot.created_at else None,
                "accuracy": float(snapshot.accuracy) if snapshot.accuracy is not None else None,
                "precision": float(snapshot.precision) if snapshot.precision is not None else None,
                "recall": float(snapshot.recall) if snapshot.recall is not None else None,
                "f1_score": float(snapshot.f1_score) if snapshot.f1_score is not None else None,
                "ndcg_score": float(snapshot.ndcg_score) if snapshot.ndcg_score is not None else None,
                "mrr_score": float(snapshot.mrr_score) if snapshot.mrr_score is not None else None,
                "sample_count": snapshot.sample_count,
            }
            trend_data.append(trend_point)

        # Get current metrics from the most recent snapshot
        current_metrics = {}
        if snapshots:
            latest = snapshots[0]  # Most recent snapshot (desc order)
            current_metrics = {
                "accuracy": float(latest.accuracy) if latest.accuracy is not None else None,
                "precision": float(latest.precision) if latest.precision is not None else None,
                "recall": float(latest.recall) if latest.recall is not None else None,
                "f1_score": float(latest.f1_score) if latest.f1_score is not None else None,
                "auc_score": float(latest.auc_score) if latest.auc_score is not None else None,
                "ndcg_score": float(latest.ndcg_score) if latest.ndcg_score is not None else None,
                "mrr_score": float(latest.mrr_score) if latest.mrr_score is not None else None,
                "sample_count": latest.sample_count,
                "evaluation_count": latest.evaluation_count,
                "health_score": float(latest.health_score) if latest.health_score is not None else None,
            }
        else:
            # No snapshots, use model's stored accuracy_metrics if available
            if active_model.accuracy_metrics:
                current_metrics = active_model.accuracy_metrics
            else:
                current_metrics = {
                    "accuracy": None,
                    "precision": None,
                    "recall": None,
                    "f1_score": None,
                    "ndcg_score": None,
                    "mrr_score": None,
                }

        # Determine trend direction
        trend_direction = "stable"
        if len(snapshots) >= 2:
            latest_snapshot = snapshots[0]
            oldest_snapshot = snapshots[-1]

            # Compare F1 scores (or accuracy as fallback)
            latest_score = latest_snapshot.f1_score or latest_snapshot.accuracy
            oldest_score = oldest_snapshot.f1_score or oldest_snapshot.accuracy

            if latest_score is not None and oldest_score is not None:
                diff = float(latest_score) - float(oldest_score)
                if diff > 0.02:  # 2% improvement threshold
                    trend_direction = "improving"
                elif diff < -0.02:  # 2% decline threshold
                    trend_direction = "declining"
                else:
                    trend_direction = "stable"
        elif snapshots:
            # Use the snapshot's recorded trend if available
            trend_direction = snapshots[0].performance_trend or "stable"

        # Get alert status from latest snapshot or default to none
        alert_status = "none"
        if snapshots:
            alert_status = snapshots[0].alert_status or "none"

        # Calculate health score
        health_score = None
        if snapshots and snapshots[0].health_score is not None:
            health_score = float(snapshots[0].health_score)
        elif active_model.performance_score is not None:
            health_score = float(active_model.performance_score)

        # Get last updated timestamp
        last_updated = None
        if snapshots:
            last_updated = snapshots[0].created_at.isoformat() if snapshots[0].created_at else None
        elif active_model.updated_at:
            last_updated = active_model.updated_at.isoformat()

        response_data = {
            "model_name": model_name,
            "active_version": active_model.version,
            "current_metrics": current_metrics,
            "trend": trend_data,
            "trend_direction": trend_direction,
            "health_score": health_score,
            "alert_status": alert_status,
            "last_updated": last_updated,
        }

        logger.info(f"Retrieved performance metrics for model: {model_name}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting model metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model metrics: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error getting model metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model metrics: {str(e)}",
        ) from e


@router.get("/ab-test/{model_name}", tags=["Model Versions"])
async def get_ab_test_results(
    model_name: str,
    significance_level: float = Query(0.05, description="Significance level (alpha) for statistical tests", ge=0.01, le=0.20),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get A/B test results with statistical significance data for a model.

    This endpoint compares the active (control) model with any experimental
    (treatment) model and returns statistical significance analysis including
    chi-square tests, t-tests, confidence intervals, and effect sizes.

    Args:
        model_name: Name of the model to analyze (e.g., ranking, skill_matching)
        significance_level: Significance level (alpha) for hypothesis tests (default: 0.05)
        db: Database session

    Returns:
        JSON response with A/B test results, statistical tests, and recommendations

    Raises:
        HTTPException(404): If no active model is found for the given name
        HTTPException(500): If analysis fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/model-versions/ab-test/ranking")
        >>> response.json()
        {
            "model_name": "ranking",
            "control_model": {"version": "v1.0.0", ...},
            "treatment_model": {"version": "v2.0.0", ...},
            "control_metrics": {"accuracy": 0.85, "f1_score": 0.83, ...},
            "treatment_metrics": {"accuracy": 0.87, "f1_score": 0.86, ...},
            "statistical_tests": [
                {
                    "test_type": "chi_square",
                    "statistic": 4.5,
                    "p_value": 0.034,
                    "is_significant": true,
                    "significance_level": 0.05,
                    "effect_size": 0.15,
                    "interpretation": "Statistically significant difference..."
                }
            ],
            "winner": "treatment",
            "confidence": 0.85,
            "recommendation": "STRONG RECOMMENDATION: Promote treatment model...",
            "sample_sizes": {"control": 1000, "treatment": 1000},
            "is_statistically_significant": true,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    """
    try:
        logger.info(f"Getting A/B test results for model: {model_name}")

        # Get the active (control) model
        control_query = select(MLModelVersion).where(
            MLModelVersion.model_name == model_name,
            MLModelVersion.is_active == True,
        )
        control_result = await db.execute(control_query)
        control_model = control_result.scalar_one_or_none()

        if control_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active model found for: {model_name}",
            )

        # Get the experimental (treatment) model
        treatment_query = select(MLModelVersion).where(
            MLModelVersion.model_name == model_name,
            MLModelVersion.is_experiment == True,
            MLModelVersion.is_active == False,
        )
        treatment_result = await db.execute(treatment_query)
        treatment_model = treatment_result.scalars().first()

        # Prepare control metrics
        control_metrics = {
            "accuracy": float(control_model.accuracy_metrics.get("accuracy", 0)) if control_model.accuracy_metrics else 0,
            "precision": float(control_model.accuracy_metrics.get("precision", 0)) if control_model.accuracy_metrics else 0,
            "recall": float(control_model.accuracy_metrics.get("recall", 0)) if control_model.accuracy_metrics else 0,
            "f1_score": float(control_model.accuracy_metrics.get("f1_score", 0)) if control_model.accuracy_metrics else 0,
            "auc_score": float(control_model.accuracy_metrics.get("auc_score", 0)) if control_model.accuracy_metrics else 0,
            "sample_size": int(control_model.model_metadata.get("sample_size", 0)) if control_model.model_metadata else 0,
            "performance_score": float(control_model.performance_score) if control_model.performance_score is not None else 0,
        }

        # Extract success/failure counts if available (for chi-square test)
        if control_model.accuracy_metrics:
            control_metrics["successes"] = control_model.accuracy_metrics.get("successes", 0)
            control_metrics["failures"] = control_model.accuracy_metrics.get("failures", 0)

        # Prepare treatment metrics if treatment model exists
        treatment_metrics = {}
        if treatment_model:
            treatment_metrics = {
                "accuracy": float(treatment_model.accuracy_metrics.get("accuracy", 0)) if treatment_model.accuracy_metrics else 0,
                "precision": float(treatment_model.accuracy_metrics.get("precision", 0)) if treatment_model.accuracy_metrics else 0,
                "recall": float(treatment_model.accuracy_metrics.get("recall", 0)) if treatment_model.accuracy_metrics else 0,
                "f1_score": float(treatment_model.accuracy_metrics.get("f1_score", 0)) if treatment_model.accuracy_metrics else 0,
                "auc_score": float(treatment_model.accuracy_metrics.get("auc_score", 0)) if treatment_model.accuracy_metrics else 0,
                "sample_size": int(treatment_model.model_metadata.get("sample_size", 0)) if treatment_model.model_metadata else 0,
                "performance_score": float(treatment_model.performance_score) if treatment_model.performance_score is not None else 0,
            }

            # Extract success/failure counts if available
            if treatment_model.accuracy_metrics:
                treatment_metrics["successes"] = treatment_model.accuracy_metrics.get("successes", 0)
                treatment_metrics["failures"] = treatment_model.accuracy_metrics.get("failures", 0)

        # Perform statistical analysis using ABTestAnalyzer
        statistical_tests = []
        winner = "control"
        confidence = 0.0
        recommendation = "No experimental model available for comparison."
        is_statistically_significant = False

        if treatment_model:
            try:
                from analyzers.ab_test_analyzer import ABTestAnalyzer

                analyzer = ABTestAnalyzer(default_significance_level=significance_level)

                # Perform comprehensive comparison
                comparison = analyzer.compare_models(
                    control_model_id=str(control_model.id),
                    treatment_model_id=str(treatment_model.id),
                    control_metrics=control_metrics,
                    treatment_metrics=treatment_metrics,
                    significance_level=significance_level,
                )

                # Extract statistical test results
                for test_name, test_result in comparison.statistical_tests.items():
                    test_response = {
                        "test_type": test_result.test_type.value,
                        "statistic": test_result.statistic,
                        "p_value": test_result.p_value,
                        "is_significant": test_result.is_significant,
                        "significance_level": test_result.significance_level,
                        "confidence_interval": list(test_result.confidence_interval) if test_result.confidence_interval else None,
                        "effect_size": test_result.effect_size,
                        "interpretation": test_result.interpretation,
                    }
                    statistical_tests.append(test_response)

                    if test_result.is_significant:
                        is_statistically_significant = True

                winner = comparison.winner
                confidence = comparison.confidence
                recommendation = comparison.recommendation

            except ImportError:
                logger.warning("ABTestAnalyzer not available, using basic comparison")
                # Fallback to simple comparison without statistical tests
                control_f1 = control_metrics.get("f1_score", 0) or 0
                treatment_f1 = treatment_metrics.get("f1_score", 0) or 0

                if treatment_f1 > control_f1:
                    winner = "treatment"
                    diff_pct = (treatment_f1 - control_f1) / control_f1 * 100 if control_f1 > 0 else 0
                    recommendation = f"Treatment model shows {diff_pct:.1f}% improvement in F1 score. Statistical analysis unavailable."
                elif control_f1 > treatment_f1:
                    winner = "control"
                    diff_pct = (control_f1 - treatment_f1) / treatment_f1 * 100 if treatment_f1 > 0 else 0
                    recommendation = f"Control model outperforms treatment by {diff_pct:.1f}% in F1 score. Statistical analysis unavailable."
                else:
                    winner = "tie"
                    recommendation = "Both models show equivalent F1 scores. Statistical analysis unavailable."

                confidence = 0.5

        # Build response
        from datetime import datetime, timezone

        response_data = {
            "model_name": model_name,
            "control_model": _format_model_response(control_model),
            "treatment_model": _format_model_response(treatment_model) if treatment_model else None,
            "control_metrics": control_metrics,
            "treatment_metrics": treatment_metrics if treatment_model else None,
            "statistical_tests": statistical_tests,
            "winner": winner,
            "confidence": confidence,
            "recommendation": recommendation,
            "sample_sizes": {
                "control": control_metrics.get("sample_size", 0),
                "treatment": treatment_metrics.get("sample_size", 0) if treatment_model else 0,
            },
            "is_statistically_significant": is_statistically_significant,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"A/B test analysis complete for model: {model_name}, winner: {winner}, "
            f"confidence: {confidence:.2%}, significant: {is_statistically_significant}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting A/B test results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get A/B test results: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error getting A/B test results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get A/B test results: {str(e)}",
        ) from e


@router.get("/{version_id}", tags=["Model Versions"])
async def get_model_version(
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific model version entry by ID.

    Args:
        version_id: Unique identifier of the model version
        db: Database session

    Returns:
        JSON response with model version details

    Raises:
        HTTPException(404): If model version is not found
        HTTPException(422): If version_id is not a valid UUID
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/model-versions/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
    """
    try:
        logger.info(f"Getting model version: {version_id}")

        # Validate UUID format
        try:
            version_uuid = UUID(version_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        query = select(MLModelVersion).where(MLModelVersion.id == version_uuid)
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version not found: {version_id}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_format_model_response(model),
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model version: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error getting model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model version: {str(e)}",
        ) from e


@router.put("/{version_id}", tags=["Model Versions"])
async def update_model_version(
    version_id: str,
    request: ModelVersionUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a model version entry.

    Args:
        version_id: Unique identifier of the model version
        request: Update request with fields to modify
        db: Database session

    Returns:
        JSON response with updated model version entry

    Raises:
        HTTPException(404): If model version is not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"performance_score": 90.0, "is_active": True}
        >>> response = requests.put(
        ...     "/api/model-versions/123",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Updating model version: {version_id}")

        # Validate UUID format
        try:
            version_uuid = UUID(version_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Validate performance score is in range [0, 100]
        if request.performance_score is not None and not (0 <= request.performance_score <= 100):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Performance score must be between 0 and 100",
            )

        # Query existing model
        query = select(MLModelVersion).where(MLModelVersion.id == version_uuid)
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version not found: {version_id}",
            )

        # Update fields
        if request.version is not None:
            model.version = request.version
        if request.is_active is not None:
            model.is_active = request.is_active
        if request.is_experiment is not None:
            model.is_experiment = request.is_experiment
        if request.experiment_config is not None:
            model.experiment_config = request.experiment_config
        if request.model_metadata is not None:
            model.model_metadata = request.model_metadata
        if request.accuracy_metrics is not None:
            model.accuracy_metrics = request.accuracy_metrics
        if request.file_path is not None:
            model.file_path = request.file_path
        if request.performance_score is not None:
            model.performance_score = request.performance_score

        await db.commit()
        await db.refresh(model)

        logger.info(f"Model version {version_id} updated successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_format_model_response(model),
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error updating model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update model version: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error updating model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update model version: {str(e)}",
        ) from e


@router.delete("/{version_id}", tags=["Model Versions"])
async def delete_model_version(
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a model version entry.

    Args:
        version_id: Unique identifier of the model version
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If model version is not found
        HTTPException(422): If version_id is not a valid UUID
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("/api/model-versions/123")
        >>> response.json()
        {"message": "Model version deleted successfully"}
    """
    try:
        logger.info(f"Deleting model version: {version_id}")

        # Validate UUID format
        try:
            version_uuid = UUID(version_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Query existing model
        query = select(MLModelVersion).where(MLModelVersion.id == version_uuid)
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version not found: {version_id}",
            )

        # Delete the model
        await db.delete(model)
        await db.commit()

        logger.info(f"Model version {version_id} deleted successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Model version {version_id} deleted successfully"},
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete model version: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error deleting model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete model version: {str(e)}",
        ) from e


@router.post("/{version_id}/activate", tags=["Model Versions"])
async def activate_model_version(
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Activate a specific model version.

    This endpoint activates a model version, deactivating other versions of the same model.

    Args:
        version_id: Unique identifier of the model version to activate
        db: Database session

    Returns:
        JSON response with activated model version details

    Raises:
        HTTPException(404): If model version is not found
        HTTPException(422): If version_id is not a valid UUID
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post("/api/model-versions/123/activate")
        >>> response.json()
        {"message": "Model version activated successfully"}
    """
    try:
        logger.info(f"Activating model version: {version_id}")

        # Validate UUID format
        try:
            version_uuid = UUID(version_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Query existing model
        query = select(MLModelVersion).where(MLModelVersion.id == version_uuid)
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version not found: {version_id}",
            )

        # Deactivate all other versions of the same model
        deactivate_query = select(MLModelVersion).where(
            MLModelVersion.model_name == model.model_name,
            MLModelVersion.id != version_uuid,
        )
        deactivate_result = await db.execute(deactivate_query)
        other_models = deactivate_result.scalars().all()

        for other_model in other_models:
            other_model.is_active = False

        # Activate the target model
        model.is_active = True

        await db.commit()
        await db.refresh(model)

        logger.info(f"Model version {version_id} activated successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Model version {version_id} activated successfully",
                **_format_model_response(model),
            },
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error activating model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate model version: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error activating model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate model version: {str(e)}",
        ) from e


@router.post("/{version_id}/deactivate", tags=["Model Versions"])
async def deactivate_model_version(
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Deactivate a specific model version.

    Args:
        version_id: Unique identifier of the model version to deactivate
        db: Database session

    Returns:
        JSON response with deactivated model version details

    Raises:
        HTTPException(404): If model version is not found
        HTTPException(422): If version_id is not a valid UUID
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post("/api/model-versions/123/deactivate")
        >>> response.json()
        {"message": "Model version deactivated successfully"}
    """
    try:
        logger.info(f"Deactivating model version: {version_id}")

        # Validate UUID format
        try:
            version_uuid = UUID(version_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID format: {e}",
            )

        # Query existing model
        query = select(MLModelVersion).where(MLModelVersion.id == version_uuid)
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version not found: {version_id}",
            )

        # Deactivate the model
        model.is_active = False

        await db.commit()
        await db.refresh(model)

        logger.info(f"Model version {version_id} deactivated successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Model version {version_id} deactivated successfully",
                **_format_model_response(model),
            },
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deactivating model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate model version: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error deactivating model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate model version: {str(e)}",
        ) from e


@router.post("/retrain", tags=["Model Versions"])
async def trigger_model_retraining(
    request: ModelRetrainRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Trigger manual retraining for a specific model.

    This endpoint initiates an asynchronous retraining job for the specified model.
    The retraining process runs in the background and this endpoint returns immediately
    with a 202 Accepted status.

    Args:
        request: Retrain request containing the model name
        db: Database session

    Returns:
        JSON response confirming retraining job initiation

    Raises:
        HTTPException(422): If model name validation fails
        HTTPException(404): If model is not found
        HTTPException(500): If retraining job fails to start

    Examples:
        >>> import requests
        >>> data = {"model_name": "ranking"}
        >>> response = requests.post(
        ...     "/api/model-versions/retrain",
        ...     json=data
        ... )
        >>> response.json()
        {
            "message": "Model retraining initiated",
            "model_name": "ranking",
            "status": "pending"
        }
    """
    try:
        logger.info(f"Triggering manual retraining for model: {request.model_name}")

        # Validate model name
        if not request.model_name or len(request.model_name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Model name cannot be empty",
            )

        # Check if at least one version of this model exists
        query = select(MLModelVersion).where(MLModelVersion.model_name == request.model_name)
        result = await db.execute(query)
        existing_models = result.scalars().all()

        if not existing_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No model found with name: {request.model_name}",
            )

        # For now, return placeholder response
        # Actual retraining logic will be implemented in a later subtask
        response_data = {
            "message": "Model retraining initiated",
            "model_name": request.model_name,
            "status": "pending",
            "existing_versions": len(existing_models),
        }

        logger.info(
            f"Retraining job initiated for model: {request.model_name}"
        )

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=response_data,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error triggering model retraining: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger model retraining: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error triggering model retraining: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger model retraining: {str(e)}",
        ) from e


@router.post("/rollback", tags=["Model Versions"])
async def rollback_model_version(
    request: ModelRollbackRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Rollback to a previous model version.

    This endpoint rolls back the active model to a specified previous version,
    deactivating the current version and activating the target version.

    Args:
        request: Rollback request containing model name and target version
        db: Database session

    Returns:
        JSON response confirming rollback operation

    Raises:
        HTTPException(422): If validation fails
        HTTPException(404): If target version is not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "model_name": "ranking",
        ...     "target_version": "v1.0.0"
        ... }
        >>> response = requests.post(
        ...     "/api/model-versions/rollback",
        ...     json=data
        ... )
        >>> response.json()
        {
            "message": "Model rolled back successfully",
            "model_name": "ranking",
            "target_version": "v1.0.0",
            "previous_version": "v2.0.0"
        }
    """
    try:
        logger.info(
            f"Rolling back model {request.model_name} to version {request.target_version}"
        )

        # Validate model name
        if not request.model_name or len(request.model_name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Model name cannot be empty",
            )

        # Validate target version
        if not request.target_version or len(request.target_version.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Target version cannot be empty",
            )

        # Get current active model
        active_query = select(MLModelVersion).where(
            MLModelVersion.model_name == request.model_name,
            MLModelVersion.is_active == True,
        )
        active_result = await db.execute(active_query)
        current_active = active_result.scalar_one_or_none()

        # Get target version
        target_query = select(MLModelVersion).where(
            MLModelVersion.model_name == request.model_name,
            MLModelVersion.version == request.target_version,
        )
        target_result = await db.execute(target_query)
        target_model = target_result.scalar_one_or_none()

        if target_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target version {request.target_version} not found for model {request.model_name}",
            )

        previous_version = None
        if current_active:
            previous_version = current_active.version
            # Don't rollback to the same version
            if current_active.id == target_model.id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Model {request.model_name} is already at version {request.target_version}",
                )
            # Deactivate current version
            current_active.is_active = False

        # Activate target version
        target_model.is_active = True

        await db.commit()
        await db.refresh(target_model)

        response_data = {
            "message": "Model rolled back successfully",
            "model_name": request.model_name,
            "target_version": request.target_version,
            "previous_version": previous_version,
            "active_model": _format_model_response(target_model),
        }

        logger.info(
            f"Model {request.model_name} rolled back to version {request.target_version}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error rolling back model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback model version: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error rolling back model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback model version: {str(e)}",
        ) from e
