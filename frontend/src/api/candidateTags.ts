/**
 * Candidate Tags API Client
 *
 * This module provides a client for managing organization-specific candidate tags,
 * including creating, reading, updating, and deleting tag configurations, as well as
 * assigning and removing tags from candidates (resumes). Tags enable flexible
 * categorization and prioritization (e.g., 'High Priority', 'Remote', 'Referral').
 *
 * @example
 * ```ts
 * import { candidateTagsClient } from '@/api/candidateTags';
 *
 * // List all tags for an organization
 * const tags = await candidateTagsClient.listTags('org-123');
 *
 * // Create a new tag
 * const newTag = await candidateTagsClient.createTag({
 *   organization_id: 'org-123',
 *   tag_name: 'High Priority',
 *   tag_order: 1,
 *   is_active: true,
 *   color: '#EF4444',
 *   description: 'For urgent or high-priority candidates'
 * });
 *
 * // Assign tag to a resume
 * await candidateTagsClient.assignTagToResume('resume-id', {
 *   tag_id: 'tag-id',
 *   recruiter_id: 'recruiter-id'
 * });
 *
 * // Update a tag
 * const updated = await candidateTagsClient.updateTag('tag-id', {
 *   tag_name: 'Updated Tag Name',
 *   is_active: false
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  CandidateTagCreate,
  CandidateTagUpdate,
  CandidateTagResponse,
  CandidateTagListResponse,
  CandidateTagsResponse,
  AssignTagRequest,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for candidate tags client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Candidate Tags API Client class
 *
 * Provides methods for managing candidate tag configurations with proper
 * error handling and type safety.
 */
export class CandidateTagsClient {
  private client: AxiosInstance;

  /**
   * Create a new CandidateTags client instance
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
      409: 'A tag with this name already exists.',
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
   * Create a candidate tag for an organization
   *
   * @param request - Create request with tag details
   * @returns Created candidate tag
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const tag = await candidateTagsClient.createTag({
   *   organization_id: 'org-123',
   *   tag_name: 'High Priority',
   *   tag_order: 1,
   *   is_active: true,
   *   color: '#EF4444',
   *   description: 'For urgent or high-priority candidates'
   * });
   * ```
   */
  async createTag(request: CandidateTagCreate): Promise<CandidateTagResponse> {
    try {
      const response: AxiosResponse<CandidateTagResponse> = await this.client.post(
        '/api/candidate-tags/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List candidate tags with optional filters
   *
   * @param organizationId - Optional organization ID filter
   * @param isActive - Optional active status filter
   * @param isDefault - Optional default status filter
   * @returns List of candidate tags
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all tags for an organization
   * const tags = await candidateTagsClient.listTags('org-123');
   *
   * // Get only active tags
   * const activeTags = await candidateTagsClient.listTags('org-123', true);
   * ```
   */
  async listTags(
    organizationId?: string,
    isActive?: boolean,
    isDefault?: boolean
  ): Promise<CandidateTagListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (isActive !== undefined) params.is_active = isActive;
      if (isDefault !== undefined) params.is_default = isDefault;

      const response: AxiosResponse<CandidateTagListResponse> = await this.client.get(
        '/api/candidate-tags/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific candidate tag by ID
   *
   * @param tagId - Candidate tag ID
   * @returns Candidate tag details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const tag = await candidateTagsClient.getTag('tag-uuid');
   * ```
   */
  async getTag(tagId: string): Promise<CandidateTagResponse> {
    try {
      const response: AxiosResponse<CandidateTagResponse> = await this.client.get(
        `/api/candidate-tags/${tagId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get all tags assigned to a specific resume
   *
   * @param resumeId - Resume ID
   * @returns Tags assigned to this resume
   * @throws ApiError if resume not found
   *
   * @example
   * ```ts
   * const tags = await candidateTagsClient.getResumeTags('resume-uuid');
   * ```
   */
  async getResumeTags(resumeId: string): Promise<CandidateTagsResponse> {
    try {
      const response: AxiosResponse<CandidateTagsResponse> = await this.client.get(
        `/api/candidate-tags/resume/${resumeId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a candidate tag
   *
   * @param tagId - Candidate tag ID
   * @param request - Update request with fields to modify
   * @returns Updated candidate tag
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await candidateTagsClient.updateTag('tag-uuid', {
   *   tag_name: 'Updated Tag Name',
   *   is_active: false
   * });
   * ```
   */
  async updateTag(
    tagId: string,
    request: CandidateTagUpdate
  ): Promise<CandidateTagResponse> {
    try {
      const response: AxiosResponse<CandidateTagResponse> = await this.client.put(
        `/api/candidate-tags/${tagId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a candidate tag
   *
   * @param tagId - Candidate tag ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await candidateTagsClient.deleteTag('tag-uuid');
   * ```
   */
  async deleteTag(tagId: string): Promise<void> {
    try {
      await this.client.delete(`/api/candidate-tags/${tagId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Assign a tag to a candidate (resume)
   *
   * @param resumeId - Resume ID
   * @param request - Assign tag request
   * @returns Success response with activity ID
   * @throws ApiError if assignment fails
   *
   * @example
   * ```ts
   * const result = await candidateTagsClient.assignTagToResume('resume-uuid', {
   *   tag_id: 'tag-uuid',
   *   recruiter_id: 'recruiter-uuid'
   * });
   * ```
   */
  async assignTagToResume(
    resumeId: string,
    request: AssignTagRequest
  ): Promise<{ message: string; resume_id: string; tag_id: string; activity_id: string }> {
    try {
      const response = await this.client.post(
        `/api/candidate-tags/resume/${resumeId}/assign`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Remove a tag from a candidate (resume)
   *
   * @param resumeId - Resume ID
   * @param tagId - Tag ID to remove
   * @param recruiterId - Optional recruiter ID who is removing the tag
   * @returns Success response with activity ID
   * @throws ApiError if removal fails
   *
   * @example
   * ```ts
   * const result = await candidateTagsClient.removeTagFromResume(
   *   'resume-uuid',
   *   'tag-uuid',
   *   'recruiter-uuid'
   * );
   * ```
   */
  async removeTagFromResume(
    resumeId: string,
    tagId: string,
    recruiterId?: string
  ): Promise<{ message: string; resume_id: string; tag_id: string; activity_id: string }> {
    try {
      const params: Record<string, string> = {};
      if (recruiterId) params.recruiter_id = recruiterId;

      const response = await this.client.delete(
        `/api/candidate-tags/resume/${resumeId}/tags/${tagId}`,
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
 * Default candidate tags client instance
 *
 * Use this singleton instance for all candidate tags calls.
 */
export const candidateTagsClient = new CandidateTagsClient();

/**
 * Export candidate tags client class for custom instances
 */
export default CandidateTagsClient;
