"""
Named Entity Recognition (NER) extraction from resume text using SpaCy.

This module provides functions to extract named entities such as organizations,
dates, persons, locations, and custom skills from resume text using SpaCy's
pre-trained models.
"""
import logging
import re
from typing import Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)

# Global model instances to avoid reloading on each call
_nlp_models: Dict[str, Optional["spacy.language.Language"]] = {
    "en": None,
    "ru": None,
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


def extract_entities(
    text: str,
    *,
    language: str = "en",
    entity_types: Optional[Union[List[str], Set[str]]] = None,
    include_custom_skills: bool = True,
) -> Dict[str, Optional[Union[Dict[str, List[Dict[str, Union[str, int, Tuple[int, int]]]]], str]]]:
    """
    Extract named entities from resume text using SpaCy.

    This function uses SpaCy's pre-trained NER models to extract entities such as:
    - ORG: Organizations, companies, institutions
    - DATE: Dates, periods, time expressions
    - PERSON: Person names
    - GPE: Geographical and political entities (countries, cities)
    - PRODUCT: Products, apps, software
    - Custom skills from technical keywords

    Args:
        text: Input text to extract entities from
        language: Document language ('en', 'english', 'ru', 'russian')
        entity_types: List of entity types to extract (default: all standard types)
            - None or empty list extracts all standard types
            - Examples: ['ORG', 'DATE', 'PERSON'], {'ORG', 'DATE'}
        include_custom_skills: Whether to extract technical skills using pattern matching

    Returns:
        Dictionary containing:
            - entities: Dict mapping entity type to list of entities with:
                - text: Entity text
                - label: Entity type label
                - start: Character start position
                - end: Character end position
                - count: Number of times entity appears
            - skills: List of detected technical skills (if enabled)
            - total_count: Total number of entities extracted
            - language: Language code used
            - error: Error message if extraction failed

    Raises:
        ValueError: If text is empty
        RuntimeError: If model loading or extraction fails

    Examples:
        >>> text = "John Doe worked at Google from 2019 to 2022. Skills: Python, Django."
        >>> result = extract_entities(text)
        >>> print(result["entities"]["PERSON"])
        [{'text': 'John Doe', 'label': 'PERSON', 'start': 0, 'end': 8}]
        >>> print(result["entities"]["ORG"])
        [{'text': 'Google', 'label': 'ORG', 'start': 18, 'end': 24}]
        >>> print(result["entities"]["DATE"])
        [{'text': '2019', 'label': 'DATE'}, {'text': '2022', 'label': 'DATE'}]

        Extract only specific entity types:
        >>> result = extract_entities(text, entity_types=['ORG', 'DATE'])

        Extract from Russian text:
        >>> result = extract_entities(russian_text, language='ru')
    """
    # Validate input
    if not text or not isinstance(text, str):
        return {
            "entities": None,
            "skills": None,
            "total_count": 0,
            "language": language,
            "error": "Text must be a non-empty string",
        }

    text = text.strip()
    if len(text) < 5:
        return {
            "entities": None,
            "skills": None,
            "total_count": 0,
            "language": language,
            "error": "Text too short for entity extraction (min 5 chars)",
        }

    # Default entity types to extract
    if entity_types is None or len(entity_types) == 0:
        entity_types = {"ORG", "DATE", "PERSON", "GPE", "PRODUCT", "EVENT", "WORK_OF_ART"}
    elif isinstance(entity_types, list):
        entity_types = set(entity_types)

    try:
        # Get or initialize model
        nlp = _get_model(language)

        # Process text
        logger.info(
            f"Extracting entities from text (length={len(text)}, language={language}, "
            f"entity_types={entity_types})"
        )

        doc = nlp(text)

        # Extract entities by type
        entities_dict: Dict[str, List[Dict[str, Union[str, int, Tuple[int, int]]]]] = {
            et: [] for et in entity_types
        }

        entity_counter: Dict[str, int] = {}

        for ent in doc.ents:
            if ent.label_ in entity_types:
                entity_data = {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                }

                entities_dict[ent.label_].append(entity_data)

                # Count entity occurrences
                entity_key = f"{ent.label_}:{ent.text.lower()}"
                entity_counter[entity_key] = entity_counter.get(entity_key, 0) + 1

        # Add count to each entity
        for etype, entities in entities_dict.items():
            for entity in entities:
                entity_key = f"{etype}:{entity['text'].lower()}"
                entity["count"] = entity_counter.get(entity_key, 1)

        # Remove empty entity types
        entities_dict = {
            etype: entities
            for etype, entities in entities_dict.items()
            if entities
        }

        # Extract custom skills if enabled
        skills = None
        if include_custom_skills:
            skills = _extract_technical_skills(text, language)
            if skills:
                entities_dict["SKILL"] = [
                    {
                        "text": skill,
                        "label": "SKILL",
                        "start": -1,  # Pattern-based, no position
                        "end": -1,
                        "count": text.lower().count(skill.lower()),
                    }
                    for skill in skills
                ]

        # Count total entities
        total_count = sum(len(entities) for entities in entities_dict.values())

        logger.info(f"Extracted {total_count} entities from text")

        return {
            "entities": entities_dict if entities_dict else None,
            "skills": skills,
            "total_count": total_count,
            "language": language,
            "error": None,
        }

    except ImportError as e:
        logger.error(f"Import error during entity extraction: {e}")
        return {
            "entities": None,
            "skills": None,
            "total_count": 0,
            "language": language,
            "error": f"Import error: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Failed to extract entities: {e}")
        return {
            "entities": None,
            "skills": None,
            "total_count": 0,
            "language": language,
            "error": f"Extraction failed: {str(e)}",
        }


def _extract_technical_skills(
    text: str,
    language: str = "en"
) -> List[str]:
    """
    Extract technical skills using pattern matching.

    This function uses regex patterns to identify common technical skills,
    programming languages, frameworks, and tools in resume text.

    Args:
        text: Resume text to extract skills from
        language: Document language ('en' or 'ru')

    Returns:
        List of unique technical skills found in text
    """
    # Common technical skill patterns
    skill_patterns = [
        # Programming languages
        r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|Go|Rust|PHP|Ruby|Swift|Kotlin|Scala|R|MATLAB)\b',
        # Web frameworks
        r'\b(React|Angular|Vue|Django|Flask|Spring\.js|Express|Node\.js|Next\.js|Nuxt\.js)\b',
        # Databases
        r'\b(PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|SQLite|Oracle|SQL Server|Cassandra)\b',
        # Cloud platforms
        r'\b(AWS|Azure|GCP|Google Cloud|Heroku|DigitalOcean|Vercel|Netlify)\b',
        # DevOps tools
        r'\b(Docker|Kubernetes|Jenkins|GitLab CI|GitHub Actions|CircleCI|Travis CI|Terraform|Ansible)\b',
        # Tools and libraries
        r'\b(Git|GitHub|GitLab|Bitbucket|Jira|Confluence|Slack|VS Code|IntelliJ|PyCharm)\b',
        # Data science/ML
        r'\b(TensorFlow|PyTorch|Keras|Scikit-learn|Pandas|NumPy|Matplotlib|Jupyter|Tableau)\b',
        # Other common skills
        r'\b(REST API|GraphQL|gRPC|Microservices|CI/CD|TDD|Agile|Scrum|Kanban)\b',
        # Version specific
        r'\b(Java \d+|Python 3\.\d+|Node\.js \d+|React \d+)\b',
    ]

    text_lower = text.lower()
    found_skills: Set[str] = set()

    for pattern in skill_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            skill = match.group()
            # Add both original and lowercase
            found_skills.add(skill)

    # Additional skill extraction from common sections
    skill_section_patterns = [
        r'(?:Skills|Technical Skills|Technologies|Tech Stack|Stack):?\s*([^\n]+)',
        r'(?:Навыки|Технические навыки|Стек технологий):?\s*([^\n]+)',
    ]

    for pattern in skill_section_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            skills_text = match.group(1)
            # Split by common separators
            potential_skills = re.split(r'[,;·•\-\n]', skills_text)
            for skill in potential_skills:
                skill = skill.strip()
                if len(skill) > 1 and len(skill) < 50:  # Reasonable skill length
                    found_skills.add(skill)

    return sorted(list(found_skills), key=lambda x: x.lower())


def extract_organizations(
    text: str,
    language: str = "en"
) -> Dict[str, Optional[Union[List[str], str]]]:
    """
    Extract organization names from resume text.

    This is a convenience function that extracts only ORG entities,
    such as company names, institutions, and organizations.

    Args:
        text: Resume text to extract organizations from
        language: Document language ('en' or 'ru')

    Returns:
        Dictionary containing:
            - organizations: List of unique organization names
            - count: Number of organizations found
            - error: Error message if extraction failed

    Examples:
        >>> text = "Worked at Google, Microsoft, and Amazon."
        >>> result = extract_organizations(text)
        >>> print(result["organizations"])
        ['Google', 'Microsoft', 'Amazon']
    """
    result = extract_entities(
        text,
        language=language,
        entity_types=["ORG"],
        include_custom_skills=False
    )

    org_entities = result.get("entities", {}).get("ORG", [])
    organizations = list(set([org["text"] for org in org_entities]))

    return {
        "organizations": organizations if organizations else None,
        "count": len(organizations),
        "error": result.get("error"),
    }


def extract_dates(
    text: str,
    language: str = "en"
) -> Dict[str, Optional[Union[List[str], str]]]:
    """
    Extract date expressions from resume text.

    This is a convenience function that extracts only DATE entities,
    such as years, months, date ranges, and time periods.

    Args:
        text: Resume text to extract dates from
        language: Document language ('en' or 'ru')

    Returns:
        Dictionary containing:
            - dates: List of unique date expressions
            - count: Number of dates found
            - error: Error message if extraction failed

    Examples:
        >>> text = "Worked from January 2019 to December 2022"
        >>> result = extract_dates(text)
        >>> print(result["dates"])
        ['January 2019', 'December 2022']
    """
    result = extract_entities(
        text,
        language=language,
        entity_types=["DATE"],
        include_custom_skills=False
    )

    date_entities = result.get("entities", {}).get("DATE", [])
    dates = list(set([date["text"] for date in date_entities]))

    return {
        "dates": dates if dates else None,
        "count": len(dates),
        "error": result.get("error"),
    }


def extract_resume_entities(
    resume_text: str,
    language: str = "en"
) -> Dict[str, Optional[Union[Dict[str, List[Dict[str, Union[str, int, Tuple[int, int]]]]], List[str], str]]]:
    """
    Extract all relevant entities from resume text.

    This function runs entity extraction optimized for resumes, extracting:
    - Organizations (companies, institutions)
    - Dates (work periods, graduation dates)
    - Persons (references, team members)
    - Locations (work locations)
    - Technical skills

    Args:
        resume_text: Full resume text
        language: Document language ('en' or 'ru')

    Returns:
        Dictionary containing:
            - organizations: List of organization names
            - dates: List of date expressions
            - persons: List of person names
            - locations: List of geographical entities
            - skills: List of technical skills
            - all_entities: Complete entity dict with positions
            - error: Error message if extraction failed

    Examples:
        >>> result = extract_resume_entities(resume_text, language="en")
        >>> print(result["organizations"])
        ['Google', 'Microsoft']
        >>> print(result["skills"])
        ['Python', 'Django', 'PostgreSQL']
    """
    try:
        result = extract_entities(
            resume_text,
            language=language,
            entity_types=["ORG", "DATE", "PERSON", "GPE", "PRODUCT"],
            include_custom_skills=True
        )

        if result.get("error"):
            return {
                "organizations": None,
                "dates": None,
                "persons": None,
                "locations": None,
                "skills": None,
                "all_entities": None,
                "error": result["error"],
            }

        entities_dict = result.get("entities", {})

        # Extract unique entities by type
        org_list = list(set([e["text"] for e in entities_dict.get("ORG", [])]))
        date_list = list(set([e["text"] for e in entities_dict.get("DATE", [])]))
        person_list = list(set([e["text"] for e in entities_dict.get("PERSON", [])]))
        location_list = list(set([e["text"] for e in entities_dict.get("GPE", [])]))
        skill_list = result.get("skills", [])

        return {
            "organizations": org_list if org_list else None,
            "dates": date_list if date_list else None,
            "persons": person_list if person_list else None,
            "locations": location_list if location_list else None,
            "skills": skill_list if skill_list else None,
            "all_entities": entities_dict if entities_dict else None,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Resume entity extraction failed: {e}")
        return {
            "organizations": None,
            "dates": None,
            "persons": None,
            "locations": None,
            "skills": None,
            "all_entities": None,
            "error": f"Extraction failed: {str(e)}",
        }
