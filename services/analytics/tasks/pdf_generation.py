"""
PDF report generation tasks for Analytics Service.

# Русский комментарий:
Этот модуль предоставляет задачи Celery для генерации PDF-отчетов из данных аналитики.
Поддерживает различные форматы отчетов с настраиваемыми шаблонами и стилями.
"""
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from io import BytesIO

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def generate_html_template(
    report_data: Dict[str, Any],
    report_name: str,
    template_style: str = "default",
) -> str:
    """
    Generate HTML template for PDF conversion.

    This function creates an HTML representation of the report data
    that can be converted to PDF using weasyprint or similar tools.

    Args:
        report_data: Report data dictionary containing metrics, dimensions, and summary
        report_name: Name of the report for the title
        template_style: Template style to use (default, executive, detailed)

    Returns:
        HTML string ready for PDF conversion

    Example:
        >>> data = {"metrics": {"time_to_hire": 15.2}, "summary": "Q1 Report"}
        >>> html = generate_html_template(data, "Quarterly Analytics")
        >>> "Quarterly Analytics" in html
        True
    """
    generated_at = report_data.get("generated_at", datetime.utcnow().isoformat())
    summary = report_data.get("summary", "No summary available")
    metrics = report_data.get("metrics", {})
    dimensions = report_data.get("dimensions", {})

    # Generate metrics HTML
    metrics_html = ""
    for metric_name, metric_value in metrics.items():
        if isinstance(metric_value, dict):
            # Nested metrics (e.g., source_effectiveness)
            metrics_html += f"""
            <div class="metric-section">
                <h3>{metric_name.replace('_', ' ').title()}</h3>
                <table class="metric-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for k, v in metric_value.items():
                formatted_value = f"{v:.2f}" if isinstance(v, float) else str(v)
                metrics_html += f"""
                        <tr>
                            <td>{k}</td>
                            <td>{formatted_value}</td>
                        </tr>
                """
            metrics_html += """
                    </tbody>
                </table>
            </div>
            """
        else:
            # Simple metrics
            formatted_value = f"{metric_value:.2f}" if isinstance(metric_value, float) else str(metric_value)
            metrics_html += f"""
            <div class="metric-card">
                <h3>{metric_name.replace('_', ' ').title()}</h3>
                <p class="metric-value">{formatted_value}</p>
            </div>
            """

    # Generate dimensions HTML
    dimensions_html = ""
    for dimension_name, dimension_data in dimensions.items():
        dimensions_html += f"""
        <div class="dimension-section">
            <h3>{dimension_name.replace('_', ' ').title()}</h3>
            <table class="dimension-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
        """
        for category, count in dimension_data.items():
            dimensions_html += f"""
                    <tr>
                        <td>{category}</td>
                        <td>{count}</td>
                    </tr>
            """
        dimensions_html += """
                </tbody>
            </table>
        </div>
        """

    # Generate complete HTML document
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{report_name}</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}

            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: #333;
                line-height: 1.6;
            }}

            .header {{
                text-align: center;
                border-bottom: 3px solid #2196F3;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}

            .header h1 {{
                color: #2196F3;
                margin: 0;
                font-size: 28px;
            }}

            .header .date {{
                color: #666;
                font-size: 14px;
                margin-top: 10px;
            }}

            .summary {{
                background-color: #f5f5f5;
                padding: 20px;
                border-left: 4px solid #2196F3;
                margin-bottom: 30px;
            }}

            .summary h2 {{
                margin-top: 0;
                color: #2196F3;
                font-size: 20px;
            }}

            .metrics-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}

            .metric-card {{
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .metric-card h3 {{
                margin: 0 0 10px 0;
                color: #666;
                font-size: 14px;
                text-transform: uppercase;
            }}

            .metric-card .metric-value {{
                font-size: 32px;
                font-weight: bold;
                color: #2196F3;
                margin: 0;
            }}

            .metric-section {{
                margin-bottom: 30px;
            }}

            .metric-section h3 {{
                color: #2196F3;
                border-bottom: 2px solid #2196F3;
                padding-bottom: 10px;
            }}

            .dimension-section {{
                margin-bottom: 30px;
            }}

            .dimension-section h3 {{
                color: #4CAF50;
                border-bottom: 2px solid #4CAF50;
                padding-bottom: 10px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}

            th {{
                background-color: #2196F3;
                color: white;
                padding: 12px;
                text-align: left;
            }}

            td {{
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }}

            tr:hover {{
                background-color: #f5f5f5;
            }}

            .footer {{
                margin-top: 50px;
                text-align: center;
                color: #999;
                font-size: 12px;
                border-top: 1px solid #ddd;
                padding-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{report_name}</h1>
            <div class="date">Generated: {generated_at}</div>
        </div>

        <div class="summary">
            <h2>Summary</h2>
            <p>{summary}</p>
        </div>

        {metrics_html}

        {dimensions_html}

        <div class="footer">
            <p>Generated by AgentHR Analytics Service</p>
            <p>© 2024 AgentHR. All rights reserved.</p>
        </div>
    </body>
    </html>
    """

    return html


def convert_html_to_pdf(
    html_content: str,
    page_size: str = "A4",
) -> Optional[bytes]:
    """
    Convert HTML content to PDF bytes.

    This function uses weasyprint to convert HTML to PDF format.
    Falls back to simple text-based PDF if weasyprint is not available.

    Args:
        html_content: HTML string to convert
        page_size: PDF page size (A4, Letter, etc.)

    Returns:
        PDF document as bytes, or None if conversion fails

    Example:
        >>> html = "<html><body><h1>Test</h1></body></html>"
        >>> pdf_bytes = convert_html_to_pdf(html)
        >>> pdf_bytes is not None
        True
    """
    try:
        # Try to import weasyprint for proper PDF generation
        try:
            from weasyprint import HTML, CSS

            logger.info("Using weasyprint for PDF generation")

            # Create PDF from HTML
            html_doc = HTML(string=html_content)
            pdf_bytes = html_doc.write_pdf()

            logger.info(f"PDF generated with weasyprint ({len(pdf_bytes)} bytes)")
            return pdf_bytes

        except ImportError:
            # Fallback: Create simple text-based PDF representation
            logger.warning(
                "weasyprint not available, using fallback text representation. "
                "Install weasyprint for proper PDF generation: pip install weasyprint"
            )

            # Strip HTML tags for simple text representation
            import re
            text_content = re.sub('<[^<]+?>', '', html_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()

            # Create simple PDF-like text format
            pdf_content = f"""
%PDF-1.4
% Simplified PDF representation (install weasyprint for proper PDFs)

{text_content}

%%EOF
            """.strip()

            pdf_bytes = pdf_content.encode('utf-8')

            logger.info(f"Fallback PDF generated ({len(pdf_bytes)} bytes)")
            return pdf_bytes

    except Exception as e:
        logger.error(f"Failed to convert HTML to PDF: {e}", exc_info=True)
        return None


@shared_task(
    name="tasks.pdf_generation.generate_pdf_report",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def generate_pdf_report(
    self,
    report_data: Dict[str, Any],
    report_name: str,
    template_style: str = "default",
    page_size: str = "A4",
) -> Dict[str, Any]:
    """
    Generate PDF report from report data.

    This Celery task handles PDF generation from analytics report data:
    1. Generate HTML template from report data
    2. Apply styling based on template style
    3. Convert HTML to PDF using weasyprint
    4. Return PDF bytes with metadata

    Task Workflow:
    1. Validate report data
    2. Generate HTML template with styling
    3. Convert HTML to PDF
    4. Calculate file size and metadata
    5. Return PDF bytes with results

    Args:
        self: Celery task instance (bind=True)
        report_data: Report data dictionary containing:
            - metrics: Dictionary of metric name -> value
            - dimensions: Dictionary of dimension name -> data
            - summary: Text summary of the report
            - generated_at: ISO timestamp of generation
        report_name: Name of the report for the PDF title
        template_style: Template style (default, executive, detailed)
        page_size: PDF page size (A4, Letter, etc.)

    Returns:
        Dictionary containing generation results:
        - status: Task status (completed/failed)
        - pdf_bytes: PDF document as bytes (if successful)
        - file_size_bytes: Size of PDF in bytes
        - report_name: Name of the report
        - template_style: Template style used
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        ValueError: If report_data is invalid
        Exception: For PDF generation errors

    Example:
        >>> from tasks.pdf_generation import generate_pdf_report
        >>> data = {
        ...     "metrics": {"time_to_hire": 15.2},
        ...     "summary": "Q1 Report"
        ... }
        >>> task = generate_pdf_report.delay(data, "Quarterly Analytics")
        >>> result = task.get()
        >>> result['status']
        'completed'
    """
    start_time = time.time()
    total_steps = 4
    current_step = 0

    try:
        logger.info(
            f"Starting PDF generation for report: {report_name}, "
            f"style: {template_style}"
        )

        # Step 1: Validate report data
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "validating_data",
            "message": "Validating report data...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(
            f"Task {self.request.id}: Step {current_step}/{total_steps} - "
            "Validating data"
        )

        if not report_data:
            raise ValueError("report_data cannot be empty")

        if not isinstance(report_data, dict):
            raise ValueError("report_data must be a dictionary")

        # Ensure required fields exist
        if "metrics" not in report_data:
            report_data["metrics"] = {}
        if "summary" not in report_data:
            report_data["summary"] = "No summary available"
        if "generated_at" not in report_data:
            report_data["generated_at"] = datetime.utcnow().isoformat()

        logger.info("Report data validated successfully")

        # Step 2: Generate HTML template
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "generating_html",
            "message": "Generating HTML template...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(
            f"Task {self.request.id}: Step {current_step}/{total_steps} - "
            "Generating HTML"
        )

        html_content = generate_html_template(
            report_data=report_data,
            report_name=report_name,
            template_style=template_style,
        )

        logger.info(f"HTML template generated ({len(html_content)} characters)")

        # Step 3: Convert HTML to PDF
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "converting_to_pdf",
            "message": "Converting to PDF format...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(
            f"Task {self.request.id}: Step {current_step}/{total_steps} - "
            "Converting to PDF"
        )

        pdf_bytes = convert_html_to_pdf(
            html_content=html_content,
            page_size=page_size,
        )

        if pdf_bytes is None:
            raise Exception("PDF conversion failed")

        logger.info(f"PDF conversion completed ({len(pdf_bytes)} bytes)")

        # Step 4: Prepare results
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "finalizing",
            "message": "Finalizing PDF report...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(
            f"Task {self.request.id}: Step {current_step}/{total_steps} - "
            "Finalizing"
        )

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "status": "completed",
            "pdf_bytes": pdf_bytes,
            "file_size_bytes": len(pdf_bytes),
            "report_name": report_name,
            "template_style": template_style,
            "page_size": page_size,
            "processing_time_ms": processing_time_ms,
            "task_id": self.request.id,
        }

        logger.info(
            f"PDF generation completed: {report_name}, "
            f"size: {len(pdf_bytes)} bytes, time: {processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "status": "failed",
            "error": "PDF generation exceeded maximum time limit",
            "report_name": report_name,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except ValueError as e:
        logger.error(f"Validation error in PDF generation: {e}")
        return {
            "status": "failed",
            "error": f"Validation error: {str(e)}",
            "report_name": report_name,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in PDF generation: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "report_name": report_name,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.pdf_generation.batch_generate_pdf_reports",
    bind=True,
    max_retries=2,
)
def batch_generate_pdf_reports(
    self,
    reports: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Generate multiple PDF reports in batch.

    This task handles batch PDF generation for multiple reports,
    useful for scheduled report delivery or bulk export operations.

    Args:
        self: Celery task instance (bind=True)
        reports: List of report configurations, each containing:
            - report_data: Report data dictionary
            - report_name: Name of the report
            - template_style: Optional template style
            - page_size: Optional page size

    Returns:
        Dictionary containing batch results:
        - total_reports: Total number of reports requested
        - successful: Number of successfully generated PDFs
        - failed: Number of failed generations
        - results: List of individual results
        - processing_time_ms: Total processing time

    Example:
        >>> from tasks.pdf_generation import batch_generate_pdf_reports
        >>> reports = [
        ...     {"report_data": {...}, "report_name": "Report 1"},
        ...     {"report_data": {...}, "report_name": "Report 2"}
        ... ]
        >>> task = batch_generate_pdf_reports.delay(reports)
        >>> result = task.get()
        >>> result['successful']
        2
    """
    start_time = time.time()

    try:
        logger.info(f"Starting batch PDF generation for {len(reports)} reports")

        total_reports = len(reports)
        successful = 0
        failed = 0
        results = []

        for idx, report_config in enumerate(reports):
            try:
                # Update progress
                progress = {
                    "current": idx + 1,
                    "total": total_reports,
                    "percentage": int((idx + 1) / total_reports * 100),
                    "status": "processing",
                    "message": f"Processing report {idx + 1}/{total_reports}...",
                }
                self.update_state(state="PROGRESS", meta=progress)

                # Extract configuration
                report_data = report_config.get("report_data", {})
                report_name = report_config.get("report_name", f"Report {idx + 1}")
                template_style = report_config.get("template_style", "default")
                page_size = report_config.get("page_size", "A4")

                # Generate PDF
                result = generate_pdf_report(
                    report_data=report_data,
                    report_name=report_name,
                    template_style=template_style,
                    page_size=page_size,
                )

                if result.get("status") == "completed":
                    successful += 1
                    logger.info(f"Successfully generated PDF: {report_name}")
                else:
                    failed += 1
                    logger.warning(f"Failed to generate PDF: {report_name}")

                results.append({
                    "report_name": report_name,
                    "status": result.get("status"),
                    "file_size_bytes": result.get("file_size_bytes"),
                    "error": result.get("error"),
                })

            except Exception as e:
                failed += 1
                logger.error(f"Error processing report {idx + 1}: {e}")
                results.append({
                    "report_name": report_config.get("report_name", f"Report {idx + 1}"),
                    "status": "failed",
                    "error": str(e),
                })

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        summary = {
            "total_reports": total_reports,
            "successful": successful,
            "failed": failed,
            "results": results,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Batch PDF generation completed: {successful} successful, "
            f"{failed} failed, time: {processing_time_ms}ms"
        )

        return summary

    except Exception as e:
        logger.error(f"Error in batch PDF generation: {e}", exc_info=True)
        return {
            "total_reports": len(reports),
            "successful": 0,
            "failed": len(reports),
            "results": [],
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "status": "failed",
            "error": str(e),
        }
