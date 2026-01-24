/**
 * API module exports
 *
 * Central exports for the API client and related types.
 */

export { ApiClient, apiClient } from './client';
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
} from '@/types/api';
