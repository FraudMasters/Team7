/**
 * Search History API Client
 *
 * This module provides a client for managing search history,
 * including retrieving and clearing search history records.
 *
 * @example
 * ```ts
 * import { searchHistoryClient } from '@/api/searchHistory';
 *
 * // List search history
 * const history = await searchHistoryClient.listSearchHistory();
 *
 * // Get search history with pagination
 * const history = await searchHistoryClient.listSearchHistory(0, 20);
 *
 * // Clear all search history
 * await searchHistoryClient.clearSearchHistory();
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import { config } from '@/config';
import type {
  SearchHistoryResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for search history client
 */
const DEFAULT_CONFIG = {
  baseURL: config.api.url,
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Search History API Client class
 *
 * Provides methods for managing search history with proper
 * error handling and type safety.
 */
export class SearchHistoryClient {
  private client: AxiosInstance;

  /**
   * Create a new SearchHistory client instance
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
   * List search history with optional pagination
   *
   * @param skip - Number of records to skip (pagination)
   * @param limit - Maximum number of records to return
   * @param recruiterId - Optional filter by recruiter ID
   * @returns List of search history items
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all search history
   * const history = await searchHistoryClient.listSearchHistory();
   *
   * // Get first 20 items
   * const history = await searchHistoryClient.listSearchHistory(0, 20);
   *
   * // Get next 20 items
   * const history = await searchHistoryClient.listSearchHistory(20, 20);
   * ```
   */
  async listSearchHistory(
    skip: number = 0,
    limit: number = 50,
    recruiterId?: string
  ): Promise<SearchHistoryResponse> {
    try {
      const params: Record<string, number | string> = { skip, limit };
      if (recruiterId) params.recruiter_id = recruiterId;

      const response: AxiosResponse<SearchHistoryResponse> = await this.client.get(
        '/api/search/history',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Clear all search history
   *
   * Note: This endpoint may not be implemented in the backend yet.
   * If you get a 404 error, the backend needs to implement this endpoint.
   *
   * @throws ApiError if clearing fails
   *
   * @example
   * ```ts
   * await searchHistoryClient.clearSearchHistory();
   * ```
   */
  async clearSearchHistory(): Promise<void> {
    try {
      await this.client.delete('/api/search/history');
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get the underlying Axios instance
   *
   * This is useful for making custom requests not covered by the convenience methods.
   *
   * @returns Axios instance
   */
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }
}

/**
 * Default search history client instance
 *
 * Use this singleton instance for all search history calls.
 */
export const searchHistoryClient = new SearchHistoryClient();

/**
 * Export search history client class for custom instances
 */
export default SearchHistoryClient;
