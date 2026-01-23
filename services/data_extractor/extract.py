"""
Resume text extraction from PDF and DOCX files.

This module provides functions to extract text content from various resume file formats,
with robust error handling for malformed files.
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Union

import pdfplumber
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf(
    file_path: Union[str, Path], use_fallback: bool = True
) -> Dict[str, Optional[str]]:
    """
    Extract text from a PDF file using PyPDF2 and pdfplumber as fallback.

    Args:
        file_path: Path to the PDF file
        use_fallback: If True, try pdfplumber if PyPDF2 fails or returns minimal text

    Returns:
        Dictionary containing:
            - text: Extracted text content (None if extraction fails)
            - method: Which library succeeded ('pypdf2', 'pdfplumber', or None)
            - pages: Number of pages detected
            - error: Error message if extraction failed

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is not a valid PDF

    Examples:
        >>> result = extract_text_from_pdf("resume.pdf")
        >>> print(result["text"])
        'John Doe\\nSoftware Engineer...'
        >>> print(result["method"])
        'pypdf2'
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.suffix.lower() == ".pdf":
        raise ValueError(f"File is not a PDF: {file_path}")

    # Try PyPDF2 first (faster)
    try:
        result = _extract_with_pypdf2(file_path)
        # Check if we got meaningful content
        text_length = len(result["text"].strip()) if result["text"] else 0

        if text_length > 50 or not use_fallback:
            logger.info(f"Extracted {text_length} chars from {file_path.name} using PyPDF2")
            return result
        else:
            logger.warning(
                f"PyPDF2 extracted minimal text ({text_length} chars), trying pdfplumber"
            )
    except Exception as e:
        logger.warning(f"PyPDF2 extraction failed: {e}")
        if not use_fallback:
            return {
                "text": None,
                "method": None,
                "pages": 0,
                "error": f"PyPDF2 failed: {str(e)}",
            }

    # Fallback to pdfplumber (better for complex layouts)
    if use_fallback:
        try:
            result = _extract_with_pdfplumber(file_path)
            text_length = len(result["text"].strip()) if result["text"] else 0
            logger.info(
                f"Extracted {text_length} chars from {file_path.name} using pdfplumber"
            )
            return result
        except Exception as e:
            logger.error(f"pdfplumber extraction also failed: {e}")
            return {
                "text": None,
                "method": None,
                "pages": 0,
                "error": f"All extraction methods failed: {str(e)}",
            }

    return {
        "text": None,
        "method": None,
        "pages": 0,
        "error": "No extraction method succeeded",
    }


def _extract_with_pypdf2(file_path: Path) -> Dict[str, Optional[str]]:
    """
    Extract text using PyPDF2 library.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dictionary with extracted text and metadata
    """
    try:
        reader = PdfReader(str(file_path))
        num_pages = len(reader.pages)

        text_parts = []
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            except Exception as e:
                logger.warning(f"Failed to extract page {page_num}: {e}")
                continue

        text = "\n\n".join(text_parts) if text_parts else ""

        return {
            "text": text if text.strip() else None,
            "method": "pypdf2",
            "pages": num_pages,
            "error": None,
        }

    except Exception as e:
        raise RuntimeError(f"PyPDF2 extraction error: {e}") from e


def _extract_with_pdfplumber(file_path: Path) -> Dict[str, Optional[str]]:
    """
    Extract text using pdfplumber library.

    Pdfplumber is more robust for complex PDF layouts and handles
    some edge cases better than PyPDF2.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dictionary with extracted text and metadata
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            num_pages = len(pdf.pages)
            text_parts = []

            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"pdfplumber failed to extract page {page_num}: {e}")
                    continue

            text = "\n\n".join(text_parts) if text_parts else ""

            return {
                "text": text if text.strip() else None,
                "method": "pdfplumber",
                "pages": num_pages,
                "error": None,
            }

    except Exception as e:
        raise RuntimeError(f"pdfplumber extraction error: {e}") from e


def validate_pdf_file(file_path: Union[str, Path]) -> Dict[str, Union[bool, str]]:
    """
    Validate a PDF file before extraction.

    Checks:
    - File exists
    - Has .pdf extension
    - Is not empty
    - Can be opened by PDF libraries

    Args:
        file_path: Path to the PDF file

    Returns:
        Dictionary with validation results:
            - valid: Boolean indicating if file is valid
            - reason: String explaining why validation failed (if applicable)

    Examples:
        >>> validation = validate_pdf_file("resume.pdf")
        >>> if validation["valid"]:
        ...     result = extract_text_from_pdf("resume.pdf")
    """
    file_path = Path(file_path)

    # Check existence
    if not file_path.exists():
        return {"valid": False, "reason": "File not found"}

    # Check extension
    if file_path.suffix.lower() != ".pdf":
        return {"valid": False, "reason": "Not a PDF file"}

    # Check file size
    if file_path.stat().st_size == 0:
        return {"valid": False, "reason": "File is empty"}

    # Try to open with PyPDF2
    try:
        reader = PdfReader(str(file_path))
        if len(reader.pages) == 0:
            return {"valid": False, "reason": "PDF has no pages"}
    except Exception as e:
        return {"valid": False, "reason": f"Cannot open PDF: {str(e)}"}

    return {"valid": True, "reason": None}
