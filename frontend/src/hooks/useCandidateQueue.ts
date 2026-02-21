/**
 * Candidate Queue Hooks
 *
 * React Query hooks for fetching and managing the candidate review queue.
 * Provides hooks for listing queue items, fetching metrics, and updating
 * candidate priority and assignments.
 *
 * @example
 * ```tsx
 * import { useCandidateQueue, useQueueMetrics, useUpdatePriority } from '@/hooks/useCandidateQueue';
 *
 * function ReviewQueuePage() {
 *   const { data: queue, isLoading } = useCandidateQueue({ status: 'pending' });
 *   const { data: metrics } = useQueueMetrics();
 *   const updatePriority = useUpdatePriority();
 *
 *   if (isLoading) return <Loading />;
 *   return (
 *     <div>
 *       {metrics && <MetricsDisplay data={metrics} />}
 *       {queue?.items.map(item => <QueueItem key={item.id} item={item} />)}
 *     </div>
 *   );
 * }
 * ```
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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

// ==================== API Client ====================

/**
 * Default API configuration for candidate queue client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? import.meta.env.VITE_API_GATEWAY_URL ?? '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Candidate Queue API Client class
 *
 * Provides methods for the candidate queue operations with proper
 * error handling and type safety.
 */
class CandidateQueueClient {
  private client: AxiosInstance;

  constructor(config: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };
    this.client = axios.create(finalConfig);

    this.client.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(this.transformError(error))
    );
  }

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
      detail: data?.detail || defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * Get candidate queue with optional filters
   */
  async getQueue(filters?: CandidateQueueFilters): Promise<QueueListResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (filters?.vacancy_id) params.vacancy_id = filters.vacancy_id;
      if (filters?.status) params.status = filters.status;
      if (filters?.priority) params.priority = filters.priority;
      if (filters?.assigned_recruiter_id) params.assigned_recruiter_id = filters.assigned_recruiter_id;
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
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a single queue item by ID
   */
  async getQueueItem(queueItemId: string): Promise<QueueItemResponse> {
    try {
      const response: AxiosResponse<QueueItemResponse> = await this.client.get(
        `/api/candidate-queue/${queueItemId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get queue counts by status
   */
  async getQueueCounts(vacancyId?: string): Promise<QueueCountsResponse> {
    try {
      const params: Record<string, string> = {};
      if (vacancyId) params.vacancy_id = vacancyId;

      const response: AxiosResponse<QueueCountsResponse> = await this.client.get(
        '/api/candidate-queue/counts',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get comprehensive queue metrics
   */
  async getQueueMetrics(vacancyId?: string): Promise<QueueMetricsResponse> {
    try {
      const params: Record<string, string> = {};
      if (vacancyId) params.vacancy_id = vacancyId;

      const response: AxiosResponse<QueueMetricsResponse> = await this.client.get(
        '/api/candidate-queue/metrics',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update priority for a queue item
   */
  async updatePriority(
    queueItemId: string,
    request: UpdatePriorityRequest
  ): Promise<UpdatePriorityResponse> {
    try {
      const response: AxiosResponse<UpdatePriorityResponse> = await this.client.put(
        `/api/candidate-queue/${queueItemId}/priority`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Assign candidates to a recruiter
   */
  async assignCandidates(request: AssignCandidatesRequest): Promise<AssignCandidatesResponse> {
    try {
      const response: AxiosResponse<AssignCandidatesResponse> = await this.client.post(
        '/api/candidate-queue/assign',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

/**
 * Default candidate queue client instance
 */
export const candidateQueueClient = new CandidateQueueClient();

// ==================== React Query Hooks ====================

/**
 * Hook for fetching the candidate review queue with filters
 *
 * @param filters - Optional filters for the queue
 * @returns Query result with queue data
 *
 * @example
 * ```tsx
 * // Get all pending candidates
 * const { data, isLoading } = useCandidateQueue({ status: 'pending' });
 *
 * // Get high priority items for a specific vacancy
 * const { data } = useCandidateQueue({
 *   vacancy_id: 'vacancy-123',
 *   priority: 'high'
 * });
 *
 * // Sort by wait time (oldest first)
 * const { data } = useCandidateQueue({
 *   sort_by: 'wait_time',
 *   sort_order: 'asc'
 * });
 * ```
 */
export function useCandidateQueue(filters?: CandidateQueueFilters) {
  return useQuery({
    queryKey: ['candidate-queue', filters],
    queryFn: () => candidateQueueClient.getQueue(filters),
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

/**
 * Hook for fetching a single queue item by ID
 *
 * @param queueItemId - UUID of the queue item
 * @returns Query result with queue item data
 */
export function useQueueItem(queueItemId: string | undefined) {
  return useQuery({
    queryKey: ['candidate-queue-item', queueItemId],
    queryFn: () => candidateQueueClient.getQueueItem(queueItemId!),
    enabled: !!queueItemId,
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

/**
 * Hook for fetching queue counts by status
 *
 * @param vacancyId - Optional vacancy ID to filter counts
 * @returns Query result with counts by status
 */
export function useQueueCounts(vacancyId?: string) {
  return useQuery({
    queryKey: ['candidate-queue-counts', vacancyId],
    queryFn: () => candidateQueueClient.getQueueCounts(vacancyId),
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

/**
 * Hook for fetching comprehensive queue metrics
 *
 * @param vacancyId - Optional vacancy ID to filter metrics
 * @returns Query result with queue metrics including wait times and throughput
 *
 * @example
 * ```tsx
 * const { data: metrics } = useQueueMetrics();
 * if (metrics) {
 *   console.log(`Pending: ${metrics.counts.pending}`);
 *   console.log(`Avg wait time: ${metrics.average_wait_time_hours}h`);
 *   console.log(`24h throughput: ${metrics.throughput_last_24h}`);
 * }
 * ```
 */
export function useQueueMetrics(vacancyId?: string) {
  return useQuery({
    queryKey: ['candidate-queue-metrics', vacancyId],
    queryFn: () => candidateQueueClient.getQueueMetrics(vacancyId),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook for updating a queue item's priority
 *
 * Invalidates queue queries on success.
 *
 * @returns Mutation for updating priority
 *
 * @example
 * ```tsx
 * const updatePriority = useUpdatePriority();
 *
 * // Update priority
 * updatePriority.mutate({
 *   queueItemId: 'item-123',
 *   priority: 'urgent'
 * }, {
 *   onSuccess: (data) => {
 *     console.log(`Priority updated from ${data.previous_priority} to ${data.new_priority}`);
 *   }
 * });
 * ```
 */
export function useUpdatePriority() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      queueItemId,
      priority,
    }: {
      queueItemId: string;
      priority: QueuePriority;
    }) => candidateQueueClient.updatePriority(queueItemId, { priority }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate-queue'] });
      queryClient.invalidateQueries({ queryKey: ['candidate-queue-item'] });
      queryClient.invalidateQueries({ queryKey: ['candidate-queue-metrics'] });
    },
  });
}

/**
 * Hook for assigning candidates to a recruiter
 *
 * Invalidates queue queries on success.
 *
 * @returns Mutation for assigning candidates
 *
 * @example
 * ```tsx
 * const assignCandidates = useAssignCandidates();
 *
 * // Assign multiple candidates to a recruiter
 * assignCandidates.mutate({
 *   resume_ids: ['resume-1', 'resume-2'],
 *   recruiter_id: 'recruiter-123'
 * }, {
 *   onSuccess: (data) => {
 *     console.log(`Assigned ${data.successful} candidates`);
 *     console.log(`Failed ${data.failed} candidates`);
 *   }
 * });
 * ```
 */
export function useAssignCandidates() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: AssignCandidatesRequest) =>
      candidateQueueClient.assignCandidates(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate-queue'] });
      queryClient.invalidateQueries({ queryKey: ['candidate-queue-counts'] });
      queryClient.invalidateQueries({ queryKey: ['candidate-queue-metrics'] });
    },
  });
}

// Re-export types for convenience
export type {
  QueueItemResponse,
  QueueListResponse,
  QueueCountsResponse,
  QueueMetricsResponse,
  AssignCandidateResult,
  AssignCandidatesResponse,
  UpdatePriorityResponse,
  CandidateQueueFilters,
  UpdatePriorityRequest,
  AssignCandidatesRequest,
};
