"""
Tests for work experience extraction module.

Tests cover experience section identification, date parsing,
entity extraction, confidence scoring, and overlap detection.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from analyzers.experience_extractor import (
    _get_spacy_model,
    _identify_experience_sections,
    _parse_experience_date,
    _extract_date_range,
    _calculate_confidence_score,
    _extract_experience_entries,
    extract_work_experience,
    _dates_overlap,
    detect_overlaps,
)


class TestGetSpacyModel:
    """Tests for _get_spacy_model function."""

    @patch("analyzers.experience_extractor._nlp_model", None)
    @patch("analyzers.experience_extractor.spacy")
    def test_model_initialization_english(self, mock_spacy):
        """Test English model is initialized on first call."""
        mock_instance = Mock()
        mock_spacy.load.return_value = mock_instance

        result = _get_spacy_model("en")

        assert result == mock_instance
        mock_spacy.load.assert_called_once_with("en_core_web_sm")

    @patch("analyzers.experience_extractor._nlp_model", None)
    @patch("analyzers.experience_extractor.spacy")
    def test_model_initialization_russian(self, mock_spacy):
        """Test Russian model is initialized."""
        mock_instance = Mock()
        mock_spacy.load.return_value = mock_instance

        result = _get_spacy_model("ru")

        assert result == mock_instance
        mock_spacy.load.assert_called_once_with("ru_core_news_sm")

    @patch("analyzers.experience_extractor._nlp_model")
    def test_model_cached(self, mock_cached_model):
        """Test model is cached on subsequent calls."""
        mock_cached_model.return_value = Mock()

        result = _get_spacy_model("en")

        assert result is not None

    @patch("analyzers.experience_extractor._nlp_model", None)
    @patch("analyzers.experience_extractor.spacy")
    def test_import_error(self, mock_spacy):
        """Test ImportError when spaCy not installed."""
        mock_spacy.side_effect = ImportError("No module named 'spacy'")

        with pytest.raises(ImportError, match="SpaCy is not installed"):
            _get_spacy_model()

    @patch("analyzers.experience_extractor._nlp_model", None)
    @patch("analyzers.experience_extractor.spacy")
    def test_model_not_found(self, mock_spacy):
        """Test RuntimeError when model not downloaded."""
        mock_spacy.load.side_effect = OSError("Model not found")

        with pytest.raises(RuntimeError, match="not found"):
            _get_spacy_model()

    @patch("analyzers.experience_extractor._nlp_model", None)
    @patch("analyzers.experience_extractor.spacy")
    def test_language_aliases(self, mock_spacy):
        """Test language aliases work (english, russian)."""
        mock_instance = Mock()
        mock_spacy.load.return_value = mock_instance

        # Test "english" alias
        _get_spacy_model("english")
        mock_spacy.load.assert_called_with("en_core_web_sm")

        # Test "russian" alias
        _get_spacy_model("russian")
        mock_spacy.load.assert_called_with("ru_core_news_sm")


class TestIdentifyExperienceSections:
    """Tests for _identify_experience_sections function."""

    def test_single_english_section(self):
        """Test identifying single English experience section."""
        text = """
        Skills
        Python, Java, SQL

        Work Experience

        Senior Developer at Google
        2020 - Present

        Software Engineer at Microsoft
        2018 - 2020
        """
        sections = _identify_experience_sections(text)

        assert len(sections) == 1
        start, end = sections[0]
        assert "Work Experience" in text[start:end]

    def test_multiple_sections(self):
        """Test identifying multiple experience sections."""
        text = """
        Work Experience

        Job 1

        Experience

        Job 2
        """
        sections = _identify_experience_sections(text)

        assert len(sections) == 2

    def test_russian_section(self):
        """Test identifying Russian experience section."""
        text = """
        Навыки
        Python, Java

        Опыт работы

        Разработчик в Яндекс
        2020 - настоящее время
        """
        sections = _identify_experience_sections(text)

        assert len(sections) == 1

    def test_no_section_found(self):
        """Test when no experience section is found."""
        text = """
        Skills
        Python, Java

        Education
        BS Computer Science
        """
        sections = _identify_experience_sections(text)

        assert len(sections) == 0

    def test_various_section_headers(self):
        """Test various experience section header patterns."""
        patterns = [
            "Employment History",
            "Professional Experience",
            "Work History",
            "Career History",
            "Professional Background",
        ]

        for pattern in patterns:
            text = f"{pattern}\n\nJob at Company"
            sections = _identify_experience_sections(text)
            assert len(sections) == 1


class TestParseExperienceDate:
    """Tests for _parse_experience_date function."""

    def test_mm_yyyy_format(self):
        """Test parsing MM/YYYY format."""
        result = _parse_experience_date("05/2020")
        assert result == "2020-05-01"

    def test_yyyy_mm_format(self):
        """Test parsing YYYY-MM format."""
        result = _parse_experience_date("2020-05")
        assert result == "2020-05-01"

    def test_month_yyyy_format(self):
        """Test parsing Month YYYY format."""
        result = _parse_experience_date("May 2020")
        assert result == "2020-05-01"

    def test_full_month_name_format(self):
        """Test parsing full month name format."""
        result = _parse_experience_date("January 2020")
        assert result == "2020-01-01"

    def test_yyyy_format(self):
        """Test parsing YYYY format."""
        result = _parse_experience_date("2020")
        assert result == "2020-01-01"

    def test_present_indicator(self):
        """Test 'present' returns None for current position."""
        result = _parse_experience_date("present")
        assert result is None

    def test_current_indicator(self):
        """Test 'current' returns None."""
        result = _parse_experience_date("current")
        assert result is None

    def test_russian_present_indicator(self):
        """Test Russian present indicators."""
        for indicator in ["сейчас", "настоящее", "по настоящее время"]:
            result = _parse_experience_date(indicator)
            assert result is None

    def test_none_input(self):
        """Test None input returns None."""
        result = _parse_experience_date(None)
        assert result is None

    def test_empty_string(self):
        """Test empty string returns None."""
        result = _parse_experience_date("")
        assert result is None

    def test_invalid_date_format(self):
        """Test invalid date format returns None."""
        result = _parse_experience_date("invalid-date")
        assert result is None

    def test_non_string_input(self):
        """Test non-string input returns None."""
        result = _parse_experience_date(123)
        assert result is None


class TestExtractDateRange:
    """Tests for _extract_date_range function."""

    def test_mm_yyyy_range(self):
        """Test extracting MM/YYYY - MM/YYYY range."""
        text = "05/2020 - 06/2023"
        result = _extract_date_range(text)

        assert result is not None
        assert result["start"] == "2020-05-01"
        assert result["end"] == "2023-06-01"

    def test_yyyy_range(self):
        """Test extracting YYYY - YYYY range."""
        text = "2020 - 2023"
        result = _extract_date_range(text)

        assert result is not None
        assert result["start"] == "2020-01-01"
        assert result["end"] == "2023-01-01"

    def test_present_range(self):
        """Test extracting date range with present."""
        text = "05/2020 - Present"
        result = _extract_date_range(text)

        assert result is not None
        assert result["start"] == "2020-05-01"
        assert result["end"] is None

    def test_month_year_range(self):
        """Test extracting Month YYYY - Month YYYY range."""
        text = "May 2020 - June 2023"
        result = _extract_date_range(text)

        assert result is not None
        assert result["start"] == "2020-05-01"
        assert result["end"] == "2023-06-01"

    def test_no_date_range(self):
        """Test text without date range returns None."""
        text = "Software Engineer at Google"
        result = _extract_date_range(text)

        assert result is None

    def test_various_separators(self):
        """Test various date range separators."""
        separators = [" - ", " – ", "—", " to "]

        for sep in separators:
            text = f"05/2020{sep}06/2023"
            result = _extract_date_range(text)
            assert result is not None


class TestCalculateConfidenceScore:
    """Tests for _calculate_confidence_score function."""

    def test_complete_entry_high_confidence(self):
        """Test complete entry has high confidence."""
        entry = {
            "company": "Google",
            "title": "Senior Software Engineer",
            "start": "2020-01-01",
            "end": "2023-01-01",
            "description": "Led development of cloud infrastructure and microservices architecture.",
        }
        result = _calculate_confidence_score(entry, has_org_entity=True, has_date_entity=True)

        assert result > 0.8
        assert result <= 1.0

    def test_minimal_entry_low_confidence(self):
        """Test minimal entry has low confidence."""
        entry = {
            "company": "G",
            "title": "Eng",
            "start": None,
            "end": None,
            "description": "",
        }
        result = _calculate_confidence_score(entry, has_org_entity=False, has_date_entity=False)

        assert result < 0.5

    def test_entry_with_dates_only(self):
        """Test entry with only dates."""
        entry = {
            "company": None,
            "title": None,
            "start": "2020-01-01",
            "end": "2023-01-01",
            "description": None,
        }
        result = _calculate_confidence_score(entry, has_org_entity=False, has_date_entity=True)

        assert 0.1 <= result <= 0.25

    def test_ner_boost(self):
        """Test NER confirmation boosts score."""
        entry = {
            "company": "Google",
            "title": "Engineer",
            "start": "2020-01-01",
            "end": None,
            "description": "Worked on search.",
        }

        score_no_ner = _calculate_confidence_score(entry, has_org_entity=False, has_date_entity=False)
        score_with_ner = _calculate_confidence_score(entry, has_org_entity=True, has_date_entity=True)

        assert score_with_ner > score_no_ner

    def test_long_description_boost(self):
        """Test longer description increases score."""
        entry = {
            "company": "Google",
            "title": "Engineer",
            "start": "2020-01-01",
            "end": None,
            "description": "This is a very long description that exceeds fifty characters and provides detailed information about the work performed.",
        }
        result = _calculate_confidence_score(entry, has_org_entity=False, has_date_entity=False)

        assert result > 0.6

    def test_short_company_penalty(self):
        """Test very short company name gives partial credit."""
        entry = {
            "company": "G",
            "title": "Senior Software Engineer",
            "start": "2020-01-01",
            "end": None,
            "description": None,
        }
        result = _calculate_confidence_score(entry, has_org_entity=False, has_date_entity=False)

        # Should get partial points for company (0.15 instead of 0.3)
        assert 0.3 < result < 0.6

    def test_current_position_no_end_date(self):
        """Test current position with no end date."""
        entry = {
            "company": "Google",
            "title": "Engineer",
            "start": "2020-01-01",
            "end": None,
            "description": None,
        }
        result = _calculate_confidence_score(entry, has_org_entity=True, has_date_entity=True)

        # Should not penalize for missing end date (current position)
        assert result > 0.4

    def test_score_capped_at_one(self):
        """Test score is capped at 1.0."""
        entry = {
            "company": "Very Long Company Name With Lots Of Words",
            "title": "Senior Principal Software Engineer and Architect",
            "start": "2020-01-01",
            "end": "2023-01-01",
            "description": "A" * 100,
        }
        result = _calculate_confidence_score(entry, has_org_entity=True, has_date_entity=True)

        assert result == 1.0


class TestExtractWorkExperience:
    """Tests for extract_work_experience function."""

    def test_empty_text(self):
        """Test with empty text."""
        result = extract_work_experience("")

        assert result["experiences"] is None
        assert result["error"] == "Text must be a non-empty string"

    def test_none_text(self):
        """Test with None text."""
        result = extract_work_experience(None)

        assert result["experiences"] is None
        assert result["error"] == "Text must be a non-empty string"

    def test_non_string_text(self):
        """Test with non-string text."""
        result = extract_work_experience(123)

        assert result["experiences"] is None
        assert result["error"] == "Text must be a non-empty string"

    def test_text_too_short(self):
        """Test with text shorter than minimum length."""
        result = extract_work_experience("Short text")

        assert result["experiences"] is None
        assert result["error"] == "Text too short for experience extraction (min 50 chars)"

    @patch("analyzers.experience_extractor._get_spacy_model")
    def test_successful_extraction(self, mock_get_model):
        """Test successful experience extraction."""
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_doc.ents = []

        # Mock entity extraction
        mock_org = Mock()
        mock_org.label_ = "ORG"
        mock_org.text = "Google"

        mock_doc.ents = [mock_org]
        mock_nlp.return_value = mock_doc
        mock_get_model.return_value = mock_nlp

        text = """
        Work Experience

        Senior Software Engineer at Google
        05/2020 - Present

        Led development of scalable systems.
        """
        result = extract_work_experience(text)

        assert result["experiences"] is not None
        assert result["total_count"] >= 0
        assert result["error"] is None

    @patch("analyzers.experience_extractor._get_spacy_model")
    def test_import_error_handling(self, mock_get_model):
        """Test ImportError is handled gracefully."""
        mock_get_model.side_effect = ImportError("spaCy not installed")

        text = "Valid text length for testing experience extraction with more than fifty characters"
        result = extract_work_experience(text)

        assert result["experiences"] is None
        assert "Import error" in result["error"]

    @patch("analyzers.experience_extractor._get_spacy_model")
    def test_extraction_error_handling(self, mock_get_model):
        """Test extraction error is handled gracefully."""
        mock_get_model.side_effect = Exception("Extraction failed")

        text = "Valid text length for testing experience extraction with more than fifty characters"
        result = extract_work_experience(text)

        assert result["experiences"] is None
        assert "Extraction failed" in result["error"]

    @patch("analyzers.experience_extractor._get_spacy_model")
    def test_language_parameter(self, mock_get_model):
        """Test language parameter is passed."""
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_doc.ents = []
        mock_nlp.return_value = mock_doc
        mock_get_model.return_value = mock_nlp

        text = "Work Experience\n\n" + "x" * 100

        extract_work_experience(text, language="ru")

        mock_get_model.assert_called_with("ru")

    @patch("analyzers.experience_extractor._get_spacy_model")
    def test_min_confidence_filtering(self, mock_get_model):
        """Test min_confidence filters results."""
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_doc.ents = []

        # Create low-confidence entities
        mock_doc.ents = []
        mock_nlp.return_value = mock_doc
        mock_get_model.return_value = mock_nlp

        text = """
        Work Experience

        x

        y
        """
        result = extract_work_experience(text, min_confidence=0.8)

        # Should filter out low confidence entries
        assert result["error"] is None

    @patch("analyzers.experience_extractor._get_spacy_model")
    def test_no_experience_section(self, mock_get_model):
        """Test extraction when no explicit experience section."""
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_doc.ents = []
        mock_nlp.return_value = mock_doc
        mock_get_model.return_value = mock_nlp

        text = "Some resume text without explicit work experience section headers. " + "x" * 100

        result = extract_work_experience(text)

        assert result["error"] is None

    @patch("analyzers.experience_extractor._get_spacy_model")
    def test_russian_text(self, mock_get_model):
        """Test extraction from Russian text."""
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_org = Mock()
        mock_org.label_ = "ORG"
        mock_org.text = "Яндекс"
        mock_doc.ents = [mock_org]
        mock_nlp.return_value = mock_doc
        mock_get_model.return_value = mock_nlp

        text = """
        Опыт работы

        Разработчик в Яндекс
        05/2020 - настоящее время

        Разработка сервисов.
        """
        result = extract_work_experience(text, language="ru")

        assert result["error"] is None


class TestDatesOverlap:
    """Tests for _dates_overlap function."""

    def test_overlapping_periods(self):
        """Test overlapping time periods."""
        p1_start = datetime(2020, 1, 1)
        p1_end = datetime(2020, 6, 1)
        p2_start = datetime(2020, 5, 1)
        p2_end = datetime(2020, 12, 1)

        result = _dates_overlap(p1_start, p1_end, p2_start, p2_end)

        assert result is True

    def test_non_overlapping_periods(self):
        """Test non-overlapping time periods."""
        p1_start = datetime(2020, 1, 1)
        p1_end = datetime(2020, 6, 1)
        p2_start = datetime(2021, 1, 1)
        p2_end = datetime(2021, 6, 1)

        result = _dates_overlap(p1_start, p1_end, p2_start, p2_end)

        assert result is False

    def test_adjacent_periods(self):
        """Test adjacent periods (end equals start)."""
        p1_start = datetime(2020, 1, 1)
        p1_end = datetime(2020, 6, 1)
        p2_start = datetime(2020, 6, 1)
        p2_end = datetime(2020, 12, 1)

        result = _dates_overlap(p1_start, p1_end, p2_start, p2_end)

        assert result is True

    def test_period1_current_none_end(self):
        """Test period 1 is current (None end)."""
        p1_start = datetime(2020, 1, 1)
        p1_end = None
        p2_start = datetime(2020, 5, 1)
        p2_end = datetime(2020, 12, 1)

        result = _dates_overlap(p1_start, p1_end, p2_start, p2_end)

        assert result is True

    def test_period2_current_none_end(self):
        """Test period 2 is current (None end)."""
        p1_start = datetime(2020, 1, 1)
        p1_end = datetime(2020, 6, 1)
        p2_start = datetime(2020, 5, 1)
        p2_end = None

        result = _dates_overlap(p1_start, p1_end, p2_start, p2_end)

        assert result is True

    def test_both_current_none_end(self):
        """Test both periods are current."""
        p1_start = datetime(2020, 1, 1)
        p1_end = None
        p2_start = datetime(2021, 1, 1)
        p2_end = None

        result = _dates_overlap(p1_start, p1_end, p2_start, p2_end)

        assert result is True

    def test_contained_period(self):
        """Test one period contained within another."""
        p1_start = datetime(2020, 1, 1)
        p1_end = datetime(2020, 12, 1)
        p2_start = datetime(2020, 6, 1)
        p2_end = datetime(2020, 8, 1)

        result = _dates_overlap(p1_start, p1_end, p2_start, p2_end)

        assert result is True


class TestDetectOverlaps:
    """Tests for detect_overlaps function."""

    def test_empty_experiences_list(self):
        """Test with empty experiences list."""
        result = detect_overlaps([])

        assert result["overlap_count"] == 0
        assert result["overlaps"] == []
        assert result["concurrent_periods"] == []
        assert result["error"] is None

    def test_single_experience(self):
        """Test with single experience entry."""
        experiences = [
            {"start": "2020-01-01", "end": "2021-01-01"}
        ]

        result = detect_overlaps(experiences)

        assert result["overlap_count"] == 0
        assert result["overlaps"] == []

    def test_overlapping_experiences(self):
        """Test detecting overlapping experiences."""
        experiences = [
            {"company": "Google", "title": "Engineer", "start": "2020-01-01", "end": "2021-01-01"},
            {"company": "Microsoft", "title": "Developer", "start": "2020-06-01", "end": "2021-06-01"},
        ]

        result = detect_overlaps(experiences)

        assert result["overlap_count"] == 1
        assert len(result["overlaps"]) == 1
        assert result["overlaps"][0]["entry1"]["company"] == "Google"
        assert result["overlaps"][0]["entry2"]["company"] == "Microsoft"

    def test_concurrent_positions(self):
        """Test detecting concurrent positions at different companies."""
        experiences = [
            {"company": "Google", "title": "Engineer", "start": "2020-01-01", "end": "2021-01-01"},
            {"company": "Microsoft", "title": "Developer", "start": "2020-06-01", "end": "2021-06-01"},
        ]

        result = detect_overlaps(experiences)

        assert len(result["concurrent_periods"]) == 1
        assert result["concurrent_periods"][0]["entry1"]["company"] == "Google"
        assert result["concurrent_periods"][0]["entry2"]["company"] == "Microsoft"

    def test_same_company_no_concurrent(self):
        """Test same company is not marked as concurrent."""
        experiences = [
            {"company": "Google", "title": "Engineer", "start": "2020-01-01", "end": "2021-01-01"},
            {"company": "Google", "title": "Senior Engineer", "start": "2020-06-01", "end": "2021-06-01"},
        ]

        result = detect_overlaps(experiences)

        # Should have overlap but not concurrent (same company)
        assert result["overlap_count"] == 1
        assert len(result["concurrent_periods"]) == 0

    def test_no_overlapping_experiences(self):
        """Test with non-overlapping experiences."""
        experiences = [
            {"company": "Google", "title": "Engineer", "start": "2020-01-01", "end": "2021-01-01"},
            {"company": "Microsoft", "title": "Developer", "start": "2021-06-01", "end": "2022-06-01"},
        ]

        result = detect_overlaps(experiences)

        assert result["overlap_count"] == 0
        assert result["overlaps"] == []

    def test_current_position_overlap(self):
        """Test overlap detection with current positions (None end)."""
        experiences = [
            {"company": "Google", "title": "Engineer", "start": "2020-01-01", "end": None},
            {"company": "Microsoft", "title": "Developer", "start": "2021-01-01", "end": "2022-01-01"},
        ]

        result = detect_overlaps(experiences)

        # Current position (Google) overlaps with Microsoft
        assert result["overlap_count"] == 1

    def test_missing_start_date_skipped(self):
        """Test experiences without start dates are skipped."""
        experiences = [
            {"company": "Google", "title": "Engineer", "start": "2020-01-01", "end": "2021-01-01"},
            {"company": "Microsoft", "title": "Developer", "start": None, "end": "2022-01-01"},
        ]

        result = detect_overlaps(experiences)

        # Second experience should be skipped
        assert result["overlap_count"] == 0

    def test_invalid_date_format_skipped(self):
        """Test experiences with invalid dates are skipped."""
        experiences = [
            {"company": "Google", "title": "Engineer", "start": "2020-01-01", "end": "2021-01-01"},
            {"company": "Microsoft", "title": "Developer", "start": "invalid-date", "end": "2022-01-01"},
        ]

        result = detect_overlaps(experiences)

        # Second experience should be skipped
        assert result["overlap_count"] == 0

    def test_multiple_overlaps(self):
        """Test detecting multiple overlapping pairs."""
        experiences = [
            {"company": "A", "title": "Job1", "start": "2020-01-01", "end": "2021-01-01"},
            {"company": "B", "title": "Job2", "start": "2020-06-01", "end": "2021-06-01"},
            {"company": "C", "title": "Job3", "start": "2020-09-01", "end": "2021-09-01"},
        ]

        result = detect_overlaps(experiences)

        # Should have 3 overlapping pairs: (A,B), (A,C), (B,C)
        assert result["overlap_count"] == 3

    def test_overlap_info_structure(self):
        """Test overlap information has correct structure."""
        experiences = [
            {"company": "Google", "title": "Engineer", "start": "2020-01-01", "end": "2021-01-01"},
            {"company": "Microsoft", "title": "Developer", "start": "2020-06-01", "end": "2021-06-01"},
        ]

        result = detect_overlaps(experiences)

        overlap = result["overlaps"][0]

        # Check structure
        assert "entry1" in overlap
        assert "entry2" in overlap
        assert "overlap_start" in overlap
        assert "overlap_end" in overlap

        # Check entry structure
        assert "index" in overlap["entry1"]
        assert "company" in overlap["entry1"]
        assert "title" in overlap["entry1"]
        assert "start" in overlap["entry1"]
        assert "end" in overlap["entry1"]

    def test_exception_handling(self):
        """Test exception is handled gracefully."""
        experiences = [
            {"start": "2020-01-01", "end": "2021-01-01"},
        ]

        # This should not raise an exception
        result = detect_overlaps(experiences)

        assert result["error"] is None


class TestIntegration:
    """Integration tests for experience extraction workflow."""

    @patch("analyzers.experience_extractor._get_spacy_model")
    def test_complete_resume_extraction(self, mock_get_model):
        """Test complete experience extraction from resume."""
        mock_nlp = Mock()

        # Mock Google entity
        mock_doc1 = Mock()
        mock_org1 = Mock()
        mock_org1.label_ = "ORG"
        mock_org1.text = "Google"
        mock_date1 = Mock()
        mock_date1.label_ = "DATE"
        mock_doc1.ents = [mock_org1, mock_date1]

        # Mock Microsoft entity
        mock_doc2 = Mock()
        mock_org2 = Mock()
        mock_org2.label_ = "ORG"
        mock_org2.text = "Microsoft"
        mock_date2 = Mock()
        mock_date2.label_ = "DATE"
        mock_doc2.ents = [mock_org2, mock_date2]

        call_count = [0]

        def side_effect(text):
            if "Google" in text:
                return mock_doc1
            return mock_doc2

        mock_nlp.side_effect = side_effect
        mock_get_model.return_value = mock_nlp

        text = """
        Work Experience

        Senior Software Engineer at Google
        05/2020 - Present

        Led development of cloud infrastructure and microservices.
        Designed scalable architecture serving millions of users.

        Software Developer at Microsoft
        06/2018 - 04/2020

        Built web applications using React and Node.js.
        Implemented RESTful APIs and database optimizations.
        """

        result = extract_work_experience(text)

        assert result["error"] is None
        assert result["experiences"] is not None
        assert result["total_count"] >= 0

    @patch("analyzers.experience_extractor._get_spacy_model")
    def test_overlap_detection_after_extraction(self, mock_get_model):
        """Test overlap detection with extracted experiences."""
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_doc.ents = []
        mock_nlp.return_value = mock_doc
        mock_get_model.return_value = mock_nlp

        # Simulate extracted experiences
        experiences = [
            {"company": "Google", "title": "Engineer", "start": "2020-01-01", "end": "2021-01-01"},
            {"company": "Microsoft", "title": "Developer", "start": "2020-06-01", "end": "2021-06-01"},
        ]

        result = detect_overlaps(experiences)

        assert result["overlap_count"] == 1
        assert len(result["concurrent_periods"]) == 1
