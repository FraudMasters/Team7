/**
 * Communication Templates API Client
 *
 * This module provides a client for managing communication templates,
 * including creating, reading, updating, and deleting
 * template configurations for candidate communications.
 *
 * @example
 * ```ts
 * import { communicationTemplatesClient } from '@/api/communicationTemplates';
 *
 * // List all communication templates
 * const templates = await communicationTemplatesClient.listTemplates();
 *
 * // Create a new template
 * const newTemplate = await communicationTemplatesClient.createTemplate({
 *   name: 'Interview Invitation',
 *   type: 'email',
 *   subject: 'Interview Invitation - {{job_title}}',
 *   body: 'Dear {{candidate_name}}, we would like to invite you...'
 * });
 *
 * // Preview a template with variables
 * const preview = await communicationTemplatesClient.previewTemplate('template-id', {
 *   candidate_name: 'John Doe',
 *   job_title: 'Senior Developer'
 * });
 *
 * // Update a template
 * const updated = await communicationTemplatesClient.updateTemplate('template-id', {
 *   name: 'Updated Template Name'
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';

/**
 * Communication template type enum
 */
export type TemplateType = 'email' | 'sms' | 'in_system';

/**
 * Template category enum
 */
export type TemplateCategory = 'outreach' | 'interview' | 'rejection' | 'offer' | 'follow_up' | 'other';

/**
 * Template create request
 */
export interface CommunicationTemplateCreate {
  name: string;
  type: TemplateType;
  category?: TemplateCategory;
  subject?: string;
  body: string;
  variables?: string[];
  description?: string;
  is_active?: boolean;
}

/**
 * Template update request
 */
export interface CommunicationTemplateUpdate {
  name?: string;
  type?: TemplateType;
  category?: TemplateCategory;
  subject?: string;
  body?: string;
  variables?: string[];
  description?: string;
  is_active?: boolean;
}

/**
 * Template response
 */
export interface CommunicationTemplateResponse {
  id: string;
  name: string;
  type: TemplateType;
  category: TemplateCategory | null;
  subject: string | null;
  body: string;
  variables: string[];
  description: string | null;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  usage_count?: number;
}

/**
 * Template list response
 */
export interface CommunicationTemplateListResponse {
  total: number;
  templates: CommunicationTemplateResponse[];
}

/**
 * Template preview request
 */
export interface TemplatePreviewRequest {
  variables: Record<string, string | number | boolean>;
}

/**
 * Template preview response
 */
export interface TemplatePreviewResponse {
  subject?: string;
  body: string;
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
 * Default API configuration for communication templates client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Communication Templates API Client class
 *
 * Provides methods for managing communication template configurations with proper
 * error handling and type safety.
 */
export class CommunicationTemplatesClient {
  private client: AxiosInstance;

  /**
   * Create a new CommunicationTemplates client instance
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
      409: 'A template with this name already exists.',
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
   * Create a communication template
   *
   * @param request - Create request with template details
   * @returns Created template
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const template = await communicationTemplatesClient.createTemplate({
   *   name: 'Interview Invitation',
   *   type: 'email',
   *   subject: 'Interview Invitation - {{job_title}}',
   *   body: 'Dear {{candidate_name}}, we would like to invite you...',
   *   variables: ['candidate_name', 'job_title', 'interview_date']
   * });
   * ```
   */
  async createTemplate(request: CommunicationTemplateCreate): Promise<CommunicationTemplateResponse> {
    try {
      const response: AxiosResponse<CommunicationTemplateResponse> = await this.client.post(
        '/api/communications/templates/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List communication templates with optional filters
   *
   * @param skip - Number of records to skip (pagination)
   * @param limit - Maximum number of records to return
   * @param type - Optional filter by template type
   * @param category - Optional filter by template category
   * @param search - Optional filter by name (case-insensitive partial match)
   * @param isActive - Optional filter by active status
   * @returns List of communication templates
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all templates
   * const templates = await communicationTemplatesClient.listTemplates();
   *
   * // Get only email templates
   * const emailTemplates = await communicationTemplatesClient.listTemplates(0, 100, 'email');
   *
   * // Search by name
   * const interviewTemplates = await communicationTemplatesClient.listTemplates(
   *   0,
   *   100,
   *   undefined,
   *   undefined,
   *   'interview'
   * );
   * ```
   */
  async listTemplates(
    skip: number = 0,
    limit: number = 100,
    type?: TemplateType,
    category?: TemplateCategory,
    search?: string,
    isActive?: boolean
  ): Promise<CommunicationTemplateListResponse> {
    try {
      const params: Record<string, number | string | boolean> = { skip, limit };
      if (type) params.type = type;
      if (category) params.category = category;
      if (search) params.search = search;
      if (isActive !== undefined) params.is_active = isActive;

      const response: AxiosResponse<CommunicationTemplateListResponse> = await this.client.get(
        '/api/communications/templates/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific template by ID
   *
   * @param templateId - Template ID
   * @returns Template details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const template = await communicationTemplatesClient.getTemplate('template-uuid');
   * ```
   */
  async getTemplate(templateId: string): Promise<CommunicationTemplateResponse> {
    try {
      const response: AxiosResponse<CommunicationTemplateResponse> = await this.client.get(
        `/api/communications/templates/${templateId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a template
   *
   * @param templateId - Template ID
   * @param request - Update request with fields to modify
   * @returns Updated template
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await communicationTemplatesClient.updateTemplate('template-uuid', {
   *   name: 'Updated Template Name',
   *   subject: 'New Subject Line'
   * });
   * ```
   */
  async updateTemplate(
    templateId: string,
    request: CommunicationTemplateUpdate
  ): Promise<CommunicationTemplateResponse> {
    try {
      const response: AxiosResponse<CommunicationTemplateResponse> = await this.client.put(
        `/api/communications/templates/${templateId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a template
   *
   * @param templateId - Template ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await communicationTemplatesClient.deleteTemplate('template-uuid');
   * ```
   */
  async deleteTemplate(templateId: string): Promise<void> {
    try {
      await this.client.delete(`/api/communications/templates/${templateId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Preview a template with variable substitution
   *
   * @param templateId - Template ID
   * @param request - Preview request with variable values
   * @returns Preview with rendered template
   * @throws ApiError if preview fails
   *
   * @example
   * ```ts
   * const preview = await communicationTemplatesClient.previewTemplate('template-uuid', {
   *   variables: {
   *     candidate_name: 'John Doe',
   *     job_title: 'Senior Developer',
   *     interview_date: '2024-02-15'
   *   }
   * });
   * ```
   */
  async previewTemplate(
    templateId: string,
    request: TemplatePreviewRequest
  ): Promise<TemplatePreviewResponse> {
    try {
      const response: AxiosResponse<TemplatePreviewResponse> = await this.client.post(
        `/api/communications/templates/${templateId}/preview`,
        request
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
 * Default communication templates client instance
 *
 * Use this singleton instance for all communication templates calls.
 */
export const communicationTemplatesClient = new CommunicationTemplatesClient();

/**
 * Export communication templates client class for custom instances
 */
export default CommunicationTemplatesClient;
