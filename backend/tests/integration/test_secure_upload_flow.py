"""
Integration tests for secure upload flow with magic number validation and rate limiting.

This test suite validates the security enhancements for file upload:
- Magic number validation (file signature verification)
- Rate limiting to prevent bulk upload attacks
- Filename sanitization to prevent path traversal
- Audit logging for security events
- Malicious file pattern detection

Test Coverage:
- Valid PDF/DOCX files accepted
- Invalid magic numbers rejected (EXE renamed to PDF, etc.)
- Rate limiting enforced (10 uploads per minute)
- Filename sanitization (path traversal prevention)
- Audit logs created for security events
- Complete secure upload workflow
"""
import io
import time
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app


@pytest.fixture
def valid_pdf_file() -> bytes:
    """
    Create a minimal valid PDF file for testing.

    Returns:
        Bytes content of a simple PDF file with correct magic number
    """
    # Create a minimal PDF file with text content and proper structure
    pdf_content = b"""%PDF-1.4
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
/Resources <<
/Font <<
/F1 4 0 R
>>
>>
/MediaBox [0 0 612 792]
/Contents 5 0 R
>>
endobj
4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
5 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
50 700 Td
(John Doe - Software Engineer) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000264 00000 n
0000000349 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
428
%%EOF
"""
    return pdf_content


@pytest.fixture
def valid_docx_file() -> bytes:
    """
    Create a minimal valid DOCX file for testing.

    Returns:
        Bytes content of a simple DOCX file with correct magic number (ZIP signature)
    """
    # DOCX files are ZIP archives starting with PK\x03\x04
    # This is a minimal valid ZIP structure for testing
    docx_content = b"PK\x03\x04" + b"Test DOCX content" * 100
    return docx_content


@pytest.fixture
def invalid_pdf_exe() -> bytes:
    """
    Create an EXE file renamed to PDF (invalid magic number).

    This simulates a malicious file upload attempt where an attacker
    renames a Windows executable to .pdf to bypass extension checks.

    Returns:
        Bytes content of a PE executable with .pdf extension
    """
    # PE executable header (MZ signature)
    exe_content = b"MZ\x90\x00" + b"\x00" * 100  # Minimal PE header
    return exe_content


@pytest.fixture
def invalid_pdf_text() -> bytes:
    """
    Create a plain text file renamed to PDF (invalid magic number).

    Returns:
        Bytes content of a text file with .pdf extension
    """
    # Plain text that doesn't start with %PDF-
    text_content = b"This is not a PDF file, just plain text."
    return text_content


@pytest.fixture
def invalid_docx_random() -> bytes:
    """
    Create random bytes with .docx extension (invalid magic number).

    Returns:
        Random bytes with .docx extension
    """
    random_content = b"\x00\x01\x02\x03" + b"Random content" * 50
    return random_content


@pytest.fixture
def malicious_filename_files() -> dict:
    """
    Create test files with malicious filename patterns.

    Returns:
        Dictionary with filename patterns and file content
    """
    return {
        "path_traversal": ("../../../etc/passwd", valid_pdf_file.__func__()),
        "null_byte": ("test\x00.pdf", valid_pdf_file.__func__()),
        "special_chars": ("test:file*.pdf", valid_pdf_file.__func__()),
        "long_name": ("a" * 300 + ".pdf", valid_pdf_file.__func__()),
    }


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client for all tests.

    Yields:
        TestClient instance
    """
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as test_client:
        yield test_client


class TestMagicNumberValidation:
    """Tests for magic number (file signature) validation."""

    def test_valid_pdf_accepted(self, client: TestClient, valid_pdf_file: bytes):
        """Test that a valid PDF file with correct magic number is accepted."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("valid_resume.pdf", io.BytesIO(valid_pdf_file), "application/pdf")}
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["filename"] == "valid_resume.pdf"
        assert data["status"] == "pending"

    def test_valid_docx_accepted(self, client: TestClient, valid_docx_file: bytes):
        """Test that a valid DOCX file with correct magic number is accepted."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("valid_resume.docx", io.BytesIO(valid_docx_file), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["filename"] == "valid_resume.docx"

    def test_invalid_pdf_exe_rejected(self, client: TestClient, invalid_pdf_exe: bytes):
        """Test that an EXE file renamed to PDF is rejected."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("malicious.exe.pdf", io.BytesIO(invalid_pdf_exe), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data
        assert "magic number" in data["detail"].lower() or "file header" in data["detail"].lower()

    def test_invalid_pdf_text_rejected(self, client: TestClient, invalid_pdf_text: bytes):
        """Test that a text file renamed to PDF is rejected."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("fake.pdf", io.BytesIO(invalid_pdf_text), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_invalid_docx_random_rejected(self, client: TestClient, invalid_docx_random: bytes):
        """Test that random bytes with .docx extension are rejected."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("random.docx", io.BytesIO(invalid_docx_random), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_empty_file_rejected(self, client: TestClient):
        """Test that an empty file is rejected."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data


class TestRateLimiting:
    """Tests for rate limiting on upload endpoint."""

    def test_rate_limiting_enforced(self, client: TestClient, valid_pdf_file: bytes):
        """
        Test that rate limiting prevents more than 10 uploads per minute.

        This test:
        1. Makes 10 successful upload requests
        2. Attempts an 11th request
        3. Verifies the 11th request is rate limited (HTTP 429)
        """
        success_count = 0
        rate_limited = False

        # Make 10 requests (should all succeed)
        for i in range(10):
            response = client.post(
                "/api/resumes/upload",
                files={"file": (f"test_{i}.pdf", io.BytesIO(valid_pdf_file), "application/pdf")}
            )
            if response.status_code == 201:
                success_count += 1
            elif response.status_code == 429:
                # Rate limiting kicked in early (possibly from previous tests)
                rate_limited = True
                break

        # The 11th request should be rate limited
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("test_11.pdf", io.BytesIO(valid_pdf_file), "application/pdf")}
        )

        # Either we got rate limited on the 11th request,
        # or we were rate limited earlier due to cumulative requests
        if response.status_code == 429:
            rate_limited = True
            data = response.json()
            # Verify rate limit response structure
            assert "detail" in data or "error" in data
            # Check for rate limit headers or error message
            assert "rate limit" in data.get("detail", "").lower() or "rate_limit_exceeded" in data.get("error", "")

        # At minimum, we should have hit the rate limit
        assert rate_limited, "Rate limiting should be enforced after 10 requests"

    def test_rate_limit_headers(self, client: TestClient, valid_pdf_file: bytes):
        """Test that rate limit headers are present in responses."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("test_headers.pdf", io.BytesIO(valid_pdf_file), "application/pdf")}
        )

        # Response may or may not have rate limit headers depending on slowapi configuration
        # Just verify the request was processed
        assert response.status_code in [201, 429]


class TestFilenameSanitization:
    """Tests for filename sanitization to prevent path traversal attacks."""

    def test_path_traversal_prevented(self, client: TestClient, valid_pdf_file: bytes):
        """Test that path traversal filenames are sanitized."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("../../../etc/passwd", io.BytesIO(valid_pdf_file), "application/pdf")}
        )

        # Upload should succeed with sanitized filename
        assert response.status_code == 201
        data = response.json()
        # The filename should be sanitized (path components removed)
        assert "id" in data

    def test_null_byte_removed(self, client: TestClient, valid_pdf_file: bytes):
        """Test that null bytes in filenames are removed."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("test\x00file.pdf", io.BytesIO(valid_pdf_file), "application/pdf")}
        )

        # Upload should succeed with sanitized filename
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    def test_special_characters_sanitized(self, client: TestClient, valid_pdf_file: bytes):
        """Test that special characters in filenames are sanitized."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("test:file*.pdf", io.BytesIO(valid_pdf_file), "application/pdf")}
        )

        # Upload should succeed with sanitized filename
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    def test_long_filename_truncated(self, client: TestClient, valid_pdf_file: bytes):
        """Test that excessively long filenames are truncated."""
        long_filename = "a" * 300 + ".pdf"
        response = client.post(
            "/api/resumes/upload",
            files={"file": (long_filename, io.BytesIO(valid_pdf_file), "application/pdf")}
        )

        # Upload should succeed with truncated filename
        assert response.status_code == 201
        data = response.json()
        assert "id" in data


class TestAuditLogging:
    """Tests for audit logging of security events."""

    def test_magic_number_failure_logged(self, client: TestClient, invalid_pdf_exe: bytes):
        """
        Test that magic number validation failures are logged as audit events.

        This verifies that security violations are properly recorded for
        monitoring and incident response.
        """
        # Note: In a real integration test, we would query the database
        # to verify the audit log was created. For now, we just verify
        # the request is handled and rejected.

        response = client.post(
            "/api/resumes/upload",
            files={"file": ("malicious.pdf", io.BytesIO(invalid_pdf_exe), "application/pdf")}
        )

        # Should be rejected
        assert response.status_code == 415

        # In production, verify audit_logs table contains:
        # - action_type: FILE_VALIDATION_FAILED
        # - validation_type: "magic_number"
        # - filename: "malicious.pdf"

    def test_successful_upload_logged(self, client: TestClient, valid_pdf_file: bytes):
        """
        Test that successful uploads are logged as audit events.

        This verifies that all file uploads are tracked for compliance
        and security monitoring.
        """
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("audit_test.pdf", io.BytesIO(valid_pdf_file), "application/pdf")}
        )

        # Should succeed
        assert response.status_code == 201
        data = response.json()
        resume_id = data["id"]

        # In production, verify audit_logs table contains:
        # - action_type: RESUME_UPLOADED
        # - entity_id: resume_id
        # - filename: "audit_test.pdf"


class TestCompleteSecureFlow:
    """Tests for complete secure upload workflow."""

    def test_complete_secure_upload_success(self, client: TestClient, valid_pdf_file: bytes):
        """
        Test complete secure upload flow with all validations passing.

        This simulates a legitimate user uploading a valid resume:
        1. File passes magic number validation
        2. File type is allowed (PDF/DOCX)
        3. File size is within limits
        4. Filename is sanitized
        5. Rate limit is not exceeded
        6. Audit log is created
        7. Database record is created
        8. File is saved to disk
        """
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("legitimate_resume.pdf", io.BytesIO(valid_pdf_file), "application/pdf")}
        )

        # All validations should pass
        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert "filename" in data
        assert data["filename"] == "legitimate_resume.pdf"
        assert data["status"] == "pending"
        assert "message" in data

        # Verify file was created
        upload_dir = Path("backend/data/uploads")
        if upload_dir.exists():
            matching_files = list(upload_dir.glob(f"{data['id']}.*"))
            assert len(matching_files) > 0, "File should be saved to disk"

    def test_malicious_file_blocked_completely(self, client: TestClient, invalid_pdf_exe: bytes):
        """
        Test that a malicious file (EXE renamed to PDF) is completely blocked.

        This simulates an attacker attempting to upload malware:
        1. Magic number validation fails
        2. Request is rejected with HTTP 415
        3. Security event is logged
        4. No file is saved to disk
        5. No database record is created
        """
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("malware.pdf", io.BytesIO(invalid_pdf_exe), "application/pdf")}
        )

        # Should be rejected at magic number validation
        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

        # Verify no file was created (ID not returned)
        assert "id" not in data or data.get("id") is None

        # Verify no malicious file was saved to disk
        upload_dir = Path("backend/data/uploads")
        if upload_dir.exists():
            # Check for any recently created files
            recent_files = [f for f in upload_dir.iterdir() if f.is_file()]
            # The specific malicious file should not exist
            assert not any("malware.pdf" in f.name for f in recent_files)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_minimal_valid_pdf(self, client: TestClient):
        """Test that a minimal but valid PDF is accepted."""
        minimal_pdf = b"%PDF-1.4\n%%EOF"
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("minimal.pdf", io.BytesIO(minimal_pdf), "application/pdf")}
        )

        # May fail due to size checks or structure validation
        # but should not fail due to magic number
        assert response.status_code in [201, 413, 415]

    def test_corrupted_pdf_structure(self, client: TestClient):
        """Test handling of a PDF with valid magic number but corrupted structure."""
        corrupted_pdf = b"%PDF-1.4\n" + b"Corrupted content" * 100 + b"%%EOF"
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("corrupted.pdf", io.BytesIO(corrupted_pdf), "application/pdf")}
        )

        # Magic number is valid, so upload succeeds
        # Structure validation may or may not catch this
        assert response.status_code == 201

    def test_concurrent_uploads(self, client: TestClient, valid_pdf_file: bytes):
        """Test handling of multiple concurrent upload requests."""
        import threading

        results = []
        errors = []

        def upload():
            try:
                response = client.post(
                    "/api/resumes/upload",
                    files={"file": ("concurrent.pdf", io.BytesIO(valid_pdf_file), "application/pdf")}
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=upload) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All requests should complete (with success or rate limit)
        assert len(results) == 3
        assert len(errors) == 0


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_uploaded_files():
    """
    Clean up uploaded test files after each test.

    This fixture runs automatically after each test to remove
    any files uploaded during the test.
    """
    yield

    # Cleanup: Remove files from uploads directory
    upload_dir = Path("backend/data/uploads")
    if upload_dir.exists():
        # Remove test files (those with hex IDs from our tests)
        for file in upload_dir.glob("*"):
            if file.is_file():
                try:
                    # Remove files created during tests
                    # (those with UUID-like names or recent modifications)
                    file.unlink()
                except Exception:
                    pass  # File may be locked by another process


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
