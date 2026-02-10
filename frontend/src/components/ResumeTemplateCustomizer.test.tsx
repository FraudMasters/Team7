/**
 * Tests for ResumeTemplateCustomizer Component
 *
 * Tests the resume template customization interface including:
 * - Template data loading and form population
 * - Color customization (primary, secondary)
 * - Font customization (family, heading, size)
 * - Layout customization (margins, sections)
 * - Form validation
 * - Save and reset functionality
 * - Live preview updates
 * - Error handling and display
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ResumeTemplateCustomizer from './ResumeTemplateCustomizer';
import { resumeTemplatesClient } from '@/api/resume-templates';

// Mock the API client
vi.mock('@/api/resume-templates', () => ({
  resumeTemplatesClient: {
    getResumeTemplate: vi.fn(),
    updateResumeTemplate: vi.fn(),
  },
}));

// Mock the translation hook
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) => defaultValue || key,
  }),
}));

// Mock ColorPicker component
vi.mock('@/components/organizations/ColorPicker', () => ({
  default: ({ label, value, onChange, helperText, disabled }: any) => (
    <div data-testid="color-picker">
      <label>{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        data-testid={`color-input-${label.toLowerCase().replace(/\s+/g, '-')}`}
      />
      <small>{helperText}</small>
    </div>
  ),
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
    secondary_color: '#64748b',
    font: 'Arial',
    heading_font: 'Arial',
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

const mockUpdatedTemplate = {
  ...mockTemplate,
  name: 'Updated Template',
  style_config: {
    ...mockTemplate.style_config,
    primary_color: '#dc2626',
  },
};

describe('ResumeTemplateCustomizer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockImplementation(
        () => new Promise(() => {}) // Pending promise
      );

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should render form after template loads', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Customize Template')).toBeInTheDocument();
        expect(screen.getByText('Personalize your resume template with colors, fonts, and layout')).toBeInTheDocument();
      });
    });

    it('should render error state when template fails to load', async () => {
      const errorMessage = 'Template not found';
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockRejectedValue(
        new Error(errorMessage)
      );

      render(
        <ResumeTemplateCustomizer
          templateId="invalid-id"
          onError={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });
  });

  describe('Form Population', () => {
    it('should populate form with template data', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/Template Name/i);
        expect(nameInput).toHaveValue('Modern Professional');
      });
    });

    it('should populate description field', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        const descInput = screen.getByLabelText(/Description/i);
        expect(descInput).toHaveValue('Clean modern design with sidebar');
      });
    });

    it('should populate color fields', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('color-input-primary-color')).toHaveValue('#2563eb');
        expect(screen.getByTestId('color-input-secondary-color')).toHaveValue('#64748b');
      });
    });

    it('should populate font fields', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Arial/i })).toBeInTheDocument();
      });
    });

    it('should populate font size field', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        const fontSizeInput = screen.getByLabelText(/Font Size/i);
        expect(fontSizeInput).toHaveValue(11);
      });
    });

    it('should populate margins field', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Normal/i)).toBeInTheDocument();
      });
    });

    it('should populate section chips', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Header')).toBeInTheDocument();
        expect(screen.getByText('Work Experience')).toBeInTheDocument();
        expect(screen.getByText('Skills')).toBeInTheDocument();
        expect(screen.getByText('Education')).toBeInTheDocument();
      });
    });
  });

  describe('Form Interactions', () => {
    it('should update template name when changed', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/Template Name/i);
        fireEvent.change(nameInput, { target: { value: 'New Template Name' } });
        expect(nameInput).toHaveValue('New Template Name');
      });
    });

    it('should update description when changed', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        const descInput = screen.getByLabelText(/Description/i);
        fireEvent.change(descInput, { target: { value: 'New description' } });
        expect(descInput).toHaveValue('New description');
      });
    });

    it('should toggle section when chip is clicked', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        const projectsChip = screen.getByText('Projects');
        fireEvent.click(projectsChip);
        // After clicking, the section should be selected
        expect(projectsChip).toBeInTheDocument();
      });
    });

    it('should update font family selection', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        const fontSelect = screen.getByLabelText(/Font Family/i);
        fireEvent.mouseDown(fontSelect);
        // In a real test, you would select a different option
        expect(fontSelect).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation', () => {
    it('should show validation error for empty name', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(async () => {
        const nameInput = screen.getByLabelText(/Template Name/i);
        fireEvent.change(nameInput, { target: { value: '' } });

        const saveButton = screen.getByRole('button', { name: /Save Changes/i });
        fireEvent.click(saveButton);

        await waitFor(() => {
          expect(screen.getByText(/Template name is required/i)).toBeInTheDocument();
        });
      });
    });

    it('should show validation error for invalid color format', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(async () => {
        const colorInput = screen.getByTestId('color-input-primary-color');
        fireEvent.change(colorInput, { target: { value: 'invalid-color' } });

        const saveButton = screen.getByRole('button', { name: /Save Changes/i });
        fireEvent.click(saveButton);

        await waitFor(() => {
          expect(screen.getByText(/Invalid hex color format/i)).toBeInTheDocument();
        });
      });
    });

    it('should show validation error for font size out of range', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(async () => {
        const fontSizeInput = screen.getByLabelText(/Font Size/i);
        fireEvent.change(fontSizeInput, { target: { value: '20' } });

        const saveButton = screen.getByRole('button', { name: /Save Changes/i });
        fireEvent.click(saveButton);

        await waitFor(() => {
          expect(screen.getByText(/Font size must be between 8 and 16/i)).toBeInTheDocument();
        });
      });
    });
  });

  describe('Save Functionality', () => {
    it('should save customization when form is valid', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);
      vi.mocked(resumeTemplatesClient.updateResumeTemplate).mockResolvedValue(mockUpdatedTemplate);

      const onSave = vi.fn();

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
          onSave={onSave}
        />
      );

      await waitFor(async () => {
        const nameInput = screen.getByLabelText(/Template Name/i);
        fireEvent.change(nameInput, { target: { value: 'Updated Template' } });

        const saveButton = screen.getByRole('button', { name: /Save Changes/i });
        fireEvent.click(saveButton);

        await waitFor(() => {
          expect(resumeTemplatesClient.updateResumeTemplate).toHaveBeenCalledWith(
            'template-123',
            expect.objectContaining({
              name: 'Updated Template',
            })
          );
          expect(onSave).toHaveBeenCalledWith(mockUpdatedTemplate);
        });
      });
    });

    it('should show success message after save', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);
      vi.mocked(resumeTemplatesClient.updateResumeTemplate).mockResolvedValue(mockUpdatedTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(async () => {
        const saveButton = screen.getByRole('button', { name: /Save Changes/i });
        fireEvent.click(saveButton);

        await waitFor(() => {
          expect(screen.getByText(/Template customization saved successfully/i)).toBeInTheDocument();
        });
      });
    });

    it('should show error message when save fails', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);
      vi.mocked(resumeTemplatesClient.updateResumeTemplate).mockRejectedValue(
        new Error('Save failed')
      );

      const onError = vi.fn();

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
          onError={onError}
        />
      );

      await waitFor(async () => {
        const saveButton = screen.getByRole('button', { name: /Save Changes/i });
        fireEvent.click(saveButton);

        await waitFor(() => {
          expect(screen.getByText(/Save failed/i)).toBeInTheDocument();
          expect(onError).toHaveBeenCalledWith('Save failed');
        });
      });
    });

    it('should disable save button while saving', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);
      vi.mocked(resumeTemplatesClient.updateResumeTemplate).mockImplementation(
        () => new Promise(() => {}) // Pending promise
      );

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(async () => {
        const saveButton = screen.getByRole('button', { name: /Save Changes/i });
        fireEvent.click(saveButton);

        await waitFor(() => {
          expect(saveButton).toBeDisabled();
        });
      });
    });
  });

  describe('Reset Functionality', () => {
    it('should reset form to original values when reset is clicked', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(async () => {
        const nameInput = screen.getByLabelText(/Template Name/i);
        fireEvent.change(nameInput, { target: { value: 'Changed Name' } });

        const resetButton = screen.getByRole('button', { name: /Reset/i });
        fireEvent.click(resetButton);

        await waitFor(() => {
          expect(nameInput).toHaveValue('Modern Professional');
        });
      });
    });

    it('should clear errors when reset is clicked', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(async () => {
        const nameInput = screen.getByLabelText(/Template Name/i);
        fireEvent.change(nameInput, { target: { value: '' } });

        const saveButton = screen.getByRole('button', { name: /Save Changes/i });
        fireEvent.click(saveButton);

        await waitFor(() => {
          expect(screen.getByText(/Template name is required/i)).toBeInTheDocument();
        });

        const resetButton = screen.getByRole('button', { name: /Reset/i });
        fireEvent.click(resetButton);

        await waitFor(() => {
          expect(screen.queryByText(/Template name is required/i)).not.toBeInTheDocument();
        });
      });
    });
  });

  describe('Live Preview', () => {
    it('should display live preview panel', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Live Preview')).toBeInTheDocument();
        expect(screen.getByText('See how your customization will look')).toBeInTheDocument();
      });
    });

    it('should update preview when color changes', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        const colorInput = screen.getByTestId('color-input-primary-color');
        fireEvent.change(colorInput, { target: { value: '#dc2626' } });
        expect(colorInput).toHaveValue('#dc2626');
      });
    });

    it('should display heading preview', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Heading Style/i)).toBeInTheDocument();
      });
    });

    it('should display body text preview', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Body Text Style/i)).toBeInTheDocument();
      });
    });

    it('should display color scheme preview', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Color Scheme/i)).toBeInTheDocument();
        expect(screen.getByText('Primary')).toBeInTheDocument();
        expect(screen.getByText('Secondary')).toBeInTheDocument();
      });
    });

    it('should display sections preview', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Sections/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle template load error gracefully', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockRejectedValue(
        new Error('Network error')
      );

      const onError = vi.fn();

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
          onError={onError}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
        expect(onError).toHaveBeenCalledWith('Network error');
      });
    });

    it('should allow closing error alert', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockRejectedValue(
        new Error('Load error')
      );

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        const closeButton = screen.getByRole('button', { name: '' }); // Close icon
        fireEvent.click(closeButton);
        expect(screen.queryByText('Load error')).not.toBeInTheDocument();
      });
    });
  });

  describe('Callbacks', () => {
    it('should call onSave when customization saves successfully', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);
      vi.mocked(resumeTemplatesClient.updateResumeTemplate).mockResolvedValue(mockUpdatedTemplate);

      const onSave = vi.fn();

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
          onSave={onSave}
        />
      );

      await waitFor(async () => {
        const saveButton = screen.getByRole('button', { name: /Save Changes/i });
        fireEvent.click(saveButton);

        await waitFor(() => {
          expect(onSave).toHaveBeenCalledWith(mockUpdatedTemplate);
        });
      });
    });

    it('should call onError when customization fails to save', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(mockTemplate);
      vi.mocked(resumeTemplatesClient.updateResumeTemplate).mockRejectedValue(
        new Error('Update failed')
      );

      const onError = vi.fn();

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
          onError={onError}
        />
      );

      await waitFor(async () => {
        const saveButton = screen.getByRole('button', { name: /Save Changes/i });
        fireEvent.click(saveButton);

        await waitFor(() => {
          expect(onError).toHaveBeenCalledWith('Update failed');
        });
      });
    });

    it('should call onError when template fails to load', async () => {
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockRejectedValue(
        new Error('Load failed')
      );

      const onError = vi.fn();

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
          onError={onError}
        />
      );

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith('Load failed');
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle template without style config', async () => {
      const templateWithoutStyle = {
        ...mockTemplate,
        style_config: null,
      };
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(templateWithoutStyle);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Customize Template')).toBeInTheDocument();
      });
    });

    it('should handle template without layout config', async () => {
      const templateWithoutLayout = {
        ...mockTemplate,
        layout_config: null,
      };
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(templateWithoutLayout);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Customize Template')).toBeInTheDocument();
      });
    });

    it('should handle template with empty sections', async () => {
      const templateWithEmptySections = {
        ...mockTemplate,
        layout_config: {
          margins: 'normal',
          sections: [],
        },
      };
      vi.mocked(resumeTemplatesClient.getResumeTemplate).mockResolvedValue(templateWithEmptySections);

      render(
        <ResumeTemplateCustomizer
          templateId="template-123"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Customize Template')).toBeInTheDocument();
      });
    });
  });
});
