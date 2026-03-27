"""
Pydantic schemas for model approval workflow requests/responses.

This module provides schema definitions for managing model deployment approval
workflows, including creating requests, reviewing/approving/rejecting requests,
and tracking approval history with audit trails.
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """Status of a model approval request in its lifecycle."""

    PENDING = "pending"  # Awaiting review
    APPROVED = "approved"  # Approved for deployment
    REJECTED = "rejected"  # Rejected by reviewer
    DEPLOYED = "deployed"  # Successfully deployed to production
    CANCELLED = "cancelled"  # Cancelled by requester


class ApprovalRequestCreate(BaseModel):
    """Request model for creating a model deployment approval request."""

    model_version_id: str = Field(
        ..., description="UUID of the model version to request deployment for"
    )
    justification: Optional[str] = Field(
        None, description="Explanation of why this model should be deployed"
    )
    target_environment: str = Field(
        "staging",
        description="Target environment for deployment (staging, production)",
    )
    organization_id: str = Field(
        ..., description="Organization that owns this approval request"
    )
    requested_by: str = Field(
        ..., description="User ID who submitted the deployment request"
    )


class ApprovalRequestUpdate(BaseModel):
    """Request model for updating an approval request (before review)."""

    justification: Optional[str] = Field(
        None, description="Updated justification for the deployment"
    )
    target_environment: Optional[str] = Field(
        None, description="Updated target environment"
    )


class ApprovalActionRequest(BaseModel):
    """Request model for approving or rejecting an approval request."""

    review_notes: Optional[str] = Field(
        None, description="Reviewer's feedback or reasons for the decision"
    )
    reviewed_by: str = Field(
        ..., description="User ID of the reviewer performing this action"
    )


class ApprovalRequestResponse(BaseModel):
    """Response model for a single approval request."""

    id: str = Field(..., description="Unique identifier for the approval request")
    model_version_id: str = Field(
        ..., description="UUID of the model version being requested"
    )
    status: ApprovalStatus = Field(..., description="Current approval status")
    requested_by: str = Field(..., description="User ID who submitted the request")
    reviewed_by: Optional[str] = Field(
        None, description="User ID who reviewed the request"
    )
    requested_at: Optional[str] = Field(
        None, description="ISO timestamp when the request was submitted"
    )
    reviewed_at: Optional[str] = Field(
        None, description="ISO timestamp when the request was reviewed"
    )
    justification: Optional[str] = Field(
        None, description="Explanation for why this model should be deployed"
    )
    review_notes: Optional[str] = Field(
        None, description="Reviewer's feedback or reasons for rejection"
    )
    target_environment: str = Field(
        ..., description="Target environment for deployment"
    )
    organization_id: str = Field(
        ..., description="Organization that owns this approval request"
    )
    created_at: str = Field(..., description="ISO timestamp when record was created")
    updated_at: str = Field(
        ..., description="ISO timestamp when record was last updated"
    )


class ApprovalRequestListResponse(BaseModel):
    """Response model for listing approval requests."""

    requests: List[ApprovalRequestResponse] = Field(
        ..., description="List of approval request entries"
    )
    total_count: int = Field(..., description="Total number of approval requests")


class ApprovalRequestDetailResponse(BaseModel):
    """Detailed response model for a single approval request with model version info."""

    approval_request: ApprovalRequestResponse = Field(
        ..., description="The approval request details"
    )
    model_version: dict = Field(
        ..., description="Details of the associated model version"
    )


class ApprovalAuditLogEntry(BaseModel):
    """Single entry in the approval workflow audit log."""

    id: str = Field(..., description="Unique identifier for the audit entry")
    approval_request_id: str = Field(
        ..., description="UUID of the related approval request"
    )
    action: str = Field(
        ...,
        description="Action performed (created, approved, rejected, deployed, cancelled)",
    )
    performed_by: str = Field(..., description="User ID who performed the action")
    previous_status: Optional[ApprovalStatus] = Field(
        None, description="Status before the action"
    )
    new_status: ApprovalStatus = Field(..., description="Status after the action")
    notes: Optional[str] = Field(None, description="Additional notes about the action")
    timestamp: str = Field(..., description="ISO timestamp when the action occurred")


class ApprovalAuditLogResponse(BaseModel):
    """Response model for approval workflow audit log."""

    entries: List[ApprovalAuditLogEntry] = Field(
        ..., description="List of audit log entries"
    )
    total_count: int = Field(..., description="Total number of audit entries")
    approval_request_id: str = Field(
        ..., description="UUID of the approval request this log belongs to"
    )


class ApprovalStatsResponse(BaseModel):
    """Response model for approval workflow statistics."""

    total_requests: int = Field(..., description="Total number of approval requests")
    pending_requests: int = Field(..., description="Number of pending requests")
    approved_requests: int = Field(..., description="Number of approved requests")
    rejected_requests: int = Field(..., description="Number of rejected requests")
    deployed_requests: int = Field(..., description="Number of deployed requests")
    cancelled_requests: int = Field(..., description="Number of cancelled requests")
    average_approval_time_hours: Optional[float] = Field(
        None, description="Average time from request to approval in hours"
    )
    approval_rate: float = Field(
        ..., description="Percentage of approved requests (0-100)"
    )
    period_start: Optional[str] = Field(
        None, description="Start date of the statistics period (ISO 8601)"
    )
    period_end: Optional[str] = Field(
        None, description="End date of the statistics period (ISO 8601)"
    )


class ApprovalDashboardResponse(BaseModel):
    """Response model for the approval workflow dashboard."""

    pending_requests: List[ApprovalRequestResponse] = Field(
        ..., description="List of pending approval requests awaiting review"
    )
    recent_approvals: List[ApprovalRequestResponse] = Field(
        ..., description="Recently approved requests"
    )
    recent_rejections: List[ApprovalRequestResponse] = Field(
        ..., description="Recently rejected requests"
    )
    stats: ApprovalStatsResponse = Field(
        ..., description="Approval workflow statistics"
    )
    user_pending_count: int = Field(
        ..., description="Number of pending requests submitted by the current user"
    )
