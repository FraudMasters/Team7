"""
Настройка базы данных для Notification Service.

# Русский комментарий:
Этот модуль предоставляет асинхронный движок SQLAlchemy, фабрику сессий
и функции управления жизненным циклом соединений с базой данных.
"""
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create async engine / Создание асинхронного движка
async_engine = create_async_engine(
    settings.get_db_url_async(),
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory / Создание фабрики асинхронных сессий
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy.

    Все модели должны наследоваться от этого класса для автоматической
    регистрации в метаданных SQLAlchemy.
    """
    pass


async def init_db() -> None:
    """
    Инициализация соединения с базой данных.

    Проверяет подключение к базе данных, создавая тестовую сессию.
    """
    try:
        async with async_engine.begin() as conn:
            # Test connection / Проверка соединения
            await conn.execute("SELECT 1")
        logger.info("Database connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {e}")
        raise


async def close_db() -> None:
    """
    Закрытие всех соединений с базой данных.

    Вызывается при отключении приложения для корректного закрытия пула соединений.
    """
    try:
        await async_engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость FastAPI для получения асинхронной сессии базы данных.

    Эта функция используется как зависимость в эндпоинтах FastAPI для
    автоматического управления сессиями базы данных.

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy

    Example:
        @app.get("/notifications")
        async def get_notifications(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Notification))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
