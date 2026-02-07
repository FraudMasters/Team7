"""
Manual endpoint verification script for refactored resume endpoints.

This script tests each resume endpoint individually to confirm responses
match original behavior after the refactoring from monolithic resumes.py
to modular structure (upload.py, listing.py, analysis.py, management.py).

Usage:
    cd backend
    python test_resume_endpoints_verification.py

Expected behavior:
    - All endpoints should respond correctly
    - Responses should match the expected structure
    - Status codes should be as documented
"""
import asyncio
import io
import sys
from pathlib import Path
from typing import Any, Dict

import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from fastapi.testclient import TestClient


def create_test_pdf() -> bytes:
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


class EndpointTester:
    """Test suite for resume endpoints verification."""

    def __init__(self):
        self.client = TestClient(app)
        self.test_results = []
        self.uploaded_resume_id = None

    def print_section(self, title: str):
        """Print a section header."""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")

    def print_test(self, test_name: str):
        """Print a test name."""
        print(f"Testing: {test_name}...")

    def print_result(self, success: bool, message: str):
        """Print test result."""
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {message}")
        self.test_results.append((success, message))

    def test_1_upload_pdf(self) -> bool:
        """Test 1: POST /api/resumes/upload - Upload a test PDF file."""
        self.print_test("POST /api/resumes/upload with PDF file")

        try:
            pdf_content = create_test_pdf()
            response = self.client.post(
                "/api/resumes/upload",
                files={"file": ("test_resume.pdf", io.BytesIO(pdf_content), "application/pdf")}
            )

            # Check status code
            if response.status_code != 201:
                self.print_result(False, f"Expected status 201, got {response.status_code}")
                return False

            # Check response structure
            data = response.json()
            required_fields = ["id", "filename", "status", "message"]
            missing_fields = [f for f in required_fields if f not in data]

            if missing_fields:
                self.print_result(False, f"Missing fields: {missing_fields}")
                return False

            # Check values
            if data["filename"] != "test_resume.pdf":
                self.print_result(False, f"Expected filename 'test_resume.pdf', got '{data['filename']}'")
                return False

            if data["status"] != "pending":
                self.print_result(False, f"Expected status 'pending', got '{data['status']}'")
                return False

            # Store ID for subsequent tests
            self.uploaded_resume_id = data["id"]

            # Check file was saved
            upload_dir = Path("data/uploads")
            if not upload_dir.exists():
                self.print_result(False, "Upload directory does not exist")
                return False

            matching_files = list(upload_dir.glob(f"{data['id']}.*"))
            if not matching_files:
                self.print_result(False, f"File not found in uploads directory with ID {data['id']}")
                return False

            self.print_result(True, f"PDF uploaded successfully (ID: {data['id']})")
            return True

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")
            return False

    def test_2_upload_unsupported_type(self) -> bool:
        """Test 2: POST /api/resumes/upload - Reject unsupported file type."""
        self.print_test("POST /api/resumes/upload with unsupported file type")

        try:
            response = self.client.post(
                "/api/resumes/upload",
                files={"file": ("test.txt", io.BytesIO(b"Plain text content"), "text/plain")}
            )

            # Should return 415 Unsupported Media Type
            if response.status_code != 415:
                self.print_result(False, f"Expected status 415, got {response.status_code}")
                return False

            data = response.json()
            if "detail" not in data:
                self.print_result(False, "Response missing 'detail' field")
                return False

            self.print_result(True, f"Correctly rejected unsupported file type: {data['detail'][:50]}...")
            return True

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")
            return False

    def test_3_list_resumes(self) -> bool:
        """Test 3: GET /api/resumes/ - List all resumes."""
        self.print_test("GET /api/resumes/ - List resumes")

        try:
            response = self.client.get("/api/resumes/")

            # Check status code
            if response.status_code != 200:
                self.print_result(False, f"Expected status 200, got {response.status_code}")
                return False

            # Check response structure
            data = response.json()
            if not isinstance(data, list):
                self.print_result(False, f"Expected list, got {type(data)}")
                return False

            # Check that our uploaded resume is in the list
            if self.uploaded_resume_id:
                found = any(resume.get("id") == self.uploaded_resume_id for resume in data)
                if not found:
                    self.print_result(False, f"Uploaded resume {self.uploaded_resume_id} not found in list")
                    return False

            # Check structure of first resume (if any)
            if data:
                resume = data[0]
                expected_fields = ["id", "filename", "status", "created_at"]
                missing_fields = [f for f in expected_fields if f not in resume]

                if missing_fields:
                    self.print_result(False, f"Resume missing fields: {missing_fields}")
                    return False

            self.print_result(True, f"Listed {len(data)} resume(s) successfully")
            return True

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")
            return False

    def test_4_get_resume_analysis(self) -> bool:
        """Test 4: GET /api/resumes/{id} - Get resume with analysis."""
        self.print_test(f"GET /api/resumes/{{id}} - Get resume analysis")

        if not self.uploaded_resume_id:
            self.print_result(False, "No resume ID available (upload test failed)")
            return False

        try:
            response = self.client.get(f"/api/resumes/{self.uploaded_resume_id}")

            # Check status code (should be 200 with placeholder data)
            if response.status_code != 200:
                self.print_result(False, f"Expected status 200, got {response.status_code}")
                return False

            # Check response structure
            data = response.json()
            expected_fields = ["resume_id", "status", "errors", "grammar_errors",
                             "keywords", "technical_skills"]
            missing_fields = [f for f in expected_fields if f not in data]

            if missing_fields:
                self.print_result(False, f"Response missing fields: {missing_fields}")
                return False

            # Check that resume_id matches
            if data["resume_id"] != self.uploaded_resume_id:
                self.print_result(False, f"resume_id mismatch: expected {self.uploaded_resume_id}, got {data['resume_id']}")
                return False

            self.print_result(True, f"Retrieved resume analysis (status: {data['status']})")
            return True

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")
            return False

    def test_5_get_nonexistent_resume(self) -> bool:
        """Test 5: GET /api/resumes/{id} - Get non-existent resume."""
        self.print_test("GET /api/resumes/{id} - Non-existent resume")

        try:
            fake_id = "00000000-0000-0000-0000-000000000000"
            response = self.client.get(f"/api/resumes/{fake_id}")

            # Should return 200 with placeholder data (DB integration pending)
            # or 404 if fully implemented
            if response.status_code not in [200, 404]:
                self.print_result(False, f"Unexpected status code: {response.status_code}")
                return False

            self.print_result(True, f"Handled non-existent resume correctly (status {response.status_code})")
            return True

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")
            return False

    def test_6_update_resume_status(self) -> bool:
        """Test 6: PATCH /api/resumes/{id} - Update resume status."""
        self.print_test("PATCH /api/resumes/{id} - Update status")

        if not self.uploaded_resume_id:
            self.print_result(False, "No resume ID available (upload test failed)")
            return False

        try:
            # Update status to "reviewed"
            response = self.client.patch(
                f"/api/resumes/{self.uploaded_resume_id}",
                json={"status": "reviewed"}
            )

            # Check status code
            if response.status_code != 200:
                self.print_result(False, f"Expected status 200, got {response.status_code}")
                return False

            # Check response structure
            data = response.json()
            required_fields = ["id", "status", "filename"]
            missing_fields = [f for f in required_fields if f not in data]

            if missing_fields:
                self.print_result(False, f"Missing fields: {missing_fields}")
                return False

            # Check that status was updated
            if data["status"] != "reviewed":
                self.print_result(False, f"Expected status 'reviewed', got '{data['status']}'")
                return False

            # Check that ID matches
            if data["id"] != self.uploaded_resume_id:
                self.print_result(False, f"ID mismatch: expected {self.uploaded_resume_id}, got {data['id']}")
                return False

            self.print_result(True, f"Updated resume status to 'reviewed'")
            return True

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")
            return False

    def test_7_update_invalid_status(self) -> bool:
        """Test 7: PATCH /api/resumes/{id} - Try invalid status."""
        self.print_test("PATCH /api/resumes/{id} - Invalid status")

        if not self.uploaded_resume_id:
            self.print_result(False, "No resume ID available (upload test failed)")
            return False

        try:
            # Try to update with invalid status
            response = self.client.patch(
                f"/api/resumes/{self.uploaded_resume_id}",
                json={"status": "invalid_status"}
            )

            # Should return 422 Unprocessable Entity
            if response.status_code != 422:
                self.print_result(False, f"Expected status 422, got {response.status_code}")
                return False

            self.print_result(True, "Correctly rejected invalid status")
            return True

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")
            return False

    def test_8_delete_resume(self) -> bool:
        """Test 8: DELETE /api/resumes/{id} - Delete resume."""
        self.print_test("DELETE /api/resumes/{id} - Delete resume")

        if not self.uploaded_resume_id:
            self.print_result(False, "No resume ID available (upload test failed)")
            return False

        try:
            # Delete the resume
            response = self.client.delete(f"/api/resumes/{self.uploaded_resume_id}")

            # Check status code (should be 204 No Content)
            if response.status_code != 204:
                self.print_result(False, f"Expected status 204, got {response.status_code}")
                return False

            # Verify it's deleted by trying to get it again
            get_response = self.client.get(f"/api/resumes/{self.uploaded_resume_id}")
            # Should return 404 or 200 with empty/placeholder data
            if get_response.status_code == 200:
                # If still returns 200, check if it's placeholder
                data = get_response.json()
                if data.get("resume_id") == self.uploaded_resume_id:
                    self.print_result(False, "Resume still accessible after deletion")
                    return False

            self.print_result(True, f"Deleted resume {self.uploaded_resume_id}")
            return True

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")
            return False

    def test_9_delete_nonexistent_resume(self) -> bool:
        """Test 9: DELETE /api/resumes/{id} - Delete non-existent resume."""
        self.print_test("DELETE /api/resumes/{id} - Non-existent resume")

        try:
            fake_id = "00000000-0000-0000-0000-000000000000"
            response = self.client.delete(f"/api/resumes/{fake_id}")

            # Should return 404 or 204 (idempotent deletion)
            if response.status_code not in [204, 404]:
                self.print_result(False, f"Unexpected status code: {response.status_code}")
                return False

            self.print_result(True, f"Handled deletion of non-existent resume (status {response.status_code})")
            return True

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all endpoint tests."""
        self.print_section("RESUME ENDPOINTS VERIFICATION")
        print("Testing refactored resume endpoints after modular refactoring")
        print(f"Base URL: http://localhost:8000")
        print(f"Endpoints to test:")
        print(f"  - POST   /api/resumes/upload (upload.py)")
        print(f"  - GET    /api/resumes/ (listing.py)")
        print(f"  - GET    /api/resumes/{{id}} (analysis.py)")
        print(f"  - PATCH  /api/resumes/{{id}} (management.py)")
        print(f"  - DELETE /api/resumes/{{id}} (management.py)")

        # Test Suite 1: Upload Endpoints
        self.print_section("TEST SUITE 1: UPLOAD ENDPOINTS (upload.py)")
        self.test_1_upload_pdf()
        self.test_2_upload_unsupported_type()

        # Test Suite 2: Listing Endpoints
        self.print_section("TEST SUITE 2: LISTING ENDPOINTS (listing.py)")
        self.test_3_list_resumes()

        # Test Suite 3: Analysis Endpoints
        self.print_section("TEST SUITE 3: ANALYSIS ENDPOINTS (analysis.py)")
        self.test_4_get_resume_analysis()
        self.test_5_get_nonexistent_resume()

        # Test Suite 4: Management Endpoints
        self.print_section("TEST SUITE 4: MANAGEMENT ENDPOINTS (management.py)")
        self.test_6_update_resume_status()
        self.test_7_update_invalid_status()
        self.test_8_delete_resume()
        self.test_9_delete_nonexistent_resume()

        # Print summary
        self.print_section("TEST SUMMARY")
        passed = sum(1 for success, _ in self.test_results if success)
        failed = sum(1 for success, _ in self.test_results if not success)
        total = len(self.test_results)

        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {passed/total*100:.1f}%")

        if failed > 0:
            print(f"\nFailed tests:")
            for success, message in self.test_results:
                if not success:
                    print(f"  - {message}")

        print(f"\n{'='*60}")
        if failed == 0:
            print("✓ ALL TESTS PASSED - Refactoring successful!")
        else:
            print(f"✗ {failed} TEST(S) FAILED - Please review")
        print(f"{'='*60}\n")

        return failed == 0


def main():
    """Run the endpoint verification tests."""
    tester = EndpointTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
