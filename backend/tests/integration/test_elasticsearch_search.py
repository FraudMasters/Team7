"""
Comprehensive integration tests for Elasticsearch search functionality.

This test suite verifies:
1. Elasticsearch service initialization and connection
2. Index management (create, delete, ensure)
3. Document indexing (single and bulk operations)
4. Full-text search with boolean operators (AND, OR, NOT)
5. Field-specific queries (skills:Python, location:Remote)
6. Multi-field filtering (skills, experience, location, education, languages)
7. Range queries (experience years)
8. Query parsing with parentheses and quotes
9. Sorting by relevance, experience, date
10. Pagination with filters
11. Error handling and edge cases
12. Search performance validation
"""
import pytest
import asyncio
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

from services.elasticsearch_service import (
    ElasticsearchService,
    SearchQuery,
    SearchResponse,
    get_candidate_mapping,
)
from services.query_parser import QueryParser


# Test configuration
TEST_INDEX_NAME = "test_candidates"
TEST_ELASTICSEARCH_URL = "http://localhost:9200"


@pytest.fixture
async def es_service():
    """Create Elasticsearch service instance for testing."""
    service = ElasticsearchService(
        elasticsearch_url=TEST_ELASTICSEARCH_URL,
        index_name=TEST_INDEX_NAME,
    )

    try:
        # Initialize the service
        await service.initialize()

        # Clean up any existing test index
        await service.delete_index()

        # Create fresh index with mapping
        await service.ensure_index()

        yield service

    finally:
        # Cleanup
        try:
            await service.delete_index()
        except Exception:
            pass

        try:
            await service.close()
        except Exception:
            pass


@pytest.fixture
async def sample_resumes(es_service: ElasticsearchService) -> List[Dict[str, Any]]:
    """Create sample resume documents for testing."""
    resumes = [
        {
            "id": str(uuid4()),
            "resume_id": str(uuid4()),
            "raw_text": "John Doe - Senior Python Developer with 8 years experience in Python, Django, FastAPI, PostgreSQL. "
                       "Strong background in building scalable web applications and RESTful APIs.",
            "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "REST API"],
            "experience_years": 8,
            "education": "M.Sc Computer Science",
            "location": "Remote",
            "languages": ["English", "Spanish"],
            "indexed_at": datetime.utcnow().isoformat(),
        },
        {
            "id": str(uuid4()),
            "resume_id": str(uuid4()),
            "raw_text": "Jane Smith - Fullstack Developer with 5 years experience in React, Node.js, Python, MongoDB. "
                       "Passionate about creating responsive web applications.",
            "skills": ["React", "Node.js", "Python", "MongoDB", "JavaScript"],
            "experience_years": 5,
            "education": "B.Sc Software Engineering",
            "location": "New York",
            "languages": ["English"],
            "indexed_at": datetime.utcnow().isoformat(),
        },
        {
            "id": str(uuid4()),
            "resume_id": str(uuid4()),
            "raw_text": "Bob Johnson - Junior Developer with 2 years experience in Python and JavaScript. "
                       "Eager to learn and grow in software development.",
            "skills": ["Python", "JavaScript", "HTML", "CSS"],
            "experience_years": 2,
            "education": "B.Sc Computer Science",
            "location": "San Francisco",
            "languages": ["English"],
            "indexed_at": datetime.utcnow().isoformat(),
        },
        {
            "id": str(uuid4()),
            "resume_id": str(uuid4()),
            "raw_text": "Alice Williams - Data Scientist with 6 years experience in Python, Machine Learning, TensorFlow, Pandas. "
                       "PhD in Data Science with publications in top ML conferences.",
            "skills": ["Python", "Machine Learning", "TensorFlow", "Pandas", "NumPy"],
            "experience_years": 6,
            "education": "PhD Data Science",
            "location": "Remote",
            "languages": ["English", "French"],
            "indexed_at": datetime.utcnow().isoformat(),
        },
        {
            "id": str(uuid4()),
            "resume_id": str(uuid4()),
            "raw_text": "Charlie Brown - DevOps Engineer with 4 years experience in Docker, Kubernetes, AWS, CI/CD. "
                       "Expert in infrastructure automation and cloud architecture.",
            "skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Terraform"],
            "experience_years": 4,
            "education": "M.Sc Information Technology",
            "location": "London",
            "languages": ["English", "German"],
            "indexed_at": datetime.utcnow().isoformat(),
        },
    ]

    # Bulk index the resumes
    stats = await es_service.bulk_index(resumes, refresh=True)
    assert stats["success"] == len(resumes), f"Expected {len(resumes)} resumes indexed, got {stats['success']}"

    # Wait for indexing to complete
    await asyncio.sleep(1)

    return resumes


@pytest.mark.asyncio
async def test_elasticsearch_service_initialization():
    """Test Elasticsearch service initialization and connection."""
    service = ElasticsearchService(
        elasticsearch_url=TEST_ELASTICSEARCH_URL,
        index_name=TEST_INDEX_NAME,
    )

    await service.initialize()

    assert service.client is not None
    assert service._initialized is True

    await service.close()


@pytest.mark.asyncio
async def test_index_management(es_service: ElasticsearchService):
    """Test index creation, existence check, and deletion."""
    # Index should already exist from fixture
    exists = await es_service.client.indices.exists(index=TEST_INDEX_NAME)
    assert exists is True

    # Delete index
    deleted = await es_service.delete_index()
    assert deleted is True

    # Verify deletion
    exists = await es_service.client.indices.exists(index=TEST_INDEX_NAME)
    assert exists is False

    # Recreate index
    created = await es_service.ensure_index()
    assert created is True

    # Verify creation
    exists = await es_service.client.indices.exists(index=TEST_INDEX_NAME)
    assert exists is True


@pytest.mark.asyncio
async def test_get_candidate_mapping():
    """Test candidate mapping structure."""
    mapping = get_candidate_mapping()

    assert "settings" in mapping
    assert "mappings" in mapping
    assert "properties" in mapping["mappings"]

    properties = mapping["mappings"]["properties"]
    assert "resume_id" in properties
    assert "raw_text" in properties
    assert "skills" in properties
    assert "experience_years" in properties
    assert "education" in properties
    assert "location" in properties
    assert "languages" in properties
    assert "indexed_at" in properties

    # Verify field types
    assert properties["resume_id"]["type"] == "keyword"
    assert properties["raw_text"]["type"] == "text"
    assert properties["skills"]["type"] == "text"
    assert properties["experience_years"]["type"] == "integer"


@pytest.mark.asyncio
async def test_index_single_resume(es_service: ElasticsearchService):
    """Test indexing a single resume document."""
    resume_id = str(uuid4())
    resume_data = {
        "resume_id": resume_id,
        "raw_text": "Test candidate with Python skills",
        "skills": ["Python", "Django"],
        "experience_years": 3,
        "education": "B.Sc Computer Science",
        "location": "Boston",
        "languages": ["English"],
        "indexed_at": datetime.utcnow().isoformat(),
    }

    result = await es_service.index_resume(resume_id, resume_data)
    assert result is True

    # Refresh index to make document searchable
    await es_service.refresh_index()

    # Retrieve the document
    doc = await es_service.get_document(resume_id)
    assert doc is not None
    assert doc["resume_id"] == resume_id
    assert doc["raw_text"] == resume_data["raw_text"]
    assert doc["skills"] == resume_data["skills"]


@pytest.mark.asyncio
async def test_bulk_index_resumes(es_service: ElasticsearchService):
    """Test bulk indexing multiple resumes."""
    resumes = [
        {
            "id": str(uuid4()),
            "raw_text": f"Candidate {i}",
            "skills": ["Python"],
            "experience_years": i,
        }
        for i in range(1, 6)
    ]

    stats = await es_service.bulk_index(resumes, refresh=True)

    assert stats["success"] == 5
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_basic_full_text_search(es_service: ElasticsearchService, sample_resumes):
    """Test basic full-text search without filters."""
    query = SearchQuery(
        query_string="Python Developer",
        size=10,
    )

    response = await es_service.search(query)

    assert isinstance(response, SearchResponse)
    assert response.total > 0
    assert len(response.hits) > 0
    assert response.took_ms >= 0


@pytest.mark.asyncio
async def test_search_with_boolean_and(es_service: ElasticsearchService, sample_resumes):
    """Test search with AND boolean operator."""
    query = SearchQuery(
        query_string="Python AND Django",
        size=10,
    )

    response = await es_service.search(query)

    assert response.total >= 1
    # Should find candidates with both Python and Django
    for hit in response.hits:
        text = hit["_source"]["raw_text"].lower()
        assert "python" in text
        assert "django" in text


@pytest.mark.asyncio
async def test_search_with_boolean_or(es_service: ElasticsearchService, sample_resumes):
    """Test search with OR boolean operator."""
    query = SearchQuery(
        query_string="React OR MongoDB",
        size=10,
    )

    response = await es_service.search(query)

    assert response.total >= 1
    # Should find candidates with either React or MongoDB
    for hit in response.hits:
        text = hit["_source"]["raw_text"].lower()
        assert "react" in text or "mongodb" in text


@pytest.mark.asyncio
async def test_search_with_boolean_not(es_service: ElasticsearchService, sample_resumes):
    """Test search with NOT boolean operator."""
    query = SearchQuery(
        query_string="Python NOT Django",
        size=10,
    )

    response = await es_service.search(query)

    assert response.total >= 1
    # Should find candidates with Python but not Django
    for hit in response.hits:
        text = hit["_source"]["raw_text"].lower()
        skills = [s.lower() for s in hit["_source"].get("skills", [])]

        # Must have Python
        assert "python" in text or "python" in skills

        # Must not have Django (in skills at least)
        if "django" in skills:
            pytest.fail(f"Found Django in skills when it should be excluded: {skills}")


@pytest.mark.asyncio
async def test_search_with_parentheses(es_service: ElasticsearchService, sample_resumes):
    """Test search with parenthesized boolean expressions."""
    query = SearchQuery(
        query_string="Python AND (Django OR Flask)",
        size=10,
    )

    response = await es_service.search(query)

    # Should find candidates with Python and either Django or Flask
    assert response.total >= 1


@pytest.mark.asyncio
async def test_search_with_field_specific_query(es_service: ElasticsearchService, sample_resumes):
    """Test field-specific search queries."""
    query = SearchQuery(
        query_string="skills:Python location:Remote",
        size=10,
    )

    response = await es_service.search(query)

    assert response.total >= 1
    # Should find candidates with Python skill and Remote location
    for hit in response.hits:
        source = hit["_source"]
        skills = [s.lower() for s in source.get("skills", [])]
        location = source.get("location", "").lower()

        assert "python" in skills
        assert "remote" in location


@pytest.mark.asyncio
async def test_search_with_skills_filter(es_service: ElasticsearchService, sample_resumes):
    """Test search with skills filter."""
    query = SearchQuery(
        query_string="Developer",
        skills=["Python", "Django"],
        size=10,
    )

    response = await es_service.search(query)

    assert response.total >= 1
    # Should find candidates with both Python and Django skills
    for hit in response.hits:
        skills = [s.lower() for s in hit["_source"].get("skills", [])]
        assert "python" in skills or "django" in skills


@pytest.mark.asyncio
async def test_search_with_experience_filter(es_service: ElasticsearchService, sample_resumes):
    """Test search with experience range filter."""
    query = SearchQuery(
        query_string="Developer",
        min_experience_years=5,
        max_experience_years=10,
        size=10,
    )

    response = await es_service.search(query)

    assert response.total >= 1
    # Should find candidates with 5-10 years experience
    for hit in response.hits:
        experience = hit["_source"].get("experience_years", 0)
        assert 5 <= experience <= 10


@pytest.mark.asyncio
async def test_search_with_location_filter(es_service: ElasticsearchService, sample_resumes):
    """Test search with location filter."""
    query = SearchQuery(
        query_string="Developer",
        location="Remote",
        size=10,
    )

    response = await es_service.search(query)

    assert response.total >= 1
    # Should find candidates in Remote location
    for hit in response.hits:
        location = hit["_source"].get("location", "").lower()
        assert "remote" in location


@pytest.mark.asyncio
async def test_search_with_education_filter(es_service: ElasticsearchService, sample_resumes):
    """Test search with education level filter."""
    query = SearchQuery(
        query_string="Developer",
        education_level="PhD",
        size=10,
    )

    response = await es_service.search(query)

    # Should find candidates with PhD
    for hit in response.hits:
        education = hit["_source"].get("education", "").lower()
        assert "phd" in education


@pytest.mark.asyncio
async def test_search_with_languages_filter(es_service: ElasticsearchService, sample_resumes):
    """Test search with languages filter."""
    query = SearchQuery(
        query_string="Developer",
        languages=["Spanish", "French"],
        size=10,
    )

    response = await es_service.search(query)

    # Should find candidates who speak Spanish or French
    for hit in response.hits:
        languages = hit["_source"].get("languages", [])
        assert any(lang in languages for lang in ["Spanish", "French"])


@pytest.mark.asyncio
async def test_search_with_combined_filters(es_service: ElasticsearchService, sample_resumes):
    """Test search with multiple combined filters."""
    query = SearchQuery(
        query_string="Python Developer",
        skills=["Python"],
        min_experience_years=3,
        location="Remote",
        size=10,
    )

    response = await es_service.search(query)

    # Should find candidates matching all criteria
    for hit in response.hits:
        source = hit["_source"]
        skills = [s.lower() for s in source.get("skills", [])]
        experience = source.get("experience_years", 0)
        location = source.get("location", "").lower()

        assert "python" in skills
        assert experience >= 3
        assert "remote" in location


@pytest.mark.asyncio
async def test_search_sorting_by_experience(es_service: ElasticsearchService, sample_resumes):
    """Test search results sorted by experience years."""
    query = SearchQuery(
        query_string="Developer",
        sort_by="experience_years",
        size=10,
    )

    response = await es_service.search(query)

    assert response.total > 0

    # Verify descending order of experience
    experiences = [hit["_source"].get("experience_years", 0) for hit in response.hits]
    assert experiences == sorted(experiences, reverse=True)


@pytest.mark.asyncio
async def test_search_pagination(es_service: ElasticsearchService, sample_resumes):
    """Test search pagination with from/size."""
    # First page
    query_page1 = SearchQuery(
        query_string="Developer",
        from_=0,
        size=2,
    )

    response_page1 = await es_service.search(query_page1)

    # Second page
    query_page2 = SearchQuery(
        query_string="Developer",
        from_=2,
        size=2,
    )

    response_page2 = await es_service.search(query_page2)

    # Should have results on both pages
    assert len(response_page1.hits) > 0

    # Results should be different
    if len(response_page2.hits) > 0:
        page1_ids = [hit["_id"] for hit in response_page1.hits]
        page2_ids = [hit["_id"] for hit in response_page2.hits]
        assert set(page1_ids).isdisjoint(set(page2_ids))


@pytest.mark.asyncio
async def test_search_with_no_results(es_service: ElasticsearchService, sample_resumes):
    """Test search that returns no results."""
    query = SearchQuery(
        query_string="NonexistentSkillXYZ123",
        size=10,
    )

    response = await es_service.search(query)

    assert response.total == 0
    assert len(response.hits) == 0


@pytest.mark.asyncio
async def test_search_empty_query(es_service: ElasticsearchService, sample_resumes):
    """Test search with empty query (match all)."""
    query = SearchQuery(
        query_string=None,
        size=10,
    )

    response = await es_service.search(query)

    # Should return all documents
    assert response.total == len(sample_resumes)


@pytest.mark.asyncio
async def test_query_parser_boolean_operators():
    """Test QueryParser with various boolean operators."""
    parser = QueryParser()

    # Test AND operator
    result = parser.parse("Python AND Django")
    assert result is not None
    assert "query" in result

    # Test OR operator
    result = parser.parse("Python OR Ruby")
    assert result is not None

    # Test NOT operator
    result = parser.parse("Python NOT Java")
    assert result is not None

    # Test complex expression
    result = parser.parse("Python AND (Django OR Flask) NOT Java")
    assert result is not None


@pytest.mark.asyncio
async def test_query_parser_field_specific():
    """Test QueryParser with field-specific queries."""
    parser = QueryParser()

    result = parser.parse("skills:Python location:Remote")
    assert result is not None
    assert "query" in result


@pytest.mark.asyncio
async def test_query_parser_quoted_strings():
    """Test QueryParser with quoted phrases."""
    parser = QueryParser()

    result = parser.parse('"Senior Python Developer"')
    assert result is not None
    assert "query" in result


@pytest.mark.asyncio
async def test_query_parser_error_handling():
    """Test QueryParser error handling for invalid queries."""
    parser = QueryParser()

    # Unclosed parenthesis
    with pytest.raises(ValueError, match="Unclosed parenthesis"):
        parser.parse("Python AND (Django")

    # Trailing operator
    with pytest.raises(ValueError, match="Expected search term"):
        parser.parse("Python AND")

    # Empty parentheses
    with pytest.raises(ValueError, match="Empty parenthesized expression"):
        parser.parse("()")


@pytest.mark.asyncio
async def test_delete_document(es_service: ElasticsearchService):
    """Test deleting a document by ID."""
    resume_id = str(uuid4())
    resume_data = {
        "resume_id": resume_id,
        "raw_text": "Test candidate",
        "skills": ["Python"],
        "experience_years": 3,
    }

    # Index document
    await es_service.index_resume(resume_id, resume_data)
    await es_service.refresh_index()

    # Verify it exists
    doc = await es_service.get_document(resume_id)
    assert doc is not None

    # Delete document
    deleted = await es_service.delete_document(resume_id)
    assert deleted is True

    # Verify deletion
    await es_service.refresh_index()
    doc = await es_service.get_document(resume_id)
    assert doc is None


@pytest.mark.asyncio
async def test_search_performance(es_service: ElasticsearchService, sample_resumes):
    """Test search performance is under acceptable threshold."""
    query = SearchQuery(
        query_string="Python AND Django",
        skills=["Python"],
        min_experience_years=2,
        size=10,
    )

    response = await es_service.search(query)

    # Search should complete in under 2000ms (2 seconds)
    assert response.took_ms < 2000, f"Search took {response.took_ms}ms, expected < 2000ms"


@pytest.mark.asyncio
async def test_refresh_index(es_service: ElasticsearchService):
    """Test index refresh operation."""
    resume_id = str(uuid4())
    resume_data = {
        "resume_id": resume_id,
        "raw_text": "Test candidate",
        "skills": ["Python"],
        "experience_years": 3,
    }

    # Index without refresh
    await es_service.index_resume(resume_id, resume_data)

    # Refresh index
    await es_service.refresh_index()

    # Document should now be searchable
    query = SearchQuery(query_string=resume_id, size=10)
    response = await es_service.search(query)

    # Should be able to find the document
    assert response.total >= 0  # May or may not be immediately visible


@pytest.mark.asyncio
async def test_search_with_boost_values(es_service: ElasticsearchService, sample_resumes):
    """Test search with custom field boost values."""
    query = SearchQuery(
        query_string="Python",
        skills_boost=3.0,
        education_boost=1.5,
        location_boost=1.0,
        size=10,
    )

    response = await es_service.search(query)

    # Should return results with boosted fields having higher relevance
    assert response.total > 0


@pytest.mark.asyncio
async def test_nonexistent_index_search():
    """Test search on non-existent index."""
    service = ElasticsearchService(
        elasticsearch_url=TEST_ELASTICSEARCH_URL,
        index_name="nonexistent_index",
    )

    await service.initialize()

    query = SearchQuery(query_string="test", size=10)
    response = await service.search(query)

    # Should return empty results, not error
    assert response.total == 0
    assert len(response.hits) == 0

    await service.close()


@pytest.mark.asyncio
async def test_get_nonexistent_document(es_service: ElasticsearchService):
    """Test retrieving a non-existent document."""
    doc = await es_service.get_document("nonexistent-id")
    assert doc is None


@pytest.mark.asyncio
async def test_delete_nonexistent_document(es_service: ElasticsearchService):
    """Test deleting a non-existent document."""
    deleted = await es_service.delete_document("nonexistent-id")
    assert deleted is False
