"""
Fairness Calculator for AI Bias Detection

This module provides fairness metrics computation for detecting demographic bias
in candidate ranking outcomes. It calculates:
- Disparate Impact Ratio (80% rule compliance)
- Statistical Parity Difference
- Group selection rates and comparisons
- Bias alerts when thresholds are exceeded

Used for compliance monitoring (EEOC, FCRA) and ensuring ethical AI practices.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from sqlalchemy import select, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    CandidateRank,
    DemographicInference,
    FairnessAlert,
    FairnessMetrics,
    JobVacancy,
)

logger = logging.getLogger(__name__)

# Fairness threshold constants
DEFAULT_DISPARATE_IMPACT_THRESHOLD = 0.8  # 80% rule
DEFAULT_STATISTICAL_PARITY_THRESHOLD = 0.1  # 10% difference
MIN_SAMPLE_SIZE = 5  # Minimum samples per group for reliable analysis


class FairnessMetricsCalculator:
    """
    Calculate fairness metrics for demographic bias detection.

    Computes standard fairness metrics from ranking outcomes to detect
    potential algorithmic bias across demographic groups.
    """

    # Demographic groups to analyze
    DEMOGRAPHIC_ATTRIBUTES = {
        "gender": ["male", "female", "non_binary"],
        "age_group": ["under_25", "25_34", "35_44", "45_54", "55_64", "65_plus"],
        "ethnicity": ["asian", "hispanic", "black_african", "white"],
    }

    def __init__(
        self,
        disparate_impact_threshold: float = DEFAULT_DISPARATE_IMPACT_THRESHOLD,
        statistical_parity_threshold: float = DEFAULT_STATISTICAL_PARITY_THRESHOLD,
    ):
        """
        Initialize the fairness calculator.

        Args:
            disparate_impact_threshold: Minimum acceptable ratio (default 0.8 for 80% rule)
            statistical_parity_threshold: Maximum acceptable difference (default 0.1)
        """
        self.disparate_impact_threshold = disparate_impact_threshold
        self.statistical_parity_threshold = statistical_parity_threshold

    def calculate_disparate_impact(
        self,
        group_selection_rate: float,
        reference_selection_rate: float,
    ) -> Tuple[float, bool]:
        """
        Calculate disparate impact ratio between groups.

        Disparate Impact = P(positive|group) / P(positive|reference)

        Args:
            group_selection_rate: Selection rate for the demographic group
            reference_selection_rate: Selection rate for reference group

        Returns:
            Tuple of (ratio, is_fair)
            - ratio: Disparate impact ratio (1.0 = fair, <0.8 = potential bias)
            - is_fair: Whether ratio meets threshold
        """
        if reference_selection_rate == 0:
            # Avoid division by zero - if reference group has 0% selection,
            # any positive selection for the group is concerning
            return 0.0, group_selection_rate == 0

        ratio = group_selection_rate / reference_selection_rate

        # Cap ratio at 2.0 for practical purposes (reverse bias exists too)
        ratio = min(ratio, 2.0)

        is_fair = ratio >= self.disparate_impact_threshold

        return ratio, is_fair

    def calculate_statistical_parity_difference(
        self,
        group_selection_rate: float,
        reference_selection_rate: float,
    ) -> Tuple[float, bool]:
        """
        Calculate statistical parity difference between groups.

        Statistical Parity Difference = P(positive|group) - P(positive|reference)

        Args:
            group_selection_rate: Selection rate for the demographic group
            reference_selection_rate: Selection rate for reference group

        Returns:
            Tuple of (difference, is_fair)
            - difference: Selection rate difference (0 = fair, large |diff| = bias)
            - is_fair: Whether difference is within threshold
        """
        difference = group_selection_rate - reference_selection_rate

        is_fair = abs(difference) <= self.statistical_parity_threshold

        return difference, is_fair

    def calculate_selection_rate(
        self,
        selected_count: int,
        total_count: int,
    ) -> float:
        """
        Calculate selection rate for a group.

        Args:
            selected_count: Number of positive outcomes
            total_count: Total group size

        Returns:
            Selection rate (0-1)
        """
        if total_count == 0:
            return 0.0

        return selected_count / total_count

    def determine_alert_severity(
        self,
        disparate_impact_ratio: float,
        statistical_parity_difference: float,
    ) -> str:
        """
        Determine alert severity based on metric values.

        Args:
            disparate_impact_ratio: Disparate impact ratio
            statistical_parity_difference: Statistical parity difference

        Returns:
            Severity level: low, medium, high, critical
        """
        # Critical: very low disparate impact (< 0.5) or high parity difference (> 0.25)
        if disparate_impact_ratio < 0.5 or abs(statistical_parity_difference) > 0.25:
            return "critical"

        # High: low disparate impact (< 0.65) or high parity difference (> 0.2)
        if disparate_impact_ratio < 0.65 or abs(statistical_parity_difference) > 0.2:
            return "high"

        # Medium: disparate impact below threshold but not severe
        if disparate_impact_ratio < self.disparate_impact_threshold:
            return "medium"

        # Low: statistical parity difference exceeded but disparate impact OK
        if abs(statistical_parity_difference) > self.statistical_parity_threshold:
            return "low"

        return None

    def generate_mitigation_suggestions(
        self,
        demographic_group: str,
        disparate_impact_ratio: float,
        statistical_parity_difference: float,
    ) -> Optional[str]:
        """
        Generate actionable mitigation suggestions based on bias detected.

        Args:
            demographic_group: The demographic group showing bias
            disparate_impact_ratio: Calculated disparate impact ratio
            statistical_parity_difference: Calculated statistical parity difference

        Returns:
            Mitigation suggestions string or None
        """
        if disparate_impact_ratio >= self.disparate_impact_threshold:
            return None

        suggestions = []

        # General recommendation
        suggestions.append("Fairness concern detected for " + demographic_group)

        # Disparate impact specific
        if disparate_impact_ratio < 0.5:
            suggestions.append("- Severe disparate impact: Consider retraining ranking model with balanced dataset")
            suggestions.append("- Review feature engineering for potential proxy variables")
        elif disparate_impact_ratio < 0.65:
            suggestions.append("- Moderate disparate impact: Apply fairness-aware ranking algorithms")

        # Statistical parity specific
        if abs(statistical_parity_difference) > 0.2:
            suggestions.append("- High selection rate disparity: Calibrate ranking thresholds by demographic group")

        # General recommendations
        suggestions.append("- Conduct manual review of ranked candidates for this demographic")
        suggestions.append("- Monitor metrics over time to track improvement")

        return "\n".join(suggestions)


class FairnessCalculator:
    """
    Main service for fairness metrics calculation and monitoring.

    Coordinates demographic data retrieval, metrics computation, and
    alert generation for bias detection in candidate ranking.
    """

    def __init__(
        self,
        disparate_impact_threshold: float = DEFAULT_DISPARATE_IMPACT_THRESHOLD,
        statistical_parity_threshold: float = DEFAULT_STATISTICAL_PARITY_THRESHOLD,
    ):
        """
        Initialize the fairness calculator.

        Args:
            disparate_impact_threshold: Minimum acceptable disparate impact ratio
            statistical_parity_threshold: Maximum acceptable statistical parity difference
        """
        self.calculator = FairnessMetricsCalculator(
            disparate_impact_threshold,
            statistical_parity_threshold,
        )

    async def analyze_vacancy_fairness(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        model_version: Optional[str] = None,
        analysis_date: Optional[str] = None,
        is_fairness_aware: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze fairness metrics for a specific vacancy's ranking outcomes.

        Args:
            db: Database session
            vacancy_id: JobVacancy UUID to analyze
            model_version: Optional model version being analyzed
            analysis_date: Date of analysis (default: today)
            is_fairness_aware: Whether fairness-aware ranking was enabled

        Returns:
            Dictionary with fairness metrics summary by demographic attribute
        """
        if analysis_date is None:
            analysis_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Analyzing fairness for vacancy {vacancy_id}")

        # Get all candidate rankings for this vacancy
        rankings_query = select(CandidateRank).where(
            CandidateRank.vacancy_id == vacancy_id
        )
        rankings_result = await db.execute(rankings_query)
        rankings = rankings_result.scalars().all()

        if len(rankings) < MIN_SAMPLE_SIZE * 2:
            logger.warning(
                f"Insufficient sample size for vacancy {vacancy_id}: "
                f"{len(rankings)} rankings (need at least {MIN_SAMPLE_SIZE * 2})"
            )
            return {
                "vacancy_id": str(vacancy_id),
                "analysis_date": analysis_date,
                "error": "insufficient_sample_size",
                "total_rankings": len(rankings),
            }

        # Get demographic inferences for all ranked resumes
        resume_ids = [r.resume_id for r in rankings]
        demographics_query = select(DemographicInference).where(
            DemographicInference.resume_id.in_(resume_ids)
        )
        demographics_result = await db.execute(demographics_query)
        demographics = {d.resume_id: d for d in demographics_result.scalars().all()}

        # Build ranking data with demographics
        ranking_data = []
        for ranking in rankings:
            demo = demographics.get(ranking.resume_id)
            if demo:
                ranking_data.append({
                    "resume_id": ranking.resume_id,
                    "rank_score": ranking.rank_score,
                    "recommendation": ranking.recommendation,
                    "gender": demo.inferred_gender,
                    "age_group": demo.inferred_age_group,
                    "ethnicity": demo.inferred_ethnicity,
                })

        if len(ranking_data) < MIN_SAMPLE_SIZE:
            logger.warning(
                f"Insufficient demographic data for vacancy {vacancy_id}: "
                f"{len(ranking_data)} with demographics"
            )
            return {
                "vacancy_id": str(vacancy_id),
                "analysis_date": analysis_date,
                "error": "insufficient_demographic_data",
                "rankings_with_demographics": len(ranking_data),
            }

        # Calculate fairness metrics for each demographic attribute
        summary = {
            "vacancy_id": str(vacancy_id),
            "analysis_date": analysis_date,
            "model_version": model_version,
            "is_fairness_aware": is_fairness_aware,
            "total_candidates": len(ranking_data),
            "attributes_analyzed": {},
        }

        # Define positive outcome (e.g., top 50% of rankings or "good"/"excellent")
        threshold_score = np.percentile([r["rank_score"] for r in ranking_data], 50)

        for attribute, groups in self.calculator.DEMOGRAPHIC_ATTRIBUTES.items():
            metrics = await self._calculate_attribute_metrics(
                db,
                vacancy_id,
                ranking_data,
                attribute,
                groups,
                threshold_score,
                model_version,
                analysis_date,
                is_fairness_aware,
            )
            summary["attributes_analyzed"][attribute] = metrics

        return summary

    async def _calculate_attribute_metrics(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        ranking_data: List[Dict[str, Any]],
        attribute: str,
        groups: List[str],
        threshold_score: float,
        model_version: Optional[str],
        analysis_date: str,
        is_fairness_aware: bool,
    ) -> Dict[str, Any]:
        """
        Calculate fairness metrics for a specific demographic attribute.

        Args:
            db: Database session
            vacancy_id: JobVacancy UUID
            ranking_data: List of ranking records with demographics
            attribute: Demographic attribute (gender, age_group, ethnicity)
            groups: List of groups in this attribute
            threshold_score: Score threshold for positive outcome
            model_version: Model version being analyzed
            analysis_date: Analysis date string
            is_fairness_aware: Whether fairness-aware ranking was used

        Returns:
            Dictionary with metrics for each group in the attribute
        """
        # Group rankings by demographic value
        group_data = {}
        for record in ranking_data:
            group_value = record.get(attribute)
            if not group_value or group_value not in groups:
                continue

            if group_value not in group_data:
                group_data[group_value] = {
                    "total": 0,
                    "selected": 0,
                    "scores": [],
                }

            group_data[group_value]["total"] += 1
            group_data[group_value]["scores"].append(record["rank_score"])

            # Positive outcome: score above threshold or good/excellent recommendation
            if record["rank_score"] >= threshold_score or record["recommendation"] in ["good", "excellent"]:
                group_data[group_value]["selected"] += 1

        # Calculate metrics for each group
        group_metrics = {}
        reference_rate = None

        # Find reference group (largest group or highest selection rate)
        for group_value, data in group_data.items():
            if data["total"] >= MIN_SAMPLE_SIZE:
                rate = self.calculator.calculate_selection_rate(
                    data["selected"], data["total"]
                )
                if reference_rate is None or rate > reference_rate:
                    reference_rate = rate

        if reference_rate is None:
            # No group meets minimum sample size
            return {"error": "insufficient_group_sizes"}

        # Calculate metrics for all groups
        alert_triggered = False
        max_severity = None

        for group_value, data in group_data.items():
            if data["total"] < MIN_SAMPLE_SIZE:
                # Skip groups with insufficient sample size
                continue

            group_rate = self.calculator.calculate_selection_rate(
                data["selected"], data["total"]
            )

            disparate_impact, di_fair = self.calculator.calculate_disparate_impact(
                group_rate, reference_rate
            )

            stat_parity_diff, sp_fair = self.calculator.calculate_statistical_parity_difference(
                group_rate, reference_rate
            )

            is_fair = di_fair and sp_fair
            severity = self.calculator.determine_alert_severity(
                disparate_impact, stat_parity_diff
            )

            if severity and (not max_severity or self._severity_rank(severity) > self._severity_rank(max_severity)):
                max_severity = severity
                alert_triggered = True

            mitigation = self.calculator.generate_mitigation_suggestions(
                f"{attribute}={group_value}",
                disparate_impact,
                stat_parity_diff,
            )

            group_metrics[group_value] = {
                "sample_size": data["total"],
                "selected_count": data["selected"],
                "selection_rate": round(group_rate, 4),
                "disparate_impact_ratio": round(disparate_impact, 4),
                "statistical_parity_difference": round(stat_parity_diff, 4),
                "is_fair": is_fair,
                "alert_severity": severity,
                "mitigation_suggested": mitigation,
            }

        # Store aggregate metrics in database
        await self._store_fairness_metrics(
            db,
            vacancy_id,
            attribute,
            group_data,
            group_metrics,
            reference_rate,
            model_version,
            analysis_date,
            is_fairness_aware,
            max_severity,
            alert_triggered,
        )

        return {
            "groups": group_metrics,
            "reference_selection_rate": round(reference_rate, 4),
            "alert_triggered": alert_triggered,
            "max_severity": max_severity,
        }

    async def _store_fairness_metrics(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        demographic_group: str,
        group_data: Dict[str, Dict],
        group_metrics: Dict[str, Dict],
        reference_rate: float,
        model_version: Optional[str],
        analysis_date: str,
        is_fairness_aware: bool,
        alert_severity: Optional[str],
        alert_triggered: bool,
    ) -> None:
        """
        Store fairness metrics in database.

        Args:
            db: Database session
            vacancy_id: JobVacancy UUID
            demographic_group: Demographic attribute name
            group_data: Raw group data
            group_metrics: Calculated metrics per group
            reference_rate: Reference group selection rate
            model_version: Model version analyzed
            analysis_date: Analysis date
            is_fairness_aware: Whether fairness-aware ranking was used
            alert_severity: Alert severity level
            alert_triggered: Whether alert was triggered
        """
        # Calculate aggregate disparate impact (minimum across groups)
        disparate_impact_values = [
            m["disparate_impact_ratio"]
            for m in group_metrics.values()
            if m["disparate_impact_ratio"] > 0
        ]
        aggregate_di = min(disparate_impact_values) if disparate_impact_values else 1.0

        # Calculate aggregate statistical parity (maximum absolute difference)
        stat_parity_values = [
            abs(m["statistical_parity_difference"])
            for m in group_metrics.values()
        ]
        aggregate_sp = max(stat_parity_values) if stat_parity_values else 0.0

        # Total sample size
        total_sample_size = sum(data["total"] for data in group_data.values())

        # Build group metrics JSON
        group_metrics_json = {
            group: {
                "sample_size": metrics["sample_size"],
                "selection_rate": metrics["selection_rate"],
                "disparate_impact_ratio": metrics["disparate_impact_ratio"],
            }
            for group, metrics in group_metrics.items()
        }

        # Create FairnessMetrics record
        fairness_metric = FairnessMetrics(
            vacancy_id=vacancy_id,
            model_version_id=model_version,
            analysis_date=analysis_date,
            demographic_group=demographic_group,
            disparate_impact_ratio=aggregate_di,
            statistical_parity_difference=aggregate_sp,
            overall_selection_rate=reference_rate,
            group_sample_size=len(group_data),
            total_sample_size=total_sample_size,
            alert_threshold=self.calculator.disparate_impact_threshold,
            alert_triggered=alert_triggered,
            alert_severity=alert_severity,
            group_metrics=group_metrics_json,
            mitigation_suggested=group_metrics.get(
                list(group_metrics.keys())[0], {}
            ).get("mitigation_suggested") if group_metrics else None,
            is_fairness_aware=is_fairness_aware,
            analysis_metadata={
                "calculator_version": "1.0.0",
                "reference_threshold": "50th_percentile",
                "min_sample_size": MIN_SAMPLE_SIZE,
            },
        )
        db.add(fairness_metric)
        await db.flush()

        # Create alert if triggered
        if alert_triggered and alert_severity:
            await self._create_fairness_alert(
                db,
                fairness_metric.id,
                vacancy_id,
                demographic_group,
                aggregate_di,
                alert_severity,
            )

        await db.commit()

    async def _create_fairness_alert(
        self,
        db: AsyncSession,
        fairness_metric_id: UUID,
        vacancy_id: UUID,
        demographic_group: str,
        actual_value: float,
        severity: str,
    ) -> None:
        """
        Create a fairness alert when bias threshold is exceeded.

        Args:
            db: Database session
            fairness_metric_id: FairnessMetrics UUID
            vacancy_id: JobVacancy UUID
            demographic_group: Demographic group with bias
            actual_value: Actual metric value that triggered alert
            severity: Alert severity level
        """
        alert_type = "disparate_impact"
        threshold_value = self.calculator.disparate_impact_threshold

        message = (
            f"Fairness alert: {demographic_group} shows disparate impact ratio of "
            f"{actual_value:.4f}, below threshold of {threshold_value:.2f}. "
            f"Severity: {severity}"
        )

        alert = FairnessAlert(
            fairness_metric_id=fairness_metric_id,
            vacancy_id=vacancy_id,
            alert_type=alert_type,
            severity=severity,
            status="active",
            message=message,
            threshold_value=threshold_value,
            actual_value=actual_value,
            alert_metadata={
                "demographic_group": demographic_group,
                "recommendation": "Review ranking model and consider retraining",
            },
        )
        db.add(alert)

    def _severity_rank(self, severity: str) -> int:
        """Get numeric rank for severity comparison."""
        ranks = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return ranks.get(severity, 0)

    async def get_fairness_report(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        analysis_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive fairness report for a vacancy.

        Args:
            db: Database session
            vacancy_id: JobVacancy UUID
            analysis_date: Optional date filter (default: latest)

        Returns:
            Comprehensive fairness report with metrics, alerts, and recommendations
        """
        # Build query for fairness metrics
        metrics_query = select(FairnessMetrics).where(
            FairnessMetrics.vacancy_id == vacancy_id
        )

        if analysis_date:
            metrics_query = metrics_query.where(
                FairnessMetrics.analysis_date == analysis_date
            )

        metrics_query = metrics_query.order_by(FairnessMetrics.created_at.desc())
        metrics_result = await db.execute(metrics_query)
        metrics = metrics_result.scalars().all()

        if not metrics:
            return {
                "vacancy_id": str(vacancy_id),
                "status": "no_data",
                "message": "No fairness metrics available for this vacancy",
            }

        # Get related alerts
        metric_ids = [m.id for m in metrics]
        alerts_query = select(FairnessAlert).where(
            FairnessAlert.fairness_metric_id.in_(metric_ids)
        )
        alerts_result = await db.execute(alerts_query)
        alerts = alerts_result.scalars().all()

        # Build report
        report = {
            "vacancy_id": str(vacancy_id),
            "analysis_date": analysis_date or metrics[0].analysis_date,
            "summary": {
                "total_metrics": len(metrics),
                "active_alerts": sum(1 for a in alerts if a.status == "active"),
                "demographics_analyzed": list(set(m.demographic_group for m in metrics)),
            },
            "metrics_by_demographic": {},
            "alerts": [],
            "recommendations": [],
        }

        # Group metrics by demographic attribute
        for metric in metrics:
            attr = metric.demographic_group
            report["metrics_by_demographic"][attr] = {
                "disparate_impact_ratio": float(metric.disparate_impact_ratio or 0),
                "statistical_parity_difference": float(metric.statistical_parity_difference or 0),
                "overall_selection_rate": float(metric.overall_selection_rate or 0),
                "sample_size": metric.total_sample_size,
                "alert_triggered": metric.alert_triggered,
                "alert_severity": metric.alert_severity,
                "is_fairness_aware": metric.is_fairness_aware,
                "group_metrics": metric.group_metrics,
            }

            # Collect recommendations
            if metric.mitigation_suggested:
                report["recommendations"].append({
                    "demographic": attr,
                    "suggestion": metric.mitigation_suggested,
                    "severity": metric.alert_severity,
                })

        # Add alerts
        for alert in alerts:
            report["alerts"].append({
                "id": str(alert.id),
                "type": alert.alert_type,
                "severity": alert.severity,
                "status": alert.status,
                "message": alert.message,
                "threshold_value": float(alert.threshold_value or 0),
                "actual_value": float(alert.actual_value or 0),
                "created_at": alert.created_at,
            })

        # Sort recommendations by severity
        severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        report["recommendations"].sort(
            key=lambda x: severity_rank.get(x["severity"], 0),
            reverse=True,
        )

        return report


# Global service instance
_fairness_calculator: Optional[FairnessCalculator] = None


def get_fairness_calculator() -> FairnessCalculator:
    """Get or create global fairness calculator instance."""
    global _fairness_calculator
    if _fairness_calculator is None:
        _fairness_calculator = FairnessCalculator()
    return _fairness_calculator
