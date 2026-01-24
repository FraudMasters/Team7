"""
Experience calculator for resume work history.

This module provides functions to calculate total work experience from resume data,
including handling overlapping periods, filtering by skills, and converting between
months and years.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse date string in various formats.

    Supports formats:
    - YYYY-MM-DD (ISO format)
    - MM/YYYY
    - YYYY-MM
    - Month YYYY (e.g., "May 2020")
    - None (returns None, indicating current date)

    Args:
        date_str: Date string to parse or None

    Returns:
        datetime object or None if date_str is None

    Raises:
        ValueError: If date string cannot be parsed

    Examples:
        >>> _parse_date("2023-02-01")
        datetime.datetime(2023, 2, 1, 0, 0)
        >>> _parse_date("02/2023")
        datetime.datetime(2023, 2, 1, 0, 0)
        >>> _parse_date(None)  # Returns None (current date)
    """
    if date_str is None:
        return None

    if not isinstance(date_str, str):
        raise ValueError(f"Date must be string or None, got {type(date_str)}")

    date_str = date_str.strip()

    # List of date formats to try
    formats = [
        "%Y-%m-%d",  # 2023-02-01
        "%Y-%m",  # 2023-02
        "%m/%Y",  # 02/2023
        "%m.%Y",  # 02.2023
        "%b %Y",  # Feb 2023
        "%B %Y",  # February 2023
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: {date_str}")


def _calculate_months_between(
    start_date: datetime, end_date: Optional[datetime]
) -> int:
    """
    Calculate the number of months between two dates.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive), or None for current date

    Returns:
        Number of months between dates (minimum 1 month)

    Examples:
        >>> from datetime import datetime
        >>> start = datetime(2023, 2, 1)
        >>> end = datetime(2023, 5, 1)
        >>> _calculate_months_between(start, end)
        3
    """
    if end_date is None:
        end_date = datetime.now()

    # Calculate month difference
    months = (end_date.year - start_date.year) * 12 + (
        end_date.month - start_date.month
    )

    # Add partial month if days indicate more than full months
    if end_date.day >= start_date.day:
        months += 1

    return max(1, months)  # Minimum 1 month


def _dates_overlap(
    period1_start: datetime,
    period1_end: Optional[datetime],
    period2_start: datetime,
    period2_end: Optional[datetime],
) -> bool:
    """
    Check if two date periods overlap.

    Args:
        period1_start: Start date of period 1
        period1_end: End date of period 1 (None means current date)
        period2_start: Start date of period 2
        period2_end: End date of period 2 (None means current date)

    Returns:
        True if periods overlap, False otherwise

    Examples:
        >>> from datetime import datetime
        >>> p1_start = datetime(2020, 1, 1)
        >>> p1_end = datetime(2020, 6, 1)
        >>> p2_start = datetime(2020, 5, 1)
        >>> p2_end = datetime(2020, 12, 1)
        >>> _dates_overlap(p1_start, p1_end, p2_start, p2_end)
        True
    """
    if period1_end is None:
        period1_end = datetime.now()
    if period2_end is None:
        period2_end = datetime.now()

    # Check for overlap: max(start1, start2) <= min(end1, end2)
    latest_start = max(period1_start, period2_start)
    earliest_end = min(period1_end, period2_end)

    return latest_start <= earliest_end


def calculate_total_experience(
    experience: List[Dict[str, Optional[str]]],
    *,
    handle_overlaps: bool = True,
    skip_invalid: bool = True,
) -> Dict[str, Optional[Union[int, str, List[Dict]]]]:
    """
    Calculate total work experience in months from a list of work periods.

    This function processes a list of work experience entries, each containing
    start and end dates, and calculates the total experience in months.
    It can handle overlapping periods to avoid double-counting.

    Args:
        experience: List of experience dictionaries, each containing:
            - start: Start date string (required)
            - end: End date string or None if current position (optional)
            - company: Company name (optional, for logging)
            - position: Job title (optional, for logging)
            - description: Job description (optional)
        handle_overlaps: If True, merge overlapping periods to avoid double-counting
        skip_invalid: If True, skip entries with invalid dates; if False, raise error

    Returns:
        Dictionary containing:
            - total_months: Total experience in months
            - total_years: Total experience in years (float)
            - periods: List of processed period information
            - overlap_count: Number of overlapping periods detected (if handle_overlaps=True)
            - error: Error message if calculation failed

    Raises:
        ValueError: If skip_invalid=False and entry has invalid dates

    Examples:
        >>> experience = [
        ...     {"start": "2020-05-01", "end": "2023-02-01", "company": "Company A"},
        ...     {"start": "2023-02-01", "end": None, "company": "Company B"},
        ... ]
        >>> result = calculate_total_experience(experience)
        >>> result["total_months"]
        46
    """
    if not experience:
        return {
            "total_months": 0,
            "total_years": 0.0,
            "periods": [],
            "overlap_count": 0,
        }

    try:
        periods = []
        overlap_count = 0

        for idx, entry in enumerate(experience):
            if not isinstance(entry, dict):
                if skip_invalid:
                    logger.warning(f"Skipping invalid entry {idx}: not a dictionary")
                    continue
                else:
                    raise ValueError(f"Entry {idx} is not a dictionary")

            start_str = entry.get("start")
            end_str = entry.get("end")

            if not start_str:
                if skip_invalid:
                    logger.warning(f"Skipping entry {idx}: missing start date")
                    continue
                else:
                    raise ValueError(f"Entry {idx} missing start date")

            try:
                start_date = _parse_date(start_str)
                end_date = _parse_date(end_str) if end_str else None
            except ValueError as e:
                if skip_invalid:
                    logger.warning(f"Skipping entry {idx}: {e}")
                    continue
                else:
                    raise ValueError(f"Entry {idx} has invalid date: {e}") from e

            months = _calculate_months_between(start_date, end_date)

            period_info = {
                "index": idx,
                "company": entry.get("company"),
                "position": entry.get("position"),
                "start": start_str,
                "end": end_str,
                "start_parsed": start_date.isoformat(),
                "end_parsed": end_date.isoformat() if end_date else None,
                "months": months,
            }
            periods.append(period_info)

        # Handle overlaps if requested
        if handle_overlaps and len(periods) > 1:
            merged_periods = _merge_overlapping_periods(periods)
            overlap_count = len(periods) - len(merged_periods)
            periods = merged_periods

        # Calculate total
        total_months = sum(p["months"] for p in periods)
        total_years = round(total_months / 12, 2)

        return {
            "total_months": total_months,
            "total_years": total_years,
            "periods": periods,
            "overlap_count": overlap_count if handle_overlaps else 0,
        }

    except Exception as e:
        logger.error(f"Error calculating total experience: {e}")
        return {
            "total_months": None,
            "total_years": None,
            "periods": [],
            "overlap_count": 0,
            "error": str(e),
        }


def _merge_overlapping_periods(
    periods: List[Dict],
) -> List[Dict]:
    """
    Merge overlapping periods to avoid double-counting months.

    Args:
        periods: List of period dictionaries with start_parsed, end_parsed, months

    Returns:
        List of merged periods without overlaps

    Examples:
        >>> periods = [
        ...     {"start_parsed": "2020-01-01", "end_parsed": "2020-06-01", "months": 6},
        ...     {"start_parsed": "2020-05-01", "end_parsed": "2020-12-01", "months": 8},
        ... ]
        >>> merged = _merge_overlapping_periods(periods)
        >>> len(merged)
        1
    """
    if not periods:
        return []

    # Sort by start date
    sorted_periods = sorted(
        periods,
        key=lambda p: datetime.fromisoformat(p["start_parsed"]),
    )

    merged = []
    current = sorted_periods[0].copy()

    for period in sorted_periods[1:]:
        current_start = datetime.fromisoformat(current["start_parsed"])
        current_end = datetime.fromisoformat(
            current["end_parsed"]
            if current["end_parsed"]
            else datetime.now().isoformat()
        )
        period_start = datetime.fromisoformat(period["start_parsed"])
        period_end = datetime.fromisoformat(
            period["end_parsed"]
            if period["end_parsed"]
            else datetime.now().isoformat()
        )

        # Check if periods overlap
        if _dates_overlap(current_start, current_end, period_start, period_end):
            # Merge periods
            merged_start = min(current_start, period_start)
            merged_end = max(current_end, period_end)

            current["start_parsed"] = merged_start.isoformat()
            current["end_parsed"] = merged_end.isoformat()
            current["months"] = _calculate_months_between(merged_start, merged_end)
        else:
            # No overlap, add current and start new
            merged.append(current)
            current = period.copy()

    merged.append(current)
    return merged


def calculate_skill_experience(
    experience: List[Dict[str, Optional[str]]],
    skill: str,
    *,
    case_sensitive: bool = False,
    handle_overlaps: bool = True,
) -> Dict[str, Optional[Union[int, str, List[Dict]]]]:
    """
    Calculate total experience with a specific skill across all projects.

    This function filters work experience entries where the specified skill
    is mentioned in the job description or position, then calculates the
    total duration in months.

    Args:
        experience: List of experience dictionaries
        skill: Skill name to search for (e.g., "Java", "Python", "React")
        case_sensitive: Whether skill matching should be case-sensitive
        handle_overlaps: If True, merge overlapping periods to avoid double-counting

    Returns:
        Dictionary containing:
            - skill: The skill searched for
            - total_months: Total months of experience with this skill
            - total_years: Total years of experience with this skill
            - matching_projects: List of projects where skill was found
            - projects_count: Number of projects where skill was found
            - error: Error message if calculation failed

    Examples:
        >>> experience = [
        ...     {
        ...         "start": "2020-05-01",
        ...         "end": "2023-02-01",
        ...         "description": "Java development using Spring Boot"
        ...     },
        ...     {
        ...         "start": "2023-02-01",
        ...         "end": None,
        ...         "description": "React frontend development"
        ...     },
        ... ]
        >>> result = calculate_skill_experience(experience, "Java")
        >>> result["total_months"]
        33
    """
    if not skill:
        return {
            "skill": skill,
            "total_months": 0,
            "total_years": 0.0,
            "matching_projects": [],
            "projects_count": 0,
            "error": "Skill cannot be empty",
        }

    try:
        matching_projects = []
        search_skill = skill if case_sensitive else skill.lower()

        for idx, entry in enumerate(experience):
            if not isinstance(entry, dict):
                continue

            # Search in description and position
            description = entry.get("description", "") or ""
            position = entry.get("position", "") or ""

            if case_sensitive:
                text = description + " " + position
            else:
                text = (description + " " + position).lower()

            # Check if skill is mentioned
            if search_skill in text:
                matching_projects.append(entry)

        # Calculate experience for matching projects
        result = calculate_total_experience(
            matching_projects, handle_overlaps=handle_overlaps
        )

        return {
            "skill": skill,
            "total_months": result.get("total_months", 0),
            "total_years": result.get("total_years", 0.0),
            "matching_projects": [
                {
                    "company": p.get("company"),
                    "position": p.get("position"),
                    "start": p.get("start"),
                    "end": p.get("end"),
                    "months": p.get("months"),
                }
                for p in result.get("periods", [])
            ],
            "projects_count": len(matching_projects),
            "error": result.get("error"),
        }

    except Exception as e:
        logger.error(f"Error calculating skill experience for '{skill}': {e}")
        return {
            "skill": skill,
            "total_months": None,
            "total_years": None,
            "matching_projects": [],
            "projects_count": 0,
            "error": str(e),
        }


def calculate_multiple_skills_experience(
    experience: List[Dict[str, Optional[str]]],
    skills: List[str],
    *,
    case_sensitive: bool = False,
    handle_overlaps: bool = True,
) -> Dict[str, Union[Dict, List[Dict]]]:
    """
    Calculate experience for multiple skills across all projects.

    This is a convenience function that calls calculate_skill_experience
    for each skill in the list and returns aggregated results.

    Args:
        experience: List of experience dictionaries
        skills: List of skill names to search for
        case_sensitive: Whether skill matching should be case-sensitive
        handle_overlaps: If True, merge overlapping periods for each skill

    Returns:
        Dictionary containing:
            - skills: Dictionary mapping skill name to experience data
            - summary: List of skills sorted by total experience (descending)
            - total_skills: Number of skills analyzed

    Examples:
        >>> experience = [
        ...     {
        ...         "start": "2020-05-01",
        ...         "end": "2023-02-01",
        ...         "description": "Java and Python development"
        ...     },
        ... ]
        >>> result = calculate_multiple_skills_experience(experience, ["Java", "Python"])
        >>> result["summary"][0]["skill"]  # Most experienced skill
        'Java'
    """
    if not skills:
        return {
            "skills": {},
            "summary": [],
            "total_skills": 0,
        }

    skills_data = {}

    for skill in skills:
        result = calculate_skill_experience(
            experience,
            skill,
            case_sensitive=case_sensitive,
            handle_overlaps=handle_overlaps,
        )
        skills_data[skill] = result

    # Create summary sorted by experience
    summary = sorted(
        [
            {
                "skill": skill,
                "total_months": data.get("total_months", 0),
                "total_years": data.get("total_years", 0.0),
                "projects_count": data.get("projects_count", 0),
            }
            for skill, data in skills_data.items()
        ],
        key=lambda x: x["total_months"] or 0,
        reverse=True,
    )

    return {
        "skills": skills_data,
        "summary": summary,
        "total_skills": len(skills),
    }


def format_experience_summary(
    experience_data: Dict[str, Optional[Union[int, str, List]]],
    *,
    include_periods: bool = False,
) -> str:
    """
    Format experience calculation results as a human-readable summary.

    Args:
        experience_data: Result dictionary from calculate_total_experience or
            calculate_skill_experience
        include_periods: Whether to include detailed period information

    Returns:
        Formatted string with experience summary

    Examples:
        >>> result = calculate_total_experience(experience)
        >>> print(format_experience_summary(result))
        Total Experience: 3 years and 10 months (46 months)
    """
    if experience_data.get("error"):
        return f"Error: {experience_data['error']}"

    total_months = experience_data.get("total_months")
    total_years = experience_data.get("total_years")

    if total_months is None:
        return "Unable to calculate experience"

    # Convert to years and months
    years = int(total_months // 12)
    months = int(total_months % 12)

    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months > 0 or years == 0:
        parts.append(f"{months} month{'s' if months != 1 else ''}")

    summary = "Total Experience: " + " and ".join(parts)
    summary += f" ({total_months} months)"

    if include_periods:
        periods = experience_data.get("periods", [])
        if periods:
            summary += "\n\nWork Periods:"
            for period in periods:
                company = period.get("company") or "Unknown"
                position = period.get("position") or "Unknown"
                months = period.get("months", 0)
                start = period.get("start", "Unknown")
                end = period.get("end") or "Present"
                summary += (
                    f"\n  - {company}: {position} ({start} to {end}) - {months} months"
                )

    return summary
