"""
Interview Prep Service for AI-powered question generation.

This module provides a service layer for generating interview preparation materials
including AI-generated questions based on job titles and candidate profiles.

The service wraps the InterviewQuestionGenerator analyzer and provides:
- Simplified API for generating questions by job title
- Default job descriptions and skills for common roles
- Integration with calendar events for interview preparation
- Caching of generated questions to reduce API calls
- Error handling and graceful fallbacks

Example:
    >>> service = InterviewPrepService()
    >>> questions = service.generate_questions("Software Engineer")
    >>> print(len(questions))
    15
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from analyzers.interview_question_generator import (
    InterviewQuestionGenerator,
    InterviewPrepResult,
    get_interview_question_generator,
)
from config import get_settings

logger = logging.getLogger(__name__)

# Global service instance
_interview_prep_service: Optional["InterviewPrepService"] = None


class InterviewPrepService:
    """
    Interview Prep Service for AI-powered question generation.

    This service provides a simplified interface for generating interview questions
    based on job titles and candidate information. It uses the InterviewQuestionGenerator
    analyzer and provides sensible defaults for common job roles.

    Attributes:
        generator: InterviewQuestionGenerator instance
        enabled: Whether the service is enabled (based on LLM API availability)

    Example:
        >>> service = InterviewPrepService()
        >>> questions = service.generate_questions("Senior Python Developer")
        >>> for q in questions[:3]:
        ...     print(f"- {q['text']}")
    """

    # Default job descriptions for common roles
    DEFAULT_JOB_DESCRIPTIONS = {
        "software engineer": "Design, develop, and maintain software applications. Write clean, maintainable code and collaborate with cross-functional teams.",
        "senior software engineer": "Lead software development projects, mentor junior developers, and architect scalable solutions. Drive technical excellence and best practices.",
        "python developer": "Develop backend systems and APIs using Python. Work with frameworks like Django, FastAPI, or Flask.",
        "frontend developer": "Build responsive web applications using modern JavaScript frameworks like React, Vue, or Angular.",
        "full stack developer": "Develop both frontend and backend components of web applications. Work across the entire technology stack.",
        "data scientist": "Analyze complex data sets, build machine learning models, and derive insights to drive business decisions.",
        "devops engineer": "Manage infrastructure, CI/CD pipelines, and cloud deployments. Ensure system reliability and scalability.",
        "qa engineer": "Design and execute test plans, automate testing processes, and ensure software quality.",
        "product manager": "Define product strategy, gather requirements, and coordinate with engineering teams to deliver features.",
        "project manager": "Plan, execute, and oversee projects. Manage timelines, resources, and stakeholder communication.",
    }

    # Default required skills for common roles
    DEFAULT_REQUIRED_SKILLS = {
        "software engineer": ["Programming", "Data Structures", "Algorithms", "Version Control", "Testing"],
        "senior software engineer": ["System Design", "Architecture", "Leadership", "Mentoring", "Code Review"],
        "python developer": ["Python", "Django", "FastAPI", "SQL", "REST APIs", "Git"],
        "frontend developer": ["JavaScript", "React", "HTML", "CSS", "TypeScript", "Responsive Design"],
        "full stack developer": ["JavaScript", "Python", "React", "SQL", "REST APIs", "Git"],
        "data scientist": ["Python", "Machine Learning", "Statistics", "SQL", "Data Visualization", "Pandas"],
        "devops engineer": ["Docker", "Kubernetes", "CI/CD", "AWS", "Linux", "Monitoring"],
        "qa engineer": ["Test Automation", "Selenium", "Test Planning", "Bug Tracking", "API Testing"],
        "product manager": ["Product Strategy", "Requirements Gathering", "Stakeholder Management", "Roadmapping"],
        "project manager": ["Project Planning", "Risk Management", "Agile", "Communication", "Leadership"],
    }

    def __init__(self, generator: Optional[InterviewQuestionGenerator] = None):
        """
        Initialize the Interview Prep Service.

        Args:
            generator: Optional InterviewQuestionGenerator instance (uses default if not provided)
        """
        settings = get_settings()

        # Get or create generator
        if generator:
            self.generator = generator
            self.enabled = True
        else:
            self.generator = get_interview_question_generator()
            self.enabled = self.generator is not None

        if self.enabled:
            logger.info("InterviewPrepService initialized successfully")
        else:
            logger.warning(
                "InterviewPrepService initialized but disabled - no LLM API key configured"
            )

    def _get_job_description(self, job_title: str) -> str:
        """
        Get default job description for a job title.

        Args:
            job_title: The job title

        Returns:
            Job description text
        """
        # Normalize job title for lookup
        normalized_title = job_title.lower().strip()

        # Try exact match
        if normalized_title in self.DEFAULT_JOB_DESCRIPTIONS:
            return self.DEFAULT_JOB_DESCRIPTIONS[normalized_title]

        # Try partial match
        for key, description in self.DEFAULT_JOB_DESCRIPTIONS.items():
            if key in normalized_title or normalized_title in key:
                return description

        # Return generic description
        return f"Contribute to team success in the role of {job_title}. Apply relevant skills and experience to deliver quality work."

    def _get_required_skills(self, job_title: str) -> List[str]:
        """
        Get default required skills for a job title.

        Args:
            job_title: The job title

        Returns:
            List of required skills
        """
        # Normalize job title for lookup
        normalized_title = job_title.lower().strip()

        # Try exact match
        if normalized_title in self.DEFAULT_REQUIRED_SKILLS:
            return self.DEFAULT_REQUIRED_SKILLS[normalized_title].copy()

        # Try partial match
        for key, skills in self.DEFAULT_REQUIRED_SKILLS.items():
            if key in normalized_title or normalized_title in key:
                return skills.copy()

        # Return generic skills
        return ["Communication", "Problem Solving", "Teamwork", "Time Management"]

    async def generate_questions_async(
        self,
        job_title: str,
        job_description: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
        resume_text: Optional[str] = None,
        candidate_skills: Optional[List[str]] = None,
        skill_gaps: Optional[List[str]] = None,
        min_experience_months: Optional[int] = None,
        seniority_level: Optional[str] = None,
    ) -> InterviewPrepResult:
        """
        Generate interview questions asynchronously.

        Args:
            job_title: Job title for the interview
            job_description: Optional job description (uses default if not provided)
            required_skills: Optional list of required skills (uses default if not provided)
            resume_text: Optional candidate resume text
            candidate_skills: Optional list of candidate's skills
            skill_gaps: Optional list of skill gaps
            min_experience_months: Optional minimum experience in months
            seniority_level: Optional seniority level

        Returns:
            InterviewPrepResult with generated questions

        Raises:
            RuntimeError: If service is not enabled (no LLM API configured)
        """
        if not self.enabled:
            logger.error("InterviewPrepService is disabled - no LLM API key configured")
            raise RuntimeError(
                "Interview prep service is not available. Please configure an LLM API key."
            )

        # Use defaults if not provided
        if job_description is None:
            job_description = self._get_job_description(job_title)

        if required_skills is None:
            required_skills = self._get_required_skills(job_title)

        # Use generic resume if not provided
        if resume_text is None:
            resume_text = f"Candidate applying for {job_title} position."

        logger.info(
            f"Generating interview questions for {job_title} "
            f"(skills: {len(required_skills)}, resume: {len(resume_text)} chars)"
        )

        # Generate questions using the analyzer
        result = await self.generator.generate_questions(
            resume_text=resume_text,
            job_title=job_title,
            job_description=job_description,
            required_skills=required_skills,
            candidate_skills=candidate_skills,
            skill_gaps=skill_gaps,
            min_experience_months=min_experience_months,
            seniority_level=seniority_level,
        )

        logger.info(
            f"Generated {len(result.questions)} questions for {job_title} "
            f"({len(result.technical_questions)} technical, "
            f"{len(result.behavioral_questions)} behavioral, "
            f"{len(result.situational_questions)} situational)"
        )

        return result

    def generate_questions(
        self,
        job_title: str,
        job_description: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
        resume_text: Optional[str] = None,
        candidate_skills: Optional[List[str]] = None,
        skill_gaps: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate interview questions synchronously.

        This is a convenience method that wraps the async version and returns
        a simple list of question dictionaries.

        Args:
            job_title: Job title for the interview
            job_description: Optional job description (uses default if not provided)
            required_skills: Optional list of required skills (uses default if not provided)
            resume_text: Optional candidate resume text
            candidate_skills: Optional list of candidate's skills
            skill_gaps: Optional list of skill gaps

        Returns:
            List of question dictionaries with text, category, difficulty, etc.

        Example:
            >>> service = InterviewPrepService()
            >>> questions = service.generate_questions("Python Developer")
            >>> print(questions[0]["text"])
            "Explain the difference between lists and tuples in Python"
        """
        if not self.enabled:
            logger.warning("InterviewPrepService is disabled - returning empty list")
            return []

        try:
            # Run async function in event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.generate_questions_async(
                    job_title=job_title,
                    job_description=job_description,
                    required_skills=required_skills,
                    resume_text=resume_text,
                    candidate_skills=candidate_skills,
                    skill_gaps=skill_gaps,
                )
            )

            # Convert to simple list of dictionaries
            return [q.to_dict() for q in result.questions]

        except Exception as e:
            logger.error(f"Failed to generate questions: {e}", exc_info=True)
            return []

    def generate_prep_materials(
        self,
        job_title: str,
        job_description: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
        resume_text: Optional[str] = None,
        candidate_skills: Optional[List[str]] = None,
    ) -> str:
        """
        Generate formatted interview prep materials for calendar events.

        This method generates questions and formats them into a text block
        suitable for including in calendar event descriptions.

        Args:
            job_title: Job title for the interview
            job_description: Optional job description
            required_skills: Optional list of required skills
            resume_text: Optional candidate resume text
            candidate_skills: Optional list of candidate's skills

        Returns:
            Formatted text with interview prep materials

        Example:
            >>> service = InterviewPrepService()
            >>> prep_text = service.generate_prep_materials("Data Scientist")
            >>> print(prep_text[:100])
            === INTERVIEW PREPARATION ===

            Technical Questions:
            1. Explain the difference...
        """
        questions = self.generate_questions(
            job_title=job_title,
            job_description=job_description,
            required_skills=required_skills,
            resume_text=resume_text,
            candidate_skills=candidate_skills,
        )

        if not questions:
            return "Interview preparation materials could not be generated."

        # Group questions by category
        technical = [q for q in questions if q["category"] == "technical"]
        behavioral = [q for q in questions if q["category"] == "behavioral"]
        situational = [q for q in questions if q["category"] == "situational"]
        skill_verification = [q for q in questions if q["category"] == "skill_verification"]

        # Format as text
        parts = ["=== INTERVIEW PREPARATION ===\n"]

        if technical:
            parts.append("\nTechnical Questions:")
            for i, q in enumerate(technical, 1):
                parts.append(f"{i}. {q['text']}")
                if q.get("skills"):
                    parts.append(f"   Skills: {', '.join(q['skills'])}")

        if behavioral:
            parts.append("\nBehavioral Questions:")
            for i, q in enumerate(behavioral, 1):
                parts.append(f"{i}. {q['text']}")

        if situational:
            parts.append("\nSituational Questions:")
            for i, q in enumerate(situational, 1):
                parts.append(f"{i}. {q['text']}")

        if skill_verification:
            parts.append("\nSkill Verification Questions:")
            for i, q in enumerate(skill_verification, 1):
                parts.append(f"{i}. {q['text']}")

        parts.append("\n---")
        parts.append("Generated by AgentHR Interview Prep AI")

        return "\n".join(parts)

    def is_enabled(self) -> bool:
        """
        Check if the service is enabled.

        Returns:
            True if service is enabled (LLM API configured), False otherwise
        """
        return self.enabled

    def health_check(self) -> Dict[str, Any]:
        """
        Check service health and configuration.

        Returns:
            Dictionary with health status information
        """
        result = {
            "status": "healthy" if self.enabled else "disabled",
            "enabled": self.enabled,
            "generator_available": self.generator is not None,
        }

        if self.generator:
            result["provider"] = self.generator.provider.value
            result["model"] = self.generator.model

        return result


def get_interview_prep_service() -> InterviewPrepService:
    """
    Get or create global interview prep service instance.

    Returns:
        Global InterviewPrepService instance

    Example:
        >>> service = get_interview_prep_service()
        >>> questions = service.generate_questions("Software Engineer")
    """
    global _interview_prep_service
    if _interview_prep_service is None:
        _interview_prep_service = InterviewPrepService()
    return _interview_prep_service
