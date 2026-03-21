/**
 * Time-to-Hire Chart Component
 *
 * Displays time-to-hire metrics with visual charts showing hiring
 * performance trends, distribution, and breakdown by department or position.
 *
 * @module components/analytics/TimeToHireChart
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Stack,
  LinearProgress,
  Chip,
  Grid,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AccessTime as TimeIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';

/**
 * Time-to-hire data point for trend analysis
 */
export interface TimeToHireDataPoint {
  /** Period identifier (date or period label) */
  period: string;
  /** Average days to hire */
  average_days: number;
  /** Median days to hire */
  median_days: number;
  /** Minimum days to hire */
  min_days: number;
  /** Maximum days to hire */
  max_days: number;
  /** Number of hires in this period */
  hire_count: number;
}

/**
 * Time-to-hire breakdown by category (department/position)
 */
export interface TimeToHireBreakdown {
  /** Category name (e.g., department or position) */
  category: string;
  /** Average days to hire */
  average_days: number;
  /** Number of hires */
  hire_count: number;
  /** Trend direction compared to previous period */
  trend?: 'up' | 'down' | 'stable';
  /** Percentage change from previous period */
  trend_percentage?: number;
}

/**
 * Format date for display
 */
const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

/**
 * Format days for display
 */
const formatDays = (days: number): string => {
  if (days === 1) return '1 day';
  return `${days.toFixed(1)} days`;
};

/**
 * TimeToHireChart Component Props
 */
interface TimeToHireChartProps {
  /** Time-to-hire trend data over time */
  trendData: TimeToHireDataPoint[];
  /** Time-to-hire breakdown by category */
  breakdownData: TimeToHireBreakdown[];
  /** Loading state */
  loading?: boolean;
}

/**
 * TimeToHireChart Component
 *
 * Displays time-to-hire metrics with visual charts:
 * - Trend over time showing average and median
 * - Distribution showing min/max ranges
 * - Breakdown by department or position
 * - Performance indicators with color-coding
 *
 * @example
 * ```tsx
 * <TimeToHireChart
 *   trendData={trendData}
 *   breakdownData={breakdownData}
 * />
 * ```
 */
const TimeToHireChart: React.FC<TimeToHireChartProps> = ({
  trendData,
  breakdownData,
  loading = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Calculate max values for bar chart scaling
  const maxAverage = Math.max(...trendData.map((d) => d.average_days), 1);
  const maxCategoryAverage = Math.max(...breakdownData.map((b) => b.average_days), 1);

  // Get color based on days (green <= 30, yellow <= 45, red > 45)
  const getTimeColor = (days: number): 'success' | 'warning' | 'error' => {
    if (days <= 30) return 'success';
    if (days <= 45) return 'warning';
    return 'error';
  };

  // Get trend icon
  const getTrendIcon = (trend?: 'up' | 'down' | 'stable') => {
    if (trend === 'down') return <TrendingDownIcon fontSize="small" />;
    if (trend === 'up') return <TrendingUpIcon fontSize="small" />;
    return null;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <Stack alignItems="center" spacing={2}>
          <LinearProgress sx={{ width: '100%' }} />
          <Typography variant="body2" color="text.secondary">
            Loading time-to-hire data...
          </Typography>
        </Stack>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Time-to-Hire Trend Over Time */}
      <Grid item xs={12} md={6}>
        <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <TimelineIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Time-to-Hire Trend
            </Typography>
          </Box>

          <Stack spacing={2}>
            {trendData.map((data, index) => {
              const avgColor = getTimeColor(data.average_days);
              const barWidth = (data.average_days / maxAverage) * 100;

              return (
                <Box key={data.period}>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 0.5,
                    }}
                  >
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(data.period)}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <Typography variant="body2" fontWeight={600}>
                        {formatDays(data.average_days)}
                      </Typography>
                      <Chip
                        label={`${data.hire_count} hires`}
                        size="small"
                        variant="outlined"
                        sx={{ height: 20, fontSize: '0.7rem' }}
                      />
                    </Box>
                  </Box>

                  {/* Bar showing average time */}
                  <LinearProgress
                    variant="determinate"
                    value={barWidth}
                    sx={{
                      height: 8,
                      borderRadius: 1,
                      bgcolor: 'action.hover',
                      '& .MuiLinearProgress-bar': {
                        bgcolor: `${avgColor}.main`,
                      },
                    }}
                  />

                  {/* Median and range info */}
                  <Box sx={{ display: 'flex', gap: 2, mt: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      Median: {formatDays(data.median_days)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Range: {data.min_days}-{data.max_days}d
                    </Typography>
                  </Box>
                </Box>
              );
            })}
          </Stack>
        </Paper>
      </Grid>

      {/* Time-to-Hire Distribution */}
      <Grid item xs={12} md={6}>
        <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <TimeIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Distribution Analysis
            </Typography>
          </Box>

          <Stack spacing={2}>
            {trendData.map((data) => {
              const range = data.max_days - data.min_days;
              const q1Position = ((data.median_days - data.min_days) / range) * 100;

              return (
                <Box key={`dist-${data.period}`}>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 0.5,
                    }}
                  >
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(data.period)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {data.min_days}d - {data.max_days}d
                    </Typography>
                  </Box>

                  {/* Box plot visualization */}
                  <Box
                    sx={{
                      position: 'relative',
                      height: 24,
                      bgcolor: 'action.hover',
                      borderRadius: 1,
                      overflow: 'hidden',
                    }}
                  >
                    {/* Full range bar */}
                    <Box
                      sx={{
                        position: 'absolute',
                        left: 0,
                        right: 0,
                        height: '100%',
                        bgcolor: 'action.selected',
                      }}
                    />
                    {/* Median line */}
                    <Box
                      sx={{
                        position: 'absolute',
                        left: `${q1Position}%`,
                        height: '100%',
                        width: 3,
                        bgcolor: 'primary.main',
                      }}
                    />
                    {/* Average marker */}
                    <Box
                      sx={{
                        position: 'absolute',
                        left: `${((data.average_days - data.min_days) / range) * 100}%`,
                        height: '100%',
                        width: 3,
                        bgcolor: getTimeColor(data.average_days) + '.main',
                      }}
                    />
                  </Box>

                  <Box sx={{ display: 'flex', gap: 2, mt: 0.5 }}>
                    <Chip
                      label={`Avg: ${formatDays(data.average_days)}`}
                      size="small"
                      color={getTimeColor(data.average_days)}
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                    <Chip
                      label={`Median: ${formatDays(data.median_days)}`}
                      size="small"
                      color="primary"
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  </Box>
                </Box>
              );
            })}
          </Stack>
        </Paper>
      </Grid>

      {/* Breakdown by Category */}
      <Grid item xs={12}>
        <Paper elevation={1} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <TrendingUpIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Performance by Category
            </Typography>
          </Box>

          <Grid container spacing={2}>
            {breakdownData.map((breakdown) => {
              const timeColor = getTimeColor(breakdown.average_days);
              const trendIcon = getTrendIcon(breakdown.trend);

              return (
                <Grid item xs={12} sm={6} md={4} key={breakdown.category}>
                  <Card
                    variant="outlined"
                    sx={{
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 2,
                      },
                    }}
                  >
                    <CardContent sx={{ py: 2, px: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                        <Typography
                          variant="subtitle2"
                          fontWeight={600}
                          sx={{
                            flex: 1,
                            minWidth: 0,
                            color: 'text.primary',
                          }}
                        >
                          {breakdown.category}
                        </Typography>
                        {breakdown.trend && (
                          <Chip
                            icon={trendIcon || undefined}
                            label={breakdown.trend_percentage ? `${Math.abs(breakdown.trend_percentage).toFixed(1)}%` : breakdown.trend}
                            size="small"
                            color={breakdown.trend === 'down' ? 'success' : breakdown.trend === 'up' ? 'error' : 'default'}
                            variant="outlined"
                            sx={{ height: 20, fontSize: '0.7rem' }}
                          />
                        )}
                      </Box>

                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          Average Time-to-Hire
                        </Typography>
                        <Typography
                          variant="h5"
                          fontWeight={700}
                          color={`${timeColor}.main`}
                        >
                          {formatDays(breakdown.average_days)}
                        </Typography>
                      </Box>

                      <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                        <Chip
                          icon={<SuccessIcon fontSize="small" />}
                          label={`${breakdown.hire_count} hires`}
                          size="small"
                          color="primary"
                          variant="outlined"
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      </Box>

                      <LinearProgress
                        variant="determinate"
                        value={(breakdown.average_days / maxCategoryAverage) * 100}
                        sx={{
                          mt: 1.5,
                          height: 4,
                          borderRadius: 1,
                          bgcolor: 'action.hover',
                          '& .MuiLinearProgress-bar': {
                            bgcolor: `${timeColor}.main`,
                          },
                        }}
                      />
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default TimeToHireChart;
