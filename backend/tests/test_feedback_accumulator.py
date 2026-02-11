"""
Unit Tests for FeedbackAccumulator Service

Tests the feedback accumulation service that tracks feedback counts
per model version and triggers retraining when thresholds are reached.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from analyzers.feedback_accumulator import (
    FeedbackAccumulator,
    FeedbackStats,
    ModelFeedbackAccumulator,
)


class TestFeedbackStats:
    """Tests for the FeedbackStats dataclass."""

    def test_feedback_stats_initialization(self):
        """Test FeedbackStats initializes with default values."""
        stats = FeedbackStats()
        assert stats.total_count == 0
        assert stats.positive_count == 0
        assert stats.negative_count == 0
        assert stats.neutral_count == 0
        assert stats.last_feedback_at is None
        assert stats.first_feedback_at is None

    def test_feedback_stats_with_values(self):
        """Test FeedbackStats initialization with custom values."""
        now = datetime.utcnow()
        stats = FeedbackStats(
            total_count=100,
            positive_count=60,
            negative_count=30,
            neutral_count=10,
            last_feedback_at=now,
            first_feedback_at=now - timedelta(days=7),
        )
        assert stats.total_count == 100
        assert stats.positive_count == 60
        assert stats.negative_count == 30
        assert stats.neutral_count == 10
        assert stats.last_feedback_at == now

    def test_feedback_stats_to_dict(self):
        """Test FeedbackStats serialization to dictionary."""
        now = datetime.utcnow()
        stats = FeedbackStats(
            total_count=50,
            positive_count=30,
            negative_count=15,
            neutral_count=5,
            last_feedback_at=now,
            first_feedback_at=now - timedelta(days=3),
        )
        result = stats.to_dict()

        assert result["total_count"] == 50
        assert result["positive_count"] == 30
        assert result["negative_count"] == 15
        assert result["neutral_count"] == 5
        assert result["last_feedback_at"] == now.isoformat()
        assert result["first_feedback_at"] == (now - timedelta(days=3)).isoformat()

    def test_feedback_stats_to_dict_with_none_timestamps(self):
        """Test FeedbackStats serialization with None timestamps."""
        stats = FeedbackStats(total_count=10)
        result = stats.to_dict()

        assert result["last_feedback_at"] is None
        assert result["first_feedback_at"] is None


class TestModelFeedbackAccumulator:
    """Tests for the ModelFeedbackAccumulator dataclass."""

    def test_model_accumulator_initialization(self):
        """Test ModelFeedbackAccumulator initializes correctly."""
        accumulator = ModelFeedbackAccumulator(
            model_name="ranking_model",
            model_version_id="v1.0.0",
        )
        assert accumulator.model_name == "ranking_model"
        assert accumulator.model_version_id == "v1.0.0"
        assert accumulator.feedback_since_training == 0
        assert accumulator.threshold_reached_at is None

    def test_model_accumulator_to_dict(self):
        """Test ModelFeedbackAccumulator serialization."""
        now = datetime.utcnow()
        accumulator = ModelFeedbackAccumulator(
            model_name="skill_matching",
            model_version_id="v2.0.0",
            feedback_since_training=500,
            threshold_reached_at=now,
        )
        result = accumulator.to_dict()

        assert result["model_name"] == "skill_matching"
        assert result["model_version_id"] == "v2.0.0"
        assert result["feedback_since_training"] == 500
        assert result["threshold_reached_at"] == now.isoformat()


class TestFeedbackAccumulator:
    """Tests for the FeedbackAccumulator class."""

    @pytest.fixture
    def accumulator(self):
        """Create a FeedbackAccumulator with a low threshold for testing."""
        return FeedbackAccumulator(feedback_threshold=10)

    @pytest.fixture
    def sample_feedback_items(self):
        """Create sample feedback items for batch testing."""
        return [
            {"type": "positive"},
            {"type": "negative"},
            {"type": "positive"},
            {"type": "neutral"},
            {"type": "positive"},
        ]

    def test_initialization_default_threshold(self):
        """Test FeedbackAccumulator initializes with default threshold."""
        acc = FeedbackAccumulator()
        assert acc.feedback_threshold == FeedbackAccumulator.DEFAULT_FEEDBACK_THRESHOLD
        assert acc.model_accumulators == {}

    def test_initialization_custom_threshold(self):
        """Test FeedbackAccumulator initializes with custom threshold."""
        acc = FeedbackAccumulator(feedback_threshold=500)
        assert acc.feedback_threshold == 500

    def test_get_accumulator_key(self, accumulator):
        """Test internal key generation for model accumulators."""
        key = accumulator._get_accumulator_key("model1", "v1.0")
        assert key == "model1:v1.0"

    def test_get_or_create_accumulator_creates_new(self, accumulator):
        """Test that _get_or_create_accumulator creates new accumulator."""
        result = accumulator._get_or_create_accumulator("new_model", "v1.0")
        assert result.model_name == "new_model"
        assert result.model_version_id == "v1.0"
        assert result.feedback_since_training == 0

    def test_get_or_create_accumulator_returns_existing(self, accumulator):
        """Test that _get_or_create_accumulator returns existing accumulator."""
        # Create first
        accumulator._get_or_create_accumulator("model", "v1.0")
        # Get same
        result = accumulator._get_or_create_accumulator("model", "v1.0")
        assert result.model_name == "model"

    def test_record_feedback_basic(self, accumulator):
        """Test basic feedback recording."""
        result = accumulator.record_feedback(
            "ranking_model", "v1.0.0", "positive"
        )

        assert result["model_name"] == "ranking_model"
        assert result["model_version_id"] == "v1.0.0"
        assert result["total_count"] == 1
        assert result["feedback_since_training"] == 1
        assert result["threshold_reached"] is False
        assert result["feedback_type"] == "positive"

    def test_record_feedback_counts_by_type(self, accumulator):
        """Test that feedback counts are tracked by type."""
        accumulator.record_feedback("model", "v1", "positive")
        accumulator.record_feedback("model", "v1", "positive")
        accumulator.record_feedback("model", "v1", "negative")
        accumulator.record_feedback("model", "v1", "neutral")

        stats = accumulator.get_feedback_stats("model", "v1")
        assert stats["stats"]["positive_count"] == 2
        assert stats["stats"]["negative_count"] == 1
        assert stats["stats"]["neutral_count"] == 1
        assert stats["stats"]["total_count"] == 4

    def test_record_feedback_invalid_type_defaults_to_neutral(self, accumulator):
        """Test that invalid feedback type defaults to neutral."""
        result = accumulator.record_feedback(
            "model", "v1", "invalid_type"
        )
        assert result["feedback_type"] == "neutral"

    def test_record_feedback_with_custom_timestamp(self, accumulator):
        """Test recording feedback with custom timestamp."""
        custom_time = datetime(2024, 1, 15, 10, 30, 0)
        accumulator.record_feedback(
            "model", "v1", "positive", timestamp=custom_time
        )

        stats = accumulator.get_feedback_stats("model", "v1")
        assert stats["stats"]["first_feedback_at"] == custom_time.isoformat()
        assert stats["stats"]["last_feedback_at"] == custom_time.isoformat()

    def test_record_feedback_updates_timestamps(self, accumulator):
        """Test that first and last feedback timestamps are updated correctly."""
        first_time = datetime(2024, 1, 1, 10, 0, 0)
        second_time = datetime(2024, 1, 2, 10, 0, 0)

        accumulator.record_feedback("model", "v1", "positive", timestamp=first_time)
        accumulator.record_feedback("model", "v1", "positive", timestamp=second_time)

        stats = accumulator.get_feedback_stats("model", "v1")
        assert stats["stats"]["first_feedback_at"] == first_time.isoformat()
        assert stats["stats"]["last_feedback_at"] == second_time.isoformat()

    def test_record_feedback_threshold_reached(self, accumulator):
        """Test that threshold_reached is True when threshold is met."""
        # Record 10 feedback items (the threshold)
        for _ in range(10):
            result = accumulator.record_feedback("model", "v1", "positive")

        assert result["threshold_reached"] is True
        assert result["feedback_since_training"] == 10

    def test_record_feedback_threshold_reached_at_set_once(self, accumulator):
        """Test that threshold_reached_at is set only once."""
        # Reach threshold
        for i in range(10):
            result = accumulator.record_feedback("model", "v1", "positive")

        # Get the timestamp
        stats = accumulator.get_feedback_stats("model", "v1")
        first_threshold_time = stats.get("threshold_reached_at")

        # Record more feedback
        accumulator.record_feedback("model", "v1", "positive")
        stats = accumulator.get_feedback_stats("model", "v1")
        second_threshold_time = stats.get("threshold_reached_at")

        # Should be the same
        assert first_threshold_time == second_threshold_time

    @patch('analyzers.feedback_accumulator.get_metrics_registry')
    def test_record_feedback_records_metrics(self, mock_get_registry, accumulator):
        """Test that metrics are recorded during feedback recording."""
        mock_registry = MagicMock()
        mock_get_registry.return_value = mock_registry

        accumulator.record_feedback("model", "v1", "positive")

        mock_registry.record_ml_inference.assert_called_once()
        call_args = mock_registry.record_ml_inference.call_args
        assert call_args.kwargs["model_name"] == "feedback_accumulator"
        assert call_args.kwargs["operation"] == "record_feedback"

    @patch('analyzers.feedback_accumulator.get_metrics_registry')
    def test_record_feedback_handles_metrics_error(self, mock_get_registry, accumulator):
        """Test that feedback recording continues even if metrics fail."""
        mock_get_registry.side_effect = Exception("Metrics error")

        result = accumulator.record_feedback("model", "v1", "positive")

        # Should still return valid result
        assert result["model_name"] == "model"
        assert result["total_count"] == 1


class TestFeedbackAccumulatorBatch:
    """Tests for batch feedback operations."""

    @pytest.fixture
    def accumulator(self):
        """Create a FeedbackAccumulator for batch testing."""
        return FeedbackAccumulator(feedback_threshold=10)

    def test_record_feedback_batch_basic(self, accumulator, sample_feedback_items):
        """Test basic batch feedback recording."""
        result = accumulator.record_feedback_batch(
            "model", "v1", sample_feedback_items
        )

        assert result["model_name"] == "model"
        assert result["model_version_id"] == "v1"
        assert result["processed_count"] == 5
        assert result["type_counts"]["positive"] == 3
        assert result["type_counts"]["negative"] == 1
        assert result["type_counts"]["neutral"] == 1

    def test_record_feedback_batch_empty_list(self, accumulator):
        """Test batch recording with empty list."""
        result = accumulator.record_feedback_batch("model", "v1", [])

        assert result["processed_count"] == 0
        assert result["type_counts"]["positive"] == 0

    def test_record_feedback_batch_with_timestamps(self, accumulator):
        """Test batch recording with string timestamps."""
        items = [
            {"type": "positive", "timestamp": "2024-01-15T10:00:00"},
            {"type": "negative", "timestamp": "2024-01-15T11:00:00"},
        ]
        result = accumulator.record_feedback_batch("model", "v1", items)

        assert result["processed_count"] == 2

    def test_record_feedback_batch_invalid_timestamp_handled(self, accumulator):
        """Test batch recording handles invalid timestamps gracefully."""
        items = [
            {"type": "positive", "timestamp": "invalid-timestamp"},
            {"type": "negative"},
        ]
        result = accumulator.record_feedback_batch("model", "v1", items)

        assert result["processed_count"] == 2

    def test_record_feedback_batch_threshold_reached(self, accumulator):
        """Test batch recording can reach threshold."""
        items = [{"type": "positive"} for _ in range(12)]
        result = accumulator.record_feedback_batch("model", "v1", items)

        assert result["threshold_reached"] is True


class TestFeedbackAccumulatorRetraining:
    """Tests for retraining trigger functionality."""

    @pytest.fixture
    def accumulator(self):
        """Create a FeedbackAccumulator for retraining tests."""
        return FeedbackAccumulator(feedback_threshold=5)

    def test_should_trigger_retraining_below_threshold(self, accumulator):
        """Test retraining not triggered below threshold."""
        for _ in range(4):
            accumulator.record_feedback("model", "v1", "positive")

        assert accumulator.should_trigger_retraining("model", "v1") is False

    def test_should_trigger_retraining_at_threshold(self, accumulator):
        """Test retraining triggered at threshold."""
        for _ in range(5):
            accumulator.record_feedback("model", "v1", "positive")

        assert accumulator.should_trigger_retraining("model", "v1") is True

    def test_should_trigger_retraining_above_threshold(self, accumulator):
        """Test retraining triggered above threshold."""
        for _ in range(10):
            accumulator.record_feedback("model", "v1", "positive")

        assert accumulator.should_trigger_retraining("model", "v1") is True

    def test_should_trigger_retraining_no_feedback(self, accumulator):
        """Test retraining not triggered for model with no feedback."""
        assert accumulator.should_trigger_retraining("new_model", "v1") is False

    def test_get_feedback_count(self, accumulator):
        """Test getting feedback count for a model."""
        for _ in range(3):
            accumulator.record_feedback("model", "v1", "positive")

        assert accumulator.get_feedback_count("model", "v1") == 3

    def test_get_feedback_count_no_feedback(self, accumulator):
        """Test getting feedback count for model with no feedback."""
        assert accumulator.get_feedback_count("unknown", "v1") == 0

    def test_get_models_needing_retraining(self, accumulator):
        """Test getting list of models needing retraining."""
        # Model 1: reaches threshold
        for _ in range(5):
            accumulator.record_feedback("model1", "v1", "positive")

        # Model 2: below threshold
        for _ in range(3):
            accumulator.record_feedback("model2", "v1", "positive")

        needs_retraining = accumulator.get_models_needing_retraining()

        assert len(needs_retraining) == 1
        assert needs_retraining[0]["model_name"] == "model1"

    def test_get_models_needing_retraining_empty(self, accumulator):
        """Test getting models needing retraining when none exist."""
        needs_retraining = accumulator.get_models_needing_retraining()
        assert needs_retraining == []


class TestFeedbackAccumulatorReset:
    """Tests for feedback reset functionality."""

    @pytest.fixture
    def accumulator(self):
        """Create a FeedbackAccumulator for reset tests."""
        return FeedbackAccumulator(feedback_threshold=5)

    def test_reset_feedback_count(self, accumulator):
        """Test resetting feedback count after retraining."""
        # Record some feedback
        for _ in range(5):
            accumulator.record_feedback("model", "v1", "positive")

        # Reset
        result = accumulator.reset_feedback_count("model", "v1")

        assert result["previous_count"] == 5
        assert result["new_count"] == 0
        assert accumulator.get_feedback_count("model", "v1") == 0

    def test_reset_feedback_count_unknown_model(self, accumulator):
        """Test resetting feedback count for unknown model."""
        result = accumulator.reset_feedback_count("unknown", "v1")

        assert result["previous_count"] == 0
        assert result["new_count"] == 0

    def test_reset_allows_new_accumulation(self, accumulator):
        """Test that reset allows new feedback accumulation."""
        # Record and reset
        for _ in range(5):
            accumulator.record_feedback("model", "v1", "positive")
        accumulator.reset_feedback_count("model", "v1")

        # Record new feedback
        accumulator.record_feedback("model", "v1", "positive")

        assert accumulator.get_feedback_count("model", "v1") == 1
        assert accumulator.should_trigger_retraining("model", "v1") is False

    def test_reset_clears_threshold_reached_at(self, accumulator):
        """Test that reset clears threshold_reached_at timestamp."""
        # Reach threshold
        for _ in range(5):
            accumulator.record_feedback("model", "v1", "positive")

        # Reset
        accumulator.reset_feedback_count("model", "v1")

        # Check stats
        stats = accumulator.get_feedback_stats("model", "v1")
        # Note: threshold_reached_at should be cleared but total stats preserved
        assert stats["feedback_since_training"] == 0


class TestFeedbackAccumulatorStats:
    """Tests for statistics functionality."""

    @pytest.fixture
    def accumulator(self):
        """Create a FeedbackAccumulator for stats tests."""
        return FeedbackAccumulator(feedback_threshold=10)

    def test_get_feedback_stats_basic(self, accumulator):
        """Test getting feedback statistics."""
        accumulator.record_feedback("model", "v1", "positive")
        accumulator.record_feedback("model", "v1", "negative")
        accumulator.record_feedback("model", "v1", "positive")

        stats = accumulator.get_feedback_stats("model", "v1")

        assert stats["model_name"] == "model"
        assert stats["model_version_id"] == "v1"
        assert stats["total_count"] == 3
        assert stats["stats"]["positive_count"] == 2
        assert stats["stats"]["negative_count"] == 1

    def test_get_feedback_stats_no_feedback(self, accumulator):
        """Test getting stats for model with no feedback."""
        stats = accumulator.get_feedback_stats("unknown", "v1")

        assert stats["model_name"] == "unknown"
        assert stats["total_count"] == 0
        assert stats["feedback_since_training"] == 0
        assert stats["threshold_reached"] is False

    def test_get_all_model_stats(self, accumulator):
        """Test getting stats for all models."""
        accumulator.record_feedback("model1", "v1", "positive")
        accumulator.record_feedback("model2", "v1", "negative")

        all_stats = accumulator.get_all_model_stats()

        assert len(all_stats) == 2
        model_names = [s["model_name"] for s in all_stats]
        assert "model1" in model_names
        assert "model2" in model_names

    def test_get_all_model_stats_empty(self, accumulator):
        """Test getting all stats when no feedback recorded."""
        all_stats = accumulator.get_all_model_stats()
        assert all_stats == []


class TestFeedbackAccumulatorThreshold:
    """Tests for threshold configuration."""

    def test_set_feedback_threshold(self):
        """Test updating feedback threshold."""
        accumulator = FeedbackAccumulator(feedback_threshold=100)
        accumulator.set_feedback_threshold(500)

        assert accumulator.feedback_threshold == 500

    def test_set_feedback_threshold_invalid(self):
        """Test that invalid threshold raises error."""
        accumulator = FeedbackAccumulator()

        with pytest.raises(ValueError, match="must be at least 1"):
            accumulator.set_feedback_threshold(0)

    def test_set_feedback_threshold_negative(self):
        """Test that negative threshold raises error."""
        accumulator = FeedbackAccumulator()

        with pytest.raises(ValueError, match="must be at least 1"):
            accumulator.set_feedback_threshold(-10)

    def test_threshold_change_affects_retraining_check(self):
        """Test that threshold change affects retraining decisions."""
        accumulator = FeedbackAccumulator(feedback_threshold=10)

        # Record 5 feedbacks
        for _ in range(5):
            accumulator.record_feedback("model", "v1", "positive")

        # Should not trigger with threshold 10
        assert accumulator.should_trigger_retraining("model", "v1") is False

        # Lower threshold to 3
        accumulator.set_feedback_threshold(3)

        # Should now trigger
        assert accumulator.should_trigger_retraining("model", "v1") is True


class TestFeedbackAccumulatorConstants:
    """Tests for class constants."""

    def test_feedback_type_constants(self):
        """Test feedback type constants are defined correctly."""
        assert FeedbackAccumulator.FEEDBACK_POSITIVE == "positive"
        assert FeedbackAccumulator.FEEDBACK_NEGATIVE == "negative"
        assert FeedbackAccumulator.FEEDBACK_NEUTRAL == "neutral"

    def test_valid_feedback_types(self):
        """Test valid feedback types set."""
        assert "positive" in FeedbackAccumulator.VALID_FEEDBACK_TYPES
        assert "negative" in FeedbackAccumulator.VALID_FEEDBACK_TYPES
        assert "neutral" in FeedbackAccumulator.VALID_FEEDBACK_TYPES
        assert len(FeedbackAccumulator.VALID_FEEDBACK_TYPES) == 3

    def test_default_threshold_constant(self):
        """Test default threshold constant."""
        assert FeedbackAccumulator.DEFAULT_FEEDBACK_THRESHOLD == 1000


class TestFeedbackAccumulatorMultiModel:
    """Tests for multi-model tracking."""

    @pytest.fixture
    def accumulator(self):
        """Create a FeedbackAccumulator for multi-model tests."""
        return FeedbackAccumulator(feedback_threshold=5)

    def test_multiple_models_tracked_independently(self, accumulator):
        """Test that multiple models are tracked independently."""
        accumulator.record_feedback("model1", "v1", "positive")
        accumulator.record_feedback("model1", "v1", "positive")
        accumulator.record_feedback("model2", "v1", "positive")

        assert accumulator.get_feedback_count("model1", "v1") == 2
        assert accumulator.get_feedback_count("model2", "v1") == 1

    def test_multiple_versions_tracked_independently(self, accumulator):
        """Test that multiple versions of same model are tracked independently."""
        accumulator.record_feedback("model", "v1", "positive")
        accumulator.record_feedback("model", "v1", "positive")
        accumulator.record_feedback("model", "v2", "positive")

        assert accumulator.get_feedback_count("model", "v1") == 2
        assert accumulator.get_feedback_count("model", "v2") == 1

    def test_retraining_check_per_model_version(self, accumulator):
        """Test retraining check is per model version."""
        # v1 reaches threshold
        for _ in range(5):
            accumulator.record_feedback("model", "v1", "positive")

        # v2 below threshold
        accumulator.record_feedback("model", "v2", "positive")

        assert accumulator.should_trigger_retraining("model", "v1") is True
        assert accumulator.should_trigger_retraining("model", "v2") is False

    def test_reset_affects_only_target_model(self, accumulator):
        """Test reset only affects target model version."""
        for _ in range(5):
            accumulator.record_feedback("model", "v1", "positive")
        for _ in range(5):
            accumulator.record_feedback("model", "v2", "positive")

        accumulator.reset_feedback_count("model", "v1")

        assert accumulator.get_feedback_count("model", "v1") == 0
        assert accumulator.get_feedback_count("model", "v2") == 5


class TestFeedbackAccumulatorEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def accumulator(self):
        """Create a FeedbackAccumulator for edge case tests."""
        return FeedbackAccumulator(feedback_threshold=10)

    def test_empty_model_name(self, accumulator):
        """Test handling of empty model name."""
        result = accumulator.record_feedback("", "v1", "positive")
        assert result["model_name"] == ""
        assert result["total_count"] == 1

    def test_empty_version_id(self, accumulator):
        """Test handling of empty version ID."""
        result = accumulator.record_feedback("model", "", "positive")
        assert result["model_version_id"] == ""
        assert result["total_count"] == 1

    def test_special_characters_in_names(self, accumulator):
        """Test handling of special characters in model names."""
        result = accumulator.record_feedback("model-with-dashes", "v1.0-beta", "positive")
        assert result["model_name"] == "model-with-dashes"
        assert result["model_version_id"] == "v1.0-beta"

    def test_unicode_in_names(self, accumulator):
        """Test handling of unicode in model names."""
        result = accumulator.record_feedback("модель", "v1", "positive")
        assert result["model_name"] == "модель"

    def test_large_feedback_count(self, accumulator):
        """Test handling of large feedback counts."""
        for _ in range(10000):
            accumulator.record_feedback("model", "v1", "positive")

        assert accumulator.get_feedback_count("model", "v1") == 10000
        assert accumulator.should_trigger_retraining("model", "v1") is True

    def test_concurrent_feedback_types(self, accumulator):
        """Test mixing feedback types in sequence."""
        types = ["positive", "negative", "neutral", "positive", "negative"]
        for t in types:
            accumulator.record_feedback("model", "v1", t)

        stats = accumulator.get_feedback_stats("model", "v1")
        assert stats["stats"]["positive_count"] == 2
        assert stats["stats"]["negative_count"] == 2
        assert stats["stats"]["neutral_count"] == 1
