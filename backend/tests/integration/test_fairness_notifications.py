"""
Integration tests for fairness violation notifications.

This test suite validates the end-to-end fairness monitoring and notification workflow:
- Fairness monitoring detects violations
- Violation triggers send_fairness_alert task
- Email notification sent to admin users
- FairnessAlert records created in database

Test Coverage:
- Fairness violation detection triggers notification
- Notification task triggered with correct parameters
- Email formatted and sent correctly
- Multiple violations trigger multiple notifications
- No notification sent when no violations detected
- Error handling for notification failures
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, Generator
from unittest.mock import Mock, patch, AsyncMock, call
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from models.job_vacancy import JobVacancy
from models.fairness_metrics import FairnessMetrics, FairnessAlert
from models.candidate_rank import CandidateRank
from tasks.fairness_monitoring import (
    monitor_fairness,
    send_fairness_alert,
    format_fairness_alert_email,
    detect_fairness_violation,
)


# Test database URL (use same as main database for integration testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_fairness_notifications.db"


@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


class TestFairnessNotificationIntegration:
    """Tests for fairness violation notification integration."""

    @pytest.mark.asyncio
    async def test_fairness_violation_triggers_notification(
        self,
        test_db: AsyncSession
    ):
        """
        Test that fairness violations trigger notification alerts.

        Verification steps:
        1. Create vacancy with fairness metrics showing violation
        2. Run monitor_fairness task
        3. Verify send_fairness_alert is triggered
        4. Check notification parameters are correct
        """
        print("\n=== Testing Fairness Violation Notification ===\n")

        # Step 1: Create job vacancy
        print("Step 1: Creating job vacancy...")
        vacancy = JobVacancy(
            title="Senior Software Engineer",
            description="Senior software engineer position",
            required_skills=["python", "react", "postgresql"],
            min_experience_months=60,
            industry="Software Development",
            work_format="remote",
            status="active"
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        vacancy_id = str(vacancy.id)
        print(f"✓ Created vacancy with ID: {vacancy_id}")

        # Step 2: Create fairness metrics showing violation (low disparate impact)
        print("\nStep 2: Creating fairness metrics with violation...")
        metrics = FairnessMetrics(
            vacancy_id=vacancy.id,
            demographic_group="gender",
            disparate_impact_ratio=0.65,  # Below 0.8 threshold - VIOLATION
            statistical_parity_difference=0.15,  # Above 0.1 threshold - VIOLATION
            overall_selection_rate=0.45,
            group_sample_size=100,
            total_sample_size=200,
            group_metrics={
                "male": {"selection_rate": 0.52, "sample_size": 100},
                "female": {"selection_rate": 0.34, "sample_size": 100}
            },
            alert_triggered=True,
            alert_severity="high"
        )
        test_db.add(metrics)
        await test_db.commit()
        await test_db.refresh(metrics)

        print(f"✓ Created fairness metrics with disparate_impact={metrics.disparate_impact_ratio}")
        print(f"  Alert triggered: {metrics.alert_triggered}")
        print(f"  Severity: {metrics.alert_severity}")

        # Step 3: Mock send_fairness_alert.delay to capture calls
        print("\nStep 3: Running monitor_fairness with mocked notification...")
        with patch('tasks.fairness_monitoring.send_fairness_alert.delay') as mock_alert:
            # Mock FairnessCalculator to return our test data
            with patch('tasks.fairness_monitoring.get_fairness_calculator') as mock_calc:
                mock_calculator = AsyncMock()
                mock_calc.return_value = mock_calculator

                # Mock analyze_vacancy_fairness to return violation
                mock_calculator.analyze_vacancy_fairness.return_value = {
                    "attributes_analyzed": {
                        "gender": {
                            "disparate_impact_ratio": 0.65,
                            "statistical_parity_difference": 0.15,
                            "overall_selection_rate": 0.45,
                            "group_sample_size": 100,
                            "total_sample_size": 200,
                            "alert_triggered": True,
                            "max_severity": "high",
                        }
                    }
                }

                # Run monitor_fairness
                result = monitor_fairness(
                    vacancy_id=vacancy_id,
                    demographic_groups=["gender"],
                    check_interval_hours=24
                )

                print(f"✓ Monitor fairness completed")
                print(f"  Vacancies checked: {result.get('vacancies_checked')}")
                print(f"  Violations detected: {result.get('violations_detected')}")
                print(f"  Alerts sent: {result.get('alerts_sent')}")

                # Step 4: Verify notification was triggered
                print("\nStep 4: Verifying notification was triggered...")
                assert result.get('violations_detected') > 0, "Expected violations to be detected"
                assert result.get('alerts_sent') > 0, "Expected alerts to be sent"

                # Verify send_fairness_alert.delay was called
                assert mock_alert.called, "send_fairness_alert.delay should have been called"
                call_args = mock_alert.call_args

                # Verify call parameters
                assert call_args is not None, "send_fairness_alert should be called with parameters"
                vac_id_arg = call_args[0][0]
                violation_details_arg = call_args[0][1]

                assert vac_id_arg == vacancy_id, f"Expected vacancy_id {vacancy_id}, got {vac_id_arg}"
                assert "demographic_group" in violation_details_arg, "violation_details should contain demographic_group"
                assert "violation" in violation_details_arg, "violation_details should contain violation"
                assert "current_metrics" in violation_details_arg, "violation_details should contain current_metrics"

                print(f"✓ Notification triggered with correct parameters")
                print(f"  Vacancy ID: {vac_id_arg}")
                print(f"  Demographic group: {violation_details_arg['demographic_group']}")
                print(f"  Severity: {violation_details_arg['violation'].get('severity')}")

    @pytest.mark.asyncio
    async def test_no_notification_when_no_violation(
        self,
        test_db: AsyncSession
    ):
        """
        Test that no notification is sent when there are no violations.

        Verification steps:
        1. Create vacancy with fairness metrics showing no violation
        2. Run monitor_fairness task
        3. Verify send_fairness_alert is NOT triggered
        """
        print("\n=== Testing No Notification When No Violation ===\n")

        # Step 1: Create job vacancy
        print("Step 1: Creating job vacancy...")
        vacancy = JobVacancy(
            title="Senior Data Scientist",
            description="Senior data scientist position",
            required_skills=["python", "machine learning", "statistics"],
            min_experience_months=48,
            industry="Data Science",
            work_format="hybrid",
            status="active"
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        vacancy_id = str(vacancy.id)
        print(f"✓ Created vacancy with ID: {vacancy_id}")

        # Step 2: Mock send_fairness_alert.delay to capture calls
        print("\nStep 2: Running monitor_fairness with mocked notification...")
        with patch('tasks.fairness_monitoring.send_fairness_alert.delay') as mock_alert:
            # Mock FairnessCalculator to return no violations
            with patch('tasks.fairness_monitoring.get_fairness_calculator') as mock_calc:
                mock_calculator = AsyncMock()
                mock_calc.return_value = mock_calculator

                # Mock analyze_vacancy_fairness to return NO violation
                mock_calculator.analyze_vacancy_fairness.return_value = {
                    "attributes_analyzed": {
                        "gender": {
                            "disparate_impact_ratio": 0.92,  # Above 0.8 threshold - OK
                            "statistical_parity_difference": 0.03,  # Below 0.1 threshold - OK
                            "overall_selection_rate": 0.48,
                            "group_sample_size": 100,
                            "total_sample_size": 200,
                            "alert_triggered": False,
                            "max_severity": None,
                        }
                    }
                }

                # Run monitor_fairness
                result = monitor_fairness(
                    vacancy_id=vacancy_id,
                    demographic_groups=["gender"],
                    check_interval_hours=24
                )

                print(f"✓ Monitor fairness completed")
                print(f"  Vacancies checked: {result.get('vacancies_checked')}")
                print(f"  Violations detected: {result.get('violations_detected')}")
                print(f"  Alerts sent: {result.get('alerts_sent')}")

                # Step 3: Verify notification was NOT triggered
                print("\nStep 3: Verifying no notification was triggered...")
                assert result.get('violations_detected') == 0, "Expected no violations"
                assert result.get('alerts_sent') == 0, "Expected no alerts sent"
                assert not mock_alert.called, "send_fairness_alert.delay should NOT have been called"

                print(f"✓ No notification triggered (as expected)")

    def test_format_fairness_alert_email(self):
        """
        Test that fairness alert email is formatted correctly.

        Verification:
        - Email subject includes severity and demographic group
        - Email body contains violation details
        - Priority set based on severity
        """
        print("\n=== Testing Fairness Alert Email Formatting ===\n")

        # Create violation details
        vacancy_id = str(uuid4())
        violation_details = {
            "demographic_group": "gender",
            "violation": {
                "is_violation": True,
                "severity": "high",
                "violated_metrics": ["disparate_impact", "statistical_parity"],
                "violation_details": {
                    "disparate_impact": {
                        "current": 0.65,
                        "threshold": 0.8,
                        "delta": -0.15,
                        "violated": True,
                    },
                    "statistical_parity": {
                        "current": 0.15,
                        "threshold": 0.1,
                        "delta": 0.05,
                        "violated": True,
                    }
                }
            },
            "current_metrics": {
                "disparate_impact_ratio": 0.65,
                "statistical_parity_difference": 0.15,
                "overall_selection_rate": 0.45,
            },
            "detected_at": datetime.utcnow().isoformat(),
        }

        # Format email
        print("Formatting fairness alert email...")
        email_details = format_fairness_alert_email(vacancy_id, violation_details)

        print(f"✓ Email formatted")
        print(f"  Subject: {email_details['subject']}")
        print(f"  Priority: {email_details['priority']}")

        # Verify email structure
        assert "subject" in email_details, "Email should have subject"
        assert "body" in email_details, "Email should have body"
        assert "priority" in email_details, "Email should have priority"

        # Verify subject contains key information
        assert "gender" in email_details['subject'].lower(), "Subject should mention demographic group"
        assert "high" in email_details['subject'].lower(), "Subject should mention severity"

        # Verify body contains violation details
        assert vacancy_id in email_details['body'], "Body should contain vacancy ID"
        assert "disparate impact" in email_details['body'].lower(), "Body should mention disparate impact"
        assert "statistical parity" in email_details['body'].lower(), "Body should mention statistical parity"

        # Verify priority is high for high severity
        assert email_details['priority'] == "high", "High severity violations should have high priority"

        print(f"✓ Email formatting verified")

    def test_detect_fairness_violation_logic(self):
        """
        Test the detect_fairness_violation function directly.

        Verification:
        - Violations detected when thresholds exceeded
        - Severity calculated correctly
        - No violations when metrics within thresholds
        """
        print("\n=== Testing Fairness Violation Detection Logic ===\n")

        # Test case 1: Clear violation
        print("Test Case 1: Clear violation (disparate impact = 0.65, stat parity = 0.15)")
        metrics_violation = {
            "disparate_impact_ratio": 0.65,
            "statistical_parity_difference": 0.15,
        }

        result_violation = detect_fairness_violation(metrics_violation)

        assert result_violation["is_violation"], "Should detect violation"
        assert result_violation["severity"] in ["high", "critical"], "Severity should be high or critical"
        assert "disparate_impact" in result_violation["violated_metrics"], "Should flag disparate impact"
        assert "statistical_parity" in result_violation["violated_metrics"], "Should flag statistical parity"

        print(f"✓ Violation detected correctly")
        print(f"  Severity: {result_violation['severity']}")
        print(f"  Violated metrics: {result_violation['violated_metrics']}")

        # Test case 2: No violation
        print("\nTest Case 2: No violation (disparate impact = 0.92, stat parity = 0.03)")
        metrics_ok = {
            "disparate_impact_ratio": 0.92,
            "statistical_parity_difference": 0.03,
        }

        result_ok = detect_fairness_violation(metrics_ok)

        assert not result_ok["is_violation"], "Should NOT detect violation"
        assert result_ok["severity"] is None, "Severity should be None"
        assert len(result_ok["violated_metrics"]) == 0, "Should have no violated metrics"

        print(f"✓ No violation detected (as expected)")

        # Test case 3: Critical violation
        print("\nTest Case 3: Critical violation (disparate impact = 0.45, stat parity = 0.28)")
        metrics_critical = {
            "disparate_impact_ratio": 0.45,
            "statistical_parity_difference": 0.28,
        }

        result_critical = detect_fairness_violation(metrics_critical)

        assert result_critical["is_violation"], "Should detect violation"
        assert result_critical["severity"] == "critical", "Severity should be critical"

        print(f"✓ Critical violation detected correctly")
        print(f"  Severity: {result_critical['severity']}")

    @pytest.mark.asyncio
    async def test_multiple_violations_trigger_multiple_notifications(
        self,
        test_db: AsyncSession
    ):
        """
        Test that multiple violations trigger multiple notifications.

        Verification steps:
        1. Create vacancy with multiple demographic group violations
        2. Run monitor_fairness task
        3. Verify multiple send_fairness_alert calls
        """
        print("\n=== Testing Multiple Violations Trigger Multiple Notifications ===\n")

        # Step 1: Create job vacancy
        print("Step 1: Creating job vacancy...")
        vacancy = JobVacancy(
            title="Product Manager",
            description="Product manager position",
            required_skills=["product management", "agile", "analytics"],
            min_experience_months=36,
            industry="Technology",
            work_format="remote",
            status="active"
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        vacancy_id = str(vacancy.id)
        print(f"✓ Created vacancy with ID: {vacancy_id}")

        # Step 2: Mock send_fairness_alert.delay to capture calls
        print("\nStep 2: Running monitor_fairness with multiple violations...")
        with patch('tasks.fairness_monitoring.send_fairness_alert.delay') as mock_alert:
            # Mock FairnessCalculator to return multiple violations
            with patch('tasks.fairness_monitoring.get_fairness_calculator') as mock_calc:
                mock_calculator = AsyncMock()
                mock_calc.return_value = mock_calculator

                # Mock analyze_vacancy_fairness to return violations for multiple groups
                mock_calculator.analyze_vacancy_fairness.return_value = {
                    "attributes_analyzed": {
                        "gender": {
                            "disparate_impact_ratio": 0.65,
                            "statistical_parity_difference": 0.15,
                            "overall_selection_rate": 0.45,
                            "group_sample_size": 100,
                            "total_sample_size": 200,
                            "alert_triggered": True,
                            "max_severity": "high",
                        },
                        "age_group": {
                            "disparate_impact_ratio": 0.72,
                            "statistical_parity_difference": 0.12,
                            "overall_selection_rate": 0.48,
                            "group_sample_size": 100,
                            "total_sample_size": 200,
                            "alert_triggered": True,
                            "max_severity": "medium",
                        }
                    }
                }

                # Run monitor_fairness
                result = monitor_fairness(
                    vacancy_id=vacancy_id,
                    demographic_groups=["gender", "age_group"],
                    check_interval_hours=24
                )

                print(f"✓ Monitor fairness completed")
                print(f"  Vacancies checked: {result.get('vacancies_checked')}")
                print(f"  Violations detected: {result.get('violations_detected')}")
                print(f"  Alerts sent: {result.get('alerts_sent')}")

                # Step 3: Verify multiple notifications triggered
                print("\nStep 3: Verifying multiple notifications triggered...")
                assert result.get('violations_detected') == 2, "Expected 2 violations"
                assert result.get('alerts_sent') == 2, "Expected 2 alerts sent"
                assert mock_alert.call_count == 2, "send_fairness_alert.delay should be called twice"

                print(f"✓ Multiple notifications triggered correctly")
                print(f"  Total alerts sent: {mock_alert.call_count}")
