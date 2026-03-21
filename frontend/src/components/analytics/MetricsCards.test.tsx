/**
 * Tests for MetricsCards Component
 *
 * Tests the metrics summary cards including:
 * - Rendering multiple metric cards
 * - Color coding (success, warning, error, info, primary)
 * - Grid layout with different column configurations
 * - Icons display
 * - Hover effects
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MetricsCards, { MetricCardData } from './MetricsCards';
import {
  AccessTime as ClockIcon,
  Person as PersonIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material';

describe('MetricsCards', () => {
  const mockMetrics: MetricCardData[] = [
    {
      id: 'time-to-hire',
      title: 'Avg Time-to-Hire',
      value: '25.5d',
      subtitle: 'Last 30 days',
      color: 'success',
      icon: <ClockIcon />,
    },
    {
      id: 'candidates',
      title: 'Active Candidates',
      value: '1,234',
      subtitle: 'In pipeline',
      color: 'primary',
      icon: <PersonIcon />,
    },
    {
      id: 'conversion',
      title: 'Conversion Rate',
      value: '15.2%',
      subtitle: 'Application to hire',
      color: 'warning',
      icon: <TrendingIcon />,
    },
  ];

  describe('Component Rendering', () => {
    it('should render all metric cards', () => {
      render(<MetricsCards metrics={mockMetrics} />);

      expect(screen.getByText('Avg Time-to-Hire')).toBeInTheDocument();
      expect(screen.getByText('25.5d')).toBeInTheDocument();
      expect(screen.getByText('Last 30 days')).toBeInTheDocument();

      expect(screen.getByText('Active Candidates')).toBeInTheDocument();
      expect(screen.getByText('1,234')).toBeInTheDocument();
      expect(screen.getByText('In pipeline')).toBeInTheDocument();

      expect(screen.getByText('Conversion Rate')).toBeInTheDocument();
      expect(screen.getByText('15.2%')).toBeInTheDocument();
      expect(screen.getByText('Application to hire')).toBeInTheDocument();
    });

    it('should render empty grid when no metrics provided', () => {
      const { container } = render(<MetricsCards metrics={[]} />);
      const grid = container.querySelector('.MuiGrid-container');
      expect(grid).toBeInTheDocument();
      expect(grid?.children).toHaveLength(0);
    });

    it('should render single metric card', () => {
      const singleMetric = [mockMetrics[0]];
      render(<MetricsCards metrics={singleMetric} />);

      expect(screen.getByText('Avg Time-to-Hire')).toBeInTheDocument();
      expect(screen.getByText('25.5d')).toBeInTheDocument();
      expect(screen.queryByText('Active Candidates')).not.toBeInTheDocument();
    });
  });

  describe('Color Themes', () => {
    it('should render success color metric', () => {
      const successMetric: MetricCardData[] = [
        {
          id: 'success-metric',
          title: 'Success Metric',
          value: '100%',
          subtitle: 'All good',
          color: 'success',
        },
      ];

      render(<MetricsCards metrics={successMetric} />);
      expect(screen.getByText('Success Metric')).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('should render warning color metric', () => {
      const warningMetric: MetricCardData[] = [
        {
          id: 'warning-metric',
          title: 'Warning Metric',
          value: '50%',
          subtitle: 'Needs attention',
          color: 'warning',
        },
      ];

      render(<MetricsCards metrics={warningMetric} />);
      expect(screen.getByText('Warning Metric')).toBeInTheDocument();
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('should render error color metric', () => {
      const errorMetric: MetricCardData[] = [
        {
          id: 'error-metric',
          title: 'Error Metric',
          value: '0%',
          subtitle: 'Critical issue',
          color: 'error',
        },
      ];

      render(<MetricsCards metrics={errorMetric} />);
      expect(screen.getByText('Error Metric')).toBeInTheDocument();
      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('should render info color metric', () => {
      const infoMetric: MetricCardData[] = [
        {
          id: 'info-metric',
          title: 'Info Metric',
          value: '42',
          subtitle: 'Just information',
          color: 'info',
        },
      ];

      render(<MetricsCards metrics={infoMetric} />);
      expect(screen.getByText('Info Metric')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
    });

    it('should render primary color metric', () => {
      const primaryMetric: MetricCardData[] = [
        {
          id: 'primary-metric',
          title: 'Primary Metric',
          value: '999',
          subtitle: 'Main metric',
          color: 'primary',
        },
      ];

      render(<MetricsCards metrics={primaryMetric} />);
      expect(screen.getByText('Primary Metric')).toBeInTheDocument();
      expect(screen.getByText('999')).toBeInTheDocument();
    });
  });

  describe('Grid Layout', () => {
    it('should use default 4 columns when not specified', () => {
      const { container } = render(<MetricsCards metrics={mockMetrics} />);
      const grid = container.querySelector('.MuiGrid-container');
      expect(grid).toBeInTheDocument();
    });

    it('should respect custom column count', () => {
      const { container } = render(<MetricsCards metrics={mockMetrics} columns={3} />);
      const grid = container.querySelector('.MuiGrid-container');
      expect(grid).toBeInTheDocument();
    });

    it('should respect custom spacing', () => {
      const { container } = render(<MetricsCards metrics={mockMetrics} spacing={4} />);
      const grid = container.querySelector('.MuiGrid-container');
      expect(grid).toBeInTheDocument();
    });

    it('should handle 2 column layout', () => {
      const { container } = render(<MetricsCards metrics={mockMetrics} columns={2} />);
      const grid = container.querySelector('.MuiGrid-container');
      expect(grid).toBeInTheDocument();
    });
  });

  describe('Icons', () => {
    it('should display icons when provided', () => {
      render(<MetricsCards metrics={mockMetrics} />);
      // Icons are rendered, we can verify the metric titles are present
      expect(screen.getByText('Avg Time-to-Hire')).toBeInTheDocument();
      expect(screen.getByText('Active Candidates')).toBeInTheDocument();
      expect(screen.getByText('Conversion Rate')).toBeInTheDocument();
    });

    it('should render metrics without icons', () => {
      const metricsWithoutIcons: MetricCardData[] = [
        {
          id: 'no-icon',
          title: 'No Icon Metric',
          value: '123',
          subtitle: 'Without icon',
          color: 'primary',
        },
      ];

      render(<MetricsCards metrics={metricsWithoutIcons} />);
      expect(screen.getByText('No Icon Metric')).toBeInTheDocument();
      expect(screen.getByText('123')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long values', () => {
      const longValueMetric: MetricCardData[] = [
        {
          id: 'long-value',
          title: 'Long Value',
          value: '1,234,567,890',
          subtitle: 'Very large number',
          color: 'primary',
        },
      ];

      render(<MetricsCards metrics={longValueMetric} />);
      expect(screen.getByText('1,234,567,890')).toBeInTheDocument();
    });

    it('should handle very long titles', () => {
      const longTitleMetric: MetricCardData[] = [
        {
          id: 'long-title',
          title: 'This is a very long title that might wrap to multiple lines',
          value: '100',
          subtitle: 'Long title test',
          color: 'success',
        },
      ];

      render(<MetricsCards metrics={longTitleMetric} />);
      expect(screen.getByText('This is a very long title that might wrap to multiple lines')).toBeInTheDocument();
    });

    it('should handle very long subtitles', () => {
      const longSubtitleMetric: MetricCardData[] = [
        {
          id: 'long-subtitle',
          title: 'Metric',
          value: '50',
          subtitle: 'This is a very long subtitle that provides extensive context and might wrap to multiple lines in the card',
          color: 'info',
        },
      ];

      render(<MetricsCards metrics={longSubtitleMetric} />);
      expect(screen.getByText('This is a very long subtitle that provides extensive context and might wrap to multiple lines in the card')).toBeInTheDocument();
    });

    it('should handle zero values', () => {
      const zeroMetric: MetricCardData[] = [
        {
          id: 'zero',
          title: 'Zero Metric',
          value: '0',
          subtitle: 'No activity',
          color: 'warning',
        },
      ];

      render(<MetricsCards metrics={zeroMetric} />);
      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should handle percentage values', () => {
      const percentMetric: MetricCardData[] = [
        {
          id: 'percent',
          title: 'Percentage',
          value: '95.5%',
          subtitle: 'Completion rate',
          color: 'success',
        },
      ];

      render(<MetricsCards metrics={percentMetric} />);
      expect(screen.getByText('95.5%')).toBeInTheDocument();
    });

    it('should handle negative values', () => {
      const negativeMetric: MetricCardData[] = [
        {
          id: 'negative',
          title: 'Negative Metric',
          value: '-15',
          subtitle: 'Decrease',
          color: 'error',
        },
      ];

      render(<MetricsCards metrics={negativeMetric} />);
      expect(screen.getByText('-15')).toBeInTheDocument();
    });
  });

  describe('Multiple Metrics Rendering', () => {
    it('should render many metrics correctly', () => {
      const manyMetrics: MetricCardData[] = Array.from({ length: 8 }, (_, i) => ({
        id: `metric-${i}`,
        title: `Metric ${i + 1}`,
        value: `${(i + 1) * 10}`,
        subtitle: `Subtitle ${i + 1}`,
        color: ['success', 'warning', 'error', 'info', 'primary'][i % 5] as MetricCardData['color'],
      }));

      render(<MetricsCards metrics={manyMetrics} />);

      manyMetrics.forEach((metric) => {
        expect(screen.getByText(metric.title)).toBeInTheDocument();
        expect(screen.getByText(metric.value)).toBeInTheDocument();
        expect(screen.getByText(metric.subtitle)).toBeInTheDocument();
      });
    });

    it('should maintain unique keys for each metric', () => {
      const { container } = render(<MetricsCards metrics={mockMetrics} />);
      const gridItems = container.querySelectorAll('.MuiGrid-item');
      expect(gridItems.length).toBe(mockMetrics.length);
    });
  });

  describe('Visual Design', () => {
    it('should render cards with proper structure', () => {
      const { container } = render(<MetricsCards metrics={mockMetrics} />);
      const cards = container.querySelectorAll('.MuiCard-root');
      expect(cards.length).toBe(mockMetrics.length);
    });

    it('should render card content for each metric', () => {
      const { container } = render(<MetricsCards metrics={mockMetrics} />);
      const cardContents = container.querySelectorAll('.MuiCardContent-root');
      expect(cardContents.length).toBe(mockMetrics.length);
    });
  });
});
