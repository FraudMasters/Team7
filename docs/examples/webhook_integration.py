#!/usr/bin/env python3
"""
AgentHR Webhook Integration Example

This example demonstrates how to:
1. Create a webhook subscription
2. Set up an HTTP endpoint to receive webhook events
3. Verify webhook signatures for security
4. Handle different event types
5. Respond to webhook deliveries

Requirements:
    pip install fastapi uvicorn pydantic

Usage:
    # Start the webhook receiver server
    python webhook_integration.py --port 8080 --secret your-webhook-secret

    # In another terminal, use ngrok or webhook.site to test
    # Then create a webhook subscription pointing to your endpoint
"""
import argparse
import hashlib
import hmac
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn


# ===== Logging Configuration =====

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ===== Webhook Event Models =====

class WebhookEvent(BaseModel):
    """Base model for webhook events."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event")
    timestamp: str = Field(..., description="Event timestamp (ISO 8601)")
    data: Dict[str, Any] = Field(..., description="Event payload data")


class CandidateCreatedEvent(WebhookEvent):
    """Event fired when a new candidate (resume) is created."""

    event_type: str = "candidate.created"
    data: Dict[str, Any] = Field(
        ...,
        description="Contains: resume_id, filename, parsed_data"
    )


class StageChangedEvent(WebhookEvent):
    """Event fired when a candidate moves to a different workflow stage."""

    event_type: str = "stage.changed"
    data: Dict[str, Any] = Field(
        ...,
        description="Contains: candidate_id, previous_stage, new_stage, vacancy_id"
    )


class RankingCreatedEvent(WebhookEvent):
    """Event fired when a candidate is ranked against a vacancy."""

    event_type: str = "ranking.created"
    data: Dict[str, Any] = Field(
        ...,
        description="Contains: vacancy_id, resume_id, score, explanation"
    )


# ===== Webhook Signature Verification =====

def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """
    Verify HMAC-SHA256 webhook signature.

    AgentHR signs webhook payloads using HMAC-SHA256 with your secret.
    The signature is sent in the X-Webhook-Signature header.

    Args:
        payload: Raw request body bytes
        signature: Signature from X-Webhook-Signature header
        secret: Your webhook secret

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature:
        return False

    # Signature format: "sha256=<hex_digest>"
    if not signature.startswith("sha256="):
        return False

    received_hash = signature[7:]  # Remove "sha256=" prefix

    # Compute expected hash
    expected_hash = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(received_hash, expected_hash)


# ===== Webhook Handler =====

class WebhookHandler:
    """
    Base webhook event handler with routing to specific handlers.

    Subclass this and override the event-specific methods to customize
    behavior for each event type.
    """

    async def handle_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """
        Route webhook event to appropriate handler.

        Args:
            event: Webhook event

        Returns:
            Response data to send back to AgentHR
        """
        event_type = event.event_type

        # Route to specific handler
        handler = getattr(self, f"handle_{event_type.replace('.', '_')}", None)
        if handler:
            return await handler(event)

        # Default handler
        return await self_handle_default(event)

    async def handle_candidate_created(
        self,
        event: CandidateCreatedEvent,
    ) -> Dict[str, Any]:
        """
        Handle candidate.created event.

        Override this method to customize behavior.
        """
        logger.info(f"New candidate created: {event.data.get('resume_id')}")
        # Custom logic here (e.g., send Slack notification, update CRM)
        return {"status": "processed", "message": "Candidate created event handled"}

    async def handle_stage_changed(
        self,
        event: StageChangedEvent,
    ) -> Dict[str, Any]:
        """
        Handle stage.changed event.

        Override this method to customize behavior.
        """
        candidate_id = event.data.get("candidate_id")
        prev_stage = event.data.get("previous_stage")
        new_stage = event.data.get("new_stage")

        logger.info(f"Candidate {candidate_id} moved from {prev_stage} to {new_stage}")

        # Example: Send notification when candidate reaches interview stage
        if new_stage == "interview":
            await self._send_interview_notification(event.data)

        return {"status": "processed", "message": "Stage changed event handled"}

    async def handle_ranking_created(
        self,
        event: RankingCreatedEvent,
    ) -> Dict[str, Any]:
        """
        Handle ranking.created event.

        Override this method to customize behavior.
        """
        score = event.data.get("score", 0)
        vacancy_id = event.data.get("vacancy_id")

        logger.info(f"New ranking for vacancy {vacancy_id}: {score:.1%}")

        # Example: Auto-move high-scoring candidates
        if score > 0.8:
            await self._auto_move_high_scorer(event.data)

        return {"status": "processed", "message": "Ranking created event handled"}

    async def _handle_default(self, event: WebhookEvent) -> Dict[str, Any]:
        """Default handler for unhandled event types."""
        logger.info(f"Received event: {event.event_type}")
        return {"status": "processed", "message": "Event logged"}

    async def _send_interview_notification(self, data: Dict[str, Any]) -> None:
        """
        Example: Send notification when candidate reaches interview stage.

        In production, this might:
        - Send a Slack message
        - Send an email
        - Update an external system
        - Trigger a workflow
        """
        # Placeholder for notification logic
        logger.info(f"Interview notification for candidate: {data.get('candidate_id')}")

    async def _auto_move_high_scorer(self, data: Dict[str, Any]) -> None:
        """
        Example: Auto-move high-scoring candidates to next stage.

        In production, this might:
        - Call the AgentHR API to move the candidate
        - Send a notification
        - Update tracking systems
        """
        # Placeholder for auto-move logic
        logger.info(f"Auto-moving high scorer: {data.get('resume_id')}")


# ===== FastAPI Webhook Receiver App =====

def create_webhook_app(
    secret: str,
    handler: Optional[WebhookHandler] = None,
) -> FastAPI:
    """
    Create FastAPI application for receiving webhooks.

    Args:
        secret: Webhook secret for signature verification
        handler: Optional custom webhook handler

    Returns:
        FastAPI application
    """

    app = FastAPI(
        title="AgentHR Webhook Receiver",
        description="Receives and processes webhook events from AgentHR",
        version="1.0.0",
    )

    webhook_handler = handler or WebhookHandler()

    @app.get("/")
    async def root() -> Dict[str, Any]:
        """Health check endpoint."""
        return {
            "service": "AgentHR Webhook Receiver",
            "status": "running",
            "timestamp": datetime.utcnow().isoformat(),
        }

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        """Health check endpoint for load balancers."""
        return {"status": "healthy"}

    @app.post("/webhook")
    async def receive_webhook(request: Request) -> JSONResponse:
        """
        Receive and process webhook events from AgentHR.

        This endpoint:
        1. Verifies the webhook signature
        2. Parses the event payload
        3. Routes to appropriate handler
        4. Returns success/error response

        Returns:
            JSONResponse with status
        """
        # Get signature from headers
        signature = request.headers.get("X-Webhook-Signature", "")
        event_id = request.headers.get("X-Webhook-Event-ID", "")
        event_type = request.headers.get("X-Webhook-Event-Type", "")

        # Get raw payload for signature verification
        payload = await request.body()

        # Verify signature
        if not verify_webhook_signature(payload, signature, secret):
            logger.warning(f"Invalid signature for event {event_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )

        # Parse event
        try:
            event_data = json.loads(payload)
            event = WebhookEvent(**event_data)
        except Exception as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payload: {str(e)}",
            )

        # Log event
        logger.info(f"Received webhook: {event.event_type} (id={event_id})")

        # Handle event
        try:
            result = await webhook_handler.handle_webhook(event)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "received": True,
                    "event_id": event_id,
                    **result,
                },
            )
        except Exception as e:
            logger.error(f"Error handling webhook {event_id}: {e}")
            # Return 200 to acknowledge receipt (AgentHR will retry on 5xx)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "received": True,
                    "event_id": event_id,
                    "error": str(e),
                },
            )

    return app


# ===== Example: Custom Webhook Handler =====

class CustomWebhookHandler(WebhookHandler):
    """
    Example custom webhook handler with business logic.

    This demonstrates how to extend the base handler with custom
    behavior for specific events.
    """

    def __init__(self, agenthr_api_key: str):
        """
        Initialize custom handler.

        Args:
            agenthr_api_key: AgentHR API key for making API calls
        """
        self.api_key = agenthr_api_key

    async def handle_candidate_created(
        self,
        event: CandidateCreatedEvent,
    ) -> Dict[str, Any]:
        """
        Handle new candidate with custom logic.

        Example actions:
        1. Extract candidate details
        2. Send notification to recruiters
        3. Update external ATS/CRM
        4. Trigger custom workflows
        """
        resume_id = event.data.get("resume_id")
        parsed_data = event.data.get("parsed_data", {})

        name = parsed_data.get("name", "Unknown")
        email = parsed_data.get("email", "No email")
        skills = parsed_data.get("skills", [])

        logger.info(f"New candidate: {name} ({email})")
        logger.info(f"Skills: {', '.join(skills)}")

        # TODO: Implement your custom logic here
        # - Send Slack notification
        # - Add to CRM
        # - Send confirmation email

        return {
            "status": "processed",
            "message": f"Welcome email sent to {email}",
        }

    async def handle_stage_changed(
        self,
        event: StageChangedEvent,
    ) -> Dict[str, Any]:
        """Handle stage change with custom notifications."""

        new_stage = event.data.get("new_stage")

        # Send different notifications based on stage
        if new_stage == "interview":
            await self._notify_interview_scheduled(event.data)
        elif new_stage == "offer":
            await self._notify_offer_sent(event.data)
        elif new_stage == "hired":
            await self._notify_candidate_hired(event.data)
        elif new_stage == "rejected":
            await self._notify_candidate_rejected(event.data)

        return {
            "status": "processed",
            "message": f"Stage change notifications sent for {new_stage}",
        }

    async def _notify_interview_scheduled(self, data: Dict[str, Any]) -> None:
        """Notify team that interview is scheduled."""
        # TODO: Implement notification logic
        logger.info(f"Interview scheduled notification: {data.get('candidate_id')}")

    async def _notify_offer_sent(self, data: Dict[str, Any]) -> None:
        """Notify team that offer was sent."""
        # TODO: Implement notification logic
        logger.info(f"Offer sent notification: {data.get('candidate_id')}")

    async def _notify_candidate_hired(self, data: Dict[str, Any]) -> None:
        """Notify team that candidate was hired."""
        # TODO: Implement notification logic
        logger.info(f"Candidate hired notification: {data.get('candidate_id')}")

    async def _notify_candidate_rejected(self, data: Dict[str, Any]) -> None:
        """Notify team that candidate was rejected."""
        # TODO: Implement notification logic
        logger.info(f"Candidate rejected notification: {data.get('candidate_id')}")


# ===== CLI Interface =====

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AgentHR Webhook Integration Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start webhook receiver with default handler
  python webhook_integration.py --secret my-webhook-secret

  # Start webhook receiver with custom handler
  python webhook_integration.py \\
    --secret my-webhook-secret \\
    --api-key my-api-key \\
    --custom-handler

  # Use with ngrok for local testing
  ngrok http 8080
  # Then create webhook subscription pointing to ngrok URL
        """,
    )

    parser.add_argument(
        "--secret",
        required=True,
        help="Webhook secret for signature verification",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--api-key",
        help="AgentHR API key (required for custom handler)",
    )
    parser.add_argument(
        "--custom-handler",
        action="store_true",
        help="Use custom webhook handler with business logic",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )

    args = parser.parse_args()

    # Set log level
    log_level = getattr(logging, args.log_level)
    logging.getLogger().setLevel(log_level)

    # Create webhook handler
    handler = None
    if args.custom_handler:
        api_key = args.api_key or os.getenv("AGENTHR_API_KEY")
        if not api_key:
            print("Error: --api-key or AGENTHR_API_KEY required for custom handler", file=sys.stderr)
            return 1
        handler = CustomWebhookHandler(api_key)
        logger.info("Using custom webhook handler")
    else:
        logger.info("Using default webhook handler")

    # Create FastAPI app
    app = create_webhook_app(secret=args.secret, handler=handler)

    # Start server
    logger.info(f"Starting webhook receiver on {args.host}:{args.port}")
    logger.info(f"Webhook endpoint: http://{args.host}:{args.port}/webhook")
    logger.info("Press Ctrl+C to stop")

    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level=args.log_level.lower(),
        )
    except KeyboardInterrupt:
        logger.info("Webhook receiver stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
