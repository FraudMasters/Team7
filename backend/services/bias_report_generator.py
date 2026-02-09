"""
PDF Report Generation Service for Bias Analysis Reports.

This module provides functionality to generate professional PDF reports
from fairness metrics data, including executive summary, methodology,
metrics by demographic, findings, and actionable recommendations.

The service supports:
- PDF generation from bias analysis data
- Professional formatting with headers, footers, and branding
- Visual elements for disparate impact ratios and severity indicators
- Multi-page reports with table of contents
- Export options for different report types

Report types:
- executive_summary: High-level overview for stakeholders
- detailed_analysis: Comprehensive technical analysis
- compliance_report: Compliance-focused documentation
- scorecard: Visual scorecard with recommendations
"""
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from config import get_settings
from models import FairnessMetrics, FairnessAlert, JobVacancy
from services.fairness_scorecard import FairnessScorecardData, get_fairness_scorecard

logger = logging.getLogger(__name__)

# Global report generator instance
_bias_report_generator: Optional["BiasReportGenerator"] = None


@dataclass
class BiasReportData:
    """
    Data structure for bias analysis report.

    Attributes:
        report_id: Unique report identifier (UUID)
        vacancy_id: Optional JobVacancy UUID for vacancy-specific reports
        vacancy_title: Job title for context
        model_version: Model version analyzed
        report_type: Type of report generated
        overall_fairness_score: Overall fairness score (0-100)
        bias_detected: Whether bias was detected
        severity_level: Maximum severity level across all findings
        executive_summary: High-level summary of findings
        methodology: Analysis methodology description
        metrics_by_demographic: Detailed metrics grouped by demographic attribute
        findings: List of specific bias findings
        recommendations: List of actionable recommendations
        feature_bias_sources: Feature-level bias sources identified
        alerts_summary: Summary of active alerts by severity
        generated_at: Timestamp of report generation
        total_sample_size: Total candidates analyzed
        demographics_analyzed: List of demographic attributes analyzed
        analysis_metadata: Additional analysis metadata
    """
    report_id: str
    vacancy_id: Optional[str] = None
    vacancy_title: Optional[str] = None
    model_version: Optional[str] = None
    report_type: str = "detailed_analysis"
    overall_fairness_score: float = 0.0
    bias_detected: bool = False
    severity_level: str = "low"
    executive_summary: str = ""
    methodology: str = ""
    metrics_by_demographic: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    feature_bias_sources: List[Dict[str, Any]] = field(default_factory=list)
    alerts_summary: Dict[str, int] = field(default_factory=dict)
    generated_at: str = ""
    total_sample_size: int = 0
    demographics_analyzed: List[str] = field(default_factory=list)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "report_id": self.report_id,
            "vacancy_id": self.vacancy_id,
            "vacancy_title": self.vacancy_title,
            "model_version": self.model_version,
            "report_type": self.report_type,
            "overall_fairness_score": self.overall_fairness_score,
            "bias_detected": self.bias_detected,
            "severity_level": self.severity_level,
            "executive_summary": self.executive_summary,
            "methodology": self.methodology,
            "metrics_by_demographic": self.metrics_by_demographic,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "feature_bias_sources": self.feature_bias_sources,
            "alerts_summary": self.alerts_summary,
            "generated_at": self.generated_at,
            "total_sample_size": self.total_sample_size,
            "demographics_analyzed": self.demographics_analyzed,
            "analysis_metadata": self.analysis_metadata,
        }


@dataclass
class BiasReportGenerationResult:
    """
    Result of bias report generation.

    Attributes:
        success: Whether report generation succeeded
        report_bytes: Generated report content as bytes
        filename: Suggested filename for the report
        content_type: MIME type (application/pdf or text/csv)
        error_message: Error message if generation failed
        file_size: Size of generated report in bytes
    """
    success: bool
    report_bytes: Optional[bytes] = None
    filename: Optional[str] = None
    content_type: str = "application/pdf"
    error_message: Optional[str] = None
    file_size: int = 0


class BiasReportGenerator:
    """
    Bias Report Generation Service.

    This service generates professional bias analysis reports from fairness
    metrics data, including executive summaries, methodology documentation,
    demographic breakdowns, findings, and actionable recommendations.

    The service uses reportlab for PDF generation with the following features:
    - Professional formatting with headers and footers
    - Visual elements for disparate impact ratios
    - Severity-based color coding
    - Multi-page layout support
    - Brand elements and company logo (optional)

    Attributes:
        enabled: Whether report generation is enabled
        page_format: Default page format (A4, Letter)
        margin: Default page margins in points
        include_branding: Whether to include branding elements

    Example:
        >>> generator = BiasReportGenerator()
        >>> result = await generator.generate_bias_report(
        ...     db=db,
        ...     vacancy_id=vacancy_id,
        ...     report_type="detailed_analysis"
        ... )
        >>> if result.success:
        ...     with open("bias_report.pdf", "wb") as f:
        ...         f.write(result.report_bytes)
    """

    # Page format constants
    PAGE_FORMAT_A4 = "A4"
    PAGE_FORMAT_LETTER = "Letter"

    # Report type constants
    REPORT_TYPE_EXECUTIVE = "executive_summary"
    REPORT_TYPE_DETAILED = "detailed_analysis"
    REPORT_TYPE_COMPLIANCE = "compliance_report"
    REPORT_TYPE_SCORECARD = "scorecard"

    # Severity colors for PDF generation
    SEVERITY_COLORS = {
        "low": "#27ae60",
        "medium": "#f39c12",
        "high": "#e67e22",
        "critical": "#e74c3c",
    }

    def __init__(
        self,
        enabled: Optional[bool] = None,
        page_format: str = PAGE_FORMAT_A4,
        margin: int = 72,  # 1 inch in points
        include_branding: bool = True,
    ) -> None:
        """
        Initialize the bias report generator.

        Args:
            enabled: Whether report generation is enabled
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
                logger.info("BiasReportGenerator initialized with reportlab")
            except ImportError:
                logger.warning(
                    "reportlab not installed, PDF generation will use fallback mode. "
                    "Install with: pip install reportlab"
                )
                self.enabled = False

    def is_available(self) -> bool:
        """Check if PDF generation is available."""
        return self.enabled and self._reportlab_available

    async def generate_bias_report(
        self,
        db: AsyncSession,
        vacancy_id: Optional[UUID] = None,
        model_version: Optional[str] = None,
        analysis_date: Optional[str] = None,
        report_type: str = REPORT_TYPE_DETAILED,
    ) -> BiasReportGenerationResult:
        """
        Generate bias analysis report from fairness metrics.

        Args:
            db: Database session
            vacancy_id: Optional JobVacancy UUID for specific vacancy report
            model_version: Optional model version filter
            analysis_date: Optional analysis date filter
            report_type: Type of report to generate

        Returns:
            BiasReportGenerationResult with generated report bytes or error

        Raises:
            ValueError: If report_type is unsupported or data is invalid
        """
        try:
            logger.info(
                f"Generating bias report for vacancy {vacancy_id}, "
                f"model {model_version}, type {report_type}"
            )

            # Validate report type
            if report_type not in [
                self.REPORT_TYPE_EXECUTIVE,
                self.REPORT_TYPE_DETAILED,
                self.REPORT_TYPE_COMPLIANCE,
                self.REPORT_TYPE_SCORECARD,
            ]:
                raise ValueError(f"Unsupported report type: {report_type}")

            # Fetch and compile report data
            report_data = await self._compile_report_data(
                db, vacancy_id, model_version, analysis_date, report_type
            )

            if not report_data:
                logger.warning("No data available for bias report generation")
                return BiasReportGenerationResult(
                    success=False,
                    error_message="No fairness metrics data available for the specified criteria",
                )

            # Check if reportlab is available
            if not self.is_available():
                logger.warning("reportlab not available, using text-based fallback")
                return await self._generate_text_fallback(report_data, report_type)

            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            vacancy_slug = report_data.vacancy_title or "org-wide" if report_data else "report"
            vacancy_slug = vacancy_slug.lower().replace(" ", "_")[:30]
            filename = f"bias_report_{vacancy_slug}_{timestamp}.pdf"

            # Generate PDF using reportlab
            report_bytes = await self._generate_pdf_with_reportlab(report_data, report_type)

            logger.info(
                f"Bias report generated successfully: {filename} "
                f"({len(report_bytes)} bytes)"
            )

            return BiasReportGenerationResult(
                success=True,
                report_bytes=report_bytes,
                filename=filename,
                content_type="application/pdf",
                file_size=len(report_bytes),
            )

        except Exception as e:
            logger.error(f"Error generating bias report: {e}", exc_info=True)
            return BiasReportGenerationResult(
                success=False,
                error_message=str(e),
            )

    async def _compile_report_data(
        self,
        db: AsyncSession,
        vacancy_id: Optional[UUID],
        model_version: Optional[str],
        analysis_date: Optional[str],
        report_type: str,
    ) -> Optional[BiasReportData]:
        """
        Compile report data from fairness metrics and scorecard.

        Args:
            db: Database session
            vacancy_id: Optional vacancy filter
            model_version: Optional model version filter
            analysis_date: Optional analysis date filter
            report_type: Type of report being generated

        Returns:
            BiasReportData with compiled information or None
        """
        try:
            # Generate scorecard for base data
            scorecard_service = get_fairness_scorecard()
            scorecard = await scorecard_service.generate_scorecard(
                db=db,
                vacancy_id=vacancy_id,
                model_version=model_version,
                analysis_date=analysis_date,
            )

            # Fetch metrics for detailed findings
            metrics = await self._fetch_fairness_metrics(
                db, vacancy_id, model_version, analysis_date
            )

            if not metrics:
                return None

            # Fetch related alerts
            alerts = await self._fetch_fairness_alerts(db, [m.id for m in metrics])

            # Generate report ID
            from uuid import uuid4
            report_id = str(uuid4())

            # Compile findings
            findings = self._compile_findings(metrics, alerts)

            # Compile executive summary
            executive_summary = self._generate_executive_summary(
                scorecard, findings, report_type
            )

            # Compile methodology
            methodology = self._generate_methodology(metrics, report_type)

            # Determine severity level
            severity_level = self._determine_severity_level(
                scorecard.alerts_summary, findings
            )

            return BiasReportData(
                report_id=report_id,
                vacancy_id=str(vacancy_id) if vacancy_id else None,
                vacancy_title=scorecard.vacancy_title,
                model_version=scorecard.model_version,
                report_type=report_type,
                overall_fairness_score=scorecard.fairness_score,
                bias_detected=any(f.get("severity") in ["high", "critical"] for f in findings),
                severity_level=severity_level,
                executive_summary=executive_summary,
                methodology=methodology,
                metrics_by_demographic=scorecard.metrics_by_demographic,
                findings=findings,
                recommendations=scorecard.recommendations,
                feature_bias_sources=scorecard.feature_bias_sources,
                alerts_summary=scorecard.alerts_summary,
                generated_at=datetime.utcnow().isoformat(),
                total_sample_size=scorecard.total_sample_size,
                demographics_analyzed=scorecard.demographics_analyzed,
                analysis_metadata={
                    "analysis_date": analysis_date,
                    "report_type": report_type,
                    "metrics_count": len(metrics),
                    "alerts_count": len(alerts),
                },
            )

        except Exception as e:
            logger.error(f"Error compiling report data: {e}", exc_info=True)
            return None

    async def _fetch_fairness_metrics(
        self,
        db: AsyncSession,
        vacancy_id: Optional[UUID],
        model_version: Optional[str],
        analysis_date: Optional[str],
    ) -> List[FairnessMetrics]:
        """Fetch fairness metrics from database."""
        query = select(FairnessMetrics)

        if vacancy_id:
            query = query.where(FairnessMetrics.vacancy_id == vacancy_id)

        if model_version:
            query = query.where(FairnessMetrics.model_version_id == model_version)

        if analysis_date:
            query = query.where(FairnessMetrics.analysis_date == analysis_date)
        else:
            # Get most recent analysis date
            latest_date_query = select(
                FairnessMetrics.analysis_date
            ).order_by(
                FairnessMetrics.analysis_date.desc()
            ).limit(1)

            if vacancy_id:
                latest_date_query = latest_date_query.where(
                    FairnessMetrics.vacancy_id == vacancy_id
                )

            latest_date_result = await db.execute(latest_date_query)
            latest_date = latest_date_result.scalar_one_or_none()

            if latest_date:
                query = query.where(FairnessMetrics.analysis_date == latest_date)

        query = query.order_by(FairnessMetrics.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def _fetch_fairness_alerts(
        self,
        db: AsyncSession,
        metric_ids: List[UUID],
    ) -> List[FairnessAlert]:
        """Fetch fairness alerts for given metric IDs."""
        if not metric_ids:
            return []

        query = select(FairnessAlert).where(
            FairnessAlert.fairness_metric_id.in_(metric_ids)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    def _compile_findings(
        self,
        metrics: List[FairnessMetrics],
        alerts: List[FairnessAlert],
    ) -> List[Dict[str, Any]]:
        """
        Compile findings from metrics and alerts.

        Args:
            metrics: List of fairness metrics
            alerts: List of fairness alerts

        Returns:
            List of finding dictionaries
        """
        findings = []

        # Findings from triggered alerts
        for alert in alerts:
            if alert.status == "active":
                findings.append({
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "demographic_group": self._get_demographic_from_alert(
                        alert, metrics
                    ),
                    "description": alert.message,
                    "threshold_value": float(alert.threshold_value or 0),
                    "actual_value": float(alert.actual_value or 0),
                    "recommendation": alert.alert_metadata.get("recommendation")
                        if alert.alert_metadata else None,
                })

        # Findings from metrics with alerts triggered but no explicit alert record
        for metric in metrics:
            if metric.alert_triggered:
                # Check if we already have an alert finding for this metric
                existing_alert = any(
                    f.get("demographic_group") == metric.demographic_group
                    for f in findings
                )

                if not existing_alert:
                    findings.append({
                        "type": "metric_threshold",
                        "severity": metric.alert_severity or "medium",
                        "demographic_group": metric.demographic_group,
                        "description": (
                            f"Fairness threshold exceeded for {metric.demographic_group}. "
                            f"Disparate Impact Ratio: {metric.disparate_impact_ratio:.3f}"
                        ),
                        "threshold_value": float(metric.alert_threshold or 0.8),
                        "actual_value": float(metric.disparate_impact_ratio or 0),
                        "recommendation": metric.mitigation_suggested,
                    })

        # Sort by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        findings.sort(key=lambda f: severity_order.get(f.get("severity", "low"), 4))

        return findings

    def _get_demographic_from_alert(
        self,
        alert: FairnessAlert,
        metrics: List[FairnessMetrics],
    ) -> str:
        """Get demographic group from alert by matching to metric."""
        for metric in metrics:
            if metric.id == alert.fairness_metric_id:
                return metric.demographic_group
        return "unknown"

    def _generate_executive_summary(
        self,
        scorecard: FairnessScorecardData,
        findings: List[Dict[str, Any]],
        report_type: str,
    ) -> str:
        """
        Generate executive summary for the report.

        Args:
            scorecard: Fairness scorecard data
            findings: List of findings
            report_type: Type of report

        Returns:
            Executive summary text
        """
        score = scorecard.fairness_score
        vacancy_context = f" for '{scorecard.vacancy_title}'" if scorecard.vacancy_title else ""

        summary_parts = []

        # Overall assessment
        if score >= 90:
            summary_parts.append(
                f"This bias analysis report{vacancy_context} demonstrates excellent fairness "
                f"across all demographic groups with an overall fairness score of {score:.1f}/100."
            )
        elif score >= 75:
            summary_parts.append(
                f"This bias analysis report{vacancy_context} indicates good fairness "
                f"with an overall score of {score:.1f}/100. Minor improvements are recommended."
            )
        elif score >= 60:
            summary_parts.append(
                f"This bias analysis report{vacancy_context} identifies fairness concerns "
                f"with an overall score of {score:.1f}/100. Attention is recommended."
            )
        else:
            summary_parts.append(
                f"This bias analysis report{vacancy_context} reveals significant fairness concerns "
                f"with a score of {score:.1f}/100. Immediate action is recommended."
            )

        # Findings summary
        critical_count = sum(1 for f in findings if f.get("severity") == "critical")
        high_count = sum(1 for f in findings if f.get("severity") == "high")

        if critical_count > 0 or high_count > 0:
            alert_summary = f" The analysis identified {critical_count} critical and {high_count} high severity findings."
            summary_parts.append(alert_summary)

        # Sample size note
        if scorecard.total_sample_size < 100:
            summary_parts.append(
                f" Note: Analysis based on {scorecard.total_sample_size} candidates. "
                "Larger sample sizes would improve statistical confidence."
            )

        return " ".join(summary_parts)

    def _generate_methodology(
        self,
        metrics: List[FairnessMetrics],
        report_type: str,
    ) -> str:
        """
        Generate methodology description for the report.

        Args:
            metrics: List of fairness metrics
            report_type: Type of report

        Returns:
            Methodology description text
        """
        methodology_parts = [
            "This bias analysis evaluates fairness across demographic groups inferred from ",
            "resume patterns using the following metrics:"
        ]

        # Disparate Impact
        methodology_parts.append(
            "\n\n<b>Disparate Impact Ratio (80% Rule):</b> Measures the ratio of "
            "selection rates between demographic groups. A ratio below 0.80 indicates "
            "potential adverse impact per the EEOC Uniform Guidelines."
        )

        # Statistical Parity
        methodology_parts.append(
            "\n\n<b>Statistical Parity Difference:</b> Calculates the difference in "
            "selection rates between groups. Values closer to zero indicate greater fairness."
        )

        # Demographics analyzed
        demographics = sorted(set(m.demographic_group for m in metrics))
        methodology_parts.append(
            f"\n\n<b>Demographics Analyzed:</b> {', '.join(demographics)}"
        )

        # Fairness-aware mode
        fairness_aware_count = sum(1 for m in metrics if m.is_fairness_aware)
        if fairness_aware_count > 0:
            methodology_parts.append(
                f"\n\n<b>Fairness-Aware Analysis:</b> {fairness_aware_count} analyses "
                "used fairness-aware ranking algorithms to reduce algorithmic bias."
            )

        # Sample size
        total_samples = max((m.total_sample_size or 0) for m in metrics) if metrics else 0
        methodology_parts.append(f"\n\n<b>Total Sample Size:</b> {total_samples} candidates")

        return "".join(methodology_parts)

    def _determine_severity_level(
        self,
        alerts_summary: Dict[str, int],
        findings: List[Dict[str, Any]],
    ) -> str:
        """
        Determine overall severity level from alerts and findings.

        Args:
            alerts_summary: Alert counts by severity
            findings: List of findings

        Returns:
            Overall severity level (critical, high, medium, low)
        """
        if alerts_summary.get("critical", 0) > 0:
            return "critical"
        if alerts_summary.get("high", 0) > 0:
            return "high"
        if alerts_summary.get("medium", 0) > 0:
            return "medium"
        return "low"

    async def _generate_pdf_with_reportlab(
        self,
        data: BiasReportData,
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

        subheading_style = ParagraphStyle(
            "CustomSubheading",
            parent=styles["Heading3"],
            fontSize=13,
            textColor=colors.HexColor("#7f8c8d"),
            spaceAfter=10,
        )

        normal_style = styles["BodyText"]
        normal_style.fontSize = 11

        # Build story (content elements)
        story = []

        # Title page
        story.append(Paragraph("AI Bias Analysis Report", title_style))
        story.append(Spacer(1, 0.3 * inch))

        # Report info
        if data.vacancy_title:
            story.append(
                Paragraph(
                    f"<b>Position:</b> {data.vacancy_title}",
                    normal_style
                )
            )

        if data.model_version:
            story.append(
                Paragraph(
                    f"<b>Model Version:</b> {data.model_version}",
                    normal_style
                )
            )

        # Overall score with color coding
        score_color = self._get_score_color(data.overall_fairness_score)
        score_style = ParagraphStyle(
            "ScoreStyle",
            parent=normal_style,
            fontSize=18,
            textColor=colors.HexColor(score_color),
            spaceAfter=10,
        )
        story.append(
            Paragraph(
                f"<b>Overall Fairness Score:</b> {data.overall_fairness_score:.1f}/100",
                score_style
            )
        )

        # Bias detected indicator
        if data.bias_detected:
            bias_style = ParagraphStyle(
                "BiasStyle",
                parent=normal_style,
                fontSize=14,
                textColor=colors.HexColor(self.SEVERITY_COLORS.get(data.severity_level, "#e74c3c")),
            )
            story.append(
                Paragraph(
                    f"<b>Bias Detected:</b> {data.severity_level.upper()} SEVERITY",
                    bias_style
                )
            )
        else:
            story.append(
                Paragraph(
                    "<b>Bias Detected:</b> No significant bias detected",
                    ParagraphStyle(
                        "NoBiasStyle",
                        parent=normal_style,
                        fontSize=14,
                        textColor=colors.HexColor("#27ae60"),
                    )
                )
            )

        story.append(Spacer(1, 0.3 * inch))

        # Report metadata
        metadata_table = [
            ["Report ID:", data.report_id[:8] + "..."],
            ["Report Type:", report_type.replace("_", " ").title()],
            ["Generated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Total Sample Size:", str(data.total_sample_size)],
            ["Demographics Analyzed:", ", ".join(data.demographics_analyzed)],
        ]

        metadata = Table(metadata_table, colWidths=[2 * inch, 4 * inch])
        metadata.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ecf0f1")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2c3e50")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(metadata)
        story.append(Spacer(1, 0.3 * inch))

        story.append(PageBreak())

        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        story.append(Paragraph(data.executive_summary, normal_style))
        story.append(Spacer(1, 0.2 * inch))

        # Alerts Summary
        if data.alerts_summary:
            story.append(Paragraph("Active Alerts Summary", subheading_style))
            alert_data = [["Severity", "Count"]]
            for severity in ["critical", "high", "medium", "low"]:
                count = data.alerts_summary.get(severity, 0)
                if count > 0:
                    alert_color = colors.HexColor(self.SEVERITY_COLORS.get(severity, "#95a5a6"))
                    alert_data.append([
                        f'<font color="{alert_color}">{severity.title()}</font>',
                        str(count)
                    ])

            if len(alert_data) > 1:
                alert_table = Table(alert_data, colWidths=[2 * inch, 1 * inch])
                alert_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#bdc3c7")),
                ]))
                story.append(alert_table)

        story.append(PageBreak())

        # Methodology
        story.append(Paragraph("Methodology", heading_style))
        story.append(Paragraph(data.methodology, normal_style))
        story.append(Spacer(1, 0.2 * inch))

        # Findings
        if data.findings:
            story.append(PageBreak())
            story.append(Paragraph("Findings", heading_style))

            for i, finding in enumerate(data.findings, 1):
                severity = finding.get("severity", "low")
                severity_color = self.SEVERITY_COLORS.get(severity, "#95a5a6")

                # Finding header with severity color
                finding_style = ParagraphStyle(
                    f"FindingStyle{i}",
                    parent=subheading_style,
                    textColor=colors.HexColor(severity_color),
                )
                story.append(
                    Paragraph(
                        f"{i}. {finding.get('type', 'Unknown').replace('_', ' ').title()} "
                        f"({severity.upper()})",
                        finding_style
                    )
                )

                # Finding details
                story.append(
                    Paragraph(
                        finding.get("description", ""),
                        normal_style
                    )
                )

                # Add values if available
                if finding.get("actual_value") is not None:
                    story.append(
                        Paragraph(
                            f"<b>Threshold:</b> {finding.get('threshold_value', 0):.3f} | "
                            f"<b>Actual:</b> {finding.get('actual_value', 0):.3f}",
                            ParagraphStyle(
                                "FindingDetails",
                                parent=normal_style,
                                fontSize=10,
                                textColor=colors.HexColor("#7f8c8d"),
                            )
                        )
                    )

                story.append(Spacer(1, 0.1 * inch))

        # Metrics by Demographic
        if data.metrics_by_demographic:
            story.append(PageBreak())
            story.append(Paragraph("Metrics by Demographic", heading_style))

            for demographic, metrics_data in data.metrics_by_demographic.items():
                story.append(Paragraph(demographic.replace("_", " ").title(), subheading_style))

                metric_table = [
                    ["Metric", "Value"],
                    ["Disparate Impact Ratio", f"{metrics_data.get('disparate_impact_ratio', 0):.3f}"],
                    ["Statistical Parity Diff", f"{metrics_data.get('statistical_parity_difference', 0):.3f}"],
                    ["Selection Rate", f"{metrics_data.get('group_selection_rate', 0):.1%}"]
                        if metrics_data.get('group_selection_rate') else None,
                    ["Sample Size", str(metrics_data.get('total_sample_size', 0))],
                ]

                # Filter out None values
                metric_table = [row for row in metric_table if row is not None]

                table = Table(metric_table, colWidths=[2.5 * inch, 1.5 * inch])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#bdc3c7")),
                ]))
                story.append(table)
                story.append(Spacer(1, 0.15 * inch))

        # Recommendations
        if data.recommendations:
            story.append(PageBreak())
            story.append(Paragraph("Recommendations", heading_style))

            for i, recommendation in enumerate(data.recommendations, 1):
                story.append(Paragraph(f"{i}. {recommendation}", normal_style))

        # Feature Bias Sources
        if data.feature_bias_sources:
            story.append(PageBreak())
            story.append(Paragraph("Feature-Level Bias Sources", heading_style))

            for i, source in enumerate(data.feature_bias_sources[:10], 1):
                severity = source.get("severity", "low")
                severity_color = self.SEVERITY_COLORS.get(severity, "#95a5a6")

                source_style = ParagraphStyle(
                    f"SourceStyle{i}",
                    parent=subheading_style,
                    textColor=colors.HexColor(severity_color),
                )
                story.append(
                    Paragraph(
                        f"{i}. {source.get('feature_label', source.get('feature_name'))} "
                        f"({severity.upper()})",
                        source_style
                    )
                )
                story.append(
                    Paragraph(
                        source.get("recommendation", ""),
                        normal_style
                    )
                )
                story.append(Spacer(1, 0.1 * inch))

        # Footer with timestamp and disclaimer
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
                f"Generated: {timestamp} | Report ID: {data.report_id}",
                footer_style
            )
        )
        story.append(
            Paragraph(
                "This report is based on demographic inferences from resume patterns. "
                "Actual demographic data was not collected. Results should be validated "
                "with additional analysis.",
                ParagraphStyle(
                    "Disclaimer",
                    parent=footer_style,
                    fontStyle="Italic",
                )
            )
        )

        # Build PDF
        doc.build(story)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _get_score_color(self, score: float) -> str:
        """Get color for fairness score display."""
        if score >= 90:
            return "#27ae60"  # Green
        elif score >= 75:
            return "#3498db"  # Blue
        elif score >= 60:
            return "#f39c12"  # Orange
        else:
            return "#e74c3c"  # Red

    async def _generate_text_fallback(
        self,
        data: BiasReportData,
        report_type: str,
    ) -> BiasReportGenerationResult:
        """
        Generate text-based fallback when reportlab is not available.

        Args:
            data: Report data
            report_type: Type of report

        Returns:
            BiasReportGenerationResult with text content
        """
        lines = []
        lines.append("=" * 80)
        lines.append("AI BIAS ANALYSIS REPORT".center(80))
        lines.append("=" * 80)
        lines.append("")

        # Basic info
        if data.vacancy_title:
            lines.append(f"Position: {data.vacancy_title}")
        if data.model_version:
            lines.append(f"Model Version: {data.model_version}")
        lines.append(f"Overall Fairness Score: {data.overall_fairness_score:.1f}/100")
        lines.append(f"Bias Detected: {data.severity_level.upper() if data.bias_detected else 'No'}")
        lines.append(f"Report Type: {report_type.replace('_', ' ').title()}")
        lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")

        # Executive Summary
        lines.append("-" * 80)
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(data.executive_summary)
        lines.append("")

        # Findings
        if data.findings:
            lines.append("-" * 80)
            lines.append("FINDINGS")
            lines.append("-" * 80)
            for i, finding in enumerate(data.findings, 1):
                lines.append(f"{i}. [{finding.get('severity', 'low').upper()}] {finding.get('type', 'Unknown')}")
                lines.append(f"   {finding.get('description', '')}")
                if finding.get('actual_value') is not None:
                    lines.append(
                        f"   Threshold: {finding.get('threshold_value', 0):.3f} | "
                        f"Actual: {finding.get('actual_value', 0):.3f}"
                    )
                lines.append("")

        # Metrics by Demographic
        if data.metrics_by_demographic:
            lines.append("-" * 80)
            lines.append("METRICS BY DEMOGRAPHIC")
            lines.append("-" * 80)
            for demographic, metrics_data in data.metrics_by_demographic.items():
                lines.append(f"\n{demographic.replace('_', ' ').title()}:")
                lines.append(f"  Disparate Impact Ratio: {metrics_data.get('disparate_impact_ratio', 0):.3f}")
                lines.append(f"  Statistical Parity Diff: {metrics_data.get('statistical_parity_difference', 0):.3f}")
                lines.append(f"  Sample Size: {metrics_data.get('total_sample_size', 0)}")

        # Recommendations
        if data.recommendations:
            lines.append("")
            lines.append("-" * 80)
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 80)
            for i, recommendation in enumerate(data.recommendations, 1):
                lines.append(f"{i}. {recommendation}")

        # Footer
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"Report ID: {data.report_id}")
        lines.append("Generated by AgentHR Bias Detection System")
        lines.append("=" * 80)

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        vacancy_slug = data.vacancy_title or "org-wide"
        vacancy_slug = vacancy_slug.lower().replace(" ", "_")[:30]
        filename = f"bias_report_{vacancy_slug}_{timestamp}.txt"

        text_content = "\n".join(lines)
        text_bytes = text_content.encode("utf-8")

        return BiasReportGenerationResult(
            success=True,
            report_bytes=text_bytes,
            filename=filename,
            content_type="text/plain",
            file_size=len(text_bytes),
        )

    async def generate_csv_export(
        self,
        db: AsyncSession,
        vacancy_id: Optional[UUID] = None,
        model_version: Optional[str] = None,
        analysis_date: Optional[str] = None,
    ) -> BiasReportGenerationResult:
        """
        Generate CSV export of raw fairness metrics data.

        Args:
            db: Database session
            vacancy_id: Optional JobVacancy UUID for specific vacancy export
            model_version: Optional model version filter
            analysis_date: Optional analysis date filter

        Returns:
            BiasReportGenerationResult with CSV content
        """
        try:
            import csv

            logger.info(
                f"Generating CSV export for vacancy {vacancy_id}, "
                f"model {model_version}"
            )

            # Fetch metrics
            metrics = await self._fetch_fairness_metrics(
                db, vacancy_id, model_version, analysis_date
            )

            if not metrics:
                return BiasReportGenerationResult(
                    success=False,
                    error_message="No fairness metrics data available for export",
                )

            # Prepare CSV data
            output = io.StringIO()
            writer = csv.writer(output)

            # Header row
            writer.writerow([
                "metric_id",
                "vacancy_id",
                "model_version_id",
                "analysis_date",
                "demographic_group",
                "disparate_impact_ratio",
                "statistical_parity_difference",
                "group_selection_rate",
                "overall_selection_rate",
                "group_sample_size",
                "total_sample_size",
                "alert_threshold",
                "alert_triggered",
                "alert_severity",
                "mitigation_suggested",
                "is_fairness_aware",
            ])

            # Data rows
            for metric in metrics:
                writer.writerow([
                    str(metric.id),
                    str(metric.vacancy_id) if metric.vacancy_id else "",
                    metric.model_version_id or "",
                    metric.analysis_date,
                    metric.demographic_group,
                    f"{metric.disparate_impact_ratio or 0:.4f}",
                    f"{metric.statistical_parity_difference or 0:.4f}",
                    f"{metric.group_selection_rate or 0:.4f}",
                    f"{metric.overall_selection_rate or 0:.4f}",
                    metric.group_sample_size or 0,
                    metric.total_sample_size or 0,
                    f"{metric.alert_threshold or 0:.4f}",
                    metric.alert_triggered,
                    metric.alert_severity or "",
                    metric.mitigation_suggested or "",
                    metric.is_fairness_aware,
                ])

            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            vacancy_slug = "org-wide"
            if vacancy_id:
                vacancy = await db.execute(
                    select(JobVacancy.title).where(JobVacancy.id == vacancy_id)
                )
                vacancy_title = vacancy.scalar_one_or_none()
                if vacancy_title:
                    vacancy_slug = vacancy_title.lower().replace(" ", "_")[:30]

            filename = f"fairness_metrics_{vacancy_slug}_{timestamp}.csv"

            csv_bytes = output.getvalue().encode("utf-8")
            output.close()

            logger.info(
                f"CSV export generated successfully: {filename} "
                f"({len(csv_bytes)} bytes)"
            )

            return BiasReportGenerationResult(
                success=True,
                report_bytes=csv_bytes,
                filename=filename,
                content_type="text/csv",
                file_size=len(csv_bytes),
            )

        except Exception as e:
            logger.error(f"Error generating CSV export: {e}", exc_info=True)
            return BiasReportGenerationResult(
                success=False,
                error_message=str(e),
            )


def get_bias_report_generator() -> Optional["BiasReportGenerator"]:
    """
    Get the global bias report generator instance.

    Returns the singleton BiasReportGenerator instance, creating it if necessary.
    Returns None if reportlab is not available and fallback mode is disabled.

    Returns:
        BiasReportGenerator instance or None

    Example:
        >>> generator = get_bias_report_generator()
        >>> if generator:
        ...     result = await generator.generate_bias_report(...)
    """
    global _bias_report_generator

    if _bias_report_generator is None:
        _bias_report_generator = BiasReportGenerator()

    return _bias_report_generator if _bias_report_generator.is_available() else None
