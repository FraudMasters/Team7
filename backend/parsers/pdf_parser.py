"""
PDF text extraction from resume documents using pypdf (PyPDF2).

This module provides functionality to extract text content from PDF files,
with validation and error handling for resume processing. The parser handles
text-based PDFs and provides detailed error messages for unsupported formats
like image-based (scanned) PDFs.
"""
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional, Union

logger = logging.getLogger(__name__)


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
    ):
        """
        Initialize the PDF parser.

        Args:
            min_text_length: Minimum expected text length for valid resumes (default: 50 chars)
            max_file_size_mb: Maximum allowed file size in megabytes (default: 10MB)
        """
        self.min_text_length = min_text_length
        self.max_file_size_mb = max_file_size_mb

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
                    }
                else:
                    return {
                        "text": full_text,
                        "text_length": text_length,
                        "page_count": page_count,
                        "is_encrypted": False,
                        "error": f"Extracted text too short: {text_length} chars (min: {self.min_text_length}). Document may be corrupted or malformed.",
                        "metadata": metadata,
                    }

            logger.info(f"Successfully extracted {text_length} chars from {page_count} pages")

            return {
                "text": full_text,
                "text_length": text_length,
                "page_count": page_count,
                "is_encrypted": False,
                "error": None,
                "metadata": metadata,
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
