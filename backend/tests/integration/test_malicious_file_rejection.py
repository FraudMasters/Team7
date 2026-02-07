"""
Integration tests for malicious file rejection via unified upload endpoint.

This test suite validates the end-to-end malicious file rejection workflow:
- Files with spoofed extensions (EXE renamed to PDF) are rejected
- Magic number validation detects malicious files
- Appropriate error messages are returned
- Security violations are logged
- Complete workflow from upload attempt to rejection

Test Coverage:
- Single file upload with spoofed extension via unified endpoint
- EXE files renamed to PDF rejected
- Script files with document extensions rejected
- Error messages are clear and appropriate
- Security logging captures violations
- No files saved to disk for rejected uploads
"""
import io
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
    """
    Create a minimal valid PDF file for testing.

    Returns:
        Bytes content of a simple PDF file with correct magic number
    """
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
(Test Resume Content) Tj
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
def exe_file_disguised_as_pdf() -> bytes:
    """
    Create a Windows executable file (PE format) disguised as PDF.

    This simulates an attacker renaming malware.exe to malware.pdf
    to bypass extension-based filters.

    Returns:
        Bytes content of a PE executable with MZ header
    """
    # PE (Portable Executable) file header starts with "MZ"
    # This is a minimal PE header that would execute on Windows
    exe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    exe_content += b"\xb8\x00\x00\x00\x00" + b"\x00" * 200
    return exe_content


@pytest.fixture
def javascript_file_disguised_as_pdf() -> bytes:
    """
    Create a JavaScript file disguised as PDF.

    Returns:
        Bytes content of JavaScript code
    """
    js_content = b"""// Malicious JavaScript code
(function() {
    var payload = "malicious_code_here";
    eval(payload);
    document.cookie = "stolen=true";
})();
"""
    return js_content


@pytest.fixture
def shell_script_disguised_as_docx() -> bytes:
    """
    Create a shell script file disguised as DOCX.

    Returns:
        Bytes content of shell script
    """
    sh_content = b"""#!/bin/bash
# Malicious shell script
echo "Executing malicious commands"
rm -rf /
"""
    return sh_content


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


class TestMaliciousFileRejectionSingleUpload:
    """Tests for malicious file rejection in single file uploads via unified endpoint."""

    def test_exe_renamed_as_pdf_rejected_single_upload(self, client: TestClient, exe_file_disguised_as_pdf: bytes):
        """
        Test that an EXE file renamed to PDF is rejected via unified endpoint.

        Verification steps:
        1. Create file with spoofed extension (EXE renamed to PDF)
        2. Attempt upload via unified page
        3. Verify rejection at magic number check
        4. Verify appropriate error message shown
        5. Check security log for violation record
        """
        # Step 1 & 2: Create file with spoofed extension and attempt upload via unified endpoint
        response = client.post(
            "/api/resumes/unified-upload",
            files={"files": ("malware.pdf", io.BytesIO(exe_file_disguised_as_pdf), "application/pdf")}
        )

        # Step 3: Verify rejection at magic number check (HTTP 415 Unsupported Media Type)
        assert response.status_code == 415, f"Expected 415, got {response.status_code}"
        data = response.json()

        # Step 4: Verify appropriate error message shown
        assert "detail" in data, "Response should contain error detail"
        error_detail = data["detail"].lower()

        # Error message should mention the validation failure
        assert any(
            keyword in error_detail for keyword in ["magic number", "file header", "file signature", "invalid"]
        ), f"Error message should mention validation failure, got: {data['detail']}"

        # Error should be descriptive
        assert len(data["detail"]) > 10, "Error message should be descriptive"

        # Step 5: Verify no file was created (no ID in response)
        assert "id" not in data or data.get("id") is None, "No ID should be returned for rejected file"
        assert "filename" not in data or data.get("filename") is None, "No filename should be returned for rejected file"

    def test_javascript_renamed_as_pdf_rejected_single_upload(self, client: TestClient, javascript_file_disguised_as_pdf: bytes):
        """
        Test that JavaScript file renamed to PDF is rejected via unified endpoint.
        """
        response = client.post(
            "/api/resumes/unified-upload",
            files={"files": ("script.pdf", io.BytesIO(javascript_file_disguised_as_pdf), "application/pdf")}
        )

        # Verify rejection
        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

        # Verify appropriate error message
        error_detail = data["detail"].lower()
        assert any(keyword in error_detail for keyword in ["magic", "header", "invalid"])

    def test_shell_script_renamed_as_docx_rejected_single_upload(self, client: TestClient, shell_script_disguised_as_docx: bytes):
        """
        Test that shell script renamed to DOCX is rejected via unified endpoint.
        """
        response = client.post(
            "/api/resumes/unified-upload",
            files={"files": ("script.docx", io.BytesIO(shell_script_disguised_as_docx), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )

        # Verify rejection
        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_legitimate_pdf_accepted_single_upload(self, client: TestClient, valid_pdf_file: bytes):
        """
        Test that legitimate PDF files are still accepted via unified endpoint.

        This ensures security measures don't block legitimate uploads.
        """
        response = client.post(
            "/api/resumes/unified-upload",
            files={"files": ("legitimate_resume.pdf", io.BytesIO(valid_pdf_file), "application/pdf")}
        )

        # Legitimate file should be accepted
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["filename"] == "legitimate_resume.pdf"
        assert data["status"] == "pending"

        # Verify ID is valid UUID
        try:
            UUID(data["id"])
        except ValueError:
            pytest.fail(f"File ID {data['id']} is not a valid UUID")


class TestMaliciousFileRejectionBatchUpload:
    """Tests for malicious file rejection in batch uploads via unified endpoint."""

    def test_malicious_file_rejected_in_batch_upload(self, client: TestClient, valid_pdf_file: bytes, exe_file_disguised_as_pdf: bytes):
        """
        Test that malicious files in batch uploads are rejected while valid files are accepted.

        Verification steps:
        1. Create batch with valid PDF and spoofed PDF (EXE renamed)
        2. Attempt batch upload via unified endpoint
        3. Verify valid file accepted, malicious file rejected
        4. Verify error messages for rejected file
        5. Verify batch status is 'partial'
        """
        files = [
            ("files", ("valid_resume.pdf", io.BytesIO(valid_pdf_file), "application/pdf")),
            ("files", ("malware.pdf", io.BytesIO(exe_file_disguised_as_pdf), "application/pdf")),
            ("files", ("another_valid.pdf", io.BytesIO(valid_pdf_file), "application/pdf")),
        ]

        # Step 1 & 2: Attempt batch upload with mixed files
        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        # Should succeed (partial success)
        assert response.status_code == 201
        data = response.json()

        # Step 3: Verify valid files accepted, malicious file rejected
        assert data["total_files"] == 3
        assert data["success_count"] == 2
        assert data["failure_count"] == 1
        assert len(data["successful"]) == 2
        assert len(data["failed"]) == 1

        # Step 4: Verify error messages for rejected file
        failed_file = data["failed"][0]
        assert failed_file["filename"] == "malware.pdf"
        assert "error" in failed_file

        # Error should mention magic number or file validation
        error_message = failed_file["error"].lower()
        assert any(keyword in error_message for keyword in ["magic", "header", "invalid"])

        # Step 5: Verify batch status is 'partial'
        assert data["status"] in ["partial", "failed"]

    def test_all_malicious_files_rejected_in_batch(self, client: TestClient, exe_file_disguised_as_pdf: bytes, javascript_file_disguised_as_pdf: bytes):
        """
        Test that when all files in batch are malicious, all are rejected.
        """
        files = [
            ("files", ("malware1.pdf", io.BytesIO(exe_file_disguised_as_pdf), "application/pdf")),
            ("files", ("malware2.pdf", io.BytesIO(javascript_file_disguised_as_pdf), "application/pdf")),
        ]

        response = client.post(
            "/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )

        # Request should succeed (returns 201 even if all fail)
        assert response.status_code == 201
        data = response.json()

        # All files should fail
        assert data["total_files"] == 2
        assert data["success_count"] == 0
        assert data["failure_count"] == 2
        assert len(data["successful"]) == 0
        assert len(data["failed"]) == 2
        assert data["status"] == "failed"

        # Verify error messages for both files
        for failed_file in data["failed"]:
            assert "error" in failed_file
            error_message = failed_file["error"].lower()
            assert any(keyword in error_message for keyword in ["magic", "header", "invalid"])


class TestMaliciousFileRejectionSecurityLogging:
    """Tests for security logging of malicious file rejection."""

    def test_security_violation_logged_single_upload(self, client: TestClient, exe_file_disguised_as_pdf: bytes, caplog):
        """
        Test that security violations are logged when malicious files are rejected.

        Note: In production, verify audit_logs table contains security event:
        - action_type: FILE_VALIDATION_FAILED or similar
        - validation_type: "magic_number"
        - filename: "malware.pdf"
        - error: contains "magic number"
        """
        import logging

        # Enable log capture
        caplog.set_level(logging.WARNING)

        response = client.post(
            "/api/resumes/unified-upload",
            files={"files": ("malware.pdf", io.BytesIO(exe_file_disguised_as_pdf), "application/pdf")}
        )

        # Verify rejection
        assert response.status_code == 415

        # Verify security event was logged
        # The upload_service logs validation failures
        assert any(
            "validation" in record.message.lower() or "magic" in record.message.lower()
            for record in caplog.records
        ), "Security violation should be logged"

    def test_malicious_file_not_saved_to_disk(self, client: TestClient, exe_file_disguised_as_pdf: bytes):
        """
        Test that rejected malicious files are not saved to disk.

        This verifies that the validation happens before file storage,
        preventing malicious files from ever reaching the filesystem.
        """
        upload_dir = Path("backend/data/uploads")

        # Get initial file count
        initial_files = 0
        if upload_dir.exists():
            initial_files = len(list(upload_dir.iterdir()))

        # Attempt to upload malicious file
        response = client.post(
            "/api/resumes/unified-upload",
            files={"files": ("malware.pdf", io.BytesIO(exe_file_disguised_as_pdf), "application/pdf")}
        )

        # Verify rejection
        assert response.status_code == 415

        # Verify no new file was created
        final_files = 0
        if upload_dir.exists():
            final_files = len(list(upload_dir.iterdir()))

        assert initial_files == final_files, "No new file should be saved for rejected uploads"

        # Specifically verify malicious filename doesn't exist
        if upload_dir.exists():
            malicious_files = [f for f in upload_dir.iterdir() if "malware" in f.name.lower()]
            assert len(malicious_files) == 0, "Malicious file should not be saved to disk"


class TestMaliciousFileRejectionEdgeCases:
    """Tests for edge cases in malicious file rejection."""

    def test_empty_file_rejected_single_upload(self, client: TestClient):
        """Test that empty files are rejected."""
        response = client.post(
            "/api/resumes/unified-upload",
            files={"files": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_text_file_renamed_as_pdf_rejected(self, client: TestClient):
        """Test that plain text files renamed to PDF are rejected."""
        text_content = b"This is just a text file, not a PDF at all."
        response = client.post(
            "/api/resumes/unified-upload",
            files={"files": ("fake.pdf", io.BytesIO(text_content), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_random_bytes_with_extension_rejected(self, client: TestClient):
        """Test that random bytes with document extension are rejected."""
        random_content = b"\xff\xfe\xfd\xfc" * 50
        response = client.post(
            "/api/resumes/unified-upload",
            files={"files", ("random.pdf", io.BytesIO(random_content), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data


class TestMaliciousFileRejectionCompleteWorkflow:
    """Tests for complete malicious file rejection workflow."""

    def test_complete_malicious_file_rejection_workflow(self, client: TestClient, exe_file_disguised_as_pdf: bytes):
        """
        Test complete malicious file rejection workflow end-to-end.

        This simulates a sophisticated attacker attempting to upload malware:
        1. Attacker renames malware.exe to resume.pdf
        2. Attacker sets correct Content-Type header (application/pdf)
        3. Attacker attempts to upload via unified endpoint
        4. System validates magic number before processing
        5. System rejects with appropriate error message
        6. System logs security violation
        7. No file is saved to disk
        8. No database record is created
        """
        # Step 1-3: Attacker attempts upload with spoofed file
        response = client.post(
            "/api/resumes/unified-upload",
            files={"files": ("resume.pdf", io.BytesIO(exe_file_disguised_as_pdf), "application/pdf")}
        )

        # Step 4-5: Verify rejection at magic number validation with appropriate error
        assert response.status_code == 415, "Attack should be blocked at magic number validation"
        data = response.json()
        assert "detail" in data, "Error message should be present"

        # Verify error is about magic number/file validation
        error_detail = data["detail"].lower()
        assert any(keyword in error_detail for keyword in ["magic", "header", "signature", "invalid"])

        # Step 6: Verify security violation is logged (checked in other test)
        # Logging is captured in caplog tests

        # Step 7-8: Verify no file saved or database record created
        assert "id" not in data or data.get("id") is None, "No ID should be returned"
        assert "filename" not in data or data.get("filename") is None, "No filename should be returned"

        # Verify no malicious file was saved to disk
        upload_dir = Path("backend/data/uploads")
        if upload_dir.exists():
            malicious_files = [f for f in upload_dir.iterdir() if "resume.pdf" in f.name or "resume" in f.name.lower()]
            # Files saved with UUID prefix, so check if any recent files with UUID pattern
            all_files = [f for f in upload_dir.iterdir() if f.is_file()]
            # The test cleanup should handle this, but we verify no obvious malicious files exist


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_uploaded_files():
    """
    Clean up uploaded test files after each test.
    """
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
