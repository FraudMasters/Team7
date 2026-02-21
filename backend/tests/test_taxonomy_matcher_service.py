"""
Unit tests for TaxonomyMatcherService.

Tests cover:
- Service initialization
- Alias resolution (sync and async)
- Related skills lookup (sync and async)
- Skill matching (single and multiple)
- Dataclass functionality
- Edge cases and error handling
"""
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import uuid

import pytest

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.taxonomy_matcher_service import (
    TaxonomyMatcherService,
    TaxonomyMatchResult,
    AliasResolution,
    RelatedSkill,
    get_taxonomy_matcher_service,
)


class TestTaxonomyMatchResult:
    """Tests for TaxonomyMatchResult dataclass."""

    def test_taxonomy_match_result_default_values(self):
        """Test default values for TaxonomyMatchResult."""
        result = TaxonomyMatchResult()
        assert result.matched_skill is None
        assert result.original_skill is None
        assert result.taxonomy_entry is None
        assert result.score == 0.0
        assert result.match_type is None
        assert result.aliases_matched == []
        assert result.related_skills == []
        assert result.category_path == []
        assert result.confidence == 0.0
        assert result.error is None

    def test_taxonomy_match_result_custom_values(self):
        """Test TaxonomyMatchResult with custom values."""
        result = TaxonomyMatchResult(
            matched_skill="JavaScript",
            original_skill="JS",
            taxonomy_entry={"skill_name": "JavaScript"},
            score=95.0,
            match_type="alias",
            confidence=0.95,
        )
        assert result.matched_skill == "JavaScript"
        assert result.original_skill == "JS"
        assert result.score == 95.0
        assert result.match_type == "alias"

    def test_taxonomy_match_result_to_dict(self):
        """Test to_dict method."""
        result = TaxonomyMatchResult(
            matched_skill="React",
            original_skill="ReactJS",
            score=90.0,
            match_type="alias",
            aliases_matched=["ReactJS"],
            related_skills=["Vue", "Angular"],
            category_path=["Frontend", "Frameworks"],
            confidence=0.9,
        )
        data = result.to_dict()
        assert data["matched_skill"] == "React"
        assert data["original_skill"] == "ReactJS"
        assert data["score"] == 90.0
        assert data["match_type"] == "alias"
        assert "ReactJS" in data["aliases_matched"]
        assert "Vue" in data["related_skills"]
        assert "Frontend" in data["category_path"]


class TestAliasResolution:
    """Tests for AliasResolution dataclass."""

    def test_alias_resolution_default_values(self):
        """Test default values for AliasResolution."""
        resolution = AliasResolution(
            alias="JS",
            resolved_skill="JavaScript",
        )
        assert resolution.alias == "JS"
        assert resolution.resolved_skill == "JavaScript"
        assert resolution.taxonomy_id is None
        assert resolution.industry is None
        assert resolution.context is None
        assert resolution.confidence == 1.0

    def test_alias_resolution_custom_values(self):
        """Test AliasResolution with custom values."""
        taxonomy_id = uuid.uuid4()
        resolution = AliasResolution(
            alias="TS",
            resolved_skill="TypeScript",
            taxonomy_id=taxonomy_id,
            industry="tech",
            context="programming_language",
            confidence=0.95,
        )
        assert resolution.alias == "TS"
        assert resolution.resolved_skill == "TypeScript"
        assert resolution.taxonomy_id == taxonomy_id
        assert resolution.industry == "tech"
        assert resolution.context == "programming_language"

    def test_alias_resolution_to_dict(self):
        """Test to_dict method."""
        taxonomy_id = uuid.uuid4()
        resolution = AliasResolution(
            alias="py",
            resolved_skill="Python",
            taxonomy_id=taxonomy_id,
            industry="tech",
            context="programming_language",
            confidence=1.0,
        )
        data = resolution.to_dict()
        assert data["alias"] == "py"
        assert data["resolved_skill"] == "Python"
        assert data["taxonomy_id"] == str(taxonomy_id)
        assert data["industry"] == "tech"
        assert data["context"] == "programming_language"


class TestRelatedSkill:
    """Tests for RelatedSkill dataclass."""

    def test_related_skill_default_values(self):
        """Test default values for RelatedSkill."""
        related = RelatedSkill(
            skill_name="Vue",
            relationship_type="similar",
        )
        assert related.skill_name == "Vue"
        assert related.relationship_type == "similar"
        assert related.weight == 1.0
        assert related.taxonomy_id is None

    def test_related_skill_custom_values(self):
        """Test RelatedSkill with custom values."""
        taxonomy_id = uuid.uuid4()
        related = RelatedSkill(
            skill_name="Redux",
            relationship_type="related",
            weight=0.85,
            taxonomy_id=taxonomy_id,
        )
        assert related.skill_name == "Redux"
        assert related.relationship_type == "related"
        assert related.weight == 0.85
        assert related.taxonomy_id == taxonomy_id

    def test_related_skill_to_dict(self):
        """Test to_dict method."""
        taxonomy_id = uuid.uuid4()
        related = RelatedSkill(
            skill_name="Next.js",
            relationship_type="parent_child",
            weight=0.9,
            taxonomy_id=taxonomy_id,
        )
        data = related.to_dict()
        assert data["skill_name"] == "Next.js"
        assert data["relationship_type"] == "parent_child"
        assert data["weight"] == 0.9
        assert data["taxonomy_id"] == str(taxonomy_id)


class TestTaxonomyMatcherServiceInit:
    """Tests for TaxonomyMatcherService initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        service = TaxonomyMatcherService()
        assert service.db is None
        assert service.fuzzy_threshold == 80
        assert service.include_relationships is True
        assert service.cache_ttl == 300

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        mock_db = Mock()
        service = TaxonomyMatcherService(
            db=mock_db,
            fuzzy_threshold=90,
            include_relationships=False,
            cache_ttl=600,
        )
        assert service.db == mock_db
        assert service.fuzzy_threshold == 90
        assert service.include_relationships is False
        assert service.cache_ttl == 600

    def test_init_invalid_fuzzy_threshold_low(self):
        """Test initialization with fuzzy_threshold below valid range."""
        with pytest.raises(ValueError) as exc_info:
            TaxonomyMatcherService(fuzzy_threshold=-1)
        assert "fuzzy_threshold must be between 0 and 100" in str(exc_info.value)

    def test_init_invalid_fuzzy_threshold_high(self):
        """Test initialization with fuzzy_threshold above valid range."""
        with pytest.raises(ValueError) as exc_info:
            TaxonomyMatcherService(fuzzy_threshold=101)
        assert "fuzzy_threshold must be between 0 and 100" in str(exc_info.value)


class TestResolveAlias:
    """Tests for synchronous resolve_alias method."""

    def test_resolve_alias_javascript(self):
        """Test resolving JS to JavaScript."""
        service = TaxonomyMatcherService()
        result = service.resolve_alias("JS")
        assert result is not None
        assert result.resolved_skill == "JavaScript"
        assert result.industry == "tech"
        assert result.context == "programming_language"

    def test_resolve_alias_typescript(self):
        """Test resolving TS to TypeScript."""
        service = TaxonomyMatcherService()
        result = service.resolve_alias("TS")
        assert result is not None
        assert result.resolved_skill == "TypeScript"

    def test_resolve_alias_python(self):
        """Test resolving py to Python."""
        service = TaxonomyMatcherService()
        result = service.resolve_alias("py")
        assert result is not None
        assert result.resolved_skill == "Python"

    def test_resolve_alias_postgres(self):
        """Test resolving postgres to PostgreSQL."""
        service = TaxonomyMatcherService()
        result = service.resolve_alias("postgres")
        assert result is not None
        assert result.resolved_skill == "PostgreSQL"

    def test_resolve_alias_case_insensitive(self):
        """Test that alias resolution is case-insensitive."""
        service = TaxonomyMatcherService()
        result_lower = service.resolve_alias("js")
        result_upper = service.resolve_alias("JS")
        assert result_lower is not None
        assert result_upper is not None
        assert result_lower.resolved_skill == result_upper.resolved_skill

    def test_resolve_alias_with_industry_filter(self):
        """Test alias resolution with industry filter."""
        service = TaxonomyMatcherService()
        result = service.resolve_alias("JS", industry="tech")
        assert result is not None
        assert result.resolved_skill == "JavaScript"

    def test_resolve_alias_with_wrong_industry(self):
        """Test alias resolution with mismatched industry filter."""
        service = TaxonomyMatcherService()
        result = service.resolve_alias("JS", industry="healthcare")
        assert result is None

    def test_resolve_alias_not_found(self):
        """Test alias resolution when alias is not found."""
        service = TaxonomyMatcherService()
        result = service.resolve_alias("UnknownSkill12345")
        assert result is None

    def test_resolve_alias_empty_string(self):
        """Test alias resolution with empty string."""
        service = TaxonomyMatcherService()
        result = service.resolve_alias("")
        assert result is None

    def test_resolve_alias_none(self):
        """Test alias resolution with None."""
        service = TaxonomyMatcherService()
        result = service.resolve_alias(None)
        assert result is None

    def test_resolve_alias_caching(self):
        """Test that alias resolution results are cached."""
        service = TaxonomyMatcherService()
        # First call
        result1 = service.resolve_alias("JS")
        # Second call should return cached result
        result2 = service.resolve_alias("JS")
        assert result1 is result2


class TestFindRelatedSkills:
    """Tests for synchronous find_related_skills method."""

    def test_find_related_skills_react(self):
        """Test finding skills related to React."""
        service = TaxonomyMatcherService()
        related = service.find_related_skills("React")
        assert len(related) > 0
        skill_names = [r.skill_name for r in related]
        assert "Vue" in skill_names
        assert "Angular" in skill_names
        assert "JavaScript" in skill_names

    def test_find_related_skills_python(self):
        """Test finding skills related to Python."""
        service = TaxonomyMatcherService()
        related = service.find_related_skills("Python")
        assert len(related) > 0
        skill_names = [r.skill_name for r in related]
        assert "Django" in skill_names
        assert "Flask" in skill_names

    def test_find_related_skills_sorted_by_weight(self):
        """Test that related skills are sorted by weight descending."""
        service = TaxonomyMatcherService()
        related = service.find_related_skills("React")
        if len(related) > 1:
            weights = [r.weight for r in related]
            assert weights == sorted(weights, reverse=True)

    def test_find_related_skills_with_type_filter(self):
        """Test filtering by relationship type."""
        service = TaxonomyMatcherService()
        related = service.find_related_skills("React", relationship_types=["similar"])
        assert len(related) > 0
        for skill in related:
            assert skill.relationship_type == "similar"

    def test_find_related_skills_with_min_weight(self):
        """Test filtering by minimum weight."""
        service = TaxonomyMatcherService()
        related = service.find_related_skills("React", min_weight=0.8)
        assert len(related) > 0
        for skill in related:
            assert skill.weight >= 0.8

    def test_find_related_skills_no_results(self):
        """Test when no related skills are found."""
        service = TaxonomyMatcherService()
        related = service.find_related_skills("UnknownSkill12345")
        assert len(related) == 0

    def test_find_related_skills_empty_string(self):
        """Test with empty skill name."""
        service = TaxonomyMatcherService()
        related = service.find_related_skills("")
        assert len(related) == 0

    def test_find_related_skills_none(self):
        """Test with None skill name."""
        service = TaxonomyMatcherService()
        related = service.find_related_skills(None)
        assert len(related) == 0

    def test_find_related_skills_invalid_weight_clamped(self):
        """Test that min_weight is clamped to valid range."""
        service = TaxonomyMatcherService()
        # Test negative weight
        related = service.find_related_skills("React", min_weight=-1.0)
        assert isinstance(related, list)

        # Test weight > 1
        related = service.find_related_skills("React", min_weight=2.0)
        assert len(related) == 0  # No skills should have weight > 1


class TestMatchSkill:
    """Tests for async match_skill method."""

    @pytest.mark.asyncio
    async def test_match_skill_invalid_input_empty(self):
        """Test match_skill with empty string."""
        service = TaxonomyMatcherService()
        result = await service.match_skill("")
        assert result.error is not None
        assert "non-empty string" in result.error

    @pytest.mark.asyncio
    async def test_match_skill_invalid_input_none(self):
        """Test match_skill with None."""
        service = TaxonomyMatcherService()
        result = await service.match_skill(None)
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_match_skill_no_db_fallback(self):
        """Test match_skill without database returns appropriate result."""
        service = TaxonomyMatcherService()
        result = await service.match_skill("SomeSkill")
        # Without DB, should not match
        assert result.matched_skill is None or result.match_type is None

    @pytest.mark.asyncio
    async def test_match_skill_with_db_exact_match(self):
        """Test match_skill with database exact match."""
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_taxonomy = Mock()
        mock_taxonomy.skill_name = "JavaScript"
        mock_taxonomy.id = uuid.uuid4()
        mock_taxonomy.industry = "tech"
        mock_taxonomy.context = "programming_language"
        mock_taxonomy.variants = ["JS", "js"]
        mock_taxonomy.extra_metadata = {}
        mock_taxonomy.parent_skill_id = None
        mock_taxonomy.category_path = ["Programming Languages"]
        mock_taxonomy.is_active = True
        mock_taxonomy.version = 1
        mock_taxonomy.organization_id = None
        mock_result.scalars.return_value.all.return_value = [mock_taxonomy]
        mock_db.execute.return_value = mock_result

        service = TaxonomyMatcherService(db=mock_db)
        result = await service.match_skill("javascript")

        assert result.matched_skill == "JavaScript"
        assert result.match_type == "exact"
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_match_skill_returns_taxonomymatchresult(self):
        """Test that match_skill returns TaxonomyMatchResult."""
        service = TaxonomyMatcherService()
        result = await service.match_skill("Python")
        assert isinstance(result, TaxonomyMatchResult)


class TestMatchSkills:
    """Tests for async match_skills method."""

    @pytest.mark.asyncio
    async def test_match_skills_invalid_input_empty_list(self):
        """Test match_skills with empty list."""
        service = TaxonomyMatcherService()
        result = await service.match_skills([])
        assert result["error"] is not None
        assert "non-empty list" in result["error"]

    @pytest.mark.asyncio
    async def test_match_skills_invalid_input_none(self):
        """Test match_skills with None."""
        service = TaxonomyMatcherService()
        result = await service.match_skills(None)
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_match_skills_returns_correct_structure(self):
        """Test that match_skills returns correct structure."""
        service = TaxonomyMatcherService()
        result = await service.match_skills(["Python", "JavaScript"])
        assert "matched" in result
        assert "unmatched" in result
        assert "matched_skills" in result
        assert "match_rate" in result
        assert "error" in result

    @pytest.mark.asyncio
    async def test_match_skills_match_rate_calculation(self):
        """Test match_rate calculation."""
        service = TaxonomyMatcherService()
        result = await service.match_skills(["Skill1", "Skill2"])
        assert isinstance(result["match_rate"], (int, float))
        assert 0 <= result["match_rate"] <= 100

    @pytest.mark.asyncio
    async def test_match_skills_handles_empty_strings(self):
        """Test that match_skills handles empty strings in list."""
        service = TaxonomyMatcherService()
        result = await service.match_skills(["", "Python", ""])
        # Should skip empty strings gracefully
        assert "error" not in result or result.get("matched") is not None


class TestResolveAliasAsync:
    """Tests for async resolve_alias_async method."""

    @pytest.mark.asyncio
    async def test_resolve_alias_async_invalid_input(self):
        """Test resolve_alias_async with invalid input."""
        service = TaxonomyMatcherService()
        result = await service.resolve_alias_async("")
        assert result is None

    @pytest.mark.asyncio
    async def test_resolve_alias_async_no_db_fallback(self):
        """Test resolve_alias_async falls back to sync method without DB."""
        service = TaxonomyMatcherService()
        result = await service.resolve_alias_async("JS")
        assert result is not None
        assert result.resolved_skill == "JavaScript"

    @pytest.mark.asyncio
    async def test_resolve_alias_async_with_db(self):
        """Test resolve_alias_async with database."""
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = TaxonomyMatcherService(db=mock_db)
        result = await service.resolve_alias_async("JS")

        # Should fall back to built-in aliases
        assert result is not None
        assert result.resolved_skill == "JavaScript"

    @pytest.mark.asyncio
    async def test_resolve_alias_async_caching(self):
        """Test that async alias resolution caches results."""
        service = TaxonomyMatcherService()
        result1 = await service.resolve_alias_async("JS")
        result2 = await service.resolve_alias_async("JS")
        assert result1 is result2


class TestFindRelatedSkillsAsync:
    """Tests for async find_related_skills_async method."""

    @pytest.mark.asyncio
    async def test_find_related_skills_async_invalid_input(self):
        """Test find_related_skills_async with invalid input."""
        service = TaxonomyMatcherService()
        result = await service.find_related_skills_async("")
        assert result == []

    @pytest.mark.asyncio
    async def test_find_related_skills_async_no_db_fallback(self):
        """Test find_related_skills_async falls back to sync method."""
        service = TaxonomyMatcherService()
        result = await service.find_related_skills_async("React")
        assert len(result) > 0
        skill_names = [r.skill_name for r in result]
        assert "Vue" in skill_names

    @pytest.mark.asyncio
    async def test_find_related_skills_async_with_db(self):
        """Test find_related_skills_async with database."""
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = TaxonomyMatcherService(db=mock_db)
        result = await service.find_related_skills_async("React")

        # Should fall back to built-in relationships
        assert isinstance(result, list)


class TestGetTaxonomyMatcherService:
    """Tests for factory function get_taxonomy_matcher_service."""

    def test_factory_default(self):
        """Test factory function with default values."""
        service = get_taxonomy_matcher_service()
        assert isinstance(service, TaxonomyMatcherService)
        assert service.db is None

    def test_factory_with_db(self):
        """Test factory function with database."""
        mock_db = Mock()
        service = get_taxonomy_matcher_service(db=mock_db)
        assert service.db == mock_db

    def test_factory_with_kwargs(self):
        """Test factory function with additional kwargs."""
        service = get_taxonomy_matcher_service(
            fuzzy_threshold=90,
            include_relationships=False,
        )
        assert service.fuzzy_threshold == 90
        assert service.include_relationships is False


class TestCommonSkillAliases:
    """Tests for built-in common skill aliases coverage."""

    def test_programming_language_aliases(self):
        """Test programming language alias resolution."""
        service = TaxonomyMatcherService()

        aliases = {
            "js": "JavaScript",
            "ts": "TypeScript",
            "py": "Python",
            "rb": "Ruby",
            "csharp": "C#",
            "cpp": "C++",
            "golang": "Go",
        }

        for alias, expected in aliases.items():
            result = service.resolve_alias(alias)
            assert result is not None, f"Failed to resolve '{alias}'"
            assert result.resolved_skill == expected, f"'{alias}' resolved to '{result.resolved_skill}' instead of '{expected}'"

    def test_framework_aliases(self):
        """Test framework alias resolution."""
        service = TaxonomyMatcherService()

        aliases = {
            "reactjs": "React",
            "vuejs": "Vue",
            "angularjs": "Angular",
            "nextjs": "Next.js",
            "nodejs": "Node.js",
        }

        for alias, expected in aliases.items():
            result = service.resolve_alias(alias)
            assert result is not None, f"Failed to resolve '{alias}'"
            assert result.resolved_skill == expected, f"'{alias}' resolved to '{result.resolved_skill}' instead of '{expected}'"

    def test_database_aliases(self):
        """Test database alias resolution."""
        service = TaxonomyMatcherService()

        aliases = {
            "postgres": "PostgreSQL",
            "postgresql": "PostgreSQL",
            "mongodb": "MongoDB",
        }

        for alias, expected in aliases.items():
            result = service.resolve_alias(alias)
            assert result is not None, f"Failed to resolve '{alias}'"
            assert result.resolved_skill == expected, f"'{alias}' resolved to '{result.resolved_skill}' instead of '{expected}'"

    def test_cloud_devops_aliases(self):
        """Test cloud/DevOps alias resolution."""
        service = TaxonomyMatcherService()

        aliases = {
            "aws": "Amazon Web Services",
            "gcp": "Google Cloud Platform",
            "azure": "Microsoft Azure",
            "k8s": "Kubernetes",
        }

        for alias, expected in aliases.items():
            result = service.resolve_alias(alias)
            assert result is not None, f"Failed to resolve '{alias}'"
            assert result.resolved_skill == expected, f"'{alias}' resolved to '{result.resolved_skill}' instead of '{expected}'"


class TestCommonSkillRelationships:
    """Tests for built-in common skill relationships coverage."""

    def test_react_relationships(self):
        """Test React skill relationships."""
        service = TaxonomyMatcherService()
        related = service.find_related_skills("React")
        skill_names = [r.skill_name for r in related]

        # React should have relationships with these skills
        assert "Vue" in skill_names
        assert "Angular" in skill_names
        assert "JavaScript" in skill_names
        assert "Next.js" in skill_names

    def test_python_relationships(self):
        """Test Python skill relationships."""
        service = TaxonomyMatcherService()
        related = service.find_related_skills("Python")
        skill_names = [r.skill_name for r in related]

        # Python should have relationships with these skills
        assert "Django" in skill_names
        assert "Flask" in skill_names
        assert "FastAPI" in skill_names

    def test_database_relationships(self):
        """Test database skill relationships."""
        service = TaxonomyMatcherService()
        related = service.find_related_skills("PostgreSQL")
        skill_names = [r.skill_name for r in related]

        # PostgreSQL should have relationship with MySQL
        assert "MySQL" in skill_names

    def test_relationship_types(self):
        """Test that relationships have valid types."""
        service = TaxonomyMatcherService()
        related = service.find_related_skills("React")

        valid_types = {"parent_child", "similar", "prerequisite", "related"}
        for skill in related:
            assert skill.relationship_type in valid_types


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_unicode_skill_names(self):
        """Test handling of Unicode characters in skill names."""
        service = TaxonomyMatcherService()
        result = service.resolve_alias("Café")
        # Should not crash, may return None
        assert result is None or isinstance(result, AliasResolution)

    def test_very_long_skill_name(self):
        """Test handling of very long skill names."""
        service = TaxonomyMatcherService()
        long_name = "A" * 1000
        result = service.resolve_alias(long_name)
        # Should not crash
        assert result is None or isinstance(result, AliasResolution)

    def test_special_characters_preserved(self):
        """Test that special characters are handled correctly."""
        service = TaxonomyMatcherService()

        # Test C#
        result = service.resolve_alias("csharp")
        assert result is not None
        assert result.resolved_skill == "C#"

        # Test C++
        result = service.resolve_alias("cpp")
        assert result is not None
        assert result.resolved_skill == "C++"

    def test_whitespace_handling(self):
        """Test handling of whitespace in skill names."""
        service = TaxonomyMatcherService()

        # Extra whitespace should be normalized
        result = service.resolve_alias("  JS  ")
        # May return None after normalization or still match
        assert result is None or result.resolved_skill == "JavaScript"

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test that concurrent operations work correctly."""
        service = TaxonomyMatcherService()

        # Run multiple async operations
        results = await service.match_skills(["React", "Vue", "Angular"])

        assert isinstance(results, dict)
        assert "matched" in results


class TestPrivateHelpers:
    """Tests for private helper methods."""

    @pytest.mark.asyncio
    async def test_taxonomy_to_dict(self):
        """Test _taxonomy_to_dict conversion."""
        mock_taxonomy = Mock()
        mock_taxonomy.id = uuid.uuid4()
        mock_taxonomy.industry = "tech"
        mock_taxonomy.skill_name = "JavaScript"
        mock_taxonomy.context = "programming_language"
        mock_taxonomy.variants = ["JS", "js"]
        mock_taxonomy.extra_metadata = {"key": "value"}
        mock_taxonomy.parent_skill_id = None
        mock_taxonomy.category_path = ["Programming"]
        mock_taxonomy.is_active = True
        mock_taxonomy.version = 1
        mock_taxonomy.organization_id = None

        service = TaxonomyMatcherService()
        result = service._taxonomy_to_dict(mock_taxonomy)

        assert result["skill_name"] == "JavaScript"
        assert result["industry"] == "tech"
        assert result["context"] == "programming_language"
        assert "JS" in result["variants"]
        assert result["is_active"] is True
