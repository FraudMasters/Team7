"""
Backend translation module for error messages and user-facing strings.

This module provides translation functions for error messages, validation messages,
and success messages in English and Russian languages. It follows the same patterns
as other backend modules with comprehensive docstrings, type hints, and error handling.
"""
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


# Language constants
SUPPORTED_LANGUAGES = ["en", "ru"]
DEFAULT_LANGUAGE = "en"


# Translation dictionaries for error messages
ERROR_MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        # File upload errors
        "file_too_large": "File size ({size:.2f}MB) exceeds maximum allowed size ({max_mb}MB)",
        "invalid_file_type": "Unsupported file type '{file_ext}'. Allowed types: {allowed}",
        "file_upload_failed": "Failed to upload file. Please try again",
        "file_not_found": "The requested file was not found",
        "file_corrupted": "The file appears to be corrupted and cannot be processed",
        "file_read_error": "Error reading file content",

        # Database errors
        "database_error": "Database error occurred",
        "database_connection_error": "Failed to connect to the database",
        "database_query_error": "Error executing database query",
        "record_not_found": "The requested record was not found",
        "record_already_exists": "A record with these details already exists",
        "database_constraint_error": "Database constraint violation",

        # Validation errors
        "invalid_input": "Invalid input provided",
        "missing_required_field": "Required field '{field}' is missing",
        "invalid_format": "Invalid format for field '{field}'",
        "value_out_of_range": "Value for '{field}' is out of valid range",
        "invalid_uuid": "Invalid UUID format",
        "invalid_enum_value": "Invalid value '{value}' for field '{field}'",

        # Analysis errors
        "analysis_failed": "Resume analysis failed",
        "parsing_failed": "Failed to parse resume content",
        "extraction_failed": "Failed to extract information from resume",
        "grammar_check_failed": "Grammar checking failed",
        "keyword_extraction_failed": "Keyword extraction failed",
        "entity_extraction_failed": "Named entity recognition failed",
        "experience_calculation_failed": "Experience calculation failed",

        # Processing errors
        "processing_timeout": "Processing timed out. Please try again",
        "service_unavailable": "Service temporarily unavailable. Please try again later",
        "rate_limit_exceeded": "Rate limit exceeded. Please try again later",
        "concurrent_request_limit": "Too many concurrent requests. Please wait",

        # Authentication/Authorization errors (for future use)
        "unauthorized": "Authentication required",
        "forbidden": "You do not have permission to perform this action",
        "token_expired": "Authentication token has expired",
        "invalid_credentials": "Invalid credentials provided",

        # Generic errors
        "internal_server_error": "An internal server error occurred",
        "bad_request": "Invalid request",
        "not_found": "Resource not found",
        "method_not_allowed": "Method not allowed",
        "not_implemented": "Feature not implemented",
    },
    "ru": {
        # File upload errors
        "file_too_large": "Размер файла ({size:.2f}МБ) превышает максимально допустимый размер ({max_mb}МБ)",
        "invalid_file_type": "Неподдерживаемый тип файла '{file_ext}'. Допустимые типы: {allowed}",
        "file_upload_failed": "Не удалось загрузить файл. Попробуйте снова",
        "file_not_found": "Запрошенный файл не найден",
        "file_corrupted": "Файл поврежден и не может быть обработан",
        "file_read_error": "Ошибка чтения содержимого файла",

        # Database errors
        "database_error": "Произошла ошибка базы данных",
        "database_connection_error": "Не удалось подключиться к базе данных",
        "database_query_error": "Ошибка выполнения запроса к базе данных",
        "record_not_found": "Запрошенная запись не найдена",
        "record_already_exists": "Запись с такими данными уже существует",
        "database_constraint_error": "Нарушение ограничения базы данных",

        # Validation errors
        "invalid_input": "Неверные входные данные",
        "missing_required_field": "Обязательное поле '{field}' отсутствует",
        "invalid_format": "Неверный формат поля '{field}'",
        "value_out_of_range": "Значение поля '{field}' вне допустимого диапазона",
        "invalid_uuid": "Неверный формат UUID",
        "invalid_enum_value": "Неверное значение '{value}' для поля '{field}'",

        # Analysis errors
        "analysis_failed": "Не удалось проанализировать резюме",
        "parsing_failed": "Не удалось проанализировать содержимое резюме",
        "extraction_failed": "Не удалось извлечь информацию из резюме",
        "grammar_check_failed": "Не удалось проверить грамматику",
        "keyword_extraction_failed": "Не удалось извлечь ключевые слова",
        "entity_extraction_failed": "Не удалось распознать именованные сущности",
        "experience_calculation_failed": "Не удалось рассчитать опыт работы",

        # Processing errors
        "processing_timeout": "Превышено время обработки. Попробуйте снова",
        "service_unavailable": "Сервис временно недоступен. Попробуйте позже",
        "rate_limit_exceeded": "Превышен лимит запросов. Попробуйте позже",
        "concurrent_request_limit": "Слишком много одновременных запросов. Подождите",

        # Authentication/Authorization errors (for future use)
        "unauthorized": "Требуется аутентификация",
        "forbidden": "У вас нет прав для выполнения этого действия",
        "token_expired": "Срок действия токена аутентификации истек",
        "invalid_credentials": "Неверные учетные данные",

        # Generic errors
        "internal_server_error": "Произошла внутренняя ошибка сервера",
        "bad_request": "Неверный запрос",
        "not_found": "Ресурс не найден",
        "method_not_allowed": "Метод не поддерживается",
        "not_implemented": "Функция не реализована",
    },
}


# Translation dictionaries for success messages
SUCCESS_MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        "file_uploaded": "Resume uploaded successfully",
        "analysis_completed": "Resume analysis completed successfully",
        "preferences_updated": "Preferences updated successfully",
        "record_created": "Record created successfully",
        "record_updated": "Record updated successfully",
        "record_deleted": "Record deleted successfully",
    },
    "ru": {
        "file_uploaded": "Резюме успешно загружено",
        "analysis_completed": "Анализ резюме успешно завершен",
        "preferences_updated": "Настройки успешно обновлены",
        "record_created": "Запись успешно создана",
        "record_updated": "Запись успешно обновлена",
        "record_deleted": "Запись успешно удалена",
    },
}


# Translation dictionaries for validation messages
VALIDATION_MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        "resume_id_required": "Resume ID is required",
        "file_required": "File is required",
        "invalid_resume_id": "Invalid resume ID format",
        "language_not_supported": "Language '{lang}' is not supported. Supported languages: {supported}",
        "invalid_date_format": "Invalid date format. Expected format: {expected_format}",
        "invalid_email_format": "Invalid email format",
        "invalid_url_format": "Invalid URL format",
    },
    "ru": {
        "resume_id_required": "Требуется ID резюме",
        "file_required": "Требуется файл",
        "invalid_resume_id": "Неверный формат ID резюме",
        "language_not_supported": "Язык '{lang}' не поддерживается. Поддерживаемые языки: {supported}",
        "invalid_date_format": "Неверный формат даты. Ожидаемый формат: {expected_format}",
        "invalid_email_format": "Неверный формат email",
        "invalid_url_format": "Неверный формат URL",
    },
}


def _validate_locale(locale: str) -> str:
    """
    Validate and normalize locale string.

    Args:
        locale: Language code (e.g., 'en', 'en-US', 'ru-RU')

    Returns:
        Normalized language code (e.g., 'en', 'ru')

    Examples:
        >>> _validate_locale("en-US")
        'en'
        >>> _validate_locale("ru")
        'ru'
        >>> _validate_locale("de")
        'en'  # Falls back to default for unsupported languages
    """
    if not locale:
        return DEFAULT_LANGUAGE

    # Extract language code from locale (e.g., 'en-US' -> 'en')
    lang_code = locale.split("-")[0].lower()

    # Return validated language or default
    if lang_code in SUPPORTED_LANGUAGES:
        return lang_code
    else:
        logger.warning(f"Unsupported language '{locale}', falling back to '{DEFAULT_LANGUAGE}'")
        return DEFAULT_LANGUAGE


def _format_message(template: str, **kwargs: Any) -> str:
    """
    Format message template with provided parameters.

    Args:
        template: Message template with placeholders
        **kwargs: Values to substitute into template

    Returns:
        Formatted message string

    Examples:
        >>> _format_message("File size {size} exceeds {max}", size=10, max=5)
        'File size 10 exceeds 5'
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing formatting key {e} in template: {template}")
        return template
    except Exception as e:
        logger.error(f"Error formatting message: {e}")
        return template


def get_error_message(error_key: str, locale: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """
    Get translated error message for the given error key.

    Args:
        error_key: Key identifying the error message
        locale: Language code (default: 'en')
        **kwargs: Parameters to substitute into error message

    Returns:
        Translated error message with parameters substituted

    Raises:
        KeyError: If error_key is not found in translation dictionary

    Examples:
        >>> get_error_message("file_too_large", "en", size=10.5, max_mb=5)
        'File size 10.50MB exceeds maximum allowed size (5MB)'
        >>> get_error_message("file_too_large", "ru", size=10.5, max_mb=5)
        'Размер файла 10.50МБ превышает максимально допустимый размер (5МБ)'
    """
    lang = _validate_locale(locale)

    if error_key not in ERROR_MESSAGES[lang]:
        logger.warning(f"Error key '{error_key}' not found for language '{lang}', checking default")
        if error_key not in ERROR_MESSAGES[DEFAULT_LANGUAGE]:
            logger.error(f"Error key '{error_key}' not found in any language")
            return error_key  # Return key as fallback
        lang = DEFAULT_LANGUAGE

    template = ERROR_MESSAGES[lang][error_key]
    return _format_message(template, **kwargs)


def get_success_message(success_key: str, locale: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """
    Get translated success message for the given key.

    Args:
        success_key: Key identifying the success message
        locale: Language code (default: 'en')
        **kwargs: Parameters to substitute into success message

    Returns:
        Translated success message with parameters substituted

    Examples:
        >>> get_success_message("file_uploaded", "en")
        'Resume uploaded successfully'
        >>> get_success_message("file_uploaded", "ru")
        'Резюме успешно загружено'
    """
    lang = _validate_locale(locale)

    if success_key not in SUCCESS_MESSAGES[lang]:
        logger.warning(f"Success key '{success_key}' not found for language '{lang}', checking default")
        if success_key not in SUCCESS_MESSAGES[DEFAULT_LANGUAGE]:
            logger.error(f"Success key '{success_key}' not found in any language")
            return success_key  # Return key as fallback
        lang = DEFAULT_LANGUAGE

    template = SUCCESS_MESSAGES[lang][success_key]
    return _format_message(template, **kwargs)


def get_validation_message(validation_key: str, locale: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """
    Get translated validation message for the given key.

    Args:
        validation_key: Key identifying the validation message
        locale: Language code (default: 'en')
        **kwargs: Parameters to substitute into validation message

    Returns:
        Translated validation message with parameters substituted

    Examples:
        >>> get_validation_message("invalid_resume_id", "en")
        'Invalid resume ID format'
        >>> get_validation_message("invalid_resume_id", "ru")
        'Неверный формат ID резюме'
    """
    lang = _validate_locale(locale)

    if validation_key not in VALIDATION_MESSAGES[lang]:
        logger.warning(
            f"Validation key '{validation_key}' not found for language '{lang}', checking default"
        )
        if validation_key not in VALIDATION_MESSAGES[DEFAULT_LANGUAGE]:
            logger.error(f"Validation key '{validation_key}' not found in any language")
            return validation_key  # Return key as fallback
        lang = DEFAULT_LANGUAGE

    template = VALIDATION_MESSAGES[lang][validation_key]
    return _format_message(template, **kwargs)


def get_message(message_key: str, locale: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """
    Get translated message by searching all message dictionaries.

    This function searches error, success, and validation message dictionaries
    in that order, returning the first match found.

    Args:
        message_key: Key identifying the message
        locale: Language code (default: 'en')
        **kwargs: Parameters to substitute into message

    Returns:
        Translated message with parameters substituted

    Examples:
        >>> get_message("file_too_large", "en", size=10.5, max_mb=5)
        'File size 10.50MB exceeds maximum allowed size (5MB)'
    """
    # Try error messages first
    if message_key in ERROR_MESSAGES.get(_validate_locale(locale), {}):
        return get_error_message(message_key, locale, **kwargs)

    # Try success messages
    if message_key in SUCCESS_MESSAGES.get(_validate_locale(locale), {}):
        return get_success_message(message_key, locale, **kwargs)

    # Try validation messages
    if message_key in VALIDATION_MESSAGES.get(_validate_locale(locale), {}):
        return get_validation_message(message_key, locale, **kwargs)

    # Not found
    logger.error(f"Message key '{message_key}' not found in any translation dictionary")
    return message_key
