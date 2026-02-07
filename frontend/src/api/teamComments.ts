/**
 * Team Comments API Client
 *
 * This module provides a client for managing team comments and threaded discussions,
 * including creating, reading, updating, and deleting collaborative comments.
 *
 * @example
 * ```ts
 * import { teamCommentsClient } from '@/api/teamComments';
 *
 * // List all comments for a candidate
 * const comments = await teamCommentsClient.listComments('resume-123');
 *
 * // Create a new comment
 * const newComment = await teamCommentsClient.createComment({
 *   resume_id: 'resume-123',
 *   author_id: 'recruiter-123',
 *   content: 'Great candidate, strong technical skills',
 *   is_resolved: false
 * });
 *
 * // Update a comment
 * const updated = await teamCommentsClient.updateComment('comment-id', {
 *   content: 'Updated comment content',
 *   is_resolved: true
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  TeamCommentCreate,
  TeamCommentUpdate,
  TeamCommentResponse,
  TeamCommentListResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for team comments client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Team Comments API Client class
 *
 * Provides methods for managing team comments with proper
 * error handling and type safety.
 */
export class TeamCommentsClient {
  private client: AxiosInstance;

  /**
   * Create a new TeamComments client instance
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
      409: 'A conflict occurred with the existing comment.',
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
   * Create a team comment
   *
   * @param request - Create request with comment details
   * @returns Created team comment
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const comment = await teamCommentsClient.createComment({
   *   resume_id: 'resume-123',
   *   author_id: 'recruiter-123',
   *   content: 'Great candidate, strong technical skills',
   *   is_resolved: false
   * });
   * ```
   */
  async createComment(request: TeamCommentCreate): Promise<TeamCommentResponse> {
    try {
      const response: AxiosResponse<TeamCommentResponse> = await this.client.post(
        '/api/team-comments/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List team comments with optional filters
   *
   * @param resumeId - Optional resume ID filter
   * @param authorId - Optional author ID filter
   * @param isResolved - Optional resolved status filter
   * @param parentCommentId - Optional parent comment ID filter
   * @param includeDeleted - Include soft-deleted comments
   * @returns List of team comments
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all comments for a candidate
   * const comments = await teamCommentsClient.listComments('resume-123');
   *
   * // Get only unresolved comments
   * const unresolved = await teamCommentsClient.listComments('resume-123', undefined, false);
   *
   * // Get all replies to a specific comment
   * const replies = await teamCommentsClient.listComments(undefined, undefined, undefined, 'comment-123');
   *
   * // Get all comments by a specific author
   * const myComments = await teamCommentsClient.listComments(undefined, 'recruiter-123');
   * ```
   */
  async listComments(
    resumeId?: string,
    authorId?: string,
    isResolved?: boolean,
    parentCommentId?: string,
    includeDeleted?: boolean
  ): Promise<TeamCommentListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (resumeId) params.resume_id = resumeId;
      if (authorId) params.author_id = authorId;
      if (isResolved !== undefined) params.is_resolved = isResolved;
      if (parentCommentId) params.parent_comment_id = parentCommentId;
      if (includeDeleted !== undefined) params.include_deleted = includeDeleted;

      const response: AxiosResponse<TeamCommentListResponse> = await this.client.get(
        '/api/team-comments/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific team comment by ID
   *
   * @param commentId - Team comment ID
   * @returns Team comment details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const comment = await teamCommentsClient.getComment('comment-uuid');
   * ```
   */
  async getComment(commentId: string): Promise<TeamCommentResponse> {
    try {
      const response: AxiosResponse<TeamCommentResponse> = await this.client.get(
        `/api/team-comments/${commentId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a team comment
   *
   * @param commentId - Team comment ID
   * @param request - Update request with fields to modify
   * @returns Updated team comment
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await teamCommentsClient.updateComment('comment-uuid', {
   *   content: 'Updated comment content',
   *   is_resolved: true
   * });
   * ```
   */
  async updateComment(
    commentId: string,
    request: TeamCommentUpdate
  ): Promise<TeamCommentResponse> {
    try {
      const response: AxiosResponse<TeamCommentResponse> = await this.client.put(
        `/api/team-comments/${commentId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a team comment (soft delete)
   *
   * @param commentId - Team comment ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await teamCommentsClient.deleteComment('comment-uuid');
   * ```
   */
  async deleteComment(commentId: string): Promise<void> {
    try {
      await this.client.delete(`/api/team-comments/${commentId}`);
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
 * Default team comments client instance
 *
 * Use this singleton instance for all team comments calls.
 */
export const teamCommentsClient = new TeamCommentsClient();

/**
 * Export team comments client class for custom instances
 */
export default TeamCommentsClient;
