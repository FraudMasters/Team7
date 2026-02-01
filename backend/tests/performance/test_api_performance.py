"""
API performance benchmarks using pytest-benchmark.

This test suite benchmarks critical API endpoints to ensure they meet
performance SLAs and detect regressions early.

Performance Targets:
- Candidate list (100 items): < 200ms p95
- Candidate detail: < 50ms p95
- Match results (50 candidates): < 500ms p95
- Analytics key metrics: < 300ms p95

Cache Effectiveness:
- Cached requests should be >10x faster than uncached
- Cache hit rate should be >70% in production
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
from unittest.mock import patch, Mock

from models.resume import Resume
from models.hiring_stage import HiringStage, HiringStageName
from models.vacancy import Vacancy
from models.match_result import MatchResult
from services.cache_service import get_cache_service, CacheService


@pytest.mark.benchmark(group="candidate_list")
@pytest.mark.asyncio
async def test_get_candidates_list_performance(
    benchmark, async_client: AsyncClient, db_session: AsyncSession
):
    """
    Benchmark GET /api/candidates/ endpoint.

    Target: < 200ms p95 for 100 candidates
    Regression threshold: +20% slowdown
    """
    # Setup: Create 100 candidates
    resumes = []
    stages = []
    for i in range(100):
        resume = Resume(
            filename=f"candidate_{i}.pdf",
            file_path=f"/test/candidate_{i}.pdf"
        )
        resumes.append(resume)
        db_session.add(resume)

    await db_session.commit()

    for resume in resumes:
        await db_session.refresh(resume)
        stage = HiringStage(
            resume_id=resume.id,
            stage_name=HiringStageName.APPLIED.value
        )
        stages.append(stage)
        db_session.add(stage)

    await db_session.commit()

    # Benchmark the endpoint
    result = await benchmark(async_client.get, "/api/candidates/?limit=100")

    assert result.status_code == 200
    candidates = result.json()
    assert len(candidates) == 100


@pytest.mark.benchmark(group="candidate_list_cached")
@pytest.mark.asyncio
async def test_get_candidates_list_cached_performance(
    benchmark, async_client: AsyncClient, db_session: AsyncSession
):
    """
    Benchmark cached GET /api/candidates/ endpoint.

    Target: < 20ms p95 for cached response (should be >10x faster)
    Regression threshold: +20% slowdown
    """
    # Setup: Create candidates
    resumes = []
    for i in range(50):
        resume = Resume(
            filename=f"cached_candidate_{i}.pdf",
            file_path=f"/test/cached_{i}.pdf"
        )
        resumes.append(resume)
        db_session.add(resume)

    await db_session.commit()

    for resume in resumes:
        await db_session.refresh(resume)
        stage = HiringStage(
            resume_id=resume.id,
            stage_name=HiringStageName.APPLIED.value
        )
        db_session.add(stage)

    await db_session.commit()

    # Prime the cache by making first request
    await async_client.get("/api/candidates/?limit=50")

    # Benchmark the cached endpoint
    result = await benchmark(async_client.get, "/api/candidates/?limit=50")

    assert result.status_code == 200
    candidates = result.json()
    assert len(candidates) == 50


@pytest.mark.benchmark(group="candidate_detail")
@pytest.mark.asyncio
async def test_get_candidate_detail_performance(
    benchmark, async_client: AsyncClient, db_session: AsyncSession
):
    """
    Benchmark GET /api/candidates/{id} endpoint.

    Target: < 50ms p95
    Regression threshold: +20% slowdown
    """
    # Setup: Create a candidate with full details
    resume = Resume(
        filename="detailed_candidate.pdf",
        file_path="/test/detailed.pdf",
        parsed_data={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience": [
                {
                    "title": "Senior Developer",
                    "company": "Tech Corp",
                    "years": 5
                }
            ]
        }
    )
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)

    stage = HiringStage(
        resume_id=resume.id,
        stage_name=HiringStageName.INTERVIEW.value
    )
    db_session.add(stage)
    await db_session.commit()

    # Benchmark the endpoint
    result = await benchmark(async_client.get, f"/api/candidates/{resume.id}")

    assert result.status_code == 200
    candidate = result.json()
    assert candidate["id"] == str(resume.id)


@pytest.mark.benchmark(group="candidate_filter")
@pytest.mark.asyncio
async def test_filter_candidates_by_stage_performance(
    benchmark, async_client: AsyncClient, db_session: AsyncSession
):
    """
    Benchmark GET /api/candidates/?stage_id={stage} endpoint.

    Target: < 150ms p95 for filtered results
    Regression threshold: +20% slowdown
    """
    # Setup: Create candidates in different stages
    resumes = []
    for i in range(50):
        resume = Resume(
            filename=f"filter_candidate_{i}.pdf",
            file_path=f"/test/filter_{i}.pdf"
        )
        resumes.append(resume)
        db_session.add(resume)

    await db_session.commit()

    for i, resume in enumerate(resumes):
        await db_session.refresh(resume)
        stage_name = (
            HiringStageName.INTERVIEW.value
            if i % 2 == 0
            else HiringStageName.APPLIED.value
        )
        stage = HiringStage(
            resume_id=resume.id,
            stage_name=stage_name
        )
        db_session.add(stage)

    await db_session.commit()

    # Benchmark filtering by interview stage
    result = await benchmark(
        async_client.get,
        "/api/candidates/?stage_id=interview"
    )

    assert result.status_code == 200
    candidates = result.json()
    assert all(c["current_stage"] == "interview" for c in candidates)


@pytest.mark.benchmark(group="candidate_search")
@pytest.mark.asyncio
async def test_search_candidates_performance(
    benchmark, async_client: AsyncClient, db_session: AsyncSession
):
    """
    Benchmark GET /api/candidates/?search={query} endpoint.

    Target: < 180ms p95 for search across 100 candidates
    Regression threshold: +20% slowdown
    """
    # Setup: Create candidates with searchable names
    names = [
        "John Smith",
        "Jane Doe",
        "Bob Johnson",
        "Alice Williams",
        "Charlie Brown"
    ]

    resumes = []
    for name in names:
        for i in range(20):
            resume = Resume(
                filename=f"{name}_{i}.pdf",
                file_path=f"/test/{name}_{i}.pdf"
            )
            resumes.append(resume)
            db_session.add(resume)

    await db_session.commit()

    for resume in resumes:
        await db_session.refresh(resume)
        stage = HiringStage(
            resume_id=resume.id,
            stage_name=HiringStageName.APPLIED.value
        )
        db_session.add(stage)

    await db_session.commit()

    # Benchmark search
    result = await benchmark(async_client.get, "/api/candidates/?search=John")

    assert result.status_code == 200
    candidates = result.json()
    assert all("John" in c["filename"] for c in candidates)


@pytest.mark.benchmark(group="match_results")
@pytest.mark.asyncio
async def test_get_match_results_performance(
    benchmark, async_client: AsyncClient, db_session: AsyncSession
):
    """
    Benchmark GET /api/vacancies/{id}/matches endpoint.

    Target: < 500ms p95 for 50 match results
    Regression threshold: +20% slowdown
    """
    # Setup: Create vacancy and match results
    vacancy = Vacancy(
        title="Software Engineer",
        description="Python developer position",
        location="Remote",
        required_skills=["Python", "FastAPI", "SQL"]
    )
    db_session.add(vacancy)
    await db_session.commit()
    await db_session.refresh(vacancy)

    # Create match results
    for i in range(50):
        resume = Resume(
            filename=f"match_candidate_{i}.pdf",
            file_path=f"/test/match_{i}.pdf"
        )
        db_session.add(resume)
        await db_session.commit()
        await db_session.refresh(resume)

        match = MatchResult(
            vacancy_id=vacancy.id,
            resume_id=resume.id,
            match_score=0.5 + (i * 0.01),
            skill_match_score=0.6 + (i * 0.008),
            experience_match_score=0.4 + (i * 0.012),
            rank=i + 1
        )
        db_session.add(match)

    await db_session.commit()

    # Benchmark the endpoint
    result = await benchmark(
        async_client.get,
        f"/api/vacancies/{vacancy.id}/matches"
    )

    assert result.status_code == 200
    matches = result.json()
    assert len(matches) == 50


@pytest.mark.benchmark(group="analytics")
@pytest.mark.asyncio
async def test_analytics_key_metrics_performance(
    benchmark, async_client: AsyncClient, db_session: AsyncSession
):
    """
    Benchmark GET /api/analytics/key-metrics endpoint.

    Target: < 300ms p95
    Regression threshold: +20% slowdown
    """
    # Setup: Create some analytics data
    for i in range(10):
        resume = Resume(
            filename=f"analytics_candidate_{i}.pdf",
            file_path=f"/test/analytics_{i}.pdf"
        )
        db_session.add(resume)
        await db_session.commit()
        await db_session.refresh(resume)

        stage = HiringStage(
            resume_id=resume.id,
            stage_name=list(HiringStageName)[i % 5].value
        )
        db_session.add(stage)

    await db_session.commit()

    # Benchmark the endpoint
    result = await benchmark(async_client.get, "/api/analytics/key-metrics")

    assert result.status_code == 200
    metrics = result.json()
    assert "total_candidates" in metrics


@pytest.mark.benchmark(group="cache_operations")
def test_cache_set_performance(benchmark):
    """
    Benchmark cache SET operation.

    Target: < 5ms p95 for simple key-value set
    Regression threshold: +20% slowdown
    """
    cache = get_cache_service()
    test_data = {"name": "John Doe", "age": 30, "skills": ["Python", "Go"]}

    # Benchmark cache set
    benchmark(
        cache.set,
        CacheService.NAMESPACE_CANDIDATE,
        "test_key",
        test_data,
        3600
    )


@pytest.mark.benchmark(group="cache_operations")
def test_cache_get_performance(benchmark):
    """
    Benchmark cache GET operation.

    Target: < 5ms p95 for simple key-value get
    Regression threshold: +20% slowdown
    """
    cache = get_cache_service()
    test_key = "bench_test_key"
    test_data = {"name": "Jane Doe", "age": 28, "skills": ["React", "TypeScript"]}

    # Setup: Put data in cache
    cache.set(CacheService.NAMESPACE_CANDIDATE, test_key, test_data, 3600)

    # Benchmark cache get
    result = benchmark(
        cache.get,
        CacheService.NAMESPACE_CANDIDATE,
        test_key
    )

    assert result is not None
    assert result["name"] == "Jane Doe"


@pytest.mark.benchmark(group="cache_operations")
def test_cache_invalidate_performance(benchmark):
    """
    Benchmark cache invalidation operation.

    Target: < 10ms p95 for pattern-based invalidation
    Regression threshold: +20% slowdown
    """
    cache = get_cache_service()

    # Setup: Create multiple cache entries
    for i in range(10):
        cache.set(
            CacheService.NAMESPACE_CANDIDATE,
            f"test_{i}",
            {"id": i},
            3600
        )

    # Benchmark cache invalidation
    benchmark(
        cache.invalidate_pattern,
        f"{cache.key_prefix}:{CacheService.NAMESPACE_CANDIDATE}:test_*"
    )


@pytest.mark.benchmark(group="pagination")
@pytest.mark.asyncio
async def test_pagination_performance(benchmark, async_client: AsyncClient, db_session: AsyncSession):
    """
    Benchmark pagination performance with large dataset.

    Target: < 100ms p95 per page
    Regression threshold: +20% slowdown
    """
    # Setup: Create 500 candidates
    for i in range(500):
        resume = Resume(
            filename=f"page_candidate_{i}.pdf",
            file_path=f"/test/page_{i}.pdf"
        )
        db_session.add(resume)

    await db_session.commit()

    for i in range(500):
        resume = Resume(filename=f"page_candidate_{i}.pdf", file_path=f"/test/page_{i}.pdf")
        result = await db_session.execute(select(Resume).filter_by(filename=resume.filename))
        resume_obj = result.scalar_one()
        stage = HiringStage(
            resume_id=resume_obj.id,
            stage_name=HiringStageName.APPLIED.value
        )
        db_session.add(stage)

    await db_session.commit()

    # Benchmark different page sizes
    page_sizes = [20, 50, 100]
    for page_size in page_sizes:
        result = await benchmark(
            async_client.get,
            f"/api/candidates/?skip=0&limit={page_size}"
        )
        assert result.status_code == 200
        candidates = result.json()
        assert len(candidates) == page_size


@pytest.mark.benchmark(group="concurrent_requests")
@pytest.mark.asyncio
async def test_concurrent_requests_performance(async_client: AsyncClient, db_session: AsyncSession):
    """
    Test performance under concurrent load.

    Target: Handle 10 concurrent requests without significant degradation
    """
    import asyncio

    # Setup: Create candidates
    for i in range(100):
        resume = Resume(
            filename=f"concurrent_{i}.pdf",
            file_path=f"/test/concurrent_{i}.pdf"
        )
        db_session.add(resume)

    await db_session.commit()

    for i in range(100):
        resume = Resume(filename=f"concurrent_{i}.pdf", file_path=f"/test/concurrent_{i}.pdf")
        result = await db_session.execute(select(Resume).filter_by(filename=resume.filename))
        resume_obj = result.scalar_one()
        stage = HiringStage(
            resume_id=resume_obj.id,
            stage_name=HiringStageName.APPLIED.value
        )
        db_session.add(stage)

    await db_session.commit()

    # Make concurrent requests
    async def make_request(client):
        response = await client.get("/api/candidates/?limit=10")
        return response

    # Benchmark 10 concurrent requests
    tasks = [make_request(async_client) for _ in range(10)]
    responses = await asyncio.gather(*tasks)

    # All requests should succeed
    assert all(r.status_code == 200 for r in responses)
    assert all(len(r.json()) == 10 for r in responses)


# Performance regression detection helpers
class PerformanceRegressionDetector:
    """Helper class to detect performance regressions."""

    @staticmethod
    def check_regression(current_metrics, baseline_metrics, threshold=0.20):
        """
        Check if current metrics show regression compared to baseline.

        Args:
            current_metrics: Dict of current benchmark results
            baseline_metrics: Dict of baseline benchmark results
            threshold: Maximum acceptable degradation (default 20%)

        Returns:
            Dict with regression detection results
        """
        regressions = []

        for key, current_value in current_metrics.items():
            if key in baseline_metrics:
                baseline_value = baseline_metrics[key]
                if baseline_value > 0:
                    degradation = (current_value - baseline_value) / baseline_value
                    if degradation > threshold:
                        regressions.append({
                            "metric": key,
                            "current": current_value,
                            "baseline": baseline_value,
                            "degradation": degradation
                        })

        return {
            "has_regression": len(regressions) > 0,
            "regressions": regressions
        }
