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
        logger.info("Generating candidate summary report")

        try:
            # Collect data if not provided
            if data is None:
                data = await self._collect_candidate_summary_data(config)

            # Validate required data
            if not data.get("resume_id"):
                raise ValueError("resume_id is required for candidate summary report")

            # Generate report based on output format
            if config.output_format == self.FORMAT_PDF:
                return await self._generate_candidate_summary_pdf(config, data)
            elif config.output_format == self.FORMAT_EXCEL:
                return await self._generate_candidate_summary_excel(config, data)
            elif config.output_format == self.FORMAT_CSV:
                return await self._generate_candidate_summary_csv(config, data)
            else:
                raise ValueError(f"Unsupported output format: {config.output_format}")

        except Exception as e:
            logger.error(f"Error generating candidate summary report: {e}", exc_info=True)
            return ReportGenerationResult(
                success=False,
                error_message=f"Failed to generate candidate summary report: {str(e)}",
            )

    async def _collect_candidate_summary_data(
        self, config: ReportConfig
    ) -> Dict[str, Any]:
        """
        Collect data for candidate summary report from database.

        Args:
            config: Report configuration with filters

        Returns:
            Dictionary with collected candidate data

        Raises:
            ValueError: If required filters are missing
        """
        from backend.models.resume import Resume
        from backend.models.candidate_rank import CandidateRank
        from backend.models.hiring_stage import HiringStage
        from backend.models.analysis_result import AnalysisResult

        # Extract resume_id from filters
        resume_id = config.filters.get("resume_id")
        if not resume_id:
            raise ValueError("resume_id is required in filters for candidate summary report")

        # Query resume data
        resume_stmt = select(Resume).where(Resume.id == resume_id)
        resume_result = await self.db.execute(resume_stmt)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        # Query candidate rank data
        rank_stmt = select(CandidateRank).where(CandidateRank.resume_id == resume_id)
        if config.filters.get("vacancy_id"):
            rank_stmt = rank_stmt.where(CandidateRank.vacancy_id == config.filters["vacancy_id"])
        rank_result = await self.db.execute(rank_stmt)
        candidate_rank = rank_result.scalar_one_or_none()

        # Query hiring stage data
        stage_stmt = (
            select(HiringStage)
            .where(HiringStage.resume_id == resume_id)
            .order_by(HiringStage.created_at.desc())
        )
        stage_result = await self.db.execute(stage_stmt)
        hiring_stage = stage_result.scalar_one_or_none()

        # Query analysis result data
        analysis_stmt = select(AnalysisResult).where(AnalysisResult.resume_id == resume_id)
        analysis_result = await self.db.execute(analysis_stmt)
        analysis = analysis_result.scalar_one_or_none()

        # Build data dictionary
        data = {
            "resume_id": str(resume.id),
            "organization_id": resume.organization_id,
            "vacancy_id": str(resume.vacancy_id) if resume.vacancy_id else None,
            "filename": resume.filename,
            "status": resume.status.value if resume.status else None,
            "language": resume.language,
            "uploaded_at": resume.created_at.isoformat() if hasattr(resume, "created_at") else None,
        }

        # Add candidate rank data if available
        if candidate_rank:
            data["rank_score"] = float(candidate_rank.rank_score)
            data["rank_position"] = int(candidate_rank.rank_position) if candidate_rank.rank_position else None
            data["model_version"] = candidate_rank.model_version
            data["prediction_confidence"] = float(candidate_rank.prediction_confidence) if candidate_rank.prediction_confidence else None
            data["explanation_narrative"] = candidate_rank.explanation_narrative
            data["recommendation"] = candidate_rank.recommendation
            data["feature_contributions"] = candidate_rank.feature_contributions
            data["ranking_factors"] = candidate_rank.ranking_factors
            data["confidence_interval"] = candidate_rank.confidence_interval

        # Add hiring stage data if available
        if hiring_stage:
            data["hiring_stage"] = hiring_stage.stage_name.value if hiring_stage.stage_name else None
            data["stage_notes"] = hiring_stage.notes
            data["priority"] = hiring_stage.priority
            data["queue_entered_at"] = hiring_stage.queue_entered_at.isoformat() if hiring_stage.queue_entered_at else None

        # Add analysis result data if available
        if analysis:
            data["skills"] = analysis.skills or []
            data["experience_summary"] = analysis.experience_summary or {}
            data["keywords"] = analysis.keywords or []
            data["entities"] = analysis.entities or {}

        return data

    async def _generate_candidate_summary_pdf(
        self, config: ReportConfig, data: Dict[str, Any]
    ) -> ReportGenerationResult:
        """
        Generate candidate summary report in PDF format.

        Args:
            config: Report configuration
            data: Collected candidate data

        Returns:
            ReportGenerationResult with PDF bytes
        """
        from reportlab.lib.pagesizes import A4, Letter
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            PageBreak,
            Table,
            TableStyle,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        # Create PDF buffer
        buffer = io.BytesIO()

        # Get page size
        pagesize = A4 if config.page_format == self.PAGE_FORMAT_A4 else Letter

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=pagesize,
            leftMargin=72,
            rightMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        # Get styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#34495e"),
            spaceAfter=12,
        )

        normal_style = styles["BodyText"]
        normal_style.fontSize = 11

        # Build story (content elements)
        story = []

        # Title
        title = config.title or "Candidate Summary Report"
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.3 * inch))

        # Resume metadata
        story.append(Paragraph("Resume Information", heading_style))

        metadata_data = [
            ["Resume ID:", data.get("resume_id", "N/A")],
            ["Filename:", data.get("filename", "N/A")],
            ["Status:", data.get("status", "N/A")],
            ["Language:", data.get("language", "N/A")],
        ]

        if data.get("uploaded_at"):
            metadata_data.append(["Uploaded:", data["uploaded_at"]])

        metadata_table = Table(metadata_data, colWidths=[2 * inch, 4 * inch])
        metadata_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 0.3 * inch))

        # Match scores and ranking
        if data.get("rank_score") is not None:
            story.append(Paragraph("Match Score & Ranking", heading_style))

            score_data = [
                ["Overall Match Score:", f"{data['rank_score']:.1%}"],
            ]

            if data.get("rank_position"):
                score_data.append(["Rank Position:", f"#{data['rank_position']}"])

            if data.get("prediction_confidence"):
                score_data.append(["Confidence:", f"{data['prediction_confidence']:.1%}"])

            if data.get("recommendation"):
                score_data.append(["Recommendation:", data["recommendation"].upper()])

            score_table = Table(score_data, colWidths=[2 * inch, 4 * inch])
            score_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(score_table)
            story.append(Spacer(1, 0.2 * inch))

            # Explanation narrative
            if data.get("explanation_narrative"):
                story.append(Paragraph("Explanation", heading_style))
                story.append(Paragraph(data["explanation_narrative"], normal_style))
                story.append(Spacer(1, 0.2 * inch))

        # Hiring stage
        if data.get("hiring_stage"):
            story.append(Paragraph("Hiring Stage", heading_style))

            stage_data = [
                ["Current Stage:", data["hiring_stage"].upper()],
            ]

            if data.get("priority"):
                stage_data.append(["Priority:", str(data["priority"])])

            if data.get("queue_entered_at"):
                stage_data.append(["Queue Entry:", data["queue_entered_at"]])

            stage_table = Table(stage_data, colWidths=[2 * inch, 4 * inch])
            stage_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(stage_table)

            if data.get("stage_notes"):
                story.append(Spacer(1, 0.1 * inch))
                story.append(Paragraph(f"<b>Notes:</b> {data['stage_notes']}", normal_style))

            story.append(Spacer(1, 0.3 * inch))

        # Skills
        if data.get("skills"):
            story.append(Paragraph("Skills", heading_style))

            skills_list = []
            for skill in data["skills"]:
                if isinstance(skill, dict):
                    skill_name = skill.get("name", str(skill))
                else:
                    skill_name = str(skill)
                skills_list.append(skill_name)

            if skills_list:
                # Group skills into columns for better layout
                skills_text = ", ".join(skills_list)
                story.append(Paragraph(skills_text, normal_style))
                story.append(Spacer(1, 0.2 * inch))

        # Experience summary
        if data.get("experience_summary"):
            story.append(Paragraph("Experience Summary", heading_style))

            exp_summary = data["experience_summary"]
            exp_text = ""

            if "total_years_formatted" in exp_summary:
                exp_text += f"<b>Total Experience:</b> {exp_summary['total_years_formatted']}<br/>"
            elif "total_years" in exp_summary:
                exp_text += f"<b>Total Experience:</b> {exp_summary['total_years']:.1f} years<br/>"

            if "framework_specific" in exp_summary:
                exp_text += "<br/><b>Framework-Specific Experience:</b><br/>"
                for framework, experience in exp_summary["framework_specific"].items():
                    exp_text += f"• {framework}: {experience}<br/>"

            if exp_text:
                story.append(Paragraph(exp_text, normal_style))
                story.append(Spacer(1, 0.2 * inch))

        # Feature contributions (if available)
        if data.get("feature_contributions"):
            story.append(PageBreak())
            story.append(Paragraph("Feature Contribution Breakdown", heading_style))

            contributions = data["feature_contributions"]
            if isinstance(contributions, dict):
                # Convert dict to list format
                contrib_list = [
                    {"name": key, "contribution": value}
                    for key, value in contributions.items()
                ]
            else:
                contrib_list = contributions

            if contrib_list:
                table_data = [["Feature", "Contribution"]]

                for contrib in contrib_list[:10]:  # Limit to top 10
                    name = contrib.get("name", "N/A")
                    value = contrib.get("contribution", contrib.get("value", 0))

                    if isinstance(value, (int, float)):
                        value_str = f"{value:.3f}"
                    else:
                        value_str = str(value)

                    table_data.append([name, value_str])

                contrib_table = Table(table_data, colWidths=[3 * inch, 2 * inch])
                contrib_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#bdc3c7")),
                ]))

                story.append(contrib_table)
                story.append(Spacer(1, 0.2 * inch))

        # Confidence interval (if available)
        if data.get("confidence_interval"):
            story.append(Paragraph("Confidence Interval", heading_style))

            ci = data["confidence_interval"]
            ci_text = (
                f"<b>Lower Bound:</b> {ci.get('lower', 0):.1%}<br/>"
                f"<b>Upper Bound:</b> {ci.get('upper', 0):.1%}<br/>"
            )

            if "confidence_level" in ci:
                ci_text += f"<b>Confidence Level:</b> {ci.get('confidence_level', 0):.0%}<br/>"

            if "explanation" in ci:
                ci_text += f"<br/>{ci['explanation']}"

            story.append(Paragraph(ci_text, normal_style))
            story.append(Spacer(1, 0.2 * inch))

        # Footer
        story.append(Spacer(1, 0.5 * inch))
        footer_style = ParagraphStyle(
            "Footer",
            parent=normal_style,
            fontSize=9,
            textColor=colors.HexColor("#7f8c8d"),
            alignment=TA_CENTER,
        )
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        footer_text = f"Generated: {timestamp} | Resume ID: {data['resume_id']}"
        if data.get("vacancy_id"):
            footer_text += f" | Vacancy ID: {data['vacancy_id']}"
        story.append(Paragraph(footer_text, footer_style))

        # Build PDF
        doc.build(story)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Generate filename
        filename = self._generate_filename(
            self.REPORT_TYPE_CANDIDATE_SUMMARY,
            self.FORMAT_PDF
        )

        return ReportGenerationResult(
            success=True,
            report_bytes=pdf_bytes,
            filename=filename,
            content_type=self.CONTENT_TYPES[self.FORMAT_PDF],
            file_size=len(pdf_bytes),
            metadata={
                "resume_id": data["resume_id"],
                "vacancy_id": data.get("vacancy_id"),
            },
        )

    async def _generate_candidate_summary_excel(
        self, config: ReportConfig, data: Dict[str, Any]
    ) -> ReportGenerationResult:
        """
        Generate candidate summary report in Excel format.

        Args:
            config: Report configuration
            data: Collected candidate data

        Returns:
            ReportGenerationResult with Excel bytes
        """
        # Placeholder for Excel generation
        # This would use openpyxl to create an Excel workbook
        return ReportGenerationResult(
            success=False,
            error_message="Excel format not yet implemented for candidate summary report",
        )

    async def _generate_candidate_summary_csv(
        self, config: ReportConfig, data: Dict[str, Any]
    ) -> ReportGenerationResult:
        """
        Generate candidate summary report in CSV format.

        Args:
            config: Report configuration
            data: Collected candidate data

        Returns:
            ReportGenerationResult with CSV bytes
        """
        # Placeholder for CSV generation
        # This would use csv module to create a CSV file
        return ReportGenerationResult(
            success=False,
            error_message="CSV format not yet implemented for candidate summary report",
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
