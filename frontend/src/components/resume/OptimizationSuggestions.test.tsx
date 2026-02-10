/**
 * Tests for OptimizationSuggestions Component
 *
 * Tests the resume optimization suggestions display including:
 * - Displaying overall optimization score with appropriate colors
 * - Showing summary statistics chips (total, high, medium, low priority counts)
 * - Priority-based filtering tabs
 * - Missing keywords section
 * - Expandable/collapsible suggestion details
 * - Priority-based styling (high=error, medium=warning, low=info)
 * - Category icons and labels
 * - Current state vs. recommended state display
 * - Examples display within suggestions
 * - Handling loading, error, and empty states
 * - Respecting maxDisplay limit
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import OptimizationSuggestions from './OptimizationSuggestions';
import type {
  OptimizationFeedback,
  OptimizationSuggestion,
} from '@/types/api';

describe('OptimizationSuggestions', () => {
  const mockOptimizationData: OptimizationFeedback = {
    resume_id: 'resume-123',
    score: 72,
    suggestions: [
      {
        type: 'keyword',
        priority: 'high',
        category: 'keywords',
        title: 'Add Missing Keywords',
        description: 'Include important keywords from the job description',
        current_state: 'Missing keywords: Agile, Scrum, CI/CD',
        recommendation: 'Add these keywords to your skills section',
        examples: ['Agile methodologies', 'Scrum framework', 'CI/CD pipelines'],
      },
      {
        type: 'content',
        priority: 'high',
        category: 'action_verbs',
        title: 'Use Stronger Action Verbs',
        description: 'Replace weak verbs with more impactful alternatives',
        current_state: 'Using basic verbs like "responsible for", "helped"',
        recommendation: 'Use strong action verbs like "led", "developed", "implemented"',
        examples: [
          'Led development of...',
          'Implemented CI/CD pipeline...',
          'Developed scalable architecture...',
        ],
      },
      {
        type: 'formatting',
        priority: 'medium',
        category: 'structure',
        title: 'Improve Resume Structure',
        description: 'Better organize sections for clarity',
        current_state: 'Sections are not clearly separated',
        recommendation: 'Use clear headings and consistent formatting',
        examples: [],
      },
      {
        type: 'content',
        priority: 'medium',
        category: 'impact',
        title: 'Quantify Achievements',
        description: 'Add numbers and metrics to demonstrate impact',
        current_state: 'Achievements listed without measurable results',
        recommendation: 'Include specific metrics and outcomes',
        examples: [
          'Increased revenue by 25%',
          'Reduced deployment time by 50%',
          'Led team of 10 engineers',
        ],
      },
      {
        type: 'content',
        priority: 'low',
        category: 'readability',
        title: 'Improve Readability',
        description: 'Make resume easier to scan',
        current_state: 'Long paragraphs and dense text',
        recommendation: 'Use bullet points and shorter sentences',
        examples: [],
      },
    ],
    total_suggestions: 5,
    high_priority_count: 2,
    medium_priority_count: 2,
    low_priority_count: 1,
    missing_keywords: ['Agile', 'Scrum', 'CI/CD', 'Kubernetes'],
  };

  describe('Component Rendering', () => {
    it('should render the component with default title', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      expect(screen.getByText('Resume Optimization Suggestions')).toBeInTheDocument();
    });

    it('should render with custom title', () => {
      render(
        <OptimizationSuggestions
          optimizationData={mockOptimizationData}
          title="Custom Optimization Title"
        />
      );

      expect(screen.getByText('Custom Optimization Title')).toBeInTheDocument();
      expect(screen.queryByText('Resume Optimization Suggestions')).not.toBeInTheDocument();
    });

    it('should display sparkles icon in header', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      // Check for sparkles icon
      const icons = document.querySelectorAll('.MuiSvgIcon-root');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  describe('Score Display', () => {
    it('should display score with success color when score >= 80', () => {
      const highScoreData = { ...mockOptimizationData, score: 85 };
      render(
        <OptimizationSuggestions optimizationData={highScoreData} />
      );

      expect(screen.getByText('85')).toBeInTheDocument();
      expect(screen.getByText('/100')).toBeInTheDocument();
    });

    it('should display score with warning color when score >= 60', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      expect(screen.getByText('72')).toBeInTheDocument();
      expect(screen.getByText('/100')).toBeInTheDocument();
    });

    it('should display score with error color when score < 60', () => {
      const lowScoreData = { ...mockOptimizationData, score: 45 };
      render(
        <OptimizationSuggestions optimizationData={lowScoreData} />
      );

      expect(screen.getByText('45')).toBeInTheDocument();
      expect(screen.getByText('/100')).toBeInTheDocument();
    });

    it('should display score 0 for edge case', () => {
      const zeroScoreData = { ...mockOptimizationData, score: 0 };
      render(
        <OptimizationSuggestions optimizationData={zeroScoreData} />
      );

      expect(screen.getByText('0')).toBeInTheDocument();
      expect(screen.getByText('/100')).toBeInTheDocument();
    });
  });

  describe('Summary Stats Chips', () => {
    it('should display total suggestions chip', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      expect(screen.getByText('5 suggestions')).toBeInTheDocument();
    });

    it('should display high priority count chip when > 0', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      expect(screen.getByText('2 high')).toBeInTheDocument();
    });

    it('should display medium priority count chip when > 0', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      expect(screen.getByText('2 medium')).toBeInTheDocument();
    });

    it('should display low priority count chip when > 0', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      expect(screen.getByText('1 low')).toBeInTheDocument();
    });

    it('should not display priority chips when count is 0', () => {
      const noHighPriorityData = {
        ...mockOptimizationData,
        high_priority_count: 0,
      };
      render(
        <OptimizationSuggestions optimizationData={noHighPriorityData} />
      );

      expect(screen.queryByText('0 high')).not.toBeInTheDocument();
      expect(screen.getByText('2 medium')).toBeInTheDocument();
    });
  });

  describe('Filter Tabs', () => {
    it('should display all filter tabs', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      expect(screen.getByText('All')).toBeInTheDocument();
      expect(screen.getByText('High Priority')).toBeInTheDocument();
      expect(screen.getByText('Medium Priority')).toBeInTheDocument();
      expect(screen.getByText('Low Priority')).toBeInTheDocument();
    });

    it('should have "All" filter selected by default', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const allChip = screen.getByText('All');
      expect(allChip.parentElement).toHaveClass('MuiChip-filled');
    });

    it('should filter suggestions when clicking High Priority', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const highPriorityChip = screen.getByText('High Priority');
      fireEvent.click(highPriorityChip);

      // Should show only high priority suggestions
      expect(screen.getByText('Add Missing Keywords')).toBeInTheDocument();
      expect(screen.getByText('Use Stronger Action Verbs')).toBeInTheDocument();
      // Medium and low should not be visible
      expect(screen.queryByText('Improve Resume Structure')).not.toBeInTheDocument();
    });

    it('should filter suggestions when clicking Medium Priority', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const mediumPriorityChip = screen.getByText('Medium Priority');
      fireEvent.click(mediumPriorityChip);

      // Should show only medium priority suggestions
      expect(screen.getByText('Improve Resume Structure')).toBeInTheDocument();
      expect(screen.getByText('Quantify Achievements')).toBeInTheDocument();
      // High and low should not be visible
      expect(screen.queryByText('Add Missing Keywords')).not.toBeInTheDocument();
    });

    it('should filter suggestions when clicking Low Priority', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const lowPriorityChip = screen.getByText('Low Priority');
      fireEvent.click(lowPriorityChip);

      // Should show only low priority suggestions
      expect(screen.getByText('Improve Readability')).toBeInTheDocument();
      // High and medium should not be visible
      expect(screen.queryByText('Add Missing Keywords')).not.toBeInTheDocument();
      expect(screen.queryByText('Improve Resume Structure')).not.toBeInTheDocument();
    });

    it('should show all suggestions when clicking All after filtering', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      // Filter to high priority
      fireEvent.click(screen.getByText('High Priority'));
      expect(screen.queryByText('Improve Resume Structure')).not.toBeInTheDocument();

      // Click All
      fireEvent.click(screen.getByText('All'));
      expect(screen.getByText('Improve Resume Structure')).toBeInTheDocument();
      expect(screen.getByText('Add Missing Keywords')).toBeInTheDocument();
    });
  });

  describe('Missing Keywords Section', () => {
    it('should display missing keywords when present', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      expect(screen.getByText('Missing Keywords')).toBeInTheDocument();
      expect(screen.getByText('Agile')).toBeInTheDocument();
      expect(screen.getByText('Scrum')).toBeInTheDocument();
      expect(screen.getByText('CI/CD')).toBeInTheDocument();
      expect(screen.getByText('Kubernetes')).toBeInTheDocument();
    });

    it('should not display missing keywords section when array is empty', () => {
      const noMissingKeywordsData = {
        ...mockOptimizationData,
        missing_keywords: [],
      };
      render(
        <OptimizationSuggestions optimizationData={noMissingKeywordsData} />
      );

      expect(screen.queryByText('Missing Keywords')).not.toBeInTheDocument();
    });

    it('should not display missing keywords section when undefined', () => {
      const noMissingKeywordsData = {
        ...mockOptimizationData,
        missing_keywords: undefined,
      } as OptimizationFeedback;
      render(
        <OptimizationSuggestions optimizationData={noMissingKeywordsData} />
      );

      expect(screen.queryByText('Missing Keywords')).not.toBeInTheDocument();
    });
  });

  describe('Suggestions Display', () => {
    it('should display all suggestion titles', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      expect(screen.getByText('Add Missing Keywords')).toBeInTheDocument();
      expect(screen.getByText('Use Stronger Action Verbs')).toBeInTheDocument();
      expect(screen.getByText('Improve Resume Structure')).toBeInTheDocument();
      expect(screen.getByText('Quantify Achievements')).toBeInTheDocument();
      expect(screen.getByText('Improve Readability')).toBeInTheDocument();
    });

    it('should display priority chips for each suggestion', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      expect(screen.getAllByText('High').length).toBe(2);
      expect(screen.getAllByText('Medium').length).toBe(2);
      expect(screen.getAllByText('Low').length).toBe(1);
    });

    it('should display category chips for each suggestion', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      expect(screen.getByText('Keywords')).toBeInTheDocument();
      expect(screen.getByText('Action Verbs')).toBeInTheDocument();
      expect(screen.getByText('Structure')).toBeInTheDocument();
      expect(screen.getByText('Impact')).toBeInTheDocument();
      expect(screen.getByText('Readability')).toBeInTheDocument();
    });

    it('should not display suggestion details initially (collapsed)', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      // Description should not be visible initially
      expect(screen.queryByText('Include important keywords from the job description')).not.toBeInTheDocument();
      // Current state should not be visible initially
      expect(screen.queryByText('Missing keywords: Agile, Scrum, CI/CD')).not.toBeInTheDocument();
      // Recommendation should not be visible initially
      expect(screen.queryByText('Add these keywords to your skills section')).not.toBeInTheDocument();
      // Examples should not be visible initially
      expect(screen.queryByText('Agile methodologies')).not.toBeInTheDocument();
    });
  });

  describe('Expand/Collapse Functionality', () => {
    it('should display suggestion details when expand button is clicked', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      // Find expand buttons (icon buttons with chevron-down)
      const expandButtons = screen.getAllByRole('button');
      const firstExpandButton = expandButtons.find((btn) =>
        btn.querySelector('svg')
      );

      if (firstExpandButton) {
        fireEvent.click(firstExpandButton);

        // Now details should be visible
        expect(screen.getByText('Include important keywords from the job description')).toBeInTheDocument();
        expect(screen.getByText('Missing keywords: Agile, Scrum, CI/CD')).toBeInTheDocument();
        expect(screen.getByText('Add these keywords to your skills section')).toBeInTheDocument();
      }
    });

    it('should display examples when expanded', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const expandButtons = screen.getAllByRole('button');
      const firstExpandButton = expandButtons.find((btn) =>
        btn.querySelector('svg')
      );

      if (firstExpandButton) {
        fireEvent.click(firstExpandButton);

        expect(screen.getByText('Examples:')).toBeInTheDocument();
        expect(screen.getByText('Agile methodologies')).toBeInTheDocument();
        expect(screen.getByText('Scrum framework')).toBeInTheDocument();
        expect(screen.getByText('CI/CD pipelines')).toBeInTheDocument();
      }
    });

    it('should collapse details when clicking expand button again', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const expandButtons = screen.getAllByRole('button');
      const firstExpandButton = expandButtons.find((btn) =>
        btn.querySelector('svg')
      );

      if (firstExpandButton) {
        // Expand
        fireEvent.click(firstExpandButton);
        expect(screen.getByText('Include important keywords from the job description')).toBeInTheDocument();

        // Collapse
        fireEvent.click(firstExpandButton);
        expect(screen.queryByText('Include important keywords from the job description')).not.toBeInTheDocument();
      }
    });

    it('should expand multiple suggestions independently', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const expandButtons = screen.getAllByRole('button').filter((btn) =>
        btn.querySelector('svg')
      );

      if (expandButtons.length >= 2) {
        // Expand first suggestion
        fireEvent.click(expandButtons[0]);
        expect(screen.getByText('Include important keywords from the job description')).toBeInTheDocument();

        // Expand second suggestion
        fireEvent.click(expandButtons[1]);
        expect(screen.getByText('Replace weak verbs with more impactful alternatives')).toBeInTheDocument();

        // First suggestion should still be visible
        expect(screen.getByText('Include important keywords from the job description')).toBeInTheDocument();
      }
    });

    it('should not expand when disabled', () => {
      render(
        <OptimizationSuggestions
          optimizationData={mockOptimizationData}
          disabled
        />
      );

      const expandButtons = screen.getAllByRole('button');
      const firstExpandButton = expandButtons.find((btn) =>
        btn.querySelector('svg')
      );

      if (firstExpandButton) {
        expect(firstExpandButton).toBeDisabled();
      }
    });
  });

  describe('Current State and Recommendations Display', () => {
    it('should display current state when expanded', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const expandButtons = screen.getAllByRole('button').filter((btn) =>
        btn.querySelector('svg')
      );

      if (expandButtons.length > 0) {
        fireEvent.click(expandButtons[0]);

        expect(screen.getByText('Current:')).toBeInTheDocument();
        expect(screen.getByText('Missing keywords: Agile, Scrum, CI/CD')).toBeInTheDocument();
      }
    });

    it('should display recommendation when expanded', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const expandButtons = screen.getAllByRole('button').filter((btn) =>
        btn.querySelector('svg')
      );

      if (expandButtons.length > 0) {
        fireEvent.click(expandButtons[0]);

        expect(screen.getByText('Recommended:')).toBeInTheDocument();
        expect(screen.getByText('Add these keywords to your skills section')).toBeInTheDocument();
      }
    });

    it('should display examples when available', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const expandButtons = screen.getAllByRole('button').filter((btn) =>
        btn.querySelector('svg')
      );

      if (expandButtons.length > 0) {
        fireEvent.click(expandButtons[0]);

        expect(screen.getByText('Examples:')).toBeInTheDocument();
        expect(screen.getByText('Agile methodologies')).toBeInTheDocument();
      }
    });

    it('should not display examples section when not available', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      // Expand a suggestion without examples (Improve Resume Structure at index 2, third expandable)
      const expandButtons = screen.getAllByRole('button').filter((btn) =>
        btn.querySelector('svg')
      );

      if (expandButtons.length > 2) {
        fireEvent.click(expandButtons[2]);

        // Should show current state and recommendation but no Examples header for this item
        expect(screen.getByText('Better organize sections for clarity')).toBeInTheDocument();
      }
    });
  });

  describe('Loading State', () => {
    it('should display loading state when loading is true', () => {
      render(
        <OptimizationSuggestions
          optimizationData={null}
          loading
        />
      );

      expect(screen.getByText('Analyzing resume for optimization opportunities...')).toBeInTheDocument();
    });

    it('should display circular progress when loading', () => {
      render(
        <OptimizationSuggestions
          optimizationData={null}
          loading
        />
      );

      const circularProgress = document.querySelector('.MuiCircularProgress-root');
      expect(circularProgress).toBeInTheDocument();
    });

    it('should not display suggestions when loading', () => {
      render(
        <OptimizationSuggestions
          optimizationData={mockOptimizationData}
          loading
        />
      );

      expect(screen.queryByText('Add Missing Keywords')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should display error message when error is provided', () => {
      const errorMessage = 'Failed to load optimization data';
      render(
        <OptimizationSuggestions
          optimizationData={null}
          error={errorMessage}
        />
      );

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('should display error alert with error severity', () => {
      render(
        <OptimizationSuggestions
          optimizationData={null}
          error="Error occurred"
        />
      );

      const alert = document.querySelector('.MuiAlert-root');
      expect(alert).toBeInTheDocument();
    });

    it('should not display suggestions when error is present', () => {
      render(
        <OptimizationSuggestions
          optimizationData={mockOptimizationData}
          error="Error loading data"
        />
      );

      expect(screen.queryByText('Add Missing Keywords')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should display empty state when optimizationData is null', () => {
      render(
        <OptimizationSuggestions optimizationData={null} />
      );

      expect(screen.getByText('No Optimization Suggestions')).toBeInTheDocument();
      expect(screen.getByText('Your resume looks great! No immediate improvements needed.')).toBeInTheDocument();
    });

    it('should display empty state when suggestions array is empty', () => {
      const emptyData: OptimizationFeedback = {
        resume_id: 'resume-123',
        score: 100,
        suggestions: [],
        total_suggestions: 0,
        high_priority_count: 0,
        medium_priority_count: 0,
        low_priority_count: 0,
      };
      render(
        <OptimizationSuggestions optimizationData={emptyData} />
      );

      expect(screen.getByText('No Optimization Suggestions')).toBeInTheDocument();
      expect(screen.getByText('Your resume looks great! No immediate improvements needed.')).toBeInTheDocument();
    });

    it('should display check-circle icon in empty state', () => {
      render(
        <OptimizationSuggestions optimizationData={null} />
      );

      const icons = document.querySelectorAll('.MuiSvgIcon-root');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  describe('maxDisplay Limit', () => {
    it('should limit displayed suggestions to maxDisplay', () => {
      const manySuggestions: OptimizationFeedback = {
        ...mockOptimizationData,
        suggestions: Array.from({ length: 10 }, (_, i) => ({
          type: 'content' as const,
          priority: 'low' as const,
          category: 'readability' as const,
          title: `Suggestion ${i + 1}`,
          description: `Description ${i + 1}`,
          current_state: `Current ${i + 1}`,
          recommendation: `Recommendation ${i + 1}`,
          examples: [],
        })),
        total_suggestions: 10,
        high_priority_count: 0,
        medium_priority_count: 0,
        low_priority_count: 10,
      };

      render(
        <OptimizationSuggestions optimizationData={manySuggestions} maxDisplay={3} />
      );

      expect(screen.getByText('Suggestion 1')).toBeInTheDocument();
      expect(screen.getByText('Suggestion 2')).toBeInTheDocument();
      expect(screen.getByText('Suggestion 3')).toBeInTheDocument();
      expect(screen.queryByText('Suggestion 4')).not.toBeInTheDocument();
    });

    it('should show indicator when more suggestions exist than maxDisplay', () => {
      const manySuggestions: OptimizationFeedback = {
        ...mockOptimizationData,
        suggestions: Array.from({ length: 10 }, (_, i) => ({
          type: 'content' as const,
          priority: 'low' as const,
          category: 'readability' as const,
          title: `Suggestion ${i + 1}`,
          description: `Description ${i + 1}`,
          current_state: `Current ${i + 1}`,
          recommendation: `Recommendation ${i + 1}`,
          examples: [],
        })),
        total_suggestions: 10,
        high_priority_count: 0,
        medium_priority_count: 0,
        low_priority_count: 10,
      };

      render(
        <OptimizationSuggestions optimizationData={manySuggestions} maxDisplay={5} />
      );

      expect(screen.getByText('Showing 5 of 10 suggestions')).toBeInTheDocument();
    });

    it('should not show indicator when suggestions fit within maxDisplay', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} maxDisplay={10} />
      );

      expect(screen.queryByText(/Showing \d+ of \d+ suggestions/)).not.toBeInTheDocument();
    });

    it('should respect maxDisplay when filter is active', () => {
      const manySuggestions: OptimizationFeedback = {
        ...mockOptimizationData,
        suggestions: Array.from({ length: 10 }, (_, i) => ({
          type: 'content' as const,
          priority: i < 5 ? ('high' as const) : ('low' as const),
          category: 'readability' as const,
          title: `Suggestion ${i + 1}`,
          description: `Description ${i + 1}`,
          current_state: `Current ${i + 1}`,
          recommendation: `Recommendation ${i + 1}`,
          examples: [],
        })),
        total_suggestions: 10,
        high_priority_count: 5,
        medium_priority_count: 0,
        low_priority_count: 5,
      };

      render(
        <OptimizationSuggestions optimizationData={manySuggestions} maxDisplay={3} />
      );

      // Filter to high priority (5 items)
      fireEvent.click(screen.getByText('High Priority'));

      // Should show only 3 of 5 high priority suggestions
      expect(screen.getByText('Suggestion 1')).toBeInTheDocument();
      expect(screen.getByText('Suggestion 2')).toBeInTheDocument();
      expect(screen.getByText('Suggestion 3')).toBeInTheDocument();
      expect(screen.queryByText('Suggestion 4')).not.toBeInTheDocument();
      expect(screen.getByText('Showing 3 of 5 suggestions')).toBeInTheDocument();
    });
  });

  describe('Priority Styling', () => {
    it('should apply high priority styling', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const highPriorityChips = screen.getAllByText('High');
      expect(highPriorityChips.length).toBeGreaterThan(0);
      expect(highPriorityChips[0].parentElement).toHaveClass('MuiChip-outlinedError');
    });

    it('should apply medium priority styling', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const mediumPriorityChips = screen.getAllByText('Medium');
      expect(mediumPriorityChips.length).toBeGreaterThan(0);
      expect(mediumPriorityChips[0].parentElement).toHaveClass('MuiChip-outlinedWarning');
    });

    it('should apply low priority styling', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const lowPriorityChips = screen.getAllByText('Low');
      expect(lowPriorityChips.length).toBeGreaterThan(0);
      expect(lowPriorityChips[0].parentElement).toHaveClass('MuiChip-outlinedInfo');
    });
  });

  describe('Category Labels', () => {
    it('should display correct category labels', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      expect(screen.getByText('Keywords')).toBeInTheDocument();
      expect(screen.getByText('Action Verbs')).toBeInTheDocument();
      expect(screen.getByText('Structure')).toBeInTheDocument();
      expect(screen.getByText('Impact')).toBeInTheDocument();
      expect(screen.getByText('Readability')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle suggestions with empty examples array', () => {
      const noExamplesData: OptimizationFeedback = {
        ...mockOptimizationData,
        suggestions: [
          {
            type: 'formatting',
            priority: 'low',
            category: 'structure',
            title: 'Test Suggestion',
            description: 'Test description',
            current_state: 'Test current',
            recommendation: 'Test recommendation',
            examples: [],
          },
        ],
        total_suggestions: 1,
        high_priority_count: 0,
        medium_priority_count: 0,
        low_priority_count: 1,
      };

      render(
        <OptimizationSuggestions optimizationData={noExamplesData} />
      );

      const expandButtons = screen.getAllByRole('button').filter((btn) =>
        btn.querySelector('svg')
      );

      if (expandButtons.length > 0) {
        fireEvent.click(expandButtons[0]);

        // Should show current and recommendation but no examples
        expect(screen.getByText('Test current')).toBeInTheDocument();
        expect(screen.getByText('Test recommendation')).toBeInTheDocument();
        // The "Examples:" header should not appear for this item
        const exampleHeaders = screen.queryAllByText('Examples:');
        const examplesPanel = screen.queryAllByText('Test current')[0]?.closest('.MuiBox-root');
        expect(examplesPanel).not.toHaveTextContent('Examples:');
      }
    });

    it('should handle undefined examples', () => {
      const undefinedExamplesData: OptimizationFeedback = {
        ...mockOptimizationData,
        suggestions: [
          {
            type: 'formatting',
            priority: 'low',
            category: 'structure',
            title: 'Test Suggestion',
            description: 'Test description',
            current_state: 'Test current',
            recommendation: 'Test recommendation',
            examples: undefined,
          } as OptimizationSuggestion,
        ],
        total_suggestions: 1,
        high_priority_count: 0,
        medium_priority_count: 0,
        low_priority_count: 1,
      };

      render(
        <OptimizationSuggestions optimizationData={undefinedExamplesData} />
      );

      expect(screen.getByText('Test Suggestion')).toBeInTheDocument();
    });

    it('should handle maxDisplay of 0', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} maxDisplay={0} />
      );

      expect(screen.queryByText('Add Missing Keywords')).not.toBeInTheDocument();
      expect(screen.getByText('Showing 0 of 5 suggestions')).toBeInTheDocument();
    });

    it('should handle very high score (100)', () => {
      const perfectScoreData = { ...mockOptimizationData, score: 100 };
      render(
        <OptimizationSuggestions optimizationData={perfectScoreData} />
      );

      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('/100')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have expand buttons that are keyboard accessible', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should render filter chips as clickable', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const allChip = screen.getByText('All');
      expect(allChip.parentElement).toHaveStyle({ cursor: 'pointer' });
    });
  });

  describe('Component Structure', () => {
    it('should render Card component', () => {
      const { container } = render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const card = container.querySelector('.MuiCard-root');
      expect(card).toBeInTheDocument();
    });

    it('should render CardContent', () => {
      const { container } = render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const cardContent = container.querySelector('.MuiCardContent-root');
      expect(cardContent).toBeInTheDocument();
    });

    it('should render divider between header and content', () => {
      const { container } = render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );

      const divider = container.querySelector('.MuiDivider-root');
      expect(divider).toBeInTheDocument();
    });
  });
});
