/**
 * Client Tenants API Client
 *
 * This module provides clients for managing client tenant relationships between
 * recruitment agencies and their client organizations with proper error handling
 * and type safety.
 *
 * @example
 * ```ts
 * import { clientTenantsClient } from '@/api/clientTenants';
 *
 * // List all client tenants for an agency
 * const tenants = await clientTenantsClient.listClientTenants('agency-id');
 *
 * // Create a new client tenant
 * const newTenant = await clientTenantsClient.createClientTenant({
 *   agency_id: 'agency-id',
 *   organization_id: 'org-id',
 *   status: 'active'
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError } from '@/types/api';

/**
 * Default API configuration for client tenants client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Client tenant status enum
 */
export enum ClientTenantStatus {
  Active = 'active',
  Inactive = 'inactive',
  Suspended = 'suspended',
}

/**
 * Client tenant create request
 */
export interface ClientTenantCreate {
  agency_id: string;
  organization_id: string;
  status?: string;
  is_primary?: boolean;
}

/**
 * Client tenant update request
 */
export interface ClientTenantUpdate {
  status?: string;
  is_primary?: boolean;
}

/**
 * Client tenant response
 */
export interface ClientTenantResponse {
  id: string;
  agency_id: string;
  organization_id: string;
  status: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Client tenant list response
 */
export interface ClientTenantListResponse {
  client_tenants: ClientTenantResponse[];
  total_count: number;
}

/**
 * Client Tenants API Client class
 *
 * Provides methods for managing client tenant relationships with proper error
 * handling and type safety.
 */
export class ClientTenantsClient {
  private client: AxiosInstance;

  /**
   * Create a new Client Tenants client instance
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

  // ==================== Client Tenants ====================

  /**
   * Create a client tenant
   *
   * @param request - Create request with client tenant details
   * @returns Created client tenant
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const tenant = await clientTenantsClient.createClientTenant({
   *   agency_id: 'agency-123',
   *   organization_id: 'org-456',
   *   status: 'active',
   *   is_primary: true
   * });
   * ```
   */
  async createClientTenant(request: ClientTenantCreate): Promise<ClientTenantResponse> {
    try {
      const response: AxiosResponse<ClientTenantResponse> = await this.client.post(
        '/api/client-tenants/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List client tenants with optional filters
   *
   * @param agencyId - Optional agency ID filter
   * @param organizationId - Optional organization ID filter
   * @param status - Optional status filter
   * @param skip - Number of records to skip (pagination)
   * @param limit - Maximum number of records to return
   * @returns List of client tenants
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all client tenants
   * const tenants = await clientTenantsClient.listClientTenants();
   *
   * // Get tenants for a specific agency
   * const agencyTenants = await clientTenantsClient.listClientTenants('agency-123');
   * ```
   */
  async listClientTenants(
    agencyId?: string,
    organizationId?: string,
    status?: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<ClientTenantListResponse> {
    try {
      const params: Record<string, string | number> = { skip, limit };
      if (agencyId) params.agency_id = agencyId;
      if (organizationId) params.organization_id = organizationId;
      if (status) params.status = status;

      const response: AxiosResponse<ClientTenantListResponse> = await this.client.get(
        '/api/client-tenants/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific client tenant by ID
   *
   * @param tenantId - Client tenant ID
   * @returns Client tenant details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const tenant = await clientTenantsClient.getClientTenant('tenant-uuid');
   * ```
   */
  async getClientTenant(tenantId: string): Promise<ClientTenantResponse> {
    try {
      const response: AxiosResponse<ClientTenantResponse> = await this.client.get(
        `/api/client-tenants/${tenantId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a client tenant
   *
   * @param tenantId - Client tenant ID
   * @param request - Update request with fields to modify
   * @returns Updated client tenant
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await clientTenantsClient.updateClientTenant('tenant-uuid', {
   *   status: 'suspended'
   * });
   * ```
   */
  async updateClientTenant(
    tenantId: string,
    request: ClientTenantUpdate
  ): Promise<ClientTenantResponse> {
    try {
      const response: AxiosResponse<ClientTenantResponse> = await this.client.put(
        `/api/client-tenants/${tenantId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a client tenant
   *
   * @param tenantId - Client tenant ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await clientTenantsClient.deleteClientTenant('tenant-uuid');
   * ```
   */
  async deleteClientTenant(tenantId: string): Promise<void> {
    try {
      await this.client.delete(`/api/client-tenants/${tenantId}`);
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
 * Default client tenants client instance
 *
 * Use this singleton instance for all client tenants API calls.
 */
export const clientTenantsClient = new ClientTenantsClient();

/**
 * Export client tenants client class for custom instances
 */
export default ClientTenantsClient;
