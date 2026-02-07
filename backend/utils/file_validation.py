"""
File validation utilities for magic number verification and content integrity.

This module provides functions for validating uploaded files by checking their
magic numbers (file signatures) to ensure the actual file content matches the
declared file type. This prevents attackers from uploading malicious files
renamed with benign extensions (e.g., malware.exe renamed to resume.pdf).
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# Magic number constants for allowed file types
# These are the byte sequences that appear at the beginning of valid files
FILE_SIGNATURES: Dict[str, bytes] = {
    "pdf": b"%PDF-",  # PDF files start with %PDF-
    "docx": b"PK\x03\x04",  # DOCX files are ZIP archives starting with PK
}


# Maximum bytes to read for magic number validation
MAX_HEADER_SIZE = 12


def validate_magic_number(
    file_content: bytes, file_extension: str, locale: str = "en"
) -> Tuple[bool, Optional[str]]:
    """
    Validate that the file content matches the expected magic number for its extension.

    This function reads the file header and checks if the magic number (file signature)
    matches what's expected for the declared file type. This prevents attackers from
    uploading malicious files renamed with benign extensions.

    Args:
        file_content: The raw bytes of the uploaded file
        file_extension: The file extension including the dot (e.g., '.pdf', '.docx')
        locale: Language code for translated error messages (default: 'en')

    Returns:
        Tuple of (is_valid, error_message):
            - is_valid: True if magic number matches, False otherwise
            - error_message: Detailed error message if validation fails, None otherwise

    Raises:
        ValueError: If file_content is empty or file_extension is invalid

    Examples:
        >>> # Valid PDF file
        >>> content = b"%PDF-1.4\\n%..."
        >>> is_valid, error = validate_magic_number(content, ".pdf")
        >>> assert is_valid is True
        >>> assert error is None

        >>> # Invalid file (EXE renamed to PDF)
        >>> content = b"MZ\\x90\\x00..."  # PE executable header
        >>> is_valid, error = validate_magic_number(content, ".pdf")
        >>> assert is_valid is False
        >>> assert "magic number" in error.lower()
    """
    try:
        # Validate inputs
        if not file_content:
            logger.warning("Empty file content provided for magic number validation")
            return False, "File content is empty"

        if not file_extension or not isinstance(file_extension, str):
            logger.warning(f"Invalid file extension: {file_extension}")
            return False, f"Invalid file extension: {file_extension}"

        # Normalize extension to lowercase without dot
        ext = file_extension.lower().lstrip(".")

        if ext not in FILE_SIGNATURES:
            logger.warning(f"Unsupported file extension for validation: {ext}")
            return False, f"Unsupported file extension: {file_extension}"

        # Get expected magic number for this file type
        expected_signature = FILE_SIGNATURES[ext]

        # Read file header (limit to MAX_HEADER_SIZE for security)
        file_header = file_content[:MAX_HEADER_SIZE]

        # Check if file is too small to contain valid header
        if len(file_header) < len(expected_signature):
            logger.warning(
                f"File too small to be valid {ext}: {len(file_header)} bytes "
                f"(expected at least {len(expected_signature)} bytes)"
            )
            return False, f"File is too small to be a valid {file_extension} file"

        # Validate magic number
        if not file_header.startswith(expected_signature):
            actual_hex = file_header[:8].hex() if len(file_header) >= 8 else "too short"
            expected_hex = expected_signature.hex()

            logger.warning(
                f"Magic number validation failed for {file_extension}: "
                f"expected {expected_hex}, got {actual_hex}"
            )

            error_message = (
                f"Invalid file content: file header does not match {file_extension} format. "
                f"Expected magic number '{expected_signature.decode('ascii', errors='ignore')}' "
                f"but file appears to be a different type. "
                f"This may indicate a malicious or corrupted file."
            )
            return False, error_message

        logger.info(f"Magic number validation passed for {file_extension}")
        return True, None

    except Exception as e:
        logger.error(f"Error during magic number validation: {e}")
        return False, f"Error validating file content: {str(e)}"


def validate_file_structure(
    file_content: bytes, file_extension: str, locale: str = "en"
) -> Tuple[bool, Optional[str]]:
    """
    Perform basic structural integrity checks on the file content.

    This function validates that the file has a plausible structure for its type,
    checking for common corruption patterns and ensuring the file appears to be
    well-formed. This is a lightweight check that doesn't fully parse the file.

    Args:
        file_content: The raw bytes of the uploaded file
        file_extension: The file extension including the dot (e.g., '.pdf', '.docx')
        locale: Language code for translated error messages (default: 'en')

    Returns:
        Tuple of (is_valid, error_message):
            - is_valid: True if structure appears valid, False otherwise
            - error_message: Detailed error message if validation fails, None otherwise

    Raises:
        ValueError: If file_content is empty or file_extension is invalid

    Examples:
        >>> # Valid PDF structure
        >>> content = b"%PDF-1.4\\n%...%%EOF"
        >>> is_valid, error = validate_file_structure(content, ".pdf")
        >>> assert is_valid is True

        >>> # Truncated PDF
        >>> content = b"%PDF-1.4\\n%..."  # Missing EOF marker
        >>> is_valid, error = validate_file_structure(content, ".pdf")
        >>> # May return False with warning about incomplete file
    """
    try:
        # Validate inputs
        if not file_content:
            logger.warning("Empty file content provided for structure validation")
            return False, "File content is empty"

        if not file_extension or not isinstance(file_extension, str):
            logger.warning(f"Invalid file extension: {file_extension}")
            return False, f"Invalid file extension: {file_extension}"

        # Normalize extension
        ext = file_extension.lower().lstrip(".")

        # Basic size checks
        file_size = len(file_content)

        # Check minimum file sizes
        min_sizes = {
            "pdf": 100,  # PDF header + minimal content
            "docx": 500,  # ZIP archive with DOCX structure
        }

        min_size = min_sizes.get(ext, 100)
        if file_size < min_size:
            logger.warning(
                f"File size ({file_size} bytes) below minimum for {ext} ({min_size} bytes)"
            )
            return False, f"File is too small to be a valid {file_extension} file"

        # Check maximum file sizes (prevent decompression bombs / DoS)
        max_sizes = {
            "pdf": 50 * 1024 * 1024,  # 50 MB
            "docx": 50 * 1024 * 1024,  # 50 MB
        }

        max_size = max_sizes.get(ext, 10 * 1024 * 1024)  # Default 10 MB
        if file_size > max_size:
            logger.warning(
                f"File size ({file_size} bytes) exceeds maximum for {ext} ({max_size} bytes)"
            )
            return False, f"File exceeds maximum allowed size for {file_extension}"

        # Type-specific structure checks
        if ext == "pdf":
            # PDF should end with %%EOF marker (last 1KB)
            eof_marker = b"%%EOF"
            file_tail = file_content[-1024:] if file_size > 1024 else file_content
            if eof_marker not in file_tail:
                logger.warning(f"PDF file missing %%EOF marker")
                return False, "PDF file appears to be incomplete or corrupted (missing EOF marker)"

        elif ext == "docx":
            # DOCX is a ZIP archive - should have PK signatures throughout
            # Check for end of central directory signature
            end_central_dir = b"PK\x05\x06"
            if file_size > 100:  # Only check if file is reasonably sized
                file_tail = file_content[-100:] if file_size > 100 else file_content
                # Not all ZIPs have the end central dir at the very end,
                # but we should see it somewhere in the last part of the file
                if end_central_dir not in file_tail:
                    # This is a warning, not a hard failure, as some valid ZIPs
                    # may have different structures
                    logger.warning(f"DOCX file may have incomplete ZIP structure")

        logger.info(f"File structure validation passed for {file_extension}")
        return True, None

    except Exception as e:
        logger.error(f"Error during file structure validation: {e}")
        return False, f"Error validating file structure: {str(e)}"


def get_file_signature(file_extension: str) -> Optional[bytes]:
    """
    Get the expected magic number signature for a given file extension.

    This is a helper function that returns the file signature constant
    for the given extension. Useful for testing and documentation.

    Args:
        file_extension: The file extension with or without dot (e.g., '.pdf', 'pdf')

    Returns:
        The magic number bytes for the file type, or None if extension is not supported

    Examples:
        >>> signature = get_file_signature(".pdf")
        >>> assert signature == b"%PDF-"
        >>> assert get_file_signature("docx") == b"PK\\x03\\x04"
    """
    ext = file_extension.lower().lstrip(".")
    return FILE_SIGNATURES.get(ext)


def is_supported_file_type(file_extension: str) -> bool:
    """
    Check if a file extension is supported for magic number validation.

    Args:
        file_extension: The file extension with or without dot (e.g., '.pdf', 'pdf')

    Returns:
        True if the file type is supported, False otherwise

    Examples:
        >>> assert is_supported_file_type(".pdf") is True
        >>> assert is_supported_file_type("docx") is True
        >>> assert is_supported_file_type(".exe") is False
    """
    ext = file_extension.lower().lstrip(".")
    return ext in FILE_SIGNATURES
