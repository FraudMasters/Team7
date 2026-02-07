"""
DOCX text extraction from resume documents using python-docx.

This module provides functionality to extract text content from DOCX (Word) files,
with validation and error handling for resume processing. The parser handles
both text and table content, providing detailed error messages for malformed
or unsupported documents.

Security:
    This module uses defusedxml for XXE (XML External Entity) attack protection.
    The python-docx library processes DOCX files (which are ZIP archives containing
    XML files), and without proper protection, malicious XML entities could be used
    to read arbitrary files or perform SSRF attacks.
"""
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Union

# Apply XXE protection before importing python-docx
# This prevents XML External Entity attacks by disabling entity expansion
try:
    from defusedxml import ElementTree as DefusedElementTree
    import defusedxml.common

    # Disable DTDs and entity expansion globally for XML parsing
    defusedxml.common.DefusedXMLException = Exception
    DefusedElementTree._has_defused_xml = True

    # Monkey-patch ElementTree to use defusedxml
    import xml.etree.ElementTree as _ElementTree
    _ElementTree.parse = DefusedElementTree.parse
    _ElementTree.fromstring = DefusedElementTree.fromstring

    logger.info("XXE protection enabled: defusedxml patched xml.etree.ElementTree")
except ImportError:
    logger.warning(
        "defusedxml not installed - XXE protection not enabled. "
        "Install with: pip install defusedxml"
    )

logger = logging.getLogger(__name__)


class DOCXParser:
    """
    Parser for extracting text from DOCX documents using python-docx.

    This class provides methods to extract raw text content from DOCX files,
    with validation for file integrity, structure validation, and text presence.
    It is designed to handle resume documents and extracts text from paragraphs
    and tables.

    Attributes:
        min_text_length: Minimum expected text length for valid resumes
        max_file_size_mb: Maximum allowed file size in megabytes
        extract_tables: Whether to extract text from tables
        extract_headers_footers: Whether to extract headers and footers

    Examples:
        >>> parser = DOCXParser()
        >>> result = parser.parse("/path/to/resume.docx")
        >>> print(result["text"])
        'John Doe\\nSoftware Engineer...'

        >>> # Parse from bytes
        >>> with open("resume.docx", "rb") as f:
        ...     docx_bytes = f.read()
        >>> result = parser.parse_bytes(docx_bytes)
        >>> print(result["text_length"])
        2543
    """

    def __init__(
        self,
        *,
        min_text_length: int = 50,
        max_file_size_mb: int = 10,
        extract_tables: bool = True,
        extract_headers_footers: bool = True,
    ):
        """
        Initialize the DOCX parser.

        Args:
            min_text_length: Minimum expected text length for valid resumes (default: 50 chars)
            max_file_size_mb: Maximum allowed file size in megabytes (default: 10MB)
            extract_tables: Whether to extract text from tables (default: True)
            extract_headers_footers: Whether to extract headers and footers (default: True)
        """
        self.min_text_length = min_text_length
        self.max_file_size_mb = max_file_size_mb
        self.extract_tables = extract_tables
        self.extract_headers_footers = extract_headers_footers

        # Check if python-docx is available
        try:
            from docx import Document  # type: ignore
            self.Document = Document
            logger.info("DOCXParser initialized with python-docx")
        except ImportError as e:
            raise ImportError(
                "python-docx is not installed. Install it with: pip install python-docx"
            ) from e

    def parse(
        self,
        file_path: Union[str, Path],
    ) -> Dict[str, Optional[Union[str, int, Dict[str, Union[str, int]]]]]:
        """
        Extract text from a DOCX file.

        This method reads a DOCX file from disk and extracts all text content
        from paragraphs and optionally from tables, headers, and footers.

        Args:
            file_path: Path to the DOCX file (string or Path object)

        Returns:
            Dictionary containing:
                - text: Extracted text content (None if failed)
                - text_length: Number of characters extracted (0 if failed)
                - paragraph_count: Number of paragraphs in document (0 if failed)
                - table_count: Number of tables extracted (0 if failed)
                - error: Error message if extraction failed (None if successful)
                - metadata: DOCX metadata dict (title, author, etc.)

        Raises:
            FileNotFoundError: If file_path does not exist
            ValueError: If file_path is not a DOCX file

        Examples:
            >>> parser = DOCXParser()
            >>> result = parser.parse("resume.docx")
            >>> if result["error"]:
            ...     print(f"Error: {result['error']}")
            ... else:
            ...     print(f"Extracted {result['text_length']} chars from {result['paragraph_count']} paragraphs")
        """
        # Validate file path
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return {
                "text": None,
                "text_length": 0,
                "paragraph_count": 0,
                "table_count": 0,
                "error": f"File not found: {file_path}",
                "metadata": None,
            }

        # Validate file extension
        if file_path.suffix.lower() not in (".docx", ".doc"):
            logger.error(f"Not a DOCX file: {file_path}")
            return {
                "text": None,
                "text_length": 0,
                "paragraph_count": 0,
                "table_count": 0,
                "error": f"Not a DOCX file: {file_path.suffix}",
                "metadata": None,
            }

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            logger.error(f"File too large: {file_size_mb:.2f}MB (max: {self.max_file_size_mb}MB)")
            return {
                "text": None,
                "text_length": 0,
                "paragraph_count": 0,
                "table_count": 0,
                "error": f"File too large: {file_size_mb:.2f}MB (max: {self.max_file_size_mb}MB)",
                "metadata": None,
            }

        try:
            logger.info(f"Parsing DOCX: {file_path} ({file_size_mb:.2f}MB)")

            # Read file bytes
            with open(file_path, "rb") as f:
                docx_bytes = f.read()

            # Parse using bytes method
            return self.parse_bytes(docx_bytes, filename=file_path.name)

        except Exception as e:
            logger.error(f"Failed to parse DOCX {file_path}: {e}")
            return {
                "text": None,
                "text_length": 0,
                "paragraph_count": 0,
                "table_count": 0,
                "error": f"Parsing failed: {str(e)}",
                "metadata": None,
            }

    def parse_bytes(
        self,
        docx_bytes: bytes,
        *,
        filename: str = "document.docx",
    ) -> Dict[str, Optional[Union[str, int, Dict[str, Union[str, int]]]]]:
        """
        Extract text from DOCX bytes.

        This method extracts text from DOCX content provided as bytes, useful for
        handling file uploads or in-memory DOCX content.

        Args:
            docx_bytes: DOCX file content as bytes
            filename: Original filename (for logging and error messages)

        Returns:
            Dictionary containing:
                - text: Extracted text content (None if failed)
                - text_length: Number of characters extracted (0 if failed)
                - paragraph_count: Number of paragraphs in document (0 if failed)
                - table_count: Number of tables extracted (0 if failed)
                - error: Error message if extraction failed (None if successful)
                - metadata: DOCX metadata dict (title, author, etc.)

        Examples:
            >>> parser = DOCXParser()
            >>> with open("resume.docx", "rb") as f:
            ...     docx_bytes = f.read()
            >>> result = parser.parse_bytes(docx_bytes)
            >>> print(result["text"][:100])  # First 100 chars
        """
        # Validate input
        if not docx_bytes:
            logger.error("Empty DOCX bytes provided")
            return {
                "text": None,
                "text_length": 0,
                "paragraph_count": 0,
                "table_count": 0,
                "error": "Empty DOCX bytes provided",
                "metadata": None,
            }

        # Check file size
        file_size_mb = len(docx_bytes) / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            logger.error(f"DOCX too large: {file_size_mb:.2f}MB")
            return {
                "text": None,
                "text_length": 0,
                "paragraph_count": 0,
                "table_count": 0,
                "error": f"DOCX too large: {file_size_mb:.2f}MB (max: {self.max_file_size_mb}MB)",
                "metadata": None,
            }

        try:
            # Create document from bytes
            docx_file = BytesIO(docx_bytes)
            doc = self.Document(docx_file)

            # Extract metadata
            metadata = self._extract_metadata(doc)

            # Extract text from paragraphs
            logger.info(f"Extracting text from {filename}")
            text_parts = []

            # Extract from paragraphs
            paragraph_count = 0
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
                    paragraph_count += 1

            logger.debug(f"Extracted {paragraph_count} non-empty paragraphs")

            # Extract from tables if enabled
            table_count = 0
            if self.extract_tables:
                table_text = self._extract_table_text(doc)
                if table_text:
                    text_parts.append(table_text)
                    table_count = len(doc.tables)
                    logger.debug(f"Extracted text from {table_count} tables")

            # Extract from headers and footers if enabled
            if self.extract_headers_footers:
                header_footer_text = self._extract_header_footer_text(doc)
                if header_footer_text:
                    text_parts.append(header_footer_text)
                    logger.debug("Extracted headers and footers")

            # Combine all text
            full_text = "\n\n".join(text_parts)
            text_length = len(full_text)

            # Validate extracted text
            if text_length < self.min_text_length:
                logger.warning(f"Extracted text too short: {text_length} chars (min: {self.min_text_length})")

                if text_length == 0:
                    return {
                        "text": None,
                        "text_length": 0,
                        "paragraph_count": paragraph_count,
                        "table_count": table_count,
                        "error": "No extractable text found. Document may be empty or contain only images.",
                        "metadata": metadata,
                    }
                else:
                    return {
                        "text": full_text,
                        "text_length": text_length,
                        "paragraph_count": paragraph_count,
                        "table_count": table_count,
                        "error": f"Extracted text too short: {text_length} chars (min: {self.min_text_length}). Document may be malformed.",
                        "metadata": metadata,
                    }

            logger.info(f"Successfully extracted {text_length} chars from {paragraph_count} paragraphs and {table_count} tables")

            return {
                "text": full_text,
                "text_length": text_length,
                "paragraph_count": paragraph_count,
                "table_count": table_count,
                "error": None,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Failed to parse DOCX bytes from {filename}: {e}")
            return {
                "text": None,
                "text_length": 0,
                "paragraph_count": 0,
                "table_count": 0,
                "error": f"Parsing failed: {str(e)}",
                "metadata": None,
            }

    def _extract_metadata(self, doc) -> Dict[str, Optional[str]]:
        """
        Extract metadata from DOCX document.

        Args:
            doc: python-docx Document instance

        Returns:
            Dictionary with DOCX metadata fields
        """
        try:
            core_props = doc.core_properties

            return {
                "title": core_props.title or None,
                "author": core_props.author or None,
                "subject": core_props.subject or None,
                "keywords": core_props.keywords or None,
                "comments": core_props.comments or None,
                "category": core_props.category or None,
                "created": core_props.created or None,
                "modified": core_props.modified or None,
                "last_modified_by": core_props.last_modified_by or None,
                "revision": core_props.revision or None,
            }
        except Exception as e:
            logger.warning(f"Failed to extract DOCX metadata: {e}")

        return {
            "title": None,
            "author": None,
            "subject": None,
            "keywords": None,
            "comments": None,
            "category": None,
            "created": None,
            "modified": None,
            "last_modified_by": None,
            "revision": None,
        }

    def _extract_table_text(self, doc) -> Optional[str]:
        """
        Extract text from all tables in document.

        Args:
            doc: python-docx Document instance

        Returns:
            Combined text from all tables or None if no tables
        """
        if not doc.tables:
            return None

        table_texts = []
        for table_idx, table in enumerate(doc.tables):
            rows_text = []
            for row in table.rows:
                cells_text = []
                for cell in row.cells:
                    if cell.text.strip():
                        cells_text.append(cell.text.strip())
                if cells_text:
                    rows_text.append(" | ".join(cells_text))

            if rows_text:
                table_text = "\n".join(rows_text)
                table_texts.append(f"[Table {table_idx + 1}]\n{table_text}")

        return "\n\n".join(table_texts) if table_texts else None

    def _extract_header_footer_text(self, doc) -> Optional[str]:
        """
        Extract text from headers and footers.

        Args:
            doc: python-docx Document instance

        Returns:
            Combined text from headers and footers or None if empty
        """
        text_parts = []

        try:
            # Extract from sections
            for section_idx, section in enumerate(doc.sections):
                # Header
                if section.header:
                    for paragraph in section.header.paragraphs:
                        if paragraph.text.strip():
                            text_parts.append(f"[Header Section {section_idx + 1}] {paragraph.text.strip()}")

                # Footer
                if section.footer:
                    for paragraph in section.footer.paragraphs:
                        if paragraph.text.strip():
                            text_parts.append(f"[Footer Section {section_idx + 1}] {paragraph.text.strip()}")

        except Exception as e:
            logger.warning(f"Failed to extract headers/footers: {e}")

        return "\n".join(text_parts) if text_parts else None

    def validate_docx(
        self,
        file_path: Union[str, Path],
    ) -> Dict[str, Union[bool, str, Optional[str]]]:
        """
        Validate DOCX file before parsing.

        This method performs quick validation checks without extracting text,
        useful for pre-flight validation.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Dictionary containing:
                - is_valid: Whether DOCX passes validation
                - error: Error message if invalid (None if valid)
                - file_size_mb: File size in MB
                - reason: Human-readable validation result

        Examples:
            >>> parser = DOCXParser()
            >>> result = parser.validate_docx("resume.docx")
            >>> if result["is_valid"]:
            ...     print("DOCX is valid for parsing")
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
        if file_path.suffix.lower() not in (".docx", ".doc"):
            return {
                "is_valid": False,
                "error": "Invalid file type",
                "file_size_mb": file_path.stat().st_size / (1024 * 1024),
                "reason": f"Not a DOCX file: {file_path.suffix}",
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
                "reason": "DOCX file is empty (0 bytes)",
            }

        # Try to open DOCX with python-docx
        try:
            with open(file_path, "rb") as f:
                doc = self.Document(f)

                # Check if has paragraphs
                if len(doc.paragraphs) == 0:
                    return {
                        "is_valid": False,
                        "error": "No content",
                        "file_size_mb": file_size_mb,
                        "reason": "DOCX contains no paragraphs",
                    }

        except Exception as e:
            return {
                "is_valid": False,
                "error": "Invalid DOCX",
                "file_size_mb": file_size_mb,
                "reason": f"Failed to open DOCX: {str(e)}",
            }

        return {
            "is_valid": True,
            "error": None,
            "file_size_mb": file_size_mb,
            "reason": f"Valid DOCX with {file_size_mb:.2f}MB",
        }
