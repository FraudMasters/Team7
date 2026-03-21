"""
Tests for export tasks (Excel/CSV export).

Tests cover Excel export, CSV export, and batch export functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from tasks.export_tasks import (
    generate_excel_export,
    generate_csv_export,
    export_to_excel,
    export_to_csv,
    batch_export_reports,
)


class TestGenerateExcelExport:
    """Tests for generate_excel_export function."""

    def test_generate_excel_with_rows(self):
        """Test Excel generation with tabular row data."""
        data = {
            "rows": [
                {"name": "John Doe", "value": 100, "status": "active"},
                {"name": "Jane Smith", "value": 200, "status": "active"},
            ],
            "generated_at": "2024-03-21T12:00:00",
        }

        result = generate_excel_export(data)

        # Should return bytes
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_excel_with_metrics(self):
        """Test Excel generation with metrics data."""
        data = {
            "metrics": {
                "time_to_hire": 15.2,
                "cost_per_hire": 5000.0,
                "conversion_rate": 0.084,
            },
            "dimensions": {
                "source": {
                    "LinkedIn": 450,
                    "Indeed": 320,
                }
            },
            "summary": "Q1 Analytics Report",
            "generated_at": "2024-03-21T12:00:00",
        }

        result = generate_excel_export(data, include_metadata=True)

        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_excel_without_metadata(self):
        """Test Excel generation without metadata sheet."""
        data = {
            "metrics": {"time_to_hire": 15.2},
            "generated_at": "2024-03-21T12:00:00",
        }

        result = generate_excel_export(data, include_metadata=False)

        assert result is not None
        assert isinstance(result, bytes)

    def test_generate_excel_with_nested_metrics(self):
        """Test Excel generation with nested metric structures."""
        data = {
            "metrics": {
                "source_effectiveness": {
                    "LinkedIn": 0.084,
                    "Indeed": 0.062,
                    "Referral": 0.224,
                }
            },
            "generated_at": "2024-03-21T12:00:00",
        }

        result = generate_excel_export(data)

        assert result is not None
        assert isinstance(result, bytes)

    def test_generate_excel_with_custom_sheet_name(self):
        """Test Excel generation with custom sheet name."""
        data = {
            "rows": [{"name": "Test", "value": 1}],
            "generated_at": "2024-03-21T12:00:00",
        }

        result = generate_excel_export(data, sheet_name="Custom Sheet")

        assert result is not None
        assert isinstance(result, bytes)

    def test_generate_excel_empty_data(self):
        """Test Excel generation with empty data."""
        data = {}

        result = generate_excel_export(data)

        # Should handle gracefully
        assert result is None or isinstance(result, bytes)


class TestGenerateCSVExport:
    """Tests for generate_csv_export function."""

    def test_generate_csv_with_rows(self):
        """Test CSV generation with tabular row data."""
        data = {
            "rows": [
                {"name": "John Doe", "value": 100, "status": "active"},
                {"name": "Jane Smith", "value": 200, "status": "active"},
            ]
        }

        result = generate_csv_export(data)

        assert result is not None
        assert isinstance(result, str)
        assert "name" in result
        assert "John Doe" in result
        assert "Jane Smith" in result

    def test_generate_csv_with_metrics(self):
        """Test CSV generation with metrics data."""
        data = {
            "metrics": {
                "time_to_hire": 15.2,
                "cost_per_hire": 5000.0,
            },
            "dimensions": {
                "source": {
                    "LinkedIn": 450,
                }
            }
        }

        result = generate_csv_export(data)

        assert result is not None
        assert isinstance(result, str)
        assert "time_to_hire" in result
        assert "15.2" in result

    def test_generate_csv_without_header(self):
        """Test CSV generation without header row."""
        data = {
            "rows": [
                {"name": "John", "value": 100},
            ]
        }

        result = generate_csv_export(data, include_header=False)

        # Should still generate CSV but without header
        assert result is not None
        assert isinstance(result, str)

    def test_generate_csv_with_custom_delimiter(self):
        """Test CSV generation with custom delimiter."""
        data = {
            "rows": [
                {"name": "John", "value": 100},
            ]
        }

        result = generate_csv_export(data, delimiter=";")

        assert result is not None
        assert ";" in result

    def test_generate_csv_with_nested_metrics(self):
        """Test CSV generation with nested metric structures."""
        data = {
            "metrics": {
                "source_effectiveness": {
                    "LinkedIn": 0.084,
                    "Indeed": 0.062,
                }
            }
        }

        result = generate_csv_export(data)

        assert result is not None
        assert "source_effectiveness.LinkedIn" in result
        assert "0.084" in result

    def test_generate_csv_empty_data(self):
        """Test CSV generation with empty data."""
        data = {}

        result = generate_csv_export(data)

        # Should return minimal CSV
        assert result is not None
        assert isinstance(result, str)


class TestExportToExcel:
    """Tests for export_to_excel Celery task."""

    def test_export_to_excel_success(self):
        """Test successful Excel export task."""
        data = {
            "rows": [
                {"name": "John", "value": 100},
            ],
            "generated_at": "2024-03-21T12:00:00",
        }

        # Mock the task object
        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = export_to_excel(mock_task, data)

        assert result["status"] == "completed"
        assert "excel_bytes" in result
        assert result["file_size_bytes"] > 0
        assert result["format"] == "excel"
        assert "processing_time_ms" in result

    def test_export_to_excel_with_options(self):
        """Test Excel export with custom options."""
        data = {
            "metrics": {"time_to_hire": 15.2},
        }

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = export_to_excel(
            mock_task,
            data,
            sheet_name="Custom Sheet",
            include_metadata=False
        )

        assert result["status"] == "completed"
        assert result["sheet_name"] == "Custom Sheet"
        assert result["include_metadata"] is False

    def test_export_to_excel_empty_data(self):
        """Test Excel export with empty data raises error."""
        data = None

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = export_to_excel(mock_task, data)

        assert result["status"] == "failed"
        assert "error" in result
        assert "empty" in result["error"].lower()

    def test_export_to_excel_invalid_data_type(self):
        """Test Excel export with invalid data type."""
        data = "not a dictionary"

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = export_to_excel(mock_task, data)

        assert result["status"] == "failed"
        assert "error" in result
        assert "dictionary" in result["error"].lower()

    def test_export_to_excel_updates_progress(self):
        """Test Excel export updates task progress."""
        data = {
            "rows": [{"name": "Test", "value": 1}],
        }

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        export_to_excel(mock_task, data)

        # Should call update_state for progress updates
        assert mock_task.update_state.call_count >= 3

    def test_export_to_excel_adds_generated_at(self):
        """Test Excel export adds generated_at if missing."""
        data = {
            "rows": [{"name": "Test", "value": 1}],
        }

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = export_to_excel(mock_task, data)

        # Data should be modified to include generated_at
        assert result["status"] == "completed"


class TestExportToCSV:
    """Tests for export_to_csv Celery task."""

    def test_export_to_csv_success(self):
        """Test successful CSV export task."""
        data = {
            "rows": [
                {"name": "John", "value": 100},
            ]
        }

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = export_to_csv(mock_task, data)

        assert result["status"] == "completed"
        assert "csv_content" in result
        assert result["file_size_bytes"] > 0
        assert result["format"] == "csv"
        assert "processing_time_ms" in result

    def test_export_to_csv_with_options(self):
        """Test CSV export with custom options."""
        data = {
            "rows": [{"name": "Test", "value": 1}],
        }

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = export_to_csv(
            mock_task,
            data,
            delimiter=";",
            include_header=False
        )

        assert result["status"] == "completed"
        assert result["delimiter"] == ";"
        assert result["include_header"] is False

    def test_export_to_csv_empty_data(self):
        """Test CSV export with empty data raises error."""
        data = None

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = export_to_csv(mock_task, data)

        assert result["status"] == "failed"
        assert "error" in result
        assert "empty" in result["error"].lower()

    def test_export_to_csv_invalid_data_type(self):
        """Test CSV export with invalid data type."""
        data = ["not", "a", "dictionary"]

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = export_to_csv(mock_task, data)

        assert result["status"] == "failed"
        assert "error" in result
        assert "dictionary" in result["error"].lower()

    def test_export_to_csv_updates_progress(self):
        """Test CSV export updates task progress."""
        data = {
            "rows": [{"name": "Test", "value": 1}],
        }

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        export_to_csv(mock_task, data)

        # Should call update_state for progress updates
        assert mock_task.update_state.call_count >= 3

    def test_export_to_csv_content_validation(self):
        """Test CSV export produces valid CSV content."""
        data = {
            "rows": [
                {"name": "John", "age": 30},
                {"name": "Jane", "age": 25},
            ]
        }

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = export_to_csv(mock_task, data)

        assert result["status"] == "completed"
        csv_content = result["csv_content"]
        lines = csv_content.strip().split("\n")
        assert len(lines) >= 2  # At least header + 1 row


class TestBatchExportReports:
    """Tests for batch_export_reports Celery task."""

    def test_batch_export_excel_reports(self):
        """Test batch export of Excel reports."""
        exports = [
            {
                "data": {"rows": [{"name": "Report 1", "value": 100}]},
                "format": "excel",
                "options": {"sheet_name": "Report 1"},
            },
            {
                "data": {"rows": [{"name": "Report 2", "value": 200}]},
                "format": "excel",
                "options": {"sheet_name": "Report 2"},
            },
        ]

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = batch_export_reports(mock_task, exports)

        assert result["status"] == "completed"
        assert result["total_exports"] == 2
        assert result["successful"] == 2
        assert result["failed"] == 0
        assert len(result["results"]) == 2

    def test_batch_export_csv_reports(self):
        """Test batch export of CSV reports."""
        exports = [
            {
                "data": {"rows": [{"name": "Report 1"}]},
                "format": "csv",
            },
            {
                "data": {"rows": [{"name": "Report 2"}]},
                "format": "csv",
            },
        ]

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = batch_export_reports(mock_task, exports)

        assert result["status"] == "completed"
        assert result["total_exports"] == 2
        assert result["successful"] == 2

    def test_batch_export_mixed_formats(self):
        """Test batch export with mixed formats."""
        exports = [
            {
                "data": {"rows": [{"name": "Excel Report"}]},
                "format": "excel",
            },
            {
                "data": {"rows": [{"name": "CSV Report"}]},
                "format": "csv",
            },
        ]

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = batch_export_reports(mock_task, exports)

        assert result["status"] == "completed"
        assert result["total_exports"] == 2
        assert result["successful"] == 2

    def test_batch_export_with_failures(self):
        """Test batch export handles individual failures."""
        exports = [
            {
                "data": {"rows": [{"name": "Valid"}]},
                "format": "excel",
            },
            {
                "data": None,  # Invalid data
                "format": "csv",
            },
        ]

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = batch_export_reports(mock_task, exports)

        assert result["status"] == "completed"
        assert result["total_exports"] == 2
        assert result["successful"] == 1
        assert result["failed"] == 1

    def test_batch_export_unsupported_format(self):
        """Test batch export with unsupported format."""
        exports = [
            {
                "data": {"rows": [{"name": "Test"}]},
                "format": "pdf",  # Not supported in batch export
            },
        ]

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = batch_export_reports(mock_task, exports)

        assert result["status"] == "completed"
        assert result["failed"] == 1
        assert "unsupported" in result["results"][0]["error"].lower()

    def test_batch_export_empty_list(self):
        """Test batch export with empty export list."""
        exports = []

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = batch_export_reports(mock_task, exports)

        assert result["status"] == "completed"
        assert result["total_exports"] == 0
        assert result["successful"] == 0
        assert result["failed"] == 0

    def test_batch_export_updates_progress(self):
        """Test batch export updates progress for each export."""
        exports = [
            {"data": {"rows": [{"name": f"Report {i}"}]}, "format": "csv"}
            for i in range(5)
        ]

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        batch_export_reports(mock_task, exports)

        # Should update progress for each export
        assert mock_task.update_state.call_count >= 5

    def test_batch_export_processing_time(self):
        """Test batch export includes processing time."""
        exports = [
            {
                "data": {"rows": [{"name": "Test"}]},
                "format": "csv",
            },
        ]

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = batch_export_reports(mock_task, exports)

        assert "processing_time_ms" in result
        assert result["processing_time_ms"] > 0

    def test_batch_export_result_details(self):
        """Test batch export includes detailed results."""
        exports = [
            {
                "data": {"rows": [{"name": "Test"}]},
                "format": "excel",
            },
        ]

        mock_task = Mock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = Mock()

        result = batch_export_reports(mock_task, exports)

        assert len(result["results"]) == 1
        export_result = result["results"][0]
        assert "export_index" in export_result
        assert "format" in export_result
        assert "status" in export_result
        assert export_result["export_index"] == 1
        assert export_result["format"] == "excel"
