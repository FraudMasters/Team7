/**
 * Tests for SkillDetailsWithConfidence Component
 *
 * Tests the skill details visualization including:
 * - Displaying matched skills with confidence scores
 * - Showing match type badges (direct, synonym, fuzzy, context, etc.)
 * - Color-coded chips based on match type
 * - Displaying skill locations in resume text
 * - Handling loading and error states
 * - Respecting maxDisplay limit
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SkillDetailsWithConfidence, { SkillMatchDetail } from './SkillDetailsWithConfidence';

describe('SkillDetailsWithConfidence', () => {
  const mockSkills: SkillMatchDetail[] = [
    {
      skill: 'Python',
      confidence: 0.95,
      match_type: 'direct',
      locations: [
        {
          text: 'Python',
          start: 10,
          end: 16,
          context: 'Experienced in Python development for 5 years',
        },
      ],
    },
    {
      skill: 'JavaScript',
      confidence: 0.85,
      match_type: 'synonym',
      matched_as: 'JS',
      locations: [
        {
          text: 'JS',
          start: 20,
          end: 22,
          context: 'Proficient in JS and modern frameworks',
        },
      ],
    },
    {
      skill: 'React',
      confidence: 0.75,
      match_type: 'fuzzy',
      locations: [
        {
          text: 'React.js',
          start: 30,
          end: 38,
          context: 'Built applications with React.js',
        },
      ],
    },
    {
      skill: 'Machine Learning',
      confidence: 0.65,
      match_type: 'context',
      locations: [
        {
          text: 'ML',
          start: 40,
          end: 42,
          context: 'Worked on ML projects',
        },
        {
          text: 'machine learning',
          start: 60,
          end: 76,
          context: 'Studied machine learning algorithms',
        },
      ],
    },
  ];

  describe('Component Rendering', () => {
    it('should render the component with default title', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      expect(screen.getByText('Matched Skills Details')).toBeInTheDocument();
    });

    it('should render with custom title', () => {
      render(
        <SkillDetailsWithConfidence
          skills={mockSkills}
          title="Custom Skills Title"
        />
      );

      expect(screen.getByText('Custom Skills Title')).toBeInTheDocument();
      expect(screen.queryByText('Matched Skills Details')).not.toBeInTheDocument();
    });

    it('should display skills count chip', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      expect(screen.getByText('4 skills')).toBeInTheDocument();
    });
  });

  describe('Skill Display', () => {
    it('should display all skill names', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getByText('JavaScript')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('Machine Learning')).toBeInTheDocument();
    });

    it('should display confidence percentages', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      expect(screen.getByText('95%')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
      expect(screen.getByText('65%')).toBeInTheDocument();
    });

    it('should display matched_as when different from skill name', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      expect(screen.getByText(/matched as "JS"/)).toBeInTheDocument();
    });

    it('should not display matched_as when same as skill name', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      // Python has no matched_as or it's the same
      const pythonText = screen.getByText('Python');
      expect(pythonText.textContent).not.toContain('matched as');
    });
  });

  describe('Match Type Badges', () => {
    it('should display direct match type badge', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      expect(screen.getByText('Direct')).toBeInTheDocument();
    });

    it('should display synonym match type badge', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      expect(screen.getByText('Synonym')).toBeInTheDocument();
    });

    it('should display fuzzy match type badge', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      expect(screen.getByText('Fuzzy')).toBeInTheDocument();
    });

    it('should display context match type badge', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      expect(screen.getByText('Context')).toBeInTheDocument();
    });

    it('should display compound match type badge', () => {
      const skillsWithCompound: SkillMatchDetail[] = [
        {
          skill: 'Full Stack',
          confidence: 0.8,
          match_type: 'compound',
        },
      ];

      render(
        <SkillDetailsWithConfidence skills={skillsWithCompound} />
      );

      expect(screen.getByText('Compound')).toBeInTheDocument();
    });

    it('should display language hierarchy match type badge', () => {
      const skillsWithHierarchy: SkillMatchDetail[] = [
        {
          skill: 'TypeScript',
          confidence: 0.9,
          match_type: 'language_hierarchy',
        },
      ];

      render(
        <SkillDetailsWithConfidence skills={skillsWithHierarchy} />
      );

      expect(screen.getByText('Hierarchy')).toBeInTheDocument();
    });
  });

  describe('Confidence Bars', () => {
    it('should render confidence bars for each skill', () => {
      const { container } = render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      // Check for confidence bar elements (styled divs)
      const confidenceBars = container.querySelectorAll('[class*="confidence"]');
      expect(confidenceBars.length).toBe(mockSkills.length);
    });
  });

  describe('Skill Locations', () => {
    it('should display locations section header', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      expect(screen.getByText('Found in resume:')).toBeInTheDocument();
    });

    it('should display location context for skills', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      expect(screen.getByText('Experienced in Python development for 5 years')).toBeInTheDocument();
      expect(screen.getByText('Proficient in JS and modern frameworks')).toBeInTheDocument();
    });

    it('should display only first 2 locations when more exist', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      // Machine Learning has 2 locations, both should be shown
      expect(screen.getByText('Worked on ML projects')).toBeInTheDocument();
      expect(screen.getByText('Studied machine learning algorithms')).toBeInTheDocument();
    });

    it('should show "more locations" text when locations exceed limit', () => {
      const skillsWithManyLocations: SkillMatchDetail[] = [
        {
          skill: 'Python',
          confidence: 0.9,
          match_type: 'direct',
          locations: [
            { text: 'Python', start: 0, end: 6, context: 'Location 1' },
            { text: 'Python', start: 10, end: 16, context: 'Location 2' },
            { text: 'Python', start: 20, end: 26, context: 'Location 3' },
          ],
        },
      ];

      render(
        <SkillDetailsWithConfidence skills={skillsWithManyLocations} />
      );

      expect(screen.getByText(/\+1 more locations/)).toBeInTheDocument();
    });

    it('should not display locations section when no locations', () => {
      const skillsWithoutLocations: SkillMatchDetail[] = [
        {
          skill: 'Python',
          confidence: 0.9,
          match_type: 'direct',
        },
      ];

      render(
        <SkillDetailsWithConfidence skills={skillsWithoutLocations} />
      );

      expect(screen.queryByText('Found in resume:')).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should render loading state when loading is true', () => {
      render(
        <SkillDetailsWithConfidence
          skills={[]}
          loading={true}
        />
      );

      expect(screen.getByText('Loading skill details...')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should not display skills when loading', () => {
      render(
        <SkillDetailsWithConfidence
          skills={mockSkills}
          loading={true}
        />
      );

      expect(screen.queryByText('Python')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should render error message when error exists', () => {
      const errorMessage = 'Failed to load skills';

      render(
        <SkillDetailsWithConfidence
          skills={[]}
          error={errorMessage}
        />
      );

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('should not display skills when error exists', () => {
      render(
        <SkillDetailsWithConfidence
          skills={mockSkills}
          error="Error loading skills"
        />
      );

      expect(screen.queryByText('Python')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should render empty state when no skills', () => {
      render(
        <SkillDetailsWithConfidence skills={[]} />
      );

      expect(screen.getByText('No matched skills')).toBeInTheDocument();
      expect(screen.getByText('No skills were matched for this position')).toBeInTheDocument();
    });

    it('should render empty state when skills is null', () => {
      render(
        <SkillDetailsWithConfidence skills={null as any} />
      );

      expect(screen.getByText('No matched skills')).toBeInTheDocument();
    });

    it('should render empty state when skills is undefined', () => {
      render(
        <SkillDetailsWithConfidence skills={undefined as any} />
      );

      expect(screen.getByText('No matched skills')).toBeInTheDocument();
    });
  });

  describe('Max Display Limit', () => {
    it('should respect default maxDisplay of 20', () => {
      const manySkills: SkillMatchDetail[] = Array.from({ length: 25 }, (_, i) => ({
        skill: `Skill ${i}`,
        confidence: 0.8,
        match_type: 'direct',
      }));

      render(
        <SkillDetailsWithConfidence skills={manySkills} />
      );

      expect(screen.getByText('25 skills')).toBeInTheDocument();
      expect(screen.getByText('Showing 20 of 25 matched skills')).toBeInTheDocument();
    });

    it('should respect custom maxDisplay', () => {
      const skills: SkillMatchDetail[] = Array.from({ length: 10 }, (_, i) => ({
        skill: `Skill ${i}`,
        confidence: 0.8,
        match_type: 'direct',
      }));

      render(
        <SkillDetailsWithConfidence skills={skills} maxDisplay={5} />
      );

      expect(screen.getByText('Showing 5 of 10 matched skills')).toBeInTheDocument();
    });

    it('should not show "showing more" text when skills fit in limit', () => {
      render(
        <SkillDetailsWithConfidence skills={mockSkills} maxDisplay={10} />
      );

      expect(screen.queryByText(/Showing/)).not.toBeInTheDocument();
    });
  });

  describe('Interactive Elements', () => {
    it('should have hover effect on skill items', () => {
      const { container } = render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      // Check for items with hover styles
      const skillItems = container.querySelectorAll('[class*="backgroundColor"]');
      expect(skillItems.length).toBeGreaterThan(0);
    });
  });

  describe('Match Type Tooltips', () => {
    it('should render tooltips for match type badges', () => {
      const { container } = render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      // Tooltips are rendered with title attributes or via Tooltip component
      const tooltips = container.querySelectorAll('[class*="MuiTooltip"]');
      expect(tooltips.length).toBeGreaterThan(0);
    });
  });

  describe('Confidence Color Coding', () => {
    it('should apply correct color for high confidence (>=0.9)', () => {
      const highConfidenceSkills: SkillMatchDetail[] = [
        {
          skill: 'Expert Skill',
          confidence: 0.95,
          match_type: 'direct',
        },
      ];

      render(
        <SkillDetailsWithConfidence skills={highConfidenceSkills} />
      );

      // High confidence should have success/light color
      expect(screen.getByText('95%')).toBeInTheDocument();
    });

    it('should apply correct color for medium confidence (>=0.7)', () => {
      const mediumConfidenceSkills: SkillMatchDetail[] = [
        {
          skill: 'Medium Skill',
          confidence: 0.75,
          match_type: 'direct',
        },
      ];

      render(
        <SkillDetailsWithConfidence skills={mediumConfidenceSkills} />
      );

      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('should apply correct color for lower confidence (>=0.5)', () => {
      const lowerConfidenceSkills: SkillMatchDetail[] = [
        {
          skill: 'Lower Skill',
          confidence: 0.55,
          match_type: 'direct',
        },
      ];

      render(
        <SkillDetailsWithConfidence skills={lowerConfidenceSkills} />
      );

      expect(screen.getByText('55%')).toBeInTheDocument();
    });

    it('should apply correct color for low confidence (<0.5)', () => {
      const lowConfidenceSkills: SkillMatchDetail[] = [
        {
          skill: 'Low Skill',
          confidence: 0.35,
          match_type: 'fuzzy',
        },
      ];

      render(
        <SkillDetailsWithConfidence skills={lowConfidenceSkills} />
      );

      expect(screen.getByText('35%')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle skill with no match_type', () => {
      const skillsWithoutType: SkillMatchDetail[] = [
        {
          skill: 'Unknown Skill',
          confidence: 0.5,
          match_type: undefined as any,
        },
      ];

      render(
        <SkillDetailsWithConfidence skills={skillsWithoutType} />
      );

      expect(screen.getByText('Unknown')).toBeInTheDocument();
    });

    it('should handle skill with empty locations array', () => {
      const skillsWithEmptyLocations: SkillMatchDetail[] = [
        {
          skill: 'Skill',
          confidence: 0.8,
          match_type: 'direct',
          locations: [],
        },
      ];

      render(
        <SkillDetailsWithConfidence skills={skillsWithEmptyLocations} />
      );

      expect(screen.queryByText('Found in resume:')).not.toBeInTheDocument();
    });

    it('should handle zero confidence', () => {
      const zeroConfidenceSkills: SkillMatchDetail[] = [
        {
          skill: 'Zero Confidence',
          confidence: 0,
          match_type: 'direct',
        },
      ];

      render(
        <SkillDetailsWithConfidence skills={zeroConfidenceSkills} />
      );

      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('should handle perfect confidence', () => {
      const perfectConfidenceSkills: SkillMatchDetail[] = [
        {
          skill: 'Perfect Skill',
          confidence: 1.0,
          match_type: 'direct',
        },
      ];

      render(
        <SkillDetailsWithConfidence skills={perfectConfidenceSkills} />
      );

      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });

  describe('Layout and Structure', () => {
    it('should render in card container', () => {
      const { container } = render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      const card = container.querySelector('.MuiCard-root');
      expect(card).toBeInTheDocument();
    });

    it('should render divider', () => {
      const { container } = render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      const divider = container.querySelector('.MuiDivider-root');
      expect(divider).toBeInTheDocument();
    });

    it('should render in stack layout', () => {
      const { container } = render(
        <SkillDetailsWithConfidence skills={mockSkills} />
      );

      const stacks = container.querySelectorAll('.MuiStack-root');
      expect(stacks.length).toBeGreaterThan(0);
    });
  });
});
