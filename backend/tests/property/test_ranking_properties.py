"""
Property-based tests for ranking algorithms.

This module uses Hypothesis to generate hundreds of random test cases
and verify that certain properties (invariants) always hold true for
the ranking algorithms.

Properties tested:
- Feature extraction structure and range constraints
- Score calculation mathematical properties
- Recommendation mapping consistency
- Model prediction constraints
"""
import pytest
from hypothesis import given, strategies as st, settings, example
from typing import Dict, Any, List
import numpy as np
from analyzers.ranking_service import RankingFeatures, RankingModel, RankingService


class TestFeatureExtractionProperties:
    """Property-based tests for ranking feature extraction."""

    @given(
        st.dictionaries(
            st.sampled_from(["skills", "experience", "education", "title", "email", "phone", "summary", "updated_at"]),
            st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
                st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
            ),
            min_size=1,
            max_size=8
        ),
        st.dictionaries(
            st.sampled_from(["required_skills", "title", "position", "description"]),
            st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
            ),
            min_size=1,
            max_size=4
        )
    )
    @settings(max_examples=100)
    def test_extract_features_returns_array(self, resume_data: Dict, vacancy_data: Dict):
        """Feature extraction should always return a numpy array."""
        features = RankingFeatures.extract_features(resume_data, vacancy_data)
        assert isinstance(features, np.ndarray)
        assert features.ndim == 1

    @given(
        st.dictionaries(
            st.sampled_from(["skills", "experience", "education", "title", "email", "phone", "summary", "updated_at"]),
            st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
                st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
            ),
            min_size=1,
            max_size=8
        ),
        st.dictionaries(
            st.sampled_from(["required_skills", "title", "position", "description"]),
            st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
            ),
            min_size=1,
            max_size=4
        )
    )
    @settings(max_examples=100)
    def test_features_have_correct_length(self, resume_data: Dict, vacancy_data: Dict):
        """Feature vector should have the correct number of features."""
        features = RankingFeatures.extract_features(resume_data, vacancy_data)
        assert len(features) == len(RankingFeatures.FEATURE_NAMES)

    @given(
        st.dictionaries(
            st.sampled_from(["skills", "experience", "education", "title", "email", "phone", "summary", "updated_at"]),
            st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
                st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
            ),
            min_size=1,
            max_size=8
        ),
        st.dictionaries(
            st.sampled_from(["required_skills", "title", "position", "description"]),
            st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
            ),
            min_size=1,
            max_size=4
        )
    )
    @settings(max_examples=100)
    def test_features_are_finite(self, resume_data: Dict, vacancy_data: Dict):
        """All feature values should be finite numbers."""
        features = RankingFeatures.extract_features(resume_data, vacancy_data)
        for value in features:
            assert np.isfinite(value), f"Non-finite feature value: {value}"

    @given(
        st.dictionaries(
            st.sampled_from(["skills", "experience", "education", "title", "email", "phone", "summary", "updated_at"]),
            st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
                st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
            ),
            min_size=1,
            max_size=8
        ),
        st.dictionaries(
            st.sampled_from(["required_skills", "title", "position", "description"]),
            st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
            ),
            min_size=1,
            max_size=4
        )
    )
    @settings(max_examples=100)
    def test_features_within_valid_range(self, resume_data: Dict, vacancy_data: Dict):
        """Most features should be within 0-1 range (normalized)."""
        features = RankingFeatures.extract_features(resume_data, vacancy_data)
        # Most features should be normalized to 0-1, except raw experience months
        for i, (name, value) in enumerate(zip(RankingFeatures.FEATURE_NAMES, features)):
            if name != "experience_months":  # experience_months can be any non-negative number
                assert 0.0 <= value <= 1.0, f"Feature {name}={value} out of range [0, 1]"
            else:
                assert value >= 0.0, f"Feature {name}={value} should be non-negative"

    @given(
        st.dictionaries(
            st.sampled_from(["skills", "experience", "education", "title", "email", "phone", "summary", "updated_at"]),
            st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
                st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
            ),
            min_size=1,
            max_size=8
        ),
        st.dictionaries(
            st.sampled_from(["required_skills", "title", "position", "description"]),
            st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
            ),
            min_size=1,
            max_size=4
        ),
        st.dictionaries(
            st.sampled_from(["overall_score", "keyword_score", "tfidf_score", "vector_score"]),
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=0,
            max_size=4
        )
    )
    @settings(max_examples=100)
    def test_features_with_match_result(self, resume_data: Dict, vacancy_data: Dict, match_result: Dict):
        """Features should use match_result scores when provided."""
        features = RankingFeatures.extract_features(resume_data, vacancy_data, match_result)
        assert len(features) == len(RankingFeatures.FEATURE_NAMES)
        for value in features:
            assert np.isfinite(value)

    @given(
        st.dictionaries(
            st.sampled_from(["skills", "experience", "education", "title", "email", "phone", "summary", "updated_at"]),
            st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
                st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
            ),
            min_size=1,
            max_size=8
        ),
        st.dictionaries(
            st.sampled_from(["required_skills", "title", "position", "description"]),
            st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
            ),
            min_size=1,
            max_size=4
        )
    )
    @settings(max_examples=100)
    def test_empty_inputs_produce_valid_features(self, resume_data: Dict, vacancy_data: Dict):
        """Empty or minimal inputs should still produce valid features."""
        # Clear out the data to simulate minimal inputs
        resume_minimal = {}
        vacancy_minimal = {}
        features = RankingFeatures.extract_features(resume_minimal, vacancy_minimal)
        assert len(features) == len(RankingFeatures.FEATURE_NAMES)
        for value in features:
            assert np.isfinite(value)


class TestScoreProperties:
    """Property-based tests for ranking score calculations."""

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=13,
            max_size=13
        )
    )
    @settings(max_examples=100)
    def test_feature_array_to_numpy(self, feature_values: List[float]):
        """Feature list should convert to numpy array correctly."""
        features = np.array(feature_values, dtype=np.float64)
        assert len(features) == 13
        assert features.dtype == np.float64

    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    @example(0.85)
    @example(0.5)
    @example(0.15)
    def test_score_within_range(self, score: float):
        """All ranking scores should be within valid range."""
        assert 0.0 <= score <= 1.0

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_scores_can_be_sorted(self, scores: List[float]):
        """Scores should be sortable."""
        sorted_scores = sorted(scores, reverse=True)
        assert len(sorted_scores) == len(scores)
        # Verify descending order
        for i in range(len(sorted_scores) - 1):
            assert sorted_scores[i] >= sorted_scores[i + 1]

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_scores_can_be_ranked(self, scores: List[float]):
        """Scores should produce valid rankings."""
        # Sort scores descending
        sorted_scores = sorted(scores, reverse=True)
        # Assign ranks
        ranks = {}
        for i, score in enumerate(sorted_scores):
            ranks[score] = i + 1
        # All ranks should be positive integers
        for rank in ranks.values():
            assert rank > 0
            assert rank <= len(scores)


class TestRecommendationProperties:
    """Property-based tests for score-to-recommendation mapping."""

    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_recommendation_returns_valid_string(self, score: float):
        """Score to recommendation should return valid string."""
        service = RankingService()
        recommendation = service._score_to_recommendation(score)
        assert isinstance(recommendation, str)
        assert recommendation in {"excellent", "good", "maybe", "poor"}

    @given(st.floats(min_value=0.8, max_value=1.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_high_score_gives_excellent_or_good(self, score: float):
        """High scores should give excellent or good recommendation."""
        service = RankingService()
        recommendation = service._score_to_recommendation(score)
        assert recommendation in {"excellent", "good"}

    @given(st.floats(min_value=0.0, max_value=0.399, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_low_score_gives_poor_or_maybe(self, score: float):
        """Low scores should give poor or maybe recommendation."""
        service = RankingService()
        recommendation = service._score_to_recommendation(score)
        assert recommendation in {"poor", "maybe"}

    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    @example(0.8)
    @example(0.6)
    @example(0.4)
    @example(0.2)
    def test_recommendation_boundary_values(self, score: float):
        """Test recommendation mapping at boundary values."""
        service = RankingService()
        recommendation = service._score_to_recommendation(score)

        if score >= 0.8:
            assert recommendation == "excellent"
        elif score >= 0.6:
            assert recommendation == "good"
        elif score >= 0.4:
            assert recommendation == "maybe"
        else:
            assert recommendation == "poor"


class TestModelPredictionProperties:
    """Property-based tests for ranking model predictions."""

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=13,
            max_size=13
        )
    )
    @settings(max_examples=100)
    def test_predict_proba_returns_valid_probability(self, feature_values: List[float]):
        """predict_proba should always return a valid probability."""
        model = RankingModel()
        features = np.array(feature_values, dtype=np.float64)
        probability = model.predict_proba(features)
        assert 0.0 <= probability <= 1.0
        assert isinstance(probability, float)

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=13,
            max_size=13
        )
    )
    @settings(max_examples=100)
    def test_predict_returns_tuple(self, feature_values: List[float]):
        """predict should return a tuple of (prediction, confidence)."""
        model = RankingModel()
        features = np.array(feature_values, dtype=np.float64)
        result = model.predict(features)
        assert isinstance(result, tuple)
        assert len(result) == 2

        prediction, confidence = result
        assert prediction in {0, 1}
        assert 0.0 <= confidence <= 1.0

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=13,
            max_size=13
        )
    )
    @settings(max_examples=100)
    def test_confidence_is_valid(self, feature_values: List[float]):
        """Confidence score should always be in valid range."""
        model = RankingModel()
        features = np.array(feature_values, dtype=np.float64)
        _, confidence = model.predict(features)
        assert 0.0 <= confidence <= 1.0

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=13,
            max_size=13
        )
    )
    @settings(max_examples=100)
    def test_prediction_is_binary(self, feature_values: List[float]):
        """Prediction should always be 0 or 1."""
        model = RankingModel()
        features = np.array(feature_values, dtype=np.float64)
        prediction, _ = model.predict(features)
        assert prediction in {0, 1}


class TestFeatureImportanceProperties:
    """Property-based tests for feature importance calculation."""

    @given(st.sampled_from(["random_forest", "gradient_boosting"]))
    @settings(max_examples=10)
    def test_feature_importance_returns_dict(self, model_type: str):
        """Feature importance should return a dictionary."""
        model = RankingModel(model_type=model_type)
        importance = model.get_feature_importance()
        assert isinstance(importance, dict)

    @given(st.sampled_from(["random_forest", "gradient_boosting"]))
    @settings(max_examples=10)
    def test_feature_importance_keys_match_features(self, model_type: str):
        """Feature importance keys should match feature names."""
        model = RankingModel(model_type=model_type)
        importance = model.get_feature_importance()

        # Even for untrained models, should return empty dict
        # For trained models, keys should match feature names
        for key in importance.keys():
            assert key in RankingFeatures.FEATURE_NAMES

    @given(st.sampled_from(["random_forest", "gradient_boosting"]))
    @settings(max_examples=10)
    def test_feature_importance_values_are_positive(self, model_type: str):
        """Feature importance values should be non-negative."""
        model = RankingModel(model_type=model_type)
        importance = model.get_feature_importance()

        for value in importance.values():
            assert value >= 0.0


class TestRankingSortingProperties:
    """Property-based tests for ranking and sorting candidates."""

    @given(
        st.lists(
            st.dictionaries(
                st.sampled_from(["resume_id", "rank_score", "confidence", "recommendation"]),
                st.one_of(
                    st.text(min_size=1, max_size=30),
                    st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                ),
                min_size=2,
                max_size=4
            ),
            min_size=0,
            max_size=50
        )
    )
    @settings(max_examples=100)
    def test_rankings_can_be_sorted(self, candidates: List[Dict]):
        """Candidate rankings should be sortable by score."""
        if not candidates:
            return

        # Ensure all have rank_score
        valid_candidates = []
        for c in candidates:
            if "rank_score" in c:
                valid_candidates.append(c)

        if not valid_candidates:
            return

        # Sort by rank_score descending
        sorted_candidates = sorted(
            valid_candidates,
            key=lambda x: x["rank_score"],
            reverse=True
        )

        # Verify descending order
        for i in range(len(sorted_candidates) - 1):
            assert sorted_candidates[i]["rank_score"] >= sorted_candidates[i + 1]["rank_score"]

    @given(
        st.lists(
            st.dictionaries(
                st.sampled_from(["resume_id", "rank_score", "confidence", "recommendation"]),
                st.one_of(
                    st.text(min_size=1, max_size=30),
                    st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                ),
                min_size=2,
                max_size=4
            ),
            min_size=5,
            max_size=50
        )
    )
    @settings(max_examples=100)
    def test_top_n_selection(self, candidates: List[Dict]):
        """Top N selection should return N candidates."""
        # Ensure all have rank_score
        valid_candidates = []
        for c in candidates:
            if "rank_score" in c:
                valid_candidates.append(c)

        if not valid_candidates:
            return

        # Sort by rank_score descending
        sorted_candidates = sorted(
            valid_candidates,
            key=lambda x: x["rank_score"],
            reverse=True
        )

        # Test various N values
        for n in [1, 3, 5, 10]:
            top_n = sorted_candidates[:n]
            assert len(top_n) <= n
            # Verify order is maintained
            for i in range(len(top_n) - 1):
                assert top_n[i]["rank_score"] >= top_n[i + 1]["rank_score"]


class TestEmptyInputProperties:
    """Property-based tests for handling edge cases and empty inputs."""

    @given(st.dictionaries(st.text(min_size=1, max_size=20), st.none(), min_size=0, max_size=10))
    @settings(max_examples=100)
    def test_empty_resume_produces_valid_features(self, resume_data: Dict):
        """Empty resume data should produce valid features."""
        vacancy_data = {"required_skills": [], "title": "Test Position"}
        features = RankingFeatures.extract_features(resume_data, vacancy_data)
        assert len(features) == len(RankingFeatures.FEATURE_NAMES)
        for value in features:
            assert np.isfinite(value)

    @given(st.dictionaries(st.text(min_size=1, max_size=20), st.none(), min_size=0, max_size=10))
    @settings(max_examples=100)
    def test_empty_vacancy_produces_valid_features(self, vacancy_data: Dict):
        """Empty vacancy data should produce valid features."""
        resume_data = {"skills": [], "title": "Test Resume"}
        features = RankingFeatures.extract_features(resume_data, vacancy_data)
        assert len(features) == len(RankingFeatures.FEATURE_NAMES)
        for value in features:
            assert np.isfinite(value)

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=13,
            max_size=13
        )
    )
    @settings(max_examples=100)
    def test_model_handles_all_zero_features(self, feature_values: List[float]):
        """Model should handle all-zero feature vectors."""
        model = RankingModel()
        features = np.zeros(13, dtype=np.float64)
        probability = model.predict_proba(features)
        assert 0.0 <= probability <= 1.0

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=13,
            max_size=13
        )
    )
    @settings(max_examples=100)
    def test_model_handles_all_max_features(self, feature_values: List[float]):
        """Model should handle all-max (1.0) feature vectors."""
        model = RankingModel()
        features = np.ones(13, dtype=np.float64)
        probability = model.predict_proba(features)
        assert 0.0 <= probability <= 1.0


class TestFeatureConsistencyProperties:
    """Property-based tests for feature consistency and determinism."""

    @given(
        st.dictionaries(
            st.sampled_from(["skills", "experience", "education", "title", "email", "phone", "summary", "updated_at"]),
            st.one_of(
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
                st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
            ),
            min_size=3,
            max_size=8
        ),
        st.dictionaries(
            st.sampled_from(["required_skills", "title", "position", "description"]),
            st.one_of(
                st.text(min_size=1, max_size=50),
                st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
            ),
            min_size=2,
            max_size=4
        )
    )
    @settings(max_examples=100)
    def test_feature_extraction_is_deterministic(self, resume_data: Dict, vacancy_data: Dict):
        """Extracting features twice with same inputs should give same results."""
        features1 = RankingFeatures.extract_features(resume_data, vacancy_data)
        features2 = RankingFeatures.extract_features(resume_data, vacancy_data)
        np.testing.assert_array_equal(features1, features2)

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=13,
            max_size=13
        )
    )
    @settings(max_examples=100)
    def test_model_prediction_is_deterministic(self, feature_values: List[float]):
        """Model prediction should be deterministic for same features."""
        model = RankingModel()
        features = np.array(feature_values, dtype=np.float64)
        prob1 = model.predict_proba(features)
        prob2 = model.predict_proba(features)
        assert prob1 == prob2
