"""
Приложение FastAPI для Matching Service.

# Русский комментарий:
Этот модуль предоставляет главное приложение FastAPI с middleware CORS,
управлением сессиями базы данных и эндпоинтами проверки работоспособности.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from config import get_settings
from database import init_db, close_db

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
    logger.info("Starting Matching Service API")
    logger.info(f"Database URL: {settings.database_url[:30]}...")
    logger.info(f"CORS origins: {settings.cors_origins}")

    # Initialize database connection
    await init_db()

    yield

    # Shutdown
    logger.info("Shutting down Matching Service API")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="Matching Service API",
    description="AI-powered job matching and resume analysis service",
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
        >>> curl http://localhost:8001/health
        {"status":"healthy","service":"matching-service-api","version":"1.0.0"}
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "matching-service-api",
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
        >>> curl http://localhost:8001/ready
        {"status":"ready"}
    """
    # TODO: Add database connectivity check
    # TODO: Add Redis connectivity check

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
        >>> curl http://localhost:8001/
        {
          "message": "Matching Service API",
          "version": "1.0.0",
          "docs": "/docs",
          "health": "/health"
        }
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Matching Service API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "ready": "/ready",
        },
    )


# Include API routers
from api.matching import router as matching_router
from api.comparisons import router as comparisons_router
from api.ranking import router as ranking_router

app.include_router(matching_router, prefix="/api/matching", tags=["Matching"])
app.include_router(comparisons_router, prefix="/api/comparisons", tags=["Comparisons"])
app.include_router(ranking_router, prefix="/api/ranking", tags=["Ranking"])


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    uvicorn.run(
        "main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
