"""
Inbound email webhook endpoints.

This module provides endpoints for receiving inbound emails from email service
providers (SendGrid, Mailgun, AWS SES, etc.) to process resume attachments
automatically.

Supports:
- Webhook reception from multiple email providers
- Attachment extraction and validation
- Automatic resume processing and candidate linking
"""
import logging
import base64
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for inbound email webhook payloads
class EmailAttachment(BaseModel):
    """Model for an email attachment."""

    filename: str = Field(..., description="Name of the attached file")
    content_type: str = Field(..., description="MIME type of the attachment")
    content: Optional[str] = Field(None, description="Base64-encoded file content")
    size: Optional[int] = Field(None, description="Size of the attachment in bytes")


class InboundEmailRequest(BaseModel):
    """
    Request model for inbound email webhooks.

    This model is designed to be flexible enough to accept payloads from
    various email providers (SendGrid, Mailgun, AWS SES, Postmark, etc.).
    """

    # Sender information
    from_email: EmailStr = Field(..., description="Email address of the sender", alias="from")
    from_name: Optional[str] = Field(None, description="Name of the sender")

    # Recipient information
    to: list[str] = Field(..., description="List of recipient email addresses")
    cc: list[str] = Field(default_factory=list, description="List of CC recipients")
    bcc: list[str] = Field(default_factory=list, description="List of BCC recipients")

    # Email content
    subject: Optional[str] = Field(None, description="Email subject line")
    text_body: Optional[str] = Field(None, description="Plain text email body", alias="text")
    html_body: Optional[str] = Field(None, description="HTML email body", alias="html")

    # Attachments
    attachments: list[EmailAttachment] = Field(
        default_factory=list,
        description="List of email attachments"
    )

    # Metadata
    message_id: Optional[str] = Field(None, description="Unique message identifier from email provider")
    received_at: Optional[str] = Field(None, description="Timestamp when email was received")
    provider: Optional[str] = Field(None, description="Email provider identifier (sendgrid, mailgun, ses, etc.)")
    spam_score: Optional[float] = Field(None, description="Spam score if available from provider")

    class Config:
        populate_by_name = True  # Allow both alias and field name


class InboundEmailResponse(BaseModel):
    """Response model for inbound email webhook."""

    message_id: str = Field(..., description="Unique identifier for this email processing request")
    status: str = Field(..., description="Processing status: accepted, processing, rejected")
    message: str = Field(..., description="Human-readable status message")
    attachments_received: int = Field(0, description="Number of attachments received")
    attachments_queued: int = Field(0, description="Number of valid resume attachments queued for processing")
    resume_formats_rejected: int = Field(0, description="Number of attachments rejected due to format")
    task_id: Optional[str] = Field(None, description="Celery task ID for tracking processing")
    vacancy_id: Optional[str] = Field(None, description="Vacancy ID extracted from recipient email address")


class WebhookStatusResponse(BaseModel):
    """Response model for webhook status check."""

    webhook_enabled: bool = Field(..., description="Whether the inbound email webhook is enabled")
    supported_providers: list[str] = Field(..., description="List of supported email providers")
    supported_formats: list[str] = Field(..., description="List of supported resume file formats")
    last_received: Optional[str] = Field(None, description="ISO 8601 timestamp of last received email")
    emails_processed_today: int = Field(0, description="Number of emails processed today")
    resumes_extracted_today: int = Field(0, description="Number of resumes extracted today")


# Allowed file types for resume attachments
ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx", ".doc"}
MAX_ATTACHMENT_SIZE_MB = 10
MAX_ATTACHMENTS_PER_EMAIL = 20


def _extract_vacancy_id_from_email(email_address: str) -> Optional[str]:
    """
    Extract vacancy ID from a vacancy-specific email address.

    Email format: vacancy-{vacancy_id}@resumes.agenthr.com
    or: resumes+{vacancy_id}@agenthr.com

    Args:
        email_address: The recipient email address

    Returns:
        Vacancy ID if found, None otherwise
    """
    import re

    # Pattern 1: vacancy-{uuid}@resumes.agenthr.com
    pattern1 = r"vacancy-([a-f0-9\-]+)@"
    match1 = re.search(pattern1, email_address.lower())
    if match1:
        return match1.group(1)

    # Pattern 2: resumes+{uuid}@agenthr.com (plus addressing)
    pattern2 = r"resumes\+([a-f0-9\-]+)@"
    match2 = re.search(pattern2, email_address.lower())
    if match2:
        return match2.group(1)

    return None


def _validate_attachment(filename: str, content_type: str, size: Optional[int]) -> tuple[bool, str]:
    """
    Validate if an attachment is a valid resume file.

    Args:
        filename: Name of the attached file
        content_type: MIME type of the attachment
        size: Size in bytes (optional)

    Returns:
        Tuple of (is_valid, error_message)
    """
    from pathlib import Path

    # Check file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_RESUME_EXTENSIONS:
        return False, f"Unsupported file type: {file_ext}. Allowed types: {', '.join(ALLOWED_RESUME_EXTENSIONS)}"

    # Check size if provided
    if size is not None and size > MAX_ATTACHMENT_SIZE_MB * 1024 * 1024:
        return False, f"File too large: {size / 1024 / 1024:.1f}MB. Maximum allowed: {MAX_ATTACHMENT_SIZE_MB}MB"

    return True, ""


@router.post(
    "/inbound",
    response_model=InboundEmailResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Inbound Email"],
)
async def receive_inbound_email(
    request: Request,
    email: InboundEmailRequest,
) -> JSONResponse:
    """
    Receive and process inbound emails with resume attachments.

    This endpoint serves as a webhook for email service providers to deliver
    inbound emails. It validates attachments, extracts resumes, and queues
    them for processing.

    The endpoint accepts payloads from various email providers including:
    - SendGrid Inbound Parse
    - Mailgun Routes
    - AWS SES Receipt Rules
    - Postmark Inbound

    Args:
        request: FastAPI request object
        email: Inbound email payload with attachments

    Returns:
        JSON response with acceptance status and processing details

    Raises:
        HTTPException(400): If the email payload is invalid
        HTTPException(403): If the sender is blocked or spam score is too high
        HTTPException(413): If total attachment size exceeds limits
        HTTPException(500): If processing fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/email/inbound",
        ...     json={
        ...         "from": "recruiter@company.com",
        ...         "to": ["vacancy-123@resumes.agenthr.com"],
        ...         "subject": "Resume for Software Engineer position",
        ...         "text": "Please find attached resume...",
        ...         "attachments": [{
        ...             "filename": "resume.pdf",
        ...             "content_type": "application/pdf",
        ...             "content": "base64-encoded-content"
        ...         }]
        ...     }
        ... )
        >>> response.json()
        {
            "message_id": "email_20250103_123456_abc123",
            "status": "accepted",
            "message": "Email accepted for processing",
            "attachments_received": 1,
            "attachments_queued": 1,
            "resume_formats_rejected": 0
        }
    """
    try:
        # Generate unique message ID for tracking
        message_id = f"email_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        logger.info(
            f"Received inbound email from {email.from_email} "
            f"with {len(email.attachments)} attachments, message_id={message_id}"
        )

        # Check spam score threshold
        if email.spam_score is not None and email.spam_score > 5.0:
            logger.warning(
                f"Rejecting email with high spam score: {email.spam_score}, "
                f"from={email.from_email}, message_id={message_id}"
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "message_id": message_id,
                    "status": "rejected",
                    "message": "Email rejected due to high spam score",
                    "attachments_received": len(email.attachments),
                    "attachments_queued": 0,
                    "resume_formats_rejected": 0,
                }
            )

        # Check attachment count limit
        if len(email.attachments) > MAX_ATTACHMENTS_PER_EMAIL:
            logger.warning(
                f"Email exceeds attachment limit: {len(email.attachments)} > {MAX_ATTACHMENTS_PER_EMAIL}, "
                f"from={email.from_email}, message_id={message_id}"
            )
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "message_id": message_id,
                    "status": "rejected",
                    "message": f"Too many attachments. Maximum allowed: {MAX_ATTACHMENTS_PER_EMAIL}",
                    "attachments_received": len(email.attachments),
                    "attachments_queued": 0,
                    "resume_formats_rejected": 0,
                }
            )

        # Check if any recipient is a vacancy-specific address
        vacancy_id = None
        for recipient in email.to:
            extracted_id = _extract_vacancy_id_from_email(recipient)
            if extracted_id:
                vacancy_id = extracted_id
                logger.info(f"Detected vacancy ID {vacancy_id} from recipient {recipient}")
                break

        # Validate and categorize attachments
        valid_attachments = []
        rejected_count = 0

        for attachment in email.attachments:
            is_valid, error_msg = _validate_attachment(
                attachment.filename,
                attachment.content_type,
                attachment.size
            )

            if is_valid:
                valid_attachments.append(attachment)
                logger.debug(
                    f"Valid resume attachment: {attachment.filename}, "
                    f"content_type={attachment.content_type}"
                )
            else:
                rejected_count += 1
                logger.warning(
                    f"Rejected attachment: {attachment.filename}, reason: {error_msg}"
                )

        # Log processing summary
        logger.info(
            f"Email processing summary: message_id={message_id}, "
            f"from={email.from_email}, subject={email.subject}, "
            f"attachments={len(email.attachments)}, "
            f"valid={len(valid_attachments)}, rejected={rejected_count}, "
            f"vacancy_id={vacancy_id}"
        )

        # If no valid attachments, return early
        if not valid_attachments:
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "message_id": message_id,
                    "status": "accepted",
                    "message": "Email accepted but no valid resume attachments found",
                    "attachments_received": len(email.attachments),
                    "attachments_queued": 0,
                    "resume_formats_rejected": rejected_count,
                }
            )

        # Queue the email for async processing
        from tasks.email_resume_task import process_inbound_email

        # Prepare attachment data for Celery task (serialize to dict)
        attachment_data = []
        for attachment in valid_attachments:
            attachment_data.append({
                "filename": attachment.filename,
                "content_type": attachment.content_type,
                "content": attachment.content,  # Base64-encoded content
                "size": attachment.size,
            })

        # Dispatch the Celery task with vacancy_id for resume linking
        task = process_inbound_email.delay(
            message_id=message_id,
            from_email=str(email.from_email),
            from_name=email.from_name,
            to_addresses=email.to,
            subject=email.subject,
            text_body=email.text_body,
            html_body=email.html_body,
            attachments=attachment_data,
            vacancy_id=vacancy_id,
            organization_id=None,  # Will be determined from vacancy if available
            provider=email.provider,
            spam_score=email.spam_score,
            received_at=email.received_at,
        )

        logger.info(
            f"Dispatched email processing task {task.id} for message_id={message_id}, "
            f"vacancy_id={vacancy_id}, attachments={len(valid_attachments)}"
        )

        # Return acceptance with details about what will be processed
        response_data = {
            "message_id": message_id,
            "status": "accepted",
            "message": f"Email accepted for processing. {len(valid_attachments)} resume(s) queued.",
            "attachments_received": len(email.attachments),
            "attachments_queued": len(valid_attachments),
            "resume_formats_rejected": rejected_count,
            "task_id": task.id,
            "vacancy_id": vacancy_id,
        }

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error processing inbound email: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process inbound email: {str(e)}",
        ) from e


@router.get(
    "/status",
    response_model=WebhookStatusResponse,
    tags=["Inbound Email"],
)
async def get_webhook_status() -> JSONResponse:
    """
    Get inbound email webhook status and configuration.

    This endpoint returns information about the webhook configuration,
    including supported providers, file formats, and processing statistics.

    Returns:
        JSON response with webhook status and configuration

    Raises:
        HTTPException(500): If status retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/email/status")
        >>> response.json()
        {
            "webhook_enabled": true,
            "supported_providers": ["sendgrid", "mailgun", "ses", "postmark"],
            "supported_formats": [".pdf", ".docx", ".doc"],
            "last_received": "2025-01-03T12:30:00Z",
            "emails_processed_today": 45,
            "resumes_extracted_today": 62
        }
    """
    try:
        logger.info("Fetching inbound email webhook status")

        # TODO: Implement actual statistics retrieval from database
        # For now, return placeholder configuration data
        response_data = {
            "webhook_enabled": True,
            "supported_providers": [
                "sendgrid",
                "mailgun",
                "ses",
                "postmark",
                "sparkpost",
            ],
            "supported_formats": list(ALLOWED_RESUME_EXTENSIONS),
            "last_received": None,
            "emails_processed_today": 0,
            "resumes_extracted_today": 0,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving webhook status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve webhook status: {str(e)}",
        ) from e


@router.post(
    "/sendgrid",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Inbound Email"],
)
async def receive_sendgrid_webhook(request: Request) -> JSONResponse:
    """
    Receive inbound email from SendGrid Inbound Parse webhook.

    SendGrid posts form-encoded data with multipart attachments.
    This endpoint normalizes the payload and processes it.

    Args:
        request: FastAPI request object with form data

    Returns:
        JSON response with acceptance status

    Raises:
        HTTPException(400): If the payload is invalid
        HTTPException(500): If processing fails

    Example SendGrid payload (form-encoded):
        - from: sender email
        - to: recipient email
        - subject: email subject
        - text: plain text body
        - html: HTML body
        - attachment{n}: attachment files
    """
    try:
        # Parse form data from SendGrid
        form_data = await request.form()

        from_email = form_data.get("from", "")
        to_emails = [form_data.get("to", "")]
        subject = form_data.get("subject", "")
        text_body = form_data.get("text", "")
        html_body = form_data.get("html", "")

        # Extract attachments from form data
        attachments = []
        for key, value in form_data.items():
            if key.startswith("attachment") and hasattr(value, "filename"):
                attachments.append(EmailAttachment(
                    filename=value.filename or "unknown",
                    content_type=value.content_type or "application/octet-stream",
                ))

        logger.info(
            f"Received SendGrid webhook: from={from_email}, "
            f"to={to_emails}, attachments={len(attachments)}"
        )

        # Create normalized request and process
        normalized_email = InboundEmailRequest(
            from_email=from_email,
            to=to_emails,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            attachments=attachments,
            provider="sendgrid",
        )

        return await receive_inbound_email(request, normalized_email)

    except Exception as e:
        logger.error(f"Error processing SendGrid webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process SendGrid webhook: {str(e)}",
        ) from e


@router.post(
    "/mailgun",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Inbound Email"],
)
async def receive_mailgun_webhook(request: Request) -> JSONResponse:
    """
    Receive inbound email from Mailgun Routes webhook.

    Mailgun posts form-encoded data with attachments.
    This endpoint normalizes the payload and processes it.

    Args:
        request: FastAPI request object with form data

    Returns:
        JSON response with acceptance status

    Raises:
        HTTPException(400): If the payload is invalid
        HTTPException(500): If processing fails

    Example Mailgun payload (form-encoded):
        - from: sender email
        - recipient: recipient email
        - subject: email subject
        - body-plain: plain text body
        - body-html: HTML body
        - attachment{n}: attachment files
    """
    try:
        # Parse form data from Mailgun
        form_data = await request.form()

        from_email = form_data.get("from", "")
        to_emails = [form_data.get("recipient", "")]
        subject = form_data.get("subject", "")
        text_body = form_data.get("body-plain", "")
        html_body = form_data.get("body-html", "")

        # Extract spam score if available
        spam_score = None
        if "X-Mailgun-Sflag" in form_data:
            try:
                spam_score = float(form_data.get("X-Mailgun-Sscore", 0))
            except (ValueError, TypeError):
                pass

        # Extract attachments from form data
        attachments = []
        for key, value in form_data.items():
            if key.startswith("attachment") and hasattr(value, "filename"):
                attachments.append(EmailAttachment(
                    filename=value.filename or "unknown",
                    content_type=value.content_type or "application/octet-stream",
                ))

        logger.info(
            f"Received Mailgun webhook: from={from_email}, "
            f"to={to_emails}, attachments={len(attachments)}"
        )

        # Create normalized request and process
        normalized_email = InboundEmailRequest(
            from_email=from_email,
            to=to_emails,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            attachments=attachments,
            provider="mailgun",
            spam_score=spam_score,
        )

        return await receive_inbound_email(request, normalized_email)

    except Exception as e:
        logger.error(f"Error processing Mailgun webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Mailgun webhook: {str(e)}",
        ) from e
