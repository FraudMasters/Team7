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
