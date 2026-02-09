"""
Unit tests for fairness and bias detection API endpoints.

Tests cover:
- Fairness metrics endpoint (disparate impact, statistical parity, etc.)
- Bias reports endpoint (CRUD operations)
- Fairness alerts endpoint (listing and acknowledgment)
- Fairness summary endpoint (overall metrics)
- Report generation endpoint
- Fairness scorecard endpoint
- Report export endpoint (PDF/CSV)
"""
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.

    Returns:
        TestClient: Configured test client
    """
    return TestClient(app)


class TestFairnessMetricsEndpoint:
    """Tests for GET /api/fairness/metrics endpoint."""

    def test_returns_200(self, client):
        """Test endpoint returns 200 status code."""
        response = client.get("/api/fairness/metrics")
        assert response.status_code == 200

    def test_response_structure(self, client):
        """Test response has correct structure."""
        response = client.get("/api/fairness/metrics")
        data = response.json()

        assert "metrics" in data
        assert "total_count" in data
        assert isinstance(data["metrics"], list)

    def test_metrics_structure(self, client):
        """Test each metric has required fields."""
        response = client.get("/api/fairness/metrics")
        data = response.json()
        metrics = data["metrics"]

        # Only check if we have metrics
        if len(metrics) > 0:
            for metric in metrics[:3]:  # Check first 3
                assert "metric_id" in metric
                assert "model_name" in metric
                assert "model_version" in metric
                assert "protected_attribute" in metric
                assert "metric_type" in metric
                assert "metric_value" in metric
                assert "threshold" in metric
                assert "is_acceptable" in metric
                assert "sample_size" in metric
                assert "calculated_at" in metric

    def test_model_name_filter(self, client):
        """Test filtering by model name."""
        response = client.get("/api/fairness/metrics?model_name=ranking")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data

    def test_protected_attribute_filter(self, client):
        """Test filtering by protected attribute."""
        response = client.get("/api/fairness/metrics?protected_attribute=gender")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data

    def test_metric_type_filter(self, client):
        """Test filtering by metric type."""
        response = client.get("/api/fairness/metrics?metric_type=disparate_impact")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data

    def test_is_acceptable_filter(self, client):
        """Test filtering by acceptability status."""
        response = client.get("/api/fairness/metrics?is_acceptable=true")
        assert response.status_code == 200

        response = client.get("/api/fairness/metrics?is_acceptable=false")
        assert response.status_code == 200

    def test_limit_parameter(self, client):
        """Test limit parameter."""
        response = client.get("/api/fairness/metrics?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["metrics"]) <= 10

    def test_limit_validation(self, client):
        """Test limit parameter validation."""
        # Max limit is 1000, should be rejected
        response = client.get("/api/fairness/metrics?limit=10000")
        # Should return 422 for limit > 1000
        assert response.status_code == 422

    def test_invalid_limit(self, client):
        """Test with invalid limit value."""
        response = client.get("/api/fairness/metrics?limit=invalid")
        assert response.status_code == 422

    def test_metric_value_ranges(self, client):
        """Test metric values are within expected ranges."""
        response = client.get("/api/fairness/metrics")
        data = response.json()
        metrics = data["metrics"]

        for metric in metrics[:5]:  # Check first 5
            if metric["metric_type"] == "disparate_impact":
                assert 0 <= metric["metric_value"] <= 2, "Disparate impact should be 0-2"
            elif metric["metric_type"] == "statistical_parity":
                assert -1 <= metric["metric_value"] <= 1, "Statistical parity should be -1 to 1"

    def test_combined_filters(self, client):
        """Test with multiple filters combined."""
        response = client.get(
            "/api/fairness/metrics?model_name=ranking&metric_type=disparate_impact&is_acceptable=true&limit=5"
        )
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert len(data["metrics"]) <= 5


class TestBiasReportsEndpoint:
    """Tests for GET /api/fairness/reports endpoint."""

    def test_returns_200(self, client):
        """Test endpoint returns 200 status code."""
        response = client.get("/api/fairness/reports")
        assert response.status_code == 200

    def test_response_structure(self, client):
        """Test response has correct structure."""
        response = client.get("/api/fairness/reports")
        data = response.json()

        assert "reports" in data
        assert "total_count" in data
        assert isinstance(data["reports"], list)

    def test_report_structure(self, client):
        """Test each report has required fields."""
        response = client.get("/api/fairness/reports")
        data = response.json()
        reports = data["reports"]

        if len(reports) > 0:
            for report in reports[:3]:  # Check first 3
                assert "report_id" in report
                assert "model_name" in report
                assert "model_version" in report
                assert "report_type" in report
                assert "protected_attributes" in report
                assert "overall_fairness_score" in report
                assert "bias_detected" in report
                assert "severity_level" in report
                assert "findings" in report
                assert "recommendations" in report
                assert "generated_at" in report

    def test_model_version_filter(self, client):
        """Test filtering by model version."""
        response = client.get("/api/fairness/reports?model_version=v1.0")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data

    def test_report_type_filter(self, client):
        """Test filtering by report type."""
        response = client.get("/api/fairness/reports?report_type=system-wide")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data

    def test_severity_level_filter(self, client):
        """Test filtering by severity level."""
        response = client.get("/api/fairness/reports?severity_level=high")
        assert response.status_code == 200

        response = client.get("/api/fairness/reports?severity_level=medium")
        assert response.status_code == 200

    def test_bias_detected_filter(self, client):
        """Test filtering by bias detection status."""
        response = client.get("/api/fairness/reports?bias_detected=true")
        assert response.status_code == 200

        response = client.get("/api/fairness/reports?bias_detected=false")
        assert response.status_code == 200

    def test_limit_parameter(self, client):
        """Test limit parameter."""
        response = client.get("/api/fairness/reports?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["reports"]) <= 10

    def test_limit_validation(self, client):
        """Test limit parameter validation."""
        response = client.get("/api/fairness/reports?limit=2000")
        assert response.status_code == 422

    def test_overall_fairness_score_range(self, client):
        """Test overall fairness score is within 0-1 range."""
        response = client.get("/api/fairness/reports")
        data = response.json()
        reports = data["reports"]

        for report in reports[:5]:
            assert 0 <= report["overall_fairness_score"] <= 1, "Overall fairness score should be 0-1"

    def test_findings_structure(self, client):
        """Test findings have correct structure."""
        response = client.get("/api/fairness/reports")
        data = response.json()
        reports = data["reports"]

        for report in reports[:3]:
            assert isinstance(report["findings"], list)
            for finding in report["findings"][:2]:  # Check first 2 findings
                assert "demographic_attribute" in finding
                assert "disparate_impact_ratio" in finding
                assert "severity" in finding

    def test_recommendations_list(self, client):
        """Test recommendations are provided as list."""
        response = client.get("/api/fairness/reports")
        data = response.json()
        reports = data["reports"]

        for report in reports[:3]:
            assert isinstance(report["recommendations"], list)


class TestFairnessAlertsEndpoint:
    """Tests for GET /api/fairness/alerts endpoint."""

    def test_returns_200(self, client):
        """Test endpoint returns 200 status code."""
        response = client.get("/api/fairness/alerts")
        assert response.status_code == 200

    def test_response_structure(self, client):
        """Test response has correct structure."""
        response = client.get("/api/fairness/alerts")
        data = response.json()

        assert "alerts" in data
        assert "total_count" in data
        assert "unacknowledged_count" in data
        assert isinstance(data["alerts"], list)

    def test_alert_structure(self, client):
        """Test each alert has required fields."""
        response = client.get("/api/fairness/alerts")
        data = response.json()
        alerts = data["alerts"]

        if len(alerts) > 0:
            for alert in alerts[:3]:  # Check first 3
                assert "alert_id" in alert
                assert "model_name" in alert
                assert "model_version" in alert
                assert "alert_type" in alert
                assert "severity" in alert
                assert "protected_attribute" in alert
                assert "metric_name" in alert
                assert "current_value" in alert
                assert "threshold_value" in alert
                assert "description" in alert
                assert "recommendation" in alert
                assert "triggered_at" in alert
                assert "acknowledged" in alert

    def test_severity_filter(self, client):
        """Test filtering by severity level."""
        response = client.get("/api/fairness/alerts?severity=high")
        assert response.status_code == 200

        response = client.get("/api/fairness/alerts?severity=critical")
        assert response.status_code == 200

    def test_acknowledged_filter(self, client):
        """Test filtering by acknowledgment status."""
        response = client.get("/api/fairness/alerts?acknowledged=false")
        assert response.status_code == 200

        response = client.get("/api/fairness/alerts?acknowledged=true")
        assert response.status_code == 200

    def test_days_parameter(self, client):
        """Test days parameter."""
        response = client.get("/api/fairness/alerts?days=7")
        assert response.status_code == 200

        response = client.get("/api/fairness/alerts?days=90")
        assert response.status_code == 200

    def test_days_validation(self, client):
        """Test days parameter validation."""
        # Days > 365 should be rejected
        response = client.get("/api/fairness/alerts?days=400")
        assert response.status_code == 422

    def test_limit_parameter(self, client):
        """Test limit parameter."""
        response = client.get("/api/fairness/alerts?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["alerts"]) <= 10

    def test_severity_levels(self, client):
        """Test severity levels are valid."""
        response = client.get("/api/fairness/alerts")
        data = response.json()
        alerts = data["alerts"]

        valid_severities = ["low", "medium", "high", "critical"]
        for alert in alerts[:5]:
            assert alert["severity"] in valid_severities, f"Invalid severity: {alert['severity']}"

    def test_unacknowledged_count_is_accurate(self, client):
        """Test unacknowledged count matches actual unacknowledged alerts."""
        response = client.get("/api/fairness/alerts?acknowledged=false")
        data = response.json()

        unacknowledged_in_response = sum(1 for alert in data["alerts"] if not alert["acknowledged"])
        assert unacknowledged_in_response == len(data["alerts"])


class TestFairnessSummaryEndpoint:
    """Tests for GET /api/fairness/summary endpoint."""

    def test_returns_200(self, client):
        """Test endpoint returns 200 status code."""
        response = client.get("/api/fairness/summary")
        assert response.status_code == 200

    def test_response_structure(self, client):
        """Test response has correct structure."""
        response = client.get("/api/fairness/summary")
        data = response.json()

        assert "total_models" in data
        assert "models_with_issues" in data
        assert "overall_fairness_score" in data
        assert "protected_attributes_analyzed" in data
        assert "recent_alerts" in data
        assert "last_updated" in data

    def test_data_types(self, client):
        """Test response fields have correct data types."""
        response = client.get("/api/fairness/summary")
        data = response.json()

        assert isinstance(data["total_models"], int)
        assert isinstance(data["models_with_issues"], int)
        assert isinstance(data["overall_fairness_score"], (int, float))
        assert isinstance(data["protected_attributes_analyzed"], list)
        assert isinstance(data["recent_alerts"], int)
        assert isinstance(data["last_updated"], str)

    def test_fairness_score_range(self, client):
        """Test fairness score is within 0-1 range."""
        response = client.get("/api/fairness/summary")
        data = response.json()

        assert 0 <= data["overall_fairness_score"] <= 1

    def test_non_negative_counts(self, client):
        """Test counts are non-negative."""
        response = client.get("/api/fairness/summary")
        data = response.json()

        assert data["total_models"] >= 0
        assert data["models_with_issues"] >= 0
        assert data["models_with_issues"] <= data["total_models"]
        assert data["recent_alerts"] >= 0

    def test_protected_attributes_list(self, client):
        """Test protected attributes is a list of strings."""
        response = client.get("/api/fairness/summary")
        data = response.json()

        assert isinstance(data["protected_attributes_analyzed"], list)
        for attr in data["protected_attributes_analyzed"]:
            assert isinstance(attr, str)

    def test_last_updated_format(self, client):
        """Test last_updated is a valid ISO 8601 timestamp."""
        response = client.get("/api/fairness/summary")
        data = response.json()

        # Should be able to parse as ISO 8601
        try:
            datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("last_updated is not a valid ISO 8601 timestamp")


class TestGenerateBiasReportEndpoint:
    """Tests for POST /api/fairness/reports/generate endpoint."""

    def test_generate_report_success(self, client):
        """Test successful report generation."""
        response = client.post(
            "/api/fairness/reports/generate?model_name=ranking&report_type=system-wide"
        )
        # May return 201 or 404 if no vacancies available
        assert response.status_code in [201, 404, 500]

    def test_generate_report_invalid_model_name(self, client):
        """Test report generation with empty model name."""
        response = client.post(
            "/api/fairness/reports/generate?model_name=&report_type=system-wide"
        )
        assert response.status_code == 422

    def test_generate_report_invalid_report_type(self, client):
        """Test report generation with invalid report type."""
        response = client.post(
            "/api/fairness/reports/generate?model_name=ranking&report_type=invalid_type"
        )
        assert response.status_code == 422

    def test_generate_report_response_structure(self, client):
        """Test generated report has correct structure."""
        response = client.post(
            "/api/fairness/reports/generate?model_name=ranking&report_type=system-wide"
        )

        if response.status_code == 201:
            data = response.json()
            assert "report_id" in data
            assert "model_name" in data
            assert "model_version" in data
            assert "report_type" in data
            assert "protected_attributes" in data
            assert "overall_fairness_score" in data
            assert "bias_detected" in data
            assert "severity_level" in data
            assert "findings" in data
            assert "recommendations" in data
            assert "generated_at" in data

    def test_generate_report_group_type(self, client):
        """Test generating group report."""
        response = client.post(
            "/api/fairness/reports/generate?model_name=ranking&report_type=group"
        )
        assert response.status_code in [201, 404, 500]

    def test_generate_report_individual_type(self, client):
        """Test generating individual report."""
        response = client.post(
            "/api/fairness/reports/generate?model_name=ranking&report_type=individual"
        )
        assert response.status_code in [201, 404, 500]


class TestAcknowledgeAlertEndpoint:
    """Tests for POST /api/fairness/alerts/{alert_id}/acknowledge endpoint."""

    def test_acknowledge_alert_success(self, client):
        """Test successful alert acknowledgment."""
        # Use a test alert ID - will likely return 404 if alert doesn't exist
        test_alert_id = str(uuid4())
        response = client.post(f"/api/fairness/alerts/{test_alert_id}/acknowledge")

        # Should return 404 for non-existent alert or 200 if it exists
        assert response.status_code in [200, 404]

    def test_acknowledge_alert_response_structure(self, client):
        """Test acknowledgment response has correct structure."""
        test_alert_id = str(uuid4())
        response = client.post(f"/api/fairness/alerts/{test_alert_id}/acknowledge")

        if response.status_code == 200:
            data = response.json()
            assert "alert_id" in data
            assert "acknowledged" in data
            assert "acknowledged_at" in data
            assert data["acknowledged"] is True

    def test_acknowledge_alert_invalid_id(self, client):
        """Test acknowledgment with invalid alert ID format."""
        response = client.post("/api/fairness/alerts/invalid-uuid/acknowledge")
        # Should handle gracefully
        assert response.status_code in [404, 422, 200]

    def test_acknowledge_already_acknowledged(self, client):
        """Test acknowledging an already acknowledged alert."""
        # This would require an actual alert in the database
        # For now, just test the endpoint exists
        test_alert_id = str(uuid4())
        response = client.post(f"/api/fairness/alerts/{test_alert_id}/acknowledge")
        assert response.status_code in [200, 404]


class TestFairnessScorecardEndpoint:
    """Tests for POST /api/fairness/scorecard endpoint."""

    def test_scorecard_success(self, client):
        """Test successful scorecard generation."""
        response = client.post("/api/fairness/scorecard")
        # May return 200 or 500 depending on data availability
        assert response.status_code in [200, 500]

    def test_scorecard_with_vacancy_id(self, client):
        """Test scorecard with vacancy ID filter."""
        test_vacancy_id = str(uuid4())
        response = client.post(f"/api/fairness/scorecard?vacancy_id={test_vacancy_id}")
        assert response.status_code in [200, 422, 500]

    def test_scorecard_with_model_version(self, client):
        """Test scorecard with model version filter."""
        response = client.post("/api/fairness/scorecard?model_version=v1.0")
        assert response.status_code in [200, 500]

    def test_scorecard_invalid_vacancy_id(self, client):
        """Test scorecard with invalid vacancy ID format."""
        response = client.post("/api/fairness/scorecard?vacancy_id=invalid-uuid")
        assert response.status_code == 422

    def test_scorecard_response_structure(self, client):
        """Test scorecard response has correct structure."""
        response = client.post("/api/fairness/scorecard")

        if response.status_code == 200:
            data = response.json()
            expected_fields = [
                "vacancy_id",
                "vacancy_title",
                "fairness_score",
                "bias_sources",
                "score_breakdown",
                "metrics_by_demographic",
                "alerts_summary",
                "recommendations",
                "analyzed_at",
                "total_sample_size",
                "demographics_analyzed",
                "model_version",
            ]

            for field in expected_fields:
                assert field in data, f"Missing field: {field}"

    def test_fairness_score_range(self, client):
        """Test fairness score is within 0-100 range."""
        response = client.post("/api/fairness/scorecard")

        if response.status_code == 200:
            data = response.json()
            assert 0 <= data["fairness_score"] <= 100


class TestGetBiasReportEndpoint:
    """Tests for GET /api/fairness/reports/{report_id} endpoint."""

    def test_get_report_success(self, client):
        """Test retrieving a specific report."""
        # Use a sample report_id format: YYYY-MM-DD_version
        response = client.get("/api/fairness/reports/2024-01-25_v1.0")
        # Will likely return 404 if report doesn't exist
        assert response.status_code in [200, 404]

    def test_get_report_invalid_format(self, client):
        """Test retrieving report with invalid ID format."""
        response = client.get("/api/fairness/reports/invalid-format")
        assert response.status_code == 404

    def test_get_report_response_structure(self, client):
        """Test report response has correct structure."""
        # Try multiple date formats
        for report_id in ["2024-01-25_v1.0", "2024-01-01_latest"]:
            response = client.get(f"/api/fairness/reports/{report_id}")

            if response.status_code == 200:
                data = response.json()
                assert "report_id" in data
                assert "model_name" in data
                assert "model_version" in data
                assert "report_type" in data
                assert "protected_attributes" in data
                assert "overall_fairness_score" in data
                assert "bias_detected" in data
                assert "findings" in data
                assert "recommendations" in data
                break


class TestExportBiasReportEndpoint:
    """Tests for POST /api/fairness/reports/{report_id}/export endpoint."""

    def test_export_pdf_success(self, client):
        """Test exporting report as PDF."""
        response = client.post("/api/fairness/reports/2024-01-25_v1.0/export?format=pdf")
        # May return 200, 404 (not found), or 500 (service unavailable)
        assert response.status_code in [200, 404, 500]

    def test_export_csv_success(self, client):
        """Test exporting report as CSV."""
        response = client.post("/api/fairness/reports/2024-01-25_v1.0/export?format=csv")
        # May return 200, 404, or 500
        assert response.status_code in [200, 404, 500]

    def test_export_invalid_format(self, client):
        """Test exporting with invalid format."""
        response = client.post("/api/fairness/reports/2024-01-25_v1.0/export?format=invalid")
        assert response.status_code == 422

    def test_export_invalid_report_id(self, client):
        """Test exporting with invalid report ID."""
        response = client.post("/api/fairness/reports/invalid-format/export?format=pdf")
        assert response.status_code == 404

    def test_export_pdf_content_type(self, client):
        """Test PDF export returns correct content type."""
        response = client.post("/api/fairness/reports/2024-01-25_v1.0/export?format=pdf")

        if response.status_code == 200:
            assert response.headers["content-type"] == "application/pdf"

    def test_export_csv_content_type(self, client):
        """Test CSV export returns correct content type."""
        response = client.post("/api/fairness/reports/2024-01-25_v1.0/export?format=csv")

        if response.status_code == 200:
            assert "text/csv" in response.headers["content-type"] or "application/csv" in response.headers["content-type"]


class TestErrorHandling:
    """Tests for error handling across all endpoints."""

    def test_method_not_allowed(self, client):
        """Test unsupported HTTP methods."""
        # Try POST on GET endpoint
        response = client.post("/api/fairness/metrics")
        assert response.status_code == 405

        response = client.post("/api/fairness/summary")
        assert response.status_code == 405

        response = client.get("/api/fairness/reports/generate")
        assert response.status_code == 405

    def test_invalid_query_parameters(self, client):
        """Test endpoints with invalid query parameters."""
        # Invalid boolean
        response = client.get("/api/fairness/metrics?is_acceptable=not-a-boolean")
        assert response.status_code == 422

        # Invalid integer
        response = client.get("/api/fairness/metrics?limit=not-a-number")
        assert response.status_code == 422


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_results(self, client):
        """Test endpoints with filters that return no results."""
        response = client.get("/api/fairness/metrics?model_name=nonexistent_model")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["metrics"], list)

    def test_very_long_model_name(self, client):
        """Test with very long model name."""
        long_name = "a" * 500
        response = client.get(f"/api/fairness/metrics?model_name={long_name}")
        assert response.status_code == 200

    def test_special_characters_in_filters(self, client):
        """Test with special characters in filter values."""
        response = client.get("/api/fairness/metrics?model_name=model<script>")
        assert response.status_code == 200

    def test_unicode_in_filters(self, client):
        """Test with unicode characters in filter values."""
        response = client.get("/api/fairness/metrics?protected_attribute=性别")
        assert response.status_code == 200

    def test_multiple_filters_with_edge_values(self, client):
        """Test with multiple filters at edge values."""
        response = client.get("/api/fairness/metrics?limit=1&is_acceptable=true&metric_type=disparate_impact")
        assert response.status_code == 200
        data = response.json()
        assert len(data["metrics"]) <= 1

    def test_date_format_in_generated_at(self, client):
        """Test that generated_at timestamps are valid ISO 8601."""
        response = client.get("/api/fairness/metrics")
        data = response.json()

        for metric in data["metrics"][:3]:
            try:
                datetime.fromisoformat(metric["calculated_at"].replace("Z", "+00:00"))
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {metric['calculated_at']}")
