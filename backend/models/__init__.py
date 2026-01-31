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
from .model_performance_history import ModelPerformanceHistory
from .model_training_event import ModelTrainingEvent
from .user_preferences import UserPreferences
from .hiring_stage import HiringStage
from .analytics_event import AnalyticsEvent
from .recruiter import Recruiter
from .report import Report, ScheduledReport
from .candidate_rank import CandidateRank, RankingFeedback
from .candidate_tag import CandidateTag
from .candidate_note import CandidateNote
from .candidate_activity import CandidateActivity
from .skill_gap import SkillGapReport
from .learning_resource import LearningResource
from .skill_development_plan import SkillDevelopmentPlan
from .matching_weights import MatchingWeightProfile, MatchingWeightVersion, PRESET_PROFILES, create_preset_profiles
from .backup import Backup, BackupConfig, BackupType, BackupStatus
from .ats_result import ATSResult

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
    "ModelPerformanceHistory",
    "ModelTrainingEvent",
    "UserPreferences",
    "HiringStage",
    "AnalyticsEvent",
    "Recruiter",
    "Report",
    "ScheduledReport",
    "CandidateRank",
    "CandidateTag",
    "CandidateNote",
    "CandidateActivity",
    "RankingFeedback",
    "SkillGapReport",
    "LearningResource",
    "SkillDevelopmentPlan",
    "MatchingWeightProfile",
    "MatchingWeightVersion",
    "PRESET_PROFILES",
    "create_preset_profiles",
    "Backup",
    "BackupConfig",
    "BackupType",
    "BackupStatus",
    "ATSResult",
]
