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
 * Language preference response
 */
export interface LanguagePreferenceResponse {
  /** Current language preference (en or ru) */
  language: 'en' | 'ru';
}

/**
 * Language preference update request
 */
export interface LanguagePreferenceUpdate {
  /** Language preference to set (en or ru) */
  language: 'en' | 'ru';
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
