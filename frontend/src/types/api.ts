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

