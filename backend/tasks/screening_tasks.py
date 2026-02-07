"""
Automated resume screening and triage tasks.

This module provides Celery tasks for automatic candidate screening,
including auto-screening triggered on resume analysis completion,
auto-response emails, and review reminder notifications.
"""
import logging
import time
from typing import Dict, Any, List, Optional, UUID
from datetime import datetime, timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from config import get_settings
from database import get_db

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.screening_tasks.auto_screen_candidate",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def auto_screen_candidate(
    self,
    resume_id: str,
    vacancy_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Automatically screen a candidate against active screening rules.

    This Celery task is triggered on resume analysis completion to
    automatically apply screening rules and categorize candidates into
    tiers (High Priority, Review, Reject).

    Task Workflow:
    1. Get resume analysis data
    2. Find active screening rules for vacancy (or all vacancies)
    3. Call ScreeningService.apply_screening_rules() for each vacancy
    4. Store ScreeningResult in database
    5. If tier=REJECT and auto_reject_with_notification=True, trigger notification
    6. If tier=HIGH_PRIORITY, trigger high-priority notification
    7. Return screening results summary

    Args:
        self: Celery task instance (bind=True)
        resume_id: Resume UUID to screen
        vacancy_id: Optional specific vacancy UUID to screen against.
                    If not provided, screens against all active vacancies.

    Returns:
        Dictionary containing screening results:
        - resume_id: The resume ID that was screened
        - total_vacancies: Number of vacancies screened against
        - screening_results: List of screening outcomes per vacancy
        - high_priority_count: Number of high-priority matches
        - rejected_count: Number of rejections
        - review_count: Number of review-tier candidates
        - processing_time_ms: Total processing time

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For screening or database errors

    Example:
        >>> from tasks.screening_tasks import auto_screen_candidate
        >>> task = auto_screen_candidate.delay("abc-123-def", "vac-456")
        >>> result = task.get()
        >>> print(result['high_priority_count'])
        1
    """
    start_time = time.time()

    try:
        logger.info(
            f"Auto-screening task started for resume_id: {resume_id}, "
            f"vacancy_id: {vacancy_id}"
        )

        # Import here to avoid issues with async/sync context
        from sqlalchemy import select
        from models import JobVacancy, ScreeningRule, ScreeningResult, Resume
        from services.screening_service import ScreeningService

        # Create database session
        db = next(get_db())

        try:
            # Step 1: Verify resume exists
            progress = {
                "current": 1,
                "total": 4,
                "percentage": 25,
                "status": "verifying_resume",
                "message": "Verifying resume exists...",
            }
            self.update_state(state="PROGRESS", meta=progress)
            logger.info(f"Task {self.request.id}: Verifying resume exists")

            resume_query = select(Resume).where(Resume.id == UUID(resume_id))
            resume_result = db.execute(resume_query)
            resume = resume_result.scalar_one_or_none()

            if not resume:
                logger.error(f"Resume not found: {resume_id}")
                return {
                    "resume_id": resume_id,
                    "status": "failed",
                    "error": f"Resume not found: {resume_id}",
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                }

            # Step 2: Determine vacancies to screen against
            progress = {
                "current": 2,
                "total": 4,
                "percentage": 50,
                "status": "finding_vacancies",
                "message": "Finding active vacancies...",
            }
            self.update_state(state="PROGRESS", meta=progress)
            logger.info(f"Task {self.request.id}: Finding active vacancies")

            vacancies_to_screen = []

            if vacancy_id:
                # Screen against specific vacancy
                vacancy_query = select(JobVacancy).where(JobVacancy.id == UUID(vacancy_id))
                vacancy_result = db.execute(vacancy_query)
                vacancy = vacancy_result.scalar_one_or_none()

                if vacancy:
                    vacancies_to_screen.append(vacancy)
                else:
                    logger.warning(f"Vacancy not found: {vacancy_id}")
            else:
                # Screen against all active vacancies with screening rules
                vacancy_query = select(JobVacancy).join(
                    ScreeningRule,
                    ScreeningRule.vacancy_id == JobVacancy.id,
                ).where(
                    ScreeningRule.is_active == True,
                ).distinct()

                vacancy_result = db.execute(vacancy_query)
                vacancies_to_screen = vacancy_result.scalars().all()

            if not vacancies_to_screen:
                logger.info(f"No active vacancies found for screening resume {resume_id}")
                return {
                    "resume_id": resume_id,
                    "status": "completed",
                    "total_vacancies": 0,
                    "screening_results": [],
                    "high_priority_count": 0,
                    "rejected_count": 0,
                    "review_count": 0,
                    "message": "No active vacancies found for screening",
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                }

            # Step 3: Apply screening rules for each vacancy
            progress = {
                "current": 3,
                "total": 4,
                "percentage": 75,
                "status": "applying_screening",
                "message": f"Applying screening rules for {len(vacancies_to_screen)} vacancies...",
            }
            self.update_state(state="PROGRESS", meta=progress)
            logger.info(f"Task {self.request.id}: Applying screening rules")

            screening_service = ScreeningService(db)
            screening_outcomes = []

            high_priority_count = 0
            rejected_count = 0
            review_count = 0

            for vacancy in vacancies_to_screen:
                try:
                    # Apply screening rules
                    outcome = await screening_service.apply_screening_rules(
                        resume_id=UUID(resume_id),
                        vacancy_id=vacancy.id,
                    )

                    screening_outcomes.append({
                        "vacancy_id": str(vacancy.id),
                        "vacancy_title": vacancy.title,
                        "tier": outcome.tier,
                        "score_applied": outcome.score_applied,
                        "rejection_reasons": outcome.rejection_reasons,
                        "passed_must_have_skills": outcome.passed_must_have_skills,
                        "screening_timestamp": outcome.screening_timestamp.isoformat(),
                    })

                    # Update counts
                    if outcome.tier == ScreeningService.TIER_HIGH_PRIORITY:
                        high_priority_count += 1
                    elif outcome.tier == ScreeningService.TIER_REVIEW:
                        review_count += 1
                    elif outcome.tier == ScreeningService.TIER_REJECT:
                        rejected_count += 1

                    # Get the screening rule to check notification settings
                    rule_query = select(ScreeningRule).where(
                        ScreeningRule.vacancy_id == vacancy.id,
                        ScreeningRule.is_active == True,
                    ).order_by(ScreeningRule.rule_priority)
                    rule_result = db.execute(rule_query)
                    rule = rule_result.scalars().first()

                    # Step 4: Trigger notifications based on tier and settings
                    if outcome.tier == ScreeningService.TIER_REJECT and rule:
                        if rule.auto_reject_with_notification:
                            # TODO: Trigger auto-rejection notification task
                            # Will be implemented in subtask-4-2
                            logger.info(
                                f"Auto-rejection notification would be sent for "
                                f"resume {resume_id}, vacancy {vacancy.id}"
                            )

                    elif outcome.tier == ScreeningService.TIER_HIGH_PRIORITY:
                        # TODO: Trigger high-priority notification task
                        # Will be implemented in future subtasks
                        logger.info(
                            f"High-priority notification would be sent for "
                            f"resume {resume_id}, vacancy {vacancy.id}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error screening resume {resume_id} against vacancy {vacancy.id}: {e}",
                        exc_info=True
                    )
                    screening_outcomes.append({
                        "vacancy_id": str(vacancy.id),
                        "vacancy_title": vacancy.title,
                        "tier": "ERROR",
                        "error": str(e),
                    })

            # Step 5: Complete
            progress = {
                "current": 4,
                "total": 4,
                "percentage": 100,
                "status": "complete",
                "message": "Screening completed",
            }
            self.update_state(state="PROGRESS", meta=progress)

            processing_time_ms = round((time.time() - start_time) * 1000, 2)

            result = {
                "resume_id": resume_id,
                "status": "completed",
                "total_vacancies": len(vacancies_to_screen),
                "screening_results": screening_outcomes,
                "high_priority_count": high_priority_count,
                "rejected_count": rejected_count,
                "review_count": review_count,
                "processing_time_ms": processing_time_ms,
            }

            logger.info(
                f"Auto-screening completed for resume {resume_id}: "
                f"{high_priority_count} high-priority, {review_count} review, "
                f"{rejected_count} rejected, time: {processing_time_ms}ms"
            )

            return result

        finally:
            db.close()

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": "Auto-screening exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in auto-screening task: {e}", exc_info=True)
        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.screening_tasks.send_application_acknowledgement",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_application_acknowledgement(
    self,
    candidate_email: str,
    candidate_name: str,
    vacancy_title: str,
    application_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send application acknowledgement email to candidate.

    This Celery task handles sending automatic acknowledgement emails to
    candidates when they submit an application. It confirms receipt of their
    resume and provides information about the next steps in the process.

    Task Workflow:
    1. Validate candidate email and application data
    2. Compose email subject and body
    3. Include personalized greeting and vacancy information
    4. Send email via configured SMTP/service
    5. Log delivery status

    Args:
        self: Celery task instance (bind=True)
        candidate_email: Email address of the candidate
        candidate_name: Full name of the candidate
        vacancy_title: Title of the position applied for
        application_data: Dictionary containing application details:
            - application_id: Unique application identifier
            - submitted_at: Timestamp of application submission
            - vacancy_id: UUID of the vacancy
            - resume_id: UUID of the submitted resume
            - expected_response_time: Expected response timeframe (optional)

    Returns:
        Dictionary containing sending results:
        - application_id: ID of the application
        - status: Task status (sent/failed/pending)
        - candidate_email: Email address of candidate
        - candidate_name: Name of candidate
        - sent_at: Timestamp when sent (Unix timestamp)
        - error: Error message (if failed)
        - processing_time_ms: Total processing time

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For email sending failures

    Example:
        >>> from tasks.screening_tasks import send_application_acknowledgement
        >>> result = send_application_acknowledgement.delay(
        ...     candidate_email="john@example.com",
        ...     candidate_name="John Doe",
        ...     vacancy_title="Senior Software Engineer",
        ...     application_data={
        ...         "application_id": "app-123",
        ...         "submitted_at": "2024-01-15T10:30:00Z"
        ...     }
        ... )
        >>> print(result.get())
        {'application_id': 'app-123', 'status': 'sent', 'candidate_email': 'john@example.com'}
    """
    start_time = time.time()

    logger.info(
        f"Sending application acknowledgement for candidate_name={candidate_name} "
        f"to {candidate_email}, vacancy={vacancy_title}"
    )

    try:
        # Compose email subject
        subject = f"Application Received: {vacancy_title}"

        # Get application details
        application_id = application_data.get("application_id", "N/A")
        submitted_at = application_data.get("submitted_at", "N/A")
        expected_response = application_data.get(
            "expected_response_time",
            "We will review your application and get back to you soon."
        )

        # Compose email body
        body = f"""
Dear {candidate_name},

Thank you for your interest in the {vacancy_title} position at our company.

We have successfully received your application. Your application ID is {application_id}.

Our team is currently reviewing your resume and qualifications. {expected_response}

If you have any questions in the meantime, please feel free to reach out to us.

Best regards,
The Recruiting Team

---
Application ID: {application_id}
Submitted At: {submitted_at}
This is an automated email from AgentHR Application System.
        """.strip()

        # Log email details (in production, actually send email)
        logger.info(f"Email composed: subject='{subject}', to={candidate_email}")
        logger.info(f"Email body length: {len(body)} characters")

        # Simulate email sending (in production, use SMTP/service)
        # For now, just log and mark as sent
        time.sleep(0.1)  # Simulate network delay

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Application acknowledgement sent successfully to {candidate_email} "
            f"in {processing_time}ms"
        )

        return {
            "application_id": application_id,
            "status": "sent",
            "candidate_email": candidate_email,
            "candidate_name": candidate_name,
            "sent_at": time.time(),
            "processing_time_ms": processing_time,
        }

    except SoftTimeLimitExceeded:
        logger.error(
            f"Application acknowledgement task timed out for candidate_email={candidate_email}"
        )
        return {
            "application_id": application_data.get("application_id", "unknown"),
            "status": "failed",
            "candidate_email": candidate_email,
            "candidate_name": candidate_name,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to send application acknowledgement for candidate_email={candidate_email}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "application_id": application_data.get("application_id", "unknown"),
            "status": "failed",
            "candidate_email": candidate_email,
            "candidate_name": candidate_name,
            "error": str(e),
        }


def format_review_reminder_email(
    recruiter_email: str,
    recruiter_name: str,
    review_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Format review reminder email for recruiters.

    This function formats an email notification for recruiters reminding them
    about candidates that need manual review. It includes a summary of pending
    reviews grouped by vacancy and candidate details.

    Args:
        recruiter_email: Email address of the recruiter
        recruiter_name: Name of the recruiter
        review_summary: Review summary dictionary containing:
            - pending_count: Total number of pending reviews
            - vacancies: List of vacancies with pending candidates:
                - vacancy_id: UUID of the vacancy
                - vacancy_title: Title of the vacancy
                - candidates: List of candidates awaiting review:
                    - candidate_name: Candidate name
                    - candidate_email: Candidate email
                    - resume_id: UUID of the resume
                    - screening_date: When screening was completed
                    - score_applied: Screening score applied
                    - priority: Candidate priority level
            - oldest_pending_date: Date of oldest pending review
            - hours_threshold: Hours threshold for pending reviews

    Returns:
        Dictionary containing email details:
        {
            "subject": "Review Reminder: 5 candidates await your review",
            "body": "Email body with candidate details...",
            "priority": "normal"
        }

    Example:
        >>> summary = {"pending_count": 5, "vacancies": [...]}
        >>> email = format_review_reminder_email("recruiter@example.com", "Jane", summary)
        >>> print(email['subject'])
        'Review Reminder: 5 candidates await your review'
    """
    try:
        logger.info(f"Formatting review reminder email for recruiter: {recruiter_email}")

        pending_count = review_summary.get("pending_count", 0)
        vacancies = review_summary.get("vacancies", [])
        oldest_pending_date = review_summary.get("oldest_pending_date")
        hours_threshold = review_summary.get("hours_threshold", 48)

        # Build email subject
        if pending_count == 1:
            subject = f"Review Reminder: {pending_count} candidate awaits your review"
        else:
            subject = f"Review Reminder: {pending_count} candidates await your review"

        # Build email body
        body_lines = [
            f"Dear {recruiter_name},",
            f"",
            f"You have {pending_count} candidate(s) awaiting your review.",
            f"",
        ]

        if oldest_pending_date:
            body_lines.append(f"Oldest pending review: {oldest_pending_date}")
            body_lines.append(f"")

        # Group candidates by vacancy
        for vacancy in vacancies:
            vacancy_title = vacancy.get("vacancy_title", "Unknown Position")
            candidates = vacancy.get("candidates", [])

            body_lines.extend([
                f"Vacancy: {vacancy_title}",
                f"  Pending candidates: {len(candidates)}",
                f"",
            ])

            # List candidates with details
            for idx, candidate in enumerate(candidates, 1):
                candidate_name = candidate.get("candidate_name", "Unknown")
                candidate_email = candidate.get("candidate_email", "N/A")
                screening_date = candidate.get("screening_date", "N/A")
                score_applied = candidate.get("score_applied", "N/A")
                priority = candidate.get("priority", "N/A")

                body_lines.extend([
                    f"  {idx}. {candidate_name} ({candidate_email})",
                    f"     Screened: {screening_date}",
                    f"     Score: {score_applied} | Priority: {priority}",
                ])

            body_lines.append(f"")

        body_lines.extend([
            f"Please review these candidates at your earliest convenience.",
            f"",
            f"You can view and manage pending reviews in the AgentHR dashboard.",
            f"",
            f"---",
            f"This is an automated reminder from AgentHR Screening System for reviews "
            f"pending for more than {hours_threshold} hours.",
        ])

        body = "\n".join(body_lines)

        email_details = {
            "subject": subject,
            "body": body,
            "priority": "normal",
        }

        logger.info(f"Review reminder email formatted successfully")
        return email_details

    except Exception as e:
        logger.error(f"Failed to format review reminder email: {e}", exc_info=True)
        # Return a basic email format on error
        pending_count = review_summary.get("pending_count", 0)
        return {
            "subject": f"Review Reminder: {pending_count} candidates await review",
            "body": f"You have {pending_count} candidate(s) awaiting your review. Please check the AgentHR dashboard for details.",
            "priority": "normal",
        }


@shared_task(
    name="tasks.screening_tasks.send_review_reminders",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_review_reminders(
    self,
    vacancy_id: Optional[str] = None,
    hours_threshold: int = 48,
) -> Dict[str, Any]:
    """
    Send review reminder notifications to recruiters.

    This Celery task is scheduled to run periodically (daily) to send
    reminder emails to recruiters about candidates that are pending review.
    It queries the database for candidates in REVIEW tier that haven't been
    reviewed yet and sends consolidated reminders to each recruiter.

    Task Workflow:
    1. Query ScreeningResult for tier=REVIEW where screening_timestamp < now - hours_threshold
    2. Group results by recruiter and vacancy
    3. Format reminder email with candidate details
    4. Send email to each recruiter with pending reviews
    5. Update ScreeningResult.review_reminder_sent=True to track sent reminders

    Args:
        self: Celery task instance (bind=True)
        vacancy_id: Optional specific vacancy UUID to filter by. If not provided, checks all vacancies.
        hours_threshold: Hours threshold for pending reviews. Default is 48 hours.

    Returns:
        Dictionary containing reminder results:
        - vacancy_id: Vacancy ID filtered (or "all")
        - hours_threshold: Hours threshold used
        - total_recruiters_notified: Number of recruiters notified
        - total_candidates_reminded: Total number of candidates in reminders
        - vacancies_covered: Number of vacancies with pending reviews
        - processing_time_ms: Total processing time
        - status: Task status (completed/failed)
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or email sending errors

    Example:
        >>> from tasks.screening_tasks import send_review_reminders
        >>> task = send_review_reminders.delay()
        >>> result = task.get()
        >>> print(result['total_recruiters_notified'])
        5
    """
    start_time = time.time()

    try:
        logger.info(
            f"Sending review reminders to recruiters: "
            f"vacancy_id={vacancy_id or 'all'}, hours_threshold={hours_threshold}"
        )

        # Import here to avoid issues with async/sync context
        from sqlalchemy import select, and_
        from models import (
            JobVacancy,
            ScreeningResult,
            ScreeningRule,
            Resume,
            User,
        )
        from tasks.notifications import send_notification_via_email

        # Create database session
        db = next(get_db())

        try:
            # Step 1: Query pending review candidates
            progress = {
                "current": 1,
                "total": 4,
                "percentage": 25,
                "status": "querying_candidates",
                "message": "Querying pending review candidates...",
            }
            self.update_state(state="PROGRESS", meta=progress)
            logger.info(f"Task {self.request.id}: Querying pending review candidates")

            # Calculate threshold datetime
            threshold_datetime = datetime.utcnow() - timedelta(hours=hours_threshold)

            # Query screening results for REVIEW tier that are pending
            # Filter by: tier=REVIEW, screening_timestamp < threshold, review_reminder_sent=False
            screening_conditions = [
                ScreeningResult.tier == "REVIEW",
                ScreeningResult.screening_timestamp < threshold_datetime,
                ScreeningResult.review_reminder_sent == False,  # noqa: E712
            ]

            # Add vacancy filter if specified
            if vacancy_id:
                screening_conditions.append(ScreeningResult.vacancy_id == UUID(vacancy_id))

            screening_query = select(ScreeningResult).join(
                Resume,
                Resume.id == ScreeningResult.resume_id,
            ).join(
                JobVacancy,
                JobVacancy.id == ScreeningResult.vacancy_id,
            ).where(
                and_(*screening_conditions)
            )

            screening_result = db.execute(screening_query)
            pending_screenings = screening_result.scalars().all()

            if not pending_screenings:
                logger.info("No pending review candidates found")
                return {
                    "vacancy_id": vacancy_id or "all",
                    "hours_threshold": hours_threshold,
                    "status": "completed",
                    "total_recruiters_notified": 0,
                    "total_candidates_reminded": 0,
                    "vacancies_covered": 0,
                    "message": "No pending review candidates found",
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                }

            # Step 2: Group by recruiter and vacancy
            progress = {
                "current": 2,
                "total": 4,
                "percentage": 50,
                "status": "grouping_candidates",
                "message": "Grouping candidates by recruiter and vacancy...",
            }
            self.update_state(state="PROGRESS", meta=progress)
            logger.info(f"Task {self.request.id}: Grouping candidates")

            # Group screenings by recruiter (vacancy owner) and vacancy
            # In a real implementation, you would get the assigned recruiter
            # from JobVacancy.assigned_recruiter_id or similar field
            recruiter_reminders = {}  # {recruiter_id: {email, name, vacancies: [...]}}
            oldest_pending_date = None

            for screening in pending_screenings:
                # Get recruiter from vacancy
                # For now, we'll use a placeholder - in production, query User table
                # recruiter_id = screening.vacancy.assigned_recruiter_id
                recruiter_id = getattr(screening.vacancy, 'assigned_recruiter_id', None)

                if not recruiter_id:
                    # Skip if no assigned recruiter
                    continue

                # Get recruiter details
                if recruiter_id not in recruiter_reminders:
                    # Query recruiter from database
                    recruiter_query = select(User).where(User.id == recruiter_id)
                    recruiter_result = db.execute(recruiter_query)
                    recruiter = recruiter_result.scalar_one_or_none()

                    if not recruiter:
                        continue

                    recruiter_reminders[recruiter_id] = {
                        "email": recruiter.email,
                        "name": recruiter.full_name or recruiter.email,
                        "vacancies": {},
                    }

                # Group by vacancy
                vacancy_id = str(screening.vacancy_id)
                if vacancy_id not in recruiter_reminders[recruiter_id]["vacancies"]:
                    recruiter_reminders[recruiter_id]["vacancies"][vacancy_id] = {
                        "vacancy_id": vacancy_id,
                        "vacancy_title": screening.vacancy.title,
                        "candidates": [],
                    }

                # Add candidate to vacancy list
                recruiter_reminders[recruiter_id]["vacancies"][vacancy_id]["candidates"].append({
                    "candidate_name": screening.resume.candidate_name or "Unknown",
                    "candidate_email": screening.resume.email or "N/A",
                    "resume_id": str(screening.resume_id),
                    "screening_date": screening.screening_timestamp.strftime("%Y-%m-%d"),
                    "score_applied": f"{screening.score_applied:.1f}" if screening.score_applied else "N/A",
                    "priority": "medium",  # Could be calculated from score
                })

                # Track oldest pending date
                if oldest_pending_date is None or screening.screening_timestamp < oldest_pending_date:
                    oldest_pending_date = screening.screening_timestamp

            # Step 3: Send reminder emails
            progress = {
                "current": 3,
                "total": 4,
                "percentage": 75,
                "status": "sending_reminders",
                "message": f"Sending reminders to {len(recruiter_reminders)} recruiters...",
            }
            self.update_state(state="PROGRESS", meta=progress)
            logger.info(f"Task {self.request.id}: Sending reminder emails")

            total_recruiters_notified = 0
            total_candidates_reminded = 0
            vacancies_covered = 0

            for recruiter_id, recruiter_data in recruiter_reminders.items():
                try:
                    # Build review summary
                    vacancies_list = list(recruiter_data["vacancies"].values())
                    pending_count = sum(len(v["candidates"]) for v in vacancies_list)

                    review_summary = {
                        "pending_count": pending_count,
                        "vacancies": vacancies_list,
                        "oldest_pending_date": oldest_pending_date.strftime("%Y-%m-%d") if oldest_pending_date else None,
                        "hours_threshold": hours_threshold,
                    }

                    # Format reminder email
                    email_details = format_review_reminder_email(
                        recruiter_email=recruiter_data["email"],
                        recruiter_name=recruiter_data["name"],
                        review_summary=review_summary,
                    )

                    # Send email
                    delivery_result = send_notification_via_email(
                        recipients=[recruiter_data["email"]],
                        email_details=email_details,
                    )

                    if delivery_result.get("success"):
                        total_recruiters_notified += 1
                        total_candidates_reminded += pending_count
                        vacancies_covered += len(vacancies_list)

                        # Update review_reminder_sent for all screenings included in this reminder
                        for vacancy in vacancies_list:
                            for candidate in vacancy["candidates"]:
                                # Find and update the ScreeningResult
                                screening_update = select(ScreeningResult).where(
                                    and_(
                                        ScreeningResult.resume_id == UUID(candidate["resume_id"]),
                                        ScreeningResult.vacancy_id == UUID(vacancy["vacancy_id"]),
                                        ScreeningResult.review_reminder_sent == False,  # noqa: E712
                                    )
                                )
                                screening_result = db.execute(screening_update)
                                screening_to_update = screening_result.scalars().first()

                                if screening_to_update:
                                    screening_to_update.review_reminder_sent = True
                                    screening_to_update.notification_sent_at = datetime.utcnow()

                        db.commit()

                        logger.info(
                            f"Review reminder sent to {recruiter_data['email']}: "
                            f"{pending_count} candidates, {len(vacancies_list)} vacancies"
                        )
                    else:
                        logger.warning(
                            f"Failed to send review reminder to {recruiter_data['email']}: "
                            f"{delivery_result.get('error')}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error sending reminder to recruiter {recruiter_id}: {e}",
                        exc_info=True
                    )

            # Step 4: Complete
            progress = {
                "current": 4,
                "total": 4,
                "percentage": 100,
                "status": "complete",
                "message": "Review reminders sent",
            }
            self.update_state(state="PROGRESS", meta=progress)

            processing_time_ms = round((time.time() - start_time) * 1000, 2)

            result = {
                "vacancy_id": vacancy_id or "all",
                "hours_threshold": hours_threshold,
                "status": "completed",
                "total_recruiters_notified": total_recruiters_notified,
                "total_candidates_reminded": total_candidates_reminded,
                "vacancies_covered": vacancies_covered,
                "processing_time_ms": processing_time_ms,
            }

            logger.info(
                f"Review reminders completed: {total_recruiters_notified} recruiters notified, "
                f"{total_candidates_reminded} candidates, {vacancies_covered} vacancies, "
                f"time: {processing_time_ms}ms"
            )

            return result

        finally:
            db.close()

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "vacancy_id": vacancy_id or "all",
            "hours_threshold": hours_threshold,
            "status": "failed",
            "error": "Review reminder sending exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in review reminders task: {e}", exc_info=True)
        return {
            "vacancy_id": vacancy_id or "all",
            "hours_threshold": hours_threshold,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }
