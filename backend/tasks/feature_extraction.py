"""
Feature Extraction Pipeline for Training Data Preparation

This module provides comprehensive feature extraction for ML model training.
The pipeline transforms raw feedback and match data into feature vectors
suitable for model training, including:
- Skill-based features (similarity, match type, confidence)
- Context features (vacancy requirements, resume attributes)
- Temporal features (feedback recency, time-based patterns)
- Interaction features (skill-vacancy compatibility)
- Aggregated features (historical performance metrics)
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

import numpy as np
from numpy import typing as npt

from analyzers.enhanced_matcher import EnhancedSkillMatcher
from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)


# Feature name constants for consistency
FEATURE_SKILL_SIMILARITY = "skill_similarity"
FEATURE_SKILL_CONFIDENCE = "skill_confidence"
FEATURE_MATCH_PERCENTAGE = "match_percentage"
FEATURE_OVERALL_SCORE = "overall_score"
FEATURE_KEYWORD_SCORE = "keyword_score"
FEATURE_TFIDF_SCORE = "tfidf_score"
FEATURE_VECTOR_SCORE = "vector_score"
FEATURE_SKILL_COUNT_MATCHED = "skill_count_matched"
FEATURE_SKILL_COUNT_MISSING = "skill_count_missing"
FEATURE_SKILL_MATCH_RATIO = "skill_match_ratio"
FEATURE_EXPERIENCE_VERIFIED = "experience_verified"
FEATURE_FEEDBACK_RECENCY_DAYS = "feedback_recency_days"
FEATURE_FEEDBACK_CORRECTNESS = "feedback_correctness"
FEATURE_VACANCY_SKILL_COUNT = "vacancy_skill_count"
FEATURE_RESUME_SKILL_COUNT = "resume_skill_count"
FEATURE_SKILL_OVERLAP_RATIO = "skill_overlap_ratio"
FEATURE_ORGANIZATION_ID = "organization_id"
FEATURE_RECRUITER_ID = "recruiter_id"


class FeatureExtractor:
    """
    Feature extraction pipeline for training data preparation.

    This class transforms raw feedback and match data into feature vectors
    suitable for machine learning model training. It supports multiple
    feature types including skill-based, context-based, temporal, and
    interaction features.

    Attributes:
        matcher: Enhanced skill matcher for computing skill similarity
        feature_names: List of feature names used in extraction

    Example:
        >>> extractor = FeatureExtractor()
        >>> feedback_data = {
        ...     "skill": "python",
        ...     "was_correct": True,
        ...     "confidence_score": 0.9
        ... }
        >>> match_data = {"overall_score": 0.85}
        >>> features = extractor.extract_training_features(feedback_data, match_data)
        >>> print(features["skill_similarity"])
        1.0
    """

    # Default feature set for training
    DEFAULT_FEATURES = [
        FEATURE_SKILL_SIMILARITY,
        FEATURE_SKILL_CONFIDENCE,
        FEATURE_MATCH_PERCENTAGE,
        FEATURE_OVERALL_SCORE,
        FEATURE_KEYWORD_SCORE,
        FEATURE_TFIDF_SCORE,
        FEATURE_VECTOR_SCORE,
        FEATURE_SKILL_COUNT_MATCHED,
        FEATURE_SKILL_COUNT_MISSING,
        FEATURE_SKILL_MATCH_RATIO,
        FEATURE_EXPERIENCE_VERIFIED,
        FEATURE_FEEDBACK_RECENCY_DAYS,
        FEATURE_FEEDBACK_CORRECTNESS,
        FEATURE_VACANCY_SKILL_COUNT,
        FEATURE_RESUME_SKILL_COUNT,
        FEATURE_SKILL_OVERLAP_RATIO,
    ]

    def __init__(self, feature_names: Optional[List[str]] = None):
        """
        Initialize the feature extractor.

        Args:
            feature_names: Optional list of feature names to extract.
                          Defaults to DEFAULT_FEATURES.
        """
        self.feature_names = feature_names or self.DEFAULT_FEATURES
        self.matcher = EnhancedSkillMatcher()
        self._skill_synonyms_cache: Optional[Dict[str, List[str]]] = None

    def _load_skill_synonyms(self) -> Dict[str, List[str]]:
        """
        Load skill synonyms for similarity computation.

        Returns:
            Dictionary mapping skill names to their synonyms.
        """
        if self._skill_synonyms_cache is None:
            self._skill_synonyms_cache = self.matcher.load_synonyms()
        return self._skill_synonyms_cache

    def extract_skill_similarity(
        self,
        resume_skill: str,
        vacancy_skill: str,
        context: Optional[str] = None
    ) -> float:
        """
        Extract skill similarity feature.

        Computes the similarity between a resume skill and a vacancy skill
        using the enhanced matcher.

        Args:
            resume_skill: Skill from the resume
            vacancy_skill: Required skill from the vacancy
            context: Optional context hint for matching

        Returns:
            Similarity score between 0.0 and 1.0

        Example:
            >>> extractor = FeatureExtractor()
            >>> extractor.extract_skill_similarity("ReactJS", "React", "web_framework")
            0.95
        """
        try:
            result = self.matcher.match_with_context(
                [resume_skill], vacancy_skill, context=context
            )
            return result.get("confidence", 0.0)
        except Exception as e:
            logger.error(f"Error computing skill similarity: {e}", exc_info=True)
            return 0.0

    def extract_skill_confidence(
        self, confidence_score: Optional[float]
    ) -> float:
        """
        Extract skill confidence feature.

        Normalizes the confidence score for feature extraction.

        Args:
            confidence_score: Raw confidence score (may be None)

        Returns:
            Normalized confidence score between 0.0 and 1.0

        Example:
            >>> extractor = FeatureExtractor()
            >>> extractor.extract_skill_confidence(0.85)
            0.85
        """
        if confidence_score is None:
            return 0.0
        return max(0.0, min(1.0, float(confidence_score)))

    def extract_match_features(
        self, match_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Extract match-related features from match result data.

        Args:
            match_data: Dictionary containing match result information

        Returns:
            Dictionary of match-related features

        Example:
            >>> extractor = FeatureExtractor()
            >>> match = {"overall_score": 0.85, "keyword_score": 0.9}
            >>> features = extractor.extract_match_features(match)
            >>> print(features["overall_score"])
            0.85
        """
        features = {}

        # Extract various score features
        for score_key in [
            FEATURE_OVERALL_SCORE,
            FEATURE_KEYWORD_SCORE,
            FEATURE_TFIDF_SCORE,
            FEATURE_VECTOR_SCORE,
            FEATURE_MATCH_PERCENTAGE,
        ]:
            value = match_data.get(score_key)
            if value is not None:
                # Normalize percentage to 0-1 range if needed
                if score_key == FEATURE_MATCH_PERCENTAGE:
                    features[score_key] = float(value) / 100.0
                else:
                    features[score_key] = float(value)
            else:
                features[score_key] = 0.0

        # Extract skill count features
        matched_skills = match_data.get("matched_skills") or []
        missing_skills = match_data.get("missing_skills") or []
        additional_skills = match_data.get("additional_skills_matched") or []

        features[FEATURE_SKILL_COUNT_MATCHED] = float(len(matched_skills))
        features[FEATURE_SKILL_COUNT_MISSING] = float(len(missing_skills))

        # Compute skill match ratio
        total_matched = len(matched_skills) + len(additional_skills)
        total_skills = total_matched + len(missing_skills)
        if total_skills > 0:
            features[FEATURE_SKILL_MATCH_RATIO] = total_matched / total_skills
        else:
            features[FEATURE_SKILL_MATCH_RATIO] = 0.0

        # Extract experience verification
        features[FEATURE_EXPERIENCE_VERIFIED] = float(
            match_data.get("experience_verified", False)
        )

        return features

    def extract_temporal_features(
        self,
        created_at: Optional[Union[datetime, str]],
        reference_time: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Extract temporal features from timestamps.

        Args:
            created_at: Timestamp of the feedback/match creation
            reference_time: Reference time for recency calculation
                           (defaults to current time)

        Returns:
            Dictionary of temporal features

        Example:
            >>> extractor = FeatureExtractor()
            >>> features = extractor.extract_temporal_features("2024-01-01T00:00:00Z")
            >>> print(features["feedback_recency_days"])
            30.0  # Approximate days since creation
        """
        features = {}

        if created_at is None:
            features[FEATURE_FEEDBACK_RECENCY_DAYS] = 0.0
            return features

        try:
            # Parse datetime if string
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

            # Use current time as reference if not provided
            if reference_time is None:
                reference_time = datetime.now(created_at.tzinfo)

            # Calculate recency in days
            time_delta = reference_time - created_at
            recency_days = time_delta.total_seconds() / 86400.0  # Convert to days

            features[FEATURE_FEEDBACK_RECENCY_DAYS] = float(recency_days)

        except (ValueError, TypeError) as e:
            logger.debug(f"Error parsing timestamp for temporal features: {e}")
            features[FEATURE_FEEDBACK_RECENCY_DAYS] = 0.0

        return features

    def extract_feedback_features(
        self, feedback_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Extract feedback-specific features.

        Args:
            feedback_data: Dictionary containing feedback information

        Returns:
            Dictionary of feedback-related features

        Example:
            >>> extractor = FeatureExtractor()
            >>> feedback = {"was_correct": True, "confidence_score": 0.9}
            >>> features = extractor.extract_feedback_features(feedback)
            >>> print(features["feedback_correctness"])
            1.0
        """
        features = {}

        # Extract feedback correctness (label)
        was_correct = feedback_data.get("was_correct")
        if was_correct is not None:
            features[FEATURE_FEEDBACK_CORRECTNESS] = float(int(was_correct))
        else:
            features[FEATURE_FEEDBACK_CORRECTNESS] = 0.0

        # Extract confidence score
        confidence = feedback_data.get("confidence_score")
        features[FEATURE_SKILL_CONFIDENCE] = self.extract_skill_confidence(confidence)

        return features

    def extract_vacancy_features(
        self,
        vacancy_skills: Optional[List[str]] = None,
        required_skills: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Extract vacancy-related features.

        Args:
            vacancy_skills: List of all skills mentioned in vacancy
            required_skills: List of required skills

        Returns:
            Dictionary of vacancy-related features

        Example:
            >>> extractor = FeatureExtractor()
            >>> features = extractor.extract_vacancy_features(
            ...     vacancy_skills=["Python", "Java", "SQL"]
            ... )
            >>> print(features["vacancy_skill_count"])
            3.0
        """
        features = {}

        # Use required_skills if provided, otherwise vacancy_skills
        skills = required_skills or vacancy_skills or []

        features[FEATURE_VACANCY_SKILL_COUNT] = float(len(skills))

        return features

    def extract_resume_features(
        self,
        resume_skills: Optional[List[str]] = None,
        parsed_skills: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Extract resume-related features.

        Args:
            resume_skills: List of skills from resume
            parsed_skills: List of parsed skills (alternative to resume_skills)

        Returns:
            Dictionary of resume-related features

        Example:
            >>> extractor = FeatureExtractor()
            >>> features = extractor.extract_resume_features(
            ...     resume_skills=["Python", "Django", "PostgreSQL"]
            ... )
            >>> print(features["resume_skill_count"])
            3.0
        """
        features = {}

        # Use parsed_skills if resume_skills not provided
        skills = resume_skills or parsed_skills or []

        features[FEATURE_RESUME_SKILL_COUNT] = float(len(skills))

        return features

    def extract_interaction_features(
        self,
        resume_skills: Optional[List[str]] = None,
        vacancy_skills: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Extract interaction features between resume and vacancy.

        Args:
            resume_skills: List of skills from resume
            vacancy_skills: List of required skills from vacancy

        Returns:
            Dictionary of interaction features

        Example:
            >>> extractor = FeatureExtractor()
            >>> features = extractor.extract_interaction_features(
            ...     resume_skills=["Python", "Django"],
            ...     vacancy_skills=["Python", "Java", "SQL"]
            ... )
            >>> print(features["skill_overlap_ratio"])
            0.33
        """
        features = {}

        if not resume_skills or not vacancy_skills:
            features[FEATURE_SKILL_OVERLAP_RATIO] = 0.0
            return features

        # Normalize skill names for comparison
        normalized_resume = [
            self.matcher.normalize_skill_name(s) for s in resume_skills
        ]
        normalized_vacancy = [
            self.matcher.normalize_skill_name(s) for s in vacancy_skills
        ]

        # Calculate overlap
        overlap = set(normalized_resume) & set(normalized_vacancy)
        total_vacancy = len(set(normalized_vacancy))

        if total_vacancy > 0:
            features[FEATURE_SKILL_OVERLAP_RATIO] = len(overlap) / total_vacancy
        else:
            features[FEATURE_SKILL_OVERLAP_RATIO] = 0.0

        return features

    def extract_training_features(
        self,
        feedback_data: Dict[str, Any],
        match_data: Optional[Dict[str, Any]] = None,
        resume_data: Optional[Dict[str, Any]] = None,
        vacancy_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """
        Extract complete feature set for training data preparation.

        This is the main feature extraction method that combines all
        feature types into a single feature vector.

        Args:
            feedback_data: Dictionary containing feedback information.
                          Must include at least "skill" key.
            match_data: Optional dictionary containing match result information
            resume_data: Optional dictionary containing resume information
            vacancy_data: Optional dictionary containing vacancy information

        Returns:
            Dictionary mapping feature names to feature values

        Example:
            >>> extractor = FeatureExtractor()
            >>> feedback = {"skill": "python", "was_correct": True}
            >>> match = {"overall_score": 0.85}
            >>> features = extractor.extract_training_features(feedback, match)
            >>> len(features) > 0
            True
        """
        start_time = time.time()

        try:
            features = {}

            # Extract feedback features (always present)
            feedback_features = self.extract_feedback_features(feedback_data)
            features.update(feedback_features)

            # Extract skill similarity
            resume_skill = feedback_data.get("actual_skill") or feedback_data.get("skill", "")
            vacancy_skill = feedback_data.get("skill", "")

            if resume_skill and vacancy_skill:
                context = vacancy_data.get("skill_context") if vacancy_data else None
                similarity = self.extract_skill_similarity(
                    resume_skill, vacancy_skill, context
                )
                features[FEATURE_SKILL_SIMILARITY] = similarity
            else:
                features[FEATURE_SKILL_SIMILARITY] = 0.0

            # Extract match features if available
            if match_data:
                match_features = self.extract_match_features(match_data)
                features.update(match_features)
            else:
                # Fill match features with zeros
                for feature in [
                    FEATURE_OVERALL_SCORE,
                    FEATURE_KEYWORD_SCORE,
                    FEATURE_TFIDF_SCORE,
                    FEATURE_VECTOR_SCORE,
                    FEATURE_MATCH_PERCENTAGE,
                    FEATURE_SKILL_COUNT_MATCHED,
                    FEATURE_SKILL_COUNT_MISSING,
                    FEATURE_SKILL_MATCH_RATIO,
                    FEATURE_EXPERIENCE_VERIFIED,
                ]:
                    if feature not in features:
                        features[feature] = 0.0

            # Extract temporal features
            created_at = feedback_data.get("created_at")
            temporal_features = self.extract_temporal_features(created_at)
            features.update(temporal_features)

            # Extract resume features if available
            resume_skills = None
            if resume_data:
                resume_features = self.extract_resume_features(
                    resume_data.get("skills"),
                    resume_data.get("parsed_skills")
                )
                features.update(resume_features)
                resume_skills = resume_data.get("skills") or resume_data.get("parsed_skills")
            else:
                features[FEATURE_RESUME_SKILL_COUNT] = 0.0
                resume_skills = None

            # Extract vacancy features if available
            vacancy_skills = None
            if vacancy_data:
                vacancy_features = self.extract_vacancy_features(
                    vacancy_data.get("skills"),
                    vacancy_data.get("required_skills")
                )
                features.update(vacancy_features)
                vacancy_skills = (
                    vacancy_data.get("required_skills") or vacancy_data.get("skills")
                )
            else:
                features[FEATURE_VACANCY_SKILL_COUNT] = 0.0
                vacancy_skills = None

            # Extract interaction features
            if resume_skills or vacancy_skills:
                interaction_features = self.extract_interaction_features(
                    resume_skills, vacancy_skills
                )
                features.update(interaction_features)
            else:
                features[FEATURE_SKILL_OVERLAP_RATIO] = 0.0

            # Ensure all requested features are present
            for feature_name in self.feature_names:
                if feature_name not in features:
                    features[feature_name] = 0.0

            # Record feature extraction timing
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name="feature_extractor",
                    operation="extract_training_features",
                    duration=duration,
                    prediction_type="feature_extraction",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            logger.debug(
                f"Extracted {len(features)} features for skill="
                f"{feedback_data.get('skill', 'unknown')}"
            )

            return features

        except Exception as e:
            logger.error(f"Error extracting training features: {e}", exc_info=True)
            # Return zero features on error
            return {name: 0.0 for name in self.feature_names}

    def extract_batch_features(
        self,
        feedback_list: List[Dict[str, Any]],
        match_list: Optional[List[Dict[str, Any]]] = None,
        resume_list: Optional[List[Dict[str, Any]]] = None,
        vacancy_list: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[npt.NDArray[np.float64], List[str]]:
        """
        Extract features for a batch of feedback entries.

        Args:
            feedback_list: List of feedback dictionaries
            match_list: Optional list of match dictionaries (same length as feedback_list)
            resume_list: Optional list of resume dictionaries
            vacancy_list: Optional list of vacancy dictionaries

        Returns:
            Tuple of:
            - Feature matrix (numpy array of shape [n_samples, n_features])
            - List of feature names

        Example:
            >>> extractor = FeatureExtractor()
            >>> feedback = [{"skill": "python", "was_correct": True}]
            >>> features, names = extractor.extract_batch_features(feedback)
            >>> features.shape
            (1, N)
        """
        try:
            feature_vectors = []

            for i, feedback_data in enumerate(feedback_list):
                # Get corresponding data from lists if available
                match_data = match_list[i] if match_list and i < len(match_list) else None
                resume_data = (
                    resume_list[i] if resume_list and i < len(resume_list) else None
                )
                vacancy_data = (
                    vacancy_list[i] if vacancy_list and i < len(vacancy_list) else None
                )

                # Extract features
                features = self.extract_training_features(
                    feedback_data, match_data, resume_data, vacancy_data
                )

                # Convert to list in feature name order
                feature_vector = [
                    features.get(name, 0.0) for name in self.feature_names
                ]
                feature_vectors.append(feature_vector)

            # Convert to numpy array
            feature_matrix = np.array(feature_vectors, dtype=np.float64)

            logger.info(
                f"Extracted batch features: shape={feature_matrix.shape}, "
                f"n_samples={len(feedback_list)}"
            )

            return feature_matrix, self.feature_names

        except Exception as e:
            logger.error(f"Error extracting batch features: {e}", exc_info=True)
            # Return empty array on error
            return np.array([], dtype=np.float64).reshape(0, len(self.feature_names)), self.feature_names

    def get_feature_importance(
        self,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Get default feature importance weights.

        Provides default importance weights for features that can be used
        for feature selection or weighting during training.

        Args:
            feature_names: Optional list of feature names. Defaults to self.feature_names.

        Returns:
            Dictionary mapping feature names to importance weights

        Example:
            >>> extractor = FeatureExtractor()
            >>> importance = extractor.get_feature_importance()
            >>> print(importance["overall_score"])
            0.15
        """
        if feature_names is None:
            feature_names = self.feature_names

        # Default importance weights based on domain knowledge
        default_importance = {
            FEATURE_SKILL_SIMILARITY: 0.15,
            FEATURE_SKILL_CONFIDENCE: 0.10,
            FEATURE_MATCH_PERCENTAGE: 0.08,
            FEATURE_OVERALL_SCORE: 0.15,
            FEATURE_KEYWORD_SCORE: 0.08,
            FEATURE_TFIDF_SCORE: 0.08,
            FEATURE_VECTOR_SCORE: 0.08,
            FEATURE_SKILL_COUNT_MATCHED: 0.05,
            FEATURE_SKILL_COUNT_MISSING: 0.05,
            FEATURE_SKILL_MATCH_RATIO: 0.08,
            FEATURE_EXPERIENCE_VERIFIED: 0.03,
            FEATURE_FEEDBACK_RECENCY_DAYS: 0.02,
            # Note: feedback_correctness is the label, not a feature
            FEATURE_FEEDBACK_CORRECTNESS: 0.0,
            FEATURE_VACANCY_SKILL_COUNT: 0.01,
            FEATURE_RESUME_SKILL_COUNT: 0.01,
            FEATURE_SKILL_OVERLAP_RATIO: 0.03,
        }

        # Return importance only for requested features
        return {
            name: default_importance.get(name, 0.01)
            for name in feature_names
        }

    def normalize_features(
        self,
        feature_matrix: npt.NDArray[np.float64],
        feature_names: Optional[List[str]] = None
    ) -> npt.NDArray[np.float64]:
        """
        Normalize feature matrix to [0, 1] range.

        Args:
            feature_matrix: Feature matrix of shape [n_samples, n_features]
            feature_names: Optional list of feature names

        Returns:
            Normalized feature matrix

        Example:
            >>> extractor = FeatureExtractor()
            >>> features = np.array([[0.5], [1.5], [2.5]])
            >>> normalized = extractor.normalize_features(features, ["feature1"])
            >>> normalized.max()
            1.0
        """
        try:
            if feature_matrix.size == 0:
                return feature_matrix

            normalized = feature_matrix.copy()

            # Normalize each feature column to [0, 1]
            for i in range(feature_matrix.shape[1]):
                column = feature_matrix[:, i]
                min_val = column.min()
                max_val = column.max()

                if max_val > min_val:
                    normalized[:, i] = (column - min_val) / (max_val - min_val)
                else:
                    # All values are the same
                    normalized[:, i] = 0.0

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing features: {e}", exc_info=True)
            return feature_matrix


# Convenience function for direct usage
def extract_training_features(
    feedback_data: Dict[str, Any],
    match_data: Optional[Dict[str, Any]] = None,
    resume_data: Optional[Dict[str, Any]] = None,
    vacancy_data: Optional[Dict[str, Any]] = None,
    feature_names: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Convenience function for extracting training features.

    This function creates a FeatureExtractor instance and extracts
    features from the provided data.

    Args:
        feedback_data: Dictionary containing feedback information
        match_data: Optional dictionary containing match result information
        resume_data: Optional dictionary containing resume information
        vacancy_data: Optional dictionary containing vacancy information
        feature_names: Optional list of feature names to extract

    Returns:
        Dictionary mapping feature names to feature values

    Example:
        >>> feedback = {"skill": "python", "was_correct": True}
        >>> features = extract_training_features(feedback)
        >>> print(features["feedback_correctness"])
        1.0
    """
    extractor = FeatureExtractor(feature_names=feature_names)
    return extractor.extract_training_features(
        feedback_data, match_data, resume_data, vacancy_data
    )
