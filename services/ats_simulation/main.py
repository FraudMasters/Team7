"""
Приложение FastAPI для ATS Simulation Service.

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
from api.ats_simulation import router as ats_simulation_router

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Менеджер контекста жизненного цикла для запуска и остановки приложения.

    Обрабатывает инициализацию и очистку пула соединений с базой данных.

    Yields:
        None

    Example:
        Менеджер жизненного цикла вызывается автоматически FastAPI при запуске/остановке.
    """
    # Запуск / Startup
    logger.info("Запуск ATS Simulation Service")
    logger.info(f"URL базы данных: {settings.database_url[:30]}...")
    logger.info(f"Источники CORS: {settings.cors_origins}")
    logger.info(f"LLM провайдер: {settings.llm_provider}")
    logger.info(f"LLM модель: {settings.llm_model}")

    # Инициализация соединения с базой данных
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Не удалось инициализировать базу данных: {e}")
        raise

    yield

    # Остановка / Shutdown
    logger.info("Остановка ATS Simulation Service")
    await close_db()


# Создание приложения FastAPI
app = FastAPI(
    title="ATS Simulation Service",
    description="Микросервис симуляции ATS с LLM-интеграцией",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Настройка CORS middleware
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

# Подключение роутера
app.include_router(ats_simulation_router, prefix="/api/ats", tags=["ATS Simulation"])


# Обработчики исключений
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Обработка ошибок базы данных SQLAlchemy.

    Args:
        request: Входящий запрос
        exc: Исключение SQLAlchemy

    Returns:
        JSON ответ с деталями ошибки
    """
    logger.error(f"Ошибка базы данных: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Произошла ошибка базы данных",
            "detail": "Произошла ошибка при доступе к базе данных",
            "type": "database_error",
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    Обработка ошибок валидации значений.

    Args:
        request: Входящий запрос
        exc: Исключение ValueError

    Returns:
        JSON ответ с деталями ошибки
    """
    logger.warning(f"Ошибка валидации: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Ошибка валидации",
            "detail": str(exc),
            "type": "validation_error",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Обработка всех остальных исключений.

    Args:
        request: Входящий запрос
        exc: Исключение

    Returns:
        JSON ответ с деталями ошибки
    """
    logger.error(f"Неожиданная ошибка: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Внутренняя ошибка сервера",
            "detail": "Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.",
            "type": "internal_error",
        },
    )


# Эндпоинты проверки работоспособности
@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """
    Эндпоинт проверки работоспособности.

    Возвращает текущий статус API. Этот эндпоинт может использоваться
    инструментами мониторинга для проверки работоспособности API.

    Returns:
        JSON ответ со статусом работоспособности

    Example:
        >>> curl http://localhost:8007/health
        {"status":"healthy","service":"ats-simulation-service","version":"1.0.0"}
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "ats-simulation-service",
            "version": "1.0.0",
        },
    )


@app.get("/ready", tags=["Health"])
async def readiness_check() -> JSONResponse:
    """
    Эндпоинт проверки готовности.

    Проверяет, готов ли API к обработке запросов. В настоящее время проверяет
    базовый статус API. В будущих версиях можно добавить проверку подключения к базе данных.

    Returns:
        JSON ответ со статусом готовности

    Example:
        >>> curl http://localhost:8007/ready
        {"status":"ready"}
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ready"},
    )


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """
    Корневой эндпоинт с информацией об API.

    Returns:
        JSON ответ с информацией об API и ссылками

    Example:
        >>> curl http://localhost:8007/
        {
          "message": "ATS Simulation Service",
          "version": "1.0.0",
          "docs": "/docs",
          "health": "/health"
        }
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "ATS Simulation Service",
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
