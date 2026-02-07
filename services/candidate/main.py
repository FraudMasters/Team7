"""
Приложение FastAPI для сервиса управления кандидатами.

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

    Контекстный менеджер жизненного цикла для запуска и остановки приложения.

    Handles database connection pool initialization and cleanup.

    Обрабатывает инициализацию и очистку пула подключений к базе данных.

    Yields:
        None

    Example:
        The lifespan is automatically called by FastAPI on startup/shutdown.
        / Жизненный цикл автоматически вызывается FastAPI при запуске/остановке.
    """
    # Startup / Запуск
    logger.info("Starting Candidate Service")
    logger.info(f"Database URL: {settings.database_url[:30]}...")
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info(f"Database schema: {settings.candidate_db_schema}")

    # Initialize database connection / Инициализация подключения к БД
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown / Остановка
    logger.info("Shutting down Candidate Service")
    await close_db()


# Create FastAPI application / Создание приложения FastAPI
app = FastAPI(
    title="Candidate Service",
    description="Service for managing candidates, notes, tags, and activities / Сервис для управления кандидатами, заметками, тегами и активностями",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Configure CORS middleware / Настройка middleware CORS
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


# Exception handlers / Обработчики исключений
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.

    Обработка ошибок базы данных SQLAlchemy.

    Args:
        request: The incoming request / Входящий запрос
        exc: The SQLAlchemy exception / Исключение SQLAlchemy

    Returns:
        JSON response with error details / JSON-ответ с деталями ошибки
    """
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database error occurred",
            "detail": "An error occurred while accessing the database / Произошла ошибка при доступе к базе данных",
            "type": "database_error",
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    Handle value validation errors.

    Обработка ошибок валидации значений.

    Args:
        request: The incoming request / Входящий запрос
        exc: The ValueError exception / Исключение ValueError

    Returns:
        JSON response with error details / JSON-ответ с деталями ошибки
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

    Обработка всех остальных исключений.

    Args:
        request: The incoming request / Входящий запрос
        exc: The exception / Исключение

    Returns:
        JSON response with error details / JSON-ответ с деталями ошибки
    """
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later. / Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.",
            "type": "internal_error",
        },
    )


# Health check endpoints / Эндпоинты проверки работоспособности
@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """
    Health check endpoint.

    Эндпоинт проверки работоспособности.

    Returns the current status of the API. This endpoint can be used
    by monitoring tools to verify the API is running.

    Возвращает текущий статус API. Этот эндпоинт может использоваться
    инструментами мониторинга для проверки работы API.

    Returns:
        JSON response with health status / JSON-ответ со статусом работоспособности

    Example:
        >>> curl http://localhost:8003/health
        {"status":"healthy","service":"candidate-service","version":"1.0.0"}
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "candidate-service",
            "version": "1.0.0",
        },
    )


@app.get("/ready", tags=["Health"])
async def readiness_check() -> JSONResponse:
    """
    Readiness check endpoint.

    Эндпоинт проверки готовности.

    Checks if the API is ready to handle requests. Currently checks
    basic API status. Future versions can add database connectivity checks.

    Проверяет готовность API к обработке запросов. В настоящее время
    проверяет базовый статус API. В будущих версиях можно добавить
    проверки подключения к базе данных.

    Returns:
        JSON response with readiness status / JSON-ответ со статусом готовности

    Example:
        >>> curl http://localhost:8003/ready
        {"status":"ready"}
    """
    # TODO: Add database connectivity check / Добавить проверку подключения к БД
    # TODO: Add Redis connectivity check / Добавить проверку подключения к Redis

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ready"},
    )


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """
    Root endpoint with API information.

    Корневой эндпоинт с информацией об API.

    Returns:
        JSON response with API information and links / JSON-ответ с информацией об API и ссылками

    Example:
        >>> curl http://localhost:8003/
        {
          "message": "Candidate Service",
          "version": "1.0.0",
          "docs": "/docs",
          "health": "/health"
        }
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Candidate Service",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "ready": "/ready",
        },
    )


# Include API routers / Подключение маршрутизаторов API
from api.candidates import router as candidates_router
from api.candidate_notes import router as candidate_notes_router
from api.candidate_tags import router as candidate_tags_router
from api.candidate_activities import router as candidate_activities_router

app.include_router(candidates_router, prefix="/api/candidates", tags=["Candidates"])
app.include_router(candidate_notes_router, prefix="/api/candidate-notes", tags=["Candidate Notes"])
app.include_router(candidate_tags_router, prefix="/api/candidate-tags", tags=["Candidate Tags"])
app.include_router(candidate_activities_router, prefix="/api/candidate-activities", tags=["Candidate Activities"])


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
