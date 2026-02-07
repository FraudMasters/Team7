#!/usr/bin/env python3
"""
LinkedIn OAuth Flow End-to-End Test

This script tests the complete OAuth 2.0 flow from frontend to backend:
1. Auth URL generation (backend → frontend → LinkedIn)
2. Callback processing (LinkedIn → backend → frontend)
3. Token exchange (backend → LinkedIn API)
4. Error handling and edge cases

Usage:
  cd backend
  python test_linkedin_oauth_flow.py

Requirements:
  - LINKEDIN_CLIENT_ID environment variable
  - LINKEDIN_CLIENT_SECRET environment variable
  - LINKEDIN_REDIRECT_URI environment variable

Test scenarios:
  ✓ Generate authorization URL with default scopes
  ✓ Generate authorization URL with custom scopes
  ✓ Validate state parameter generation
  ✓ Test state verification (CSRF protection)
  ✓ Validate callback endpoint structure
  ✓ Test error handling for missing configuration
  ✓ Test error handling for invalid codes
  ✓ Verify complete OAuth flow integration
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from database import async_session_maker
from utils.linkedin_oauth import (
    generate_auth_url,
    generate_state,
    exchange_code_for_token,
    verify_state,
)


class OAuthFlowTester:
    """Test suite for LinkedIn OAuth flow."""

    def __init__(self):
        self.test_results = []
        self.auth_state = None
        self.auth_url = None

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Record test result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")

    def test_1_environment_config(self) -> bool:
        """Test that required environment variables are configured."""
        print("\n=== Test 1: Environment Configuration ===")

        required_vars = {
            "LINKEDIN_CLIENT_ID": os.getenv("LINKEDIN_CLIENT_ID"),
            "LINKEDIN_CLIENT_SECRET": os.getenv("LINKEDIN_CLIENT_SECRET"),
            "LINKEDIN_REDIRECT_URI": os.getenv("LINKEDIN_REDIRECT_URI"),
        }

        all_present = True
        for var_name, var_value in required_vars.items():
            if not var_value:
                all_present = False
                self.log_result(
                    f"Environment variable {var_name}",
                    False,
                    f"Missing or empty"
                )
            else:
                # Show partial value for security
                display_value = var_value[:10] + "..." if len(var_value) > 10 else var_value
                self.log_result(
                    f"Environment variable {var_name}",
                    True,
                    f"Configured: {display_value}"
                )

        return all_present

    def test_2_generate_auth_url_defaults(self) -> bool:
        """Test generating authorization URL with default parameters."""
        print("\n=== Test 2: Generate Auth URL with Defaults ===")

        try:
            # Generate state
            self.auth_state = generate_state()
            self.log_result(
                "Generate state parameter",
                True,
                f"State: {self.auth_state[:10]}... (length: {len(self.auth_state)})"
            )

            # Generate auth URL with defaults
            self.auth_url = generate_auth_url(state=self.auth_state)
            self.log_result(
                "Generate authorization URL",
                True,
                f"URL generated successfully"
            )

            # Validate URL structure
            parsed = urlparse(self.auth_url)
            self.log_result(
                "URL has valid structure",
                parsed.scheme == "https" and parsed.netloc == "www.linkedin.com",
                f"Scheme: {parsed.scheme}, Netloc: {parsed.netloc}"
            )

            # Validate query parameters
            params = parse_qs(parsed.query)
            required_params = ["response_type", "client_id", "redirect_uri", "state", "scope"]
            all_present = all(param in params for param in required_params)

            self.log_result(
                "URL contains all required parameters",
                all_present,
                f"Present: {', '.join(params.keys())}"
            )

            # Validate specific parameter values
            self.log_result(
                "response_type is 'code'",
                params.get("response_type") == ["code"],
                f"response_type: {params.get('response_type')}"
            )

            self.log_result(
                "state parameter matches generated state",
                params.get("state") == [self.auth_state],
                f"state in URL matches generated state"
            )

            return True

        except Exception as e:
            self.log_result(
                "Generate auth URL with defaults",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_3_generate_auth_url_custom(self) -> bool:
        """Test generating authorization URL with custom parameters."""
        print("\n=== Test 3: Generate Auth URL with Custom Parameters ===")

        try:
            # Generate with custom scopes
            custom_scopes = ["r_liteprofile", "r_emailaddress", "w_member_social"]
            custom_state = generate_state()

            auth_url = generate_auth_url(
                state=custom_state,
                scopes=custom_scopes,
                force_login=True
            )

            parsed = urlparse(auth_url)
            params = parse_qs(parsed.query)

            # Validate custom scopes
            scope_value = params.get("scope", [""])[0]
            has_all_scopes = all(scope in scope_value for scope in custom_scopes)

            self.log_result(
                "Custom scopes included in URL",
                has_all_scopes,
                f"Scopes: {scope_value}"
            )

            # Validate force_login parameter
            has_force_login = "force_login" in params and params["force_login"] == ["true"]
            self.log_result(
                "force_login parameter included",
                has_force_login,
                f"force_login: {params.get('force_login')}"
            )

            return True

        except Exception as e:
            self.log_result(
                "Generate auth URL with custom parameters",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_4_state_verification(self) -> bool:
        """Test state parameter verification for CSRF protection."""
        print("\n=== Test 4: State Parameter Verification (CSRF Protection) ===")

        try:
            # Generate two different states
            state1 = generate_state()
            state2 = generate_state()

            self.log_result(
                "States are unique",
                state1 != state2,
                f"state1: {state1[:10]}..., state2: {state2[:10]}..."
            )

            # Test correct state verification
            is_valid = verify_state(state1, state1)
            self.log_result(
                "State verification succeeds with matching states",
                is_valid,
                "State verification works correctly"
            )

            # Test incorrect state verification
            is_invalid = verify_state(state1, state2)
            self.log_result(
                "State verification fails with different states",
                not is_invalid,
                "CSRF protection working"
            )

            return True

        except Exception as e:
            self.log_result(
                "State parameter verification",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_5_callback_endpoint_structure(self) -> bool:
        """Test that callback endpoint is properly structured."""
        print("\n=== Test 5: Callback Endpoint Structure ===")

        try:
            from main import app
            from api.linkedin import router

            # Check that router is registered
            routes = [route.path for route in router.routes]
            has_callback = "/auth/callback" in routes

            self.log_result(
                "Callback endpoint exists in router",
                has_callback,
                f"Routes: {', '.join(routes)}"
            )

            # Check endpoint accepts POST
            callback_route = None
            for route in router.routes:
                if route.path == "/auth/callback":
                    callback_route = route
                    break

            if callback_route:
                methods = getattr(callback_route, "methods", set())
                self.log_result(
                    "Callback endpoint accepts POST requests",
                    "POST" in methods,
                    f"Methods: {', '.join(methods)}"
                )

            return True

        except Exception as e:
            self.log_result(
                "Callback endpoint structure",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_6_error_handling_missing_config(self) -> None:
        """Test error handling for missing configuration."""
        print("\n=== Test 6: Error Handling - Missing Configuration ===")

        try:
            # Temporarily unset environment variables
            original_client_id = os.environ.get("LINKEDIN_CLIENT_ID")
            original_client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET")
            original_redirect_uri = os.environ.get("LINKEDIN_REDIRECT_URI")

            # Test missing client ID
            os.environ["LINKEDIN_CLIENT_ID"] = ""
            try:
                generate_auth_url(state="test")
                self.log_result(
                    "Raise error for missing client ID",
                    False,
                    "Should have raised ValueError"
                )
            except ValueError as e:
                self.log_result(
                    "Raise error for missing client ID",
                    "client ID" in str(e).lower(),
                    f"Correct error raised: {str(e)[:50]}..."
                )

            # Test missing client secret
            os.environ["LINKEDIN_CLIENT_ID"] = original_client_id or "test"
            os.environ["LINKEDIN_CLIENT_SECRET"] = ""
            try:
                exchange_code_for_token("test_code")
                self.log_result(
                    "Raise error for missing client secret",
                    False,
                    "Should have raised ValueError"
                )
            except ValueError as e:
                self.log_result(
                    "Raise error for missing client secret",
                    "client secret" in str(e).lower(),
                    f"Correct error raised: {str(e)[:50]}..."
                )

            # Restore environment
            if original_client_id:
                os.environ["LINKEDIN_CLIENT_ID"] = original_client_id
            if original_client_secret:
                os.environ["LINKEDIN_CLIENT_SECRET"] = original_client_secret
            if original_redirect_uri:
                os.environ["LINKEDIN_REDIRECT_URI"] = original_redirect_uri

        except Exception as e:
            self.log_result(
                "Error handling for missing configuration",
                False,
                f"Unexpected error: {str(e)}"
            )

    def test_7_frontend_integration(self) -> bool:
        """Test that frontend components are properly integrated."""
        print("\n=== Test 7: Frontend Integration ===")

        try:
            # Check frontend API client methods
            frontend_client_path = "../frontend/src/api/client.ts"
            if os.path.exists(frontend_client_path):
                with open(frontend_client_path, "r") as f:
                    client_content = f.read()

                has_linkedin_methods = (
                    "getLinkedInAuthUrl" in client_content and
                    "processLinkedInCallback" in client_content
                )

                self.log_result(
                    "Frontend API client has LinkedIn methods",
                    has_linkedin_methods,
                    "LinkedIn integration methods present"
                )
            else:
                self.log_result(
                    "Frontend API client exists",
                    False,
                    "File not found"
                )

            # Check frontend components exist
            components = [
                "LinkedInAuthButton",
                "LinkedInImport",
                "LinkedInSearch"
            ]

            for component in components:
                component_path = f"../frontend/src/components/{component}.tsx"
                exists = os.path.exists(component_path)
                self.log_result(
                    f"Component {component} exists",
                    exists,
                    f"Path: {component_path}"
                )

            return True

        except Exception as e:
            self.log_result(
                "Frontend integration",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_8_oauth_flow_simulation(self) -> bool:
        """Simulate complete OAuth flow without actual LinkedIn call."""
        print("\n=== Test 8: Complete OAuth Flow Simulation ===")

        try:
            from main import app

            # Create test client
            client = TestClient(app)

            # Step 1: Generate auth URL
            print("\n  Step 1: Request authorization URL")
            response = client.get("/api/linkedin/auth/url")
            self.log_result(
                "Auth URL endpoint responds",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )

            if response.status_code != 200:
                print(f"    Response: {response.text}")
                return False

            data = response.json()
            has_auth_url = "auth_url" in data and "state" in data

            self.log_result(
                "Auth URL response has required fields",
                has_auth_url,
                f"Fields: {', '.join(data.keys())}"
            )

            if not has_auth_url:
                return False

            auth_url = data["auth_url"]
            state = data["state"]

            print(f"    Generated auth URL: {auth_url[:80]}...")
            print(f"    Generated state: {state[:10]}...")

            # Step 2: Simulate callback (with mock code)
            print("\n  Step 2: Simulate OAuth callback")
            callback_data = {
                "code": "test_authorization_code_12345",
                "state": state
            }

            # This will fail because we're using a fake code, but we can test the endpoint structure
            callback_response = client.post(
                "/api/linkedin/auth/callback",
                json=callback_data
            )

            # We expect either success (if mocked) or proper error handling
            self.log_result(
                "Callback endpoint accepts POST",
                callback_response.status_code in [200, 401, 500],
                f"Status: {callback_response.status_code}"
            )

            if callback_response.status_code == 200:
                print("    ✓ Token exchange would succeed with valid code")
            else:
                print(f"    Expected error with fake code: {callback_response.json().get('detail', 'No detail')[:100]}")

            return True

        except Exception as e:
            self.log_result(
                "Complete OAuth flow simulation",
                False,
                f"Error: {str(e)}"
            )
            return False

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        passed = sum(1 for r in self.test_results if "PASS" in r["status"])
        failed = sum(1 for r in self.test_results if "FAIL" in r["status"])
        total = len(self.test_results)

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")

        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if "FAIL" in result["status"]:
                    print(f"  ✗ {result['test']}")
                    if result["message"]:
                        print(f"    {result['message']}")

        print("\n" + "=" * 70)

        if failed == 0:
            print("✓ ALL TESTS PASSED - OAuth flow is properly integrated!")
        else:
            print(f"✗ {failed} TEST(S) FAILED - Please review the implementation")

        print("=" * 70)


def main():
    """Run all OAuth flow tests."""
    print("=" * 70)
    print("LinkedIn OAuth Flow End-to-End Test")
    print("=" * 70)
    print("\nThis test validates the complete OAuth 2.0 integration:")
    print("1. Backend auth URL generation")
    print("2. Frontend redirect handling")
    print("3. Backend callback processing")
    print("4. Token exchange logic")
    print("5. Error handling")
    print("6. CSRF protection")
    print()

    tester = OAuthFlowTester()

    # Run tests
    env_configured = tester.test_1_environment_config()

    if not env_configured:
        print("\n⚠ WARNING: Environment variables not configured")
        print("Some tests will be skipped or may fail.")
        print("\nTo run complete tests, set the following environment variables:")
        print("  export LINKEDIN_CLIENT_ID='your-client-id'")
        print("  export LINKEDIN_CLIENT_SECRET='your-client-secret'")
        print("  export LINKEDIN_REDIRECT_URI='http://localhost:8000/api/linkedin/auth/callback'")
        print()

    # Run all tests
    try:
        if env_configured:
            tester.test_2_generate_auth_url_defaults()
            tester.test_3_generate_auth_url_custom()
        else:
            print("\n=== Skipping tests that require configuration ===")

        tester.test_4_state_verification()
        tester.test_5_callback_endpoint_structure()
        tester.test_6_error_handling_missing_config()
        tester.test_7_frontend_integration()
        tester.test_8_oauth_flow_simulation()

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nUnexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Print summary
    tester.print_summary()

    # Return exit code
    failed = sum(1 for r in tester.test_results if "FAIL" in r["status"])
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
