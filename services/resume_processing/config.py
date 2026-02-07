"""
Application configuration for Resume Processing Service.

This module uses pydantic-settings to load and validate configuration
from environment variables with sensible defaults.
"""
import logging
from pathlib import Path
from typing import List, Optional

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        database_url: PostgreSQL database connection URL
        redis_url: Redis connection URL for caching and Celery
        service_host: Host to bind the FastAPI server
        service_port: Port to bind the FastAPI server
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        celery_broker_url: Celery broker URL
        celery_result_backend: Celery result backend URL
        models_cache_path: Path to cache ML models
        processing_timeout_seconds: Maximum time for resume processing
        max_file_size_mb: Maximum file size for processing
        allowed_file_types: Comma-separated list of allowed file extensions
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/resume_analysis",
        description="PostgreSQL database connection URL",
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and Celery",
    )

    # Service Server Configuration
    service_host: str = Field(
        default="0.0.0.0",
        description="Host to bind the FastAPI server",
    )

    service_port: int = Field(
        default=8001,
        description="Port to bind the FastAPI server",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # Celery Configuration
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL",
    )

    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL",
    )

    # ML Models Configuration
    models_cache_path: Path = Field(
        default=Path("./models_cache"),
        description="Path to cache ML models",
    )

    # Processing Configuration
    processing_timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=600,
        description="Maximum time for resume processing in seconds",
    )

    # File Upload Configuration
    max_file_size_mb: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum file size for processing in megabytes",
    )

    allowed_file_types: str = Field(
        default=".pdf,.docx,.doc",
        description="Allowed file extensions for processing (comma-separated)",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+async://")):
            logger.warning(
                f"Database URL should start with 'postgresql://' or 'postgresql+async://', got: {v[:20]}..."
            )
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate and uppercase log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            logger.warning(f"Invalid log level '{v}', defaulting to INFO")
            return "INFO"
        return v_upper

    @property
    def max_file_size_bytes(self) -> int:
        """Convert max_file_size_mb to bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def cors_origins(self) -> List[str]:
        """Get list of allowed CORS origins."""
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
        Get async database URL for SQLAlchemy async engine.

        Returns:
            Async database URL with asyncpg driver
        """
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.database_url


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create global settings instance.

    Returns:
        Application settings instance

    Example:
        >>> settings = get_settings()
        >>> print(settings.database_url)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        logger.info(f"Loaded Resume Processing Service configuration (log_level={_settings.log_level})")
    return _settings
