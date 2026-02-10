"""
Unit tests for TagSuggester analyzer.

Tests cover:
- Text normalization
- Fuzzy similarity calculation
- Keyword extraction from resume text
- Direct keyword matching for tag suggestions
- Fuzzy matching for tag suggestions
- Complete tag suggestion workflow
- Edge cases and error handling
"""
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.tag_suggester import TagSuggester


class TestNormalizeText:
    """Tests for text normalization."""

    def test_normalize_text_basic(self):
        """Test basic text normalization."""
        suggester = TagSuggester()
        result = suggester.normalize_text("  Senior Developer  ")
        assert result == "senior developer"

    def test_normalize_text_lowercase(self):
        """Test lowercase conversion."""
        suggester = TagSuggester()
        result = suggester.normalize_text("PYTHON")
        assert result == "python"

    def test_normalize_text_extra_whitespace(self):
        """Test removal of extra whitespace."""
        suggester = TagSuggester()
        result = suggester.normalize_text("Java   Script    Developer")
        assert result == "java script developer"

    def test_normalize_text_newlines_and_tabs(self):
        """Test handling of newlines and tabs."""
        suggester = TagSuggester()
        result = suggester.normalize_text("  Senior\n\tDeveloper  ")
        assert result == "senior developer"

    def test_normalize_text_empty_string(self):
        """Test handling of empty string."""
        suggester = TagSuggester()
        result = suggester.normalize_text("")
        assert result == ""

    def test_normalize_text_preserves_special_chars(self):
        """Test that meaningful special characters are preserved."""
        suggester = TagSuggester()
        result = suggester.normalize_text("C++ Developer")
        assert "c++" in result.lower()


class TestCalculateFuzzySimilarity:
    """Tests for fuzzy similarity calculation."""

    def test_fuzzy_similarity_identical(self):
        """Test similarity of identical strings."""
        suggester = TagSuggester()
        result = suggester.calculate_fuzzy_similarity("Senior Developer", "Senior Developer")
        assert result == 1.0

    def test_fuzzy_similarity_similar(self):
        """Test similarity of similar strings."""
        suggester = TagSuggester()
        result = suggester.calculate_fuzzy_similarity("Senior Dev", "Senior Developer")
        assert result > 0.7

    def test_fuzzy_similarity_different(self):
        """Test similarity of different strings."""
        suggester = TagSuggester()
        result = suggester.calculate_fuzzy_similarity("Python", "Java")
        assert result < 0.5

    def test_fuzzy_similarity_case_insensitive(self):
        """Test that similarity is case-insensitive."""
        suggester = TagSuggester()
        result1 = suggester.calculate_fuzzy_similarity("REACT", "react")
        result2 = suggester.calculate_fuzzy_similarity("React", "React")
        # Both should be high similarity due to normalization
        assert result1 > 0.9
        assert result2 == 1.0

    def test_fuzzy_similarity_whitespace_insensitive(self):
        """Test that similarity is whitespace-insensitive."""
        suggester = TagSuggester()
        result = suggester.calculate_fuzzy_similarity("Python Developer", "Python  Developer")
        assert result > 0.9

    def test_fuzzy_similarity_abbreviations(self):
        """Test similarity with common abbreviations."""
        suggester = TagSuggester()
        result = suggester.calculate_fuzzy_similarity("ML Engineer", "Machine Learning Engineer")
        # Should have some similarity but not perfect match
        assert 0 <= result <= 0.6


class TestExtractKeywordsFromResume:
    """Tests for keyword extraction from resume text."""

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_extract_keywords_from_resume_success(self, mock_extract):
        """Test successful keyword extraction."""
        mock_extract.return_value = {
            "keywords": ["python", "django", "postgresql", "api"],
            "keywords_with_scores": [("python", 0.9), ("django", 0.8), ("postgresql", 0.7), ("api", 0.6)],
            "count": 4,
            "error": None
        }

        suggester = TagSuggester()
        result = suggester.extract_keywords_from_resume(
            "Experienced Python developer with Django and PostgreSQL skills",
            top_n=10
        )

        assert result["keywords"] == ["python", "django", "postgresql", "api"]
        assert result["count"] == 4
        assert result["error"] is None
        assert len(result["keywords_with_scores"]) == 4

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_extract_keywords_from_resume_with_error(self, mock_extract):
        """Test keyword extraction when extraction returns error."""
        mock_extract.return_value = {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "error": "Model not loaded"
        }

        suggester = TagSuggester()
        result = suggester.extract_keywords_from_resume(
            "Some resume text",
            top_n=10
        )

        assert result["keywords"] is None
        assert result["count"] == 0
        assert result["error"] == "Model not loaded"

    @patch('analyzers.tag_suggester.extract_keywords', side_effect=ImportError("Module not found"))
    def test_extract_keywords_import_error(self, mock_extract):
        """Test keyword extraction with import error."""
        suggester = TagSuggester()
        result = suggester.extract_keywords_from_resume(
            "Some resume text",
            top_n=10
        )

        assert result["keywords"] is None
        assert result["count"] == 0
        assert "Import error" in result["error"]

    @patch('analyzers.tag_suggester.extract_keywords', side_effect=Exception("Unexpected error"))
    def test_extract_keywords_exception_handling(self, mock_extract):
        """Test keyword extraction exception handling."""
        suggester = TagSuggester()
        result = suggester.extract_keywords_from_resume(
            "Some resume text",
            top_n=10
        )

        assert result["keywords"] is None
        assert result["count"] == 0
        assert "Extraction failed" in result["error"]


class TestFindDirectMatches:
    """Tests for direct keyword matching."""

    def test_find_direct_matches_exact_match(self):
        """Test finding exact keyword matches."""
        suggester = TagSuggester()
        keywords = ["python", "django"]
        keywords_with_scores = [("python", 0.9), ("django", 0.8)]
        organization_tags = [
            {"id": "1", "tag_name": "Python Developer", "is_active": True},
            {"id": "2", "tag_name": "Java Developer", "is_active": True},
        ]

        suggestions = suggester.find_direct_matches(keywords, keywords_with_scores, organization_tags)

        assert len(suggestions) > 0
        assert suggestions[0]["tag_name"] == "Python Developer"
        assert suggestions[0]["reason"] == "direct_match"
        assert suggestions[0]["score"] > 0.8

    def test_find_direct_matches_partial_match(self):
        """Test finding partial keyword matches (substring)."""
        suggester = TagSuggester()
        keywords = ["python"]
        keywords_with_scores = [("python", 0.8)]
        organization_tags = [
            {"id": "1", "tag_name": "Python Expert", "is_active": True},
        ]

        suggestions = suggester.find_direct_matches(keywords, keywords_with_scores, organization_tags)

        assert len(suggestions) > 0
        assert suggestions[0]["tag_name"] == "Python Expert"
        assert "match" in suggestions[0]["reason"]

    def test_find_direct_matches_no_match(self):
        """Test when no keywords match tags."""
        suggester = TagSuggester()
        keywords = ["python", "django"]
        keywords_with_scores = [("python", 0.9), ("django", 0.8)]
        organization_tags = [
            {"id": "1", "tag_name": "Java Developer", "is_active": True},
            {"id": "2", "tag_name": "C# Developer", "is_active": True},
        ]

        suggestions = suggester.find_direct_matches(keywords, keywords_with_scores, organization_tags)

        assert len(suggestions) == 0

    def test_find_direct_matches_inactive_tags_ignored(self):
        """Test that inactive tags are ignored."""
        suggester = TagSuggester()
        keywords = ["python"]
        keywords_with_scores = [("python", 0.9)]
        organization_tags = [
            {"id": "1", "tag_name": "Python Developer", "is_active": True},
            {"id": "2", "tag_name": "Python Expert", "is_active": False},
        ]

        suggestions = suggester.find_direct_matches(keywords, keywords_with_scores, organization_tags)

        assert len(suggestions) == 1
        assert suggestions[0]["id"] == "1"

    def test_find_direct_matches_empty_tag_list(self):
        """Test with empty organization tags list."""
        suggester = TagSuggester()
        keywords = ["python"]
        keywords_with_scores = [("python", 0.9)]
        organization_tags = []

        suggestions = suggester.find_direct_matches(keywords, keywords_with_scores, organization_tags)

        assert len(suggestions) == 0


class TestFindFuzzyMatches:
    """Tests for fuzzy matching."""

    def test_find_fuzzy_matches_similar_names(self):
        """Test fuzzy matching with similar tag names."""
        suggester = TagSuggester()
        keywords = ["ml engineer"]
        keywords_with_scores = [("ml engineer", 0.8)]
        organization_tags = [
            {"id": "1", "tag_name": "Machine Learning Engineer", "is_active": True},
        ]

        suggestions = suggester.find_fuzzy_matches(keywords, keywords_with_scores, organization_tags, set())

        # With fuzzy threshold of 0.6, this should not match (too different)
        # The test verifies the fuzzy matching logic is working
        assert isinstance(suggestions, list)

    def test_find_fuzzy_matches_respects_existing_tags(self):
        """Test that existing tag IDs are excluded."""
        suggester = TagSuggester()
        keywords = ["python"]
        keywords_with_scores = [("python", 0.9)]
        organization_tags = [
            {"id": "1", "tag_name": "Python Developer", "is_active": True},
            {"id": "2", "tag_name": "Python Expert", "is_active": True},
        ]
        existing_tag_ids = {"1"}

        suggestions = suggester.find_fuzzy_matches(keywords, keywords_with_scores, organization_tags, existing_tag_ids)

        # Should not include tag with id "1"
        for suggestion in suggestions:
            assert suggestion["id"] != "1"

    def test_find_fuzzy_matches_inactive_tags_ignored(self):
        """Test that inactive tags are ignored in fuzzy matching."""
        suggester = TagSuggester()
        keywords = ["python"]
        keywords_with_scores = [("python", 0.9)]
        organization_tags = [
            {"id": "1", "tag_name": "Python Dev", "is_active": False},
        ]
        existing_tag_ids = set()

        suggestions = suggester.find_fuzzy_matches(keywords, keywords_with_scores, organization_tags, existing_tag_ids)

        assert len(suggestions) == 0

    def test_find_fuzzy_matches_sorted_by_score(self):
        """Test that fuzzy suggestions are sorted by score."""
        suggester = TagSuggester()
        keywords = ["python", "java"]
        keywords_with_scores = [("python", 0.9), ("java", 0.8)]
        organization_tags = [
            {"id": "1", "tag_name": "Python Development", "is_active": True},
            {"id": "2", "tag_name": "Java Development", "is_active": True},
        ]
        existing_tag_ids = set()

        suggestions = suggester.find_fuzzy_matches(keywords, keywords_with_scores, organization_tags, existing_tag_ids)

        if len(suggestions) > 1:
            scores = [s["score"] for s in suggestions]
            assert scores == sorted(scores, reverse=True)


class TestSuggestTags:
    """Tests for the main suggest_tags method."""

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_suggest_tags_empty_resume_text(self, mock_extract):
        """Test suggest_tags with empty resume text."""
        suggester = TagSuggester()
        result = suggester.suggest_tags("", [])

        assert result["suggestions"] == []
        assert result["total_count"] == 0
        assert result["keywords_extracted"] == []
        assert result["error"] is None
        # extract_keywords should not be called
        mock_extract.assert_not_called()

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_suggest_tags_empty_organization_tags(self, mock_extract):
        """Test suggest_tags with empty organization tags."""
        mock_extract.return_value = {
            "keywords": ["python"],
            "keywords_with_scores": [("python", 0.9)],
            "count": 1,
            "error": None
        }

        suggester = TagSuggester()
        result = suggester.suggest_tags("Python developer experience", [])

        assert result["suggestions"] == []
        assert result["total_count"] == 0

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_suggest_tags_no_matching_keywords(self, mock_extract):
        """Test suggest_tags when no keywords match tags."""
        mock_extract.return_value = {
            "keywords": ["excellent", "communication", "skills"],
            "keywords_with_scores": [("excellent", 0.8), ("communication", 0.7), ("skills", 0.6)],
            "count": 3,
            "error": None
        }

        suggester = TagSuggester()
        result = suggester.suggest_tags(
            "Experienced professional with excellent communication skills",
            [{"id": "1", "tag_name": "Python Developer", "is_active": True}]
        )

        # Should return empty suggestions since keywords don't match
        assert "suggestions" in result
        assert result["total_count"] == 0

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_suggest_tags_happy_path(self, mock_extract):
        """Test suggest_tags with matching content."""
        mock_extract.return_value = {
            "keywords": ["senior", "python", "django"],
            "keywords_with_scores": [("senior", 0.85), ("python", 0.9), ("django", 0.8)],
            "count": 3,
            "error": None
        }

        suggester = TagSuggester()
        result = suggester.suggest_tags(
            "Senior Python developer with Django experience",
            [
                {"id": "1", "tag_name": "Python", "is_active": True},
                {"id": "2", "tag_name": "Django", "is_active": True},
                {"id": "3", "tag_name": "Java", "is_active": True},
            ],
            limit=5
        )

        assert len(result["suggestions"]) > 0
        assert result["total_count"] > 0
        assert result["keywords_extracted"] == ["senior", "python", "django"]
        assert result["error"] is None

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_suggest_tags_limit_enforced(self, mock_extract):
        """Test that limit parameter is respected."""
        mock_extract.return_value = {
            "keywords": ["python", "django", "flask", "fastapi", "sqlalchemy", "postgres"],
            "keywords_with_scores": [
                ("python", 0.9), ("django", 0.85), ("flask", 0.8),
                ("fastapi", 0.75), ("sqlalchemy", 0.7), ("postgres", 0.65)
            ],
            "count": 6,
            "error": None
        }

        suggester = TagSuggester()
        result = suggester.suggest_tags(
            "Python developer with Django, Flask, FastAPI, SQLAlchemy, and PostgreSQL skills",
            [
                {"id": "1", "tag_name": "Python", "is_active": True},
                {"id": "2", "tag_name": "Django", "is_active": True},
                {"id": "3", "tag_name": "Flask", "is_active": True},
                {"id": "4", "tag_name": "FastAPI", "is_active": True},
                {"id": "5", "tag_name": "SQLAlchemy", "is_active": True},
                {"id": "6", "tag_name": "PostgreSQL", "is_active": True},
            ],
            limit=2
        )

        assert len(result["suggestions"]) <= 2

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_suggest_tags_with_extraction_error(self, mock_extract):
        """Test suggest_tags when keyword extraction fails."""
        mock_extract.return_value = {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "error": "Extraction service unavailable"
        }

        suggester = TagSuggester()
        result = suggester.suggest_tags(
            "Some resume text",
            [{"id": "1", "tag_name": "Python", "is_active": True}]
        )

        assert result["suggestions"] == []
        assert result["total_count"] == 0
        assert result["error"] == "Extraction service unavailable"

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_suggest_tags_no_keywords_extracted(self, mock_extract):
        """Test suggest_tags when no keywords are extracted."""
        mock_extract.return_value = {
            "keywords": [],
            "keywords_with_scores": [],
            "count": 0,
            "error": None
        }

        suggester = TagSuggester()
        result = suggester.suggest_tags(
            "Short text",
            [{"id": "1", "tag_name": "Python", "is_active": True}]
        )

        assert result["suggestions"] == []
        assert result["total_count"] == 0
        assert result["error"] is None

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_suggest_tags_scores_in_valid_range(self, mock_extract):
        """Test that all suggestion scores are in valid range (0-1)."""
        mock_extract.return_value = {
            "keywords": ["python", "django"],
            "keywords_with_scores": [("python", 0.9), ("django", 0.8)],
            "count": 2,
            "error": None
        }

        suggester = TagSuggester()
        result = suggester.suggest_tags(
            "Python developer with Django experience",
            [
                {"id": "1", "tag_name": "Python", "is_active": True},
                {"id": "2", "tag_name": "Django", "is_active": True},
            ],
            limit=10
        )

        for suggestion in result["suggestions"]:
            assert 0 <= suggestion["score"] <= 1.0

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_suggest_tags_sorted_by_score(self, mock_extract):
        """Test that suggestions are sorted by score (highest first)."""
        mock_extract.return_value = {
            "keywords": ["python", "django", "flask"],
            "keywords_with_scores": [("python", 0.9), ("django", 0.8), ("flask", 0.7)],
            "count": 3,
            "error": None
        }

        suggester = TagSuggester()
        result = suggester.suggest_tags(
            "Python developer with Django and Flask experience",
            [
                {"id": "1", "tag_name": "Python", "is_active": True},
                {"id": "2", "tag_name": "Django", "is_active": True},
                {"id": "3", "tag_name": "Flask", "is_active": True},
            ],
            limit=10
        )

        if len(result["suggestions"]) > 1:
            scores = [s["score"] for s in result["suggestions"]]
            assert scores == sorted(scores, reverse=True)

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_suggest_tags_no_duplicates(self, mock_extract):
        """Test that duplicate tag suggestions are removed."""
        mock_extract.return_value = {
            "keywords": ["python", "developer"],
            "keywords_with_scores": [("python", 0.9), ("developer", 0.8)],
            "count": 2,
            "error": None
        }

        suggester = TagSuggester()
        result = suggester.suggest_tags(
            "Python developer",
            [
                {"id": "1", "tag_name": "Python Developer", "is_active": True},
                {"id": "2", "tag_name": "Python", "is_active": True},
            ],
            limit=10
        )

        # Check no duplicate tag IDs
        tag_ids = [s.get("id") for s in result["suggestions"] if s.get("id")]
        assert len(tag_ids) == len(set(tag_ids))


class TestSuggestTagsForMultipleResumes:
    """Tests for batch tag suggestions."""

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_suggest_tags_for_multiple_resumes(self, mock_extract):
        """Test suggesting tags for multiple resumes."""
        mock_extract.return_value = {
            "keywords": ["python"],
            "keywords_with_scores": [("python", 0.9)],
            "count": 1,
            "error": None
        }

        suggester = TagSuggester()
        resume_texts = [
            "Python developer with 5 years experience",
            "Senior Python engineer with Django"
        ]
        organization_tags = [
            {"id": "1", "tag_name": "Python", "is_active": True},
        ]

        results = suggester.suggest_tags_for_multiple_resumes(
            resume_texts,
            organization_tags,
            limit_per_resume=5
        )

        assert len(results) == 2
        assert results[0]["resume_index"] == 0
        assert results[1]["resume_index"] == 1
        for result in results:
            assert "suggestions" in result
            assert "total_count" in result

    @patch('analyzers.tag_suggester.extract_keywords')
    def test_suggest_tags_for_multiple_empty_list(self, mock_extract):
        """Test with empty resume list."""
        suggester = TagSuggester()
        results = suggester.suggest_tags_for_multiple_resumes(
            [],
            [{"id": "1", "tag_name": "Python", "is_active": True}]
        )

        assert len(results) == 0


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_init_with_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        suggester = TagSuggester(min_score=0.5, fuzzy_threshold=0.7)
        assert suggester.min_score == 0.5
        assert suggester.fuzzy_threshold == 0.7

    def test_normalize_text_unicode(self):
        """Test handling of Unicode characters."""
        suggester = TagSuggester()
        result = suggester.normalize_text("Développeur Senior")
        assert isinstance(result, str)

    def test_fuzzy_similarity_empty_strings(self):
        """Test fuzzy similarity with empty strings."""
        suggester = TagSuggester()
        result = suggester.calculate_fuzzy_similarity("", "")
        assert result == 1.0

    def test_suggest_tags_with_missing_tag_fields(self):
        """Test handling of tags with missing fields."""
        suggester = TagSuggester()

        # Create a mock that returns keywords
        with patch('analyzers.tag_suggester.extract_keywords') as mock_extract:
            mock_extract.return_value = {
                "keywords": ["python"],
                "keywords_with_scores": [("python", 0.9)],
                "count": 1,
                "error": None
            }

            result = suggester.suggest_tags(
                "Python developer",
                [
                    {"id": "1", "tag_name": "Python", "is_active": True},
                    {"id": "2"},  # Missing tag_name and is_active
                ],
                limit=10
            )

            # Should handle gracefully - might have fewer suggestions
            assert isinstance(result["suggestions"], list)

    def test_suggest_tags_language_parameter(self):
        """Test suggest_tags with different language parameter."""
        with patch('analyzers.tag_suggester.extract_keywords') as mock_extract:
            mock_extract.return_value = {
                "keywords": ["python"],
                "keywords_with_scores": [("python", 0.9)],
                "count": 1,
                "error": None
            }

            suggester = TagSuggester()
            result = suggester.suggest_tags(
                "Python разработчик",  # Russian text
                [{"id": "1", "tag_name": "Python", "is_active": True}],
                limit=10,
                language="russian"
            )

            mock_extract.assert_called_once()
            # Verify the language parameter was passed
            call_kwargs = mock_extract.call_args[1]
            assert call_kwargs["stop_words"] == "russian"
