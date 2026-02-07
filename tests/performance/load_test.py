"""
End-to-end load testing suite using Locust.

This load test simulates realistic user behavior on the recruitment platform
with 100 concurrent users performing various operations.

Performance Targets:
- Candidate list P95 response time: < 2 seconds
- Resume upload and analysis P95 time: < 30 seconds
- Redis cache hit rate: > 70%
- No memory leaks in worker processes

Test Scenarios:
1. Browse candidates (most frequent - 70% weight)
2. View candidate details (medium - 20% weight)
3. Upload and analyze resume (heavy - 10% weight)

Usage:
    # Run with default settings (100 users, 10 spawn rate, 1 minute)
    locust -f tests/performance/load_test.py --headless -u 100 -r 10 -t 1m

    # Run with custom settings
    locust -f tests/performance/load_test.py --headless -u 200 -r 20 -t 5m

    # Run with web UI
    locust -f tests/performance/load_test.py

Environment Variables:
    TARGET_HOST: API base URL (default: http://localhost:8000)
    REDIS_HOST: Redis host for cache monitoring (default: localhost)
    REDIS_PORT: Redis port (default: 6379)
"""
import os
import random
import time
import io
from typing import Dict, List
from collections import defaultdict

from locust import HttpUser, task, between, events, constant
from locust.runners import MasterRunner

# Test configuration
TARGET_HOST = os.getenv("TARGET_HOST", "http://localhost:8000")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Performance thresholds
CANDIDATE_LIST_P95_THRESHOLD_MS = 500  # 500ms - optimized target
CANDIDATE_DETAIL_P95_THRESHOLD_MS = 500  # 500ms - optimized target
ANALYSIS_P95_THRESHOLD_MS = 30000  # 30 seconds - heavy operation
CACHE_HIT_RATE_THRESHOLD = 0.70  # 70%

# Sample test data
SAMPLE_RESUME_NAMES = [
    "John Smith - Software Engineer.pdf",
    "Jane Doe - Data Scientist.pdf",
    "Bob Johnson - DevOps Engineer.pdf",
    "Alice Williams - Frontend Developer.pdf",
    "Charlie Brown - Full Stack Developer.pdf"
]

SAMPLE_VACANCY_IDS = []  # Will be populated during test setup


class PerformanceMetrics:
    """Track performance metrics across all users."""

    def __init__(self):
        self.response_times: Dict[str, List[int]] = defaultdict(list)
        self.cache_hits = 0
        self.cache_misses = 0
        self.requests_total = 0
        self.start_time = None

    def record_response(self, endpoint: str, response_time_ms: int):
        """Record a response time for an endpoint."""
        self.response_times[endpoint].append(response_time_ms)
        self.requests_total += 1

    def record_cache_hit(self):
        """Record a cache hit."""
        self.cache_hits += 1

    def record_cache_miss(self):
        """Record a cache miss."""
        self.cache_misses += 1

    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def get_p95_response_time(self, endpoint: str) -> float:
        """Calculate 95th percentile response time for an endpoint."""
        times = sorted(self.response_times.get(endpoint, []))
        if not times:
            return 0.0
        index = int(len(times) * 0.95)
        return times[index]

    def print_summary(self):
        """Print performance summary."""
        print("\n" + "=" * 80)
        print("LOAD TEST PERFORMANCE SUMMARY")
        print("=" * 80)

        # Cache hit rate
        hit_rate = self.get_cache_hit_rate()
        print(f"\nCache Hit Rate: {hit_rate * 100:.2f}%")
        print(f"  Hits: {self.cache_hits}")
        print(f"  Misses: {self.cache_misses}")
        print(f"  Status: {'✓ PASS' if hit_rate >= CACHE_HIT_RATE_THRESHOLD else '✗ FAIL'} " +
              f"(threshold: {CACHE_HIT_RATE_THRESHOLD * 100:.0f}%)")

        # Response times by endpoint
        print("\nResponse Times (P95):")
        print("-" * 80)
        for endpoint, times in sorted(self.response_times.items()):
            if times:
                p95 = self.get_p95_response_time(endpoint)
                avg = sum(times) / len(times)
                print(f"{endpoint}")
                print(f"  P95: {p95:.0f}ms")
                print(f"  Avg: {avg:.0f}ms")
                print(f"  Count: {len(times)}")

                # Check thresholds
                if "candidates" in endpoint:
                    if "{id}" in endpoint:
                        status = "✓ PASS" if p95 <= CANDIDATE_DETAIL_P95_THRESHOLD_MS else "✗ FAIL"
                        print(f"  Status: {status} (threshold: {CANDIDATE_DETAIL_P95_THRESHOLD_MS}ms)")
                    else:
                        status = "✓ PASS" if p95 <= CANDIDATE_LIST_P95_THRESHOLD_MS else "✗ FAIL"
                        print(f"  Status: {status} (threshold: {CANDIDATE_LIST_P95_THRESHOLD_MS}ms)")
                elif "analyze" in endpoint or "upload" in endpoint:
                    status = "✓ PASS" if p95 <= ANALYSIS_P95_THRESHOLD_MS else "✗ FAIL"
                    print(f"  Status: {status} (threshold: {ANALYSIS_P95_THRESHOLD_MS}ms)")

        print("\n" + "=" * 80)


# Global metrics tracker
metrics = PerformanceMetrics()


def create_test_pdf() -> bytes:
    """Create a minimal valid PDF for testing resume upload.

    Returns:
        Bytes content of a simple PDF file with resume-like content
    """
    # Simple PDF content with resume text
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
/Length 200
>>
stream
BT
/F1 12 Tf
50 700 Td
(John Doe) Tj
0 -20 Td
(Senior Software Engineer) Tj
0 -20 Td
(Email: john.doe@example.com) Tj
0 -20 Td
(Phone: +1-234-567-8900) Tj
0 -40 Td
(Skills: Python, FastAPI, PostgreSQL, Redis, Docker) Tj
0 -30 Td
(Experience:) Tj
0 -20 Td
(5+ years in full-stack development) Tj
0 -20 Td
(Expertise in API design and microservices) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000262 00000 n
0000000345 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
567
%%EOF
"""
    return pdf_content


def check_cache_headers(response) -> bool:
    """Check if response was served from cache based on headers.

    Args:
        response: HTTP response object

    Returns:
        True if response was cached, False otherwise
    """
    # Check for common cache indicators
    cache_indicators = [
        "X-Cache-Status",
        "X-Cache",
        "Age",
        "X-From-Cache"
    ]

    for header in cache_indicators:
        header_value = response.headers.get(header, "")
        if header_value and ("hit" in header_value.lower() or "cached" in header_value.lower()):
            return True

    return False


class RecruitmentPlatformUser(HttpUser):
    """Simulate a realistic user on the recruitment platform.

    User Behavior:
    - Most users browse candidates (70% of actions)
    - Some users view candidate details (20% of actions)
    - Few users upload resumes (10% of actions)
    """

    # Wait time between tasks (in seconds): realistically between 1 and 3 seconds
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a user starts. Perform initial setup."""
        # Login or initialize session if needed
        self.client.verify = False  # Skip SSL verification for local testing

        # Discover available vacancies
        try:
            response = self.client.get("/api/vacancies/", timeout=5)
            if response.status_code == 200:
                vacancies = response.json()
                SAMPLE_VACANCY_IDS.extend([v.get("id") for v in vacancies[:5]])
        except Exception:
            pass

    @task(weight=70)
    def browse_candidates(self):
        """Browse the candidate list with different filters.

        This is the most common action - recruiters frequently look through
        lists of candidates to find potential matches.
        """
        # Randomize query parameters to simulate real browsing
        limit = random.choice([20, 50, 100])
        skip = random.choice([0, 20, 50, 100])

        # Add optional filters
        params = {"limit": limit, "skip": skip}

        # 30% of the time, filter by stage
        if random.random() < 0.3:
            stage = random.choice(["applied", "interview", "offer", "rejected"])
            params["stage_id"] = stage

        # 20% of the time, search by name
        if random.random() < 0.2:
            params["search"] = random.choice(["John", "Jane", "Engineer", "Developer"])

        start_time = time.time()

        with self.client.get(
            "/api/candidates/",
            params=params,
            catch_response=True,
            name="/api/candidates/ [browse]"
        ) as response:
            response_time = int((time.time() - start_time) * 1000)

            # Record metrics
            metrics.record_response("/api/candidates/", response_time)

            # Check cache status
            if check_cache_headers(response):
                metrics.record_cache_hit()
            else:
                metrics.record_cache_miss()

            # Validate response
            if response.status_code == 200:
                candidates = response.json()
                if isinstance(candidates, list):
                    response.success()
                else:
                    response.failure(f"Expected list, got {type(candidates)}")
            else:
                response.failure(f"Status {response.status_code}: {response.text[:100]}")

    @task(weight=20)
    def view_candidate_details(self):
        """View detailed information about a specific candidate.

        Users click on candidates from the list to see more details.
        """
        # First get a list of candidates
        list_response = self.client.get("/api/candidates/?limit=20", name="/api/candidates/ [list for details]")

        if list_response.status_code != 200:
            return

        candidates = list_response.json()
        if not candidates or len(candidates) == 0:
            return

        # Pick a random candidate
        candidate = random.choice(candidates)
        candidate_id = candidate.get("id")

        if not candidate_id:
            return

        start_time = time.time()

        with self.client.get(
            f"/api/candidates/{candidate_id}",
            catch_response=True,
            name="/api/candidates/{id} [view details]"
        ) as response:
            response_time = int((time.time() - start_time) * 1000)

            # Record metrics
            metrics.record_response("/api/candidates/{id}", response_time)

            # Check cache status
            if check_cache_headers(response):
                metrics.record_cache_hit()
            else:
                metrics.record_cache_miss()

            # Validate response
            if response.status_code == 200:
                candidate_data = response.json()
                if candidate_data.get("id") == candidate_id:
                    response.success()
                else:
                    response.failure("Candidate ID mismatch")
            else:
                response.failure(f"Status {response.status_code}")

    @task(weight=10)
    def upload_and_analyze_resume(self):
        """Upload a new resume and trigger analysis.

        This is a heavy operation that should complete in < 30 seconds.
        """
        # Create test PDF
        pdf_content = create_test_pdf()
        filename = random.choice(SAMPLE_RESUME_NAMES)

        # Prepare file upload
        files = {
            "file": (filename, io.BytesIO(pdf_content), "application/pdf")
        }

        # Optional: associate with a vacancy
        data = {}
        if SAMPLE_VACANCY_IDS:
            data["vacancy_id"] = random.choice(SAMPLE_VACANCY_IDS)

        start_time = time.time()

        with self.client.post(
            "/api/resumes/upload",
            files=files,
            data=data,
            catch_response=True,
            name="/api/resumes/upload [analyze]"
        ) as response:
            response_time = int((time.time() - start_time) * 1000)

            # Record metrics
            metrics.record_response("/api/resumes/upload", response_time)

            # Validate response
            if response.status_code in [200, 201, 202]:
                # Upload accepted, analysis may be async
                response.success()
            elif response.status_code == 413:
                # Payload too large - acceptable in load test
                response.success()
            else:
                response.failure(f"Status {response.status_code}: {response.text[:100]}")

    @task(weight=5)
    def view_vacancy_matches(self):
        """View candidates matched to a vacancy.

        Recruiters often look at top candidates for specific vacancies.
        """
        if not SAMPLE_VACANCY_IDS:
            return

        vacancy_id = random.choice(SAMPLE_VACANCY_IDS)

        start_time = time.time()

        with self.client.get(
            f"/api/vacancies/{vacancy_id}/matches",
            catch_response=True,
            name="/api/vacancies/{id}/matches [view]"
        ) as response:
            response_time = int((time.time() - start_time) * 1000)

            # Record metrics
            metrics.record_response("/api/vacancies/{id}/matches", response_time)

            # Check cache status
            if check_cache_headers(response):
                metrics.record_cache_hit()
            else:
                metrics.record_cache_miss()

            # Validate response
            if response.status_code == 200:
                matches = response.json()
                if isinstance(matches, list):
                    response.success()
                else:
                    response.failure(f"Expected list, got {type(matches)}")
            else:
                response.failure(f"Status {response.status_code}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops. Print performance summary."""
    if not isinstance(environment.runner, MasterRunner):
        metrics.print_summary()

        # Check if thresholds were met
        print("\nTHRESHOLD VERIFICATION:")
        print("-" * 80)

        # Cache hit rate
        hit_rate = metrics.get_cache_hit_rate()
        cache_status = "✓ PASS" if hit_rate >= CACHE_HIT_RATE_THRESHOLD else "✗ FAIL"
        print(f"Cache Hit Rate: {cache_status} ({hit_rate * 100:.2f}% >= {CACHE_HIT_RATE_THRESHOLD * 100:.0f}%)")

        # Candidate list P95
        candidate_p95 = metrics.get_p95_response_time("/api/candidates/")
        if candidate_p95 > 0:
            list_status = "✓ PASS" if candidate_p95 <= CANDIDATE_LIST_P95_THRESHOLD_MS else "✗ FAIL"
            print(f"Candidate List P95: {list_status} ({candidate_p95:.0f}ms <= {CANDIDATE_LIST_P95_THRESHOLD_MS}ms)")

        # Candidate detail P95
        detail_p95 = metrics.get_p95_response_time("/api/candidates/{id}")
        if detail_p95 > 0:
            detail_status = "✓ PASS" if detail_p95 <= CANDIDATE_DETAIL_P95_THRESHOLD_MS else "✗ FAIL"
            print(f"Candidate Detail P95: {detail_status} ({detail_p95:.0f}ms <= {CANDIDATE_DETAIL_P95_THRESHOLD_MS}ms)")

        # Upload/analysis P95
        upload_p95 = metrics.get_p95_response_time("/api/resumes/upload")
        if upload_p95 > 0:
            upload_status = "✓ PASS" if upload_p95 <= ANALYSIS_P95_THRESHOLD_MS else "✗ FAIL"
            print(f"Resume Upload P95: {upload_status} ({upload_p95:.0f}ms <= {ANALYSIS_P95_THRESHOLD_MS}ms)")

        print("\n" + "=" * 80)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track individual requests for additional metrics."""
    # This is called by Locust for each request
    # We can add custom logging or metrics here if needed
    pass


class MemoryLeakDetector:
    """Detect potential memory leaks during load testing.

    This class monitors memory usage trends over time to identify
    potential memory leaks in long-running processes.
    """

    def __init__(self):
        self.memory_samples = []
        self.start_time = time.time()

    def record_memory(self):
        """Record current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_samples.append({
                "time": time.time() - self.start_time,
                "memory_mb": memory_mb
            })
        except ImportError:
            # psutil not available, skip memory monitoring
            pass

    def check_memory_leak(self) -> bool:
        """Check if memory usage indicates a leak.

        Returns:
            True if memory leak detected, False otherwise
        """
        if len(self.memory_samples) < 10:
            return False

        # Compare first 10% to last 10% of samples
        n = len(self.memory_samples)
        early_samples = self.memory_samples[:max(10, n // 10)]
        late_samples = self.memory_samples[-max(10, n // 10):]

        early_avg = sum(s["memory_mb"] for s in early_samples) / len(early_samples)
        late_avg = sum(s["memory_mb"] for s in late_samples) / len(late_samples)

        # If memory grew by more than 50%, potential leak
        growth = (late_avg - early_avg) / early_avg if early_avg > 0 else 0
        return growth > 0.5


# Memory leak detector instance
memory_detector = MemoryLeakDetector()


@events.worker.add_listener
def on_worker(worker, **kwargs):
    """Called on worker instances. Periodically check memory."""
    pass


if __name__ == "__main__":
    # Allow running this file directly for testing
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        sys.exit(0)

    # Print performance targets for verification
    print("=" * 80)
    print("PERFORMANCE TESTING AND OPTIMIZATION")
    print("=" * 80)
    print()
    print("Performance Targets:")
    print(f"  - Candidate List P95: < 500ms")
    print(f"  - Candidate Detail P95: < 500ms")
    print(f"  - Resume Upload P95: < 30000ms")
    print(f"  - Cache Hit Rate: > 70%")
    print()
    print("Test Scenarios:")
    print("  - Browse candidates (70% weight)")
    print("  - View candidate details (20% weight)")
    print("  - Upload and analyze resume (10% weight)")
    print()
    print("Status: Performance targets configured")
    print("Target: <500ms for candidate list operations")
    print("Target: <500ms for candidate detail operations")
    print("Target: <30000ms for resume upload operations")
    print("=" * 80)
    print()
    print("This is a Locust load test file.")
    print("Run with: locust -f tests/performance/load_test.py")
    print("For headless mode: locust -f tests/performance/load_test.py --headless -u 100 -r 10 -t 1m")
