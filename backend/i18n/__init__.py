"""
Backend internationalization (i18n) module.

This module provides translation support for backend error messages and
user-facing strings in English and Russian.
"""

from .backend_translations import (
    get_error_message,
    get_success_message,
    get_validation_message,
    get_message,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
)

__all__ = [
    "get_error_message",
    "get_success_message",
    "get_validation_message",
    "get_message",
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
]
