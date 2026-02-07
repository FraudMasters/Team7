/**
 * Communications API Client
 *
 * This module provides a client for managing candidate communications,
 * including emails, SMS messages, phone calls, and in-system messages.
 *
 * @example
 * ```ts
 * import { communicationsClient } from '@/api/communications';
 *
 * // List all communications for a candidate
 * const communications = await communicationsClient.listCommunications('resume-123');
 *
 * // Create a new communication
 * const newComm = await communicationsClient.createCommunication({
 *   candidate_id: 'resume-123',
 *   type: 'email',
 *   direction: 'outbound',
 *   subject: 'Interview Invitation',
 *   body: 'We would like to invite you for an interview...',
 *   recruiter_id: 'recruiter-123'
 * });
 *
 * // Get communication metrics
 * const metrics = await communicationsClient.getMetrics();
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';

/**
 * Communication type enum
 */
export type CommunicationType = 'email' | 'sms' | 'phone_call' | 'in_system';

/**
 * Communication direction enum
 */
export type CommunicationDirection = 'inbound' | 'outbound';

/**
 * Communication status enum
 */
export type CommunicationStatus = 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced';

/**
 * Communication create request
 */
export interface CommunicationCreate {
  candidate_id: string;
  vacancy_id?: string;
  recruiter_id?: string;
  type: CommunicationType;
  direction: CommunicationDirection;
  status?: CommunicationStatus;
  subject?: string;
  body: string;
  sent_at?: string;
  received_at?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Communication update request
 */
export interface CommunicationUpdate {
  vacancy_id?: string;
  recruiter_id?: string;
  type?: CommunicationType;
  direction?: CommunicationDirection;
  status?: CommunicationStatus;
  subject?: string;
  body?: string;
  sent_at?: string;
  received_at?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Communication response
 */
export interface CommunicationResponse {
  id: string;
  candidate_id: string;
  vacancy_id: string | null;
  recruiter_id: string | null;
  type: CommunicationType;
  direction: CommunicationDirection;
  status: CommunicationStatus;
  subject: string | null;
  body: string;
  sent_at: string | null;
  received_at: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

/**
 * Communication list response
 */
export interface CommunicationListResponse {
  communications: CommunicationResponse[];
  total_count: number;
  filters_applied?: Record<string, unknown>;
}

/**
 * Response time metrics
 */
export interface ResponseTimeMetrics {
  average: number;
  median: number;
  min: number;
  max: number;
}

/**
 * Engagement metrics breakdown
 */
export interface EngagementBreakdown {
  email: number;
  sms: number;
  phone_call: number;
  in_system: number;
}

/**
 * Engagement metrics
 */
export interface EngagementMetrics {
  total_sent: number;
  total_responses: number;
  response_rate: number;
  breakdown_by_type: EngagementBreakdown;
  breakdown_by_status: Record<string, number>;
}

/**
 * Upcoming follow-up
 */
export interface UpcomingFollowup {
  communication_id: string;
  candidate_id: string;
  type: CommunicationType;
  subject: string | null;
  followup_date: string;
  priority: 'high' | 'medium' | 'low';
}

/**
 * Communication metrics response
 */
export interface CommunicationMetricsResponse {
  response_time: ResponseTimeMetrics;
  engagement: EngagementMetrics;
  upcoming_followups: UpcomingFollowup[];
  period_start?: string;
  period_end?: string;
}

/**
 * API error response
 */
export interface ApiError {
  detail: string;
  status?: number;
}

/**
 * Default API configuration for communications client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Communications API Client class
 *
 * Provides methods for managing candidate communications with proper
 * error handling and type safety.
 */
export class CommunicationsClient {
  private client: AxiosInstance;

  /**
   * Create a new Communications client instance
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
      409: 'A conflict occurred with the existing communication.',
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
   * Create a communication
   *
   * @param request - Create request with communication details
   * @returns Created communication
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const comm = await communicationsClient.createCommunication({
   *   candidate_id: 'resume-123',
   *   type: 'email',
   *   direction: 'outbound',
   *   subject: 'Interview Invitation',
   *   body: 'We would like to invite you for an interview...',
   *   recruiter_id: 'recruiter-123'
   * });
   * ```
   */
  async createCommunication(request: CommunicationCreate): Promise<CommunicationResponse> {
    try {
      const response: AxiosResponse<CommunicationResponse> = await this.client.post(
        '/api/communications/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List communications with optional filters
   *
   * @param candidateId - Optional candidate ID filter
   * @param vacancyId - Optional vacancy ID filter
   * @param recruiterId - Optional recruiter ID filter
   * @param type - Optional communication type filter
   * @param direction - Optional direction filter
   * @param status - Optional status filter
   * @param searchQuery - Optional search query for subject/body
   * @param dateRange - Optional date range (format: "YYYY-MM-DD,YYYY-MM-DD")
   * @param limit - Maximum number of results to return (default: 100)
   * @returns List of communications
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all communications for a candidate
   * const comms = await communicationsClient.listCommunications('resume-123');
   *
   * // Get only email communications
   * const emails = await communicationsClient.listCommunications(
   *   'resume-123',
   *   undefined,
   *   undefined,
   *   'email'
   * );
   *
   * // Search communications
   * const results = await communicationsClient.listCommunications(
   *   undefined,
   *   undefined,
   *   undefined,
   *   undefined,
   *   undefined,
   *   undefined,
   *   'interview'
   * );
   * ```
   */
  async listCommunications(
    candidateId?: string,
    vacancyId?: string,
    recruiterId?: string,
    type?: CommunicationType,
    direction?: CommunicationDirection,
    status?: CommunicationStatus,
    searchQuery?: string,
    dateRange?: string,
    limit = 100
  ): Promise<CommunicationListResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (candidateId) params.candidate_id = candidateId;
      if (vacancyId) params.vacancy_id = vacancyId;
      if (recruiterId) params.recruiter_id = recruiterId;
      if (type) params.type = type;
      if (direction) params.direction = direction;
      if (status) params.status = status;
      if (searchQuery) params.search_query = searchQuery;
      if (dateRange) params.date_range = dateRange;
      params.limit = limit;

      const response: AxiosResponse<CommunicationListResponse> = await this.client.get(
        '/api/communications/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific communication by ID
   *
   * @param id - Communication ID
   * @returns Communication details
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const comm = await communicationsClient.getCommunication('comm-id');
   * ```
   */
  async getCommunication(id: string): Promise<CommunicationResponse> {
    try {
      const response: AxiosResponse<CommunicationResponse> = await this.client.get(
        `/api/communications/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a communication
   *
   * @param id - Communication ID
   * @param request - Update request with fields to modify
   * @returns Updated communication
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await communicationsClient.updateCommunication('comm-id', {
   *   status: 'sent',
   *   sent_at: new Date().toISOString()
   * });
   * ```
   */
  async updateCommunication(
    id: string,
    request: CommunicationUpdate
  ): Promise<CommunicationResponse> {
    try {
      const response: AxiosResponse<CommunicationResponse> = await this.client.put(
        `/api/communications/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a communication
   *
   * @param id - Communication ID
   * @returns Deleted communication confirmation
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await communicationsClient.deleteCommunication('comm-id');
   * ```
   */
  async deleteCommunication(id: string): Promise<{ message: string }> {
    try {
      const response: AxiosResponse<{ message: string }> = await this.client.delete(
        `/api/communications/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Search communications by query
   *
   * This is a convenience method that wraps listCommunications with a search query.
   *
   * @param searchQuery - Search query for subject/body
   * @param candidateId - Optional candidate ID filter
   * @param type - Optional communication type filter
   * @param limit - Maximum number of results to return (default: 100)
   * @returns Filtered list of communications
   * @throws ApiError if search fails
   *
   * @example
   * ```ts
   * // Search for communications about interviews
   * const results = await communicationsClient.search('interview');
   *
   * // Search within a specific candidate's communications
   * const candidateResults = await communicationsClient.search(
   *   'salary',
   *   'resume-123'
   * );
   * ```
   */
  async search(
    searchQuery: string,
    candidateId?: string,
    type?: CommunicationType,
    limit = 100
  ): Promise<CommunicationListResponse> {
    return this.listCommunications(
      candidateId,
      undefined,
      undefined,
      type,
      undefined,
      undefined,
      searchQuery,
      undefined,
      limit
    );
  }

  /**
   * Get communication metrics
   *
   * @param startDate - Optional start date for metrics period (format: YYYY-MM-DD)
   * @param endDate - Optional end date for metrics period (format: YYYY-MM-DD)
   * @param limit - Maximum number of upcoming follow-ups to return (default: 10)
   * @returns Communication metrics
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * // Get all metrics
   * const metrics = await communicationsClient.getMetrics();
   *
   * // Get metrics for a specific date range
   * const metrics = await communicationsClient.getMetrics('2024-01-01', '2024-01-31');
   * ```
   */
  async getMetrics(
    startDate?: string,
    endDate?: string,
    limit = 10
  ): Promise<CommunicationMetricsResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      params.limit = limit;

      const response: AxiosResponse<CommunicationMetricsResponse> = await this.client.get(
        '/api/communications/metrics',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

/**
 * Default communications client instance
 */
export const communicationsClient = new CommunicationsClient();
