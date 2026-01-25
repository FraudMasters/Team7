"""
Resume comparison endpoints for multi-resume analysis and ranking.

This module provides endpoints for creating, retrieving, and managing
multi-resume comparison views with ranking, filtering, and sorting capabilities.
"""
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
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

logger = logging.getLogger(__name__)

router = APIRouter()

# Directory where uploaded resumes are stored
UPLOAD_DIR = Path("data/uploads")

# Path to skill synonyms file
SYNONYMS_FILE = Path(__file__).parent.parent / "models" / "skill_synonyms.json"


def compare_multiple_resumes(
    resume_ids: List[str],
    vacancy_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compare multiple resumes against a job vacancy and aggregate results.

    This function performs intelligent matching between each resume's skills
    and the job vacancy requirements, handling synonyms (e.g., PostgreSQL ≈ SQL)
    and providing aggregated results with ranking by match percentage.

    Features:
    - Skill synonym matching (PostgreSQL matches SQL requirement)
    - Match percentage calculation for each resume
    - Experience verification for each resume
    - Automatic ranking by match percentage (descending)
    - Processing time tracking

    Args:
        resume_ids: List of resume IDs to compare (2-5 resumes)
        vacancy_data: Job vacancy data with required skills and experience

    Returns:
        Dictionary containing:
        - vacancy_title: Title of the job vacancy
        - comparison_results: List of match results for each resume, ranked
        - total_resumes: Number of resumes compared
        - processing_time_ms: Total processing time

    Raises:
        HTTPException(404): If any resume file is not found
        HTTPException(422): If text extraction fails for any resume
        HTTPException(500): If matching processing fails

    Example:
        >>> vacancy = {
        ...     "title": "Java Developer",
        ...     "required_skills": ["Java", "Spring", "SQL"],
        ...     "min_experience_months": 36
        ... }
        >>> results = compare_multiple_resumes(
        ...     ["resume1", "resume2", "resume3"],
        ...     vacancy
        ... )
        >>> results["comparison_results"][0]["rank"]
        1
    """
    start_time = time.time()

    try:
        logger.info(
            f"Starting comparison for {len(resume_ids)} resumes against vacancy: "
            f"{vacancy_data.get('title', 'Unknown')}"
        )

        # Validate resume count
        if len(resume_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least 2 resumes must be provided for comparison",
            )
        if len(resume_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Maximum 5 resumes can be compared at once",
            )

        # Get vacancy data
        vacancy_title = vacancy_data.get(
            "title", vacancy_data.get("position", "Unknown Position")
        )
        required_skills = vacancy_data.get("required_skills", [])
        additional_skills = vacancy_data.get(
            "additional_requirements", vacancy_data.get("additional_skills", [])
        )
        min_experience_months = vacancy_data.get("min_experience_months", None)

        # If required_skills is a string list, use it directly
        if isinstance(required_skills, str):
            required_skills = [required_skills]

        # Process each resume
        comparison_results = []

        for resume_id in resume_ids:
            try:
                logger.info(f"Processing resume_id: {resume_id}")

                # Step 1: Find the resume file
                for ext in [".pdf", ".docx", ".PDF", ".DOCX"]:
                    file_path = UPLOAD_DIR / f"{resume_id}{ext}"
                    if file_path.exists():
                        break
                else:
                    logger.warning(f"Resume file not found: {resume_id}")
                    # Add a placeholder result for missing resumes
                    comparison_results.append({
                        "resume_id": resume_id,
                        "vacancy_title": vacancy_title,
                        "match_percentage": 0.0,
                        "required_skills_match": [],
                        "additional_skills_match": [],
                        "experience_verification": None,
                        "processing_time_ms": 0.0,
                        "error": "Resume file not found",
                    })
                    continue

                # Step 2: Extract text from file
                try:
                    from extract import extract_text_from_pdf, extract_text_from_docx

                    file_ext = file_path.suffix.lower()
                    if file_ext == ".pdf":
                        result = extract_text_from_pdf(file_path)
                    elif file_ext == ".docx":
                        result = extract_text_from_docx(file_path)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail=f"Unsupported file type: {file_ext}",
                        )

                    if result.get("error"):
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Text extraction failed: {result['error']}",
                        )

                    resume_text = result.get("text", "")
                    if not resume_text or len(resume_text.strip()) < 10:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Extracted text is too short or empty",
                        )

                    logger.info(f"Extracted {len(resume_text)} characters from resume")

                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Error extracting text: {e}", exc_info=True)
                    comparison_results.append({
                        "resume_id": resume_id,
                        "vacancy_title": vacancy_title,
                        "match_percentage": 0.0,
                        "required_skills_match": [],
                        "additional_skills_match": [],
                        "experience_verification": None,
                        "processing_time_ms": 0.0,
                        "error": f"Text extraction failed: {str(e)}",
                    })
                    continue

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
                synonyms_map = enhanced_matcher.load_synonyms()
                logger.info(f"Initialized enhanced skill matcher with {len(synonyms_map)} synonym mappings")

                # Step 6: Match required skills
                required_skills_matches = []
                for skill in required_skills:
                    match_result = enhanced_matcher.match_with_context(
                        resume_skills=resume_skills,
                        required_skill=skill,
                        context=vacancy_title.lower(),
                        use_fuzzy=True
                    )

                    if match_result["matched"]:
                        required_skills_matches.append({
                            "skill": skill,
                            "status": "matched",
                            "matched_as": match_result["matched_as"],
                            "highlight": "green",
                            "confidence": round(match_result["confidence"], 2),
                            "match_type": match_result["match_type"]
                        })
                    else:
                        required_skills_matches.append({
                            "skill": skill,
                            "status": "missing",
                            "matched_as": None,
                            "highlight": "red",
                            "confidence": 0.0,
                            "match_type": "none"
                        })

                # Step 7: Match additional/preferred skills
                additional_skills_matches = []
                for skill in additional_skills:
                    match_result = enhanced_matcher.match_with_context(
                        resume_skills=resume_skills,
                        required_skill=skill,
                        context=vacancy_title.lower(),
                        use_fuzzy=True
                    )

                    if match_result["matched"]:
                        additional_skills_matches.append({
                            "skill": skill,
                            "status": "matched",
                            "matched_as": match_result["matched_as"],
                            "highlight": "green",
                            "confidence": round(match_result["confidence"], 2),
                            "match_type": match_result["match_type"]
                        })
                    else:
                        additional_skills_matches.append({
                            "skill": skill,
                            "status": "missing",
                            "matched_as": None,
                            "highlight": "red",
                            "confidence": 0.0,
                            "match_type": "none"
                        })

                # Step 8: Calculate match percentage
                total_required = len(required_skills)
                matched_required = sum(
                    1 for m in required_skills_matches if m["status"] == "matched"
                )
                match_percentage = (
                    round((matched_required / total_required * 100), 2) if total_required > 0 else 0.0
                )

                logger.info(
                    f"Matched {matched_required}/{total_required} required skills ({match_percentage}%)"
                )

                # Step 9: Verify experience (if vacancy has experience requirement)
                experience_verification = None
                if min_experience_months and min_experience_months > 0:
                    logger.info(f"Verifying experience requirement: {min_experience_months} months")

                    primary_skill = required_skills[0] if required_skills else None

                    if primary_skill:
                        try:
                            skill_exp_result = calculate_skill_experience(
                                resume_text, primary_skill, language=language
                            )
                            actual_months = skill_exp_result.get("total_months", 0)
                            experience_summary = format_experience_summary(actual_months)

                            experience_verification = {
                                "required_months": min_experience_months,
                                "actual_months": actual_months,
                                "meets_requirement": actual_months >= min_experience_months,
                                "summary": experience_summary,
                            }

                            logger.info(
                                f"Experience verification: {actual_months} months (required: {min_experience_months})"
                            )

                        except Exception as e:
                            logger.warning(f"Experience calculation failed: {e}")
                            # Continue without experience verification

                # Build result for this resume
                resume_result = {
                    "resume_id": resume_id,
                    "vacancy_title": vacancy_title,
                    "match_percentage": match_percentage,
                    "required_skills_match": required_skills_matches,
                    "additional_skills_match": additional_skills_matches,
                    "experience_verification": experience_verification,
                    "processing_time_ms": 0.0,  # Will be updated after total time calculation
                }

                comparison_results.append(resume_result)

            except Exception as e:
                logger.error(f"Error processing resume {resume_id}: {e}", exc_info=True)
                comparison_results.append({
                    "resume_id": resume_id,
                    "vacancy_title": vacancy_title,
                    "match_percentage": 0.0,
                    "required_skills_match": [],
                    "additional_skills_match": [],
                    "experience_verification": None,
                    "processing_time_ms": 0.0,
                    "error": str(e),
                })

        # Step 10: Sort results by match percentage (descending)
        comparison_results.sort(key=lambda x: x.get("match_percentage", 0), reverse=True)

        # Assign ranks
        for idx, result in enumerate(comparison_results, start=1):
            result["rank"] = idx

        # Calculate total processing time
        total_processing_time_ms = (time.time() - start_time) * 1000

        # Distribute processing time across resumes (approximate)
        if comparison_results:
            time_per_resume = total_processing_time_ms / len(comparison_results)
            for result in comparison_results:
                if "error" not in result:
                    result["processing_time_ms"] = round(time_per_resume, 2)

        logger.info(
            f"Comparison completed for {len(resume_ids)} resumes in {total_processing_time_ms:.2f}ms"
        )

        return {
            "vacancy_title": vacancy_title,
            "comparison_results": comparison_results,
            "total_resumes": len(resume_ids),
            "processing_time_ms": round(total_processing_time_ms, 2),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing multiple resumes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare resumes: {str(e)}",
        ) from e


class ComparisonCreate(BaseModel):
    """Request model for creating a comparison view."""

    vacancy_id: str = Field(..., description="ID of the job vacancy to compare against")
    resume_ids: List[str] = Field(..., description="List of resume IDs to compare (2-5 resumes)", min_length=2, max_length=5)
    name: Optional[str] = Field(None, description="Optional name for the comparison view")
    filters: Optional[dict] = Field(None, description="Filter settings (match range, sort field, etc.)")
    created_by: Optional[str] = Field(None, description="User identifier who created the comparison")
    shared_with: Optional[List[str]] = Field(None, description="List of user IDs/emails to share with")


class ComparisonUpdate(BaseModel):
    """Request model for updating a comparison view."""

    name: Optional[str] = Field(None, description="Updated name for the comparison view")
    filters: Optional[dict] = Field(None, description="Updated filter settings")
    shared_with: Optional[List[str]] = Field(None, description="Updated list of users to share with")


class ComparisonResponse(BaseModel):
    """Response model for a comparison view."""

    id: str = Field(..., description="Unique identifier for the comparison")
    vacancy_id: str = Field(..., description="ID of the job vacancy")
    resume_ids: List[str] = Field(..., description="List of resume IDs being compared")
    name: Optional[str] = Field(None, description="Name of the comparison view")
    filters: Optional[dict] = Field(None, description="Filter settings")
    created_by: Optional[str] = Field(None, description="User who created the comparison")
    shared_with: Optional[List[str]] = Field(None, description="List of users shared with")
    comparison_results: Optional[List[dict]] = Field(None, description="Match results for each resume")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ComparisonListResponse(BaseModel):
    """Response model for listing comparison views."""

    comparisons: List[ComparisonResponse] = Field(..., description="List of comparison views")
    total_count: int = Field(..., description="Total number of comparison views")


@router.post(
    "/",
    response_model=ComparisonResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Comparisons"],
)
async def create_comparison(request: ComparisonCreate) -> JSONResponse:
    """
    Create a new resume comparison view.

    This endpoint creates a new comparison view for analyzing multiple resumes
    side-by-side against a job vacancy. The comparison can be saved with filters,
    shared with team members, and retrieved later.

    Args:
        request: Create request with vacancy_id, resume_ids, and optional settings

    Returns:
        JSON response with created comparison view details

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "vacancy_id": "vacancy-123",
        ...     "resume_ids": ["resume1", "resume2", "resume3"],
        ...     "name": "Senior Developer Candidates"
        ... }
        >>> response = requests.post("http://localhost:8000/api/comparisons/", json=data)
        >>> response.json()
        {
            "id": "comp-123",
            "vacancy_id": "vacancy-123",
            "resume_ids": ["resume1", "resume2", "resume3"],
            "name": "Senior Developer Candidates",
            "filters": None,
            "created_by": None,
            "shared_with": None,
            "comparison_results": None,
            "created_at": "2024-01-25T00:00:00Z",
            "updated_at": "2024-01-25T00:00:00Z"
        }
    """
    try:
        logger.info(
            f"Creating comparison for vacancy_id: {request.vacancy_id} "
            f"with {len(request.resume_ids)} resumes"
        )

        # Validate resume_ids count
        if len(request.resume_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least 2 resumes must be provided for comparison",
            )
        if len(request.resume_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Maximum 5 resumes can be compared at once",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        comparison_response = {
            "id": "placeholder-comparison-id",
            "vacancy_id": request.vacancy_id,
            "resume_ids": request.resume_ids,
            "name": request.name,
            "filters": request.filters,
            "created_by": request.created_by,
            "shared_with": request.shared_with,
            "comparison_results": None,
            "created_at": "2024-01-25T00:00:00Z",
            "updated_at": "2024-01-25T00:00:00Z",
        }

        logger.info(
            f"Created comparison for vacancy {request.vacancy_id} "
            f"with {len(request.resume_ids)} resumes"
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=comparison_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comparison: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comparison: {str(e)}",
        ) from e


@router.get("/", tags=["Comparisons"])
async def list_comparisons(
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    created_by: Optional[str] = Query(None, description="Filter by creator user ID"),
    min_match_percentage: Optional[float] = Query(None, description="Filter by minimum match percentage", ge=0, le=100),
    max_match_percentage: Optional[float] = Query(None, description="Filter by maximum match percentage", ge=0, le=100),
    sort_by: Optional[str] = Query("created_at", description="Sort field (created_at, match_percentage, name)"),
    order: Optional[str] = Query("desc", description="Sort order (asc or desc)"),
    limit: int = Query(50, description="Maximum number of comparisons to return", ge=1, le=100),
    offset: int = Query(0, description="Number of comparisons to skip", ge=0),
) -> JSONResponse:
    """
    List resume comparison views with optional filters and sorting.

    Args:
        vacancy_id: Optional vacancy ID filter
        created_by: Optional creator user ID filter
        min_match_percentage: Optional minimum match percentage filter (0-100)
        max_match_percentage: Optional maximum match percentage filter (0-100)
        sort_by: Sort field - created_at, match_percentage, or name (default: created_at)
        order: Sort order - asc or desc (default: desc)
        limit: Maximum number of results to return (default: 50, max: 100)
        offset: Number of results to skip (default: 0)

    Returns:
        JSON response with list of comparison views

    Raises:
        HTTPException(422): If sort_by or order parameters are invalid
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> # List comparisons for a specific vacancy
        >>> response = requests.get("http://localhost:8000/api/comparisons/?vacancy_id=vac-123")
        >>> # Sort by match percentage descending
        >>> response = requests.get("http://localhost:8000/api/comparisons/?sort_by=match_percentage&order=desc")
        >>> # Filter by match percentage range
        >>> response = requests.get("http://localhost:8000/api/comparisons/?min_match_percentage=50&max_match_percentage=90")
        >>> response.json()
    """
    try:
        # Validate sort_by parameter
        valid_sort_fields = ["created_at", "match_percentage", "name", "updated_at"]
        if sort_by and sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}",
            )

        # Validate order parameter
        valid_orders = ["asc", "desc"]
        if order and order not in valid_orders:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid order field. Must be one of: {', '.join(valid_orders)}",
            )

        # Validate match percentage range
        if min_match_percentage is not None and max_match_percentage is not None:
            if min_match_percentage > max_match_percentage:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="min_match_percentage must be less than or equal to max_match_percentage",
                )

        logger.info(
            f"Listing comparisons with filters - vacancy_id: {vacancy_id}, "
            f"created_by: {created_by}, min_match_percentage: {min_match_percentage}, "
            f"max_match_percentage: {max_match_percentage}, sort_by: {sort_by}, "
            f"order: {order}, limit: {limit}, offset: {offset}"
        )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        # When database is integrated, filters and sorting will be applied at the query level:
        # - Build WHERE clauses based on filter parameters
        # - Apply ORDER BY with sort_by and order
        # - Use LIMIT and OFFSET for pagination
        response_data = {
            "comparisons": [],
            "total_count": 0,
            "filters_applied": {
                "vacancy_id": vacancy_id,
                "created_by": created_by,
                "min_match_percentage": min_match_percentage,
                "max_match_percentage": max_match_percentage,
                "sort_by": sort_by,
                "order": order,
            },
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing comparisons: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list comparisons: {str(e)}",
        ) from e


@router.get("/{comparison_id}", tags=["Comparisons"])
async def get_comparison(comparison_id: str) -> JSONResponse:
    """
    Get a specific comparison view by ID.

    Args:
        comparison_id: Unique identifier of the comparison view

    Returns:
        JSON response with comparison view details

    Raises:
        HTTPException(404): If comparison view is not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/comparisons/123e4567-e89b-12d3-a456-426614174000"
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Getting comparison: {comparison_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": comparison_id,
                "vacancy_id": "vacancy-123",
                "resume_ids": ["resume1", "resume2"],
                "name": "Sample Comparison",
                "filters": None,
                "created_by": "user-123",
                "shared_with": None,
                "comparison_results": None,
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": "2024-01-25T00:00:00Z",
            },
        )

    except Exception as e:
        logger.error(f"Error getting comparison: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comparison: {str(e)}",
        ) from e


@router.put("/{comparison_id}", tags=["Comparisons"])
async def update_comparison(
    comparison_id: str, request: ComparisonUpdate
) -> JSONResponse:
    """
    Update a comparison view.

    Args:
        comparison_id: Unique identifier of the comparison view
        request: Update request with fields to modify

    Returns:
        JSON response with updated comparison view

    Raises:
        HTTPException(404): If comparison view is not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"name": "Updated Comparison Name"}
        >>> response = requests.put(
        ...     "http://localhost:8000/api/comparisons/123",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Updating comparison: {comparison_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": comparison_id,
                "vacancy_id": "vacancy-123",
                "resume_ids": ["resume1", "resume2"],
                "name": request.name if request.name is not None else "Sample Comparison",
                "filters": request.filters,
                "created_by": "user-123",
                "shared_with": request.shared_with,
                "comparison_results": None,
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": "2024-01-25T00:00:00Z",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating comparison: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update comparison: {str(e)}",
        ) from e


@router.delete("/{comparison_id}", tags=["Comparisons"])
async def delete_comparison(comparison_id: str) -> JSONResponse:
    """
    Delete a comparison view.

    Args:
        comparison_id: Unique identifier of the comparison view

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If comparison view is not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/comparisons/123")
        >>> response.json()
        {"message": "Comparison deleted successfully"}
    """
    try:
        logger.info(f"Deleting comparison: {comparison_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Comparison {comparison_id} deleted successfully"},
        )

    except Exception as e:
        logger.error(f"Error deleting comparison: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete comparison: {str(e)}",
        ) from e
