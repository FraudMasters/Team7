"""
Fallback skill extractor with automatic method selection.

This module provides a unified interface that automatically tries different
extraction methods in order of preference, falling back to alternatives
when one method fails.
"""
import logging
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def extract_skills_with_fallback(
    text: str,
    *,
    top_n: int = 10,
    candidate_skills: Optional[List[str]] = None,
    preferred_method: str = "auto",
) -> Dict[str, Optional[Union[List[str], List[tuple], str]]]:
    """
    Extract skills from text with automatic fallback.

    This function tries multiple extraction methods in order:
    1. Hugging Face NER (if transformers is available)
    2. KeyBERT (if keybert is available)
    3. SpaCy NER (if available)
    4. Zero-shot classification (if candidate_skills provided)

    Args:
        text: Text to extract skills from
        top_n: Maximum number of skills to return
        candidate_skills: Optional list of candidate skills for zero-shot
        preferred_method: Preferred extraction method:
            - 'auto': Try all methods automatically (default)
            - 'ner': Use NER models only
            - 'keybert': Use KeyBERT only
            - 'zero-shot': Use zero-shot only (requires candidate_skills)
            - 'hybrid': Try NER first, then KeyBERT

    Returns:
        Dictionary with extraction results including:
            - skills: List of extracted skills
            - skills_with_scores: List of (skill, score) tuples
            - count: Number of skills extracted
            - method: Method that succeeded
            - model: Model name used
            - error: Error message if all methods failed

    Examples:
        >>> # Automatic method selection
        >>> result = extract_skills_with_fallback(resume_text, top_n=10)

        >>> # With predefined skill taxonomy
        >>> taxonomy = ["Python", "Java", "JavaScript", "Django", "React"]
        >>> result = extract_skills_with_fallback(
        ...     resume_text,
        ...     candidate_skills=taxonomy,
        ...     top_n=5
        ... )
    """
    if not text or not isinstance(text) or len(text.strip()) < 10:
        return {
            "skills": None,
            "skills_with_scores": None,
            "count": 0,
            "method": "none",
            "model": "none",
            "error": "Text must be a non-empty string with at least 10 characters",
        }

    # Track attempted methods
    attempts = []

    # Method 1: Try Hugging Face NER (recommended, no KeyBERT dependency)
    if preferred_method in ["auto", "ner", "hybrid"]:
        try:
            from .hf_skill_extractor import extract_skills_ner

            logger.info("Attempting Hugging Face NER extraction")
            result = extract_skills_ner(text, top_n=top_n)

            if not result.get("error") and result.get("skills"):
                logger.info(f"✓ Hugging Face NER succeeded: {result['count']} skills")
                return {
                    **result,
                    "method": "huggingface_ner",
                }
            else:
                attempts.append(("huggingface_ner", result.get("error", "No skills found")))
                logger.warning(f"Hugging Face NER failed: {result.get('error')}")
        except ImportError:
            attempts.append(("huggingface_ner", "Transformers not installed"))
            logger.info("Hugging Face transformers not available")
        except Exception as e:
            attempts.append(("huggingface_ner", str(e)))
            logger.warning(f"Hugging Face NER error: {e}")

    # Method 2: Try KeyBERT (original method, may have Keras issues)
    if preferred_method in ["auto", "keybert", "hybrid"]:
        try:
            from .keyword_extractor import extract_top_skills

            logger.info("Attempting KeyBERT extraction")
            result = extract_top_skills(text, top_n=top_n)

            if not result.get("error") and result.get("skills"):
                logger.info(f"✓ KeyBERT succeeded: {result['count']} skills")
                return {
                    **result,
                    "method": "keybert",
                }
            else:
                attempts.append(("keybert", result.get("error", "No skills found")))
                logger.warning(f"KeyBERT failed: {result.get('error')}")
        except ImportError:
            attempts.append(("keybert", "KeyBERT not installed"))
            logger.info("KeyBERT not available")
        except Exception as e:
            attempts.append(("keybert", str(e)))
            logger.warning(f"KeyBERT error: {e}")

    # Method 3: Try Hugging Face zero-shot (if candidate skills provided)
    if candidate_skills and preferred_method in ["auto", "zero-shot", "hybrid"]:
        try:
            from .hf_skill_extractor import extract_skills_zero_shot

            logger.info("Attempting zero-shot classification")
            result = extract_skills_zero_shot(text, candidate_skills, top_n=top_n)

            if not result.get("error") and result.get("skills"):
                logger.info(f"✓ Zero-shot succeeded: {result['count']} skills")
                return {
                    **result,
                    "method": "zero_shot",
                }
            else:
                attempts.append(("zero_shot", result.get("error", "No skills found")))
                logger.warning(f"Zero-shot failed: {result.get('error')}")
        except ImportError:
            attempts.append(("zero_shot", "Transformers not installed"))
            logger.info("Zero-shot not available")
        except Exception as e:
            attempts.append(("zero_shot", str(e)))
            logger.warning(f"Zero-shot error: {e}")

    # Method 4: Try SpaCy NER (basic fallback)
    if preferred_method in ["auto", "hybrid"]:
        try:
            from .ner_extractor import extract_entities

            logger.info("Attempting SpaCy NER extraction")
            result = extract_entities(text)

            # Filter for skill-like entities
            if result and not result.get("error"):
                entities = result.get("entities", {})
                skills = []

                # Extract organizations and products as potential skills
                for org in entities.get("organizations", [])[:top_n]:
                    skills.append((org, 0.7))  # Default score
                for product in entities.get("products", [])[: top_n // 2]:
                    skills.append((product, 0.6))

                if skills:
                    skills = skills[:top_n]
                    logger.info(f"✓ SpaCy NER succeeded: {len(skills)} skills")
                    return {
                        "skills": [s for s, _ in skills],
                        "skills_with_scores": skills,
                        "count": len(skills),
                        "method": "spacy_ner",
                        "model": "spacy",
                        "error": None,
                    }
                else:
                    attempts.append(("spacy_ner", "No skill-like entities found"))
            else:
                attempts.append(("spacy_ner", result.get("error", "Unknown error")))
        except Exception as e:
            attempts.append(("spacy_ner", str(e)))
            logger.warning(f"SpaCy NER error: {e}")

    # All methods failed
    error_msg = f"All extraction methods failed. Attempts: {attempts}"
    logger.error(error_msg)

    return {
        "skills": None,
        "skills_with_scores": None,
        "count": 0,
        "method": "none",
        "model": "none",
        "error": error_msg,
        "attempts": attempts,
    }


def extract_top_skills_auto(
    text: str,
    top_n: int = 10,
    candidate_skills: Optional[List[str]] = None,
) -> Dict[str, Optional[Union[List[str], List[tuple], str]]]:
    """
    Convenience function for automatic skill extraction.

    This is the recommended function for most use cases. It automatically
    tries different extraction methods and returns the best result.

    Args:
        text: Text to extract skills from
        top_n: Maximum number of skills to return
        candidate_skills: Optional predefined skill taxonomy

    Returns:
        Dictionary with extraction results

    Examples:
        >>> from analyzers import extract_top_skills_auto
        >>>
        >>> # Simple usage
        >>> result = extract_top_skills_auto(resume_text, top_n=10)
        >>> print(result["skills"])
        ['Python', 'Django', 'PostgreSQL']

        >>> # With predefined skills
        >>> taxonomy = ["Python", "Java", "JavaScript", "React"]
        >>> result = extract_top_skills_auto(resume_text, candidate_skills=taxonomy)
        >>> print(f"Method used: {result['method']}")
    """
    return extract_skills_with_fallback(
        text,
        top_n=top_n,
        candidate_skills=candidate_skills,
        preferred_method="auto",
    )
