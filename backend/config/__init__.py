"""
Centralized configuration management system.

This package provides a hierarchical configuration system with:
- BaseConfig: Base configuration with all common settings
- Environment-specific configs: Development, Staging, Production
- Validators: Common validation functions
- Validation: Startup configuration validation
- Convenience functions for getting configuration

Example usage:
    >>> from config import get_settings, get_environment_config
    >>>
    >>> # Get base settings (respects ENVIRONMENT variable)
    >>> settings = get_settings()
    >>>
    >>> # Get specific environment config
    >>> dev_config = get_environment_config("development")
    >>> prod_config = get_environment_config("production")
    >>>
    >>> # Validate configuration
    >>> from config.validation import validate_config
    >>> warnings = validate_config(settings)
"""

import logging
import os
from typing import Optional

from .base import BaseConfig
from .environments import (
    DevelopmentConfig,
    ProductionConfig,
    StagingConfig,
    get_environment_config,
)
from .validators import (
    validate_database_url,
    validate_environment,
    validate_log_level,
)
from . import validation

logger = logging.getLogger(__name__)

__all__ = [
    # Base configuration
    "BaseConfig",
    # Environment configurations
    "DevelopmentConfig",
    "StagingConfig",
    "ProductionConfig",
    # Convenience functions
    "get_settings",
    "get_environment_config",
    # Validators
    "validate_database_url",
    "validate_log_level",
    "validate_environment",
    # Validation module
    "validation",
]

# Global settings instance (singleton pattern)
_settings: Optional[BaseConfig] = None


def get_settings() -> BaseConfig:
    """
    Get or create global settings instance.

    This function respects the ENVIRONMENT environment variable and
    returns the appropriate configuration instance. It implements
    the singleton pattern to ensure only one configuration instance
    is created per application lifecycle.

    Returns:
        Application settings instance for the current environment

    Example:
        >>> settings = get_settings()
        >>> print(settings.database_url)
        postgresql://...
        >>> print(settings.environment)
        development
    """
    global _settings

    if _settings is None:
        # Get environment from ENVIRONMENT variable, default to development
        environment = os.getenv("ENVIRONMENT", "development").lower()

        # Use get_environment_config to get the right config class
        _settings = get_environment_config(environment)

        logger.info(
            f"Loaded {_settings.environment} configuration "
            f"(log_level={_settings.log_level})"
        )

    return _settings


def reload_settings() -> BaseConfig:
    """
    Force reload of settings from environment variables.

    This function clears the cached settings instance and creates
    a new one, useful for testing or when environment variables
    change at runtime.

    Returns:
        Fresh application settings instance

    Example:
        >>> os.environ["ENVIRONMENT"] = "production"
        >>> settings = reload_settings()
        >>> print(settings.environment)
        production
    """
    global _settings
    _settings = None
    return get_settings()
