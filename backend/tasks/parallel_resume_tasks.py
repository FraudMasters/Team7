"""
Parallel resume processing tasks using Celery primitives.

This module provides Celery tasks for parallel batch resume analysis
using Celery groups and chords. Multiple resumes are processed concurrently
instead of sequentially, significantly reducing batch processing time.
"""
import logging
import time
from typing import Dict, Any, List, Optional

from celery import shared_task, group
from celery.exceptions import SoftTimeLimitExceeded
from celery.result import GroupResult, allow_join_result

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Import core analysis function from analysis_task
# We import this way to allow both sync usage and Celery task wrapping
def _get_analysis_core():
    """Lazy import of analyze_resume_core to avoid circular imports."""
    from tasks.analysis_task import analyze_resume_core
    return analyze_resume_core


@shared_task(
    name="tasks.parallel_resume_tasks._analyze_single_resume",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def _analyze_single_resume(
    self,
    resume_id: str,
    check_grammar: bool = True,
    extract_experience: bool = True,
    detect_errors: bool = True,
) -> Dict[str, Any]:
    """
    Analyze a single resume as part of a parallel batch.

    This is a private Celery task that wraps the core analysis function
    for use in parallel groups. It includes retry logic and proper error handling.

    Args:
        self: Celery task instance (bind=True)
        resume_id: Unique identifier of the resume to analyze
        check_grammar: Whether to perform grammar checking
        extract_experience: Whether to calculate experience
        detect_errors: Whether to detect resume errors

    Returns:
        Dictionary containing analysis results

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For analysis errors (with retry)
    """
    start_time = time.time()

    try:
        logger.info(f"[Parallel Task] Analyzing resume: {resume_id}")

        # Get core analysis function
        analyze_resume_core = _get_analysis_core()

        # Call core analysis function
        result = analyze_resume_core(
            resume_id=resume_id,
            check_grammar=check_grammar,
            extract_experience=extract_experience,
            detect_errors=detect_errors,
        )

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        # Add metadata about this parallel execution
        result["parallel_processing_time_ms"] = processing_time_ms
        result["task_id"] = self.request.id

        logger.info(
            f"[Parallel Task] Completed resume {resume_id} in {processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"[Parallel Task] Resume {resume_id} exceeded time limit")
        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": "Analysis exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "task_id": self.request.id,
        }

    except Exception as e:
        logger.error(
            f"[Parallel Task] Failed to analyze resume {resume_id}: {e}",
            exc_info=True
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            logger.info(
                f"[Parallel Task] Retrying resume {resume_id}, "
                f"attempt {self.request.retries + 1}/{self.max_retries}"
            )
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "task_id": self.request.id,
        }


@shared_task(
    name="tasks.parallel_resume_tasks.parallel_batch_analyze_resumes",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
)
def parallel_batch_analyze_resumes(
    self,
    resume_ids: List[str],
    check_grammar: bool = True,
    extract_experience: bool = True,
    detect_errors: bool = True,
    batch_size: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Analyze multiple resumes in parallel using Celery groups.

    This Celery task processes multiple resumes concurrently using Celery's
    group primitive. Instead of processing resumes sequentially, all resumes
    are analyzed in parallel, significantly reducing total processing time.

    Key Features:
    - Uses Celery group for parallel execution
    - Supports configurable batch size to control concurrency
    - Aggregates results from all parallel tasks
    - Provides progress tracking at batch level
    - Handles individual failures without stopping entire batch
    - Returns sorted results matching input order

    Args:
        self: Celery task instance (bind=True)
        resume_ids: List of resume identifiers to analyze in parallel
        check_grammar: Whether to perform grammar checking (default: True)
        extract_experience: Whether to calculate experience (default: True)
        detect_errors: Whether to detect resume errors (default: True)
        batch_size: Maximum number of resumes to process in parallel.
                    If None, processes all resumes in one batch.
                    If set, divides resumes into chunks of this size.

    Returns:
        Dictionary containing batch analysis results:
        - total_resumes: Total number of resumes to process
        - successful: Number of successfully analyzed resumes
        - failed: Number of failed analyses
        - results: List of individual analysis results (sorted by input order)
        - batch_size: Number of resumes processed in each parallel batch
        - num_batches: Number of parallel batches executed
        - processing_time_ms: Total batch processing time
        - status: Overall task status (completed/failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For group execution errors

    Example:
        >>> from tasks.parallel_resume_tasks import parallel_batch_analyze_resumes
        >>> task = parallel_batch_analyze_resumes.delay(
        ...     resume_ids=["abc123", "def456", "ghi789"],
        ...     batch_size=5
        ... )
        >>> result = task.get()
        >>> print(result['successful'])
        3
        >>> print(result['processing_time_ms'])
        1234.56
    """
    batch_start_time = time.time()

    try:
        logger.info(
            f"Starting parallel batch analysis for {len(resume_ids)} resumes, "
            f"batch_size={batch_size}"
        )

        # Validate input
        if not resume_ids:
            logger.warning("Empty resume_ids list provided")
            return {
                "total_resumes": 0,
                "successful": 0,
                "failed": 0,
                "results": [],
                "batch_size": 0,
                "num_batches": 0,
                "processing_time_ms": 0,
                "status": "completed",
                "message": "No resumes to process",
            }

        # Step 1: Preparing parallel tasks
        progress = {
            "current": 1,
            "total": 3,
            "percentage": 33,
            "status": "preparing",
            "message": f"Preparing parallel analysis for {len(resume_ids)} resumes...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Preparing parallel tasks")

        # Determine batch size
        if batch_size is None:
            batch_size = len(resume_ids)
        elif batch_size < 1:
            batch_size = 1

        # Split resumes into batches
        resume_batches = [
            resume_ids[i:i + batch_size]
            for i in range(0, len(resume_ids), batch_size)
        ]
        num_batches = len(resume_batches)

        logger.info(
            f"Split {len(resume_ids)} resumes into {num_batches} batch(es) "
            f"of max size {batch_size}"
        )

        # Step 2: Execute parallel batches
        progress = {
            "current": 2,
            "total": 3,
            "percentage": 66,
            "status": "processing",
            "message": f"Processing {num_batches} parallel batch(es)...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Executing parallel tasks")

        all_results = []
        total_successful = 0
        total_failed = 0

        # Process each batch in parallel
        for batch_idx, batch in enumerate(resume_batches):
            batch_start = time.time()

            logger.info(
                f"Processing batch {batch_idx + 1}/{num_batches} "
                f"({len(batch)} resumes)"
            )

            # Create a Celery group for parallel execution
            # Each resume in the batch gets its own task
            parallel_tasks = group(
                _analyze_single_resume.s(
                    resume_id=resume_id,
                    check_grammar=check_grammar,
                    extract_experience=extract_experience,
                    detect_errors=detect_errors,
                )
                for resume_id in batch
            )

            # Execute the group and wait for results
            # allow_join_result() allows joining even if result backend is disabled
            with allow_join_result():
                group_result: GroupResult = parallel_tasks()

                # Wait for all tasks in the group to complete
                # This blocks until all parallel tasks finish
                batch_results = group_result.get()

            # Aggregate results
            for result in batch_results:
                all_results.append(result)

                if result.get("status") == "completed":
                    total_successful += 1
                else:
                    total_failed += 1

            batch_time = round((time.time() - batch_start) * 1000, 2)
            logger.info(
                f"Batch {batch_idx + 1}/{num_batches} completed in {batch_time}ms: "
                f"{sum(1 for r in batch_results if r.get('status') == 'completed')}/{len(batch)} successful"
            )

        # Step 3: Complete and return results
        progress = {
            "current": 3,
            "total": 3,
            "percentage": 100,
            "status": "complete",
            "message": "Parallel batch analysis complete",
        }
        self.update_state(state="PROGRESS", meta=progress)

        processing_time_ms = round((time.time() - batch_start_time) * 1000, 2)

        result = {
            "total_resumes": len(resume_ids),
            "successful": total_successful,
            "failed": total_failed,
            "results": all_results,
            "batch_size": batch_size,
            "num_batches": num_batches,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Parallel batch analysis completed: {total_successful} successful, "
            f"{total_failed} failed, time: {processing_time_ms}ms, "
            f"batches: {num_batches}"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "total_resumes": len(resume_ids),
            "successful": total_successful,
            "failed": total_failed,
            "results": all_results,
            "batch_size": batch_size or len(resume_ids),
            "num_batches": len(resume_batches) if 'resume_batches' in locals() else 0,
            "processing_time_ms": round((time.time() - batch_start_time) * 1000, 2),
            "status": "failed",
            "error": "Parallel batch analysis exceeded maximum time limit",
        }

    except Exception as e:
        logger.error(
            f"Error in parallel batch analysis: {e}",
            exc_info=True
        )
        return {
            "total_resumes": len(resume_ids),
            "successful": total_successful,
            "failed": total_failed,
            "results": all_results,
            "batch_size": batch_size or len(resume_ids),
            "num_batches": len(resume_batches) if 'resume_batches' in locals() else 0,
            "processing_time_ms": round((time.time() - batch_start_time) * 1000, 2),
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    name="tasks.parallel_resume_tasks.batch_analyze_with_screening",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
)
def batch_analyze_with_screening(
    self,
    resume_ids: List[str],
    vacancy_id: Optional[str] = None,
    check_grammar: bool = True,
    extract_experience: bool = True,
    batch_size: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Analyze resumes in parallel and optionally screen against vacancies.

    This is a convenience task that combines parallel batch analysis with
    automatic candidate screening. It first analyzes all resumes in parallel,
    then triggers screening for each successfully analyzed resume.

    Task Workflow:
    1. Analyze all resumes in parallel using parallel_batch_analyze_resumes
    2. Filter successfully analyzed resumes
    3. For each successful analysis, trigger auto_screen_candidate task
    4. Return combined analysis and screening results

    Args:
        self: Celery task instance (bind=True)
        resume_ids: List of resume identifiers to analyze and screen
        vacancy_id: Optional specific vacancy UUID to screen against.
                    If not provided, screens against all active vacancies.
        check_grammar: Whether to perform grammar checking (default: True)
        extract_experience: Whether to calculate experience (default: True)
        batch_size: Maximum number of resumes to process in parallel.

    Returns:
        Dictionary containing combined results:
        - total_resumes: Total number of resumes to process
        - analysis_results: Parallel batch analysis results
        - screening_results: Screening results per resume
        - processing_time_ms: Total processing time
        - status: Overall task status

    Example:
        >>> from tasks.parallel_resume_tasks import batch_analyze_with_screening
        >>> task = batch_analyze_with_screening.delay(
        ...     resume_ids=["abc123", "def456"],
        ...     vacancy_id="vac-789"
        ... )
        >>> result = task.get()
        >>> print(result['analysis_results']['successful'])
        2
    """
    start_time = time.time()

    try:
        logger.info(
            f"Starting batch analyze with screening for {len(resume_ids)} resumes, "
            f"vacancy_id={vacancy_id}"
        )

        # Step 1: Parallel analyze all resumes
        progress = {
            "current": 1,
            "total": 2,
            "percentage": 50,
            "status": "analyzing",
            "message": f"Analyzing {len(resume_ids)} resumes in parallel...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        # Import task to avoid circular dependency
        from tasks.screening_tasks import auto_screen_candidate

        # Run parallel batch analysis (synchronous - it's already wrapped in Celery)
        analysis_result = parallel_batch_analyze_resumes(
            resume_ids=resume_ids,
            check_grammar=check_grammar,
            extract_experience=extract_experience,
            detect_errors=True,
            batch_size=batch_size,
        )

        # Step 2: Screen successful resumes
        progress = {
            "current": 2,
            "total": 2,
            "percentage": 75,
            "status": "screening",
            "message": "Screening analyzed resumes...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        screening_results = []
        successfully_analyzed = []

        # Extract successfully analyzed resume IDs
        for result in analysis_result.get("results", []):
            if result.get("status") == "completed":
                successfully_analyzed.append(result["resume_id"])

        logger.info(
            f"Triggering screening for {len(successfully_analyzed)} "
            f"successfully analyzed resumes"
        )

        # Trigger screening for each successful resume
        # We use Celery's delay() to trigger these as separate async tasks
        for resume_id in successfully_analyzed:
            try:
                screening_task = auto_screen_candidate.delay(
                    resume_id=resume_id,
                    vacancy_id=vacancy_id,
                )
                screening_results.append({
                    "resume_id": resume_id,
                    "screening_task_id": screening_task.id,
                    "status": "screening_triggered",
                })
            except Exception as e:
                logger.error(f"Failed to trigger screening for {resume_id}: {e}")
                screening_results.append({
                    "resume_id": resume_id,
                    "status": "screening_failed",
                    "error": str(e),
                })

        # Complete
        progress = {
            "current": 2,
            "total": 2,
            "percentage": 100,
            "status": "complete",
            "message": "Analysis and screening triggered",
        }
        self.update_state(state="PROGRESS", meta=progress)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "total_resumes": len(resume_ids),
            "analysis_results": analysis_result,
            "screening_results": screening_results,
            "screening_triggered_count": len(successfully_analyzed),
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Batch analyze with screening completed: "
            f"{len(successfully_analyzed)} screenings triggered, "
            f"time: {processing_time_ms}ms"
        )

        return result

    except Exception as e:
        logger.error(f"Error in batch analyze with screening: {e}", exc_info=True)
        return {
            "total_resumes": len(resume_ids),
            "analysis_results": analysis_result if 'analysis_result' in locals() else {},
            "screening_results": screening_results if 'screening_results' in locals() else [],
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "status": "failed",
            "error": str(e),
        }
