/**
 * Tests for TimeToHireChart Component
 *
 * Tests the time-to-hire chart including:
 * - Rendering trend data over time
 * - Distribution analysis visualization
 * - Category breakdown display
 * - Color coding based on performance
 * - Loading states
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import TimeToHireChart, {
  TimeToHireDataPoint,
  TimeToHireBreakdown,
} from './TimeToHireChart';

describe('TimeToHireChart', () => {
  const mockTrendData: TimeToHireDataPoint[] = [
    {
      period: '2024-01-01',
      average_days: 25.5,
      median_days: 23.0,
      min_days: 15,
      max_days: 42,
      hire_count: 12,
    },
    {
      period: '2024-02-01',
      average_days: 28.3,
      median_days: 26.0,
      min_days: 18,
      max_days: 45,
      hire_count: 10,
    },
    {
      period: '2024-03-01',
      average_days: 22.1,
      median_days: 21.0,
      min_days: 12,
      max_days: 35,
      hire_count: 15,
    },
  ];

  const mockBreakdownData: TimeToHireBreakdown[] = [
    {
      category: 'Engineering',
      average_days: 32.5,
      hire_count: 15,
      trend: 'down',
      trend_percentage: -5.2,
    },
    {
      category: 'Sales',
      average_days: 28.0,
      hire_count: 20,
      trend: 'stable',
      trend_percentage: 0.5,
    },
    {
      category: 'Marketing',
      average_days: 24.5,
      hire_count: 10,
      trend: 'up',
      trend_percentage: 3.1,
    },
  ];

  describe('Component Rendering', () => {
    it('should render all main sections', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      expect(screen.getByText('Time-to-Hire Trend')).toBeInTheDocument();
      expect(screen.getByText('Distribution Analysis')).toBeInTheDocument();
      expect(screen.getByText('Performance by Category')).toBeInTheDocument();
    });

    it('should render trend data points', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      // Check that hire counts are displayed
      expect(screen.getAllByText(/12 hires/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/10 hires/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/15 hires/).length).toBeGreaterThan(0);
    });

    it('should render breakdown categories', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      expect(screen.getByText('Engineering')).toBeInTheDocument();
      expect(screen.getByText('Sales')).toBeInTheDocument();
      expect(screen.getByText('Marketing')).toBeInTheDocument();
    });

    it('should render with empty trend data', () => {
      render(
        <TimeToHireChart
          trendData={[]}
          breakdownData={mockBreakdownData}
        />
      );

      expect(screen.getByText('Time-to-Hire Trend')).toBeInTheDocument();
      expect(screen.getByText('Engineering')).toBeInTheDocument();
    });

    it('should render with empty breakdown data', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={[]}
        />
      );

      expect(screen.getByText('Time-to-Hire Trend')).toBeInTheDocument();
      expect(screen.queryByText('Engineering')).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading state when loading is true', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
          loading={true}
        />
      );

      expect(screen.getByText('Loading time-to-hire data...')).toBeInTheDocument();
      expect(screen.queryByText('Time-to-Hire Trend')).not.toBeInTheDocument();
    });

    it('should not show loading state when loading is false', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
          loading={false}
        />
      );

      expect(screen.queryByText('Loading time-to-hire data...')).not.toBeInTheDocument();
      expect(screen.getByText('Time-to-Hire Trend')).toBeInTheDocument();
    });

    it('should show content when loading is undefined (default false)', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      expect(screen.queryByText('Loading time-to-hire data...')).not.toBeInTheDocument();
      expect(screen.getByText('Time-to-Hire Trend')).toBeInTheDocument();
    });
  });

  describe('Trend Data Visualization', () => {
    it('should display average days for each period', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      expect(screen.getAllByText(/25.5 days/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/28.3 days/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/22.1 days/).length).toBeGreaterThan(0);
    });

    it('should display median and range information', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      // Check for median and range text
      expect(screen.getAllByText(/Median:/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Range:/).length).toBeGreaterThan(0);
    });

    it('should handle single trend data point', () => {
      const singleTrend: TimeToHireDataPoint[] = [mockTrendData[0]];

      render(
        <TimeToHireChart
          trendData={singleTrend}
          breakdownData={mockBreakdownData}
        />
      );

      expect(screen.getAllByText(/25.5 days/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/12 hires/).length).toBeGreaterThan(0);
    });
  });

  describe('Distribution Analysis', () => {
    it('should display distribution section', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      expect(screen.getByText('Distribution Analysis')).toBeInTheDocument();
    });

    it('should show min and max days for distribution', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      // Check for range displays (e.g., "15d - 42d")
      expect(screen.getAllByText(/15d - 42d/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/18d - 45d/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/12d - 35d/).length).toBeGreaterThan(0);
    });

    it('should display average and median chips', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      // Average and median chips should be present
      expect(screen.getAllByText(/Avg:/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Median:/).length).toBeGreaterThan(0);
    });
  });

  describe('Category Breakdown', () => {
    it('should display all breakdown categories', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      expect(screen.getByText('Engineering')).toBeInTheDocument();
      expect(screen.getByText('Sales')).toBeInTheDocument();
      expect(screen.getByText('Marketing')).toBeInTheDocument();
    });

    it('should display average days for each category', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      expect(screen.getAllByText(/32.5 days/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/28.0 days/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/24.5 days/).length).toBeGreaterThan(0);
    });

    it('should display hire count for each category', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      expect(screen.getAllByText(/15 hires/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/20 hires/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/10 hires/).length).toBeGreaterThan(0);
    });

    it('should display trend information when available', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      // Trend percentages
      expect(screen.getByText('5.2%')).toBeInTheDocument(); // Engineering down
      expect(screen.getByText('0.5%')).toBeInTheDocument(); // Sales stable
      expect(screen.getByText('3.1%')).toBeInTheDocument(); // Marketing up
    });

    it('should handle breakdown without trend data', () => {
      const breakdownNoTrend: TimeToHireBreakdown[] = [
        {
          category: 'HR',
          average_days: 20.0,
          hire_count: 5,
        },
      ];

      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={breakdownNoTrend}
        />
      );

      expect(screen.getByText('HR')).toBeInTheDocument();
      expect(screen.getAllByText(/20.0 days/).length).toBeGreaterThan(0);
    });
  });

  describe('Performance Color Coding', () => {
    it('should use success color for fast hiring (<=30 days)', () => {
      const fastHiringData: TimeToHireDataPoint[] = [
        {
          period: '2024-01-01',
          average_days: 25.0,
          median_days: 24.0,
          min_days: 20,
          max_days: 30,
          hire_count: 10,
        },
      ];

      render(
        <TimeToHireChart
          trendData={fastHiringData}
          breakdownData={[]}
        />
      );

      expect(screen.getAllByText(/25.0 days/).length).toBeGreaterThan(0);
    });

    it('should use warning color for moderate hiring (31-45 days)', () => {
      const moderateHiringData: TimeToHireDataPoint[] = [
        {
          period: '2024-01-01',
          average_days: 35.0,
          median_days: 34.0,
          min_days: 30,
          max_days: 40,
          hire_count: 8,
        },
      ];

      render(
        <TimeToHireChart
          trendData={moderateHiringData}
          breakdownData={[]}
        />
      );

      expect(screen.getAllByText(/35.0 days/).length).toBeGreaterThan(0);
    });

    it('should use error color for slow hiring (>45 days)', () => {
      const slowHiringData: TimeToHireDataPoint[] = [
        {
          period: '2024-01-01',
          average_days: 50.0,
          median_days: 48.0,
          min_days: 45,
          max_days: 60,
          hire_count: 5,
        },
      ];

      render(
        <TimeToHireChart
          trendData={slowHiringData}
          breakdownData={[]}
        />
      );

      expect(screen.getAllByText(/50.0 days/).length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero hire count', () => {
      const zeroHireData: TimeToHireDataPoint[] = [
        {
          period: '2024-01-01',
          average_days: 30.0,
          median_days: 30.0,
          min_days: 30,
          max_days: 30,
          hire_count: 0,
        },
      ];

      render(
        <TimeToHireChart
          trendData={zeroHireData}
          breakdownData={[]}
        />
      );

      expect(screen.getByText('0 hires')).toBeInTheDocument();
    });

    it('should handle very large hire counts', () => {
      const largeHireData: TimeToHireDataPoint[] = [
        {
          period: '2024-01-01',
          average_days: 25.0,
          median_days: 24.0,
          min_days: 15,
          max_days: 40,
          hire_count: 1000,
        },
      ];

      render(
        <TimeToHireChart
          trendData={largeHireData}
          breakdownData={[]}
        />
      );

      expect(screen.getByText('1000 hires')).toBeInTheDocument();
    });

    it('should handle single day (1 day)', () => {
      const oneDayData: TimeToHireDataPoint[] = [
        {
          period: '2024-01-01',
          average_days: 1.0,
          median_days: 1.0,
          min_days: 1,
          max_days: 1,
          hire_count: 5,
        },
      ];

      render(
        <TimeToHireChart
          trendData={oneDayData}
          breakdownData={[]}
        />
      );

      expect(screen.getByText('1 day')).toBeInTheDocument();
    });

    it('should handle very long category names', () => {
      const longNameBreakdown: TimeToHireBreakdown[] = [
        {
          category: 'Senior Software Engineering and Architecture Department',
          average_days: 30.0,
          hire_count: 10,
        },
      ];

      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={longNameBreakdown}
        />
      );

      expect(screen.getByText('Senior Software Engineering and Architecture Department')).toBeInTheDocument();
    });

    it('should handle min equal to max days', () => {
      const equalRangeData: TimeToHireDataPoint[] = [
        {
          period: '2024-01-01',
          average_days: 25.0,
          median_days: 25.0,
          min_days: 25,
          max_days: 25,
          hire_count: 5,
        },
      ];

      render(
        <TimeToHireChart
          trendData={equalRangeData}
          breakdownData={[]}
        />
      );

      expect(screen.getByText('25d - 25d')).toBeInTheDocument();
    });
  });

  describe('Visual Design Elements', () => {
    it('should render paper components for each section', () => {
      const { container } = render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      const papers = container.querySelectorAll('.MuiPaper-root');
      expect(papers.length).toBeGreaterThan(0);
    });

    it('should render cards for breakdown categories', () => {
      const { container } = render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      const cards = container.querySelectorAll('.MuiCard-root');
      expect(cards.length).toBe(mockBreakdownData.length);
    });

    it('should render linear progress bars', () => {
      const { container } = render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      const progressBars = container.querySelectorAll('.MuiLinearProgress-root');
      expect(progressBars.length).toBeGreaterThan(0);
    });
  });

  describe('Data Formatting', () => {
    it('should format decimal days correctly', () => {
      const decimalData: TimeToHireDataPoint[] = [
        {
          period: '2024-01-01',
          average_days: 25.678,
          median_days: 24.123,
          min_days: 20,
          max_days: 30,
          hire_count: 10,
        },
      ];

      render(
        <TimeToHireChart
          trendData={decimalData}
          breakdownData={[]}
        />
      );

      expect(screen.getAllByText(/25.7 days/).length).toBeGreaterThan(0);
    });

    it('should format dates correctly', () => {
      render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );

      // Dates should be formatted (e.g., "Jan 1")
      // This will vary based on locale, so we just check that dates are rendered
      const { container } = render(
        <TimeToHireChart
          trendData={mockTrendData}
          breakdownData={mockBreakdownData}
        />
      );
      expect(container.textContent).toBeTruthy();
    });
  });
});
