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
