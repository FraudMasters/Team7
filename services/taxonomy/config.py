"""
Application configuration for Taxonomy Service.

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
        database_url: PostgreSQL connection URL
        redis_url: Redis connection URL for caching
        service_host: Host for FastAPI server binding
        service_port: Port for FastAPI server binding
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
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
        description="PostgreSQL connection URL",
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching",
    )

    # Service Server Configuration
    service_host: str = Field(
        default="0.0.0.0",
        description="Host for FastAPI server binding",
    )

    service_port: int = Field(
        default=8005,
        description="Port for FastAPI server binding",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level",
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
        """Validate and normalize log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            logger.warning(f"Invalid log level '{v}', defaulting to INFO")
            return "INFO"
        return v_upper

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
            "http://localhost:8888",
            "http://127.0.0.1:8888",
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
        logger.info(f"Taxonomy Service configuration loaded (log_level={_settings.log_level})")
    return _settings
