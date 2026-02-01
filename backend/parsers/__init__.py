"""
Parsers module for document text extraction.

This module provides document parsers for extracting text from various file formats,
including PDF and DOCX files. These parsers are designed to handle resume documents
and extract raw text content for further processing by NLP components.
"""

from .pdf_parser import (
    PDFParser,
)
from .docx_parser import (
    DOCXParser,
)

__all__ = [
    "PDFParser",
    "DOCXParser",
]
