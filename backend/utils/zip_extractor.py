"""
ZIP archive extraction for resume bulk upload operations.

This module provides functionality to extract and validate resume files from
uploaded ZIP archives. It handles nested directory structures, validates file
types using magic number verification, and provides detailed error reporting
for files that fail extraction or validation.

Security considerations:
- Path traversal prevention to avoid ZIP slip attacks
- Maximum file size limits to prevent decompression bombs
- Magic number validation to verify actual file types
- Maximum extraction count to prevent resource exhaustion
"""
import logging
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from backend.utils.file_validation import (
    FILE_SIGNATURES,
    validate_file_structure,
    validate_magic_number,
)

logger = logging.getLogger(__name__)


# Configuration constants
MAX_ZIP_SIZE_MB = 100  # Maximum ZIP file size in MB
MAX_EXTRACTED_FILES = 100  # Maximum number of files to extract
MAX_EXTRACTED_SIZE_MB = 500  # Maximum total extracted size in MB
MAX_SINGLE_FILE_SIZE_MB = 50  # Maximum single file size in MB

# Allowed file extensions for resume files (normalized lowercase without dot)
ALLOWED_EXTENSIONS = {"pdf", "docx"}


def _is_allowed_extension(filename: str) -> bool:
    """
    Check if a filename has an allowed extension.

    Args:
        filename: The filename to check

    Returns:
        True if the extension is allowed, False otherwise
    """
    ext = Path(filename).suffix.lower().lstrip(".")
    return ext in ALLOWED_EXTENSIONS


def _sanitize_filename(filename: str) -> Optional[str]:
    """
    Sanitize a filename to prevent path traversal attacks.

    This function removes directory components and dangerous characters
    from filenames extracted from ZIP archives to prevent ZIP slip attacks.

    Args:
        filename: The original filename from the ZIP archive

    Returns:
        Sanitized filename safe for use, or None if filename is dangerous
    """
    # Remove any directory components
    basename = Path(filename).name

    # Check for empty filename
    if not basename:
        return None

    # Check for dangerous patterns
    if ".." in basename or basename.startswith("."):
        logger.warning(f"Skipping potentially dangerous filename: {filename}")
        return None

    # Check for null bytes (could be used to bypass extension checks)
    if "\x00" in basename:
        logger.warning(f"Filename contains null byte: {filename}")
        return None

    return basename


def _validate_zip_file(zip_content: bytes) -> Tuple[bool, Optional[str]]:
    """
    Validate ZIP file structure and size.

    Args:
        zip_content: Raw bytes of the ZIP file

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if content is empty
    if not zip_content:
        return False, "ZIP file is empty"

    # Check ZIP file size
    zip_size_mb = len(zip_content) / (1024 * 1024)
    if zip_size_mb > MAX_ZIP_SIZE_MB:
        return False, f"ZIP file size ({zip_size_mb:.2f}MB) exceeds maximum ({MAX_ZIP_SIZE_MB}MB)"

    # Verify ZIP magic number
    zip_signature = b"PK\x03\x04"
    if not zip_content.startswith(zip_signature):
        return False, "File is not a valid ZIP archive (invalid magic number)"

    return True, None


def extract_resumes_from_zip(
    zip_source: Union[bytes, str, Path],
    *,
    validate_files: bool = True,
    skip_unsupported: bool = True,
    max_files: int = MAX_EXTRACTED_FILES,
    max_total_size_mb: int = MAX_EXTRACTED_SIZE_MB,
) -> Dict[str, Optional[Union[List[Dict], str, int]]]:
    """
    Extract and validate resume files from a ZIP archive.

    This function extracts PDF and DOCX files from a ZIP archive, validates
    their content using magic number verification, and returns detailed
    information about each extracted file.

    Args:
        zip_source: Source of the ZIP file - either raw bytes, file path string,
                   or Path object
        validate_files: Whether to validate extracted files (default: True)
        skip_unsupported: Whether to skip unsupported file types (default: True)
                         If False, unsupported files are included with a warning
        max_files: Maximum number of files to extract (default: 100)
        max_total_size_mb: Maximum total extracted size in MB (default: 500)

    Returns:
        Dictionary containing:
            - files: List of successfully extracted file dictionaries, each with:
                - filename: Sanitized filename
                - content: Raw file content as bytes
                - size: File size in bytes
                - extension: File extension (lowercase, no dot)
                - valid: Whether file passed validation
                - validation_error: Validation error message (None if valid)
            - file_count: Number of successfully extracted files
            - total_size: Total size of extracted files in bytes
            - skipped_count: Number of files skipped (unsupported type or too many)
            - error: Overall error message if extraction failed (None if successful)
            - warnings: List of warning messages for non-fatal issues

    Raises:
        ValueError: If zip_source is empty or invalid

    Examples:
        >>> # Extract from bytes
        >>> with open("resumes.zip", "rb") as f:
        ...     result = extract_resumes_from_zip(f.read())
        >>> for file_info in result["files"]:
        ...     print(f"{file_info['filename']}: {file_info['size']} bytes")

        >>> # Extract from file path
        >>> result = extract_resumes_from_zip("/path/to/resumes.zip")
        >>> if result["error"]:
        ...     print(f"Error: {result['error']}")
        ... else:
        ...     print(f"Extracted {result['file_count']} files")
    """
    files: List[Dict] = []
    skipped_count = 0
    total_size = 0
    warnings: List[str] = []

    try:
        # Get ZIP content from source
        if isinstance(zip_source, bytes):
            zip_content = zip_source
        elif isinstance(zip_source, (str, Path)):
            zip_path = Path(zip_source)
            if not zip_path.exists():
                logger.error(f"ZIP file not found: {zip_source}")
                return {
                    "files": [],
                    "file_count": 0,
                    "total_size": 0,
                    "skipped_count": 0,
                    "error": f"ZIP file not found: {zip_source}",
                    "warnings": [],
                }
            try:
                with open(zip_path, "rb") as f:
                    zip_content = f.read()
            except Exception as e:
                logger.error(f"Failed to read ZIP file: {e}")
                return {
                    "files": [],
                    "file_count": 0,
                    "total_size": 0,
                    "skipped_count": 0,
                    "error": f"Failed to read ZIP file: {str(e)}",
                    "warnings": [],
                }
        else:
            logger.error(f"Invalid zip_source type: {type(zip_source)}")
            return {
                "files": [],
                "file_count": 0,
                "total_size": 0,
                "skipped_count": 0,
                "error": f"Invalid zip_source type: {type(zip_source).__name__}",
                "warnings": [],
            }

        # Validate ZIP file
        is_valid, error = _validate_zip_file(zip_content)
        if not is_valid:
            logger.error(f"ZIP validation failed: {error}")
            return {
                "files": [],
                "file_count": 0,
                "total_size": 0,
                "skipped_count": 0,
                "error": error,
                "warnings": [],
            }

        logger.info(f"Extracting ZIP archive ({len(zip_content)} bytes)")

        # Open ZIP from bytes
        zip_buffer = BytesIO(zip_content)
        max_total_size_bytes = max_total_size_mb * 1024 * 1024
        max_single_file_bytes = MAX_SINGLE_FILE_SIZE_MB * 1024 * 1024

        with zipfile.ZipFile(zip_buffer, mode='r') as zip_file:
            # Get list of file infos
            file_infos = zip_file.infolist()

            # Check if too many files
            if len(file_infos) > max_files * 2:
                warnings.append(
                    f"ZIP contains {len(file_infos)} files, extracting up to {max_files}"
                )

            for file_info in file_infos:
                # Skip directories
                if file_info.is_dir():
                    continue

                # Check extraction limit
                if len(files) >= max_files:
                    skipped_count += len(file_infos) - file_infos.index(file_info)
                    warnings.append(
                        f"Reached maximum file limit ({max_files}), "
                        f"skipped {skipped_count} remaining files"
                    )
                    break

                original_filename = file_info.filename

                # Sanitize filename for security
                safe_filename = _sanitize_filename(original_filename)
                if safe_filename is None:
                    skipped_count += 1
                    logger.warning(f"Skipped unsafe filename: {original_filename}")
                    continue

                # Check file extension
                if not _is_allowed_extension(safe_filename):
                    if skip_unsupported:
                        skipped_count += 1
                        logger.debug(f"Skipped unsupported file: {safe_filename}")
                        continue
                    else:
                        # Include with warning (but don't validate)
                        pass

                # Check file size before extraction (decompression bomb protection)
                uncompressed_size = file_info.file_size
                if uncompressed_size > max_single_file_bytes:
                    skipped_count += 1
                    warning_msg = (
                        f"Skipped file exceeding size limit: {safe_filename} "
                        f"({uncompressed_size / (1024 * 1024):.2f}MB > {MAX_SINGLE_FILE_SIZE_MB}MB)"
                    )
                    warnings.append(warning_msg)
                    logger.warning(warning_msg)
                    continue

                # Check total extracted size
                if total_size + uncompressed_size > max_total_size_bytes:
                    skipped_count += 1
                    warning_msg = (
                        f"Total extracted size would exceed limit, skipping: {safe_filename}"
                    )
                    warnings.append(warning_msg)
                    logger.warning(warning_msg)
                    continue

                try:
                    # Extract file content
                    file_content = zip_file.read(file_info)

                    # Verify actual extracted size matches expected
                    actual_size = len(file_content)
                    if actual_size != uncompressed_size:
                        warning_msg = (
                            f"Size mismatch for {safe_filename}: "
                            f"expected {uncompressed_size}, got {actual_size}"
                        )
                        warnings.append(warning_msg)
                        logger.warning(warning_msg)

                    # Get file extension
                    extension = Path(safe_filename).suffix.lower().lstrip(".")

                    # Validate file if requested and it's an allowed type
                    is_valid_file = True
                    validation_error = None

                    if validate_files and extension in ALLOWED_EXTENSIONS:
                        # Validate magic number
                        is_valid_file, validation_error = validate_magic_number(
                            file_content, f".{extension}"
                        )

                        # If magic number passed, also validate structure
                        if is_valid_file:
                            is_valid_file, validation_error = validate_file_structure(
                                file_content, f".{extension}"
                            )

                    # Create file info dictionary
                    file_dict = {
                        "filename": safe_filename,
                        "original_path": original_filename,
                        "content": file_content,
                        "size": actual_size,
                        "extension": extension,
                        "valid": is_valid_file,
                        "validation_error": validation_error,
                    }

                    files.append(file_dict)
                    total_size += actual_size

                    if not is_valid_file:
                        logger.warning(
                            f"Extracted file failed validation: {safe_filename} - {validation_error}"
                        )
                    else:
                        logger.debug(f"Successfully extracted: {safe_filename} ({actual_size} bytes)")

                except Exception as e:
                    skipped_count += 1
                    error_msg = f"Failed to extract {safe_filename}: {str(e)}"
                    warnings.append(error_msg)
                    logger.error(error_msg)
                    continue

        # Check if any files were extracted
        if not files:
            error_msg = "No valid resume files found in ZIP archive"
            if skipped_count > 0:
                error_msg += f" ({skipped_count} files skipped)"
            logger.warning(error_msg)
            return {
                "files": [],
                "file_count": 0,
                "total_size": 0,
                "skipped_count": skipped_count,
                "error": error_msg,
                "warnings": warnings,
            }

        logger.info(
            f"Successfully extracted {len(files)} files "
            f"({total_size / (1024 * 1024):.2f}MB total)"
        )

        return {
            "files": files,
            "file_count": len(files),
            "total_size": total_size,
            "skipped_count": skipped_count,
            "error": None,
            "warnings": warnings,
        }

    except zipfile.BadZipFile as e:
        logger.error(f"Invalid ZIP file: {e}")
        return {
            "files": [],
            "file_count": 0,
            "total_size": 0,
            "skipped_count": 0,
            "error": f"Invalid or corrupted ZIP file: {str(e)}",
            "warnings": warnings,
        }
    except Exception as e:
        logger.error(f"Failed to extract ZIP archive: {e}")
        return {
            "files": [],
            "file_count": 0,
            "total_size": 0,
            "skipped_count": 0,
            "error": f"ZIP extraction failed: {str(e)}",
            "warnings": warnings,
        }


def get_zip_info(
    zip_source: Union[bytes, str, Path],
) -> Dict[str, Optional[Union[List[Dict], str, int]]]:
    """
    Get information about files in a ZIP archive without extracting them.

    This is a lightweight function to preview ZIP contents and get metadata
    about files without actually reading their contents.

    Args:
        zip_source: Source of the ZIP file - either raw bytes, file path string,
                   or Path object

    Returns:
        Dictionary containing:
            - files: List of file info dictionaries, each with:
                - filename: Filename in the archive
                - size: Uncompressed file size in bytes
                - compressed_size: Compressed size in bytes
                - extension: File extension (lowercase, no dot)
                - is_directory: Whether entry is a directory
                - is_resume: Whether file is a resume (PDF/DOCX)
            - file_count: Total number of files (excluding directories)
            - total_size: Total uncompressed size in bytes
            - compression_ratio: Overall compression ratio
            - resume_count: Number of resume files
            - error: Error message if failed (None if successful)

    Examples:
        >>> info = get_zip_info("/path/to/resumes.zip")
        >>> print(f"Found {info['resume_count']} resumes in {info['file_count']} files")
    """
    files: List[Dict] = []

    try:
        # Get ZIP content from source
        if isinstance(zip_source, bytes):
            zip_content = zip_source
        elif isinstance(zip_source, (str, Path)):
            zip_path = Path(zip_source)
            if not zip_path.exists():
                return {
                    "files": [],
                    "file_count": 0,
                    "total_size": 0,
                    "compression_ratio": 0.0,
                    "resume_count": 0,
                    "error": f"ZIP file not found: {zip_source}",
                }
            with open(zip_path, "rb") as f:
                zip_content = f.read()
        else:
            return {
                "files": [],
                "file_count": 0,
                "total_size": 0,
                "compression_ratio": 0.0,
                "resume_count": 0,
                "error": f"Invalid zip_source type: {type(zip_source).__name__}",
            }

        # Validate basic ZIP structure
        is_valid, error = _validate_zip_file(zip_content)
        if not is_valid:
            return {
                "files": [],
                "file_count": 0,
                "total_size": 0,
                "compression_ratio": 0.0,
                "resume_count": 0,
                "error": error,
            }

        zip_buffer = BytesIO(zip_content)
        total_compressed = 0
        total_uncompressed = 0
        resume_count = 0

        with zipfile.ZipFile(zip_buffer, mode='r') as zip_file:
            for file_info in zip_file.infolist():
                is_directory = file_info.is_dir()
                filename = file_info.filename

                # Sanitize filename for display
                safe_filename = _sanitize_filename(filename) or filename
                extension = Path(safe_filename).suffix.lower().lstrip(".")
                is_resume = extension in ALLOWED_EXTENSIONS

                if is_resume and not is_directory:
                    resume_count += 1

                file_dict = {
                    "filename": safe_filename,
                    "size": file_info.file_size,
                    "compressed_size": file_info.compress_size,
                    "extension": extension,
                    "is_directory": is_directory,
                    "is_resume": is_resume,
                }

                files.append(file_dict)
                total_compressed += file_info.compress_size
                total_uncompressed += file_info.file_size

        # Calculate compression ratio
        compression_ratio = (
            total_compressed / total_uncompressed if total_uncompressed > 0 else 0.0
        )

        # Count files (excluding directories)
        file_count = sum(1 for f in files if not f["is_directory"])

        return {
            "files": files,
            "file_count": file_count,
            "total_size": total_uncompressed,
            "compression_ratio": compression_ratio,
            "resume_count": resume_count,
            "error": None,
        }

    except zipfile.BadZipFile as e:
        logger.error(f"Invalid ZIP file: {e}")
        return {
            "files": [],
            "file_count": 0,
            "total_size": 0,
            "compression_ratio": 0.0,
            "resume_count": 0,
            "error": f"Invalid or corrupted ZIP file: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Failed to read ZIP info: {e}")
        return {
            "files": [],
            "file_count": 0,
            "total_size": 0,
            "compression_ratio": 0.0,
            "resume_count": 0,
            "error": f"Failed to read ZIP info: {str(e)}",
        }
