/**
 * Organizations API Client
 *
 * This module provides clients for managing organizations, branding settings,
 * email templates, and workflow stage configurations with proper error handling
 * and type safety.
 *
 * @example
 * ```ts
 * import { organizationsClient } from '@/api/organizations';
 *
 * // List all organizations
 * const orgs = await organizationsClient.listOrganizations();
 *
 * // Create a new organization
 * const newOrg = await organizationsClient.createOrganization({
 *   name: 'Acme Corp',
 *   slug: 'acme-corp',
 *   domain: 'acme.com'
 * });
 *
 * // Update branding settings
 * const branding = await organizationsClient.updateBrandingSettings('branding-id', {
 *   primary_color: '#3B82F6',
 *   secondary_color: '#10B981'
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  OrganizationCreate,
  OrganizationUpdate,
  OrganizationResponse,
  OrganizationListResponse,
  BrandingSettingsCreate,
  BrandingSettingsUpdate,
  BrandingSettingsResponse,
  BrandingSettingsListResponse,
  EmailTemplateCreate,
  EmailTemplateUpdate,
  EmailTemplateResponse,
  EmailTemplateListResponse,
  EmailTemplatePreviewRequest,
  EmailTemplatePreviewResponse,
  WorkflowStageConfigCreate,
  WorkflowStageConfigUpdate,
  WorkflowStageConfigResponse,
  WorkflowStageConfigListResponse,
  ReorderWorkflowStagesRequest,
  ReorderWorkflowStagesResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for organizations client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Organizations API Client class
 *
 * Provides methods for managing organizations, branding settings, email templates,
 * and workflow stage configurations with proper error handling and type safety.
 */
export class OrganizationsClient {
  private client: AxiosInstance;

  /**
   * Create a new Organizations client instance
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

  // ==================== Organizations ====================

  /**
   * Create an organization
   *
   * @param request - Create request with organization details
   * @returns Created organization
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const org = await organizationsClient.createOrganization({
   *   name: 'Acme Corp',
   *   slug: 'acme-corp',
   *   domain: 'acme.com',
   *   logo_url: 'https://acme.com/logo.png'
   * });
   * ```
   */
  async createOrganization(request: OrganizationCreate): Promise<OrganizationResponse> {
    try {
      const response: AxiosResponse<OrganizationResponse> = await this.client.post(
        '/api/organizations/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List organizations with optional filters
   *
   * @param isActive - Optional active status filter
   * @param skip - Number of records to skip (pagination)
   * @param limit - Maximum number of records to return
   * @returns List of organizations
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all organizations
   * const orgs = await organizationsClient.listOrganizations();
   *
   * // Get only active organizations
   * const activeOrgs = await organizationsClient.listOrganizations(true);
   * ```
   */
  async listOrganizations(
    isActive?: boolean,
    skip: number = 0,
    limit: number = 100
  ): Promise<OrganizationListResponse> {
    try {
      const params: Record<string, boolean | number> = { skip, limit };
      if (isActive !== undefined) params.is_active = isActive;

      const response: AxiosResponse<OrganizationListResponse> = await this.client.get(
        '/api/organizations/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific organization by ID
   *
   * @param organizationId - Organization ID
   * @returns Organization details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const org = await organizationsClient.getOrganization('org-uuid');
   * ```
   */
  async getOrganization(organizationId: string): Promise<OrganizationResponse> {
    try {
      const response: AxiosResponse<OrganizationResponse> = await this.client.get(
        `/api/organizations/${organizationId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update an organization
   *
   * @param organizationId - Organization ID
   * @param request - Update request with fields to modify
   * @returns Updated organization
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await organizationsClient.updateOrganization('org-uuid', {
   *   name: 'Updated Organization Name',
   *   logo_url: 'https://example.com/new-logo.png'
   * });
   * ```
   */
  async updateOrganization(
    organizationId: string,
    request: OrganizationUpdate
  ): Promise<OrganizationResponse> {
    try {
      const response: AxiosResponse<OrganizationResponse> = await this.client.put(
        `/api/organizations/${organizationId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete an organization
   *
   * @param organizationId - Organization ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await organizationsClient.deleteOrganization('org-uuid');
   * ```
   */
  async deleteOrganization(organizationId: string): Promise<void> {
    try {
      await this.client.delete(`/api/organizations/${organizationId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Branding Settings ====================

  /**
   * Create branding settings for an organization
   *
   * @param request - Create request with branding details
   * @returns Created branding settings
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const branding = await organizationsClient.createBrandingSettings({
   *   organization_id: 'org-123',
   *   primary_color: '#3B82F6',
   *   secondary_color: '#10B981',
   *   accent_color: '#F59E0B'
   * });
   * ```
   */
  async createBrandingSettings(request: BrandingSettingsCreate): Promise<BrandingSettingsResponse> {
    try {
      const response: AxiosResponse<BrandingSettingsResponse> = await this.client.post(
        '/api/branding/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List branding settings with optional filters
   *
   * @param organizationId - Optional organization ID filter
   * @param isActive - Optional active status filter
   * @returns List of branding settings
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all branding settings
   * const settings = await organizationsClient.listBrandingSettings();
   *
   * // Get settings for a specific organization
   * const orgSettings = await organizationsClient.listBrandingSettings('org-123');
   * ```
   */
  async listBrandingSettings(
    organizationId?: string,
    isActive?: boolean
  ): Promise<BrandingSettingsListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (isActive !== undefined) params.is_active = isActive;

      const response: AxiosResponse<BrandingSettingsListResponse> = await this.client.get(
        '/api/branding/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific branding settings by ID
   *
   * @param brandingId - Branding settings ID
   * @returns Branding settings details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const branding = await organizationsClient.getBrandingSettings('branding-uuid');
   * ```
   */
  async getBrandingSettings(brandingId: string): Promise<BrandingSettingsResponse> {
    try {
      const response: AxiosResponse<BrandingSettingsResponse> = await this.client.get(
        `/api/branding/${brandingId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update branding settings
   *
   * @param brandingId - Branding settings ID
   * @param request - Update request with fields to modify
   * @returns Updated branding settings
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await organizationsClient.updateBrandingSettings('branding-uuid', {
   *   primary_color: '#EF4444',
   *   logo_url: 'https://example.com/new-logo.png'
   * });
   * ```
   */
  async updateBrandingSettings(
    brandingId: string,
    request: BrandingSettingsUpdate
  ): Promise<BrandingSettingsResponse> {
    try {
      const response: AxiosResponse<BrandingSettingsResponse> = await this.client.put(
        `/api/branding/${brandingId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete branding settings
   *
   * @param brandingId - Branding settings ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await organizationsClient.deleteBrandingSettings('branding-uuid');
   * ```
   */
  async deleteBrandingSettings(brandingId: string): Promise<void> {
    try {
      await this.client.delete(`/api/branding/${brandingId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Email Templates ====================

  /**
   * Create an email template
   *
   * @param request - Create request with email template details
   * @returns Created email template
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const template = await organizationsClient.createEmailTemplate({
   *   organization_id: 'org-123',
   *   template_type: 'candidate_feedback',
   *   subject: 'Feedback for {{candidate_name}}',
   *   body: 'Dear {{recruiter_name}}, your feedback is ready.'
   * });
   * ```
   */
  async createEmailTemplate(request: EmailTemplateCreate): Promise<EmailTemplateResponse> {
    try {
      const response: AxiosResponse<EmailTemplateResponse> = await this.client.post(
        '/api/email-templates/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List email templates with optional filters
   *
   * @param organizationId - Optional organization ID filter
   * @param templateType - Optional template type filter
   * @param isDefault - Optional default status filter
   * @param isActive - Optional active status filter
   * @returns List of email templates
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all email templates for an organization
   * const templates = await organizationsClient.listEmailTemplates('org-123');
   *
   * // Get only feedback templates
   * const feedbackTemplates = await organizationsClient.listEmailTemplates(
   *   'org-123',
   *   'candidate_feedback'
   * );
   * ```
   */
  async listEmailTemplates(
    organizationId?: string,
    templateType?: string,
    isDefault?: boolean,
    isActive?: boolean
  ): Promise<EmailTemplateListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (templateType) params.template_type = templateType;
      if (isDefault !== undefined) params.is_default = isDefault;
      if (isActive !== undefined) params.is_active = isActive;

      const response: AxiosResponse<EmailTemplateListResponse> = await this.client.get(
        '/api/email-templates/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific email template by ID
   *
   * @param templateId - Email template ID
   * @returns Email template details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const template = await organizationsClient.getEmailTemplate('template-uuid');
   * ```
   */
  async getEmailTemplate(templateId: string): Promise<EmailTemplateResponse> {
    try {
      const response: AxiosResponse<EmailTemplateResponse> = await this.client.get(
        `/api/email-templates/${templateId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update an email template
   *
   * @param templateId - Email template ID
   * @param request - Update request with fields to modify
   * @returns Updated email template
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await organizationsClient.updateEmailTemplate('template-uuid', {
   *   subject: 'Updated Subject',
   *   body: 'Updated body content'
   * });
   * ```
   */
  async updateEmailTemplate(
    templateId: string,
    request: EmailTemplateUpdate
  ): Promise<EmailTemplateResponse> {
    try {
      const response: AxiosResponse<EmailTemplateResponse> = await this.client.put(
        `/api/email-templates/${templateId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete an email template
   *
   * @param templateId - Email template ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await organizationsClient.deleteEmailTemplate('template-uuid');
   * ```
   */
  async deleteEmailTemplate(templateId: string): Promise<void> {
    try {
      await this.client.delete(`/api/email-templates/${templateId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Preview an email template with variable substitution
   *
   * @param request - Preview request with template ID or type and variables
   * @returns Preview with subject and rendered body
   * @throws ApiError if preview fails
   *
   * @example
   * ```ts
   * const preview = await organizationsClient.previewEmailTemplate({
   *   template_id: 'template-uuid',
   *   variables: {
   *     candidate_name: 'John Doe',
   *     recruiter_name: 'Jane Smith'
   *   }
   * });
   * ```
   */
  async previewEmailTemplate(request: EmailTemplatePreviewRequest): Promise<EmailTemplatePreviewResponse> {
    try {
      const response: AxiosResponse<EmailTemplatePreviewResponse> = await this.client.post(
        '/api/email-templates/preview',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Workflow Stage Configurations ====================

  /**
   * Create a workflow stage configuration
   *
   * @param request - Create request with workflow stage details
   * @returns Created workflow stage configuration
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const stage = await organizationsClient.createWorkflowStageConfig({
   *   organization_id: 'org-123',
   *   stage_name: 'Technical Interview',
   *   stage_order: 3,
   *   color: '#3B82F6'
   * });
   * ```
   */
  async createWorkflowStageConfig(request: WorkflowStageConfigCreate): Promise<WorkflowStageConfigResponse> {
    try {
      const response: AxiosResponse<WorkflowStageConfigResponse> = await this.client.post(
        '/api/workflow-stage-configs/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List workflow stage configurations with optional filters
   *
   * @param organizationId - Optional organization ID filter
   * @param isActive - Optional active status filter
   * @param isDefault - Optional default status filter
   * @returns List of workflow stage configurations
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all stages for an organization
   * const stages = await organizationsClient.listWorkflowStageConfigs('org-123');
   *
   * // Get only active stages
   * const activeStages = await organizationsClient.listWorkflowStageConfigs('org-123', true);
   * ```
   */
  async listWorkflowStageConfigs(
    organizationId?: string,
    isActive?: boolean,
    isDefault?: boolean
  ): Promise<WorkflowStageConfigListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (isActive !== undefined) params.is_active = isActive;
      if (isDefault !== undefined) params.is_default = isDefault;

      const response: AxiosResponse<WorkflowStageConfigListResponse> = await this.client.get(
        '/api/workflow-stage-configs/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific workflow stage configuration by ID
   *
   * @param stageId - Workflow stage configuration ID
   * @returns Workflow stage configuration details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const stage = await organizationsClient.getWorkflowStageConfig('stage-uuid');
   * ```
   */
  async getWorkflowStageConfig(stageId: string): Promise<WorkflowStageConfigResponse> {
    try {
      const response: AxiosResponse<WorkflowStageConfigResponse> = await this.client.get(
        `/api/workflow-stage-configs/${stageId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a workflow stage configuration
   *
   * @param stageId - Workflow stage configuration ID
   * @param request - Update request with fields to modify
   * @returns Updated workflow stage configuration
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await organizationsClient.updateWorkflowStageConfig('stage-uuid', {
   *   stage_name: 'Updated Technical Interview',
   *   color: '#10B981'
   * });
   * ```
   */
  async updateWorkflowStageConfig(
    stageId: string,
    request: WorkflowStageConfigUpdate
  ): Promise<WorkflowStageConfigResponse> {
    try {
      const response: AxiosResponse<WorkflowStageConfigResponse> = await this.client.put(
        `/api/workflow-stage-configs/${stageId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a workflow stage configuration
   *
   * @param stageId - Workflow stage configuration ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await organizationsClient.deleteWorkflowStageConfig('stage-uuid');
   * ```
   */
  async deleteWorkflowStageConfig(stageId: string): Promise<void> {
    try {
      await this.client.delete(`/api/workflow-stage-configs/${stageId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Reorder workflow stage configurations
   *
   * @param request - Reorder request with stage IDs and their new orders
   * @returns Updated workflow stage configurations
   * @throws ApiError if reordering fails
   *
   * @example
   * ```ts
   * const result = await organizationsClient.reorderWorkflowStages({
   *   stage_orders: [
   *     { id: 'stage-1', stage_order: 1 },
   *     { id: 'stage-2', stage_order: 2 },
   *     { id: 'stage-3', stage_order: 3 }
   *   ]
   * });
   * ```
   */
  async reorderWorkflowStages(request: ReorderWorkflowStagesRequest): Promise<ReorderWorkflowStagesResponse> {
    try {
      const response: AxiosResponse<ReorderWorkflowStagesResponse> = await this.client.post(
        '/api/workflow-stage-configs/reorder',
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
 * Default organizations client instance
 *
 * Use this singleton instance for all organizations API calls.
 */
export const organizationsClient = new OrganizationsClient();

/**
 * Export organizations client class for custom instances
 */
export default OrganizationsClient;
