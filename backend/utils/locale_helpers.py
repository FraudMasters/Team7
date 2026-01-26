"""
Locale helpers for date and number formatting.

This module provides functions to format dates and numbers according to different
locale conventions, supporting English (en) and Russian (ru) languages.
"""
import logging
from datetime import datetime
from typing import Optional, Union

logger = logging.getLogger(__name__)

# Locale configurations
LOCALE_DATE_FORMATS = {
    "en": "%B %d, %Y",  # January 15, 2024
    "ru": "%d %B %Y",  # 15 января 2024
}

LOCALE_MONTH_NAMES = {
    "en": [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ],
    "ru": [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
}


def _validate_locale(locale: str) -> str:
    """
    Validate and normalize locale string.

    Args:
        locale: Locale code (e.g., 'en', 'ru', 'en-US')

    Returns:
        Normalized locale code (e.g., 'en', 'ru')

    Raises:
        ValueError: If locale is not supported

    Examples:
        >>> _validate_locale("en")
        'en'
        >>> _validate_locale("en-US")
        'en'
        >>> _validate_locale("ru_RU")
        'ru'
    """
    if not isinstance(locale, str):
        raise ValueError(f"Locale must be a string, got {type(locale)}")

    # Extract base locale (e.g., 'en-US' -> 'en')
    base_locale = locale.split("-")[0].split("_")[0].lower()

    if base_locale not in ["en", "ru"]:
        raise ValueError(
            f"Unsupported locale: {locale}. "
            f"Supported locales are: en, ru"
        )

    return base_locale


def format_date(
    date_input: Union[str, datetime],
    locale: str = "en",
    *,
    input_format: Optional[str] = None,
) -> str:
    """
    Format a date according to locale conventions.

    Supports English and Russian date formats with proper month names
    and date ordering for each locale.

    Args:
        date_input: Date as string (e.g., '2024-01-15') or datetime object
        locale: Locale code ('en' or 'ru')
        input_format: Optional format string for parsing date_input if it's a string.
            If None, will try common formats automatically.

    Returns:
        Formatted date string according to locale conventions

    Raises:
        ValueError: If date cannot be parsed or locale is unsupported

    Examples:
        >>> format_date("2024-01-15", "en")
        'January 15, 2024'
        >>> format_date("2024-01-15", "ru")
        '15 января 2024'
        >>> format_date(datetime(2024, 1, 15), "en")
        'January 15, 2024'
    """
    try:
        # Validate and normalize locale
        normalized_locale = _validate_locale(locale)

        # Parse date if string
        if isinstance(date_input, str):
            parsed_date = _parse_date_string(date_input, input_format)
        elif isinstance(date_input, datetime):
            parsed_date = date_input
        else:
            raise ValueError(
                f"date_input must be string or datetime, got {type(date_input)}"
            )

        # Get month names for locale
        month_names = LOCALE_MONTH_NAMES[normalized_locale]
        month_name = month_names[parsed_date.month - 1]

        # Format according to locale conventions
        if normalized_locale == "en":
            # English: January 15, 2024
            return f"{month_name} {parsed_date.day}, {parsed_date.year}"
        else:  # Russian: 15 января 2024
            return f"{parsed_date.day} {month_name} {parsed_date.year}"

    except Exception as e:
        logger.error(f"Error formatting date '{date_input}' for locale '{locale}': {e}")
        raise ValueError(f"Failed to format date: {e}") from e


def _parse_date_string(
    date_str: str,
    input_format: Optional[str] = None,
) -> datetime:
    """
    Parse date string in various formats.

    Args:
        date_str: Date string to parse
        input_format: Specific format to use, or None to auto-detect

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If date string cannot be parsed

    Examples:
        >>> _parse_date_string("2024-01-15", None)
        datetime.datetime(2024, 1, 15, 0, 0)
        >>> _parse_date_string("15.01.2024", "%d.%m.%Y")
        datetime.datetime(2024, 1, 15, 0, 0)
    """
    if not isinstance(date_str, str):
        raise ValueError(f"date_str must be a string, got {type(date_str)}")

    date_str = date_str.strip()

    # Use specific format if provided
    if input_format:
        try:
            return datetime.strptime(date_str, input_format)
        except ValueError as e:
            raise ValueError(
                f"Could not parse date '{date_str}' with format '{input_format}': {e}"
            ) from e

    # Try common formats automatically
    formats = [
        "%Y-%m-%d",  # 2024-01-15
        "%Y-%m-%dT%H:%M:%S",  # 2024-01-15T10:30:00
        "%Y-%m-%dT%H:%M:%SZ",  # 2024-01-15T10:30:00Z
        "%d.%m.%Y",  # 15.01.2024
        "%d/%m/%Y",  # 15/01/2024
        "%m/%d/%Y",  # 01/15/2024
        "%Y/%m/%d",  # 2024/01/15
        "%B %d, %Y",  # January 15, 2024
        "%b %d, %Y",  # Jan 15, 2024
        "%d %B %Y",  # 15 January 2024
        "%d %b %Y",  # 15 Jan 2024
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: {date_str}")


def format_number(
    number: Union[int, float],
    locale: str = "en",
    *,
    decimals: Optional[int] = None,
) -> str:
    """
    Format a number according to locale conventions.

    Uses proper decimal separators and thousand separators for each locale.
    English uses period for decimal and comma for thousands.
    Russian uses comma for decimal and space (non-breaking) for thousands.

    Args:
        number: Number to format (int or float)
        locale: Locale code ('en' or 'ru')
        decimals: Number of decimal places to show. If None, uses original
            precision for floats, 0 for ints.

    Returns:
        Formatted number string according to locale conventions

    Raises:
        ValueError: If locale is unsupported

    Examples:
        >>> format_number(1234.56, "en")
        '1,234.56'
        >>> format_number(1234.56, "ru")
        '1 234,56'
        >>> format_number(1000000, "en")
        '1,000,000'
        >>> format_number(1234.567, "en", decimals=2)
        '1,234.57'
    """
    try:
        # Validate and normalize locale
        normalized_locale = _validate_locale(locale)

        # Validate number
        if not isinstance(number, (int, float)):
            raise ValueError(f"number must be int or float, got {type(number)}")

        # Handle decimals parameter
        if decimals is not None:
            if not isinstance(decimals, int) or decimals < 0:
                raise ValueError("decimals must be a non-negative integer")
            number = round(number, decimals)
        elif isinstance(number, int):
            decimals = 0

        # Convert to string and split into integer and decimal parts
        if decimals is not None:
            number_str = f"{number:.{decimals}f}"
        else:
            number_str = str(number)

        if "." in number_str:
            int_part, dec_part = number_str.split(".")
        else:
            int_part, dec_part = number_str, None

        # Format integer part with thousand separators
        formatted_int = _format_integer_part(int_part, normalized_locale)

        # Combine with decimal part
        if dec_part:
            decimal_separator = "," if normalized_locale == "ru" else "."
            return f"{formatted_int}{decimal_separator}{dec_part}"
        else:
            return formatted_int

    except Exception as e:
        logger.error(f"Error formatting number '{number}' for locale '{locale}': {e}")
        raise ValueError(f"Failed to format number: {e}") from e


def _format_integer_part(int_part: str, locale: str) -> str:
    """
    Format integer part with thousand separators.

    Args:
        int_part: Integer part as string (no decimals)
        locale: Normalized locale code ('en' or 'ru')

    Returns:
        Formatted integer string with thousand separators

    Examples:
        >>> _format_integer_part("1000000", "en")
        '1,000,000'
        >>> _format_integer_part("1000000", "ru")
        '1 000 000'
    """
    # Remove leading zeros but keep at least one digit
    int_part = int_part.lstrip("0") or "0"

    # Add thousand separators from right to left
    if locale == "en":
        separator = ","
    else:  # Russian uses non-breaking space (we'll use regular space)
        separator = " "

    # Split into groups of 3 digits from right
    groups = []
    for i in range(len(int_part), 0, -3):
        start = max(0, i - 3)
        groups.insert(0, int_part[start:i])

    return separator.join(groups)


def format_currency(
    amount: Union[int, float],
    locale: str = "en",
    *,
    currency: str = "USD",
    decimals: int = 2,
) -> str:
    """
    Format a currency amount according to locale conventions.

    Args:
        amount: Currency amount to format
        locale: Locale code ('en' or 'ru')
        currency: Currency code (USD, EUR, RUB, etc.)
        decimals: Number of decimal places (default 2)

    Returns:
        Formatted currency string with symbol

    Raises:
        ValueError: If locale is unsupported

    Examples:
        >>> format_currency(1234.56, "en", currency="USD")
        '1,234.56 USD'
        >>> format_currency(1234.56, "ru", currency="RUB")
        '1 234,56 RUB'
    """
    # Format the number part
    formatted_number = format_number(amount, locale, decimals=decimals)

    # Add currency code
    return f"{formatted_number} {currency}"


def get_supported_locales() -> list[str]:
    """
    Get list of supported locale codes.

    Returns:
        List of supported locale codes

    Examples:
        >>> get_supported_locales()
        ['en', 'ru']
    """
    return ["en", "ru"]
