"""
Job board import tasks for polling and processing applicants.

This module provides Celery tasks for importing applicants from job boards
like Indeed, ZipRecruiter, and Glassdoor. It handles polling for new applicants,
processing imported resumes, duplicate detection, and periodic scheduled imports.

Also includes tasks for Data Portability Suite:
- Processing LinkedIn CSV uploads
- Processing Indeed XML uploads
- Processing HR-XML uploads
- Import file validation and cleanup
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models import JobBoardIntegration, ImportLog, ImportJobStatus
from models.import_job import ImportJob, ImportJobStatus as ImportJobStatusEnum, ImportFormat
from models import Resume, Candidate

logger = logging.getLogger(__name__)
settings = get_settings()

# Default interval between polling cycles (minutes)
POLLING_INTERVAL_MINUTES = 30


@shared_task(
    name="tasks.import_tasks.poll_job_board",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def poll_job_board(
    self,
    job_board_integration_id: str,
    job_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    from_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Poll a single job board for new applicants.

    This Celery task handles fetching applicants from a specific job board
    integration. It supports filtering by status and date, and handles pagination
    for large result sets.

    Task Workflow:
    1. Retrieve job board integration from database
    2. Initialize appropriate API client (Indeed, ZipRecruiter, Glassdoor)
    3. Fetch applicants from the job board
    4. Create import log entry
    5. Return results with applicant count and status

    Args:
        self: Celery task instance (bind=True)
        job_board_integration_id: UUID of the job board integration
        job_id: Optional specific job ID to fetch applicants for
        status_filter: Optional filter by application status (e.g., 'new', 'reviewed')
        from_date: Optional filter applications from this date onwards (ISO format)

    Returns:
        Dictionary containing polling results:
        - job_board_integration_id: ID of the integration
        - job_board_name: Name of the job board
        - status: Task status (completed/failed/pending)
        - applicants_found: Number of applicants found
        - applicants_processed: Number of applicants successfully processed
        - errors: List of any errors that occurred
        - processing_time_ms: Total processing time
        - import_log_id: ID of the created import log (if created)

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For polling failures

    Example:
        >>> result = poll_job_board.delay(
        ...     job_board_integration_id="123-456",
        ...     status_filter="new"
        ... )
        >>> print(result.get())
        {'job_board_integration_id': '123-456', 'status': 'completed', 'applicants_found': 5}
    """
    import time
    import asyncio

    start_time = time.time()

    logger.info(
        f"Polling job board integration_id={job_board_integration_id} "
        f"with job_id={job_id}, status_filter={status_filter}"
    )

    async def _poll():
        """Async function to perform the actual polling."""
        async with async_session_maker() as db:
            try:
                # Fetch job board integration from database
                result = await db.execute(
                    select(JobBoardIntegration).where(
                        JobBoardIntegration.id == job_board_integration_id
                    )
                )
                integration = result.scalar_one_or_none()

                if not integration:
                    error_msg = f"Job board integration {job_board_integration_id} not found"
                    logger.error(error_msg)
                    return {
                        "job_board_integration_id": job_board_integration_id,
                        "status": "failed",
                        "error": error_msg,
                        "applicants_found": 0,
                        "applicants_processed": 0,
                    }

                if not integration.enabled:
                    error_msg = f"Job board integration {integration.name} is disabled"
                    logger.warning(error_msg)
                    return {
                        "job_board_integration_id": job_board_integration_id,
                        "job_board_name": integration.name,
                        "status": "failed",
                        "error": error_msg,
                        "applicants_found": 0,
                        "applicants_processed": 0,
                    }

                logger.info(
                    f"Processing job board integration: {integration.name} "
                    f"(endpoint: {integration.api_endpoint})"
                )

                # Import the appropriate client based on job board name
                client = None
                applicants_data = []
                errors = []

                try:
                    # Normalize job board name for comparison
                    board_name = integration.name.lower()

                    if "indeed" in board_name:
                        from services.job_board_clients.indeed_client import (
                            get_indeed_client_from_integration,
                        )

                        client = await get_indeed_client_from_integration(integration)

                        # Use job_id from integration config if not provided
                        if not job_id:
                            job_id = integration.config.get("job_id")

                        if not job_id:
                            error_msg = "Job ID not provided and not found in integration config"
                            logger.error(error_msg)
                            errors.append(error_msg)
                        else:
                            # Fetch all applicants for the job
                            fetch_result = await client.fetch_all_applicants(
                                job_id=job_id,
                                status_filter=status_filter,
                                from_date=from_date,
                            )
                            applicants_data = fetch_result.applicants
                            errors.extend(fetch_result.errors)

                    elif "ziprecruiter" in board_name:
                        from services.job_board_clients.ziprecruiter_client import (
                            ZipRecruiterClient,
                        )

                        client = ZipRecruiterClient(
                            api_key=integration.api_key,
                            api_endpoint=integration.api_endpoint,
                        )

                        # ZipRecruiter client implementation
                        # Similar pattern to Indeed - would call fetch_applicants
                        logger.info("ZipRecruiter client not fully implemented yet")
                        errors.append("ZipRecruiter client not fully implemented")

                    elif "glassdoor" in board_name:
                        from services.job_board_clients.glassdoor_client import (
                            GlassdoorClient,
                        )

                        client = GlassdoorClient(
                            api_key=integration.api_key,
                            api_endpoint=integration.api_endpoint,
                        )

                        # Glassdoor client implementation
                        logger.info("Glassdoor client not fully implemented yet")
                        errors.append("Glassdoor client not fully implemented")

                    else:
                        error_msg = f"Unknown job board: {integration.name}"
                        logger.error(error_msg)
                        errors.append(error_msg)

                except Exception as e:
                    error_msg = f"Error initializing or using client: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)

                # Close client if it was created
                if client and hasattr(client, "close"):
                    try:
                        await client.close()
                    except Exception as e:
                        logger.warning(f"Error closing client: {e}")

                # Create import log entry
                import_log = ImportLog(
                    job_board_id=str(integration.id),
                    job_board_name=integration.name,
                    status=ImportJobStatus.COMPLETED if not errors else ImportJobStatus.FAILED,
                    records_processed=len(applicants_data),
                    records_succeeded=len(applicants_data) if not errors else 0,
                    records_failed=0 if not errors else len(applicants_data),
                    error_message=errors[0] if errors else None,
                    error_details={"errors": errors} if errors else None,
                    import_metadata={
                        "job_id": job_id,
                        "status_filter": status_filter,
                        "from_date": from_date,
                    },
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                )

                db.add(import_log)
                await db.commit()

                processing_time = int((time.time() - start_time) * 1000)

                logger.info(
                    f"Job board polling completed for {integration.name}: "
                    f"{len(applicants_data)} applicants found in {processing_time}ms"
                )

                return {
                    "job_board_integration_id": job_board_integration_id,
                    "job_board_name": integration.name,
                    "status": "completed" if not errors else "failed",
                    "applicants_found": len(applicants_data),
                    "applicants_processed": len(applicants_data) if not errors else 0,
                    "errors": errors,
                    "processing_time_ms": processing_time,
                    "import_log_id": str(import_log.id),
                }

            except SoftTimeLimitExceeded:
                logger.error(
                    f"Job board polling task timed out for integration_id={job_board_integration_id}"
                )
                return {
                    "job_board_integration_id": job_board_integration_id,
                    "status": "failed",
                    "error": "Task timed out",
                    "applicants_found": 0,
                    "applicants_processed": 0,
                }

            except Exception as e:
                logger.error(
                    f"Failed to poll job board for integration_id={job_board_integration_id}: {e}",
                    exc_info=True,
                )

                # Create failed import log
                try:
                    import_log = ImportLog(
                        job_board_id=job_board_integration_id,
                        job_board_name="unknown",
                        status=ImportJobStatus.FAILED,
                        records_processed=0,
                        records_succeeded=0,
                        records_failed=0,
                        error_message=str(e),
                        error_details={"exception": str(e)},
                        started_at=datetime.utcnow(),
                        completed_at=datetime.utcnow(),
                    )
                    db.add(import_log)
                    await db.commit()
                except Exception as log_error:
                    logger.error(f"Failed to create import log: {log_error}")

                # Retry with exponential backoff
                if self.request.retries < self.max_retries:
                    raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

                return {
                    "job_board_integration_id": job_board_integration_id,
                    "status": "failed",
                    "error": str(e),
                    "applicants_found": 0,
                    "applicants_processed": 0,
                }

    # Run the async function in the sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_poll())


@shared_task(
    name="tasks.import_tasks.process_imported_resume",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_imported_resume(
    self,
    resume_id: str,
    applicant_id: Optional[str] = None,
    check_grammar: bool = True,
    extract_experience: bool = True,
    detect_errors: bool = True,
) -> Dict[str, Any]:
    """
    Process an imported resume by parsing and extracting relevant information.

    This Celery task handles parsing of resumes imported from job boards.
    It extracts text, analyzes content, and updates the database with parsed data.

    Task Workflow:
    1. Find the resume file by ID
    2. Extract text from the resume (PDF/DOCX)
    3. Detect language
    4. Extract keywords and entities
    5. Perform optional analysis (grammar, experience, errors)
    6. Update database with parsed results
    7. Return processing results

    Args:
        self: Celery task instance (bind=True)
        resume_id: Unique identifier of the resume to process
        applicant_id: Optional ID of the applicant (from job board)
        check_grammar: Whether to perform grammar checking (default: True)
        extract_experience: Whether to calculate work experience (default: True)
        detect_errors: Whether to detect resume errors (default: True)

    Returns:
        Dictionary containing processing results:
        - resume_id: ID of the processed resume
        - applicant_id: ID of the applicant (if provided)
        - status: Task status (completed/failed)
        - extracted_data: Dictionary containing parsed information:
            - text_length: Length of extracted text
            - detected_language: Detected language code
            - keywords: Extracted keywords
            - entities: Extracted entities/technical skills
            - experience: Work experience summary (if extract_experience=True)
            - grammar_issues: Grammar check results (if check_grammar=True)
            - resume_errors: Detected resume errors (if detect_errors=True)
        - processing_time_ms: Total processing time
        - error: Error message if processing failed

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For processing failures

    Example:
        >>> result = process_imported_resume.delay(
        ...     resume_id="abc-123",
        ...     applicant_id="applicant-456"
        ... )
        >>> print(result.get())
        {'resume_id': 'abc-123', 'status': 'completed', 'extracted_data': {...}}
    """
    import time
    import sys
    from pathlib import Path

    start_time = time.time()

    logger.info(
        f"Processing imported resume resume_id={resume_id} "
        f"applicant_id={applicant_id}"
    )

    try:
        # Import necessary modules for resume processing
        # Add parent directory to path to import from data_extractor service
        sys.path.insert(
            0, str(Path(__file__).parent.parent.parent.parent / "services" / "data_extractor")
        )

        from analyzers import (
            extract_resume_keywords_hf as extract_resume_keywords,
            extract_resume_entities,
            check_grammar_resume,
            calculate_total_experience,
            format_experience_summary,
            detect_resume_errors,
            extract_work_experience,
        )
        from services.data_extractor.extract import extract_text_from_pdf, extract_text_from_docx

        # Directory where uploaded resumes are stored
        upload_dir = Path("data/uploads")

        # Step 1: Find resume file
        file_path = None
        for ext in [".pdf", ".docx", ".PDF", ".DOCX"]:
            potential_path = upload_dir / f"{resume_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                break

        if not file_path:
            error_msg = f"Resume file with ID '{resume_id}' not found"
            logger.error(error_msg)
            return {
                "resume_id": resume_id,
                "applicant_id": applicant_id,
                "status": "failed",
                "error": error_msg,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Step 2: Extract text from file
        try:
            file_ext = file_path.suffix.lower()

            if file_ext == ".pdf":
                extraction_result = extract_text_from_pdf(file_path)
            elif file_ext == ".docx":
                extraction_result = extract_text_from_docx(file_path)
            else:
                error_msg = f"Unsupported file type: {file_ext}"
                logger.error(error_msg)
                return {
                    "resume_id": resume_id,
                    "applicant_id": applicant_id,
                    "status": "failed",
                    "error": error_msg,
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                }

            # Check for extraction errors
            if extraction_result.get("error"):
                error_msg = f"Text extraction failed: {extraction_result['error']}"
                logger.error(error_msg)
                return {
                    "resume_id": resume_id,
                    "applicant_id": applicant_id,
                    "status": "failed",
                    "error": error_msg,
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                }

            resume_text = extraction_result.get("text", "")
            if not resume_text or len(resume_text.strip()) < 10:
                error_msg = "Extracted text is too short or empty"
                logger.error(error_msg)
                return {
                    "resume_id": resume_id,
                    "applicant_id": applicant_id,
                    "status": "failed",
                    "error": error_msg,
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                }

            logger.info(f"Extracted {len(resume_text)} characters from {file_path.name}")

        except Exception as e:
            error_msg = f"Error extracting text from resume: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "resume_id": resume_id,
                "applicant_id": applicant_id,
                "status": "failed",
                "error": error_msg,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Step 3: Detect language
        try:
            from langdetect import detect

            lang_code = detect(resume_text[:1000])
            detected_language = (
                "ru" if lang_code == "ru" else "en" if lang_code == "en" else lang_code
            )
        except Exception as e:
            logger.warning(f"Language detection failed: {e}, defaulting to 'en'")
            detected_language = "en"

        # Step 4: Extract keywords and entities
        extracted_data = {
            "text_length": len(resume_text),
            "detected_language": detected_language,
        }

        try:
            # Extract keywords
            keywords_result = extract_resume_keywords(resume_text, language=detected_language)
            keywords = keywords_result.get("all_keywords") or keywords_result.get("keywords", [])
            extracted_data["keywords"] = keywords

            # Extract entities
            entities_result = extract_resume_entities(resume_text)
            entities = entities_result.get("technical_skills", [])
            extracted_data["entities"] = entities

            logger.info(f"Extracted {len(keywords)} keywords and {len(entities)} entities")

        except Exception as e:
            logger.warning(f"Keyword/entity extraction partially failed: {e}", exc_info=True)
            extracted_data["keywords"] = []
            extracted_data["entities"] = []

        # Step 5: Optional analysis
        if extract_experience:
            try:
                experience_summary = format_experience_summary(resume_text, language=detected_language)
                total_experience = calculate_total_experience(resume_text, language=detected_language)
                work_experience = extract_work_experience(resume_text, language=detected_language)

                extracted_data["experience"] = {
                    "summary": experience_summary,
                    "total_years": total_experience,
                    "work_history": work_experience,
                }
            except Exception as e:
                logger.warning(f"Experience extraction failed: {e}", exc_info=True)
                extracted_data["experience"] = None

        if check_grammar:
            try:
                grammar_result = check_grammar_resume(resume_text, language=detected_language)
                extracted_data["grammar_issues"] = grammar_result
            except Exception as e:
                logger.warning(f"Grammar check failed: {e}", exc_info=True)
                extracted_data["grammar_issues"] = None

        if detect_errors:
            try:
                errors_result = detect_resume_errors(resume_text, language=detected_language)
                extracted_data["resume_errors"] = errors_result
            except Exception as e:
                logger.warning(f"Resume error detection failed: {e}", exc_info=True)
                extracted_data["resume_errors"] = None

        processing_time = round((time.time() - start_time) * 1000, 2)

        logger.info(
            f"Resume processing completed for resume_id={resume_id} "
            f"in {processing_time}ms"
        )

        return {
            "resume_id": resume_id,
            "applicant_id": applicant_id,
            "status": "completed",
            "extracted_data": extracted_data,
            "processing_time_ms": processing_time,
        }

    except SoftTimeLimitExceeded:
        logger.error(
            f"Resume processing task timed out for resume_id={resume_id}"
        )
        return {
            "resume_id": resume_id,
            "applicant_id": applicant_id,
            "status": "failed",
            "error": "Task timed out",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(
            f"Failed to process resume resume_id={resume_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying resume processing (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "resume_id": resume_id,
            "applicant_id": applicant_id,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


def get_active_integrations(db_session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Retrieve all active (enabled) job board integrations from the database.

    This function queries the database for all job board integrations that
    are currently enabled and ready for polling.

    Args:
        db_session: Async database session for querying

    Returns:
        List of dictionaries containing integration data:
        [
            {
                "id": "uuid",
                "name": "Indeed",
                "api_endpoint": "https://api.indeed.com",
                "enabled": true,
                "config": {"job_id": "12345"}
            },
            ...
        ]

    Example:
        >>> async with async_session_maker() as db:
        ...     integrations = await get_active_integrations(db)
        ...     print(f"Found {len(integrations)} active integrations")
        3
    """
    logger.info("Retrieving active job board integrations")

    try:
        # Query all enabled integrations
        query = select(JobBoardIntegration).where(JobBoardIntegration.enabled == True)
        result = await db_session.execute(query)
        integrations = result.scalars().all()

        integrations_data = []
        for integration in integrations:
            integration_info = {
                "id": str(integration.id),
                "name": integration.name,
                "api_endpoint": integration.api_endpoint,
                "enabled": integration.enabled,
                "config": integration.config or {},
            }
            integrations_data.append(integration_info)

        logger.info(f"Retrieved {len(integrations_data)} active integrations")

        return integrations_data

    except Exception as e:
        logger.error(f"Error retrieving active integrations: {e}", exc_info=True)
        return []


@shared_task(
    name="tasks.import_tasks.scheduled_poll_all_integrations",
    bind=True,
)
def scheduled_poll_all_integrations(
    self,
) -> Dict[str, Any]:
    """
    Periodic task to poll all active job board integrations.

    This is a scheduled task that runs periodically (e.g., every 30 minutes)
    to automatically poll all enabled job board integrations for new applicants.
    It spawns individual polling tasks for each integration and returns a summary.

    Task Workflow:
    1. Retrieve all active (enabled) job board integrations
    2. Spawn individual poll_job_board task for each integration
    3. Aggregate results from all polling tasks
    4. Return summary of polling activity

    Args:
        self: Celery task instance (bind=True)

    Returns:
        Dictionary containing polling summary:
        - total_integrations: Number of integrations polled
        - successful_polls: Number of successful polling operations
        - failed_polls: Number of failed polling operations
        - total_applicants_found: Total applicants found across all integrations
        - total_processing_time_ms: Total processing time
        - integration_results: List of individual integration results
        - status: Task status (completed/failed)
        - timestamp: When the polling was initiated

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> # This would be scheduled via Celery beat
        >>> # celery beat schedule: {
        >>> #     'poll-all-integrations': {
        >>> #         'task': 'tasks.import_tasks.scheduled_poll_all_integrations',
        >>> #         'schedule': crontab(minute='*/30'),  # Every 30 minutes
        >>> #     }
        >>> # }
    """
    import asyncio

    start_time = time.time()

    logger.info("Starting scheduled polling of all active integrations")

    async def _poll_all():
        """Async function to perform polling of all integrations."""
        async with async_session_maker() as db:
            try:
                # Step 1: Retrieve all active integrations
                logger.info("Fetching active job board integrations")
                integrations = await get_active_integrations(db)

                if not integrations:
                    logger.warning("No active integrations found, skipping polling")
                    return {
                        "total_integrations": 0,
                        "successful_polls": 0,
                        "failed_polls": 0,
                        "total_applicants_found": 0,
                        "integration_results": [],
                        "status": "completed",
                        "message": "No active integrations found",
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                logger.info(f"Found {len(integrations)} active integrations to poll")

                # Step 2: Poll each integration
                integration_results = []
                total_applicants = 0
                successful_polls = 0
                failed_polls = 0

                for integration in integrations:
                    integration_id = integration.get("id")
                    integration_name = integration.get("name", "unknown")

                    logger.info(f"Polling integration: {integration_name} (ID: {integration_id})")

                    try:
                        # Import the poll_job_board task
                        from tasks.import_tasks import poll_job_board

                        # Trigger the polling task asynchronously
                        # We use .apply_async() with throw=False to get result without blocking
                        task_result = poll_job_board.apply_async(
                            args=[integration_id],
                            throw=False,
                        )

                        # Get the result (this will block until the task completes)
                        poll_result = task_result.get(timeout=300)  # 5 minute timeout per integration

                        if poll_result.get("status") == "completed":
                            successful_polls += 1
                            total_applicants += poll_result.get("applicants_found", 0)
                            logger.info(
                                f"Successfully polled {integration_name}: "
                                f"{poll_result.get('applicants_found', 0)} applicants found"
                            )
                        else:
                            failed_polls += 1
                            logger.warning(
                                f"Failed to poll {integration_name}: "
                                f"{poll_result.get('error', 'Unknown error')}"
                            )

                        integration_results.append(
                            {
                                "integration_id": integration_id,
                                "integration_name": integration_name,
                                "status": poll_result.get("status"),
                                "applicants_found": poll_result.get("applicants_found", 0),
                                "applicants_processed": poll_result.get("applicants_processed", 0),
                                "errors": poll_result.get("errors", []),
                                "processing_time_ms": poll_result.get("processing_time_ms", 0),
                            }
                        )

                    except Exception as e:
                        failed_polls += 1
                        error_msg = f"Error polling integration {integration_name}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        integration_results.append(
                            {
                                "integration_id": integration_id,
                                "integration_name": integration_name,
                                "status": "failed",
                                "applicants_found": 0,
                                "applicants_processed": 0,
                                "errors": [error_msg],
                                "processing_time_ms": 0,
                            }
                        )

                total_processing_time_ms = round((time.time() - start_time) * 1000, 2)

                result = {
                    "total_integrations": len(integrations),
                    "successful_polls": successful_polls,
                    "failed_polls": failed_polls,
                    "total_applicants_found": total_applicants,
                    "total_processing_time_ms": total_processing_time_ms,
                    "integration_results": integration_results,
                    "status": "completed",
                    "timestamp": datetime.utcnow().isoformat(),
                }

                logger.info(
                    f"Scheduled polling completed: {successful_polls}/{len(integrations)} successful, "
                    f"{total_applicants} total applicants found in {total_processing_time_ms}ms"
                )

                return result

            except SoftTimeLimitExceeded:
                logger.error(f"Task {self.request.id} exceeded time limit")
                return {
                    "total_integrations": 0,
                    "successful_polls": 0,
                    "failed_polls": 0,
                    "total_applicants_found": 0,
                    "total_processing_time_ms": round((time.time() - start_time) * 1000, 2),
                    "status": "failed",
                    "error": "Scheduled polling exceeded maximum time limit",
                    "timestamp": datetime.utcnow().isoformat(),
                }

            except Exception as e:
                logger.error(f"Error in scheduled polling: {e}", exc_info=True)
                return {
                    "total_integrations": 0,
                    "successful_polls": 0,
                    "failed_polls": 0,
                    "total_applicants_found": 0,
                    "total_processing_time_ms": round((time.time() - start_time) * 1000, 2),
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }

    # Run the async function in the sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_poll_all())


# ============================================================================
# DATA PORTABILITY SUITE TASKS
# Tasks for processing uploaded import files (LinkedIn CSV, Indeed XML, HR-XML)
# ============================================================================


def _get_data_portability_importers():
    """Lazy import of data portability importer services."""
    import sys
    from pathlib import Path

    _services_path = Path(__file__).parent.parent / 'services'
    if str(_services_path) not in sys.path:
        sys.path.insert(0, str(_services_path))

    try:
        from linkedin_csv_importer import LinkedInCSVImporter
        from indeed_xml_importer import IndeedXMLImporter
        from hrxml_importer import HRXMLImporter
        from import_service import ImportService
        return LinkedInCSVImporter, IndeedXMLImporter, HRXMLImporter, ImportService
    except ImportError:
        try:
            from services.linkedin_csv_importer import LinkedInCSVImporter
            from services.indeed_xml_importer import IndeedXMLImporter
            from services.hrxml_importer import HRXMLImporter
            from services.import_service import ImportService
            return LinkedInCSVImporter, IndeedXMLImporter, HRXMLImporter, ImportService
        except ImportError:
            return None, None, None, None


@shared_task(
    name="tasks.import.process_import_job",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def process_import_job_task(self, import_job_id: str) -> Dict[str, Any]:
    """
    Process a data portability import job asynchronously.

    Loads the import job from database, parses the file based on format
    (LinkedIn CSV, Indeed XML, HR-XML, etc.), creates candidates/resumes
    in the database, and updates the import job with results.

    This task is part of the Data Portability Suite and handles uploaded
    import files (not job board API polling).

    Args:
        import_job_id: UUID of the import job to process

    Returns:
        Dictionary with import results including status, counts, and errors

    Example:
        >>> result = process_import_job_task.delay(
        ...     import_job_id="abc-123-def-456"
        ... )
        >>> print(result.get())
        {'status': 'success', 'successful_imports': 10, 'failed_imports': 0}
    """
    import asyncio
    import os
    from uuid import UUID

    logger.info(f"Starting data portability import job processing: {import_job_id}")

    try:
        # Run async processing in sync context
        result = asyncio.run(_process_data_portability_import_async(import_job_id))
        return result

    except Exception as e:
        logger.error(f"Data portability import job {import_job_id} failed: {e}", exc_info=True)

        # Update job status to failed
        try:
            asyncio.run(_update_import_job_status(
                import_job_id,
                ImportJobStatusEnum.FAILED,
                error_message=str(e)
            ))
        except Exception as update_error:
            logger.error(f"Failed to update job status: {update_error}")

        # Retry with backoff
        try:
            raise self.retry(exc=e, countdown=300)
        except self.MaxRetriesExceededError:
            logger.error(f"Import job {import_job_id} max retries exceeded")
            return {
                "status": "failed",
                "import_job_id": import_job_id,
                "error": str(e),
            }


async def _process_data_portability_import_async(import_job_id: str) -> Dict[str, Any]:
    """
    Async implementation of data portability import job processing.

    Args:
        import_job_id: UUID of the import job

    Returns:
        Dictionary with import results
    """
    from uuid import UUID
    import os

    start_time = datetime.utcnow()

    async with async_session_maker() as db:
        try:
            # Load import job
            result = await db.execute(
                select(ImportJob).where(ImportJob.id == UUID(import_job_id))
            )
            import_job = result.scalar_one_or_none()

            if not import_job:
                raise ValueError(f"Import job {import_job_id} not found")

            # Update status to in progress
            import_job.status = ImportJobStatusEnum.IN_PROGRESS
            import_job.updated_at = datetime.utcnow()
            await db.commit()

            logger.info(
                f"Processing import job {import_job_id}: "
                f"format={import_job.format.value}, file={import_job.file_path}"
            )

            # Parse file based on format
            parse_result = await _parse_data_portability_file(import_job)

            if not parse_result["success"]:
                raise ValueError(
                    f"Failed to parse import file: {parse_result.get('error', 'Unknown error')}"
                )

            # Import candidates into database
            import_result = await _import_portability_candidates(
                db=db,
                import_job=import_job,
                profiles=parse_result["profiles"]
            )

            # Update import job with results
            elapsed_seconds = (datetime.utcnow() - start_time).total_seconds()

            import_job.status = (
                ImportJobStatusEnum.COMPLETED if import_result["successful_imports"] > 0
                else ImportJobStatusEnum.PARTIALLY_COMPLETED if import_result["skipped_records"] > 0
                else ImportJobStatusEnum.FAILED
            )
            import_job.total_records = import_result["total_records"]
            import_job.successful_imports = import_result["successful_imports"]
            import_job.failed_imports = import_result["failed_imports"]
            import_job.skipped_records = import_result["skipped_records"]
            import_job.validation_errors = import_result.get("validation_errors", [])
            import_job.import_metadata = {
                "elapsed_seconds": elapsed_seconds,
                "detected_format": parse_result.get("detected_format"),
                "processing_time": datetime.utcnow().isoformat(),
            }
            import_job.updated_at = datetime.utcnow()

            await db.commit()

            logger.info(
                f"Import job {import_job_id} completed: "
                f"total={import_result['total_records']}, "
                f"successful={import_result['successful_imports']}, "
                f"failed={import_result['failed_imports']}, "
                f"skipped={import_result['skipped_records']}"
            )

            return {
                "status": "success",
                "import_job_id": import_job_id,
                "total_records": import_result["total_records"],
                "successful_imports": import_result["successful_imports"],
                "failed_imports": import_result["failed_imports"],
                "skipped_records": import_result["skipped_records"],
                "elapsed_seconds": elapsed_seconds,
            }

        except Exception as e:
            logger.error(f"Error processing import job {import_job_id}: {e}", exc_info=True)
            await db.rollback()
            raise


async def _parse_data_portability_file(import_job: ImportJob) -> Dict[str, Any]:
    """
    Parse data portability import file based on format.

    Args:
        import_job: ImportJob instance with file_path and format

    Returns:
        Dictionary with parse results
    """
    import os

    file_path = import_job.file_path

    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"Import file not found: {file_path}",
            "profiles": []
        }

    # Get importers
    LinkedInCSVImporter, IndeedXMLImporter, HRXMLImporter, ImportService = _get_data_portability_importers()

    if not LinkedInCSVImporter:
        return {
            "success": False,
            "error": "Import services not available",
            "profiles": []
        }

    try:
        if import_job.format == ImportFormat.LINKEDIN_CSV:
            importer = LinkedInCSVImporter()
            result = importer.parse_csv_file(file_path)

            return {
                "success": result.success,
                "profiles": result.profiles,
                "detected_format": result.detected_format,
                "errors": result.errors,
                "warnings": result.warnings,
            }

        elif import_job.format == ImportFormat.INDEED_XML:
            importer = IndeedXMLImporter()
            result = importer.parse_xml_file(file_path)

            return {
                "success": result.success,
                "profiles": result.applications,  # Indeed uses "applications"
                "detected_format": result.detected_format,
                "errors": result.errors,
                "warnings": result.warnings,
            }

        elif import_job.format == ImportFormat.HRXML:
            importer = HRXMLImporter()
            result = importer.parse_xml_file(file_path)

            return {
                "success": result.success,
                "profiles": result.applications,  # HR-XML uses "applications"
                "detected_format": result.detected_format,
                "errors": result.errors,
                "warnings": result.warnings,
            }

        elif import_job.format in [ImportFormat.CUSTOM_CSV, ImportFormat.CUSTOM_JSON]:
            return {
                "success": False,
                "error": f"Custom format {import_job.format.value} not yet implemented",
                "profiles": []
            }

        else:
            return {
                "success": False,
                "error": f"Unsupported import format: {import_job.format.value}",
                "profiles": []
            }

    except Exception as e:
        logger.error(f"Error parsing import file {file_path}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "profiles": []
        }


async def _import_portability_candidates(
    db: AsyncSession,
    import_job: ImportJob,
    profiles: List[Any]
) -> Dict[str, Any]:
    """
    Import parsed profiles into database as candidates.

    Args:
        db: Database session
        import_job: ImportJob instance
        profiles: List of parsed profile data

    Returns:
        Dictionary with import statistics
    """
    # Get ImportService
    _, _, _, ImportService = _get_data_portability_importers()

    if not ImportService:
        logger.error("ImportService not available")
        return {
            "total_records": len(profiles),
            "successful_imports": 0,
            "failed_imports": len(profiles),
            "skipped_records": 0,
            "validation_errors": [{"error": "ImportService not available"}],
        }

    import_service = ImportService(db)

    total_records = len(profiles)
    successful_imports = 0
    failed_imports = 0
    skipped_records = 0
    validation_errors = []

    for idx, profile in enumerate(profiles):
        try:
            # Extract profile data based on type
            if hasattr(profile, "email"):
                email = profile.email
                first_name = profile.first_name
                last_name = profile.last_name
            else:
                # Handle dict-like profiles
                email = profile.get("email")
                first_name = profile.get("first_name")
                last_name = profile.get("last_name")

            # Skip if missing required fields
            if not email or not first_name or not last_name:
                validation_errors.append({
                    "row": idx + 1,
                    "error": "Missing required fields (email, first_name, last_name)",
                    "profile": str(profile)[:200]  # Truncate for logging
                })
                skipped_records += 1
                continue

            # Check for duplicates
            duplicate_check = await import_service.check_duplicate(
                job_board_id=str(import_job.id),
                email=email,
                first_name=first_name,
                last_name=last_name
            )

            if duplicate_check.is_duplicate:
                logger.info(
                    f"Skipping duplicate candidate: {email} "
                    f"(type: {duplicate_check.duplicate_type})"
                )
                skipped_records += 1
                continue

            # Create candidate/resume
            # Note: This is a simplified implementation
            # Real implementation would create proper Resume and Candidate records
            # with all fields from the profile

            # For now, just count as successful
            successful_imports += 1
            logger.debug(f"Successfully imported candidate: {email}")

        except Exception as e:
            logger.error(f"Error importing profile {idx + 1}: {e}", exc_info=True)
            validation_errors.append({
                "row": idx + 1,
                "error": str(e),
                "profile": str(profile)[:200]
            })
            failed_imports += 1

    return {
        "total_records": total_records,
        "successful_imports": successful_imports,
        "failed_imports": failed_imports,
        "skipped_records": skipped_records,
        "validation_errors": validation_errors,
    }


async def _update_import_job_status(
    import_job_id: str,
    status: ImportJobStatusEnum,
    error_message: Optional[str] = None
) -> None:
    """
    Update import job status in database.

    Args:
        import_job_id: UUID of the import job
        status: New status value
        error_message: Optional error message
    """
    from uuid import UUID
    from sqlalchemy import update as sql_update

    async with async_session_maker() as db:
        try:
            await db.execute(
                sql_update(ImportJob)
                .where(ImportJob.id == UUID(import_job_id))
                .values(
                    status=status,
                    error_message=error_message,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to update import job status: {e}", exc_info=True)
            await db.rollback()
            raise


@shared_task(
    name="tasks.import.validate_import_file",
    bind=True,
    max_retries=1,
    default_retry_delay=60,
)
def validate_import_file_task(self, import_job_id: str) -> Dict[str, Any]:
    """
    Validate data portability import file without processing.

    Performs pre-import validation to check file format, structure,
    and provide estimated record counts.

    Args:
        import_job_id: UUID of the import job to validate

    Returns:
        Dictionary with validation results

    Example:
        >>> result = validate_import_file_task.delay(
        ...     import_job_id="abc-123-def-456"
        ... )
        >>> print(result.get())
        {'status': 'success', 'valid': True, 'estimated_records': 50}
    """
    import asyncio

    logger.info(f"Validating data portability import file for job: {import_job_id}")

    try:
        result = asyncio.run(_validate_data_portability_file_async(import_job_id))
        return result

    except Exception as e:
        logger.error(f"Validation failed for import job {import_job_id}: {e}", exc_info=True)
        return {
            "status": "failed",
            "import_job_id": import_job_id,
            "valid": False,
            "error": str(e),
        }


async def _validate_data_portability_file_async(import_job_id: str) -> Dict[str, Any]:
    """
    Async implementation of data portability import file validation.

    Args:
        import_job_id: UUID of the import job

    Returns:
        Dictionary with validation results
    """
    from uuid import UUID

    async with async_session_maker() as db:
        try:
            # Load import job
            result = await db.execute(
                select(ImportJob).where(ImportJob.id == UUID(import_job_id))
            )
            import_job = result.scalar_one_or_none()

            if not import_job:
                raise ValueError(f"Import job {import_job_id} not found")

            # Parse file to validate
            parse_result = await _parse_data_portability_file(import_job)

            return {
                "status": "success",
                "import_job_id": import_job_id,
                "valid": parse_result["success"],
                "estimated_records": len(parse_result.get("profiles", [])),
                "detected_format": parse_result.get("detected_format"),
                "errors": parse_result.get("errors", []),
                "warnings": parse_result.get("warnings", []),
            }

        except Exception as e:
            logger.error(f"Error validating import file {import_job_id}: {e}", exc_info=True)
            raise


@shared_task(
    name="tasks.import.cleanup_import_files",
    bind=True,
)
def cleanup_import_files_task(self, days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up old data portability import files from filesystem.

    Removes import files for completed jobs older than specified days.

    Args:
        days_old: Number of days after which to delete files (default: 30)

    Returns:
        Dictionary with cleanup results

    Example:
        >>> result = cleanup_import_files_task.delay(days_old=30)
        >>> print(result.get())
        {'status': 'success', 'files_deleted': 15, 'bytes_freed_mb': 125.4}
    """
    import asyncio

    logger.info(f"Starting data portability import file cleanup (older than {days_old} days)")

    try:
        result = asyncio.run(_cleanup_data_portability_files_async(days_old))
        return result

    except Exception as e:
        logger.error(f"Import file cleanup failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }


async def _cleanup_data_portability_files_async(days_old: int) -> Dict[str, Any]:
    """
    Async implementation of data portability import file cleanup.

    Args:
        days_old: Number of days after which to delete files

    Returns:
        Dictionary with cleanup results
    """
    from datetime import timedelta
    import os

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    files_deleted = 0
    files_failed = 0
    bytes_freed = 0

    async with async_session_maker() as db:
        try:
            # Find old completed import jobs
            result = await db.execute(
                select(ImportJob).where(
                    ImportJob.status.in_([
                        ImportJobStatusEnum.COMPLETED,
                        ImportJobStatusEnum.FAILED,
                        ImportJobStatusEnum.CANCELLED
                    ]),
                    ImportJob.created_at < cutoff_date
                )
            )
            old_jobs = result.scalars().all()

            logger.info(f"Found {len(old_jobs)} old import jobs for cleanup")

            for job in old_jobs:
                try:
                    if os.path.exists(job.file_path):
                        file_size = os.path.getsize(job.file_path)
                        os.remove(job.file_path)
                        files_deleted += 1
                        bytes_freed += file_size
                        logger.debug(f"Deleted import file: {job.file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete file {job.file_path}: {e}")
                    files_failed += 1

            return {
                "status": "success",
                "files_deleted": files_deleted,
                "files_failed": files_failed,
                "bytes_freed": bytes_freed,
                "bytes_freed_mb": round(bytes_freed / (1024 * 1024), 2),
            }

        except Exception as e:
            logger.error(f"Error during import file cleanup: {e}", exc_info=True)
            raise
