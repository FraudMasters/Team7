"""
Agency analytics endpoints.

This module provides endpoints for retrieving cross-client analytics metrics
for recruitment agencies, including aggregated performance across multiple
client tenants, resource utilization, and agency-level KPIs.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class ClientMetrics(BaseModel):
    """Per-client metrics summary."""

    total_clients: int = Field(..., description="Total number of active client tenants")
    clients_with_active_roles: int = Field(..., description="Clients with open positions")
    avg_roles_per_client: float = Field(..., description="Average open roles per client")


class CandidateMetrics(BaseModel):
    """Cross-client candidate metrics."""

    total_candidates: int = Field(..., description="Total candidates across all clients")
    candidates_this_month: int = Field(..., description="New candidates added this month")
    candidates_this_week: int = Field(..., description="New candidates added this week")
    avg_candidates_per_client: float = Field(..., description="Average candidates per client")


class PlacementMetrics(BaseModel):
    """Placement and hiring metrics."""

    total_placements: int = Field(..., description="Total successful placements")
    placements_this_month: int = Field(..., description="Placements made this month")
    placements_this_week: int = Field(..., description="Placements made this week")
    avg_time_to_placement_days: float = Field(..., description="Average time-to-placement in days")
    placement_rate: float = Field(..., description="Overall placement success rate (0-1)")


class ResourceUtilization(BaseModel):
    """Agency resource utilization metrics."""

    total_recruiters: int = Field(..., description="Total number of recruiters")
    avg_roles_per_recruiter: float = Field(..., description="Average open roles per recruiter")
    avg_candidates_per_recruiter: float = Field(..., description="Average candidates per recruiter")
    recruiter_utilization_rate: float = Field(..., description="Recruiter utilization rate (0-1)")


class AgencyAnalyticsSummary(BaseModel):
    """Response model for agency analytics summary."""

    agency_id: str = Field(..., description="Agency identifier")
    clients: ClientMetrics = Field(..., description="Client metrics summary")
    candidates: CandidateMetrics = Field(..., description="Candidate metrics across clients")
    placements: PlacementMetrics = Field(..., description="Placement and hiring metrics")
    resources: ResourceUtilization = Field(..., description="Resource utilization metrics")


@router.get(
    "/summary",
    response_model=AgencyAnalyticsSummary,
    tags=["Agency Analytics"],
)
async def get_agency_analytics_summary(
    agency_id: str = Query(..., description="Agency identifier for filtering metrics"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
) -> JSONResponse:
    """
    Get agency analytics summary with cross-client metrics.

    This endpoint provides aggregated analytics across all client tenants
    managed by a recruitment agency. It includes client metrics, candidate
    metrics, placement statistics, and resource utilization data to help
    agency owners monitor performance and optimize operations.

    Args:
        agency_id: Agency identifier for filtering metrics
        start_date: Optional start date for filtering metrics (ISO 8601 format)
        end_date: Optional end date for filtering metrics (ISO 8601 format)

    Returns:
        JSON response with agency analytics including client, candidate,
        placement, and resource utilization metrics

    Raises:
        HTTPException(400): If agency_id is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/agency-analytics/summary?agency_id=test-uuid")
        >>> response.json()
        {
            "agency_id": "test-uuid",
            "clients": {
                "total_clients": 15,
                "clients_with_active_roles": 12,
                "avg_roles_per_client": 8.3
            },
            "candidates": {
                "total_candidates": 1850,
                "candidates_this_month": 245,
                "candidates_this_week": 58,
                "avg_candidates_per_client": 123.3
            },
            "placements": {
                "total_placements": 342,
                "placements_this_month": 28,
                "placements_this_week": 6,
                "avg_time_to_placement_days": 24.5,
                "placement_rate": 0.185
            },
            "resources": {
                "total_recruiters": 25,
                "avg_roles_per_recruiter": 5.0,
                "avg_candidates_per_recruiter": 74.0,
                "recruiter_utilization_rate": 0.82
            }
        }
    """
    try:
        logger.info(
            f"Fetching agency analytics summary - agency_id: {agency_id}, "
            f"start_date: {start_date}, end_date: {end_date}"
        )

        # Validate agency_id
        if not agency_id or not agency_id.strip():
            logger.warning("Invalid agency_id provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid agency_id: must be a non-empty string",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        response_data = {
            "agency_id": agency_id,
            "clients": {
                "total_clients": 15,
                "clients_with_active_roles": 12,
                "avg_roles_per_client": 8.3,
            },
            "candidates": {
                "total_candidates": 1850,
                "candidates_this_month": 245,
                "candidates_this_week": 58,
                "avg_candidates_per_client": 123.3,
            },
            "placements": {
                "total_placements": 342,
                "placements_this_month": 28,
                "placements_this_week": 6,
                "avg_time_to_placement_days": 24.5,
                "placement_rate": 0.185,
            },
            "resources": {
                "total_recruiters": 25,
                "avg_roles_per_recruiter": 5.0,
                "avg_candidates_per_recruiter": 74.0,
                "recruiter_utilization_rate": 0.82,
            },
        }

        logger.info(f"Agency analytics summary retrieved successfully for agency {agency_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving agency analytics summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve agency analytics summary: {str(e)}",
        ) from e
