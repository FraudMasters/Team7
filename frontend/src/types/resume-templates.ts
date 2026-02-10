/**
 * Resume Template type definitions
 *
 * This module contains TypeScript interfaces for all resume template
 * related operations including layout, style, and section configurations.
 */

/**
 * Configuration for resume template layout
 */
export interface LayoutConfig {
  /** Page margins (e.g., 'normal', 'wide', 'narrow') */
  margins?: string;
  /** List of sections to include in the template */
  sections?: string[];
  /** Spacing configuration for different elements */
  spacing?: Record<string, number>;
  /** Additional layout properties */
  [key: string]: unknown;
}

/**
 * Configuration for resume template styling
 */
export interface StyleConfig {
  /** Primary color for headings and accents (hex code) */
  primary_color?: string;
  /** Secondary color for supporting elements */
  secondary_color?: string;
  /** Main font family */
  font?: string;
  /** Base font size in points */
  font_size?: number;
  /** Font family for headings */
  heading_font?: string;
  /** Additional style properties */
  [key: string]: unknown;
}

/**
 * Configuration for a single section in the resume template
 */
export interface SectionConfigItem {
  /** Whether this section is enabled */
  enabled?: boolean;
  /** Position of the section (e.g., 'top', 'main', 'sidebar') */
  position?: string;
  /** Order of the section within the layout */
  order?: number;
  /** Additional section properties */
  [key: string]: unknown;
}

/**
 * Configuration for resume template sections
 */
export interface SectionConfig {
  /** Configuration for each named section */
  [sectionName: string]: SectionConfigItem;
}

/**
 * Resume template type enum
 */
export type ResumeTemplateType =
  | 'modern'
  | 'classic'
  | 'creative'
  | 'ats_friendly'
  | 'professional'
  | 'minimal'
  | 'elegant'
  | 'bold';

/**
 * Resume template create request
 */
export interface ResumeTemplateCreate {
  /** ID of the organization (null for global templates) */
  organization_id?: string | null;
  /** Template name (e.g., 'Modern Professional', 'Classic') */
  name: string;
  /** Description of the template style */
  description?: string | null;
  /** Type/category of the template */
  template_type: string;
  /** Layout configuration (margins, sections, spacing, etc.) */
  layout_config?: LayoutConfig | null;
  /** Style configuration (colors, fonts, headings, etc.) */
  style_config?: StyleConfig | null;
  /** Section configuration (which sections to include and order) */
  section_config?: SectionConfig | null;
  /** URL to preview image of the template */
  preview_url?: string | null;
  /** Whether this is the default template */
  is_default?: boolean;
  /** Whether this template is active and available */
  is_active?: boolean;
  /** Whether this template is ATS-friendly */
  is_ats_compliant?: boolean;
  /** ID of the user creating the template */
  created_by?: string | null;
}

/**
 * Resume template update request
 */
export interface ResumeTemplateUpdate {
  /** Template name */
  name?: string;
  /** Description of the template style */
  description?: string | null;
  /** Layout configuration */
  layout_config?: LayoutConfig | null;
  /** Style configuration */
  style_config?: StyleConfig | null;
  /** Section configuration */
  section_config?: SectionConfig | null;
  /** URL to preview image */
  preview_url?: string | null;
  /** Whether this is the default template */
  is_default?: boolean;
  /** Whether this template is active */
  is_active?: boolean;
  /** Whether this template is ATS-friendly */
  is_ats_compliant?: boolean;
}

/**
 * Resume template response
 */
export interface ResumeTemplateResponse {
  /** Unique identifier for the template */
  id: string;
  /** ID of the organization (null for global templates) */
  organization_id: string | null;
  /** Template name */
  name: string;
  /** Description of the template style */
  description: string | null;
  /** Type/category of the template */
  template_type: string;
  /** Layout configuration */
  layout_config: LayoutConfig | null;
  /** Style configuration */
  style_config: StyleConfig | null;
  /** Section configuration */
  section_config: SectionConfig | null;
  /** URL to preview image */
  preview_url: string | null;
  /** Whether this is the default template */
  is_default: boolean;
  /** Whether this template is active */
  is_active: boolean;
  /** Whether this template is ATS-friendly */
  is_ats_compliant: boolean;
  /** ID of the user who created the template */
  created_by: string | null;
  /** Creation timestamp (ISO 8601) */
  created_at: string;
  /** Last update timestamp (ISO 8601) */
  updated_at: string;
}

/**
 * Resume template list response
 */
export interface ResumeTemplateListResponse {
  /** List of resume templates */
  templates: ResumeTemplateResponse[];
  /** Total number of templates */
  total_count: number;
}

/**
 * Query parameters for listing resume templates
 */
export interface ResumeTemplateListParams {
  /** Filter by organization ID (null for global templates) */
  organization_id?: string | null;
  /** Filter by template type */
  template_type?: string | null;
  /** Filter by default status */
  is_default?: boolean;
  /** Filter by active status */
  is_active?: boolean;
  /** Filter by ATS compliance */
  is_ats_compliant?: boolean;
  /** Maximum number of results to return */
  limit?: number;
  /** Number of results to skip for pagination */
  offset?: number;
}

/**
 * Resume template delete response
 */
export interface ResumeTemplateDeleteResponse {
  /** Confirmation message */
  message: string;
  /** ID of the deleted template */
  id: string;
}

/**
 * Template preview request
 */
export interface TemplatePreviewRequest {
  /** Template ID to preview */
  template_id: string;
  /** Optional resume data to populate the preview */
  resume_data?: Record<string, unknown>;
}

/**
 * Template preview response
 */
export interface TemplatePreviewResponse {
  /** URL to the preview image */
  preview_url: string;
  /** Template ID */
  template_id: string;
  /** Generated timestamp */
  generated_at: string;
}

/**
 * Template customization options
 */
export interface TemplateCustomizationOptions {
  /** Primary color override */
  primary_color?: string;
  /** Font family override */
  font?: string;
  /** Font size override */
  font_size?: number;
  /** Enable/disable specific sections */
  sections?: {
    [key: string]: boolean;
  };
  /** Section order customization */
  section_order?: string[];
}
