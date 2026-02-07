#!/usr/bin/env python3
"""
Comprehensive test script for candidate source attribution endpoint.

This script tests:
1. Endpoint availability and response structure
2. Metrics calculation accuracy (conversion rates, time-to-hire)
3. Stage distribution percentage calculations
4. Date filtering functionality
5. Error handling for invalid inputs
6. Empty dataset handling
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/analytics/candidate-source-attribution"
FULL_URL = f"{BASE_URL}{ENDPOINT}"

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_section(title: str):
    """Print a section header."""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")

def print_success(message: str):
    """Print a success message."""
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message: str):
    """Print an error message."""
    print(f"{RED}✗ {message}{RESET}")

def print_info(message: str):
    """Print an info message."""
    print(f"{YELLOW}ℹ {message}{RESET}")

def check_server_running() -> bool:
    """Check if the backend server is running."""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def test_endpoint_exists() -> bool:
    """Test that the endpoint is registered and accessible."""
    print_section("TEST 1: Endpoint Availability")

    try:
        response = requests.get(FULL_URL, timeout=10)
        if response.status_code == 200:
            print_success(f"Endpoint is accessible at {FULL_URL}")
            return True
        else:
            print_error(f"Endpoint returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend server. Is it running?")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False

def test_response_structure() -> bool:
    """Test that the response has the correct structure."""
    print_section("TEST 2: Response Structure Validation")

    try:
        response = requests.get(FULL_URL, timeout=10)
        if response.status_code != 200:
            print_error(f"Endpoint returned status code {response.status_code}")
            return False

        data = response.json()

        # Check required top-level fields
        required_fields = ["sources", "total_candidates", "date_range"]
        missing_fields = [f for f in required_fields if f not in data]

        if missing_fields:
            print_error(f"Missing required fields: {missing_fields}")
            return False

        print_success("All required top-level fields present")

        # Check sources is a list
        if not isinstance(data["sources"], list):
            print_error("'sources' field is not a list")
            return False

        print_success("'sources' field is a list")

        # Check total_candidates is an integer
        if not isinstance(data["total_candidates"], int):
            print_error("'total_candidates' field is not an integer")
            return False

        print_success("'total_candidates' field is an integer")

        # Validate each source entry
        if len(data["sources"]) > 0:
            source = data["sources"][0]
            required_source_fields = [
                "source", "candidate_count", "hired_count",
                "conversion_rate", "average_time_to_hire_days", "stage_distribution"
            ]
            missing_source_fields = [f for f in required_source_fields if f not in source]

            if missing_source_fields:
                print_error(f"Source entry missing fields: {missing_source_fields}")
                return False

            print_success("Source entries have all required fields")

            # Check data types
            if not isinstance(source["source"], str):
                print_error("'source' field is not a string")
                return False

            if not isinstance(source["candidate_count"], int):
                print_error("'candidate_count' field is not an integer")
                return False

            if not isinstance(source["hired_count"], int):
                print_error("'hired_count' field is not an integer")
                return False

            if not isinstance(source["conversion_rate"], (int, float)):
                print_error("'conversion_rate' field is not a number")
                return False

            if not isinstance(source["average_time_to_hire_days"], (int, float)):
                print_error("'average_time_to_hire_days' field is not a number")
                return False

            if not isinstance(source["stage_distribution"], list):
                print_error("'stage_distribution' field is not a list")
                return False

            print_success("All source fields have correct data types")

            # Validate stage distribution structure
            if len(source["stage_distribution"]) > 0:
                stage = source["stage_distribution"][0]
                required_stage_fields = ["stage_name", "count", "percentage"]

                missing_stage_fields = [f for f in required_stage_fields if f not in stage]
                if missing_stage_fields:
                    print_error(f"Stage entry missing fields: {missing_stage_fields}")
                    return False

                print_success("Stage distribution entries have all required fields")

        return True

    except Exception as e:
        print_error(f"Error validating response structure: {str(e)}")
        return False

def test_conversion_rate_calculation() -> bool:
    """Test that conversion rates are calculated correctly."""
    print_section("TEST 3: Conversion Rate Calculation")

    try:
        response = requests.get(FULL_URL, timeout=10)
        if response.status_code != 200:
            print_error("Could not fetch data for conversion rate validation")
            return False

        data = response.json()

        if len(data["sources"]) == 0:
            print_info("No sources to validate conversion rates")
            return True

        all_valid = True
        for source in data["sources"]:
            candidate_count = source["candidate_count"]
            hired_count = source["hired_count"]
            reported_rate = source["conversion_rate"]

            # Calculate expected conversion rate
            if candidate_count > 0:
                expected_rate = round(hired_count / candidate_count, 3)
            else:
                expected_rate = 0.0

            # Check if the reported rate matches (with small floating point tolerance)
            if abs(reported_rate - expected_rate) < 0.001:
                print_success(
                    f"Source '{source['source']}': conversion rate is correct "
                    f"({hired_count}/{candidate_count} = {reported_rate})"
                )
            else:
                print_error(
                    f"Source '{source['source']}': conversion rate mismatch - "
                    f"expected {expected_rate}, got {reported_rate}"
                )
                all_valid = False

            # Validate conversion rate is between 0 and 1
            if not (0 <= reported_rate <= 1):
                print_error(
                    f"Source '{source['source']}': conversion rate {reported_rate} "
                    f"is not between 0 and 1"
                )
                all_valid = False

            # Validate hired_count <= candidate_count
            if hired_count > candidate_count:
                print_error(
                    f"Source '{source['source']}': hired_count ({hired_count}) > "
                    f"candidate_count ({candidate_count})"
                )
                all_valid = False

        return all_valid

    except Exception as e:
        print_error(f"Error validating conversion rates: {str(e)}")
        return False

def test_stage_distribution_percentages() -> bool:
    """Test that stage distribution percentages sum to approximately 1.0."""
    print_section("TEST 4: Stage Distribution Percentages")

    try:
        response = requests.get(FULL_URL, timeout=10)
        if response.status_code != 200:
            print_error("Could not fetch data for stage distribution validation")
            return False

        data = response.json()

        if len(data["sources"]) == 0:
            print_info("No sources to validate stage distributions")
            return True

        all_valid = True
        for source in data["sources"]:
            stage_dist = source["stage_distribution"]

            if len(stage_dist) == 0:
                print_info(f"Source '{source['source']}': no stage distribution data")
                continue

            # Sum all percentages
            total_percentage = sum(stage["percentage"] for stage in stage_dist)

            # Allow small floating point errors
            if abs(total_percentage - 1.0) < 0.01:  # Within 1% tolerance
                print_success(
                    f"Source '{source['source']}': stage distribution percentages sum to {total_percentage:.3f}"
                )
            else:
                print_error(
                    f"Source '{source['source']}': stage distribution percentages sum to "
                    f"{total_percentage:.3f}, expected ~1.0"
                )
                all_valid = False

            # Validate each percentage is between 0 and 1
            for stage in stage_dist:
                if not (0 <= stage["percentage"] <= 1):
                    print_error(
                        f"Source '{source['source']}', stage '{stage['stage_name']}': "
                        f"percentage {stage['percentage']} is not between 0 and 1"
                    )
                    all_valid = False

            # Validate counts are non-negative
            for stage in stage_dist:
                if stage["count"] < 0:
                    print_error(
                        f"Source '{source['source']}', stage '{stage['stage_name']}': "
                        f"count {stage['count']} is negative"
                    )
                    all_valid = False

        return all_valid

    except Exception as e:
        print_error(f"Error validating stage distributions: {str(e)}")
        return False

def test_date_filtering() -> bool:
    """Test date filtering functionality."""
    print_section("TEST 5: Date Filtering")

    try:
        # Test with valid date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }

        response = requests.get(FULL_URL, params=params, timeout=10)
        if response.status_code == 200:
            print_success("Date filtering works with valid date range")
            data = response.json()

            # Check that date_range is populated in response
            if data.get("date_range"):
                print_success(f"Date range returned in response: {data['date_range']}")
            else:
                print_info("Date range is null (may indicate no data in range)")
        else:
            print_error(f"Date filtering returned status code {response.status_code}")
            return False

        # Test with ISO 8601 datetime format
        params_iso = {
            "start_date": start_date.strftime("%Y-%m-%dT00:00:00Z"),
            "end_date": end_date.strftime("%Y-%m-%dT23:59:59Z")
        }

        response_iso = requests.get(FULL_URL, params=params_iso, timeout=10)
        if response_iso.status_code == 200:
            print_success("Date filtering works with ISO 8601 datetime format")
        else:
            print_error(f"ISO 8601 format returned status code {response_iso.status_code}")
            return False

        # Test with invalid date format
        invalid_params = {"start_date": "invalid-date-format"}
        response_invalid = requests.get(FULL_URL, params=invalid_params, timeout=10)

        if response_invalid.status_code == 400:
            print_success("Invalid date format returns 400 status code")
        elif response_invalid.status_code == 422:
            print_success("Invalid date format returns 422 status code (FastAPI validation)")
        else:
            print_error(
                f"Invalid date format returned unexpected status code {response_invalid.status_code}"
            )
            return False

        return True

    except Exception as e:
        print_error(f"Error testing date filtering: {str(e)}")
        return False

def test_empty_dataset_handling() -> bool:
    """Test handling of empty or minimal datasets."""
    print_section("TEST 6: Empty Dataset Handling")

    try:
        # Test with a very old date range that likely has no data
        old_start = "2020-01-01"
        old_end = "2020-01-31"

        params = {"start_date": old_start, "end_date": old_end}
        response = requests.get(FULL_URL, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_success("Endpoint returns 200 even with no data in date range")

            # Check that empty sources list is handled correctly
            if "sources" in data and isinstance(data["sources"], list):
                print_success("Empty dataset returns valid structure with sources list")
                if len(data["sources"]) == 0:
                    print_info("No sources found in specified date range (expected)")
            else:
                print_error("Empty dataset response structure is invalid")
                return False
        else:
            print_error(f"Empty dataset returned status code {response.status_code}")
            return False

        return True

    except Exception as e:
        print_error(f"Error testing empty dataset handling: {str(e)}")
        return False

def test_source_sorting() -> bool:
    """Test that sources are sorted by candidate_count descending."""
    print_section("TEST 7: Source Sorting")

    try:
        response = requests.get(FULL_URL, timeout=10)
        if response.status_code != 200:
            print_error("Could not fetch data to validate sorting")
            return False

        data = response.json()

        if len(data["sources"]) <= 1:
            print_info("Not enough sources to validate sorting")
            return True

        # Check that sources are sorted by candidate_count descending
        for i in range(len(data["sources"]) - 1):
            current_count = data["sources"][i]["candidate_count"]
            next_count = data["sources"][i + 1]["candidate_count"]

            if current_count >= next_count:
                print_success(
                    f"Source {i}: {current_count} >= Source {i+1}: {next_count}"
                )
            else:
                print_error(
                    f"Sources not sorted correctly: Source {i} has {current_count}, "
                    f"Source {i+1} has {next_count}"
                )
                return False

        print_success("All sources are correctly sorted by candidate_count descending")
        return True

    except Exception as e:
        print_error(f"Error validating source sorting: {str(e)}")
        return False

def test_average_time_to_hire_calculation() -> bool:
    """Test that average time-to-hire is reasonable."""
    print_section("TEST 8: Average Time-to-Hire Validation")

    try:
        response = requests.get(FULL_URL, timeout=10)
        if response.status_code != 200:
            print_error("Could not fetch data for time-to-hire validation")
            return False

        data = response.json()

        if len(data["sources"]) == 0:
            print_info("No sources to validate time-to-hire")
            return True

        all_valid = True
        for source in data["sources"]:
            avg_time = source["average_time_to_hire_days"]
            hired_count = source["hired_count"]

            # Time-to-hire should be 0 if no one was hired
            if hired_count == 0:
                if avg_time == 0.0:
                    print_success(
                        f"Source '{source['source']}': time-to-hire is 0 for no hires"
                    )
                else:
                    print_error(
                        f"Source '{source['source']}': time-to-hire is {avg_time} "
                        f"but hired_count is 0"
                    )
                    all_valid = False
            else:
                # Time-to-hire should be positive
                if avg_time > 0:
                    print_success(
                        f"Source '{source['source']}': time-to-hire is {avg_time} days "
                        f"(reasonable for {hired_count} hires)"
                    )
                elif avg_time == 0.0:
                    print_info(
                        f"Source '{source['source']}': time-to-hire is 0 (may indicate "
                        f"same-day hire or missing timestamps)"
                    )
                else:
                    print_error(
                        f"Source '{source['source']}': time-to-hire is negative ({avg_time})"
                    )
                    all_valid = False

        return all_valid

    except Exception as e:
        print_error(f"Error validating time-to-hire: {str(e)}")
        return False

def display_sample_data():
    """Display a sample of the data returned by the endpoint."""
    print_section("SAMPLE DATA")

    try:
        response = requests.get(FULL_URL, timeout=10)
        if response.status_code != 200:
            print_error("Could not fetch sample data")
            return

        data = response.json()

        print(f"Total Candidates: {data['total_candidates']}")
        print(f"Date Range: {data.get('date_range', 'Not specified')}")
        print(f"Number of Sources: {len(data['sources'])}")

        if len(data['sources']) > 0:
            print("\nTop 5 Sources:")
            print("-" * 80)
            for i, source in enumerate(data['sources'][:5], 1):
                print(f"\n{i}. {source['source'].upper()}")
                print(f"   Candidates: {source['candidate_count']}")
                print(f"   Hired: {source['hired_count']}")
                print(f"   Conversion Rate: {source['conversion_rate']:.1%}")
                print(f"   Avg Time-to-Hire: {source['average_time_to_hire_days']} days")
                print(f"   Stages: {', '.join(s['stage_name'] for s in source['stage_distribution'][:3])}")

    except Exception as e:
        print_error(f"Error displaying sample data: {str(e)}")

def main():
    """Run all tests."""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}CANDIDATE SOURCE ATTRIBUTION ENDPOINT TEST SUITE{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")
    print(f"\nTesting endpoint: {FULL_URL}\n")

    # Check if server is running
    if not check_server_running():
        print_error("Backend server is not running!")
        print_info("Please start the backend server first:")
        print_info("  cd backend && python -m uvicorn main:app --reload")
        sys.exit(1)

    print_success("Backend server is running")

    # Run all tests
    tests = [
        ("Endpoint Availability", test_endpoint_exists),
        ("Response Structure", test_response_structure),
        ("Conversion Rate Calculation", test_conversion_rate_calculation),
        ("Stage Distribution Percentages", test_stage_distribution_percentages),
        ("Date Filtering", test_date_filtering),
        ("Empty Dataset Handling", test_empty_dataset_handling),
        ("Source Sorting", test_source_sorting),
        ("Average Time-to-Hire", test_average_time_to_hire_calculation),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {str(e)}")
            results[test_name] = False

    # Display sample data
    display_sample_data()

    # Print summary
    print_section("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_test in results.items():
        status = f"{GREEN}PASSED{RESET}" if passed_test else f"{RED}FAILED{RESET}"
        print(f"{status}: {test_name}")

    print(f"\n{BLUE}Total: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}✓ ALL TESTS PASSED!{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{RED}✗ SOME TESTS FAILED{RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
