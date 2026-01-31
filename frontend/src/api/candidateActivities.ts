/**
 * Candidate Activities API Client
 *
 * This module provides a client for retrieving candidate activity history,
 * including stage changes, notes additions/changes, tag modifications,
 * and other significant candidate events throughout the hiring process.
 *
 * @example
 * ```ts
 * import { candidateActivitiesClient } from '@/api/candidateActivities';
 *
 * // List all activities for a candidate
 * const activities = await candidateActivitiesClient.listActivities('resume-123');
 *
 * // Filter activities by type
 * const stageChanges = await candidateActivitiesClient.filterByType(
 *   'resume-123',
 *   'stage_changed'
 * );
 *
 * // Get available activity types
 * const types = await candidateActivitiesClient.getActivityTypes();
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  ActivityItem,
  ActivityTimelineResponse,
  ActivityTypesResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for candidate activities client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Candidate Activities API Client class
 *
 * Provides methods for retrieving candidate activity history with proper
 * error handling and type safety.
 */
export class CandidateActivitiesClient {
  private client: AxiosInstance;

  /**
   * Create a new CandidateActivities client instance
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
   * List candidate activities with optional filters
   *
   * @param resumeId - Resume (candidate) ID
   * @param activityType - Optional activity type filter
   * @param vacancyId - Optional vacancy ID filter
   * @param limit - Maximum number of activities to return (default: 100)
   * @param offset - Number of activities to skip for pagination (default: 0)
   * @returns List of activities in chronological order
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all activities for a candidate
   * const activities = await candidateActivitiesClient.listActivities('resume-123');
   *
   * // Get activities with pagination
   * const page1 = await candidateActivitiesClient.listActivities(
   *   'resume-123',
   *   undefined,
   *   undefined,
   *   50,
   *   0
   * );
   *
   * // Filter by vacancy
   * const vacancyActivities = await candidateActivitiesClient.listActivities(
   *   'resume-123',
   *   undefined,
   *   'vacancy-456'
   * );
   * ```
   */
  async listActivities(
    resumeId: string,
    activityType?: string,
    vacancyId?: string,
    limit = 100,
    offset = 0
  ): Promise<ActivityTimelineResponse> {
    try {
      const params: Record<string, string | number> = {
        resume_id: resumeId,
        limit,
        offset,
      };
      if (activityType) params.activity_type = activityType;
      if (vacancyId) params.vacancy_id = vacancyId;

      const response: AxiosResponse<ActivityTimelineResponse> = await this.client.get(
        '/api/candidate-activities/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Filter candidate activities by type
   *
   * This is a convenience method that wraps listActivities with an activity type filter.
   *
   * @param resumeId - Resume (candidate) ID
   * @param activityType - Activity type to filter by (e.g., 'stage_changed', 'note_added')
   * @param vacancyId - Optional vacancy ID filter
   * @param limit - Maximum number of activities to return (default: 100)
   * @param offset - Number of activities to skip for pagination (default: 0)
   * @returns Filtered list of activities
   * @throws ApiError if filtering fails
   *
   * @example
   * ```ts
   * // Get only stage changes
   * const stageChanges = await candidateActivitiesClient.filterByType(
   *   'resume-123',
   *   'stage_changed'
   * );
   *
   * // Get only note additions
   * const notes = await candidateActivitiesClient.filterByType(
   *   'resume-123',
   *   'note_added'
   * );
   *
   * // Get tag additions for a specific vacancy
   * const tags = await candidateActivitiesClient.filterByType(
   *   'resume-123',
   *   'tag_added',
   *   'vacancy-456'
   * );
   * ```
   */
  async filterByType(
    resumeId: string,
    activityType: string,
    vacancyId?: string,
    limit = 100,
    offset = 0
  ): Promise<ActivityTimelineResponse> {
    try {
      const params: Record<string, string | number> = {
        resume_id: resumeId,
        activity_type: activityType,
        limit,
        offset,
      };
      if (vacancyId) params.vacancy_id = vacancyId;

      const response: AxiosResponse<ActivityTimelineResponse> = await this.client.get(
        '/api/candidate-activities/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get available activity types
   *
   * @returns List of available activity types that can be used for filtering
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const types = await candidateActivitiesClient.getActivityTypes();
   * console.log(types.activity_types);
   * // [
   * //   'stage_changed',
   * //   'note_added',
   * //   'note_updated',
   * //   'note_deleted',
   * //   'tag_added',
   * //   'tag_removed',
   * //   'ranking_changed',
   * //   'rating_changed',
   * //   'contact_attempt',
   * //   'interview_scheduled',
   * //   'feedback_provided',
   * //   'status_updated'
   * // ]
   * ```
   */
  async getActivityTypes(): Promise<ActivityTypesResponse> {
    try {
      const response: AxiosResponse<ActivityTypesResponse> = await this.client.get(
        '/api/candidate-activities/types'
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
 * Default candidate activities client instance
 *
 * Use this singleton instance for all candidate activities calls.
 */
export const candidateActivitiesClient = new CandidateActivitiesClient();

/**
 * Export candidate activities client class for custom instances
 */
export default CandidateActivitiesClient;
