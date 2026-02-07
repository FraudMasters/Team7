"""
Data processing agreement management endpoints.

This module provides endpoints for managing GDPR data processing agreements,
including CRUD operations for creating, reading, updating, and deleting
agreements with third-party data processors.
"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

router = APIRouter()


class ProcessingAgreementCreate(BaseModel):
    """Request model for creating a data processing agreement."""

    organization_id: str = Field(..., description="Organization identifier (data controller)")
    vendor_name: str = Field(..., description="Name of the third-party data processor")
    vendor_contact_email: str = Field(..., description="Contact email for the data processor")
    purpose_description: str = Field(..., description="Description of processing purpose")
    data_categories: List[str] = Field(..., description="Categories of personal data processed (e.g., contact_info, employment_history)")
    processing_activities: List[str] = Field(..., description="List of processing activities (e.g., storage, analysis, backup)")
    retention_period: str = Field(..., description="Data retention period (e.g., 2 years, 90 days)")
    security_measures: str = Field(..., description="Description of technical and organizational security measures")
    data_location: str = Field(..., description="Location where data will be processed/stored (e.g., EU, US)")
    subprocessing_allowed: bool = Field(False, description="Whether the processor may engage sub-processors")
    review_date: Optional[str] = Field(None, description="Next review date (ISO 8601 format)")
    created_by: Optional[str] = Field(None, description="User ID who is creating this agreement")


class ProcessingAgreementUpdate(BaseModel):
    """Request model for updating a data processing agreement."""

    vendor_name: Optional[str] = Field(None, description="Name of the third-party data processor")
    vendor_contact_email: Optional[str] = Field(None, description="Contact email for the data processor")
    purpose_description: Optional[str] = Field(None, description="Description of processing purpose")
    data_categories: Optional[List[str]] = Field(None, description="Categories of personal data processed")
    processing_activities: Optional[List[str]] = Field(None, description="List of processing activities")
    retention_period: Optional[str] = Field(None, description="Data retention period")
    security_measures: Optional[str] = Field(None, description="Description of security measures")
    data_location: Optional[str] = Field(None, description="Location where data will be processed/stored")
    subprocessing_allowed: Optional[bool] = Field(None, description="Whether the processor may engage sub-processors")
    review_date: Optional[str] = Field(None, description="Next review date (ISO 8601 format)")
    status: Optional[str] = Field(None, description="Agreement status (active, expired, suspended)")


class ProcessingAgreementResponse(BaseModel):
    """Response model for a single processing agreement."""

    id: str = Field(..., description="Unique identifier for the agreement")
    organization_id: str = Field(..., description="Organization identifier")
    vendor_name: str = Field(..., description="Name of the data processor")
    vendor_contact_email: str = Field(..., description="Contact email for the data processor")
    purpose_description: str = Field(..., description="Description of processing purpose")
    data_categories: List[str] = Field(..., description="Categories of personal data processed")
    processing_activities: List[str] = Field(..., description="List of processing activities")
    retention_period: str = Field(..., description="Data retention period")
    security_measures: str = Field(..., description="Description of security measures")
    data_location: str = Field(..., description="Location where data will be processed/stored")
    subprocessing_allowed: bool = Field(..., description="Whether the processor may engage sub-processors")
    status: str = Field(..., description="Agreement status (active, expired, suspended)")
    agreement_date: str = Field(..., description="Agreement creation/signing date")
    review_date: Optional[str] = Field(None, description="Next review date")
    created_by: Optional[str] = Field(None, description="User ID who created this agreement")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ProcessingAgreementListResponse(BaseModel):
    """Response model for listing processing agreements."""

    organization_id: Optional[str] = Field(None, description="Organization identifier (if filtered)")
    status: Optional[str] = Field(None, description="Status filter (if applied)")
    agreements: List[ProcessingAgreementResponse] = Field(..., description="List of processing agreements")
    total_count: int = Field(..., description="Total number of agreements")


@router.post(
    "/",
    response_model=ProcessingAgreementResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Processing Agreements"],
)
async def create_processing_agreement(request: ProcessingAgreementCreate) -> JSONResponse:
    """
    Create a data processing agreement.

    This endpoint creates a new GDPR data processing agreement with a third-party
    processor, documenting the purposes, categories of data, and security measures.

    Args:
        request: Create request with agreement details

    Returns:
        JSON response with created processing agreement

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "organization_id": "org123",
        ...     "vendor_name": "Cloud Storage Inc.",
        ...     "vendor_contact_email": "compliance@cloudstorage.com",
        ...     "purpose_description": "Secure cloud storage for candidate documents",
        ...     "data_categories": ["contact_info", "employment_history", "documents"],
        ...     "processing_activities": ["storage", "backup", "retrieval"],
        ...     "retention_period": "2 years",
        ...     "security_measures": "Encryption at rest and in transit, ISO 27001 certified",
        ...     "data_location": "EU",
        ...     "subprocessing_allowed": False,
        ...     "review_date": "2025-01-25T00:00:00Z",
        ...     "created_by": "user456"
        ... }
        >>> response = requests.post("http://localhost:8000/api/processing-agreements/", json=data)
        >>> response.json()
        {
            "id": "pa-123",
            "organization_id": "org123",
            "vendor_name": "Cloud Storage Inc.",
            ...
        }
    """
    try:
        logger.info(f"Creating processing agreement with vendor: {request.vendor_name}")

        # Validate organization_id
        if not request.organization_id or len(request.organization_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Organization ID cannot be empty",
            )

        # Validate vendor_name
        if not request.vendor_name or len(request.vendor_name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Vendor name cannot be empty",
            )

        # Validate vendor_contact_email
        if not request.vendor_contact_email or len(request.vendor_contact_email.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Vendor contact email cannot be empty",
            )

        # Validate email format
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, request.vendor_contact_email):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid vendor contact email format",
            )

        # Validate purpose_description
        if not request.purpose_description or len(request.purpose_description.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Purpose description cannot be empty",
            )

        # Validate data_categories
        if not request.data_categories or len(request.data_categories) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one data category must be provided",
            )

        # Validate processing_activities
        if not request.processing_activities or len(request.processing_activities) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one processing activity must be provided",
            )

        # Validate retention_period
        if not request.retention_period or len(request.retention_period.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Retention period cannot be empty",
            )

        # Validate security_measures
        if not request.security_measures or len(request.security_measures.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Security measures description cannot be empty",
            )

        # Validate data_location
        if not request.data_location or len(request.data_location.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Data location cannot be empty",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        from datetime import datetime
        import uuid
        now = datetime.utcnow()
        now_iso = now.isoformat() + "Z"

        agreement_id = f"pa-{uuid.uuid4().hex[:8]}"

        response_data = {
            "id": agreement_id,
            "organization_id": request.organization_id,
            "vendor_name": request.vendor_name,
            "vendor_contact_email": request.vendor_contact_email,
            "purpose_description": request.purpose_description,
            "data_categories": request.data_categories,
            "processing_activities": request.processing_activities,
            "retention_period": request.retention_period,
            "security_measures": request.security_measures,
            "data_location": request.data_location,
            "subprocessing_allowed": request.subprocessing_allowed,
            "status": "active",
            "agreement_date": now_iso,
            "review_date": request.review_date,
            "created_by": request.created_by,
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        logger.info(f"Created processing agreement '{request.vendor_name}' with ID: {agreement_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating processing agreement: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create processing agreement: {str(e)}",
        ) from e


@router.get("/", tags=["Processing Agreements"])
async def list_processing_agreements(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    status: Optional[str] = Query(None, description="Filter by status (active, expired, suspended)"),
    data_location: Optional[str] = Query(None, description="Filter by data location"),
) -> JSONResponse:
    """
    List data processing agreements with optional filters.

    Args:
        organization_id: Optional organization ID filter
        status: Optional status filter
        data_location: Optional data location filter

    Returns:
        JSON response with list of processing agreements

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/processing-agreements/?organization_id=org123")
        >>> response.json()
    """
    try:
        logger.info(f"Listing processing agreements with filters - organization_id: {organization_id}, status: {status}, data_location: {data_location}")

        # Validate status if provided
        if status and status not in ["active", "expired", "suspended"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Status must be one of: active, expired, suspended",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        response_data = {
            "organization_id": organization_id,
            "status": status,
            "agreements": [],
            "total_count": 0,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing processing agreements: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list processing agreements: {str(e)}",
        ) from e


@router.get("/{agreement_id}", tags=["Processing Agreements"])
async def get_processing_agreement(agreement_id: str) -> JSONResponse:
    """
    Get a specific data processing agreement by ID.

    Args:
        agreement_id: Unique identifier of the agreement

    Returns:
        JSON response with processing agreement details

    Raises:
        HTTPException(404): If agreement is not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/processing-agreements/pa-123")
        >>> response.json()
    """
    try:
        logger.info(f"Getting processing agreement: {agreement_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": agreement_id,
                "organization_id": "org123",
                "vendor_name": "Cloud Storage Inc.",
                "vendor_contact_email": "compliance@cloudstorage.com",
                "purpose_description": "Secure cloud storage for candidate documents",
                "data_categories": ["contact_info", "employment_history", "documents"],
                "processing_activities": ["storage", "backup", "retrieval"],
                "retention_period": "2 years",
                "security_measures": "Encryption at rest and in transit, ISO 27001 certified",
                "data_location": "EU",
                "subprocessing_allowed": False,
                "status": "active",
                "agreement_date": "2024-01-25T00:00:00Z",
                "review_date": "2025-01-25T00:00:00Z",
                "created_by": "user456",
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": "2024-01-25T00:00:00Z",
            },
        )

    except Exception as e:
        logger.error(f"Error getting processing agreement: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing agreement: {str(e)}",
        ) from e


@router.put("/{agreement_id}", tags=["Processing Agreements"])
async def update_processing_agreement(
    agreement_id: str, request: ProcessingAgreementUpdate
) -> JSONResponse:
    """
    Update a data processing agreement.

    Args:
        agreement_id: Unique identifier of the agreement
        request: Update request with fields to modify

    Returns:
        JSON response with updated processing agreement

    Raises:
        HTTPException(404): If agreement is not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"retention_period": "3 years", "status": "active"}
        >>> response = requests.put(
        ...     "http://localhost:8000/api/processing-agreements/pa-123",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Updating processing agreement: {agreement_id}")

        # Validate email format if provided
        if request.vendor_contact_email:
            import re
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_pattern, request.vendor_contact_email):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid vendor contact email format",
                )

        # Validate status if provided
        if request.status and request.status not in ["active", "expired", "suspended"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Status must be one of: active, expired, suspended",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        from datetime import datetime
        now = datetime.utcnow().isoformat() + "Z"

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": agreement_id,
                "organization_id": "org123",
                "vendor_name": request.vendor_name or "Cloud Storage Inc.",
                "vendor_contact_email": request.vendor_contact_email or "compliance@cloudstorage.com",
                "purpose_description": request.purpose_description or "Secure cloud storage for candidate documents",
                "data_categories": request.data_categories or ["contact_info", "documents"],
                "processing_activities": request.processing_activities or ["storage"],
                "retention_period": request.retention_period or "2 years",
                "security_measures": request.security_measures or "Encryption at rest and in transit",
                "data_location": request.data_location or "EU",
                "subprocessing_allowed": request.subprocessing_allowed if request.subprocessing_allowed is not None else False,
                "status": request.status or "active",
                "agreement_date": "2024-01-25T00:00:00Z",
                "review_date": request.review_date,
                "created_by": "user456",
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": now,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating processing agreement: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update processing agreement: {str(e)}",
        ) from e


@router.delete("/{agreement_id}", tags=["Processing Agreements"])
async def delete_processing_agreement(agreement_id: str) -> JSONResponse:
    """
    Delete a data processing agreement.

    Args:
        agreement_id: Unique identifier of the agreement

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If agreement is not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/processing-agreements/pa-123")
        >>> response.json()
        {"message": "Processing agreement deleted successfully"}
    """
    try:
        logger.info(f"Deleting processing agreement: {agreement_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Processing agreement {agreement_id} deleted successfully"},
        )

    except Exception as e:
        logger.error(f"Error deleting processing agreement: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete processing agreement: {str(e)}",
        ) from e


@router.delete("/organization/{organization_id}", tags=["Processing Agreements"])
async def delete_processing_agreements_by_organization(organization_id: str) -> JSONResponse:
    """
    Delete all data processing agreements for a specific organization.

    Args:
        organization_id: Organization identifier to delete agreements for

    Returns:
        JSON response confirming deletion with count

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/processing-agreements/organization/org123")
        >>> response.json()
        {"message": "Deleted 5 processing agreements for organization: org123"}
    """
    try:
        logger.info(f"Deleting all processing agreements for organization: {organization_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Deleted processing agreements for organization: {organization_id}", "deleted_count": 0},
        )

    except Exception as e:
        logger.error(f"Error deleting processing agreements for organization {organization_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete processing agreements: {str(e)}",
        ) from e
