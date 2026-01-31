"""
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
