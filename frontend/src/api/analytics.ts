/**
 * API Usage Analytics Client
 *
 * Provides methods for retrieving API usage analytics including
 * request counts, response times, error rates, and endpoint usage statistics.
 *
 * @module api/analytics
 */

import { ApiClient } from './client';
import type { ApiError } from '@/types/api';

/**
 * API request status
 */
export enum APIRequestStatus {
  Success = 'success',
  RateLimited = 'rate_limited',
  Unauthorized = 'unauthorized',
  Forbidden = 'forbidden',
  NotFound = 'not_found',
  ServerError = 'server_error',
  ValidationError = 'validation_error',
}

/**
 * API usage metrics summary
 */
export interface APIUsageSummary {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  rate_limited_requests: number;
  average_response_time_ms: number;
  p95_response_time_ms: number;
  p99_response_time_ms: number;
  unique_endpoints: number;
  date_range: {
    start_date: string;
    end_date: string;
  };
}

/**
 * Request count by time period
 */
export interface RequestCountByTime {
  timestamp: string;
  count: number;
  success_count: number;
  error_count: number;
}

/**
 * Response time metrics
 */
export interface ResponseTimeMetrics {
  timestamp: string;
  average_ms: number;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
}

/**
 * Endpoint usage statistics
 */
export interface EndpointUsage {
  endpoint: string;
  method: string;
  request_count: number;
  success_count: number;
  error_count: number;
  average_response_time_ms: number;
  error_rate: number;
}

/**
 * Status code distribution
 */
export interface StatusCodeDistribution {
  status_code: number;
  count: number;
  percentage: number;
}

/**
 * Top errors by frequency
 */
export interface TopError {
  status_code: number;
  endpoint: string;
  method: string;
  count: number;
  last_occurred: string;
}

/**
 * API usage analytics response
 */
export interface APIUsageAnalytics {
  summary: APIUsageSummary;
  requests_by_time: RequestCountByTime[];
  response_times: ResponseTimeMetrics[];
  top_endpoints: EndpointUsage[];
  status_codes: StatusCodeDistribution[];
  top_errors: TopError[];
}

// ==================== AI Explainability Types ====================

/**
 * Confidence interval for model predictions
 */
export interface ConfidenceIntervalStats {
  lower: number;
  upper: number;
  confidence_level: number;
}

/**
 * Confidence distribution counts
 */
export interface ConfidenceDistribution {
  high_confidence_count: number;
  medium_confidence_count: number;
  low_confidence_count: number;
}

/**
 * Model confidence response
 */
export interface ModelConfidenceResponse {
  average_confidence: number;
  confidence_interval: ConfidenceIntervalStats;
  distribution: ConfidenceDistribution;
  confidence_accuracy_correlation: number;
}

/**
 * Feature importance item
 */
export interface FeatureImportanceItem {
  name: string;
  importance: number;
  description: string;
}

/**
 * Feature importance response
 */
export interface FeatureImportanceResponse {
  features: FeatureImportanceItem[];
  model_version: string;
  model_type: string;
}

/**
 * Feature contribution for ranking rationale
 */
export interface FeatureContribution {
  name: string;
  value: number;
  contribution: number;
  impact: 'positive' | 'negative';
}

/**
 * Ranking rationale confidence interval
 */
export interface RationaleConfidenceInterval {
  lower: number;
  upper: number;
}

/**
 * Ranking rationale response
 */
export interface RankingRationaleResponse {
  candidate_id: string;
  rank_score: number;
  rank_position: number;
  narrative: string;
  feature_contributions: FeatureContribution[];
  strengths: string[];
  weaknesses: string[];
  confidence_interval: RationaleConfidenceInterval;
}

/**
 * Performance metrics for a single time point
 */
export interface PerformanceMetricPoint {
  date: string;
  accuracy: number;
  f1_score: number;
  ndcg_score: number;
  sample_size: number;
}

/**
 * Aggregated performance metrics
 */
export interface PerformanceAggregates {
  avg_accuracy: number;
  avg_f1: number;
  accuracy_change_pct: number;
}

/**
 * Performance trends response
 */
export interface PerformanceTrendsResponse {
  period: string;
  trend_direction: 'improving' | 'stable' | 'declining';
  metrics: PerformanceMetricPoint[];
  aggregates: PerformanceAggregates;
}

/**
 * Analytics Client
 *
 * Handles API usage analytics retrieval operations.
 */
export class AnalyticsClient {
  /**
   * @param apiClient - The API client instance
   */
  constructor(private apiClient: ApiClient) {}

  /**
   * Get API usage analytics
   *
   * @param startDate - Optional start date for filtering (ISO 8601 format)
   * @param endDate - Optional end date for filtering (ISO 8601 format)
   * @param interval - Time interval for aggregation (hour, day, week)
   * @returns API usage analytics data
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const analytics = await analyticsClient.getAPIUsageAnalytics();
   * ```
   *
   * @example
   * ```ts
   * const analytics = await analyticsClient.getAPIUsageAnalytics(
   *   '2024-01-01',
   *   '2024-12-31',
   *   'day'
   * );
   * ```
   */
  async getAPIUsageAnalytics(
    startDate?: string,
    endDate?: string,
    interval: 'hour' | 'day' | 'week' = 'day'
  ): Promise<APIUsageAnalytics> {
    try {
      const params: Record<string, string> = { interval };
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response = await this.apiClient.getAxiosInstance().get<APIUsageAnalytics>(
        '/api/analytics/api-usage',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get usage summary for a specific API key
   *
   * @param apiKeyId - API key UUID
   * @param startDate - Optional start date for filtering (ISO 8601 format)
   * @param endDate - Optional end date for filtering (ISO 8601 format)
   * @returns API usage summary for the key
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const summary = await analyticsClient.getAPIKeyUsage('key-uuid');
   * ```
   */
  async getAPIKeyUsage(
    apiKeyId: string,
    startDate?: string,
    endDate?: string
  ): Promise<APIUsageSummary> {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response = await this.apiClient.getAxiosInstance().get<APIUsageSummary>(
        `/api/analytics/api-usage/keys/${apiKeyId}`,
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== AI Explainability Methods ====================

  /**
   * Get model confidence statistics
   *
   * Returns model confidence distribution and statistics including
   * average confidence, confidence intervals, and distribution breakdown.
   *
   * @returns Model confidence statistics
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const confidence = await analyticsClient.getModelConfidence();
   * console.log(`Average: ${confidence.average_confidence}`);
   * console.log(`High confidence: ${confidence.distribution.high_confidence_count}`);
   * ```
   */
  async getModelConfidence(): Promise<ModelConfidenceResponse> {
    try {
      const response = await this.apiClient
        .getAxiosInstance()
        .get<ModelConfidenceResponse>('/api/analytics/ai-explainability/confidence');
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get feature importance from the trained model
   *
   * Returns feature importance scores for all ranking features,
   * showing which factors most influence candidate rankings.
   *
   * @returns Feature importance data with descriptions
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const importance = await analyticsClient.getFeatureImportance();
   * importance.features.forEach(f => {
   *   console.log(`${f.name}: ${(f.importance * 100).toFixed(1)}%`);
   * });
   * ```
   */
  async getFeatureImportance(): Promise<FeatureImportanceResponse> {
    try {
      const response = await this.apiClient
        .getAxiosInstance()
        .get<FeatureImportanceResponse>('/api/analytics/ai-explainability/feature-importance');
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get ranking rationale for a specific candidate
   *
   * Provides detailed explanation of why a candidate received their ranking,
   * including feature contributions, strengths, weaknesses, and confidence interval.
   *
   * @param candidateId - Candidate UUID
   * @returns Detailed ranking rationale
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const rationale = await analyticsClient.getRankingRationale('candidate-uuid');
   * console.log(`Score: ${rationale.rank_score}`);
   * console.log(`Narrative: ${rationale.narrative}`);
   * ```
   */
  async getRankingRationale(candidateId: string): Promise<RankingRationaleResponse> {
    try {
      const response = await this.apiClient
        .getAxiosInstance()
        .get<RankingRationaleResponse>(
          `/api/analytics/ai-explainability/ranking-rationale/${candidateId}`
        );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get model performance trends over time
   *
   * Returns time-series performance metrics (accuracy, F1, NDCG) with
   * trend analysis and aggregated statistics.
   *
   * @param period - Time period for analysis ("7d", "30d", or "90d")
   * @param startDate - Optional start date for filtering (ISO 8601 format)
   * @param endDate - Optional end date for filtering (ISO 8601 format)
   * @returns Performance trends with metrics and aggregates
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const trends = await analyticsClient.getPerformanceTrends('30d');
   * console.log(`Trend: ${trends.trend_direction}`);
   * console.log(`Avg accuracy: ${trends.aggregates.avg_accuracy}`);
   * ```
   */
  async getPerformanceTrends(
    period: '7d' | '30d' | '90d' = '30d',
    startDate?: string,
    endDate?: string
  ): Promise<PerformanceTrendsResponse> {
    try {
      const params: Record<string, string> = { period };
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response = await this.apiClient
        .getAxiosInstance()
        .get<PerformanceTrendsResponse>('/api/analytics/ai-explainability/performance-trends', {
          params,
        });
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Transform unknown error to ApiError
   */
  private transformError(error: unknown): ApiError {
    if (error && typeof error === 'object' && 'detail' in error) {
      const apiError = error as { detail: string; status?: number };
      return {
        detail: apiError.detail,
        status: apiError.status || 0,
      };
    }
    return {
      detail: error instanceof Error ? error.message : 'An unknown error occurred',
      status: 0,
    };
  }
}

/**
 * Default analytics client instance
 */
export const analyticsClient = new AnalyticsClient(
  new (require('./client').ApiClient)()
);

/**
 * Export analytics client class
 */
export default AnalyticsClient;
