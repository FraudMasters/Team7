"""
Grammar and spelling checking from resume text using LanguageTool.

This module provides functions to detect grammar, spelling, and punctuation
errors in resume text using LanguageTool with automatic language detection.
"""
import logging
from typing import Dict, List, Optional, Union, Tuple

logger = logging.getLogger(__name__)

# Global tool instances to avoid reloading on each call
_language_tools: Dict[str, Optional["LanguageTool"]] = {
    "en-US": None,
    "en-GB": None,
    "ru-RU": None,
}


def _detect_language(text: str) -> str:
    """
    Detect the language of the input text.

    Args:
        text: Input text to detect language from

    Returns:
        Detected language code ('en' or 'ru')
    """
    try:
        from langdetect import detect, LangDetectException

        try:
            lang = detect(text)
            logger.info(f"Detected language: {lang}")
            return lang
        except LangDetectException:
            logger.warning("Language detection failed, defaulting to English")
            return "en"
    except ImportError:
        logger.warning("langdetect not installed, defaulting to English")
        return "en"


def _get_tool(language: str = "en") -> "LanguageTool":
    """
    Get or initialize the LanguageTool for the specified language.

    Args:
        language: Language code ('en' for English, 'ru' for Russian)

    Returns:
        Initialized LanguageTool instance

    Raises:
        ImportError: If language-tool-python is not installed
        RuntimeError: If tool fails to initialize
    """
    global _language_tools

    # Map language codes to LanguageTool language codes
    lang_map = {
        "english": "en-US",
        "en": "en-US",
        "russian": "ru-RU",
        "ru": "ru-RU",
    }

    lang_code = lang_map.get(language.lower(), "en-US")

    if _language_tools.get(lang_code) is None:
        try:
            from language_tool_python import LanguageTool

            logger.info(f"Initializing LanguageTool for language: {lang_code}")

            _language_tools[lang_code] = LanguageTool(lang_code)

            logger.info(f"LanguageTool {lang_code} initialized successfully")

        except ImportError as e:
            raise ImportError(
                "language-tool-python is not installed. "
                "Install it with: pip install language-tool-python"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LanguageTool: {e}") from e

    return _language_tools[lang_code]


def check_grammar(
    text: str,
    *,
    language: Optional[str] = None,
    auto_detect_language: bool = True,
    max_errors: int = 100,
    include_punctuation: bool = True,
    include_style: bool = False,
) -> Dict[str, Optional[Union[List[Dict[str, Union[str, int, List[str], Tuple[int, int]]]], str, int]]]:
    """
    Check grammar and spelling in resume text using LanguageTool.

    This function detects grammar, spelling, and punctuation errors in text.
    It supports automatic language detection for English and Russian resumes.

    Args:
        text: Input text to check for errors
        language: Document language ('en', 'english', 'ru', 'russian')
            - If None and auto_detect_language=True, language is auto-detected
            - If None and auto_detect_language=False, defaults to 'en'
        auto_detect_language: Whether to automatically detect language (default: True)
        max_errors: Maximum number of errors to return (default: 100)
        include_punctuation: Whether to check punctuation errors (default: True)
        include_style: Whether to check style issues (default: False)

    Returns:
        Dictionary containing:
            - errors: List of error objects with:
                - message: Error description
                - category: Error category (grammar, spelling, punctuation, style)
                - severity: Error severity (error, warning)
                - context: Text context around the error
                - suggestions: List of suggested corrections
                - position: Dict with 'start' and 'end' character positions
                - rule_id: LanguageTool rule identifier
            - count: Total number of errors found
            - language_detected: Detected language code
            - language_used: LanguageTool code used for checking
            - error_summary: Dict with error counts by category
            - error: Error message if checking failed

    Raises:
        ValueError: If text is empty
        RuntimeError: If tool initialization or checking fails

    Examples:
        >>> text = "I has work at Google for 3 years."
        >>> result = check_grammar(text)
        >>> print(result["errors"][0]["message"])
        "Use 'have' instead of 'has'"
        >>> print(result["errors"][0]["suggestions"])
        ['have']

        Check Russian text:
        >>> text = "Я работает в компании"
        >>> result = check_grammar(text)
        >>> print(result["errors"][0]["suggestions"])
        ['работаю']

        Disable automatic language detection:
        >>> result = check_grammar(text, language='en', auto_detect_language=False)
    """
    # Validate input
    if not text or not isinstance(text, str):
        return {
            "errors": None,
            "count": 0,
            "language_detected": None,
            "language_used": None,
            "error_summary": None,
            "error": "Text must be a non-empty string",
        }

    text = text.strip()
    if len(text) < 5:
        return {
            "errors": None,
            "count": 0,
            "language_detected": None,
            "language_used": None,
            "error_summary": None,
            "error": "Text too short for grammar checking (min 5 chars)",
        }

    # Determine language to use
    detected_lang = None
    if language is None and auto_detect_language:
        detected_lang = _detect_language(text)
        language = detected_lang
    elif language is None:
        language = "en"

    try:
        # Get or initialize LanguageTool
        tool = _get_tool(language)

        # Check for errors
        logger.info(
            f"Checking grammar in text (length={len(text)}, language={language}, "
            f"auto_detect={auto_detect_language})"
        )

        matches = tool.check(text)

        # Limit errors if needed
        if len(matches) > max_errors:
            matches = matches[:max_errors]
            logger.warning(f"Limited errors to {max_errors} (found {len(matches)})")

        # Convert matches to error objects
        errors = []
        error_categories = {
            "grammar": 0,
            "spelling": 0,
            "punctuation": 0,
            "style": 0,
            "other": 0,
        }

        for match in matches:
            # Determine error category
            category = _categorize_error(match)

            # Skip certain categories if disabled
            if category == "punctuation" and not include_punctuation:
                continue
            if category == "style" and not include_style:
                continue

            # Build error object
            error_obj = {
                "message": match.message,
                "category": category,
                "severity": _get_severity(match),
                "context": match.context,
                "suggestions": match.replacements if hasattr(match, 'replacements') else [],
                "position": {
                    "start": match.offset,
                    "end": match.offset + match.errorLength,
                },
                "rule_id": match.ruleId if hasattr(match, 'ruleId') else "unknown",
            }

            errors.append(error_obj)
            error_categories[category] += 1

        # Get the language code actually used
        lang_map = {
            "en": "en-US",
            "ru": "ru-RU",
        }
        lang_used = lang_map.get(language.lower() if language else "en", "en-US")

        logger.info(f"Found {len(errors)} errors in text")

        return {
            "errors": errors if errors else None,
            "count": len(errors),
            "language_detected": detected_lang,
            "language_used": lang_used,
            "error_summary": error_categories if errors else None,
            "error": None,
        }

    except ImportError as e:
        logger.error(f"Import error during grammar check: {e}")
        return {
            "errors": None,
            "count": 0,
            "language_detected": detected_lang,
            "language_used": None,
            "error_summary": None,
            "error": f"Import error: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Failed to check grammar: {e}")
        return {
            "errors": None,
            "count": 0,
            "language_detected": detected_lang,
            "language_used": None,
            "error_summary": None,
            "error": f"Grammar check failed: {str(e)}",
        }


def _categorize_error(match) -> str:
    """
    Categorize a LanguageTool error match.

    Args:
        match: LanguageTool match object

    Returns:
        Category string: 'grammar', 'spelling', 'punctuation', 'style', or 'other'
    """
    rule_id = getattr(match, 'ruleId', '').lower()
    message = getattr(match, 'message', '').lower()

    # Spelling errors
    if 'spelling' in rule_id or 'spell' in rule_id:
        return "spelling"

    # Punctuation errors
    if 'punctuation' in rule_id or any(p in rule_id for p in ['comma', 'period', 'question', 'exclamation']):
        return "punctuation"
    if any(p in message for p in ['punctuation', 'comma', 'period', 'question mark', 'exclamation']):
        return "punctuation"

    # Style issues
    if 'style' in rule_id or 'typography' in rule_id:
        return "style"

    # Grammar errors (default)
    if 'grammar' in rule_id or 'morphology' in rule_id or 'syntax' in rule_id:
        return "grammar"

    # Try to guess from message
    if 'grammar' in message:
        return "grammar"
    if 'spell' in message:
        return "spelling"
    if 'style' in message:
        return "style"

    return "other"


def _get_severity(match) -> str:
    """
    Determine the severity of a LanguageTool error match.

    Args:
        match: LanguageTool match object

    Returns:
        Severity string: 'error' or 'warning'
    """
    # Spelling and grammar errors are critical
    rule_id = getattr(match, 'ruleId', '').lower()

    if 'spelling' in rule_id or 'spell' in rule_id:
        return "error"
    if 'grammar' in rule_id:
        return "error"

    # Punctuation and style are warnings
    return "warning"


def check_grammar_resume(
    resume_text: str,
    language: Optional[str] = None,
) -> Dict[str, Optional[Union[List[Dict[str, Union[str, int, List[str], Tuple[int, int]]]], Dict[str, int], str]]]:
    """
    Check grammar in resume text with optimized settings.

    This is a convenience function optimized for resume checking.
    It includes punctuation checking but excludes style suggestions
    to focus on critical errors.

    Args:
        resume_text: Full resume text
        language: Document language ('en' or 'ru'), auto-detected if None

    Returns:
        Dictionary containing:
            - errors: List of error objects
            - count: Total number of errors
            - critical_errors: Count of critical errors (grammar, spelling)
            - warning_errors: Count of warning errors (punctuation)
            - language_detected: Detected language code
            - error_summary: Dict with error counts by category
            - error: Error message if checking failed

    Examples:
        >>> result = check_grammar_resume(resume_text)
        >>> print(f"Found {result['critical_errors']} critical errors")
        >>> if result["errors"]:
        ...     for error in result["errors"][:3]:
        ...         print(f"- {error['message']}: {error['suggestions']}")
    """
    result = check_grammar(
        resume_text,
        language=language,
        auto_detect_language=True,
        max_errors=100,
        include_punctuation=True,
        include_style=False,
    )

    if result.get("error"):
        return {
            "errors": None,
            "count": 0,
            "critical_errors": 0,
            "warning_errors": 0,
            "language_detected": result.get("language_detected"),
            "error_summary": None,
            "error": result["error"],
        }

    # Count critical vs warning errors
    critical_count = 0
    warning_count = 0

    for error in result.get("errors", []):
        if error.get("severity") == "error":
            critical_count += 1
        else:
            warning_count += 1

    return {
        "errors": result.get("errors"),
        "count": result.get("count", 0),
        "critical_errors": critical_count,
        "warning_errors": warning_count,
        "language_detected": result.get("language_detected"),
        "error_summary": result.get("error_summary"),
        "error": None,
    }


def get_error_suggestions_summary(
    text: str,
    language: Optional[str] = None
) -> Dict[str, Optional[Union[Dict[str, List[str]], str]]]:
    """
    Get a summary of error suggestions organized by category.

    This function groups all suggestions by error category for easy review.

    Args:
        text: Input text to check
        language: Document language ('en' or 'ru'), auto-detected if None

    Returns:
        Dictionary containing:
            - grammar_suggestions: List of grammar corrections
            - spelling_suggestions: List of spelling corrections
            - punctuation_suggestions: List of punctuation corrections
            - all_suggestions: Combined list of all suggestions
            - error: Error message if checking failed

    Examples:
        >>> result = get_error_suggestions_summary(resume_text)
        >>> print(result["spelling_suggestions"])
        ['recieve -> receive', 'occured -> occurred']
    """
    result = check_grammar(text, language=language)

    if result.get("error"):
        return {
            "grammar_suggestions": None,
            "spelling_suggestions": None,
            "punctuation_suggestions": None,
            "all_suggestions": None,
            "error": result["error"],
        }

    # Group suggestions by category
    grammar_suggs = []
    spelling_suggs = []
    punctuation_suggs = []

    for error in result.get("errors", []):
        category = error.get("category", "other")
        message = error.get("message", "")
        suggestions = error.get("suggestions", [])

        if suggestions:
            # Format suggestion
            suggestion_text = f"{message}"

            # Add suggested replacements
            if len(suggestions) <= 3:
                suggestion_text += f" Suggestions: {', '.join(suggestions[:3])}"
            else:
                suggestion_text += f" Suggestions: {', '.join(suggestions[:3])}, ..."

            if category == "grammar":
                grammar_suggs.append(suggestion_text)
            elif category == "spelling":
                spelling_suggs.append(suggestion_text)
            elif category == "punctuation":
                punctuation_suggs.append(suggestion_text)

    all_suggs = grammar_suggs + spelling_suggs + punctuation_suggs

    return {
        "grammar_suggestions": grammar_suggs if grammar_suggs else None,
        "spelling_suggestions": spelling_suggs if spelling_suggs else None,
        "punctuation_suggestions": punctuation_suggs if punctuation_suggs else None,
        "all_suggestions": all_suggs if all_suggs else None,
        "error": None,
    }
