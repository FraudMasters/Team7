"""
PDF text extraction from resume documents using pypdf (PyPDF2).

This module provides functionality to extract text content from PDF files,
with validation and error handling for resume processing. The parser handles
text-based PDFs and provides detailed error messages for unsupported formats
like image-based (scanned) PDFs.

Includes complex layout detection for multi-column layouts and tables,
providing structured information about the document's visual organization.
"""
import logging
import os
import re
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class LayoutRegion:
    """
    Represents a detected region in a PDF page.

    Attributes:
        region_type: Type of region (text, table, multi_column, header, footer)
        bbox: Bounding box as (x0, y0, x1, y1) in page coordinates
        confidence: Detection confidence (0.0 to 1.0)
        content: Extracted text content from the region
        page_num: Page number (1-indexed)
        column_count: Number of columns detected (for multi_column type)
    """
    region_type: str
    bbox: Tuple[float, float, float, float]
    confidence: float
    content: str = ""
    page_num: int = 1
    column_count: int = 1


@dataclass
class LayoutAnalysis:
    """
    Results of layout analysis for a PDF document.

    Attributes:
        has_multi_column: Whether any page has multi-column layout
        has_tables: Whether tables were detected
        regions: List of detected layout regions
        page_count: Total number of pages analyzed
        complexity_score: Overall layout complexity (0.0 to 1.0)
        warnings: List of warnings about layout issues
    """
    has_multi_column: bool = False
    has_tables: bool = False
    regions: List[LayoutRegion] = field(default_factory=list)
    page_count: int = 0
    complexity_score: float = 0.0
    warnings: List[str] = field(default_factory=list)


class PDFParser:
    """
    Parser for extracting text from PDF documents using pypdf.

    This class provides methods to extract raw text content from PDF files,
    with validation for file integrity, encryption status, and text presence.
    It is designed to handle resume documents and provides informative errors
    for unsupported formats.

    Attributes:
        min_text_length: Minimum expected text length for valid resumes
        max_file_size_mb: Maximum allowed file size in megabytes

    Examples:
        >>> parser = PDFParser()
        >>> result = parser.parse("/path/to/resume.pdf")
        >>> print(result["text"])
        'John Doe\\nSoftware Engineer...'

        >>> # Parse from bytes
        >>> with open("resume.pdf", "rb") as f:
        ...     pdf_bytes = f.read()
        >>> result = parser.parse_bytes(pdf_bytes)
        >>> print(result["text_length"])
        2543
    """

    def __init__(
        self,
        *,
        min_text_length: int = 50,
        max_file_size_mb: int = 10,
        detect_layouts: bool = True,
        column_threshold: float = 0.3,
    ):
        """
        Initialize the PDF parser.

        Args:
            min_text_length: Minimum expected text length for valid resumes (default: 50 chars)
            max_file_size_mb: Maximum allowed file size in megabytes (default: 10MB)
            detect_layouts: Whether to detect complex layouts (default: True)
            column_threshold: Threshold for column detection (default: 0.3)
        """
        self.min_text_length = min_text_length
        self.max_file_size_mb = max_file_size_mb
        self.detect_layouts = detect_layouts
        self.column_threshold = column_threshold

        # Check if pypdf is available
        try:
            from pypdf import PdfReader  # type: ignore
            self.PdfReader = PdfReader
            logger.info("PDFParser initialized with pypdf")
        except ImportError as e:
            raise ImportError(
                "pypdf is not installed. Install it with: pip install pypdf"
            ) from e

    def parse(
        self,
        file_path: Union[str, Path],
    ) -> Dict[str, Optional[Union[str, int, Dict[str, Union[str, int]]]]]:
        """
        Extract text from a PDF file.

        This method reads a PDF file from disk and extracts all text content.
        It validates the file, checks for encryption, and ensures text content
        is present.

        Args:
            file_path: Path to the PDF file (string or Path object)

        Returns:
            Dictionary containing:
                - text: Extracted text content (None if failed)
                - text_length: Number of characters extracted (0 if failed)
                - page_count: Number of pages in PDF (0 if failed)
                - is_encrypted: Whether PDF is encrypted (bool)
                - error: Error message if extraction failed (None if successful)
                - metadata: PDF metadata dict (title, author, etc.)
                - layout_analysis: LayoutAnalysis object with detected regions (None if detection disabled)

        Raises:
            FileNotFoundError: If file_path does not exist
            ValueError: If file_path is not a PDF file

        Examples:
            >>> parser = PDFParser()
            >>> result = parser.parse("resume.pdf")
            >>> if result["error"]:
            ...     print(f"Error: {result['error']}")
            ... else:
            ...     print(f"Extracted {result['text_length']} chars from {result['page_count']} pages")
        """
        # Validate file path
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return {
                "text": None,
                "text_length": 0,
                "page_count": 0,
                "is_encrypted": False,
                "error": f"File not found: {file_path}",
                "metadata": None,
                "layout_analysis": None,
            }

        # Validate file extension
        if file_path.suffix.lower() != ".pdf":
            logger.error(f"Not a PDF file: {file_path}")
            return {
                "text": None,
                "text_length": 0,
                "page_count": 0,
                "is_encrypted": False,
                "error": f"Not a PDF file: {file_path.suffix}",
                "metadata": None,
                "layout_analysis": None,
            }

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            logger.error(f"File too large: {file_size_mb:.2f}MB (max: {self.max_file_size_mb}MB)")
            return {
                "text": None,
                "text_length": 0,
                "page_count": 0,
                "is_encrypted": False,
                "error": f"File too large: {file_size_mb:.2f}MB (max: {self.max_file_size_mb}MB)",
                "metadata": None,
                "layout_analysis": None,
            }

        try:
            logger.info(f"Parsing PDF: {file_path} ({file_size_mb:.2f}MB)")

            # Read file bytes
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()

            # Parse using bytes method
            return self.parse_bytes(pdf_bytes, filename=file_path.name)

        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {e}")
            return {
                "text": None,
                "text_length": 0,
                "page_count": 0,
                "is_encrypted": False,
                "error": f"Parsing failed: {str(e)}",
                "metadata": None,
                "layout_analysis": None,
            }

    def parse_bytes(
        self,
        pdf_bytes: bytes,
        *,
        filename: str = "document.pdf",
    ) -> Dict[str, Optional[Union[str, int, Dict[str, Union[str, int]]]]]:
        """
        Extract text from PDF bytes.

        This method extracts text from PDF content provided as bytes, useful for
        handling file uploads or in-memory PDF content.

        Args:
            pdf_bytes: PDF file content as bytes
            filename: Original filename (for logging and error messages)

        Returns:
            Dictionary containing:
                - text: Extracted text content (None if failed)
                - text_length: Number of characters extracted (0 if failed)
                - page_count: Number of pages in PDF (0 if failed)
                - is_encrypted: Whether PDF is encrypted (bool)
                - error: Error message if extraction failed (None if successful)
                - metadata: PDF metadata dict (title, author, etc.)
                - layout_analysis: LayoutAnalysis object with detected regions (None if detection disabled)

        Examples:
            >>> parser = PDFParser()
            >>> with open("resume.pdf", "rb") as f:
            ...     pdf_bytes = f.read()
            >>> result = parser.parse_bytes(pdf_bytes)
            >>> print(result["text"][:100])  # First 100 chars
        """
        # Validate input
        if not pdf_bytes:
            logger.error("Empty PDF bytes provided")
            return {
                "text": None,
                "text_length": 0,
                "page_count": 0,
                "is_encrypted": False,
                "error": "Empty PDF bytes provided",
                "metadata": None,
                "layout_analysis": None,
            }

        # Check file size
        file_size_mb = len(pdf_bytes) / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            logger.error(f"PDF too large: {file_size_mb:.2f}MB")
            return {
                "text": None,
                "text_length": 0,
                "page_count": 0,
                "is_encrypted": False,
                "error": f"PDF too large: {file_size_mb:.2f}MB (max: {self.max_file_size_mb}MB)",
                "metadata": None,
                "layout_analysis": None,
            }

        try:
            # Create PDF reader from bytes
            pdf_file = BytesIO(pdf_bytes)
            reader = self.PdfReader(pdf_file)

            # Check if encrypted
            is_encrypted = reader.is_encrypted
            if is_encrypted:
                logger.error(f"PDF is encrypted: {filename}")
                return {
                    "text": None,
                    "text_length": 0,
                    "page_count": len(reader.pages),
                    "is_encrypted": True,
                    "error": "PDF is encrypted and password-protected. Text-based encrypted PDFs are not supported.",
                    "metadata": None,
                    "layout_analysis": None,
                }

            # Extract metadata
            metadata = self._extract_metadata(reader)

            # Extract text from all pages
            page_count = len(reader.pages)
            logger.info(f"Extracting text from {page_count} pages in {filename}")

            text_parts = []
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                        logger.debug(f"Extracted {len(page_text)} chars from page {page_num}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {e}")

            # Combine text from all pages
            full_text = "\n\n".join(text_parts)
            text_length = len(full_text)

            # Validate extracted text
            if text_length < self.min_text_length:
                logger.warning(f"Extracted text too short: {text_length} chars (min: {self.min_text_length})")

                # Check if this might be an image-based PDF
                if text_length == 0:
                    return {
                        "text": None,
                        "text_length": 0,
                        "page_count": page_count,
                        "is_encrypted": False,
                        "error": "No extractable text found. This appears to be an image-based (scanned) PDF. OCR is not supported.",
                        "metadata": metadata,
                        "layout_analysis": None,
                    }
                else:
                    # Perform layout analysis even for short text
                    layout_analysis = None
                    if self.detect_layouts:
                        layout_analysis = self._analyze_layout(reader, text_parts)

                    return {
                        "text": full_text,
                        "text_length": text_length,
                        "page_count": page_count,
                        "is_encrypted": False,
                        "error": f"Extracted text too short: {text_length} chars (min: {self.min_text_length}). Document may be corrupted or malformed.",
                        "metadata": metadata,
                        "layout_analysis": layout_analysis,
                    }

            logger.info(f"Successfully extracted {text_length} chars from {page_count} pages")

            # Perform layout analysis if enabled
            layout_analysis = None
            if self.detect_layouts:
                layout_analysis = self._analyze_layout(reader, text_parts)
                if layout_analysis and layout_analysis.warnings:
                    for warning in layout_analysis.warnings:
                        logger.warning(f"Layout issue: {warning}")

            return {
                "text": full_text,
                "text_length": text_length,
                "page_count": page_count,
                "is_encrypted": False,
                "error": None,
                "metadata": metadata,
                "layout_analysis": layout_analysis,
            }

        except Exception as e:
            logger.error(f"Failed to parse PDF bytes from {filename}: {e}")
            return {
                "text": None,
                "text_length": 0,
                "page_count": 0,
                "is_encrypted": False,
                "error": f"Parsing failed: {str(e)}",
                "metadata": None,
                "layout_analysis": None,
            }

    def _extract_metadata(self, reader) -> Dict[str, Optional[Union[str, int]]]:
        """
        Extract metadata from PDF reader.

        Args:
            reader: pypdf PdfReader instance

        Returns:
            Dictionary with PDF metadata fields
        """
        try:
            metadata = reader.metadata
            if metadata:
                return {
                    "title": metadata.get("/Title", None),
                    "author": metadata.get("/Author", None),
                    "subject": metadata.get("/Subject", None),
                    "creator": metadata.get("/Creator", None),
                    "producer": metadata.get("/Producer", None),
                    "creation_date": metadata.get("/CreationDate", None),
                }
        except Exception as e:
            logger.warning(f"Failed to extract PDF metadata: {e}")

        return {
            "title": None,
            "author": None,
            "subject": None,
            "creator": None,
            "producer": None,
            "creation_date": None,
        }

    def _analyze_layout(self, reader, text_parts: List[str]) -> LayoutAnalysis:
        """
        Analyze the layout of the PDF document.

        Detects multi-column layouts, tables, and other complex structures
        that may affect text extraction quality.

        Args:
            reader: pypdf PdfReader instance
            text_parts: List of extracted text from each page

        Returns:
            LayoutAnalysis object with detected regions and complexity score
        """
        analysis = LayoutAnalysis(page_count=len(reader.pages))
        regions = []

        for page_num, (page, page_text) in enumerate(zip(reader.pages, text_parts), start=1):
            try:
                # Get page dimensions
                mediabox = page.mediabox
                page_width = float(mediabox.width)
                page_height = float(mediabox.height)

                # Detect multi-column layout
                column_regions = self._detect_columns(page_text, page_width, page_height, page_num)
                if column_regions:
                    analysis.has_multi_column = True
                    regions.extend(column_regions)

                # Detect tables
                table_regions = self._detect_tables(page_text, page_width, page_height, page_num)
                if table_regions:
                    analysis.has_tables = True
                    regions.extend(table_regions)

            except Exception as e:
                logger.warning(f"Failed to analyze layout for page {page_num}: {e}")
                analysis.warnings.append(f"Could not analyze page {page_num}: {str(e)}")

        analysis.regions = regions
        analysis.complexity_score = self._calculate_complexity(analysis)

        # Add warnings for complex layouts
        if analysis.has_multi_column:
            analysis.warnings.append("Multi-column layout detected. Text order may not reflect reading order.")

        if analysis.has_tables:
            analysis.warnings.append("Tables detected. Consider manual verification of extracted data.")

        return analysis

    def _detect_columns(
        self,
        page_text: str,
        page_width: float,
        page_height: float,
        page_num: int,
    ) -> List[LayoutRegion]:
        """
        Detect multi-column layout in a page.

        Uses heuristics based on line length distribution and text patterns
        to identify potential multi-column sections.

        Args:
            page_text: Extracted text from the page
            page_width: Width of the page in points
            page_height: Height of the page in points
            page_num: Page number (1-indexed)

        Returns:
            List of LayoutRegion objects for detected columns
        """
        regions = []

        if not page_text:
            return regions

        lines = page_text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        if len(non_empty_lines) < 5:
            return regions

        # Calculate average line length
        line_lengths = [len(line) for line in non_empty_lines]
        avg_length = sum(line_lengths) / len(line_lengths)

        # Count short lines (potential column breaks)
        short_line_threshold = avg_length * self.column_threshold
        short_lines = sum(1 for length in line_lengths if length < short_line_threshold)
        short_line_ratio = short_lines / len(non_empty_lines)

        # Detect columns based on short line patterns
        # Multiple short lines interspersed with longer content suggest columns
        if short_line_ratio > 0.2:
            # Look for patterns suggesting column breaks
            column_breaks = []
            consecutive_short = 0

            for i, line in enumerate(non_empty_lines):
                if len(line) < short_line_threshold:
                    consecutive_short += 1
                else:
                    if consecutive_short >= 2:
                        column_breaks.append(i - consecutive_short)
                    consecutive_short = 0

            if len(column_breaks) >= 1:
                # Detected multi-column layout
                region = LayoutRegion(
                    region_type="multi_column",
                    bbox=(0, 0, page_width, page_height),
                    confidence=min(0.9, short_line_ratio * 2),
                    content=page_text,
                    page_num=page_num,
                    column_count=len(column_breaks) + 1,
                )
                regions.append(region)
                logger.debug(f"Detected {region.column_count}-column layout on page {page_num}")

        return regions

    def _detect_tables(
        self,
        page_text: str,
        page_width: float,
        page_height: float,
        page_num: int,
    ) -> List[LayoutRegion]:
        """
        Detect tables in a page.

        Uses heuristics based on delimiter patterns and alignment
        to identify potential table regions.

        Args:
            page_text: Extracted text from the page
            page_width: Width of the page in points
            page_height: Height of the page in points
            page_num: Page number (1-indexed)

        Returns:
            List of LayoutRegion objects for detected tables
        """
        regions = []

        if not page_text:
            return regions

        lines = page_text.split('\n')

        # Look for table-like patterns
        # Pattern 1: Lines with consistent pipe or tab delimiters
        delimiter_pattern = re.compile(r'(\|.+\|)|(?:\S+\t\S+)+')
        delimiter_matches = [i for i, line in enumerate(lines) if delimiter_pattern.search(line)]

        # Pattern 2: Lines with similar word counts (columnar data)
        word_counts = [len(line.split()) for line in lines if line.strip()]
        if word_counts:
            avg_word_count = sum(word_counts) / len(word_counts)
            consistent_lines = sum(1 for wc in word_counts if abs(wc - avg_word_count) <= 2)
            consistency_ratio = consistent_lines / len(word_counts)

            # High consistency suggests tabular data
            if consistency_ratio > 0.7 and len(word_counts) >= 3:
                # Group consecutive lines as potential table
                table_lines = []
                current_table = []

                for i, line in enumerate(lines):
                    if line.strip() and abs(len(line.split()) - avg_word_count) <= 2:
                        current_table.append(i)
                    else:
                        if len(current_table) >= 3:
                            table_lines.append(current_table)
                        current_table = []

                if len(current_table) >= 3:
                    table_lines.append(current_table)

                for table_indices in table_lines:
                    if table_indices:
                        start_idx = table_indices[0]
                        end_idx = table_indices[-1]
                        table_text = '\n'.join(lines[start_idx:end_idx + 1])

                        # Estimate bounding box (rough approximation)
                        y_start = page_height - (start_idx / len(lines)) * page_height
                        y_end = page_height - (end_idx / len(lines)) * page_height

                        region = LayoutRegion(
                            region_type="table",
                            bbox=(0, y_end, page_width, y_start),
                            confidence=min(0.9, consistency_ratio),
                            content=table_text,
                            page_num=page_num,
                        )
                        regions.append(region)
                        logger.debug(f"Detected table on page {page_num} (lines {start_idx + 1}-{end_idx + 1})")

        # Check for delimiter-based tables
        if len(delimiter_matches) >= 3:
            # Group consecutive matches
            table_groups = []
            current_group = [delimiter_matches[0]]

            for i in range(1, len(delimiter_matches)):
                if delimiter_matches[i] - delimiter_matches[i-1] <= 2:
                    current_group.append(delimiter_matches[i])
                else:
                    if len(current_group) >= 2:
                        table_groups.append(current_group)
                    current_group = [delimiter_matches[i]]

            if len(current_group) >= 2:
                table_groups.append(current_group)

            for group in table_groups:
                start_idx = group[0]
                end_idx = group[-1]
                table_text = '\n'.join(lines[start_idx:end_idx + 1])

                # Check if this overlaps with already detected tables
                overlaps = False
                for existing in regions:
                    if existing.page_num == page_num:
                        existing_start = lines.index(existing.content.split('\n')[0]) if existing.content in page_text else -1
                        if existing_start >= 0 and abs(existing_start - start_idx) < 3:
                            overlaps = True
                            break

                if not overlaps:
                    y_start = page_height - (start_idx / len(lines)) * page_height
                    y_end = page_height - (end_idx / len(lines)) * page_height

                    region = LayoutRegion(
                        region_type="table",
                        bbox=(0, y_end, page_width, y_start),
                        confidence=0.85,
                        content=table_text,
                        page_num=page_num,
                    )
                    regions.append(region)
                    logger.debug(f"Detected delimiter table on page {page_num}")

        return regions

    def _calculate_complexity(self, analysis: LayoutAnalysis) -> float:
        """
        Calculate overall layout complexity score.

        Args:
            analysis: LayoutAnalysis object with detected regions

        Returns:
            Complexity score from 0.0 (simple) to 1.0 (very complex)
        """
        score = 0.0

        # Multi-column adds complexity
        if analysis.has_multi_column:
            score += 0.3

        # Tables add complexity
        if analysis.has_tables:
            table_count = sum(1 for r in analysis.regions if r.region_type == "table")
            score += min(0.3, table_count * 0.1)

        # Number of regions indicates complexity
        if len(analysis.regions) > 3:
            score += 0.2

        # Warnings indicate potential issues
        if analysis.warnings:
            score += min(0.2, len(analysis.warnings) * 0.05)

        return min(1.0, score)

    def validate_pdf(
        self,
        file_path: Union[str, Path],
    ) -> Dict[str, Union[bool, str, Optional[str]]]:
        """
        Validate PDF file before parsing.

        This method performs quick validation checks without extracting text,
        useful for pre-flight validation.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing:
                - is_valid: Whether PDF passes validation
                - error: Error message if invalid (None if valid)
                - file_size_mb: File size in MB
                - reason: Human-readable validation result

        Examples:
            >>> parser = PDFParser()
            >>> result = parser.validate_pdf("resume.pdf")
            >>> if result["is_valid"]:
            ...     print("PDF is valid for parsing")
            ... else:
            ...     print(f"Invalid: {result['error']}")
        """
        file_path = Path(file_path)

        # Check existence
        if not file_path.exists():
            return {
                "is_valid": False,
                "error": "File not found",
                "file_size_mb": 0,
                "reason": f"File does not exist: {file_path}",
            }

        # Check extension
        if file_path.suffix.lower() != ".pdf":
            return {
                "is_valid": False,
                "error": "Invalid file type",
                "file_size_mb": file_path.stat().st_size / (1024 * 1024),
                "reason": f"Not a PDF file: {file_path.suffix}",
            }

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            return {
                "is_valid": False,
                "error": "File too large",
                "file_size_mb": file_size_mb,
                "reason": f"File size {file_size_mb:.2f}MB exceeds maximum {self.max_file_size_mb}MB",
            }

        # Check if file is empty
        if file_size_mb == 0:
            return {
                "is_valid": False,
                "error": "Empty file",
                "file_size_mb": 0,
                "reason": "PDF file is empty (0 bytes)",
            }

        # Try to open PDF with pypdf
        try:
            with open(file_path, "rb") as f:
                reader = self.PdfReader(f)

                # Check if encrypted
                if reader.is_encrypted:
                    return {
                        "is_valid": False,
                        "error": "Encrypted PDF",
                        "file_size_mb": file_size_mb,
                        "reason": "PDF is password-protected and cannot be parsed",
                    }

                # Check if has pages
                if len(reader.pages) == 0:
                    return {
                        "is_valid": False,
                        "error": "No pages",
                        "file_size_mb": file_size_mb,
                        "reason": "PDF contains no pages",
                    }

        except Exception as e:
            return {
                "is_valid": False,
                "error": "Invalid PDF",
                "file_size_mb": file_size_mb,
                "reason": f"Failed to open PDF: {str(e)}",
            }

        return {
            "is_valid": True,
            "error": None,
            "file_size_mb": file_size_mb,
            "reason": f"Valid PDF with {file_size_mb:.2f}MB",
        }
