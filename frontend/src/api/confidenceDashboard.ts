/**
 * Confidence Dashboard API Client
 *
 * This module provides a convenient interface for the AI Confidence Scoring
 * & Transparency Dashboard, including confidence metrics, model accuracy trends,
 * AI vs human comparisons, and confidence report export functionality.
 *
 * @example
 * ```ts
 * import { confidenceDashboard } from '@/api/confidenceDashboard';
 *
 * // Get confidence metrics
 * const metrics = await confidenceDashboard.getConfidenceMetrics({
 *   start_date: '2024-01-01T00:00:00Z',
 *   end_date: '2024-03-21T00:00:00Z',
 *   vacancy_id: 'vac-123',
 * });
 *
 * // Get model accuracy trend
 * const trend = await confidenceDashboard.getModelAccuracyTrend({
 *   period: '30d',
 *   model_name: 'skill_matching',
 * });
 *
 * // Get AI vs human comparison
 * const comparison = await confidenceDashboard.getAIHumanComparison({
 *   start_date: '2024-01-01T00:00:00Z',
 * });
 *
 * // Export confidence report
 * const report = await confidenceDashboard.exportConfidenceReport({
 *   format: 'csv',
 *   start_date: '2024-01-01T00:00:00Z',
 *   include_metadata: true,
 * });
 * ```
 */

import axios, { AxiosInstance } from 'axios';
import type { ApiError } from '@/types/api';

// ==================== Types ====================

/**
 * Confidence score distribution across different ranges
 */
export interface ConfidenceDistribution {
  high_confidence: number;
  medium_confidence: number;
  low_confidence: number;
  high_confidence_percentage: number;
  medium_confidence_percentage: number;
  low_confidence_percentage: number;
}

/**
 * Indicators for model uncertainty and edge cases
 */
export interface UncertaintyIndicators {
  low_confidence_count: number;
  high_uncertainty_count: number;
  average_confidence_interval_width: number;
  flagged_for_review: number;
}

/**
 * Summary of model accuracy based on historical performance
 */
export interface ModelAccuracySummary {
  overall_accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  total_predictions: number;
  feedback_count: number;
}

/**
 * Response model for confidence dashboard metrics
 */
export interface ConfidenceMetricsResponse {
  average_confidence: number;
  median_confidence: number;
  min_confidence: number;
  max_confidence: number;
  total_rankings: number;
  distribution: ConfidenceDistribution;
  uncertainty: UncertaintyIndicators;
  model_accuracy: ModelAccuracySummary;
}

/**
 * Request parameters for confidence metrics
 */
export interface ConfidenceMetricsRequest {
  start_date?: string;
  end_date?: string;
  vacancy_id?: string;
}

/**
 * Single data point in model accuracy trend
 */
export interface ModelAccuracyDataPoint {
  timestamp: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  sample_size: number;
}

/**
 * Model accuracy trend over time
 */
export interface ModelAccuracyTrendResponse {
  model_name: string;
  period: string;
  data_points: ModelAccuracyDataPoint[];
  summary: {
    avg_accuracy: number;
    avg_f1_score: number;
    trend: string;
    total_samples: number;
  };
}

/**
 * Request parameters for model accuracy trend
 */
export interface ModelAccuracyTrendRequest {
  period?: string;
  model_name?: string;
}

/**
 * AI vs Human agreement metrics
 */
export interface AgreementMetrics {
  agreement_rate: number;
  total_comparisons: number;
  ai_correct_count: number;
  human_override_count: number;
  human_override_correct: number;
}

/**
 * Efficiency and time-saving metrics from AI recommendations
 */
export interface EfficiencyMetrics {
  avg_time_saved_hours: number;
  total_time_saved_hours: number;
  automation_rate: number;
  manual_review_rate: number;
}

/**
 * Correlation between AI confidence and actual accuracy
 */
export interface ConfidenceCorrelation {
  high_confidence_accuracy: number;
  medium_confidence_accuracy: number;
  low_confidence_accuracy: number;
  correlation_coefficient: number;
}

/**
 * Response model for AI vs human recruiter comparison
 */
export interface AIHumanComparisonResponse {
  agreement: AgreementMetrics;
  efficiency: EfficiencyMetrics;
  confidence_correlation: ConfidenceCorrelation;
  recommendations: string[];
}

/**
 * Request parameters for AI vs human comparison
 */
export interface AIHumanComparisonRequest {
  start_date?: string;
  end_date?: string;
  vacancy_id?: string;
}

/**
 * Supported export formats for confidence report data
 */
export enum ConfidenceExportFormat {
  JSON = 'json',
  CSV = 'csv',
}

/**
 * Request model for confidence report data export
 */
export interface ConfidenceExportRequest {
  format?: ConfidenceExportFormat;
  start_date?: string;
  end_date?: string;
  vacancy_id?: string;
  include_metadata?: boolean;
}

/**
 * Metadata about a confidence report export
 */
export interface ConfidenceExportMetadata {
  export_timestamp: string;
  format: string;
  start_date?: string;
  end_date?: string;
  total_records: number;
  filters_applied: {
    vacancy_id?: string;
  };
}

/**
 * Response model for confidence report export
 */
export interface ConfidenceExportResponse {
  format: string;
  data: any;
  metadata?: ConfidenceExportMetadata;
}

// ==================== API Client Class ====================

/**
 * Confidence Dashboard API client
 */
class ConfidenceDashboardClient {
  private client: AxiosInstance;

  constructor(baseURL: string = '/api') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Get aggregated confidence metrics for the transparency dashboard
   *
   * @param params - Request parameters (optional filters)
   * @returns Confidence metrics response
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const metrics = await confidenceDashboard.getConfidenceMetrics({
   *   start_date: '2024-01-01T00:00:00Z',
   *   vacancy_id: 'vac-123',
   * });
   * console.log(`Average confidence: ${metrics.average_confidence}`);
   * ```
   */
  async getConfidenceMetrics(
    params?: ConfidenceMetricsRequest
  ): Promise<ConfidenceMetricsResponse> {
    try {
      const response = await this.client.get<ConfidenceMetricsResponse>(
        '/confidence-dashboard/metrics',
        { params }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const apiError: ApiError = {
          detail: error.response?.data?.detail || error.message,
          status: error.response?.status,
        };
        throw apiError;
      }
      throw error;
    }
  }

  /**
   * Get model accuracy trends with historical performance data
   *
   * @param params - Request parameters (period, model_name)
   * @returns Model accuracy trend response
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const trend = await confidenceDashboard.getModelAccuracyTrend({
   *   period: '30d',
   *   model_name: 'skill_matching',
   * });
   * console.log(`Average accuracy: ${trend.summary.avg_accuracy}`);
   * ```
   */
  async getModelAccuracyTrend(
    params?: ModelAccuracyTrendRequest
  ): Promise<ModelAccuracyTrendResponse> {
    try {
      const response = await this.client.get<ModelAccuracyTrendResponse>(
        '/analytics/model-accuracy-trend',
        { params }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const apiError: ApiError = {
          detail: error.response?.data?.detail || error.message,
          status: error.response?.status,
        };
        throw apiError;
      }
      throw error;
    }
  }

  /**
   * Get AI vs human recruiter comparison metrics
   *
   * @param params - Request parameters (optional filters)
   * @returns AI vs human comparison response
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const comparison = await confidenceDashboard.getAIHumanComparison({
   *   start_date: '2024-01-01T00:00:00Z',
   * });
   * console.log(`Agreement rate: ${comparison.agreement.agreement_rate}`);
   * ```
   */
  async getAIHumanComparison(
    params?: AIHumanComparisonRequest
  ): Promise<AIHumanComparisonResponse> {
    try {
      const response = await this.client.get<AIHumanComparisonResponse>(
        '/confidence-dashboard/ai-human-comparison',
        { params }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const apiError: ApiError = {
          detail: error.response?.data?.detail || error.message,
          status: error.response?.status,
        };
        throw apiError;
      }
      throw error;
    }
  }

  /**
   * Export confidence report data in CSV or JSON format
   *
   * @param request - Export request with format and filters
   * @returns Exported confidence report
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const report = await confidenceDashboard.exportConfidenceReport({
   *   format: ConfidenceExportFormat.CSV,
   *   start_date: '2024-01-01T00:00:00Z',
   *   include_metadata: true,
   * });
   * console.log(`Exported ${report.metadata?.total_records} records`);
   * ```
   */
  async exportConfidenceReport(
    request: ConfidenceExportRequest
  ): Promise<ConfidenceExportResponse> {
    try {
      const response = await this.client.post<ConfidenceExportResponse>(
        '/confidence-dashboard/export',
        request
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const apiError: ApiError = {
          detail: error.response?.data?.detail || error.message,
          status: error.response?.status,
        };
        throw apiError;
      }
      throw error;
    }
  }
}

// ==================== Export ====================

/**
 * Default confidence dashboard client instance
 *
 * Use this singleton instance for all confidence dashboard API calls.
 */
export const confidenceDashboard = new ConfidenceDashboardClient();

/**
 * Export confidence dashboard client class for custom instances
 */
export default ConfidenceDashboardClient;
