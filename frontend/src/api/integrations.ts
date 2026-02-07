/**
 * Integrations API Client
 *
 * This module provides a client for managing HRIS/ATS platform integrations,
 * including Workday, Greenhouse, Lever, BambooHR, and Ashby.
 *
 * Features include:
 * - CRUD operations for integration configurations
 * - Testing connections to external platforms
 * - Triggering sync operations (full and incremental)
 * - Viewing sync history and status
 *
 * @example
 * ```ts
 * import { integrationsClient } from '@/api/integrations';
 *
 * // List all integrations
 * const integrations = await integrationsClient.listIntegrations();
 *
 * // Create a new integration
 * const newIntegration = await integrationsClient.createIntegration({
 *   name: 'Workday Production',
 *   platform: 'workday',
 *   credentials: { api_url: '...', username: '...', password: '...' },
 *   sync_enabled: true,
 *   sync_interval_minutes: 60
 * });
 *
 * // Test connection
 * const testResult = await integrationsClient.testConnection('integration-id');
 *
 * // Trigger sync
 * const syncResult = await integrationsClient.triggerSync('integration-id', {
 *   sync_type: 'full'
 * });
 *
 * // Get sync history
 * const history = await integrationsClient.getSyncHistory('integration-id');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  IntegrationCreate,
  IntegrationUpdate,
  IntegrationResponse,
  IntegrationListResponse,
  TestConnectionResponse,
  SyncTriggerRequest,
  SyncTriggerResponse,
  SyncHistoryResponse,
  SyncStatusResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for integrations client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 30000, // 30 seconds for sync operations
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Integrations API Client class
 *
 * Provides methods for managing HRIS/ATS platform integrations with proper
 * error handling and type safety.
 */
export class IntegrationsClient {
  private client: AxiosInstance;

  /**
   * Create a new Integrations client instance
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
      409: 'An integration with this name already exists.',
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
   * Create a new integration configuration
   *
   * @param request - Create request with integration details
   * @returns Created integration
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const integration = await integrationsClient.createIntegration({
   *   name: 'Workday Production',
   *   platform: 'workday',
   *   credentials: {
   *     api_url: 'https://wd1.workday.com',
   *     username: 'user@example.com',
   *     password: 'secret'
   *   },
   *   organization_config: {
   *     company_id: '12345'
   *   },
   *   sync_enabled: true,
   *   sync_interval_minutes: 60
   * });
   * ```
   */
  async createIntegration(request: IntegrationCreate): Promise<IntegrationResponse> {
    try {
      const response: AxiosResponse<IntegrationResponse> = await this.client.post(
        '/api/integrations/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List all integrations with optional filters
   *
   * @param platform - Optional filter by platform type
   * @param status - Optional filter by status
   * @param skip - Number of records to skip (pagination)
   * @param limit - Maximum number of records to return
   * @returns List of integrations
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all integrations
   * const integrations = await integrationsClient.listIntegrations();
   *
   * // Filter by platform
   * const workdayIntegrations = await integrationsClient.listIntegrations('workday');
   *
   * // Filter by status
   * const activeIntegrations = await integrationsClient.listIntegrations(undefined, 'active');
   * ```
   */
  async listIntegrations(
    platform?: string,
    status?: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<IntegrationListResponse> {
    try {
      const params: Record<string, number | string> = { skip, limit };
      if (platform) params.platform = platform;
      if (status) params.status = status;

      const response: AxiosResponse<IntegrationListResponse> = await this.client.get(
        '/api/integrations/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific integration by ID
   *
   * @param integrationId - Integration ID
   * @returns Integration details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const integration = await integrationsClient.getIntegration('integration-uuid');
   * ```
   */
  async getIntegration(integrationId: string): Promise<IntegrationResponse> {
    try {
      const response: AxiosResponse<IntegrationResponse> = await this.client.get(
        `/api/integrations/${integrationId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update an integration configuration
   *
   * @param integrationId - Integration ID
   * @param request - Update request with fields to modify
   * @returns Updated integration
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await integrationsClient.updateIntegration('integration-uuid', {
   *   name: 'Updated Integration Name',
   *   sync_enabled: false
   * });
   * ```
   */
  async updateIntegration(
    integrationId: string,
    request: IntegrationUpdate
  ): Promise<IntegrationResponse> {
    try {
      const response: AxiosResponse<IntegrationResponse> = await this.client.put(
        `/api/integrations/${integrationId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete an integration configuration
   *
   * @param integrationId - Integration ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await integrationsClient.deleteIntegration('integration-uuid');
   * ```
   */
  async deleteIntegration(integrationId: string): Promise<void> {
    try {
      await this.client.delete(`/api/integrations/${integrationId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Test connection to an external platform
   *
   * @param integrationId - Integration ID
   * @returns Connection test result
   * @throws ApiError if test fails
   *
   * @example
   * ```ts
   * const result = await integrationsClient.testConnection('integration-uuid');
   * if (result.success) {
   *   console.log('Connection successful:', result.message);
   * } else {
   *   console.error('Connection failed:', result.message);
   * }
   * ```
   */
  async testConnection(integrationId: string): Promise<TestConnectionResponse> {
    try {
      const response: AxiosResponse<TestConnectionResponse> = await this.client.post(
        `/api/integrations/${integrationId}/test`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Trigger a sync operation for an integration
   *
   * @param integrationId - Integration ID
   * @param request - Sync trigger request
   * @returns Sync trigger response
   * @throws ApiError if trigger fails
   *
   * @example
   * ```ts
   * // Trigger full sync
   * const syncResult = await integrationsClient.triggerSync('integration-uuid', {
   *   sync_type: 'full'
   * });
   *
   * // Trigger incremental sync with force
   * const incrementalResult = await integrationsClient.triggerSync('integration-uuid', {
   *   sync_type: 'incremental',
   *   force: true
   * });
   * ```
   */
  async triggerSync(
    integrationId: string,
    request: SyncTriggerRequest
  ): Promise<SyncTriggerResponse> {
    try {
      const response: AxiosResponse<SyncTriggerResponse> = await this.client.post(
        `/api/integrations/${integrationId}/sync`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get sync history for an integration
   *
   * @param integrationId - Integration ID
   * @param skip - Number of records to skip (pagination)
   * @param limit - Maximum number of records to return
   * @returns Sync history
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const history = await integrationsClient.getSyncHistory('integration-uuid');
   * console.log(`Total syncs: ${history.total_syncs}`);
   * console.log(`Completed: ${history.completed_syncs}, Failed: ${history.failed_syncs}`);
   * ```
   */
  async getSyncHistory(
    integrationId: string,
    skip: number = 0,
    limit: number = 50
  ): Promise<SyncHistoryResponse> {
    try {
      const params: Record<string, number> = { skip, limit };

      const response: AxiosResponse<SyncHistoryResponse> = await this.client.get(
        `/api/integrations/${integrationId}/syncs`,
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get status of a specific sync operation
   *
   * @param integrationId - Integration ID
   * @param syncId - Sync operation ID
   * @returns Sync status
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const status = await integrationsClient.getSyncStatus('integration-uuid', 'sync-uuid');
   * console.log(`Sync status: ${status.status}`);
   * console.log(`Progress: ${status.records_successful}/${status.records_processed}`);
   * ```
   */
  async getSyncStatus(integrationId: string, syncId: string): Promise<SyncStatusResponse> {
    try {
      const response: AxiosResponse<SyncStatusResponse> = await this.client.get(
        `/api/integrations/${integrationId}/syncs/${syncId}`
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
 * Default integrations client instance
 *
 * Use this singleton instance for all integrations calls.
 */
export const integrationsClient = new IntegrationsClient();

/**
 * Export integrations client class for custom instances
 */
export default IntegrationsClient;
