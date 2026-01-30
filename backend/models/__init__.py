"""
SQLAlchemy database models for Resume Analysis System
"""
from .base import Base
from .resume import Resume
from .resume_analysis import ResumeAnalysis
from .analysis_result import AnalysisResult
from .comparison import ResumeComparison
from .job_vacancy import JobVacancy
from .match_result import MatchResult
from .skill_taxonomy import SkillTaxonomy
from .custom_synonyms import CustomSynonym
from .skill_feedback import SkillFeedback
from .ml_model_version import MLModelVersion
from .user_preferences import UserPreferences
from .hiring_stage import HiringStage
from .analytics_event import AnalyticsEvent
from .recruiter import Recruiter
from .report import Report, ScheduledReport

__all__ = [
    "Base",
    "Resume",
    "ResumeAnalysis",
    "AnalysisResult",
    "ResumeComparison",
    "JobVacancy",
    "MatchResult",
    "SkillTaxonomy",
    "CustomSynonym",
    "SkillFeedback",
    "MLModelVersion",
    "UserPreferences",
    "HiringStage",
    "AnalyticsEvent",
    "Recruiter",
    "Report",
    "ScheduledReport",
]
