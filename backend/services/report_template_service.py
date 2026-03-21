"""
Report Template Service for generating various report types.

This module provides functionality to generate different types of reports
(candidate summary, hiring pipeline, EEOC compliance, custom analytics)
in multiple formats (PDF, Excel, CSV).

The service supports:
- Candidate summary reports with resume data, match scores, and hiring stage
- Hiring pipeline reports with stage breakdowns, time metrics, and conversion rates
- EEOC compliance reports with diversity metrics and demographic breakdowns
- Custom analytics reports with user-selected metrics and filters
- Multiple export formats: PDF (via reportlab), Excel (via openpyxl), CSV

Report types:
- candidate_summary: Individual candidate report with detailed information
- hiring_pipeline: Pipeline analysis with stage metrics and conversion rates
- eeoc_compliance: EEOC compliance report with diversity metrics
- custom_analytics: Custom report with user-selected metrics

The service integrates with:
- ReportGenerator for PDF generation
- Export services for Excel/CSV generation
- Database models for data collection
"""
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings

logger = logging.getLogger(__name__)

# Global report template service instance
_report_template_service: Optional["ReportTemplateService"] = None


@dataclass
class ReportConfig:
    """
    Configuration for report generation.

    Attributes:
        report_type: Type of report (candidate_summary, hiring_pipeline, eeoc_compliance, custom_analytics)
        output_format: Output format (pdf, excel, csv)
        title: Report title
        organization_id: Organization ID for filtering data
        filters: Additional filters for data collection
        metrics: List of metrics to include (for custom reports)
        include_charts: Whether to include charts/visualizations
        page_format: Page format for PDF (A4, Letter)
        date_range: Optional date range for filtering
    """
    report_type: str
    output_format: str = "pdf"
    title: Optional[str] = None
    organization_id: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    metrics: List[str] = field(default_factory=list)
    include_charts: bool = True
    page_format: str = "A4"
    date_range: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "report_type": self.report_type,
            "output_format": self.output_format,
            "title": self.title,
            "organization_id": self.organization_id,
            "filters": self.filters,
            "metrics": self.metrics,
            "include_charts": self.include_charts,
            "page_format": self.page_format,
            "date_range": self.date_range,
        }


@dataclass
class ReportGenerationResult:
    """
    Result of report generation.

    Attributes:
        success: Whether report generation succeeded
        report_bytes: Generated report content as bytes
        filename: Suggested filename for the report
        content_type: MIME type (application/pdf, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, text/csv)
        error_message: Error message if generation failed
        file_size: Size of generated report in bytes
        metadata: Additional metadata about the report
        report_type: Type of report that was generated
        generated_at: Timestamp when report was generated
    """
    success: bool
    report_bytes: Optional[bytes] = None
    filename: Optional[str] = None
    content_type: str = "application/pdf"
    error_message: Optional[str] = None
    file_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    report_type: Optional[str] = None
    generated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "filename": self.filename,
            "content_type": self.content_type,
            "error_message": self.error_message,
            "file_size": self.file_size,
            "metadata": self.metadata,
            "report_type": self.report_type,
            "generated_at": self.generated_at,
        }


class ReportTemplateService:
    """
    Report Template Service for generating various report types.

    This service generates professional reports in multiple formats:
    - PDF reports using reportlab
    - Excel reports using openpyxl
    - CSV exports for data portability

    The service supports multiple report types:
    - candidate_summary: Individual candidate reports with detailed information
    - hiring_pipeline: Pipeline analysis with stage metrics and conversion rates
    - eeoc_compliance: EEOC compliance reports with diversity metrics
    - custom_analytics: Custom reports with user-selected metrics

    Attributes:
        db: Database session for data collection
        enabled: Whether report generation is enabled
        default_page_format: Default page format for PDF reports

    Example:
        >>> service = ReportTemplateService(db)
        >>> config = ReportConfig(
        ...     report_type="candidate_summary",
        ...     output_format="pdf",
        ...     title="Candidate Summary Report"
        ... )
        >>> result = await service.generate_report(
        ...     config=config,
        ...     data={"resume_id": "abc-123", ...}
        ... )
        >>> if result.success:
        ...     with open("report.pdf", "wb") as f:
        ...         f.write(result.report_bytes)
    """

    # Report type constants
    REPORT_TYPE_CANDIDATE_SUMMARY = "candidate_summary"
    REPORT_TYPE_HIRING_PIPELINE = "hiring_pipeline"
    REPORT_TYPE_EEOC_COMPLIANCE = "eeoc_compliance"
    REPORT_TYPE_CUSTOM_ANALYTICS = "custom_analytics"

    # Output format constants
    FORMAT_PDF = "pdf"
    FORMAT_EXCEL = "excel"
    FORMAT_CSV = "csv"

    # Page format constants
    PAGE_FORMAT_A4 = "A4"
    PAGE_FORMAT_LETTER = "Letter"

    # Content type mappings
    CONTENT_TYPES = {
        "pdf": "application/pdf",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
    }

    def __init__(
        self,
        db: AsyncSession,
        enabled: Optional[bool] = None,
        default_page_format: str = PAGE_FORMAT_A4,
    ) -> None:
        """
        Initialize the report template service.

        Args:
            db: Database session for data collection
            enabled: Whether report generation is enabled (default: True)
            default_page_format: Default page format for PDF reports (default: A4)
        """
        settings = get_settings()

        self.db = db
        self.enabled = enabled if enabled is not None else True
        self.default_page_format = default_page_format

        # Check for required libraries
        self._reportlab_available = False
        self._openpyxl_available = False

        if self.enabled:
            # Check for reportlab (PDF generation)
            try:
                import reportlab
                self._reportlab_available = True
                logger.info("ReportTemplateService initialized with reportlab support")
            except ImportError:
                logger.warning(
                    "reportlab not installed, PDF generation will be disabled. "
                    "Install with: pip install reportlab"
                )

            # Check for openpyxl (Excel generation)
            try:
                import openpyxl
                self._openpyxl_available = True
                logger.info("ReportTemplateService initialized with openpyxl support")
            except ImportError:
                logger.warning(
                    "openpyxl not installed, Excel generation will be disabled. "
                    "Install with: pip install openpyxl"
                )

        logger.info(
            f"ReportTemplateService initialized: "
            f"enabled={self.enabled}, "
            f"reportlab={self._reportlab_available}, "
            f"openpyxl={self._openpyxl_available}"
        )

    async def generate_report(
        self,
        config: ReportConfig,
        data: Optional[Dict[str, Any]] = None,
    ) -> ReportGenerationResult:
        """
        Generate a report based on configuration.

        This is the main entry point for report generation. It routes to the
        appropriate report type handler based on the configuration.

        Args:
            config: Report configuration
            data: Optional pre-collected data (if None, data will be collected)

        Returns:
            ReportGenerationResult with generated report or error

        Example:
            >>> config = ReportConfig(
            ...     report_type="candidate_summary",
            ...     output_format="pdf"
            ... )
            >>> result = await service.generate_report(config, {"resume_id": "123"})
        """
        if not self.enabled:
            return ReportGenerationResult(
                success=False,
                error_message="Report generation is disabled",
            )

        logger.info(
            f"Generating report: type={config.report_type}, "
            f"format={config.output_format}"
        )

        try:
            # Validate configuration
            self._validate_config(config)

            # Route to appropriate report type handler
            if config.report_type == self.REPORT_TYPE_CANDIDATE_SUMMARY:
                result = await self._generate_candidate_summary(config, data)
            elif config.report_type == self.REPORT_TYPE_HIRING_PIPELINE:
                result = await self._generate_hiring_pipeline(config, data)
            elif config.report_type == self.REPORT_TYPE_EEOC_COMPLIANCE:
                result = await self._generate_eeoc_compliance(config, data)
            elif config.report_type == self.REPORT_TYPE_CUSTOM_ANALYTICS:
                result = await self._generate_custom_analytics(config, data)
            else:
                return ReportGenerationResult(
                    success=False,
                    error_message=f"Unknown report type: {config.report_type}",
                )

            # Add metadata
            result.report_type = config.report_type
            result.generated_at = datetime.utcnow().isoformat() + "Z"

            if result.success:
                logger.info(
                    f"Report generated successfully: "
                    f"type={config.report_type}, "
                    f"size={result.file_size} bytes"
                )
            else:
                logger.error(
                    f"Report generation failed: "
                    f"type={config.report_type}, "
                    f"error={result.error_message}"
                )

            return result

        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return ReportGenerationResult(
                success=False,
                error_message=f"Report generation error: {str(e)}",
            )

    def _validate_config(self, config: ReportConfig) -> None:
        """
        Validate report configuration.

        Args:
            config: Report configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate report type
        valid_types = [
            self.REPORT_TYPE_CANDIDATE_SUMMARY,
            self.REPORT_TYPE_HIRING_PIPELINE,
            self.REPORT_TYPE_EEOC_COMPLIANCE,
            self.REPORT_TYPE_CUSTOM_ANALYTICS,
        ]
        if config.report_type not in valid_types:
            raise ValueError(
                f"Invalid report type: {config.report_type}. "
                f"Must be one of: {', '.join(valid_types)}"
            )

        # Validate output format
        valid_formats = [self.FORMAT_PDF, self.FORMAT_EXCEL, self.FORMAT_CSV]
        if config.output_format not in valid_formats:
            raise ValueError(
                f"Invalid output format: {config.output_format}. "
                f"Must be one of: {', '.join(valid_formats)}"
            )

        # Check format-specific requirements
        if config.output_format == self.FORMAT_PDF and not self._reportlab_available:
            raise ValueError(
                "PDF generation requires reportlab library. "
                "Install with: pip install reportlab"
            )

        if config.output_format == self.FORMAT_EXCEL and not self._openpyxl_available:
            raise ValueError(
                "Excel generation requires openpyxl library. "
                "Install with: pip install openpyxl"
            )

    async def _generate_candidate_summary(
        self,
        config: ReportConfig,
        data: Optional[Dict[str, Any]] = None,
    ) -> ReportGenerationResult:
        """
        Generate candidate summary report.

        This report includes:
        - Resume metadata and contact information
        - Match scores and hiring stage
        - Skills and experience breakdown
        - Interview feedback and notes
        - Recommendation summary

        Args:
            config: Report configuration
            data: Pre-collected data or None to collect from database

        Returns:
            ReportGenerationResult with generated report or error

        Note:
            This is a placeholder implementation. The actual report generation
            logic will be implemented in subsequent subtasks.
        """
        logger.info("Generating candidate summary report (placeholder)")

        # Placeholder implementation
        # This will be fully implemented in subtask-2-2
        return ReportGenerationResult(
            success=False,
            error_message="Candidate summary report not yet implemented",
        )

    async def _generate_hiring_pipeline(
        self,
        config: ReportConfig,
        data: Optional[Dict[str, Any]] = None,
    ) -> ReportGenerationResult:
        """
        Generate hiring pipeline report.

        This report includes:
        - Stage breakdowns with candidate counts
        - Time metrics (time in stage, total time to hire)
        - Conversion rates between stages
        - Pipeline health indicators
        - Bottleneck identification

        Args:
            config: Report configuration
            data: Pre-collected data or None to collect from database

        Returns:
            ReportGenerationResult with generated report or error

        Note:
            This is a placeholder implementation. The actual report generation
            logic will be implemented in subsequent subtasks.
        """
        logger.info("Generating hiring pipeline report (placeholder)")

        # Placeholder implementation
        # This will be fully implemented in subtask-2-3
        return ReportGenerationResult(
            success=False,
            error_message="Hiring pipeline report not yet implemented",
        )

    async def _generate_eeoc_compliance(
        self,
        config: ReportConfig,
        data: Optional[Dict[str, Any]] = None,
    ) -> ReportGenerationResult:
        """
        Generate EEOC compliance report.

        This report includes:
        - Diversity metrics by demographic category
        - Hiring statistics by protected class
        - Adverse impact analysis
        - Compliance status indicators
        - Year-over-year trends

        Args:
            config: Report configuration
            data: Pre-collected data or None to collect from database

        Returns:
            ReportGenerationResult with generated report or error

        Note:
            This is a placeholder implementation. The actual report generation
            logic will be implemented in subsequent subtasks.
        """
        logger.info("Generating EEOC compliance report (placeholder)")

        # Placeholder implementation
        # This will be fully implemented in subtask-2-4
        return ReportGenerationResult(
            success=False,
            error_message="EEOC compliance report not yet implemented",
        )

    async def _generate_custom_analytics(
        self,
        config: ReportConfig,
        data: Optional[Dict[str, Any]] = None,
    ) -> ReportGenerationResult:
        """
        Generate custom analytics report.

        This report includes:
        - User-selected metrics and dimensions
        - Custom filters and date ranges
        - Flexible visualizations
        - Exportable data tables
        - Summary statistics

        Args:
            config: Report configuration
            data: Pre-collected data or None to collect from database

        Returns:
            ReportGenerationResult with generated report or error

        Note:
            This is a placeholder implementation. The actual report generation
            logic will be implemented in subsequent subtasks.
        """
        logger.info("Generating custom analytics report (placeholder)")

        # Placeholder implementation
        # This will be fully implemented in subtask-2-5
        return ReportGenerationResult(
            success=False,
            error_message="Custom analytics report not yet implemented",
        )

    def _generate_filename(
        self,
        report_type: str,
        output_format: str,
        timestamp: Optional[str] = None,
    ) -> str:
        """
        Generate filename for report.

        Args:
            report_type: Type of report
            output_format: Output format
            timestamp: Optional timestamp (default: current time)

        Returns:
            Suggested filename for the report

        Example:
            >>> service._generate_filename("candidate_summary", "pdf")
            "candidate_summary_2024-03-21_143045.pdf"
        """
        if timestamp is None:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")

        extension_map = {
            self.FORMAT_PDF: "pdf",
            self.FORMAT_EXCEL: "xlsx",
            self.FORMAT_CSV: "csv",
        }

        extension = extension_map.get(output_format, "bin")
        return f"{report_type}_{timestamp}.{extension}"


# Singleton pattern for global instance
def get_report_template_service(db: AsyncSession) -> ReportTemplateService:
    """
    Get or create the report template service instance.

    Args:
        db: Database session

    Returns:
        ReportTemplateService instance

    Example:
        >>> from sqlalchemy.ext.asyncio import AsyncSession
        >>> service = get_report_template_service(db)
        >>> result = await service.generate_report(config, data)
    """
    return ReportTemplateService(db)
