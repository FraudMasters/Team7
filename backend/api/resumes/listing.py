"""
Resume listing endpoints.

This module provides endpoints for listing resumes with pagination,
retrieving basic resume information, and displaying pre-analyzed skills.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.resume import Resume

logger = logging.getLogger(__name__)

router = APIRouter()


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


class ResumeListItem(BaseModel):
    """Response model for a single resume in a list."""

    id: str = Field(..., description="Unique identifier")
    filename: str = Field(..., description="Filename")
    status: str = Field(..., description="Processing status")
    created_at: str = Field(..., description="Creation timestamp")
    language: Optional[str] = Field(None, description="Detected language")


@router.get(
    "/",
    response_model=list[ResumeListItem],
    tags=["Resumes"],
)
async def list_resumes(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List all resumes in the database with their pre-analyzed skills.

    Returns a paginated list of all resumes with their basic information.

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of resumes

    Example:
        >>> response = requests.get("http://localhost:8000/api/resumes/?limit=10")
        >>> resumes = response.json()
    """
    try:
        from models.resume_analysis import ResumeAnalysis

        # Query resumes with their analysis
        query = select(Resume).order_by(Resume.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        resumes = result.scalars().all()

        # Convert to response format
        resumes_list = []
        for resume in resumes:
            skills = []

            # Try to get skills from saved analysis
            analysis = await db.execute(
                select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume.id)
            )
            analysis_obj = analysis.scalar_one_or_none()

            if analysis_obj and analysis_obj.skills:
                skills = analysis_obj.skills[:30]  # Use saved skills
            elif resume.raw_text:
                # Fallback: extract from raw_text if no analysis saved
                try:
                    from analyzers.hf_skill_extractor import extract_resume_skills
                    result = extract_resume_skills(
                        resume.raw_text[:5000],
                        method='pattern',
                        top_n=30
                    )
                    skills = result.get("skills") or []
                except Exception as e:
                    logger.warning(f"Failed to extract skills from raw_text for resume {resume.id}: {e}")

            resumes_list.append({
                "id": str(resume.id),
                "filename": resume.filename,
                "status": resume.status.value.lower(),  # Return lowercase for frontend
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
                "language": resume.language,
                "technical_skills": skills,
            })

        return JSONResponse(
            status_code=200,
            content=resumes_list,
        )

    except Exception as e:
        logger.error(f"Error listing resumes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list resumes: {str(e)}",
        ) from e
