"""
Keyword extraction from resume text using KeyBERT.

This module provides functions to extract relevant keywords and key phrases
from resume text using BERT-based embeddings for contextual understanding.
"""
import logging
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Global model instance to avoid reloading on each call
_kw_model: Optional["KeyBERT"] = None


def _get_model(model_name: str = "distilbert-base-nli-mean-tokens") -> "KeyBERT":
    """
    Get or initialize the KeyBERT model.

    Args:
        model_name: Name of the sentence-transformers model to use

    Returns:
        Initialized KeyBERT model instance

    Raises:
        ImportError: If keybert is not installed
        RuntimeError: If model fails to load
    """
    global _kw_model

    if _kw_model is None:
        try:
            from keybert import KeyBERT

            logger.info(f"Loading KeyBERT model: {model_name}")
            _kw_model = KeyBERT(model=model_name)
            logger.info("KeyBERT model loaded successfully")
        except ImportError as e:
            raise ImportError(
                "KeyBERT is not installed. Install it with: pip install keybert"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to load KeyBERT model: {e}") from e

    return _kw_model


def extract_keywords(
    text: str,
    *,
    keyphrase_ngram_range: Tuple[int, int] = (1, 2),
    stop_words: Union[str, List[str], None] = "english",
    top_n: int = 20,
    min_score: float = 0.0,
    use_maxsum: bool = False,
    use_mmr: bool = True,
    diversity: float = 0.5,
    model_name: str = "distilbert-base-nli-mean-tokens",
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Extract keywords from text using KeyBERT.

    KeyBERT uses BERT embeddings to find the most relevant keywords and key phrases
    in a document. It extracts candidates based on cosine similarity between the
    document and candidate keywords/phrases.

    Args:
        text: Input text to extract keywords from
        keyphrase_ngram_range: Min and max n-gram size for key phrases
            - (1, 1) for single words only
            - (1, 2) for single words and bigrams (default)
            - (2, 3) for bigrams and trigrams only
        stop_words: Stop words to remove
            - 'english' for English stop words (default)
            - 'russian' for Russian stop words
            - None to disable stop word removal
            - Custom list of stop words
        top_n: Number of top keywords to return
        min_score: Minimum similarity score threshold (0.0 to 1.0)
        use_maxsum: Whether to use Max Sum Similarity for diverse keywords
        use_mmr: Whether to use Maximal Marginal Relevance (default: True)
        diversity: MMR diversity parameter (0.0 to 1.0), higher = more diverse
        model_name: Sentence-transformers model name

    Returns:
        Dictionary containing:
            - keywords: List of extracted keywords (without scores)
            - keywords_with_scores: List of (keyword, score) tuples
            - count: Number of keywords extracted
            - model: Model name used
            - error: Error message if extraction failed

    Raises:
        ValueError: If text is empty or invalid parameters provided
        RuntimeError: If model loading or extraction fails

    Examples:
        >>> text = "John Doe is a Python developer with experience in Django..."
        >>> result = extract_keywords(text, top_n=5)
        >>> print(result["keywords"])
        ['Python', 'Django', 'developer', 'experience']
        >>> print(result["keywords_with_scores"])
        [('Python', 0.85), ('Django', 0.78), ('developer', 0.72)]

        Extract key phrases instead of single words:
        >>> result = extract_keywords(text, keyphrase_ngram_range=(2, 3), top_n=5)

        Extract from Russian text:
        >>> result = extract_keywords(russian_text, stop_words='russian')
    """
    # Validate input
    if not text or not isinstance(text, str):
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Text must be a non-empty string",
        }

    text = text.strip()
    if len(text) < 10:
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Text too short for keyword extraction (min 10 chars)",
        }

    # Validate parameters
    if not isinstance(keyphrase_ngram_range, tuple) or len(keyphrase_ngram_range) != 2:
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "keyphrase_ngram_range must be a tuple of (min, max)",
        }

    if keyphrase_ngram_range[0] < 1 or keyphrase_ngram_range[1] < keyphrase_ngram_range[0]:
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "Invalid keyphrase_ngram_range values",
        }

    if top_n < 1:
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "top_n must be at least 1",
        }

    if not 0.0 <= min_score <= 1.0:
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "min_score must be between 0.0 and 1.0",
        }

    if not 0.0 <= diversity <= 1.0:
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": "diversity must be between 0.0 and 1.0",
        }

    try:
        # Get or initialize model
        model = _get_model(model_name)

        # Extract keywords
        logger.info(
            f"Extracting keywords from text (length={len(text)}, top_n={top_n}, "
            f"ngram_range={keyphrase_ngram_range})"
        )

        keywords_with_scores = model.extract_keywords(
            text,
            keyphrase_ngram_range=keyphrase_ngram_range,
            stop_words=stop_words,
            top_n=top_n,
            min_score=min_score,
            use_maxsum=use_maxsum,
            use_mmr=use_mmr,
            diversity=diversity,
        )

        # Filter by min_score (KeyBERT doesn't always respect min_score parameter)
        if min_score > 0.0:
            keywords_with_scores = [
                (kw, score) for kw, score in keywords_with_scores if score >= min_score
            ]

        # Extract just the keywords without scores
        keywords = [kw for kw, _ in keywords_with_scores]

        logger.info(f"Extracted {len(keywords)} keywords from text")

        return {
            "keywords": keywords if keywords else None,
            "keywords_with_scores": keywords_with_scores if keywords_with_scores else None,
            "count": len(keywords),
            "model": model_name,
            "error": None,
        }

    except ImportError as e:
        logger.error(f"Import error during keyword extraction: {e}")
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": f"Import error: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Failed to extract keywords: {e}")
        return {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "model": model_name,
            "error": f"Extraction failed: {str(e)}",
        }


def extract_top_skills(
    text: str,
    top_n: int = 10,
    min_score: float = 0.3,
    language: str = "english",
) -> Dict[str, Optional[Union[List[str], List[Tuple[str, float]], str]]]:
    """
    Extract top skills from resume text using keyword extraction.

    This is a convenience function optimized for skill extraction from resumes.
    It uses bigrams and trigrams to capture multi-word skills (e.g., "machine learning",
    "natural language processing").

    Args:
        text: Resume text to extract skills from
        top_n: Number of top skills to return (default: 10)
        min_score: Minimum similarity score (default: 0.3)
        language: Language for stop words ('english' or 'russian')

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
        ['Machine Learning', 'Python', 'Django', 'PostgreSQL']
    """
    # Map language to stop words
    stop_words_map = {
        "english": "english",
        "russian": "russian",
        "en": "english",
        "ru": "russian",
    }

    stop_words = stop_words_map.get(language.lower(), "english")

    result = extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3),  # Include multi-word skills
        stop_words=stop_words,
        top_n=top_n,
        min_score=min_score,
        use_mmr=True,
        diversity=0.5,
    )

    # Adapt result format
    return {
        "skills": result.get("keywords"),
        "skills_with_scores": result.get("keywords_with_scores"),
        "count": result.get("count", 0),
        "error": result.get("error"),
    }


def extract_resume_keywords(
    resume_text: str,
    language: str = "english",
    include_keyphrases: bool = True,
) -> Dict[str, Optional[Union[List[str], Dict[str, List[Tuple[str, float]]], str]]]:
    """
    Extract keywords optimized for resume analysis.

    This function runs multiple extraction strategies to capture:
    - Single-word technical skills
    - Multi-word key phrases
    - Tools and technologies

    Args:
        resume_text: Full resume text
        language: Document language ('english' or 'russian')
        include_keyphrases: Whether to include multi-word phrases

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
        # Extract single words (unigrams)
        single_result = extract_keywords(
            resume_text,
            keyphrase_ngram_range=(1, 1),
            stop_words=language,
            top_n=15,
            min_score=0.25,
            use_mmr=True,
            diversity=0.4,
        )

        if single_result.get("error"):
            return {
                "single_words": None,
                "keyphrases": None,
                "all_keywords": None,
                "error": single_result["error"],
            }

        single_words = single_result.get("keywords_with_scores", [])

        keyphrases = []
        if include_keyphrases:
            # Extract multi-word phrases (bigrams and trigrams)
            phrase_result = extract_keywords(
                resume_text,
                keyphrase_ngram_range=(2, 3),
                stop_words=language,
                top_n=10,
                min_score=0.3,
                use_mmr=True,
                diversity=0.5,
            )

            if phrase_result.get("error"):
                logger.warning(f"Phrase extraction failed: {phrase_result['error']}")
            else:
                keyphrases = phrase_result.get("keywords_with_scores", [])

        # Combine and deduplicate
        all_keywords = [kw for kw, _ in single_words] + [
            kw for kw, _ in keyphrases
        ]

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in all_keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                unique_keywords.append(kw)

        return {
            "single_words": single_words,
            "keyphrases": keyphrases,
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
