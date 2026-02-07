"""
PDF Report Generation Service for Explainability Reports.

This module provides functionality to generate professional PDF reports
from explainability data, including candidate ranking explanations,
feature breakdowns, confidence intervals, and what-if analysis results.

The service supports:
- PDF generation from explainability data
- Professional formatting with headers, footers, and branding
- Visual elements like progress bars and confidence interval charts
- Multi-page reports with table of contents
- Export options for different report types

Report types:
- ranking_explanation: Full ranking explanation with features
- comparison: Side-by-side candidate comparison
- what_if: What-if scenario analysis
- confidence: Confidence interval analysis
"""
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from config import get_settings

logger = logging.getLogger(__name__)

# Global report generator instance
_report_generator: Optional["ReportGenerator"] = None


@dataclass
class ReportData:
    """
    Data structure for explainability report.

    Attributes:
        resume_id: Resume UUID
        vacancy_id: Vacancy UUID
        candidate_name: Candidate's name (if available)
        job_title: Position title
        rank_score: Overall ranking score
        rank_position: Position in ranked list
        narrative: Natural language explanation
        feature_explanations: List of feature contribution breakdowns
        confidence_interval: Confidence interval data
        strengths: List of candidate strengths
        weaknesses: List of areas for improvement
        recommendation: Hiring recommendation
        highlight_sections: Resume sections to highlight
        comparison_data: Optional comparison data for side-by-side reports
        what_if_data: Optional what-if analysis data
        generated_at: Timestamp of report generation
    """
    resume_id: str
    vacancy_id: str
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    rank_score: float = 0.0
    rank_position: Optional[int] = None
    narrative: str = ""
    feature_explanations: List[Dict[str, Any]] = field(default_factory=list)
    confidence_interval: Optional[Dict[str, Any]] = None
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendation: str = "good"
    highlight_sections: Dict[str, str] = field(default_factory=dict)
    comparison_data: Optional[Dict[str, Any]] = None
    what_if_data: Optional[Dict[str, Any]] = None
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "resume_id": self.resume_id,
            "vacancy_id": self.vacancy_id,
            "candidate_name": self.candidate_name,
            "job_title": self.job_title,
            "rank_score": self.rank_score,
            "rank_position": self.rank_position,
            "narrative": self.narrative,
            "feature_explanations": self.feature_explanations,
            "confidence_interval": self.confidence_interval,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendation": self.recommendation,
            "highlight_sections": self.highlight_sections,
            "comparison_data": self.comparison_data,
            "what_if_data": self.what_if_data,
            "generated_at": self.generated_at,
        }


@dataclass
class PDFGenerationResult:
    """
    Result of PDF generation.

    Attributes:
        success: Whether PDF generation succeeded
        pdf_bytes: Generated PDF content as bytes
        filename: Suggested filename for the PDF
        content_type: MIME type (application/pdf)
        error_message: Error message if generation failed
        file_size: Size of generated PDF in bytes
    """
    success: bool
    pdf_bytes: Optional[bytes] = None
    filename: Optional[str] = None
    content_type: str = "application/pdf"
    error_message: Optional[str] = None
    file_size: int = 0


class ReportGenerator:
    """
    PDF Report Generation Service.

    This service generates professional PDF reports from explainability data,
    including ranking explanations, feature breakdowns, confidence intervals,
    and what-if analysis results.

    The service uses reportlab for PDF generation with the following features:
    - Professional formatting with headers and footers
    - Visual elements for feature contributions
    - Confidence interval visualization
    - Multi-page layout support
    - Brand elements and company logo (optional)

    Attributes:
        enabled: Whether PDF generation is enabled
        page_format: Default page format (A4, Letter)
        margin: Default page margins in points
        include_branding: Whether to include branding elements

    Example:
        >>> generator = ReportGenerator()
        >>> result = await generator.generate_explainability_pdf(
        ...     resume_id="abc-123",
        ...     vacancy_id="vac-456",
        ...     data=report_data
        ... )
        >>> if result.success:
        ...     with open("report.pdf", "wb") as f:
        ...         f.write(result.pdf_bytes)
    """

    # Page format constants
    PAGE_FORMAT_A4 = "A4"
    PAGE_FORMAT_LETTER = "Letter"

    # Report type constants
    REPORT_TYPE_RANKING = "ranking_explanation"
    REPORT_TYPE_COMPARISON = "comparison"
    REPORT_TYPE_WHAT_IF = "what_if"
    REPORT_TYPE_CONFIDENCE = "confidence"

    def __init__(
        self,
        enabled: Optional[bool] = None,
        page_format: str = PAGE_FORMAT_A4,
        margin: int = 72,  # 1 inch in points
        include_branding: bool = True,
    ) -> None:
        """
        Initialize the report generator.

        Args:
            enabled: Whether PDF generation is enabled
            page_format: Default page format (A4, Letter)
            margin: Page margin in points (default 72 = 1 inch)
            include_branding: Whether to include branding elements
        """
        settings = get_settings()

        self.enabled = enabled if enabled is not None else True
        self.page_format = page_format
        self.margin = margin
        self.include_branding = include_branding

        # Try to import reportlab, disable if not available
        self._reportlab_available = False
        if self.enabled:
            try:
                from reportlab.lib.pagesizes import A4, Letter
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet

                self._reportlab_available = True
                self._pagesizes = {"A4": A4, "Letter": Letter}
                logger.info("ReportGenerator initialized with reportlab")
            except ImportError:
                logger.warning(
                    "reportlab not installed, PDF generation will use fallback mode. "
                    "Install with: pip install reportlab"
                )
                self.enabled = False

    def is_available(self) -> bool:
        """Check if PDF generation is available."""
        return self.enabled and self._reportlab_available

    async def generate_explainability_pdf(
        self,
        resume_id: str,
        vacancy_id: str,
        data: ReportData,
        report_type: str = REPORT_TYPE_RANKING,
    ) -> PDFGenerationResult:
        """
        Generate PDF report from explainability data.

        Args:
            resume_id: Resume UUID
            vacancy_id: Vacancy UUID
            data: Report data with explainability information
            report_type: Type of report to generate

        Returns:
            PDFGenerationResult with generated PDF bytes or error

        Raises:
            ValueError: If data is invalid or report_type is unsupported
        """
        try:
            logger.info(
                f"Generating PDF report for resume {resume_id}, "
                f"vacancy {vacancy_id}, type {report_type}"
            )

            # Validate data
            if not data:
                raise ValueError("Report data cannot be empty")

            if report_type not in [
                self.REPORT_TYPE_RANKING,
                self.REPORT_TYPE_COMPARISON,
                self.REPORT_TYPE_WHAT_IF,
                self.REPORT_TYPE_CONFIDENCE,
            ]:
                raise ValueError(f"Unsupported report type: {report_type}")

            # Check if reportlab is available
            if not self.is_available():
                logger.warning("reportlab not available, using text-based fallback")
                return await self._generate_text_fallback(
                    resume_id, vacancy_id, data, report_type
                )

            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            candidate_name = data.candidate_name or "candidate"
            filename = f"explainability_{candidate_name}_{timestamp}.pdf"

            # Generate PDF using reportlab
            pdf_bytes = await self._generate_pdf_with_reportlab(data, report_type)

            logger.info(
                f"PDF generated successfully: {filename} "
                f"({len(pdf_bytes)} bytes)"
            )

            return PDFGenerationResult(
                success=True,
                pdf_bytes=pdf_bytes,
                filename=filename,
                content_type="application/pdf",
                file_size=len(pdf_bytes),
            )

        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            return PDFGenerationResult(
                success=False,
                error_message=str(e),
            )

    async def _generate_pdf_with_reportlab(
        self,
        data: ReportData,
        report_type: str,
    ) -> bytes:
        """
        Generate PDF using reportlab library.

        Args:
            data: Report data
            report_type: Type of report

        Returns:
            PDF content as bytes
        """
        from reportlab.lib.pagesizes import A4
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
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        # Create PDF buffer
        buffer = io.BytesIO()

        # Get page size
        pagesize = self._pagesizes.get(self.page_format, A4)

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=pagesize,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
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

        # Title page
        story.append(Paragraph("Candidate Ranking Explanation", title_style))
        story.append(Spacer(1, 0.3 * inch))

        # Candidate and job info
        if data.job_title:
            story.append(
                Paragraph(
                    f"<b>Position:</b> {data.job_title}",
                    normal_style
                )
            )

        if data.candidate_name:
            story.append(
                Paragraph(
                    f"<b>Candidate:</b> {data.candidate_name}",
                    normal_style
                )
            )

        story.append(
            Paragraph(
                f"<b>Overall Score:</b> {data.rank_score:.1%}",
                normal_style
            )
        )

        if data.rank_position is not None:
            story.append(
                Paragraph(
                    f"<b>Rank Position:</b> #{data.rank_position}",
                    normal_style
                )
            )

        story.append(Spacer(1, 0.3 * inch))

        # Narrative
        story.append(Paragraph("Summary", heading_style))
        story.append(Paragraph(data.narrative, normal_style))
        story.append(Spacer(1, 0.2 * inch))

        # Recommendation
        recommendation_colors = {
            "excellent": colors.HexColor("#27ae60"),
            "good": colors.HexColor("#3498db"),
            "maybe": colors.HexColor("#f39c12"),
            "poor": colors.HexColor("#e74c3c"),
        }
        rec_color = recommendation_colors.get(
            data.recommendation.lower(),
            colors.HexColor("#3498db")
        )

        recommendation_style = ParagraphStyle(
            "Recommendation",
            parent=normal_style,
            fontSize=14,
            textColor=rec_color,
            spaceAfter=20,
        )
        story.append(
            Paragraph(
                f"<b>Recommendation: {data.recommendation.upper()}</b>",
                recommendation_style
            )
        )

        story.append(PageBreak())

        # Feature breakdowns
        if data.feature_explanations:
            story.append(Paragraph("Feature Contribution Breakdown", heading_style))

            # Create feature table
            table_data = [["Feature", "Value", "Contribution", "Impact"]]

            for feature in data.feature_explanations:
                name = feature.get("name", "N/A")
                value = feature.get("value", 0)
                contrib = feature.get("contribution", 0)
                contrib_pct = feature.get("contribution_percent", 0)
                impact = feature.get("impact_level", "medium")

                # Format values
                value_str = f"{value:.3f}" if isinstance(value, (int, float)) else str(value)
                contrib_str = f"{contrib:.3f} ({contrib_pct:.1f}%)"

                # Color code impact
                impact_colors = {
                    "high": "#27ae60",
                    "medium": "#f39c12",
                    "low": "#95a5a6",
                }
                impact_color = impact_colors.get(impact.lower(), "#95a5a6")
                impact_str = f'<font color="{impact_color}">{impact.title()}</font>'

                table_data.append([name, value_str, contrib_str, impact_str])

            # Create table
            table = Table(table_data, colWidths=[2.5 * inch, 1 * inch, 1.5 * inch, 1 * inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#bdc3c7")),
            ]))

            story.append(table)
            story.append(Spacer(1, 0.2 * inch))

        # Confidence interval
        if data.confidence_interval:
            story.append(PageBreak())
            story.append(Paragraph("Confidence Interval", heading_style))

            ci = data.confidence_interval
            ci_text = (
                f"<b>Lower Bound:</b> {ci.get('lower', 0):.1%}<br/>"
                f"<b>Upper Bound:</b> {ci.get('upper', 0):.1%}<br/>"
                f"<b>Confidence Level:</b> {ci.get('confidence_level', 0):.0%}<br/>"
                f"<b>Margin of Error:</b> ±{ci.get('margin_of_error', 0):.1%}<br/>"
                f"<br/>"
                f"{ci.get('explanation', '')}"
            )
            story.append(Paragraph(ci_text, normal_style))

        # Strengths
        if data.strengths:
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("Candidate Strengths", heading_style))

            for strength in data.strengths:
                story.append(Paragraph(f"• {strength}", normal_style))

        # Weaknesses
        if data.weaknesses:
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("Areas for Improvement", heading_style))

            for weakness in data.weaknesses:
                story.append(Paragraph(f"• {weakness}", normal_style))

        # Highlight sections
        if data.highlight_sections:
            story.append(PageBreak())
            story.append(Paragraph("Resume Section Highlights", heading_style))

            for section, explanation in data.highlight_sections.items():
                story.append(Paragraph(f"<b>{section}:</b>", normal_style))
                story.append(Paragraph(explanation, normal_style))
                story.append(Spacer(1, 0.1 * inch))

        # Footer with timestamp
        story.append(Spacer(1, 0.5 * inch))
        footer_style = ParagraphStyle(
            "Footer",
            parent=normal_style,
            fontSize=9,
            textColor=colors.HexColor("#7f8c8d"),
            alignment=TA_CENTER,
        )
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        story.append(
            Paragraph(
                f"Generated: {timestamp} | Resume ID: {data.resume_id} | Vacancy ID: {data.vacancy_id}",
                footer_style
            )
        )

        # Build PDF
        doc.build(story)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    async def _generate_text_fallback(
        self,
        resume_id: str,
        vacancy_id: str,
        data: ReportData,
        report_type: str,
    ) -> PDFGenerationResult:
        """
        Generate text-based fallback when reportlab is not available.

        This creates a simple text representation that can be saved as .txt
        or easily converted to PDF using external tools.

        Args:
            resume_id: Resume UUID
            vacancy_id: Vacancy UUID
            data: Report data
            report_type: Type of report

        Returns:
            PDFGenerationResult with text content (as pdf_bytes)
        """
        lines = []
        lines.append("=" * 80)
        lines.append("CANDIDATE RANKING EXPLANATION REPORT".center(80))
        lines.append("=" * 80)
        lines.append("")

        # Basic info
        if data.job_title:
            lines.append(f"Position: {data.job_title}")
        if data.candidate_name:
            lines.append(f"Candidate: {data.candidate_name}")
        lines.append(f"Overall Score: {data.rank_score:.1%}")
        if data.rank_position is not None:
            lines.append(f"Rank Position: #{data.rank_position}")
        lines.append(f"Recommendation: {data.recommendation.upper()}")
        lines.append("")

        # Narrative
        lines.append("-" * 80)
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(data.narrative)
        lines.append("")

        # Feature breakdowns
        if data.feature_explanations:
            lines.append("-" * 80)
            lines.append("FEATURE CONTRIBUTION BREAKDOWN")
            lines.append("-" * 80)
            lines.append(f"{'Feature':<30} {'Value':<12} {'Contribution':<20} {'Impact':<10}")
            lines.append("-" * 80)

            for feature in data.feature_explanations:
                name = feature.get("name", "N/A")[:30]
                value = feature.get("value", 0)
                contrib = feature.get("contribution", 0)
                contrib_pct = feature.get("contribution_percent", 0)
                impact = feature.get("impact_level", "medium").title()

                value_str = f"{value:.3f}" if isinstance(value, (int, float)) else str(value)
                contrib_str = f"{contrib:.3f} ({contrib_pct:.1f}%)"

                lines.append(f"{name:<30} {value_str:<12} {contrib_str:<20} {impact:<10}")
            lines.append("")

        # Confidence interval
        if data.confidence_interval:
            lines.append("-" * 80)
            lines.append("CONFIDENCE INTERVAL")
            lines.append("-" * 80)
            ci = data.confidence_interval
            lines.append(f"Lower Bound: {ci.get('lower', 0):.1%}")
            lines.append(f"Upper Bound: {ci.get('upper', 0):.1%}")
            lines.append(f"Confidence Level: {ci.get('confidence_level', 0):.0%}")
            lines.append(f"Margin of Error: ±{ci.get('margin_of_error', 0):.1%}")
            lines.append(f"")
            lines.append(ci.get('explanation', ''))
            lines.append("")

        # Strengths
        if data.strengths:
            lines.append("-" * 80)
            lines.append("CANDIDATE STRENGTHS")
            lines.append("-" * 80)
            for strength in data.strengths:
                lines.append(f"  • {strength}")
            lines.append("")

        # Weaknesses
        if data.weaknesses:
            lines.append("-" * 80)
            lines.append("AREAS FOR IMPROVEMENT")
            lines.append("-" * 80)
            for weakness in data.weaknesses:
                lines.append(f"  • {weakness}")
            lines.append("")

        # Highlight sections
        if data.highlight_sections:
            lines.append("-" * 80)
            lines.append("RESUME SECTION HIGHLIGHTS")
            lines.append("-" * 80)
            for section, explanation in data.highlight_sections.items():
                lines.append(f"{section}:")
                lines.append(f"  {explanation}")
                lines.append("")

        # Footer
        lines.append("=" * 80)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"Generated: {timestamp} | Resume ID: {data.resume_id} | Vacancy ID: {data.vacancy_id}")
        lines.append("=" * 80)

        # Generate filename
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        candidate_name = data.candidate_name or "candidate"
        filename = f"explainability_{candidate_name}_{timestamp_str}.txt"

        text_content = "\n".join(lines)
        text_bytes = text_content.encode("utf-8")

        return PDFGenerationResult(
            success=True,
            pdf_bytes=text_bytes,
            filename=filename,
            content_type="text/plain",
            file_size=len(text_bytes),
        )


def get_report_generator() -> Optional[ReportGenerator]:
    """
    Get the global report generator instance.

    Returns the singleton ReportGenerator instance, creating it if necessary.
    Returns None if reportlab is not available and fallback mode is disabled.

    Returns:
        ReportGenerator instance or None

    Example:
        >>> generator = get_report_generator()
        >>> if generator:
        ...     result = await generator.generate_explainability_pdf(...)
    """
    global _report_generator

    if _report_generator is None:
        _report_generator = ReportGenerator()

    return _report_generator if _report_generator.is_available() else None
