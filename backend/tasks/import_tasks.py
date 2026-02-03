"""
Job board import tasks for polling and processing applicants.

This module provides Celery tasks for importing applicants from job boards
like Indeed, ZipRecruiter, and Glassdoor. It handles polling for new applicants,
processing imported resumes, duplicate detection, and periodic scheduled imports.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models import JobBoardIntegration, ImportLog, ImportJobStatus

logger = logging.getLogger(__name__)
settings = get_settings()


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
