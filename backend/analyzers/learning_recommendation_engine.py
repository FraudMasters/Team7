"""
Learning recommendation engine for matching skills to courses and resources.

This module provides comprehensive learning recommendations that:
1. Match missing skills to relevant courses and resources
2. Rank recommendations by quality, relevance, and accessibility
3. Support multiple resource types (courses, certifications, tutorials)
4. Consider cost, time investment, and skill level requirements
5. Provide diverse options from various learning platforms

The engine uses skill matching and ranking algorithms to provide
personalized learning recommendations for skill development.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .skill_gap_analyzer import SkillGapResult

logger = logging.getLogger(__name__)


@dataclass
class LearningRecommendation:
    """
    Individual learning resource recommendation.

    Attributes:
        skill: Target skill this resource addresses
        resource_type: Type of resource (course, certification, tutorial, book, etc.)
        title: Resource title
        description: Brief description of the resource
        provider: Platform or provider name (e.g., Coursera, Udemy, freeCodeCamp)
        url: Direct URL to the resource
        skill_level: Required/provided skill level (beginner, intermediate, advanced)
        duration_hours: Estimated time to complete (in hours)
        duration_weeks: Estimated time to complete (in weeks)
        cost_amount: Cost in currency (0 for free resources)
        currency: Currency code (USD, EUR, etc.)
        access_type: Access type (free, paid, freemium, subscription)
        rating: Average rating (0-5)
        rating_count: Number of ratings
        topics_covered: List of topics covered in the resource
        prerequisites: Required prior knowledge/skills
        certificate_offered: Whether completion certificate is offered
        difficulty_level: Perceived difficulty (1-5)
        relevance_score: How relevant to the target skill (0-1)
        quality_score: Overall quality assessment (0-1)
        popularity_score: How popular/widely used (0-1)
        priority_score: Combined score for ranking (0-1)
        language: Resource language
        is_self_paced: Whether resource is self-paced
    """

    # Skill matching
    skill: str = ""
    resource_type: str = "course"  # course, certification, tutorial, book, video, article
    title: str = ""
    description: str = ""
    provider: str = ""
    url: str = ""

    # Content details
    skill_level: str = "intermediate"  # beginner, intermediate, advanced, expert
    topics_covered: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    language: str = "en"
    is_self_paced: bool = True

    # Time investment
    duration_hours: float = 0.0
    duration_weeks: float = 0.0

    # Cost and access
    cost_amount: float = 0.0
    currency: str = "USD"
    access_type: str = "free"  # free, paid, freemium, subscription

    # Quality metrics
    rating: float = 0.0
    rating_count: int = 0
    certificate_offered: bool = False
    difficulty_level: int = 3  # 1-5 scale

    # Computed scores
    relevance_score: float = 0.0  # 0-1, how well it matches the skill
    quality_score: float = 0.0  # 0-1, based on ratings and reviews
    popularity_score: float = 0.0  # 0-1, based on enrollment and engagement
    priority_score: float = 0.0  # 0-1, combined ranking score

    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to dictionary for JSON serialization."""
        return {
            "skill": self.skill,
            "resource_type": self.resource_type,
            "title": self.title,
            "description": self.description,
            "provider": self.provider,
            "url": self.url,
            "skill_level": self.skill_level,
            "topics_covered": self.topics_covered,
            "prerequisites": self.prerequisites,
            "language": self.language,
            "is_self_paced": self.is_self_paced,
            "duration_hours": self.duration_hours,
            "duration_weeks": self.duration_weeks,
            "cost_amount": self.cost_amount,
            "currency": self.currency,
            "access_type": self.access_type,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "certificate_offered": self.certificate_offered,
            "difficulty_level": self.difficulty_level,
            "relevance_score": round(self.relevance_score, 4),
            "quality_score": round(self.quality_score, 4),
            "popularity_score": round(self.popularity_score, 4),
            "priority_score": round(self.priority_score, 4),
        }


@dataclass
class LearningRecommendationResult:
    """
    Comprehensive result from learning recommendation analysis.

    Attributes:
        target_skills: Skills that need recommendations
        recommendations: List of recommended resources grouped by skill
        total_recommendations: Total number of recommendations
        total_cost: Sum of costs for all recommended resources
        total_duration_hours: Total hours to complete all recommendations
        alternative_free_resources: Count of free alternatives available
        skills_with_certifications: Skills that offer certification options
        priority_ordering: Recommended order to address skills
        summary: Brief summary of recommendations
    """

    # Input
    target_skills: List[str] = field(default_factory=list)

    # Recommendations
    recommendations: Dict[str, List[LearningRecommendation]] = field(
        default_factory=dict
    )

    # Aggregated metrics
    total_recommendations: int = 0
    total_cost: float = 0.0
    total_duration_hours: float = 0.0

    # Alternative options
    alternative_free_resources: int = 0
    skills_with_certifications: List[str] = field(default_factory=list)

    # Priority ordering
    priority_ordering: List[str] = field(default_factory=list)

    # Summary
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "target_skills": self.target_skills,
            "recommendations": {
                skill: [rec.to_dict() for rec in recs]
                for skill, recs in self.recommendations.items()
            },
            "total_recommendations": self.total_recommendations,
            "total_cost": round(self.total_cost, 2),
            "total_duration_hours": round(self.total_duration_hours, 2),
            "alternative_free_resources": self.alternative_free_resources,
            "skills_with_certifications": self.skills_with_certifications,
            "priority_ordering": self.priority_ordering,
            "summary": self.summary,
        }


class LearningRecommendationEngine:
    """
    Engine for recommending learning resources based on skill gaps.

    Uses skill gap analysis results to find and rank relevant learning
    resources from various platforms including Coursera, Udemy, edX,
    freeCodeCamp, and other free resources.

    The ranking considers:
    - Relevance to the target skill
    - Quality (ratings, reviews, provider reputation)
    - Accessibility (cost, time, prerequisites)
    - Learning outcomes (certifications, practical projects)

    Example:
        >>> engine = LearningRecommendationEngine()
        >>> result = engine.recommend_for_skill_gaps(
        ...     skill_gap_result=skill_gap_result,
        ...     max_recommendations_per_skill=5,
        ...     include_free_resources=True,
        ...     max_cost_per_resource=100
        ... )
        >>> print(result.recommendations.keys())
        dict_keys(['React', 'AWS', 'Docker'])
        >>> print(result.total_cost)
        150.0
        >>> print(result.summary)
        'Found 12 resources for 3 skills with total cost of $150.00'
    """

    def __init__(
        self,
        # Recommendation limits
        max_recommendations_per_skill: int = 5,
        max_cost_per_resource: float = 200.0,
        max_duration_per_resource: float = 100.0,  # hours

        # Ranking weights
        relevance_weight: float = 0.4,
        quality_weight: float = 0.3,
        accessibility_weight: float = 0.2,
        outcome_weight: float = 0.1,

        # Resource preferences
        prefer_free_resources: bool = True,
        prefer_certified_courses: bool = False,
        prefer_self_paced: bool = True,

        # Use mock data for development
        use_mock_data: bool = True,
    ):
        """
        Initialize the learning recommendation engine.

        Args:
            max_recommendations_per_skill: Maximum recommendations to return per skill
            max_cost_per_resource: Maximum cost for a single resource
            max_duration_per_resource: Maximum duration for a single resource (hours)
            relevance_weight: Weight for relevance in ranking (0-1)
            quality_weight: Weight for quality in ranking (0-1)
            accessibility_weight: Weight for accessibility (cost/time) in ranking (0-1)
            outcome_weight: Weight for learning outcomes (certifications) in ranking (0-1)
            prefer_free_resources: Whether to prioritize free resources
            prefer_certified_courses: Whether to prioritize courses with certificates
            prefer_self_paced: Whether to prioritize self-paced resources
            use_mock_data: Whether to use mock data (for development/testing)
        """
        self.max_recommendations_per_skill = max_recommendations_per_skill
        self.max_cost_per_resource = max_cost_per_resource
        self.max_duration_per_resource = max_duration_per_resource

        self.relevance_weight = relevance_weight
        self.quality_weight = quality_weight
        self.accessibility_weight = accessibility_weight
        self.outcome_weight = outcome_weight

        self.prefer_free_resources = prefer_free_resources
        self.prefer_certified_courses = prefer_certified_courses
        self.prefer_self_paced = prefer_self_paced

        self.use_mock_data = use_mock_data

        # Initialize mock resource database
        if use_mock_data:
            self._mock_resources = self._initialize_mock_resources()

        logger.info(
            f"LearningRecommendationEngine initialized with "
            f"max_recommendations={max_recommendations_per_skill}, "
            f"max_cost={max_cost_per_resource}"
        )

    def recommend_for_skill_gaps(
        self,
        skill_gap_result: SkillGapResult,
        max_recommendations_per_skill: Optional[int] = None,
        include_free_resources: bool = True,
        include_paid_resources: bool = True,
        max_cost_per_resource: Optional[float] = None,
        skill_level_requirements: Optional[Dict[str, str]] = None,
        priority_ordering: Optional[List[str]] = None,
    ) -> LearningRecommendationResult:
        """
        Generate learning recommendations based on skill gap analysis.

        Args:
            skill_gap_result: Result from skill gap analysis
            max_recommendations_per_skill: Override max recommendations per skill
            include_free_resources: Whether to include free resources
            include_paid_resources: Whether to include paid resources
            max_cost_per_resource: Override maximum cost per resource
            skill_level_requirements: Required level for each skill
            priority_ordering: Priority order for addressing skills

        Returns:
            LearningRecommendationResult with comprehensive recommendations
        """
        # Get skills that need recommendations (missing + partial matches)
        target_skills = skill_gap_result.missing_skills + skill_gap_result.partial_match_skills

        if not target_skills:
            return self._create_empty_result("No skill gaps found - all requirements met!")

        # Use priority ordering from skill gap result or provided parameter
        priority_ordering = priority_ordering or skill_gap_result.priority_ordering

        # Get required skill levels from gap result
        if skill_level_requirements is None:
            skill_level_requirements = {}
            for skill, details in skill_gap_result.missing_skill_details.items():
                skill_level_requirements[skill] = details.get("required_level", "intermediate")

        # Generate recommendations for each skill
        recommendations = {}
        total_cost = 0.0
        total_duration = 0.0
        total_count = 0
        free_resource_count = 0
        skills_with_certs = []

        max_rec = max_recommendations_per_skill or self.max_recommendations_per_skill
        max_cost = max_cost_per_resource or self.max_cost_per_resource

        for skill in target_skills:
            required_level = skill_level_requirements.get(skill, "intermediate")

            # Get resources for this skill
            resources = self._get_resources_for_skill(
                skill=skill,
                required_level=required_level,
                include_free=include_free_resources,
                include_paid=include_paid_resources,
                max_cost=max_cost,
            )

            # Rank and filter resources
            ranked_resources = self._rank_and_filter_resources(
                resources=resources,
                skill=skill,
                required_level=required_level,
                max_count=max_rec,
            )

            if ranked_resources:
                recommendations[skill] = ranked_resources

                # Track metrics
                for resource in ranked_resources:
                    total_count += 1
                    total_cost += resource.cost_amount
                    total_duration += resource.duration_hours
                    if resource.cost_amount == 0:
                        free_resource_count += 1
                    if resource.certificate_offered and skill not in skills_with_certs:
                        skills_with_certs.append(skill)

        # Generate summary
        if total_count > 0:
            avg_cost = total_cost / total_count
            summary = (
                f"Found {total_count} learning resources for {len(target_skills)} skills. "
                f"Total estimated cost: ${total_cost:.2f} "
                f"(avg ${avg_cost:.2f} per resource), "
                f"total time: {total_duration:.0f} hours. "
                f"Free resources: {free_resource_count}."
            )
        else:
            summary = f"No matching resources found for {len(target_skills)} skills."

        return LearningRecommendationResult(
            target_skills=target_skills,
            recommendations=recommendations,
            total_recommendations=total_count,
            total_cost=total_cost,
            total_duration_hours=total_duration,
            alternative_free_resources=free_resource_count,
            skills_with_certifications=skills_with_certs,
            priority_ordering=priority_ordering,
            summary=summary,
        )

    def recommend_for_skill(
        self,
        skill: str,
        skill_level: str = "intermediate",
        max_recommendations: int = 5,
        include_free: bool = True,
        include_paid: bool = True,
        max_cost: float = 200.0,
    ) -> List[LearningRecommendation]:
        """
        Get recommendations for a single skill.

        Args:
            skill: Skill to find resources for
            skill_level: Required skill level
            max_recommendations: Maximum recommendations to return
            include_free: Whether to include free resources
            include_paid: Whether to include paid resources
            max_cost: Maximum cost per resource

        Returns:
            List of LearningRecommendation objects
        """
        # Get resources for this skill
        resources = self._get_resources_for_skill(
            skill=skill,
            required_level=skill_level,
            include_free=include_free,
            include_paid=include_paid,
            max_cost=max_cost,
        )

        # Rank and filter
        ranked_resources = self._rank_and_filter_resources(
            resources=resources,
            skill=skill,
            required_level=skill_level,
            max_count=max_recommendations,
        )

        return ranked_resources

    def _get_resources_for_skill(
        self,
        skill: str,
        required_level: str = "intermediate",
        include_free: bool = True,
        include_paid: bool = True,
        max_cost: float = 200.0,
    ) -> List[LearningRecommendation]:
        """
        Get all available resources for a specific skill.

        Args:
            skill: Target skill
            required_level: Required skill level
            include_free: Whether to include free resources
            include_paid: Whether to include paid resources
            max_cost: Maximum cost threshold

        Returns:
            List of learning resources for the skill
        """
        resources = []

        if self.use_mock_data:
            # Get mock resources matching the skill
            resources = self._get_mock_resources_for_skill(skill)
        else:
            # TODO: Integrate with actual learning platform APIs
            # For now, return empty list - will be implemented in future subtasks
            logger.warning(f"No external resource integration configured for skill: {skill}")
            return []

        # Filter by criteria
        filtered_resources = []
        for resource in resources:
            # Filter by cost
            if resource.cost_amount == 0 and not include_free:
                continue
            if resource.cost_amount > 0 and not include_paid:
                continue
            if resource.cost_amount > max_cost:
                continue

            # Filter by skill level compatibility
            if not self._is_skill_level_compatible(
                resource_level=resource.skill_level,
                required_level=required_level,
            ):
                continue

            filtered_resources.append(resource)

        return filtered_resources

    def _rank_and_filter_resources(
        self,
        resources: List[LearningRecommendation],
        skill: str,
        required_level: str,
        max_count: int,
    ) -> List[LearningRecommendation]:
        """
        Rank resources by relevance and quality, then return top N.

        Args:
            resources: List of resources to rank
            skill: Target skill
            required_level: Required skill level
            max_count: Maximum number of resources to return

        Returns:
            Ranked and filtered list of resources
        """
        if not resources:
            return []

        # Calculate scores for each resource
        for resource in resources:
            resource.relevance_score = self._calculate_relevance_score(
                resource=resource,
                target_skill=skill,
                required_level=required_level,
            )

            resource.quality_score = self._calculate_quality_score(resource)

            resource.accessibility_score = self._calculate_accessibility_score(
                resource=resource,
                required_level=required_level,
            )

            resource.outcome_score = self._calculate_outcome_score(resource)

            # Calculate combined priority score
            resource.priority_score = (
                resource.relevance_score * self.relevance_weight
                + resource.quality_score * self.quality_weight
                + resource.accessibility_score * self.accessibility_weight
                + resource.outcome_score * self.outcome_weight
            )

        # Sort by priority score descending
        ranked_resources = sorted(
            resources, key=lambda r: r.priority_score, reverse=True
        )

        # Return top N
        return ranked_resources[:max_count]

    def _calculate_relevance_score(
        self,
        resource: LearningRecommendation,
        target_skill: str,
        required_level: str,
    ) -> float:
        """
        Calculate how relevant a resource is to the target skill.

        Args:
            resource: Learning resource
            target_skill: Target skill to learn
            required_level: Required skill level

        Returns:
            Relevance score from 0-1
        """
        score = 0.0

        # Base relevance from skill matching
        if target_skill.lower() in resource.title.lower():
            score += 0.4
        if target_skill.lower() in resource.description.lower():
            score += 0.2

        # Topic coverage
        if target_skill.lower() in [t.lower() for t in resource.topics_covered]:
            score += 0.2

        # Skill level matching
        if resource.skill_level == required_level:
            score += 0.2
        elif self._is_skill_level_compatible(resource.skill_level, required_level):
            score += 0.1

        return min(score, 1.0)

    def _calculate_quality_score(self, resource: LearningRecommendation) -> float:
        """
        Calculate quality score based on ratings and provider reputation.

        Args:
            resource: Learning resource

        Returns:
            Quality score from 0-1
        """
        score = 0.0

        # Rating component (0-0.5)
        if resource.rating > 0:
            # Normalize rating from 0-5 to 0-0.5
            score += (resource.rating / 5.0) * 0.5

        # Rating count component (more ratings = more reliable, 0-0.3)
        if resource.rating_count > 0:
            # Logarithmic scale for rating count
            import math

            normalized_count = min(math.log10(resource.rating_count + 1) / 4, 1.0)
            score += normalized_count * 0.3

        # Provider reputation (0-0.2)
        reputable_providers = [
            "coursera",
            "edx",
            "udacity",
            "pluralsight",
            "freecodecamp",
            "udemy",
        ]
        if resource.provider.lower() in reputable_providers:
            score += 0.2

        return min(score, 1.0)

    def _calculate_accessibility_score(
        self,
        resource: LearningRecommendation,
        required_level: str,
    ) -> float:
        """
        Calculate accessibility score based on cost, time, and prerequisites.

        Args:
            resource: Learning resource
            required_level: Required skill level

        Returns:
            Accessibility score from 0-1 (higher = more accessible)
        """
        score = 0.0

        # Cost component (0-0.4)
        if resource.cost_amount == 0:
            score += 0.4  # Free is most accessible
        else:
            # Decreasing score with cost
            cost_penalty = min(resource.cost_amount / self.max_cost_per_resource, 1.0)
            score += 0.4 * (1.0 - cost_penalty)

        # Time component (0-0.3)
        if resource.duration_hours > 0:
            # Shorter is more accessible
            time_penalty = min(
                resource.duration_hours / self.max_duration_per_resource, 1.0
            )
            score += 0.3 * (1.0 - time_penalty)
        else:
            score += 0.15  # Neutral if unknown

        # Self-paced bonus (0-0.15)
        if resource.is_self_paced:
            score += 0.15

        # Prerequisites component (0-0.15)
        if not resource.prerequisites:
            score += 0.15  # No prerequisites is most accessible
        else:
            # Fewer prerequisites is better
            prereq_penalty = min(len(resource.prerequisites) * 0.05, 0.15)
            score += 0.15 - prereq_penalty

        return min(score, 1.0)

    def _calculate_outcome_score(self, resource: LearningRecommendation) -> float:
        """
        Calculate outcome score based on certifications and practical value.

        Args:
            resource: Learning resource

        Returns:
            Outcome score from 0-1
        """
        score = 0.0

        # Certificate bonus (0-0.6)
        if resource.certificate_offered:
            score += 0.6

        # Resource type value (0-0.4)
        type_values = {
            "certification": 0.4,
            "course": 0.3,
            "bootcamp": 0.35,
            "tutorial": 0.2,
            "book": 0.15,
            "video": 0.15,
            "article": 0.1,
        }
        score += type_values.get(resource.resource_type.lower(), 0.15)

        return min(score, 1.0)

    def _is_skill_level_compatible(
        self, resource_level: str, required_level: str
    ) -> bool:
        """
        Check if resource level is compatible with required level.

        Args:
            resource_level: Level taught by resource
            required_level: Level required by job

        Returns:
            True if resource can help achieve required level
        """
        level_rank = {
            "beginner": 1,
            "intermediate": 2,
            "advanced": 3,
            "expert": 4,
        }

        resource_rank = level_rank.get(resource_level.lower(), 2)
        required_rank = level_rank.get(required_level.lower(), 2)

        # Resource should be at or above required level
        # or one level below (for building up)
        return resource_rank >= required_rank or resource_rank == required_rank - 1

    def _create_empty_result(self, message: str) -> LearningRecommendationResult:
        """Create an empty result with a message."""
        return LearningRecommendationResult(
            target_skills=[],
            recommendations={},
            total_recommendations=0,
            total_cost=0.0,
            total_duration_hours=0.0,
            alternative_free_resources=0,
            skills_with_certifications=[],
            priority_ordering=[],
            summary=message,
        )

    def _initialize_mock_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Initialize mock resource database for development/testing.

        Returns:
            Dictionary mapping skill names to resource data
        """
        return {
            "python": [
                {
                    "title": "Complete Python Bootcamp: Go from Zero to Hero",
                    "provider": "Udemy",
                    "url": "https://www.udemy.com/complete-python-bootcamp",
                    "description": "Learn Python like a professional. Start from basics and go all the way to creating your own applications and games.",
                    "skill_level": "beginner",
                    "duration_hours": 22.0,
                    "cost_amount": 15.0,
                    "rating": 4.6,
                    "rating_count": 250000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "course",
                    "topics_covered": ["Python", "Programming", "Data Types", "OOP", "File Handling"],
                    "prerequisites": [],
                },
                {
                    "title": "Python for Everybody Specialization",
                    "provider": "Coursera",
                    "url": "https://www.coursera.org/specializations/python",
                    "description": "Learn to Program and Analyze Data with Python. Develop programs to gather, clean, analyze, and visualize data.",
                    "skill_level": "beginner",
                    "duration_hours": 32.0,
                    "cost_amount": 49.0,
                    "rating": 4.8,
                    "rating_count": 120000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "course",
                    "topics_covered": ["Python", "Data Analysis", "Web Scraping", "Databases", "JSON"],
                    "prerequisites": [],
                },
                {
                    "title": "freeCodeCamp Python Certification",
                    "provider": "freeCodeCamp",
                    "url": "https://www.freecodecamp.org/learn/data-analysis-with-python",
                    "description": "Free Python certification covering data analysis, visualization, and machine learning basics.",
                    "skill_level": "intermediate",
                    "duration_hours": 30.0,
                    "cost_amount": 0.0,
                    "rating": 4.7,
                    "rating_count": 45000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "certification",
                    "topics_covered": ["Python", "Data Analysis", "Pandas", "NumPy", "Visualization"],
                    "prerequisites": ["Basic Python"],
                },
            ],
            "javascript": [
                {
                    "title": "JavaScript - The Complete Guide 2024",
                    "provider": "Udemy",
                    "url": "https://www.udemy.com/javascript-the-complete-guide",
                    "description": "Master modern JavaScript from scratch. Build real projects and understand core concepts deeply.",
                    "skill_level": "intermediate",
                    "duration_hours": 42.0,
                    "cost_amount": 20.0,
                    "rating": 4.7,
                    "rating_count": 98000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "course",
                    "topics_covered": ["JavaScript", "ES6+", "DOM", "Async", "OOP", "Modules"],
                    "prerequisites": ["Basic HTML/CSS"],
                },
                {
                    "title": "JavaScript Algorithms and Data Structures",
                    "provider": "freeCodeCamp",
                    "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures",
                    "description": "Free interactive course covering JavaScript fundamentals, algorithms, and data structures.",
                    "skill_level": "beginner",
                    "duration_hours": 40.0,
                    "cost_amount": 0.0,
                    "rating": 4.8,
                    "rating_count": 78000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "certification",
                    "topics_covered": ["JavaScript", "ES6", "Algorithms", "Data Structures", "Regex"],
                    "prerequisites": [],
                },
            ],
            "react": [
                {
                    "title": "React - The Complete Guide (incl Hooks, React Router, Redux)",
                    "provider": "Udemy",
                    "url": "https://www.udemy.com/react-the-complete-guide",
                    "description": "Dive in and learn React.js from scratch! Learn React, Hooks, Redux, React Router, Next.js and way more!",
                    "skill_level": "intermediate",
                    "duration_hours": 48.0,
                    "cost_amount": 25.0,
                    "rating": 4.7,
                    "rating_count": 180000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "course",
                    "topics_covered": ["React", "Hooks", "Redux", "React Router", "Next.js"],
                    "prerequisites": ["JavaScript", "HTML/CSS"],
                },
                {
                    "title": "Front-End Development Libraries",
                    "provider": "freeCodeCamp",
                    "url": "https://www.freecodecamp.org/learn/front-end-development-libraries",
                    "description": "Learn React, Redux, and React Router through hands-on projects.",
                    "skill_level": "intermediate",
                    "duration_hours": 35.0,
                    "cost_amount": 0.0,
                    "rating": 4.6,
                    "rating_count": 32000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "certification",
                    "topics_covered": ["React", "Redux", "React Router", "Bootstrap", "jQuery"],
                    "prerequisites": ["JavaScript"],
                },
            ],
            "aws": [
                {
                    "title": "AWS Certified Solutions Architect - Associate",
                    "provider": "Udemy",
                    "url": "https://www.udemy.com/aws-certified-solutions-architect-associate",
                    "description": "Complete Amazon Web Services Certified Solutions Architect Associate preparation course.",
                    "skill_level": "intermediate",
                    "duration_hours": 28.0,
                    "cost_amount": 20.0,
                    "rating": 4.7,
                    "rating_count": 145000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "course",
                    "topics_covered": ["AWS", "EC2", "S3", "Lambda", "VPC", "IAM", "RDS"],
                    "prerequisites": ["Basic networking knowledge"],
                },
                {
                    "title": "AWS Cloud Practitioner Essentials",
                    "provider": "Coursera",
                    "url": "https://www.coursera.org/learn/aws-cloud-practitioner-essentials",
                    "description": "Fundamental AWS cloud concepts and services. Perfect starting point for AWS journey.",
                    "skill_level": "beginner",
                    "duration_hours": 10.0,
                    "cost_amount": 0.0,
                    "rating": 4.5,
                    "rating_count": 28000,
                    "certificate_offered": False,
                    "is_self_paced": True,
                    "resource_type": "course",
                    "topics_covered": ["AWS", "Cloud Computing", "Security", "Pricing", "Support"],
                    "prerequisites": [],
                },
            ],
            "docker": [
                {
                    "title": "Docker Mastery: with Kubernetes +Swarm",
                    "provider": "Udemy",
                    "url": "https://www.udemy.com/docker-mastery",
                    "description": "Best-selling Docker course. Learn Docker, Kubernetes, and container orchestration from scratch.",
                    "skill_level": "intermediate",
                    "duration_hours": 18.0,
                    "cost_amount": 18.0,
                    "rating": 4.7,
                    "rating_count": 85000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "course",
                    "topics_covered": ["Docker", "Containers", "Kubernetes", "Swarm", "Compose"],
                    "prerequisites": ["Basic Linux command line"],
                },
                {
                    "title": "Docker Tutorial for Beginners",
                    "provider": "freeCodeCamp",
                    "url": "https://www.youtube.com/watch?v=3c-iBn73dY4",
                    "description": "Free video tutorial covering Docker basics, containers, images, and more.",
                    "skill_level": "beginner",
                    "duration_hours": 4.0,
                    "cost_amount": 0.0,
                    "rating": 4.8,
                    "rating_count": 12000,
                    "certificate_offered": False,
                    "is_self_paced": True,
                    "resource_type": "video",
                    "topics_covered": ["Docker", "Containers", "Images", "Volumes", "Networks"],
                    "prerequisites": [],
                },
            ],
            "sql": [
                {
                    "title": "The Complete SQL Bootcamp: Go from Zero to Hero",
                    "provider": "Udemy",
                    "url": "https://www.udemy.com/the-complete-sql-bootcamp",
                    "description": "Learn SQL with PostgreSQL. Master database queries, design, and management.",
                    "skill_level": "beginner",
                    "duration_hours": 9.0,
                    "cost_amount": 15.0,
                    "rating": 4.6,
                    "rating_count": 95000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "course",
                    "topics_covered": ["SQL", "PostgreSQL", "Queries", "Joins", "Aggregation", "Database Design"],
                    "prerequisites": [],
                },
                {
                    "title": "SQL for Data Science",
                    "provider": "Coursera",
                    "url": "https://www.coursera.org/learn/sql-for-data-science",
                    "description": "Learn SQL for data analysis and data science. Work with real databases.",
                    "skill_level": "beginner",
                    "duration_hours": 15.0,
                    "cost_amount": 0.0,
                    "rating": 4.6,
                    "rating_count": 42000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "course",
                    "topics_covered": ["SQL", "Data Analysis", "Queries", "Subqueries", "Window Functions"],
                    "prerequisites": [],
                },
            ],
            "django": [
                {
                    "title": "Python and Django Full Stack Web Developer Bootcamp",
                    "provider": "Udemy",
                    "url": "https://www.udemy.com/django-developer",
                    "description": "Learn Django by building real websites. Complete Python web development course.",
                    "skill_level": "intermediate",
                    "duration_hours": 35.0,
                    "cost_amount": 20.0,
                    "rating": 4.7,
                    "rating_count": 62000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "course",
                    "topics_covered": ["Django", "Python", "HTML", "CSS", "JavaScript", "PostgreSQL"],
                    "prerequisites": ["Python"],
                },
                {
                    "title": "Django for Everybody",
                    "provider": "Coursera",
                    "url": "https://www.coursera.org/specializations/django",
                    "description": "Learn to build web applications using Django. Covers models, views, templates, and APIs.",
                    "skill_level": "intermediate",
                    "duration_hours": 40.0,
                    "cost_amount": 49.0,
                    "rating": 4.8,
                    "rating_count": 28000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "course",
                    "topics_covered": ["Django", "Python", "Web Development", "APIs", "Authentication"],
                    "prerequisites": ["Python"],
                },
            ],
            "machine learning": [
                {
                    "title": "Machine Learning Specialization",
                    "provider": "Coursera",
                    "url": "https://www.coursera.org/specializations/machine-learning",
                    "description": "Build ML models with NumPy & scikit-learn, build & train neural networks with TensorFlow.",
                    "skill_level": "intermediate",
                    "duration_hours": 60.0,
                    "cost_amount": 49.0,
                    "rating": 4.7,
                    "rating_count": 85000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "course",
                    "topics_covered": ["Machine Learning", "Python", "TensorFlow", "Neural Networks", "Deep Learning"],
                    "prerequisites": ["Python", "Basic Math"],
                },
                {
                    "title": "Machine Learning with Python",
                    "provider": "freeCodeCamp",
                    "url": "https://www.freecodecamp.org/learn/machine-learning-with-python",
                    "description": "Free introduction to machine learning using Python and scikit-learn.",
                    "skill_level": "beginner",
                    "duration_hours": 35.0,
                    "cost_amount": 0.0,
                    "rating": 4.7,
                    "rating_count": 18000,
                    "certificate_offered": True,
                    "is_self_paced": True,
                    "resource_type": "certification",
                    "topics_covered": ["Machine Learning", "Python", "Scikit-learn", "Classification", "Regression"],
                    "prerequisites": ["Python"],
                },
            ],
        }

    def _get_mock_resources_for_skill(self, skill: str) -> List[LearningRecommendation]:
        """
        Get mock resources for a specific skill.

        Args:
            skill: Target skill

        Returns:
            List of LearningRecommendation objects
        """
        resources = []

        # Try exact match first
        skill_lower = skill.lower()
        if skill_lower in self._mock_resources:
            resource_data = self._mock_resources[skill_lower]
        else:
            # Try to find partial match
            for key in self._mock_resources:
                if skill_lower in key or key in skill_lower:
                    resource_data = self._mock_resources[key]
                    break
            else:
                # No match found
                return []

        # Convert data to LearningRecommendation objects
        for data in resource_data:
            resource = LearningRecommendation(
                skill=skill,
                resource_type=data.get("resource_type", "course"),
                title=data["title"],
                description=data["description"],
                provider=data["provider"],
                url=data["url"],
                skill_level=data.get("skill_level", "intermediate"),
                topics_covered=data.get("topics_covered", []),
                prerequisites=data.get("prerequisites", []),
                language=data.get("language", "en"),
                is_self_paced=data.get("is_self_paced", True),
                duration_hours=data.get("duration_hours", 0.0),
                duration_weeks=data.get("duration_weeks", 0.0),
                cost_amount=data.get("cost_amount", 0.0),
                currency=data.get("currency", "USD"),
                access_type="free" if data.get("cost_amount", 0) == 0 else "paid",
                rating=data.get("rating", 0.0),
                rating_count=data.get("rating_count", 0),
                certificate_offered=data.get("certificate_offered", False),
                difficulty_level=data.get("difficulty_level", 3),
            )
            resources.append(resource)

        return resources


# Singleton instance
_default_engine: Optional[LearningRecommendationEngine] = None


def get_learning_recommendation_engine() -> LearningRecommendationEngine:
    """Get or create default learning recommendation engine instance."""
    global _default_engine
    if _default_engine is None:
        _default_engine = LearningRecommendationEngine()
    return _default_engine
