"""
AI-powered Salary Analysis and Benchmarking Service

This module provides intelligent salary benchmarking and compensation suggestions.
It considers multiple factors including:
- Market salary data for roles and locations
- Candidate skills and experience
- Cost-of-living adjustments by geography
- Internal equity considerations
- Historical salary data
"""
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CostOfLivingIndex, JobVacancy, Resume, ResumeAnalysis, SalaryBenchmark, SalaryHistory
from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)


class SalaryFeatures:
    """
    Feature extraction for salary analysis.

    Extracts and computes features used by salary suggestion algorithms.
    """

    # Experience level multipliers for salary adjustments
    EXPERIENCE_MULTIPLIERS = {
        "entry": 0.8,      # 0-2 years
        "junior": 0.9,     # 2-4 years
        "mid": 1.0,        # 4-7 years
        "senior": 1.2,     # 7-10 years
        "lead": 1.4,       # 10-15 years
        "principal": 1.6,  # 15+ years
    }

    # Education level bonuses (as percentage of base salary)
    EDUCATION_BONUS = {
        "phd": 0.15,
        "doctorate": 0.15,
        "master": 0.10,
        "ms": 0.10,
        "m.sc": 0.10,
        "mba": 0.12,
        "bachelor": 0.05,
        "bs": 0.05,
        "b.sc": 0.05,
        "ba": 0.05,
        "diploma": 0.0,
        "associate": 0.0,
        "certificate": 0.0,
        "high_school": 0.0,
        "none": 0.0,
    }

    @classmethod
    def extract_experience_level(cls, experience_months: float) -> str:
        """
        Determine experience level from total months.

        Args:
            experience_months: Total experience in months

        Returns:
            Experience level category
        """
        years = experience_months / 12

        if years < 2:
            return "entry"
        elif years < 4:
            return "junior"
        elif years < 7:
            return "mid"
        elif years < 10:
            return "senior"
        elif years < 15:
            return "lead"
        else:
            return "principal"

    @classmethod
    def compute_experience_multiplier(cls, experience_months: float) -> float:
        """
        Compute salary multiplier based on experience.

        Args:
            experience_months: Total experience in months

        Returns:
            Salary multiplier (0.8 - 1.6)
        """
        level = cls.extract_experience_level(experience_months)
        return cls.EXPERIENCE_MULTIPLIERS.get(level, 1.0)

    @classmethod
    def compute_education_bonus(cls, resume_data: Dict[str, Any]) -> float:
        """
        Compute salary bonus based on education level.

        Args:
            resume_data: Resume data including education

        Returns:
            Bonus as decimal (0.0 - 0.15)
        """
        education = resume_data.get("education", {})
        if isinstance(education, dict):
            degree = education.get("degree", "").lower()
            level = education.get("level", "").lower()
        else:
            degree = str(education).lower()
            level = ""

        # Check degree and level against known values
        for key, value in cls.EDUCATION_BONUS.items():
            if key in degree or key in level:
                return value

        return 0.0

    @classmethod
    def compute_skill_rarity_bonus(cls, resume_data: Dict[str, Any], vacancy_data: Dict[str, Any]) -> float:
        """
        Compute salary bonus based on skill rarity.

        Rarer, more in-demand skills command higher salaries.

        Args:
            resume_data: Resume data with skills
            vacancy_data: Vacancy data with required skills

        Returns:
            Bonus as decimal (0.0 - 0.20)
        """
        resume_skills = set(s.lower() for s in resume_data.get("skills", []))
        required_skills = vacancy_data.get("required_skills", [])

        if not required_skills:
            return 0.0

        # Skills that are often in high demand
        premium_skills = {
            "machine learning", "deep learning", "mlops", "kubernetes",
            "aws", "gcp", "azure", "react", "angular", "vue.js",
            "scala", "golang", "rust", "python", "tensorflow",
            "pytorch", "blockchain", "devops", "site reliability",
            "data engineering", "microservices", "cloud architecture"
        }

        matched_premium = 0
        for skill in required_skills:
            if skill.lower() in resume_skills:
                # Check if it's a premium skill
                if any(premium in skill.lower() for premium in premium_skills):
                    matched_premium += 1

        # Max 20% bonus for premium skills
        ratio = matched_premium / max(len(required_skills), 1)
        return min(ratio * 0.20, 0.20)

    @classmethod
    def get_location_adjustment(cls, location: str, cost_of_living_data: List[Dict[str, Any]]) -> float:
        """
        Get cost-of-living adjustment factor for a location.

        Args:
            location: Location name or "Remote"
            cost_of_living_data: List of cost-of-living index records

        Returns:
            Adjustment factor (e.g., 1.2 for NYC, 0.8 for rural areas)
        """
        if not location or location.lower() == "remote":
            return 1.0  # No adjustment for remote

        location_normalized = location.lower().strip()

        # Find matching cost-of-living data
        for col_record in cost_of_living_data:
            col_location = col_record.get("location", "").lower()
            if col_location in location_normalized or location_normalized in col_location:
                # Convert index to adjustment factor (index 100 = 1.0 factor)
                index = col_record.get("index", 100.0)
                return max(0.5, min(index / 100.0, 2.0))  # Clamp between 0.5 and 2.0

        return 1.0  # Default: no adjustment


class SalaryAnalyzer:
    """
    Main service for salary analysis and benchmarking.

    Coordinates market data, candidate profiles, and compensation logic.
    """

    def __init__(self):
        """Initialize the salary analyzer."""
        self.version = "1.0.0"

    async def get_market_benchmark(
        self,
        db: AsyncSession,
        role: str,
        location: str,
        seniority: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get market salary benchmark for a role and location.

        Args:
            db: Database session
            role: Job title or role
            location: Geographic location or "Remote"
            seniority: Optional seniority level

        Returns:
            Benchmark data with percentiles or None if not found
        """
        try:
            # Query salary benchmarks
            query = select(SalaryBenchmark).where(
                and_(
                    SalaryBenchmark.job_title.ilike(f"%{role}%"),
                    SalaryBenchmark.location.ilike(f"%{location}%"),
                )
            )

            if seniority:
                query = query.where(SalaryBenchmark.experience_level == seniority)

            # Order by data_source_priority and updated_at
            query = query.order_by(SalaryBenchmark.updated_at.desc())

            result = await db.execute(query)
            benchmark = result.scalar_one_or_none()

            if not benchmark:
                logger.warning(f"No benchmark found for role={role}, location={location}")
                return None

            return {
                "role": benchmark.job_title,
                "location": benchmark.location,
                "seniority": benchmark.experience_level,
                "currency": benchmark.currency,
                "min_salary": float(benchmark.salary_min),
                "median_salary": float(benchmark.salary_median),
                "max_salary": float(benchmark.salary_max),
                "sample_size": benchmark.sample_size,
                "data_source": benchmark.data_source,
                "updated_at": benchmark.updated_at.isoformat() if benchmark.updated_at else None,
            }

        except Exception as e:
            logger.error(f"Error fetching market benchmark: {e}", exc_info=True)
            return None

    async def suggest_salary_range(
        self,
        db: AsyncSession,
        resume_id: UUID,
        vacancy_id: UUID,
    ) -> Dict[str, Any]:
        """
        Suggest salary range for a candidate applying to a vacancy.

        Args:
            db: Database session
            resume_id: Resume UUID
            vacancy_id: JobVacancy UUID

        Returns:
            Salary suggestion with breakdown
        """
        start_time = datetime.now()

        try:
            # Fetch resume data
            resume_query = select(Resume).where(Resume.id == resume_id)
            resume_result = await db.execute(resume_query)
            resume = resume_result.scalar_one_or_none()

            if not resume:
                raise ValueError(f"Resume not found: {resume_id}")

            # Fetch vacancy data
            vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_id)
            vacancy_result = await db.execute(vacancy_query)
            vacancy = vacancy_result.scalar_one_or_none()

            if not vacancy:
                raise ValueError(f"Vacancy not found: {vacancy_id}")

            # Get resume analysis for skills and experience
            analysis_query = select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)
            analysis_result = await db.execute(analysis_query)
            analysis = analysis_result.scalar_one_or_none()

            # Prepare resume data
            resume_data = {
                "skills": analysis.skills if analysis else [],
                "experience": {},
                "education": {},
                "title": resume.raw_text[:100] if resume.raw_text else "",
            }

            # Extract experience months if available
            if analysis and analysis.total_experience_months:
                resume_data["experience"] = {
                    "total_months": analysis.total_experience_months,
                }

            # Prepare vacancy data
            vacancy_data = {
                "title": vacancy.title,
                "required_skills": vacancy.required_skills or [],
                "min_salary": float(vacancy.min_salary) if vacancy.min_salary else None,
                "max_salary": float(vacancy.max_salary) if vacancy.max_salary else None,
                "location": vacancy.location or "Remote",
            }

            # Get market benchmark
            location = vacancy_data["location"]
            benchmark = await self.get_market_benchmark(
                db, vacancy_data["title"], location
            )

            # Get cost-of-living data
            col_query = select(CostOfLivingIndex).where(
                CostOfLivingIndex.location.ilike(f"%{location}%")
            )
            col_result = await db.execute(col_query)
            col_records = col_result.scalars().all()

            cost_of_living_data = [
                {
                    "location": r.location,
                    "index": float(r.index),
                    "category": r.category,
                }
                for r in col_records
            ]

            # Get candidate's salary history
            history_query = select(SalaryHistory).where(
                SalaryHistory.resume_id == resume_id
            ).order_by(SalaryHistory.effective_date.desc())

            history_result = await db.execute(history_query)
            history_records = history_result.scalars().all()

            current_salary = None
            if history_records:
                current_salary = float(history_records[0].annual_salary)

            # Compute salary suggestion
            suggestion = self._compute_salary_suggestion(
                resume_data=resume_data,
                vacancy_data=vacancy_data,
                benchmark=benchmark,
                cost_of_living_data=cost_of_living_data,
                current_salary=current_salary,
            )

            duration = (datetime.now() - start_time).total_seconds()

            # Record metrics
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name="salary_analyzer",
                    operation="suggest_salary_range",
                    duration=duration,
                    prediction_type="salary_range",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            return suggestion

        except Exception as e:
            logger.error(f"Error suggesting salary range: {e}", exc_info=True)
            raise

    def _compute_salary_suggestion(
        self,
        resume_data: Dict[str, Any],
        vacancy_data: Dict[str, Any],
        benchmark: Optional[Dict[str, Any]],
        cost_of_living_data: List[Dict[str, Any]],
        current_salary: Optional[float],
    ) -> Dict[str, Any]:
        """
        Compute salary suggestion based on multiple factors.

        Args:
            resume_data: Candidate resume data
            vacancy_data: Job vacancy data
            benchmark: Market benchmark data
            cost_of_living_data: Cost-of-living indices
            current_salary: Candidate's current salary

        Returns:
            Salary suggestion with breakdown
        """
        # Start with benchmark or vacancy salary range
        if benchmark:
            base_min = benchmark["min_salary"]
            base_max = benchmark["max_salary"]
            base_median = benchmark["median_salary"]
        elif vacancy_data.get("min_salary") and vacancy_data.get("max_salary"):
            base_min = vacancy_data["min_salary"]
            base_max = vacancy_data["max_salary"]
            base_median = (base_min + base_max) / 2
        else:
            # Fallback: use industry default
            base_min = 60000
            base_max = 120000
            base_median = 90000

        # Get experience multiplier
        exp_months = resume_data.get("experience", {}).get("total_months", 0)
        exp_multiplier = SalaryFeatures.compute_experience_multiplier(exp_months)

        # Get education bonus
        edu_bonus = SalaryFeatures.compute_education_bonus(resume_data)

        # Get skill rarity bonus
        skill_bonus = SalaryFeatures.compute_skill_rarity_bonus(resume_data, vacancy_data)

        # Get location adjustment
        location = vacancy_data.get("location", "Remote")
        location_adj = SalaryFeatures.get_location_adjustment(location, cost_of_living_data)

        # Calculate total adjustment factor
        total_multiplier = exp_multiplier * location_adj
        total_bonus = edu_bonus + skill_bonus

        # Apply adjustments to base salary
        suggested_min = base_min * total_multiplier * (1 + total_bonus)
        suggested_max = base_max * total_multiplier * (1 + total_bonus)
        suggested_median = base_median * total_multiplier * (1 + total_bonus)

        # Ensure reasonable range (min >= 80% of median, max <= 150% of median)
        suggested_min = max(suggested_min, suggested_median * 0.8)
        suggested_max = min(suggested_max, suggested_median * 1.5)

        # Consider current salary (don't suggest less than 10% increase from current)
        if current_salary:
            suggested_min = max(suggested_min, current_salary * 1.05)
            suggested_median = max(suggested_median, current_salary * 1.10)

        # Round to nearest thousand
        suggested_min = round(suggested_min / 1000) * 1000
        suggested_median = round(suggested_median / 1000) * 1000
        suggested_max = round(suggested_max / 1000) * 1000

        return {
            "suggested_range": {
                "min": suggested_min,
                "median": suggested_median,
                "max": suggested_max,
            },
            "breakdown": {
                "base_benchmark": {
                    "min": base_min,
                    "median": base_median,
                    "max": base_max,
                },
                "adjustments": {
                    "experience_multiplier": exp_multiplier,
                    "education_bonus": edu_bonus,
                    "skill_rarity_bonus": skill_bonus,
                    "location_adjustment": location_adj,
                    "total_multiplier": total_multiplier,
                    "total_bonus": total_bonus,
                },
                "current_salary_considered": current_salary is not None,
                "current_salary": current_salary,
            },
            "location": location,
            "currency": "USD",
            "confidence": self._compute_confidence(benchmark, resume_data),
            "recommendation": self._salary_to_recommendation(suggested_median, current_salary),
        }

    def _compute_confidence(
        self,
        benchmark: Optional[Dict[str, Any]],
        resume_data: Dict[str, Any],
    ) -> str:
        """
        Compute confidence level for the suggestion.

        Args:
            benchmark: Market benchmark data
            resume_data: Candidate resume data

        Returns:
            Confidence level (low, medium, high)
        """
        score = 0

        # High confidence if we have good benchmark data
        if benchmark and benchmark.get("sample_size", 0) > 100:
            score += 2
        elif benchmark:
            score += 1

        # High confidence if resume is complete
        if resume_data.get("skills") and len(resume_data["skills"]) > 5:
            score += 1

        if resume_data.get("experience", {}).get("total_months", 0) > 0:
            score += 1

        if score >= 3:
            return "high"
        elif score >= 2:
            return "medium"
        return "low"

    def _salary_to_recommendation(
        self,
        suggested_salary: float,
        current_salary: Optional[float],
    ) -> str:
        """
        Convert suggested salary to recommendation text.

        Args:
            suggested_salary: Suggested median salary
            current_salary: Candidate's current salary

        Returns:
            Recommendation text
        """
        if current_salary:
            increase_pct = ((suggested_salary - current_salary) / current_salary) * 100

            if increase_pct > 20:
                return "competitive_offer"
            elif increase_pct > 10:
                return "fair_offer"
            elif increase_pct > 0:
                return "modest_increase"
            else:
                return "below_current"
        else:
            # No current salary data, give general recommendation
            if suggested_salary > 100000:
                return "competitive_offer"
            elif suggested_salary > 75000:
                return "fair_offer"
            else:
                return "entry_level"

    async def compare_offers(
        self,
        db: AsyncSession,
        resume_id: UUID,
        offers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compare multiple salary offers adjusting for cost-of-living.

        Args:
            db: Database session
            resume_id: Resume UUID
            offers: List of offers with salary and location

        Returns:
            Comparison analysis with normalized salaries
        """
        try:
            # Fetch resume for current salary
            history_query = select(SalaryHistory).where(
                SalaryHistory.resume_id == resume_id
            ).order_by(SalaryHistory.effective_date.desc())

            history_result = await db.execute(history_query)
            history_records = history_result.scalars().all()

            current_salary = None
            if history_records:
                current_salary = float(history_records[0].annual_salary)

            # Get cost-of-living data for all offer locations
            locations = [offer.get("location", "Remote") for offer in offers]
            cost_of_living_data = []

            for location in locations:
                if location.lower() != "remote":
                    col_query = select(CostOfLivingIndex).where(
                        CostOfLivingIndex.location.ilike(f"%{location}%")
                    )
                    col_result = await db.execute(col_query)
                    col_records = col_result.scalars().all()

                    for r in col_records:
                        cost_of_living_data.append({
                            "location": r.location,
                            "index": float(r.index),
                            "category": r.category,
                        })

            # Normalize all offers
            normalized_offers = []
            for offer in offers:
                salary = offer.get("salary", 0)
                location = offer.get("location", "Remote")

                # Get location adjustment
                location_adj = SalaryFeatures.get_location_adjustment(location, cost_of_living_data)

                # Normalize to national average (divide by location factor)
                normalized_salary = salary / location_adj if location_adj > 0 else salary

                normalized_offers.append({
                    "original_salary": salary,
                    "location": location,
                    "location_adjustment": location_adj,
                    "normalized_salary": normalized_salary,
                    "is_remote": location.lower() == "remote",
                })

            # Sort by normalized salary
            normalized_offers.sort(key=lambda x: x["normalized_salary"], reverse=True)

            # Find best offer
            best_offer = normalized_offers[0] if normalized_offers else None

            return {
                "current_salary": current_salary,
                "offers": normalized_offers,
                "best_offer": best_offer,
                "recommendation": self._compare_to_current(best_offer, current_salary) if best_offer else None,
            }

        except Exception as e:
            logger.error(f"Error comparing offers: {e}", exc_info=True)
            raise

    def _compare_to_current(
        self,
        best_offer: Dict[str, Any],
        current_salary: Optional[float],
    ) -> Optional[str]:
        """
        Compare best offer to current salary.

        Args:
            best_offer: Best normalized offer
            current_salary: Current salary

        Returns:
            Comparison recommendation
        """
        if not current_salary:
            return None

        normalized_salary = best_offer["normalized_salary"]
        increase_pct = ((normalized_salary - current_salary) / current_salary) * 100

        if increase_pct > 15:
            return "significant_increase"
        elif increase_pct > 5:
            return "moderate_increase"
        elif increase_pct > 0:
            return "small_increase"
        else:
            return "decrease"


# Global service instance
_salary_analyzer: Optional[SalaryAnalyzer] = None


def get_salary_analyzer() -> SalaryAnalyzer:
    """Get or create global salary analyzer instance."""
    global _salary_analyzer
    if _salary_analyzer is None:
        _salary_analyzer = SalaryAnalyzer()
    return _salary_analyzer
