"""
Taxonomy-aware skill matching service.

This module provides the TaxonomyMatcherService class for matching skills
using the skill taxonomy with variants, aliases, and relationships.
It integrates with the existing SkillsMatcher for fuzzy and semantic matching
while adding taxonomy-specific enhancements.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.skill_taxonomy import SkillTaxonomy
from models.skill_relationship import SkillRelationship, RelationshipType
from skills.skills_matcher import SkillsMatcher

logger = logging.getLogger(__name__)


@dataclass
class TaxonomyMatchResult:
    """
    Result of a taxonomy-aware skill match.

    Attributes:
        matched_skill: The matched canonical skill name
        original_skill: The original skill string that was matched
        taxonomy_entry: Full taxonomy entry if available
        score: Match score (0-100)
        match_type: Type of match ('exact', 'alias', 'variant', 'fuzzy', 'semantic', 'relationship')
        aliases_matched: List of aliases that matched
        related_skills: List of related skills found
        category_path: Hierarchical path from root to skill
        confidence: Confidence level of the match (0-1)
        error: Error message if matching failed
    """
    matched_skill: Optional[str] = None
    original_skill: Optional[str] = None
    taxonomy_entry: Optional[Dict[str, Any]] = None
    score: float = 0.0
    match_type: Optional[str] = None
    aliases_matched: List[str] = field(default_factory=list)
    related_skills: List[str] = field(default_factory=list)
    category_path: List[str] = field(default_factory=list)
    confidence: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "matched_skill": self.matched_skill,
            "original_skill": self.original_skill,
            "taxonomy_entry": self.taxonomy_entry,
            "score": self.score,
            "match_type": self.match_type,
            "aliases_matched": self.aliases_matched,
            "related_skills": self.related_skills,
            "category_path": self.category_path,
            "confidence": self.confidence,
            "error": self.error,
        }


@dataclass
class AliasResolution:
    """
    Result of alias resolution.

    Attributes:
        alias: The original alias/variant string
        resolved_skill: The canonical skill name
        taxonomy_id: UUID of the taxonomy entry
        industry: Industry context
        context: Skill context/category
        confidence: Resolution confidence (0-1)
    """
    alias: str
    resolved_skill: str
    taxonomy_id: Optional[UUID] = None
    industry: Optional[str] = None
    context: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alias": self.alias,
            "resolved_skill": self.resolved_skill,
            "taxonomy_id": str(self.taxonomy_id) if self.taxonomy_id else None,
            "industry": self.industry,
            "context": self.context,
            "confidence": self.confidence,
        }


@dataclass
class RelatedSkill:
    """
    A skill related to another skill.

    Attributes:
        skill_name: Name of the related skill
        relationship_type: Type of relationship (parent_child, similar, etc.)
        weight: Relationship strength (0-1)
        taxonomy_id: UUID of the taxonomy entry
    """
    skill_name: str
    relationship_type: str
    weight: float = 1.0
    taxonomy_id: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_name": self.skill_name,
            "relationship_type": self.relationship_type,
            "weight": self.weight,
            "taxonomy_id": str(self.taxonomy_id) if self.taxonomy_id else None,
        }


class TaxonomyMatcherService:
    """
    Taxonomy-aware skill matching service.

    This service enhances skill matching by using the skill taxonomy:
    - Matches skills using variants and aliases from the taxonomy
    - Resolves common abbreviations and alternative names
    - Finds related skills using skill relationships
    - Provides hierarchical category information

    The service integrates with the existing SkillsMatcher for fuzzy matching
    while adding taxonomy-specific enhancements for better accuracy.

    Attributes:
        db: Database session for querying taxonomy data
        skills_matcher: Underlying SkillsMatcher instance
        fuzzy_threshold: Minimum fuzzy match score (0-100)
        include_relationships: Whether to include related skills in results
        cache_ttl: Cache time-to-live in seconds

    Example:
        >>> service = TaxonomyMatcherService(db)
        >>> result = await service.match_skill("JS")
        >>> print(result.matched_skill)  # 'JavaScript'
        >>> print(result.match_type)  # 'alias'
    """

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        *,
        fuzzy_threshold: int = 80,
        include_relationships: bool = True,
        cache_ttl: int = 300,
    ) -> None:
        """
        Initialize the taxonomy matcher service.

        Args:
            db: Database session for querying taxonomy data
            fuzzy_threshold: Minimum fuzzy match score (0-100, default: 80)
            include_relationships: Whether to include related skills (default: True)
            cache_ttl: Cache TTL in seconds (default: 300)

        Raises:
            ValueError: If threshold values are out of valid range
        """
        if not 0 <= fuzzy_threshold <= 100:
            raise ValueError("fuzzy_threshold must be between 0 and 100")

        self.db = db
        self.fuzzy_threshold = fuzzy_threshold
        self.include_relationships = include_relationships
        self.cache_ttl = cache_ttl

        # Initialize the underlying SkillsMatcher
        self.skills_matcher = SkillsMatcher(
            fuzzy_threshold=fuzzy_threshold,
            use_semantic=False,
        )

        # In-memory cache for taxonomy data
        self._taxonomy_cache: Dict[str, Dict[str, Any]] = {}
        self._alias_cache: Dict[str, AliasResolution] = {}
        self._cache_timestamp: Optional[datetime] = None

        logger.info(
            f"TaxonomyMatcherService initialized (fuzzy_threshold={fuzzy_threshold}, "
            f"include_relationships={include_relationships})"
        )

    async def match_skill(
        self,
        candidate_skill: str,
        organization_id: Optional[str] = None,
        *,
        include_variants: bool = True,
        include_relationships: Optional[bool] = None,
    ) -> TaxonomyMatchResult:
        """
        Match a candidate skill against the taxonomy.

        Attempts to find the best match using:
        1. Exact match against canonical skill names
        2. Alias/variant match from taxonomy
        3. Fuzzy match using the underlying SkillsMatcher
        4. Relationship-based match (if enabled)

        Args:
            candidate_skill: The skill to match
            organization_id: Organization ID for filtering taxonomy
            include_variants: Whether to check variants/aliases (default: True)
            include_relationships: Whether to find related skills (default: from instance)

        Returns:
            TaxonomyMatchResult with match details

        Example:
            >>> result = await service.match_skill("JS")
            >>> print(result.matched_skill)  # 'JavaScript'
            >>> print(result.match_type)  # 'alias'
        """
        # Validate input
        if not candidate_skill or not isinstance(candidate_skill, str):
            return TaxonomyMatchResult(
                original_skill=candidate_skill,
                error="candidate_skill must be a non-empty string",
            )

        should_include_relationships = (
            include_relationships
            if include_relationships is not None
            else self.include_relationships
        )

        try:
            # Normalize the candidate skill
            normalized_candidate = self.skills_matcher.normalize_skill(candidate_skill)

            # Step 1: Try exact match against taxonomy canonical names
            if self.db:
                exact_match = await self._find_exact_match(
                    normalized_candidate, organization_id
                )
                if exact_match:
                    result = TaxonomyMatchResult(
                        matched_skill=exact_match["skill_name"],
                        original_skill=candidate_skill,
                        taxonomy_entry=exact_match,
                        score=100,
                        match_type="exact",
                        confidence=1.0,
                        category_path=exact_match.get("category_path", []),
                    )

                    if should_include_relationships:
                        result.related_skills = await self._get_related_skill_names(
                            exact_match["id"], organization_id
                        )

                    return result

            # Step 2: Try alias/variant match from taxonomy
            if include_variants and self.db:
                alias_match = await self._find_alias_match(
                    candidate_skill, normalized_candidate, organization_id
                )
                if alias_match:
                    result = TaxonomyMatchResult(
                        matched_skill=alias_match["skill_name"],
                        original_skill=candidate_skill,
                        taxonomy_entry=alias_match,
                        score=95,  # High score for alias match
                        match_type="alias",
                        confidence=0.95,
                        aliases_matched=[candidate_skill],
                        category_path=alias_match.get("category_path", []),
                    )

                    if should_include_relationships:
                        result.related_skills = await self._get_related_skill_names(
                            alias_match["id"], organization_id
                        )

                    return result

            # Step 3: Fall back to fuzzy matching with taxonomy skills
            if self.db:
                taxonomy_skills = await self._get_taxonomy_skills(organization_id)
            else:
                taxonomy_skills = []

            if taxonomy_skills:
                fuzzy_result = self.skills_matcher.match_skill(
                    candidate_skill, taxonomy_skills
                )

                if fuzzy_result.get("matched_skill"):
                    # Get the full taxonomy entry for the matched skill
                    matched_entry = await self._get_taxonomy_entry_by_name(
                        fuzzy_result["matched_skill"], organization_id
                    )

                    result = TaxonomyMatchResult(
                        matched_skill=fuzzy_result["matched_skill"],
                        original_skill=candidate_skill,
                        taxonomy_entry=matched_entry,
                        score=fuzzy_result.get("score", 0),
                        match_type=fuzzy_result.get("match_type", "fuzzy"),
                        confidence=fuzzy_result.get("score", 0) / 100.0,
                        category_path=matched_entry.get("category_path", []) if matched_entry else [],
                    )

                    if should_include_relationships and matched_entry:
                        result.related_skills = await self._get_related_skill_names(
                            matched_entry["id"], organization_id
                        )

                    return result

            # No match found
            logger.debug(f"No match found for skill '{candidate_skill}'")
            return TaxonomyMatchResult(
                original_skill=candidate_skill,
                matched_skill=None,
                score=0,
                match_type=None,
            )

        except Exception as e:
            logger.error(f"Error matching skill '{candidate_skill}': {e}")
            return TaxonomyMatchResult(
                original_skill=candidate_skill,
                error=f"Matching failed: {str(e)}",
            )

    async def match_skills(
        self,
        candidate_skills: List[str],
        organization_id: Optional[str] = None,
        *,
        include_variants: bool = True,
        include_relationships: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Match multiple candidate skills against the taxonomy.

        Args:
            candidate_skills: List of skills to match
            organization_id: Organization ID for filtering taxonomy
            include_variants: Whether to check variants/aliases (default: True)
            include_relationships: Whether to find related skills (default: from instance)

        Returns:
            Dictionary containing:
                - matched: Dict mapping original skills to match results
                - unmatched: List of skills that didn't match
                - matched_skills: List of successfully matched skill names
                - match_rate: Percentage of skills that matched
                - error: Error message if matching failed

        Example:
            >>> result = await service.match_skills(["JS", "React.js"])
            >>> print(result["matched_skills"])  # ['JavaScript', 'React']
        """
        if not candidate_skills or not isinstance(candidate_skills, list):
            return {
                "matched": None,
                "unmatched": None,
                "matched_skills": None,
                "match_rate": 0,
                "error": "candidate_skills must be a non-empty list",
            }

        try:
            matched: Dict[str, Dict[str, Any]] = {}
            matched_skills: List[str] = []
            unmatched: List[str] = []

            for skill in candidate_skills:
                if not skill or not isinstance(skill, str):
                    continue

                result = await self.match_skill(
                    skill,
                    organization_id,
                    include_variants=include_variants,
                    include_relationships=include_relationships,
                )

                if result.error:
                    logger.warning(f"Error matching '{skill}': {result.error}")
                    unmatched.append(skill)
                elif result.matched_skill:
                    matched[skill] = result.to_dict()
                    matched_skills.append(result.matched_skill)
                else:
                    unmatched.append(skill)

            # Remove duplicates while preserving order
            seen: Set[str] = set()
            unique_matched: List[str] = []
            for skill in matched_skills:
                if skill not in seen:
                    seen.add(skill)
                    unique_matched.append(skill)

            match_rate = (
                len(unique_matched) / len(candidate_skills) * 100
                if candidate_skills
                else 0
            )

            logger.info(
                f"Matched {len(unique_matched)}/{len(candidate_skills)} skills "
                f"({match_rate:.1f}%)"
            )

            return {
                "matched": matched,
                "unmatched": unmatched if unmatched else None,
                "matched_skills": unique_matched if unique_matched else None,
                "match_rate": round(match_rate, 2),
                "error": None,
            }

        except Exception as e:
            logger.error(f"Skills matching failed: {e}")
            return {
                "matched": None,
                "unmatched": None,
                "matched_skills": None,
                "match_rate": 0,
                "error": f"Matching failed: {str(e)}",
            }

    def resolve_alias(
        self,
        alias: str,
        *,
        industry: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Optional[AliasResolution]:
        """
        Resolve a skill alias to its canonical form.

        This is a synchronous method that uses cached data for fast lookups.
        For database-backed resolution, use resolve_alias_async instead.

        Args:
            alias: The alias or variant to resolve
            industry: Optional industry filter
            organization_id: Optional organization filter

        Returns:
            AliasResolution if found, None otherwise

        Note:
            This method is implemented in subtask-3-2. The current
            implementation is a stub that returns None.

        Example:
            >>> resolution = service.resolve_alias("JS")
            >>> print(resolution.resolved_skill)  # 'JavaScript'
        """
        # Check cache first
        cache_key = f"{alias}:{industry}:{organization_id}"
        if cache_key in self._alias_cache:
            return self._alias_cache[cache_key]

        # TODO: Implement full alias resolution in subtask-3-2
        # For now, return None to indicate no match found
        logger.debug(f"Alias resolution not yet implemented for '{alias}'")
        return None

    async def resolve_alias_async(
        self,
        alias: str,
        *,
        industry: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Optional[AliasResolution]:
        """
        Resolve a skill alias to its canonical form asynchronously.

        This method queries the database for alias/variant resolution.

        Args:
            alias: The alias or variant to resolve
            industry: Optional industry filter
            organization_id: Optional organization filter

        Returns:
            AliasResolution if found, None otherwise

        Note:
            This method is implemented in subtask-3-2. The current
            implementation is a stub that returns None.

        Example:
            >>> resolution = await service.resolve_alias_async("JS")
            >>> print(resolution.resolved_skill)  # 'JavaScript'
        """
        # TODO: Implement full async alias resolution in subtask-3-2
        # For now, fall back to the sync method
        return self.resolve_alias(alias, industry=industry, organization_id=organization_id)

    def find_related_skills(
        self,
        skill_name: str,
        *,
        relationship_types: Optional[List[str]] = None,
        min_weight: float = 0.0,
        organization_id: Optional[str] = None,
    ) -> List[RelatedSkill]:
        """
        Find skills related to the given skill.

        This is a synchronous method that uses cached data for fast lookups.
        For database-backed resolution, use find_related_skills_async instead.

        Args:
            skill_name: The skill to find relations for
            relationship_types: Types of relationships to include (default: all)
            min_weight: Minimum relationship weight (default: 0.0)
            organization_id: Optional organization filter

        Returns:
            List of RelatedSkill objects

        Note:
            This method is implemented in subtask-3-3. The current
            implementation returns an empty list.

        Example:
            >>> related = service.find_related_skills("React")
            >>> print([r.skill_name for r in related])  # ['Vue', 'Angular', 'Frontend']
        """
        # TODO: Implement full related skills lookup in subtask-3-3
        # For now, return empty list
        logger.debug(f"Related skills lookup not yet implemented for '{skill_name}'")
        return []

    async def find_related_skills_async(
        self,
        skill_name: str,
        *,
        relationship_types: Optional[List[str]] = None,
        min_weight: float = 0.0,
        organization_id: Optional[str] = None,
    ) -> List[RelatedSkill]:
        """
        Find skills related to the given skill asynchronously.

        This method queries the database for skill relationships.

        Args:
            skill_name: The skill to find relations for
            relationship_types: Types of relationships to include (default: all)
            min_weight: Minimum relationship weight (default: 0.0)
            organization_id: Optional organization filter

        Returns:
            List of RelatedSkill objects

        Note:
            This method is implemented in subtask-3-3. The current
            implementation is a stub that returns an empty list.

        Example:
            >>> related = await service.find_related_skills_async("React")
            >>> print([r.skill_name for r in related])  # ['Vue', 'Angular', 'Frontend']
        """
        # TODO: Implement full async related skills lookup in subtask-3-3
        # For now, fall back to the sync method
        return self.find_related_skills(
            skill_name,
            relationship_types=relationship_types,
            min_weight=min_weight,
            organization_id=organization_id,
        )

    # Private helper methods

    async def _find_exact_match(
        self,
        normalized_skill: str,
        organization_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Find an exact match in the taxonomy."""
        if not self.db:
            return None

        try:
            query = select(SkillTaxonomy).where(
                and_(
                    SkillTaxonomy.is_active == True,
                    SkillTaxonomy.is_latest == True,
                )
            )

            # Add organization filter if provided
            if organization_id:
                query = query.where(SkillTaxonomy.organization_id == organization_id)

            result = await self.db.execute(query)
            taxonomies = result.scalars().all()

            # Check for exact match (normalized)
            for taxonomy in taxonomies:
                normalized_name = self.skills_matcher.normalize_skill(taxonomy.skill_name)
                if normalized_name == normalized_skill:
                    return self._taxonomy_to_dict(taxonomy)

            return None

        except Exception as e:
            logger.error(f"Error finding exact match: {e}")
            return None

    async def _find_alias_match(
        self,
        original_skill: str,
        normalized_skill: str,
        organization_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Find a match using aliases and variants."""
        if not self.db:
            return None

        try:
            query = select(SkillTaxonomy).where(
                and_(
                    SkillTaxonomy.is_active == True,
                    SkillTaxonomy.is_latest == True,
                    SkillTaxonomy.variants.isnot(None),
                )
            )

            if organization_id:
                query = query.where(SkillTaxonomy.organization_id == organization_id)

            result = await self.db.execute(query)
            taxonomies = result.scalars().all()

            # Check variants for matches
            for taxonomy in taxonomies:
                if not taxonomy.variants:
                    continue

                for variant in taxonomy.variants:
                    normalized_variant = self.skills_matcher.normalize_skill(variant)
                    if normalized_variant == normalized_skill:
                        return self._taxonomy_to_dict(taxonomy)

                    # Also check case-insensitive exact match
                    if variant.lower() == original_skill.lower():
                        return self._taxonomy_to_dict(taxonomy)

            return None

        except Exception as e:
            logger.error(f"Error finding alias match: {e}")
            return None

    async def _get_taxonomy_skills(
        self,
        organization_id: Optional[str],
    ) -> List[str]:
        """Get list of all canonical skill names from taxonomy."""
        if not self.db:
            return []

        try:
            query = select(SkillTaxonomy.skill_name).where(
                and_(
                    SkillTaxonomy.is_active == True,
                    SkillTaxonomy.is_latest == True,
                )
            )

            if organization_id:
                query = query.where(SkillTaxonomy.organization_id == organization_id)

            result = await self.db.execute(query)
            return [row[0] for row in result.all()]

        except Exception as e:
            logger.error(f"Error getting taxonomy skills: {e}")
            return []

    async def _get_taxonomy_entry_by_name(
        self,
        skill_name: str,
        organization_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Get full taxonomy entry by skill name."""
        if not self.db:
            return None

        try:
            query = select(SkillTaxonomy).where(
                and_(
                    SkillTaxonomy.skill_name == skill_name,
                    SkillTaxonomy.is_active == True,
                    SkillTaxonomy.is_latest == True,
                )
            )

            if organization_id:
                query = query.where(SkillTaxonomy.organization_id == organization_id)

            result = await self.db.execute(query)
            taxonomy = result.scalar_one_or_none()

            if taxonomy:
                return self._taxonomy_to_dict(taxonomy)
            return None

        except Exception as e:
            logger.error(f"Error getting taxonomy entry: {e}")
            return None

    async def _get_related_skill_names(
        self,
        taxonomy_id: UUID,
        organization_id: Optional[str],
    ) -> List[str]:
        """Get names of skills related to the given taxonomy entry."""
        if not self.db or not self.include_relationships:
            return []

        try:
            # Find relationships where this skill is either source or target
            query = select(SkillRelationship, SkillTaxonomy).join(
                SkillTaxonomy,
                or_(
                    and_(
                        SkillRelationship.target_skill_id == taxonomy_id,
                        SkillTaxonomy.id == SkillRelationship.source_skill_id,
                    ),
                    and_(
                        SkillRelationship.source_skill_id == taxonomy_id,
                        SkillTaxonomy.id == SkillRelationship.target_skill_id,
                    ),
                ),
            ).where(
                and_(
                    SkillRelationship.is_active == True,
                    SkillTaxonomy.is_active == True,
                )
            )

            if organization_id:
                query = query.where(SkillRelationship.organization_id == organization_id)

            result = await self.db.execute(query)
            rows = result.all()

            related_names: List[str] = []
            for relationship, related_taxonomy in rows:
                if related_taxonomy.skill_name not in related_names:
                    related_names.append(related_taxonomy.skill_name)

            return related_names

        except Exception as e:
            logger.error(f"Error getting related skills: {e}")
            return []

    def _taxonomy_to_dict(self, taxonomy: SkillTaxonomy) -> Dict[str, Any]:
        """Convert a taxonomy model to dictionary."""
        return {
            "id": str(taxonomy.id),
            "industry": taxonomy.industry,
            "skill_name": taxonomy.skill_name,
            "context": taxonomy.context,
            "variants": taxonomy.variants or [],
            "extra_metadata": taxonomy.extra_metadata or {},
            "parent_skill_id": str(taxonomy.parent_skill_id) if taxonomy.parent_skill_id else None,
            "category_path": taxonomy.category_path or [],
            "is_active": taxonomy.is_active,
            "version": taxonomy.version,
            "organization_id": taxonomy.organization_id,
        }


# Factory function for dependency injection
def get_taxonomy_matcher_service(
    db: Optional[AsyncSession] = None,
    **kwargs,
) -> TaxonomyMatcherService:
    """
    Get a TaxonomyMatcherService instance.

    This function is designed for use with FastAPI dependency injection.

    Args:
        db: Database session
        **kwargs: Additional arguments to pass to TaxonomyMatcherService

    Returns:
        TaxonomyMatcherService instance

    Example:
        >>> from fastapi import Depends
        >>> from database import get_db
        >>> from services.taxonomy_matcher_service import get_taxonomy_matcher_service
        >>>
        >>> @router.post("/match-skills")
        >>> async def match_skills(
        >>>     skills: List[str],
        >>>     db: AsyncSession = Depends(get_db),
        >>>     matcher: TaxonomyMatcherService = Depends(get_taxonomy_matcher_service)
        >>> ):
        >>>     result = await matcher.match_skills(skills)
        >>>     return result
    """
    return TaxonomyMatcherService(db=db, **kwargs)
