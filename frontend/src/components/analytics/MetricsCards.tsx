import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
} from '@mui/material';

/**
 * Single metric card data
 */
export interface MetricCardData {
  /** Unique identifier for the metric */
  id: string;
  /** Title of the metric */
  title: string;
  /** Main value to display */
  value: string;
  /** Subtitle or description */
  subtitle: string;
  /** Color theme for the metric */
  color: 'success' | 'warning' | 'error' | 'info' | 'primary';
  /** Optional icon to display */
  icon?: React.ReactNode;
}

/**
 * Props for MetricCard component
 */
interface MetricCardProps {
  /** Metric data to display */
  data: MetricCardData;
}

/**
 * Individual metric card component
 */
const MetricCard: React.FC<MetricCardProps> = ({ data }) => {
  const getColor = () => {
    switch (data.color) {
      case 'success': return '#2e7d32';
      case 'warning': return '#ed6c02';
      case 'error': return '#d32f2f';
      case 'info': return '#0288d1';
      case 'primary': return '#1976d2';
      default: return '#1976d2';
    }
  };

  return (
    <Card
      sx={{
        height: '100%',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 4,
        },
      }}
    >
      <CardContent sx={{ pb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
          {data.icon && <Box sx={{ fontSize: 14, color: getColor() }}>{data.icon}</Box>}
          <Typography variant="caption" color="text.secondary">
            {data.title}
          </Typography>
        </Box>
        <Typography variant="h6" fontWeight={600} color={getColor()} sx={{ lineHeight: 1.2 }}>
          {data.value}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.65rem' }}>
          {data.subtitle}
        </Typography>
      </CardContent>
    </Card>
  );
};

/**
 * Props for MetricsCards component
 */
export interface MetricsCardsProps {
  /** Array of metric cards to display */
  metrics: MetricCardData[];
  /** Number of columns in the grid (default: 4) */
  columns?: number;
  /** Spacing between cards (default: 2) */
  spacing?: number;
}

/**
 * MetricsCards Component
 *
 * Displays a grid of metric summary cards with title, value, subtitle, color, and optional icon.
 * Reusable component for showing key metrics across analytics dashboards.
 *
 * @example
 * ```tsx
 * const metrics = [
 *   {
 *     id: 'time-to-hire',
 *     title: 'Avg Time-to-Hire',
 *     value: '25.5d',
 *     subtitle: 'Last 30 days',
 *     color: 'success',
 *     icon: <ClockIcon />
 *   },
 *   {
 *     id: 'candidates',
 *     title: 'Active Candidates',
 *     value: '1,234',
 *     subtitle: 'In pipeline',
 *     color: 'primary',
 *     icon: <PersonIcon />
 *   }
 * ];
 *
 * <MetricsCards metrics={metrics} columns={3} />
 * ```
 */
const MetricsCards: React.FC<MetricsCardsProps> = ({
  metrics,
  columns = 4,
  spacing = 2,
}) => {
  // Calculate responsive grid columns
  const gridColumns = {
    xs: 12,
    sm: columns >= 3 ? 6 : 12,
    md: columns >= 4 ? 3 : columns === 3 ? 4 : 6,
    lg: 12 / columns,
  };

  return (
    <Grid container spacing={spacing}>
      {metrics.map((metric) => (
        <Grid
          key={metric.id}
          item
          xs={gridColumns.xs}
          sm={gridColumns.sm}
          md={gridColumns.md}
          lg={gridColumns.lg}
        >
          <MetricCard data={metric} />
        </Grid>
      ))}
    </Grid>
  );
};

export default MetricsCards;
