"""
API usage analytics endpoints.

This module provides endpoints for querying and analyzing API usage metrics:
- API usage statistics (request counts, response times, error rates)
- Detailed API usage logs with filtering and pagination
- Usage breakdown by endpoint, status, and API key
- Time-series usage analytics for monitoring and alerting

These endpoints help track API consumption patterns, identify abuse,
and optimize rate limiting policies.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.api_usage import APIUsage, APIRequestStatus
from models.api_key import APIKey

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class APIUsageStatistics(BaseModel):
    """API usage statistics summary."""

    total_requests: int = Field(..., description="Total number of API requests")
    successful_requests: int = Field(..., description="Number of successful requests (2xx)")
    failed_requests: int = Field(..., description="Number of failed requests (4xx, 5xx)")
    rate_limited_requests: int = Field(..., description="Number of rate-limited requests (429)")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    min_response_time_ms: Optional[int] = Field(None, description="Minimum response time")
    max_response_time_ms: Optional[int] = Field(None, description="Maximum response time")
    unique_api_keys: int = Field(..., description="Number of unique API keys used")
    unique_endpoints: int = Field(..., description="Number of unique endpoints accessed")


class APIUsageByEndpoint(BaseModel):
    """API usage breakdown by endpoint."""

    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field(..., description="HTTP method")
    request_count: int = Field(..., description="Number of requests to this endpoint")
    success_rate: float = Field(..., description="Success rate (0-1)")
    avg_response_time_ms: float = Field(..., description="Average response time")


class APIUsageByStatus(BaseModel):
    """API usage breakdown by status."""

    status: str = Field(..., description="Request status (success, rate_limited, etc.)")
    status_code: int = Field(..., description="HTTP status code")
    request_count: int = Field(..., description="Number of requests with this status")
    percentage: float = Field(..., description="Percentage of total requests (0-100)")


class APIUsageLogItem(BaseModel):
    """Individual API usage log entry."""

    id: str = Field(..., description="Usage record UUID")
    api_key_id: str = Field(..., description="API key UUID")
    api_key_prefix: Optional[str] = Field(None, description="API key prefix for identification")
    endpoint: str = Field(..., description="API endpoint accessed")
    method: str = Field(..., description="HTTP method used")
    status: str = Field(..., description="Request status")
    status_code: int = Field(..., description="HTTP status code")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    rate_limit_remaining: Optional[int] = Field(None, description="Requests remaining in rate limit")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    created_at: str = Field(..., description="Timestamp when request was made")


class APIUsageStatisticsResponse(BaseModel):
    """Response model for API usage statistics."""

    statistics: APIUsageStatistics = Field(..., description="Overall usage statistics")
    by_endpoint: List[APIUsageByEndpoint] = Field(..., description="Usage breakdown by endpoint")
    by_status: List[APIUsageByStatus] = Field(..., description="Usage breakdown by status")
    date_range: Dict[str, Optional[str]] = Field(..., description="Date range for the statistics")


@router.get(
    "/statistics",
    response_model=APIUsageStatisticsResponse,
    tags=["API Usage"],
)
async def get_api_usage_statistics(
    request: Request,
    api_key_id: Optional[str] = Query(None, description="Filter by API key UUID"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get API usage statistics and analytics.

    Returns comprehensive statistics about API usage, including request counts,
    response times, error rates, and breakdowns by endpoint and status.
    This endpoint is useful for monitoring API health, identifying trends,
    and optimizing rate limiting policies.

    Args:
        request: FastAPI request object
        api_key_id: Optional filter by specific API key UUID
        start_date: Optional start date for filtering (ISO 8601 format)
        end_date: Optional end date for filtering (ISO 8601 format)
        db: Database session

    Returns:
        JSON response with usage statistics, endpoint breakdown, and status breakdown

    Raises:
        HTTPException(400): If date format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all usage statistics
        >>> response = requests.get("/api/api-usage/statistics")
        >>> # Get statistics for a specific API key
        >>> response = requests.get(f"/api/api-usage/statistics?api_key_id={key_id}")
        >>> # Get statistics for a date range
        >>> response = requests.get(
        ...     "/api/api-usage/statistics"
        ...     "?start_date=2026-03-01T00:00:00Z"
        ...     "&end_date=2026-03-21T23:59:59Z"
        ... )
        >>> stats = response.json()
    """
    try:
        logger.info(
            f"Fetching API usage statistics - "
            f"api_key_id: {api_key_id}, start_date: {start_date}, end_date: {end_date}"
        )

        # Build base query
        conditions = []

        # Add API key filter
        if api_key_id:
            try:
                key_uuid = UUID(api_key_id)
                conditions.append(APIUsage.api_key_id == key_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid API key ID format: {api_key_id}",
                )

        # Add date filters
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                conditions.append(APIUsage.created_at >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                )

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                conditions.append(APIUsage.created_at <= end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                )

        # Get overall statistics
        stats_query = select(
            func.count(APIUsage.id).label("total_requests"),
            func.count(APIUsage.id).filter(
                APIUsage.status == APIRequestStatus.SUCCESS
            ).label("successful_requests"),
            func.count(APIUsage.id).filter(
                APIUsage.status != APIRequestStatus.SUCCESS
            ).label("failed_requests"),
            func.count(APIUsage.id).filter(
                APIUsage.status == APIRequestStatus.RATE_LIMITED
            ).label("rate_limited_requests"),
            func.avg(APIUsage.response_time_ms).label("avg_response_time_ms"),
            func.min(APIUsage.response_time_ms).label("min_response_time_ms"),
            func.max(APIUsage.response_time_ms).label("max_response_time_ms"),
            func.count(func.distinct(APIUsage.api_key_id)).label("unique_api_keys"),
            func.count(func.distinct(APIUsage.endpoint)).label("unique_endpoints"),
        )

        if conditions:
            stats_query = stats_query.where(and_(*conditions))

        stats_result = await db.execute(stats_query)
        stats_row = stats_result.first()

        # Get usage by endpoint
        endpoint_query = select(
            APIUsage.endpoint,
            APIUsage.method,
            func.count(APIUsage.id).label("request_count"),
            (
                func.count(APIUsage.id).filter(
                    APIUsage.status == APIRequestStatus.SUCCESS
                ).cast(float)
                / func.count(APIUsage.id)
            ).label("success_rate"),
            func.avg(APIUsage.response_time_ms).label("avg_response_time_ms"),
        ).group_by(APIUsage.endpoint, APIUsage.method).order_by(
            func.count(APIUsage.id).desc()
        ).limit(10)

        if conditions:
            endpoint_query = endpoint_query.where(and_(*conditions))

        endpoint_result = await db.execute(endpoint_query)
        endpoint_rows = endpoint_result.all()

        # Get usage by status
        status_query = select(
            APIUsage.status,
            APIUsage.status_code,
            func.count(APIUsage.id).label("request_count"),
        ).group_by(APIUsage.status, APIUsage.status_code).order_by(
            func.count(APIUsage.id).desc()
        )

        if conditions:
            status_query = status_query.where(and_(*conditions))

        status_result = await db.execute(status_query)
        status_rows = status_result.all()

        # Calculate total for percentage
        total = stats_row.total_requests if stats_row and stats_row.total_requests else 0

        # Build response
        response_data = {
            "statistics": {
                "total_requests": stats_row.total_requests if stats_row else 0,
                "successful_requests": stats_row.successful_requests if stats_row else 0,
                "failed_requests": stats_row.failed_requests if stats_row else 0,
                "rate_limited_requests": stats_row.rate_limited_requests if stats_row else 0,
                "avg_response_time_ms": round(stats_row.avg_response_time_ms, 2)
                if stats_row and stats_row.avg_response_time_ms
                else 0.0,
                "min_response_time_ms": stats_row.min_response_time_ms if stats_row else None,
                "max_response_time_ms": stats_row.max_response_time_ms if stats_row else None,
                "unique_api_keys": stats_row.unique_api_keys if stats_row else 0,
                "unique_endpoints": stats_row.unique_endpoints if stats_row else 0,
            },
            "by_endpoint": [
                {
                    "endpoint": row.endpoint,
                    "method": row.method,
                    "request_count": row.request_count,
                    "success_rate": round(row.success_rate if row.success_rate else 0.0, 4),
                    "avg_response_time_ms": round(
                        row.avg_response_time_ms if row.avg_response_time_ms else 0.0, 2
                    ),
                }
                for row in endpoint_rows
            ],
            "by_status": [
                {
                    "status": row.status.value if isinstance(row.status, APIRequestStatus) else row.status,
                    "status_code": row.status_code,
                    "request_count": row.request_count,
                    "percentage": round(
                        (row.request_count / total * 100) if total > 0 else 0.0, 2
                    ),
                }
                for row in status_rows
            ],
            "date_range": {
                "start_date": start_date,
                "end_date": end_date,
            },
        }

        logger.info(
            f"Retrieved API usage statistics: "
            f"{response_data['statistics']['total_requests']} total requests"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving API usage statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API usage statistics: {str(e)}",
        ) from e


@router.get(
    "/logs",
    response_model=List[APIUsageLogItem],
    tags=["API Usage"],
)
async def get_api_usage_logs(
    request: Request,
    api_key_id: Optional[str] = Query(None, description="Filter by API key UUID"),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint path"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    status: Optional[str] = Query(None, description="Filter by request status"),
    status_code: Optional[int] = Query(None, description="Filter by HTTP status code"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get detailed API usage logs.

    Returns a paginated list of individual API usage records with detailed information
    about each request. Supports filtering by API key, endpoint, status, and date range.

    Args:
        request: FastAPI request object
        api_key_id: Optional filter by API key UUID
        endpoint: Optional filter by endpoint path
        method: Optional filter by HTTP method (GET, POST, etc.)
        status: Optional filter by request status (success, rate_limited, etc.)
        status_code: Optional filter by HTTP status code
        start_date: Optional start date for filtering (ISO 8601 format)
        end_date: Optional end date for filtering (ISO 8601 format)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of API usage log entries

    Raises:
        HTTPException(400): If parameters are invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get recent API usage logs
        >>> response = requests.get("/api/api-usage/logs?limit=50")
        >>> # Get logs for a specific API key
        >>> response = requests.get(f"/api/api-usage/logs?api_key_id={key_id}")
        >>> # Get rate-limited requests
        >>> response = requests.get("/api/api-usage/logs?status=rate_limited")
        >>> # Get logs for a specific endpoint
        >>> response = requests.get("/api/api-usage/logs?endpoint=/api/candidates")
        >>> logs = response.json()
    """
    try:
        logger.info(
            f"Fetching API usage logs - "
            f"api_key_id: {api_key_id}, endpoint: {endpoint}, "
            f"status: {status}, skip: {skip}, limit: {limit}"
        )

        # Build query
        query = select(APIUsage, APIKey.key_prefix).join(
            APIKey, APIUsage.api_key_id == APIKey.id, isouter=True
        )

        conditions = []

        # Add filters
        if api_key_id:
            try:
                key_uuid = UUID(api_key_id)
                conditions.append(APIUsage.api_key_id == key_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid API key ID format: {api_key_id}",
                )

        if endpoint:
            conditions.append(APIUsage.endpoint == endpoint)

        if method:
            conditions.append(APIUsage.method == method.upper())

        if status:
            # Validate status
            try:
                status_enum = APIRequestStatus(status)
                conditions.append(APIUsage.status == status_enum)
            except ValueError:
                valid_statuses = [s.value for s in APIRequestStatus]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}. Valid values: {', '.join(valid_statuses)}",
                )

        if status_code:
            conditions.append(APIUsage.status_code == status_code)

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                conditions.append(APIUsage.created_at >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                )

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                conditions.append(APIUsage.created_at <= end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                )

        # Apply filters
        if conditions:
            query = query.where(and_(*conditions))

        # Order by most recent
        query = query.order_by(APIUsage.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        rows = result.all()

        # Convert to response format
        logs_list = []
        for usage, key_prefix in rows:
            logs_list.append({
                "id": str(usage.id),
                "api_key_id": str(usage.api_key_id),
                "api_key_prefix": key_prefix,
                "endpoint": usage.endpoint,
                "method": usage.method,
                "status": usage.status.value if isinstance(usage.status, APIRequestStatus) else usage.status,
                "status_code": usage.status_code,
                "response_time_ms": usage.response_time_ms,
                "rate_limit_remaining": usage.rate_limit_remaining,
                "ip_address": usage.ip_address,
                "user_agent": usage.user_agent,
                "created_at": usage.created_at.isoformat() if usage.created_at else None,
            })

        logger.info(f"Retrieved {len(logs_list)} API usage log entries")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=logs_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving API usage logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API usage logs: {str(e)}",
        ) from e


@router.get(
    "/summary/{api_key_id}",
    response_model=Dict[str, Any],
    tags=["API Usage"],
)
async def get_api_key_usage_summary(
    request: Request,
    api_key_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to include in summary"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get usage summary for a specific API key.

    Returns a comprehensive usage summary for a specific API key, including
    total requests, success rate, most used endpoints, and recent activity.
    This is useful for API key owners to monitor their usage and quotas.

    Args:
        request: FastAPI request object
        api_key_id: API key UUID
        days: Number of days to include in summary (1-365, default 30)
        db: Database session

    Returns:
        JSON response with API key usage summary

    Raises:
        HTTPException(400): If api_key_id is not a valid UUID
        HTTPException(404): If API key not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get 30-day usage summary
        >>> response = requests.get(f"/api/api-usage/summary/{key_id}")
        >>> # Get 7-day usage summary
        >>> response = requests.get(f"/api/api-usage/summary/{key_id}?days=7")
        >>> summary = response.json()
    """
    try:
        logger.info(f"Fetching usage summary for API key: {api_key_id} ({days} days)")

        # Parse api_key_id as UUID
        try:
            key_uuid = UUID(api_key_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid API key ID format: {api_key_id}",
            )

        # Verify API key exists
        key_query = select(APIKey).where(APIKey.id == key_uuid)
        key_result = await db.execute(key_query)
        api_key = key_result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key not found: {api_key_id}",
            )

        # Calculate date range
        from datetime import timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get usage statistics
        stats_query = select(
            func.count(APIUsage.id).label("total_requests"),
            func.count(APIUsage.id).filter(
                APIUsage.status == APIRequestStatus.SUCCESS
            ).label("successful_requests"),
            func.count(APIUsage.id).filter(
                APIUsage.status == APIRequestStatus.RATE_LIMITED
            ).label("rate_limited_requests"),
            func.avg(APIUsage.response_time_ms).label("avg_response_time_ms"),
        ).where(
            and_(
                APIUsage.api_key_id == key_uuid,
                APIUsage.created_at >= start_date,
                APIUsage.created_at <= end_date,
            )
        )

        stats_result = await db.execute(stats_query)
        stats_row = stats_result.first()

        # Get top endpoints
        endpoint_query = (
            select(
                APIUsage.endpoint,
                APIUsage.method,
                func.count(APIUsage.id).label("request_count"),
            )
            .where(
                and_(
                    APIUsage.api_key_id == key_uuid,
                    APIUsage.created_at >= start_date,
                    APIUsage.created_at <= end_date,
                )
            )
            .group_by(APIUsage.endpoint, APIUsage.method)
            .order_by(func.count(APIUsage.id).desc())
            .limit(5)
        )

        endpoint_result = await db.execute(endpoint_query)
        endpoint_rows = endpoint_result.all()

        # Build response
        total = stats_row.total_requests if stats_row else 0
        successful = stats_row.successful_requests if stats_row else 0
        success_rate = (successful / total) if total > 0 else 0.0

        response_data = {
            "api_key_id": str(api_key.id),
            "api_key_name": api_key.name,
            "api_key_prefix": api_key.key_prefix,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days,
            },
            "summary": {
                "total_requests": total,
                "successful_requests": successful,
                "rate_limited_requests": stats_row.rate_limited_requests if stats_row else 0,
                "success_rate": round(success_rate, 4),
                "avg_response_time_ms": round(stats_row.avg_response_time_ms, 2)
                if stats_row and stats_row.avg_response_time_ms
                else 0.0,
            },
            "top_endpoints": [
                {
                    "endpoint": row.endpoint,
                    "method": row.method,
                    "request_count": row.request_count,
                }
                for row in endpoint_rows
            ],
            "rate_limit": api_key.rate_limit,
        }

        logger.info(
            f"Retrieved usage summary for API key {api_key_id}: "
            f"{total} requests in {days} days"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving usage summary for {api_key_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage summary: {str(e)}",
        ) from e
