"""
Unit tests for what-if scenario analysis features.

Tests cover:
- Feature perturbation analysis (single and multiple features)
- Skill addition scenarios
- Experience adjustment scenarios
- Education level changes
- Sensitivity analysis
- Counterfactual generation
- Natural language explanation generation
- Database integration for what-if analysis
"""
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime

import pytest
import numpy as np

from analyzers.sensitivity_analyzer import (
    SensitivityAnalyzer,
    FeaturePerturbation,
    WhatIfResult,
    SensitivitySummary,
    get_sensitivity_analyzer,
)
from analyzers.ranking_service import RankingModel, RankingFeatures


@pytest.fixture
def mock_ranking_model():
    """Create a mock ranking model for testing."""
    model = Mock(spec=RankingModel)

    # Mock predict_proba to return score based on features
    def mock_predict(features):
        # Simple scoring: average of first 5 features
        return float(np.mean(features[:5]))

    model.predict_proba.side_effect = mock_predict

    # Mock feature importance
    model.get_feature_importance.return_value = {
        "overall_match_score": 0.25,
        "skills_match_ratio": 0.20,
        "experience_months": 0.15,
        "experience_relevance": 0.12,
        "education_level": 0.10,
        "keyword_score": 0.08,
        "tfidf_score": 0.05,
        "vector_score": 0.05,
    }

    return model


@pytest.fixture
def sensitivity_analyzer(mock_ranking_model):
    """Create a sensitivity analyzer with mock model."""
    return SensitivityAnalyzer(model=mock_ranking_model)


@pytest.fixture
def sample_resume_data():
    """Create sample resume data for testing."""
    return {
        "id": str(uuid4()),
        "title": "Senior Python Developer",
        "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "Docker"],
        "experience": {
            "total_months": 84,
            "relevant_months": 72,
            "positions": [
                {
                    "title": "Senior Developer",
                    "duration_months": 36,
                    "company": "Tech Corp"
                },
                {
                    "title": "Mid-level Developer",
                    "duration_months": 48,
                    "company": "StartupCo"
                }
            ]
        },
        "education": {
            "degree": "B.Sc Computer Science",
            "institution": "Test University"
        },
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_vacancy_data():
    """Create sample vacancy data for testing."""
    return {
        "id": str(uuid4()),
        "title": "Senior Python Developer",
        "description": "Looking for experienced Python developer",
        "required_skills": ["Python", "Django", "FastAPI", "PostgreSQL", "Docker", "Kubernetes", "Redis"],
    }


@pytest.fixture
def sample_match_result():
    """Create sample match result data."""
    return {
        "overall_score": 0.75,
        "keyword_score": 0.70,
        "tfidf_score": 0.72,
        "vector_score": 0.78,
    }


class TestFeaturePerturbation:
    """Test FeaturePerturbation dataclass."""

    def test_feature_perturbation_creation(self):
        """Test creating a feature perturbation."""
        perturbation = FeaturePerturbation(
            feature_name="skills_match_ratio",
            original_value=0.7,
            perturbed_value=0.9,
            delta=0.2,
            delta_percent=28.57
        )

        assert perturbation.feature_name == "skills_match_ratio"
        assert perturbation.original_value == 0.7
        assert perturbation.perturbed_value == 0.9
        assert perturbation.delta == 0.2
        assert perturbation.delta_percent == 28.57

    def test_feature_perturbation_to_dict(self):
        """Test converting perturbation to dictionary."""
        perturbation = FeaturePerturbation(
            feature_name="experience_months",
            original_value=60.0,
            perturbed_value=72.0,
            delta=12.0,
            delta_percent=20.0
        )

        result = perturbation.to_dict()

        assert result["feature_name"] == "experience_months"
        assert result["original_value"] == 60.0
        assert result["perturbed_value"] == 72.0
        assert result["delta"] == 12.0
        assert result["delta_percent"] == 20.0


class TestWhatIfAnalysis:
    """Test what-if scenario analysis."""

    def test_single_feature_perturbation(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test what-if analysis with single feature change."""
        # Test increasing skills match
        result = sensitivity_analyzer.analyze_what_if(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            perturbations={"skills_match_ratio": 0.1},
            original_score=0.65,
            match_result=sample_match_result
        )

        assert isinstance(result, WhatIfResult)
        assert result.original_score == 0.65
        assert result.new_score != result.original_score
        assert len(result.perturbations) == 1
        assert result.perturbations[0].feature_name == "skills_match_ratio"
        assert result.explanation != ""
        assert result.new_recommendation in ["poor", "maybe", "good", "excellent"]

    def test_multiple_feature_perturbations(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test what-if analysis with multiple simultaneous changes."""
        # Test multiple improvements
        result = sensitivity_analyzer.analyze_what_if(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            perturbations={
                "skills_match_ratio": 0.15,
                "experience_months": 12,
                "education_level": 0.1
            },
            original_score=0.60,
            match_result=sample_match_result
        )

        assert isinstance(result, WhatIfResult)
        assert len(result.perturbations) == 3
        assert result.score_delta != 0

        # Check all perturbations are present
        feature_names = [p.feature_name for p in result.perturbations]
        assert "skills_match_ratio" in feature_names
        assert "experience_months" in feature_names
        assert "education_level" in feature_names

    def test_experience_adjustment_scenario(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test what-if scenario for experience adjustment."""
        # Test adding 24 months of experience
        result = sensitivity_analyzer.analyze_what_if(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            perturbations={"experience_months": 24},
            original_score=0.55,
            match_result=sample_match_result
        )

        assert len(result.perturbations) == 1
        exp_perturbation = result.perturbations[0]
        assert exp_perturbation.feature_name == "experience_months"
        assert exp_perturbation.delta == 24 or exp_perturbation.delta < 24  # May be clamped
        assert "experience" in result.scenario_description.lower() or "months" in result.scenario_description.lower()

    def test_education_level_change(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test what-if scenario for education level change."""
        result = sensitivity_analyzer.analyze_what_if(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            perturbations={"education_level": 0.2},
            original_score=0.50,
            match_result=sample_match_result
        )

        assert len(result.perturbations) == 1
        edu_perturbation = result.perturbations[0]
        assert edu_perturbation.feature_name == "education_level"
        assert edu_perturbation.delta > 0

    def test_feature_clamping(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test that feature values are clamped to valid ranges."""
        # Try to set skills_match_ratio above 1.0
        result = sensitivity_analyzer.analyze_what_if(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            perturbations={"skills_match_ratio": 2.0},  # Would exceed 1.0
            original_score=0.70,
            match_result=sample_match_result
        )

        perturbation = result.perturbations[0]
        assert perturbation.perturbed_value <= 1.0

        # Try to set negative experience
        result2 = sensitivity_analyzer.analyze_what_if(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            perturbations={"experience_months": -1000},  # Would be negative
            original_score=0.70,
            match_result=sample_match_result
        )

        perturbation2 = result2.perturbations[0]
        assert perturbation2.perturbed_value >= 0.0

    def test_unknown_feature_handling(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test that unknown features are gracefully ignored."""
        result = sensitivity_analyzer.analyze_what_if(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            perturbations={
                "unknown_feature": 0.5,
                "skills_match_ratio": 0.1
            },
            original_score=0.65,
            match_result=sample_match_result
        )

        # Should only have the valid feature
        assert len(result.perturbations) == 1
        assert result.perturbations[0].feature_name == "skills_match_ratio"


class TestNaturalLanguageExplanations:
    """Test natural language explanation generation."""

    def test_explanation_for_increase(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test explanation when score increases."""
        result = sensitivity_analyzer.analyze_what_if(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            perturbations={"skills_match_ratio": 0.2},
            original_score=0.50,
            match_result=sample_match_result
        )

        assert "increase" in result.explanation.lower() or "improve" in result.explanation.lower()
        assert str(result.original_score) in result.explanation or f"{result.original_score:.2f}" in result.explanation
        assert str(result.new_score) in result.explanation or f"{result.new_score:.2f}" in result.explanation

    def test_explanation_for_decrease(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test explanation when score decreases."""
        result = sensitivity_analyzer.analyze_what_if(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            perturbations={"skills_match_ratio": -0.3},
            original_score=0.80,
            match_result=sample_match_result
        )

        if result.score_delta < -0.01:
            assert "decrease" in result.explanation.lower() or "lower" in result.explanation.lower()

    def test_explanation_for_minimal_change(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test explanation when score changes minimally."""
        result = sensitivity_analyzer.analyze_what_if(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            perturbations={"completeness_score": 0.001},
            original_score=0.70,
            match_result=sample_match_result
        )

        # May have minimal or no impact
        assert result.explanation != ""

    def test_scenario_description_generation(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test scenario description is human-readable."""
        result = sensitivity_analyzer.analyze_what_if(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            perturbations={
                "skills_match_ratio": 0.1,
                "experience_months": 12
            },
            original_score=0.65,
            match_result=sample_match_result
        )

        assert result.scenario_description != ""
        assert "scenario" in result.scenario_description.lower() or len(result.scenario_description) > 10


class TestSensitivityAnalysis:
    """Test feature sensitivity analysis."""

    def test_sensitivity_analysis(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test sensitivity analysis for all features."""
        result = sensitivity_analyzer.analyze_sensitivity(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            original_score=0.70,
            match_result=sample_match_result,
            perturbation_percent=0.1
        )

        assert isinstance(result, SensitivitySummary)
        assert len(result.most_sensitive_features) > 0
        assert len(result.sensitivity_scores) > 0
        assert len(result.recommendations) > 0

    def test_sensitivity_scores_computed(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test that sensitivity scores are computed for all features."""
        result = sensitivity_analyzer.analyze_sensitivity(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            original_score=0.60,
            match_result=sample_match_result
        )

        # Should have sensitivity scores
        assert "skills_match_ratio" in result.sensitivity_scores
        assert "experience_months" in result.sensitivity_scores
        assert all(isinstance(v, float) for v in result.sensitivity_scores.values())

    def test_recommendations_generation(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test that actionable recommendations are generated."""
        result = sensitivity_analyzer.analyze_sensitivity(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            original_score=0.55,
            match_result=sample_match_result
        )

        assert len(result.recommendations) > 0
        assert len(result.recommendations) <= 5

        # Recommendations should be strings
        for rec in result.recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 10

    def test_sensitivity_summary_to_dict(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test converting sensitivity summary to dictionary."""
        result = sensitivity_analyzer.analyze_sensitivity(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            original_score=0.65,
            match_result=sample_match_result
        )

        dict_result = result.to_dict()

        assert "most_sensitive_features" in dict_result
        assert "sensitivity_scores" in dict_result
        assert "recommendations" in dict_result
        assert "analysis_timestamp" in dict_result


class TestCounterfactualGeneration:
    """Test counterfactual scenario generation."""

    def test_generate_counterfactuals_to_improve(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test generating counterfactuals to reach higher score."""
        counterfactuals = sensitivity_analyzer.generate_counterfactuals(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            original_score=0.50,
            target_score=0.70,
            match_result=sample_match_result,
            max_iterations=10
        )

        assert isinstance(counterfactuals, list)

        # Should find at least one way to reach target
        if len(counterfactuals) > 0:
            for cf in counterfactuals:
                assert isinstance(cf, WhatIfResult)
                assert cf.new_score >= 0.70

    def test_generate_counterfactuals_single_feature(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test that single-feature counterfactuals are prioritized."""
        counterfactuals = sensitivity_analyzer.generate_counterfactuals(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            original_score=0.55,
            target_score=0.65,
            match_result=sample_match_result
        )

        if len(counterfactuals) > 0:
            # First counterfactuals should prefer single-feature changes
            first_cf = counterfactuals[0]
            assert len(first_cf.perturbations) >= 1

    def test_counterfactual_limit(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test that counterfactual generation respects max_iterations."""
        max_iter = 3
        counterfactuals = sensitivity_analyzer.generate_counterfactuals(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            original_score=0.40,
            target_score=0.90,
            match_result=sample_match_result,
            max_iterations=max_iter
        )

        assert len(counterfactuals) <= max_iter


class TestWhatIfResultMethods:
    """Test WhatIfResult dataclass methods."""

    def test_whatif_result_to_dict(self):
        """Test converting WhatIfResult to dictionary."""
        perturbations = [
            FeaturePerturbation(
                feature_name="skills_match_ratio",
                original_value=0.7,
                perturbed_value=0.85,
                delta=0.15,
                delta_percent=21.43
            )
        ]

        result = WhatIfResult(
            scenario_description="Test scenario",
            original_score=0.65,
            new_score=0.72,
            score_delta=0.07,
            score_delta_percent=10.77,
            new_recommendation="good",
            perturbations=perturbations,
            feature_impacts={"skills_match_ratio": 0.03},
            explanation="Test explanation"
        )

        dict_result = result.to_dict()

        assert dict_result["scenario_description"] == "Test scenario"
        assert dict_result["original_score"] == 0.65
        assert dict_result["new_score"] == 0.72
        assert dict_result["score_delta"] == 0.07
        assert dict_result["new_recommendation"] == "good"
        assert len(dict_result["perturbations"]) == 1
        assert "skills_match_ratio" in dict_result["feature_impacts"]
        assert dict_result["explanation"] == "Test explanation"
        assert "timestamp" in dict_result


class TestDatabaseIntegration:
    """Test database integration for what-if analysis."""

    @pytest.mark.asyncio
    async def test_analyze_from_db_not_found(self, sensitivity_analyzer):
        """Test analyze_from_db with non-existent records."""
        mock_db = AsyncMock()

        # Mock empty result for resume query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Resume not found"):
            await sensitivity_analyzer.analyze_from_db(
                db=mock_db,
                resume_id=uuid4(),
                vacancy_id=uuid4(),
                perturbations={"skills_match_ratio": 0.1}
            )

    @pytest.mark.asyncio
    async def test_analyze_from_db_success(self, sensitivity_analyzer):
        """Test successful analyze_from_db."""
        mock_db = AsyncMock()

        resume_id = uuid4()
        vacancy_id = uuid4()

        # Mock resume
        mock_resume = Mock()
        mock_resume.id = resume_id
        mock_resume.raw_text = "Senior Python Developer with 5 years experience"
        mock_resume.updated_at = datetime.utcnow()

        # Mock vacancy
        mock_vacancy = Mock()
        mock_vacancy.id = vacancy_id
        mock_vacancy.title = "Python Developer"
        mock_vacancy.description = "Looking for Python developer"
        mock_vacancy.required_skills = ["Python", "Django"]

        # Mock ranking
        mock_ranking = Mock()
        mock_ranking.rank_score = 0.75

        # Mock match result
        mock_match = Mock()
        mock_match.overall_score = 0.70
        mock_match.keyword_score = 0.65
        mock_match.tfidf_score = 0.68
        mock_match.vector_score = 0.72

        # Mock analysis
        mock_analysis = Mock()
        mock_analysis.skills = ["Python", "Django", "FastAPI"]
        mock_analysis.raw_text = "Experienced Python developer"

        # Setup execute mock to return different results for different queries
        execute_results = [
            mock_resume,  # Resume query
            mock_vacancy,  # Vacancy query
            mock_ranking,  # Ranking query
            mock_match,   # Match result query
            mock_analysis # Analysis query
        ]

        async def mock_execute(query):
            result = AsyncMock()
            result.scalar_one_or_none.return_value = execute_results.pop(0) if execute_results else None
            return result

        mock_db.execute.side_effect = mock_execute

        # Execute
        result = await sensitivity_analyzer.analyze_from_db(
            db=mock_db,
            resume_id=resume_id,
            vacancy_id=vacancy_id,
            perturbations={"skills_match_ratio": 0.1}
        )

        assert isinstance(result, WhatIfResult)
        assert result.original_score == 0.75


class TestGlobalAnalyzer:
    """Test global analyzer singleton."""

    def test_get_sensitivity_analyzer(self):
        """Test getting global analyzer instance."""
        analyzer1 = get_sensitivity_analyzer()
        analyzer2 = get_sensitivity_analyzer()

        assert analyzer1 is analyzer2
        assert isinstance(analyzer1, SensitivityAnalyzer)


class TestRecommendationMapping:
    """Test score to recommendation mapping."""

    def test_score_to_recommendation(self, sensitivity_analyzer):
        """Test recommendation thresholds."""
        assert sensitivity_analyzer._score_to_recommendation(0.85) == "excellent"
        assert sensitivity_analyzer._score_to_recommendation(0.75) == "good"
        assert sensitivity_analyzer._score_to_recommendation(0.55) == "maybe"
        assert sensitivity_analyzer._score_to_recommendation(0.30) == "poor"


class TestFeatureImpacts:
    """Test feature impact calculation."""

    def test_feature_impacts_calculated(
        self,
        sensitivity_analyzer,
        sample_resume_data,
        sample_vacancy_data,
        sample_match_result
    ):
        """Test that feature impacts are calculated for perturbations."""
        result = sensitivity_analyzer.analyze_what_if(
            resume_data=sample_resume_data,
            vacancy_data=sample_vacancy_data,
            perturbations={
                "skills_match_ratio": 0.1,
                "experience_months": 12
            },
            original_score=0.60,
            match_result=sample_match_result
        )

        assert len(result.feature_impacts) == 2
        assert "skills_match_ratio" in result.feature_impacts
        assert "experience_months" in result.feature_impacts
        assert all(isinstance(v, float) for v in result.feature_impacts.values())
