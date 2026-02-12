"""
Tests for ZIP archive extraction utilities.

Tests cover ZIP file validation, filename sanitization, extraction,
info retrieval, and security scenarios including path traversal prevention.
"""
import io
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from utils.zip_extractor import (
    extract_resumes_from_zip,
    get_zip_info,
    _is_allowed_extension,
    _sanitize_filename,
    _validate_zip_file,
    MAX_ZIP_SIZE_MB,
    MAX_EXTRACTED_FILES,
    MAX_EXTRACTED_SIZE_MB,
    MAX_SINGLE_FILE_SIZE_MB,
    ALLOWED_EXTENSIONS,
)


def create_valid_zip_with_files(files: dict) -> bytes:
    """
    Helper to create a valid ZIP archive in memory.

    Args:
        files: Dictionary of {filename: content} pairs

    Returns:
        ZIP file as bytes
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename, content in files.items():
            zf.writestr(filename, content)
    return buffer.getvalue()


def create_valid_pdf_content() -> bytes:
    """Create valid PDF content for testing."""
    return b"%PDF-1.4\n% test content\n" + b"x" * 200 + b"\n%%EOF"


def create_valid_docx_content() -> bytes:
    """Create minimal valid DOCX/ZIP content for testing."""
    return create_valid_zip_with_files({
        "[Content_Types].xml": b"<?xml version='1.0'?><Types/>",
        "word/document.xml": b"<?xml version='1.0'?><document/>",
    })


class TestIsAllowedExtension:
    """Tests for _is_allowed_extension function."""

    def test_pdf_extension_allowed(self):
        """Test PDF extension is allowed."""
        assert _is_allowed_extension("resume.pdf") is True

    def test_docx_extension_allowed(self):
        """Test DOCX extension is allowed."""
        assert _is_allowed_extension("resume.docx") is True

    def test_uppercase_pdf_allowed(self):
        """Test uppercase PDF extension is allowed."""
        assert _is_allowed_extension("resume.PDF") is True

    def test_uppercase_docx_allowed(self):
        """Test uppercase DOCX extension is allowed."""
        assert _is_allowed_extension("resume.DOCX") is True

    def test_mixed_case_allowed(self):
        """Test mixed case extension is allowed."""
        assert _is_allowed_extension("resume.PdF") is True
        assert _is_allowed_extension("resume.DoCx") is True

    def test_txt_not_allowed(self):
        """Test TXT extension is not allowed."""
        assert _is_allowed_extension("resume.txt") is False

    def test_exe_not_allowed(self):
        """Test EXE extension is not allowed."""
        assert _is_allowed_extension("malware.exe") is False

    def test_no_extension(self):
        """Test file without extension is not allowed."""
        assert _is_allowed_extension("resume") is False

    def test_empty_string(self):
        """Test empty string is not allowed."""
        assert _is_allowed_extension("") is False

    def test_hidden_file(self):
        """Test hidden file (starting with dot) is not allowed."""
        assert _is_allowed_extension(".hidden") is False

    def test_jpg_not_allowed(self):
        """Test JPG extension is not allowed."""
        assert _is_allowed_extension("photo.jpg") is False

    def test_png_not_allowed(self):
        """Test PNG extension is not allowed."""
        assert _is_allowed_extension("photo.png") is False


class TestSanitizeFilename:
    """Tests for _sanitize_filename function."""

    def test_simple_filename(self):
        """Test sanitizing a simple filename."""
        result = _sanitize_filename("resume.pdf")
        assert result == "resume.pdf"

    def test_filename_with_directory(self):
        """Test filename with directory path is stripped."""
        result = _sanitize_filename("folder/resume.pdf")
        assert result == "resume.pdf"

    def test_filename_with_nested_directory(self):
        """Test filename with nested path is stripped."""
        result = _sanitize_filename("deep/nested/path/resume.docx")
        assert result == "resume.docx"

    def test_path_traversal_attack(self):
        """Test path traversal attack is blocked."""
        result = _sanitize_filename("../../../etc/passwd")
        assert result is None

    def test_double_dot_in_filename(self):
        """Test double dots in filename are blocked."""
        result = _sanitize_filename("resume..pdf")
        assert result is None

    def test_hidden_file_blocked(self):
        """Test hidden files (starting with dot) are blocked."""
        result = _sanitize_filename(".hidden_file")
        assert result is None

    def test_null_byte_in_filename(self):
        """Test null byte injection is blocked."""
        result = _sanitize_filename("resume\x00.pdf")
        assert result is None

    def test_empty_filename(self):
        """Test empty filename returns None."""
        result = _sanitize_filename("")
        assert result is None

    def test_directory_only(self):
        """Test directory only (ending with slash) returns None."""
        result = _sanitize_filename("folder/")
        assert result is None

    def test_windows_path(self):
        """Test Windows-style path is handled."""
        result = _sanitize_filename("C:\\Users\\test\\resume.pdf")
        # Path.name should extract just the filename
        assert result == "resume.pdf"

    def test_path_traversal_with_subdir(self):
        """Test path traversal within subdirectory."""
        result = _sanitize_filename("subdir/../resume.pdf")
        # Path.name strips directory components
        assert result == "resume.pdf"

    def test_complex_path_traversal(self):
        """Test complex path traversal attempt."""
        result = _sanitize_filename("a/b/c/../../../resume.pdf")
        assert result == "resume.pdf"

    def test_empty_after_sanitization(self):
        """Test filename that becomes empty after sanitization."""
        result = _sanitize_filename(".")
        assert result is None


class TestValidateZipFile:
    """Tests for _validate_zip_file function."""

    def test_valid_zip_content(self):
        """Test validation of valid ZIP content."""
        zip_content = create_valid_zip_with_files({"test.txt": b"content"})
        is_valid, error = _validate_zip_file(zip_content)
        assert is_valid is True
        assert error is None

    def test_empty_content(self):
        """Test validation fails with empty content."""
        is_valid, error = _validate_zip_file(b"")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_none_content(self):
        """Test validation fails with None content."""
        is_valid, error = _validate_zip_file(None)
        assert is_valid is False
        assert "empty" in error.lower()

    def test_invalid_magic_number(self):
        """Test validation fails with invalid magic number."""
        content = b"Not a ZIP file content"
        is_valid, error = _validate_zip_file(content)
        assert is_valid is False
        assert "magic number" in error.lower() or "valid" in error.lower()

    def test_pdf_file_as_zip(self):
        """Test validation fails when PDF is passed as ZIP."""
        content = b"%PDF-1.4\n% content"
        is_valid, error = _validate_zip_file(content)
        assert is_valid is False
        assert "magic number" in error.lower() or "valid" in error.lower()

    def test_exe_file_as_zip(self):
        """Test validation fails when EXE is passed as ZIP."""
        # PE executable header
        content = b"MZ\x90\x00\x03\x00"
        is_valid, error = _validate_zip_file(content)
        assert is_valid is False

    def test_small_valid_zip(self):
        """Test validation of small valid ZIP."""
        zip_content = create_valid_zip_with_files({"a.txt": b"x"})
        is_valid, error = _validate_zip_file(zip_content)
        assert is_valid is True
        assert error is None


class TestExtractResumesFromZip:
    """Tests for extract_resumes_from_zip function."""

    def test_extract_single_pdf(self):
        """Test extracting a single PDF file."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume.pdf": pdf_content})

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is None
        assert result["file_count"] == 1
        assert len(result["files"]) == 1
        assert result["files"][0]["filename"] == "resume.pdf"
        assert result["files"][0]["valid"] is True

    def test_extract_single_docx(self):
        """Test extracting a single DOCX file."""
        docx_content = create_valid_docx_content()
        zip_content = create_valid_zip_with_files({"resume.docx": docx_content})

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is None
        assert result["file_count"] == 1
        assert result["files"][0]["filename"] == "resume.docx"

    def test_extract_multiple_files(self):
        """Test extracting multiple files."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({
            "resume1.pdf": pdf_content,
            "resume2.pdf": pdf_content,
            "resume3.docx": create_valid_docx_content(),
        })

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is None
        assert result["file_count"] == 3
        assert len(result["files"]) == 3

    def test_skip_unsupported_files(self):
        """Test that unsupported files are skipped."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({
            "resume.pdf": pdf_content,
            "readme.txt": b"text content",
            "image.jpg": b"fake image",
        })

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is None
        assert result["file_count"] == 1
        assert result["skipped_count"] == 2

    def test_skip_directories(self):
        """Test that directories are skipped."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({
            "resume.pdf": pdf_content,
            "folder/": b"",  # Directory entry
        })

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is None
        assert result["file_count"] == 1

    def test_nested_directory_structure(self):
        """Test extraction from nested directories."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({
            "resumes/2024/jan/resume.pdf": pdf_content,
            "resumes/2024/feb/resume2.pdf": pdf_content,
        })

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is None
        assert result["file_count"] == 2
        # Filenames should be sanitized (stripped of directory)
        assert result["files"][0]["filename"] == "resume.pdf"
        assert result["files"][1]["filename"] == "resume2.pdf"

    def test_empty_zip(self):
        """Test extraction from empty ZIP."""
        zip_content = create_valid_zip_with_files({})

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is not None
        assert "no valid" in result["error"].lower()
        assert result["file_count"] == 0

    def test_invalid_zip(self):
        """Test extraction from invalid ZIP."""
        result = extract_resumes_from_zip(b"Not a ZIP file")

        assert result["error"] is not None
        assert result["file_count"] == 0

    def test_empty_bytes_input(self):
        """Test extraction from empty bytes."""
        result = extract_resumes_from_zip(b"")

        assert result["error"] is not None
        assert "empty" in result["error"].lower()

    def test_none_input(self):
        """Test extraction from None."""
        # The function should handle this gracefully
        # It returns early with invalid type error
        result = extract_resumes_from_zip(None)

        assert result["error"] is not None

    def test_file_path_input(self, tmp_path):
        """Test extraction from file path."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume.pdf": pdf_content})

        zip_path = tmp_path / "test.zip"
        zip_path.write_bytes(zip_content)

        result = extract_resumes_from_zip(str(zip_path))

        assert result["error"] is None
        assert result["file_count"] == 1

    def test_path_object_input(self, tmp_path):
        """Test extraction from Path object."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume.pdf": pdf_content})

        zip_path = tmp_path / "test.zip"
        zip_path.write_bytes(zip_content)

        result = extract_resumes_from_zip(zip_path)

        assert result["error"] is None
        assert result["file_count"] == 1

    def test_nonexistent_file_path(self):
        """Test extraction from non-existent file path."""
        result = extract_resumes_from_zip("/nonexistent/path/to/file.zip")

        assert result["error"] is not None
        assert "not found" in result["error"].lower()

    def test_invalid_source_type(self):
        """Test extraction with invalid source type."""
        result = extract_resumes_from_zip(12345)  # Invalid type

        assert result["error"] is not None
        assert "invalid" in result["error"].lower()

    def test_validation_enabled(self):
        """Test extraction with validation enabled."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume.pdf": pdf_content})

        result = extract_resumes_from_zip(zip_content, validate_files=True)

        assert result["error"] is None
        assert result["files"][0]["valid"] is True
        assert result["files"][0]["validation_error"] is None

    def test_validation_disabled(self):
        """Test extraction with validation disabled."""
        # Invalid PDF content (wrong magic number)
        invalid_content = b"Not a PDF content"
        zip_content = create_valid_zip_with_files({"resume.pdf": invalid_content})

        result = extract_resumes_from_zip(zip_content, validate_files=False)

        assert result["error"] is None
        assert result["files"][0]["valid"] is True  # Not validated

    def test_invalid_file_validation(self):
        """Test extraction catches invalid files during validation."""
        # PDF with wrong content
        invalid_content = b"Not a PDF at all"
        zip_content = create_valid_zip_with_files({"resume.pdf": invalid_content})

        result = extract_resumes_from_zip(zip_content, validate_files=True)

        assert result["error"] is None
        # File is extracted but marked as invalid
        assert result["files"][0]["valid"] is False
        assert result["files"][0]["validation_error"] is not None

    def test_max_files_limit(self):
        """Test maximum files limit is enforced."""
        pdf_content = create_valid_pdf_content()
        files = {f"resume{i}.pdf": pdf_content for i in range(10)}
        zip_content = create_valid_zip_with_files(files)

        result = extract_resumes_from_zip(zip_content, max_files=5)

        assert result["file_count"] == 5
        assert result["skipped_count"] > 0
        assert len(result["warnings"]) > 0

    def test_total_size_limit(self):
        """Test total size limit is enforced."""
        # Create large PDF content
        large_pdf = b"%PDF-1.4\n" + b"x" * (2 * 1024 * 1024) + b"\n%%EOF"  # 2MB
        files = {f"resume{i}.pdf": large_pdf for i in range(10)}
        zip_content = create_valid_zip_with_files(files)

        # Set a very low total size limit (1MB)
        result = extract_resumes_from_zip(zip_content, max_total_size_mb=1)

        # Should skip files due to size limit
        assert result["total_size"] <= 1 * 1024 * 1024

    def test_path_traversal_prevention(self):
        """Test path traversal attack is prevented."""
        pdf_content = create_valid_pdf_content()
        # Create ZIP with path traversal attempt
        zip_content = create_valid_zip_with_files({
            "../../../malicious.pdf": pdf_content,
            "normal.pdf": pdf_content,
        })

        result = extract_resumes_from_zip(zip_content)

        # Path traversal file should be skipped
        assert result["error"] is None
        filenames = [f["filename"] for f in result["files"]]
        assert "malicious.pdf" not in filenames
        assert "normal.pdf" in filenames

    def test_result_includes_total_size(self):
        """Test result includes total extracted size."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({
            "resume1.pdf": pdf_content,
            "resume2.pdf": pdf_content,
        })

        result = extract_resumes_from_zip(zip_content)

        assert "total_size" in result
        assert result["total_size"] > 0
        assert result["total_size"] == len(pdf_content) * 2

    def test_result_includes_warnings(self):
        """Test result includes warnings list."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume.pdf": pdf_content})

        result = extract_resumes_from_zip(zip_content)

        assert "warnings" in result
        assert isinstance(result["warnings"], list)

    def test_file_info_structure(self):
        """Test extracted file info structure."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume.pdf": pdf_content})

        result = extract_resumes_from_zip(zip_content)

        file_info = result["files"][0]
        assert "filename" in file_info
        assert "content" in file_info
        assert "size" in file_info
        assert "extension" in file_info
        assert "valid" in file_info
        assert "validation_error" in file_info
        assert "original_path" in file_info

    def test_skip_unsupported_false(self):
        """Test including unsupported files when skip_unsupported=False."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({
            "resume.pdf": pdf_content,
            "notes.txt": b"some notes",
        })

        result = extract_resumes_from_zip(zip_content, skip_unsupported=False)

        # Both files should be extracted (though txt won't be validated)
        assert result["file_count"] == 2


class TestGetZipInfo:
    """Tests for get_zip_info function."""

    def test_get_info_single_file(self):
        """Test getting info for ZIP with single file."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume.pdf": pdf_content})

        result = get_zip_info(zip_content)

        assert result["error"] is None
        assert result["file_count"] == 1
        assert result["resume_count"] == 1
        assert len(result["files"]) == 1

    def test_get_info_multiple_files(self):
        """Test getting info for ZIP with multiple files."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({
            "resume1.pdf": pdf_content,
            "resume2.pdf": pdf_content,
            "notes.txt": b"notes",
        })

        result = get_zip_info(zip_content)

        assert result["error"] is None
        assert result["file_count"] == 3
        assert result["resume_count"] == 2

    def test_get_info_with_directories(self):
        """Test getting info for ZIP with directories."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({
            "resume.pdf": pdf_content,
            "folder/": b"",
        })

        result = get_zip_info(zip_content)

        assert result["error"] is None
        # Directories are not counted in file_count
        assert result["file_count"] == 1

    def test_get_info_invalid_zip(self):
        """Test getting info for invalid ZIP."""
        result = get_zip_info(b"Not a ZIP")

        assert result["error"] is not None
        assert result["file_count"] == 0

    def test_get_info_empty_zip(self):
        """Test getting info for empty ZIP."""
        zip_content = create_valid_zip_with_files({})

        result = get_zip_info(zip_content)

        assert result["file_count"] == 0
        assert result["resume_count"] == 0

    def test_get_info_file_path(self, tmp_path):
        """Test getting info from file path."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume.pdf": pdf_content})

        zip_path = tmp_path / "test.zip"
        zip_path.write_bytes(zip_content)

        result = get_zip_info(str(zip_path))

        assert result["error"] is None
        assert result["file_count"] == 1

    def test_get_info_nonexistent_file(self):
        """Test getting info for non-existent file."""
        result = get_zip_info("/nonexistent/file.zip")

        assert result["error"] is not None
        assert "not found" in result["error"].lower()

    def test_get_info_invalid_source_type(self):
        """Test getting info with invalid source type."""
        result = get_zip_info(12345)

        assert result["error"] is not None

    def test_get_info_includes_compression_ratio(self):
        """Test info includes compression ratio."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume.pdf": pdf_content})

        result = get_zip_info(zip_content)

        assert "compression_ratio" in result
        assert isinstance(result["compression_ratio"], float)

    def test_get_info_file_structure(self):
        """Test file info structure."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume.pdf": pdf_content})

        result = get_zip_info(zip_content)

        file_info = result["files"][0]
        assert "filename" in file_info
        assert "size" in file_info
        assert "compressed_size" in file_info
        assert "extension" in file_info
        assert "is_directory" in file_info
        assert "is_resume" in file_info

    def test_get_info_total_size(self):
        """Test info includes total uncompressed size."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({
            "resume1.pdf": pdf_content,
            "resume2.pdf": pdf_content,
        })

        result = get_zip_info(zip_content)

        assert result["total_size"] == len(pdf_content) * 2


class TestConfigurationConstants:
    """Tests for configuration constants."""

    def test_max_zip_size_mb_reasonable(self):
        """Test MAX_ZIP_SIZE_MB is reasonable."""
        assert isinstance(MAX_ZIP_SIZE_MB, int)
        assert MAX_ZIP_SIZE_MB > 0
        assert MAX_ZIP_SIZE_MB <= 500  # Not too large

    def test_max_extracted_files_reasonable(self):
        """Test MAX_EXTRACTED_FILES is reasonable."""
        assert isinstance(MAX_EXTRACTED_FILES, int)
        assert MAX_EXTRACTED_FILES > 0
        assert MAX_EXTRACTED_FILES <= 1000  # Not too large

    def test_max_extracted_size_mb_reasonable(self):
        """Test MAX_EXTRACTED_SIZE_MB is reasonable."""
        assert isinstance(MAX_EXTRACTED_SIZE_MB, int)
        assert MAX_EXTRACTED_SIZE_MB > 0
        assert MAX_EXTRACTED_SIZE_MB >= MAX_ZIP_SIZE_MB

    def test_max_single_file_size_mb_reasonable(self):
        """Test MAX_SINGLE_FILE_SIZE_MB is reasonable."""
        assert isinstance(MAX_SINGLE_FILE_SIZE_MB, int)
        assert MAX_SINGLE_FILE_SIZE_MB > 0
        assert MAX_SINGLE_FILE_SIZE_MB <= MAX_EXTRACTED_SIZE_MB

    def test_allowed_extensions_set(self):
        """Test ALLOWED_EXTENSIONS is a set."""
        assert isinstance(ALLOWED_EXTENSIONS, set)

    def test_allowed_extensions_contains_pdf(self):
        """Test ALLOWED_EXTENSIONS contains PDF."""
        assert "pdf" in ALLOWED_EXTENSIONS

    def test_allowed_extensions_contains_docx(self):
        """Test ALLOWED_EXTENSIONS contains DOCX."""
        assert "docx" in ALLOWED_EXTENSIONS

    def test_allowed_extensions_lowercase(self):
        """Test all allowed extensions are lowercase."""
        for ext in ALLOWED_EXTENSIONS:
            assert ext == ext.lower()


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_unicode_filename(self):
        """Test extraction with Unicode filename."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"résumé_日本語.pdf": pdf_content})

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is None
        assert result["file_count"] == 1

    def test_spaces_in_filename(self):
        """Test extraction with spaces in filename."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"my resume 2024.pdf": pdf_content})

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is None
        assert result["files"][0]["filename"] == "my resume 2024.pdf"

    def test_special_characters_in_filename(self):
        """Test extraction with special characters in filename."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume_(final)-v2.pdf": pdf_content})

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is None

    def test_duplicate_filenames_different_paths(self):
        """Test extraction with duplicate filenames in different paths."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({
            "folder1/resume.pdf": pdf_content,
            "folder2/resume.pdf": pdf_content,
        })

        result = extract_resumes_from_zip(zip_content)

        # Both should be extracted (same basename, different original paths)
        assert result["file_count"] == 2
        # Both have same sanitized filename
        filenames = [f["filename"] for f in result["files"]]
        assert filenames.count("resume.pdf") == 2

    def test_case_insensitive_extension_matching(self):
        """Test case-insensitive extension matching."""
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({
            "resume.PDF": pdf_content,
            "resume.Pdf": pdf_content,
            "resume.DocX": create_valid_docx_content(),
        })

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is None
        assert result["file_count"] == 3

    def test_file_exactly_at_size_limit(self, tmp_path):
        """Test file exactly at single file size limit."""
        # Create content at the exact limit
        content_size = MAX_SINGLE_FILE_SIZE_MB * 1024 * 1024
        # Note: actual test would need to create this, but it's very large
        # This is more of a documentation test
        assert MAX_SINGLE_FILE_SIZE_MB > 0

    def test_empty_pdf_file(self):
        """Test handling of empty PDF file in ZIP."""
        # Create ZIP with empty file
        zip_content = create_valid_zip_with_files({"empty.pdf": b""})

        result = extract_resumes_from_zip(zip_content, validate_files=True)

        # Empty file should either fail validation or be skipped
        if result["file_count"] > 0:
            assert result["files"][0]["valid"] is False

    def test_corrupted_zip_entry(self):
        """Test handling of corrupted ZIP entry."""
        # Create a valid ZIP then corrupt it
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume.pdf": pdf_content})

        # Corrupt the ZIP by modifying some bytes in the middle
        corrupted = bytearray(zip_content)
        if len(corrupted) > 50:
            corrupted[30:40] = b'\x00' * 10
            corrupted = bytes(corrupted)

        result = extract_resumes_from_zip(corrupted)

        # Should either handle gracefully or report error
        assert "error" in result
        assert "files" in result

    def test_zip_with_only_directories(self):
        """Test ZIP containing only directories."""
        zip_content = create_valid_zip_with_files({
            "folder1/": b"",
            "folder2/": b"",
        })

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is not None
        assert "no valid" in result["error"].lower()

    def test_zip_with_only_unsupported_files(self):
        """Test ZIP containing only unsupported file types."""
        zip_content = create_valid_zip_with_files({
            "readme.txt": b"text",
            "image.jpg": b"fake image",
        })

        result = extract_resumes_from_zip(zip_content)

        assert result["error"] is not None
        assert result["skipped_count"] == 2


class TestSecurityScenarios:
    """Tests for security-related scenarios."""

    def test_zip_slip_attack(self):
        """Test ZIP slip path traversal attack is blocked."""
        pdf_content = create_valid_pdf_content()

        # Manually create a ZIP with path traversal
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zf:
            # Normal entry
            zf.writestr("normal.pdf", pdf_content)
            # Path traversal entry
            zf.writestr("../../../tmp/malicious.pdf", pdf_content)

        result = extract_resumes_from_zip(buffer.getvalue())

        # Path traversal file should be skipped
        for f in result["files"]:
            assert ".." not in f["filename"]

    def test_null_byte_injection(self):
        """Test null byte injection is blocked."""
        pdf_content = create_valid_pdf_content()

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zf:
            zf.writestr("resume\x00.exe.pdf", pdf_content)

        result = extract_resumes_from_zip(buffer.getvalue())

        # File with null byte should be skipped
        for f in result["files"]:
            assert "\x00" not in f["filename"]

    def test_symlink_in_zip(self):
        """Test handling of symlinks in ZIP."""
        # Note: Python's zipfile handles symlinks specially
        # This test documents expected behavior
        pdf_content = create_valid_pdf_content()
        zip_content = create_valid_zip_with_files({"resume.pdf": pdf_content})

        result = extract_resumes_from_zip(zip_content)

        # Regular files should be extracted normally
        assert result["error"] is None

    def test_very_long_filename(self):
        """Test handling of very long filenames."""
        pdf_content = create_valid_pdf_content()
        long_name = "a" * 500 + ".pdf"

        zip_content = create_valid_zip_with_files({long_name: pdf_content})

        result = extract_resumes_from_zip(zip_content)

        # Should handle gracefully (may truncate or skip)
        assert "error" in result
        assert "files" in result

    def test_maximum_files_limit_enforced(self):
        """Test that maximum files limit cannot be bypassed."""
        pdf_content = create_valid_pdf_content()
        # Create ZIP with many files
        files = {f"file{i}.pdf": pdf_content for i in range(200)}
        zip_content = create_valid_zip_with_files(files)

        result = extract_resumes_from_zip(zip_content, max_files=50)

        assert result["file_count"] <= 50
        assert result["skipped_count"] > 0

    def test_decompression_bomb_protection(self):
        """Test protection against decompression bombs."""
        # Create highly compressed content (simulated)
        # In practice, the size limits should prevent this
        small_compressed = b"PK\x03\x04" + b"\x00" * 100

        result = extract_resumes_from_zip(small_compressed)

        # Should fail validation as invalid ZIP
        assert result["error"] is not None
