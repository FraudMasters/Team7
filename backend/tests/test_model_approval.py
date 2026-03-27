"""
Tests for model approval workflow.

Tests cover model creation, relationships, validation methods,
enum values, and edge cases for ModelApprovalRequest and ApprovalStatus.
"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from models.model_approval import (
    ModelApprovalRequest,
    ApprovalStatus,
)
from models.base import Base


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""

    def test_status_values(self):
        """Test that all expected status values exist."""
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.DEPLOYED.value == "deployed"
        assert ApprovalStatus.CANCELLED.value == "cancelled"

    def test_status_count(self):
        """Test that there are exactly 5 status values."""
        assert len(ApprovalStatus) == 5

    def test_status_is_string_enum(self):
        """Test that ApprovalStatus inherits from str and enum."""
        assert ApprovalStatus.PENDING == "pending"
        assert ApprovalStatus.APPROVED == "approved"


class TestModelApprovalRequestModel:
    """Tests for ModelApprovalRequest model."""

    def test_model_inheritance(self):
        """Test that ModelApprovalRequest inherits from proper base classes."""
        assert issubclass(ModelApprovalRequest, Base)
        # Check for mixin attributes
        request = ModelApprovalRequest()
        assert hasattr(request, "id")
        assert hasattr(request, "created_at")
        assert hasattr(request, "updated_at")

    def test_table_name(self):
        """Test that table name is correctly set."""
        assert ModelApprovalRequest.__tablename__ == "model_approval_requests"

    def test_create_minimal_approval_request(self):
        """Test creating a ModelApprovalRequest with minimal required fields."""
        version_id = uuid4()

        request = ModelApprovalRequest(
            model_version_id=version_id,
            requested_by="user-123",
            organization_id="org-456",
        )

        assert request.model_version_id == version_id
        assert request.requested_by == "user-123"
        assert request.organization_id == "org-456"
        assert request.status == ApprovalStatus.PENDING
        assert request.target_environment == "staging"
        assert request.reviewed_by is None
        assert request.requested_at is None
        assert request.reviewed_at is None
        assert request.justification is None
        assert request.review_notes is None

    def test_create_full_approval_request(self):
        """Test creating a ModelApprovalRequest with all fields."""
        version_id = uuid4()
        now = datetime.now(timezone.utc)

        request = ModelApprovalRequest(
            model_version_id=version_id,
            status=ApprovalStatus.APPROVED,
            requested_by="user-123",
            reviewed_by="reviewer-456",
            requested_at=now - timedelta(hours=2),
            reviewed_at=now,
            justification="Improved model accuracy by 15%",
            review_notes="Approved after thorough testing",
            target_environment="production",
            organization_id="org-789",
        )

        assert request.model_version_id == version_id
        assert request.status == ApprovalStatus.APPROVED
        assert request.requested_by == "user-123"
        assert request.reviewed_by == "reviewer-456"
        assert request.requested_at == now - timedelta(hours=2)
        assert request.reviewed_at == now
        assert request.justification == "Improved model accuracy by 15%"
        assert request.review_notes == "Approved after thorough testing"
        assert request.target_environment == "production"
        assert request.organization_id == "org-789"

    def test_default_status_is_pending(self):
        """Test that default status is PENDING."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )
        assert request.status == ApprovalStatus.PENDING

    def test_default_target_environment_is_staging(self):
        """Test that default target_environment is staging."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )
        assert request.target_environment == "staging"

    def test_repr(self):
        """Test __repr__ method."""
        request_id = uuid4()
        version_id = uuid4()

        request = ModelApprovalRequest(
            id=request_id,
            model_version_id=version_id,
            status=ApprovalStatus.APPROVED,
            requested_by="user-123",
            organization_id="org-456",
        )

        repr_str = repr(request)
        assert "ModelApprovalRequest" in repr_str
        assert str(request_id) in repr_str
        assert str(version_id) in repr_str
        assert "approved" in repr_str
        assert "user-123" in repr_str

    def test_status_can_be_changed(self):
        """Test that status can be changed through the workflow."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )
        assert request.status == ApprovalStatus.PENDING

        request.status = ApprovalStatus.APPROVED
        assert request.status == ApprovalStatus.APPROVED

        request.status = ApprovalStatus.DEPLOYED
        assert request.status == ApprovalStatus.DEPLOYED

    def test_status_can_be_rejected(self):
        """Test that status can be set to rejected."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )

        request.status = ApprovalStatus.REJECTED
        assert request.status == ApprovalStatus.REJECTED

    def test_status_can_be_cancelled(self):
        """Test that status can be set to cancelled."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )

        request.status = ApprovalStatus.CANCELLED
        assert request.status == ApprovalStatus.CANCELLED

    def test_optional_fields_are_nullable(self):
        """Test that optional fields can be None."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            reviewed_by=None,
            requested_at=None,
            reviewed_at=None,
            justification=None,
            review_notes=None,
        )

        assert request.reviewed_by is None
        assert request.requested_at is None
        assert request.reviewed_at is None
        assert request.justification is None
        assert request.review_notes is None

    def test_model_version_id_is_uuid(self):
        """Test that model_version_id accepts UUID values."""
        version_id = uuid4()
        request = ModelApprovalRequest(
            model_version_id=version_id,
            requested_by="user-123",
            organization_id="org-456",
        )

        assert request.model_version_id == version_id

    def test_all_status_values(self):
        """Test creating requests with all status values."""
        version_id = uuid4()

        for status in ApprovalStatus:
            request = ModelApprovalRequest(
                model_version_id=version_id,
                status=status,
                requested_by="user-123",
                organization_id="org-456",
            )
            assert request.status == status

    def test_various_target_environments(self):
        """Test creating requests with different target environments."""
        environments = ["staging", "production", "canary", "development"]

        for env in environments:
            request = ModelApprovalRequest(
                model_version_id=uuid4(),
                requested_by="user-123",
                organization_id="org-456",
                target_environment=env,
            )
            assert request.target_environment == env


class TestModelApprovalRequestTimestamps:
    """Tests for timestamp fields in ModelApprovalRequest."""

    def test_requested_at_timezone_aware(self):
        """Test that requested_at can store timezone-aware datetime."""
        now = datetime.now(timezone.utc)
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            requested_at=now,
        )

        assert request.requested_at == now

    def test_reviewed_at_timezone_aware(self):
        """Test that reviewed_at can store timezone-aware datetime."""
        now = datetime.now(timezone.utc)
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            reviewed_at=now,
        )

        assert request.reviewed_at == now

    def test_both_timestamps_set(self):
        """Test that both timestamps can be set."""
        requested = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        reviewed = datetime(2024, 1, 16, 14, 45, 0, tzinfo=timezone.utc)

        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            requested_at=requested,
            reviewed_at=reviewed,
        )

        assert request.requested_at == requested
        assert request.reviewed_at == reviewed

    def test_timestamp_ordering(self):
        """Test that requested_at can be before reviewed_at."""
        requested = datetime.now(timezone.utc) - timedelta(hours=24)
        reviewed = datetime.now(timezone.utc)

        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            requested_at=requested,
            reviewed_at=reviewed,
        )

        assert request.requested_at < request.reviewed_at


class TestModelApprovalRequestTextFields:
    """Tests for text fields in ModelApprovalRequest."""

    def test_justification_text(self):
        """Test that justification can store text."""
        justification = "This model improves matching accuracy by optimizing the ranking algorithm."
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            justification=justification,
        )

        assert request.justification == justification

    def test_review_notes_text(self):
        """Test that review_notes can store text."""
        notes = "Model has been validated on test data. Approved for production deployment."
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            review_notes=notes,
        )

        assert request.review_notes == notes

    def test_long_justification(self):
        """Test that justification can store long text."""
        long_justification = "A" * 2000
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            justification=long_justification,
        )

        assert request.justification == long_justification

    def test_long_review_notes(self):
        """Test that review_notes can store long text."""
        long_notes = "B" * 2000
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            review_notes=long_notes,
        )

        assert request.review_notes == long_notes


class TestModelApprovalRequestEdgeCases:
    """Tests for edge cases in ModelApprovalRequest."""

    def test_empty_requested_by(self):
        """Test request with empty string requested_by."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="",
            organization_id="org-456",
        )
        assert request.requested_by == ""

    def test_empty_organization_id(self):
        """Test request with empty string organization_id."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="",
        )
        assert request.organization_id == ""

    def test_empty_target_environment(self):
        """Test request with empty string target_environment."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            target_environment="",
        )
        assert request.target_environment == ""

    def test_empty_justification(self):
        """Test request with empty string justification."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            justification="",
        )
        assert request.justification == ""

    def test_empty_review_notes(self):
        """Test request with empty string review_notes."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            review_notes="",
        )
        assert request.review_notes == ""

    def test_special_characters_in_justification(self):
        """Test justification with special characters."""
        justification = "Improved metrics: 15% ↑ accuracy, 10% ↓ latency (p<0.05)"
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            justification=justification,
        )
        assert request.justification == justification

    def test_multiline_justification(self):
        """Test justification with newlines."""
        justification = "Key improvements:\n- Better accuracy\n- Lower latency\n- Improved recall"
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            justification=justification,
        )
        assert "\n" in request.justification


class TestModelApprovalRequestWorkflowScenarios:
    """Tests for typical approval workflow scenarios."""

    def test_pending_to_approved_workflow(self):
        """Test typical pending to approved workflow."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )

        # Initial state
        assert request.status == ApprovalStatus.PENDING
        assert request.reviewed_by is None

        # Approval
        request.status = ApprovalStatus.APPROVED
        request.reviewed_by = "reviewer-789"
        request.review_notes = "All tests passed"
        request.reviewed_at = datetime.now(timezone.utc)

        assert request.status == ApprovalStatus.APPROVED
        assert request.reviewed_by == "reviewer-789"

    def test_pending_to_rejected_workflow(self):
        """Test typical pending to rejected workflow."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )

        # Rejection
        request.status = ApprovalStatus.REJECTED
        request.reviewed_by = "reviewer-789"
        request.review_notes = "Model accuracy below threshold"
        request.reviewed_at = datetime.now(timezone.utc)

        assert request.status == ApprovalStatus.REJECTED
        assert request.review_notes == "Model accuracy below threshold"

    def test_pending_to_cancelled_workflow(self):
        """Test typical pending to cancelled workflow."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )

        # Cancellation
        request.status = ApprovalStatus.CANCELLED
        request.review_notes = "Cancelled by requester - found bug in model"

        assert request.status == ApprovalStatus.CANCELLED

    def test_approved_to_deployed_workflow(self):
        """Test approved to deployed workflow."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            status=ApprovalStatus.APPROVED,
        )

        # Deployment
        request.status = ApprovalStatus.DEPLOYED
        request.review_notes = "Successfully deployed to production"

        assert request.status == ApprovalStatus.DEPLOYED

    def test_production_deployment_request(self):
        """Test request for production deployment."""
        now = datetime.now(timezone.utc)

        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="data-scientist-123",
            reviewed_by="ml-lead-456",
            requested_at=now - timedelta(days=2),
            reviewed_at=now - timedelta(hours=4),
            status=ApprovalStatus.APPROVED,
            justification="Model v2.1 shows 20% improvement in matching quality",
            review_notes="Validated on shadow traffic for 48 hours. Approved.",
            target_environment="production",
            organization_id="org-789",
        )

        assert request.target_environment == "production"
        assert request.status == ApprovalStatus.APPROVED


class TestModelApprovalRequestDefaultsAndConstraints:
    """Tests for default values and constraints."""

    def test_status_default(self):
        """Test that status defaults to PENDING."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )
        assert request.status == ApprovalStatus.PENDING

    def test_target_environment_default(self):
        """Test that target_environment defaults to staging."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )
        assert request.target_environment == "staging"

    def test_uuid_primary_key(self):
        """Test that model uses UUID as primary key."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )

        # Should have id attribute from UUIDMixin
        assert hasattr(request, "id")

    def test_timestamp_mixin_attributes(self):
        """Test that model has timestamp attributes from TimestampMixin."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )

        # Should have timestamp attributes from TimestampMixin
        assert hasattr(request, "created_at")
        assert hasattr(request, "updated_at")

    def test_required_fields(self):
        """Test that required fields must be provided."""
        # This test documents the required fields
        # Actual validation would occur at the database level
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
        )

        # These are required
        assert request.model_version_id is not None
        assert request.requested_by is not None
        assert request.organization_id is not None
        assert request.status is not None
        assert request.target_environment is not None


class TestApprovalStatusEnumBehavior:
    """Tests for ApprovalStatus enum behavior."""

    def test_status_string_comparison(self):
        """Test that status enum can be compared with strings."""
        request = ModelApprovalRequest(
            model_version_id=uuid4(),
            requested_by="user-123",
            organization_id="org-456",
            status=ApprovalStatus.APPROVED,
        )

        assert request.status.value == "approved"
        assert request.status == ApprovalStatus.APPROVED
        assert str(request.status) == "approved"

    def test_status_inheritance_from_str(self):
        """Test that ApprovalStatus values are strings."""
        assert isinstance(ApprovalStatus.PENDING, str)
        assert ApprovalStatus.PENDING == "pending"

    def test_all_statuses_string_equivalence(self):
        """Test all status values are equivalent to their string values."""
        status_mapping = {
            ApprovalStatus.PENDING: "pending",
            ApprovalStatus.APPROVED: "approved",
            ApprovalStatus.REJECTED: "rejected",
            ApprovalStatus.DEPLOYED: "deployed",
            ApprovalStatus.CANCELLED: "cancelled",
        }

        for status, expected_str in status_mapping.items():
            assert status == expected_str
            assert status.value == expected_str
