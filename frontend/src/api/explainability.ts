/**
 * Explainability API Client
 *
 * This module provides a convenient interface for AI decision transparency,
 * including natural language explanations, feature contributions, what-if
 * analysis, confidence intervals, candidate comparisons, and organization
 * preference management.
 *
 * @example
 * ```ts
 * import { explainability } from '@/api/explainability';
 *
 * // Get ranking explanation
 * const explanation = await explainability.explainRanking({
 *   resume_id: 'abc-123',
 *   vacancy_id: 'vac-456',
 *   use_llm: true,
 * });
 *
 * // Perform what-if analysis
 * const whatIf = await explainability.whatIfAnalysis({
 *   resume_id: 'abc-123',
 *   vacancy_id: 'vac-456',
 *   adjustments: { experience_months: 12 },
 * });
 *
 * // Compare two candidates
 * const comparison = await explainability.compareCandidates({
 *   resume_a_id: 'resume-1',
 *   resume_b_id: 'resume-2',
 *   vacancy_id: 'vacancy-123',
 *   use_llm: true,
 * });
 *
 * // Get sensitivity analysis
 * const sensitivity = await explainability.sensitivityAnalysis({
 *   resume_id: 'abc-123',
 *   vacancy_id: 'vac-456',
 *   perturbation_percent: 0.1,
 * });
 *
 * // Get confidence interval
 * const confidence = await explainability.getConfidenceInterval('rank-id-123');
 *
 * // Get organization preferences
 * const preferences = await explainability.getOrganizationPreferences('test-org');
 *
 * // Update organization preferences
 * const updated = await explainability.updateOrganizationPreferences('test-org', {
 *   tone: 'casual',
 *   style: 'concise',
 *   is_active: true,
 * });
 * ```
 */

import axios, { AxiosInstance } from 'axios';
import type { ApiError } from '@/types/api';

// ==================== Types ====================

/**
 * Feature explanation detail
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
 * Confidence interval for prediction
 */
export interface ConfidenceInterval {
  lower_bound: number;
  upper_bound: number;
  margin_of_error: number;
  confidence_level: number;
  interpretation: string;
}

/**
 * Explain ranking request
 */
export interface ExplainRankingRequest {
  resume_id: string;
  vacancy_id: string;
  use_llm?: boolean;
}

/**
 * Explain ranking response
 */
export interface ExplainRankingResponse {
  resume_id: string;
  vacancy_id: string;
  candidate_name: string | null;
  rank_score: number;
  rank_position: number | null;
  narrative: string;
  feature_explanations: FeatureExplanation[];
  confidence_interval: ConfidenceInterval | null;
  strengths: string[];
  weaknesses: string[];
  recommendation: string;
  highlight_sections: Record<string, string>;
  percentile_rank: number | null;
  percentile_explanation: string;
  provider: string;
  model: string;
  generated_at: string;
}

/**
 * What-if analysis request
 */
export interface WhatIfAnalysisRequest {
  resume_id: string;
  vacancy_id: string;
  adjustments: Record<string, number>;
}

/**
 * Feature perturbation detail
 */
export interface FeaturePerturbation {
  feature_name: string;
  original_value: number;
  perturbed_value: number;
  perturbation_amount: number;
  perturbation_percent: number;
}

/**
 * What-if analysis response
 */
export interface WhatIfAnalysisResponse {
  resume_id: string;
  vacancy_id: string;
  scenario_description: string;
  original_score: number;
  new_score: number;
  score_delta: number;
  score_delta_percent: number;
  original_recommendation: string;
  new_recommendation: string;
  perturbations: FeaturePerturbation[];
  feature_impacts: Record<string, number>;
  explanation: string;
  timestamp: string;
}

/**
 * Sensitivity analysis request
 */
export interface SensitivityAnalysisRequest {
  resume_id: string;
  vacancy_id: string;
  perturbation_percent?: number;
}

/**
 * Sensitive feature detail
 */
export interface SensitiveFeature {
  feature: string;
  sensitivity: number;
  impact_description: string;
}

/**
 * Sensitivity analysis response
 */
export interface SensitivityAnalysisResponse {
  resume_id: string;
  vacancy_id: string;
  most_sensitive_features: SensitiveFeature[];
  sensitivity_scores: Record<string, number>;
  recommendations: string[];
  analysis_timestamp: string;
}

/**
 * Compare candidates request
 */
export interface CompareCandidatesRequest {
  resume_a_id: string;
  resume_b_id: string;
  vacancy_id: string;
  use_llm?: boolean;
}

/**
 * Compare candidates response
 */
export interface CompareCandidatesResponse {
  vacancy_id: string;
  candidate_a_name: string;
  candidate_b_name: string;
  candidate_a_score: number;
  candidate_b_score: number;
  score_difference: number;
  narrative: string;
  key_differences: string[];
  winning_factors: string[];
  losing_factors: string[];
  recommendation: string;
  provider: string;
  model: string;
  generated_at: string;
}

/**
 * Candidate info in detailed comparison
 */
export interface CandidateInfo {
  resume_id: string;
  candidate_name: string;
  rank_score: number;
  rank_position: number | null;
  confidence: number;
}

/**
 * Factor-by-factor comparison detail
 */
export interface FactorComparison {
  factor_name: string;
  candidate_a_score: number;
  candidate_b_score: number;
  difference: number;
  winner: 'A' | 'B' | 'tie';
  explanation: string;
}

/**
 * Score differential analysis
 */
export interface ScoreDifferential {
  score_difference: number;
  score_difference_percent: number;
  higher_candidate: 'A' | 'B';
  margin_category: 'significant' | 'moderate' | 'slight';
}

/**
 * Strengths and weaknesses comparison table
 */
export interface StrengthsWeaknessesTable {
  candidate_a_strengths: string[];
  candidate_b_strengths: string[];
  candidate_a_weaknesses: string[];
  candidate_b_weaknesses: string[];
}

/**
 * Detailed comparison response
 */
export interface DetailedCompareResponse {
  vacancy_id: string;
  candidate_a_info: CandidateInfo;
  candidate_b_info: CandidateInfo;
  score_differential: ScoreDifferential;
  factor_by_factor_comparison: FactorComparison[];
  winner_narrative: string;
  key_differences: string[];
  strengths_weaknesses_table: StrengthsWeaknessesTable;
  recommendation: string;
  provider: string;
  model: string;
  generated_at: string;
}

/**
 * Confidence interval response
 */
export interface ConfidenceIntervalResponse {
  rank_id: string;
  confidence_interval: ConfidenceInterval;
}

/**
 * Explanation preferences update request
 */
export interface ExplanationPreferencesUpdate {
  tone?: 'professional' | 'casual' | 'friendly' | 'formal';
  style?: 'detailed' | 'concise' | 'balanced';
  detail_level?: 'high' | 'medium' | 'low';
  include_percentiles?: boolean;
  include_skill_names?: boolean;
  include_experience_details?: boolean;
  include_education_details?: boolean;
  language?: string;
  custom_prompt_template?: string;
  is_active?: boolean;
}

/**
 * Explanation preferences response
 */
export interface ExplanationPreferencesResponse {
  id: string;
  organization_id: string;
  tone: 'professional' | 'casual' | 'friendly' | 'formal';
  style: 'detailed' | 'concise' | 'balanced';
  detail_level: 'high' | 'medium' | 'low';
  include_percentiles: boolean;
  include_skill_names: boolean;
  include_experience_details: boolean;
  include_education_details: boolean;
  language: string | null;
  custom_prompt_template: string | null;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

// ==================== Client ====================

/**
 * Default API configuration
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 120000,
};

/**
 * Transform Axios error to standardized API error
 */
function transformError(error: unknown): ApiError {
  const axiosError = error as {
    response?: { status?: number; data?: { detail?: string } };
    message?: string;
  };

  return {
    detail: axiosError.response?.data?.detail ?? axiosError.message ?? 'Unknown error',
    status: axiosError.response?.status,
  };
}

/**
 * Explainability Client class
 *
 * Provides methods for AI decision transparency explanations.
 */
export class ExplainabilityClient {
  private client: AxiosInstance;

  /**
   * Create a new Explainability client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);
  }

  /**
   * Get the underlying axios instance for custom requests
   *
   * @returns Axios instance
   */
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }

  /**
   * Generate comprehensive explanation for a candidate ranking
   *
   * Provides detailed explanations including:
   * - Natural language narrative
   * - Feature contribution breakdowns
   * - Confidence intervals
   * - Candidate strengths and weaknesses
   * - Resume section highlighting
   *
   * @param request - Explanation request
   * @returns Comprehensive ranking explanation
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const explanation = await explainability.explainRanking({
   *   resume_id: 'abc-123-def',
   *   vacancy_id: 'vac-456-ghi',
   *   use_llm: true,
   * });
   * console.log(explanation.narrative);
   * console.log(explanation.feature_explanations);
   * ```
   */
  async explainRanking(
    request: ExplainRankingRequest
  ): Promise<ExplainRankingResponse> {
    try {
      const response = await this.client.post<ExplainRankingResponse>(
        '/api/explainability/explain',
        {
          resume_id: request.resume_id,
          vacancy_id: request.vacancy_id,
          use_llm: request.use_llm ?? true,
        }
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Perform what-if scenario analysis on candidate ranking
   *
   * Explores how hypothetical changes to candidate attributes
   * would affect their ranking. Useful for:
   * - Understanding feature importance
   * - Providing feedback to candidates
   * - Exploring ranking sensitivity
   *
   * Supported adjustments:
   * - experience_months: Add/remove months of experience
   * - skills_match_ratio: Adjust skills match score
   * - keyword_score: Adjust keyword matching score
   * - tfidf_score: Adjust TF-IDF score
   * - vector_score: Adjust vector similarity score
   * - education_level: Adjust education score
   *
   * @param request - What-if request with adjustments
   * @returns What-if analysis results
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const result = await explainability.whatIfAnalysis({
   *   resume_id: 'abc-123-def',
   *   vacancy_id: 'vac-456-ghi',
   *   adjustments: { experience_months: 12 },
   * });
   * console.log(`Score: ${result.original_score} → ${result.new_score}`);
   * console.log(result.explanation);
   * ```
   */
  async whatIfAnalysis(
    request: WhatIfAnalysisRequest
  ): Promise<WhatIfAnalysisResponse> {
    try {
      const response = await this.client.post<WhatIfAnalysisResponse>(
        '/api/explainability/what-if',
        request
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Analyze feature sensitivity for a candidate ranking
   *
   * Tests how much the ranking changes when each feature
   * is perturbed by a given percentage, identifying which features
   * most impact the ranking.
   *
   * @param request - Sensitivity analysis request
   * @returns Feature sensitivity analysis
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const sensitivity = await explainability.sensitivityAnalysis({
   *   resume_id: 'abc-123-def',
   *   vacancy_id: 'vac-456-ghi',
   *   perturbation_percent: 0.1,
   * });
   * console.log(sensitivity.most_sensitive_features);
   * console.log(sensitivity.recommendations);
   * ```
   */
  async sensitivityAnalysis(
    request: SensitivityAnalysisRequest
  ): Promise<SensitivityAnalysisResponse> {
    try {
      const response = await this.client.post<SensitivityAnalysisResponse>(
        '/api/explainability/sensitivity',
        {
          resume_id: request.resume_id,
          vacancy_id: request.vacancy_id,
          perturbation_percent: request.perturbation_percent ?? 0.1,
        }
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Explain why one candidate ranks higher than another
   *
   * Provides side-by-side comparison explanations, highlighting
   * the key differences between candidates.
   *
   * @param request - Comparison explanation request
   * @returns Detailed comparison explanation
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const comparison = await explainability.compareCandidates({
   *   resume_a_id: 'resume-1',
   *   resume_b_id: 'resume-2',
   *   vacancy_id: 'vacancy-123',
   *   use_llm: true,
   * });
   * console.log(comparison.narrative);
   * console.log(comparison.key_differences);
   * ```
   */
  async compareCandidates(
    request: CompareCandidatesRequest
  ): Promise<CompareCandidatesResponse> {
    try {
      const response = await this.client.post<CompareCandidatesResponse>(
        '/api/explainability/compare-explain',
        {
          resume_a_id: request.resume_a_id,
          resume_b_id: request.resume_b_id,
          vacancy_id: request.vacancy_id,
          use_llm: request.use_llm ?? true,
        }
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get detailed side-by-side comparison of two candidates
   *
   * Provides comprehensive comparison analysis with:
   * - Score differential breakdown
   * - Factor-by-factor comparison
   * - Natural language winner narrative
   * - Strengths and weaknesses comparison
   * - Hiring recommendations
   *
   * @param request - Comparison request with candidate and vacancy IDs
   * @returns Detailed comparison analysis
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const comparison = await explainability.getDetailedComparison({
   *   resume_a_id: 'resume-1',
   *   resume_b_id: 'resume-2',
   *   vacancy_id: 'vacancy-123',
   *   use_llm: true,
   * });
   * console.log(comparison.winner_narrative);
   * console.log(comparison.factor_by_factor_comparison);
   * ```
   */
  async getDetailedComparison(
    request: CompareCandidatesRequest
  ): Promise<DetailedCompareResponse> {
    try {
      const response = await this.client.post<DetailedCompareResponse>(
        '/api/explainability/compare',
        {
          resume_id_a: request.resume_a_id,
          resume_id_b: request.resume_b_id,
          vacancy_id: request.vacancy_id,
          use_llm: request.use_llm ?? true,
        }
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get confidence interval for a specific ranking
   *
   * Returns the confidence interval for a ranking prediction,
   * indicating the uncertainty range of the score.
   *
   * @param rankId - CandidateRank UUID
   * @returns Confidence interval with bounds
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const confidence = await explainability.getConfidenceInterval('rank-123');
   * console.log(`Range: ${confidence.confidence_interval.lower_bound} - ${confidence.confidence_interval.upper_bound}`);
   * ```
   */
  async getConfidenceInterval(
    rankId: string
  ): Promise<ConfidenceIntervalResponse> {
    try {
      const response = await this.client.get<ConfidenceIntervalResponse>(
        `/api/explainability/confidence/${rankId}`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get explanation preferences for an organization
   *
   * Retrieves the explanation preferences for a specific organization,
   * including tone, style, detail level, and content inclusion flags.
   * Returns default preferences if none exist for the organization.
   *
   * @param organizationId - Organization identifier (slug or UUID)
   * @returns Organization explanation preferences
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const preferences = await explainability.getOrganizationPreferences('test-org');
   * console.log(`Tone: ${preferences.tone}`);
   * console.log(`Style: ${preferences.style}`);
   * ```
   */
  async getOrganizationPreferences(
    organizationId: string
  ): Promise<ExplanationPreferencesResponse> {
    try {
      const response = await this.client.get<ExplanationPreferencesResponse>(
        `/api/explainability/preferences/${organizationId}`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Update explanation preferences for an organization
   *
   * Updates the explanation preferences for a specific organization.
   * Only the fields specified in the request body will be updated.
   * Creates new preferences if none exist for the organization.
   *
   * @param organizationId - Organization identifier (slug or UUID)
   * @param request - Request body containing fields to update
   * @returns Updated organization explanation preferences
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const updated = await explainability.updateOrganizationPreferences('test-org', {
   *   tone: 'casual',
   *   style: 'concise',
   *   is_active: true,
   * });
   * console.log(`Updated tone: ${updated.tone}`);
   * ```
   */
  async updateOrganizationPreferences(
    organizationId: string,
    request: ExplanationPreferencesUpdate
  ): Promise<ExplanationPreferencesResponse> {
    try {
      const response = await this.client.put<ExplanationPreferencesResponse>(
        `/api/explainability/preferences/${organizationId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }
}

/**
 * Default explainability client instance
 *
 * Use this singleton instance for all explainability API calls.
 */
export const explainability = new ExplainabilityClient();

/**
 * Export explainability client class for custom instances
 */
export default ExplainabilityClient;
