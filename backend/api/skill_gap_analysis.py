"""
Skill gap analysis endpoints for comparing candidate skills against job requirements.

This module provides endpoints for analyzing skill gaps between candidates and job vacancies,
generating comprehensive reports, and providing learning recommendations to help candidates
bridge the gaps.
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path to import from data_extractor service
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "data_extractor"))

from database import get_db
from models.skill_gap import SkillGapReport
from models.learning_resource import LearningResource
from models.skill_development_plan import SkillDevelopmentPlan

from analyzers import (
    extract_resume_keywords_hf as extract_resume_keywords,
    extract_resume_entities,
)
from analyzers.skill_gap_analyzer import SkillGapAnalyzer, get_skill_gap_analyzer, SkillGapResult
from analyzers.learning_recommendation_engine import (
    LearningRecommendationEngine,
    get_learning_recommendation_engine,
)
from i18n.backend_translations import get_error_message, get_success_message

logger = logging.getLogger(__name__)

router = APIRouter()

# Directory where uploaded resumes are stored
UPLOAD_DIR = Path("data/uploads")


def _extract_locale(request: Optional[Request]) -> str:
    """
    Extract Accept-Language header from request.

    Args:
        request: The incoming FastAPI request (optional)

    Returns:
        Language code (e.g., 'en', 'ru')
    """
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


class SkillGapAnalysisRequest(BaseModel):
    """Request model for skill gap analysis endpoint."""

    resume_id: str = Field(..., description="Unique identifier of the resume to analyze")
    vacancy_data: Dict[str, Any] = Field(
        ..., description="Job vacancy data with required skills and experience"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "resume_id": "abc123-def456-ghi789",
            "vacancy_data": {
                "id": "vacancy-123",
                "title": "Senior React Developer",
                "description": "Looking for an experienced React developer with TypeScript skills",
                "required_skills": [
                    "React",
                    "TypeScript",
                    "JavaScript",
                    "AWS",
                    "Docker",
                    "GraphQL"
                ],
                "required_skill_levels": {
                    "React": "advanced",
                    "TypeScript": "intermediate",
                    "JavaScript": "advanced",
                    "AWS": "beginner",
                    "Docker": "intermediate",
                    "GraphQL": "intermediate"
                },
                "required_experience_years": 5,
                "required_education": ["Bachelor's Degree"]
            }
        }
    })


class SkillGapAnalysisResponse(BaseModel):
    """Response model for skill gap analysis."""

    report_id: str = Field(..., description="Unique identifier of the generated report")
    resume_id: str = Field(..., description="Resume identifier")
    vacancy_id: Optional[str] = Field(None, description="Vacancy identifier (if provided)")
    vacancy_title: str = Field(..., description="Job vacancy title")

    # Candidate skills
    candidate_skills: List[str] = Field(..., description="Skills extracted from candidate's resume")

    # Required skills
    required_skills: List[str] = Field(..., description="Skills required by the vacancy")

    # Analysis results
    matched_skills: List[str] = Field(..., description="Skills that match requirements")
    missing_skills: List[str] = Field(..., description="Required skills not found in candidate's resume")
    partial_match_skills: List[str] = Field(
        ..., description="Skills present but at insufficient proficiency level"
    )

    # Detailed analysis
    missing_skill_details: Dict[str, Dict[str, Any]] = Field(
        ..., description="Detailed info about each missing skill"
    )

    # Overall assessment
    gap_severity: str = Field(..., description="Overall severity: critical, moderate, minimal, or none")
    gap_percentage: float = Field(..., description="Percentage of required skills missing (0-100)")
    bridgeability_score: float = Field(
        ..., description="Score indicating how easily gaps can be bridged (0-1)"
    )
    estimated_time_to_bridge: int = Field(..., description="Estimated hours to bridge all gaps")

    # Priority ordering
    priority_ordering: List[str] = Field(
        ..., description="Optimal order for addressing skill gaps"
    )

    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "report_id": "report-uuid-12345",
            "resume_id": "abc123-def456-ghi789",
            "vacancy_id": "vacancy-123",
            "vacancy_title": "Senior React Developer",
            "candidate_skills": ["JavaScript", "React", "HTML", "CSS", "Git"],
            "required_skills": ["React", "TypeScript", "JavaScript", "AWS", "Docker", "GraphQL"],
            "matched_skills": ["React", "JavaScript"],
            "missing_skills": ["TypeScript", "AWS", "Docker", "GraphQL"],
            "partial_match_skills": [],
            "missing_skill_details": {
                "TypeScript": {
                    "status": "missing",
                    "required_level": "intermediate",
                    "category": "programming_language",
                    "importance": "high"
                },
                "AWS": {
                    "status": "missing",
                    "required_level": "beginner",
                    "category": "cloud_devops",
                    "importance": "medium"
                },
                "Docker": {
                    "status": "missing",
                    "required_level": "intermediate",
                    "category": "cloud_devops",
                    "importance": "high"
                },
                "GraphQL": {
                    "status": "missing",
                    "required_level": "intermediate",
                    "category": "web_framework",
                    "importance": "medium"
                }
            },
            "gap_severity": "moderate",
            "gap_percentage": 66.7,
            "bridgeability_score": 0.65,
            "estimated_time_to_bridge": 80,
            "priority_ordering": ["TypeScript", "Docker", "GraphQL", "AWS"],
            "processing_time_ms": 150.5
        }
    })


class SkillGapReportResponse(BaseModel):
    """Response model for a skill gap report."""

    id: str = Field(..., description="Report ID")
    resume_id: str = Field(..., description="Resume ID")
    vacancy_id: str = Field(..., description="Vacancy ID")
    candidate_skills: List[str] = Field(..., description="Candidate's skills")
    required_skills: List[str] = Field(..., description="Required skills")
    matched_skills: List[str] = Field(..., description="Matched skills")
    missing_skills: List[str] = Field(..., description="Missing skills")
    partial_match_skills: List[str] = Field(..., description="Partial match skills")
    gap_severity: str = Field(..., description="Gap severity")
    gap_percentage: float = Field(..., description="Gap percentage")
    bridgeability_score: float = Field(..., description="Bridgeability score")
    estimated_time_to_bridge: int = Field(..., description="Estimated time to bridge (hours)")
    priority_ordering: List[str] = Field(..., description="Priority ordering")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class SkillGapReportListResponse(BaseModel):
    """Response model for listing skill gap reports."""

    reports: List[SkillGapReportResponse] = Field(..., description="List of skill gap reports")
    total: int = Field(..., description="Total number of reports")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of reports per page")


# Learning Resource Models
class LearningResourceResponse(BaseModel):
    """Response model for a single learning resource."""

    id: str = Field(..., description="Resource ID")
    title: str = Field(..., description="Resource title")
    description: Optional[str] = Field(None, description="Resource description")
    resource_type: str = Field(..., description="Type of resource (course, certification, tutorial, etc.)")
    source_platform: Optional[str] = Field(None, description="Platform offering the resource")

    # Content details
    skills_taught: List[str] = Field(default_factory=list, description="Skills that this resource teaches")
    skill_level: Optional[str] = Field(None, description="Difficulty level (beginner, intermediate, advanced, expert)")
    topics_covered: List[str] = Field(default_factory=list, description="Topics covered")
    prerequisites: List[str] = Field(default_factory=list, description="Required prior knowledge")

    # Access information
    url: Optional[str] = Field(None, description="URL to access the resource")
    access_type: str = Field(..., description="Access type (free, paid, freemium, subscription)")
    cost_amount: Optional[float] = Field(None, description="Cost in currency")
    currency: str = Field(..., description="Currency code")

    # Time investment
    duration_hours: Optional[float] = Field(None, description="Estimated duration in hours")
    duration_weeks: Optional[float] = Field(None, description="Estimated duration in weeks")
    is_self_paced: bool = Field(..., description="Whether the resource is self-paced")

    # Quality metrics
    rating: Optional[float] = Field(None, description="Average rating (0-5)")
    rating_count: int = Field(..., description="Number of ratings")
    popularity_score: Optional[float] = Field(None, description="Popularity score (0-1)")
    quality_score: Optional[float] = Field(None, description="Quality score (0-1)")

    # Provider information
    provider_name: Optional[str] = Field(None, description="Name of the provider")
    instructor_name: Optional[str] = Field(None, description="Name of the instructor")
    certificate_offered: bool = Field(..., description="Whether completion certificate is offered")
    certificate_url: Optional[str] = Field(None, description="URL to sample certificate")

    # Additional metadata
    language: str = Field(..., description="Resource language")
    is_active: bool = Field(..., description="Whether this resource is active")
    is_verified: bool = Field(..., description="Whether this resource is verified")
    recommendation_count: int = Field(..., description="Number of times recommended")

    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class LearningResourceListResponse(BaseModel):
    """Response model for listing learning resources."""

    resources: List[LearningResourceResponse] = Field(..., description="List of learning resources")
    total: int = Field(..., description="Total number of resources")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")


class LearningRecommendationRequest(BaseModel):
    """Request model for getting learning recommendations."""

    skills: List[str] = Field(..., description="List of skills to get recommendations for")
    skill_levels: Optional[Dict[str, str]] = Field(None, description="Target skill levels for each skill")
    max_recommendations_per_skill: int = Field(5, description="Maximum recommendations per skill")
    max_cost_per_resource: Optional[float] = Field(None, description="Maximum cost per resource")
    include_free_resources: bool = Field(True, description="Include free resources")
    min_rating: float = Field(0.0, description="Minimum rating (0-5)")
    preferred_languages: List[str] = Field(default_factory=lambda: ["en"], description="Preferred languages")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "skills": ["Python", "Docker"],
            "skill_levels": {
                "Python": "intermediate",
                "Docker": "beginner"
            },
            "max_recommendations_per_skill": 5,
            "max_cost_per_resource": 50.0,
            "include_free_resources": True,
            "min_rating": 4.0,
            "preferred_languages": ["en"]
        }
    })


class LearningRecommendationResponse(BaseModel):
    """Response model for learning recommendations."""

    target_skills: List[str] = Field(..., description="Skills that recommendations are for")
    recommendations: Dict[str, List[Dict[str, Any]]] = Field(..., description="Recommendations grouped by skill")
    total_recommendations: int = Field(..., description="Total number of recommendations")
    total_cost: float = Field(..., description="Total cost of all recommendations")
    total_duration_hours: float = Field(..., description="Total duration in hours")
    alternative_free_resources: int = Field(..., description="Number of free alternatives")
    skills_with_certifications: List[str] = Field(..., description="Skills offering certifications")
    priority_ordering: List[str] = Field(..., description="Recommended order to address skills")
    summary: str = Field(..., description="Summary of recommendations")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "target_skills": ["Python", "Docker"],
            "recommendations": {
                "Python": [
                    {
                        "id": "resource-1",
                        "title": "Python for Data Science",
                        "description": "Comprehensive Python course",
                        "resource_type": "course",
                        "url": "https://example.com/course",
                        "cost": 29.99,
                        "rating": 4.7,
                        "duration_hours": 40,
                        "skill_level": "intermediate",
                        "skills_taught": ["Python", "Pandas", "NumPy"]
                    }
                ],
                "Docker": [
                    {
                        "id": "resource-2",
                        "title": "Docker Essentials",
                        "description": "Learn Docker from scratch",
                        "resource_type": "course",
                        "url": "https://example.com/docker",
                        "cost": 0,
                        "rating": 4.5,
                        "duration_hours": 10,
                        "skill_level": "beginner",
                        "skills_taught": ["Docker", "Containers"]
                    }
                ]
            },
            "total_recommendations": 2,
            "total_cost": 29.99,
            "total_duration_hours": 50.0,
            "alternative_free_resources": 1,
            "skills_with_certifications": ["Python"],
            "priority_ordering": ["Docker", "Python"],
            "summary": "Found 2 recommendations for 2 skills. Total cost: $29.99, Total time: 50 hours"
        }
    })


# Skill Development Plan Models
class DevelopmentPlanCreate(BaseModel):
    """Request model for creating a skill development plan."""

    resume_id: str = Field(..., description="Resume ID")
    vacancy_id: Optional[str] = Field(None, description="Vacancy ID (optional)")
    skill_gap_report_id: Optional[str] = Field(None, description="Skill gap report ID (optional)")
    title: str = Field(..., description="Plan title")
    description: Optional[str] = Field(None, description="Plan description")
    status: str = Field("draft", description="Plan status (draft, active, completed, paused, abandoned)")
    priority: str = Field("medium", description="Priority level (low, medium, high, urgent)")
    difficulty_level: Optional[str] = Field(None, description="Difficulty level (beginner, intermediate, advanced, expert)")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    target_completion_date: Optional[str] = Field(None, description="Target completion date (ISO format)")
    learning_goals: Optional[List[str]] = Field(None, description="Learning goals")
    milestones: Optional[List[Dict[str, Any]]] = Field(None, description="Milestones with completion status")
    recommended_resources: Optional[List[Dict[str, Any]]] = Field(None, description="Recommended learning resources")
    is_public: bool = Field(False, description="Whether plan is publicly shareable")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "resume_id": "abc123-def456-ghi789",
            "vacancy_id": "vacancy-123",
            "skill_gap_report_id": "report-uuid-12345",
            "title": "Learn TypeScript and Docker",
            "description": "Bridge skill gaps for Senior React Developer position",
            "status": "active",
            "priority": "high",
            "difficulty_level": "intermediate",
            "start_date": "2024-01-15T00:00:00Z",
            "target_completion_date": "2024-04-15T00:00:00Z",
            "learning_goals": [
                "Master TypeScript fundamentals",
                "Learn Docker containerization",
                "Build 3 projects using TypeScript"
            ],
            "milestones": [
                {"title": "Complete TypeScript course", "target_date": "2024-02-15", "completed": False},
                {"title": "Deploy first Docker container", "target_date": "2024-03-01", "completed": False}
            ],
            "recommended_resources": [
                {"resource_id": "res-1", "title": "TypeScript Course", "priority": "high"}
            ],
            "is_public": False,
            "tags": ["frontend", "backend", "devops"]
        }
    })


class DevelopmentPlanUpdate(BaseModel):
    """Request model for updating a skill development plan."""

    title: Optional[str] = Field(None, description="Plan title")
    description: Optional[str] = Field(None, description="Plan description")
    status: Optional[str] = Field(None, description="Plan status (draft, active, completed, paused, abandoned)")
    overall_progress: Optional[float] = Field(None, description="Overall completion percentage (0-100)")
    priority: Optional[str] = Field(None, description="Priority level (low, medium, high, urgent)")
    difficulty_level: Optional[str] = Field(None, description="Difficulty level")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    target_completion_date: Optional[str] = Field(None, description="Target completion date (ISO format)")
    actual_completion_date: Optional[str] = Field(None, description="Actual completion date (ISO format)")
    learning_goals: Optional[List[str]] = Field(None, description="Learning goals")
    milestones: Optional[List[Dict[str, Any]]] = Field(None, description="Milestones with completion status")
    recommended_resources: Optional[List[Dict[str, Any]]] = Field(None, description="Recommended learning resources")
    completed_resources: Optional[List[Dict[str, Any]]] = Field(None, description="Completed resources with dates")
    hours_invested: Optional[float] = Field(None, description="Total hours invested")
    estimated_hours_remaining: Optional[float] = Field(None, description="Estimated hours remaining")
    is_public: Optional[bool] = Field(None, description="Whether plan is publicly shareable")
    reminder_frequency: Optional[str] = Field(None, description="Reminder frequency (daily, weekly, monthly, none)")
    notes: Optional[str] = Field(None, description="Candidate notes")
    reapplication_status: Optional[str] = Field(None, description="Reapplication status")
    reapplication_date: Optional[str] = Field(None, description="Reapplication date (ISO format)")
    outcome_notes: Optional[str] = Field(None, description="Outcome notes")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")


class DevelopmentPlanProgressUpdate(BaseModel):
    """Request model for updating plan progress."""

    completed_resources: Optional[List[Dict[str, Any]]] = Field(None, description="Completed resources with completion dates")
    overall_progress: Optional[float] = Field(None, description="Overall completion percentage (0-100)")
    hours_invested: Optional[float] = Field(None, description="Additional hours invested in this session")
    milestone_updates: Optional[List[Dict[str, Any]]] = Field(None, description="Milestone completion updates")
    notes: Optional[str] = Field(None, description="Progress notes")


class DevelopmentPlanResponse(BaseModel):
    """Response model for a skill development plan."""

    id: str = Field(..., description="Plan ID")
    resume_id: str = Field(..., description="Resume ID")
    vacancy_id: Optional[str] = Field(None, description="Vacancy ID")
    skill_gap_report_id: Optional[str] = Field(None, description="Skill gap report ID")

    # Plan details
    title: str = Field(..., description="Plan title")
    description: Optional[str] = Field(None, description="Plan description")
    status: str = Field(..., description="Plan status")
    overall_progress: float = Field(..., description="Overall completion percentage")

    # Timeline
    start_date: Optional[str] = Field(None, description="Start date")
    target_completion_date: Optional[str] = Field(None, description="Target completion date")
    actual_completion_date: Optional[str] = Field(None, description="Actual completion date")

    # Plan content
    learning_goals: Optional[List[str]] = Field(None, description="Learning goals")
    milestones: Optional[List[Dict[str, Any]]] = Field(None, description="Milestones")
    recommended_resources: Optional[List[Dict[str, Any]]] = Field(None, description="Recommended resources")
    completed_resources: Optional[List[Dict[str, Any]]] = Field(None, description="Completed resources")

    # Progress tracking
    total_resources_count: int = Field(..., description="Total resources count")
    completed_resources_count: int = Field(..., description="Completed resources count")
    hours_invested: float = Field(..., description="Hours invested")
    estimated_hours_remaining: Optional[float] = Field(None, description="Estimated hours remaining")

    # Sharing and access
    shareable_token: Optional[str] = Field(None, description="Shareable token")
    is_public: bool = Field(..., description="Whether plan is public")
    shared_with_recruiters: Optional[List[str]] = Field(None, description="Shared with recruiters")
    access_expires_at: Optional[str] = Field(None, description="Access expiration")

    # Engagement tracking
    last_accessed_at: Optional[str] = Field(None, description="Last accessed timestamp")
    reminder_scheduled_at: Optional[str] = Field(None, description="Reminder scheduled timestamp")
    reminder_frequency: str = Field(..., description="Reminder frequency")
    notes: Optional[str] = Field(None, description="Candidate notes")

    # Outcome tracking
    reapplication_status: str = Field(..., description="Reapplication status")
    reapplication_date: Optional[str] = Field(None, description="Reapplication date")
    outcome_notes: Optional[str] = Field(None, description="Outcome notes")

    # Additional metadata
    priority: str = Field(..., description="Priority level")
    difficulty_level: Optional[str] = Field(None, description="Difficulty level")
    tags: Optional[List[str]] = Field(None, description="Tags")

    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "plan-uuid-12345",
            "resume_id": "abc123-def456-ghi789",
            "vacancy_id": "vacancy-123",
            "skill_gap_report_id": "report-uuid-12345",
            "title": "Learn TypeScript and Docker",
            "description": "Bridge skill gaps for Senior React Developer position",
            "status": "active",
            "overall_progress": 35.0,
            "start_date": "2024-01-15T00:00:00Z",
            "target_completion_date": "2024-04-15T00:00:00Z",
            "actual_completion_date": None,
            "learning_goals": [
                "Master TypeScript fundamentals",
                "Learn Docker containerization",
                "Build 3 projects using TypeScript"
            ],
            "milestones": [
                {
                    "title": "Complete TypeScript course",
                    "target_date": "2024-02-15",
                    "completed": False,
                    "completion_date": None
                },
                {
                    "title": "Deploy first Docker container",
                    "target_date": "2024-03-01",
                    "completed": False,
                    "completion_date": None
                }
            ],
            "recommended_resources": [
                {"resource_id": "res-1", "title": "TypeScript Course", "priority": "high"}
            ],
            "completed_resources": [],
            "total_resources_count": 5,
            "completed_resources_count": 2,
            "hours_invested": 20.5,
            "estimated_hours_remaining": 59.5,
            "shareable_token": None,
            "is_public": False,
            "shared_with_recruiters": [],
            "access_expires_at": None,
            "last_accessed_at": "2024-01-20T10:30:00Z",
            "reminder_scheduled_at": "2024-01-22T09:00:00Z",
            "reminder_frequency": "weekly",
            "notes": "Making good progress on TypeScript fundamentals",
            "reapplication_status": "not_ready",
            "reapplication_date": None,
            "outcome_notes": None,
            "priority": "high",
            "difficulty_level": "intermediate",
            "tags": ["frontend", "backend", "devops"],
            "created_at": "2024-01-15T08:00:00Z",
            "updated_at": "2024-01-20T10:30:00Z"
        }
    })


class DevelopmentPlanListResponse(BaseModel):
    """Response model for listing development plans."""

    plans: List[DevelopmentPlanResponse] = Field(..., description="List of development plans")
    total: int = Field(..., description="Total number of plans")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of plans per page")


@router.post(
    "/analyze",
    response_model=SkillGapAnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["Skill Gap Analysis"],
)
async def analyze_skill_gaps(
    http_request: Request, request: SkillGapAnalysisRequest, db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Analyze skill gaps between a candidate's resume and job requirements.

    This endpoint performs comprehensive skill gap analysis by:
    1. Extracting skills from the candidate's resume
    2. Comparing against job vacancy requirements
    3. Identifying missing skills and partial matches
    4. Calculating gap severity and bridgeability
    5. Estimating time required to bridge gaps
    6. Providing priority ordering for addressing gaps

    The analysis is saved to the database for future reference.

    Args:
        http_request: FastAPI request object (for Accept-Language header)
        request: Analysis request with resume_id and vacancy_data
        db: Database session

    Returns:
        JSON response with comprehensive skill gap analysis

    Raises:
        HTTPException(404): If resume file is not found
        HTTPException(422): If text extraction fails
        HTTPException(500): If analysis processing fails

    Examples:
        >>> import requests
        >>> vacancy = {
        ...     "id": "vacancy-123",
        ...     "title": "Senior React Developer",
        ...     "description": "Looking for experienced React developer",
        ...     "required_skills": ["React", "TypeScript", "JavaScript", "AWS", "Docker"],
        ...     "required_skill_levels": {
        ...         "React": "advanced",
        ...         "TypeScript": "intermediate",
        ...         "JavaScript": "advanced",
        ...         "AWS": "beginner",
        ...         "Docker": "intermediate"
        ...     }
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/skill-gap/analyze",
        ...     json={"resume_id": "abc123", "vacancy_data": vacancy}
        ... )
        >>> response.json()
        {
            "report_id": "report-uuid",
            "resume_id": "abc123",
            "vacancy_id": "vacancy-123",
            "vacancy_title": "Senior React Developer",
            "candidate_skills": ["JavaScript", "React", "HTML", "CSS"],
            "required_skills": ["React", "TypeScript", "JavaScript", "AWS", "Docker"],
            "matched_skills": ["React", "JavaScript"],
            "missing_skills": ["TypeScript", "AWS", "Docker"],
            "partial_match_skills": [],
            "missing_skill_details": {
                "TypeScript": {"status": "missing", "required_level": "intermediate", "category": "programming_language"},
                "AWS": {"status": "missing", "required_level": "beginner", "category": "cloud_devops"},
                "Docker": {"status": "missing", "required_level": "intermediate", "category": "cloud_devops"}
            },
            "gap_severity": "moderate",
            "gap_percentage": 60.0,
            "bridgeability_score": 0.65,
            "estimated_time_to_bridge": 80,
            "priority_ordering": ["TypeScript", "Docker", "AWS"],
            "processing_time_ms": 150.5
        }
    """
    import time

    locale = _extract_locale(http_request)
    start_time = time.time()

    try:
        logger.info(f"Starting skill gap analysis for resume_id: {request.resume_id}")

        # Step 1: Find the resume file
        resume_path = None
        for ext in [".pdf", ".docx", ".PDF", ".DOCX"]:
            file_path = UPLOAD_DIR / f"{request.resume_id}{ext}"
            if file_path.exists():
                resume_path = file_path
                break

        # If file not found, try to get text from database
        resume_text = None
        if resume_path:
            # Extract text from file
            try:
                from services.data_extractor.extract import extract_text_from_pdf, extract_text_from_docx

                file_ext = resume_path.suffix.lower()
                if file_ext == ".pdf":
                    result = extract_text_from_pdf(resume_path)
                elif file_ext == ".docx":
                    result = extract_text_from_docx(resume_path)
                else:
                    error_msg = get_error_message("invalid_file_type", locale, file_ext=file_ext, allowed=".pdf, .docx")
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail=error_msg,
                    )

                if result.get("error"):
                    error_msg = get_error_message("extraction_failed", locale)
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=error_msg,
                    )

                resume_text = result.get("text", "")
                if not resume_text or len(resume_text.strip()) < 10:
                    error_msg = get_error_message("file_corrupted", locale)
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=error_msg,
                    )

                logger.info(f"Extracted {len(resume_text)} characters from resume")

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error extracting text: {e}", exc_info=True)
                error_msg = get_error_message("extraction_failed", locale)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg,
                ) from e
        else:
            # Try to get text from database
            try:
                from models.resume import Resume as ResumeModel
                from models.resume_analysis import ResumeAnalysis

                resume_uuid = UUID(request.resume_id)
                resume_query = select(ResumeModel).where(ResumeModel.id == resume_uuid)
                resume_result = await db.execute(resume_query)
                resume_record = resume_result.scalar_one_or_none()

                if resume_record and resume_record.raw_text:
                    resume_text = resume_record.raw_text
                    logger.info(f"Using raw_text from database for resume {request.resume_id}")
                elif resume_record:
                    # Try to get from ResumeAnalysis
                    analysis_query = select(ResumeAnalysis).where(
                        ResumeAnalysis.resume_id == resume_uuid
                    )
                    analysis_result = await db.execute(analysis_query)
                    analysis_record = analysis_result.scalar_one_or_none()

                    if analysis_record and analysis_record.raw_text:
                        resume_text = analysis_record.raw_text
                        logger.info(f"Using raw_text from ResumeAnalysis for resume {request.resume_id}")
                    else:
                        logger.warning(f"No text found for resume {request.resume_id}")
                else:
                    logger.warning(f"Resume {request.resume_id} not found in database")

            except Exception as e:
                logger.error(f"Error getting resume from database: {e}")

        if not resume_text or len(resume_text.strip()) < 10:
            error_msg = get_error_message("file_not_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Step 2: Detect language
        try:
            from langdetect import detect, LangDetectException

            try:
                detected_lang = detect(resume_text)
                language = "ru" if detected_lang == "ru" else "en"
            except LangDetectException:
                language = "en"
        except ImportError:
            language = "en"

        logger.info(f"Detected language: {language}")

        # Step 3: Extract skills from resume
        logger.info("Extracting skills from resume...")
        keywords_result = extract_resume_keywords(
            resume_text, language=language
        )
        entities_result = extract_resume_entities(resume_text, language=language)

        # Extract keyword names from HF format (tuples) if present
        # HF extractor returns tuples like ('Docker', 0.93) - extract just the names
        keywords = keywords_result.get("keywords") or []
        keyphrases = keywords_result.get("keyphrases") or []

        # Convert tuples to plain strings if needed
        def extract_names(items):
            """Extract just the names from keyword tuples if present."""
            result = []
            for item in items:
                if isinstance(item, (list, tuple)) and len(item) >= 1:
                    result.append(item[0])  # First element is the keyword name
                else:
                    result.append(item)
            return result

        keyword_names = extract_names(keywords)
        keyphrase_names = extract_names(keyphrases)

        # Combine keywords and technical skills
        candidate_skills = list(set(
            keyword_names +
            keyphrase_names +
            (entities_result.get("technical_skills") or [])
        ))

        logger.info(f"Extracted {len(candidate_skills)} unique skills from resume")

        # Step 4: Get vacancy data
        vacancy_title = request.vacancy_data.get(
            "title", request.vacancy_data.get("position", "Unknown Position")
        )
        vacancy_description = request.vacancy_data.get("description", "")
        vacancy_id = request.vacancy_data.get("id")
        required_skills = request.vacancy_data.get("required_skills", [])
        required_skill_levels = request.vacancy_data.get("required_skill_levels", {})

        if isinstance(required_skills, str):
            required_skills = [required_skills]

        # Step 5: Perform skill gap analysis
        logger.info("Analyzing skill gaps...")
        analyzer = get_skill_gap_analyzer()

        gap_result = analyzer.analyze_resume_to_vacancy(
            resume_text=resume_text,
            candidate_skills=candidate_skills,
            vacancy_title=vacancy_title,
            vacancy_description=vacancy_description,
            vacancy_skills=required_skills,
            vacancy_skill_levels=required_skill_levels,
        )

        # Step 6: Save or update report in database
        try:
            resume_uuid = UUID(request.resume_id)
            vacancy_uuid = UUID(vacancy_id) if vacancy_id else None

            # Check if report already exists
            existing_report = None
            if vacancy_uuid:
                existing_query = select(SkillGapReport).where(
                    SkillGapReport.resume_id == resume_uuid,
                    SkillGapReport.vacancy_id == vacancy_uuid
                )
                existing_result = await db.execute(existing_query)
                existing_report = existing_result.scalar_one_or_none()

            if existing_report:
                # Update existing report
                existing_report.candidate_skills = gap_result.candidate_skills
                existing_report.candidate_skill_levels = {}
                existing_report.required_skills = gap_result.required_skills
                existing_report.required_skill_levels = required_skill_levels
                existing_report.matched_skills = gap_result.matched_skills
                existing_report.missing_skills = gap_result.missing_skills
                existing_report.partial_match_skills = gap_result.partial_match_skills
                existing_report.missing_skill_details = gap_result.missing_skill_details
                existing_report.gap_severity = gap_result.gap_severity
                existing_report.gap_percentage = gap_result.gap_percentage
                existing_report.bridgeability_score = gap_result.bridgeability_score
                existing_report.estimated_time_to_bridge = gap_result.estimated_time_to_bridge
                existing_report.priority_ordering = gap_result.priority_ordering
                existing_report.recommended_resources_count = 0  # Will be updated by recommendation engine

                report_id = existing_report.id
                logger.info(f"Updated existing skill gap report: {report_id}")
            else:
                # Create new report (only if we have a vacancy_id)
                if vacancy_uuid:
                    new_report = SkillGapReport(
                        resume_id=resume_uuid,
                        vacancy_id=vacancy_uuid,
                        candidate_skills=gap_result.candidate_skills,
                        candidate_skill_levels={},
                        required_skills=gap_result.required_skills,
                        required_skill_levels=required_skill_levels,
                        matched_skills=gap_result.matched_skills,
                        missing_skills=gap_result.missing_skills,
                        partial_match_skills=gap_result.partial_match_skills,
                        missing_skill_details=gap_result.missing_skill_details,
                        gap_severity=gap_result.gap_severity,
                        gap_percentage=gap_result.gap_percentage,
                        bridgeability_score=gap_result.bridgeability_score,
                        estimated_time_to_bridge=gap_result.estimated_time_to_bridge,
                        priority_ordering=gap_result.priority_ordering,
                        recommended_resources_count=0,
                    )
                    db.add(new_report)
                    await db.flush()
                    report_id = new_report.id
                    logger.info(f"Created new skill gap report: {report_id}")
                else:
                    report_id = None

            await db.commit()

        except ValueError as e:
            logger.warning(f"Invalid UUID format, skipping database save: {e}")
            report_id = None
        except Exception as e:
            logger.error(f"Failed to save skill gap report to database: {e}")
            await db.rollback()
            report_id = None

        processing_time_ms = (time.time() - start_time) * 1000

        # Build response
        response_data = {
            "report_id": str(report_id) if report_id else "not-saved",
            "resume_id": request.resume_id,
            "vacancy_id": vacancy_id,
            "vacancy_title": vacancy_title,
            "candidate_skills": gap_result.candidate_skills,
            "required_skills": gap_result.required_skills,
            "matched_skills": gap_result.matched_skills,
            "missing_skills": gap_result.missing_skills,
            "partial_match_skills": gap_result.partial_match_skills,
            "missing_skill_details": gap_result.missing_skill_details,
            "gap_severity": gap_result.gap_severity,
            "gap_percentage": round(gap_result.gap_percentage, 2),
            "bridgeability_score": round(gap_result.bridgeability_score, 4),
            "estimated_time_to_bridge": gap_result.estimated_time_to_bridge,
            "priority_ordering": gap_result.priority_ordering,
            "processing_time_ms": round(processing_time_ms, 2),
        }

        logger.info(
            f"Skill gap analysis completed for resume_id {request.resume_id} "
            f"with gap_severity={gap_result.gap_severity}, "
            f"gap_percentage={gap_result.gap_percentage:.2f}%"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing skill gaps: {e}", exc_info=True)
        error_msg = get_error_message("parsing_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.get(
    "/",
    response_model=SkillGapReportListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Skill Gap Analysis"],
)
async def list_skill_gap_reports(
    resume_id: Optional[str] = None,
    vacancy_id: Optional[str] = None,
    gap_severity: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List skill gap reports with optional filtering.

    Supports filtering by resume_id, vacancy_id, and gap_severity.
    Results are paginated.

    Args:
        resume_id: Optional filter by resume ID
        vacancy_id: Optional filter by vacancy ID
        gap_severity: Optional filter by gap severity (critical, moderate, minimal, none)
        page: Page number (1-indexed)
        page_size: Number of reports per page
        db: Database session

    Returns:
        JSON response with list of skill gap reports

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/skill-gap/")
        >>> response.json()
        {
            "reports": [...],
            "total": 42,
            "page": 1,
            "page_size": 20
        }
    """
    try:
        logger.info(
            f"Listing skill gap reports: resume_id={resume_id}, "
            f"vacancy_id={vacancy_id}, gap_severity={gap_severity}"
        )

        # Build query
        query = select(SkillGapReport)

        # Apply filters
        if resume_id:
            try:
                resume_uuid = UUID(resume_id)
                query = query.where(SkillGapReport.resume_id == resume_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid resume_id format: {resume_id}",
                )

        if vacancy_id:
            try:
                vacancy_uuid = UUID(vacancy_id)
                query = query.where(SkillGapReport.vacancy_id == vacancy_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid vacancy_id format: {vacancy_id}",
                )

        if gap_severity:
            if gap_severity not in ["critical", "moderate", "minimal", "none"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid gap_severity: {gap_severity}. Must be one of: critical, moderate, minimal, none",
                )
            query = query.where(SkillGapReport.gap_severity == gap_severity)

        # Order by most recent first
        query = query.order_by(SkillGapReport.created_at.desc())

        # Get total count
        from sqlalchemy import func

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(query)
        reports = result.scalars().all()

        # Convert to response format
        report_responses = []
        for report in reports:
            report_responses.append({
                "id": str(report.id),
                "resume_id": str(report.resume_id),
                "vacancy_id": str(report.vacancy_id),
                "candidate_skills": report.candidate_skills or [],
                "required_skills": report.required_skills or [],
                "matched_skills": report.matched_skills or [],
                "missing_skills": report.missing_skills or [],
                "partial_match_skills": report.partial_match_skills or [],
                "gap_severity": report.gap_severity or "unknown",
                "gap_percentage": float(report.gap_percentage) if report.gap_percentage else 0.0,
                "bridgeability_score": float(report.bridgeability_score) if report.bridgeability_score else 0.0,
                "estimated_time_to_bridge": report.estimated_time_to_bridge or 0,
                "priority_ordering": report.priority_ordering or [],
                "created_at": report.created_at.isoformat() if report.created_at else "",
                "updated_at": report.updated_at.isoformat() if report.updated_at else "",
            })

        response_data = {
            "reports": report_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

        logger.info(f"Returning {len(report_responses)} skill gap reports (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing skill gap reports: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skill gap reports: {str(e)}",
        ) from e


@router.get(
    "/{report_id}",
    response_model=SkillGapReportResponse,
    status_code=status.HTTP_200_OK,
    tags=["Skill Gap Analysis"],
)
async def get_skill_gap_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific skill gap report by ID.

    Args:
        report_id: UUID of the skill gap report
        db: Database session

    Returns:
        JSON response with skill gap report details

    Raises:
        HTTPException(404): If report is not found

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/skill-gap/abc-123-def")
        >>> response.json()
        {
            "id": "abc-123-def",
            "resume_id": "resume-uuid",
            "vacancy_id": "vacancy-uuid",
            "candidate_skills": ["Python", "Django"],
            "required_skills": ["Python", "Django", "React"],
            "matched_skills": ["Python", "Django"],
            "missing_skills": ["React"],
            "partial_match_skills": [],
            "gap_severity": "minimal",
            "gap_percentage": 33.33,
            "bridgeability_score": 0.85,
            "estimated_time_to_bridge": 20,
            "priority_ordering": ["React"],
            "created_at": "2024-01-31T00:00:00Z",
            "updated_at": "2024-01-31T00:00:00Z"
        }
    """
    try:
        logger.info(f"Fetching skill gap report: {report_id}")

        # Validate report_id format
        try:
            report_uuid = UUID(report_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report_id format: {report_id}",
            )

        # Query database
        query = select(SkillGapReport).where(SkillGapReport.id == report_uuid)
        result = await db.execute(query)
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill gap report not found: {report_id}",
            )

        # Build response
        response_data = {
            "id": str(report.id),
            "resume_id": str(report.resume_id),
            "vacancy_id": str(report.vacancy_id),
            "candidate_skills": report.candidate_skills or [],
            "required_skills": report.required_skills or [],
            "matched_skills": report.matched_skills or [],
            "missing_skills": report.missing_skills or [],
            "partial_match_skills": report.partial_match_skills or [],
            "gap_severity": report.gap_severity or "unknown",
            "gap_percentage": float(report.gap_percentage) if report.gap_percentage else 0.0,
            "bridgeability_score": float(report.bridgeability_score) if report.bridgeability_score else 0.0,
            "estimated_time_to_bridge": report.estimated_time_to_bridge or 0,
            "priority_ordering": report.priority_ordering or [],
            "created_at": report.created_at.isoformat() if report.created_at else "",
            "updated_at": report.updated_at.isoformat() if report.updated_at else "",
        }

        logger.info(f"Returning skill gap report: {report_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching skill gap report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch skill gap report: {str(e)}",
        ) from e


# Learning Resource Endpoints

@router.get(
    "/learning-resources/",
    response_model=LearningResourceListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Learning Resources"],
)
async def list_learning_resources(
    skill: Optional[str] = Query(None, description="Filter by skill taught"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    source_platform: Optional[str] = Query(None, description="Filter by source platform"),
    skill_level: Optional[str] = Query(None, description="Filter by skill level"),
    access_type: Optional[str] = Query(None, description="Filter by access type (free, paid, etc.)"),
    min_rating: Optional[float] = Query(None, description="Minimum rating"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    max_cost: Optional[float] = Query(None, description="Maximum cost"),
    language: Optional[str] = Query(None, description="Filter by language"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List learning resources with optional filtering.

    Supports filtering by:
    - skill: Resources that teach a specific skill
    - resource_type: Type of resource (course, certification, tutorial, etc.)
    - source_platform: Platform offering the resource (Coursera, Udemy, etc.)
    - skill_level: Difficulty level (beginner, intermediate, advanced, expert)
    - access_type: Access type (free, paid, freemium, subscription)
    - min_rating: Minimum rating threshold
    - is_verified: Whether the resource is verified
    - max_cost: Maximum cost amount
    - language: Resource language

    Results are paginated.

    Args:
        skill: Optional skill filter
        resource_type: Optional resource type filter
        source_platform: Optional platform filter
        skill_level: Optional skill level filter
        access_type: Optional access type filter
        min_rating: Optional minimum rating filter
        is_verified: Optional verification filter
        max_cost: Optional maximum cost filter
        language: Optional language filter
        page: Page number (1-indexed)
        page_size: Number of resources per page
        db: Database session

    Returns:
        JSON response with list of learning resources

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/learning-resources/?skill=Python")
        >>> response.json()
        {
            "resources": [...],
            "total": 15,
            "filters_applied": {"skill": "Python"}
        }
    """
    try:
        logger.info(
            f"Listing learning resources: skill={skill}, resource_type={resource_type}, "
            f"source_platform={source_platform}, skill_level={skill_level}, access_type={access_type}"
        )

        # Build query
        query = select(LearningResource).where(LearningResource.is_active == True)

        # Apply filters
        if skill:
            # Filter by skill in skills_taught array
            query = query.where(LearningResource.skills_taught.contains([skill]))

        if resource_type:
            query = query.where(LearningResource.resource_type == resource_type)

        if source_platform:
            query = query.where(LearningResource.source_platform == source_platform)

        if skill_level:
            query = query.where(LearningResource.skill_level == skill_level)

        if access_type:
            query = query.where(LearningResource.access_type == access_type)

        if min_rating is not None:
            query = query.where(LearningResource.rating >= min_rating)

        if is_verified is not None:
            query = query.where(LearningResource.is_verified == is_verified)

        if max_cost is not None:
            query = query.where(
                (LearningResource.cost_amount <= max_cost) |
                (LearningResource.cost_amount == None)
            )

        if language:
            query = query.where(LearningResource.language == language)

        # Get total count
        from sqlalchemy import func

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Order by recommendation count and rating
        query = query.order_by(
            LearningResource.recommendation_count.desc(),
            LearningResource.rating.desc()
        )

        # Execute query
        result = await db.execute(query)
        resources = result.scalars().all()

        # Convert to response format
        resource_responses = []
        for resource in resources:
            resource_responses.append({
                "id": str(resource.id),
                "title": resource.title,
                "description": resource.description,
                "resource_type": resource.resource_type,
                "source_platform": resource.source_platform,
                "skills_taught": resource.skills_taught or [],
                "skill_level": resource.skill_level,
                "topics_covered": resource.topics_covered or [],
                "prerequisites": resource.prerequisites or [],
                "url": resource.url,
                "access_type": resource.access_type,
                "cost_amount": float(resource.cost_amount) if resource.cost_amount else None,
                "currency": resource.currency,
                "duration_hours": float(resource.duration_hours) if resource.duration_hours else None,
                "duration_weeks": float(resource.duration_weeks) if resource.duration_weeks else None,
                "is_self_paced": resource.is_self_paced,
                "rating": float(resource.rating) if resource.rating else None,
                "rating_count": resource.rating_count,
                "popularity_score": float(resource.popularity_score) if resource.popularity_score else None,
                "quality_score": float(resource.quality_score) if resource.quality_score else None,
                "provider_name": resource.provider_name,
                "instructor_name": resource.instructor_name,
                "certificate_offered": resource.certificate_offered,
                "certificate_url": resource.certificate_url,
                "language": resource.language,
                "is_active": resource.is_active,
                "is_verified": resource.is_verified,
                "recommendation_count": resource.recommendation_count,
                "created_at": resource.created_at.isoformat() if resource.created_at else "",
                "updated_at": resource.updated_at.isoformat() if resource.updated_at else "",
            })

        # Build filters applied dict
        filters_applied = {}
        if skill:
            filters_applied["skill"] = skill
        if resource_type:
            filters_applied["resource_type"] = resource_type
        if source_platform:
            filters_applied["source_platform"] = source_platform
        if skill_level:
            filters_applied["skill_level"] = skill_level
        if access_type:
            filters_applied["access_type"] = access_type
        if min_rating is not None:
            filters_applied["min_rating"] = min_rating
        if is_verified is not None:
            filters_applied["is_verified"] = is_verified
        if max_cost is not None:
            filters_applied["max_cost"] = max_cost
        if language:
            filters_applied["language"] = language

        response_data = {
            "resources": resource_responses,
            "total": total,
            "filters_applied": filters_applied,
        }

        logger.info(f"Returning {len(resource_responses)} learning resources (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing learning resources: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list learning resources: {str(e)}",
        ) from e


@router.get(
    "/learning-resources/{resource_id}",
    response_model=LearningResourceResponse,
    status_code=status.HTTP_200_OK,
    tags=["Learning Resources"],
)
async def get_learning_resource(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific learning resource by ID.

    Args:
        resource_id: UUID of the learning resource
        db: Database session

    Returns:
        JSON response with learning resource details

    Raises:
        HTTPException(404): If resource is not found

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/learning-resources/abc-123-def")
        >>> response.json()
        {
            "id": "abc-123-def",
            "title": "Python for Data Science",
            "resource_type": "course",
            ...
        }
    """
    try:
        logger.info(f"Fetching learning resource: {resource_id}")

        # Validate resource_id format
        try:
            resource_uuid = UUID(resource_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resource_id format: {resource_id}",
            )

        # Query database
        query = select(LearningResource).where(LearningResource.id == resource_uuid)
        result = await db.execute(query)
        resource = result.scalar_one_or_none()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning resource not found: {resource_id}",
            )

        # Build response
        response_data = {
            "id": str(resource.id),
            "title": resource.title,
            "description": resource.description,
            "resource_type": resource.resource_type,
            "source_platform": resource.source_platform,
            "skills_taught": resource.skills_taught or [],
            "skill_level": resource.skill_level,
            "topics_covered": resource.topics_covered or [],
            "prerequisites": resource.prerequisites or [],
            "url": resource.url,
            "access_type": resource.access_type,
            "cost_amount": float(resource.cost_amount) if resource.cost_amount else None,
            "currency": resource.currency,
            "duration_hours": float(resource.duration_hours) if resource.duration_hours else None,
            "duration_weeks": float(resource.duration_weeks) if resource.duration_weeks else None,
            "is_self_paced": resource.is_self_paced,
            "rating": float(resource.rating) if resource.rating else None,
            "rating_count": resource.rating_count,
            "popularity_score": float(resource.popularity_score) if resource.popularity_score else None,
            "quality_score": float(resource.quality_score) if resource.quality_score else None,
            "provider_name": resource.provider_name,
            "instructor_name": resource.instructor_name,
            "certificate_offered": resource.certificate_offered,
            "certificate_url": resource.certificate_url,
            "language": resource.language,
            "is_active": resource.is_active,
            "is_verified": resource.is_verified,
            "recommendation_count": resource.recommendation_count,
            "created_at": resource.created_at.isoformat() if resource.created_at else "",
            "updated_at": resource.updated_at.isoformat() if resource.updated_at else "",
        }

        logger.info(f"Returning learning resource: {resource_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching learning resource: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch learning resource: {str(e)}",
        ) from e


@router.post(
    "/learning-resources/recommendations",
    response_model=LearningRecommendationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Learning Resources"],
)
async def get_learning_recommendations(
    request: LearningRecommendationRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get personalized learning recommendations for specified skills.

    This endpoint uses the LearningRecommendationEngine to find and rank
    relevant learning resources for the specified skills. The recommendations
    are based on:
    - Relevance to the target skills
    - Quality (ratings, reviews, provider reputation)
    - Accessibility (cost, time, prerequisites)
    - Learning outcomes (certifications, practical projects)

    Args:
        request: Recommendation request with skills and preferences
        db: Database session

    Returns:
        JSON response with personalized learning recommendations

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/learning-resources/recommendations",
        ...     json={
        ...         "skills": ["Python", "Docker"],
        ...         "max_cost_per_resource": 50,
        ...         "include_free_resources": True
        ...     }
        ... )
        >>> response.json()
        {
            "target_skills": ["Python", "Docker"],
            "recommendations": {
                "Python": [...],
                "Docker": [...]
            },
            "total_recommendations": 10,
            "summary": "Found 10 recommendations..."
        }
    """
    try:
        logger.info(f"Getting learning recommendations for skills: {request.skills}")

        # Validate inputs
        if not request.skills or len(request.skills) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one skill must be provided",
            )

        # Validate skill levels
        skill_levels = request.skill_levels or {}
        valid_levels = ["beginner", "intermediate", "advanced", "expert"]
        for skill, level in skill_levels.items():
            if level not in valid_levels:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid skill level '{level}' for skill '{skill}'. Must be one of: {valid_levels}",
                )

        # Validate max_recommendations_per_skill
        if request.max_recommendations_per_skill < 1 or request.max_recommendations_per_skill > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="max_recommendations_per_skill must be between 1 and 20",
            )

        # Validate min_rating
        if request.min_rating < 0 or request.min_rating > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_rating must be between 0 and 5",
            )

        # Get recommendation engine
        engine = get_learning_recommendation_engine()

        # Build skill levels dict for all skills
        default_skill_levels = {skill: "intermediate" for skill in request.skills}
        if skill_levels:
            default_skill_levels.update(skill_levels)

        # Create minimal skill gap result for recommendation
        # Since we don't have candidate skills here, treat all skills as missing
        missing_skill_details = {}
        for skill in request.skills:
            level = default_skill_levels.get(skill, "intermediate")
            missing_skill_details[skill] = {
                "status": "missing",
                "required_level": level,
                "importance": "high",
            }

        skill_gap_result = SkillGapResult(
            candidate_skills=[],
            required_skills=request.skills,
            matched_skills=[],
            missing_skills=request.skills,
            partial_match_skills=[],
            missing_skill_details=missing_skill_details,
            gap_severity="moderate",
            gap_percentage=100.0,
            bridgeability_score=0.5,
            estimated_time_to_bridge=0,
            priority_ordering=request.skills,
            match_result=None,
        )

        # Get recommendations from engine
        recommendations_result = engine.recommend_for_skill_gaps(
            skill_gap_result=skill_gap_result,
            max_recommendations_per_skill=request.max_recommendations_per_skill,
            max_cost_per_resource=request.max_cost_per_resource,
            include_free_resources=request.include_free_resources,
            skill_level_requirements=default_skill_levels,
            priority_ordering=request.skills,
        )

        # Query database for matching resources to update recommendation counts
        try:
            for skill in request.skills:
                # Find resources that teach this skill
                resource_query = select(LearningResource).where(
                    LearningResource.skills_taught.contains([skill])
                )
                if request.min_rating > 0:
                    resource_query = resource_query.where(
                        LearningResource.rating >= request.min_rating
                    )
                if request.max_cost_per_resource is not None:
                    resource_query = resource_query.where(
                        (LearningResource.cost_amount <= request.max_cost_per_resource) |
                        (LearningResource.cost_amount == None)
                    )

                resources = await db.execute(resource_query)
                for resource in resources.scalars().all():
                    # Increment recommendation count
                    resource.recommendation_count += 1
                    if resource.last_recommended_at is None:
                        from datetime import datetime
                        resource.last_recommended_at = datetime.utcnow().isoformat()

            await db.commit()

        except Exception as e:
            logger.warning(f"Failed to update recommendation counts: {e}")
            await db.rollback()

        # Convert result to dict for JSON serialization
        response_data = recommendations_result.to_dict()

        logger.info(
            f"Returning {recommendations_result.total_recommendations} recommendations "
            f"for {len(request.skills)} skills"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get learning recommendations: {str(e)}",
        ) from e


# Skill Development Plan Endpoints

@router.post(
    "/development-plans/",
    response_model=DevelopmentPlanResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Development Plans"],
)
async def create_development_plan(
    request: DevelopmentPlanCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new skill development plan.

    This endpoint creates a personalized skill development plan for a candidate,
    based on a skill gap analysis. The plan includes learning goals, milestones,
    and recommended resources to help the candidate bridge their skill gaps.

    Args:
        request: Create request with plan details
        db: Database session

    Returns:
        JSON response with created development plan

    Raises:
        HTTPException(422): If validation fails
        HTTPException(404): If resume or vacancy not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_id": "abc-123-def",
        ...     "vacancy_id": "vac-456-ghi",
        ...     "title": "Full-Stack Developer Development Plan",
        ...     "description": "Bridge gaps in React and Docker skills",
        ...     "priority": "high",
        ...     "difficulty_level": "intermediate",
        ...     "learning_goals": [
        ...         "Master React hooks and state management",
        ...         "Learn Docker containerization"
        ...     ],
        ...     "recommended_resources": [
        ...         {"resource_id": "res-1", "skill": "React", "priority": 1},
        ...         {"resource_id": "res-2", "skill": "Docker", "priority": 2}
        ...     ]
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/development-plans/",
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "plan-uuid",
            "resume_id": "abc-123-def",
            "vacancy_id": "vac-456-ghi",
            "title": "Full-Stack Developer Development Plan",
            ...
        }
    """
    try:
        logger.info(f"Creating development plan '{request.title}' for resume_id: {request.resume_id}")

        # Validate resume_id
        try:
            resume_uuid = UUID(request.resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resume_id format: {request.resume_id}",
            )

        # Validate vacancy_id if provided
        vacancy_uuid = None
        if request.vacancy_id:
            try:
                vacancy_uuid = UUID(request.vacancy_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid vacancy_id format: {request.vacancy_id}",
                )

        # Validate skill_gap_report_id if provided
        skill_gap_report_uuid = None
        if request.skill_gap_report_id:
            try:
                skill_gap_report_uuid = UUID(request.skill_gap_report_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid skill_gap_report_id format: {request.skill_gap_report_id}",
                )

        # Validate status
        valid_statuses = ["draft", "active", "completed", "paused", "abandoned"]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status: {request.status}. Must be one of: {valid_statuses}",
            )

        # Validate priority
        valid_priorities = ["low", "medium", "high", "urgent"]
        if request.priority not in valid_priorities:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid priority: {request.priority}. Must be one of: {valid_priorities}",
            )

        # Generate shareable token if plan is public
        shareable_token = None
        if request.is_public:
            import secrets
            shareable_token = secrets.token_urlsafe(32)

        # Calculate initial counts
        total_resources = len(request.recommended_resources) if request.recommended_resources else 0
        completed_resources = 0

        # Create new development plan
        new_plan = SkillDevelopmentPlan(
            resume_id=resume_uuid,
            vacancy_id=vacancy_uuid,
            skill_gap_report_id=skill_gap_report_uuid,
            title=request.title,
            description=request.description,
            status=request.status,
            priority=request.priority,
            difficulty_level=request.difficulty_level,
            start_date=request.start_date,
            target_completion_date=request.target_completion_date,
            learning_goals=request.learning_goals,
            milestones=request.milestones,
            recommended_resources=request.recommended_resources,
            completed_resources=request.completed_resources,
            total_resources_count=total_resources,
            completed_resources_count=completed_resources,
            is_public=request.is_public,
            shareable_token=shareable_token,
            tags=request.tags,
        )

        db.add(new_plan)
        await db.flush()

        logger.info(f"Created development plan: {new_plan.id}")

        await db.commit()

        # Build response
        response_data = {
            "id": str(new_plan.id),
            "resume_id": str(new_plan.resume_id),
            "vacancy_id": str(new_plan.vacancy_id) if new_plan.vacancy_id else None,
            "skill_gap_report_id": str(new_plan.skill_gap_report_id) if new_plan.skill_gap_report_id else None,
            "title": new_plan.title,
            "description": new_plan.description,
            "status": new_plan.status,
            "overall_progress": float(new_plan.overall_progress) if new_plan.overall_progress else 0.0,
            "start_date": new_plan.start_date,
            "target_completion_date": new_plan.target_completion_date,
            "actual_completion_date": new_plan.actual_completion_date,
            "learning_goals": new_plan.learning_goals,
            "milestones": new_plan.milestones,
            "recommended_resources": new_plan.recommended_resources,
            "completed_resources": new_plan.completed_resources,
            "total_resources_count": new_plan.total_resources_count,
            "completed_resources_count": new_plan.completed_resources_count,
            "hours_invested": float(new_plan.hours_invested) if new_plan.hours_invested else 0.0,
            "estimated_hours_remaining": float(new_plan.estimated_hours_remaining) if new_plan.estimated_hours_remaining else None,
            "shareable_token": new_plan.shareable_token,
            "is_public": new_plan.is_public,
            "shared_with_recruiters": new_plan.shared_with_recruiters,
            "access_expires_at": new_plan.access_expires_at,
            "last_accessed_at": new_plan.last_accessed_at,
            "reminder_scheduled_at": new_plan.reminder_scheduled_at,
            "reminder_frequency": new_plan.reminder_frequency,
            "notes": new_plan.notes,
            "reapplication_status": new_plan.reapplication_status,
            "reapplication_date": new_plan.reapplication_date,
            "outcome_notes": new_plan.outcome_notes,
            "priority": new_plan.priority,
            "difficulty_level": new_plan.difficulty_level,
            "tags": new_plan.tags,
            "created_at": new_plan.created_at.isoformat() if new_plan.created_at else "",
            "updated_at": new_plan.updated_at.isoformat() if new_plan.updated_at else "",
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating development plan: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create development plan: {str(e)}",
        ) from e


@router.get(
    "/development-plans/",
    response_model=DevelopmentPlanListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Development Plans"],
)
async def list_development_plans(
    resume_id: Optional[str] = Query(None, description="Filter by resume ID"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List skill development plans with optional filtering.

    Supports filtering by resume_id, vacancy_id, status, priority, and is_public.
    Results are paginated.

    Args:
        resume_id: Optional filter by resume ID
        vacancy_id: Optional filter by vacancy ID
        status: Optional filter by status
        priority: Optional filter by priority
        is_public: Optional filter by public status
        page: Page number (1-indexed)
        page_size: Number of plans per page
        db: Database session

    Returns:
        JSON response with list of development plans

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/development-plans/?resume_id=abc-123")
        >>> response.json()
        {
            "plans": [...],
            "total": 5,
            "page": 1,
            "page_size": 20
        }
    """
    try:
        logger.info(
            f"Listing development plans: resume_id={resume_id}, vacancy_id={vacancy_id}, "
            f"status={status}, priority={priority}, is_public={is_public}"
        )

        # Build query
        query = select(SkillDevelopmentPlan)

        # Apply filters
        if resume_id:
            try:
                resume_uuid = UUID(resume_id)
                query = query.where(SkillDevelopmentPlan.resume_id == resume_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid resume_id format: {resume_id}",
                )

        if vacancy_id:
            try:
                vacancy_uuid = UUID(vacancy_id)
                query = query.where(SkillDevelopmentPlan.vacancy_id == vacancy_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid vacancy_id format: {vacancy_id}",
                )

        if status:
            valid_statuses = ["draft", "active", "completed", "paused", "abandoned"]
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}. Must be one of: {valid_statuses}",
                )
            query = query.where(SkillDevelopmentPlan.status == status)

        if priority:
            valid_priorities = ["low", "medium", "high", "urgent"]
            if priority not in valid_priorities:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid priority: {priority}. Must be one of: {valid_priorities}",
                )
            query = query.where(SkillDevelopmentPlan.priority == priority)

        if is_public is not None:
            query = query.where(SkillDevelopmentPlan.is_public == is_public)

        # Order by most recent first
        query = query.order_by(SkillDevelopmentPlan.created_at.desc())

        # Get total count
        from sqlalchemy import func

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(query)
        plans = result.scalars().all()

        # Convert to response format
        plan_responses = []
        for plan in plans:
            plan_responses.append({
                "id": str(plan.id),
                "resume_id": str(plan.resume_id),
                "vacancy_id": str(plan.vacancy_id) if plan.vacancy_id else None,
                "skill_gap_report_id": str(plan.skill_gap_report_id) if plan.skill_gap_report_id else None,
                "title": plan.title,
                "description": plan.description,
                "status": plan.status,
                "overall_progress": float(plan.overall_progress) if plan.overall_progress else 0.0,
                "start_date": plan.start_date,
                "target_completion_date": plan.target_completion_date,
                "actual_completion_date": plan.actual_completion_date,
                "learning_goals": plan.learning_goals,
                "milestones": plan.milestones,
                "recommended_resources": plan.recommended_resources,
                "completed_resources": plan.completed_resources,
                "total_resources_count": plan.total_resources_count,
                "completed_resources_count": plan.completed_resources_count,
                "hours_invested": float(plan.hours_invested) if plan.hours_invested else 0.0,
                "estimated_hours_remaining": float(plan.estimated_hours_remaining) if plan.estimated_hours_remaining else None,
                "shareable_token": plan.shareable_token,
                "is_public": plan.is_public,
                "shared_with_recruiters": plan.shared_with_recruiters,
                "access_expires_at": plan.access_expires_at,
                "last_accessed_at": plan.last_accessed_at,
                "reminder_scheduled_at": plan.reminder_scheduled_at,
                "reminder_frequency": plan.reminder_frequency,
                "notes": plan.notes,
                "reapplication_status": plan.reapplication_status,
                "reapplication_date": plan.reapplication_date,
                "outcome_notes": plan.outcome_notes,
                "priority": plan.priority,
                "difficulty_level": plan.difficulty_level,
                "tags": plan.tags,
                "created_at": plan.created_at.isoformat() if plan.created_at else "",
                "updated_at": plan.updated_at.isoformat() if plan.updated_at else "",
            })

        response_data = {
            "plans": plan_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

        logger.info(f"Returning {len(plan_responses)} development plans (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing development plans: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list development plans: {str(e)}",
        ) from e


@router.get(
    "/development-plans/{plan_id}",
    response_model=DevelopmentPlanResponse,
    status_code=status.HTTP_200_OK,
    tags=["Development Plans"],
)
async def get_development_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific skill development plan by ID.

    Args:
        plan_id: UUID of the development plan
        db: Database session

    Returns:
        JSON response with development plan details

    Raises:
        HTTPException(404): If plan is not found
        HTTPException(400): If plan_id format is invalid

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/development-plans/abc-123-def")
        >>> response.json()
        {
            "id": "abc-123-def",
            "title": "Full-Stack Developer Plan",
            ...
        }
    """
    try:
        logger.info(f"Fetching development plan: {plan_id}")

        # Validate plan_id format
        try:
            plan_uuid = UUID(plan_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan_id format: {plan_id}",
            )

        # Query database
        query = select(SkillDevelopmentPlan).where(SkillDevelopmentPlan.id == plan_uuid)
        result = await db.execute(query)
        plan = result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Development plan not found: {plan_id}",
            )

        # Update last_accessed_at
        from datetime import datetime
        plan.last_accessed_at = datetime.utcnow().isoformat()
        await db.commit()

        # Build response
        response_data = {
            "id": str(plan.id),
            "resume_id": str(plan.resume_id),
            "vacancy_id": str(plan.vacancy_id) if plan.vacancy_id else None,
            "skill_gap_report_id": str(plan.skill_gap_report_id) if plan.skill_gap_report_id else None,
            "title": plan.title,
            "description": plan.description,
            "status": plan.status,
            "overall_progress": float(plan.overall_progress) if plan.overall_progress else 0.0,
            "start_date": plan.start_date,
            "target_completion_date": plan.target_completion_date,
            "actual_completion_date": plan.actual_completion_date,
            "learning_goals": plan.learning_goals,
            "milestones": plan.milestones,
            "recommended_resources": plan.recommended_resources,
            "completed_resources": plan.completed_resources,
            "total_resources_count": plan.total_resources_count,
            "completed_resources_count": plan.completed_resources_count,
            "hours_invested": float(plan.hours_invested) if plan.hours_invested else 0.0,
            "estimated_hours_remaining": float(plan.estimated_hours_remaining) if plan.estimated_hours_remaining else None,
            "shareable_token": plan.shareable_token,
            "is_public": plan.is_public,
            "shared_with_recruiters": plan.shared_with_recruiters,
            "access_expires_at": plan.access_expires_at,
            "last_accessed_at": plan.last_accessed_at,
            "reminder_scheduled_at": plan.reminder_scheduled_at,
            "reminder_frequency": plan.reminder_frequency,
            "notes": plan.notes,
            "reapplication_status": plan.reapplication_status,
            "reapplication_date": plan.reapplication_date,
            "outcome_notes": plan.outcome_notes,
            "priority": plan.priority,
            "difficulty_level": plan.difficulty_level,
            "tags": plan.tags,
            "created_at": plan.created_at.isoformat() if plan.created_at else "",
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else "",
        }

        logger.info(f"Returning development plan: {plan_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching development plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch development plan: {str(e)}",
        ) from e


@router.put(
    "/development-plans/{plan_id}",
    response_model=DevelopmentPlanResponse,
    status_code=status.HTTP_200_OK,
    tags=["Development Plans"],
)
async def update_development_plan(
    plan_id: str,
    request: DevelopmentPlanUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a skill development plan.

    Allows updating most fields of a development plan. Use the progress
    endpoint for updating progress-related fields like completed_resources
    and hours_invested.

    Args:
        plan_id: UUID of the development plan
        request: Update request with fields to modify
        db: Database session

    Returns:
        JSON response with updated development plan

    Raises:
        HTTPException(404): If plan is not found
        HTTPException(422): If validation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "status": "active",
        ...     "title": "Updated Plan Title"
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8000/api/development-plans/abc-123",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Updating development plan: {plan_id}")

        # Validate plan_id format
        try:
            plan_uuid = UUID(plan_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan_id format: {plan_id}",
            )

        # Query database
        query = select(SkillDevelopmentPlan).where(SkillDevelopmentPlan.id == plan_uuid)
        result = await db.execute(query)
        plan = result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Development plan not found: {plan_id}",
            )

        # Update provided fields
        if request.title is not None:
            plan.title = request.title
        if request.description is not None:
            plan.description = request.description
        if request.status is not None:
            valid_statuses = ["draft", "active", "completed", "paused", "abandoned"]
            if request.status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid status: {request.status}. Must be one of: {valid_statuses}",
                )
            plan.status = request.status
        if request.overall_progress is not None:
            plan.overall_progress = request.overall_progress
        if request.priority is not None:
            valid_priorities = ["low", "medium", "high", "urgent"]
            if request.priority not in valid_priorities:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid priority: {request.priority}. Must be one of: {valid_priorities}",
                )
            plan.priority = request.priority
        if request.difficulty_level is not None:
            plan.difficulty_level = request.difficulty_level
        if request.start_date is not None:
            plan.start_date = request.start_date
        if request.target_completion_date is not None:
            plan.target_completion_date = request.target_completion_date
        if request.actual_completion_date is not None:
            plan.actual_completion_date = request.actual_completion_date
        if request.learning_goals is not None:
            plan.learning_goals = request.learning_goals
        if request.milestones is not None:
            plan.milestones = request.milestones
        if request.recommended_resources is not None:
            plan.recommended_resources = request.recommended_resources
            plan.total_resources_count = len(request.recommended_resources)
        if request.completed_resources is not None:
            plan.completed_resources = request.completed_resources
            plan.completed_resources_count = len(request.completed_resources)
        if request.hours_invested is not None:
            plan.hours_invested = request.hours_invested
        if request.estimated_hours_remaining is not None:
            plan.estimated_hours_remaining = request.estimated_hours_remaining
        if request.is_public is not None:
            plan.is_public = request.is_public
            # Generate shareable token if making public and token doesn't exist
            if request.is_public and not plan.shareable_token:
                import secrets
                plan.shareable_token = secrets.token_urlsafe(32)
        if request.reminder_frequency is not None:
            valid_frequencies = ["daily", "weekly", "monthly", "none"]
            if request.reminder_frequency not in valid_frequencies:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid reminder_frequency: {request.reminder_frequency}. Must be one of: {valid_frequencies}",
                )
            plan.reminder_frequency = request.reminder_frequency
        if request.notes is not None:
            plan.notes = request.notes
        if request.reapplication_status is not None:
            valid_statuses = ["not_applied", "applied", "interviewing", "offered", "hired"]
            if request.reapplication_status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid reapplication_status: {request.reapplication_status}. Must be one of: {valid_statuses}",
                )
            plan.reapplication_status = request.reapplication_status
        if request.reapplication_date is not None:
            plan.reapplication_date = request.reapplication_date
        if request.outcome_notes is not None:
            plan.outcome_notes = request.outcome_notes
        if request.tags is not None:
            plan.tags = request.tags

        await db.commit()

        logger.info(f"Updated development plan: {plan_id}")

        # Build response
        response_data = {
            "id": str(plan.id),
            "resume_id": str(plan.resume_id),
            "vacancy_id": str(plan.vacancy_id) if plan.vacancy_id else None,
            "skill_gap_report_id": str(plan.skill_gap_report_id) if plan.skill_gap_report_id else None,
            "title": plan.title,
            "description": plan.description,
            "status": plan.status,
            "overall_progress": float(plan.overall_progress) if plan.overall_progress else 0.0,
            "start_date": plan.start_date,
            "target_completion_date": plan.target_completion_date,
            "actual_completion_date": plan.actual_completion_date,
            "learning_goals": plan.learning_goals,
            "milestones": plan.milestones,
            "recommended_resources": plan.recommended_resources,
            "completed_resources": plan.completed_resources,
            "total_resources_count": plan.total_resources_count,
            "completed_resources_count": plan.completed_resources_count,
            "hours_invested": float(plan.hours_invested) if plan.hours_invested else 0.0,
            "estimated_hours_remaining": float(plan.estimated_hours_remaining) if plan.estimated_hours_remaining else None,
            "shareable_token": plan.shareable_token,
            "is_public": plan.is_public,
            "shared_with_recruiters": plan.shared_with_recruiters,
            "access_expires_at": plan.access_expires_at,
            "last_accessed_at": plan.last_accessed_at,
            "reminder_scheduled_at": plan.reminder_scheduled_at,
            "reminder_frequency": plan.reminder_frequency,
            "notes": plan.notes,
            "reapplication_status": plan.reapplication_status,
            "reapplication_date": plan.reapplication_date,
            "outcome_notes": plan.outcome_notes,
            "priority": plan.priority,
            "difficulty_level": plan.difficulty_level,
            "tags": plan.tags,
            "created_at": plan.created_at.isoformat() if plan.created_at else "",
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else "",
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating development plan: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update development plan: {str(e)}",
        ) from e


@router.patch(
    "/development-plans/{plan_id}/progress",
    response_model=DevelopmentPlanResponse,
    status_code=status.HTTP_200_OK,
    tags=["Development Plans"],
)
async def update_development_plan_progress(
    plan_id: str,
    request: DevelopmentPlanProgressUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update progress tracking for a skill development plan.

    This endpoint is specifically designed for tracking progress updates,
    such as marking resources as completed, updating progress percentage,
    and logging hours invested.

    Args:
        plan_id: UUID of the development plan
        request: Progress update request
        db: Database session

    Returns:
        JSON response with updated development plan

    Raises:
        HTTPException(404): If plan is not found

    Examples:
        >>> import requests
        >>> data = {
        ...     "completed_resources": [
        ...         {"resource_id": "res-1", "completed_at": "2024-01-31T10:00:00Z"}
        ...     ],
        ...     "hours_invested": 5.5,
        ...     "notes": "Completed React hooks module"
        ... }
        >>> response = requests.patch(
        ...     "http://localhost:8000/api/development-plans/abc-123/progress",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Updating progress for development plan: {plan_id}")

        # Validate plan_id format
        try:
            plan_uuid = UUID(plan_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan_id format: {plan_id}",
            )

        # Query database
        query = select(SkillDevelopmentPlan).where(SkillDevelopmentPlan.id == plan_uuid)
        result = await db.execute(query)
        plan = result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Development plan not found: {plan_id}",
            )

        # Update completed resources
        if request.completed_resources is not None:
            # Merge with existing completed resources
            existing_completed = plan.completed_resources or []
            resource_dict = {r.get("resource_id"): r for r in existing_completed}

            for resource in request.completed_resources:
                resource_id = resource.get("resource_id")
                if resource_id:
                    resource_dict[resource_id] = resource

            plan.completed_resources = list(resource_dict.values())
            plan.completed_resources_count = len(plan.completed_resources)

            # Auto-calculate overall_progress if not explicitly provided
            if request.overall_progress is None and plan.total_resources_count > 0:
                plan.overall_progress = (plan.completed_resources_count / plan.total_resources_count) * 100

        # Update overall progress if explicitly provided
        if request.overall_progress is not None:
            plan.overall_progress = request.overall_progress

        # Update hours invested (add to existing)
        if request.hours_invested is not None:
            plan.hours_invested += request.hours_invested

        # Update milestones if provided
        if request.milestone_updates is not None:
            existing_milestones = plan.milestones or []
            milestone_dict = {m.get("id"): m for m in existing_milestones}

            for milestone_update in request.milestone_updates:
                milestone_id = milestone_update.get("id")
                if milestone_id and milestone_id in milestone_dict:
                    milestone_dict[milestone_id].update(milestone_update)

            plan.milestones = list(milestone_dict.values())

        # Append notes if provided
        if request.notes:
            existing_notes = plan.notes or ""
            from datetime import datetime
            timestamp = datetime.utcnow().isoformat()
            plan.notes = f"{existing_notes}\n\n[{timestamp}] {request.notes}" if existing_notes else f"[{timestamp}] {request.notes}"

        # Update last_accessed_at
        from datetime import datetime
        plan.last_accessed_at = datetime.utcnow().isoformat()

        await db.commit()

        logger.info(f"Updated progress for development plan: {plan_id}")

        # Build response
        response_data = {
            "id": str(plan.id),
            "resume_id": str(plan.resume_id),
            "vacancy_id": str(plan.vacancy_id) if plan.vacancy_id else None,
            "skill_gap_report_id": str(plan.skill_gap_report_id) if plan.skill_gap_report_id else None,
            "title": plan.title,
            "description": plan.description,
            "status": plan.status,
            "overall_progress": float(plan.overall_progress) if plan.overall_progress else 0.0,
            "start_date": plan.start_date,
            "target_completion_date": plan.target_completion_date,
            "actual_completion_date": plan.actual_completion_date,
            "learning_goals": plan.learning_goals,
            "milestones": plan.milestones,
            "recommended_resources": plan.recommended_resources,
            "completed_resources": plan.completed_resources,
            "total_resources_count": plan.total_resources_count,
            "completed_resources_count": plan.completed_resources_count,
            "hours_invested": float(plan.hours_invested) if plan.hours_invested else 0.0,
            "estimated_hours_remaining": float(plan.estimated_hours_remaining) if plan.estimated_hours_remaining else None,
            "shareable_token": plan.shareable_token,
            "is_public": plan.is_public,
            "shared_with_recruiters": plan.shared_with_recruiters,
            "access_expires_at": plan.access_expires_at,
            "last_accessed_at": plan.last_accessed_at,
            "reminder_scheduled_at": plan.reminder_scheduled_at,
            "reminder_frequency": plan.reminder_frequency,
            "notes": plan.notes,
            "reapplication_status": plan.reapplication_status,
            "reapplication_date": plan.reapplication_date,
            "outcome_notes": plan.outcome_notes,
            "priority": plan.priority,
            "difficulty_level": plan.difficulty_level,
            "tags": plan.tags,
            "created_at": plan.created_at.isoformat() if plan.created_at else "",
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else "",
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating development plan progress: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update development plan progress: {str(e)}",
        ) from e


@router.delete(
    "/development-plans/{plan_id}",
    status_code=status.HTTP_200_OK,
    tags=["Development Plans"],
)
async def delete_development_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a skill development plan.

    Args:
        plan_id: UUID of the development plan
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If plan is not found

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/development-plans/abc-123")
        >>> response.json()
        {"message": "Development plan deleted successfully"}
    """
    try:
        logger.info(f"Deleting development plan: {plan_id}")

        # Validate plan_id format
        try:
            plan_uuid = UUID(plan_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan_id format: {plan_id}",
            )

        # Query database
        query = select(SkillDevelopmentPlan).where(SkillDevelopmentPlan.id == plan_uuid)
        result = await db.execute(query)
        plan = result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Development plan not found: {plan_id}",
            )

        # Delete the plan
        await db.delete(plan)
        await db.commit()

        logger.info(f"Deleted development plan: {plan_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Development plan {plan_id} deleted successfully"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting development plan: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete development plan: {str(e)}",
        ) from e
