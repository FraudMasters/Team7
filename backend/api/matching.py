"""
Job matching endpoints with skill synonym handling and visual highlighting.

This module provides endpoints for comparing resumes against job vacancies,
calculating match percentages, and providing visual highlighting for
matched (green) and missing (red) skills.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add parent directory to path to import from data_extractor service
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "data_extractor"))

from ..analyzers import (
    extract_resume_keywords,
    extract_resume_entities,
    calculate_skill_experience,
    format_experience_summary,
    EnhancedSkillMatcher,
)
from ..i18n.backend_translations import get_error_message, get_success_message

logger = logging.getLogger(__name__)

router = APIRouter()

# Directory where uploaded resumes are stored
UPLOAD_DIR = Path("data/uploads")

# Path to skill synonyms file
SYNONYMS_FILE = Path(__file__).parent.parent / "models" / "skill_synonyms.json"

# Cache for skill synonyms
_skill_synonyms_cache: Optional[Dict[str, List[str]]] = None


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


def load_skill_synonyms() -> Dict[str, List[str]]:
    """
    Load skill synonyms from JSON file.

    Returns a dictionary mapping canonical skill names to lists of synonyms.

    The synonyms file structure organizes skills by category (databases,
    programming_languages, web_frameworks, etc.) with each skill having
    a canonical name and list of equivalent terms.

    Returns:
        Dictionary mapping skill names to their synonyms

    Example:
        >>> synonyms = load_skill_synonyms()
        >>> synonyms["PostgreSQL"]
        ["PostgreSQL", "Postgres", "Postgres SQL"]
    """
    global _skill_synonyms_cache

    if _skill_synonyms_cache is not None:
        return _skill_synonyms_cache

    try:
        with open(SYNONYMS_FILE, "r", encoding="utf-8") as f:
            synonyms_data = json.load(f)

        # Flatten the category structure into a single dictionary
        # Input: {"databases": {"SQL": ["SQL", "PostgreSQL", ...]}}
        # Output: {"SQL": ["SQL", "PostgreSQL", ...]}
        flat_synonyms: Dict[str, List[str]] = {}

        for category in synonyms_data.values():
            if isinstance(category, dict):
                for canonical_name, synonyms_list in category.items():
                    if isinstance(synonyms_list, list):
                        # Ensure the canonical name itself is in the list
                        all_synonyms = set(synonyms_list + [canonical_name])
                        flat_synonyms[canonical_name] = list(all_synonyms)

        _skill_synonyms_cache = flat_synonyms
        logger.info(f"Loaded {len(flat_synonyms)} skill synonym mappings")
        return flat_synonyms

    except FileNotFoundError:
        logger.warning(f"Skill synonyms file not found: {SYNONYMS_FILE}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing skill synonyms JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading skill synonyms: {e}", exc_info=True)
        return {}


def normalize_skill_name(skill: str) -> str:
    """
    Normalize a skill name for consistent comparison.

    Removes extra whitespace, converts to lowercase, and handles
    common variations in capitalization and spacing.

    Args:
        skill: The skill name to normalize

    Returns:
        Normalized skill name

    Example:
        >>> normalize_skill_name("  React JS  ")
        "react js"
    """
    return " ".join(skill.strip().lower().split())


def check_skill_match(
    resume_skills: List[str], required_skill: str, synonyms_map: Dict[str, List[str]]
) -> bool:
    """
    Check if a required skill matches any skill in the resume.

    Performs case-insensitive comparison and checks for skill synonyms.
    For example, if the vacancy requires "SQL" and the resume has "PostgreSQL",
    this will match if "PostgreSQL" is in the synonyms list for "SQL".

    Args:
        resume_skills: List of skills extracted from the resume
        required_skill: The skill required by the vacancy
        synonyms_map: Dictionary of skill synonyms

    Returns:
        True if the skill is found in resume skills (direct match or synonym)

    Example:
        >>> synonyms = {"SQL": ["SQL", "PostgreSQL", "MySQL"]}
        >>> check_skill_match(["Java", "PostgreSQL"], "SQL", synonyms)
        True
    """
    normalized_required = normalize_skill_name(required_skill)

    # First check for direct match
    for resume_skill in resume_skills:
        if normalize_skill_name(resume_skill) == normalized_required:
            return True

    # Then check for synonym matches
    # Get all synonyms for the required skill
    all_required_variants = [normalized_required]

    for canonical_name, synonym_list in synonyms_map.items():
        normalized_canonical = normalize_skill_name(canonical_name)
        # If this canonical name matches the required skill
        if normalized_canonical == normalized_required:
            # Add all its synonyms
            all_required_variants.extend(
                [normalize_skill_name(s) for s in synonym_list]
            )
        # Also check if any synonym matches
        for synonym in synonym_list:
            if normalize_skill_name(synonym) == normalized_required:
                all_required_variants.extend(
                    [normalize_skill_name(canonical_name)] +
                    [normalize_skill_name(s) for s in synonym_list]
                )
                break

    # Check if any resume skill matches any variant
    unique_variants = set(all_required_variants)
    for resume_skill in resume_skills:
        if normalize_skill_name(resume_skill) in unique_variants:
            return True

    return False


def find_matching_synonym(
    resume_skills: List[str], required_skill: str, synonyms_map: Dict[str, List[str]]
) -> Optional[str]:
    """
    Find the matching resume skill for a required skill.

    Returns the actual skill name from the resume that matches the required skill,
    either directly or through synonyms. Useful for displaying to the user
    which specific variant was found.

    Args:
        resume_skills: List of skills extracted from the resume
        required_skill: The skill required by the vacancy
        synonyms_map: Dictionary of skill synonyms

    Returns:
        The matching resume skill name, or None if no match found

    Example:
        >>> synonyms = {"SQL": ["SQL", "PostgreSQL"]}
        >>> find_matching_synonym(["Java", "PostgreSQL"], "SQL", synonyms)
        "PostgreSQL"
    """
    normalized_required = normalize_skill_name(required_skill)

    # Build set of all variants for the required skill
    all_variants = {normalized_required}

    for canonical_name, synonym_list in synonyms_map.items():
        normalized_canonical = normalize_skill_name(canonical_name)
        if normalized_canonical == normalized_required:
            all_variants.update([normalize_skill_name(s) for s in synonym_list])
        else:
            for synonym in synonym_list:
                if normalize_skill_name(synonym) == normalized_required:
                    all_variants.add(normalized_canonical)
                    all_variants.update([normalize_skill_name(s) for s in synonym_list])
                    break

    # Find matching resume skill
    for resume_skill in resume_skills:
        if normalize_skill_name(resume_skill) in all_variants:
            return resume_skill

    return None


class MatchRequest(BaseModel):
    """Request model for job matching endpoint."""

    resume_id: str = Field(..., description="Unique identifier of the resume to match")
    vacancy_data: Dict[str, Any] = Field(
        ..., description="Job vacancy data with required skills and experience"
    )


class SkillMatch(BaseModel):
    """Individual skill match result with confidence scoring."""

    skill: str = Field(..., description="The skill name from the vacancy")
    status: str = Field(..., description="Match status: 'matched' or 'missing'")
    matched_as: Optional[str] = Field(
        None, description="The actual skill name found in resume (if matched)"
    )
    highlight: str = Field(..., description="Highlight color: 'green' or 'red'")
    confidence: float = Field(
        0.0, description="Confidence score from 0.0 to 1.0 (0% to 100%)"
    )
    match_type: str = Field(
        "none", description="Type of match: 'direct', 'context', 'synonym', 'fuzzy', or 'none'"
    )


class ExperienceVerification(BaseModel):
    """Experience verification results."""

    required_months: int = Field(..., description="Required experience in months")
    actual_months: int = Field(..., description="Actual experience in months")
    meets_requirement: bool = Field(..., description="Whether experience requirement is met")
    summary: str = Field(..., description="Human-readable experience summary")


class MatchResponse(BaseModel):
    """Complete job matching response."""

    resume_id: str = Field(..., description="Resume identifier")
    vacancy_title: str = Field(..., description="Job vacancy title")
    match_percentage: float = Field(..., description="Overall skill match percentage (0-100)")
    required_skills_match: List[SkillMatch] = Field(
        ..., description="Match results for required skills"
    )
    additional_skills_match: List[SkillMatch] = Field(
        ..., description="Match results for additional/preferred skills"
    )
    experience_verification: Optional[ExperienceVerification] = Field(
        None, description="Experience requirement verification (if applicable)"
    )
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class MatchFeedbackRequest(BaseModel):
    """Request model for submitting feedback on skill matches."""

    match_id: str = Field(..., description="ID of the match result")
    skill: str = Field(..., description="The skill name that was matched")
    was_correct: bool = Field(..., description="Whether the AI's match was correct")
    recruiter_correction: Optional[str] = Field(
        None, description="What the recruiter corrected it to (if incorrect)"
    )
    confidence_score: Optional[float] = Field(
        None,
        description="The confidence score the AI assigned (0-1)",
        ge=0,
        le=1,
    )
    metadata: Optional[dict] = Field(None, description="Additional feedback metadata")


class MatchFeedbackResponse(BaseModel):
    """Response model for match feedback submission."""

    id: str = Field(..., description="Unique identifier for the feedback entry")
    match_id: str = Field(..., description="ID of the match result")
    skill: str = Field(..., description="The skill name that was matched")
    was_correct: bool = Field(..., description="Whether the AI's match was correct")
    recruiter_correction: Optional[str] = Field(None, description="Recruiter's correction")
    feedback_source: str = Field(..., description="Source of feedback")
    processed: bool = Field(..., description="Whether feedback has been processed by ML pipeline")
    created_at: str = Field(..., description="Creation timestamp")


@router.post(
    "/compare",
    response_model=MatchResponse,
    status_code=status.HTTP_200_OK,
    tags=["Matching"],
)
async def compare_resume_to_vacancy(http_request: Request, request: MatchRequest) -> JSONResponse:
    """
    Compare a resume to a job vacancy with skill synonym handling.

    This endpoint performs intelligent matching between resume skills and job
    vacancy requirements, handling synonyms (e.g., PostgreSQL ≈ SQL) and
    providing visual highlighting for recruiters.

    Features:
    - Skill synonym matching (PostgreSQL matches SQL requirement)
    - Match percentage calculation
    - Visual highlighting (green=matched, red=missing)
    - Experience verification (sums months across projects)
    - Case-insensitive comparison
    - Support for multi-word skills

    Args:
        http_request: FastAPI request object (for Accept-Language header)
        request: Match request with resume_id and vacancy_data

    Returns:
        JSON response with match results, highlighting data, and verification

    Raises:
        HTTPException(404): If resume file is not found
        HTTPException(422): If text extraction fails
        HTTPException(500): If matching processing fails

    Examples:
        >>> import requests
        >>> vacancy = {
        ...     "title": "Java Developer",
        ...     "required_skills": ["Java", "Spring", "SQL"],
        ...     "min_experience_months": 36
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/matching/compare",
        ...     json={"resume_id": "abc123", "vacancy_data": vacancy}
        ... )
        >>> response.json()
        {
            "resume_id": "abc123",
            "vacancy_title": "Java Developer",
            "match_percentage": 66.67,
            "required_skills_match": [
                {"skill": "Java", "status": "matched", "matched_as": "Java", "highlight": "green"},
                {"skill": "Spring", "status": "matched", "matched_as": "Spring Boot", "highlight": "green"},
                {"skill": "SQL", "status": "matched", "matched_as": "PostgreSQL", "highlight": "green"}
            ],
            "additional_skills_match": [],
            "experience_verification": {
                "required_months": 36,
                "actual_months": 47,
                "meets_requirement": true,
                "summary": "47 months (3 years 11 months) of experience"
            },
            "processing_time_ms": 123.45
        }
    """
    import time

    # Extract locale from Accept-Language header
    locale = _extract_locale(http_request)

    start_time = time.time()

    try:
        logger.info(f"Starting matching for resume_id: {request.resume_id}")

        # Step 1: Find the resume file
        for ext in [".pdf", ".docx", ".PDF", ".DOCX"]:
            file_path = UPLOAD_DIR / f"{request.resume_id}{ext}"
            if file_path.exists():
                break
        else:
            error_msg = get_error_message("file_not_found", locale)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        logger.info(f"Found resume file: {file_path}")

        # Step 2: Extract text from file
        try:
            from extract import extract_text_from_pdf, extract_text_from_docx

            file_ext = file_path.suffix.lower()
            if file_ext == ".pdf":
                result = extract_text_from_pdf(file_path)
            elif file_ext == ".docx":
                result = extract_text_from_docx(file_path)
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

        # Step 3: Detect language
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

        # Step 4: Extract skills from resume
        logger.info("Extracting skills from resume...")
        keywords_result = extract_resume_keywords(
            resume_text, language=language, top_n=50
        )
        entities_result = extract_resume_entities(resume_text, language=language)

        # Combine keywords and technical skills
        resume_skills = list(set(
            keywords_result.get("keywords", []) +
            keywords_result.get("keyphrases", []) +
            entities_result.get("technical_skills", [])
        ))

        logger.info(f"Extracted {len(resume_skills)} unique skills from resume")

        # Step 5: Initialize enhanced skill matcher
        enhanced_matcher = EnhancedSkillMatcher()
        # Pre-load synonyms for logging
        synonyms_map = enhanced_matcher.load_synonyms()
        logger.info(f"Initialized enhanced skill matcher with {len(synonyms_map)} synonym mappings")

        # Step 6: Get vacancy data
        vacancy_title = request.vacancy_data.get(
            "title", request.vacancy_data.get("position", "Unknown Position")
        )
        required_skills = request.vacancy_data.get("required_skills", [])
        additional_skills = request.vacancy_data.get(
            "additional_requirements", request.vacancy_data.get("additional_skills", [])
        )
        min_experience_months = request.vacancy_data.get("min_experience_months", None)

        # If required_skills is a string list, use it directly
        if isinstance(required_skills, str):
            required_skills = [required_skills]

        # Step 7: Match required skills with enhanced matcher
        required_skills_matches = []
        for skill in required_skills:
            # Use enhanced matcher with context awareness
            match_result = enhanced_matcher.match_with_context(
                resume_skills=resume_skills,
                required_skill=skill,
                context=vacancy_title.lower(),  # Use vacancy title as context hint
                use_fuzzy=True  # Enable fuzzy matching
            )

            if match_result["matched"]:
                required_skills_matches.append(
                    SkillMatch(
                        skill=skill,
                        status="matched",
                        matched_as=match_result["matched_as"],
                        highlight="green",
                        confidence=round(match_result["confidence"], 2),
                        match_type=match_result["match_type"]
                    )
                )
            else:
                required_skills_matches.append(
                    SkillMatch(
                        skill=skill,
                        status="missing",
                        matched_as=None,
                        highlight="red",
                        confidence=0.0,
                        match_type="none"
                    )
                )

        # Step 8: Match additional/preferred skills with enhanced matcher
        additional_skills_matches = []
        for skill in additional_skills:
            # Use enhanced matcher with context awareness
            match_result = enhanced_matcher.match_with_context(
                resume_skills=resume_skills,
                required_skill=skill,
                context=vacancy_title.lower(),  # Use vacancy title as context hint
                use_fuzzy=True  # Enable fuzzy matching
            )

            if match_result["matched"]:
                additional_skills_matches.append(
                    SkillMatch(
                        skill=skill,
                        status="matched",
                        matched_as=match_result["matched_as"],
                        highlight="green",
                        confidence=round(match_result["confidence"], 2),
                        match_type=match_result["match_type"]
                    )
                )
            else:
                additional_skills_matches.append(
                    SkillMatch(
                        skill=skill,
                        status="missing",
                        matched_as=None,
                        highlight="red",
                        confidence=0.0,
                        match_type="none"
                    )
                )

        # Step 9: Calculate match percentage
        total_required = len(required_skills)
        matched_required = sum(
            1 for m in required_skills_matches if m.status == "matched"
        )
        match_percentage = (
            round((matched_required / total_required * 100), 2) if total_required > 0 else 0.0
        )

        logger.info(
            f"Matched {matched_required}/{total_required} required skills ({match_percentage}%)"
        )

        # Step 10: Verify experience (if vacancy has experience requirement)
        experience_verification = None
        if min_experience_months and min_experience_months > 0:
            logger.info(f"Verifying experience requirement: {min_experience_months} months")

            # Try to get experience from vacancy data's main skill
            # For now, we'll use the first required skill as the primary skill
            primary_skill = required_skills[0] if required_skills else None

            if primary_skill:
                try:
                    # Calculate experience for the primary skill
                    skill_exp_result = calculate_skill_experience(
                        resume_text, primary_skill, language=language
                    )
                    actual_months = skill_exp_result.get("total_months", 0)

                    # Format the experience summary
                    experience_summary = format_experience_summary(actual_months)

                    experience_verification = ExperienceVerification(
                        required_months=min_experience_months,
                        actual_months=actual_months,
                        meets_requirement=actual_months >= min_experience_months,
                        summary=experience_summary,
                    )

                    logger.info(
                        f"Experience verification: {actual_months} months (required: {min_experience_months})"
                    )

                except Exception as e:
                    logger.warning(f"Experience calculation failed: {e}")
                    # Continue without experience verification

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Build response
        response_data = {
            "resume_id": request.resume_id,
            "vacancy_title": vacancy_title,
            "match_percentage": match_percentage,
            "required_skills_match": [
                m.model_dump() for m in required_skills_matches
            ],
            "additional_skills_match": [
                m.model_dump() for m in additional_skills_matches
            ],
            "experience_verification": (
                experience_verification.model_dump() if experience_verification else None
            ),
            "processing_time_ms": round(processing_time_ms, 2),
        }

        logger.info(
            f"Matching completed for resume_id {request.resume_id} in {processing_time_ms:.2f}ms"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching resume to vacancy: {e}", exc_info=True)
        error_msg = get_error_message("parsing_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.post(
    "/feedback",
    response_model=MatchFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Matching"],
)
async def submit_match_feedback(http_request: Request, request: MatchFeedbackRequest) -> JSONResponse:
    """
    Submit feedback on a skill match result.

    This endpoint allows recruiters to provide feedback on the AI's skill matching
    decisions, recording whether matches were correct and any corrections needed.
    This feedback is used to improve future matching accuracy through ML retraining.

    Args:
        http_request: FastAPI request object (for Accept-Language header)
        request: Feedback request with match details and recruiter corrections

    Returns:
        JSON response with created feedback entry

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "match_id": "match123",
        ...     "skill": "React",
        ...     "was_correct": True,
        ...     "recruiter_correction": None
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/matching/feedback",
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "feedback-id",
            "match_id": "match123",
            "skill": "React",
            "was_correct": True,
            "recruiter_correction": None,
            "feedback_source": "matching_api",
            "processed": False,
            "created_at": "2024-01-25T00:00:00Z"
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(http_request)

    try:
        logger.info(
            f"Submitting feedback for match_id: {request.match_id}, "
            f"skill: {request.skill}, was_correct: {request.was_correct}"
        )

        # Validate confidence score if provided
        if request.confidence_score is not None and not (
            0 <= request.confidence_score <= 1
        ):
            error_msg = get_error_message("value_out_of_range", locale, field="confidence_score")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        feedback_response = {
            "id": "placeholder-feedback-id",
            "match_id": request.match_id,
            "skill": request.skill,
            "was_correct": request.was_correct,
            "recruiter_correction": request.recruiter_correction,
            "feedback_source": "matching_api",
            "processed": False,
            "created_at": "2024-01-25T00:00:00Z",
        }

        logger.info(f"Created feedback entry for match_id: {request.match_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=feedback_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting match feedback: {e}", exc_info=True)
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
