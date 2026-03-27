/**
 * Notification Templates API Client
 *
 * This module provides a client for managing notification templates,
 * including creating, reading, updating, and deleting
 * template configurations for email and SMS notifications with support
 * for dynamic variables, conditional blocks, and preview capabilities.
 *
 * @example
 * ```ts
 * import { notificationTemplatesClient } from '@/api/notificationTemplates';
 *
 * // List all notification templates
 * const templates = await notificationTemplatesClient.listTemplates();
 *
 * // Create a new email template
 * const newTemplate = await notificationTemplatesClient.createTemplate({
 *   name: 'Interview Invitation',
 *   type: 'email',
 *   category: 'interview',
 *   pipeline_stage: 'interview_scheduled',
 *   subject: 'Interview Invitation - {{job_title}}',
 *   body: 'Dear {{candidate_name}}, we would like to invite you...',
 *   variables: ['candidate_name', 'job_title', 'interview_date'],
 *   is_active: true,
 *   language: 'en'
 * });
 *
 * // Preview a template with variables
 * const preview = await notificationTemplatesClient.previewTemplate({
 *   template_id: 'template-id',
 *   template_type: 'email',
 *   variables: {
 *     candidate_name: 'John Doe',
 *     job_title: 'Senior Developer',
 *     interview_date: '2026-03-25'
 *   }
 * });
 *
 * // Update a template
 * const updated = await notificationTemplatesClient.updateTemplate('template-id', {
 *   name: 'Updated Template Name',
 *   is_active: false
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  NotificationTemplateType,
  NotificationTemplateCategory,
  PipelineStage,
  TemplateBlock,
  TemplateVariableContext,
} from '@/types/templates';

/**
 * Template create request
 */
export interface NotificationTemplateCreate {
  name: string;
  type: NotificationTemplateType;
  category?: NotificationTemplateCategory;
  pipeline_stage?: PipelineStage;
  subject?: string;
  body: string;
  variables?: string[];
  template_blocks?: TemplateBlock[];
  description?: string;
  is_active?: boolean;
  language?: string;
}

/**
 * Template update request
 */
export interface NotificationTemplateUpdate {
  name?: string;
  type?: NotificationTemplateType;
  category?: NotificationTemplateCategory;
  pipeline_stage?: PipelineStage;
  subject?: string;
  body?: string;
  variables?: string[];
  template_blocks?: TemplateBlock[];
  description?: string;
  is_active?: boolean;
  language?: string;
}

/**
 * Template response
 */
export interface NotificationTemplateResponse {
  id: string;
  name: string;
  type: NotificationTemplateType;
  category: NotificationTemplateCategory | null;
  pipeline_stage: PipelineStage | null;
  subject: string | null;
  body: string;
  variables: string[];
  template_blocks: TemplateBlock[] | null;
  description: string | null;
  is_active: boolean;
  language: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  usage_count?: number;
}

/**
 * Template list response
 */
export interface NotificationTemplateListResponse {
  total: number;
  templates: NotificationTemplateResponse[];
}

/**
 * Template list filters
 */
export interface NotificationTemplateListFilters {
  type?: NotificationTemplateType;
  category?: NotificationTemplateCategory;
  pipeline_stage?: PipelineStage;
  is_active?: boolean;
  language?: string;
  limit?: number;
  offset?: number;
}

/**
 * Template preview request
 */
export interface TemplatePreviewRequest {
  template_id: string;
  template_type: NotificationTemplateType;
  variables: TemplateVariableContext;
}

/**
 * Template preview response
 */
export interface TemplatePreviewResponse {
  subject?: string;
  body: string;
  active_blocks?: TemplateBlock[];
  rendered_at: string;
}

/**
 * API error response
 */
export interface ApiError {
  detail: string;
  status?: number;
}

/**
 * Default API configuration for notification templates client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Notification Templates API Client class
 *
 * Provides methods for managing notification template configurations with proper
 * error handling and type safety.
 */
export class NotificationTemplatesClient {
  private client: AxiosInstance;

  /**
   * Create a new NotificationTemplates client instance
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
      404: 'Template not found.',
      409: 'Template with this name already exists.',
      422: 'Validation error. Please check your input.',
      500: 'Server error. Please try again later.',
      502: 'Bad gateway. Service temporarily unavailable.',
      503: 'Service unavailable. Please try again later.',
    };

    return {
      detail: defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * List all notification templates with optional filters
   *
   * @param filters - Optional filters for templates
   * @returns Promise resolving to template list response
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * // List all templates
   * const all = await client.listTemplates();
   *
   * // Filter by type and category
   * const emailTemplates = await client.listTemplates({
   *   type: 'email',
   *   category: 'interview',
   *   is_active: true
   * });
   *
   * // Paginated results
   * const page = await client.listTemplates({
   *   limit: 10,
   *   offset: 20
   * });
   * ```
   */
  async listTemplates(
    filters?: NotificationTemplateListFilters
  ): Promise<NotificationTemplateListResponse> {
    const response: AxiosResponse<NotificationTemplateListResponse> = await this.client.get(
      '/api/templates',
      { params: filters }
    );
    return response.data;
  }

  /**
   * Get a single notification template by ID
   *
   * @param id - Template ID
   * @returns Promise resolving to template response
   * @throws ApiError if template not found or request fails
   *
   * @example
   * ```ts
   * const template = await client.getTemplate('template-id-123');
   * console.log(template.name, template.body);
   * ```
   */
  async getTemplate(id: string): Promise<NotificationTemplateResponse> {
    const response: AxiosResponse<NotificationTemplateResponse> = await this.client.get(
      `/api/templates/${id}`
    );
    return response.data;
  }

  /**
   * Create a new notification template
   *
   * @param template - Template create request
   * @returns Promise resolving to created template
   * @throws ApiError if validation fails or template already exists
   *
   * @example
   * ```ts
   * const newTemplate = await client.createTemplate({
   *   name: 'Rejection Email',
   *   type: 'email',
   *   category: 'rejection',
   *   pipeline_stage: 'rejected',
   *   subject: 'Application Status Update',
   *   body: 'Dear {{candidate_name}}, thank you for your interest...',
   *   variables: ['candidate_name', 'job_title'],
   *   is_active: true,
   *   language: 'en'
   * });
   * ```
   */
  async createTemplate(
    template: NotificationTemplateCreate
  ): Promise<NotificationTemplateResponse> {
    const response: AxiosResponse<NotificationTemplateResponse> = await this.client.post(
      '/api/templates',
      template
    );
    return response.data;
  }

  /**
   * Update an existing notification template
   *
   * @param id - Template ID
   * @param updates - Partial template update request
   * @returns Promise resolving to updated template
   * @throws ApiError if template not found or validation fails
   *
   * @example
   * ```ts
   * const updated = await client.updateTemplate('template-id-123', {
   *   name: 'Updated Template Name',
   *   is_active: false
   * });
   * ```
   */
  async updateTemplate(
    id: string,
    updates: NotificationTemplateUpdate
  ): Promise<NotificationTemplateResponse> {
    const response: AxiosResponse<NotificationTemplateResponse> = await this.client.put(
      `/api/templates/${id}`,
      updates
    );
    return response.data;
  }

  /**
   * Delete a notification template
   *
   * @param id - Template ID
   * @param hard - Whether to permanently delete (hard delete) or soft delete
   * @returns Promise resolving when template is deleted
   * @throws ApiError if template not found or deletion fails
   *
   * @example
   * ```ts
   * // Soft delete (mark as inactive)
   * await client.deleteTemplate('template-id-123');
   *
   * // Hard delete (permanently remove)
   * await client.deleteTemplate('template-id-123', true);
   * ```
   */
  async deleteTemplate(id: string, hard: boolean = false): Promise<void> {
    await this.client.delete(`/api/templates/${id}`, {
      params: { hard },
    });
  }

  /**
   * Preview a template with variable substitution
   *
   * Renders the template with provided variable values and evaluates
   * conditional blocks based on the variable context.
   *
   * @param request - Template preview request
   * @returns Promise resolving to preview response
   * @throws ApiError if template not found or preview fails
   *
   * @example
   * ```ts
   * const preview = await client.previewTemplate({
   *   template_id: 'template-id-123',
   *   template_type: 'email',
   *   variables: {
   *     candidate_name: 'Jane Smith',
   *     job_title: 'Senior Developer',
   *     interview_date: '2026-03-25',
   *     pipeline_stage: 'interview_scheduled'
   *   }
   * });
   *
   * console.log('Subject:', preview.subject);
   * console.log('Body:', preview.body);
   * console.log('Active blocks:', preview.active_blocks);
   * ```
   */
  async previewTemplate(request: TemplatePreviewRequest): Promise<TemplatePreviewResponse> {
    const response: AxiosResponse<TemplatePreviewResponse> = await this.client.post(
      '/api/templates/preview',
      request
    );
    return response.data;
  }
}

/**
 * Default notification templates client instance
 *
 * Pre-configured client using environment variables.
 * Use this for most cases unless you need custom configuration.
 *
 * @example
 * ```ts
 * import { notificationTemplatesClient } from '@/api/notificationTemplates';
 *
 * const templates = await notificationTemplatesClient.listTemplates();
 * ```
 */
export const notificationTemplatesClient = new NotificationTemplatesClient();

/**
 * Export default instance for convenience
 */
export default notificationTemplatesClient;

/**
 * Re-export template types for convenience
 */
export type {
  NotificationTemplateType,
  NotificationTemplateCategory,
  PipelineStage,
  TemplateBlock,
  TemplateBlockType,
  TemplateCondition,
  TemplateVariable,
  TemplateVariableValue,
  TemplateVariableContext,
  ConditionalOperator,
  ConditionalBlock,
  TextBlock,
  HeadingBlock,
  ButtonBlock,
  BaseTemplateBlock,
  TemplateValidationError,
  TemplateValidationResult,
} from '@/types/templates';
