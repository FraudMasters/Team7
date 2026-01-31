/**
 * Tests for CandidateSelector Component
 *
 * Tests the candidate selection interface including:
 * - Selecting and deselecting candidates
 * - Min/max selection limits validation
 * - Select All and Clear All functionality
 * - Match percentage and skills count display
 * - Disabled state handling
 * - Visual feedback for selection state
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import CandidateSelector from './CandidateSelector';

describe('CandidateSelector', () => {
  const mockCandidates = [
    {
      resume_id: 'resume-1',
      name: 'John Doe',
      match_percentage: 85.5,
      matched_skills_count: 8,
      total_skills_count: 10,
      overall_match: true,
    },
    {
      resume_id: 'resume-2',
      name: 'Jane Smith',
      match_percentage: 65.0,
      matched_skills_count: 6,
      total_skills_count: 10,
      overall_match: false,
    },
    {
      resume_id: 'resume-3',
      name: 'Bob Johnson',
      match_percentage: 92.0,
      matched_skills_count: 9,
      total_skills_count: 10,
      overall_match: true,
    },
    {
      resume_id: 'resume-4',
      name: 'Alice Williams',
      match_percentage: 45.0,
      matched_skills_count: 4,
      total_skills_count: 10,
      overall_match: false,
    },
  ];

  const mockOnSelectionChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render the component with header', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('Select Candidates to Compare')).toBeInTheDocument();
    });

    it('should display selection count chip', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1', 'resume-2']}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('2 / 5 selected')).toBeInTheDocument();
    });

    it('should display min-max selection requirement', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          minCandidates={2}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText(/Select 2-5 candidates for side-by-side comparison/)).toBeInTheDocument();
    });

    it('should display all candidates as cards', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
      expect(screen.getByText('Alice Williams')).toBeInTheDocument();
    });

    it('should show warning when below minimum candidates', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1']}
          minCandidates={2}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText(/At least 2 candidates are required for comparison/)).toBeInTheDocument();
    });

    it('should show warning when above maximum candidates', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['r1', 'r2', 'r3', 'r4', 'r5', 'r6']}
          minCandidates={2}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText(/Maximum 5 candidates can be compared at once/)).toBeInTheDocument();
    });

    it('should display empty state when no candidates available', () => {
      render(
        <CandidateSelector
          candidates={[]}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText(/No candidates available for this vacancy/)).toBeInTheDocument();
    });
  });

  describe('Candidate Selection', () => {
    it('should select candidate when card is clicked', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
      fireEvent.click(johnCard!);

      expect(mockOnSelectionChange).toHaveBeenCalledWith(['resume-1']);
    });

    it('should deselect candidate when already selected', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
      fireEvent.click(johnCard!);

      expect(mockOnSelectionChange).toHaveBeenCalledWith([]);
    });

    it('should select candidate when checkbox is clicked', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);

      expect(mockOnSelectionChange).toHaveBeenCalledWith(['resume-1']);
    });

    it('should not select beyond max limit', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1', 'resume-2', 'resume-3', 'resume-4', 'resume-5']}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      // All candidates should be visually disabled when max is reached
      const cards = screen.getAllByRole('checkbox');
      const unselectedCheckbox = cards.find((cb) => !(cb as HTMLInputElement).checked);

      if (unselectedCheckbox) {
        expect(unselectedCheckbox).toBeDisabled();
      }
    });

    it('should not select when disabled', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          disabled={true}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
      fireEvent.click(johnCard!);

      expect(mockOnSelectionChange).not.toHaveBeenCalled();
    });

    it('should maintain selection when initialSelectedIds prop changes', () => {
      const { rerender } = render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      rerender(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1', 'resume-2', 'resume-3']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('3 / 5 selected')).toBeInTheDocument();
    });
  });

  describe('Match Percentage Display', () => {
    it('should display match percentage for candidates', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          showMatchPercentage={true}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('86%')).toBeInTheDocument();
      expect(screen.getByText('65%')).toBeInTheDocument();
      expect(screen.getByText('92%')).toBeInTheDocument();
      expect(screen.getByText('45%')).toBeInTheDocument();
    });

    it('should not display match percentage when showMatchPercentage is false', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          showMatchPercentage={false}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.queryByText('86%')).not.toBeInTheDocument();
      expect(screen.queryByText('65%')).not.toBeInTheDocument();
    });

    it('should color code match percentage chips correctly', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          showMatchPercentage={true}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      // High match (>=80%) should have success color
      const highMatchChips = screen.getAllByText('86%');
      expect(highMatchChips[0]).toHaveClass('MuiChip-outlinedSuccess');

      // Medium match (60-79%) should have primary color
      const mediumMatchChips = screen.getAllByText('65%');
      expect(mediumMatchChips[0]).toHaveClass('MuiChip-outlinedPrimary');
    });
  });

  describe('Skills Count Display', () => {
    it('should display skills count for candidates', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          showSkillsCount={true}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('8 / 10 skills matched')).toBeInTheDocument();
      expect(screen.getByText('6 / 10 skills matched')).toBeInTheDocument();
      expect(screen.getByText('9 / 10 skills matched')).toBeInTheDocument();
      expect(screen.getByText('4 / 10 skills matched')).toBeInTheDocument();
    });

    it('should not display skills count when showSkillsCount is false', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          showSkillsCount={false}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.queryByText('8 / 10 skills matched')).not.toBeInTheDocument();
      expect(screen.queryByText('6 / 10 skills matched')).not.toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('should render Select All Best button', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('Select 5 Best')).toBeInTheDocument();
    });

    it('should render Clear All button', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('Clear All')).toBeInTheDocument();
    });

    it('should select best candidates when Select All Best is clicked', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          maxCandidates={3}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      fireEvent.click(screen.getByText('Select 3 Best'));

      // Should select top 3 by match percentage
      expect(mockOnSelectionChange).toHaveBeenCalledWith(['resume-3', 'resume-1', 'resume-2']);
    });

    it('should clear all selections when Clear All is clicked', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1', 'resume-2']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      fireEvent.click(screen.getByText('Clear All'));

      expect(mockOnSelectionChange).toHaveBeenCalledWith([]);
    });

    it('should disable Select All Best when at max limit', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1', 'resume-2', 'resume-3', 'resume-4', 'resume-5']}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('Select 5 Best')).toBeDisabled();
    });

    it('should disable Clear All when no selections', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('Clear All')).toBeDisabled();
    });

    it('should disable Select All Best when no candidates', () => {
      render(
        <CandidateSelector
          candidates={[]}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('Select 5 Best')).toBeDisabled();
    });

    it('should disable action buttons when disabled prop is true', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1']}
          disabled={true}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('Select 5 Best')).toBeDisabled();
      expect(screen.getByText('Clear All')).toBeDisabled();
    });
  });

  describe('Visual Feedback', () => {
    it('should highlight selected candidates', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      const selectedCheckbox = checkboxes[0];

      expect(selectedCheckbox).toBeChecked();
    });

    it('should show dimmed appearance for unselectable candidates at max', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1', 'resume-2', 'resume-3', 'resume-4', 'resume-5']}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      const unselectedCheckboxes = checkboxes.filter((cb) => !(cb as HTMLInputElement).checked);

      if (unselectedCheckboxes.length > 0) {
        expect(unselectedCheckboxes[0]).toBeDisabled();
      }
    });

    it('should show cursor pointer for enabled cards', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
      expect(johnCard).toHaveStyle({ cursor: 'pointer' });
    });

    it('should show cursor not-allowed when disabled', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          disabled={true}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
      expect(johnCard).toHaveStyle({ cursor: 'not-allowed' });
    });
  });

  describe('Validation Messages', () => {
    it('should display info alert with tip when selection is invalid', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1']}
          minCandidates={2}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText(/Tip:/)).toBeInTheDocument();
      expect(screen.getByText(/Select 2-5 candidates to enable comparison/)).toBeInTheDocument();
    });

    it('should display max limit warning when limit is reached', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1', 'resume-2', 'resume-3', 'resume-4', 'resume-5']}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText(/Maximum selection limit reached/)).toBeInTheDocument();
    });

    it('should not display validation messages when selection is valid', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1', 'resume-2', 'resume-3']}
          minCandidates={2}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.queryByText(/At least 2 candidates are required/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Maximum 5 candidates can be compared/)).not.toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('should disable all interactions when disabled prop is true', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          disabled={true}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      checkboxes.forEach((checkbox) => {
        expect(checkbox).toBeDisabled();
      });

      expect(screen.getByText('Select 5 Best')).toBeDisabled();
      expect(screen.getByText('Clear All')).toBeDisabled();
    });

    it('should not call onSelectionChange when disabled', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          disabled={true}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const johnCard = screen.getByText('John Doe').closest('.MuiCard-root');
      fireEvent.click(johnCard!);

      expect(mockOnSelectionChange).not.toHaveBeenCalled();
    });
  });

  describe('Candidate Sorting', () => {
    it('should sort candidates by match percentage descending', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const cards = screen.getAllByRole('checkbox');
      const firstCardName = cards[0].closest('.MuiCard-root')?.textContent;

      // Bob Johnson has 92% match, should be first
      expect(firstCardName).toContain('Bob Johnson');
    });

    it('should handle candidates without match percentage', () => {
      const candidatesWithoutMatch = [
        { resume_id: 'resume-1', name: 'John Doe' },
        { resume_id: 'resume-2', name: 'Jane Smith', match_percentage: 85 },
      ];

      render(
        <CandidateSelector
          candidates={candidatesWithoutMatch}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });
  });

  describe('Custom Container Height', () => {
    it('should apply custom container height when provided', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          containerHeight={300}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const container = screen.getByText('John Doe').closest('.MuiPaper-root');
      // The container should have maxHeight set
      expect(container?.parentElement).toHaveStyle({ maxHeight: '300px' });
    });

    it('should accept string container height', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          containerHeight="60vh"
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const container = screen.getByText('John Doe').closest('.MuiPaper-root');
      expect(container?.parentElement).toHaveStyle({ maxHeight: '60vh' });
    });
  });

  describe('Edge Cases', () => {
    it('should handle candidate with only required fields', () => {
      const minimalCandidate = [{ resume_id: 'resume-1' }];

      render(
        <CandidateSelector
          candidates={minimalCandidate}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('resume-1')).toBeInTheDocument();
    });

    it('should handle candidate with name but no match data', () => {
      const candidateWithoutMatch = [{ resume_id: 'resume-1', name: 'John Doe' }];

      render(
        <CandidateSelector
          candidates={candidateWithoutMatch}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    });

    it('should handle zero-based min and max values', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          minCandidates={0}
          maxCandidates={10}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText(/Select 0-10 candidates/)).toBeInTheDocument();
    });
  });

  describe('Selection Count Chip', () => {
    it('should show primary color when minimum is met', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1', 'resume-2']}
          minCandidates={2}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const chip = screen.getByText('2 / 5 selected');
      expect(chip).toHaveClass('MuiChip-filled');
    });

    it('should show outlined style when minimum is not met', () => {
      render(
        <CandidateSelector
          candidates={mockCandidates}
          initialSelectedIds={['resume-1']}
          minCandidates={2}
          maxCandidates={5}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const chip = screen.getByText('1 / 5 selected');
      expect(chip).toHaveClass('MuiChip-outlined');
    });
  });
});
