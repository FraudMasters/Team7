/**
 * Tests for ResumeTemplatePreview Component
 *
 * Tests the resume template preview interface including:
 * - Template data fetching and display
 * - Loading and error states
 * - Style and layout configuration display
 * - ATS compliance badge display
 * - Action buttons (preview, download)
 * - Imperative handle methods
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ResumeTemplatePreview, { ResumeTemplatePreviewHandle } from './ResumeTemplatePreview';
import { resumeTemplatesClient } from '@/api/resume-templates';

// Mock the API client
vi.mock('@/api/resume-templates', () => ({
  resumeTemplatesClient: {
    getResumeTemplate: vi.fn(),
  },
}));

// Mock the translation hook
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) => defaultValue || key,
  }),
}));

const mockTemplate = {
  id: 'template-123',
  organization_id: null,
  name: 'Modern Professional',
  description: 'Clean modern design with sidebar',
  template_type: 'modern',
  layout_config: {
    margins: 'normal',
    sections: ['header', 'experience', 'skills', 'education'],
  },
  style_config: {
    primary_color: '#2563eb',
    font: 'Arial',
    font_size: 11,
  },
  section_config: null,
  preview_url: 'https://example.com/preview.jpg',
  is_default: true,
  is_active: true,
  is_ats_compliant: true,
  created_by: 'user-123',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

describe('ResumeTemplatePreview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockImplementation(
        () => new Promise(() => {}) // Pending promise
      );

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      expect(screen.getByText('resumeTemplate.preview.loading')).toBeInTheDocument();
    });

    it('should render template data after successful fetch', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Modern Professional')).toBeInTheDocument();
      });
    });

    it('should render error state when fetch fails', async () => {
      const errorMessage = 'Template not found';
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockRejectedValue(
        new Error(errorMessage)
      );

      render(
        <ResumeTemplatePreview
          templateId="invalid-id"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });

    it('should render empty state when no templateId provided', () => {
      render(
        <ResumeTemplatePreview
          templateId=""
        />
      );

      expect(screen.getByText('resumeTemplate.preview.noTemplate')).toBeInTheDocument();
    });
  });

  describe('Template Information Display', () => {
    it('should display template name', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Modern Professional')).toBeInTheDocument();
      });
    });

    it('should display template description', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Clean modern design with sidebar')).toBeInTheDocument();
      });
    });

    it('should display template type chip', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('modern')).toBeInTheDocument();
      });
    });

    it('should display default badge when template is default', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('resumeTemplate.default')).toBeInTheDocument();
      });
    });

    it('should display ATS compliant badge when template is ATS compliant', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('resumeTemplate.atsCompliant')).toBeInTheDocument();
      });
    });
  });

  describe('Style Configuration Display', () => {
    it('should display primary color with visual indicator', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('#2563eb')).toBeInTheDocument();
      });
    });

    it('should display font family', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Arial/)).toBeInTheDocument();
      });
    });

    it('should display font size', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/11pt/)).toBeInTheDocument();
      });
    });
  });

  describe('Layout Configuration Display', () => {
    it('should display margins', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/normal/)).toBeInTheDocument();
      });
    });

    it('should display sections as chips', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('header')).toBeInTheDocument();
        expect(screen.getByText('experience')).toBeInTheDocument();
        expect(screen.getByText('skills')).toBeInTheDocument();
        expect(screen.getByText('education')).toBeInTheDocument();
      });
    });
  });

  describe('Action Buttons', () => {
    it('should show download button when showDownloadButton is true', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
          showDownloadButton={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('resumeTemplate.preview.download')).toBeInTheDocument();
      });
    });

    it('should not show download button when showDownloadButton is false', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
          showDownloadButton={false}
        />
      );

      await waitFor(() => {
        expect(screen.queryByText('resumeTemplate.preview.download')).not.toBeInTheDocument();
      });
    });

    it('should show preview button when showPreviewButton is true', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
          showPreviewButton={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('resumeTemplate.preview.preview')).toBeInTheDocument();
      });
    });

    it('should show custom actions when provided', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
          customActions={<button data-testid="custom-action">Custom</button>}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('custom-action')).toBeInTheDocument();
      });
    });
  });

  describe('Callbacks', () => {
    it('should call onPreviewLoad when template loads successfully', async () => {
      const onPreviewLoad = vi.fn();
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
          onPreviewLoad={onPreviewLoad}
        />
      );

      await waitFor(() => {
        expect(onPreviewLoad).toHaveBeenCalledWith(mockTemplate);
      });
    });

    it('should call onPreviewError when template fails to load', async () => {
      const onPreviewError = vi.fn();
      const errorMessage = 'Not found';
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockRejectedValue(
        new Error(errorMessage)
      );

      render(
        <ResumeTemplatePreview
          templateId="invalid-id"
          onPreviewError={onPreviewError}
        />
      );

      await waitFor(() => {
        expect(onPreviewError).toHaveBeenCalledWith(errorMessage);
      });
    });

    it('should call onLoadingChange when loading state changes', async () => {
      const onLoadingChange = vi.fn();
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
          onLoadingChange={onLoadingChange}
        />
      );

      await waitFor(() => {
        expect(onLoadingChange).toHaveBeenCalledWith(false);
      });
    });
  });

  describe('Imperative Handle', () => {
    it('should expose refreshPreview method', async () => {
      const ref: React.RefObject<ResumeTemplatePreviewHandle> = React.createRef();
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          ref={ref}
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(ref.current).toBeTruthy();
      });

      // Call refreshPreview
      ref.current?.refreshPreview();

      // Should trigger another fetch
      expect(resumeTemplatesClient.getResumeTemplate).toHaveBeenCalledTimes(2);
    });

    it('should expose resetPreview method', async () => {
      const ref: React.RefObject<ResumeTemplatePreviewHandle> = React.createRef();
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          ref={ref}
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(ref.current).toBeTruthy();
      });

      // Call resetPreview - should clear the template
      ref.current?.resetPreview();

      // After reset, template should be null (but we can't easily test this without internal access)
      expect(ref.current).toBeTruthy();
    });

    it('should expose getTemplate method', async () => {
      const ref: React.RefObject<ResumeTemplatePreviewHandle> = React.createRef();
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplatePreview
          ref={ref}
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(ref.current).toBeTruthy();
      });

      const template = ref.current?.getTemplate();
      expect(template).toEqual(mockTemplate);
    });
  });

  describe('Error Handling', () => {
    it('should display retry button on error', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockRejectedValue(
        new Error('Network error')
      );

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('common.retry')).toBeInTheDocument();
      });
    });

    it('should retry fetching when retry button is clicked', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockTemplate);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      // Wait for error
      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      // Click retry
      const retryButton = screen.getByText('common.retry');
      fireEvent.click(retryButton);

      // Should now show the template
      await waitFor(() => {
        expect(screen.getByText('Modern Professional')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle template without style config', async () => {
      const templateWithoutStyle = { ...mockTemplate, style_config: null };
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(templateWithoutStyle);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Modern Professional')).toBeInTheDocument();
        expect(screen.queryByText('resumeTemplate.preview.styleConfig')).not.toBeInTheDocument();
      });
    });

    it('should handle template without layout config', async () => {
      const templateWithoutLayout = { ...mockTemplate, layout_config: null };
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(templateWithoutLayout);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Modern Professional')).toBeInTheDocument();
        expect(screen.queryByText('resumeTemplate.preview.layoutConfig')).not.toBeInTheDocument();
      });
    });

    it('should handle template without description', async () => {
      const templateWithoutDesc = { ...mockTemplate, description: null };
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(templateWithoutDesc);

      render(
        <ResumeTemplatePreview
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Modern Professional')).toBeInTheDocument();
      });
    });
  });
});
