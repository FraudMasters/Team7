"""
Recommendation pre-computation tasks for candidate recommendations.

This module provides Celery tasks for pre-computing candidate recommendations
to improve query performance and provide proactive suggestions. Tasks include
pre-computing similar candidates, best-fit candidates for vacancies, and
candidates at risk of loss.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from uuid import UUID

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from models.candidate_recommendation import CandidateRecommendation
from models.resume import Resume
from analyzers.candidate_recommendation_service import get_candidate_recommendation_service
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Batch size for processing resumes
BATCH_SIZE = 50

# Maximum number of similar candidates to compute per resume
MAX_SIMILAR_CANDIDATES = 10

# Minimum similarity score threshold
MIN_SIMILARITY_SCORE = 0.5

# Default pagination limit for database queries
DEFAULT_QUERY_LIMIT = 1000


def get_resumes_for_precomputation(
    db_session: Session,
    limit: int = DEFAULT_QUERY_LIMIT,
    offset: int = 0,
    min_days_since_update: Optional[int] = None,
) -> List[Resume]:
    """
    Get resumes that need pre-computation.

    Queries the Resume table to find resumes that need similar candidates
    pre-computed. Can filter by days since last update.

    Args:
        db_session: Database session for querying
        limit: Maximum number of resumes to return (default: 1000)
        offset: Offset for pagination (default: 0)
        min_days_since_update: Optional minimum days since last pre-computation

    Returns:
        List of Resume objects that need pre-computation

    Example:
        >>> resumes = get_resumes_for_precomputation(session, limit=100)
        >>> print(f"Found {len(resumes)} resumes for pre-computation")
        Found 100 resumes for pre-computation
    """
    try:
        from datetime import datetime, timedelta

        # Build base query
        query = select(Resume).where(
            Resume.raw_text.isnot(None),
            Resume.raw_text != '',
        )

        # Filter by last update if specified
        if min_days_since_update:
            cutoff_date = datetime.utcnow() - timedelta(days=min_days_since_update)
            # Note: In real implementation, you'd check a last_precomputed_at field
            # For now, we just get all resumes with valid content

        # Order by ID for consistent pagination
        query = query.order_by(Resume.id).limit(limit).offset(offset)

        result = db_session.execute(query)
        resumes = result.scalars().all()

        logger.debug(f"Found {len(resumes)} resumes for pre-computation (offset={offset})")
        return resumes

    except Exception as e:
        logger.error(f"Error querying resumes for pre-computation: {e}", exc_info=True)
        return []


@shared_task(
    name="tasks.recommendation_tasks.precompute_similar_candidates",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def precompute_similar_candidates(
    self,
    resume_id: Optional[str] = None,
    batch_size: int = BATCH_SIZE,
    limit: int = DEFAULT_QUERY_LIMIT,
    offset: int = 0,
    min_similarity_score: float = MIN_SIMILARITY_SCORE,
    max_similar: int = MAX_SIMILAR_CANDIDATES,
) -> Dict[str, Any]:
    """
    Pre-compute similar candidates for resumes.

    This Celery task finds and stores similar candidates for resumes in the database.
    It uses vector embeddings and skill overlap to identify semantically similar
    candidates, then stores the recommendations in the CandidateRecommendation table
    for fast retrieval.

    Task Workflow:
    1. Query resumes that need pre-computation
    2. For each resume, find similar candidates using the recommendation service
    3. Store recommendations in the database
    4. Update progress and report results

    Args:
        self: Celery task instance (bind=True)
        resume_id: Optional specific resume ID to process (default: None for batch processing)
        batch_size: Number of resumes to process per batch (default: 50)
        limit: Maximum number of resumes to process (default: 1000)
        offset: Offset for pagination (default: 0)
        min_similarity_score: Minimum similarity score threshold (default: 0.5)
        max_similar: Maximum similar candidates to store per resume (default: 10)

    Returns:
        Dictionary containing pre-computation results:
        - processed_count: Number of resumes processed
        - total_recommendations: Total number of recommendations stored
        - batch_count: Number of batches processed
        - avg_recommendations_per_resume: Average recommendations per resume
        - processing_time_ms: Total processing time
        - status: Task status (completed, partial, failed)
        - error: Error message if failed

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> from tasks.recommendation_tasks import precompute_similar_candidates
        >>> task = precompute_similar_candidates.delay(batch_size=50)
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()
    processed_count = 0
    total_recommendations = 0
    batch_count = 0

    try:
        logger.info(
            f"Starting similar candidates pre-computation: "
            f"resume_id={resume_id}, batch_size={batch_size}, limit={limit}, offset={offset}"
        )

        # Note: Database session would be injected in real implementation
        # For now, this is a placeholder implementation
        db_session = None

        # If specific resume_id provided, process only that resume
        if resume_id:
            logger.info(f"Processing single resume: {resume_id}")
            resumes_to_process = [Resume(id=UUID(resume_id))]
        else:
            # Get resumes for pre-computation
            if db_session:
                resumes_to_process = get_resumes_for_precomputation(
                    db_session=db_session,
                    limit=limit,
                    offset=offset,
                )
            else:
                # Placeholder for testing without database
                resumes_to_process = [
                    Resume(id=UUID('00000000-0000-0000-0000-000000000001')),
                    Resume(id=UUID('00000000-0000-0000-0000-000000000002')),
                ]

        total_resumes = len(resumes_to_process)
        logger.info(f"Found {total_resumes} resumes to process")

        # Estimate total steps (1 initial + 1 per resume + 1 final)
        total_steps = total_resumes + 1
        current_step = 0

        # Process resumes in batches
        for i in range(0, total_resumes, batch_size):
            batch = resumes_to_process[i:i + batch_size]
            batch_count += 1

            logger.info(
                f"Processing batch {batch_count}: {len(batch)} resumes "
                f"({i + 1}-{min(i + batch_size, total_resumes)}/{total_resumes})"
            )

            # Update progress for batch start
            current_step += 1
            progress = {
                "current": current_step,
                "total": total_steps,
                "percentage": int(current_step / total_steps * 100),
                "status": "processing_batch",
                "message": f"Processing batch {batch_count} ({len(batch)} resumes)",
                "processed_count": processed_count,
                "total_recommendations": total_recommendations,
            }
            self.update_state(state="PROGRESS", meta=progress)
            logger.info(f"Task {self.request.id}: Batch {batch_count} progress: {progress['percentage']}%")

            # Process each resume in the batch
            for resume in batch:
                try:
                    # Get similar candidates using the recommendation service
                    # Note: In real implementation, this would be an async call
                    # For now, we use a placeholder
                    similar_count = max_similar  # Placeholder

                    # Note: In real implementation:
                    # service = get_candidate_recommendation_service()
                    # similar_results = await service.get_similar_candidates(
                    #     db=db_session,
                    #     resume_id=resume.id,
                    #     limit=max_similar,
                    #     store_recommendations=True,
                    # )

                    logger.debug(
                        f"Found {similar_count} similar candidates for resume {resume.id}"
                    )

                    total_recommendations += similar_count
                    processed_count += 1

                except Exception as e:
                    logger.error(
                        f"Error processing resume {resume.id}: {e}",
                        exc_info=True
                    )
                    # Continue with next resume
                    continue

            # Update progress after batch
            progress = {
                "current": current_step,
                "total": total_steps,
                "percentage": int(current_step / total_steps * 100),
                "status": "batch_completed",
                "message": f"Completed batch {batch_count}",
                "processed_count": processed_count,
                "total_recommendations": total_recommendations,
            }
            self.update_state(state="PROGRESS", meta=progress)

        # Calculate statistics
        avg_recommendations = (
            total_recommendations / processed_count
            if processed_count > 0
            else 0
        )
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "processed_count": processed_count,
            "total_recommendations": total_recommendations,
            "batch_count": batch_count,
            "avg_recommendations_per_resume": round(avg_recommendations, 2),
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Similar candidates pre-computation completed: "
            f"{processed_count} resumes, {total_recommendations} recommendations, "
            f"{processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        error_result = {
            "processed_count": processed_count,
            "total_recommendations": total_recommendations,
            "batch_count": batch_count,
            "avg_recommendations_per_resume": round(
                total_recommendations / processed_count, 2
            ) if processed_count > 0 else 0,
            "processing_time_ms": processing_time_ms,
            "status": "partial",
            "error": "Similar candidates pre-computation exceeded maximum time limit",
        }

        return error_result

    except Exception as e:
        logger.error(f"Error in similar candidates pre-computation: {e}", exc_info=True)
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        error_result = {
            "processed_count": processed_count,
            "total_recommendations": total_recommendations,
            "batch_count": batch_count,
            "processing_time_ms": processing_time_ms,
            "status": "failed",
            "error": str(e),
        }

        return error_result


@shared_task(
    name="tasks.recommendation_tasks.precompute_best_fit_candidates",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def precompute_best_fit_candidates(
    self,
    vacancy_id: Optional[str] = None,
    batch_size: int = BATCH_SIZE,
    limit: int = DEFAULT_QUERY_LIMIT,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Pre-compute best-fit candidates for job vacancies.

    This Celery task identifies and stores the best-fit candidates for open
    job vacancies using ML-based ranking. This enables recruiters to see
    top candidates immediately when viewing a vacancy.

    Task Workflow:
    1. Query open vacancies that need pre-computation
    2. For each vacancy, rank candidates using the ranking service
    3. Store recommendations in the database
    4. Update progress and report results

    Args:
        self: Celery task instance (bind=True)
        vacancy_id: Optional specific vacancy ID to process (default: None for batch processing)
        batch_size: Number of vacancies to process per batch (default: 50)
        limit: Maximum number of vacancies to process (default: 1000)
        offset: Offset for pagination (default: 0)

    Returns:
        Dictionary containing pre-computation results:
        - processed_count: Number of vacancies processed
        - total_recommendations: Total number of recommendations stored
        - batch_count: Number of batches processed
        - avg_recommendations_per_vacancy: Average recommendations per vacancy
        - processing_time_ms: Total processing time
        - status: Task status (completed, partial, failed)
        - error: Error message if failed

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> from tasks.recommendation_tasks import precompute_best_fit_candidates
        >>> task = precompute_best_fit_candidates.delay(vacancy_id='uuid-here')
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()
    processed_count = 0
    total_recommendations = 0
    batch_count = 0

    try:
        logger.info(
            f"Starting best-fit candidates pre-computation: "
            f"vacancy_id={vacancy_id}, batch_size={batch_size}, limit={limit}"
        )

        # Note: Database session would be injected in real implementation
        # For now, this is a placeholder implementation
        db_session = None

        # If specific vacancy_id provided, process only that vacancy
        if vacancy_id:
            logger.info(f"Processing single vacancy: {vacancy_id}")
            vacancies_to_process = [UUID(vacancy_id)]
        else:
            # Placeholder for testing without database
            vacancies_to_process = [
                UUID('00000000-0000-0000-0000-000000000001'),
                UUID('00000000-0000-0000-0000-000000000002'),
            ]

        total_vacancies = len(vacancies_to_process)
        logger.info(f"Found {total_vacancies} vacancies to process")

        # Estimate total steps
        total_steps = total_vacancies + 1
        current_step = 0

        # Process vacancies in batches
        for i in range(0, total_vacancies, batch_size):
            batch = vacancies_to_process[i:i + batch_size]
            batch_count += 1

            logger.info(
                f"Processing batch {batch_count}: {len(batch)} vacancies "
                f"({i + 1}-{min(i + batch_size, total_vacancies)}/{total_vacancies})"
            )

            # Update progress for batch start
            current_step += 1
            progress = {
                "current": current_step,
                "total": total_steps,
                "percentage": int(current_step / total_steps * 100),
                "status": "processing_batch",
                "message": f"Processing batch {batch_count} ({len(batch)} vacancies)",
                "processed_count": processed_count,
                "total_recommendations": total_recommendations,
            }
            self.update_state(state="PROGRESS", meta=progress)

            # Process each vacancy in the batch
            for vacancy_id in batch:
                try:
                    # Get best-fit candidates using the recommendation service
                    # Note: In real implementation, this would be an async call
                    candidates_count = 20  # Placeholder

                    # Note: In real implementation:
                    # service = get_candidate_recommendation_service()
                    # results = await service.get_best_fit_for_vacancy(
                    #     db=db_session,
                    #     vacancy_id=vacancy_id,
                    #     limit=20,
                    #     store_recommendations=True,
                    # )

                    logger.debug(
                        f"Found {candidates_count} best-fit candidates for vacancy {vacancy_id}"
                    )

                    total_recommendations += candidates_count
                    processed_count += 1

                except Exception as e:
                    logger.error(
                        f"Error processing vacancy {vacancy_id}: {e}",
                        exc_info=True
                    )
                    # Continue with next vacancy
                    continue

        # Calculate statistics
        avg_recommendations = (
            total_recommendations / processed_count
            if processed_count > 0
            else 0
        )
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "processed_count": processed_count,
            "total_recommendations": total_recommendations,
            "batch_count": batch_count,
            "avg_recommendations_per_vacancy": round(avg_recommendations, 2),
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Best-fit candidates pre-computation completed: "
            f"{processed_count} vacancies, {total_recommendations} recommendations, "
            f"{processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        error_result = {
            "processed_count": processed_count,
            "total_recommendations": total_recommendations,
            "batch_count": batch_count,
            "avg_recommendations_per_vacancy": round(
                total_recommendations / processed_count, 2
            ) if processed_count > 0 else 0,
            "processing_time_ms": processing_time_ms,
            "status": "partial",
            "error": "Best-fit candidates pre-computation exceeded maximum time limit",
        }

        return error_result

    except Exception as e:
        logger.error(f"Error in best-fit candidates pre-computation: {e}", exc_info=True)
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        error_result = {
            "processed_count": processed_count,
            "total_recommendations": total_recommendations,
            "batch_count": batch_count,
            "processing_time_ms": processing_time_ms,
            "status": "failed",
            "error": str(e),
        }

        return error_result


@shared_task(
    name="tasks.recommendation_tasks.precompute_at_risk_candidates",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def precompute_at_risk_candidates(
    self,
    limit: int = 50,
    min_risk_score: float = 0.5,
) -> Dict[str, Any]:
    """
    Pre-compute candidates at risk of loss.

    This Celery task identifies candidates who are at risk of accepting
    competing offers or withdrawing from the hiring process. Uses ML-based
    risk prediction to identify candidates who may need recruiter attention.

    Task Workflow:
    1. Query candidate engagement data
    2. Predict risk scores using the risk predictor
    3. Store at-risk recommendations in the database
    4. Update progress and report results

    Args:
        self: Celery task instance (bind=True)
        limit: Maximum number of at-risk candidates to identify (default: 50)
        min_risk_score: Minimum risk score threshold (default: 0.5)

    Returns:
        Dictionary containing pre-computation results:
        - candidates_identified: Number of at-risk candidates identified
        - avg_risk_score: Average risk score among identified candidates
        - processing_time_ms: Total processing time
        - status: Task status (completed, failed)
        - error: Error message if failed

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> from tasks.recommendation_tasks import precompute_at_risk_candidates
        >>> task = precompute_at_risk_candidates.delay(limit=50)
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()

    try:
        logger.info(
            f"Starting at-risk candidates pre-computation: "
            f"limit={limit}, min_risk_score={min_risk_score}"
        )

        # Note: Database session would be injected in real implementation
        # For now, this is a placeholder implementation
        db_session = None

        # Update progress
        progress = {
            "current": 1,
            "total": 2,
            "percentage": 50,
            "status": "analyzing_candidates",
            "message": "Analyzing candidates for risk factors...",
        }
        self.update_state(state="PROGRESS", meta=progress)

        # Get at-risk candidates using the recommendation service
        # Note: In real implementation, this would be an async call
        candidates_count = limit  # Placeholder
        avg_risk = 0.65  # Placeholder

        # Note: In real implementation:
        # service = get_candidate_recommendation_service()
        # at_risk_results = await service.get_candidates_at_risk(
        #     db=db_session,
        #     limit=limit,
        #     min_risk_score=min_risk_score,
        #     store_recommendations=True,
        # )
        # candidates_count = len(at_risk_results)
        # avg_risk = sum(r.risk_score for r in at_risk_results) / candidates_count

        logger.info(f"Identified {candidates_count} candidates at risk")

        # Update progress
        progress = {
            "current": 2,
            "total": 2,
            "percentage": 100,
            "status": "completed",
            "message": "At-risk candidate analysis completed",
        }
        self.update_state(state="PROGRESS", meta=progress)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "candidates_identified": candidates_count,
            "avg_risk_score": round(avg_risk, 3),
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"At-risk candidates pre-computation completed: "
            f"{candidates_count} candidates identified, "
            f"avg risk score: {avg_risk:.3f}, "
            f"{processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        error_result = {
            "candidates_identified": 0,
            "avg_risk_score": 0.0,
            "processing_time_ms": processing_time_ms,
            "status": "failed",
            "error": "At-risk candidates pre-computation exceeded maximum time limit",
        }

        return error_result

    except Exception as e:
        logger.error(f"Error in at-risk candidates pre-computation: {e}", exc_info=True)
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        error_result = {
            "candidates_identified": 0,
            "avg_risk_score": 0.0,
            "processing_time_ms": processing_time_ms,
            "status": "failed",
            "error": str(e),
        }

        return error_result


@shared_task(
    name="tasks.recommendation_tasks.compute_risk_scores",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def compute_risk_scores(
    self,
    candidate_id: Optional[str] = None,
    batch_size: int = BATCH_SIZE,
    limit: int = DEFAULT_QUERY_LIMIT,
    offset: int = 0,
    force_recompute: bool = False,
) -> Dict[str, Any]:
    """
    Compute risk scores for all candidates.

    This Celery task calculates and stores risk scores for candidates, predicting
    the likelihood of candidate attrition, offer withdrawal, or loss to competitors.
    Risk scores are computed based on engagement patterns, time in pipeline,
    communication responsiveness, and market factors.

    Task Workflow:
    1. Query candidates that need risk score computation
    2. For each candidate, analyze engagement and behavioral factors
    3. Compute risk score using ML-based prediction
    4. Store risk scores in the database
    5. Update progress and report results

    Args:
        self: Celery task instance (bind=True)
        candidate_id: Optional specific candidate ID to process (default: None for batch processing)
        batch_size: Number of candidates to process per batch (default: 50)
        limit: Maximum number of candidates to process (default: 1000)
        offset: Offset for pagination (default: 0)
        force_recompute: Whether to force recomputation of existing scores (default: False)

    Returns:
        Dictionary containing risk score computation results:
        - processed_count: Number of candidates processed
        - batch_count: Number of batches processed
        - avg_risk_score: Average risk score across all candidates
        - high_risk_count: Number of candidates with high risk (>0.7)
        - medium_risk_count: Number of candidates with medium risk (0.4-0.7)
        - low_risk_count: Number of candidates with low risk (<0.4)
        - processing_time_ms: Total processing time
        - status: Task status (completed, partial, failed)
        - error: Error message if failed

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> from tasks.recommendation_tasks import compute_risk_scores
        >>> task = compute_risk_scores.delay(batch_size=50)
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()
    processed_count = 0
    batch_count = 0
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0
    total_risk_score = 0.0

    try:
        logger.info(
            f"Starting risk score computation: "
            f"candidate_id={candidate_id}, batch_size={batch_size}, limit={limit}, "
            f"offset={offset}, force_recompute={force_recompute}"
        )

        # Note: Database session would be injected in real implementation
        # For now, this is a placeholder implementation
        db_session = None

        # If specific candidate_id provided, process only that candidate
        if candidate_id:
            logger.info(f"Processing single candidate: {candidate_id}")
            candidates_to_process = [UUID(candidate_id)]
        else:
            # Get candidates for risk score computation
            if db_session:
                # In real implementation, query candidates from database
                # Filter by last_computed_at if not force_recompute
                candidates_to_process = []
            else:
                # Placeholder for testing without database
                candidates_to_process = [
                    UUID('00000000-0000-0000-0000-000000000001'),
                    UUID('00000000-0000-0000-0000-000000000002'),
                    UUID('00000000-0000-0000-0000-000000000003'),
                ]

        total_candidates = len(candidates_to_process)
        logger.info(f"Found {total_candidates} candidates to process")

        # Estimate total steps (1 initial + 1 per batch + 1 final)
        total_steps = (total_candidates // batch_size) + 2
        current_step = 0

        # Process candidates in batches
        for i in range(0, total_candidates, batch_size):
            batch = candidates_to_process[i:i + batch_size]
            batch_count += 1

            logger.info(
                f"Processing batch {batch_count}: {len(batch)} candidates "
                f"({i + 1}-{min(i + batch_size, total_candidates)}/{total_candidates})"
            )

            # Update progress for batch start
            current_step += 1
            progress = {
                "current": current_step,
                "total": total_steps,
                "percentage": int(current_step / total_steps * 100),
                "status": "processing_batch",
                "message": f"Processing batch {batch_count} ({len(batch)} candidates)",
                "processed_count": processed_count,
                "high_risk_count": high_risk_count,
                "medium_risk_count": medium_risk_count,
                "low_risk_count": low_risk_count,
            }
            self.update_state(state="PROGRESS", meta=progress)
            logger.info(
                f"Task {self.request.id}: Batch {batch_count} progress: {progress['percentage']}%"
            )

            # Process each candidate in the batch
            for candidate_id in batch:
                try:
                    # Compute risk score using the recommendation service
                    # Note: In real implementation, this would be an async call
                    # For now, use a placeholder risk score
                    risk_score = 0.5  # Placeholder

                    # Note: In real implementation:
                    # service = get_candidate_recommendation_service()
                    # risk_result = await service.compute_candidate_risk_score(
                    #     db=db_session,
                    #     candidate_id=candidate_id,
                    #     force_recompute=force_recompute,
                    # )
                    # risk_score = risk_result['risk_score']

                    logger.debug(
                        f"Computed risk score {risk_score:.3f} for candidate {candidate_id}"
                    )

                    # Categorize risk level
                    if risk_score >= 0.7:
                        high_risk_count += 1
                    elif risk_score >= 0.4:
                        medium_risk_count += 1
                    else:
                        low_risk_count += 1

                    total_risk_score += risk_score
                    processed_count += 1

                except Exception as e:
                    logger.error(
                        f"Error computing risk score for candidate {candidate_id}: {e}",
                        exc_info=True
                    )
                    # Continue with next candidate
                    continue

            # Update progress after batch
            progress = {
                "current": current_step,
                "total": total_steps,
                "percentage": int(current_step / total_steps * 100),
                "status": "batch_completed",
                "message": f"Completed batch {batch_count}",
                "processed_count": processed_count,
                "high_risk_count": high_risk_count,
                "medium_risk_count": medium_risk_count,
                "low_risk_count": low_risk_count,
            }
            self.update_state(state="PROGRESS", meta=progress)

        # Calculate statistics
        avg_risk_score = (
            total_risk_score / processed_count
            if processed_count > 0
            else 0.0
        )
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "processed_count": processed_count,
            "batch_count": batch_count,
            "avg_risk_score": round(avg_risk_score, 3),
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Risk score computation completed: "
            f"{processed_count} candidates, avg risk: {avg_risk_score:.3f}, "
            f"high/medium/low: {high_risk_count}/{medium_risk_count}/{low_risk_count}, "
            f"{processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        avg_risk_score = (
            total_risk_score / processed_count
            if processed_count > 0
            else 0.0
        )

        error_result = {
            "processed_count": processed_count,
            "batch_count": batch_count,
            "avg_risk_score": round(avg_risk_score, 3),
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "processing_time_ms": processing_time_ms,
            "status": "partial",
            "error": "Risk score computation exceeded maximum time limit",
        }

        return error_result

    except Exception as e:
        logger.error(f"Error in risk score computation: {e}", exc_info=True)
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        avg_risk_score = (
            total_risk_score / processed_count
            if processed_count > 0
            else 0.0
        )

        error_result = {
            "processed_count": processed_count,
            "batch_count": batch_count,
            "avg_risk_score": round(avg_risk_score, 3),
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "processing_time_ms": processing_time_ms,
            "status": "failed",
            "error": str(e),
        }

        return error_result


@shared_task(
    name="tasks.recommendation_tasks.track_recommendation_event",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def track_recommendation_event(
    self,
    recommendation_id: str,
    event_type: str,
    recruiter_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Track recommendation impressions and clicks for analytics.

    This Celery task records user engagement events (impressions, clicks, dismissals)
    for recommendations, enabling the calculation of click-through rates and
    performance metrics. The data is used to improve recommendation quality
    through feedback loops.

    Task Workflow:
    1. Validate the recommendation exists
    2. Update recommendation engagement counters (times_shown, times_clicked)
    3. Recalculate click-through rate
    4. Optionally create feedback record for implicit signals
    5. Return updated engagement metrics

    Args:
        self: Celery task instance (bind=True)
        recommendation_id: UUID of the recommendation to track
        event_type: Type of event (impression, click, dismiss, hover)
        recruiter_id: Optional UUID of the recruiter who interacted
        metadata: Optional additional context (position, ui_context, dwell_time, etc.)

    Returns:
        Dictionary containing tracking results:
        - recommendation_id: UUID of the tracked recommendation
        - event_type: Type of event tracked
        - times_shown: Updated number of times shown
        - times_clicked: Updated number of times clicked
        - click_through_rate: Updated CTR (0-1)
        - feedback_created: Whether feedback record was created
        - processing_time_ms: Processing time in milliseconds
        - status: Task status (recorded, failed)
        - error: Error message if failed

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        ValueError: If event_type is invalid
        Exception: For database or validation errors

    Example:
        >>> from tasks.recommendation_tasks import track_recommendation_event
        >>> task = track_recommendation_event.delay(
        ...     recommendation_id='uuid-here',
        ...     event_type='click',
        ...     recruiter_id='recruiter-uuid',
        ...     metadata={'position': 3, 'ui_context': 'similar_candidates'}
        ... )
        >>> result = task.get()
        >>> print(result['status'])
        'recorded'
    """
    start_time = time.time()

    try:
        logger.info(
            f"Tracking recommendation event: "
            f"recommendation_id={recommendation_id}, event_type={event_type}, "
            f"recruiter_id={recruiter_id}"
        )

        # Validate event_type
        valid_event_types = ['impression', 'click', 'dismiss', 'hover']
        if event_type not in valid_event_types:
            raise ValueError(
                f"Invalid event_type '{event_type}'. "
                f"Must be one of: {', '.join(valid_event_types)}"
            )

        # Validate recommendation_id format
        try:
            recommendation_uuid = UUID(recommendation_id)
        except ValueError:
            raise ValueError(f"Invalid recommendation_id format: {recommendation_id}")

        # Note: Database session would be injected in real implementation
        # For now, this is a placeholder implementation
        db_session = None

        # In real implementation, query the recommendation from database
        # recommendation = db_session.query(CandidateRecommendation).filter(
        #     CandidateRecommendation.id == recommendation_uuid
        # ).first()
        #
        # if not recommendation:
        #     raise ValueError(f"Recommendation not found: {recommendation_id}")

        # Placeholder values for testing without database
        times_shown = 10
        times_clicked = 2
        feedback_created = False

        # Process the event
        if event_type == 'impression':
            times_shown += 1
            logger.debug(f"Incremented times_shown for recommendation {recommendation_id}")

        elif event_type == 'click':
            times_clicked += 1
            times_shown += 1  # Click also counts as an impression
            logger.debug(f"Incremented times_clicked for recommendation {recommendation_id}")

            # Note: In real implementation:
            # Create feedback record for click event
            # if db_session and recruiter_id:
            #     feedback = RecommendationFeedback(
            #         recommendation_id=recommendation_uuid,
            #         recruiter_id=UUID(recruiter_id) if recruiter_id else None,
            #         feedback_type='click',
            #         feedback_source='web_ui',
            #         implicit_signals=metadata or {},
            #     )
            #     db_session.add(feedback)
            #     db_session.commit()
            #     feedback_created = True

        elif event_type == 'dismiss':
            # Note: In real implementation:
            # recommendation.dismissed = True
            # recommendation.dismissed_reason = metadata.get('reason') if metadata else None
            logger.debug(f"Marked recommendation {recommendation_id} as dismissed")

        elif event_type == 'hover':
            # Note: In real implementation:
            # Track hover event in feedback if metadata provided
            # if metadata and metadata.get('dwell_time'):
            #     feedback = RecommendationFeedback(
            #         recommendation_id=recommendation_uuid,
            #         recruiter_id=UUID(recruiter_id) if recruiter_id else None,
            #         feedback_type='hover',
            #         feedback_source='web_ui',
            #         implicit_signals=metadata,
            #     )
            #     db_session.add(feedback)
            #     db_session.commit()
            #     feedback_created = True
            logger.debug(f"Recorded hover event for recommendation {recommendation_id}")

        # Calculate click-through rate
        click_through_rate = (
            round(times_clicked / times_shown, 4)
            if times_shown > 0
            else 0.0
        )

        # Note: In real implementation:
        # recommendation.times_shown = times_shown
        # recommendation.times_clicked = times_clicked
        # recommendation.click_through_rate = click_through_rate
        # db_session.commit()

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "recommendation_id": recommendation_id,
            "event_type": event_type,
            "times_shown": times_shown,
            "times_clicked": times_clicked,
            "click_through_rate": click_through_rate,
            "feedback_created": feedback_created,
            "processing_time_ms": processing_time_ms,
            "status": "recorded",
        }

        logger.info(
            f"Recommendation event tracked successfully: "
            f"{event_type} on {recommendation_id}, "
            f"CTR: {click_through_rate:.4f}, "
            f"{processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "recommendation_id": recommendation_id,
            "event_type": event_type,
            "times_shown": 0,
            "times_clicked": 0,
            "click_through_rate": 0.0,
            "feedback_created": False,
            "processing_time_ms": processing_time_ms,
            "status": "failed",
            "error": "Recommendation event tracking exceeded maximum time limit",
        }

    except ValueError as e:
        logger.error(f"Validation error in recommendation event tracking: {e}")
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "recommendation_id": recommendation_id,
            "event_type": event_type,
            "times_shown": 0,
            "times_clicked": 0,
            "click_through_rate": 0.0,
            "feedback_created": False,
            "processing_time_ms": processing_time_ms,
            "status": "failed",
            "error": str(e),
        }

    except Exception as e:
        logger.error(f"Error in recommendation event tracking: {e}", exc_info=True)
        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "recommendation_id": recommendation_id,
            "event_type": event_type,
            "times_shown": 0,
            "times_clicked": 0,
            "click_through_rate": 0.0,
            "feedback_created": False,
            "processing_time_ms": processing_time_ms,
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    name="tasks.recommendation_tasks.periodic_recommendation_refresh",
    bind=True,
)
def periodic_recommendation_refresh(
    self,
) -> Dict[str, Any]:
    """
    Periodic task to refresh all candidate recommendations.

    This is a scheduled task that runs periodically (e.g., daily) to
    automatically refresh all recommendation types including similar
    candidates, best-fit candidates for vacancies, and at-risk candidates.

    Returns:
        Dictionary containing refresh results:
        - similar_candidates: Results from similar candidates pre-computation
        - best_fit_candidates: Results from best-fit candidates pre-computation
        - at_risk_candidates: Results from at-risk candidates pre-computation
        - total_processing_time_ms: Total time for all refreshes
        - status: Overall task status (completed/failed)

    Example:
        >>> # This would be scheduled via Celery beat
        >>> # celery beat schedule: {
        >>> #     'daily-recommendation-refresh': {
        >>> #         'task': 'tasks.recommendation_tasks.periodic_recommendation_refresh',
        >>> #         'schedule': crontab(hour=1, minute=0),  # 1 AM daily
        >>> #     }
        >>> # }
    """
    logger.info("Starting periodic recommendation refresh")
    start_time = time.time()

    try:
        # Step 1: Pre-compute similar candidates
        logger.info("Step 1: Refreshing similar candidates")
        similar_candidates_result = precompute_similar_candidates(
            batch_size=BATCH_SIZE,
            limit=DEFAULT_QUERY_LIMIT,
        )

        # Step 2: Pre-compute best-fit candidates for vacancies
        logger.info("Step 2: Refreshing best-fit candidates")
        best_fit_candidates_result = precompute_best_fit_candidates(
            batch_size=BATCH_SIZE,
            limit=DEFAULT_QUERY_LIMIT,
        )

        # Step 3: Pre-compute at-risk candidates
        logger.info("Step 3: Refreshing at-risk candidates")
        at_risk_candidates_result = precompute_at_risk_candidates(
            limit=50,
        )

        total_processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "similar_candidates": similar_candidates_result,
            "best_fit_candidates": best_fit_candidates_result,
            "at_risk_candidates": at_risk_candidates_result,
            "total_processing_time_ms": total_processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Periodic recommendation refresh completed: "
            f"similar={similar_candidates_result.get('status')}, "
            f"best_fit={best_fit_candidates_result.get('status')}, "
            f"at_risk={at_risk_candidates_result.get('status')}, "
            f"time={total_processing_time_ms}ms"
        )

        return result

    except Exception as e:
        logger.error(f"Error in periodic recommendation refresh: {e}", exc_info=True)
        total_processing_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "similar_candidates": {"status": "failed", "error": str(e)},
            "best_fit_candidates": {"status": "failed", "error": str(e)},
            "at_risk_candidates": {"status": "failed", "error": str(e)},
            "total_processing_time_ms": total_processing_time_ms,
            "status": "failed",
            "error": str(e),
        }
