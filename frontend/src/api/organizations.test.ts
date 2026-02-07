/**
 * Tests for Organizations API Client
 *
 * Tests the Axios-based API client for organizations, branding settings,
 * email templates, and workflow stage configurations.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { OrganizationsClient } from './organizations';
import axios from 'axios';
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
} from '@/types/api';

// Mock Axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: {
          use: vi.fn(),
        },
        response: {
          use: vi.fn(),
        },
      },
      post: vi.fn(),
      get: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    })),
  },
}));

describe('OrganizationsClient', () => {
  let client: OrganizationsClient;
  let mockAxiosInstance: any;

  beforeEach(() => {
    // Create mock axios instance
    mockAxiosInstance = {
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
      post: vi.fn(),
      get: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    };

    // Mock axios.create to return our mock instance
    vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as any);

    // Create client with mock
    client = new OrganizationsClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const testClient = new OrganizationsClient();
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: expect.any(String),
          timeout: 10000,
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
    });

    it('should create client with custom config', () => {
      const testClient = new OrganizationsClient({
        baseURL: 'http://custom.com',
        timeout: 30000,
      });

      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: 'http://custom.com',
          timeout: 30000,
        })
      );
    });

    it('should set up response interceptor', () => {
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  describe('Organizations', () => {
    const mockOrganization: OrganizationResponse = {
      id: 'org-123',
      name: 'Test Organization',
      slug: 'test-org',
      domain: 'test.com',
      logo_url: 'https://test.com/logo.png',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('should create an organization', async () => {
      const createRequest: OrganizationCreate = {
        name: 'Test Organization',
        slug: 'test-org',
        domain: 'test.com',
        logo_url: 'https://test.com/logo.png',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockOrganization });

      const result = await client.createOrganization(createRequest);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/organizations/',
        createRequest
      );
      expect(result).toEqual(mockOrganization);
    });

    it('should list organizations', async () => {
      const mockResponse: OrganizationListResponse = {
        organizations: [mockOrganization],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listOrganizations(true, 0, 100);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/organizations/', {
        params: { skip: 0, limit: 100, is_active: true },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should get an organization by ID', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockOrganization });

      const result = await client.getOrganization('org-123');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/organizations/org-123'
      );
      expect(result).toEqual(mockOrganization);
    });

    it('should update an organization', async () => {
      const updateRequest: OrganizationUpdate = {
        name: 'Updated Organization',
      };

      const updatedOrg = { ...mockOrganization, name: 'Updated Organization' };
      mockAxiosInstance.put.mockResolvedValue({ data: updatedOrg });

      const result = await client.updateOrganization('org-123', updateRequest);

      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/api/organizations/org-123',
        updateRequest
      );
      expect(result).toEqual(updatedOrg);
    });

    it('should delete an organization', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await client.deleteOrganization('org-123');

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/organizations/org-123'
      );
    });
  });

  describe('Branding Settings', () => {
    const mockBranding: BrandingSettingsResponse = {
      id: 'branding-123',
      organization_id: 'org-123',
      primary_color: '#3B82F6',
      secondary_color: '#10B981',
      accent_color: '#F59E0B',
      background_color: '#FFFFFF',
      text_color: '#000000',
      font_family: 'Inter',
      custom_css: null,
      logo_url: 'https://test.com/logo.png',
      favicon_url: null,
      is_active: true,
      created_by: 'user-123',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('should create branding settings', async () => {
      const createRequest: BrandingSettingsCreate = {
        organization_id: 'org-123',
        primary_color: '#3B82F6',
        secondary_color: '#10B981',
        accent_color: '#F59E0B',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockBranding });

      const result = await client.createBrandingSettings(createRequest);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/branding/',
        createRequest
      );
      expect(result).toEqual(mockBranding);
    });

    it('should list branding settings', async () => {
      const mockResponse: BrandingSettingsListResponse = {
        branding_settings: [mockBranding],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listBrandingSettings('org-123', true);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/branding/', {
        params: { organization_id: 'org-123', is_active: true },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should get branding settings by ID', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockBranding });

      const result = await client.getBrandingSettings('branding-123');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/branding/branding-123'
      );
      expect(result).toEqual(mockBranding);
    });

    it('should update branding settings', async () => {
      const updateRequest: BrandingSettingsUpdate = {
        primary_color: '#EF4444',
      };

      const updatedBranding = { ...mockBranding, primary_color: '#EF4444' };
      mockAxiosInstance.put.mockResolvedValue({ data: updatedBranding });

      const result = await client.updateBrandingSettings(
        'branding-123',
        updateRequest
      );

      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/api/branding/branding-123',
        updateRequest
      );
      expect(result).toEqual(updatedBranding);
    });

    it('should delete branding settings', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await client.deleteBrandingSettings('branding-123');

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/branding/branding-123'
      );
    });
  });

  describe('Email Templates', () => {
    const mockTemplate: EmailTemplateResponse = {
      id: 'template-123',
      organization_id: 'org-123',
      template_type: 'candidate_feedback',
      subject: 'Feedback for {{candidate_name}}',
      body: 'Dear {{recruiter_name}}, feedback is ready.',
      variables: { candidate_name: 'John', recruiter_name: 'Jane' },
      is_default: false,
      is_active: true,
      created_by: 'user-123',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('should create an email template', async () => {
      const createRequest: EmailTemplateCreate = {
        organization_id: 'org-123',
        template_type: 'candidate_feedback',
        subject: 'Feedback for {{candidate_name}}',
        body: 'Dear {{recruiter_name}}, feedback is ready.',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockTemplate });

      const result = await client.createEmailTemplate(createRequest);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/email-templates/',
        createRequest
      );
      expect(result).toEqual(mockTemplate);
    });

    it('should list email templates', async () => {
      const mockResponse: EmailTemplateListResponse = {
        templates: [mockTemplate],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listEmailTemplates(
        'org-123',
        'candidate_feedback',
        false,
        true
      );

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/email-templates/', {
        params: {
          organization_id: 'org-123',
          template_type: 'candidate_feedback',
          is_default: false,
          is_active: true,
        },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should get an email template by ID', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockTemplate });

      const result = await client.getEmailTemplate('template-123');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/email-templates/template-123'
      );
      expect(result).toEqual(mockTemplate);
    });

    it('should update an email template', async () => {
      const updateRequest: EmailTemplateUpdate = {
        subject: 'Updated Subject',
      };

      const updatedTemplate = { ...mockTemplate, subject: 'Updated Subject' };
      mockAxiosInstance.put.mockResolvedValue({ data: updatedTemplate });

      const result = await client.updateEmailTemplate(
        'template-123',
        updateRequest
      );

      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/api/email-templates/template-123',
        updateRequest
      );
      expect(result).toEqual(updatedTemplate);
    });

    it('should delete an email template', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await client.deleteEmailTemplate('template-123');

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/email-templates/template-123'
      );
    });

    it('should preview an email template', async () => {
      const previewRequest: EmailTemplatePreviewRequest = {
        template_id: 'template-123',
        variables: {
          candidate_name: 'John Doe',
          recruiter_name: 'Jane Smith',
        },
      };

      const mockPreview: EmailTemplatePreviewResponse = {
        subject: 'Feedback for John Doe',
        body: 'Dear Jane Smith, feedback is ready.',
        html_body: '<p>Dear Jane Smith, feedback is ready.</p>',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockPreview });

      const result = await client.previewEmailTemplate(previewRequest);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/email-templates/preview',
        previewRequest
      );
      expect(result).toEqual(mockPreview);
    });
  });

  describe('Workflow Stage Configurations', () => {
    const mockStage: WorkflowStageConfigResponse = {
      id: 'stage-123',
      organization_id: 'org-123',
      stage_name: 'Technical Interview',
      stage_order: 3,
      is_default: false,
      is_active: true,
      color: '#3B82F6',
      description: 'Technical assessment',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('should create a workflow stage configuration', async () => {
      const createRequest: WorkflowStageConfigCreate = {
        organization_id: 'org-123',
        stage_name: 'Technical Interview',
        stage_order: 3,
        color: '#3B82F6',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockStage });

      const result = await client.createWorkflowStageConfig(createRequest);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/workflow-stage-configs/',
        createRequest
      );
      expect(result).toEqual(mockStage);
    });

    it('should list workflow stage configurations', async () => {
      const mockResponse: WorkflowStageConfigListResponse = {
        organization_id: 'org-123',
        stages: [mockStage],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listWorkflowStageConfigs(
        'org-123',
        true,
        false
      );

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/workflow-stage-configs/',
        {
          params: {
            organization_id: 'org-123',
            is_active: true,
            is_default: false,
          },
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should get a workflow stage configuration by ID', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockStage });

      const result = await client.getWorkflowStageConfig('stage-123');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/workflow-stage-configs/stage-123'
      );
      expect(result).toEqual(mockStage);
    });

    it('should update a workflow stage configuration', async () => {
      const updateRequest: WorkflowStageConfigUpdate = {
        stage_name: 'Updated Stage Name',
      };

      const updatedStage = { ...mockStage, stage_name: 'Updated Stage Name' };
      mockAxiosInstance.put.mockResolvedValue({ data: updatedStage });

      const result = await client.updateWorkflowStageConfig(
        'stage-123',
        updateRequest
      );

      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/api/workflow-stage-configs/stage-123',
        updateRequest
      );
      expect(result).toEqual(updatedStage);
    });

    it('should delete a workflow stage configuration', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await client.deleteWorkflowStageConfig('stage-123');

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/workflow-stage-configs/stage-123'
      );
    });

    it('should reorder workflow stages', async () => {
      const reorderRequest: ReorderWorkflowStagesRequest = {
        stage_orders: [
          { id: 'stage-1', stage_order: 1 },
          { id: 'stage-2', stage_order: 2 },
          { id: 'stage-3', stage_order: 3 },
        ],
      };

      const mockResponse: ReorderWorkflowStagesResponse = {
        message: 'Stages reordered successfully',
        updated_stages: [mockStage],
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await client.reorderWorkflowStages(reorderRequest);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/workflow-stage-configs/reorder',
        reorderRequest
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Error Handling', () => {
    it('should transform network errors', async () => {
      const networkError = new Error('Network Error');
      (networkError as any).code = 'ECONNABORTED';
      mockAxiosInstance.post.mockRejectedValue(networkError);

      await expect(
        client.createOrganization({
          name: 'Test',
          slug: 'test',
        })
      ).rejects.toMatchObject({
        detail: 'Request timeout. Please check your connection and try again.',
        status: 408,
      });
    });

    it('should transform HTTP errors', async () => {
      const httpError = {
        response: {
          status: 404,
          data: { detail: 'Organization not found' },
        },
      };
      mockAxiosInstance.get.mockRejectedValue(httpError);

      await expect(
        client.getOrganization('nonexistent')
      ).rejects.toMatchObject({
        detail: 'Organization not found',
        status: 404,
      });
    });

    it('should use default error messages', async () => {
      const httpError = {
        response: {
          status: 500,
          data: {},
        },
      };
      mockAxiosInstance.get.mockRejectedValue(httpError);

      await expect(
        client.getOrganization('error-id')
      ).rejects.toMatchObject({
        detail: 'Server error. Please try again later.',
        status: 500,
      });
    });
  });

  describe('getAxiosInstance', () => {
    it('should return the underlying axios instance', () => {
      const instance = client.getAxiosInstance();
      expect(instance).toBe(mockAxiosInstance);
    });
  });
});
