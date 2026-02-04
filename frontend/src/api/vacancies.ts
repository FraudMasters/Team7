/**
 * Vacancy Search API Client
 *
 * This module provides a client for advanced vacancy search with
 * full-text search, boolean operators, and multi-field filtering.
 *
 * @example
 * ```ts
 * import { vacancySearchClient } from '@/api/vacancies';
 *
 * // Search with query and filters
 * const results = await vacancySearchClient.searchVacancies({
 *   query: 'software engineer',
 *   filters: {
 *     work_format: 'remote',
 *     employment_type: 'full-time',
 *     salary_min: 80000,
 *     salary_max: 120000
 *   },
 *   limit: 10
 * });
 *
 * // Search by location only
 * const results = await vacancySearchClient.searchVacancies({
 *   filters: {
 *     location: 'New York',
 *     work_format: 'hybrid'
 *   }
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  VacancySearchRequest,
  VacancySearchResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for vacancy search client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Vacancy Search API Client class
 *
 * Provides methods for searching vacancies with proper
 * error handling and type safety.
 */
export class VacancySearchClient {
  private client: AxiosInstance;

  /**
   * Create a new VacancySearch client instance
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
      400: 'Invalid search parameters. Please check your input.',
      401: 'Unauthorized. Please log in.',
      403: 'Forbidden. You do not have permission.',
      404: 'Resource not found.',
      422: 'Validation error. Please check your search criteria.',
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
   * Search for vacancies with advanced filters
   *
   * Supports full-text search with boolean operators (AND, OR, NOT)
   * and multi-field filtering by work format, location, salary range, employment type, etc.
   *
   * @param request - Search request with query, filters, pagination, and sorting
   * @returns Search results with vacancy list and metadata
   * @throws ApiError if search fails
   *
   * @example
   * ```ts
   * // Search with query and filters
   * const results = await vacancySearchClient.searchVacancies({
   *   query: 'software engineer',
   *   filters: {
   *     work_format: 'remote',
   *     employment_type: 'full-time',
   *     salary_min: 80000,
   *     salary_max: 120000
   *   },
   *   limit: 10,
   *   sort_by: 'date'
   * });
   *
   * // Filter by location and work format
   * const results = await vacancySearchClient.searchVacancies({
   *   filters: {
   *     location: 'New York',
   *     work_format: 'hybrid'
   *   }
   * });
   *
   * // Search with salary range only
   * const results = await vacancySearchClient.searchVacancies({
   *   filters: {
   *     salary_min: 50000,
   *     salary_max: 100000
   *   },
   *   sort_by: 'salary'
   * });
   * ```
   */
  async searchVacancies(request: VacancySearchRequest = {}): Promise<VacancySearchResponse> {
    try {
      const response: AxiosResponse<VacancySearchResponse> = await this.client.post(
        '/api/vacancies/search',
        {
          query: request.query ?? null,
          filters: request.filters ?? null,
          skip: request.skip ?? 0,
          limit: request.limit ?? 100,
          sort_by: request.sort_by ?? 'date',
        }
      );
      return response.data;
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
 * Default vacancy search client instance
 *
 * Use this singleton instance for all vacancy search calls.
 */
export const vacancySearchClient = new VacancySearchClient();

/**
 * Export vacancy search client class for custom instances
 */
export default VacancySearchClient;
