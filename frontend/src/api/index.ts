/**
 * API module exports
 *
 * Central exports for the API client and related types.
 */

// Base client
export { ApiClient, apiClient } from './client';

// AI/ML services
export { biasReports, BiasReportsClient } from './biasReports';
export { comparisonsClient, ComparisonsClient } from './comparisons';
export { explainability, ExplainabilityClient } from './explainability';
export { fairness, FairnessClient } from './fairness';
export { industryClassifier, IndustryClassifierClient } from './industryClassifier';
export { matchingClient, MatchingClient } from './matching';
export { matchingWeightsClient, MatchingWeightsClient } from './matchingWeights';
export { modelVersionsClient, ModelVersionsClient } from './modelVersions';
export { salaryBenchmarking, SalaryBenchmarkingClient } from './salaryBenchmarking';
export { semanticSearchClient, SemanticSearchClient } from './semanticSearch';
export { skillGap } from './skillGap';
export { skillSuggestions, SkillSuggestionsClient } from './skillSuggestions';
export { skillTaxonomiesClient, SkillTaxonomiesClient } from './skillTaxonomies';

// Analytics & reporting
export { analyticsClient, AnalyticsClient } from './analyticsClient';

// Authentication & security
export * from './auth';
export { gdprClient, GDPRClient } from './gdpr';
export { securityConfigClient, SecurityConfigClient } from './securityConfig';
export { sessionsClient, SessionsClient } from './sessions';
export { ssoClient, SSOClient } from './sso';
export { twoFactorClient, TwoFactorClient } from './twoFactor';

// Candidate management
export { candidatesClient, CandidatesClient } from './candidates';
export { candidateActivitiesClient, CandidateActivitiesClient } from './candidateActivities';
export { candidateNotesClient, CandidateNotesClient } from './candidateNotes';
export { candidateTagsClient, CandidateTagsClient } from './candidateTags';
export { candidateSearchClient, CandidateSearchClient } from './search';

// Job seeker profile management
export { profilesClient, ProfilesClient } from './profiles';

// Communication
export { communicationTemplatesClient, CommunicationTemplatesClient } from './communicationTemplates';
export { communicationsClient, CommunicationsClient } from './communications';
export { emailSyncClient, EmailSyncClient } from './emailSync';
export { smsClient, SMSClient } from './sms';

// Configuration & settings
export { apiKeysClient, APIKeysClient } from './apiKeys';
export { customSynonymsClient, CustomSynonymsClient } from './customSynonyms';
export { pluginsClient, PluginsClient } from './plugins';
export { preferencesClient, PreferencesClient } from './preferences';

// Document processing
export { atsEvaluationClient, AtsEvaluationClient } from './atsEvaluation';
export { resumesClient, ResumesClient } from './resume';
export { parsingCorrectionsClient, ParsingCorrectionsClient } from './parsingCorrections';

// Feedback & learning
export { feedbackClient, FeedbackClient } from './feedback';
export * from './recommendations';

// Health & monitoring
export * from './health';
export * from './notifications';

// Integrations
export { integrationsClient, IntegrationsClient } from './integrations';
export { jobIntegrationsClient, JobIntegrationsClient } from './jobIntegrations';
export { webhooksClient, WebhooksClient } from './webhooks';

// Organization management
export { agenciesClient, AgenciesClient } from './agencies';
export { calendarClient, CalendarClient } from './calendar';
export { clientTenantsClient, ClientTenantsClient } from './clientTenants';
export { interviewsClient, InterviewsClient } from './interviews';
export { jobDescriptionsClient, JobDescriptionsClient } from './jobDescriptions';
export { organizationsClient, OrganizationsClient } from './organizations';
export { teamCommentsClient, TeamCommentsClient } from './teamComments';
export { vacanciesClient, VacanciesClient } from './vacancies';
export { workflowsClient, WorkflowsClient } from './workflows';

// Workflow & search management
export { workflowStagesClient, WorkflowStagesClient } from './workflowStages';
export { savedSearchesClient, SavedSearchesClient } from './savedSearches';
export { searchHistoryClient, SearchHistoryClient } from './searchHistory';

// Taxonomies & classification
export { taxonomiesClient, TaxonomiesClient } from './taxonomies';
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
  ComponentHealthStatus,
  DetailedHealthResponse,
  ReadyCheckResponse,
  ServiceDependencyInfo,
  DependencyGraphSummary,
  DependencyGraphResponse,
  ComponentHealthCheckResponse,
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
  JobSeekerProfile,
  JobSeekerProfileCreate,
  JobSeekerProfileUpdate,
  WorkHistoryItem,
  WorkHistoryCreate,
  WorkHistoryUpdate,
  WorkHistoryListResponse,
  EducationItem,
  EducationCreate,
  EducationUpdate,
  EducationListResponse,
  SkillItem,
  SkillCreate,
  SkillUpdate,
  SkillListResponse,
  EmploymentType,
  DegreeType,
  ProficiencyLevel,
  JobSeekerStatus,
  JobDescriptionGenerateRequest,
  JobDescriptionResponse,
  // Parsing correction types
  SourceTextLocation,
  CorrectionReason,
  CorrectableFieldName,
  ParsingCorrection,
  ParsingCorrectionCreate,
  ParsingCorrectionUpdate,
  ParsingCorrectionResponse,
  ParsingCorrectionsListResponse,
  ParsingCorrectionCreateResponse,
  FieldUpdateRequest,
  FieldUpdateResponse,
  LearningPatternType,
  LearningFeedback,
  LearningFeedbackCreate,
  LearningFeedbackUpdate,
  LearningFeedbackResponse,
  LearningFeedbackListResponse,
  LearningPatternSummary,
  LearningFeedbackSummaryResponse,
  FieldSourceLocation,
  VisualParsingFeedback,
  CorrectionStatistics,
  CorrectionStatisticsResponse,
  CorrectionsQueryParams,
  LearningFeedbackQueryParams,
} from '@/types/api';
