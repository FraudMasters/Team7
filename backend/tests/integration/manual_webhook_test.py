#!/usr/bin/env python3
"""
Manual webhook endpoint test script.

This script can be run directly to verify the webhook endpoint
without requiring pytest or other test infrastructure.

Usage:
    python backend/tests/integration/manual_webhook_test.py
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any
import urllib.request
import urllib.error


# Configuration
API_URL = "http://localhost:8000/api/webhooks/resume"


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    symbol = "✓" if passed else "✗"
    print(f"\n{symbol} {test_name}")
    if details:
        print(f"  {details}")


def send_webhook_request(payload: Dict[Any, Any]) -> tuple[bool, int, str]:
    """
    Send a POST request to the webhook endpoint.

    Args:
        payload: JSON payload to send

    Returns:
        Tuple of (success, status_code, response_text)
    """
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            API_URL,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            return True, response.status, response.read().decode('utf-8')

    except urllib.error.HTTPError as e:
        return False, e.code, e.read().decode('utf-8')
    except urllib.error.URLError as e:
        return False, 0, f"Connection error: {e.reason}"
    except Exception as e:
        return False, 0, f"Error: {str(e)}"


def test_1_minimal_payload():
    """Test 1: Minimal valid payload."""
    print_section("Test 1: Minimal Valid Payload")

    payload = {
        "source": "test",
        "candidate_name": "Jane Smith"
    }

    success, status_code, response = send_webhook_request(payload)

    if success and status_code == 201:
        try:
            data = json.loads(response)
            has_id = "id" in data
            has_status = data.get("status") == "pending"
            has_source = data.get("source") == "test"

            if has_id and has_status and has_source:
                print_result("Minimal payload", True, f"Resume ID: {data['id']}")
                return True, data.get('id')
            else:
                print_result("Minimal payload", False, f"Response: {response}")
                return False, None
        except json.JSONDecodeError:
            print_result("Minimal payload", False, f"Invalid JSON response: {response}")
            return False, None
    else:
        print_result("Minimal payload", False, f"Status: {status_code}, Response: {response}")
        return False, None


def test_2_full_payload():
    """Test 2: Full payload with all fields."""
    print_section("Test 2: Full Payload")

    payload = {
        "source": "indeed",
        "resume_url": "https://example.com/resumes/john_doe.pdf",
        "candidate_name": "John Doe",
        "candidate_email": "john.doe@example.com",
        "candidate_phone": "+1-555-0123-4567",
        "job_id": "job-12345",
        "metadata": {
            "external_id": "ext-67890",
            "applied_date": "2026-02-03"
        }
    }

    success, status_code, response = send_webhook_request(payload)

    if success and status_code == 201:
        try:
            data = json.loads(response)
            has_id = "id" in data
            has_status = data.get("status") == "pending"
            has_source = data.get("source") == "indeed"

            if has_id and has_status and has_source:
                print_result("Full payload", True, f"Resume ID: {data['id']}")
                return True, data.get('id')
            else:
                print_result("Full payload", False, f"Response: {response}")
                return False, None
        except json.JSONDecodeError:
            print_result("Full payload", False, f"Invalid JSON response: {response}")
            return False, None
    else:
        print_result("Full payload", False, f"Status: {status_code}, Response: {response}")
        return False, None


def test_3_empty_source():
    """Test 3: Empty source field (should fail)."""
    print_section("Test 3: Empty Source Validation")

    payload = {
        "source": "   ",  # Whitespace only
        "candidate_name": "Test"
    }

    success, status_code, response = send_webhook_request(payload)

    # Should return 400 Bad Request
    if not success and status_code == 400:
        print_result("Empty source rejection", True, "Correctly rejected with 400")
        return True
    else:
        print_result("Empty source rejection", False,
                    f"Expected 400, got {status_code}. Response: {response}")
        return False


def test_4_missing_source():
    """Test 4: Missing source field (should fail)."""
    print_section("Test 4: Missing Source Validation")

    payload = {
        "candidate_name": "Test",
        "candidate_email": "test@example.com"
    }

    success, status_code, response = send_webhook_request(payload)

    # Should return 422 Unprocessable Entity
    if not success and status_code == 422:
        print_result("Missing source rejection", True, "Correctly rejected with 422")
        return True
    else:
        print_result("Missing source rejection", False,
                    f"Expected 422, got {status_code}. Response: {response}")
        return False


def test_5_invalid_url():
    """Test 5: Invalid URL format (should fail)."""
    print_section("Test 5: Invalid URL Validation")

    payload = {
        "source": "test",
        "resume_url": "not-a-valid-url",
        "candidate_name": "Test"
    }

    success, status_code, response = send_webhook_request(payload)

    # Should return 422 Unprocessable Entity
    if not success and status_code == 422:
        print_result("Invalid URL rejection", True, "Correctly rejected with 422")
        return True
    else:
        print_result("Invalid URL rejection", False,
                    f"Expected 422, got {status_code}. Response: {response}")
        return False


def print_database_instructions(resume_ids: list):
    """Print instructions for manual database verification."""
    print_section("Database Verification Instructions")

    print("\nTo verify resumes were stored in the database:")
    print("\n1. Using psql:")
    print(f"   psql -U agenthr -d agenthr -c \"SELECT id, filename, status FROM resumes WHERE filename LIKE 'webhook_%' ORDER BY created_at DESC LIMIT 5;\"")

    print("\n2. Check specific resume:")
    if resume_ids:
        for rid in resume_ids:
            print(f"   psql -U agenthr -d agenthr -c \"SELECT * FROM resumes WHERE id = '{rid}';\"")

    print("\n3. Check audit logs:")
    print("   psql -U agenthr -d agenthr -c \"SELECT * FROM audit_logs WHERE action_type = 'resume_uploaded' ORDER BY created_at DESC LIMIT 5;\"")

    print("\n4. Expected results:")
    print("   - Resume records with filenames like 'webhook_indeed_<uuid>'")
    print("   - Status should be 'PENDING'")
    print("   - raw_text should contain candidate information")
    print("   - Audit logs should have 'webhook': true in action_data")


def main():
    """Run all tests."""
    print_section("Webhook Endpoint Manual Test")

    print(f"\nTesting endpoint: {API_URL}")
    print("\nNote: Backend server must be running on http://localhost:8000")
    print("      Start with: cd backend && uvicorn main:app --reload")

    # Run tests
    results = []
    resume_ids = []

    success, resume_id = test_1_minimal_payload()
    results.append(("Minimal payload", success))
    if resume_id:
        resume_ids.append(resume_id)

    success, resume_id = test_2_full_payload()
    results.append(("Full payload", success))
    if resume_id:
        resume_ids.append(resume_id)

    results.append(("Empty source validation", test_3_empty_source()))
    results.append(("Missing source validation", test_4_missing_source()))
    results.append(("Invalid URL validation", test_5_invalid_url()))

    # Print summary
    print_section("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    # Print database verification instructions
    print_database_instructions(resume_ids)

    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
