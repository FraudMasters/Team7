"""
Enhanced skill matcher with context awareness and confidence scoring.

This module provides intelligent skill matching that goes beyond simple
string comparison to include:
- Context-aware matching (e.g., React.js ≈ React in web_framework context)
- Confidence scoring for match quality
- Support for industry-specific taxonomies
- Custom organization synonym handling
- Partial match detection with fuzzy matching
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Path to skill synonyms file
SYNONYMS_FILE = Path(__file__).parent.parent / "models" / "skill_synonyms.json"

# Cache for skill synonyms
_synonyms_cache: Optional[Dict[str, List[str]]] = None


class EnhancedSkillMatcher:
    """
    Enhanced skill matcher with context awareness and confidence scoring.

    This matcher provides intelligent skill matching capabilities including:
    - Direct name matching
    - Synonym-based matching
    - Context-aware matching (considers the domain/industry context)
    - Fuzzy matching for typos and variations
    - Confidence scoring for all match types

    Example:
        >>> matcher = EnhancedSkillMatcher()
        >>> result = matcher.match_with_context(['ReactJS'], 'React', context='web_framework')
        >>> print(result['confidence'])
        0.95
        >>> result = matcher.match_with_context(['React Native'], 'React', context='web_framework')
        >>> print(result['confidence'])
        0.7
    """

    def __init__(self, synonyms_file: Optional[Path] = None):
        """
        Initialize the enhanced skill matcher.

        Args:
            synonyms_file: Optional path to custom synonyms JSON file.
                          Defaults to built-in skill_synonyms.json.
        """
        self.synonyms_file = synonyms_file or SYNONYMS_FILE
        self._synonyms_map: Optional[Dict[str, List[str]]] = None
        self._taxonomy_map: Dict[str, Dict[str, List[str]]] = {}

    def load_synonyms(self) -> Dict[str, List[str]]:
        """
        Load skill synonyms from JSON file.

        Returns a dictionary mapping canonical skill names to lists of synonyms.

        The synonyms file structure organizes skills by category (databases,
        programming_languages, web_frameworks, etc.) with each skill having
        a canonical name and list of equivalent terms.

        Returns:
            Dictionary mapping skill names to their synonyms

        Example:
            >>> matcher = EnhancedSkillMatcher()
            >>> synonyms = matcher.load_synonyms()
            >>> synonyms["PostgreSQL"]
            ["PostgreSQL", "Postgres", "Postgres SQL"]
        """
        if self._synonyms_map is not None:
            return self._synonyms_map

        try:
            with open(self.synonyms_file, "r", encoding="utf-8") as f:
                synonyms_data = json.load(f)

            # Flatten the category structure into a single dictionary
            # Input: {"databases": {"SQL": ["SQL", "PostgreSQL", ...]}}
            # Output: {"SQL": ["SQL", "PostgreSQL", ...]}
            flat_synonyms: Dict[str, List[str]] = {}

            for category, skills in synonyms_data.items():
                if isinstance(skills, dict):
                    for canonical_name, synonyms_list in skills.items():
                        if isinstance(synonyms_list, list):
                            # Ensure the canonical name itself is in the list
                            all_synonyms = set(synonyms_list + [canonical_name])
                            flat_synonyms[canonical_name] = list(all_synonyms)

                            # Also build taxonomy map by category
                            if category not in self._taxonomy_map:
                                self._taxonomy_map[category] = {}
                            self._taxonomy_map[category][canonical_name] = list(all_synonyms)

            self._synonyms_map = flat_synonyms
            logger.info(f"Loaded {len(flat_synonyms)} skill synonym mappings")
            return flat_synonyms

        except FileNotFoundError:
            logger.warning(f"Skill synonyms file not found: {self.synonyms_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing skill synonyms JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading skill synonyms: {e}", exc_info=True)
            return {}

    @staticmethod
    def normalize_skill_name(skill: str) -> str:
        """
        Normalize a skill name for consistent comparison.

        Removes extra whitespace, converts to lowercase, handles
        common variations in capitalization and spacing, and removes
        special characters that don't affect meaning.

        Args:
            skill: The skill name to normalize

        Returns:
            Normalized skill name

        Example:
            >>> EnhancedSkillMatcher.normalize_skill_name("  React JS  ")
            "react js"
        """
        # Remove extra whitespace and convert to lowercase
        normalized = " ".join(skill.strip().lower().split())

        # Remove common punctuation that doesn't affect meaning
        # Keep: letters, numbers, spaces, dots, plus, hash
        normalized = "".join(c for c in normalized if c.isalnum() or c in " .+#")

        return normalized

    def calculate_fuzzy_similarity(self, skill1: str, skill2: str) -> float:
        """
        Calculate fuzzy similarity between two skill names.

        Uses SequenceMatcher to determine how similar two strings are,
        useful for detecting typos and minor variations.

        Args:
            skill1: First skill name
            skill2: Second skill name

        Returns:
            Similarity score between 0.0 and 1.0

        Example:
            >>> matcher = EnhancedSkillMatcher()
            >>> matcher.calculate_fuzzy_similarity("React", "ReactJS")
            0.75
        """
        norm1 = self.normalize_skill_name(skill1)
        norm2 = self.normalize_skill_name(skill2)

        return SequenceMatcher(None, norm1, norm2).ratio()

    def find_synonym_match(
        self,
        resume_skills: List[str],
        required_skill: str,
        synonyms_map: Dict[str, List[str]]
    ) -> Optional[Tuple[str, float]]:
        """
        Find a synonym match for the required skill in resume skills.

        Searches through the synonyms map to find if any resume skill
        is a synonym of the required skill.

        Args:
            resume_skills: List of skills extracted from the resume
            required_skill: The skill required by the vacancy
            synonyms_map: Dictionary of skill synonyms

        Returns:
            Tuple of (matched_skill, confidence) if found, None otherwise

        Example:
            >>> matcher = EnhancedSkillMatcher()
            >>> synonyms = {"SQL": ["SQL", "PostgreSQL", "MySQL"]}
            >>> matcher.find_synonym_match(["Java", "PostgreSQL"], "SQL", synonyms)
            ("PostgreSQL", 0.85)
        """
        normalized_required = self.normalize_skill_name(required_skill)

        # Build set of all variants for the required skill
        all_variants = {normalized_required}

        for canonical_name, synonym_list in synonyms_map.items():
            normalized_canonical = self.normalize_skill_name(canonical_name)
            if normalized_canonical == normalized_required:
                all_variants.update([self.normalize_skill_name(s) for s in synonym_list])
            else:
                for synonym in synonym_list:
                    if self.normalize_skill_name(synonym) == normalized_required:
                        all_variants.add(normalized_canonical)
                        all_variants.update([self.normalize_skill_name(s) for s in synonym_list])
                        break

        # Find matching resume skill
        for resume_skill in resume_skills:
            normalized_resume = self.normalize_skill_name(resume_skill)
            if normalized_resume in all_variants:
                # Calculate confidence based on match type
                if normalized_resume == normalized_required:
                    # Direct match after normalization
                    return resume_skill, 0.95
                else:
                    # Synonym match
                    return resume_skill, 0.85

        return None

    def find_context_match(
        self,
        resume_skills: List[str],
        required_skill: str,
        context: Optional[str]
    ) -> Optional[Tuple[str, float]]:
        """
        Find a context-aware match for the required skill.

        Context-aware matching considers the domain/industry to improve
        matching accuracy. For example:
        - "React" in "web_framework" context matches "ReactJS", "React.js"
        - "React" in "mobile" context may NOT match "React Native" (different domain)

        Args:
            resume_skills: List of skills extracted from the resume
            required_skill: The skill required by the vacancy
            context: Optional context hint (e.g., "web_framework", "database", "mobile")

        Returns:
            Tuple of (matched_skill, confidence) if found, None otherwise

        Example:
            >>> matcher = EnhancedSkillMatcher()
            >>> result = matcher.find_context_match(['ReactJS'], 'React', 'web_framework')
            >>> result
            ('ReactJS', 0.95)
        """
        if not context:
            return None

        normalized_context = self.normalize_skill_name(context)
        normalized_required = self.normalize_skill_name(required_skill)

        # Context-specific matching rules
        context_rules: Dict[str, Dict[str, List[str]]] = {
            "web_framework": {
                "react": ["react", "reactjs", "react.js", "reactjs"],
                "vue": ["vue", "vue.js", "vuejs"],
                "angular": ["angular", "angularjs", "angular.js"],
            },
            "database": {
                "sql": ["sql", "postgresql", "mysql", "sqlite", "mssql"],
                "nosql": ["mongodb", "cassandra", "dynamodb", "redis"],
            },
            "language": {
                "javascript": ["javascript", "js", "ecmascript"],
                "typescript": ["typescript", "ts"],
            },
        }

        # Check if context has rules
        if normalized_context not in context_rules:
            return None

        # Check if required skill has context rules
        context_skill_map = context_rules[normalized_context]
        if normalized_required not in context_skill_map:
            return None

        # Find matching resume skill
        allowed_variants = context_skill_map[normalized_required]

        for resume_skill in resume_skills:
            normalized_resume = self.normalize_skill_name(resume_skill)
            if normalized_resume in [self.normalize_skill_name(v) for v in allowed_variants]:
                # High confidence for context-aware match
                return resume_skill, 0.95

        return None

    def find_fuzzy_match(
        self,
        resume_skills: List[str],
        required_skill: str,
        threshold: float = 0.7
    ) -> Optional[Tuple[str, float]]:
        """
        Find a fuzzy match for the required skill in resume skills.

        Uses string similarity to detect typos and minor variations.
        Useful when the resume has "ReactJS" and vacancy requires "React.js".

        Args:
            resume_skills: List of skills extracted from the resume
            required_skill: The skill required by the vacancy
            threshold: Minimum similarity score (0.0-1.0) to consider a match

        Returns:
            Tuple of (matched_skill, confidence) if found, None otherwise

        Example:
            >>> matcher = EnhancedSkillMatcher()
            >>> result = matcher.find_fuzzy_match(['ReactJS'], 'React.js')
            >>> result
            ('ReactJS', 0.85)
        """
        best_match: Optional[Tuple[str, float]] = None
        best_similarity = 0.0

        for resume_skill in resume_skills:
            similarity = self.calculate_fuzzy_similarity(resume_skill, required_skill)

            if similarity >= threshold and similarity > best_similarity:
                best_match = (resume_skill, similarity)
                best_similarity = similarity

        return best_match

    def match_with_context(
        self,
        resume_skills: List[str],
        required_skill: str,
        context: Optional[str] = None,
        organization_id: Optional[str] = None,
        use_fuzzy: bool = True
    ) -> Dict[str, Any]:
        """
        Match a required skill against resume skills with context awareness.

        This is the main matching method that combines multiple matching strategies:
        1. Direct match (highest confidence)
        2. Context-aware match (high confidence)
        3. Synonym match (medium-high confidence)
        4. Fuzzy match (medium confidence)

        Args:
            resume_skills: List of skills extracted from the resume
            required_skill: The skill required by the vacancy
            context: Optional context hint (e.g., "web_framework", "database")
            organization_id: Optional organization ID for custom synonyms
            use_fuzzy: Whether to use fuzzy matching (default: True)

        Returns:
            Dictionary with match results:
            - matched (bool): Whether a match was found
            - confidence (float): Confidence score (0.0-1.0)
            - matched_as (str|None): The actual skill name from resume that matched
            - match_type (str): Type of match ('direct', 'context', 'synonym', 'fuzzy', 'none')

        Example:
            >>> matcher = EnhancedSkillMatcher()
            >>> result = matcher.match_with_context(['ReactJS'], 'React', context='web_framework')
            >>> result['matched']
            True
            >>> result['confidence']
            0.95
        """
        result: Dict[str, Any] = {
            "matched": False,
            "confidence": 0.0,
            "matched_as": None,
            "match_type": "none",
        }

        if not resume_skills or not required_skill:
            return result

        # Load synonyms if not already loaded
        synonyms_map = self.load_synonyms()

        normalized_required = self.normalize_skill_name(required_skill)

        # Strategy 1: Direct match
        for resume_skill in resume_skills:
            if self.normalize_skill_name(resume_skill) == normalized_required:
                result.update({
                    "matched": True,
                    "confidence": 1.0,
                    "matched_as": resume_skill,
                    "match_type": "direct"
                })
                return result

        # Strategy 2: Context-aware match
        if context:
            context_match = self.find_context_match(resume_skills, required_skill, context)
            if context_match:
                matched_skill, confidence = context_match
                result.update({
                    "matched": True,
                    "confidence": confidence,
                    "matched_as": matched_skill,
                    "match_type": "context"
                })
                return result

        # Strategy 3: Synonym match
        synonym_match = self.find_synonym_match(resume_skills, required_skill, synonyms_map)
        if synonym_match:
            matched_skill, confidence = synonym_match
            result.update({
                "matched": True,
                "confidence": confidence,
                "matched_as": matched_skill,
                "match_type": "synonym"
            })
            return result

        # Strategy 4: Fuzzy match
        if use_fuzzy:
            fuzzy_match = self.find_fuzzy_match(resume_skills, required_skill)
            if fuzzy_match:
                matched_skill, confidence = fuzzy_match
                result.update({
                    "matched": True,
                    "confidence": confidence,
                    "matched_as": matched_skill,
                    "match_type": "fuzzy"
                })
                return result

        # No match found
        return result

    def match_multiple(
        self,
        resume_skills: List[str],
        required_skills: List[str],
        context: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Match multiple required skills against resume skills.

        Args:
            resume_skills: List of skills extracted from the resume
            required_skills: List of skills required by the vacancy
            context: Optional context hint for all matches
            organization_id: Optional organization ID for custom synonyms

        Returns:
            Dictionary mapping each required skill to its match result

        Example:
            >>> matcher = EnhancedSkillMatcher()
            >>> results = matcher.match_multiple(
            ...     ['ReactJS', 'Python', 'PostgreSQL'],
            ...     ['React', 'Python', 'SQL'],
            ...     context='web_framework'
            ... )
            >>> results['React']['matched']
            True
            >>> results['SQL']['matched']
            True  # PostgreSQL matched via synonym
        """
        results: Dict[str, Dict[str, Any]] = {}

        for skill in required_skills:
            results[skill] = self.match_with_context(
                resume_skills, skill, context, organization_id
            )

        return results

    def calculate_match_percentage(
        self,
        match_results: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Calculate overall match percentage from multiple match results.

        Args:
            match_results: Dictionary of skill match results from match_multiple()

        Returns:
            Match percentage (0.0-100.0)

        Example:
            >>> matcher = EnhancedSkillMatcher()
            >>> results = matcher.match_multiple(['React'], ['React', 'Python'])
            >>> matcher.calculate_match_percentage(results)
            50.0
        """
        if not match_results:
            return 0.0

        total = len(match_results)
        matched = sum(1 for r in match_results.values() if r.get("matched", False))

        return round((matched / total * 100), 2) if total > 0 else 0.0

    def get_low_confidence_matches(
        self,
        match_results: Dict[str, Dict[str, Any]],
        threshold: float = 0.8
    ) -> List[str]:
        """
        Get list of skills with low confidence matches.

        Useful for flagging matches that may need recruiter review.

        Args:
            match_results: Dictionary of skill match results from match_multiple()
            threshold: Confidence threshold below which matches are considered low

        Returns:
            List of skill names with low confidence matches

        Example:
            >>> matcher = EnhancedSkillMatcher()
            >>> results = matcher.match_multiple(['ReactJS'], ['React', 'Python'])
            >>> low_conf = matcher.get_low_confidence_matches(results, threshold=0.9)
            >>> 'React' in low_conf
            True  # Assuming synonym match with 0.85 confidence
        """
        return [
            skill
            for skill, result in match_results.items()
            if result.get("matched", False) and result.get("confidence", 0) < threshold
        ]
