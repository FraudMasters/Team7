"""
Tests for fairness monitoring tasks.

This module tests fairness monitoring Celery tasks including:
- Fairness metrics calculation
- Demographic outcome comparison
- Violation detection
- Alert formatting and sending
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID

from tasks.fairness_monitoring import (
    calculate_fairness_metrics,
    detect_fairness_violation,
    compare_demographic_outcomes,
    format_fairness_alert_email,
)
from models.fairness_metrics import FairnessMetrics, FairnessAlert
from models.job_vacancy import JobVacancy
from models.candidate_rank import CandidateRank
from models.demographic_inference import DemographicInference
from models.resume import Resume


class TestCalculateFairnessMetrics:
    """Tests for calculate_fairness_metrics function."""

    @pytest.mark.asyncio
    async def test_calculate_metrics_no_data(self, async_db):
        """Test calculating metrics when no data exists."""
        vacancy_id = str(uuid4())

        result = calculate_fairness_metrics(vacancy_id, "gender")

        assert result["vacancy_id"] == vacancy_id
        assert result["demographic_group"] == "gender"
        assert result["latest_metrics"] is None
        assert result["metric_count"] == 0
        assert result["alert_triggered"] is False

    @pytest.mark.asyncio
    async def test_calculate_metrics_with_data(self, async_db):
        """Test calculating metrics when data exists."""
        # Create test vacancy
        vacancy = JobVacancy(
            id=uuid4(),
            job_title="Software Engineer",
            status="active",
            company_name="Test Corp",
        )
        async_db.add(vacancy)

        # Create fairness metrics
        metrics = FairnessMetrics(
            id=uuid4(),
            vacancy_id=vacancy.id,
            demographic_group="gender",
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            disparate_impact_ratio=0.85,
            statistical_parity_difference=0.05,
            overall_selection_rate=0.45,
            group_sample_size=2,
            total_sample_size=100,
            alert_threshold=0.8,
            alert_triggered=False,
            alert_severity=None,
            group_metrics={
                "male": {"selection_rate": 0.48, "sample_size": 50},
                "female": {"selection_rate": 0.42, "sample_size": 50},
            },
            is_fairness_aware=False,
        )
        async_db.add(metrics)
        await async_db.commit()

        # Calculate metrics
        result = calculate_fairness_metrics(str(vacancy.id), "gender")

        assert result["vacancy_id"] == str(vacancy.id)
        assert result["demographic_group"] == "gender"
        assert result["latest_metrics"]["disparate_impact_ratio"] == 0.85
        assert result["latest_metrics"]["statistical_parity_difference"] == 0.05
        assert result["latest_metrics"]["overall_selection_rate"] == 0.45
        assert result["group_metrics"]["male"]["selection_rate"] == 0.48
        assert result["group_metrics"]["female"]["selection_rate"] == 0.42
        assert result["metric_count"] == 1
        assert result["alert_triggered"] is False

    @pytest.mark.asyncio
    async def test_calculate_metrics_with_alert(self, async_db):
        """Test calculating metrics when alert is triggered."""
        # Create test vacancy
        vacancy = JobVacancy(
            id=uuid4(),
            job_title="Software Engineer",
            status="active",
            company_name="Test Corp",
        )
        async_db.add(vacancy)

        # Create fairness metrics with violation
        metrics = FairnessMetrics(
            id=uuid4(),
            vacancy_id=vacancy.id,
            demographic_group="gender",
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            disparate_impact_ratio=0.65,  # Below threshold
            statistical_parity_difference=0.18,  # Above threshold
            overall_selection_rate=0.45,
            group_sample_size=2,
            total_sample_size=100,
            alert_threshold=0.8,
            alert_triggered=True,
            alert_severity="high",
            group_metrics={
                "male": {"selection_rate": 0.54, "sample_size": 50},
                "female": {"selection_rate": 0.36, "sample_size": 50},
            },
            is_fairness_aware=False,
        )
        async_db.add(metrics)
        await async_db.commit()

        # Calculate metrics
        result = calculate_fairness_metrics(str(vacancy.id), "gender")

        assert result["alert_triggered"] is True
        assert result["alert_severity"] == "high"
        assert result["latest_metrics"]["disparate_impact_ratio"] == 0.65


class TestDetectFairnessViolation:
    """Tests for detect_fairness_violation function."""

    def test_detect_no_violation(self):
        """Test detection when no violation exists."""
        current_metrics = {
            "disparate_impact_ratio": 0.92,
            "statistical_parity_difference": 0.03,
        }

        result = detect_fairness_violation(current_metrics)

        assert result["is_violation"] is False
        assert result["severity"] is None
        assert len(result["violated_metrics"]) == 0

    def test_detect_disparate_impact_violation(self):
        """Test detection of disparate impact violation."""
        current_metrics = {
            "disparate_impact_ratio": 0.72,  # Below 0.8 threshold
            "statistical_parity_difference": 0.05,
        }

        result = detect_fairness_violation(current_metrics)

        assert result["is_violation"] is True
        assert result["severity"] == "medium"
        assert "disparate_impact" in result["violated_metrics"]
        assert result["violation_details"]["disparate_impact"]["violated"] is True

    def test_detect_statistical_parity_violation(self):
        """Test detection of statistical parity violation."""
        current_metrics = {
            "disparate_impact_ratio": 0.85,
            "statistical_parity_difference": 0.15,  # Above 0.1 threshold
        }

        result = detect_fairness_violation(current_metrics)

        assert result["is_violation"] is True
        assert result["severity"] == "medium"
        assert "statistical_parity" in result["violated_metrics"]

    def test_detect_critical_violation(self):
        """Test detection of critical severity violation."""
        current_metrics = {
            "disparate_impact_ratio": 0.45,  # Very low
            "statistical_parity_difference": 0.28,  # Very high
        }

        result = detect_fairness_violation(current_metrics)

        assert result["is_violation"] is True
        assert result["severity"] == "critical"
        assert "disparate_impact" in result["violated_metrics"]
        assert "statistical_parity" in result["violated_metrics"]

    def test_detect_high_severity_violation(self):
        """Test detection of high severity violation."""
        current_metrics = {
            "disparate_impact_ratio": 0.62,  # Below 0.65
            "statistical_parity_difference": 0.22,  # Above 0.2
        }

        result = detect_fairness_violation(current_metrics)

        assert result["is_violation"] is True
        assert result["severity"] == "high"


class TestCompareDemographicOutcomes:
    """Tests for compare_demographic_outcomes function."""

    @pytest.mark.asyncio
    async def test_compare_no_data(self, async_db):
        """Test comparison when no data exists."""
        vacancy_id = str(uuid4())
        demographic_groups = ["gender", "age_group"]

        result = compare_demographic_outcomes(vacancy_id, demographic_groups)

        assert result["vacancy_id"] == vacancy_id
        assert result["demographics_compared"] == demographic_groups
        assert result["group_selection_rates"] == {}
        assert result["max_disparity"] == 0.0
        assert result["groups_with_violations"] == []
        assert result["comparison_count"] == 2

    @pytest.mark.asyncio
    async def test_compare_with_data(self, async_db):
        """Test comparison with existing metrics."""
        # Create test vacancy
        vacancy = JobVacancy(
            id=uuid4(),
            job_title="Software Engineer",
            status="active",
            company_name="Test Corp",
        )
        async_db.add(vacancy)

        # Create metrics for gender
        gender_metrics = FairnessMetrics(
            id=uuid4(),
            vacancy_id=vacancy.id,
            demographic_group="gender",
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            disparate_impact_ratio=0.85,
            statistical_parity_difference=0.05,
            overall_selection_rate=0.45,
            group_sample_size=2,
            total_sample_size=100,
            alert_triggered=False,
            group_metrics={
                "male": {"selection_rate": 0.48, "sample_size": 50},
                "female": {"selection_rate": 0.42, "sample_size": 50},
            },
        )
        async_db.add(gender_metrics)

        # Create metrics for age_group
        age_metrics = FairnessMetrics(
            id=uuid4(),
            vacancy_id=vacancy.id,
            demographic_group="age_group",
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            disparate_impact_ratio=0.75,
            statistical_parity_difference=0.12,
            overall_selection_rate=0.45,
            group_sample_size=3,
            total_sample_size=100,
            alert_triggered=True,
            group_metrics={
                "under_25": {"selection_rate": 0.40, "sample_size": 30},
                "25_34": {"selection_rate": 0.46, "sample_size": 40},
                "35_44": {"selection_rate": 0.48, "sample_size": 30},
            },
        )
        async_db.add(age_metrics)
        await async_db.commit()

        # Compare outcomes
        result = compare_demographic_outcomes(
            str(vacancy.id),
            ["gender", "age_group"]
        )

        assert result["vacancy_id"] == str(vacancy.id)
        assert "gender" in result["group_selection_rates"]
        assert "age_group" in result["group_selection_rates"]
        assert result["group_selection_rates"]["gender"]["male"] == 0.48
        assert result["group_selection_rates"]["gender"]["female"] == 0.42
        assert result["max_disparity"] > 0
        assert "age_group" in result["groups_with_violations"]
        assert "gender" not in result["groups_with_violations"]


class TestFormatFairnessAlertEmail:
    """Tests for format_fairness_alert_email function."""

    def test_format_email_critical_severity(self):
        """Test email formatting for critical severity alert."""
        violation_details = {
            "demographic_group": "gender",
            "violation": {
                "is_violation": True,
                "severity": "critical",
                "violated_metrics": ["disparate_impact", "statistical_parity"],
                "violation_details": {
                    "disparate_impact": {
                        "current": 0.45,
                        "threshold": 0.8,
                        "delta": -0.35,
                        "violated": True,
                    },
                    "statistical_parity": {
                        "current": 0.28,
                        "threshold": 0.1,
                        "delta": 0.18,
                        "violated": True,
                    },
                },
            },
            "current_metrics": {
                "disparate_impact_ratio": 0.45,
                "statistical_parity_difference": 0.28,
                "overall_selection_rate": 0.45,
            },
            "detected_at": "2026-03-21T10:00:00",
        }

        result = format_fairness_alert_email("vacancy-123", violation_details)

        assert "subject" in result
        assert "body" in result
        assert "priority" in result
        assert "🚨" in result["subject"]
        assert "CRITICAL" in result["subject"]
        assert "gender" in result["subject"]
        assert "IMMEDIATE ACTION REQUIRED" in result["body"]
        assert result["priority"] == "high"

    def test_format_email_high_severity(self):
        """Test email formatting for high severity alert."""
        violation_details = {
            "demographic_group": "age_group",
            "violation": {
                "is_violation": True,
                "severity": "high",
                "violated_metrics": ["disparate_impact"],
                "violation_details": {
                    "disparate_impact": {
                        "current": 0.62,
                        "threshold": 0.8,
                        "delta": -0.18,
                        "violated": True,
                    },
                },
            },
            "current_metrics": {
                "disparate_impact_ratio": 0.62,
            },
            "detected_at": "2026-03-21T10:00:00",
        }

        result = format_fairness_alert_email("vacancy-123", violation_details)

        assert "⚠️" in result["subject"]
        assert "HIGH" in result["subject"]
        assert "age_group" in result["subject"]
        assert result["priority"] == "high"

    def test_format_email_medium_severity(self):
        """Test email formatting for medium severity alert."""
        violation_details = {
            "demographic_group": "ethnicity",
            "violation": {
                "is_violation": True,
                "severity": "medium",
                "violated_metrics": ["disparate_impact"],
                "violation_details": {},
            },
            "current_metrics": {},
            "detected_at": "2026-03-21T10:00:00",
        }

        result = format_fairness_alert_email("vacancy-123", violation_details)

        assert "⚡" in result["subject"]
        assert "MEDIUM" in result["subject"]
        assert result["priority"] == "normal"

    def test_format_email_low_severity(self):
        """Test email formatting for low severity alert."""
        violation_details = {
            "demographic_group": "gender",
            "violation": {
                "is_violation": True,
                "severity": "low",
                "violated_metrics": ["statistical_parity"],
                "violation_details": {},
            },
            "current_metrics": {},
            "detected_at": "2026-03-21T10:00:00",
        }

        result = format_fairness_alert_email("vacancy-123", violation_details)

        assert "ℹ️" in result["subject"]
        assert "LOW" in result["subject"]
        assert result["priority"] == "normal"
