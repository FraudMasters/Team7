"""
Fairness Scorecard Service for AI Bias Detection Dashboard

This module provides functionality to generate fairness scorecards that aggregate
fairness metrics into actionable insights for hiring managers and compliance officers.

The service supports:
- Overall fairness score calculation (0-100)
- Metrics aggregation by demographic attribute
- Severity-based alert aggregation
- Actionable insights generation

Score calculation:
- Aggregates disparate impact ratios across demographic groups
- Incorporates statistical parity differences
- Accounts for alert severity levels
- Returns 0-100 score where 100 = perfectly fair

Usage:
    >>> scorecard = get_fairness_scorecard()
    >>> result = await scorecard.generate_scorecard(
    ...     db=db,
    ...     vacancy_id=vacancy_id
    ... )
    >>> print(result.fairness_score)  # 0-100
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from models import FairnessAlert, FairnessMetrics, JobVacancy

logger = logging.getLogger(__name__)

# Global scorecard instance
_fairness_scorecard: Optional["FairnessScorecard"] = None

# Score calculation constants
DEFAULT_DISPARATE_IMPACT_WEIGHT = 0.5
DEFAULT_STATISTICAL_PARITY_WEIGHT = 0.3
DEFAULT_ALERT_SEVERITY_WEIGHT = 0.2

# Severity penalty values (higher = more penalty)
SEVERITY_PENALTIES = {
    "low": 5,
    "medium": 15,
    "high": 30,
    "critical": 50,
}


@dataclass
class FairnessScorecardData:
    """
    Data structure for fairness scorecard.

    Attributes:
        vacancy_id: JobVacancy UUID (optional for org-wide scorecards)
        vacancy_title: Job title for context
        fairness_score: Overall fairness score (0-100)
        score_breakdown: Component scores that make up the overall score
        metrics_by_demographic: Detailed metrics grouped by demographic attribute
        alerts_summary: Summary of active alerts by severity
        recommendations: List of actionable recommendations
        analyzed_at: Timestamp of scorecard generation
        total_sample_size: Total candidates analyzed
        demographics_analyzed: List of demographic attributes analyzed
        model_version: Model version analyzed (if applicable)
    """
    vacancy_id: Optional[str] = None
    vacancy_title: Optional[str] = None
    fairness_score: float = 0.0
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    metrics_by_demographic: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    alerts_summary: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    analyzed_at: str = ""
    total_sample_size: int = 0
    demographics_analyzed: List[str] = field(default_factory=list)
    model_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "vacancy_id": self.vacancy_id,
            "vacancy_title": self.vacancy_title,
            "fairness_score": self.fairness_score,
            "score_breakdown": self.score_breakdown,
            "metrics_by_demographic": self.metrics_by_demographic,
            "alerts_summary": self.alerts_summary,
            "recommendations": self.recommendations,
            "analyzed_at": self.analyzed_at,
            "total_sample_size": self.total_sample_size,
            "demographics_analyzed": self.demographics_analyzed,
            "model_version": self.model_version,
        }


class FairnessScorecard:
    """
    Fairness Scorecard Generation Service.

    This service generates comprehensive fairness scorecards that aggregate
    fairness metrics into an overall score (0-100) with detailed breakdowns
    by demographic attribute and actionable recommendations.

    The scorecard combines:
    - Disparate Impact Ratio (80% rule compliance)
    - Statistical Parity Difference
    - Alert Severity levels
    - Sample size considerations

    Attributes:
        disparate_impact_weight: Weight for disparate impact in score (0-1)
        statistical_parity_weight: Weight for statistical parity in score (0-1)
        alert_severity_weight: Weight for alert severity in score (0-1)
        severity_penalties: Penalty points per severity level

    Example:
        >>> scorecard = FairnessScorecard()
        >>> result = await scorecard.generate_scorecard(
        ...     db=db,
        ...     vacancy_id=vacancy_id
        ... )
        >>> print(f"Fairness Score: {result.fairness_score}/100")
    """

    # Score ranges
    SCORE_EXCELLENT = 90
    SCORE_GOOD = 75
    SCORE_FAIR = 60
    SCORE_POOR = 40

    # Demographic attributes
    DEMOGRAPHIC_ATTRIBUTES = ["gender", "age_group", "ethnicity"]

    def __init__(
        self,
        disparate_impact_weight: float = DEFAULT_DISPARATE_IMPACT_WEIGHT,
        statistical_parity_weight: float = DEFAULT_STATISTICAL_PARITY_WEIGHT,
        alert_severity_weight: float = DEFAULT_ALERT_SEVERITY_WEIGHT,
        severity_penalties: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Initialize the fairness scorecard service.

        Args:
            disparate_impact_weight: Weight for disparate impact score (0-1)
            statistical_parity_weight: Weight for statistical parity score (0-1)
            alert_severity_weight: Weight for alert severity penalty (0-1)
            severity_penalties: Custom severity penalty values
        """
        self.disparate_impact_weight = disparate_impact_weight
        self.statistical_parity_weight = statistical_parity_weight
        self.alert_severity_weight = alert_severity_weight
        self.severity_penalties = severity_penalties or SEVERITY_PENALTIES

    async def generate_scorecard(
        self,
        db: AsyncSession,
        vacancy_id: Optional[UUID] = None,
        model_version: Optional[str] = None,
        analysis_date: Optional[str] = None,
    ) -> FairnessScorecardData:
        """
        Generate a comprehensive fairness scorecard.

        Args:
            db: Database session
            vacancy_id: Optional JobVacancy UUID for specific vacancy analysis
            model_version: Optional model version filter
            analysis_date: Optional analysis date filter

        Returns:
            FairnessScorecardData with complete scorecard information
        """
        try:
            logger.info(
                f"Generating fairness scorecard for vacancy {vacancy_id}, "
                f"model {model_version}"
            )

            # Fetch fairness metrics
            metrics = await self._fetch_fairness_metrics(
                db, vacancy_id, model_version, analysis_date
            )

            if not metrics:
                logger.warning("No fairness metrics found for scorecard generation")
                return self._empty_scorecard(vacancy_id)

            # Fetch related alerts
            alerts = await self._fetch_fairness_alerts(
                db, [m.id for m in metrics]
            )

            # Get vacancy title if applicable
            vacancy_title = None
            if vacancy_id:
                vacancy_title = await self._get_vacancy_title(db, vacancy_id)

            # Calculate overall fairness score
            fairness_score, score_breakdown = self._calculate_fairness_score(
                metrics, alerts
            )

            # Aggregate metrics by demographic
            metrics_by_demographic = self._aggregate_metrics_by_demographic(metrics)

            # Summarize alerts by severity
            alerts_summary = self._summarize_alerts(alerts)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                metrics, alerts, fairness_score
            )

            # Calculate total sample size
            total_sample_size = max(
                (m.total_sample_size or 0) for m in metrics
            ) if metrics else 0

            # Get demographics analyzed
            demographics_analyzed = sorted(set(
                m.demographic_group for m in metrics
            ))

            # Get model version
            resolved_model_version = metrics[0].model_version_id if metrics else None

            return FairnessScorecardData(
                vacancy_id=str(vacancy_id) if vacancy_id else None,
                vacancy_title=vacancy_title,
                fairness_score=round(fairness_score, 2),
                score_breakdown=score_breakdown,
                metrics_by_demographic=metrics_by_demographic,
                alerts_summary=alerts_summary,
                recommendations=recommendations,
                analyzed_at=datetime.utcnow().isoformat(),
                total_sample_size=total_sample_size,
                demographics_analyzed=demographics_analyzed,
                model_version=resolved_model_version,
            )

        except Exception as e:
            logger.error(f"Error generating fairness scorecard: {e}", exc_info=True)
            raise

    async def _fetch_fairness_metrics(
        self,
        db: AsyncSession,
        vacancy_id: Optional[UUID],
        model_version: Optional[str],
        analysis_date: Optional[str],
    ) -> List[FairnessMetrics]:
        """
        Fetch fairness metrics from database.

        Args:
            db: Database session
            vacancy_id: Optional vacancy filter
            model_version: Optional model version filter
            analysis_date: Optional analysis date filter

        Returns:
            List of FairnessMetrics records
        """
        query = select(FairnessMetrics)

        if vacancy_id:
            query = query.where(FairnessMetrics.vacancy_id == vacancy_id)

        if model_version:
            query = query.where(FairnessMetrics.model_version_id == model_version)

        if analysis_date:
            query = query.where(FairnessMetrics.analysis_date == analysis_date)
        else:
            # Get most recent analysis date
            latest_date_query = select(
                FairnessMetrics.analysis_date
            ).order_by(
                FairnessMetrics.analysis_date.desc()
            ).limit(1)

            if vacancy_id:
                latest_date_query = latest_date_query.where(
                    FairnessMetrics.vacancy_id == vacancy_id
                )

            latest_date_result = await db.execute(latest_date_query)
            latest_date = latest_date_result.scalar_one_or_none()

            if latest_date:
                query = query.where(FairnessMetrics.analysis_date == latest_date)

        query = query.order_by(FairnessMetrics.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def _fetch_fairness_alerts(
        self,
        db: AsyncSession,
        metric_ids: List[UUID],
    ) -> List[FairnessAlert]:
        """
        Fetch fairness alerts for given metric IDs.

        Args:
            db: Database session
            metric_ids: List of FairnessMetric IDs

        Returns:
            List of FairnessAlert records
        """
        if not metric_ids:
            return []

        query = select(FairnessAlert).where(
            FairnessAlert.fairness_metric_id.in_(metric_ids)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def _get_vacancy_title(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
    ) -> Optional[str]:
        """
        Get vacancy title for context.

        Args:
            db: Database session
            vacancy_id: JobVacancy UUID

        Returns:
            Vacancy title or None
        """
        try:
            query = select(JobVacancy.title).where(JobVacancy.id == vacancy_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception:
            return None

    def _calculate_fairness_score(
        self,
        metrics: List[FairnessMetrics],
        alerts: List[FairnessAlert],
    ) -> tuple[float, Dict[str, float]]:
        """
        Calculate overall fairness score (0-100).

        Score components:
        - Disparate Impact: Average ratio converted to 0-100
        - Statistical Parity: Inverse of average absolute difference
        - Alert Penalty: Severity-based deductions

        Args:
            metrics: List of fairness metrics
            alerts: List of fairness alerts

        Returns:
            Tuple of (overall_score, score_breakdown)
        """
        # Extract disparate impact ratios
        di_ratios = [
            float(m.disparate_impact_ratio or 1.0)
            for m in metrics
            if m.disparate_impact_ratio is not None
        ]

        # Extract statistical parity differences
        sp_diffs = [
            abs(float(m.statistical_parity_difference or 0))
            for m in metrics
            if m.statistical_parity_difference is not None
        ]

        # Calculate disparate impact score (0-100)
        if di_ratios:
            avg_di = sum(di_ratios) / len(di_ratios)
            # Convert to 0-100: ratio of 0.8 = 80, ratio of 1.0 = 100
            di_score = min(avg_di * 100, 100)
        else:
            di_score = 100.0  # No bias detected = perfect score

        # Calculate statistical parity score (0-100)
        # Lower difference = higher score
        if sp_diffs:
            avg_sp = sum(sp_diffs) / len(sp_diffs)
            # Convert to 0-100: difference of 0 = 100, difference of 0.3 = 0
            sp_score = max(100 - (avg_sp * 333), 0)
        else:
            sp_score = 100.0

        # Calculate alert penalty
        alert_penalty = 0.0
        for alert in alerts:
            if alert.status == "active":
                severity = alert.severity or "low"
                alert_penalty += self.severity_penalties.get(severity, 0)

        # Cap penalty at 100
        alert_penalty = min(alert_penalty, 100)

        # Calculate weighted score
        weighted_di = di_score * self.disparate_impact_weight
        weighted_sp = sp_score * self.statistical_parity_weight
        weighted_penalty = alert_penalty * self.alert_severity_weight

        overall_score = max(weighted_di + weighted_sp - weighted_penalty, 0)

        score_breakdown = {
            "disparate_impact_score": round(di_score, 2),
            "statistical_parity_score": round(sp_score, 2),
            "alert_penalty": round(alert_penalty, 2),
            "weighted_disparate_impact": round(weighted_di, 2),
            "weighted_statistical_parity": round(weighted_sp, 2),
            "weighted_penalty": round(weighted_penalty, 2),
        }

        return overall_score, score_breakdown

    def _aggregate_metrics_by_demographic(
        self,
        metrics: List[FairnessMetrics],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate metrics by demographic attribute.

        Args:
            metrics: List of fairness metrics

        Returns:
            Dictionary grouped by demographic attribute
        """
        result = {}

        for metric in metrics:
            attr = metric.demographic_group

            if attr not in result:
                result[attr] = {
                    "disparate_impact_ratio": float(metric.disparate_impact_ratio or 0),
                    "statistical_parity_difference": float(
                        metric.statistical_parity_difference or 0
                    ),
                    "alert_triggered": metric.alert_triggered,
                    "alert_severity": metric.alert_severity,
                    "total_sample_size": metric.total_sample_size or 0,
                    "group_metrics": metric.group_metrics or {},
                    "mitigation_suggested": metric.mitigation_suggested,
                }

        return result

    def _summarize_alerts(
        self,
        alerts: List[FairnessAlert],
    ) -> Dict[str, int]:
        """
        Summarize alerts by severity level.

        Args:
            alerts: List of fairness alerts

        Returns:
            Dictionary with count per severity
        """
        summary = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for alert in alerts:
            if alert.status == "active":
                severity = alert.severity or "low"
                if severity in summary:
                    summary[severity] += 1

        return summary

    def _generate_recommendations(
        self,
        metrics: List[FairnessMetrics],
        alerts: List[FairnessAlert],
        fairness_score: float,
    ) -> List[str]:
        """
        Generate actionable recommendations based on metrics and alerts.

        Args:
            metrics: List of fairness metrics
            alerts: List of fairness alerts
            fairness_score: Overall fairness score

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Score-based recommendation
        if fairness_score >= self.SCORE_EXCELLENT:
            recommendations.append(
                "Excellent fairness score detected. Continue current practices "
                "and monitor regularly."
            )
        elif fairness_score >= self.SCORE_GOOD:
            recommendations.append(
                "Good fairness score. Minor improvements could optimize fairness "
                "across all demographic groups."
            )
        elif fairness_score >= self.SCORE_FAIR:
            recommendations.append(
                "Fairness concerns detected. Review ranking model and consider "
                "fairness-aware retraining."
            )
        else:
            recommendations.append(
                "Significant fairness concerns detected. Immediate review and "
                "remediation recommended before production use."
            )

        # Alert-based recommendations
        critical_alerts = [a for a in alerts if a.severity == "critical" and a.status == "active"]
        if critical_alerts:
            recommendations.append(
                f"{len(critical_alerts)} critical alert(s) detected. "
                "Priority: Re-evaluate model training data and feature engineering."
            )

        high_alerts = [a for a in alerts if a.severity == "high" and a.status == "active"]
        if high_alerts:
            recommendations.append(
                f"{len(high_alerts)} high severity alert(s). "
                "Recommendation: Apply fairness-aware ranking algorithms."
            )

        # Generate actionable insights based on metrics
        actionable_insights = self._generate_actionable_insights(metrics, fairness_score)
        recommendations.extend(actionable_insights)

        # Metric-specific recommendations
        for metric in metrics:
            if metric.alert_triggered and metric.mitigation_suggested:
                # Only add if not duplicate
                if not any(
                    metric.demographic_group in r
                    for r in recommendations
                ):
                    recommendations.append(
                        f"{metric.demographic_group}: {metric.mitigation_suggested}"
                    )

        return recommendations

    def _generate_actionable_insights(
        self,
        metrics: List[FairnessMetrics],
        fairness_score: float,
    ) -> List[str]:
        """
        Generate detailed actionable insights based on bias metrics.

        Provides specific recommendations including:
        - Model retraining suggestions
        - Threshold adjustment recommendations
        - Feature review guidance
        - Sample size improvement suggestions

        Args:
            metrics: List of fairness metrics
            fairness_score: Overall fairness score

        Returns:
            List of actionable insight strings
        """
        insights = []

        if not metrics:
            return insights

        # Analyze disparate impact patterns
        low_di_metrics = [
            m for m in metrics
            if m.disparate_impact_ratio is not None
            and m.disparate_impact_ratio < 0.8
        ]

        if low_di_metrics:
            # Sort by severity
            low_di_metrics.sort(key=lambda m: float(m.disparate_impact_ratio or 0))

            most_severe = low_di_metrics[0]
            di_ratio = float(most_severe.disparate_impact_ratio or 0)

            if di_ratio < 0.5:
                insights.append(
                    "CRITICAL: Retrain ranking model with balanced training data "
                    f"to address severe disparate impact in {most_severe.demographic_group}. "
                    "Current ratio indicates significant adverse impact."
                )
            elif di_ratio < 0.65:
                insights.append(
                    "Retrain ranking model using fairness-aware techniques "
                    f"(e.g., adversarial debiasing, reweighting) for {most_severe.demographic_group}. "
                    "Consider applying fairness constraints during model training."
                )

        # Analyze statistical parity patterns
        high_sp_metrics = [
            m for m in metrics
            if m.statistical_parity_difference is not None
            and abs(m.statistical_parity_difference) > 0.1
        ]

        if high_sp_metrics:
            # Sort by absolute difference
            high_sp_metrics.sort(
                key=lambda m: abs(float(m.statistical_parity_difference or 0)),
                reverse=True
            )

            worst_sp = high_sp_metrics[0]
            sp_diff = abs(float(worst_sp.statistical_parity_difference or 0))

            if sp_diff > 0.2:
                insights.append(
                    "Adjust ranking thresholds to reduce selection rate disparity. "
                    f"Consider group-specific threshold calibration for {worst_sp.demographic_group} "
                    "or implement post-processing equalization techniques."
                )
            elif sp_diff > 0.15:
                insights.append(
                    "Review ranking score distribution across demographic groups. "
                    "Threshold adjustment or score calibration may improve fairness."
                )

        # Sample size analysis
        for metric in metrics:
            if metric.group_sample_size and metric.group_sample_size < 10:
                insights.append(
                    f"Increase sample size for {metric.demographic_group} "
                    f"(current: {metric.group_sample_size}). "
                    "Small sample sizes may lead to unreliable fairness metrics. "
                    "Collect more data to improve analysis confidence."
                )

        # Feature-based recommendations (if group metrics available)
        features_to_review = self._identify_features_for_review(metrics)
        if features_to_review:
            for feature, demographic in features_to_review:
                insights.append(
                    f"Review feature '{feature}' for potential bias against {demographic}. "
                    "This feature may be acting as a proxy for protected attributes. "
                    "Consider feature removal or transformation."
                )

        # Model-specific recommendations based on fairness-aware status
        fairness_aware_count = sum(1 for m in metrics if m.is_fairness_aware)
        total_count = len(metrics)

        if total_count > 0 and fairness_aware_count == 0:
            insights.append(
                "Enable fairness-aware ranking mode to reduce algorithmic bias. "
                "The current model does not use fairness constraints during ranking."
            )
        elif fairness_aware_count < total_count:
            insights.append(
                f"Only {fairness_aware_count}/{total_count} analyses use fairness-aware ranking. "
                "Consider enabling fairness-aware mode across all rankings for consistency."
            )

        # Threshold-specific guidance
        if fairness_score >= self.SCORE_GOOD and fairness_score < self.SCORE_EXCELLENT:
            insights.append(
                "Fine-tune ranking model by adjusting feature weights or "
                "applying light regularization to improve fairness without significant accuracy loss."
            )

        return insights

    def _identify_features_for_review(
        self,
        metrics: List[FairnessMetrics],
    ) -> List[tuple[str, str]]:
        """
        Identify features that may be contributing to bias for review.

        Analyzes group metrics to identify features that correlate with
        demographic disparities.

        Args:
            metrics: List of fairness metrics

        Returns:
            List of (feature_name, demographic_group) tuples to review
        """
        features_to_review = []

        # Features that commonly act as proxies for protected attributes
        proxy_features = {
            "gender": ["name", "pronouns", "gendered_words", "titles"],
            "age_group": ["graduation_year", "experience_duration", "career_start"],
            "ethnicity": ["names", "language_patterns", "location", "schools"],
        }

        for metric in metrics:
            if metric.alert_triggered and metric.group_metrics:
                # Check if any groups have significantly lower selection rates
                group_data = metric.group_metrics or {}
                selection_rates = {
                    group: data.get("selection_rate", 0)
                    for group, data in group_data.items()
                }

                if selection_rates:
                    max_rate = max(selection_rates.values())
                    for group, rate in selection_rates.items():
                        if rate < max_rate * 0.7:  # 30% lower than max
                            demographic = metric.demographic_group
                            if demographic in proxy_features:
                                # Add proxy features for review
                                for feature in proxy_features[demographic][:2]:  # Top 2
                                    features_to_review.append((feature, demographic))

        return features_to_review[:5]  # Limit to 5 recommendations

    def _empty_scorecard(
        self,
        vacancy_id: Optional[UUID],
    ) -> FairnessScorecardData:
        """Return an empty scorecard when no data is available."""
        return FairnessScorecardData(
            vacancy_id=str(vacancy_id) if vacancy_id else None,
            fairness_score=0.0,
            score_breakdown={},
            metrics_by_demographic={},
            alerts_summary={},
            recommendations=["No fairness metrics available for analysis."],
            analyzed_at=datetime.utcnow().isoformat(),
            total_sample_size=0,
            demographics_analyzed=[],
            model_version=None,
        )


def get_fairness_scorecard() -> FairnessScorecard:
    """
    Get the global fairness scorecard instance.

    Returns the singleton FairnessScorecard instance, creating it if necessary.

    Returns:
        FairnessScorecard instance

    Example:
        >>> scorecard = get_fairness_scorecard()
        >>> result = await scorecard.generate_scorecard(db=db, vacancy_id=vacancy_id)
    """
    global _fairness_scorecard

    if _fairness_scorecard is None:
        _fairness_scorecard = FairnessScorecard()

    return _fairness_scorecard
