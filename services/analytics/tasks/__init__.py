"""
Celery tasks for Analytics Service.

This package provides background job processing for scheduled reports,
analytics data aggregation, and other batch operations.
"""
from tasks.report_generation import (
    generate_scheduled_reports,
    process_all_pending_reports,
)
from tasks.pdf_generation import (
    generate_pdf_report,
    batch_generate_pdf_reports,
)

__all__ = [
    "generate_scheduled_reports",
    "process_all_pending_reports",
    "generate_pdf_report",
    "batch_generate_pdf_reports",
]
