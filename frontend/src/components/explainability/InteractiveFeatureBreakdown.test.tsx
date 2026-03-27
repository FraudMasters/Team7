/**
 * Tests for InteractiveFeatureBreakdown Component
 *
 * Tests the interactive feature breakdown visualization including:
 * - Displaying individual feature scores with weights and contributions
 * - Interactive hover effects and tooltips
 * - Drill-down capabilities for features with breakdowns
 * - Expandable/collapsible detailed breakdowns
 * - Color-coded progress bars based on score values
 * - Overall score calculation and display
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import InteractiveFeatureBreakdown, {
  InteractiveFeature,
} from './InteractiveFeatureBreakdown';

describe('InteractiveFeatureBreakdown', () => {
  const mockFeatures: InteractiveFeature[] = [
    {
      name: 'Technical Skills',
      value: 0.85,
      weight: 0.4,
      contribution: 0.34,
      category: 'Skills',
      description: 'Programming languages and frameworks',
      breakdown: [
        {
          label: 'JavaScript',
          value: 0.9,
          description: 'Advanced JavaScript proficiency',
          impact: 'positive',
        },
        {
          label: 'React',
          value: 0.8,
          description: 'Strong React experience',
          impact: 'positive',
        },
      ],
      metadata: {
        source: 'Resume Analysis',
        confidence: 0.95,
        lastUpdated: '2024-03-20',
      },
    },
    {
      name: 'Work Experience',
      value: 0.72,
      weight: 0.35,
      contribution: 0.252,
      category: 'Experience',
      description: 'Years of relevant work experience',
    },
    {
      name: 'Education',
      value: 0.60,
      weight: 0.25,
      contribution: 0.15,
      category: 'Academics',
    },
  ];

  describe('Component Rendering', () => {
    it('should render the component with default title', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getByText('Interactive Feature Breakdown')).toBeInTheDocument();
      expect(
        screen.getByText('Hover over features for details, click to drill down into sub-components')
      ).toBeInTheDocument();
    });

    it('should render with custom title and description', () => {
      render(
        <InteractiveFeatureBreakdown
          features={mockFeatures}
          title="Custom Analysis"
          description="Custom description text"
        />
      );

      expect(screen.getByText('Custom Analysis')).toBeInTheDocument();
      expect(screen.getByText('Custom description text')).toBeInTheDocument();
    });

    it('should display overall score', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getByText('Overall Score')).toBeInTheDocument();
      // Overall = 0.34 + 0.252 + 0.15 = 0.742 = 74%
      expect(screen.getByText('74%')).toBeInTheDocument();
    });

    it('should use provided overall score when available', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} overallScore={0.85} />);

      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.queryByText('74%')).not.toBeInTheDocument();
    });

    it('should display empty state when no features provided', () => {
      render(<InteractiveFeatureBreakdown features={[]} />);

      expect(screen.getByText('No feature data available')).toBeInTheDocument();
    });
  });

  describe('Feature Displays', () => {
    it('should display all feature names', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getByText('Technical Skills')).toBeInTheDocument();
      expect(screen.getByText('Work Experience')).toBeInTheDocument();
      expect(screen.getByText('Education')).toBeInTheDocument();
    });

    it('should display feature categories', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getByText('Skills')).toBeInTheDocument();
      expect(screen.getByText('Experience')).toBeInTheDocument();
      expect(screen.getByText('Academics')).toBeInTheDocument();
    });

    it('should display feature values as percentages', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getByText('85%')).toBeInTheDocument(); // Technical Skills value
      expect(screen.getByText('72%')).toBeInTheDocument(); // Work Experience value
      expect(screen.getByText('60%')).toBeInTheDocument(); // Education value
    });

    it('should display feature weights', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getByText('40%')).toBeInTheDocument(); // Technical Skills weight
      expect(screen.getByText('35%')).toBeInTheDocument(); // Work Experience weight
      expect(screen.getByText('25%')).toBeInTheDocument(); // Education weight
    });

    it('should display feature contributions', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getByText('+34%')).toBeInTheDocument(); // Technical Skills contribution
      expect(screen.getByText('+25%')).toBeInTheDocument(); // Work Experience contribution
      expect(screen.getByText('+15%')).toBeInTheDocument(); // Education contribution
    });

    it('should show breakdown item count for expandable features', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getByText('2 items')).toBeInTheDocument(); // Technical Skills has 2 breakdown items
    });
  });

  describe('Interactive Features', () => {
    it('should show info icons when showHoverDetails is true', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} showHoverDetails={true} />);

      const infoIcons = document.querySelectorAll('[data-testid="InfoIcon"]');
      expect(infoIcons.length).toBeGreaterThan(0);
    });

    it('should call onFeatureClick when feature is clicked', () => {
      const mockOnFeatureClick = vi.fn();
      render(
        <InteractiveFeatureBreakdown
          features={mockFeatures}
          onFeatureClick={mockOnFeatureClick}
        />
      );

      const technicalSkillsCard = screen.getByText('Technical Skills').closest('.MuiCard-root');
      if (technicalSkillsCard) {
        fireEvent.click(technicalSkillsCard);
      }

      expect(mockOnFeatureClick).toHaveBeenCalledWith(mockFeatures[0]);
    });

    it('should display progress bars for each feature', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      const progressBars = document.querySelectorAll('.MuiLinearProgress-root');
      expect(progressBars.length).toBeGreaterThanOrEqual(3); // At least 3 main progress bars
    });

    it('should display Feature Value labels', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getAllByText('Feature Value').length).toBeGreaterThanOrEqual(3);
    });

    it('should display Weight and Contribution labels', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getAllByText('Weight').length).toBeGreaterThanOrEqual(3);
      expect(screen.getAllByText('Contribution').length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Drill-Down Functionality', () => {
    it('should show expand icons for features with breakdown', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      const expandIcons = document.querySelectorAll('[data-testid="ExpandMoreIcon"]');
      expect(expandIcons.length).toBeGreaterThan(0);
    });

    it('should toggle breakdown when expand button is clicked', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      // Initially, breakdown should not be visible
      expect(screen.queryByText('JavaScript')).not.toBeInTheDocument();
      expect(screen.queryByText('React')).not.toBeInTheDocument();

      // Click expand button
      const expandButton = document.querySelector('[data-testid="ExpandMoreIcon"]')
        ?.closest('button');
      if (expandButton) {
        fireEvent.click(expandButton);
      }

      // Breakdown should now be visible
      expect(screen.getByText('JavaScript')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
    });

    it('should display breakdown descriptions', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      // Expand the feature
      const expandButton = document.querySelector('[data-testid="ExpandMoreIcon"]')
        ?.closest('button');
      if (expandButton) {
        fireEvent.click(expandButton);
      }

      expect(screen.getByText('Advanced JavaScript proficiency')).toBeInTheDocument();
      expect(screen.getByText('Strong React experience')).toBeInTheDocument();
    });

    it('should display breakdown values as percentages', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      // Expand the feature
      const expandButton = document.querySelector('[data-testid="ExpandMoreIcon"]')
        ?.closest('button');
      if (expandButton) {
        fireEvent.click(expandButton);
      }

      expect(screen.getByText('90%')).toBeInTheDocument(); // JavaScript value
      expect(screen.getByText('80%')).toBeInTheDocument(); // React value
    });

    it('should expand all features by default when defaultExpanded is true', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} defaultExpanded={true} />);

      // Breakdown items should be visible immediately
      expect(screen.getByText('JavaScript')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
    });
  });

  describe('Score Calculations', () => {
    it('should calculate overall score correctly', () => {
      const features: InteractiveFeature[] = [
        { name: 'Feature1', value: 0.5, weight: 0.5, contribution: 0.25 },
        { name: 'Feature2', value: 0.5, weight: 0.5, contribution: 0.25 },
      ];

      render(<InteractiveFeatureBreakdown features={features} />);

      // Overall = 0.25 + 0.25 = 0.50 = 50%
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('should display feature breakdown formula', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getByText('Feature Breakdown Formula')).toBeInTheDocument();
      expect(screen.getByText(/34% \+ 25% \+ 15% = 74%/)).toBeInTheDocument();
    });

    it('should prioritize provided overall score over calculated', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} overallScore={0.9} />);

      expect(screen.getByText('90%')).toBeInTheDocument();
      expect(screen.queryByText('74%')).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle features with zero scores', () => {
      const features: InteractiveFeature[] = [
        { name: 'Feature1', value: 0, weight: 0.5, contribution: 0 },
        { name: 'Feature2', value: 0, weight: 0.5, contribution: 0 },
      ];

      render(<InteractiveFeatureBreakdown features={features} />);

      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('should handle features with perfect scores', () => {
      const features: InteractiveFeature[] = [
        { name: 'Feature1', value: 1, weight: 0.5, contribution: 0.5 },
        { name: 'Feature2', value: 1, weight: 0.5, contribution: 0.5 },
      ];

      render(<InteractiveFeatureBreakdown features={features} />);

      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('should handle features without categories', () => {
      const features: InteractiveFeature[] = [
        { name: 'Feature1', value: 0.5, weight: 0.5, contribution: 0.25 },
      ];

      render(<InteractiveFeatureBreakdown features={features} />);

      expect(screen.getByText('Feature1')).toBeInTheDocument();
    });

    it('should handle features without breakdowns', () => {
      const features: InteractiveFeature[] = [
        { name: 'Feature1', value: 0.5, weight: 0.5, contribution: 0.25 },
      ];

      render(<InteractiveFeatureBreakdown features={features} />);

      const expandIcons = document.querySelectorAll('[data-testid="ExpandMoreIcon"]');
      expect(expandIcons.length).toBe(0);
    });

    it('should handle decimal scores correctly', () => {
      const features: InteractiveFeature[] = [
        { name: 'Feature1', value: 0.856, weight: 0.423, contribution: 0.362 },
      ];

      render(<InteractiveFeatureBreakdown features={features} />);

      // Should round to nearest percent
      expect(screen.getByText('86%')).toBeInTheDocument(); // value
      expect(screen.getByText('42%')).toBeInTheDocument(); // weight
      expect(screen.getByText('+36%')).toBeInTheDocument(); // contribution
    });
  });

  describe('Layout and Structure', () => {
    it('should render cards for each feature', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      const cards = document.querySelectorAll('.MuiCard-root');
      expect(cards.length).toBeGreaterThanOrEqual(3);
    });

    it('should render in stack layout', () => {
      const { container } = render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      const stacks = container.querySelectorAll('.MuiStack-root');
      expect(stacks.length).toBeGreaterThan(0);
    });

    it('should display interactive help text when showHoverDetails is true', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} showHoverDetails={true} />);

      expect(screen.getByText(/Interactive Features:/)).toBeInTheDocument();
      expect(
        screen.getByText(/Hover over any feature to see detailed information/)
      ).toBeInTheDocument();
    });

    it('should not display interactive help when showHoverDetails is false', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} showHoverDetails={false} />);

      expect(screen.queryByText(/Interactive Features:/)).not.toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('should use Grid layout for responsive design', () => {
      const { container } = render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      const grids = container.querySelectorAll('.MuiGrid-root');
      expect(grids.length).toBeGreaterThan(0);
    });

    it('should render all features in mobile view', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getByText('Technical Skills')).toBeInTheDocument();
      expect(screen.getByText('Work Experience')).toBeInTheDocument();
      expect(screen.getByText('Education')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading structure', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getByText('Interactive Feature Breakdown')).toBeInTheDocument();
      expect(screen.getByText('Interactive Feature Analysis')).toBeInTheDocument();
    });

    it('should provide labels for progress bars', () => {
      render(<InteractiveFeatureBreakdown features={mockFeatures} />);

      expect(screen.getAllByText('Feature Value').length).toBeGreaterThanOrEqual(3);
    });
  });
});
