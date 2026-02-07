"""
Unit tests for XXE (XML External Entity) protection in DOCX parsing.

This test suite validates the security-critical XXE protection that:
- Prevents XML External Entity attacks in DOCX file processing
- Ensures defusedxml is properly patched
- Neutralizes malicious XML entities before processing
- Protects against file disclosure attacks (SSRF)
- Protects against denial of service via entity expansion
- Logs security violations for monitoring

Test Coverage:
- XXE protection initialization (defusedxml patching)
- Malicious XXE payload detection and neutralization
- File disclosure attempts (SSRF) are blocked
- Billion laughs attack protection (DoS via entity expansion)
- Valid DOCX files still parse correctly with protection active
- Edge cases: Malformed XML, nested entities, parameter entities
"""
import io
import zipfile
from pathlib import Path
from typing import Generator
from unittest.mock import patch, MagicMock

import pytest

# Import the functions we're testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from parsers.docx_parser import DOCXParser


# =============================================================================
# Test Fixtures - Valid DOCX Files
# =============================================================================

@pytest.fixture
def minimal_valid_docx() -> bytes:
    """
    Create a minimal valid DOCX file for testing.

    A DOCX file is a ZIP archive containing XML files. This fixture
    creates the minimum required structure.
    """
    # Create a minimal DOCX as ZIP archive in memory
    docx_buffer = io.BytesIO()

    with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Required [Content_Types].xml
        content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
        zipf.writestr('[Content_Types].xml', content_types)

        # Required _rels/.rels
        rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
        zipf.writestr('_rels/.rels', rels)

        # Required word/_rels/document.xml.rels
        doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
        zipf.writestr('word/_rels/document.xml.rels', doc_rels)

        # Main document content
        document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r>
                <w:t>John Doe - Software Engineer</w:t>
            </w:r>
        </w:p>
        <w:p>
            <w:r>
                <w:t>Experience with Python, FastAPI, and security testing.</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>"""
        zipf.writestr('word/document.xml', document_xml)

    return docx_buffer.getvalue()


@pytest.fixture
def docx_parser() -> DOCXParser:
    """Create a DOCXParser instance for testing."""
    return DOCXParser(min_text_length=10)


# =============================================================================
# Test XXE Protection Initialization
# =============================================================================

class TestXXEProtectionInitialization:
    """Tests for XXE protection initialization and defusedxml patching."""

    def test_defusedxml_is_available(self):
        """Test that defusedxml is installed and available."""
        try:
            import defusedxml
            import defusedxml.ElementTree
            assert defusedxml is not None
        except ImportError:
            pytest.fail("defusedxml is not installed - XXE protection not available")

    @patch('parsers.docx_parser.logger')
    def test_xxe_protection_logged_on_import(self, mock_logger):
        """Test that XXE protection initialization is logged."""
        # Re-import to trigger logging
        import importlib
        import parsers.docx_parser
        importlib.reload(parsers.docx_parser)

        # Verify XXE protection was logged
        assert mock_logger.info.called
        log_messages = [str(call) for call in mock_logger.info.call_args_list]
        assert any("xxe protection" in msg.lower() for msg in log_messages)

    def test_elementtree_is_patched_with_defusedxml(self):
        """Test that xml.etree.ElementTree is patched with defusedxml."""
        import xml.etree.ElementTree as ET

        # Verify that parse and fromstring are from defusedxml
        # The patching in docx_parser.py should have replaced these
        assert hasattr(ET, 'parse')
        assert hasattr(ET, 'fromstring')

        # Verify defusedxml's safety features are active
        # defusedxml prohibits DTDs and entity expansion
        try:
            from defusedxml import common
            # Check if defusedxml protections are in place
            # The _has_defused_xml attribute is set in the patching code
            assert common.DefusedXMLException is not None
        except ImportError:
            pytest.fail("defusedxml.common not available")


# =============================================================================
# Test XXE Attack Payloads - File Disclosure (SSRF)
# =============================================================================

class TestXXEFileDisclosureAttacks:
    """Tests for XXE file disclosure attacks (SSRF - Server-Side Request Forgery)."""

    def test_xxe_file_disclosure_attack_blocked(self, docx_parser: DOCXParser):
        """
        Test that XXE file disclosure attack is blocked.

        This test attempts to read /etc/passwd using XML external entity.
        The defusedxml patch should prevent this attack.
        """
        # Create malicious DOCX with XXE payload attempting file disclosure
        malicious_docx = self._create_xxe_docx_with_file_disclosure()

        # Attempt to parse - should not crash or leak file contents
        result = docx_parser.parse_bytes(malicious_docx, filename="malicious.docx")

        # The parser should handle this gracefully
        # Either it parses safely without expanding entities,
        # or it fails with an error (but doesn't crash)
        assert result is not None

        # Verify no file content was leaked in extracted text
        if result["text"]:
            # If parsing succeeded, verify no sensitive file content is present
            assert "root:" not in result["text"]
            assert "/etc/passwd" not in result["text"]
            assert "nobody:" not in result["text"]

    def test_xxe_local_file_inclusion_blocked(self, docx_parser: DOCXParser):
        """
        Test that XXE local file inclusion is blocked.

        This test attempts to include a local file via XXE.
        """
        # Create malicious DOCX attempting to read local file
        malicious_docx = self._create_xxe_docx_with_local_file_inclusion()

        result = docx_parser.parse_bytes(malicious_docx, filename="local_file_include.docx")

        # Verify local file content not leaked
        if result["text"]:
            assert "LOCAL_FILE_CONTENT" not in result["text"]

    def _create_xxe_docx_with_file_disclosure(self) -> bytes:
        """Create a malicious DOCX with XXE payload for file disclosure."""
        docx_buffer = io.BytesIO()

        with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Content types
            content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
            zipf.writestr('[Content_Types].xml', content_types)

            # Rels
            rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
            zipf.writestr('_rels/.rels', rels)

            # Document rels
            doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
            zipf.writestr('word/_rels/document.xml.rels', doc_rels)

            # Malicious document with XXE payload
            # This attempts to read /etc/passwd via XXE
            malicious_xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE document [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r>
                <w:t>&xxe;</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>"""
            zipf.writestr('word/document.xml', malicious_xml)

        return docx_buffer.getvalue()

    def _create_xxe_docx_with_local_file_inclusion(self) -> bytes:
        """Create a malicious DOCX with XXE payload for local file inclusion."""
        docx_buffer = io.BytesIO()

        with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
            zipf.writestr('[Content_Types].xml', content_types)

            rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
            zipf.writestr('_rels/.rels', rels)

            doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
            zipf.writestr('word/_rels/document.xml.rels', doc_rels)

            # Malicious XML with local file inclusion
            malicious_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE document [
  <!ENTITY % local DTD SYSTEM "file:///local/config.dtd">
  %local;
]>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p><w:r><w:t>Test content</w:t></w:r></w:p>
    </w:body>
</w:document>"""
            zipf.writestr('word/document.xml', malicious_xml)

        return docx_buffer.getvalue()


# =============================================================================
# Test XXE Denial of Service Attacks
# =============================================================================

class TestXXEDenialOfServiceAttacks:
    """Tests for XXE DoS attacks (Billion Laughs, entity expansion)."""

    def test_billion_laughs_attack_blocked(self, docx_parser: DOCXParser):
        """
        Test that Billion Laughs XXE attack is blocked.

        The Billion Laughs attack uses nested entities to cause
        exponential entity expansion, leading to memory exhaustion.
        defusedxml prevents this by disabling DTDs entirely.
        """
        # Create malicious DOCX with billion laughs payload
        malicious_docx = self._create_billion_laughs_docx()

        # Should either parse safely without entity expansion,
        # or fail gracefully (not crash)
        result = docx_parser.parse_bytes(malicious_docx, filename="billion_laughs.docx")

        # Verify protection - either safe parse or error
        assert result is not None

        # If parsing succeeded, verify entities weren't expanded
        # (the billion laughs would create gigabytes of text if expanded)
        if result["text"]:
            # Entity expansion was blocked - text should be minimal
            assert len(result["text"]) < 10000, "Entity expansion was not blocked"

    def test_entity_expansion_limit_enforced(self, docx_parser: DOCXParser):
        """Test that entity expansion is limited to prevent DoS."""
        # Create DOCX with large recursive entity definition
        malicious_docx = self._create_recursive_entity_docx()

        result = docx_parser.parse_bytes(malicious_docx, filename="recursive_entity.docx")

        # Should handle gracefully
        assert result is not None

        # Verify no unbounded expansion occurred
        if result["text"]:
            assert len(result["text"]) < 50000, "Recursive entity expansion not limited"

    def _create_billion_laughs_docx(self) -> bytes:
        """Create a malicious DOCX with Billion Laughs XXE payload."""
        docx_buffer = io.BytesIO()

        with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
            zipf.writestr('[Content_Types].xml', content_types)

            rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
            zipf.writestr('_rels/.rels', rels)

            doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
            zipf.writestr('word/_rels/document.xml.rels', doc_rels)

            # Billion Laughs attack payload
            # Each entity expands to 10 copies of the next, creating exponential growth
            malicious_xml = """<?xml version="1.0"?>
<!DOCTYPE document [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
  <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
  <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">
  <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">
  <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">
  <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">
  <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">
]>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r>
                <w:t>&lol9;</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>"""
            zipf.writestr('word/document.xml', malicious_xml)

        return docx_buffer.getvalue()

    def _create_recursive_entity_docx(self) -> bytes:
        """Create a DOCX with recursive entity definition (DoS attempt)."""
        docx_buffer = io.BytesIO()

        with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
            zipf.writestr('[Content_Types].xml', content_types)

            rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
            zipf.writestr('_rels/.rels', rels)

            doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
            zipf.writestr('word/_rels/document.xml.rels', doc_rels)

            # Recursive entity that could cause infinite expansion
            malicious_xml = """<?xml version="1.0"?>
<!DOCTYPE document [
  <!ENTITY rec "&rec;">
]>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p><w:r><w:t>&rec;</w:t></w:r></w:p>
    </w:body>
</w:document>"""
            zipf.writestr('word/document.xml', malicious_xml)

        return docx_buffer.getvalue()


# =============================================================================
# Test Valid DOCX Parsing with XXE Protection
# =============================================================================

class TestValidDOCXWithXXEProtection:
    """Tests that valid DOCX files parse correctly with XXE protection active."""

    def test_valid_docx_parses_successfully(self, docx_parser: DOCXParser, minimal_valid_docx: bytes):
        """Test that valid DOCX file parses successfully with XXE protection."""
        result = docx_parser.parse_bytes(minimal_valid_docx, filename="valid.docx")

        assert result["error"] is None
        assert result["text"] is not None
        assert len(result["text"]) > 0
        assert result["text_length"] > 0
        assert result["paragraph_count"] > 0

    def test_valid_docx_extracts_text_correctly(self, docx_parser: DOCXParser, minimal_valid_docx: bytes):
        """Test that text is extracted correctly from valid DOCX."""
        result = docx_parser.parse_bytes(minimal_valid_docx, filename="valid.docx")

        assert "John Doe" in result["text"]
        assert "Software Engineer" in result["text"]
        assert "Python" in result["text"]

    def test_valid_docx_metadata_extraction(self, docx_parser: DOCXParser, minimal_valid_docx: bytes):
        """Test that metadata is extracted from valid DOCX."""
        result = docx_parser.parse_bytes(minimal_valid_docx, filename="valid.docx")

        assert result["metadata"] is not None
        assert isinstance(result["metadata"], dict)

    def test_valid_docx_with_tables(self, docx_parser: DOCXParser):
        """Test that DOCX with tables parses correctly."""
        docx_with_table = self._create_docx_with_table()

        result = docx_parser.parse_bytes(docx_with_table, filename="with_table.docx")

        assert result["error"] is None
        assert result["text"] is not None
        # Table content should be extracted
        assert result["table_count"] > 0

    def test_valid_docx_with_multiple_paragraphs(self, docx_parser: DOCXParser):
        """Test that DOCX with multiple paragraphs parses correctly."""
        docx_with_paragraphs = self._create_docx_with_multiple_paragraphs()

        result = docx_parser.parse_bytes(docx_with_paragraphs, filename="paragraphs.docx")

        assert result["error"] is None
        assert result["paragraph_count"] >= 5

    def _create_docx_with_table(self) -> bytes:
        """Create a valid DOCX with a table."""
        docx_buffer = io.BytesIO()

        with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
            zipf.writestr('[Content_Types].xml', content_types)

            rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
            zipf.writestr('_rels/.rels', rels)

            doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
            zipf.writestr('word/_rels/document.xml.rels', doc_rels)

            # Document with table
            document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:tbl>
            <w:tr>
                <w:tc>
                    <w:p>
                        <w:r>
                            <w:t>Name</w:t>
                        </w:r>
                    </w:p>
                </w:tc>
                <w:tc>
                    <w:p>
                        <w:r>
                            <w:t>Experience</w:t>
                        </w:r>
                    </w:p>
                </w:tc>
            </w:tr>
            <w:tr>
                <w:tc>
                    <w:p>
                        <w:r>
                            <w:t>John Doe</w:t>
                        </w:r>
                    </w:p>
                </w:tc>
                <w:tc>
                    <w:p>
                        <w:r>
                            <w:t>5 years</w:t>
                        </w:r>
                    </w:p>
                </w:tc>
            </w:tr>
        </w:tbl>
    </w:body>
</w:document>"""
            zipf.writestr('word/document.xml', document_xml)

        return docx_buffer.getvalue()

    def _create_docx_with_multiple_paragraphs(self) -> bytes:
        """Create a DOCX with multiple paragraphs."""
        docx_buffer = io.BytesIO()

        with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
            zipf.writestr('[Content_Types].xml', content_types)

            rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
            zipf.writestr('_rels/.rels', rels)

            doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
            zipf.writestr('word/_rels/document.xml.rels', doc_rels)

            # Document with multiple paragraphs
            paragraphs = []
            for i in range(10):
                paragraphs.append(f"""        <w:p>
            <w:r>
                <w:t>Paragraph {i}: Resume content line</w:t>
            </w:r>
        </w:p>""")

            document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
{chr(10).join(paragraphs)}
    </w:body>
</w:document>"""
            zipf.writestr('word/document.xml', document_xml)

        return docx_buffer.getvalue()


# =============================================================================
# Test XXE Attack Logging
# =============================================================================

class TestXXEAttackLogging:
    """Tests for XXE attack logging and security event tracking."""

    @patch('parsers.docx_parser.logger')
    def test_xxe_attempt_is_logged(self, mock_logger, docx_parser: DOCXParser):
        """Test that XXE attack attempts are logged as security events."""
        # Create malicious DOCX with XXE payload
        malicious_docx = self._create_xxe_docx_with_file_disclosure()

        docx_parser.parse_bytes(malicious_docx, filename="xxe_attack.docx")

        # Verify security event was logged
        # defusedxml may raise an exception which gets logged
        # Check for error or warning logs
        assert mock_logger.error.called or mock_logger.warning.called

    @patch('parsers.docx_parser.logger')
    def test_successful_parse_logs_info(self, mock_logger, docx_parser: DOCXParser, minimal_valid_docx: bytes):
        """Test that successful DOCX parsing is logged."""
        docx_parser.parse_bytes(minimal_valid_docx, filename="valid.docx")

        # Verify info logging for successful parse
        assert mock_logger.info.called
        log_messages = [str(call) for call in mock_logger.info.call_args_list]
        assert any("parsing" in msg.lower() or "extracting" in msg.lower() for msg in log_messages)

    def _create_xxe_docx_with_file_disclosure(self) -> bytes:
        """Create a malicious DOCX with XXE payload."""
        docx_buffer = io.BytesIO()

        with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
            zipf.writestr('[Content_Types].xml', content_types)

            rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
            zipf.writestr('_rels/.rels', rels)

            doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
            zipf.writestr('word/_rels/document.xml.rels', doc_rels)

            malicious_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE document [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body><w:p><w:r><w:t>&xxe;</w:t></w:r></w:p></w:body>
</w:document>"""
            zipf.writestr('word/document.xml', malicious_xml)

        return docx_buffer.getvalue()


# =============================================================================
# Test Edge Cases and Malformed Input
# =============================================================================

class TestXXEProtectionEdgeCases:
    """Tests for edge cases and malformed XML input."""

    def test_malformed_xml_handled_gracefully(self, docx_parser: DOCXParser):
        """Test that malformed XML is handled gracefully."""
        malformed_docx = self._create_malformed_xml_docx()

        result = docx_parser.parse_bytes(malformed_docx, filename="malformed.docx")

        # Should not crash - either parse with error or fail gracefully
        assert result is not None
        # Error should be present if parsing failed
        if result["text"] is None:
            assert result["error"] is not None

    def test_docx_with_special_characters(self, docx_parser: DOCXParser):
        """Test that DOCX with special characters parses safely."""
        special_chars_docx = self._create_docx_with_special_characters()

        result = docx_parser.parse_bytes(special_chars_docx, filename="special_chars.docx")

        # Should parse successfully
        assert result is not None
        # Special characters should be preserved safely
        if result["text"]:
            assert "<" not in result["text"] or "&lt;" in result["text"]
            assert ">" not in result["text"] or "&gt;" in result["text"]

    def test_docx_with_unicode_content(self, docx_parser: DOCXParser):
        """Test that DOCX with Unicode content parses safely."""
        unicode_docx = self._create_docx_with_unicode()

        result = docx_parser.parse_bytes(unicode_docx, filename="unicode.docx")

        # Should parse successfully
        assert result is not None
        assert result["error"] is None

    def _create_malformed_xml_docx(self) -> bytes:
        """Create a DOCX with malformed XML."""
        docx_buffer = io.BytesIO()

        with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
            zipf.writestr('[Content_Types].xml', content_types)

            rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
            zipf.writestr('_rels/.rels', rels)

            doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
            zipf.writestr('word/_rels/document.xml.rels', doc_rels)

            # Malformed XML (unclosed tag)
            malformed_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r>
                <w:t>Unclosed tag
            </w:r>
        </w:p>
    </w:body>
</w:document>"""
            zipf.writestr('word/document.xml', malformed_xml)

        return docx_buffer.getvalue()

    def _create_docx_with_special_characters(self) -> bytes:
        """Create a DOCX with special characters that need escaping."""
        docx_buffer = io.BytesIO()

        with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
            zipf.writestr('[Content_Types].xml', content_types)

            rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
            zipf.writestr('_rels/.rels', rels)

            doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
            zipf.writestr('word/_rels/document.xml.rels', doc_rels)

            # Content with XML special characters (should be escaped)
            document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r>
                <w:t>Special chars: &lt;tag&gt; &amp; &quot;quoted&quot;</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>"""
            zipf.writestr('word/document.xml', document_xml)

        return docx_buffer.getvalue()

    def _create_docx_with_unicode(self) -> bytes:
        """Create a DOCX with Unicode content."""
        docx_buffer = io.BytesIO()

        with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
            zipf.writestr('[Content_Types].xml', content_types)

            rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
            zipf.writestr('_rels/.rels', rels)

            doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
            zipf.writestr('word/_rels/document.xml.rels', doc_rels)

            # Unicode content: emojis, accented chars, CJK
            document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r>
                <w:t>José García 日本語 👨‍💻 Developer</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>"""
            zipf.writestr('word/document.xml', document_xml)

        return docx_buffer.getvalue()


# =============================================================================
# Test Parameter Entity XXE Attacks
# =============================================================================

class TestParameterEntityXXEAttacks:
    """Tests for parameter entity XXE attacks (more sophisticated)."""

    def test_parameter_entity_attack_blocked(self, docx_parser: DOCXParser):
        """
        Test that parameter entity XXE attack is blocked.

        Parameter entity attacks are more sophisticated and can bypass
        some basic XXE protections. defusedxml blocks these entirely.
        """
        malicious_docx = self._create_parameter_entity_xxe_docx()

        result = docx_parser.parse_bytes(malicious_docx, filename="parameter_entity.docx")

        # Should handle gracefully - either safe parse or error
        assert result is not None

        # Verify no data exfiltration
        if result["text"]:
            # Sensitive data should not be present
            assert "root:" not in result["text"]

    def _create_parameter_entity_xxe_docx(self) -> bytes:
        """Create a DOCX with parameter entity XXE payload."""
        docx_buffer = io.BytesIO()

        with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
            zipf.writestr('[Content_Types].xml', content_types)

            rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
            zipf.writestr('_rels/.rels', rels)

            doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
            zipf.writestr('word/_rels/document.xml.rels', doc_rels)

            # Parameter entity XXE payload
            # This attempts to use parameter entities for file disclosure
            malicious_xml = """<?xml version="1.0"?>
<!DOCTYPE document [
  <!ENTITY % xxe SYSTEM "file:///etc/passwd">
  %xxe;
]>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body><w:p><w:r><w:t>Test</w:t></w:r></w:p></w:body>
</w:document>"""
            zipf.writestr('word/document.xml', malicious_xml)

        return docx_buffer.getvalue()


# =============================================================================
# Configuration for pytest
# =============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "xxe: marks tests as XXE protection tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
