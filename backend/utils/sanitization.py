"""
Filename sanitization utilities to prevent path traversal attacks.

This module provides functions for sanitizing user-provided filenames to prevent
path traversal and other filesystem-based attacks. It ensures that filenames are
safe to use when storing uploaded files on the filesystem.

Path traversal attacks occur when malicious users craft filenames with directory
traversal sequences (e.g., '../../../etc/passwd') to access files outside the
intended directory. This module prevents such attacks by:
1. Removing all directory separators and path components
2. Validating against known malicious patterns
3. Replacing dangerous characters
4. Limiting filename length
"""
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# Patterns that indicate path traversal attempts
PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",       # Parent directory (../)
    r"\.\./",       # Parent directory with encoded slash
    r"%2e%2e",      # Double-dot encoded
    r"%252e",       # Partially encoded double-dot
    r"\.\.\\",      # Windows parent directory (..\)
    r"~",           # Home directory reference
    r"/etc/",       # Unix system paths
    r"C:\\",        # Windows drive paths
    r"\\\\",        # UNC paths
    r"\0",          # Null bytes (path truncation)
]

# Compiled regex pattern for efficient matching
PATH_TRAVERSAL_REGEX = re.compile(
    "|".join(PATH_TRAVERSAL_PATTERNS),
    re.IGNORECASE
)

# Characters that are problematic in filenames
DANGEROUS_CHARS = {
    "/": "",        # Unix path separator
    "\\": "",       # Windows path separator
    ":": "-",       # Windows drive separator, colon in filenames
    "*": "",        # Wildcard (Windows)
    "?": "",        # Wildcard (Windows)
    '"': "",        # Quote (Windows)
    "<": "",        # Redirect operator (Windows)
    ">": "",        # Redirect operator (Windows)
    "|": "",        # Pipe operator (Windows)
    "\x00": "",     # Null byte
    "\n": "",       # Newline
    "\r": "",       # Carriage return
    "\t": "",       # Tab
}

# Maximum filename length (before extension)
MAX_FILENAME_BASE = 255

# Minimum filename length after sanitization
MIN_FILENAME_LENGTH = 1


def sanitize_filename(filename: str, preserve_extension: bool = True) -> str:
    """
    Sanitize a user-provided filename to prevent path traversal attacks.

    This function removes dangerous characters, path components, and ensures
    the filename is safe for use on the filesystem. It can optionally preserve
    the file extension for proper file type handling.

    Args:
        filename: The user-provided filename to sanitize
        preserve_extension: If True, preserves the file extension (default: True)

    Returns:
        A sanitized filename safe for filesystem use

    Raises:
        ValueError: If filename is None, empty, or cannot be sanitized

    Examples:
        >>> # Safe filenames remain unchanged
        >>> sanitize_filename("resume.pdf")
        'resume.pdf'

        >>> # Path traversal is stripped
        >>> sanitize_filename("../../etc/passwd")
        'etcpasswd'

        >>> # Extension can be preserved or removed
        >>> sanitize_filename("my resume.pdf", preserve_extension=True)
        'my-resume.pdf'
        >>> sanitize_filename("my resume.pdf", preserve_extension=False)
        'my-resume'

        >>> # Dangerous characters are removed/replaced
        >>> sanitize_filename("resume:final*.pdf")
        'resume-final.pdf'
    """
    if not filename or not isinstance(filename, str):
        logger.warning(f"Invalid filename provided: {filename}")
        raise ValueError(f"Invalid filename: {filename}")

    original_filename = filename
    filename = filename.strip()

    if not filename:
        logger.warning("Empty filename after stripping whitespace")
        raise ValueError("Filename is empty")

    # Check for path traversal patterns
    traversal_match = PATH_TRAVERSAL_REGEX.search(filename)
    if traversal_match:
        logger.warning(
            f"Path traversal pattern detected in filename: {original_filename}. "
            f"Match: {traversal_match.group()}"
        )

    # Extract extension if preserving
    extension = ""
    if preserve_extension:
        path_obj = Path(filename)
        extension = path_obj.suffix
        filename = filename[:-len(extension)] if extension else filename

    # Remove dangerous characters
    for char, replacement in DANGEROUS_CHARS.items():
        filename = filename.replace(char, replacement)

    # Replace multiple consecutive spaces/hyphens/underscores with single hyphen
    filename = re.sub(r"[\s_-]+", "-", filename)

    # Remove leading/trailing hyphens and dots
    filename = filename.strip("-. ")

    # Collapse multiple consecutive hyphens
    filename = re.sub(r"-{2,}", "-", filename)

    # Remove any remaining path separators that might have been encoded
    filename = filename.replace("/", "").replace("\\", "")

    # Ensure filename is not empty after sanitization
    if not filename:
        # Generate a safe fallback filename
        filename = "file"

    # Truncate to maximum length
    if len(filename) > MAX_FILENAME_BASE:
        filename = filename[:MAX_FILENAME_BASE]
        logger.info(
            f"Filename truncated from {len(original_filename)} to {MAX_FILENAME_BASE} characters"
        )

    # Re-add extension if preserving and it was present
    if preserve_extension and extension:
        filename = filename + extension

    # Final sanity check - ensure we haven't introduced any issues
    if not filename or filename in {".", ".."}:
        logger.error(f"Sanitization resulted in invalid filename: {filename}")
        raise ValueError("Filename sanitization failed - invalid result")

    logger.info(f"Sanitized filename: '{original_filename}' -> '{filename}'")
    return filename


def validate_filename_safe(filename: str) -> tuple[bool, Optional[str]]:
    """
    Validate that a filename is safe and does not contain path traversal patterns.

    This is a read-only validation function that checks if a filename is safe
    without modifying it. Useful for pre-validation and logging security events.

    Args:
        filename: The filename to validate

    Returns:
        Tuple of (is_safe, error_message):
            - is_safe: True if filename is safe, False otherwise
            - error_message: Detailed error message if unsafe, None otherwise

    Examples:
        >>> # Safe filename
        >>> is_safe, error = validate_filename_safe("resume.pdf")
        >>> assert is_safe is True
        >>> assert error is None

        >>> # Path traversal attempt
        >>> is_safe, error = validate_filename_safe("../../etc/passwd")
        >>> assert is_safe is False
        >>> assert "path traversal" in error.lower()
    """
    if not filename or not isinstance(filename, str):
        return False, "Filename is empty or invalid"

    filename = filename.strip()

    if not filename:
        return False, "Filename is empty"

    # Check for path traversal patterns
    traversal_match = PATH_TRAVERSAL_REGEX.search(filename)
    if traversal_match:
        dangerous_pattern = traversal_match.group()
        logger.warning(
            f"Path traversal attempt detected: '{filename}' contains '{dangerous_pattern}'"
        )
        return False, f"Filename contains path traversal pattern: {dangerous_pattern}"

    # Check for dangerous characters
    found_dangerous = []
    for char in DANGEROUS_CHARS:
        if char in filename:
            found_dangerous.append(repr(char))

    if found_dangerous:
        chars_str = ", ".join(found_dangerous)
        logger.warning(
            f"Filename contains dangerous characters: '{filename}' has {chars_str}"
        )
        return False, f"Filename contains dangerous characters: {chars_str}"

    # Check for Windows device names (CON, PRN, AUX, NUL, COM*, LPT*)
    base_name = Path(filename).stem.upper()
    windows_devices = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    }
    if base_name in windows_devices:
        logger.warning(f"Filename is a Windows reserved device name: {base_name}")
        return False, f"Filename is a reserved device name: {base_name}"

    return True, None


def sanitize_and_validate(filename: str, preserve_extension: bool = True) -> str:
    """
    Sanitize and validate a filename in one operation.

    This convenience function combines sanitization and validation, raising
    an exception if the filename cannot be made safe.

    Args:
        filename: The filename to sanitize and validate
        preserve_extension: If True, preserves the file extension (default: True)

    Returns:
        A sanitized filename safe for filesystem use

    Raises:
        ValueError: If filename is invalid or cannot be sanitized

    Examples:
        >>> # Safe filename
        >>> sanitize_and_validate("resume.pdf")
        'resume.pdf'

        >>> # Path traversal - gets sanitized
        >>> sanitize_and_validate("../../my resume.pdf")
        'my-resume.pdf'
    """
    # First validate to detect potential attacks (for logging)
    is_safe, error_msg = validate_filename_safe(filename)
    if not is_safe:
        logger.warning(f"Filename validation failed: {error_msg}. Proceeding with sanitization.")

    # Then sanitize to get a safe filename
    return sanitize_filename(filename, preserve_extension)


def get_safe_stored_filename(
    original_filename: str,
    unique_id: str,
    preserve_extension: bool = True
) -> str:
    """
    Generate a safe filename for storage using a unique identifier.

    This function is designed for file upload scenarios where you want to:
    1. Use a UUID-based filename for storage (prevents collisions)
    2. Preserve the file extension for type identification
    3. Optionally sanitize the original filename for display purposes

    Args:
        original_filename: The user-provided original filename
        unique_id: A unique identifier (typically a UUID)
        preserve_extension: If True, preserves the file extension (default: True)

    Returns:
        A safe filename for storage (e.g., "a1b2c3d4.pdf")

    Examples:
        >>> import uuid
        >>> uid = str(uuid.uuid4())
        >>> get_safe_stored_filename("resume.pdf", uid)
        'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d.pdf'

        >>> # With dangerous original filename
        >>> get_safe_stored_filename("../../etc/passwd", "my-uuid")
        'my-uuid'
    """
    # Get just the extension from the sanitized filename
    if preserve_extension:
        safe_name = sanitize_filename(original_filename, preserve_extension=True)
        extension = Path(safe_name).suffix
    else:
        extension = ""

    # Return unique_id + extension for storage
    return f"{unique_id}{extension}"
