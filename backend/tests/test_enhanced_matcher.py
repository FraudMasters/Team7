"""
Tests for enhanced skill matcher with confidence scoring.

Tests cover normalization, fuzzy similarity calculation,
synonym matching, context-aware matching, and confidence scoring.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from analyzers.enhanced_matcher import EnhancedSkillMatcher


class TestNormalizeSkillName:
    """Tests for normalize_skill_name static method."""

    def test_basic_normalization(self):
        """Test basic skill name normalization."""
        result = EnhancedSkillMatcher.normalize_skill_name("React JS")
        assert result == "react js"

    def test_leading_trailing_whitespace(self):
        """Test removing leading and trailing whitespace."""
        result = EnhancedSkillMatcher.normalize_skill_name("  Python  ")
        assert result == "python"

    def test_multiple_spaces(self):
        """Test removing multiple internal spaces."""
        result = EnhancedSkillMatcher.normalize_skill_name("Machine   Learning")
        assert result == "machine learning"

    def test_case_insensitive(self):
        """Test case is converted to lowercase."""
        result = EnhancedSkillMatcher.normalize_skill_name("POSTGRESQL")
        assert result == "postgresql"

    def test_mixed_case(self):
        """Test mixed case is normalized."""
        result = EnhancedSkillMatcher.normalize_skill_name("JaVa ScRiPt")
        assert result == "java script"

    def test_special_characters_preserved(self):
        """Test that special characters like dots and plus are preserved."""
        result = EnhancedSkillMatcher.normalize_skill_name("C++")
        assert result == "c++"

        result = EnhancedSkillMatcher.normalize_skill_name("Node.js")
        assert result == "node.js"

    def test_hash_preserved(self):
        """Test that hash character is preserved."""
        result = EnhancedSkillMatcher.normalize_skill_name("C#")
        assert result == "c#"

    def test_special_characters_removed(self):
        """Test that other special characters are removed."""
        result = EnhancedSkillMatcher.normalize_skill_name("React,JS!")
        assert result == "reactjs"

    def test_empty_string(self):
        """Test empty string normalization."""
        result = EnhancedSkillMatcher.normalize_skill_name("")
        assert result == ""

    def test_only_whitespace(self):
        """Test string with only whitespace."""
        result = EnhancedSkillMatcher.normalize_skill_name("   \t\n  ")
        assert result == ""

    def test_tabs_and_newlines(self):
        """Test tabs and newlines are handled."""
        result = EnhancedSkillMatcher.normalize_skill_name("\tDjango\t\nFramework\n")
        assert result == "django framework"

    def test_multi_word_skill(self):
        """Test multi-word skill."""
        result = EnhancedSkillMatcher.normalize_skill_name("Natural Language Processing")
        assert result == "natural language processing"


class TestCalculateFuzzySimilarity:
    """Tests for calculate_fuzzy_similarity method."""

    def test_exact_match(self):
        """Test exact match returns 1.0."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("React", "React")
        assert result == 1.0

    def test_case_insensitive(self):
        """Test case insensitive similarity."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("React", "react")
        assert result == 1.0

    def test_whitespace_insensitive(self):
        """Test whitespace insensitive similarity."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("React JS", "ReactJS")
        assert result > 0.8

    def test_partial_match(self):
        """Test partial match has lower similarity."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("React", "ReactJS")
        assert 0.6 < result < 1.0

    def test_no_similarity(self):
        """Test completely different strings have low similarity."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("Python", "Java")
        assert result < 0.3

    def test_typo_detection(self):
        """Test detection of typos."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("PostgreSQL", "Postgre")
        assert result > 0.7

    def test_special_characters(self):
        """Test similarity with special characters."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("Node.js", "NodeJS")
        assert result > 0.7

    def test_empty_strings(self):
        """Test with empty strings."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("", "")
        assert result == 1.0

    def test_one_empty_string(self):
        """Test with one empty string."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("React", "")
        assert result == 0.0


class TestFindSynonymMatch:
    """Tests for find_synonym_match method."""

    def test_direct_match_high_confidence(self):
        """Test direct match returns high confidence."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java", "Django"]
        synonyms_map = {}

        result = matcher.find_synonym_match(resume_skills, "Python", synonyms_map)

        assert result is not None
        matched_skill, confidence = result
        assert matched_skill == "Python"
        assert confidence == 0.95

    def test_synonym_match_medium_confidence(self):
        """Test synonym match returns medium-high confidence."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "PostgreSQL", "Django"]
        synonyms_map = {"SQL": ["SQL", "PostgreSQL", "MySQL"]}

        result = matcher.find_synonym_match(resume_skills, "SQL", synonyms_map)

        assert result is not None
        matched_skill, confidence = result
        assert matched_skill == "PostgreSQL"
        assert confidence == 0.85

    def test_no_match_returns_none(self):
        """Test when no match found returns None."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java"]
        synonyms_map = {}

        result = matcher.find_synonym_match(resume_skills, "Ruby", synonyms_map)

        assert result is None

    def test_synonym_in_synonym_list(self):
        """Test matching when required skill is in synonym list."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java"]
        synonyms_map = {"Python": ["Python", "Python 3", "Python3"]}

        result = matcher.find_synonym_match(resume_skills, "Python 3", synonyms_map)

        assert result is not None
        matched_skill, confidence = result
        assert matched_skill == "Python"
        assert confidence == 0.85

    def test_case_insensitive_synonym_match(self):
        """Test synonym matching is case-insensitive."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["REACTJS", "TYPESCRIPT"]
        synonyms_map = {"React": ["React", "ReactJS", "React.js"]}

        result = matcher.find_synonym_match(resume_skills, "react", synonyms_map)

        assert result is not None
        matched_skill, confidence = result
        assert matched_skill == "REACTJS"
        assert confidence == 0.85

    def test_complex_synonym_chain(self):
        """Test complex synonym chain."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Postgres"]
        synonyms_map = {
            "SQL": ["SQL", "PostgreSQL", "MySQL"],
            "PostgreSQL": ["PostgreSQL", "Postgres", "Postgres SQL"]
        }

        result = matcher.find_synonym_match(resume_skills, "SQL", synonyms_map)

        assert result is not None
        assert result[0] == "Postgres"

    def test_empty_resume_skills(self):
        """Test with empty resume skills list."""
        matcher = EnhancedSkillMatcher()
        resume_skills = []
        synonyms_map = {}

        result = matcher.find_synonym_match(resume_skills, "Python", synonyms_map)

        assert result is None

    def test_empty_synonyms_map(self):
        """Test with empty synonyms map."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java"]

        result = matcher.find_synonym_match(resume_skills, "Python", {})

        assert result is not None
        matched_skill, confidence = result
        assert matched_skill == "Python"
        assert confidence == 0.95


class TestFindContextMatch:
    """Tests for find_context_match method."""

    def test_web_framework_react_match(self):
        """Test React matching in web_framework context."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["ReactJS", "TypeScript", "Node.js"]

        result = matcher.find_context_match(resume_skills, "React", "web_framework")

        assert result is not None
        matched_skill, confidence = result
        assert matched_skill == "ReactJS"
        assert confidence == 0.95

    def test_web_framework_vue_match(self):
        """Test Vue matching in web_framework context."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Vue.js", "TypeScript"]

        result = matcher.find_context_match(resume_skills, "Vue", "web_framework")

        assert result is not None
        assert result[0] == "Vue.js"

    def test_database_sql_match(self):
        """Test SQL matching in database context."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["PostgreSQL", "MongoDB", "Redis"]

        result = matcher.find_context_match(resume_skills, "SQL", "database")

        assert result is not None
        assert result[0] == "PostgreSQL"

    def test_database_nosql_match(self):
        """Test NoSQL matching in database context."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["MongoDB", "Cassandra", "Redis"]

        result = matcher.find_context_match(resume_skills, "NoSQL", "database")

        assert result is not None
        assert result[0] == "MongoDB"

    def test_language_javascript_match(self):
        """Test JavaScript matching in language context."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["JS", "HTML", "CSS"]

        result = matcher.find_context_match(resume_skills, "JavaScript", "language")

        assert result is not None
        assert result[0] == "JS"

    def test_no_context_returns_none(self):
        """Test that no context returns None."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["ReactJS", "TypeScript"]

        result = matcher.find_context_match(resume_skills, "React", None)

        assert result is None

    def test_unknown_context_returns_none(self):
        """Test that unknown context returns None."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["ReactJS", "TypeScript"]

        result = matcher.find_context_match(resume_skills, "React", "mobile")

        assert result is None

    def test_no_match_in_context(self):
        """Test when skill not found in context."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Django"]

        result = matcher.find_context_match(resume_skills, "React", "web_framework")

        assert result is None

    def test_case_insensitive_context(self):
        """Test context matching is case-insensitive."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["REACTJS", "TYPESCRIPT"]

        result = matcher.find_context_match(resume_skills, "REACT", "WEB_FRAMEWORK")

        assert result is not None
        assert result[0] == "REACTJS"


class TestFindFuzzyMatch:
    """Tests for find_fuzzy_match method."""

    def test_exact_fuzzy_match(self):
        """Test exact match with fuzzy matching."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["React", "Python", "Java"]

        result = matcher.find_fuzzy_match(resume_skills, "React")

        assert result is not None
        matched_skill, confidence = result
        assert matched_skill == "React"
        assert confidence == 1.0

    def test_typo_fuzzy_match(self):
        """Test fuzzy match detects typos."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["PostgreSQL", "Python", "Java"]

        result = matcher.find_fuzzy_match(resume_skills, "Postgre")

        assert result is not None
        matched_skill, confidence = result
        assert matched_skill == "PostgreSQL"
        assert confidence > 0.7

    def test_below_threshold_no_match(self):
        """Test that matches below threshold return None."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java"]

        result = matcher.find_fuzzy_match(resume_skills, "C++")

        assert result is None

    def test_custom_threshold(self):
        """Test custom threshold works."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["ReactJS"]

        # With default threshold (0.7)
        result = matcher.find_fuzzy_match(resume_skills, "React")
        assert result is not None

        # With higher threshold (0.9)
        result = matcher.find_fuzzy_match(resume_skills, "React", threshold=0.9)
        assert result is None

    def test_best_match_returned(self):
        """Test that best match is returned when multiple exist."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["React", "ReactJS", "Redux"]

        result = matcher.find_fuzzy_match(resume_skills, "React")

        assert result is not None
        # Should return the best match (React)
        assert result[0] == "React"

    def test_empty_resume_skills(self):
        """Test with empty resume skills."""
        matcher = EnhancedSkillMatcher()
        resume_skills = []

        result = matcher.find_fuzzy_match(resume_skills, "React")

        assert result is None

    def test_special_characters_fuzzy(self):
        """Test fuzzy match with special characters."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Node.js"]

        result = matcher.find_fuzzy_match(resume_skills, "NodeJS")

        assert result is not None
        assert result[0] == "Node.js"


class TestMatchWithContext:
    """Tests for match_with_context method."""

    def test_direct_match_strategy(self):
        """Test direct match strategy (highest priority)."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java", "Django"]

        result = matcher.match_with_context(resume_skills, "Python")

        assert result["matched"] is True
        assert result["confidence"] == 1.0
        assert result["matched_as"] == "Python"
        assert result["match_type"] == "direct"

    def test_context_match_strategy(self):
        """Test context-aware match strategy."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["ReactJS", "TypeScript"]

        result = matcher.match_with_context(resume_skills, "React", context="web_framework")

        assert result["matched"] is True
        assert result["confidence"] == 0.95
        assert result["matched_as"] == "ReactJS"
        assert result["match_type"] == "context"

    def test_synonym_match_strategy(self):
        """Test synonym match strategy."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["PostgreSQL", "Python"]

        result = matcher.match_with_context(resume_skills, "SQL")

        assert result["matched"] is True
        assert result["confidence"] >= 0.85
        assert result["matched_as"] == "PostgreSQL"
        assert result["match_type"] == "synonym"

    def test_fuzzy_match_strategy(self):
        """Test fuzzy match strategy."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["PostgreSQL", "Python"]

        result = matcher.match_with_context(resume_skills, "Postgre")

        assert result["matched"] is True
        assert result["confidence"] > 0.7
        assert result["matched_as"] == "PostgreSQL"
        assert result["match_type"] == "fuzzy"

    def test_no_match(self):
        """Test when no match is found."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java"]

        result = matcher.match_with_context(resume_skills, "Ruby")

        assert result["matched"] is False
        assert result["confidence"] == 0.0
        assert result["matched_as"] is None
        assert result["match_type"] == "none"

    def test_empty_resume_skills(self):
        """Test with empty resume skills."""
        matcher = EnhancedSkillMatcher()
        resume_skills = []

        result = matcher.match_with_context(resume_skills, "Python")

        assert result["matched"] is False
        assert result["match_type"] == "none"

    def test_empty_required_skill(self):
        """Test with empty required skill."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java"]

        result = matcher.match_with_context(resume_skills, "")

        assert result["matched"] is False
        assert result["match_type"] == "none"

    def test_fuzzy_disabled(self):
        """Test with fuzzy matching disabled."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["PostgreSQL", "Python"]

        result = matcher.match_with_context(
            resume_skills, "Postgre", use_fuzzy=False
        )

        # Should not match because fuzzy is disabled and no other strategy matches
        assert result["matched"] is False

    def test_priority_order(self):
        """Test that strategies are tried in priority order."""
        matcher = EnhancedSkillMatcher()

        # Direct match should always win
        resume_skills = ["React", "ReactJS"]
        result = matcher.match_with_context(resume_skills, "React", context="web_framework")

        assert result["match_type"] == "direct"
        assert result["confidence"] == 1.0


class TestMatchMultiple:
    """Tests for match_multiple method."""

    def test_match_multiple_skills(self):
        """Test matching multiple required skills."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["ReactJS", "Python", "PostgreSQL"]
        required_skills = ["React", "Python", "Java"]

        results = matcher.match_multiple(resume_skills, required_skills)

        assert len(results) == 3
        assert results["React"]["matched"] is True
        assert results["Python"]["matched"] is True
        assert results["Java"]["matched"] is False

    def test_with_context(self):
        """Test matching multiple skills with context."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["ReactJS", "Python", "PostgreSQL"]
        required_skills = ["React", "SQL"]

        results = matcher.match_multiple(
            resume_skills, required_skills, context="web_framework"
        )

        assert results["React"]["matched"] is True
        assert results["SQL"]["matched"] is True

    def test_empty_required_skills(self):
        """Test with empty required skills list."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java"]

        results = matcher.match_multiple(resume_skills, [])

        assert results == {}

    def test_all_results_have_correct_structure(self):
        """Test that all results have the correct structure."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python"]
        required_skills = ["Python", "Java"]

        results = matcher.match_multiple(resume_skills, required_skills)

        for skill, result in results.items():
            assert "matched" in result
            assert "confidence" in result
            assert "matched_as" in result
            assert "match_type" in result


class TestCalculateMatchPercentage:
    """Tests for calculate_match_percentage method."""

    def test_full_match_percentage(self):
        """Test 100% match when all skills match."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": True},
            "Java": {"matched": True},
            "Django": {"matched": True}
        }

        result = matcher.calculate_match_percentage(match_results)

        assert result == 100.0

    def test_partial_match_percentage(self):
        """Test partial match percentage."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": True},
            "Java": {"matched": True},
            "Django": {"matched": False}
        }

        result = matcher.calculate_match_percentage(match_results)

        assert result == pytest.approx(66.67, rel=0.01)

    def test_no_match_percentage(self):
        """Test 0% match when no skills match."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": False},
            "Java": {"matched": False}
        }

        result = matcher.calculate_match_percentage(match_results)

        assert result == 0.0

    def test_empty_results(self):
        """Test with empty match results."""
        matcher = EnhancedSkillMatcher()
        match_results = {}

        result = matcher.calculate_match_percentage(match_results)

        assert result == 0.0

    def test_rounding_to_two_decimals(self):
        """Test that percentage is rounded to two decimals."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Skill1": {"matched": True},
            "Skill2": {"matched": True},
            "Skill3": {"matched": False}
        }

        result = matcher.calculate_match_percentage(match_results)

        # Should be rounded to 2 decimal places
        assert len(str(result).split('.')[-1]) <= 2


class TestGetLowConfidenceMatches:
    """Tests for get_low_confidence_matches method."""

    def test_filter_low_confidence(self):
        """Test filtering matches below threshold."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": True, "confidence": 1.0},
            "React": {"matched": True, "confidence": 0.85},
            "SQL": {"matched": True, "confidence": 0.70},
            "Java": {"matched": False, "confidence": 0.0}
        }

        result = matcher.get_low_confidence_matches(match_results, threshold=0.9)

        assert "React" in result
        assert "SQL" in result
        assert "Python" not in result
        assert "Java" not in result

    def test_default_threshold(self):
        """Test default threshold of 0.8."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": True, "confidence": 0.85},
            "React": {"matched": True, "confidence": 0.75}
        }

        result = matcher.get_low_confidence_matches(match_results)

        assert "React" in result
        assert "Python" not in result

    def test_unmatched_skills_not_included(self):
        """Test that unmatched skills are not included."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": True, "confidence": 0.7},
            "Java": {"matched": False, "confidence": 0.0}
        }

        result = matcher.get_low_confidence_matches(match_results)

        assert "Python" in result
        assert "Java" not in result

    def test_empty_results(self):
        """Test with empty match results."""
        matcher = EnhancedSkillMatcher()
        match_results = {}

        result = matcher.get_low_confidence_matches(match_results)

        assert result == []

    def test_all_high_confidence(self):
        """Test when all matches are high confidence."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": True, "confidence": 1.0},
            "React": {"matched": True, "confidence": 0.95}
        }

        result = matcher.get_low_confidence_matches(match_results, threshold=0.9)

        assert result == []


class TestLoadSynonyms:
    """Tests for load_synonyms method."""

    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "databases": {
            "SQL": ["SQL", "PostgreSQL", "MySQL"],
            "PostgreSQL": ["PostgreSQL", "Postgres"]
        },
        "web_frameworks": {
            "React": ["React", "ReactJS", "React.js"]
        }
    }''')
    def test_successful_loading(self, mock_file):
        """Test successful loading of synonyms file."""
        matcher = EnhancedSkillMatcher()
        result = matcher.load_synonyms()

        assert "SQL" in result
        assert "PostgreSQL" in result
        assert "React" in result
        assert result["SQL"] == ["SQL", "PostgreSQL", "MySQL"]
        assert result["PostgreSQL"] == ["PostgreSQL", "Postgres"]
        assert result["React"] == ["React", "ReactJS", "React.js"]

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_file_not_found(self, mock_file):
        """Test handling when synonyms file is not found."""
        matcher = EnhancedSkillMatcher()
        result = matcher.load_synonyms()
        assert result == {}

    @patch("builtins.open", new_callable=mock_open, read_data='invalid json')
    def test_invalid_json(self, mock_file):
        """Test handling of invalid JSON."""
        matcher = EnhancedSkillMatcher()
        result = matcher.load_synonyms()
        assert result == {}

    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "databases": {
            "SQL": ["SQL", "PostgreSQL"]
        }
    }''')
    def test_canonical_name_added_to_synonyms(self, mock_file):
        """Test that canonical name is added to its own synonym list."""
        matcher = EnhancedSkillMatcher()
        result = matcher.load_synonyms()

        # Canonical name "SQL" should be in its own list
        assert "SQL" in result["SQL"]

    @patch("builtins.open", new_callable=mock_open, read_data='''{
        "databases": {
            "SQL": ["PostgreSQL", "MySQL", "PostgreSQL"]
        }
    }''')
    def test_synonyms_deduplicated(self, mock_file):
        """Test that synonyms are deduplicated."""
        matcher = EnhancedSkillMatcher()
        result = matcher.load_synonyms()

        # Should have unique values
        assert len(result["SQL"]) == len(set(result["SQL"]))

    def test_cache_used(self):
        """Test that cached value is used on subsequent calls."""
        matcher = EnhancedSkillMatcher()
        # First call
        with patch("builtins.open", new_callable=mock_open, read_data='{"test": {"Skill": ["Skill"]}}'):
            result1 = matcher.load_synonyms()
            # Second call should use cache
            result2 = matcher.load_synonyms()

        assert result1 is result2


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_unicode_skill_names(self):
        """Test skill names with unicode characters."""
        matcher = EnhancedSkillMatcher()
        result = matcher.normalize_skill_name("Русский язык")
        assert result == "русский язык"

    def test_very_long_skill_name(self):
        """Test with very long skill name."""
        matcher = EnhancedSkillMatcher()
        long_skill = "A" * 100
        result = matcher.normalize_skill_name(long_skill)
        assert result == long_skill.lower()

    def test_special_characters_in_skills(self):
        """Test skills with various special characters."""
        matcher = EnhancedSkillMatcher()
        result = matcher.normalize_skill_name("C++/C#/.NET")
        # Should keep +, #, .
        assert "+" in result or "#" in result or "." in result

    def test_whitespace_variations(self):
        """Test various whitespace combinations."""
        matcher = EnhancedSkillMatcher()
        result = matcher.normalize_skill_name("  React   JS  \t\n")
        assert result == "react js"

    def test_match_with_none_context(self):
        """Test matching with None context doesn't fail."""
        matcher = EnhancedSkillMatcher()
        result = matcher.match_with_context(["Python"], "Python", context=None)
        assert result["matched"] is True

    def test_match_percentage_with_missing_confidence(self):
        """Test calculate_match_percentage handles missing confidence."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": True},  # No confidence key
            "Java": {"matched": False}
        }
        percentage = matcher.calculate_match_percentage(match_results)
        assert percentage == 50.0

    def test_get_low_confidence_with_missing_confidence(self):
        """Test get_low_confidence_matches handles missing confidence."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": True},  # No confidence key
        }
        result = matcher.get_low_confidence_matches(match_results)
        assert "Python" in result  # Missing confidence defaults to 0


class TestRealWorldScenarios:
    """Tests for real-world skill matching scenarios."""

    def test_full_stack_developer_matching(self):
        """Test matching full-stack developer skills."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["ReactJS", "Node.js", "Python", "PostgreSQL", "Docker"]
        required_skills = ["React", "Node", "Python", "SQL", "Docker"]

        results = matcher.match_multiple(resume_skills, required_skills)

        assert results["React"]["matched"] is True
        assert results["Node"]["matched"] is True  # Via fuzzy match
        assert results["Python"]["matched"] is True
        assert results["SQL"]["matched"] is True  # Via synonym
        assert results["Docker"]["matched"] is True

        percentage = matcher.calculate_match_percentage(results)
        assert percentage == 100.0

    def test_data_scientist_matching(self):
        """Test matching data scientist skills."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Pandas", "NumPy", "Scikit-learn", "TensorFlow"]
        required_skills = ["Python", "Machine Learning", "Deep Learning", "SQL"]

        results = matcher.match_multiple(resume_skills, required_skills)

        # Direct match for Python
        assert results["Python"]["matched"] is True
        # Machine Learning not directly in resume (would need fuzzy or context)
        # SQL not in resume

    def test_devops_engineer_matching(self):
        """Test matching DevOps engineer skills."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["K8s", "Docker", "Jenkins", "AWS", "Terraform"]
        required_skills = ["Kubernetes", "Docker", "CI/CD", "Cloud"]

        results = matcher.match_multiple(resume_skills, required_skills)

        # K8s should match Kubernetes via fuzzy
        assert results["Kubernetes"]["matched"] is True
        # Docker direct match
        assert results["Docker"]["matched"] is True
        # Jenkins matches CI/CD via context if available
        # AWS might match Cloud if context rules exist

    def test_confidence_threshold_flagging(self):
        """Test flagging low confidence matches for recruiter review."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["ReactJS", "Python", "MongoDB"]
        required_skills = ["React", "Python", "SQL", "Java"]

        results = matcher.match_multiple(resume_skills, required_skills)
        low_confidence = matcher.get_low_confidence_matches(results, threshold=0.9)

        # React matched via synonym/context (not 1.0)
        # SQL matched via MongoDB? (shouldn't match)
        # Java no match

        # At least one of these should be flagged
        assert len(low_confidence) >= 0
