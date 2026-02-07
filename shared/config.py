"""
Базовая конфигурация микросервисов с использованием переменных окружения.

Этот модуль предоставляет базовый класс конфигурации для всех микросервисов,
используя pydantic-settings для загрузки и валидации настроек из переменных
окружения с разумными значениями по умолчанию.
"""
import logging
from pathlib import Path
from typing import List, Optional

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class ServiceSettings(BaseSettings):
    """
    Базовые настройки микросервиса, загружаемые из переменных окружения.

    Этот класс предоставляет общую конфигурацию для всех микросервисов,
    включая настройки базы данных, Redis, сервера, логирования и
    обнаружения сервисов.

    Атрибуты:
        service_name: Название микросервиса для логирования и метрик
        service_port: Порт, на котором запускается микросервис
        database_url: URL подключения к PostgreSQL
        redis_url: URL подключения к Redis для кэширования и Celery
        host: Хост для привязки сервера
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Окружение развертывания (development, staging, production)
        enable_tracing: Включить распределенную трассировку с Jaeger
        jaeger_host: Хост агента Jaeger
        jaeger_port: Порт агента Jaeger
        trace_sample_rate: Частота выборки трасс (0.0-1.0)
        service_registry_enabled: Включить регистрацию сервисов в Consul
        consul_host: Хост Consul для обнаружения сервисов
        consul_port: Порт Consul
        consul_token: Токен для авторизации в Consul
        health_check_interval: Интервал проверок работоспособности в секундах
        max_request_size_mb: Максимальный размер запроса в мегабайтах
        timeout_seconds: Тайм-аут выполнения запросов в секундах
        worker_processes: Количество процессов-воркеров
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================
    # Идентификация сервиса
    # ==========================================
    service_name: str = Field(
        default="service",
        description="Название микросервиса для логирования и метрик",
    )

    service_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Порт, на котором запускается микросервис",
    )

    # ==========================================
    # Конфигурация базы данных
    # ==========================================
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/resume_analysis",
        description="URL подключения к PostgreSQL",
    )

    database_pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Размер пула соединений с базой данных",
    )

    database_max_overflow: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Максимальное количество дополнительных соединений",
    )

    # ==========================================
    # Конфигурация Redis
    # ==========================================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="URL подключения к Redis для кэширования и Celery",
    )

    redis_db: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Номер базы данных Redis",
    )

    redis_max_connections: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Максимальное количество соединений с Redis",
    )

    # ==========================================
    # Конфигурация сервера
    # ==========================================
    host: str = Field(
        default="0.0.0.0",
        description="Хост для привязки сервера",
    )

    workers: int = Field(
        default=1,
        ge=1,
        le=32,
        description="Количество воркеров для обработки запросов",
    )

    # ==========================================
    # Конфигурация логирования
    # ==========================================
    log_level: str = Field(
        default="INFO",
        description="Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    log_format: str = Field(
        default="json",
        description="Формат логов (json, text)",
    )

    log_file: Optional[Path] = Field(
        default=None,
        description="Путь к файлу логов (если указан, логи пишутся в файл)",
    )

    # ==========================================
    # Конфигурация окружения
    # ==========================================
    environment: str = Field(
        default="development",
        description="Окружение развертывания (development, staging, production)",
    )

    debug: bool = Field(
        default=False,
        description="Режим отладки",
    )

    # ==========================================
    # Конфигурация распределенной трассировки
    # ==========================================
    enable_tracing: bool = Field(
        default=True,
        description="Включить распределенную трассировку с Jaeger",
    )

    jaeger_host: str = Field(
        default="localhost",
        description="Хост агента Jaeger",
    )

    jaeger_port: int = Field(
        default=6831,
        ge=1,
        le=65535,
        description="Порт агента Jaeger",
    )

    trace_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Частота выборки трасс (0.0-1.0, где 1.0 - все запросы)",
    )

    # ==========================================
    # Конфигурация обнаружения сервисов (Consul)
    # ==========================================
    service_registry_enabled: bool = Field(
        default=False,
        description="Включить регистрацию сервисов в Consul",
    )

    consul_host: str = Field(
        default="localhost",
        description="Хост Consul для обнаружения сервисов",
    )

    consul_port: int = Field(
        default=8500,
        ge=1,
        le=65535,
        description="Порт Consul",
    )

    consul_token: Optional[str] = Field(
        default=None,
        description="Токен для авторизации в Consul (если требуется)",
    )

    consul_scheme: str = Field(
        default="http",
        description="Схема подключения к Consul (http или https)",
    )

    health_check_interval: int = Field(
        default=10,
        ge=1,
        le=300,
        description="Интервал проверок работоспособности в секундах",
    )

    health_check_timeout: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Тайм-аут проверки работоспособности в секундах",
    )

    # ==========================================
    # Конфигурация обработки запросов
    # ==========================================
    max_request_size_mb: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Максимальный размер запроса в мегабайтах",
    )

    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=600,
        description="Тайм-аут выполнения запросов в секундах",
    )

    keepalive_timeout: int = Field(
        default=5,
        ge=1,
        le=300,
        description="Тайм-аут поддержания соединения в секундах",
    )

    # ==========================================
    # Конфигурация Celery (для фоновых задач)
    # ==========================================
    celery_enabled: bool = Field(
        default=False,
        description="Включить поддержку Celery для фоновых задач",
    )

    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="URL брокера Celery (Redis)",
    )

    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        description="URL бэкенда результатов Celery",
    )

    celery_task_routes: dict = Field(
        default={},
        description="Маршруты задач Celery для распределения по очередям",
    )

    # ==========================================
    # Конфигурация API Gateway
    # ==========================================
    api_gateway_url: Optional[str] = Field(
        default=None,
        description="URL API Gateway для регистрации эндпоинтов",
    )

    api_gateway_token: Optional[str] = Field(
        default=None,
        description="Токен для авторизации в API Gateway",
    )

    # ==========================================
    # Валидаторы
    # ==========================================
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Проверить формат URL базы данных."""
        if not v.startswith(("postgresql://", "postgresql+async://")):
            logger.warning(
                f"URL базы данных должен начинаться с 'postgresql://' или 'postgresql+async://', получено: {v[:20]}..."
            )
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Проверить и привести к верхнему регистру уровень логирования."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            logger.warning(f"Недопустимый уровень логирования '{v}', используется значение INFO")
            return "INFO"
        return v_upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Проверить окружение развертывания."""
        valid_envs = ["development", "staging", "production", "testing"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            logger.warning(f"Недопустимое окружение '{v}', используется значение development")
            return "development"
        return v_lower

    @field_validator("consul_scheme")
    @classmethod
    def validate_consul_scheme(cls, v: str) -> str:
        """Проверить схему подключения к Consul."""
        valid_schemes = ["http", "https"]
        v_lower = v.lower()
        if v_lower not in valid_schemes:
            logger.warning(f"Недопустимая схема '{v}', используется значение http")
            return "http"
        return v_lower

    # ==========================================
    # Свойства (Properties)
    # ==========================================
    @property
    def max_request_size_bytes(self) -> int:
        """Конвертировать max_request_size_mb в байты."""
        return self.max_request_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Проверить, является ли окружение production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Проверить, является ли окружение development."""
        return self.environment == "development"

    @property
    def service_url(self) -> str:
        """Получить полный URL сервиса."""
        return f"http://{self.host}:{self.service_port}"

    @property
    def health_check_url(self) -> str:
        """Получить URL эндпоинта Health Check."""
        return f"{self.service_url}/health"

    @property
    def consul_url(self) -> str:
        """Получить полный URL Consul."""
        return f"{self.consul_scheme}://{self.consul_host}:{self.consul_port}"

    # ==========================================
    # Методы
    # ==========================================
    def get_db_url_async(self) -> str:
        """
        Получить асинхронный URL базы данных для SQLAlchemy async engine.

        Возвращает:
            Асинхронный URL базы данных с драйвером asyncpg
        """
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.database_url

    def get_redis_db(self) -> int:
        """
        Получить номер базы данных Redis для конкретного сервиса.

        Каждый сервис может использовать свою базу данных Redis,
        основываясь на номере порта или другой логике.

        Возвращает:
            Номер базы данных Redis (0-15)
        """
        # Используем последнюю цифру порта для определения базы данных
        return self.service_port % 15

    def get_celery_queue_name(self) -> str:
        """
        Получить имя очереди Celery для сервиса.

        Возвращает:
            Имя очереди Celery
        """
        return f"{self.service_name}_queue"

    def get_service_id(self) -> str:
        """
        Получить уникальный идентификатор сервиса.

        Возвращает:
            Уникальный идентификатор сервиса
        """
        return f"{self.service_name}-{self.service_port}"


# Глобальный экземпляр настроек
_settings_cache: dict = {}


def get_service_settings(service_name: str, service_port: int) -> ServiceSettings:
    """
    Получить или создать экземпляр настроек для конкретного сервиса.

    Эта функция использует кэширование для создания только одного экземпляра
    настроек для каждой комбинации (service_name, service_port).

    Аргументы:
        service_name: Название микросервиса
        service_port: Порт микросервиса

    Возвращает:
        Экземпляр настроек микросервиса

    Пример:
        >>> settings = get_service_settings("resume_processing", 8001)
        >>> print(settings.service_name)
        resume_processing
        >>> print(settings.database_url)
        postgresql://...
    """
    cache_key = f"{service_name}:{service_port}"

    if cache_key not in _settings_cache:
        settings = ServiceSettings(
            service_name=service_name,
            service_port=service_port,
        )
        _settings_cache[cache_key] = settings
        logger.info(
            f"Загружена конфигурация для сервиса '{service_name}' "
            f"(порт={service_port}, уровень логов={settings.log_level})"
        )

    return _settings_cache[cache_key]
