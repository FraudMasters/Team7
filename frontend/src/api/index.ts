/**
 * API module exports
 *
 * Central exports for the API client and related types.
 */

export { ApiClient, apiClient } from './client';
export { skillGap } from './skillGap';
export { workflowStagesClient, WorkflowStagesClient } from './workflowStages';
export { candidateTagsClient, CandidateTagsClient } from './candidateTags';
export type {
  ResumeUploadResponse,
  AnalysisRequest,
  AnalysisResponse,
  KeywordAnalysis,
  EntityAnalysis,
  GrammarError,
  GrammarAnalysis,
  ExperienceEntry,
  ExperienceAnalysis,
  MatchResponse,
  SkillMatch,
  SkillExperienceVerification,
  JobVacancy,
  ApiError,
  HealthResponse,
  UploadProgressCallback,
  ApiClientConfig,
  SkillGapAnalysisRequest,
  SkillGapAnalysisResponse,
  LearningRecommendationsRequest,
  LearningRecommendationsResponse,
  LearningResource,
  MissingSkillDetail,
  ATSEvaluationRequest,
  ATSEvaluationResponse,
  BatchATSEvaluationRequest,
  BatchATSEvaluationResponse,
  BatchATSResult,
  ATSConfigResponse,
  ATSResult,
  ATSResultListResponse,
  WorkflowStageCreate,
  WorkflowStageUpdate,
  WorkflowStageResponse,
  WorkflowStageListResponse,
  CandidateTagCreate,
  CandidateTagUpdate,
  CandidateTagResponse,
  CandidateTagListResponse,
  AssignTagRequest,
  CandidateTagsResponse,
  CandidateListItem,
  MoveCandidateRequest,
  MoveCandidateResponse,
} from '@/types/api';
