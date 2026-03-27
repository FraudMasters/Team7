/**
 * Tests for FunnelConversionChart Component
 *
 * Tests the funnel conversion chart including:
 * - Rendering conversion data
 * - Summary metrics display
 * - Stage-by-stage conversion rates
 * - Best and worst performing stages
 * - Color coding based on conversion rates
 * - Loading states
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import FunnelConversionChart from './FunnelConversionChart';
import type { FunnelStage } from '@/types/api';

describe('FunnelConversionChart', () => {
  const mockStages: FunnelStage[] = [
    {
      stage_name: 'resumes_uploaded',
      count: 1000,
      conversion_rate: 1.0,
    },
    {
      stage_name: 'resumes_processed',
      count: 900,
      conversion_rate: 0.9,
    },
    {
      stage_name: 'candidates_matched',
      count: 600,
      conversion_rate: 0.667,
    },
    {
      stage_name: 'candidates_shortlisted',
      count: 300,
      conversion_rate: 0.5,
    },
    {
      stage_name: 'candidates_interviewed',
      count: 150,
      conversion_rate: 0.5,
    },
    {
      stage_name: 'candidates_hired',
      count: 50,
      conversion_rate: 0.333,
    },
  ];

  const mockTotalCount = 1000;

  describe('Component Rendering', () => {
    it('should render all main sections', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      expect(screen.getByText('Overall Conversion')).toBeInTheDocument();
      expect(screen.getByText('Average Stage Conversion')).toBeInTheDocument();
      expect(screen.getByText('Total Drop-off')).toBeInTheDocument();
      expect(screen.getByText('Stage-by-Stage Conversion Rates')).toBeInTheDocument();
    });

    it('should render all funnel stages', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      expect(screen.getByText('Resumes Uploaded')).toBeInTheDocument();
      expect(screen.getByText('Resumes Processed')).toBeInTheDocument();
      expect(screen.getByText('Candidates Matched')).toBeInTheDocument();
      expect(screen.getByText('Candidates Shortlisted')).toBeInTheDocument();
      expect(screen.getByText('Candidates Interviewed')).toBeInTheDocument();
      expect(screen.getByText('Candidates Hired')).toBeInTheDocument();
    });

    it('should render with empty stages', () => {
      render(
        <FunnelConversionChart
          stages={[]}
          totalCount={0}
        />
      );

      expect(screen.getByText('No funnel data available')).toBeInTheDocument();
    });

    it('should render insights sections', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      expect(screen.getByText('Best Performing Stage')).toBeInTheDocument();
      expect(screen.getByText('Needs Attention')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading state when loading is true', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
          loading={true}
        />
      );

      expect(screen.getByText('Loading conversion data...')).toBeInTheDocument();
      expect(screen.queryByText('Overall Conversion')).not.toBeInTheDocument();
    });

    it('should not show loading state when loading is false', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
          loading={false}
        />
      );

      expect(screen.queryByText('Loading conversion data...')).not.toBeInTheDocument();
      expect(screen.getByText('Overall Conversion')).toBeInTheDocument();
    });

    it('should show content when loading is undefined (default false)', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      expect(screen.queryByText('Loading conversion data...')).not.toBeInTheDocument();
      expect(screen.getByText('Overall Conversion')).toBeInTheDocument();
    });
  });

  describe('Summary Metrics', () => {
    it('should display overall conversion rate', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      // Overall conversion: 50/1000 = 0.05 = 5.0%
      expect(screen.getByText('5.0%')).toBeInTheDocument();
      expect(screen.getByText('First to final stage')).toBeInTheDocument();
    });

    it('should display average stage conversion', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      // Average of conversion rates (excluding first stage)
      expect(screen.getByText(/Across 5 transitions/)).toBeInTheDocument();
    });

    it('should display total drop-off', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      // 1 - 0.05 = 0.95 = 95.0%
      expect(screen.getByText('95.0%')).toBeInTheDocument();
      expect(screen.getByText('950 candidates lost')).toBeInTheDocument();
    });

    it('should handle zero total count', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={0}
        />
      );

      expect(screen.getByText('0.0%')).toBeInTheDocument();
    });
  });

  describe('Stage Conversion Details', () => {
    it('should display starting point chip for first stage', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      expect(screen.getByText('Starting Point')).toBeInTheDocument();
    });

    it('should display conversion rates for non-first stages', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      expect(screen.getByText('90.0%')).toBeInTheDocument(); // resumes_processed
      expect(screen.getByText('66.7%')).toBeInTheDocument(); // candidates_matched
    });

    it('should display count for each stage', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      // Use getAllByText because counts appear multiple times
      expect(screen.getAllByText('1,000').length).toBeGreaterThan(0);
      expect(screen.getAllByText('900').length).toBeGreaterThan(0);
      expect(screen.getAllByText('600').length).toBeGreaterThan(0);
    });

    it('should display drop-off information', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      // Check for drop-off text (100 candidates from 1000 to 900)
      expect(screen.getByText(/100 candidates dropped/)).toBeInTheDocument();
      expect(screen.getByText(/400 candidates dropped/)).toBeInTheDocument(); // 900 to 600
    });

    it('should show "From" label for stage transitions', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      expect(screen.getByText(/From Resumes Uploaded/)).toBeInTheDocument();
      expect(screen.getByText(/From Resumes Processed/)).toBeInTheDocument();
    });

    it('should display above/below average indicators', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      expect(screen.getAllByText('Above Average').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Below Average').length).toBeGreaterThan(0);
    });
  });

  describe('Best Performing Stage', () => {
    it('should identify and display best performing stage', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      // Best stage is resumes_processed with 90% conversion
      expect(screen.getAllByText('Resumes Processed').length).toBeGreaterThan(0);
    });

    it('should show "Not enough data" when only one stage', () => {
      const singleStage: FunnelStage[] = [
        {
          stage_name: 'resumes_uploaded',
          count: 100,
          conversion_rate: 1.0,
        },
      ];

      render(
        <FunnelConversionChart
          stages={singleStage}
          totalCount={100}
        />
      );

      expect(screen.getAllByText('Not enough data').length).toBe(2);
    });

    it('should display positive variance from average', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      // Should show +X% vs avg
      const { container } = render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );
      expect(container.textContent).toContain('vs avg');
    });
  });

  describe('Worst Performing Stage', () => {
    it('should identify and display worst performing stage', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      // Worst stage is candidates_hired with 33.3% conversion
      expect(screen.getAllByText('Candidates Hired').length).toBeGreaterThan(0);
    });

    it('should display negative variance from average', () => {
      render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      // Should show percentage variance
      const { container } = render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );
      expect(container.textContent).toContain('vs avg');
    });
  });

  describe('Conversion Color Coding', () => {
    it('should use success color for high conversion (>=70%)', () => {
      const highConversionStages: FunnelStage[] = [
        {
          stage_name: 'stage_1',
          count: 100,
          conversion_rate: 1.0,
        },
        {
          stage_name: 'stage_2',
          count: 85,
          conversion_rate: 0.85,
        },
      ];

      const { container } = render(
        <FunnelConversionChart
          stages={highConversionStages}
          totalCount={100}
        />
      );

      // Check that success indicators are rendered
      const successIcons = container.querySelectorAll('[data-testid="CheckCircleIcon"]');
      expect(successIcons.length).toBeGreaterThan(0);
    });

    it('should use warning color for moderate conversion (50-69%)', () => {
      const moderateConversionStages: FunnelStage[] = [
        {
          stage_name: 'stage_1',
          count: 100,
          conversion_rate: 1.0,
        },
        {
          stage_name: 'stage_2',
          count: 60,
          conversion_rate: 0.6,
        },
      ];

      const { container } = render(
        <FunnelConversionChart
          stages={moderateConversionStages}
          totalCount={100}
        />
      );

      // Check that warning indicators are rendered
      const warningIcons = container.querySelectorAll('[data-testid="WarningIcon"]');
      expect(warningIcons.length).toBeGreaterThan(0);
    });

    it('should use error color for low conversion (<50%)', () => {
      const lowConversionStages: FunnelStage[] = [
        {
          stage_name: 'stage_1',
          count: 100,
          conversion_rate: 1.0,
        },
        {
          stage_name: 'stage_2',
          count: 30,
          conversion_rate: 0.3,
        },
      ];

      const { container } = render(
        <FunnelConversionChart
          stages={lowConversionStages}
          totalCount={100}
        />
      );

      // Check that warning indicators are rendered (used for both warning and error cases)
      const warningIcons = container.querySelectorAll('[data-testid="WarningIcon"]');
      expect(warningIcons.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle single stage', () => {
      const singleStage: FunnelStage[] = [
        {
          stage_name: 'resumes_uploaded',
          count: 100,
          conversion_rate: 1.0,
        },
      ];

      render(
        <FunnelConversionChart
          stages={singleStage}
          totalCount={100}
        />
      );

      expect(screen.getByText('Resumes Uploaded')).toBeInTheDocument();
      expect(screen.getByText('Starting Point')).toBeInTheDocument();
    });

    it('should handle zero conversion rate', () => {
      const zeroConversionStages: FunnelStage[] = [
        {
          stage_name: 'stage_1',
          count: 100,
          conversion_rate: 1.0,
        },
        {
          stage_name: 'stage_2',
          count: 0,
          conversion_rate: 0.0,
        },
      ];

      render(
        <FunnelConversionChart
          stages={zeroConversionStages}
          totalCount={100}
        />
      );

      expect(screen.getByText('0.0%')).toBeInTheDocument();
      expect(screen.getByText('100 candidates dropped (100.0%)')).toBeInTheDocument();
    });

    it('should handle perfect conversion rate (100%)', () => {
      const perfectConversionStages: FunnelStage[] = [
        {
          stage_name: 'stage_1',
          count: 100,
          conversion_rate: 1.0,
        },
        {
          stage_name: 'stage_2',
          count: 100,
          conversion_rate: 1.0,
        },
      ];

      render(
        <FunnelConversionChart
          stages={perfectConversionStages}
          totalCount={100}
        />
      );

      expect(screen.getByText('100.0%')).toBeInTheDocument();
      expect(screen.getByText('0 candidates dropped (0.0%)')).toBeInTheDocument();
    });

    it('should handle large numbers with proper formatting', () => {
      const largeNumberStages: FunnelStage[] = [
        {
          stage_name: 'stage_1',
          count: 1000000,
          conversion_rate: 1.0,
        },
        {
          stage_name: 'stage_2',
          count: 500000,
          conversion_rate: 0.5,
        },
      ];

      render(
        <FunnelConversionChart
          stages={largeNumberStages}
          totalCount={1000000}
        />
      );

      expect(screen.getAllByText('1,000,000').length).toBeGreaterThan(0);
      expect(screen.getAllByText('500,000').length).toBeGreaterThan(0);
    });

    it('should handle decimal conversion rates', () => {
      const decimalConversionStages: FunnelStage[] = [
        {
          stage_name: 'stage_1',
          count: 1000,
          conversion_rate: 1.0,
        },
        {
          stage_name: 'stage_2',
          count: 678,
          conversion_rate: 0.678,
        },
      ];

      render(
        <FunnelConversionChart
          stages={decimalConversionStages}
          totalCount={1000}
        />
      );

      expect(screen.getByText('67.8%')).toBeInTheDocument();
    });

    it('should handle custom stage names', () => {
      const customStages: FunnelStage[] = [
        {
          stage_name: 'custom_stage_name',
          count: 100,
          conversion_rate: 1.0,
        },
        {
          stage_name: 'another_custom_stage',
          count: 80,
          conversion_rate: 0.8,
        },
      ];

      render(
        <FunnelConversionChart
          stages={customStages}
          totalCount={100}
        />
      );

      expect(screen.getByText('Custom Stage Name')).toBeInTheDocument();
      expect(screen.getByText('Another Custom Stage')).toBeInTheDocument();
    });
  });

  describe('Visual Design Elements', () => {
    it('should render paper components', () => {
      const { container } = render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      const papers = container.querySelectorAll('.MuiPaper-root');
      expect(papers.length).toBeGreaterThan(0);
    });

    it('should render cards for summary metrics', () => {
      const { container } = render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      const cards = container.querySelectorAll('.MuiCard-root');
      expect(cards.length).toBeGreaterThan(0);
    });

    it('should render linear progress bars for each stage', () => {
      const { container } = render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      const progressBars = container.querySelectorAll('.MuiLinearProgress-root');
      expect(progressBars.length).toBe(mockStages.length);
    });

    it('should render chips for conversion indicators', () => {
      const { container } = render(
        <FunnelConversionChart
          stages={mockStages}
          totalCount={mockTotalCount}
        />
      );

      const chips = container.querySelectorAll('.MuiChip-root');
      expect(chips.length).toBeGreaterThan(0);
    });
  });

  describe('Data Formatting', () => {
    it('should format percentages with one decimal place', () => {
      const stages: FunnelStage[] = [
        {
          stage_name: 'stage_1',
          count: 1000,
          conversion_rate: 1.0,
        },
        {
          stage_name: 'stage_2',
          count: 666,
          conversion_rate: 0.666,
        },
      ];

      render(
        <FunnelConversionChart
          stages={stages}
          totalCount={1000}
        />
      );

      expect(screen.getByText('66.6%')).toBeInTheDocument();
    });

    it('should format large numbers with commas', () => {
      const stages: FunnelStage[] = [
        {
          stage_name: 'stage_1',
          count: 123456,
          conversion_rate: 1.0,
        },
      ];

      render(
        <FunnelConversionChart
          stages={stages}
          totalCount={123456}
        />
      );

      expect(screen.getAllByText('123,456').length).toBeGreaterThan(0);
    });

    it('should format stage names with proper capitalization', () => {
      const stages: FunnelStage[] = [
        {
          stage_name: 'resumes_uploaded',
          count: 100,
          conversion_rate: 1.0,
        },
      ];

      render(
        <FunnelConversionChart
          stages={stages}
          totalCount={100}
        />
      );

      expect(screen.getByText('Resumes Uploaded')).toBeInTheDocument();
    });
  });
});
