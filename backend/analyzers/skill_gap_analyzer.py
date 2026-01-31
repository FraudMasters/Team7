"""
Skill gap analyzer for comparing candidate skills against job requirements.

This module provides comprehensive skill gap analysis that identifies:
1. Missing required skills
2. Matched skills
3. Partial matches (skills present but with insufficient proficiency)
4. Gap severity assessment
5. Bridgeability score (how easily gaps can be addressed)
6. Estimated time to bridge gaps

The analyzer uses multiple matching strategies from the existing matchers
to provide accurate and nuanced skill gap analysis.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .enhanced_matcher import EnhancedSkillMatcher
from .unified_matcher import UnifiedSkillMatcher, UnifiedMatchResult

logger = logging.getLogger(__name__)


@dataclass
class SkillGapResult:
    """
    Comprehensive result from skill gap analysis.

    Attributes:
        candidate_skills: Skills extracted from candidate's resume
        required_skills: Skills required by the job vacancy
        matched_skills: Skills that match requirements
        missing_skills: Required skills not found in candidate's resume
        partial_match_skills: Skills present but with insufficient proficiency
        missing_skill_details: Detailed info about each missing skill
        gap_severity: Overall severity (critical, moderate, minimal, none)
        gap_percentage: Percentage of required skills missing (0-100)
        bridgeability_score: Score indicating how easily gaps can be bridged (0-1)
        estimated_time_to_bridge: Estimated hours to bridge all gaps
        priority_ordering: Order of priority for addressing gaps
        match_result: Raw unified match result for reference
    """

    # Input data
    candidate_skills: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)

    # Categorized skills
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    partial_match_skills: List[str] = field(default_factory=list)

    # Detailed analysis
    missing_skill_details: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Overall assessment
    gap_severity: str = "none"  # critical, moderate, minimal, none
    gap_percentage: float = 0.0
    bridgeability_score: float = 1.0  # 0-1, higher = easier to bridge
    estimated_time_to_bridge: int = 0  # in hours

    # Priority ordering
    priority_ordering: List[str] = field(default_factory=list)

    # Reference to full match result
    match_result: Optional[UnifiedMatchResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "candidate_skills": self.candidate_skills,
            "required_skills": self.required_skills,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "partial_match_skills": self.partial_match_skills,
            "missing_skill_details": self.missing_skill_details,
            "gap_severity": self.gap_severity,
            "gap_percentage": round(self.gap_percentage, 2),
            "bridgeability_score": round(self.bridgeability_score, 4),
            "estimated_time_to_bridge": self.estimated_time_to_bridge,
            "priority_ordering": self.priority_ordering,
            "match_result": self.match_result.to_dict() if self.match_result else None,
        }


class SkillGapAnalyzer:
    """
    Analyzes skill gaps between candidate skills and job requirements.

    Uses the unified matcher to perform comprehensive skill comparison,
    then analyzes the results to determine:
    - Which skills are missing
    - Gap severity level
    - How bridgeable the gaps are
    - Estimated time to address gaps
    - Priority order for addressing gaps

    Example:
        >>> analyzer = SkillGapAnalyzer()
        >>> result = analyzer.analyze(
        ...     resume_text="Experienced Python developer with Django",
        ...     candidate_skills=["Python", "Django", "SQL"],
        ...     job_title="Senior Full Stack Developer",
        ...     job_description="Looking for Python, Django, React, and AWS",
        ...     required_skills=["Python", "Django", "React", "AWS", "Docker"],
        ...     required_skill_levels={
        ...             "Python": "advanced",
        ...             "Django": "intermediate",
        ...             "React": "intermediate",
        ...             "AWS": "beginner",
        ...             "Docker": "beginner",
        ...         }
        ... )
        >>> print(result.missing_skills)
        ['React', 'AWS', 'Docker']
        >>> print(result.gap_severity)
        'moderate'
        >>> print(result.estimated_time_to_bridge)
        40
    """

    def __init__(
        self,
        # Skill gap thresholds
        critical_gap_threshold: float = 0.5,  # >50% missing = critical
        moderate_gap_threshold: float = 0.3,  # >30% missing = moderate
        minimal_gap_threshold: float = 0.1,  # >10% missing = minimal

        # Bridgeability factors
        bridgeability_difficulty_multiplier: float = 1.0,  # Adjusts time estimates
        hours_per_beginner_skill: int = 20,
        hours_per_intermediate_skill: int = 40,
        hours_per_advanced_skill: int = 80,

        # Use unified matcher for comprehensive analysis
        use_unified_matcher: bool = True,
    ):
        """
        Initialize the skill gap analyzer.

        Args:
            critical_gap_threshold: Gap percentage above which severity is 'critical'
            moderate_gap_threshold: Gap percentage above which severity is 'moderate'
            minimal_gap_threshold: Gap percentage above which severity is 'minimal'
            bridgeability_difficulty_multiplier: Multiplier for time estimates
            hours_per_beginner_skill: Base hours to learn a beginner skill
            hours_per_intermediate_skill: Base hours to learn an intermediate skill
            hours_per_advanced_skill: Base hours to learn an advanced skill
            use_unified_matcher: Whether to use UnifiedSkillMatcher (vs simple matcher)
        """
        self.critical_gap_threshold = critical_gap_threshold
        self.moderate_gap_threshold = moderate_gap_threshold
        self.minimal_gap_threshold = minimal_gap_threshold

        self.bridgeability_difficulty_multiplier = bridgeability_difficulty_multiplier
        self.hours_per_beginner_skill = hours_per_beginner_skill
        self.hours_per_intermediate_skill = hours_per_intermediate_skill
        self.hours_per_advanced_skill = hours_per_advanced_skill

        # Initialize matchers
        if use_unified_matcher:
            self.unified_matcher = UnifiedSkillMatcher()
            self.keyword_matcher = self.unified_matcher.keyword_matcher
        else:
            self.unified_matcher = None
            self.keyword_matcher = EnhancedSkillMatcher()

        logger.info(
            f"SkillGapAnalyzer initialized with "
            f"critical_threshold={critical_gap_threshold}, "
            f"moderate_threshold={moderate_gap_threshold}"
        )

    def analyze(
        self,
        resume_text: str,
        candidate_skills: List[str],
        job_title: str,
        job_description: str,
        required_skills: List[str],
        required_skill_levels: Optional[Dict[str, str]] = None,
        candidate_skill_levels: Optional[Dict[str, str]] = None,
        context: Optional[str] = None,
    ) -> SkillGapResult:
        """
        Analyze skill gaps between candidate and job requirements.

        Args:
            resume_text: Full resume text for context
            candidate_skills: List of skills extracted from candidate's resume
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills from job posting
            required_skill_levels: Optional mapping of required skills to levels
            candidate_skill_levels: Optional mapping of candidate skills to levels
            context: Optional context hint for matching

        Returns:
            SkillGapResult with comprehensive gap analysis
        """
        # Normalize inputs
        required_skill_levels = required_skill_levels or {}
        candidate_skill_levels = candidate_skill_levels or {}

        # Step 1: Perform skill matching
        if self.unified_matcher:
            match_result = self.unified_matcher.match(
                resume_text=resume_text,
                resume_skills=candidate_skills,
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
                context=context,
            )
            matched_skills = match_result.matched_skills
            missing_skills = match_result.missing_skills
        else:
            # Use simple keyword matching
            keyword_results = self.keyword_matcher.match_multiple(
                resume_skills=candidate_skills,
                required_skills=required_skills,
                context=context,
            )
            matched_skills = [
                skill for skill, result in keyword_results.items()
                if result.get("matched", False)
            ]
            missing_skills = [
                skill for skill, result in keyword_results.items()
                if not result.get("matched", False)
            ]
            match_result = None

        # Step 2: Identify partial matches (skills present but insufficient level)
        partial_match_skills = self._identify_partial_matches(
            matched_skills=matched_skills,
            required_skill_levels=required_skill_levels,
            candidate_skill_levels=candidate_skill_levels,
        )

        # Step 3: Calculate gap metrics
        gap_percentage = self._calculate_gap_percentage(
            required_skills=required_skills,
            missing_skills=missing_skills,
            partial_match_skills=partial_match_skills,
        )

        gap_severity = self._determine_gap_severity(gap_percentage)

        # Step 4: Analyze missing skills in detail
        missing_skill_details = self._analyze_missing_skills(
            missing_skills=missing_skills,
            partial_match_skills=partial_match_skills,
            required_skill_levels=required_skill_levels,
        )

        # Step 5: Calculate bridgeability score
        bridgeability_score = self._calculate_bridgeability_score(
            missing_skills=missing_skills,
            partial_match_skills=partial_match_skills,
            required_skill_levels=required_skill_levels,
            gap_percentage=gap_percentage,
        )

        # Step 6: Estimate time to bridge gaps
        estimated_time = self._estimate_time_to_bridge(
            missing_skills=missing_skills,
            partial_match_skills=partial_match_skills,
            required_skill_levels=required_skill_levels,
            bridgeability_score=bridgeability_score,
        )

        # Step 7: Determine priority ordering
        priority_ordering = self._determine_priority_ordering(
            missing_skills=missing_skills,
            partial_match_skills=partial_match_skills,
            missing_skill_details=missing_skill_details,
        )

        return SkillGapResult(
            candidate_skills=candidate_skills,
            required_skills=required_skills,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            partial_match_skills=partial_match_skills,
            missing_skill_details=missing_skill_details,
            gap_severity=gap_severity,
            gap_percentage=gap_percentage,
            bridgeability_score=bridgeability_score,
            estimated_time_to_bridge=estimated_time,
            priority_ordering=priority_ordering,
            match_result=match_result,
        )

    def _identify_partial_matches(
        self,
        matched_skills: List[str],
        required_skill_levels: Dict[str, str],
        candidate_skill_levels: Dict[str, str],
    ) -> List[str]:
        """
        Identify skills that are present but at insufficient proficiency levels.

        Args:
            matched_skills: Skills that were matched
            required_skill_levels: Required proficiency levels
            candidate_skill_levels: Candidate's proficiency levels

        Returns:
            List of skills with partial proficiency match
        """
        partial_matches = []

        level_rank = {
            "beginner": 1,
            "intermediate": 2,
            "advanced": 3,
            "expert": 4,
        }

        for skill in matched_skills:
            required_level = required_skill_levels.get(skill)
            candidate_level = candidate_skill_levels.get(skill)

            if required_level and candidate_level:
                required_rank = level_rank.get(required_level.lower(), 2)
                candidate_rank = level_rank.get(candidate_level.lower(), 2)

                # If candidate level is below required level, it's a partial match
                if candidate_rank < required_rank:
                    partial_matches.append(skill)

        return partial_matches

    def _calculate_gap_percentage(
        self,
        required_skills: List[str],
        missing_skills: List[str],
        partial_match_skills: List[str],
    ) -> float:
        """
        Calculate the percentage of required skills that are missing or partial.

        Args:
            required_skills: All required skills
            missing_skills: Skills not present at all
            partial_match_skills: Skills present but at insufficient level

        Returns:
            Gap percentage (0-100)
        """
        if not required_skills:
            return 0.0

        # Count both missing and partial matches as gaps
        # Partial matches count as 50% gap
        total_gaps = len(missing_skills) + (0.5 * len(partial_match_skills))
        gap_percentage = (total_gaps / len(required_skills)) * 100

        return min(gap_percentage, 100.0)  # Cap at 100%

    def _determine_gap_severity(self, gap_percentage: float) -> str:
        """
        Determine severity level based on gap percentage.

        Args:
            gap_percentage: Percentage of skills missing

        Returns:
            Severity level: 'critical', 'moderate', 'minimal', or 'none'
        """
        if gap_percentage >= self.critical_gap_threshold * 100:
            return "critical"
        elif gap_percentage >= self.moderate_gap_threshold * 100:
            return "moderate"
        elif gap_percentage >= self.minimal_gap_threshold * 100:
            return "minimal"
        else:
            return "none"

    def _analyze_missing_skills(
        self,
        missing_skills: List[str],
        partial_match_skills: List[str],
        required_skill_levels: Dict[str, str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create detailed analysis for each missing or partial skill.

        Args:
            missing_skills: Skills not present
            partial_match_skills: Skills with insufficient proficiency
            required_skill_levels: Required levels for each skill

        Returns:
            Dictionary mapping skill names to detail objects
        """
        details = {}

        # Analyze completely missing skills
        for skill in missing_skills:
            required_level = required_skill_levels.get(skill, "intermediate")

            details[skill] = {
                "status": "missing",
                "required_level": required_level,
                "importance": "high",  # Could be enhanced with taxonomy data
                "category": self._categorize_skill(skill),
            }

        # Analyze partial match skills
        for skill in partial_match_skills:
            required_level = required_skill_levels.get(skill, "intermediate")

            details[skill] = {
                "status": "partial",
                "required_level": required_level,
                "importance": "medium",
                "category": self._categorize_skill(skill),
                "note": "Skill present but at insufficient proficiency level",
            }

        return details

    def _categorize_skill(self, skill: str) -> str:
        """
        Categorize a skill into a broad category.

        This is a simple heuristic-based categorization.
        Could be enhanced with a proper taxonomy.

        Args:
            skill: Skill name

        Returns:
            Category name
        """
        skill_lower = skill.lower()

        # Programming languages
        if any(
            lang in skill_lower
            for lang in [
                "python",
                "java",
                "javascript",
                "typescript",
                "c++",
                "c#",
                "go",
                "rust",
                "ruby",
                "php",
                "swift",
                "kotlin",
            ]
        ):
            return "programming_language"

        # Web frameworks
        if any(
            fw in skill_lower
            for fw in [
                "react",
                "angular",
                "vue",
                "django",
                "flask",
                "spring",
                "express",
                "rails",
            ]
        ):
            return "web_framework"

        # Databases
        if any(
            db in skill_lower
            for db in [
                "sql",
                "mysql",
                "postgresql",
                "mongodb",
                "redis",
                "elasticsearch",
                "oracle",
            ]
        ):
            return "database"

        # Cloud/DevOps
        if any(
            cloud in skill_lower
            for cloud in ["aws", "azure", "gcp", "docker", "kubernetes", "terraform"]
        ):
            return "cloud_devops"

        # Tools/Other
        return "other"

    def _calculate_bridgeability_score(
        self,
        missing_skills: List[str],
        partial_match_skills: List[str],
        required_skill_levels: Dict[str, str],
        gap_percentage: float,
    ) -> float:
        """
        Calculate how easily the skill gaps can be bridged.

        Factors:
        - Number of missing skills (fewer = higher score)
        - Complexity of missing skills (beginner vs advanced)
        - Partial matches are easier to bridge than completely missing skills
        - Overall gap percentage

        Args:
            missing_skills: Skills not present
            partial_match_skills: Skills with insufficient proficiency
            required_skill_levels: Required levels
            gap_percentage: Overall gap percentage

        Returns:
            Bridgeability score from 0 (hard to bridge) to 1 (easy to bridge)
        """
        if not missing_skills and not partial_match_skills:
            return 1.0

        # Start with base score
        base_score = 1.0 - (gap_percentage / 100)

        # Adjust for skill complexity
        complexity_penalty = 0.0
        for skill in missing_skills:
            level = required_skill_levels.get(skill, "intermediate").lower()
            if level == "advanced":
                complexity_penalty += 0.1
            elif level == "expert":
                complexity_penalty += 0.15

        # Bonus for partial matches (easier to upgrade than learn from scratch)
        partial_match_bonus = len(partial_match_skills) * 0.05

        # Calculate final score
        bridgeability_score = base_score - complexity_penalty + partial_match_bonus

        return max(0.0, min(bridgeability_score, 1.0))

    def _estimate_time_to_bridge(
        self,
        missing_skills: List[str],
        partial_match_skills: List[str],
        required_skill_levels: Dict[str, str],
        bridgeability_score: float,
    ) -> int:
        """
        Estimate total hours required to bridge all skill gaps.

        Args:
            missing_skills: Skills not present
            partial_match_skills: Skills with insufficient proficiency
            required_skill_levels: Required levels for each skill
            bridgeability_score: Overall bridgeability score

        Returns:
            Estimated hours to bridge all gaps
        """
        total_hours = 0

        # Time for completely missing skills
        for skill in missing_skills:
            level = required_skill_levels.get(skill, "intermediate").lower()

            if level == "beginner":
                total_hours += self.hours_per_beginner_skill
            elif level == "intermediate":
                total_hours += self.hours_per_intermediate_skill
            elif level in ("advanced", "expert"):
                total_hours += self.hours_per_advanced_skill
            else:
                total_hours += self.hours_per_intermediate_skill

        # Time for partial match skills (50% of full time since foundation exists)
        for skill in partial_match_skills:
            level = required_skill_levels.get(skill, "intermediate").lower()

            if level == "beginner":
                total_hours += self.hours_per_beginner_skill * 0.5
            elif level == "intermediate":
                total_hours += self.hours_per_intermediate_skill * 0.5
            elif level in ("advanced", "expert"):
                total_hours += self.hours_per_advanced_skill * 0.5

        # Adjust by bridgeability score and difficulty multiplier
        # Higher bridgeability = less time needed
        adjusted_hours = int(
            total_hours
            * self.bridgeability_difficulty_multiplier
            * (2 - bridgeability_score)
        )

        return adjusted_hours

    def _determine_priority_ordering(
        self,
        missing_skills: List[str],
        partial_match_skills: List[str],
        missing_skill_details: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        """
        Determine the optimal order for addressing skill gaps.

        Priority factors:
1. Partial matches first (easier to complete)
        2. High-importance skills
        3. Beginner-level skills before advanced
        4. Foundational skills (programming languages) before tools

        Args:
            missing_skills: Skills not present
            partial_match_skills: Skills with insufficient proficiency
            missing_skill_details: Detailed information about each gap

        Returns:
            Ordered list of skills to address
        """
        # Priority score for each skill
        skill_scores = {}

        # Partial matches get priority (they're closer to completion)
        for skill in partial_match_skills:
            details = missing_skill_details.get(skill, {})
            importance = details.get("importance", "medium")
            level = details.get("required_level", "intermediate")

            score = 100  # Base priority for partial matches

            # Adjust by importance
            if importance == "high":
                score += 50
            elif importance == "medium":
                score += 25

            # Adjust by level (beginner skills first)
            if level == "beginner":
                score += 30
            elif level == "intermediate":
                score += 20

            # Adjust by category (foundational skills first)
            category = details.get("category", "other")
            if category == "programming_language":
                score += 20
            elif category == "web_framework" or category == "database":
                score += 10

            skill_scores[skill] = score

        # Missing skills
        for skill in missing_skills:
            details = missing_skill_details.get(skill, {})
            importance = details.get("importance", "medium")
            level = details.get("required_level", "intermediate")

            score = 50  # Base priority for missing skills

            # Adjust by importance
            if importance == "high":
                score += 50
            elif importance == "medium":
                score += 25

            # Adjust by level (beginner skills first)
            if level == "beginner":
                score += 30
            elif level == "intermediate":
                score += 20

            # Adjust by category (foundational skills first)
            category = details.get("category", "other")
            if category == "programming_language":
                score += 20
            elif category == "web_framework" or category == "database":
                score += 10

            skill_scores[skill] = score

        # Sort by score descending
        ordered_skills = sorted(
            skill_scores.keys(), key=lambda s: skill_scores[s], reverse=True
        )

        return ordered_skills

    def analyze_resume_to_vacancy(
        self,
        resume_text: str,
        candidate_skills: List[str],
        vacancy_title: str,
        vacancy_description: str,
        vacancy_skills: List[str],
        vacancy_skill_levels: Optional[Dict[str, str]] = None,
        candidate_skill_levels: Optional[Dict[str, str]] = None,
    ) -> SkillGapResult:
        """
        Analyze skill gaps for a specific resume-vacancy pair.

        Convenience method with clearer naming for vacancy analysis.

        Args:
            resume_text: Full resume text
            candidate_skills: Skills extracted from resume
            vacancy_title: Vacancy title
            vacancy_description: Vacancy description
            vacancy_skills: Required skills for vacancy
            vacancy_skill_levels: Required skill levels
            candidate_skill_levels: Candidate's skill levels

        Returns:
            SkillGapResult with comprehensive analysis
        """
        return self.analyze(
            resume_text=resume_text,
            candidate_skills=candidate_skills,
            job_title=vacancy_title,
            job_description=vacancy_description,
            required_skills=vacancy_skills,
            required_skill_levels=vacancy_skill_levels,
            candidate_skill_levels=candidate_skill_levels,
        )


# Singleton instance
_default_analyzer: Optional[SkillGapAnalyzer] = None


def get_skill_gap_analyzer() -> SkillGapAnalyzer:
    """Get or create default skill gap analyzer instance."""
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = SkillGapAnalyzer()
    return _default_analyzer
