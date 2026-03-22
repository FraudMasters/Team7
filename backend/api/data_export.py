"""
Data export endpoints for GDPR right to portability.

This module provides endpoints for:
- Exporting candidate/resume data in machine-readable formats (JSON, CSV)
- Supporting GDPR Article 15 - Right of Access and Article 20 - Data Portability
- Providing comprehensive data export including all associated information

The export includes all personal data stored about a candidate including
resume data, hiring stages, notes, tags, activities, and audit trails.
"""
import csv
import io
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.resume import Resume
from models.hiring_stage import HiringStage
from models.workflow_stage_config import WorkflowStageConfig
from models.candidate_tag import CandidateTag
from models.candidate_note import CandidateNote
from models.candidate_activity import CandidateActivity, CandidateActivityType
from models.audit_log import AuditActionType
from utils.audit_logger import log_audit_event, get_request_context

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class PersonalDataExport(BaseModel):
    """Comprehensive export of all personal data for a candidate."""

    resume_id: str = Field(..., description="Resume UUID")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Stored file path")
    content_type: str = Field(..., description="MIME type")
    raw_text: Optional[str] = Field(None, description="Extracted text content")
    language: Optional[str] = Field(None, description="Detected language")
    status: str = Field(..., description="Processing status")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    hiring_stages: List[Dict[str, Any]] = Field(default_factory=list, description="All hiring stage transitions")
    notes: List[Dict[str, Any]] = Field(default_factory=list, description="All candidate notes")
    tags: List[Dict[str, Any]] = Field(default_factory=list, description="Current and past tags")
    activities: List[Dict[str, Any]] = Field(default_factory=list, description="All activities/interactions")


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


@router.get(
    "/resume/{resume_id}",
    response_model=PersonalDataExport,
    tags=["Data Export"],
)
async def export_resume_data(
    resume_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Export all personal data for a specific resume/candidate (GDPR Right to Portability).

    This endpoint provides a comprehensive export of all personal data stored
    about a candidate in accordance with GDPR Article 15 (Right of Access) and
    Article 20 (Right to Data Portability).

    The export includes:
    - Resume metadata and content
    - All hiring stage transitions
    - All notes associated with the candidate
    - Tag history (current and past tags)
    - Complete activity/interaction log

    Args:
        resume_id: Resume UUID
        request: FastAPI request object
        db: Database session

    Returns:
        JSON response with comprehensive personal data export

    Raises:
        HTTPException(404): If resume is not found
        HTTPException(422): If resume_id format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/data-export/resume/123e4567-e89b-12d3-a456-426614174000"
        ... )
        >>> data = response.json()
        >>> # data contains all personal information about the candidate
    """
    locale = _extract_locale(request)

    try:
        # Validate resume_id format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid resume ID format: {resume_id}",
            )

        # Get the resume
        resume_query = select(Resume).where(Resume.id == resume_uuid)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}",
            )

        # Get all hiring stages for this resume
        hiring_stages_query = (
            select(HiringStage, WorkflowStageConfig)
            .outerjoin(
                WorkflowStageConfig,
                HiringStage.workflow_stage_config_id == WorkflowStageConfig.id,
            )
            .where(HiringStage.resume_id == resume_uuid)
            .order_by(HiringStage.created_at)
        )
        hiring_stages_result = await db.execute(hiring_stages_query)
        hiring_stages_rows = hiring_stages_result.all()

        hiring_stages = []
        for hs, wc in hiring_stages_rows:
            hiring_stages.append({
                "id": str(hs.id),
                "stage_name": hs.stage_name,
                "custom_stage_name": wc.stage_name if wc else None,
                "display_name": wc.display_name if wc else None,
                "vacancy_id": str(hs.vacancy_id) if hs.vacancy_id else None,
                "notes": hs.notes,
                "created_at": hs.created_at.isoformat() if hs.created_at else None,
                "updated_at": hs.updated_at.isoformat() if hs.updated_at else None,
            })

        # Get all notes for this resume
        notes_query = (
            select(CandidateNote)
            .where(CandidateNote.resume_id == resume_uuid)
            .order_by(CandidateNote.created_at)
        )
        notes_result = await db.execute(notes_query)
        notes = notes_result.scalars().all()

        notes_list = []
        for note in notes:
            notes_list.append({
                "id": str(note.id),
                "content": note.content,
                "created_at": note.created_at.isoformat() if note.created_at else None,
                "updated_at": note.updated_at.isoformat() if note.updated_at else None,
            })

        # Get all tag-related activities
        tag_activities_query = (
            select(CandidateActivity, CandidateTag)
            .outerjoin(
                CandidateTag,
                CandidateActivity.tag_id == CandidateTag.id
            )
            .where(
                and_(
                    CandidateActivity.candidate_id == resume_uuid,
                    CandidateActivity.activity_type.in_([
                        CandidateActivityType.TAG_ADDED,
                        CandidateActivityType.TAG_REMOVED
                    ])
                )
            )
            .order_by(CandidateActivity.created_at)
        )
        tag_activities_result = await db.execute(tag_activities_query)
        tag_activities_rows = tag_activities_result.all()

        # Build tag history
        tags_list = []
        for activity, tag in tag_activities_rows:
            tags_list.append({
                "tag_id": str(tag.id) if tag else None,
                "tag_name": tag.tag_name if tag else None,
                "color": tag.color if tag else None,
                "activity_type": activity.activity_type.value,
                "created_at": activity.created_at.isoformat() if activity.created_at else None,
            })

        # Get all activities for this resume
        activities_query = (
            select(CandidateActivity)
            .where(CandidateActivity.candidate_id == resume_uuid)
            .order_by(CandidateActivity.created_at)
        )
        activities_result = await db.execute(activities_query)
        activities = activities_result.scalars().all()

        activities_list = []
        for activity in activities:
            activities_list.append({
                "id": str(activity.id),
                "activity_type": activity.activity_type.value,
                "tag_id": str(activity.tag_id) if activity.tag_id else None,
                "metadata": activity.metadata,
                "created_at": activity.created_at.isoformat() if activity.created_at else None,
            })

        # Build comprehensive export
        export_data = {
            "resume_id": str(resume.id),
            "filename": resume.filename,
            "file_path": resume.file_path,
            "content_type": resume.content_type,
            "raw_text": resume.raw_text,
            "language": resume.language,
            "status": resume.status.value,
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
            "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
            "hiring_stages": hiring_stages,
            "notes": notes_list,
            "tags": tags_list,
            "activities": activities_list,
        }

        logger.info(f"Data export generated for resume {resume_id}")

        # Log audit event for data export (GDPR)
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.DATA_EXPORTED,
            entity_type="resume",
            entity_id=resume_uuid,
            ip_address=ip_address,
            user_agent=user_agent,
            action_data={
                "export_format": "json",
                "export_type": "resume_personal_data",
                "gdpr_compliance": True,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=export_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting data for resume {resume_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}",
        ) from e


@router.get(
    "/resume/{resume_id}/csv",
    tags=["Data Export"],
)
async def export_resume_data_csv(
    resume_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Export all personal data for a specific resume/candidate in CSV format.

    This endpoint provides the same comprehensive export as the JSON endpoint
    but formats the data as CSV for easier import into other systems.

    Args:
        resume_id: Resume UUID
        request: FastAPI request object
        db: Database session

    Returns:
        CSV file download with comprehensive personal data

    Raises:
        HTTPException(404): If resume is not found
        HTTPException(422): If resume_id format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/data-export/resume/123e4567-e89b-12d3-a456-426614174000/csv"
        ... )
        >>> # Returns CSV file for download
    """
    locale = _extract_locale(request)

    try:
        # Validate resume_id format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid resume ID format: {resume_id}",
            )

        # Get the resume
        resume_query = select(Resume).where(Resume.id == resume_uuid)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}",
            )

        # Get all hiring stages for this resume
        hiring_stages_query = (
            select(HiringStage, WorkflowStageConfig)
            .outerjoin(
                WorkflowStageConfig,
                HiringStage.workflow_stage_config_id == WorkflowStageConfig.id,
            )
            .where(HiringStage.resume_id == resume_uuid)
            .order_by(HiringStage.created_at)
        )
        hiring_stages_result = await db.execute(hiring_stages_query)
        hiring_stages_rows = hiring_stages_result.all()

        # Get all notes for this resume
        notes_query = (
            select(CandidateNote)
            .where(CandidateNote.resume_id == resume_uuid)
            .order_by(CandidateNote.created_at)
        )
        notes_result = await db.execute(notes_query)
        notes = notes_result.scalars().all()

        # Get all tag-related activities
        tag_activities_query = (
            select(CandidateActivity, CandidateTag)
            .outerjoin(
                CandidateTag,
                CandidateActivity.tag_id == CandidateTag.id
            )
            .where(
                and_(
                    CandidateActivity.candidate_id == resume_uuid,
                    CandidateActivity.activity_type.in_([
                        CandidateActivityType.TAG_ADDED,
                        CandidateActivityType.TAG_REMOVED
                    ])
                )
            )
            .order_by(CandidateActivity.created_at)
        )
        tag_activities_result = await db.execute(tag_activities_query)
        tag_activities_rows = tag_activities_result.all()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write summary section
        writer.writerow(["Data Export for Resume", resume_id])
        writer.writerow(["Generated at", resume.updated_at.isoformat() if resume.updated_at else "N/A"])
        writer.writerow([])

        # Write resume information
        writer.writerow(["RESUME INFORMATION"])
        writer.writerow(["Field", "Value"])
        writer.writerow(["Resume ID", str(resume.id)])
        writer.writerow(["Filename", resume.filename])
        writer.writerow(["Content Type", resume.content_type])
        writer.writerow(["Language", resume.language or "N/A"])
        writer.writerow(["Status", resume.status.value])
        writer.writerow(["Created At", resume.created_at.isoformat() if resume.created_at else "N/A"])
        writer.writerow(["Updated At", resume.updated_at.isoformat() if resume.updated_at else "N/A"])
        writer.writerow([])

        # Write hiring stages
        writer.writerow(["HIRING STAGES"])
        writer.writerow(["Stage Name", "Custom Stage", "Display Name", "Vacancy ID", "Notes", "Created At", "Updated At"])
        for hs, wc in hiring_stages_rows:
            writer.writerow([
                hs.stage_name,
                wc.stage_name if wc else "",
                wc.display_name if wc else "",
                str(hs.vacancy_id) if hs.vacancy_id else "",
                hs.notes or "",
                hs.created_at.isoformat() if hs.created_at else "",
                hs.updated_at.isoformat() if hs.updated_at else "",
            ])
        writer.writerow([])

        # Write notes
        writer.writerow(["NOTES"])
        writer.writerow(["Note ID", "Content", "Created At", "Updated At"])
        for note in notes:
            writer.writerow([
                str(note.id),
                note.content,
                note.created_at.isoformat() if note.created_at else "",
                note.updated_at.isoformat() if note.updated_at else "",
            ])
        writer.writerow([])

        # Write tag history
        writer.writerow(["TAG HISTORY"])
        writer.writerow(["Tag Name", "Action", "Color", "Date"])
        for activity, tag in tag_activities_rows:
            writer.writerow([
                tag.tag_name if tag else "N/A",
                activity.activity_type.value,
                tag.color if tag else "",
                activity.created_at.isoformat() if activity.created_at else "",
            ])

        # Prepare response
        csv_content = output.getvalue()
        output.close()

        logger.info(f"CSV data export generated for resume {resume_id}")

        # Log audit event for CSV data export (GDPR)
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.DATA_EXPORTED,
            entity_type="resume",
            entity_id=resume_uuid,
            ip_address=ip_address,
            user_agent=user_agent,
            action_data={
                "export_format": "csv",
                "export_type": "resume_personal_data",
                "gdpr_compliance": True,
            },
        )

        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=resume_{resume_id}_export.csv"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting CSV data for resume {resume_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export CSV data: {str(e)}",
        ) from e


@router.get(
    "/organization/{organization_id}",
    tags=["Data Export"],
)
async def export_organization_data(
    organization_id: str,
    request: Request,
    format: str = Query("json", description="Export format: json or csv"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to export"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Export all personal data for an organization (GDPR Right to Portability).

    This endpoint provides a comprehensive export of all candidate data
    associated with an organization. Useful for data portability and backup purposes.

    Args:
        organization_id: Organization UUID
        request: FastAPI request object
        format: Export format (json or csv, default: json)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with organization-wide data export

    Raises:
        HTTPException(422): If organization_id format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8000/api/data-export/organization/org-123?format=json&limit=50"
        ... )
        >>> data = response.json()
    """
    locale = _extract_locale(request)

    try:
        # Validate organization_id format
        try:
            organization_uuid = UUID(organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid organization ID format: {organization_id}",
            )

        # Get all resumes for this organization
        resumes_query = (
            select(Resume)
            .where(Resume.organization_id == organization_uuid)
            .order_by(Resume.created_at)
            .offset(skip)
            .limit(limit)
        )
        resumes_result = await db.execute(resumes_query)
        resumes = resumes_result.scalars().all()

        # Build simplified export for each resume
        export_data = []
        for res in resumes:
            export_data.append({
                "resume_id": str(res.id),
                "filename": res.filename,
                "content_type": res.content_type,
                "language": res.language,
                "status": res.status.value,
                "created_at": res.created_at.isoformat() if res.created_at else None,
                "updated_at": res.updated_at.isoformat() if res.updated_at else None,
            })

        logger.info(f"Organization data export generated for {organization_id}, {len(export_data)} records")

        # Log audit event for organization-wide data export
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.DATA_EXPORTED,
            entity_type="organization",
            entity_id=organization_uuid,
            organization_id=organization_uuid,
            ip_address=ip_address,
            user_agent=user_agent,
            action_data={
                "export_format": format,
                "export_type": "organization_data",
                "record_count": len(export_data),
                "skip": skip,
                "limit": limit,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "export_id": f"org_{organization_id}_{skip}_{limit}",
                "format": format,
                "organization_id": organization_id,
                "data": export_data,
                "generated_at": datetime.utcnow().isoformat(),
                "total_records": len(export_data),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting data for organization {organization_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export organization data: {str(e)}",
        ) from e
