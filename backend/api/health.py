"""
Health check and system status endpoints.

This module provides endpoints for monitoring the health and status of the API
and its dependencies, including database connectivity, ML models availability,
and external services status.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter()


class ComponentHealth(BaseModel):
    """Health status of a system component."""

    name: str = Field(..., description="Component name")
    status: str = Field(..., description="Health status: 'healthy', 'degraded', or 'unhealthy'")
    message: Optional[str] = Field(None, description="Additional status information")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    degraded_mode: Optional[bool] = Field(None, description="Whether component is in degraded mode")


class SystemHealthResponse(BaseModel):
    """Response model for system health check."""

    status: str = Field(..., description="Overall system status: 'healthy', 'degraded', or 'unhealthy'")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="ISO 8601 timestamp of health check")
    components: dict[str, ComponentHealth] = Field(..., description="Health status of individual components")


@router.get(
    "",
    response_model=SystemHealthResponse,
    tags=["Health"],
)
async def get_health_status() -> JSONResponse:
    """
    Get comprehensive health status of the API and all system components.

    This endpoint provides detailed health information for the API and its dependencies,
    including database connectivity, ML models availability, and other critical components.
    It's designed for use by monitoring tools, orchestrators, and health check systems.

    The overall system status is determined as follows:
    - 'healthy': All components are healthy
    - 'degraded': Some components are degraded but the system can function
    - 'unhealthy': Critical components are unhealthy

    Components checked include:
    - **api**: The FastAPI application itself
    - **database**: PostgreSQL database connectivity
    - **redis**: Redis availability and performance
    - **celery_workers**: Celery worker status and queue length
    - **ml_models**: ML/NLP models availability (spaCy, transformers, etc.)
    - **storage**: File system storage availability
    - **external_services**: External service dependencies (LanguageTool, S3) with graceful degradation

    Returns:
        JSON response with overall system status and individual component health

    Raises:
        HTTPException(500): If health check itself fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/health")
        >>> response.json()
        {
            "status": "healthy",
            "service": "resume-analysis-api",
            "version": "1.0.0",
            "timestamp": "2024-01-15T10:30:00Z",
            "components": {
                "api": {
                    "name": "api",
                    "status": "healthy",
                    "message": "API is responding normally",
                    "response_time_ms": 0.5
                },
                "database": {
                    "name": "database",
                    "status": "healthy",
                    "message": "Database connection successful",
                    "response_time_ms": 5.2
                },
                "redis": {
                    "name": "redis",
                    "status": "healthy",
                    "message": "Redis connected (keys: 150, latency: 2.5ms)",
                    "response_time_ms": 2.5
                },
                "celery_workers": {
                    "name": "celery_workers",
                    "status": "healthy",
                    "message": "2 workers online, queue length: 5",
                    "response_time_ms": 45.2
                },
                "ml_models": {
                    "name": "ml_models",
                    "status": "healthy",
                    "message": "ML models loaded (3/3)",
                    "response_time_ms": 12.3
                },
                "storage": {
                    "name": "storage",
                    "status": "healthy",
                    "message": "File system storage accessible",
                    "response_time_ms": 1.1
                },
                "external_services": {
                    "name": "external_services",
                    "status": "healthy",
                    "message": "LanguageTool: healthy (enabled: True), S3: healthy (enabled: True)",
                    "response_time_ms": 15.3,
                    "degraded_mode": false
                }
            }
        }
    """
    import time
    from datetime import datetime, timezone

    try:
        logger.info("Performing comprehensive health check")
        start_time = time.time()

        components = {}
        overall_status = "healthy"

        # Check API component
        api_start = time.time()
        components["api"] = ComponentHealth(
            name="api",
            status="healthy",
            message="API is responding normally",
            response_time_ms=round((time.time() - api_start) * 1000, 2),
        )

        # Check database connectivity
        db_start = time.time()
        try:
            from database import get_db

            db_connected = False
            async for db in get_db():
                # Execute simple query to test connectivity
                await db.execute(text("SELECT 1"))
                db_connected = True
                break

            if db_connected:
                components["database"] = ComponentHealth(
                    name="database",
                    status="healthy",
                    message="Database connection successful",
                    response_time_ms=round((time.time() - db_start) * 1000, 2),
                )
            else:
                components["database"] = ComponentHealth(
                    name="database",
                    status="unhealthy",
                    message="Failed to establish database connection",
                    response_time_ms=round((time.time() - db_start) * 1000, 2),
                )
                overall_status = "unhealthy"

        except Exception as db_error:
            logger.error(f"Database health check failed: {db_error}")
            components["database"] = ComponentHealth(
                name="database",
                status="unhealthy",
                message=f"Database connection error: {str(db_error)}",
                response_time_ms=round((time.time() - db_start) * 1000, 2),
            )
            overall_status = "unhealthy"

        # Check storage availability
        storage_start = time.time()
        try:
            from config import get_settings
            import os

            settings = get_settings()

            # Check if upload directory is accessible
            upload_dir = settings.upload_dir
            if upload_dir.exists() and os.access(upload_dir, os.W_OK):
                components["storage"] = ComponentHealth(
                    name="storage",
                    status="healthy",
                    message=f"File system storage accessible ({upload_dir})",
                    response_time_ms=round((time.time() - storage_start) * 1000, 2),
                )
            else:
                components["storage"] = ComponentHealth(
                    name="storage",
                    status="unhealthy",
                    message=f"Storage directory not accessible or not writable ({upload_dir})",
                    response_time_ms=round((time.time() - storage_start) * 1000, 2),
                )
                overall_status = "unhealthy"

        except Exception as storage_error:
            logger.error(f"Storage health check failed: {storage_error}")
            components["storage"] = ComponentHealth(
                name="storage",
                status="unhealthy",
                message=f"Storage check failed: {str(storage_error)}",
                response_time_ms=round((time.time() - storage_start) * 1000, 2),
            )
            overall_status = "unhealthy"

        # Check Redis availability
        redis_start = time.time()
        try:
            from utils.health_checks import check_redis

            redis_result = await check_redis()

            # Map health check result to ComponentHealth
            redis_status = redis_result.get("status", "unhealthy")
            components["redis"] = ComponentHealth(
                name="redis",
                status=redis_status,
                message=f"Redis {'connected' if redis_result.get('connected') else 'not connected'} "
                       f"(keys: {redis_result.get('key_count', 0)}, "
                       f"latency: {redis_result.get('latency_seconds', 0)*1000:.1f}ms)",
                response_time_ms=round(redis_result.get('latency_seconds', 0) * 1000, 2),
            )

            # Update overall status based on Redis health
            if redis_status == "unhealthy" and overall_status == "healthy":
                overall_status = "degraded"  # Redis is important but not critical

        except Exception as redis_error:
            logger.warning(f"Redis health check failed: {redis_error}")
            components["redis"] = ComponentHealth(
                name="redis",
                status="degraded",
                message=f"Redis check failed: {str(redis_error)}",
                response_time_ms=round((time.time() - redis_start) * 1000, 2),
            )
            if overall_status == "healthy":
                overall_status = "degraded"

        # Check Celery workers status
        celery_start = time.time()
        try:
            from utils.health_checks import check_celery_workers

            celery_result = await check_celery_workers()

            # Map health check result to ComponentHealth
            celery_status = celery_result.get("status", "unhealthy")
            workers_online = celery_result.get("workers_online", 0)
            queue_length = celery_result.get("queue_length", 0)

            components["celery_workers"] = ComponentHealth(
                name="celery_workers",
                status=celery_status,
                message=f"{workers_online} worker(s) online, queue length: {queue_length}",
                response_time_ms=round(celery_result.get('latency_seconds', 0) * 1000, 2),
            )

            # Update overall status based on Celery health
            if celery_status == "unhealthy":
                overall_status = "unhealthy"
            elif celery_status == "degraded" and overall_status == "healthy":
                overall_status = "degraded"

        except Exception as celery_error:
            logger.warning(f"Celery workers health check failed: {celery_error}")
            components["celery_workers"] = ComponentHealth(
                name="celery_workers",
                status="degraded",
                message=f"Celery workers check failed: {str(celery_error)}",
                response_time_ms=round((time.time() - celery_start) * 1000, 2),
            )
            if overall_status == "healthy":
                overall_status = "degraded"

        # Check ML models availability
        ml_models_start = time.time()
        try:
            from utils.health_checks import check_ml_models

            ml_result = await check_ml_models()

            # Map health check result to ComponentHealth
            ml_status = ml_result.get("status", "unhealthy")
            successful_count = ml_result.get("successful_count", 0)
            total_models = ml_result.get("total_models", 0)

            components["ml_models"] = ComponentHealth(
                name="ml_models",
                status=ml_status,
                message=f"ML models loaded ({successful_count}/{total_models})",
                response_time_ms=round((time.time() - ml_models_start) * 1000, 2),
            )

            # Update overall status based on ML models health
            if ml_status == "unhealthy":
                overall_status = "unhealthy"
            elif ml_status == "degraded" and overall_status == "healthy":
                overall_status = "degraded"

        except Exception as ml_error:
            logger.warning(f"ML models health check failed: {ml_error}")
            components["ml_models"] = ComponentHealth(
                name="ml_models",
                status="degraded",
                message=f"ML models check failed: {str(ml_error)}",
                response_time_ms=round((time.time() - ml_models_start) * 1000, 2),
            )
            if overall_status == "healthy":
                overall_status = "degraded"

        # Check external services (LanguageTool and S3)
        external_services_start = time.time()
        external_degraded = False
        try:
            from utils.health_checks import check_languagetool, check_s3

            # Check LanguageTool
            lt_result = await check_languagetool()
            lt_status = lt_result.get("status", "unhealthy")

            # Check S3
            s3_result = await check_s3()
            s3_status = s3_result.get("status", "unhealthy")

            # Determine overall external services status
            # If both are healthy -> healthy
            # If one is degraded or unhealthy, but system can function -> degraded
            # Only mark as unhealthy if both critical external services are down
            if lt_status == "healthy" and s3_status == "healthy":
                external_status = "healthy"
            elif lt_status == "unhealthy" and s3_status == "unhealthy":
                external_status = "unhealthy"
                external_degraded = True
            else:
                external_status = "degraded"
                external_degraded = True

            # Build combined external services component
            lt_enabled = lt_result.get("enabled", True)
            s3_enabled = s3_result.get("enabled", True)

            components["external_services"] = ComponentHealth(
                name="external_services",
                status=external_status,
                message=f"LanguageTool: {lt_status} (enabled: {lt_enabled}), S3: {s3_status} (enabled: {s3_enabled})",
                response_time_ms=round((time.time() - external_services_start) * 1000, 2),
                degraded_mode=external_degraded,
            )

            # Update overall status based on external services health
            # External services are optional, so they only cause degradation, not unhealthy
            if external_degraded and overall_status == "healthy":
                overall_status = "degraded"

        except Exception as ext_error:
            logger.warning(f"External services health check failed: {ext_error}")
            components["external_services"] = ComponentHealth(
                name="external_services",
                status="degraded",
                message=f"External services check failed: {str(ext_error)}",
                response_time_ms=round((time.time() - external_services_start) * 1000, 2),
                degraded_mode=True,
            )
            if overall_status == "healthy":
                overall_status = "degraded"

        total_time = time.time() - start_time

        response_data = {
            "status": overall_status,
            "service": "resume-analysis-api",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                key: value.model_dump() for key, value in components.items()
            },
        }

        logger.info(
            f"Health check completed - status: {overall_status}, "
            f"components checked: {len(components)}, "
            f"total time: {round(total_time * 1000, 2)}ms"
        )

        # Return appropriate HTTP status code based on overall health
        http_status = status.HTTP_200_OK if overall_status != "unhealthy" else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=http_status,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Health check endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}",
        ) from e


class LivenessResponse(BaseModel):
    """Response model for liveness probe."""

    status: str = Field(..., description="Liveness status: 'alive'")
    service: str = Field(..., description="Service name")


@router.get(
    "/live",
    response_model=LivenessResponse,
    tags=["Health"],
)
async def liveness_probe() -> JSONResponse:
    """
    Liveness probe endpoint.

    This is a simple liveness check that indicates whether the API container/process
    is running and responsive. This endpoint is designed for Kubernetes liveness probes
    and similar monitoring systems that need to detect if the service needs to be restarted.

    Unlike the comprehensive health check, this endpoint only verifies that the API
    process is alive and does not check dependencies like database or external services.

    Returns:
        JSON response with liveness status

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/health/live")
        >>> response.json()
        {
            "status": "alive",
            "service": "resume-analysis-api"
        }
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "alive",
            "service": "resume-analysis-api",
        },
    )


class ReadinessResponse(BaseModel):
    """Response model for readiness probe."""

    status: str = Field(..., description="Readiness status: 'ready' or 'not_ready'")
    service: str = Field(..., description="Service name")
    checks_passed: int = Field(..., description="Number of readiness checks passed")
    checks_total: int = Field(..., description="Total number of readiness checks")
    message: Optional[str] = Field(None, description="Additional status information")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    tags=["Health"],
)
async def readiness_probe() -> JSONResponse:
    """
    Readiness probe endpoint.

    This endpoint checks if the API is ready to handle requests, which means not only
    is the process running, but all critical dependencies are available. This endpoint
    is designed for Kubernetes readiness probes and similar monitoring systems.

    Readiness checks include:
    - Database connectivity (critical)
    - Storage availability (critical)

    The API is considered ready if all critical checks pass. If critical checks fail,
    the endpoint returns a 503 status code to indicate the service should not receive traffic.

    Returns:
        JSON response with readiness status and check details

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/health/ready")
        >>> response.json()
        {
            "status": "ready",
            "service": "resume-analysis-api",
            "checks_passed": 2,
            "checks_total": 2,
            "message": "All critical dependencies are available"
        }
    """
    import time

    try:
        logger.info("Performing readiness check")
        start_time = time.time()

        checks_passed = 0
        checks_total = 0
        messages = []

        # Check 1: Database connectivity (critical)
        checks_total += 1
        try:
            from database import get_db
            from sqlalchemy import text

            db_connected = False
            async for db in get_db():
                await db.execute(text("SELECT 1"))
                db_connected = True
                break

            if db_connected:
                checks_passed += 1
                messages.append("Database: connected")
            else:
                messages.append("Database: not connected")
        except Exception as db_error:
            messages.append(f"Database: error - {str(db_error)}")

        # Check 2: Storage availability (critical)
        checks_total += 1
        try:
            from config import get_settings
            import os

            settings = get_settings()
            upload_dir = settings.upload_dir

            if upload_dir.exists() and os.access(upload_dir, os.W_OK):
                checks_passed += 1
                messages.append("Storage: accessible")
            else:
                messages.append("Storage: not accessible")
        except Exception as storage_error:
            messages.append(f"Storage: error - {str(storage_error)}")

        # Determine readiness status
        is_ready = checks_passed == checks_total
        status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

        response_data = {
            "status": "ready" if is_ready else "not_ready",
            "service": "resume-analysis-api",
            "checks_passed": checks_passed,
            "checks_total": checks_total,
            "message": "All critical dependencies are available" if is_ready else f"Some checks failed: {', '.join(messages)}",
        }

        logger.info(
            f"Readiness check completed - status: {response_data['status']}, "
            f"checks: {checks_passed}/{checks_total}, "
            f"time: {round((time.time() - start_time) * 1000, 2)}ms"
        )

        return JSONResponse(
            status_code=status_code,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": "resume-analysis-api",
                "checks_passed": 0,
                "checks_total": checks_total,
                "message": f"Readiness check failed: {str(e)}",
            },
        )
