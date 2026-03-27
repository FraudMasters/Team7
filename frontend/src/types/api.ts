/**
 * API request and response type definitions
 *
 * This module contains TypeScript interfaces for all API communications
 * with the backend resume analysis service.
 */

/**
 * Resume upload response
 */
export interface ResumeUploadResponse {
  id: string;
  filename: string;
  status: string;
  message: string;
}

/**
 * Resume analysis request
 */
export interface AnalysisRequest {
  resume_id: string;
  extract_experience?: boolean;
  check_grammar?: boolean;
}

/**
 * Keyword analysis results
 */
export interface KeywordAnalysis {
  keywords: string[];
  keyphrases: string[];
  scores: number[];
}

/**
 * Entity analysis results
 */
export interface EntityAnalysis {
  organizations: string[];
  dates: string[];
  persons?: string[];
  locations?: string[];
  technical_skills: string[];
}

/**
 * Individual grammar/spelling error
 */
export interface GrammarError {
  type: string;
  severity: string;
  message: string;
  context: string;
  suggestions: string[];
  position: {
    start: number;
    end: number;
  };
}

/**
 * Grammar analysis results
 */
export interface GrammarAnalysis {
  total_errors: number;
  errors_by_category: Record<string, number>;
  errors_by_severity: Record<string, number>;
  errors: GrammarError[];
}

/**
 * Individual work experience entry
 */
export interface ExperienceEntry {
  company: string;
  position: string;
  start_date: string;
  end_date: string | null;
  duration_months: number;
}

/**
 * Experience analysis results
 */
export interface ExperienceAnalysis {
  total_experience_months: number;
  total_experience_summary: string;
  experiences: ExperienceEntry[];
}

/**
 * Resume analysis response
 */
export interface AnalysisResponse {
  resume_id: string;
  filename: string;
  processing_time_seconds: number;
  keywords: KeywordAnalysis;
  entities: EntityAnalysis;
  grammar?: GrammarAnalysis;
  experience?: ExperienceAnalysis;
  language_detected: string;
}

/**
 * Individual skill match result
 */
export interface SkillMatch {
  skill: string;
  status: 'matched' | 'missing';
  highlight: 'green' | 'red';
}

/**
 * Experience verification for a specific skill
 */
export interface SkillExperienceVerification {
  skill: string;
  required_experience_months: number;
  candidate_experience_months: number;
  meets_requirement: boolean;
  projects: Array<{
    company: string;
    position: string;
    duration_months: number;
  }>;
}

/**
 * Job matching response
 */
export interface MatchResponse {
  resume_id: string;
  match_percentage: number;
  matched_skills: SkillMatch[];
  missing_skills: SkillMatch[];
  experience_verification: SkillExperienceVerification[];
  overall_assessment: string;
}

/**
 * Job vacancy data for comparison
 */
export interface JobVacancy {
  uid?: string;
  data: {
    position: string;
    industry?: string;
    mandatory_requirements: string[];
    additional_requirements?: string[];
    experience_levels?: string[];
    project_tasks?: string[];
    project_description?: string[];
  };
}

/**
 * API error response
 */
export interface ApiError {
  detail: string;
  status?: number;
}

/**
 * Health check response
 */
export interface HealthResponse {
  status: string;
  version?: string;
}

/**
 * Component health status
 */
export interface ComponentHealthStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  essential: boolean;
  category: string;
  response_time_ms?: number;
  details?: Record<string, unknown>;
  error?: string | null;
  last_check: string;
}

/**
 * Detailed health check response
 */
export interface DetailedHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  service: string;
  version: string;
  checks: Record<string, ComponentHealthStatus>;
  overall_health_percentage: number;
  critical_issues: string[];
  warnings: string[];
}

/**
 * Ready check response
 */
export interface ReadyCheckResponse {
  status: string;
  checks: Record<string, string>;
}

/**
 * Service dependency information
 */
export interface ServiceDependencyInfo {
  name: string;
  display_name: string;
  description: string;
  essential: boolean;
  category: string;
  dependencies: string[];
  dependents: string[];
}

/**
 * Dependency graph summary
 */
export interface DependencyGraphSummary {
  total_services: number;
  essential_services: number;
  non_essential_services: number;
  max_dependency_depth: number;
  critical_path: string[];
}

/**
 * Dependency graph response
 */
export interface DependencyGraphResponse {
  services: Record<string, ServiceDependencyInfo>;
  summary: DependencyGraphSummary;
}

/**
 * Component health check response
 */
export interface ComponentHealthCheckResponse {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  essential: boolean;
  category: string;
  response_time_ms: number;
  details: Record<string, unknown>;
  error: string | null;
  last_check: string;
}

/**
 * Upload progress callback
 */
export type UploadProgressCallback = (progress: number) => void;

/**
 * API client configuration
 */
export interface ApiClientConfig {
  baseURL?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

/**
 * Skill variant for taxonomy entries
 */
export interface SkillVariant {
  name: string;
  context?: string;
  variants: string[];
  metadata?: Record<string, unknown>;
  is_active: boolean;
}

/**
 * Skill taxonomy create request
 */
export interface SkillTaxonomyCreate {
  industry: string;
  skills: SkillVariant[];
}

/**
 * Skill taxonomy update request
 */
export interface SkillTaxonomyUpdate {
  skill_name?: string;
  context?: string;
  variants?: string[];
  metadata?: Record<string, unknown>;
  is_active?: boolean;
}

/**
 * Skill taxonomy response
 */
export interface SkillTaxonomyResponse {
  id: string;
  industry: string;
  skill_name: string;
  context?: string;
  variants: string[];
  metadata?: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Skill taxonomy list response
 */
export interface SkillTaxonomyListResponse {
  industry: string;
  skills: SkillTaxonomyResponse[];
  total_count: number;
}

/**
 * Custom synonym entry definition
 */
export interface CustomSynonymEntry {
  canonical_skill: string;
  custom_synonyms: string[];
  context?: string;
  is_active: boolean;
}

/**
 * Custom synonym create request
 */
export interface CustomSynonymCreate {
  organization_id: string;
  created_by?: string;
  synonyms: CustomSynonymEntry[];
}

/**
 * Custom synonym update request
 */
export interface CustomSynonymUpdate {
  canonical_skill?: string;
  custom_synonyms?: string[];
  context?: string;
  is_active?: boolean;
}

/**
 * Custom synonym response
 */
export interface CustomSynonymResponse {
  id: string;
  organization_id: string;
  canonical_skill: string;
  custom_synonyms: string[];
  context?: string;
  created_by?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Custom synonym list response
 */
export interface CustomSynonymListResponse {
  organization_id: string;
  synonyms: CustomSynonymResponse[];
  total_count: number;
}

/**
 * Feedback entry definition
 */
export interface FeedbackEntry {
  resume_id: string;
  vacancy_id: string;
  match_result_id?: string;
  skill: string;
  was_correct: boolean;
  confidence_score?: number;
  recruiter_correction?: string;
  actual_skill?: string;
  feedback_source: string;
  metadata?: Record<string, unknown>;
}

/**
 * Feedback create request
 */
export interface FeedbackCreate {
  feedback: FeedbackEntry[];
}

/**
 * Feedback update request
 */
export interface FeedbackUpdate {
  was_correct?: boolean;
  confidence_score?: number;
  recruiter_correction?: string;
  actual_skill?: string;
  processed?: boolean;
  metadata?: Record<string, unknown>;
}

/**
 * Feedback response
 */
export interface FeedbackResponse {
  id: string;
  resume_id: string;
  vacancy_id: string;
  match_result_id?: string;
  skill: string;
  was_correct: boolean;
  confidence_score?: number;
  recruiter_correction?: string;
  actual_skill?: string;
  feedback_source: string;
  processed: boolean;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

/**
 * Feedback list response
 */
export interface FeedbackListResponse {
  feedback: FeedbackResponse[];
  total_count: number;
}

/**
 * Model version entry definition
 */
export interface ModelVersionEntry {
  model_name: string;
  version: string;
  is_active: boolean;
  is_experiment: boolean;
  experiment_config?: Record<string, unknown>;
  model_metadata?: Record<string, unknown>;
  accuracy_metrics?: Record<string, unknown>;
  file_path?: string;
  performance_score?: number;
}

/**
 * Model version create request
 */
export interface ModelVersionCreate {
  models: ModelVersionEntry[];
}

/**
 * Model version update request
 */
export interface ModelVersionUpdate {
  version?: string;
  is_active?: boolean;
  is_experiment?: boolean;
  experiment_config?: Record<string, unknown>;
  model_metadata?: Record<string, unknown>;
  accuracy_metrics?: Record<string, unknown>;
  file_path?: string;
  performance_score?: number;
}

/**
 * Model version response
 */
export interface ModelVersionResponse {
  id: string;
  model_name: string;
  version: string;
  is_active: boolean;
  is_experiment: boolean;
  experiment_config?: Record<string, unknown>;
  model_metadata?: Record<string, unknown>;
  accuracy_metrics?: Record<string, unknown>;
  file_path?: string;
  performance_score?: number;
  created_at: string;
  updated_at: string;
}

/**
 * Model version list response
 */
export interface ModelVersionListResponse {
  models: ModelVersionResponse[];
  total_count: number;
}

/**
 * Match feedback request
 */
export interface MatchFeedbackRequest {
  match_id: string;
  skill: string;
  was_correct: boolean;
  recruiter_correction?: string;
  confidence_score?: number;
  metadata?: Record<string, unknown>;
}

/**
 * Match feedback response
 */
export interface MatchFeedbackResponse {
  id: string;
  match_id: string;
  skill: string;
  was_correct: boolean;
  recruiter_correction?: string;
  feedback_source: string;
  processed: boolean;
  created_at: string;
}

/**
 * Skill match result for comparison
 */
export interface ComparisonSkillMatch {
  skill: string;
  status: 'matched' | 'missing';
  matched_as: string | null;
  highlight: 'green' | 'red';
  confidence: number;
  match_type: string;
}

/**
 * Experience verification for comparison
 */
export interface ComparisonExperienceVerification {
  required_months: number;
  actual_months: number;
  meets_requirement: boolean;
  summary: string;
}

/**
 * Resume comparison result
 */
export interface ResumeComparisonResult {
  rank: number;
  resume_id: string;
  vacancy_title: string;
  match_percentage: number;
  required_skills_match: ComparisonSkillMatch[];
  additional_skills_match: ComparisonSkillMatch[];
  experience_verification: ComparisonExperienceVerification | null;
  processing_time_ms: number;
  error?: string;
}

/**
 * Comparison matrix data response
 */
export interface ComparisonMatrixData {
  vacancy_title: string;
  comparison_results: ResumeComparisonResult[];
  total_resumes: number;
  processing_time_ms: number;
}

/**
 * Comparison create request
 */
export interface ComparisonCreate {
  vacancy_id: string;
  resume_ids: string[];
  name?: string;
  filters?: Record<string, unknown>;
  created_by?: string;
  shared_with?: string[];
}

/**
 * Comparison update request
 */
export interface ComparisonUpdate {
  name?: string;
  filters?: Record<string, unknown>;
  shared_with?: string[];
}

/**
 * Comparison response
 */
export interface ComparisonResponse {
  id: string;
  vacancy_id: string;
  resume_ids: string[];
  name?: string;
  filters?: Record<string, unknown>;
  created_by?: string;
  shared_with?: string[];
  comparison_results?: ResumeComparisonResult[];
  created_at: string;
  updated_at: string;
}

/**
 * Comparison list response
 */
export interface ComparisonListResponse {
  comparisons: ComparisonResponse[];
  total_count: number;
  filters_applied?: {
    vacancy_id?: string;
    created_by?: string;
    min_match_percentage?: number;
    max_match_percentage?: number;
    sort_by?: string;
    order?: string;
  };
}

/**
 * Compare multiple resumes request
 */
export interface CompareMultipleRequest {
  vacancy_id: string;
  resume_ids: string[];
}

// ==================== Analytics Types ====================

/**
 * Time-to-hire metrics from backend
 */
export interface TimeToHireMetrics {
  average_days: number;
  median_days: number;
  min_days: number;
  max_days: number;
  percentile_25: number;
  percentile_75: number;
}

/**
 * Resume processing metrics from backend
 */
export interface ResumeMetrics {
  total_processed: number;
  processed_this_month: number;
  processed_this_week: number;
  processing_rate_avg: number;
}

/**
 * Match rate metrics from backend
 */
export interface MatchRateMetrics {
  overall_match_rate: number;
  high_confidence_matches: number;
  low_confidence_matches: number;
  average_confidence: number;
}

/**
 * Key metrics response from backend
 */
export interface KeyMetricsResponse {
  time_to_hire: TimeToHireMetrics;
  resumes: ResumeMetrics;
  match_rates: MatchRateMetrics;
}

/**
 * Funnel stage interface from backend
 */
export interface FunnelStage {
  stage_name: string;
  count: number;
  conversion_rate: number;
}

/**
 * Funnel metrics response from backend
 */
export interface FunnelMetricsResponse {
  stages: FunnelStage[];
  total_resumes: number;
  overall_hire_rate: number;
}

/**
 * Skill demand item interface from backend
 */
export interface SkillDemandItem {
  skill_name: string;
  demand_count: number;
  demand_percentage: number;
  trend_percentage: number;
}

/**
 * Skill demand response from backend
 */
export interface SkillDemandResponse {
  skills: SkillDemandItem[];
  total_postings_analyzed: number;
}

/**
 * Source tracking item interface from backend
 */
export interface SourceTrackingItem {
  source_name: string;
  vacancy_count: number;
  percentage: number;
  average_time_to_fill: number;
}

/**
 * Source tracking response from backend
 */
export interface SourceTrackingResponse {
  sources: SourceTrackingItem[];
  total_vacancies: number;
}

/**
 * Individual recruiter performance metrics
 */
export interface RecruiterPerformanceItem {
  recruiter_id: string;
  recruiter_name: string;
  hires: number;
  interviews_conducted: number;
  resumes_processed: number;
  average_time_to_hire: number;
  offer_acceptance_rate: number;
  candidate_satisfaction_score: number;
}

/**
 * Recruiter performance response from backend
 */
export interface RecruiterPerformanceResponse {
  recruiters: RecruiterPerformanceItem[];
  total_recruiters: number;
  period_start_date: string;
  period_end_date: string;
}

/**
 * Language preference update request
 */
export interface LanguagePreferenceUpdate {
  language: string;
}

/**
 * Language preference response
 */
export interface LanguagePreferenceResponse {
  language: string;
  updated_at: string;
}

// ==================== Search Analytics Types ====================

/**
 * Search query response from analytics
 */
export interface SearchQueryResponse {
  id: string;
  query: string;
  filters: Record<string, unknown>;
  results_count: number;
  execution_time_ms?: number | null;
  search_type?: string | null;
  created_at: string;
}

/**
 * Recent searches response
 */
export interface RecentSearchesResponse {
  total: number;
  searches: SearchQueryResponse[];
}

/**
 * Popular search response
 */
export interface PopularSearchResponse {
  id: string;
  query: string;
  filters: Record<string, unknown>;
  search_count: number;
  avg_results_count?: number | null;
  avg_click_through_rate?: number | null;
  last_searched_at: string;
}

/**
 * Popular searches response
 */
export interface PopularSearchesResponse {
  total: number;
  searches: PopularSearchResponse[];
}

/**
 * Zero result search response
 */
export interface ZeroResultSearchResponse {
  id: string;
  query: string;
  filters: Record<string, unknown>;
  search_type?: string | null;
  created_at: string;
}

/**
 * Zero result searches response
 */
export interface ZeroResultSearchesResponse {
  total: number;
  searches: ZeroResultSearchResponse[];
}

// ==================== Ranking Types ====================

/**
 * Feature explanation for AI ranking
 */
export interface FeatureExplanation {
  feature_name: string;
  contribution: number;
  contribution_percentage: number;
  direction: 'positive' | 'negative';
  description: string;
  value?: number;
}

/**
 * Ranked candidate from AI ranking
 */
export interface RankedCandidate {
  resume_id: string;
  candidate_name: string;
  ranking_score: number;
  hire_probability: number;
  match_score: number;
  overall_score: number;
  recommendation: 'excellent' | 'good' | 'fair';
  explanation: {
    summary: string;
    top_positive_factors: FeatureExplanation[];
    top_negative_factors: FeatureExplanation[];
    feature_contributions: Record<string, number>;
    percentile_rank?: number | null;
    percentile_explanation?: string;
  };
  is_top_recommendation: boolean;
  is_experiment?: boolean;
  experiment_group?: 'control' | 'treatment';
  model_version?: string;
}

/**
 * Ranking request
 */
export interface RankingRequest {
  vacancy_id: string;
  limit?: number;
}

/**
 * Ranking response
 */
export interface RankingResponse {
  vacancy_id: string;
  ranked_candidates: RankedCandidate[];
  total_candidates: number;
  model_version: string;
  processing_time_ms: number;
}

/**
 * Recommendations response (top 3 candidates)
 */
export interface RecommendationsResponse {
  vacancy_id: string;
  top_candidates: RankedCandidate[];
  total_candidates_considered: number;
  model_version: string;
  generated_at: string;
}

/**
 * Ranking feedback request
 */
export interface RankingFeedbackRequest {
  rank_id?: string;
  resume_id: string;
  vacancy_id: string;
  was_correct: boolean;
  recruiter_corrected_score?: number;
  recruiter_corrected_position?: number;
  feedback_reason?: string;
  recruiter_comments?: string;
}

/**
 * Ranking feedback response
 */
export interface RankingFeedbackResponse {
  id: string;
  resume_id: string;
  vacancy_id: string;
  candidate_rank_id?: string;
  was_correct: boolean;
  original_score: number;
  recruiter_corrected_score?: number;
  original_position: number;
  corrected_position?: number;
  feedback_reason?: string;
  feedback_source: string;
  processed: boolean;
  created_at: string;
}

// ==================== Industry Classifier Types ====================

/**
 * Industry classification request
 */
export interface IndustryClassificationRequest {
  title: string;
  description: string;
}

/**
 * Industry match result
 */
export interface IndustryMatch {
  industry: string;
  confidence: number;
}

/**
 * Industry classification response
 */
export interface IndustryClassificationResponse {
  industry: string;
  confidence: number;
  all_matches: IndustryMatch[];
  keywords_matched: Record<string, string[]>;
}

// ==================== Skill Suggestions Types ====================

/**
 * Skill suggestion request
 */
export interface SkillSuggestionRequest {
  industry: string;
  title: string;
  description?: string;
  limit?: number;
}

/**
 * Suggested skill item
 */
export interface SkillSuggestionItem {
  skill_name: string;
  context?: string;
  variants: string[];
  relevance_score: number;
  category?: string;
  is_industry_specific?: boolean;
}

/**
 * Skill suggestion response
 */
export interface SkillSuggestionResponse {
  industry: string;
  job_title: string;
  suggestions: SkillSuggestionItem[];
  total_count: number;
}

// ==================== Skill Gap Analysis Types ====================

/**
 * Missing skill detail
 */
export interface MissingSkillDetail {
  status: 'missing' | 'partial';
  required_level: string;
  importance: 'high' | 'medium' | 'low';
  category: string;
}

/**
 * Skill gap analysis request
 */
export interface SkillGapAnalysisRequest {
  resume_id: string;
  vacancy_data: {
    id: string;
    title: string;
    description?: string;
    required_skills: string[];
    required_skill_levels?: Record<string, string>;
    required_experience_years?: number;
    required_education?: string[];
  };
}

/**
 * Skill gap analysis response
 */
export interface SkillGapAnalysisResponse {
  report_id: string;
  resume_id: string;
  vacancy_id: string | null;
  vacancy_title: string;
  candidate_skills: string[];
  required_skills: string[];
  matched_skills: string[];
  missing_skills: string[];
  partial_match_skills: string[];
  missing_skill_details: Record<string, MissingSkillDetail>;
  gap_severity: 'critical' | 'moderate' | 'minimal' | 'none';
  gap_percentage: number;
  bridgeability_score: number;
  estimated_time_to_bridge: number;
  priority_ordering: string[];
  processing_time_ms: number;
}

/**
 * Learning resource item
 */
export interface LearningResource {
  id?: string;
  skill: string;
  resource_type: 'course' | 'certification' | 'book' | 'tutorial' | 'video' | 'bootcamp' | 'workshop' | 'other';
  title: string;
  description: string;
  provider?: string;
  url?: string;
  skill_level?: string;
  topics_covered?: string[];
  prerequisites?: string[];
  language?: string;
  is_self_paced: boolean;
  duration_hours?: number;
  duration_weeks?: number;
  cost_amount?: number;
  currency?: string;
  access_type: 'free' | 'paid' | 'subscription' | 'freemium';
  rating?: number;
  rating_count?: number;
  certificate_offered: boolean;
  difficulty_level?: number;
  relevance_score: number;
  quality_score: number;
  priority_score: number;
}

/**
 * Learning recommendations request
 */
export interface LearningRecommendationsRequest {
  skills: string[];
  skill_levels?: Record<string, string>;
  max_recommendations_per_skill?: number;
  max_cost_per_resource?: number | null;
  include_free_resources?: boolean;
  min_rating?: number;
  preferred_languages?: string[];
}

/**
 * Learning recommendations response
 */
export interface LearningRecommendationsResponse {
  target_skills: string[];
  recommendations: Record<string, LearningResource[]>;
  total_recommendations: number;
  total_cost: number;
  total_duration_hours: number;
  alternative_free_resources: number;
  skills_with_certifications: string[];
  priority_ordering: string[];
  summary: string;
}

/**
 * Skill gap report list response
 */
export interface SkillGapReportListResponse {
  reports: Array<{
    id: string;
    resume_id: string;
    vacancy_id: string;
    created_at: string;
    gap_severity: string;
    gap_percentage: number;
  }>;
  total_count: number;
}

/**
 * Learning resources query params
 */
export interface LearningResourcesQuery {
  skill?: string;
  resource_type?: string;
  skill_level?: string;
  access_type?: string;
  min_rating?: number;
  max_cost?: number;
  limit?: number;
  offset?: number;
}

/**
 * Learning resources list response
 */
export interface LearningResourcesListResponse {
  resources: LearningResource[];
  total_count: number;
  filters_applied: Record<string, unknown>;
}

// ==================== Matching Weights Types ====================

/**
 * Matching weight profile response
 */
export interface MatchingWeightsProfile {
  id: string;
  name: string;
  description: string | null;
  organization_id: string | null;
  vacancy_id: string | null;
  is_preset: boolean;
  is_active: boolean;
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  weights_percentage: {
    keyword: number;
    tfidf: number;
    vector: number;
  };
  version: string | null;
  created_at: string;
  updated_at: string;
  created_by: string | null;
  updated_by: string | null;
}

/**
 * Create matching weight profile request
 */
export interface MatchingWeightsCreate {
  name: string;
  description?: string;
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  organization_id?: string;
  vacancy_id?: string;
  change_reason?: string;
}

/**
 * Update matching weight profile request
 */
export interface MatchingWeightsUpdate {
  name?: string;
  description?: string;
  keyword_weight?: number;
  tfidf_weight?: number;
  vector_weight?: number;
  is_active?: boolean;
  change_reason?: string;
}

/**
 * List matching weight profiles response
 */
export interface MatchingWeightsListResponse {
  profiles: MatchingWeightsProfile[];
  total_count: number;
  preset_count: number;
  custom_count: number;
}

/**
 * Preset profile response
 */
export interface PresetProfile {
  name: string;
  description: string;
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  weights_percentage: {
    keyword: number;
    tfidf: number;
    vector: number;
  };
  use_case: string;
}

/**
 * Preset profiles response
 */
export interface PresetsResponse {
  presets: PresetProfile[];
}

/**
 * Version history entry
 */
export interface WeightVersionEntry {
  id: string;
  version: string;
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  changed_by: string | null;
  change_reason: string | null;
  created_at: string;
}

/**
 * Version history response
 */
export interface VersionHistoryResponse {
  versions: WeightVersionEntry[];
  total_count: number;
}

/**
 * Normalize weights request
 */
export interface NormalizeWeightsRequest {
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
}

/**
 * Normalized weights response
 */
export interface NormalizedWeightsResponse {
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  original_sum: number;
  normalized: boolean;
}

/**
 * Apply weights request
 */
export interface ApplyWeightsRequest {
  vacancy_id: string;
  profile_id?: string;
  weights?: MatchingWeightsUpdate;
  re_match_candidates: boolean;
}

/**
 * Apply weights response
 */
export interface ApplyWeightsResponse {
  vacancy_id: string;
  weights_applied: {
    keyword_weight: number;
    tfidf_weight: number;
    vector_weight: number;
  };
  profile_used: string | null;
  candidates_affected: number;
  processing_time_ms: number;
}

// ==================== Backup Types ====================

/**
 * Backup entry
 */
export interface Backup {
  id: string;
  name: string;
  type: 'database' | 'files' | 'models' | 'full';
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'expired' | 'restoring';
  size_bytes: number | null;
  size_human: string | null;
  backup_path: string;
  created_at: string;
  completed_at: string | null;
  retention_days: number;
  expires_at: string | null;
  checksum: string | null;
  is_incremental: boolean;
  parent_backup_id: string | null;
  s3_uploaded: boolean;
  s3_key: string | null;
  error_message: string | null;
  files_count: number | null;
  tables_count: number | null;
}

/**
 * Backup create request
 */
export interface BackupCreate {
  name: string;
  type: 'database' | 'files' | 'models' | 'full';
  retention_days: number;
  is_incremental: boolean;
  upload_to_s3: boolean;
}

/**
 * Backup restore request
 */
export interface BackupRestoreRequest {
  restore_type: 'full' | 'database' | 'files' | 'models' | null;
  confirm: boolean;
  create_backup_before: boolean;
}

/**
 * Backup configuration
 */
export interface BackupConfig {
  retention_days: number;
  backup_schedule: string;
  s3_enabled: boolean;
  s3_bucket: string | null;
  s3_endpoint: string | null;
  s3_region: string | null;
  notification_email: string | null;
  enabled: boolean;
  incremental_enabled: boolean;
  compression_enabled: boolean;
  last_backup_at: string | null;
  last_backup_status: string | null;
}

/**
 * Backup configuration update request
 */
export interface BackupConfigUpdate {
  retention_days?: number;
  backup_schedule?: string;
  s3_enabled?: boolean;
  s3_bucket?: string;
  s3_endpoint?: string;
  s3_access_key?: string;
  s3_secret_key?: string;
  s3_region?: string;
  notification_email?: string;
  enabled?: boolean;
  incremental_enabled?: boolean;
  compression_enabled?: boolean;
}

/**
 * Backup status response
 */
export interface BackupStatus {
  enabled: boolean;
  last_backup_at: string | null;
  last_backup_status: string | null;
  total_backups: number;
  total_size_bytes: number;
  total_size_human: string;
  next_scheduled_backup: string | null;
  recent_backups: Backup[];
  disk_usage_bytes: number | null;
  disk_usage_human: string | null;
}

/**
 * Backup verification response
 */
export interface BackupVerifyResponse {
  backup_id: string;
  valid: boolean;
  checksum_match: boolean;
  files_intact: boolean;
  details: string | null;
}

/**
 * S3 configuration
 */
export interface S3Config {
  enabled: boolean;
  bucket: string | null;
  endpoint: string | null;
  access_key: string | null;
  secret_key: string | null;
  region: string;
}

// ==================== ATS Simulation Types ====================

/**
 * ATS evaluation request
 */
export interface ATSEvaluationRequest {
  resume_id: string;
  vacancy_id: string;
  use_llm?: boolean;
}

/**
 * ATS evaluation response
 */
export interface ATSEvaluationResponse {
  resume_id: string;
  vacancy_id: string;
  passed: boolean;
  overall_score: number;
  keyword_score: number;
  experience_score: number;
  education_score: number;
  fit_score: number;
  looks_professional: boolean;
  disqualified: boolean;
  visual_issues: string[];
  ats_issues: string[];
  missing_keywords: string[];
  suggestions: string[];
  feedback: string;
  provider: string;
  model: string;
  processing_time_ms: number;
}

/**
 * Batch ATS evaluation request
 */
export interface BatchATSEvaluationRequest {
  vacancy_id: string;
  resume_ids: string[];
  use_llm?: boolean;
}

/**
 * Batch ATS evaluation result for a single resume
 */
export interface BatchATSResult {
  resume_id: string;
  passed?: boolean;
  overall_score?: number;
  keyword_score?: number;
  experience_score?: number;
  education_score?: number;
  fit_score?: number;
  looks_professional?: boolean;
  disqualified?: boolean;
  visual_issues?: string[];
  ats_issues?: string[];
  missing_keywords?: string[];
  suggestions?: string[];
  feedback?: string;
  provider?: string;
  model?: string;
  error?: string;
}

/**
 * Batch ATS evaluation response
 */
export interface BatchATSEvaluationResponse {
  vacancy_id: string;
  results: BatchATSResult[];
  total_count: number;
  passed_count: number;
  processing_time_ms: number;
}

/**
 * ATS configuration response
 */
export interface ATSConfigResponse {
  llm_configured: boolean;
  provider: string;
  model: string;
  threshold: number;
  weights: {
    keyword: number;
    experience: number;
    education: number;
    fit: number;
  };
  visual_check_enabled: boolean;
}

/**
 * Cached ATS result from database
 */
export interface ATSResult {
  id: string;
  resume_id: string;
  vacancy_id: string;
  passed: boolean;
  overall_score: number;
  keyword_score: number | null;
  experience_score: number | null;
  education_score: number | null;
  fit_score: number | null;
  looks_professional: boolean;
  disqualified: boolean;
  visual_issues: Record<string, unknown> | null;
  ats_issues: Record<string, unknown> | null;
  missing_keywords: Record<string, unknown> | null;
  suggestions: Record<string, unknown> | null;
  feedback: string | null;
  provider: string | null;
  model: string | null;
  raw_response: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * ATS result list response
 */
export interface ATSResultListResponse {
  results: ATSResult[];
  total_count: number;
}

// ==================== Workflow Stages Types ====================

/**
 * Workflow stage create request
 */
export interface WorkflowStageCreate {
  organization_id: string;
  stage_name: string;
  stage_order: number;
  is_default?: boolean;
  is_active?: boolean;
  color?: string;
  description?: string;
}

/**
 * Workflow stage update request
 */
export interface WorkflowStageUpdate {
  stage_name?: string;
  stage_order?: number;
  is_default?: boolean;
  is_active?: boolean;
  color?: string;
  description?: string;
}

/**
 * Workflow stage response
 */
export interface WorkflowStageResponse {
  id: string;
  organization_id: string;
  stage_name: string;
  stage_order: number;
  is_default: boolean;
  is_active: boolean;
  color: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Workflow stage list response
 */
export interface WorkflowStageListResponse {
  organization_id: string;
  stages: WorkflowStageResponse[];
  total_count: number;
}

// ==================== Candidate Tags Types ====================

/**
 * Candidate tag (base interface for frontend usage)
 */
export interface CandidateTag {
  id: string;
  organization_id: string;
  tag_name: string;
  tag_order: number;
  is_default: boolean;
  is_active: boolean;
  color: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Candidate tag create request
 */
export interface CandidateTagCreate {
  organization_id: string;
  tag_name: string;
  tag_order?: number;
  is_default?: boolean;
  is_active?: boolean;
  color?: string;
  description?: string;
}

/**
 * Candidate tag update request
 */
export interface CandidateTagUpdate {
  tag_name?: string;
  tag_order?: number;
  is_default?: boolean;
  is_active?: boolean;
  color?: string;
  description?: string;
}

/**
 * Candidate tag response
 */
export interface CandidateTagResponse {
  id: string;
  organization_id: string;
  tag_name: string;
  tag_order: number;
  is_default: boolean;
  is_active: boolean;
  color: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Candidate tag list response
 */
export interface CandidateTagListResponse {
  organization_id: string;
  tags: CandidateTagResponse[];
  total_count: number;
}

/**
 * Assign tag request
 */
export interface AssignTagRequest {
  tag_id: string;
  recruiter_id?: string;
}

/**
 * Candidate tags response (tags assigned to a resume)
 */
export interface CandidateTagsResponse {
  resume_id: string;
  tags: CandidateTagResponse[];
  total_count: number;
}

/**
 * Tag suggestion item
 */
export interface TagSuggestionItem {
  id: string;
  tag_name: string;
  color: string | null;
  usage_count: number;
}

/**
 * Tag suggestions response
 */
export interface TagSuggestionsResponse {
  organization_id: string;
  suggestions: TagSuggestionItem[];
  total_count: number;
}

/**
 * Merge tags request
 */
export interface MergeTagsRequest {
  source_tag_id: string;
  target_tag_id: string;
}

/**
 * Merge tags response
 */
export interface MergeTagsResponse {
  message: string;
  source_tag_id: string;
  target_tag_id: string;
  candidates_transferred: number;
}

/**
 * Intelligent tag suggestion with relevance score
 */
export interface IntelligentTagSuggestion {
  id: string;
  organization_id: string;
  tag_name: string;
  tag_order: number;
  is_default: boolean;
  is_active: boolean;
  color: string | null;
  description: string | null;
  relevance_score: number;
}

/**
 * Intelligent tag suggestions response
 */
export interface IntelligentTagSuggestionResponse {
  organization_id: string;
  resume_id: string;
  suggestions: IntelligentTagSuggestion[];
  keywords_extracted: string[];
  total_count: number;
}

// ==================== Candidates Types ====================

/**
 * Tag information assigned to a candidate
 */
export interface TagInfo {
  id: string;
  tag_name: string;
  color: string | null;
  organization_id: string;
}

/**
 * Latest activity information for a candidate
 */
export interface LatestActivityInfo {
  activity_type: string;
  created_at: string;
}

/**
 * Candidate list item
 */
export interface CandidateListItem {
  id: string;
  filename: string;
  current_stage: string;
  stage_name: string;
  vacancy_id: string | null;
  created_at: string;
  updated_at: string;
  notes: string | null;
  tags: TagInfo[];
  notes_count: number;
  latest_activity: LatestActivityInfo | null;
}

/**
 * Move candidate request
 */
export interface MoveCandidateRequest {
  stage_id: string;
  vacancy_id?: string;
  notes?: string;
}

/**
 * Move candidate response
 */
export interface MoveCandidateResponse {
  id: string;
  resume_id: string;
  previous_stage: string;
  new_stage: string;
  message: string;
}

/**
 * Stage duration analytics metrics
 */
export interface StageDurationMetrics {
  stage_name: string;
  average_days: number;
  median_days: number;
  min_days: number;
  max_days: number;
  candidate_count: number;
}

/**
 * Stage duration analytics response
 */
export interface StageDurationResponse {
  stages: StageDurationMetrics[];
}

// ==================== Candidate Notes Types ====================

/**
 * Candidate note (base interface for frontend usage)
 */
export interface CandidateNote {
  id: string;
  resume_id: string;
  recruiter_id: string | null;
  content: string;
  is_private: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Candidate note create request
 */
export interface CandidateNoteCreate {
  resume_id: string;
  recruiter_id?: string;
  content: string;
  is_private?: boolean;
}

/**
 * Candidate note update request
 */
export interface CandidateNoteUpdate {
  content?: string;
  is_private?: boolean;
}

/**
 * Candidate note response
 */
export interface CandidateNoteResponse {
  id: string;
  resume_id: string;
  recruiter_id: string | null;
  content: string;
  is_private: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Candidate note list response
 */
export interface CandidateNoteListResponse {
  resume_id: string;
  notes: CandidateNoteResponse[];
  total_count: number;
}

// ==================== Candidate Activities Types ====================

/**
 * Candidate activity (base interface for frontend usage)
 */
export interface CandidateActivity {
  id: string;
  activity_type: string;
  candidate_id: string;
  vacancy_id: string | null;
  from_stage: string | null;
  to_stage: string | null;
  note_id: string | null;
  tag_id: string | null;
  recruiter_id: string | null;
  activity_data: Record<string, unknown> | null;
  reason: string | null;
  created_at: string;
}

/**
 * Single activity item in the timeline
 */
export interface ActivityItem {
  id: string;
  activity_type: string;
  candidate_id: string;
  vacancy_id: string | null;
  from_stage: string | null;
  to_stage: string | null;
  note_id: string | null;
  tag_id: string | null;
  recruiter_id: string | null;
  activity_data: Record<string, unknown> | null;
  reason: string | null;
  created_at: string;
}

/**
 * Response model for candidate activity timeline
 */
export interface ActivityTimelineResponse {
  resume_id: string;
  activities: ActivityItem[];
  total_count: number;
}

/**
 * Response model for available activity types
 */
export interface ActivityTypesResponse {
  activity_types: string[];
}

// ==================== Filter Suggestions Types ====================

/**
 * Source of a filter suggestion
 */
export type FilterSuggestionSource = 'extracted' | 'inferred' | 'synonym' | 'provided';

/**
 * Single suggested filter item with confidence scoring
 */
export interface SuggestedFilterItem {
  /** Type of filter (skills, location, education_level, languages) */
  filter_type: string;
  /** The filter value (string, array, number, or boolean) */
  value: string | string[] | number | boolean;
  /** Confidence score (0.0-1.0) */
  confidence: number;
  /** Source of suggestion */
  source: FilterSuggestionSource;
  /** Original text from JD that led to this suggestion */
  original_text?: string;
}

/**
 * Request for JD filter suggestions
 */
export interface FilterSuggestionRequest {
  /** Job description text to analyze for filter suggestions */
  job_description: string;
  /** Maximum number of skills to suggest (1-50) */
  max_skills?: number;
  /** Minimum confidence threshold for suggestions (0.0-1.0) */
  min_confidence?: number;
}

/**
 * Request for structured vacancy filter suggestions
 */
export interface VacancyFilterRequest {
  /** Job title */
  title?: string;
  /** Job description text */
  description?: string;
  /** List of required skills from vacancy */
  skills?: string[];
  /** List of additional requirements */
  requirements?: string[];
}

/**
 * Response from filter suggestions API
 */
export interface FilterSuggestionResponse {
  /** List of suggested skill filters with confidence scores */
  skills: SuggestedFilterItem[];
  /** Suggested minimum years of experience */
  min_experience_years: number | null;
  /** Suggested maximum years of experience */
  max_experience_years: number | null;
  /** Detected seniority level (entry, mid, senior, lead, executive) */
  seniority_level: string | null;
  /** Suggested location filter */
  location: SuggestedFilterItem | null;
  /** Suggested education level filter */
  education_level: SuggestedFilterItem | null;
  /** List of suggested language filters */
  languages: SuggestedFilterItem[];
  /** Combined list of all suggested filters sorted by confidence */
  all_filters: SuggestedFilterItem[];
  /** Overall confidence in the suggestions (0.0-1.0) */
  confidence: number;
  /** Time taken to analyze the job description */
  analysis_time_seconds: number;
  /** Ready-to-use filters dictionary for search API */
  search_filters: Record<string, unknown>;
}

// ==================== Alert Settings Types ====================

/**
 * Alert frequency options
 */
export type AlertFrequency = 'realtime' | 'daily' | 'weekly';

/**
 * Alert settings update request
 */
export interface AlertSettingsUpdate {
  /** Enable or disable alerts for this saved search */
  alert_enabled?: boolean;
  /** Frequency of alerts */
  alert_frequency?: AlertFrequency;
}

/**
 * Alert settings response
 */
export interface AlertSettingsResponse {
  /** Saved search UUID */
  id: string;
  /** Saved search name */
  name: string;
  /** Whether alerts are enabled */
  alert_enabled: boolean;
  /** Frequency of alerts (realtime, daily, weekly) */
  alert_frequency: string | null;
  /** ISO timestamp when last alert was sent */
  last_alert_at: string | null;
}

/**
 * Alert settings list response
 */
export interface AlertSettingsListResponse {
  /** Total number of saved searches with alerts */
  total: number;
  /** Number of saved searches with alerts enabled */
  alerts_enabled_count: number;
  /** List of alert settings for saved searches */
  alert_settings: AlertSettingsResponse[];
}

/**
 * Apply saved search response (one-click apply)
 */
export interface ApplySearchResponse {
  /** UUID of the applied saved search */
  saved_search_id: string;
  /** Name of the saved search */
  saved_search_name: string;
  /** Total number of matching candidates */
  total: number;
  /** List of candidate results */
  candidates: Array<Record<string, unknown>>;
  /** Search query that was executed */
  query: string;
  /** Filters that were applied */
  filters_applied: Record<string, unknown>;
  /** Time taken to execute search */
  execution_time_seconds: number;
}

// ==================== Saved Searches Types ====================

/**
 * Saved search create request
 */
export interface SavedSearchCreate {
  name: string;
  query: string;
  filters?: Record<string, unknown>;
}

/**
 * Saved search update request
 */
export interface SavedSearchUpdate {
  name?: string;
  query?: string;
  filters?: Record<string, unknown>;
}

/**
 * Saved search response
 */
export interface SavedSearchResponse {
  id: string;
  name: string;
  query: string;
  filters: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

/**
 * Saved search list response
 */
export interface SavedSearchListResponse {
  total: number;
  saved_searches: SavedSearchResponse[];
}

/**
 * Request for creating a saved search with optional alert settings
 */
export interface SavedSearchWithAlertsCreate {
  /** User-provided name for the saved search */
  name: string;
  /** Search query string with boolean operators */
  query: string;
  /** Filter settings (skills, experience_years, location, etc.) */
  filters?: Record<string, unknown>;
  /** Whether to enable alerts for this saved search */
  alert_enabled?: boolean;
  /** Frequency of alerts if enabled */
  alert_frequency?: AlertFrequency;
}

/**
 * Request for updating a saved search with alert settings
 */
export interface SavedSearchWithAlertsUpdate {
  /** Updated name for the saved search */
  name?: string;
  /** Updated search query string */
  query?: string;
  /** Updated filter settings */
  filters?: Record<string, unknown>;
  /** Enable or disable alerts */
  alert_enabled?: boolean;
  /** Updated frequency of alerts */
  alert_frequency?: AlertFrequency;
}

/**
 * Response for a saved search including alert settings
 */
export interface SavedSearchWithAlertsResponse {
  /** Saved search UUID */
  id: string;
  /** Saved search name */
  name: string;
  /** Search query string */
  query: string;
  /** Filter settings */
  filters: Record<string, unknown>;
  /** Whether alerts are enabled for this saved search */
  alert_enabled: boolean;
  /** Frequency of alerts if enabled */
  alert_frequency: string | null;
  /** Timestamp when last alert was sent */
  last_alert_at: string | null;
  /** Creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
}

/**
 * Response for listing saved searches with alert settings
 */
export interface SavedSearchListWithAlertsResponse {
  /** Total number of saved searches */
  total: number;
  /** Number of saved searches with alerts enabled */
  alerts_enabled_count: number;
  /** List of saved searches with alert settings */
  saved_searches: SavedSearchWithAlertsResponse[];
}

/**
 * Request for updating alert settings on multiple saved searches
 */
export interface BulkAlertSettingsUpdate {
  /** List of saved search UUIDs to update */
  saved_search_ids: string[];
  /** Enable or disable alerts for all specified saved searches */
  alert_enabled?: boolean;
  /** Set alert frequency for all specified saved searches */
  alert_frequency?: AlertFrequency;
}

/**
 * Response for bulk alert settings update
 */
export interface BulkAlertSettingsResponse {
  /** Number of saved searches updated */
  updated_count: number;
  /** Number of saved searches that failed to update */
  failed_count: number;
  /** List of successfully updated alert settings */
  updated: AlertSettingsResponse[];
  /** List of failed updates with error details */
  failed: Array<{ id: string; error: string }>;
}

// ==================== Candidate Search Types ====================

/**
 * Search filter configuration for candidate search
 */
export interface SearchFilters {
  skills?: string[];
  min_experience_years?: number;
  max_experience_years?: number;
  location?: string;
  education_level?: string;
  languages?: string[];
  min_match_score?: number;
  max_match_score?: number;
  date_from?: string;
  date_to?: string;
  vacancy_id?: string;
  stage_id?: string;
}

/**
 * Candidate search request
 */
export interface CandidateSearchRequest {
  query?: string | null;
  filters?: SearchFilters | null;
  skip?: number;
  limit?: number;
  sort_by?: string;
}

/**
 * Single candidate search result
 */
export interface CandidateSearchResult {
  id: string;
  filename: string;
  status: string;
  created_at: string;
  updated_at: string;
  current_stage: string;
  vacancy_id: string | null;
  skills: string[];
  total_experience_months: number | null;
  experience_years: number | null;
  education: Array<Record<string, unknown>>;
  language: string | null;
  quality_score: number | null;
}

/**
 * Candidate search response
 */
export interface CandidateSearchResponse {
  total: number;
  candidates: Array<Record<string, unknown>>;
  query: string;
  filters_applied: Record<string, unknown>;
  execution_time_seconds: number;
  skip: number;
  limit: number;
}

// ==================== Search History Types ====================

/**
 * Search history item
 */
export interface SearchHistoryItem {
  id: string;
  query: string | null;
  filters: Record<string, unknown>;
  results_count: number | null;
  execution_time_seconds: number | null;
  created_at: string;
  recruiter_id: string | null;
}

/**
 * Search history response
 */
export interface SearchHistoryResponse {
  total: number;
  history: SearchHistoryItem[];
  skip: number;
  limit: number;
}

// ==================== Auth Types ====================

/**
 * User role enum for registration
 */
export type UserRole = 'admin' | 'hiring_manager' | 'job_seeker' | 'recruiter' | 'viewer';

/**
 * Registration request with optional role for job seeker support
 */
export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
  role?: UserRole;
}

/**
 * Registration response
 */
export interface RegisterResponse {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  message: string;
}

/**
 * Login request
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Basic user information
 */
export interface UserInfo {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
}

/**
 * Login response
 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserInfo;
}

/**
 * Token refresh request
 */
export interface RefreshTokenRequest {
  refresh_token: string;
}

/**
 * Token refresh response
 */
export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

/**
 * Logout request
 */
export interface LogoutRequest {
  refresh_token: string;
}

/**
 * Logout response
 */
export interface LogoutResponse {
  message: string;
}

/**
 * Password reset request
 */
export interface PasswordResetRequest {
  email: string;
}

/**
 * Password reset request response
 */
export interface PasswordResetRequestResponse {
  message: string;
}

/**
 * Password reset confirmation request
 */
export interface PasswordResetConfirmRequest {
  token: string;
  new_password: string;
}

/**
 * Password reset confirmation response
 */
export interface PasswordResetConfirmResponse {
  message: string;
}

/**
 * Request email verification request
 */
export interface RequestEmailVerificationRequest {
  email: string;
}

/**
 * Request email verification response
 */
export interface RequestEmailVerificationResponse {
  message: string;
}

/**
 * Verify email request
 */
export interface VerifyEmailRequest {
  token: string;
}

/**
 * Verify email response
 */
export interface VerifyEmailResponse {
  message: string;
}

/**
 * Auth error response
 */
export interface AuthErrorResponse {
  error: string;
  detail: string;
  type: string;
}

// ==================== Job Search Types ====================

/**
 * Filters for job search
 */
export interface JobSearchFilters {
  /** Location filter (partial match) */
  location?: string;
  /** Minimum salary */
  salary_min?: number;
  /** Maximum salary */
  salary_max?: number;
  /** Work format: remote, office, hybrid */
  work_format?: 'remote' | 'office' | 'hybrid';
  /** Employment type: full-time, part-time, contract */
  employment_type?: 'full-time' | 'part-time' | 'contract';
  /** Industry sector */
  industry?: string;
  /** List of required skills (OR logic) */
  skills?: string[];
}

/**
 * Job search request
 */
export interface JobSearchRequest {
  /** Search query for job title and description */
  query?: string | null;
  /** Filter criteria */
  filters?: JobSearchFilters | null;
  /** Number of records to skip (pagination) */
  skip?: number;
  /** Maximum number of records to return */
  limit?: number;
  /** Sort field: date, salary_asc, salary_desc, relevance */
  sort_by?: 'date' | 'salary_asc' | 'salary_desc' | 'relevance';
}

/**
 * Job search result item
 */
export interface JobSearchResult {
  /** Job vacancy ID */
  id: string;
  /** Job title */
  title: string;
  /** Job description */
  description: string;
  /** Required technical skills */
  required_skills: string[];
  /** Minimum experience in months */
  min_experience_months: number | null;
  /** Additional skills */
  additional_requirements: string[];
  /** Industry */
  industry: string | null;
  /** Work format */
  work_format: string | null;
  /** Location */
  location: string | null;
  /** Minimum salary */
  salary_min: number | null;
  /** Maximum salary */
  salary_max: number | null;
  /** English level */
  english_level: string | null;
  /** Employment type */
  employment_type: string | null;
  /** Creation timestamp */
  created_at: string;
}

/**
 * Job search response
 */
export interface JobSearchResponse {
  /** Total number of matching jobs */
  total: number;
  /** List of job results */
  jobs: JobSearchResult[];
  /** Search query that was executed */
  query: string;
  /** Filters that were applied */
  filters_applied: Record<string, unknown>;
  /** Time taken to execute search in seconds */
  execution_time_seconds: number;
  /** Number of results skipped */
  skip: number;
  /** Maximum number of results returned */
  limit: number;
}

// ==================== Job Applications Types ====================

/**
 * Job application status enum
 */
export type JobApplicationStatus = 'pending' | 'submitted' | 'under_review' | 'rejected' | 'accepted';

/**
 * Job application submit request
 */
export interface JobApplicationSubmitRequest {
  /** ID of the vacancy to apply for */
  vacancy_id: string;
  /** ID of the resume to submit (optional) */
  resume_id?: string;
  /** Contact email */
  email: string;
  /** Contact phone number */
  phone?: string;
  /** Cover letter text */
  cover_letter?: string;
}

/**
 * Job application response
 */
export interface JobApplicationResponse {
  /** Application ID */
  id: string;
  /** ID of the vacancy */
  vacancy_id: string;
  /** Title of the vacancy */
  vacancy_title?: string;
  /** ID of the resume submitted */
  resume_id?: string;
  /** Contact email */
  email: string;
  /** Contact phone */
  phone?: string;
  /** Cover letter text */
  cover_letter?: string;
  /** Application status */
  status: JobApplicationStatus;
  /** Submission timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
}

/**
 * Job applications list response
 */
export interface JobApplicationsListResponse {
  /** List of applications */
  applications: JobApplicationResponse[];
  /** Total count of applications */
  total: number;
  /** Page size */
  limit: number;
  /** Number of records skipped */
  skip: number;
}

// ==================== Saved Jobs Types ====================

/**
 * Saved job response
 */
export interface SavedJobResponse {
  /** Saved job ID */
  id: string;
  /** User ID who saved the job */
  user_id: string;
  /** Job vacancy ID */
  vacancy_id: string;
  /** Job vacancy title */
  vacancy_title: string | null;
  /** Job vacancy description */
  vacancy_description: string | null;
  /** Creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
}

/**
 * Saved jobs list response
 */
export interface SavedJobsListResponse {
  /** Total number of saved jobs */
  total: number;
  /** List of saved jobs */
  saved_jobs: SavedJobResponse[];
}

/**
 * Save job request
 */
export interface SaveJobRequest {
  /** Job vacancy ID to save */
  vacancy_id: string;
  /** User ID who is saving the job */
  user_id: string;
}

/**
 * Check if job saved response
 */
export interface CheckJobSavedResponse {
  /** Whether the job is saved by the user */
  is_saved: boolean;
  /** The saved job ID if saved, null otherwise */
  saved_job_id: string | null;
}

// ==================== Resume Optimization Types ====================

/**
 * Optimization suggestion priority levels
 */
export type OptimizationPriority = 'high' | 'medium' | 'low';

/**
 * Optimization suggestion types
 */
export type OptimizationSuggestionType = 'keyword' | 'formatting' | 'content';

/**
 * Optimization suggestion categories
 */
export type OptimizationCategory =
  | 'keywords'
  | 'structure'
  | 'readability'
  | 'impact'
  | 'action_verbs'
  | 'summary'
  | 'active_language'
  | 'achievements';

/**
 * Individual optimization suggestion
 */
export interface OptimizationSuggestion {
  /** Type of suggestion */
  type: OptimizationSuggestionType;
  /** Priority level */
  priority: OptimizationPriority;
  /** Category within the type */
  category: OptimizationCategory;
  /** Short suggestion title */
  title: string;
  /** Detailed suggestion description */
  description: string;
  /** Current state description */
  current_state: string;
  /** What to change */
  recommendation: string;
  /** Example improvements */
  examples: string[];
}

/**
 * Resume optimization request
 */
export interface OptimizationRequest {
  /** Optional job description to target */
  target_job_description?: string;
  /** Whether to check keywords */
  check_keywords?: boolean;
  /** Whether to check formatting */
  check_formatting?: boolean;
  /** Whether to check content */
  check_content?: boolean;
}

/**
 * Resume optimization feedback response
 */
export interface OptimizationFeedback {
  /** Resume ID being optimized */
  resume_id: string;
  /** List of optimization suggestions */
  suggestions: OptimizationSuggestion[];
  /** Total number of suggestions */
  total_suggestions: number;
  /** Number of high-priority suggestions */
  high_priority_count: number;
  /** Number of medium-priority suggestions */
  medium_priority_count: number;
  /** Number of low-priority suggestions */
  low_priority_count: number;
  /** Keywords found in resume */
  keywords_found: string[] | null;
  /** Missing recommended keywords */
  missing_keywords: string[] | null;
  /** Overall optimization score (0-100) */
  score: number;
  /** Error message if analysis failed */
  error: string | null;
  /** Processing time in milliseconds */
  processing_time_ms?: number;
}

// ==================== Job Descriptions Types ====================

/**
 * Job description generation request
 */
export interface JobDescriptionGenerateRequest {
  /** Job title (e.g., 'Senior Python Developer') */
  title: string;
  /** List of required technical skills */
  required_skills: string[];
  /** Minimum experience in months */
  min_experience_months?: number;
  /** Seniority level (junior, mid, senior, lead) */
  seniority_level?: string;
  /** Industry sector (e.g., 'Technology', 'Finance') */
  industry?: string;
  /** Work format (remote, office, hybrid) */
  work_format?: string;
  /** Job location */
  location?: string;
  /** Employment type (full-time, part-time, contract) */
  employment_type?: string;
  /** Salary range (e.g., '$80,000 - $120,000') */
  salary_range?: string;
  /** Additional preferred skills/qualifications */
  additional_requirements?: string[];
  /** Tone for the description (professional, casual, formal, friendly) */
  tone?: 'professional' | 'casual' | 'formal' | 'friendly';
  /** Language for the job description (en, ru) */
  language?: 'en' | 'ru';
}

/**
 * Job description generation response
 */
export interface JobDescriptionResponse {
  /** Job title */
  title: string;
  /** Brief summary of the role */
  summary: string;
  /** Key responsibilities */
  responsibilities: string[];
  /** Requirements and qualifications */
  requirements: string[];
  /** Benefits and perks */
  benefits: string[];
  /** Company culture description */
  company_culture: string;
  /** Interview process overview */
  interview_process: string;
  /** LLM provider used */
  provider: string;
  /** Model name used */
  model: string;
  /** Timestamp of generation */
  generated_at: string;
  /** Inclusiveness score (0-1) from bias checking */
  inclusive_language_score?: number;
  /** Bias warnings detected in the description */
  bias_warnings?: string[];
}

// ==================== Salary Benchmarking Types ====================

/**
 * Salary benchmark request
 */
export interface SalaryBenchmarkRequest {
  /** Job title or role */
  role: string;
  /** Location (city, state, or 'Remote') */
  location: string;
  /** Country code (ISO 3166-1 alpha-2) */
  country?: string;
  /** Experience level (entry, mid, senior, lead, executive) */
  experience_level?: string;
  /** Industry sector */
  industry?: string;
  /** Employment type */
  employment_type?: string;
}

/**
 * Salary benchmark response
 */
export interface SalaryBenchmarkResponse {
  /** Job title */
  role: string;
  /** Location */
  location: string;
  /** 25th percentile salary */
  salary_min: number;
  /** Median salary (50th percentile) */
  salary_median: number;
  /** 75th percentile salary */
  salary_max: number;
  /** 90th percentile salary */
  salary_p90?: number;
  /** Currency code */
  currency: string;
  /** Number of data points */
  sample_size?: number;
  /** Data source */
  data_source?: string;
  /** Date when benchmark is effective */
  effective_date?: string;
}

/**
 * Salary suggestion request
 */
export interface SalarySuggestionRequest {
  /** Resume UUID */
  resume_id: string;
  /** JobVacancy UUID */
  vacancy_id: string;
  /** Apply cost-of-living adjustments */
  include_cost_of_living?: boolean;
  /** Target location for cost adjustment */
  target_location?: string;
}

/**
 * Salary suggestion response
 */
export interface SalarySuggestionResponse {
  /** Resume UUID */
  resume_id: string;
  /** JobVacancy UUID */
  vacancy_id: string;
  /** Suggested minimum salary */
  suggested_min: number;
  /** Suggested median salary */
  suggested_median: number;
  /** Suggested maximum salary */
  suggested_max: number;
  /** Currency code */
  currency: string;
  /** Confidence level (0-1) */
  confidence: number;
  /** Factors affecting the suggestion */
  factors: Record<string, unknown>;
  /** Underlying market data */
  market_benchmark?: SalaryBenchmarkResponse;
}

/**
 * Salary history create request
 */
export interface SalaryHistoryCreate {
  /** Resume UUID */
  resume_id: string;
  /** Base salary amount */
  salary_amount: number;
  /** Payment frequency (annual, monthly, hourly, weekly) */
  salary_frequency?: string;
  /** Currency code */
  currency?: string;
  /** Effective date (YYYY-MM-DD) */
  effective_date: string;
  /** Salary type (current, previous, offer, projected) */
  salary_type?: string;
  /** Employment type */
  employment_type?: string;
  /** Job title */
  job_title?: string;
  /** Company name */
  company_name?: string;
  /** Job location */
  location?: string;
  /** Country code */
  country?: string;
  /** Annual bonus amount */
  bonus_amount?: number;
  /** Bonus type */
  bonus_type?: string;
  /** Annual equity value */
  equity_value?: number;
  /** Equity type */
  equity_type?: string;
  /** Other compensation details */
  other_compensation?: Record<string, unknown>;
  /** Whether data is confirmed */
  is_confirmed?: boolean;
  /** Data source */
  data_source?: string;
}

/**
 * Salary history response
 */
export interface SalaryHistoryResponse {
  /** SalaryHistory UUID */
  id: string;
  /** Resume UUID */
  resume_id: string;
  /** Base salary */
  salary_amount: number;
  /** Payment frequency */
  salary_frequency: string;
  /** Currency code */
  currency: string;
  /** Effective date */
  effective_date: string;
  /** Salary type */
  salary_type: string;
  /** Employment type */
  employment_type: string;
  /** Job title */
  job_title?: string;
  /** Company name */
  company_name?: string;
  /** Location */
  location?: string;
  /** Bonus amount */
  bonus_amount?: number;
  /** Equity value */
  equity_value?: number;
  /** Total annual compensation */
  total_compensation?: number;
  /** Is confirmed */
  is_confirmed: boolean;
  /** Verification status */
  verification_status: string;
  /** Creation timestamp */
  created_at: string;
}

/**
 * Salary history list response
 */
export interface SalaryHistoryListResponse {
  resume_id: string;
  history: SalaryHistoryResponse[];
  total_count: number;
}

/**
 * Offer comparison request
 */
export interface OfferComparisonRequest {
  /** Resume UUID */
  resume_id: string;
  /** List of offers to compare */
  offers: Array<{
    salary: number;
    location: string;
    currency?: string;
    bonus?: number;
    equity?: number;
    job_title?: string;
    company?: string;
  }>;
  /** Apply cost-of-living adjustments */
  apply_cost_of_living?: boolean;
}

/**
 * Offer comparison response
 */
export interface OfferComparisonResponse {
  /** Resume UUID */
  resume_id: string;
  /** Compared offers with adjustments */
  offers: Array<Record<string, unknown>>;
  /** Recommendation based on analysis */
  recommendation: string;
  /** Detailed analysis */
  analysis: Record<string, unknown>;
  /** Candidate's current salary for comparison */
  current_salary?: number;
}

/**
 * Equity analysis request
 */
export interface EquityAnalysisRequest {
  /** JobVacancy UUID */
  vacancy_id: string;
  /** Include demographic breakdown */
  include_demographics?: boolean;
  /** Pay gap threshold (default 0.05) */
  pay_gap_threshold?: number;
}

/**
 * Equity analysis response
 */
export interface EquityAnalysisResponse {
  /** JobVacancy UUID */
  vacancy_id: string;
  /** Job title */
  role: string;
  /** Total candidates analyzed */
  total_candidates: number;
  /** Overall mean salary */
  mean_salary: number;
  /** Overall median salary */
  median_salary: number;
  /** Salary range (min, max) */
  salary_range: { min: number; max: number };
  /** Demographic disparities */
  disparities: Array<{
    group: string;
    mean_salary: number;
    sample_size: number;
    pay_gap: number;
    is_fair: boolean;
  }>;
  /** Equity alerts */
  alerts: string[];
  /** Recommendations */
  recommendations: string[];
}

/**
 * Market trend data point
 */
export interface MarketTrendDataPoint {
  /** Time period (e.g., '2024-Q1', '2024-01') */
  period: string;
  /** 25th percentile salary for the period */
  salary_min: number;
  /** Median salary for the period */
  salary_median: number;
  /** 75th percentile salary for the period */
  salary_max: number;
  /** Number of data points for the period */
  sample_size?: number;
}

/**
 * Market trends response
 */
export interface MarketTrendsResponse {
  /** Job title */
  role: string;
  /** Location */
  location: string;
  /** Currency code */
  currency: string;
  /** Period type (quarterly, monthly, yearly) */
  period_type: string;
  /** Salary trend data points */
  trends: MarketTrendDataPoint[];
  /** Year-over-year salary change percentage */
  year_over_year_change?: number;
  /** Quarter-over-quarter salary change percentage */
  quarter_over_quarter_change?: number;
  /** Data source */
  data_source?: string;
  /** Last update timestamp */
  last_updated?: string;
}

// ==================== Analytics Export Types ====================

/**
 * Supported export formats for analytics data
 */
export type AnalyticsExportFormat = 'json' | 'csv';

/**
 * Analytics sections that can be included in exports
 */
export type AnalyticsExportSection =
  | 'key_metrics'
  | 'funnel'
  | 'recruiter_performance'
  | 'source_tracking'
  | 'stage_duration'
  | 'quality_metrics'
  | 'skill_demand'
  | 'ranking_accuracy'
  | 'taxonomy_usage';

/**
 * Request parameters for analytics data export
 */
export interface AnalyticsExportRequest {
  /** Export format (json or csv) */
  format?: AnalyticsExportFormat;
  /** Start date for analytics data (ISO 8601 format) */
  start_date?: string;
  /** End date for analytics data (ISO 8601 format) */
  end_date?: string;
  /** Specific sections to include. If null, includes all sections */
  sections?: AnalyticsExportSection[];
  /** Whether to include export metadata in the response */
  include_metadata?: boolean;
  /** Filter by specific recruiter ID */
  recruiter_id?: string;
  /** Filter by specific vacancy ID */
  vacancy_id?: string;
}

/**
 * Metadata about an analytics export
 */
export interface AnalyticsExportMetadata {
  /** ISO 8601 timestamp when export was generated */
  export_timestamp: string;
  /** Export format used (json or csv) */
  format: string;
  /** Start date of included data (ISO 8601) */
  start_date?: string;
  /** End date of included data (ISO 8601) */
  end_date?: string;
  /** List of analytics sections included in the export */
  sections_included: string[];
  /** Total number of data records in the export */
  total_records: number;
  /** Filters that were applied to the export */
  filters_applied?: Record<string, unknown>;
  /** User ID or system that generated the export */
  generated_by?: string;
}

/**
 * Configuration for scheduled analytics reports
 */
export interface ScheduledReportConfig {
  /** Name/identifier for the scheduled report */
  report_name: string;
  /** Whether the scheduled report is enabled */
  enabled?: boolean;
  /** Cron expression for report schedule */
  schedule_cron: string;
  /** Export format for the report */
  format?: AnalyticsExportFormat;
  /** Analytics sections to include in the report */
  sections: AnalyticsExportSection[];
  /** Email addresses to receive the report */
  recipients: string[];
  /** Whether to include an executive summary in the email */
  include_summary?: boolean;
  /** Number of days to look back for data (default: 7 days) */
  date_range_days?: number;
}

/**
 * Status of a scheduled analytics report
 */
export interface ScheduledReportStatus {
  /** Name of the scheduled report */
  report_name: string;
  /** Timestamp of last successful run */
  last_run?: string;
  /** Timestamp of next scheduled run */
  next_run?: string;
  /** Current status (active, paused, error) */
  status: string;
  /** Error message from last failed run, if any */
  last_error?: string;
  /** Total number of times the report has been run */
  total_runs?: number;
}

// ==================== Ranking Accuracy Metrics Types ====================

/**
 * Feedback conversion metrics for ranked recommendations
 */
export interface FeedbackConversionMetrics {
  /** Total number of ranked recommendations generated */
  total_recommendations: number;
  /** Number of recommendations that received recruiter feedback */
  recommendations_with_feedback: number;
  /** Proportion of recommendations with feedback (0-1) */
  feedback_rate: number;
  /** Number of recommendations with positive feedback (approved/advanced) */
  positive_feedback_count: number;
  /** Number of recommendations with negative feedback (rejected/dismissed) */
  negative_feedback_count: number;
  /** Proportion of feedback that was positive (0-1) */
  positive_feedback_rate: number;
}

/**
 * Top-N recommendation success rate metrics
 */
export interface TopNRecommendationMetrics {
  /** Success rate for top-1 ranked candidates (0-1) */
  top_1_success_rate: number;
  /** Success rate for top-3 ranked candidates (0-1) */
  top_3_success_rate: number;
  /** Success rate for top-5 ranked candidates (0-1) */
  top_5_success_rate: number;
  /** Success rate for top-10 ranked candidates (0-1) */
  top_10_success_rate: number;
  /** Number of top-1 ranked candidates hired */
  top_1_hired_count: number;
  /** Number of top-5 ranked candidates hired */
  top_5_hired_count: number;
  /** Number of top-10 ranked candidates hired */
  top_10_hired_count: number;
  /** Total number of hires in the period */
  total_hires: number;
}

/**
 * Ranking confidence distribution metrics
 */
export interface RankingConfidenceMetrics {
  /** Recommendations with high confidence score (>0.8) */
  high_confidence_count: number;
  /** Recommendations with medium confidence score (0.5-0.8) */
  medium_confidence_count: number;
  /** Recommendations with low confidence score (<0.5) */
  low_confidence_count: number;
  /** Average ranking confidence score across all recommendations (0-1) */
  avg_confidence_score: number;
  /** Correlation between confidence score and actual success (0-1) */
  confidence_accuracy_correlation?: number;
}

/**
 * Ranking performance trend over time
 */
export interface RankingPerformanceTrend {
  /** Time period identifier (e.g., '2024-01') */
  period: string;
  /** Overall success rate for the period (0-1) */
  success_rate: number;
  /** Feedback rate for the period (0-1) */
  feedback_rate: number;
  /** Average confidence for the period (0-1) */
  avg_confidence: number;
  /** Total recommendations in the period */
  total_recommendations: number;
}

/**
 * Response model for ranking accuracy analytics
 */
export interface RankingMetricsResponse {
  /** Feedback conversion metrics */
  feedback_conversion: FeedbackConversionMetrics;
  /** Top-N recommendation success rate metrics */
  top_n_performance: TopNRecommendationMetrics;
  /** Ranking confidence distribution metrics */
  confidence_distribution: RankingConfidenceMetrics;
  /** Performance trends over time */
  trends?: RankingPerformanceTrend[];
  /** Start date of the analysis period (ISO 8601) */
  period_start?: string;
  /** End date of the analysis period (ISO 8601) */
  period_end?: string;
  /** Total number of vacancies with ranking data */
  total_vacancies_analyzed: number;
}

// ==================== WebSocket Types ====================

/**
 * WebSocket message types
 */
export type WebSocketMessageType =
  | 'notification'
  | 'notification_ack'
  | 'analytics_update'
  | 'ping'
  | 'pong'
  | 'error'
  | 'connection_established';

/**
 * Base WebSocket message structure
 */
export interface WebSocketMessage {
  type: WebSocketMessageType;
  id: string;
  timestamp: string;
  original_message_id?: string;
  status?: string;
  error?: string;
}

/**
 * Notification data within WebSocket message
 */
export interface WebSocketNotificationData {
  id: string;
  recipient_id: string;
  notification_type: string;
  title: string;
  message: string;
  data?: Record<string, unknown>;
  is_read: boolean;
  action_url?: string;
  created_at: string;
}

/**
 * WebSocket notification message
 */
export interface WebSocketNotificationMessage extends WebSocketMessage {
  type: 'notification';
  notification: WebSocketNotificationData;
}

/**
 * WebSocket error message
 */
export interface WebSocketErrorMessage extends WebSocketMessage {
  type: 'error';
  error: string;
  message?: string;
}

/**
 * Analytics update message type
 */
export type AnalyticsUpdateType =
  | 'key_metrics'
  | 'quality_metrics'
  | 'stage_duration'
  | 'ranking_accuracy'
  | 'predictive';

/**
 * Analytics update data sent via WebSocket
 */
export interface AnalyticsUpdateData {
  update_type: AnalyticsUpdateType;
  computed_at: string;
  data: Record<string, unknown>;
}

/**
 * WebSocket analytics update message
 */
export interface WebSocketAnalyticsUpdateMessage extends WebSocketMessage {
  type: 'analytics_update';
  update_type: AnalyticsUpdateType;
  data: AnalyticsUpdateData;
}

// ==================== Calendar Integration Types ====================

/**
 * Supported calendar providers
 */
export type CalendarProvider = 'google' | 'outlook';

/**
 * Calendar connection status
 */
export type ConnectionStatus = 'active' | 'expired' | 'error' | 'disconnected';

/**
 * Create calendar connection request
 */
export interface CalendarConnectionCreate {
  recruiter_id: string;
  provider: CalendarProvider;
  access_token: string;
  refresh_token: string;
  token_expires_at: string;
  calendar_email: string;
  calendar_id?: string;
  webhook_subscription_id?: string;
}

/**
 * Update calendar connection request
 */
export interface CalendarConnectionUpdate {
  access_token?: string;
  refresh_token?: string;
  token_expires_at?: string;
  status?: ConnectionStatus;
  error_message?: string;
  webhook_subscription_id?: string;
  last_sync_at?: string;
}

/**
 * Calendar connection response
 */
export interface CalendarConnectionResponse {
  id: string;
  recruiter_id: string;
  recruiter_name?: string;
  recruiter_email?: string;
  provider: CalendarProvider;
  calendar_email: string;
  calendar_id?: string;
  status: ConnectionStatus;
  token_expires_at: string;
  webhook_subscription_id?: string;
  last_sync_at?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

/**
 * Calendar connection list response
 */
export interface CalendarConnectionListResponse {
  connections: CalendarConnectionResponse[];
  total_count: number;
}

/**
 * Interviewer availability status
 */
export interface InterviewerAvailability {
  interviewer_id: string;
  interviewer_name?: string;
  interviewer_email?: string;
  is_available: boolean;
  has_calendar_connection: boolean;
  calendar_provider?: CalendarProvider;
  conflicting_events: string[];
}

/**
 * Availability check request
 */
export interface AvailabilityCheckRequest {
  interviewer_ids: string[];
  start_time: string;
  duration_minutes: number;
}

/**
 * Availability check response
 */
export interface AvailabilityCheckResponse {
  start_time: string;
  end_time: string;
  duration_minutes: number;
  all_available: boolean;
  interviewer_count: number;
  available_count: number;
  interviewer_availability: InterviewerAvailability[];
}

// ==================== Parsing Correction Types ====================

// Re-export types from parsingCorrection module for centralized access
export type {
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
} from './parsingCorrection';

