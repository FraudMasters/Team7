"""
End-to-End Integration Tests for Confidence Dashboard API

Tests the complete confidence dashboard workflow:
1. Fetch aggregated confidence metrics
2. Retrieve AI vs human comparison data
3. Export confidence reports in CSV and JSON formats
4. Error handling and validation
"""
import pytest
import requests
from typing import Dict, Any
from uuid import uuid4


class TestConfidenceDashboardE2E:
    """End-to-end tests for the confidence dashboard API."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(scope="class")
    def test_vacancy(self):
        """Create a test vacancy for confidence dashboard tests."""
        vacancy_data = {
            "position": "Senior Python Developer",
            "industry": "Technology",
            "mandatory_requirements": ["Python", "Django", "PostgreSQL", "Docker"],
            "additional_requirements": ["Kubernetes", "Redis", "Celery"],
            "experience_levels": ["senior", "middle"],
        }

        response = requests.post(f"{self.BASE_URL}/api/vacancies/", json=vacancy_data)
        assert response.status_code == 201

        vacancy = response.json()
        yield vacancy

        # Cleanup
        requests.delete(f"{self.BASE_URL}/api/vacancies/{vacancy['id']}")

    @pytest.fixture(scope="class")
    def test_resumes(self):
        """Upload test resumes for confidence dashboard tests."""
        resume_ids = []

        # Create multiple test resumes with varying skill levels
        resumes_data = [
            {
                "filename": "senior_python_resume.pdf",
                "raw_text": """
                John Senior
                Senior Python Developer with 7 years of experience.

                Skills: Python, Django, PostgreSQL, Docker, Kubernetes, Redis, Celery, AWS.
                Experience: Led team of 5 developers, built microservices architecture.
                Education: Master's in Computer Science
                """,
            },
            {
                "filename": "mid_python_resume.pdf",
                "raw_text": """
                Jane Middle
                Python Developer with 4 years of experience.

                Skills: Python, Django, PostgreSQL, Docker.
                Experience: Developed REST APIs, worked on web applications.
                Education: Bachelor's in Computer Science
                """,
            },
            {
                "filename": "junior_python_resume.pdf",
                "raw_text": """
                Jack Junior
                Junior Python Developer with 1 year of experience.

                Skills: Python, basic Django knowledge.
                Experience: Internship and personal projects.
                Education: Bachelor's in Computer Science
                """,
            },
        ]

        for resume_data in resumes_data:
            response = requests.post(f"{self.BASE_URL}/api/resumes/", json=resume_data)
            if response.status_code == 201:
                resume_ids.append(response.json()['id'])

        yield resume_ids

        # Cleanup
        for resume_id in resume_ids:
            requests.delete(f"{self.BASE_URL}/api/resumes/{resume_id}")

    def test_confidence_metrics_endpoint(self, test_vacancy, test_resumes):
        """Test confidence metrics aggregation endpoint."""
        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/metrics"
        )

        assert response.status_code == 200

        metrics = response.json()

        # Verify response structure
        assert "average_confidence" in metrics
        assert "median_confidence" in metrics
        assert "min_confidence" in metrics
        assert "max_confidence" in metrics
        assert "total_rankings" in metrics
        assert "distribution" in metrics
        assert "uncertainty" in metrics
        assert "model_accuracy" in metrics

        # Verify data types
        assert isinstance(metrics["average_confidence"], (int, float))
        assert isinstance(metrics["median_confidence"], (int, float))
        assert isinstance(metrics["min_confidence"], (int, float))
        assert isinstance(metrics["max_confidence"], (int, float))
        assert isinstance(metrics["total_rankings"], int)

        # Verify confidence values are in valid range (0-1)
        assert 0 <= metrics["average_confidence"] <= 1
        assert 0 <= metrics["median_confidence"] <= 1
        assert 0 <= metrics["min_confidence"] <= 1
        assert 0 <= metrics["max_confidence"] <= 1

        # Verify distribution structure
        distribution = metrics["distribution"]
        assert "high_confidence" in distribution
        assert "medium_confidence" in distribution
        assert "low_confidence" in distribution
        assert "high_confidence_percentage" in distribution
        assert "medium_confidence_percentage" in distribution
        assert "low_confidence_percentage" in distribution

        # Verify distribution counts are non-negative
        assert distribution["high_confidence"] >= 0
        assert distribution["medium_confidence"] >= 0
        assert distribution["low_confidence"] >= 0

        # Verify distribution percentages sum to ~100%
        total_percentage = (
            distribution["high_confidence_percentage"]
            + distribution["medium_confidence_percentage"]
            + distribution["low_confidence_percentage"]
        )
        assert 99.0 <= total_percentage <= 101.0  # Allow small rounding errors

        # Verify uncertainty indicators
        uncertainty = metrics["uncertainty"]
        assert "low_confidence_count" in uncertainty
        assert "high_uncertainty_count" in uncertainty
        assert "average_confidence_interval_width" in uncertainty
        assert "flagged_for_review" in uncertainty

        # Verify model accuracy summary
        accuracy = metrics["model_accuracy"]
        assert "overall_accuracy" in accuracy
        assert "precision" in accuracy
        assert "recall" in accuracy
        assert "f1_score" in accuracy
        assert "total_predictions" in accuracy
        assert "feedback_count" in accuracy

        # Verify accuracy metrics are in valid range (0-1)
        assert 0 <= accuracy["overall_accuracy"] <= 1
        assert 0 <= accuracy["precision"] <= 1
        assert 0 <= accuracy["recall"] <= 1
        assert 0 <= accuracy["f1_score"] <= 1

    def test_confidence_metrics_with_date_filters(self, test_vacancy):
        """Test confidence metrics with date range filters."""
        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/metrics",
            params={
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
            }
        )

        assert response.status_code == 200

        metrics = response.json()
        assert "average_confidence" in metrics
        assert "total_rankings" in metrics

    def test_confidence_metrics_with_vacancy_filter(self, test_vacancy):
        """Test confidence metrics filtered by vacancy."""
        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/metrics",
            params={"vacancy_id": test_vacancy["id"]}
        )

        assert response.status_code == 200

        metrics = response.json()
        assert "average_confidence" in metrics
        assert "total_rankings" in metrics

    def test_ai_human_comparison_endpoint(self, test_vacancy, test_resumes):
        """Test AI vs human recruiter comparison endpoint."""
        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/ai-human-comparison"
        )

        assert response.status_code == 200

        comparison = response.json()

        # Verify response structure
        assert "agreement" in comparison
        assert "efficiency" in comparison
        assert "confidence_correlation" in comparison
        assert "recommendations" in comparison

        # Verify agreement metrics
        agreement = comparison["agreement"]
        assert "agreement_rate" in agreement
        assert "total_comparisons" in agreement
        assert "ai_correct_count" in agreement
        assert "human_override_count" in agreement
        assert "human_override_correct" in agreement

        # Verify agreement rate is valid (0-1)
        assert 0 <= agreement["agreement_rate"] <= 1

        # Verify counts are non-negative
        assert agreement["total_comparisons"] >= 0
        assert agreement["ai_correct_count"] >= 0
        assert agreement["human_override_count"] >= 0
        assert agreement["human_override_correct"] >= 0

        # Verify efficiency metrics
        efficiency = comparison["efficiency"]
        assert "avg_time_saved_hours" in efficiency
        assert "total_time_saved_hours" in efficiency
        assert "automation_rate" in efficiency
        assert "manual_review_rate" in efficiency

        # Verify rates are valid (0-1)
        assert 0 <= efficiency["automation_rate"] <= 1
        assert 0 <= efficiency["manual_review_rate"] <= 1

        # Verify confidence correlation
        correlation = comparison["confidence_correlation"]
        assert "high_confidence_accuracy" in correlation
        assert "medium_confidence_accuracy" in correlation
        assert "low_confidence_accuracy" in correlation
        assert "correlation_coefficient" in correlation

        # Verify accuracy values are valid (0-1)
        assert 0 <= correlation["high_confidence_accuracy"] <= 1
        assert 0 <= correlation["medium_confidence_accuracy"] <= 1
        assert 0 <= correlation["low_confidence_accuracy"] <= 1

        # Verify correlation coefficient is valid (-1 to 1)
        assert -1 <= correlation["correlation_coefficient"] <= 1

        # Verify recommendations is a list
        assert isinstance(comparison["recommendations"], list)
        assert len(comparison["recommendations"]) > 0

        # Verify each recommendation is a string
        for recommendation in comparison["recommendations"]:
            assert isinstance(recommendation, str)
            assert len(recommendation) > 0

    def test_ai_human_comparison_with_date_filters(self, test_vacancy):
        """Test AI-human comparison with date range filters."""
        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/ai-human-comparison",
            params={
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
            }
        )

        assert response.status_code == 200

        comparison = response.json()
        assert "agreement" in comparison
        assert "efficiency" in comparison

    def test_ai_human_comparison_with_vacancy_filter(self, test_vacancy):
        """Test AI-human comparison filtered by vacancy."""
        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/ai-human-comparison",
            params={"vacancy_id": test_vacancy["id"]}
        )

        assert response.status_code == 200

        comparison = response.json()
        assert "agreement" in comparison
        assert "confidence_correlation" in comparison

    def test_export_confidence_report_json(self, test_vacancy):
        """Test confidence report export in JSON format."""
        export_request = {
            "format": "json",
            "include_metadata": True,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/confidence-dashboard/export",
            json=export_request
        )

        assert response.status_code == 200

        export_data = response.json()

        # Verify response structure
        assert "format" in export_data
        assert "data" in export_data
        assert "metadata" in export_data

        # Verify format is correct
        assert export_data["format"] == "json"

        # Verify data is a dictionary
        assert isinstance(export_data["data"], dict)

        # Verify data sections
        data = export_data["data"]
        assert "summary_metrics" in data
        assert "distribution" in data
        assert "uncertainty" in data
        assert "model_accuracy" in data
        assert "ai_human_comparison" in data

        # Verify metadata structure
        metadata = export_data["metadata"]
        assert "export_timestamp" in metadata
        assert "format" in metadata
        assert "total_records" in metadata
        assert "filters_applied" in metadata

        # Verify metadata format is correct
        assert metadata["format"] == "json"
        assert isinstance(metadata["total_records"], int)
        assert metadata["total_records"] > 0

        # Verify timestamp is ISO 8601 format
        assert "T" in metadata["export_timestamp"]
        assert "Z" in metadata["export_timestamp"]

    def test_export_confidence_report_csv(self, test_vacancy):
        """Test confidence report export in CSV format."""
        export_request = {
            "format": "csv",
            "include_metadata": True,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/confidence-dashboard/export",
            json=export_request
        )

        assert response.status_code == 200

        export_data = response.json()

        # Verify response structure
        assert "format" in export_data
        assert "data" in export_data
        assert "metadata" in export_data

        # Verify format is correct
        assert export_data["format"] == "csv"

        # Verify data is a string (CSV content)
        assert isinstance(export_data["data"], str)

        # Verify CSV has header row
        csv_lines = export_data["data"].strip().split('\n')
        assert len(csv_lines) > 1  # At least header + data

        # Verify CSV header format
        header = csv_lines[0]
        assert "section" in header
        assert "metric" in header
        assert "value" in header

        # Verify CSV has data rows
        data_rows = csv_lines[1:]
        assert len(data_rows) > 0

        # Verify each data row has 3 columns (section, metric, value)
        for row in data_rows:
            columns = row.split(',')
            assert len(columns) == 3

        # Verify metadata
        metadata = export_data["metadata"]
        assert metadata["format"] == "csv"
        assert isinstance(metadata["total_records"], int)

    def test_export_confidence_report_with_date_filters(self, test_vacancy):
        """Test confidence report export with date range filters."""
        export_request = {
            "format": "json",
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-12-31T23:59:59Z",
            "include_metadata": True,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/confidence-dashboard/export",
            json=export_request
        )

        assert response.status_code == 200

        export_data = response.json()
        assert "format" in export_data
        assert "metadata" in export_data

        # Verify date filters are recorded in metadata
        metadata = export_data["metadata"]
        assert metadata["start_date"] == "2024-01-01T00:00:00Z"
        assert metadata["end_date"] == "2024-12-31T23:59:59Z"

    def test_export_confidence_report_with_vacancy_filter(self, test_vacancy):
        """Test confidence report export filtered by vacancy."""
        export_request = {
            "format": "json",
            "vacancy_id": test_vacancy["id"],
            "include_metadata": True,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/confidence-dashboard/export",
            json=export_request
        )

        assert response.status_code == 200

        export_data = response.json()

        # Verify vacancy filter is recorded in metadata
        metadata = export_data["metadata"]
        assert metadata["filters_applied"]["vacancy_id"] == test_vacancy["id"]

    def test_export_confidence_report_without_metadata(self, test_vacancy):
        """Test confidence report export without metadata."""
        export_request = {
            "format": "json",
            "include_metadata": False,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/confidence-dashboard/export",
            json=export_request
        )

        assert response.status_code == 200

        export_data = response.json()
        assert "format" in export_data
        assert "data" in export_data

        # Verify metadata is not included
        assert "metadata" not in export_data

    def test_export_defaults_to_json(self, test_vacancy):
        """Test that export defaults to JSON format when not specified."""
        export_request = {}

        response = requests.post(
            f"{self.BASE_URL}/api/confidence-dashboard/export",
            json=export_request
        )

        assert response.status_code == 200

        export_data = response.json()
        assert export_data["format"] == "json"
        assert isinstance(export_data["data"], dict)

    def test_confidence_metrics_consistency(self, test_vacancy, test_resumes):
        """Test that confidence metrics are consistent across multiple requests."""
        # Make multiple requests
        responses = []
        for _ in range(3):
            response = requests.get(
                f"{self.BASE_URL}/api/confidence-dashboard/metrics"
            )
            assert response.status_code == 200
            responses.append(response.json())

        # Verify all responses are identical (no random variation)
        for i in range(1, len(responses)):
            assert responses[i]["average_confidence"] == responses[0]["average_confidence"]
            assert responses[i]["total_rankings"] == responses[0]["total_rankings"]

    def test_concurrent_export_requests(self, test_vacancy):
        """Test that multiple concurrent export requests are handled properly."""
        import concurrent.futures

        def make_export_request(format_type):
            return requests.post(
                f"{self.BASE_URL}/api/confidence-dashboard/export",
                json={
                    "format": format_type,
                    "include_metadata": True,
                }
            )

        # Send concurrent requests with different formats
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(make_export_request, "json"),
                executor.submit(make_export_request, "csv"),
                executor.submit(make_export_request, "json"),
            ]

            results = [
                future.result()
                for future in concurrent.futures.as_completed(futures)
            ]

        # All requests should complete successfully
        for result in results:
            assert result.status_code == 200

        # Verify formats are correct
        json_count = sum(1 for r in results if r.json()["format"] == "json")
        csv_count = sum(1 for r in results if r.json()["format"] == "csv")

        assert json_count == 2
        assert csv_count == 1

    def test_error_handling_invalid_vacancy_id(self):
        """Test error handling with invalid vacancy UUID."""
        fake_id = str(uuid4())

        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/metrics",
            params={"vacancy_id": fake_id}
        )

        # Should still return 200 with empty/default metrics
        # (Not 404, as metrics endpoint is always available)
        assert response.status_code == 200

    def test_error_handling_invalid_date_format(self):
        """Test error handling with invalid date format."""
        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/metrics",
            params={
                "start_date": "not-a-date",
                "end_date": "also-not-a-date",
            }
        )

        # Should still return 200 (ignoring invalid dates)
        # or return 422 for validation error
        assert response.status_code in [200, 422]

    def test_error_handling_invalid_export_format(self, test_vacancy):
        """Test error handling with invalid export format."""
        export_request = {
            "format": "xml",  # Not supported
            "include_metadata": True,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/confidence-dashboard/export",
            json=export_request
        )

        # Should return 422 validation error
        assert response.status_code == 422

    def test_distribution_totals_match(self, test_vacancy):
        """Test that distribution counts match total rankings."""
        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/metrics"
        )

        assert response.status_code == 200

        metrics = response.json()
        distribution = metrics["distribution"]

        # Total of high/medium/low should equal total rankings
        distribution_total = (
            distribution["high_confidence"]
            + distribution["medium_confidence"]
            + distribution["low_confidence"]
        )

        assert distribution_total == metrics["total_rankings"]

    def test_confidence_correlation_accuracy_ordering(self, test_vacancy):
        """Test that confidence levels correlate with accuracy (high > medium > low)."""
        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/ai-human-comparison"
        )

        assert response.status_code == 200

        comparison = response.json()
        correlation = comparison["confidence_correlation"]

        # High confidence should have higher accuracy than medium
        assert correlation["high_confidence_accuracy"] >= correlation["medium_confidence_accuracy"]

        # Medium confidence should have higher accuracy than low
        assert correlation["medium_confidence_accuracy"] >= correlation["low_confidence_accuracy"]

    def test_export_csv_data_integrity(self, test_vacancy):
        """Test that CSV export contains all expected sections."""
        export_request = {
            "format": "csv",
            "include_metadata": True,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/confidence-dashboard/export",
            json=export_request
        )

        assert response.status_code == 200

        export_data = response.json()
        csv_content = export_data["data"]

        # Verify all expected sections are present in CSV
        expected_sections = [
            "summary_metrics",
            "distribution",
            "uncertainty",
            "model_accuracy",
            "ai_human_comparison",
        ]

        for section in expected_sections:
            assert section in csv_content, f"Section {section} missing from CSV export"


class TestConfidenceDashboardErrorHandling:
    """Tests for error handling and edge cases."""

    BASE_URL = "http://localhost:8000"

    def test_metrics_endpoint_always_available(self):
        """Test that metrics endpoint is always available even with no data."""
        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/metrics"
        )

        # Should return 200 with placeholder/default data
        assert response.status_code == 200

        metrics = response.json()
        assert "average_confidence" in metrics
        assert "total_rankings" in metrics

    def test_comparison_endpoint_always_available(self):
        """Test that comparison endpoint is always available even with no data."""
        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/ai-human-comparison"
        )

        # Should return 200 with placeholder/default data
        assert response.status_code == 200

        comparison = response.json()
        assert "agreement" in comparison
        assert "efficiency" in comparison

    def test_export_endpoint_handles_empty_request(self):
        """Test that export endpoint handles empty request body."""
        response = requests.post(
            f"{self.BASE_URL}/api/confidence-dashboard/export",
            json={}
        )

        # Should return 200 with default JSON format
        assert response.status_code == 200

        export_data = response.json()
        assert export_data["format"] == "json"

    def test_metrics_response_time(self):
        """Test that metrics endpoint responds within acceptable time."""
        import time

        start = time.time()
        response = requests.get(
            f"{self.BASE_URL}/api/confidence-dashboard/metrics"
        )
        end = time.time()

        assert response.status_code == 200

        # Response should be within 2 seconds
        response_time = end - start
        assert response_time < 2.0

    def test_export_response_time(self):
        """Test that export endpoint responds within acceptable time."""
        import time

        export_request = {
            "format": "csv",
            "include_metadata": True,
        }

        start = time.time()
        response = requests.post(
            f"{self.BASE_URL}/api/confidence-dashboard/export",
            json=export_request
        )
        end = time.time()

        assert response.status_code == 200

        # Response should be within 3 seconds
        response_time = end - start
        assert response_time < 3.0
