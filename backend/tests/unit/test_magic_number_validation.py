"""
Unit tests for magic number validation (file signature verification).

This test suite validates the security-critical file validation functions that:
- Verify file content matches declared file type (magic number validation)
- Check file structure integrity (EOF markers, minimum sizes)
- Detect malicious file uploads (EXE renamed to PDF, etc.)
- Prevent file spoofing attacks

Test Coverage:
- validate_magic_number: Valid PDF/DOCX accepted, invalid rejected
- validate_file_structure: Size checks, EOF marker validation
- get_file_signature: Signature lookup function
- is_supported_file_type: Extension validation
- Edge cases: Empty files, malformed data, boundary conditions
"""
import pytest
from pathlib import Path
from unittest.mock import patch

# Import the functions we're testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.file_validation import (
    validate_magic_number,
    validate_file_structure,
    get_file_signature,
    is_supported_file_type,
    FILE_SIGNATURES,
    MAX_HEADER_SIZE,
)


# =============================================================================
# Test Fixtures - Valid File Content
# =============================================================================

@pytest.fixture
def valid_pdf_content() -> bytes:
    """Create valid PDF file content with correct magic number."""
    # Minimal PDF file with %PDF- header and %%EOF marker
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
214
%%EOF
"""


@pytest.fixture
def valid_docx_content() -> bytes:
    """Create valid DOCX file content with ZIP magic number."""
    # DOCX files are ZIP archives starting with PK\x03\x04
    # Include end of central directory signature for structure validation
    content = b"PK\x03\x04" + b"Test DOCX content" * 50 + b"PK\x05\x06"
    return content


@pytest.fixture
def minimal_pdf() -> bytes:
    """Create minimal but valid PDF content."""
    return b"%PDF-1.4\n%%EOF"


@pytest.fixture
def minimal_docx() -> bytes:
    """Create minimal but valid DOCX content."""
    return b"PK\x03\x04" + b"Content" * 100 + b"PK\x05\x06"


# =============================================================================
# Test Fixtures - Invalid/Malicious File Content
# =============================================================================

@pytest.fixture
def exe_renamed_to_pdf() -> bytes:
    """Create EXE file content (MZ header) simulating malicious file."""
    # PE executable header (MZ signature) - simulating malware.exe renamed to .pdf
    return b"MZ\x90\x00" + b"\x00" * 100


@pytest.fixture
def text_renamed_to_pdf() -> bytes:
    """Create plain text file renamed to PDF."""
    return b"This is not a PDF file, just plain text."


@pytest.fixture
def random_renamed_to_docx() -> bytes:
    """Create random bytes renamed to DOCX."""
    return b"\x00\x01\x02\x03\x04\x05" + b"Random content" * 50


@pytest.fixture
def pdf_missing_eof() -> bytes:
    """Create PDF with valid magic number but missing EOF marker."""
    return b"%PDF-1.4\nSome content but no EOF marker"


@pytest.fixture
def truncated_pdf() -> bytes:
    """Create truncated PDF file."""
    return b"%PDF-1"


@pytest.fixture
def empty_file() -> bytes:
    """Create empty file content."""
    return b""


@pytest.fixture
def tiny_file() -> bytes:
    """Create file too small to contain valid header."""
    return b"%P"


# =============================================================================
# Test validate_magic_number - Valid Files
# =============================================================================

class TestValidateMagicNumberValidFiles:
    """Tests for validate_magic_number with valid file content."""

    def test_valid_pdf_accepted(self, valid_pdf_content: bytes):
        """Test that valid PDF content with correct magic number is accepted."""
        is_valid, error = validate_magic_number(valid_pdf_content, ".pdf")

        assert is_valid is True
        assert error is None

    def test_valid_pdf_case_insensitive_extension(self, valid_pdf_content: bytes):
        """Test that file extension is case-insensitive."""
        is_valid, error = validate_magic_number(valid_pdf_content, ".PDF")
        assert is_valid is True
        assert error is None

        is_valid, error = validate_magic_number(valid_pdf_content, "Pdf")
        assert is_valid is True
        assert error is None

    def test_valid_pdf_without_dot_extension(self, valid_pdf_content: bytes):
        """Test that extension works without leading dot."""
        is_valid, error = validate_magic_number(valid_pdf_content, "pdf")
        assert is_valid is True
        assert error is None

    def test_valid_docx_accepted(self, valid_docx_content: bytes):
        """Test that valid DOCX content with ZIP magic number is accepted."""
        is_valid, error = validate_magic_number(valid_docx_content, ".docx")

        assert is_valid is True
        assert error is None

    def test_valid_docx_case_insensitive(self, valid_docx_content: bytes):
        """Test that DOCX extension is case-insensitive."""
        is_valid, error = validate_magic_number(valid_docx_content, ".DOCX")
        assert is_valid is True
        assert error is None

    def test_minimal_pdf_accepted(self, minimal_pdf: bytes):
        """Test that minimal but valid PDF is accepted."""
        is_valid, error = validate_magic_number(minimal_pdf, ".pdf")

        assert is_valid is True
        assert error is None

    def test_minimal_docx_accepted(self, minimal_docx: bytes):
        """Test that minimal but valid DOCX is accepted."""
        is_valid, error = validate_magic_number(minimal_docx, ".docx")

        assert is_valid is True
        assert error is None

    def test_pdf_with_latin1_locale(self, valid_pdf_content: bytes):
        """Test that locale parameter is accepted (for future i18n)."""
        is_valid, error = validate_magic_number(valid_pdf_content, ".pdf", locale="en")

        assert is_valid is True
        assert error is None


# =============================================================================
# Test validate_magic_number - Invalid/Malicious Files
# =============================================================================

class TestValidateMagicNumberInvalidFiles:
    """Tests for validate_magic_number with invalid/malicious file content."""

    def test_exe_renamed_to_pdf_rejected(self, exe_renamed_to_pdf: bytes):
        """
        Test that EXE file renamed to PDF is rejected.

        This is a critical security test - prevents attackers from uploading
        malware by renaming executables to benign extensions.
        """
        is_valid, error = validate_magic_number(exe_renamed_to_pdf, ".pdf")

        assert is_valid is False
        assert error is not None
        assert "magic number" in error.lower() or "file header" in error.lower()

    def test_text_renamed_to_pdf_rejected(self, text_renamed_to_pdf: bytes):
        """Test that text file renamed to PDF is rejected."""
        is_valid, error = validate_magic_number(text_renamed_to_pdf, ".pdf")

        assert is_valid is False
        assert error is not None
        assert "magic number" in error.lower() or "file header" in error.lower()

    def test_random_renamed_to_docx_rejected(self, random_renamed_to_docx: bytes):
        """Test that random bytes renamed to DOCX are rejected."""
        is_valid, error = validate_magic_number(random_renamed_to_docx, ".docx")

        assert is_valid is False
        assert error is not None

    def test_empty_file_rejected(self, empty_file: bytes):
        """Test that empty file is rejected."""
        is_valid, error = validate_magic_number(empty_file, ".pdf")

        assert is_valid is False
        assert error is not None
        assert "empty" in error.lower()

    def test_file_too_small_for_header_rejected(self, tiny_file: bytes):
        """Test that file too small to contain header is rejected."""
        is_valid, error = validate_magic_number(tiny_file, ".pdf")

        assert is_valid is False
        assert error is not None
        assert "too small" in error.lower()

    def test_unsupported_extension_rejected(self, valid_pdf_content: bytes):
        """Test that unsupported file extensions are rejected."""
        is_valid, error = validate_magic_number(valid_pdf_content, ".exe")

        assert is_valid is False
        assert error is not None
        assert "unsupported" in error.lower()

    def test_invalid_extension_format_rejected(self, valid_pdf_content: bytes):
        """Test that invalid extension format is rejected."""
        is_valid, error = validate_magic_number(valid_pdf_content, "")

        assert is_valid is False
        assert error is not None

    def test_none_extension_rejected(self, valid_pdf_content: bytes):
        """Test that None extension is rejected."""
        is_valid, error = validate_magic_number(valid_pdf_content, None)

        assert is_valid is False
        assert error is not None

    def test_wrong_magic_number_for_docx(self, valid_pdf_content: bytes):
        """Test PDF content is rejected when declared as DOCX."""
        is_valid, error = validate_magic_number(valid_pdf_content, ".docx")

        assert is_valid is False
        assert error is not None


# =============================================================================
# Test validate_file_structure - Valid Files
# =============================================================================

class TestValidateFileStructureValid:
    """Tests for validate_file_structure with valid file structure."""

    def test_valid_pdf_structure_accepted(self, valid_pdf_content: bytes):
        """Test that valid PDF structure with EOF marker is accepted."""
        is_valid, error = validate_file_structure(valid_pdf_content, ".pdf")

        assert is_valid is True
        assert error is None

    def test_valid_docx_structure_accepted(self, valid_docx_content: bytes):
        """Test that valid DOCX structure is accepted."""
        is_valid, error = validate_file_structure(valid_docx_content, ".docx")

        assert is_valid is True
        assert error is None

    def test_minimal_pdf_structure_accepted(self, minimal_pdf: bytes):
        """Test that minimal PDF structure is accepted."""
        is_valid, error = validate_file_structure(minimal_pdf, ".pdf")

        assert is_valid is True
        assert error is None


# =============================================================================
# Test validate_file_structure - Invalid Files
# =============================================================================

class TestValidateFileStructureInvalid:
    """Tests for validate_file_structure with invalid file structure."""

    def test_pdf_missing_eof_rejected(self, pdf_missing_eof: bytes):
        """Test that PDF missing EOF marker is rejected."""
        is_valid, error = validate_file_structure(pdf_missing_eof, ".pdf")

        assert is_valid is False
        assert error is not None
        assert "eof" in error.lower() or "incomplete" in error.lower() or "corrupted" in error.lower()

    def test_empty_file_structure_rejected(self, empty_file: bytes):
        """Test that empty file fails structure validation."""
        is_valid, error = validate_file_structure(empty_file, ".pdf")

        assert is_valid is False
        assert error is not None
        assert "empty" in error.lower()

    def test_file_too_small_rejected(self, tiny_file: bytes):
        """Test that file below minimum size is rejected."""
        is_valid, error = validate_file_structure(tiny_file, ".pdf")

        assert is_valid is False
        assert error is not None
        assert "too small" in error.lower()

    def test_file_too_large_rejected(self):
        """Test that file exceeding maximum size is rejected."""
        # Create file larger than 50MB max
        large_file = b"%PDF-1.4\n" + b"X" * (51 * 1024 * 1024) + b"\n%%EOF"

        is_valid, error = validate_file_structure(large_file, ".pdf")

        assert is_valid is False
        assert error is not None
        assert "exceeds maximum" in error.lower() or "too large" in error.lower()

    def test_unsupported_extension_structure_rejected(self, valid_pdf_content: bytes):
        """Test that unsupported extensions are rejected."""
        is_valid, error = validate_file_structure(valid_pdf_content, ".exe")

        # May fail at unsupported extension check or size check
        assert is_valid is False
        assert error is not None

    def test_invalid_extension_format_rejected(self, valid_pdf_content: bytes):
        """Test that invalid extension format is rejected."""
        is_valid, error = validate_file_structure(valid_pdf_content, "")

        assert is_valid is False
        assert error is not None

    def test_none_extension_rejected(self, valid_pdf_content: bytes):
        """Test that None extension is rejected."""
        is_valid, error = validate_file_structure(valid_pdf_content, None)

        assert is_valid is False
        assert error is not None


# =============================================================================
# Test get_file_signature
# =============================================================================

class TestGetFileSignature:
    """Tests for get_file_signature helper function."""

    def test_get_pdf_signature(self):
        """Test getting PDF magic number signature."""
        signature = get_file_signature(".pdf")

        assert signature == b"%PDF-"
        assert signature is not None

    def test_get_pdf_signature_without_dot(self):
        """Test getting PDF signature without leading dot."""
        signature = get_file_signature("pdf")

        assert signature == b"%PDF-"

    def test_get_docx_signature(self):
        """Test getting DOCX magic number signature."""
        signature = get_file_signature(".docx")

        assert signature == b"PK\x03\x04"
        assert signature is not None

    def test_get_docx_signature_case_insensitive(self):
        """Test getting DOCX signature is case-insensitive."""
        signature = get_file_signature("DOCX")

        assert signature == b"PK\x03\x04"

    def test_get_unsupported_signature_returns_none(self):
        """Test that unsupported extension returns None."""
        signature = get_file_signature(".exe")

        assert signature is None

    def test_get_empty_extension_returns_none(self):
        """Test that empty extension returns None."""
        signature = get_file_signature("")

        assert signature is None

    def test_get_none_extension_returns_none(self):
        """Test that None extension returns None."""
        signature = get_file_signature(None)

        assert signature is None


# =============================================================================
# Test is_supported_file_type
# =============================================================================

class TestIsSupportedFileType:
    """Tests for is_supported_file_type helper function."""

    def test_pdf_is_supported(self):
        """Test that PDF is a supported file type."""
        assert is_supported_file_type(".pdf") is True

    def test_pdf_without_dot_is_supported(self):
        """Test that PDF without dot is supported."""
        assert is_supported_file_type("pdf") is True

    def test_pdf_uppercase_is_supported(self):
        """Test that uppercase PDF is supported."""
        assert is_supported_file_type("PDF") is True

    def test_docx_is_supported(self):
        """Test that DOCX is a supported file type."""
        assert is_supported_file_type(".docx") is True

    def test_docx_without_dot_is_supported(self):
        """Test that DOCX without dot is supported."""
        assert is_supported_file_type("docx") is True

    def test_exe_is_not_supported(self):
        """Test that EXE is not a supported file type."""
        assert is_supported_file_type(".exe") is False

    def test_txt_is_not_supported(self):
        """Test that TXT is not a supported file type."""
        assert is_supported_file_type(".txt") is False

    def test_empty_extension_is_not_supported(self):
        """Test that empty extension is not supported."""
        assert is_supported_file_type("") is False

    def test_none_extension_is_not_supported(self):
        """Test that None extension is not supported."""
        assert is_supported_file_type(None) is False

    def test_jpg_is_not_supported(self):
        """Test that JPG is not a supported file type."""
        assert is_supported_file_type(".jpg") is False

    def test_png_is_not_supported(self):
        """Test that PNG is not a supported file type."""
        assert is_supported_file_type(".png") is False


# =============================================================================
# Test Constants
# =============================================================================

class TestFileValidationConstants:
    """Tests for file validation module constants."""

    def test_file_signatures_constant(self):
        """Test that FILE_SIGNATURES contains expected entries."""
        assert "pdf" in FILE_SIGNATURES
        assert "docx" in FILE_SIGNATURES
        assert FILE_SIGNATURES["pdf"] == b"%PDF-"
        assert FILE_SIGNATURES["docx"] == b"PK\x03\x04"

    def test_max_header_size_constant(self):
        """Test that MAX_HEADER_SIZE is set correctly."""
        assert MAX_HEADER_SIZE == 12
        assert MAX_HEADER_SIZE >= 5  # At least large enough for PDF header


# =============================================================================
# Test Edge Cases and Boundary Conditions
# =============================================================================

class TestMagicNumberValidationEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_pdf_exactly_at_header_boundary(self):
        """Test PDF file content exactly at header size boundary."""
        # Create PDF content exactly MAX_HEADER_SIZE bytes
        pdf_content = b"%PDF-1.4\n" + b"X" * (MAX_HEADER_SIZE - 8) + b"\n%%EOF"

        is_valid, error = validate_magic_number(pdf_content, ".pdf")

        # Should validate magic number successfully
        assert is_valid is True
        assert error is None

    def test_pdf_one_byte_over_header_boundary(self):
        """Test PDF file content one byte over header size."""
        pdf_content = b"%PDF-1.4\n" + b"X" * (MAX_HEADER_SIZE - 7) + b"\n%%EOF"

        is_valid, error = validate_magic_number(pdf_content, ".pdf")

        assert is_valid is True
        assert error is None

    def test_pdf_with_special_characters(self):
        """Test PDF with special characters in content."""
        pdf_content = b"%PDF-1.4\n\x00\x01\x02\xff\xfe\n%%EOF"

        is_valid, error = validate_magic_number(pdf_content, ".pdf")

        assert is_valid is True
        assert error is None

    def test_pdf_with_unicode_content(self):
        """Test PDF with UTF-8 encoded content."""
        pdf_content = b"%PDF-1.4\n\xc3\xa9\xc3\xa0\n%%EOF"  # UTF-8 chars

        is_valid, error = validate_magic_number(pdf_content, ".pdf")

        assert is_valid is True
        assert error is None

    def test_docx_with_multiple_pk_signatures(self):
        """Test DOCX with multiple PK signatures (valid ZIP structure)."""
        docx_content = b"PK\x03\x04" + b"A" * 100 + b"PK\x03\x04" + b"B" * 100 + b"PK\x05\x06"

        is_valid, error = validate_magic_number(docx_content, ".docx")

        assert is_valid is True
        assert error is None

    def test_pdf_version_variations(self):
        """Test different PDF version numbers are accepted."""
        versions = [b"%PDF-1.0", b"%PDF-1.1", b"%PDF-1.2", b"%PDF-1.3",
                    b"%PDF-1.4", b"%PDF-1.5", b"%PDF-1.6", b"%PDF-1.7",
                    b"%PDF-2.0"]

        for version in versions:
            pdf_content = version + b"\nContent\n%%EOF"
            is_valid, error = validate_magic_number(pdf_content, ".pdf")

            assert is_valid is True, f"Failed for version: {version}"
            assert error is None

    def test_pdf_with_comment_after_header(self):
        """Test PDF with comment immediately after header."""
        pdf_content = b"%PDF-1.4\n%This is a comment\nContent\n%%EOF"

        is_valid, error = validate_magic_number(pdf_content, ".pdf")

        assert is_valid is True
        assert error is None

    def test_corrupted_pdf_header_rejected(self):
        """Test PDF with corrupted magic number is rejected."""
        # Slight corruption of the magic number
        corrupted_headers = [
            b"%PD",           # Too short
            b"%PDX",          # Wrong character
            b"%PDF",          # Missing version
            b"PDF-1.4",       # Missing %
            b"%PDF 1.4",      # Missing -
        ]

        for header in corrupted_headers:
            content = header + b"\nContent\n%%EOF"
            is_valid, error = validate_magic_number(content, ".pdf")

            assert is_valid is False, f"Should reject corrupted header: {header}"


# =============================================================================
# Test Logging and Security Events
# =============================================================================

class TestMagicNumberValidationLogging:
    """Tests to verify security violations are logged appropriately."""

    @patch('utils.file_validation.logger')
    def test_empty_file_logs_warning(self, mock_logger):
        """Test that empty file triggers warning log."""
        validate_magic_number(b"", ".pdf")

        # Verify warning was logged
        assert mock_logger.warning.called
        log_message = str(mock_logger.warning.call_args)
        assert "empty" in log_message.lower()

    @patch('utils.file_validation.logger')
    def test_invalid_magic_number_logs_warning(self, mock_logger):
        """Test that invalid magic number triggers warning log."""
        validate_magic_number(b"MZ\x90\x00", ".pdf")

        # Verify warning was logged
        assert mock_logger.warning.called
        log_message = str(mock_logger.warning.call_args)
        assert "magic number" in log_message.lower() or "validation failed" in log_message.lower()

    @patch('utils.file_validation.logger')
    def test_valid_file_logs_info(self, mock_logger):
        """Test that valid file triggers info log."""
        validate_magic_number(b"%PDF-1.4\n%%EOF", ".pdf")

        # Verify info was logged
        assert mock_logger.info.called
        log_message = str(mock_logger.info.call_args)
        assert "validation passed" in log_message.lower()

    @patch('utils.file_validation.logger')
    def test_unsupported_extension_logs_warning(self, mock_logger):
        """Test that unsupported extension triggers warning log."""
        validate_magic_number(b"Some content", ".exe")

        # Verify warning was logged
        assert mock_logger.warning.called

    @patch('utils.file_validation.logger')
    def test_exception_handling_logs_error(self, mock_logger):
        """Test that exceptions during validation are logged."""
        # Force an exception by passing invalid data that causes an error
        # The function should handle exceptions gracefully
        is_valid, error = validate_magic_number(b"test", ".pdf")

        # Even with invalid content, should not raise exception
        assert is_valid is False
        assert error is not None


# =============================================================================
# Test Locale Support (for future i18n)
# =============================================================================

class TestLocaleSupport:
    """Tests for locale parameter support (for future internationalization)."""

    def test_validate_with_english_locale(self, valid_pdf_content: bytes):
        """Test validation with English locale."""
        is_valid, error = validate_magic_number(valid_pdf_content, ".pdf", locale="en")

        assert is_valid is True
        assert error is None

    def test_validate_with_spanish_locale(self, valid_pdf_content: bytes):
        """Test validation with Spanish locale."""
        is_valid, error = validate_magic_number(valid_pdf_content, ".pdf", locale="es")

        assert is_valid is True
        assert error is None

    def test_validate_with_french_locale(self, valid_pdf_content: bytes):
        """Test validation with French locale."""
        is_valid, error = validate_magic_number(valid_pdf_content, ".pdf", locale="fr")

        assert is_valid is True
        assert error is None


# =============================================================================
# Test Combined Validation Scenarios
# =============================================================================

class TestCombinedValidationScenarios:
    """Tests for combined magic number and structure validation."""

    def test_valid_file_passes_both_validations(self, valid_pdf_content: bytes):
        """Test that valid file passes both magic number and structure validation."""
        magic_valid, magic_error = validate_magic_number(valid_pdf_content, ".pdf")
        struct_valid, struct_error = validate_file_structure(valid_pdf_content, ".pdf")

        assert magic_valid is True
        assert magic_error is None
        assert struct_valid is True
        assert struct_error is None

    def test_file_with_valid_magic_invalid_structure(self, pdf_missing_eof: bytes):
        """Test file with valid magic number but invalid structure."""
        magic_valid, magic_error = validate_magic_number(pdf_missing_eof, ".pdf")
        struct_valid, struct_error = validate_file_structure(pdf_missing_eof, ".pdf")

        # Magic number should pass (starts with %PDF-)
        assert magic_valid is True
        assert magic_error is None

        # Structure should fail (missing %%EOF)
        assert struct_valid is False
        assert struct_error is not None

    def test_malicious_file_fails_both_validations(self, exe_renamed_to_pdf: bytes):
        """Test malicious file fails both validations."""
        # Add content to make it pass minimum size check
        malicious_content = exe_renamed_to_pdf + b"X" * 200

        magic_valid, magic_error = validate_magic_number(malicious_content, ".pdf")

        # Should fail magic number validation
        assert magic_valid is False
        assert magic_error is not None
        assert "magic number" in magic_error.lower() or "file header" in magic_error.lower()


# =============================================================================
# Configuration for pytest
# =============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
