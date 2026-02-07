"""
Приложение FastAPI для Taxonomy Service.

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
from api.skill_taxonomies import router as skill_taxonomies_router
from api.taxonomy_import_export import router as taxonomy_import_export_router

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for application startup and shutdown.

    Handles initialization of the database connection pool and cleanup.

    Yields:
        None

    Example:
        Lifespan is automatically called by FastAPI on startup/shutdown.
    """
    # Startup
    logger.info("Starting Taxonomy Service")
    logger.info(f"Database URL: {settings.database_url[:30]}...")
    logger.info(f"CORS origins: {settings.cors_origins}")

    # Initialize database connection
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Taxonomy Service")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="Taxonomy Service",
    description="Skill taxonomy management microservice",
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "Accept-Language",
    ],
)

# Include routers
app.include_router(skill_taxonomies_router, prefix="/api/skill-taxonomies", tags=["Skill Taxonomies"])
app.include_router(taxonomy_import_export_router, prefix="/api/taxonomy-import-export", tags=["Taxonomy Import/Export"])


# Exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.

    Args:
        request: Incoming request
        exc: SQLAlchemy exception

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
        request: Incoming request
        exc: ValueError exception

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
        request: Incoming request
        exc: Exception

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
    by monitoring tools to check if the API is running.

    Returns:
        JSON response with health status

    Example:
        >>> curl http://localhost:8005/health
        {"status":"healthy","service":"taxonomy-service","version":"1.0.0"}
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "taxonomy-service",
            "version": "1.0.0",
        },
    )


@app.get("/ready", tags=["Health"])
async def readiness_check() -> JSONResponse:
    """
    Readiness check endpoint.

    Checks if the API is ready to handle requests. Currently checks
    basic API status. In future versions, add database connectivity check.

    Returns:
        JSON response with readiness status

    Example:
        >>> curl http://localhost:8005/ready
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
        >>> curl http://localhost:8005/
        {
          "message": "Taxonomy Service",
          "version": "1.0.0",
          "docs": "/docs",
          "health": "/health"
        }
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Taxonomy Service",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "ready": "/ready",
        },
    )


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
