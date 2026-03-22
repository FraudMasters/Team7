"""
Base configuration class for application settings.

This module contains the base configuration class with all common
settings that are shared across environments.
"""
import logging
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .encryption import (
    decrypt_value,
    encrypt_value,
    generate_encryption_key,
    is_encrypted_value,
)
from .validators import validate_database_url, validate_log_level

logger = logging.getLogger(__name__)


class BaseConfig(BaseSettings):
    """
    Base application settings loaded from environment variables.

    This class contains all common configuration settings that are
    shared across development, staging, and production environments.

    Attributes:
        environment: Current environment name (development, staging, production)
        database_url: PostgreSQL database connection URL
        redis_url: Redis connection URL for Celery
        backend_host: Host to bind the FastAPI server
        backend_port: Port to bind the FastAPI server
        frontend_url: Frontend URL for CORS configuration
        models_cache_path: Path to cache ML models
        languagetool_server: LanguageTool server URL for grammar checking
        max_upload_size_mb: Maximum file upload size in megabytes
        allowed_file_types: Comma-separated list of allowed file extensions
        analysis_timeout_seconds: Maximum time for resume analysis
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rate_limit_per_minute: API rate limit (requests per minute per IP)
        celery_broker_url: Celery broker URL
        celery_result_backend: Celery result backend URL
        backup_retention_days: Default backup retention period in days
        audit_log_retention_days: Default audit log retention period in days
        mlflow_enabled: Whether MLflow experiment tracking is enabled
        mlflow_tracking_uri: MLflow tracking server URI
        mlflow_registry_uri: MLflow model registry URI
        mlflow_artifact_root: Root directory for MLflow artifacts
        mlflow_experiment_prefix: Prefix for MLflow experiment names
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: str = Field(
        default="development",
        description="Current environment (development, staging, production)",
    )

    # Database Configuration
    database_url: str = Field(
        default="",
        description="PostgreSQL database connection URL (must be set via environment variable)",
    )

    # Redis Configuration
    redis_url: str = Field(
        default="",
        description="Redis connection URL for caching and Celery (must be set via environment variable)",
    )

    # Backend Server Configuration
    backend_host: str = Field(
        default="0.0.0.0",
        description="Host to bind the FastAPI server",
    )
    backend_port: int = Field(
        default=8000,
        description="Port to bind the FastAPI server",
    )

    # Frontend Configuration for CORS
    frontend_url: str = Field(
        default="",
        description="Frontend URL for CORS configuration (must be set via environment variable)",
    )

    # ML Models Configuration
    models_cache_path: Path = Field(
        default=Path("./models_cache"),
        description="Path to cache ML models",
    )

    # LanguageTool Server Configuration
    languagetool_server: Optional[str] = Field(
        default=None,
        description="LanguageTool server URL for grammar checking",
    )

    # File Upload Configuration
    max_upload_size_mb: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum file upload size in megabytes",
    )

    allowed_file_types: str = Field(
        default=".pdf,.docx",
        description="Allowed file extensions for upload (comma-separated)",
    )

    # Analysis Configuration
    analysis_timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=600,
        description="Maximum time for resume analysis in seconds",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # Rate Limiting Configuration
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        le=10000,
        description="API rate limit (requests per minute per IP)",
    )

    # Celery Configuration
    celery_broker_url: str = Field(
        default="",
        description="Celery broker URL (must be set via environment variable)",
    )

    celery_result_backend: str = Field(
        default="",
        description="Celery result backend URL (must be set via environment variable)",
    )

    # Backup Configuration
    backup_enabled: bool = Field(
        default=True,
        description="Enable automated backups",
    )

    backup_retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Default backup retention period in days",
    )

    backup_schedule: str = Field(
        default="0 2 * * *",
        description="Cron expression for scheduled backups (default: daily at 2 AM)",
    )

    backup_dir: Path = Field(
        default=Path("./data/backups"),
        description="Directory for storing backup files",
    )

    upload_dir: Path = Field(
        default=Path("./data/uploads"),
        description="Directory for storing uploaded resume files",
    )

    # S3 Backup Configuration
    backup_s3_enabled: bool = Field(
        default=False,
        description="Enable S3 off-site backup",
    )

    backup_s3_bucket: Optional[str] = Field(
        default=None,
        description="S3 bucket name for backups",
    )

    backup_s3_endpoint: Optional[str] = Field(
        default=None,
        description="S3-compatible endpoint URL",
    )

    backup_s3_access_key: Optional[str] = Field(
        default=None,
        description="S3 access key ID",
    )

    backup_s3_secret_key: Optional[str] = Field(
        default=None,
        description="S3 secret access key",
    )

    backup_s3_region: str = Field(
        default="us-east-1",
        description="S3 region",
    )

    backup_notification_email: Optional[str] = Field(
        default=None,
        description="Email for backup failure notifications",
    )

    backup_incremental_enabled: bool = Field(
        default=True,
        description="Enable incremental backups",
    )

    backup_compression_enabled: bool = Field(
        default=True,
        description="Enable backup compression",
    )

    # Audit Log Configuration
    audit_log_retention_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Default audit log retention period in days",
    )

    # ==============================================
    # LLM API Configuration for ATS Simulation
    # ==============================================
    llm_provider: str = Field(
        default="zai",
        description="LLM provider to use (openai, anthropic, google, zai)",
    )

    zai_api_key: Optional[str] = Field(
        default=None,
        description="Z.ai API key for ATS simulation",
    )

    zai_base_url: str = Field(
        default="https://api.z.ai/api/paas/v4",
        description="Z.ai API base URL",
    )

    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for ATS simulation",
    )

    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for ATS simulation",
    )

    google_api_key: Optional[str] = Field(
        default=None,
        description="Google API key for Gemini models",
    )

    llm_model: str = Field(
        default="glm-4.7",
        description="Default LLM model for ATS simulation",
    )

    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Temperature for LLM calls (lower = more deterministic)",
    )

    llm_max_tokens: int = Field(
        default=4096,
        ge=256,
        le=32768,
        description="Maximum tokens for LLM responses",
    )

    # ATS Simulation Configuration
    ats_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum ATS score to pass (0.0-1.0)",
    )

    ats_visual_check_enabled: bool = Field(
        default=True,
        description="Enable visual format checking in ATS",
    )

    ats_keyword_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for keyword matching in ATS score",
    )

    ats_experience_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for experience matching in ATS score",
    )

    ats_education_weight: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Weight for education matching in ATS score",
    )

    ats_fit_weight: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Weight for overall fit assessment in ATS score",
    )

    # ==============================================
    # MLflow Experiment Tracking Configuration
    # ==============================================
    mlflow_enabled: bool = Field(
        default=False,
        description="Enable MLflow experiment tracking for ML models",
    )

    mlflow_tracking_uri: Optional[str] = Field(
        default=None,
        description="MLflow tracking server URI (e.g., http://localhost:5000, sqlite:///mlflow.db)",
    )

    mlflow_registry_uri: Optional[str] = Field(
        default=None,
        description="MLflow model registry URI (defaults to tracking_uri if not set)",
    )

    mlflow_artifact_root: str = Field(
        default="./mlruns",
        description="Root directory for MLflow artifacts (for local tracking)",
    )

    mlflow_experiment_prefix: str = Field(
        default="agenthr",
        description="Prefix for MLflow experiment names",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url_field(cls, v: str) -> str:
        """Validate database URL format."""
        return validate_database_url(v)

    @field_validator("log_level")
    @classmethod
    def validate_log_level_field(cls, v: str) -> str:
        """Validate and uppercase log level."""
        return validate_log_level(v)

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert max_upload_size_mb to bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def cors_origins(self) -> List[str]:
        """Get list of allowed CORS origins from configuration."""
        origins = []
        if self.frontend_url:
            origins.append(self.frontend_url)
        return origins

    def get_db_url_async(self) -> str:
        """
        Get async database URL for SQLAlchemy async engine.

        Returns:
            Async database URL with asyncpg driver
        """
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.database_url
