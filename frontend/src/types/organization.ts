/**
 * Organization-related type definitions
 *
 * This module contains TypeScript interfaces for organization management,
 * branding settings, email templates, and workflow customization features.
 */

// ==================== Organization Types ====================

/**
 * Organization (base interface for frontend usage)
 */
export interface Organization {
  id: string;
  name: string;
  slug: string;
  domain: string | null;
  logo_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Organization create request
 */
export interface OrganizationCreate {
  name: string;
  slug: string;
  domain?: string;
  logo_url?: string;
  is_active?: boolean;
}

/**
 * Organization update request
 */
export interface OrganizationUpdate {
  name?: string;
  slug?: string;
  domain?: string;
  logo_url?: string;
  is_active?: boolean;
}

/**
 * Organization response
 */
export interface OrganizationResponse {
  id: string;
  name: string;
  slug: string;
  domain: string | null;
  logo_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Organization list response
 */
export interface OrganizationListResponse {
  organizations: OrganizationResponse[];
  total_count: number;
}

// ==================== Branding Settings Types ====================

/**
 * Branding settings (base interface for frontend usage)
 */
export interface BrandingSettings {
  id: string;
  organization_id: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  background_color: string | null;
  text_color: string | null;
  font_family: string | null;
  custom_css: string | null;
  logo_url: string | null;
  favicon_url: string | null;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Branding settings create request
 */
export interface BrandingSettingsCreate {
  organization_id: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  background_color?: string;
  text_color?: string;
  font_family?: string;
  custom_css?: string;
  logo_url?: string;
  favicon_url?: string;
  is_active?: boolean;
  created_by?: string;
}

/**
 * Branding settings update request
 */
export interface BrandingSettingsUpdate {
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  background_color?: string;
  text_color?: string;
  font_family?: string;
  custom_css?: string;
  logo_url?: string;
  favicon_url?: string;
  is_active?: boolean;
}

/**
 * Branding settings response
 */
export interface BrandingSettingsResponse {
  id: string;
  organization_id: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  background_color: string | null;
  text_color: string | null;
  font_family: string | null;
  custom_css: string | null;
  logo_url: string | null;
  favicon_url: string | null;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Branding settings list response
 */
export interface BrandingSettingsListResponse {
  branding_settings: BrandingSettingsResponse[];
  total_count: number;
}

// ==================== Email Template Types ====================

/**
 * Email template (base interface for frontend usage)
 */
export interface EmailTemplate {
  id: string;
  organization_id: string;
  template_type: string;
  subject: string;
  body: string;
  variables: Record<string, unknown> | null;
  is_default: boolean;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Email template create request
 */
export interface EmailTemplateCreate {
  organization_id: string;
  template_type: string;
  subject: string;
  body: string;
  variables?: Record<string, unknown>;
  is_default?: boolean;
  is_active?: boolean;
  created_by?: string;
}

/**
 * Email template update request
 */
export interface EmailTemplateUpdate {
  template_type?: string;
  subject?: string;
  body?: string;
  variables?: Record<string, unknown>;
  is_default?: boolean;
  is_active?: boolean;
}

/**
 * Email template response
 */
export interface EmailTemplateResponse {
  id: string;
  organization_id: string;
  template_type: string;
  subject: string;
  body: string;
  variables: Record<string, unknown> | null;
  is_default: boolean;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Email template list response
 */
export interface EmailTemplateListResponse {
  templates: EmailTemplateResponse[];
  total_count: number;
}

/**
 * Email template preview request
 */
export interface EmailTemplatePreviewRequest {
  template_id?: string;
  template_type?: string;
  variables: Record<string, unknown>;
}

/**
 * Email template preview response
 */
export interface EmailTemplatePreviewResponse {
  subject: string;
  body: string;
  html_body: string;
}

// ==================== Workflow Stage Types ====================

/**
 * Workflow stage config (base interface for frontend usage)
 */
export interface WorkflowStageConfig {
  id: string;
  organization_id: string;
  stage_name: string;
  stage_order: number;
  is_default: boolean;
  is_active: boolean;
  color: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Workflow stage config create request
 */
export interface WorkflowStageConfigCreate {
  organization_id: string;
  stage_name: string;
  stage_order: number;
  is_default?: boolean;
  is_active?: boolean;
  color?: string;
  description?: string;
}

/**
 * Workflow stage config update request
 */
export interface WorkflowStageConfigUpdate {
  stage_name?: string;
  stage_order?: number;
  is_default?: boolean;
  is_active?: boolean;
  color?: string;
  description?: string;
}

/**
 * Workflow stage config response
 */
export interface WorkflowStageConfigResponse {
  id: string;
  organization_id: string;
  stage_name: string;
  stage_order: number;
  is_default: boolean;
  is_active: boolean;
  color: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Workflow stage config list response
 */
export interface WorkflowStageConfigListResponse {
  organization_id: string;
  stages: WorkflowStageConfigResponse[];
  total_count: number;
}

/**
 * Reorder workflow stages request
 */
export interface ReorderWorkflowStagesRequest {
  stage_orders: Array<{
    id: string;
    stage_order: number;
  }>;
}

/**
 * Reorder workflow stages response
 */
export interface ReorderWorkflowStagesResponse {
  message: string;
  updated_stages: WorkflowStageConfigResponse[];
}
