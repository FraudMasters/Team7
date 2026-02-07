"""
Configuration fixtures for integration tests.

This module provides pytest fixtures for integration tests,
including the base URL for the API server.
"""
import os
import pytest


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """
    Get the base URL for the API server.

    Reads from API_BASE_URL environment variable.

    Returns:
        Base URL for API requests

    Raises:
        ValueError: If API_BASE_URL environment variable is not set
    """
    url = os.getenv("API_BASE_URL", "")
    if not url:
        raise ValueError("API_BASE_URL environment variable must be set for integration tests")
    return url
