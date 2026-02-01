"""
Resume entity extraction using SpaCy NLP.

This module provides functions to extract resume-specific entities such as
job positions, education details, age, and languages from resume text using
SpaCy's pre-trained models and custom pattern matching.
"""
import logging
import re
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Global model instances to avoid reloading on each call
_nlp_models: Dict[str, Optional["spacy.language.Language"]] = {
    "en": None,
    "ru": None,
}

# Position title patterns (English and Russian)
POSITION_PATTERNS = {
    "en": [
        r"\b(Senior|Junior|Lead|Principal|Staff|Chief)?\s*(Software|Front-?end|Back-?end|Full-?stack)?\s*(Engineer|Developer|Architect)\b",
        r"\b(Data Scientist|Machine Learning Engineer|AI Engineer|DevOps Engineer)\b",
        r"\b(Product Manager|Project Manager|Program Manager|Scrum Master)\b",
        r"\b(UI/UX Designer|Product Designer|UX Researcher|Graphic Designer)\b",
        r"\b(QA Engineer|Test Engineer|Quality Assurance Engineer|SDET)\b",
        r"\b(Business Analyst|Systems Analyst|Data Analyst)\b",
        r"\b(CTO|CFO|CEO|COO|VP|Director|Manager|Head)\b",
        r"\b(Consultant|Contractor|Freelancer)\b",
    ],
    "ru": [
        r"\b(Старший|Младший|Ведущий|Главный)?\s*(разработчик|инженер|программист)\b",
        r"\b(Front-?end|Back-?end|Full-?stack)?\s*(разработчик|инженер)\b",
        r"\b(Data Scientist|ML Engineer|DevOps-инженер)\b",
        r"\b(Менеджер|Руководитель|Директор|Начальник)\b",
        r"\b(Дизайнер|UX дизайнер|UI дизайнер)\b",
        r"\b(Аналитик|Business Analyst|System Analyst)\b",
        r"\b(Тестировщик|QA инженер)\b",
    ],
}

# Education level patterns
EDUCATION_LEVELS = {
    "en": [
        "PhD", "Doctor of Philosophy", "Doctorate",
        "Master's Degree", "Master", "M.Sc", "M.S.", "M.A.", "MBA",
        "Bachelor's Degree", "Bachelor", "B.Sc", "B.S.", "B.A.", "B.E.",
        "Associate's Degree", "Associate", "A.A.", "A.S.",
        "High School Diploma", "GED", "Certificate", "Diploma",
    ],
    "ru": [
        "PhD", "Доктор наук", "Докторская степень",
        "Магистр", "Магистерская степень", "МВА", "Master",
        "Бакалавр", "Бакалавриат", "Bachelor",
        "Аспирантура", "Аспирант",
        "Среднее образование", "Аттестат",
        "Сертификат", "Диплом",
    ],
}

# Institution type patterns
INSTITUTION_PATTERNS = {
    "en": [
        r"\b(University|College|Institute|School|Academy)\b",
        r"\b(Institute of Technology|Polytechnic)\b",
        r"\b(State University|National University)\b",
    ],
    "ru": [
        r"\b(Университет|Институт|Академия|Колледж|Школа)\b",
        r"\b(Технический университет|Политех)\b",
        r"\b(Государственный университет|Национальный университет)\b",
    ],
}

# Language patterns
LANGUAGE_PATTERNS = {
    "en": [
        (r"\b(English|Russian|Spanish|French|German|Chinese|Japanese|Korean|Portuguese|Italian|Dutch|Arabic|Hindi)\b", "language"),
        (r"\b(Native|Fluent|Proficient|Advanced|Intermediate|Basic|Beginner|Elementary)\b", "proficiency"),
    ],
    "ru": [
        (r"\b(Английский|Русский|Испанский|Французский|Немецкий|Китайский|Японский|Корейский|Португальский|Итальянский|Голландский|Арабский|Хинди)\b", "language"),
        (r"\b(Родной|Свободный|Продвинутый|Средний|Базовый|Начальный)\b", "proficiency"),
    ],
}


def _get_model(language: str = "en") -> "spacy.language.Language":
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
    global _nlp_models

    # Normalize language code
    lang_map = {
        "english": "en",
        "en": "en",
        "russian": "ru",
        "ru": "ru",
    }
    lang = lang_map.get(language.lower(), "en")

    if _nlp_models.get(lang) is None:
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
                _nlp_models[lang] = spacy.load(model_name)
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

    return _nlp_models[lang]


def extract_position(
    text: str,
    language: str = "en"
) -> Dict[str, Optional[Union[str, List[str], Tuple[int, int]]]]:
    """
    Extract job position/title from resume text.

    This function searches for job titles using pattern matching, prioritizing
    the most recent position (typically mentioned first or in a summary section).

    Args:
        text: Resume text to extract position from
        language: Document language ('en', 'english', 'ru', 'russian')

    Returns:
        Dictionary containing:
            - position: Detected position/title
            - alternatives: List of all detected positions
            - confidence: Confidence score (0-1)
            - location: Character position (start, end) if found
            - error: Error message if extraction failed

    Examples:
        >>> text = "Senior Software Engineer with 5 years of experience..."
        >>> result = extract_position(text)
        >>> print(result["position"])
        'Senior Software Engineer'

        >>> text = "Работаю ведущим разработчиком на Python..."
        >>> result = extract_position(text, language="ru")
        >>> print(result["position"])
        'ведущим разработчиком'
    """
    try:
        if not text or not isinstance(text):
            return {
                "position": None,
                "alternatives": None,
                "confidence": 0.0,
                "location": None,
                "error": "Text must be a non-empty string",
            }

        # Normalize language code
        lang = "ru" if language.lower() in ["ru", "russian"] else "en"
        patterns = POSITION_PATTERNS.get(lang, POSITION_PATTERNS["en"])

        all_positions: List[Tuple[str, Tuple[int, int]]] = []

        # Search for position patterns
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                position = match.group().strip()
                position = re.sub(r"\s+", " ", position)  # Normalize whitespace
                all_positions.append((position, (match.start(), match.end())))

        if not all_positions:
            return {
                "position": None,
                "alternatives": [],
                "confidence": 0.0,
                "location": None,
                "error": None,
            }

        # Deduplicate positions
        unique_positions = []
        seen = set()
        for pos, loc in all_positions:
            pos_lower = pos.lower()
            if pos_lower not in seen:
                seen.add(pos_lower)
                unique_positions.append((pos, loc))

        # Primary position is typically the first significant match
        primary_position, primary_location = unique_positions[0]
        alternatives = [pos for pos, _ in unique_positions]

        # Simple confidence based on position quality
        confidence = 0.9 if len(primary_position.split()) >= 2 else 0.7

        logger.info(f"Extracted position: {primary_position}")

        return {
            "position": primary_position,
            "alternatives": alternatives,
            "confidence": confidence,
            "location": primary_location,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Position extraction failed: {e}")
        return {
            "position": None,
            "alternatives": None,
            "confidence": 0.0,
            "location": None,
            "error": f"Extraction failed: {str(e)}",
        }


def extract_education(
    text: str,
    language: str = "en"
) -> Dict[str, Optional[Union[List[Dict[str, str]], str]]]:
    """
    Extract education information from resume text.

    This function extracts education level and institution names using
    pattern matching and entity recognition.

    Args:
        text: Resume text to extract education from
        language: Document language ('en', 'english', 'ru', 'russian')

    Returns:
        Dictionary containing:
            - education_entries: List of education entries with:
                - level: Degree level (Bachelor, Master, PhD, etc.)
                - institution: Institution name
                - field: Field of study (if detected)
            - highest_level: Highest education level detected
            - institutions: List of institution names
            - error: Error message if extraction failed

    Examples:
        >>> text = "Master of Science in Computer Science from Stanford University"
        >>> result = extract_education(text)
        >>> print(result["highest_level"])
        'Master of Science'

        >>> text = "Магистр технических наук, МГУ"
        >>> result = extract_education(text, language="ru")
        >>> print(result["highest_level"])
        'Магистр'
    """
    try:
        if not text or not isinstance(text):
            return {
                "education_entries": None,
                "highest_level": None,
                "institutions": None,
                "error": "Text must be a non-empty string",
            }

        # Normalize language code
        lang = "ru" if language.lower() in ["ru", "russian"] else "en"

        # Get SpaCy model for entity recognition
        nlp = _get_model(language)
        doc = nlp(text)

        # Extract education levels
        education_levels = EDUCATION_LEVELS.get(lang, EDUCATION_LEVELS["en"])
        found_levels = []

        for level in education_levels:
            if re.search(rf"\b{re.escape(level)}\b", text, re.IGNORECASE):
                found_levels.append(level)

        # Extract organizations (institutions)
        institutions = []
        for ent in doc.ents:
            if ent.label_ == "ORG":
                # Check if it's an educational institution
                inst_patterns = INSTITUTION_PATTERNS.get(lang, INSTITUTION_PATTERNS["en"])
                for pattern in inst_patterns:
                    if re.search(pattern, ent.text, re.IGNORECASE):
                        institutions.append(ent.text)
                        break

        # Determine highest level
        hierarchy = {
            "phd": 5, "doctor": 5, "doctorate": 5, "доктор": 5,
            "master": 4, "m.sc": 4, "m.s.": 4, "m.a.": 4, "mba": 4, "магистр": 4,
            "bachelor": 3, "b.sc": 3, "b.s.": 3, "b.a.": 3, "бакалавр": 3,
            "associate": 2, "ассоциат": 2,
            "high school": 1, "ged": 1, "диплом": 1, "сертификат": 1,
        }

        highest_level = None
        highest_rank = 0
        for level in found_levels:
            level_lower = level.lower()
            for key, rank in hierarchy.items():
                if key in level_lower and rank > highest_rank:
                    highest_rank = rank
                    highest_level = level

        # Build education entries
        education_entries = []
        if highest_level:
            entries = [{
                "level": highest_level,
                "institution": institutions[0] if institutions else None,
                "field": None,  # Would require more complex parsing
            }]
            education_entries = entries

        logger.info(f"Extracted education: {highest_level}, institutions: {len(institutions)}")

        return {
            "education_entries": education_entries if education_entries else None,
            "highest_level": highest_level,
            "institutions": institutions if institutions else None,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Education extraction failed: {e}")
        return {
            "education_entries": None,
            "highest_level": None,
            "institutions": None,
            "error": f"Extraction failed: {str(e)}",
        }


def extract_age(
    text: str,
    language: str = "en"
) -> Dict[str, Optional[Union[int, str]]]:
    """
    Extract age from resume text if explicitly mentioned.

    This function searches for explicit age mentions in the resume text.
    Returns None if age is not explicitly stated (no inference/guessing).

    Args:
        text: Resume text to extract age from
        language: Document language ('en', 'english', 'ru', 'russian')

    Returns:
        Dictionary containing:
            - age: Detected age as integer (None if not found)
            - mention: The actual text mentioning age
            - location: Character position (start, end) if found
            - error: Error message if extraction failed

    Examples:
        >>> text = "Age: 28 years old"
        >>> result = extract_age(text)
        >>> print(result["age"])
        28

        >>> text = "Возраст: 32 года"
        >>> result = extract_age(text, language="ru")
        >>> print(result["age"])
        32

        >>> text = "Software Engineer with 5 years experience"
        >>> result = extract_age(text)
        >>> print(result["age"])
        None
    """
    try:
        if not text or not isinstance(text):
            return {
                "age": None,
                "mention": None,
                "location": None,
                "error": "Text must be a non-empty string",
            }

        # Age extraction patterns
        age_patterns = []

        if language.lower() in ["ru", "russian"]:
            # Russian patterns: "Возраст: 28", "28 лет", "28 года"
            age_patterns.extend([
                r"(?:Возраст[:\s]*|Мне\s*)?(\d{2})\s*(?:лет|год|года)\b",
                r"(\d{2})\s*(?:лет|год|года)\s*(?:от роду|возраст)?\b",
            ])
        else:
            # English patterns: "Age: 28", "28 years old", "28-year-old"
            age_patterns.extend([
                r"(?:Age[:\s]*|aged?\s*)?(\d{2})\s*(?:years?\s?old|yo\b|\-year\-old)\b",
                r"(\d{2})\s*years?\s?old\b",
            ])

        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age_str = match.group(1)
                try:
                    age = int(age_str)
                    # Basic validation: age should be reasonable
                    if 18 <= age <= 80:
                        logger.info(f"Extracted age: {age}")
                        return {
                            "age": age,
                            "mention": match.group(0),
                            "location": (match.start(), match.end()),
                            "error": None,
                        }
                except ValueError:
                    continue

        # Age not found (this is expected - don't treat as error)
        return {
            "age": None,
            "mention": None,
            "location": None,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Age extraction failed: {e}")
        return {
            "age": None,
            "mention": None,
            "location": None,
            "error": f"Extraction failed: {str(e)}",
        }


def extract_languages(
    text: str,
    language: str = "en"
) -> Dict[str, Optional[Union[List[Dict[str, str]], str]]]:
    """
    Extract spoken languages and proficiency levels from resume text.

    This function detects language mentions and associated proficiency levels
    using pattern matching.

    Args:
        text: Resume text to extract languages from
        language: Document language ('en', 'english', 'ru', 'russian')

    Returns:
        Dictionary containing:
            - languages: List of language entries with:
                - language: Language name
                - proficiency: Proficiency level (if specified)
            - primary_language: Detected primary/resume language
            - error: Error message if extraction failed

    Examples:
        >>> text = "Languages: English (Native), Spanish (Intermediate), French (Basic)"
        >>> result = extract_languages(text)
        >>> print(result["languages"][0])
        {'language': 'English', 'proficiency': 'Native'}

        >>> text = "Знание языков: Русский (родной), Английский (B2)"
        >>> result = extract_languages(text, language="ru")
        >>> print(result["languages"])
        [{'language': 'Русский', 'proficiency': 'родной'}, {'language': 'Английский', 'proficiency': 'B2'}]
    """
    try:
        if not text or not isinstance(text):
            return {
                "languages": None,
                "primary_language": None,
                "error": "Text must be a non-empty string",
            }

        # Normalize language code
        lang = "ru" if language.lower() in ["ru", "russian"] else "en"

        # Language patterns
        lang_patterns = LANGUAGE_PATTERNS.get(lang, LANGUAGE_PATTERNS["en"])

        found_languages: List[Dict[str, str]] = []

        # Look for language sections
        lang_section_patterns = [
            r"(?:Languages?|Языки|Language Skills)[:\s]+([^.\n]+)",
            r"(?:Language proficiency|Знание языков)[:\s]+([^.\n]+)",
        ]

        lang_sections = []
        for pattern in lang_section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                lang_sections.append(match.group(1))

        # If no sections found, search entire text
        search_text = " ".join(lang_sections) if lang_sections else text

        # Extract languages and proficiencies
        for pattern_type, pattern in lang_patterns:
            matches = re.finditer(pattern, search_text, re.IGNORECASE)
            for match in matches:
                term = match.group().strip()
                if pattern_type == "language":
                    # Check if we already have this language
                    if not any(l["language"] == term for l in found_languages):
                        found_languages.append({"language": term, "proficiency": None})
                elif pattern_type == "proficiency":
                    # Associate proficiency with most recent language
                    if found_languages and found_languages[-1]["proficiency"] is None:
                        found_languages[-1]["proficiency"] = term

        # Detect primary language (language of the resume itself)
        primary_language = "Russian" if lang == "ru" else "English"

        logger.info(f"Extracted {len(found_languages)} languages")

        return {
            "languages": found_languages if found_languages else None,
            "primary_language": primary_language,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Language extraction failed: {e}")
        return {
            "languages": None,
            "primary_language": None,
            "error": f"Extraction failed: {str(e)}",
        }


def extract_resume_entities(
    resume_text: str,
    language: str = "en"
) -> Dict[str, Optional[Union[Dict, List, str]]]:
    """
    Extract all resume-specific entities from resume text.

    This is the main entry point for resume entity extraction, combining
    position, education, age, and language extraction into a single call.

    Args:
        resume_text: Full resume text to analyze
        language: Document language ('en', 'english', 'ru', 'russian')

    Returns:
        Dictionary containing:
            - position: Position extraction result
            - education: Education extraction result
            - age: Age extraction result
            - languages: Languages extraction result
            - summary: Quick summary with key fields
            - error: Error message if overall extraction failed

    Examples:
        >>> text = "John Smith\\\\nSenior Software Engineer\\\\nAge: 32"
        >>> result = extract_resume_entities(text)
        >>> result["summary"]["position"]
        'Software Engineer'

        >>> text = "Иван Петров... Разработчик Python..."
        >>> result = extract_resume_entities(text, language="ru")
        >>> print(result["summary"]["position"])
        'разработчик'
    """
    try:
        if not resume_text or not isinstance(resume_text):
            return {
                "position": None,
                "education": None,
                "age": None,
                "languages": None,
                "summary": None,
                "error": "Resume text must be a non-empty string",
            }

        resume_text = resume_text.strip()
        if len(resume_text) < 10:
            return {
                "position": None,
                "education": None,
                "age": None,
                "languages": None,
                "summary": None,
                "error": "Resume text too short for extraction (min 10 chars)",
            }

        logger.info(
            f"Extracting resume entities (length={len(resume_text)}, language={language})"
        )

        # Extract all entity types
        position_result = extract_position(resume_text, language)
        education_result = extract_education(resume_text, language)
        age_result = extract_age(resume_text, language)
        languages_result = extract_languages(resume_text, language)

        # Build summary
        summary = {
            "position": position_result.get("position"),
            "age": age_result.get("age"),
            "highest_education": education_result.get("highest_level"),
            "language_count": len(languages_result.get("languages") or []),
            "primary_language": languages_result.get("primary_language"),
        }

        # Check for errors
        errors = []
        for name, result in [
            ("position", position_result),
            ("education", education_result),
            ("age", age_result),
            ("languages", languages_result),
        ]:
            if result.get("error"):
                errors.append(f"{name}: {result['error']}")

        error_message = "; ".join(errors) if errors else None

        logger.info(f"Resume entity extraction complete: position={summary['position']}, "
                   f"age={summary['age']}, education={summary['highest_education']}")

        return {
            "position": position_result,
            "education": education_result,
            "age": age_result,
            "languages": languages_result,
            "summary": summary,
            "error": error_message,
        }

    except Exception as e:
        logger.error(f"Resume entity extraction failed: {e}")
        return {
            "position": None,
            "education": None,
            "age": None,
            "languages": None,
            "summary": None,
            "error": f"Extraction failed: {str(e)}",
        }
