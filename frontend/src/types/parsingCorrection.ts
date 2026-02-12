/**
 * Parsing correction and learning feedback type definitions
 *
 * This module contains TypeScript interfaces for parsing corrections
 * and learning feedback, enabling tracking and improvement of resume parsing accuracy.
 */

// ==================== Source Text Location Types ====================

/**
 * Source text location for visual highlighting
 * Represents where in the document a field was extracted from
 */
export interface SourceTextLocation {
  /** Page number in document (1-indexed) */
  page?: number;
  /** Bounding box coordinates [x0, y0, x1, y1] */
  bbox?: [number, number, number, number];
  /** The source text snippet that was extracted */
  text?: string;
  /** Start position in the document text */
  start?: number;
  /** End position in the document text */
  end?: number;
}

// ==================== Parsing Correction Types ====================

/**
 * Correction reason enumeration
 * Standard reasons for parsing corrections
 */
export type CorrectionReason =
  | 'position_was_incorrect'
  | 'missing_skill'
  | 'incorrect_skill'
  | 'date_was_incorrect'
  | 'company_was_incorrect'
  | 'education_was_incorrect'
  | 'language_was_incorrect'
  | 'field_was_empty'
  | 'field_was_incomplete'
  | 'wrong_field_type'
  | 'other';

/**
 * Valid field names that can be corrected
 */
export type CorrectableFieldName =
  | 'position'
  | 'skills'
  | 'education'
  | 'work_experience'
  | 'languages'
  | 'age'
  | 'raw_text'
  | 'other';

/**
 * Parsing correction entry (base interface)
 */
export interface ParsingCorrection {
  /** Unique correction ID */
  id: string;
  /** Resume ID this correction belongs to */
  resume_id: string;
  /** Name of the corrected field */
  field_name: CorrectableFieldName;
  /** Original AI-parsed value before correction */
  original_value: Record<string, unknown> | null;
  /** User's corrected value */
  corrected_value: Record<string, unknown> | null;
  /** Reason for the correction */
  reason: CorrectionReason | string | null;
  /** Location in source document used for parsing */
  source_text_location: SourceTextLocation | null;
  /** ID of user who made the correction */
  corrected_by: string | null;
  /** Timestamp when correction was created */
  created_at: string;
}

/**
 * Parsing correction create request
 */
export interface ParsingCorrectionCreate {
  /** Name of the corrected field */
  field_name: CorrectableFieldName;
  /** Original AI-parsed value before correction */
  original_value?: Record<string, unknown> | null;
  /** User's corrected value */
  corrected_value?: Record<string, unknown> | null;
  /** Reason for the correction */
  reason?: CorrectionReason | string | null;
  /** Location in source document used for parsing */
  source_text_location?: SourceTextLocation | null;
}

/**
 * Parsing correction update request
 */
export interface ParsingCorrectionUpdate {
  /** Corrected value */
  corrected_value?: Record<string, unknown> | null;
  /** Reason for the correction */
  reason?: CorrectionReason | string | null;
}

/**
 * Single correction response
 */
export interface ParsingCorrectionResponse {
  /** Unique correction ID */
  id: string;
  /** Resume ID this correction belongs to */
  resume_id: string;
  /** Name of the corrected field */
  field_name: CorrectableFieldName;
  /** Original AI-parsed value before correction */
  original_value: Record<string, unknown> | null;
  /** User's corrected value */
  corrected_value: Record<string, unknown> | null;
  /** Reason for the correction */
  reason: CorrectionReason | string | null;
  /** Location in source document used for parsing */
  source_text_location: SourceTextLocation | null;
  /** ID of user who made the correction */
  corrected_by: string | null;
  /** Timestamp when correction was created */
  created_at: string | null;
}

/**
 * Parsing corrections list response
 */
export interface ParsingCorrectionsListResponse {
  /** Whether request was successful */
  success: boolean;
  /** List of corrections */
  data: ParsingCorrectionResponse[];
  /** Total number of corrections */
  count: number;
  /** Success message */
  message: string;
}

/**
 * Parsing correction create response
 */
export interface ParsingCorrectionCreateResponse {
  /** Whether correction was created successfully */
  success: boolean;
  /** Created correction details */
  data: ParsingCorrectionResponse;
  /** Success message */
  message: string;
}

/**
 * Field update request for updating a single parsed field
 */
export interface FieldUpdateRequest {
  /** The corrected value for the field */
  value: string;
  /** The original AI-parsed value before correction */
  original_value?: string | null;
  /** Reason for the correction */
  reason?: CorrectionReason | string | null;
}

/**
 * Field update response
 */
export interface FieldUpdateResponse {
  /** Whether field was updated successfully */
  success: boolean;
  /** Created correction details */
  data: ParsingCorrectionResponse;
  /** Success message */
  message: string;
}

// ==================== Learning Feedback Types ====================

/**
 * Pattern type for learning feedback classification
 */
export type LearningPatternType =
  | 'extraction'
  | 'classification'
  | 'formatting'
  | 'merge'
  | 'split';

/**
 * Learning feedback entry (base interface)
 * Stores aggregated patterns from corrections for parser improvement
 */
export interface LearningFeedback {
  /** Unique feedback ID */
  id: string;
  /** Optional reference to specific correction that triggered this feedback */
  correction_id: string | null;
  /** Field type this feedback applies to */
  field_name: CorrectableFieldName;
  /** Description of the error pattern observed */
  error_pattern: string | null;
  /** Suggested improvement for the parser */
  suggestion: string | null;
  /** Type of pattern identified */
  pattern_type: LearningPatternType | null;
  /** Confidence level of this learning (0.0-1.0) */
  confidence_score: number | null;
  /** Number of corrections that contributed to this pattern */
  sample_count: number | null;
  /** Example corrections demonstrating this pattern */
  examples: Array<{
    original: Record<string, unknown>;
    corrected: Record<string, unknown>;
    context?: string;
  }> | null;
  /** Version of parser when feedback was generated */
  parser_version: string | null;
  /** Whether feedback has been applied to improve parser */
  is_applied: boolean;
  /** Timestamp when feedback was created */
  created_at: string;
  /** Timestamp when feedback was last updated */
  updated_at: string;
}

/**
 * Learning feedback create request
 */
export interface LearningFeedbackCreate {
  /** Optional correction ID that triggered this feedback */
  correction_id?: string | null;
  /** Field type this feedback applies to */
  field_name: CorrectableFieldName;
  /** Description of the error pattern */
  error_pattern?: string | null;
  /** Suggested improvement */
  suggestion?: string | null;
  /** Pattern type */
  pattern_type?: LearningPatternType | null;
  /** Confidence score (0.0-1.0) */
  confidence_score?: number | null;
  /** Sample count */
  sample_count?: number | null;
  /** Examples */
  examples?: Array<{
    original: Record<string, unknown>;
    corrected: Record<string, unknown>;
    context?: string;
  }> | null;
  /** Parser version */
  parser_version?: string | null;
}

/**
 * Learning feedback update request
 */
export interface LearningFeedbackUpdate {
  /** Error pattern description */
  error_pattern?: string | null;
  /** Suggested improvement */
  suggestion?: string | null;
  /** Confidence score */
  confidence_score?: number | null;
  /** Sample count */
  sample_count?: number | null;
  /** Examples */
  examples?: Array<{
    original: Record<string, unknown>;
    corrected: Record<string, unknown>;
    context?: string;
  }> | null;
  /** Whether feedback has been applied */
  is_applied?: boolean;
}

/**
 * Learning feedback response
 */
export interface LearningFeedbackResponse {
  /** Unique feedback ID */
  id: string;
  /** Optional correction ID reference */
  correction_id: string | null;
  /** Field type */
  field_name: CorrectableFieldName;
  /** Error pattern description */
  error_pattern: string | null;
  /** Suggested improvement */
  suggestion: string | null;
  /** Pattern type */
  pattern_type: LearningPatternType | null;
  /** Confidence score */
  confidence_score: number | null;
  /** Sample count */
  sample_count: number | null;
  /** Examples */
  examples: Array<{
    original: Record<string, unknown>;
    corrected: Record<string, unknown>;
    context?: string;
  }> | null;
  /** Parser version */
  parser_version: string | null;
  /** Whether applied */
  is_applied: boolean;
  /** Creation timestamp */
  created_at: string;
  /** Update timestamp */
  updated_at: string;
}

/**
 * Learning feedback list response
 */
export interface LearningFeedbackListResponse {
  /** List of feedback entries */
  data: LearningFeedbackResponse[];
  /** Total count */
  count: number;
  /** Success message */
  message: string;
}

/**
 * Learning pattern summary for a specific field
 */
export interface LearningPatternSummary {
  /** Field name */
  field_name: CorrectableFieldName;
  /** Total patterns identified */
  total_patterns: number;
  /** Average confidence score */
  average_confidence: number;
  /** Patterns by type */
  patterns_by_type: Record<LearningPatternType, number>;
  /** Most common error pattern */
  most_common_error: string | null;
  /** Improvement suggestion */
  top_suggestion: string | null;
}

/**
 * Learning feedback summary response
 */
export interface LearningFeedbackSummaryResponse {
  /** Summary by field */
  field_summaries: LearningPatternSummary[];
  /** Total patterns across all fields */
  total_patterns: number;
  /** Total applied patterns */
  applied_patterns: number;
  /** Average confidence across all patterns */
  overall_confidence: number;
}

// ==================== Visual Parsing Feedback Types ====================

/**
 * Source location for a single extracted field
 */
export interface FieldSourceLocation {
  /** Field name */
  field_name: string;
  /** Source text location in document */
  location: SourceTextLocation;
  /** The extracted value */
  extracted_value: string | Record<string, unknown>;
  /** Confidence score of extraction (0-1) */
  confidence?: number;
}

/**
 * Visual parsing feedback for displaying source-to-field mapping
 */
export interface VisualParsingFeedback {
  /** Resume ID */
  resume_id: string;
  /** All source locations for extracted fields */
  source_locations: FieldSourceLocation[];
  /** Total fields extracted */
  total_fields: number;
  /** Fields with corrections */
  corrected_fields: string[];
}

/**
 * Correction statistics for a resume
 */
export interface CorrectionStatistics {
  /** Resume ID */
  resume_id: string;
  /** Total corrections made */
  total_corrections: number;
  /** Corrections by field */
  corrections_by_field: Record<CorrectableFieldName, number>;
  /** Corrections by reason */
  corrections_by_reason: Record<string, number>;
  /** Most corrected field */
  most_corrected_field: CorrectableFieldName | null;
  /** Last correction timestamp */
  last_correction_at: string | null;
}

/**
 * Correction statistics response
 */
export interface CorrectionStatisticsResponse {
  /** Statistics */
  data: CorrectionStatistics;
  /** Success message */
  message: string;
}

// ==================== API Query Params Types ====================

/**
 * Query parameters for fetching corrections
 */
export interface CorrectionsQueryParams {
  /** Filter by field name */
  field_name?: CorrectableFieldName;
  /** Filter by reason */
  reason?: CorrectionReason | string;
  /** Maximum number of results */
  limit?: number;
  /** Number of results to skip */
  offset?: number;
}

/**
 * Query parameters for fetching learning feedback
 */
export interface LearningFeedbackQueryParams {
  /** Filter by field name */
  field_name?: CorrectableFieldName;
  /** Filter by pattern type */
  pattern_type?: LearningPatternType;
  /** Filter by applied status */
  is_applied?: boolean;
  /** Minimum confidence score */
  min_confidence?: number;
  /** Maximum number of results */
  limit?: number;
  /** Number of results to skip */
  offset?: number;
}
