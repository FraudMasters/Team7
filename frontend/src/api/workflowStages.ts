/**
 * Workflow Stages API Client
 *
 * This module provides a client for managing organization-specific hiring
 * workflow stages, including creating, reading, updating, and deleting
 * workflow stage configurations.
 *
 * @example
 * ```ts
 * import { workflowStagesClient } from '@/api/workflowStages';
 *
 * // List all workflow stages for an organization
 * const stages = await workflowStagesClient.listStages('org-123');
 *
 * // Create a new workflow stage
 * const newStage = await workflowStagesClient.createStage({
 *   organization_id: 'org-123',
 *   stage_name: 'Technical Interview',
 *   stage_order: 3,
 *   is_active: true,
 *   color: '#3B82F6',
 *   description: 'Technical assessment with engineering team'
 * });
 *
 * // Update a workflow stage
 * const updated = await workflowStagesClient.updateStage('stage-id', {
 *   stage_name: 'Updated Technical Interview',
 *   is_active: false
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  WorkflowStageCreate,
  WorkflowStageUpdate,
  WorkflowStageResponse,
  WorkflowStageListResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for workflow stages client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Workflow Stages API Client class
 *
 * Provides methods for managing workflow stage configurations with proper
 * error handling and type safety.
 */
export class WorkflowStagesClient {
  private client: AxiosInstance;

  /**
   * Create a new WorkflowStages client instance
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
      409: 'A workflow stage with this name already exists.',
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
   * Create a workflow stage for an organization
   *
   * @param request - Create request with workflow stage details
   * @returns Created workflow stage
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const stage = await workflowStagesClient.createStage({
   *   organization_id: 'org-123',
   *   stage_name: 'Technical Interview',
   *   stage_order: 3,
   *   is_active: true,
   *   color: '#3B82F6',
   *   description: 'Technical assessment with engineering team'
   * });
   * ```
   */
  async createStage(request: WorkflowStageCreate): Promise<WorkflowStageResponse> {
    try {
      const response: AxiosResponse<WorkflowStageResponse> = await this.client.post(
        '/api/workflow-stages/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List workflow stages with optional filters
   *
   * @param organizationId - Optional organization ID filter
   * @param isActive - Optional active status filter
   * @param isDefault - Optional default status filter
   * @returns List of workflow stages
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all stages for an organization
   * const stages = await workflowStagesClient.listStages('org-123');
   *
   * // Get only active stages
   * const activeStages = await workflowStagesClient.listStages('org-123', true);
   * ```
   */
  async listStages(
    organizationId?: string,
    isActive?: boolean,
    isDefault?: boolean
  ): Promise<WorkflowStageListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (isActive !== undefined) params.is_active = isActive;
      if (isDefault !== undefined) params.is_default = isDefault;

      const response: AxiosResponse<WorkflowStageListResponse> = await this.client.get(
        '/api/workflow-stages/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific workflow stage by ID
   *
   * @param stageId - Workflow stage ID
   * @returns Workflow stage details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const stage = await workflowStagesClient.getStage('stage-uuid');
   * ```
   */
  async getStage(stageId: string): Promise<WorkflowStageResponse> {
    try {
      const response: AxiosResponse<WorkflowStageResponse> = await this.client.get(
        `/api/workflow-stages/${stageId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a workflow stage
   *
   * @param stageId - Workflow stage ID
   * @param request - Update request with fields to modify
   * @returns Updated workflow stage
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await workflowStagesClient.updateStage('stage-uuid', {
   *   stage_name: 'Updated Technical Interview',
   *   is_active: false
   * });
   * ```
   */
  async updateStage(
    stageId: string,
    request: WorkflowStageUpdate
  ): Promise<WorkflowStageResponse> {
    try {
      const response: AxiosResponse<WorkflowStageResponse> = await this.client.put(
        `/api/workflow-stages/${stageId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a workflow stage
   *
   * @param stageId - Workflow stage ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await workflowStagesClient.deleteStage('stage-uuid');
   * ```
   */
  async deleteStage(stageId: string): Promise<void> {
    try {
      await this.client.delete(`/api/workflow-stages/${stageId}`);
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
 * Default workflow stages client instance
 *
 * Use this singleton instance for all workflow stages calls.
 */
export const workflowStagesClient = new WorkflowStagesClient();

/**
 * Export workflow stages client class for custom instances
 */
export default WorkflowStagesClient;
