/**
 * Saved Searches API Client
 *
 * This module provides a client for managing saved searches,
 * including creating, reading, updating, and deleting
 * saved search configurations.
 *
 * @example
 * ```ts
 * import { savedSearchesClient } from '@/api/savedSearches';
 *
 * // List all saved searches
 * const searches = await savedSearchesClient.listSavedSearches();
 *
 * // Create a new saved search
 * const newSearch = await savedSearchesClient.createSavedSearch({
 *   name: 'Senior Python Developers',
 *   query: 'Python AND Django',
 *   filters: { min_experience_years: 5 }
 * });
 *
 * // Update a saved search
 * const updated = await savedSearchesClient.updateSavedSearch('search-id', {
 *   name: 'Updated Search Name'
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import { config } from '@/config';
import type {
  SavedSearchCreate,
  SavedSearchUpdate,
  SavedSearchResponse,
  SavedSearchListResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for saved searches client
 */
const DEFAULT_CONFIG = {
  baseURL: config.api.url,
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Saved Searches API Client class
 *
 * Provides methods for managing saved search configurations with proper
 * error handling and type safety.
 */
export class SavedSearchesClient {
  private client: AxiosInstance;

  /**
   * Create a new SavedSearches client instance
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
      409: 'A saved search with this name already exists.',
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
   * Create a saved search
   *
   * @param request - Create request with saved search details
   * @returns Created saved search
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const search = await savedSearchesClient.createSavedSearch({
   *   name: 'Senior Python Developers',
   *   query: 'Python AND Django',
   *   filters: { min_experience_years: 5 }
   * });
   * ```
   */
  async createSavedSearch(request: SavedSearchCreate): Promise<SavedSearchResponse> {
    try {
      const response: AxiosResponse<SavedSearchResponse> = await this.client.post(
        '/api/saved-searches/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List saved searches with optional filters
   *
   * @param skip - Number of records to skip (pagination)
   * @param limit - Maximum number of records to return
   * @param search - Optional filter by name (case-insensitive partial match)
   * @returns List of saved searches
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all saved searches
   * const searches = await savedSearchesClient.listSavedSearches();
   *
   * // Search by name
   * const pythonSearches = await savedSearchesClient.listSavedSearches(0, 100, 'python');
   * ```
   */
  async listSavedSearches(
    skip: number = 0,
    limit: number = 100,
    search?: string
  ): Promise<SavedSearchListResponse> {
    try {
      const params: Record<string, number | string> = { skip, limit };
      if (search) params.search = search;

      const response: AxiosResponse<SavedSearchListResponse> = await this.client.get(
        '/api/saved-searches/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific saved search by ID
   *
   * @param savedSearchId - Saved search ID
   * @returns Saved search details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const search = await savedSearchesClient.getSavedSearch('search-uuid');
   * ```
   */
  async getSavedSearch(savedSearchId: string): Promise<SavedSearchResponse> {
    try {
      const response: AxiosResponse<SavedSearchResponse> = await this.client.get(
        `/api/saved-searches/${savedSearchId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a saved search
   *
   * @param savedSearchId - Saved search ID
   * @param request - Update request with fields to modify
   * @returns Updated saved search
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await savedSearchesClient.updateSavedSearch('search-uuid', {
   *   name: 'Updated Search Name',
   *   query: 'Python OR Django'
   * });
   * ```
   */
  async updateSavedSearch(
    savedSearchId: string,
    request: SavedSearchUpdate
  ): Promise<SavedSearchResponse> {
    try {
      const response: AxiosResponse<SavedSearchResponse> = await this.client.put(
        `/api/saved-searches/${savedSearchId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a saved search
   *
   * @param savedSearchId - Saved search ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await savedSearchesClient.deleteSavedSearch('search-uuid');
   * ```
   */
  async deleteSavedSearch(savedSearchId: string): Promise<void> {
    try {
      await this.client.delete(`/api/saved-searches/${savedSearchId}`);
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
 * Default saved searches client instance
 *
 * Use this singleton instance for all saved searches calls.
 */
export const savedSearchesClient = new SavedSearchesClient();

/**
 * Export saved searches client class for custom instances
 */
export default SavedSearchesClient;
