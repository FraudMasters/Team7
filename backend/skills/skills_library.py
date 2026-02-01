"""
Skills library for position-specific skill taxonomies.

This module provides a SkillsLibrary class that loads and manages
position-specific skill taxonomies from JSON configuration. It supports
querying skills by position, normalizing skill names, and matching
position variants.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Path to position skills file
POSITION_SKILLS_FILE = Path(__file__).parent / "position_skills.json"

# Cache for loaded position skills
_position_skills_cache: Optional[Dict[str, Dict[str, List[str]]]] = None


class SkillsLibrary:
    """
    Skills library for position-specific taxonomies.

    This class provides methods to load and query position-specific
    skill taxonomies, including required skills, optional skills,
    and position name variants.

    Attributes:
        use_cache: Whether to cache loaded taxonomies for performance

    Example:
        >>> lib = SkillsLibrary()
        >>> skills = lib.get_skills_for_position("frontend_developer")
        >>> print(skills["required_skills"])
        ['JavaScript', 'TypeScript', 'HTML', 'CSS', 'React', ...]
    """

    def __init__(self, use_cache: bool = True) -> None:
        """
        Initialize the skills library.

        Args:
            use_cache: Whether to cache loaded position skills (default: True)
        """
        self.use_cache = use_cache

    def load_position_skills(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Load position-specific skills from JSON file.

        This method loads the complete position skills taxonomy from
        the JSON configuration file, which includes required skills,
        optional skills, and position name variants for each position.

        Returns:
            Dictionary mapping position IDs to their skill taxonomies

        Example:
            >>> lib = SkillsLibrary()
            >>> positions = lib.load_position_skills()
            >>> positions["frontend_developer"]["required_skills"]
            ['JavaScript', 'TypeScript', 'HTML', ...]
        """
        global _position_skills_cache

        if self.use_cache and _position_skills_cache is not None:
            return _position_skills_cache

        try:
            with open(POSITION_SKILLS_FILE, "r", encoding="utf-8") as f:
                skills_data = json.load(f)

            if self.use_cache:
                _position_skills_cache = skills_data

            logger.info(
                f"Loaded {len(skills_data)} position skill taxonomies "
                f"from {POSITION_SKILLS_FILE}"
            )
            return skills_data

        except FileNotFoundError:
            logger.error(f"Position skills file not found: {POSITION_SKILLS_FILE}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing position skills JSON: {e}")
            return {}
        except Exception as e:
            logger.error(
                f"Error loading position skills: {e}", exc_info=True
            )
            return {}

    def get_skills_for_position(
        self, position_id: str
    ) -> Optional[Dict[str, List[str]]]:
        """
        Get skills taxonomy for a specific position.

        Returns the complete skill taxonomy for a position, including
        required skills, optional skills, and position variants.

        Args:
            position_id: Position identifier (e.g., "frontend_developer")

        Returns:
            Dictionary with required_skills, optional_skills, and
            position_variants lists, or None if position not found

        Example:
            >>> lib = SkillsLibrary()
            >>> skills = lib.get_skills_for_position("frontend_developer")
            >>> print(skills["required_skills"])
            ['JavaScript', 'TypeScript', 'HTML', 'CSS', ...]
        """
        positions = self.load_position_skills()
        return positions.get(position_id)

    def get_required_skills(self, position_id: str) -> List[str]:
        """
        Get required skills for a position.

        Args:
            position_id: Position identifier

        Returns:
            List of required skill names, or empty list if position not found

        Example:
            >>> lib = SkillsLibrary()
            >>> req = lib.get_required_skills("backend_developer")
            >>> print(req)
            ['Python', 'Java', 'Node.js', 'SQL', 'REST', 'Git']
        """
        position_data = self.get_skills_for_position(position_id)
        if position_data:
            return position_data.get("required_skills", [])
        return []

    def get_optional_skills(self, position_id: str) -> List[str]:
        """
        Get optional skills for a position.

        Args:
            position_id: Position identifier

        Returns:
            List of optional skill names, or empty list if position not found

        Example:
            >>> lib = SkillsLibrary()
            >>> opt = lib.get_optional_skills("backend_developer")
            >>> print(opt)
            ['Django', 'Flask', 'Spring', 'Express', ...]
        """
        position_data = self.get_skills_for_position(position_id)
        if position_data:
            return position_data.get("optional_skills", [])
        return []

    def get_all_skills_for_position(self, position_id: str) -> List[str]:
        """
        Get all skills (required + optional) for a position.

        Args:
            position_id: Position identifier

        Returns:
            Combined list of required and optional skills

        Example:
            >>> lib = SkillsLibrary()
            >>> all_skills = lib.get_all_skills_for_position("frontend_developer")
            >>> print(len(all_skills))
            30
        """
        required = self.get_required_skills(position_id)
        optional = self.get_optional_skills(position_id)
        return list(set(required + optional))

    def get_position_variants(self, position_id: str) -> List[str]:
        """
        Get position name variants for a position.

        Returns a list of common name variations for the position
        (e.g., "Frontend Developer", "Front-End Developer", "UI Developer").

        Args:
            position_id: Position identifier

        Returns:
            List of position name variants, or empty list if not found

        Example:
            >>> lib = SkillsLibrary()
            >>> variants = lib.get_position_variants("frontend_developer")
            >>> print(variants)
            ['Frontend Developer', 'Front-End Developer', ...]
        """
        position_data = self.get_skills_for_position(position_id)
        if position_data:
            return position_data.get("position_variants", [])
        return []

    def get_all_positions(self) -> List[str]:
        """
        Get list of all available position IDs.

        Returns:
            List of all position identifiers in the library

        Example:
            >>> lib = SkillsLibrary()
            >>> positions = lib.get_all_positions()
            >>> print(positions)
            ['frontend_developer', 'backend_developer', ...]
        """
        positions = self.load_position_skills()
        return list(positions.keys())

    def get_all_skills(self) -> Set[str]:
        """
        Get set of all unique skills across all positions.

        Returns a deduplicated set of all skill names mentioned
        in any position's required or optional skills.

        Returns:
            Set of all unique skill names

        Example:
            >>> lib = SkillsLibrary()
            >>> skills = lib.get_all_skills()
            >>> print(len(skills))
            150
        """
        positions = self.load_position_skills()
        all_skills: Set[str] = set()

        for position_data in positions.values():
            required = position_data.get("required_skills", [])
            optional = position_data.get("optional_skills", [])
            all_skills.update(required)
            all_skills.update(optional)

        return all_skills

    def find_position_by_variant(
        self, position_name: str, fuzzy_threshold: int = 80
    ) -> Optional[str]:
        """
        Find position ID by matching against position variants.

        Attempts to find a position ID by matching the given position
        name against all position variants (exact match first, then
        case-insensitive match).

        Args:
            position_name: Position name to search for
            fuzzy_threshold: Minimum similarity score for fuzzy matching (0-100)

        Returns:
            Matching position ID, or None if no match found

        Example:
            >>> lib = SkillsLibrary()
            >>> pos_id = lib.find_position_by_variant("Front-End Developer")
            >>> print(pos_id)
            'frontend_developer'
        """
        positions = self.load_position_skills()

        # Try exact match first
        for pos_id, pos_data in positions.items():
            variants = pos_data.get("position_variants", [])
            if position_name in variants:
                return pos_id

        # Try case-insensitive match
        position_name_lower = position_name.lower()
        for pos_id, pos_data in positions.items():
            variants = pos_data.get("position_variants", [])
            for variant in variants:
                if variant.lower() == position_name_lower:
                    return pos_id

        # If rapidfuzz is available, try fuzzy matching
        try:
            from rapidfuzz import process, fuzz

            # Build list of all variants
            all_variants = []
            for pos_id, pos_data in positions.items():
                variants = pos_data.get("position_variants", [])
                for variant in variants:
                    all_variants.append((variant, pos_id))

            # Find best match
            result = process.extractOne(
                position_name,
                [v[0] for v in all_variants],
                scorer=fuzz.WRatio
            )

            if result and result[1] >= fuzzy_threshold:
                # Find the position_id for this variant
                best_variant = result[0]
                for variant, pos_id in all_variants:
                    if variant == best_variant:
                        return pos_id

        except ImportError:
            logger.debug("rapidfuzz not available, skipping fuzzy match")

        return None

    def check_skill_match(
        self, position_id: str, candidate_skills: List[str]
    ) -> Dict[str, any]:
        """
        Check how well a candidate's skills match a position.

        Compares candidate's skills against position requirements
        and returns match statistics.

        Args:
            position_id: Position identifier
            candidate_skills: List of candidate's skills

        Returns:
            Dictionary with match statistics:
            - required_matched: List of matched required skills
            - required_missing: List of missing required skills
            - optional_matched: List of matched optional skills
            - required_match_rate: Percentage of required skills matched
            - total_match_rate: Percentage of all skills matched

        Example:
            >>> lib = SkillsLibrary()
            >>> result = lib.check_skill_match(
            ...     "frontend_developer",
            ...     ["JavaScript", "React", "Python"]
            ... )
            >>> print(result["required_match_rate"])
            37.5
        """
        required = set(self.get_required_skills(position_id))
        optional = set(self.get_optional_skills(position_id))
        candidate_set = set(candidate_skills)

        required_matched = list(required & candidate_set)
        required_missing = list(required - candidate_set)
        optional_matched = list(optional & candidate_set)

        required_match_rate = (
            len(required_matched) / len(required) * 100 if required else 0
        )

        all_position_skills = required | optional
        total_matched = required_matched + optional_matched
        total_match_rate = (
            len(total_matched) / len(all_position_skills) * 100
            if all_position_skills
            else 0
        )

        return {
            "required_matched": required_matched,
            "required_missing": required_missing,
            "optional_matched": optional_matched,
            "required_match_rate": round(required_match_rate, 2),
            "total_match_rate": round(total_match_rate, 2),
        }

    def clear_cache(self) -> None:
        """
        Clear cached position skills data.

        Example:
            >>> lib = SkillsLibrary()
            >>> lib.clear_cache()
        """
        global _position_skills_cache
        _position_skills_cache = None
        logger.info("Position skills cache cleared")


# Convenience functions for backward compatibility

def load_position_skills() -> Dict[str, Dict[str, List[str]]]:
    """
    Load position skills from JSON file.

    Convenience function that creates a SkillsLibrary instance
    and loads position skills.

    Returns:
        Dictionary of position skill taxonomies

    Example:
        >>> skills = load_position_skills()
        >>> print(skills["frontend_developer"]["required_skills"])
        ['JavaScript', 'TypeScript', 'HTML', ...]
    """
    lib = SkillsLibrary()
    return lib.load_position_skills()


def get_skills_for_position(position_id: str) -> Optional[Dict[str, List[str]]]:
    """
    Get skills for a specific position.

    Convenience function that creates a SkillsLibrary instance
    and returns skills for a position.

    Args:
        position_id: Position identifier

    Returns:
        Dictionary with position skills, or None if not found

    Example:
        >>> skills = get_skills_for_position("backend_developer")
        >>> print(skills["required_skills"])
        ['Python', 'Java', 'Node.js', ...]
    """
    lib = SkillsLibrary()
    return lib.get_skills_for_position(position_id)
