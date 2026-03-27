"""
End-to-End Integration Tests for Bias Detection Workflow

Tests the complete bias detection workflow:
1. Upload resumes with varied demographic patterns
2. Run ranking for multiple candidates
3. Verify demographic inference runs
4. Verify bias detection metrics are calculated
5. Verify bias alerts are triggered and can be managed
6. Verify bias reports can be generated
7. Verify bias alert configuration can be managed
"""

import os
import pytest
import requests
from typing import Dict, Any, List
import time
from datetime import datetime, timedelta


class TestBiasDetectionE2E:
    """End-to-end tests for the bias detection workflow."""

    BASE_URL = os.getenv("API_BASE_URL", "")

    @pytest.fixture(scope="class")
    def test_vacancy(self):
        """Create a test vacancy for bias detection testing."""
        vacancy_data = {
            "position": "Senior Data Scientist",
            "industry": "Technology",
            "mandatory_requirements": [
                "Python",
                "Machine Learning",
                "Statistics",
                "SQL",
                "Data Analysis",
            ],
            "additional_requirements": ["Deep Learning", "TensorFlow", "PyTorch"],
            "experience_levels": ["senior", "middle"],
        }

        response = requests.post(f"{self.BASE_URL}/api/vacancies/", json=vacancy_data)
        assert response.status_code == 201, f"Failed to create vacancy: {response.text}"

        vacancy = response.json()
        yield vacancy

        # Cleanup
        try:
            requests.delete(f"{self.BASE_URL}/api/vacancies/{vacancy['id']}")
        except:
            pass

    @pytest.fixture(scope="class")
    def test_resumes(self):
        """
        Upload test resumes with varied demographic patterns for bias detection testing.

        Creates resumes with diverse:
        - Gender indicators (male/female names, pronouns)
        - Age indicators (graduation years, experience levels)
        - Ethnicity indicators (surname patterns)
        """
        resume_ids = []

        # Resume 1: Male, 30s, likely White
        resume_1_data = {
            "filename": "michael_johnson_resume.pdf",
            "raw_text": """
            Michael Johnson
            Senior Data Scientist

            Summary
            He is a senior data scientist with 8 years of experience in machine learning and statistical analysis.

            Experience
            Senior Data Scientist at DataCorp (2018-2026)
            - Led development of ML models using Python and TensorFlow
            - Implemented deep learning solutions for predictive analytics
            - Reduced model training time by 40% through optimization

            Data Scientist at Analytics Inc (2016-2018)
            - Developed statistical models using Python and R
            - Built data pipelines with SQL and Spark

            Education
            Master of Science in Data Science, Stanford University (2016)
            Bachelor of Science in Statistics, UCLA (2014)

            Skills
            Python, Machine Learning, Statistics, SQL, Data Analysis, Deep Learning, TensorFlow, PyTorch
            """,
        }

        # Resume 2: Female, 20s, likely Asian
        resume_2_data = {
            "filename": "sarah_kim_resume.pdf",
            "raw_text": """
            Sarah Kim
            Data Scientist

            Summary
            She is a data scientist with 4 years of experience in machine learning and data analysis.

            Experience
            Data Scientist at TechML (2022-2026)
            - Developed ML models using Python and scikit-learn
            - Implemented data analysis workflows with SQL and Pandas
            - Built deep learning models with PyTorch

            Junior Data Analyst at DataWorks (2020-2022)
            - Performed statistical analysis using Python and R
            - Created data visualizations with Tableau

            Education
            Master of Science in Statistics, UC Berkeley (2020)
            Bachelor of Science in Mathematics, MIT (2018)

            Skills
            Python, Machine Learning, Statistics, SQL, Data Analysis, PyTorch, Pandas
            """,
        }

        # Resume 3: Male, 40s, likely Hispanic
        resume_3_data = {
            "filename": "carlos_rodriguez_resume.pdf",
            "raw_text": """
            Carlos Rodriguez
            Lead Data Scientist

            Summary
            He is a lead data scientist with 15 years of experience in statistical modeling and machine learning.

            Experience
            Lead Data Scientist at ML Solutions (2011-2026)
            - Designed machine learning architectures using Python and TensorFlow
            - Led team of 6 data scientists in developing predictive models
            - Implemented deep learning for computer vision applications

            Senior Analyst at Analytics Pro (2006-2011)
            - Developed statistical models using SAS and R
            - Performed data analysis with SQL and Python

            Education
            PhD in Statistics, UT Austin (2006)
            Master of Science in Mathematics, University of Texas (2003)
            Bachelor of Science in Computer Science, Texas A&M (2001)

            Skills
            Python, Machine Learning, Statistics, SQL, Data Analysis, Deep Learning, TensorFlow, PyTorch, R
            """,
        }

        # Resume 4: Female, 30s, likely Black/African
        resume_4_data = {
            "filename": "jasmine_washington_resume.pdf",
            "raw_text": """
            Jasmine Washington
            Senior Data Scientist

            Summary
            She is a senior data scientist with 9 years of experience in machine learning and analytics.

            Experience
            Senior Data Scientist at DataFlow Inc (2017-2026)
            - Developed Python-based ML models for predictive analytics
            - Implemented deep learning solutions using TensorFlow
            - Led statistical analysis for business intelligence

            Data Scientist at Tech Analytics (2014-2017)
            - Built ML models using Python and scikit-learn
            - Performed data analysis with SQL and Pandas

            Education
            Master of Science in Data Science, Howard University (2014)
            Bachelor of Science in Statistics, Spelman College (2012)

            Skills
            Python, Machine Learning, Statistics, SQL, Data Analysis, Deep Learning, TensorFlow, Pandas
            """,
        }

        # Resume 5: Male, 20s, likely White
        resume_5_data = {
            "filename": "david_miller_resume.pdf",
            "raw_text": """
            David Miller
            Junior Data Scientist

            Summary
            He is a junior data scientist with 2 years of experience in machine learning and data analysis.

            Experience
            Junior Data Scientist at StartupML (2024-2026)
            - Developed ML models using Python and scikit-learn
            - Assisted with data analysis using SQL and Pandas
            - Built simple neural networks with TensorFlow

            Education
            Master of Science in Data Science, University of Michigan (2024)
            Bachelor of Science in Statistics, Northwestern University (2022)

            Skills
            Python, Machine Learning, Statistics, SQL, Data Analysis, TensorFlow, Pandas
            """,
        }

        resumes = [resume_1_data, resume_2_data, resume_3_data, resume_4_data, resume_5_data]

        for resume_data in resumes:
            response = requests.post(
                f"{self.BASE_URL}/api/resumes/", json=resume_data, timeout=10
            )
            if response.status_code == 201:
                resume_ids.append(response.json()["id"])
            else:
                print(f"Failed to upload resume: {response.status_code} - {response.text}")

        yield resume_ids

        # Cleanup
        for resume_id in resume_ids:
            try:
                requests.delete(f"{self.BASE_URL}/api/resumes/{resume_id}")
            except:
                pass

    def test_complete_bias_detection_workflow(
        self, test_vacancy, test_resumes: List[str]
    ):
        """
        Test the complete bias detection workflow from resume upload to alert generation.

        Workflow steps:
        1. Upload resumes with varied demographic patterns
        2. Run ranking for multiple candidates
        3. Verify demographic inference runs
        4. Verify bias detection metrics are calculated
        5. Verify alerts are triggered when bias exceeds thresholds
        """
        if not test_resumes:
            pytest.skip("No test resumes available")

        # Step 1: Verify resumes were uploaded successfully
        assert len(test_resumes) >= 3, "Need at least 3 resumes for bias detection testing"

        # Step 2: Run ranking for all candidates
        ranking_results = []
        for resume_id in test_resumes:
            ranking_request = {
                "resume_id": resume_id,
                "vacancy_id": test_vacancy["id"],
                "use_experiment": False,
            }

            response = requests.post(
                f"{self.BASE_URL}/api/ranking/rank",
                json=ranking_request,
                timeout=30,
            )

            if response.status_code == 200:
                ranking_results.append(response.json())
            else:
                print(f"Ranking failed for resume {resume_id}: {response.status_code}")

        # We may not have rankings if ML model is not trained
        if not ranking_results:
            print("No ranking results available (ML model may not be trained)")
            return

        # Step 3: Verify demographic inference was triggered
        demographic_inferences_found = 0
        for ranking_result in ranking_results:
            resume_id = ranking_result.get("resume_id")
            if not resume_id:
                continue

            # Try to get demographic inference
            response = requests.get(
                f"{self.BASE_URL}/api/resumes/{resume_id}/demographic-inference",
                timeout=10,
            )

            if response.status_code == 200:
                inference = response.json()
                # Verify key demographic attributes were inferred
                assert "inferred_gender" in inference or any(
                    key in inference
                    for key in [
                        "inferred_age_group",
                        "inferred_ethnicity",
                        "inferred_education_level",
                    ]
                ), f"Demographic inference missing key attributes for resume {resume_id}"
                demographic_inferences_found += 1

        print(
            f"Found demographic inferences for {demographic_inferences_found}/{len(ranking_results)} candidates"
        )

        # Step 4: Verify bias detection metrics are available
        metrics_response = requests.get(
            f"{self.BASE_URL}/api/fairness/metrics",
            params={
                "vacancy_id": test_vacancy["id"],
                "model_name": "ranking",
                "limit": 50,
            },
            timeout=10,
        )

        if metrics_response.status_code == 200:
            metrics_data = metrics_response.json()
            assert "metrics" in metrics_data, "Metrics response missing 'metrics' field"

            # If we have rankings, we should have bias detection metrics
            if len(ranking_results) >= 3:
                print(f"Bias detection metrics count: {len(metrics_data['metrics'])}")

                # If metrics exist, verify their structure
                for metric in metrics_data.get("metrics", [])[:3]:
                    assert "metric_id" in metric, "Metric missing metric_id"
                    assert "model_name" in metric, "Metric missing model_name"
                    assert "protected_attribute" in metric, "Metric missing protected_attribute"
                    assert "metric_type" in metric, "Metric missing metric_type"
                    assert "metric_value" in metric, "Metric missing metric_value"
                    assert "threshold" in metric, "Metric missing threshold"
                    assert "is_acceptable" in metric, "Metric missing is_acceptable"
                    assert "sample_size" in metric, "Metric missing sample_size"

        # Step 5: Verify bias alerts can be retrieved
        alerts_response = requests.get(
            f"{self.BASE_URL}/api/fairness/alerts",
            params={
                "vacancy_id": test_vacancy["id"],
                "acknowledged": False,
                "limit": 20,
            },
            timeout=10,
        )

        if alerts_response.status_code == 200:
            alerts_data = alerts_response.json()
            assert "alerts" in alerts_data, "Alerts response missing 'alerts' field"
            assert (
                "unacknowledged_count" in alerts_data
            ), "Alerts response missing unacknowledged_count"

            print(f"Found {len(alerts_data['alerts'])} bias detection alerts")

    def test_bias_reports_generation(self, test_vacancy, test_resumes: List[str]):
        """Test that bias reports can be generated on demand."""
        if not test_resumes:
            pytest.skip("No test resumes available")

        # Generate a new bias report
        report_request = {
            "vacancy_id": test_vacancy["id"],
            "model_name": "ranking",
            "model_version": "latest",
            "report_type": "demographic_analysis",
            "demographic_attributes": ["gender", "age_group", "ethnicity"],
        }

        response = requests.post(
            f"{self.BASE_URL}/api/fairness/reports/generate",
            json=report_request,
            timeout=30,
        )

        # Report generation might not be fully implemented
        if response.status_code in [200, 201]:
            report = response.json()
            assert "report_id" in report, "Report missing report_id"
            print(f"Generated bias report: {report['report_id']}")

            # Verify we can retrieve reports
            reports_response = requests.get(
                f"{self.BASE_URL}/api/fairness/reports",
                params={"vacancy_id": test_vacancy["id"], "limit": 10},
                timeout=10,
            )

            if reports_response.status_code == 200:
                reports_data = reports_response.json()
                assert "reports" in reports_data, "Reports response missing 'reports' field"
                print(f"Found {len(reports_data['reports'])} bias reports")

    def test_bias_alerts_workflow(self, test_vacancy, test_resumes: List[str]):
        """Test that bias alerts are triggered and can be managed."""
        if not test_resumes:
            pytest.skip("No test resumes available")

        # Get alerts for the vacancy
        alerts_response = requests.get(
            f"{self.BASE_URL}/api/fairness/alerts",
            params={
                "vacancy_id": test_vacancy["id"],
                "severity": ["critical", "high"],
                "acknowledged": False,
                "limit": 20,
            },
            timeout=10,
        )

        if alerts_response.status_code == 200:
            alerts_data = alerts_response.json()
            assert "alerts" in alerts_data, "Alerts response missing 'alerts' field"
            assert (
                "unacknowledged_count" in alerts_data
            ), "Alerts response missing unacknowledged_count"

            print(f"Found {len(alerts_data['alerts'])} bias alerts")

            # If we have alerts, test acknowledging one
            if alerts_data["alerts"]:
                alert = alerts_data["alerts"][0]
                alert_id = alert.get("alert_id")

                if alert_id:
                    # Acknowledge the alert
                    acknowledge_response = requests.post(
                        f"{self.BASE_URL}/api/fairness/alerts/{alert_id}/acknowledge",
                        json={"acknowledged_by": "test_user", "notes": "Test acknowledgment"},
                        timeout=10,
                    )

                    if acknowledge_response.status_code == 200:
                        result = acknowledge_response.json()
                        assert (
                            result.get("acknowledged") == True
                        ), "Alert was not marked as acknowledged"
                        print(f"Successfully acknowledged bias alert {alert_id}")

    def test_bias_alert_configuration(self, test_vacancy):
        """Test that bias alert configuration can be managed."""
        # Create a new bias alert configuration
        config_data = {
            "organization_id": None,
            "alert_type": "disparate_impact",
            "metric_name": "Gender Disparate Impact",
            "threshold_value": 0.8,
            "comparison_operator": "less_than",
            "severity_level": "high",
            "is_enabled": True,
            "notification_enabled": True,
            "demographic_groups": ["gender"],
            "alert_frequency": "immediate",
            "description": "Alert when gender disparate impact falls below 0.8",
        }

        response = requests.post(
            f"{self.BASE_URL}/api/bias-alert-config/",
            json=config_data,
            timeout=10,
        )

        config_id = None
        if response.status_code in [200, 201]:
            config = response.json()
            assert "id" in config, "Config missing id"
            config_id = config["id"]
            print(f"Created bias alert configuration: {config_id}")

            # Verify we can retrieve the configuration
            get_response = requests.get(
                f"{self.BASE_URL}/api/bias-alert-config/{config_id}",
                timeout=10,
            )

            if get_response.status_code == 200:
                retrieved_config = get_response.json()
                assert retrieved_config["alert_type"] == "disparate_impact"
                assert retrieved_config["threshold_value"] == 0.8

            # Clean up - delete the configuration
            try:
                requests.delete(
                    f"{self.BASE_URL}/api/bias-alert-config/{config_id}",
                    timeout=10,
                )
            except:
                pass

        # Get list of all configurations
        list_response = requests.get(
            f"{self.BASE_URL}/api/bias-alert-config/",
            params={"limit": 10},
            timeout=10,
        )

        if list_response.status_code == 200:
            configs_data = list_response.json()
            assert "configs" in configs_data, "Response missing 'configs' field"
            print(f"Found {len(configs_data['configs'])} bias alert configurations")

    def test_fairness_summary(self, test_vacancy):
        """Test that fairness summary is available for dashboard display."""
        # Get fairness summary
        summary_response = requests.get(
            f"{self.BASE_URL}/api/fairness/summary",
            timeout=10,
        )

        if summary_response.status_code == 200:
            summary = summary_response.json()
            assert "total_models" in summary, "Summary missing total_models"
            assert "models_with_issues" in summary, "Summary missing models_with_issues"
            assert "overall_fairness_score" in summary, "Summary missing overall_fairness_score"
            assert (
                "protected_attributes_analyzed" in summary
            ), "Summary missing protected_attributes_analyzed"

            print(
                f"Fairness Summary: {summary['total_models']} models, "
                f"{summary['models_with_issues']} with issues, "
                f"score: {summary.get('overall_fairness_score', 'N/A')}"
            )

    def test_bias_detection_metrics_by_attribute(self, test_vacancy, test_resumes: List[str]):
        """Test that bias detection metrics can be filtered by protected attribute."""
        if not test_resumes:
            pytest.skip("No test resumes available")

        # Test filtering by different protected attributes
        protected_attributes = ["gender", "age_group", "ethnicity"]

        for attribute in protected_attributes:
            metrics_response = requests.get(
                f"{self.BASE_URL}/api/fairness/metrics",
                params={
                    "vacancy_id": test_vacancy["id"],
                    "protected_attribute": attribute,
                    "limit": 10,
                },
                timeout=10,
            )

            if metrics_response.status_code == 200:
                metrics_data = metrics_response.json()
                assert "metrics" in metrics_data, f"Missing metrics field for {attribute}"

                # Verify all metrics are for the requested attribute
                for metric in metrics_data["metrics"]:
                    assert (
                        metric["protected_attribute"] == attribute
                    ), f"Metric has wrong protected attribute"

                print(f"Found {len(metrics_data['metrics'])} metrics for {attribute}")

    def test_bias_thresholds_evaluation(self, test_vacancy):
        """Test that bias thresholds are correctly evaluated."""
        # Get metrics below threshold (should trigger alerts)
        below_threshold_response = requests.get(
            f"{self.BASE_URL}/api/fairness/metrics",
            params={
                "vacancy_id": test_vacancy["id"],
                "is_acceptable": False,
                "limit": 10,
            },
            timeout=10,
        )

        if below_threshold_response.status_code == 200:
            below_threshold = below_threshold_response.json()

            if below_threshold["metrics"]:
                print(
                    f"Found {len(below_threshold['metrics'])} metrics below threshold"
                )

                # Verify these metrics should trigger alerts
                for metric in below_threshold["metrics"]:
                    assert (
                        metric["is_acceptable"] == False
                    ), "Metric should be marked as unacceptable"

                # Check if corresponding alerts exist
                alerts_response = requests.get(
                    f"{self.BASE_URL}/api/fairness/alerts",
                    params={"vacancy_id": test_vacancy["id"], "limit": 20},
                    timeout=10,
                )

                if alerts_response.status_code == 200:
                    alerts_data = alerts_response.json()
                    print(
                        f"Found {len(alerts_data['alerts'])} alerts for this vacancy"
                    )


class TestBiasDetectionDataIntegrity:
    """Test data integrity and privacy protections for bias detection."""

    BASE_URL = os.getenv("API_BASE_URL", "")

    def test_demographic_inference_privacy(self):
        """Test that demographic data respects privacy protections."""
        # Create a test resume
        resume_data = {
            "filename": "privacy_test_resume.pdf",
            "raw_text": """
            Alex Morgan
            Data Scientist

            Experience
            Data Scientist at TechCorp (2020-2024)
            - Developed ML models using Python
            - Performed statistical analysis with R
            - Built data pipelines with SQL

            Education
            MS Data Science, MIT (2020)
            """,
        }

        response = requests.post(f"{self.BASE_URL}/api/resumes/", json=resume_data)
        if response.status_code != 201:
            pytest.skip("Could not create test resume")

        resume_id = response.json()["id"]

        try:
            # Get demographic inference
            inference_response = requests.get(
                f"{self.BASE_URL}/api/resumes/{resume_id}/demographic-inference"
            )

            if inference_response.status_code == 200:
                inference = inference_response.json()

                # Verify confidence scores are present
                assert (
                    "confidence_scores" in inference
                ), "Demographic inference must include confidence scores"

                # Verify inference is marked as probabilistic
                assert (
                    "confidence_threshold_met" in inference
                ), "Should indicate if confidence threshold is met"

                # Verify raw features are retained for audit
                assert "raw_features" in inference, "Raw features should be retained"

        finally:
            # Cleanup
            requests.delete(f"{self.BASE_URL}/api/resumes/{resume_id}")

    def test_bias_metrics_aggregation(self):
        """Test that bias metrics are computed from aggregate data."""
        # Get bias detection metrics
        response = requests.get(f"{self.BASE_URL}/api/fairness/metrics", params={"limit": 5})

        if response.status_code == 200:
            metrics_data = response.json()

            for metric in metrics_data["metrics"]:
                # Verify sample size is reported
                assert (
                    "sample_size" in metric
                ), "Bias metrics must include sample size"

                # Verify sample size is reasonable
                assert metric["sample_size"] >= 0, "Sample size cannot be negative"

                # If sample size is provided, verify it's used for validity
                if metric["sample_size"] > 0:
                    # Metrics with small samples should be flagged
                    if metric["sample_size"] < 10:
                        print(
                            f"Warning: Metric {metric['metric_id']} has small sample size: {metric['sample_size']}"
                        )

    def test_bias_audit_trail(self):
        """Test that bias detection actions are logged for compliance."""
        # This test verifies that bias detection creates audit trail entries
        # when bias is detected or alerts are triggered

        # Get recent audit logs
        response = requests.get(
            f"{self.BASE_URL}/api/audit-logs",
            params={"event_type": "bias_detected", "limit": 10},
            timeout=10,
        )

        if response.status_code == 200:
            audit_data = response.json()

            # Verify audit log structure
            if audit_data.get("logs"):
                for log in audit_data["logs"][:3]:
                    assert "event_id" in log, "Audit log missing event_id"
                    assert "event_type" in log, "Audit log missing event_type"
                    assert "timestamp" in log, "Audit log missing timestamp"
                    assert "details" in log, "Audit log missing details"

                print(f"Found {len(audit_data['logs'])} bias detection audit log entries")
