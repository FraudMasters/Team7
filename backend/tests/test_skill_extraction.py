"""
Tests for keyword extraction module.

Tests cover keyword extraction, top skills extraction,
resume keyword extraction, and error handling.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from analyzers.keyword_extractor import (
    extract_keywords,
    extract_top_skills,
    extract_resume_keywords,
    _get_model,
)


class TestGetModel:
    """Tests for _get_model function."""

    @patch("analyzers.keyword_extractor._kw_model", None)
    @patch("analyzers.keyword_extractor.KeyBERT")
    def test_model_initialization(self, mock_keybert):
        """Test model is initialized on first call."""
        mock_instance = Mock()
        mock_keybert.return_value = mock_instance

        result = _get_model("test-model")

        assert result == mock_instance
        mock_keybert.assert_called_once_with(model="test-model")

    @patch("analyzers.keyword_extractor._kw_model")
    def test_model_cached(self, mock_cached_model):
        """Test model is cached on subsequent calls."""
        mock_cached_model.return_value = Mock()

        result = _get_model()

        assert result is not None
        # Should not try to initialize again

    @patch("analyzers.keyword_extractor.KeyBERT")
    def test_import_error(self, mock_keybert):
        """Test ImportError when KeyBERT not installed."""
        mock_keybert.side_effect = ImportError("No module named 'keybert'")

        with pytest.raises(ImportError, match="KeyBERT is not installed"):
            _get_model()

    @patch("analyzers.keyword_extractor.KeyBERT")
    def test_runtime_error_loading_fails(self, mock_keybert):
        """Test RuntimeError when model loading fails."""
        mock_keybert.side_effect = Exception("Model load failed")

        with pytest.raises(RuntimeError, match="Failed to load KeyBERT model"):
            _get_model()


class TestExtractKeywords:
    """Tests for extract_keywords function."""

    def test_empty_text(self):
        """Test with empty text."""
        result = extract_keywords("")
        assert result["keywords"] is None
        assert result["error"] == "Text must be a non-empty string"

    def test_none_text(self):
        """Test with None text."""
        result = extract_keywords(None)
        assert result["keywords"] is None
        assert result["error"] == "Text must be a non-empty string"

    def test_non_string_text(self):
        """Test with non-string text."""
        result = extract_keywords(123)
        assert result["keywords"] is None
        assert result["error"] == "Text must be a non-empty string"

    def test_text_too_short(self):
        """Test with text shorter than minimum length."""
        result = extract_keywords("short")
        assert result["keywords"] is None
        assert result["error"] == "Text too short for keyword extraction"

    def test_invalid_ngram_range_not_tuple(self):
        """Test with invalid n-gram range (not a tuple)."""
        result = extract_keywords("Valid text length for testing keywords", keyphrase_ngram_range="invalid")
        assert result["keywords"] is None
        assert result["error"] == "keyphrase_ngram_range must be a tuple"

    def test_invalid_ngram_range_wrong_length(self):
        """Test with invalid n-gram range (wrong length)."""
        result = extract_keywords("Valid text", keyphrase_ngram_range=(1, 2, 3))
        assert result["keywords"] is None
        assert result["error"] == "keyphrase_ngram_range must be a tuple"

    def test_invalid_ngram_range_values(self):
        """Test with invalid n-gram range values."""
        result = extract_keywords("Valid text", keyphrase_ngram_range=(2, 1))
        assert result["keywords"] is None
        assert result["error"] == "Invalid keyphrase_ngram_range values"

    def test_invalid_top_n(self):
        """Test with invalid top_n value."""
        result = extract_keywords("Valid text", top_n=0)
        assert result["keywords"] is None
        assert result["error"] == "top_n must be at least 1"

    def test_invalid_min_score(self):
        """Test with invalid min_score value."""
        result = extract_keywords("Valid text", min_score=1.5)
        assert result["keywords"] is None
        assert result["error"] == "min_score must be between 0.0 and 1.0"

    def test_invalid_diversity(self):
        """Test with invalid diversity value."""
        result = extract_keywords("Valid text", diversity=1.5)
        assert result["keywords"] is None
        assert result["error"] == "diversity must be between 0.0 and 1.0"

    @patch("analyzers.keyword_extractor._get_model")
    def test_successful_extraction(self, mock_get_model):
        """Test successful keyword extraction."""
        mock_model = Mock()
        mock_model.extract_keywords.return_value = [("Python", 0.85), ("Django", 0.78)]
        mock_get_model.return_value = mock_model

        text = "Python developer with experience in Django framework and web development"
        result = extract_keywords(text, top_n=5)

        assert result["keywords"] == ["Python", "Django"]
        assert result["keywords_with_scores"] == [("Python", 0.85), ("Django", 0.78)]
        assert result["count"] == 2
        assert result["error"] is None
        mock_model.extract_keywords.assert_called_once()

    @patch("analyzers.keyword_extractor._get_model")
    def test_min_score_filtering(self, mock_get_model):
        """Test min_score filtering works."""
        mock_model = Mock()
        mock_model.extract_keywords.return_value = [
            ("Python", 0.85),
            ("Java", 0.45),
            ("Django", 0.25),
        ]
        mock_get_model.return_value = mock_model

        result = extract_keywords("Valid text", min_score=0.3)

        assert result["keywords"] == ["Python", "Java"]
        assert result["count"] == 2

    @patch("analyzers.keyword_extractor._get_model")
    def test_import_error_handling(self, mock_get_model):
        """Test ImportError is handled gracefully."""
        mock_get_model.side_effect = ImportError("KeyBERT not installed")

        result = extract_keywords("Valid text")

        assert result["keywords"] is None
        assert result["error"] == "Import error: KeyBERT not installed"

    @patch("analyzers.keyword_extractor._get_model")
    def test_extraction_error_handling(self, mock_get_model):
        """Test extraction error is handled gracefully."""
        mock_model = Mock()
        mock_model.extract_keywords.side_effect = Exception("Extraction failed")
        mock_get_model.return_value = mock_model

        result = extract_keywords("Valid text")

        assert result["keywords"] is None
        assert "Extraction failed" in result["error"]

    @patch("analyzers.keyword_extractor._get_model")
    def test_custom_model_name(self, mock_get_model):
        """Test custom model name is used."""
        mock_model = Mock()
        mock_model.extract_keywords.return_value = []
        mock_get_model.return_value = mock_model

        extract_keywords("Valid text", model_name="custom-model")

        mock_get_model.assert_called_with("custom-model")

    @patch("analyzers.keyword_extractor._get_model")
    def test_stop_words_parameter(self, mock_get_model):
        """Test stop_words parameter is passed."""
        mock_model = Mock()
        mock_model.extract_keywords.return_value = []
        mock_get_model.return_value = mock_model

        extract_keywords("Valid text", stop_words="russian")

        mock_model.extract_keywords.assert_called_once()
        call_kwargs = mock_model.extract_keywords.call_args[1]
        assert call_kwargs["stop_words"] == "russian"

    @patch("analyzers.keyword_extractor._get_model")
    def test_use_maxsum_parameter(self, mock_get_model):
        """Test use_maxsum parameter is passed."""
        mock_model = Mock()
        mock_model.extract_keywords.return_value = []
        mock_get_model.return_value = mock_model

        extract_keywords("Valid text", use_maxsum=True)

        mock_model.extract_keywords.assert_called_once()
        call_kwargs = mock_model.extract_keywords.call_args[1]
        assert call_kwargs["use_maxsum"] is True

    @patch("analyzers.keyword_extractor._get_model")
    def test_use_mmr_parameter(self, mock_get_model):
        """Test use_mmr parameter is passed."""
        mock_model = Mock()
        mock_model.extract_keywords.return_value = []
        mock_get_model.return_value = mock_model

        extract_keywords("Valid text", use_mmr=False)

        mock_model.extract_keywords.assert_called_once()
        call_kwargs = mock_model.extract_keywords.call_args[1]
        assert call_kwargs["use_mmr"] is False

    @patch("analyzers.keyword_extractor._get_model")
    def test_diversity_parameter(self, mock_get_model):
        """Test diversity parameter is passed."""
        mock_model = Mock()
        mock_model.extract_keywords.return_value = []
        mock_get_model.return_value = mock_model

        extract_keywords("Valid text", diversity=0.7)

        mock_model.extract_keywords.assert_called_once()
        call_kwargs = mock_model.extract_keywords.call_args[1]
        assert call_kwargs["diversity"] == 0.7


class TestExtractTopSkills:
    """Tests for extract_top_skills function."""

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_successful_skill_extraction(self, mock_extract_keywords):
        """Test successful skill extraction."""
        mock_extract_keywords.return_value = {
            "keywords": ["Python", "Django", "PostgreSQL"],
            "keywords_with_scores": [("Python", 0.85), ("Django", 0.78)],
            "count": 3,
            "error": None,
        }

        result = extract_top_skills("Resume text with skills", top_n=10)

        assert result["skills"] == ["Python", "Django", "PostgreSQL"]
        assert result["skills_with_scores"] == [("Python", 0.85), ("Django", 0.78)]
        assert result["count"] == 3
        assert result["error"] is None

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_english_stop_words(self, mock_extract_keywords):
        """Test English stop words are used."""
        mock_extract_keywords.return_value = {
            "keywords": [],
            "keywords_with_scores": [],
            "count": 0,
            "error": None,
        }

        extract_top_skills("Resume text", language="english")

        mock_extract_keywords.assert_called_once()
        call_kwargs = mock_extract_keywords.call_args[1]
        assert call_kwargs["stop_words"] == "english"

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_russian_stop_words(self, mock_extract_keywords):
        """Test Russian stop words are used."""
        mock_extract_keywords.return_value = {
            "keywords": [],
            "keywords_with_scores": [],
            "count": 0,
            "error": None,
        }

        extract_top_skills("Резюме текст", language="russian")

        mock_extract_keywords.assert_called_once()
        call_kwargs = mock_extract_keywords.call_args[1]
        assert call_kwargs["stop_words"] == "russian"

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_language_aliases(self, mock_extract_keywords):
        """Test language aliases work (en, ru)."""
        mock_extract_keywords.return_value = {
            "keywords": [],
            "keywords_with_scores": [],
            "count": 0,
            "error": None,
        }

        # Test "en" alias
        extract_top_skills("Text", language="en")
        call_kwargs = mock_extract_keywords.call_args[1]
        assert call_kwargs["stop_words"] == "english"

        # Test "ru" alias
        extract_top_skills("Текст", language="ru")
        call_kwargs = mock_extract_keywords.call_args[1]
        assert call_kwargs["stop_words"] == "russian"

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_default_parameters(self, mock_extract_keywords):
        """Test default parameters for skill extraction."""
        mock_extract_keywords.return_value = {
            "keywords": [],
            "keywords_with_scores": [],
            "count": 0,
            "error": None,
        }

        extract_top_skills("Resume text")

        mock_extract_keywords.assert_called_once()
        call_kwargs = mock_extract_keywords.call_args[1]
        assert call_kwargs["keyphrase_ngram_range"] == (1, 3)  # Include multi-word skills
        assert call_kwargs["top_n"] == 10
        assert call_kwargs["min_score"] == 0.3
        assert call_kwargs["use_mmr"] is True
        assert call_kwargs["diversity"] == 0.5

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_custom_top_n(self, mock_extract_keywords):
        """Test custom top_n parameter."""
        mock_extract_keywords.return_value = {
            "keywords": [],
            "keywords_with_scores": [],
            "count": 0,
            "error": None,
        }

        extract_top_skills("Resume text", top_n=15)

        mock_extract_keywords.assert_called_once()
        call_kwargs = mock_extract_keywords.call_args[1]
        assert call_kwargs["top_n"] == 15

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_custom_min_score(self, mock_extract_keywords):
        """Test custom min_score parameter."""
        mock_extract_keywords.return_value = {
            "keywords": [],
            "keywords_with_scores": [],
            "count": 0,
            "error": None,
        }

        extract_top_skills("Resume text", min_score=0.5)

        mock_extract_keywords.assert_called_once()
        call_kwargs = mock_extract_keywords.call_args[1]
        assert call_kwargs["min_score"] == 0.5

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_error_propagation(self, mock_extract_keywords):
        """Test errors from extract_keywords are propagated."""
        mock_extract_keywords.return_value = {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "error": "Text too short",
        }

        result = extract_top_skills("Short")

        assert result["error"] == "Text too short"
        assert result["skills"] is None


class TestExtractResumeKeywords:
    """Tests for extract_resume_keywords function."""

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_successful_extraction(self, mock_extract_keywords):
        """Test successful resume keyword extraction."""
        # Mock single word extraction
        mock_extract_keywords.side_effect = [
            # First call for single words
            {
                "keywords": ["Python", "Java", "Django"],
                "keywords_with_scores": [("Python", 0.85), ("Java", 0.78), ("Django", 0.72)],
                "count": 3,
                "error": None,
            },
            # Second call for phrases
            {
                "keywords": ["Machine Learning", "REST API"],
                "keywords_with_scores": [("Machine Learning", 0.80), ("REST API", 0.75)],
                "count": 2,
                "error": None,
            },
        ]

        result = extract_resume_keywords("Resume text with various skills and technologies")

        assert result["single_words"] == [("Python", 0.85), ("Java", 0.78), ("Django", 0.72)]
        assert result["keyphrases"] == [("Machine Learning", 0.80), ("REST API", 0.75)]
        assert result["all_keywords"] == ["Python", "Java", "Django", "Machine Learning", "REST API"]
        assert result["error"] is None

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_single_word_extraction_error(self, mock_extract_keywords):
        """Test error when single word extraction fails."""
        mock_extract_keywords.return_value = {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "error": "Extraction failed",
        }

        result = extract_resume_keywords("Resume text")

        assert result["error"] == "Extraction failed"
        assert result["single_words"] is None
        assert result["keyphrases"] is None
        assert result["all_keywords"] is None

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_phrase_extraction_error_continues(self, mock_extract_keywords):
        """Test that phrase extraction error doesn't fail entire operation."""
        mock_extract_keywords.side_effect = [
            # First call succeeds (single words)
            {
                "keywords": ["Python", "Java"],
                "keywords_with_scores": [("Python", 0.85), ("Java", 0.78)],
                "count": 2,
                "error": None,
            },
            # Second call fails (phrases)
            {
                "keywords": None,
                "keywords_with_scores": None,
                "count": 0,
                "error": "Phrase extraction failed",
            },
        ]

        result = extract_resume_keywords("Resume text")

        # Should still have single words
        assert result["single_words"] == [("Python", 0.85), ("Java", 0.78)]
        assert result["keyphrases"] == []
        assert result["all_keywords"] == ["Python", "Java"]
        assert result["error"] is None  # Overall operation succeeds

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_deduplication(self, mock_extract_keywords):
        """Test that duplicate keywords are removed."""
        mock_extract_keywords.side_effect = [
            {
                "keywords": ["Python", "Django"],
                "keywords_with_scores": [("Python", 0.85), ("Django", 0.78)],
                "count": 2,
                "error": None,
            },
            {
                "keywords": ["python", "Machine Learning"],  # "python" is duplicate (case)
                "keywords_with_scores": [("python", 0.70), ("Machine Learning", 0.75)],
                "count": 2,
                "error": None,
            },
        ]

        result = extract_resume_keywords("Resume text")

        # Should deduplicate "python" and "Python"
        assert result["all_keywords"] == ["Python", "Django", "Machine Learning"]
        assert len(result["all_keywords"]) == 3

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_include_keyphrases_false(self, mock_extract_keywords):
        """Test disabling keyphrase extraction."""
        mock_extract_keywords.return_value = {
            "keywords": ["Python", "Java"],
            "keywords_with_scores": [("Python", 0.85), ("Java", 0.78)],
            "count": 2,
            "error": None,
        }

        result = extract_resume_keywords("Resume text", include_keyphrases=False)

        # Should only call extract_keywords once
        assert mock_extract_keywords.call_count == 1
        assert result["keyphrases"] == []
        assert result["all_keywords"] == ["Python", "Java"]

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_language_parameter(self, mock_extract_keywords):
        """Test language parameter is passed."""
        mock_extract_keywords.side_effect = [
            {"keywords": [], "keywords_with_scores": [], "count": 0, "error": None},
            {"keywords": [], "keywords_with_scores": [], "count": 0, "error": None},
        ]

        extract_resume_keywords("Resume text", language="russian")

        # Both calls should use russian stop words
        assert mock_extract_keywords.call_count == 2
        for call in mock_extract_keywords.call_args_list:
            call_kwargs = call[1]
            assert call_kwargs["stop_words"] == "russian"

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_default_parameters(self, mock_extract_keywords):
        """Test default parameters for resume extraction."""
        mock_extract_keywords.side_effect = [
            {"keywords": [], "keywords_with_scores": [], "count": 0, "error": None},
            {"keywords": [], "keywords_with_scores": [], "count": 0, "error": None},
        ]

        extract_resume_keywords("Resume text")

        # First call (single words)
        first_call_kwargs = mock_extract_keywords.call_args_list[0][1]
        assert first_call_kwargs["keyphrase_ngram_range"] == (1, 1)
        assert first_call_kwargs["top_n"] == 15
        assert first_call_kwargs["min_score"] == 0.25

        # Second call (phrases)
        second_call_kwargs = mock_extract_keywords.call_args_list[1][1]
        assert second_call_kwargs["keyphrase_ngram_range"] == (2, 3)
        assert second_call_kwargs["top_n"] == 10
        assert second_call_kwargs["min_score"] == 0.3

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_exception_handling(self, mock_extract_keywords):
        """Test exception is handled gracefully."""
        mock_extract_keywords.side_effect = Exception("Unexpected error")

        result = extract_resume_keywords("Resume text")

        assert result["error"] == "Extraction failed: Unexpected error"
        assert result["single_words"] is None
        assert result["keyphrases"] is None
        assert result["all_keywords"] is None


class TestIntegration:
    """Integration tests for keyword extraction workflow."""

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_complete_resume_analysis(self, mock_extract_keywords):
        """Test complete resume keyword extraction."""
        mock_extract_keywords.side_effect = [
            # Single words
            {
                "keywords": ["Python", "Java", "Django", "PostgreSQL"],
                "keywords_with_scores": [
                    ("Python", 0.90),
                    ("Java", 0.85),
                    ("Django", 0.80),
                    ("PostgreSQL", 0.75),
                ],
                "count": 4,
                "error": None,
            },
            # Phrases
            {
                "keywords": ["Machine Learning", "REST API", "Microservices"],
                "keywords_with_scores": [
                    ("Machine Learning", 0.82),
                    ("REST API", 0.78),
                    ("Microservices", 0.70),
                ],
                "count": 3,
                "error": None,
            },
        ]

        result = extract_resume_keywords(
            "Python developer with experience in Django, Java, PostgreSQL, "
            "machine learning, REST APIs, and microservices architecture"
        )

        assert result["error"] is None
        assert len(result["single_words"]) == 4
        assert len(result["keyphrases"]) == 3
        assert len(result["all_keywords"]) == 7
        assert "Python" in result["all_keywords"]
        assert "Machine Learning" in result["all_keywords"]

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_top_skills_from_resume(self, mock_extract_keywords):
        """Test extracting top skills from resume."""
        mock_extract_keywords.return_value = {
            "keywords": ["Python", "Django", "Flask", "PostgreSQL", "Redis"],
            "keywords_with_scores": [
                ("Python", 0.90),
                ("Django", 0.82),
                ("Flask", 0.78),
                ("PostgreSQL", 0.75),
                ("Redis", 0.70),
            ],
            "count": 5,
            "error": None,
        }

        result = extract_top_skills("Resume with various technical skills", top_n=5)

        assert result["skills"] == ["Python", "Django", "Flask", "PostgreSQL", "Redis"]
        assert result["count"] == 5
        assert result["error"] is None

    @patch("analyzers.keyword_extractor.extract_keywords")
    def test_empty_results_handling(self, mock_extract_keywords):
        """Test handling of empty extraction results."""
        mock_extract_keywords.return_value = {
            "keywords": [],
            "keywords_with_scores": [],
            "count": 0,
            "error": None,
        }

        result = extract_keywords("Valid text but no keywords found")

        assert result["keywords"] == []  # Empty list, not None
        assert result["count"] == 0
        assert result["error"] is None
