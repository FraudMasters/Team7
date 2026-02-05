/**
 * Экспорты модуля API
 *
 * Централизованные экспорты для API клиента и связанных типов.
 */

export { ApiClient, apiClient } from './client';
export { skillGap } from './skillGap';
export { workflowStagesClient, WorkflowStagesClient } from './workflowStages';
export { candidateTagsClient, CandidateTagsClient } from './candidateTags';
export { candidateNotesClient, CandidateNotesClient } from './candidateNotes';
export { candidateActivitiesClient, CandidateActivitiesClient } from './candidateActivities';
export { savedSearchesClient, SavedSearchesClient } from './savedSearches';
export { searchHistoryClient, SearchHistoryClient } from './searchHistory';
export { candidateSearchClient, CandidateSearchClient } from './search';
export { vacanciesClient, VacanciesClient } from './vacancies';
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
  CandidateNoteCreate,
  CandidateNoteUpdate,
  CandidateNoteResponse,
  CandidateNoteListResponse,
  CandidateListItem,
  MoveCandidateRequest,
  MoveCandidateResponse,
  ActivityItem,
  ActivityTimelineResponse,
  ActivityTypesResponse,
  SavedSearchCreate,
  SavedSearchUpdate,
  SavedSearchResponse,
  SavedSearchListResponse,
  SearchHistoryItem,
  SearchHistoryResponse,
  SearchFilters,
  CandidateSearchRequest,
  CandidateSearchResult,
  CandidateSearchResponse,
  VacancyCreate,
  VacancyUpdate,
  VacancyResponse,
  VacancyListResponse,
  VacancyBulkImportRequest,
  VacancyBulkImportResponse,
} from '@/types/api';
