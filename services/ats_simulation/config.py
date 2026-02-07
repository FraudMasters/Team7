"""
Конфигурация приложения для ATS Simulation Service.

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
        redis_url: URL подключения к Redis для кэширования
        service_host: Хост для привязки FastAPI сервера
        service_port: Порт для привязки FastAPI сервера
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        llm_provider: Провайдер LLM для ATS-симуляции
        llm_model: Модель LLM для использования
        ats_threshold: Порог проходного балла ATS (0.0-1.0)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration / Конфигурация базы данных
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/ats_service",
        description="URL подключения к базе данных PostgreSQL",
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
        default=8007,
        description="Порт для привязки FastAPI сервера",
    )

    # Logging Configuration / Конфигурация логирования
    log_level: str = Field(
        default="INFO",
        description="Уровень логирования",
    )

    # LLM API Configuration / Конфигурация LLM API
    llm_provider: str = Field(
        default="zai",
        description="Провайдер LLM (openai, anthropic, google, zai)",
    )

    zai_api_key: Optional[str] = Field(
        default=None,
        description="API ключ Z.ai для ATS-симуляции",
    )

    zai_base_url: str = Field(
        default="https://api.z.ai/api/paas/v4",
        description="Базовый URL Z.ai API",
    )

    openai_api_key: Optional[str] = Field(
        default=None,
        description="API ключ OpenAI для ATS-симуляции",
    )

    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="API ключ Anthropic для ATS-симуляции",
    )

    google_api_key: Optional[str] = Field(
        default=None,
        description="API ключ Google для Gemini моделей",
    )

    llm_model: str = Field(
        default="glm-4.7",
        description="Модель LLM для ATS-симуляции",
    )

    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Температура для вызовов LLM (меньше = более детерминированно)",
    )

    llm_max_tokens: int = Field(
        default=4096,
        ge=256,
        le=32768,
        description="Максимальное количество токенов в ответах LLM",
    )

    # ATS Simulation Configuration / Конфигурация ATS-симуляции
    ats_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Минимальный балл ATS для прохода (0.0-1.0)",
    )

    ats_visual_check_enabled: bool = Field(
        default=True,
        description="Включить проверку визуального формата в ATS",
    )

    ats_keyword_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Вес сопоставления ключевых слов в оценке ATS",
    )

    ats_experience_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Вес сопоставления опыта в оценке ATS",
    )

    ats_education_weight: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Вес сопоставления образования в оценке ATS",
    )

    ats_fit_weight: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Вес общей оценки соответствия в ATS",
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
        logger.info(f"Loaded ATS Simulation Service configuration (log_level={_settings.log_level})")
    return _settings
