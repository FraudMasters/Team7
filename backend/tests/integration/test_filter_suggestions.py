"""
Comprehensive integration tests for AI-powered filter suggestions workflow.

This test suite verifies:
1. Basic JD filter suggestion analysis
2. Skills extraction from job descriptions
3. Experience requirements extraction (years and seniority level)
4. Location requirements extraction
5. Education requirements extraction
6. Language requirements extraction
7. Structured vacancy filter suggestions
8. Filter confidence scoring
9. Ready-to-use search filters generation
10. Performance optimization
"""
import pytest
import time
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_filter_suggestions.db"


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


@pytest.mark.asyncio
async def test_basic_filter_suggestions(client: AsyncClient):
    """Test basic JD filter suggestion analysis."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "Senior Python Developer with 5+ years experience in Django and AWS. Based in NYC.",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "skills" in data
    assert "min_experience_years" in data
    assert "max_experience_years" in data
    assert "seniority_level" in data
    assert "location" in data
    assert "confidence" in data
    assert "analysis_time_seconds" in data
    assert "search_filters" in data

    # Verify skills were extracted
    assert len(data["skills"]) >= 1
    skill_values = [s["value"] for s in data["skills"]]
    assert "Python" in skill_values

    # Verify experience was extracted
    assert data["min_experience_years"] == 5
    assert data["seniority_level"] == "senior"

    # Verify location was extracted
    assert data["location"] is not None
    assert data["location"]["value"] in ["New York", "Nyc", "Remote"]  # Flexible matching


@pytest.mark.asyncio
async def test_filter_suggestions_with_multiple_skills(client: AsyncClient):
    """Test JD analysis extracts multiple skills correctly."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": """
            We are looking for a Fullstack Developer with experience in:
            - Python, Django, FastAPI for backend
            - React, TypeScript for frontend
            - PostgreSQL, Redis for databases
            - Docker, Kubernetes for DevOps
            """,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify multiple skills were extracted
    assert len(data["skills"]) >= 3
    skill_values = [s["value"] for s in data["skills"]]

    # Should find at least some of these skills
    expected_skills = ["Python", "Django", "FastAPI", "React", "PostgreSQL", "Docker"]
    found_skills = [s for s in expected_skills if s in skill_values]
    assert len(found_skills) >= 3, f"Expected to find at least 3 skills, found: {found_skills}"


@pytest.mark.asyncio
async def test_filter_suggestions_with_experience_range(client: AsyncClient):
    """Test JD analysis extracts experience ranges."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "Looking for a Mid-level Developer with 3-7 years of experience in software development.",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify experience range was extracted
    assert data["min_experience_years"] == 3
    assert data["max_experience_years"] == 7
    assert data["seniority_level"] == "mid"


@pytest.mark.asyncio
async def test_filter_suggestions_with_education(client: AsyncClient):
    """Test JD analysis extracts education requirements."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "Bachelor's degree in Computer Science required. Master's degree preferred.",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify education was extracted
    assert data["education_level"] is not None
    assert data["education_level"]["value"] in ["bachelor", "master"]


@pytest.mark.asyncio
async def test_filter_suggestions_with_languages(client: AsyncClient):
    """Test JD analysis extracts language requirements."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "Must be fluent in English and Spanish. German is a plus.",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify languages were extracted
    assert len(data["languages"]) >= 2
    language_values = [l["value"] for l in data["languages"]]
    assert "English" in language_values
    assert "Spanish" in language_values


@pytest.mark.asyncio
async def test_filter_suggestions_with_remote_location(client: AsyncClient):
    """Test JD analysis extracts remote location."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "This is a fully remote position. Work from anywhere!",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify remote location was extracted
    assert data["location"] is not None
    assert data["location"]["value"] == "Remote"


@pytest.mark.asyncio
async def test_filter_suggestions_with_seniority_levels(client: AsyncClient):
    """Test JD analysis detects various seniority levels."""
    test_cases = [
        ("Junior Developer", "entry"),
        ("Senior Software Engineer", "senior"),
        ("Lead Developer", "lead"),
        ("Engineering Manager", "executive"),
        ("Mid-level Engineer", "mid"),
    ]

    for title, expected_level in test_cases:
        response = await client.post(
            "/api/filter-suggestions/suggest",
            json={
                "job_description": f"Looking for a {title} with relevant experience.",
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify seniority level was detected
        assert data["seniority_level"] == expected_level, \
            f"Expected {expected_level} for {title}, got {data['seniority_level']}"


@pytest.mark.asyncio
async def test_filter_suggestions_confidence_scores(client: AsyncClient):
    """Test that confidence scores are in valid range."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "Python Developer with 5 years experience in Django and PostgreSQL.",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify overall confidence is in valid range
    assert 0.0 <= data["confidence"] <= 1.0

    # Verify each skill has valid confidence
    for skill in data["skills"]:
        assert 0.0 <= skill["confidence"] <= 1.0

    # Verify location confidence if present
    if data["location"]:
        assert 0.0 <= data["location"]["confidence"] <= 1.0

    # Verify education confidence if present
    if data["education_level"]:
        assert 0.0 <= data["education_level"]["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_filter_suggestions_search_filters_output(client: AsyncClient):
    """Test that search_filters output is ready for search API."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "Senior Python Developer with 5+ years experience. Bachelor's degree required. Remote position.",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify search_filters structure
    search_filters = data["search_filters"]
    assert isinstance(search_filters, dict)

    # Should contain skills if extracted
    if data["skills"]:
        assert "skills" in search_filters
        assert isinstance(search_filters["skills"], list)

    # Should contain experience if extracted
    if data["min_experience_years"] is not None:
        assert "min_experience_years" in search_filters

    # Should contain location if extracted
    if data["location"]:
        assert "location" in search_filters

    # Should contain education if extracted
    if data["education_level"]:
        assert "education_level" in search_filters


@pytest.mark.asyncio
async def test_filter_suggestions_min_confidence_threshold(client: AsyncClient):
    """Test that min_confidence threshold filters low-confidence suggestions."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "Software developer needed for various projects.",
            "min_confidence": 0.8,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify all returned skills meet the confidence threshold
    for skill in data["skills"]:
        assert skill["confidence"] >= 0.8, \
            f"Skill {skill['value']} has confidence {skill['confidence']} < 0.8"


@pytest.mark.asyncio
async def test_filter_suggestions_max_skills_limit(client: AsyncClient):
    """Test that max_skills parameter limits number of skills returned."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": """
            Developer with experience in Python, Django, FastAPI, Flask, PostgreSQL,
            MongoDB, Redis, Docker, Kubernetes, AWS, React, TypeScript, JavaScript,
            Node.js, and Git.
            """,
            "max_skills": 5,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify skills are limited
    assert len(data["skills"]) <= 5


@pytest.mark.asyncio
async def test_filter_suggestions_empty_jd(client: AsyncClient):
    """Test handling of empty or minimal job descriptions."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "Developer needed.",
        }
    )

    # Should return 200 with empty suggestions
    assert response.status_code == 200
    data = response.json()

    # Should have valid structure even with minimal input
    assert "skills" in data
    assert "confidence" in data
    assert "search_filters" in data


@pytest.mark.asyncio
async def test_filter_suggestions_too_short_jd(client: AsyncClient):
    """Test handling of too short job descriptions."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "abc",
        }
    )

    # Should return 400 for validation error (min_length=10)
    assert response.status_code == 400


# ============================================================================
# Structured Vacancy Filter Suggestions Tests
# ============================================================================

@pytest.mark.asyncio
async def test_vacancy_filter_suggestions(client: AsyncClient):
    """Test structured vacancy filter suggestions."""
    response = await client.post(
        "/api/filter-suggestions/suggest-vacancy",
        json={
            "title": "Senior Python Developer",
            "description": "5+ years experience required. Remote position.",
            "skills": ["Python", "Django", "PostgreSQL"],
            "requirements": ["Bachelor's degree", "Strong communication skills"],
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "skills" in data
    assert "confidence" in data
    assert "search_filters" in data

    # Verify provided skills are included with high confidence
    skill_values = [s["value"] for s in data["skills"]]
    assert "Python" in skill_values
    assert "Django" in skill_values
    assert "PostgreSQL" in skill_values

    # Verify provided skills have 'provided' source
    for skill in data["skills"]:
        if skill["value"] in ["Python", "Django", "PostgreSQL"]:
            assert skill["source"] == "provided"
            assert skill["confidence"] >= 0.9


@pytest.mark.asyncio
async def test_vacancy_filter_suggestions_title_only(client: AsyncClient):
    """Test vacancy filter suggestions with title only."""
    response = await client.post(
        "/api/filter-suggestions/suggest-vacancy",
        json={
            "title": "Senior Python Developer",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should extract seniority from title
    assert data["seniority_level"] == "senior"

    # Should have skills from title analysis
    skill_values = [s["value"] for s in data["skills"]]
    assert "Python" in skill_values


@pytest.mark.asyncio
async def test_vacancy_filter_suggestions_skills_only(client: AsyncClient):
    """Test vacancy filter suggestions with skills only."""
    response = await client.post(
        "/api/filter-suggestions/suggest-vacancy",
        json={
            "skills": ["Python", "React", "PostgreSQL"],
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify provided skills are included
    skill_values = [s["value"] for s in data["skills"]]
    assert "Python" in skill_values
    assert "React" in skill_values
    assert "PostgreSQL" in skill_values


@pytest.mark.asyncio
async def test_vacancy_filter_suggestions_empty_data(client: AsyncClient):
    """Test vacancy filter suggestions with no data."""
    response = await client.post(
        "/api/filter-suggestions/suggest-vacancy",
        json={}
    )

    # Should return 400 as at least one field is required
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_filter_suggestions_all_filters_list(client: AsyncClient):
    """Test that all_filters contains combined sorted filters."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "Senior Python Developer with 5+ years experience. Bachelor's degree. Remote. Fluent in Spanish.",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify all_filters list exists
    assert "all_filters" in data
    assert len(data["all_filters"]) > 0

    # Verify filters are sorted by confidence (descending)
    confidences = [f["confidence"] for f in data["all_filters"]]
    assert confidences == sorted(confidences, reverse=True)


@pytest.mark.asyncio
async def test_filter_suggestions_performance(client: AsyncClient):
    """Test that filter suggestions complete in reasonable time."""
    long_jd = """
    We are looking for a Senior Fullstack Developer to join our team.

    Requirements:
    - 5+ years of experience in Python, Django, FastAPI
    - Experience with React, TypeScript, JavaScript
    - Knowledge of PostgreSQL, MongoDB, Redis
    - Familiarity with Docker, Kubernetes, AWS
    - Bachelor's degree in Computer Science
    - Excellent communication skills
    - Fluent in English, Spanish is a plus

    This is a fully remote position based in New York.
    You will be working on cutting-edge projects with a talented team.
    """ * 10  # Repeat to make it longer

    start_time = time.time()

    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": long_jd,
        }
    )

    end_time = time.time()
    execution_time = end_time - start_time

    assert response.status_code == 200
    data = response.json()

    # Should complete in under 1 second
    assert execution_time < 1.0, f"Filter suggestions took {execution_time:.2f}s, expected < 1s"

    # Server-reported time should also be reasonable
    assert data["analysis_time_seconds"] < 1.0


@pytest.mark.asyncio
async def test_filter_suggestions_filter_types(client: AsyncClient):
    """Test that filter items have correct filter_type values."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "Python Developer with Bachelor's degree. Remote. Fluent in Spanish.",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Check skills filter type
    for skill in data["skills"]:
        assert skill["filter_type"] == "skills"

    # Check location filter type
    if data["location"]:
        assert data["location"]["filter_type"] == "location"

    # Check education filter type
    if data["education_level"]:
        assert data["education_level"]["filter_type"] == "education_level"

    # Check languages filter type
    for lang in data["languages"]:
        assert lang["filter_type"] == "languages"


@pytest.mark.asyncio
async def test_filter_suggestions_source_types(client: AsyncClient):
    """Test that filter items have valid source values."""
    response = await client.post(
        "/api/filter-suggestions/suggest",
        json={
            "job_description": "Python Developer with Bachelor's degree. Remote.",
        }
    )

    assert response.status_code == 200
    data = response.json()

    valid_sources = ["extracted", "inferred", "synonym", "provided"]

    # Check all filters have valid source
    for skill in data["skills"]:
        assert skill["source"] in valid_sources

    if data["location"]:
        assert data["location"]["source"] in valid_sources

    if data["education_level"]:
        assert data["education_level"]["source"] in valid_sources
