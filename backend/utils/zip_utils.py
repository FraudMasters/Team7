"""
ZIP archive creation for resume bulk export operations.

This module provides functionality to create ZIP archives containing multiple
resume files, with validation and error handling for bulk export operations.
The utility handles file reading, archive creation, and provides detailed error
messages for failed operations.
"""
import logging
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def create_resume_zip(
    resume_files: List[Dict[str, Union[str, bytes, Path]]],
    *,
    zip_filename: str = "resumes.zip",
    compression_level: int = 6,
) -> Dict[str, Optional[Union[bytes, str, int, List[str]]]]:
    """
    Create a ZIP archive containing multiple resume files.

    This function creates a ZIP archive from a list of resume files provided as
    dictionaries with filename and content (either as bytes or file path). It validates
    inputs, handles compression, and provides detailed error messages for failed operations.

    Args:
        resume_files: List of dictionaries, each containing:
            - filename: Name of the file in the ZIP archive
            - content: File content as bytes (optional if 'file_path' provided)
            - file_path: Path to file on disk (optional if 'content' provided)
        zip_filename: Name for the ZIP file (default: "resumes.zip")
        compression_level: ZIP compression level (0-9, default: 6)
                          0 = no compression, 9 = maximum compression

    Returns:
        Dictionary containing:
            - zip_bytes: ZIP archive content as bytes (None if failed)
            - file_count: Number of files added to ZIP (0 if failed)
            - total_size: Total size of ZIP archive in bytes (0 if failed)
            - filenames: List of filenames added to ZIP (empty if failed)
            - error: Error message if creation failed (None if successful)
            - compression_ratio: Compression ratio (compressed_size / uncompressed_size)

    Raises:
        ValueError: If resume_files is empty or file data is invalid

    Examples:
        >>> # Create ZIP from bytes
        >>> files = [
        ...     {"filename": "resume1.pdf", "content": b"PDF data..."},
        ...     {"filename": "resume2.pdf", "content": b"More PDF data..."},
        ... ]
        >>> result = create_resume_zip(files)
        >>> if result["error"]:
        ...     print(f"Error: {result['error']}")
        ... else:
        ...     print(f"Created ZIP with {result['file_count']} files")

        >>> # Create ZIP from file paths
        >>> files = [
        ...     {"filename": "john_doe.pdf", "file_path": "/path/to/john.pdf"},
        ...     {"filename": "jane_smith.pdf", "file_path": "/path/to/jane.pdf"},
        ... ]
        >>> result = create_resume_zip(files, zip_filename="candidates.zip")
    """
    # Validate input
    if not resume_files:
        logger.error("Empty resume_files list provided")
        return {
            "zip_bytes": None,
            "file_count": 0,
            "total_size": 0,
            "filenames": [],
            "error": "Empty resume_files list provided",
            "compression_ratio": 0.0,
        }

    # Validate compression level
    if not 0 <= compression_level <= 9:
        logger.error(f"Invalid compression level: {compression_level}")
        return {
            "zip_bytes": None,
            "file_count": 0,
            "total_size": 0,
            "filenames": [],
            "error": f"Invalid compression level: {compression_level} (must be 0-9)",
            "compression_ratio": 0.0,
        }

    try:
        logger.info(f"Creating ZIP archive '{zip_filename}' with {len(resume_files)} files")

        # Create in-memory ZIP file
        zip_buffer = BytesIO()
        added_files = []
        total_uncompressed_size = 0

        with zipfile.ZipFile(
            zip_buffer,
            mode='w',
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=compression_level,
        ) as zip_file:
            for idx, file_info in enumerate(resume_files, start=1):
                try:
                    # Validate file_info structure
                    if not isinstance(file_info, dict):
                        logger.error(f"File info #{idx} is not a dictionary")
                        continue

                    filename = file_info.get("filename")
                    if not filename:
                        logger.error(f"File info #{idx} missing 'filename' field")
                        continue

                    content = file_info.get("content")
                    file_path = file_info.get("file_path")

                    # Validate that either content or file_path is provided
                    if content is None and file_path is None:
                        logger.error(f"File '{filename}' missing both 'content' and 'file_path'")
                        continue

                    # Get file content
                    if content is not None:
                        # Use provided content
                        if not isinstance(content, bytes):
                            logger.error(f"File '{filename}' content is not bytes")
                            continue
                        file_bytes = content
                    else:
                        # Read from file path
                        file_path_obj = Path(file_path)
                        if not file_path_obj.exists():
                            logger.error(f"File path does not exist: {file_path}")
                            continue

                        try:
                            with open(file_path_obj, "rb") as f:
                                file_bytes = f.read()
                        except Exception as e:
                            logger.error(f"Failed to read file '{filename}' from {file_path}: {e}")
                            continue

                    # Security check: Prevent path traversal in filename
                    if '..' in filename or filename.startswith('/'):
                        logger.warning(f"Skipping potentially malicious filename: {filename}")
                        continue

                    # Add file to ZIP
                    zip_file.writestr(filename, file_bytes)
                    added_files.append(filename)
                    total_uncompressed_size += len(file_bytes)

                    logger.debug(f"Added to ZIP: {filename} ({len(file_bytes)} bytes)")

                except Exception as e:
                    logger.error(f"Error processing file #{idx} for ZIP: {e}")
                    continue

        # Check if any files were added
        if not added_files:
            logger.error("No files were successfully added to ZIP archive")
            return {
                "zip_bytes": None,
                "file_count": 0,
                "total_size": 0,
                "filenames": [],
                "error": "No valid files were added to ZIP archive (all files failed validation or reading)",
                "compression_ratio": 0.0,
            }

        # Get final ZIP size
        zip_bytes = zip_buffer.getvalue()
        total_size = len(zip_bytes)

        # Calculate compression ratio
        compression_ratio = total_size / total_uncompressed_size if total_uncompressed_size > 0 else 0.0

        logger.info(
            f"Successfully created ZIP archive: {len(added_files)} files, "
            f"{total_size} bytes (compression: {compression_ratio:.1%})"
        )

        return {
            "zip_bytes": zip_bytes,
            "file_count": len(added_files),
            "total_size": total_size,
            "filenames": added_files,
            "error": None,
            "compression_ratio": compression_ratio,
        }

    except Exception as e:
        logger.error(f"Failed to create ZIP archive: {e}")
        return {
            "zip_bytes": None,
            "file_count": 0,
            "total_size": 0,
            "filenames": [],
            "error": f"ZIP creation failed: {str(e)}",
            "compression_ratio": 0.0,
        }


def create_resume_zip_from_paths(
    file_paths: List[Union[str, Path]],
    *,
    zip_filename: str = "resumes.zip",
    compression_level: int = 6,
    preserve_structure: bool = False,
) -> Dict[str, Optional[Union[bytes, str, int, List[str]]]]:
    """
    Create a ZIP archive from a list of file paths.

    This is a convenience function that wraps create_resume_zip for cases where
    you have a list of file paths instead of file info dictionaries.

    Args:
        file_paths: List of file paths to include in the ZIP archive
        zip_filename: Name for the ZIP file (default: "resumes.zip")
        compression_level: ZIP compression level (0-9, default: 6)
        preserve_structure: Whether to preserve directory structure in ZIP
                          (default: False - uses only filenames)

    Returns:
        Dictionary containing:
            - zip_bytes: ZIP archive content as bytes (None if failed)
            - file_count: Number of files added to ZIP (0 if failed)
            - total_size: Total size of ZIP archive in bytes (0 if failed)
            - filenames: List of filenames added to ZIP (empty if failed)
            - error: Error message if creation failed (None if successful)
            - compression_ratio: Compression ratio (compressed_size / uncompressed_size)

    Examples:
        >>> files = ["/data/resume1.pdf", "/data/resume2.pdf"]
        >>> result = create_resume_zip_from_paths(files)
        >>> if result["error"]:
        ...     print(f"Error: {result['error']}")
        ... else:
        ...     with open("export.zip", "wb") as f:
        ...         f.write(result["zip_bytes"])
    """
    # Validate input
    if not file_paths:
        logger.error("Empty file_paths list provided")
        return {
            "zip_bytes": None,
            "file_count": 0,
            "total_size": 0,
            "filenames": [],
            "error": "Empty file_paths list provided",
            "compression_ratio": 0.0,
        }

    # Convert file paths to file info dictionaries
    resume_files = []
    for file_path in file_paths:
        path_obj = Path(file_path)

        # Determine filename in ZIP
        if preserve_structure:
            # Preserve directory structure
            filename = str(path_obj)
        else:
            # Use only the base filename
            filename = path_obj.name

        resume_files.append({
            "filename": filename,
            "file_path": str(path_obj),
        })

    # Delegate to main function
    return create_resume_zip(
        resume_files,
        zip_filename=zip_filename,
        compression_level=compression_level,
    )


def validate_zip_size(
    zip_size_bytes: int,
    max_size_mb: int = 100,
) -> Dict[str, Union[bool, str, int]]:
    """
    Validate that a ZIP file size is within acceptable limits.

    Args:
        zip_size_bytes: Size of the ZIP file in bytes
        max_size_mb: Maximum allowed size in megabytes (default: 100MB)

    Returns:
        Dictionary containing:
            - is_valid: Whether ZIP size is valid
            - size_mb: ZIP size in megabytes
            - error: Error message if invalid (None if valid)

    Examples:
        >>> result = validate_zip_size(50 * 1024 * 1024, max_size_mb=100)
        >>> if result["is_valid"]:
        ...     print("ZIP size is acceptable")
        ... else:
        ...     print(f"ZIP too large: {result['size_mb']:.2f}MB")
    """
    size_mb = zip_size_bytes / (1024 * 1024)

    if zip_size_bytes > max_size_mb * 1024 * 1024:
        return {
            "is_valid": False,
            "size_mb": size_mb,
            "error": f"ZIP file size {size_mb:.2f}MB exceeds maximum {max_size_mb}MB",
        }

    return {
        "is_valid": True,
        "size_mb": size_mb,
        "error": None,
    }
