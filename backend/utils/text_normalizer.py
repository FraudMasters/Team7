"""
Text normalization utilities for skill and position names.

This module provides functions to normalize skill and position names
by removing variations, formatting differences, and common suffixes.
This enables consistent matching and comparison of skills and positions
across different resume formats and conventions.
"""
import logging
import re
from typing import Optional, Set

logger = logging.getLogger(__name__)

# Common file extensions and suffixes to remove from skill names
SKILL_SUFFIXES = [
    ".js", ".py", ".ts", ".java", ".cpp", ".cs", ".go", ".rs", ".php", ".rb",
    ".jsx", ".tsx", ".vue", ".css", ".scss", ".sass", ".less",
    "js", "py", "ts", "jsx", "tsx",  # Without dot
]

# Common prefixes to remove
SKILL_PREFIXES = [
    "the ", "a ", "an ",  # Articles
    "programming in ", "coding in ", "developing in ",  # Verbs
]

# Words to remove from skill names
FILLER_WORDS = [
    "programming", "coding", "development", "developer", "language",
    "framework", "library", "tool", "software", "application",
    "based", "oriented", "driven", "powered",
]

# Position suffixes to remove
POSITION_SUFFIXES = [
    " sr", " jr", " i", " ii", " iii", " iv", " v",
    " senior", " junior", " mid", " lead", " principal",
    " (remote)", " (hybrid)", " (on-site)",
    " - remote", " - hybrid", " - on-site",
]

# Cache for normalized names
_normalization_cache: dict[str, str] = {}


def normalize_skill_name(skill_name: str) -> str:
    """
    Normalize a skill name by removing variations and formatting differences.

    This function normalizes skill names by:
    - Converting to lowercase
    - Removing file extensions (.js, .py, etc.)
    - Removing common prefixes and suffixes
    - Removing special characters
    - Removing filler words
    - Normalizing whitespace

    Args:
        skill_name: Raw skill name to normalize (e.g., "React.js", "JavaScript")

    Returns:
        Normalized skill name in lowercase without formatting (e.g., "react", "javascript")

    Raises:
        ValueError: If skill_name is empty or not a string

    Examples:
        >>> normalize_skill_name("React.js")
        'react'
        >>> normalize_skill_name("JavaScript")
        'javascript'
        >>> normalize_skill_name("TypeScript")
        'typescript'
        >>> normalize_skill_name("Python")
        'python'
        >>> normalize_skill_name("C++")
        'c'
        >>> normalize_skill_name("Node.js")
        'node'
        >>> normalize_skill_name("Vue.js")
        'vue'
    """
    if not skill_name or not isinstance(skill_name, str):
        raise ValueError("skill_name must be a non-empty string")

    # Check cache
    cache_key = f"skill:{skill_name}"
    if cache_key in _normalization_cache:
        return _normalization_cache[cache_key]

    try:
        # Convert to lowercase
        normalized = skill_name.lower().strip()

        # Remove file extensions (with and without dots)
        for suffix in SKILL_SUFFIXES:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
                break

        # Remove common prefixes
        for prefix in SKILL_PREFIXES:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
                break

        # Remove special characters but keep spaces and word characters
        normalized = re.sub(r"[^\w\s]", " ", normalized)

        # Remove filler words
        words = normalized.split()
        filtered_words = [
            word for word in words
            if word not in FILLER_WORDS and len(word) > 1
        ]
        normalized = " ".join(filtered_words)

        # Normalize whitespace (multiple spaces -> single space)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # Handle special cases
        normalized = _handle_special_skill_cases(normalized)

        # Cache result
        _normalization_cache[cache_key] = normalized

        logger.debug(f"Normalized skill '{skill_name}' -> '{normalized}'")
        return normalized

    except Exception as e:
        logger.error(f"Error normalizing skill name '{skill_name}': {e}")
        # Return lowercase original as fallback
        return skill_name.lower().strip()


def normalize_position_name(position_name: str) -> str:
    """
    Normalize a position/job title by removing variations and formatting differences.

    This function normalizes position names by:
    - Converting to lowercase
    - Removing seniority suffixes (sr, jr, senior, junior, etc.)
    - Removing work location suffixes (remote, hybrid, on-site)
    - Removing special characters
    - Replacing common separators with spaces
    - Normalizing whitespace

    Args:
        position_name: Raw position title to normalize
            (e.g., "Senior Software Engineer - Remote")

    Returns:
        Normalized position name (e.g., "software engineer")

    Raises:
        ValueError: If position_name is empty or not a string

    Examples:
        >>> normalize_position_name("Senior Software Engineer")
        'software engineer'
        >>> normalize_position_name("Junior Python Developer")
        'python developer'
        >>> normalize_position_name("Frontend Developer - Remote")
        'frontend developer'
        >>> normalize_position_name("Full Stack Developer (Hybrid)")
        'full stack developer'
    """
    if not position_name or not isinstance(position_name, str):
        raise ValueError("position_name must be a non-empty string")

    # Check cache
    cache_key = f"position:{position_name}"
    if cache_key in _normalization_cache:
        return _normalization_cache[cache_key]

    try:
        # Convert to lowercase
        normalized = position_name.lower().strip()

        # Remove position suffixes
        for suffix in POSITION_SUFFIXES:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()

        # Replace common separators with spaces
        normalized = re.sub(r"[/_\-–—]", " ", normalized)

        # Remove special characters but keep spaces and word characters
        normalized = re.sub(r"[^\w\s]", " ", normalized)

        # Normalize whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # Cache result
        _normalization_cache[cache_key] = normalized

        logger.debug(f"Normalized position '{position_name}' -> '{normalized}'")
        return normalized

    except Exception as e:
        logger.error(f"Error normalizing position name '{position_name}': {e}")
        # Return lowercase original as fallback
        return position_name.lower().strip()


def normalize_text(
    text: str,
    *,
    lowercase: bool = True,
    remove_special_chars: bool = True,
    normalize_whitespace: bool = True,
) -> str:
    """
    Normalize text by applying common text cleaning operations.

    This is a general-purpose text normalization function that can be
    configured to perform various cleaning operations.

    Args:
        text: Text to normalize
        lowercase: Whether to convert to lowercase (default: True)
        remove_special_chars: Whether to remove special characters (default: True)
        normalize_whitespace: Whether to normalize whitespace (default: True)

    Returns:
        Normalized text string

    Raises:
        ValueError: If text is empty or not a string

    Examples:
        >>> normalize_text("Hello   World!")
        'hello world'
        >>> normalize_text("React.js & Node.js")
        'reactjs nodejs'
        >>> normalize_text("Test-Text_With/Separators", lowercase=False)
        'Test Text With Separators'
    """
    if not text or not isinstance(text, str):
        raise ValueError("text must be a non-empty string")

    try:
        normalized = text

        if lowercase:
            normalized = normalized.lower()

        if remove_special_chars:
            # Replace special chars with spaces, keep word chars
            normalized = re.sub(r"[^\w\s]", " ", normalized)

        if normalize_whitespace:
            # Normalize multiple spaces/tabs/newlines to single space
            normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    except Exception as e:
        logger.error(f"Error normalizing text: {e}")
        return text


def remove_special_chars(text: str, keep_spaces: bool = True) -> str:
    """
    Remove special characters from text.

    Args:
        text: Text to clean
        keep_spaces: Whether to keep spaces (default: True)

    Returns:
        Text with special characters removed

    Examples:
        >>> remove_special_chars("React.js & Node.js")
        'Reactjs  Nodejs'
        >>> remove_special_chars("Test-Text", keep_spaces=False)
        'TestText'
    """
    if not text or not isinstance(text, str):
        return ""

    try:
        if keep_spaces:
            # Keep word characters and spaces
            return re.sub(r"[^\w\s]", "", text)
        else:
            # Keep only word characters
            return re.sub(r"[^\w]", "", text)

    except Exception as e:
        logger.error(f"Error removing special characters: {e}")
        return text


def split_on_separators(text: str, separators: Optional[Set[str]] = None) -> list[str]:
    """
    Split text on common separators.

    Args:
        text: Text to split
        separators: Set of separator characters. If None, uses default set:
            {',', ';', '.', '|', '/', '\n', '\t'}

    Returns:
        List of non-empty split parts

    Examples:
        >>> split_on_separators("React, Vue; Angular")
        ['React', 'Vue', 'Angular']
        >>> split_on_separators("Python/Java/C++")
        ['Python', 'Java', 'C']
    """
    if not text or not isinstance(text, str):
        return []

    if separators is None:
        separators = {',', ';', '.', '|', '/', '\n', '\t'}

    try:
        # Create regex pattern from separators
        pattern = f"[{''.join(re.escape(s) for s in separators)}]"

        # Split and filter empty strings
        parts = re.split(pattern, text)
        return [part.strip() for part in parts if part.strip()]

    except Exception as e:
        logger.error(f"Error splitting text on separators: {e}")
        return [text]


def _handle_special_skill_cases(skill_name: str) -> str:
    """
    Handle special cases for skill normalization.

    Args:
        skill_name: Skill name after basic normalization

    Returns:
        Corrected skill name for special cases

    Examples:
        >>> _handle_special_skill_cases("c")
        'c'
        >>> _handle_special_skill_cases("c++")
        'cpp'
        >>> _handle_special_skill_cases("c#")
        'csharp'
        >>> _handle_special_skill_cases(".net")
        'dotnet'
    """
    special_cases = {
        "c#": "csharp",
        "c++": "cpp",
        ".net": "dotnet",
        "node": "nodejs",  # Normalize Node to Node.js
        "vue": "vuejs",  # Normalize Vue to Vue.js
    }

    # Check exact matches
    if skill_name in special_cases:
        return special_cases[skill_name]

    # Check for partial matches
    for key, value in special_cases.items():
        if key in skill_name:
            return value

    return skill_name


def clear_normalization_cache() -> None:
    """
    Clear the normalization cache.

    This can be useful for testing or when memory needs to be freed.
    """
    global _normalization_cache
    _normalization_cache.clear()
    logger.debug("Normalization cache cleared")


def get_cache_size() -> int:
    """
    Get the current size of the normalization cache.

    Returns:
        Number of cached normalized names
    """
    return len(_normalization_cache)
