"""
Error detection for resume text and structured data.

This module provides functions to detect common resume issues including
missing contact information, length problems, portfolio requirements,
and other structural issues.
"""
import logging
import re
from typing import Dict, List, Optional, Union, Tuple

logger = logging.getLogger(__name__)

# Constants for validation
MAX_RESUME_LENGTH_CHARS = 10000  # ~3-4 pages
MIN_RESUME_LENGTH_CHARS = 500    # ~0.5 page
ENTRY_LEVEL_EXPERIENCE_MONTHS = 12  # 1 year


def detect_resume_errors(
    resume_text: str,
    resume_data: Optional[Dict[str, Union[str, List, Dict]]] = None,
    *,
    max_length: int = MAX_RESUME_LENGTH_CHARS,
    min_length: int = MIN_RESUME_LENGTH_CHARS,
    entry_level_months: int = ENTRY_LEVEL_EXPERIENCE_MONTHS,
    check_contact: bool = True,
    check_length: bool = True,
    check_portfolio: bool = True,
    check_sections: bool = True,
) -> Dict[str, Optional[Union[List[Dict[str, Union[str, int, List[str]]]], str, int]]]:
    """
    Detect errors and issues in resume text and structured data.

    This function performs comprehensive error detection including:
    - Missing contact information (email, phone)
    - Resume length issues (too long or too short)
    - Missing portfolio for entry-level candidates
    - Missing required sections (skills, experience, education)

    Args:
        resume_text: Raw resume text content
        resume_data: Optional structured resume data containing fields like:
            - contact: Dict with email, phone, linked_in, etc.
            - experience: List of experience entries
            - education: List of education entries
            - skills: List of skills or skills section
            - portfolio: Portfolio links or projects
            - total_experience_months: Total experience in months
        max_length: Maximum allowed resume length in characters
        min_length: Minimum recommended resume length in characters
        entry_level_months: Experience threshold for entry-level candidates (months)
        check_contact: Whether to check for contact information
        check_length: Whether to check resume length
        check_portfolio: Whether to check portfolio requirement
        check_sections: Whether to check for required sections

    Returns:
        Dictionary containing:
            - errors: List of detected errors with severity, type, message
            - total_errors: Total number of errors detected
            - critical_count: Number of critical errors
            - warning_count: Number of warnings
            - info_count: Number of info-level issues
            - error: Error message if analysis failed

    Raises:
        ValueError: If resume_text is empty or not a string
        TypeError: If invalid parameter types provided

    Examples:
        >>> text = "John Doe\\nEmail: john@example.com\\nExperience: ..."
        >>> data = {"contact": {"email": "john@example.com"}, "experience": [...]}
        >>> result = detect_resume_errors(text, data)
        >>> print(result["total_errors"])
        0

        >>> # Missing contact info
        >>> text = "John Doe\\nExperience: ..."
        >>> result = detect_resume_errors(text)
        >>> assert result["critical_count"] > 0
    """
    try:
        # Input validation
        if not isinstance(resume_text, str):
            raise TypeError("resume_text must be a string")

        if not resume_text or not resume_text.strip():
            raise ValueError("resume_text cannot be empty")

        if resume_data is not None and not isinstance(resume_data, dict):
            raise TypeError("resume_data must be a dictionary or None")

        logger.info("Starting resume error detection")
        errors = []

        # 1. Check resume length
        if check_length:
            length_errors = _check_resume_length(
                resume_text,
                max_length=max_length,
                min_length=min_length
            )
            errors.extend(length_errors)
            logger.info(f"Length check completed: {len(length_errors)} issues found")

        # 2. Check for contact information
        if check_contact:
            contact_errors = _check_contact_info(
                resume_text,
                resume_data
            )
            errors.extend(contact_errors)
            logger.info(f"Contact check completed: {len(contact_errors)} issues found")

        # 3. Check portfolio requirement for entry-level
        if check_portfolio:
            portfolio_errors = _check_portfolio_requirement(
                resume_text,
                resume_data,
                entry_level_months=entry_level_months
            )
            errors.extend(portfolio_errors)
            logger.info(f"Portfolio check completed: {len(portfolio_errors)} issues found")

        # 4. Check for required sections
        if check_sections:
            section_errors = _check_required_sections(
                resume_text,
                resume_data
            )
            errors.extend(section_errors)
            logger.info(f"Sections check completed: {len(section_errors)} issues found")

        # Count errors by severity
        critical_count = sum(1 for e in errors if e.get("severity") == "critical")
        warning_count = sum(1 for e in errors if e.get("severity") == "warning")
        info_count = sum(1 for e in errors if e.get("severity") == "info")

        logger.info(
            f"Error detection completed: {len(errors)} total errors "
            f"({critical_count} critical, {warning_count} warnings, {info_count} info)"
        )

        return {
            "errors": errors,
            "total_errors": len(errors),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "error": None,
        }

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in detect_resume_errors: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in detect_resume_errors: {e}")
        return {
            "errors": [],
            "total_errors": 0,
            "critical_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "error": f"Error detection failed: {str(e)}",
        }


def _check_resume_length(
    resume_text: str,
    max_length: int = MAX_RESUME_LENGTH_CHARS,
    min_length: int = MIN_RESUME_LENGTH_CHARS,
) -> List[Dict[str, Union[str, int, List[str]]]]:
    """
    Check if resume length is within acceptable range.

    Args:
        resume_text: Resume text content
        max_length: Maximum allowed length
        min_length: Minimum recommended length

    Returns:
        List of error dictionaries
    """
    errors = []
    text_length = len(resume_text)

    if text_length > max_length:
        errors.append({
            "type": "resume_too_long",
            "severity": "warning",
            "category": "length",
            "message": f"Resume is too long ({text_length:,} characters). "
                      f"Recommended maximum is {max_length:,} characters (~3-4 pages). "
                      f"Consider condensing to focus on most relevant experience.",
            "current_length": text_length,
            "recommended_max_length": max_length,
            "suggestions": [
                "Remove older or less relevant experience",
                "Combine similar bullet points",
                "Use more concise language",
                "Focus on achievements rather than duties"
            ]
        })

    if text_length < min_length:
        errors.append({
            "type": "resume_too_short",
            "severity": "warning",
            "category": "length",
            "message": f"Resume appears too short ({text_length} characters). "
                      f"Recommended minimum is {min_length:,} characters. "
                      f"Consider adding more detail about your experience and skills.",
            "current_length": text_length,
            "recommended_min_length": min_length,
            "suggestions": [
                "Add more detail to your experience descriptions",
                "Include specific achievements and metrics",
                "Expand on your skills and certifications",
                "Add relevant projects or volunteer work"
            ]
        })

    return errors


def _check_contact_info(
    resume_text: str,
    resume_data: Optional[Dict[str, Union[str, List, Dict]]] = None,
) -> List[Dict[str, Union[str, int, List[str]]]]:
    """
    Check for presence of contact information.

    Looks for email, phone number, and optionally LinkedIn profile.
    Checks both resume text and structured data.

    Args:
        resume_text: Resume text content
        resume_data: Optional structured resume data

    Returns:
        List of error dictionaries
    """
    errors = []

    # Regex patterns for contact information
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
    linkedin_pattern = r'linkedin\.com/in/[A-Za-z0-9-]+'

    # Check in structured data first
    has_email = False
    has_phone = False
    has_linkedin = False

    if resume_data:
        contact = resume_data.get("contact", {})
        if isinstance(contact, dict):
            has_email = bool(contact.get("email"))
            has_phone = bool(contact.get("phone"))
            has_linkedin = bool(contact.get("linked_in") or contact.get("linkedin"))

    # If not found in structured data, check text
    if not has_email:
        if re.search(email_pattern, resume_text, re.IGNORECASE):
            has_email = True

    if not has_phone:
        if re.search(phone_pattern, resume_text):
            has_phone = True

    if not has_linkedin:
        if re.search(linkedin_pattern, resume_text, re.IGNORECASE):
            has_linkedin = True

    # Generate errors for missing contact info
    if not has_email:
        errors.append({
            "type": "missing_email",
            "severity": "critical",
            "category": "contact",
            "message": "Email address is missing. This is essential for recruiters to contact you.",
            "field": "email",
            "suggestions": [
                "Add a professional email address",
                "Use a personal email rather than work email",
                "Avoid nicknames or unprofessional names in email"
            ]
        })

    if not has_phone:
        errors.append({
            "type": "missing_phone",
            "severity": "warning",
            "category": "contact",
            "message": "Phone number is missing. While not always critical, it provides another way for recruiters to reach you.",
            "field": "phone",
            "suggestions": [
                "Add a phone number where you can be reached",
                "Include country code if applying internationally"
            ]
        })

    if not has_linkedin:
        errors.append({
            "type": "missing_linkedin",
            "severity": "info",
            "category": "contact",
            "message": "LinkedIn profile URL is missing. Many recruiters use LinkedIn to learn more about candidates.",
            "field": "linkedin",
            "suggestions": [
                "Add your LinkedIn profile URL",
                "Ensure your profile is complete and up-to-date"
            ]
        })

    return errors


def _check_portfolio_requirement(
    resume_text: str,
    resume_data: Optional[Dict[str, Union[str, List, Dict]]] = None,
    entry_level_months: int = ENTRY_LEVEL_EXPERIENCE_MONTHS,
) -> List[Dict[str, Union[str, int, List[str]]]]:
    """
    Check for portfolio requirement for entry-level candidates.

    Entry-level candidates (less than 1 year experience) should include
    portfolio links or project descriptions to demonstrate their skills.

    Args:
        resume_text: Resume text content
        resume_data: Optional structured resume data
        entry_level_months: Experience threshold for entry-level (months)

    Returns:
        List of error dictionaries
    """
    errors = []

    # Determine if candidate is entry-level
    total_months = 0

    if resume_data:
        # Check if total_experience_months is provided
        total_months = resume_data.get("total_experience_months", 0)

        # If not, calculate from experience array
        if total_months == 0 and "experience" in resume_data:
            from analyzers.experience_calculator import calculate_total_experience
            exp_result = calculate_total_experience(resume_data["experience"])
            if exp_result.get("total_months"):
                total_months = exp_result["total_months"]

    # Check if entry-level
    is_entry_level = total_months < entry_level_months

    if not is_entry_level:
        # Not entry-level, no portfolio check needed
        return errors

    # For entry-level, check for portfolio/projects
    has_portfolio = False

    # Check structured data
    if resume_data:
        portfolio = resume_data.get("portfolio")
        if portfolio and (isinstance(portfolio, list) and len(portfolio) > 0 or
                          isinstance(portfolio, str) and portfolio.strip()):
            has_portfolio = True

    # Check text for portfolio indicators
    portfolio_keywords = [
        r'portfolio',
        r'github\.com',
        r'gitlab\.com',
        r'behance\.net',
        r'dribbble\.com',
        r'project',
        r'projects',
        r'demo',
        r'sample'
    ]

    if not has_portfolio:
        text_lower = resume_text.lower()
        for keyword in portfolio_keywords:
            if re.search(rf'\b{keyword}\b', text_lower):
                has_portfolio = True
                break

    if not has_portfolio:
        errors.append({
            "type": "missing_portfolio",
            "severity": "warning",
            "category": "portfolio",
            "message": f"Entry-level candidates (less than {entry_level_months // 12} year experience) "
                      f"should include portfolio links or project descriptions to demonstrate their skills.",
            "current_experience_months": total_months,
            "entry_level_threshold_months": entry_level_months,
            "suggestions": [
                "Add links to your portfolio or GitHub profile",
                "Include relevant academic or personal projects",
                "Link to live demos or sample work",
                "Include hackathon or open-source contributions"
            ]
        })

    return errors


def _check_required_sections(
    resume_text: str,
    resume_data: Optional[Dict[str, Union[str, List, Dict]]] = None,
) -> List[Dict[str, Union[str, int, List[str]]]]:
    """
    Check for presence of required resume sections.

    Checks for skills, experience, and education sections which are
    typically expected in resumes.

    Args:
        resume_text: Resume text content
        resume_data: Optional structured resume data

    Returns:
        List of error dictionaries
    """
    errors = []

    # Section indicators in text
    section_patterns = {
        "skills": [
            r'\bskills?:?\b',
            r'\btechnical\s+skills?\b',
            r'\bcompetencies?\b',
            r'\btechnologies?\b'
        ],
        "experience": [
            r'\bexperience?\b',
            r'\bwork\s+experience?\b',
            r'\bemployment\s+history\b',
            r'\bprofessional\s+experience?\b'
        ],
        "education": [
            r'\beducation?\b',
            r'\bacademic\s+background\b',
            r'\bqualifications?\b',
            r'\bdegree?\b'
        ]
    }

    # Check structured data first
    has_skills = False
    has_experience = False
    has_education = False

    if resume_data:
        has_skills = bool(resume_data.get("skills") or
                         resume_data.get("skill_set"))
        has_experience = bool(resume_data.get("experience") and
                             len(resume_data.get("experience", [])) > 0)
        has_education = bool(resume_data.get("education") and
                            len(resume_data.get("education", [])) > 0)

    # If not found in structured data, check text
    text_lower = resume_text.lower()

    if not has_skills:
        for pattern in section_patterns["skills"]:
            if re.search(pattern, text_lower):
                has_skills = True
                break

    if not has_experience:
        for pattern in section_patterns["experience"]:
            if re.search(pattern, text_lower):
                has_experience = True
                break

    if not has_education:
        for pattern in section_patterns["education"]:
            if re.search(pattern, text_lower):
                has_education = True
                break

    # Generate errors for missing sections
    if not has_skills:
        errors.append({
            "type": "missing_skills_section",
            "severity": "critical",
            "category": "structure",
            "message": "Skills section is missing. This is one of the most important sections for recruiters.",
            "section": "skills",
            "suggestions": [
                "Add a skills section listing your technical and professional skills",
                "Group skills by category (e.g., Programming Languages, Frameworks, Tools)",
                "Be specific about skill levels (e.g., 'Fluent in', 'Working knowledge of')"
            ]
        })

    if not has_experience:
        errors.append({
            "type": "missing_experience_section",
            "severity": "critical",
            "category": "structure",
            "message": "Experience section is missing. Recruiters need to see your work history.",
            "section": "experience",
            "suggestions": [
                "Add a work experience section with your previous positions",
                "Include company name, position, dates, and key responsibilities",
                "Focus on achievements and quantifiable results"
            ]
        })

    if not has_education:
        errors.append({
            "type": "missing_education_section",
            "severity": "warning",
            "category": "structure",
            "message": "Education section is missing. While not always critical, it's often expected.",
            "section": "education",
            "suggestions": [
                "Add your education history including degree, institution, and graduation year",
                "Include relevant coursework, honors, or certifications",
                "If self-taught, include online courses or bootcamps"
            ]
        })

    return errors


def get_error_summary(
    errors: List[Dict[str, Union[str, int, List[str]]]]
) -> Dict[str, Union[List[str], List[Dict[str, int]], int]]:
    """
    Get a summary of errors grouped by category and severity.

    Args:
        errors: List of error dictionaries from detect_resume_errors

    Returns:
        Dictionary containing:
            - by_category: Errors grouped by category
            - by_severity: Errors grouped by severity with counts
            - total: Total number of errors

    Examples:
        >>> errors = [
        ...     {"type": "missing_email", "severity": "critical", "category": "contact"},
        ...     {"type": "resume_too_long", "severity": "warning", "category": "length"}
        ... ]
        >>> summary = get_error_summary(errors)
        >>> assert summary["total"] == 2
    """
    by_category = {}
    by_severity = {
        "critical": [],
        "warning": [],
        "info": []
    }

    for error in errors:
        category = error.get("category", "other")
        severity = error.get("severity", "info")

        # Group by category
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(error.get("type"))

        # Group by severity
        if severity in by_severity:
            by_severity[severity].append(error.get("type"))

    return {
        "by_category": by_category,
        "by_severity": by_severity,
        "total": len(errors)
    }


def format_errors_for_display(
    errors: List[Dict[str, Union[str, int, List[str]]]],
    include_suggestions: bool = True
) -> str:
    """
    Format errors for human-readable display.

    Args:
        errors: List of error dictionaries from detect_resume_errors
        include_suggestions: Whether to include suggestions

    Returns:
        Formatted string with errors organized by severity

    Examples:
        >>> errors = [
        ...     {"type": "missing_email", "severity": "critical", "message": "Missing email"}
        ... ]
        >>> formatted = format_errors_for_display(errors)
        >>> "Missing email" in formatted
        True
    """
    if not errors:
        return "✓ No errors detected in resume."

    lines = []
    lines.append("=" * 80)
    lines.append("RESUME ERROR REPORT")
    lines.append("=" * 80)
    lines.append("")

    # Group by severity
    critical = [e for e in errors if e.get("severity") == "critical"]
    warnings = [e for e in errors if e.get("severity") == "warning"]
    info = [e for e in errors if e.get("severity") == "info"]

    if critical:
        lines.append(f"🔴 CRITICAL ISSUES ({len(critical)})")
        lines.append("-" * 80)
        for i, error in enumerate(critical, 1):
            lines.append(f"{i}. {error.get('message', 'Unknown error')}")
            if include_suggestions and error.get("suggestions"):
                lines.append("   Suggestions:")
                for suggestion in error["suggestions"]:
                    lines.append(f"   • {suggestion}")
            lines.append("")

    if warnings:
        lines.append(f"⚠️  WARNINGS ({len(warnings)})")
        lines.append("-" * 80)
        for i, error in enumerate(warnings, 1):
            lines.append(f"{i}. {error.get('message', 'Unknown warning')}")
            if include_suggestions and error.get("suggestions"):
                lines.append("   Suggestions:")
                for suggestion in error["suggestions"]:
                    lines.append(f"   • {suggestion}")
            lines.append("")

    if info:
        lines.append(f"ℹ️  INFO ({len(info)})")
        lines.append("-" * 80)
        for i, error in enumerate(info, 1):
            lines.append(f"{i}. {error.get('message', 'Unknown info')}")
            if include_suggestions and error.get("suggestions"):
                lines.append("   Suggestions:")
                for suggestion in error["suggestions"]:
                    lines.append(f"   • {suggestion}")
            lines.append("")

    lines.append("=" * 80)
    lines.append(f"TOTAL: {len(errors)} issue(s) found")
    lines.append("=" * 80)

    return "\n".join(lines)
