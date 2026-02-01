"""
Pydantic models for parsed resume data.

This module defines data models for structured resume information extracted
from PDF and DOCX documents, including skills, position, education, work
experience, and languages.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class Skill(BaseModel):
    """
    Individual skill extracted from resume.

    Attributes:
        name: Normalized skill name (e.g., "React" not "React.js")
        original_name: Original skill name as found in resume
        category: Skill category (technical, soft, framework, language, etc.)
        variations: List of alternative names/synonyms for this skill
        sources: List of experience entry indices where this skill was used
        confidence: Confidence score for skill extraction (0.0 to 1.0)
    """

    name: str = Field(..., description="Normalized skill name")
    original_name: str = Field(..., description="Original skill name as found in resume")
    category: Optional[str] = Field(None, description="Skill category (technical, soft, framework, language)")
    variations: List[str] = Field(default_factory=list, description="Alternative names/synonyms")
    sources: List[int] = Field(default_factory=list, description="Experience entry indices where skill was used")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for extraction")

    def __repr__(self) -> str:
        return f"<Skill(name={self.name}, category={self.category})>"


class Education(BaseModel):
    """
    Education entry from resume.

    Attributes:
        degree: Degree level (Bachelor, Master, PhD, etc.)
        institution: University/college name
        field_of_study: Major/field of study
        start_date: Start date (ISO format or partial date like "2020-09")
        end_date: Graduation date (ISO format or partial date)
        gpa: Grade point average if mentioned
        description: Additional details (honors, thesis, etc.)
    """

    degree: Optional[str] = Field(None, description="Degree level (Bachelor, Master, PhD)")
    institution: Optional[str] = Field(None, description="University/college name")
    field_of_study: Optional[str] = Field(None, description="Major/field of study")
    start_date: Optional[str] = Field(None, description="Start date (ISO or partial format)")
    end_date: Optional[str] = Field(None, description="Graduation date (ISO or partial format)")
    gpa: Optional[str] = Field(None, description="Grade point average")
    description: Optional[str] = Field(None, description="Additional details (honors, thesis)")

    def __repr__(self) -> str:
        return f"<Education(degree={self.degree}, institution={self.institution})>"


class WorkExperience(BaseModel):
    """
    Work experience entry from resume.

    Attributes:
        company: Company/organization name
        position: Job title/position
        start_date: Start date (ISO format or partial date)
        end_date: End date (None if current position)
        duration_months: Duration in months (calculated)
        description: Job description and achievements
        skills: List of skills used in this role
        location: Job location (city, country)
    """

    company: Optional[str] = Field(None, description="Company/organization name")
    position: Optional[str] = Field(None, description="Job title/position")
    start_date: Optional[str] = Field(None, description="Start date (ISO or partial format)")
    end_date: Optional[str] = Field(None, description="End date (None if current position)")
    duration_months: Optional[int] = Field(None, description="Duration in months")
    description: Optional[str] = Field(None, description="Job description and achievements")
    skills: List[str] = Field(default_factory=list, description="Skills used in this role")
    location: Optional[str] = Field(None, description="Job location (city, country)")

    def __repr__(self) -> str:
        return f"<WorkExperience(company={self.company}, position={self.position})>"


class Language(BaseModel):
    """
    Language proficiency from resume.

    Attributes:
        name: Language name (English, Russian, etc.)
        proficiency: Proficiency level (native, fluent, intermediate, basic)
        certification: Language certification if any (IELTS, TOEFL, etc.)
    """

    name: str = Field(..., description="Language name")
    proficiency: Optional[str] = Field(None, description="Proficiency level (native, fluent, intermediate, basic)")
    certification: Optional[str] = Field(None, description="Language certification (IELTS, TOEFL)")

    def __repr__(self) -> str:
        return f"<Language(name={self.name}, proficiency={self.proficiency})>"


class ExperienceSummary(BaseModel):
    """
    Summary of total and framework-specific experience.

    Attributes:
        total_months: Total work experience in months
        total_years: Total work experience in years (float)
        total_years_formatted: Human-readable total experience (e.g., "5 years 6 months")
        framework_specific: Dictionary mapping framework/skill to specific experience
            Example: {"React": "3 years", "Python": "5 years"}
    """

    total_months: int = Field(..., ge=0, description="Total work experience in months")
    total_years: float = Field(..., ge=0.0, description="Total work experience in years")
    total_years_formatted: str = Field(..., description="Human-readable experience string")
    framework_specific: dict = Field(default_factory=dict, description="Framework-specific experience")

    def __repr__(self) -> str:
        return f"<ExperienceSummary(total_years={self.total_years})>"


class ParsedResume(BaseModel):
    """
    Complete parsed resume data.

    This model contains all extracted information from a resume document,
    including personal information, skills, work history, education, and
    calculated metrics like experience summary.

    Attributes:
        raw_text: Full text extracted from resume document
        language: Detected resume language (en, ru)
        position: Current/most recent job position
        age: Age if explicitly mentioned (null otherwise)
        skills: List of extracted skills with metadata
        education: List of education entries
        work_experience: List of work experience entries
        languages: List of languages with proficiency
        experience_summary: Summary of total and framework-specific experience
        warnings: List of parsing warnings (missing dates, ambiguities, etc.)
        processing_metadata: Metadata about parsing process (models used, version, etc.)
    """

    raw_text: Optional[str] = Field(None, description="Full text extracted from resume")
    language: str = Field(..., description="Detected resume language (en, ru)")
    position: Optional[str] = Field(None, description="Current/most recent job position")
    age: Optional[int] = Field(None, ge=0, le=150, description="Age if explicitly mentioned")
    skills: List[Skill] = Field(default_factory=list, description="Extracted skills")
    education: List[Education] = Field(default_factory=list, description="Education entries")
    work_experience: List[WorkExperience] = Field(default_factory=list, description="Work experience entries")
    languages: List[Language] = Field(default_factory=list, description="Languages with proficiency")
    experience_summary: Optional[ExperienceSummary] = Field(None, description="Experience summary")
    warnings: List[str] = Field(default_factory=list, description="Parsing warnings")
    processing_metadata: dict = Field(default_factory=dict, description="Processing metadata")

    def __repr__(self) -> str:
        return f"<ParsedResume(language={self.language}, position={self.position}, skills={len(self.skills)})>"

    def model_dump_schema(self) -> dict:
        """
        Return a schema dictionary for JSON serialization.

        This is a convenience method for exporting the parsed resume
        to JSON format, ensuring all nested models are properly serialized.
        """
        return self.model_dump(mode='json')
