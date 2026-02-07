"""
Equity Analyzer for Internal Pay Equity Analysis

This module provides internal equity analysis to identify pay disparities
across demographic groups and ensure fair compensation practices. It calculates:
- Pay gap analysis between demographic groups
- Compa-ratio analysis (salary vs midpoint comparison)
- Internal equity alerts when thresholds are exceeded
- Trend analysis for salary progression

Used for compliance monitoring (EEOC, pay equity laws) and ensuring fair pay practices.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from sqlalchemy import and_, func as sql_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    CandidateRank,
    DemographicInference,
    JobVacancy,
    SalaryHistory,
)

logger = logging.getLogger(__name__)

# Equity threshold constants
DEFAULT_PAY_GAP_THRESHOLD = 0.05  # 5% pay gap triggers alert
DEFAULT_COMPA_RATIO_MIN = 0.80  # 80% of midpoint is minimum fair
DEFAULT_COMPA_RATIO_MAX = 1.20  # 120% of midpoint is maximum fair
MIN_SAMPLE_SIZE = 3  # Minimum samples per group for reliable analysis


class EquityMetricsCalculator:
    """
    Calculate internal equity metrics for pay disparity detection.

    Computes standard equity metrics from salary data to detect
    potential pay bias across demographic groups within the organization.
    """

    # Demographic groups to analyze
    DEMOGRAPHIC_ATTRIBUTES = {
        "gender": ["male", "female", "non_binary"],
        "age_group": ["under_25", "25_34", "35_44", "45_54", "55_64", "65_plus"],
        "ethnicity": ["asian", "hispanic", "black_african", "white"],
    }

    def __init__(
        self,
        pay_gap_threshold: float = DEFAULT_PAY_GAP_THRESHOLD,
        compa_ratio_min: float = DEFAULT_COMPA_RATIO_MIN,
        compa_ratio_max: float = DEFAULT_COMPA_RATIO_MAX,
    ):
        """
        Initialize the equity calculator.

        Args:
            pay_gap_threshold: Maximum acceptable pay gap as decimal (default 0.05 for 5%)
            compa_ratio_min: Minimum acceptable compa-ratio (default 0.80)
            compa_ratio_max: Maximum acceptable compa-ratio (default 1.20)
        """
        self.pay_gap_threshold = pay_gap_threshold
        self.compa_ratio_min = compa_ratio_min
        self.compa_ratio_max = compa_ratio_max

    def calculate_pay_gap(
        self,
        group_mean_salary: float,
        reference_mean_salary: float,
    ) -> Tuple[float, bool]:
        """
        Calculate pay gap ratio between demographic groups.

        Pay Gap = (reference_mean - group_mean) / reference_mean

        Args:
            group_mean_salary: Mean salary for the demographic group
            reference_mean_salary: Mean salary for reference group

        Returns:
            Tuple of (gap_ratio, is_fair)
            - gap_ratio: Pay gap ratio (0 = fair, positive = group paid less)
            - is_fair: Whether gap is within threshold
        """
        if reference_mean_salary == 0:
            # Avoid division by zero
            return 0.0, group_mean_salary == 0

        gap_ratio = (reference_mean_salary - group_mean_salary) / reference_mean_salary

        # We care about absolute gap - reverse bias exists too
        is_fair = abs(gap_ratio) <= self.pay_gap_threshold

        return gap_ratio, is_fair

    def calculate_compa_ratio(
        self,
        individual_salary: float,
        midpoint_salary: float,
    ) -> Tuple[float, bool]:
        """
        Calculate compa-ratio (individual salary vs midpoint).

        Compa-Ratio = individual_salary / midpoint_salary

        Args:
            individual_salary: Individual's annual salary
            midpoint_salary: Midpoint salary for the role/level

        Returns:
            Tuple of (compa_ratio, is_within_range)
            - compa_ratio: Ratio of salary to midpoint (1.0 = at midpoint)
            - is_within_range: Whether ratio is within acceptable range
        """
        if midpoint_salary == 0:
            return 0.0, False

        compa_ratio = individual_salary / midpoint_salary

        is_within_range = self.compa_ratio_min <= compa_ratio <= self.compa_ratio_max

        return compa_ratio, is_within_range

    def calculate_mean_salary(
        self,
        salaries: List[float],
    ) -> float:
        """
        Calculate mean salary for a group.

        Args:
            salaries: List of annual salaries

        Returns:
            Mean salary or 0 if list is empty
        """
        if not salaries:
            return 0.0

        return np.mean(salaries)

    def calculate_median_salary(
        self,
        salaries: List[float],
    ) -> float:
        """
        Calculate median salary for a group.

        Args:
            salaries: List of annual salaries

        Returns:
            Median salary or 0 if list is empty
        """
        if not salaries:
            return 0.0

        return np.median(salaries)

    def determine_alert_severity(
        self,
        pay_gap_ratio: float,
        compa_ratio: float,
    ) -> Optional[str]:
        """
        Determine alert severity based on metric values.

        Args:
            pay_gap_ratio: Pay gap ratio (can be negative)
            compa_ratio: Compa-ratio value

        Returns:
            Severity level: low, medium, high, critical or None
        """
        # Critical: very high pay gap (> 15%) or extreme compa-ratio
        if abs(pay_gap_ratio) > 0.15 or compa_ratio < 0.7 or compa_ratio > 1.4:
            return "critical"

        # High: high pay gap (> 10%) or concerning compa-ratio
        if abs(pay_gap_ratio) > 0.10 or compa_ratio < 0.75 or compa_ratio > 1.35:
            return "high"

        # Medium: pay gap exceeds threshold
        if abs(pay_gap_ratio) > self.pay_gap_threshold:
            return "medium"

        # Low: compa-ratio out of range but pay gap acceptable
        if not (self.compa_ratio_min <= compa_ratio <= self.compa_ratio_max):
            return "low"

        return None

    def generate_mitigation_suggestions(
        self,
        demographic_group: str,
        pay_gap_ratio: float,
        compa_ratio: float,
        is_underpaid: bool,
    ) -> Optional[str]:
        """
        Generate actionable mitigation suggestions based on equity issues detected.

        Args:
            demographic_group: The demographic group showing equity issues
            pay_gap_ratio: Calculated pay gap ratio
            compa_ratio: Calculated compa-ratio
            is_underpaid: Whether the group is underpaid (vs overpaid)

        Returns:
            Mitigation suggestions string or None
        """
        if abs(pay_gap_ratio) <= self.pay_gap_threshold:
            # Check compa-ratio instead
            if not (self.compa_ratio_min <= compa_ratio <= self.compa_ratio_max):
                suggestions = []
                suggestions.append(f"Compa-ratio concern for {demographic_group}")

                if compa_ratio < self.compa_ratio_min:
                    suggestions.append(f"- Salary is {self.compa_ratio_min - compa_ratio:.1%} below minimum range")
                    suggestions.append("- Consider salary adjustment to bring within range")
                    suggestions.append("- Review market benchmarks for this role")
                else:
                    suggestions.append(f"- Salary is {compa_ratio - self.compa_ratio_max:.1%} above maximum range")
                    suggestions.append("- Verify role and level alignment")
                    suggestions.append("- Review if promotion is warranted")

                return "\n".join(suggestions)

            return None

        suggestions = []

        # General recommendation
        if is_underpaid:
            suggestions.append(f"Pay equity concern: {demographic_group} appears underpaid")
        else:
            suggestions.append(f"Pay equity concern: {demographic_group} appears overpaid")

        # Pay gap specific
        if abs(pay_gap_ratio) > 0.15:
            suggestions.append("- Significant pay gap detected: Immediate review recommended")
            suggestions.append("- Conduct compensation audit for this group")
            suggestions.append("- Consider equitable salary adjustments")
        elif abs(pay_gap_ratio) > 0.10:
            suggestions.append("- Moderate pay gap detected: Schedule review")
            suggestions.append("- Analyze factors contributing to gap")
            suggestions.append("- Plan corrective adjustments if needed")

        # Compa-ratio specific
        if compa_ratio < self.compa_ratio_min:
            suggestions.append(f"- Compa-ratio of {compa_ratio:.2f} is below minimum ({self.compa_ratio_min})")
        elif compa_ratio > self.compa_ratio_max:
            suggestions.append(f"- Compa-ratio of {compa_ratio:.2f} exceeds maximum ({self.compa_ratio_max})")

        # General recommendations
        suggestions.append("- Document business rationale for any pay differences")
        suggestions.append("- Ensure consistent application of compensation policies")
        suggestions.append("- Monitor trends over time")

        return "\n".join(suggestions)


class EquityAnalyzer:
    """
    Main service for internal equity analysis and monitoring.

    Coordinates salary data retrieval, equity metrics computation, and
    alert generation for pay disparity detection.
    """

    def __init__(
        self,
        pay_gap_threshold: float = DEFAULT_PAY_GAP_THRESHOLD,
        compa_ratio_min: float = DEFAULT_COMPA_RATIO_MIN,
        compa_ratio_max: float = DEFAULT_COMPA_RATIO_MAX,
    ):
        """
        Initialize the equity analyzer.

        Args:
            pay_gap_threshold: Maximum acceptable pay gap ratio
            compa_ratio_min: Minimum acceptable compa-ratio
            compa_ratio_max: Maximum acceptable compa-ratio
        """
        self.calculator = EquityMetricsCalculator(
            pay_gap_threshold,
            compa_ratio_min,
            compa_ratio_max,
        )

    async def analyze_vacancy_equity(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        analysis_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze internal equity metrics for candidates considered for a vacancy.

        Args:
            db: Database session
            vacancy_id: JobVacancy UUID to analyze
            analysis_date: Date of analysis (default: today)

        Returns:
            Dictionary with equity metrics summary by demographic attribute
        """
        if analysis_date is None:
            analysis_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Analyzing equity for vacancy {vacancy_id}")

        # Get vacancy details
        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_id)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        if not vacancy:
            return {
                "vacancy_id": str(vacancy_id),
                "analysis_date": analysis_date,
                "error": "vacancy_not_found",
            }

        # Get all candidate rankings for this vacancy
        rankings_query = select(CandidateRank).where(
            CandidateRank.vacancy_id == vacancy_id
        )
        rankings_result = await db.execute(rankings_query)
        rankings = rankings_result.scalars().all()

        if len(rankings) < MIN_SAMPLE_SIZE:
            logger.warning(
                f"Insufficient sample size for vacancy {vacancy_id}: "
                f"{len(rankings)} rankings (need at least {MIN_SAMPLE_SIZE})"
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

        # Get salary history for all ranked resumes
        salary_query = select(SalaryHistory).where(
            and_(
                SalaryHistory.resume_id.in_(resume_ids),
                SalaryHistory.salary_type == "current",
            )
        )
        salary_result = await db.execute(salary_query)
        salary_records = salary_result.scalars().all()
        salaries = {s.resume_id: s for s in salary_records}

        # Build salary data with demographics
        salary_data = []
        for ranking in rankings:
            demo = demographics.get(ranking.resume_id)
            salary = salaries.get(ranking.resume_id)

            if demo and salary:
                total_comp = salary.calculate_total_compensation()
                if total_comp:
                    salary_data.append({
                        "resume_id": ranking.resume_id,
                        "salary": total_comp,
                        "currency": salary.currency,
                        "gender": demo.inferred_gender,
                        "age_group": demo.inferred_age_group,
                        "ethnicity": demo.inferred_ethnicity,
                    })

        if len(salary_data) < MIN_SAMPLE_SIZE:
            logger.warning(
                f"Insufficient salary data for vacancy {vacancy_id}: "
                f"{len(salary_data)} with salary and demographics"
            )
            return {
                "vacancy_id": str(vacancy_id),
                "analysis_date": analysis_date,
                "error": "insufficient_salary_data",
                "records_with_data": len(salary_data),
            }

        # Calculate equity metrics for each demographic attribute
        summary = {
            "vacancy_id": str(vacancy_id),
            "vacancy_title": vacancy.title,
            "analysis_date": analysis_date,
            "total_candidates": len(salary_data),
            "median_salary": self.calculator.calculate_median_salary(
                [d["salary"] for d in salary_data]
            ),
            "attributes_analyzed": {},
        }

        for attribute, groups in self.calculator.DEMOGRAPHIC_ATTRIBUTES.items():
            metrics = await self._calculate_attribute_equity(
                db,
                vacancy_id,
                salary_data,
                attribute,
                groups,
                analysis_date,
            )
            summary["attributes_analyzed"][attribute] = metrics

        return summary

    async def _calculate_attribute_equity(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        salary_data: List[Dict[str, Any]],
        attribute: str,
        groups: List[str],
        analysis_date: str,
    ) -> Dict[str, Any]:
        """
        Calculate equity metrics for a specific demographic attribute.

        Args:
            db: Database session
            vacancy_id: JobVacancy UUID
            salary_data: List of salary records with demographics
            attribute: Demographic attribute (gender, age_group, ethnicity)
            groups: List of groups in this attribute
            analysis_date: Analysis date string

        Returns:
            Dictionary with metrics for each group in the attribute
        """
        # Group salaries by demographic value
        group_data = {}
        for record in salary_data:
            group_value = record.get(attribute)
            if not group_value or group_value not in groups:
                continue

            if group_value not in group_data:
                group_data[group_value] = {
                    "salaries": [],
                    "count": 0,
                }

            group_data[group_value]["salaries"].append(record["salary"])
            group_data[group_value]["count"] += 1

        # Calculate metrics for each group
        group_metrics = {}
        reference_mean = None

        # Find reference group (largest group or highest mean salary)
        for group_value, data in group_data.items():
            if data["count"] >= MIN_SAMPLE_SIZE:
                mean_salary = self.calculator.calculate_mean_salary(data["salaries"])
                if reference_mean is None or mean_salary > reference_mean:
                    reference_mean = mean_salary

        if reference_mean is None:
            # No group meets minimum sample size
            return {"error": "insufficient_group_sizes"}

        # Calculate overall midpoint for compa-ratio
        all_salaries = [s for d in salary_data for s in [d["salary"]]]
        midpoint_salary = self.calculator.calculate_median_salary(all_salaries)

        # Calculate metrics for all groups
        alert_triggered = False
        max_severity = None

        for group_value, data in group_data.items():
            if data["count"] < MIN_SAMPLE_SIZE:
                # Skip groups with insufficient sample size
                continue

            group_mean = self.calculator.calculate_mean_salary(data["salaries"])
            group_median = self.calculator.calculate_median_salary(data["salaries"])

            # Calculate pay gap
            pay_gap, gap_fair = self.calculator.calculate_pay_gap(
                group_mean, reference_mean
            )

            # Calculate compa-ratio using median salary
            compa_ratio, compa_fair = self.calculator.calculate_compa_ratio(
                group_median, midpoint_salary
            )

            is_fair = gap_fair and compa_fair
            is_underpaid = pay_gap > 0  # Positive gap means group paid less

            severity = self.calculator.determine_alert_severity(
                pay_gap, compa_ratio
            )

            if severity and (not max_severity or self._severity_rank(severity) > self._severity_rank(max_severity)):
                max_severity = severity
                alert_triggered = True

            mitigation = self.calculator.generate_mitigation_suggestions(
                f"{attribute}={group_value}",
                pay_gap,
                compa_ratio,
                is_underpaid,
            )

            group_metrics[group_value] = {
                "sample_size": data["count"],
                "mean_salary": round(group_mean, 2),
                "median_salary": round(group_median, 2),
                "pay_gap_ratio": round(pay_gap, 4),
                "compa_ratio": round(compa_ratio, 4),
                "is_fair": is_fair,
                "is_underpaid": is_underpaid,
                "alert_severity": severity,
                "mitigation_suggested": mitigation,
            }

        return {
            "groups": group_metrics,
            "reference_mean_salary": round(reference_mean, 2),
            "midpoint_salary": round(midpoint_salary, 2),
            "alert_triggered": alert_triggered,
            "max_severity": max_severity,
        }

    def _severity_rank(self, severity: str) -> int:
        """Get numeric rank for severity comparison."""
        ranks = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return ranks.get(severity, 0)

    async def get_equity_report(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        analysis_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive equity report for a vacancy.

        Args:
            db: Database session
            vacancy_id: JobVacancy UUID
            analysis_date: Optional date filter (default: latest)

        Returns:
            Comprehensive equity report with metrics, alerts, and recommendations
        """
        # Analyze equity for this vacancy
        analysis = await self.analyze_vacancy_equity(
            db,
            vacancy_id,
            analysis_date,
        )

        if "error" in analysis:
            return {
                "vacancy_id": str(vacancy_id),
                "status": "error",
                "message": analysis.get("error"),
                "details": analysis,
            }

        # Build report
        report = {
            "vacancy_id": str(vacancy_id),
            "vacancy_title": analysis.get("vacancy_title"),
            "analysis_date": analysis_date or analysis["analysis_date"],
            "summary": {
                "total_candidates": analysis["total_candidates"],
                "median_salary": analysis["median_salary"],
                "attributes_analyzed": list(analysis["attributes_analyzed"].keys()),
                "alerts_triggered": [],
            },
            "metrics_by_demographic": {},
            "recommendations": [],
        }

        # Group metrics by demographic attribute
        for attr, attr_data in analysis["attributes_analyzed"].items():
            if "error" in attr_data:
                continue

            report["metrics_by_demographic"][attr] = {
                "groups": attr_data["groups"],
                "reference_mean_salary": attr_data["reference_mean_salary"],
                "midpoint_salary": attr_data["midpoint_salary"],
                "alert_triggered": attr_data["alert_triggered"],
                "max_severity": attr_data["max_severity"],
            }

            # Track alerts
            if attr_data["alert_triggered"] and attr_data["max_severity"]:
                report["summary"]["alerts_triggered"].append({
                    "attribute": attr,
                    "severity": attr_data["max_severity"],
                })

            # Collect recommendations from groups
            for group_name, group_metrics in attr_data["groups"].items():
                if group_metrics.get("mitigation_suggested"):
                    report["recommendations"].append({
                        "demographic": f"{attr}={group_name}",
                        "suggestion": group_metrics["mitigation_suggested"],
                        "severity": group_metrics["alert_severity"],
                        "is_underpaid": group_metrics["is_underpaid"],
                        "pay_gap": group_metrics["pay_gap_ratio"],
                        "compa_ratio": group_metrics["compa_ratio"],
                    })

        # Sort recommendations by severity
        severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        report["recommendations"].sort(
            key=lambda x: severity_rank.get(x["severity"], 0),
            reverse=True,
        )

        # Overall status
        if not report["summary"]["alerts_triggered"]:
            report["status"] = "fair"
        elif any(a["severity"] in ["critical", "high"] for a in report["summary"]["alerts_triggered"]):
            report["status"] = "concerning"
        else:
            report["status"] = "review_needed"

        return report


# Global service instance
_equity_analyzer: Optional[EquityAnalyzer] = None


def get_equity_analyzer() -> EquityAnalyzer:
    """Get or create global equity analyzer instance."""
    global _equity_analyzer
    if _equity_analyzer is None:
        _equity_analyzer = EquityAnalyzer()
    return _equity_analyzer
