"""
JD Filter Suggestion Service for analyzing job descriptions and suggesting search filters.

This module provides intelligent filter suggestion capabilities that analyze
job descriptions and extract relevant search filters:
- Skill extraction using synonym matching and pattern recognition
- Experience requirements extraction (years, seniority level)
- Location requirements extraction
- Education level requirements extraction
- Language requirements extraction
- Suggested filter combinations with confidence scores
"""
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Path to skill synonyms file
SYNONYMS_FILE = Path(__file__).parent.parent / "models" / "skill_synonyms.json"

# Experience level mappings
SENIORITY_PATTERNS = {
    "entry": ["entry", "junior", "intern", "graduate", "trainee", "associate"],
    "mid": ["mid", "middle", "intermediate", "developer", "engineer"],
    "senior": ["senior", "lead", "principal", "staff", "sr.", "sr "],
    "lead": ["lead", "team lead", "tech lead", "technical lead", "engineering lead"],
    "executive": ["director", "vp", "vice president", "cto", "ceo", "c-level", "executive", "head of"],
}

# Experience years patterns
EXPERIENCE_PATTERNS = [
    # "5+ years", "5+ years of experience", "at least 5 years"
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)?",
    # "minimum of 5 years", "min 5 years"
    r"(?:minimum|min)\s+(?:of\s+)?(\d+)\s*(?:years?|yrs?)",
    # "5-7 years"
    r"(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)",
    # "5 years minimum"
    r"(\d+)\s*(?:years?|yrs?)\s*(?:minimum|min)",
]

# Education level patterns
EDUCATION_PATTERNS = {
    "phd": ["phd", "ph.d", "doctorate", "doctoral"],
    "master": ["master", "ms", "m.s", "m.sc", "mba", "m.b.a", "graduate degree"],
    "bachelor": ["bachelor", "bs", "b.s", "b.sc", "ba", "b.a", "undergraduate degree"],
    "associate": ["associate", "aa", "a.a", "a.s"],
    "certificate": ["certification", "certificate", "certified"],
}

# Common location patterns
LOCATION_INDICATORS = [
    "located in", "based in", "location:", "work from", "office in",
    "remote from", "must be in", "must live in", "position in"
]

# Language patterns
LANGUAGE_PATTERNS = [
    "fluent in", "native", "bilingual", "proficiency in", "speaks",
    "written and spoken", "language:"
]


@dataclass
class SuggestedFilter:
    """
    A suggested filter with confidence score.

    Attributes:
        filter_type: Type of filter (skills, experience, location, education, languages)
        value: The filter value
        confidence: Confidence score (0.0-1.0)
        source: Where this suggestion came from (extracted, inferred, synonym)
        original_text: Original text from JD that led to this suggestion
    """
    filter_type: str
    value: Any
    confidence: float
    source: str = "extracted"
    original_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert filter to dictionary for JSON serialization."""
        return {
            "filter_type": self.filter_type,
            "value": self.value,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "original_text": self.original_text,
        }


@dataclass
class FilterSuggestionsResult:
    """
    Result of JD filter suggestion analysis.

    Attributes:
        skills: List of suggested skill filters
        min_experience_years: Suggested minimum experience years
        max_experience_years: Suggested maximum experience years
        seniority_level: Detected seniority level
        location: Suggested location filter
        education_level: Suggested education level filter
        languages: Suggested language filters
        all_filters: Combined list of all suggested filters
        confidence: Overall confidence in the suggestions
        analysis_time_seconds: Time taken for analysis
    """
    skills: List[SuggestedFilter] = field(default_factory=list)
    min_experience_years: Optional[int] = None
    max_experience_years: Optional[int] = None
    seniority_level: Optional[str] = None
    location: Optional[SuggestedFilter] = None
    education_level: Optional[SuggestedFilter] = None
    languages: List[SuggestedFilter] = field(default_factory=list)
    all_filters: List[SuggestedFilter] = field(default_factory=list)
    confidence: float = 0.0
    analysis_time_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "skills": [s.to_dict() for s in self.skills],
            "min_experience_years": self.min_experience_years,
            "max_experience_years": self.max_experience_years,
            "seniority_level": self.seniority_level,
            "location": self.location.to_dict() if self.location else None,
            "education_level": self.education_level.to_dict() if self.education_level else None,
            "languages": [l.to_dict() for l in self.languages],
            "all_filters": [f.to_dict() for f in self.all_filters],
            "confidence": round(self.confidence, 3),
            "analysis_time_seconds": round(self.analysis_time_seconds, 3),
        }

    def to_search_filters(self) -> Dict[str, Any]:
        """
        Convert suggestions to SearchFilters-compatible dictionary.

        Returns a dictionary that can be used to construct SearchFilters
        for the search service.
        """
        filters: Dict[str, Any] = {}

        if self.skills:
            filters["skills"] = [s.value for s in self.skills]

        if self.min_experience_years is not None:
            filters["min_experience_years"] = self.min_experience_years

        if self.max_experience_years is not None:
            filters["max_experience_years"] = self.max_experience_years

        if self.location:
            filters["location"] = self.location.value

        if self.education_level:
            filters["education_level"] = self.education_level.value

        if self.languages:
            filters["languages"] = [l.value for l in self.languages]

        return filters


class JDFilterSuggester:
    """
    JD Filter Suggestion service for analyzing job descriptions.

    This service analyzes job descriptions and suggests relevant search
    filters for finding matching candidates. It uses pattern matching
    and synonym-based skill extraction.

    Example:
        >>> suggester = JDFilterSuggester()
        >>> result = suggester.suggest_filters(
        ...     job_description="Senior Python Developer with 5+ years
        ...                     experience in Django and AWS. Based in NYC."
        ... )
        >>> print([s.value for s in result.skills])
        ["Python", "Django", "AWS"]
        >>> print(result.min_experience_years)
        5
        >>> print(result.seniority_level)
        "senior"
    """

    def __init__(self, synonyms_file: Optional[Path] = None):
        """
        Initialize the JD filter suggester.

        Args:
            synonyms_file: Optional path to custom synonyms JSON file.
                          Defaults to built-in skill_synonyms.json.
        """
        self.synonyms_file = synonyms_file or SYNONYMS_FILE
        self._synonyms_map: Optional[Dict[str, List[str]]] = None
        self._category_map: Dict[str, List[str]] = {}
        self._taxonomy_map: Dict[str, Dict[str, List[str]]] = {}
        self._all_skills_lower: Dict[str, str] = {}  # lower -> canonical

    def load_synonyms(self) -> Dict[str, List[str]]:
        """
        Load skill synonyms from JSON file.

        Returns a dictionary mapping canonical skill names to lists of synonyms.

        The synonyms file structure organizes skills by category (databases,
        programming_languages, web_frameworks, etc.) with each skill having
        a canonical name and list of equivalent terms.

        Returns:
            Dictionary mapping skill names to their synonyms

        Example:
            >>> suggester = JDFilterSuggester()
            >>> synonyms = suggester.load_synonyms()
            >>> synonyms["PostgreSQL"]
            ["PostgreSQL", "Postgres", "Postgres SQL"]
        """
        if self._synonyms_map is not None:
            return self._synonyms_map

        try:
            with open(self.synonyms_file, "r", encoding="utf-8") as f:
                synonyms_data = json.load(f)

            # Flatten the category structure into a single dictionary
            flat_synonyms: Dict[str, List[str]] = {}

            for category, skills in synonyms_data.items():
                if isinstance(skills, dict):
                    for canonical_name, synonyms_list in skills.items():
                        if isinstance(synonyms_list, list):
                            # Ensure the canonical name itself is in the list
                            all_synonyms = set(synonyms_list + [canonical_name])
                            flat_synonyms[canonical_name] = list(all_synonyms)

                            # Build reverse lookup for all skill variants
                            for syn in all_synonyms:
                                self._all_skills_lower[syn.lower()] = canonical_name

                            # Also build taxonomy map by category
                            if category not in self._taxonomy_map:
                                self._taxonomy_map[category] = {}
                            self._taxonomy_map[category][canonical_name] = list(all_synonyms)

                            # Build category map for all skills in category
                            if category not in self._category_map:
                                self._category_map[category] = []
                            self._category_map[category].extend(list(all_synonyms))

                    # Deduplicate category lists
                    self._category_map[category] = list(set(self._category_map[category]))

            self._synonyms_map = flat_synonyms
            logger.info(f"Loaded {len(flat_synonyms)} skill synonym mappings for JD analysis")
            return flat_synonyms

        except FileNotFoundError:
            logger.warning(f"Skill synonyms file not found: {self.synonyms_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing skill synonyms JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading skill synonyms: {e}", exc_info=True)
            return {}

    def extract_skills(self, job_description: str) -> List[SuggestedFilter]:
        """
        Extract skills from a job description.

        Uses pattern matching and synonym lookup to identify skills
        mentioned in the job description.

        Args:
            job_description: The job description text

        Returns:
            List of suggested skill filters with confidence scores

        Example:
            >>> suggester = JDFilterSuggester()
            >>> skills = suggester.extract_skills(
            ...     "Looking for Python, React, and PostgreSQL experience"
            ... )
            >>> [s.value for s in skills]
            ["Python", "React", "PostgreSQL"]
        """
        suggestions = []
        synonyms_map = self.load_synonyms()

        if not synonyms_map:
            logger.warning("No synonyms loaded, skill extraction limited")
            return suggestions

        # Normalize text for matching
        text_lower = job_description.lower()

        # Track found skills to avoid duplicates
        found_skills: Dict[str, SuggestedFilter] = {}

        # Search for each skill in the synonyms map
        for canonical_name, synonyms_list in synonyms_map.items():
            for synonym in synonyms_list:
                # Use word boundary matching for more accuracy
                pattern = r'\b' + re.escape(synonym.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    if canonical_name not in found_skills:
                        # Calculate confidence based on synonym match quality
                        confidence = 0.95 if synonym.lower() == canonical_name.lower() else 0.85

                        found_skills[canonical_name] = SuggestedFilter(
                            filter_type="skills",
                            value=canonical_name,
                            confidence=confidence,
                            source="extracted",
                            original_text=synonym,
                        )
                    break

        # Convert to list and sort by confidence
        suggestions = list(found_skills.values())
        suggestions.sort(key=lambda x: x.confidence, reverse=True)

        logger.info(f"Extracted {len(suggestions)} skills from JD")
        return suggestions

    def extract_experience(
        self, job_description: str
    ) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """
        Extract experience requirements from a job description.

        Parses years of experience and seniority level from the text.

        Args:
            job_description: The job description text

        Returns:
            Tuple of (min_years, max_years, seniority_level)

        Example:
            >>> suggester = JDFilterSuggester()
            >>> min_yrs, max_yrs, level = suggester.extract_experience(
            ...     "Senior developer with 5-7 years experience"
            ... )
            >>> min_yrs, max_yrs, level
            (5, 7, "senior")
        """
        text_lower = job_description.lower()
        min_years: Optional[int] = None
        max_years: Optional[int] = None

        # Extract years of experience
        for pattern in EXPERIENCE_PATTERNS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 1 and groups[0]:
                    years = int(groups[0])
                    if min_years is None or years > min_years:
                        min_years = years

                    # Check for range (e.g., "5-7 years")
                    if len(groups) >= 2 and groups[1]:
                        max_years = int(groups[1])

        # Extract seniority level
        seniority_level: Optional[str] = None
        for level, patterns in SENIORITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(r'\b' + re.escape(pattern) + r'\b', text_lower):
                    seniority_level = level
                    break
            if seniority_level:
                break

        # Infer experience from seniority if not explicitly stated
        if seniority_level and min_years is None:
            inferred_years = {
                "entry": 0,
                "mid": 2,
                "senior": 5,
                "lead": 7,
                "executive": 10,
            }
            min_years = inferred_years.get(seniority_level)

        return min_years, max_years, seniority_level

    def extract_location(self, job_description: str) -> Optional[SuggestedFilter]:
        """
        Extract location requirements from a job description.

        Parses location mentions and remote work indicators.

        Args:
            job_description: The job description text

        Returns:
            Suggested location filter or None

        Example:
            >>> suggester = JDFilterSuggester()
            >>> loc = suggester.extract_location(
            ...     "Position based in New York or Remote"
            ... )
            >>> loc.value if loc else None
            "New York"
        """
        text_lower = job_description.lower()

        # Check for remote work
        if re.search(r'\bremote\b', text_lower):
            # Check if it's fully remote or hybrid
            if re.search(r'\bfully remote\b|\b100% remote\b|\bwork from home\b|\bwfh\b', text_lower):
                return SuggestedFilter(
                    filter_type="location",
                    value="Remote",
                    confidence=0.95,
                    source="extracted",
                    original_text="remote",
                )
            elif re.search(r'\bhybrid\b|\bhybrid remote\b', text_lower):
                return SuggestedFilter(
                    filter_type="location",
                    value="Hybrid",
                    confidence=0.90,
                    source="extracted",
                    original_text="hybrid",
                )

        # Look for location indicators
        for indicator in LOCATION_INDICATORS:
            pattern = re.escape(indicator) + r'\s+([A-Za-z\s,]+?)(?:\.|,|;|$|\n)'
            match = re.search(pattern, text_lower)
            if match:
                location = match.group(1).strip()
                # Clean up location
                location = re.sub(r'\s+', ' ', location)
                if len(location) > 2 and len(location) < 100:
                    # Capitalize properly
                    location = location.title()
                    return SuggestedFilter(
                        filter_type="location",
                        value=location,
                        confidence=0.80,
                        source="extracted",
                        original_text=match.group(0),
                    )

        return None

    def extract_education(self, job_description: str) -> Optional[SuggestedFilter]:
        """
        Extract education requirements from a job description.

        Parses degree requirements and education level mentions.

        Args:
            job_description: The job description text

        Returns:
            Suggested education filter or None

        Example:
            >>> suggester = JDFilterSuggester()
            >>> edu = suggester.extract_education(
            ...     "Bachelor's degree in Computer Science required"
            ... )
            >>> edu.value if edu else None
            "bachelor"
        """
        text_lower = job_description.lower()

        # Check for each education level
        for level, patterns in EDUCATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(r'\b' + re.escape(pattern) + r'\b', text_lower):
                    return SuggestedFilter(
                        filter_type="education_level",
                        value=level,
                        confidence=0.90,
                        source="extracted",
                        original_text=pattern,
                    )

        return None

    def extract_languages(self, job_description: str) -> List[SuggestedFilter]:
        """
        Extract language requirements from a job description.

        Parses language requirements and proficiency levels.

        Args:
            job_description: The job description text

        Returns:
            List of suggested language filters

        Example:
            >>> suggester = JDFilterSuggester()
            >>> langs = suggester.extract_languages(
            ...     "Must be fluent in English and Spanish"
            ... )
            >>> [l.value for l in langs]
            ["English", "Spanish"]
        """
        suggestions = []
        text_lower = job_description.lower()

        # Common language list
        common_languages = [
            "english", "spanish", "french", "german", "chinese", "japanese",
            "korean", "portuguese", "italian", "russian", "arabic", "hindi",
            "dutch", "swedish", "polish", "turkish", "vietnamese", "thai",
        ]

        # Check for language requirements
        for lang in common_languages:
            # Look for language mentioned with requirement indicators
            for indicator in LANGUAGE_PATTERNS + [""]:
                if indicator:
                    pattern = indicator + r'\s+' + re.escape(lang)
                else:
                    # Check for standalone mention with context
                    pattern = r'(?:fluent|native|proficient|speaks?)\s+(?:in\s+)?' + re.escape(lang)

                if re.search(pattern, text_lower):
                    suggestions.append(SuggestedFilter(
                        filter_type="languages",
                        value=lang.capitalize(),
                        confidence=0.85,
                        source="extracted",
                        original_text=lang,
                    ))
                    break

        return suggestions

    def suggest_filters(
        self,
        job_description: str,
        max_skills: int = 10,
        min_confidence: float = 0.5,
    ) -> FilterSuggestionsResult:
        """
        Analyze a job description and suggest search filters.

        Extracts skills, experience requirements, location, education,
        and language requirements from the job description text.

        Args:
            job_description: The job description text to analyze
            max_skills: Maximum number of skills to suggest (default: 10)
            min_confidence: Minimum confidence threshold for suggestions (default: 0.5)

        Returns:
            FilterSuggestionsResult with all suggested filters

        Example:
            >>> suggester = JDFilterSuggester()
            >>> result = suggester.suggest_filters(
            ...     job_description="Senior Python Developer with 5+ years
            ...                     experience in Django and AWS. Based in NYC.
            ...                     Bachelor's degree required."
            ... )
            >>> len(result.skills)
            3
            >>> result.min_experience_years
            5
            >>> result.seniority_level
            "senior"
        """
        import time
        start_time = time.time()

        logger.info("Starting JD filter suggestion analysis")

        try:
            # Extract all filter types
            skills = self.extract_skills(job_description)[:max_skills]
            min_years, max_years, seniority = self.extract_experience(job_description)
            location = self.extract_location(job_description)
            education = self.extract_education(job_description)
            languages = self.extract_languages(job_description)

            # Filter by confidence threshold
            skills = [s for s in skills if s.confidence >= min_confidence]
            languages = [l for l in languages if l.confidence >= min_confidence]

            # Build combined list of all filters
            all_filters: List[SuggestedFilter] = []
            all_filters.extend(skills)
            if location and location.confidence >= min_confidence:
                all_filters.append(location)
            if education and education.confidence >= min_confidence:
                all_filters.append(education)
            all_filters.extend(languages)

            # Calculate overall confidence
            if all_filters:
                confidence = sum(f.confidence for f in all_filters) / len(all_filters)
            else:
                confidence = 0.0

            # Sort by confidence
            all_filters.sort(key=lambda x: x.confidence, reverse=True)

            analysis_time = time.time() - start_time

            result = FilterSuggestionsResult(
                skills=skills,
                min_experience_years=min_years,
                max_experience_years=max_years,
                seniority_level=seniority,
                location=location,
                education_level=education,
                languages=languages,
                all_filters=all_filters,
                confidence=confidence,
                analysis_time_seconds=analysis_time,
            )

            logger.info(
                f"JD analysis completed: {len(skills)} skills, "
                f"experience: {min_years}-{max_years} years ({seniority}), "
                f"confidence: {confidence:.2f}, time: {analysis_time:.3f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Error during JD filter suggestion: {e}", exc_info=True)
            analysis_time = time.time() - start_time
            return FilterSuggestionsResult(
                analysis_time_seconds=analysis_time,
            )

    def suggest_filters_from_vacancy(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        skills: Optional[List[str]] = None,
        requirements: Optional[List[str]] = None,
    ) -> FilterSuggestionsResult:
        """
        Suggest filters from structured vacancy data.

        When vacancy data is already structured, use this method to
        generate filter suggestions without text parsing.

        Args:
            title: Job title
            description: Job description text
            skills: List of required skills
            requirements: List of additional requirements

        Returns:
            FilterSuggestionsResult with suggested filters

        Example:
            >>> suggester = JDFilterSuggester()
            >>> result = suggester.suggest_filters_from_vacancy(
            ...     title="Senior Python Developer",
            ...     skills=["Python", "Django", "PostgreSQL"],
            ...     description="5+ years experience required"
            ... )
        """
        import time
        start_time = time.time()

        # Combine all text for analysis
        all_text_parts = []
        if title:
            all_text_parts.append(title)
        if description:
            all_text_parts.append(description)
        if requirements:
            all_text_parts.extend(requirements)

        combined_text = " ".join(all_text_parts)

        # Start with basic text analysis
        result = self.suggest_filters(combined_text)

        # If skills are provided directly, use them with high confidence
        if skills:
            provided_skills = [
                SuggestedFilter(
                    filter_type="skills",
                    value=skill,
                    confidence=0.95,
                    source="provided",
                    original_text=None,
                )
                for skill in skills
            ]

            # Merge with extracted skills (provided skills take precedence)
            extracted_skill_values = {s.value.lower() for s in result.skills}
            for skill_filter in provided_skills:
                if skill_filter.value.lower() not in extracted_skill_values:
                    result.skills.append(skill_filter)

            # Update all_filters
            result.all_filters = result.skills + [
                f for f in result.all_filters
                if f.filter_type != "skills"
            ]

        # Extract seniority from title if not already detected
        if title and not result.seniority_level:
            for level, patterns in SENIORITY_PATTERNS.items():
                for pattern in patterns:
                    if pattern in title.lower():
                        result.seniority_level = level
                        break
                if result.seniority_level:
                    break

        result.analysis_time_seconds = time.time() - start_time

        return result


# Singleton instance for convenience
_suggester_instance: Optional[JDFilterSuggester] = None


def get_jd_filter_suggester() -> JDFilterSuggester:
    """
    Get or create the default JD filter suggester instance.

    Returns:
        JDFilterSuggester instance

    Example:
        >>> suggester = get_jd_filter_suggester()
        >>> result = suggester.suggest_filters("Senior Python Developer...")
    """
    global _suggester_instance
    if _suggester_instance is None:
        _suggester_instance = JDFilterSuggester()
    return _suggester_instance


def suggest_jd_filters(
    job_description: str,
    max_skills: int = 10,
    min_confidence: float = 0.5,
) -> FilterSuggestionsResult:
    """
    Convenience function to suggest filters from a job description.

    Args:
        job_description: The job description text to analyze
        max_skills: Maximum number of skills to suggest
        min_confidence: Minimum confidence threshold

    Returns:
        FilterSuggestionsResult with suggested filters

    Example:
        >>> result = suggest_jd_filters(
        ...     "Senior Python Developer with 5+ years experience"
        ... )
    """
    suggester = get_jd_filter_suggester()
    return suggester.suggest_filters(
        job_description=job_description,
        max_skills=max_skills,
        min_confidence=min_confidence,
    )
