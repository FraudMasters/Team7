"""
SkillDevelopmentPlan model for tracking candidate upskilling progress
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SkillDevelopmentPlan(Base, UUIDMixin, TimestampMixin):
    """
    SkillDevelopmentPlan model for tracking candidate skill development progress

    This model stores personalized skill development plans for candidates,
    tracking their progress through recommended learning resources and
    milestones to bridge skill gaps for specific roles.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        vacancy_id: Foreign key to JobVacancy (optional, for role-specific plans)
        skill_gap_report_id: Foreign key to SkillGapReport that generated this plan

        # Plan details
        title: Title of the development plan
        description: Detailed description of the plan objectives
        status: Current status of the plan (draft, active, completed, paused, abandoned)
        overall_progress: Overall completion percentage (0-100)

        # Timeline
        start_date: Planned or actual start date
        target_completion_date: Target date for plan completion
        actual_completion_date: Actual date when plan was completed (if applicable)

        # Plan content
        learning_goals: JSON array of specific learning goals
        milestones: JSON array of milestones with completion status
        recommended_resources: JSON array of learning resource IDs and details
        completed_resources: JSON array of completed resource IDs and completion dates

        # Progress tracking
        total_resources_count: Total number of resources in the plan
        completed_resources_count: Number of resources completed
        hours_invested: Total hours spent on learning activities
        estimated_hours_remaining: Estimated hours remaining to complete the plan

        # Sharing and access
        shareable_token: Unique token for sharing the plan publicly
        is_public: Whether the plan is publicly accessible via share link
        shared_with_recruiters: JSON array of recruiter IDs who have access
        access_expires_at: Optional expiration date for shared access

        # Engagement tracking
        last_accessed_at: Timestamp when the plan was last accessed by the candidate
        reminder_scheduled_at: Timestamp when the next reminder is scheduled
        reminder_frequency: Frequency of reminders (daily, weekly, monthly, none)
        notes: Candidate's personal notes about the plan

        # Outcome tracking
        reapplication_status: Status of reapplication after upskilling (not_applied, applied, interviewing, offered, hired)
        reapplication_date: Date when candidate reapplied after completing the plan
        outcome_notes: Notes about the outcome of the development plan

        # Additional metadata
        priority: Priority level of the plan (low, medium, high, urgent)
        difficulty_level: Perceived difficulty level (beginner, intermediate, advanced, expert)
        tags: JSON array of tags for categorizing the plan
        metadata: JSON object for additional plan-specific data

        created_at: Timestamp when plan was created (inherited)
        updated_at: Timestamp when plan was last updated (inherited)
    """

    __tablename__ = "skill_development_plans"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    skill_gap_report_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("skill_gap_reports.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Plan details
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )  # draft, active, completed, paused, abandoned
    overall_progress: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.0
    )  # 0-100

    # Timeline
    start_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_completion_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    actual_completion_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Plan content
    learning_goals: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    milestones: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    recommended_resources: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    completed_resources: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Progress tracking
    total_resources_count: Mapped[int] = mapped_column(nullable=False, default=0)
    completed_resources_count: Mapped[int] = mapped_column(nullable=False, default=0)
    hours_invested: Mapped[float] = mapped_column(
        Numeric(8, 2), nullable=False, default=0.0
    )
    estimated_hours_remaining: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2), nullable=True, default=None
    )

    # Sharing and access
    shareable_token: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )
    is_public: Mapped[bool] = mapped_column(nullable=False, default=False)
    shared_with_recruiters: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    access_expires_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Engagement tracking
    last_accessed_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reminder_scheduled_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reminder_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="none"
    )  # daily, weekly, monthly, none
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Outcome tracking
    reapplication_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="not_applied"
    )  # not_applied, applied, interviewing, offered, hired
    reapplication_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    outcome_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional metadata
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium", index=True
    )  # low, medium, high, urgent
    difficulty_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )  # beginner, intermediate, advanced, expert
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    plan_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SkillDevelopmentPlan(id={self.id}, title='{self.title}', "
            f"status={self.status}, progress={self.overall_progress}%)>"
        )
