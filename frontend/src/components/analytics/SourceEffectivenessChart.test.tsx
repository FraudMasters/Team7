/**
 * Tests for SourceEffectivenessChart Component
 *
 * Tests the source effectiveness chart including:
 * - Rendering source metrics
 * - Application volume visualization
 * - Conversion rate comparison
 * - Quality score display
 * - Cost effectiveness analysis
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import SourceEffectivenessChart, {
  SourceEffectivenessMetrics,
  SourceMetrics,
} from './SourceEffectivenessChart';

describe('SourceEffectivenessChart', () => {
  const mockSourceMetrics: SourceMetrics[] = [
    {
      source_type: 'JOB_BOARD',
      source_name: 'LinkedIn',
      total_applications: 450,
      hired_count: 38,
      conversion_rate: 0.084,
      average_quality_score: 78.5,
      average_cost_per_application: 12.5,
      total_cost: 5625.0,
      cost_per_hire: 148.03,
      average_time_to_hire_days: 28.5,
    },
    {
      source_type: 'REFERRAL',
      source_name: 'Employee Referral',
      total_applications: 125,
      hired_count: 28,
      conversion_rate: 0.224,
      average_quality_score: 85.7,
      average_cost_per_application: 5.0,
      total_cost: 625.0,
      cost_per_hire: 22.32,
      average_time_to_hire_days: 21.5,
    },
    {
      source_type: 'JOB_BOARD',
      source_name: 'Indeed',
      total_applications: 380,
      hired_count: 25,
      conversion_rate: 0.066,
      average_quality_score: 72.3,
      average_cost_per_application: 8.75,
      total_cost: 3325.0,
      cost_per_hire: 133.0,
      average_time_to_hire_days: 32.0,
    },
  ];

  const mockMetrics: SourceEffectivenessMetrics = {
    sources: mockSourceMetrics,
    total_applications: 955,
    total_hired: 91,
    overall_conversion_rate: 0.095,
    best_source_by_conversion: 'Employee Referral',
    best_source_by_quality: 'Employee Referral',
    best_source_by_cost: 'Employee Referral',
    total_recruiting_cost: 9575.0,
    average_cost_per_hire: 105.22,
  };

  describe('Component Rendering', () => {
    it('should render summary cards with correct metrics', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText('Total Applications')).toBeInTheDocument();
      expect(screen.getByText('955')).toBeInTheDocument();

      expect(screen.getByText('Overall Conversion')).toBeInTheDocument();
      expect(screen.getByText('9.5%')).toBeInTheDocument();
      expect(screen.getByText('91 hired')).toBeInTheDocument();

      expect(screen.getByText('Avg Cost Per Hire')).toBeInTheDocument();
      expect(screen.getByText('$105.22')).toBeInTheDocument();

      expect(screen.getByText('Best Source')).toBeInTheDocument();
      expect(screen.getByText('Employee Referral')).toBeInTheDocument();
    });

    it('should render all source names in application volume section', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText('Application Volume')).toBeInTheDocument();
      expect(screen.getAllByText('LinkedIn')[0]).toBeInTheDocument();
      expect(screen.getAllByText('Employee Referral')[0]).toBeInTheDocument();
      expect(screen.getAllByText('Indeed')[0]).toBeInTheDocument();
    });

    it('should render conversion rates section with sorted sources', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText('Conversion Rates')).toBeInTheDocument();

      // Check that conversion rates are displayed
      expect(screen.getByText('22.4%')).toBeInTheDocument(); // Employee Referral
      expect(screen.getByText('8.4%')).toBeInTheDocument(); // LinkedIn
      expect(screen.getByText('6.6%')).toBeInTheDocument(); // Indeed
    });

    it('should render quality scores section', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText('Quality Scores')).toBeInTheDocument();
      expect(screen.getByText('85.7')).toBeInTheDocument();
      expect(screen.getByText('78.5')).toBeInTheDocument();
      expect(screen.getByText('72.3')).toBeInTheDocument();
    });

    it('should render cost per hire section', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText('Cost Per Hire')).toBeInTheDocument();
      expect(screen.getByText('$22.32')).toBeInTheDocument();
      expect(screen.getByText('$148.03')).toBeInTheDocument();
      expect(screen.getByText('$133.00')).toBeInTheDocument();
    });

    it('should display source types as chips', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      const jobBoardChips = screen.getAllByText('JOB_BOARD');
      expect(jobBoardChips.length).toBeGreaterThan(0);

      const referralChips = screen.getAllByText('REFERRAL');
      expect(referralChips.length).toBeGreaterThan(0);
    });
  });

  describe('Loading State', () => {
    it('should show loading indicator when loading is true', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} loading={true} />);

      expect(screen.getByText('Loading source effectiveness data...')).toBeInTheDocument();
      expect(screen.queryByText('Application Volume')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should show empty state message when no sources', () => {
      const emptyMetrics: SourceEffectivenessMetrics = {
        sources: [],
        total_applications: 0,
        total_hired: 0,
        overall_conversion_rate: 0,
      };

      render(<SourceEffectivenessChart metrics={emptyMetrics} />);

      expect(screen.getByText('No source effectiveness data available')).toBeInTheDocument();
      expect(screen.queryByText('Application Volume')).not.toBeInTheDocument();
    });
  });

  describe('Data Formatting', () => {
    it('should format currency values correctly', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText('$105.22')).toBeInTheDocument();
      expect(screen.getByText('$22.32')).toBeInTheDocument();
    });

    it('should format percentage values correctly', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText('9.5%')).toBeInTheDocument();
      expect(screen.getByText('22.4%')).toBeInTheDocument();
      expect(screen.getByText('8.4%')).toBeInTheDocument();
    });

    it('should format application counts with locale string', () => {
      const largeMetrics: SourceEffectivenessMetrics = {
        sources: [
          {
            source_type: 'JOB_BOARD',
            source_name: 'LinkedIn',
            total_applications: 1234567,
            hired_count: 100,
            conversion_rate: 0.01,
          },
        ],
        total_applications: 1234567,
        total_hired: 100,
        overall_conversion_rate: 0.01,
      };

      render(<SourceEffectivenessChart metrics={largeMetrics} />);

      expect(screen.getByText('1,234,567')).toBeInTheDocument();
    });
  });

  describe('Trophy Indicators', () => {
    it('should show "Best" chip for highest conversion rate', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      const bestChips = screen.getAllByText('Best');
      expect(bestChips.length).toBeGreaterThan(0);
    });

    it('should show "Highest Quality" chip for best quality source', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText('Highest Quality')).toBeInTheDocument();
    });

    it('should show "Most Efficient" chip for lowest cost per hire', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText('Most Efficient')).toBeInTheDocument();
    });
  });

  describe('Optional Data Handling', () => {
    it('should handle missing quality scores', () => {
      const metricsWithoutQuality: SourceEffectivenessMetrics = {
        sources: [
          {
            source_type: 'JOB_BOARD',
            source_name: 'LinkedIn',
            total_applications: 100,
            hired_count: 10,
            conversion_rate: 0.1,
          },
        ],
        total_applications: 100,
        total_hired: 10,
        overall_conversion_rate: 0.1,
      };

      render(<SourceEffectivenessChart metrics={metricsWithoutQuality} />);

      expect(screen.getByText('Quality Scores')).toBeInTheDocument();
      expect(screen.getByText('N/A')).toBeInTheDocument();
    });

    it('should handle missing cost data', () => {
      const metricsWithoutCost: SourceEffectivenessMetrics = {
        sources: [
          {
            source_type: 'JOB_BOARD',
            source_name: 'LinkedIn',
            total_applications: 100,
            hired_count: 10,
            conversion_rate: 0.1,
          },
        ],
        total_applications: 100,
        total_hired: 10,
        overall_conversion_rate: 0.1,
      };

      render(<SourceEffectivenessChart metrics={metricsWithoutCost} />);

      expect(screen.getByText('Cost Per Hire')).toBeInTheDocument();
      expect(screen.getByText('No cost data available for sources')).toBeInTheDocument();
    });

    it('should show N/A for missing average cost per hire', () => {
      const metricsWithoutAvgCost: SourceEffectivenessMetrics = {
        ...mockMetrics,
        average_cost_per_hire: undefined,
      };

      render(<SourceEffectivenessChart metrics={metricsWithoutAvgCost} />);

      const summaryCards = screen.getAllByText('N/A');
      expect(summaryCards.length).toBeGreaterThan(0);
    });
  });

  describe('Time to Hire Display', () => {
    it('should display average time to hire when available', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText(/29d/)).toBeInTheDocument(); // LinkedIn: 28.5 days rounded
      expect(screen.getByText(/22d/)).toBeInTheDocument(); // Employee Referral: 21.5 days rounded
      expect(screen.getByText(/32d/)).toBeInTheDocument(); // Indeed: 32 days
    });
  });

  describe('Application Details', () => {
    it('should show hired count in application volume section', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText('Hired: 38')).toBeInTheDocument();
      expect(screen.getByText('Hired: 28')).toBeInTheDocument();
      expect(screen.getByText('Hired: 25')).toBeInTheDocument();
    });

    it('should show application breakdown in conversion rates', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText('28 of 125 applications')).toBeInTheDocument();
      expect(screen.getByText('38 of 450 applications')).toBeInTheDocument();
      expect(screen.getByText('25 of 380 applications')).toBeInTheDocument();
    });
  });

  describe('Multiple Sources Count', () => {
    it('should display correct source count in summary', () => {
      render(<SourceEffectivenessChart metrics={mockMetrics} />);

      expect(screen.getByText('3 sources')).toBeInTheDocument();
    });

    it('should handle single source', () => {
      const singleSourceMetrics: SourceEffectivenessMetrics = {
        sources: [mockSourceMetrics[0]],
        total_applications: 450,
        total_hired: 38,
        overall_conversion_rate: 0.084,
        best_source_by_conversion: 'LinkedIn',
      };

      render(<SourceEffectivenessChart metrics={singleSourceMetrics} />);

      expect(screen.getByText('1 sources')).toBeInTheDocument();
    });
  });
});
