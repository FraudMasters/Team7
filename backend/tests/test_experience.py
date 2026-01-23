"""
Tests for experience calculator module.

Tests cover date parsing, experience calculation, skill filtering,
overlap handling, and edge cases.
"""
import pytest
from datetime import datetime
from analyzers.experience_calculator import (
    _parse_date,
    _calculate_months_between,
    _dates_overlap,
    calculate_total_experience,
    calculate_skill_experience,
    calculate_multiple_skills_experience,
    format_experience_summary,
)


class TestParseDate:
    """Tests for _parse_date function."""

    def test_parse_iso_date(self):
        """Test parsing ISO format dates (YYYY-MM-DD)."""
        result = _parse_date("2023-02-01")
        assert result == datetime(2023, 2, 1)

    def test_parse_year_month(self):
        """Test parsing year-month format (YYYY-MM)."""
        result = _parse_date("2023-02")
        assert result == datetime(2023, 2, 1)

    def test_parse_month_year_slash(self):
        """Test parsing month/year format with slash (MM/YYYY)."""
        result = _parse_date("02/2023")
        assert result == datetime(2023, 2, 1)

    def test_parse_month_year_dot(self):
        """Test parsing month.year format (MM.YYYY)."""
        result = _parse_date("02.2023")
        assert result == datetime(2023, 2, 1)

    def test_parse_month_name_year_short(self):
        """Test parsing short month name with year (Feb 2023)."""
        result = _parse_date("Feb 2023")
        assert result == datetime(2023, 2, 1)

    def test_parse_month_name_year_long(self):
        """Test parsing full month name with year (February 2023)."""
        result = _parse_date("February 2023")
        assert result == datetime(2023, 2, 1)

    def test_parse_none(self):
        """Test parsing None returns None."""
        result = _parse_date(None)
        assert result is None

    def test_parse_invalid_string(self):
        """Test parsing invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Unable to parse date"):
            _parse_date("invalid-date")

    def test_parse_non_string_raises_error(self):
        """Test parsing non-string raises ValueError."""
        with pytest.raises(ValueError, match="Date must be string"):
            _parse_date(123)


class TestCalculateMonthsBetween:
    """Tests for _calculate_months_between function."""

    def test_same_month(self):
        """Test same month returns 1."""
        start = datetime(2023, 2, 1)
        end = datetime(2023, 2, 15)
        result = _calculate_months_between(start, end)
        assert result == 1

    def test_different_months_same_year(self):
        """Test different months in same year."""
        start = datetime(2023, 2, 1)
        end = datetime(2023, 5, 1)
        result = _calculate_months_between(start, end)
        assert result == 3

    def test_different_years(self):
        """Test months across different years."""
        start = datetime(2020, 5, 1)
        end = datetime(2023, 2, 1)
        result = _calculate_months_between(start, end)
        assert result == 33

    def test_end_date_none(self):
        """Test with end_date as None (current date)."""
        start = datetime(2023, 2, 1)
        result = _calculate_months_between(start, None)
        # Should be approximately months from start to now
        assert result >= 1

    def test_february_2020_to_april_2024(self):
        """Test specific example from spec: Project 1 example."""
        start = datetime(2023, 2, 1)
        end = datetime(2024, 4, 1)
        result = _calculate_months_between(start, end)
        assert result == 14

    def test_may_2020_to_february_2023(self):
        """Test specific example from spec: Project 2 example."""
        start = datetime(2020, 5, 1)
        end = datetime(2023, 2, 1)
        result = _calculate_months_between(start, end)
        assert result == 33


class TestDatesOverlap:
    """Tests for _dates_overlap function."""

    def test_overlapping_periods(self):
        """Test clearly overlapping periods."""
        p1_start = datetime(2020, 1, 1)
        p1_end = datetime(2020, 6, 1)
        p2_start = datetime(2020, 5, 1)
        p2_end = datetime(2020, 12, 1)
        result = _dates_overlap(p1_start, p1_end, p2_start, p2_end)
        assert result is True

    def test_non_overlapping_periods(self):
        """Test clearly non-overlapping periods."""
        p1_start = datetime(2020, 1, 1)
        p1_end = datetime(2020, 6, 1)
        p2_start = datetime(2020, 7, 1)
        p2_end = datetime(2020, 12, 1)
        result = _dates_overlap(p1_start, p1_end, p2_start, p2_end)
        assert result is False

    def test_adjacent_periods(self):
        """Test adjacent periods (end = start)."""
        p1_start = datetime(2020, 1, 1)
        p1_end = datetime(2020, 6, 1)
        p2_start = datetime(2020, 6, 1)
        p2_end = datetime(2020, 12, 1)
        result = _dates_overlap(p1_start, p1_end, p2_start, p2_end)
        assert result is True

    def test_period_with_none_end(self):
        """Test period with None end date (current)."""
        p1_start = datetime(2023, 1, 1)
        p1_end = None
        p2_start = datetime(2023, 6, 1)
        p2_end = datetime(2023, 12, 1)
        result = _dates_overlap(p1_start, p1_end, p2_start, p2_end)
        assert result is True


class TestCalculateTotalExperience:
    """Tests for calculate_total_experience function."""

    def test_empty_experience_list(self):
        """Test with empty experience list."""
        result = calculate_total_experience([])
        assert result["total_months"] == 0
        assert result["total_years"] == 0.0
        assert result["periods"] == []

    def test_single_project(self):
        """Test with single project."""
        experience = [
            {
                "start": "2020-05-01",
                "end": "2023-02-01",
                "company": "Test Company",
                "position": "Developer",
            }
        ]
        result = calculate_total_experience(experience)
        assert result["total_months"] == 33
        assert result["total_years"] == 2.75
        assert len(result["periods"]) == 1
        assert result["periods"][0]["company"] == "Test Company"

    def test_multiple_non_overlapping_projects(self):
        """Test with multiple non-overlapping projects."""
        experience = [
            {"start": "2020-05-01", "end": "2021-05-01", "company": "Company A"},
            {"start": "2021-06-01", "end": "2022-06-01", "company": "Company B"},
        ]
        result = calculate_total_experience(experience, handle_overlaps=False)
        assert result["total_months"] == 24

    def test_overlapping_projects_with_merge(self):
        """Test overlapping projects with merge enabled."""
        experience = [
            {
                "start": "2020-01-01",
                "end": "2020-12-01",
                "company": "Company A",
                "description": "Project A",
            },
            {
                "start": "2020-10-01",
                "end": "2021-06-01",
                "company": "Company B",
                "description": "Project B",
            },
        ]
        result = calculate_total_experience(experience, handle_overlaps=True)
        # Should merge to avoid double-counting Oct-Dec 2020
        assert result["total_months"] == 17  # Jan 2020 to Jun 2021
        assert result["overlap_count"] == 1

    def test_overlapping_projects_without_merge(self):
        """Test overlapping projects with merge disabled."""
        experience = [
            {"start": "2020-01-01", "end": "2020-12-01", "company": "Company A"},
            {"start": "2020-10-01", "end": "2021-06-01", "company": "Company B"},
        ]
        result = calculate_total_experience(experience, handle_overlaps=False)
        # Should count both separately
        assert result["total_months"] == 19  # 12 + 7
        assert result["overlap_count"] == 0

    def test_current_position_null_end(self):
        """Test project with null end date (current position)."""
        experience = [
            {"start": "2023-02-01", "end": None, "company": "Current Company"}
        ]
        result = calculate_total_experience(experience)
        # Should calculate from start to current date
        assert result["total_months"] >= 1

    def test_spec_example_resume(self):
        """Test using the exact example from the spec."""
        experience = [
            {
                "start": "2023-02-01",
                "end": "2024-04-01",
                "company": "МТС",
                "position": "Ведущий разработчик",
            },
            {
                "start": "2020-05-01",
                "end": "2023-02-01",
                "company": "JBorn",
                "position": "Java-разработчик",
            },
        ]
        result = calculate_total_experience(experience)
        # 14 months + 33 months = 47 months
        assert result["total_months"] == 47
        assert result["total_years"] == 3.92

    def test_skip_invalid_entries(self):
        """Test skipping invalid entries when skip_invalid=True."""
        experience = [
            {"start": "2020-05-01", "end": "2021-05-01", "company": "Valid"},
            {"start": "invalid-date", "end": "2021-06-01", "company": "Invalid"},
            {"start": "2021-07-01", "end": "2022-07-01", "company": "Valid"},
        ]
        result = calculate_total_experience(experience, skip_invalid=True)
        # Should skip the invalid entry
        assert result["total_months"] == 24

    def test_raise_on_invalid_entries(self):
        """Test raising error on invalid entries when skip_invalid=False."""
        experience = [
            {"start": "invalid-date", "end": "2021-06-01", "company": "Invalid"}
        ]
        with pytest.raises(ValueError, match="has invalid date"):
            calculate_total_experience(experience, skip_invalid=False)

    def test_missing_start_date(self):
        """Test entry with missing start date."""
        experience = [{"end": "2021-05-01", "company": "No Start"}]
        result = calculate_total_experience(experience, skip_invalid=True)
        assert result["total_months"] == 0

    def test_non_dictionary_entry(self):
        """Test with non-dictionary entry in list."""
        experience = [
            {"start": "2020-05-01", "end": "2021-05-01"},
            "not a dictionary",
        ]
        result = calculate_total_experience(experience, skip_invalid=True)
        assert result["total_months"] == 12


class TestCalculateSkillExperience:
    """Tests for calculate_skill_experience function."""

    def test_empty_skill(self):
        """Test with empty skill string."""
        experience = [{"start": "2020-01-01", "end": "2021-01-01"}]
        result = calculate_skill_experience(experience, "")
        assert result["error"] == "Skill cannot be empty"

    def test_skill_found_in_description(self):
        """Test skill found in job description."""
        experience = [
            {
                "start": "2020-05-01",
                "end": "2023-02-01",
                "description": "Java development using Spring Boot",
            }
        ]
        result = calculate_skill_experience(experience, "Java")
        assert result["total_months"] == 33
        assert result["projects_count"] == 1

    def test_skill_found_in_position(self):
        """Test skill found in position title."""
        experience = [
            {
                "start": "2023-02-01",
                "end": None,
                "position": "Java Developer",
                "description": "Backend development",
            }
        ]
        result = calculate_skill_experience(experience, "Java")
        assert result["total_months"] >= 1
        assert result["projects_count"] == 1

    def test_skill_not_found(self):
        """Test skill not found in any project."""
        experience = [
            {
                "start": "2020-05-01",
                "end": "2023-02-01",
                "description": "Python development using Django",
            }
        ]
        result = calculate_skill_experience(experience, "Java")
        assert result["total_months"] == 0
        assert result["projects_count"] == 0

    def test_case_insensitive_search(self):
        """Test case-insensitive skill search (default)."""
        experience = [
            {
                "start": "2020-05-01",
                "end": "2021-05-01",
                "description": "java development",
            }
        ]
        result = calculate_skill_experience(experience, "JAVA", case_sensitive=False)
        assert result["total_months"] == 12

    def test_case_sensitive_search(self):
        """Test case-sensitive skill search."""
        experience = [
            {
                "start": "2020-05-01",
                "end": "2021-05-01",
                "description": "java development",
            }
        ]
        result = calculate_skill_experience(experience, "JAVA", case_sensitive=True)
        assert result["total_months"] == 0

    def test_multiple_projects_with_same_skill(self):
        """Test skill appearing in multiple projects."""
        experience = [
            {
                "start": "2020-05-01",
                "end": "2021-05-01",
                "description": "Java backend development",
            },
            {
                "start": "2021-06-01",
                "end": "2023-02-01",
                "description": "Java full-stack development",
            },
        ]
        result = calculate_skill_experience(experience, "Java")
        assert result["total_months"] == 33  # 12 + 21
        assert result["projects_count"] == 2

    def test_spec_java_example(self):
        """Test using the Java example from the spec."""
        experience = [
            {
                "start": "2023-02-01",
                "end": "2024-04-01",
                "description": "Java 11, Spring Framework",
                "company": "МТС",
            },
            {
                "start": "2020-05-01",
                "end": "2023-02-01",
                "description": "Java 8, Spring Boot",
                "company": "JBorn",
            },
        ]
        result = calculate_skill_experience(experience, "Java")
        # 14 + 33 = 47 months total with Java
        assert result["total_months"] == 47
        assert result["total_years"] == 3.92
        assert result["projects_count"] == 2

    def test_react_skill_example(self):
        """Test using the React example from the spec."""
        experience = [
            {
                "start": "2021-01-01",
                "end": "2024-05-01",
                "description": "ReactJS and TypeScript development",
            }
        ]
        result = calculate_skill_experience(experience, "ReactJS")
        assert result["total_months"] == 40
        assert result["total_years"] == 3.33

    def test_skill_with_overlaps_merge(self):
        """Test skill experience with overlapping projects merged."""
        experience = [
            {
                "start": "2020-01-01",
                "end": "2020-12-01",
                "description": "Java project A",
            },
            {
                "start": "2020-10-01",
                "end": "2021-06-01",
                "description": "Java project B",
            },
        ]
        result = calculate_skill_experience(experience, "Java", handle_overlaps=True)
        # Should merge overlapping periods
        assert result["total_months"] == 17

    def test_partial_skill_match(self):
        """Test partial skill matching (substring)."""
        experience = [
            {
                "start": "2020-01-01",
                "end": "2021-01-01",
                "description": "JavaScript development",
            }
        ]
        result = calculate_skill_experience(experience, "Java")
        # Should match "Java" in "JavaScript"
        assert result["total_months"] == 12

    def test_skill_in_multiple_fields(self):
        """Test skill found in both position and description."""
        experience = [
            {
                "start": "2020-01-01",
                "end": "2021-01-01",
                "position": "Python Developer",
                "description": "Python backend development",
            }
        ]
        result = calculate_skill_experience(experience, "Python")
        assert result["total_months"] == 12


class TestCalculateMultipleSkillsExperience:
    """Tests for calculate_multiple_skills_experience function."""

    def test_empty_skills_list(self):
        """Test with empty skills list."""
        experience = [{"start": "2020-01-01", "end": "2021-01-01"}]
        result = calculate_multiple_skills_experience(experience, [])
        assert result["total_skills"] == 0
        assert result["skills"] == {}
        assert result["summary"] == []

    def test_single_skill(self):
        """Test with single skill."""
        experience = [
            {"start": "2020-01-01", "end": "2021-01-01", "description": "Java dev"}
        ]
        result = calculate_multiple_skills_experience(experience, ["Java"])
        assert result["total_skills"] == 1
        assert "Java" in result["skills"]
        assert result["summary"][0]["skill"] == "Java"

    def test_multiple_skills(self):
        """Test with multiple skills."""
        experience = [
            {
                "start": "2020-01-01",
                "end": "2021-01-01",
                "description": "Java and Python development",
            },
            {
                "start": "2021-02-01",
                "end": "2022-02-01",
                "description": "Python and React development",
            },
        ]
        result = calculate_multiple_skills_experience(
            experience, ["Java", "Python", "React"]
        )
        assert result["total_skills"] == 3
        assert result["skills"]["Java"]["total_months"] == 12
        assert result["skills"]["Python"]["total_months"] == 24
        assert result["skills"]["React"]["total_months"] == 12

    def test_summary_sorted_by_experience(self):
        """Test that summary is sorted by experience (descending)."""
        experience = [
            {
                "start": "2020-01-01",
                "end": "2022-01-01",
                "description": "Python development",
            },
            {
                "start": "2022-02-01",
                "end": "2022-08-01",
                "description": "React development",
            },
        ]
        result = calculate_multiple_skills_experience(
            experience, ["Python", "React"]
        )
        summary = result["summary"]
        assert summary[0]["skill"] == "Python"
        assert summary[0]["total_months"] == 24
        assert summary[1]["skill"] == "React"
        assert summary[1]["total_months"] == 6


class TestFormatExperienceSummary:
    """Tests for format_experience_summary function."""

    def test_format_basic_experience(self):
        """Test formatting basic experience result."""
        data = {"total_months": 46, "total_years": 3.83}
        result = format_experience_summary(data)
        assert "3 years" in result
        assert "10 months" in result
        assert "46 months" in result

    def test_format_months_only(self):
        """Test formatting experience less than 1 year."""
        data = {"total_months": 8, "total_years": 0.67}
        result = format_experience_summary(data)
        assert "8 months" in result
        assert "0 years" not in result

    def test_format_years_only(self):
        """Test formatting exact years."""
        data = {"total_months": 24, "total_years": 2.0}
        result = format_experience_summary(data)
        assert "2 years" in result
        assert "0 months" not in result

    def test_format_with_periods(self):
        """Test formatting with period details."""
        data = {
            "total_months": 12,
            "total_years": 1.0,
            "periods": [
                {
                    "company": "Test Company",
                    "position": "Developer",
                    "start": "2020-01-01",
                    "end": "2021-01-01",
                    "months": 12,
                }
            ],
        }
        result = format_experience_summary(data, include_periods=True)
        assert "Test Company" in result
        assert "Developer" in result
        assert "Work Periods" in result

    def test_format_error(self):
        """Test formatting error result."""
        data = {"error": "Test error", "total_months": None}
        result = format_experience_summary(data)
        assert "Error" in result
        assert "Test error" in result

    def test_format_none_experience(self):
        """Test formatting None experience."""
        data = {"total_months": None, "total_years": None}
        result = format_experience_summary(data)
        assert "Unable to calculate" in result

    def test_singular_plurals(self):
        """Test correct singular/plural forms."""
        # 1 month
        result1 = format_experience_summary({"total_months": 1, "total_years": 0.08})
        assert "1 month" in result1

        # 2 months
        result2 = format_experience_summary({"total_months": 2, "total_years": 0.17})
        assert "2 months" in result2

        # 1 year
        result3 = format_experience_summary({"total_months": 12, "total_years": 1.0})
        assert "1 year" in result3

        # 2 years
        result4 = format_experience_summary({"total_months": 24, "total_years": 2.0})
        assert "2 years" in result4


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_very_long_experience(self):
        """Test very long experience duration (20+ years)."""
        experience = [
            {"start": "2000-01-01", "end": "2023-01-01", "company": "Long Term"}
        ]
        result = calculate_total_experience(experience)
        assert result["total_months"] == 276  # 23 years
        assert result["total_years"] == 23.0

    def test_very_short_experience(self):
        """Test very short experience (1 month)."""
        experience = [
            {"start": "2023-01-01", "end": "2023-01-15", "company": "Short Term"}
        ]
        result = calculate_total_experience(experience)
        assert result["total_months"] >= 1

    def test_feb_29_leap_year(self):
        """Test date parsing including leap year."""
        result = _parse_date("2020-02-29")
        assert result == datetime(2020, 2, 29)

    def test_missing_description_and_position(self):
        """Test experience entries without description or position."""
        experience = [
            {"start": "2020-01-01", "end": "2021-01-01", "company": "Company"}
        ]
        result = calculate_skill_experience(experience, "Java")
        assert result["total_months"] == 0

    def test_empty_description(self):
        """Test experience with empty string description."""
        experience = [
            {
                "start": "2020-01-01",
                "end": "2021-01-01",
                "description": "",
                "position": "",
            }
        ]
        result = calculate_skill_experience(experience, "Java")
        assert result["total_months"] == 0

    def test_concurrent_projects(self):
        """Test completely concurrent projects (same dates)."""
        experience = [
            {"start": "2020-01-01", "end": "2021-01-01", "company": "Company A"},
            {"start": "2020-01-01", "end": "2021-01-01", "company": "Company B"},
        ]
        result = calculate_total_experience(experience, handle_overlaps=True)
        # Should merge to 12 months, not 24
        assert result["total_months"] == 12

    def test_nested_periods(self):
        """Test one period completely inside another."""
        experience = [
            {"start": "2020-01-01", "end": "2022-01-01", "company": "Company A"},
            {"start": "2020-06-01", "end": "2021-06-01", "company": "Company B"},
        ]
        result = calculate_total_experience(experience, handle_overlaps=True)
        # Should only count outer period
        assert result["total_months"] == 24
