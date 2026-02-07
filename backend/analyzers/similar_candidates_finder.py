"""
Similar Candidates Finder using Vector Embeddings

This module provides semantic similarity-based candidate recommendations using
sentence-transformers embeddings. It enables "Candidates Like This" functionality
to help recruiters discover similar candidates when viewing a profile.

Key features:
- Vector-based semantic similarity between resumes
- Skills overlap scoring
- Experience relevance matching
- Cached model loading for performance
- Explainable recommendations with feature contributions
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    _HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None  # type: ignore

from models import CandidateRecommendation, Resume, ResumeAnalysis
from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)


@dataclass
class SimilarCandidateResult:
    """Result of similar candidates search."""

    resume_id: UUID
    similarity_score: float  # 0-1
    skills_overlap_score: float  # 0-1
    experience_similarity: float  # 0-1
    overall_score: float  # 0-1
    shared_skills: List[str]
    reason: str
    explanation: str


class SimilarCandidatesFinder:
    """
    Similar candidates finder using vector embeddings.

    Finds candidates similar to a given candidate based on:
    - Semantic similarity of resume text (using sentence embeddings)
    - Skills overlap
    - Experience similarity
    - Education match

    Example:
        >>> finder = SimilarCandidatesFinder()
        >>> results = await finder.find_similar(
        ...     db=session,
        ...     resume_id=uuid4(),
        ...     limit=10
        ... )
        >>> print(results[0].resume_id)
    """

    # Class-level model cache
    _model: Optional['SentenceTransformer'] = None
    _model_name: Optional[str] = None

    def __init__(
        self,
        threshold: float = 0.4,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
    ):
        """
        Initialize the similar candidates finder.

        Args:
            threshold: Minimum similarity score to include (0.0-1.0)
            model_name: Name of sentence-transformers model to use
                       Default: "all-MiniLM-L6-v2" (fast, good quality)
            device: Device to run model on ("cpu", "cuda", or None for auto)
        """
        self.threshold = threshold
        self.model_name = model_name
        self.device = device

        if not _HAS_SENTENCE_TRANSFORMERS:
            logger.warning("sentence-transformers not installed, similarity search disabled")

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
            # Truncate text if too long
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

    def _compute_skills_overlap(
        self,
        skills1: Optional[List[str]],
        skills2: Optional[List[str]],
    ) -> tuple[float, List[str]]:
        """
        Compute skills overlap between two candidates.

        Args:
            skills1: Skills of first candidate
            skills2: Skills of second candidate

        Returns:
            Tuple of (overlap_score, shared_skills)
        """
        if not skills1 or not skills2:
            return 0.0, []

        set1 = set(s.lower() for s in skills1)
        set2 = set(s.lower() for s in skills2)

        shared = list(set1 & set2)
        union = set1 | set2

        if not union:
            return 0.0, []

        overlap_score = len(shared) / len(union)
        return overlap_score, [s for s in skills1 if s.lower() in shared]

    def _compute_experience_similarity(
        self,
        exp1: Optional[int],
        exp2: Optional[int],
    ) -> float:
        """
        Compute experience similarity between two candidates.

        Args:
            exp1: Experience of first candidate (months)
            exp2: Experience of second candidate (months)

        Returns:
            Similarity score (0-1)
        """
        if exp1 is None or exp2 is None or exp1 == 0 or exp2 == 0:
            return 0.5  # Neutral score if no experience data

        # Use ratio of experiences, penalize large differences
        ratio = min(exp1, exp2) / max(exp1, exp2)
        return float(ratio)

    def _build_explanation(
        self,
        shared_skills: List[str],
        similarity_score: float,
        skills_overlap: float,
        exp_similarity: float,
    ) -> str:
        """
        Build human-readable explanation for recommendation.

        Args:
            shared_skills: List of shared skills
            similarity_score: Semantic similarity score
            skills_overlap: Skills overlap score
            exp_similarity: Experience similarity score

        Returns:
            Explanation string
        """
        parts = []

        # Skills explanation
        if shared_skills:
            top_skills = shared_skills[:5]
            if len(shared_skills) > 5:
                top_skills.append(f"{len(shared_skills) - 5} more")
            parts.append(f"Shared skills: {', '.join(top_skills)}")

        # Similarity explanation
        if similarity_score > 0.7:
            parts.append("Very similar profile and background")
        elif similarity_score > 0.5:
            parts.append("Similar professional background")

        # Experience explanation
        if exp_similarity > 0.8:
            parts.append("Comparable experience level")

        return ". ".join(parts) if parts else "Similar candidate profile"

    def _compute_reason(
        self,
        skills_overlap: float,
        similarity_score: float,
        exp_similarity: float,
    ) -> str:
        """
        Determine primary reason for recommendation.

        Args:
            skills_overlap: Skills overlap score
            similarity_score: Semantic similarity score
            exp_similarity: Experience similarity score

        Returns:
            Reason string
        """
        if skills_overlap > 0.6:
            return "skills_match"
        elif similarity_score > 0.7:
            return "profile_similarity"
        elif exp_similarity > 0.8:
            return "experience"
        else:
            return "overall_fit"

    async def find_similar(
        self,
        db: AsyncSession,
        resume_id: UUID,
        limit: int = 10,
        min_similarity: Optional[float] = None,
    ) -> List[SimilarCandidateResult]:
        """
        Find candidates similar to the given resume.

        Args:
            db: Database session
            resume_id: UUID of the reference resume
            limit: Maximum number of similar candidates to return
            min_similarity: Override default minimum similarity threshold

        Returns:
            List of similar candidate results, sorted by overall score
        """
        import time
        start_time = time.time()

        threshold = min_similarity if min_similarity is not None else self.threshold

        # Fetch the source resume
        source_query = select(Resume).where(Resume.id == resume_id)
        source_result = await db.execute(source_query)
        source_resume = source_result.scalar_one_or_none()

        if not source_resume:
            raise ValueError(f"Resume not found: {resume_id}")

        # Fetch source resume analysis
        source_analysis_query = select(ResumeAnalysis).where(
            ResumeAnalysis.resume_id == resume_id
        )
        source_analysis_result = await db.execute(source_analysis_query)
        source_analysis = source_analysis_result.scalar_one_or_none()

        # Get source resume data
        source_text = source_resume.raw_text or ""
        source_skills = source_analysis.skills if source_analysis else []
        source_exp = source_analysis.total_experience_months if source_analysis else None

        # Encode source resume
        source_embedding = self._encode_text(source_text)

        # Fetch all other completed resumes
        candidates_query = select(Resume).where(
            Resume.status == "COMPLETED",
            Resume.id != resume_id,
        ).limit(limit * 5)  # Fetch more to filter

        candidates_result = await db.execute(candidates_query)
        candidate_resumes = candidates_result.scalars().all()

        if not candidate_resumes:
            return []

        # Get candidate IDs for batch analysis fetch
        candidate_ids = [r.id for r in candidate_resumes]
        analyses_query = select(ResumeAnalysis).where(
            ResumeAnalysis.resume_id.in_(candidate_ids)
        )
        analyses_result = await db.execute(analyses_query)
        analyses = {a.resume_id: a for a in analyses_result.scalars().all()}

        # Compute similarities
        candidates_data = []
        for candidate_resume in candidate_resumes:
            analysis = analyses.get(candidate_resume.id)

            # Get candidate data
            candidate_text = candidate_resume.raw_text or ""
            candidate_skills = analysis.skills if analysis else []
            candidate_exp = analysis.total_experience_months if analysis else None

            # Skip if no text
            if not candidate_text:
                continue

            # Compute scores
            similarity_score = 0.0
            if source_embedding is not None and _HAS_SENTENCE_TRANSFORMERS:
                candidate_embedding = self._encode_text(candidate_text)
                if candidate_embedding is not None:
                    cosine_sim = self._cosine_similarity(source_embedding, candidate_embedding)
                    similarity_score = self._normalize_score(cosine_sim)

            # If vector similarity is disabled, use heuristic
            if not _HAS_SENTENCE_TRANSFORMERS:
                similarity_score = 0.5

            # Compute skills overlap
            skills_overlap, shared_skills = self._compute_skills_overlap(
                source_skills, candidate_skills
            )

            # Compute experience similarity
            exp_similarity = self._compute_experience_similarity(source_exp, candidate_exp)

            # Compute overall score (weighted average)
            overall_score = (
                similarity_score * 0.5 +
                skills_overlap * 0.3 +
                exp_similarity * 0.2
            )

            if overall_score < threshold:
                continue

            # Build explanation
            explanation = self._build_explanation(
                shared_skills, similarity_score, skills_overlap, exp_similarity
            )

            # Determine reason
            reason = self._compute_reason(skills_overlap, similarity_score, exp_similarity)

            candidates_data.append(
                SimilarCandidateResult(
                    resume_id=candidate_resume.id,
                    similarity_score=similarity_score,
                    skills_overlap_score=skills_overlap,
                    experience_similarity=exp_similarity,
                    overall_score=overall_score,
                    shared_skills=shared_skills,
                    reason=reason,
                    explanation=explanation,
                )
            )

        # Sort by overall score
        candidates_data.sort(key=lambda x: x.overall_score, reverse=True)

        # Record metrics
        duration = time.time() - start_time
        try:
            registry = get_metrics_registry()
            registry.record_ml_inference(
                model_name="similar_candidates_finder",
                operation="find_similar",
                duration=duration,
                prediction_type="recommendation",
            )
        except Exception as metrics_error:
            logger.debug(f"Failed to record metrics: {metrics_error}")

        return candidates_data[:limit]

    async def create_recommendations(
        self,
        db: AsyncSession,
        resume_id: UUID,
        recruiter_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[CandidateRecommendation]:
        """
        Create recommendation records for similar candidates.

        Args:
            db: Database session
            resume_id: UUID of the source resume
            recruiter_id: Optional UUID of the recruiter for personalization
            limit: Maximum number of recommendations to create

        Returns:
            List of created CandidateRecommendation records
        """
        # Find similar candidates
        similar_results = await self.find_similar(db, resume_id, limit)

        recommendations = []
        for rank, result in enumerate(similar_results, start=1):
            # Check if recommendation already exists
            existing_query = select(CandidateRecommendation).where(
                CandidateRecommendation.resume_id == result.resume_id,
                CandidateRecommendation.recommendation_type == "similar_candidates",
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            # Feature contributions
            feature_contributions = {
                "similarity_score": result.similarity_score,
                "skills_overlap": result.skills_overlap_score,
                "experience_similarity": result.experience_similarity,
            }

            # Context with shared skills
            context = {
                "shared_skills": result.shared_skills,
                "source_resume_id": str(resume_id),
            }

            if existing:
                # Update existing
                existing.score = result.overall_score
                existing.rank_position = rank
                existing.reason = result.reason
                existing.similarity_score = result.similarity_score
                existing.explanation = result.explanation
                existing.feature_contributions = feature_contributions
                existing.context = context
                recommendations.append(existing)
            else:
                # Create new
                recommendation = CandidateRecommendation(
                    resume_id=result.resume_id,
                    recruiter_id=recruiter_id,
                    recommendation_type="similar_candidates",
                    score=result.overall_score,
                    rank_position=rank,
                    reason=result.reason,
                    similarity_score=result.similarity_score,
                    model_version="v1.0",
                    algorithm="vector_similarity",
                    feature_contributions=feature_contributions,
                    explanation=result.explanation,
                    context=context,
                )
                db.add(recommendation)
                recommendations.append(recommendation)

        await db.commit()

        return recommendations


# Singleton instance for convenience
_default_finder: Optional[SimilarCandidatesFinder] = None


def get_similar_candidates_finder() -> Optional[SimilarCandidatesFinder]:
    """Get or create default similar candidates finder instance."""
    global _default_finder
    if _default_finder is None:
        if _HAS_SENTENCE_TRANSFORMERS:
            _default_finder = SimilarCandidatesFinder()
        else:
            logger.warning("sentence-transformers not available")
    return _default_finder
