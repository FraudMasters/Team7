/**
 * Search Analytics API Client
 *
 * This module provides a client for accessing search analytics data,
 * including recent searches, popular searches, and zero-result searches.
 *
 * @example
 * ```ts
 * import { searchAnalyticsClient } from '@/api/searchAnalytics';
 *
 * // Get recent searches
 * const recentSearches = await searchAnalyticsClient.getRecentSearches(20);
 *
 * // Get popular searches
 * const popularSearches = await searchAnalyticsClient.getPopularSearches(10);
 *
 * // Get zero-result searches
 * const zeroResults = await searchAnalyticsClient.getZeroResultSearches(10);
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import { config } from '@/config';
import type {
  RecentSearchesResponse,
  PopularSearchesResponse,
  ZeroResultSearchesResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for search analytics client
 */
const DEFAULT_CONFIG = {
  baseURL: config.api.url,
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Search Analytics API Client class
 *
 * Provides methods for accessing search analytics data with proper
 * error handling and type safety.
 */
export class SearchAnalyticsClient {
  private client: AxiosInstance;

  /**
   * Create a new SearchAnalytics client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(this.transformError(error))
    );
  }

  /**
   * Transform Axios error to standardized API error
   *
   * @param error - Axios error
   * @returns Transformed API error
   */
  private transformError(error: unknown): ApiError {
    const axiosError = error as AxiosError<{ detail?: string }>;

    // Network error (no response)
    if (!axiosError.response) {
      if (axiosError.code === 'ECONNABORTED') {
        return {
          detail: 'Request timeout. Please check your connection and try again.',
          status: 408,
        };
      }
      return {
        detail: 'Network error. Please check your connection and try again.',
        status: 0,
      };
    }

    // Server returned error response
    const status = axiosError.response.status;
    const data = axiosError.response.data;

    // Use server's error message if available
    if (data?.detail) {
      return { detail: data.detail, status };
    }

    // Default error messages by status code
    const defaultMessages: Record<number, string> = {
      400: 'Invalid request. Please check your input.',
      401: 'Unauthorized. Please log in.',
      403: 'Forbidden. You do not have permission.',
      404: 'Resource not found.',
      422: 'Validation error. Please check your input.',
      429: 'Too many requests. Please try again later.',
      500: 'Server error. Please try again later.',
      502: 'Bad gateway. Please try again later.',
      503: 'Service unavailable. Please try again later.',
    };

    return {
      detail: data?.detail || defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * Get recent search queries
   *
   * @param limit - Maximum number of searches to return (default: 20, max: 100)
   * @param skip - Number of records to skip for pagination (default: 0)
   * @returns List of recent search queries
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * // Get 10 most recent searches
   * const searches = await searchAnalyticsClient.getRecentSearches(10);
   *
   * // Get next page
   * const moreSearches = await searchAnalyticsClient.getRecentSearches(10, 10);
   * ```
   */
  async getRecentSearches(
    limit: number = 20,
    skip: number = 0
  ): Promise<RecentSearchesResponse> {
    try {
      const response: AxiosResponse<RecentSearchesResponse> = await this.client.get(
        '/api/search/analytics/recent',
        {
          params: { limit, skip },
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get popular search queries
   *
   * @param limit - Maximum number of searches to return (default: 20, max: 100)
   * @param skip - Number of records to skip for pagination (default: 0)
   * @param minSearchCount - Minimum search count to be considered popular (default: 2)
   * @returns List of popular search queries
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * // Get 10 most popular searches
   * const searches = await searchAnalyticsClient.getPopularSearches(10);
   *
   * // Get popular searches with at least 5 occurrences
   * const veryPopular = await searchAnalyticsClient.getPopularSearches(10, 0, 5);
   * ```
   */
  async getPopularSearches(
    limit: number = 20,
    skip: number = 0,
    minSearchCount: number = 2
  ): Promise<PopularSearchesResponse> {
    try {
      const response: AxiosResponse<PopularSearchesResponse> = await this.client.get(
        '/api/search/analytics/popular',
        {
          params: {
            limit,
            skip,
            min_search_count: minSearchCount,
          },
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get searches that returned zero results
   *
   * @param limit - Maximum number of searches to return (default: 20, max: 100)
   * @param skip - Number of records to skip for pagination (default: 0)
   * @returns List of searches with zero results
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * // Get 10 recent zero-result searches
   * const searches = await searchAnalyticsClient.getZeroResultSearches(10);
   * ```
   */
  async getZeroResultSearches(
    limit: number = 20,
    skip: number = 0
  ): Promise<ZeroResultSearchesResponse> {
    try {
      const response: AxiosResponse<ZeroResultSearchesResponse> = await this.client.get(
        '/api/search/analytics/zero-results',
        {
          params: { limit, skip },
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

/**
 * Default search analytics client instance
 *
 * Pre-configured client using default configuration.
 * Use this instance for most cases.
 *
 * @example
 * ```ts
 * import { searchAnalyticsClient } from '@/api/searchAnalytics';
 *
 * const searches = await searchAnalyticsClient.getRecentSearches();
 * ```
 */
export const searchAnalyticsClient = new SearchAnalyticsClient();
