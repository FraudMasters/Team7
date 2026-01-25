"""
Tests for ML learning tasks and feedback aggregation.

Tests cover feedback aggregation, synonym generation,
model retraining, and Celery task execution.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from celery.exceptions import SoftTimeLimitExceeded

from tasks.learning_tasks import (
    aggregate_corrections,
    generate_synonym_candidates,
    aggregate_feedback_and_generate_synonyms,
    review_and_activate_synonyms,
    periodic_feedback_aggregation,
    retrain_skill_matching_model,
    MIN_CORRECTION_THRESHOLD,
    MIN_SYNONYM_CONFIDENCE,
)


class TestAggregateCorrections:
    """Tests for aggregate_corrections function."""

    def test_empty_feedback_list(self):
        """Test with empty feedback list."""
        result = aggregate_corrections([])

        assert result == {}

    def test_single_correction(self):
        """Test with single correction."""
        feedback = Mock()
        feedback.skill = "reactjs"
        feedback.actual_skill = "React"
        feedback.recruiter_correction = None
        feedback.feedback_source = "api"

        result = aggregate_corrections([feedback])

        assert "react" in result
        assert result["react"]["synonyms"] == ["reactjs"]
        assert result["react"]["correction_count"] == 1

    def test_multiple_corrections_same_skill(self):
        """Test multiple corrections for the same skill."""
        feedback_entries = [
            Mock(skill="reactjs", actual_skill="React", recruiter_correction=None, feedback_source="api"),
            Mock(skill="react.js", actual_skill="React", recruiter_correction=None, feedback_source="frontend"),
            Mock(skill="reactjs", actual_skill="React", recruiter_correction=None, feedback_source="api"),
        ]

        result = aggregate_corrections(feedback_entries)

        assert "react" in result
        # reactjs appears twice, react.js once
        assert "reactjs" in result["react"]["synonyms"]
        assert "react.js" in result["react"]["synonyms"]
        assert result["react"]["correction_count"] == 3
        assert len(result["react"]["sources"]) == 2

    def test_filters_by_minimum_threshold(self):
        """Test that corrections below threshold are filtered."""
        # Create 2 corrections for a skill (below MIN_CORRECTION_THRESHOLD of 3)
        feedback_entries = [
            Mock(skill="skill1", actual_skill="Skill1", recruiter_correction=None, feedback_source="api"),
            Mock(skill="skill2", actual_skill="Skill1", recruiter_correction=None, feedback_source="api"),
        ]

        result = aggregate_corrections(feedback_entries)

        # Should not be included due to low count
        assert "skill1" not in result

    def test_meets_minimum_threshold(self):
        """Test that corrections meeting threshold are included."""
        # Create 3 corrections for a skill (meets MIN_CORRECTION_THRESHOLD of 3)
        feedback_entries = [
            Mock(skill="synonym1", actual_skill="Skill1", recruiter_correction=None, feedback_source="api"),
            Mock(skill="synonym1", actual_skill="Skill1", recruiter_correction=None, feedback_source="api"),
            Mock(skill="synonym1", actual_skill="Skill1", recruiter_correction=None, feedback_source="api"),
        ]

        result = aggregate_corrections(feedback_entries)

        assert "skill1" in result
        assert result["skill1"]["synonyms"] == ["synonym1"]
        assert result["skill1"]["correction_count"] == 3

    def test_uses_recruiter_correction_fallback(self):
        """Test that recruiter_correction is used when actual_skill is None."""
        feedback = Mock()
        feedback.skill = "js"
        feedback.actual_skill = None
        feedback.recruiter_correction = "JavaScript"
        feedback.feedback_source = "api"

        result = aggregate_corrections([feedback])

        assert "javascript" in result
        assert result["javascript"]["synonyms"] == ["js"]

    def test_skips_none_values(self):
        """Test feedback with None values is skipped."""
        feedback = Mock()
        feedback.skill = None
        feedback.actual_skill = None
        feedback.recruiter_correction = None
        feedback.feedback_source = "api"

        result = aggregate_corrections([feedback])

        assert result == {}

    def test_skips_same_skill_no_correction(self):
        """Test that identical skills (no correction) are skipped."""
        feedback = Mock()
        feedback.skill = "react"
        feedback.actual_skill = "react"
        feedback.recruiter_correction = None
        feedback.feedback_source = "api"

        result = aggregate_corrections([feedback])

        assert result == {}

    def test_normalizes_case_and_whitespace(self):
        """Test skill name normalization."""
        feedback = Mock()
        feedback.skill = "  ReactJS  "
        feedback.actual_skill = " React "
        feedback.recruiter_correction = None
        feedback.feedback_source = "api"

        result = aggregate_corrections([feedback])

        assert "react" in result
        assert result["react"]["synonyms"] == ["reactjs"]

    def test_multiple_canonical_skills(self):
        """Test aggregating corrections for multiple different skills."""
        feedback_entries = [
            Mock(skill="reactjs", actual_skill="React", recruiter_correction=None, feedback_source="api"),
            Mock(skill="angularjs", actual_skill="Angular", recruiter_correction=None, feedback_source="frontend"),
        ]

        result = aggregate_corrections(feedback_entries)

        assert len(result) == 2
        assert "react" in result
        assert "angular" in result

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        # Create 6 corrections (confidence = 6 / (3*2) = 1.0)
        feedback_entries = [
            Mock(skill="syn", actual_skill="Skill", recruiter_correction=None, feedback_source="api")
            for _ in range(6)
        ]

        result = aggregate_corrections(feedback_entries)

        assert result["skill"]["confidence"] == 1.0

    def test_sources_tracking(self):
        """Test that feedback sources are tracked."""
        feedback_entries = [
            Mock(skill="syn1", actual_skill="Skill", recruiter_correction=None, feedback_source="api"),
            Mock(skill="syn2", actual_skill="Skill", recruiter_correction=None, feedback_source="frontend"),
            Mock(skill="syn1", actual_skill="Skill", recruiter_correction=None, feedback_source="api"),
        ]

        result = aggregate_corrections(feedback_entries)

        assert "api" in result["skill"]["sources"]
        assert "frontend" in result["skill"]["sources"]


class TestGenerateSynonymCandidates:
    """Tests for generate_synonym_candidates function."""

    def test_empty_corrections(self):
        """Test with empty corrections."""
        result = generate_synonym_candidates({})

        assert result == []

    def test_single_candidate(self):
        """Test generating single synonym candidate."""
        corrections = {
            "react": {
                "synonyms": ["reactjs", "react.js"],
                "correction_count": 10,
                "confidence": 0.92,
                "sources": ["api", "frontend"],
            }
        }

        result = generate_synonym_candidates(corrections)

        assert len(result) == 1
        assert result[0]["canonical_skill"] == "react"
        assert result[0]["custom_synonyms"] == ["reactjs", "react.js"]
        assert result[0]["confidence"] == 0.92
        assert result[0]["correction_count"] == 10
        assert result[0]["context"] is None

    def test_filters_low_confidence(self):
        """Test that low confidence candidates are filtered."""
        corrections = {
            "react": {
                "synonyms": ["reactjs"],
                "correction_count": 2,
                "confidence": 0.5,  # Below MIN_SYNONYM_CONFIDENCE
                "sources": ["api"],
            }
        }

        result = generate_synonym_candidates(corrections)

        assert len(result) == 0

    def test_includes_high_confidence(self):
        """Test that high confidence candidates are included."""
        corrections = {
            "react": {
                "synonyms": ["reactjs"],
                "correction_count": 10,
                "confidence": 0.95,  # Above MIN_SYNONYM_CONFIDENCE
                "sources": ["api"],
            }
        }

        result = generate_synonym_candidates(corrections)

        assert len(result) == 1
        assert result[0]["confidence"] == 0.95

    def test_includes_organization_id(self):
        """Test that organization_id is included when provided."""
        corrections = {
            "react": {
                "synonyms": ["reactjs"],
                "correction_count": 10,
                "confidence": 0.9,
                "sources": ["api"],
            }
        }

        result = generate_synonym_candidates(corrections, organization_id="org123")

        assert result[0]["organization_id"] == "org123"

    def test_no_organization_id(self):
        """Test candidate without organization_id."""
        corrections = {
            "react": {
                "synonyms": ["reactjs"],
                "correction_count": 10,
                "confidence": 0.9,
                "sources": ["api"],
            }
        }

        result = generate_synonym_candidates(corrections)

        assert "organization_id" not in result[0]

    def test_metadata_includes_sources(self):
        """Test that metadata includes sources."""
        corrections = {
            "react": {
                "synonyms": ["reactjs"],
                "correction_count": 10,
                "confidence": 0.9,
                "sources": ["api", "frontend"],
            }
        }

        result = generate_synonym_candidates(corrections)

        assert result[0]["metadata"]["sources"] == ["api", "frontend"]

    def test_metadata_includes_timestamp(self):
        """Test that metadata includes generation timestamp."""
        corrections = {
            "react": {
                "synonyms": ["reactjs"],
                "correction_count": 10,
                "confidence": 0.9,
                "sources": ["api"],
            }
        }

        result = generate_synonym_candidates(corrections)

        assert "generated_at" in result[0]["metadata"]
        assert "auto_generated" in result[0]["metadata"]
        assert result[0]["metadata"]["auto_generated"] is True

    def test_multiple_candidates(self):
        """Test generating multiple candidates."""
        corrections = {
            "react": {
                "synonyms": ["reactjs"],
                "correction_count": 10,
                "confidence": 0.9,
                "sources": ["api"],
            },
            "angular": {
                "synonyms": ["angularjs"],
                "correction_count": 8,
                "confidence": 0.85,
                "sources": ["frontend"],
            },
        }

        result = generate_synonym_candidates(corrections)

        assert len(result) == 2
        canonical_skills = [c["canonical_skill"] for c in result]
        assert "react" in canonical_skills
        assert "angular" in canonical_skills


class TestAggregateFeedbackAndGenerateSynonyms:
    """Tests for aggregate_feedback_and_generate_synonyms Celery task."""

    @patch("tasks.learning_tasks.aggregate_corrections")
    @patch("tasks.learning_tasks.generate_synonym_candidates")
    def test_successful_execution(self, mock_generate, mock_aggregate):
        """Test successful task execution."""
        # Setup mocks
        mock_aggregate.return_value = {
            "react": {
                "synonyms": ["reactjs"],
                "correction_count": 10,
                "confidence": 0.9,
                "sources": ["api"],
            }
        }
        mock_generate.return_value = [
            {
                "canonical_skill": "react",
                "custom_synonyms": ["reactjs"],
                "confidence": 0.9,
                "metadata": {},
            }
        ]

        task = Mock()
        task.request.id = "test-task-id"
        task.update_state = Mock()

        result = aggregate_feedback_and_generate_synonyms(
            task, organization_id="org123", days_back=30, mark_processed=False
        )

        assert result["status"] == "completed"
        assert result["total_feedback"] == 0
        assert result["corrections_found"] == 1
        assert result["candidates_generated"] == 1
        assert result["processed_count"] == 0
        assert "processing_time_ms" in result

    @patch("tasks.learning_tasks.aggregate_corrections")
    @patch("tasks.learning_tasks.generate_synonym_candidates")
    def test_with_mark_processed(self, mock_generate, mock_aggregate):
        """Test with mark_processed=True."""
        mock_aggregate.return_value = {}
        mock_generate.return_value = []

        task = Mock()
        task.request.id = "test-task-id"
        task.update_state = Mock()

        result = aggregate_feedback_and_generate_synonyms(
            task, mark_processed=True
        )

        # With empty feedback, processed_count should be 0
        assert result["processed_count"] == 0

    @patch("tasks.learning_tasks.aggregate_corrections")
    @patch("tasks.learning_tasks.generate_synonym_candidates")
    def test_task_progress_updates(self, mock_generate, mock_aggregate):
        """Test that task updates progress."""
        mock_aggregate.return_value = {}
        mock_generate.return_value = []

        task = Mock()
        task.request.id = "test-task-id"
        task.update_state = Mock()

        aggregate_feedback_and_generate_synonyms(task)

        # Should have called update_state multiple times
        assert task.update_state.call_count == 4

    def test_soft_time_limit_exceeded(self):
        """Test handling of SoftTimeLimitExceeded."""
        task = Mock()
        task.request.id = "test-task-id"

        with patch("tasks.learning_tasks.aggregate_corrections", side_effect=SoftTimeLimitExceeded()):
            result = aggregate_feedback_and_generate_synonyms(task)

        assert result["status"] == "failed"
        assert "exceeded maximum time limit" in result["error"]
        assert "processing_time_ms" in result

    @patch("tasks.learning_tasks.aggregate_corrections")
    def test_general_exception_handling(self, mock_aggregate):
        """Test handling of general exceptions."""
        task = Mock()
        task.request.id = "test-task-id"

        mock_aggregate.side_effect = Exception("Database error")

        result = aggregate_feedback_and_generate_synonyms(task)

        assert result["status"] == "failed"
        assert result["error"] == "Database error"
        assert "processing_time_ms" in result


class TestReviewAndActivateSynonyms:
    """Tests for review_and_activate_synonyms Celery task."""

    def test_successful_review(self):
        """Test successful synonym review."""
        task = Mock()
        task.request.id = "test-task-id"

        result = review_and_activate_synonyms(
            task, candidate_ids=["id1", "id2", "id3"], auto_activate_threshold=0.9
        )

        assert result["status"] == "completed"
        assert result["total_candidates"] == 3
        assert "processing_time_ms" in result

    def test_empty_candidate_list(self):
        """Test with empty candidate list."""
        task = Mock()
        task.request.id = "test-task-id"

        result = review_and_activate_synonyms(task, candidate_ids=[])

        assert result["status"] == "completed"
        assert result["total_candidates"] == 0

    def test_exception_handling(self):
        """Test exception handling in review task."""
        task = Mock()
        task.request.id = "test-task-id"

        with patch.object(review_and_activate_synonyms, "run", side_effect=Exception("Review error")):
            result = review_and_activate_synonyms(task, candidate_ids=["id1"])

        # The function should handle the exception
        assert "error" in result or result["status"] == "failed"


class TestPeriodicFeedbackAggregation:
    """Tests for periodic_feedback_aggregation Celery task."""

    @patch("tasks.learning_tasks.aggregate_feedback_and_generate_synonyms")
    def test_calls_aggregate_task(self, mock_aggregate):
        """Test that periodic task calls aggregate task."""
        mock_aggregate.return_value = {"status": "completed", "candidates_generated": 5}

        task = Mock()
        task.request.id = "test-task-id"

        result = periodic_feedback_aggregation(task)

        assert mock_aggregate.called
        assert result["status"] == "completed"
        assert result["candidates_generated"] == 5

    @patch("tasks.learning_tasks.aggregate_feedback_and_generate_synonyms")
    def test_default_parameters(self, mock_aggregate):
        """Test default parameters for periodic aggregation."""
        mock_aggregate.return_value = {"status": "completed"}

        task = Mock()
        task.request.id = "test-task-id"

        periodic_feedback_aggregation(task)

        # Should call with None organization_id and 7 days back
        mock_aggregate.assert_called_once_with(
            organization_id=None,
            days_back=7,
            mark_processed=True,
        )


class TestRetrainSkillMatchingModel:
    """Tests for retrain_skill_matching_model Celery task."""

    def test_successful_retraining(self):
        """Test successful model retraining."""
        task = Mock()
        task.request.id = "test-task-id"
        task.update_state = Mock()

        result = retrain_skill_matching_model(
            task,
            model_name="skill_matching",
            days_back=30,
            min_feedback_count=50,
            auto_activate=False,
        )

        assert result["status"] == "completed"
        assert result["is_active"] is False
        assert result["is_experiment"] is True
        assert "new_version" in result
        assert "performance_score" in result

    def test_insufficient_feedback(self):
        """Test with insufficient feedback count."""
        task = Mock()
        task.request.id = "test-task-id"
        task.update_state = Mock()

        result = retrain_skill_matching_model(
            task,
            min_feedback_count=100,  # High threshold
        )

        assert result["status"] == "skipped"
        assert "Insufficient feedback samples" in result["reason"]
        assert result["training_samples"] == 0

    def test_auto_activate_threshold(self):
        """Test auto-activation based on performance threshold."""
        task = Mock()
        task.request.id = "test-task-id"
        task.update_state = Mock()

        result = retrain_skill_matching_model(
            task,
            auto_activate=True,
            performance_threshold=0.5,  # Low threshold
        )

        # With placeholder performance (0.7+), should activate
        assert result["status"] == "completed"
        assert "improvement_over_baseline" in result

    def test_progress_updates(self):
        """Test that retraining task updates progress."""
        task = Mock()
        task.request.id = "test-task-id"
        task.update_state = Mock()

        retrain_skill_matching_model(task, min_feedback_count=0)

        # Should update progress for each step
        assert task.update_state.call_count == 6

    def test_soft_time_limit_exceeded(self):
        """Test handling of SoftTimeLimitExceeded."""
        task = Mock()
        task.request.id = "test-task-id"

        with patch("tasks.learning_tasks.aggregate_corrections", side_effect=SoftTimeLimitExceeded()):
            result = retrain_skill_matching_model(task)

        assert result["status"] == "failed"
        assert "exceeded maximum time limit" in result["error"]

    def test_general_exception_handling(self):
        """Test handling of general exceptions."""
        task = Mock()
        task.request.id = "test-task-id"

        with patch("tasks.learning_tasks.aggregate_corrections", side_effect=Exception("Training error")):
            result = retrain_skill_matching_model(task)

        assert result["status"] == "failed"
        assert result["error"] == "Training error"

    def test_custom_parameters(self):
        """Test with custom parameters."""
        task = Mock()
        task.request.id = "test-task-id"
        task.update_state = Mock()

        result = retrain_skill_matching_model(
            task,
            model_name="custom_model",
            days_back=60,
            min_feedback_count=100,
            auto_activate=True,
            performance_threshold=0.9,
        )

        assert result["status"] == "completed"


class TestLearningIntegration:
    """Tests for learning pipeline integration scenarios."""

    @patch("tasks.learning_tasks.generate_synonym_candidates")
    def test_full_pipeline_flow(self, mock_generate):
        """Test complete flow from feedback to candidates."""
        mock_generate.return_value = []

        feedback_entries = [
            Mock(skill="reactjs", actual_skill="React", recruiter_correction=None, feedback_source="api"),
            Mock(skill="reactjs", actual_skill="React", recruiter_correction=None, feedback_source="api"),
            Mock(skill="reactjs", actual_skill="React", recruiter_correction=None, feedback_source="api"),
        ]

        corrections = aggregate_corrections(feedback_entries)
        candidates = generate_synonym_candidates(corrections)

        assert "react" in corrections
        assert isinstance(candidates, list)

    def test_confidence_threshold_filtering(self):
        """Test that confidence thresholds properly filter candidates."""
        corrections = {
            "high_conf": {
                "synonyms": ["syn1"],
                "correction_count": 10,
                "confidence": 0.95,
                "sources": ["api"],
            },
            "low_conf": {
                "synonyms": ["syn2"],
                "correction_count": 2,
                "confidence": 0.5,
                "sources": ["api"],
            },
        }

        candidates = generate_synonym_candidates(corrections)

        # Only high confidence should pass
        assert len(candidates) == 1
        assert candidates[0]["canonical_skill"] == "high_conf"


class TestEdgeCases:
    """Tests for edge cases and error scenarios."""

    def test_none_skill_in_feedback(self):
        """Test feedback with None skill."""
        feedback = Mock()
        feedback.skill = None
        feedback.actual_skill = "React"
        feedback.recruiter_correction = None
        feedback.feedback_source = "api"

        result = aggregate_corrections([feedback])

        assert result == {}

    def test_empty_string_skill(self):
        """Test feedback with empty string skill."""
        feedback = Mock()
        feedback.skill = ""
        feedback.actual_skill = "React"
        feedback.recruiter_correction = None
        feedback.feedback_source = "api"

        result = aggregate_corrections([feedback])

        assert result == {}

    def test_unicode_skill_names(self):
        """Test handling of unicode characters in skill names."""
        feedback = Mock()
        feedback.skill = "中文技能"
        feedback.actual_skill = "Chinese Skill"
        feedback.recruiter_correction = None
        feedback.feedback_source = "api"

        result = aggregate_corrections([feedback])

        assert "chinese skill" in result

    def test_very_long_skill_names(self):
        """Test handling of very long skill names."""
        long_skill = "a" * 200
        feedback = Mock()
        feedback.skill = long_skill
        feedback.actual_skill = "Short"
        feedback.recruiter_correction = None
        feedback.feedback_source = "api"

        result = aggregate_corrections([feedback])

        assert "short" in result

    def test_special_characters_in_skills(self):
        """Test handling of special characters."""
        feedback = Mock()
        feedback.skill = "C++/C#"
        feedback.actual_skill = "C Languages"
        feedback.recruiter_correction = None
        feedback.feedback_source = "api"

        result = aggregate_corrections([feedback])

        assert "c languages" in result
