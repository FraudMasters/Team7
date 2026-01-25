"""
Unit tests for analytics and reports API endpoints.

Tests cover:
- Key metrics endpoint (time-to-hire, resumes processed, match rates)
- Funnel visualization endpoint
- Skill demand analytics endpoint
- Source tracking endpoint
- Recruiter performance endpoint
- Report CRUD endpoints
- PDF/CSV export endpoints
- Date range filtering validation
"""
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.

    Returns:
        TestClient: Configured test client
    """
    return TestClient(app)


class TestValidateDateRange:
    """Tests for validate_date_range utility function."""

    def test_no_date_parameters(self, client):
        """Test when no date parameters are provided."""
        response = client.get("/api/analytics/key-metrics")
        assert response.status_code == 200

    def test_valid_start_date_only(self, client):
        """Test with only start_date provided."""
        response = client.get("/api/analytics/key-metrics?start_date=2024-01-01")
        assert response.status_code == 200

    def test_valid_end_date_only(self, client):
        """Test with only end_date provided."""
        response = client.get("/api/analytics/key-metrics?end_date=2024-12-31")
        assert response.status_code == 200

    def test_valid_date_range(self, client):
        """Test with valid start_date and end_date."""
        response = client.get(
            "/api/analytics/key-metrics?start_date=2024-01-01&end_date=2024-12-31"
        )
        assert response.status_code == 200

    def test_invalid_start_date_format(self, client):
        """Test with invalid start_date format."""
        response = client.get("/api/analytics/key-metrics?start_date=invalid-date")
        assert response.status_code == 422
        assert "Invalid start_date format" in response.json()["detail"]

    def test_invalid_end_date_format(self, client):
        """Test with invalid end_date format."""
        response = client.get("/api/analytics/key-metrics?end_date=2024-13-45")
        assert response.status_code == 422
        assert "Invalid end_date format" in response.json()["detail"]

    def test_start_date_after_end_date(self, client):
        """Test when start_date is after end_date."""
        response = client.get(
            "/api/analytics/key-metrics?start_date=2024-12-31&end_date=2024-01-01"
        )
        assert response.status_code == 422
        assert "must be before or equal to end_date" in response.json()["detail"]

    def test_iso8601_date_format(self, client):
        """Test with ISO 8601 datetime format."""
        response = client.get(
            "/api/analytics/key-metrics?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z"
        )
        assert response.status_code == 200

    def test_same_start_and_end_date(self, client):
        """Test when start_date equals end_date."""
        response = client.get(
            "/api/analytics/key-metrics?start_date=2024-01-01&end_date=2024-01-01"
        )
        assert response.status_code == 200


class TestKeyMetricsEndpoint:
    """Tests for GET /api/analytics/key-metrics endpoint."""

    def test_returns_200(self, client):
        """Test endpoint returns 200 status code."""
        response = client.get("/api/analytics/key-metrics")
        assert response.status_code == 200

    def test_response_structure(self, client):
        """Test response has correct structure."""
        response = client.get("/api/analytics/key-metrics")
        data = response.json()

        assert "time_to_hire" in data
        assert "resumes" in data
        assert "match_rates" in data

    def test_time_to_hire_metrics(self, client):
        """Test time-to-hire metrics are present and valid."""
        response = client.get("/api/analytics/key-metrics")
        data = response.json()
        tth = data["time_to_hire"]

        assert "average_days" in tth
        assert "median_days" in tth
        assert "min_days" in tth
        assert "max_days" in tth
        assert "percentile_25" in tth
        assert "percentile_75" in tth
        assert tth["min_days"] >= 0
        assert tth["max_days"] >= tth["min_days"]

    def test_resume_metrics(self, client):
        """Test resume metrics are present and valid."""
        response = client.get("/api/analytics/key-metrics")
        data = response.json()
        resumes = data["resumes"]

        assert "total_processed" in resumes
        assert "processed_this_month" in resumes
        assert "processed_this_week" in resumes
        assert "processing_rate_avg" in resumes
        assert resumes["total_processed"] >= 0

    def test_match_rate_metrics(self, client):
        """Test match rate metrics are present and valid."""
        response = client.get("/api/analytics/key-metrics")
        data = response.json()
        match_rates = data["match_rates"]

        assert "overall_match_rate" in match_rates
        assert "high_confidence_matches" in match_rates
        assert "low_confidence_matches" in match_rates
        assert "average_confidence" in match_rates
        assert 0 <= match_rates["overall_match_rate"] <= 1

    def test_with_date_filter(self, client):
        """Test endpoint with date range filter."""
        response = client.get(
            "/api/analytics/key-metrics?start_date=2024-01-01&end_date=2024-12-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert "time_to_hire" in data


class TestFunnelMetricsEndpoint:
    """Tests for GET /api/analytics/funnel endpoint."""

    def test_returns_200(self, client):
        """Test endpoint returns 200 status code."""
        response = client.get("/api/analytics/funnel")
        assert response.status_code == 200

    def test_response_structure(self, client):
        """Test response has correct structure."""
        response = client.get("/api/analytics/funnel")
        data = response.json()

        assert "stages" in data
        assert "total_resumes" in data
        assert "overall_hire_rate" in data
        assert isinstance(data["stages"], list)

    def test_funnel_stages(self, client):
        """Test funnel stages are present."""
        response = client.get("/api/analytics/funnel")
        data = response.json()
        stages = data["stages"]

        stage_names = [s["stage_name"] for s in stages]
        expected_stages = [
            "resumes_uploaded",
            "resumes_processed",
            "candidates_matched",
            "candidates_shortlisted",
            "candidates_interviewed",
            "candidates_hired",
        ]
        for expected in expected_stages:
            assert expected in stage_names

    def test_stage_structure(self, client):
        """Test each stage has required fields."""
        response = client.get("/api/analytics/funnel")
        data = response.json()
        stages = data["stages"]

        for stage in stages:
            assert "stage_name" in stage
            assert "count" in stage
            assert "conversion_rate" in stage
            assert stage["count"] >= 0
            assert 0 <= stage["conversion_rate"] <= 100

    def test_with_date_filter(self, client):
        """Test endpoint with date range filter."""
        response = client.get(
            "/api/analytics/funnel?start_date=2024-01-01&end_date=2024-12-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert "stages" in data


class TestSkillDemandEndpoint:
    """Tests for GET /api/analytics/skill-demand endpoint."""

    def test_returns_200(self, client):
        """Test endpoint returns 200 status code."""
        response = client.get("/api/analytics/skill-demand")
        assert response.status_code == 200

    def test_response_structure(self, client):
        """Test response has correct structure."""
        response = client.get("/api/analytics/skill-demand")
        data = response.json()

        assert "skills" in data
        assert "total_postings_analyzed" in data
        assert isinstance(data["skills"], list)

    def test_skills_structure(self, client):
        """Test each skill has required fields."""
        response = client.get("/api/analytics/skill-demand")
        data = response.json()
        skills = data["skills"]

        if len(skills) > 0:
            for skill in skills:
                assert "skill_name" in skill
                assert "demand_count" in skill
                assert "demand_percentage" in skill
                assert "trend_percentage" in skill
                assert skill["demand_count"] >= 0

    def test_default_limit(self, client):
        """Test default limit is applied."""
        response = client.get("/api/analytics/skill-demand")
        data = response.json()
        skills = data["skills"]

        assert len(skills) <= 20

    def test_custom_limit(self, client):
        """Test custom limit parameter."""
        response = client.get("/api/analytics/skill-demand?limit=5")
        data = response.json()
        skills = data["skills"]

        assert len(skills) <= 5

    def test_limit_validation(self, client):
        """Test limit parameter validation."""
        response = client.get("/api/analytics/skill-demand?limit=150")
        # Should return 422 for limit > 100
        assert response.status_code == 422

    def test_with_date_filter(self, client):
        """Test endpoint with date range filter."""
        response = client.get(
            "/api/analytics/skill-demand?start_date=2024-01-01&end_date=2024-12-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data


class TestSourceTrackingEndpoint:
    """Tests for GET /api/analytics/source-tracking endpoint."""

    def test_returns_200(self, client):
        """Test endpoint returns 200 status code."""
        response = client.get("/api/analytics/source-tracking")
        assert response.status_code == 200

    def test_response_structure(self, client):
        """Test response has correct structure."""
        response = client.get("/api/analytics/source-tracking")
        data = response.json()

        assert "sources" in data
        assert "total_vacancies" in data
        assert isinstance(data["sources"], list)

    def test_sources_structure(self, client):
        """Test each source has required fields."""
        response = client.get("/api/analytics/source-tracking")
        data = response.json()
        sources = data["sources"]

        if len(sources) > 0:
            for source in sources:
                assert "source_name" in source
                assert "vacancy_count" in source
                assert "percentage" in source
                assert "average_time_to_fill" in source
                assert source["vacancy_count"] >= 0

    def test_with_date_filter(self, client):
        """Test endpoint with date range filter."""
        response = client.get(
            "/api/analytics/source-tracking?start_date=2024-01-01&end_date=2024-12-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data


class TestRecruiterPerformanceEndpoint:
    """Tests for GET /api/analytics/recruiter-performance endpoint."""

    def test_returns_200(self, client):
        """Test endpoint returns 200 status code."""
        response = client.get("/api/analytics/recruiter-performance")
        assert response.status_code == 200

    def test_response_structure(self, client):
        """Test response has correct structure."""
        response = client.get("/api/analytics/recruiter-performance")
        data = response.json()

        assert "recruiters" in data
        assert "total_recruiters" in data
        assert isinstance(data["recruiters"], list)

    def test_recruiters_structure(self, client):
        """Test each recruiter has required fields."""
        response = client.get("/api/analytics/recruiter-performance")
        data = response.json()
        recruiters = data["recruiters"]

        if len(recruiters) > 0:
            for recruiter in recruiters:
                assert "recruiter_id" in recruiter
                assert "recruiter_name" in recruiter
                assert "hires" in recruiter
                assert "interviews_conducted" in recruiter
                assert "resumes_processed" in recruiter
                assert "average_time_to_hire" in recruiter
                assert "offer_acceptance_rate" in recruiter
                assert recruiter["hires"] >= 0

    def test_default_limit(self, client):
        """Test default limit is applied."""
        response = client.get("/api/analytics/recruiter-performance")
        data = response.json()
        recruiters = data["recruiters"]

        assert len(recruiters) <= 20

    def test_custom_limit(self, client):
        """Test custom limit parameter."""
        response = client.get("/api/analytics/recruiter-performance?limit=5")
        data = response.json()
        recruiters = data["recruiters"]

        assert len(recruiters) <= 5

    def test_with_date_filter(self, client):
        """Test endpoint with date range filter."""
        response = client.get(
            "/api/analytics/recruiter-performance?start_date=2024-01-01&end_date=2024-12-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert "recruiters" in data


class TestReportCreateEndpoint:
    """Tests for POST /api/reports endpoint."""

    def test_create_report_success(self, client):
        """Test successful report creation."""
        payload = {
            "name": "Weekly Performance Report",
            "description": "Weekly hiring performance metrics",
            "organization_id": "org-123",
            "created_by": "user-456",
            "metrics": ["time_to_hire", "resumes_processed", "match_rates"],
            "filters": {"start_date": "2024-01-01", "end_date": "2024-12-31"},
            "is_public": True,
        }
        response = client.post("/api/reports", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Weekly Performance Report"
        assert data["metrics"] == ["time_to_hire", "resumes_processed", "match_rates"]

    def test_create_report_minimal_payload(self, client):
        """Test report creation with minimal required fields."""
        payload = {
            "name": "Minimal Report",
            "metrics": ["time_to_hire"],
            "filters": {},
        }
        response = client.post("/api/reports", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Report"

    def test_create_report_validation_error(self, client):
        """Test report creation with invalid payload."""
        payload = {
            "name": "Invalid Report",
            # Missing required 'metrics' field
        }
        response = client.post("/api/reports", json=payload)
        assert response.status_code == 422


class TestReportListEndpoint:
    """Tests for GET /api/reports endpoint."""

    def test_list_reports_success(self, client):
        """Test successful report listing."""
        response = client.get("/api/reports")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        assert "total_count" in data
        assert isinstance(data["reports"], list)

    def test_list_reports_by_organization(self, client):
        """Test filtering reports by organization."""
        response = client.get("/api/reports?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data


class TestReportDetailEndpoint:
    """Tests for GET /api/reports/{id} endpoint."""

    def test_get_report_success(self, client):
        """Test successful report retrieval."""
        report_id = "test-report-123"
        response = client.get(f"/api/reports/{report_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == report_id

    def test_get_report_not_found(self, client):
        """Test retrieving non-existent report."""
        report_id = "non-existent-report"
        response = client.get(f"/api/reports/{report_id}")
        # Should return 404 or 200 with placeholder
        assert response.status_code in [200, 404]


class TestReportUpdateEndpoint:
    """Tests for PUT /api/reports/{id} endpoint."""

    def test_update_report_success(self, client):
        """Test successful report update."""
        report_id = "test-report-123"
        payload = {
            "name": "Updated Report Name",
            "description": "Updated description",
        }
        response = client.put(f"/api/reports/{report_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Report Name"


class TestReportDeleteEndpoint:
    """Tests for DELETE /api/reports/{id} endpoint."""

    def test_delete_report_success(self, client):
        """Test successful report deletion."""
        report_id = "test-report-123"
        response = client.delete(f"/api/reports/{report_id}")
        assert response.status_code == 200


class TestPDFExportEndpoint:
    """Tests for POST /api/reports/export/pdf endpoint."""

    def test_export_pdf_success(self, client):
        """Test successful PDF export."""
        payload = {
            "report_id": "test-report-123",
            "data": {"metrics": ["time_to_hire"]},
            "format": "A4",
        }
        response = client.post("/api/reports/export/pdf", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "download_url" in data
        assert "expires_at" in data

    def test_export_pdf_validation_error(self, client):
        """Test PDF export with invalid payload."""
        payload = {
            # Missing required 'report_id' and 'data' fields
        }
        response = client.post("/api/reports/export/pdf", json=payload)
        assert response.status_code == 422


class TestCSVExportEndpoint:
    """Tests for POST /api/reports/export/csv endpoint."""

    def test_export_csv_success(self, client):
        """Test successful CSV export."""
        payload = {
            "metrics": ["time_to_hire", "resumes_processed"],
            "filters": {},
            "format": "standard",
        }
        response = client.post("/api/reports/export/csv", json=payload)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

    def test_export_csv_content(self, client):
        """Test CSV export contains correct content."""
        payload = {
            "metrics": ["time_to_hire"],
            "filters": {},
        }
        response = client.post("/api/reports/export/csv", json=payload)
        assert response.status_code == 200
        content = response.text
        assert "metric" in content.lower()
        assert "value" in content.lower()

    def test_export_csv_validation_error(self, client):
        """Test CSV export with invalid payload."""
        payload = {
            # Missing required 'metrics' field
        }
        response = client.post("/api/reports/export/csv", json=payload)
        assert response.status_code == 422


class TestScheduleReportEndpoint:
    """Tests for POST /api/reports/schedule endpoint."""

    def test_schedule_report_success(self, client):
        """Test successful report scheduling."""
        payload = {
            "name": "Weekly Executive Report",
            "organization_id": "org-123",
            "report_id": None,
            "configuration": {
                "metrics": ["time_to_hire", "resumes_processed"],
                "filters": {},
            },
            "schedule_config": {
                "frequency": "weekly",
                "day_of_week": 1,
                "hour": 9,
                "minute": 0,
            },
            "delivery_config": {
                "format": "pdf",
                "include_charts": True,
                "include_summary": True,
            },
            "recipients": ["manager@example.com", "hr@example.com"],
            "is_active": True,
        }
        response = client.post("/api/reports/schedule", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Weekly Executive Report"
        assert "id" in data

    def test_schedule_report_validation_frequency(self, client):
        """Test scheduling with invalid frequency."""
        payload = {
            "name": "Invalid Schedule",
            "configuration": {"metrics": ["time_to_hire"], "filters": {}},
            "schedule_config": {
                "frequency": "invalid_frequency",  # Invalid
                "hour": 9,
                "minute": 0,
            },
            "delivery_config": {"format": "pdf"},
            "recipients": ["test@example.com"],
        }
        response = client.post("/api/reports/schedule", json=payload)
        assert response.status_code == 422

    def test_schedule_report_validation_email(self, client):
        """Test scheduling with invalid email."""
        payload = {
            "name": "Invalid Email Schedule",
            "configuration": {"metrics": ["time_to_hire"], "filters": {}},
            "schedule_config": {
                "frequency": "daily",
                "hour": 9,
                "minute": 0,
            },
            "delivery_config": {"format": "pdf"},
            "recipients": ["not-an-email"],  # Invalid email
        }
        response = client.post("/api/reports/schedule", json=payload)
        assert response.status_code == 422

    def test_schedule_report_validation_time(self, client):
        """Test scheduling with invalid time."""
        payload = {
            "name": "Invalid Time Schedule",
            "configuration": {"metrics": ["time_to_hire"], "filters": {}},
            "schedule_config": {
                "frequency": "daily",
                "hour": 25,  # Invalid hour
                "minute": 0,
            },
            "delivery_config": {"format": "pdf"},
            "recipients": ["test@example.com"],
        }
        response = client.post("/api/reports/schedule", json=payload)
        assert response.status_code == 422


class TestErrorHandling:
    """Tests for error handling across all endpoints."""

    def test_method_not_allowed(self, client):
        """Test unsupported HTTP methods."""
        response = client.post("/api/analytics/key-metrics")
        assert response.status_code == 405

    def test_invalid_json(self, client):
        """Test endpoints with invalid JSON."""
        response = client.post(
            "/api/reports",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_content_type(self, client):
        """Test POST endpoints without Content-Type."""
        response = client.post(
            "/api/reports",
            data="name=test&metrics=time_to_hire",
        )
        # Should either work or return 415/422
        assert response.status_code in [200, 201, 415, 422]


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_metrics_list(self, client):
        """Test report creation with empty metrics list."""
        payload = {
            "name": "Empty Metrics Report",
            "metrics": [],
            "filters": {},
        }
        response = client.post("/api/reports", json=payload)
        # Should accept empty list or return validation error
        assert response.status_code in [201, 422]

    def test_very_long_report_name(self, client):
        """Test report creation with very long name."""
        long_name = "A" * 500
        payload = {
            "name": long_name,
            "metrics": ["time_to_hire"],
            "filters": {},
        }
        response = client.post("/api/reports", json=payload)
        assert response.status_code == 201

    def test_special_characters_in_name(self, client):
        """Test report creation with special characters."""
        payload = {
            "name": "Report <script>alert('test')</script>",
            "metrics": ["time_to_hire"],
            "filters": {},
        }
        response = client.post("/api/reports", json=payload)
        assert response.status_code == 201

    def test_unicode_in_report_name(self, client):
        """Test report creation with unicode characters."""
        payload = {
            "name": "报告 名称",
            "metrics": ["time_to_hire"],
            "filters": {},
        }
        response = client.post("/api/reports", json=payload)
        assert response.status_code == 201

    def test_large_filters_dict(self, client):
        """Test report with large filters dictionary."""
        large_filters = {f"filter_{i}": f"value_{i}" for i in range(100)}
        payload = {
            "name": "Complex Filters Report",
            "metrics": ["time_to_hire"],
            "filters": large_filters,
        }
        response = client.post("/api/reports", json=payload)
        assert response.status_code == 201
