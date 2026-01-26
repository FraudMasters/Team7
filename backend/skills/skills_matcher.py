"""
Skills matching with fuzzy matching and semantic similarity.

This module provides the SkillsMatcher class for matching candidate skills
against known skills using rapidfuzz for fuzzy string matching and optional
semantic similarity using sentence-transformers embeddings.
"""
import logging
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Global model instance for semantic similarity
_semantic_model: Optional["SentenceTransformer"] = None


def _get_semantic_model(model_name: str = "all-MiniLM-L6-v2") -> "SentenceTransformer":
    """
    Get or initialize the semantic similarity model.

    Args:
        model_name: Name of the sentence-transformers model to use

    Returns:
        Initialized SentenceTransformer model instance

    Raises:
        ImportError: If sentence-transformers is not installed
        RuntimeError: If model fails to load
    """
    global _semantic_model

    if _semantic_model is None:
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading sentence-transformers model: {model_name}")
            _semantic_model = SentenceTransformer(model_name)
            logger.info("Sentence-transformers model loaded successfully")
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install it with: pip install sentence-transformers"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to load sentence-transformers model: {e}") from e

    return _semantic_model


class SkillsMatcher:
    """
    Skills matcher with fuzzy matching and semantic similarity.

    This class matches candidate skills against a known skills library using:
    - Rapidfuzz for fuzzy string matching (handles typos, variations)
    - Optional semantic similarity using sentence-transformers embeddings
    - Configurable matching thresholds and strategies

    Attributes:
        fuzzy_threshold: Minimum similarity score for fuzzy matching (0-100)
        semantic_threshold: Minimum similarity for semantic matching (0-1)
        use_semantic: Whether to use semantic similarity matching
        case_sensitive: Whether matching should be case-sensitive

    Example:
        >>> matcher = SkillsMatcher(fuzzy_threshold=85)
        >>> result = matcher.match_skill("React.js", ["React", "ReactJS", "Vue"])
        >>> print(result["matched_skill"])
        'React'
        >>> print(result["score"])
        90
    """

    def __init__(
        self,
        *,
        fuzzy_threshold: int = 80,
        semantic_threshold: float = 0.75,
        use_semantic: bool = False,
        case_sensitive: bool = False,
    ) -> None:
        """
        Initialize the skills matcher.

        Args:
            fuzzy_threshold: Minimum fuzzy similarity score (0-100, default: 80)
            semantic_threshold: Minimum semantic similarity (0-1, default: 0.75)
            use_semantic: Whether to use semantic similarity (default: False)
            case_sensitive: Whether matching is case-sensitive (default: False)

        Raises:
            ValueError: If threshold values are out of valid range
        """
        if not 0 <= fuzzy_threshold <= 100:
            raise ValueError("fuzzy_threshold must be between 0 and 100")

        if not 0.0 <= semantic_threshold <= 1.0:
            raise ValueError("semantic_threshold must be between 0.0 and 1.0")

        self.fuzzy_threshold = fuzzy_threshold
        self.semantic_threshold = semantic_threshold
        self.use_semantic = use_semantic
        self.case_sensitive = case_sensitive

        logger.info(
            f"SkillsMatcher initialized (fuzzy_threshold={fuzzy_threshold}, "
            f"use_semantic={use_semantic})"
        )

    def normalize_skill(self, skill: str) -> str:
        """
        Normalize a skill name for matching.

        Removes common variations in formatting, whitespace, and special characters.

        Args:
            skill: Raw skill name

        Returns:
            Normalized skill name

        Example:
            >>> matcher = SkillsMatcher()
            >>> matcher.normalize_skill("React.js")
            'reactjs'
            >>> matcher.normalize_skill("  Machine Learning  ")
            'machine learning'
        """
        if not skill:
            return ""

        # Strip whitespace
        normalized = skill.strip()

        # Convert to lowercase if not case-sensitive
        if not self.case_sensitive:
            normalized = normalized.lower()

        # Remove common separators and dots
        for separator in [".", "-", "_", "+", "#"]:
            normalized = normalized.replace(separator, "")

        # Normalize whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def match_skill(
        self,
        candidate_skill: str,
        known_skills: List[str],
        *,
        use_fuzzy: bool = True,
        use_semantic: Optional[bool] = None,
    ) -> Dict[str, Optional[Union[str, int, float]]]:
        """
        Match a candidate skill against a list of known skills.

        Attempts to find the best match using:
        1. Exact match (after normalization)
        2. Fuzzy match (if enabled, using rapidfuzz)
        3. Semantic match (if enabled, using embeddings)

        Args:
            candidate_skill: The skill to match
            known_skills: List of known skills to match against
            use_fuzzy: Whether to use fuzzy matching (default: True)
            use_semantic: Whether to use semantic matching (default: from instance)

        Returns:
            Dictionary containing:
                - matched_skill: Best matching skill (or None if no match)
                - score: Similarity score (0-100 for fuzzy, 0-1 for semantic)
                - match_type: Type of match ('exact', 'fuzzy', 'semantic', or None)
                - error: Error message if matching failed

        Example:
            >>> matcher = SkillsMatcher()
            >>> result = matcher.match_skill("React.js", ["React", "Vue", "Angular"])
            >>> print(result["matched_skill"])
            'React'
            >>> print(result["match_type"])
            'fuzzy'
        """
        # Validate inputs
        if not candidate_skill or not isinstance(candidate_skill, str):
            return {
                "matched_skill": None,
                "score": 0,
                "match_type": None,
                "error": "candidate_skill must be a non-empty string",
            }

        if not known_skills or not isinstance(known_skills, list):
            return {
                "matched_skill": None,
                "score": 0,
                "match_type": None,
                "error": "known_skills must be a non-empty list",
            }

        # Normalize candidate skill
        normalized_candidate = self.normalize_skill(candidate_skill)

        # Normalize known skills for matching
        normalized_known = {
            self.normalize_skill(skill): skill for skill in known_skills
        }

        # Try exact match first
        if normalized_candidate in normalized_known:
            matched = normalized_known[normalized_candidate]
            logger.debug(f"Exact match found: '{candidate_skill}' -> '{matched}'")
            return {
                "matched_skill": matched,
                "score": 100,
                "match_type": "exact",
                "error": None,
            }

        # Try fuzzy matching
        if use_fuzzy:
            try:
                from rapidfuzz import process, fuzz

                # Use normalized skills for fuzzy matching
                normalized_list = list(normalized_known.keys())

                result = process.extractOne(
                    normalized_candidate,
                    normalized_list,
                    scorer=fuzz.WRatio,
                )

                if result and result[1] >= self.fuzzy_threshold:
                    matched_normalized, score = result
                    matched = normalized_known[matched_normalized]
                    logger.debug(
                        f"Fuzzy match found: '{candidate_skill}' -> '{matched}' (score: {score})"
                    )
                    return {
                        "matched_skill": matched,
                        "score": score,
                        "match_type": "fuzzy",
                        "error": None,
                    }

            except ImportError:
                logger.warning("rapidfuzz not installed, skipping fuzzy matching")
            except Exception as e:
                logger.error(f"Fuzzy matching failed: {e}")
                return {
                    "matched_skill": None,
                    "score": 0,
                    "match_type": None,
                    "error": f"Fuzzy matching failed: {str(e)}",
                }

        # Try semantic matching
        should_use_semantic = use_semantic if use_semantic is not None else self.use_semantic
        if should_use_semantic:
            try:
                model = _get_semantic_model()

                # Encode candidate and known skills
                candidate_embedding = model.encode([normalized_candidate])
                known_embeddings = model.encode(list(normalized_known.keys()))

                # Calculate cosine similarity
                import numpy as np

                similarities = np.dot(candidate_embedding, known_embeddings.T)[0]
                best_idx = int(np.argmax(similarities))
                best_score = float(similarities[best_idx])

                if best_score >= self.semantic_threshold:
                    matched_normalized = list(normalized_known.keys())[best_idx]
                    matched = normalized_known[matched_normalized]
                    # Convert to 0-100 scale for consistency
                    score_100 = round(best_score * 100, 2)
                    logger.debug(
                        f"Semantic match found: '{candidate_skill}' -> '{matched}' "
                        f"(score: {score_100})"
                    )
                    return {
                        "matched_skill": matched,
                        "score": score_100,
                        "match_type": "semantic",
                        "error": None,
                    }

            except ImportError:
                logger.warning("sentence-transformers not installed, skipping semantic matching")
            except Exception as e:
                logger.error(f"Semantic matching failed: {e}")
                return {
                    "matched_skill": None,
                    "score": 0,
                    "match_type": None,
                    "error": f"Semantic matching failed: {str(e)}",
                }

        # No match found
        logger.debug(f"No match found for '{candidate_skill}'")
        return {
            "matched_skill": None,
            "score": 0,
            "match_type": None,
            "error": None,
        }

    def match_skills(
        self,
        candidate_skills: List[str],
        known_skills: List[str],
        *,
        use_fuzzy: bool = True,
        use_semantic: Optional[bool] = None,
    ) -> Dict[str, Optional[Union[List[str], Dict[str, Dict[str, Union[str, int]]], str]]]:
        """
        Match multiple candidate skills against known skills.

        Args:
            candidate_skills: List of candidate skills to match
            known_skills: List of known skills to match against
            use_fuzzy: Whether to use fuzzy matching (default: True)
            use_semantic: Whether to use semantic matching (default: from instance)

        Returns:
            Dictionary containing:
                - matched: Dict mapping original skills to matched skills with metadata
                - unmatched: List of skills that didn't match
                - matched_skills: List of successfully matched skill names
                - match_rate: Percentage of skills that matched
                - error: Error message if matching failed

        Example:
            >>> matcher = SkillsMatcher()
            >>> result = matcher.match_skills(
            ...     ["React.js", "VueJS", "UnknownSkill"],
            ...     ["React", "Vue", "Angular"]
            ... )
            >>> print(result["matched_skills"])
            ['React', 'Vue']
            >>> print(result["unmatched"])
            ['UnknownSkill']
        """
        # Validate inputs
        if not candidate_skills or not isinstance(candidate_skills, list):
            return {
                "matched": None,
                "unmatched": None,
                "matched_skills": None,
                "match_rate": 0,
                "error": "candidate_skills must be a non-empty list",
            }

        if not known_skills or not isinstance(known_skills, list):
            return {
                "matched": None,
                "unmatched": None,
                "matched_skills": None,
                "match_rate": 0,
                "error": "known_skills must be a non-empty list",
            }

        try:
            matched = {}
            matched_skills = []
            unmatched = []

            for skill in candidate_skills:
                if not skill or not isinstance(skill, str):
                    continue

                result = self.match_skill(
                    skill,
                    known_skills,
                    use_fuzzy=use_fuzzy,
                    use_semantic=use_semantic,
                )

                if result.get("error"):
                    logger.warning(f"Error matching '{skill}': {result['error']}")
                    unmatched.append(skill)
                elif result.get("matched_skill"):
                    matched[skill] = {
                        "skill": result["matched_skill"],
                        "score": result["score"],
                        "type": result["match_type"],
                    }
                    matched_skills.append(result["matched_skill"])
                else:
                    unmatched.append(skill)

            # Remove duplicates from matched_skills while preserving order
            seen = set()
            unique_matched = []
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

    def match_position_skills(
        self,
        candidate_skills: List[str],
        position_id: str,
        skills_library: Optional["SkillsLibrary"] = None,
    ) -> Dict[str, Optional[Union[Dict[str, any], str]]]:
        """
        Match candidate skills against position-specific skill taxonomy.

        Args:
            candidate_skills: List of candidate's skills
            position_id: Position identifier (e.g., "frontend_developer")
            skills_library: SkillsLibrary instance (created if not provided)

        Returns:
            Dictionary containing:
                - required_matched: Matched required skills
                - required_missing: Missing required skills
                - optional_matched: Matched optional skills
                - match_details: Full match details for all skills
                - required_match_rate: Percentage of required skills matched
                - total_match_rate: Percentage of all skills matched
                - error: Error message if matching failed

        Example:
            >>> from skills.skills_library import SkillsLibrary
            >>> matcher = SkillsMatcher()
            >>> lib = SkillsLibrary()
            >>> result = matcher.match_position_skills(
            ...     ["React", "Python"],
            ...     "frontend_developer",
            ...     lib
            ... )
            >>> print(result["required_match_rate"])
            50.0
        """
        try:
            # Import SkillsLibrary if not provided
            if skills_library is None:
                from .skills_library import SkillsLibrary

                skills_library = SkillsLibrary()

            # Get position skills
            required = skills_library.get_required_skills(position_id)
            optional = skills_library.get_optional_skills(position_id)

            if not required and not optional:
                return {
                    "required_matched": None,
                    "required_missing": None,
                    "optional_matched": None,
                    "match_details": None,
                    "required_match_rate": 0,
                    "total_match_rate": 0,
                    "error": f"Position '{position_id}' not found or has no skills",
                }

            all_position_skills = required + optional

            # Match skills
            match_result = self.match_skills(candidate_skills, all_position_skills)

            if match_result.get("error"):
                return {
                    "required_matched": None,
                    "required_missing": None,
                    "optional_matched": None,
                    "match_details": None,
                    "required_match_rate": 0,
                    "total_match_rate": 0,
                    "error": match_result["error"],
                }

            matched_skills = set(match_result.get("matched_skills", []))

            # Categorize matches
            required_matched = [s for s in required if s in matched_skills]
            required_missing = [s for s in required if s not in matched_skills]
            optional_matched = [s for s in optional if s in matched_skills]

            # Calculate match rates
            required_match_rate = (
                len(required_matched) / len(required) * 100 if required else 0
            )
            total_match_rate = (
                len(required_matched) + len(optional_matched)
            ) / len(all_position_skills) * 100 if all_position_skills else 0

            return {
                "required_matched": required_matched if required_matched else None,
                "required_missing": required_missing if required_missing else None,
                "optional_matched": optional_matched if optional_matched else None,
                "match_details": match_result.get("matched"),
                "required_match_rate": round(required_match_rate, 2),
                "total_match_rate": round(total_match_rate, 2),
                "error": None,
            }

        except Exception as e:
            logger.error(f"Position skills matching failed: {e}")
            return {
                "required_matched": None,
                "required_missing": None,
                "optional_matched": None,
                "match_details": None,
                "required_match_rate": 0,
                "total_match_rate": 0,
                "error": f"Matching failed: {str(e)}",
            }


# Convenience functions for backward compatibility

def match_skill(
    candidate_skill: str,
    known_skills: List[str],
    *,
    fuzzy_threshold: int = 80,
    case_sensitive: bool = False,
) -> Dict[str, Optional[Union[str, int, float]]]:
    """
    Match a single skill against known skills using fuzzy matching.

    Convenience function that creates a SkillsMatcher instance
    and performs matching.

    Args:
        candidate_skill: The skill to match
        known_skills: List of known skills
        fuzzy_threshold: Minimum similarity threshold (0-100)
        case_sensitive: Whether matching should be case-sensitive

    Returns:
        Dictionary with match results

    Example:
        >>> result = match_skill("React.js", ["React", "Vue", "Angular"])
        >>> print(result["matched_skill"])
        'React'
    """
    matcher = SkillsMatcher(
        fuzzy_threshold=fuzzy_threshold,
        case_sensitive=case_sensitive,
    )
    return matcher.match_skill(candidate_skill, known_skills)


def match_skills(
    candidate_skills: List[str],
    known_skills: List[str],
    *,
    fuzzy_threshold: int = 80,
) -> Dict[str, Optional[Union[List[str], Dict[str, Dict[str, Union[str, int]]], str]]]:
    """
    Match multiple skills against known skills using fuzzy matching.

    Convenience function that creates a SkillsMatcher instance
    and performs matching.

    Args:
        candidate_skills: List of candidate skills
        known_skills: List of known skills
        fuzzy_threshold: Minimum similarity threshold (0-100)

    Returns:
        Dictionary with match results

    Example:
        >>> result = match_skills(
        ...     ["React.js", "VueJS"],
        ...     ["React", "Vue", "Angular"]
        ... )
        >>> print(result["matched_skills"])
        ['React', 'Vue']
    """
    matcher = SkillsMatcher(fuzzy_threshold=fuzzy_threshold)
    return matcher.match_skills(candidate_skills, known_skills)
