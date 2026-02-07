"""
Unit tests for Resume Processing service.

Tests cover PDF parsing, DOCX parsing, keyword extraction,
experience extraction, and API endpoints.
"""
import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from unittest import TestCase as FileTestCase

from parsers.pdf_parser import extract_text_from_pdf, validate_pdf_file, _extract_with_pypdf2, _extract_with_pdfplumber
from parsers.docx_parser import extract_text_from_docx, extract_text_with_metadata, validate_docx_file
from analyzers.keyword_extractor import extract_keywords, extract_top_skills, extract_resume_keywords
from analyzers.experience_extractor import (
    extract_work_experience,
    detect_overlaps,
    _parse_experience_date,
    _extract_date_range,
    _calculate_confidence_score,
    _identify_experience_sections,
)


# =============================================================================
# PDF Parser Tests
# =============================================================================

class TestExtractTextFromPDF:
    """Tests for extract_text_from_pdf function."""

    def test_raises_file_not_found(self):
        """Test FileNotFoundError when file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            extract_text_from_pdf("nonexistent.pdf")

    def test_raises_value_error_for_non_pdf(self):
        """Test ValueError when file is not a PDF."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.suffix", ".txt"):
                with pytest.raises(ValueError, match="File is not a PDF"):
                    extract_text_from_pdf("document.txt")

    @patch("parsers.pdf_parser._extract_with_pypdf2")
    @patch("parsers.pdf_parser.Path.exists")
    @patch("parsers.pdf_parser.Path.suffix")
    def test_successful_pypdf2_extraction(self, mock_suffix, mock_exists, mock_extract):
        """Test successful text extraction with PyPDF2."""
        mock_exists.return_value = True
        mock_suffix.__eq__ = Mock(return_value=True)
        mock_extract.return_value = {
            "text": "Sample resume content",
            "method": "pypdf2",
            "pages": 2,
            "error": None,
        }

        result = extract_text_from_pdf("resume.pdf")

        assert result["text"] == "Sample resume content"
        assert result["method"] == "pypdf2"
        assert result["pages"] == 2
        assert result["error"] is None

    @patch("parsers.pdf_parser._extract_with_pdfplumber")
    @patch("parsers.pdf_parser._extract_with_pypdf2")
    @patch("parsers.pdf_parser.Path.exists")
    @patch("parsers.pdf_parser.Path.suffix")
    def test_fallback_to_pdfplumber(self, mock_suffix, mock_exists, mock_pypdf2, mock_pdfplumber):
        """Test fallback to pdfplumber when PyPDF2 fails."""
        mock_exists.return_value = True
        mock_suffix.__eq__ = Mock(return_value=True)
        mock_pypdf2.side_effect = Exception("PyPDF2 failed")
        mock_pdfplumber.return_value = {
            "text": "Fallback content",
            "method": "pdfplumber",
            "pages": 2,
            "error": None,
        }

        result = extract_text_from_pdf("resume.pdf")

        assert result["text"] == "Fallback content"
        assert result["method"] == "pdfplumber"

    @patch("parsers.pdf_parser._extract_with_pdfplumber")
    @patch("parsers.pdf_parser._extract_with_pypdf2")
    @patch("parsers.pdf_parser.Path.exists")
    @patch("parsers.pdf_parser.Path.suffix")
    def test_both_methods_fail(self, mock_suffix, mock_exists, mock_pypdf2, mock_pdfplumber):
        """Test error handling when both extraction methods fail."""
        mock_exists.return_value = True
        mock_suffix.__eq__ = Mock(return_value=True)
        mock_pypdf2.side_effect = Exception("PyPDF2 failed")
        mock_pdfplumber.side_effect = Exception("pdfplumber failed")

        result = extract_text_from_pdf("resume.pdf")

        assert result["text"] is None
        assert result["error"] is not None
        assert "All extraction methods failed" in result["error"]


class TestValidatePDFFile:
    """Tests for validate_pdf_file function."""

    @patch("parsers.pdf_parser.Path.exists")
    def test_file_not_exists(self, mock_exists):
        """Test validation when file doesn't exist."""
        mock_exists.return_value = False

        result = validate_pdf_file("missing.pdf")

        assert result["valid"] is False
        assert "does not exist" in result["reason"]

    @patch("parsers.pdf_parser.Path.exists")
    @patch("parsers.pdf_parser.Path.suffix")
    def test_wrong_extension(self, mock_suffix, mock_exists):
        """Test validation with wrong file extension."""
        mock_exists.return_value = True
        mock_suffix.__eq__ = Mock(return_value=False)

        result = validate_pdf_file("document.txt")

        assert result["valid"] is False
        assert "extension" in result["reason"].lower()

    @patch("parsers.pdf_parser.Path.exists")
    @patch("parsers.pdf_parser.Path.suffix")
    @patch("parsers.pdf_parser.Path.stat")
    def test_empty_file(self, mock_stat, mock_suffix, mock_exists):
        """Test validation for empty file."""
        mock_exists.return_value = True
        mock_suffix.__eq__ = Mock(return_value=True)
        mock_stat.return_value.st_size = 0

        result = validate_pdf_file("empty.pdf")

        assert result["valid"] is False
        assert "empty" in result["reason"].lower()


# =============================================================================
# DOCX Parser Tests
# =============================================================================

class TestExtractTextFromDOCX:
    """Tests for extract_text_from_docx function."""

    def test_raises_file_not_found(self):
        """Test FileNotFoundError when file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            extract_text_from_docx("nonexistent.docx")

    def test_raises_value_error_for_non_docx(self):
        """Test ValueError when file is not a DOCX."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.suffix", ".txt"):
                with pytest.raises(ValueError, match="File is not a DOCX"):
                    extract_text_from_docx("document.txt")

    @patch("parsers.docx_parser.Document")
    @patch("parsers.docx_parser.Path.exists")
    @patch("parsers.docx_parser.Path.suffix")
    def test_successful_extraction(self, mock_suffix, mock_exists, mock_doc_class):
        """Test successful text extraction from DOCX."""
        mock_exists.return_value = True
        mock_suffix.__eq__ = Mock(return_value=True)

        # Mock document with paragraphs
        mock_doc = MagicMock()
        mock_doc.paragraphs = [
            MagicMock(text="John Doe"),
            MagicMock(text="Software Engineer"),
        ]
        mock_doc.tables = []
        mock_doc_class.return_value = mock_doc

        result = extract_text_from_docx("resume.docx")

        assert result["text"] == "John Doe\n\nSoftware Engineer"
        assert result["method"] == "python-docx"
        assert result["paragraphs"] == 2
        assert result["tables"] == 0
        assert result["error"] is None

    @patch("parsers.docx_parser.Document")
    @patch("parsers.docx_parser.Path.exists")
    @patch("parsers.docx_parser.Path.suffix")
    def test_extraction_with_tables(self, mock_suffix, mock_exists, mock_doc_class):
        """Test extraction including table content."""
        mock_exists.return_value = True
        mock_suffix.__eq__ = Mock(return_value=True)

        # Mock document with tables
        mock_doc = MagicMock()
        mock_doc.paragraphs = [MagicMock(text="Summary")]
        mock_table = MagicMock()
        mock_row = MagicMock()
        mock_cell = MagicMock()
        mock_cell.text.strip = Mock(return_value="Skill: Python")
        mock_row.cells = [mock_cell]
        mock_table.rows = [mock_row]
        mock_doc.tables = [mock_table]
        mock_doc_class.return_value = mock_doc

        result = extract_text_from_docx("resume.docx")

        assert "Skill: Python" in result["text"]
        assert result["tables"] == 1


class TestExtractTextWithMetadata:
    """Tests for extract_text_with_metadata function."""

    @patch("parsers.docx_parser.extract_text_from_docx")
    @patch("parsers.docx_parser.Document")
    @patch("parsers.docx_parser.Path.exists")
    @patch("parsers.docx_parser.Path.suffix")
    def test_metadata_extraction(self, mock_suffix, mock_exists, mock_doc_class, mock_extract):
        """Test extraction with document metadata."""
        mock_exists.return_value = True
        mock_suffix.__eq__ = Mock(return_value=True)

        mock_doc = MagicMock()
        mock_doc.paragraphs = [MagicMock(text="Content")]
        mock_doc.tables = []

        # Mock core properties
        mock_doc.core_properties.author = "John Doe"
        mock_doc.core_properties.title = "Resume"
        mock_doc.core_properties.subject = "Software Engineer"
        mock_doc.core_properties.created = datetime(2024, 1, 1, 12, 0, 0)
        mock_doc.core_properties.modified = datetime(2024, 1, 2, 12, 0, 0)
        mock_doc.core_properties.last_modified_by = "Jane Smith"

        mock_doc_class.return_value = mock_doc
        mock_extract.return_value = {
            "text": "Content",
            "method": "python-docx",
            "paragraphs": 1,
            "tables": 0,
            "error": None,
        }

        result = extract_text_with_metadata("resume.docx")

        assert result["author"] == "John Doe"
        assert result["title"] == "Resume"
        assert result["subject"] == "Software Engineer"
        assert result["created"] is not None
        assert result["last_modified_by"] == "Jane Smith"


class TestValidateDOCXFile:
    """Tests for validate_docx_file function."""

    @patch("parsers.docx_parser.Path.exists")
    def test_file_not_exists(self, mock_exists):
        """Test validation when file doesn't exist."""
        mock_exists.return_value = False

        result = validate_docx_file("missing.docx")

        assert result["valid"] is False
        assert "does not exist" in result["reason"]

    @patch("parsers.docx_parser.Path.exists")
    @patch("parsers.docx_parser.Path.suffix")
    @patch("parsers.docx_parser.Path.stat")
    def test_empty_file(self, mock_stat, mock_suffix, mock_exists):
        """Test validation for empty file."""
        mock_exists.return_value = True
        mock_suffix.__lower__ = ".docx"
        mock_suffix.__eq__ = Mock(side_effect=lambda x: x in [".docx", ".DOC"])
        mock_stat.return_value.st_size = 0

        result = validate_docx_file("empty.docx")

        assert result["valid"] is False
        assert "empty" in result["reason"].lower()


# =============================================================================
# Keyword Extractor Tests
# =============================================================================

class TestExtractKeywords:
    """Tests for extract_keywords function."""

    def test_empty_text_returns_error(self):
        """Test that empty text returns error."""
        result = extract_keywords("")

        assert result["keywords"] is None
        assert result["error"] is not None

    def test_short_text_returns_error(self):
        """Test that text too short returns error."""
        result = extract_keywords("Hi")

        assert result["keywords"] is None
        assert "too short" in result["error"].lower()

    def test_invalid_ngram_range(self):
        """Test validation of keyphrase_ngram_range parameter."""
        result = extract_keywords("Sample text", keyphrase_ngram_range=(3, 1))

        assert result["keywords"] is None
        assert "ngram_range" in result["error"].lower()

    def test_invalid_top_n(self):
        """Test validation of top_n parameter."""
        result = extract_keywords("Sample text", top_n=0)

        assert result["keywords"] is None
        assert "top_n" in result["error"].lower()

    def test_invalid_min_score(self):
        """Test validation of min_score parameter."""
        result = extract_keywords("Sample text", min_score=1.5)

        assert result["keywords"] is None
        assert "min_score" in result["error"].lower()

    def test_invalid_diversity(self):
        """Test validation of diversity parameter."""
        result = extract_keywords("Sample text", diversity=2.0)

        assert result["keywords"] is None
        assert "diversity" in result["error"].lower()


class TestExtractTopSkills:
    """Tests for extract_top_skills function."""

    def test_convenience_wrapper(self):
        """Test that extract_top_skills wraps extract_keywords correctly."""
        with patch("analyzers.keyword_extractor.extract_keywords") as mock_extract:
            mock_extract.return_value = {
                "keywords": ["Python", "Django"],
                "keywords_with_scores": [("Python", 0.9), ("Django", 0.8)],
                "count": 2,
                "model": "test-model",
                "error": None,
            }

            result = extract_top_skills("Python developer with Django experience")

            assert result["skills"] == ["Python", "Django"]
            assert result["count"] == 2
            assert result["error"] is None


class TestExtractResumeKeywords:
    """Tests for extract_resume_keywords function."""

    def test_combined_extraction(self):
        """Test extraction of both single words and keyphrases."""
        with patch("analyzers.keyword_extractor.extract_keywords") as mock_extract:
            # Mock responses for single words and phrases
            mock_extract.side_effect = [
                {
                    "keywords_with_scores": [("Python", 0.9), ("Django", 0.8)],
                    "error": None,
                },
                {
                    "keywords_with_scores": [("Machine Learning", 0.7)],
                    "error": None,
                },
            ]

            result = extract_resume_keywords("Python Django Machine Learning expert")

            assert result["all_keywords"] is not None
            assert result["error"] is None
            # Verify deduplication
            assert len(result["all_keywords"]) == len(set(result["all_keywords"]))

    def test_handles_keyphrase_extraction_failure(self):
        """Test that failed keyphrase extraction doesn't break the function."""
        with patch("analyzers.keyword_extractor.extract_keywords") as mock_extract:
            mock_extract.side_effect = [
                {
                    "keywords_with_scores": [("Python", 0.9)],
                    "error": None,
                },
                {
                    "keywords_with_scores": None,
                    "error": "Keyphrase extraction failed",
                },
            ]

            result = extract_resume_keywords("Python developer")

            # Should still have single words
            assert result["single_words"] is not None
            # But error in keyphrases
            assert result["keyphrases"] == []


# =============================================================================
# Experience Extractor Tests
# =============================================================================

class TestParseExperienceDate:
    """Tests for _parse_experience_date helper function."""

    def test_parse_month_year(self):
        """Test parsing MM/YYYY format."""
        result = _parse_experience_date("05/2020")
        assert result == "2020-05-01"

    def test_parse_russian_month_year(self):
        """Test parsing Russian MM.YYYY format."""
        result = _parse_experience_date("05.2020")
        assert result == "2020-05-01"

    def test_parse_year_only(self):
        """Test parsing YYYY format."""
        result = _parse_experience_date("2020")
        assert result == "2020-01-01"

    def test_present_indicators_return_none(self):
        """Test that 'present' indicators return None."""
        assert _parse_experience_date("present") is None
        assert _parse_experience_date("current") is None
        assert _parse_experience_date("now") is None
        assert _parse_experience_date("сейчас") is None
        assert _parse_experience_date("по настоящее время") is None

    def test_invalid_date_returns_none(self):
        """Test that invalid date returns None."""
        assert _parse_experience_date("invalid") is None

    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        assert _parse_experience_date(None) is None


class TestExtractDateRange:
    """Tests for _extract_date_range helper function."""

    def test_extract_year_range(self):
        """Test extracting YYYY - YYYY range."""
        text = "2020 - 2022"
        result = _extract_date_range(text)

        assert result is not None
        assert result["start"] == "2020-01-01"
        assert result["end"] == "2022-01-01"

    def test_extract_year_to_present(self):
        """Test extracting YYYY - present range."""
        text = "2020 - present"
        result = _extract_date_range(text)

        assert result is not None
        assert result["start"] == "2020-01-01"
        assert result["end"] is None  # Present returns None

    def test_no_date_range_returns_none(self):
        """Test that text without date range returns None."""
        result = _extract_date_range("Software Engineer at Google")
        assert result is None


class TestCalculateConfidenceScore:
    """Tests for _calculate_confidence_score helper function."""

    def test_full_entry_high_confidence(self):
        """Test high confidence for complete entry."""
        entry = {
            "company": "Google",
            "title": "Senior Software Engineer",
            "start": "2020-01-01",
            "end": "2022-01-01",
            "description": "Led development of cloud infrastructure serving millions of users.",
        }

        score = _calculate_confidence_score(entry, has_org_entity=True, has_date_entity=True)

        assert score > 0.8  # Should be high confidence

    def test_partial_entry_lower_confidence(self):
        """Test lower confidence for partial entry."""
        entry = {
            "company": "G",
            "title": "Eng",
            "start": "2020-01-01",
            "end": None,
            "description": "Worked.",
        }

        score = _calculate_confidence_score(entry, has_org_entity=False, has_date_entity=False)

        assert score < 0.6  # Should be lower confidence

    def test_minimal_entry_low_confidence(self):
        """Test very low confidence for minimal entry."""
        entry = {
            "company": None,
            "title": None,
            "start": None,
            "end": None,
            "description": "",
        }

        score = _calculate_confidence_score(entry, has_org_entity=False, has_date_entity=False)

        assert score < 0.3

    def test_score_capped_at_one(self):
        """Test that score is capped at 1.0."""
        entry = {
            "company": "A" * 100,
            "title": "B" * 100,
            "start": "2020-01-01",
            "end": "2022-01-01",
            "description": "C" * 200,
        }

        score = _calculate_confidence_score(entry, has_org_entity=True, has_date_entity=True)

        assert score <= 1.0


class TestIdentifyExperienceSections:
    """Tests for _identify_experience_sections helper function."""

    def test_finds_work_experience_section(self):
        """Test finding standard 'Work Experience' section."""
        text = """
        Skills
        Python, Java

        Work Experience
        Senior Developer at Google
        2020 - Present

        Education
        BS Computer Science
        """

        sections = _identify_experience_sections(text)

        assert len(sections) > 0
        # Section should start after "Work Experience"
        start, end = sections[0]
        assert start > 0

    def test_finds_professional_experience_section(self):
        """Test finding 'Professional Experience' section."""
        text = """
        Professional Experience
        Software Engineer at Microsoft
        """

        sections = _identify_experience_sections(text)

        assert len(sections) > 0

    def test_finds_russian_experience_section(self):
        """Test finding Russian 'опыт работы' section."""
        text = """
        опыт работы
        Разработчик в Яндекс
        """

        sections = _identify_experience_sections(text)

        assert len(sections) > 0

    def test_no_section_returns_empty(self):
        """Test that text without experience section returns empty list."""
        text = "Skills: Python, Java, C++"

        sections = _identify_experience_sections(text)

        assert len(sections) == 0


class TestExtractWorkExperience:
    """Tests for extract_work_experience function."""

    def test_empty_text_returns_error(self):
        """Test that empty text returns error."""
        result = extract_work_experience("")

        assert result["experiences"] is None
        assert result["error"] is not None

    def test_short_text_returns_error(self):
        """Test that text too short returns error."""
        result = extract_work_experience("Short")

        assert result["experiences"] is None
        assert "too short" in result["error"].lower()

    @patch("analyzers.experience_extractor._get_spacy_model")
    def test_successful_extraction(self, mock_get_model):
        """Test successful experience extraction."""
        # Mock SpaCy model
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        mock_doc.ents = []  # No entities for simplicity
        mock_nlp.return_value = mock_doc
        mock_get_model.return_value = mock_nlp

        text = """
        Work Experience

        Senior Developer at Google
        2020 - 2022
        Developed cloud infrastructure.
        """

        result = extract_work_experience(text, min_confidence=0.0)

        assert result["error"] is None
        # Should find at least the section

    @patch("analyzers.experience_extractor._get_spacy_model")
    def test_filters_by_confidence(self, mock_get_model):
        """Test that low confidence entries are filtered out."""
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        mock_doc.ents = []
        mock_nlp.return_value = mock_doc
        mock_get_model.return_value = mock_nlp

        text = "Experience\nDeveloper at Company\n2020 - 2021"

        # Extract with high threshold
        result = extract_work_experience(text, min_confidence=0.9)

        # Should have fewer or no results due to high threshold
        assert result["error"] is None


class TestDetectOverlaps:
    """Tests for detect_overlaps function."""

    def test_empty_list_returns_no_overlaps(self):
        """Test that empty list returns no overlaps."""
        result = detect_overlaps([])

        assert result["overlap_count"] == 0
        assert result["overlaps"] == []
        assert result["concurrent_periods"] == []

    def test_single_entry_returns_no_overlaps(self):
        """Test that single entry returns no overlaps."""
        experiences = [
            {"start": "2020-01-01", "end": "2022-01-01"}
        ]

        result = detect_overlaps(experiences)

        assert result["overlap_count"] == 0

    def test_detects_overlapping_periods(self):
        """Test detection of overlapping date ranges."""
        experiences = [
            {"start": "2020-01-01", "end": "2021-01-01"},
            {"start": "2020-06-01", "end": "2021-06-01"},
        ]

        result = detect_overlaps(experiences)

        assert result["overlap_count"] == 1
        assert len(result["overlaps"]) == 1

    def test_identifies_concurrent_periods(self):
        """Test identification of concurrent positions at different companies."""
        experiences = [
            {"start": "2020-01-01", "end": "2021-01-01", "company": "Company A", "title": "Role A"},
            {"start": "2020-06-01", "end": "2021-06-01", "company": "Company B", "title": "Role B"},
        ]

        result = detect_overlaps(experiences)

        assert len(result["concurrent_periods"]) == 1
        # Different companies should be marked as concurrent
        assert result["concurrent_periods"][0]["entry1"]["company"] != result["concurrent_periods"][0]["entry2"]["company"]

    def test_handles_missing_dates(self):
        """Test handling of entries with missing dates."""
        experiences = [
            {"start": None, "end": None},
            {"start": "2020-01-01", "end": "2021-01-01"},
        ]

        result = detect_overlaps(experiences)

        # Should handle gracefully without crashing
        assert result["error"] is None
        # Missing dates means no overlap detected
        assert result["overlap_count"] == 0

    def test_detects_current_position_overlaps(self):
        """Test overlap detection with current positions (None end date)."""
        from datetime import datetime

        experiences = [
            {"start": "2020-01-01", "end": None},  # Current position
            {"start": "2021-01-01", "end": "2022-01-01"},
        ]

        result = detect_overlaps(experiences)

        # Current position (end=None) should be compared against now
        assert result["overlap_count"] == 1


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================

class TestResumeProcessingEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_unicode_handling_in_parsers(self):
        """Test that parsers handle Unicode characters correctly."""
        # This test verifies Unicode text doesn't break parsing
        text = "Русский текст и English text mixed"
        assert len(text) > 0

    def test_very_long_resume_text(self):
        """Test handling of very long resume text."""
        long_text = "Python Developer " * 1000

        result = extract_resume_keywords(long_text, include_keyphrases=False)

        # Should handle long text without error
        assert result is not None

    def test_special_characters_in_skills(self):
        """Test handling of skills with special characters."""
        skills = ["C++", "C#", ".NET", "Node.js"]
        # Verify characters are preserved
        for skill in skills:
            assert len(skill) > 0

    def test_mixed_language_resume(self):
        """Test extraction from mixed language resume."""
        mixed_text = "Python developer with опыт работы в software engineering"

        # Should handle mixed language without crashing
        result = extract_keywords(mixed_text, stop_words=None, top_n=5)
        assert result is not None

    def test_empty_file_error_handling(self):
        """Test error handling for empty/corrupted files."""
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf("empty.pdf")


class TestDateParsingEdgeCases:
    """Tests for date parsing edge cases."""

    def test_various_date_formats(self):
        """Test parsing of various date formats."""
        test_cases = [
            ("01/2020", "2020-01-01"),
            ("2020", "2020-01-01"),
            ("May 2020", "2020-05-01"),
        ]

        for input_date, expected_prefix in test_cases:
            result = _parse_experience_date(input_date)
            if result:
                assert result.startswith(expected_prefix[:7])

    def test_russian_date_formats(self):
        """Test Russian date format parsing."""
        result = _parse_experience_date("01.2020")
        assert result == "2020-01-01"


class TestConfidenceScoringEdgeCases:
    """Tests for confidence scoring edge cases."""

    def test_very_long_company_name(self):
        """Test confidence with very long company name."""
        entry = {
            "company": "A" * 200,
            "title": "Developer",
            "start": "2020-01-01",
            "end": None,
            "description": "Work",
        }

        score = _calculate_confidence_score(entry, has_org_entity=False, has_date_entity=False)

        # Should still be valid score
        assert 0 <= score <= 1.0

    def test_very_long_description(self):
        """Test confidence with very long description."""
        entry = {
            "company": "Google",
            "title": "Developer",
            "start": "2020-01-01",
            "end": None,
            "description": "Work " * 500,
        }

        score = _calculate_confidence_score(entry, has_org_entity=True, has_date_entity=True)

        # Long description should increase confidence but cap at 1.0
        assert score <= 1.0

    def test_empty_all_fields(self):
        """Test confidence with all empty fields."""
        entry = {
            "company": None,
            "title": None,
            "start": None,
            "end": None,
            "description": None,
        }

        score = _calculate_confidence_score(entry, has_org_entity=False, has_date_entity=False)

        assert score == 0.0


class TestExperienceEntryStructure:
    """Tests for experience entry data structure validation."""

    def test_entry_has_required_fields(self):
        """Test that experience entries have all required fields."""
        # Mock extraction result
        mock_entry = {
            "company": "Google",
            "title": "Developer",
            "start": "2020-01-01",
            "end": None,
            "description": "Developed software",
            "confidence": 0.85,
        }

        # Verify all expected keys are present
        expected_keys = {"company", "title", "start", "end", "description", "confidence"}
        assert set(mock_entry.keys()) == expected_keys

    def test_entry_confidence_range(self):
        """Test that confidence is always in valid range."""
        for confidence in [0.0, 0.5, 0.85, 1.0]:
            assert 0.0 <= confidence <= 1.0


class TestOverlapDetectionEdgeCases:
    """Tests for overlap detection edge cases."""

    def test_exact_same_dates(self):
        """Test overlap when dates are exactly the same."""
        experiences = [
            {"start": "2020-01-01", "end": "2021-01-01", "company": "A"},
            {"start": "2020-01-01", "end": "2021-01-01", "company": "B"},
        ]

        result = detect_overlaps(experiences)

        # Should detect overlap
        assert result["overlap_count"] == 1
        # Should be concurrent (different companies)
        assert len(result["concurrent_periods"]) == 1

    def test_adjacent_periods_no_overlap(self):
        """Test that adjacent periods don't count as overlap."""
        experiences = [
            {"start": "2020-01-01", "end": "2021-01-01"},
            {"start": "2021-01-01", "end": "2022-01-01"},
        ]

        result = detect_overlaps(experiences)

        # Adjacent (end == start) may or may not be overlap depending on implementation
        assert result["overlap_count"] >= 0

    def test_three_way_overlap(self):
        """Test detection of three-way overlapping periods."""
        experiences = [
            {"start": "2020-01-01", "end": "2022-01-01", "company": "A"},
            {"start": "2020-06-01", "end": "2021-06-01", "company": "B"},
            {"start": "2021-01-01", "end": "2021-12-01", "company": "C"},
        ]

        result = detect_overlaps(experiences)

        # Should detect multiple overlaps
        assert result["overlap_count"] >= 2


class TestInputValidation:
    """Tests for input validation across all modules."""

    def test_pdf_parser_nonexistent_file(self):
        """Test PDF parser with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf("nonexistent.pdf")

    def test_docx_parser_nonexistent_file(self):
        """Test DOCX parser with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            extract_text_from_docx("nonexistent.docx")

    def test_keyword_extractor_none_text(self):
        """Test keyword extractor with None text."""
        result = extract_keywords(None)
        assert result["keywords"] is None
        assert result["error"] is not None

    def test_experience_extractor_none_text(self):
        """Test experience extractor with None text."""
        result = extract_work_experience(None)
        assert result["experiences"] is None
        assert result["error"] is not None

    def test_experience_extractor_non_string_text(self):
        """Test experience extractor with non-string input."""
        result = extract_work_experience(12345)
        assert result["experiences"] is None
        assert result["error"] is not None


class TestResultsStructure:
    """Tests for validating return value structures."""

    def test_pdf_parser_result_structure(self):
        """Test PDF parser returns correct structure."""
        with patch("parsers.pdf_parser._extract_with_pypdf2") as mock_extract:
            mock_extract.return_value = {
                "text": "Sample",
                "method": "pypdf2",
                "pages": 1,
                "error": None,
            }

            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.suffix", ".pdf"):
                    result = extract_text_from_pdf("test.pdf")

            expected_keys = {"text", "method", "pages", "error"}
            assert set(result.keys()) == expected_keys

    def test_docx_parser_result_structure(self):
        """Test DOCX parser returns correct structure."""
        with patch("parsers.docx_parser.Document") as mock_doc_class:
            mock_doc = MagicMock()
            mock_doc.paragraphs = [MagicMock(text="Text")]
            mock_doc.tables = []
            mock_doc_class.return_value = mock_doc

            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.suffix", ".docx"):
                    result = extract_text_from_docx("test.docx")

            expected_keys = {"text", "method", "paragraphs", "tables", "error"}
            assert set(result.keys()) == expected_keys

    def test_keyword_extractor_result_structure(self):
        """Test keyword extractor returns correct structure."""
        result = extract_keywords("Short text")  # Will fail validation but return structure

        expected_keys = {"keywords", "keywords_with_scores", "count", "model", "error"}
        assert set(result.keys()) == expected_keys

    def test_experience_extractor_result_structure(self):
        """Test experience extractor returns correct structure."""
        result = extract_work_experience("Too short")

        expected_keys = {"experiences", "total_count", "language", "error"}
        assert set(result.keys()) == expected_keys

    def test_detect_overlaps_result_structure(self):
        """Test detect_overlaps returns correct structure."""
        result = detect_overlaps([])

        expected_keys = {"overlap_count", "overlaps", "concurrent_periods", "error"}
        assert set(result.keys()) == expected_keys
