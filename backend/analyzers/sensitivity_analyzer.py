"""
Sensitivity Analyzer for What-If Analysis

This module provides what-if analysis capabilities for candidate rankings,
allowing recruiters to explore how hypothetical changes to candidate profiles
would affect their rankings.

Key features:
- Feature perturbation analysis (what if skill score was higher?)
- Scenario simulation (what if candidate had more leadership experience?)
- Ranking impact quantification
- Feature importance validation
- Counterfactual explanations

The module helps recruiters understand which factors most impact rankings
and provides insights into how candidates could improve their standings.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from numpy import typing as npt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CandidateRank, JobVacancy, MatchResult, Resume, ResumeAnalysis
from analyzers.ranking_service import RankingFeatures, RankingModel
from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)


@dataclass
class FeaturePerturbation:
    """
    A single feature perturbation for what-if analysis.

    Attributes:
        feature_name: Name of the feature to perturb
        original_value: Original feature value
        perturbed_value: New feature value after perturbation
        delta: Change amount (perturbed - original)
        delta_percent: Change as percentage of original
    """
    feature_name: str
    original_value: float
    perturbed_value: float
    delta: float
    delta_percent: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "feature_name": self.feature_name,
            "original_value": self.original_value,
            "perturbed_value": self.perturbed_value,
            "delta": self.delta,
            "delta_percent": self.delta_percent,
        }


@dataclass
class WhatIfResult:
    """
    Result of a what-if analysis scenario.

    Attributes:
        scenario_description: Human-readable description of the scenario
        original_score: Original ranking score
        new_score: New ranking score after perturbations
        score_delta: Change in score (new - original)
        score_delta_percent: Score change as percentage
        new_recommendation: New hiring recommendation
        perturbations: List of feature perturbations applied
        feature_impacts: Dictionary of feature -> score impact
        explanation: Natural language explanation of the result
        timestamp: When the analysis was performed
    """
    scenario_description: str
    original_score: float
    new_score: float
    score_delta: float
    score_delta_percent: float
    new_recommendation: str
    perturbations: List[FeaturePerturbation]
    feature_impacts: Dict[str, float]
    explanation: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "scenario_description": self.scenario_description,
            "original_score": self.original_score,
            "new_score": self.new_score,
            "score_delta": self.score_delta,
            "score_delta_percent": self.score_delta_percent,
            "new_recommendation": self.new_recommendation,
            "perturbations": [p.to_dict() for p in self.perturbations],
            "feature_impacts": self.feature_impacts,
            "explanation": self.explanation,
            "timestamp": self.timestamp,
        }


@dataclass
class SensitivitySummary:
    """
    Summary of feature sensitivity analysis.

    Attributes:
        most_sensitive_features: Features that most impact ranking
        sensitivity_scores: Dictionary of feature -> sensitivity score
        recommendations: Suggestions for ranking improvement
        analysis_timestamp: When analysis was performed
    """
    most_sensitive_features: List[Tuple[str, float]]
    sensitivity_scores: Dict[str, float]
    recommendations: List[str]
    analysis_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "most_sensitive_features": [
                {"feature": f, "sensitivity": s} for f, s in self.most_sensitive_features
            ],
            "sensitivity_scores": self.sensitivity_scores,
            "recommendations": self.recommendations,
            "analysis_timestamp": self.analysis_timestamp,
        }


class SensitivityAnalyzer:
    """
    Sensitivity analyzer for what-if analysis of candidate rankings.

    This analyzer helps recruiters understand how changes to candidate
    attributes would affect their ranking, providing insights into
    feature importance and ranking drivers.

    Example:
        >>> analyzer = SensitivityAnalyzer()
        >>> result = analyzer.analyze_what_if(
        ...     resume_data=resume_dict,
        ...     vacancy_data=vacancy_dict,
        ...     perturbations={"experience_months": 12},
        ...     original_score=0.65
        ... )
        >>> print(result.explanation)
        "Adding 12 months of experience would increase the ranking score
        from 0.65 to 0.72 (+10.8%), changing recommendation from 'maybe' to 'good'."
    """

    # Feature ranges for perturbation analysis
    FEATURE_RANGES = {
        "overall_match_score": (0.0, 1.0),
        "keyword_score": (0.0, 1.0),
        "tfidf_score": (0.0, 1.0),
        "vector_score": (0.0, 1.0),
        "skills_match_ratio": (0.0, 1.0),
        "experience_months": (0.0, 480.0),  # 0-40 years
        "experience_relevance": (0.0, 1.0),
        "education_level": (0.0, 1.0),
        "recent_experience": (0.0, 1.0),
        "skill_rarity_score": (0.0, 1.0),
        "title_similarity": (0.0, 1.0),
        "freshness_score": (0.0, 1.0),
        "completeness_score": (0.0, 1.0),
    }

    # Human-readable feature names
    FEATURE_LABELS = {
        "overall_match_score": "Overall Match Score",
        "keyword_score": "Keyword Score",
        "tfidf_score": "TF-IDF Score",
        "vector_score": "Vector Similarity Score",
        "skills_match_ratio": "Skills Match Ratio",
        "experience_months": "Experience (months)",
        "experience_relevance": "Experience Relevance",
        "education_level": "Education Level",
        "recent_experience": "Recent Experience",
        "skill_rarity_score": "Skill Rarity Score",
        "title_similarity": "Title Similarity",
        "freshness_score": "Freshness Score",
        "completeness_score": "Resume Completeness",
    }

    def __init__(self, model: Optional[RankingModel] = None):
        """
        Initialize the Sensitivity Analyzer.

        Args:
            model: Optional RankingModel for score prediction
        """
        self.model = model or RankingModel(model_type="random_forest")

    def _score_to_recommendation(self, score: float) -> str:
        """Convert numeric score to recommendation."""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "maybe"
        return "poor"

    def _create_scenario_description(
        self,
        perturbations: List[FeaturePerturbation],
    ) -> str:
        """Create human-readable scenario description."""
        if not perturbations:
            return "No changes applied (baseline scenario)"

        descriptions = []
        for p in perturbations:
            label = self.FEATURE_LABELS.get(p.feature_name, p.feature_name)

            if p.feature_name == "experience_months":
                if p.delta > 0:
                    descriptions.append(f"adding {int(p.delta)} months of experience")
                else:
                    descriptions.append(f"removing {int(abs(p.delta))} months of experience")
            elif p.delta_percent > 0:
                descriptions.append(f"increasing {label} by {p.delta_percent:.1f}%")
            else:
                descriptions.append(f"decreasing {label} by {abs(p.delta_percent):.1f}%")

        if len(descriptions) == 1:
            return f"Scenario: {descriptions[0]}"
        elif len(descriptions) == 2:
            return f"Scenario: {descriptions[0]} and {descriptions[1]}"
        else:
            return f"Scenario: {', '.join(descriptions[:-1])}, and {descriptions[-1]}"

    def _generate_explanation(
        self,
        result: WhatIfResult,
    ) -> str:
        """Generate natural language explanation for what-if result."""
        original_rec = self._score_to_recommendation(result.original_score)
        new_rec = result.new_recommendation

        # Score change direction
        if result.score_delta > 0.01:
            direction = "increase"
            verb = "improves"
        elif result.score_delta < -0.01:
            direction = "decrease"
            verb = "lowers"
        else:
            return (
                f"The changes would have minimal impact on the ranking score "
                f"({result.original_score:.2f} → {result.new_score:.2f}). "
                f"The recommendation remains '{new_rec}'."
            )

        # Build explanation
        explanation = (
            f"{result.scenario_description} would {direction} the ranking score "
            f"from {result.original_score:.2f} to {result.new_score:.2f} "
            f"({result.score_delta_percent:+.1f}%)."
        )

        # Add recommendation change if applicable
        if original_rec != new_rec:
            explanation += (
                f" This would change the recommendation from '{original_rec}' to '{new_rec}'."
            )

        # Add key driver if available
        if result.perturbations:
            top_perturbation = max(
                result.perturbations,
                key=lambda p: abs(p.delta_percent) if p.delta_percent != float('inf') else 0
            )
            if top_perturbation.delta_percent != float('inf'):
                label = self.FEATURE_LABELS.get(
                    top_perturbation.feature_name,
                    top_perturbation.feature_name
                )
                explanation += (
                    f" The {label.lower()} has the most significant impact on this scenario."
                )

        return explanation

    def analyze_what_if(
        self,
        resume_data: Dict[str, Any],
        vacancy_data: Dict[str, Any],
        perturbations: Dict[str, float],
        original_score: float,
        match_result: Optional[Dict[str, Any]] = None,
    ) -> WhatIfResult:
        """
        Analyze what-if scenario with feature perturbations.

        Args:
            resume_data: Original resume data
            vacancy_data: Vacancy requirements
            perturbations: Dictionary of feature_name -> delta to apply
            original_score: Original ranking score
            match_result: Optional pre-computed match result

        Returns:
            WhatIfResult with analysis of the scenario
        """
        logger.info(
            f"Analyzing what-if scenario with {len(perturbations)} perturbations, "
            f"original_score={original_score:.2f}"
        )

        # Extract original features
        original_features = RankingFeatures.extract_features(
            resume_data, vacancy_data, match_result
        )

        # Create perturbed feature vector
        perturbed_features = original_features.copy()
        perturbation_list = []

        for feature_name, delta in perturbations.items():
            # Find feature index
            try:
                feature_idx = RankingFeatures.FEATURE_NAMES.index(feature_name)
            except ValueError:
                logger.warning(f"Unknown feature: {feature_name}, skipping")
                continue

            original_value = float(original_features[feature_idx])
            perturbed_value = original_value + delta

            # Clamp to valid range
            min_val, max_val = self.FEATURE_RANGES.get(feature_name, (0.0, 1.0))
            perturbed_value = max(min_val, min(max_val, perturbed_value))

            # Calculate delta and percent
            actual_delta = perturbed_value - original_value
            delta_percent = (
                (actual_delta / original_value * 100)
                if original_value != 0
                else float('inf') if actual_delta > 0 else 0
            )

            # Apply perturbation
            perturbed_features[feature_idx] = perturbed_value

            perturbation_list.append(FeaturePerturbation(
                feature_name=feature_name,
                original_value=original_value,
                perturbed_value=perturbed_value,
                delta=actual_delta,
                delta_percent=delta_percent,
            ))

        # Get new score
        new_score = self.model.predict_proba(perturbed_features)

        # Calculate deltas
        score_delta = new_score - original_score
        score_delta_percent = (score_delta / original_score * 100) if original_score > 0 else 0

        # Get new recommendation
        new_recommendation = self._score_to_recommendation(new_score)

        # Calculate feature impacts
        feature_impacts = {}
        for perturbation in perturbation_list:
            # Estimate impact using feature importance
            importances = self.model.get_feature_importance()
            weight = importances.get(perturbation.feature_name, 0)
            impact = perturbation.delta * weight
            feature_impacts[perturbation.feature_name] = float(impact)

        # Create scenario description
        scenario_description = self._create_scenario_description(perturbation_list)

        # Create result
        result = WhatIfResult(
            scenario_description=scenario_description,
            original_score=original_score,
            new_score=new_score,
            score_delta=score_delta,
            score_delta_percent=score_delta_percent,
            new_recommendation=new_recommendation,
            perturbations=perturbation_list,
            feature_impacts=feature_impacts,
            explanation="",  # Will be filled by _generate_explanation
        )

        # Generate explanation
        result.explanation = self._generate_explanation(result)

        logger.info(
            f"What-if analysis complete: score {original_score:.2f} → {new_score:.2f} "
            f"({score_delta_percent:+.1f}%)"
        )

        return result

    def analyze_sensitivity(
        self,
        resume_data: Dict[str, Any],
        vacancy_data: Dict[str, Any],
        original_score: float,
        match_result: Optional[Dict[str, Any]] = None,
        perturbation_percent: float = 0.1,
    ) -> SensitivitySummary:
        """
        Analyze sensitivity of ranking to each feature.

        Tests how much the ranking changes when each feature is perturbed
        by a given percentage.

        Args:
            resume_data: Resume data
            vacancy_data: Vacancy requirements
            original_score: Original ranking score
            match_result: Optional pre-computed match result
            perturbation_percent: Percentage to perturb each feature (default 10%)

        Returns:
            SensitivitySummary with feature sensitivity analysis
        """
        logger.info(
            f"Analyzing feature sensitivity with {perturbation_percent*100:.1f}% perturbation"
        )

        sensitivity_scores = {}
        feature_impacts = []

        # Extract original features
        original_features = RankingFeatures.extract_features(
            resume_data, vacancy_data, match_result
        )

        # Get feature importances from model
        importances = self.model.get_feature_importance()

        # Test each feature
        for i, feature_name in enumerate(RankingFeatures.FEATURE_NAMES):
            # Get feature value and range
            feature_value = float(original_features[i])
            min_val, max_val = self.FEATURE_RANGES.get(feature_name, (0.0, 1.0))
            range_size = max_val - min_val

            if range_size == 0:
                sensitivity_scores[feature_name] = 0.0
                continue

            # Calculate perturbation amount
            if feature_name == "experience_months":
                delta = 6.0  # 6 months
            else:
                delta = range_size * perturbation_percent

            # Apply perturbation upward
            perturbed_features = original_features.copy()
            perturbed_features[i] = min(max_val, feature_value + delta)

            # Get new score
            new_score = self.model.predict_proba(perturbed_features)
            score_change = abs(new_score - original_score)

            # Normalize by perturbation amount
            if delta > 0:
                sensitivity = score_change / delta
            else:
                sensitivity = 0.0

            # Weight by feature importance
            weighted_sensitivity = sensitivity * importances.get(feature_name, 1.0)
            sensitivity_scores[feature_name] = float(weighted_sensitivity)
            feature_impacts.append((feature_name, float(weighted_sensitivity)))

        # Sort by sensitivity
        feature_impacts.sort(key=lambda x: x[1], reverse=True)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            feature_impacts[:5],  # Top 5 features
            resume_data,
            vacancy_data,
        )

        result = SensitivitySummary(
            most_sensitive_features=feature_impacts,
            sensitivity_scores=sensitivity_scores,
            recommendations=recommendations,
        )

        logger.info(
            f"Sensitivity analysis complete. Most sensitive feature: "
            f"{feature_impacts[0][0] if feature_impacts else 'N/A'}"
        )

        return result

    def _generate_recommendations(
        self,
        top_features: List[Tuple[str, float]],
        resume_data: Dict[str, Any],
        vacancy_data: Dict[str, Any],
    ) -> List[str]:
        """Generate recommendations based on sensitivity analysis."""
        recommendations = []

        required_skills = vacancy_data.get("required_skills", [])
        resume_skills = resume_data.get("skills", [])

        for feature_name, sensitivity in top_features:
            if sensitivity < 0.01:
                continue

            label = self.FEATURE_LABELS.get(feature_name, feature_name)

            if feature_name == "skills_match_ratio":
                matched = len([
                    s for s in required_skills
                    if s.lower() in [rs.lower() for rs in resume_skills]
                ])
                missing = len(required_skills) - matched
                if missing > 0:
                    recommendations.append(
                        f"Improve {label.lower()} by adding experience with "
                        f"{min(3, missing)} of the missing required skills."
                    )

            elif feature_name == "experience_months":
                recommendations.append(
                    f"Gain more relevant experience to improve the {label.lower()}."
                )

            elif feature_name == "experience_relevance":
                recommendations.append(
                    f"Focus on experience more directly related to the required skills "
                    f"to improve {label.lower()}."
                )

            elif feature_name == "education_level":
                recommendations.append(
                    f"Consider additional certifications or education to improve {label.lower()}."
                )

            elif feature_name == "completeness_score":
                recommendations.append(
                    f"Enhance the resume by adding more details to improve {label.lower()}."
                )

            else:
                recommendations.append(
                    f"Focus on improving {label.lower()} to increase ranking score."
                )

        # Limit to 5 recommendations
        return recommendations[:5]

    def generate_counterfactuals(
        self,
        resume_data: Dict[str, Any],
        vacancy_data: Dict[str, Any],
        original_score: float,
        target_score: float,
        match_result: Optional[Dict[str, Any]] = None,
        max_iterations: int = 100,
    ) -> List[WhatIfResult]:
        """
        Generate counterfactual scenarios to reach target score.

        Finds combinations of feature changes that would achieve the
        desired ranking score.

        Args:
            resume_data: Resume data
            vacancy_data: Vacancy requirements
            original_score: Original ranking score
            target_score: Target ranking score to achieve
            match_result: Optional pre-computed match result
            max_iterations: Maximum scenarios to generate

        Returns:
            List of WhatIfResult scenarios that reach target score
        """
        logger.info(
            f"Generating counterfactuals to reach target score {target_score:.2f} "
            f"from {original_score:.2f}"
        )

        counterfactuals = []

        # Get feature importances to prioritize changes
        importances = self.model.get_feature_importance()

        # Sort features by importance
        sorted_features = sorted(
            importances.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Try single-feature changes first
        for feature_name, importance in sorted_features[:5]:
            # Determine direction (need higher or lower score?)
            if target_score > original_score:
                # Need to increase - add positive delta
                if feature_name == "experience_months":
                    deltas = [6, 12, 24, 36, 60]  # months
                else:
                    deltas = [0.05, 0.1, 0.15, 0.2, 0.3]
            else:
                # Need to decrease - add negative delta
                if feature_name == "experience_months":
                    deltas = [-6, -12, -24, -36, -60]
                else:
                    deltas = [-0.05, -0.1, -0.15, -0.2, -0.3]

            # Try each delta
            for delta in deltas:
                result = self.analyze_what_if(
                    resume_data=resume_data,
                    vacancy_data=vacancy_data,
                    perturbations={feature_name: delta},
                    original_score=original_score,
                    match_result=match_result,
                )

                # Check if target reached
                if target_score > original_score:
                    reached = result.new_score >= target_score
                else:
                    reached = result.new_score <= target_score

                if reached:
                    counterfactuals.append(result)
                    break

                if len(counterfactuals) >= max_iterations:
                    break

            if len(counterfactuals) >= max_iterations:
                break

        # If not enough single-feature solutions, try combinations
        if len(counterfactuals) < 3 and target_score > original_score:
            # Try improving top 2 features together
            top_features = [f for f, _ in sorted_features[:2]]
            perturbations = {}
            for f in top_features:
                if f == "experience_months":
                    perturbations[f] = 12
                else:
                    perturbations[f] = 0.1

            result = self.analyze_what_if(
                resume_data=resume_data,
                vacancy_data=vacancy_data,
                perturbations=perturbations,
                original_score=original_score,
                match_result=match_result,
            )

            if result.new_score >= target_score:
                counterfactuals.append(result)

        logger.info(f"Generated {len(counterfactuals)} counterfactual scenarios")
        return counterfactuals[:max_iterations]

    async def analyze_from_db(
        self,
        db: AsyncSession,
        resume_id: UUID,
        vacancy_id: UUID,
        perturbations: Dict[str, float],
    ) -> WhatIfResult:
        """
        Analyze what-if scenario using database records.

        Fetches resume and vacancy data from database and performs analysis.

        Args:
            db: Database session
            resume_id: Resume UUID
            vacancy_id: JobVacancy UUID
            perturbations: Feature perturbations to apply

        Returns:
            WhatIfResult with analysis

        Raises:
            ValueError: If resume or vacancy not found
        """
        # Fetch resume
        resume_query = select(Resume).where(Resume.id == resume_id)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        # Fetch vacancy
        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_id)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        if not vacancy:
            raise ValueError(f"Vacancy not found: {vacancy_id}")

        # Fetch existing ranking
        rank_query = select(CandidateRank).where(
            CandidateRank.resume_id == resume_id,
            CandidateRank.vacancy_id == vacancy_id,
        )
        rank_result = await db.execute(rank_query)
        ranking = rank_result.scalar_one_or_none()

        if not ranking:
            raise ValueError(f"No ranking found for resume {resume_id} and vacancy {vacancy_id}")

        # Fetch match result
        match_query = select(MatchResult).where(
            MatchResult.resume_id == resume_id,
            MatchResult.vacancy_id == vacancy_id,
        )
        match_result_obj = await db.execute(match_query)
        match_record = match_result_obj.scalar_one_or_none()

        match_result = None
        if match_record:
            match_result = {
                "overall_score": float(match_record.overall_score or 0),
                "keyword_score": float(match_record.keyword_score or 0),
                "tfidf_score": float(match_record.tfidf_score or 0),
                "vector_score": float(match_record.vector_score or 0),
            }

        # Prepare resume data
        resume_data = {
            "id": str(resume.id),
            "title": resume.raw_text[:100] if resume.raw_text else "",
            "skills": [],
            "experience": {},
            "education": {},
            "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
        }

        # Try to get skills from ResumeAnalysis
        analysis_query = select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)
        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()

        if analysis:
            if analysis.skills:
                resume_data["skills"] = analysis.skills
            if analysis.raw_text:
                resume_data["title"] = analysis.raw_text[:100]

        # Prepare vacancy data
        vacancy_data = {
            "id": str(vacancy.id),
            "title": vacancy.title,
            "required_skills": vacancy.required_skills or [],
            "description": vacancy.description or "",
        }

        # Perform analysis
        return self.analyze_what_if(
            resume_data=resume_data,
            vacancy_data=vacancy_data,
            perturbations=perturbations,
            original_score=float(ranking.rank_score),
            match_result=match_result,
        )


# Global service instance
_default_analyzer: Optional[SensitivityAnalyzer] = None


def get_sensitivity_analyzer() -> SensitivityAnalyzer:
    """Get or create global sensitivity analyzer instance."""
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = SensitivityAnalyzer()
    return _default_analyzer
