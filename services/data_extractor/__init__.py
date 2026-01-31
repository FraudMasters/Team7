"""
Data Extractor Service.

This service provides text extraction capabilities for resume files
in PDF and DOCX formats with robust error handling.
"""

from .extract import (
    extract_text_from_pdf,
    extract_text_from_docx,
    validate_pdf_file,
    validate_docx_file,
)

__version__ = "0.1.0"

__all__ = [
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "validate_pdf_file",
    "validate_docx_file",
]
