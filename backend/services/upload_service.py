"""
Unified upload service module for handling file uploads.

This module provides a centralized service for handling single and batch file uploads,
including validation, storage, and database record creation. It consolidates common
upload logic that was previously duplicated across multiple endpoints.

Key features:
- File type validation (PDF, DOCX)
- File size validation
- Magic number verification to prevent malicious uploads
- Filename sanitization to prevent path traversal attacks
- Locale-aware error messages
- Support for both single and batch uploads
"""
import logging
from pathlib import Path
from typing import Optional, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from i18n.backend_translations import get_error_message, get_success_message
from models.resume import Resume, ResumeStatus
from utils.file_validation import validate_magic_number, validate_file_structure
from utils.sanitization import get_safe_stored_filename, sanitize_filename

logger = logging.getLogger(__name__)
settings = get_settings()


# Directory for storing uploaded files (from centralized config)
UPLOAD_DIR = settings.upload_dir
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class UploadValidationError(Exception):
    """Custom exception for upload validation errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UnifiedUploadService:
    """
    Unified service for handling file uploads.

    This service provides a centralized interface for uploading and validating files,
    with support for both single and batch upload operations. It handles all aspects
    of the upload process including validation, storage, and database record creation.

    Examples:
        >>> service = UnifiedUploadService()
        >>> # Single file upload
        >>> result = await service.upload_file(file, db, locale, request)
        >>> print(result["id"])
        >>>
        >>> # Batch file upload
        >>> results = await service.upload_batch(files, db, locale, request)
        >>> print(len(results["successful"]))
    """

    def __init__(self):
        """Initialize the upload service with default settings."""
        self.max_files_per_batch = 100
        self._allowed_content_types: dict[str, list[str]] = {
            ".pdf": ["application/pdf"],
            ".docx": [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
            ],
        }

    def extract_locale(self, request: Optional[Request]) -> str:
        """
        Extract Accept-Language header from request.

        Args:
            request: The incoming FastAPI request (optional)

        Returns:
            Language code (e.g., 'en', 'ru')
        """
        if request is None:
            return "en"
        accept_language = request.headers.get("Accept-Language", "en")
        lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
        return lang_code

    def validate_file_type(self, filename: str, content_type: str, locale: str = "en") -> None:
        """
        Validate that the file type is allowed.

        Args:
            filename: Name of the uploaded file
            content_type: MIME type of the file
            locale: Language code for translated error messages

        Raises:
            UploadValidationError: If file type is not allowed
        """
        file_ext = Path(filename).suffix.lower()
        if file_ext not in settings.allowed_file_types:
            allowed = ", ".join(settings.allowed_file_types)
            error_msg = get_error_message("invalid_file_type", locale, file_ext=file_ext, allowed=allowed)
            raise UploadValidationError(
                error_msg,
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )

        # Check content type for additional validation
        if file_ext in self._allowed_content_types:
            if content_type not in self._allowed_content_types[file_ext]:
                logger.warning(
                    f"Content type mismatch for {filename}: {content_type} not in "
                    f"{self._allowed_content_types[file_ext]}"
                )

    def validate_file_size(self, file_size: int, locale: str = "en") -> None:
        """
        Validate that the file size is within allowed limits.

        Args:
            file_size: Size of the file in bytes
            locale: Language code for translated error messages

        Raises:
            UploadValidationError: If file size exceeds maximum allowed
        """
        max_size = settings.max_upload_size_bytes
        if file_size > max_size:
            max_mb = settings.max_upload_size_mb
            size_mb = file_size / 1024 / 1024
            error_msg = get_error_message("file_too_large", locale, size=size_mb, max_mb=max_mb)
            raise UploadValidationError(
                error_msg,
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

    def validate_file_content(
        self,
        file_content: bytes,
        filename: str,
        locale: str = "en"
    ) -> None:
        """
        Validate file content using magic number and structure checks.

        Args:
            file_content: Raw file content as bytes
            filename: Original filename (used to extract extension)
            locale: Language code for translated error messages

        Raises:
            UploadValidationError: If file content is invalid or suspicious
        """
        file_extension = Path(filename).suffix

        # Validate magic number (file signature) to prevent malicious file uploads
        is_valid, error_msg = validate_magic_number(file_content, file_extension, locale)
        if not is_valid:
            raise UploadValidationError(
                error_msg,
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )

        # Validate file structure for additional integrity checks
        is_valid, error_msg = validate_file_structure(file_content, file_extension, locale)
        if not is_valid:
            logger.warning(f"File structure validation warning for {filename}: {error_msg}")
            # Structure validation warnings are logged but don't block upload
            # as they may be overly conservative for some valid files

    async def read_and_validate_file(
        self,
        file: UploadFile,
        locale: str = "en"
    ) -> Tuple[bytes, str]:
        """
        Read file content and perform all validations.

        Args:
            file: The uploaded file object
            locale: Language code for translated error messages

        Returns:
            Tuple of (file_content, filename)

        Raises:
            UploadValidationError: If any validation fails
        """
        filename = file.filename or "unknown"
        content_type = file.content_type or "application/octet-stream"

        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        logger.info(f"Read file: {filename} ({file_size} bytes)")

        # Validate file type
        self.validate_file_type(filename, content_type, locale)

        # Validate file size
        self.validate_file_size(file_size, locale)

        # Validate file content (magic number and structure)
        self.validate_file_content(file_content, filename, locale)

        return file_content, filename

    def save_file_to_disk(
        self,
        file_content: bytes,
        filename: str,
        file_id: str
    ) -> Path:
        """
        Save file content to disk with a safe filename.

        Args:
            file_content: Raw file content as bytes
            filename: Original filename (used for extension)
            file_id: Unique identifier for the file (typically a UUID)

        Returns:
            Path to the saved file

        Raises:
            IOError: If file cannot be written to disk
        """
        # Generate safe stored filename
        stored_filename = get_safe_stored_filename(
            filename,
            file_id,
            preserve_extension=True
        )
        file_path = UPLOAD_DIR / stored_filename

        # Save file to disk
        logger.info(f"Saving file to: {file_path}")
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            logger.info(f"File saved successfully: {file_path}")
            return file_path
        except IOError as e:
            logger.error(f"Failed to save file to {file_path}: {e}")
            raise

    async def create_resume_record(
        self,
        db: AsyncSession,
        resume_id: UUID,
        filename: str,
        file_path: Path,
        content_type: str
    ) -> Resume:
        """
        Create a resume database record.

        Args:
            db: Database session
            resume_id: Unique identifier for the resume
            filename: Sanitized display filename
            file_path: Path to the stored file
            content_type: MIME type of the file

        Returns:
            Created Resume object
        """
        resume = Resume(
            id=resume_id,
            filename=filename,
            file_path=str(file_path),
            content_type=content_type,
            status=ResumeStatus.PENDING,
        )

        db.add(resume)
        await db.flush()  # Flush to get the ID but don't commit yet

        logger.info(f"Resume record created: {resume_id}")
        return resume

    async def upload_file(
        self,
        file: UploadFile,
        db: AsyncSession,
        locale: str = "en",
        request: Optional[Request] = None
    ) -> dict:
        """
        Upload a single file with full validation and database record creation.

        This method handles the complete upload workflow:
        1. Read and validate the file
        2. Save to disk
        3. Create database record
        4. Return success response

        Args:
            file: The uploaded file object
            db: Database session
            locale: Language code for translated error messages
            request: Optional request object for context

        Returns:
            Dictionary with upload result:
                - id: Resume ID as string
                - filename: Sanitized filename
                - status: Resume status
                - message: Success message

        Raises:
            UploadValidationError: If validation fails
            HTTPException: If database or file system operations fail

        Examples:
            >>> service = UnifiedUploadService()
            >>> result = await service.upload_file(file, db, "en", request)
            >>> print(result["id"])
            '123e4567-e89b-12d3-a456-426614174000'
        """
        try:
            # Read and validate file
            file_content, original_filename = await self.read_and_validate_file(file, locale)

            # Generate UUID for the resume
            resume_id = uuid4()

            # Save file to disk
            file_path = self.save_file_to_disk(file_content, original_filename, str(resume_id))

            # Sanitize filename for display
            display_filename = sanitize_filename(original_filename, preserve_extension=True)
            content_type = file.content_type or "application/octet-stream"

            # Create database record
            await self.create_resume_record(
                db,
                resume_id,
                display_filename,
                file_path,
                content_type
            )

            await db.commit()
            await db.refresh(resume_id)

            # Get translated success message
            success_message = get_success_message("file_uploaded", locale)

            logger.info(f"File uploaded successfully: {resume_id}")

            return {
                "id": str(resume_id),
                "filename": display_filename,
                "status": ResumeStatus.PENDING.value,
                "message": success_message,
            }

        except UploadValidationError as e:
            # Re-raise validation errors with appropriate status code
            raise HTTPException(
                status_code=e.status_code,
                detail=e.message,
            ) from e
        except Exception as e:
            logger.error(f"Error uploading file: {e}", exc_info=True)
            await db.rollback()
            error_msg = get_error_message("file_upload_failed", locale)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            ) from e

    async def upload_batch(
        self,
        files: list[UploadFile],
        db: AsyncSession,
        locale: str = "en",
        request: Optional[Request] = None
    ) -> dict:
        """
        Upload multiple files with validation and database record creation.

        This method handles batch upload workflow:
        1. Validate batch size limits
        2. Process each file (validate, save, create record)
        3. Return summary with successful and failed uploads

        Args:
            files: List of uploaded file objects
            db: Database session
            locale: Language code for translated error messages
            request: Optional request object for context

        Returns:
            Dictionary with batch upload result:
                - successful: List of successfully uploaded resume info
                - failed: List of failed upload info with errors
                - total_files: Total number of files processed
                - success_count: Number of successful uploads
                - failure_count: Number of failed uploads

        Raises:
            HTTPException: If batch size exceeds limit

        Examples:
            >>> service = UnifiedUploadService()
            >>> result = await service.upload_batch(files, db, "en", request)
            >>> print(f"Uploaded {result['success_count']} files")
            Uploaded 5
        """
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided",
            )

        if len(files) > self.max_files_per_batch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {self.max_files_per_batch} files allowed per batch",
            )

        logger.info(f"Processing batch upload with {len(files)} files")

        successful = []
        failed = []

        for file in files:
            try:
                # Read and validate file
                file_content, original_filename = await self.read_and_validate_file(file, locale)

                # Generate UUID
                resume_id = uuid4()

                # Save file to disk
                file_path = self.save_file_to_disk(file_content, original_filename, str(resume_id))

                # Sanitize filename for display
                display_filename = sanitize_filename(original_filename, preserve_extension=True)
                content_type = file.content_type or "application/octet-stream"

                # Create database record
                await self.create_resume_record(
                    db,
                    resume_id,
                    display_filename,
                    file_path,
                    content_type
                )

                successful.append({
                    "id": str(resume_id),
                    "filename": display_filename,
                    "status": ResumeStatus.PENDING.value,
                })

                logger.info(f"File uploaded in batch: {resume_id}")

            except UploadValidationError as e:
                failed.append({
                    "filename": file.filename or "unknown",
                    "error": e.message,
                })
                logger.warning(f"File validation failed in batch: {file.filename} - {e.message}")
            except Exception as e:
                failed.append({
                    "filename": file.filename or "unknown",
                    "error": str(e),
                })
                logger.error(f"File upload failed in batch: {file.filename} - {e}")

        # Commit all successful uploads
        try:
            await db.commit()
        except Exception as e:
            logger.error(f"Database commit failed during batch upload: {e}", exc_info=True)
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save batch upload",
            ) from e

        return {
            "successful": successful,
            "failed": failed,
            "total_files": len(files),
            "success_count": len(successful),
            "failure_count": len(failed),
        }

    async def validate_for_batch(
        self,
        files: list[UploadFile],
        locale: str = "en"
    ) -> Tuple[list[UploadFile], list[dict]]:
        """
        Pre-validate files for batch upload without saving.

        This method validates all files in a batch without saving them to disk
        or creating database records. Useful for pre-flight validation.

        Args:
            files: List of uploaded file objects
            locale: Language code for translated error messages

        Returns:
            Tuple of (valid_files, validation_errors):
                - valid_files: List of files that passed validation
                - validation_errors: List of error info for failed files
        """
        if not files:
            return [], []

        if len(files) > self.max_files_per_batch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {self.max_files_per_batch} files allowed per batch",
            )

        valid_files = []
        validation_errors = []

        for file in files:
            try:
                # Read and validate file content
                file_content, original_filename = await self.read_and_validate_file(file, locale)
                valid_files.append(file)
            except UploadValidationError as e:
                validation_errors.append({
                    "filename": file.filename or "unknown",
                    "error": e.message,
                })
            except Exception as e:
                validation_errors.append({
                    "filename": file.filename or "unknown",
                    "error": str(e),
                })

        return valid_files, validation_errors


# Singleton instance for convenient use
_upload_service_instance: Optional[UnifiedUploadService] = None


def get_upload_service() -> UnifiedUploadService:
    """
    Get the singleton instance of the upload service.

    Returns:
        The shared UnifiedUploadService instance

    Examples:
        >>> service = get_upload_service()
        >>> result = await service.upload_file(file, db, "en")
    """
    global _upload_service_instance
    if _upload_service_instance is None:
        _upload_service_instance = UnifiedUploadService()
    return _upload_service_instance
