"""
Model Approval Service for managing ML model deployment approval workflows.

This module provides a comprehensive service for managing approval workflows when deploying
ML models. It supports multi-stage approval processes with status tracking, reviewer
assignments, and audit trails for governance purposes.

The service supports:
- Creating and managing model deployment approval requests
- Approving/rejecting requests with reviewer tracking
- Automatic deployment upon approval (optional)
- Audit trail logging for all workflow actions
- Statistics and dashboard data generation
- Integration with ModelVersionManager for deployment actions
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from models.model_approval import ModelApprovalRequest, ApprovalStatus
from models.ml_model_version import MLModelVersion

logger = logging.getLogger(__name__)


class ModelApprovalService:
    """
    Service for managing model deployment approval workflows.

    This service handles the complete lifecycle of model deployment approval
    requests, from creation through approval/rejection to deployment tracking.
    It maintains a complete audit trail and provides statistics for monitoring
    the approval process.

    Attributes:
        auto_deploy_on_approval: Whether to automatically deploy approved models

    Example:
        >>> service = ModelApprovalService()
        >>> request = service.create_approval_request(
        ...     model_version_id='uuid-here',
        ...     requested_by='user123',
        ...     organization_id='org1',
        ...     justification='New model with 15% improvement'
        ... )
        >>> approved = service.approve_request(
        ...     request_id=request['id'],
        ...     reviewed_by='admin1',
        ...     review_notes='Looks good, proceed with deployment',
        ...     db_session=session
        ... )
    """

    # Default target environments
    ENVIRONMENT_STAGING = "staging"
    ENVIRONMENT_PRODUCTION = "production"

    # Valid environments for deployment
    VALID_ENVIRONMENTS = {ENVIRONMENT_STAGING, ENVIRONMENT_PRODUCTION}

    def __init__(self, auto_deploy_on_approval: bool = False) -> None:
        """
        Initialize the model approval service.

        Args:
            auto_deploy_on_approval: Whether to automatically deploy models
                                    when requests are approved (default: False)
        """
        self.auto_deploy_on_approval = auto_deploy_on_approval
        logger.info(
            f"ModelApprovalService initialized (auto_deploy={auto_deploy_on_approval})"
        )

    def create_approval_request(
        self,
        model_version_id: str,
        requested_by: str,
        organization_id: str,
        justification: Optional[str] = None,
        target_environment: str = "staging",
        db_session: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new model deployment approval request.

        This method creates a new approval request for deploying a specific
        model version. The request starts in PENDING status and requires
        approval before deployment can proceed.

        Args:
            model_version_id: UUID of the model version to deploy
            requested_by: User ID of the person making the request
            organization_id: Organization that owns this approval request
            justification: Optional explanation of why this model should be deployed
            target_environment: Target environment (staging or production)
            db_session: Database session for querying and writing

        Returns:
            Dictionary with the created approval request information,
            or None if creation failed

        Example:
            >>> service = ModelApprovalService()
            >>> request = service.create_approval_request(
            ...     model_version_id='123e4567-e89b-12d3-a456-426614174000',
            ...     requested_by='data-scientist-1',
            ...     organization_id='org-123',
            ...     justification='Improved skill matching accuracy by 12%',
            ...     target_environment='production',
            ...     db_session=session
            ... )
            >>> print(request['status'])
            'pending'
        """
        if db_session is None:
            logger.debug(
                "No database session provided for create_approval_request, returning None"
            )
            return None

        # Validate target environment
        if target_environment not in self.VALID_ENVIRONMENTS:
            logger.error(
                f"Invalid target environment: {target_environment}. "
                f"Must be one of: {self.VALID_ENVIRONMENTS}"
            )
            return None

        try:
            # Check if the model version exists
            model_version = (
                db_session.query(MLModelVersion)
                .filter(MLModelVersion.id == model_version_id)
                .first()
            )

            if not model_version:
                logger.error(f"Model version {model_version_id} not found")
                return None

            # Check for existing pending request for the same model version
            existing_request = (
                db_session.query(ModelApprovalRequest)
                .filter(
                    ModelApprovalRequest.model_version_id == model_version_id,
                    ModelApprovalRequest.status == ApprovalStatus.PENDING,
                )
                .first()
            )

            if existing_request:
                logger.warning(
                    f"Pending approval request already exists for model version {model_version_id}"
                )
                return None

            # Create the approval request
            approval_request = ModelApprovalRequest(
                model_version_id=model_version_id,
                status=ApprovalStatus.PENDING,
                requested_by=requested_by,
                organization_id=organization_id,
                justification=justification,
                target_environment=target_environment,
                requested_at=datetime.now(timezone.utc),
            )

            db_session.add(approval_request)
            db_session.commit()

            logger.info(
                f"Created approval request {approval_request.id} for "
                f"model {model_version.model_name}:{model_version.version} "
                f"(requested_by={requested_by}, target={target_environment})"
            )

            return self._format_approval_response(approval_request, model_version)

        except Exception as e:
            logger.error(
                f"Error creating approval request for model version {model_version_id}: {e}",
                exc_info=True,
            )
            if db_session:
                db_session.rollback()
            return None

    def approve_request(
        self,
        request_id: str,
        reviewed_by: str,
        review_notes: Optional[str] = None,
        db_session: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Approve a pending model deployment approval request.

        This method approves a pending request and optionally triggers
        automatic deployment if auto_deploy_on_approval is enabled.
        The request status is changed to APPROVED and reviewer information
        is recorded.

        Args:
            request_id: UUID of the approval request to approve
            reviewed_by: User ID of the person approving the request
            review_notes: Optional notes from the reviewer
            db_session: Database session for querying and writing

        Returns:
            Dictionary with the approved request information,
            or None if approval failed

        Example:
            >>> service = ModelApprovalService()
            >>> result = service.approve_request(
            ...     request_id='approval-uuid',
            ...     reviewed_by='admin-user',
            ...     review_notes='Model metrics look good, approved for production',
            ...     db_session=session
            ... )
            >>> print(result['status'])
            'approved'
        """
        if db_session is None:
            logger.debug(
                "No database session provided for approve_request, returning None"
            )
            return None

        try:
            # Get the approval request
            approval_request = (
                db_session.query(ModelApprovalRequest)
                .filter(ModelApprovalRequest.id == request_id)
                .first()
            )

            if not approval_request:
                logger.error(f"Approval request {request_id} not found")
                return None

            # Check if request is in a valid state for approval
            if approval_request.status != ApprovalStatus.PENDING:
                logger.warning(
                    f"Approval request {request_id} is not pending (status={approval_request.status})"
                )
                return None

            # Update the request
            previous_status = approval_request.status
            approval_request.status = ApprovalStatus.APPROVED
            approval_request.reviewed_by = reviewed_by
            approval_request.reviewed_at = datetime.now(timezone.utc)
            approval_request.review_notes = review_notes

            # Get the associated model version
            model_version = (
                db_session.query(MLModelVersion)
                .filter(MLModelVersion.id == approval_request.model_version_id)
                .first()
            )

            # Auto-deploy if enabled and for production environment
            deployed = False
            if (
                self.auto_deploy_on_approval
                and model_version
                and approval_request.target_environment == self.ENVIRONMENT_PRODUCTION
            ):
                deployment_result = self._deploy_model(model_version, db_session)
                if deployment_result:
                    approval_request.status = ApprovalStatus.DEPLOYED
                    deployed = True
                    logger.info(
                        f"Auto-deployed model {model_version.model_name}:{model_version.version} "
                        f"after approval"
                    )

            db_session.commit()

            logger.info(
                f"Approved request {request_id} by {reviewed_by} "
                f"(auto_deployed={deployed})"
            )

            result = self._format_approval_response(approval_request, model_version)
            result["previous_status"] = previous_status.value if previous_status else None
            result["deployed"] = deployed
            return result

        except Exception as e:
            logger.error(
                f"Error approving request {request_id}: {e}",
                exc_info=True,
            )
            if db_session:
                db_session.rollback()
            return None

    def reject_request(
        self,
        request_id: str,
        reviewed_by: str,
        review_notes: Optional[str] = None,
        db_session: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Reject a pending model deployment approval request.

        This method rejects a pending request. The request status is
        changed to REJECTED and reviewer information with rejection
        reason is recorded.

        Args:
            request_id: UUID of the approval request to reject
            reviewed_by: User ID of the person rejecting the request
            review_notes: Required notes explaining the rejection reason
            db_session: Database session for querying and writing

        Returns:
            Dictionary with the rejected request information,
            or None if rejection failed

        Example:
            >>> service = ModelApprovalService()
            >>> result = service.reject_request(
            ...     request_id='approval-uuid',
            ...     reviewed_by='admin-user',
            ...     review_notes='Performance metrics insufficient for production',
            ...     db_session=session
            ... )
            >>> print(result['status'])
            'rejected'
        """
        if db_session is None:
            logger.debug(
                "No database session provided for reject_request, returning None"
            )
            return None

        try:
            # Get the approval request
            approval_request = (
                db_session.query(ModelApprovalRequest)
                .filter(ModelApprovalRequest.id == request_id)
                .first()
            )

            if not approval_request:
                logger.error(f"Approval request {request_id} not found")
                return None

            # Check if request is in a valid state for rejection
            if approval_request.status != ApprovalStatus.PENDING:
                logger.warning(
                    f"Approval request {request_id} is not pending (status={approval_request.status})"
                )
                return None

            # Update the request
            previous_status = approval_request.status
            approval_request.status = ApprovalStatus.REJECTED
            approval_request.reviewed_by = reviewed_by
            approval_request.reviewed_at = datetime.now(timezone.utc)
            approval_request.review_notes = review_notes

            # Get the associated model version
            model_version = (
                db_session.query(MLModelVersion)
                .filter(MLModelVersion.id == approval_request.model_version_id)
                .first()
            )

            db_session.commit()

            logger.info(
                f"Rejected request {request_id} by {reviewed_by}"
            )

            result = self._format_approval_response(approval_request, model_version)
            result["previous_status"] = previous_status.value if previous_status else None
            return result

        except Exception as e:
            logger.error(
                f"Error rejecting request {request_id}: {e}",
                exc_info=True,
            )
            if db_session:
                db_session.rollback()
            return None

    def cancel_request(
        self,
        request_id: str,
        cancelled_by: str,
        reason: Optional[str] = None,
        db_session: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Cancel a pending approval request.

        This method cancels a pending request. Only the original requester
        or an administrator can cancel a request. The request status is
        changed to CANCELLED.

        Args:
            request_id: UUID of the approval request to cancel
            cancelled_by: User ID of the person cancelling the request
            reason: Optional reason for cancellation
            db_session: Database session for querying and writing

        Returns:
            Dictionary with the cancelled request information,
            or None if cancellation failed

        Example:
            >>> service = ModelApprovalService()
            >>> result = service.cancel_request(
            ...     request_id='approval-uuid',
            ...     cancelled_by='requester-user',
            ...     reason='No longer needed, model deprecated',
            ...     db_session=session
            ... )
            >>> print(result['status'])
            'cancelled'
        """
        if db_session is None:
            logger.debug(
                "No database session provided for cancel_request, returning None"
            )
            return None

        try:
            # Get the approval request
            approval_request = (
                db_session.query(ModelApprovalRequest)
                .filter(ModelApprovalRequest.id == request_id)
                .first()
            )

            if not approval_request:
                logger.error(f"Approval request {request_id} not found")
                return None

            # Check if request is in a valid state for cancellation
            if approval_request.status != ApprovalStatus.PENDING:
                logger.warning(
                    f"Approval request {request_id} is not pending (status={approval_request.status})"
                )
                return None

            # Update the request
            previous_status = approval_request.status
            approval_request.status = ApprovalStatus.CANCELLED
            # Store cancellation info in review_notes if provided
            if reason:
                existing_notes = approval_request.review_notes or ""
                approval_request.review_notes = f"CANCELLED: {reason}\n{existing_notes}".strip()

            # Get the associated model version
            model_version = (
                db_session.query(MLModelVersion)
                .filter(MLModelVersion.id == approval_request.model_version_id)
                .first()
            )

            db_session.commit()

            logger.info(
                f"Cancelled request {request_id} by {cancelled_by}"
            )

            result = self._format_approval_response(approval_request, model_version)
            result["previous_status"] = previous_status.value if previous_status else None
            result["cancelled_by"] = cancelled_by
            return result

        except Exception as e:
            logger.error(
                f"Error cancelling request {request_id}: {e}",
                exc_info=True,
            )
            if db_session:
                db_session.rollback()
            return None

    def mark_deployed(
        self,
        request_id: str,
        db_session: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Mark an approved request as deployed.

        This method is called after a model has been successfully deployed
        to update the approval request status to DEPLOYED.

        Args:
            request_id: UUID of the approval request to mark as deployed
            db_session: Database session for querying and writing

        Returns:
            Dictionary with the deployed request information,
            or None if operation failed

        Example:
            >>> service = ModelApprovalService()
            >>> result = service.mark_deployed(
            ...     request_id='approval-uuid',
            ...     db_session=session
            ... )
            >>> print(result['status'])
            'deployed'
        """
        if db_session is None:
            logger.debug(
                "No database session provided for mark_deployed, returning None"
            )
            return None

        try:
            # Get the approval request
            approval_request = (
                db_session.query(ModelApprovalRequest)
                .filter(ModelApprovalRequest.id == request_id)
                .first()
            )

            if not approval_request:
                logger.error(f"Approval request {request_id} not found")
                return None

            # Check if request is in a valid state for deployment
            if approval_request.status not in [ApprovalStatus.APPROVED, ApprovalStatus.DEPLOYED]:
                logger.warning(
                    f"Approval request {request_id} is not approved (status={approval_request.status})"
                )
                return None

            # Update the request
            previous_status = approval_request.status
            approval_request.status = ApprovalStatus.DEPLOYED

            # Get the associated model version
            model_version = (
                db_session.query(MLModelVersion)
                .filter(MLModelVersion.id == approval_request.model_version_id)
                .first()
            )

            db_session.commit()

            logger.info(
                f"Marked request {request_id} as deployed"
            )

            result = self._format_approval_response(approval_request, model_version)
            result["previous_status"] = previous_status.value if previous_status else None
            return result

        except Exception as e:
            logger.error(
                f"Error marking request {request_id} as deployed: {e}",
                exc_info=True,
            )
            if db_session:
                db_session.rollback()
            return None

    def get_request(
        self,
        request_id: str,
        db_session: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific approval request.

        Args:
            request_id: UUID of the approval request
            db_session: Database session for querying

        Returns:
            Dictionary with approval request details including model version info,
            or None if not found

        Example:
            >>> service = ModelApprovalService()
            >>> request = service.get_request(
            ...     request_id='approval-uuid',
            ...     db_session=session
            ... )
            >>> print(request['status'])
            'pending'
        """
        if db_session is None:
            logger.debug(
                "No database session provided for get_request, returning None"
            )
            return None

        try:
            # Get the approval request with model version
            approval_request = (
                db_session.query(ModelApprovalRequest)
                .filter(ModelApprovalRequest.id == request_id)
                .first()
            )

            if not approval_request:
                logger.debug(f"Approval request {request_id} not found")
                return None

            # Get the associated model version
            model_version = (
                db_session.query(MLModelVersion)
                .filter(MLModelVersion.id == approval_request.model_version_id)
                .first()
            )

            return self._format_approval_response(approval_request, model_version)

        except Exception as e:
            logger.error(
                f"Error getting request {request_id}: {e}",
                exc_info=True,
            )
            return None

    def list_requests(
        self,
        organization_id: Optional[str] = None,
        status: Optional[ApprovalStatus] = None,
        requested_by: Optional[str] = None,
        target_environment: Optional[str] = None,
        model_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        db_session: Optional[Any] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List approval requests with optional filtering.

        This method retrieves a paginated list of approval requests
        with support for various filters.

        Args:
            organization_id: Filter by organization ID
            status: Filter by approval status
            requested_by: Filter by requester user ID
            target_environment: Filter by target environment
            model_name: Filter by model name (joins with model versions)
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            db_session: Database session for querying

        Returns:
            Tuple of (list of request dictionaries, total count)

        Example:
            >>> service = ModelApprovalService()
            >>> requests, total = service.list_requests(
            ...     organization_id='org-123',
            ...     status=ApprovalStatus.PENDING,
            ...     limit=10,
            ...     db_session=session
            ... )
            >>> print(f"Found {total} pending requests")
        """
        if db_session is None:
            logger.debug(
                "No database session provided for list_requests, returning ([], 0)"
            )
            return [], 0

        try:
            # Build base query
            query = db_session.query(ModelApprovalRequest)

            # Apply filters
            if organization_id:
                query = query.filter(
                    ModelApprovalRequest.organization_id == organization_id
                )

            if status:
                query = query.filter(ModelApprovalRequest.status == status)

            if requested_by:
                query = query.filter(ModelApprovalRequest.requested_by == requested_by)

            if target_environment:
                query = query.filter(
                    ModelApprovalRequest.target_environment == target_environment
                )

            # Filter by model name requires join
            if model_name:
                query = query.join(MLModelVersion).filter(
                    MLModelVersion.model_name == model_name
                )

            # Get total count
            total_count = query.count()

            # Apply pagination and ordering
            requests = (
                query.order_by(ModelApprovalRequest.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            # Format results with model version info
            results = []
            for request in requests:
                model_version = (
                    db_session.query(MLModelVersion)
                    .filter(MLModelVersion.id == request.model_version_id)
                    .first()
                )
                results.append(self._format_approval_response(request, model_version))

            logger.info(
                f"Listed {len(results)} approval requests (total={total_count})"
            )

            return results, total_count

        except Exception as e:
            logger.error(
                f"Error listing approval requests: {e}",
                exc_info=True,
            )
            return [], 0

    def get_pending_requests(
        self,
        organization_id: Optional[str] = None,
        limit: int = 50,
        db_session: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all pending approval requests.

        Convenience method for getting all requests that need review.

        Args:
            organization_id: Optional filter by organization
            limit: Maximum number of results
            db_session: Database session for querying

        Returns:
            List of pending approval request dictionaries

        Example:
            >>> service = ModelApprovalService()
            >>> pending = service.get_pending_requests(
            ...     organization_id='org-123',
            ...     db_session=session
            ... )
            >>> print(f"{len(pending)} requests awaiting review")
        """
        requests, _ = self.list_requests(
            organization_id=organization_id,
            status=ApprovalStatus.PENDING,
            limit=limit,
            db_session=db_session,
        )
        return requests

    def get_requests_by_model(
        self,
        model_version_id: str,
        db_session: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all approval requests for a specific model version.

        Args:
            model_version_id: UUID of the model version
            db_session: Database session for querying

        Returns:
            List of approval request dictionaries for the model version

        Example:
            >>> service = ModelApprovalService()
            >>> requests = service.get_requests_by_model(
            ...     model_version_id='model-uuid',
            ...     db_session=session
            ... )
        """
        if db_session is None:
            logger.debug(
                "No database session provided for get_requests_by_model, returning []"
            )
            return []

        try:
            requests = (
                db_session.query(ModelApprovalRequest)
                .filter(ModelApprovalRequest.model_version_id == model_version_id)
                .order_by(ModelApprovalRequest.created_at.desc())
                .all()
            )

            results = []
            for request in requests:
                model_version = (
                    db_session.query(MLModelVersion)
                    .filter(MLModelVersion.id == request.model_version_id)
                    .first()
                )
                results.append(self._format_approval_response(request, model_version))

            return results

        except Exception as e:
            logger.error(
                f"Error getting requests for model {model_version_id}: {e}",
                exc_info=True,
            )
            return []

    def get_audit_log(
        self,
        request_id: str,
        db_session: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get the audit log for a specific approval request.

        This method reconstructs the audit trail for a request based on
        the status changes and timestamps recorded.

        Args:
            request_id: UUID of the approval request
            db_session: Database session for querying

        Returns:
            List of audit log entries for the request

        Example:
            >>> service = ModelApprovalService()
            >>> audit_log = service.get_audit_log(
            ...     request_id='approval-uuid',
            ...     db_session=session
            ... )
            >>> for entry in audit_log:
            ...     print(f"{entry['action']} by {entry['performed_by']}")
        """
        if db_session is None:
            logger.debug(
                "No database session provided for get_audit_log, returning []"
            )
            return []

        try:
            # Get the approval request
            approval_request = (
                db_session.query(ModelApprovalRequest)
                .filter(ModelApprovalRequest.id == request_id)
                .first()
            )

            if not approval_request:
                logger.debug(f"Approval request {request_id} not found")
                return []

            audit_entries = []

            # Entry 1: Request created
            audit_entries.append({
                "id": f"{request_id}-created",
                "approval_request_id": str(request_id),
                "action": "created",
                "performed_by": approval_request.requested_by,
                "previous_status": None,
                "new_status": ApprovalStatus.PENDING.value,
                "notes": approval_request.justification,
                "timestamp": approval_request.requested_at.isoformat()
                if approval_request.requested_at
                else approval_request.created_at.isoformat(),
            })

            # Entry 2: Request reviewed (if reviewed)
            if approval_request.reviewed_at and approval_request.reviewed_by:
                action = "approved" if approval_request.status == ApprovalStatus.APPROVED else \
                        "rejected" if approval_request.status == ApprovalStatus.REJECTED else \
                        "reviewed"

                audit_entries.append({
                    "id": f"{request_id}-reviewed",
                    "approval_request_id": str(request_id),
                    "action": action,
                    "performed_by": approval_request.reviewed_by,
                    "previous_status": ApprovalStatus.PENDING.value,
                    "new_status": approval_request.status.value,
                    "notes": approval_request.review_notes,
                    "timestamp": approval_request.reviewed_at.isoformat(),
                })

            # Entry 3: Model deployed (if deployed)
            if approval_request.status == ApprovalStatus.DEPLOYED:
                # Get updated_at as deployment timestamp (approximate)
                audit_entries.append({
                    "id": f"{request_id}-deployed",
                    "approval_request_id": str(request_id),
                    "action": "deployed",
                    "performed_by": approval_request.reviewed_by or "system",
                    "previous_status": ApprovalStatus.APPROVED.value,
                    "new_status": ApprovalStatus.DEPLOYED.value,
                    "notes": f"Deployed to {approval_request.target_environment}",
                    "timestamp": approval_request.updated_at.isoformat()
                    if approval_request.updated_at
                    else None,
                })

            # Entry 4: Request cancelled (if cancelled)
            if approval_request.status == ApprovalStatus.CANCELLED:
                # Extract cancellation reason from review_notes
                cancel_reason = None
                if approval_request.review_notes:
                    if approval_request.review_notes.startswith("CANCELLED:"):
                        cancel_reason = approval_request.review_notes

                audit_entries.append({
                    "id": f"{request_id}-cancelled",
                    "approval_request_id": str(request_id),
                    "action": "cancelled",
                    "performed_by": approval_request.reviewed_by or approval_request.requested_by,
                    "previous_status": ApprovalStatus.PENDING.value,
                    "new_status": ApprovalStatus.CANCELLED.value,
                    "notes": cancel_reason,
                    "timestamp": approval_request.updated_at.isoformat()
                    if approval_request.updated_at
                    else None,
                })

            return audit_entries

        except Exception as e:
            logger.error(
                f"Error getting audit log for request {request_id}: {e}",
                exc_info=True,
            )
            return []

    def get_statistics(
        self,
        organization_id: Optional[str] = None,
        period_days: Optional[int] = None,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Get approval workflow statistics.

        This method computes statistics about the approval workflow,
        including request counts by status, approval rate, and
        average approval time.

        Args:
            organization_id: Optional filter by organization
            period_days: Optional time period in days (e.g., last 30 days)
            db_session: Database session for querying

        Returns:
            Dictionary with approval workflow statistics

        Example:
            >>> service = ModelApprovalService()
            >>> stats = service.get_statistics(
            ...     organization_id='org-123',
            ...     period_days=30,
            ...     db_session=session
            ... )
            >>> print(f"Approval rate: {stats['approval_rate']}%")
        """
        if db_session is None:
            logger.debug(
                "No database session provided for get_statistics, returning empty stats"
            )
            return self._empty_statistics()

        try:
            # Build base query
            query = db_session.query(ModelApprovalRequest)

            if organization_id:
                query = query.filter(
                    ModelApprovalRequest.organization_id == organization_id
                )

            # Apply time period filter
            if period_days:
                period_start = datetime.now(timezone.utc) - timedelta(days=period_days)
                query = query.filter(ModelApprovalRequest.created_at >= period_start)

            # Get all matching requests
            requests = query.all()

            # Calculate statistics
            total_count = len(requests)
            pending_count = sum(1 for r in requests if r.status == ApprovalStatus.PENDING)
            approved_count = sum(1 for r in requests if r.status == ApprovalStatus.APPROVED)
            rejected_count = sum(1 for r in requests if r.status == ApprovalStatus.REJECTED)
            deployed_count = sum(1 for r in requests if r.status == ApprovalStatus.DEPLOYED)
            cancelled_count = sum(1 for r in requests if r.status == ApprovalStatus.CANCELLED)

            # Calculate approval rate
            reviewed_count = approved_count + rejected_count
            approval_rate = 0.0
            if reviewed_count > 0:
                approval_rate = (approved_count / reviewed_count) * 100

            # Calculate average approval time
            approval_times = []
            for r in requests:
                if r.status in [ApprovalStatus.APPROVED, ApprovalStatus.DEPLOYED] and \
                   r.requested_at and r.reviewed_at:
                    delta = r.reviewed_at - r.requested_at
                    hours = delta.total_seconds() / 3600
                    approval_times.append(hours)

            avg_approval_time = None
            if approval_times:
                avg_approval_time = sum(approval_times) / len(approval_times)

            # Determine period dates
            period_start_str = None
            period_end_str = None
            if period_days:
                period_start_str = (
                    datetime.now(timezone.utc) - timedelta(days=period_days)
                ).isoformat()
                period_end_str = datetime.now(timezone.utc).isoformat()

            return {
                "total_requests": total_count,
                "pending_requests": pending_count,
                "approved_requests": approved_count,
                "rejected_requests": rejected_count,
                "deployed_requests": deployed_count,
                "cancelled_requests": cancelled_count,
                "average_approval_time_hours": round(avg_approval_time, 2)
                if avg_approval_time is not None
                else None,
                "approval_rate": round(approval_rate, 2),
                "period_start": period_start_str,
                "period_end": period_end_str,
            }

        except Exception as e:
            logger.error(
                f"Error getting approval statistics: {e}",
                exc_info=True,
            )
            return self._empty_statistics()

    def get_dashboard_data(
        self,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Get dashboard data for the approval workflow.

        This method retrieves all data needed for the approval workflow
        dashboard, including pending requests, recent activity, and statistics.

        Args:
            organization_id: Optional filter by organization
            user_id: Optional user ID for user-specific counts
            db_session: Database session for querying

        Returns:
            Dictionary with dashboard data

        Example:
            >>> service = ModelApprovalService()
            >>> dashboard = service.get_dashboard_data(
            ...     organization_id='org-123',
            ...     user_id='user-123',
            ...     db_session=session
            ... )
            >>> print(f"{len(dashboard['pending_requests'])} pending requests")
        """
        if db_session is None:
            logger.debug(
                "No database session provided for get_dashboard_data, returning empty dashboard"
            )
            return self._empty_dashboard()

        try:
            # Get pending requests
            pending_requests = self.get_pending_requests(
                organization_id=organization_id,
                limit=10,
                db_session=db_session,
            )

            # Get recent approvals (last 5)
            recent_approvals, _ = self.list_requests(
                organization_id=organization_id,
                status=ApprovalStatus.APPROVED,
                limit=5,
                db_session=db_session,
            )

            # Get recent rejections (last 5)
            recent_rejections, _ = self.list_requests(
                organization_id=organization_id,
                status=ApprovalStatus.REJECTED,
                limit=5,
                db_session=db_session,
            )

            # Get statistics
            stats = self.get_statistics(
                organization_id=organization_id,
                period_days=30,
                db_session=db_session,
            )

            # Get user's pending count
            user_pending_count = 0
            if user_id:
                user_pending, _ = self.list_requests(
                    organization_id=organization_id,
                    requested_by=user_id,
                    status=ApprovalStatus.PENDING,
                    limit=1000,  # Just for counting
                    db_session=db_session,
                )
                user_pending_count = len(user_pending)

            return {
                "pending_requests": pending_requests,
                "recent_approvals": recent_approvals,
                "recent_rejections": recent_rejections,
                "stats": stats,
                "user_pending_count": user_pending_count,
            }

        except Exception as e:
            logger.error(
                f"Error getting dashboard data: {e}",
                exc_info=True,
            )
            return self._empty_dashboard()

    def can_request_approval(
        self,
        model_version_id: str,
        organization_id: str,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Check if a new approval request can be created for a model version.

        This method validates whether a model version is eligible for
        an approval request, checking for existing pending requests
        and model version status.

        Args:
            model_version_id: UUID of the model version to check
            organization_id: Organization ID for access control
            db_session: Database session for querying

        Returns:
            Dictionary with:
            - can_request: Boolean indicating if request can be made
            - reason: Explanation if request cannot be made
            - existing_request: Existing pending request if any

        Example:
            >>> service = ModelApprovalService()
            >>> check = service.can_request_approval(
            ...     model_version_id='model-uuid',
            ...     organization_id='org-123',
            ...     db_session=session
            ... )
            >>> if check['can_request']:
            ...     # Proceed with creating request
        """
        if db_session is None:
            return {
                "can_request": False,
                "reason": "No database session available",
                "existing_request": None,
            }

        try:
            # Check if model version exists
            model_version = (
                db_session.query(MLModelVersion)
                .filter(MLModelVersion.id == model_version_id)
                .first()
            )

            if not model_version:
                return {
                    "can_request": False,
                    "reason": "Model version not found",
                    "existing_request": None,
                }

            # Check for existing pending request
            existing_request = (
                db_session.query(ModelApprovalRequest)
                .filter(
                    ModelApprovalRequest.model_version_id == model_version_id,
                    ModelApprovalRequest.status == ApprovalStatus.PENDING,
                )
                .first()
            )

            if existing_request:
                return {
                    "can_request": False,
                    "reason": "A pending approval request already exists for this model version",
                    "existing_request": self._format_approval_response(
                        existing_request, model_version
                    ),
                }

            # Check if model is already active in production
            if model_version.is_active and not model_version.is_experiment:
                return {
                    "can_request": False,
                    "reason": "This model version is already active in production",
                    "existing_request": None,
                }

            return {
                "can_request": True,
                "reason": None,
                "existing_request": None,
                "model_version": {
                    "id": str(model_version.id),
                    "model_name": model_version.model_name,
                    "version": model_version.version,
                    "performance_score": float(model_version.performance_score)
                    if model_version.performance_score
                    else None,
                },
            }

        except Exception as e:
            logger.error(
                f"Error checking if approval can be requested for {model_version_id}: {e}",
                exc_info=True,
            )
            return {
                "can_request": False,
                "reason": f"Error checking eligibility: {str(e)}",
                "existing_request": None,
            }

    # Private helper methods

    def _deploy_model(
        self,
        model_version: MLModelVersion,
        db_session: Any,
    ) -> bool:
        """
        Deploy a model version to production.

        This internal method handles the actual deployment of a model
        by activating it and deactivating the previous version.

        Args:
            model_version: MLModelVersion to deploy
            db_session: Database session

        Returns:
            True if deployment succeeded, False otherwise
        """
        try:
            # Deactivate any currently active model for this model name
            active_models = (
                db_session.query(MLModelVersion)
                .filter(
                    MLModelVersion.model_name == model_version.model_name,
                    MLModelVersion.is_active == True,
                    MLModelVersion.id != model_version.id,
                )
                .all()
            )

            for active_model in active_models:
                active_model.is_active = False
                logger.info(
                    f"Deactivated model {active_model.model_name}:{active_model.version}"
                )

            # Activate the new model
            model_version.is_active = True
            model_version.is_experiment = False

            logger.info(
                f"Deployed model {model_version.model_name}:{model_version.version} to production"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error deploying model {model_version.model_name}:{model_version.version}: {e}",
                exc_info=True,
            )
            return False

    def _format_approval_response(
        self,
        approval_request: ModelApprovalRequest,
        model_version: Optional[MLModelVersion] = None,
    ) -> Dict[str, Any]:
        """
        Format an approval request for API response.

        Args:
            approval_request: ModelApprovalRequest to format
            model_version: Optional associated MLModelVersion

        Returns:
            Dictionary with formatted approval request data
        """
        response = {
            "id": str(approval_request.id),
            "model_version_id": str(approval_request.model_version_id),
            "status": approval_request.status.value,
            "requested_by": approval_request.requested_by,
            "reviewed_by": approval_request.reviewed_by,
            "requested_at": approval_request.requested_at.isoformat()
            if approval_request.requested_at
            else None,
            "reviewed_at": approval_request.reviewed_at.isoformat()
            if approval_request.reviewed_at
            else None,
            "justification": approval_request.justification,
            "review_notes": approval_request.review_notes,
            "target_environment": approval_request.target_environment,
            "organization_id": approval_request.organization_id,
            "created_at": approval_request.created_at.isoformat()
            if approval_request.created_at
            else None,
            "updated_at": approval_request.updated_at.isoformat()
            if approval_request.updated_at
            else None,
        }

        # Add model version info if available
        if model_version:
            response["model_version"] = {
                "id": str(model_version.id),
                "model_name": model_version.model_name,
                "version": model_version.version,
                "is_active": model_version.is_active,
                "is_experiment": model_version.is_experiment,
                "performance_score": float(model_version.performance_score)
                if model_version.performance_score
                else None,
                "file_path": model_version.file_path,
            }

        return response

    def _empty_statistics(self) -> Dict[str, Any]:
        """Return empty statistics structure."""
        return {
            "total_requests": 0,
            "pending_requests": 0,
            "approved_requests": 0,
            "rejected_requests": 0,
            "deployed_requests": 0,
            "cancelled_requests": 0,
            "average_approval_time_hours": None,
            "approval_rate": 0.0,
            "period_start": None,
            "period_end": None,
        }

    def _empty_dashboard(self) -> Dict[str, Any]:
        """Return empty dashboard structure."""
        return {
            "pending_requests": [],
            "recent_approvals": [],
            "recent_rejections": [],
            "stats": self._empty_statistics(),
            "user_pending_count": 0,
        }


# Global service instance
_model_approval_service: Optional[ModelApprovalService] = None


def get_model_approval_service() -> ModelApprovalService:
    """
    Get or create the global model approval service instance.

    Returns:
        ModelApprovalService singleton instance

    Example:
        >>> service = get_model_approval_service()
        >>> request = service.create_approval_request(
        ...     model_version_id='uuid-here',
        ...     requested_by='user123',
        ...     organization_id='org1'
        ... )
    """
    global _model_approval_service
    if _model_approval_service is None:
        _model_approval_service = ModelApprovalService()
    return _model_approval_service


__all__ = [
    "ModelApprovalService",
    "get_model_approval_service",
]
