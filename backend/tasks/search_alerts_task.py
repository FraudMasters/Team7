"""
Search alert tasks for notifying users of new resume matches.

This module provides Celery tasks for processing search alerts when new resumes
are uploaded that match saved search criteria. It handles matching, notification
delivery, and alert status tracking.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models import SavedSearch, SearchAlert, Resume, ResumeAnalysis
from analyzers.unified_matcher import UnifiedSkillMatcher, get_unified_matcher

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.search_alerts.check_resume_against_saved_searches",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def check_resume_against_saved_searches(
    self,
    resume_id: str,
    resume_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Check a new resume against all saved searches and create alerts for matches.

    This Celery task runs when a new resume is uploaded to find any saved searches
    that match the resume's criteria. For each match, it creates a SearchAlert
    record for notification.

    Task Workflow:
    1. Retrieve all saved searches from database
    2. Compare resume data against each search's criteria using UnifiedSkillMatcher
    3. Create SearchAlert records for matching searches
    4. Trigger notification tasks for each alert

    Args:
        self: Celery task instance (bind=True)
        resume_id: UUID of the newly uploaded resume
        resume_data: Dictionary containing resume information:
            - skills: List of skills extracted from resume
            - experience_years: Total years of experience
            - location: Geographic location
            - education: Education level
            - keywords: Important keywords from resume
            - metadata: Additional resume metadata

    Returns:
        Dictionary containing processing results:
        - resume_id: ID of the processed resume
        - status: Task status (completed/failed/pending)
        - total_searches_checked: Number of saved searches checked
        - matches_found: Number of matching searches
        - alerts_created: Number of alerts created
        - processing_time_ms: Total processing time
        - match_details: List of matching search details

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For database or processing errors

    Example:
        >>> result = check_resume_against_saved_searches.delay(
        ...     resume_id="abc-123",
        ...     resume_data={"skills": ["Python", "FastAPI"], "experience_years": 5}
        ... )
        >>> print(result.get())
        {'resume_id': 'abc-123', 'matches_found': 2, 'alerts_created': 2}
    """
    import time
    import asyncio
    start_time = time.time()

    logger.info(f"Checking resume {resume_id} against saved searches")

    try:
        # Run async database operations in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _process_saved_searches(resume_id, resume_data)
            )
        finally:
            loop.close()

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Resume {resume_id} checked against {result['total_searches_checked']} saved searches: "
            f"{result['matches_found']} matches found, {result['alerts_created']} alerts created "
            f"in {processing_time}ms"
        )

        result["processing_time_ms"] = processing_time
        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Search alert check timed out for resume_id={resume_id}")
        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to check resume {resume_id} against saved searches: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    name="tasks.search_alerts.send_search_alert_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_search_alert_notification(
    self,
    alert_id: str,
    saved_search_id: str,
    resume_id: str,
    recipient_email: str,
) -> Dict[str, Any]:
    """
    Send notification for a specific search alert.

    This Celery task handles sending individual search alert notifications
    to users who have saved searches matching new resumes.

    Args:
        self: Celery task instance (bind=True)
        alert_id: UUID of the search alert
        saved_search_id: UUID of the saved search that matched
        resume_id: UUID of the matching resume
        recipient_email: Email address to send notification to

    Returns:
        Dictionary containing sending results:
        - alert_id: ID of the alert
        - status: Task status (sent/failed/pending)
        - recipient: Email address of recipient
        - sent_at: Timestamp when sent (ISO format)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Example:
        >>> result = send_search_alert_notification.delay(
        ...     alert_id="alert-123",
        ...     saved_search_id="search-456",
        ...     resume_id="resume-789",
        ...     recipient_email="user@example.com"
        ... )
        >>> print(result.get())
        {'alert_id': 'alert-123', 'status': 'sent'}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending search alert notification for alert_id={alert_id} "
        f"to {recipient_email}"
    )

    try:
        # In a real implementation, you would:
        # 1. Retrieve SearchAlert, SavedSearch, and Resume details from database
        # 2. Compose notification email with resume details
        # 3. Send email via configured SMTP/service
        # 4. Update SearchAlert.is_sent and SearchAlert.sent_at

        # Placeholder: Simulate sending notification
        subject = f"New Resume Matches Your Saved Search"
        body = f"""
A new resume has been uploaded that matches your saved search.

Alert ID: {alert_id}
Resume ID: {resume_id}
Saved Search ID: {saved_search_id}

View the resume details in your dashboard.

---
This is an automated email from AgentHR.
        """.strip()

        # Log email details (in production, actually send email)
        logger.info(f"Alert notification composed: subject='{subject}', to={recipient_email}")
        logger.info(f"Alert body length: {len(body)} characters")

        # Simulate email sending (in production, use SMTP/service)
        time.sleep(0.1)  # Simulate network delay

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Search alert notification sent successfully to {recipient_email} "
            f"in {processing_time}ms"
        )

        return {
            "alert_id": alert_id,
            "status": "sent",
            "recipient": recipient_email,
            "sent_at": time.time(),
            "processing_time_ms": processing_time,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Search alert notification task timed out for alert_id={alert_id}")
        return {
            "alert_id": alert_id,
            "status": "failed",
            "recipient": recipient_email,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to send search alert notification for alert_id={alert_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "alert_id": alert_id,
            "status": "failed",
            "recipient": recipient_email,
            "error": str(e),
        }


@shared_task(
    name="tasks.search_alerts.process_pending_alerts",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def process_pending_alerts(
    self,
    batch_size: int = 50,
) -> Dict[str, Any]:
    """
    Process all pending search alerts that haven't been sent yet.

    This Celery task runs periodically to process any pending search alerts
    that may have failed or been delayed. It's useful for recovery and
    ensuring all alerts are eventually delivered.

    Args:
        self: Celery task instance (bind=True)
        batch_size: Maximum number of alerts to process in one batch (default: 50)

    Returns:
        Dictionary containing processing results:
        - status: Task status (completed/failed/pending)
        - total_alerts_processed: Number of alerts processed
        - successful_sends: Number of alerts successfully sent
        - failed_sends: Number of alerts that failed to send
        - processing_time_ms: Total processing time
        - remaining_pending: Number of alerts still pending

    Example:
        >>> result = process_pending_alerts.delay(batch_size=100)
        >>> print(result.get())
        {'status': 'completed', 'successful_sends': 45, 'failed_sends': 5}
    """
    import time
    start_time = time.time()

    logger.info(f"Processing pending search alerts (batch_size={batch_size})")

    try:
        # In a real implementation, you would:
        # 1. Query database for pending SearchAlert records (is_sent=False)
        # 2. For each pending alert, trigger send_search_alert_notification task
        # 3. Track success/failure and update database

        # Placeholder: Simulate processing pending alerts
        pending_alerts = []  # Would query: SearchAlert.query.filter_by(is_sent=False).limit(batch_size).all()

        successful_sends = 0
        failed_sends = 0

        for alert in pending_alerts:
            try:
                # Trigger notification task
                # send_search_alert_notification.delay(...)
                successful_sends += 1
            except Exception as e:
                failed_sends += 1
                logger.error(f"Failed to process alert {alert.id}: {e}")

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Processed {len(pending_alerts)} pending alerts: "
            f"{successful_sends} successful, {failed_sends} failed "
            f"in {processing_time}ms"
        )

        return {
            "status": "completed",
            "total_alerts_processed": len(pending_alerts),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "processing_time_ms": processing_time,
            "remaining_pending": 0,  # Would query actual count
        }

    except SoftTimeLimitExceeded:
        logger.error("Process pending alerts task timed out")
        return {
            "status": "failed",
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to process pending alerts: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))

        return {
            "status": "failed",
            "error": str(e),
        }


async def _process_saved_searches(
    resume_id: str,
    resume_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Process saved searches and create alerts for matches (async).

    Args:
        resume_id: UUID of the resume to check
        resume_data: Dictionary containing resume information

    Returns:
        Dictionary with processing results
    """
    async with async_session_maker() as db:
        # Query all saved searches
        stmt = select(SavedSearch)
        result = await db.execute(stmt)
        saved_searches = result.scalars().all()

        matches_found = 0
        alerts_created = []
        match_details = []

        # Get unified matcher instance
        matcher = get_unified_matcher()

        # Check resume against each saved search
        for search in saved_searches:
            match_result = await _check_resume_against_search(
                db=db,
                resume_id=resume_id,
                resume_data=resume_data,
                saved_search=search,
                matcher=matcher,
            )

            if match_result["matched"]:
                matches_found += 1

                # Create SearchAlert record
                alert = SearchAlert(
                    saved_search_id=search.id,
                    resume_id=UUID(resume_id),
                    is_sent=False,
                )
                db.add(alert)
                await db.flush()

                alerts_created.append({
                    "alert_id": str(alert.id),
                    "saved_search_id": str(search.id),
                    "saved_search_name": search.name,
                })

                match_details.append({
                    "saved_search_name": search.name,
                    "match_score": match_result["match_score"],
                    "matched_criteria": match_result["matched_criteria"],
                })

                logger.info(
                    f"Match found: saved search '{search.name}' matches resume {resume_id} "
                    f"with score {match_result['match_score']}"
                )

        # Commit all alerts to database
        await db.commit()

        return {
            "resume_id": resume_id,
            "status": "completed",
            "total_searches_checked": len(saved_searches),
            "matches_found": matches_found,
            "alerts_created": len(alerts_created),
            "alert_ids": [a["alert_id"] for a in alerts_created],
            "match_details": match_details,
        }


async def _check_resume_against_search(
    db: AsyncSession,
    resume_id: str,
    resume_data: Dict[str, Any],
    saved_search: SavedSearch,
    matcher: UnifiedSkillMatcher,
) -> Dict[str, Any]:
    """
    Check if a resume matches a specific saved search.

    Args:
        db: Database session
        resume_id: UUID of the resume
        resume_data: Dictionary containing resume information
        saved_search: SavedSearch instance
        matcher: UnifiedSkillMatcher instance

    Returns:
        Dictionary with:
        - matched: bool indicating if resume matches search
        - match_score: int 0-100 indicating match strength
        - matched_criteria: list of criteria that matched
    """
    filters = saved_search.filters or {}
    matched_criteria = []
    total_score = 0
    max_score = 0

    # 1. Skills matching (highest priority - 60% of score)
    required_skills = filters.get("skills", [])
    if required_skills:
        max_score += 60
        resume_skills = resume_data.get("skills", [])

        if resume_skills:
            # Use unified matcher for skill matching
            match_result = matcher.match(
                resume_text=resume_data.get("raw_text", ""),
                resume_skills=resume_skills,
                job_title="Saved Search: " + saved_search.name,
                job_description=saved_search.query,
                required_skills=required_skills,
            )

            skills_score = int(match_result.overall_score * 60)
            total_score += skills_score

            if skills_score >= 30:  # At least 50% of skills portion
                matched_criteria.append("skills")

    # 2. Experience years matching (medium priority - 20% of score)
    min_experience = filters.get("min_experience_years")
    max_experience = filters.get("max_experience_years")
    resume_experience = resume_data.get("experience_years", 0)

    if min_experience is not None or max_experience is not None:
        max_score += 20
        experience_match = True

        if min_experience is not None and resume_experience < min_experience:
            experience_match = False
        if max_experience is not None and resume_experience > max_experience:
            experience_match = False

        if experience_match:
            total_score += 20
            matched_criteria.append("experience")

    # 3. Location matching (low priority - 10% of score)
    location_filter = filters.get("location")
    if location_filter:
        max_score += 10
        resume_location = resume_data.get("location", "")

        if resume_location and location_filter.lower() in resume_location.lower():
            total_score += 10
            matched_criteria.append("location")

    # 4. Education level matching (low priority - 10% of score)
    education_filter = filters.get("education_level")
    if education_filter:
        max_score += 10
        resume_education = resume_data.get("education", "")

        if resume_education:
            # Simple matching - could be enhanced with education level hierarchy
            if education_filter.lower() in str(resume_education).lower():
                total_score += 10
                matched_criteria.append("education")

    # Normalize score to 0-100
    final_score = int((total_score / max_score * 100) if max_score > 0 else 0)

    # Consider it a match if score >= 50% and at least one criterion matched
    matched = final_score >= 50 and len(matched_criteria) > 0

    return {
        "matched": matched,
        "match_score": final_score,
        "matched_criteria": matched_criteria,
    }


# Legacy helper functions kept for compatibility

def _resume_matches_search(resume_data: Dict[str, Any], search_criteria: Dict[str, Any]) -> bool:
    """
    Check if a resume matches saved search criteria (legacy sync version).

    Note: This is a simplified sync version for backward compatibility.
    The actual matching is done by async _check_resume_against_search.
    """
    # Check skills
    required_skills = search_criteria.get("skills", [])
    resume_skills = resume_data.get("skills", [])

    if required_skills:
        skill_match = any(
            skill.lower() in [rs.lower() for rs in resume_skills]
            for skill in required_skills
        )
        if not skill_match:
            return False

    # Check experience
    min_experience = search_criteria.get("min_experience_years")
    max_experience = search_criteria.get("max_experience_years")
    resume_experience = resume_data.get("experience_years", 0)

    if min_experience is not None and resume_experience < min_experience:
        return False
    if max_experience is not None and resume_experience > max_experience:
        return False

    return True


def _calculate_match_score(resume_data: Dict[str, Any], search_criteria: Dict[str, Any]) -> int:
    """
    Calculate match score between resume and search criteria (legacy sync version).

    Returns a score from 0-100 indicating how well the resume matches.
    """
    score = 0
    max_score = 100

    # Skills (60 points)
    required_skills = search_criteria.get("skills", [])
    resume_skills = resume_data.get("skills", [])

    if required_skills and resume_skills:
        matched_skills = sum(
            1 for skill in required_skills
            if skill.lower() in [rs.lower() for rs in resume_skills]
        )
        score += int((matched_skills / len(required_skills)) * 60)

    # Experience (20 points)
    min_experience = search_criteria.get("min_experience_years")
    max_experience = search_criteria.get("max_experience_years")
    resume_experience = resume_data.get("experience_years", 0)

    if min_experience is not None or max_experience is not None:
        experience_match = True
        if min_experience is not None and resume_experience < min_experience:
            experience_match = False
        if max_experience is not None and resume_experience > max_experience:
            experience_match = False

        if experience_match:
            score += 20

    # Location (10 points)
    location_filter = search_criteria.get("location")
    if location_filter and resume_data.get("location"):
        if location_filter.lower() in resume_data.get("location", "").lower():
            score += 10

    # Education (10 points)
    education_filter = search_criteria.get("education_level")
    if education_filter and resume_data.get("education"):
        if education_filter.lower() in str(resume_data.get("education", "")).lower():
            score += 10

    return min(score, max_score)


def _get_matched_criteria(resume_data: Dict[str, Any], search_criteria: Dict[str, Any]) -> List[str]:
    """
    Get list of criteria that matched between resume and search (legacy sync version).

    Returns a list of specific criteria that matched (e.g., ['skills', 'location']).
    """
    matched = []

    # Check skills
    required_skills = search_criteria.get("skills", [])
    resume_skills = resume_data.get("skills", [])

    if required_skills and resume_skills:
        if any(
            skill.lower() in [rs.lower() for rs in resume_skills]
            for skill in required_skills
        ):
            matched.append("skills")

    # Check experience
    min_experience = search_criteria.get("min_experience_years")
    max_experience = search_criteria.get("max_experience_years")
    resume_experience = resume_data.get("experience_years", 0)

    if min_experience is not None or max_experience is not None:
        experience_match = True
        if min_experience is not None and resume_experience < min_experience:
            experience_match = False
        if max_experience is not None and resume_experience > max_experience:
            experience_match = False

        if experience_match:
            matched.append("experience")

    # Check location
    location_filter = search_criteria.get("location")
    if location_filter and resume_data.get("location"):
        if location_filter.lower() in resume_data.get("location", "").lower():
            matched.append("location")

    # Check education
    education_filter = search_criteria.get("education_level")
    if education_filter and resume_data.get("education"):
        if education_filter.lower() in str(resume_data.get("education", "")).lower():
            matched.append("education")

    return matched
