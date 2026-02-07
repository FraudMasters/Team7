"""
Application configuration for Candidate Service.

Конфигурация приложения для сервиса управления кандидатами.
Этот модуль использует pydantic-settings для загрузки и проверки конфигурации
из переменных окружения с разумными значениями по умолчанию.

Русские комментарии: Все настройки имеют описания на русском языке.
"""
import logging
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Настройки приложения, загружаемые из переменных окружения.

    Attributes:
        database_url: PostgreSQL database connection URL
        redis_url: Redis connection URL for caching
        service_host: Host to bind the FastAPI server
        service_port: Port to bind the FastAPI server (default: 8003 for Candidate Service)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        candidate_db_schema: Database schema name for candidate service tables

    Атрибуты:
        database_url: URL подключения к PostgreSQL
        redis_url: URL подключения к Redis для кэширования
        service_host: Хост для привязки FastAPI сервера
        service_port: Порт для привязки FastAPI сервера (по умолчанию: 8003)
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        candidate_db_schema: Имя схемы базы данных для таблиц сервиса кандидатов
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration / Конфигурация базы данных
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/resume_analysis",
        description="PostgreSQL database connection URL / URL подключения к PostgreSQL",
    )

    # Database Schema for Candidate Service / Схема БД для сервиса кандидатов
    candidate_db_schema: str = Field(
        default="candidates_service",
        description="Database schema name for candidate service tables / Имя схемы БД для таблиц сервиса кандидатов",
    )

    # Redis Configuration / Конфигурация Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching / URL подключения к Redis для кэширования",
    )

    # Service Server Configuration / Конфигурация сервера сервиса
    service_host: str = Field(
        default="0.0.0.0",
        description="Host to bind the FastAPI server / Хост для привязки FastAPI сервера",
    )

    service_port: int = Field(
        default=8003,
        description="Port to bind the FastAPI server / Порт для привязки FastAPI сервера",
    )

    # Logging Configuration / Конфигурация логирования
    log_level: str = Field(
        default="INFO",
        description="Logging level / Уровень логирования",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """
        Validate database URL format.

        Проверка формата URL базы данных.
        """
        if not v.startswith(("postgresql://", "postgresql+async://")):
            logger.warning(
                f"Database URL should start with 'postgresql://' or 'postgresql+async://', got: {v[:20]}..."
            )
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """
        Validate and uppercase log level.

        Проверка и преобразование к верхнему регистру уровня логирования.
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            logger.warning(f"Invalid log level '{v}', defaulting to INFO")
            return "INFO"
        return v_upper

    @property
    def cors_origins(self) -> List[str]:
        """
        Get list of allowed CORS origins.

        Получить список разрешенных источников CORS.
        """
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:8888",  # API Gateway
            "http://127.0.0.1:8888",
        ]

    def get_db_url_async(self) -> str:
        """
        Get async database URL for SQLAlchemy async engine.

        Получить асинхронный URL базы данных для SQLAlchemy async engine.

        Returns:
            Async database URL with asyncpg driver / Асинхронный URL БД с драйвером asyncpg
        """
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.database_url


# Global settings instance / Глобальный экземпляр настроек
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create global settings instance.

    Получить или создать глобальный экземпляр настроек.

    Returns:
        Application settings instance / Экземпляр настроек приложения

    Example:
        >>> settings = get_settings()
        >>> print(settings.database_url)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        logger.info(f"Loaded Candidate Service configuration (log_level={_settings.log_level}, port={_settings.service_port})")
    return _settings
