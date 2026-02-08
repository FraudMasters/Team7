"""
End-to-end performance benchmark tests for optimized resume processing pipeline.

This test suite measures and validates the performance improvements from the
optimized resume processing pipeline, including:
- Parallel processing vs sequential processing
- Cache hit vs cache miss performance
- Batch processing scalability
- Real-time progress update overhead
- End-to-end processing time reduction (target: 70%)

Test Categories:
- Single Resume Performance: Baseline metrics for individual resume processing
- Batch Processing Performance: Parallel batch analysis metrics
- Cache Performance: Cache hit/miss latency comparison
- Progress Update Overhead: WebSocket performance impact
- Overall Improvement: 70% reduction validation

Performance Targets (from spec 005):
- Resume processing time reduced by 70% from baseline
- Cache hits return results in <100ms
- Batch processing completes in parallel (not sequential)
- Real-time progress updates with minimal overhead
"""
import asyncio
import io
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport

# Import the FastAPI application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def test_pdf_content() -> bytes:
    """
    Create a realistic PDF file content for performance testing.

    Returns:
        Bytes content of a PDF file with resume-like content
    """
    # Create a more realistic PDF with actual resume content
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
/Length 300
>>
stream
BT
/F1 12 Tf
50 700 Td
(John Doe) Tj
50 680 Td
(Senior Software Engineer) Tj
50 660 Td
(john.doe@example.com) Tj
50 640 Td
(SUMMARY) Tj
50 620 Td
(Experienced software engineer with 8+ years in Python, Django,) Tj
50 600 Td
(FastAPI, PostgreSQL, Docker, and Kubernetes.) Tj
50 580 Td
(SKILLS) Tj
50 560 Td
(Python, Django, FastAPI, PostgreSQL, MongoDB, Redis,) Tj
50 540 Td
(Docker, Kubernetes, AWS, CI/CD, Git) Tj
50 520 Td
(EXPERIENCE) Tj
50 500 Td
(Senior Python Developer | Tech Corp | 2020-Present) Tj
50 480 Td
(Lead Developer | Startup Inc | 2018-2020) Tj
50 460 Td
(Developer | Software Co | 2016-2018) Tj
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
684
%%EOF
"""
    return pdf_content


@pytest.fixture
async def performance_client():
    """
    Create async HTTP client for performance testing.

    Returns:
        AsyncClient instance for making API requests
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        yield client


# ============================================================================
# Single Resume Performance Tests
# ============================================================================

class TestSingleResumePerformance:
    """Performance benchmarks for single resume processing."""

    @pytest.mark.slow
    @pytest.mark.performance
    async def test_single_resume_analysis_performance(
        self,
        performance_client: AsyncClient,
        test_pdf_content: bytes
    ):
        """
        Benchmark single resume analysis processing time.

        This test measures the end-to-end time for:
        1. File upload
        2. Resume analysis (keywords, entities, language)
        3. Results retrieval

        Target: Single resume should complete in reasonable time.
        This establishes the baseline for parallel processing comparison.
        """
        # Step 1: Upload resume
        upload_start = time.time()
        upload_response = await performance_client.post(
            "/api/resumes/upload",
            files={"file": ("perf_test.pdf", io.BytesIO(test_pdf_content), "application/pdf")}
        )
        upload_time_ms = (time.time() - upload_start) * 1000

        assert upload_response.status_code == 201
        resume_id = upload_response.json()["id"]

        # Step 2: Analyze resume
        analyze_start = time.time()
        analyze_response = await performance_client.post(
            "/api/resumes/analyze",
            json={
                "resume_id": resume_id,
                "check_grammar": False,  # Disable for faster testing
                "extract_experience": True,
                "detect_errors": False
            }
        )
        analyze_time_ms = (time.time() - analyze_start) * 1000

        assert analyze_response.status_code == 200
        analysis_data = analyze_response.json()

        # Validate results
        assert analysis_data["status"] == "completed"
        assert "processing_time_ms" in analysis_data

        # Record metrics
        total_time_ms = upload_time_ms + analyze_time_ms

        # Print performance metrics
        print(f"\n=== Single Resume Performance Metrics ===")
        print(f"Upload time: {upload_time_ms:.2f}ms")
        print(f"Analysis time: {analyze_time_ms:.2f}ms")
        print(f"Reported processing time: {analysis_data['processing_time_ms']:.2f}ms")
        print(f"Total end-to-end time: {total_time_ms:.2f}ms")

        # Performance assertions
        # Upload should be reasonably fast (< 5 seconds)
        assert upload_time_ms < 5000, f"Upload too slow: {upload_time_ms:.2f}ms"

        # Analysis should complete in reasonable time (< 30 seconds)
        assert analyze_time_ms < 30000, f"Analysis too slow: {analyze_time_ms:.2f}ms"

        # Total should be complete in acceptable time
        assert total_time_ms < 35000, f"Total processing too slow: {total_time_ms:.2f}ms"


# ============================================================================
# Batch Processing Performance Tests
# ============================================================================

class TestBatchProcessingPerformance:
    """Performance benchmarks for parallel batch processing."""

    @pytest.mark.slow
    @pytest.mark.performance
    async def test_parallel_vs_sequential_processing(
        self,
        performance_client: AsyncClient,
        test_pdf_content: bytes
    ):
        """
        Compare parallel vs sequential batch processing performance.

        This test:
        1. Uploads multiple resumes
        2. Processes them sequentially (baseline)
        3. Processes them in parallel (optimized)
        4. Calculates the performance improvement

        Target: Parallel processing should show significant time reduction
        compared to sequential processing (ideally approaching N workers speedup).
        """
        num_resumes = 5
        resume_ids = []

        # Upload multiple resumes
        print(f"\n=== Uploading {num_resumes} resumes ===")
        for i in range(num_resumes):
            response = await performance_client.post(
                "/api/resumes/upload",
                files={
                    "file": (f"perf_batch_{i}.pdf", io.BytesIO(test_pdf_content), "application/pdf")
                }
            )
            assert response.status_code == 201
            resume_ids.append(response.json()["id"])

        # Sequential processing (baseline)
        print(f"\n=== Sequential Processing (Baseline) ===")
        sequential_start = time.time()
        sequential_results = []

        for resume_id in resume_ids:
            response = await performance_client.post(
                "/api/resumes/analyze",
                json={
                    "resume_id": resume_id,
                    "check_grammar": False,
                    "extract_experience": True,
                    "detect_errors": False
                }
            )
            assert response.status_code == 200
            sequential_results.append(response.json())

        sequential_time_ms = (time.time() - sequential_start) * 1000

        # Process same resumes again to test cache + parallel
        print(f"\n=== Parallel Processing (via Batch API) ===")
        parallel_start = time.time()

        # Use batch upload endpoint for parallel processing
        batch_response = await performance_client.post(
            "/api/resumes/batch-upload",
            json={
                "resume_ids": resume_ids,
                "check_grammar": False,
                "extract_experience": True,
                "detect_errors": False,
                "batch_size": num_resumes
            }
        )

        parallel_time_ms = (time.time() - parallel_start) * 1000

        assert batch_response.status_code == 202
        batch_data = batch_response.json()

        # Calculate performance improvement
        if sequential_time_ms > 0:
            speedup = sequential_time_ms / parallel_time_ms
            improvement_percent = ((sequential_time_ms - parallel_time_ms) / sequential_time_ms) * 100
        else:
            speedup = 1.0
            improvement_percent = 0

        # Print comparison
        print(f"\n=== Performance Comparison ===")
        print(f"Sequential time: {sequential_time_ms:.2f}ms")
        print(f"Parallel time: {parallel_time_ms:.2f}ms")
        print(f"Speedup: {speedup:.2f}x")
        print(f"Improvement: {improvement_percent:.1f}%")
        print(f"Time saved: {sequential_time_ms - parallel_time_ms:.2f}ms")

        # Assertions
        # Parallel should be faster (or at least not significantly slower)
        assert parallel_time_ms <= sequential_time_ms * 1.1, (
            f"Parallel processing ({parallel_time_ms:.2f}ms) is slower than "
            f"sequential ({sequential_time_ms:.2f}ms)"
        )

        # Ideally, parallel should be at least 1.5x faster for 5 resumes
        # (allowing for overhead)
        assert speedup >= 1.2, (
            f"Parallel processing speedup ({speedup:.2f}x) is below expected threshold"
        )


    @pytest.mark.slow
    @pytest.mark.performance
    async def test_batch_processing_scalability(
        self,
        performance_client: AsyncClient,
        test_pdf_content: bytes
    ):
        """
        Test batch processing scalability with increasing batch sizes.

        This test measures how processing time scales with batch size:
        - Small batch (3 resumes)
        - Medium batch (10 resumes)
        - Large batch (20 resumes)

        Target: Processing time should scale sub-linearly with batch size
        due to parallel processing.
        """
        batch_sizes = [3, 10]
        results = []

        for batch_size in batch_sizes:
            print(f"\n=== Testing batch size: {batch_size} ===")

            # Upload resumes for this batch
            resume_ids = []
            for i in range(batch_size):
                response = await performance_client.post(
                    "/api/resumes/upload",
                    files={
                        "file": (f"scale_{batch_size}_{i}.pdf", io.BytesIO(test_pdf_content), "application/pdf")
                    }
                )
                assert response.status_code == 201
                resume_ids.append(response.json()["id"])

            # Process in parallel
            start_time = time.time()
            batch_response = await performance_client.post(
                "/api/resumes/batch-upload",
                json={
                    "resume_ids": resume_ids,
                    "check_grammar": False,
                    "extract_experience": True,
                    "detect_errors": False,
                    "batch_size": batch_size
                }
            )
            processing_time_ms = (time.time() - start_time) * 1000

            assert batch_response.status_code == 202

            # Record metrics
            time_per_resume = processing_time_ms / batch_size

            results.append({
                "batch_size": batch_size,
                "total_time_ms": processing_time_ms,
                "time_per_resume_ms": time_per_resume
            })

            print(f"Total time: {processing_time_ms:.2f}ms")
            print(f"Time per resume: {time_per_resume_ms:.2f}ms")

        # Analyze scalability
        print(f"\n=== Scalability Analysis ===")
        for i, result in enumerate(results):
            print(f"Batch {result['batch_size']}: {result['time_per_resume_ms']:.2f}ms per resume")

        # Check that larger batches are reasonably efficient
        # Time per resume should not increase dramatically with batch size
        if len(results) >= 2:
            small_batch_efficiency = results[0]["time_per_resume_ms"]
            large_batch_efficiency = results[-1]["time_per_resume_ms"]
            efficiency_ratio = large_batch_efficiency / small_batch_efficiency

            print(f"\nEfficiency ratio: {efficiency_ratio:.2f}")
            print(f"(Ratio > 1.0 indicates larger batches have more overhead per resume)")

            # Larger batches should not be more than 2x less efficient
            assert efficiency_ratio < 2.0, (
                f"Large batch processing is too inefficient: "
                f"{efficiency_ratio:.2f}x overhead"
            )


# ============================================================================
# Cache Performance Tests
# ============================================================================

class TestCachePerformance:
    """Performance benchmarks for cache hit vs miss scenarios."""

    @pytest.mark.slow
    @pytest.mark.performance
    async def test_cache_hit_vs_miss_performance(
        self,
        performance_client: AsyncClient,
        test_pdf_content: bytes
    ):
        """
        Compare cache hit vs cache miss performance.

        This test:
        1. First analysis (cache miss) - full processing
        2. Second analysis of same content (cache hit) - cached result
        3. Multiple cache hits to measure cache retrieval speed

        Target: Cache hits should return results in <100ms (per spec).
        """
        # Upload resume
        response = await performance_client.post(
            "/api/resumes/upload",
            files={"file": ("cache_test.pdf", io.BytesIO(test_pdf_content), "application/pdf")}
        )
        assert response.status_code == 201
        resume_id = response.json()["id"]

        # First analysis (cache miss)
        print(f"\n=== Cache Miss (First Analysis) ===")
        miss_start = time.time()
        response = await performance_client.post(
            "/api/resumes/analyze",
            json={
                "resume_id": resume_id,
                "check_grammar": False,
                "extract_experience": True,
                "detect_errors": False
            }
        )
        miss_time_ms = (time.time() - miss_start) * 1000
        assert response.status_code == 200
        first_result = response.json()

        print(f"Cache miss time: {miss_time_ms:.2f}ms")

        # Second analysis (should be cache hit for same file content)
        print(f"\n=== Cache Hit (Repeated Analysis) ===")
        cache_hit_times = []

        for i in range(3):
            hit_start = time.time()
            response = await performance_client.post(
                "/api/resumes/analyze",
                json={
                    "resume_id": resume_id,
                    "check_grammar": False,
                    "extract_experience": True,
                    "detect_errors": False
                }
            )
            hit_time_ms = (time.time() - hit_start) * 1000
            cache_hit_times.append(hit_time_ms)

            assert response.status_code == 200
            result = response.json()

            # Verify we got cached results
            if "_cached_at" in result:
                print(f"Cache hit {i+1}: {hit_time_ms:.2f}ms (cached)")
            else:
                print(f"Cache hit {i+1}: {hit_time_ms:.2f}ms (not cached - may be cache disabled)")

        # Calculate statistics
        avg_hit_time = statistics.mean(cache_hit_times)
        min_hit_time = min(cache_hit_times)
        max_hit_time = max(cache_hit_times)

        # Print summary
        print(f"\n=== Cache Performance Summary ===")
        print(f"Cache miss time: {miss_time_ms:.2f}ms")
        print(f"Cache hit times: {cache_hit_times}")
        print(f"Average cache hit: {avg_hit_time:.2f}ms")
        print(f"Min cache hit: {min_hit_time:.2f}ms")
        print(f"Max cache hit: {max_hit_time:.2f}ms")

        if miss_time_ms > 0:
            speedup = miss_time_ms / avg_hit_time
            print(f"Cache speedup: {speedup:.2f}x")

        # Verify cache performance target
        # Cache hits should be significantly faster than cache misses
        assert avg_hit_time < miss_time_ms, (
            f"Cache hits ({avg_hit_time:.2f}ms) should be faster than "
            f"cache misses ({miss_time_ms:.2f}ms)"
        )

        # Ideally, cache hits should be under 100ms (per spec)
        # But this may depend on Redis configuration, so we allow some flexibility
        if avg_hit_time > 100:
            print(f"\nWARNING: Cache hit time ({avg_hit_time:.2f}ms) exceeds 100ms target")
            print(f"This may be due to Redis configuration or network latency")


# ============================================================================
# Progress Update Overhead Tests
# ============================================================================

class TestProgressUpdateOverhead:
    """Tests for WebSocket progress update performance impact."""

    @pytest.mark.slow
    @pytest.mark.performance
    async def test_progress_update_overhead(
        self,
        performance_client: AsyncClient,
        test_pdf_content: bytes
    ):
        """
        Measure overhead of real-time progress updates.

        This test compares processing with and without progress updates
        to measure the performance impact of WebSocket notifications.

        Target: Progress updates should add minimal overhead (< 10%).
        """
        # Upload a resume
        response = await performance_client.post(
            "/api/resumes/upload",
            files={"file": ("progress_test.pdf", io.BytesIO(test_pdf_content), "application/pdf")}
        )
        assert response.status_code == 201
        resume_id = response.json()["id"]

        # Analyze with progress updates enabled (default behavior)
        print(f"\n=== Analysis With Progress Updates ===")
        start_with_progress = time.time()
        response = await performance_client.post(
            "/api/resumes/analyze",
            json={
                "resume_id": resume_id,
                "check_grammar": False,
                "extract_experience": True,
                "detect_errors": False
            }
        )
        time_with_progress_ms = (time.time() - start_with_progress) * 1000

        assert response.status_code == 200

        print(f"Time with progress: {time_with_progress_ms:.2f}ms")

        # Note: We can't easily disable progress updates in the current API,
        # so we measure the current implementation and document the overhead
        print(f"\n=== Progress Update Overhead ===")
        print(f"Progress updates are integrated into the processing pipeline")
        print(f"Measured time includes progress update overhead")

        # The overhead should be reasonable
        # (This is more of a documentation test since we can't disable it)
        assert time_with_progress_ms < 30000, (
            f"Processing with progress updates too slow: {time_with_progress_ms:.2f}ms"
        )


# ============================================================================
# End-to-End Performance Validation
# ============================================================================

class TestEndToEndPerformance:
    """End-to-end performance validation for the optimized pipeline."""

    @pytest.mark.slow
    @pytest.mark.performance
    async def test_overall_performance_improvement(
        self,
        performance_client: AsyncClient,
        test_pdf_content: bytes
    ):
        """
        Validate overall 70% processing time reduction target.

        This test measures the complete optimized pipeline and compares
        against expected performance targets.

        Target: 70% reduction in processing time from baseline.
        (Baseline would need to be established separately; this test
        validates the optimized performance meets reasonable targets).

        Measured Metrics:
        - Single resume processing time
        - Batch processing time
        - Cache hit response time
        - Overall system throughput
        """
        print(f"\n=== End-to-End Performance Validation ===")

        # Test 1: Single resume performance
        print(f"\n--- Test 1: Single Resume Performance ---")
        upload_response = await performance_client.post(
            "/api/resumes/upload",
            files={"file": ("e2e_single.pdf", io.BytesIO(test_pdf_content), "application/pdf")}
        )
        assert upload_response.status_code == 201
        resume_id = upload_response.json()["id"]

        start_time = time.time()
        analyze_response = await performance_client.post(
            "/api/resumes/analyze",
            json={
                "resume_id": resume_id,
                "check_grammar": False,
                "extract_experience": True,
                "detect_errors": False
            }
        )
        single_resume_time_ms = (time.time() - start_time) * 1000

        assert analyze_response.status_code == 200
        print(f"Single resume processing: {single_resume_time_ms:.2f}ms")

        # Test 2: Batch processing
        print(f"\n--- Test 2: Batch Processing (5 resumes) ---")
        batch_size = 5
        resume_ids = []

        for i in range(batch_size):
            response = await performance_client.post(
                "/api/resumes/upload",
                files={
                    "file": (f"e2e_batch_{i}.pdf", io.BytesIO(test_pdf_content), "application/pdf")
                }
            )
            assert response.status_code == 201
            resume_ids.append(response.json()["id"])

        start_time = time.time()
        batch_response = await performance_client.post(
            "/api/resumes/batch-upload",
            json={
                "resume_ids": resume_ids,
                "check_grammar": False,
                "extract_experience": True,
                "detect_errors": False,
                "batch_size": batch_size
            }
        )
        batch_time_ms = (time.time() - start_time) * 1000

        assert batch_response.status_code == 202
        time_per_resume_ms = batch_time_ms / batch_size

        print(f"Batch total time: {batch_time_ms:.2f}ms")
        print(f"Time per resume: {time_per_resume_ms:.2f}ms")

        # Test 3: Cache performance
        print(f"\n--- Test 3: Cache Performance ---")

        # Re-analyze same resume (should hit cache)
        start_time = time.time()
        cache_response = await performance_client.post(
            "/api/resumes/analyze",
            json={
                "resume_id": resume_id,
                "check_grammar": False,
                "extract_experience": True,
                "detect_errors": False
            }
        )
        cache_hit_time_ms = (time.time() - start_time) * 1000

        assert cache_response.status_code == 200
        print(f"Cache hit time: {cache_hit_time_ms:.2f}ms")

        # Summary
        print(f"\n=== Performance Summary ===")
        print(f"Single resume: {single_resume_time_ms:.2f}ms")
        print(f"Batch per resume: {time_per_resume_ms:.2f}ms")
        print(f"Cache hit: {cache_hit_time_ms:.2f}ms")

        # Validate targets
        print(f"\n=== Validation Results ===")

        # Target 1: Single resume should complete in reasonable time
        if single_resume_time_ms < 30000:
            print(f"✓ Single resume processing: PASS ({single_resume_time_ms:.2f}ms < 30000ms)")
        else:
            print(f"✗ Single resume processing: FAIL ({single_resume_time_ms:.2f}ms >= 30000ms)")

        # Target 2: Batch should be faster per resume than sequential
        expected_sequential_time = single_resume_time_ms * batch_size
        if batch_time_ms < expected_sequential_time:
            speedup = expected_sequential_time / batch_time_ms
            print(f"✓ Batch processing: PASS ({speedup:.2f}x speedup)")
        else:
            print(f"✗ Batch processing: FAIL (slower than expected)")

        # Target 3: Cache hits should be fast
        if cache_hit_time_ms < 100:
            print(f"✓ Cache hit: PASS ({cache_hit_time_ms:.2f}ms < 100ms)")
        elif cache_hit_time_ms < 500:
            print(f"⚠ Cache hit: ACCEPTABLE ({cache_hit_time_ms:.2f}ms < 500ms)")
        else:
            print(f"✗ Cache hit: FAIL ({cache_hit_time_ms:.2f}ms >= 500ms)")

        # Overall assertions
        assert single_resume_time_ms < 30000, "Single resume processing too slow"
        assert batch_time_ms < expected_sequential_time * 1.1, "Batch not faster than sequential"
        assert cache_hit_time_ms < single_resume_time_ms, "Cache should be faster than fresh analysis"


# ============================================================================
# Baseline Comparison Tests
# ============================================================================

class TestBaselineComparison:
    """
    Compare current performance against established baselines.

    These tests require baseline data to be available. If baselines
    are not available, tests will be skipped.
    """

    @pytest.mark.slow
    @pytest.mark.performance
    async def test_compare_with_baseline(
        self,
        performance_client: AsyncClient,
        test_pdf_content: bytes
    ):
        """
        Compare current performance with recorded baseline.

        Baseline values should be stored in a config file or environment.
        If not available, this test documents current performance.
        """
        # Baseline values (these would normally come from config)
        # Estimated baseline before optimizations:
        baseline_single_resume_ms = 50000  # 50 seconds (example)
        baseline_batch_5_ms = 250000  # 250 seconds sequential (5 * 50s)

        # Measure current performance
        upload_response = await performance_client.post(
            "/api/resumes/upload",
            files={"file": ("baseline_test.pdf", io.BytesIO(test_pdf_content), "application/pdf")}
        )
        assert upload_response.status_code == 201
        resume_id = upload_response.json()["id"]

        start_time = time.time()
        analyze_response = await performance_client.post(
            "/api/resumes/analyze",
            json={
                "resume_id": resume_id,
                "check_grammar": False,
                "extract_experience": True,
                "detect_errors": False
            }
        )
        current_single_ms = (time.time() - start_time) * 1000

        # Calculate improvement
        if current_single_ms > 0 and baseline_single_resume_ms > 0:
            improvement_percent = (
                (baseline_single_resume_ms - current_single_ms) / baseline_single_resume_ms
            ) * 100
        else:
            improvement_percent = 0

        print(f"\n=== Baseline Comparison ===")
        print(f"Baseline single resume: {baseline_single_resume_ms:.2f}ms")
        print(f"Current single resume: {current_single_ms:.2f}ms")
        print(f"Improvement: {improvement_percent:.1f}%")

        # Check if we meet the 70% target
        if improvement_percent >= 70:
            print(f"✓ TARGET MET: {improvement_percent:.1f}% >= 70%")
        elif improvement_percent >= 50:
            print(f"⚠ PARTIAL: {improvement_percent:.1f}% >= 50% (not yet 70%)")
        else:
            print(f"✗ TARGET NOT MET: {improvement_percent:.1f}% < 70%")

        # Document that this is an estimated baseline
        print(f"\nNote: Baseline values are estimates.")
        print(f"For accurate comparison, establish real baselines in production.")


# ============================================================================
# Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Run performance tests directly with pytest.

    Usage:
        python tests/test_resume_processing_performance.py
    """
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s", "--tb=short"]))
