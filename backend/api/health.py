"""
Health check API endpoints.

This module provides endpoints for:
- Basic health check (/health) - Quick API status check
- Readiness check (/ready) - Verify essential services are operational
- Detailed health check (/health/detailed) - Comprehensive status of all components
- Component check (/health/component/{name}) - Health check for specific component
- Dependency graph (/health/dependencies) - Service dependency relationships

These endpoints support monitoring systems, load balancer health checks,
and operational dashboards.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.health_check import (
    get_health_check_service,
    HealthCheckResult,
    HealthCheckService,
)
from utils.dependency_graph import (
    get_dependency_graph,
    DependencyGraph,
    ServiceNode,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class ComponentHealthInfo(BaseModel):
    """Health information for a single component."""

    component: str = Field(..., description="Component name")
    status: str = Field(..., description="Health status: healthy, degraded, or unhealthy")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    message: str = Field(..., description="Human-readable status message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional component details")
    error: Optional[str] = Field(None, description="Error message if check failed")


class HealthCheckSummary(BaseModel):
    """Summary statistics for health check results."""

    total_time_ms: float = Field(..., description="Total time for all health checks")
    components_checked: int = Field(..., description="Number of components checked")
    components_healthy: int = Field(..., description="Number of healthy components")
    components_degraded: int = Field(..., description="Number of degraded components")
    components_unhealthy: int = Field(..., description="Number of unhealthy components")


class DetailedHealthResponse(BaseModel):
    """Response model for detailed health check."""

    overall_status: str = Field(..., description="Overall system health status")
    summary: HealthCheckSummary = Field(..., description="Health check summary statistics")
    components: Dict[str, ComponentHealthInfo] = Field(..., description="Individual component status")
    timestamp: float = Field(..., description="Unix timestamp of health check")


class BasicHealthResponse(BaseModel):
    """Response model for basic health check."""

    status: str = Field(..., description="API status: healthy or unhealthy")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: float = Field(..., description="Unix timestamp")


class ReadinessResponse(BaseModel):
    """Response model for readiness check."""

    status: str = Field(..., description="Readiness status: ready or not_ready")
    timestamp: float = Field(..., description="Unix timestamp")
    checks: Dict[str, str] = Field(..., description="Status of essential components")


class ServiceDependencyInfo(BaseModel):
    """Dependency information for a single service."""

    name: str = Field(..., description="Unique service identifier")
    display_name: str = Field(..., description="Human-readable service name")
    description: str = Field(..., description="Brief description of the service")
    dependencies: List[str] = Field(..., description="Services this service depends on")
    dependents: List[str] = Field(..., description="Services that depend on this service")
    essential: bool = Field(..., description="Whether this service is essential for system operation")
    category: str = Field(..., description="Service category (infrastructure, worker, external, model)")


class DependencyGraphSummary(BaseModel):
    """Summary statistics for the dependency graph."""

    total_services: int = Field(..., description="Total number of services")
    essential_services: int = Field(..., description="Number of essential services")
    categories: Dict[str, int] = Field(..., description="Service count by category")
    services_with_most_dependents: List[Dict[str, Any]] = Field(
        ..., description="Services with the most dependents"
    )
    services_with_most_dependencies: List[Dict[str, Any]] = Field(
        ..., description="Services with the most dependencies"
    )
    critical_path: List[str] = Field(..., description="Critical path of essential services")


class DependencyGraphResponse(BaseModel):
    """Response model for dependency graph endpoint."""

    services: Dict[str, ServiceDependencyInfo] = Field(
        ..., description="All services and their dependencies"
    )
    summary: DependencyGraphSummary = Field(..., description="Graph summary statistics")


@router.get(
    "/",
    response_model=BasicHealthResponse,
    tags=["Health"],
)
async def health_check(request: Request) -> JSONResponse:
    """
    Basic health check endpoint.

    Returns the current status of the API. This endpoint can be used
    by monitoring tools and load balancers to verify the API is running.
    This is a lightweight check that returns immediately without checking
    dependent services.

    Args:
        request: FastAPI request object

    Returns:
        JSON response with basic health status

    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/health")
        >>> response.json()
        {
            "status": "healthy",
            "service": "resume-analysis-api",
            "version": "1.0.0",
            "timestamp": 1234567890.123
        }
    """
    try:
        logger.debug("Basic health check requested")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "service": "resume-analysis-api",
                "version": "1.0.0",
                "timestamp": time.time(),
            },
        )

    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}",
        ) from e


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    tags=["Health"],
)
async def readiness_check(request: Request) -> JSONResponse:
    """
    Readiness check endpoint.

    Checks if the API is ready to handle requests by verifying essential
    services (database, Redis, Celery) are operational. This endpoint is
    designed for Kubernetes readiness probes and similar orchestration tools.

    A system is considered "ready" if all essential components are operational
    (healthy or degraded). Essential components that are unhealthy will cause
    the system to be "not_ready".

    Args:
        request: FastAPI request object

    Returns:
        JSON response with readiness status and essential component checks

    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/health/ready")
        >>> response.json()
        {
            "status": "ready",
            "timestamp": 1234567890.123,
            "checks": {
                "database": "healthy",
                "redis": "healthy",
                "celery": "healthy"
            }
        }
    """
    try:
        logger.info("Readiness check requested")

        # Get health check service
        health_service = get_health_check_service()

        # Check only essential components
        result = await health_service.check_essential_only()

        # Determine overall readiness
        overall_status = result.get("overall_status", "unhealthy")
        is_ready = overall_status in ("healthy", "degraded")

        # Extract component statuses
        components = result.get("components", {})
        checks = {name: comp.get("status", "unknown") for name, comp in components.items()}

        readiness_status = "ready" if is_ready else "not_ready"

        logger.info(
            f"Readiness check completed: {readiness_status} "
            f"(database: {checks.get('database', 'unknown')}, "
            f"redis: {checks.get('redis', 'unknown')}, "
            f"celery: {checks.get('celery', 'unknown')})"
        )

        http_status = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=http_status,
            content={
                "status": readiness_status,
                "timestamp": time.time(),
                "checks": checks,
            },
        )

    except Exception as e:
        logger.error(f"Error in readiness check: {e}", exc_info=True)
        # Return not_ready on error
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "timestamp": time.time(),
                "checks": {},
                "error": str(e),
            },
        )


@router.get(
    "/detailed",
    response_model=DetailedHealthResponse,
    tags=["Health"],
)
async def detailed_health_check(request: Request) -> JSONResponse:
    """
    Detailed health check endpoint.

    Performs comprehensive health checks on all system components including:
    - Database (PostgreSQL)
    - Redis cache
    - Celery workers
    - ML models
    - External APIs

    This endpoint provides detailed status information for each component
    including response times, error messages, and additional metrics.

    The overall health status is determined as follows:
    - healthy: All essential components are healthy
    - degraded: Essential components are operational but some have issues,
                or optional components are unhealthy
    - unhealthy: One or more essential components are unhealthy

    Args:
        request: FastAPI request object

    Returns:
        JSON response with detailed health status for all components

    Raises:
        HTTPException(500): If health check service fails

    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/health/detailed")
        >>> response.json()
        {
            "overall_status": "healthy",
            "summary": {
                "total_time_ms": 150.5,
                "components_checked": 5,
                "components_healthy": 5,
                "components_degraded": 0,
                "components_unhealthy": 0
            },
            "components": {
                "database": {
                    "component": "database",
                    "status": "healthy",
                    "response_time_ms": 25.3,
                    "message": "Database is operational",
                    "details": {"response_time_ms": 25.3},
                    "error": null
                },
                ...
            },
            "timestamp": 1234567890.123
        }
    """
    try:
        logger.info("Detailed health check requested")

        # Get health check service
        health_service = get_health_check_service()

        # Run all health checks
        result = await health_service.check_all()

        # Extract and format results
        overall_status = result.get("overall_status", "unknown")
        summary_data = result.get("summary", {})
        components_data = result.get("components", {})
        timestamp = result.get("timestamp", time.time())

        # Build summary
        summary = HealthCheckSummary(
            total_time_ms=summary_data.get("total_time_ms", 0),
            components_checked=summary_data.get("components_checked", 0),
            components_healthy=summary_data.get("components_healthy", 0),
            components_degraded=summary_data.get("components_degraded", 0),
            components_unhealthy=summary_data.get("components_unhealthy", 0),
        )

        # Build component info
        components = {}
        for name, comp_data in components_data.items():
            components[name] = ComponentHealthInfo(
                component=comp_data.get("component", name),
                status=comp_data.get("status", "unknown"),
                response_time_ms=comp_data.get("response_time_ms", 0),
                message=comp_data.get("message", ""),
                details=comp_data.get("details", {}),
                error=comp_data.get("error"),
            )

        logger.info(
            f"Detailed health check completed: {overall_status} "
            f"({summary.components_healthy}/{summary.components_checked} healthy, "
            f"{summary.total_time_ms:.2f}ms)"
        )

        # Determine HTTP status based on overall health
        http_status = status.HTTP_200_OK
        if overall_status == HealthCheckResult.STATUS_UNHEALTHY:
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        elif overall_status == HealthCheckResult.STATUS_DEGRADED:
            # Still return 200 for degraded, but status indicates degradation
            http_status = status.HTTP_200_OK

        return JSONResponse(
            status_code=http_status,
            content={
                "overall_status": overall_status,
                "summary": summary.dict(),
                "components": {name: comp.dict() for name, comp in components.items()},
                "timestamp": timestamp,
            },
        )

    except Exception as e:
        logger.error(f"Error in detailed health check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detailed health check failed: {str(e)}",
        ) from e


@router.get(
    "/component/{component_name}",
    response_model=ComponentHealthInfo,
    tags=["Health"],
)
async def component_health_check(
    request: Request,
    component_name: str,
) -> JSONResponse:
    """
    Health check for a specific component.

    Checks the health of a single system component by name. Valid component
    names include: database, redis, celery, ml_models, external_apis.

    Args:
        request: FastAPI request object
        component_name: Name of the component to check

    Returns:
        JSON response with component health status

    Raises:
        HTTPException(400): If component_name is invalid
        HTTPException(500): If health check fails

    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/health/component/database")
        >>> response.json()
        {
            "component": "database",
            "status": "healthy",
            "response_time_ms": 25.3,
            "message": "Database is operational",
            "details": {"response_time_ms": 25.3},
            "error": null
        }
    """
    try:
        logger.info(f"Component health check requested for: {component_name}")

        # Get health check service
        health_service = get_health_check_service()

        # Check if component is registered
        if component_name not in health_service.checkers:
            available = list(health_service.checkers.keys())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown component: {component_name}. "
                f"Available components: {', '.join(available)}",
            )

        # Run health check for the specific component
        result = await health_service.check_component(component_name)

        # Determine HTTP status based on component health
        http_status = status.HTTP_200_OK
        if result.status == HealthCheckResult.STATUS_UNHEALTHY:
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE

        logger.info(
            f"Component health check for {component_name}: {result.status} "
            f"({result.response_time_ms:.2f}ms)"
        )

        return JSONResponse(
            status_code=http_status,
            content=result.to_dict(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in component health check for {component_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Component health check failed: {str(e)}",
        ) from e


@router.get(
    "/dependencies",
    response_model=DependencyGraphResponse,
    tags=["Health"],
)
async def dependency_graph(request: Request) -> JSONResponse:
    """
    Service dependency graph endpoint.

    Returns the complete dependency graph showing relationships between
    all system services. This includes service dependencies, dependents,
    categorization, and critical path analysis.

    The dependency graph helps understand:
    - Which services depend on each other
    - Potential cascading failure scenarios
    - Critical paths that affect system operation
    - Service categorization (infrastructure, worker, external, model)

    Args:
        request: FastAPI request object

    Returns:
        JSON response with complete dependency graph

    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/health/dependencies")
        >>> response.json()
        {
            "services": {
                "database": {
                    "name": "database",
                    "display_name": "PostgreSQL Database",
                    "description": "Primary database for storing resumes...",
                    "dependencies": [],
                    "dependents": ["backend_api", "celery_worker"],
                    "essential": true,
                    "category": "infrastructure"
                },
                ...
            },
            "summary": {
                "total_services": 9,
                "essential_services": 5,
                "categories": {"infrastructure": 5, "worker": 1, "model": 2, "external": 1},
                "services_with_most_dependents": [...],
                "services_with_most_dependencies": [...],
                "critical_path": ["database", "backend_api"]
            }
        }
    """
    try:
        logger.debug("Dependency graph requested")

        # Get dependency graph
        graph = get_dependency_graph()

        # Convert to dictionary
        graph_dict = graph.to_dict()

        logger.debug(
            f"Dependency graph returned: {graph_dict['summary']['total_services']} services, "
            f"{graph_dict['summary']['essential_services']} essential"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=graph_dict,
        )

    except Exception as e:
        logger.error(f"Error in dependency graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dependency graph failed: {str(e)}",
        ) from e
