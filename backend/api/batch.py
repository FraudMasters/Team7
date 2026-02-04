"""
Batch resume upload and processing endpoints.

This module provides endpoints for uploading multiple resume files at once,
tracking batch processing status, and retrieving batch results.
"""
import logging
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models.batch_job import BatchJob, BatchJobStatus
from models.resume import Resume, ResumeStatus
from tasks.analysis_task import batch_analyze_resumes
from tasks.email_task import send_batch_completion_notification
from celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# Directory for storing uploaded resumes
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def extract_zip_files(
    zip_bytes: bytes,
    *,
    max_file_size_mb: int = 100,
    max_files: int = 100,
    allowed_extensions: Optional[List[str]] = None,
) -> Dict[str, Optional[Union[List[Dict[str, Union[str, int, bytes]]], str, int]]]:
    """
    Extract and validate files from a ZIP archive.

    This function extracts files from a ZIP archive provided as bytes, with validation
    for file count, size limits, and allowed extensions. It includes security checks
    to prevent ZIP bomb attacks (path traversal and excessive compression).

    Args:
        zip_bytes: ZIP file content as bytes
        max_file_size_mb: Maximum allowed size of the ZIP file in megabytes (default: 100MB)
        max_files: Maximum number of files to extract from the ZIP (default: 100)
        allowed_extensions: List of allowed file extensions (e.g., [".pdf", ".docx"])
                         If None, all extensions are allowed

    Returns:
        Dictionary containing:
            - files: List of extracted file dictionaries with keys:
                - filename: Original filename from ZIP
                - extension: File extension (lowercase, with dot)
                - size: File size in bytes
                - content: File content as bytes
            - total_files: Total number of files found in ZIP
            - extracted_count: Number of successfully extracted files
            - error: Error message if extraction failed (None if successful)
            - skipped_count: Number of files skipped due to extension filter

    Examples:
        >>> with open("resumes.zip", "rb") as f:
        ...     zip_bytes = f.read()
        >>> result = extract_zip_files(zip_bytes, allowed_extensions=[".pdf", ".docx"])
        >>> if result["error"]:
        ...     print(f"Error: {result['error']}")
        ... else:
        ...     print(f"Extracted {result['extracted_count']} files")

    Security:
        - Protects against ZIP bomb attacks by checking for path traversal (..)
        - Validates uncompressed size to prevent denial of service
        - Limits number of extracted files to prevent resource exhaustion
    """
    # Set default allowed extensions if not provided
    if allowed_extensions is None:
        allowed_extensions = [".pdf", ".docx", ".doc"]

    # Validate input
    if not zip_bytes:
        logger.error("Empty ZIP bytes provided")
        return {
            "files": None,
            "total_files": 0,
            "extracted_count": 0,
            "skipped_count": 0,
            "error": "Empty ZIP bytes provided",
        }

    # Check ZIP file size
    zip_size_mb = len(zip_bytes) / (1024 * 1024)
    if zip_size_mb > max_file_size_mb:
        logger.error(f"ZIP file too large: {zip_size_mb:.2f}MB (max: {max_file_size_mb}MB)")
        return {
            "files": None,
            "total_files": 0,
            "extracted_count": 0,
            "skipped_count": 0,
            "error": f"ZIP file too large: {zip_size_mb:.2f}MB (max: {max_file_size_mb}MB)",
        }

    try:
        # Open ZIP file from bytes
        zip_file = BytesIO(zip_bytes)

        with zipfile.ZipFile(zip_file, mode='r') as zip_ref:
            # Validate ZIP structure
            file_list = zip_ref.namelist()
            total_files = len([f for f in file_list if not f.endswith('/')])

            if total_files == 0:
                logger.error("ZIP file contains no files")
                return {
                    "files": None,
                    "total_files": 0,
                    "extracted_count": 0,
                    "skipped_count": 0,
                    "error": "ZIP file contains no files",
                }

            if total_files > max_files:
                logger.error(f"ZIP contains too many files: {total_files} (max: {max_files})")
                return {
                    "files": None,
                    "total_files": total_files,
                    "extracted_count": 0,
                    "skipped_count": 0,
                    "error": f"ZIP contains too many files: {total_files} (max: {max_files})",
                }

            logger.info(f"Extracting files from ZIP: {total_files} files found, {zip_size_mb:.2f}MB")

            extracted_files = []
            skipped_count = 0

            for file_path in file_list:
                # Skip directories
                if file_path.endswith('/'):
                    continue

                # Security check: Prevent path traversal attacks
                if '..' in file_path or file_path.startswith('/'):
                    logger.warning(f"Skipping potentially malicious file: {file_path}")
                    skipped_count += 1
                    continue

                # Get filename without path
                filename = Path(file_path).name

                # Skip if no filename (e.g., just a directory entry)
                if not filename:
                    continue

                # Check file extension
                file_extension = Path(file_path).suffix.lower()
                if allowed_extensions and file_extension not in allowed_extensions:
                    logger.debug(f"Skipping file with disallowed extension: {file_path} ({file_extension})")
                    skipped_count += 1
                    continue

                try:
                    # Get file info
                    info = zip_ref.getinfo(file_path)

                    # Security check: Validate uncompressed size to prevent ZIP bomb
                    uncompressed_size = info.file_size
                    if uncompressed_size > max_file_size_mb * 1024 * 1024:
                        logger.warning(f"Skipping file too large after extraction: {file_path} ({uncompressed_size / 1024 / 1024:.2f}MB)")
                        skipped_count += 1
                        continue

                    # Extract file content
                    with zip_ref.open(file_path) as extracted_file:
                        file_content = extracted_file.read()

                    extracted_files.append({
                        "filename": filename,
                        "extension": file_extension,
                        "size": uncompressed_size,
                        "content": file_content,
                    })

                    logger.debug(f"Extracted: {filename} ({uncompressed_size} bytes)")

                except (zipfile.BadZipFile, KeyError) as e:
                    logger.warning(f"Failed to extract file {file_path}: {e}")
                    skipped_count += 1
                    continue

            if not extracted_files:
                logger.error("No valid files extracted from ZIP")
                return {
                    "files": None,
                    "total_files": total_files,
                    "extracted_count": 0,
                    "skipped_count": skipped_count,
                    "error": "No valid files extracted from ZIP (all files may have disallowed extensions or failed extraction)",
                }

            logger.info(f"Successfully extracted {len(extracted_files)} files from ZIP (skipped: {skipped_count})")

            return {
                "files": extracted_files,
                "total_files": total_files,
                "extracted_count": len(extracted_files),
                "skipped_count": skipped_count,
                "error": None,
            }

    except zipfile.BadZipFile as e:
        logger.error(f"Invalid ZIP file: {e}")
        return {
            "files": None,
            "total_files": 0,
            "extracted_count": 0,
            "skipped_count": 0,
            "error": f"Invalid ZIP file: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Failed to extract ZIP files: {e}")
        return {
            "files": None,
            "total_files": 0,
            "extracted_count": 0,
            "skipped_count": 0,
            "error": f"ZIP extraction failed: {str(e)}",
        }


def _extract_locale(request: Optional[Request]) -> str:
    """Extract Accept-Language header from request."""
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


def validate_file_type(filename: str, content_type: str, locale: str = "en") -> None:
    """Validate that the file type is allowed."""
    file_ext = Path(filename).suffix.lower()
    if file_ext not in settings.allowed_file_types:
        allowed = ", ".join(settings.allowed_file_types)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid file type: {file_ext}. Allowed types: {allowed}",
        )


def validate_file_size(file_size: int, locale: str = "en") -> None:
    """Validate that the file size is within allowed limits."""
    max_size = settings.max_upload_size_bytes
    if file_size > max_size:
        max_mb = settings.max_upload_size_mb
        size_mb = file_size / 1024 / 1024
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {size_mb:.1f}MB. Maximum allowed: {max_mb}MB",
        )


def validate_zip_file_size(file_size: int, locale: str = "en") -> None:
    """Validate that the ZIP file size is within allowed limits.

    ZIP files can contain multiple resumes, so they have a higher size limit
    than individual file uploads.

    Args:
        file_size: Size of the ZIP file in bytes
        locale: Locale for error messages (not currently used)

    Raises:
        HTTPException(413): If ZIP file size exceeds maximum allowed
    """
    # ZIP files have a higher limit since they contain multiple files
    # Default to 100MB which matches the extract_zip_files default
    max_zip_size_mb = 100
    max_zip_size = max_zip_size_mb * 1024 * 1024

    if file_size > max_zip_size:
        size_mb = file_size / 1024 / 1024
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"ZIP file too large: {size_mb:.1f}MB. Maximum allowed: {max_zip_size_mb}MB",
        )


# Pydantic models for requests/responses
class BatchUploadRequest(BaseModel):
    """Request model for batch upload with optional notification email."""

    notification_email: Optional[str] = Field(None, description="Email to send notification to when complete")
    analyze: bool = Field(True, description="Whether to analyze resumes after upload")


class BatchUploadResponse(BaseModel):
    """Response model for batch upload initiation."""

    batch_id: str = Field(..., description="Unique identifier for the batch job")
    total_files: int = Field(..., description="Number of files in the batch")
    status: str = Field(..., description="Initial status of the batch job")
    message: str = Field(..., description="Success message")


class BatchStatusResponse(BaseModel):
    """Response model for batch status query."""

    batch_id: str = Field(..., description="Unique identifier for the batch job")
    status: str = Field(..., description="Current status of the batch job")
    total_files: int = Field(..., description="Total number of files in the batch")
    processed_files: int = Field(..., description="Number of files processed")
    failed_files: int = Field(..., description="Number of files that failed")
    progress_percentage: int = Field(..., description="Progress percentage")
    created_at: Optional[str] = Field(None, description="Timestamp when batch was created")
    completed_at: Optional[str] = Field(None, description="Timestamp when batch completed")
    error_message: Optional[str] = Field(None, description="Error message if batch failed")


class BatchFileItem(BaseModel):
    """Response model for a single file in batch results."""

    resume_id: str = Field(..., description="Resume identifier")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Processing status")
    error: Optional[str] = Field(None, description="Error message if failed")


class BatchResultsResponse(BaseModel):
    """Response model for batch results."""

    batch_id: str = Field(..., description="Unique identifier for the batch job")
    status: str = Field(..., description="Final status of the batch job")
    total_files: int = Field(..., description="Total number of files")
    successful: int = Field(..., description="Number of successfully processed files")
    failed: int = Field(..., description="Number of failed files")
    files: list[BatchFileItem] = Field(..., description="List of files with their status")


@router.post(
    "/upload",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Batch"],
)
async def upload_batch(
    request: Request,
    files: list[UploadFile] = File(...),
    notification_email: Optional[str] = Form(None),
    analyze: bool = Form(True),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Upload multiple resume files for batch processing.

    This endpoint accepts multiple resume files (PDF, DOCX, or ZIP archives),
    validates each file, stores them, creates database records, and initiates
    batch processing. ZIP files are automatically extracted and their contents
    are processed individually.

    Args:
        request: FastAPI request object
        files: List of uploaded resume files or ZIP archives
        notification_email: Optional email for completion notification
        analyze: Whether to analyze resumes after upload
        db: Database session

    Returns:
        JSON response with batch ID and initial status

    Raises:
        HTTPException(415): If file type is not supported
        HTTPException(413): If file size exceeds maximum
        HTTPException(500): If file storage or database operation fails
    """
    locale = _extract_locale(request)

    # Validate content type - endpoint expects multipart/form-data
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("multipart/form-data"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Content-Type must be multipart/form-data",
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )

    if len(files) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 files allowed per batch",
        )

    logger.info(f"Received batch upload request with {len(files)} files, analyze={analyze}, notification_email={notification_email}")

    try:
        # Create batch job record
        batch_id = uuid4()
        batch_job = BatchJob(
            id=batch_id,
            total_files=len(files),
            processed_files=0,
            failed_files=0,
            status=BatchJobStatus.pending,
            notification_email=notification_email,
        )
        db.add(batch_job)

        # Store files and create resume records
        resume_ids = []
        failed_uploads = []
        zip_files_processed = 0

        for file in files:
            try:
                # Read file content
                file_content = await file.read()
                file_size = len(file_content)
                file_filename = file.filename or "unknown"

                # Check if file is a ZIP archive
                file_extension = Path(file_filename).suffix.lower()
                is_zip_file = file_extension == ".zip"

                if is_zip_file:
                    # Validate ZIP file size before extraction
                    validate_zip_file_size(file_size, locale)

                    # Extract files from ZIP archive
                    logger.info(f"Detected ZIP file: {file_filename}, extracting...")

                    zip_result = extract_zip_files(
                        file_content,
                        max_file_size_mb=100,
                        max_files=100,
                        allowed_extensions=[".pdf", ".docx", ".doc"],
                    )

                    if zip_result["error"]:
                        logger.error(f"Failed to extract ZIP file {file_filename}: {zip_result['error']}")
                        failed_uploads.append(f"{file_filename} (ZIP extraction failed: {zip_result['error']})")
                        continue

                    extracted_files = zip_result["files"]
                    zip_files_processed += 1

                    logger.info(f"Extracted {zip_result['extracted_count']} files from {file_filename} (skipped: {zip_result['skipped_count']})")

                    # Process each extracted file
                    for extracted_file in extracted_files:
                        try:
                            # Generate resume ID and save file
                            resume_id = uuid4()
                            ext = extracted_file["extension"]
                            stored_filename = f"{resume_id}{ext}"
                            file_path = UPLOAD_DIR / stored_filename

                            with open(file_path, "wb") as f:
                                f.write(extracted_file["content"])

                            # Create resume record
                            resume = Resume(
                                id=resume_id,
                                filename=extracted_file["filename"],
                                file_path=str(file_path),
                                content_type=f"application/{ext[1:]}",  # Remove dot for content type
                                status=ResumeStatus.PENDING,
                            )
                            db.add(resume)
                            resume_ids.append(str(resume_id))

                            logger.info(f"Stored extracted file: {extracted_file['filename']} -> {resume_id}")

                        except Exception as e:
                            failed_uploads.append(extracted_file["filename"])
                            logger.error(f"Failed to store extracted file {extracted_file['filename']}: {e}")
                else:
                    # Process regular (non-ZIP) file
                    # Validate
                    validate_file_type(file_filename, file.content_type or "application/octet-stream", locale)
                    validate_file_size(file_size, locale)

                    # Generate resume ID and save file
                    resume_id = uuid4()
                    safe_filename = Path(file_filename).name
                    file_extension = Path(safe_filename).suffix
                    stored_filename = f"{resume_id}{file_extension}"
                    file_path = UPLOAD_DIR / stored_filename

                    with open(file_path, "wb") as f:
                        f.write(file_content)

                    # Create resume record
                    resume = Resume(
                        id=resume_id,
                        filename=file_filename,
                        file_path=str(file_path),
                        content_type=file.content_type or "application/octet-stream",
                        status=ResumeStatus.PENDING,
                    )
                    db.add(resume)
                    resume_ids.append(str(resume_id))

                    logger.info(f"Stored file: {file_filename} -> {resume_id}")

            except HTTPException:
                failed_uploads.append(file.filename)
                logger.warning(f"Failed to validate file: {file.filename}")
            except Exception as e:
                failed_uploads.append(file.filename)
                logger.error(f"Failed to store file {file.filename}: {e}")

        await db.commit()

        # Update batch job with actual counts
        batch_job.total_files = len(resume_ids)
        batch_job.failed_files = len(failed_uploads)

        if failed_uploads:
            batch_job.status = BatchJobStatus.failed
            batch_job.error_message = f"Failed to upload {len(failed_uploads)} files: {', '.join(failed_uploads[:5])}"
            await db.commit()

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "batch_id": str(batch_id),
                    "total_files": len(resume_ids),
                    "status": BatchJobStatus.failed.value,
                    "message": f"Batch created with errors. {len(failed_uploads)} files failed to upload.",
                }
            )

        # Initiate batch analysis if requested
        if analyze and resume_ids:
            logger.info(f"Initiating batch analysis for {len(resume_ids)} resumes")
            batch_job.status = BatchJobStatus.processing
            await db.commit()

            # Trigger Celery task
            try:
                celery_task = batch_analyze_resumes.delay(resume_ids)
                logger.info(f"Celery task dispatched: {celery_task.id}")

                # Store Celery task ID
                batch_job.celery_task_id = celery_task.id
                await db.commit()

                logger.info(f"Started Celery task {celery_task.id} for batch {batch_id}")
            except Exception as task_error:
                logger.error(f"Error dispatching Celery task: {task_error}", exc_info=True)
                raise
        else:
            logger.info(f"Batch analysis not requested. analyze={analyze}, resume_ids count={len(resume_ids) if resume_ids else 0}")
            await db.commit()

        # Build success message with ZIP processing info
        message_parts = [f"Batch upload started with {len(resume_ids)} files"]
        if zip_files_processed > 0:
            message_parts.append(f"from {zip_files_processed} ZIP archive{'s' if zip_files_processed > 1 else ''}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "batch_id": str(batch_id),
                "total_files": len(resume_ids),
                "status": batch_job.status.value,
                "message": " ".join(message_parts),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch upload: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch upload failed: {str(e)}",
        ) from e


@router.get(
    "/{batch_id}",
    response_model=BatchStatusResponse,
    tags=["Batch"],
)
async def get_batch_status(
    request: Request,
    batch_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get the status of a batch job.

    Args:
        request: FastAPI request object
        batch_id: Unique identifier of the batch job
        db: Database session

    Returns:
        JSON response with current batch status

    Raises:
        HTTPException(404): If batch job not found
    """
    try:
        batch_uuid = UUID(batch_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid batch ID format",
        )

    query = select(BatchJob).where(BatchJob.id == batch_uuid)
    result = await db.execute(query)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found",
        )

    # Check Celery task status if processing
    if batch.celery_task_id and batch.status == BatchJobStatus.processing:
        # Store previous status to detect transition
        previous_status = batch.status

        try:
            celery_result = celery_app.AsyncResult(batch.celery_task_id)
            if celery_result.state == "SUCCESS":
                batch.status = BatchJobStatus.completed
                batch.processed_files = batch.total_files
                batch.failed_files = 0
                # Set completion time
                from datetime import datetime, timezone
                batch.completed_at = datetime.now(timezone.utc)
            elif celery_result.state == "FAILURE":
                batch.status = BatchJobStatus.failed
                batch.error_message = "Celery task failed"
                from datetime import datetime, timezone
                batch.completed_at = datetime.now(timezone.utc)
            await db.commit()

            # Send email notification if status changed and notification email is provided
            if batch.status != previous_status and batch.notification_email:
                try:
                    from datetime import datetime, timezone

                    # Prepare batch results for notification
                    batch_results = {
                        "operation_type": "upload",
                        "status": batch.status.value,
                        "total_items": batch.total_files,
                        "successful_count": batch.processed_files,
                        "failed_count": batch.failed_files,
                        "started_at": batch.created_at.isoformat() if batch.created_at else None,
                        "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
                        "errors": [batch.error_message] if batch.error_message else [],
                        "metadata": {
                            "batch_id": str(batch.id),
                            "celery_task_id": batch.celery_task_id,
                        }
                    }

                    # Trigger email notification asynchronously
                    send_batch_completion_notification.delay(
                        batch_id=str(batch.id),
                        recipient_email=batch.notification_email,
                        batch_results=batch_results
                    )

                    logger.info(
                        f"Batch completion notification dispatched for batch {batch.id} "
                        f"to {batch.notification_email}"
                    )
                except Exception as email_error:
                    # Don't fail the request if email sending fails
                    logger.error(
                        f"Failed to dispatch batch completion notification for batch {batch.id}: {email_error}",
                        exc_info=True
                    )

        except Exception as e:
            logger.warning(f"Failed to check Celery task status: {e}")

    progress_percentage = 0
    if batch.total_files > 0:
        progress_percentage = int((batch.processed_files / batch.total_files) * 100)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "batch_id": str(batch.id),
            "status": batch.status.value,
            "total_files": batch.total_files,
            "processed_files": batch.processed_files,
            "failed_files": batch.failed_files,
            "progress_percentage": progress_percentage,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "error_message": batch.error_message,
        }
    )


@router.get(
    "/{batch_id}/results",
    response_model=BatchResultsResponse,
    tags=["Batch"],
)
async def get_batch_results(
    request: Request,
    batch_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get the results of a completed batch job.

    Args:
        request: FastAPI request object
        batch_id: Unique identifier of the batch job
        db: Database session

    Returns:
        JSON response with batch results including individual file status

    Raises:
        HTTPException(404): If batch job not found
    """
    try:
        batch_uuid = UUID(batch_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid batch ID format",
        )

    query = select(BatchJob).where(BatchJob.id == batch_uuid)
    result = await db.execute(query)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found",
        )

    # Get all resumes for this batch (by creation time and batch reference)
    # For simplicity, we'll get recent resumes
    from datetime import datetime, timedelta
    from models.resume_analysis import ResumeAnalysis

    # Get resumes created around the batch creation time
    time_threshold = batch.created_at + timedelta(seconds=5)
    resume_query = select(Resume).where(
        Resume.created_at <= time_threshold
    ).order_by(Resume.created_at.desc()).limit(batch.total_files)

    resume_result = await db.execute(resume_query)
    resumes = resume_result.scalars().all()

    files = []
    successful = 0
    failed = 0

    for resume in resumes:
        # Check if analysis exists
        analysis_query = select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume.id)
        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()

        status = "completed" if analysis else resume.status.value
        if status == "completed":
            successful += 1
        else:
            failed += 1

        files.append({
            "resume_id": str(resume.id),
            "filename": resume.filename,
            "status": status,
            "error": None,
        })

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "batch_id": str(batch.id),
            "status": batch.status.value,
            "total_files": batch.total_files,
            "successful": successful,
            "failed": failed,
            "files": files,
        }
    )


@router.get(
    "/",
    tags=["Batch"],
)
async def list_batches(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List all batch jobs.

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of batch jobs
    """
    try:
        query = select(BatchJob).order_by(BatchJob.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        batches = result.scalars().all()

        batches_list = []
        for batch in batches:
            progress_percentage = 0
            if batch.total_files > 0:
                progress_percentage = int((batch.processed_files / batch.total_files) * 100)

            batches_list.append({
                "batch_id": str(batch.id),
                "status": batch.status.value,
                "total_files": batch.total_files,
                "processed_files": batch.processed_files,
                "failed_files": batch.failed_files,
                "progress_percentage": progress_percentage,
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"batches": batches_list, "total": len(batches_list)},
        )

    except Exception as e:
        logger.error(f"Error listing batches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list batches: {str(e)}",
        ) from e
