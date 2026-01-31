"""
Tests for error detector module.

Tests cover error detection for missing contact info, length issues,
portfolio requirements, and missing sections.
"""
import pytest
from analyzers.error_detector import (
    detect_resume_errors,
    _check_resume_length,
    _check_contact_info,
    _check_portfolio_requirement,
    _check_required_sections,
    get_error_summary,
    format_errors_for_display,
    MAX_RESUME_LENGTH_CHARS,
    MIN_RESUME_LENGTH_CHARS,
    ENTRY_LEVEL_EXPERIENCE_MONTHS,
)


class TestCheckResumeLength:
    """Tests for _check_resume_length function."""

    def test_resume_within_limits(self):
        """Test resume with acceptable length."""
        text = "x" * 3000  # Within limits
        errors = _check_resume_length(text)
        assert len(errors) == 0

    def test_resume_too_long(self):
        """Test resume that exceeds maximum length."""
        text = "x" * (MAX_RESUME_LENGTH_CHARS + 1000)
        errors = _check_resume_length(text)
        assert len(errors) == 1
        assert errors[0]["type"] == "resume_too_long"
        assert errors[0]["severity"] == "warning"
        assert errors[0]["category"] == "length"
        assert "current_length" in errors[0]
        assert errors[0]["current_length"] > MAX_RESUME_LENGTH_CHARS
        assert "suggestions" in errors[0]

    def test_resume_too_short(self):
        """Test resume that is too short."""
        text = "x" * (MIN_RESUME_LENGTH_CHARS - 100)
        errors = _check_resume_length(text)
        assert len(errors) == 1
        assert errors[0]["type"] == "resume_too_short"
        assert errors[0]["severity"] == "warning"
        assert errors[0]["category"] == "length"
        assert "suggestions" in errors[0]

    def test_resume_exactly_at_limits(self):
        """Test resume exactly at minimum and maximum limits."""
        # Exactly at minimum
        text_min = "x" * MIN_RESUME_LENGTH_CHARS
        errors = _check_resume_length(text_min)
        assert len(errors) == 0

        # Exactly at maximum
        text_max = "x" * MAX_RESUME_LENGTH_CHARS
        errors = _check_resume_length(text_max)
        assert len(errors) == 0

    def test_resume_custom_limits(self):
        """Test with custom min/max limits."""
        text = "x" * 1000
        errors = _check_resume_length(text, max_length=500, min_length=1500)
        assert len(errors) == 2
        # Should have both too long and too short errors
        error_types = {e["type"] for e in errors}
        assert error_types == {"resume_too_long", "resume_too_short"}

    def test_resume_empty_text(self):
        """Test with empty text."""
        text = ""
        errors = _check_resume_length(text)
        assert len(errors) == 1
        assert errors[0]["type"] == "resume_too_short"


class TestCheckContactInfo:
    """Tests for _check_contact_info function."""

    def test_all_contact_info_present_in_data(self):
        """Test with all contact info in structured data."""
        text = "Some resume text"
        data = {
            "contact": {
                "email": "john@example.com",
                "phone": "+1-555-0123-4567",
                "linked_in": "https://linkedin.com/in/johndoe"
            }
        }
        errors = _check_contact_info(text, data)
        assert len(errors) == 0

    def test_email_missing_critical(self):
        """Test missing email generates critical error."""
        text = "Some resume text"
        data = {"contact": {"phone": "+1-555-0123-4567"}}
        errors = _check_contact_info(text, data)
        assert len(errors) >= 1
        email_errors = [e for e in errors if e["type"] == "missing_email"]
        assert len(email_errors) == 1
        assert email_errors[0]["severity"] == "critical"

    def test_email_detected_in_text(self):
        """Test email detected from text when not in data."""
        text = "Contact me at john.doe@example.com for more info"
        errors = _check_contact_info(text, None)
        email_errors = [e for e in errors if e["type"] == "missing_email"]
        assert len(email_errors) == 0

    def test_email_missing_no_data(self):
        """Test missing email when no data provided."""
        text = "Some resume text without email"
        errors = _check_contact_info(text, None)
        email_errors = [e for e in errors if e["type"] == "missing_email"]
        assert len(email_errors) == 1
        assert email_errors[0]["severity"] == "critical"
        assert "suggestions" in email_errors[0]

    def test_phone_missing_warning(self):
        """Test missing phone generates warning."""
        text = "Email: john@example.com"
        errors = _check_contact_info(text, None)
        phone_errors = [e for e in errors if e["type"] == "missing_phone"]
        assert len(phone_errors) == 1
        assert phone_errors[0]["severity"] == "warning"

    def test_phone_detected_in_text(self):
        """Test various phone number formats detected."""
        test_cases = [
            "Phone: 555-123-4567",
            "Call me at (555) 123-4567",
            "Tel: 555.123.4567",
            "Contact: +1-555-123-4567"
        ]
        for text in test_cases:
            errors = _check_contact_info(text, None)
            phone_errors = [e for e in errors if e["type"] == "missing_phone"]
            assert len(phone_errors) == 0, f"Failed to detect phone in: {text}"

    def test_linkedin_missing_info(self):
        """Test missing LinkedIn generates info level error."""
        text = "Email: john@example.com"
        errors = _check_contact_info(text, None)
        linkedin_errors = [e for e in errors if e["type"] == "missing_linkedin"]
        assert len(linkedin_errors) == 1
        assert linkedin_errors[0]["severity"] == "info"

    def test_linkedin_detected_in_text(self):
        """Test LinkedIn URL detected from text."""
        text = "Find me at https://linkedin.com/in/johndoe"
        errors = _check_contact_info(text, None)
        linkedin_errors = [e for e in errors if e["type"] == "missing_linkedin"]
        assert len(linkedin_errors) == 0

    def test_no_contact_info_at_all(self):
        """Test resume with no contact information."""
        text = "John Doe\nSoftware Developer\nSkills: Python, Java"
        errors = _check_contact_info(text, None)
        assert len(errors) == 3  # email, phone, linkedin all missing
        severities = {e["severity"] for e in errors}
        assert "critical" in severities
        assert "warning" in severities
        assert "info" in severities

    def test_email_regex_patterns(self):
        """Test various email formats are detected."""
        test_cases = [
            "john@example.com",
            "john.doe@example.com",
            "john_doe+test@example.co.uk",
            "JOHN@example.com"  # Case insensitive
        ]
        for email in test_cases:
            text = f"Contact: {email}"
            errors = _check_contact_info(text, None)
            email_errors = [e for e in errors if e["type"] == "missing_email"]
            assert len(email_errors) == 0, f"Failed to detect email: {email}"


class TestCheckPortfolioRequirement:
    """Tests for _check_portfolio_requirement function."""

    def test_experienced_candidate_no_portfolio(self):
        """Test experienced candidate doesn't need portfolio."""
        text = "Experienced developer"
        data = {"total_experience_months": 60}  # 5 years
        errors = _check_portfolio_requirement(text, data)
        assert len(errors) == 0

    def test_entry_level_no_portfolio_error(self):
        """Test entry-level candidate without portfolio generates warning."""
        text = "Junior developer"
        data = {"total_experience_months": 6}  # Less than 1 year
        errors = _check_portfolio_requirement(text, data)
        assert len(errors) == 1
        assert errors[0]["type"] == "missing_portfolio"
        assert errors[0]["severity"] == "warning"
        assert "suggestions" in errors[0]

    def test_entry_level_with_portfolio(self):
        """Test entry-level candidate with portfolio."""
        text = "Junior developer with portfolio"
        data = {
            "total_experience_months": 6,
            "portfolio": ["https://github.com/johndoe", "https://johndoe.dev"]
        }
        errors = _check_portfolio_requirement(text, data)
        assert len(errors) == 0

    def test_portfolio_in_text(self):
        """Test portfolio links detected from text."""
        text = "Check my work at github.com/johndoe or my portfolio site"
        data = {"total_experience_months": 6}
        errors = _check_portfolio_requirement(text, data)
        assert len(errors) == 0

    def test_portfolio_keywords_in_text(self):
        """Test portfolio keywords detected from text."""
        keywords = [
            ("Projects section included", "projects"),
            ("See my demo at example.com", "demo"),
            ("Portfolio available upon request", "portfolio"),
            ("Samples of my work", "samples")
        ]
        for text, keyword in keywords:
            data = {"total_experience_months": 6}
            errors = _check_portfolio_requirement(text, data)
            assert len(errors) == 0, f"Failed to detect keyword: {keyword}"

    def test_entry_level_boundary(self):
        """Test entry level threshold boundary."""
        # Just below threshold
        data_below = {"total_experience_months": ENTRY_LEVEL_EXPERIENCE_MONTHS - 1}
        errors_below = _check_portfolio_requirement("text", data_below)
        assert len(errors_below) == 1

        # Exactly at threshold
        data_at = {"total_experience_months": ENTRY_LEVEL_EXPERIENCE_MONTHS}
        errors_at = _check_portfolio_requirement("text", data_at)
        assert len(errors_at) == 0

        # Just above threshold
        data_above = {"total_experience_months": ENTRY_LEVEL_EXPERIENCE_MONTHS + 1}
        errors_above = _check_portfolio_requirement("text", data_above)
        assert len(errors_above) == 0

    def test_calculate_experience_from_array(self):
        """Test experience calculated from experience array."""
        text = "Junior developer"
        data = {
            "experience": [
                {
                    "start": "2023-01-01",
                    "end": "2023-06-01",
                    "description": "Junior position"
                }
            ]
        }
        errors = _check_portfolio_requirement(text, data)
        # Should detect entry level and suggest portfolio
        assert len(errors) == 1
        assert errors[0]["type"] == "missing_portfolio"

    def test_github_gitlab_urls(self):
        """Test GitHub and GitLab URLs detected as portfolio."""
        test_cases = [
            "https://github.com/username",
            "https://gitlab.com/username",
            "github.com/username",
            "gitlab.com/username"
        ]
        for url in test_cases:
            text = f"My work: {url}"
            data = {"total_experience_months": 6}
            errors = _check_portfolio_requirement(text, data)
            assert len(errors) == 0, f"Failed to detect portfolio URL: {url}"

    def test_portfolio_platforms(self):
        """Test various portfolio platforms detected."""
        platforms = [
            "behance.net/username",
            "dribbble.com/username"
        ]
        for platform in platforms:
            text = f"My design work at {platform}"
            data = {"total_experience_months": 6}
            errors = _check_portfolio_requirement(text, data)
            assert len(errors) == 0


class TestCheckRequiredSections:
    """Tests for _check_required_sections function."""

    def test_all_sections_present_in_data(self):
        """Test all sections present in structured data."""
        text = "Some text"
        data = {
            "skills": ["Python", "Java"],
            "experience": [{"position": "Developer"}],
            "education": [{"degree": "BS"}]
        }
        errors = _check_required_sections(text, data)
        assert len(errors) == 0

    def test_missing_skills_critical(self):
        """Test missing skills section is critical."""
        text = "Experience section\n\nWorked as developer"
        data = {
            "experience": [{"position": "Developer"}],
            "education": [{"degree": "BS"}]
        }
        errors = _check_required_sections(text, data)
        skills_errors = [e for e in errors if e["type"] == "missing_skills_section"]
        assert len(skills_errors) == 1
        assert skills_errors[0]["severity"] == "critical"

    def test_missing_experience_critical(self):
        """Test missing experience section is critical."""
        text = "Skills: Python, Java"
        data = {
            "skills": ["Python", "Java"],
            "education": [{"degree": "BS"}]
        }
        errors = _check_required_sections(text, data)
        exp_errors = [e for e in errors if e["type"] == "missing_experience_section"]
        assert len(exp_errors) == 1
        assert exp_errors[0]["severity"] == "critical"

    def test_missing_education_warning(self):
        """Test missing education section is warning."""
        text = "Skills: Python\n\nExperience: Developer"
        data = {
            "skills": ["Python"],
            "experience": [{"position": "Developer"}]
        }
        errors = _check_required_sections(text, data)
        edu_errors = [e for e in errors if e["type"] == "missing_education_section"]
        assert len(edu_errors) == 1
        assert edu_errors[0]["severity"] == "warning"

    def test_detect_skills_in_text(self):
        """Test skills section detected from text."""
        test_cases = [
            "Skills: Python, Java, SQL",
            "Technical Skills:\n- Python\n- Java",
            "Competencies: Programming, Analysis",
            "Technologies: React, Node.js"
        ]
        for text in test_cases:
            errors = _check_required_sections(text, None)
            skills_errors = [e for e in errors if e["type"] == "missing_skills_section"]
            assert len(skills_errors) == 0, f"Failed to detect skills in: {text}"

    def test_detect_experience_in_text(self):
        """Test experience section detected from text."""
        test_cases = [
            "Experience:\nWorked at company",
            "Work Experience:\nDeveloper at XYZ",
            "Employment History:\nVarious positions",
            "Professional Experience:\nSenior role"
        ]
        for text in test_cases:
            errors = _check_required_sections(text, None)
            exp_errors = [e for e in errors if e["type"] == "missing_experience_section"]
            assert len(exp_errors) == 0, f"Failed to detect experience in: {text}"

    def test_detect_education_in_text(self):
        """Test education section detected from text."""
        test_cases = [
            "Education:\nBS Computer Science",
            "Academic Background:\nUniversity degree",
            "Qualifications:\nMasters degree",
            "Degree:\nPhD in Physics"
        ]
        for text in test_cases:
            errors = _check_required_sections(text, None)
            edu_errors = [e for e in errors if e["type"] == "missing_education_section"]
            assert len(edu_errors) == 0, f"Failed to detect education in: {text}"

    def test_all_sections_missing(self):
        """Test all sections missing generates 3 errors."""
        text = "John Doe\nSome random text"
        errors = _check_required_sections(text, None)
        assert len(errors) == 3
        error_types = {e["type"] for e in errors}
        expected_types = {
            "missing_skills_section",
            "missing_experience_section",
            "missing_education_section"
        }
        assert error_types == expected_types

    def test_empty_experience_array(self):
        """Test empty experience array treated as missing."""
        text = "Some text"
        data = {
            "skills": ["Python"],
            "experience": [],
            "education": [{"degree": "BS"}]
        }
        errors = _check_required_sections(text, data)
        exp_errors = [e for e in errors if e["type"] == "missing_experience_section"]
        assert len(exp_errors) == 1


class TestDetectResumeErrors:
    """Tests for main detect_resume_errors function."""

    def test_valid_resume_no_errors(self):
        """Test valid resume with no errors."""
        text = "x" * 3000 + "\n\n"
        text += "Email: john@example.com\n"
        text += "Phone: 555-123-4567\n"
        text += "Skills: Python, Java\n"
        text += "Experience: Developer at XYZ\n"
        text += "Education: BS CS\n"
        text += "Portfolio: github.com/john\n"

        data = {
            "contact": {"email": "john@example.com", "phone": "555-123-4567"},
            "total_experience_months": 60,
            "skills": ["Python"],
            "experience": [{"position": "Developer"}],
            "education": [{"degree": "BS"}],
            "portfolio": ["github.com/john"]
        }

        result = detect_resume_errors(text, data)
        assert result["total_errors"] == 0
        assert result["critical_count"] == 0
        assert result["warning_count"] == 0
        assert result["error"] is None

    def test_multiple_errors_detected(self):
        """Test multiple errors are detected."""
        text = "Short"  # Too short, no contact, no sections
        result = detect_resume_errors(text)
        assert result["total_errors"] > 0
        assert result["critical_count"] > 0

    def test_empty_text_raises_error(self):
        """Test empty text raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            detect_resume_errors("")

    def test_non_string_text_raises_error(self):
        """Test non-string text raises TypeError."""
        with pytest.raises(TypeError, match="must be a string"):
            detect_resume_errors(123)

    def test_invalid_resume_data_raises_error(self):
        """Test invalid resume_data raises TypeError."""
        with pytest.raises(TypeError, match="must be a dictionary"):
            detect_resume_errors("text", resume_data="invalid")

    def test_disable_checks(self):
        """Test disabling individual checks."""
        text = "Short text without contact"
        result = detect_resume_errors(
            text,
            check_contact=False,
            check_length=False,
            check_portfolio=False,
            check_sections=False
        )
        assert result["total_errors"] == 0

    def test_severity_counts(self):
        """Test severity counts are accurate."""
        text = "x" * (MAX_RESUME_LENGTH_CHARS + 1000)  # Too long
        result = detect_resume_errors(text)
        # Should have at least one warning for length
        assert result["warning_count"] > 0
        assert result["critical_count"] >= 0
        assert result["info_count"] >= 0
        assert result["total_errors"] == sum([
            result["critical_count"],
            result["warning_count"],
            result["info_count"]
        ])

    def test_return_structure(self):
        """Test result has correct structure."""
        text = "Some text"
        result = detect_resume_errors(text)
        expected_keys = {
            "errors", "total_errors", "critical_count",
            "warning_count", "info_count", "error"
        }
        assert set(result.keys()) == expected_keys
        assert isinstance(result["errors"], list)
        assert isinstance(result["total_errors"], int)
        assert isinstance(result["critical_count"], int)
        assert isinstance(result["warning_count"], int)
        assert isinstance(result["info_count"], int)

    def test_error_handling_exception(self):
        """Test exception handling in detect_resume_errors."""
        # This should not raise, but return error in result
        # We can't easily test this without mocking, but we can verify
        # the structure handles errors gracefully
        text = "Valid text"
        result = detect_resume_errors(text)
        # Should have error field even if no errors detected
        assert "error" in result


class TestGetErrorSummary:
    """Tests for get_error_summary function."""

    def test_empty_errors(self):
        """Test summary with empty error list."""
        summary = get_error_summary([])
        assert summary["total"] == 0
        assert summary["by_category"] == {}
        assert summary["by_severity"]["critical"] == []
        assert summary["by_severity"]["warning"] == []
        assert summary["by_severity"]["info"] == []

    def test_group_by_category(self):
        """Test errors grouped by category."""
        errors = [
            {"type": "missing_email", "severity": "critical", "category": "contact"},
            {"type": "missing_phone", "severity": "warning", "category": "contact"},
            {"type": "resume_too_long", "severity": "warning", "category": "length"}
        ]
        summary = get_error_summary(errors)
        assert summary["by_category"]["contact"] == ["missing_email", "missing_phone"]
        assert summary["by_category"]["length"] == ["resume_too_long"]

    def test_group_by_severity(self):
        """Test errors grouped by severity."""
        errors = [
            {"type": "error1", "severity": "critical", "category": "cat1"},
            {"type": "error2", "severity": "critical", "category": "cat2"},
            {"type": "error3", "severity": "warning", "category": "cat1"}
        ]
        summary = get_error_summary(errors)
        assert summary["by_severity"]["critical"] == ["error1", "error2"]
        assert summary["by_severity"]["warning"] == ["error3"]
        assert summary["by_severity"]["info"] == []

    def test_total_count(self):
        """Test total count is accurate."""
        errors = [
            {"type": "error1", "severity": "critical", "category": "cat1"},
            {"type": "error2", "severity": "warning", "category": "cat2"}
        ]
        summary = get_error_summary(errors)
        assert summary["total"] == 2


class TestFormatErrorsForDisplay:
    """Tests for format_errors_for_display function."""

    def test_no_errors_message(self):
        """Test message when no errors."""
        formatted = format_errors_for_display([])
        assert "✓ No errors detected" in formatted
        assert "RESUME ERROR REPORT" in formatted

    def test_with_critical_errors(self):
        """Test formatting critical errors."""
        errors = [
            {
                "type": "missing_email",
                "severity": "critical",
                "message": "Email is missing",
                "suggestions": ["Add email"]
            }
        ]
        formatted = format_errors_for_display(errors)
        assert "CRITICAL ISSUES" in formatted
        assert "Email is missing" in formatted
        assert "Add email" in formatted

    def test_with_warnings(self):
        """Test formatting warnings."""
        errors = [
            {
                "type": "resume_too_long",
                "severity": "warning",
                "message": "Resume too long",
                "suggestions": ["Shorten it"]
            }
        ]
        formatted = format_errors_for_display(errors)
        assert "WARNINGS" in formatted
        assert "Resume too long" in formatted

    def test_with_info(self):
        """Test formatting info-level issues."""
        errors = [
            {
                "type": "missing_linkedin",
                "severity": "info",
                "message": "LinkedIn missing",
                "suggestions": ["Add LinkedIn"]
            }
        ]
        formatted = format_errors_for_display(errors)
        assert "INFO" in formatted
        assert "LinkedIn missing" in formatted

    def test_mixed_severities(self):
        """Test formatting mixed severity errors."""
        errors = [
            {"type": "critical", "severity": "critical", "message": "Critical error"},
            {"type": "warning", "severity": "warning", "message": "Warning"},
            {"type": "info", "severity": "info", "message": "Info"}
        ]
        formatted = format_errors_for_display(errors)
        assert "CRITICAL ISSUES" in formatted
        assert "WARNINGS" in formatted
        assert "INFO" in formatted
        assert "Critical error" in formatted
        assert "Warning" in formatted
        assert "Info" in formatted

    def test_without_suggestions(self):
        """Test formatting without suggestions."""
        errors = [
            {
                "type": "test",
                "severity": "warning",
                "message": "Test error",
                "suggestions": ["Suggestion 1", "Suggestion 2"]
            }
        ]
        formatted = format_errors_for_display(errors, include_suggestions=False)
        assert "Test error" in formatted
        assert "Suggestion 1" not in formatted

    def test_total_count_display(self):
        """Test total count shown at end."""
        errors = [
            {"type": "e1", "severity": "critical", "message": "Error 1"},
            {"type": "e2", "severity": "warning", "message": "Error 2"}
        ]
        formatted = format_errors_for_display(errors)
        assert "TOTAL: 2 issue(s)" in formatted

    def test_formatting_structure(self):
        """Test overall formatting structure."""
        errors = [
            {"type": "test", "severity": "warning", "message": "Test"}
        ]
        formatted = format_errors_for_display(errors)
        lines = formatted.split("\n")
        assert lines[0] == "=" * 80
        assert "RESUME ERROR REPORT" in formatted
        assert lines[-1] == "=" * 80


class TestIntegration:
    """Integration tests for complete error detection workflow."""

    def test_complete_resume_analysis(self):
        """Test analyzing a complete resume."""
        text = """
        John Doe
        Email: john.doe@example.com
        Phone: (555) 123-4567
        LinkedIn: linkedin.com/in/johndoe

        Skills:
        - Python
        - JavaScript
        - React

        Experience:
        Software Developer at Tech Corp (2020 - Present)
        - Developed web applications
        - Led team of 3 developers

        Junior Developer at StartupXYZ (2018 - 2020)
        - Built MVP product

        Education:
        BS Computer Science, University of Technology (2018)

        Projects:
        - E-commerce platform (github.com/johndoe/ecommerce)
        - Task manager app
        """

        data = {
            "contact": {
                "email": "john.doe@example.com",
                "phone": "(555) 123-4567",
                "linked_in": "linkedin.com/in/johndoe"
            },
            "skills": ["Python", "JavaScript", "React"],
            "experience": [
                {
                    "position": "Software Developer",
                    "company": "Tech Corp",
                    "start": "2020-01-01",
                    "end": None
                },
                {
                    "position": "Junior Developer",
                    "company": "StartupXYZ",
                    "start": "2018-01-01",
                    "end": "2020-01-01"
                }
            ],
            "education": [{"degree": "BS", "year": 2018}],
            "portfolio": ["github.com/johndoe"],
            "total_experience_months": 60
        }

        result = detect_resume_errors(text, data)
        assert result["total_errors"] == 0

    def test_problematic_resume(self):
        """Test analyzing a resume with multiple issues."""
        text = "Short resume"  # Too short, no contact, no sections

        result = detect_resume_errors(text)
        assert result["total_errors"] > 0

        # Should detect multiple issues
        error_types = {e["type"] for e in result["errors"]}
        assert "missing_email" in error_types
        assert "resume_too_short" in error_types
        assert "missing_skills_section" in error_types

    def test_entry_level_resume_with_portfolio(self):
        """Test entry-level resume with portfolio passes."""
        text = """
        Jane Smith
        Email: jane@example.com
        GitHub: github.com/janesmith

        Skills: Python, HTML, CSS
        Education: High School Diploma (2023)

        Projects:
        - Personal website
        - Python scripts for automation
        """

        data = {
            "contact": {"email": "jane@example.com"},
            "total_experience_months": 6,  # Entry level
            "portfolio": ["github.com/janesmith"]
        }

        result = detect_resume_errors(text, data)
        # Should not have portfolio error
        portfolio_errors = [e for e in result["errors"]
                           if e["type"] == "missing_portfolio"]
        assert len(portfolio_errors) == 0

    def test_display_format(self):
        """Test complete workflow with display formatting."""
        text = "Resume text with some issues"

        result = detect_resume_errors(text)
        summary = get_error_summary(result["errors"])
        formatted = format_errors_for_display(result["errors"])

        assert summary["total"] == result["total_errors"]
        assert len(formatted) > 0
        assert "RESUME ERROR REPORT" in formatted
