"""
Конфигурация приложения для Notification Service.

# Русский комментарий:
Этот модуль использует pydantic-settings для загрузки и проверки конфигурации
из переменных окружения с разумными значениями по умолчанию.
"""
import logging
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Настройки приложения, загружаемые из переменных окружения.

    Attributes:
        database_url: URL подключения к базе данных PostgreSQL
        redis_url: URL подключения к Redis для кэширования и Celery
        service_host: Хост для привязки FastAPI сервера
        service_port: Порт для привязки FastAPI сервера
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        celery_broker_url: URL брокера Celery
        celery_result_backend: URL бэкенда результатов Celery
        smtp_host: Хост SMTP сервера для отправки email
        smtp_port: Порт SMTP сервера
        smtp_username: Имя пользователя SMTP
        smtp_password: Пароль SMTP
        smtp_default_from: Email адрес отправителя по умолчанию
        smtp_use_tls: Использовать TLS для SMTP
        sms_provider: Провайдер SMS (twilio, sns, none)
        webhook_timeout: Таймаут для webhook запросов в секундах
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration / Конфигурация базы данных
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/notifications_service",
        description="URL подключения к базе данных PostgreSQL",
    )

    # Redis Configuration / Конфигурация Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="URL подключения к Redis для кэширования и Celery",
    )

    # Service Server Configuration / Конфигурация сервера сервиса
    service_host: str = Field(
        default="0.0.0.0",
        description="Хост для привязки FastAPI сервера",
    )

    service_port: int = Field(
        default=8008,
        description="Порт для привязки FastAPI сервера",
    )

    # Logging Configuration / Конфигурация логирования
    log_level: str = Field(
        default="INFO",
        description="Уровень логирования",
    )

    # Celery Configuration / Конфигурация Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="URL брокера Celery",
    )

    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        description="URL бэкенда результатов Celery",
    )

    # SMTP Configuration / Конфигурация SMTP
    smtp_host: str = Field(
        default="smtp.gmail.com",
        description="Хост SMTP сервера для отправки email",
    )

    smtp_port: int = Field(
        default=587,
        description="Порт SMTP сервера",
    )

    smtp_username: str = Field(
        default="",
        description="Имя пользователя SMTP",
    )

    smtp_password: str = Field(
        default="",
        description="Пароль SMTP",
    )

    smtp_default_from: str = Field(
        default="noreply@agenthr.com",
        description="Email адрес отправителя по умолчанию",
    )

    smtp_use_tls: bool = Field(
        default=True,
        description="Использовать TLS для SMTP",
    )

    # SMS Configuration / Конфигурация SMS
    sms_provider: str = Field(
        default="none",
        description="Провайдер SMS (twilio, sns, none)",
    )

    # Webhook Configuration / Конфигурация Webhook
    webhook_timeout: int = Field(
        default=10,
        description="Таймаут для webhook запросов в секундах",
    )

    # Email Templates Path / Путь к шаблонам email
    email_templates_path: Path = Field(
        default=Path("./email_templates"),
        description="Путь к шаблонам email",
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
        logger.info(f"Loaded Notification Service configuration (log_level={_settings.log_level})")
    return _settings
