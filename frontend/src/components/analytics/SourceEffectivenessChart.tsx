/**
 * Source Effectiveness Chart Component
 *
 * Displays source effectiveness metrics with visual charts showing application
 * volumes, conversion rates, quality scores, and cost effectiveness across
 * different recruiting sources.
 *
 * @module components/analytics/SourceEffectivenessChart
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
  EmojiEvents as TrophyIcon,
  AttachMoney as MoneyIcon,
  People as PeopleIcon,
  Star as QualityIcon,
  Schedule as TimeIcon,
} from '@mui/icons-material';

/**
 * Format currency for display
 */
const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * Format percentage for display
 */
const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Format days for display
 */
const formatDays = (days: number): string => {
  return `${days.toFixed(0)}d`;
};

/**
 * Source metrics data
 */
export interface SourceMetrics {
  source_type: string;
  source_name: string;
  total_applications: number;
  hired_count: number;
  conversion_rate: number;
  average_quality_score?: number;
  average_cost_per_application?: number;
  total_cost?: number;
  cost_per_hire?: number;
  average_time_to_hire_days?: number;
}

/**
 * Source effectiveness metrics
 */
export interface SourceEffectivenessMetrics {
  sources: SourceMetrics[];
  total_applications: number;
  total_hired: number;
  overall_conversion_rate: number;
  best_source_by_conversion?: string;
  best_source_by_quality?: string;
  best_source_by_cost?: string;
  total_recruiting_cost?: number;
  average_cost_per_hire?: number;
}

/**
 * SourceEffectivenessChart Component Props
 */
interface SourceEffectivenessChartProps {
  /** Source effectiveness metrics data */
  metrics: SourceEffectivenessMetrics;
  /** Loading state */
  loading?: boolean;
}

/**
 * SourceEffectivenessChart Component
 *
 * Displays source effectiveness metrics with visual charts:
 * - Application volume by source
 * - Conversion rates (hired/applications)
 * - Quality scores comparison
 * - Cost effectiveness (cost per hire)
 * - Time to hire by source
 *
 * @example
 * ```tsx
 * <SourceEffectivenessChart
 *   metrics={sourceEffectivenessMetrics}
 * />
 * ```
 */
const SourceEffectivenessChart: React.FC<SourceEffectivenessChartProps> = ({
  metrics,
  loading = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Calculate max values for bar chart scaling
  const maxApplications = Math.max(...metrics.sources.map((s) => s.total_applications), 1);
  const maxConversionRate = Math.max(...metrics.sources.map((s) => s.conversion_rate), 0.01);
  const maxQualityScore = Math.max(
    ...metrics.sources.map((s) => s.average_quality_score || 0),
    1
  );
  const maxCostPerHire = Math.max(...metrics.sources.map((s) => s.cost_per_hire || 0), 1);

  // Get color based on conversion rate performance
  const getConversionColor = (rate: number): string => {
    if (rate >= 0.15) return theme.palette.success.main;
    if (rate >= 0.08) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  // Get color based on quality score
  const getQualityColor = (score?: number): string => {
    if (!score) return theme.palette.grey[400];
    if (score >= 80) return theme.palette.success.main;
    if (score >= 70) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  // Get color based on cost effectiveness (lower is better)
  const getCostColor = (cost?: number): string => {
    if (!cost) return theme.palette.grey[400];
    if (cost <= 50) return theme.palette.success.main;
    if (cost <= 100) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <Stack alignItems="center" spacing={2}>
          <LinearProgress sx={{ width: '100%' }} />
          <Typography variant="body2" color="text.secondary">
            Loading source effectiveness data...
          </Typography>
        </Stack>
      </Box>
    );
  }

  if (!metrics.sources || metrics.sources.length === 0) {
    return (
      <Box sx={{ py: 4, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No source effectiveness data available
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Summary Cards */}
      <Grid item xs={12}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Card elevation={1}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <PeopleIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="caption" color="text.secondary">
                    Total Applications
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight={600}>
                  {metrics.total_applications.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {metrics.sources.length} sources
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card elevation={1}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                  <Typography variant="caption" color="text.secondary">
                    Overall Conversion
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight={600} color="success.main">
                  {formatPercentage(metrics.overall_conversion_rate)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {metrics.total_hired} hired
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card elevation={1}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <MoneyIcon color="warning" sx={{ mr: 1 }} />
                  <Typography variant="caption" color="text.secondary">
                    Avg Cost Per Hire
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight={600}>
                  {metrics.average_cost_per_hire
                    ? formatCurrency(metrics.average_cost_per_hire)
                    : 'N/A'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {metrics.total_recruiting_cost
                    ? `Total: ${formatCurrency(metrics.total_recruiting_cost)}`
                    : 'No cost data'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card elevation={1}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <TrophyIcon color="info" sx={{ mr: 1 }} />
                  <Typography variant="caption" color="text.secondary">
                    Best Source
                  </Typography>
                </Box>
                <Typography variant="h6" fontWeight={600} noWrap>
                  {metrics.best_source_by_conversion || 'N/A'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  by conversion rate
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Grid>

      {/* Application Volume */}
      <Grid item xs={12} md={6}>
        <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <PeopleIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Application Volume
            </Typography>
          </Box>

          <Stack spacing={2}>
            {metrics.sources.map((source, index) => {
              const percentage = (source.total_applications / maxApplications) * 100;

              return (
                <Box key={`${source.source_name}-${index}`}>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 0.5,
                    }}
                  >
                    <Typography variant="body2" fontWeight={500}>
                      {source.source_name}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" fontWeight={600}>
                        {source.total_applications.toLocaleString()}
                      </Typography>
                      <Chip
                        label={source.source_type}
                        size="small"
                        sx={{ fontSize: '0.7rem', height: 20 }}
                      />
                    </Box>
                  </Box>

                  <LinearProgress
                    variant="determinate"
                    value={percentage}
                    sx={{
                      height: 8,
                      borderRadius: 1,
                      bgcolor: 'action.hover',
                      '& .MuiLinearProgress-bar': {
                        bgcolor: 'primary.main',
                      },
                    }}
                  />

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      Hired: {source.hired_count}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatPercentage(percentage / 100)} of total
                    </Typography>
                  </Box>
                </Box>
              );
            })}
          </Stack>
        </Paper>
      </Grid>

      {/* Conversion Rates */}
      <Grid item xs={12} md={6}>
        <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <TrendingUpIcon color="success" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Conversion Rates
            </Typography>
          </Box>

          <Stack spacing={2}>
            {metrics.sources
              .slice()
              .sort((a, b) => b.conversion_rate - a.conversion_rate)
              .map((source, index) => {
                const percentage = (source.conversion_rate / maxConversionRate) * 100;
                const color = getConversionColor(source.conversion_rate);

                return (
                  <Box key={`${source.source_name}-conv-${index}`}>
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        mb: 0.5,
                      }}
                    >
                      <Typography variant="body2" fontWeight={500}>
                        {source.source_name}
                      </Typography>
                      <Typography variant="body2" fontWeight={600} sx={{ color }}>
                        {formatPercentage(source.conversion_rate)}
                      </Typography>
                    </Box>

                    <LinearProgress
                      variant="determinate"
                      value={percentage}
                      sx={{
                        height: 8,
                        borderRadius: 1,
                        bgcolor: 'action.hover',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: color,
                        },
                      }}
                    />

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        {source.hired_count} of {source.total_applications} applications
                      </Typography>
                      {index === 0 && (
                        <Chip
                          icon={<TrophyIcon />}
                          label="Best"
                          size="small"
                          color="success"
                          sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                      )}
                    </Box>
                  </Box>
                );
              })}
          </Stack>
        </Paper>
      </Grid>

      {/* Quality Scores */}
      <Grid item xs={12} md={6}>
        <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <QualityIcon color="warning" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Quality Scores
            </Typography>
          </Box>

          <Stack spacing={2}>
            {metrics.sources
              .slice()
              .sort((a, b) => (b.average_quality_score || 0) - (a.average_quality_score || 0))
              .map((source, index) => {
                const score = source.average_quality_score || 0;
                const percentage = score > 0 ? (score / 100) * 100 : 0;
                const color = getQualityColor(score);
                const isTopQuality =
                  metrics.best_source_by_quality &&
                  source.source_name === metrics.best_source_by_quality;

                return (
                  <Box key={`${source.source_name}-qual-${index}`}>
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        mb: 0.5,
                      }}
                    >
                      <Typography variant="body2" fontWeight={500}>
                        {source.source_name}
                      </Typography>
                      <Typography variant="body2" fontWeight={600} sx={{ color }}>
                        {score > 0 ? score.toFixed(1) : 'N/A'}
                      </Typography>
                    </Box>

                    <LinearProgress
                      variant="determinate"
                      value={percentage}
                      sx={{
                        height: 8,
                        borderRadius: 1,
                        bgcolor: 'action.hover',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: color,
                        },
                      }}
                    />

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Average candidate quality
                      </Typography>
                      {isTopQuality && (
                        <Chip
                          icon={<TrophyIcon />}
                          label="Highest Quality"
                          size="small"
                          color="warning"
                          sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                      )}
                    </Box>
                  </Box>
                );
              })}
          </Stack>
        </Paper>
      </Grid>

      {/* Cost Effectiveness */}
      <Grid item xs={12} md={6}>
        <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <MoneyIcon color="error" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Cost Per Hire
            </Typography>
          </Box>

          <Stack spacing={2}>
            {metrics.sources
              .slice()
              .filter((s) => s.cost_per_hire !== undefined && s.cost_per_hire > 0)
              .sort((a, b) => (a.cost_per_hire || 0) - (b.cost_per_hire || 0))
              .map((source, index) => {
                const cost = source.cost_per_hire || 0;
                const percentage = (cost / maxCostPerHire) * 100;
                const color = getCostColor(cost);
                const isLowestCost =
                  metrics.best_source_by_cost && source.source_name === metrics.best_source_by_cost;

                return (
                  <Box key={`${source.source_name}-cost-${index}`}>
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        mb: 0.5,
                      }}
                    >
                      <Typography variant="body2" fontWeight={500}>
                        {source.source_name}
                      </Typography>
                      <Typography variant="body2" fontWeight={600} sx={{ color }}>
                        {formatCurrency(cost)}
                      </Typography>
                    </Box>

                    <LinearProgress
                      variant="determinate"
                      value={percentage}
                      sx={{
                        height: 8,
                        borderRadius: 1,
                        bgcolor: 'action.hover',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: color,
                        },
                      }}
                    />

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        {source.total_cost ? `Total: ${formatCurrency(source.total_cost)}` : 'Cost data available'}
                      </Typography>
                      {isLowestCost && (
                        <Chip
                          icon={<TrophyIcon />}
                          label="Most Efficient"
                          size="small"
                          color="success"
                          sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                      )}
                    </Box>

                    {source.average_time_to_hire_days && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                        <TimeIcon fontSize="small" sx={{ color: 'text.secondary' }} />
                        <Typography variant="caption" color="text.secondary">
                          Avg time to hire: {formatDays(source.average_time_to_hire_days)}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                );
              })}
            {metrics.sources.every((s) => !s.cost_per_hire || s.cost_per_hire === 0) && (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                No cost data available for sources
              </Typography>
            )}
          </Stack>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default SourceEffectivenessChart;
