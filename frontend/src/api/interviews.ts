/**
 * Interviews API Client
 *
 * This module provides a client for managing interview scheduling,
 * including creating, reading, updating, and deleting interviews
 * with participant management and calendar integration.
 *
 * @example
 * ```ts
 * import { interviewsClient } from '@/api/interviews';
 *
 * // List all interviews for a candidate
 * const interviews = await interviewsClient.listInterviews({ candidate_id: 'candidate-123' });
 *
 * // Create a new interview
 * const newInterview = await interviewsClient.createInterview({
 *   candidate_id: 'candidate-123',
 *   vacancy_id: 'vacancy-456',
 *   scheduled_start: '2024-01-15T10:00:00Z',
 *   duration_minutes: 60,
 *   interview_type: 'video',
 *   title: 'Technical Interview',
 *   participant_ids: ['recruiter-1', 'recruiter-2']
 * });
 *
 * // Update an interview
 * const updated = await interviewsClient.updateInterview('interview-id', {
 *   status: 'confirmed',
 *   meeting_link: 'https://meet.google.com/abc-defg-hij'
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  InterviewCreate,
  InterviewUpdate,
  InterviewResponse,
  InterviewListResponse,
  ApiError,
} from '@/types/api';

/**
 * Interview list filters
 */
export interface InterviewListFilters {
  candidate_id?: string;
  vacancy_id?: string;
  status?: string;
  interviewer_id?: string;
  start_date?: string;
  end_date?: string;
  skip?: number;
  limit?: number;
}

/**
 * Default API configuration for interviews client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Interviews API Client class
 *
 * Provides methods for managing interview scheduling with proper
 * error handling and type safety.
 */
export class InterviewsClient {
  private client: AxiosInstance;

  /**
   * Create a new Interviews client instance
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
      409: 'A conflict occurred with this interview time.',
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
   * Create a new interview
   *
   * @param request - Create request with interview details
   * @returns Created interview
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const interview = await interviewsClient.createInterview({
   *   candidate_id: 'candidate-123',
   *   vacancy_id: 'vacancy-456',
   *   scheduled_start: '2024-01-15T10:00:00Z',
   *   duration_minutes: 60,
   *   interview_type: 'video',
   *   title: 'Technical Interview',
   *   description: 'Technical assessment with engineering team',
   *   participant_ids: ['recruiter-1', 'recruiter-2']
   * });
   * ```
   */
  async createInterview(request: InterviewCreate): Promise<InterviewResponse> {
    try {
      const response: AxiosResponse<InterviewResponse> = await this.client.post(
        '/api/interviews/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List interviews with optional filters
   *
   * @param filters - Optional filters for listing interviews
   * @returns List of interviews
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all interviews for a candidate
   * const interviews = await interviewsClient.listInterviews({
   *   candidate_id: 'candidate-123'
   * });
   *
   * // Get upcoming interviews for a specific date range
   * const upcoming = await interviewsClient.listInterviews({
   *   status: 'scheduled',
   *   start_date: '2024-01-01T00:00:00Z',
   *   end_date: '2024-01-31T23:59:59Z'
   * });
   *
   * // Get interviews where a specific recruiter is participating
   * const myInterviews = await interviewsClient.listInterviews({
   *   interviewer_id: 'recruiter-123'
   * });
   * ```
   */
  async listInterviews(filters?: InterviewListFilters): Promise<InterviewListResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (filters?.candidate_id) params.candidate_id = filters.candidate_id;
      if (filters?.vacancy_id) params.vacancy_id = filters.vacancy_id;
      if (filters?.status) params.status_filter = filters.status;
      if (filters?.interviewer_id) params.interviewer_id = filters.interviewer_id;
      if (filters?.start_date) params.start_date = filters.start_date;
      if (filters?.end_date) params.end_date = filters.end_date;
      if (filters?.skip !== undefined) params.skip = filters.skip;
      if (filters?.limit !== undefined) params.limit = filters.limit;

      const response: AxiosResponse<InterviewListResponse> = await this.client.get(
        '/api/interviews/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific interview by ID
   *
   * @param interviewId - Interview ID
   * @returns Interview details with participants
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const interview = await interviewsClient.getInterview('interview-uuid');
   * console.log(interview.participants); // Array of participants
   * ```
   */
  async getInterview(interviewId: string): Promise<InterviewResponse> {
    try {
      const response: AxiosResponse<InterviewResponse> = await this.client.get(
        `/api/interviews/${interviewId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update an interview
   *
   * @param interviewId - Interview ID
   * @param request - Update request with fields to modify
   * @returns Updated interview
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * // Reschedule an interview
   * const updated = await interviewsClient.updateInterview('interview-uuid', {
   *   scheduled_start: '2024-01-16T14:00:00Z',
   *   status: 'rescheduled'
   * });
   *
   * // Add meeting link
   * const withLink = await interviewsClient.updateInterview('interview-uuid', {
   *   meeting_link: 'https://meet.google.com/abc-defg-hij'
   * });
   *
   * // Confirm interview
   * const confirmed = await interviewsClient.updateInterview('interview-uuid', {
   *   status: 'confirmed'
   * });
   * ```
   */
  async updateInterview(
    interviewId: string,
    request: InterviewUpdate
  ): Promise<InterviewResponse> {
    try {
      const response: AxiosResponse<InterviewResponse> = await this.client.put(
        `/api/interviews/${interviewId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete/cancel an interview
   *
   * @param interviewId - Interview ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await interviewsClient.deleteInterview('interview-uuid');
   * ```
   */
  async deleteInterview(interviewId: string): Promise<void> {
    try {
      await this.client.delete(`/api/interviews/${interviewId}`);
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
 * Default interviews client instance
 *
 * Use this singleton instance for all interview API calls.
 */
export const interviewsClient = new InterviewsClient();

/**
 * Export interviews client class for custom instances
 */
export default InterviewsClient;
