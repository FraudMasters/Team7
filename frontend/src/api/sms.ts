/**
 * SMS API Client
 *
 * This module provides a client for managing SMS communications with candidates,
 * including sending SMS messages, tracking delivery status, and retrieving SMS history.
 *
 * @example
 * ```ts
 * import { smsClient } from '@/api/sms';
 *
 * // Send an SMS message
 * const sms = await smsClient.send({
 *   candidate_id: 'resume-123',
 *   to_number: '+1234567890',
 *   message: 'Hello! We would like to schedule an interview.',
 *   provider: 'Twilio',
 *   recruiter_id: 'recruiter-123'
 * });
 *
 * // List SMS messages for a candidate
 * const messages = await smsClient.list('resume-123');
 *
 * // Get delivery status
 * const status = await smsClient.getDeliveryStatus(undefined, 'sms-id');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError } from '@/types/api';

/**
 * SMS send request
 */
export interface SMSSendRequest {
  candidate_id: string;
  recruiter_id?: string;
  to_number: string;
  from_number?: string;
  message: string;
  provider: string;
  vacancy_id?: string;
}

/**
 * SMS response
 */
export interface SMSResponse {
  id: string;
  communication_id: string;
  candidate_id: string;
  recruiter_id: string | null;
  to_number: string;
  from_number: string | null;
  message: string;
  provider: string;
  delivery_status: string;
  delivery_error: string | null;
  provider_message_id: string | null;
  segment_count: number | null;
  sent_at: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * SMS list response
 */
export interface SMSListResponse {
  messages: SMSResponse[];
  total_count: number;
}

/**
 * Delivery status response
 */
export interface DeliveryStatusResponse {
  id: string;
  delivery_status: string;
  provider_message_id: string | null;
  delivery_error: string | null;
  sent_at: string | null;
  updated_at: string;
}

/**
 * Default API configuration for SMS client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * SMS API Client class
 *
 * Provides methods for managing SMS communications with proper
 * error handling and type safety.
 */
export class SMSClient {
  private client: AxiosInstance;

  /**
   * Create a new SMS client instance
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
      409: 'A conflict occurred with the existing SMS.',
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
   * Send an SMS message to a candidate
   *
   * @param request - Send request with SMS details
   * @returns Sent SMS message details
   * @throws ApiError if sending fails
   *
   * @example
   * ```ts
   * const sms = await smsClient.send({
   *   candidate_id: 'resume-123',
   *   to_number: '+1234567890',
   *   message: 'Hello! We would like to schedule an interview.',
   *   provider: 'Twilio',
   *   recruiter_id: 'recruiter-123'
   * });
   * ```
   */
  async send(request: SMSSendRequest): Promise<SMSResponse> {
    try {
      const response: AxiosResponse<SMSResponse> = await this.client.post(
        '/api/sms/send',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List SMS messages with optional filters
   *
   * @param candidateId - Optional candidate ID filter
   * @param recruiterId - Optional recruiter ID filter
   * @param provider - Optional SMS provider filter
   * @param deliveryStatus - Optional delivery status filter
   * @param limit - Maximum number of results to return (default: 100)
   * @param offset - Number of results to skip (default: 0)
   * @returns List of SMS messages
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all SMS messages for a candidate
   * const messages = await smsClient.list('resume-123');
   *
   * // Get only delivered SMS messages
   * const delivered = await smsClient.list(
   *   'resume-123',
   *   undefined,
   *   undefined,
   *   'delivered'
   * );
   *
   * // Get SMS messages from a specific provider
   * const twilioSms = await smsClient.list(
   *   undefined,
   *   undefined,
   *   'Twilio'
   * );
   * ```
   */
  async list(
    candidateId?: string,
    recruiterId?: string,
    provider?: string,
    deliveryStatus?: string,
    limit = 100,
    offset = 0
  ): Promise<SMSListResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (candidateId) params.candidate_id = candidateId;
      if (recruiterId) params.recruiter_id = recruiterId;
      if (provider) params.provider = provider;
      if (deliveryStatus) params.delivery_status = deliveryStatus;
      params.limit = limit;
      params.offset = offset;

      const response: AxiosResponse<SMSListResponse> = await this.client.get(
        '/api/sms/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific SMS message by ID
   *
   * @param id - SMS message ID
   * @returns SMS message details
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const sms = await smsClient.get('sms-id');
   * ```
   */
  async get(id: string): Promise<SMSResponse> {
    try {
      const response: AxiosResponse<SMSResponse> = await this.client.get(
        `/api/sms/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get delivery status for an SMS message
   *
   * @param providerMessageId - Optional provider message ID to query
   * @param smsId - Optional SMS ID to query
   * @returns Delivery status information
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * // Query by SMS ID
   * const status = await smsClient.getDeliveryStatus(undefined, 'sms-id');
   *
   * // Query by provider message ID
   * const status = await smsClient.getDeliveryStatus('provider-msg-id');
   * ```
   */
  async getDeliveryStatus(
    providerMessageId?: string,
    smsId?: string
  ): Promise<DeliveryStatusResponse> {
    try {
      const params: Record<string, string> = {};
      if (providerMessageId) params.provider_message_id = providerMessageId;
      if (smsId) params.sms_id = smsId;

      const response: AxiosResponse<DeliveryStatusResponse> = await this.client.get(
        '/api/sms/delivery-status',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

/**
 * Default SMS client instance
 */
export const smsClient = new SMSClient();
