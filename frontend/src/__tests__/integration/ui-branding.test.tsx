/**
 * Integration test for UI branding display.
 *
 * This test verifies that organization branding is correctly displayed throughout the UI:
 * 1. Organization logo displays in header
 * 2. Brand colors are applied throughout UI
 * 3. Custom workflow stages are used in candidate pipeline
 *
 * Note: This is a component-level integration test that verifies the integration
 * between OrganizationContext, ThemeContext, and UI components.
 */
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios from 'axios';

// Context imports
import { ThemeProvider, useThemeContext } from '@/contexts/ThemeContext';
import { OrganizationProvider, useOrganizationContext } from '@/contexts/OrganizationContext';
import Layout from '@/components/Layout';

// Mock axios for API calls
vi.mock('axios');

// Mock organization data
const mockOrganization = {
  id: 'test-org-123',
  name: 'Test Branding Organization',
  slug: 'test-branding-org',
  domain: 'testbranding.com',
  logo_url: 'https://example.com/logo.png',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

// Mock branding data
const mockBranding = {
  id: 'branding-123',
  organization_id: 'test-org-123',
  primary_color: '#8B5CF6', // Purple
  secondary_color: '#10B981', // Green
  accent_color: '#F59E0B', // Orange
  background_color: '#FFFFFF',
  text_color: '#1F2937',
  font_family: 'Inter',
  logo_url: 'https://example.com/logo.png',
  favicon_url: 'https://example.com/favicon.ico',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockAxios = axios as jest.Mocked<typeof axios>;

describe('UI Branding Integration', () => {
  let queryClient: QueryClient;

  const createWrapper = () => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    return ({ children }: { children: React.ReactNode }) => (
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <OrganizationProvider organizationId="test-org-123">
            <ThemeProvider>
              {children}
            </ThemeProvider>
          </OrganizationProvider>
        </QueryClientProvider>
      </BrowserRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient?.clear();
  });

  describe('Organization Logo Display', () => {
    it('should display organization logo in header when available', async () => {
      // Mock API responses
      (axios.get as any).mockImplementation((url: string) => {
        if (url.includes('/organizations/')) {
          return Promise.resolve({ data: mockOrganization });
        }
        if (url.includes('/branding/')) {
          return Promise.resolve({
            data: {
              branding_settings: [mockBranding],
              total_count: 1,
            },
          });
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      render(<Layout />, { wrapper: createWrapper() });

      // Wait for organization data to load
      await waitFor(() => {
        expect(axios.get).toHaveBeenCalledWith('/api/organizations/test-org-123');
      });

      // Check if logo image is present
      await waitFor(() => {
        const logoImage = document.querySelector('img[src="https://example.com/logo.png"]');
        expect(logoImage).toBeInTheDocument();
      });

      // Check if organization name is displayed
      await waitFor(() => {
        const orgName = screen.getByText('Test Branding Organization');
        expect(orgName).toBeInTheDocument();
      });
    });

    it('should display default icon when organization logo is not available', async () => {
      // Mock organization without logo
      const orgWithoutLogo = { ...mockOrganization, logo_url: undefined };

      (axios.get as any).mockImplementation((url: string) => {
        if (url.includes('/organizations/')) {
          return Promise.resolve({ data: orgWithoutLogo });
        }
        if (url.includes('/branding/')) {
          return Promise.resolve({
            data: {
              branding_settings: [{ ...mockBranding, logo_url: undefined }],
              total_count: 1,
            },
          });
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      render(<Layout />, { wrapper: createWrapper() });

      // Wait for data to load
      await waitFor(() => {
        expect(axios.get).toHaveBeenCalled();
      });

      // Check that default icon is displayed (ResumeIcon)
      await waitFor(() => {
        const defaultIcon = document.querySelector('.MuiSvgIcon-root');
        expect(defaultIcon).toBeInTheDocument();
      });
    });
  });

  describe('Brand Colors Application', () => {
    it('should apply organization primary color to theme', async () => {
      (axios.get as any).mockImplementation((url: string) => {
        if (url.includes('/organizations/')) {
          return Promise.resolve({ data: mockOrganization });
        }
        if (url.includes('/branding/')) {
          return Promise.resolve({
            data: {
              branding_settings: [mockBranding],
              total_count: 1,
            },
          });
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      const TestComponent = () => {
        const { theme } = useThemeContext();

        return (
          <div>
            <span data-testid="primary-color">{theme.palette.primary.main}</span>
            <span data-testid="secondary-color">{theme.palette.secondary.main}</span>
          </div>
        );
      };

      render(<TestComponent />, { wrapper: createWrapper() });

      // Wait for branding to load
      await waitFor(() => {
        expect(axios.get).toHaveBeenCalledWith('/api/branding/', {
          params: { organization_id: 'test-org-123', is_active: true, limit: 1 },
        });
      });

      // Check if colors are applied
      await waitFor(() => {
        expect(screen.getByTestId('primary-color')).toHaveTextContent('#8B5CF6');
        expect(screen.getByTestId('secondary-color')).toHaveTextContent('#10B981');
      });
    });

    it('should use default colors when branding is not available', async () => {
      (axios.get as any).mockImplementation((url: string) => {
        if (url.includes('/organizations/')) {
          return Promise.resolve({ data: mockOrganization });
        }
        if (url.includes('/branding/')) {
          return Promise.resolve({
            data: {
              branding_settings: [],
              total_count: 0,
            },
          });
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      const TestComponent = () => {
        const { theme } = useThemeContext();

        return (
          <div>
            <span data-testid="primary-color">{theme.palette.primary.main}</span>
            <span data-testid="secondary-color">{theme.palette.secondary.main}</span>
          </div>
        );
      };

      render(<TestComponent />, { wrapper: createWrapper() });

      // Check if default colors are used
      await waitFor(() => {
        expect(screen.getByTestId('primary-color')).toHaveTextContent('#1976d2');
        expect(screen.getByTestId('secondary-color')).toHaveTextContent('#dc004e');
      });
    });
  });

  describe('Custom Workflow Stages', () => {
    it('should fetch and display custom workflow stages', async () => {
      const mockWorkflowStages = [
        {
          id: 'stage-1',
          organization_id: 'test-org-123',
          stage_name: 'Applied',
          stage_order: 1,
          color: '#8B5CF6',
          description: 'Candidate has submitted application',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'stage-2',
          organization_id: 'test-org-123',
          stage_name: 'Screening Call',
          stage_order: 2,
          color: '#10B981',
          description: 'Initial phone screening completed',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ];

      (axios.get as any).mockImplementation((url: string) => {
        if (url.includes('/organizations/')) {
          return Promise.resolve({ data: mockOrganization });
        }
        if (url.includes('/branding/')) {
          return Promise.resolve({
            data: {
              branding_settings: [mockBranding],
              total_count: 1,
            },
          });
        }
        if (url.includes('/workflow-stages/')) {
          return Promise.resolve({ data: mockWorkflowStages });
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      // Import WorkflowKanban dynamically to avoid issues
      const { default: WorkflowKanban } = await import('@/components/WorkflowKanban');

      render(<WorkflowKanban />, { wrapper: createWrapper() });

      // Wait for workflow stages to load
      await waitFor(() => {
        expect(axios.get).toHaveBeenCalledWith('/api/workflow-stages/');
      });

      // Check if custom stage names are displayed
      await waitFor(() => {
        expect(screen.getByText('Applied')).toBeInTheDocument();
        expect(screen.getByText('Screening Call')).toBeInTheDocument();
      });
    });
  });

  describe('Branding Integration', () => {
    it('should integrate organization context with theme context', async () => {
      (axios.get as any).mockImplementation((url: string) => {
        if (url.includes('/organizations/')) {
          return Promise.resolve({ data: mockOrganization });
        }
        if (url.includes('/branding/')) {
          return Promise.resolve({
            data: {
              branding_settings: [mockBranding],
              total_count: 1,
            },
          });
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      const TestComponent = () => {
        const orgContext = useOrganizationContext();
        const themeContext = useThemeContext();

        return (
          <div>
            <span data-testid="org-loaded">{orgContext.organization?.id || 'not-loaded'}</span>
            <span data-testid="branding-loaded">{orgContext.branding?.id || 'not-loaded'}</span>
            <span data-testid="theme-primary">{themeContext.theme.palette.primary.main}</span>
            <span data-testid="org-logo">{orgContext.getLogoUrl() || 'no-logo'}</span>
          </div>
        );
      };

      render(<TestComponent />, { wrapper: createWrapper() });

      // Verify all contexts are integrated
      await waitFor(() => {
        expect(screen.getByTestId('org-loaded')).toHaveTextContent('test-org-123');
        expect(screen.getByTestId('branding-loaded')).toHaveTextContent('branding-123');
        expect(screen.getByTestId('theme-primary')).toHaveTextContent('#8B5CF6');
        expect(screen.getByTestId('org-logo')).toHaveTextContent('https://example.com/logo.png');
      });
    });
  });
});
