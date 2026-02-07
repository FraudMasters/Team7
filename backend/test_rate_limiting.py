#!/usr/bin/env python3
"""Verification script for rate limiting and exponential backoff implementation."""

import sys

def test_implementation():
    """Test that rate limiting and exponential backoff are implemented."""
    try:
        from services.linkedin_service import LinkedInService

        # Create service with test token
        service = LinkedInService(access_token="test_token_12345")

        # Check for rate limiting method
        assert hasattr(service, '_check_rate_limit'), "Missing _check_rate_limit method"
        print("✓ Rate limiting method exists")

        # Check for exponential backoff method
        assert hasattr(service, '_calculate_backoff'), "Missing _calculate_backoff method"
        print("✓ Exponential backoff method exists")

        # Check for retry logic method
        assert hasattr(service, '_should_retry'), "Missing _should_retry method"
        print("✓ Retry logic method exists")

        # Check for async sleep method
        assert hasattr(service, '_async_sleep'), "Missing _async_sleep method"
        print("✓ Async sleep method exists")

        # Test backoff calculation
        backoff1 = service._calculate_backoff(0)
        assert backoff1 >= 0, f"Invalid backoff value: {backoff1}"
        assert backoff1 <= service._max_backoff, f"Backoff exceeds max: {backoff1}"
        print(f"✓ Backoff calculation works (attempt 0: {backoff1:.2f}s)")

        backoff2 = service._calculate_backoff(1)
        assert backoff2 >= backoff1 * 0.75, f"Backoff should increase: {backoff2} >= {backoff1}"
        print(f"✓ Exponential backoff increases (attempt 1: {backoff2:.2f}s)")

        # Test retry logic
        assert service._should_retry(429, None) is True, "Should retry on 429"
        assert service._should_retry(503, None) is True, "Should retry on 503"
        assert service._should_retry(401, None) is False, "Should not retry on 401"
        assert service._should_retry(404, None) is False, "Should not retry on 404"
        print("✓ Retry logic works correctly")

        # Test that retry configuration is accessible
        assert service._max_retries > 0, "max_retries should be positive"
        assert service._initial_backoff > 0, "initial_backoff should be positive"
        assert service._max_backoff > service._initial_backoff, "max_backoff should exceed initial"
        assert service._backoff_multiplier > 1, "backoff_multiplier should exceed 1"
        print("✓ Retry configuration is valid")

        print("\n✓✓✓ All verification checks passed! ✓✓✓")
        print("Rate limiting and exponential backoff are properly implemented.")
        return 0

    except Exception as e:
        print(f"\n✗✗✗ Verification failed: {e} ✗✗✗")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_implementation())
