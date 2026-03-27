/**
 * Agencies API Client
 *
 * This module provides clients for managing recruitment agencies with proper
 * error handling and type safety.
 *
 * @example
 * ```ts
 * import { agenciesClient } from '@/api/agencies';
 *
 * // List all agencies
 * const agencies = await agenciesClient.listAgencies();
 *
 * // Create a new agency
 * const newAgency = await agenciesClient.createAgency({
 *   name: 'Elite Recruiters',
 *   slug: 'elite-recruiters',
 *   domain: 'elite.com'
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError } from '@/types/api';

/**
 * Default API configuration for agencies client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Agency create request
 */
export interface AgencyCreate {
  name: string;
  slug: string;
  domain?: string;
  logo_url?: string;
  contact_email?: string;
  contact_phone?: string;
  is_active?: boolean;
}

/**
 * Agency update request
 */
export interface AgencyUpdate {
  name?: string;
  slug?: string;
  domain?: string;
  logo_url?: string;
  contact_email?: string;
  contact_phone?: string;
  is_active?: boolean;
}

/**
 * Agency response
 */
export interface AgencyResponse {
  id: string;
  name: string;
  slug: string;
  domain?: string;
  logo_url?: string;
  contact_email?: string;
  contact_phone?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Agency list response
 */
export interface AgencyListResponse {
  agencies: AgencyResponse[];
  total_count: number;
}

/**
 * Agencies API Client class
 *
 * Provides methods for managing agencies with proper error handling and type safety.
 */
export class AgenciesClient {
  private client: AxiosInstance;

  /**
   * Create a new Agencies client instance
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
      409: 'A resource with these attributes already exists.',
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

  // ==================== Agencies ====================

  /**
   * Create an agency
   *
   * @param request - Create request with agency details
   * @returns Created agency
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const agency = await agenciesClient.createAgency({
   *   name: 'Elite Recruiters',
   *   slug: 'elite-recruiters',
   *   domain: 'elite.com',
   *   logo_url: 'https://elite.com/logo.png'
   * });
   * ```
   */
  async createAgency(request: AgencyCreate): Promise<AgencyResponse> {
    try {
      const response: AxiosResponse<AgencyResponse> = await this.client.post(
        '/api/agencies/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List agencies with optional filters
   *
   * @param isActive - Optional active status filter
   * @param search - Optional search query
   * @param skip - Number of records to skip (pagination)
   * @param limit - Maximum number of records to return
   * @returns List of agencies
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all agencies
   * const agencies = await agenciesClient.listAgencies();
   *
   * // Get only active agencies
   * const activeAgencies = await agenciesClient.listAgencies(true);
   * ```
   */
  async listAgencies(
    isActive?: boolean,
    search?: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<AgencyListResponse> {
    try {
      const params: Record<string, boolean | string | number> = { skip, limit };
      if (isActive !== undefined) params.is_active = isActive;
      if (search) params.search = search;

      const response: AxiosResponse<AgencyListResponse> = await this.client.get(
        '/api/agencies/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific agency by ID
   *
   * @param agencyId - Agency ID
   * @returns Agency details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const agency = await agenciesClient.getAgency('agency-id');
   * ```
   */
  async getAgency(agencyId: string): Promise<AgencyResponse> {
    try {
      const response: AxiosResponse<AgencyResponse> = await this.client.get(
        `/api/agencies/${agencyId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update an agency
   *
   * @param agencyId - Agency ID
   * @param request - Update request with fields to modify
   * @returns Updated agency
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await agenciesClient.updateAgency('agency-id', {
   *   name: 'Updated Agency Name',
   *   logo_url: 'https://example.com/new-logo.png'
   * });
   * ```
   */
  async updateAgency(
    agencyId: string,
    request: AgencyUpdate
  ): Promise<AgencyResponse> {
    try {
      const response: AxiosResponse<AgencyResponse> = await this.client.put(
        `/api/agencies/${agencyId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete an agency
   *
   * @param agencyId - Agency ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await agenciesClient.deleteAgency('agency-id');
   * ```
   */
  async deleteAgency(agencyId: string): Promise<void> {
    try {
      await this.client.delete(`/api/agencies/${agencyId}`);
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
 * Default agencies client instance
 *
 * Use this singleton instance for all agencies API calls.
 */
export const agenciesClient = new AgenciesClient();

/**
 * Export agencies client class for custom instances
 */
export default AgenciesClient;
