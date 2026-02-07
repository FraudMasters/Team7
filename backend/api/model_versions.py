"""
ML model version management endpoints.

This module provides endpoints for managing machine learning model versions,
including CRUD operations for creating, reading, updating, and deleting model
version entries with A/B testing support and performance metrics.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
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


@router.post(
    "/",
    response_model=ModelVersionListResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Model Versions"],
)
async def create_model_versions(
    request: Request,
    create_data: ModelVersionCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create ML model version entries.

    This endpoint accepts a batch of model version entries for tracking different
    versions of ML models with A/B testing support, validating the data and creating
    database records for each model with performance metrics and configuration.

    Args:
        request: FastAPI request object
        create_data: Create request with list of model versions
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
        >>> response = requests.post("http://localhost:8000/api/model-versions/", json=data)
        >>> response.json()
        {
            "models": [...],
            "total_count": 1
        }
    """
    try:
        logger.info(f"Creating {len(create_data.models)} model versions")

        # Validate models list
        if not create_data.models or len(create_data.models) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one model version must be provided",
            )

        # Validate model names and versions
        for model in create_data.models:
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

        created_models = []
        for model_entry in create_data.models:
            # Create new model version
            model_version = MLModelVersion(
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

            db.add(model_version)
            await db.commit()
            await db.refresh(model_version)

            created_models.append({
                "id": str(model_version.id),
                "model_name": model_version.model_name,
                "version": model_version.version,
                "is_active": model_version.is_active,
                "is_experiment": model_version.is_experiment,
                "experiment_config": model_version.experiment_config,
                "model_metadata": model_version.model_metadata,
                "accuracy_metrics": model_version.accuracy_metrics,
                "file_path": model_version.file_path,
                "performance_score": float(model_version.performance_score) if model_version.performance_score is not None else None,
                "created_at": model_version.created_at.isoformat() if model_version.created_at else None,
                "updated_at": model_version.updated_at.isoformat() if model_version.updated_at else None,
            })

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
    except Exception as e:
        logger.error(f"Error creating model versions: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create model versions: {str(e)}",
        ) from e


@router.get("/", tags=["Model Versions"])
async def list_model_versions(
    request: Request,
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_experiment: Optional[bool] = Query(None, description="Filter by experiment status"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List model version entries with optional filters.

    Args:
        request: FastAPI request object
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
        >>> response = requests.get("http://localhost:8000/api/model-versions/?model_name=skill_matching")
        >>> response.json()
    """
    try:
        logger.info(
            f"Listing model versions with filters - model_name: {model_name}, "
            f"is_active: {is_active}, is_experiment: {is_experiment}"
        )

        # Build base query
        query = select(MLModelVersion)

        # Apply filters if provided
        if model_name:
            query = query.where(MLModelVersion.model_name == model_name)
        if is_active is not None:
            query = query.where(MLModelVersion.is_active == is_active)
        if is_experiment is not None:
            query = query.where(MLModelVersion.is_experiment == is_experiment)

        # Get total count
        count_query = select(func.count()).select_from(MLModelVersion)
        if model_name:
            count_query = count_query.where(MLModelVersion.model_name == model_name)
        if is_active is not None:
            count_query = count_query.where(MLModelVersion.is_active == is_active)
        if is_experiment is not None:
            count_query = count_query.where(MLModelVersion.is_experiment == is_experiment)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Order by most recently created
        query = query.order_by(MLModelVersion.created_at.desc())

        # Execute query
        result = await db.execute(query)
        model_versions = result.scalars().all()

        # Convert to response format
        models_list = []
        for model_version in model_versions:
            models_list.append({
                "id": str(model_version.id),
                "model_name": model_version.model_name,
                "version": model_version.version,
                "is_active": model_version.is_active,
                "is_experiment": model_version.is_experiment,
                "experiment_config": model_version.experiment_config,
                "model_metadata": model_version.model_metadata,
                "accuracy_metrics": model_version.accuracy_metrics,
                "file_path": model_version.file_path,
                "performance_score": float(model_version.performance_score) if model_version.performance_score is not None else None,
                "created_at": model_version.created_at.isoformat() if model_version.created_at else None,
                "updated_at": model_version.updated_at.isoformat() if model_version.updated_at else None,
            })

        logger.info(f"Retrieved {len(models_list)} model versions (total: {total})")

        response_data = {
            "models": models_list,
            "total_count": total,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing model versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list model versions: {str(e)}",
        ) from e


@router.get("/active", tags=["Model Versions"])
async def get_active_model(
    request: Request,
    model_name: str = Query(..., description="Model name to get active version for"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get the active model version for a specific model name.

    Args:
        request: FastAPI request object
        model_name: Name of the model
        db: Database session

    Returns:
        JSON response with active model version details

    Raises:
        HTTPException(404): If no active model is found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/model-versions/active?model_name=skill_matching")
        >>> response.json()
    """
    try:
        logger.info(f"Getting active model for: {model_name}")

        # Query for active model
        query = select(MLModelVersion).where(
            MLModelVersion.model_name == model_name,
            MLModelVersion.is_active == True
        )

        result = await db.execute(query)
        model_version = result.scalar_one_or_none()

        if not model_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active model found for: {model_name}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(model_version.id),
                "model_name": model_version.model_name,
                "version": model_version.version,
                "is_active": model_version.is_active,
                "is_experiment": model_version.is_experiment,
                "experiment_config": model_version.experiment_config,
                "model_metadata": model_version.model_metadata,
                "accuracy_metrics": model_version.accuracy_metrics,
                "file_path": model_version.file_path,
                "performance_score": float(model_version.performance_score) if model_version.performance_score is not None else None,
                "created_at": model_version.created_at.isoformat() if model_version.created_at else None,
                "updated_at": model_version.updated_at.isoformat() if model_version.updated_at else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active model: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active model: {str(e)}",
        ) from e


@router.get("/{version_id}", tags=["Model Versions"])
async def get_model_version(
    request: Request,
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific model version entry by ID.

    Args:
        request: FastAPI request object
        version_id: Unique identifier of the model version
        db: Database session

    Returns:
        JSON response with model version details

    Raises:
        HTTPException(400): If version ID format is invalid
        HTTPException(404): If model version is not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/model-versions/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
    """
    try:
        logger.info(f"Getting model version: {version_id}")

        # Parse version_id as UUID
        try:
            version_uuid = UUID(version_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model version ID format: {version_id}",
            )

        # Get the model version
        query = select(MLModelVersion).where(MLModelVersion.id == version_uuid)
        result = await db.execute(query)
        model_version = result.scalar_one_or_none()

        if not model_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version not found: {version_id}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(model_version.id),
                "model_name": model_version.model_name,
                "version": model_version.version,
                "is_active": model_version.is_active,
                "is_experiment": model_version.is_experiment,
                "experiment_config": model_version.experiment_config,
                "model_metadata": model_version.model_metadata,
                "accuracy_metrics": model_version.accuracy_metrics,
                "file_path": model_version.file_path,
                "performance_score": float(model_version.performance_score) if model_version.performance_score is not None else None,
                "created_at": model_version.created_at.isoformat() if model_version.created_at else None,
                "updated_at": model_version.updated_at.isoformat() if model_version.updated_at else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model version: {str(e)}",
        ) from e


@router.put("/{version_id}", tags=["Model Versions"])
async def update_model_version(
    request: Request,
    version_id: str,
    update_data: ModelVersionUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a model version entry.

    Args:
        request: FastAPI request object
        version_id: Unique identifier of the model version
        update_data: Update request with fields to modify
        db: Database session

    Returns:
        JSON response with updated model version entry

    Raises:
        HTTPException(400): If version ID format is invalid
        HTTPException(404): If model version is not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"performance_score": 90.0, "is_active": True}
        >>> response = requests.put(
        ...     "http://localhost:8000/api/model-versions/123",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Updating model version: {version_id}")

        # Validate performance score is in range [0, 100]
        if update_data.performance_score is not None and not (0 <= update_data.performance_score <= 100):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Performance score must be between 0 and 100",
            )

        # Parse version_id as UUID
        try:
            version_uuid = UUID(version_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model version ID format: {version_id}",
            )

        # Get the model version
        query = select(MLModelVersion).where(MLModelVersion.id == version_uuid)
        result = await db.execute(query)
        model_version = result.scalar_one_or_none()

        if not model_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version not found: {version_id}",
            )

        # Update fields if provided
        if update_data.version is not None:
            model_version.version = update_data.version
        if update_data.is_active is not None:
            model_version.is_active = update_data.is_active
        if update_data.is_experiment is not None:
            model_version.is_experiment = update_data.is_experiment
        if update_data.experiment_config is not None:
            model_version.experiment_config = update_data.experiment_config
        if update_data.model_metadata is not None:
            model_version.model_metadata = update_data.model_metadata
        if update_data.accuracy_metrics is not None:
            model_version.accuracy_metrics = update_data.accuracy_metrics
        if update_data.file_path is not None:
            model_version.file_path = update_data.file_path
        if update_data.performance_score is not None:
            model_version.performance_score = update_data.performance_score

        await db.commit()
        await db.refresh(model_version)

        logger.info(f"Model version {version_id} updated successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(model_version.id),
                "model_name": model_version.model_name,
                "version": model_version.version,
                "is_active": model_version.is_active,
                "is_experiment": model_version.is_experiment,
                "experiment_config": model_version.experiment_config,
                "model_metadata": model_version.model_metadata,
                "accuracy_metrics": model_version.accuracy_metrics,
                "file_path": model_version.file_path,
                "performance_score": float(model_version.performance_score) if model_version.performance_score is not None else None,
                "created_at": model_version.created_at.isoformat() if model_version.created_at else None,
                "updated_at": model_version.updated_at.isoformat() if model_version.updated_at else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating model version: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update model version: {str(e)}",
        ) from e


@router.delete("/{version_id}", tags=["Model Versions"])
async def delete_model_version(
    request: Request,
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a model version entry.

    Args:
        request: FastAPI request object
        version_id: Unique identifier of the model version
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(400): If version ID format is invalid
        HTTPException(404): If model version is not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/model-versions/123")
        >>> response.json()
        {"message": "Model version deleted successfully"}
    """
    try:
        logger.info(f"Deleting model version: {version_id}")

        # Parse version_id as UUID
        try:
            version_uuid = UUID(version_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model version ID format: {version_id}",
            )

        # Get the model version
        query = select(MLModelVersion).where(MLModelVersion.id == version_uuid)
        result = await db.execute(query)
        model_version = result.scalar_one_or_none()

        if not model_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version not found: {version_id}",
            )

        # Delete the model version
        await db.delete(model_version)
        await db.commit()

        logger.info(f"Model version {version_id} deleted successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Model version {version_id} deleted successfully"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model version: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete model version: {str(e)}",
        ) from e


@router.post("/{version_id}/activate", tags=["Model Versions"])
async def activate_model_version(
    request: Request,
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Activate a specific model version.

    This endpoint activates a model version, deactivating other versions of the same model.

    Args:
        request: FastAPI request object
        version_id: Unique identifier of the model version to activate
        db: Database session

    Returns:
        JSON response with activated model version details

    Raises:
        HTTPException(400): If version ID format is invalid
        HTTPException(404): If model version is not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post("http://localhost:8000/api/model-versions/123/activate")
        >>> response.json()
        {"message": "Model version activated successfully"}
    """
    try:
        logger.info(f"Activating model version: {version_id}")

        # Parse version_id as UUID
        try:
            version_uuid = UUID(version_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model version ID format: {version_id}",
            )

        # Get the model version to activate
        query = select(MLModelVersion).where(MLModelVersion.id == version_uuid)
        result = await db.execute(query)
        model_version = result.scalar_one_or_none()

        if not model_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version not found: {version_id}",
            )

        # Deactivate all other versions of the same model
        deactivate_query = select(MLModelVersion).where(
            MLModelVersion.model_name == model_version.model_name,
            MLModelVersion.id != version_uuid
        )
        deactivate_result = await db.execute(deactivate_query)
        other_versions = deactivate_result.scalars().all()

        for other_version in other_versions:
            other_version.is_active = False

        # Activate the target version
        model_version.is_active = True

        await db.commit()
        await db.refresh(model_version)

        logger.info(f"Model version {version_id} activated successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Model version {version_id} activated successfully",
                "id": str(model_version.id),
                "is_active": model_version.is_active,
                "model_name": model_version.model_name,
                "version": model_version.version,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating model version: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate model version: {str(e)}",
        ) from e


@router.post("/{version_id}/deactivate", tags=["Model Versions"])
async def deactivate_model_version(
    request: Request,
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Deactivate a specific model version.

    Args:
        request: FastAPI request object
        version_id: Unique identifier of the model version to deactivate
        db: Database session

    Returns:
        JSON response with deactivated model version details

    Raises:
        HTTPException(400): If version ID format is invalid
        HTTPException(404): If model version is not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post("http://localhost:8000/api/model-versions/123/deactivate")
        >>> response.json()
        {"message": "Model version deactivated successfully"}
    """
    try:
        logger.info(f"Deactivating model version: {version_id}")

        # Parse version_id as UUID
        try:
            version_uuid = UUID(version_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model version ID format: {version_id}",
            )

        # Get the model version
        query = select(MLModelVersion).where(MLModelVersion.id == version_uuid)
        result = await db.execute(query)
        model_version = result.scalar_one_or_none()

        if not model_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model version not found: {version_id}",
            )

        # Deactivate the model version
        model_version.is_active = False

        await db.commit()
        await db.refresh(model_version)

        logger.info(f"Model version {version_id} deactivated successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Model version {version_id} deactivated successfully",
                "id": str(model_version.id),
                "is_active": model_version.is_active,
                "model_name": model_version.model_name,
                "version": model_version.version,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating model version: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate model version: {str(e)}",
        ) from e


@router.post("/retrain", tags=["Model Versions"])
async def trigger_model_retraining(
    request: Request,
    retrain_data: ModelRetrainRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Trigger manual retraining for a specific model.

    This endpoint initiates an asynchronous retraining job for the specified model.
    The retraining process runs in the background via Celery and this endpoint returns
    immediately with a 202 Accepted status and a task ID for tracking.

    Args:
        request: FastAPI request object
        retrain_data: Retrain request containing the model name
        db: Database session

    Returns:
        JSON response with task ID for tracking the retraining job

    Raises:
        HTTPException(422): If model name validation fails
        HTTPException(500): If retraining job fails to start

    Examples:
        >>> import requests
        >>> data = {"model_name": "ranking"}
        >>> response = requests.post(
        ...     "http://localhost:8000/api/model-versions/retrain",
        ...     json=data
        ... )
        >>> response.json()
        {
            "message": "Model retraining initiated",
            "model_name": "ranking",
            "task_id": "abc-123-def",
            "status": "pending"
        }
    """
    try:
        logger.info(f"Triggering manual retraining for model: {retrain_data.model_name}")

        # Validate model name
        if not retrain_data.model_name or len(retrain_data.model_name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Model name cannot be empty",
            )

        # Import the Celery task for manual retraining
        from tasks.model_retraining import manual_retraining_task

        # Trigger the retraining task asynchronously
        task = manual_retraining_task.delay(
            model_name=retrain_data.model_name,
            days_back=30,
            requested_by=None,  # Could be extracted from auth context
            auto_activate=False,
        )

        task_id = task.id

        response_data = {
            "message": "Model retraining initiated",
            "model_name": retrain_data.model_name,
            "task_id": task_id,
            "status": "pending",
        }

        logger.info(
            f"Retraining job initiated for model: {retrain_data.model_name}, "
            f"task_id: {task_id}"
        )

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering model retraining: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger model retraining: {str(e)}",
        ) from e


@router.post("/rollback", tags=["Model Versions"])
async def rollback_model_version(
    request: Request,
    rollback_data: ModelRollbackRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Rollback to a previous model version.

    This endpoint rolls back the active model to a specified previous version,
    deactivating the current version and activating the target version.

    Args:
        request: FastAPI request object
        rollback_data: Rollback request containing model name and target version
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
        ...     "http://localhost:8000/api/model-versions/rollback",
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
            f"Rolling back model {rollback_data.model_name} to version {rollback_data.target_version}"
        )

        # Validate model name
        if not rollback_data.model_name or len(rollback_data.model_name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Model name cannot be empty",
            )

        # Validate target version
        if not rollback_data.target_version or len(rollback_data.target_version.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Target version cannot be empty",
            )

        # Find the target version to rollback to
        target_query = select(MLModelVersion).where(
            MLModelVersion.model_name == rollback_data.model_name,
            MLModelVersion.version == rollback_data.target_version
        )
        target_result = await db.execute(target_query)
        target_version = target_result.scalar_one_or_none()

        if not target_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target version {rollback_data.target_version} not found for model {rollback_data.model_name}",
            )

        # Find the currently active version
        current_query = select(MLModelVersion).where(
            MLModelVersion.model_name == rollback_data.model_name,
            MLModelVersion.is_active == True
        )
        current_result = await db.execute(current_query)
        current_version = current_result.scalar_one_or_none()

        previous_version_str = None
        if current_version:
            previous_version_str = current_version.version
            # Deactivate the current version
            current_version.is_active = False

        # Activate the target version
        target_version.is_active = True

        await db.commit()
        await db.refresh(target_version)

        response_data = {
            "message": "Model rolled back successfully",
            "model_name": rollback_data.model_name,
            "target_version": rollback_data.target_version,
            "previous_version": previous_version_str,
        }

        logger.info(
            f"Model {rollback_data.model_name} rolled back to version {rollback_data.target_version}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rolling back model version: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback model version: {str(e)}",
        ) from e
