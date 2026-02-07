"""
Application configuration using environment variables.

This module provides backward-compatible imports from the new centralized
configuration system. The actual configuration is now in the config package.

For new code, prefer importing from the config package directly:
    from config import get_settings, get_environment_config

Legacy imports still work:
    from config import Settings, get_settings
"""
import logging
from pathlib import Path
from typing import List, Optional

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Import from new configuration package
from config.base import BaseConfig
from config import get_settings as _get_settings

# Legacy compatibility: Settings alias for BaseConfig
Settings = BaseConfig

# Re-export get_settings for backward compatibility
get_settings = _get_settings


# Legacy convenience: Create Settings() directly returns environment-specific config
def __getattr__(name: str):
    """Provide backward compatibility for direct Settings() instantiation."""
    if name == "Settings":
        # When someone calls Settings(), return the environment-specific config
        return get_settings()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
