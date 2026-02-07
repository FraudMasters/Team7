"""
Конфигурация приложения для Integration Service.

# Русский комментарий:
Этот модуль использует pydantic-settings для загрузки и проверки конфигурации
из переменных окружения с разумными значениями по умолчанию.
"""
import logging
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Настройки приложения, загружаемые из переменных окружения.

    Attributes:
        database_url: URL подключения к базе данных PostgreSQL
        redis_url: URL подключения к Redis для кэширования
        service_host: Хост для привязки FastAPI сервера
        service_port: Порт для привязки FastAPI сервера (по умолчанию: 8009)
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        integration_db_schema: Имя схемы базы данных для таблиц сервиса интеграций
        linkedin_client_id: Client ID для LinkedIn API
        linkedin_client_secret: Client Secret для LinkedIn API
        linkedin_redirect_uri: Redirect URI для LinkedIn OAuth
        linkedin_api_timeout: Таймаут запросов к LinkedIn API
        job_board_timeout: Таймаут запросов к job board API
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration / Конфигурация базы данных
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/integrations_service",
        description="URL подключения к базе данных PostgreSQL",
    )

    # Database Schema for Integration Service / Схема БД для сервиса интеграций
    integration_db_schema: str = Field(
        default="integrations_service",
        description="Имя схемы базы данных для таблиц сервиса интеграций",
    )

    # Redis Configuration / Конфигурация Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="URL подключения к Redis для кэширования",
    )

    # Service Server Configuration / Конфигурация сервера сервиса
    service_host: str = Field(
        default="0.0.0.0",
        description="Хост для привязки FastAPI сервера",
    )

    service_port: int = Field(
        default=8009,
        description="Порт для привязки FastAPI сервера",
    )

    # Logging Configuration / Конфигурация логирования
    log_level: str = Field(
        default="INFO",
        description="Уровень логирования",
    )

    # LinkedIn Configuration / Конфигурация LinkedIn
    linkedin_client_id: str = Field(
        default="",
        description="Client ID для LinkedIn API",
    )

    linkedin_client_secret: str = Field(
        default="",
        description="Client Secret для LinkedIn API",
    )

    linkedin_redirect_uri: str = Field(
        default="http://localhost:8888/api/integrations/linkedin/callback",
        description="Redirect URI для LinkedIn OAuth",
    )

    linkedin_api_timeout: int = Field(
        default=30,
        description="Таймаут запросов к LinkedIn API в секундах",
    )

    # Job Board Configuration / Конфигурация Job Boards
    job_board_timeout: int = Field(
        default=30,
        description="Таймаут запросов к job board API в секундах",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Проверка формата URL базы данных."""
        if not v.startswith(("postgresql://", "postgresql+async://")):
            logger.warning(
                f"Database URL should start with 'postgresql://' or 'postgresql+async://', got: {v[:20]}..."
            )
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Проверка и приведение к верхнему регистру уровня логирования."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            logger.warning(f"Invalid log level '{v}', defaulting to INFO")
            return "INFO"
        return v_upper

    @property
    def cors_origins(self) -> List[str]:
        """Получить список разрешенных CORS источников."""
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
        Получить асинхронный URL базы данных для SQLAlchemy async engine.

        Returns:
            Асинхронный URL базы данных с драйвером asyncpg
        """
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.database_url


# Global settings instance / Глобальный экземпляр настроек
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Получить или создать глобальный экземпляр настроек.

    Returns:
        Экземпляр настроек приложения

    Example:
        >>> settings = get_settings()
        >>> print(settings.database_url)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        logger.info(f"Loaded Integration Service configuration (log_level={_settings.log_level}, port={_settings.service_port})")
    return _settings
