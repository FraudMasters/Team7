"""
PDF Generator Service for Resume Templates.

This module provides functionality to generate PDF documents from
HTML resumes rendered using the template renderer service.

The service supports:
- HTML to PDF conversion using WeasyPrint
- Professional resume formatting with proper CSS support
- Multiple page formats (A4, Letter)
- Custom margins and page settings
- ATS-friendly PDF output
- Error handling and graceful fallback
- PDF metadata generation
- Font embedding for better compatibility

The service integrates with the template renderer to convert
HTML templates to professional PDF resumes that can be
downloaded by job seekers.

Example:
    >>> from services.pdf_generator import PDFGenerator
    >>> from services.template_renderer import TemplateRenderer
    >>> renderer = TemplateRenderer()
    >>> html = renderer.render_resume(template, resume_data)
    >>> generator = PDFGenerator()
    >>> result = await generator.generate_resume_pdf(html, "John Doe Resume")
    >>> if result.success:
    ...     with open("resume.pdf", "wb") as f:
    ...         f.write(result.pdf_bytes)
"""
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import get_settings

logger = logging.getLogger(__name__)

# Global PDF generator instance
_pdf_generator: Optional["PDFGenerator"] = None


@dataclass
class PDFGenerationOptions:
    """
    Configuration options for PDF generation.

    Attributes:
        page_format: Page size format ('A4' or 'Letter')
        margin_top: Top margin in millimeters
        margin_bottom: Bottom margin in millimeters
        margin_left: Left margin in millimeters
        margin_right: Right margin in millimeters
        dpi: Resolution for images in PDF
        embed_fonts: Whether to embed fonts for better compatibility
        enable_javascript: Whether to enable JavaScript (disabled by default for security)
        print_background: Whether to print background colors/graphics
        prefer_css_page_size: Whether to prefer CSS page size over default
    """
    page_format: str = "A4"
    margin_top: float = 20.0
    margin_bottom: float = 20.0
    margin_left: float = 20.0
    margin_right: float = 20.0
    dpi: int = 300
    embed_fonts: bool = True
    enable_javascript: bool = False
    print_background: bool = True
    prefer_css_page_size: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for WeasyPrint configuration."""
        return {
            "presentational_hints": True,
            "print_background": self.print_background,
            "prefer_css_page_size": self.prefer_css_page_size,
        }


@dataclass
class PDFMetadata:
    """
    Metadata for generated PDF documents.

    Attributes:
        title: Document title
        author: Document author
        subject: Document subject/description
        keywords: List of keywords for the document
        creator: Software that created the PDF
        creation_date: When the PDF was created
    """
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    creator: str = "AgentHR Resume Builder"
    creation_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for WeasyPrint metadata."""
        metadata = {}
        if self.title:
            metadata["title"] = self.title
        if self.author:
            metadata["author"] = self.author
        if self.subject:
            metadata["subject"] = self.subject
        if self.keywords:
            metadata["keywords"] = ", ".join(self.keywords)
        if self.creator:
            metadata["creator"] = self.creator
        if self.creation_date:
            metadata["created"] = self.creation_date
        return metadata


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
        page_count: Number of pages in the PDF
        metadata: PDF metadata included in the document
    """
    success: bool
    pdf_bytes: Optional[bytes] = None
    filename: Optional[str] = None
    content_type: str = "application/pdf"
    error_message: Optional[str] = None
    file_size: int = 0
    page_count: int = 0
    metadata: Optional[PDFMetadata] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "filename": self.filename,
            "content_type": self.content_type,
            "error_message": self.error_message,
            "file_size": self.file_size,
            "page_count": self.page_count,
            "metadata": self.metadata.to_dict() if self.metadata else None,
        }


class PDFGenerator:
    """
    PDF Generator Service for Resume Templates.

    This service converts HTML resumes (rendered by the template renderer)
    into professional PDF documents suitable for job applications.

    The service uses WeasyPrint for HTML-to-PDF conversion with support for:
    - Full CSS styling including flexbox and grid
    - Custom fonts and embedding
    - Proper page breaks for multi-page resumes
    - High DPI for crisp rendering
    - PDF metadata (title, author, etc.)
    - ATS-friendly output (simple, clean structure)

    WeasyPrint is preferred over reportlab for resumes because:
    - Better CSS support for modern layouts
    - More accurate HTML rendering
    - Easier to maintain with existing templates
    - Better font handling

    Attributes:
        enabled: Whether PDF generation is enabled
        default_options: Default PDF generation options
        weasyprint_available: Whether WeasyPrint library is available

    Example:
        >>> generator = PDFGenerator()
        >>> result = await generator.generate_resume_pdf(
        ...     html="<html>...</html>",
        ...     filename="John_Doe_Resume.pdf"
        ... )
        >>> if result.success:
        ...     with open("resume.pdf", "wb") as f:
        ...         f.write(result.pdf_bytes)
    """

    # Page format constants
    PAGE_FORMAT_A4 = "A4"
    PAGE_FORMAT_LETTER = "Letter"

    # Page sizes in millimeters
    PAGE_SIZES = {
        "A4": (210, 297),
        "Letter": (216, 279),
    }

    def __init__(
        self,
        enabled: Optional[bool] = None,
        default_options: Optional[PDFGenerationOptions] = None,
    ) -> None:
        """
        Initialize the PDF generator service.

        Args:
            enabled: Whether PDF generation is enabled
            default_options: Default PDF generation options
        """
        settings = get_settings()

        self.enabled = enabled if enabled is not None else True
        self.default_options = default_options or PDFGenerationOptions()

        # Try to import WeasyPrint, disable if not available
        self.weasyprint_available = False
        if self.enabled:
            try:
                from weasyprint import HTML, CSS
                from weasyprint.text.fonts import FontConfiguration

                self._HTML = HTML
                self._CSS = CSS
                self._FontConfiguration = FontConfiguration
                self.weasyprint_available = True
                logger.info("PDFGenerator initialized with WeasyPrint")
            except ImportError:
                logger.warning(
                    "WeasyPrint not installed, PDF generation will use fallback mode. "
                    "Install with: pip install weasyprint"
                )
                self.weasyprint_available = False
        else:
            logger.info("PDFGenerator initialized but disabled")

    def is_available(self) -> bool:
        """
        Check if PDF generation is available.

        Returns:
            True if WeasyPrint is available and enabled
        """
        return self.enabled and self.weasyprint_available

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing/replacing problematic characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem use
        """
        # Replace problematic characters with underscore
        problematic = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        sanitized = filename
        for char in problematic:
            sanitized = sanitized.replace(char, '_')

        # Ensure filename ends with .pdf
        if not sanitized.lower().endswith('.pdf'):
            sanitized += '.pdf'

        return sanitized

    def _generate_suggested_filename(
        self,
        candidate_name: Optional[str] = None,
        template_name: Optional[str] = None,
    ) -> str:
        """
        Generate a suggested filename for the resume PDF.

        Args:
            candidate_name: Name of the candidate
            template_name: Name of the template used

        Returns:
            Suggested filename in format: "FirstName_LastName_Resume_Template.pdf"
        """
        parts = []

        if candidate_name:
            # Convert name to filename-friendly format
            name_parts = candidate_name.strip().split()
            if name_parts:
                formatted_name = "_".join(
                    part.capitalize() for part in name_parts if part
                )
                parts.append(formatted_name)

        if not parts:
            parts.append("Resume")

        if template_name:
            template_formatted = template_name.strip().replace(" ", "_")
            parts.append(template_formatted)

        if len(parts) == 1:
            parts.append("Resume")

        filename = "_".join(parts)
        return self._sanitize_filename(filename)

    def _convert_mm_to_points(self, mm: float) -> float:
        """
        Convert millimeters to points (1/72 inch).

        Args:
            mm: Value in millimeters

        Returns:
            Value in points
        """
        # 1 inch = 25.4 mm = 72 points
        # Therefore: points = mm * 72 / 25.4
        return mm * 72 / 25.4

    async def generate_resume_pdf(
        self,
        html: str,
        filename: Optional[str] = None,
        candidate_name: Optional[str] = None,
        template_name: Optional[str] = None,
        metadata: Optional[PDFMetadata] = None,
        options: Optional[PDFGenerationOptions] = None,
    ) -> PDFGenerationResult:
        """
        Generate a PDF resume from HTML content.

        Args:
            html: HTML content rendered from template
            filename: Optional filename for the PDF (auto-generated if not provided)
            candidate_name: Name of the candidate for filename and metadata
            template_name: Name of the template used
            metadata: Optional PDF metadata
            options: Optional PDF generation options

        Returns:
            PDFGenerationResult with generated PDF or error details

        Raises:
            ValueError: If HTML content is empty or invalid

        Example:
            >>> result = await generator.generate_resume_pdf(
            ...     html="<html><body><h1>John Doe</h1></body></html>",
            ...     candidate_name="John Doe",
            ...     template_name="Modern"
            ... )
        """
        if not html or not html.strip():
            return PDFGenerationResult(
                success=False,
                error_message="HTML content is empty"
            )

        # Check if WeasyPrint is available
        if not self.is_available():
            return PDFGenerationResult(
                success=False,
                error_message="WeasyPrint is not available. Install with: pip install weasyprint"
            )

        # Use provided options or defaults
        generation_options = options or self.default_options

        # Generate filename if not provided
        if not filename:
            filename = self._generate_suggested_filename(
                candidate_name=candidate_name,
                template_name=template_name
            )
        else:
            filename = self._sanitize_filename(filename)

        # Prepare metadata
        if not metadata:
            metadata = PDFMetadata(
                title=f"{candidate_name} - Resume" if candidate_name else "Resume",
                author=candidate_name or "Candidate",
                subject="Professional Resume",
                keywords=["resume", "cv", "curriculum vitae"],
                creation_date=datetime.utcnow().isoformat(),
            )

        try:
            logger.info(
                f"Generating PDF resume: {filename} "
                f"(page_format={generation_options.page_format})"
            )

            # Create WeasyPrint HTML document
            html_doc = self._HTML(
                string=html,
                base_url="",
                metadata=metadata.to_dict(),
            )

            # Page configuration
            page_width, page_height = self.PAGE_SIZES.get(
                generation_options.page_format,
                self.PAGE_SIZES["A4"]
            )

            # CSS for page configuration
            page_css = f"""
            @page {{
                size: {page_width}mm {page_height}mm;
                margin: {generation_options.margin_top}mm {generation_options.margin_right}mm {generation_options.margin_bottom}mm {generation_options.margin_left}mm;
            }}
            """

            # Create CSS for page settings
            css = self._CSS(string=page_css)

            # Generate PDF
            font_config = self._FontConfiguration()
            pdf_bytes = html_doc.write_pdf(
                stylesheets=[css],
                font_config=font_config,
                presentational_hints=True,
                optimize_images=('lossless', None),
            )

            # Get page count from metadata
            page_count = len(html_doc.pages)

            file_size = len(pdf_bytes)

            logger.info(
                f"Successfully generated PDF: {filename} "
                f"({file_size} bytes, {page_count} pages)"
            )

            return PDFGenerationResult(
                success=True,
                pdf_bytes=pdf_bytes,
                filename=filename,
                content_type="application/pdf",
                file_size=file_size,
                page_count=page_count,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(
                f"Failed to generate PDF resume '{filename}': {e}",
                exc_info=True
            )
            return PDFGenerationResult(
                success=False,
                filename=filename,
                error_message=f"PDF generation failed: {str(e)}"
            )

    async def generate_resume_pdf_from_template(
        self,
        template_html: str,
        resume_data: Dict[str, Any],
        candidate_name: Optional[str] = None,
        template_name: Optional[str] = None,
        metadata: Optional[PDFMetadata] = None,
        options: Optional[PDFGenerationOptions] = None,
    ) -> PDFGenerationResult:
        """
        Generate a PDF resume by first rendering HTML from template data.

        This is a convenience method that combines template rendering
        and PDF generation in a single call.

        Args:
            template_html: HTML template string (can include Jinja2 syntax)
            resume_data: Dictionary with resume data for template
            candidate_name: Name of the candidate
            template_name: Name of the template
            metadata: Optional PDF metadata
            options: Optional PDF generation options

        Returns:
            PDFGenerationResult with generated PDF or error details

        Example:
            >>> result = await generator.generate_resume_pdf_from_template(
            ...     template_html="<h1>{{name}}</h1>...",
            ...     resume_data={"name": "John Doe", "email": "john@example.com"},
            ...     candidate_name="John Doe"
            ... )
        """
        try:
            # Import here to avoid dependency issues
            from jinja2 import Environment, BaseLoader

            # Render template with resume data
            env = Environment(loader=BaseLoader())
            template = env.from_string(template_html)
            rendered_html = template.render(**resume_data)

            # Generate PDF from rendered HTML
            return await self.generate_resume_pdf(
                html=rendered_html,
                candidate_name=candidate_name,
                template_name=template_name,
                metadata=metadata,
                options=options,
            )

        except Exception as e:
            logger.error(
                f"Failed to render template and generate PDF: {e}",
                exc_info=True
            )
            return PDFGenerationResult(
                success=False,
                error_message=f"Template rendering or PDF generation failed: {str(e)}"
            )

    async def generate_multiple_resumes(
        self,
        requests: List[Dict[str, Any]],
    ) -> List[PDFGenerationResult]:
        """
        Generate multiple resume PDFs in batch.

        Args:
            requests: List of dictionaries, each containing:
                - html: HTML content
                - filename: Optional filename
                - candidate_name: Optional candidate name
                - metadata: Optional PDF metadata
                - options: Optional PDF generation options

        Returns:
            List of PDFGenerationResult objects

        Example:
            >>> requests = [
            ...     {"html": "<html>...</html>", "candidate_name": "John Doe"},
            ...     {"html": "<html>...</html>", "candidate_name": "Jane Smith"},
            ... ]
            >>> results = await generator.generate_multiple_resumes(requests)
        """
        results = []

        for request in requests:
            result = await self.generate_resume_pdf(
                html=request.get("html", ""),
                filename=request.get("filename"),
                candidate_name=request.get("candidate_name"),
                template_name=request.get("template_name"),
                metadata=request.get("metadata"),
                options=request.get("options"),
            )
            results.append(result)

        return results

    def health_check(self) -> Dict[str, Any]:
        """
        Check PDF generator health and availability.

        Returns:
            Dictionary with health status and capabilities
        """
        return {
            "status": "healthy" if self.is_available() else "unavailable",
            "enabled": self.enabled,
            "weasyprint_available": self.weasyprint_available,
            "available_page_formats": list(self.PAGE_SIZES.keys()),
        }


def get_pdf_generator() -> PDFGenerator:
    """
    Get or create global PDF generator service instance.

    Returns:
        Global PDFGenerator instance

    Example:
        >>> from services.pdf_generator import get_pdf_generator
        >>> generator = get_pdf_generator()
        >>> result = await generator.generate_resume_pdf(html, filename)
    """
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = PDFGenerator()
    return _pdf_generator


async def generate_resume_pdf(
    html: str,
    filename: Optional[str] = None,
    candidate_name: Optional[str] = None,
    template_name: Optional[str] = None,
    metadata: Optional[PDFMetadata] = None,
    options: Optional[PDFGenerationOptions] = None,
) -> PDFGenerationResult:
    """
    Convenience function to generate a resume PDF.

    This is a shortcut for using the PDFGenerator class directly.

    Args:
        html: HTML content rendered from template
        filename: Optional filename for the PDF
        candidate_name: Name of the candidate
        template_name: Name of the template used
        metadata: Optional PDF metadata
        options: Optional PDF generation options

    Returns:
        PDFGenerationResult with generated PDF or error details

    Example:
        >>> from services.pdf_generator import generate_resume_pdf
        >>> result = await generate_resume_pdf(
        ...     html="<html>...</html>",
        ...     candidate_name="John Doe"
        ... )
        >>> if result.success:
        ...     with open("resume.pdf", "wb") as f:
        ...         f.write(result.pdf_bytes)
    """
    generator = get_pdf_generator()
    return await generator.generate_resume_pdf(
        html=html,
        filename=filename,
        candidate_name=candidate_name,
        template_name=template_name,
        metadata=metadata,
        options=options,
    )
