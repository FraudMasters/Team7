#!/usr/bin/env python3
"""
Verification script for FastAPI application startup and health check.

This script tests that the main.py application can be imported and
the basic endpoints are accessible.
"""
import sys
import time
import subprocess
import signal
import requests
from pathlib import Path


def test_import():
    """Test that main.py can be imported without errors."""
    print("Testing import of main.py...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from main import app, settings
        print("✓ main.py imported successfully")
        print(f"  - Backend host: {settings.backend_host}")
        print(f"  - Backend port: {settings.backend_port}")
        print(f"  - Database URL: {settings.database_url[:30]}...")
        print(f"  - CORS origins: {settings.cors_origins}")
        return True
    except Exception as e:
        print(f"✗ Failed to import main.py: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test that configuration is loaded correctly."""
    print("\nTesting configuration...")
    try:
        from config import get_settings
        settings = get_settings()

        # Test basic settings
        assert settings.backend_port == 8000, "Backend port should be 8000"
        assert settings.max_upload_size_mb > 0, "Max upload size should be positive"
        assert len(settings.allowed_file_types) > 0, "Should have allowed file types"
        assert len(settings.cors_origins) > 0, "Should have CORS origins"

        print("✓ Configuration loaded successfully")
        print(f"  - Max upload size: {settings.max_upload_size_mb}MB")
        print(f"  - Allowed file types: {settings.allowed_file_types}")
        print(f"  - CORS origins: {settings.cors_origins}")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def start_server():
    """Start the FastAPI server in the background."""
    print("\nStarting FastAPI server...")
    try:
        # Start uvicorn in the background
        proc = subprocess.Popen(
            ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent,
        )

        # Give server time to start
        print("Waiting for server to start...")
        time.sleep(3)

        # Check if process is still running
        if proc.poll() is None:
            print("✓ Server started successfully (PID: %d)" % proc.pid)
            return proc
        else:
            stdout, stderr = proc.communicate()
            print(f"✗ Server failed to start")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"✗ Failed to start server: {e}")
        return None


def test_health_endpoint():
    """Test the /health endpoint."""
    print("\nTesting /health endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print("✓ Health endpoint returned 200")
            print(f"  - Response: {data}")

            # Validate response structure
            assert data["status"] == "healthy", "Status should be healthy"
            assert "service" in data, "Should have service field"
            assert "version" in data, "Should have version field"

            print("✓ Health endpoint response structure is valid")
            return True
        else:
            print(f"✗ Health endpoint returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server (connection refused)")
        return False
    except requests.exceptions.Timeout:
        print("✗ Request timed out")
        return False
    except Exception as e:
        print(f"✗ Health endpoint test failed: {e}")
        return False


def test_root_endpoint():
    """Test the / root endpoint."""
    print("\nTesting / endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print("✓ Root endpoint returned 200")
            print(f"  - Response: {data}")
            return True
        else:
            print(f"✗ Root endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Root endpoint test failed: {e}")
        return False


def test_ready_endpoint():
    """Test the /ready endpoint."""
    print("\nTesting /ready endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8000/ready", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print("✓ Ready endpoint returned 200")
            print(f"  - Response: {data}")
            return True
        else:
            print(f"✗ Ready endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Ready endpoint test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("FastAPI Application Verification")
    print("=" * 60)

    # Test import and configuration (without starting server)
    import_ok = test_import()
    config_ok = test_config()

    if not (import_ok and config_ok):
        print("\n✗ Import/config tests failed, not starting server")
        sys.exit(1)

    # Start server and test endpoints
    proc = start_server()
    if proc is None:
        print("\n✗ Failed to start server")
        sys.exit(1)

    try:
        # Test endpoints
        health_ok = test_health_endpoint()
        root_ok = test_root_endpoint()
        ready_ok = test_ready_endpoint()

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary:")
        print("=" * 60)
        print(f"Import test:        {'PASS' if import_ok else 'FAIL'}")
        print(f"Config test:        {'PASS' if config_ok else 'FAIL'}")
        print(f"Health endpoint:    {'PASS' if health_ok else 'FAIL'}")
        print(f"Root endpoint:      {'PASS' if root_ok else 'FAIL'}")
        print(f"Ready endpoint:     {'PASS' if ready_ok else 'FAIL'}")
        print("=" * 60)

        if all([import_ok, config_ok, health_ok, root_ok, ready_ok]):
            print("\n✓ All tests PASSED")
            return 0
        else:
            print("\n✗ Some tests FAILED")
            return 1
    finally:
        # Stop server
        if proc:
            print("\nStopping server...")
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=5)
            print("✓ Server stopped")


if __name__ == "__main__":
    sys.exit(main())
