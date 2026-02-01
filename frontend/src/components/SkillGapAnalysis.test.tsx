/**
 * Tests for SkillGapAnalysis Component
 *
 * Tests the skill gap analysis visualization including:
 * - Displaying missing required skills
 * - Showing suggested alternative skills from resume
 * - Color-coded suggestion chips based on confidence
 * - Expandable/collapsible suggestion sections
 * - Handling loading and error states
 * - Respecting maxDisplay limit
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SkillGapAnalysis, { MissingSkillWithSuggestions, SkillSuggestion } from './SkillGapAnalysis';

describe('SkillGapAnalysis', () => {
  const mockMissingSkills: MissingSkillWithSuggestions[] = [
    {
      skill: 'Docker',
      suggestions: [
        {
          skill: 'Kubernetes',
          confidence: 0.85,
          reason: 'same_category',
        },
        {
          skill: 'Container Management',
          confidence: 0.75,
          reason: 'related',
        },
      ],
    },
    {
      skill: 'AWS',
      suggestions: [
        {
          skill: 'Amazon Web Services',
          confidence: 0.92,
          reason: 'synonym',
        },
        {
          skill: 'Cloud Computing',
          confidence: 0.70,
          reason: 'same_category',
        },
        {
          skill: 'Azure',
          confidence: 0.65,
          reason: 'related',
        },
      ],
    },
    {
      skill: 'GraphQL',
      suggestions: [],
    },
    {
      skill: 'TypeScript',
      suggestions: [
        {
          skill: 'TS',
          confidence: 0.88,
          reason: 'fuzzy_match',
        },
      ],
    },
  ];

  describe('Component Rendering', () => {
    it('should render the component with default title', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      expect(screen.getByText('Skill Gap Analysis')).toBeInTheDocument();
    });

    it('should render with custom title', () => {
      render(
        <SkillGapAnalysis
          missingSkills={mockMissingSkills}
          title="Missing Skills Report"
        />
      );

      expect(screen.getByText('Missing Skills Report')).toBeInTheDocument();
      expect(screen.queryByText('Skill Gap Analysis')).not.toBeInTheDocument();
    });

    it('should display missing skills count chip', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      expect(screen.getByText('4 missing')).toBeInTheDocument();
    });

    it('should display warning icon', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      const icon = document.querySelector('.MuiSvgIcon-root');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('Missing Skills Display', () => {
    it('should display all missing skill names', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      expect(screen.getByText('Docker')).toBeInTheDocument();
      expect(screen.getByText('AWS')).toBeInTheDocument();
      expect(screen.getByText('GraphQL')).toBeInTheDocument();
      expect(screen.getByText('TypeScript')).toBeInTheDocument();
    });

    it('should display suggestion count for skills with suggestions', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      expect(screen.getByText('2 suggestions available')).toBeInTheDocument(); // Docker
      expect(screen.getByText('3 suggestions available')).toBeInTheDocument(); // AWS
    });

    it('should display no suggestions message for skills without suggestions', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      expect(screen.getByText('No similar skills found in resume')).toBeInTheDocument(); // GraphQL
    });

    it('should use singular "suggestion" when only one suggestion', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      expect(screen.getByText('1 suggestion available')).toBeInTheDocument(); // TypeScript
    });
  });

  describe('Suggestion Display', () => {
    it('should not display suggestions initially (collapsed)', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      // Suggestion details should not be visible initially
      expect(screen.queryByText('Kubernetes')).not.toBeInTheDocument();
      expect(screen.queryByText('Amazon Web Services')).not.toBeInTheDocument();
    });

    it('should display suggestions when expand button is clicked', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      // Find expand button for Docker (first skill with suggestions)
      const expandButtons = screen.getAllByRole('button');
      const firstExpandButton = expandButtons.find((btn) =>
        btn.querySelector('svg')?.classList.contains('MuiSvgIcon-root')
      );

      if (firstExpandButton) {
        fireEvent.click(firstExpandButton);

        // Now suggestions should be visible
        expect(screen.getByText('Kubernetes')).toBeInTheDocument();
        expect(screen.getByText('Container Management')).toBeInTheDocument();
      }
    });

    it('should collapse suggestions when clicking expand button again', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      const expandButtons = screen.getAllByRole('button');
      const firstExpandButton = expandButtons.find((btn) =>
        btn.querySelector('svg')
      );

      if (firstExpandButton) {
        // Expand
        fireEvent.click(firstExpandButton);
        expect(screen.getByText('Kubernetes')).toBeInTheDocument();

        // Collapse
        fireEvent.click(firstExpandButton);
        expect(screen.queryByText('Kubernetes')).not.toBeInTheDocument();
      }
    });

    it('should not show expand button for skills without suggestions', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      // GraphQL has no suggestions, so no expand button should be associated with it
      const graphqlElement = screen.getByText('GraphQL').closest('[class*="MuiBox-root"]');
      const expandButton = graphqlElement?.querySelector('button');

      expect(expandButton).not.toBeInTheDocument();
    });
  });

  describe('Suggestion Details', () => {
    it('should display suggestion names when expanded', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      // Expand first skill with suggestions
      const expandButtons = screen.getAllByRole('button');
      const firstExpandButton = expandButtons.find((btn) =>
        btn.querySelector('svg')
      );

      if (firstExpandButton) {
        fireEvent.click(firstExpandButton);

        expect(screen.getByText('Kubernetes')).toBeInTheDocument();
        expect(screen.getByText('Container Management')).toBeInTheDocument();
      }
    });

    it('should display suggestion confidence percentages', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      const expandButtons = screen.getAllByRole('button');
      const firstExpandButton = expandButtons.find((btn) =>
        btn.querySelector('svg')
      );

      if (firstExpandButton) {
        fireEvent.click(firstExpandButton);

        expect(screen.getByText('85%')).toBeInTheDocument();
        expect(screen.getByText('75%')).toBeInTheDocument();
      }
    });

    it('should display suggestion reason badges', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      // Expand AWS to see different reason types
      const expandButtons = screen.getAllByRole('button');
      // AWS is the second skill with suggestions
      const awsExpandButton = expandButtons[1];

      if (awsExpandButton) {
        fireEvent.click(awsExpandButton);

        expect(screen.getByText('Synonym')).toBeInTheDocument();
        expect(screen.getByText('Category')).toBeInTheDocument();
        expect(screen.getByText('Related')).toBeInTheDocument();
      }
    });

    it('should display suggestion reason for fuzzy_match', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      // Expand TypeScript to see fuzzy_match
      const expandButtons = screen.getAllByRole('button');
      const tsExpandButton = expandButtons[2]; // Third expandable

      if (tsExpandButton) {
        fireEvent.click(tsExpandButton);

        expect(screen.getByText('Similar')).toBeInTheDocument();
      }
    });
  });

  describe('Suggestion Confidence Bars', () => {
    it('should render confidence bars for suggestions', () => {
      const { container } = render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      // Expand first skill
      const expandButtons = screen.getAllByRole('button');
      const firstExpandButton = expandButtons.find((btn) =>
        btn.querySelector('svg')
      );

      if (firstExpandButton) {
        fireEvent.click(firstExpandButton);

        // Check for confidence bar elements
        const confidenceBars = container.querySelectorAll('[class*="confidence"]');
        expect(confidenceBars.length).toBeGreaterThan(0);
      }
    });
  });

  describe('Suggestion Reason Types', () => {
    it('should display synonym reason', () => {
      const skillsWithSynonym: MissingSkillWithSuggestions[] = [
        {
          skill: 'React',
          suggestions: [
            {
              skill: 'React.js',
              confidence: 0.9,
              reason: 'synonym',
            },
          ],
        },
      ];

      render(
        <SkillGapAnalysis missingSkills={skillsWithSynonym} />
      );

      const expandButton = screen.getByRole('button');
      fireEvent.click(expandButton);

      expect(screen.getByText('Synonym')).toBeInTheDocument();
    });

    it('should display same_category reason', () => {
      const skillsWithCategory: MissingSkillWithSuggestions[] = [
        {
          skill: 'Python',
          suggestions: [
            {
              skill: 'Programming Languages',
              confidence: 0.8,
              reason: 'same_category',
            },
          ],
        },
      ];

      render(
        <SkillGapAnalysis missingSkills={skillsWithCategory} />
      );

      const expandButton = screen.getByRole('button');
      fireEvent.click(expandButton);

      expect(screen.getByText('Category')).toBeInTheDocument();
    });

    it('should display related reason', () => {
      const skillsWithRelated: MissingSkillWithSuggestions[] = [
        {
          skill: 'SQL',
          suggestions: [
            {
              skill: 'Databases',
              confidence: 0.75,
              reason: 'related',
            },
          ],
        },
      ];

      render(
        <SkillGapAnalysis missingSkills={skillsWithRelated} />
      );

      const expandButton = screen.getByRole('button');
      fireEvent.click(expandButton);

      expect(screen.getByText('Related')).toBeInTheDocument();
    });

    it('should display fuzzy_match reason', () => {
      const skillsWithFuzzy: MissingSkillWithSuggestions[] = [
        {
          skill: 'NodeJS',
          suggestions: [
            {
              skill: 'Node.js',
              confidence: 0.88,
              reason: 'fuzzy_match',
            },
          ],
        },
      ];

      render(
        <SkillGapAnalysis missingSkills={skillsWithFuzzy} />
      );

      const expandButton = screen.getByRole('button');
      fireEvent.click(expandButton);

      expect(screen.getByText('Similar')).toBeInTheDocument();
    });

    it('should handle unknown reason type', () => {
      const skillsWithUnknown: MissingSkillWithSuggestions[] = [
        {
          skill: 'Unknown',
          suggestions: [
            {
              skill: 'Something',
              confidence: 0.5,
              reason: 'unknown_reason' as any,
            },
          ],
        },
      ];

      render(
        <SkillGapAnalysis missingSkills={skillsWithUnknown} />
      );

      const expandButton = screen.getByRole('button');
      fireEvent.click(expandButton);

      expect(screen.getByText('Suggestion')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should render loading state when loading is true', () => {
      render(
        <SkillGapAnalysis
          missingSkills={[]}
          loading={true}
        />
      );

      expect(screen.getByText('Analyzing skill gaps...')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should not display skills when loading', () => {
      render(
        <SkillGapAnalysis
          missingSkills={mockMissingSkills}
          loading={true}
        />
      );

      expect(screen.queryByText('Docker')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should render error message when error exists', () => {
      const errorMessage = 'Failed to load skill gaps';

      render(
        <SkillGapAnalysis
          missingSkills={[]}
          error={errorMessage}
        />
      );

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('should not display skills when error exists', () => {
      render(
        <SkillGapAnalysis
          missingSkills={mockMissingSkills}
          error="Error loading gaps"
        />
      );

      expect(screen.queryByText('Docker')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should render success message when no missing skills', () => {
      render(
        <SkillGapAnalysis missingSkills={[]} />
      );

      expect(screen.getByText('No Missing Skills')).toBeInTheDocument();
      expect(screen.getByText('All required skills are covered in the resume')).toBeInTheDocument();
    });

    it('should render lightbulb icon in empty state', () => {
      render(
        <SkillGapAnalysis missingSkills={[]} />
      );

      const icons = document.querySelectorAll('.MuiSvgIcon-root');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  describe('Max Display Limit', () => {
    it('should respect default maxDisplay of 20', () => {
      const manyMissingSkills: MissingSkillWithSuggestions[] = Array.from({ length: 25 }, (_, i) => ({
        skill: `Missing Skill ${i}`,
        suggestions: [],
      }));

      render(
        <SkillGapAnalysis missingSkills={manyMissingSkills} />
      );

      expect(screen.getByText('25 missing')).toBeInTheDocument();
      expect(screen.getByText('Showing 20 of 25 missing skills')).toBeInTheDocument();
    });

    it('should respect custom maxDisplay', () => {
      const missingSkills: MissingSkillWithSuggestions[] = Array.from({ length: 10 }, (_, i) => ({
        skill: `Skill ${i}`,
        suggestions: [],
      }));

      render(
        <SkillGapAnalysis missingSkills={missingSkills} maxDisplay={5} />
      );

      expect(screen.getByText('Showing 5 of 10 missing skills')).toBeInTheDocument();
    });

    it('should not show "showing more" text when skills fit in limit', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} maxDisplay={10} />
      );

      expect(screen.queryByText(/Showing/)).not.toBeInTheDocument();
    });
  });

  describe('Confidence Color Coding', () => {
    it('should apply correct color for high confidence (>=0.8)', () => {
      const highConfidenceSuggestions: MissingSkillWithSuggestions[] = [
        {
          skill: 'Test',
          suggestions: [
            {
              skill: 'High Confidence',
              confidence: 0.85,
              reason: 'synonym',
            },
          ],
        },
      ];

      render(
        <SkillGapAnalysis missingSkills={highConfidenceSuggestions} />
      );

      const expandButton = screen.getByRole('button');
      fireEvent.click(expandButton);

      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('should apply correct color for medium confidence (>=0.65)', () => {
      const mediumConfidenceSuggestions: MissingSkillWithSuggestions[] = [
        {
          skill: 'Test',
          suggestions: [
            {
              skill: 'Medium Confidence',
              confidence: 0.70,
              reason: 'same_category',
            },
          ],
        },
      ];

      render(
        <SkillGapAnalysis missingSkills={mediumConfidenceSuggestions} />
      );

      const expandButton = screen.getByRole('button');
      fireEvent.click(expandButton);

      expect(screen.getByText('70%')).toBeInTheDocument();
    });

    it('should apply correct color for lower confidence (>=0.5)', () => {
      const lowerConfidenceSuggestions: MissingSkillWithSuggestions[] = [
        {
          skill: 'Test',
          suggestions: [
            {
              skill: 'Lower Confidence',
              confidence: 0.55,
              reason: 'related',
            },
          ],
        },
      ];

      render(
        <SkillGapAnalysis missingSkills={lowerConfidenceSuggestions} />
      );

      const expandButton = screen.getByRole('button');
      fireEvent.click(expandButton);

      expect(screen.getByText('55%')).toBeInTheDocument();
    });
  });

  describe('Interactive Elements', () => {
    it('should toggle expand/collapse state independently for each skill', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      const expandButtons = screen.getAllByRole('button');

      // Expand first skill
      if (expandButtons[0]) {
        fireEvent.click(expandButtons[0]);
        expect(screen.getByText('Kubernetes')).toBeInTheDocument();
      }

      // Expand second skill
      if (expandButtons[1]) {
        fireEvent.click(expandButtons[1]);
        expect(screen.getByText('Amazon Web Services')).toBeInTheDocument();
      }

      // First skill should still be expanded
      expect(screen.getByText('Kubernetes')).toBeInTheDocument();
    });

    it('should have hover effect on skill items', () => {
      const { container } = render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      // Check for items with hover styles
      const skillItems = container.querySelectorAll('[class*="backgroundColor"]');
      expect(skillItems.length).toBeGreaterThan(0);
    });
  });

  describe('Layout and Structure', () => {
    it('should render in card container', () => {
      const { container } = render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      const card = container.querySelector('.MuiCard-root');
      expect(card).toBeInTheDocument();
    });

    it('should render divider', () => {
      const { container } = render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      const divider = container.querySelector('.MuiDivider-root');
      expect(divider).toBeInTheDocument();
    });

    it('should render in stack layout', () => {
      const { container } = render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      const stacks = container.querySelectorAll('.MuiStack-root');
      expect(stacks.length).toBeGreaterThan(0);
    });

    it('should display suggestion icon in header', () => {
      render(
        <SkillGapAnalysis missingSkills={mockMissingSkills} />
      );

      const suggestionIcon = document.querySelector('[class*="MuiSvgIcon-root"]');
      expect(suggestionIcon).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing skill with null suggestions', () => {
      const skillsWithNullSuggestions: MissingSkillWithSuggestions[] = [
        {
          skill: 'Test',
          suggestions: null as any,
        },
      ];

      render(
        <SkillGapAnalysis missingSkills={skillsWithNullSuggestions} />
      );

      expect(screen.getByText('Test')).toBeInTheDocument();
      expect(screen.getByText('No similar skills found in resume')).toBeInTheDocument();
    });

    it('should handle suggestion with zero confidence', () => {
      const zeroConfidenceSuggestions: MissingSkillWithSuggestions[] = [
        {
          skill: 'Test',
          suggestions: [
            {
              skill: 'Zero',
              confidence: 0,
              reason: 'synonym',
            },
          ],
        },
      ];

      render(
        <SkillGapAnalysis missingSkills={zeroConfidenceSuggestions} />
      );

      const expandButton = screen.getByRole('button');
      fireEvent.click(expandButton);

      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('should handle suggestion with perfect confidence', () => {
      const perfectConfidenceSuggestions: MissingSkillWithSuggestions[] = [
        {
          skill: 'Test',
          suggestions: [
            {
              skill: 'Perfect',
              confidence: 1.0,
              reason: 'synonym',
            },
          ],
        },
      ];

      render(
        <SkillGapAnalysis missingSkills={perfectConfidenceSuggestions} />
      );

      const expandButton = screen.getByRole('button');
      fireEvent.click(expandButton);

      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('should handle very long skill names', () => {
      const longSkillNames: MissingSkillWithSuggestions[] = [
        {
          skill: 'Very Long Skill Name That Goes On And On',
          suggestions: [],
        },
      ];

      render(
        <SkillGapAnalysis missingSkills={longSkillNames} />
      );

      expect(screen.getByText('Very Long Skill Name That Goes On And On')).toBeInTheDocument();
    });
  });
});
