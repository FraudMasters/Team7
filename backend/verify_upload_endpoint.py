#!/usr/bin/env python3
"""
Verification script for resume upload endpoint.

This script tests the resume upload endpoint to ensure:
1. Endpoint accepts POST requests
2. File validation works (type, size)
3. Returns 201 status on success
4. Returns appropriate error codes on validation failure
"""
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests

    API_URL = "http://localhost:8000/api/resumes/upload"

    def create_test_pdf(filename: str) -> None:
        """Create a minimal PDF file for testing."""
        # Minimal PDF header
        pdf_header = b"%PDF-1.4\n"
        pdf_body = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        pdf_trailer = b"%%EOF\n"

        with open(filename, "wb") as f:
            f.write(pdf_header + pdf_body + pdf_trailer)

    def test_upload_success():
        """Test successful file upload."""
        print("Test 1: Successful PDF upload")

        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            create_test_pdf(tmp.name)
            tmp_filename = tmp.name

        try:
            with open(tmp_filename, "rb") as f:
                files = {"file": ("test.pdf", f, "application/pdf")}
                response = requests.post(API_URL, files=files, timeout=5)

            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.json()}")

            if response.status_code == 201:
                print("  ✓ PASS: Returns 201 status on successful upload")
                return True
            else:
                print(f"  ✗ FAIL: Expected 201, got {response.status_code}")
                return False
        finally:
            os.unlink(tmp_filename)

    def test_invalid_file_type():
        """Test rejection of invalid file type."""
        print("\nTest 2: Invalid file type rejection")

        # Create a temporary text file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"This is not a PDF or DOCX file")
            tmp_filename = tmp.name

        try:
            with open(tmp_filename, "rb") as f:
                files = {"file": ("test.txt", f, "text/plain")}
                response = requests.post(API_URL, files=files, timeout=5)

            print(f"  Status Code: {response.status_code}")

            if response.status_code == 415:
                print("  ✓ PASS: Returns 415 for unsupported file type")
                return True
            else:
                print(f"  ✗ FAIL: Expected 415, got {response.status_code}")
                return False
        finally:
            os.unlink(tmp_filename)

    def test_file_too_large():
        """Test rejection of file that exceeds size limit."""
        print("\nTest 3: File size limit enforcement")

        # Create a large file (> 10MB default limit)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            # Write 11MB of data
            tmp.write(b"%PDF-1.4\n" + b"0" * (11 * 1024 * 1024))
            tmp_filename = tmp.name

        try:
            with open(tmp_filename, "rb") as f:
                files = {"file": ("large.pdf", f, "application/pdf")}
                response = requests.post(API_URL, files=files, timeout=10)

            print(f"  Status Code: {response.status_code}")

            if response.status_code == 413:
                print("  ✓ PASS: Returns 413 for file exceeding size limit")
                return True
            else:
                print(f"  ✗ FAIL: Expected 413, got {response.status_code}")
                return False
        finally:
            os.unlink(tmp_filename)

    def main():
        """Run all tests."""
        print("=" * 60)
        print("Resume Upload Endpoint Verification")
        print("=" * 60)

        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code != 200:
                print("\n✗ ERROR: Server health check failed")
                sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"\n✗ ERROR: Cannot connect to server: {e}")
            print("\nPlease start the server first:")
            print("  cd backend")
            print("  python -m uvicorn main:app --reload --port 8000")
            sys.exit(1)

        # Run tests
        results = []
        results.append(test_upload_success())
        results.append(test_invalid_file_type())
        results.append(test_file_too_large())

        # Summary
        print("\n" + "=" * 60)
        passed = sum(results)
        total = len(results)
        print(f"Results: {passed}/{total} tests passed")
        print("=" * 60)

        if all(results):
            print("\n✓ All tests PASSED")
            sys.exit(0)
        else:
            print("\n✗ Some tests FAILED")
            sys.exit(1)

    if __name__ == "__main__":
        main()

except ImportError:
    print("Note: requests library not installed. Install with:")
    print("  pip install requests")
    print("\nOr test manually with curl:")
    print("  # Create a test PDF")
    print('  echo \'%PDF-1.4\\n%%EOF\' > test.pdf')
    print("  # Upload the file")
    print("  curl -X POST http://localhost:8000/api/resumes/upload -F 'file=@test.pdf'")
    sys.exit(1)
