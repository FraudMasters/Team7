"""
Resume Comparator Analyzer

This module provides comparison analysis between a candidate's resume and
top-performing candidates for similar roles. It helps identify:
1. Strengths relative to top performers
2. Areas for improvement
3. Competitive positioning
4. Skill coverage compared to successful candidates
5. Experience level benchmarking
6. Overall competitiveness score

The comparator uses unified matching and ranking features to provide
comprehensive comparison insights.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CandidateRank, Resume, ResumeAnalysis
from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)


@dataclass
class ComparisonMetric:
    """
    Individual metric comparison against top performers.

    Attributes:
        metric_name: Name of the metric being compared
        candidate_value: Candidate's value for this metric
        top_performers_avg: Average value among top performers
        top_performers_max: Maximum value among top performers
        percentile: Candidate's percentile rank (0-100)
        gap: Difference from top performers average
        competitive_position: Position relative to top performers (leading, competitive, trailing)
    """

    metric_name: str
    candidate_value: float
    top_performers_avg: float
    top_performers_max: float
    percentile: float = 0.0
    gap: float = 0.0
    competitive_position: str = "unknown"  # leading, competitive, trailing

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "metric_name": self.metric_name,
            "candidate_value": round(self.candidate_value, 2),
            "top_performers_avg": round(self.top_performers_avg, 2),
            "top_performers_max": round(self.top_performers_max, 2),
            "percentile": round(self.percentile, 2),
            "gap": round(self.gap, 2),
            "competitive_position": self.competitive_position,
        }


@dataclass
class ComparisonResult:
    """
    Comprehensive result from resume comparison analysis.

    Attributes:
        candidate_resume_id: UUID of candidate being compared
        job_role: Job role being compared against
        top_performers_count: Number of top performers used for comparison
        metrics: List of individual metric comparisons
        strengths: Areas where candidate exceeds top performers
        improvement_areas: Areas where candidate trails top performers
        competitive_skills: Skills shared with top performers
        missing_skills: Skills common among top performers but missing
        overall_competitiveness_score: Overall score (0-100)
        competitiveness_tier: Tier classification (top, strong, average, weak)
        recommendations: Specific recommendations for improvement
        benchmark_summary: Human-readable summary of positioning
    """

    # Input data
    candidate_resume_id: UUID
    job_role: str = ""
    top_performers_count: int = 0

    # Comparison metrics
    metrics: List[ComparisonMetric] = field(default_factory=list)

    # Categorized analysis
    strengths: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    competitive_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)

    # Overall assessment
    overall_competitiveness_score: float = 0.0  # 0-100
    competitiveness_tier: str = "unknown"  # top, strong, average, weak

    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    benchmark_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "candidate_resume_id": str(self.candidate_resume_id),
            "job_role": self.job_role,
            "top_performers_count": self.top_performers_count,
            "metrics": [m.to_dict() for m in self.metrics],
            "strengths": self.strengths,
            "improvement_areas": self.improvement_areas,
            "competitive_skills": self.competitive_skills,
            "missing_skills": self.missing_skills,
            "overall_competitiveness_score": round(self.overall_competitiveness_score, 2),
            "competitiveness_tier": self.competitiveness_tier,
            "recommendations": self.recommendations,
            "benchmark_summary": self.benchmark_summary,
        }


class ResumeComparator:
    """
    Compares candidate resumes against top-performing candidates.

    Uses ranking data and resume analysis to benchmark a candidate against
    successful candidates in similar roles. Provides actionable insights
    for resume improvement and competitive positioning.

    Example:
        >>> comparator = ResumeComparator()
        >>> result = await comparator.compare_against_top_performers(
        ...     db=session,
        ...     candidate_resume_id=uuid4(),
        ...     job_vacancy_id=uuid4(),
        ...     top_n=10
        ... )
        >>> print(result.overall_competitiveness_score)
        75.5
        >>> print(result.competitiveness_tier)
        'strong'
        >>> print(result.recommendations)
        ['Add cloud computing skills', 'Highlight leadership experience']
    """

    def __init__(
        self,
        # Competitiveness tier thresholds
        top_tier_threshold: float = 80.0,  # >=80 = top
        strong_tier_threshold: float = 60.0,  # >=60 = strong
        average_tier_threshold: float = 40.0,  # >=40 = average

        # Competitive position thresholds
        leading_threshold: float = 1.1,  # >110% of avg = leading
        competitive_threshold: float = 0.9,  # >90% of avg = competitive

        # Minimum top performers for valid comparison
        min_top_performers: int = 3,
    ):
        """
        Initialize the resume comparator.

        Args:
            top_tier_threshold: Score threshold for 'top' tier (0-100)
            strong_tier_threshold: Score threshold for 'strong' tier (0-100)
            average_tier_threshold: Score threshold for 'average' tier (0-100)
            leading_threshold: Ratio threshold for 'leading' position
            competitive_threshold: Ratio threshold for 'competitive' position
            min_top_performers: Minimum number of top performers needed
        """
        self.top_tier_threshold = top_tier_threshold
        self.strong_tier_threshold = strong_tier_threshold
        self.average_tier_threshold = average_tier_threshold
        self.leading_threshold = leading_threshold
        self.competitive_threshold = competitive_threshold
        self.min_top_performers = min_top_performers

        logger.info(
            f"ResumeComparator initialized with "
            f"top_tier={top_tier_threshold}, "
            f"strong_tier={strong_tier_threshold}"
        )

    def _determine_competitive_position(
        self, candidate_value: float, top_performers_avg: float
    ) -> str:
        """
        Determine competitive position based on candidate value vs average.

        Args:
            candidate_value: Candidate's metric value
            top_performers_avg: Average value among top performers

        Returns:
            Position classification: 'leading', 'competitive', or 'trailing'
        """
        if top_performers_avg == 0:
            return "unknown"

        ratio = candidate_value / top_performers_avg

        if ratio >= self.leading_threshold:
            return "leading"
        elif ratio >= self.competitive_threshold:
            return "competitive"
        else:
            return "trailing"

    def _calculate_percentile(
        self, candidate_value: float, all_values: List[float]
    ) -> float:
        """
        Calculate percentile rank of candidate among all values.

        Args:
            candidate_value: Candidate's value
            all_values: List of all values including candidate

        Returns:
            Percentile rank (0-100)
        """
        if not all_values:
            return 50.0

        sorted_values = sorted(all_values)
        count_below = sum(1 for v in sorted_values if v < candidate_value)
        percentile = (count_below / len(sorted_values)) * 100
        return percentile

    def _compare_metric(
        self,
        metric_name: str,
        candidate_value: float,
        top_performers_values: List[float],
    ) -> ComparisonMetric:
        """
        Compare a single metric against top performers.

        Args:
            metric_name: Name of the metric
            candidate_value: Candidate's value
            top_performers_values: Values from top performers

        Returns:
            ComparisonMetric with detailed comparison
        """
        if not top_performers_values:
            return ComparisonMetric(
                metric_name=metric_name,
                candidate_value=candidate_value,
                top_performers_avg=0.0,
                top_performers_max=0.0,
            )

        top_avg = float(np.mean(top_performers_values))
        top_max = float(np.max(top_performers_values))
        gap = candidate_value - top_avg

        # Calculate percentile including candidate
        all_values = top_performers_values + [candidate_value]
        percentile = self._calculate_percentile(candidate_value, all_values)

        # Determine competitive position
        position = self._determine_competitive_position(candidate_value, top_avg)

        return ComparisonMetric(
            metric_name=metric_name,
            candidate_value=candidate_value,
            top_performers_avg=top_avg,
            top_performers_max=top_max,
            percentile=percentile,
            gap=gap,
            competitive_position=position,
        )

    def _extract_strengths_and_gaps(
        self, metrics: List[ComparisonMetric]
    ) -> tuple[List[str], List[str]]:
        """
        Extract strengths and improvement areas from metrics.

        Args:
            metrics: List of comparison metrics

        Returns:
            Tuple of (strengths, improvement_areas)
        """
        strengths = []
        improvement_areas = []

        for metric in metrics:
            if metric.competitive_position == "leading":
                strengths.append(
                    f"{metric.metric_name}: {metric.percentile:.0f}th percentile"
                )
            elif metric.competitive_position == "trailing":
                improvement_areas.append(
                    f"{metric.metric_name}: Below average by {abs(metric.gap):.1f}"
                )

        return strengths, improvement_areas

    def _compare_skills(
        self,
        candidate_skills: List[str],
        top_performers_skills: List[List[str]],
    ) -> tuple[List[str], List[str]]:
        """
        Compare candidate skills against top performers.

        Args:
            candidate_skills: List of candidate's skills
            top_performers_skills: List of skill lists from top performers

        Returns:
            Tuple of (competitive_skills, missing_skills)
        """
        if not top_performers_skills:
            return [], []

        # Normalize skills
        candidate_skills_lower = set(s.lower() for s in candidate_skills)

        # Find common skills among top performers
        all_top_skills = []
        for skills in top_performers_skills:
            all_top_skills.extend(s.lower() for s in skills)

        # Skills that appear in at least 50% of top performers
        skill_frequency = {}
        for skill in all_top_skills:
            skill_frequency[skill] = skill_frequency.get(skill, 0) + 1

        common_threshold = len(top_performers_skills) * 0.5
        common_top_skills = {
            skill for skill, count in skill_frequency.items() if count >= common_threshold
        }

        # Competitive skills: skills candidate has that are common among top performers
        competitive_skills = list(candidate_skills_lower & common_top_skills)

        # Missing skills: common top performer skills that candidate lacks
        missing_skills = list(common_top_skills - candidate_skills_lower)

        return competitive_skills, missing_skills

    def _calculate_overall_score(self, metrics: List[ComparisonMetric]) -> float:
        """
        Calculate overall competitiveness score from metrics.

        Args:
            metrics: List of comparison metrics

        Returns:
            Overall score (0-100)
        """
        if not metrics:
            return 0.0

        # Use average percentile as overall score
        percentiles = [m.percentile for m in metrics]
        return float(np.mean(percentiles))

    def _determine_tier(self, overall_score: float) -> str:
        """
        Determine competitiveness tier based on overall score.

        Args:
            overall_score: Overall competitiveness score (0-100)

        Returns:
            Tier classification: 'top', 'strong', 'average', or 'weak'
        """
        if overall_score >= self.top_tier_threshold:
            return "top"
        elif overall_score >= self.strong_tier_threshold:
            return "strong"
        elif overall_score >= self.average_tier_threshold:
            return "average"
        else:
            return "weak"

    def _generate_recommendations(
        self,
        improvement_areas: List[str],
        missing_skills: List[str],
        competitiveness_tier: str,
    ) -> List[str]:
        """
        Generate actionable recommendations for improvement.

        Args:
            improvement_areas: Areas where candidate trails
            missing_skills: Skills commonly found in top performers
            competitiveness_tier: Current tier classification

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Skill-based recommendations
        if missing_skills:
            top_missing = missing_skills[:5]
            if len(top_missing) <= 3:
                for skill in top_missing:
                    recommendations.append(f"Add '{skill}' skill to your resume")
            else:
                recommendations.append(
                    f"Consider adding these in-demand skills: {', '.join(top_missing)}"
                )

        # Metric-based recommendations
        if improvement_areas:
            # Focus on top 3 areas
            for area in improvement_areas[:3]:
                if "experience" in area.lower():
                    recommendations.append("Highlight relevant experience more prominently")
                elif "education" in area.lower():
                    recommendations.append("Consider additional certifications or training")
                elif "score" in area.lower():
                    recommendations.append("Optimize resume for keyword matching")

        # Tier-specific recommendations
        if competitiveness_tier == "weak":
            recommendations.append(
                "Consider significant resume restructuring to match top performer profiles"
            )
        elif competitiveness_tier == "average":
            recommendations.append(
                "Focus on differentiating yourself through unique skills or achievements"
            )
        elif competitiveness_tier == "strong":
            recommendations.append("Refine and polish existing strengths")

        # Default if no specific recommendations
        if not recommendations:
            recommendations.append("Continue building relevant skills and experience")

        return recommendations

    def _build_benchmark_summary(
        self,
        competitiveness_tier: str,
        overall_score: float,
        top_performers_count: int,
    ) -> str:
        """
        Build human-readable benchmark summary.

        Args:
            competitiveness_tier: Tier classification
            overall_score: Overall competitiveness score
            top_performers_count: Number of top performers compared against

        Returns:
            Summary string
        """
        tier_descriptions = {
            "top": "in the top tier of",
            "strong": "strongly competitive with",
            "average": "moderately competitive with",
            "weak": "below average compared to",
        }

        description = tier_descriptions.get(competitiveness_tier, "comparable to")

        return (
            f"Your resume scores {overall_score:.1f}/100, placing you {description} "
            f"{top_performers_count} top-performing candidates for similar roles."
        )

    async def compare_against_top_performers(
        self,
        db: AsyncSession,
        candidate_resume_id: UUID,
        job_vacancy_id: Optional[UUID] = None,
        job_role: Optional[str] = None,
        top_n: int = 10,
    ) -> ComparisonResult:
        """
        Compare candidate resume against top-performing candidates.

        Args:
            db: Database session
            candidate_resume_id: UUID of candidate's resume
            job_vacancy_id: Optional UUID of specific job vacancy
            job_role: Optional job role/title for comparison
            top_n: Number of top performers to compare against

        Returns:
            ComparisonResult with detailed benchmarking analysis

        Raises:
            ValueError: If resume not found or insufficient top performers
        """
        import time
        start_time = time.time()

        # Fetch candidate resume and analysis
        candidate_query = select(Resume).where(Resume.id == candidate_resume_id)
        candidate_result = await db.execute(candidate_query)
        candidate_resume = candidate_result.scalar_one_or_none()

        if not candidate_resume:
            raise ValueError(f"Resume not found: {candidate_resume_id}")

        candidate_analysis_query = select(ResumeAnalysis).where(
            ResumeAnalysis.resume_id == candidate_resume_id
        )
        candidate_analysis_result = await db.execute(candidate_analysis_query)
        candidate_analysis = candidate_analysis_result.scalar_one_or_none()

        # Fetch top performers
        # If job_vacancy_id provided, get top performers for that vacancy
        # Otherwise, get generally high-ranking candidates
        top_performers_query = select(CandidateRank).order_by(
            CandidateRank.final_score.desc()
        )

        if job_vacancy_id:
            top_performers_query = top_performers_query.where(
                CandidateRank.vacancy_id == job_vacancy_id
            )

        top_performers_query = top_performers_query.limit(top_n)
        top_performers_result = await db.execute(top_performers_query)
        top_performers = top_performers_result.scalars().all()

        if len(top_performers) < self.min_top_performers:
            raise ValueError(
                f"Insufficient top performers found: {len(top_performers)} "
                f"(minimum {self.min_top_performers} required)"
            )

        # Fetch resume analyses for top performers
        top_performer_resume_ids = [tp.resume_id for tp in top_performers]
        top_analyses_query = select(ResumeAnalysis).where(
            ResumeAnalysis.resume_id.in_(top_performer_resume_ids)
        )
        top_analyses_result = await db.execute(top_analyses_query)
        top_analyses = {a.resume_id: a for a in top_analyses_result.scalars().all()}

        # Extract candidate metrics
        candidate_metrics = {
            "overall_match_score": candidate_analysis.quality_score if candidate_analysis else 0.0,
            "skills_count": len(candidate_analysis.skills) if candidate_analysis and candidate_analysis.skills else 0,
            "experience_months": candidate_analysis.total_experience_months if candidate_analysis else 0,
        }

        # Extract top performers metrics
        top_performers_metrics = {
            "overall_match_score": [],
            "skills_count": [],
            "experience_months": [],
        }

        top_performers_skills = []
        for tp in top_performers:
            analysis = top_analyses.get(tp.resume_id)
            if analysis:
                top_performers_metrics["overall_match_score"].append(analysis.quality_score or 0.0)
                skills = analysis.skills or []
                top_performers_metrics["skills_count"].append(len(skills))
                top_performers_metrics["experience_months"].append(
                    analysis.total_experience_months or 0
                )
                top_performers_skills.append(skills)

        # Compare metrics
        metrics = []
        for metric_name, candidate_value in candidate_metrics.items():
            metric = self._compare_metric(
                metric_name=metric_name,
                candidate_value=float(candidate_value),
                top_performers_values=top_performers_metrics[metric_name],
            )
            metrics.append(metric)

        # Extract strengths and gaps
        strengths, improvement_areas = self._extract_strengths_and_gaps(metrics)

        # Compare skills
        candidate_skills = candidate_analysis.skills if candidate_analysis and candidate_analysis.skills else []
        competitive_skills, missing_skills = self._compare_skills(
            candidate_skills, top_performers_skills
        )

        # Calculate overall score and tier
        overall_score = self._calculate_overall_score(metrics)
        tier = self._determine_tier(overall_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            improvement_areas, missing_skills, tier
        )

        # Build summary
        role = job_role or "this role"
        summary = self._build_benchmark_summary(tier, overall_score, len(top_performers))

        # Build result
        result = ComparisonResult(
            candidate_resume_id=candidate_resume_id,
            job_role=role,
            top_performers_count=len(top_performers),
            metrics=metrics,
            strengths=strengths,
            improvement_areas=improvement_areas,
            competitive_skills=competitive_skills,
            missing_skills=missing_skills,
            overall_competitiveness_score=overall_score,
            competitiveness_tier=tier,
            recommendations=recommendations,
            benchmark_summary=summary,
        )

        # Record metrics
        duration = time.time() - start_time
        try:
            registry = get_metrics_registry()
            registry.record_ml_inference(
                model_name="resume_comparator",
                operation="compare_against_top_performers",
                duration=duration,
                prediction_type="comparison",
            )
        except Exception as metrics_error:
            logger.debug(f"Failed to record metrics: {metrics_error}")

        logger.info(
            f"Comparison completed for resume {candidate_resume_id}: "
            f"tier={tier}, score={overall_score:.1f}"
        )

        return result


# Singleton instance for convenience
_default_comparator: Optional[ResumeComparator] = None


def get_resume_comparator() -> ResumeComparator:
    """Get or create default resume comparator instance."""
    global _default_comparator
    if _default_comparator is None:
        _default_comparator = ResumeComparator()
    return _default_comparator
