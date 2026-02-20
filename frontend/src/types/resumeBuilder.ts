/**
 * TypeScript types for Resume Builder API
 *
 * This module contains TypeScript interfaces for all API communications
 * with the backend resume builder service, including:
 * - Resume content structure (personal info, work experience, education, skills)
 * - AI-powered improvement suggestions
 * - ATS optimization scoring
 * - Document export (PDF, DOCX)
 * - Skill gap analysis against target jobs
 */

// =============================================================================
// Resume Content Section Types
// =============================================================================

/**
 * Personal information section of a resume
 */
export interface PersonalInfo {
  /** Full name */
  full_name?: string;
  /** Email address */
  email?: string;
  /** Phone number */
  phone?: string;
  /** City, Country */
  location?: string;
  /** LinkedIn profile URL */
  linkedin_url?: string;
  /** Personal website URL */
  website_url?: string;
  /** GitHub profile URL */
  github_url?: string;
  /** Professional title/headline */
  title?: string;
  /** Professional summary/objective */
  summary?: string;
}

/**
 * A single work experience entry
 */
export interface WorkExperienceEntry {
  /** Unique identifier for this entry */
  id?: string;
  /** Company name */
  company?: string;
  /** Job title/position */
  position?: string;
  /** Work location */
  location?: string;
  /** Start date (YYYY-MM or YYYY) */
  start_date?: string;
  /** End date (YYYY-MM, YYYY, or 'Present') */
  end_date?: string;
  /** Whether this is a current position */
  is_current: boolean;
  /** Job description and achievements */
  description?: string;
  /** Skills used in this role */
  skills: string[];
  /** Key achievements/bullet points */
  highlights: string[];
}

/**
 * A single education entry
 */
export interface EducationEntry {
  /** Unique identifier for this entry */
  id?: string;
  /** School/university name */
  institution?: string;
  /** Degree type (Bachelor, Master, etc.) */
  degree?: string;
  /** Major/field of study */
  field_of_study?: string;
  /** Institution location */
  location?: string;
  /** Start date (YYYY-MM or YYYY) */
  start_date?: string;
  /** Graduation date (YYYY-MM or YYYY) */
  end_date?: string;
  /** GPA */
  gpa?: string;
  /** Honors/awards */
  honors: string[];
  /** Additional details (thesis, activities) */
  description?: string;
}

/**
 * A skill entry with optional categorization
 */
export interface SkillEntry {
  /** Skill name */
  name: string;
  /** Skill category (technical, soft, language) */
  category?: string;
  /** Proficiency level (expert, advanced, intermediate, basic) */
  level?: string;
  /** Years of experience with this skill */
  years_of_experience?: number;
}

/**
 * A certification or license entry
 */
export interface CertificationEntry {
  /** Unique identifier for this entry */
  id?: string;
  /** Certification name */
  name: string;
  /** Issuing organization */
  issuer?: string;
  /** Issue date (YYYY-MM or YYYY) */
  issue_date?: string;
  /** Expiry date (YYYY-MM or YYYY), if applicable */
  expiry_date?: string;
  /** Credential ID or number */
  credential_id?: string;
  /** URL to verify credential */
  credential_url?: string;
}

/**
 * A language proficiency entry
 */
export interface LanguageEntry {
  /** Language name */
  name: string;
  /** Proficiency level (native, fluent, intermediate, basic) */
  proficiency?: string;
  /** Language certification (IELTS, TOEFL, etc.) */
  certification?: string;
}

/**
 * A project entry
 */
export interface ProjectEntry {
  /** Unique identifier for this entry */
  id?: string;
  /** Project name */
  name: string;
  /** Project description */
  description?: string;
  /** Start date (YYYY-MM or YYYY) */
  start_date?: string;
  /** End date (YYYY-MM or YYYY) */
  end_date?: string;
  /** Project URL */
  url?: string;
  /** Technologies used */
  technologies: string[];
  /** Key achievements */
  highlights: string[];
}

/**
 * Complete resume content structure
 *
 * This interface represents the JSON content stored in the BuiltResume.content field.
 * It contains all sections of a resume in a structured format.
 */
export interface ResumeContent {
  /** Personal information section */
  personal_info?: PersonalInfo;
  /** Professional summary/objective */
  summary?: string;
  /** Work experience entries */
  work_experience: WorkExperienceEntry[];
  /** Education entries */
  education: EducationEntry[];
  /** Skills */
  skills: SkillEntry[];
  /** Certifications */
  certifications: CertificationEntry[];
  /** Languages */
  languages: LanguageEntry[];
  /** Projects */
  projects: ProjectEntry[];
  /** Custom sections */
  custom_sections: Record<string, unknown>;
}

// =============================================================================
// AI Suggestions Types
// =============================================================================

/**
 * AI suggestion type
 */
export type AISuggestionType = 'content' | 'grammar' | 'keyword' | 'format' | 'ats' | 'skills';

/**
 * A single AI-generated improvement suggestion
 */
export interface AISuggestion {
  /** Unique suggestion identifier */
  id: string;
  /** Suggestion type */
  type: AISuggestionType;
  /** Target section (summary, work_experience, skills, etc.) */
  section: string;
  /** Specific field within section */
  field?: string;
  /** ID of the specific entry being improved */
  entry_id?: string;
  /** Original text to be replaced */
  original_text?: string;
  /** Suggested improvement text */
  suggested_text: string;
  /** Explanation for the suggestion */
  reason?: string;
  /** Priority level (0=low, 1=medium, 2=high) */
  priority: number;
  /** Expected impact on ATS score (0-100) */
  impact_score?: number;
}

/**
 * Response model for AI suggestions
 */
export interface AISuggestionsResponse {
  /** List of suggestions */
  suggestions: AISuggestion[];
  /** ATS score before applying suggestions */
  ats_score_before?: number;
  /** Potential ATS score if all applied */
  ats_score_potential?: number;
  /** Timestamp when suggestions were generated */
  generated_at: string;
}

/**
 * Request model for applying an AI suggestion
 */
export interface ApplySuggestionRequest {
  /** ID of the suggestion to apply */
  suggestion_id: string;
  /** Optional modified version of suggested text */
  modified_text?: string;
}

// =============================================================================
// ATS Optimization Types
// =============================================================================

/**
 * ATS issue severity level
 */
export type ATSIssueSeverity = 'low' | 'medium' | 'high';

/**
 * An ATS optimization issue
 */
export interface ATSIssue {
  /** Section with the issue */
  section: string;
  /** Specific field with the issue */
  field?: string;
  /** ID of the specific entry */
  entry_id?: string;
  /** Type of issue (missing_keyword, format, length, etc.) */
  issue_type: string;
  /** Severity level */
  severity: ATSIssueSeverity;
  /** Description of the issue */
  description: string;
  /** Suggested fix */
  suggestion?: string;
}

/**
 * Response model for ATS score analysis
 */
export interface ATSScoreResponse {
  /** ATS compatibility score (0-100) */
  score: number;
  /** List of issues found */
  issues: ATSIssue[];
  /** Keywords detected in resume */
  keywords_found: string[];
  /** Important keywords missing */
  keywords_missing: string[];
  /** Sections that were analyzed */
  sections_analyzed: string[];
  /** Timestamp of analysis */
  analyzed_at: string;
}

// =============================================================================
// Skill Gap Analysis Types
// =============================================================================

/**
 * Skill importance level for job requirements
 */
export type SkillImportance = 'required' | 'preferred' | 'nice_to_have';

/**
 * Learning resource for skill development
 */
export interface LearningResource {
  /** Resource title */
  title: string;
  /** Resource URL */
  url?: string;
  /** Resource type (course, tutorial, etc.) */
  type?: string;
  /** Estimated duration */
  duration?: string;
  /** Whether the resource is free */
  is_free?: boolean;
}

/**
 * A skill gap between resume and target job
 */
export interface SkillGap {
  /** Name of the missing skill */
  skill_name: string;
  /** Skill category */
  category?: string;
  /** Importance level */
  importance: SkillImportance;
  /** How often this skill appears in similar jobs (%) */
  job_frequency?: number;
  /** Suggested learning resources */
  learning_resources: LearningResource[];
}

/**
 * Response model for skill gap analysis (resume builder specific)
 */
export interface ResumeSkillGapAnalysisResponse {
  /** ID of the target job vacancy */
  target_job_id: string;
  /** Title of the target job */
  target_job_title?: string;
  /** Skills that match the job */
  matching_skills: string[];
  /** Skills with partial match */
  partial_match_skills: string[];
  /** Missing skills with details */
  missing_skills: SkillGap[];
  /** Overall match percentage */
  match_percentage: number;
  /** General recommendations */
  recommendations: string[];
  /** Timestamp of analysis */
  analyzed_at: string;
}

// =============================================================================
// Export Types
// =============================================================================

/**
 * Supported export formats
 */
export type ExportFormat = 'pdf' | 'docx' | 'json';

/**
 * Request model for exporting a resume
 */
export interface ExportRequest {
  /** Export format (pdf, docx, json) */
  format: ExportFormat;
}

/**
 * Response model for export operation
 */
export interface ExportResponse {
  /** URL to download the exported file */
  download_url: string;
  /** Generated filename */
  filename: string;
  /** Export format used */
  format: string;
  /** File size in bytes */
  file_size?: number;
  /** Download URL expiration timestamp */
  expires_at?: string;
}

// =============================================================================
// Resume CRUD Types
// =============================================================================

/**
 * Request model for creating a new resume
 */
export interface BuiltResumeCreate {
  /** Template ID to use for this resume */
  template_id?: string;
  /** Resume title/name */
  title: string;
  /** Initial resume content */
  content?: ResumeContent;
  /** Target job vacancy ID for skill gap analysis */
  target_job_id?: string;
  /** Whether this is a draft */
  is_draft: boolean;
}

/**
 * Request model for updating an existing resume
 */
export interface BuiltResumeUpdate {
  /** Updated template ID */
  template_id?: string;
  /** Updated resume title */
  title?: string;
  /** Updated resume content */
  content?: ResumeContent;
  /** Updated target job vacancy ID */
  target_job_id?: string;
  /** Updated ATS score */
  ats_score?: number;
  /** Updated draft status */
  is_draft?: boolean;
}

/**
 * Response model for a single resume
 */
export interface BuiltResumeResponse {
  /** Resume UUID */
  id: string;
  /** Owner user ID */
  user_id: string;
  /** Organization ID */
  organization_id: string;
  /** Template ID */
  template_id?: string;
  /** Resume title */
  title: string;
  /** Resume content */
  content: ResumeContent;
  /** Target job vacancy ID */
  target_job_id?: string;
  /** ATS score (0-100) */
  ats_score?: number;
  /** Resume version number */
  version: number;
  /** Whether this is a draft */
  is_draft: boolean;
  /** Last AI suggestions */
  last_ai_suggestions?: AISuggestionsResponse;
  /** Creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
}

/**
 * Response model for listing resumes
 */
export interface BuiltResumeListResponse {
  /** List of resumes */
  items: BuiltResumeResponse[];
  /** Total number of resumes */
  total: number;
  /** Current page number */
  page: number;
  /** Items per page */
  page_size: number;
  /** Total number of pages */
  total_pages: number;
}

/**
 * Summary model for resume list view (lighter response)
 */
export interface BuiltResumeSummary {
  /** Resume UUID */
  id: string;
  /** Resume title */
  title: string;
  /** ATS score */
  ats_score?: number;
  /** Version number */
  version: number;
  /** Draft status */
  is_draft: boolean;
  /** Creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
}

/**
 * Response model for listing resume summaries
 */
export interface BuiltResumeSummaryListResponse {
  /** List of resume summaries */
  items: BuiltResumeSummary[];
  /** Total number of resumes */
  total: number;
  /** Current page number */
  page: number;
  /** Items per page */
  page_size: number;
  /** Total number of pages */
  total_pages: number;
}

// =============================================================================
// Template Types
// =============================================================================

/**
 * Summary model for a resume template
 */
export interface ResumeTemplateSummary {
  /** Template UUID */
  id: string;
  /** Template name */
  name: string;
  /** Template description */
  description?: string;
  /** Preview image URL */
  preview_url?: string;
  /** Template category (modern, classic, etc.) */
  category?: string;
  /** Whether this is a premium template */
  is_premium: boolean;
}

/**
 * Response model for listing resume templates
 */
export interface ResumeTemplateListResponse {
  /** List of templates */
  items: ResumeTemplateSummary[];
  /** Total number of templates */
  total: number;
}

// =============================================================================
// Version History Types
// =============================================================================

/**
 * Summary of a resume version
 */
export interface ResumeVersionSummary {
  /** Version number */
  version: number;
  /** Title at this version */
  title: string;
  /** ATS score at this version */
  ats_score?: number;
  /** When this version was created */
  created_at: string;
  /** Summary of changes from previous version */
  changes_summary?: string;
}

/**
 * Response model for resume version history
 */
export interface ResumeVersionHistoryResponse {
  /** Resume UUID */
  resume_id: string;
  /** Current version number */
  current_version: number;
  /** List of all versions */
  versions: ResumeVersionSummary[];
}

// =============================================================================
// Default/Empty Values Helper
// =============================================================================

/**
 * Creates an empty resume content structure with default values
 */
export function createEmptyResumeContent(): ResumeContent {
  return {
    personal_info: {
      full_name: '',
      email: '',
      phone: '',
      location: '',
      linkedin_url: '',
      website_url: '',
      github_url: '',
      title: '',
      summary: '',
    },
    summary: '',
    work_experience: [],
    education: [],
    skills: [],
    certifications: [],
    languages: [],
    projects: [],
    custom_sections: {},
  };
}

/**
 * Creates an empty work experience entry
 */
export function createEmptyWorkExperience(): WorkExperienceEntry {
  return {
    id: crypto.randomUUID ? crypto.randomUUID() : `we-${Date.now()}`,
    company: '',
    position: '',
    location: '',
    start_date: '',
    end_date: '',
    is_current: false,
    description: '',
    skills: [],
    highlights: [],
  };
}

/**
 * Creates an empty education entry
 */
export function createEmptyEducation(): EducationEntry {
  return {
    id: crypto.randomUUID ? crypto.randomUUID() : `edu-${Date.now()}`,
    institution: '',
    degree: '',
    field_of_study: '',
    location: '',
    start_date: '',
    end_date: '',
    gpa: '',
    honors: [],
    description: '',
  };
}

/**
 * Creates an empty skill entry
 */
export function createEmptySkill(): SkillEntry {
  return {
    name: '',
    category: '',
    level: '',
    years_of_experience: undefined,
  };
}

/**
 * Creates an empty certification entry
 */
export function createEmptyCertification(): CertificationEntry {
  return {
    id: crypto.randomUUID ? crypto.randomUUID() : `cert-${Date.now()}`,
    name: '',
    issuer: '',
    issue_date: '',
    expiry_date: '',
    credential_id: '',
    credential_url: '',
  };
}

/**
 * Creates an empty language entry
 */
export function createEmptyLanguage(): LanguageEntry {
  return {
    name: '',
    proficiency: '',
    certification: '',
  };
}

/**
 * Creates an empty project entry
 */
export function createEmptyProject(): ProjectEntry {
  return {
    id: crypto.randomUUID ? crypto.randomUUID() : `proj-${Date.now()}`,
    name: '',
    description: '',
    start_date: '',
    end_date: '',
    url: '',
    technologies: [],
    highlights: [],
  };
}
