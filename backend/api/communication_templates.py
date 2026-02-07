"""
Communication template management endpoints.

This module provides endpoints for managing communication templates,
including CRUD operations for creating, reading, updating, and deleting
templates with variable substitution and preview capabilities.
"""
import logging
import re
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class TemplateEntry(BaseModel):
    """Individual template entry definition."""

    organization_id: str = Field(..., description="ID of the organization")
    name: str = Field(..., description="Name of the template", min_length=1, max_length=255)
    type: str = Field(..., description="Type of communication (email, sms, phone)", min_length=1, max_length=50)
    subject: Optional[str] = Field(None, description="Subject line (for emails)", max_length=500)
    body: str = Field(..., description="Body content of the communication", min_length=1)
    variables: Dict[str, str] = Field(default_factory=dict, description="Template variables with descriptions")
    is_active: bool = Field(True, description="Whether this template is active")
    language: str = Field("en", description="Language code (e.g., 'en', 'ru')", min_length=2, max_length=10)
    created_by: Optional[str] = Field(None, description="ID of the user creating this template")


class TemplateCreate(BaseModel):
    """Request model for creating a template."""

    template: TemplateEntry = Field(..., description="Template to create")


class TemplateUpdate(BaseModel):
    """Request model for updating a template."""

    name: Optional[str] = Field(None, description="Name of the template", min_length=1, max_length=255)
    type: Optional[str] = Field(None, description="Type of communication (email, sms, phone)", min_length=1, max_length=50)
    subject: Optional[str] = Field(None, description="Subject line (for emails)", max_length=500)
    body: Optional[str] = Field(None, description="Body content of the communication", min_length=1)
    variables: Optional[Dict[str, str]] = Field(None, description="Template variables with descriptions")
    is_active: Optional[bool] = Field(None, description="Whether this template is active")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'ru')", min_length=2, max_length=10)


class TemplatePreviewRequest(BaseModel):
    """Request model for template preview."""

    variables: Dict[str, str] = Field(..., description="Variable values for substitution")


class TemplateResponse(BaseModel):
    """Response model for a single template."""

    id: str = Field(..., description="Unique identifier for the template")
    organization_id: str = Field(..., description="ID of the organization")
    name: str = Field(..., description="Name of the template")
    type: str = Field(..., description="Type of communication")
    subject: Optional[str] = Field(None, description="Subject line")
    body: str = Field(..., description="Body content")
    variables: Dict[str, str] = Field(..., description="Template variables")
    is_active: bool = Field(..., description="Whether template is active")
    language: str = Field(..., description="Language code")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class TemplateListResponse(BaseModel):
    """Response model for listing templates."""

    templates: List[TemplateResponse] = Field(..., description="List of templates")
    total_count: int = Field(..., description="Total number of templates")


def _extract_template_variables(content: str) -> List[str]:
    """
    Extract template variables from content.

    Variables are expected to be in the format {{variable_name}}.

    Args:
        content: Content to extract variables from

    Returns:
        List of variable names found in the content
    """
    pattern = r"\{\{(\w+)\}\}"
    variables = re.findall(pattern, content)
    return list(set(variables))


def _substitute_variables(content: Optional[str], variables: Dict[str, str]) -> str:
    """
    Substitute template variables in content.

    Args:
        content: Content with variables in {{variable_name}} format
        variables: Dictionary of variable values

    Returns:
        Content with variables substituted
    """
    if not content:
        return ""

    result = content
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))

    return result


@router.post(
    "/",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Communication Templates"],
)
async def create_template(request: TemplateCreate) -> JSONResponse:
    """
    Create a communication template.

    This endpoint creates a new communication template with support for
    variable substitution in subject and body. Templates can be used for
    emails, SMS, and other communication types.

    Args:
        request: Create request with template details

    Returns:
        JSON response with created template

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "template": {
        ...         "organization_id": "org123",
        ...         "name": "Interview Invitation",
        ...         "type": "email",
        ...         "subject": "Interview Invitation - {{company_name}}",
        ...         "body": "Dear {{candidate_name}}, ...",
        ...         "variables": {"candidate_name": "Candidate name", "company_name": "Company name"}
        ...     }
        ... }
        >>> response = requests.post("http://localhost:8000/api/communication-templates/", json=data)
        >>> response.json()
    """
    try:
        logger.info(f"Creating communication template: {request.template.name}")

        # Validate template type
        valid_types = ["email", "sms", "phone"]
        if request.template.type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Type must be one of: {', '.join(valid_types)}",
            )

        # Validate body content
        if not request.template.body or not request.template.body.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Body content cannot be empty",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        template_response = {
            "id": "placeholder-id",
            "organization_id": request.template.organization_id,
            "name": request.template.name,
            "type": request.template.type,
            "subject": request.template.subject,
            "body": request.template.body,
            "variables": request.template.variables,
            "is_active": request.template.is_active,
            "language": request.template.language,
            "created_by": request.template.created_by,
            "created_at": "2024-01-25T00:00:00Z",
            "updated_at": "2024-01-25T00:00:00Z",
        }

        logger.info(f"Created template: {template_response['id']}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=template_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}",
        ) from e


@router.get("/", tags=["Communication Templates"])
async def list_templates(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    type: Optional[str] = Query(None, description="Filter by communication type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    language: Optional[str] = Query(None, description="Filter by language code"),
) -> JSONResponse:
    """
    List communication templates with optional filters.

    Args:
        organization_id: Optional organization ID filter
        type: Optional communication type filter
        is_active: Optional active status filter
        language: Optional language code filter

    Returns:
        JSON response with list of templates

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/communication-templates/?type=email")
        >>> response.json()
    """
    try:
        logger.info(
            f"Listing templates with filters - organization_id: {organization_id}, "
            f"type: {type}, is_active: {is_active}, language: {language}"
        )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        response_data = {
            "templates": [],
            "total_count": 0,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}",
        ) from e


@router.get("/{template_id}", tags=["Communication Templates"])
async def get_template(template_id: str) -> JSONResponse:
    """
    Get a specific communication template by ID.

    Args:
        template_id: Unique identifier of the template

    Returns:
        JSON response with template details

    Raises:
        HTTPException(404): If template is not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/communication-templates/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
    """
    try:
        logger.info(f"Getting template: {template_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": template_id,
                "organization_id": "org123",
                "name": "Interview Invitation",
                "type": "email",
                "subject": "Interview Invitation - {{company_name}}",
                "body": "Dear {{candidate_name}},\n\nWe are pleased to invite you...",
                "variables": {
                    "candidate_name": "Candidate name",
                    "company_name": "Company name",
                    "interview_date": "Interview date"
                },
                "is_active": True,
                "language": "en",
                "created_by": "user123",
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": "2024-01-25T00:00:00Z",
            },
        )

    except Exception as e:
        logger.error(f"Error getting template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}",
        ) from e


@router.put("/{template_id}", tags=["Communication Templates"])
async def update_template(
    template_id: str, request: TemplateUpdate
) -> JSONResponse:
    """
    Update a communication template.

    Args:
        template_id: Unique identifier of the template
        request: Update request with fields to modify

    Returns:
        JSON response with updated template

    Raises:
        HTTPException(404): If template is not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"name": "Updated Interview Invitation", "is_active": False}
        >>> response = requests.put(
        ...     "http://localhost:8000/api/communication-templates/123",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Updating template: {template_id}")

        # Validate template type if provided
        if request.type is not None:
            valid_types = ["email", "sms", "phone"]
            if request.type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Type must be one of: {', '.join(valid_types)}",
                )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": template_id,
                "organization_id": "org123",
                "name": request.name if request.name is not None else "Interview Invitation",
                "type": request.type if request.type is not None else "email",
                "subject": request.subject if request.subject is not None else "Interview Invitation - {{company_name}}",
                "body": request.body if request.body is not None else "Dear {{candidate_name}}...",
                "variables": request.variables if request.variables is not None else {},
                "is_active": request.is_active if request.is_active is not None else True,
                "language": request.language if request.language is not None else "en",
                "created_by": "user123",
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": "2024-01-25T00:00:00Z",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}",
        ) from e


@router.delete("/{template_id}", tags=["Communication Templates"])
async def delete_template(template_id: str) -> JSONResponse:
    """
    Delete a communication template.

    Args:
        template_id: Unique identifier of the template

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If template is not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/communication-templates/123")
        >>> response.json()
        {"message": "Template deleted successfully"}
    """
    try:
        logger.info(f"Deleting template: {template_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Template {template_id} deleted successfully"},
        )

    except Exception as e:
        logger.error(f"Error deleting template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}",
        ) from e


@router.post("/{template_id}/preview", tags=["Communication Templates"])
async def preview_template(
    template_id: str, request: TemplatePreviewRequest
) -> JSONResponse:
    """
    Preview a communication template with variable substitution.

    This endpoint renders the template with provided variable values,
    allowing users to preview the final content before sending.

    Args:
        template_id: Unique identifier of the template
        request: Preview request with variable values

    Returns:
        JSON response with rendered subject and body

    Raises:
        HTTPException(404): If template is not found
        HTTPException(500): If preview generation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "variables": {
        ...         "candidate_name": "John Doe",
        ...         "company_name": "Acme Corp",
        ...         "interview_date": "2024-02-01"
        ...     }
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/communication-templates/123/preview",
        ...     json=data
        ... )
        >>> response.json()
        {
            "subject": "Interview Invitation - Acme Corp",
            "body": "Dear John Doe,\\n\\nWe are pleased to invite you...",
            "missing_variables": []
        }
    """
    try:
        logger.info(f"Previewing template: {template_id}")

        # For now, use placeholder template data
        # Database integration will be added in a later subtask when we have async session setup
        template_subject = "Interview Invitation - {{company_name}}"
        template_body = "Dear {{candidate_name}},\n\nWe are pleased to invite you to interview for the position at {{company_name}} on {{interview_date}}.\n\nBest regards"

        # Extract expected variables from template
        subject_vars = _extract_template_variables(template_subject)
        body_vars = _extract_template_variables(template_body)
        all_vars = set(subject_vars + body_vars)

        # Find missing variables
        provided_vars = set(request.variables.keys())
        missing_vars = list(all_vars - provided_vars)

        # Substitute variables
        rendered_subject = _substitute_variables(template_subject, request.variables)
        rendered_body = _substitute_variables(template_body, request.variables)

        response_data = {
            "subject": rendered_subject,
            "body": rendered_body,
            "missing_variables": missing_vars,
        }

        logger.info(f"Generated preview for template: {template_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error previewing template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview template: {str(e)}",
        ) from e
