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
