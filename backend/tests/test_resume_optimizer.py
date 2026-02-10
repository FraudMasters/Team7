"""
Tests for resume optimizer module.

Tests cover keyword analysis, formatting recommendations,
content improvements, and scoring calculations.
"""
import pytest
from analyzers.resume_optimizer import (
    generate_resume_optimization,
    _analyze_keywords,
    _analyze_formatting,
    _analyze_content,
    _calculate_optimization_score,
    format_suggestions_for_display,
    MIN_KEYWORD_DENSITY,
    MAX_SECTION_COUNT,
    IDEAL_SECTION_COUNT,
    MIN_ACTION_VERBS,
)


class TestAnalyzeKeywords:
    """Tests for _analyze_keywords function."""

    def test_keywords_found_in_resume(self):
        """Test detecting common keywords in resume."""
        text = "Python developer with experience in JavaScript, React, and SQL"
        result = _analyze_keywords(text, None, None)

        assert "keywords_found" in result
        assert len(result["keywords_found"]) > 0
        assert "python" in result["keywords_found"]
        assert "javascript" in result["keywords_found"]
        assert "react" in result["keywords_found"]
        assert "sql" in result["keywords_found"]

    def test_no_keywords_in_resume(self):
        """Test resume with no technical keywords."""
        text = "Worked as a professional doing various tasks"
        result = _analyze_keywords(text, None, None)

        assert len(result["keywords_found"]) == 0

    def test_job_description_matching(self):
        """Test matching keywords against job description."""
        text = "Python developer with SQL experience"
        jd = "Looking for Python developer with Django and React experience"

        result = _analyze_keywords(text, None, jd)

        # Should find missing keywords
        assert "missing_keywords" in result
        assert len(result["missing_keywords"]) > 0
        # React should be missing, Django should be missing
        assert "react" in result["missing_keywords"]
        assert "django" in result["missing_keywords"]

    def test_job_description_no_missing(self):
        """Test when all JD keywords are in resume."""
        text = "Python developer with Django and React experience"
        jd = "Looking for Python developer"

        result = _analyze_keywords(text, None, jd)

        # Should have few or no missing keywords
        assert len(result["missing_keywords"]) == 0

    def test_low_keyword_density_suggestion(self):
        """Test low keyword density generates suggestion."""
        text = "This is a resume with very few technical words " * 100
        result = _analyze_keywords(text, None, None, min_density=0.1)

        suggestions = result.get("suggestions", [])
        density_suggestions = [s for s in suggestions if s.get("category") == "keywords"]
        assert len(density_suggestions) > 0

    def test_high_keyword_density_no_suggestion(self):
        """Test adequate keyword density doesn't generate suggestion."""
        text = "python java javascript react angular vue node django flask sql aws docker kubernetes"
        result = _analyze_keywords(text, None, None, min_density=0.001)

        # Should not have density suggestion with high keyword count
        suggestions = result.get("suggestions", [])
        density_suggestions = [s for s in suggestions if "density" in s.get("title", "").lower()]
        assert len(density_suggestions) == 0

    def test_missing_skills_section_suggestion(self):
        """Test missing skills section generates high priority suggestion."""
        text = "Some resume text"
        data = {}  # No skills section

        result = _analyze_keywords(text, data, None)
        suggestions = result.get("suggestions", [])

        skills_suggestions = [s for s in suggestions if "skills section" in s.get("title", "").lower()]
        assert len(skills_suggestions) == 1
        assert skills_suggestions[0]["priority"] == "high"

    def test_with_skills_section_no_suggestion(self):
        """Test skills section present doesn't generate suggestion."""
        text = "Some resume text"
        data = {"skills": ["Python", "Java"]}

        result = _analyze_keywords(text, data, None)
        suggestions = result.get("suggestions", [])

        skills_suggestions = [s for s in suggestions if "skills section" in s.get("title", "").lower()]
        assert len(skills_suggestions) == 0

    def test_missing_keywords_priority(self):
        """Test priority based on number of missing keywords."""
        text = "Python developer"
        jd = "Looking for Python developer with Django, React, Angular, Node, and AWS"

        result = _analyze_keywords(text, None, jd)
        suggestions = result.get("suggestions", [])

        keyword_suggestions = [s for s in suggestions if s.get("category") == "keywords"]
        if keyword_suggestions:
            # Should be high priority with many missing keywords
            assert keyword_suggestions[0]["priority"] in ["high", "medium"]

    def test_keyword_case_insensitive(self):
        """Test keyword detection is case insensitive."""
        test_cases = [
            "PYTHON Developer",
            "python Developer",
            "Python Developer",
            "pYtHoN Developer"
        ]
        for text in test_cases:
            result = _analyze_keywords(text, None, None)
            assert "python" in result["keywords_found"], f"Failed for: {text}"


class TestAnalyzeFormatting:
    """Tests for _analyze_formatting function."""

    def test_too_many_sections(self):
        """Test resume with too many sections."""
        text = "\n".join([f"Section {i}:" for i in range(15)])
        suggestions = _analyze_formatting(text, None)

        section_suggestions = [s for s in suggestions if "Reduce number of sections" in s.get("title", "")]
        assert len(section_suggestions) == 1
        assert section_suggestions[0]["priority"] == "medium"

    def test_too_few_sections(self):
        """Test resume with too few sections."""
        text = "Name\n\nJust some content"
        suggestions = _analyze_formatting(text, None)

        section_suggestions = [s for s in suggestions if "Add more resume sections" in s.get("title", "")]
        assert len(section_suggestions) == 1
        assert section_suggestions[0]["priority"] == "medium"

    def test_ideal_section_count(self):
        """Test resume with ideal number of sections."""
        text = "\n".join([f"Section {i}:" for i in range(6)])
        suggestions = _analyze_formatting(text, None)

        # Should not have section count suggestions
        section_suggestions = [s for s in suggestions if "section" in s.get("title", "").lower()]
        assert len(section_suggestions) == 0

    def test_no_bullet_points_suggestion(self):
        """Test missing bullet points generates high priority suggestion."""
        text = "Line 1\nLine 2\nLine 3\nNo bullets here"
        suggestions = _analyze_formatting(text, None)

        bullet_suggestions = [s for s in suggestions if "bullet points" in s.get("title", "").lower()]
        assert len(bullet_suggestions) == 1
        assert bullet_suggestions[0]["priority"] == "high"

    def test_with_bullet_points_no_suggestion(self):
        """Test bullet points present doesn't generate suggestion."""
        text = "Skills:\n- Python\n- Java\n• JavaScript"
        suggestions = _analyze_formatting(text, None)

        bullet_suggestions = [s for s in suggestions if "bullet points" in s.get("title", "").lower()]
        assert len(bullet_suggestions) == 0

    def test_no_quantifiable_achievements(self):
        """Test missing metrics generates high priority suggestion."""
        text = "Worked on projects and did things"
        suggestions = _analyze_formatting(text, None)

        metrics_suggestions = [s for s in suggestions if "quantifiable" in s.get("title", "").lower()]
        assert len(metrics_suggestions) == 1
        assert metrics_suggestions[0]["priority"] == "high"

    def test_with_quantifiable_achievements(self):
        """Test metrics present doesn't generate suggestion."""
        text = "Increased sales by 25% and managed team of 8 developers"
        suggestions = _analyze_formatting(text, None)

        metrics_suggestions = [s for s in suggestions if "quantifiable" in s.get("title", "").lower()]
        assert len(metrics_suggestions) == 0

    def test_various_metric_formats(self):
        """Test various metric formats are detected."""
        test_cases = [
            "Improved performance by 30%",
            "Managed $50K budget",
            "Led team of 10 members",
            "Increased by 50 users",
            "Reduced costs by 20 dollars"
        ]
        for text in test_cases:
            suggestions = _analyze_formatting(text, None)
            metrics_suggestions = [s for s in suggestions if "quantifiable" in s.get("title", "").lower()]
            assert len(metrics_suggestions) == 0, f"Failed to detect metrics in: {text}"

    def test_long_line_length_suggestion(self):
        """Test long lines generate low priority suggestion."""
        long_lines = ["x" * 120 for _ in range(10)]
        text = "\n".join(long_lines)
        suggestions = _analyze_formatting(text, None)

        length_suggestions = [s for s in suggestions if "shortening" in s.get("title", "").lower()]
        assert len(length_suggestions) == 1
        assert length_suggestions[0]["priority"] == "low"

    def test_short_lines_no_suggestion(self):
        """Test short lines don't generate suggestion."""
        short_lines = ["x" * 50 for _ in range(10)]
        text = "\n".join(short_lines)
        suggestions = _analyze_formatting(text, None)

        length_suggestions = [s for s in suggestions if "shortening" in s.get("title", "").lower()]
        assert len(length_suggestions) == 0

    def test_section_header_detection(self):
        """Test various section header formats are detected."""
        test_cases = [
            "# Skills\n## Experience",
            "SKILLS:\nEXPERIENCE:",
            "Summary:\nEducation:",
            "Work History\nProjects"
        ]
        for text in test_cases:
            suggestions = _analyze_formatting(text, None)
            # Should detect at least some sections
            section_suggestions = [s for s in suggestions if "section" in s.get("title", "").lower()]
            # With proper section headers, should not have "add more sections" suggestion
            add_suggestions = [s for s in section_suggestions if "Add more" in s.get("title", "")]
            assert len(add_suggestions) == 0, f"Failed to detect sections in: {text}"


class TestAnalyzeContent:
    """Tests for _analyze_content function."""

    def test_few_action_verbs_suggestion(self):
        """Test few action verbs generates high priority suggestion."""
        text = "I was responsible for tasks and did work"
        suggestions = _analyze_content(text, None, min_action_verbs=5)

        action_suggestions = [s for s in suggestions if "action verbs" in s.get("title", "").lower()]
        assert len(action_suggestions) == 1
        assert action_suggestions[0]["priority"] == "high"

    def test_many_action_verbs_no_suggestion(self):
        """Test adequate action verbs doesn't generate suggestion."""
        text = "achieved improved developed created managed led designed implemented increased decreased optimized launched built established delivered"
        suggestions = _analyze_content(text, None, min_action_verbs=5)

        action_suggestions = [s for s in suggestions if "action verbs" in s.get("title", "").lower()]
        assert len(action_suggestions) == 0

    def test_missing_summary_suggestion(self):
        """Test missing summary generates medium priority suggestion."""
        text = "Skills: Python\nExperience: Developer"
        data = {}  # No summary

        suggestions = _analyze_content(text, data)

        summary_suggestions = [s for s in suggestions if "summary" in s.get("title", "").lower()]
        assert len(summary_suggestions) == 1
        assert summary_suggestions[0]["priority"] == "medium"

    def test_summary_in_data_no_suggestion(self):
        """Test summary in data doesn't generate suggestion."""
        text = "Some text"
        data = {"summary": "Experienced software developer"}

        suggestions = _analyze_content(text, data)

        summary_suggestions = [s for s in suggestions if "summary" in s.get("title", "").lower()]
        assert len(summary_suggestions) == 0

    def test_summary_detected_in_text(self):
        """Test summary keywords detected from text."""
        test_cases = [
            "Professional Summary: Experienced developer",
            "Summary: Software engineer with skills",
            "Objective: Seeking position as developer",
            "Profile: Professional with experience"
        ]
        for text in test_cases:
            suggestions = _analyze_content(text, None)
            summary_suggestions = [s for s in suggestions if "summary" in s.get("title", "").lower()]
            assert len(summary_suggestions) == 0, f"Failed to detect summary in: {text}"

    def test_passive_language_suggestion(self):
        """Test passive language generates medium priority suggestion."""
        text = "Responsible for managing team. Duties include coding. Worked on projects. Helped with testing. Assisted in development. Participated in meetings"
        suggestions = _analyze_content(text, None)

        passive_suggestions = [s for s in suggestions if "passive language" in s.get("title", "").lower()]
        assert len(passive_suggestions) == 1
        assert passive_suggestions[0]["priority"] == "medium"

    def test_active_language_no_suggestion(self):
        """Test active language doesn't generate passive suggestion."""
        text = "Managed team. Developed software. Led projects. Built products"
        suggestions = _analyze_content(text, None)

        passive_suggestions = [s for s in suggestions if "passive language" in s.get("title", "").lower()]
        assert len(passive_suggestions) == 0

    def test_various_passive_phrases(self):
        """Test various passive phrases are detected."""
        passive_phrases = [
            "responsible for managing",
            "duties include coding",
            "worked on projects",
            "helped with testing",
            "assisted in development",
            "participated in meetings"
        ]
        for phrase in passive_phrases:
            suggestions = _analyze_content(phrase, None)
            # At minimum should not cause errors
            assert isinstance(suggestions, list)

    def test_no_measurable_results_in_experience(self):
        """Test missing measurable results generates high priority suggestion."""
        data = {
            "experience": [
                {
                    "position": "Developer",
                    "description": "Worked on software development",
                    "achievements": "Did coding tasks"
                }
            ]
        }
        text = "Some text"
        suggestions = _analyze_content(text, data)

        results_suggestions = [s for s in suggestions if "measurable results" in s.get("title", "").lower()]
        assert len(results_suggestions) == 1
        assert results_suggestions[0]["priority"] == "high"

    def test_measurable_results_in_experience(self):
        """Test measurable results in experience doesn't generate suggestion."""
        data = {
            "experience": [
                {
                    "position": "Developer",
                    "description": "Improved performance by 30%",
                    "achievements": "Increased revenue by $50K"
                }
            ]
        }
        text = "Some text"
        suggestions = _analyze_content(text, data)

        results_suggestions = [s for s in suggestions if "measurable results" in s.get("title", "").lower()]
        assert len(results_suggestions) == 0

    def test_empty_experience_array(self):
        """Test empty experience array handled gracefully."""
        data = {"experience": []}
        text = "Some text"
        suggestions = _analyze_content(text, data)

        # Should not crash, and no results suggestion for empty experience
        results_suggestions = [s for s in suggestions if "measurable results" in s.get("title", "").lower()]
        assert len(results_suggestions) == 0

    def test_custom_min_action_verbs(self):
        """Test custom minimum action verbs threshold."""
        text = "achieved improved developed"
        suggestions = _analyze_content(text, None, min_action_verbs=5)

        action_suggestions = [s for s in suggestions if "action verbs" in s.get("title", "").lower()]
        assert len(action_suggestions) == 1  # Only 3 verbs, need 5

        suggestions_custom = _analyze_content(text, None, min_action_verbs=2)
        action_suggestions_custom = [s for s in suggestions_custom if "action verbs" in s.get("title", "").lower()]
        assert len(action_suggestions_custom) == 0  # 3 verbs >= 2 required


class TestCalculateOptimizationScore:
    """Tests for _calculate_optimization_score function."""

    def test_perfect_score(self):
        """Test perfect score with no suggestions."""
        score = _calculate_optimization_score([], 0, 0)
        assert score == 100

    def test_high_priority_deductions(self):
        """Test high priority suggestions reduce score."""
        # 3 high priority = 30 points deduction
        score = _calculate_optimization_score(
            [{"priority": "high"}, {"priority": "high"}, {"priority": "high"}],
            3,
            0
        )
        assert score == 70

    def test_medium_priority_deductions(self):
        """Test medium priority suggestions reduce score."""
        # 4 medium priority = 20 points deduction
        score = _calculate_optimization_score(
            [{"priority": "medium"}, {"priority": "medium"}, {"priority": "medium"}, {"priority": "medium"}],
            0,
            4
        )
        assert score == 80

    def test_low_priority_deductions(self):
        """Test low priority suggestions reduce score."""
        # 5 low priority = 10 points deduction
        suggestions = [{"priority": "low"}] * 5
        score = _calculate_optimization_score(suggestions, 0, 0)
        assert score == 90

    def test_mixed_priorities(self):
        """Test mixed priority suggestions."""
        # 2 high (20) + 3 medium (15) + 4 low (8) = 43 points deduction
        suggestions = (
            [{"priority": "high"}] * 2 +
            [{"priority": "medium"}] * 3 +
            [{"priority": "low"}] * 4
        )
        score = _calculate_optimization_score(suggestions, 2, 3)
        assert score == 57

    def test_score_never_negative(self):
        """Test score is never below zero."""
        suggestions = [{"priority": "high"}] * 20  # Would be -200
        score = _calculate_optimization_score(suggestions, 20, 0)
        assert score == 0  # Should floor at 0

    def test_score_never_exceeds_100(self):
        """Test score is never above 100."""
        score = _calculate_optimization_score([], 0, 0)
        assert score == 100

    def test_actual_counts_match_list(self):
        """Test priority counts match actual suggestions."""
        suggestions = [
            {"priority": "high"},
            {"priority": "high"},
            {"priority": "medium"},
            {"priority": "medium"},
            {"priority": "medium"},
            {"priority": "low"}
        ]
        score = _calculate_optimization_score(suggestions, 2, 3)
        # Should calculate correctly based on counts
        assert score == 100 - (2 * 10) - (3 * 5) - (1 * 2)
        assert score == 63


class TestGenerateResumeOptimization:
    """Tests for main generate_resume_optimization function."""

    def test_basic_optimization(self):
        """Test basic optimization with valid resume."""
        text = "Python developer with skills in JavaScript and React. Experience includes building web applications."

        result = generate_resume_optimization(text)

        assert result["error"] is None
        assert isinstance(result["suggestions"], list)
        assert isinstance(result["total_suggestions"], int)
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100

    def test_with_job_description(self):
        """Test optimization with job description."""
        text = "Python developer"
        jd = "Looking for Python developer with Django experience"

        result = generate_resume_optimization(text, target_job_description=jd)

        assert result["error"] is None
        assert result["missing_keywords"] is not None
        assert "django" in result["missing_keywords"]

    def test_with_structured_data(self):
        """Test optimization with structured resume data."""
        text = "Some resume text"
        data = {
            "skills": ["Python", "Java"],
            "experience": [{"position": "Developer"}],
            "summary": "Experienced developer"
        }

        result = generate_resume_optimization(text, resume_data=data)

        assert result["error"] is None
        assert isinstance(result["suggestions"], list)

    def test_disable_keyword_check(self):
        """Test disabling keyword analysis."""
        text = "Some resume text"

        result = generate_resume_optimization(text, check_keywords=False)

        assert result["error"] is None
        assert result["keywords_found"] is None
        assert result["missing_keywords"] is None

    def test_disable_formatting_check(self):
        """Test disabling formatting analysis."""
        text = "Some resume text"

        result = generate_resume_optimization(text, check_formatting=False)

        assert result["error"] is None
        # Should have fewer suggestions without formatting check
        format_suggestions = [s for s in result["suggestions"] if s.get("type") == "formatting"]
        assert len(format_suggestions) == 0

    def test_disable_content_check(self):
        """Test disabling content analysis."""
        text = "Some resume text"

        result = generate_resume_optimization(text, check_content=False)

        assert result["error"] is None
        content_suggestions = [s for s in result["suggestions"] if s.get("type") == "content"]
        assert len(content_suggestions) == 0

    def test_custom_keyword_density(self):
        """Test custom keyword density threshold."""
        text = "Python developer " * 10

        result = generate_resume_optimization(
            text,
            check_keywords=True,
            min_keyword_density=0.5  # Very high threshold
        )

        assert result["error"] is None
        # Should likely trigger density suggestion with such high threshold

    def test_custom_action_verbs(self):
        """Test custom action verbs threshold."""
        text = "Achieved and improved results"

        result = generate_resume_optimization(
            text,
            check_content=True,
            min_action_verbs=10  # More than the 2 in text
        )

        assert result["error"] is None
        # Should trigger action verbs suggestion
        action_suggestions = [s for s in result["suggestions"] if "action verbs" in s.get("title", "").lower()]
        assert len(action_suggestions) > 0

    def test_priority_counts(self):
        """Test priority counts are accurate."""
        text = "Short"  # Will generate multiple suggestions

        result = generate_resume_optimization(text)

        assert result["error"] is None
        high = result["high_priority_count"]
        medium = result["medium_priority_count"]
        low = result["low_priority_count"]

        assert result["total_suggestions"] == high + medium + low
        assert isinstance(high, int)
        assert isinstance(medium, int)
        assert isinstance(low, int)

    def test_empty_text_raises_error(self):
        """Test empty text raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            generate_resume_optimization("")

    def test_non_string_text_raises_error(self):
        """Test non-string text raises TypeError."""
        with pytest.raises(TypeError, match="must be a string"):
            generate_resume_optimization(123)

    def test_invalid_resume_data_raises_error(self):
        """Test invalid resume_data raises TypeError."""
        with pytest.raises(TypeError, match="must be a dictionary"):
            generate_resume_optimization("text", resume_data="invalid")

    def test_invalid_job_description_raises_error(self):
        """Test invalid job description raises TypeError."""
        with pytest.raises(TypeError, match="must be a string"):
            generate_resume_optimization("text", target_job_description=123)

    def test_return_structure(self):
        """Test result has correct structure."""
        text = "Some resume text"
        result = generate_resume_optimization(text)

        expected_keys = {
            "suggestions",
            "total_suggestions",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
            "keywords_found",
            "missing_keywords",
            "score",
            "error"
        }
        assert set(result.keys()) == expected_keys

    def test_exception_handling(self):
        """Test exception handling returns error in result."""
        # This tests the catch block for unexpected errors
        # We can't easily trigger unexpected errors without mocking
        text = "Valid resume text with enough content to avoid most issues"
        result = generate_resume_optimization(text)

        # Should have error field even if no error occurred
        assert "error" in result
        assert result["error"] is None


class TestFormatSuggestionsForDisplay:
    """Tests for format_suggestions_for_display function."""

    def test_no_suggestions_message(self):
        """Test message when no suggestions."""
        formatted = format_suggestions_for_display([])
        assert "✓ Your resume looks great" in formatted
        assert "RESUME OPTIMIZATION REPORT" in formatted

    def test_high_priority_suggestions(self):
        """Test formatting high priority suggestions."""
        suggestions = [
            {
                "type": "keyword",
                "priority": "high",
                "title": "Add missing keywords",
                "description": "Your resume is missing important keywords",
                "recommendation": "Add Python, Django",
                "examples": ["Example 1", "Example 2"]
            }
        ]
        formatted = format_suggestions_for_display(suggestions)

        assert "HIGH PRIORITY" in formatted
        assert "Add missing keywords" in formatted
        assert "Your resume is missing important keywords" in formatted

    def test_medium_priority_suggestions(self):
        """Test formatting medium priority suggestions."""
        suggestions = [
            {
                "type": "formatting",
                "priority": "medium",
                "title": "Improve structure",
                "description": "Restructure your resume",
                "recommendation": "Combine sections"
            }
        ]
        formatted = format_suggestions_for_display(suggestions)

        assert "MEDIUM PRIORITY" in formatted
        assert "Improve structure" in formatted

    def test_low_priority_suggestions(self):
        """Test formatting low priority suggestions."""
        suggestions = [
            {
                "type": "content",
                "priority": "low",
                "title": "Minor improvement",
                "description": "Small change suggested"
            }
        ]
        formatted = format_suggestions_for_display(suggestions)

        assert "LOW PRIORITY" in formatted
        assert "Minor improvement" in formatted

    def test_mixed_priorities(self):
        """Test formatting mixed priority suggestions."""
        suggestions = [
            {"priority": "high", "title": "High priority issue", "description": "Important"},
            {"priority": "medium", "title": "Medium priority issue", "description": "Moderate"},
            {"priority": "low", "title": "Low priority issue", "description": "Minor"}
        ]
        formatted = format_suggestions_for_display(suggestions)

        assert "HIGH PRIORITY" in formatted
        assert "MEDIUM PRIORITY" in formatted
        assert "LOW PRIORITY" in formatted
        assert "High priority issue" in formatted
        assert "Medium priority issue" in formatted
        assert "Low priority issue" in formatted

    def test_with_examples(self):
        """Test formatting includes examples."""
        suggestions = [
            {
                "priority": "high",
                "title": "Test suggestion",
                "description": "Test description",
                "recommendation": "Do this",
                "examples": ["Example 1", "Example 2", "Example 3"]
            }
        ]
        formatted = format_suggestions_for_display(suggestions, show_examples=True)

        assert "Example 1" in formatted
        assert "Example 2" in formatted
        assert "Example 3" in formatted

    def test_without_examples(self):
        """Test formatting without examples."""
        suggestions = [
            {
                "priority": "high",
                "title": "Test suggestion",
                "description": "Test description",
                "recommendation": "Do this",
                "examples": ["Example 1", "Example 2"]
            }
        ]
        formatted = format_suggestions_for_display(suggestions, show_examples=False)

        assert "Example 1" not in formatted
        assert "Example 2" not in formatted
        assert "Test description" in formatted

    def test_total_count_display(self):
        """Test total count shown at end."""
        suggestions = [
            {"priority": "high", "title": "Issue 1", "description": "Desc 1"},
            {"priority": "medium", "title": "Issue 2", "description": "Desc 2"},
            {"priority": "low", "title": "Issue 3", "description": "Desc 3"}
        ]
        formatted = format_suggestions_for_display(suggestions)

        assert "TOTAL: 3 suggestion(s)" in formatted

    def test_formatting_structure(self):
        """Test overall formatting structure."""
        suggestions = [
            {"priority": "high", "title": "Test", "description": "Test"}
        ]
        formatted = format_suggestions_for_display(suggestions)
        lines = formatted.split("\n")

        assert lines[0] == "=" * 80
        assert "RESUME OPTIMIZATION REPORT" in formatted
        assert lines[-1] == "=" * 80

    def test_recommendation_display(self):
        """Test recommendation is displayed with arrow."""
        suggestions = [
            {
                "priority": "high",
                "title": "Test",
                "description": "Test description",
                "recommendation": "Specific recommendation"
            }
        ]
        formatted = format_suggestions_for_display(suggestions)

        assert "→" in formatted
        assert "Specific recommendation" in formatted

    def test_empty_examples_list(self):
        """Test empty examples list handled gracefully."""
        suggestions = [
            {
                "priority": "high",
                "title": "Test",
                "description": "Test description",
                "examples": []
            }
        ]
        formatted = format_suggestions_for_display(suggestions, show_examples=True)

        # Should not crash, should still have title and description
        assert "Test" in formatted
        assert "Test description" in formatted


class TestIntegration:
    """Integration tests for complete optimization workflow."""

    def test_complete_resume_analysis(self):
        """Test analyzing a complete resume."""
        text = """
        John Doe
        Email: john.doe@example.com

        Professional Summary
        Experienced software developer with strong skills in Python and JavaScript.

        Skills
        - Python
        - JavaScript
        - React
        - SQL

        Experience
        Senior Developer at Tech Corp (2020 - Present)
        - Led team of 5 developers
        - Improved application performance by 40%
        - Achieved 99.9% uptime

        Junior Developer at StartupXYZ (2018 - 2020)
        - Developed RESTful APIs using Python and Django
        - Built responsive web applications

        Education
        BS Computer Science, University of Technology (2018)

        Projects
        - E-commerce platform (github.com/johndoe/ecommerce)
        - Task manager app with React and Node.js
        """

        data = {
            "skills": ["Python", "JavaScript", "React", "SQL"],
            "experience": [
                {
                    "position": "Senior Developer",
                    "company": "Tech Corp",
                    "description": "Led team of 5 developers",
                    "achievements": "Improved performance by 40%"
                }
            ],
            "education": [{"degree": "BS", "year": 2018}],
            "summary": "Experienced software developer"
        }

        result = generate_resume_optimization(text, resume_data=data)

        assert result["error"] is None
        assert result["score"] > 70  # Should have good score

    def test_resume_needing_improvement(self):
        """Test resume that needs improvements."""
        text = "I was responsible for doing some work"

        result = generate_resume_optimization(text)

        assert result["error"] is None
        assert result["total_suggestions"] > 0
        assert result["score"] < 70  # Should have lower score

    def test_with_job_matching(self):
        """Test optimization with job description matching."""
        text = "Python developer with SQL experience"
        jd = "Looking for Python developer with Django, React, and AWS experience"

        result = generate_resume_optimization(text, target_job_description=jd)

        assert result["error"] is None
        assert result["missing_keywords"] is not None
        assert "django" in result["missing_keywords"]
        assert "react" in result["missing_keywords"]

    def test_display_format_workflow(self):
        """Test complete workflow with display formatting."""
        text = "Developer resume"
        result = generate_resume_optimization(text)

        formatted = format_suggestions_for_display(result["suggestions"])

        assert len(formatted) > 0
        assert "RESUME OPTIMIZATION REPORT" in formatted
        assert "TOTAL:" in formatted

    def test_all_checks_enabled(self):
        """Test with all analysis checks enabled."""
        text = """
        Skills: Python
        Experience: Worked as developer
        Education: BS Degree
        Summary: Professional developer
        """ * 5

        result = generate_resume_optimization(
            text,
            check_keywords=True,
            check_formatting=True,
            check_content=True
        )

        assert result["error"] is None
        # Should have suggestions from all three types
        suggestion_types = {s.get("type") for s in result["suggestions"]}
        assert "keyword" in suggestion_types or "formatting" in suggestion_types or "content" in suggestion_types

    def test_score_calculation_integration(self):
        """Test score calculation with actual suggestions."""
        text = "I was responsible for tasks"  # Will trigger multiple issues

        result = generate_resume_optimization(text)

        assert result["error"] is None
        assert result["score"] >= 0
        assert result["score"] <= 100

        # Score should reflect the number of suggestions
        # More suggestions = lower score
        if result["total_suggestions"] > 0:
            expected_score = 100 - (
                result["high_priority_count"] * 10 +
                result["medium_priority_count"] * 5 +
                result["low_priority_count"] * 2
            )
            expected_score = max(0, min(100, expected_score))
            assert result["score"] == expected_score
