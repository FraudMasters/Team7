"""
Candidate Documents API endpoints for uploading and managing additional documents.

This module provides endpoints for candidates to upload additional documents
(portfolios, certifications, transcripts) and manage their document collection.
"""
import logging
from pathlib import Path
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from i18n.backend_translations import get_error_message, get_success_message
from database import get_db
from models.candidate_document import CandidateDocument, DocumentType
from models.user import User
from models.job_application import JobApplication
from models.audit_log import AuditActionType
from utils.audit_logger import log_audit_event, get_request_context
from dependencies.auth import get_current_user

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


# Directory for storing uploaded documents
UPLOAD_DIR = Path("data/uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class DocumentUploadResponse(BaseModel):
    """Response model for document upload endpoint."""

    id: str = Field(..., description="Unique identifier for the uploaded document")
    filename: str = Field(..., description="Original filename of the uploaded document")
    document_type: str = Field(..., description="Type of document")
    description: Optional[str] = Field(None, description="Document description")
    application_id: Optional[str] = Field(None, description="Associated application ID")
    message: str = Field(..., description="Success message")


class DocumentResponse(BaseModel):
    """Response model for document information."""

    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    document_type: str = Field(..., description="Type of document")
    description: Optional[str] = Field(None, description="Document description")
    application_id: Optional[str] = Field(None, description="Associated application ID")
    content_type: str = Field(..., description="MIME type")
    created_at: str = Field(..., description="Upload timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class DocumentsListResponse(BaseModel):
    """Response model for listing documents."""

    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total count of documents")


def validate_file_type(filename: str, content_type: str, locale: str = "en") -> None:
    """
    Validate that the file type is allowed.

    Args:
        filename: Name of the uploaded file
        content_type: MIME type of the file
        locale: Language code for translated error messages

    Raises:
        HTTPException: If file type is not allowed
    """
    # Check file extension
    file_ext = Path(filename).suffix.lower()

    # Allow additional file types for documents (images for portfolios)
    allowed_extensions = [".pdf", ".docx", ".png", ".jpg", ".jpeg", ".gif"]

    if file_ext not in allowed_extensions:
        allowed = ", ".join(allowed_extensions)
        error_msg = get_error_message("invalid_file_type", locale, file_ext=file_ext, allowed=allowed)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=error_msg,
        )

    # Check content type for additional validation
    allowed_content_types = {
        ".pdf": ["application/pdf"],
        ".docx": [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ],
        ".png": ["image/png"],
        ".jpg": ["image/jpeg"],
        ".jpeg": ["image/jpeg"],
        ".gif": ["image/gif"],
    }

    if file_ext in allowed_content_types:
        if content_type not in allowed_content_types[file_ext]:
            logger.warning(
                f"Content type mismatch for {filename}: {content_type} not in {allowed_content_types[file_ext]}"
            )


def validate_file_size(file_size: int, locale: str = "en") -> None:
    """
    Validate that the file size is within allowed limits.

    Args:
        file_size: Size of the file in bytes
        locale: Language code for translated error messages

    Raises:
        HTTPException: If file size exceeds maximum allowed
    """
    max_size = settings.max_upload_size_bytes
    if file_size > max_size:
        max_mb = settings.max_upload_size_mb
        size_mb = file_size / 1024 / 1024
        error_msg = get_error_message("file_too_large", locale, size=size_mb, max_mb=max_mb)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_msg,
        )


def _document_to_response(document: CandidateDocument) -> dict:
    """Convert CandidateDocument model to response dict."""
    return {
        "id": str(document.id),
        "filename": document.filename,
        "document_type": document.document_type.value,
        "description": document.description,
        "application_id": str(document.application_id) if document.application_id else None,
        "content_type": document.content_type,
        "created_at": document.created_at.isoformat() if document.created_at else None,
        "updated_at": document.updated_at.isoformat() if document.updated_at else None,
    }


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Candidate Documents"],
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: DocumentType = Query(..., description="Type of document being uploaded"),
    description: Optional[str] = Query(None, max_length=500, description="Optional document description"),
    application_id: Optional[str] = Query(None, description="Optional job application ID to link this document to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Upload a candidate document (portfolio, certification, etc.).

    This endpoint allows authenticated candidates to upload additional documents
    such as portfolios, certifications, transcripts, or references.

    Args:
        request: FastAPI request object (for Accept-Language header)
        file: Uploaded document file
        document_type: Type of document (PORTFOLIO, CERTIFICATION, etc.)
        description: Optional description of the document
        application_id: Optional job application ID to link the document to
        db: Database session
        current_user: Authenticated user

    Returns:
        JSON response with document ID, filename, and status

    Raises:
        HTTPException(415): If file type is not supported
        HTTPException(413): If file size exceeds maximum allowed
        HTTPException(404): If application_id is provided but not found
        HTTPException(403): If application doesn't belong to the user
        HTTPException(500): If file storage or database operation fails

    Examples:
        >>> import requests
        >>> with open("portfolio.pdf", "rb") as f:
        ...     response = requests.post(
        ...         "http://localhost:8000/api/candidate-documents/upload",
        ...         files={"file": f},
        ...         params={"document_type": "PORTFOLIO", "description": "My design portfolio"}
        ...     )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "portfolio.pdf",
            "document_type": "PORTFOLIO",
            "description": "My design portfolio",
            "application_id": null,
            "message": "Document uploaded successfully"
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        logger.info(f"Received document upload: {file.filename} ({file_size} bytes) by user {current_user.id}")

        # Validate file type
        validate_file_type(file.filename or "unknown", file.content_type or "application/octet-stream", locale)

        # Validate file size
        validate_file_size(file_size, locale)

        # Validate application_id if provided
        application_uuid = None
        if application_id:
            try:
                application_uuid = UUID(application_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid application ID format",
                )

            # Check if application exists and belongs to the user
            app_query = select(JobApplication).where(JobApplication.id == application_uuid)
            app_result = await db.execute(app_query)
            application = app_result.scalar_one_or_none()

            if not application:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Application not found",
                )

            if application.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Application does not belong to the authenticated user",
                )

        # Generate UUID for the document
        document_id = uuid4()
        safe_filename = Path(file.filename or "document").name
        file_extension = Path(safe_filename).suffix
        stored_filename = f"{document_id}{file_extension}"
        file_path = UPLOAD_DIR / stored_filename

        # Save file to disk
        logger.info(f"Saving document to: {file_path}")
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Create database record
        new_document = CandidateDocument(
            id=document_id,
            user_id=current_user.id,
            application_id=application_uuid,
            document_type=document_type,
            filename=file.filename or "unknown",
            file_path=str(file_path),
            content_type=file.content_type or "application/octet-stream",
            description=description,
        )

        db.add(new_document)
        await db.commit()
        await db.refresh(new_document)

        # Log audit event
        await log_audit_event(
            db=db,
            action_type=AuditActionType.UPLOAD,
            user_id=current_user.id,
            resource_type="candidate_document",
            resource_id=str(document_id),
            details={
                "filename": file.filename,
                "document_type": document_type.value,
                "application_id": str(application_uuid) if application_uuid else None,
                "file_size": file_size,
            },
            request_context=get_request_context(request),
        )

        logger.info(f"Document uploaded successfully: {document_id}")

        success_message = get_success_message("file_uploaded", locale)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(document_id),
                "filename": file.filename or "unknown",
                "document_type": document_type.value,
                "description": description,
                "application_id": str(application_uuid) if application_uuid else None,
                "message": success_message,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        error_msg = get_error_message("file_upload_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


@router.get(
    "/list",
    response_model=DocumentsListResponse,
    tags=["Candidate Documents"],
)
async def list_documents(
    request: Request,
    document_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    application_id: Optional[str] = Query(None, description="Filter by application ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    List all documents for the authenticated user.

    This endpoint returns a paginated list of documents uploaded by the authenticated user,
    with optional filtering by document type and application.

    Args:
        request: FastAPI request object
        document_type: Optional filter by document type
        application_id: Optional filter by application ID
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        db: Database session
        current_user: Authenticated user

    Returns:
        JSON response with list of documents and total count

    Raises:
        HTTPException(400): If application_id format is invalid

    Examples:
        >>> response = requests.get(
        ...     "http://localhost:8000/api/candidate-documents/list",
        ...     params={"document_type": "PORTFOLIO", "limit": 10}
        ... )
        >>> response.json()
        {
            "documents": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "filename": "portfolio.pdf",
                    "document_type": "PORTFOLIO",
                    "description": "My design portfolio",
                    "application_id": null,
                    "content_type": "application/pdf",
                    "created_at": "2026-03-21T10:30:00",
                    "updated_at": "2026-03-21T10:30:00"
                }
            ],
            "total": 1
        }
    """
    try:
        # Build query
        query = select(CandidateDocument).where(
            CandidateDocument.user_id == current_user.id
        )

        # Apply filters
        if document_type:
            query = query.where(CandidateDocument.document_type == document_type)

        if application_id:
            try:
                application_uuid = UUID(application_id)
                query = query.where(CandidateDocument.application_id == application_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid application ID format",
                )

        # Get total count
        count_query = select(CandidateDocument).where(
            CandidateDocument.user_id == current_user.id
        )
        if document_type:
            count_query = count_query.where(CandidateDocument.document_type == document_type)
        if application_id:
            count_query = count_query.where(CandidateDocument.application_id == application_uuid)

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # Apply pagination and ordering
        query = query.order_by(CandidateDocument.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        documents = result.scalars().all()

        # Convert to response format
        documents_list = [_document_to_response(doc) for doc in documents]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "documents": documents_list,
                "total": total,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}", exc_info=True)
        locale = _extract_locale(request)
        error_msg = get_error_message("file_upload_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Candidate Documents"],
)
async def delete_document(
    request: Request,
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a candidate document.

    This endpoint allows users to delete their uploaded documents.

    Args:
        request: FastAPI request object
        document_id: ID of the document to delete
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException(400): If document_id format is invalid
        HTTPException(404): If document not found
        HTTPException(403): If document doesn't belong to the user

    Examples:
        >>> response = requests.delete(
        ...     "http://localhost:8000/api/candidate-documents/123e4567-e89b-12d3-a456-426614174000"
        ... )
        >>> response.status_code
        204
    """
    try:
        # Parse document_id
        try:
            doc_uuid = UUID(document_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document ID format",
            )

        # Find document
        query = select(CandidateDocument).where(CandidateDocument.id == doc_uuid)
        result = await db.execute(query)
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        # Verify ownership
        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Document does not belong to the authenticated user",
            )

        # Delete file from disk
        file_path = Path(document.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {str(e)}")

        # Delete database record
        await db.delete(document)
        await db.commit()

        # Log audit event
        await log_audit_event(
            db=db,
            action_type=AuditActionType.DELETE,
            user_id=current_user.id,
            resource_type="candidate_document",
            resource_id=str(doc_uuid),
            details={
                "filename": document.filename,
                "document_type": document.document_type.value,
            },
            request_context=get_request_context(request),
        )

        logger.info(f"Document deleted successfully: {doc_uuid}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        locale = _extract_locale(request)
        error_msg = get_error_message("file_upload_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )
