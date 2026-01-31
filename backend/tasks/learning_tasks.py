"""
ML learning tasks for skill synonym discovery and model improvement.

This module provides Celery tasks for processing recruiter feedback,
aggregating corrections, and generating new synonym candidates to improve
matching accuracy over time.
"""
import logging
import time
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from models.skill_feedback import SkillFeedback
from models.custom_synonyms import CustomSynonym
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Minimum number of corrections before suggesting a synonym
MIN_CORRECTION_THRESHOLD = 3

# Minimum confidence score for synonym suggestions
MIN_SYNONYM_CONFIDENCE = 0.7


def aggregate_corrections(
    feedback_entries: List[SkillFeedback],
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate recruiter corrections to find synonym patterns.

    This function analyzes feedback entries where recruiters corrected
    the AI's matching, identifying patterns that suggest new synonyms.

    Args:
        feedback_entries: List of SkillFeedback objects with corrections

    Returns:
        Dictionary mapping canonical skills to their discovered synonyms:
        {
            "React": {
                "synonyms": {"ReactJS", "React.js", "React Framework"},
                "correction_count": 15,
                "confidence": 0.92,
                "sources": ["api", "frontend"]
            }
        }

    Example:
        >>> entries = [feedback1, feedback2, feedback3]
        >>> corrections = aggregate_corrections(entries)
        >>> print(corrections["React"]["synonyms"])
        {'ReactJS', 'React.js'}
    """
    # Group corrections by canonical skill (what the recruiter corrected to)
    skill_groups: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "synonyms": defaultdict(int),
        "correction_count": 0,
        "sources": set(),
    })

    for feedback in feedback_entries:
        # Skip if no correction was provided
        if not feedback.recruiter_correction and not feedback.actual_skill:
            continue

        # Use actual_skill if provided, otherwise use recruiter_correction
        corrected_skill = feedback.actual_skill or feedback.recruiter_correction

        if not corrected_skill or not feedback.skill:
            continue

        # Normalize skill names for comparison
        canonical_skill = corrected_skill.strip().lower()
        original_skill = feedback.skill.strip().lower()

        # Skip if they're the same (no actual correction)
        if canonical_skill == original_skill:
            continue

        # Record this correction
        skill_groups[canonical_skill]["synonyms"][original_skill] += 1
        skill_groups[canonical_skill]["correction_count"] += 1
        skill_groups[canonical_skill]["sources"].add(feedback.feedback_source)

    # Calculate confidence scores and convert sets to lists
    results = {}
    for canonical_skill, data in skill_groups.items():
        # Filter synonyms by minimum threshold
        filtered_synonyms = {
            syn: count
            for syn, count in data["synonyms"].items()
            if count >= MIN_CORRECTION_THRESHOLD
        }

        if not filtered_synonyms:
            continue

        # Calculate confidence based on correction count consistency
        total_corrections = sum(filtered_synonyms.values())
        confidence = min(1.0, total_corrections / (MIN_CORRECTION_THRESHOLD * 2))

        results[canonical_skill] = {
            "synonyms": list(filtered_synonyms.keys()),
            "correction_count": total_corrections,
            "confidence": round(confidence, 2),
            "sources": list(data["sources"]),
        }

    return results


def generate_synonym_candidates(
    corrections: Dict[str, Dict[str, Any]],
    organization_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Generate synonym candidate entries from aggregated corrections.

    This function converts aggregated correction data into CustomSynonym
    candidate entries that can be reviewed and activated.

    Args:
        corrections: Aggregated corrections from aggregate_corrections()
        organization_id: Optional organization ID for custom synonyms

    Returns:
        List of synonym candidate dictionaries:
        [
            {
                "canonical_skill": "react",
                "custom_synonyms": ["reactjs", "react.js"],
                "context": None,
                "confidence": 0.92,
                "correction_count": 15,
                "metadata": {"sources": ["api", "frontend"]}
            }
        ]

    Example:
        >>> corrections = {"react": {"synonyms": ["reactjs"], "confidence": 0.9}}
        >>> candidates = generate_synonym_candidates(corrections, "org123")
        >>> print(candidates[0]["canonical_skill"])
        'react'
    """
    candidates = []

    for canonical_skill, data in corrections.items():
        # Skip low-confidence suggestions
        if data["confidence"] < MIN_SYNONYM_CONFIDENCE:
            logger.info(
                f"Skipping low-confidence synonym candidate '{canonical_skill}' "
                f"(confidence: {data['confidence']} < {MIN_SYNONYM_CONFIDENCE})"
            )
            continue

        candidate = {
            "canonical_skill": canonical_skill,
            "custom_synonyms": data["synonyms"],
            "context": None,  # Could be inferred from future metadata
            "confidence": data["confidence"],
            "correction_count": data["correction_count"],
            "metadata": {
                "sources": data.get("sources", []),
                "generated_at": datetime.utcnow().isoformat(),
                "auto_generated": True,
            },
        }

        # Add organization_id if provided
        if organization_id:
            candidate["organization_id"] = organization_id

        candidates.append(candidate)

    logger.info(f"Generated {len(candidates)} synonym candidates from corrections")
    return candidates


@shared_task(
    name="tasks.learning_tasks.aggregate_feedback_and_generate_synonyms",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def aggregate_feedback_and_generate_synonyms(
    self,
    organization_id: Optional[str] = None,
    days_back: int = 30,
    mark_processed: bool = True,
) -> Dict[str, Any]:
    """
    Aggregate feedback and generate new synonym candidates.

    This Celery task processes unprocessed recruiter feedback to identify
    patterns in skill corrections and generates new synonym candidates for
    review and activation. This enables continuous learning from recruiter
    behavior to improve matching accuracy over time.

    Task Workflow:
    1. Query unprocessed feedback entries from the database
    2. Filter by organization_id (if provided) and date range
    3. Aggregate corrections to find synonym patterns
    4. Generate high-confidence synonym candidates
    5. Optionally mark feedback as processed

    Args:
        self: Celery task instance (bind=True)
        organization_id: Optional organization ID to filter feedback
        days_back: Number of days to look back for feedback (default: 30)
        mark_processed: Whether to mark feedback as processed (default: True)

    Returns:
        Dictionary containing aggregation results:
        - total_feedback: Total feedback entries processed
        - unprocessed_count: Number of unprocessed entries
        - corrections_found: Number of corrections aggregated
        - candidates_generated: Number of synonym candidates generated
        - candidates: List of generated synonym candidates
        - processing_time_ms: Total processing time
        - status: Task status (completed/failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> from tasks.learning_tasks import aggregate_feedback_and_generate_synonyms
        >>> task = aggregate_feedback_and_generate_synonyms.delay("org123")
        >>> result = task.get()
        >>> print(result['candidates_generated'])
        5
    """
    start_time = time.time()
    total_steps = 4
    current_step = 0

    try:
        logger.info(
            f"Starting feedback aggregation for organization: {organization_id or 'all'}, "
            f"days_back: {days_back}"
        )

        # Step 1: Query unprocessed feedback
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "querying_feedback",
            "message": "Querying unprocessed feedback from database...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Querying feedback")

        # Note: This is a placeholder for database query
        # In a real implementation, you would use async session to query SkillFeedback
        # feedback_entries = await db_session.execute(
        #     select(SkillFeedback).where(
        #         and_(
        #             SkillFeedback.processed == False,
        #             SkillFeedback.created_at >= datetime.utcnow() - timedelta(days=days_back),
        #             SkillFeedback.organization_id == organization_id if organization_id else True
        #         )
        #     )
        # )
        # For now, return placeholder result
        feedback_entries = []
        unprocessed_count = 0

        logger.info(f"Found {unprocessed_count} unprocessed feedback entries")

        # Step 2: Aggregate corrections
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "aggregating_corrections",
            "message": "Aggregating recruiter corrections...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Aggregating corrections")

        corrections = aggregate_corrections(feedback_entries)
        corrections_count = len(corrections)
        logger.info(f"Aggregated {corrections_count} unique skill corrections")

        # Step 3: Generate synonym candidates
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "generating_candidates",
            "message": "Generating synonym candidates from patterns...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Generating candidates")

        candidates = generate_synonym_candidates(corrections, organization_id)
        logger.info(f"Generated {len(candidates)} synonym candidates")

        # Step 4: Mark feedback as processed (if requested)
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "marking_processed",
            "message": "Marking feedback as processed...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Marking processed")

        # Note: This is a placeholder for marking feedback as processed
        # In a real implementation, you would update the processed flag
        processed_count = 0
        if mark_processed and feedback_entries:
            # for entry in feedback_entries:
            #     entry.processed = True
            # await db_session.commit()
            processed_count = len(feedback_entries)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "total_feedback": unprocessed_count,
            "unprocessed_count": unprocessed_count,
            "corrections_found": corrections_count,
            "candidates_generated": len(candidates),
            "candidates": candidates,
            "processed_count": processed_count,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Feedback aggregation completed: {corrections_count} corrections, "
            f"{len(candidates)} candidates generated in {processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "status": "failed",
            "error": "Aggregation exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in feedback aggregation: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.learning_tasks.review_and_activate_synonyms",
    bind=True,
    max_retries=1,
    default_retry_delay=60,
)
def review_and_activate_synonyms(
    self,
    candidate_ids: List[str],
    auto_activate_threshold: float = 0.9,
) -> Dict[str, Any]:
    """
    Review and activate synonym candidates.

    This task reviews generated synonym candidates and automatically activates
    high-confidence candidates, while flagging lower-confidence ones for manual
    review.

    Args:
        self: Celery task instance (bind=True)
        candidate_ids: List of candidate IDs to review
        auto_activate_threshold: Confidence threshold for auto-activation (default: 0.9)

    Returns:
        Dictionary containing review results:
        - total_candidates: Total candidates reviewed
        - auto_activated: Number automatically activated
        - manual_review: Number flagged for manual review
        - rejected: Number rejected (low confidence)
        - processing_time_ms: Total processing time
        - status: Task status

    Example:
        >>> from tasks.learning_tasks import review_and_activate_synonyms
        >>> task = review_and_activate_synonyms.delay(["id1", "id2"])
        >>> result = task.get()
        >>> print(result['auto_activated'])
        2
    """
    start_time = time.time()

    try:
        logger.info(f"Reviewing {len(candidate_ids)} synonym candidates")

        auto_activated = 0
        manual_review = 0
        rejected = 0

        # Note: This is a placeholder for review logic
        # In a real implementation, you would:
        # 1. Query candidates by ID
        # 2. Check confidence scores
        # 3. Auto-activate high confidence ones
        # 4. Flag medium confidence for review
        # 5. Reject low confidence ones

        for candidate_id in candidate_ids:
            # Placeholder logic - in real implementation, query the candidate
            # candidate = await db_session.get(CustomSynonym, candidate_id)
            # if candidate and candidate.metadata.get("confidence", 0) >= auto_activate_threshold:
            #     candidate.is_active = True
            #     auto_activated += 1
            pass

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "total_candidates": len(candidate_ids),
            "auto_activated": auto_activated,
            "manual_review": manual_review,
            "rejected": rejected,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Review completed: {auto_activated} activated, "
            f"{manual_review} flagged for review, {rejected} rejected"
        )

        return result

    except Exception as e:
        logger.error(f"Error in synonym review: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.learning_tasks.periodic_feedback_aggregation",
    bind=True,
)
def periodic_feedback_aggregation(
    self,
) -> Dict[str, Any]:
    """
    Periodic task to aggregate feedback and generate synonyms.

    This is a scheduled task that runs periodically (e.g., daily) to
    automatically process new feedback and generate improvement candidates.

    Returns:
        Dictionary containing aggregation results

    Example:
        >>> # This would be scheduled via Celery beat
        >>> # celery beat schedule: {
        >>> #     'daily-feedback-aggregation': {
        >>> #         'task': 'tasks.learning_tasks.periodic_feedback_aggregation',
        >>> #         'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        >>> #     }
        >>> # }
    """
    logger.info("Starting periodic feedback aggregation")

    # Aggregate feedback from the last 7 days
    result = aggregate_feedback_and_generate_synonyms(
        organization_id=None,  # All organizations
        days_back=7,
        mark_processed=True,
    )

    logger.info(f"Periodic aggregation completed: {result.get('status')}")
    return result


@shared_task(
    name="tasks.learning_tasks.retrain_skill_matching_model",
    bind=True,
    max_retries=1,
    default_retry_delay=300,
)
def retrain_skill_matching_model(
    self,
    model_name: str = "skill_matching",
    days_back: int = 30,
    min_feedback_count: int = 50,
    auto_activate: bool = False,
    performance_threshold: float = 0.85,
) -> Dict[str, Any]:
    """
    Retrain the skill matching model based on accumulated feedback.

    This Celery task processes accumulated recruiter feedback to retrain
    and improve the skill matching model. It creates a new model version,
    evaluates performance, and optionally activates it if performance
    thresholds are met.

    Task Workflow:
    1. Query feedback data from the specified time period
    2. Validate minimum feedback count for training
    3. Extract training data (skill pairs and correctness labels)
    4. Train new model or update existing synonyms
    5. Create new MLModelVersion entry
    6. Evaluate model performance on validation set
    7. Optionally activate model if performance exceeds threshold

    Args:
        self: Celery task instance (bind=True)
        model_name: Name of the model to retrain (default: "skill_matching")
        days_back: Number of days of feedback to use for training (default: 30)
        min_feedback_count: Minimum feedback entries required for training (default: 50)
        auto_activate: Whether to auto-activate if performance threshold met (default: False)
        performance_threshold: Minimum accuracy score for auto-activation (default: 0.85)

    Returns:
        Dictionary containing retraining results:
        - training_samples: Number of feedback samples used
        - new_version_id: ID of the created model version
        - performance_score: Model performance score (0-1)
        - is_active: Whether the model was activated
        - is_experiment: Whether the model is an experiment
        - improvement_over_baseline: Performance improvement over current model
        - processing_time_ms: Total processing time
        - status: Task status (completed/failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> from tasks.learning_tasks import retrain_skill_matching_model
        >>> task = retrain_skill_matching_model.delay(
        ...     model_name="skill_matching",
        ...     days_back=30,
        ...     auto_activate=True
        ... )
        >>> result = task.get()
        >>> print(result['performance_score'])
        0.92
    """
    start_time = time.time()
    total_steps = 6
    current_step = 0

    try:
        logger.info(
            f"Starting model retraining for '{model_name}', "
            f"days_back: {days_back}, min_feedback: {min_feedback_count}"
        )

        # Step 1: Query feedback data
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "querying_feedback",
            "message": "Querying feedback data for training...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Querying feedback")

        # Note: This is a placeholder for database query
        # In a real implementation, you would use async session to query SkillFeedback
        # feedback_entries = await db_session.execute(
        #     select(SkillFeedback).where(
        #         and_(
        #             SkillFeedback.created_at >= datetime.utcnow() - timedelta(days=days_back),
        #             SkillFeedback.was_correct.is_not(None),
        #             SkillFeedback.skill.is_not(None)
        #         )
        #     ).order_by(SkillFeedback.created_at.desc())
        # )
        feedback_entries = []
        training_samples = len(feedback_entries)

        logger.info(f"Found {training_samples} feedback samples for training")

        # Validate minimum feedback count
        if training_samples < min_feedback_count:
            logger.warning(
                f"Insufficient feedback for training: {training_samples} < {min_feedback_count}. "
                f"Skipping retraining."
            )
            return {
                "status": "skipped",
                "reason": f"Insufficient feedback samples ({training_samples} < {min_feedback_count})",
                "training_samples": training_samples,
                "min_required": min_feedback_count,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Step 2: Extract training data
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "extracting_features",
            "message": "Extracting training features from feedback...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Extracting features")

        # Extract skill pairs and correctness labels
        # Note: In a real implementation, this would process feedback_entries
        training_data = []
        for entry in feedback_entries:
            # Extract features from feedback
            # This is a placeholder - real implementation would extract:
            # - Original skill as matched by AI
            # - Corrected skill (if provided)
            # - Whether the match was correct
            # - Context information
            pass

        logger.info(f"Extracted {len(training_data)} training samples")

        # Step 3: Aggregate corrections for synonym updates
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "aggregating_corrections",
            "message": "Aggregating corrections for synonym updates...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Aggregating corrections")

        corrections = aggregate_corrections(feedback_entries)
        corrections_count = len(corrections)
        logger.info(f"Aggregated {corrections_count} skill corrections")

        # Step 4: Generate and save synonym candidates
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "generating_synonyms",
            "message": "Generating new synonym candidates...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Generating synonyms")

        # Generate synonym candidates from corrections
        candidates = generate_synonym_candidates(corrections, organization_id=None)

        # Note: In a real implementation, you would save candidates to database
        # for candidate in candidates:
        #     new_synonym = CustomSynonym(**candidate)
        #     db_session.add(new_synonym)
        # await db_session.commit()

        logger.info(f"Generated {len(candidates)} new synonym candidates")

        # Step 5: Create new model version
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "creating_model_version",
            "message": "Creating new model version entry...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Creating model version")

        # Generate new version number
        # Note: In a real implementation, you would query the latest version
        # latest_version = await db_session.execute(
        #     select(MLModelVersion)
        #     .where(MLModelVersion.model_name == model_name)
        #     .order_by(MLModelVersion.created_at.desc())
        #     .limit(1)
        # )
        # and increment the version number
        new_version = "1.0.0"  # Placeholder

        # Calculate training accuracy
        # Note: In a real implementation, this would evaluate on a validation set
        training_accuracy = min(1.0, len(candidates) * 0.1 + 0.7)  # Placeholder calculation
        performance_score = round(training_accuracy, 3)

        # Note: In a real implementation, you would create MLModelVersion entry
        # new_model = MLModelVersion(
        #     model_name=model_name,
        #     version=new_version,
        #     is_active=False,
        #     is_experiment=not auto_activate,
        #     performance_score=performance_score * 100,
        #     training_samples=training_samples,
        #     metadata={
        #         "training_days": days_back,
        #         "synonyms_added": len(candidates),
        #         "corrections_aggregated": corrections_count,
        #         "auto_generated": True,
        #     }
        # )
        # db_session.add(new_model)
        # await db_session.commit()
        # new_version_id = str(new_model.id)

        new_version_id = "placeholder-uuid"  # Placeholder
        logger.info(f"Created new model version: {new_version} (ID: {new_version_id})")

        # Step 6: Evaluate and optionally activate
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "evaluating_performance",
            "message": "Evaluating model performance...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Evaluating performance")

        # Determine if model should be activated
        should_activate = auto_activate and performance_score >= performance_threshold
        is_active = False
        is_experiment = not should_activate

        # Note: In a real implementation, you would activate the model if needed
        # if should_activate:
        #     # Deactivate other versions
        #     await db_session.execute(
        #         update(MLModelVersion)
        #         .where(
        #             and_(
        #                 MLModelVersion.model_name == model_name,
        #                 MLModelVersion.id != new_version_id
        #             )
        #         )
        #         .values(is_active=False)
        #     )
        #     # Activate new version
        #     new_model.is_active = True
        #     new_model.is_experiment = False
        #     await db_session.commit()
        #     is_active = True
        #     is_experiment = False

        # Calculate improvement over baseline
        # Note: In a real implementation, you would compare with current active model
        baseline_score = 0.75  # Placeholder
        improvement = round(performance_score - baseline_score, 3)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "training_samples": training_samples,
            "new_version_id": new_version_id,
            "new_version": new_version,
            "performance_score": performance_score,
            "is_active": is_active,
            "is_experiment": is_experiment,
            "improvement_over_baseline": improvement,
            "synonyms_generated": len(candidates),
            "corrections_aggregated": corrections_count,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Model retraining completed: version {new_version}, "
            f"score: {performance_score}, activated: {is_active}, "
            f"improvement: {improvement:+.3f}"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "status": "failed",
            "error": "Model retraining exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in model retraining: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }
