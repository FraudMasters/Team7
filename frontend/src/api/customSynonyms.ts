/**
 * Custom Synonyms API Client
 *
 * This module provides a client for managing custom synonym CRUD operations.
 * Supports creating, listing, retrieving, updating, and deleting custom synonyms
 * for organizations.
 *
 * @example
 * ```ts
 * import { customSynonymsClient } from '@/api/customSynonyms';
 *
 * // Create new custom synonyms for an organization
 * const created = await customSynonymsClient.createCustomSynonyms({
 *   organization_id: 'org123',
 *   created_by: 'user456',
 *   synonyms: [
 *     {
 *       canonical_skill: 'React',
 *       custom_synonyms: ['ReactJS', 'React.js', 'React Framework'],
 *       context: 'web_framework',
 *       is_active: true,
 *     },
 *   ],
 * });
 *
 * // List all custom synonyms for an organization
 * const list = await customSynonymsClient.listCustomSynonyms('org123');
 *
 * // Get a specific custom synonym entry
 * const synonym = await customSynonymsClient.getCustomSynonym('synonym-123');
 *
 * // Update a custom synonym
 * const updated = await customSynonymsClient.updateCustomSynonym('synonym-123', {
 *   canonical_skill: 'React',
 *   custom_synonyms: ['ReactJS', 'React.js'],
 *   is_active: true,
 * });
 *
 * // Delete a custom synonym
 * await customSynonymsClient.deleteCustomSynonym('synonym-123');
 *
 * // Delete all custom synonyms for an organization
 * await customSynonymsClient.deleteCustomSynonymsByOrganization('org123');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import { config } from '@/config';
import type {
  CustomSynonymCreate,
  CustomSynonymUpdate,
  CustomSynonymResponse,
  CustomSynonymListResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for custom synonyms client
 */
const DEFAULT_CONFIG = {
  baseURL: config.api.url,
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * List options for custom synonyms
 */
export interface ListCustomSynonymsOptions {
  organization_id?: string;
  canonical_skill?: string;
  is_active?: boolean;
}

/**
 * Custom Synonyms API Client class
 *
 * Provides methods for managing custom synonyms with proper error handling
 * and type safety.
 */
export class CustomSynonymsClient {
  private client: AxiosInstance;

  /**
   * Create a new Custom Synonyms client instance
   *
   * @param configOverride - Optional configuration overrides
   */
  constructor(configOverride: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...configOverride };

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
   * Create custom synonym entries for an organization
   *
   * @param data - Custom synonym creation request
   * @returns Created synonym entries
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const result = await customSynonymsClient.createCustomSynonyms({
   *   organization_id: 'org123',
   *   created_by: 'user456',
   *   synonyms: [
   *     {
   *       canonical_skill: 'React',
   *       custom_synonyms: ['ReactJS', 'React.js', 'React Framework'],
   *       context: 'web_framework',
   *       is_active: true,
   *     },
   *   ],
   * });
   * ```
   */
  async createCustomSynonyms(
    data: CustomSynonymCreate
  ): Promise<CustomSynonymListResponse> {
    try {
      const response: AxiosResponse<CustomSynonymListResponse> =
        await this.client.post('/api/custom-synonyms/', data);
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List custom synonyms with optional filters
   *
   * @param options - List options including organization_id, canonical_skill, and is_active filters
   * @returns List of custom synonym entries
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all custom synonyms for an organization
   * const list = await customSynonymsClient.listCustomSynonyms({
   *   organization_id: 'org123',
   * });
   *
   * // Filter by canonical skill and active status
   * const filtered = await customSynonymsClient.listCustomSynonyms({
   *   organization_id: 'org123',
   *   canonical_skill: 'React',
   *   is_active: true,
   * });
   * ```
   */
  async listCustomSynonyms(
    options: ListCustomSynonymsOptions = {}
  ): Promise<CustomSynonymListResponse[]> {
    try {
      const { organization_id, canonical_skill, is_active } = options;

      const params: Record<string, string | boolean> = {};

      if (organization_id) {
        params.organization_id = organization_id;
      }
      if (canonical_skill) {
        params.canonical_skill = canonical_skill;
      }
      if (is_active !== undefined) {
        params.is_active = is_active;
      }

      const response: AxiosResponse<CustomSynonymListResponse[]> =
        await this.client.get('/api/custom-synonyms/', { params });
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific custom synonym entry by ID
   *
   * @param id - Synonym entry ID
   * @returns Custom synonym entry
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const synonym = await customSynonymsClient.getCustomSynonym('synonym-123');
   * console.log(synonym.canonical_skill, synonym.custom_synonyms);
   * ```
   */
  async getCustomSynonym(id: string): Promise<CustomSynonymResponse> {
    try {
      const response: AxiosResponse<CustomSynonymResponse> =
        await this.client.get(`/api/custom-synonyms/${id}`);
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a custom synonym entry
   *
   * @param id - Synonym entry ID
   * @param data - Update request
   * @returns Updated synonym entry
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await customSynonymsClient.updateCustomSynonym(
   *   'synonym-123',
   *   {
   *     canonical_skill: 'React',
   *     custom_synonyms: ['ReactJS', 'React.js'],
   *     is_active: true,
   *   }
   * );
   * ```
   */
  async updateCustomSynonym(
    id: string,
    data: CustomSynonymUpdate
  ): Promise<CustomSynonymResponse> {
    try {
      const response: AxiosResponse<CustomSynonymResponse> =
        await this.client.put(`/api/custom-synonyms/${id}`, data);
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a specific custom synonym entry
   *
   * @param id - Synonym entry ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await customSynonymsClient.deleteCustomSynonym('synonym-123');
   * ```
   */
  async deleteCustomSynonym(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/custom-synonyms/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete all custom synonyms for an organization
   *
   * @param organizationId - Organization ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await customSynonymsClient.deleteCustomSynonymsByOrganization('org123');
   * ```
   */
  async deleteCustomSynonymsByOrganization(organizationId: string): Promise<void> {
    try {
      await this.client.delete(`/api/custom-synonyms/organization/${organizationId}`);
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
 * Default custom synonyms client instance
 *
 * Use this singleton instance for all custom synonym operations.
 */
export const customSynonymsClient = new CustomSynonymsClient();

/**
 * Export custom synonyms client class for custom instances
 */
export default CustomSynonymsClient;
