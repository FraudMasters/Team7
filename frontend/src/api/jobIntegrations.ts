/**
 * Job Board Integrations API Client
 *
 * This module provides a client for managing job board integrations,
 * including creating, reading, updating, and deleting integration configurations,
 * as well as viewing import logs and toggling integration status.
 * Integrations enable automatic resume imports from external job boards
 * (Indeed, ZipRecruiter, Glassdoor) and custom webhook sources.
 *
 * @example
 * ```ts
 * import { jobIntegrationsClient } from '@/api/jobIntegrations';
 *
 * // List all integrations
 * const integrations = await jobIntegrationsClient.listIntegrations();
 *
 * // Create a new integration
 * const newIntegration = await jobIntegrationsClient.createIntegration({
 *   name: 'Indeed',
 *   api_endpoint: 'https://api.indeed.com/v2',
 *   api_key: 'your-api-key',
 *   enabled: true
 * });
 *
 * // Toggle integration status
 * await jobIntegrationsClient.toggleIntegration('integration-id');
 *
 * // View import logs
 * const logs = await jobIntegrationsClient.listImportLogs();
 *
 * // Update an integration
 * const updated = await jobIntegrationsClient.updateIntegration('integration-id', {
 *   enabled: false
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  JobBoardIntegrationCreate,
  JobBoardIntegrationUpdate,
  JobBoardIntegrationResponse,
  JobBoardIntegrationListResponse,
  ImportLogResponse,
  ImportLogListResponse,
  ManualImportTriggerResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for job integrations client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Job Board Integrations API Client class
 *
 * Provides methods for managing job board integration configurations with proper
 * error handling and type safety.
 */
export class JobIntegrationsClient {
  private client: AxiosInstance;

  /**
   * Create a new JobIntegrations client instance
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
   * Create a job board integration
   *
   * @param request - Create request with integration details
   * @returns Created job board integration
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const integration = await jobIntegrationsClient.createIntegration({
   *   name: 'Indeed',
   *   api_endpoint: 'https://api.indeed.com/v2',
   *   api_key: 'your-api-key',
   *   enabled: true,
   *   config: { polling_interval: 3600 }
   * });
   * ```
   */
  async createIntegration(request: JobBoardIntegrationCreate): Promise<JobBoardIntegrationResponse> {
    try {
      const response: AxiosResponse<JobBoardIntegrationResponse> = await this.client.post(
        '/api/integrations/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List job board integrations with pagination
   *
   * @param skip - Number of records to skip (pagination)
   * @param limit - Maximum number of records to return
   * @returns List of job board integrations
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get first page of integrations
   * const integrations = await jobIntegrationsClient.listIntegrations(0, 20);
   *
   * // Get second page
   * const page2 = await jobIntegrationsClient.listIntegrations(20, 20);
   * ```
   */
  async listIntegrations(
    skip: number = 0,
    limit: number = 50
  ): Promise<JobBoardIntegrationListResponse> {
    try {
      const response: AxiosResponse<JobBoardIntegrationListResponse> = await this.client.get(
        '/api/integrations/',
        { params: { skip, limit } }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific job board integration by ID
   *
   * @param integrationId - Integration ID
   * @returns Job board integration details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const integration = await jobIntegrationsClient.getIntegration('integration-uuid');
   * ```
   */
  async getIntegration(integrationId: string): Promise<JobBoardIntegrationResponse> {
    try {
      const response: AxiosResponse<JobBoardIntegrationResponse> = await this.client.get(
        `/api/integrations/${integrationId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a job board integration
   *
   * @param integrationId - Integration ID
   * @param request - Update request with fields to modify
   * @returns Updated job board integration
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await jobIntegrationsClient.updateIntegration('integration-uuid', {
   *   name: 'Indeed (Updated)',
   *   enabled: false
   * });
   * ```
   */
  async updateIntegration(
    integrationId: string,
    request: JobBoardIntegrationUpdate
  ): Promise<JobBoardIntegrationResponse> {
    try {
      const response: AxiosResponse<JobBoardIntegrationResponse> = await this.client.put(
        `/api/integrations/${integrationId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a job board integration
   *
   * @param integrationId - Integration ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await jobIntegrationsClient.deleteIntegration('integration-uuid');
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
   * Toggle a job board integration enabled/disabled status
   *
   * @param integrationId - Integration ID
   * @returns Response with updated status
   * @throws ApiError if toggle fails
   *
   * @example
   * ```ts
   * const result = await jobIntegrationsClient.toggleIntegration('integration-uuid');
   * console.log(result.message); // "Integration enabled" or "Integration disabled"
   * ```
   */
  async toggleIntegration(
    integrationId: string
  ): Promise<{ id: string; enabled: boolean; message: string }> {
    try {
      const response = await this.client.patch(
        `/api/integrations/${integrationId}/toggle`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List import logs with pagination and optional status filtering
   *
   * @param skip - Number of records to skip (pagination)
   * @param limit - Maximum number of records to return
   * @param statusFilter - Optional filter by import status (success, failed, partial, skipped, in_progress)
   * @returns List of import logs
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all import logs
   * const logs = await jobIntegrationsClient.listImportLogs();
   *
   * // Get only failed imports
   * const failedLogs = await jobIntegrationsClient.listImportLogs(0, 50, 'failed');
   *
   * // Get second page of successful imports
   * const successLogs = await jobIntegrationsClient.listImportLogs(50, 50, 'success');
   * ```
   */
  async listImportLogs(
    skip: number = 0,
    limit: number = 50,
    statusFilter?: string
  ): Promise<ImportLogListResponse> {
    try {
      const params: Record<string, number | string> = { skip, limit };
      if (statusFilter) params.status_filter = statusFilter;

      const response: AxiosResponse<ImportLogListResponse> = await this.client.get(
        '/api/integrations/logs',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Trigger a manual import for a specific job board integration
   *
   * This endpoint manually triggers the poll_job_board Celery task for the specified
   * integration, allowing users to import applicants on-demand without waiting for
   * the scheduled polling interval.
   *
   * @param integrationId - Integration ID
   * @returns Response with task ID and status
   * @throws ApiError if trigger fails
   *
   * @example
   * ```ts
   * const result = await jobIntegrationsClient.triggerManualImport('integration-uuid');
   * console.log(result.task_id); // 'abc-123-def'
   * console.log(result.message); // 'Import task triggered successfully'
   * ```
   */
  async triggerManualImport(
    integrationId: string
  ): Promise<ManualImportTriggerResponse> {
    try {
      const response = await this.client.post(
        `/api/integrations/${integrationId}/trigger-import`
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
 * Default job integrations client instance
 *
 * Use this singleton instance for all job integrations calls.
 */
export const jobIntegrationsClient = new JobIntegrationsClient();

/**
 * Export job integrations client class for custom instances
 */
export default JobIntegrationsClient;
