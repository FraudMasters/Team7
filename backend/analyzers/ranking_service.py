"""
AI-powered Candidate Ranking Service

This module provides ML-based candidate ranking using scikit-learn models.
It considers multiple factors including:
- Skills match score
- Experience relevance
- Education quality
- Keyword/TF-IDF/Vector scores from unified matching
- Historical hiring outcomes
"""
import json
import logging
import pickle
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from numpy import typing as npt
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CandidateRank, JobVacancy, MatchResult, Resume, ResumeAnalysis
from models.ranking_weights_profile import RankingWeightProfile
from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)

# Model storage directory
MODELS_DIR = Path("app/models_cache/ranking")
MODELS_DIR.mkdir(parents=True, exist_ok=True)


class RankingFeatures:
    """
    Feature extraction for candidate ranking.

    Extracts and normalizes features used by the ML ranking model.
    """

    # Feature names for model training/inference
    FEATURE_NAMES = [
        "overall_match_score",
        "keyword_score",
        "tfidf_score",
        "vector_score",
        "skills_match_ratio",
        "experience_months",
        "experience_relevance",
        "education_level",
        "recent_experience",
        "skill_rarity_score",
        "title_similarity",
        "freshness_score",
        "completeness_score",
    ]

    # Education level mapping
    EDUCATION_LEVELS = {
        "phd": 5,
        "doctorate": 5,
        "master": 4,
        "ms": 4,
        "m.sc": 4,
        "mba": 4,
        "bachelor": 3,
        "bs": 3,
        "b.sc": 3,
        "ba": 3,
        "diploma": 2,
        "associate": 2,
        "certificate": 1,
        "high_school": 0,
        "none": 0,
    }

    @classmethod
    def extract_features(
        cls,
        resume_data: Dict[str, Any],
        vacancy_data: Dict[str, Any],
        match_result: Optional[Dict[str, Any]] = None,
    ) -> npt.NDArray[np.float64]:
        """
        Extract feature vector from resume and vacancy data.

        Args:
            resume_data: Resume data including skills, experience, education
            vacancy_data: Vacancy data with requirements
            match_result: Optional pre-computed match result from unified matching

        Returns:
            numpy array of feature values (shape: [n_features])
        """
        features = np.zeros(len(cls.FEATURE_NAMES), dtype=np.float64)

        # 1. Overall match score (from unified matching or computed)
        if match_result:
            features[0] = match_result.get("overall_score", 0.0)
        else:
            features[0] = cls._compute_basic_match(resume_data, vacancy_data)

        # 2. Individual matching scores
        if match_result:
            features[1] = match_result.get("keyword_score", 0.0)
            features[2] = match_result.get("tfidf_score", 0.0)
            features[3] = match_result.get("vector_score", 0.0)
        else:
            features[1] = features[2] = features[3] = features[0]

        # 4. Skills match ratio
        features[4] = cls._compute_skill_ratio(resume_data, vacancy_data)

        # 5. Experience months
        features[5] = cls._extract_experience_months(resume_data)

        # 6. Experience relevance (how well experience matches job requirements)
        features[6] = cls._compute_experience_relevance(resume_data, vacancy_data)

        # 7. Education level
        features[7] = cls._extract_education_level(resume_data)

        # 8. Recent experience (years of relevant experience in last 5 years)
        features[8] = cls._compute_recent_experience(resume_data, vacancy_data)

        # 9. Skill rarity score (rarer skills are more valuable)
        features[9] = cls._compute_skill_rarity(resume_data, vacancy_data)

        # 10. Title similarity
        features[10] = cls._compute_title_similarity(resume_data, vacancy_data)

        # 11. Freshness score (how recent is the resume)
        features[11] = cls._compute_freshness(resume_data)

        # 12. Completeness score (how complete is the resume)
        features[12] = cls._compute_completeness(resume_data)

        return features

    @classmethod
    def _compute_basic_match(cls, resume: Dict, vacancy: Dict) -> float:
        """Compute basic skill match ratio."""
        resume_skills = set(resume.get("skills", []))
        required_skills = set(vacancy.get("required_skills", []))

        if not required_skills:
            return 0.5  # Neutral score if no requirements

        matched = len(resume_skills & required_skills)
        return matched / len(required_skills)

    @classmethod
    def _compute_skill_ratio(cls, resume: Dict, vacancy: Dict) -> float:
        """Compute detailed skills match ratio."""
        resume_skills = [s.lower() for s in resume.get("skills", [])]
        required_skills = [s.lower() for s in vacancy.get("required_skills", [])]

        if not required_skills:
            return 1.0

        matched = sum(1 for rs in resume_skills if any(rs == req or rs in req or req in rs for req in required_skills))
        return min(matched / len(required_skills), 1.0)

    @classmethod
    def _extract_experience_months(cls, resume: Dict) -> float:
        """Extract total experience in months."""
        exp_data = resume.get("experience", {})
        if isinstance(exp_data, dict):
            return exp_data.get("total_months", 0)
        if isinstance(exp_data, (int, float)):
            return float(exp_data)
        return 0.0

    @classmethod
    def _compute_experience_relevance(cls, resume: Dict, vacancy: Dict) -> float:
        """Compute how relevant the experience is to the job."""
        resume_skills = set(s.lower() for s in resume.get("skills", []))
        required_skills = set(s.lower() for s in vacancy.get("required_skills", []))

        if not required_skills:
            return 0.5

        # Get experience details if available
        exp_details = resume.get("experience_details", {})
        if isinstance(exp_details, dict):
            relevant_exp = exp_details.get("relevant_months", 0)
            total_exp = exp_details.get("total_months", 1)
            if total_exp > 0:
                return min(relevant_exp / total_exp, 1.0)

        # Fallback: use skill overlap as proxy
        overlap = len(resume_skills & required_skills)
        return min(overlap / len(required_skills), 1.0)

    @classmethod
    def _extract_education_level(cls, resume: Dict) -> float:
        """Extract and normalize education level."""
        education = resume.get("education", {})
        if isinstance(education, dict):
            degree = education.get("degree", "").lower()
            level = education.get("level", "").lower()
        else:
            degree = str(education).lower()
            level = ""

        # Check degree and level against known values
        for key, value in cls.EDUCATION_LEVELS.items():
            if key in degree or key in level:
                return float(value) / 5.0  # Normalize to 0-1

        return 0.0

    @classmethod
    def _compute_recent_experience(cls, resume: Dict, vacancy: Dict) -> float:
        """Compute relevant experience in recent years."""
        # This would require parsed work history
        # For now, return a moderate score
        exp_months = cls._extract_experience_months(resume)
        years = exp_months / 12
        return min(years / 10, 1.0)  # Normalize to 0-1, assuming 10 years is excellent

    @classmethod
    def _compute_skill_rarity(cls, resume: Dict, vacancy: Dict) -> float:
        """
        Compute skill rarity score.

        Rarer skills that are required get higher scores.
        Common skills everyone has get lower scores.
        """
        required_skills = vacancy.get("required_skills", [])
        resume_skills = resume.get("skills", [])

        # Simple rarity heuristic: longer skill names are often more specific/rare
        rarity_sum = 0
        matched_count = 0

        for skill in required_skills:
            if any(s.lower() == skill.lower() for s in resume_skills):
                # Rarity based on skill name length (heuristic)
                rarity = min(len(skill.split()) / 3, 1.0)
                rarity_sum += rarity
                matched_count += 1

        if matched_count == 0:
            return 0.0

        return rarity_sum / max(matched_count, 1)

    @classmethod
    def _compute_title_similarity(cls, resume: Dict, vacancy: Dict) -> float:
        """Compute similarity between resume title and job title."""
        resume_title = resume.get("title", "").lower()
        vacancy_title = vacancy.get("title", vacancy.get("position", "")).lower()

        if not resume_title or not vacancy_title:
            return 0.0

        # Simple word overlap
        resume_words = set(resume_title.split())
        vacancy_words = set(vacancy_title.split())

        if not vacancy_words:
            return 0.0

        overlap = len(resume_words & vacancy_words)
        return min(overlap / len(vacancy_words), 1.0)

    @classmethod
    def _compute_freshness(cls, resume: Dict) -> float:
        """Compute freshness score based on resume update date."""
        updated_at = resume.get("updated_at")
        if isinstance(updated_at, str):
            try:
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                days_old = (datetime.now(dt.tzinfo) - dt).days
                # Freshness decays over time: 0 days = 1.0, 365+ days = 0.0
                return max(0, 1 - (days_old / 365))
            except Exception:
                pass

        return 0.5  # Default neutral score

    @classmethod
    def _compute_completeness(cls, resume: Dict) -> float:
        """Compute resume completeness score."""
        required_fields = ["skills", "experience", "education", "title"]
        filled = sum(1 for field in required_fields if resume.get(field))

        # Bonus for having contact info, summary
        bonus_fields = ["email", "phone", "summary"]
        bonus = sum(1 for field in bonus_fields if resume.get(field)) / len(bonus_fields) * 0.2

        base = filled / len(required_fields)
        return min(base + bonus, 1.0)


class RankingModel:
    """
    ML-based ranking model using scikit-learn.

    Uses ensemble methods (RandomForest + GradientBoosting) for robust predictions.
    """

    def __init__(self, model_type: str = "random_forest"):
        """
        Initialize the ranking model.

        Args:
            model_type: Type of model ('random_forest' or 'gradient_boosting')
        """
        self.model_type = model_type
        self.model: Optional[Any] = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.version = "1.0.0"

        # Try to load existing model
        self._load_model()

    def _load_model(self) -> bool:
        """Load model from disk if available."""
        model_path = MODELS_DIR / f"ranking_{self.model_type}_model.pkl"
        scaler_path = MODELS_DIR / f"ranking_{self.model_type}_scaler.pkl"

        if model_path.exists() and scaler_path.exists():
            try:
                with open(model_path, "rb") as f:
                    self.model = pickle.load(f)
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
                self.is_trained = True
                logger.info(f"Loaded ranking model from {model_path}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")

        return False

    def _save_model(self) -> bool:
        """Save model to disk."""
        if not self.is_trained or self.model is None:
            return False

        model_path = MODELS_DIR / f"ranking_{self.model_type}_model.pkl"
        scaler_path = MODELS_DIR / f"ranking_{self.model_type}_scaler.pkl"

        try:
            with open(model_path, "wb") as f:
                pickle.dump(self.model, f)
            with open(scaler_path, "wb") as f:
                pickle.dump(self.scaler, f)
            logger.info(f"Saved ranking model to {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def train(self, X: npt.NDArray[np.float64], y: npt.NDArray[np.int64]) -> Dict[str, float]:
        """
        Train the ranking model.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target labels (0=rejected, 1=hired) or ratings (1-5)

        Returns:
            Training metrics
        """
        logger.info(f"Training {self.model_type} ranking model with {len(X)} samples")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Initialize model
        if self.model_type == "gradient_boosting":
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42,
            )
        else:  # random_forest
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1,
            )

        # Train
        self.model.fit(X_scaled, y)
        self.is_trained = True

        # Calculate metrics
        y_pred = self.model.predict(X_scaled)
        accuracy = np.mean(y_pred == y)

        metrics = {
            "accuracy": float(accuracy),
            "n_samples": len(X),
            "n_features": X.shape[1],
        }

        # Save model
        self._save_model()

        logger.info(f"Training complete. Accuracy: {accuracy:.3f}")
        return metrics

    def predict_proba(self, features: npt.NDArray[np.float64]) -> float:
        """
        Predict hiring probability for a candidate.

        Args:
            features: Feature vector (n_features,)

        Returns:
            Probability of positive outcome (0-1)
        """
        start_time = time.time()
        model_name = f"ranking_{self.model_type}"

        try:
            if not self.is_trained or self.model is None:
                # Return heuristic score if model not trained
                result = float(np.mean(features))
            else:
                # Scale features
                features_scaled = self.scaler.transform(features.reshape(1, -1))

                # Get probability of positive class
                proba = self.model.predict_proba(features_scaled)[0]

                # Return probability of class 1 (hired/suitable)
                if len(proba) > 1:
                    result = float(proba[1])
                else:
                    result = float(proba[0])

            # Record inference metrics
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name=model_name,
                    operation="predict_proba",
                    duration=duration,
                    prediction_type="probability",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            return result

        except Exception as e:
            logger.error(f"Error in predict_proba: {e}", exc_info=True)
            raise

    def predict(self, features: npt.NDArray[np.float64]) -> Tuple[int, float]:
        """
        Predict hiring decision and confidence.

        Args:
            features: Feature vector (n_features,)

        Returns:
            Tuple of (prediction, confidence)
            prediction: 0=reject, 1=accept
            confidence: Model confidence (0-1)
        """
        start_time = time.time()
        model_name = f"ranking_{self.model_type}"

        try:
            if not self.is_trained or self.model is None:
                # Use heuristic
                score = float(np.mean(features))
                result = (1 if score > 0.5 else 0, abs(score - 0.5) * 2)
            else:
                features_scaled = self.scaler.transform(features.reshape(1, -1))
                prediction = int(self.model.predict(features_scaled)[0])

                # Get confidence from probability
                proba = self.model.predict_proba(features_scaled)[0]
                confidence = float(max(proba))

                result = (prediction, confidence)

            # Record inference metrics
            duration = time.time() - start_time
            try:
                registry = get_metrics_registry()
                registry.record_ml_inference(
                    model_name=model_name,
                    operation="predict",
                    duration=duration,
                    prediction_type="classification",
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record metrics: {metrics_error}")

            return result

        except Exception as e:
            logger.error(f"Error in predict: {e}", exc_info=True)
            raise

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from the trained model.

        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_trained or self.model is None:
            return {}

        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            return dict(zip(RankingFeatures.FEATURE_NAMES, importances))

        return {}

    @staticmethod
    def compute_dcg(relevances: List[float], k: Optional[int] = None) -> float:
        """
        Compute Discounted Cumulative Gain (DCG).

        DCG = sum(relevance_i / log2(i + 1)) for i in 1..k

        Args:
            relevances: List of relevance scores in ranked order
            k: Optional cutoff position (if None, use all items)

        Returns:
            DCG score
        """
        if k is not None:
            relevances = relevances[:k]

        dcg = 0.0
        for i, rel in enumerate(relevances, start=1):
            dcg += rel / np.log2(i + 1)

        return dcg

    @staticmethod
    def compute_ndcg(
        predicted_relevances: List[float],
        ideal_relevances: List[float],
        k: Optional[int] = None,
    ) -> float:
        """
        Compute Normalized Discounted Cumulative Gain (NDCG).

        NDCG = DCG(predicted) / DCG(ideal)

        Args:
            predicted_relevances: Relevances in predicted ranking order
            ideal_relevances: Relevances in ideal (perfect) order
            k: Optional cutoff position (if None, use all items)

        Returns:
            NDCG score (0-1, where 1 is perfect ranking)
        """
        dcg = RankingModel.compute_dcg(predicted_relevances, k)

        # Sort ideal relevances in descending order for ideal DCG
        sorted_ideal = sorted(ideal_relevances, reverse=True)
        idcg = RankingModel.compute_dcg(sorted_ideal, k)

        if idcg == 0:
            return 0.0

        return dcg / idcg

    @staticmethod
    def compute_mrr(relevances: List[float], threshold: float = 0.5) -> float:
        """
        Compute Mean Reciprocal Rank (MRR).

        MRR = 1 / rank of first relevant item

        Args:
            relevances: List of relevance scores in ranked order
            threshold: Minimum relevance score to consider an item relevant

        Returns:
            Reciprocal rank (0 if no relevant item found, 1 if first item is relevant)
        """
        for i, rel in enumerate(relevances, start=1):
            if rel >= threshold:
                return 1.0 / i

        return 0.0

    def evaluate_ranking(
        self,
        predicted_ranking: List[Tuple[str, float]],
        ground_truth: Dict[str, float],
        k_values: Optional[List[int]] = None,
    ) -> Dict[str, float]:
        """
        Evaluate ranking quality using NDCG and MRR metrics.

        Args:
            predicted_ranking: List of (item_id, predicted_score) tuples in ranked order
            ground_truth: Dictionary mapping item_id to true relevance score
            k_values: List of cutoff positions for NDCG@k (default: [5, 10, 20])

        Returns:
            Dictionary with NDCG@k and MRR metrics
        """
        if k_values is None:
            k_values = [5, 10, 20]

        metrics: Dict[str, float] = {}

        # Extract relevances for predicted ranking
        predicted_relevances = [
            ground_truth.get(item_id, 0.0)
            for item_id, _ in predicted_ranking
        ]

        # Get all ground truth relevances for ideal ranking
        ideal_relevances = list(ground_truth.values())

        # Compute NDCG@k for each k value
        for k in k_values:
            ndcg = self.compute_ndcg(predicted_relevances, ideal_relevances, k)
            metrics[f"ndcg@{k}"] = ndcg

        # Compute MRR
        metrics["mrr"] = self.compute_mrr(predicted_relevances)

        # Compute NDCG across all items (no cutoff)
        metrics["ndcg"] = self.compute_ndcg(
            predicted_relevances, ideal_relevances, k=None
        )

        return metrics

    def evaluate_batch(
        self,
        rankings: List[List[Tuple[str, float]]],
        ground_truths: List[Dict[str, float]],
        k_values: Optional[List[int]] = None,
    ) -> Dict[str, float]:
        """
        Evaluate ranking quality across multiple queries/vacancies.

        Computes mean NDCG@k and MRR across all rankings.

        Args:
            rankings: List of predicted rankings, each being a list of (item_id, score) tuples
            ground_truths: List of ground truth relevance dictionaries
            k_values: List of cutoff positions for NDCG@k

        Returns:
            Dictionary with mean metrics across all rankings
        """
        if len(rankings) != len(ground_truths):
            raise ValueError(
                f"Number of rankings ({len(rankings)}) must match "
                f"number of ground truths ({len(ground_truths)})"
            )

        if not rankings:
            return {"ndcg": 0.0, "mrr": 0.0}

        all_metrics: List[Dict[str, float]] = []

        for ranking, gt in zip(rankings, ground_truths):
            metrics = self.evaluate_ranking(ranking, gt, k_values)
            all_metrics.append(metrics)

        # Compute mean metrics
        mean_metrics: Dict[str, float] = {}
        metric_keys = all_metrics[0].keys()

        for key in metric_keys:
            values = [m[key] for m in all_metrics]
            mean_metrics[f"mean_{key}"] = float(np.mean(values))
            mean_metrics[f"std_{key}"] = float(np.std(values))

        mean_metrics["n_queries"] = float(len(rankings))

        return mean_metrics


class RankingService:
    """
    Main service for AI-powered candidate ranking.

    Coordinates feature extraction, model prediction, and result storage.
    """

    def __init__(self):
        """Initialize the ranking service."""
        self.model = RankingModel(model_type="random_forest")
        self.ab_test_ratio = 0.2  # 20% of candidates go to treatment group

    async def get_ranking_weights(
        self,
        db: AsyncSession,
        organization_id: Optional[UUID] = None,
        vacancy_id: Optional[UUID] = None,
    ) -> Optional[npt.NDArray[np.float64]]:
        """
        Get applicable ranking weights for organization or vacancy.

        Priority order:
        1. Vacancy-specific profile (if vacancy_id provided)
        2. Organization default profile (if organization_id provided)
        3. None (use default ML model)

        Args:
            db: Database session
            organization_id: Organization UUID
            vacancy_id: Vacancy UUID

        Returns:
            Numpy array of weights (13 elements) or None if no custom weights
        """
        profile = None

        # Try vacancy-specific profile first
        if vacancy_id:
            query = select(RankingWeightProfile).where(
                RankingWeightProfile.vacancy_id == vacancy_id,
                RankingWeightProfile.is_active == True,
            )
            result = await db.execute(query)
            profile = result.scalar_one_or_none()
            if profile:
                logger.info(f"Using vacancy-specific ranking weights: {profile.name}")

        # Try organization default profile
        if not profile and organization_id:
            query = select(RankingWeightProfile).where(
                RankingWeightProfile.organization_id == organization_id,
                RankingWeightProfile.is_active == True,
                RankingWeightProfile.vacancy_id.is_(None),
            )
            result = await db.execute(query)
            profile = result.scalar_one_or_none()
            if profile:
                logger.info(f"Using organization default ranking weights: {profile.name}")

        if profile:
            # Convert weights to numpy array matching feature order
            weights = np.array(profile.get_weights_as_list(), dtype=np.float64)
            logger.debug(f"Custom weights: {weights}")
            return weights

        return None

    async def rank_candidate(
        self,
        db: AsyncSession,
        resume_id: UUID,
        vacancy_id: UUID,
        use_experiment: bool = True,
    ) -> Dict[str, Any]:
        """
        Rank a candidate for a specific vacancy.

        Args:
            db: Database session
            resume_id: Resume UUID
            vacancy_id: JobVacancy UUID
            use_experiment: Whether to assign to A/B test experiment

        Returns:
            Ranking result with score, position, recommendation, etc.
        """
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

        # Try to get existing match result
        match_query = select(MatchResult).where(
            MatchResult.resume_id == resume_id,
            MatchResult.vacancy_id == vacancy_id,
        )
        match_result_obj = await db.execute(match_query)
        match_record = match_result_obj.scalar_one_or_none()

        match_result = None
        if match_record:
            match_result = {
                "overall_score": float(match_record.overall_score or 0),
                "keyword_score": float(match_record.keyword_score or 0),
                "tfidf_score": float(match_record.tfidf_score or 0),
                "vector_score": float(match_record.vector_score or 0),
            }

        # Prepare resume data dict
        resume_data = {
            "id": str(resume.id),
            "title": resume.raw_text[:100] if resume.raw_text else "",
            "skills": [],
            "experience": {},
            "education": {},
            "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
        }

        # Try to get skills from ResumeAnalysis
        analysis_query = select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)
        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()

        if analysis:
            if analysis.skills:
                resume_data["skills"] = analysis.skills
            if analysis.raw_text:
                resume_data["title"] = analysis.raw_text[:100]

        # Prepare vacancy data dict
        vacancy_data = {
            "id": str(vacancy.id),
            "title": vacancy.title,
            "required_skills": vacancy.required_skills or [],
            "description": vacancy.description or "",
        }

        # Extract features
        features = RankingFeatures.extract_features(resume_data, vacancy_data, match_result)

        # Check for custom ranking weights
        custom_weights = await self.get_ranking_weights(
            db=db,
            organization_id=UUID(vacancy.organization_id) if vacancy.organization_id else None,
            vacancy_id=vacancy_id,
        )

        # Calculate rank score using custom weights or ML model
        if custom_weights is not None:
            # Use weighted sum: score = sum(feature[i] * weight[i])
            rank_score = float(np.dot(features, custom_weights))
            # Normalize to 0-1 range (features are already 0-1, so weighted sum should be too)
            rank_score = np.clip(rank_score, 0.0, 1.0)
            # For custom weights, confidence is based on variance of weighted features
            weighted_features = features * custom_weights
            confidence = float(1.0 - np.std(weighted_features))
            prediction = 1 if rank_score > 0.5 else 0
            logger.info(f"Using custom weights: rank_score={rank_score:.3f}")
        else:
            # Use ML model prediction (backward compatibility)
            rank_score = self.model.predict_proba(features)
            prediction, confidence = self.model.predict(features)
            logger.debug(f"Using ML model: rank_score={rank_score:.3f}")

        # Determine A/B test group
        is_experiment = use_experiment and random.random() < self.ab_test_ratio
        experiment_group = None
        if is_experiment:
            experiment_group = "treatment" if random.random() < 0.5 else "control"

        # Determine recommendation
        recommendation = self._score_to_recommendation(rank_score)

        # Get feature contributions (using feature importance as proxy)
        feature_importance = self.model.get_feature_importance()
        feature_contributions = {
            name: float(features[i] * feature_importance.get(name, 0))
            for i, name in enumerate(RankingFeatures.FEATURE_NAMES)
        }

        # Build ranking factors detail
        ranking_factors = {
            "skills_match": {
                "score": float(features[4]),
                "matched": len([s for s in vacancy_data["required_skills"]
                              if s.lower() in [rs.lower() for rs in resume_data["skills"]]]),
                "total": len(vacancy_data["required_skills"]),
            },
            "experience_score": float(features[5] / 120),  # Normalize to ~0-1
            "education_score": float(features[7]),
            "freshness": float(features[11]),
        }

        # Create or update CandidateRank record
        existing_rank_query = select(CandidateRank).where(
            CandidateRank.resume_id == resume_id,
            CandidateRank.vacancy_id == vacancy_id,
        )
        existing_rank_result = await db.execute(existing_rank_query)
        existing_rank = existing_rank_result.scalar_one_or_none()

        if existing_rank:
            # Update existing
            existing_rank.rank_score = rank_score
            existing_rank.model_version = self.model.version
            existing_rank.model_type = self.model.model_type
            existing_rank.is_experiment = is_experiment
            existing_rank.experiment_group = experiment_group
            existing_rank.feature_contributions = feature_contributions
            existing_rank.ranking_factors = ranking_factors
            existing_rank.prediction_confidence = confidence
            existing_rank.recommendation = recommendation
        else:
            # Create new
            new_rank = CandidateRank(
                resume_id=resume_id,
                vacancy_id=vacancy_id,
                rank_score=rank_score,
                model_version=self.model.version,
                model_type=self.model.model_type,
                is_experiment=is_experiment,
                experiment_group=experiment_group,
                feature_contributions=feature_contributions,
                ranking_factors=ranking_factors,
                prediction_confidence=confidence,
                recommendation=recommendation,
            )
            db.add(new_rank)

        await db.commit()

        return {
            "resume_id": str(resume_id),
            "vacancy_id": str(vacancy_id),
            "rank_score": rank_score,
            "recommendation": recommendation,
            "confidence": confidence,
            "is_experiment": is_experiment,
            "experiment_group": experiment_group,
            "model_version": self.model.version,
            "feature_contributions": feature_contributions,
            "ranking_factors": ranking_factors,
        }

    async def rank_candidates_for_vacancy(
        self,
        db: AsyncSession,
        vacancy_id: UUID,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Rank multiple candidates for a vacancy.

        Args:
            db: Database session
            vacancy_id: JobVacancy UUID
            limit: Maximum number of candidates to return

        Returns:
            List of ranked candidates with scores
        """
        # Get all resumes
        resume_query = select(Resume).where(Resume.status == "COMPLETED").limit(limit * 2)
        resume_result = await db.execute(resume_query)
        resumes = resume_result.scalars().all()

        rankings = []
        for resume in resumes:
            try:
                ranking = await self.rank_candidate(
                    db, resume.id, vacancy_id, use_experiment=True
                )
                rankings.append(ranking)
            except Exception as e:
                logger.warning(f"Failed to rank candidate {resume.id}: {e}")
                continue

        # Sort by rank score and assign positions
        rankings.sort(key=lambda x: x["rank_score"], reverse=True)
        for i, ranking in enumerate(rankings):
            ranking["rank_position"] = i + 1

        return rankings[:limit]

    def _score_to_recommendation(self, score: float) -> str:
        """Convert numeric score to recommendation."""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "maybe"
        return "poor"

    async def submit_feedback(
        self,
        db: AsyncSession,
        rank_id: UUID,
        was_helpful: bool,
        actual_outcome: Optional[str] = None,
        adjusted_score: Optional[float] = None,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit feedback on a ranking.

        Args:
            db: Database session
            rank_id: CandidateRank UUID
            was_helpful: Whether the ranking was helpful
            actual_outcome: Actual hiring outcome
            adjusted_score: Recruiter's adjusted score
            comments: Optional comments

        Returns:
            Created feedback record
        """
        from models.candidate_rank import RankingFeedback

        feedback = RankingFeedback(
            rank_id=rank_id,
            was_helpful=was_helpful,
            actual_outcome=actual_outcome,
            adjusted_score=adjusted_score,
            comments=comments,
            feedback_source="web_ui",
        )

        db.add(feedback)
        await db.commit()

        return {
            "id": str(feedback.id),
            "rank_id": str(feedback.rank_id),
            "was_helpful": feedback.was_helpful,
            "actual_outcome": feedback.actual_outcome,
        }


# Global service instance
_ranking_service: Optional[RankingService] = None


def get_ranking_service() -> RankingService:
    """Get or create global ranking service instance."""
    global _ranking_service
    if _ranking_service is None:
        _ranking_service = RankingService()
    return _ranking_service
