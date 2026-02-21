"""
Resume builder service for CRUD operations and AI suggestions.

This module provides the core service for the resume builder feature, handling:
- CRUD operations for built resumes
- AI-powered improvement suggestions
- ATS optimization scoring
- Skill gap analysis against target jobs
- Version management and history

The service integrates with existing analyzers and services to provide
comprehensive resume building capabilities.
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.built_resume import BuiltResume
from models.resume_template import ResumeTemplate
from models.job_vacancy import JobVacancy
from schemas.resume_builder import (
    AISuggestion,
    AISuggestionsResponse,
    ATSIssue,
    ATSScoreResponse,
    BuiltResumeCreate,
    BuiltResumeUpdate,
    BuiltResumeResponse,
    BuiltResumeSummary,
    SkillGap,
    SkillGapAnalysisResponse,
    ResumeContent,
)
from analyzers.skill_gap_analyzer import SkillGapAnalyzer, get_skill_gap_analyzer
from analyzers.grammar_checker import check_grammar_resume
from analyzers.resume_optimizer import generate_resume_optimization

logger = logging.getLogger(__name__)


class ResumeBuilderService:
    """
    Service for managing built resumes and providing AI suggestions.

    This service provides comprehensive functionality for the resume builder:
    - Create, read, update, delete operations for resumes
    - AI-powered improvement suggestions
    - ATS optimization scoring
    - Skill gap analysis against target jobs
    - Version management

    Attributes:
        db: Database session for executing queries
        skill_gap_analyzer: Analyzer for skill gap analysis

    Example:
        >>> service = ResumeBuilderService(db)
        >>> resume = await service.create_resume(user_id, org_id, BuiltResumeCreate(...))
        >>> suggestions = await service.get_ai_suggestions(resume.id)
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the resume builder service.

        Args:
            db: Database session for executing queries
        """
        self.db = db
        self.skill_gap_analyzer = get_skill_gap_analyzer()
        logger.info("ResumeBuilderService initialized")

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def create_resume(
        self,
        user_id: str,
        organization_id: str,
        resume_data: BuiltResumeCreate,
    ) -> BuiltResume:
        """
        Create a new resume.

        Args:
            user_id: UUID of the user creating the resume
            organization_id: UUID of the organization
            resume_data: Resume creation data

        Returns:
            Created BuiltResume instance

        Raises:
            ValueError: If template_id is invalid
        """
        logger.info(f"Creating resume for user_id={user_id}, title={resume_data.title}")

        # Validate template if provided
        if resume_data.template_id:
            template = await self._get_template(resume_data.template_id)
            if not template:
                raise ValueError(f"Template not found: {resume_data.template_id}")

        # Prepare content
        content = resume_data.content.model_dump() if resume_data.content else {}

        # Create resume instance
        resume = BuiltResume(
            user_id=user_id,
            organization_id=organization_id,
            template_id=resume_data.template_id,
            title=resume_data.title,
            content=content,
            target_job_id=resume_data.target_job_id,
            is_draft=resume_data.is_draft,
            version=1,
        )

        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)

        logger.info(f"Created resume id={resume.id}, version={resume.version}")
        return resume

    async def get_resume(
        self,
        resume_id: UUID,
        user_id: Optional[str] = None,
    ) -> Optional[BuiltResume]:
        """
        Get a resume by ID.

        Args:
            resume_id: UUID of the resume
            user_id: Optional user ID for ownership verification

        Returns:
            BuiltResume instance or None if not found
        """
        query = select(BuiltResume).where(BuiltResume.id == resume_id)

        if user_id:
            query = query.where(BuiltResume.user_id == user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_resumes(
        self,
        user_id: str,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        include_drafts: bool = True,
    ) -> tuple[List[BuiltResume], int]:
        """
        List resumes for a user.

        Args:
            user_id: UUID of the user
            organization_id: UUID of the organization
            page: Page number (1-indexed)
            page_size: Number of items per page
            include_drafts: Whether to include draft resumes

        Returns:
            Tuple of (list of resumes, total count)
        """
        offset = (page - 1) * page_size

        # Build query
        query = select(BuiltResume).where(
            BuiltResume.user_id == user_id,
            BuiltResume.organization_id == organization_id,
        )

        if not include_drafts:
            query = query.where(BuiltResume.is_draft == False)

        query = query.order_by(BuiltResume.updated_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(BuiltResume).where(
            BuiltResume.user_id == user_id,
            BuiltResume.organization_id == organization_id,
        )
        if not include_drafts:
            count_query = count_query.where(BuiltResume.is_draft == False)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        resumes = list(result.scalars().all())

        logger.info(f"Listed {len(resumes)} resumes for user_id={user_id}, total={total}")
        return resumes, total

    async def update_resume(
        self,
        resume_id: UUID,
        user_id: str,
        update_data: BuiltResumeUpdate,
    ) -> Optional[BuiltResume]:
        """
        Update a resume.

        Automatically increments version on content changes.

        Args:
            resume_id: UUID of the resume
            user_id: UUID of the user (for ownership verification)
            update_data: Update data

        Returns:
            Updated BuiltResume instance or None if not found
        """
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            logger.warning(f"Resume not found: {resume_id}")
            return None

        logger.info(f"Updating resume id={resume_id}, version={resume.version}")

        # Track if content changed (for version increment)
        content_changed = False

        # Update fields
        if update_data.template_id is not None:
            resume.template_id = update_data.template_id
        if update_data.title is not None:
            resume.title = update_data.title
        if update_data.content is not None:
            resume.content = update_data.content.model_dump()
            content_changed = True
        if update_data.target_job_id is not None:
            resume.target_job_id = update_data.target_job_id
        if update_data.ats_score is not None:
            resume.ats_score = update_data.ats_score
        if update_data.is_draft is not None:
            resume.is_draft = update_data.is_draft

        # Increment version if content changed
        if content_changed:
            resume.version += 1

        await self.db.commit()
        await self.db.refresh(resume)

        logger.info(f"Updated resume id={resume_id}, new_version={resume.version}")
        return resume

    async def delete_resume(
        self,
        resume_id: UUID,
        user_id: str,
    ) -> bool:
        """
        Delete a resume.

        Args:
            resume_id: UUID of the resume
            user_id: UUID of the user (for ownership verification)

        Returns:
            True if deleted, False if not found
        """
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            logger.warning(f"Resume not found for deletion: {resume_id}")
            return False

        await self.db.delete(resume)
        await self.db.commit()

        logger.info(f"Deleted resume id={resume_id}")
        return True

    async def duplicate_resume(
        self,
        resume_id: UUID,
        user_id: str,
        new_title: Optional[str] = None,
    ) -> Optional[BuiltResume]:
        """
        Duplicate a resume.

        Creates a copy of the resume with a new ID and reset version.

        Args:
            resume_id: UUID of the resume to duplicate
            user_id: UUID of the user (for ownership verification)
            new_title: Optional new title for the duplicate

        Returns:
            New BuiltResume instance or None if source not found
        """
        original = await self.get_resume(resume_id, user_id)
        if not original:
            logger.warning(f"Resume not found for duplication: {resume_id}")
            return None

        duplicate = BuiltResume(
            user_id=original.user_id,
            organization_id=original.organization_id,
            template_id=original.template_id,
            title=new_title or f"Copy of {original.title}",
            content=original.content.copy() if original.content else {},
            target_job_id=original.target_job_id,
            is_draft=True,  # Duplicates start as drafts
            version=1,
            ats_score=original.ats_score,
        )

        self.db.add(duplicate)
        await self.db.commit()
        await self.db.refresh(duplicate)

        logger.info(f"Duplicated resume {resume_id} -> {duplicate.id}")
        return duplicate

    # =========================================================================
    # AI Suggestions
    # =========================================================================

    async def get_ai_suggestions(
        self,
        resume_id: UUID,
        user_id: Optional[str] = None,
        target_job_description: Optional[str] = None,
    ) -> AISuggestionsResponse:
        """
        Generate AI-powered improvement suggestions for a resume.

        Analyzes the resume content and provides suggestions for:
        - Content improvements (action verbs, achievements)
        - Keyword optimization
        - Formatting recommendations
        - Grammar corrections

        Args:
            resume_id: UUID of the resume
            user_id: Optional user ID for ownership verification
            target_job_description: Optional job description for keyword matching

        Returns:
            AISuggestionsResponse with list of suggestions
        """
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        logger.info(f"Generating AI suggestions for resume_id={resume_id}")

        # Convert content to text for analysis
        resume_text = self._content_to_text(resume.content)
        resume_data = resume.content

        # Get optimization suggestions
        optimization_result = generate_resume_optimization(
            resume_text=resume_text,
            resume_data=resume_data,
            target_job_description=target_job_description,
            check_keywords=True,
            check_formatting=True,
            check_content=True,
        )

        # Get grammar suggestions
        grammar_result = check_grammar_resume(resume_text)

        # Build suggestions list
        suggestions: List[AISuggestion] = []

        # Add optimization suggestions
        for idx, opt_sugg in enumerate(optimization_result.get("suggestions", [])):
            suggestion = AISuggestion(
                id=f"opt-{idx}-{uuid.uuid4().hex[:8]}",
                type=opt_sugg.get("type", "content"),
                section=self._map_category_to_section(opt_sugg.get("category", "")),
                field=None,
                entry_id=None,
                original_text=None,
                suggested_text=opt_sugg.get("recommendation", ""),
                reason=opt_sugg.get("description", ""),
                priority=self._map_priority(opt_sugg.get("priority", "medium")),
                impact_score=None,
            )
            suggestions.append(suggestion)

        # Add grammar suggestions
        if grammar_result.get("errors"):
            for idx, error in enumerate(grammar_result["errors"][:10]):  # Limit to 10
                suggestion = AISuggestion(
                    id=f"gram-{idx}-{uuid.uuid4().hex[:8]}",
                    type="grammar",
                    section="general",
                    field=None,
                    entry_id=None,
                    original_text=error.get("context", ""),
                    suggested_text=error.get("suggestions", [""])[0] if error.get("suggestions") else "",
                    reason=error.get("message", ""),
                    priority=2 if error.get("severity") == "error" else 1,
                    impact_score=5 if error.get("category") == "spelling" else 3,
                )
                suggestions.append(suggestion)

        # Calculate ATS scores
        ats_score_before = resume.ats_score or optimization_result.get("score", 0)
        ats_score_potential = min(100, ats_score_before + len(suggestions) * 3)

        # Build response
        response = AISuggestionsResponse(
            resume_id=str(resume_id),
            suggestions=suggestions,
            ats_score_before=ats_score_before,
            ats_score_potential=ats_score_potential,
            generated_at=datetime.utcnow().isoformat() + "Z",
        )

        # Store suggestions in resume
        resume.last_ai_suggestions = response.model_dump()
        await self.db.commit()

        logger.info(f"Generated {len(suggestions)} suggestions for resume_id={resume_id}")
        return response

    async def apply_suggestion(
        self,
        resume_id: UUID,
        user_id: str,
        suggestion_id: str,
        modified_text: Optional[str] = None,
    ) -> Optional[BuiltResume]:
        """
        Apply an AI suggestion to a resume.

        Args:
            resume_id: UUID of the resume
            user_id: UUID of the user
            suggestion_id: ID of the suggestion to apply
            modified_text: Optional modified version of the suggested text

        Returns:
            Updated BuiltResume or None if not found
        """
        resume = await self.get_resume(resume_id, user_id)
        if not resume or not resume.last_ai_suggestions:
            return None

        # Find the suggestion
        suggestions = resume.last_ai_suggestions.get("suggestions", [])
        target_suggestion = None
        for sugg in suggestions:
            if sugg.get("id") == suggestion_id:
                target_suggestion = sugg
                break

        if not target_suggestion:
            raise ValueError(f"Suggestion not found: {suggestion_id}")

        # Apply the suggestion based on its type and section
        # This is a simplified implementation - in production, you'd have
        # more sophisticated logic to apply suggestions to specific fields
        text_to_apply = modified_text or target_suggestion.get("suggested_text", "")

        # For now, just update the timestamp to reflect the change
        # The actual application logic would depend on the suggestion type
        resume.version += 1

        await self.db.commit()
        await self.db.refresh(resume)

        logger.info(f"Applied suggestion {suggestion_id} to resume {resume_id}")
        return resume

    # =========================================================================
    # ATS Scoring
    # =========================================================================

    async def calculate_ats_score(
        self,
        resume_id: UUID,
        user_id: Optional[str] = None,
    ) -> ATSScoreResponse:
        """
        Calculate ATS compatibility score for a resume.

        Analyzes the resume for:
        - Keyword presence and density
        - Formatting compatibility
        - Section structure
        - Contact information completeness

        Args:
            resume_id: UUID of the resume
            user_id: Optional user ID for ownership verification

        Returns:
            ATSScoreResponse with score and issues
        """
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        logger.info(f"Calculating ATS score for resume_id={resume_id}")

        resume_text = self._content_to_text(resume.content)
        resume_data = resume.content

        # Get optimization analysis
        optimization_result = generate_resume_optimization(
            resume_text=resume_text,
            resume_data=resume_data,
            check_keywords=True,
            check_formatting=True,
            check_content=True,
        )

        # Build issues list
        issues: List[ATSIssue] = []
        for idx, sugg in enumerate(optimization_result.get("suggestions", [])):
            issue = ATSIssue(
                section=self._map_category_to_section(sugg.get("category", "")),
                field=None,
                entry_id=None,
                issue_type=sugg.get("type", "content"),
                severity=sugg.get("priority", "medium"),
                description=sugg.get("description", ""),
                suggestion=sugg.get("recommendation", ""),
            )
            issues.append(issue)

        # Extract keywords
        keywords_found = optimization_result.get("keywords_found", []) or []
        keywords_missing = optimization_result.get("missing_keywords", []) or []

        # Calculate score
        score = optimization_result.get("score", 0)

        # Update resume with score
        resume.ats_score = score
        await self.db.commit()

        response = ATSScoreResponse(
            score=score,
            issues=issues,
            keywords_found=keywords_found,
            keywords_missing=keywords_missing,
            sections_analyzed=self._get_analyzed_sections(resume.content),
            analyzed_at=datetime.utcnow().isoformat() + "Z",
        )

        logger.info(f"ATS score for resume_id={resume_id}: {score}")
        return response

    # =========================================================================
    # Skill Gap Analysis
    # =========================================================================

    async def analyze_skill_gaps(
        self,
        resume_id: UUID,
        target_job_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> SkillGapAnalysisResponse:
        """
        Analyze skill gaps between a resume and target job.

        Args:
            resume_id: UUID of the resume
            target_job_id: Optional job vacancy ID (uses resume's target if not provided)
            user_id: Optional user ID for ownership verification

        Returns:
            SkillGapAnalysisResponse with analysis results
        """
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        # Get target job
        job_id = target_job_id or resume.target_job_id
        if not job_id:
            raise ValueError("No target job specified")

        job = await self._get_job_vacancy(job_id)
        if not job:
            raise ValueError(f"Job vacancy not found: {job_id}")

        logger.info(f"Analyzing skill gaps for resume_id={resume_id}, job_id={job_id}")

        # Extract skills from resume
        candidate_skills = self._extract_skills_from_content(resume.content)
        resume_text = self._content_to_text(resume.content)

        # Get job skills
        job_skills = job.skills or []
        job_skill_levels = job.skill_levels or {} if hasattr(job, 'skill_levels') else {}

        # Run skill gap analysis
        gap_result = self.skill_gap_analyzer.analyze(
            resume_text=resume_text,
            candidate_skills=candidate_skills,
            job_title=job.title,
            job_description=job.description or "",
            required_skills=job_skills,
            required_skill_levels=job_skill_levels,
        )

        # Build response
        matching_skills = gap_result.matched_skills
        partial_match_skills = gap_result.partial_match_skills

        missing_skills: List[SkillGap] = []
        for skill_name in gap_result.missing_skills:
            details = gap_result.missing_skill_details.get(skill_name, {})
            missing_skills.append(SkillGap(
                skill_name=skill_name,
                category=details.get("category"),
                importance="high" if details.get("importance") == "high" else "preferred",
                job_frequency=None,
                learning_resources=[],
            ))

        match_percentage = int(100 - gap_result.gap_percentage)

        response = SkillGapAnalysisResponse(
            target_job_id=str(job_id),
            target_job_title=job.title,
            matching_skills=matching_skills,
            partial_match_skills=partial_match_skills,
            missing_skills=missing_skills,
            match_percentage=match_percentage,
            recommendations=self._generate_recommendations(gap_result),
            analyzed_at=datetime.utcnow().isoformat() + "Z",
        )

        logger.info(
            f"Skill gap analysis complete: {len(matching_skills)} matching, "
            f"{len(missing_skills)} missing, {match_percentage}% match"
        )
        return response

    # =========================================================================
    # Version History
    # =========================================================================

    async def get_version_history(
        self,
        resume_id: UUID,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get version history for a resume.

        Note: This is a simplified implementation. In production, you might
        store version snapshots in a separate table.

        Args:
            resume_id: UUID of the resume
            user_id: Optional user ID for ownership verification

        Returns:
            Dictionary with version history information
        """
        resume = await self.get_resume(resume_id, user_id)
        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        # For now, return current version info
        # In production, you'd query a version history table
        return {
            "resume_id": str(resume_id),
            "current_version": resume.version,
            "versions": [
                {
                    "version": resume.version,
                    "title": resume.title,
                    "ats_score": resume.ats_score,
                    "created_at": resume.updated_at.isoformat() if resume.updated_at else None,
                    "changes_summary": "Current version",
                }
            ],
        }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _get_template(self, template_id: str) -> Optional[ResumeTemplate]:
        """Get a resume template by ID."""
        try:
            result = await self.db.execute(
                select(ResumeTemplate).where(ResumeTemplate.id == template_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching template {template_id}: {e}")
            return None

    async def _get_job_vacancy(self, job_id: str) -> Optional[JobVacancy]:
        """Get a job vacancy by ID."""
        try:
            result = await self.db.execute(
                select(JobVacancy).where(JobVacancy.id == job_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching job vacancy {job_id}: {e}")
            return None

    def _content_to_text(self, content: Dict[str, Any]) -> str:
        """
        Convert resume content dict to plain text for analysis.

        Args:
            content: Resume content dictionary

        Returns:
            Plain text representation of the resume
        """
        parts = []

        # Personal info
        personal = content.get("personal_info", {})
        if personal:
            if personal.get("full_name"):
                parts.append(personal["full_name"])
            if personal.get("title"):
                parts.append(personal["title"])
            if personal.get("summary"):
                parts.append(personal["summary"])

        # Summary
        if content.get("summary"):
            parts.append(content["summary"])

        # Work experience
        for exp in content.get("work_experience", []):
            if exp.get("position"):
                parts.append(exp["position"])
            if exp.get("company"):
                parts.append(exp["company"])
            if exp.get("description"):
                parts.append(exp["description"])
            parts.extend(exp.get("highlights", []))

        # Education
        for edu in content.get("education", []):
            if edu.get("degree"):
                parts.append(edu["degree"])
            if edu.get("field_of_study"):
                parts.append(edu["field_of_study"])
            if edu.get("institution"):
                parts.append(edu["institution"])
            if edu.get("description"):
                parts.append(edu["description"])

        # Skills
        for skill in content.get("skills", []):
            if isinstance(skill, dict):
                parts.append(skill.get("name", ""))
            else:
                parts.append(str(skill))

        # Certifications
        for cert in content.get("certifications", []):
            if cert.get("name"):
                parts.append(cert["name"])

        # Projects
        for proj in content.get("projects", []):
            if proj.get("name"):
                parts.append(proj["name"])
            if proj.get("description"):
                parts.append(proj["description"])
            parts.extend(proj.get("technologies", []))

        return " ".join(filter(None, parts))

    def _extract_skills_from_content(self, content: Dict[str, Any]) -> List[str]:
        """
        Extract skills list from resume content.

        Args:
            content: Resume content dictionary

        Returns:
            List of skill names
        """
        skills = []

        for skill in content.get("skills", []):
            if isinstance(skill, dict):
                name = skill.get("name")
                if name:
                    skills.append(name)
            else:
                skills.append(str(skill))

        return skills

    def _map_category_to_section(self, category: str) -> str:
        """Map optimization category to resume section."""
        mapping = {
            "keywords": "skills",
            "structure": "general",
            "readability": "general",
            "impact": "work_experience",
            "action_verbs": "work_experience",
            "summary": "summary",
            "active_language": "work_experience",
            "achievements": "work_experience",
        }
        return mapping.get(category, "general")

    def _map_priority(self, priority: str) -> int:
        """Map priority string to integer (0=low, 1=medium, 2=high)."""
        mapping = {
            "low": 0,
            "medium": 1,
            "high": 2,
        }
        return mapping.get(priority.lower(), 1)

    def _get_analyzed_sections(self, content: Dict[str, Any]) -> List[str]:
        """Get list of sections that were analyzed."""
        sections = []

        if content.get("personal_info"):
            sections.append("personal_info")
        if content.get("summary"):
            sections.append("summary")
        if content.get("work_experience"):
            sections.append("work_experience")
        if content.get("education"):
            sections.append("education")
        if content.get("skills"):
            sections.append("skills")
        if content.get("certifications"):
            sections.append("certifications")
        if content.get("projects"):
            sections.append("projects")
        if content.get("languages"):
            sections.append("languages")

        return sections

    def _generate_recommendations(self, gap_result) -> List[str]:
        """Generate recommendations based on skill gap analysis."""
        recommendations = []

        if gap_result.gap_severity == "critical":
            recommendations.append(
                "Consider focusing on learning the missing skills before applying. "
                "The skill gap is significant."
            )
        elif gap_result.gap_severity == "moderate":
            recommendations.append(
                "You have a good foundation but should work on the missing skills "
                "to strengthen your application."
            )

        if gap_result.estimated_time_to_bridge > 0:
            recommendations.append(
                f"Estimated time to bridge skill gaps: "
                f"{gap_result.estimated_time_to_bridge} hours of learning."
            )

        if gap_result.priority_ordering:
            top_priorities = gap_result.priority_ordering[:3]
            recommendations.append(
                f"Priority skills to learn: {', '.join(top_priorities)}"
            )

        return recommendations


# Global service instance
_resume_builder_service: Optional[ResumeBuilderService] = None


def get_resume_builder_service(db: AsyncSession) -> ResumeBuilderService:
    """
    Get or create the resume builder service instance.

    Args:
        db: Database session

    Returns:
        ResumeBuilderService instance
    """
    return ResumeBuilderService(db)
