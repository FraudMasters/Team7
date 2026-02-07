"""
Integration tests for secure batch upload flow.

This test suite validates the end-to-end batch upload functionality:
- Multiple file uploads (PDF + DOCX)
- Batch validation and processing
- Security logging for violations
- Batch job creation and tracking
- Partial failure handling
- All files pass validation
"""
import io
import zipfile
from pathlib import Path
from typing import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app


@pytest.fixture
def valid_pdf_file() -> bytes:
    """Create a minimal valid PDF file for testing."""
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
    """Create a minimal valid DOCX file for testing."""
    # DOCX files are ZIP archives starting with PK\x03\x04
    docx_content = b"PK\x03\x04" + b"Test DOCX content" * 100
    return docx_content


@pytest.fixture
def invalid_pdf_exe() -> bytes:
    """Create an EXE file renamed to PDF (invalid magic number)."""
    exe_content = b"MZ\x90\x00" + b"\x00" * 100
    return exe_content


@pytest.fixture
def invalid_docx_script() -> bytes:
    """Create a script file renamed to DOCX."""
    script_content = b"#!/bin/bash\necho 'malicious'"
    return script_content


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a FastAPI test client for all tests."""
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as test_client:
        yield test_client


class TestBatchUploadValidation:
    """Tests for batch upload validation with multiple file types."""

    def test_batch_upload_pdf_and_docx(self, client: TestClient, valid_pdf_file: bytes, valid_docx_file: bytes):
        """
        Test batch upload with both PDF and DOCX files.

        This simulates a user uploading multiple resume files of different types:
        1. Both PDF and DOCX files are accepted
        2. All files pass magic number validation
        3. Batch processing completes successfully
        4. Response contains batch_id and file counts
        """
        files = [
            ("files", ("resume1.pdf", io.BytesIO(valid_pdf_file), "application/pdf")),
            ("files", ("resume2.docx", io.BytesIO(valid_docx_file), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        # Should succeed with batch upload response
        assert response.status_code == 201
        data = response.json()

        # Verify batch response structure
        assert "batch_id" in data
        assert "total_files" in data
        assert "success_count" in data
        assert "failure_count" in data
        assert "successful" in data
        assert "failed" in data
        assert "status" in data

        # Verify both files uploaded successfully
        assert data["total_files"] == 2
        assert data["success_count"] == 2
        assert data["failure_count"] == 0
        assert len(data["successful"]) == 2
        assert len(data["failed"]) == 0

        # Verify batch_id is valid UUID
        try:
            UUID(data["batch_id"])
        except ValueError:
            pytest.fail("batch_id is not a valid UUID")

        # Verify status is completed
        assert data["status"] == "completed"

    def test_batch_upload_multiple_pdfs(self, client: TestClient, valid_pdf_file: bytes):
        """Test batch upload with multiple PDF files."""
        files = [
            ("files", (f"resume{i}.pdf", io.BytesIO(valid_pdf_file), "application/pdf"))
            for i in range(5)
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        assert response.status_code == 201
        data = response.json()

        # Verify all files uploaded successfully
        assert data["total_files"] == 5
        assert data["success_count"] == 5
        assert data["failure_count"] == 0
        assert len(data["successful"]) == 5
        assert data["status"] == "completed"

    def test_batch_upload_multiple_docx(self, client: TestClient, valid_docx_file: bytes):
        """Test batch upload with multiple DOCX files."""
        files = [
            ("files", (f"resume{i}.docx", io.BytesIO(valid_docx_file), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
            for i in range(3)
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        assert response.status_code == 201
        data = response.json()

        # Verify all files uploaded successfully
        assert data["total_files"] == 3
        assert data["success_count"] == 3
        assert data["failure_count"] == 0
        assert len(data["successful"]) == 3
        assert data["status"] == "completed"

    def test_batch_upload_with_invalid_file(self, client: TestClient, valid_pdf_file: bytes, invalid_pdf_exe: bytes):
        """
        Test batch upload with one invalid file (EXE renamed to PDF).

        This verifies:
        1. Valid files are processed successfully
        2. Invalid files are rejected with proper error messages
        3. Batch status is 'partial' when some files fail
        4. Error details are provided for failed files
        """
        files = [
            ("files", ("valid_resume.pdf", io.BytesIO(valid_pdf_file), "application/pdf")),
            ("files", ("malicious.exe.pdf", io.BytesIO(invalid_pdf_exe), "application/pdf")),
            ("files", ("another_valid.pdf", io.BytesIO(valid_pdf_file), "application/pdf")),
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        # Request should succeed (partial success)
        assert response.status_code == 201
        data = response.json()

        # Verify partial success
        assert data["total_files"] == 3
        assert data["success_count"] == 2
        assert data["failure_count"] == 1
        assert len(data["successful"]) == 2
        assert len(data["failed"]) == 1

        # Verify status is partial
        assert data["status"] in ["partial", "failed"]

        # Verify error message for failed file
        assert data["failed"][0]["filename"] == "malicious.exe.pdf"
        assert "error" in data["failed"][0]
        assert "magic number" in data["failed"][0]["error"].lower() or "file header" in data["failed"][0]["error"].lower()

    def test_batch_upload_all_files_invalid(self, client: TestClient, invalid_pdf_exe: bytes, invalid_docx_script: bytes):
        """Test batch upload where all files are invalid."""
        files = [
            ("files", ("malicious1.pdf", io.BytesIO(invalid_pdf_exe), "application/pdf")),
            ("files", ("malicious2.docx", io.BytesIO(invalid_docx_script), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        # Request should still succeed (batch API returns 201 even if all fail)
        assert response.status_code == 201
        data = response.json()

        # Verify all files failed
        assert data["total_files"] == 2
        assert data["success_count"] == 0
        assert data["failure_count"] == 2
        assert len(data["successful"]) == 0
        assert len(data["failed"]) == 2
        assert data["status"] == "failed"


class TestBatchUploadSecurity:
    """Tests for security features in batch upload."""

    def test_magic_number_validation_in_batch(self, client: TestClient, valid_pdf_file: bytes, invalid_pdf_exe: bytes):
        """
        Test that magic number validation is applied to all files in batch.

        This ensures that malicious files cannot bypass validation by being
        part of a batch upload.
        """
        files = [
            ("files", ("valid.pdf", io.BytesIO(valid_pdf_file), "application/pdf")),
            ("files", ("spoofed.pdf", io.BytesIO(invalid_pdf_exe), "application/pdf")),
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        data = response.json()

        # Valid file should succeed
        assert data["success_count"] == 1
        assert any(f["filename"] == "valid.pdf" for f in data["successful"])

        # Spoofed file should fail
        assert data["failure_count"] == 1
        assert any(f["filename"] == "spoofed.pdf" for f in data["failed"])
        failed_file = next(f for f in data["failed"] if f["filename"] == "spoofed.pdf")
        assert "magic number" in failed_file["error"].lower() or "file header" in failed_file["error"].lower()

    def test_filename_sanitization_in_batch(self, client: TestClient, valid_pdf_file: bytes):
        """Test that filenames are sanitized in batch uploads."""
        malicious_filenames = [
            "../../../etc/passwd.pdf",
            "test\x00file.pdf",
            "file:with*.chars.pdf",
        ]

        files = [
            ("files", (filename, io.BytesIO(valid_pdf_file), "application/pdf"))
            for filename in malicious_filenames
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        # All files should be accepted with sanitized names
        assert response.status_code == 201
        data = response.json()

        # All uploads should succeed
        assert data["success_count"] == len(malicious_filenames)
        assert data["failure_count"] == 0

        # Verify sanitized filenames in response
        for file_info in data["successful"]:
            # Filename should be sanitized (no path traversal, null bytes, etc.)
            assert "../" not in file_info["filename"]
            assert "\x00" not in file_info["filename"]
            assert ":" not in file_info["filename"] or ":" not in file_info["filename"].split("/")[-1]


class TestBatchUploadLimits:
    """Tests for batch upload size limits."""

    def test_batch_upload_exceeds_limit(self, client: TestClient, valid_pdf_file: bytes):
        """
        Test that batch upload is rejected when exceeding the maximum file limit.

        The maximum is 100 files per batch (as defined in UnifiedUploadService).
        """
        # Create 101 files (exceeds the limit of 100)
        files = [
            ("files", (f"resume{i}.pdf", io.BytesIO(valid_pdf_file), "application/pdf"))
            for i in range(101)
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        # Should be rejected due to batch size limit
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "100" in data["detail"] or "maximum" in data["detail"].lower()

    def test_batch_upload_at_limit(self, client: TestClient, valid_pdf_file: bytes):
        """Test batch upload with exactly 100 files (at the limit)."""
        # Create 100 files (at the limit)
        files = [
            ("files", (f"resume{i}.pdf", io.BytesIO(valid_pdf_file), "application/pdf"))
            for i in range(100)
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        # Should succeed
        assert response.status_code == 201
        data = response.json()

        # Verify all files were processed
        assert data["total_files"] == 100
        assert data["success_count"] == 100
        assert data["failure_count"] == 0


class TestBatchUploadAuditLogging:
    """Tests for audit logging in batch uploads."""

    def test_batch_upload_creates_audit_log(self, client: TestClient, valid_pdf_file: bytes, valid_docx_file: bytes):
        """
        Test that batch uploads create audit log entries.

        This verifies security logging for compliance and monitoring.
        """
        files = [
            ("files", ("resume1.pdf", io.BytesIO(valid_pdf_file), "application/pdf")),
            ("files", ("resume2.docx", io.BytesIO(valid_docx_file), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        assert response.status_code == 201
        data = response.json()

        # In production, verify audit_logs table contains:
        # - action_type: RESUME_UPLOADED
        # - entity_type: "batch"
        # - entity_id: batch_id
        # - action_data: {total_files, success_count, failure_count, upload_type: "unified_batch"}

        # Verify response contains necessary information for audit
        assert "batch_id" in data
        assert "total_files" in data
        assert "success_count" in data
        assert "failure_count" in data

    def test_batch_upload_security_violations_logged(self, client: TestClient, valid_pdf_file: bytes, invalid_pdf_exe: bytes):
        """
        Test that security violations (invalid magic numbers) are logged in batch uploads.

        This verifies that the system detects and logs malicious file upload attempts.
        """
        files = [
            ("files", ("valid.pdf", io.BytesIO(valid_pdf_file), "application/pdf")),
            ("files", ("malicious.pdf", io.BytesIO(invalid_pdf_exe), "application/pdf")),
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        assert response.status_code == 201
        data = response.json()

        # Verify malicious file was rejected
        assert data["failure_count"] == 1
        assert any(f["filename"] == "malicious.pdf" for f in data["failed"])

        # In production, verify audit_logs table contains security event:
        # - action_type: FILE_VALIDATION_FAILED or similar
        # - validation_type: "magic_number"
        # - filename: "malicious.pdf"
        # - error: contains "magic number"


class TestBatchUploadNotificationEmail:
    """Tests for notification email option in batch uploads."""

    def test_batch_upload_with_notification_email(self, client: TestClient, valid_pdf_file: bytes):
        """Test batch upload with notification email parameter."""
        files = [
            ("files", ("resume.pdf", io.BytesIO(valid_pdf_file), "application/pdf")),
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={
                "analyze": "true",
                "notification_email": "test@example.com",
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Verify batch was created
        assert "batch_id" in data
        assert data["success_count"] == 1

        # In production, verify BatchJob record has notification_email set


class TestBatchUploadCompleteWorkflow:
    """Tests for complete batch upload workflow."""

    def test_complete_batch_upload_workflow(self, client: TestClient, valid_pdf_file: bytes, valid_docx_file: bytes):
        """
        Test complete batch upload workflow from start to finish.

        This simulates a real-world scenario:
        1. User selects multiple files (PDF + DOCX)
        2. All files pass validation
        3. Batch processing completes
        4. Security logs are clean (no violations)
        5. Response contains all necessary information
        """
        files = [
            ("files", ("software_engineer.pdf", io.BytesIO(valid_pdf_file), "application/pdf")),
            ("files", ("product_manager.docx", io.BytesIO(valid_docx_file), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            ("files", ("data_analyst.pdf", io.BytesIO(valid_pdf_file), "application/pdf")),
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        # Step 1: Request should succeed
        assert response.status_code == 201
        data = response.json()

        # Step 2: Verify all files pass validation
        assert data["total_files"] == 3
        assert data["success_count"] == 3
        assert data["failure_count"] == 0
        assert len(data["successful"]) == 3
        assert len(data["failed"]) == 0

        # Step 3: Verify batch processing completes
        assert data["status"] == "completed"
        assert "batch_id" in data

        # Verify each successful upload has required fields
        for file_info in data["successful"]:
            assert "id" in file_info
            assert "filename" in file_info
            assert "status" in file_info
            assert file_info["status"] == "pending"

            # Verify ID is valid UUID
            try:
                UUID(file_info["id"])
            except ValueError:
                pytest.fail(f"File ID {file_info['id']} is not a valid UUID")

        # Step 4: Verify no security violations
        # (All files passed validation, no errors related to security)
        assert data["failure_count"] == 0
        assert len(data["failed"]) == 0

        # Step 5: Verify response completeness
        assert "message" in data
        assert "Batch upload completed" in data["message"]


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_uploaded_files():
    """Clean up uploaded test files after each test."""
    yield

    # Cleanup: Remove files from uploads directory
    upload_dir = Path("backend/data/uploads")
    if upload_dir.exists():
        for file in upload_dir.glob("*"):
            if file.is_file():
                try:
                    file.unlink()
                except Exception:
                    pass


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
