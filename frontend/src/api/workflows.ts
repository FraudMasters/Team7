/**
 * Workflows API Client
 *
 * Provides methods for managing workflow automations with triggers and actions.
 *
 * @module api/workflows
 */

import { ApiClient } from './client';
import type { ApiError } from '@/types/api';

/**
 * Workflow trigger type enum
 */
export enum WorkflowTriggerType {
  Webhook = 'webhook',
  Schedule = 'schedule',
  Manual = 'manual',
}

/**
 * Workflow status enum
 */
export enum WorkflowStatus {
  Draft = 'draft',
  Active = 'active',
  Paused = 'paused',
  Archived = 'archived',
}

/**
 * Execution status enum
 */
export enum ExecutionStatus {
  Pending = 'pending',
  Running = 'running',
  Completed = 'completed',
  Failed = 'failed',
  Cancelled = 'cancelled',
}

/**
 * Action type enum
 */
export enum ActionType {
  // Notification actions
  SendEmail = 'send_email',
  SendWebhook = 'send_webhook',
  SendSlack = 'send_slack',

  // Candidate actions
  AddTag = 'add_tag',
  RemoveTag = 'remove_tag',
  AddNote = 'add_note',
  MoveStage = 'move_stage',
  AssignRecruiter = 'assign_recruiter',

  // Data actions
  UpdateField = 'update_field',
  CreateEntity = 'create_entity',
  DeleteEntity = 'delete_entity',

  // Analytics actions
  TrackEvent = 'track_event',
  GenerateReport = 'generate_report',

  // Custom actions
  ExecuteFunction = 'execute_function',
  RunPlugin = 'run_plugin',
  Log = 'log',
  Conditional = 'conditional',
  Delay = 'delay',
}

/**
 * Trigger configuration
 */
export interface TriggerConfig {
  type: string;
  event?: string;
  cron_expression?: string;
  webhook_url?: string;
}

/**
 * Action configuration
 */
export interface ActionConfig {
  type: string;
  config: Record<string, unknown>;
  label?: string;
}

/**
 * Workflow data (list item)
 */
export interface Workflow {
  id: string;
  name: string;
  description: string | null;
  trigger_type: string;
  status: string;
  is_active: boolean;
  execution_count: number;
  success_rate: number;
  last_executed_at: string | null;
  created_at: string;
}

/**
 * Workflow detail data
 */
export interface WorkflowDetail extends Workflow {
  trigger_config: Record<string, unknown>;
  actions: ActionConfig[];
  version: number;
  api_key_id: string | null;
  success_count: number;
  failure_count: number;
  updated_at: string;
}

/**
 * Workflow execution info
 */
export interface ExecutionInfo {
  id: string;
  workflow_id: string;
  status: string;
  trigger_type: string;
  error_message: string | null;
  duration_seconds: number | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

/**
 * Workflow execution detail
 */
export interface ExecutionDetail extends ExecutionInfo {
  trigger_data: Record<string, unknown> | null;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  action_results: Array<Record<string, unknown>> | null;
  updated_at: string;
}

/**
 * Create workflow request
 */
export interface CreateWorkflowRequest {
  name: string;
  description?: string;
  trigger: TriggerConfig;
  actions: ActionConfig[];
  api_key_id?: string;
}

/**
 * Update workflow request
 */
export interface UpdateWorkflowRequest {
  name?: string;
  description?: string;
  trigger?: TriggerConfig;
  actions?: ActionConfig[];
}

/**
 * Create workflow response
 */
export interface CreateWorkflowResponse {
  id: string;
  name: string;
  description: string | null;
  trigger_type: string;
  trigger_config: Record<string, unknown>;
  actions: ActionConfig[];
  status: string;
  version: number;
  is_active: boolean;
  api_key_id: string | null;
  last_executed_at: string | null;
  execution_count: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  created_at: string;
  updated_at: string;
  message: string;
}

/**
 * Update workflow response
 */
export interface UpdateWorkflowResponse {
  id: string;
  name: string;
  description: string | null;
  trigger_type: string;
  trigger_config: Record<string, unknown>;
  actions: ActionConfig[];
  status: string;
  version: number;
  is_active: boolean;
  api_key_id: string | null;
  last_executed_at: string | null;
  execution_count: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  created_at: string;
  updated_at: string;
  message: string;
}

/**
 * List workflows request filters
 */
export interface ListWorkflowsFilters {
  status?: string;
  is_active?: boolean;
  trigger_type?: string;
  skip?: number;
  limit?: number;
}

/**
 * Workflow statistics
 */
export interface WorkflowStatistics {
  total_workflows: number;
  active_workflows: number;
  paused_workflows: number;
  draft_workflows: number;
  total_executions_today: number;
  successful_executions_today: number;
  failed_executions_today: number;
}

/**
 * Workflows Client
 *
 * Handles workflow automation management operations.
 */
export class WorkflowsClient {
  /**
   * @param apiClient - The API client instance
   */
  constructor(private apiClient: ApiClient) {}

  /**
   * List all workflows with optional filters
   *
   * @param filters - Optional filters for listing workflows
   * @returns List of workflows
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * const workflows = await workflowsClient.listWorkflows({ is_active: true });
   * const activeWorkflows = await workflowsClient.listWorkflows({ status: 'active' });
   * ```
   */
  async listWorkflows(filters?: ListWorkflowsFilters): Promise<Workflow[]> {
    try {
      const params: Record<string, string | number | boolean> = {};
      if (filters) {
        if (filters.status) params.status = filters.status;
        if (filters.is_active !== undefined) params.is_active = filters.is_active;
        if (filters.trigger_type) params.trigger_type = filters.trigger_type;
        params.skip = filters.skip ?? 0;
        params.limit = filters.limit ?? 100;
      }

      const response = await this.apiClient.getAxiosInstance().get<Workflow[]>(
        '/api/workflows/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get detailed information about a specific workflow
   *
   * @param workflowId - Workflow UUID
   * @returns Workflow details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const workflow = await workflowsClient.getWorkflow('workflow-uuid');
   * ```
   */
  async getWorkflow(workflowId: string): Promise<WorkflowDetail> {
    try {
      const response = await this.apiClient.getAxiosInstance().get<WorkflowDetail>(
        `/api/workflows/${workflowId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Create a new workflow
   *
   * @param request - Workflow creation details
   * @returns Created workflow details
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const result = await workflowsClient.createWorkflow({
   *   name: 'Candidate Notification',
   *   trigger: { type: 'webhook', event: 'candidate.created' },
   *   actions: [{ type: 'send_email', config: { to: 'hr@example.com' } }]
   * });
   * ```
   */
  async createWorkflow(request: CreateWorkflowRequest): Promise<CreateWorkflowResponse> {
    try {
      const response = await this.apiClient.post<CreateWorkflowResponse>(
        '/api/workflows/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a workflow
   *
   * @param workflowId - Workflow UUID
   * @param request - Update options
   * @returns Updated workflow details
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const result = await workflowsClient.updateWorkflow('workflow-uuid', {
   *   name: 'Updated Workflow Name'
   * });
   * ```
   */
  async updateWorkflow(
    workflowId: string,
    request: UpdateWorkflowRequest
  ): Promise<UpdateWorkflowResponse> {
    try {
      const response = await this.apiClient.put<UpdateWorkflowResponse>(
        `/api/workflows/${workflowId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a workflow
   *
   * @param workflowId - Workflow UUID
   * @returns Delete confirmation
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await workflowsClient.deleteWorkflow('workflow-uuid');
   * ```
   */
  async deleteWorkflow(workflowId: string): Promise<{ message: string }> {
    try {
      const response = await this.apiClient.delete<{ message: string }>(
        `/api/workflows/${workflowId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Activate a workflow
   *
   * @param workflowId - Workflow UUID
   * @returns Updated workflow details
   * @throws ApiError if activation fails
   *
   * @example
   * ```ts
   * const result = await workflowsClient.activateWorkflow('workflow-uuid');
   * ```
   */
  async activateWorkflow(workflowId: string): Promise<WorkflowDetail> {
    try {
      const response = await this.apiClient.post<WorkflowDetail>(
        `/api/workflows/${workflowId}/activate`,
        {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Pause a workflow
   *
   * @param workflowId - Workflow UUID
   * @returns Updated workflow details
   * @throws ApiError if pause fails
   *
   * @example
   * ```ts
   * const result = await workflowsClient.pauseWorkflow('workflow-uuid');
   * ```
   */
  async pauseWorkflow(workflowId: string): Promise<WorkflowDetail> {
    try {
      const response = await this.apiClient.post<WorkflowDetail>(
        `/api/workflows/${workflowId}/pause`,
        {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get workflow execution history
   *
   * @param workflowId - Workflow UUID
   * @param skip - Number of records to skip (default: 0)
   * @param limit - Maximum number of records to return (default: 50)
   * @returns List of workflow executions
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * const executions = await workflowsClient.getExecutions('workflow-uuid', 0, 20);
   * ```
   */
  async getExecutions(
    workflowId: string,
    skip: number = 0,
    limit: number = 50
  ): Promise<ExecutionInfo[]> {
    try {
      const response = await this.apiClient.getAxiosInstance().get<ExecutionInfo[]>(
        `/api/workflows/${workflowId}/executions`,
        { params: { skip, limit } }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Manually trigger workflow execution
   *
   * @param workflowId - Workflow UUID
   * @param inputData - Optional input data to pass to the workflow
   * @returns Execution details
   * @throws ApiError if execution fails
   *
   * @example
   * ```ts
   * const result = await workflowsClient.executeWorkflow('workflow-uuid', { candidate_id: '123' });
   * ```
   */
  async executeWorkflow(
    workflowId: string,
    inputData?: Record<string, unknown>
  ): Promise<ExecutionDetail> {
    try {
      const response = await this.apiClient.post<ExecutionDetail>(
        `/api/workflows/${workflowId}/execute`,
        { input_data: inputData ?? {} }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get workflow statistics
   *
   * @returns Workflow statistics
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const stats = await workflowsClient.getStatistics();
   * console.log(stats.total_workflows);
   * ```
   */
  async getStatistics(): Promise<WorkflowStatistics> {
    try {
      const response = await this.apiClient.getAxiosInstance().get<WorkflowStatistics>(
        '/api/workflows/statistics'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Transform unknown error to ApiError
   */
  private transformError(error: unknown): ApiError {
    if (error && typeof error === 'object' && 'detail' in error) {
      const apiError = error as { detail: string; status?: number };
      return {
        detail: apiError.detail,
        status: apiError.status || 0,
      };
    }
    return {
      detail: error instanceof Error ? error.message : 'An unknown error occurred',
      status: 0,
    };
  }
}

/**
 * Default workflows client instance
 */
export const workflowsClient = new WorkflowsClient(
  new (require('./client').ApiClient)()
);

/**
 * Export workflows client class
 */
export default WorkflowsClient;
