"""
Tag suggestion service for candidate tagging based on resume content analysis.

This module provides intelligent tag suggestion capabilities that help identify
relevant candidate tags from resume text using keyword extraction and fuzzy matching:
- Keyword-based suggestions (extracted keywords matched to organization tags)
- Fuzzy matching suggestions (similar tag names for variations)
- Multi-word phrase matching (e.g., "Machine Learning" matched to "ML Engineer")
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class TagSuggester:
    """
    Tag suggestion service for suggesting relevant candidate tags based on resume content.

    This service analyzes resume text to extract relevant keywords and matches them
    against organization-specific tags, providing intelligent suggestions with
    confidence scores.

    The suggestion process uses multiple strategies:
    1. Direct keyword matching (highest confidence)
    2. Fuzzy string matching for variations (medium confidence)
    3. Multi-word phrase matching (variable confidence)

    Example:
        >>> suggester = TagSuggester()
        >>> organization_tags = [
        ...     {"id": "1", "tag_name": "Senior Developer", "is_active": True},
        ...     {"id": "2", "tag_name": "Remote", "is_active": True},
        ... ]
        >>> suggestions = suggester.suggest_tags(
        ...     resume_text="Experienced senior software developer with 5 years...",
        ...     organization_tags=organization_tags,
        ...     limit=5
        ... )
        >>> print(suggestions[0]['tag_name'])
        "Senior Developer"
        >>> print(suggestions[0]['score'])
        0.85
    """

    def __init__(self, min_score: float = 0.3, fuzzy_threshold: float = 0.6):
        """
        Initialize the tag suggester.

        Args:
            min_score: Minimum keyword extraction score (0.0-1.0) to consider keywords
            fuzzy_threshold: Minimum fuzzy match similarity (0.0-1.0) for suggestions
        """
        self.min_score = min_score
        self.fuzzy_threshold = fuzzy_threshold

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text for consistent comparison.

        Removes extra whitespace, converts to lowercase, and handles
        common variations in capitalization and spacing.

        Args:
            text: The text to normalize

        Returns:
            Normalized text

        Example:
            >>> TagSuggester.normalize_text("  Senior Java Developer  ")
            "senior java developer"
        """
        # Remove extra whitespace and convert to lowercase
        normalized = " ".join(text.strip().lower().split())
        return normalized

    def calculate_fuzzy_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate fuzzy similarity between two text strings.

        Uses SequenceMatcher to determine how similar two strings are,
        useful for detecting variations and typos.

        Args:
            text1: First text string
            text2: Second text string

        Returns:
            Similarity score between 0.0 and 1.0

        Example:
            >>> suggester = TagSuggester()
            >>> suggester.calculate_fuzzy_similarity("Senior Dev", "Senior Developer")
            0.78
        """
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)

        return SequenceMatcher(None, norm1, norm2).ratio()

    def extract_keywords_from_resume(
        self,
        resume_text: str,
        top_n: int = 30,
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Extract relevant keywords from resume text.

        Uses the keyword_extractor module to identify important terms
        and phrases from the resume content.

        Args:
            resume_text: Full resume text to analyze
            top_n: Maximum number of keywords to extract
            language: Document language ('english' or 'russian')

        Returns:
            Dictionary containing:
                - keywords: List of extracted keywords
                - keywords_with_scores: List of (keyword, score) tuples
                - count: Number of keywords extracted
                - error: Error message if extraction failed

        Example:
            >>> suggester = TagSuggester()
            >>> result = suggester.extract_keywords_from_resume(
            ...     "Python developer with Django experience...",
            ...     top_n=10
            ... )
            >>> result["keywords"]
            ['Python', 'Django', 'developer']
        """
        try:
            # Import here to avoid issues if keybert is not installed
            from analyzers.keyword_extractor import extract_keywords

            logger.info(
                f"Extracting keywords from resume (length={len(resume_text)}, top_n={top_n})"
            )

            result = extract_keywords(
                resume_text,
                keyphrase_ngram_range=(1, 3),  # Include multi-word phrases
                stop_words=language,
                top_n=top_n,
                min_score=self.min_score,
                use_mmr=True,
                diversity=0.5,
            )

            if result.get("error"):
                logger.warning(f"Keyword extraction returned error: {result['error']}")
            else:
                logger.info(f"Extracted {result.get('count', 0)} keywords from resume")

            return result

        except ImportError as e:
            logger.error(f"Failed to import keyword_extractor: {e}")
            return {
                "keywords": None,
                "keywords_with_scores": None,
                "count": 0,
                "error": f"Import error: {str(e)}",
            }
        except Exception as e:
            logger.error(f"Failed to extract keywords: {e}", exc_info=True)
            return {
                "keywords": None,
                "keywords_with_scores": None,
                "count": 0,
                "error": f"Extraction failed: {str(e)}",
            }

    def find_direct_matches(
        self,
        keywords: List[str],
        keywords_with_scores: List[Tuple[str, float]],
        organization_tags: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find direct keyword matches in organization tags.

        Searches for tags that exactly or closely match extracted keywords.

        Args:
            keywords: List of extracted keywords
            keywords_with_scores: List of (keyword, score) tuples
            organization_tags: List of organization tag dictionaries

        Returns:
            List of suggestion dicts with tag details and confidence scores

        Example:
            >>> suggester = TagSuggester()
            >>> keywords = ["python", "django", "postgresql"]
            >>> tags = [{"tag_name": "Python Expert", "is_active": True}]
            >>> suggester.find_direct_matches(keywords, [], tags)
            [{'tag_name': 'Python Expert', 'score': 0.85, 'reason': 'direct_match'}]
        """
        suggestions = []

        # Create a lookup for keyword scores
        keyword_scores = {kw.lower(): score for kw, score in keywords_with_scores}

        for tag in organization_tags:
            if not tag.get("is_active", True):
                continue

            tag_name = tag.get("tag_name", "")
            if not tag_name:
                continue

            normalized_tag = self.normalize_text(tag_name)

            # Check for direct matches
            for keyword in keywords:
                normalized_keyword = self.normalize_text(keyword)

                # Exact match
                if normalized_keyword == normalized_tag:
                    # Get the keyword score, or use a default high score
                    base_score = keyword_scores.get(normalized_keyword, 0.7)
                    suggestions.append({
                        **tag,
                        "score": round(min(base_score * 1.1, 1.0), 2),  # Boost for exact match
                        "reason": "direct_match",
                    })
                    break

                # Check if keyword is contained in tag name or vice versa
                if normalized_keyword in normalized_tag or normalized_tag in normalized_keyword:
                    base_score = keyword_scores.get(normalized_keyword, 0.5)
                    suggestions.append({
                        **tag,
                        "score": round(min(base_score * 0.9, 1.0), 2),
                        "reason": "partial_match",
                    })
                    break

        return suggestions

    def find_fuzzy_matches(
        self,
        keywords: List[str],
        keywords_with_scores: List[Tuple[str, float]],
        organization_tags: List[Dict[str, Any]],
        existing_tag_ids: set
    ) -> List[Dict[str, Any]]:
        """
        Find fuzzy matches between keywords and organization tags.

        Uses string similarity to find tags that are similar in name to
        extracted keywords, useful for detecting variations and abbreviations.

        Args:
            keywords: List of extracted keywords
            keywords_with_scores: List of (keyword, score) tuples
            organization_tags: List of organization tag dictionaries
            existing_tag_ids: Set of tag IDs already matched to avoid duplicates

        Returns:
            List of suggestion dicts with tag details and confidence scores

        Example:
            >>> suggester = TagSuggester()
            >>> keywords = ["ml engineer"]
            >>> tags = [{"id": "1", "tag_name": "Machine Learning Engineer", "is_active": True}]
            >>> suggester.find_fuzzy_matches(keywords, [], tags, set())
            [{'tag_name': 'Machine Learning Engineer', 'score': 0.72, 'reason': 'fuzzy_match'}]
        """
        suggestions = []

        # Create a lookup for keyword scores
        keyword_scores = {kw.lower(): score for kw, score in keywords_with_scores}

        for tag in organization_tags:
            if not tag.get("is_active", True):
                continue

            tag_id = tag.get("id")
            if tag_id in existing_tag_ids:
                continue

            tag_name = tag.get("tag_name", "")
            if not tag_name:
                continue

            for keyword in keywords:
                similarity = self.calculate_fuzzy_similarity(keyword, tag_name)

                if similarity >= self.fuzzy_threshold:
                    base_score = keyword_scores.get(keyword.lower(), 0.5)
                    suggestions.append({
                        **tag,
                        "score": round(similarity * base_score, 2),
                        "reason": "fuzzy_match",
                    })
                    existing_tag_ids.add(tag_id)
                    break

        # Sort by score (highest first)
        suggestions.sort(key=lambda x: x["score"], reverse=True)

        return suggestions

    def suggest_tags(
        self,
        resume_text: str,
        organization_tags: List[Dict[str, Any]],
        limit: int = 10,
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Suggest relevant candidate tags based on resume content.

        Analyzes resume text to extract keywords and matches them against
        organization-specific tags using direct and fuzzy matching strategies.

        Args:
            resume_text: Full resume text to analyze
            organization_tags: List of organization tag dictionaries with keys:
                - id: Tag identifier
                - tag_name: Tag name
                - is_active: Whether tag is active (default: True)
            limit: Maximum number of suggestions to return
            language: Document language ('english' or 'russian')

        Returns:
            Dictionary containing:
                - suggestions: List of tag suggestions with scores
                - total_count: Number of suggestions returned
                - keywords_extracted: List of keywords extracted from resume
                - error: Error message if analysis failed

        Example:
            >>> suggester = TagSuggester()
            >>> tags = [
            ...     {"id": "1", "tag_name": "Senior Developer", "is_active": True},
            ...     {"id": "2", "tag_name": "Remote", "is_active": True},
            ... ]
            >>> result = suggester.suggest_tags(
            ...     "Senior Python developer seeking remote position...",
            ...     organization_tags=tags,
            ...     limit=5
            ... )
            >>> len(result["suggestions"])
            2
            >>> result["suggestions"][0]["tag_name"]
            "Senior Developer"
        """
        if not resume_text or not organization_tags:
            return {
                "suggestions": [],
                "total_count": 0,
                "keywords_extracted": [],
                "error": None,
            }

        try:
            # Extract keywords from resume
            extraction_result = self.extract_keywords_from_resume(
                resume_text,
                top_n=30,
                language=language
            )

            if extraction_result.get("error"):
                return {
                    "suggestions": [],
                    "total_count": 0,
                    "keywords_extracted": [],
                    "error": extraction_result["error"],
                }

            keywords = extraction_result.get("keywords") or []
            keywords_with_scores = extraction_result.get("keywords_with_scores") or []

            if not keywords:
                return {
                    "suggestions": [],
                    "total_count": 0,
                    "keywords_extracted": [],
                    "error": None,
                }

            logger.info(f"Extracted {len(keywords)} keywords for tag matching")

            all_suggestions = []

            # Strategy 1: Direct matches (higher confidence)
            direct_matches = self.find_direct_matches(
                keywords,
                keywords_with_scores,
                organization_tags
            )
            all_suggestions.extend(direct_matches)

            # Track matched tag IDs to avoid duplicates
            matched_tag_ids = {s.get("id") for s in direct_matches if s.get("id")}

            # Strategy 2: Fuzzy matches (for variations)
            fuzzy_matches = self.find_fuzzy_matches(
                keywords,
                keywords_with_scores,
                organization_tags,
                matched_tag_ids
            )
            all_suggestions.extend(fuzzy_matches)

            # Remove duplicates (keep highest score version)
            unique_suggestions: Dict[str, Dict[str, Any]] = {}
            for suggestion in all_suggestions:
                tag_id = suggestion.get("id")
                if tag_id:
                    if tag_id not in unique_suggestions:
                        unique_suggestions[tag_id] = suggestion
                    else:
                        # Keep the one with higher score
                        if suggestion["score"] > unique_suggestions[tag_id]["score"]:
                            unique_suggestions[tag_id] = suggestion

            # Convert back to list and sort by score
            final_suggestions = list(unique_suggestions.values())
            final_suggestions.sort(key=lambda x: x["score"], reverse=True)

            # Apply limit
            final_suggestions = final_suggestions[:limit]

            logger.info(f"Generated {len(final_suggestions)} tag suggestions")

            return {
                "suggestions": final_suggestions,
                "total_count": len(final_suggestions),
                "keywords_extracted": keywords[:10],  # Return top 10 keywords for reference
                "error": None,
            }

        except Exception as e:
            logger.error(f"Failed to generate tag suggestions: {e}", exc_info=True)
            return {
                "suggestions": [],
                "total_count": 0,
                "keywords_extracted": [],
                "error": f"Suggestion failed: {str(e)}",
            }

    def suggest_tags_for_multiple_resumes(
        self,
        resume_texts: List[str],
        organization_tags: List[Dict[str, Any]],
        limit_per_resume: int = 5,
        language: str = "english"
    ) -> List[Dict[str, Any]]:
        """
        Suggest tags for multiple resumes in batch.

        Args:
            resume_texts: List of resume texts to analyze
            organization_tags: List of organization tag dictionaries
            limit_per_resume: Maximum suggestions per resume
            language: Document language

        Returns:
            List of suggestion dictionaries, one per resume

        Example:
            >>> suggester = TagSuggester()
            >>> resumes = ["Resume 1 text...", "Resume 2 text..."]
            >>> tags = [{"id": "1", "tag_name": "Developer", "is_active": True}]
            >>> results = suggester.suggest_tags_for_multiple_resumes(resumes, tags)
            >>> len(results)
            2
        """
        results = []

        for i, resume_text in enumerate(resume_texts):
            result = self.suggest_tags(
                resume_text,
                organization_tags,
                limit=limit_per_resume,
                language=language
            )
            results.append({
                "resume_index": i,
                **result,
            })

        return results
