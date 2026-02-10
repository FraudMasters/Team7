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
        "interview_prep_generation_failed": "Failed to generate interview preparation questions",
        "vacancy_not_found": "Job vacancy not found",
        "invalid_vacancy_id": "Invalid vacancy ID format",

        # Optimization errors
        "optimization_failed": "Resume optimization analysis failed",
        "keyword_analysis_failed": "Keyword analysis failed",
        "formatting_analysis_failed": "Formatting analysis failed",
        "content_analysis_failed": "Content analysis failed",
        "optimization_generation_failed": "Failed to generate optimization suggestions",

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

        # GDPR / Data Deletion errors
        "resume_not_found": "Resume with ID '{id}' not found",
        "deletion_request_not_found": "Deletion request with ID '{id}' not found",
        "cannot_cancel_request": "Cannot cancel request with status '{status}'. Only pending requests can be cancelled",
        "internal_error": "An internal error occurred. Please try again",
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
        "interview_prep_generation_failed": "Не удалось сгенерировать вопросы для интервью",
        "vacancy_not_found": "Вакансия не найдена",
        "invalid_vacancy_id": "Неверный формат ID вакансии",

        # Optimization errors
        "optimization_failed": "Не удалось выполнить анализ оптимизации резюме",
        "keyword_analysis_failed": "Не удалось выполнить анализ ключевых слов",
        "formatting_analysis_failed": "Не удалось выполнить анализ форматирования",
        "content_analysis_failed": "Не удалось выполнить анализ содержимого",
        "optimization_generation_failed": "Не удалось сгенерировать предложения по оптимизации",

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

        # GDPR / Data Deletion errors
        "resume_not_found": "Резюме с ID '{id}' не найдено",
        "deletion_request_not_found": "Запрос на удаление с ID '{id}' не найден",
        "cannot_cancel_request": "Нельзя отменить запрос со статусом '{status}'. Только ожидающие запросы могут быть отменены",
        "internal_error": "Произошла внутренняя ошибка. Попробуйте снова",
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
        "deletion_request_created": "Data deletion request created successfully. We will process your request shortly.",
        # Optimization success messages
        "optimization_completed": "Resume optimization completed successfully",
        "optimization_saved": "Optimization feedback saved successfully",
    },
    "ru": {
        "file_uploaded": "Резюме успешно загружено",
        "analysis_completed": "Анализ резюме успешно завершен",
        "preferences_updated": "Настройки успешно обновлены",
        "record_created": "Запись успешно создана",
        "record_updated": "Запись успешно обновлена",
        "record_deleted": "Запись успешно удалена",
        "deletion_request_created": "Запрос на удаление данных успешно создан. Мы обработаем ваш запрос в ближайшее время.",
        # Optimization success messages
        "optimization_completed": "Оптимизация резюме успешно завершена",
        "optimization_saved": "Результаты оптимизации успешно сохранены",
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
        # Optimization validation messages
        "resume_text_required": "Resume text is required for optimization",
        "invalid_keyword_density": "Keyword density must be between {min} and {max}",
        "invalid_min_action_verbs": "Minimum action verbs must be a positive integer",
    },
    "ru": {
        "resume_id_required": "Требуется ID резюме",
        "file_required": "Требуется файл",
        "invalid_resume_id": "Неверный формат ID резюме",
        "language_not_supported": "Язык '{lang}' не поддерживается. Поддерживаемые языки: {supported}",
        "invalid_date_format": "Неверный формат даты. Ожидаемый формат: {expected_format}",
        "invalid_email_format": "Неверный формат email",
        "invalid_url_format": "Неверный формат URL",
        # Optimization validation messages
        "resume_text_required": "Требуется текст резюме для оптимизации",
        "invalid_keyword_density": "Плотность ключевых слов должна быть между {min} и {max}",
        "invalid_min_action_verbs": "Минимальное количество глаголов должно быть положительным целым числом",
    },
}


# Translation dictionaries for optimization feedback messages
OPTIMIZATION_MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        # Suggestion categories
        "category_keywords": "Keywords",
        "category_structure": "Structure",
        "category_readability": "Readability",
        "category_impact": "Impact",
        "category_action_verbs": "Action Verbs",
        "category_summary": "Summary",
        "category_active_language": "Active Language",
        "category_achievements": "Achievements",

        # Priority levels
        "priority_high": "High",
        "priority_medium": "Medium",
        "priority_low": "Low",

        # Keyword analysis messages
        "keywords_missing_title": "Add missing job-relevant keywords",
        "keywords_missing_desc": "Your resume is missing {count} keyword(s) that appear in the job description. Including these can improve ATS matching.",
        "keywords_low_density_title": "Increase keyword density",
        "keywords_low_density_desc": "Your resume has low keyword density ({density:.1%}). Include more industry-relevant keywords to improve ATS visibility.",
        "keywords_no_section_title": "Add or expand skills section",
        "keywords_no_section_desc": "A clear skills section helps recruiters and ATS systems quickly identify your qualifications.",

        # Formatting messages
        "format_too_many_sections_title": "Reduce number of sections",
        "format_too_many_sections_desc": "Your resume has {count} sections, which may be too many. Too many sections can make your resume harder to read and scan.",
        "format_too_few_sections_title": "Add more resume sections",
        "format_too_few_sections_desc": "Your resume has only {count} section(s). Adding more sections can provide a more complete picture of your qualifications.",
        "format_no_bullets_title": "Use bullet points for better readability",
        "format_no_bullets_desc": "Bullet points make your resume easier to scan and read. Recruiters typically spend only 6-7 seconds on each resume.",
        "format_no_metrics_title": "Add quantifiable achievements",
        "format_no_metrics_desc": "Quantifiable achievements (numbers, percentages, metrics) make your accomplishments more concrete and impressive.",
        "format_long_lines_title": "Consider shortening long lines",
        "format_long_lines_desc": "Average line length is {avg:.0f} characters. Lines longer than 80 characters can be harder to read.",

        # Content messages
        "content_few_action_verbs_title": "Use more action verbs",
        "content_few_action_verbs_desc": "Your resume uses {count} action verb(s). Action verbs make your experience more dynamic and showcase your achievements effectively.",
        "content_no_summary_title": "Add a professional summary",
        "content_no_summary_desc": "A professional summary at the top of your resume provides a quick overview of your qualifications and career goals.",
        "content_passive_language_title": "Replace passive language with active language",
        "content_passive_language_desc": "Found {count} instance(s) of passive language. Active language is more impactful and demonstrates your contributions more effectively.",
        "content_no_results_title": "Add measurable results to experience",
        "content_no_results_desc": "Your experience descriptions lack specific metrics. Quantifiable achievements help recruiters understand the impact of your work.",

        # Labels and UI text
        "current_state": "Current State",
        "recommendation": "Recommendation",
        "examples": "Examples",
        "no_suggestions": "Your resume looks great! No optimization suggestions.",
        "optimization_report": "RESUME OPTIMIZATION REPORT",
        "total_suggestions": "Total",
        "high_priority": "High Priority",
        "medium_priority": "Medium Priority",
        "low_priority": "Low Priority",
    },
    "ru": {
        # Suggestion categories
        "category_keywords": "Ключевые слова",
        "category_structure": "Структура",
        "category_readability": "Читаемость",
        "category_impact": "Результативность",
        "category_action_verbs": "Глаголы действия",
        "category_summary": "Резюме",
        "category_active_language": "Активный язык",
        "category_achievements": "Достижения",

        # Priority levels
        "priority_high": "Высокий",
        "priority_medium": "Средний",
        "priority_low": "Низкий",

        # Keyword analysis messages
        "keywords_missing_title": "Добавьте отсутствующие ключевые слова",
        "keywords_missing_desc": "В вашем резюме отсутствует {count} ключевое(-ых) слово(-а), которое(-ые) встречается(-ются) в описании вакансии. Включение этих слов может улучшить соответствие ATS.",
        "keywords_low_density_title": "Увеличьте плотность ключевых слов",
        "keywords_low_density_desc": "В вашем резюме низкая плотность ключевых слов ({density:.1%}). Включите больше отраслевых ключевых слов для улучшения видимости в ATS.",
        "keywords_no_section_title": "Добавьте или расширьте раздел навыков",
        "keywords_no_section_desc": "Четкий раздел навыков помогает рекрутерам и системам ATS быстро определить вашу квалификацию.",

        # Formatting messages
        "format_too_many_sections_title": "Уменьшите количество разделов",
        "format_too_many_sections_desc": "В вашем резюме {count} разделов, что может быть слишком много. Слишком много разделов может затруднить чтение и сканирование резюме.",
        "format_too_few_sections_title": "Добавьте больше разделов в резюме",
        "format_too_few_sections_desc": "В вашем резюме только {count} раздел(-ов). Добавление большего количества разделов может дать более полную картину вашей квалификации.",
        "format_no_bullets_title": "Используйте маркированные списки для лучшей читаемости",
        "format_no_bullets_desc": "Маркированные списки облегчают сканирование и чтение резюме. Рекрутеры обычно тратят всего 6-7 секунд на каждое резюме.",
        "format_no_metrics_title": "Добавьте измеримые достижения",
        "format_no_metrics_desc": "Измеримые достижения (числа, проценты, метрики) делают ваши достижения более конкретными и впечатляющими.",
        "format_long_lines_title": "Рассмотрите возможность сокращения длинных строк",
        "format_long_lines_desc": "Средняя длина строки составляет {avg:.0f} символов. Строки длиннее 80 символов могут быть труднее для чтения.",

        # Content messages
        "content_few_action_verbs_title": "Используйте больше глаголов действия",
        "content_few_action_verbs_desc": "В вашем резюме используется {count} глагол(-ов) действия. Глаголы действия делают ваш опыт более динамичным и эффективно демонстрируют ваши достижения.",
        "content_no_summary_title": "Добавьте профессиональное резюме",
        "content_no_summary_desc": "Профессиональное резюме в верхней части вашего резюме дает быстрый обзор вашей квалификации и карьерных целей.",
        "content_passive_language_title": "Замените пассивный язык на активный",
        "content_passive_language_desc": "Обнаружено {count} пример(-ов) пассивного языка. Активный язык более эффективен и лучше демонстрирует ваш вклад.",
        "content_no_results_title": "Добавьте измеримые результаты в опыт работы",
        "content_no_results_desc": "В описаниях вашего опыта не хватает конкретных метрик. Измеримые достижения помогают рекрутерам понять влияние вашей работы.",

        # Labels and UI text
        "current_state": "Текущее состояние",
        "recommendation": "Рекомендация",
        "examples": "Примеры",
        "no_suggestions": "Ваше резюме выглядит отлично! Нет предложений по оптимизации.",
        "optimization_report": "ОТЧЕТ ОБ ОПТИМИЗАЦИИ РЕЗЮМЕ",
        "total_suggestions": "Всего",
        "high_priority": "Высокий приоритет",
        "medium_priority": "Средний приоритет",
        "low_priority": "Низкий приоритет",
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

    This function searches error, success, validation, and optimization message dictionaries
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

    # Try optimization messages
    if message_key in OPTIMIZATION_MESSAGES.get(_validate_locale(locale), {}):
        return get_optimization_message(message_key, locale, **kwargs)

    # Not found
    logger.error(f"Message key '{message_key}' not found in any translation dictionary")
    return message_key


def get_optimization_message(
    optimization_key: str,
    locale: str = DEFAULT_LANGUAGE,
    **kwargs: Any
) -> str:
    """
    Get translated optimization feedback message for the given key.

    Args:
        optimization_key: Key identifying the optimization message
        locale: Language code (default: 'en')
        **kwargs: Parameters to substitute into optimization message

    Returns:
        Translated optimization message with parameters substituted

    Examples:
        >>> get_optimization_message("keywords_missing_title", "en")
        'Add missing job-relevant keywords'
        >>> get_optimization_message("keywords_low_density_desc", "en", density=0.02)
        'Your resume has low keyword density (2.0%). Include more industry-relevant keywords...'
    """
    lang = _validate_locale(locale)

    if optimization_key not in OPTIMIZATION_MESSAGES[lang]:
        logger.warning(
            f"Optimization key '{optimization_key}' not found for language '{lang}', checking default"
        )
        if optimization_key not in OPTIMIZATION_MESSAGES[DEFAULT_LANGUAGE]:
            logger.error(f"Optimization key '{optimization_key}' not found in any language")
            return optimization_key  # Return key as fallback
        lang = DEFAULT_LANGUAGE

    template = OPTIMIZATION_MESSAGES[lang][optimization_key]
    return _format_message(template, **kwargs)
