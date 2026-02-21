/**
 * Candidate Queue API Service
 *
 * Provides methods for interacting with the candidate review queue endpoints.
 * Supports queue listing, filtering, priority management, and recruiter assignments.
 */
import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError } from '@/types/api';

// ==================== Response Types ====================

/**
 * Priority levels for queue items
 */
export type QueuePriority = 'urgent' | 'high' | 'medium' | 'low';

/**
 * Status values for queue items
 */
export type QueueStatus = 'pending' | 'in_review' | 'completed' | 'skipped';

/**
 * Single queue item response
 */
export interface QueueItemResponse {
  id: string;
  resume_id: string;
  filename: string | null;
  vacancy_id: string | null;
  vacancy_title: string | null;
  priority: QueuePriority;
  status: QueueStatus;
  assigned_recruiter_id: string | null;
  queue_entered_at: string;
  review_started_at: string | null;
  review_completed_at: string | null;
  notes: string | null;
  wait_time_hours: number | null;
  created_at: string;
  updated_at: string;
}

/**
 * Queue list response with pagination
 */
export interface QueueListResponse {
  total: number;
  items: QueueItemResponse[];
  skip: number;
  limit: number;
}

/**
 * Queue counts by status
 */
export interface QueueCountsResponse {
  pending: number;
  in_review: number;
  completed: number;
  skipped: number;
  total: number;
}

/**
 * Comprehensive queue metrics
 */
export interface QueueMetricsResponse {
  counts: QueueCountsResponse;
  average_wait_time_hours: number | null;
  median_wait_time_hours: number | null;
  oldest_pending_at: string | null;
  throughput_last_24h: number;
  throughput_last_7d: number;
}

/**
 * Result of a single assignment in a bulk operation
 */
export interface AssignCandidateResult {
  resume_id: string;
  success: boolean;
  queue_item_id: string | null;
  previous_recruiter_id: string | null;
  message: string;
}

/**
 * Bulk assignment response
 */
export interface AssignCandidatesResponse {
  total_requested: number;
  successful: number;
  failed: number;
  results: AssignCandidateResult[];
}

/**
 * Priority update response
 */
export interface UpdatePriorityResponse {
  id: string;
  resume_id: string;
  previous_priority: QueuePriority;
  new_priority: QueuePriority;
  message: string;
}

// ==================== Filter Types ====================

/**
 * Filters for the candidate queue
 */
export interface CandidateQueueFilters {
  vacancy_id?: string;
  status?: QueueStatus;
  priority?: QueuePriority;
  assigned_recruiter_id?: string;
  entered_after?: string;
  entered_before?: string;
  sort_by?: 'priority' | 'wait_time' | 'created_at';
  sort_order?: 'asc' | 'desc';
  skip?: number;
  limit?: number;
}

/**
 * Request to update priority
 */
export interface UpdatePriorityRequest {
  priority: QueuePriority;
}

/**
 * Request to assign candidates to a recruiter
 */
export interface AssignCandidatesRequest {
  resume_ids: string[];
  recruiter_id: string;
}

/**
 * Candidate Queue API Service class
 *
 * Provides methods for interacting with the candidate review queue endpoints.
 * Includes comprehensive error handling and type safety.
 */
class CandidateQueueApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
      timeout: 10000, // 10 seconds for queue operations
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('Candidate Queue API error:', error);
        throw this.transformError(error);
      }
    );
  }

  /**
   * Transform Axios error to ApiError format
   */
  private transformError(error: unknown): ApiError {
    const axiosError = error as AxiosError<{ detail?: string }>;

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

    const status = axiosError.response.status;
    const data = axiosError.response.data;

    if (data?.detail) {
      return { detail: data.detail, status };
    }

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
      detail: defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * Get candidate queue with optional filters
   *
   * @param filters - Optional filters for the queue
   * @returns Promise with queue list response
   */
  async getQueue(filters?: CandidateQueueFilters): Promise<QueueListResponse> {
    const params: Record<string, string | number> = {};

    if (filters?.vacancy_id) params.vacancy_id = filters.vacancy_id;
    if (filters?.status) params.status = filters.status;
    if (filters?.priority) params.priority = filters.priority;
    if (filters?.assigned_recruiter_id)
      params.assigned_recruiter_id = filters.assigned_recruiter_id;
    if (filters?.entered_after) params.entered_after = filters.entered_after;
    if (filters?.entered_before) params.entered_before = filters.entered_before;
    if (filters?.sort_by) params.sort_by = filters.sort_by;
    if (filters?.sort_order) params.sort_order = filters.sort_order;
    if (filters?.skip !== undefined) params.skip = filters.skip;
    if (filters?.limit !== undefined) params.limit = filters.limit;

    const response: AxiosResponse<QueueListResponse> = await this.client.get(
      '/api/candidate-queue/',
      { params }
    );
    return response.data;
  }

  /**
   * Get a single queue item by ID
   *
   * @param queueItemId - UUID of the queue item
   * @returns Promise with queue item response
   */
  async getQueueItem(queueItemId: string): Promise<QueueItemResponse> {
    const response: AxiosResponse<QueueItemResponse> = await this.client.get(
      `/api/candidate-queue/${queueItemId}`
    );
    return response.data;
  }

  /**
   * Get queue counts by status
   *
   * @param vacancyId - Optional vacancy ID to filter counts
   * @returns Promise with counts by status
   */
  async getQueueCounts(vacancyId?: string): Promise<QueueCountsResponse> {
    const params: Record<string, string> = {};
    if (vacancyId) params.vacancy_id = vacancyId;

    const response: AxiosResponse<QueueCountsResponse> = await this.client.get(
      '/api/candidate-queue/counts',
      { params }
    );
    return response.data;
  }

  /**
   * Get comprehensive queue metrics
   *
   * @param vacancyId - Optional vacancy ID to filter metrics
   * @returns Promise with queue metrics including wait times and throughput
   */
  async getQueueMetrics(vacancyId?: string): Promise<QueueMetricsResponse> {
    const params: Record<string, string> = {};
    if (vacancyId) params.vacancy_id = vacancyId;

    const response: AxiosResponse<QueueMetricsResponse> = await this.client.get(
      '/api/candidate-queue/metrics',
      { params }
    );
    return response.data;
  }

  /**
   * Update priority for a queue item
   *
   * @param queueItemId - UUID of the queue item
   * @param request - Priority update request
   * @returns Promise with update response
   */
  async updatePriority(
    queueItemId: string,
    request: UpdatePriorityRequest
  ): Promise<UpdatePriorityResponse> {
    const response: AxiosResponse<UpdatePriorityResponse> = await this.client.put(
      `/api/candidate-queue/${queueItemId}/priority`,
      request
    );
    return response.data;
  }

  /**
   * Assign candidates to a recruiter
   *
   * @param request - Assignment request with resume IDs and recruiter ID
   * @returns Promise with assignment response
   */
  async assignCandidates(request: AssignCandidatesRequest): Promise<AssignCandidatesResponse> {
    const response: AxiosResponse<AssignCandidatesResponse> = await this.client.post(
      '/api/candidate-queue/assign',
      request
    );
    return response.data;
  }
}

// Export singleton instance
export const candidateQueueApi = new CandidateQueueApiService();
export default candidateQueueApi;
