"""
Integration tests for complete model approval workflow lifecycle.

This test suite validates the end-to-end integration between:
- Model Approval Request data models (ModelApprovalRequest, ApprovalStatus)
- Model Approval Service (request creation, approval, rejection, deployment)
- ML Model Version model (activation, deployment tracking)
- Database (persistence, relationships, audit trails)

Test Coverage:
- Complete approval workflow lifecycle (create → pending → approve → deploy)
- Model version activation upon approval
- Audit trail generation and verification
- Rejection workflows
- Cancellation workflows
- Error handling and edge cases
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.model_approval import (
    ModelApprovalRequest,
    ApprovalStatus,
)
from models.ml_model_version import MLModelVersion, ModelRole
from services.model_approval_service import ModelApprovalService


# ============================================================================
# Fixtures for Approval Workflow Integration Tests
# ============================================================================

@pytest.fixture(scope="function")
async def sample_model_version(test_db: AsyncSession):
    """
    Create a sample ML model version for approval workflow testing.

    This fixture creates an inactive model version that can be submitted
    for approval to be deployed to production.

    Args:
        test_db: Database session

    Returns:
        Created MLModelVersion instance
    """
    model_version = MLModelVersion(
        model_name="skill_matching",
        version="v2.1.0",
        is_active=False,
        is_experiment=False,
        model_metadata={
            "algorithm": "gradient_boosting",
            "training_date": "2026-02-15",
            "feature_count": 150,
        },
        accuracy_metrics={
            "precision": 0.92,
            "recall": 0.89,
            "f1_score": 0.905,
        },
        performance_score=90.5,
        model_role=ModelRole.STANDARD,
    )
    test_db.add(model_version)
    await test_db.commit()
    await test_db.refresh(model_version)

    return model_version


@pytest.fixture(scope="function")
async def active_model_version(test_db: AsyncSession):
    """
    Create an active ML model version for testing replacement scenarios.

    This fixture creates a currently active model version that should
    be deactivated when a new model is approved and deployed.

    Args:
        test_db: Database session

    Returns:
        Created active MLModelVersion instance
    """
    model_version = MLModelVersion(
        model_name="skill_matching",
        version="v2.0.0",
        is_active=True,
        is_experiment=False,
        model_metadata={
            "algorithm": "random_forest",
            "training_date": "2025-11-01",
        },
        accuracy_metrics={
            "precision": 0.85,
            "recall": 0.82,
            "f1_score": 0.835,
        },
        performance_score=83.5,
        model_role=ModelRole.CHAMPION,
    )
    test_db.add(model_version)
    await test_db.commit()
    await test_db.refresh(model_version)

    return model_version


@pytest.fixture(scope="function")
async def pending_approval_request(
    test_db: AsyncSession,
    sample_model_version: MLModelVersion,
):
    """
    Create a pending approval request for testing.

    This fixture creates an approval request in PENDING status
    ready for approval/rejection testing.

    Args:
        test_db: Database session
        sample_model_version: Model version to create request for

    Returns:
        Created ModelApprovalRequest instance
    """
    approval_request = ModelApprovalRequest(
        model_version_id=sample_model_version.id,
        status=ApprovalStatus.PENDING,
        requested_by="data-scientist-123",
        organization_id=str(uuid4()),
        justification="Model v2.1.0 shows 15% improvement in matching accuracy",
        target_environment="production",
        requested_at=datetime.now(timezone.utc),
    )
    test_db.add(approval_request)
    await test_db.commit()
    await test_db.refresh(approval_request)

    return approval_request


@pytest.fixture(scope="function")
def approval_service() -> ModelApprovalService:
    """
    Create a ModelApprovalService instance for testing.

    Returns:
        ModelApprovalService instance with auto_deploy enabled
    """
    return ModelApprovalService(auto_deploy_on_approval=True)


@pytest.fixture(scope="function")
def approval_service_no_auto_deploy() -> ModelApprovalService:
    """
    Create a ModelApprovalService instance without auto-deploy.

    Returns:
        ModelApprovalService instance with auto_deploy disabled
    """
    return ModelApprovalService(auto_deploy_on_approval=False)


# ============================================================================
# Test Classes
# ============================================================================

class TestApprovalRequestCreation:
    """Tests for approval request creation and initialization."""

    @pytest.mark.asyncio
    async def test_create_approval_request_with_valid_data(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """
        Test creating an approval request with valid data.

        Validates:
        - Request is created successfully
        - Initial status is PENDING
        - All required fields are populated
        - Timestamps are set correctly
        """
        org_id = str(uuid4())
        user_id = "data-scientist-456"

        request = approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by=user_id,
            organization_id=org_id,
            justification="New model with improved accuracy",
            target_environment="production",
            db_session=test_db,
        )

        assert request is not None
        assert request["status"] == "pending"
        assert request["requested_by"] == user_id
        assert request["organization_id"] == org_id
        assert request["model_version_id"] == str(sample_model_version.id)
        assert request["target_environment"] == "production"
        assert request["justification"] == "New model with improved accuracy"
        assert request["requested_at"] is not None

    @pytest.mark.asyncio
    async def test_create_approval_request_defaults_to_staging(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test that target_environment defaults to staging."""
        request = approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="user-123",
            organization_id=str(uuid4()),
            db_session=test_db,
        )

        assert request["target_environment"] == "staging"

    @pytest.mark.asyncio
    async def test_create_approval_request_fails_for_nonexistent_model(
        self,
        test_db: AsyncSession,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test that creating a request for non-existent model fails."""
        request = approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(uuid4()),
            requested_by="user-123",
            organization_id=str(uuid4()),
            db_session=test_db,
        )

        assert request is None

    @pytest.mark.asyncio
    async def test_create_approval_request_fails_for_invalid_environment(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test that invalid target environment is rejected."""
        request = approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="user-123",
            organization_id=str(uuid4()),
            target_environment="invalid_env",
            db_session=test_db,
        )

        assert request is None

    @pytest.mark.asyncio
    async def test_create_duplicate_pending_request_fails(
        self,
        test_db: AsyncSession,
        pending_approval_request: ModelApprovalRequest,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test that duplicate pending requests are prevented."""
        request = approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(pending_approval_request.model_version_id),
            requested_by="another-user",
            organization_id=str(uuid4()),
            db_session=test_db,
        )

        assert request is None


class TestApprovalWorkflow:
    """Tests for the approval workflow (approve, reject, cancel)."""

    @pytest.mark.asyncio
    async def test_approve_pending_request(
        self,
        test_db: AsyncSession,
        pending_approval_request: ModelApprovalRequest,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """
        Test approving a pending approval request.

        Validates:
        - Status changes to APPROVED
        - Reviewer information is recorded
        - Review timestamp is set
        - Review notes are stored
        """
        reviewer_id = "ml-lead-789"

        result = approval_service_no_auto_deploy.approve_request(
            request_id=str(pending_approval_request.id),
            reviewed_by=reviewer_id,
            review_notes="Model metrics validated. Approved for deployment.",
            db_session=test_db,
        )

        assert result is not None
        assert result["status"] == "approved"
        assert result["reviewed_by"] == reviewer_id
        assert result["review_notes"] == "Model metrics validated. Approved for deployment."
        assert result["reviewed_at"] is not None
        assert result["previous_status"] == "pending"

    @pytest.mark.asyncio
    async def test_reject_pending_request(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """
        Test rejecting a pending approval request.

        Validates:
        - Status changes to REJECTED
        - Rejection reason is recorded
        - Reviewer information is stored
        """
        # Create a new request for rejection
        org_id = str(uuid4())
        request = approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="data-scientist-123",
            organization_id=org_id,
            justification="Requesting approval",
            db_session=test_db,
        )

        result = approval_service_no_auto_deploy.reject_request(
            request_id=request["id"],
            reviewed_by="ml-lead-789",
            review_notes="Model accuracy below required threshold",
            db_session=test_db,
        )

        assert result is not None
        assert result["status"] == "rejected"
        assert result["reviewed_by"] == "ml-lead-789"
        assert result["review_notes"] == "Model accuracy below required threshold"

    @pytest.mark.asyncio
    async def test_cancel_pending_request(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """
        Test cancelling a pending approval request.

        Validates:
        - Status changes to CANCELLED
        - Cancellation reason is recorded
        """
        # Create a new request for cancellation
        request = approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="data-scientist-123",
            organization_id=str(uuid4()),
            justification="Requesting approval",
            db_session=test_db,
        )

        result = approval_service_no_auto_deploy.cancel_request(
            request_id=request["id"],
            cancelled_by="data-scientist-123",
            reason="Found critical bug, need to fix first",
            db_session=test_db,
        )

        assert result is not None
        assert result["status"] == "cancelled"
        assert "critical bug" in result["review_notes"].lower()

    @pytest.mark.asyncio
    async def test_approve_non_pending_request_fails(
        self,
        test_db: AsyncSession,
        pending_approval_request: ModelApprovalRequest,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test that approving a non-pending request fails."""
        # First approve the request
        approval_service_no_auto_deploy.approve_request(
            request_id=str(pending_approval_request.id),
            reviewed_by="ml-lead-789",
            db_session=test_db,
        )

        # Try to approve again
        result = approval_service_no_auto_deploy.approve_request(
            request_id=str(pending_approval_request.id),
            reviewed_by="another-reviewer",
            db_session=test_db,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_reject_non_pending_request_fails(
        self,
        test_db: AsyncSession,
        pending_approval_request: ModelApprovalRequest,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test that rejecting a non-pending request fails."""
        # First approve the request
        approval_service_no_auto_deploy.approve_request(
            request_id=str(pending_approval_request.id),
            reviewed_by="ml-lead-789",
            db_session=test_db,
        )

        # Try to reject
        result = approval_service_no_auto_deploy.reject_request(
            request_id=str(pending_approval_request.id),
            reviewed_by="another-reviewer",
            db_session=test_db,
        )

        assert result is None


class TestModelVersionActivation:
    """Tests for model version activation upon approval."""

    @pytest.mark.asyncio
    async def test_model_activated_on_approval_with_auto_deploy(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service: ModelApprovalService,
    ):
        """
        Test that model version is activated when approved with auto-deploy.

        Validates:
        - Model is_active becomes True
        - Model is_experiment becomes False
        - Approval request status becomes DEPLOYED
        """
        org_id = str(uuid4())

        # Create approval request for production
        request = approval_service.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="data-scientist-123",
            organization_id=org_id,
            justification="Ready for production deployment",
            target_environment="production",
            db_session=test_db,
        )

        # Approve the request
        result = approval_service.approve_request(
            request_id=request["id"],
            reviewed_by="ml-lead-789",
            review_notes="Approved for production",
            db_session=test_db,
        )

        assert result is not None
        assert result["status"] == "deployed"
        assert result["deployed"] is True

        # Verify model version is now active
        await test_db.refresh(sample_model_version)
        assert sample_model_version.is_active is True
        assert sample_model_version.is_experiment is False

    @pytest.mark.asyncio
    async def test_previous_model_deactivated_on_deploy(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        active_model_version: MLModelVersion,
        approval_service: ModelApprovalService,
    ):
        """
        Test that previous active model is deactivated when new model is deployed.

        Validates:
        - Previous champion model is deactivated
        - New model becomes active
        """
        org_id = str(uuid4())

        # Create approval request
        request = approval_service.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="data-scientist-123",
            organization_id=org_id,
            justification="Upgrading to v2.1.0",
            target_environment="production",
            db_session=test_db,
        )

        # Approve
        approval_service.approve_request(
            request_id=request["id"],
            reviewed_by="ml-lead-789",
            db_session=test_db,
        )

        # Verify new model is active
        await test_db.refresh(sample_model_version)
        assert sample_model_version.is_active is True

        # Verify old model is deactivated
        await test_db.refresh(active_model_version)
        assert active_model_version.is_active is False

    @pytest.mark.asyncio
    async def test_staging_deployment_does_not_activate(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service: ModelApprovalService,
    ):
        """
        Test that staging deployments don't auto-activate the model.

        Validates:
        - Model remains inactive for staging deployments
        - Request status is APPROVED (not DEPLOYED)
        """
        org_id = str(uuid4())

        # Create approval request for staging
        request = approval_service.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="data-scientist-123",
            organization_id=org_id,
            justification="Testing in staging",
            target_environment="staging",
            db_session=test_db,
        )

        # Approve
        result = approval_service.approve_request(
            request_id=request["id"],
            reviewed_by="ml-lead-789",
            db_session=test_db,
        )

        # Staging deployments should be APPROVED, not DEPLOYED
        assert result["status"] == "approved"
        assert result["deployed"] is False

        # Model should remain inactive
        await test_db.refresh(sample_model_version)
        assert sample_model_version.is_active is False


class TestAuditTrail:
    """Tests for audit trail generation and verification."""

    @pytest.mark.asyncio
    async def test_audit_log_for_created_request(
        self,
        test_db: AsyncSession,
        pending_approval_request: ModelApprovalRequest,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """
        Test that audit log is generated for request creation.

        Validates:
        - Audit entry for 'created' action exists
        - Timestamp is recorded
        - Requester information is captured
        """
        audit_log = approval_service_no_auto_deploy.get_audit_log(
            request_id=str(pending_approval_request.id),
            db_session=test_db,
        )

        assert len(audit_log) >= 1

        # Find the 'created' entry
        created_entry = next(
            (e for e in audit_log if e["action"] == "created"),
            None
        )
        assert created_entry is not None
        assert created_entry["performed_by"] == "data-scientist-123"
        assert created_entry["new_status"] == "pending"
        assert created_entry["timestamp"] is not None

    @pytest.mark.asyncio
    async def test_audit_log_for_approved_request(
        self,
        test_db: AsyncSession,
        pending_approval_request: ModelApprovalRequest,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """
        Test that audit log is updated when request is approved.

        Validates:
        - Audit entry for 'approved' action exists
        - Previous status is recorded
        - Reviewer information is captured
        """
        # Approve the request
        approval_service_no_auto_deploy.approve_request(
            request_id=str(pending_approval_request.id),
            reviewed_by="ml-lead-789",
            review_notes="Approved",
            db_session=test_db,
        )

        # Get audit log
        audit_log = approval_service_no_auto_deploy.get_audit_log(
            request_id=str(pending_approval_request.id),
            db_session=test_db,
        )

        # Find the 'approved' entry
        approved_entry = next(
            (e for e in audit_log if e["action"] == "approved"),
            None
        )
        assert approved_entry is not None
        assert approved_entry["performed_by"] == "ml-lead-789"
        assert approved_entry["previous_status"] == "pending"
        assert approved_entry["new_status"] == "approved"

    @pytest.mark.asyncio
    async def test_audit_log_for_deployed_model(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service: ModelApprovalService,
    ):
        """
        Test that audit log captures deployment information.

        Validates:
        - Audit entry for 'deployed' action exists
        - Target environment is recorded
        """
        org_id = str(uuid4())

        # Create and approve request with auto-deploy
        request = approval_service.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="data-scientist-123",
            organization_id=org_id,
            justification="Ready for production",
            target_environment="production",
            db_session=test_db,
        )

        approval_service.approve_request(
            request_id=request["id"],
            reviewed_by="ml-lead-789",
            db_session=test_db,
        )

        # Get audit log
        audit_log = approval_service.get_audit_log(
            request_id=request["id"],
            db_session=test_db,
        )

        # Find the 'deployed' entry
        deployed_entry = next(
            (e for e in audit_log if e["action"] == "deployed"),
            None
        )
        assert deployed_entry is not None
        assert "production" in deployed_entry["notes"].lower()

    @pytest.mark.asyncio
    async def test_audit_log_for_rejected_request(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """
        Test that audit log captures rejection information.

        Validates:
        - Audit entry for 'rejected' action exists
        - Rejection notes are recorded
        """
        org_id = str(uuid4())

        # Create and reject request
        request = approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="data-scientist-123",
            organization_id=org_id,
            db_session=test_db,
        )

        approval_service_no_auto_deploy.reject_request(
            request_id=request["id"],
            reviewed_by="ml-lead-789",
            review_notes="Insufficient accuracy",
            db_session=test_db,
        )

        # Get audit log
        audit_log = approval_service_no_auto_deploy.get_audit_log(
            request_id=request["id"],
            db_session=test_db,
        )

        # Find the 'rejected' entry
        rejected_entry = next(
            (e for e in audit_log if e["action"] == "rejected"),
            None
        )
        assert rejected_entry is not None
        assert rejected_entry["performed_by"] == "ml-lead-789"

    @pytest.mark.asyncio
    async def test_audit_log_for_cancelled_request(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """
        Test that audit log captures cancellation information.

        Validates:
        - Audit entry for 'cancelled' action exists
        """
        org_id = str(uuid4())

        # Create and cancel request
        request = approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="data-scientist-123",
            organization_id=org_id,
            db_session=test_db,
        )

        approval_service_no_auto_deploy.cancel_request(
            request_id=request["id"],
            cancelled_by="data-scientist-123",
            reason="Testing complete",
            db_session=test_db,
        )

        # Get audit log
        audit_log = approval_service_no_auto_deploy.get_audit_log(
            request_id=request["id"],
            db_session=test_db,
        )

        # Find the 'cancelled' entry
        cancelled_entry = next(
            (e for e in audit_log if e["action"] == "cancelled"),
            None
        )
        assert cancelled_entry is not None
        assert cancelled_entry["new_status"] == "cancelled"


class TestEndToEndApprovalWorkflow:
    """Complete end-to-end tests of the approval workflow lifecycle."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_approval_to_deployment_workflow(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        active_model_version: MLModelVersion,
        approval_service: ModelApprovalService,
    ):
        """
        Test the complete approval workflow from request to deployment.

        This test validates the entire lifecycle:
        1. Create model version deployment request
        2. Verify pending approval status
        3. Approve deployment request
        4. Verify model version is activated
        5. Verify audit trail is recorded

        Validates:
        - All components work together correctly
        - Data flows correctly through the system
        - Previous model is properly deactivated
        - Audit trail is complete
        """
        org_id = str(uuid4())
        requester_id = "data-scientist-123"
        reviewer_id = "ml-lead-789"

        # Step 1: Create model version deployment request
        request = approval_service.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by=requester_id,
            organization_id=org_id,
            justification="Model v2.1.0 shows 15% improvement in F1 score",
            target_environment="production",
            db_session=test_db,
        )

        assert request is not None, "Failed to create approval request"

        # Step 2: Verify pending approval status
        assert request["status"] == "pending"
        assert request["requested_by"] == requester_id
        assert request["target_environment"] == "production"

        # Verify model is not yet active
        await test_db.refresh(sample_model_version)
        assert sample_model_version.is_active is False

        # Step 3: Approve deployment request
        approval_result = approval_service.approve_request(
            request_id=request["id"],
            reviewed_by=reviewer_id,
            review_notes="Validated on shadow traffic. All metrics improved.",
            db_session=test_db,
        )

        assert approval_result is not None, "Failed to approve request"
        assert approval_result["status"] == "deployed"
        assert approval_result["deployed"] is True

        # Step 4: Verify model version is activated
        await test_db.refresh(sample_model_version)
        assert sample_model_version.is_active is True
        assert sample_model_version.is_experiment is False

        # Verify previous model is deactivated
        await test_db.refresh(active_model_version)
        assert active_model_version.is_active is False

        # Step 5: Verify audit trail is recorded
        audit_log = approval_service.get_audit_log(
            request_id=request["id"],
            db_session=test_db,
        )

        assert len(audit_log) >= 3  # created, approved, deployed

        # Verify audit entries
        actions = [entry["action"] for entry in audit_log]
        assert "created" in actions
        assert "approved" in actions or "deployed" in actions

        # Verify the created entry
        created_entry = next(e for e in audit_log if e["action"] == "created")
        assert created_entry["performed_by"] == requester_id
        assert created_entry["new_status"] == "pending"

    @pytest.mark.asyncio
    async def test_rejection_workflow(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """
        Test the complete rejection workflow.

        Validates:
        - Request is created in pending state
        - Rejection updates status correctly
        - Model remains inactive
        - Audit trail captures rejection
        """
        org_id = str(uuid4())

        # Create request
        request = approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="data-scientist-123",
            organization_id=org_id,
            justification="Requesting deployment",
            target_environment="production",
            db_session=test_db,
        )

        # Reject the request
        result = approval_service_no_auto_deploy.reject_request(
            request_id=request["id"],
            reviewed_by="ml-lead-789",
            review_notes="Model accuracy below 90% threshold",
            db_session=test_db,
        )

        assert result["status"] == "rejected"

        # Model should remain inactive
        await test_db.refresh(sample_model_version)
        assert sample_model_version.is_active is False

        # Audit trail should reflect rejection
        audit_log = approval_service_no_auto_deploy.get_audit_log(
            request_id=request["id"],
            db_session=test_db,
        )

        actions = [e["action"] for e in audit_log]
        assert "rejected" in actions

    @pytest.mark.asyncio
    async def test_cancellation_workflow(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """
        Test the complete cancellation workflow.

        Validates:
        - Request can be cancelled
        - Model remains inactive
        - Audit trail captures cancellation
        """
        org_id = str(uuid4())

        # Create request
        request = approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="data-scientist-123",
            organization_id=org_id,
            db_session=test_db,
        )

        # Cancel the request
        result = approval_service_no_auto_deploy.cancel_request(
            request_id=request["id"],
            cancelled_by="data-scientist-123",
            reason="Found issue in training data",
            db_session=test_db,
        )

        assert result["status"] == "cancelled"

        # Model should remain inactive
        await test_db.refresh(sample_model_version)
        assert sample_model_version.is_active is False


class TestStatisticsAndDashboard:
    """Tests for approval workflow statistics and dashboard data."""

    @pytest.mark.asyncio
    async def test_approval_statistics(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service: ModelApprovalService,
    ):
        """
        Test that approval statistics are computed correctly.

        Validates:
        - Total requests count
        - Status breakdown
        - Approval rate calculation
        """
        org_id = str(uuid4())

        # Create and approve a request
        request1 = approval_service.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="user1",
            organization_id=org_id,
            db_session=test_db,
        )
        approval_service.approve_request(
            request_id=request1["id"],
            reviewed_by="reviewer1",
            db_session=test_db,
        )

        # Create another model for a different request
        model2 = MLModelVersion(
            model_name="resume_parser",
            version="v1.0.0",
            is_active=False,
        )
        test_db.add(model2)
        await test_db.commit()
        await test_db.refresh(model2)

        # Create and reject a request
        request2 = approval_service.create_approval_request(
            model_version_id=str(model2.id),
            requested_by="user2",
            organization_id=org_id,
            db_session=test_db,
        )
        approval_service.reject_request(
            request_id=request2["id"],
            reviewed_by="reviewer1",
            review_notes="Rejected",
            db_session=test_db,
        )

        # Get statistics
        stats = approval_service.get_statistics(
            organization_id=org_id,
            db_session=test_db,
        )

        assert stats["total_requests"] >= 2
        assert stats["approved_requests"] >= 1
        assert stats["rejected_requests"] >= 1
        assert stats["approval_rate"] > 0

    @pytest.mark.asyncio
    async def test_dashboard_data(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service: ModelApprovalService,
    ):
        """
        Test that dashboard data includes all expected components.

        Validates:
        - Pending requests list
        - Recent approvals/rejections
        - Statistics summary
        """
        org_id = str(uuid4())
        user_id = "data-scientist-123"

        # Create a request
        approval_service.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by=user_id,
            organization_id=org_id,
            db_session=test_db,
        )

        # Get dashboard data
        dashboard = approval_service.get_dashboard_data(
            organization_id=org_id,
            user_id=user_id,
            db_session=test_db,
        )

        assert "pending_requests" in dashboard
        assert "recent_approvals" in dashboard
        assert "recent_rejections" in dashboard
        assert "stats" in dashboard
        assert "user_pending_count" in dashboard


class TestRequestListing:
    """Tests for listing and filtering approval requests."""

    @pytest.mark.asyncio
    async def test_list_requests_by_status(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test filtering requests by status."""
        org_id = str(uuid4())

        # Create a pending request
        approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="user1",
            organization_id=org_id,
            db_session=test_db,
        )

        # List pending requests
        pending, total = approval_service_no_auto_deploy.list_requests(
            organization_id=org_id,
            status=ApprovalStatus.PENDING,
            db_session=test_db,
        )

        assert total >= 1
        assert all(r["status"] == "pending" for r in pending)

    @pytest.mark.asyncio
    async def test_list_requests_by_organization(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test filtering requests by organization."""
        org_id = str(uuid4())

        # Create a request
        approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="user1",
            organization_id=org_id,
            db_session=test_db,
        )

        # List requests for this org
        requests, total = approval_service_no_auto_deploy.list_requests(
            organization_id=org_id,
            db_session=test_db,
        )

        assert total >= 1
        assert all(r["organization_id"] == org_id for r in requests)

    @pytest.mark.asyncio
    async def test_get_pending_requests(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test getting all pending requests."""
        org_id = str(uuid4())

        # Create a pending request
        approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="user1",
            organization_id=org_id,
            db_session=test_db,
        )

        # Get pending requests
        pending = approval_service_no_auto_deploy.get_pending_requests(
            organization_id=org_id,
            db_session=test_db,
        )

        assert len(pending) >= 1
        assert all(r["status"] == "pending" for r in pending)


class TestCanRequestApproval:
    """Tests for checking if approval can be requested."""

    @pytest.mark.asyncio
    async def test_can_request_approval_for_valid_model(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test that approval can be requested for valid model."""
        org_id = str(uuid4())

        result = approval_service_no_auto_deploy.can_request_approval(
            model_version_id=str(sample_model_version.id),
            organization_id=org_id,
            db_session=test_db,
        )

        assert result["can_request"] is True
        assert result["reason"] is None

    @pytest.mark.asyncio
    async def test_cannot_request_approval_for_nonexistent_model(
        self,
        test_db: AsyncSession,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test that approval cannot be requested for non-existent model."""
        org_id = str(uuid4())

        result = approval_service_no_auto_deploy.can_request_approval(
            model_version_id=str(uuid4()),
            organization_id=org_id,
            db_session=test_db,
        )

        assert result["can_request"] is False
        assert "not found" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_cannot_request_approval_for_active_model(
        self,
        test_db: AsyncSession,
        active_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test that approval cannot be requested for already active model."""
        org_id = str(uuid4())

        result = approval_service_no_auto_deploy.can_request_approval(
            model_version_id=str(active_model_version.id),
            organization_id=org_id,
            db_session=test_db,
        )

        assert result["can_request"] is False
        assert "already active" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_cannot_request_approval_with_pending_request(
        self,
        test_db: AsyncSession,
        pending_approval_request: ModelApprovalRequest,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test that approval cannot be requested when pending request exists."""
        org_id = str(uuid4())

        result = approval_service_no_auto_deploy.can_request_approval(
            model_version_id=str(pending_approval_request.model_version_id),
            organization_id=org_id,
            db_session=test_db,
        )

        assert result["can_request"] is False
        assert "already exists" in result["reason"].lower()
        assert result["existing_request"] is not None


class TestMarkDeployed:
    """Tests for manually marking requests as deployed."""

    @pytest.mark.asyncio
    async def test_mark_approved_request_as_deployed(
        self,
        test_db: AsyncSession,
        sample_model_version: MLModelVersion,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test marking an approved request as deployed."""
        org_id = str(uuid4())

        # Create and approve request (without auto-deploy)
        request = approval_service_no_auto_deploy.create_approval_request(
            model_version_id=str(sample_model_version.id),
            requested_by="user1",
            organization_id=org_id,
            target_environment="staging",  # Staging so it doesn't auto-deploy
            db_session=test_db,
        )

        approval_service_no_auto_deploy.approve_request(
            request_id=request["id"],
            reviewed_by="reviewer1",
            db_session=test_db,
        )

        # Manually mark as deployed
        result = approval_service_no_auto_deploy.mark_deployed(
            request_id=request["id"],
            db_session=test_db,
        )

        assert result["status"] == "deployed"
        assert result["previous_status"] == "approved"

    @pytest.mark.asyncio
    async def test_cannot_mark_non_approved_as_deployed(
        self,
        test_db: AsyncSession,
        pending_approval_request: ModelApprovalRequest,
        approval_service_no_auto_deploy: ModelApprovalService,
    ):
        """Test that pending requests cannot be marked as deployed."""
        result = approval_service_no_auto_deploy.mark_deployed(
            request_id=str(pending_approval_request.id),
            db_session=test_db,
        )

        assert result is None


# ============================================================================
# Test Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers for approval workflow tests."""
    config.addinivalue_line(
        "markers",
        "approval_workflow: Marks tests as approval workflow integration tests"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
