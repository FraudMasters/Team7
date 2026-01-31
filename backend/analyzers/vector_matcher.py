"""
Vector similarity matcher using sentence-transformers.

This module provides semantic similarity matching between resumes and job postings
using sentence embeddings from the sentence-transformers library.

Key features:
- Semantic similarity beyond keyword matching
- Context-aware matching (e.g., "JS developer" ≈ "JavaScript programmer")
- Cosine similarity scoring
- Cached model loading for performance
"""
import logging
from dataclasses import dataclass
from typing import List, Optional

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    _HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None  # type: ignore

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VectorMatchResult:
    """Result of vector similarity matching."""

    similarity: float
    score: float  # Normalized to 0-1
    passed: bool
    method: str = "cosine"


class VectorSimilarityMatcher:
    """
    Vector similarity matcher using sentence-transformers.

    Uses sentence embeddings to calculate semantic similarity between
    resume text and job postings. This allows matching based on meaning
    rather than just keyword overlap.

    Example:
        >>> matcher = VectorSimilarityMatcher()
        >>> result = matcher.match(
        ...     resume_text="Experienced web developer with React expertise",
        ...     job_title="Frontend Developer",
        ...     job_description="Looking for React.js specialist",
        ...     required_skills=["React"]
        ... )
        >>> print(result.score)
        0.85
    """

    # Class-level model cache
    _model: Optional['SentenceTransformer'] = None
    _model_name: Optional[str] = None

    def __init__(
        self,
        threshold: float = 0.5,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
    ):
        """
        Initialize the vector similarity matcher.

        Args:
            threshold: Minimum similarity score to pass (0.0-1.0)
            model_name: Name of sentence-transformers model to use
                       Default: "all-MiniLM-L6-v2" (fast, good quality)
                       Options:
                       - "all-MiniLM-L6-v2": Fast, 384dim
                       - "all-mpnet-base-v2": Slower, better quality, 768dim
                       - "paraphrase-multilingual-MiniLM-L12-v2": Multilingual
            device: Device to run model on ("cpu", "cuda", or None for auto)
        """
        self.threshold = threshold
        self.model_name = model_name
        self.device = device

        if not _HAS_SENTENCE_TRANSFORMERS:
            logger.warning("sentence-transformers not installed, vector matching disabled")

    @classmethod
    def _get_model(cls, model_name: str) -> Optional['SentenceTransformer']:
        """
        Get or load the sentence transformer model (cached).

        Args:
            model_name: Name of the model to load

        Returns:
            SentenceTransformer instance or None if not available
        """
        if not _HAS_SENTENCE_TRANSFORMERS:
            return None

        # Return cached model if same
        if cls._model is not None and cls._model_name == model_name:
            return cls._model

        try:
            logger.info(f"Loading sentence-transformers model: {model_name}")
            cls._model = SentenceTransformer(model_name)
            cls._model_name = model_name
            logger.info(f"Model loaded successfully")
            return cls._model
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model: {e}")
            return None

    def _encode_text(self, text: str) -> Optional[np.ndarray]:
        """
        Encode text to vector embedding.

        Args:
            text: Text to encode

        Returns:
            Numpy array of embeddings or None if encoding failed
        """
        if not _HAS_SENTENCE_TRANSFORMERS:
            return None

        model = self._get_model(self.model_name)
        if model is None:
            return None

        try:
            # Truncate text if too long (model max is usually 256-512 tokens)
            # Rough estimate: 1 token ≈ 4 characters
            max_chars = 8000
            truncated_text = text[:max_chars] if len(text) > max_chars else text

            embedding = model.encode(
                truncated_text,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            return embedding
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            return None

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (-1 to 1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.sqrt(np.dot(vec1, vec1))
        norm2 = np.sqrt(np.dot(vec2, vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def _normalize_score(self, cosine_sim: float) -> float:
        """
        Normalize cosine similarity to 0-1 range.

        Args:
            cosine_sim: Cosine similarity (-1 to 1)

        Returns:
            Normalized score (0 to 1)
        """
        return max(0.0, min(1.0, (cosine_sim + 1) / 2))

    def match(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        threshold: Optional[float] = None,
    ) -> VectorMatchResult:
        """
        Match resume against job posting using vector similarity.

        Args:
            resume_text: Resume text content
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills from job posting
            threshold: Override default threshold

        Returns:
            VectorMatchResult with similarity score and pass status
        """
        if threshold is None:
            threshold = self.threshold

        if not _HAS_SENTENCE_TRANSFORMERS:
            return VectorMatchResult(
                similarity=0.0,
                score=1.0,
                passed=True,
                method="disabled",
            )

        # Combine job text
        job_text = f"{job_title} {job_description} {' '.join(required_skills)}"

        # Encode both texts
        resume_embedding = self._encode_text(resume_text)
        job_embedding = self._encode_text(job_text)

        if resume_embedding is None or job_embedding is None:
            logger.warning("Failed to encode texts for vector matching")
            return VectorMatchResult(
                similarity=0.0,
                score=0.0,
                passed=False,
                method="error",
            )

        # Calculate cosine similarity
        cosine_sim = self._cosine_similarity(resume_embedding, job_embedding)

        # Normalize to 0-1
        score = self._normalize_score(cosine_sim)

        return VectorMatchResult(
            similarity=cosine_sim,
            score=score,
            passed=bool(score >= threshold),
            method="cosine",
        )

    def match_resume_to_vacancy(
        self,
        resume_text: str,
        resume_skills: List[str],
        vacancy_title: str,
        vacancy_description: str,
        vacancy_skills: List[str],
    ) -> VectorMatchResult:
        """
        Match a resume to a specific vacancy.

        Convenience method that combines resume skills with full text
        for better semantic matching.

        Args:
            resume_text: Full resume text
            resume_skills: Extracted skills from resume
            vacancy_title: Vacancy title
            vacancy_description: Vacancy description
            vacancy_skills: Required skills for vacancy

        Returns:
            VectorMatchResult with similarity details
        """
        # Combine resume text with skills
        enhanced_resume = f"{resume_text} {' '.join(resume_skills)}"

        return self.match(
            resume_text=enhanced_resume,
            job_title=vacancy_title,
            job_description=vacancy_description,
            required_skills=vacancy_skills,
        )

    def batch_match(
        self,
        resume_texts: List[str],
        job_text: str,
    ) -> List[float]:
        """
        Match multiple resumes against a single job posting.

        Useful for ranking candidates for a position.

        Args:
            resume_texts: List of resume texts
            job_text: Combined job posting text

        Returns:
            List of similarity scores (0-1)
        """
        if not _HAS_SENTENCE_TRANSFORMERS:
            return [0.0] * len(resume_texts)

        job_embedding = self._encode_text(job_text)
        if job_embedding is None:
            return [0.0] * len(resume_texts)

        scores = []
        for resume_text in resume_texts:
            resume_embedding = self._encode_text(resume_text)
            if resume_embedding is None:
                scores.append(0.0)
                continue

            cosine_sim = self._cosine_similarity(resume_embedding, job_embedding)
            score = self._normalize_score(cosine_sim)
            scores.append(score)

        return scores


# Singleton instance for convenience
_default_matcher: Optional[VectorSimilarityMatcher] = None


def get_vector_matcher() -> Optional[VectorSimilarityMatcher]:
    """Get or create default vector matcher instance."""
    global _default_matcher
    if _default_matcher is None:
        if _HAS_SENTENCE_TRANSFORMERS:
            _default_matcher = VectorSimilarityMatcher()
        else:
            logger.warning("sentence-transformers not available")
    return _default_matcher
