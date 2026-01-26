"""
FastAPI application for resume analysis system.

This module provides the main FastAPI application with CORS middleware,
database session management, and health check endpoints.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings
from .i18n.backend_translations import get_error_message

logger = logging.getLogger(__name__)
settings = get_settings()


def _extract_accept_language(request: Request) -> str:
    """
    Extract and validate Accept-Language header from request.

    Args:
        request: The incoming FastAPI request

    Returns:
        Validated language code (e.g., 'en', 'ru')

    Examples:
        >>> _extract_accept_language(request_with_en_header)
        'en'
        >>> _extract_accept_language(request_with_ru_header)
        'ru'
        >>> _extract_accept_language(request_without_header)
        'en'  # Falls back to default
    """
    accept_language = request.headers.get("Accept-Language", "en")
    # Extract primary language code (e.g., 'en-US' -> 'en', 'ru-RU' -> 'ru')
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for application startup and shutdown.

    Handles database connection pool initialization and cleanup.

    Yields:
        None

    Example:
        The lifespan is automatically called by FastAPI on startup/shutdown.
    """
    # Startup
    logger.info("Starting Resume Analysis API")
    logger.info(f"Database URL: {settings.database_url[:30]}...")
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info(f"Max upload size: {settings.max_upload_size_mb}MB")
    logger.info(f"Allowed file types: {settings.allowed_file_types}")

    # Initialize models cache directory
    settings.models_cache_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Models cache directory: {settings.models_cache_path}")

    yield

    # Shutdown
    logger.info("Shutting down Resume Analysis API")


# Create FastAPI application
app = FastAPI(
    title="Resume Analysis API",
    description="AI-powered resume analysis and job matching API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
)


# Exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.

    Args:
        request: The incoming request
        exc: The SQLAlchemy exception

    Returns:
        JSON response with error details
    """
    logger.error(f"Database error: {exc}")
    locale = _extract_accept_language(request)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": get_error_message("database_error", locale),
            "detail": get_error_message("database_query_error", locale),
            "type": "database_error",
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    Handle value validation errors.

    Args:
        request: The incoming request
        exc: The ValueError exception

    Returns:
        JSON response with error details
    """
    logger.warning(f"Validation error: {exc}")
    locale = _extract_accept_language(request)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": get_error_message("invalid_input", locale),
            "detail": str(exc),
            "type": "validation_error",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other exceptions.

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSON response with error details
    """
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    locale = _extract_accept_language(request)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": get_error_message("internal_server_error", locale),
            "detail": get_error_message("service_unavailable", locale),
            "type": "internal_error",
        },
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """
    Health check endpoint.

    Returns the current status of the API. This endpoint can be used
    by monitoring tools to verify the API is running.

    Returns:
        JSON response with health status

    Example:
        >>> curl http://localhost:8000/health
        {"status":"healthy","service":"resume-analysis-api","version":"1.0.0"}
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "resume-analysis-api",
            "version": "1.0.0",
        },
    )


@app.get("/ready", tags=["Health"])
async def readiness_check() -> JSONResponse:
    """
    Readiness check endpoint.

    Checks if the API is ready to handle requests. Currently checks
    basic API status. Future versions can add database connectivity checks.

    Returns:
        JSON response with readiness status

    Example:
        >>> curl http://localhost:8000/ready
        {"status":"ready"}
    """
    # TODO: Add database connectivity check
    # TODO: Add Redis connectivity check
    # TODO: Add ML models availability check

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ready"},
    )


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """
    Root endpoint with API information.

    Returns:
        JSON response with API information and links

    Example:
        >>> curl http://localhost:8000/
        {
          "message": "Resume Analysis API",
          "version": "1.0.0",
          "docs": "/docs",
          "health": "/health"
        }
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Resume Analysis API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "ready": "/ready",
        },
    )


# Include API routers
from .api import (
    resumes,
    analysis,
    matching,
    skill_taxonomies,
    custom_synonyms,
    feedback,
    model_versions,
    comparisons,
    analytics,
    reports,
)

app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(analysis.router, prefix="/api/resumes", tags=["Analysis"])
app.include_router(matching.router, prefix="/api/matching", tags=["Matching"])
app.include_router(skill_taxonomies.router, prefix="/api/skill-taxonomies", tags=["Skill Taxonomies"])
app.include_router(custom_synonyms.router, prefix="/api/custom-synonyms", tags=["Custom Synonyms"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(model_versions.router, prefix="/api/model-versions", tags=["Model Versions"])
app.include_router(comparisons.router, prefix="/api/comparisons", tags=["Comparisons"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
