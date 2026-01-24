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
