/**
 * Candidate Search API Client
 *
 * This module provides a client for advanced candidate search with
 * full-text search, boolean operators, and multi-field filtering.
 *
 * @example
 * ```ts
 * import { candidateSearchClient } from '@/api/search';
 *
 * // Search with query and filters
 * const results = await candidateSearchClient.searchCandidates({
 *   query: 'Python AND Django',
 *   filters: {
 *     min_experience_years: 3,
 *     max_experience_years: 10,
 *     location: 'Remote'
 *   },
 *   limit: 10
 * });
 *
 * // Search by skills only
 * const results = await candidateSearchClient.searchCandidates({
 *   filters: {
 *     skills: ['Python', 'FastAPI'],
 *     min_experience_years: 5
 *   }
 * });
 *
 * // Get search history
 * const history = await candidateSearchClient.getSearchHistory(0, 20);
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  CandidateSearchRequest,
  CandidateSearchResponse,
  SearchHistoryResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for candidate search client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Candidate Search API Client class
 *
 * Provides methods for searching candidates with proper
 * error handling and type safety.
 */
export class CandidateSearchClient {
  private client: AxiosInstance;

  /**
   * Create a new CandidateSearch client instance
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
   * Search for candidates with advanced filters
   *
   * Supports full-text search with boolean operators (AND, OR, NOT)
   * and multi-field filtering by skills, experience, education, location, etc.
   *
   * @param request - Search request with query, filters, pagination, and sorting
   * @returns Search results with candidate list and metadata
   * @throws ApiError if search fails
   *
   * @example
   * ```ts
   * // Search with boolean operators and filters
   * const results = await candidateSearchClient.searchCandidates({
   *   query: 'Python AND Django',
   *   filters: {
   *     min_experience_years: 3,
   *     max_experience_years: 10,
   *     location: 'Remote'
   *   },
   *   limit: 10,
   *   sort_by: 'relevance'
   * });
   *
   * // Filter by skills only
   * const results = await candidateSearchClient.searchCandidates({
   *   filters: {
   *     skills: ['Python', 'FastAPI', 'PostgreSQL'],
   *     min_experience_years: 5
   *   }
   * });
   *
   * // Search with match score range
   * const results = await candidateSearchClient.searchCandidates({
   *   filters: {
   *     min_match_score: 70,
   *     max_match_score: 100
   *   },
   *   sort_by: 'experience'
   * });
   * ```
   */
  async searchCandidates(request: CandidateSearchRequest = {}): Promise<CandidateSearchResponse> {
    try {
      const response: AxiosResponse<CandidateSearchResponse> = await this.client.post(
        '/api/search/candidates',
        {
          query: request.query ?? null,
          filters: request.filters ?? null,
          skip: request.skip ?? 0,
          limit: request.limit ?? 100,
          sort_by: request.sort_by ?? 'relevance',
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get search history with pagination
   *
   * Retrieves previously executed searches including query, filters,
   * results count, and execution time. Useful for reviewing and repeating searches.
   *
   * @param skip - Number of records to skip (pagination)
   * @param limit - Maximum number of records to return
   * @param recruiterId - Optional filter by recruiter ID
   * @returns Search history records with pagination metadata
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * // Get recent search history
   * const history = await candidateSearchClient.getSearchHistory(0, 20);
   *
   * // Get next page
   * const history = await candidateSearchClient.getSearchHistory(20, 20);
   *
   * // Get history for specific recruiter
   * const history = await candidateSearchClient.getSearchHistory(0, 50, 'recruiter-uuid');
   * ```
   */
  async getSearchHistory(
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
 * Default candidate search client instance
 *
 * Use this singleton instance for all candidate search calls.
 */
export const candidateSearchClient = new CandidateSearchClient();

/**
 * Export candidate search client class for custom instances
 */
export default CandidateSearchClient;
