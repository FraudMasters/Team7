"""
Billing and usage tracking endpoints.

This module provides endpoints for tracking agency usage metrics and generating
billing reports, including API calls, resume processing, candidate management,
and other billable activities.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.agency import Agency
from middleware.tenant_context import get_agency_context

logger = logging.getLogger(__name__)

router = APIRouter()


class UsageMetrics(BaseModel):
    """Usage metrics for billing calculations."""

    api_calls: int = Field(..., description="Total number of API calls")
    resumes_processed: int = Field(..., description="Number of resumes processed")
    candidates_managed: int = Field(..., description="Number of candidates managed")
    job_postings: int = Field(..., description="Number of job postings created")
    matches_generated: int = Field(..., description="Number of candidate-job matches generated")
    storage_used_mb: float = Field(..., description="Storage used in megabytes")


class BillingPeriod(BaseModel):
    """Billing period information."""

    start_date: str = Field(..., description="Period start date (ISO 8601 format)")
    end_date: str = Field(..., description="Period end date (ISO 8601 format)")
    days_in_period: int = Field(..., description="Number of days in billing period")


class CostBreakdown(BaseModel):
    """Breakdown of costs by service."""

    api_calls_cost: float = Field(..., description="Cost for API calls")
    resume_processing_cost: float = Field(..., description="Cost for resume processing")
    storage_cost: float = Field(..., description="Cost for storage")
    candidate_management_cost: float = Field(..., description="Cost for candidate management")
    total_cost: float = Field(..., description="Total cost for the period")
    currency: str = Field(default="USD", description="Currency code")


class UsageResponse(BaseModel):
    """Response model for usage tracking."""

    agency_id: str = Field(..., description="Agency UUID")
    agency_name: str = Field(..., description="Agency name")
    billing_period: BillingPeriod = Field(..., description="Billing period information")
    usage_metrics: UsageMetrics = Field(..., description="Usage metrics for the period")
    cost_breakdown: CostBreakdown = Field(..., description="Cost breakdown by service")
    tier: str = Field(..., description="Current billing tier (e.g., 'starter', 'professional', 'enterprise')")


class BillingSummary(BaseModel):
    """Summary of billing information."""

    total_agencies: int = Field(..., description="Total number of agencies")
    total_revenue: float = Field(..., description="Total revenue for the period")
    currency: str = Field(default="USD", description="Currency code")
    top_agencies_by_usage: list = Field(..., description="Top agencies by usage")


@router.get(
    "/usage",
    response_model=UsageResponse,
    tags=["Billing"],
)
async def get_usage_metrics(
    request: Request,
    agency_id: str = Query(..., description="Agency UUID"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get usage metrics and billing information for an agency.

    This endpoint provides detailed usage tracking and cost breakdown for a specific
    agency over a given billing period. It tracks API calls, resume processing,
    candidate management, and other billable activities.

    Args:
        agency_id: Agency UUID (required)
        start_date: Optional start date for the billing period (ISO 8601 format)
        end_date: Optional end date for the billing period (ISO 8601 format)

    Returns:
        JSON response with usage metrics and cost breakdown

    Raises:
        HTTPException(400): If agency_id is invalid
        HTTPException(404): If agency not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/billing/usage",
        ...     params={"agency_id": "123e4567-e89b-12d3-a456-426614174000"}
        ... )
        >>> response.json()
        {
            "agency_id": "123e4567-e89b-12d3-a456-426614174000",
            "agency_name": "Tech Recruiters Inc.",
            "billing_period": {
                "start_date": "2026-03-01T00:00:00Z",
                "end_date": "2026-03-31T23:59:59Z",
                "days_in_period": 31
            },
            "usage_metrics": {
                "api_calls": 15420,
                "resumes_processed": 342,
                "candidates_managed": 128,
                "job_postings": 45,
                "matches_generated": 1876,
                "storage_used_mb": 2450.5
            },
            "cost_breakdown": {
                "api_calls_cost": 154.20,
                "resume_processing_cost": 342.00,
                "storage_cost": 24.50,
                "candidate_management_cost": 128.00,
                "total_cost": 648.70,
                "currency": "USD"
            },
            "tier": "professional"
        }
    """
    try:
        logger.info(
            f"Fetching usage metrics for agency_id: {agency_id}, "
            f"start_date: {start_date}, end_date: {end_date}"
        )

        # Validate agency exists
        agency_result = await db.execute(
            select(Agency).where(Agency.id == agency_id)
        )
        agency = agency_result.scalars().first()

        if not agency:
            raise HTTPException(
                status_code=404,
                detail=f"Agency not found: {agency_id}"
            )

        # Get agency context from headers for authorization
        agency_context = get_agency_context(request)

        # TODO: Add authentication/authorization check
        # Verify that the current user has access to this agency
        # For now, we log the agency context but don't enforce it
        # until authentication is implemented
        if agency_context:
            logger.info(f"Agency context from headers: {agency_context}")
            if agency_context != agency_id:
                logger.warning(
                    f"Agency context mismatch: header={agency_context}, requested={agency_id}"
                )

        # Validate agency_id format (basic validation)
        if not agency_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="agency_id is required",
            )

        # Set default billing period if not provided
        if not start_date:
            start_date = "2026-03-01T00:00:00Z"
        if not end_date:
            end_date = "2026-03-31T23:59:59Z"

        # Calculate days in period
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            days_in_period = (end - start).days + 1
        except Exception as e:
            logger.warning(f"Error parsing dates, using default: {e}")
            days_in_period = 31

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        response_data = {
            "agency_id": agency_id,
            "agency_name": "Tech Recruiters Inc.",
            "billing_period": {
                "start_date": start_date,
                "end_date": end_date,
                "days_in_period": days_in_period,
            },
            "usage_metrics": {
                "api_calls": 15420,
                "resumes_processed": 342,
                "candidates_managed": 128,
                "job_postings": 45,
                "matches_generated": 1876,
                "storage_used_mb": 2450.5,
            },
            "cost_breakdown": {
                "api_calls_cost": 154.20,
                "resume_processing_cost": 342.00,
                "storage_cost": 24.50,
                "candidate_management_cost": 128.00,
                "total_cost": 648.70,
                "currency": "USD",
            },
            "tier": "professional",
        }

        logger.info(f"Usage metrics retrieved successfully for agency_id: {agency_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTPExceptions without wrapping
        raise
    except Exception as e:
        logger.error(f"Error retrieving usage metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage metrics: {str(e)}",
        ) from e


@router.get(
    "/summary",
    response_model=BillingSummary,
    tags=["Billing"],
)
async def get_billing_summary(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
) -> JSONResponse:
    """
    Get billing summary across all agencies.

    This endpoint provides an aggregate view of billing information across all
    agencies, including total revenue and top agencies by usage.

    Args:
        start_date: Optional start date for the billing period (ISO 8601 format)
        end_date: Optional end date for the billing period (ISO 8601 format)

    Returns:
        JSON response with billing summary

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/billing/summary")
        >>> response.json()
        {
            "total_agencies": 45,
            "total_revenue": 29235.50,
            "currency": "USD",
            "top_agencies_by_usage": [
                {"agency_id": "123...", "agency_name": "Tech Recruiters", "total_cost": 1250.00},
                {"agency_id": "456...", "agency_name": "HR Solutions", "total_cost": 980.50}
            ]
        }
    """
    try:
        logger.info(
            f"Fetching billing summary - start_date: {start_date}, end_date: {end_date}"
        )

        # For now, return placeholder response
        response_data = {
            "total_agencies": 45,
            "total_revenue": 29235.50,
            "currency": "USD",
            "top_agencies_by_usage": [
                {
                    "agency_id": "123e4567-e89b-12d3-a456-426614174000",
                    "agency_name": "Tech Recruiters Inc.",
                    "total_cost": 1250.00,
                },
                {
                    "agency_id": "456e7890-e89b-12d3-a456-426614174001",
                    "agency_name": "HR Solutions Group",
                    "total_cost": 980.50,
                },
                {
                    "agency_id": "789e0123-e89b-12d3-a456-426614174002",
                    "agency_name": "Global Talent Partners",
                    "total_cost": 875.25,
                },
            ],
        }

        logger.info("Billing summary retrieved successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving billing summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve billing summary: {str(e)}",
        ) from e
