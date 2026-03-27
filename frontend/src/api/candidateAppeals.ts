/**
 * Candidate Appeals API Client
 *
 * This module provides a client for managing candidate appeals against AI ranking
 * decisions. Candidates can submit appeals with additional context and supporting
 * documentation, while recruiters can review and take action on appeals.
 *
 * @example
 * ```ts
 * import { candidateAppealsClient } from '@/api/candidateAppeals';
 *
 * // Create a new appeal
 * const appeal = await candidateAppealsClient.createAppeal({
 *   candidate_rank_id: 'rank-uuid',
 *   candidate_email: 'candidate@example.com',
 *   appeal_type: 'ranking_position',
 *   appeal_text: 'I have 5 years of experience with React',
 * });
 *
 * // Get appeal by ID
 * const appeal = await candidateAppealsClient.getAppeal('appeal-uuid');
 *
 * // List appeals for a candidate
 * const appeals = await candidateAppealsClient.listAppeals('candidate@example.com');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';

/**
 * Appeal types
 */
export type AppealType = 'ranking_position' | 'score_explanation' | 'missing_skills';

/**
 * Appeal status
 */
export type AppealStatus = 'pending' | 'under_review' | 'accepted' | 'rejected';

/**
 * API error type
 */
export interface ApiError {
  detail: string;
  status: number;
}

/**
 * Supporting documents metadata
 */
export interface SupportingDocuments {
  documents: Array<{
    filename: string;
    url: string;
    type: string;
  }>;
}

/**
 * Request model for creating a candidate appeal
 */
export interface AppealCreate {
  candidate_rank_id: string;
  candidate_email: string;
  appeal_type: AppealType;
  appeal_text: string;
  supporting_documents?: SupportingDocuments;
}

/**
 * Response model for a single appeal
 */
export interface AppealResponse {
  id: string;
  candidate_rank_id: string;
  candidate_email: string;
  appeal_type: AppealType;
  appeal_text: string;
  supporting_documents?: SupportingDocuments;
  status: AppealStatus;
  reviewer_id?: string;
  review_notes?: string;
  resolution_outcome?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Response model for listing appeals
 */
export interface AppealListResponse {
  appeals: AppealResponse[];
  total_count: number;
}

/**
 * Request model for reviewing an appeal (recruiter action)
 */
export interface AppealReviewRequest {
  status: AppealStatus;
  review_notes?: string;
  resolution_outcome?: string;
}

/**
 * Default configuration for the appeals client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Candidate Appeals API Client
 *
 * Provides methods for creating, viewing, and managing candidate appeals
 * with proper error handling and type safety.
 */
export class CandidateAppealsClient {
  private client: AxiosInstance;

  /**
   * Create a new candidate appeals client
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

    // Server returned an error
    const status = axiosError.response.status;
    const data = axiosError.response.data;

    // Use server error message if available
    if (data?.detail) {
      return { detail: data.detail, status };
    }

    // Default error messages for different status codes
    const defaultMessages: Record<number, string> = {
      400: 'Invalid request. Please check your input.',
      401: 'Unauthorized. Please log in.',
      403: 'Access denied. You do not have permission to perform this action.',
      404: 'Appeal not found.',
      422: 'Validation error. Please check your data format.',
      429: 'Too many requests. Please try again later.',
      500: 'Server error. Please try again later.',
      502: 'Gateway error. Please try again later.',
      503: 'Service unavailable. Please try again later.',
    };

    return {
      detail: data?.detail || defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * Create a new appeal
   *
   * @param request - Appeal creation request
   * @returns Created appeal
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const appeal = await client.createAppeal({
   *   candidate_rank_id: 'rank-uuid',
   *   candidate_email: 'candidate@example.com',
   *   appeal_type: 'ranking_position',
   *   appeal_text: 'I have 5 years of experience with React and advanced TypeScript skills',
   *   supporting_documents: {
   *     documents: [
   *       { filename: 'react-cert.pdf', url: 's3://bucket/cert.pdf', type: 'certification' }
   *     ]
   *   }
   * });
   * ```
   */
  async createAppeal(request: AppealCreate): Promise<AppealResponse> {
    try {
      const response: AxiosResponse<AppealResponse> = await this.client.post(
        '/api/candidate-appeals/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get appeal by ID
   *
   * @param id - Appeal UUID
   * @returns Appeal details
   * @throws ApiError if appeal not found
   *
   * @example
   * ```ts
   * const appeal = await client.getAppeal('appeal-uuid');
   * console.log(appeal.status, appeal.appeal_text);
   * ```
   */
  async getAppeal(id: string): Promise<AppealResponse> {
    try {
      const response: AxiosResponse<AppealResponse> = await this.client.get(
        `/api/candidate-appeals/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List appeals with optional filters
   *
   * @param candidateEmail - Optional filter by candidate email
   * @param candidateRankId - Optional filter by candidate rank ID
   * @param appealType - Optional filter by appeal type
   * @param status - Optional filter by status
   * @param reviewerId - Optional filter by reviewer ID
   * @returns List of appeals
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * // Get all appeals for a candidate
   * const appeals = await client.listAppeals('candidate@example.com');
   *
   * // Get all pending appeals
   * const pending = await client.listAppeals(undefined, undefined, undefined, 'pending');
   * ```
   */
  async listAppeals(
    candidateEmail?: string,
    candidateRankId?: string,
    appealType?: AppealType,
    status?: AppealStatus,
    reviewerId?: string
  ): Promise<AppealListResponse> {
    try {
      const params: Record<string, string> = {};
      if (candidateEmail) params.candidate_email = candidateEmail;
      if (candidateRankId) params.candidate_rank_id = candidateRankId;
      if (appealType) params.appeal_type = appealType;
      if (status) params.status = status;
      if (reviewerId) params.reviewer_id = reviewerId;

      const response: AxiosResponse<AppealListResponse> = await this.client.get(
        '/api/candidate-appeals/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Review an appeal (recruiter action)
   *
   * @param id - Appeal UUID
   * @param request - Review request
   * @returns Updated appeal
   * @throws ApiError if review fails
   *
   * @example
   * ```ts
   * const updated = await client.reviewAppeal('appeal-uuid', {
   *   status: 'accepted',
   *   review_notes: 'Valid additional skills identified',
   *   resolution_outcome: 'Re-ranked candidate with updated skill profile'
   * });
   * ```
   */
  async reviewAppeal(
    id: string,
    request: AppealReviewRequest
  ): Promise<AppealResponse> {
    try {
      const response: AxiosResponse<AppealResponse> = await this.client.patch(
        `/api/candidate-appeals/${id}/review`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get base Axios instance
   *
   * Useful for custom requests not covered by client methods.
   *
   * @returns Axios instance
   */
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }
}

/**
 * Default candidate appeals client instance
 *
 * Use this singleton instance for all appeal operations.
 */
export const candidateAppealsClient = new CandidateAppealsClient();

/**
 * Export class for creating custom instances
 */
export default CandidateAppealsClient;
