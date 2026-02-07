"""
Environment-specific configuration profiles.

This module contains configuration classes for different environments
(development, staging, production) that extend the base configuration.
"""
import logging
import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field

from .base import BaseConfig

logger = logging.getLogger(__name__)


class DevelopmentConfig(BaseConfig):
    """
    Development environment configuration.

    This configuration is optimized for local development with:
    - Verbose logging (DEBUG level)
    - Detailed error messages
    - Development-optimized settings
    - Relaxed security settings
    """

    environment: str = Field(
        default="development",
        description="Environment name",
    )

    log_level: str = Field(
        default="DEBUG",
        description="Logging level for development",
    )

    # Development defaults for local services
    backend_host: str = Field(
        default="",
        description="Host to bind the FastAPI server in development (from env var or YAML)",
    )

    backend_port: int = Field(
        default=8000,
        description="Port to bind the FastAPI server in development",
    )

    frontend_url: str = Field(
        default="",
        description="Frontend URL for CORS in development (from env var or YAML)",
    )

    # More permissive upload limits for development
    max_upload_size_mb: int = Field(
        default=20,
        description="Maximum file upload size in development",
    )

    # Shorter timeouts for development debugging
    analysis_timeout_seconds: int = Field(
        default=600,
        ge=30,
        le=600,
        description="Maximum time for resume analysis in development",
    )

    # Disabled backups in development
    backup_enabled: bool = Field(
        default=False,
        description="Disable automated backups in development",
    )


class StagingConfig(BaseConfig):
    """
    Staging environment configuration.

    This configuration is for pre-production testing with:
    - INFO level logging
    - Production-like settings
    - Staging-specific URLs
    - Enabled backups with shorter retention
    """

    environment: str = Field(
        default="staging",
        description="Environment name",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level for staging",
    )

    # Staging-specific configuration
    frontend_url: str = Field(
        default="https://staging.example.com",
        description="Frontend URL for CORS in staging",
    )

    # Moderate upload limits
    max_upload_size_mb: int = Field(
        default=10,
        description="Maximum file upload size in staging",
    )

    # Production-like timeouts
    analysis_timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=600,
        description="Maximum time for resume analysis in staging",
    )

    # Enabled backups with shorter retention
    backup_enabled: bool = Field(
        default=True,
        description="Enable automated backups in staging",
    )

    backup_retention_days: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Backup retention period in staging (shorter for cost savings)",
    )

    # Audit log retention
    audit_log_retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Audit log retention period in staging",
    )


class ProductionConfig(BaseConfig):
    """
    Production environment configuration.

    This configuration is optimized for production deployment with:
    - WARNING level logging (less verbose)
    - Production URLs
    - Strict security settings
    - Full backup and audit retention
    """

    environment: str = Field(
        default="production",
        description="Environment name",
    )

    log_level: str = Field(
        default="WARNING",
        description="Logging level for production",
    )

    # Production-specific configuration
    frontend_url: str = Field(
        default="https://app.example.com",
        description="Frontend URL for CORS in production",
    )

    # Standard upload limits
    max_upload_size_mb: int = Field(
        default=10,
        description="Maximum file upload size in production",
    )

    # Production timeouts
    analysis_timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=600,
        description="Maximum time for resume analysis in production",
    )

    # Full backup retention
    backup_enabled: bool = Field(
        default=True,
        description="Enable automated backups in production",
    )

    backup_retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Backup retention period in production",
    )

    # Full audit log retention
    audit_log_retention_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Audit log retention period in production",
    )


# Environment configuration mapping
ENVIRONMENT_CONFIGS = {
    "development": DevelopmentConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
}


def get_environment_config(environment: Optional[str] = None) -> BaseConfig:
    """
    Get configuration class for the specified environment.

    Args:
        environment: Environment name (development, staging, production).
                    If None, reads from ENVIRONMENT environment variable.

    Returns:
        Configuration instance for the specified environment

    Raises:
        ValueError: If environment is not recognized

    Example:
        >>> config = get_environment_config("development")
        >>> print(config.environment)
        development
    """
    import os

    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")

    environment_lower = environment.lower()
    config_class = ENVIRONMENT_CONFIGS.get(environment_lower)

    if config_class is None:
        valid = ", ".join(ENVIRONMENT_CONFIGS.keys())
        raise ValueError(
            f"Invalid environment '{environment}'. "
            f"Valid options: {valid}"
        )

    logger.info(f"Loading {environment} configuration")
    return config_class()


def load_config_file(environment: Optional[str] = None) -> BaseConfig:
    """
    Load configuration from environment-specific YAML file.

    This function reads the appropriate YAML config file based on the
    environment and creates a configuration object with those values.

    Args:
        environment: Environment name (dev, staging, production).
                    If None, reads from ENVIRONMENT environment variable.
                    Accepts both short names (dev, staging, prod) and
                    full names (development, staging, production).

    Returns:
        Configuration instance loaded from the YAML file

    Raises:
        ValueError: If environment is not recognized or config file not found
        FileNotFoundError: If the config file doesn't exist

    Example:
        >>> import os
        >>> os.environ['ENVIRONMENT'] = 'dev'
        >>> cfg = load_config_file()
        >>> print(cfg.environment)
        dev
    """
    # Get environment from parameter or ENVIRONMENT variable
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "dev")

    # Normalize environment name to short form
    env_map = {
        "dev": "dev",
        "development": "dev",
        "staging": "staging",
        "prod": "production",
        "production": "production",
    }

    environment_lower = environment.lower()
    if environment_lower not in env_map:
        valid = ", ".join(env_map.keys())
        raise ValueError(
            f"Invalid environment '{environment}'. "
            f"Valid options: {valid}"
        )

    env_short = env_map[environment_lower]

    # Map short env to config class (use full names for classes)
    class_env_map = {
        "dev": "development",
        "staging": "staging",
        "production": "production",
    }

    class_env = class_env_map.get(env_short, env_short)

    # Build config file path
    config_dir = Path(__file__).parent
    config_file = config_dir / f"config.{env_short}.yml"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_file}. "
            f"Please ensure config.{env_short}.yml exists in the config directory."
        )

    # Load YAML config file
    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)

    if config_data is None:
        config_data = {}

    # Get the appropriate config class
    config_class = ENVIRONMENT_CONFIGS.get(class_env)
    if config_class is None:
        raise ValueError(f"No config class found for environment: {class_env}")

    # Create config instance with YAML data
    # The YAML values override the defaults
    config = config_class(**config_data)

    logger.info(f"Loaded {config.environment} configuration from {config_file.name}")
    return config
