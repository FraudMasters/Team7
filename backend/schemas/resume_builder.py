"""
Pydantic schemas for resume builder API.

This module provides request/response models for:
- Resume CRUD operations (create, read, update, delete)
- Resume content structure (personal info, work experience, education, skills)
- AI-powered improvement suggestions
- ATS optimization scoring
- Document export (PDF, DOCX)
- Skill gap analysis against target jobs

These schemas ensure data validation and serialization for the resume builder API.
"""
from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Resume Content Section Models
# =============================================================================


class PersonalInfo(BaseModel):
    """Personal information section of a resume."""

    full_name: Optional[str] = Field(None, description="Full name", max_length=255)
    email: Optional[str] = Field(None, description="Email address", max_length=255)
    phone: Optional[str] = Field(None, description="Phone number", max_length=50)
    location: Optional[str] = Field(None, description="City, Country", max_length=255)
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL", max_length=512)
    website_url: Optional[str] = Field(None, description="Personal website URL", max_length=512)
    github_url: Optional[str] = Field(None, description="GitHub profile URL", max_length=512)
    title: Optional[str] = Field(None, description="Professional title/headline", max_length=255)
    summary: Optional[str] = Field(None, description="Professional summary/objective")


class WorkExperienceEntry(BaseModel):
    """A single work experience entry."""

    id: Optional[str] = Field(None, description="Unique identifier for this entry")
    company: Optional[str] = Field(None, description="Company name", max_length=255)
    position: Optional[str] = Field(None, description="Job title/position", max_length=255)
    location: Optional[str] = Field(None, description="Work location", max_length=255)
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM or YYYY)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM, YYYY, or 'Present')")
    is_current: bool = Field(False, description="Whether this is a current position")
    description: Optional[str] = Field(None, description="Job description and achievements")
    skills: List[str] = Field(default_factory=list, description="Skills used in this role")
    highlights: List[str] = Field(default_factory=list, description="Key achievements/bullet points")


class EducationEntry(BaseModel):
    """A single education entry."""

    id: Optional[str] = Field(None, description="Unique identifier for this entry")
    institution: Optional[str] = Field(None, description="School/university name", max_length=255)
    degree: Optional[str] = Field(None, description="Degree type (Bachelor, Master, etc.)", max_length=100)
    field_of_study: Optional[str] = Field(None, description="Major/field of study", max_length=255)
    location: Optional[str] = Field(None, description="Institution location", max_length=255)
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM or YYYY)")
    end_date: Optional[str] = Field(None, description="Graduation date (YYYY-MM or YYYY)")
    gpa: Optional[str] = Field(None, description="GPA", max_length=20)
    honors: List[str] = Field(default_factory=list, description="Honors/awards")
    description: Optional[str] = Field(None, description="Additional details (thesis, activities)")


class SkillEntry(BaseModel):
    """A skill entry with optional categorization."""

    name: str = Field(..., description="Skill name", max_length=100)
    category: Optional[str] = Field(None, description="Skill category (technical, soft, language)", max_length=50)
    level: Optional[str] = Field(None, description="Proficiency level (expert, advanced, intermediate, basic)", max_length=50)
    years_of_experience: Optional[int] = Field(None, description="Years of experience with this skill", ge=0)


class CertificationEntry(BaseModel):
    """A certification or license entry."""

    id: Optional[str] = Field(None, description="Unique identifier for this entry")
    name: str = Field(..., description="Certification name", max_length=255)
    issuer: Optional[str] = Field(None, description="Issuing organization", max_length=255)
    issue_date: Optional[str] = Field(None, description="Issue date (YYYY-MM or YYYY)")
    expiry_date: Optional[str] = Field(None, description="Expiry date (YYYY-MM or YYYY), if applicable")
    credential_id: Optional[str] = Field(None, description="Credential ID or number", max_length=100)
    credential_url: Optional[str] = Field(None, description="URL to verify credential", max_length=512)


class LanguageEntry(BaseModel):
    """A language proficiency entry."""

    name: str = Field(..., description="Language name", max_length=100)
    proficiency: Optional[str] = Field(None, description="Proficiency level (native, fluent, intermediate, basic)", max_length=50)
    certification: Optional[str] = Field(None, description="Language certification (IELTS, TOEFL, etc.)", max_length=100)


class ProjectEntry(BaseModel):
    """A project entry."""

    id: Optional[str] = Field(None, description="Unique identifier for this entry")
    name: str = Field(..., description="Project name", max_length=255)
    description: Optional[str] = Field(None, description="Project description")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM or YYYY)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM or YYYY)")
    url: Optional[str] = Field(None, description="Project URL", max_length=512)
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    highlights: List[str] = Field(default_factory=list, description="Key achievements")


class ResumeContent(BaseModel):
    """
    Complete resume content structure.

    This model represents the JSON content stored in the BuiltResume.content field.
    It contains all sections of a resume in a structured format.
    """

    personal_info: Optional[PersonalInfo] = Field(None, description="Personal information section")
    summary: Optional[str] = Field(None, description="Professional summary/objective")
    work_experience: List[WorkExperienceEntry] = Field(default_factory=list, description="Work experience entries")
    education: List[EducationEntry] = Field(default_factory=list, description="Education entries")
    skills: List[SkillEntry] = Field(default_factory=list, description="Skills")
    certifications: List[CertificationEntry] = Field(default_factory=list, description="Certifications")
    languages: List[LanguageEntry] = Field(default_factory=list, description="Languages")
    projects: List[ProjectEntry] = Field(default_factory=list, description="Projects")
    custom_sections: Dict[str, Any] = Field(default_factory=dict, description="Custom sections")


# =============================================================================
# AI Suggestions Models
# =============================================================================


class AISuggestion(BaseModel):
    """A single AI-generated improvement suggestion."""

    id: str = Field(..., description="Unique suggestion identifier")
    type: str = Field(..., description="Suggestion type (content, grammar, keyword, format, ats)")
    section: str = Field(..., description="Target section (summary, work_experience, skills, etc.)")
    field: Optional[str] = Field(None, description="Specific field within section")
    entry_id: Optional[str] = Field(None, description="ID of the specific entry being improved")
    original_text: Optional[str] = Field(None, description="Original text to be replaced")
    suggested_text: str = Field(..., description="Suggested improvement text")
    reason: Optional[str] = Field(None, description="Explanation for the suggestion")
    priority: int = Field(0, description="Priority level (0=low, 1=medium, 2=high)", ge=0, le=2)
    impact_score: Optional[float] = Field(None, description="Expected impact on ATS score (0-100)", ge=0, le=100)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        valid_types = ["content", "grammar", "keyword", "format", "ats", "skills"]
        if v not in valid_types:
            raise ValueError(f"Invalid type. Must be one of: {', '.join(valid_types)}")
        return v


class AISuggestionsResponse(BaseModel):
    """Response model for AI suggestions."""

    suggestions: List[AISuggestion] = Field(default_factory=list, description="List of suggestions")
    ats_score_before: Optional[int] = Field(None, description="ATS score before applying suggestions", ge=0, le=100)
    ats_score_potential: Optional[int] = Field(None, description="Potential ATS score if all applied", ge=0, le=100)
    generated_at: str = Field(..., description="Timestamp when suggestions were generated")


class ApplySuggestionRequest(BaseModel):
    """Request model for applying an AI suggestion."""

    suggestion_id: str = Field(..., description="ID of the suggestion to apply")
    modified_text: Optional[str] = Field(None, description="Optional modified version of suggested text")


# =============================================================================
# ATS Optimization Models
# =============================================================================


class ATSIssue(BaseModel):
    """An ATS optimization issue."""

    section: str = Field(..., description="Section with the issue")
    field: Optional[str] = Field(None, description="Specific field with the issue")
    entry_id: Optional[str] = Field(None, description="ID of the specific entry")
    issue_type: str = Field(..., description="Type of issue (missing_keyword, format, length, etc.)")
    severity: str = Field(..., description="Severity level (low, medium, high)")
    description: str = Field(..., description="Description of the issue")
    suggestion: Optional[str] = Field(None, description="Suggested fix")


class ATSScoreResponse(BaseModel):
    """Response model for ATS score analysis."""

    score: int = Field(..., description="ATS compatibility score (0-100)", ge=0, le=100)
    issues: List[ATSIssue] = Field(default_factory=list, description="List of issues found")
    keywords_found: List[str] = Field(default_factory=list, description="Keywords detected in resume")
    keywords_missing: List[str] = Field(default_factory=list, description="Important keywords missing")
    sections_analyzed: List[str] = Field(default_factory=list, description="Sections that were analyzed")
    analyzed_at: str = Field(..., description="Timestamp of analysis")


# =============================================================================
# Skill Gap Analysis Models
# =============================================================================


class SkillGap(BaseModel):
    """A skill gap between resume and target job."""

    skill_name: str = Field(..., description="Name of the missing skill")
    category: Optional[str] = Field(None, description="Skill category")
    importance: str = Field(..., description="Importance level (required, preferred, nice_to_have)")
    job_frequency: Optional[int] = Field(None, description="How often this skill appears in similar jobs (%)", ge=0, le=100)
    learning_resources: List[Dict[str, Any]] = Field(default_factory=list, description="Suggested learning resources")


class SkillGapAnalysisResponse(BaseModel):
    """Response model for skill gap analysis."""

    target_job_id: str = Field(..., description="ID of the target job vacancy")
    target_job_title: Optional[str] = Field(None, description="Title of the target job")
    matching_skills: List[str] = Field(default_factory=list, description="Skills that match the job")
    partial_match_skills: List[str] = Field(default_factory=list, description="Skills with partial match")
    missing_skills: List[SkillGap] = Field(default_factory=list, description="Missing skills with details")
    match_percentage: int = Field(..., description="Overall match percentage", ge=0, le=100)
    recommendations: List[str] = Field(default_factory=list, description="General recommendations")
    analyzed_at: str = Field(..., description="Timestamp of analysis")


# =============================================================================
# Export Models
# =============================================================================


class ExportFormat:
    """Supported export formats."""
    PDF = "pdf"
    DOCX = "docx"
    JSON = "json"


class ExportRequest(BaseModel):
    """Request model for exporting a resume."""

    format: str = Field(..., description="Export format (pdf, docx, json)")

    @field_validator("format")
    @classmethod
    def validate_format(cls, v):
        valid_formats = [ExportFormat.PDF, ExportFormat.DOCX, ExportFormat.JSON]
        if v not in valid_formats:
            raise ValueError(f"Invalid format. Must be one of: {', '.join(valid_formats)}")
        return v


class ExportResponse(BaseModel):
    """Response model for export operation."""

    download_url: str = Field(..., description="URL to download the exported file")
    filename: str = Field(..., description="Generated filename")
    format: str = Field(..., description="Export format used")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    expires_at: Optional[str] = Field(None, description="Download URL expiration timestamp")


# =============================================================================
# Resume CRUD Schemas
# =============================================================================


class BuiltResumeCreate(BaseModel):
    """Request model for creating a new resume."""

    template_id: Optional[str] = Field(None, description="Template ID to use for this resume")
    title: str = Field(..., description="Resume title/name", min_length=1, max_length=255)
    content: Optional[ResumeContent] = Field(None, description="Initial resume content")
    target_job_id: Optional[str] = Field(None, description="Target job vacancy ID for skill gap analysis")
    is_draft: bool = Field(True, description="Whether this is a draft")


class BuiltResumeUpdate(BaseModel):
    """Request model for updating an existing resume."""

    template_id: Optional[str] = Field(None, description="Updated template ID")
    title: Optional[str] = Field(None, description="Updated resume title", min_length=1, max_length=255)
    content: Optional[ResumeContent] = Field(None, description="Updated resume content")
    target_job_id: Optional[str] = Field(None, description="Updated target job vacancy ID")
    ats_score: Optional[int] = Field(None, description="Updated ATS score", ge=0, le=100)
    is_draft: Optional[bool] = Field(None, description="Updated draft status")


class BuiltResumeResponse(BaseModel):
    """Response model for a single resume."""

    id: str = Field(..., description="Resume UUID")
    user_id: str = Field(..., description="Owner user ID")
    organization_id: str = Field(..., description="Organization ID")
    template_id: Optional[str] = Field(None, description="Template ID")
    title: str = Field(..., description="Resume title")
    content: ResumeContent = Field(..., description="Resume content")
    target_job_id: Optional[str] = Field(None, description="Target job vacancy ID")
    ats_score: Optional[int] = Field(None, description="ATS score (0-100)")
    version: int = Field(..., description="Resume version number")
    is_draft: bool = Field(..., description="Whether this is a draft")
    last_ai_suggestions: Optional[AISuggestionsResponse] = Field(None, description="Last AI suggestions")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class BuiltResumeListResponse(BaseModel):
    """Response model for listing resumes."""

    items: List[BuiltResumeResponse] = Field(..., description="List of resumes")
    total: int = Field(..., description="Total number of resumes")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class BuiltResumeSummary(BaseModel):
    """Summary model for resume list view (lighter response)."""

    id: str = Field(..., description="Resume UUID")
    title: str = Field(..., description="Resume title")
    ats_score: Optional[int] = Field(None, description="ATS score")
    version: int = Field(..., description="Version number")
    is_draft: bool = Field(..., description="Draft status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class BuiltResumeSummaryListResponse(BaseModel):
    """Response model for listing resume summaries."""

    items: List[BuiltResumeSummary] = Field(..., description="List of resume summaries")
    total: int = Field(..., description="Total number of resumes")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


# =============================================================================
# Template Models
# =============================================================================


class ResumeTemplateSummary(BaseModel):
    """Summary model for a resume template."""

    id: str = Field(..., description="Template UUID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    preview_url: Optional[str] = Field(None, description="Preview image URL")
    category: Optional[str] = Field(None, description="Template category (modern, classic, etc.)")
    is_premium: bool = Field(False, description="Whether this is a premium template")


class ResumeTemplateListResponse(BaseModel):
    """Response model for listing resume templates."""

    items: List[ResumeTemplateSummary] = Field(..., description="List of templates")
    total: int = Field(..., description="Total number of templates")


# =============================================================================
# Version History Models
# =============================================================================


class ResumeVersionSummary(BaseModel):
    """Summary of a resume version."""

    version: int = Field(..., description="Version number")
    title: str = Field(..., description="Title at this version")
    ats_score: Optional[int] = Field(None, description="ATS score at this version")
    created_at: str = Field(..., description="When this version was created")
    changes_summary: Optional[str] = Field(None, description="Summary of changes from previous version")


class ResumeVersionHistoryResponse(BaseModel):
    """Response model for resume version history."""

    resume_id: str = Field(..., description="Resume UUID")
    current_version: int = Field(..., description="Current version number")
    versions: List[ResumeVersionSummary] = Field(..., description="List of all versions")
