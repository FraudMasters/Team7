"""
Candidate Recommendation Service - Orchestrates all recommendation types.

This module provides a unified service for generating AI-powered candidate recommendations:
1. Similar Candidates ("Candidates Like This") - based on vector embeddings and skill similarity
2. Best Fit for Vacancy - top-ranked candidates for open roles using ML ranking
3. Candidates at Risk of Loss - identifies candidates likely to accept competing offers

The service coordinates multiple analyzers to provide comprehensive recommendations
with explanations, A/B testing support, and feedback tracking.
"""
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CandidateRecommendation, JobVacancy, Resume, ResumeAnalysis
from .ranking_service import RankingService, get_ranking_service
from .risk_predictor import RiskPredictor, RiskPredictionResult, get_risk_predictor
from .similar_candidates_finder import SimilarCandidatesFinder, SimilarCandidateResult, get_similar_candidates_finder
from .skill_gap_analyzer import SkillGapAnalyzer, get_skill_gap_analyzer
from .learning_recommendation_engine import LearningRecommendationEngine, get_learning_recommendation_engine

logger = logging.getLogger(__name__)


@dataclass
class RecommendationSummary:
    """
    Summary of all recommendation types for a candidate or vacancy.

    Attributes:
        similar_candidates: List of candidates similar to the target candidate
        best_fit_for_vacancy: List of top candidates for a vacancy (if vacancy_id provided)
        at_risk_candidates: List of candidates at risk of loss (if requested)
        total_recommendations: Total number of recommendations across all types
        generated_at: Timestamp when recommendations were generated
    """
    similar_candidates: List[SimilarCandidateResult] = field(default_factory=list)
    best_fit_for_vacancy: List[Dict[str, Any]] = field(default_factory=list)
    at_risk_candidates: List[RiskPredictionResult] = field(default_factory=list)
    total_recommendations: int = 0
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary for JSON serialization."""
        return {
            "similar_candidates": [
                {
                    "resume_id": str(c.resume_id),
                    "similarity_score": c.similarity_score,
                    "skills_overlap_score": c.skills_overlap_score,
                    "overall_score": c.overall_score,
                    "shared_skills": c.shared_skills,
                    "reason": c.reason,
                    "explanation": c.explanation,
                }
                for c in self.similar_candidates
            ],
            "best_fit_for_vacancy": self.best_fit_for_vacancy,
            "at_risk_candidates": [r.to_dict() for r in self.at_risk_candidates],
            "total_recommendations": self.total_recommendations,
            "generated_at": self.generated_at,
        }


@dataclass
class VacancyRecommendations:
    """
    Comprehensive recommendations for a specific job vacancy.

    Attributes:
        vacancy_id: UUID of the job vacancy
        top_candidates: Ranked list of best-fit candidates for this vacancy
        skill_gaps_summary: Summary of common skill gaps among top candidates
        learning_recommendations: Learning resources to address skill gaps
        total_candidates_analyzed: Total number of candidates considered
        generated_at: Timestamp when recommendations were generated
    """
    vacancy_id: str = ""
    top_candidates: List[Dict[str, Any]] = field(default_factory=list)
    skill_gaps_summary: Dict[str, Any] = field(default_factory=dict)
    learning_recommendations: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    total_candidates_analyzed: int = 0
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "vacancy_id": self.vacancy_id,
            "top_candidates": self.top_candidates,
            "skill_gaps_summary": self.skill_gaps_summary,
            "learning_recommendations": self.learning_recommendations,
            "total_candidates_analyzed": self.total_candidates_analyzed,
            "generated_at": self.generated_at,
        }


class CandidateRecommendationService:
    """
    Main service for coordinating all candidate recommendation types.

    This service orchestrates:
    - Similar candidates discovery (via SimilarCandidatesFinder)
    - Vacancy-specific best-fit ranking (via RankingService)
    - Risk prediction for candidate retention (via RiskPredictor)
    - Skill gap analysis (via SkillGapAnalyzer)
    - Learning recommendations (via LearningRecommendationEngine)

    All recommendations are stored in the database for tracking and feedback collection.

    Example:
        >>> service = CandidateRecommendationService()
        >>> # Get similar candidates
        >>> similar = await service.get_similar_candidates(db, resume_id, limit=10)
        >>> # Get best fit for a vacancy
        >>> best_fit = await service.get_best_fit_for_vacancy(db, vacancy_id, limit=20)
        >>> # Get candidates at risk
        >>> at_risk = await service.get_candidates_at_risk(db, limit=15)
    """

    def __init__(
        self,
        # Service instances (will use singleton getters if not provided)
        ranking_service: Optional[RankingService] = None,
        similar_finder: Optional[SimilarCandidatesFinder] = None,
        risk_predictor: Optional[RiskPredictor] = None,
        skill_gap_analyzer: Optional[SkillGapAnalyzer] = None,
        learning_engine: Optional[LearningRecommendationEngine] = None,

        # A/B testing configuration
        enable_ab_testing: bool = True,
        experiment_ratio: float = 0.2,  # 20% of requests go to experiment
    ):
        """
        Initialize the candidate recommendation service.

        Args:
            ranking_service: Optional RankingService instance (uses singleton if None)
            similar_finder: Optional SimilarCandidatesFinder instance (uses singleton if None)
            risk_predictor: Optional RiskPredictor instance (uses singleton if None)
            skill_gap_analyzer: Optional SkillGapAnalyzer instance (uses singleton if None)
            learning_engine: Optional LearningRecommendationEngine instance (uses singleton if None)
            enable_ab_testing: Whether to enable A/B testing for recommendations
            experiment_ratio: Ratio of requests to assign to experiment group (0-1)
        """
        self.ranking_service = ranking_service or get_ranking_service()
        self.similar_finder = similar_finder or get_similar_candidates_finder()
        self.risk_predictor = risk_predictor or get_risk_predictor()
        self.skill_gap_analyzer = skill_gap_analyzer or get_skill_gap_analyzer()
        self.learning_engine = learning_engine or get_learning_recommendation_engine()

        self.enable_ab_testing = enable_ab_testing
        self.experiment_ratio = experiment_ratio

        logger.info(
            f"CandidateRecommendationService initialized with "
            f"ab_testing={enable_ab_testing}, experiment_ratio={experiment_ratio}"
        )

    async def get_similar_candidates(
        self,
        db: AsyncSession,
        resume_id: UUID,
        limit: int = 10,
        store_recommendations: bool = True,
    ) -> List[SimilarCandidateResult]:
        """
        Get candidates similar to a given candidate.

        Uses vector embeddings and skill overlap to find semantically similar candidates.

        Args:
            db: Database session
            resume_id: UUID of the source resume
            limit: Maximum number of similar candidates to return
            store_recommendations: Whether to store recommendations in database

        Returns:
            List of SimilarCandidateResult objects, sorted by similarity score
        """
        logger.info(f"Finding similar candidates for resume {resume_id}")

        # Get similar candidates using the finder
        similar_results = await self.similar_finder.find_similar(
            db=db,
            resume_id=resume_id,
            limit=limit,
        )

        # Store recommendations in database if requested
        if store_recommendations and similar_results:
            await self._store_similar_candidate_recommendations(
                db=db,
                source_resume_id=resume_id,
                similar_results=similar_results,
            )

        logger.info(f"Found {len(similar_results)} similar candidates for {resume_id}")
        return similar_results

    async def get_best_fit_for_vacancy(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        limit: int = 20,
        include_skill_gaps: bool = True,
        include_learning_recommendations: bool = False,
        store_recommendations: bool = True,
    ) -> VacancyRecommendations:
        """
        Get best-fit candidates for a specific vacancy.

        Uses ML-based ranking to identify top candidates for the vacancy.

        Args:
            db: Database session
            vacancy_id: UUID of the job vacancy
            limit: Maximum number of candidates to return
            include_skill_gaps: Whether to include skill gap analysis
            include_learning_recommendations: Whether to include learning recommendations
            store_recommendations: Whether to store recommendations in database

        Returns:
            VacancyRecommendations object with top candidates and optional analysis
        """
        logger.info(f"Finding best-fit candidates for vacancy {vacancy_id}")

        # Get ranked candidates using the ranking service
        rankings = await self.ranking_service.rank_candidates_for_vacancy(
            db=db,
            vacancy_id=vacancy_id,
            limit=limit,
        )

        # Convert rankings to the expected format
        top_candidates = []
        skill_gaps_summary = {}
        learning_recommendations = {}

        if include_skill_gaps or include_learning_recommendations:
            # Analyze skill gaps for top candidates
            skill_gaps_summary = await self._analyze_vacancy_skill_gaps(
                db=db,
                vacancy_id=vacancy_id,
                top_candidates=rankings[:5],  # Analyze top 5
            )

            if include_learning_recommendations and skill_gaps_summary.get("common_gaps"):
                # Get learning recommendations for common gaps
                learning_recommendations = await self._get_learning_recommendations_for_gaps(
                    skill_gaps=skill_gaps_summary.get("common_gaps", [])
                )

        # Build top candidates list with additional context
        for ranking in rankings:
            top_candidates.append({
                "resume_id": ranking["resume_id"],
                "rank_score": ranking["rank_score"],
                "recommendation": ranking["recommendation"],
                "confidence": ranking["confidence"],
                "ranking_factors": ranking.get("ranking_factors", {}),
                "feature_contributions": ranking.get("feature_contributions", {}),
                "explanation": self._generate_ranking_explanation(ranking),
            })

        # Store recommendations in database if requested
        if store_recommendations and top_candidates:
            await self._store_best_fit_recommendations(
                db=db,
                vacancy_id=vacancy_id,
                top_candidates=top_candidates,
            )

        result = VacancyRecommendations(
            vacancy_id=str(vacancy_id),
            top_candidates=top_candidates,
            skill_gaps_summary=skill_gaps_summary,
            learning_recommendations=learning_recommendations,
            total_candidates_analyzed=len(rankings),
            generated_at=datetime.utcnow().isoformat(),
        )

        logger.info(f"Found {len(top_candidates)} best-fit candidates for vacancy {vacancy_id}")
        return result

    async def get_best_fit_candidates(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        limit: int = 20,
        min_score: float = 0.5,
        use_experiment: bool = True,
    ) -> Dict[str, Any]:
        """
        Get best fit candidates for a vacancy (API-compatible method).

        This is a convenience method that returns data in the format expected
        by the BestFitResponse API model.

        Args:
            db: Database session
            vacancy_id: UUID of the job vacancy
            limit: Maximum number of candidates to return
            min_score: Minimum match score threshold (0-1)
            use_experiment: Whether to include in A/B test experiment

        Returns:
            Dictionary with vacancy_id, candidates list, and metadata
        """
        logger.info(f"Finding best fit candidates for vacancy {vacancy_id} (min_score={min_score})")

        # Get ranked candidates using the ranking service
        rankings = await self.ranking_service.rank_candidates_for_vacancy(
            db=db,
            vacancy_id=vacancy_id,
            limit=limit,
        )

        # Filter by minimum score
        filtered_rankings = [
            r for r in rankings
            if r.get("rank_score", 0) >= min_score
        ]

        # Get vacancy details for skill comparison
        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_id)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        required_skills = []
        if vacancy:
            required_skills = vacancy.required_skills or []

        # Build candidates list with additional context
        candidates = []
        for ranking in filtered_rankings:
            resume_id = UUID(ranking["resume_id"])

            # Get resume details
            resume_query = select(Resume).where(Resume.id == resume_id)
            resume_result = await db.execute(resume_query)
            resume = resume_result.scalar_one_or_none()

            # Get resume analysis for skills
            analysis_query = select(ResumeAnalysis).where(
                ResumeAnalysis.resume_id == resume_id
            )
            analysis_result = await db.execute(analysis_query)
            analysis = analysis_result.scalar_one_or_none()

            candidate_skills = analysis.skills if analysis else []
            skills_set = {s.lower() for s in candidate_skills}
            required_set = {s.lower() for s in required_skills}

            # Determine matched and missing skills
            matched_skills = [
                s for s in required_skills
                if s.lower() in skills_set
            ]
            missing_skills = [
                s for s in required_skills
                if s.lower() not in skills_set
            ]

            # Calculate years of experience
            years_experience = None
            if resume and resume.work_experience:
                # Calculate total years from work experiences
                total_months = sum(
                    exp.get("months", 0) or 0
                    for exp in resume.work_experience
                    if exp.get("months")
                )
                years_experience = round(total_months / 12, 1)

            candidate_data = {
                "resume_id": ranking["resume_id"],
                "match_score": ranking["rank_score"],
                "name": resume.candidate_name if resume else None,
                "title": resume.title if resume else None,
                "skills_match": matched_skills,
                "missing_skills": missing_skills,
                "recommendation": ranking["recommendation"],
                "years_experience": years_experience,
                "recommendation_type": "best_fit",
                "feature_contributions": ranking.get("feature_contributions", {}),
            }

            candidates.append(candidate_data)

        # Determine experiment group for the response
        is_experiment, experiment_group = self._assign_experiment_group(use_experiment=use_experiment)

        result = {
            "vacancy_id": str(vacancy_id),
            "total_candidates": len(candidates),
            "candidates": candidates,
            "is_experiment": is_experiment if use_experiment else False,
            "experiment_group": experiment_group if use_experiment else None,
            "algorithm_version": self.ranking_service.model.version,
        }

        logger.info(f"Found {len(candidates)} best fit candidates for vacancy {vacancy_id}")
        return result

    async def get_candidates_at_risk(
        self,
        db: AsyncSession,
        limit: int = 15,
        min_risk_score: float = 0.5,
        store_recommendations: bool = True,
    ) -> List[RiskPredictionResult]:
        """
        Get candidates at risk of accepting competing offers or withdrawing.

        Uses ML-based risk prediction to identify candidates who may need attention.

        Args:
            db: Database session
            limit: Maximum number of at-risk candidates to return
            min_risk_score: Minimum risk score to include (0-1)
            store_recommendations: Whether to store recommendations in database

        Returns:
            List of RiskPredictionResult objects, sorted by risk score
        """
        logger.info(f"Finding candidates at risk (min_score={min_risk_score})")

        # Get at-risk candidates using the risk predictor
        risk_results = await self.risk_predictor.predict_at_risk_candidates(
            db=db,
            limit=limit,
            min_risk_score=min_risk_score,
        )

        # Store recommendations in database if requested
        if store_recommendations and risk_results:
            await self._store_at_risk_recommendations(
                db=db,
                risk_results=risk_results,
            )

        logger.info(f"Found {len(risk_results)} candidates at risk")
        return risk_results

    async def get_at_risk_candidates(
        self,
        db: AsyncSession,
        limit: int = 20,
        min_risk_score: float = 0.5,
        vacancy_id: Optional[UUID] = None,
        use_experiment: bool = True,
    ) -> Dict[str, Any]:
        """
        Get candidates at risk of loss (API-compatible method).

        This is a convenience method that returns data in the format expected
        by the AtRiskResponse API model.

        Args:
            db: Database session
            limit: Maximum number of candidates to return
            min_risk_score: Minimum risk score threshold (0-1)
            vacancy_id: Optional vacancy UUID to filter candidates (not yet implemented)
            use_experiment: Whether to include in A/B test experiment

        Returns:
            Dictionary with total_candidates, candidates list, and metadata
        """
        logger.info(f"Finding at-risk candidates for API (min_risk={min_risk_score})")

        # Get at-risk candidates using the core method
        risk_results = await self.get_candidates_at_risk(
            db=db,
            limit=limit,
            min_risk_score=min_risk_score,
            store_recommendations=True,
        )

        # Build candidates list with additional context
        candidates = []
        for risk_result in risk_results:
            # Get resume details for additional context
            resume_query = select(Resume).where(Resume.id == risk_result.resume_id)
            resume_result = await db.execute(resume_query)
            resume = resume_result.scalar_one_or_none()

            # Determine risk level based on score
            if risk_result.risk_score >= 0.7:
                risk_level = "high"
            elif risk_result.risk_score >= 0.5:
                risk_level = "medium"
            else:
                risk_level = "low"

            candidate_data = {
                "resume_id": str(risk_result.resume_id),
                "risk_score": risk_result.risk_score,
                "risk_level": risk_level,
                "name": resume.candidate_name if resume else None,
                "title": resume.title if resume else None,
                "risk_factors": risk_result.risk_factors,
                "days_since_contact": risk_result.days_since_contact,
                "recommended_action": risk_result.recommended_action,
                "recommendation_type": "at_risk",
                "feature_contributions": risk_result.feature_contributions if hasattr(risk_result, 'feature_contributions') else {},
            }

            candidates.append(candidate_data)

        # Determine experiment group for the response
        is_experiment, experiment_group = self._assign_experiment_group(use_experiment=use_experiment)

        result = {
            "total_candidates": len(candidates),
            "candidates": candidates,
            "is_experiment": is_experiment if use_experiment else False,
            "experiment_group": experiment_group if use_experiment else None,
            "algorithm_version": "1.0.0",
        }

        logger.info(f"Returning {len(candidates)} at-risk candidates for API")
        return result

    async def get_comprehensive_recommendations(
        self,
        db: AsyncSession,
        resume_id: Optional[UUID] = None,
        vacancy_id: Optional[UUID] = None,
        include_at_risk: bool = False,
        limits: Optional[Dict[str, int]] = None,
    ) -> RecommendationSummary:
        """
        Get comprehensive recommendations across all types.

        This is a convenience method that fetches all applicable recommendation types.

        Args:
            db: Database session
            resume_id: Optional resume ID for similar candidates
            vacancy_id: Optional vacancy ID for best-fit candidates
            include_at_risk: Whether to include at-risk candidates
            limits: Optional dict with limits for each type (similar, best_fit, at_risk)

        Returns:
            RecommendationSummary with all applicable recommendations
        """
        limits = limits or {"similar": 10, "best_fit": 20, "at_risk": 15}

        summary = RecommendationSummary(
            generated_at=datetime.utcnow().isoformat()
        )

        # Get similar candidates if resume_id provided
        if resume_id:
            summary.similar_candidates = await self.get_similar_candidates(
                db=db,
                resume_id=resume_id,
                limit=limits.get("similar", 10),
                store_recommendations=True,
            )

        # Get best fit if vacancy_id provided
        if vacancy_id:
            vacancy_recs = await self.get_best_fit_for_vacancy(
                db=db,
                vacancy_id=vacancy_id,
                limit=limits.get("best_fit", 20),
                include_skill_gaps=False,
                store_recommendations=True,
            )
            summary.best_fit_for_vacancy = vacancy_recs.top_candidates

        # Get at-risk candidates if requested
        if include_at_risk:
            summary.at_risk_candidates = await self.get_candidates_at_risk(
                db=db,
                limit=limits.get("at_risk", 15),
                store_recommendations=True,
            )

        # Calculate total
        summary.total_recommendations = (
            len(summary.similar_candidates) +
            len(summary.best_fit_for_vacancy) +
            len(summary.at_risk_candidates)
        )

        return summary

    async def _store_similar_candidate_recommendations(
        self,
        db: AsyncSession,
        source_resume_id: UUID,
        similar_results: List[SimilarCandidateResult],
    ):
        """Store similar candidate recommendations in database."""
        for idx, result in enumerate(similar_results):
            # Determine A/B test group (always enable for storage)
            is_experiment, experiment_group = self._assign_experiment_group(use_experiment=True)

            recommendation = CandidateRecommendation(
                resume_id=result.resume_id,
                recommendation_type="similar_candidates",
                score=result.overall_score,
                rank_position=idx + 1,
                reason=result.reason,
                similarity_score=result.similarity_score,
                model_version=self.similar_finder.model_name,
                algorithm="vector_similarity",
                feature_contributions={
                    "similarity_score": result.similarity_score,
                    "skills_overlap": result.skills_overlap_score,
                    "experience_similarity": result.experience_similarity,
                },
                explanation=result.explanation,
                context={
                    "shared_skills": result.shared_skills,
                    "source_resume_id": str(source_resume_id),
                },
                is_experiment=is_experiment,
                experiment_group=experiment_group,
            )

            # Check if recommendation already exists
            existing = await db.execute(
                select(CandidateRecommendation).where(
                    CandidateRecommendation.resume_id == result.resume_id,
                    CandidateRecommendation.recommendation_type == "similar_candidates",
                    CandidateRecommendation.context["source_resume_id"].astext == str(source_resume_id),
                )
            )
            existing_rec = existing.scalar_one_or_none()

            if existing_rec:
                # Update existing
                existing_rec.score = result.overall_score
                existing_rec.rank_position = idx + 1
                existing_rec.feature_contributions = recommendation.feature_contributions
                existing_rec.explanation = result.explanation
                existing_rec.updated_at = datetime.utcnow()
            else:
                db.add(recommendation)

        await db.commit()

    async def _store_best_fit_recommendations(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        top_candidates: List[Dict[str, Any]],
    ):
        """Store best-fit candidate recommendations in database."""
        for idx, candidate in enumerate(top_candidates):
            # Determine A/B test group (always enable for storage)
            is_experiment, experiment_group = self._assign_experiment_group(use_experiment=True)

            recommendation = CandidateRecommendation(
                resume_id=UUID(candidate["resume_id"]),
                vacancy_id=vacancy_id,
                recommendation_type="best_fit",
                score=candidate["rank_score"],
                rank_position=idx + 1,
                reason="skills_match",  # Primary reason
                model_version=self.ranking_service.model.version,
                algorithm="ml_ranking",
                feature_contributions=candidate.get("feature_contributions", {}),
                explanation=candidate.get("explanation", ""),
                context={
                    "recommendation": candidate.get("recommendation"),
                    "confidence": candidate.get("confidence"),
                },
                is_experiment=is_experiment,
                experiment_group=experiment_group,
            )

            # Check if recommendation already exists
            existing = await db.execute(
                select(CandidateRecommendation).where(
                    CandidateRecommendation.resume_id == UUID(candidate["resume_id"]),
                    CandidateRecommendation.vacancy_id == vacancy_id,
                    CandidateRecommendation.recommendation_type == "best_fit",
                )
            )
            existing_rec = existing.scalar_one_or_none()

            if existing_rec:
                # Update existing
                existing_rec.score = candidate["rank_score"]
                existing_rec.rank_position = idx + 1
                existing_rec.feature_contributions = recommendation.feature_contributions
                existing_rec.explanation = recommendation.explanation
                existing_rec.updated_at = datetime.utcnow()
            else:
                db.add(recommendation)

        await db.commit()

    async def _store_at_risk_recommendations(
        self,
        db: AsyncSession,
        risk_results: List[RiskPredictionResult],
    ):
        """Store at-risk candidate recommendations in database."""
        for idx, result in enumerate(risk_results):
            # Determine A/B test group (always enable for storage)
            is_experiment, experiment_group = self._assign_experiment_group(use_experiment=True)

            recommendation = CandidateRecommendation(
                resume_id=UUID(result.resume_id),
                recommendation_type="at_risk",
                score=result.risk_score,
                rank_position=idx + 1,
                reason=result.primary_risk_factors[0] if result.primary_risk_factors else "high_risk",
                risk_score=result.risk_score,
                model_version=result.model_version,
                algorithm="risk_prediction",
                feature_contributions=result.feature_contributions,
                explanation=result.explanation,
                context={
                    "risk_level": result.risk_level,
                    "recommended_actions": result.recommended_actions,
                },
                is_experiment=is_experiment,
                experiment_group=experiment_group,
            )

            # Check if recommendation already exists
            existing = await db.execute(
                select(CandidateRecommendation).where(
                    CandidateRecommendation.resume_id == UUID(result.resume_id),
                    CandidateRecommendation.recommendation_type == "at_risk",
                )
            )
            existing_rec = existing.scalar_one_or_none()

            if existing_rec:
                # Update existing
                existing_rec.score = result.risk_score
                existing_rec.rank_position = idx + 1
                existing_rec.feature_contributions = recommendation.feature_contributions
                existing_rec.explanation = result.explanation
                existing_rec.updated_at = datetime.utcnow()
            else:
                db.add(recommendation)

        await db.commit()

    async def _analyze_vacancy_skill_gaps(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        top_candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze common skill gaps among top candidates for a vacancy."""
        # Get vacancy details
        vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_id)
        vacancy_result = await db.execute(vacancy_query)
        vacancy = vacancy_result.scalar_one_or_none()

        if not vacancy:
            return {}

        # Get required skills from vacancy
        required_skills = vacancy.required_skills or []

        # Analyze each top candidate's skills
        all_candidate_skills = []
        for candidate in top_candidates:
            resume_id = UUID(candidate["resume_id"])

            # Get resume analysis
            analysis_query = select(ResumeAnalysis).where(
                ResumeAnalysis.resume_id == resume_id
            )
            analysis_result = await db.execute(analysis_query)
            analysis = analysis_result.scalar_one_or_none()

            if analysis and analysis.skills:
                all_candidate_skills.extend(analysis.skills)

        # Find common gaps (required skills not present in candidates)
        unique_candidate_skills = list(set(all_candidate_skills))
        common_gaps = [
            skill for skill in required_skills
            if skill.lower() not in [s.lower() for s in unique_candidate_skills]
        ]

        return {
            "required_skills": required_skills,
            "candidate_skills": unique_candidate_skills,
            "common_gaps": common_gaps,
            "gap_count": len(common_gaps),
        }

    async def _get_learning_recommendations_for_gaps(
        self,
        skill_gaps: List[str],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get learning recommendations for specific skill gaps."""
        recommendations = {}

        for skill in skill_gaps:
            # Get learning recommendations for this skill
            skill_recs = self.learning_engine.recommend_for_skill(
                skill=skill,
                skill_level="intermediate",
                max_recommendations=3,
                include_free=True,
                include_paid=True,
            )

            # Convert to dict format
            recommendations[skill] = [rec.to_dict() for rec in skill_recs]

        return recommendations

    def _generate_ranking_explanation(self, ranking: Dict[str, Any]) -> str:
        """Generate human-readable explanation for a ranking result."""
        recommendation = ranking.get("recommendation", "maybe")
        confidence = ranking.get("confidence", 0.0)

        if recommendation == "excellent":
            base = "Strong match with high skills overlap and relevant experience"
        elif recommendation == "good":
            base = "Good fit with solid skills and experience"
        elif recommendation == "maybe":
            base = "Potential fit with some skills match"
        else:
            base = "Limited match with significant skill gaps"

        factors = ranking.get("ranking_factors", {})
        if factors:
            details = []
            if "skills_match" in factors:
                matched = factors["skills_match"].get("matched", 0)
                total = factors["skills_match"].get("total", 0)
                if total > 0:
                    details.append(f"matches {matched}/{total} required skills")
            if details:
                base += f" ({', '.join(details)})"

        return base

    async def submit_feedback(
        self,
        db: AsyncSession,
        recommendation_id: UUID,
        was_helpful: bool,
        was_contacted: bool = False,
        outcome: Optional[str] = None,
        rating: Optional[int] = None,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit feedback on a recommendation.

        Args:
            db: Database session
            recommendation_id: CandidateRecommendation UUID
            was_helpful: Whether the recommendation was helpful
            was_contacted: Whether user contacted the recommended candidate
            outcome: Actual hiring outcome (hired, rejected, pending, etc.)
            rating: Optional star rating (1-5)
            comments: Optional comments

        Returns:
            Created feedback record

        Raises:
            ValueError: If recommendation not found
        """
        from models.candidate_recommendation import RecommendationFeedback

        # Verify recommendation exists
        recommendation_query = select(CandidateRecommendation).where(
            CandidateRecommendation.id == recommendation_id
        )
        result = await db.execute(recommendation_query)
        recommendation = result.scalar_one_or_none()

        if not recommendation:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        # Create feedback record
        feedback = RecommendationFeedback(
            recommendation_id=recommendation_id,
            feedback_type="thumbs",
            was_helpful=was_helpful,
            was_actionable=was_contacted,
            actual_outcome=outcome,
            rating=rating,
            comments=comments,
            feedback_source="api",
        )

        db.add(feedback)
        await db.commit()

        logger.info(
            f"Feedback submitted for recommendation {recommendation_id}: "
            f"helpful={was_helpful}, contacted={was_contacted}, outcome={outcome}"
        )

        return {
            "id": str(feedback.id),
            "recommendation_id": str(feedback.recommendation_id),
            "was_helpful": feedback.was_helpful,
            "was_contacted": feedback.was_actionable,
            "outcome": feedback.actual_outcome,
        }

    def _assign_experiment_group(self, use_experiment: bool = True) -> tuple[bool, Optional[str]]:
        """
        Assign request to A/B test group if enabled.

        Follows the same pattern as RankingService:
        - First determines if the request should be in the experiment group
        - Then assigns to control/treatment if in experiment

        Args:
            use_experiment: Whether to allow A/B testing for this request

        Returns:
            Tuple of (is_experiment, experiment_group)
            is_experiment: Whether this recommendation is in an A/B test
            experiment_group: 'control', 'treatment', or None
        """
        # Determine if this request should be in the experiment group
        is_experiment = use_experiment and self.enable_ab_testing and random.random() < self.experiment_ratio

        # Assign experiment group if in experiment
        experiment_group = None
        if is_experiment:
            # 50/50 split between control and treatment
            experiment_group = "treatment" if random.random() < 0.5 else "control"

        return is_experiment, experiment_group


# Singleton instance
_default_service: Optional[CandidateRecommendationService] = None


def get_candidate_recommendation_service() -> CandidateRecommendationService:
    """Get or create default candidate recommendation service instance."""
    global _default_service
    if _default_service is None:
        _default_service = CandidateRecommendationService()
    return _default_service
