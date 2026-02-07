/**
 * Skill Taxonomies API Client
 *
 * This module provides a client for managing skill taxonomy CRUD operations.
 * Supports creating, listing, retrieving, updating, and deleting skill taxonomies
 * by industry.
 *
 * @example
 * ```ts
 * import { skillTaxonomiesClient } from '@/api/skillTaxonomies';
 *
 * // Create new skill taxonomies for an industry
 * const created = await skillTaxonomiesClient.createSkillTaxonomies({
 *   industry: 'healthcare',
 *   skills: [
 *     {
 *       name: 'Patient Care',
 *       variants: ['patient care', 'caregiving', 'patient support'],
 *       is_active: true,
 *     },
 *   ],
 * });
 *
 * // List all skill taxonomies for an industry
 * const list = await skillTaxonomiesClient.listSkillTaxonomies('healthcare');
 *
 * // Get a specific skill taxonomy
 * const skill = await skillTaxonomiesClient.getSkillTaxonomy('skill-123');
 *
 * // Update a skill taxonomy
 * const updated = await skillTaxonomiesClient.updateSkillTaxonomy('skill-123', {
 *   skill_name: 'Advanced Patient Care',
 *   is_active: true,
 * });
 *
 * // Delete a skill taxonomy
 * await skillTaxonomiesClient.deleteSkillTaxonomy('skill-123');
 *
 * // Delete all skill taxonomies for an industry
 * await skillTaxonomiesClient.deleteSkillTaxonomiesByIndustry('healthcare');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import { config } from '@/config';
import type {
  SkillTaxonomyCreate,
  SkillTaxonomyUpdate,
  SkillTaxonomyResponse,
  SkillTaxonomyListResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for skill taxonomies client
 */
const DEFAULT_CONFIG = {
  baseURL: config.api.url,
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * List options for skill taxonomies
 */
export interface ListSkillTaxonomiesOptions {
  skip?: number;
  limit?: number;
  is_active?: boolean;
}

/**
 * Skill Taxonomies API Client class
 *
 * Provides methods for managing skill taxonomies with proper error handling
 * and type safety.
 */
export class SkillTaxonomiesClient {
  private client: AxiosInstance;

  /**
   * Create a new Skill Taxonomies client instance
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
   * Create new skill taxonomies for an industry
   *
   * @param data - Skill taxonomy creation request
   * @returns Created skill taxonomies
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const result = await skillTaxonomiesClient.createSkillTaxonomies({
   *   industry: 'healthcare',
   *   skills: [
   *     {
   *       name: 'Patient Care',
   *       context: 'clinical',
   *       variants: ['patient care', 'caregiving'],
   *       metadata: { category: 'clinical' },
   *       is_active: true,
   *     },
   *   ],
   * });
   * ```
   */
  async createSkillTaxonomies(
    data: SkillTaxonomyCreate
  ): Promise<SkillTaxonomyListResponse> {
    try {
      const response: AxiosResponse<SkillTaxonomyListResponse> =
        await this.client.post('/api/skill-taxonomies/', data);
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List skill taxonomies for an industry
   *
   * @param industry - Industry identifier
   * @param options - List options including pagination and filters
   * @returns List of skill taxonomies
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all active skills for healthcare industry
   * const list = await skillTaxonomiesClient.listSkillTaxonomies(
   *   'healthcare',
   *   { is_active: true, limit: 100 }
   * );
   *
   * // Pagination
   * const page2 = await skillTaxonomiesClient.listSkillTaxonomies(
   *   'healthcare',
   *   { skip: 100, limit: 100 }
   * );
   * ```
   */
  async listSkillTaxonomies(
    industry: string,
    options: ListSkillTaxonomiesOptions = {}
  ): Promise<SkillTaxonomyListResponse> {
    try {
      const { skip = 0, limit = 100, is_active } = options;

      const params: Record<string, number | boolean | string> = {
        industry,
        skip,
        limit,
      };

      if (is_active !== undefined) {
        params.is_active = is_active;
      }

      const response: AxiosResponse<SkillTaxonomyListResponse> =
        await this.client.get('/api/skill-taxonomies/', { params });
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific skill taxonomy by ID
   *
   * @param id - Skill taxonomy ID
   * @returns Skill taxonomy details
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const skill = await skillTaxonomiesClient.getSkillTaxonomy('skill-123');
   * console.log(skill.skill_name, skill.variants);
   * ```
   */
  async getSkillTaxonomy(id: string): Promise<SkillTaxonomyResponse> {
    try {
      const response: AxiosResponse<SkillTaxonomyResponse> =
        await this.client.get(`/api/skill-taxonomies/${id}`);
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a skill taxonomy
   *
   * @param id - Skill taxonomy ID
   * @param data - Update request data
   * @returns Updated skill taxonomy
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await skillTaxonomiesClient.updateSkillTaxonomy(
   *   'skill-123',
   *   {
   *     skill_name: 'Advanced Patient Care',
   *     variants: ['advanced patient care', 'senior caregiving'],
   *     is_active: true,
   *   }
   * );
   * ```
   */
  async updateSkillTaxonomy(
    id: string,
    data: SkillTaxonomyUpdate
  ): Promise<SkillTaxonomyResponse> {
    try {
      const response: AxiosResponse<SkillTaxonomyResponse> =
        await this.client.put(`/api/skill-taxonomies/${id}`, data);
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a skill taxonomy
   *
   * @param id - Skill taxonomy ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await skillTaxonomiesClient.deleteSkillTaxonomy('skill-123');
   * ```
   */
  async deleteSkillTaxonomy(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/skill-taxonomies/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete all skill taxonomies for an industry
   *
   * @param industry - Industry identifier
   * @returns Deletion result with count
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * const result = await skillTaxonomiesClient.deleteSkillTaxonomiesByIndustry('healthcare');
   * console.log(`Deleted ${result.deleted_count} skills`);
   * ```
   */
  async deleteSkillTaxonomiesByIndustry(
    industry: string
  ): Promise<{ deleted_count: number; industry: string }> {
    try {
      const response: AxiosResponse<{ deleted_count: number; industry: string }> =
        await this.client.delete(`/api/skill-taxonomies/industry/${industry}`);
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
 * Default skill taxonomies client instance
 *
 * Use this singleton instance for all skill taxonomy operations.
 */
export const skillTaxonomiesClient = new SkillTaxonomiesClient();

/**
 * Export skill taxonomies client class for custom instances
 */
export default SkillTaxonomiesClient;
