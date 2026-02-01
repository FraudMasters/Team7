"""
Skill suggestion service for finding similar skills when required skills are missing.

This module provides intelligent skill suggestion capabilities that help identify
alternative skills from a candidate's resume that are similar to missing required skills:
- Synonym-based suggestions (e.g., PostgreSQL suggested for SQL)
- Category-based suggestions (e.g., MongoDB suggested for databases)
- Fuzzy matching suggestions (e.g., ReactJS suggested for React)
- Related skill suggestions (e.g., Express suggested for Node.js)
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Path to skill synonyms file
SYNONYMS_FILE = Path(__file__).parent.parent / "models" / "skill_synonyms.json"

# Related skill mappings for suggestions
RELATED_SKILLS = {
    "node.js": ["express", "nest.js", "koa", "socket.io"],
    "react": ["redux", "react hooks", "next.js", "jest"],
    "angular": ["rxjs", "typescript", "ngx"],
    "vue": ["vuex", "vue router", "nuxt"],
    "django": ["flask", "fastapi", "python", "sqlalchemy"],
    "spring": ["java", "hibernate", "maven", "gradle"],
    "docker": ["kubernetes", "docker compose", "container"],
    "kubernetes": ["docker", "helm", "k8s", "kubectl"],
    "aws": ["lambda", "ec2", "s3", "rds", "cloudformation"],
    "azure": ["azure devops", "azure functions", "azure ad"],
    "sql": ["postgresql", "mysql", "sqlite", "oracle", "mssql"],
    "nosql": ["mongodb", "cassandra", "dynamodb", "redis", "elasticsearch"],
}


class SkillSuggester:
    """
    Skill suggestion service for finding similar skills when required skills are missing.

    This service helps identify alternative skills from a candidate's resume that
    are similar to missing required skills, using multiple strategies:
    - Synonym-based suggestions (highest confidence)
    - Category-based suggestions (medium-high confidence)
    - Related skill suggestions (medium confidence)
    - Fuzzy matching suggestions (lower confidence)

    Example:
        >>> suggester = SkillSuggester()
        >>> suggestions = suggester.suggest_alternatives(
        ...     missing_skill="SQL",
        ...     resume_skills=["PostgreSQL", "MongoDB", "Redis"]
        ... )
        >>> print(suggestions[0]['skill'])
        "PostgreSQL"
        >>> print(suggestions[0]['confidence'])
        0.85
    """

    def __init__(self, synonyms_file: Optional[Path] = None):
        """
        Initialize the skill suggester.

        Args:
            synonyms_file: Optional path to custom synonyms JSON file.
                          Defaults to built-in skill_synonyms.json.
        """
        self.synonyms_file = synonyms_file or SYNONYMS_FILE
        self._synonyms_map: Optional[Dict[str, List[str]]] = None
        self._category_map: Dict[str, List[str]] = {}
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
            >>> suggester = SkillSuggester()
            >>> synonyms = suggester.load_synonyms()
            >>> synonyms["PostgreSQL"]
            ["PostgreSQL", "Postgres", "Postgres SQL"]
        """
        if self._synonyms_map is not None:
            return self._synonyms_map

        try:
            with open(self.synonyms_file, "r", encoding="utf-8") as f:
                synonyms_data = json.load(f)

            # Flatten the category structure into a single dictionary
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

                            # Build category map for all skills in category
                            if category not in self._category_map:
                                self._category_map[category] = []
                            self._category_map[category].extend(list(all_synonyms))

                    # Deduplicate category lists
                    self._category_map[category] = list(set(self._category_map[category]))

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
            >>> SkillSuggester.normalize_skill_name("  React JS  ")
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
            >>> suggester = SkillSuggester()
            >>> suggester.calculate_fuzzy_similarity("React", "ReactJS")
            0.75
        """
        norm1 = self.normalize_skill_name(skill1)
        norm2 = self.normalize_skill_name(skill2)

        return SequenceMatcher(None, norm1, norm2).ratio()

    def find_synonym_suggestions(
        self,
        missing_skill: str,
        resume_skills: List[str],
        synonyms_map: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Find synonym-based suggestions for a missing skill.

        Searches through the synonyms map to find if any resume skill
        is a synonym of the missing skill.

        Args:
            missing_skill: The skill that's missing from the resume
            resume_skills: List of skills from the resume
            synonyms_map: Dictionary of skill synonyms

        Returns:
            List of suggestion dicts with skill and confidence

        Example:
            >>> suggester = SkillSuggester()
            >>> synonyms = {"SQL": ["SQL", "PostgreSQL", "MySQL"]}
            >>> suggester.find_synonym_suggestions(
            ...     "SQL", ["PostgreSQL", "MongoDB"], synonyms
            ... )
            [{"skill": "PostgreSQL", "confidence": 0.85, "reason": "synonym"}]
        """
        suggestions = []
        normalized_missing = self.normalize_skill_name(missing_skill)

        # Build set of all variants for the missing skill
        all_variants = {normalized_missing}

        for canonical_name, synonym_list in synonyms_map.items():
            normalized_canonical = self.normalize_skill_name(canonical_name)
            if normalized_canonical == normalized_missing:
                all_variants.update([self.normalize_skill_name(s) for s in synonym_list])
            else:
                for synonym in synonym_list:
                    if self.normalize_skill_name(synonym) == normalized_missing:
                        all_variants.add(normalized_canonical)
                        all_variants.update([self.normalize_skill_name(s) for s in synonym_list])
                        break

        # Find matching resume skills
        for resume_skill in resume_skills:
            normalized_resume = self.normalize_skill_name(resume_skill)
            if normalized_resume in all_variants and normalized_resume != normalized_missing:
                suggestions.append({
                    "skill": resume_skill,
                    "confidence": 0.85,
                    "reason": "synonym"
                })

        return suggestions

    def find_category_suggestions(
        self,
        missing_skill: str,
        resume_skills: List[str],
        synonyms_map: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Find category-based suggestions for a missing skill.

        If the missing skill is in a category (e.g., "databases"), suggest
        other skills from that category present in the resume.

        Args:
            missing_skill: The skill that's missing from the resume
            resume_skills: List of skills from the resume
            synonyms_map: Dictionary of skill synonyms

        Returns:
            List of suggestion dicts with skill and confidence

        Example:
            >>> suggester = SkillSuggester()
            >>> suggestions = suggester.find_category_suggestions(
            ...     "PostgreSQL", ["MongoDB", "Redis"], {}
            ... )
            # Might return MongoDB and Redis as database alternatives
        """
        suggestions = []
        normalized_missing = self.normalize_skill_name(missing_skill)

        # Find which category the missing skill belongs to
        missing_category = None
        for category, skills in self._taxonomy_map.items():
            for canonical_name, synonym_list in skills.items():
                all_variants = [self.normalize_skill_name(s) for s in synonym_list]
                if normalized_missing in all_variants:
                    missing_category = category
                    break
            if missing_category:
                break

        if not missing_category:
            return suggestions

        # Get all skills from the same category in resume
        category_skills = self._category_map.get(missing_category, [])
        normalized_category = [self.normalize_skill_name(s) for s in category_skills]

        for resume_skill in resume_skills:
            normalized_resume = self.normalize_skill_name(resume_skill)
            if normalized_resume in normalized_category and normalized_resume != normalized_missing:
                suggestions.append({
                    "skill": resume_skill,
                    "confidence": 0.70,
                    "reason": f"same_category ({missing_category})"
                })

        return suggestions

    def find_related_suggestions(
        self,
        missing_skill: str,
        resume_skills: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Find related skill suggestions for a missing skill.

        Uses predefined mappings of related skills to suggest alternatives
        that are commonly used together.

        Args:
            missing_skill: The skill that's missing from the resume
            resume_skills: List of skills from the resume

        Returns:
            List of suggestion dicts with skill and confidence

        Example:
            >>> suggester = SkillSuggester()
            >>> suggestions = suggester.find_related_suggestions(
            ...     "Node.js", ["Express", "MongoDB"]
            ... )
            [{"skill": "Express", "confidence": 0.65, "reason": "related"}]
        """
        suggestions = []
        normalized_missing = self.normalize_skill_name(missing_skill)

        # Check if missing skill has related skills defined
        for skill_key, related_skills in RELATED_SKILLS.items():
            if self.normalize_skill_name(skill_key) == normalized_missing:
                # Find which related skills are in resume
                for related_skill in related_skills:
                    for resume_skill in resume_skills:
                        if self.normalize_skill_name(resume_skill) == self.normalize_skill_name(related_skill):
                            suggestions.append({
                                "skill": resume_skill,
                                "confidence": 0.65,
                                "reason": "related"
                            })
                break

        return suggestions

    def find_fuzzy_suggestions(
        self,
        missing_skill: str,
        resume_skills: List[str],
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Find fuzzy match suggestions for a missing skill.

        Uses string similarity to find skills that are similar in name,
        useful for detecting variations and typos.

        Args:
            missing_skill: The skill that's missing from the resume
            resume_skills: List of skills from the resume
            threshold: Minimum similarity score (0.0-1.0) to consider a suggestion

        Returns:
            List of suggestion dicts with skill and confidence

        Example:
            >>> suggester = SkillSuggester()
            >>> suggestions = suggester.find_fuzzy_suggestions(
            ...     "React.js", ["ReactJS", "React JS"]
            ... )
        """
        suggestions = []

        for resume_skill in resume_skills:
            similarity = self.calculate_fuzzy_similarity(resume_skill, missing_skill)

            if similarity >= threshold:
                suggestions.append({
                    "skill": resume_skill,
                    "confidence": round(similarity * 0.9, 2),  # Scale down slightly
                    "reason": "fuzzy_match"
                })

        # Sort by confidence (highest first)
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)

        return suggestions

    def suggest_alternatives(
        self,
        missing_skill: str,
        resume_skills: List[str],
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggest alternative skills from the resume for a missing required skill.

        Combines multiple suggestion strategies:
        1. Synonym-based suggestions (highest confidence: 0.85)
        2. Category-based suggestions (medium-high confidence: 0.70)
        3. Related skill suggestions (medium confidence: 0.65)
        4. Fuzzy match suggestions (variable confidence: 0.60-0.90)

        Args:
            missing_skill: The required skill that's missing from the resume
            resume_skills: List of skills extracted from the resume
            max_suggestions: Maximum number of suggestions to return (default: 5)

        Returns:
            List of suggestion dicts, each containing:
            - skill (str): The suggested skill name
            - confidence (float): Confidence score (0.0-1.0)
            - reason (str): Why this skill was suggested

        Example:
            >>> suggester = SkillSuggester()
            >>> suggestions = suggester.suggest_alternatives(
            ...     missing_skill="SQL",
            ...     resume_skills=["PostgreSQL", "MongoDB", "Python"]
            ... )
            >>> len(suggestions)
            2
            >>> suggestions[0]['skill']
            "PostgreSQL"
            >>> suggestions[0]['confidence']
            0.85
        """
        if not missing_skill or not resume_skills:
            return []

        # Load synonyms if not already loaded
        synonyms_map = self.load_synonyms()

        all_suggestions = []

        # Strategy 1: Synonym-based suggestions
        synonym_suggestions = self.find_synonym_suggestions(
            missing_skill, resume_skills, synonyms_map
        )
        all_suggestions.extend(synonym_suggestions)

        # Strategy 2: Category-based suggestions
        category_suggestions = self.find_category_suggestions(
            missing_skill, resume_skills, synonyms_map
        )
        all_suggestions.extend(category_suggestions)

        # Strategy 3: Related skill suggestions
        related_suggestions = self.find_related_suggestions(
            missing_skill, resume_skills
        )
        all_suggestions.extend(related_suggestions)

        # Strategy 4: Fuzzy match suggestions
        fuzzy_suggestions = self.find_fuzzy_suggestions(
            missing_skill, resume_skills
        )
        all_suggestions.extend(fuzzy_suggestions)

        # Remove duplicates (keep highest confidence version)
        unique_suggestions: Dict[str, Dict[str, Any]] = {}
        for suggestion in all_suggestions:
            skill_key = self.normalize_skill_name(suggestion["skill"])
            if skill_key not in unique_suggestions:
                unique_suggestions[skill_key] = suggestion
            else:
                # Keep the one with higher confidence
                if suggestion["confidence"] > unique_suggestions[skill_key]["confidence"]:
                    unique_suggestions[skill_key] = suggestion

        # Convert back to list and sort by confidence
        final_suggestions = list(unique_suggestions.values())
        final_suggestions.sort(key=lambda x: x["confidence"], reverse=True)

        # Return top N suggestions
        return final_suggestions[:max_suggestions]

    def suggest_for_multiple(
        self,
        missing_skills: List[str],
        resume_skills: List[str],
        max_suggestions_per_skill: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Suggest alternatives for multiple missing skills.

        Args:
            missing_skills: List of required skills that are missing
            resume_skills: List of skills extracted from the resume
            max_suggestions_per_skill: Max suggestions per missing skill

        Returns:
            Dictionary mapping each missing skill to its list of suggestions

        Example:
            >>> suggester = SkillSuggester()
            >>> results = suggester.suggest_for_multiple(
            ...     ["SQL", "React"],
            ...     ["PostgreSQL", "Angular", "Vue"]
            ... )
            >>> results["SQL"][0]["skill"]
            "PostgreSQL"
        """
        results = {}

        for missing_skill in missing_skills:
            results[missing_skill] = self.suggest_alternatives(
                missing_skill,
                resume_skills,
                max_suggestions=max_suggestions_per_skill
            )

        return results
