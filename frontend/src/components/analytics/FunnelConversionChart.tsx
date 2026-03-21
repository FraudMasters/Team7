/**
 * Funnel Conversion Chart Component
 *
 * Displays funnel conversion metrics with visual charts showing conversion rates,
 * drop-off percentages, and stage-by-stage progression analysis.
 *
 * @module components/analytics/FunnelConversionChart
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
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  FilterList as FunnelIcon,
  Insights as InsightsIcon,
} from '@mui/icons-material';
import type { FunnelStage } from '@/types/api';

/**
 * Format stage name for display
 */
const formatStageName = (stageName: string): string => {
  const nameMap: Record<string, string> = {
    resumes_uploaded: 'Resumes Uploaded',
    resumes_processed: 'Resumes Processed',
    candidates_matched: 'Candidates Matched',
    candidates_shortlisted: 'Candidates Shortlisted',
    candidates_interviewed: 'Candidates Interviewed',
    candidates_hired: 'Candidates Hired',
  };
  return nameMap[stageName] || stageName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
};

/**
 * Format percentage for display
 */
const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Get color for conversion rate
 */
const getConversionColor = (rate: number): 'success' | 'warning' | 'error' => {
  if (rate >= 0.7) return 'success';
  if (rate >= 0.5) return 'warning';
  return 'error';
};

/**
 * Get color for drop-off rate
 */
const getDropOffColor = (rate: number): string => {
  if (rate <= 0.3) return 'success.main';
  if (rate <= 0.5) return 'warning.main';
  return 'error.main';
};

/**
 * FunnelConversionChart Component Props
 */
interface FunnelConversionChartProps {
  /** Funnel stages with conversion data */
  stages: FunnelStage[];
  /** Total count at start of funnel */
  totalCount: number;
  /** Loading state */
  loading?: boolean;
}

/**
 * FunnelConversionChart Component
 *
 * Displays funnel conversion metrics with visual charts:
 * - Conversion rates between consecutive stages
 * - Drop-off percentages showing candidate attrition
 * - Overall funnel health indicators
 * - Stage-by-stage performance comparison
 *
 * @example
 * ```tsx
 * <FunnelConversionChart
 *   stages={funnelStages}
 *   totalCount={1000}
 * />
 * ```
 */
const FunnelConversionChart: React.FC<FunnelConversionChartProps> = ({
  stages,
  totalCount,
  loading = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Calculate overall conversion rate (first to last stage)
  const overallConversionRate = stages.length > 0 && totalCount > 0
    ? stages[stages.length - 1].count / totalCount
    : 0;

  // Calculate average conversion rate across all stages
  const avgConversionRate = stages.length > 1
    ? stages.slice(1).reduce((sum, stage) => sum + stage.conversion_rate, 0) / (stages.length - 1)
    : 0;

  // Find the stage with worst conversion
  const worstConversionStage = stages.length > 1
    ? stages.slice(1).reduce((worst, stage) =>
        stage.conversion_rate < worst.conversion_rate ? stage : worst
      )
    : null;

  // Find the stage with best conversion (excluding first stage)
  const bestConversionStage = stages.length > 1
    ? stages.slice(1).reduce((best, stage) =>
        stage.conversion_rate > best.conversion_rate ? stage : best
      )
    : null;

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <Stack alignItems="center" spacing={2}>
          <LinearProgress sx={{ width: '100%' }} />
          <Typography variant="body2" color="text.secondary">
            Loading conversion data...
          </Typography>
        </Stack>
      </Box>
    );
  }

  if (stages.length === 0) {
    return (
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="body1" color="text.secondary" align="center">
          No funnel data available
        </Typography>
      </Paper>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Summary Cards */}
      <Grid item xs={12} md={4}>
        <Card elevation={2}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <FunnelIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="subtitle2" color="text.secondary">
                Overall Conversion
              </Typography>
            </Box>
            <Typography variant="h3" fontWeight={700} color="primary.main">
              {formatPercentage(overallConversionRate)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              First to final stage
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card elevation={2}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <InsightsIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="subtitle2" color="text.secondary">
                Average Stage Conversion
              </Typography>
            </Box>
            <Typography variant="h3" fontWeight={700} color="primary.main">
              {formatPercentage(avgConversionRate)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Across {stages.length - 1} transitions
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card elevation={2}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <WarningIcon color="warning" sx={{ mr: 1 }} />
              <Typography variant="subtitle2" color="text.secondary">
                Total Drop-off
              </Typography>
            </Box>
            <Typography variant="h3" fontWeight={700} color="warning.main">
              {formatPercentage(1 - overallConversionRate)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {((1 - overallConversionRate) * totalCount).toFixed(0)} candidates lost
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Conversion Rate Details */}
      <Grid item xs={12}>
        <Paper elevation={1} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <TrendingUpIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Stage-by-Stage Conversion Rates
            </Typography>
          </Box>

          <Stack spacing={3}>
            {stages.map((stage, index) => {
              if (index === 0) {
                // First stage - no conversion rate to show
                return (
                  <Box key={stage.stage_name}>
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        mb: 1,
                      }}
                    >
                      <Typography variant="subtitle1" fontWeight={600}>
                        {formatStageName(stage.stage_name)}
                      </Typography>
                      <Box sx={{ textAlign: 'right' }}>
                        <Typography variant="h6" fontWeight={700}>
                          {stage.count.toLocaleString()}
                        </Typography>
                        <Chip
                          label="Starting Point"
                          size="small"
                          color="info"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem' }}
                        />
                      </Box>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={100}
                      sx={{
                        height: 10,
                        borderRadius: 1,
                        bgcolor: 'action.hover',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: 'info.main',
                        },
                      }}
                    />
                  </Box>
                );
              }

              const previousStage = stages[index - 1];
              const dropOffCount = previousStage.count - stage.count;
              const dropOffRate = 1 - stage.conversion_rate;

              return (
                <Box key={stage.stage_name}>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 1,
                    }}
                  >
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {formatStageName(stage.stage_name)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        From {formatStageName(previousStage.stage_name)}
                      </Typography>
                    </Box>

                    <Box sx={{ textAlign: 'right', minWidth: 180 }}>
                      <Typography variant="h6" fontWeight={700}>
                        {stage.count.toLocaleString()}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                        <Chip
                          label={formatPercentage(stage.conversion_rate)}
                          size="small"
                          color={getConversionColor(stage.conversion_rate)}
                          icon={
                            stage.conversion_rate >= 0.7 ? (
                              <SuccessIcon />
                            ) : (
                              <WarningIcon />
                            )
                          }
                          sx={{ fontSize: '0.75rem' }}
                        />
                        {stage.conversion_rate >= avgConversionRate ? (
                          <TrendingUpIcon fontSize="small" color="success" />
                        ) : (
                          <TrendingDownIcon fontSize="small" color="error" />
                        )}
                      </Box>
                    </Box>
                  </Box>

                  {/* Conversion Bar */}
                  <Box sx={{ mb: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={stage.conversion_rate * 100}
                      sx={{
                        height: 10,
                        borderRadius: 1,
                        bgcolor: 'action.hover',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: getDropOffColor(dropOffRate),
                        },
                      }}
                    />
                  </Box>

                  {/* Drop-off Information */}
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <Typography variant="caption" color="text.secondary">
                      {dropOffCount.toLocaleString()} candidates dropped ({formatPercentage(dropOffRate)})
                    </Typography>
                    {stage.conversion_rate < avgConversionRate && (
                      <Chip
                        label="Below Average"
                        size="small"
                        color="warning"
                        variant="outlined"
                        sx={{ fontSize: '0.65rem', height: 18 }}
                      />
                    )}
                    {stage.conversion_rate >= avgConversionRate && (
                      <Chip
                        label="Above Average"
                        size="small"
                        color="success"
                        variant="outlined"
                        sx={{ fontSize: '0.65rem', height: 18 }}
                      />
                    )}
                  </Box>
                </Box>
              );
            })}
          </Stack>
        </Paper>
      </Grid>

      {/* Insights */}
      <Grid item xs={12} md={6}>
        <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <SuccessIcon color="success" sx={{ mr: 1 }} />
            <Typography variant="subtitle1" fontWeight={600}>
              Best Performing Stage
            </Typography>
          </Box>
          {bestConversionStage ? (
            <Box>
              <Typography variant="h5" fontWeight={700} color="success.main">
                {formatStageName(bestConversionStage.stage_name)}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {formatPercentage(bestConversionStage.conversion_rate)} conversion rate
              </Typography>
              <Chip
                label={`+${formatPercentage(bestConversionStage.conversion_rate - avgConversionRate)} vs avg`}
                size="small"
                color="success"
                sx={{ mt: 1, fontSize: '0.75rem' }}
              />
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Not enough data
            </Typography>
          )}
        </Paper>
      </Grid>

      <Grid item xs={12} md={6}>
        <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <WarningIcon color="warning" sx={{ mr: 1 }} />
            <Typography variant="subtitle1" fontWeight={600}>
              Needs Attention
            </Typography>
          </Box>
          {worstConversionStage ? (
            <Box>
              <Typography variant="h5" fontWeight={700} color="warning.main">
                {formatStageName(worstConversionStage.stage_name)}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {formatPercentage(worstConversionStage.conversion_rate)} conversion rate
              </Typography>
              <Chip
                label={`${formatPercentage(worstConversionStage.conversion_rate - avgConversionRate)} vs avg`}
                size="small"
                color="warning"
                sx={{ mt: 1, fontSize: '0.75rem' }}
              />
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Not enough data
            </Typography>
          )}
        </Paper>
      </Grid>
    </Grid>
  );
};

export default FunnelConversionChart;
