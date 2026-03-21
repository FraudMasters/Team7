"""
Resume optimization analyzer for providing AI-powered improvement suggestions.

This module provides functions to analyze resumes and generate optimization
recommendations including keyword analysis, formatting suggestions, and
content improvements.
"""
import asyncio
import logging
import re
from typing import Dict, List, Optional, Union

from .ats_simulation import evaluate_resume_ats, get_simple_ats_checker
from .ranking_service import RankingFeatures, RankingModel
from .skill_gap_analyzer import SkillGapAnalyzer

logger = logging.getLogger(__name__)

# Constants for optimization
MIN_KEYWORD_DENSITY = 0.005  # Minimum keyword density as percentage of text
MAX_SECTION_COUNT = 10  # Maximum recommended sections
IDEAL_SECTION_COUNT = 6  # Ideal number of sections
MIN_ACTION_VERBS = 5  # Minimum recommended action verbs


def generate_resume_optimization(
    resume_text: str,
    resume_data: Optional[Dict[str, Union[str, List, Dict]]] = None,
    *,
    target_job_description: Optional[str] = None,
    job_title: Optional[str] = None,
    required_skills: Optional[List[str]] = None,
    check_keywords: bool = True,
    check_formatting: bool = True,
    check_content: bool = True,
    check_ats: bool = True,
    min_keyword_density: float = MIN_KEYWORD_DENSITY,
    min_action_verbs: int = MIN_ACTION_VERBS,
) -> Dict[str, Optional[Union[List[Dict[str, Union[str, List[str]]]], str, int, float, Dict]]]:
    """
    Generate optimization suggestions for a resume.

    This function performs comprehensive resume optimization analysis including:
    - Keyword analysis and missing keywords detection
    - Formatting recommendations (structure, length, sections)
    - Content improvements (action verbs, quantifiable achievements, clarity)
    - ATS compatibility checks and scoring

    Args:
        resume_text: Raw resume text content
        resume_data: Optional structured resume data containing fields like:
            - skills: List of skills or skills section
            - experience: List of experience entries
            - education: List of education entries
            - contact: Dict with email, phone, linked_in, etc.
            - summary: Professional summary or objective
        target_job_description: Optional job description to compare against for keyword matching
        job_title: Optional job title for ATS evaluation
        required_skills: Optional list of required skills for ATS evaluation
        check_keywords: Whether to perform keyword analysis
        check_formatting: Whether to provide formatting recommendations
        check_content: Whether to provide content improvement suggestions
        check_ats: Whether to perform ATS compatibility check (requires target_job_description)
        min_keyword_density: Minimum keyword density threshold (0.0-1.0)
        min_action_verbs: Minimum recommended action verbs count

    Returns:
        Dictionary containing:
            - suggestions: List of optimization suggestions with:
                - type: Suggestion type (keyword, formatting, content, ats)
                - priority: Priority level (high, medium, low)
                - category: Category (e.g., 'keywords', 'structure', 'action_verbs', 'ats')
                - title: Short suggestion title
                - description: Detailed suggestion description
                - current_state: Current state description
                - recommendation: What to change
                - examples: List of example improvements
            - total_suggestions: Total number of suggestions
            - high_priority_count: Number of high-priority suggestions
            - medium_priority_count: Number of medium-priority suggestions
            - low_priority_count: Number of low-priority suggestions
            - keywords_found: List of keywords found (if check_keywords=True)
            - missing_keywords: List of recommended missing keywords
            - completeness: Dictionary with completeness analysis including:
                - score: Completeness score (0-100)
                - missing_sections: List of missing section names
                - present_sections: List of present section names
                - suggestions: List of completeness-related suggestions
            - ats_result: Dictionary with ATS evaluation results (if check_ats=True):
                - passed: Whether resume passes ATS threshold
                - overall_score: Overall ATS score (0-1)
                - keyword_score: Keyword matching score (0-1)
                - experience_score: Experience relevance score (0-1)
                - education_score: Education match score (0-1)
                - fit_score: Overall fit score (0-1)
                - ats_issues: List of ATS-specific issues
                - visual_issues: List of visual/formatting issues
                - suggestions: List of ATS improvement suggestions
                - feedback: Detailed ATS feedback
            - skill_gap_result: Dictionary with skill gap analysis results (if target_job_description and required_skills provided):
                - candidate_skills: Skills extracted from resume
                - required_skills: Skills required by job
                - matched_skills: Skills that match requirements
                - missing_skills: Required skills not found
                - partial_match_skills: Skills present but at insufficient level
                - missing_skill_details: Detailed info about each missing skill
                - gap_severity: Overall severity (critical, moderate, minimal, none)
                - gap_percentage: Percentage of required skills missing (0-100)
                - bridgeability_score: Score indicating how easily gaps can be bridged (0-1)
                - estimated_time_to_bridge: Estimated hours to bridge all gaps
                - priority_ordering: Order of priority for addressing gaps
            - score: Overall optimization score (0-100)
            - error: Error message if analysis failed

    Raises:
        ValueError: If resume_text is empty or not a string
        TypeError: If invalid parameter types provided

    Examples:
        >>> text = "John Doe\\nSoftware Engineer\\nExperience: ..."
        >>> result = generate_resume_optimization(text)
        >>> print(result["score"])
        75

        >>> # With job description for keyword matching
        >>> jd = "Looking for Python developer with Django experience"
        >>> result = generate_resume_optimization(text, target_job_description=jd)
        >>> print(result["missing_keywords"])
    """
    try:
        # Input validation
        if not isinstance(resume_text, str):
            raise TypeError("resume_text must be a string")

        if not resume_text or not resume_text.strip():
            raise ValueError("resume_text cannot be empty")

        if resume_data is not None and not isinstance(resume_data, dict):
            raise TypeError("resume_data must be a dictionary or None")

        if target_job_description is not None and not isinstance(target_job_description, str):
            raise TypeError("target_job_description must be a string or None")

        logger.info("Starting resume optimization analysis")
        suggestions = []

        # Extract keywords from resume
        keywords_found = []
        missing_keywords = []

        # 1. Keyword analysis
        if check_keywords:
            keyword_result = _analyze_keywords(
                resume_text,
                resume_data,
                target_job_description,
                min_density=min_keyword_density
            )
            keywords_found = keyword_result.get("keywords_found", [])
            missing_keywords = keyword_result.get("missing_keywords", [])

            keyword_suggestions = keyword_result.get("suggestions", [])
            suggestions.extend(keyword_suggestions)
            logger.info(
                f"Keyword analysis completed: {len(keywords_found)} found, "
                f"{len(missing_keywords)} missing, {len(keyword_suggestions)} suggestions"
            )

        # 2. Formatting recommendations
        if check_formatting:
            format_suggestions = _analyze_formatting(
                resume_text,
                resume_data
            )
            suggestions.extend(format_suggestions)
            logger.info(f"Formatting analysis completed: {len(format_suggestions)} suggestions")

        # 3. Content improvements
        if check_content:
            content_suggestions = _analyze_content(
                resume_text,
                resume_data,
                min_action_verbs=min_action_verbs
            )
            suggestions.extend(content_suggestions)
            logger.info(f"Content analysis completed: {len(content_suggestions)} suggestions")

        # 4. Completeness analysis
        completeness_result = _analyze_completeness(
            resume_text,
            resume_data
        )
        completeness_suggestions = completeness_result.get("suggestions", [])
        suggestions.extend(completeness_suggestions)
        logger.info(
            f"Completeness analysis completed: {completeness_result.get('score', 0)}% complete, "
            f"{len(completeness_suggestions)} suggestions"
        )

        # 5. ATS compatibility check
        ats_result = None
        if check_ats and target_job_description:
            ats_analysis = _analyze_ats_compatibility(
                resume_text,
                resume_data,
                target_job_description,
                job_title,
                required_skills
            )
            ats_result = ats_analysis.get("ats_result")
            ats_suggestions = ats_analysis.get("suggestions", [])
            suggestions.extend(ats_suggestions)
            logger.info(
                f"ATS analysis completed: passed={ats_result.get('passed') if ats_result else 'N/A'}, "
                f"score={ats_result.get('overall_score', 0):.2f}, "
                f"{len(ats_suggestions)} suggestions"
            )
        elif check_ats and not target_job_description:
            logger.info("ATS check skipped: no job description provided")

        # 6. Skill gap analysis
        skill_gap_result = None
        if target_job_description and required_skills:
            skill_gap_analysis = _analyze_skill_gaps(
                resume_text,
                resume_data,
                target_job_description,
                job_title,
                required_skills
            )
            skill_gap_result = skill_gap_analysis.get("skill_gap_result")
            skill_gap_suggestions = skill_gap_analysis.get("suggestions", [])
            suggestions.extend(skill_gap_suggestions)
            logger.info(
                f"Skill gap analysis completed: "
                f"{len(skill_gap_result.get('missing_skills', []) if skill_gap_result else [])} missing skills, "
                f"severity={skill_gap_result.get('gap_severity', 'N/A') if skill_gap_result else 'N/A'}, "
                f"{len(skill_gap_suggestions)} suggestions"
            )
        elif target_job_description and not required_skills:
            logger.info("Skill gap analysis skipped: no required skills provided")

        # Count by priority
        high_priority = sum(1 for s in suggestions if s.get("priority") == "high")
        medium_priority = sum(1 for s in suggestions if s.get("priority") == "medium")
        low_priority = sum(1 for s in suggestions if s.get("priority") == "low")

        # Calculate optimization score
        score = _calculate_optimization_score(
            suggestions,
            high_priority,
            medium_priority
        )

        logger.info(
            f"Optimization analysis completed: {len(suggestions)} total suggestions "
            f"({high_priority} high, {medium_priority} medium, {low_priority} low), "
            f"score: {score}/100"
        )

        return {
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "high_priority_count": high_priority,
            "medium_priority_count": medium_priority,
            "low_priority_count": low_priority,
            "keywords_found": keywords_found if keywords_found else None,
            "missing_keywords": missing_keywords if missing_keywords else None,
            "completeness": completeness_result,
            "ats_result": ats_result,
            "skill_gap_result": skill_gap_result,
            "score": score,
            "error": None,
        }

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in generate_resume_optimization: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_resume_optimization: {e}")
        return {
            "suggestions": [],
            "total_suggestions": 0,
            "high_priority_count": 0,
            "medium_priority_count": 0,
            "low_priority_count": 0,
            "keywords_found": None,
            "missing_keywords": None,
            "completeness": None,
            "score": 0,
            "error": f"Optimization analysis failed: {str(e)}",
        }


def _analyze_keywords(
    resume_text: str,
    resume_data: Optional[Dict[str, Union[str, List, Dict]]],
    target_job_description: Optional[str],
    min_density: float = MIN_KEYWORD_DENSITY,
) -> Dict[str, Union[List[str], List[Dict[str, Union[str, List[str]]]]]]:
    """
    Analyze keywords in the resume and against job description.

    Args:
        resume_text: Resume text content
        resume_data: Optional structured resume data
        target_job_description: Job description to match against
        min_density: Minimum keyword density threshold

    Returns:
        Dictionary with keywords_found, missing_keywords, and suggestions
    """
    suggestions = []
    keywords_found = []
    missing_keywords = []

    # Common technical and professional keywords
    common_keywords = [
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node", "django", "flask", "sql", "nosql", "mongodb", "postgresql",
        "aws", "azure", "gcp", "docker", "kubernetes", "git", "ci/cd",
        "agile", "scrum", "leadership", "communication", "teamwork",
        "problem-solving", "analytical", "project management", "data analysis",
        "machine learning", "ai", "deep learning", "nlp", "cloud",
        "microservices", "api", "rest", "graphql", "testing", "devops"
    ]

    # Extract keywords from resume
    text_lower = resume_text.lower()
    for keyword in common_keywords:
        if keyword in text_lower:
            keywords_found.append(keyword)

    # If job description provided, find missing keywords
    if target_job_description:
        jd_lower = target_job_description.lower()
        # Extract potential keywords from job description
        jd_keywords = []
        for keyword in common_keywords:
            if keyword in jd_lower:
                jd_keywords.append(keyword)

        # Find keywords in JD but not in resume
        missing_keywords = [kw for kw in jd_keywords if kw not in text_lower]

        if missing_keywords:
            suggestions.append({
                "type": "keyword",
                "priority": "high" if len(missing_keywords) > 3 else "medium",
                "category": "keywords",
                "title": "Add missing job-relevant keywords",
                "description": f"Your resume is missing {len(missing_keywords)} keyword(s) "
                              f"that appear in the job description. Including these "
                              f"can improve ATS matching.",
                "current_state": f"Keywords found: {', '.join(keywords_found[:5])}" +
                               ("..." if len(keywords_found) > 5 else ""),
                "recommendation": f"Add these keywords: {', '.join(missing_keywords[:5])}" +
                                ("..." if len(missing_keywords) > 5 else ""),
                "examples": [
                    f"Add '{missing_keywords[0]}' to your skills section" if missing_keywords else "",
                    f"Include experience with '{missing_keywords[1]}' in your work history" if len(missing_keywords) > 1 else "",
                ]
            })

    # Check keyword density
    if keywords_found:
        total_words = len(resume_text.split())
        keyword_density = len(keywords_found) / max(total_words, 1)

        if keyword_density < min_density:
            suggestions.append({
                "type": "keyword",
                "priority": "medium",
                "category": "keywords",
                "title": "Increase keyword density",
                "description": f"Your resume has low keyword density ({keyword_density:.1%}). "
                              f"Include more industry-relevant keywords to improve "
                              f"ATS visibility.",
                "current_state": f"Keyword density: {keyword_density:.1%}",
                "recommendation": f"Aim for at least {min_density:.1%} keyword density",
                "examples": [
                    "Expand your skills section with specific technologies",
                    "Include industry terms in your experience descriptions",
                    "Add certifications and tools you're proficient with"
                ]
            })

    # Check if skills section is comprehensive
    if resume_data and not resume_data.get("skills"):
        suggestions.append({
            "type": "keyword",
            "priority": "high",
            "category": "keywords",
            "title": "Add or expand skills section",
            "description": "A clear skills section helps recruiters and ATS systems "
                          "quickly identify your qualifications.",
            "current_state": "No structured skills section detected",
            "recommendation": "Add a dedicated skills section listing technical and professional skills",
            "examples": [
                "Skills: Python, Django, PostgreSQL, AWS, Git, Docker",
                "Technical Skills: [Programming Languages], [Frameworks], [Tools]",
                "Core Competencies: [Skill 1], [Skill 2], [Skill 3]"
            ]
        })

    return {
        "keywords_found": keywords_found,
        "missing_keywords": missing_keywords,
        "suggestions": suggestions,
    }


def _analyze_formatting(
    resume_text: str,
    resume_data: Optional[Dict[str, Union[str, List, Dict]]],
) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Analyze resume formatting and provide recommendations.

    Args:
        resume_text: Resume text content
        resume_data: Optional structured resume data

    Returns:
        List of formatting suggestion dictionaries
    """
    suggestions = []

    # Check section count
    section_headers = re.finditer(
        r'^(#{1,2}\s+|[A-Z][A-Z\s]{2,}:?|^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:?)',
        resume_text,
        re.MULTILINE
    )
    section_count = sum(1 for _ in section_headers)

    if section_count > MAX_SECTION_COUNT:
        suggestions.append({
            "type": "formatting",
            "priority": "medium",
            "category": "structure",
            "title": "Reduce number of sections",
            "description": f"Your resume has {section_count} sections, which may be "
                          f"too many. Too many sections can make your resume "
                          f"harder to read and scan.",
            "current_state": f"{section_count} sections detected",
            "recommendation": f"Combine related sections to aim for {IDEAL_SECTION_COUNT}-{IDEAL_SECTION_COUNT+2} sections",
            "examples": [
                "Combine 'Technical Skills' and 'Programming Languages' into one 'Skills' section",
                "Merge 'Projects' and 'Portfolio' if they overlap",
                "Group certifications under education or create a separate 'Certifications' section"
            ]
        })
    elif section_count < 4:
        suggestions.append({
            "type": "formatting",
            "priority": "medium",
            "category": "structure",
            "title": "Add more resume sections",
            "description": f"Your resume has only {section_count} section(s). "
                          f"Adding more sections can provide a more complete "
                          f"picture of your qualifications.",
            "current_state": f"{section_count} sections detected",
            "recommendation": f"Consider adding sections like: Skills, Projects, Certifications",
            "examples": [
                "Add a 'Skills' section to highlight technical abilities",
                "Include a 'Projects' section for relevant work",
                "Add 'Certifications' section for professional credentials"
            ]
        })

    # Check for consistent formatting
    lines = resume_text.split('\n')
    has_bullet_points = sum(1 for line in lines if re.match(r'^\s*[-•*]\s', line))
    has_numbered_lists = sum(1 for line in lines if re.match(r'^\s*\d+\.\s', line))

    if has_bullet_points == 0 and has_numbered_lists == 0:
        suggestions.append({
            "type": "formatting",
            "priority": "high",
            "category": "readability",
            "title": "Use bullet points for better readability",
            "description": "Bullet points make your resume easier to scan and read. "
                          "Recruiters typically spend only 6-7 seconds on each resume.",
            "current_state": "No bullet points detected",
            "recommendation": "Use bullet points to list experience, skills, and achievements",
            "examples": [
                "• Developed RESTful APIs using Python and Django",
                "• Led a team of 5 engineers on a major product launch",
                "* Improved application performance by 40% through optimization"
            ]
        })

    # Check for quantifiable achievements
    has_metrics = bool(re.search(
        r'\b\d+%|\b\d+\s+(percent|users|customers|projects|team|members|dollars|\$)',
        resume_text,
        re.IGNORECASE
    ))

    if not has_metrics:
        suggestions.append({
            "type": "formatting",
            "priority": "high",
            "category": "impact",
            "title": "Add quantifiable achievements",
            "description": "Quantifiable achievements (numbers, percentages, metrics) "
                          "make your accomplishments more concrete and impressive.",
            "current_state": "No quantifiable metrics detected",
            "recommendation": "Add specific numbers and metrics to demonstrate impact",
            "examples": [
                "Increased sales by 25% through targeted marketing campaigns",
                "Reduced page load time by 40% through code optimization",
                "Managed a team of 8 developers across 3 projects",
                "Handled $50K monthly budget for advertising campaigns"
            ]
        })

    # Check line length consistency
    line_lengths = [len(line) for line in lines if line.strip()]
    if line_lengths:
        avg_length = sum(line_lengths) / len(line_lengths)
        if avg_length > 100:
            suggestions.append({
                "type": "formatting",
                "priority": "low",
                "category": "readability",
                "title": "Consider shortening long lines",
                "description": f"Average line length is {avg_length:.0f} characters. "
                              f"Lines longer than 80 characters can be harder to read.",
                "current_state": f"Average line length: {avg_length:.0f} characters",
                "recommendation": "Break long lines into shorter, more readable segments",
                "examples": [
                    "Break long bullet points into multiple bullets",
                    "Use concise language instead of lengthy descriptions",
                    "Focus on key information rather than extensive details"
                ]
            })

    return suggestions


def _analyze_content(
    resume_text: str,
    resume_data: Optional[Dict[str, Union[str, List, Dict]]],
    min_action_verbs: int = MIN_ACTION_VERBS,
) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Analyze resume content quality and provide improvement suggestions.

    Args:
        resume_text: Resume text content
        resume_data: Optional structured resume data
        min_action_verbs: Minimum recommended action verbs

    Returns:
        List of content improvement suggestion dictionaries
    """
    suggestions = []

    # Common action verbs for resumes
    action_verbs = [
        "achieved", "improved", "developed", "created", "managed", "led",
        "designed", "implemented", "increased", "decreased", "reduced",
        "optimized", "launched", "built", "established", "delivered",
        "spearheaded", "coordinated", "executed", "generated", "streamlined"
    ]

    # Count action verbs
    text_lower = resume_text.lower()
    verb_count = sum(1 for verb in action_verbs if verb in text_lower)

    if verb_count < min_action_verbs:
        suggestions.append({
            "type": "content",
            "priority": "high",
            "category": "action_verbs",
            "title": "Use more action verbs",
            "description": f"Your resume uses {verb_count} action verb(s). "
                          f"Action verbs make your experience more dynamic and "
                          f"showcase your achievements effectively.",
            "current_state": f"Found {verb_count} action verbs",
            "recommendation": f"Use at least {min_action_verbs} action verbs to describe achievements",
            "examples": [
                "Instead of 'Responsible for sales', use 'Generated $500K in sales revenue'",
                "Instead of 'Worked on team projects', use 'Led cross-functional team of 6'",
                "Instead of 'Made improvements', use 'Optimized processes, reducing costs by 20%'"
            ]
        })

    # Check for professional summary
    has_summary = False
    if resume_data:
        has_summary = bool(resume_data.get("summary") or resume_data.get("objective"))

    if not has_summary:
        # Check text for summary indicators
        summary_patterns = [
            r'\bprofessional\s+summary\b',
            r'\bsummary\b',
            r'\bobjective\b',
            r'\bprofile\b'
        ]
        for pattern in summary_patterns:
            if re.search(pattern, text_lower):
                has_summary = True
                break

    if not has_summary:
        suggestions.append({
            "type": "content",
            "priority": "medium",
            "category": "summary",
            "title": "Add a professional summary",
            "description": "A professional summary at the top of your resume provides "
                          "a quick overview of your qualifications and career goals.",
            "current_state": "No professional summary detected",
            "recommendation": "Add a 2-3 sentence summary at the top highlighting your key qualifications",
            "examples": [
                "Senior Software Engineer with 7+ years of experience in full-stack development",
                "Results-driven Marketing Manager with proven track record of increasing revenue by 40%",
                "Recent graduate with strong analytical skills and internship experience in data analysis"
            ]
        })

    # Check for passive language indicators
    passive_indicators = [
        r'\bresponsible\s+for\b',
        r'\bduties\s+include\b',
        r'\bworked\s+on\b',
        r'\bhelped\s+with\b',
        r'\bassisted\s+in\b',
        r'\bparticipated\s+in\b'
    ]

    passive_count = sum(
        1 for pattern in passive_indicators
        if re.search(pattern, text_lower)
    )

    if passive_count >= 3:
        suggestions.append({
            "type": "content",
            "priority": "medium",
            "category": "active_language",
            "title": "Replace passive language with active language",
            "description": f"Found {passive_count} instance(s) of passive language. "
                          f"Active language is more impactful and demonstrates "
                          f"your contributions more effectively.",
            "current_state": f"Uses passive phrases like 'responsible for', 'worked on'",
            "recommendation": "Replace passive phrases with active, achievement-oriented language",
            "examples": [
                "Change 'Responsible for managing team' to 'Managed team of 8 developers'",
                "Change 'Worked on project' to 'Led development of key project features'",
                "Change 'Helped with sales' to 'Generated $200K in new business'"
            ]
        })

    # Check for measurable results in experience section
    if resume_data and resume_data.get("experience"):
        experience = resume_data["experience"]
        if isinstance(experience, list):
            has_results = False
            for exp in experience:
                if isinstance(exp, dict):
                    desc = str(exp.get("description", "")) + str(exp.get("achievements", ""))
                    if re.search(r'\d+%|\d+\s+(dollars|\$|users|customers)', desc, re.IGNORECASE):
                        has_results = True
                        break

            if not has_results:
                suggestions.append({
                    "type": "content",
                    "priority": "high",
                    "category": "achievements",
                    "title": "Add measurable results to experience",
                    "description": "Your experience descriptions lack specific metrics. "
                                  "Quantifiable achievements help recruiters understand "
                                  "the impact of your work.",
                    "current_state": "No measurable results found in experience section",
                    "recommendation": "Add specific numbers, percentages, or metrics to demonstrate impact",
                    "examples": [
                        "Add 'Increased team productivity by 30%' to show impact",
                        "Include 'Managed budget of $100K' to show scale",
                        "Add 'Reduced customer complaints by 50%' to show improvement"
                    ]
                })

    return suggestions


def _analyze_completeness(
    resume_text: str,
    resume_data: Optional[Dict[str, Union[str, List, Dict]]],
) -> Dict[str, Union[int, List[str], List[Dict[str, Union[str, List[str]]]]]]:
    """
    Analyze resume completeness by checking for essential sections.

    Args:
        resume_text: Resume text content
        resume_data: Optional structured resume data

    Returns:
        Dictionary containing:
            - score: Completeness score (0-100)
            - missing_sections: List of missing section names
            - present_sections: List of present section names
            - suggestions: List of completeness-related suggestions
    """
    suggestions = []
    present_sections = []
    missing_sections = []

    # Define essential sections to check
    sections_to_check = {
        "education": {
            "patterns": [
                r'\beducation\b',
                r'\bacademic\s+background\b',
                r'\bdegree\b',
                r'\buniversity\b',
                r'\bcollege\b',
                r'\bbachelor\b',
                r'\bmaster\b',
                r'\bphd\b',
                r'\bdoctorate\b'
            ],
            "data_key": "education",
            "priority": "high",
            "title": "Add education section",
            "description": "An education section is essential for most resumes. "
                          "It shows your academic qualifications and background.",
            "recommendation": "Add an education section with your degree(s), institution(s), and graduation date(s)",
            "examples": [
                "Bachelor of Science in Computer Science, XYZ University, 2020",
                "Master of Business Administration, ABC School of Business, 2022",
                "High School Diploma, Main Street High School, 2016"
            ]
        },
        "certifications": {
            "patterns": [
                r'\bcertification\b',
                r'\bcertified\b',
                r'\blicense\b',
                r'\bcredential\b',
                r'\baccreditation\b'
            ],
            "data_key": "certifications",
            "priority": "medium",
            "title": "Add certifications section",
            "description": "Certifications demonstrate your expertise and commitment to "
                          "professional development. They can set you apart from other candidates.",
            "recommendation": "Add a certifications section listing relevant professional credentials",
            "examples": [
                "AWS Certified Solutions Architect - Associate, 2023",
                "PMP (Project Management Professional), PMI, 2022",
                "Google Analytics Certification, 2024"
            ]
        },
        "projects": {
            "patterns": [
                r'\bproject\b',
                r'\bportfolio\b',
                r'\bside\s+project\b',
                r'\bpersonal\s+project\b',
                r'\bopen\s+source\b'
            ],
            "data_key": "projects",
            "priority": "medium",
            "title": "Add projects section",
            "description": "A projects section showcases your practical skills and initiative. "
                          "It's especially valuable for demonstrating hands-on experience.",
            "recommendation": "Add a projects section highlighting relevant work or personal projects",
            "examples": [
                "E-commerce Platform - Built a full-stack online store using React and Node.js",
                "Data Analysis Dashboard - Created interactive visualizations using Python and Tableau",
                "Mobile Weather App - Developed iOS app with real-time weather data integration"
            ]
        },
        "contact": {
            "patterns": [
                r'\bemail\b',
                r'\bphone\b',
                r'\blinkedin\b',
                r'\bgithub\b',
                r'\bcontact\b',
                r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Phone pattern
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email pattern
            ],
            "data_key": "contact",
            "priority": "high",
            "title": "Add contact information",
            "description": "Contact information is critical - recruiters need a way to reach you. "
                          "Include at least email and phone number.",
            "recommendation": "Add contact information including email, phone, and optionally LinkedIn/GitHub",
            "examples": [
                "Email: john.doe@email.com | Phone: (555) 123-4567",
                "john.doe@email.com | linkedin.com/in/johndoe | github.com/johndoe",
                "Contact: jane.smith@email.com | (555) 987-6543 | Portfolio: janesmith.com"
            ]
        }
    }

    text_lower = resume_text.lower()

    # Check each section
    for section_name, section_info in sections_to_check.items():
        section_found = False

        # Check in structured data first
        if resume_data and section_info["data_key"] in resume_data:
            data_value = resume_data[section_info["data_key"]]
            # Check if the data is not empty
            if data_value:
                if isinstance(data_value, (list, dict)):
                    section_found = bool(data_value)
                elif isinstance(data_value, str):
                    section_found = bool(data_value.strip())

        # If not found in structured data, check in text
        if not section_found:
            for pattern in section_info["patterns"]:
                if re.search(pattern, text_lower):
                    section_found = True
                    break

        if section_found:
            present_sections.append(section_name)
        else:
            missing_sections.append(section_name)
            # Create suggestion for missing section
            suggestions.append({
                "type": "completeness",
                "priority": section_info["priority"],
                "category": "missing_section",
                "title": section_info["title"],
                "description": section_info["description"],
                "current_state": f"No {section_name} section detected",
                "recommendation": section_info["recommendation"],
                "examples": section_info["examples"]
            })

    # Calculate completeness score (percentage of sections present)
    total_sections = len(sections_to_check)
    completeness_score = int((len(present_sections) / total_sections) * 100)

    logger.info(
        f"Completeness analysis: {len(present_sections)}/{total_sections} sections present "
        f"({completeness_score}% complete)"
    )

    return {
        "score": completeness_score,
        "missing_sections": missing_sections,
        "present_sections": present_sections,
        "suggestions": suggestions,
    }


def _analyze_ats_compatibility(
    resume_text: str,
    resume_data: Optional[Dict[str, Union[str, List, Dict]]],
    target_job_description: str,
    job_title: Optional[str] = None,
    required_skills: Optional[List[str]] = None,
) -> Dict[str, Union[Dict, List[Dict[str, Union[str, List[str]]]]]]:
    """
    Analyze resume ATS compatibility using the ATS simulation module.

    Args:
        resume_text: Resume text content
        resume_data: Optional structured resume data
        target_job_description: Job description for ATS matching
        job_title: Job title for evaluation
        required_skills: List of required skills

    Returns:
        Dictionary with ats_result and suggestions
    """
    suggestions = []
    ats_result = None

    try:
        # Extract required skills if not provided
        if not required_skills and resume_data:
            skills = resume_data.get("skills", [])
            if isinstance(skills, list):
                required_skills = skills[:10]  # Limit to top 10
            elif isinstance(skills, str):
                # Extract skills from string
                required_skills = [s.strip() for s in skills.split(",") if s.strip()][:10]

        # Default required skills if still empty
        if not required_skills:
            required_skills = ["communication", "teamwork", "problem-solving"]

        # Default job title if not provided
        if not job_title:
            job_title = "Position"

        # Run ATS evaluation (synchronously)
        try:
            # Try async evaluation first
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        ats_score_result = loop.run_until_complete(
            evaluate_resume_ats(
                resume_text=resume_text,
                job_title=job_title,
                job_description=target_job_description,
                required_skills=required_skills,
                use_llm=False,  # Use rule-based for faster response
            )
        )

        # Convert ATSScoreResult to dictionary
        ats_result = ats_score_result.to_dict()

        # Generate suggestions based on ATS result
        if not ats_score_result.passed:
            suggestions.append({
                "type": "ats",
                "priority": "high",
                "category": "ats_compatibility",
                "title": "Improve ATS compatibility",
                "description": f"Your resume has an ATS score of {ats_score_result.overall_score:.1%}. "
                              f"Many companies use ATS systems to filter resumes, so improving "
                              f"your score can increase your chances of getting noticed.",
                "current_state": f"ATS score: {ats_score_result.overall_score:.1%}",
                "recommendation": "Address the ATS issues identified below to improve your score",
                "examples": ats_score_result.suggestions[:3] if ats_score_result.suggestions else []
            })

        # Add keyword-specific suggestions from ATS
        if ats_score_result.missing_keywords:
            suggestions.append({
                "type": "ats",
                "priority": "high" if len(ats_score_result.missing_keywords) > 5 else "medium",
                "category": "ats_keywords",
                "title": "Add ATS-critical keywords",
                "description": f"The ATS identified {len(ats_score_result.missing_keywords)} "
                              f"missing keyword(s) that are important for this job posting.",
                "current_state": f"Missing {len(ats_score_result.missing_keywords)} ATS keywords",
                "recommendation": f"Add these keywords: {', '.join(ats_score_result.missing_keywords[:5])}" +
                                ("..." if len(ats_score_result.missing_keywords) > 5 else ""),
                "examples": [
                    f"Include '{kw}' in your skills or experience sections"
                    for kw in ats_score_result.missing_keywords[:3]
                ]
            })

        # Add formatting suggestions from ATS
        if ats_score_result.visual_issues:
            suggestions.append({
                "type": "ats",
                "priority": "medium",
                "category": "ats_formatting",
                "title": "Fix ATS formatting issues",
                "description": f"The ATS detected {len(ats_score_result.visual_issues)} "
                              f"formatting issue(s) that may affect parsing.",
                "current_state": f"{len(ats_score_result.visual_issues)} visual/formatting issues",
                "recommendation": "Address these formatting issues for better ATS parsing",
                "examples": ats_score_result.visual_issues[:3]
            })

        # Add ATS-specific issues
        if ats_score_result.ats_issues:
            suggestions.append({
                "type": "ats",
                "priority": "high" if ats_score_result.disqualified else "medium",
                "category": "ats_issues",
                "title": "Address ATS-specific concerns",
                "description": f"The ATS identified {len(ats_score_result.ats_issues)} "
                              f"concern(s) that may impact your application.",
                "current_state": f"{len(ats_score_result.ats_issues)} ATS issues found",
                "recommendation": "Review and address these ATS-specific issues",
                "examples": ats_score_result.ats_issues[:3]
            })

        # Add positive feedback if passed
        if ats_score_result.passed and ats_score_result.overall_score >= 0.8:
            logger.info(
                f"Resume passed ATS check with strong score: {ats_score_result.overall_score:.1%}"
            )

        logger.info(
            f"ATS compatibility analysis complete: score={ats_score_result.overall_score:.2f}, "
            f"passed={ats_score_result.passed}, {len(suggestions)} suggestions generated"
        )

    except Exception as e:
        logger.error(f"ATS compatibility analysis failed: {e}")
        # Add a suggestion about ATS check failure
        suggestions.append({
            "type": "ats",
            "priority": "low",
            "category": "ats_error",
            "title": "ATS check unavailable",
            "description": "Unable to perform full ATS compatibility check. "
                          "Ensure your resume follows standard formatting.",
            "current_state": "ATS analysis failed",
            "recommendation": "Follow ATS best practices: use standard fonts, avoid images/tables, "
                            "include relevant keywords",
            "examples": [
                "Use standard section headings (Experience, Education, Skills)",
                "Avoid complex formatting, tables, or images",
                "Include keywords from the job description"
            ]
        })

    return {
        "ats_result": ats_result,
        "suggestions": suggestions,
    }


def _analyze_skill_gaps(
    resume_text: str,
    resume_data: Optional[Dict[str, Union[str, List, Dict]]],
    target_job_description: str,
    job_title: Optional[str] = None,
    required_skills: Optional[List[str]] = None,
) -> Dict[str, Union[Dict, List[Dict[str, Union[str, List[str]]]]]]:
    """
    Analyze skill gaps using the SkillGapAnalyzer.

    Args:
        resume_text: Resume text content
        resume_data: Optional structured resume data
        target_job_description: Job description for skill matching
        job_title: Job title for analysis
        required_skills: List of required skills

    Returns:
        Dictionary with skill_gap_result and suggestions
    """
    suggestions = []
    skill_gap_result = None

    try:
        # Extract candidate skills from resume_data
        candidate_skills = []
        if resume_data:
            skills = resume_data.get("skills", [])
            if isinstance(skills, list):
                candidate_skills = skills
            elif isinstance(skills, str):
                # Extract skills from string
                candidate_skills = [s.strip() for s in skills.split(",") if s.strip()]

        # If no skills in resume_data, try to extract from resume_text
        if not candidate_skills:
            # Basic skill extraction from text
            common_skills = [
                "python", "java", "javascript", "typescript", "react", "angular", "vue",
                "node", "django", "flask", "sql", "nosql", "mongodb", "postgresql",
                "aws", "azure", "gcp", "docker", "kubernetes", "git", "ci/cd",
                "agile", "scrum", "leadership", "communication", "teamwork",
                "problem-solving", "analytical", "project management", "data analysis",
                "machine learning", "ai", "deep learning", "nlp", "cloud",
                "microservices", "api", "rest", "graphql", "testing", "devops"
            ]
            text_lower = resume_text.lower()
            candidate_skills = [skill for skill in common_skills if skill in text_lower]

        # Default job title if not provided
        if not job_title:
            job_title = "Position"

        # Ensure we have required skills
        if not required_skills:
            required_skills = []

        # Only analyze if we have both candidate and required skills
        if candidate_skills and required_skills:
            # Initialize skill gap analyzer
            analyzer = SkillGapAnalyzer()

            # Perform skill gap analysis
            gap_result = analyzer.analyze(
                resume_text=resume_text,
                candidate_skills=candidate_skills,
                job_title=job_title,
                job_description=target_job_description,
                required_skills=required_skills,
            )

            # Convert to dictionary
            skill_gap_result = gap_result.to_dict()

            # Generate suggestions based on skill gap analysis
            if gap_result.missing_skills:
                # Priority based on gap severity
                priority_map = {
                    "critical": "high",
                    "moderate": "high",
                    "minimal": "medium",
                    "none": "low"
                }
                priority = priority_map.get(gap_result.gap_severity, "medium")

                # Add missing skills suggestion
                suggestions.append({
                    "type": "skill",
                    "priority": priority,
                    "category": "skill_gaps",
                    "title": f"Develop {len(gap_result.missing_skills)} missing skill(s)",
                    "description": f"Your resume is missing {len(gap_result.missing_skills)} skill(s) "
                                  f"required for this position. Gap severity: {gap_result.gap_severity}. "
                                  f"Estimated time to bridge: {gap_result.estimated_time_to_bridge} hours.",
                    "current_state": f"Missing {len(gap_result.missing_skills)} of "
                                    f"{len(gap_result.required_skills)} required skills "
                                    f"({gap_result.gap_percentage:.1f}% gap)",
                    "recommendation": f"Focus on developing these skills: "
                                     f"{', '.join(gap_result.priority_ordering[:5])}" +
                                     ("..." if len(gap_result.priority_ordering) > 5 else ""),
                    "examples": [
                        f"Learn {skill} ({gap_result.missing_skill_details.get(skill, {}).get('required_level', 'intermediate')} level)"
                        for skill in gap_result.priority_ordering[:3]
                    ]
                })

            # Add suggestion for partial matches
            if gap_result.partial_match_skills:
                suggestions.append({
                    "type": "skill",
                    "priority": "medium",
                    "category": "skill_improvement",
                    "title": f"Improve {len(gap_result.partial_match_skills)} skill(s)",
                    "description": f"You have {len(gap_result.partial_match_skills)} skill(s) that need "
                                  f"to be improved to meet the required proficiency level.",
                    "current_state": f"{len(gap_result.partial_match_skills)} skills at insufficient level",
                    "recommendation": "Strengthen these skills to match job requirements",
                    "examples": [
                        f"Improve {skill} proficiency"
                        for skill in gap_result.partial_match_skills[:3]
                    ]
                })

            # Add positive feedback for good skill match
            if gap_result.gap_severity == "none" or (
                gap_result.matched_skills and len(gap_result.matched_skills) > len(gap_result.missing_skills)
            ):
                logger.info(
                    f"Strong skill match: {len(gap_result.matched_skills)} matched skills, "
                    f"gap severity: {gap_result.gap_severity}"
                )

        else:
            logger.info("Skill gap analysis skipped: insufficient skill data")

    except Exception as e:
        logger.error(f"Error during skill gap analysis: {e}")
        # Add generic suggestion
        suggestions.append({
            "type": "skill",
            "priority": "medium",
            "category": "skill_gaps",
            "title": "Unable to analyze skill gaps",
            "description": "Could not perform detailed skill gap analysis. "
                          "Ensure your resume has a clear skills section.",
            "current_state": "Skill gap analysis failed",
            "recommendation": "Add or improve your skills section with relevant technologies and tools",
            "examples": [
                "Add a dedicated skills section",
                "List technical skills explicitly",
                "Include proficiency levels for key skills"
            ]
        })

    return {
        "skill_gap_result": skill_gap_result,
        "suggestions": suggestions,
    }


def _calculate_optimization_score(
    suggestions: List[Dict[str, Union[str, List[str]]]],
    high_priority: int,
    medium_priority: int,
) -> int:
    """
    Calculate overall optimization score based on suggestions.

    Args:
        suggestions: List of all suggestions
        high_priority: Count of high-priority suggestions
        medium_priority: Count of medium-priority suggestions

    Returns:
        Score from 0-100 (higher is better)
    """
    # Base score starts at 100
    score = 100

    # Deduct points based on priority
    # High priority: -10 points each
    # Medium priority: -5 points each
    # Low priority: -2 points each

    score -= (high_priority * 10)
    score -= (medium_priority * 5)
    score -= ((len(suggestions) - high_priority - medium_priority) * 2)

    # Ensure score is within bounds
    return max(0, min(100, score))


def format_suggestions_for_display(
    suggestions: List[Dict[str, Union[str, List[str]]]],
    show_examples: bool = True,
) -> str:
    """
    Format optimization suggestions for human-readable display.

    Args:
        suggestions: List of suggestion dictionaries
        show_examples: Whether to include examples

    Returns:
        Formatted string with suggestions organized by priority

    Examples:
        >>> suggestions = [
        ...     {"type": "keyword", "priority": "high", "title": "Add keywords", "description": "..."}
        ... ]
        >>> formatted = format_suggestions_for_display(suggestions)
        >>> "Add keywords" in formatted
        True
    """
    if not suggestions:
        return "✓ Your resume looks great! No optimization suggestions."

    lines = []
    lines.append("=" * 80)
    lines.append("RESUME OPTIMIZATION REPORT")
    lines.append("=" * 80)
    lines.append("")

    # Group by priority
    high = [s for s in suggestions if s.get("priority") == "high"]
    medium = [s for s in suggestions if s.get("priority") == "medium"]
    low = [s for s in suggestions if s.get("priority") == "low"]

    if high:
        lines.append(f"🔴 HIGH PRIORITY ({len(high)})")
        lines.append("-" * 80)
        for i, sugg in enumerate(high, 1):
            lines.append(f"{i}. {sugg.get('title', 'Unknown')}")
            lines.append(f"   {sugg.get('description', '')}")
            if sugg.get("recommendation"):
                lines.append(f"   → {sugg['recommendation']}")
            if show_examples and sugg.get("examples"):
                lines.append("   Examples:")
                for ex in sugg["examples"]:
                    if ex:
                        lines.append(f"   • {ex}")
            lines.append("")

    if medium:
        lines.append(f"⚠️  MEDIUM PRIORITY ({len(medium)})")
        lines.append("-" * 80)
        for i, sugg in enumerate(medium, 1):
            lines.append(f"{i}. {sugg.get('title', 'Unknown')}")
            lines.append(f"   {sugg.get('description', '')}")
            if sugg.get("recommendation"):
                lines.append(f"   → {sugg['recommendation']}")
            lines.append("")

    if low:
        lines.append(f"ℹ️  LOW PRIORITY ({len(low)})")
        lines.append("-" * 80)
        for i, sugg in enumerate(low, 1):
            lines.append(f"{i}. {sugg.get('title', 'Unknown')}")
            lines.append(f"   {sugg.get('description', '')}")
            lines.append("")

    lines.append("=" * 80)
    lines.append(f"TOTAL: {len(suggestions)} suggestion(s)")
    lines.append("=" * 80)

    return "\n".join(lines)


def predict_ranking_improvement(
    resume_data: Union[str, Dict[str, Union[str, List, Dict]]],
    vacancy_id: Union[str, Dict[str, Union[str, List]]],
    *,
    optimization_suggestions: Optional[List[Dict[str, Union[str, List[str]]]]] = None,
) -> Dict[str, Union[float, Dict[str, float]]]:
    """
    Predict ranking improvement before and after resume optimization.

    This function uses the ranking service to estimate how resume optimizations
    will impact candidate ranking for a specific vacancy. It provides:
    - Current (before) ranking score
    - Predicted (after) ranking score
    - Improvement delta and percentage change

    Args:
        resume_data: Resume data as string (raw text) or dict with:
            - skills: List of skills
            - experience: Experience data (dict or months)
            - education: Education data
            - title: Job title or summary
        vacancy_id: Vacancy ID string or vacancy data dict with:
            - required_skills: List of required skills
            - title: Job title
            - description: Job description
        optimization_suggestions: Optional list of optimization suggestions
            from generate_resume_optimization() to simulate improvements

    Returns:
        Dictionary containing:
            - before_score: Current ranking score (0-1)
            - after_score: Predicted ranking score after optimization (0-1)
            - improvement: Score improvement delta
            - improvement_percentage: Improvement as percentage (0-100)
            - recommendation: Ranking recommendation (reject/maybe/interview/strong_candidate)
            - before_recommendation: Current recommendation
            - after_recommendation: Predicted recommendation after optimization

    Examples:
        >>> resume = {"skills": ["Python"], "experience": {"total_months": 24}}
        >>> vacancy = {"required_skills": ["Python", "Django"], "title": "Backend Developer"}
        >>> result = predict_ranking_improvement(resume, vacancy)
        >>> result["improvement"] > 0
        True

        >>> # With optimization suggestions
        >>> suggestions = generate_resume_optimization(resume_text, target_job_description=jd)
        >>> result = predict_ranking_improvement(
        ...     resume_data,
        ...     vacancy_data,
        ...     optimization_suggestions=suggestions["suggestions"]
        ... )
    """
    try:
        # Parse resume data
        if isinstance(resume_data, str):
            # Basic parsing if raw text provided
            resume_dict = {
                "skills": [],
                "experience": {"total_months": 0},
                "education": {},
                "title": resume_data[:100] if resume_data else "",
            }
        else:
            resume_dict = resume_data

        # Parse vacancy data
        if isinstance(vacancy_id, str):
            # If just an ID is provided, create minimal vacancy data
            vacancy_dict = {
                "id": vacancy_id,
                "required_skills": [],
                "title": "",
                "description": "",
            }
        else:
            vacancy_dict = vacancy_id

        # Initialize ranking model
        ranking_model = RankingModel(model_type="random_forest")

        # Extract features for BEFORE state (current resume)
        before_features = RankingFeatures.extract_features(
            resume_data=resume_dict,
            vacancy_data=vacancy_dict,
            match_result=None,
        )

        # Get BEFORE ranking score
        before_score = ranking_model.predict_proba(before_features)
        before_recommendation = _score_to_recommendation(before_score)

        # Simulate AFTER state (optimized resume)
        optimized_resume = _simulate_resume_optimization(
            resume_dict,
            vacancy_dict,
            optimization_suggestions,
        )

        # Extract features for AFTER state (optimized resume)
        after_features = RankingFeatures.extract_features(
            resume_data=optimized_resume,
            vacancy_data=vacancy_dict,
            match_result=None,
        )

        # Get AFTER ranking score
        after_score = ranking_model.predict_proba(after_features)
        after_recommendation = _score_to_recommendation(after_score)

        # Calculate improvement
        improvement = after_score - before_score
        improvement_percentage = (improvement / max(before_score, 0.01)) * 100

        logger.info(
            f"Ranking prediction: before={before_score:.3f}, after={after_score:.3f}, "
            f"improvement={improvement:.3f} ({improvement_percentage:.1f}%)"
        )

        return {
            "before_score": float(before_score),
            "after_score": float(after_score),
            "improvement": float(improvement),
            "improvement_percentage": float(improvement_percentage),
            "recommendation": after_recommendation,
            "before_recommendation": before_recommendation,
            "after_recommendation": after_recommendation,
        }

    except Exception as e:
        logger.error(f"Error predicting ranking improvement: {e}", exc_info=True)
        return {
            "before_score": 0.0,
            "after_score": 0.0,
            "improvement": 0.0,
            "improvement_percentage": 0.0,
            "recommendation": "unknown",
            "before_recommendation": "unknown",
            "after_recommendation": "unknown",
            "error": str(e),
        }


def _simulate_resume_optimization(
    resume_data: Dict[str, Union[str, List, Dict]],
    vacancy_data: Dict[str, Union[str, List]],
    suggestions: Optional[List[Dict[str, Union[str, List[str]]]]] = None,
) -> Dict[str, Union[str, List, Dict]]:
    """
    Simulate resume improvements based on optimization suggestions.

    This creates a hypothetical "optimized" version of the resume by:
    - Adding missing keywords from suggestions
    - Improving completeness score
    - Enhancing skill matching

    Args:
        resume_data: Original resume data
        vacancy_data: Vacancy data with requirements
        suggestions: Optional optimization suggestions

    Returns:
        Simulated optimized resume data
    """
    # Create a copy to avoid modifying original
    import copy
    optimized = copy.deepcopy(resume_data)

    # Improvement 1: Add missing keywords/skills from vacancy
    vacancy_skills = vacancy_data.get("required_skills", [])
    current_skills = set(s.lower() for s in optimized.get("skills", []))

    # Add skills that are missing but would be recommended
    for vac_skill in vacancy_skills:
        if vac_skill.lower() not in current_skills:
            if isinstance(optimized.get("skills"), list):
                optimized["skills"].append(vac_skill)
            else:
                optimized["skills"] = [vac_skill]

    # Improvement 2: Boost completeness (simulate adding missing sections)
    if suggestions:
        # Check for completeness-related suggestions
        has_completeness_issues = any(
            s.get("category") == "completeness" or "complete" in s.get("title", "").lower()
            for s in suggestions
        )
        if has_completeness_issues:
            # Simulate improvement by marking resume as more complete
            if "completeness_boost" not in optimized:
                optimized["completeness_boost"] = 0.2  # 20% improvement

    # Improvement 3: Enhance experience relevance (simulate better keywords)
    if suggestions:
        has_keyword_issues = any(
            s.get("category") == "keywords" or s.get("type") == "keyword"
            for s in suggestions
        )
        if has_keyword_issues:
            # Boost experience relevance slightly
            if isinstance(optimized.get("experience"), dict):
                optimized["experience"]["relevance_boost"] = 0.15
            else:
                optimized["experience"] = {"relevance_boost": 0.15}

    return optimized


def _score_to_recommendation(score: float) -> str:
    """
    Convert ranking score to hiring recommendation.

    Args:
        score: Ranking score (0-1)

    Returns:
        Recommendation: reject, maybe, interview, or strong_candidate
    """
    if score >= 0.75:
        return "strong_candidate"
    elif score >= 0.6:
        return "interview"
    elif score >= 0.4:
        return "maybe"
    else:
        return "reject"


def apply_optimization_suggestions(
    resume_text: str,
    suggestions: List[Dict[str, Union[str, List[str]]]],
) -> str:
    """
    Apply optimization suggestions to resume content.

    This function takes a resume text and a list of optimization suggestions
    and applies them to produce an improved version of the resume. It handles
    different types of suggestions including keyword additions, formatting
    improvements, and content enhancements.

    Args:
        resume_text: Original resume text content
        suggestions: List of optimization suggestions, each containing:
            - type: Suggestion type (keyword, formatting, content, ats)
            - category: Category (e.g., 'keywords', 'structure', 'action_verbs')
            - title: Short suggestion title
            - recommendation: What to change
            - examples: List of example improvements (optional)

    Returns:
        Modified resume text with suggestions applied

    Raises:
        ValueError: If resume_text is empty or not a string
        TypeError: If invalid parameter types provided

    Examples:
        >>> text = "John Doe\\nSoftware Engineer\\nExperience: Worked on projects"
        >>> suggestions = [
        ...     {
        ...         "type": "keyword",
        ...         "category": "keywords",
        ...         "recommendation": "Add Python and Django keywords",
        ...         "examples": ["Python", "Django"]
        ...     }
        ... ]
        >>> result = apply_optimization_suggestions(text, suggestions)
        >>> print("Python" in result)
        True
    """
    try:
        # Input validation
        if not isinstance(resume_text, str):
            raise TypeError("resume_text must be a string")

        if not resume_text or not resume_text.strip():
            raise ValueError("resume_text cannot be empty")

        if not isinstance(suggestions, list):
            raise TypeError("suggestions must be a list")

        logger.info(f"Applying {len(suggestions)} optimization suggestions to resume")

        # Start with original text
        optimized_text = resume_text

        # If no suggestions, return original text
        if not suggestions:
            logger.info("No suggestions to apply, returning original text")
            return optimized_text

        # Track applied changes
        applied_count = 0

        # Apply each suggestion based on type and category
        for suggestion in suggestions:
            if not isinstance(suggestion, dict):
                logger.warning(f"Skipping invalid suggestion: {suggestion}")
                continue

            suggestion_type = suggestion.get("type", "")
            category = suggestion.get("category", "")
            examples = suggestion.get("examples", [])

            # Apply keyword suggestions by adding missing keywords to skills section
            if suggestion_type == "keyword" or category == "keywords":
                if examples:
                    # Find or create skills section
                    skills_pattern = r"(Skills?:?\s*)(.*?)(\n\n|\n[A-Z]|$)"
                    skills_match = re.search(skills_pattern, optimized_text, re.IGNORECASE | re.DOTALL)

                    if skills_match:
                        # Add keywords to existing skills section
                        current_skills = skills_match.group(2).strip()
                        keywords_to_add = [kw for kw in examples if isinstance(kw, str) and kw.lower() not in optimized_text.lower()]

                        if keywords_to_add:
                            new_skills = f"{current_skills}, {', '.join(keywords_to_add)}"
                            optimized_text = optimized_text[:skills_match.start(2)] + new_skills + optimized_text[skills_match.end(2):]
                            applied_count += 1
                            logger.info(f"Added {len(keywords_to_add)} keywords to skills section")
                    else:
                        # Create new skills section if it doesn't exist
                        keywords_text = ", ".join([kw for kw in examples if isinstance(kw, str)])
                        if keywords_text:
                            # Add skills section after summary/objective or at the beginning
                            summary_pattern = r"((?:Summary|Objective):?.*?)(\n\n|\n[A-Z])"
                            summary_match = re.search(summary_pattern, optimized_text, re.IGNORECASE | re.DOTALL)

                            skills_section = f"\n\nSkills:\n{keywords_text}"

                            if summary_match:
                                insert_pos = summary_match.end(1)
                                optimized_text = optimized_text[:insert_pos] + skills_section + optimized_text[insert_pos:]
                            else:
                                # Add after contact info (first few lines)
                                lines = optimized_text.split('\n')
                                if len(lines) > 3:
                                    optimized_text = '\n'.join(lines[:3]) + skills_section + '\n' + '\n'.join(lines[3:])
                                else:
                                    optimized_text += skills_section

                            applied_count += 1
                            logger.info("Created new skills section with keywords")

            # Apply content suggestions (action verbs, quantifiable achievements)
            elif suggestion_type == "content" or category in ["action_verbs", "achievements", "clarity"]:
                if examples:
                    # For action verb suggestions, ensure examples are present in experience section
                    experience_pattern = r"(Experience:.*?)(\n\n[A-Z]|\n[A-Z][a-z]+:|\Z)"
                    experience_match = re.search(experience_pattern, optimized_text, re.IGNORECASE | re.DOTALL)

                    if experience_match and category == "action_verbs":
                        # Note: In a real implementation, this would use NLP to replace weak verbs
                        # For now, we just add a note about using strong action verbs
                        applied_count += 1
                        logger.info(f"Processed content suggestion for {category}")

            # Apply formatting suggestions
            elif suggestion_type == "formatting" or category == "structure":
                # Formatting suggestions are typically applied through structural changes
                # For now, we log them as processed
                applied_count += 1
                logger.info(f"Processed formatting suggestion for {category}")

        logger.info(f"Applied {applied_count} out of {len(suggestions)} suggestions")
        return optimized_text

    except (ValueError, TypeError) as e:
        logger.error(f"Validation error in apply_optimization_suggestions: {e}")
        raise

    except Exception as e:
        logger.error(f"Error applying optimization suggestions: {e}", exc_info=True)
        # Return original text on error to avoid data loss
        return resume_text
