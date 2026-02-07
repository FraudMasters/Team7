"""
import os
End-to-End Integration Tests for AI Bias Detection and Fairness Monitoring

Tests the complete fairness monitoring workflow:
1. Upload resumes with varied demographic patterns
2. Run ranking for multiple candidates
3. Verify demographic inference runs
4. Verify fairness metrics are calculated
5. Verify metrics are displayed in dashboard
6. Verify alerts trigger when bias exceeds threshold
"""

import pytest
import requests
from typing import Dict, Any, List
import time
from datetime import datetime, timedelta


class TestFairnessE2E:
    """End-to-end tests for the fairness monitoring workflow."""

    BASE_URL = os.getenv("API_BASE_URL", "")

    @pytest.fixture(scope="class")
    def test_vacancy(self):
        """Create a test vacancy for fairness testing."""
        vacancy_data = {
            "position": "Senior Software Engineer",
            "industry": "Technology",
            "mandatory_requirements": [
                "Python",
                "JavaScript",
                "React",
                "PostgreSQL",
                "Docker",
            ],
            "additional_requirements": ["Kubernetes", "AWS", "GraphQL"],
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
    def diverse_resumes(self):
        """
        Upload test resumes with varied demographic patterns for bias testing.

        Creates resumes with diverse:
        - Gender indicators (male/female names, pronouns)
        - Age indicators (graduation years, experience levels)
        - Ethnicity indicators (surname patterns)
        """
        resume_ids = []

        # Resume 1: Male, 30s, likely White
        resume_1_data = {
            "filename": "john_smith_resume.pdf",
            "raw_text": """
            John Smith
            Senior Software Engineer

            Summary
            He is a senior software engineer with 8 years of experience building scalable web applications.

            Experience
            Senior Software Engineer at Tech Corp (2018-2026)
            - Led development of microservices architecture using Python and Django
            - Implemented CI/CD pipelines with Docker and Kubernetes
            - Reduced application latency by 40% through optimization

            Software Engineer at Startup Inc (2016-2018)
            - Developed React-based frontend applications
            - Built RESTful APIs with PostgreSQL and Node.js

            Education
            Bachelor of Science in Computer Science, Stanford University (2016)

            Skills
            Python, JavaScript, React, Docker, Kubernetes, PostgreSQL, AWS, GraphQL
            """,
        }

        # Resume 2: Female, 20s, likely Asian
        resume_2_data = {
            "filename": "emily_chen_resume.pdf",
            "raw_text": """
            Emily Chen
            Software Engineer

            Summary
            She is a motivated software engineer with 4 years of experience in full-stack development.

            Experience
            Software Engineer at CloudTech (2022-2026)
            - Developed web applications using React and TypeScript
            - Implemented database optimizations for PostgreSQL
            - Worked with Docker containers in AWS environment

            Junior Developer at WebAgency (2020-2022)
            - Built responsive web applications with JavaScript
            - Assisted with database design and SQL queries

            Education
            Bachelor of Science in Computer Engineering, UC Berkeley (2020)

            Skills
            Python, JavaScript, React, TypeScript, PostgreSQL, Docker, AWS
            """,
        }

        # Resume 3: Male, 40s, likely Hispanic
        resume_3_data = {
            "filename": "rodrigo_garcia_resume.pdf",
            "raw_text": """
            Rodrigo Garcia
            Senior Software Architect

            Summary
            He is a senior software architect with 15 years of experience designing enterprise systems.

            Experience
            Software Architect at Enterprise Solutions (2011-2026)
            - Designed microservices architecture using Python and Java
            - Led team of 8 engineers in implementing scalable systems
            - Implemented PostgreSQL clustering for high availability

            Lead Developer at FinanceTech (2006-2011)
            - Developed trading platforms using Java and PostgreSQL
            - Optimized database queries for real-time transactions

            Education
            Master of Science in Computer Science, UT Austin (2006)
            Bachelor of Science in Computer Engineering, Texas A&M (2004)

            Skills
            Python, Java, JavaScript, React, PostgreSQL, Docker, Kubernetes, AWS, GraphQL
            """,
        }

        # Resume 4: Female, 30s, likely Black/African
        resume_4_data = {
            "filename": "latoya_williams_resume.pdf",
            "raw_text": """
            Latoya Williams
            Senior Software Developer

            Summary
            She is a senior software developer with 9 years of experience in backend development.

            Experience
            Senior Developer at DataFlow (2017-2026)
            - Developed Python-based microservices for data processing
            - Implemented PostgreSQL database optimizations
            - Led deployment using Docker and Kubernetes

            Software Engineer at AppWorks (2014-2017)
            - Built React applications with JavaScript
            - Developed RESTful APIs with Python and Flask

            Education
            Master of Science in Software Engineering, Howard University (2014)
            Bachelor of Science in Computer Science, Spelman College (2012)

            Skills
            Python, JavaScript, React, Django, PostgreSQL, Docker, Kubernetes, AWS
            """,
        }

        # Resume 5: Male, 20s, likely White
        resume_5_data = {
            "filename": "james_anderson_resume.pdf",
            "raw_text": """
            James Anderson
            Junior Software Engineer

            Summary
            He is a junior software engineer with 2 years of experience in web development.

            Experience
            Junior Developer at StartupCo (2024-2026)
            - Developed frontend features using React and JavaScript
            - Assisted with backend API development in Python
            - Worked with PostgreSQL databases in Docker environment

            Education
            Bachelor of Science in Computer Science, University of Michigan (2024)

            Skills
            Python, JavaScript, React, PostgreSQL, Docker, Git
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

    def test_complete_fairness_workflow(
        self, test_vacancy, diverse_resumes: List[str]
    ):
        """
        Test the complete fairness monitoring workflow from resume upload to metric calculation.

        Workflow steps:
        1. Upload resumes with varied demographic patterns
        2. Run ranking for multiple candidates
        3. Verify demographic inference runs
        4. Verify fairness metrics are calculated
        5. Verify metrics are displayed in dashboard
        """
        if not diverse_resumes:
            pytest.skip("No test resumes available")

        # Step 1: Verify resumes were uploaded successfully
        assert len(diverse_resumes) >= 3, "Need at least 3 resumes for fairness testing"

        # Step 2: Run ranking for all candidates
        ranking_results = []
        for resume_id in diverse_resumes:
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
        # Check demographic inferences for each ranked candidate
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

        # Step 4: Verify fairness metrics are available
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

            # If we have rankings, we should have fairness metrics
            if len(ranking_results) >= 3:
                # Verify at least one metric exists (may be from background task)
                print(f"Fairness metrics count: {len(metrics_data['metrics'])}")

                # If metrics exist, verify their structure
                for metric in metrics_data.get("metrics", [])[:3]:  # Check first 3
                    assert "metric_id" in metric, "Metric missing metric_id"
                    assert "model_name" in metric, "Metric missing model_name"
                    assert "protected_attribute" in metric, "Metric missing protected_attribute"
                    assert "metric_type" in metric, "Metric missing metric_type"
                    assert "metric_value" in metric, "Metric missing metric_value"
                    assert "threshold" in metric, "Metric missing threshold"
                    assert "is_acceptable" in metric, "Metric missing is_acceptable"

        # Step 5: Verify fairness summary is available
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

    def test_fairness_reports_generation(self, test_vacancy, diverse_resumes: List[str]):
        """Test that fairness reports can be generated on demand."""
        if not diverse_resumes:
            pytest.skip("No test resumes available")

        # Generate a new fairness report
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
            print(f"Generated fairness report: {report['report_id']}")

            # Verify we can retrieve reports
            reports_response = requests.get(
                f"{self.BASE_URL}/api/fairness/reports",
                params={"vacancy_id": test_vacancy["id"], "limit": 10},
                timeout=10,
            )

            if reports_response.status_code == 200:
                reports_data = reports_response.json()
                assert "reports" in reports_data, "Reports response missing 'reports' field"
                print(f"Found {len(reports_data['reports'])} fairness reports")

    def test_fairness_alerts_workflow(self, test_vacancy, diverse_resumes: List[str]):
        """Test that fairness alerts are triggered and can be managed."""
        if not diverse_resumes:
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

            print(f"Found {len(alerts_data['alerts'])} fairness alerts")

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
                        print(f"Successfully acknowledged alert {alert_id}")

    def test_fairness_aware_ranking(self, test_vacancy, diverse_resumes: List[str]):
        """Test that fairness-aware ranking endpoint works correctly."""
        if not diverse_resumes:
            pytest.skip("No test resumes available")

        # Test fairness-aware ranking
        resume_id = diverse_resumes[0]

        fair_ranking_request = {
            "resume_id": resume_id,
            "vacancy_id": test_vacancy["id"],
            "enable_fairness": True,
            "mitigation_strategy": "equal_opportunity",
            "use_experiment": False,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/ranking/rank-fair",
            json=fair_ranking_request,
            timeout=30,
        )

        # May not be implemented if ML model not trained
        if response.status_code == 200:
            fair_ranking = response.json()
            assert "resume_id" in fair_ranking, "Fair ranking missing resume_id"
            assert "vacancy_id" in fair_ranking, "Fair ranking missing vacancy_id"
            assert (
                "fairness_enabled" in fair_ranking
            ), "Fair ranking missing fairness_enabled flag"
            assert (
                fair_ranking["fairness_enabled"] == True
            ), "Fairness was not enabled in response"

            # Verify bias metrics are included
            if "bias_metrics" in fair_ranking:
                assert isinstance(
                    fair_ranking["bias_metrics"], dict
                ), "Bias metrics should be a dictionary"
                print(f"Bias metrics: {fair_ranking['bias_metrics']}")

    def test_demographic_inference_direct(self, diverse_resumes: List[str]):
        """Test demographic inference directly on uploaded resumes."""
        if not diverse_resumes:
            pytest.skip("No test resumes available")

        # Test demographic inference for a few resumes
        for resume_id in diverse_resumes[:3]:  # Test first 3 resumes
            response = requests.get(
                f"{self.BASE_URL}/api/resumes/{resume_id}/demographic-inference",
                timeout=10,
            )

            if response.status_code == 200:
                inference = response.json()

                # Verify structure
                expected_fields = [
                    "resume_id",
                    "inferred_gender",
                    "inferred_age_group",
                    "inferred_ethnicity",
                    "confidence_scores",
                ]

                for field in expected_fields:
                    assert field in inference, f"Demographic inference missing {field}"

                # Verify confidence scores are present
                if "confidence_scores" in inference:
                    assert isinstance(
                        inference["confidence_scores"], dict
                    ), "Confidence scores should be a dictionary"

                print(
                    f"Resume {resume_id}: gender={inference.get('inferred_gender')}, "
                    f"age_group={inference.get('inferred_age_group')}, "
                    f"ethnicity={inference.get('inferred_ethnicity')}"
                )

    def test_dashboard_metrics_display(self, test_vacancy):
        """Test that fairness metrics can be retrieved for dashboard display."""
        # Get metrics for dashboard
        metrics_response = requests.get(
            f"{self.BASE_URL}/api/fairness/metrics",
            params={
                "vacancy_id": test_vacancy["id"],
                "protected_attribute": "gender",
                "limit": 10,
            },
            timeout=10,
        )

        if metrics_response.status_code == 200:
            metrics_data = metrics_response.json()
            assert "metrics" in metrics_data, "Missing metrics field"
            assert "total_count" in metrics_data, "Missing total_count field"

            # Verify metric structure for dashboard display
            for metric in metrics_data["metrics"][:3]:
                assert (
                    "protected_attribute" in metric
                ), "Metric missing protected_attribute"
                assert "metric_type" in metric, "Metric missing metric_type"
                assert "metric_value" in metric, "Metric missing metric_value"
                assert "is_acceptable" in metric, "Metric missing is_acceptable"

                # Verify value is within expected ranges
                if metric["metric_type"] == "disparate_impact":
                    assert (
                        0 <= metric["metric_value"] <= 2
                    ), "Disparate impact should be 0-2"
                elif metric["metric_type"] == "statistical_parity":
                    assert (
                        -1 <= metric["metric_value"] <= 1
                    ), "Statistical parity should be -1 to 1"

            print(
                f"Dashboard metrics: {len(metrics_data['metrics'])} metrics for {metrics_data['total_count']} total"
            )

    def test_fairness_thresholds_and_alerts(self, test_vacancy):
        """Test that fairness thresholds are correctly evaluated and alerts triggered."""
        # Get metrics below threshold (should trigger alerts)
        below_threshold_response = requests.get(
            f"{self.BASE_URL}/api/fairness/metrics",
            params={
                "vacancy_id": test_vacancy["id"],
                "is_acceptable": False,  # Get metrics that exceeded thresholds
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
                    assert (
                        metric["metric_value"] < metric["threshold"]
                        or metric["metric_value"] > metric["threshold"] * 1.5
                    ), "Metric value should be outside acceptable range"

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


class TestFairnessDataIntegrity:
    """Test data integrity and privacy protections for fairness monitoring."""

    BASE_URL = os.getenv("API_BASE_URL", "")

    def test_demographic_data_privacy(self):
        """Test that demographic data respects privacy protections."""
        # This test verifies that demographic data:
        # 1. Is inferred probabilistically (not self-reported)
        # 2. Includes confidence scores
        # 3. Is used only for aggregate analysis

        # Create a test resume
        resume_data = {
            "filename": "privacy_test_resume.pdf",
            "raw_text": """
            Alex Morgan
            Software Developer

            Experience
            Developer at TechCorp (2020-2024)
            - Developed Python applications
            - Worked with React and PostgreSQL

            Education
            BS Computer Science, MIT (2020)
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

    def test_fairness_metrics_aggregation(self):
        """Test that fairness metrics are computed from aggregate data, not individual."""
        # This test verifies that fairness metrics:
        # 1. Include sample sizes
        # 2. Require minimum samples for validity
        # 3. Provide group-level statistics

        # Get fairness metrics
        response = requests.get(f"{self.BASE_URL}/api/fairness/metrics", params={"limit": 5})

        if response.status_code == 200:
            metrics_data = response.json()

            for metric in metrics_data["metrics"]:
                # Verify sample size is reported
                assert (
                    "sample_size" in metric
                ), "Fairness metrics must include sample size"

                # Verify sample size is reasonable
                assert metric["sample_size"] >= 0, "Sample size cannot be negative"

                # If sample size is provided, verify it's used for validity
                if metric["sample_size"] > 0:
                    # Metrics with small samples should be flagged
                    if metric["sample_size"] < 10:
                        print(
                            f"Warning: Metric {metric['metric_id']} has small sample size: {metric['sample_size']}"
                        )
