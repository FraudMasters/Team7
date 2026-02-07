"""
Configuration validators for application settings.

This module contains common validators used across configuration classes.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def validate_database_url(value: str) -> str:
    """
    Validate database URL format.

    Args:
        value: Database URL to validate

    Returns:
        Validated database URL
    """
    if not value.startswith(("postgresql://", "postgresql+async://")):
        logger.warning(
            f"Database URL should start with 'postgresql://' or 'postgresql+async://', got: {value[:20]}..."
        )
    return value


def validate_log_level(value: str) -> str:
    """
    Validate and uppercase log level.

    Args:
        value: Log level to validate

    Returns:
        Uppercased valid log level
    """
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    value_upper = value.upper()
    if value_upper not in valid_levels:
        logger.warning(f"Invalid log level '{value}', defaulting to INFO")
        return "INFO"
    return value_upper


def validate_environment(value: str) -> str:
    """
    Validate environment name.

    Args:
        value: Environment name to validate

    Returns:
        Validated environment name
    """
    valid_environments = ["development", "staging", "production"]
    value_lower = value.lower()
    if value_lower not in valid_environments:
        logger.warning(f"Invalid environment '{value}', defaulting to development")
        return "development"
    return value_lower
