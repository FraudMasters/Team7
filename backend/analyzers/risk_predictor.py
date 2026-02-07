"""
AI-powered Risk Predictor for identifying candidates at risk of loss.

This module provides ML-based prediction of candidates who are likely to
accept competing offers or withdraw from the hiring process. It considers
multiple factors including:
- Time in pipeline (stale candidates are more likely to look elsewhere)
- Resume freshness (recent updates indicate active job searching)
- Skills demand (candidates with high-demand skills have more options)
- Engagement patterns (slow responses, missed communications)
- Hiring stage (candidates waiting longer at any stage are at higher risk)
- Market factors (skill scarcity, competition level)
"""
import json
import logging
import pickle
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from numpy import typing as npt
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CandidateRecommendation, JobVacancy, Resume, ResumeAnalysis
from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)

# Model storage directory
MODELS_DIR = Path("app/models_cache/risk")
MODELS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class RiskPredictionResult:
    """
    Result from risk prediction analysis for a candidate.

    Attributes:
        resume_id: UUID of the candidate's resume
        risk_score: Overall risk score (0-1, higher = more likely to accept competing offer)
        risk_level: Categorical risk level (low, medium, high, critical)
        primary_risk_factors: List of main factors contributing to risk
        feature_contributions: Dictionary of feature names to their contribution scores
        explanation: Human-readable explanation of the risk assessment
        recommended_actions: Suggested actions to mitigate risk
        confidence: Model confidence in prediction (0-1)
        model_version: Version of the risk model used
        predicted_at: Timestamp when prediction was made
    """

    resume_id: str = ""
    risk_score: float = 0.0
    risk_level: str = "low"  # low, medium, high, critical
    primary_risk_factors: List[str] = field(default_factory=list)
    feature_contributions: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""
    recommended_actions: List[str] = field(default_factory=list)
    confidence: float = 0.0
    model_version: str = "v1.0"
    predicted_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "resume_id": self.resume_id,
            "risk_score": round(self.risk_score, 4),
            "risk_level": self.risk_level,
            "primary_risk_factors": self.primary_risk_factors,
            "feature_contributions": {
                k: round(v, 4) for k, v in self.feature_contributions.items()
            },
            "explanation": self.explanation,
            "recommended_actions": self.recommended_actions,
            "confidence": round(self.confidence, 4),
            "model_version": self.model_version,
            "predicted_at": self.predicted_at,
        }


class RiskFeatures:
    """
    Feature extraction for candidate risk prediction.

    Extracts and normalizes features used by the ML risk model.
    """

    # Feature names for model training/inference
    FEATURE_NAMES = [
        "days_in_pipeline",
        "days_since_last_contact",
        "resume_freshness_days",
        "skills_rarity_score",
        "skills_demand_score",
        "engagement_score",
        "response_time_avg_hours",
        "missed_communications",
        "interview_stage",
        "stage_duration_days",
        "competing_applications",
        "salary_expectation_gap",
        "location_match_score",
        "experience_level",
        "education_level",
    ]

    # Interview stage mapping to numeric values
    INTERVIEW_STAGES = {
        "applied": 1,
        "screening": 2,
        "initial_interview": 3,
        "technical_interview": 4,
        "final_interview": 5,
        "offer": 6,
        "hired": 7,
        "rejected": 0,
        "withdrawn": -1,
    }

    # Risk level thresholds
    RISK_THRESHOLDS = {
        "low": 0.3,
        "medium": 0.5,
        "high": 0.7,
        "critical": 0.85,
    }

    @classmethod
    def extract_features(
        cls,
        resume_data: Dict[str, Any],
        pipeline_data: Dict[str, Any],
        vacancy_data: Optional[Dict[str, Any]] = None,
    ) -> npt.NDArray[np.float64]:
        """
        Extract feature vector from resume and pipeline data.

        Args:
            resume_data: Resume data including skills, experience, education
            pipeline_data: Hiring pipeline data (stage, dates, engagement)
            vacancy_data: Optional vacancy data for context

        Returns:
            numpy array of feature values (shape: [n_features])
        """
        features = np.zeros(len(cls.FEATURE_NAMES), dtype=np.float64)

        # 1. Days in pipeline (how long has candidate been in process)
        features[0] = cls._compute_days_in_pipeline(pipeline_data)

        # 2. Days since last contact
        features[1] = cls._compute_days_since_last_contact(pipeline_data)

        # 3. Resume freshness (days since last update)
        features[2] = cls._compute_resume_freshness(resume_data)

        # 4. Skills rarity score (rarer skills = higher demand = higher risk)
        features[3] = cls._compute_skills_rarity(resume_data)

        # 5. Skills demand score (in-demand skills = more options = higher risk)
        features[4] = cls._compute_skills_demand(resume_data)

        # 6. Engagement score (lower engagement = higher risk)
        features[5] = cls._compute_engagement_score(pipeline_data)

        # 7. Average response time in hours
        features[6] = cls._compute_response_time(pipeline_data)

        # 8. Number of missed communications
        features[7] = cls._compute_missed_communications(pipeline_data)

        # 9. Interview stage (normalized)
        features[8] = cls._normalize_interview_stage(pipeline_data)

        # 10. Days at current stage (stalled at a stage = higher risk)
        features[9] = cls._compute_stage_duration(pipeline_data)

        # 11. Estimated competing applications (inferred)
        features[10] = cls._estimate_competing_applications(resume_data)

        # 12. Salary expectation gap (if available)
        features[11] = cls._compute_salary_gap(resume_data, vacancy_data)

        # 13. Location match score
        features[12] = cls._compute_location_match(resume_data, vacancy_data)

        # 14. Experience level
        features[13] = cls._compute_experience_level(resume_data)

        # 15. Education level
        features[14] = cls._compute_education_level(resume_data)

        return features

    @classmethod
    def _compute_days_in_pipeline(cls, pipeline: Dict) -> float:
        """Compute how many days the candidate has been in the hiring pipeline."""
        applied_at = pipeline.get("applied_at")
        if applied_at:
            try:
                if isinstance(applied_at, str):
                    applied_date = datetime.fromisoformat(applied_at.replace("Z", "+00:00"))
                else:
                    applied_date = applied_at
                days = (datetime.now(applied_date.tzinfo) - applied_date).days
                return min(days / 90, 1.0)  # Normalize to 0-1, 90 days = max
            except Exception:
                pass
        return 0.0

    @classmethod
    def _compute_days_since_last_contact(cls, pipeline: Dict) -> float:
        """Compute days since last communication."""
        last_contact = pipeline.get("last_contact_at")
        if last_contact:
            try:
                if isinstance(last_contact, str):
                    last_date = datetime.fromisoformat(last_contact.replace("Z", "+00:00"))
                else:
                    last_date = last_contact
                days = (datetime.now(last_date.tzinfo) - last_date).days
                return min(days / 30, 1.0)  # Normalize to 0-1, 30 days = max risk
            except Exception:
                pass
        return 0.0

    @classmethod
    def _compute_resume_freshness(cls, resume: Dict) -> float:
        """Compute resume freshness score (older updates = higher risk)."""
        updated_at = resume.get("updated_at")
        if updated_at:
            try:
                if isinstance(updated_at, str):
                    updated_date = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                else:
                    updated_date = updated_at
                days = (datetime.now(updated_date.tzinfo) - updated_date).days
                # Recent update (within 7 days) = low risk, old (60+ days) = high risk
                return min(days / 60, 1.0)
            except Exception:
                pass
        return 0.5  # Default neutral

    @classmethod
    def _compute_skills_rarity(cls, resume: Dict) -> float:
        """
        Compute skills rarity score.

        Rarer, more specialized skills indicate candidate has more options
        and is at higher risk of accepting competing offers.
        """
        skills = resume.get("skills", [])
        if not skills:
            return 0.5

        # Heuristic: longer skill names and multi-word skills are often more specialized
        rarity_scores = []
        for skill in skills:
            # Normalize by word count and length
            word_count = len(skill.split())
            length = len(skill)
            # Specialized skills tend to be longer and multi-word
            rarity = min((word_count * 0.3 + length / 50) / 2, 1.0)
            rarity_scores.append(rarity)

        return np.mean(rarity_scores) if rarity_scores else 0.5

    @classmethod
    def _compute_skills_demand(cls, resume: Dict) -> float:
        """
        Compute skills demand score.

        High-demand skills (cloud, ML, security) mean candidate has more options.
        """
        skills = [s.lower() for s in resume.get("skills", [])]

        # List of high-demand skills (this could be loaded from market data)
        high_demand_skills = {
            "python", "javascript", "react", "node.js", "aws", "azure", "gcp",
            "kubernetes", "docker", "tensorflow", "pytorch", "machine learning",
            "data science", "devops", "security", "blockchain", "rust", "go",
            "kotlin", "swift", "sql", "nosql", "mongodb", "postgresql",
        }

        if not skills:
            return 0.5

        matched = sum(1 for skill in skills if any(hds in skill for hds in high_demand_skills))
        ratio = matched / len(skills)

        # More high-demand skills = higher risk
        return ratio

    @classmethod
    def _compute_engagement_score(cls, pipeline: Dict) -> float:
        """
        Compute engagement score.

        Lower engagement = higher risk. Return 1.0 - engagement so higher
        value indicates higher risk.
        """
        # Engagement metrics from pipeline
        email_open_rate = pipeline.get("email_open_rate", 0.5)
        response_rate = pipeline.get("response_rate", 0.5)
        profile_views = pipeline.get("profile_views", 0)
        login_frequency = pipeline.get("login_frequency_days", 7)

        # Compute engagement (0-1, higher = more engaged)
        engagement = (
            email_open_rate * 0.3 +
            response_rate * 0.4 +
            min(profile_views / 10, 1.0) * 0.2 +
            max(0, 1 - login_frequency / 30) * 0.1
        )

        # Return risk score (lower engagement = higher risk)
        return 1.0 - engagement

    @classmethod
    def _compute_response_time(cls, pipeline: Dict) -> float:
        """
        Compute average response time.

        Slower response = higher risk.
        """
        avg_hours = pipeline.get("avg_response_hours", 24)

        # Normalize: < 24 hours = low risk (0), > 7 days = high risk (1)
        response_time_score = min(avg_hours / (24 * 7), 1.0)

        return response_time_score

    @classmethod
    def _compute_missed_communications(cls, pipeline: Dict) -> float:
        """
        Compute missed communications score.

        More missed communications = higher risk.
        """
        missed = pipeline.get("missed_communications", 0)
        total = pipeline.get("total_communications", 1)

        if total == 0:
            return 0.0

        missed_ratio = missed / total
        return min(missed_ratio * 2, 1.0)  # Amplify the impact

    @classmethod
    def _normalize_interview_stage(cls, pipeline: Dict) -> float:
        """
        Normalize interview stage.

        Later stages = candidate has invested more time = might be more committed
        but also might be getting offers from other companies.
        """
        stage = pipeline.get("stage", "applied").lower()
        stage_value = cls.INTERVIEW_STAGES.get(stage, 1)

        # Normalize to 0-1 (stages 0-7)
        return max(0, min(stage_value / 7, 1.0))

    @classmethod
    def _compute_stage_duration(cls, pipeline: Dict) -> float:
        """
        Compute days at current stage.

        Stalled at a stage for too long = higher risk.
        """
        stage_entered_at = pipeline.get("stage_entered_at")
        stage = pipeline.get("stage", "applied").lower()
        stage_value = cls.INTERVIEW_STAGES.get(stage, 1)

        if stage_entered_at:
            try:
                if isinstance(stage_entered_at, str):
                    stage_date = datetime.fromisoformat(stage_entered_at.replace("Z", "+00:00"))
                else:
                    stage_date = stage_entered_at
                days = (datetime.now(stage_date.tzinfo) - stage_date).days

                # Different stages have different expected durations
                # Early stages: 7 days is normal, later stages: 14 days
                expected_duration = 7 if stage_value <= 3 else 14
                return min(days / expected_duration, 1.0)
            except Exception:
                pass

        return 0.0

    @classmethod
    def _estimate_competing_applications(cls, resume: Dict) -> float:
        """
        Estimate number of competing applications.

        This is heuristic based on resume quality and activity.
        """
        # Factors indicating more competing applications:
        # - High quality resume (good skills, experience)
        # - Recent updates
        # - Completeness

        quality_score = 0.0

        # Skills diversity
        skills = resume.get("skills", [])
        if len(skills) >= 10:
            quality_score += 0.3
        elif len(skills) >= 5:
            quality_score += 0.2

        # Experience level
        exp_months = resume.get("experience", {}).get("total_months", 0)
        if exp_months >= 60:  # 5+ years
            quality_score += 0.3
        elif exp_months >= 36:  # 3+ years
            quality_score += 0.2

        # Education
        education = resume.get("education", {})
        if education.get("level"):
            quality_score += 0.2

        # Completeness
        required_fields = ["skills", "experience", "education"]
        completeness = sum(1 for f in required_fields if resume.get(f))
        quality_score += (completeness / 3) * 0.2

        return min(quality_score, 1.0)

    @classmethod
    def _compute_salary_gap(cls, resume: Dict, vacancy: Optional[Dict]) -> float:
        """
        Compute salary expectation gap.

        Large gap between expected and offered = higher risk.
        """
        if not vacancy:
            return 0.0

        expected = resume.get("salary_expectation")
        offered = vacancy.get("salary_max")

        if expected and offered:
            try:
                gap = (expected - offered) / offered
                return min(max(gap, 0), 1.0)  # Only if expecting more than offered
            except Exception:
                pass

        return 0.0

    @classmethod
    def _compute_location_match(cls, resume: Dict, vacancy: Optional[Dict]) -> float:
        """
        Compute location match score.

        Poor location match = higher risk of declining.
        """
        if not vacancy:
            return 0.0

        candidate_location = resume.get("location", "").lower()
        vacancy_location = vacancy.get("location", "").lower()

        if not candidate_location or not vacancy_location:
            return 0.5  # Neutral if unknown

        # Simple match check
        if candidate_location == vacancy_location:
            return 0.0  # Perfect match = low risk

        # Check for partial match (same city/region)
        if any(loc in candidate_location for loc in vacancy_location.split()) or \
           any(loc in vacancy_location for loc in candidate_location.split()):
            return 0.3  # Partial match = moderate risk

        return 0.7  # No match = high risk

    @classmethod
    def _compute_experience_level(cls, resume: Dict) -> float:
        """Compute and normalize experience level."""
        exp_months = resume.get("experience", {}).get("total_months", 0)

        # Normalize to 0-1 (10+ years = max)
        return min(exp_months / 120, 1.0)

    @classmethod
    def _compute_education_level(cls, resume: Dict) -> float:
        """Compute and normalize education level."""
        education = resume.get("education", {})

        # Simple mapping
        degree = education.get("degree", "").lower()
        level = education.get("level", "").lower()

        if "phd" in degree or "doctor" in degree:
            return 1.0
        elif "master" in degree or "mba" in degree:
            return 0.8
        elif "bachelor" in degree or "bs" in degree or "ba" in degree:
            return 0.6
        elif "associate" in degree or "diploma" in degree:
            return 0.4
        elif "certificate" in degree:
            return 0.2

        return 0.0


class RiskModel:
    """
    ML-based risk prediction model using scikit-learn.

    Uses ensemble methods for robust predictions of candidate attrition risk.
    """

    def __init__(self, model_type: str = "random_forest"):
        """
        Initialize the risk model.

        Args:
            model_type: Type of model ('random_forest' or 'logistic_regression')
        """
        self.model_type = model_type
        self.model: Optional[Any] = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.version = "v1.0"

        # Try to load existing model
        self._load_model()

    def _load_model(self) -> bool:
        """Load model from disk if available."""
        model_path = MODELS_DIR / f"risk_{self.model_type}_model.pkl"
        scaler_path = MODELS_DIR / f"risk_{self.model_type}_scaler.pkl"

        if model_path.exists() and scaler_path.exists():
            try:
                with open(model_path, "rb") as f:
                    self.model = pickle.load(f)
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
                self.is_trained = True
                logger.info(f"Loaded risk model from {model_path}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")

        return False

    def _save_model(self) -> bool:
        """Save model to disk."""
        if not self.is_trained or self.model is None:
            return False

        model_path = MODELS_DIR / f"risk_{self.model_type}_model.pkl"
        scaler_path = MODELS_DIR / f"risk_{self.model_type}_scaler.pkl"

        try:
            with open(model_path, "wb") as f:
                pickle.dump(self.model, f)
            with open(scaler_path, "wb") as f:
                pickle.dump(self.scaler, f)
            logger.info(f"Saved risk model to {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def train(self, X: npt.NDArray[np.float64], y: npt.NDArray[np.int64]) -> Dict[str, float]:
        """
        Train the risk model.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target labels (0=stayed, 1=withdrawn/accepted_other_offer)

        Returns:
            Training metrics
        """
        logger.info(f"Training {self.model_type} risk model with {len(X)} samples")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Initialize model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",  # Handle imbalanced data
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
        Predict risk probability for a candidate.

        Args:
            features: Feature vector (n_features,)

        Returns:
            Probability of risk (0-1)
        """
        start_time = time.time()
        model_name = f"risk_{self.model_type}"

        try:
            if not self.is_trained or self.model is None:
                # Return heuristic score if model not trained
                result = float(np.mean(features))
            else:
                # Scale features
                features_scaled = self.scaler.transform(features.reshape(1, -1))

                # Get probability of positive class (risk)
                proba = self.model.predict_proba(features_scaled)[0]

                # Return probability of class 1 (at risk)
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
            return dict(zip(RiskFeatures.FEATURE_NAMES, importances))

        return {}


class RiskPredictor:
    """
    Main service for AI-powered candidate risk prediction.

    Coordinates feature extraction, model prediction, and result storage.
    """

    def __init__(self):
        """Initialize the risk predictor service."""
        self.model = RiskModel(model_type="random_forest")
        self.ab_test_ratio = 0.2  # 20% of predictions go to treatment group

    async def predict_risk(
        self,
        db: AsyncSession,
        resume_id: UUID,
        vacancy_id: Optional[UUID] = None,
        pipeline_data: Optional[Dict[str, Any]] = None,
        use_experiment: bool = True,
    ) -> RiskPredictionResult:
        """
        Predict risk for a candidate.

        Args:
            db: Database session
            resume_id: Resume UUID
            vacancy_id: Optional JobVacancy UUID for context
            pipeline_data: Optional pipeline data (stage, dates, engagement)
            use_experiment: Whether to assign to A/B test experiment

        Returns:
            RiskPredictionResult with comprehensive risk assessment
        """
        # Fetch resume data
        resume_query = select(Resume).where(Resume.id == resume_id)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        # Try to get resume analysis
        analysis_query = select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)
        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()

        # Prepare resume data dict
        resume_data = {
            "id": str(resume.id),
            "skills": analysis.skills if analysis and analysis.skills else [],
            "experience": {},
            "education": {},
            "location": "",
            "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
        }

        if analysis:
            if analysis.raw_data:
                resume_data.update(analysis.raw_data)

        # Fetch vacancy data if provided
        vacancy_data = None
        if vacancy_id:
            vacancy_query = select(JobVacancy).where(JobVacancy.id == vacancy_id)
            vacancy_result = await db.execute(vacancy_query)
            vacancy = vacancy_result.scalar_one_or_none()
            if vacancy:
                vacancy_data = {
                    "id": str(vacancy.id),
                    "title": vacancy.title,
                    "location": vacancy.location or "",
                    "salary_min": float(vacancy.salary_min) if vacancy.salary_min else 0,
                    "salary_max": float(vacancy.salary_max) if vacancy.salary_max else 0,
                }

        # Prepare pipeline data
        if pipeline_data is None:
            pipeline_data = {}

        # Extract features
        features = RiskFeatures.extract_features(resume_data, pipeline_data, vacancy_data)

        # Get model prediction
        risk_score = self.model.predict_proba(features)

        # Get feature importance
        feature_importance = self.model.get_feature_importance()
        feature_contributions = {
            name: float(features[i] * feature_importance.get(name, 0))
            for i, name in enumerate(RiskFeatures.FEATURE_NAMES)
        }

        # Determine risk level
        risk_level = self._score_to_risk_level(risk_score)

        # Identify primary risk factors (top contributing features)
        primary_factors = self._get_primary_risk_factors(
            feature_contributions, top_n=3
        )

        # Generate explanation
        explanation = self._generate_explanation(
            risk_score, risk_level, primary_factors, pipeline_data
        )

        # Generate recommended actions
        recommended_actions = self._generate_recommendations(
            risk_level, primary_factors, pipeline_data
        )

        # Build result
        result = RiskPredictionResult(
            resume_id=str(resume_id),
            risk_score=risk_score,
            risk_level=risk_level,
            primary_risk_factors=primary_factors,
            feature_contributions=feature_contributions,
            explanation=explanation,
            recommended_actions=recommended_actions,
            confidence=0.8 if self.model.is_trained else 0.5,
            model_version=self.model.version,
            predicted_at=datetime.now().isoformat(),
        )

        # Store recommendation in database
        await self._store_risk_recommendation(
            db=db,
            resume_id=resume_id,
            vacancy_id=vacancy_id,
            risk_result=result,
            use_experiment=use_experiment,
        )

        return result

    async def predict_candidates_at_risk(
        self,
        db: AsyncSession,
        vacancy_id: Optional[UUID] = None,
        limit: int = 50,
        min_risk_score: float = 0.5,
    ) -> List[RiskPredictionResult]:
        """
        Predict risk for multiple candidates and return those at risk.

        Args:
            db: Database session
            vacancy_id: Optional JobVacancy UUID to filter candidates
            limit: Maximum number of at-risk candidates to return
            min_risk_score: Minimum risk score to include in results

        Returns:
            List of RiskPredictionResult for candidates at or above min_risk_score
        """
        # Get resumes (optionally filtered by vacancy applications)
        resume_query = select(Resume).where(Resume.status == "COMPLETED").limit(limit * 2)
        resume_result = await db.execute(resume_query)
        resumes = resume_result.scalars().all()

        at_risk_candidates = []
        for resume in resumes:
            try:
                result = await self.predict_risk(
                    db, resume.id, vacancy_id, use_experiment=False
                )
                if result.risk_score >= min_risk_score:
                    at_risk_candidates.append(result)
            except Exception as e:
                logger.warning(f"Failed to predict risk for {resume.id}: {e}")
                continue

        # Sort by risk score descending
        at_risk_candidates.sort(key=lambda r: r.risk_score, reverse=True)

        return at_risk_candidates[:limit]

    async def _store_risk_recommendation(
        self,
        db: AsyncSession,
        resume_id: UUID,
        vacancy_id: Optional[UUID],
        risk_result: RiskPredictionResult,
        use_experiment: bool,
    ) -> None:
        """
        Store risk prediction as a recommendation in the database.

        Args:
            db: Database session
            resume_id: Resume UUID
            vacancy_id: Optional JobVacancy UUID
            risk_result: Risk prediction result
            use_experiment: Whether to use A/B testing
        """
        import random

        # Determine A/B test group
        is_experiment = use_experiment and random.random() < self.ab_test_ratio
        experiment_group = None
        if is_experiment:
            experiment_group = "treatment" if random.random() < 0.5 else "control"

        # Create or update CandidateRecommendation record
        existing_query = select(CandidateRecommendation).where(
            CandidateRecommendation.resume_id == resume_id,
            CandidateRecommendation.vacancy_id == vacancy_id,
            CandidateRecommendation.recommendation_type == "at_risk",
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.score = risk_result.risk_score
            existing.risk_score = risk_result.risk_score
            existing.feature_contributions = risk_result.feature_contributions
            existing.explanation = risk_result.explanation
            existing.context = {
                "risk_level": risk_result.risk_level,
                "primary_factors": risk_result.primary_risk_factors,
                "recommended_actions": risk_result.recommended_actions,
            }
            existing.model_version = risk_result.model_version
            existing.is_experiment = is_experiment
            existing.experiment_group = experiment_group
        else:
            # Create new
            new_rec = CandidateRecommendation(
                resume_id=resume_id,
                vacancy_id=vacancy_id,
                recommendation_type="at_risk",
                score=risk_result.risk_score,
                risk_score=risk_result.risk_score,
                reason=risk_result.primary_risk_factors[0] if risk_result.primary_risk_factors else "high_risk",
                feature_contributions=risk_result.feature_contributions,
                explanation=risk_result.explanation,
                context={
                    "risk_level": risk_result.risk_level,
                    "primary_factors": risk_result.primary_risk_factors,
                    "recommended_actions": risk_result.recommended_actions,
                },
                model_version=risk_result.model_version,
                algorithm="random_forest",
                is_experiment=is_experiment,
                experiment_group=experiment_group,
            )
            db.add(new_rec)

        await db.commit()

    def _score_to_risk_level(self, score: float) -> str:
        """Convert numeric score to risk level category."""
        if score >= RiskFeatures.RISK_THRESHOLDS["critical"]:
            return "critical"
        elif score >= RiskFeatures.RISK_THRESHOLDS["high"]:
            return "high"
        elif score >= RiskFeatures.RISK_THRESHOLDS["medium"]:
            return "medium"
        return "low"

    def _get_primary_risk_factors(
        self,
        feature_contributions: Dict[str, float],
        top_n: int = 3,
    ) -> List[str]:
        """
        Get the top contributing features as primary risk factors.

        Args:
            feature_contributions: Dictionary of feature names to contributions
            top_n: Number of top factors to return

        Returns:
            List of primary risk factor names
        """
        # Sort by contribution descending
        sorted_features = sorted(
            feature_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        # Map feature names to human-readable labels
        factor_labels = {
            "days_in_pipeline": "Time in hiring process",
            "days_since_last_contact": "Time since last contact",
            "resume_freshness_days": "Recent job search activity",
            "skills_rarity_score": "Specialized skills",
            "skills_demand_score": "High-demand skills",
            "engagement_score": "Low engagement",
            "response_time_avg_hours": "Slow response time",
            "missed_communications": "Missed communications",
            "interview_stage": "Interview stage",
            "stage_duration_days": "Time at current stage",
            "competing_applications": "Competing opportunities",
            "salary_expectation_gap": "Salary expectations",
            "location_match_score": "Location mismatch",
            "experience_level": "Experience level",
            "education_level": "Education level",
        }

        primary_factors = []
        for feature_name, _ in sorted_features[:top_n]:
            label = factor_labels.get(feature_name, feature_name)
            if label not in primary_factors:
                primary_factors.append(label)

        return primary_factors

    def _generate_explanation(
        self,
        risk_score: float,
        risk_level: str,
        primary_factors: List[str],
        pipeline_data: Dict[str, Any],
    ) -> str:
        """Generate human-readable explanation of the risk assessment."""
        if risk_level == "critical":
            intro = "This candidate is at critical risk of accepting a competing offer."
        elif risk_level == "high":
            intro = "This candidate shows strong indicators of being at risk."
        elif risk_level == "medium":
            intro = "This candidate has some risk factors that should be monitored."
        else:
            intro = "This candidate appears to be low risk."

        factors_str = ", ".join(primary_factors[:2])

        if risk_level in ["critical", "high"]:
            action_hint = " Immediate action recommended to prevent loss."
        elif risk_level == "medium":
            action_hint = " Consider proactive engagement."
        else:
            action_hint = " Continue normal monitoring."

        return f"{intro} Key factors: {factors_str}.{action_hint}"

    def _generate_recommendations(
        self,
        risk_level: str,
        primary_factors: List[str],
        pipeline_data: Dict[str, Any],
    ) -> List[str]:
        """Generate recommended actions to mitigate risk."""
        actions = []

        if "Time since last contact" in primary_factors:
            actions.append("Reach out to the candidate within 24-48 hours")

        if "Low engagement" in primary_factors:
            actions.append("Send personalized message to re-engage")
            actions.append("Offer additional information about the role")

        if "Time at current stage" in primary_factors:
            actions.append("Accelerate the hiring process")
            actions.append("Schedule next interview within 3 days")

        if "Specialized skills" in primary_factors or "High-demand skills" in primary_factors:
            actions.append("Highlight unique benefits of this position")
            actions.append("Discuss career growth opportunities")

        if "Slow response time" in primary_factors:
            actions.append("Try alternative communication channels")
            actions.append("Check if candidate needs additional information")

        if risk_level == "critical":
            actions.insert(0, "URGENT: Candidate likely considering other offers")
            actions.append("Consider expedited offer process")

        # Default actions if no specific factors
        if not actions:
            actions = ["Continue monitoring candidate engagement"]

        return actions


# Global service instance
_risk_predictor: Optional[RiskPredictor] = None


def get_risk_predictor() -> RiskPredictor:
    """Get or create global risk predictor instance."""
    global _risk_predictor
    if _risk_predictor is None:
        _risk_predictor = RiskPredictor()
    return _risk_predictor
