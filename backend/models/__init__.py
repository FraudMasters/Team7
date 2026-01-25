"""
SQLAlchemy database models for Resume Analysis System
"""
from .base import Base
from .resume import Resume
from .analysis_result import AnalysisResult
from .job_vacancy import JobVacancy
from .match_result import MatchResult
from .skill_taxonomy import SkillTaxonomy
from .custom_synonyms import CustomSynonym
from .skill_feedback import SkillFeedback
from .ml_model_version import MLModelVersion

__all__ = [
    "Base",
    "Resume",
    "AnalysisResult",
    "JobVacancy",
    "MatchResult",
    "SkillTaxonomy",
    "CustomSynonym",
    "SkillFeedback",
    "MLModelVersion",
]
