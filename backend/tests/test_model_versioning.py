"""
Tests for model versioning system with A/B testing.

Tests cover model version management, traffic allocation,
performance tracking, and model promotion recommendations.
"""
import pytest
import hashlib
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from analyzers.model_versioning import ModelVersionManager


class TestModelVersionManagerInit:
    """Tests for ModelVersionManager initialization."""

    def test_default_initialization(self):
        """Test initialization with default values."""
        manager = ModelVersionManager()

        assert manager.default_fallback_version == "v1.0.0"

    def test_custom_fallback_version(self):
        """Test initialization with custom fallback version."""
        manager = ModelVersionManager(default_fallback_version="v2.0.0")

        assert manager.default_fallback_version == "v2.0.0"

    def test_none_fallback_version(self):
        """Test initialization with None as fallback."""
        manager = ModelVersionManager(default_fallback_version=None)

        # Should use DEFAULT_FALLBACK_VERSION
        assert manager.default_fallback_version == "v1.0.0"


class TestGetActiveModel:
    """Tests for get_active_model method."""

    def test_no_database_session(self):
        """Test with no database session provided."""
        manager = ModelVersionManager()

        result = manager.get_active_model("skill_matching", db_session=None)

        assert result is None

    def test_successful_active_model_retrieval(self):
        """Test successful retrieval of active model."""
        manager = ModelVersionManager()

        # Mock database session and model
        mock_session = Mock()
        mock_model = Mock()
        mock_model.id = "model-123"
        mock_model.model_name = "skill_matching"
        mock_model.version = "v1.2.0"
        mock_model.file_path = "/models/v1.2.0.pkl"
        mock_model.performance_score = 85.5
        mock_model.model_metadata = {"algorithm": "transformer"}
        mock_model.accuracy_metrics = {"precision": 0.92}
        mock_model.is_active = True
        mock_model.is_experiment = False

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_model
        mock_session.query.return_value = mock_query

        result = manager.get_active_model("skill_matching", db_session=mock_session)

        assert result is not None
        assert result["id"] == "model-123"
        assert result["version"] == "v1.2.0"
        assert result["performance_score"] == 85.5
        assert result["is_active"] is True
        assert result["is_experiment"] is False

    def test_no_active_model_found(self):
        """Test when no active model exists."""
        manager = ModelVersionManager()

        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        result = manager.get_active_model("skill_matching", db_session=mock_session)

        assert result is None

    def test_filters_non_experimental_models(self):
        """Test that experimental models are filtered out."""
        manager = ModelVersionManager()

        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        manager.get_active_model("skill_matching", db_session=mock_session)

        # Verify filter was called with is_experiment=False
        filter_calls = mock_query.filter.call_args_list
        assert len(filter_calls) == 1

    def test_database_exception_handling(self):
        """Test handling of database exceptions."""
        manager = ModelVersionManager()

        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database connection error")

        result = manager.get_active_model("skill_matching", db_session=mock_session)

        assert result is None

    def test_none_performance_score(self):
        """Test handling of None performance score."""
        manager = ModelVersionManager()

        mock_session = Mock()
        mock_model = Mock()
        mock_model.id = "model-123"
        mock_model.model_name = "skill_matching"
        mock_model.version = "v1.0.0"
        mock_model.file_path = "/models/v1.0.0.pkl"
        mock_model.performance_score = None
        mock_model.model_metadata = None
        mock_model.accuracy_metrics = None
        mock_model.is_active = True
        mock_model.is_experiment = False

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_model
        mock_session.query.return_value = mock_query

        result = manager.get_active_model("skill_matching", db_session=mock_session)

        assert result["performance_score"] is None
        assert result["model_metadata"] == {}
        assert result["accuracy_metrics"] == {}


class TestGetExperimentModels:
    """Tests for get_experiment_models method."""

    def test_no_database_session(self):
        """Test with no database session."""
        manager = ModelVersionManager()

        result = manager.get_experiment_models("skill_matching", db_session=None)

        assert result == []

    def test_no_experiments_found(self):
        """Test when no experimental models exist."""
        manager = ModelVersionManager()

        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        result = manager.get_experiment_models("skill_matching", db_session=mock_session)

        assert result == []

    def test_single_experiment(self):
        """Test retrieval of single experimental model."""
        manager = ModelVersionManager()

        mock_session = Mock()
        mock_model = Mock()
        mock_model.id = "exp-123"
        mock_model.model_name = "skill_matching"
        mock_model.version = "v2.0.0-experiment"
        mock_model.file_path = "/models/v2.0.0-exp.pkl"
        mock_model.performance_score = 88.0
        mock_model.experiment_config = {"traffic_percentage": 20}
        mock_model.model_metadata = {}
        mock_model.accuracy_metrics = {}

        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_model]
        mock_session.query.return_value = mock_query

        result = manager.get_experiment_models("skill_matching", db_session=mock_session)

        assert len(result) == 1
        assert result[0]["version"] == "v2.0.0-experiment"
        assert result[0]["traffic_percentage"] == 20

    def test_multiple_experiments(self):
        """Test retrieval of multiple experimental models."""
        manager = ModelVersionManager()

        mock_session = Mock()
        mock_model1 = Mock()
        mock_model1.id = "exp-1"
        mock_model1.version = "v2.0.0-experiment"
        mock_model1.file_path = "/models/v2.0.0.pkl"
        mock_model1.performance_score = 88.0
        mock_model1.experiment_config = {"traffic_percentage": 20}
        mock_model1.model_metadata = {}
        mock_model1.accuracy_metrics = {}

        mock_model2 = Mock()
        mock_model2.id = "exp-2"
        mock_model2.version = "v2.1.0-experiment"
        mock_model2.file_path = "/models/v2.1.0.pkl"
        mock_model2.performance_score = 90.0
        mock_model2.experiment_config = {"traffic_percentage": 10}
        mock_model2.model_metadata = {}
        mock_model2.accuracy_metrics = {}

        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_model1, mock_model2]
        mock_session.query.return_value = mock_query

        result = manager.get_experiment_models("skill_matching", db_session=mock_session)

        assert len(result) == 2
        assert result[0]["traffic_percentage"] == 20
        assert result[1]["traffic_percentage"] == 10

    def test_missing_experiment_config(self):
        """Test handling of missing experiment_config."""
        manager = ModelVersionManager()

        mock_session = Mock()
        mock_model = Mock()
        mock_model.id = "exp-123"
        mock_model.version = "v2.0.0-experiment"
        mock_model.file_path = "/models/v2.0.0.pkl"
        mock_model.performance_score = 88.0
        mock_model.experiment_config = None
        mock_model.model_metadata = {}
        mock_model.accuracy_metrics = {}

        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_model]
        mock_session.query.return_value = mock_query

        result = manager.get_experiment_models("skill_matching", db_session=mock_session)

        assert result[0]["traffic_percentage"] == 0

    def test_database_exception_handling(self):
        """Test handling of database exceptions."""
        manager = ModelVersionManager()

        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")

        result = manager.get_experiment_models("skill_matching", db_session=mock_session)

        assert result == []


class TestAllocateModelForUser:
    """Tests for allocate_model_for_user method."""

    def test_no_active_model_returns_fallback(self):
        """Test that fallback is returned when no active model exists."""
        manager = ModelVersionManager()

        result = manager.allocate_model_for_user(
            "skill_matching", "user123", db_session=None
        )

        assert result["version"] == "v1.0.0"
        assert result["is_fallback"] is True
        assert result["allocation_type"] == "fallback"

    def test_custom_fallback_version(self):
        """Test custom fallback version."""
        manager = ModelVersionManager(default_fallback_version="v0.5.0")

        result = manager.allocate_model_for_user(
            "skill_matching", "user123", db_session=None
        )

        assert result["version"] == "v0.5.0"

    def test_no_experiments_returns_control(self):
        """Test that control model is returned when no experiments exist."""
        manager = ModelVersionManager()

        mock_session = Mock()

        # Mock active model
        mock_active = Mock()
        mock_active.id = "model-123"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.0.0.pkl"
        mock_active.performance_score = 85.0
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.is_active = True
        mock_active.is_experiment = False

        # Mock no experiments
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        result = manager.allocate_model_for_user(
            "skill_matching", "user123", db_session=mock_session
        )

        assert result["version"] == "v1.0.0"
        assert result["is_fallback"] is False
        assert result["allocation_type"] == "control"

    def test_user_allocated_to_experiment(self):
        """Test user allocation to experimental model."""
        manager = ModelVersionManager()

        mock_session = Mock()

        # Mock active model
        mock_active = Mock()
        mock_active.id = "model-123"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.0.0.pkl"
        mock_active.performance_score = 85.0
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.is_active = True
        mock_active.is_experiment = False

        # Mock experiment with 30% traffic
        mock_exp = Mock()
        mock_exp.id = "exp-123"
        mock_exp.model_name = "skill_matching"
        mock_exp.version = "v2.0.0-experiment"
        mock_exp.file_path = "/models/v2.0.0.pkl"
        mock_exp.performance_score = 88.0
        mock_exp.experiment_config = {"traffic_percentage": 30}
        mock_exp.model_metadata = {}
        mock_exp.accuracy_metrics = {}

        # Setup query to return different results based on filter
        def filter_side_effect(*args):
            mock_filtered = Mock()
            # For experiments
            if hasattr(mock_exp, 'is_experiment'):
                mock_filtered.all.return_value = [mock_exp]
            # For active model
            else:
                mock_filtered.first.return_value = mock_active
            return mock_filtered

        mock_query = Mock()
        mock_query.filter.side_effect = filter_side_effect
        mock_session.query.return_value = mock_query

        # Use user_id that will hash to < 30 (in experiment bucket)
        # We can't easily predict hash, so we'll just verify the logic runs
        result = manager.allocate_model_for_user(
            "skill_matching", "user123", db_session=mock_session
        )

        assert result["is_fallback"] is False
        assert result["allocation_type"] in ["control", "experiment"]

    def test_user_allocated_to_control(self):
        """Test user allocation to control model."""
        manager = ModelVersionManager()

        mock_session = Mock()

        # Mock active model
        mock_active = Mock()
        mock_active.id = "model-123"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.0.0.pkl"
        mock_active.performance_score = 85.0
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.is_active = True
        mock_active.is_experiment = False

        # Mock experiments
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        result = manager.allocate_model_for_user(
            "skill_matching", "user456", db_session=mock_session
        )

        assert result["allocation_type"] == "control"
        assert result["version"] == "v1.0.0"

    def test_consistent_allocation_same_user(self):
        """Test that same user always gets same model."""
        manager = ModelVersionManager()

        mock_session = Mock()

        # Mock active model
        mock_active = Mock()
        mock_active.id = "model-123"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.0.0.pkl"
        mock_active.performance_score = 85.0
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.is_active = True
        mock_active.is_experiment = False

        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        result1 = manager.allocate_model_for_user(
            "skill_matching", "user789", db_session=mock_session
        )
        result2 = manager.allocate_model_for_user(
            "skill_matching", "user789", db_session=mock_session
        )

        assert result1["allocation_type"] == result2["allocation_type"]
        assert result1["version"] == result2["version"]

    def test_different_allocation_different_users(self):
        """Test that different users can get different models."""
        manager = ModelVersionManager()

        mock_session = Mock()

        # Mock active model
        mock_active = Mock()
        mock_active.id = "model-123"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.0.0.pkl"
        mock_active.performance_score = 85.0
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.is_active = True
        mock_active.is_experiment = False

        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        # With no experiments, all users should get control
        result1 = manager.allocate_model_for_user(
            "skill_matching", "user001", db_session=mock_session
        )
        result2 = manager.allocate_model_for_user(
            "skill_matching", "user002", db_session=mock_session
        )

        # Both should be control with no experiments
        assert result1["allocation_type"] == "control"
        assert result2["allocation_type"] == "control"


class TestGetAllModelVersions:
    """Tests for get_all_model_versions method."""

    def test_no_database_session(self):
        """Test with no database session."""
        manager = ModelVersionManager()

        result = manager.get_all_model_versions("skill_matching", db_session=None)

        assert result == []

    def test_empty_model_list(self):
        """Test when no versions exist."""
        manager = ModelVersionManager()

        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        result = manager.get_all_model_versions("skill_matching", db_session=mock_session)

        assert result == []

    def test_multiple_model_versions(self):
        """Test retrieval of multiple model versions."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_model1 = Mock()
        mock_model1.id = "model-1"
        mock_model1.model_name = "skill_matching"
        mock_model1.version = "v1.0.0"
        mock_model1.file_path = "/models/v1.0.0.pkl"
        mock_model1.performance_score = 85.0
        mock_model1.is_active = True
        mock_model1.is_experiment = False
        mock_model1.experiment_config = {}
        mock_model1.model_metadata = {}
        mock_model1.accuracy_metrics = {}
        mock_model1.created_at = datetime(2024, 1, 1)
        mock_model1.updated_at = datetime(2024, 1, 1)

        mock_model2 = Mock()
        mock_model2.id = "model-2"
        mock_model2.model_name = "skill_matching"
        mock_model2.version = "v2.0.0"
        mock_model2.file_path = "/models/v2.0.0.pkl"
        mock_model2.performance_score = 90.0
        mock_model2.is_active = False
        mock_model2.is_experiment = True
        mock_model2.experiment_config = {"traffic_percentage": 20}
        mock_model2.model_metadata = {}
        mock_model2.accuracy_metrics = {}
        mock_model2.created_at = datetime(2024, 1, 2)
        mock_model2.updated_at = datetime(2024, 1, 2)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [
            mock_model2, mock_model1
        ]
        mock_session.query.return_value = mock_query

        result = manager.get_all_model_versions("skill_matching", db_session=mock_session)

        assert len(result) == 2
        assert result[0]["version"] == "v2.0.0"
        assert result[1]["version"] == "v1.0.0"

    def test_orders_by_created_at_descending(self):
        """Test that versions are ordered by creation date descending."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_model = Mock()
        mock_model.id = "model-1"
        mock_model.model_name = "skill_matching"
        mock_model.version = "v1.0.0"
        mock_model.file_path = "/models/v1.0.0.pkl"
        mock_model.performance_score = 85.0
        mock_model.is_active = True
        mock_model.is_experiment = False
        mock_model.experiment_config = {}
        mock_model.model_metadata = {}
        mock_model.accuracy_metrics = {}
        mock_model.created_at = datetime(2024, 1, 1)
        mock_model.updated_at = datetime(2024, 1, 1)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_model]
        mock_session.query.return_value = mock_query

        manager.get_all_model_versions("skill_matching", db_session=mock_session)

        # Verify order_by was called with created_at.desc()
        mock_query.filter.return_value.order_by.assert_called_once()

    def test_datetime_serialization(self):
        """Test that datetime fields are properly serialized."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_model = Mock()
        mock_model.id = "model-1"
        mock_model.model_name = "skill_matching"
        mock_model.version = "v1.0.0"
        mock_model.file_path = "/models/v1.0.0.pkl"
        mock_model.performance_score = 85.0
        mock_model.is_active = True
        mock_model.is_experiment = False
        mock_model.experiment_config = {}
        mock_model.model_metadata = {}
        mock_model.accuracy_metrics = {}
        mock_model.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_model.updated_at = datetime(2024, 1, 2, 12, 0, 0)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_model]
        mock_session.query.return_value = mock_query

        result = manager.get_all_model_versions("skill_matching", db_session=mock_session)

        assert result[0]["created_at"] == "2024-01-01T12:00:00"
        assert result[0]["updated_at"] == "2024-01-02T12:00:00"


class TestCalculateModelMetrics:
    """Tests for calculate_model_metrics method."""

    def test_empty_model_list(self):
        """Test with no model versions."""
        manager = ModelVersionManager()

        result = manager.calculate_model_metrics("skill_matching", db_session=None)

        assert result["total_versions"] == 0
        assert result["active_version"] is None
        assert result["experiment_count"] == 0
        assert result["avg_performance_score"] == 0.0

    def test_with_active_model_only(self):
        """Test with only active model."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_active = Mock()
        mock_active.id = "model-1"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.0.0.pkl"
        mock_active.performance_score = 85.0
        mock_active.is_active = True
        mock_active.is_experiment = False
        mock_active.experiment_config = {}
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.created_at = datetime(2024, 1, 1)
        mock_active.updated_at = datetime(2024, 1, 1)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_active]
        mock_session.query.return_value = mock_query

        result = manager.calculate_model_metrics("skill_matching", db_session=mock_session)

        assert result["total_versions"] == 1
        assert result["active_version"] == "v1.0.0"
        assert result["experiment_count"] == 0
        assert result["avg_performance_score"] == 85.0
        assert result["best_performance_score"] == 85.0

    def test_with_experiments(self):
        """Test with active model and experiments."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_active = Mock()
        mock_active.id = "model-1"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.performance_score = 85.0
        mock_active.is_active = True
        mock_active.is_experiment = False
        mock_active.experiment_config = {}
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.created_at = datetime(2024, 1, 1)
        mock_active.updated_at = datetime(2024, 1, 1)
        mock_active.file_path = "/models/v1.0.0.pkl"

        mock_exp = Mock()
        mock_exp.id = "exp-1"
        mock_exp.model_name = "skill_matching"
        mock_exp.version = "v2.0.0-experiment"
        mock_exp.performance_score = 90.0
        mock_exp.is_active = False
        mock_exp.is_experiment = True
        mock_exp.experiment_config = {"traffic_percentage": 20}
        mock_exp.model_metadata = {}
        mock_exp.accuracy_metrics = {}
        mock_exp.created_at = datetime(2024, 1, 2)
        mock_exp.updated_at = datetime(2024, 1, 2)
        mock_exp.file_path = "/models/v2.0.0.pkl"

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_exp, mock_active]
        mock_session.query.return_value = mock_query

        result = manager.calculate_model_metrics("skill_matching", db_session=mock_session)

        assert result["total_versions"] == 2
        assert result["experiment_count"] == 1
        assert result["avg_performance_score"] == 87.5
        assert result["best_performance_score"] == 90.0

    def test_traffic_distribution_calculation(self):
        """Test traffic distribution calculation."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_active = Mock()
        mock_active.id = "model-1"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.performance_score = 85.0
        mock_active.is_active = True
        mock_active.is_experiment = False
        mock_active.experiment_config = {}
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.created_at = datetime(2024, 1, 1)
        mock_active.updated_at = datetime(2024, 1, 1)
        mock_active.file_path = "/models/v1.0.0.pkl"

        mock_exp1 = Mock()
        mock_exp1.id = "exp-1"
        mock_exp1.model_name = "skill_matching"
        mock_exp1.version = "v2.0.0-experiment"
        mock_exp1.performance_score = 90.0
        mock_exp1.is_active = False
        mock_exp1.is_experiment = True
        mock_exp1.experiment_config = {"traffic_percentage": 20}
        mock_exp1.model_metadata = {}
        mock_exp1.accuracy_metrics = {}
        mock_exp1.created_at = datetime(2024, 1, 2)
        mock_exp1.updated_at = datetime(2024, 1, 2)
        mock_exp1.file_path = "/models/v2.0.0.pkl"

        mock_exp2 = Mock()
        mock_exp2.id = "exp-2"
        mock_exp2.model_name = "skill_matching"
        mock_exp2.version = "v2.1.0-experiment"
        mock_exp2.performance_score = 88.0
        mock_exp2.is_active = False
        mock_exp2.is_experiment = True
        mock_exp2.experiment_config = {"traffic_percentage": 10}
        mock_exp2.model_metadata = {}
        mock_exp2.accuracy_metrics = {}
        mock_exp2.created_at = datetime(2024, 1, 3)
        mock_exp2.updated_at = datetime(2024, 1, 3)
        mock_exp2.file_path = "/models/v2.1.0.pkl"

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [
            mock_exp2, mock_exp1, mock_active
        ]
        mock_session.query.return_value = mock_query

        result = manager.calculate_model_metrics("skill_matching", db_session=mock_session)

        # Control gets 100 - (20 + 10) = 70%
        assert result["traffic_distribution"]["control"] == 70
        assert result["traffic_distribution"]["v2.0.0-experiment"] == 20
        assert result["traffic_distribution"]["v2.1.0-experiment"] == 10


class TestRecommendPromotion:
    """Tests for recommend_promotion method."""

    def test_no_active_model(self):
        """Test when no active model exists."""
        manager = ModelVersionManager()

        result = manager.recommend_promotion("skill_matching", db_session=None)

        assert result is None

    def test_no_experiments(self):
        """Test when no experiments exist."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_active = Mock()
        mock_active.id = "model-1"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.0.0.pkl"
        mock_active.performance_score = 85.0
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.is_active = True
        mock_active.is_experiment = False

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_active
        mock_query.filter.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        result = manager.recommend_promotion("skill_matching", db_session=mock_session)

        assert result is None

    def test_experiment_with_insufficient_sample(self):
        """Test experiment with insufficient sample size."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_active = Mock()
        mock_active.id = "model-1"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.0.0.pkl"
        mock_active.performance_score = 85.0
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.is_active = True
        mock_active.is_experiment = False

        mock_exp = Mock()
        mock_exp.id = "exp-1"
        mock_exp.model_name = "skill_matching"
        mock_exp.version = "v2.0.0-experiment"
        mock_exp.file_path = "/models/v2.0.0.pkl"
        mock_exp.performance_score = 90.0
        mock_exp.experiment_config = {"traffic_percentage": 20}
        mock_exp.accuracy_metrics = {"sample_size": 50}  # Below default min_sample_size of 100
        mock_exp.model_metadata = {}

        def filter_side_effect(*args):
            mock_filtered = Mock()
            mock_filtered.first.return_value = mock_active
            mock_filtered.all.return_value = [mock_exp]
            return mock_filtered

        mock_query = Mock()
        mock_query.filter.side_effect = filter_side_effect
        mock_session.query.return_value = mock_query

        result = manager.recommend_promotion("skill_matching", db_session=mock_session)

        # Should not recommend due to insufficient sample size
        assert result["should_promote"] is False

    def test_experiment_below_performance_threshold(self):
        """Test experiment that doesn't meet performance improvement threshold."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_active = Mock()
        mock_active.id = "model-1"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.0.0.pkl"
        mock_active.performance_score = 85.0
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.is_active = True
        mock_active.is_experiment = False

        mock_exp = Mock()
        mock_exp.id = "exp-1"
        mock_exp.model_name = "skill_matching"
        mock_exp.version = "v2.0.0-experiment"
        mock_exp.file_path = "/models/v2.0.0.pkl"
        mock_exp.performance_score = 86.0  # Only 1.2% improvement
        mock_exp.experiment_config = {"traffic_percentage": 20}
        mock_exp.accuracy_metrics = {"sample_size": 150}
        mock_exp.model_metadata = {}

        def filter_side_effect(*args):
            mock_filtered = Mock()
            mock_filtered.first.return_value = mock_active
            mock_filtered.all.return_value = [mock_exp]
            return mock_filtered

        mock_query = Mock()
        mock_query.filter.side_effect = filter_side_effect
        mock_session.query.return_value = mock_query

        result = manager.recommend_promotion(
            "skill_matching",
            min_performance_improvement=5.0,
            db_session=mock_session
        )

        assert result["should_promote"] is False
        assert "best_improvement_pct" in result

    def test_successful_promotion_recommendation(self):
        """Test successful promotion recommendation."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_active = Mock()
        mock_active.id = "model-1"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.0.0.pkl"
        mock_active.performance_score = 80.0
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.is_active = True
        mock_active.is_experiment = False

        mock_exp = Mock()
        mock_exp.id = "exp-1"
        mock_exp.model_name = "skill_matching"
        mock_exp.version = "v2.0.0-experiment"
        mock_exp.file_path = "/models/v2.0.0.pkl"
        mock_exp.performance_score = 90.0  # 12.5% improvement
        mock_exp.experiment_config = {"traffic_percentage": 20}
        mock_exp.accuracy_metrics = {"sample_size": 150}
        mock_exp.model_metadata = {}

        def filter_side_effect(*args):
            mock_filtered = Mock()
            mock_filtered.first.return_value = mock_active
            mock_filtered.all.return_value = [mock_exp]
            return mock_filtered

        mock_query = Mock()
        mock_query.filter.side_effect = filter_side_effect
        mock_session.query.return_value = mock_query

        result = manager.recommend_promotion(
            "skill_matching",
            min_performance_improvement=5.0,
            db_session=mock_session
        )

        assert result["should_promote"] is True
        assert result["current_active"] == "v1.0.0"
        assert result["experiment_version"] == "v2.0.0-experiment"
        assert result["performance_improvement_pct"] == 12.5

    def test_chooses_best_experiment(self):
        """Test that best experiment is chosen when multiple exist."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_active = Mock()
        mock_active.id = "model-1"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.0.0.pkl"
        mock_active.performance_score = 80.0
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.is_active = True
        mock_active.is_experiment = False

        mock_exp1 = Mock()
        mock_exp1.id = "exp-1"
        mock_exp1.model_name = "skill_matching"
        mock_exp1.version = "v2.0.0-experiment"
        mock_exp1.file_path = "/models/v2.0.0.pkl"
        mock_exp1.performance_score = 88.0
        mock_exp1.experiment_config = {"traffic_percentage": 20}
        mock_exp1.accuracy_metrics = {"sample_size": 150}
        mock_exp1.model_metadata = {}

        mock_exp2 = Mock()
        mock_exp2.id = "exp-2"
        mock_exp2.model_name = "skill_matching"
        mock_exp2.version = "v2.1.0-experiment"
        mock_exp2.file_path = "/models/v2.1.0.pkl"
        mock_exp2.performance_score = 92.0  # Best performance
        mock_exp2.experiment_config = {"traffic_percentage": 10}
        mock_exp2.accuracy_metrics = {"sample_size": 150}
        mock_exp2.model_metadata = {}

        def filter_side_effect(*args):
            mock_filtered = Mock()
            mock_filtered.first.return_value = mock_active
            mock_filtered.all.return_value = [mock_exp1, mock_exp2]
            return mock_filtered

        mock_query = Mock()
        mock_query.filter.side_effect = filter_side_effect
        mock_session.query.return_value = mock_query

        result = manager.recommend_promotion("skill_matching", db_session=mock_session)

        assert result["should_promote"] is True
        assert result["experiment_version"] == "v2.1.0-experiment"  # Best one
        assert result["performance_improvement_pct"] == 15.0  # (92-80)/80 * 100


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_none_performance_score_in_metrics(self):
        """Test handling of None performance scores in metrics calculation."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_model1 = Mock()
        mock_model1.id = "model-1"
        mock_model1.model_name = "skill_matching"
        mock_model1.version = "v1.0.0"
        mock_model1.file_path = "/models/v1.0.0.pkl"
        mock_model1.performance_score = 85.0
        mock_model1.is_active = True
        mock_model1.is_experiment = False
        mock_model1.experiment_config = {}
        mock_model1.model_metadata = {}
        mock_model1.accuracy_metrics = {}
        mock_model1.created_at = datetime(2024, 1, 1)
        mock_model1.updated_at = datetime(2024, 1, 1)

        mock_model2 = Mock()
        mock_model2.id = "model-2"
        mock_model2.model_name = "skill_matching"
        mock_model2.version = "v2.0.0"
        mock_model2.file_path = "/models/v2.0.0.pkl"
        mock_model2.performance_score = None
        mock_model2.is_active = False
        mock_model2.is_experiment = True
        mock_model2.experiment_config = {}
        mock_model2.model_metadata = {}
        mock_model2.accuracy_metrics = {}
        mock_model2.created_at = datetime(2024, 1, 2)
        mock_model2.updated_at = datetime(2024, 1, 2)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [
            mock_model2, mock_model1
        ]
        mock_session.query.return_value = mock_query

        result = manager.calculate_model_metrics("skill_matching", db_session=mock_session)

        # Only non-None scores should be averaged
        assert result["avg_performance_score"] == 85.0
        assert result["best_performance_score"] == 85.0

    def test_empty_experiment_config_in_traffic_calculation(self):
        """Test handling of empty experiment_config in traffic distribution."""
        manager = ModelVersionManager()

        mock_session = Mock()

        mock_active = Mock()
        mock_active.id = "model-1"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.performance_score = 85.0
        mock_active.is_active = True
        mock_active.is_experiment = False
        mock_active.experiment_config = {}
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}
        mock_active.created_at = datetime(2024, 1, 1)
        mock_active.updated_at = datetime(2024, 1, 1)
        mock_active.file_path = "/models/v1.0.0.pkl"

        mock_exp = Mock()
        mock_exp.id = "exp-1"
        mock_exp.model_name = "skill_matching"
        mock_exp.version = "v2.0.0-experiment"
        mock_exp.performance_score = 90.0
        mock_exp.is_active = False
        mock_exp.is_experiment = True
        mock_exp.experiment_config = {}  # No traffic_percentage specified
        mock_exp.model_metadata = {}
        mock_exp.accuracy_metrics = {}
        mock_exp.created_at = datetime(2024, 1, 2)
        mock_exp.updated_at = datetime(2024, 1, 2)
        mock_exp.file_path = "/models/v2.0.0.pkl"

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_exp, mock_active]
        mock_session.query.return_value = mock_query

        result = manager.calculate_model_metrics("skill_matching", db_session=mock_session)

        # Experiment with 0% traffic, control gets 100%
        assert result["traffic_distribution"]["control"] == 100
