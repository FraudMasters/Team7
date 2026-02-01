"""
DemographicInference model for storing inferred demographic attributes

This table stores AI-inferred demographic information for bias monitoring:
- Gender predictions
- Age group estimates
- Ethnicity/race classifications
- Geographic indicators
- Confidence scores for each prediction
- Inference metadata and model version
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class DemographicInference(Base, UUIDMixin, TimestampMixin):
    """
    DemographicInference model for storing AI-inferred demographic attributes

    This table stores demographic attributes inferred from resume data using
    AI models, used for bias detection and fairness monitoring in the hiring process.
    All inferences are probabilistic with associated confidence scores.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        analysis_id: Foreign key to ResumeAnalysis (optional)

        # Inferred demographic attributes
        inferred_gender: Predicted gender (male, female, non_binary, unknown)
        gender_confidence: Confidence score for gender prediction (0-1)
        inferred_age_group: Predicted age group (e.g., 25-34, 35-44)
        age_confidence: Confidence score for age prediction (0-1)
        inferred_ethnicity: Predicted ethnicity/race category
        ethnicity_confidence: Confidence score for ethnicity prediction (0-1)
        inferred_geographic_region: Predicted geographic region based on name/location
        geographic_confidence: Confidence score for geographic prediction (0-1)

        # Additional inferences
        inferred_education_level: Predicted education level from text patterns
        education_confidence: Confidence score for education prediction (0-1)
        inferred_career_stage: Predicted career stage (entry, mid, senior, executive)
        career_stage_confidence: Confidence score for career stage prediction (0-1)

        # Raw inference data
        raw_features: JSON object with raw features used for inference
        alternative_predictions: JSON array with alternative predictions and scores
        bias_indicators: JSON array with detected potential bias indicators

        # Processing metadata
        inference_method: Method/model used for inference (e.g., 'nlp_model_v1')
        inference_version: Version of the inference model
        processing_time_seconds: Time taken for inference
        is_manual_override: Whether this was manually verified/overridden
        verified_by: User ID who verified (if manually overridden)
        verification_notes: Notes about manual verification

        # Quality flags
        confidence_threshold_met: Whether all predictions meet minimum threshold
        requires_review: Whether this inference requires human review
        review_status: Status of review (pending, reviewed, rejected, approved)
    """

    __tablename__ = "demographic_inferences"

    # References
    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    analysis_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("resume_analyses.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Core demographic inferences
    inferred_gender: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gender_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    inferred_age_group: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    age_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    inferred_ethnicity: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ethnicity_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    inferred_geographic_region: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    geographic_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Additional inferences
    inferred_education_level: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    education_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    inferred_career_stage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    career_stage_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Raw inference data
    raw_features: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    alternative_predictions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    bias_indicators: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Processing metadata
    inference_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inference_version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Manual verification fields
    is_manual_override: Mapped[bool] = mapped_column(nullable=False, default=False)
    verified_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Quality flags
    confidence_threshold_met: Mapped[Optional[bool]] = mapped_column(nullable=True)
    requires_review: Mapped[Optional[bool]] = mapped_column(nullable=True)
    review_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DemographicInference(id={self.id}, resume_id={self.resume_id}, gender={self.inferred_gender})>"
