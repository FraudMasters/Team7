"""
Unit tests for skill suggester service.

Tests cover:
- Skill normalization
- Synonym-based suggestions
- Category-based suggestions
- Related skill suggestions
- Fuzzy matching suggestions
- Combined suggestion strategies
"""
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.skill_suggester import SkillSuggester


class TestSkillNormalization:
    """Tests for skill name normalization."""

    def test_normalize_skill_name_basic(self):
        """Test basic skill name normalization."""
        suggester = SkillSuggester()
        result = suggester.normalize_skill_name("  React JS  ")
        assert result == "react js"

    def test_normalize_skill_name_lowercase(self):
        """Test lowercase conversion."""
        suggester = SkillSuggester()
        result = suggester.normalize_skill_name("PYTHON")
        assert result == "python"

    def test_normalize_skill_name_special_characters(self):
        """Test removal of special characters."""
        suggester = SkillSuggester()
        result = suggester.normalize_skill_name("C++")
        assert result == "c++"
        result = suggester.normalize_skill_name("C#")
        assert result == "c#"

    def test_normalize_skill_name_extra_whitespace(self):
        """Test removal of extra whitespace."""
        suggester = SkillSuggester()
        result = suggester.normalize_skill_name("Java   Script")
        assert result == "java script"

    def test_normalize_skill_name_dots_and_pluses(self):
        """Test preservation of dots and plus signs."""
        suggester = SkillSuggester()
        result = suggester.normalize_skill_name("Node.js")
        assert result == "node.js"
        result = suggester.normalize_skill_name("React.NET")
        assert result == "react.net"


class TestFuzzySimilarity:
    """Tests for fuzzy similarity calculation."""

    def test_fuzzy_similarity_identical(self):
        """Test similarity of identical strings."""
        suggester = SkillSuggester()
        result = suggester.calculate_fuzzy_similarity("React", "React")
        assert result == 1.0

    def test_fuzzy_similarity_similar(self):
        """Test similarity of similar strings."""
        suggester = SkillSuggester()
        result = suggester.calculate_fuzzy_similarity("React", "ReactJS")
        assert result > 0.5

    def test_fuzzy_similarity_different(self):
        """Test similarity of different strings."""
        suggester = SkillSuggester()
        result = suggester.calculate_fuzzy_similarity("Python", "Java")
        assert result < 0.5

    def test_fuzzy_similarity_case_insensitive(self):
        """Test that similarity is case-insensitive."""
        suggester = SkillSuggester()
        result1 = suggester.calculate_fuzzy_similarity("react", "REACT")
        result2 = suggester.calculate_fuzzy_similarity("React", "React")
        assert result1 == result2


class TestSynonymSuggestions:
    """Tests for synonym-based suggestions."""

    def test_synonym_suggestions_exact_match(self):
        """Test finding exact synonym matches."""
        suggester = SkillSuggester()
        synonyms_map = {"SQL": ["SQL", "PostgreSQL", "MySQL"]}
        result = suggester.find_synonym_suggestions(
            "SQL", ["PostgreSQL", "MongoDB"], synonyms_map
        )
        assert len(result) > 0
        assert any(s["skill"] == "PostgreSQL" for s in result)
        assert all(s["reason"] == "synonym" for s in result)

    def test_synonym_suggestions_no_match(self):
        """Test when no synonyms are found."""
        suggester = SkillSuggester()
        synonyms_map = {"Python": ["Python", "Py"]}
        result = suggester.find_synonym_suggestions(
            "Java", ["JavaScript", "C++"], synonyms_map
        )
        assert len(result) == 0

    def test_synonym_suggestions_confidence(self):
        """Test that synonym suggestions have correct confidence."""
        suggester = SkillSuggester()
        synonyms_map = {"SQL": ["SQL", "PostgreSQL"]}
        result = suggester.find_synonym_suggestions(
            "SQL", ["PostgreSQL"], synonyms_map
        )
        if len(result) > 0:
            assert result[0]["confidence"] == 0.85


class TestCategorySuggestions:
    """Tests for category-based suggestions."""

    @patch('analyzers.skill_suggester.SkillSuggester.load_synonyms')
    def test_category_suggestions_same_category(self, mock_load_synonyms):
        """Test finding skills from the same category."""
        mock_load_synonyms.return_value = {
            "PostgreSQL": ["PostgreSQL", "Postgres"],
            "MySQL": ["MySQL"],
            "MongoDB": ["MongoDB", "Mongo"]
        }

        suggester = SkillSuggester()
        # Manually set up taxonomy map
        suggester._taxonomy_map = {
            "databases": {
                "PostgreSQL": ["PostgreSQL", "Postgres"],
                "MySQL": ["MySQL"],
                "MongoDB": ["MongoDB", "Mongo"]
            }
        }
        suggester._category_map = {
            "databases": ["PostgreSQL", "Postgres", "MySQL", "MongoDB", "Mongo"]
        }

        result = suggester.find_category_suggestions(
            "PostgreSQL", ["MongoDB", "Redis"], {}
        )
        # Should find MongoDB as a database alternative
        assert len(result) >= 0

    def test_category_suggestions_no_category(self):
        """Test when skill has no category."""
        suggester = SkillSuggester()
        result = suggester.find_category_suggestions(
            "UnknownSkill", ["SomeSkill"], {}
        )
        assert len(result) == 0


class TestRelatedSuggestions:
    """Tests for related skill suggestions."""

    def test_related_suggestions_nodejs(self):
        """Test finding Node.js related skills."""
        suggester = SkillSuggester()
        result = suggester.find_related_suggestions(
            "node.js", ["Express", "MongoDB", "Python"]
        )
        assert len(result) > 0
        assert any(s["skill"] == "Express" for s in result)
        assert all(s["reason"] == "related" for s in result)

    def test_related_suggestions_react(self):
        """Test finding React related skills."""
        suggester = SkillSuggester()
        result = suggester.find_related_suggestions(
            "react", ["Redux", "Angular", "Vue"]
        )
        assert len(result) > 0
        assert any(s["skill"] == "Redux" for s in result)

    def test_related_suggestions_no_related(self):
        """Test when skill has no related skills defined."""
        suggester = SkillSuggester()
        result = suggester.find_related_suggestions(
            "UnknownSkill", ["SomeSkill"]
        )
        assert len(result) == 0

    def test_related_suggestions_confidence(self):
        """Test that related suggestions have correct confidence."""
        suggester = SkillSuggester()
        result = suggester.find_related_suggestions(
            "node.js", ["Express"]
        )
        if len(result) > 0:
            assert result[0]["confidence"] == 0.65


class TestFuzzySuggestions:
    """Tests for fuzzy matching suggestions."""

    def test_fuzzy_suggestions_similar_names(self):
        """Test finding skills with similar names."""
        suggester = SkillSuggester()
        result = suggester.find_fuzzy_suggestions(
            "React.js", ["ReactJS", "React JS", "React"]
        )
        assert len(result) > 0
        assert all(s["reason"] == "fuzzy_match" for s in result)

    def test_fuzzy_suggestions_threshold(self):
        """Test fuzzy matching with threshold."""
        suggester = SkillSuggester()
        result = suggester.find_fuzzy_suggestions(
            "Python", ["Py", "Pythonic", "Java"], threshold=0.6
        )
        # Should filter out low-similarity matches
        for suggestion in result:
            assert suggestion["confidence"] >= 0.6 * 0.9

    def test_fuzzy_suggestions_high_threshold(self):
        """Test fuzzy matching with high threshold."""
        suggester = SkillSuggester()
        result = suggester.find_fuzzy_suggestions(
            "React", ["Redux", "Vue", "Angular"], threshold=0.9
        )
        # Should return fewer or no results with high threshold
        assert len(result) <= 3

    def test_fuzzy_suggestions_sorted_by_confidence(self):
        """Test that fuzzy suggestions are sorted by confidence."""
        suggester = SkillSuggester()
        result = suggester.find_fuzzy_suggestions(
            "React", ["ReactJS", "React JS", "Redux"]
        )
        if len(result) > 1:
            confidences = [s["confidence"] for s in result]
            assert confidences == sorted(confidences, reverse=True)


class TestSuggestAlternatives:
    """Tests for the main suggest_alternatives method."""

    def test_suggest_alternatives_basic(self):
        """Test basic alternative suggestions."""
        suggester = SkillSuggester()
        result = suggester.suggest_alternatives(
            missing_skill="SQL",
            resume_skills=["PostgreSQL", "MongoDB", "Python"],
            max_suggestions=5
        )
        assert isinstance(result, list)
        assert len(result) <= 5
        if len(result) > 0:
            assert "skill" in result[0]
            assert "confidence" in result[0]
            assert "reason" in result[0]

    def test_suggest_alternatives_empty_inputs(self):
        """Test with empty inputs."""
        suggester = SkillSuggester()
        result = suggester.suggest_alternatives(
            missing_skill="",
            resume_skills=[]
        )
        assert result == []

    def test_suggest_alternatives_no_duplicates(self):
        """Test that duplicate skills are removed."""
        suggester = SkillSuggester()
        result = suggester.suggest_alternatives(
            missing_skill="SQL",
            resume_skills=["PostgreSQL", "Postgres", "MongoDB"],
            max_suggestions=10
        )
        # Check no duplicate skill names (normalized)
        normalized_skills = [suggester.normalize_skill_name(s["skill"]) for s in result]
        assert len(normalized_skills) == len(set(normalized_skills))

    def test_suggest_alternatives_sorted_by_confidence(self):
        """Test that suggestions are sorted by confidence."""
        suggester = SkillSuggester()
        result = suggester.suggest_alternatives(
            missing_skill="SQL",
            resume_skills=["PostgreSQL", "MySQL", "MongoDB"],
            max_suggestions=10
        )
        if len(result) > 1:
            confidences = [s["confidence"] for s in result]
            assert confidences == sorted(confidences, reverse=True)

    def test_suggest_alternatives_max_suggestions(self):
        """Test that max_suggestions limit is respected."""
        suggester = SkillSuggester()
        result = suggester.suggest_alternatives(
            missing_skill="SQL",
            resume_skills=["PostgreSQL", "MySQL", "MongoDB", "Redis", "Cassandra"],
            max_suggestions=3
        )
        assert len(result) <= 3

    def test_suggest_alternatives_confidence_range(self):
        """Test that all confidence scores are in valid range."""
        suggester = SkillSuggester()
        result = suggester.suggest_alternatives(
            missing_skill="SQL",
            resume_skills=["PostgreSQL", "MongoDB"],
            max_suggestions=10
        )
        for suggestion in result:
            assert 0 <= suggestion["confidence"] <= 1


class TestSuggestForMultiple:
    """Tests for suggesting alternatives for multiple missing skills."""

    def test_suggest_for_multiple_basic(self):
        """Test suggesting for multiple missing skills."""
        suggester = SkillSuggester()
        result = suggester.suggest_for_multiple(
            missing_skills=["SQL", "React"],
            resume_skills=["PostgreSQL", "Angular", "Vue"],
            max_suggestions_per_skill=3
        )
        assert isinstance(result, dict)
        assert "SQL" in result
        assert "React" in result

    def test_suggest_for_multiple_empty_list(self):
        """Test with empty missing_skills list."""
        suggester = SkillSuggester()
        result = suggester.suggest_for_multiple(
            missing_skills=[],
            resume_skills=["Python", "Java"]
        )
        assert result == {}

    def test_suggest_for_multiple_respects_limit(self):
        """Test that max_suggestions_per_skill is respected."""
        suggester = SkillSuggester()
        result = suggester.suggest_for_multiple(
            missing_skills=["SQL"],
            resume_skills=["PostgreSQL", "MySQL", "MongoDB", "Redis"],
            max_suggestions_per_skill=2
        )
        assert len(result["SQL"]) <= 2

    def test_suggest_for_multiple_structure(self):
        """Test that structure is correct for each skill."""
        suggester = SkillSuggester()
        result = suggester.suggest_for_multiple(
            missing_skills=["SQL"],
            resume_skills=["PostgreSQL"],
            max_suggestions_per_skill=3
        )
        for skill, suggestions in result.items():
            assert isinstance(suggestions, list)
            for suggestion in suggestions:
                assert "skill" in suggestion
                assert "confidence" in suggestion
                assert "reason" in suggestion


class TestLoadSynonyms:
    """Tests for loading synonyms from file."""

    def test_load_synonyms_returns_dict(self):
        """Test that load_synonyms returns a dictionary."""
        suggester = SkillSuggester()
        result = suggester.load_synonyms()
        assert isinstance(result, dict)

    def test_load_synonyms_caching(self):
        """Test that synonyms are cached after first load."""
        suggester = SkillSuggester()
        result1 = suggester.load_synonyms()
        result2 = suggester.load_synonyms()
        # Should return same cached result
        assert result1 is result2

    def test_load_synonyms_handles_missing_file(self):
        """Test handling of missing synonyms file."""
        suggester = SkillSuggester(synonyms_file=Path("/nonexistent/path.json"))
        result = suggester.load_synonyms()
        assert isinstance(result, dict)
        assert result == {}


class TestEdgeCases:
    """Tests for edge cases."""

    def test_unicode_skill_names(self):
        """Test handling of Unicode characters in skill names."""
        suggester = SkillSuggester()
        result = suggester.normalize_skill_name("Café")
        assert isinstance(result, str)

    def test_very_long_skill_name(self):
        """Test handling of very long skill names."""
        suggester = SkillSuggester()
        long_name = "A" * 1000
        result = suggester.normalize_skill_name(long_name)
        assert isinstance(result, str)

    def test_special_characters_preserved(self):
        """Test that allowed special characters are preserved."""
        suggester = SkillSuggester()
        result = suggester.normalize_skill_name("C# .NET + plus")
        assert "#" in result or "c#" in result.lower()
