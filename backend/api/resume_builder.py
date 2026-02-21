"""
Resume builder API endpoints.

This module provides REST API endpoints for the resume builder feature, including:
- CRUD operations for creating and managing resumes
- AI-powered improvement suggestions
- ATS optimization scoring
- Document export (PDF, DOCX)
- Skill gap analysis against target jobs
- Version history management

These endpoints integrate with the ResumeBuilderService for business logic.
"""
import io
import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models.built_resume import BuiltResume
from models.resume_template import ResumeTemplate
from services.resume_builder_service import ResumeBuilderService, get_resume_builder_service
from services.pdf_generator import get_pdf_generator, PDFGenerationOptions
from services.docx_generator import get_docx_generator, DOCXGenerationOptions
from schemas.resume_builder import (
    BuiltResumeCreate,
    BuiltResumeUpdate,
    BuiltResumeResponse,
    BuiltResumeListResponse,
    BuiltResumeSummary,
    BuiltResumeSummaryListResponse,
    AISuggestionsResponse,
    ApplySuggestionRequest,
    ATSScoreResponse,
    SkillGapAnalysisResponse,
    ExportRequest,
    ExportResponse,
    ResumeContent,
    ResumeTemplateSummary,
    ResumeTemplateListResponse,
    ResumeVersionHistoryResponse,
)
from i18n.backend_translations import get_error_message, get_success_message

logger = logging.getLogger(__name__)
settings = get_settings()

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


def _get_user_context(request: Request) -> tuple[str, str]:
    """
    Extract user_id and organization_id from request context.

    In production, this would extract from JWT token or session.
    For now, uses headers for testing purposes.

    Args:
        request: FastAPI request object

    Returns:
        Tuple of (user_id, organization_id)
    """
    # In production, decode JWT token from Authorization header
    # For development/testing, use X-User-Id and X-Organization-Id headers
    user_id = request.headers.get("X-User-Id", "test-user")
    organization_id = request.headers.get("X-Organization-Id", "test-org")
    return user_id, organization_id


def _resume_to_response(resume: BuiltResume) -> Dict[str, Any]:
    """
    Convert BuiltResume model to response dictionary.

    Args:
        resume: BuiltResume model instance

    Returns:
        Dictionary representation for API response
    """
    content = resume.content or {}
    last_suggestions = None
    if resume.last_ai_suggestions:
        try:
            last_suggestions = AISuggestionsResponse(**resume.last_ai_suggestions)
        except Exception:
            last_suggestions = None

    return {
        "id": str(resume.id),
        "user_id": resume.user_id,
        "organization_id": resume.organization_id,
        "template_id": str(resume.template_id) if resume.template_id else None,
        "title": resume.title,
        "content": content,
        "target_job_id": str(resume.target_job_id) if resume.target_job_id else None,
        "ats_score": resume.ats_score,
        "version": resume.version,
        "is_draft": resume.is_draft,
        "last_ai_suggestions": last_suggestions.model_dump() if last_suggestions else None,
        "created_at": resume.created_at.isoformat() if resume.created_at else None,
        "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
    }


def _resume_to_summary(resume: BuiltResume) -> Dict[str, Any]:
    """
    Convert BuiltResume model to summary dictionary.

    Args:
        resume: BuiltResume model instance

    Returns:
        Dictionary representation for list view
    """
    return {
        "id": str(resume.id),
        "title": resume.title,
        "ats_score": resume.ats_score,
        "version": resume.version,
        "is_draft": resume.is_draft,
        "created_at": resume.created_at.isoformat() if resume.created_at else None,
        "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
    }


def _render_resume_to_html(content: Dict[str, Any]) -> str:
    """
    Render resume content dictionary to HTML for PDF generation.

    Args:
        content: Resume content dictionary with sections

    Returns:
        HTML string for PDF generation
    """
    html_parts = ['<!DOCTYPE html><html><head><meta charset="UTF-8">']
    html_parts.append('<style>')
    html_parts.append('body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }')
    html_parts.append('h1 { color: #2c3e50; margin-bottom: 5px; }')
    html_parts.append('h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 20px; }')
    html_parts.append('h3 { color: #34495e; margin-bottom: 3px; }')
    html_parts.append('.contact-info { color: #7f8c8d; margin-bottom: 15px; }')
    html_parts.append('.contact-info a { color: #3498db; text-decoration: none; }')
    html_parts.append('.section { margin-bottom: 20px; }')
    html_parts.append('.entry { margin-bottom: 15px; }')
    html_parts.append('.entry-header { display: flex; justify-content: space-between; }')
    html_parts.append('.entry-title { font-weight: bold; }')
    html_parts.append('.entry-date { color: #7f8c8d; }')
    html_parts.append('.entry-company { color: #34495e; font-style: italic; }')
    html_parts.append('.entry-description { margin-top: 5px; }')
    html_parts.append('.skills-container { display: flex; flex-wrap: wrap; gap: 8px; }')
    html_parts.append('.skill-tag { background: #ecf0f1; padding: 4px 10px; border-radius: 4px; font-size: 14px; }')
    html_parts.append('.skill-expert { background: #27ae60; color: white; }')
    html_parts.append('.skill-advanced { background: #3498db; color: white; }')
    html_parts.append('.summary { font-style: italic; color: #34495e; }')
    html_parts.append('</style></head><body>')

    # Personal Info
    personal_info = content.get("personal_info", {})
    if personal_info:
        full_name = personal_info.get("full_name", "")
        if full_name:
            html_parts.append(f'<h1>{full_name}</h1>')

        # Contact info line
        contact_parts = []
        if personal_info.get("email"):
            contact_parts.append(f'<a href="mailto:{personal_info["email"]}">{personal_info["email"]}</a>')
        if personal_info.get("phone"):
            contact_parts.append(personal_info["phone"])
        if personal_info.get("location"):
            contact_parts.append(personal_info["location"])

        if contact_parts:
            html_parts.append(f'<div class="contact-info">{" | ".join(contact_parts)}</div>')

        # Social links
        social_links = personal_info.get("social_links", {})
        if social_links:
            link_parts = []
            for platform, url in social_links.items():
                if url:
                    link_parts.append(f'<a href="{url}">{platform.title()}</a>')
            if link_parts:
                html_parts.append(f'<div class="contact-info">{" | ".join(link_parts)}</div>')

    # Professional Summary
    summary = content.get("professional_summary", "")
    if summary:
        html_parts.append('<div class="section">')
        html_parts.append('<h2>Professional Summary</h2>')
        html_parts.append(f'<p class="summary">{summary}</p>')
        html_parts.append('</div>')

    # Work Experience
    work_experience = content.get("work_experience", [])
    if work_experience:
        html_parts.append('<div class="section">')
        html_parts.append('<h2>Work Experience</h2>')
        for entry in work_experience:
            html_parts.append('<div class="entry">')
            html_parts.append('<div class="entry-header">')
            html_parts.append(f'<span class="entry-title">{entry.get("position", "")}</span>')
            if entry.get("start_date"):
                date_str = entry.get("start_date", "")
                if entry.get("end_date"):
                    date_str += f' - {entry["end_date"]}'
                elif entry.get("is_current"):
                    date_str += ' - Present'
                html_parts.append(f'<span class="entry-date">{date_str}</span>')
            html_parts.append('</div>')
            if entry.get("company"):
                html_parts.append(f'<div class="entry-company">{entry["company"]}</div>')
            if entry.get("description"):
                html_parts.append(f'<p class="entry-description">{entry["description"]}</p>')
            highlights = entry.get("highlights", [])
            if highlights:
                html_parts.append('<ul>')
                for highlight in highlights:
                    html_parts.append(f'<li>{highlight}</li>')
                html_parts.append('</ul>')
            html_parts.append('</div>')
        html_parts.append('</div>')

    # Education
    education = content.get("education", [])
    if education:
        html_parts.append('<div class="section">')
        html_parts.append('<h2>Education</h2>')
        for entry in education:
            html_parts.append('<div class="entry">')
            html_parts.append('<div class="entry-header">')
            degree_parts = []
            if entry.get("degree"):
                degree_parts.append(entry["degree"])
            if entry.get("field_of_study"):
                degree_parts.append(f'in {entry["field_of_study"]}')
            html_parts.append(f'<span class="entry-title">{" ".join(degree_parts)}</span>')
            if entry.get("start_date"):
                date_str = entry.get("start_date", "")
                if entry.get("end_date"):
                    date_str += f' - {entry["end_date"]}'
                html_parts.append(f'<span class="entry-date">{date_str}</span>')
            html_parts.append('</div>')
            if entry.get("institution"):
                html_parts.append(f'<div class="entry-company">{entry["institution"]}</div>')
            if entry.get("gpa"):
                html_parts.append(f'<div>GPA: {entry["gpa"]}</div>')
            html_parts.append('</div>')
        html_parts.append('</div>')

    # Skills
    skills = content.get("skills", [])
    if skills:
        html_parts.append('<div class="section">')
        html_parts.append('<h2>Skills</h2>')
        html_parts.append('<div class="skills-container">')
        for skill in skills:
            skill_name = skill.get("name", "")
            proficiency = skill.get("proficiency_level", "").lower()
            css_class = "skill-tag"
            if proficiency == "expert":
                css_class += " skill-expert"
            elif proficiency == "advanced":
                css_class += " skill-advanced"
            html_parts.append(f'<span class="{css_class}">{skill_name}</span>')
        html_parts.append('</div>')
        html_parts.append('</div>')

    # Certifications
    certifications = content.get("certifications", [])
    if certifications:
        html_parts.append('<div class="section">')
        html_parts.append('<h2>Certifications</h2>')
        for entry in certifications:
            html_parts.append('<div class="entry">')
            html_parts.append(f'<span class="entry-title">{entry.get("name", "")}</span>')
            if entry.get("issuer"):
                html_parts.append(f' - <span class="entry-company">{entry["issuer"]}</span>')
            if entry.get("issue_date"):
                html_parts.append(f' <span class="entry-date">({entry["issue_date"]})</span>')
            html_parts.append('</div>')
        html_parts.append('</div>')

    # Languages
    languages = content.get("languages", [])
    if languages:
        html_parts.append('<div class="section">')
        html_parts.append('<h2>Languages</h2>')
        html_parts.append('<div class="skills-container">')
        for lang in languages:
            lang_name = lang.get("name", "")
            proficiency = lang.get("proficiency", "")
            html_parts.append(f'<span class="skill-tag">{lang_name}')
            if proficiency:
                html_parts.append(f' ({proficiency})')
            html_parts.append('</span>')
        html_parts.append('</div>')
        html_parts.append('</div>')

    # Projects
    projects = content.get("projects", [])
    if projects:
        html_parts.append('<div class="section">')
        html_parts.append('<h2>Projects</h2>')
        for entry in projects:
            html_parts.append('<div class="entry">')
            html_parts.append(f'<span class="entry-title">{entry.get("name", "")}</span>')
            if entry.get("url"):
                html_parts.append(f' - <a href="{entry["url"]}">{entry["url"]}</a>')
            if entry.get("description"):
                html_parts.append(f'<p class="entry-description">{entry["description"]}</p>')
            technologies = entry.get("technologies", [])
            if technologies:
                html_parts.append('<div class="skills-container">')
                for tech in technologies:
                    html_parts.append(f'<span class="skill-tag">{tech}</span>')
                html_parts.append('</div>')
            html_parts.append('</div>')
        html_parts.append('</div>')

    html_parts.append('</body></html>')
    return ''.join(html_parts)


# =============================================================================
# CRUD Endpoints
# =============================================================================


@router.post(
    "/",
    response_model=BuiltResumeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Resume Builder"],
)
async def create_resume(
    request: Request,
    resume_data: BuiltResumeCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new resume.

    This endpoint creates a new resume from scratch using the resume builder.
    Optionally, a template can be specified to pre-populate styling and sections.

    Args:
        request: FastAPI request object (for user context)
        resume_data: Resume creation data
        db: Database session

    Returns:
        JSON response with created resume details

    Raises:
        HTTPException(422): If validation fails
        HTTPException(404): If template_id is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "title": "Software Engineer Resume",
        ...     "template_id": "abc123",
        ...     "content": {
        ...         "personal_info": {"full_name": "John Doe"},
        ...         "skills": [{"name": "Python"}]
        ...     }
        ... }
        >>> response = requests.post("/api/resume-builder/", json=data)
        >>> response.json()
        {
            "id": "...",
            "title": "Software Engineer Resume",
            "version": 1,
            ...
        }
    """
    locale = _extract_locale(request)
    user_id, organization_id = _get_user_context(request)

    try:
        logger.info(f"Creating resume for user_id={user_id}, title={resume_data.title}")

        service = get_resume_builder_service(db)
        resume = await service.create_resume(
            user_id=user_id,
            organization_id=organization_id,
            resume_data=resume_data,
        )

        response_data = _resume_to_response(resume)
        success_msg = get_success_message("resume_created", locale)

        logger.info(f"Created resume id={resume.id}, version={resume.version}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except ValueError as e:
        logger.warning(f"Validation error creating resume: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except SQLAlchemyError as e:
        logger.error(f"Database error creating resume: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error creating resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create resume: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=BuiltResumeSummaryListResponse,
    tags=["Resume Builder"],
)
async def list_resumes(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_drafts: bool = Query(True, description="Include draft resumes"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List resumes for the current user.

    Returns a paginated list of resumes created by the user with summary information.

    Args:
        request: FastAPI request object (for user context)
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        include_drafts: Whether to include draft resumes
        db: Database session

    Returns:
        JSON response with paginated list of resume summaries

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/resume-builder/?page=1&page_size=10")
        >>> response.json()
        {
            "items": [...],
            "total": 5,
            "page": 1,
            "page_size": 10,
            "total_pages": 1
        }
    """
    locale = _extract_locale(request)
    user_id, organization_id = _get_user_context(request)

    try:
        logger.info(f"Listing resumes for user_id={user_id}, page={page}")

        service = get_resume_builder_service(db)
        resumes, total = await service.list_resumes(
            user_id=user_id,
            organization_id=organization_id,
            page=page,
            page_size=page_size,
            include_drafts=include_drafts,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        response_data = {
            "items": [_resume_to_summary(r) for r in resumes],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

        logger.info(f"Listed {len(resumes)} resumes for user_id={user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error listing resumes: {e}", exc_info=True)
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error listing resumes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list resumes: {str(e)}",
        ) from e


@router.get(
    "/{resume_id}",
    response_model=BuiltResumeResponse,
    tags=["Resume Builder"],
)
async def get_resume(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific resume by ID.

    Retrieves the full resume content including all sections and metadata.

    Args:
        request: FastAPI request object (for user context)
        resume_id: UUID of the resume
        db: Database session

    Returns:
        JSON response with full resume details

    Raises:
        HTTPException(404): If resume not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/resume-builder/abc123")
        >>> response.json()
        {
            "id": "abc123",
            "title": "Software Engineer Resume",
            "content": {...},
            "version": 3,
            ...
        }
    """
    locale = _extract_locale(request)
    user_id, _ = _get_user_context(request)

    try:
        logger.info(f"Getting resume id={resume_id}")

        # Validate UUID format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_id", locale, id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        service = get_resume_builder_service(db)
        resume = await service.get_resume(resume_uuid, user_id)

        if resume is None:
            error_msg = get_error_message("resume_not_found", locale, resume_id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        response_data = _resume_to_response(resume)

        logger.info(f"Retrieved resume id={resume_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error getting resume: {e}", exc_info=True)
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error getting resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resume: {str(e)}",
        ) from e


@router.put(
    "/{resume_id}",
    response_model=BuiltResumeResponse,
    tags=["Resume Builder"],
)
async def update_resume(
    request: Request,
    resume_id: str,
    update_data: BuiltResumeUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a resume.

    Updates an existing resume with new content or metadata.
    Version is automatically incremented on content changes.

    Args:
        request: FastAPI request object (for user context)
        resume_id: UUID of the resume
        update_data: Update data
        db: Database session

    Returns:
        JSON response with updated resume details

    Raises:
        HTTPException(404): If resume not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"title": "Updated Resume", "is_draft": False}
        >>> response = requests.put("/api/resume-builder/abc123", json=data)
        >>> response.json()
        {
            "id": "abc123",
            "title": "Updated Resume",
            "version": 4,
            ...
        }
    """
    locale = _extract_locale(request)
    user_id, _ = _get_user_context(request)

    try:
        logger.info(f"Updating resume id={resume_id}")

        # Validate UUID format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_id", locale, id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        service = get_resume_builder_service(db)
        resume = await service.update_resume(
            resume_id=resume_uuid,
            user_id=user_id,
            update_data=update_data,
        )

        if resume is None:
            error_msg = get_error_message("resume_not_found", locale, resume_id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        response_data = _resume_to_response(resume)
        success_msg = get_success_message("resume_updated", locale)

        logger.info(f"Updated resume id={resume_id}, version={resume.version}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error updating resume: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except SQLAlchemyError as e:
        logger.error(f"Database error updating resume: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error updating resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update resume: {str(e)}",
        ) from e


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Resume Builder"],
)
async def delete_resume(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a resume.

    Permanently deletes a resume from the system.

    Args:
        request: FastAPI request object (for user context)
        resume_id: UUID of the resume
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException(404): If resume not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("/api/resume-builder/abc123")
        >>> response.status_code
        204
    """
    locale = _extract_locale(request)
    user_id, _ = _get_user_context(request)

    try:
        logger.info(f"Deleting resume id={resume_id}")

        # Validate UUID format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_id", locale, id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        service = get_resume_builder_service(db)
        deleted = await service.delete_resume(
            resume_id=resume_uuid,
            user_id=user_id,
        )

        if not deleted:
            error_msg = get_error_message("resume_not_found", locale, resume_id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        logger.info(f"Deleted resume id={resume_id}")

        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting resume: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error deleting resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete resume: {str(e)}",
        ) from e


@router.post(
    "/{resume_id}/duplicate",
    response_model=BuiltResumeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Resume Builder"],
)
async def duplicate_resume(
    request: Request,
    resume_id: str,
    new_title: Optional[str] = Query(None, description="Title for the duplicated resume"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Duplicate a resume.

    Creates a copy of an existing resume with a new ID and reset version.

    Args:
        request: FastAPI request object (for user context)
        resume_id: UUID of the resume to duplicate
        new_title: Optional new title for the duplicate
        db: Database session

    Returns:
        JSON response with the new duplicated resume

    Raises:
        HTTPException(404): If source resume not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/resume-builder/abc123/duplicate?new_title=My%20Copy"
        ... )
        >>> response.json()
        {
            "id": "new-uuid",
            "title": "My Copy",
            "version": 1,
            ...
        }
    """
    locale = _extract_locale(request)
    user_id, _ = _get_user_context(request)

    try:
        logger.info(f"Duplicating resume id={resume_id}")

        # Validate UUID format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_id", locale, id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        service = get_resume_builder_service(db)
        duplicate = await service.duplicate_resume(
            resume_id=resume_uuid,
            user_id=user_id,
            new_title=new_title,
        )

        if duplicate is None:
            error_msg = get_error_message("resume_not_found", locale, resume_id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        response_data = _resume_to_response(duplicate)
        success_msg = get_success_message("resume_duplicated", locale)

        logger.info(f"Duplicated resume {resume_id} -> {duplicate.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error duplicating resume: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error duplicating resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate resume: {str(e)}",
        ) from e


# =============================================================================
# AI Suggestions Endpoints
# =============================================================================


@router.get(
    "/{resume_id}/suggestions",
    response_model=AISuggestionsResponse,
    tags=["Resume Builder - AI"],
)
async def get_ai_suggestions(
    request: Request,
    resume_id: str,
    target_job_description: Optional[str] = Query(None, description="Target job description for keyword matching"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get AI-powered improvement suggestions for a resume.

    Analyzes the resume content and provides suggestions for:
    - Content improvements (action verbs, achievements)
    - Keyword optimization
    - Formatting recommendations
    - Grammar corrections

    Args:
        request: FastAPI request object
        resume_id: UUID of the resume
        target_job_description: Optional job description for keyword matching
        db: Database session

    Returns:
        JSON response with list of suggestions

    Raises:
        HTTPException(404): If resume not found
        HTTPException(500): If analysis fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/resume-builder/abc123/suggestions",
        ...     params={"target_job_description": "Senior Python Developer..."}
        ... )
        >>> response.json()
        {
            "suggestions": [...],
            "ats_score_before": 65,
            "ats_score_potential": 85,
            ...
        }
    """
    locale = _extract_locale(request)
    user_id, _ = _get_user_context(request)

    try:
        logger.info(f"Getting AI suggestions for resume id={resume_id}")

        # Validate UUID format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_id", locale, id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        service = get_resume_builder_service(db)
        suggestions = await service.get_ai_suggestions(
            resume_id=resume_uuid,
            user_id=user_id,
            target_job_description=target_job_description,
        )

        logger.info(f"Generated {len(suggestions.suggestions)} suggestions for resume {resume_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=suggestions.model_dump(),
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error getting suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error getting AI suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggestions: {str(e)}",
        ) from e


@router.post(
    "/{resume_id}/suggestions/apply",
    response_model=BuiltResumeResponse,
    tags=["Resume Builder - AI"],
)
async def apply_suggestion(
    request: Request,
    resume_id: str,
    apply_data: ApplySuggestionRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Apply an AI suggestion to a resume.

    Applies a specific suggestion to the resume content, incrementing the version.

    Args:
        request: FastAPI request object
        resume_id: UUID of the resume
        apply_data: Suggestion application data
        db: Database session

    Returns:
        JSON response with updated resume

    Raises:
        HTTPException(404): If resume or suggestion not found
        HTTPException(500): If application fails

    Examples:
        >>> import requests
        >>> data = {"suggestion_id": "opt-0-abc123"}
        >>> response = requests.post(
        ...     "/api/resume-builder/abc123/suggestions/apply",
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "abc123",
            "version": 5,
            ...
        }
    """
    locale = _extract_locale(request)
    user_id, _ = _get_user_context(request)

    try:
        logger.info(f"Applying suggestion {apply_data.suggestion_id} to resume {resume_id}")

        # Validate UUID format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_id", locale, id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        service = get_resume_builder_service(db)
        resume = await service.apply_suggestion(
            resume_id=resume_uuid,
            user_id=user_id,
            suggestion_id=apply_data.suggestion_id,
            modified_text=apply_data.modified_text,
        )

        if resume is None:
            error_msg = get_error_message("resume_not_found", locale, resume_id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        response_data = _resume_to_response(resume)

        logger.info(f"Applied suggestion to resume {resume_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error applying suggestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error applying suggestion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply suggestion: {str(e)}",
        ) from e


# =============================================================================
# ATS Score Endpoints
# =============================================================================


@router.get(
    "/{resume_id}/ats-score",
    response_model=ATSScoreResponse,
    tags=["Resume Builder - ATS"],
)
async def get_ats_score(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get ATS compatibility score for a resume.

    Analyzes the resume for:
    - Keyword presence and density
    - Formatting compatibility
    - Section structure
    - Contact information completeness

    Args:
        request: FastAPI request object
        resume_id: UUID of the resume
        db: Database session

    Returns:
        JSON response with ATS score and issues

    Raises:
        HTTPException(404): If resume not found
        HTTPException(500): If analysis fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/resume-builder/abc123/ats-score")
        >>> response.json()
        {
            "score": 78,
            "issues": [...],
            "keywords_found": [...],
            "keywords_missing": [...],
            ...
        }
    """
    locale = _extract_locale(request)
    user_id, _ = _get_user_context(request)

    try:
        logger.info(f"Calculating ATS score for resume id={resume_id}")

        # Validate UUID format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_id", locale, id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        service = get_resume_builder_service(db)
        ats_response = await service.calculate_ats_score(
            resume_id=resume_uuid,
            user_id=user_id,
        )

        logger.info(f"ATS score for resume {resume_id}: {ats_response.score}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=ats_response.model_dump(),
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error calculating ATS score: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error calculating ATS score: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate ATS score: {str(e)}",
        ) from e


# =============================================================================
# Skill Gap Analysis Endpoints
# =============================================================================


@router.get(
    "/{resume_id}/skill-gap",
    response_model=SkillGapAnalysisResponse,
    tags=["Resume Builder - Skills"],
)
async def analyze_skill_gaps(
    request: Request,
    resume_id: str,
    target_job_id: Optional[str] = Query(None, description="Target job vacancy ID"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Analyze skill gaps between a resume and target job.

    Compares the skills in the resume against the requirements of a target job
    and provides recommendations for bridging the gaps.

    Args:
        request: FastAPI request object
        resume_id: UUID of the resume
        target_job_id: Optional job vacancy ID (uses resume's target if not provided)
        db: Database session

    Returns:
        JSON response with skill gap analysis

    Raises:
        HTTPException(400): If no target job specified
        HTTPException(404): If resume or job not found
        HTTPException(500): If analysis fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/resume-builder/abc123/skill-gap",
        ...     params={"target_job_id": "job123"}
        ... )
        >>> response.json()
        {
            "target_job_id": "job123",
            "matching_skills": ["Python", "Django"],
            "missing_skills": [...],
            "match_percentage": 75,
            ...
        }
    """
    locale = _extract_locale(request)
    user_id, _ = _get_user_context(request)

    try:
        logger.info(f"Analyzing skill gaps for resume id={resume_id}")

        # Validate UUID format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_id", locale, id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        service = get_resume_builder_service(db)
        gap_analysis = await service.analyze_skill_gaps(
            resume_id=resume_uuid,
            target_job_id=target_job_id,
            user_id=user_id,
        )

        logger.info(
            f"Skill gap analysis complete for resume {resume_id}: "
            f"{len(gap_analysis.matching_skills)} matching, "
            f"{len(gap_analysis.missing_skills)} missing"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=gap_analysis.model_dump(),
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error in skill gap analysis: {e}")
        if "No target job" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error analyzing skill gaps: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze skill gaps: {str(e)}",
        ) from e


# =============================================================================
# Export Endpoints
# =============================================================================


@router.post(
    "/{resume_id}/export",
    tags=["Resume Builder - Export"],
)
async def export_resume(
    request: Request,
    resume_id: str,
    export_data: ExportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Export a resume to PDF, DOCX, or JSON format.

    Generates a downloadable file in the specified format.

    Args:
        request: FastAPI request object
        resume_id: UUID of the resume
        export_data: Export format specification
        db: Database session

    Returns:
        File download (StreamingResponse) or JSON response with download URL

    Raises:
        HTTPException(404): If resume not found
        HTTPException(500): If export fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/resume-builder/abc123/export",
        ...     json={"format": "pdf"}
        ... )
        >>> # Response is a PDF file download
    """
    locale = _extract_locale(request)
    user_id, _ = _get_user_context(request)

    try:
        logger.info(f"Exporting resume id={resume_id} as {export_data.format}")

        # Validate UUID format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_id", locale, id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        service = get_resume_builder_service(db)
        resume = await service.get_resume(resume_uuid, user_id)

        if resume is None:
            error_msg = get_error_message("resume_not_found", locale, resume_id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Generate filename
        safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in resume.title)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if export_data.format == "pdf":
            # Generate PDF
            pdf_generator = get_pdf_generator()
            options = PDFGenerationOptions(
                page_format="A4",
                margin_top=20,
                margin_bottom=20,
                margin_left=20,
                margin_right=20,
            )
            filename = f"{safe_title}_{timestamp}.pdf"

            # Render resume content to HTML for PDF generation
            html_content = _render_resume_to_html(resume.content)
            result = await pdf_generator.generate_resume_pdf(
                html=html_content,
                filename=filename,
                options=options,
            )

            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate PDF: {result.error_message}",
                )

            return StreamingResponse(
                io.BytesIO(result.pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Content-Length": str(result.file_size),
                },
            )

        elif export_data.format == "docx":
            # Generate DOCX
            docx_generator = get_docx_generator()
            options = DOCXGenerationOptions(
                page_format="A4",
                margin_top=20,
                margin_bottom=20,
                margin_left=20,
                margin_right=20,
            )
            filename = f"{safe_title}_{timestamp}.docx"
            result = await docx_generator.generate_resume_docx(
                resume_content=resume.content,
                filename=filename,
                options=options,
            )

            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate DOCX: {result.error_message}",
                )

            return StreamingResponse(
                io.BytesIO(result.docx_bytes),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Content-Length": str(result.file_size),
                },
            )

        elif export_data.format == "json":
            # Return JSON content
            filename = f"{safe_title}_{timestamp}.json"
            content = _resume_to_response(resume)

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=content,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                },
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported export format: {export_data.format}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export resume: {str(e)}",
        ) from e


# =============================================================================
# Version History Endpoints
# =============================================================================


@router.get(
    "/{resume_id}/versions",
    response_model=ResumeVersionHistoryResponse,
    tags=["Resume Builder - Versions"],
)
async def get_version_history(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get version history for a resume.

    Returns the list of all saved versions of the resume.

    Args:
        request: FastAPI request object
        resume_id: UUID of the resume
        db: Database session

    Returns:
        JSON response with version history

    Raises:
        HTTPException(404): If resume not found
        HTTPException(500): If query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/resume-builder/abc123/versions")
        >>> response.json()
        {
            "resume_id": "abc123",
            "current_version": 5,
            "versions": [...]
        }
    """
    locale = _extract_locale(request)
    user_id, _ = _get_user_context(request)

    try:
        logger.info(f"Getting version history for resume id={resume_id}")

        # Validate UUID format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_id", locale, id=resume_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        service = get_resume_builder_service(db)
        history = await service.get_version_history(
            resume_id=resume_uuid,
            user_id=user_id,
        )

        logger.info(f"Retrieved version history for resume {resume_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=history,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error getting version history: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error getting version history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version history: {str(e)}",
        ) from e


# =============================================================================
# Templates Endpoints
# =============================================================================


@router.get(
    "/templates",
    response_model=ResumeTemplateListResponse,
    tags=["Resume Builder - Templates"],
)
async def list_templates(
    request: Request,
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    is_ats_compliant: Optional[bool] = Query(None, description="Filter by ATS compliance"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List available resume templates.

    Returns a list of templates that can be used to create resumes.

    Args:
        request: FastAPI request object
        template_type: Optional filter by template type (modern, classic, creative, ats_friendly)
        is_ats_compliant: Optional filter by ATS compliance
        db: Database session

    Returns:
        JSON response with list of templates

    Raises:
        HTTPException(500): If query fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/resume-builder/templates",
        ...     params={"is_ats_compliant": True}
        ... )
        >>> response.json()
        {
            "items": [...],
            "total": 5
        }
    """
    locale = _extract_locale(request)

    try:
        logger.info(f"Listing resume templates with filters: type={template_type}, ats={is_ats_compliant}")

        # Build query
        stmt = select(ResumeTemplate).where(ResumeTemplate.is_active == True)

        if template_type:
            stmt = stmt.where(ResumeTemplate.template_type == template_type)
        if is_ats_compliant is not None:
            stmt = stmt.where(ResumeTemplate.is_ats_compliant == is_ats_compliant)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        # Execute query
        stmt = stmt.order_by(ResumeTemplate.is_default.desc(), ResumeTemplate.name)
        result = await db.execute(stmt)
        templates = result.scalars().all()

        items = [
            ResumeTemplateSummary(
                id=str(t.id),
                name=t.name,
                description=t.description,
                preview_url=t.preview_url,
                category=t.template_type,
                is_premium=False,  # For now, all templates are free
            ).model_dump()
            for t in templates
        ]

        logger.info(f"Retrieved {total} resume templates")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "items": items,
                "total": total,
            },
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error listing templates: {e}", exc_info=True)
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}",
        ) from e
