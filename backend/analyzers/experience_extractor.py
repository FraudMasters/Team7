"""
Work Experience extraction from resume text using NLP and pattern matching.

This module provides functions to extract structured work experience entries
from resume text, including company names, job titles, dates, and descriptions.
It uses SpaCy NER for entity extraction and pattern matching for resume structure.
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Patterns to identify work experience section headers
_EXPERIENCE_SECTION_PATTERNS = [
    r"work\s+experience",
    r"employment\s+history",
    r"professional\s+experience",
    r"work\s+history",
    r"experience",
    r"career\s+history",
    r"professional\s+background",
    # Russian patterns
    r"опыт\s+работы",
    r"трудовая\s+биография",
    r"профессиональный\s+опыт",
    r"опыт",
]

# Compiled regex for experience sections
_EXPERIENCE_SECTION_REGEX = re.compile(
    "|".join(_EXPERIENCE_SECTION_PATTERNS),
    re.IGNORECASE | re.MULTILINE
)

# Patterns for date ranges in experience entries
_DATE_RANGE_PATTERNS = [
    r"(\d{4})\s+(?:–|-|to|—)\s+(\d{4}|present|current|now)",  # YYYY - YYYY
    r"(\d{4})\s{2,}(\d{4}|present|current|now)",  # YYYY  YYYY (space-separated)
    r"(\d{4})\s+(?:–|-|to|—)\s+(\d{4}|present|current|now)",  # YYYY - YYYY
    r"(\d{1,2}/\d{4})\s*(?:–|-|to|—)\s*(\d{1,2}/\d{4}|present|current|now)",  # MM/YYYY - MM/YYYY
    r"(\d{4}-\d{2})\s*(?:–|-|to|—)\s*(\d{4}-\d{2}|present|current|now)",  # YYYY-MM - YYYY-MM
    r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\s*(?:–|-|to|—)\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|present|current|now)",
    r"(\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\s*(?:–|-|to|—)\s*((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|present|current|now)",
]

_DATE_RANGE_REGEX = re.compile(
    "|".join(_DATE_RANGE_PATTERNS),
    re.IGNORECASE
)

# Global SpaCy model cache
_nlp_model: Optional["spacy.language.Language"] = None


def _get_spacy_model(language: str = "en") -> "spacy.language.Language":
    """
    Get or initialize the SpaCy model for the specified language.

    Args:
        language: Language code ('en' for English, 'ru' for Russian)

    Returns:
        Initialized SpaCy model instance

    Raises:
        ImportError: If spaCy is not installed
        RuntimeError: If model fails to load or is not downloaded
    """
    global _nlp_model

    # Normalize language code
    lang_map = {
        "english": "en",
        "en": "en",
        "russian": "ru",
        "ru": "ru",
    }
    lang = lang_map.get(language.lower(), "en")

    if _nlp_model is None:
        try:
            import spacy

            # Model name mapping
            model_names = {
                "en": "en_core_web_sm",
                "ru": "ru_core_news_sm",
            }

            model_name = model_names.get(lang, "en_core_web_sm")

            logger.info(f"Loading SpaCy model: {model_name} for language: {lang}")

            try:
                _nlp_model = spacy.load(model_name)
            except OSError:
                raise RuntimeError(
                    f"SpaCy model '{model_name}' not found. "
                    f"Download it with: python -m spacy download {model_name}"
                )

            logger.info(f"SpaCy model {model_name} loaded successfully")

        except ImportError as e:
            raise ImportError(
                "SpaCy is not installed. Install it with: pip install spacy"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to load SpaCy model: {e}") from e

    return _nlp_model


def _identify_experience_sections(
    text: str
) -> List[Tuple[int, int]]:
    """
    Identify the start and end positions of work experience sections in resume text.

    Args:
        text: Resume text to search

    Returns:
        List of tuples (start_pos, end_pos) for each experience section found
    """
    sections = []

    # Find all experience section headers
    for match in _EXPERIENCE_SECTION_REGEX.finditer(text):
        start = match.start()

        # Find the end of this section (next section header or end of text)
        remaining_text = text[match.end():]
        next_match = _EXPERIENCE_SECTION_REGEX.search(remaining_text)

        if next_match:
            end = match.end() + next_match.start()
        else:
            end = len(text)

        sections.append((start, end))

    return sections


def _parse_experience_date(date_str: Optional[str]) -> Optional[str]:
    """
    Parse various date formats into ISO format (YYYY-MM-DD).

    Supports formats:
    - MM/YYYY
    - YYYY-MM
    - Month YYYY (e.g., "May 2020")
    - YYYY
    - "Present", "Current" (returns None)

    Args:
        date_str: Date string to parse

    Returns:
        ISO format date string (YYYY-MM-DD) or None for current positions

    Examples:
        >>> _parse_experience_date("01/2020")
        '2020-01-01'
        >>> _parse_experience_date("May 2020")
        '2020-05-01'
        >>> _parse_experience_date("present")
        None
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()

    # Check for current/present indicators
    if re.match(r"^(present|current|now|сейчас|настоящее|по настоящее время)$", date_str, re.IGNORECASE):
        return None

    # List of date formats to try
    formats = [
        "%Y-%m-%d",  # 2023-02-01
        "%Y-%m",  # 2023-02
        "%m/%Y",  # 02/2023
        "%m.%Y",  # 02.2023
        "%b %Y",  # Feb 2023
        "%B %Y",  # February 2023
        "%Y",  # 2023
    ]

    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue

    logger.warning(f"Unable to parse date: {date_str}")
    return None


def _extract_date_range(text: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Extract start and end dates from a line of text.

    Args:
        text: Text line containing date information

    Returns:
        Dictionary with 'start' and 'end' date strings, or None if no dates found
    """
    match = _DATE_RANGE_REGEX.search(text)
    if not match:
        return None

    # Extract the two date groups
    groups = match.groups()
    if len(groups) >= 2:
        start_date = _parse_experience_date(groups[0])
        end_date = _parse_experience_date(groups[1])

        return {
            "start": start_date,
            "end": end_date,
        }

    return None


def _calculate_confidence_score(
    entry: Dict[str, Optional[str]],
    has_org_entity: bool,
    has_date_entity: bool
) -> float:
    """
    Calculate confidence score for an extracted experience entry.

    The score is based on entity completeness (company, title, dates, description)
    and boosted when NER confirms entity types.

    Scoring:
    - Company: 0.3 (full), 0.15 (partial/short)
    - Title: 0.3 (full), 0.15 (partial/short)
    - Dates: 0.2 (start + end), 0.1 (start only)
    - Description: 0.2 (substantial), 0.1 (minimal)
    - NER boost: +0.05 per confirmed entity type

    Args:
        entry: Experience entry dictionary with keys: company, title, start, end, description
        has_org_entity: Whether ORG entity was found by NER
        has_date_entity: Whether DATE entity was found by NER

    Returns:
        Confidence score between 0.0 and 1.0

    Examples:
        >>> entry = {"company": "Google", "title": "Senior Engineer", "start": "2020-01-01", "end": None, "description": "Led team..."}
        >>> score = _calculate_confidence_score(entry, has_org_entity=True, has_date_entity=True)
        >>> >>> 0.85 < score < 1.0  # High confidence for complete entry with NER confirmation
        >>> entry2 = {"company": "G", "title": "Eng", "start": "2020-01-01", "end": None, "description": ""}
        >>> score2 = _calculate_confidence_score(entry2, has_org_entity=False, has_date_entity=False)
        >>> >>> 0.3 < score2 < 0.5  # Lower confidence for partial entry
    """
    score = 0.0

    # Company scoring (0.3 max)
    company = entry.get("company")
    if company:
        company_len = len(company.strip())
        if company_len > 2:
            score += 0.3  # Full points for substantial company name
        elif company_len > 0:
            score += 0.15  # Partial points for very short name

    # Title scoring (0.3 max)
    title = entry.get("title")
    if title:
        title_len = len(title.strip())
        if title_len > 2:
            score += 0.3  # Full points for substantial title
        elif title_len > 0:
            score += 0.15  # Partial points for very short title

    # Dates scoring (0.2 max)
    if entry.get("start"):
        score += 0.1  # Start date
        if entry.get("end") is not None:  # Can be None for current positions
            score += 0.1  # End date (when present)
    elif entry.get("end") is not None:
        # Has end date but no start (unusual but possible)
        score += 0.05

    # Description scoring (0.2 max)
    description = entry.get("description")
    if description:
        desc_len = len(description.strip())
        if desc_len > 50:
            score += 0.2  # Full points for substantial description
        elif desc_len > 20:
            score += 0.15  # Most points for moderate description
        elif desc_len > 0:
            score += 0.1  # Partial points for minimal description

    # NER confirmation boosts (up to 0.1 total)
    if has_org_entity:
        score += 0.05
    if has_date_entity:
        score += 0.05

    # Cap at 1.0
    return min(1.0, score)


def _extract_experience_entries(
    section_text: str,
    nlp: "spacy.language.Language"
) -> List[Dict[str, Optional[str]]]:
    """
    Extract individual experience entries from an experience section.

    Args:
        section_text: Text of a work experience section
        nlp: SpaCy NLP model

    Returns:
        List of experience entry dictionaries
    """
    entries = []

    # Split into lines and process
    lines = section_text.split("\n")
    current_entry: Dict[str, Optional[str]] = {}
    description_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            # Empty line might indicate end of an entry
            if current_entry:
                # Finalize description
                if description_lines:
                    current_entry["description"] = " ".join(description_lines).strip()

                # Only add if we have some basic info
                if current_entry.get("company") or current_entry.get("title"):
                    entries.append(current_entry)

                current_entry = {}
                description_lines = []
            continue

        # Check for date range (likely start of new entry)
        date_range = _extract_date_range(line)

        if date_range:
            # Save previous entry if exists
            if current_entry:
                if description_lines:
                    current_entry["description"] = " ".join(description_lines).strip()
                if current_entry.get("company") or current_entry.get("title"):
                    entries.append(current_entry)

            # Start new entry
            current_entry = {
                "start": date_range["start"],
                "end": date_range["end"],
            }
            description_lines = []

            # Try to extract company/title from this line
            # Use NER to identify organizations
            doc = nlp(line)
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            if orgs:
                current_entry["company"] = orgs[0]
        else:
            # Not a date line, could be title, company, or description
            doc = nlp(line)

            # Check for "Title at Company" pattern (common in functional resumes)
            if " at " in line.lower() and not current_entry.get("company") and not current_entry.get("title"):
                parts = line.split(" at ", 1)
                if len(parts) == 2:
                    potential_title = parts[0].strip()
                    potential_company = parts[1].strip()
                    # Basic validation: both parts should have reasonable length
                    if len(potential_title) > 2 and len(potential_company) > 2:
                        current_entry["title"] = potential_title
                        current_entry["company"] = potential_company
                        # Continue to next line (don't process as ORG/description)
                        continue

            # Check for organization entities
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]

            # Heuristic: if line has org and entry has no company yet, it's the company
            if orgs and not current_entry.get("company"):
                current_entry["company"] = orgs[0]

                # The rest might be the title
                line_without_org = line.replace(orgs[0], "").strip()
                if line_without_org and len(line_without_org) > 3:
                    current_entry["title"] = line_without_org
            elif not current_entry.get("title") and not current_entry.get("company"):
                # No company yet, this might be a title line
                # Look for common title patterns
                if any(word in line.lower() for word in ["senior", "junior", "lead", "manager", "engineer", "developer", "director", "analyst", "specialist"]):
                    current_entry["title"] = line
                else:
                    # Treat as description or company/title combo
                    if len(line) < 60:  # Likely title/company
                        if not current_entry.get("company"):
                            current_entry["company"] = line
                        else:
                            current_entry["title"] = line
                    else:
                        description_lines.append(line)
            else:
                # Add to description
                description_lines.append(line)

    # Don't forget the last entry
    if current_entry:
        if description_lines:
            current_entry["description"] = " ".join(description_lines).strip()
        if current_entry.get("company") or current_entry.get("title"):
            entries.append(current_entry)

    return entries


def extract_work_experience(
    text: str,
    *,
    language: str = "en",
    min_confidence: float = 0.3
) -> Dict[str, Optional[Union[List[Dict[str, Union[str, float, None]]], str]]]:
    """
    Extract structured work experience entries from resume text.

    This function uses SpaCy NER to extract organizations and dates, combined
    with pattern matching to identify experience sections and parse individual
    entries. It returns a list of experience dictionaries with company, title,
    dates, description, and confidence scores.

    Args:
        text: Resume text to extract experience from
        language: Document language ('en', 'english', 'ru', 'russian')
        min_confidence: Minimum confidence score (0-1) for entries to include

    Returns:
        Dictionary containing:
            - experiences: List of experience entry dictionaries with:
                - company: Company name (str or None)
                - title: Job title (str or None)
                - start: Start date in ISO format (str or None)
                - end: End date in ISO format (str or None) - None for current positions
                - description: Job description (str or None)
                - confidence: Confidence score (float 0-1)
            - total_count: Number of experience entries extracted
            - language: Language code used
            - error: Error message if extraction failed

    Raises:
        ValueError: If text is empty
        RuntimeError: If model loading fails

    Examples:
        >>> text = '''
        ... Work Experience
        ...
        ... Senior Software Engineer at Google
        ... 05/2020 - Present
        ... Led development of cloud infrastructure...
        ...
        ... Software Developer at Microsoft
        ... 06/2018 - 04/2020
        ... Built web applications using React...
        ... '''
        >>> result = extract_work_experience(text)
        >>> print(result["experiences"][0]["company"])
        'Google'
        >>> print(result["experiences"][0]["title"])
        'Senior Software Engineer'
        >>> print(result["experiences"][0]["start"])
        '2020-05-01'

        Extract from Russian text:
        >>> result = extract_work_experience(russian_text, language='ru')
    """
    # Validate input
    if not text or not isinstance(text, str):
        return {
            "experiences": None,
            "total_count": 0,
            "language": language,
            "error": "Text must be a non-empty string",
        }

    text = text.strip()
    if len(text) < 50:
        return {
            "experiences": None,
            "total_count": 0,
            "language": language,
            "error": "Text too short for experience extraction (min 50 chars)",
        }

    try:
        # Get SpaCy model
        nlp = _get_spacy_model(language)

        logger.info(
            f"Extracting work experience from text (length={len(text)}, language={language})"
        )

        # Identify experience sections
        sections = _identify_experience_sections(text)

        if not sections:
            # No explicit section found, try to extract from entire text
            logger.info("No experience section headers found, attempting full text extraction")
            sections = [(0, len(text))]

        all_entries = []

        # Extract entries from each section
        for start, end in sections:
            section_text = text[start:end]
            entries = _extract_experience_entries(section_text, nlp)

            # Calculate confidence scores
            for entry in entries:
                # Check if NER found entities
                entry_text = " ".join(filter(None, [
                    entry.get("company", ""),
                    entry.get("title", ""),
                    entry.get("description", "")
                ]))

                doc = nlp(entry_text)
                has_org = any(ent.label_ == "ORG" for ent in doc.ents)
                has_date = any(ent.label_ == "DATE" for ent in doc.ents)

                confidence = _calculate_confidence_score(entry, has_org, has_date)
                entry["confidence"] = confidence

            all_entries.extend(entries)

        # Filter by minimum confidence
        filtered_entries = [
            entry for entry in all_entries
            if entry.get("confidence", 0) >= min_confidence
        ]

        logger.info(f"Extracted {len(filtered_entries)} work experience entries")

        return {
            "experiences": filtered_entries if filtered_entries else None,
            "total_count": len(filtered_entries),
            "language": language,
            "error": None,
        }

    except ImportError as e:
        logger.error(f"Import error during experience extraction: {e}")
        return {
            "experiences": None,
            "total_count": 0,
            "language": language,
            "error": f"Import error: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Failed to extract work experience: {e}")
        return {
            "experiences": None,
            "total_count": 0,
            "language": language,
            "error": f"Extraction failed: {str(e)}",
        }


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


def detect_overlaps(
    experiences: List[Dict[str, Optional[str]]]
) -> Dict[str, Union[int, List[Dict]]]:
    """
    Detect overlapping work periods in experience entries.

    Args:
        experiences: List of experience entry dictionaries with start and end dates

    Returns:
        Dictionary containing:
            - overlap_count: Number of overlapping pairs found
            - overlaps: List of overlap information dictionaries
            - concurrent_periods: List of periods with concurrent positions
            - error: Error message if detection failed

    Examples:
        >>> experiences = [
        ...     {"start": "2020-01-01", "end": "2021-01-01"},
        ...     {"start": "2020-06-01", "end": "2021-06-01"},
        ... ]
        >>> result = detect_overlaps(experiences)
        >>> result["overlap_count"]
        1
    """
    try:
        if not experiences or len(experiences) < 2:
            return {
                "overlap_count": 0,
                "overlaps": [],
                "concurrent_periods": [],
                "error": None,
            }

        overlaps = []
        concurrent_periods = []

        # Convert string dates to datetime objects
        parsed_experiences = []
        for idx, exp in enumerate(experiences):
            start_str = exp.get("start")
            end_str = exp.get("end")

            if not start_str:
                continue

            try:
                start_date = datetime.fromisoformat(start_str) if start_str else None
                end_date = datetime.fromisoformat(end_str) if end_str else None
            except (ValueError, TypeError):
                continue

            parsed_experiences.append({
                "index": idx,
                "start": start_date,
                "end": end_date,
                "company": exp.get("company"),
                "title": exp.get("title"),
            })

        # Check for overlaps
        for i, exp1 in enumerate(parsed_experiences):
            for exp2 in parsed_experiences[i + 1:]:
                # Get dates (None means current)
                start1 = exp1["start"]
                end1 = exp1.get("end") or datetime.now()
                start2 = exp2["start"]
                end2 = exp2.get("end") or datetime.now()

                # Check overlap using helper function
                if _dates_overlap(start1, exp1.get("end"), start2, exp2.get("end")):
                    # Calculate overlap period
                    latest_start = max(start1, start2)
                    earliest_end = min(end1, end2)

                    overlap_info = {
                        "entry1": {
                            "index": exp1["index"],
                            "company": exp1.get("company"),
                            "title": exp1.get("title"),
                            "start": exp1["start"].isoformat(),
                            "end": exp1.get("end").isoformat() if exp1.get("end") else None,
                        },
                        "entry2": {
                            "index": exp2["index"],
                            "company": exp2.get("company"),
                            "title": exp2.get("title"),
                            "start": exp2["start"].isoformat(),
                            "end": exp2.get("end").isoformat() if exp2.get("end") else None,
                        },
                        "overlap_start": latest_start.isoformat(),
                        "overlap_end": earliest_end.isoformat(),
                    }
                    overlaps.append(overlap_info)

                    # Check if this represents concurrent positions (different companies)
                    if exp1.get("company") and exp2.get("company"):
                        if exp1.get("company") != exp2.get("company"):
                            concurrent_periods.append(overlap_info)

        return {
            "overlap_count": len(overlaps),
            "overlaps": overlaps,
            "concurrent_periods": concurrent_periods,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Failed to detect overlaps: {e}")
        return {
            "overlap_count": 0,
            "overlaps": [],
            "concurrent_periods": [],
            "error": str(e),
        }
