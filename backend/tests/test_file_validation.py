"""
Tests for file validation utilities.

Tests cover magic number validation, file structure checks,
signature retrieval, and supported file type verification.
"""
import pytest
from utils.file_validation import (
    validate_magic_number,
    validate_file_structure,
    get_file_signature,
    is_supported_file_type,
    FILE_SIGNATURES,
    MAX_HEADER_SIZE,
)


class TestValidateMagicNumber:
    """Tests for validate_magic_number function."""

    def test_valid_pdf_file(self):
        """Test validation of a valid PDF file."""
        content = b"%PDF-1.4\n% some content\n%%EOF"
        is_valid, error = validate_magic_number(content, ".pdf")
        assert is_valid is True
        assert error is None

    def test_valid_docx_file(self):
        """Test validation of a valid DOCX file."""
        content = b"PK\x03\x04\x14\x00\x00\x00" + b"\x00" * 100
        is_valid, error = validate_magic_number(content, ".docx")
        assert is_valid is True
        assert error is None

    def test_pdf_without_dot(self):
        """Test validation with extension without dot."""
        content = b"%PDF-1.4\n% some content"
        is_valid, error = validate_magic_number(content, "pdf")
        assert is_valid is True
        assert error is None

    def test_docx_uppercase_extension(self):
        """Test validation with uppercase extension."""
        content = b"PK\x03\x04\x14\x00\x00\x00"
        is_valid, error = validate_magic_number(content, ".DOCX")
        assert is_valid is True
        assert error is None

    def test_invalid_magic_number_for_pdf(self):
        """Test validation fails when magic number doesn't match PDF."""
        content = b"PK\x03\x04\x14\x00\x00\x00"  # ZIP signature
        is_valid, error = validate_magic_number(content, ".pdf")
        assert is_valid is False
        assert error is not None
        assert "magic number" in error.lower() or "header" in error.lower()

    def test_invalid_magic_number_for_docx(self):
        """Test validation fails when magic number doesn't match DOCX."""
        content = b"%PDF-1.4\n% some content"  # PDF signature
        is_valid, error = validate_magic_number(content, ".docx")
        assert is_valid is False
        assert error is not None
        assert "magic number" in error.lower() or "header" in error.lower()

    def test_empty_file_content(self):
        """Test validation fails with empty file content."""
        content = b""
        is_valid, error = validate_magic_number(content, ".pdf")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_file_too_small_for_pdf(self):
        """Test validation fails when file is too small."""
        content = b"%PDF"  # Too short
        is_valid, error = validate_magic_number(content, ".pdf")
        assert is_valid is False
        assert "too small" in error.lower()

    def test_file_too_small_for_docx(self):
        """Test validation fails when DOCX file is too small."""
        content = b"PK"
        is_valid, error = validate_magic_number(content, ".docx")
        assert is_valid is False
        assert "too small" in error.lower()

    def test_none_file_content(self):
        """Test validation fails with None file content."""
        is_valid, error = validate_magic_number(None, ".pdf")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_invalid_file_extension_none(self):
        """Test validation fails with None extension."""
        content = b"%PDF-1.4\n% some content"
        is_valid, error = validate_magic_number(content, None)
        assert is_valid is False
        assert "invalid" in error.lower() or "extension" in error.lower()

    def test_invalid_file_extension_empty_string(self):
        """Test validation fails with empty extension."""
        content = b"%PDF-1.4\n% some content"
        is_valid, error = validate_magic_number(content, "")
        assert is_valid is False
        assert "invalid" in error.lower() or "extension" in error.lower()

    def test_unsupported_file_extension(self):
        """Test validation fails for unsupported file type."""
        content = b"some content"
        is_valid, error = validate_magic_number(content, ".exe")
        assert is_valid is False
        assert "unsupported" in error.lower() or "extension" in error.lower()

    def test_unsupported_file_extension_txt(self):
        """Test validation fails for .txt files."""
        content = b"plain text content"
        is_valid, error = validate_magic_number(content, ".txt")
        assert is_valid is False
        assert "unsupported" in error.lower() or "extension" in error.lower()

    def test_malicious_file_renamed_as_pdf(self):
        """Test detection of malicious file renamed to PDF."""
        # PE executable header (MZ signature)
        content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
        is_valid, error = validate_magic_number(content, ".pdf")
        assert is_valid is False
        assert error is not None

    def test_malicious_file_renamed_as_docx(self):
        """Test detection of malicious file renamed to DOCX."""
        # PE executable header
        content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
        is_valid, error = validate_magic_number(content, ".docx")
        assert is_valid is False
        assert error is not None

    def test_pdf_with_extra_bytes_before_signature(self):
        """Test PDF with bytes before magic number fails."""
        content = b"\x00\x00\x00%PDF-1.4"
        is_valid, error = validate_magic_number(content, ".pdf")
        assert is_valid is False
        assert "magic number" in error.lower() or "header" in error.lower()

    def test_different_pdf_versions(self):
        """Test validation accepts different PDF versions."""
        for version in ["1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "2.0"]:
            content = f"%PDF-{version}\n%content".encode()
            is_valid, error = validate_magic_number(content, ".pdf")
            assert is_valid is True, f"Failed for PDF version {version}"
            assert error is None

    def test_content_exactly_max_header_size(self):
        """Test file with content exactly MAX_HEADER_SIZE."""
        content = b"%PDF-1.4\n" + b"x" * (MAX_HEADER_SIZE - 8)
        is_valid, error = validate_magic_number(content, ".pdf")
        assert is_valid is True
        assert error is None


class TestValidateFileStructure:
    """Tests for validate_file_structure function."""

    def test_valid_pdf_structure(self):
        """Test validation of valid PDF structure."""
        content = b"%PDF-1.4\n% some content\n" + b"x" * 100 + b"\n%%EOF"
        is_valid, error = validate_file_structure(content, ".pdf")
        assert is_valid is True
        assert error is None

    def test_valid_docx_structure(self):
        """Test validation of valid DOCX structure."""
        # Minimal ZIP/DOCX structure
        content = (
            b"PK\x03\x04\x14\x00\x00\x00"
            + b"\x00" * 100
            + b"PK\x01\x02"
            + b"\x00" * 100
            + b"PK\x05\x06"  # End of central directory
        )
        is_valid, error = validate_file_structure(content, ".docx")
        assert is_valid is True
        assert error is None

    def test_pdf_missing_eof_marker(self):
        """Test PDF without EOF marker fails validation."""
        content = b"%PDF-1.4\n% some content" + b"x" * 100
        is_valid, error = validate_file_structure(content, ".pdf")
        assert is_valid is False
        assert "eof" in error.lower() or "incomplete" in error.lower() or "corrupted" in error.lower()

    def test_pdf_eof_marker_in_last_1kb(self):
        """Test PDF with EOF marker in last 1KB passes."""
        content = b"%PDF-1.4\n" + b"x" * 900 + b"%%EOF"
        is_valid, error = validate_file_structure(content, ".pdf")
        assert is_valid is True
        assert error is None

    def test_pdf_too_small(self):
        """Test PDF file that's too small fails."""
        content = b"%PDF-1.4\n%%EOF"
        is_valid, error = validate_file_structure(content, ".pdf")
        assert is_valid is False
        assert "too small" in error.lower()

    def test_docx_too_small(self):
        """Test DOCX file that's too small fails."""
        content = b"PK\x03\x04"
        is_valid, error = validate_file_structure(content, ".docx")
        assert is_valid is False
        assert "too small" in error.lower()

    def test_pdf_exceeds_max_size(self):
        """Test PDF exceeding maximum size fails."""
        # 51 MB PDF (exceeds 50 MB limit)
        content = b"%PDF-1.4\n" + b"x" * (51 * 1024 * 1024) + b"\n%%EOF"
        is_valid, error = validate_file_structure(content, ".pdf")
        assert is_valid is False
        assert "maximum" in error.lower() or "size" in error.lower()

    def test_docx_exceeds_max_size(self):
        """Test DOCX exceeding maximum size fails."""
        # 51 MB DOCX (exceeds 50 MB limit)
        content = b"PK\x03\x04" + b"x" * (51 * 1024 * 1024)
        is_valid, error = validate_file_structure(content, ".docx")
        assert is_valid is False
        assert "maximum" in error.lower() or "size" in error.lower()

    def test_empty_file_content(self):
        """Test validation fails with empty file content."""
        content = b""
        is_valid, error = validate_file_structure(content, ".pdf")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_invalid_file_extension(self):
        """Test validation fails with invalid extension."""
        content = b"some content"
        is_valid, error = validate_file_structure(content, ".exe")
        assert is_valid is False
        assert "unsupported" in error.lower() or "extension" in error.lower()

    def test_none_file_content(self):
        """Test validation fails with None file content."""
        is_valid, error = validate_file_structure(None, ".pdf")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_none_file_extension(self):
        """Test validation fails with None extension."""
        content = b"%PDF-1.4\n%%EOF"
        is_valid, error = validate_file_structure(content, None)
        assert is_valid is False
        assert "invalid" in error.lower() or "extension" in error.lower()

    def test_minimal_valid_pdf_size(self):
        """Test PDF at minimum size boundary."""
        # Exactly 100 bytes
        content = b"%PDF-1.4\n" + b"x" * 88 + b"\n%%EOF"
        is_valid, error = validate_file_structure(content, ".pdf")
        assert is_valid is True
        assert error is None

    def test_just_under_min_pdf_size(self):
        """Test PDF just under minimum size."""
        # 99 bytes
        content = b"%PDF-1.4\n" + b"x" * 87 + b"\n%%EOF"
        is_valid, error = validate_file_structure(content, ".pdf")
        assert is_valid is False
        assert "too small" in error.lower()

    def test_minimal_valid_docx_size(self):
        """Test DOCX at minimum size boundary."""
        # Exactly 500 bytes
        content = b"PK\x03\x04" + b"x" * 495
        is_valid, error = validate_file_structure(content, ".docx")
        assert is_valid is True
        assert error is None

    def test_just_under_min_docx_size(self):
        """Test DOCX just under minimum size."""
        # 499 bytes
        content = b"PK\x03\x04" + b"x" * 494
        is_valid, error = validate_file_structure(content, ".docx")
        assert is_valid is False
        assert "too small" in error.lower()

    def test_case_insensitive_extension(self):
        """Test extension matching is case-insensitive."""
        content = b"%PDF-1.4\n" + b"x" * 100 + b"\n%%EOF"
        for ext in [".pdf", ".PDF", ".Pdf", "pdf", "PDF"]:
            is_valid, error = validate_file_structure(content, ext)
            assert is_valid is True, f"Failed for extension {ext}"
            assert error is None

    def test_unsupported_extension(self):
        """Test unsupported file extension."""
        content = b"some content" * 100
        is_valid, error = validate_file_structure(content, ".txt")
        assert is_valid is False
        assert "unsupported" in error.lower() or "extension" in error.lower()


class TestGetFileSignature:
    """Tests for get_file_signature function."""

    def test_get_pdf_signature_with_dot(self):
        """Test getting PDF signature with dot prefix."""
        signature = get_file_signature(".pdf")
        assert signature == b"%PDF-"

    def test_get_pdf_signature_without_dot(self):
        """Test getting PDF signature without dot prefix."""
        signature = get_file_signature("pdf")
        assert signature == b"%PDF-"

    def test_get_docx_signature_with_dot(self):
        """Test getting DOCX signature with dot prefix."""
        signature = get_file_signature(".docx")
        assert signature == b"PK\x03\x04"

    def test_get_docx_signature_without_dot(self):
        """Test getting DOCX signature without dot prefix."""
        signature = get_file_signature("docx")
        assert signature == b"PK\x03\x04"

    def test_uppercase_extension(self):
        """Test getting signature with uppercase extension."""
        signature = get_file_signature(".PDF")
        assert signature == b"%PDF-"

    def test_mixed_case_extension(self):
        """Test getting signature with mixed case extension."""
        signature = get_file_signature(".Pdf")
        assert signature == b"%PDF-"

    def test_unsupported_extension_returns_none(self):
        """Test unsupported extension returns None."""
        signature = get_file_signature(".exe")
        assert signature is None

    def test_txt_extension_returns_none(self):
        """Test .txt extension returns None."""
        signature = get_file_signature(".txt")
        assert signature is None

    def test_empty_string_extension(self):
        """Test empty string extension returns None."""
        signature = get_file_signature("")
        assert signature is None

    def test_none_extension(self):
        """Test None extension returns None."""
        signature = get_file_signature(None)
        assert signature is None


class TestIsSupportedFileType:
    """Tests for is_supported_file_type function."""

    def test_pdf_supported_with_dot(self):
        """Test PDF is supported with dot prefix."""
        assert is_supported_file_type(".pdf") is True

    def test_pdf_supported_without_dot(self):
        """Test PDF is supported without dot prefix."""
        assert is_supported_file_type("pdf") is True

    def test_docx_supported_with_dot(self):
        """Test DOCX is supported with dot prefix."""
        assert is_supported_file_type(".docx") is True

    def test_docx_supported_without_dot(self):
        """Test DOCX is supported without dot prefix."""
        assert is_supported_file_type("docx") is True

    def test_uppercase_pdf_supported(self):
        """Test uppercase PDF extension is supported."""
        assert is_supported_file_type(".PDF") is True

    def test_mixed_case_pdf_supported(self):
        """Test mixed case PDF extension is supported."""
        assert is_supported_file_type(".Pdf") is True

    def test_exe_not_supported(self):
        """Test .exe is not supported."""
        assert is_supported_file_type(".exe") is False

    def test_txt_not_supported(self):
        """Test .txt is not supported."""
        assert is_supported_file_type(".txt") is False

    def test_jpg_not_supported(self):
        """Test .jpg is not supported."""
        assert is_supported_file_type(".jpg") is False

    def test_png_not_supported(self):
        """Test .png is not supported."""
        assert is_supported_file_type(".png") is False

    def test_empty_string_not_supported(self):
        """Test empty string is not supported."""
        assert is_supported_file_type("") is False

    def test_none_not_supported(self):
        """Test None is not supported."""
        assert is_supported_file_type(None) is False


class TestFileSignaturesConstant:
    """Tests for FILE_SIGNATURES constant."""

    def test_pdf_signature_correct(self):
        """Test PDF signature is correct."""
        assert "pdf" in FILE_SIGNATURES
        assert FILE_SIGNATURES["pdf"] == b"%PDF-"

    def test_docx_signature_correct(self):
        """Test DOCX signature is correct."""
        assert "docx" in FILE_SIGNATURES
        assert FILE_SIGNATURES["docx"] == b"PK\x03\x04"

    def test_signatures_are_bytes(self):
        """Test all signatures are bytes."""
        for ext, signature in FILE_SIGNATURES.items():
            assert isinstance(signature, bytes), f"Signature for {ext} is not bytes"

    def test_extensions_lowercase(self):
        """Test all extensions are lowercase."""
        for ext in FILE_SIGNATURES.keys():
            assert ext == ext.lower(), f"Extension {ext} is not lowercase"


class TestMaxHeaderSizeConstant:
    """Tests for MAX_HEADER_SIZE constant."""

    def test_max_header_size_is_int(self):
        """Test MAX_HEADER_SIZE is an integer."""
        assert isinstance(MAX_HEADER_SIZE, int)

    def test_max_header_size_reasonable(self):
        """Test MAX_HEADER_SIZE is reasonable for magic number checking."""
        assert MAX_HEADER_SIZE >= 8  # At least 8 bytes for basic signatures
        assert MAX_HEADER_SIZE <= 32  # Not too large


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_pdf_with_bom(self):
        """Test PDF with UTF-8 BOM fails validation."""
        content = b"\xef\xbb\xbf%PDF-1.4\n"
        is_valid, error = validate_magic_number(content, ".pdf")
        assert is_valid is False
        assert "magic number" in error.lower() or "header" in error.lower()

    def test_zip_with_extra_data(self):
        """Test ZIP/DOCX with extra data after signature."""
        content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00" + b"\x00" * 100
        is_valid, error = validate_magic_number(content, ".docx")
        assert is_valid is True
        assert error is None

    def test_pdf_with_binary_content(self):
        """Test PDF with binary content after header."""
        content = b"%PDF-1.4\n" + b"\x00\x01\x02\x03\xff\xfe\xfd" * 20 + b"\n%%EOF"
        is_valid, error = validate_file_structure(content, ".pdf")
        assert is_valid is True
        assert error is None

    def test_exactly_minimum_pdf_bytes(self):
        """Test PDF with exactly minimum bytes for magic number."""
        content = b"%PDF-"
        is_valid, error = validate_magic_number(content, ".pdf")
        # Should fail structure validation but pass magic number
        assert is_valid is True
        assert error is None

    def test_one_byte_less_than_minimum(self):
        """Test PDF one byte shorter than magic number."""
        content = b"%PDF"
        is_valid, error = validate_magic_number(content, ".pdf")
        assert is_valid is False
        assert "too small" in error.lower()

    def test_multiple_extensions_supported(self):
        """Test that multiple file types are supported."""
        supported_types = ["pdf", "docx"]
        for ext in supported_types:
            assert is_supported_file_type(ext), f"{ext} should be supported"

    def test_locale_parameter_accepted(self):
        """Test that locale parameter is accepted (even if not used yet)."""
        content = b"%PDF-1.4\n%%EOF"
        is_valid, error = validate_magic_number(content, ".pdf", locale="en")
        assert is_valid is True

        is_valid, error = validate_file_structure(content, ".pdf", locale="ru")
        assert is_valid is True

    def test_non_string_extension_type(self):
        """Test with non-string extension type."""
        content = b"%PDF-1.4\n"
        is_valid, error = validate_magic_number(content, 123)
        assert is_valid is False

    def test_bytes_in_extension(self):
        """Test with bytes instead of string for extension."""
        content = b"%PDF-1.4\n"
        is_valid, error = validate_magic_number(content, b".pdf")
        # Should handle gracefully
        assert is_valid is False


class TestCombinedValidation:
    """Tests for combined validation scenarios."""

    def test_valid_file_passes_both_validations(self):
        """Test that a valid file passes both magic number and structure checks."""
        content = b"%PDF-1.4\n" + b"x" * 200 + b"\n%%EOF"

        magic_valid, magic_error = validate_magic_number(content, ".pdf")
        struct_valid, struct_error = validate_file_structure(content, ".pdf")

        assert magic_valid is True
        assert magic_error is None
        assert struct_valid is True
        assert struct_error is None

    def test_invalid_magic_fails_first(self):
        """Test that invalid magic number is caught early."""
        content = b"Wrong header" + b"x" * 200 + b"\n%%EOF"

        magic_valid, magic_error = validate_magic_number(content, ".pdf")
        struct_valid, struct_error = validate_file_structure(content, ".pdf")

        # Magic number validation should fail
        assert magic_valid is False
        # Structure validation should also fail (wrong magic number)
        assert struct_valid is False

    def test_valid_magic_invalid_structure(self):
        """Test file with valid magic number but invalid structure."""
        # Valid PDF header but missing EOF
        content = b"%PDF-1.4\n" + b"x" * 200

        magic_valid, magic_error = validate_magic_number(content, ".pdf")
        struct_valid, struct_error = validate_file_structure(content, ".pdf")

        # Magic number should pass
        assert magic_valid is True
        # Structure validation should fail (no EOF)
        assert struct_valid is False
        assert "eof" in struct_error.lower() or "incomplete" in struct_error.lower()
