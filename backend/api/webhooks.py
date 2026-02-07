"""
Webhook endpoints for receiving real-time updates from external HRIS/ATS platforms.

This module provides endpoints for:
- Receiving webhook events from Workday, Greenhouse, Lever, BambooHR, and Ashby
- Validating webhook signatures for security
- Processing platform-specific event formats
- Logging webhook events for audit and debugging
- Triggering sync operations based on webhook events

Supports real-time data synchronization from external systems.
"""
import logging
import hmac
import hashlib
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.integration import Integration, IntegrationPlatform, IntegrationStatus
from models.sync_log import SyncLog, SyncType, SyncStatus
from models.audit_log import AuditActionType
from utils.audit_logger import log_audit_event, get_request_context

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class WebhookEventRequest(BaseModel):
    """Base model for webhook event data."""

    event: str = Field(..., description="Event type (e.g., 'candidate.updated', 'employee.created')")
    data: Dict[str, Any] = Field(..., description="Event payload data")
    timestamp: Optional[str] = Field(None, description="Event timestamp from platform")
    platform: Optional[str] = Field(None, description="Platform identifier (optional, inferred from URL)")


class WebhookResponse(BaseModel):
    """Response model for webhook endpoints."""

    success: bool = Field(..., description="Whether webhook was processed successfully")
    message: str = Field(..., description="Response message")
    event_id: Optional[str] = Field(None, description="Internal event ID for tracking")


class WebhookValidationRequest(BaseModel):
    """Request model for manual webhook validation testing."""

    platform: str = Field(..., description="Platform to validate against")
    payload: Dict[str, Any] = Field(..., description="Webhook payload to validate")
    signature: Optional[str] = Field(None, description="Webhook signature if available")


class WebhookValidationResponse(BaseModel):
    """Response model for webhook validation."""

    valid: bool = Field(..., description="Whether webhook payload is valid")
    platform: str = Field(..., description="Platform that was validated")
    message: str = Field(..., description="Validation result message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional validation details")


async def _verify_webhook_signature(
    payload: bytes,
    signature: Optional[str],
    secret: Optional[str],
    platform: IntegrationPlatform
) -> bool:
    """
    Verify webhook signature for security.

    Args:
        payload: Raw request payload bytes
        signature: Signature from request headers
        secret: Webhook secret from integration config
        platform: Platform type for signature algorithm

    Returns:
        True if signature is valid or signature verification is not required
    """
    if not signature:
        logger.warning(f"Missing signature for {platform.value} webhook")
        return False

    if not secret:
        logger.warning(f"No webhook secret configured for {platform.value}")
        return False

    try:
        # Different platforms use different signature formats
        if platform == IntegrationPlatform.GREENHOUSE:
            # Greenhouse uses HMAC-SHA256
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            # Greenhouse sends signature as "sha256=<hex>"
            if signature.startswith("sha256="):
                signature = signature[7:]
            return hmac.compare_digest(signature, expected_signature)

        elif platform == IntegrationPlatform.LEVER:
            # Lever uses HMAC-SHA256
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected_signature)

        elif platform == IntegrationPlatform.WORKDAY:
            # Workday uses HMAC-SHA256
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected_signature)

        elif platform == IntegrationPlatform.BAMBOOHR:
            # BambooHR uses HMAC-SHA256
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected_signature)

        elif platform == IntegrationPlatform.ASHBY:
            # Ashby uses HMAC-SHA256
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected_signature)

        else:
            logger.warning(f"Signature verification not implemented for {platform.value}")
            return True

    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}", exc_info=True)
        return False


async def _process_webhook_event(
    platform: IntegrationPlatform,
    event_type: str,
    event_data: Dict[str, Any],
    integration_id: UUID,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Process webhook event and trigger appropriate actions.

    Args:
        platform: Platform that sent the webhook
        event_type: Type of event (e.g., 'candidate.updated')
        event_data: Event payload data
        integration_id: Integration ID that received the webhook
        db: Database session

    Returns:
        Processing result metadata
    """
    try:
        logger.info(
            f"Processing {platform.value} webhook event: {event_type} "
            f"(integration: {integration_id})"
        )

        # Map webhook events to sync types
        sync_type = None
        should_trigger_sync = False

        # Candidate-related events
        if "candidate" in event_type.lower():
            if "created" in event_type.lower() or "applied" in event_type.lower():
                sync_type = SyncType.INCREMENTAL_SYNC
                should_trigger_sync = True
            elif "updated" in event_type.lower() or "stage" in event_type.lower():
                sync_type = SyncType.INCREMENTAL_SYNC
                should_trigger_sync = True
            elif "deleted" in event_type.lower() or "removed" in event_type.lower():
                sync_type = SyncType.INCREMENTAL_SYNC
                should_trigger_sync = True

        # Employee-related events
        elif "employee" in event_type.lower():
            if "created" in event_type.lower() or "hired" in event_type.lower():
                sync_type = SyncType.INCREMENTAL_SYNC
                should_trigger_sync = True
            elif "updated" in event_type.lower():
                sync_type = SyncType.INCREMENTAL_SYNC
                should_trigger_sync = True
            elif "terminated" in event_type.lower():
                sync_type = SyncType.INCREMENTAL_SYNC
                should_trigger_sync = True

        # Vacancy/Job-related events
        elif "vacancy" in event_type.lower() or "job" in event_type.lower():
            if "created" in event_type.lower() or "opened" in event_type.lower():
                sync_type = SyncType.INCREMENTAL_SYNC
                should_trigger_sync = True
            elif "updated" in event_type.lower() or "closed" in event_type.lower():
                sync_type = SyncType.INCREMENTAL_SYNC
                should_trigger_sync = True

        # If event indicates data changes, trigger incremental sync
        if should_trigger_sync and sync_type:
            # Check if there's already a sync in progress
            existing_sync_query = select(SyncLog).where(
                SyncLog.integration_id == integration_id,
                SyncLog.status.in_([SyncStatus.PENDING, SyncStatus.RUNNING])
            ).order_by(SyncLog.created_at.desc())

            existing_sync_result = await db.execute(existing_sync_query)
            existing_sync = existing_sync_result.first()

            if existing_sync:
                logger.info(
                    f"Sync already in progress for integration {integration_id}, "
                    f"not triggering new sync from webhook"
                )
                return {
                    "sync_triggered": False,
                    "reason": "Sync already in progress",
                }

            # Create new sync log entry
            new_sync = SyncLog(
                integration_id=integration_id,
                sync_type=sync_type,
                status=SyncStatus.PENDING,
                records_processed=0,
                records_successful=0,
                records_failed=0,
                sync_metadata={
                    "triggered_by": "webhook",
                    "webhook_event": event_type,
                    "webhook_data": event_data,
                },
            )

            db.add(new_sync)
            await db.commit()
            await db.refresh(new_sync)

            logger.info(
                f"Triggered {sync_type.value} sync from webhook event {event_type} "
                f"(sync_id: {new_sync.id})"
            )

            # TODO: Trigger Celery task for actual sync execution
            # This will be implemented in phase-4 (worker tasks)
            # Example: sync_integration_task.delay(str(new_sync.id))

            return {
                "sync_triggered": True,
                "sync_id": str(new_sync.id),
                "sync_type": sync_type.value,
            }

        return {
            "sync_triggered": False,
            "reason": "Event type does not require sync",
        }

    except Exception as e:
        logger.error(f"Error processing webhook event: {e}", exc_info=True)
        return {
            "sync_triggered": False,
            "error": str(e),
        }


@router.post(
    "/{platform}",
    response_model=WebhookResponse,
    tags=["Webhooks"],
)
async def receive_webhook(
    request: Request,
    platform: str,
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    x_hub_signature: Optional[str] = Header(None, alias="X-Hub-Signature"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Receive webhook events from external HRIS/ATS platforms.

    This endpoint accepts real-time webhook notifications from supported platforms:
    - Workday: candidate and employee events
    - Greenhouse: candidate application and stage changes
    - Lever: candidate and opportunity updates
    - BambooHR: employee data changes
    - Ashby: candidate and application events

    Webhooks are validated using signature verification when available.

    Args:
        request: FastAPI request object
        platform: Platform identifier (workday, greenhouse, lever, bamboohr, ashby)
        x_webhook_signature: Webhook signature header (varies by platform)
        x_hub_signature: GitHub-style signature header
        x_hub_signature_256: GitHub-style SHA256 signature header
        db: Database session

    Returns:
        JSON response acknowledging webhook receipt

    Raises:
        HTTPException(400): Invalid platform
        HTTPException(401): Signature verification failed
        HTTPException(404): No active integration found for platform
        HTTPException(500): Webhook processing failed

    Examples:
        >>> import requests
        >>> webhook_data = {
        ...     "event": "candidate.updated",
        ...     "data": {"candidate_id": "123", "name": "John Doe"}
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/webhooks/greenhouse",
        ...     json=webhook_data,
        ...     headers={"X-Webhook-Signature": "sha256=..."}
        ... )
    """
    try:
        # Normalize platform name
        platform_normalized = platform.lower().strip()

        # Map to enum
        platform_map = {
            "workday": IntegrationPlatform.WORKDAY,
            "greenhouse": IntegrationPlatform.GREENHOUSE,
            "lever": IntegrationPlatform.LEVER,
            "bamboohr": IntegrationPlatform.BAMBOOHR,
            "ashby": IntegrationPlatform.ASHBY,
        }

        if platform_normalized not in platform_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform}. Supported platforms: {', '.join(platform_map.keys())}",
            )

        platform_enum = platform_map[platform_normalized]

        # Get raw payload for signature verification
        raw_payload = await request.body()

        # Parse request body
        try:
            webhook_data = await request.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON payload: {str(e)}",
            )

        # Validate using request model
        try:
            webhook_event = WebhookEventRequest(**webhook_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid webhook data format: {str(e)}",
            )

        # Find active integration for this platform
        # TODO: Handle multiple integrations per platform
        integration_query = select(Integration).where(
            Integration.platform == platform_enum,
            Integration.status == IntegrationStatus.ACTIVE
        ).order_by(Integration.created_at.desc())

        integration_result = await db.execute(integration_query)
        integration = integration_result.scalar_one_or_none()

        if not integration:
            logger.warning(f"No active integration found for platform: {platform_enum.value}")
            # For security, still return success but log the issue
            # This prevents information leakage about configured integrations
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Webhook received (no active integration)",
                    "event_id": None,
                },
            )

        # Verify webhook signature if secret is configured
        webhook_secret = integration.credentials.get("webhook_secret")
        signature = x_webhook_signature or x_hub_signature or x_hub_signature_256

        if webhook_secret and signature:
            signature_valid = await _verify_webhook_signature(
                raw_payload,
                signature,
                webhook_secret,
                platform_enum
            )

            if not signature_valid:
                logger.warning(
                    f"Invalid webhook signature for platform {platform_enum.value} "
                    f"(integration: {integration.id})"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature",
                )

        # Log audit event for webhook receipt
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.INTEGRATION_UPDATED,  # Using existing audit type
            entity_type="webhook",
            entity_id=integration.id,
            ip_address=ip_address,
            user_agent=user_agent,
            after_value={
                "platform": platform_enum.value,
                "event": webhook_event.event,
                "integration_id": str(integration.id),
            },
        )

        # Process the webhook event
        processing_result = await _process_webhook_event(
            platform_enum,
            webhook_event.event,
            webhook_event.data,
            integration.id,
            db
        )

        logger.info(
            f"Webhook processed successfully: {platform_enum.value} - {webhook_event.event} "
            f"(integration: {integration.id})"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": f"Webhook received and processed for {platform_enum.value}",
                "event_id": processing_result.get("sync_id"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        ) from e


@router.post(
    "/validate",
    response_model=WebhookValidationResponse,
    tags=["Webhooks"],
)
async def validate_webhook(
    request: Request,
    validation: WebhookValidationRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Validate a webhook payload manually (for testing and debugging).

    This endpoint allows manual validation of webhook payloads without actually
    processing them. Useful for testing webhook integrations and debugging issues.

    Args:
        request: FastAPI request object
        validation: Validation request with platform, payload, and optional signature
        db: Database session

    Returns:
        JSON response with validation result

    Raises:
        HTTPException(400): Invalid platform or payload

    Examples:
        >>> import requests
        >>> validation_data = {
        ...     "platform": "greenhouse",
        ...     "payload": {"event": "candidate.updated", "data": {}},
        ...     "signature": "sha256=..."
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/webhooks/validate",
        ...     json=validation_data
        ... )
    """
    try:
        # Normalize platform name
        platform_normalized = validation.platform.lower().strip()

        # Map to enum
        platform_map = {
            "workday": IntegrationPlatform.WORKDAY,
            "greenhouse": IntegrationPlatform.GREENHOUSE,
            "lever": IntegrationPlatform.LEVER,
            "bamboohr": IntegrationPlatform.BAMBOOHR,
            "ashby": IntegrationPlatform.ASHBY,
        }

        if platform_normalized not in platform_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {validation.platform}",
            )

        platform_enum = platform_map[platform_normalized]

        # Validate payload structure
        try:
            webhook_event = WebhookEventRequest(**validation.payload)
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "valid": False,
                    "platform": validation.platform,
                    "message": f"Invalid payload structure: {str(e)}",
                    "details": {"error": str(e)},
                },
            )

        # Find active integration for signature validation
        integration_query = select(Integration).where(
            Integration.platform == platform_enum,
            Integration.status == IntegrationStatus.ACTIVE
        ).order_by(Integration.created_at.desc())

        integration_result = await db.execute(integration_query)
        integration = integration_result.scalar_one_or_none()

        validation_details = {
            "event_type": webhook_event.event,
            "payload_size": len(str(validation.payload)),
            "integration_found": integration is not None,
        }

        # Validate signature if provided
        if validation.signature and integration:
            webhook_secret = integration.credentials.get("webhook_secret")
            if webhook_secret:
                # Create a mock payload bytes
                import json
                payload_bytes = json.dumps(validation.payload).encode()

                signature_valid = await _verify_webhook_signature(
                    payload_bytes,
                    validation.signature,
                    webhook_secret,
                    platform_enum
                )

                validation_details["signature_valid"] = signature_valid

                if not signature_valid:
                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content={
                            "valid": False,
                            "platform": validation.platform,
                            "message": "Signature validation failed",
                            "details": validation_details,
                        },
                    )

        logger.info(
            f"Webhook validation successful for platform {validation.platform}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "valid": True,
                "platform": validation.platform,
                "message": "Webhook payload is valid",
                "details": validation_details,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate webhook: {str(e)}",
        ) from e


@router.get(
    "/",
    tags=["Webhooks"],
)
async def list_webhook_endpoints(
    request: Request
) -> JSONResponse:
    """
    List available webhook endpoints.

    Returns a list of supported webhook platforms and their endpoint URLs.
    Useful for configuring external systems to send webhooks.

    Returns:
        JSON response with list of webhook endpoints

    Examples:
        >>> response = requests.get("http://localhost:8000/api/webhooks/")
        >>> endpoints = response.json()
        >>> {
        ...     "platforms": [
        ...         {"platform": "workday", "url": "/api/webhooks/workday"},
        ...         {"platform": "greenhouse", "url": "/api/webhooks/greenhouse"},
        ...         ...
        ...     ]
        ... }
    """
    # Get base URL from request
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    platforms = [
        {
            "platform": "workday",
            "url": f"{base_url}/api/webhooks/workday",
            "description": "Workday HRIS webhooks for employee and candidate events",
        },
        {
            "platform": "greenhouse",
            "url": f"{base_url}/api/webhooks/greenhouse",
            "description": "Greenhouse ATS webhooks for candidate and application events",
        },
        {
            "platform": "lever",
            "url": f"{base_url}/api/webhooks/lever",
            "description": "Lever ATS webhooks for candidate and opportunity events",
        },
        {
            "platform": "bamboohr",
            "url": f"{base_url}/api/webhooks/bamboohr",
            "description": "BambooHR HRIS webhooks for employee data events",
        },
        {
            "platform": "ashby",
            "url": f"{base_url}/api/webhooks/ashby",
            "description": "Ashby ATS webhooks for candidate and application events",
        },
    ]

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "platforms": platforms,
            "total": len(platforms),
        },
    )
