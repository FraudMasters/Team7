"""
Приложение FastAPI для Vacancy Service.

# Русский комментарий:
Этот модуль предоставляет главное приложение FastAPI с middleware CORS,
управлением сессиями базы данных и endpoints проверки работоспособности.
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
from api.vacancies import router as vacancies_router

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Контекстный менеджер времени жизни для запуска и остановки приложения.

    Обрабатывает инициализацию пула подключений к базе данных и очистку.

    Yields:
        None

    Example:
        Lifespan автоматически вызывается FastAPI при запуске/остановке.
    """
    # Startup / Запуск
    logger.info("Starting Vacancy Service")
    logger.info(f"Database URL: {settings.database_url[:30]}...")
    logger.info(f"CORS origins: {settings.cors_origins}")

    # Initialize database connection / Инициализируем подключение к базе данных
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown / Остановка
    logger.info("Shutting down Vacancy Service")
    await close_db()


# Create FastAPI application / Создаем приложение FastAPI
app = FastAPI(
    title="Vacancy Service",
    description="Vacancy management microservice",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Configure CORS middleware / Настраиваем middleware CORS
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

# Include routers / Подключаем роутеры
app.include_router(vacancies_router, prefix="/api/vacancies", tags=["Vacancies"])


# Exception handlers / Обработчики исключений
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Обрабатывать ошибки базы данных SQLAlchemy.

    Args:
        request: Входящий запрос
        exc: Исключение SQLAlchemy

    Returns:
        JSON ответ с деталями ошибки
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
    Обрабатывать ошибки валидации значений.

    Args:
        request: Входящий запрос
        exc: Исключение ValueError

    Returns:
        JSON ответ с деталями ошибки
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
    Обрабатывать все остальные исключения.

    Args:
        request: Входящий запрос
        exc: Исключение

    Returns:
        JSON ответ с деталями ошибки
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


# Health check endpoints / Endpoints проверки работоспособности
@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """
    Endpoint проверки работоспособности.

    Возвращает текущий статус API. Этот endpoint может использоваться
    инструментами мониторинга для проверки работы API.

    Returns:
        JSON ответ со статусом работоспособности

    Example:
        >>> curl http://localhost:8004/health
        {"status":"healthy","service":"vacancy-service","version":"1.0.0"}
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "vacancy-service",
            "version": "1.0.0",
        },
    )


@app.get("/ready", tags=["Health"])
async def readiness_check() -> JSONResponse:
    """
    Endpoint проверки готовности.

    Проверяет, готов ли API к обработке запросов. В настоящее время проверяет
    базовый статус API. В будущих версиях можно добавить проверку подключения к базе данных.

    Returns:
        JSON ответ со статусом готовности

    Example:
        >>> curl http://localhost:8004/ready
        {"status":"ready"}
    """
    # TODO: Add database connectivity check / Добавить проверку подключения к базе данных
    # TODO: Add Redis connectivity check / Добавить проверку подключения к Redis

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ready"},
    )


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """
    Корневой endpoint с информацией об API.

    Returns:
        JSON ответ с информацией об API и ссылками

    Example:
        >>> curl http://localhost:8004/
        {
          "message": "Vacancy Service",
          "version": "1.0.0",
          "docs": "/docs",
          "health": "/health"
        }
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Vacancy Service",
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
