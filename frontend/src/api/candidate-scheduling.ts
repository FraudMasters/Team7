/**
 * Candidate Scheduling API Client
 *
 * This module provides a client for candidate self-scheduling functionality.
 * Candidates use a unique token to view available interview slots and book
 * interviews at their preferred time.
 *
 * @example
 * ```ts
 * import { candidateSchedulingClient } from '@/api/candidate-scheduling';
 *
 * // Verify a scheduling token
 * const tokenInfo = await candidateSchedulingClient.verifyToken('token-123');
 *
 * // Get available slots
 * const slots = await candidateSchedulingClient.getAvailableSlots('token-123');
 *
 * // Book an interview
 * const interview = await candidateSchedulingClient.scheduleInterview({
 *   token: 'token-123',
 *   selected_slot: '2024-01-15T10:00:00Z',
 *   duration_minutes: 60,
 *   interview_type: 'video'
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';

/**
 * API Error response structure
 */
export interface ApiError {
  detail: string;
  status: number;
}

/**
 * Available time slot structure
 */
export interface AvailableSlot {
  start_time: string;
  end_time: string;
  duration_minutes: number;
  available: boolean;
}

/**
 * Available slots response from API
 */
export interface AvailableSlotsResponse {
  recruiter_name: string;
  vacancy_title: string | null;
  available_slots: AvailableSlot[];
  expires_at: string | null;
}

/**
 * Token verification response
 */
export interface TokenVerificationResponse {
  valid: boolean;
  candidate_name?: string;
  recruiter_name?: string;
  vacancy_title?: string | null;
  expires_at?: string;
  message: string;
}

/**
 * Self-schedule interview request
 */
export interface SelfScheduleRequest {
  token: string;
  selected_slot: string;
  duration_minutes: number;
  interview_type?: string;
}

/**
 * Self-schedule interview response
 */
export interface SelfScheduleResponse {
  interview_id: string;
  candidate_name: string;
  scheduled_start: string;
  scheduled_end: string;
  duration_minutes: number;
  interview_type: string;
  title: string;
  meeting_link: string | null;
  location: string | null;
  recruiter_name: string | null;
  message: string;
}

/**
 * Default API configuration for candidate scheduling client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Candidate Scheduling API Client class
 *
 * Provides methods for candidate self-scheduling with proper
 * error handling and type safety.
 */
export class CandidateSchedulingClient {
  private client: AxiosInstance;

  /**
   * Create a new Candidate Scheduling client instance
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
      401: 'Invalid or expired scheduling token. Please request a new link.',
      403: 'Forbidden. You do not have permission.',
      404: 'Resource not found.',
      409: 'This time slot is no longer available.',
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
   * Verify a scheduling token
   *
   * @param token - Unique scheduling token
   * @returns Token verification information
   * @throws ApiError if verification fails
   *
   * @example
   * ```ts
   * const tokenInfo = await candidateSchedulingClient.verifyToken('token-123');
   * if (!tokenInfo.valid) {
   *   console.error(tokenInfo.message);
   * }
   * ```
   */
  async verifyToken(token: string): Promise<TokenVerificationResponse> {
    try {
      const response: AxiosResponse<TokenVerificationResponse> = await this.client.get(
        `/api/candidate-scheduling/verify-token/${token}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get available time slots for a candidate
   *
   * @param token - Unique scheduling token
   * @returns Available slots response
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const slots = await candidateSchedulingClient.getAvailableSlots('token-123');
   * console.log(`Found ${slots.available_slots.length} available slots`);
   * ```
   */
  async getAvailableSlots(token: string): Promise<AvailableSlotsResponse> {
    try {
      const response: AxiosResponse<AvailableSlotsResponse> = await this.client.post(
        '/api/candidate-scheduling/available-slots',
        { token }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Schedule an interview using a selected time slot
   *
   * @param request - Schedule request with token and selected slot
   * @returns Created interview details
   * @throws ApiError if scheduling fails
   *
   * @example
   * ```ts
   * const interview = await candidateSchedulingClient.scheduleInterview({
   *   token: 'token-123',
   *   selected_slot: '2024-01-15T10:00:00Z',
   *   duration_minutes: 60,
   *   interview_type: 'video'
   * });
   * console.log(interview.message);
   * ```
   */
  async scheduleInterview(request: SelfScheduleRequest): Promise<SelfScheduleResponse> {
    try {
      const response: AxiosResponse<SelfScheduleResponse> = await this.client.post(
        '/api/candidate-scheduling/schedule',
        request
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
 * Default candidate scheduling client instance
 *
 * Use this singleton instance for all candidate scheduling API calls.
 */
export const candidateSchedulingClient = new CandidateSchedulingClient();

/**
 * Export candidate scheduling client class for custom instances
 */
export default CandidateSchedulingClient;
