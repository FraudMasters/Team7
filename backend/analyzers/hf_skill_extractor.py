"""
Hugging Face-based skill extraction from resume text.

This module provides functions to extract relevant skills and keywords
from resume text using pre-trained Hugging Face models, avoiding KeyBERT
and its Keras 3 compatibility issues.
"""
import logging
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Global model instances to avoid reloading on each call
_ner_pipeline = None
_ner_model_name = None
_zero_shot_pipeline = None


def _get_ner_model(model_name: str = "dslim/bert-base-NER") -> Optional:
    """
    Get or initialize the NER model from Hugging Face.

    Args:
        model_name: Name of the Hugging Face NER model to use.
            Defaults: "dslim/bert-base-NER" (reliable, well-tested)
            Alternatives: "yashpwr/resume-ner-bert-v2" (resume-specific)

    Returns:
        Initialized Hugging Face pipeline or None if loading fails
    """
    global _ner_pipeline, _ner_model_name

    if _ner_pipeline is None or _ner_model_name != model_name:
        try:
            from transformers import pipeline

            logger.info(f"Loading NER model: {model_name}")
            _ner_pipeline = pipeline(
                "ner",
                model=model_name,
                aggregation_strategy="simple",  # Merge sub-tokens
                device=-1,  # Use CPU (change to 0 for GPU)
            )
            _ner_model_name = model_name
            logger.info(f"NER model '{model_name}' loaded successfully")
        except ImportError as e:
            logger.error(f"Transformers not installed: {e}")
            logger.error("Install with: pip install transformers torch")
            _ner_pipeline = None
        except Exception as e:
            logger.error(f"Failed to load NER model '{model_name}': {e}")
            _ner_pipeline = None

    return _ner_pipeline


def _get_zero_shot_model(model_name: str = "facebook/bart-large-mnli") -> Optional:
    """
    Get or initialize the zero-shot classification model.

    Args:
        model_name: Name of the Hugging Face model for zero-shot classification

    Returns:
        Initialized Hugging Face pipeline or None if loading fails
    """
    global _zero_shot_pipeline

    if _zero_shot_pipeline is None:
        try:
            from transformers import pipeline

            logger.info(f"Loading zero-shot model: {model_name}")
            _zero_shot_pipeline = pipeline("zero-shot-classification", model=model_name)
            logger.info("Zero-shot model loaded successfully")
        except ImportError as e:
            logger.error(f"Transformers not installed: {e}")
            _zero_shot_pipeline = None
        except Exception as e:
            logger.error(f"Failed to load zero-shot model: {e}")
            _zero_shot_pipeline = None

    return _zero_shot_pipeline


def extract_skills_ner(
    text: str,
    *,
    top_n: int = 10,
    model_name: str = "dslim/bert-base-NER",
    min_score: float = 0.5,
    skill_entity_types: Optional[List[str]] = None,
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Extract skills from resume text using NER (Named Entity Recognition).

    This function uses a pre-trained NER model to identify entities in the text
    that likely represent skills, technologies, tools, or certifications.

    Args:
        text: Input text to extract skills from
        top_n: Maximum number of skills to return
        model_name: Hugging Face model name for NER
        min_score: Minimum confidence score threshold (0.0 to 1.0)
        skill_entity_types: Entity types to consider as skills.
            Defaults to ['ORG', 'PRODUCT', 'SKILL'] for generic models.
            For resume-specific models, use ['SKILL'].

    Returns:
        Dictionary containing:
            - skills: List of extracted skills (without scores)
            - skills_with_scores: List of (skill, score) tuples
            - count: Number of skills extracted
            - model: Model name used
            - error: Error message if extraction failed

    Examples:
        >>> text = "John Doe is a Python developer with experience in Django..."
        >>> result = extract_skills_ner(text, top_n=5)
        >>> print(result["skills"])
        ['Python', 'Django', 'developer']
    """
    # Default entity types that often indicate skills
    if skill_entity_types is None:
        skill_entity_types = ['ORG', 'PRODUCT', 'SKILL']

    # Validate input
    if not text or not isinstance(text, str):
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Text must be a non-empty string",
        }

    text = text.strip()
    if len(text) < 10:
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Text too short for skill extraction (min 10 chars)",
        }

    try:
        # Get or initialize model
        ner_model = _get_ner_model(model_name)

        if ner_model is None:
            return {
                "skills": None,
                "skills_with_scores": None,
                "count": 0,
                "model": model_name,
                "error": "Failed to load NER model. Install: pip install transformers torch",
            }

        # Truncate text if too long (BERT max is 512 tokens)
        max_length = 5000  # Character limit (was 1000, increased for better resume coverage)
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"Text truncated to {max_length} characters for NER")

        # Extract entities
        logger.info(f"Extracting skills using NER from text (length={len(text)})")
        entities = ner_model(text)

        # Filter entities by type and score
        skills_with_scores = []
        for entity in entities:
            entity_text = entity.get('word', '')
            entity_group = entity.get('entity_group', entity.get('entity', ''))
            score = entity.get('score', 0.0)

            # Check if this entity type should be considered a skill
            entity_type_upper = entity_group.upper()
            is_skill_type = any(
                skill_type.upper() in entity_type_upper
                for skill_type in skill_entity_types
            )

            if is_skill_type and score >= min_score:
                # Additional filtering: skills should have some technical characteristics
                if _is_likely_skill(entity_text):
                    skills_with_scores.append((entity_text, score))

        # Remove duplicates while preserving highest scores
        seen = {}
        for skill, score in skills_with_scores:
            skill_lower = skill.lower()
            if skill_lower not in seen or score > seen[skill_lower][1]:
                seen[skill_lower] = (skill, score)

        skills_with_scores = sorted(seen.values(), key=lambda x: x[1], reverse=True)

        # Limit to top_n
        skills_with_scores = skills_with_scores[:top_n]
        skills = [skill for skill, _ in skills_with_scores]

        logger.info(f"Extracted {len(skills)} skills using NER")

        return {
            "skills": skills if skills else None,
            "skills_with_scores": skills_with_scores if skills_with_scores else None,
            "count": len(skills),
            "model": model_name,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Failed to extract skills with NER: {e}")
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": f"NER extraction failed: {str(e)}",
        }


def _is_likely_skill(text: str) -> bool:
    """
    Heuristic to determine if a text fragment is likely a technical skill.

    Args:
        text: Text to evaluate

    Returns:
        True if text has characteristics of a technical skill
    """
    if not text or len(text) < 2:
        return False

    # Skills often have these characteristics
    has_uppercase = any(c.isupper() for c in text)
    has_digit = any(c.isdigit() for c in text)
    has_special_char = any(c in '.+-/#@' for c in text)
    is_multiword = ' ' in text

    # At least one characteristic should be present
    return has_uppercase or has_digit or has_special_char or is_multiword


def extract_skills_zero_shot(
    text: str,
    candidate_skills: List[str],
    *,
    top_n: int = 10,
    model_name: str = "facebook/bart-large-mnli",
    min_score: float = 0.3,
    multi_label: bool = True,
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Extract skills from resume text using zero-shot classification.

    This function uses zero-shot classification to determine which skills from
    a provided list are present in the resume text. This is useful when you have
    a predefined taxonomy of skills.

    Args:
        text: Input text (resume or job description)
        candidate_skills: List of potential skills to search for
        top_n: Maximum number of skills to return
        model_name: Hugging Face model name for zero-shot classification
        min_score: Minimum confidence score threshold (0.0 to 1.0)
        multi_label: Whether to allow multiple labels (True for skills)

    Returns:
        Dictionary containing:
            - skills: List of extracted skills (without scores)
            - skills_with_scores: List of (skill, score) tuples
            - count: Number of skills extracted
            - model: Model name used
            - error: Error message if extraction failed

    Examples:
        >>> text = "Experienced Python developer with Django and PostgreSQL knowledge"
        >>> candidates = ["Python", "Java", "Django", "React", "PostgreSQL", "MongoDB"]
        >>> result = extract_skills_zero_shot(text, candidates, top_n=3)
        >>> print(result["skills"])
        ['Python', 'Django', 'PostgreSQL']
    """
    # Validate input
    if not text or not isinstance(text, str):
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Text must be a non-empty string",
        }

    if not candidate_skills or not isinstance(candidate_skills, list):
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "candidate_skills must be a non-empty list",
        }

    text = text.strip()
    if len(text) < 10:
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Text too short for skill extraction (min 10 chars)",
        }

    try:
        # Get or initialize model
        zero_shot_model = _get_zero_shot_model(model_name)

        if zero_shot_model is None:
            return {
                "skills": None,
                "skills_with_scores": None,
                "count": 0,
                "model": model_name,
                "error": "Failed to load zero-shot model. Install: pip install transformers torch",
            }

        # Truncate text if too long
        max_length = 5000  # Character limit for zero-shot (increased from 2000)
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"Text truncated to {max_length} characters for zero-shot")

        # Run zero-shot classification
        logger.info(
            f"Running zero-shot classification with {len(candidate_skills)} candidate skills"
        )
        results = zero_shot_model(
            text,
            candidate_skills,
            multi_label=multi_label,
        )

        # Pair labels with scores and filter by threshold
        skills_with_scores = [
            (label, score)
            for label, score in zip(results["labels"], results["scores"])
            if score >= min_score
        ]

        # Sort by score (descending) and limit to top_n
        skills_with_scores = sorted(skills_with_scores, key=lambda x: x[1], reverse=True)[
            :top_n
        ]
        skills = [skill for skill, _ in skills_with_scores]

        logger.info(f"Extracted {len(skills)} skills using zero-shot classification")

        return {
            "skills": skills if skills else None,
            "skills_with_scores": skills_with_scores if skills_with_scores else None,
            "count": len(skills),
            "model": model_name,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Failed to extract skills with zero-shot: {e}")
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": f"Zero-shot extraction failed: {str(e)}",
        }


def extract_resume_skills(
    resume_text: str,
    *,
    method: str = "ner",
    candidate_skills: Optional[List[str]] = None,
    top_n: int = 10,
    **kwargs,
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Extract skills from resume text using the specified method.

    This is a convenience function that automatically selects the appropriate
    extraction method based on the parameters provided.

    Args:
        resume_text: Resume text to extract skills from
        method: Extraction method to use:
            - 'ner': Use NER model (doesn't require candidate skills)
            - 'zero-shot': Use zero-shot classification (requires candidate_skills)
            - 'hybrid': Try NER first, fallback to zero-shot if candidate_skills provided
        candidate_skills: List of candidate skills (required for zero-shot)
        top_n: Maximum number of skills to return
        **kwargs: Additional parameters passed to the extraction function

    Returns:
        Dictionary containing extracted skills and metadata

    Examples:
        >>> # Using NER (no candidate skills needed)
        >>> result = extract_resume_skills(resume_text, method='ner', top_n=10)

        >>> # Using zero-shot with predefined skill taxonomy
        >>> skills_taxonomy = ["Python", "Java", "JavaScript", "Django", "React"]
        >>> result = extract_resume_skills(
        ...     resume_text,
        ...     method='zero-shot',
        ...     candidate_skills=skills_taxonomy,
        ...     top_n=5
        ... )

        >>> # Hybrid: try NER first, use zero-shot as backup
        >>> result = extract_resume_skills(
        ...     resume_text,
        ...     method='hybrid',
        ...     candidate_skills=skills_taxonomy,
        ...     top_n=10
        ... )
    """
    if method == "ner":
        return extract_skills_ner(resume_text, top_n=top_n, **kwargs)

    elif method == "zero-shot":
        if not candidate_skills:
            return {
                "skills": None,
                "skills_with_scores": None,
                "count": 0,
                "model": "zero-shot",
                "error": "candidate_skills is required for zero-shot method",
            }
        return extract_skills_zero_shot(
            resume_text, candidate_skills, top_n=top_n, **kwargs
        )

    elif method == "hybrid":
        # Try NER first
        ner_result = extract_skills_ner(resume_text, top_n=top_n, **kwargs)

        # If NER failed and we have candidate_skills, try zero-shot
        if ner_result.get("error") and candidate_skills:
            logger.info("NER failed, trying zero-shot classification")
            return extract_skills_zero_shot(
                resume_text, candidate_skills, top_n=top_n, **kwargs
            )

        return ner_result

    else:
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "model": "none",
            "error": f"Unknown method: {method}. Use 'ner', 'zero-shot', or 'hybrid'",
        }


def extract_top_skills(
    text: str,
    top_n: int = 10,
    method: str = "ner",
    language: str = "english",
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Extract top skills from resume text (convenience function).

    This function provides a simple interface optimized for skill extraction
    from resumes. It uses NER by default, which doesn't require a predefined
    skill list.

    Args:
        text: Resume text to extract skills from
        top_n: Number of top skills to return (default: 10)
        method: Extraction method ('ner' or 'zero-shot')
        language: Document language ('english' or 'russian')
            Note: Currently only affects logging, model selection is automatic

    Returns:
        Dictionary containing:
            - skills: List of extracted skills (without scores)
            - skills_with_scores: List of (skill, score) tuples
            - count: Number of skills extracted
            - error: Error message if extraction failed

    Examples:
        >>> text = "Skills: Python, Django, PostgreSQL, Machine Learning..."
        >>> result = extract_top_skills(text, top_n=5)
        >>> print(result["skills"])
        ['Python', 'Django', 'PostgreSQL', 'Machine Learning']
    """
    logger.info(f"Extracting top {top_n} skills using {method} method (language={language})")

    result = extract_resume_skills(
        text,
        method=method,
        top_n=top_n,
    )

    return {
        "skills": result.get("skills"),
        "skills_with_scores": result.get("skills_with_scores"),
        "count": result.get("count", 0),
        "error": result.get("error"),
    }


def extract_resume_keywords(
    resume_text: str,
    language: str = "english",
    include_keyphrases: bool = True,
    method: str = "ner",
) -> Dict[str, Optional[Union[List[str], Dict[str, List[Tuple[str, float]]], str]]]:
    """
    Extract keywords optimized for resume analysis.

    This function provides a drop-in replacement for the KeyBERT-based
    extract_resume_keywords function, using Hugging Face models instead.

    Args:
        resume_text: Full resume text
        language: Document language ('english' or 'russian')
        include_keyphrases: Whether to include multi-word phrases (ignored for NER)
        method: Extraction method to use

    Returns:
        Dictionary containing:
            - single_words: List of single-word keywords with scores
            - keyphrases: List of multi-word phrases with scores
            - all_keywords: Combined list of all extracted keywords
            - error: Error message if extraction failed

    Examples:
        >>> result = extract_resume_keywords(resume_text, language="english")
        >>> print(result["all_keywords"])
        ['Python', 'Machine Learning', 'Django', 'REST API']
    """
    try:
        result = extract_resume_skills(
            resume_text,
            method=method,
            top_n=20,  # Get more to separate single words from phrases
        )

        if result.get("error"):
            return {
                "single_words": None,
                "keyphrases": None,
                "all_keywords": None,
                "error": result["error"],
            }

        skills_with_scores = result.get("skills_with_scores") or []

        # Separate single words from phrases
        single_words = [(s, score) for s, score in skills_with_scores if " " not in s]
        keyphrases = [(s, score) for s, score in skills_with_scores if " " in s]

        # Combine and deduplicate
        all_keywords = [s for s, _ in single_words] + [s for s, _ in keyphrases]

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in all_keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                unique_keywords.append(kw)

        return {
            "single_words": single_words[:15],  # Limit results
            "keyphrases": keyphrases[:10],
            "all_keywords": unique_keywords,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Resume keyword extraction failed: {e}")
        return {
            "single_words": None,
            "keyphrases": None,
            "all_keywords": None,
            "error": f"Extraction failed: {str(e)}",
        }
