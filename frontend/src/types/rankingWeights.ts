/**
 * Ranking Weights Type Definitions
 *
 * This module contains TypeScript interfaces for ranking weights API communications.
 * These types mirror the backend Pydantic schemas for ranking weight profiles,
 * version history, and weight normalization.
 */

/**
 * Preset type literal for ranking weight profiles
 */
export type PresetType = 'technical' | 'sales' | 'executive' | 'balanced';

/**
 * Request model for creating a ranking weight profile
 */
export interface RankingWeightProfileCreate {
  organization_id?: string;
  vacancy_id?: string;
  name: string;
  description?: string;

  // 13 ranking feature weights
  overall_match_score_weight?: number;
  keyword_score_weight?: number;
  tfidf_score_weight?: number;
  vector_score_weight?: number;
  skills_match_ratio_weight?: number;
  experience_months_weight?: number;
  experience_relevance_weight?: number;
  education_level_weight?: number;
  recent_experience_weight?: number;
  skill_rarity_weight?: number;
  title_similarity_weight?: number;
  freshness_score_weight?: number;
  completeness_score_weight?: number;

  is_active?: boolean;
  is_preset?: boolean;
  preset_type?: PresetType;
  created_by?: string;
  change_reason?: string;
}

/**
 * Request model for updating a ranking weight profile
 */
export interface RankingWeightProfileUpdate {
  name?: string;
  description?: string;

  // 13 ranking feature weights (all optional for partial updates)
  overall_match_score_weight?: number;
  keyword_score_weight?: number;
  tfidf_score_weight?: number;
  vector_score_weight?: number;
  skills_match_ratio_weight?: number;
  experience_months_weight?: number;
  experience_relevance_weight?: number;
  education_level_weight?: number;
  recent_experience_weight?: number;
  skill_rarity_weight?: number;
  title_similarity_weight?: number;
  freshness_score_weight?: number;
  completeness_score_weight?: number;

  is_active?: boolean;
  updated_by?: string;
  change_reason?: string;
}

/**
 * Response model for a single ranking weight profile
 */
export interface RankingWeightProfile {
  id: string;
  organization_id?: string;
  vacancy_id?: string;
  name: string;
  description?: string;

  // 13 ranking feature weights
  overall_match_score_weight: number;
  keyword_score_weight: number;
  tfidf_score_weight: number;
  vector_score_weight: number;
  skills_match_ratio_weight: number;
  experience_months_weight: number;
  experience_relevance_weight: number;
  education_level_weight: number;
  recent_experience_weight: number;
  skill_rarity_weight: number;
  title_similarity_weight: number;
  freshness_score_weight: number;
  completeness_score_weight: number;

  is_active: boolean;
  is_preset: boolean;
  preset_type?: string;
  created_by?: string;
  updated_by?: string;
  version?: string;
  change_reason?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Response model for listing ranking weight profiles
 */
export interface RankingWeightProfileListResponse {
  organization_id?: string;
  vacancy_id?: string;
  profiles: RankingWeightProfile[];
  total_count: number;
}

/**
 * Response model for a ranking weight version history entry
 */
export interface RankingWeightVersion {
  id: string;
  profile_id: string;

  // Snapshot of weights at this version
  overall_match_score_weight: number;
  keyword_score_weight: number;
  tfidf_score_weight: number;
  vector_score_weight: number;
  skills_match_ratio_weight: number;
  experience_months_weight: number;
  experience_relevance_weight: number;
  education_level_weight: number;
  recent_experience_weight: number;
  skill_rarity_weight: number;
  title_similarity_weight: number;
  freshness_score_weight: number;
  completeness_score_weight: number;

  changed_by?: string;
  version: string;
  change_reason?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Response model for version history list
 */
export interface RankingWeightVersionHistoryResponse {
  profile_id: string;
  versions: RankingWeightVersion[];
  total_count: number;
}

/**
 * Request model for normalizing ranking weights
 */
export interface NormalizeRankingWeightsRequest {
  // 13 ranking feature weights (all optional, only provided weights will be normalized)
  overall_match_score_weight?: number;
  keyword_score_weight?: number;
  tfidf_score_weight?: number;
  vector_score_weight?: number;
  skills_match_ratio_weight?: number;
  experience_months_weight?: number;
  experience_relevance_weight?: number;
  education_level_weight?: number;
  recent_experience_weight?: number;
  skill_rarity_weight?: number;
  title_similarity_weight?: number;
  freshness_score_weight?: number;
  completeness_score_weight?: number;
}

/**
 * Response model for normalized ranking weights
 */
export interface NormalizedRankingWeightsResponse {
  // Normalized weights (sum to 1.0)
  overall_match_score_weight: number;
  keyword_score_weight: number;
  tfidf_score_weight: number;
  vector_score_weight: number;
  skills_match_ratio_weight: number;
  experience_months_weight: number;
  experience_relevance_weight: number;
  education_level_weight: number;
  recent_experience_weight: number;
  skill_rarity_weight: number;
  title_similarity_weight: number;
  freshness_score_weight: number;
  completeness_score_weight: number;

  total: number;
}

/**
 * Model showing how a single candidate's ranking changed
 */
export interface CandidateRankingChange {
  resume_id: string;
  candidate_name?: string;

  // Current (baseline) ranking
  current_position: number;
  current_score: number;

  // New (preview) ranking
  new_position: number;
  new_score: number;

  // Change metrics
  position_change: number;
  score_change: number;
}

/**
 * Request model for previewing ranking weight impact
 */
export interface PreviewRankingImpactRequest {
  vacancy_id: string;

  // 13 ranking feature weights (all optional, only provided weights will be used)
  overall_match_score_weight?: number;
  keyword_score_weight?: number;
  tfidf_score_weight?: number;
  vector_score_weight?: number;
  skills_match_ratio_weight?: number;
  experience_months_weight?: number;
  experience_relevance_weight?: number;
  education_level_weight?: number;
  recent_experience_weight?: number;
  skill_rarity_weight?: number;
  title_similarity_weight?: number;
  freshness_score_weight?: number;
  completeness_score_weight?: number;
}

/**
 * Response model for ranking weight impact preview
 */
export interface PreviewRankingImpactResponse {
  vacancy_id: string;
  vacancy_title?: string;

  // Weight information
  current_weights_profile?: string;
  preview_weights_source: string;

  // Ranking changes
  total_candidates: number;
  candidates_moved: number;
  candidates_unchanged: number;

  // Top changes
  biggest_movers_up: CandidateRankingChange[];
  biggest_movers_down: CandidateRankingChange[];

  // All rankings (limited)
  all_changes: CandidateRankingChange[];

  // Summary statistics
  avg_score_change: number;
  max_position_change: number;
}

/**
 * Preset ranking weight profile
 */
export interface RankingWeightPreset {
  name: string;
  preset_type: PresetType;
  description: string;
  use_case: string;
  weights: {
    overall_match_score_weight: number;
    keyword_score_weight: number;
    tfidf_score_weight: number;
    vector_score_weight: number;
    skills_match_ratio_weight: number;
    experience_months_weight: number;
    experience_relevance_weight: number;
    education_level_weight: number;
    recent_experience_weight: number;
    skill_rarity_weight: number;
    title_similarity_weight: number;
    freshness_score_weight: number;
    completeness_score_weight: number;
  };
}

/**
 * Response model for preset profiles
 */
export interface RankingWeightPresetsResponse {
  presets: RankingWeightPreset[];
  total_count: number;
}
