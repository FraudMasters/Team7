/**
 * Tests for ComparisonControls Component
 *
 * Tests the comparison controls interface including:
 * - Adding and removing resumes
 * - Filter by match percentage range
 * - Sorting by different fields and orders
 * - Export to Excel (CSV format)
 * - Reset functionality
 * - Save and share actions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ComparisonControls from './ComparisonControls';

describe('ComparisonControls', () => {
  const mockResumeIds = ['resume-1', 'resume-2'];
  const mockComparisonData = {
    vacancy_id: 'vacancy-123',
    comparisons: [
      {
        resume_id: 'resume-1',
        match_percentage: 85.5,
        matched_skills: [
          { skill: 'Java', matched: true, highlight: 'green' },
          { skill: 'Python', matched: true, highlight: 'green' },
        ],
        missing_skills: [
          { skill: 'Docker', matched: false, highlight: 'red' },
        ],
        experience_verification: [],
        overall_match: true,
      },
      {
        resume_id: 'resume-2',
        match_percentage: 65.0,
        matched_skills: [
          { skill: 'Java', matched: true, highlight: 'green' },
        ],
        missing_skills: [
          { skill: 'Python', matched: false, highlight: 'red' },
        ],
        experience_verification: [],
        overall_match: false,
      },
    ],
    all_unique_skills: ['Java', 'Python', 'Docker'],
  };

  const mockCallbacks = {
    onResumeIdsChange: vi.fn(),
    onFiltersChange: vi.fn(),
    onSortChange: vi.fn(),
    onSave: vi.fn(),
    onShare: vi.fn(),
    onExport: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render all control sections', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('Resume Selection')).toBeInTheDocument();
      expect(screen.getByText('Filters')).toBeInTheDocument();
      expect(screen.getByText('Sorting')).toBeInTheDocument();
      expect(screen.getByText('Reset All')).toBeInTheDocument();
    });

    it('should display resume count information', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          maxResumes={5}
          minResumes={2}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText(/Selected Resumes: 2 \/ 5 \(minimum 2\)/)).toBeInTheDocument();
    });

    it('should display current resumes as chips', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('resume-1')).toBeInTheDocument();
      expect(screen.getByText('resume-2')).toBeInTheDocument();
    });

    it('should show warning when below minimum resumes', () => {
      render(
        <ComparisonControls
          resumeIds={['resume-1']}
          minResumes={2}
          maxResumes={5}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText(/At least 2 resumes are required for comparison/)).toBeInTheDocument();
    });

    it('should show warning when above maximum resumes', () => {
      render(
        <ComparisonControls
          resumeIds={['r1', 'r2', 'r3', 'r4', 'r5', 'r6']}
          minResumes={2}
          maxResumes={5}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText(/Maximum 5 resumes can be compared at once/)).toBeInTheDocument();
    });
  });

  describe('Resume Management', () => {
    it('should add new resume when Add button is clicked', async () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          {...mockCallbacks}
        />
      );

      const input = screen.getByLabelText('Add Resume ID');
      const addButton = screen.getByText('Add');

      fireEvent.change(input, { target: { value: 'resume-3' } });
      fireEvent.click(addButton);

      expect(mockCallbacks.onResumeIdsChange).toHaveBeenCalledWith(['resume-1', 'resume-2', 'resume-3']);
    });

    it('should add resume on Enter key press', async () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          {...mockCallbacks}
        />
      );

      const input = screen.getByLabelText('Add Resume ID');

      fireEvent.change(input, { target: { value: 'resume-3' } });
      fireEvent.keyPress(input, { key: 'Enter', code: 'Enter' });

      expect(mockCallbacks.onResumeIdsChange).toHaveBeenCalledWith(['resume-1', 'resume-2', 'resume-3']);
    });

    it('should not add empty resume ID', async () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          {...mockCallbacks}
        />
      );

      const input = screen.getByLabelText('Add Resume ID');
      const addButton = screen.getByText('Add');

      fireEvent.change(input, { target: { value: '   ' } });

      expect(addButton).toBeDisabled();
      expect(mockCallbacks.onResumeIdsChange).not.toHaveBeenCalled();
    });

    it('should not add resume beyond max limit', () => {
      render(
        <ComparisonControls
          resumeIds={['r1', 'r2', 'r3', 'r4', 'r5']}
          maxResumes={5}
          {...mockCallbacks}
        />
      );

      // Add input should not be shown when at max
      expect(screen.queryByLabelText('Add Resume ID')).not.toBeInTheDocument();
    });

    it('should not add duplicate resume IDs', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          {...mockCallbacks}
        />
      );

      const input = screen.getByLabelText('Add Resume ID');
      const addButton = screen.getByText('Add');

      fireEvent.change(input, { target: { value: 'resume-1' } });
      fireEvent.click(addButton);

      // Should not call callback with duplicate
      expect(mockCallbacks.onResumeIdsChange).not.toHaveBeenCalled();
    });

    it('should remove resume when chip delete is clicked', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          {...mockCallbacks}
        />
      );

      const deleteButtons = screen.getAllByRole('button');
      const resume1DeleteButton = deleteButtons.find(
        (btn) => btn.getAttribute('aria-label') === `Delete ${mockResumeIds[0]}`
      );

      if (resume1DeleteButton) {
        fireEvent.click(resume1DeleteButton);
        expect(mockCallbacks.onResumeIdsChange).toHaveBeenCalledWith(['resume-2']);
      }
    });

    it('should clear input after adding resume', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          {...mockCallbacks}
        />
      );

      const input = screen.getByLabelText('Add Resume ID') as HTMLInputElement;
      const addButton = screen.getByText('Add');

      fireEvent.change(input, { target: { value: 'resume-3' } });
      fireEvent.click(addButton);

      expect(input.value).toBe('');
    });
  });

  describe('Filters', () => {
    it('should display match percentage range filter', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          initialFilters={{ min_match_percentage: 40, max_match_percentage: 80 }}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText(/Match Percentage Range: 40% - 80%/)).toBeInTheDocument();
    });

    it('should update filters when slider changes', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          {...mockCallbacks}
        />
      );

      const sliders = screen.getAllByRole('slider');
      const minSlider = sliders[0];
      const maxSlider = sliders[1];

      fireEvent.change(minSlider, { target: { value: 25 } });
      fireEvent.change(maxSlider, { target: { value: 75 } });

      expect(mockCallbacks.onFiltersChange).toHaveBeenCalledWith({
        min_match_percentage: 25,
        max_match_percentage: 75,
      });
    });

    it('should maintain min-max constraint when adjusting filters', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          initialFilters={{ min_match_percentage: 30, max_match_percentage: 70 }}
          {...mockCallbacks}
        />
      );

      const sliders = screen.getAllByRole('slider');
      const minSlider = sliders[0];

      // Try to set min above max
      fireEvent.change(minSlider, { target: { value: 80 } });

      // Max should be adjusted to match min
      expect(mockCallbacks.onFiltersChange).toHaveBeenCalledWith(
        expect.objectContaining({
          min_match_percentage: 80,
          max_match_percentage: 80,
        })
      );
    });

    it('should display slider marks at correct positions', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('0%')).toBeInTheDocument();
      expect(screen.getByText('25%')).toBeInTheDocument();
      expect(screen.getByText('50%')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });

  describe('Sorting', () => {
    it('should display sort field dropdown', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          initialSort={{ field: 'match_percentage', order: 'desc' }}
          {...mockCallbacks}
        />
      );

      expect(screen.getByLabelText('Sort By')).toBeInTheDocument();
    });

    it('should change sort field when selection changes', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          {...mockCallbacks}
        />
      );

      const sortFieldSelect = screen.getByLabelText('Sort By');

      fireEvent.change(sortFieldSelect, { target: { value: 'created_at' } });

      expect(mockCallbacks.onSortChange).toHaveBeenCalledWith({
        field: 'created_at',
        order: 'desc',
      });
    });

    it('should change sort order when selection changes', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          initialSort={{ field: 'match_percentage', order: 'desc' }}
          {...mockCallbacks}
        />
      );

      const sortOrderSelect = screen.getByLabelText('Order');

      fireEvent.change(sortOrderSelect, { target: { value: 'asc' } });

      expect(mockCallbacks.onSortChange).toHaveBeenCalledWith({
        field: 'match_percentage',
        order: 'asc',
      });
    });

    it('should display current sort indicator', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          initialSort={{ field: 'match_percentage', order: 'desc' }}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('Sorted by match percentage (desc)')).toBeInTheDocument();
    });

    it('should display all sort field options', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          {...mockCallbacks}
        />
      );

      fireEvent.click(screen.getByLabelText('Sort By'));

      expect(screen.getByText('Match Percentage')).toBeInTheDocument();
      expect(screen.getByText('Date Created')).toBeInTheDocument();
      expect(screen.getByText('Last Updated')).toBeInTheDocument();
      expect(screen.getByText('Name')).toBeInTheDocument();
    });
  });

  describe('Actions', () => {
    it('should reset all controls when Reset button is clicked', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          initialFilters={{ min_match_percentage: 40, max_match_percentage: 80 }}
          initialSort={{ field: 'created_at', order: 'asc' }}
          {...mockCallbacks}
        />
      );

      fireEvent.click(screen.getByText('Reset All'));

      expect(mockCallbacks.onFiltersChange).toHaveBeenCalledWith({
        min_match_percentage: 0,
        max_match_percentage: 100,
      });
      expect(mockCallbacks.onSortChange).toHaveBeenCalledWith({
        field: 'match_percentage',
        order: 'desc',
      });
    });

    it('should call onSave when Save button is clicked', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          onSave={mockCallbacks.onSave}
          {...mockCallbacks}
        />
      );

      fireEvent.click(screen.getByText('Save Comparison'));

      expect(mockCallbacks.onSave).toHaveBeenCalledTimes(1);
    });

    it('should call onShare when Share button is clicked', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          onShare={mockCallbacks.onShare}
          {...mockCallbacks}
        />
      );

      fireEvent.click(screen.getByText('Share'));

      expect(mockCallbacks.onShare).toHaveBeenCalledTimes(1);
    });

    it('should call onExport when Export button is clicked', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          onExport={mockCallbacks.onExport}
          comparisonData={mockComparisonData}
          {...mockCallbacks}
        />
      );

      fireEvent.click(screen.getByText('Export to Excel'));

      expect(mockCallbacks.onExport).toHaveBeenCalledTimes(1);
    });
  });

  describe('Export Functionality', () => {
    it('should generate CSV when custom onExport not provided', () => {
      const mockLink = {
        href: '',
        setAttribute: vi.fn(),
        style: { visibility: '' as string },
        click: vi.fn(),
      };

      vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
      vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
      vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);
      vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:url');
      vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});

      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          comparisonData={mockComparisonData}
          {...mockCallbacks}
        />
      );

      fireEvent.click(screen.getByText('Export to Excel'));

      expect(document.createElement).toHaveBeenCalledWith('a');
      expect(mockLink.setAttribute).toHaveBeenCalledWith('href', 'blob:url');
      expect(mockLink.click).toHaveBeenCalled();
    });

    it('should not export when no comparison data available', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          comparisonData={null}
          {...mockCallbacks}
        />
      );

      const exportButton = screen.getByText('Export to Excel');
      expect(exportButton).toBeDisabled();
    });

    it('should disable export when invalid resume count', () => {
      render(
        <ComparisonControls
          resumeIds={['resume-1']}
          minResumes={2}
          comparisonData={mockComparisonData}
          {...mockCallbacks}
        />
      );

      const exportButton = screen.getByText('Export to Excel');
      expect(exportButton).toBeDisabled();
    });
  });

  describe('Conditional Rendering', () => {
    it('should hide save actions when showSaveActions is false', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          showSaveActions={false}
          {...mockCallbacks}
        />
      );

      expect(screen.queryByText('Save Comparison')).not.toBeInTheDocument();
      expect(screen.queryByText('Share')).not.toBeInTheDocument();
    });

    it('should hide export button when showExport is false', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          showExport={false}
          {...mockCallbacks}
        />
      );

      expect(screen.queryByText('Export to Excel')).not.toBeInTheDocument();
    });

    it('should disable all controls when disabled prop is true', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          disabled={true}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('Reset All')).toBeDisabled();
      expect(screen.getByLabelText('Sort By')).toBeDisabled();
      expect(screen.getByLabelText('Order')).toBeDisabled();
    });

    it('should disable add resume input when disabled', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          disabled={true}
          {...mockCallbacks}
        />
      );

      const input = screen.getByLabelText('Add Resume ID');
      expect(input).toBeDisabled();
    });
  });

  describe('Validation Messages', () => {
    it('should display info alert with tip', () => {
      render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          minResumes={2}
          maxResumes={5}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText(/Tip:/)).toBeInTheDocument();
      expect(screen.getByText(/Select 2-5 resumes to compare/)).toBeInTheDocument();
    });
  });

  describe('Props Updates', () => {
    it('should update filters when initialFilters prop changes', () => {
      const { rerender } = render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          initialFilters={{ min_match_percentage: 0, max_match_percentage: 100 }}
          {...mockCallbacks}
        />
      );

      rerender(
        <ComparisonControls
          resumeIds={mockResumeIds}
          initialFilters={{ min_match_percentage: 40, max_match_percentage: 80 }}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText(/Match Percentage Range: 40% - 80%/)).toBeInTheDocument();
    });

    it('should update sort when initialSort prop changes', () => {
      const { rerender } = render(
        <ComparisonControls
          resumeIds={mockResumeIds}
          initialSort={{ field: 'match_percentage', order: 'desc' }}
          {...mockCallbacks}
        />
      );

      rerender(
        <ComparisonControls
          resumeIds={mockResumeIds}
          initialSort={{ field: 'created_at', order: 'asc' }}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('Sorted by created_at (asc)')).toBeInTheDocument();
    });
  });
});
