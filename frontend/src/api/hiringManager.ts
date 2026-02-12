/**
 * Hiring Manager API Client
 *
 * This module provides a client for the hiring manager portal interface,
 * including dashboard statistics, candidate review queue, one-click
 * approval/rejection actions, and evaluation summaries.
 *
 * @example
 * ```ts
 * import { hiringManagerClient } from '@/api/hiringManager';
 *
 * // Get dashboard statistics
 * const stats = await hiringManagerClient.getDashboardStats();
 *
 * // Get review queue with filters
 * const queue = await hiringManagerClient.getReviewQueue({
 *   priority: 'urgent',
 *   min_match_score: 0.8
 * });
 *
 * // Approve a candidate
 * const result = await hiringManagerClient.approveCandidate('candidate-123', {
 *   rationale: 'Excellent technical skills and culture fit'
 * });
 *
 * // Reject a candidate
 * const result = await hiringManagerClient.rejectCandidate('candidate-456', {
 *   rationale: 'Insufficient experience',
 *   rejection_reason: 'experience'
 * });
 *
 * // Get evaluation summary for a candidate
 * const evaluation = await hiringManagerClient.getEvaluationSummary('candidate-123');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError } from '@/types/api';

// ==================== Response Types ====================

/**
 * Statistics for candidates pending manager review
 */
export interface PendingReviewStats {
  total_pending: number;
  urgent_count: number;
  new_this_week: number;
  average_wait_days: number;
}

/**
 * Statistics for a single vacancy
 */
export interface VacancyStats {
  vacancy_id: string;
  vacancy_title: string;
  pending_review: number;
  total_candidates: number;
  stage: string;
}

/**
 * Recent activity item for the hiring manager
 */
export interface RecentActivity {
  activity_type: string;
  candidate_name: string;
  vacancy_title: string;
  timestamp: string;
}

/**
 * Dashboard statistics response
 */
export interface DashboardStatsResponse {
  pending_review: PendingReviewStats;
  my_vacancies: VacancyStats[];
  recent_activity: RecentActivity[];
  quick_stats: {
    approved_this_month: number;
    rejected_this_month: number;
    interviews_scheduled: number;
    avg_time_to_decision_days: number;
    [key: string]: unknown;
  };
}

/**
 * Recruiter feedback for a candidate
 */
export interface RecruiterFeedback {
  recruiter_name: string;
  rating: number | null;
  recommendation: string | null;
  notes: string | null;
  created_at: string;
}

/**
 * Candidate in the review queue
 */
export interface ReviewQueueCandidate {
  id: string;
  filename: string;
  candidate_name: string | null;
  vacancy_id: string | null;
  vacancy_title: string | null;
  current_stage: string;
  stage_name: string;
  priority: string | null;
  days_in_stage: number;
  match_score: number | null;
  recruiter_feedback: RecruiterFeedback[];
  team_consensus: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
}

/**
 * Review queue response
 */
export interface ReviewQueueResponse {
  total_candidates: number;
  candidates: ReviewQueueCandidate[];
  filters_applied: Record<string, unknown>;
  pagination: {
    skip: number;
    limit: number;
    total: number;
  };
}

/**
 * Candidate approval request
 */
export interface CandidateApprovalRequest {
  rationale?: string;
  next_stage?: string;
}

/**
 * Candidate rejection request
 */
export interface CandidateRejectionRequest {
  rationale?: string;
  rejection_reason?:
    | 'skills_match'
    | 'experience'
    | 'culture_fit'
    | 'salary_expectations'
    | 'location'
    | 'availability'
    | 'other';
  notify_candidate?: boolean;
}

/**
 * Candidate decision response (approve/reject)
 */
export interface CandidateDecisionResponse {
  candidate_id: string;
  decision: 'approved' | 'rejected';
  previous_stage: string;
  new_stage: string;
  rationale: string | null;
  decided_at: string;
  message: string;
}

/**
 * Feedback summary for evaluation
 */
export interface FeedbackSummary {
  total_feedback_count: number;
  average_rating: number | null;
  recommendations_breakdown: {
    approve: number;
    reject: number;
    maybe: number;
  };
  feedback_list: RecruiterFeedback[];
}

/**
 * Consensus details for evaluation
 */
export interface ConsensusDetails {
  consensus: string | null;
  approval_rate: number;
  rejection_rate: number;
  total_reviewers: number;
  unanimous: boolean;
}

/**
 * Evaluation summary response
 */
export interface EvaluationSummaryResponse {
  candidate_id: string;
  candidate_name: string | null;
  vacancy_id: string | null;
  vacancy_title: string | null;
  current_stage: string;
  match_score: number | null;
  feedback_summary: FeedbackSummary;
  consensus_details: ConsensusDetails;
  screening_tier: string | null;
  tags: string[];
  evaluation_date: string;
}

// ==================== Filter Types ====================

/**
 * Review queue filters
 */
export interface ReviewQueueFilters {
  vacancy_id?: string;
  priority?: 'urgent' | 'high' | 'normal' | 'low';
  stage_id?: string;
  search?: string;
  min_match_score?: number;
  has_recruiter_feedback?: boolean;
  skip?: number;
  limit?: number;
}

/**
 * Dashboard stats filters
 */
export interface DashboardStatsFilters {
  start_date?: string;
  end_date?: string;
}

// ==================== Client Class ====================

/**
 * Default API configuration for hiring manager client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? import.meta.env.VITE_API_GATEWAY_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Hiring Manager API Client class
 *
 * Provides methods for the hiring manager portal with proper
 * error handling and type safety.
 */
export class HiringManagerClient {
  private client: AxiosInstance;

  /**
   * Create a new Hiring Manager client instance
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
      403: 'Forbidden. You do not have permission to access this resource.',
      404: 'Resource not found.',
      409: 'A conflict occurred with this operation.',
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
   * Get hiring manager dashboard statistics
   *
   * @param filters - Optional date filters for the statistics
   * @returns Dashboard statistics including pending review counts and recent activity
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * // Get all dashboard stats
   * const stats = await hiringManagerClient.getDashboardStats();
   * console.log(stats.pending_review.total_pending);
   *
   * // Get stats for a specific date range
   * const stats = await hiringManagerClient.getDashboardStats({
   *   start_date: '2024-01-01',
   *   end_date: '2024-01-31'
   * });
   * ```
   */
  async getDashboardStats(filters?: DashboardStatsFilters): Promise<DashboardStatsResponse> {
    try {
      const params: Record<string, string> = {};
      if (filters?.start_date) params.start_date = filters.start_date;
      if (filters?.end_date) params.end_date = filters.end_date;

      const response: AxiosResponse<DashboardStatsResponse> = await this.client.get(
        '/api/hiring-manager/dashboard',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get the hiring manager's review queue with candidate filtering
   *
   * @param filters - Optional filters for the review queue
   * @returns List of candidates awaiting review with feedback and consensus
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * // Get all candidates in review queue
   * const queue = await hiringManagerClient.getReviewQueue();
   *
   * // Filter by vacancy
   * const queue = await hiringManagerClient.getReviewQueue({
   *   vacancy_id: 'vacancy-123'
   * });
   *
   * // Get urgent candidates with high match scores
   * const queue = await hiringManagerClient.getReviewQueue({
   *   priority: 'urgent',
   *   min_match_score: 0.8
   * });
   *
   * // Search by name
   * const queue = await hiringManagerClient.getReviewQueue({
   *   search: 'John Doe'
   * });
   * ```
   */
  async getReviewQueue(filters?: ReviewQueueFilters): Promise<ReviewQueueResponse> {
    try {
      const params: Record<string, string | number | boolean> = {};
      if (filters?.vacancy_id) params.vacancy_id = filters.vacancy_id;
      if (filters?.priority) params.priority = filters.priority;
      if (filters?.stage_id) params.stage_id = filters.stage_id;
      if (filters?.search) params.search = filters.search;
      if (filters?.min_match_score !== undefined) params.min_match_score = filters.min_match_score;
      if (filters?.has_recruiter_feedback !== undefined) {
        params.has_recruiter_feedback = filters.has_recruiter_feedback;
      }
      if (filters?.skip !== undefined) params.skip = filters.skip;
      if (filters?.limit !== undefined) params.limit = filters.limit;

      const response: AxiosResponse<ReviewQueueResponse> = await this.client.get(
        '/api/hiring-manager/review-queue',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * One-click approve a candidate with optional rationale
   *
   * @param candidateId - UUID of the candidate to approve
   * @param request - Approval details including optional rationale
   * @returns Approval confirmation with updated candidate status
   * @throws ApiError if approval fails
   *
   * @example
   * ```ts
   * // Simple approval
   * const result = await hiringManagerClient.approveCandidate('candidate-123');
   *
   * // Approval with rationale
   * const result = await hiringManagerClient.approveCandidate('candidate-123', {
   *   rationale: 'Excellent technical skills and culture fit'
   * });
   *
   * // Approval with custom next stage
   * const result = await hiringManagerClient.approveCandidate('candidate-123', {
   *   rationale: 'Moving to final interview',
   *   next_stage: 'final_interview'
   * });
   * ```
   */
  async approveCandidate(
    candidateId: string,
    request?: CandidateApprovalRequest
  ): Promise<CandidateDecisionResponse> {
    try {
      const response: AxiosResponse<CandidateDecisionResponse> = await this.client.post(
        `/api/hiring-manager/candidates/${candidateId}/approve`,
        request ?? {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * One-click reject a candidate with optional rationale
   *
   * @param candidateId - UUID of the candidate to reject
   * @param request - Rejection details including optional rationale and reason
   * @returns Rejection confirmation with updated candidate status
   * @throws ApiError if rejection fails
   *
   * @example
   * ```ts
   * // Simple rejection
   * const result = await hiringManagerClient.rejectCandidate('candidate-456');
   *
   * // Rejection with rationale
   * const result = await hiringManagerClient.rejectCandidate('candidate-456', {
   *   rationale: 'Insufficient experience with required technologies',
   *   rejection_reason: 'experience'
   * });
   *
   * // Rejection with notification
   * const result = await hiringManagerClient.rejectCandidate('candidate-456', {
   *   rationale: 'Position filled',
   *   notify_candidate: true
   * });
   * ```
   */
  async rejectCandidate(
    candidateId: string,
    request?: CandidateRejectionRequest
  ): Promise<CandidateDecisionResponse> {
    try {
      const response: AxiosResponse<CandidateDecisionResponse> = await this.client.post(
        `/api/hiring-manager/candidates/${candidateId}/reject`,
        request ?? {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get evaluation summary for a candidate
   *
   * Shows recruiter feedback and team consensus to help hiring managers
   * make informed decisions.
   *
   * @param candidateId - UUID of the candidate
   * @returns Evaluation summary with feedback and consensus details
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const evaluation = await hiringManagerClient.getEvaluationSummary('candidate-123');
   * console.log(evaluation.feedback_summary.average_rating);
   * console.log(evaluation.consensus_details.consensus);
   * console.log(evaluation.match_score);
   * ```
   */
  async getEvaluationSummary(candidateId: string): Promise<EvaluationSummaryResponse> {
    try {
      const response: AxiosResponse<EvaluationSummaryResponse> = await this.client.get(
        `/api/hiring-manager/candidates/${candidateId}/evaluation`
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
 * Default hiring manager client instance
 *
 * Use this singleton instance for all hiring manager API calls.
 */
export const hiringManagerClient = new HiringManagerClient();

/**
 * Export hiring manager client class for custom instances
 */
export default HiringManagerClient;

// Re-export types for convenience
export type {
  DashboardStatsResponse,
  ReviewQueueResponse,
  ReviewQueueCandidate,
  RecruiterFeedback,
  CandidateApprovalRequest,
  CandidateRejectionRequest,
  CandidateDecisionResponse,
  EvaluationSummaryResponse,
  FeedbackSummary,
  ConsensusDetails,
  ReviewQueueFilters,
  DashboardStatsFilters,
  PendingReviewStats,
  VacancyStats,
  RecentActivity,
};
