"""
Batch resume upload and processing endpoints.

This module provides endpoints for uploading multiple resume files at once,
tracking batch processing status, and retrieving batch results.

Supports:
- Direct file uploads (PDF, DOCX)
- ZIP archive uploads with automatic extraction
"""
import logging
from pathlib import Path
from typing import Optional
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
from celery_app import celery_app
from utils.zip_extractor import extract_resumes_from_zip
from utils.duplicate_detector import (
    detect_duplicate,
    record_duplicate,
    DuplicateMatch,
)
from middleware.organization_context import get_organization_context

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# Directory for storing uploaded resumes (from centralized config)
UPLOAD_DIR = settings.upload_dir
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _extract_locale(request: Optional[Request]) -> str:
    """Extract Accept-Language header from request."""
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


def validate_file_type(filename: str, content_type: str, locale: str = "en", allow_zip: bool = False) -> None:
    """
    Validate that the file type is allowed.

    Args:
        filename: Name of the uploaded file
        content_type: MIME type of the file
        locale: Language code for error messages
        allow_zip: If True, also allow .zip files for batch upload

    Raises:
        HTTPException: If file type is not allowed
    """
    file_ext = Path(filename).suffix.lower()
    allowed_types = list(settings.allowed_file_types)
    if allow_zip and ".zip" not in allowed_types:
        allowed_types.append(".zip")

    if file_ext not in allowed_types:
        allowed = ", ".join(allowed_types)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid file type: {file_ext}. Allowed types: {allowed}",
        )


def is_zip_file(filename: str) -> bool:
    """Check if the file is a ZIP archive based on extension."""
    return Path(filename).suffix.lower() == ".zip"


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


# Pydantic models for requests/responses
class BatchUploadRequest(BaseModel):
    """Request model for batch upload with optional notification email."""

    notification_email: Optional[str] = Field(None, description="Email to send notification to when complete")
    analyze: bool = Field(True, description="Whether to analyze resumes after upload")


class DuplicateInfo(BaseModel):
    """Response model for duplicate detection information."""

    resume_id: str = Field(..., description="ID of the duplicate resume")
    filename: str = Field(..., description="Filename of the duplicate")
    original_resume_id: str = Field(..., description="ID of the original resume")
    match_type: str = Field(..., description="Type of match (exact or fuzzy)")
    similarity_score: float = Field(..., description="Similarity score (1.0 for exact matches)")


class BatchUploadResponse(BaseModel):
    """Response model for batch upload initiation."""

    batch_id: str = Field(..., description="Unique identifier for the batch job")
    total_files: int = Field(..., description="Number of files in the batch")
    status: str = Field(..., description="Initial status of the batch job")
    message: str = Field(..., description="Success message")
    duplicates_detected: int = Field(0, description="Number of duplicate files detected")
    duplicates: list[DuplicateInfo] = Field(default_factory=list, description="List of detected duplicates")


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
    is_duplicate: bool = Field(False, description="Whether this file is a duplicate")
    original_resume_id: Optional[str] = Field(None, description="Original resume ID if duplicate")


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

    This endpoint accepts multiple resume files (PDF or DOCX) or ZIP archives
    containing resume files. ZIP files are automatically extracted and each
    valid resume file within is processed.

    Args:
        request: FastAPI request object
        files: List of uploaded resume files (PDF, DOCX, or ZIP archives)
        notification_email: Optional email for completion notification
        analyze: Whether to analyze resumes after upload
        db: Database session

    Returns:
        JSON response with batch ID and initial status

    Raises:
        HTTPException(415): If file type is not supported
        HTTPException(413): If file size exceeds maximum
        HTTPException(500): If file storage or database operation fails

    ZIP Processing:
        - ZIP files are automatically extracted
        - Only PDF and DOCX files within the archive are processed
        - Nested directories are flattened
        - Maximum 100 files per batch (including extracted files)
        - Invalid files in ZIP are skipped with warnings
    """
    locale = _extract_locale(request)
    organization_id = get_organization_context(request)

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

    logger.info(f"Received batch upload request with {len(files)} files, analyze={analyze}, notification_email={notification_email}, organization_id={organization_id}")

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

        # Track detected duplicates
        detected_duplicates: list[dict] = []

        for file in files:
            try:
                # Read file content
                file_content = await file.read()
                file_size = len(file_content)

                # Validate file type (allow ZIP files for batch upload)
                validate_file_type(
                    file.filename or "unknown",
                    file.content_type or "application/octet-stream",
                    locale,
                    allow_zip=True
                )
                validate_file_size(file_size, locale)

                # Check if this is a ZIP file
                if is_zip_file(file.filename or "unknown"):
                    logger.info(f"Processing ZIP file: {file.filename}")
                    zip_files_processed += 1

                    # Extract resumes from ZIP
                    extraction_result = extract_resumes_from_zip(file_content)

                    if extraction_result.get("error"):
                        failed_uploads.append(f"{file.filename} (ZIP error: {extraction_result['error']})")
                        logger.warning(f"ZIP extraction failed for {file.filename}: {extraction_result['error']}")
                        continue

                    extracted_files = extraction_result.get("files", [])
                    logger.info(
                        f"Extracted {len(extracted_files)} files from {file.filename} "
                        f"({extraction_result.get('skipped_count', 0)} skipped)"
                    )

                    # Process each extracted file
                    for extracted_file in extracted_files:
                        try:
                            # Skip files that failed validation during extraction
                            if not extracted_file.get("valid", True):
                                validation_error = extracted_file.get("validation_error", "Unknown validation error")
                                failed_uploads.append(f"{extracted_file['filename']} (from {file.filename}): {validation_error}")
                                logger.warning(
                                    f"Skipped invalid file {extracted_file['filename']} from ZIP: {validation_error}"
                                )
                                continue

                            # Generate resume ID and save extracted file
                            resume_id = uuid4()
                            safe_filename = extracted_file["filename"]
                            file_extension = f".{extracted_file['extension']}"
                            stored_filename = f"{resume_id}{file_extension}"
                            file_path = UPLOAD_DIR / stored_filename

                            # Write extracted content to disk
                            with open(file_path, "wb") as f:
                                f.write(extracted_file["content"])

                            # Determine content type
                            content_type = "application/pdf" if file_extension == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

                            # Create resume record
                            resume = Resume(
                                id=resume_id,
                                filename=safe_filename,
                                file_path=str(file_path),
                                content_type=content_type,
                                status=ResumeStatus.PENDING,
                            )
                            db.add(resume)
                            resume_ids.append(str(resume_id))

                            logger.info(f"Stored extracted file: {safe_filename} (from {file.filename}) -> {resume_id}")

                            # Check for duplicates if organization context is available
                            if organization_id:
                                try:
                                    duplicate_match = await detect_duplicate(
                                        file_content=extracted_file["content"],
                                        organization_id=organization_id,
                                        db_session=db,
                                        current_resume_id=str(resume_id),
                                        batch_job_id=str(batch_id),
                                        check_file_system=True,
                                    )

                                    if duplicate_match.is_duplicate and duplicate_match.original_resume_id:
                                        # Record the duplicate
                                        await record_duplicate(
                                            original_resume_id=duplicate_match.original_resume_id,
                                            duplicate_resume_id=str(resume_id),
                                            content_hash=duplicate_match.content_hash,
                                            organization_id=organization_id,
                                            db_session=db,
                                            batch_job_id=str(batch_id),
                                            match_type=duplicate_match.match_type or "exact",
                                            similarity_score=duplicate_match.similarity_score,
                                        )

                                        detected_duplicates.append({
                                            "resume_id": str(resume_id),
                                            "filename": safe_filename,
                                            "original_resume_id": duplicate_match.original_resume_id,
                                            "match_type": duplicate_match.match_type or "exact",
                                            "similarity_score": duplicate_match.similarity_score,
                                        })

                                        logger.info(
                                            f"Duplicate detected: {safe_filename} matches "
                                            f"resume {duplicate_match.original_resume_id}"
                                        )
                                except Exception as dup_error:
                                    # Log but don't fail the upload on duplicate detection error
                                    logger.warning(f"Duplicate detection failed for {safe_filename}: {dup_error}")

                        except Exception as e:
                            failed_uploads.append(f"{extracted_file['filename']} (from {file.filename})")
                            logger.error(f"Failed to store extracted file {extracted_file['filename']}: {e}")

                else:
                    # Process as regular file (PDF or DOCX)
                    resume_id = uuid4()
                    safe_filename = Path(file.filename or "resume").name
                    file_extension = Path(safe_filename).suffix
                    stored_filename = f"{resume_id}{file_extension}"
                    file_path = UPLOAD_DIR / stored_filename

                    with open(file_path, "wb") as f:
                        f.write(file_content)

                    # Create resume record
                    resume = Resume(
                        id=resume_id,
                        filename=file.filename or "unknown",
                        file_path=str(file_path),
                        content_type=file.content_type or "application/octet-stream",
                        status=ResumeStatus.PENDING,
                    )
                    db.add(resume)
                    resume_ids.append(str(resume_id))

                    logger.info(f"Stored file: {file.filename} -> {resume_id}")

                    # Check for duplicates if organization context is available
                    if organization_id:
                        try:
                            duplicate_match = await detect_duplicate(
                                file_content=file_content,
                                organization_id=organization_id,
                                db_session=db,
                                current_resume_id=str(resume_id),
                                batch_job_id=str(batch_id),
                                check_file_system=True,
                            )

                            if duplicate_match.is_duplicate and duplicate_match.original_resume_id:
                                # Record the duplicate
                                await record_duplicate(
                                    original_resume_id=duplicate_match.original_resume_id,
                                    duplicate_resume_id=str(resume_id),
                                    content_hash=duplicate_match.content_hash,
                                    organization_id=organization_id,
                                    db_session=db,
                                    batch_job_id=str(batch_id),
                                    match_type=duplicate_match.match_type or "exact",
                                    similarity_score=duplicate_match.similarity_score,
                                )

                                detected_duplicates.append({
                                    "resume_id": str(resume_id),
                                    "filename": file.filename or "unknown",
                                    "original_resume_id": duplicate_match.original_resume_id,
                                    "match_type": duplicate_match.match_type or "exact",
                                    "similarity_score": duplicate_match.similarity_score,
                                })

                                logger.info(
                                    f"Duplicate detected: {file.filename} matches "
                                    f"resume {duplicate_match.original_resume_id}"
                                )
                        except Exception as dup_error:
                            # Log but don't fail the upload on duplicate detection error
                            logger.warning(f"Duplicate detection failed for {file.filename}: {dup_error}")

            except HTTPException:
                failed_uploads.append(file.filename)
                logger.warning(f"Failed to validate file: {file.filename}")
            except Exception as e:
                failed_uploads.append(file.filename)
                logger.error(f"Failed to store file {file.filename}: {e}")

        await db.commit()

        # Log processing summary
        dup_count = len(detected_duplicates)
        if zip_files_processed > 0:
            logger.info(
                f"Batch upload summary: {len(files)} input files ({zip_files_processed} ZIP archives), "
                f"{len(resume_ids)} resumes stored, {len(failed_uploads)} failures, {dup_count} duplicates"
            )
        else:
            logger.info(
                f"Batch upload summary: {len(files)} files, "
                f"{len(resume_ids)} resumes stored, {len(failed_uploads)} failures, {dup_count} duplicates"
            )

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
                    "duplicates_detected": len(detected_duplicates),
                    "duplicates": detected_duplicates,
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

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "batch_id": str(batch_id),
                "total_files": len(resume_ids),
                "status": batch_job.status.value,
                "message": f"Batch upload started with {len(resume_ids)} files",
                "duplicates_detected": len(detected_duplicates),
                "duplicates": detected_duplicates,
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
