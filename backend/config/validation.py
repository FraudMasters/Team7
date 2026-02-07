"""
Configuration validation with startup checks.

This module provides comprehensive validation of application configuration
to ensure the application can start successfully with valid settings.
"""
import logging
from pathlib import Path
from typing import List, Optional

from config.base import BaseConfig

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Exception raised for configuration validation errors."""

    pass


class ValidationWarning:
    """Represents a non-critical validation warning."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message

    def __str__(self) -> str:
        return f"[{self.field}] {self.message}"


def validate_config(settings: BaseConfig) -> List[ValidationWarning]:
    """
    Validate application configuration with comprehensive startup checks.

    This function performs validation of critical configuration settings
    to ensure the application can start successfully. Critical errors will
    raise ConfigurationError, while non-critical issues return warnings.

    Args:
        settings: Application settings to validate

    Returns:
        List of non-critical validation warnings

    Raises:
        ConfigurationError: If critical configuration validation fails

    Example:
        >>> from config import get_settings
        >>> from config.validation import validate_config
        >>>
        >>> settings = get_settings()
        >>> warnings = validate_config(settings)
        >>> for warning in warnings:
        ...     logger.warning(warning)
    """
    warnings: List[ValidationWarning] = []

    # Validate critical settings
    _validate_database_config(settings, warnings)
    _validate_redis_config(settings, warnings)
    _validate_celery_config(settings, warnings)
    _validate_paths_config(settings, warnings)
    _validate_llm_config(settings, warnings)
    _validate_backup_config(settings, warnings)
    _validate_file_upload_config(settings, warnings)

    # Log all warnings
    for warning in warnings:
        logger.warning(f"Configuration warning: {warning}")

    return warnings


def _validate_database_config(settings: BaseConfig, warnings: List[ValidationWarning]) -> None:
    """
    Validate database configuration.

    Checks database URL format and required components.

    Args:
        settings: Application settings
        warnings: List to append warnings to

    Raises:
        ConfigurationError: If database URL is critically invalid
    """
    db_url = settings.database_url

    if not db_url:
        raise ConfigurationError("Database URL is not configured")

    # Check database URL format
    if not db_url.startswith(("postgresql://", "postgresql+asyncpg://")):
        raise ConfigurationError(
            f"Invalid database URL format: must start with 'postgresql://' or 'postgresql+asyncpg://', got: {db_url[:20]}..."
        )

    # Check for required URL components (without exposing credentials)
    # Extract hostname to check for loopback addresses
    from urllib.parse import urlparse
    import ipaddress
    import socket
    parsed = urlparse(db_url)
    hostname = parsed.hostname or ""

    # Check if hostname is a loopback address
    is_loopback = False
    if hostname:
        try:
            # Try to parse as IP address
            addr = ipaddress.ip_address(hostname)
            is_loopback = addr.is_loopback
        except ValueError:
            # Not an IP address, try to resolve and check
            try:
                # Try to resolve hostname to check if it's loopback
                addr_info = socket.getaddrinfo(hostname, None)
                if addr_info:
                    # Check if any resolved address is loopback
                    for family, _, _, _, sockaddr in addr_info:
                        ip = sockaddr[0]
                        try:
                            if ipaddress.ip_address(ip).is_loopback:
                                is_loopback = True
                                break
                        except ValueError:
                            pass
            except (socket.gaierror, socket.error):
                # Can't resolve, skip the check
                pass

    if is_loopback and settings.environment == "production":
        warnings.append(
            ValidationWarning(
                "database_url",
                "Using loopback address in production environment may cause connectivity issues"
            )
        )

    # Warn if default credentials are detected
    if ":postgres@" in db_url or ":password@" in db_url:
        warnings.append(
            ValidationWarning(
                "database_url",
                "Default database credentials detected - please change in production"
            )
        )


def _validate_redis_config(settings: BaseConfig, warnings: List[ValidationWarning]) -> None:
    """
    Validate Redis configuration.

    Checks Redis URL format and connectivity requirements.

    Args:
        settings: Application settings
        warnings: List to append warnings to

    Raises:
        ConfigurationError: If Redis URL is critically invalid
    """
    redis_url = settings.redis_url

    if not redis_url:
        raise ConfigurationError("Redis URL is not configured")

    # Check Redis URL format
    if not redis_url.startswith("redis://"):
        raise ConfigurationError(
            f"Invalid Redis URL format: must start with 'redis://', got: {redis_url[:20]}..."
        )

    # Warn if loopback address in production
    from urllib.parse import urlparse
    import ipaddress
    import socket
    parsed = urlparse(redis_url)
    hostname = parsed.hostname or ""

    # Check if hostname is a loopback address
    is_loopback = False
    if hostname:
        try:
            # Try to parse as IP address
            addr = ipaddress.ip_address(hostname)
            is_loopback = addr.is_loopback
        except ValueError:
            # Not an IP address, try to resolve and check
            try:
                # Try to resolve hostname to check if it's loopback
                addr_info = socket.getaddrinfo(hostname, None)
                if addr_info:
                    # Check if any resolved address is loopback
                    for family, _, _, _, sockaddr in addr_info:
                        ip = sockaddr[0]
                        try:
                            if ipaddress.ip_address(ip).is_loopback:
                                is_loopback = True
                                break
                        except ValueError:
                            pass
            except (socket.gaierror, socket.error):
                # Can't resolve, skip the check
                pass

    if is_loopback and settings.environment == "production":
        warnings.append(
            ValidationWarning(
                "redis_url",
                "Using loopback address for Redis in production environment may cause connectivity issues"
            )
        )


def _validate_celery_config(settings: BaseConfig, warnings: List[ValidationWarning]) -> None:
    """
    Validate Celery configuration.

    Checks broker and result backend URLs.

    Args:
        settings: Application settings
        warnings: List to append warnings to

    Raises:
        ConfigurationError: If Celery configuration is critically invalid
    """
    broker_url = settings.celery_broker_url
    result_backend = settings.celery_result_backend

    if not broker_url:
        raise ConfigurationError("Celery broker URL is not configured")

    if not result_backend:
        raise ConfigurationError("Celery result backend URL is not configured")

    # Check URL formats
    if not broker_url.startswith("redis://"):
        raise ConfigurationError(
            f"Invalid Celery broker URL format: must use Redis, got: {broker_url[:20]}..."
        )

    if not result_backend.startswith("redis://"):
        raise ConfigurationError(
            f"Invalid Celery result backend URL format: must use Redis, got: {result_backend[:20]}..."
        )

    # Warn if URLs differ
    if broker_url != result_backend:
        warnings.append(
            ValidationWarning(
                "celery_config",
                "Celery broker and result backend URLs differ - this may cause issues"
            )
        )


def _validate_paths_config(settings: BaseConfig, warnings: List[ValidationWarning]) -> None:
    """
    Validate file path configurations.

    Checks that critical paths exist or can be created.

    Args:
        settings: Application settings
        warnings: List to append warnings to
    """
    # Check models cache path
    models_path = settings.models_cache_path
    try:
        models_path.mkdir(parents=True, exist_ok=True)
        if not models_path.exists():
            warnings.append(
                ValidationWarning(
                    "models_cache_path",
                    f"Models cache path does not exist and could not be created: {models_path}"
                )
            )
    except PermissionError:
        warnings.append(
            ValidationWarning(
                "models_cache_path",
                f"Insufficient permissions to create models cache path: {models_path}"
            )
        )

    # Check backup directory
    backup_path = settings.backup_dir
    try:
        backup_path.mkdir(parents=True, exist_ok=True)
        if not backup_path.exists():
            warnings.append(
                ValidationWarning(
                    "backup_dir",
                    f"Backup directory does not exist and could not be created: {backup_path}"
                )
            )
    except PermissionError:
        warnings.append(
            ValidationWarning(
                "backup_dir",
                f"Insufficient permissions to create backup directory: {backup_path}"
            )
        )


def _validate_llm_config(settings: BaseConfig, warnings: List[ValidationWarning]) -> None:
    """
    Validate LLM API configuration.

    Checks that at least one LLM provider has an API key configured.

    Args:
        settings: Application settings
        warnings: List to append warnings to

    Raises:
        ConfigurationError: If LLM configuration is critically invalid
    """
    provider = settings.llm_provider
    api_key = None

    # Map provider to its API key field
    if provider == "zai":
        api_key = settings.zai_api_key
    elif provider == "openai":
        api_key = settings.openai_api_key
    elif provider == "anthropic":
        api_key = settings.anthropic_api_key
    elif provider == "google":
        api_key = settings.google_api_key
    else:
        warnings.append(
            ValidationWarning(
                "llm_provider",
                f"Unknown LLM provider: {provider}, defaulting to zai"
            )
        )
        api_key = settings.zai_api_key

    if not api_key:
        warnings.append(
            ValidationWarning(
                f"{provider}_api_key",
                f"No API key configured for {provider} - ATS simulation may not work properly"
            )
        )

    # Validate model configuration
    model = settings.llm_model
    if not model:
        warnings.append(
            ValidationWarning(
                "llm_model",
                "No LLM model configured - using default"
            )
        )


def _validate_backup_config(settings: BaseConfig, warnings: List[ValidationWarning]) -> None:
    """
    Validate backup configuration.

    Checks S3 backup settings if enabled.

    Args:
        settings: Application settings
        warnings: List to append warnings to
    """
    if not settings.backup_s3_enabled:
        return

    # S3 is enabled - check required fields
    required_fields = {
        "bucket": settings.backup_s3_bucket,
        "access_key": settings.backup_s3_access_key,
        "secret_key": settings.backup_s3_secret_key,
    }

    missing_fields = [
        field_name for field_name, field_value in required_fields.items() if not field_value
    ]

    if missing_fields:
        warnings.append(
            ValidationWarning(
                "backup_s3_config",
                f"S3 backup enabled but missing required fields: {', '.join(missing_fields)}"
            )
        )

    # Check endpoint for non-AWS S3
    if settings.backup_s3_endpoint and "amazonaws.com" not in settings.backup_s3_endpoint:
        # Using S3-compatible service - endpoint should be set
        if not settings.backup_s3_endpoint:
            warnings.append(
                ValidationWarning(
                    "backup_s3_endpoint",
                    "S3-compatible service detected but endpoint not configured"
                )
            )


def _validate_file_upload_config(settings: BaseConfig, warnings: List[ValidationWarning]) -> None:
    """
    Validate file upload configuration.

    Checks upload limits and allowed file types.

    Args:
        settings: Application settings
        warnings: List to append warnings to
    """
    # Check max upload size
    max_size = settings.max_upload_size_mb
    if max_size > 50:
        warnings.append(
            ValidationWarning(
                "max_upload_size_mb",
                f"Max upload size ({max_size}MB) is very large - consider reducing for security"
            )
        )

    # Check allowed file types
    allowed_types = settings.allowed_file_types
    if not allowed_types:
        warnings.append(
            ValidationWarning(
                "allowed_file_types",
                "No file types specified - uploads will be rejected"
            )
        )

    # Parse file types and validate format
    file_types = [t.strip() for t in allowed_types.split(",")]
    invalid_types = [t for t in file_types if not t.startswith(".")]
    if invalid_types:
        warnings.append(
            ValidationWarning(
                "allowed_file_types",
                f"Invalid file type format (should start with '.'): {', '.join(invalid_types)}"
            )
        )


def validate_startup_health(settings: BaseConfig) -> bool:
    """
    Quick health check for startup validation.

    This is a lightweight validation that checks only the most critical
    configuration settings. Use this for fast startup checks.

    Args:
        settings: Application settings to validate

    Returns:
        True if validation passes, False otherwise

    Example:
        >>> from config import get_settings
        >>> from config.validation import validate_startup_health
        >>>
        >>> settings = get_settings()
        >>> if validate_startup_health(settings):
        ...     print("Ready to start")
    """
    try:
        # Check only critical settings
        if not settings.database_url:
            logger.error("Database URL not configured")
            return False

        if not settings.redis_url:
            logger.error("Redis URL not configured")
            return False

        if not settings.celery_broker_url:
            logger.error("Celery broker URL not configured")
            return False

        # Check URL formats
        if not settings.database_url.startswith("postgresql://"):
            logger.error("Invalid database URL format")
            return False

        if not settings.redis_url.startswith("redis://"):
            logger.error("Invalid Redis URL format")
            return False

        return True

    except Exception as e:
        logger.error(f"Startup validation error: {e}")
        return False
