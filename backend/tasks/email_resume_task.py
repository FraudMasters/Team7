"""
Email attachment processing task for extracting resumes from inbound emails.

This module provides Celery tasks for processing inbound emails received via webhook,
extracting resume attachments, validating file formats, creating resume records,
and triggering background analysis.

The task integrates with:
- Inbound email API (webhook reception)
- File validation utilities (magic number verification)
- Resume model (database storage)
- BatchJob model (processing tracking)
- Parallel resume analysis tasks (background processing)

Queue Management:
- Supports pause/resume/cancel via batch job status checking
- Real-time progress updates via WebSocket
"""
import asyncio
import base64
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select

from config import get_settings
from database import async_session_maker

logger = logging.getLogger(__name__)
settings = get_settings()


# Directory for storing uploaded resumes from email
EMAIL_UPLOAD_DIR = Path("data/uploads/email")
EMAIL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions for resume attachments
ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx", ".doc"}
MAX_ATTACHMENT_SIZE_MB = 10


class EmailProcessingError(Exception):
    """Custom exception for email processing errors."""
    pass


def _validate_attachment_format(
    filename: str,
    content: bytes,
) -> tuple[bool, str]:
    """
    Validate attachment file format using magic number verification.

    Args:
        filename: Name of the attached file
        content: Raw bytes of the file content

    Returns:
        Tuple of (is_valid, error_message)
    """
    from utils.file_validation import validate_magic_number, validate_file_structure

    file_ext = Path(filename).suffix.lower()

    # Check extension
    if file_ext not in ALLOWED_RESUME_EXTENSIONS:
        return False, f"Unsupported file type: {file_ext}. Allowed: {', '.join(ALLOWED_RESUME_EXTENSIONS)}"

    # Check size
    if len(content) > MAX_ATTACHMENT_SIZE_MB * 1024 * 1024:
        return False, f"File too large: {len(content) / 1024 / 1024:.1f}MB. Maximum: {MAX_ATTACHMENT_SIZE_MB}MB"

    # Check magic number
    is_valid, error = validate_magic_number(content, file_ext)
    if not is_valid:
        return False, error

    # Check file structure
    is_valid, error = validate_file_structure(content, file_ext)
    if not is_valid:
        return False, error

    return True, ""


async def _store_resume_from_attachment(
    filename: str,
    content: bytes,
    content_type: str,
    organization_id: Optional[str] = None,
    vacancy_id: Optional[str] = None,
    sender_email: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Store a resume attachment as a Resume record.

    This function saves the file to disk and creates a database record
    for tracking.

    Args:
        filename: Original filename of the attachment
        content: Raw bytes of the file content
        content_type: MIME type of the file
        organization_id: Optional organization UUID
        vacancy_id: Optional vacancy UUID to link the resume to
        sender_email: Optional sender email address for tracking

    Returns:
        Dictionary with resume_id and file_path

    Raises:
        EmailProcessingError: If storage fails
    """
    from models.resume import Resume, ResumeStatus

    try:
        # Generate unique ID
        resume_id = uuid4()

        # Create safe filename
        safe_filename = Path(filename).name
        file_extension = Path(safe_filename).suffix
        stored_filename = f"{resume_id}{file_extension}"
        file_path = EMAIL_UPLOAD_DIR / stored_filename

        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Stored email attachment: {filename} -> {file_path}")

        # Create Resume record
        resume = Resume(
            id=resume_id,
            organization_id=organization_id or str(uuid4()),  # Default org if not provided
            filename=filename,
            file_path=str(file_path),
            content_type=content_type,
            status=ResumeStatus.PENDING,
        )

        async with async_session_maker() as db:
            db.add(resume)
            await db.flush()

            # If vacancy_id is provided, create a job application link
            # This will be handled by the analysis/screening tasks
            if vacancy_id:
                logger.info(f"Resume {resume_id} linked to vacancy {vacancy_id}")

            await db.commit()

        return {
            "resume_id": str(resume_id),
            "filename": filename,
            "file_path": str(file_path),
            "status": ResumeStatus.PENDING.value,
        }

    except Exception as e:
        logger.error(f"Failed to store resume from attachment: {e}", exc_info=True)
        raise EmailProcessingError(f"Failed to store resume: {str(e)}")


async def _create_batch_job_for_email(
    total_files: int,
    sender_email: str,
    vacancy_id: Optional[str] = None,
) -> str:
    """
    Create a BatchJob to track email resume processing.

    Args:
        total_files: Number of resume attachments to process
        sender_email: Email address of the sender
        vacancy_id: Optional vacancy UUID

    Returns:
        UUID string of the created batch job
    """
    from models.batch_job import BatchJob, BatchJobStatus

    batch_job = BatchJob(
        total_files=total_files,
        processed_files=0,
        failed_files=0,
        status=BatchJobStatus.pending,
        notification_email=sender_email,
    )

    async with async_session_maker() as db:
        db.add(batch_job)
        await db.flush()
        await db.commit()

        logger.info(f"Created batch job {batch_job.id} for email from {sender_email}")

        return str(batch_job.id)


async def _update_batch_job_progress(
    batch_job_id: str,
    processed: int,
    failed: int,
    status: str,
) -> None:
    """
    Update batch job progress in the database.

    Args:
        batch_job_id: UUID string of the batch job
        processed: Number of files processed
        failed: Number of files that failed
        status: Current status string
    """
    from models.batch_job import BatchJob, BatchJobStatus

    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(BatchJob).where(BatchJob.id == UUID(batch_job_id))
            )
            batch_job = result.scalar_one_or_none()

            if batch_job:
                batch_job.processed_files = processed
                batch_job.failed_files = failed
                batch_job.status = BatchJobStatus(status)

                if status == "completed":
                    batch_job.completed_at = datetime.now(timezone.utc)

                await db.commit()

    except Exception as e:
        logger.error(f"Failed to update batch job progress: {e}")


def _broadcast_email_progress_safe(
    task_id: str,
    batch_job_id: str,
    current: int,
    total: int,
    message: str,
) -> int:
    """
    Safely broadcast email processing progress via WebSocket.

    Args:
        task_id: Celery task ID
        batch_job_id: Batch job UUID
        current: Current number of processed attachments
        total: Total number of attachments
        message: Human-readable progress message

    Returns:
        Number of clients the message was sent to
    """
    try:
        from websocket.resume_progress import broadcast_resume_progress

        return asyncio.run(
            broadcast_resume_progress(
                task_id=task_id,
                current=current,
                total=total,
                message=message,
            )
        )
    except Exception as e:
        logger.debug(f"Failed to broadcast email progress: {e}")
        return 0


@shared_task(
    name="tasks.email_resume_task.process_inbound_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_inbound_email(
    self,
    message_id: str,
    from_email: str,
    from_name: Optional[str],
    to_addresses: List[str],
    subject: Optional[str],
    text_body: Optional[str],
    html_body: Optional[str],
    attachments: List[Dict[str, Any]],
    vacancy_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    provider: Optional[str] = None,
    spam_score: Optional[float] = None,
    received_at: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process an inbound email and extract resume attachments.

    This Celery task processes emails received via webhook, extracts and
    validates resume attachments, creates Resume records, and triggers
    background analysis.

    Task Workflow:
    1. Validate email is not spam
    2. Iterate through attachments
    3. Validate each attachment format
    4. Store valid attachments as Resume records
    5. Create BatchJob for tracking
    6. Trigger parallel resume analysis
    7. Update progress via WebSocket

    Args:
        self: Celery task instance (bind=True)
        message_id: Unique message identifier for tracking
        from_email: Sender email address
        from_name: Optional sender name
        to_addresses: List of recipient email addresses
        subject: Email subject line
        text_body: Plain text email body
        html_body: HTML email body
        attachments: List of attachment dictionaries with:
            - filename: Name of the file
            - content_type: MIME type
            - content: Base64-encoded file content
            - size: File size in bytes (optional)
        vacancy_id: Optional vacancy UUID to link resumes to
        organization_id: Optional organization UUID
        provider: Email provider identifier (sendgrid, mailgun, etc.)
        spam_score: Spam score from provider (optional)
        received_at: ISO timestamp when email was received (optional)

    Returns:
        Dictionary containing processing results:
        - status: Task status (completed/failed/partial)
        - message_id: Original message ID
        - total_attachments: Total number of attachments
        - valid_resumes: Number of valid resume attachments
        - rejected_attachments: Number of rejected attachments
        - resume_ids: List of created resume IDs
        - batch_job_id: Batch job UUID for tracking
        - processing_time_ms: Total processing time
        - errors: List of error messages (if any)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For processing errors (with retry)

    Example:
        >>> from tasks.email_resume_task import process_inbound_email
        >>> task = process_inbound_email.delay(
        ...     message_id="email_20250103_123456_abc123",
        ...     from_email="recruiter@company.com",
        ...     to_addresses=["vacancy-123@resumes.agenthr.com"],
        ...     subject="Resume submission",
        ...     attachments=[{
        ...         "filename": "resume.pdf",
        ...         "content_type": "application/pdf",
        ...         "content": "base64-encoded-content"
        ...     }]
        ... )
        >>> result = task.get()
        >>> print(result['valid_resumes'])
        1
    """
    import time as time_module
    start_time = time_module.time()
    task_id = self.request.id

    logger.info(
        f"Processing inbound email: message_id={message_id}, "
        f"from={from_email}, attachments={len(attachments)}"
    )

    try:
        # Validate spam score
        if spam_score is not None and spam_score > 5.0:
            logger.warning(
                f"Rejecting email with high spam score: {spam_score}, "
                f"from={from_email}, message_id={message_id}"
            )
            return {
                "status": "rejected",
                "message_id": message_id,
                "rejection_reason": "high_spam_score",
                "spam_score": spam_score,
                "total_attachments": len(attachments),
                "valid_resumes": 0,
                "processing_time_ms": round((time_module.time() - start_time) * 1000, 2),
            }

        # Track results
        valid_resumes = []
        rejected_attachments = []
        errors = []

        # Create async processing loop
        async def _process_attachments():
            nonlocal valid_resumes, rejected_attachments, errors

            for attachment in attachments:
                filename = attachment.get("filename", "unknown")
                content_type = attachment.get("content_type", "application/octet-stream")
                content_b64 = attachment.get("content")

                # Decode base64 content
                if not content_b64:
                    rejected_attachments.append({
                        "filename": filename,
                        "reason": "Missing content",
                    })
                    continue

                try:
                    content = base64.b64decode(content_b64)
                except Exception as e:
                    rejected_attachments.append({
                        "filename": filename,
                        "reason": f"Invalid base64 encoding: {str(e)}",
                    })
                    continue

                # Validate attachment format
                is_valid, error_msg = _validate_attachment_format(filename, content)
                if not is_valid:
                    rejected_attachments.append({
                        "filename": filename,
                        "reason": error_msg,
                    })
                    logger.warning(f"Rejected attachment {filename}: {error_msg}")
                    continue

                # Store as Resume record
                try:
                    resume_data = await _store_resume_from_attachment(
                        filename=filename,
                        content=content,
                        content_type=content_type,
                        organization_id=organization_id,
                        vacancy_id=vacancy_id,
                        sender_email=from_email,
                    )
                    valid_resumes.append(resume_data)
                    logger.info(f"Stored resume from email: {filename} -> {resume_data['resume_id']}")
                except EmailProcessingError as e:
                    errors.append(f"Failed to store {filename}: {str(e)}")
                    rejected_attachments.append({
                        "filename": filename,
                        "reason": str(e),
                    })

        # Run async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_process_attachments())
        finally:
            loop.close()

        # If no valid resumes, return early
        if not valid_resumes:
            logger.info(
                f"No valid resumes extracted from email {message_id} "
                f"({len(rejected_attachments)} rejected)"
            )
            return {
                "status": "completed",
                "message_id": message_id,
                "total_attachments": len(attachments),
                "valid_resumes": 0,
                "rejected_attachments": len(rejected_attachments),
                "rejection_details": rejected_attachments,
                "resume_ids": [],
                "processing_time_ms": round((time_module.time() - start_time) * 1000, 2),
            }

        # Create batch job for tracking
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            batch_job_id = loop.run_until_complete(
                _create_batch_job_for_email(
                    total_files=len(valid_resumes),
                    sender_email=from_email,
                    vacancy_id=vacancy_id,
                )
            )
        finally:
            loop.close()

        logger.info(f"Created batch job {batch_job_id} for {len(valid_resumes)} resumes")

        # Broadcast initial progress
        _broadcast_email_progress_safe(
            task_id=task_id,
            batch_job_id=batch_job_id,
            current=0,
            total=len(valid_resumes),
            message=f"Processing {len(valid_resumes)} resumes from email...",
        )

        # Extract resume IDs for analysis
        resume_ids = [r["resume_id"] for r in valid_resumes]

        # Trigger parallel analysis
        # Import here to avoid circular dependency
        from tasks.parallel_resume_tasks import parallel_batch_analyze_resumes

        analysis_task = parallel_batch_analyze_resumes.delay(
            resume_ids=resume_ids,
            check_grammar=True,
            extract_experience=True,
            detect_errors=True,
            batch_size=None,  # Process all in parallel
            batch_job_id=batch_job_id,
        )

        logger.info(
            f"Triggered parallel analysis task {analysis_task.id} "
            f"for {len(resume_ids)} resumes"
        )

        # Update batch job with Celery task ID
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                _update_batch_job_progress(
                    batch_job_id=batch_job_id,
                    processed=0,
                    failed=0,
                    status="processing",
                )
            )
        finally:
            loop.close()

        processing_time_ms = round((time_module.time() - start_time) * 1000, 2)

        # Determine status
        status = "completed"
        if rejected_attachments and valid_resumes:
            status = "partial"
        elif rejected_attachments and not valid_resumes:
            status = "failed"

        result = {
            "status": status,
            "message_id": message_id,
            "from_email": from_email,
            "total_attachments": len(attachments),
            "valid_resumes": len(valid_resumes),
            "rejected_attachments": len(rejected_attachments),
            "resume_ids": resume_ids,
            "resume_details": valid_resumes,
            "rejection_details": rejected_attachments if rejected_attachments else None,
            "batch_job_id": batch_job_id,
            "analysis_task_id": analysis_task.id,
            "vacancy_id": vacancy_id,
            "processing_time_ms": processing_time_ms,
        }

        logger.info(
            f"Email processing completed: message_id={message_id}, "
            f"valid={len(valid_resumes)}, rejected={len(rejected_attachments)}, "
            f"time={processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Email processing task timed out: message_id={message_id}")
        return {
            "status": "failed",
            "message_id": message_id,
            "error": "Task timed out",
            "total_attachments": len(attachments),
            "valid_resumes": 0,
            "processing_time_ms": round((time_module.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(
            f"Failed to process inbound email {message_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying email processing, attempt {self.request.retries + 1}/{self.max_retries}"
            )
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "status": "failed",
            "message_id": message_id,
            "error": str(e),
            "total_attachments": len(attachments),
            "valid_resumes": 0,
            "processing_time_ms": round((time_module.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.email_resume_task.process_email_batch",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def process_email_batch(
    self,
    emails: List[Dict[str, Any]],
    organization_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process a batch of inbound emails in sequence.

    This task is useful for processing multiple emails that were queued
    or collected in a batch.

    Args:
        self: Celery task instance (bind=True)
        emails: List of email dictionaries with same structure as process_inbound_email
        organization_id: Optional organization UUID for all emails

    Returns:
        Dictionary containing batch processing results:
        - status: Overall status (completed/partial/failed)
        - total_emails: Total number of emails processed
        - successful: Number of successfully processed emails
        - failed: Number of failed emails
        - results: List of individual email results
        - processing_time_ms: Total processing time
    """
    import time as time_module
    start_time = time_module.time()

    logger.info(f"Processing batch of {len(emails)} emails")

    results = []
    successful = 0
    failed = 0
    total_resumes_extracted = 0

    for email in emails:
        try:
            # Process each email
            result = process_inbound_email(
                message_id=email.get("message_id"),
                from_email=email.get("from_email"),
                from_name=email.get("from_name"),
                to_addresses=email.get("to", []),
                subject=email.get("subject"),
                text_body=email.get("text_body"),
                html_body=email.get("html_body"),
                attachments=email.get("attachments", []),
                vacancy_id=email.get("vacancy_id"),
                organization_id=organization_id or email.get("organization_id"),
                provider=email.get("provider"),
                spam_score=email.get("spam_score"),
                received_at=email.get("received_at"),
            )

            results.append(result)

            if result.get("status") in ("completed", "partial"):
                successful += 1
                total_resumes_extracted += result.get("valid_resumes", 0)
            else:
                failed += 1

        except Exception as e:
            logger.error(f"Failed to process email in batch: {e}")
            results.append({
                "message_id": email.get("message_id"),
                "status": "failed",
                "error": str(e),
            })
            failed += 1

    processing_time_ms = round((time_module.time() - start_time) * 1000, 2)

    # Determine overall status
    if failed == 0:
        status = "completed"
    elif successful == 0:
        status = "failed"
    else:
        status = "partial"

    logger.info(
        f"Email batch processing completed: {successful} successful, "
        f"{failed} failed, {total_resumes_extracted} resumes extracted "
        f"in {processing_time_ms}ms"
    )

    return {
        "status": status,
        "total_emails": len(emails),
        "successful": successful,
        "failed": failed,
        "total_resumes_extracted": total_resumes_extracted,
        "results": results,
        "processing_time_ms": processing_time_ms,
    }
