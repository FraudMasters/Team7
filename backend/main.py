"""
FastAPI application for resume analysis system.

This module provides the main FastAPI application with CORS middleware,
database session management, and health check endpoints.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


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
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database error occurred",
            "detail": "An error occurred while accessing the database",
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
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
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
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
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
from .api import resumes, analysis, matching

app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(analysis.router, prefix="/api/resumes", tags=["Analysis"])
app.include_router(matching.router, prefix="/api/matching", tags=["Matching"])


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
