"""
Locust performance test file for critical backend endpoints.

This module defines load testing scenarios for the Resume Analysis API.
It tests the performance of critical endpoints under various load conditions.

Test Scenarios:
    - Health Check: Lightweight endpoint for baseline performance
    - Candidate Listing: Test fetching candidate lists with pagination
    - Vacancy Operations: Test creating and listing job vacancies
    - Matching Operations: Test matching resumes to vacancies

Usage:
    # Run with web UI
    locust -f tests/performance/locustfile.py

    # Run headless mode
    locust -f tests/performance/locustfile.py --headless --users 50 --spawn-rate 10 -t 60s

    # Run with specific host
    locust -f tests/performance/locustfile.py --host http://localhost:8888
"""
import json
import random
import uuid
from typing import Dict, List

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# ============================================================================
# Test Data Generators
# ============================================================================

SKILL_POOL = [
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust",
    "React", "Vue", "Angular", "FastAPI", "Django", "Flask",
    "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
    "Docker", "Kubernetes", "AWS", "GCP", "Azure",
    "TensorFlow", "PyTorch", "scikit-learn", "Pandas",
    "Git", "CI/CD", "Linux", "Nginx"
]

LOCATION_POOL = [
    "Remote", "New York", "San Francisco", "London", "Berlin",
    "Amsterdam", "Toronto", "Sydney", "Singapore", "Tokyo"
]

INDUSTRY_POOL = [
    "Technology", "Finance", "Healthcare", "E-commerce",
    "Manufacturing", "Education", "Consulting"
]


def generate_random_skills(min_count: int = 3, max_count: int = 8) -> List[str]:
    """Generate a random list of skills from the skill pool."""
    count = random.randint(min_count, max_count)
    return random.sample(SKILL_POOL, min(count, len(SKILL_POOL)))


def generate_vacancy_data() -> Dict:
    """Generate realistic vacancy creation data."""
    return {
        "title": f"Senior {random.choice(['Software Engineer', 'Developer', 'Data Scientist', 'DevOps Engineer'])}",
        "description": (
            f"We are looking for a skilled professional with experience in "
            f"{', '.join(generate_random_skills(3, 5))}. "
            f"The ideal candidate should be passionate about technology and "
            f"eager to work in a dynamic environment."
        ),
        "required_skills": generate_random_skills(3, 6),
        "min_experience_months": random.randint(24, 96),
        "additional_requirements": generate_random_skills(0, 3),
        "industry": random.choice(INDUSTRY_POOL),
        "work_format": random.choice(["Remote", "Office", "Hybrid"]),
        "location": random.choice(LOCATION_POOL),
        "salary_min": random.randint(60000, 100000),
        "salary_max": random.randint(100000, 180000),
        "english_level": random.choice(["B1", "B2", "C1", "C2"]),
        "employment_type": random.choice(["full-time", "part-time", "contract"])
    }


def generate_matching_data(vacancy_id: str = None) -> Dict:
    """Generate realistic matching request data."""
    if vacancy_id is None:
        vacancy_id = str(uuid.uuid4())

    return {
        "vacancy_id": vacancy_id,
        "resume_text": (
            f"Experienced professional with strong background in "
            f"{', '.join(generate_random_skills(4, 7))}. "
            f"Proven track record of delivering high-quality solutions. "
            f"Excellent communication skills and team collaboration abilities."
        ),
        "threshold": random.uniform(0.3, 0.7)
    }


# ============================================================================
# Test User Classes
# ============================================================================

class ResumeAnalysisUser(HttpUser):
    """
    Simulates user behavior for the Resume Analysis API.

    This user class performs realistic load testing by:
    - Making regular health checks (lightweight)
    - Listing candidates with various pagination options
    - Creating and listing vacancies
    - Performing matching operations

    Wait time between tasks: 1-3 seconds (simulates realistic user behavior)
    """

    # Wait time between task executions (in seconds)
    wait_time = between(1, 3)

    def on_start(self):
        """
        Called when a user starts.

        Performs initial setup like authentication and data seeding.
        """
        # Optionally perform login or setup here
        # For now, we'll skip auth to test public endpoints
        pass

    # ========================================================================
    # Health Check Tasks (Lightweight, high frequency)
    # ========================================================================

    @task(10)
    def health_check(self):
        """
        Check API health status.

        This is a lightweight endpoint that should respond very quickly.
        High weight (10) means this task runs frequently.
        """
        with self.client.get("/health", catch_response=True, name="Health Check") as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure(f"Unhealthy status: {data}")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(5)
    def readiness_check(self):
        """
        Check API readiness status.

        Similar to health check but verifies the service is ready to handle requests.
        """
        with self.client.get("/ready", catch_response=True, name="Readiness Check") as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ready":
                    response.success()
                else:
                    response.failure(f"Not ready: {data}")
            else:
                response.failure(f"Status code: {response.status_code}")

    # ========================================================================
    # Candidate Listing Tasks (Medium weight)
    # ========================================================================

    @task(8)
    def list_candidates_all(self):
        """
        List all candidates without filters.

        Tests the basic candidate listing functionality.
        """
        params = {
            "skip": random.randint(0, 50),
            "limit": random.choice([10, 20, 50, 100])
        }
        with self.client.get(
            "/api/candidates",
            params=params,
            catch_response=True,
            name="List Candidates [All]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    response.success()
                else:
                    response.failure(f"Expected list, got {type(data)}")
            elif response.status_code == 404:
                # Empty list is acceptable
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(6)
    def list_candidates_by_stage(self):
        """
        List candidates filtered by stage.

        Tests candidate filtering by workflow stage.
        """
        stages = ["applied", "screening", "interview", "offer", "hired", "rejected"]
        stage = random.choice(stages)
        params = {
            "stage": stage,
            "skip": random.randint(0, 20),
            "limit": random.choice([10, 20, 50])
        }
        with self.client.get(
            "/api/candidates",
            params=params,
            catch_response=True,
            name=f"List Candidates by Stage [{stage}]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    # ========================================================================
    # Vacancy Operations Tasks (Medium weight)
    # ========================================================================

    @task(7)
    def list_vacancies(self):
        """
        List all job vacancies.

        Tests the vacancy listing endpoint with pagination.
        """
        params = {
            "skip": random.randint(0, 20),
            "limit": random.choice([10, 20, 50])
        }
        with self.client.get(
            "/api/vacancies",
            params=params,
            catch_response=True,
            name="List Vacancies"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(3)
    def create_vacancy(self):
        """
        Create a new job vacancy.

        Tests the vacancy creation endpoint with realistic data.
        Lower weight (3) means this runs less frequently than read operations.
        """
        vacancy_data = generate_vacancy_data()
        with self.client.post(
            "/api/vacancies",
            json=vacancy_data,
            catch_response=True,
            name="Create Vacancy"
        ) as response:
            if response.status_code in [200, 201]:
                data = response.json()
                if "id" in data:
                    response.success()
                else:
                    response.failure("No ID in response")
            elif response.status_code == 422:
                # Validation errors are acceptable during load testing
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(4)
    def get_vacancy_by_id(self):
        """
        Get a specific vacancy by ID.

        Tests single vacancy retrieval.
        Uses a random UUID to simulate various lookup scenarios.
        """
        # Use a random UUID - some will exist, some won't
        vacancy_id = str(uuid.uuid4())
        with self.client.get(
            f"/api/vacancies/{vacancy_id}",
            catch_response=True,
            name="Get Vacancy by ID"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    # ========================================================================
    # Matching Operations Tasks (Lower weight - more expensive)
    # ========================================================================

    @task(2)
    def match_resume_to_vacancy(self):
        """
        Match a resume to a vacancy.

        Tests the matching endpoint which involves NLP processing.
        Lowest weight (2) because this is computationally expensive.
        """
        vacancy_id = str(uuid.uuid4())
        matching_data = generate_matching_data(vacancy_id)
        with self.client.post(
            "/api/matching/match",
            json=matching_data,
            catch_response=True,
            name="Match Resume to Vacancy"
        ) as response:
            if response.status_code in [200, 201]:
                data = response.json()
                # Validate response structure
                if "match_percentage" in data or "matches" in data:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            elif response.status_code in [404, 422]:
                # Vacancy not found or validation error is acceptable
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def compare_resume_vacancy(self):
        """
        Compare resume with vacancy for detailed matching.

        Tests the comparison endpoint which provides detailed skill analysis.
        Very low weight (1) as this is the most expensive operation.
        """
        vacancy_id = str(uuid.uuid4())
        comparison_data = {
            "vacancy_id": vacancy_id,
            "resume_text": (
                f"Senior Software Engineer with expertise in "
                f"{', '.join(generate_random_skills(5, 8))}. "
                f"Strong background in software development lifecycle."
            )
        }
        with self.client.post(
            "/api/matching/compare",
            json=comparison_data,
            catch_response=True,
            name="Compare Resume to Vacancy"
        ) as response:
            if response.status_code in [200, 201]:
                data = response.json()
                if "matched_skills" in data or "missing_skills" in data:
                    response.success()
                else:
                    response.failure("Invalid comparison response structure")
            elif response.status_code in [404, 422]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


# ============================================================================
# Specialized User Classes for Specific Scenarios
# ============================================================================

class ReadOnlyUser(ResumeAnalysisUser):
    """
    A user that only performs read operations.

    Useful for testing read-heavy workloads and ensuring
    that GET endpoints remain responsive under load.
    """

    # Override to only include read tasks
    @task(15)
    def list_candidates_all(self):
        super().list_candidates_all()

    @task(10)
    def list_vacancies(self):
        super().list_vacancies()

    @task(20)
    def health_check(self):
        super().health_check()


class WriteHeavyUser(ResumeAnalysisUser):
    """
    A user focused on write operations.

    Useful for testing how the system handles
    create operations under load.
    """

    wait_time = between(2, 5)  # Slower pace for writes

    @task(10)
    def create_vacancy(self):
        super().create_vacancy()

    @task(5)
    def list_vacancies(self):
        super().list_vacancies()

    @task(3)
    def health_check(self):
        super().health_check()


class MatchingIntensiveUser(ResumeAnalysisUser):
    """
    A user focused on matching operations.

    Useful for testing the performance of NLP-heavy
    matching endpoints under sustained load.
    """

    wait_time = between(3, 6)  # Slower due to expensive operations

    @task(8)
    def match_resume_to_vacancy(self):
        super().match_resume_to_vacancy()

    @task(5)
    def compare_resume_vacancy(self):
        super().compare_resume_vacancy()

    @task(2)
    def health_check(self):
        super().health_check()


# ============================================================================
# Event Handlers for Custom Reporting
# ============================================================================

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Called when the test stops.

    Can be used for custom reporting or cleanup.
    """
    if environment.stats.total.fail_ratio > 0.1:
        print(
            f"\n⚠️  WARNING: Failure rate is {environment.stats.total.fail_ratio:.2%}\n"
        )


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Called for each request to track custom metrics.

    This can be extended to log slow requests or trigger alerts.
    """
    # Example: Log slow requests
    if response_time > 5000:  # 5 seconds
        print(
            f"⚠️  Slow request detected: {name} "
            f"took {response_time}ms"
        )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # This allows running the file directly for quick testing
    import argparse

    parser = argparse.ArgumentParser(description="Run Locust performance tests")
    parser.add_argument(
        "--host",
        default="http://localhost:8888",
        help="Target host for load testing"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=10,
        help="Number of users to simulate"
    )
    parser.add_argument(
        "--spawn-rate",
        type=int,
        default=1,
        help="Rate at which users spawn (users per second)"
    )
    parser.add_argument(
        "--time",
        type=int,
        default=60,
        help="Duration of test in seconds"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (without web UI)"
    )

    args = parser.parse_args()

    # Build locust command
    import sys
    cmd_args = [
        "--host", args.host,
        "--users", str(args.users),
        "--spawn-rate", str(args.spawn_rate),
        "-t", f"{args.time}s"
    ]
    if args.headless:
        cmd_args.append("--headless")

    # Replace sys.argv to simulate command line invocation
    sys.argv = ["locust"] + cmd_args

    # Import and run locust
    from locust import main
    main()
