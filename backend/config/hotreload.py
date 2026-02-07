"""
Hot-reload functionality for non-critical configuration settings.

This module provides functions to reload non-critical settings at runtime
without requiring a full application restart. Critical settings (database
connections, server bindings, etc.) are excluded from hot-reload and
require a service restart.

Non-critical settings include:
- Logging configuration (log level)
- File upload limits (max_upload_size_mb, allowed_file_types)
- Analysis timeouts (analysis_timeout_seconds)
- LLM parameters (llm_temperature, llm_max_tokens, llm_model)
- ATS scoring thresholds and weights
- Backup settings (schedule, retention, S3 configuration)
- Audit log retention

Critical settings requiring restart:
- Database URL
- Redis URL
- Celery broker/result backend URLs
- Server host/port bindings
- Environment (development/staging/production)
"""
import logging
from typing import Any, Dict, List, Optional, Set

from config.base import BaseConfig

logger = logging.getLogger(__name__)

# Settings that can be hot-reloaded (non-critical)
RELOADABLE_SETTINGS: Set[str] = {
    # Logging
    "log_level",

    # File upload configuration
    "max_upload_size_mb",
    "allowed_file_types",

    # Analysis configuration
    "analysis_timeout_seconds",

    # LLM configuration
    "llm_model",
    "llm_temperature",
    "llm_max_tokens",

    # ATS simulation configuration
    "ats_threshold",
    "ats_visual_check_enabled",
    "ats_keyword_weight",
    "ats_experience_weight",
    "ats_education_weight",
    "ats_fit_weight",

    # Backup configuration
    "backup_enabled",
    "backup_retention_days",
    "backup_schedule",
    "backup_s3_enabled",
    "backup_s3_bucket",
    "backup_s3_endpoint",
    "backup_s3_region",
    "backup_notification_email",
    "backup_incremental_enabled",
    "backup_compression_enabled",

    # Audit log configuration
    "audit_log_retention_days",

    # LanguageTool server
    "languagetool_server",
}

# Critical settings that require restart (not reloadable)
CRITICAL_SETTINGS: Set[str] = {
    "environment",
    "database_url",
    "redis_url",
    "backend_host",
    "backend_port",
    "frontend_url",
    "celery_broker_url",
    "celery_result_backend",
}


def get_reloadable_settings() -> List[str]:
    """
    Get list of settings that can be hot-reloaded.

    Returns:
        List of reloadable setting names

    Example:
        >>> get_reloadable_settings()
        ['log_level', 'max_upload_size_mb', 'llm_temperature', ...]
    """
    return sorted(RELOADABLE_SETTINGS)


def get_critical_settings() -> List[str]:
    """
    Get list of settings that require a service restart to change.

    Returns:
        List of critical setting names

    Example:
        >>> get_critical_settings()
        ['environment', 'database_url', 'redis_url', ...]
    """
    return sorted(CRITICAL_SETTINGS)


def is_reloadable(setting_name: str) -> bool:
    """
    Check if a setting can be hot-reloaded.

    Args:
        setting_name: Name of the setting to check

    Returns:
        True if the setting can be hot-reloaded, False otherwise

    Example:
        >>> is_reloadable("log_level")
        True
        >>> is_reloadable("database_url")
        False
    """
    return setting_name in RELOADABLE_SETTINGS


def detect_setting_changes(
    old_config: BaseConfig,
    new_config: BaseConfig,
) -> Dict[str, Dict[str, Any]]:
    """
    Detect which reloadable settings have changed between configs.

    Args:
        old_config: Previous configuration
        new_config: New configuration after reload

    Returns:
        Dictionary with setting names as keys and dicts containing
        'before' and 'after' values as values

    Example:
        >>> changes = detect_setting_changes(old_settings, new_settings)
        >>> changes
        {
            'log_level': {'before': 'INFO', 'after': 'DEBUG'},
            'llm_temperature': {'before': 0.1, 'after': 0.2}
        }
    """
    changes: Dict[str, Dict[str, Any]] = {}

    for setting_name in RELOADABLE_SETTINGS:
        if hasattr(old_config, setting_name) and hasattr(new_config, setting_name):
            old_value = getattr(old_config, setting_name)
            new_value = getattr(new_config, setting_name)

            if old_value != new_value:
                changes[setting_name] = {
                    "before": old_value,
                    "after": new_value,
                }

    return changes


def get_reload_summary(old_config: BaseConfig, new_config: BaseConfig) -> Dict[str, Any]:
    """
    Generate a summary of configuration changes after hot-reload.

    Args:
        old_config: Previous configuration before reload
        new_config: New configuration after reload

    Returns:
        Dictionary containing:
        - changed_count: Number of settings that changed
        - changes: Dict of setting changes with before/after values
        - reloadable_count: Total number of reloadable settings
        - critical_unchanged: List of critical settings that remained unchanged

    Example:
        >>> summary = get_reload_summary(old_settings, new_settings)
        >>> summary
        {
            'changed_count': 2,
            'changes': {
                'log_level': {'before': 'INFO', 'after': 'DEBUG'}
            },
            'reloadable_count': 25,
            'critical_unchanged': ['database_url', 'redis_url']
        }
    """
    changes = detect_setting_changes(old_config, new_config)

    # Check that critical settings haven't changed
    critical_unchanged: List[str] = []
    for setting_name in CRITICAL_SETTINGS:
        if hasattr(old_config, setting_name) and hasattr(new_config, setting_name):
            old_value = getattr(old_config, setting_name)
            new_value = getattr(new_config, setting_name)
            if old_value == new_value:
                critical_unchanged.append(setting_name)

    return {
        "changed_count": len(changes),
        "changes": changes,
        "reloadable_count": len(RELOADABLE_SETTINGS),
        "critical_unchanged": critical_unchanged,
    }


def validate_reload_safety(old_config: BaseConfig, new_config: BaseConfig) -> List[str]:
    """
    Validate that a hot-reload is safe (no critical settings changed).

    Args:
        old_config: Previous configuration
        new_config: New configuration after reload

    Returns:
        List of critical settings that changed (empty if safe)

    Example:
        >>> unsafe = validate_reload_safety(old_settings, new_settings)
        >>> if unsafe:
        ...     print(f"Unsafe to reload: {unsafe}")
    """
    unsafe_changes: List[str] = []

    for setting_name in CRITICAL_SETTINGS:
        if hasattr(old_config, setting_name) and hasattr(new_config, setting_name):
            old_value = getattr(old_config, setting_name)
            new_value = getattr(new_config, setting_name)
            if old_value != new_value:
                unsafe_changes.append(setting_name)

    return unsafe_changes


def mask_sensitive_values(
    value: Any,
    setting_name: str = "",
) -> Any:
    """
    Mask sensitive configuration values for logging.

    Args:
        value: The value to potentially mask
        setting_name: Name of the setting (to determine if sensitive)

    Returns:
        The original value or a masked version

    Example:
        >>> mask_sensitive_values("secret_key", "zai_api_key")
        '******'
        >>> mask_sensitive_values("INFO", "log_level")
        'INFO'
    """
    # Sensitive setting patterns
    sensitive_patterns = [
        "api_key",
        "secret",
        "password",
        "token",
        "credentials",
    ]

    value_str = str(value)
    setting_lower = setting_name.lower()

    # Check if this is a sensitive setting
    for pattern in sensitive_patterns:
        if pattern in setting_lower:
            if len(value_str) > 6:
                return f"{value_str[:3]}...{value_str[-2:]}"
            else:
                return "***"

    return value


def format_changes_for_logging(changes: Dict[str, Dict[str, Any]]) -> str:
    """
    Format configuration changes for safe logging.

    Args:
        changes: Dictionary of changes from detect_setting_changes

    Returns:
        Formatted string with sensitive values masked

    Example:
        >>> changes = {'log_level': {'before': 'INFO', 'after': 'DEBUG'}}
        >>> format_changes_for_logging(changes)
        'log_level: INFO -> DEBUG'
    """
    parts: List[str] = []

    for setting_name, change in changes.items():
        before = mask_sensitive_values(change["before"], setting_name)
        after = mask_sensitive_values(change["after"], setting_name)
        parts.append(f"{setting_name}: {before} -> {after}")

    return ", ".join(parts)
