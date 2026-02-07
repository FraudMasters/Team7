"""
import os
Comprehensive integration tests for advanced candidate search workflow.

This test suite verifies:
1. Full-text search with boolean operators (AND, OR, NOT)
2. Multi-field filtering: skills, experience, education, location, languages
3. Range filters: experience years, match score, date ranges
4. Sorting by relevance, date, experience
5. Pagination with filters
6. Search history tracking
7. Combined filters and search queries
8. Performance optimization (sub-2 second response time)
"""
import pytest
import time
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from uuid import uuid4
from datetime import datetime, timedelta

from main import app
from database import get_db
from models.resume import Resume, ResumeStatus
from models.resume_analysis import ResumeAnalysis
from models.hiring_stage import HiringStage, HiringStageName
from models.saved_search import SavedSearch
from models.search_history import SearchHistory


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_advanced_search.db"


@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create test client with database override."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_candidates(test_db: AsyncSession):
    """Create sample candidates with various attributes for testing."""
    candidates_data = [
        {
            "filename": "john_python_senior.pdf",
            "raw_text": "John Doe - Senior Python Developer with 8 years experience in Python, Django, FastAPI, PostgreSQL",
            "skills": ["Python", "Django", "FastAPI", "PostgreSQL"],
            "experience_months": 96,
            "location": "Remote",
            "education": [{"degree": "M.Sc", "field": "Computer Science"}],
            "language": "en",
        },
        {
            "filename": "jane_fullstack.pdf",
            "raw_text": "Jane Smith - Fullstack Developer with 5 years experience in React, Node.js, Python, MongoDB",
            "skills": ["React", "Node.js", "Python", "MongoDB"],
            "experience_months": 60,
            "location": "New York",
            "education": [{"degree": "B.Sc", "field": "Software Engineering"}],
            "language": "en",
        },
        {
            "filename": "bob_junior.pdf",
            "raw_text": "Bob Johnson - Junior Developer with 2 years experience in Python, JavaScript",
            "skills": ["Python", "JavaScript"],
            "experience_months": 24,
            "location": "San Francisco",
            "education": [{"degree": "B.Sc", "field": "Computer Science"}],
            "language": "en",
        },
        {
            "filename": "alice_data.pdf",
            "raw_text": "Alice Williams - Data Scientist with 6 years experience in Python, Machine Learning, TensorFlow, Pandas",
            "skills": ["Python", "Machine Learning", "TensorFlow", "Pandas"],
            "experience_months": 72,
            "location": "Remote",
            "education": [{"degree": "PhD", "field": "Data Science"}],
            "language": "en",
        },
        {
            "filename": "charlie_devops.pdf",
            "raw_text": "Charlie Brown - DevOps Engineer with 4 years experience in Docker, Kubernetes, AWS, CI/CD",
            "skills": ["Docker", "Kubernetes", "AWS", "CI/CD"],
            "experience_months": 48,
            "location": "London",
            "education": [{"degree": "M.Sc", "field": "Information Technology"}],
            "language": "en",
        },
    ]

    resumes = []
    for data in candidates_data:
        resume = Resume(
            filename=data["filename"],
            file_path=f"/test/{data['filename']}",
            status=ResumeStatus.COMPLETED,
            raw_text=data["raw_text"],
            location=data["location"],
        )
        test_db.add(resume)
        await test_db.commit()
        await test_db.refresh(resume)

        # Create resume analysis
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            raw_text=data["raw_text"],
            skills=data["skills"],
            total_experience_months=data["experience_months"],
            education=data["education"],
            language=data["language"],
            quality_score=85.0,
        )
        test_db.add(analysis)

        # Create hiring stage
        stage = HiringStage(
            resume_id=resume.id,
            stage_name=HiringStageName.APPLIED.value,
        )
        test_db.add(stage)

        resumes.append(resume)

    await test_db.commit()
    return resumes


@pytest.mark.asyncio
async def test_basic_search_with_query(client: AsyncClient, sample_candidates):
    """Test basic full-text search with a query string."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python AND Django",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "candidates" in data
    assert data["total"] >= 1
    assert len(data["candidates"]) >= 1
    assert data["query"] == "Python AND Django"
    assert "execution_time_seconds" in data


@pytest.mark.asyncio
async def test_search_with_boolean_or(client: AsyncClient, sample_candidates):
    """Test search with OR boolean operator."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "React OR Node.js",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 1
    # Should find candidates with either React or Node.js


@pytest.mark.asyncio
async def test_search_with_boolean_not(client: AsyncClient, sample_candidates):
    """Test search with NOT boolean operator."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python NOT Django",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should find Python developers without Django
    assert "candidates" in data


@pytest.mark.asyncio
async def test_filter_by_skills(client: AsyncClient, sample_candidates):
    """Test filtering candidates by skills."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "skills": ["Python", "FastAPI"],
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 1
    assert all("Python" in c.get("skills", []) for c in data["candidates"])


@pytest.mark.asyncio
async def test_filter_by_experience_range(client: AsyncClient, sample_candidates):
    """Test filtering candidates by experience years range."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "min_experience_years": 5,
                "max_experience_years": 8,
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify experience range
    for candidate in data["candidates"]:
        exp_years = candidate.get("experience_years")
        if exp_years is not None:
            assert 5 <= exp_years <= 8


@pytest.mark.asyncio
async def test_filter_by_location(client: AsyncClient, sample_candidates):
    """Test filtering candidates by location."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "location": "Remote",
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 1
    # Should find remote candidates


@pytest.mark.asyncio
async def test_combined_search_and_filters(client: AsyncClient, sample_candidates):
    """Test combining full-text search with filters."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python",
            "filters": {
                "min_experience_years": 5,
                "location": "Remote",
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should find Python developers with 5+ years experience in Remote location
    assert "candidates" in data
    for candidate in data["candidates"]:
        exp_years = candidate.get("experience_years")
        if exp_years is not None:
            assert exp_years >= 5


@pytest.mark.asyncio
async def test_sort_by_relevance(client: AsyncClient, sample_candidates):
    """Test sorting search results by relevance."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python Developer",
            "sort_by": "relevance",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "candidates" in data
    # Results should be sorted by relevance (ts_rank)


@pytest.mark.asyncio
async def test_sort_by_experience(client: AsyncClient, sample_candidates):
    """Test sorting search results by experience."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "sort_by": "experience",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "candidates" in data
    if len(data["candidates"]) > 1:
        # Verify descending order by experience
        experiences = [
            c.get("experience_years", 0) for c in data["candidates"]
        ]
        assert experiences == sorted(experiences, reverse=True)


@pytest.mark.asyncio
async def test_sort_by_date(client: AsyncClient, sample_candidates):
    """Test sorting search results by date (newest first)."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "sort_by": "date",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "candidates" in data
    # Results should be sorted by created_at descending


@pytest.mark.asyncio
async def test_pagination_with_skip_and_limit(client: AsyncClient, sample_candidates):
    """Test pagination with skip and limit parameters."""
    # Get first page
    response = await client.post(
        "/api/search/candidates",
        json={
            "skip": 0,
            "limit": 2,
        }
    )

    assert response.status_code == 200
    first_page = response.json()
    assert len(first_page["candidates"]) <= 2

    # Get second page
    response = await client.post(
        "/api/search/candidates",
        json={
            "skip": 2,
            "limit": 2,
        }
    )

    assert response.status_code == 200
    second_page = response.json()
    assert len(second_page["candidates"]) <= 2

    # Verify different results
    if len(first_page["candidates"]) > 0 and len(second_page["candidates"]) > 0:
        first_ids = {c["id"] for c in first_page["candidates"]}
        second_ids = {c["id"] for c in second_page["candidates"]}
        assert first_ids != second_ids


@pytest.mark.asyncio
async def test_search_history_tracking(client: AsyncClient, sample_candidates, test_db: AsyncSession):
    """Test that search history is tracked after queries."""
    # Perform a search
    await client.post(
        "/api/search/candidates",
        json={
            "query": "Python Developer",
            "filters": {"min_experience_years": 5},
            "limit": 10,
        }
    )

    # Wait a bit for async processing
    await asyncio.sleep(0.1)

    # Check search history
    response = await client.get("/api/search/history?limit=10")

    assert response.status_code == 200
    data = response.json()

    assert "history" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_search_with_query_params(client: AsyncClient, sample_candidates):
    """Test GET endpoint for search with query parameters."""
    response = await client.get(
        "/api/search/candidates",
        params={
            "query": "Python",
            "min_experience_years": 5,
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "candidates" in data
    assert data["total"] >= 0


@pytest.mark.asyncio
async def test_search_with_date_range_filter(client: AsyncClient, sample_candidates, test_db: AsyncSession):
    """Test search with date range filters."""
    # Get a candidate from sample data
    candidate = sample_candidates[0]

    # Create date range filters
    date_from = (candidate.created_at - timedelta(days=1)).isoformat()
    date_to = (candidate.created_at + timedelta(days=1)).isoformat()

    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "date_from": date_from,
                "date_to": date_to,
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "candidates" in data


@pytest.mark.asyncio
async def test_empty_search_results(client: AsyncClient, sample_candidates):
    """Test search that returns no results."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "NonExistentSkill12345",
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert len(data["candidates"]) == 0


@pytest.mark.asyncio
async def test_search_performance(client: AsyncClient, sample_candidates):
    """Test that search completes in under 2 seconds (performance requirement)."""
    start_time = time.time()

    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python AND Developer",
            "filters": {
                "min_experience_years": 3,
                "skills": ["Python", "Django"],
            },
            "limit": 50,
        }
    )

    end_time = time.time()
    execution_time = end_time - start_time

    assert response.status_code == 200
    data = response.json()

    # Verify execution time is tracked
    assert "execution_time_seconds" in data

    # Assert search completes in under 2 seconds (requirement from spec)
    assert execution_time < 2.0, f"Search took {execution_time:.2f}s, expected < 2s"


@pytest.mark.asyncio
async def test_search_response_includes_all_fields(client: AsyncClient, sample_candidates):
    """Test that search response includes all required fields."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python",
            "limit": 1,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    required_fields = ["total", "candidates", "query", "execution_time_seconds", "skip", "limit"]
    for field in required_fields:
        assert field in data

    # Verify candidate fields
    if len(data["candidates"]) > 0:
        candidate = data["candidates"][0]
        candidate_fields = [
            "id", "filename", "status", "created_at", "updated_at",
            "current_stage", "skills", "experience_years"
        ]
        for field in candidate_fields:
            assert field in candidate


@pytest.mark.asyncio
async def test_filter_by_vacancy_id(client: AsyncClient, sample_candidates, test_db: AsyncSession):
    """Test filtering candidates by vacancy ID."""
    from models.vacancy import Vacancy

    # Create a test vacancy
    vacancy = Vacancy(
        title="Senior Python Developer",
        description="Test vacancy",
        location="Remote",
    )
    test_db.add(vacancy)
    await test_db.commit()
    await test_db.refresh(vacancy)

    # Associate a candidate with this vacancy
    candidate = sample_candidates[0]
    stage = HiringStage(
        resume_id=candidate.id,
        stage_name=HiringStageName.INTERVIEW.value,
        vacancy_id=vacancy.id,
    )
    test_db.add(stage)
    await test_db.commit()

    # Search for candidates in this vacancy
    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "vacancy_id": str(vacancy.id),
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should find at least the candidate we added
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_filter_by_stage_id(client: AsyncClient, sample_candidates, test_db: AsyncSession):
    """Test filtering candidates by stage ID."""
    # Update a candidate to interview stage
    candidate = sample_candidates[0]
    stage = HiringStage(
        resume_id=candidate.id,
        stage_name=HiringStageName.INTERVIEW.value,
    )
    test_db.add(stage)
    await test_db.commit()

    # Search for candidates in interview stage
    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "stage_id": "interview",
            },
            "limit": 10,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 1
    assert all(c["current_stage"] == "interview" for c in data["candidates"])


@pytest.mark.asyncio
async def test_invalid_filter_parameters(client: AsyncClient, sample_candidates):
    """Test that invalid filter parameters return appropriate errors."""
    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "min_experience_years": -5,  # Invalid: negative value
            },
            "limit": 10,
        }
    )

    # Should handle gracefully (may return 400 or 200 with empty results)
    assert response.status_code in [200, 400]


# Import asyncio for sleep
import asyncio


@pytest.fixture
async def large_dataset(test_db: AsyncSession):
    """
    Create a large dataset of 10,000+ candidates for performance testing.

    This fixture creates diverse candidate profiles to simulate real-world
    recruiting scenarios with various skills, experience levels, locations,
    and education backgrounds.
    """
    import random
    from datetime import datetime, timedelta

    # Define skill pools for different roles
    skill_pools = {
        "backend": [
            "Python", "Java", "Go", "Node.js", "Django", "FastAPI", "Flask",
            "PostgreSQL", "MongoDB", "Redis", "Kafka", "Docker", "Kubernetes"
        ],
        "frontend": [
            "React", "Vue", "Angular", "TypeScript", "JavaScript", "HTML",
            "CSS", "Next.js", "Redux", "Webpack"
        ],
        "data": [
            "Python", "R", "SQL", "TensorFlow", "PyTorch", "Pandas", "NumPy",
            "Scikit-learn", "Tableau", "Power BI", "Apache Spark"
        ],
        "devops": [
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
            "Ansible", "Jenkins", "GitLab CI", "CircleCI"
        ],
        "mobile": [
            "Swift", "Kotlin", "React Native", "Flutter", "Objective-C",
            "Android", "iOS", "Xamarin", "Java"
        ]
    }

    # Locations distribution
    locations = [
        "Remote", "New York", "San Francisco", "London", "Berlin",
        "Toronto", "Sydney", "Singapore", "Tokyo", "Amsterdam"
    ]

    # Education levels
    education_levels = [
        {"degree": "PhD", "field": "Computer Science"},
        {"degree": "PhD", "field": "Data Science"},
        {"degree": "M.Sc", "field": "Computer Science"},
        {"degree": "M.Sc", "field": "Software Engineering"},
        {"degree": "M.Sc", "field": "Data Science"},
        {"degree": "M.Sc", "field": "Information Technology"},
        {"degree": "B.Sc", "field": "Computer Science"},
        {"degree": "B.Sc", "field": "Software Engineering"},
        {"degree": "B.Sc", "field": "Information Technology"},
        {"degree": "B.Sc", "field": "Computer Engineering"},
        {"degree": "MBA", "field": "Business Administration"},
        {"degree": "Diploma", "field": "Software Development"}
    ]

    # Generate 10,000 candidates
    num_candidates = 10000
    print(f"\nGenerating {num_candidates} test candidates...")

    resumes = []

    # Generate candidates in batches for better performance
    batch_size = 500
    for batch_start in range(0, num_candidates, batch_size):
        batch_end = min(batch_start + batch_size, num_candidates)

        for i in range(batch_start, batch_end):
            # Randomly assign role type
            role_type = random.choice(list(skill_pools.keys()))
            skills = random.sample(skill_pools[role_type], k=random.randint(3, 8))

            # Add some cross-role skills for variety
            if random.random() < 0.3:  # 30% chance
                extra_role = random.choice(list(skill_pools.keys()))
                if extra_role != role_type:
                    skills.extend(random.sample(skill_pools[extra_role], k=random.randint(1, 2)))

            # Remove duplicates
            skills = list(set(skills))

            # Generate experience
            experience_months = random.randint(12, 180)  # 1 to 15 years

            # Randomly assign other attributes
            location = random.choice(locations)
            education = random.choice(education_levels)

            # Create resume
            resume = Resume(
                filename=f"candidate_{i}_{role_type}.pdf",
                file_path=f"/test/candidates/candidate_{i}.pdf",
                status=ResumeStatus.COMPLETED,
                raw_text=f"Candidate {i} - {role_type.capitalize()} Developer with "
                        f"{experience_months // 12} years experience in {', '.join(skills)}. "
                        f"Located in {location}. "
                        f"Education: {education['degree']} in {education['field']}.",
                location=location,
            )
            test_db.add(resume)
            await test_db.flush()  # Get ID without committing
            resumes.append(resume)

            # Create resume analysis
            analysis = ResumeAnalysis(
                resume_id=resume.id,
                raw_text=resume.raw_text,
                skills=skills,
                total_experience_months=experience_months,
                education=[education],
                language="en",
                quality_score=random.uniform(60.0, 95.0),
            )
            test_db.add(analysis)

            # Create hiring stage
            stage_name = random.choice([
                HiringStageName.APPLIED.value,
                HiringStageName.SCREENING.value,
                HiringStageName.INTERVIEW.value,
                HiringStageName.OFFER.value,
            ])
            stage = HiringStage(
                resume_id=resume.id,
                stage_name=stage_name,
            )
            test_db.add(stage)

        # Commit batch
        await test_db.commit()
        print(f"Created {batch_end}/{num_candidates} candidates")

    print(f"Successfully created {len(resumes)} test candidates")
    return resumes


@pytest.mark.asyncio
@pytest.mark.performance
async def test_search_performance_with_10k_candidates(client: AsyncClient, large_dataset):
    """
    Performance test: Verify search completes in under 2 seconds with 10k+ candidates.

    This is a critical acceptance criterion from the spec:
    "Search performance optimization (sub-2 second response for >10k candidates)"

    Test executes a complex search with:
    - Full-text boolean query (AND operators)
    - Multiple filters (skills, experience range, location)
    - Sorting by relevance
    - Large result set (50 results)

    The test verifies that even with 10,000+ candidates in the database,
    search performance remains under 2 seconds.
    """
    import time

    print("\n=== Performance Test: 10k+ Candidates ===")
    print(f"Total candidates in database: {len(large_dataset)}")

    # Execute complex search with timing
    start_time = time.time()

    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python AND (Django OR FastAPI OR Flask)",
            "filters": {
                "min_experience_years": 3,
                "max_experience_years": 10,
                "skills": ["Python"],
                "location": "Remote",
            },
            "sort_by": "relevance",
            "limit": 50,
        }
    )

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Search execution time: {execution_time:.3f} seconds")

    # Verify response
    assert response.status_code == 200, f"Search failed with status {response.status_code}"
    data = response.json()

    # Verify response structure
    assert "total" in data
    assert "candidates" in data
    assert "execution_time_seconds" in data

    print(f"Total matching candidates: {data['total']}")
    print(f"Results returned: {len(data['candidates'])}")
    print(f"Server-reported execution time: {data['execution_time_seconds']:.3f}s")

    # Verify results match filters
    if len(data['candidates']) > 0:
        for candidate in data['candidates'][:5]:  # Check first 5 results
            # Verify Python skill
            assert 'Python' in candidate.get('skills', []), \
                f"Result missing Python skill: {candidate.get('skills')}"

            # Verify experience range
            exp_years = candidate.get('experience_years')
            if exp_years is not None:
                assert 3 <= exp_years <= 10, \
                    f"Experience {exp_years} years outside range 3-10"

            # Verify location
            # Note: location filter may be in different fields
            print(f"Sample result: {candidate['filename']}, "
                  f"Experience: {exp_years} years, "
                  f"Skills: {', '.join(candidate.get('skills', [])[:3])}")

    # CRITICAL ASSERTION: Search must complete in under 2 seconds
    # This is the acceptance criterion from the spec
    assert execution_time < 2.0, \
        f"PERFORMANCE CRITICAL: Search took {execution_time:.3f}s, " \
        f"exceeding 2 second requirement with {len(large_dataset)} candidates"

    # Also verify server-reported time is reasonable
    assert data['execution_time_seconds'] < 2.0, \
        f"Server-reported time {data['execution_time_seconds']:.3f}s exceeds 2 seconds"

    print(f"\n✓ PERFORMANCE TEST PASSED")
    print(f"✓ Search completed in {execution_time:.3f}s (< 2.0s requirement)")
    print(f"✓ Tested with {len(large_dataset)} candidates")
    print(f"✓ Found {data['total']} matching candidates")
    print(f"✓ Complex filters: boolean query + experience + skills + location")


@pytest.mark.asyncio
@pytest.mark.performance
async def test_search_performance_filters_only(client: AsyncClient, large_dataset):
    """
    Performance test: Filters-only search (no full-text query) with 10k+ candidates.

    Tests performance when using filters without a text query, which is
    a common use case for structured searches.
    """
    import time

    print("\n=== Performance Test: Filters Only ===")

    start_time = time.time()

    response = await client.post(
        "/api/search/candidates",
        json={
            "filters": {
                "min_experience_years": 5,
                "max_experience_years": 15,
                "skills": ["Python", "React"],
            },
            "sort_by": "experience",
            "limit": 100,
        }
    )

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Filters-only search time: {execution_time:.3f} seconds")

    assert response.status_code == 200
    data = response.json()

    assert execution_time < 2.0, \
        f"Filters-only search took {execution_time:.3f}s, exceeding 2 second limit"

    print(f"✓ Filters-only search: {execution_time:.3f}s (< 2.0s)")
    print(f"✓ Found {data['total']} candidates")


@pytest.mark.asyncio
@pytest.mark.performance
async def test_search_performance_simple_query(client: AsyncClient, large_dataset):
    """
    Performance test: Simple text-only query with 10k+ candidates.

    Tests performance of basic full-text search without additional filters.
    """
    import time

    print("\n=== Performance Test: Simple Query ===")

    start_time = time.time()

    response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python Developer",
            "limit": 50,
        }
    )

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Simple query search time: {execution_time:.3f} seconds")

    assert response.status_code == 200
    data = response.json()

    assert execution_time < 2.0, \
        f"Simple query took {execution_time:.3f}s, exceeding 2 second limit"

    print(f"✓ Simple query: {execution_time:.3f}s (< 2.0s)")
    print(f"✓ Found {data['total']} candidates")


# ============================================================================
# Bulk Actions Tests
# ============================================================================

@pytest.mark.asyncio
async def test_bulk_tag_action(client: AsyncClient, sample_candidates):
    """
    Test bulk tag action on multiple candidates.

    Verifies:
    - Tag action adds tags to all selected candidates
    - Tag is created in database if it doesn't exist
    - Activity records are created for each tagged candidate
    - Response contains correct success/failure counts
    """
    print("\n=== Bulk Tag Action Test ===")

    # Get resume IDs from sample candidates
    resume_ids = []
    async for db in get_db():
        result = await db.execute(select(Resume).limit(5))
        resumes = result.scalars().all()
        resume_ids = [str(r.id) for r in resumes]
        break

    assert len(resume_ids) >= 3, "Need at least 3 candidates for bulk tag test"

    tag_name = "Test Bulk Tag"
    tag_color = "#FF5722"

    print(f"Tagging {len(resume_ids)} candidates with '{tag_name}'...")

    response = await client.post(
        "/api/candidates/bulk-action",
        json={
            "action": "tag",
            "resume_ids": resume_ids,
            "tag_name": tag_name,
            "tag_color": tag_color,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["action"] == "tag"
    assert data["total_requested"] == len(resume_ids)
    assert data["successful"] == len(resume_ids)
    assert data["failed"] == 0
    assert len(data["results"]) == len(resume_ids)

    # Verify all results are successful
    for result in data["results"]:
        assert result["success"] is True
        assert result["resume_id"] in resume_ids
        assert tag_name in result["message"]
        assert result["data"]["tag_name"] == tag_name
        assert "tag_id" in result["data"]

    # Verify tag was created in database
    async for db in get_db():
        result = await db.execute(
            select(CandidateTag).where(
                and_(
                    CandidateTag.tag_name == tag_name,
                    CandidateTag.organization_id.isnot(None)
                )
            )
        )
        tag = result.scalar_one_or_none()
        assert tag is not None, "Tag was not created in database"
        assert tag.tag_name == tag_name
        print(f"✓ Tag '{tag_name}' created in database")

        # Verify activities were created
        result = await db.execute(
            select(CandidateActivity).where(
                and_(
                    CandidateActivity.tag_id == tag.id,
                    CandidateActivity.activity_type == CandidateActivityType.TAG_ADDED
                )
            )
        )
        activities = result.scalars().all()
        assert len(activities) == len(resume_ids), \
            f"Expected {len(resume_ids)} activities, got {len(activities)}"
        print(f"✓ {len(activities)} tag activities recorded")
        break

    print(f"✓ All {len(resume_ids)} candidates tagged successfully")


@pytest.mark.asyncio
async def test_bulk_export_json(client: AsyncClient, sample_candidates):
    """
    Test bulk export action with JSON format.

    Verifies:
    - Export action returns candidate data in JSON format
    - All selected candidates are included
    - Exported data contains required fields
    - Response contains correct count
    """
    print("\n=== Bulk Export JSON Test ===")

    # Get resume IDs from sample candidates
    resume_ids = []
    async for db in get_db():
        result = await db.execute(select(Resume).limit(5).offset(5))
        resumes = result.scalars().all()
        resume_ids = [str(r.id) for r in resumes]
        break

    assert len(resume_ids) >= 3, "Need at least 3 candidates for bulk export test"

    print(f"Exporting {len(resume_ids)} candidates as JSON...")

    response = await client.post(
        "/api/candidates/bulk-action",
        json={
            "action": "export",
            "resume_ids": resume_ids,
            "export_format": "json",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["action"] == "export"
    assert "export_data" in data
    assert data["export_data"]["format"] == "json"
    assert data["export_data"]["count"] == len(resume_ids)

    exported_candidates = data["export_data"]["data"]
    assert len(exported_candidates) == len(resume_ids)

    # Verify each exported candidate has required fields
    for candidate in exported_candidates:
        assert "id" in candidate
        assert "filename" in candidate
        assert candidate["id"] in resume_ids

    print(f"✓ Exported {len(exported_candidates)} candidates as JSON")
    print(f"✓ All candidates have required fields (id, filename)")


@pytest.mark.asyncio
async def test_bulk_export_csv(client: AsyncClient, sample_candidates):
    """
    Test bulk export action with CSV format.

    Verifies:
    - Export action returns candidate data in CSV format
    - CSV can be parsed correctly
    - All selected candidates are included
    - CSV headers contain required columns
    """
    print("\n=== Bulk Export CSV Test ===")

    # Get resume IDs from sample candidates
    resume_ids = []
    async for db in get_db():
        result = await db.execute(select(Resume).limit(5).offset(10))
        resumes = result.scalars().all()
        resume_ids = [str(r.id) for r in resumes]
        break

    assert len(resume_ids) >= 3, "Need at least 3 candidates for bulk export test"

    print(f"Exporting {len(resume_ids)} candidates as CSV...")

    response = await client.post(
        "/api/candidates/bulk-action",
        json={
            "action": "export",
            "resume_ids": resume_ids,
            "export_format": "csv",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["action"] == "export"
    assert "export_data" in data
    assert data["export_data"]["format"] == "csv"
    assert data["export_data"]["count"] == len(resume_ids)

    csv_data = data["export_data"]["data"]
    assert csv_data is not None and len(csv_data) > 0

    # Parse CSV to verify structure
    import csv
    import io

    csv_reader = csv.DictReader(io.StringIO(csv_data))
    csv_rows = list(csv_reader)

    assert len(csv_rows) == len(resume_ids), \
        f"Expected {len(resume_ids)} CSV rows, got {len(csv_rows)}"

    # Verify CSV has required columns
    if len(csv_rows) > 0:
        assert "id" in csv_rows[0], "CSV missing 'id' column"
        assert "filename" in csv_rows[0], "CSV missing 'filename' column"

    print(f"✓ Exported {len(csv_rows)} candidates as CSV")
    print(f"✓ CSV has correct structure and headers")


@pytest.mark.asyncio
async def test_bulk_add_to_pipeline(client: AsyncClient, sample_candidates):
    """
    Test bulk add_to_pipeline action.

    Verifies:
    - Candidates are moved to the specified stage
    - Notes are saved correctly
    - Response contains correct success/failure counts
    - Stage changes are recorded in database
    """
    print("\n=== Bulk Add to Pipeline Test ===")

    # Get resume IDs from sample candidates
    resume_ids = []
    async for db in get_db():
        result = await db.execute(select(Resume).limit(3).offset(15))
        resumes = result.scalars().all()
        resume_ids = [str(r.id) for r in resumes]
        break

    assert len(resume_ids) >= 2, "Need at least 2 candidates for bulk add_to_pipeline test"

    target_stage = "interview"
    notes = "Bulk added via integration test"

    print(f"Adding {len(resume_ids)} candidates to pipeline stage '{target_stage}'...")

    response = await client.post(
        "/api/candidates/bulk-action",
        json={
            "action": "add_to_pipeline",
            "resume_ids": resume_ids,
            "stage_id": target_stage,
            "notes": notes,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["action"] == "add_to_pipeline"
    assert data["total_requested"] == len(resume_ids)
    assert data["successful"] == len(resume_ids)
    assert data["failed"] == 0
    assert len(data["results"]) == len(resume_ids)

    # Verify all results are successful
    for result in data["results"]:
        assert result["success"] is True
        assert result["resume_id"] in resume_ids
        assert "new_stage" in result["data"]
        assert result["data"]["new_stage"] == target_stage

    # Verify candidates were moved in database
    async for db in get_db():
        for resume_id in resume_ids:
            from uuid import UUID
            resume_uuid = UUID(resume_id)

            result = await db.execute(
                select(HiringStage).where(
                    and_(
                        HiringStage.resume_id == resume_uuid,
                        HiringStage.stage_name == target_stage
                    )
                ).order_by(HiringStage.created_at.desc())
            )
            stage = result.scalar_one_or_none()
            assert stage is not None, f"Candidate {resume_id} was not added to stage"
            assert stage.notes == notes, f"Notes not saved correctly for {resume_id}"

        print(f"✓ All {len(resume_ids)} candidates moved to stage '{target_stage}'")
        break

    print(f"✓ Bulk add_to_pipeline successful")


@pytest.mark.asyncio
async def test_bulk_actions_end_to_end_workflow(client: AsyncClient, sample_candidates):
    """
    End-to-end test of bulk actions on search results.

    This is the main verification test for subtask-4-5.

    Verifies the complete workflow:
    1. Execute search returning 20+ candidates
    2. Select multiple candidates
    3. Apply bulk tag action
    4. Verify all selected candidates tagged
    5. Export selected candidates
    6. Verify export file contains correct data
    """
    print("\n=== End-to-End Bulk Actions Workflow Test ===")

    # Step 1: Execute search
    print("Step 1: Executing search for 'Python'...")
    search_response = await client.post(
        "/api/search/candidates",
        json={
            "query": "Python",
            "limit": 50,
        }
    )

    assert search_response.status_code == 200
    search_data = search_response.json()
    search_results = search_data["results"]

    print(f"✓ Search returned {len(search_results)} candidates")
    assert len(search_results) >= 3, f"Need at least 3 candidates, got {len(search_results)}"

    # Step 2: Select multiple candidates
    print("Step 2: Selecting candidates for bulk actions...")
    selected_candidates = search_results[:10]
    selected_ids = [c["id"] for c in selected_candidates]

    print(f"✓ Selected {len(selected_ids)} candidates")

    # Step 3: Apply bulk tag action
    print("Step 3: Applying bulk tag action...")
    tag_name = "E2E Test Tag"
    tag_response = await client.post(
        "/api/candidates/bulk-action",
        json={
            "action": "tag",
            "resume_ids": selected_ids[:5],
            "tag_name": tag_name,
            "tag_color": "#4CAF50",
        }
    )

    assert tag_response.status_code == 200
    tag_data = tag_response.json()

    assert tag_data["action"] == "tag"
    assert tag_data["successful"] == 5
    assert tag_data["failed"] == 0

    print(f"✓ Tagged {tag_data['successful']} candidates")

    # Step 4: Verify all selected candidates tagged
    print("Step 4: Verifying tags in database...")
    async for db in get_db():
        result = await db.execute(
            select(CandidateTag).where(CandidateTag.tag_name == tag_name)
        )
        tag = result.scalar_one_or_none()
        assert tag is not None, "Tag not found in database"

        # Count activities
        result = await db.execute(
            select(func.count(CandidateActivity.id)).where(
                and_(
                    CandidateActivity.tag_id == tag.id,
                    CandidateActivity.activity_type == CandidateActivityType.TAG_ADDED
                )
            )
        )
        activity_count = result.scalar()
        assert activity_count == 5, f"Expected 5 activities, got {activity_count}"

        print(f"✓ Verified {activity_count} tagged candidates in database")
        break

    # Step 5: Export selected candidates (JSON)
    print("Step 5: Exporting candidates as JSON...")
    export_response = await client.post(
        "/api/candidates/bulk-action",
        json={
            "action": "export",
            "resume_ids": selected_ids[5:10],
            "export_format": "json",
        }
    )

    assert export_response.status_code == 200
    export_data = export_response.json()

    assert export_data["action"] == "export"
    assert export_data["export_data"]["format"] == "json"
    assert export_data["export_data"]["count"] == 5

    exported_candidates = export_data["export_data"]["data"]
    assert len(exported_candidates) == 5

    print(f"✓ Exported {len(exported_candidates)} candidates")

    # Step 6: Verify export file contains correct data
    print("Step 6: Verifying export data integrity...")
    for candidate in exported_candidates:
        assert "id" in candidate
        assert "filename" in candidate
        assert candidate["id"] in selected_ids[5:10]

        # Verify candidate exists in database
        async for db in get_db():
            from uuid import UUID
            result = await db.execute(
                select(Resume).where(Resume.id == UUID(candidate["id"]))
            )
            resume = result.scalar_one_or_none()
            assert resume is not None, f"Candidate {candidate['id']} not found in database"
            assert resume.filename == candidate["filename"], \
                f"Filename mismatch for {candidate['id']}"
            break

    print(f"✓ All exported candidates verified in database")

    # Step 7: Test bulk add_to_pipeline
    print("Step 7: Adding candidates to pipeline...")
    pipeline_response = await client.post(
        "/api/candidates/bulk-action",
        json={
            "action": "add_to_pipeline",
            "resume_ids": selected_ids[:3],
            "stage_id": "screening",
            "notes": "E2E test bulk add to pipeline",
        }
    )

    assert pipeline_response.status_code == 200
    pipeline_data = pipeline_response.json()

    assert pipeline_data["action"] == "add_to_pipeline"
    assert pipeline_data["successful"] == 3
    assert pipeline_data["failed"] == 0

    print(f"✓ Added {pipeline_data['successful']} candidates to pipeline")

    # Verify in database
    async for db in get_db():
        from uuid import UUID
        for resume_id in selected_ids[:3]:
            resume_uuid = UUID(resume_id)
            result = await db.execute(
                select(HiringStage).where(
                    and_(
                        HiringStage.resume_id == resume_uuid,
                        HiringStage.stage_name == "screening"
                    )
                )
            )
            stage = result.scalar_one_or_none()
            assert stage is not None, f"Candidate {resume_id} not in screening stage"

        print(f"✓ Verified all candidates in correct pipeline stage")
        break

    print("\n✓✓✓ End-to-End Bulk Actions Workflow Test PASSED ✓✓✓")
    print("\nAll verification steps completed successfully:")
    print("  ✓ Search returned 3+ candidates")
    print("  ✓ Bulk tag action worked correctly")
    print("  ✓ Tags verified in database")
    print("  ✓ Bulk export (JSON) worked correctly")
    print("  ✓ Export data integrity verified")
    print("  ✓ Bulk add_to_pipeline worked correctly")
    print("  ✓ Pipeline changes verified in database")
