/**
 * Tests for OptimizationSuggestions Component
 *
 * Tests the resume optimization suggestions display including:
 * - Displaying overall optimization score
 * - Showing summary statistics
 * - Priority-based filtering
 * - Missing keywords display
 * - Expandable/collapsible suggestion details
 * - Handling loading, error, and empty states
 * - Respecting maxDisplay limit
 */

import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import OptimizationSuggestions from './OptimizationSuggestions';
import type { OptimizationFeedback } from '@/types/api';

describe('OptimizationSuggestions', () => {
  // Standard mock data for testing
  const createMockData = (overrides: Partial<OptimizationFeedback> = {}): OptimizationFeedback => ({
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
        current_state: 'Using basic verbs like "responsible for"',
        recommendation: 'Use strong action verbs',
        examples: ['Led development of...', 'Implemented...'],
      },
      {
        type: 'formatting',
        priority: 'medium',
        category: 'structure',
        title: 'Improve Resume Structure',
        description: 'Better organize sections',
        current_state: 'Sections not clearly separated',
        recommendation: 'Use clear headings',
        examples: [],
      },
      {
        type: 'content',
        priority: 'low',
        category: 'readability',
        title: 'Improve Readability',
        description: 'Make resume easier to scan',
        current_state: 'Long paragraphs',
        recommendation: 'Use bullet points',
        examples: [],
      },
    ],
    total_suggestions: 4,
    high_priority_count: 2,
    medium_priority_count: 1,
    low_priority_count: 1,
    keywords_found: ['Python', 'JavaScript', 'React'],
    missing_keywords: ['Agile', 'Scrum', 'CI/CD'],
    error: null,
    ...overrides,
  });

  const mockOptimizationData = createMockData();

  // ===========================================
  // BASIC RENDERING TESTS
  // ===========================================
  describe('Basic Rendering', () => {
    it('renders with default title', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      expect(screen.getByText('Resume Optimization Suggestions')).toBeInTheDocument();
    });

    it('renders with custom title', () => {
      render(
        <OptimizationSuggestions
          optimizationData={mockOptimizationData}
          title="Custom Title"
        />
      );
      expect(screen.getByText('Custom Title')).toBeInTheDocument();
    });

    it('displays the score value', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      expect(screen.getByText('72')).toBeInTheDocument();
      expect(screen.getByText('/100')).toBeInTheDocument();
    });

    it('displays total suggestions count', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      expect(screen.getByText('4 suggestions')).toBeInTheDocument();
    });
  });

  // ===========================================
  // SCORE DISPLAY TESTS
  // ===========================================
  describe('Score Display', () => {
    it('displays score 85 correctly', () => {
      render(<OptimizationSuggestions optimizationData={createMockData({ score: 85 })} />);
      expect(screen.getByText('85')).toBeInTheDocument();
    });

    it('displays score 45 correctly', () => {
      render(<OptimizationSuggestions optimizationData={createMockData({ score: 45 })} />);
      expect(screen.getByText('45')).toBeInTheDocument();
    });

    it('displays score 0 correctly', () => {
      render(<OptimizationSuggestions optimizationData={createMockData({ score: 0 })} />);
      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('displays score 100 correctly', () => {
      render(<OptimizationSuggestions optimizationData={createMockData({ score: 100 })} />);
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });

  // ===========================================
  // PRIORITY COUNT TESTS
  // ===========================================
  describe('Priority Count Display', () => {
    it('displays high priority count when > 0', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      expect(screen.getByText('2 high')).toBeInTheDocument();
    });

    it('displays medium priority count when > 0', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      expect(screen.getByText('1 medium')).toBeInTheDocument();
    });

    it('displays low priority count when > 0', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      expect(screen.getByText('1 low')).toBeInTheDocument();
    });

    it('hides high priority count when 0', () => {
      render(
        <OptimizationSuggestions
          optimizationData={createMockData({ high_priority_count: 0 })}
        />
      );
      expect(screen.queryByText('0 high')).not.toBeInTheDocument();
    });
  });

  // ===========================================
  // FILTER TABS TESTS
  // ===========================================
  describe('Filter Tabs', () => {
    it('displays all filter options', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      expect(screen.getByText('All')).toBeInTheDocument();
      expect(screen.getByText('High Priority')).toBeInTheDocument();
      expect(screen.getByText('Medium Priority')).toBeInTheDocument();
      expect(screen.getByText('Low Priority')).toBeInTheDocument();
    });

    it('shows all suggestions by default', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      expect(screen.getByText('Add Missing Keywords')).toBeInTheDocument();
      expect(screen.getByText('Use Stronger Action Verbs')).toBeInTheDocument();
      expect(screen.getByText('Improve Resume Structure')).toBeInTheDocument();
      expect(screen.getByText('Improve Readability')).toBeInTheDocument();
    });

    it('filters to high priority only when clicking High Priority', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      fireEvent.click(screen.getByText('High Priority'));
      expect(screen.getByText('Add Missing Keywords')).toBeInTheDocument();
      expect(screen.getByText('Use Stronger Action Verbs')).toBeInTheDocument();
      expect(screen.queryByText('Improve Resume Structure')).not.toBeInTheDocument();
      expect(screen.queryByText('Improve Readability')).not.toBeInTheDocument();
    });

    it('filters to medium priority only when clicking Medium Priority', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      fireEvent.click(screen.getByText('Medium Priority'));
      expect(screen.queryByText('Add Missing Keywords')).not.toBeInTheDocument();
      expect(screen.getByText('Improve Resume Structure')).toBeInTheDocument();
    });

    it('filters to low priority only when clicking Low Priority', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      fireEvent.click(screen.getByText('Low Priority'));
      expect(screen.queryByText('Add Missing Keywords')).not.toBeInTheDocument();
      expect(screen.getByText('Improve Readability')).toBeInTheDocument();
    });

    it('resets filter when clicking All', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      fireEvent.click(screen.getByText('High Priority'));
      expect(screen.queryByText('Improve Resume Structure')).not.toBeInTheDocument();
      fireEvent.click(screen.getByText('All'));
      expect(screen.getByText('Improve Resume Structure')).toBeInTheDocument();
    });
  });

  // ===========================================
  // MISSING KEYWORDS TESTS
  // ===========================================
  describe('Missing Keywords', () => {
    it('displays missing keywords section when keywords exist', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      expect(screen.getByText('Missing Keywords')).toBeInTheDocument();
      expect(screen.getByText('Agile')).toBeInTheDocument();
      expect(screen.getByText('Scrum')).toBeInTheDocument();
      expect(screen.getByText('CI/CD')).toBeInTheDocument();
    });

    it('hides missing keywords section when empty', () => {
      render(
        <OptimizationSuggestions
          optimizationData={createMockData({ missing_keywords: [] })}
        />
      );
      expect(screen.queryByText('Missing Keywords')).not.toBeInTheDocument();
    });

    it('hides missing keywords section when undefined', () => {
      const data = createMockData();
      delete data.missing_keywords;
      render(<OptimizationSuggestions optimizationData={data} />);
      expect(screen.queryByText('Missing Keywords')).not.toBeInTheDocument();
    });
  });

  // ===========================================
  // SUGGESTIONS DISPLAY TESTS
  // ===========================================
  describe('Suggestions Display', () => {
    it('displays all suggestion titles', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      expect(screen.getByText('Add Missing Keywords')).toBeInTheDocument();
      expect(screen.getByText('Use Stronger Action Verbs')).toBeInTheDocument();
      expect(screen.getByText('Improve Resume Structure')).toBeInTheDocument();
      expect(screen.getByText('Improve Readability')).toBeInTheDocument();
    });

    it('displays priority labels', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      // Each suggestion has a priority chip
      const highLabels = screen.getAllByText('High');
      expect(highLabels.length).toBe(2);
      expect(screen.getByText('Medium')).toBeInTheDocument();
      expect(screen.getByText('Low')).toBeInTheDocument();
    });

    it('displays category labels', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      expect(screen.getByText('Keywords')).toBeInTheDocument();
      expect(screen.getByText('Action Verbs')).toBeInTheDocument();
      expect(screen.getByText('Structure')).toBeInTheDocument();
      expect(screen.getByText('Readability')).toBeInTheDocument();
    });

    it('does not show details initially (collapsed)', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      // Description should not be visible initially
      expect(
        screen.queryByText('Include important keywords from the job description')
      ).not.toBeInTheDocument();
    });
  });

  // ===========================================
  // EXPAND/COLLAPSE TESTS
  // ===========================================
  describe('Expand/Collapse Functionality', () => {
    it('shows details when expand button is clicked', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      // Find the first expand button (icon button)
      const buttons = screen.getAllByRole('button');
      const expandButton = buttons.find((btn) => btn.querySelector('svg'));

      if (expandButton) {
        fireEvent.click(expandButton);
        expect(
          screen.getByText('Include important keywords from the job description')
        ).toBeInTheDocument();
        expect(screen.getByText('Current:')).toBeInTheDocument();
        expect(screen.getByText('Recommended:')).toBeInTheDocument();
      }
    });

    it('shows examples when expanded', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      const buttons = screen.getAllByRole('button');
      const expandButton = buttons.find((btn) => btn.querySelector('svg'));

      if (expandButton) {
        fireEvent.click(expandButton);
        expect(screen.getByText('Examples:')).toBeInTheDocument();
        expect(screen.getByText('Agile methodologies')).toBeInTheDocument();
      }
    });

    it('hides details when collapse button is clicked', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      const buttons = screen.getAllByRole('button');
      const expandButton = buttons.find((btn) => btn.querySelector('svg'));

      if (expandButton) {
        // Expand
        fireEvent.click(expandButton);
        expect(
          screen.getByText('Include important keywords from the job description')
        ).toBeInTheDocument();

        // Collapse
        fireEvent.click(expandButton);
        expect(
          screen.queryByText('Include important keywords from the job description')
        ).not.toBeInTheDocument();
      }
    });

    it('expands multiple suggestions independently', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} />);
      const buttons = screen.getAllByRole('button').filter((btn) => btn.querySelector('svg'));

      if (buttons.length >= 2) {
        fireEvent.click(buttons[0]);
        fireEvent.click(buttons[1]);
        expect(
          screen.getByText('Include important keywords from the job description')
        ).toBeInTheDocument();
        expect(
          screen.getByText('Replace weak verbs with more impactful alternatives')
        ).toBeInTheDocument();
      }
    });
  });

  // ===========================================
  // LOADING STATE TESTS
  // ===========================================
  describe('Loading State', () => {
    it('displays loading message when loading', () => {
      render(<OptimizationSuggestions optimizationData={null} loading />);
      expect(
        screen.getByText('Analyzing resume for optimization opportunities...')
      ).toBeInTheDocument();
    });

    it('displays circular progress when loading', () => {
      render(<OptimizationSuggestions optimizationData={null} loading />);
      const progress = document.querySelector('.MuiCircularProgress-root');
      expect(progress).toBeInTheDocument();
    });

    it('hides suggestions when loading', () => {
      render(<OptimizationSuggestions optimizationData={mockOptimizationData} loading />);
      expect(screen.queryByText('Add Missing Keywords')).not.toBeInTheDocument();
    });
  });

  // ===========================================
  // ERROR STATE TESTS
  // ===========================================
  describe('Error State', () => {
    it('displays error message', () => {
      render(
        <OptimizationSuggestions optimizationData={null} error="Test error message" />
      );
      expect(screen.getByText('Test error message')).toBeInTheDocument();
    });

    it('displays alert component for error', () => {
      render(<OptimizationSuggestions optimizationData={null} error="Error" />);
      const alert = document.querySelector('.MuiAlert-root');
      expect(alert).toBeInTheDocument();
    });

    it('hides suggestions when error is present', () => {
      render(
        <OptimizationSuggestions
          optimizationData={mockOptimizationData}
          error="Error"
        />
      );
      expect(screen.queryByText('Add Missing Keywords')).not.toBeInTheDocument();
    });
  });

  // ===========================================
  // EMPTY STATE TESTS
  // ===========================================
  describe('Empty State', () => {
    it('displays empty state when data is null', () => {
      render(<OptimizationSuggestions optimizationData={null} />);
      expect(screen.getByText('No Optimization Suggestions')).toBeInTheDocument();
      expect(
        screen.getByText('Your resume looks great! No immediate improvements needed.')
      ).toBeInTheDocument();
    });

    it('displays empty state when suggestions array is empty', () => {
      render(
        <OptimizationSuggestions
          optimizationData={createMockData({
            suggestions: [],
            total_suggestions: 0,
            high_priority_count: 0,
            medium_priority_count: 0,
            low_priority_count: 0,
          })}
        />
      );
      expect(screen.getByText('No Optimization Suggestions')).toBeInTheDocument();
    });
  });

  // ===========================================
  // MAX DISPLAY LIMIT TESTS
  // ===========================================
  describe('Max Display Limit', () => {
    it('limits displayed suggestions to maxDisplay', () => {
      const manySuggestions = Array.from({ length: 10 }, (_, i) => ({
        type: 'content' as const,
        priority: 'low' as const,
        category: 'readability' as const,
        title: `Suggestion ${i + 1}`,
        description: `Description ${i + 1}`,
        current_state: `Current ${i + 1}`,
        recommendation: `Recommendation ${i + 1}`,
        examples: [],
      }));

      render(
        <OptimizationSuggestions
          optimizationData={createMockData({
            suggestions: manySuggestions,
            total_suggestions: 10,
            low_priority_count: 10,
          })}
          maxDisplay={3}
        />
      );

      expect(screen.getByText('Suggestion 1')).toBeInTheDocument();
      expect(screen.getByText('Suggestion 2')).toBeInTheDocument();
      expect(screen.getByText('Suggestion 3')).toBeInTheDocument();
      expect(screen.queryByText('Suggestion 4')).not.toBeInTheDocument();
    });

    it('shows indicator when more suggestions exist', () => {
      const manySuggestions = Array.from({ length: 10 }, (_, i) => ({
        type: 'content' as const,
        priority: 'low' as const,
        category: 'readability' as const,
        title: `Suggestion ${i + 1}`,
        description: `Description ${i + 1}`,
        current_state: `Current ${i + 1}`,
        recommendation: `Recommendation ${i + 1}`,
        examples: [],
      }));

      render(
        <OptimizationSuggestions
          optimizationData={createMockData({
            suggestions: manySuggestions,
            total_suggestions: 10,
            low_priority_count: 10,
          })}
          maxDisplay={5}
        />
      );

      expect(screen.getByText('Showing 5 of 10 suggestions')).toBeInTheDocument();
    });

    it('hides indicator when suggestions fit within limit', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} maxDisplay={10} />
      );
      expect(
        screen.queryByText(/Showing \d+ of \d+ suggestions/)
      ).not.toBeInTheDocument();
    });
  });

  // ===========================================
  // COMPONENT STRUCTURE TESTS
  // ===========================================
  describe('Component Structure', () => {
    it('renders in a Card', () => {
      const { container } = render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );
      const card = container.querySelector('.MuiCard-root');
      expect(card).toBeInTheDocument();
    });

    it('renders CardContent', () => {
      const { container } = render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );
      const cardContent = container.querySelector('.MuiCardContent-root');
      expect(cardContent).toBeInTheDocument();
    });

    it('renders Divider', () => {
      const { container } = render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} />
      );
      const divider = container.querySelector('.MuiDivider-root');
      expect(divider).toBeInTheDocument();
    });
  });

  // ===========================================
  // CATEGORY LABEL TESTS
  // ===========================================
  describe('Category Labels', () => {
    it('displays all category types correctly', () => {
      const allCategoriesData = createMockData({
        suggestions: [
          {
            type: 'keyword',
            priority: 'high',
            category: 'keywords',
            title: 'Test Keywords',
            description: 'Test',
            current_state: 'Test',
            recommendation: 'Test',
            examples: [],
          },
          {
            type: 'formatting',
            priority: 'medium',
            category: 'structure',
            title: 'Test Structure',
            description: 'Test',
            current_state: 'Test',
            recommendation: 'Test',
            examples: [],
          },
          {
            type: 'content',
            priority: 'low',
            category: 'impact',
            title: 'Test Impact',
            description: 'Test',
            current_state: 'Test',
            recommendation: 'Test',
            examples: [],
          },
        ],
        total_suggestions: 3,
        high_priority_count: 1,
        medium_priority_count: 1,
        low_priority_count: 1,
        missing_keywords: [],
      });

      render(<OptimizationSuggestions optimizationData={allCategoriesData} />);

      expect(screen.getByText('Keywords')).toBeInTheDocument();
      expect(screen.getByText('Structure')).toBeInTheDocument();
      expect(screen.getByText('Impact')).toBeInTheDocument();
    });
  });

  // ===========================================
  // DISABLED STATE TESTS
  // ===========================================
  describe('Disabled State', () => {
    it('disables expand buttons when disabled prop is true', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} disabled />
      );
      const buttons = screen.getAllByRole('button');
      const iconButton = buttons.find((btn) => btn.querySelector('svg'));

      if (iconButton) {
        expect(iconButton).toBeDisabled();
      }
    });
  });

  // ===========================================
  // EDGE CASE TESTS
  // ===========================================
  describe('Edge Cases', () => {
    it('handles suggestions without examples', () => {
      const noExamplesData = createMockData({
        suggestions: [
          {
            type: 'formatting',
            priority: 'low',
            category: 'structure',
            title: 'No Examples Suggestion',
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
        missing_keywords: [],
      });

      render(<OptimizationSuggestions optimizationData={noExamplesData} />);
      const buttons = screen.getAllByRole('button');
      const expandButton = buttons.find((btn) => btn.querySelector('svg'));

      if (expandButton) {
        fireEvent.click(expandButton);
        // Should show current and recommendation but no Examples section
        expect(screen.getByText('Test current')).toBeInTheDocument();
        expect(screen.getByText('Test recommendation')).toBeInTheDocument();
      }
    });

    it('handles maxDisplay of 0', () => {
      render(
        <OptimizationSuggestions optimizationData={mockOptimizationData} maxDisplay={0} />
      );
      expect(screen.queryByText('Add Missing Keywords')).not.toBeInTheDocument();
      expect(screen.getByText('Showing 0 of 4 suggestions')).toBeInTheDocument();
    });
  });
});
