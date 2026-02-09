import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Stack,
  Card,
  CardContent,
  Grid,
  Tooltip,
  Chip,
  Divider,
  Alert,
  AlertTitle,
} from '@mui/material';
import {
  BarChart as BarChartIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';

/**
 * Demographic metric data for bias chart
 */
export interface DemographicMetricData {
  /** Name of the demographic group (e.g., "Female", "Age 25-34") */
  demographic_group: string;
  /** Protected attribute category (e.g., "gender", "age_group") */
  protected_attribute: string;
  /** Disparate impact ratio (0-1, where 0.8 is the legal threshold) */
  disparate_impact_ratio: number;
  /** Statistical parity difference (0-1) */
  statistical_parity_difference: number;
  /** Selection rate for this group (0-1) */
  group_selection_rate: number;
  /** Overall selection rate across all groups (0-1) */
  overall_selection_rate: number;
  /** Sample size for this demographic group */
  sample_size: number;
  /** Whether the metric meets the 80% threshold */
  is_acceptable: boolean;
  /** Optional recommendation text */
  recommendation?: string;
}

/**
 * BiasMetricsChart Component Props
 */
export interface BiasMetricsChartProps {
  /** Array of demographic metrics to visualize */
  metrics: DemographicMetricData[];
  /** Optional title for the chart */
  title?: string;
  /** Optional description subtitle */
  description?: string;
  /** Whether to show detailed tooltips */
  showDetails?: boolean;
}

/**
 * Get severity level based on disparate impact ratio
 */
function getSeverityLevel(ratio: number): 'critical' | 'high' | 'medium' | 'low' | 'acceptable' {
  if (ratio < 0.5) return 'critical';
  if (ratio < 0.65) return 'high';
  if (ratio < 0.75) return 'medium';
  if (ratio < 0.8) return 'low';
  return 'acceptable';
}

/**
 * Get color based on disparate impact ratio
 */
function getSeverityColor(ratio: number): 'error' | 'warning' | 'info' | 'success' {
  if (ratio < 0.5) return 'error';
  if (ratio < 0.65) return 'error';
  if (ratio < 0.75) return 'warning';
  if (ratio < 0.8) return 'info';
  return 'success';
}

/**
 * Get severity icon
 */
function getSeverityIcon(ratio: number) {
  if (ratio < 0.5) return <ErrorIcon fontSize="small" />;
  if (ratio < 0.65) return <ErrorIcon fontSize="small" />;
  if (ratio < 0.75) return <WarningIcon fontSize="small" />;
  if (ratio < 0.8) return <InfoIcon fontSize="small" />;
  return <CheckIcon fontSize="small" />;
}

/**
 * Get bar color for disparate impact visualization
 */
function getBarColor(ratio: number): string {
  if (ratio < 0.5) return '#d32f2f'; // red
  if (ratio < 0.65) return '#f57c00'; // orange
  if (ratio < 0.75) return '#fbc02d'; // yellow
  if (ratio < 0.8) return '#1976d2'; // blue
  return '#388e3c'; // green
}

/**
 * BiasMetricsChart Component
 *
 * Visualizes disparate impact ratios across demographic groups with:
 * - Horizontal bar chart showing disparate impact ratios
 * - 80% threshold reference line (4/5ths rule)
 * - Color coding based on bias severity
 * - Detailed tooltips on hover
 *
 * @example
 * ```tsx
 * const metrics = [
 *   {
 *     demographic_group: 'Female',
 *     protected_attribute: 'gender',
 *     disparate_impact_ratio: 0.75,
 *     statistical_parity_difference: 0.15,
 *     group_selection_rate: 0.35,
 *     overall_selection_rate: 0.45,
 *     sample_size: 150,
 *     is_acceptable: false,
 *   },
 *   {
 *     demographic_group: 'Male',
 *     protected_attribute: 'gender',
 *     disparate_impact_ratio: 0.92,
 *     statistical_parity_difference: 0.02,
 *     group_selection_rate: 0.48,
 *     overall_selection_rate: 0.45,
 *     sample_size: 180,
 *     is_acceptable: true,
 *   },
 * ];
 * <BiasMetricsChart metrics={metrics} />
 * ```
 */
const BiasMetricsChart: React.FC<BiasMetricsChartProps> = ({
  metrics,
  title = 'Disparate Impact Analysis',
  description = 'Visual representation of selection rates across demographic groups compared to the 80% threshold (4/5ths rule)',
  showDetails = true,
}) => {
  /**
   * Calculate percentage for display
   */
  const toPercentage = (value: number): string => (value * 100).toFixed(1);

  /**
   * Calculate the maximum ratio for chart scaling
   */
  const maxRatio = React.useMemo(
    () => Math.max(...metrics.map((m) => m.disparate_impact_ratio), 1.0),
    [metrics]
  );

  /**
   * Count metrics by severity
   */
  const severityCounts = React.useMemo(() => {
    const counts = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      acceptable: 0,
    };
    metrics.forEach((m) => {
      const severity = getSeverityLevel(m.disparate_impact_ratio);
      counts[severity]++;
    });
    return counts;
  }, [metrics]);

  /**
   * Render empty state
   */
  if (!metrics || metrics.length === 0) {
    return (
      <Paper elevation={1} sx={{ p: 3, textAlign: 'center' }}>
        <BarChartIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="body2" color="text.secondary">
          No demographic metrics available
        </Typography>
      </Paper>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <BarChartIcon color="primary" />
          <Typography variant="h5" fontWeight={700}>
            {title}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      </Box>

      {/* Summary Cards */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={6} sm={2.4}>
            <Card
              variant="outlined"
              sx={{
                borderColor: severityCounts.critical > 0 ? 'error.main' : 'divider',
                bgcolor: severityCounts.critical > 0 ? 'error.50' : 'background.paper',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="error.main" fontWeight={700}>
                  {severityCounts.critical}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Critical
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={2.4}>
            <Card
              variant="outlined"
              sx={{
                borderColor: severityCounts.high > 0 ? 'error.main' : 'divider',
                bgcolor: severityCounts.high > 0 ? 'error.50' : 'background.paper',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="error.main" fontWeight={700}>
                  {severityCounts.high}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  High
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={2.4}>
            <Card
              variant="outlined"
              sx={{
                borderColor: severityCounts.medium > 0 ? 'warning.main' : 'divider',
                bgcolor: severityCounts.medium > 0 ? 'warning.50' : 'background.paper',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="warning.main" fontWeight={700}>
                  {severityCounts.medium}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Medium
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={2.4}>
            <Card
              variant="outlined"
              sx={{
                borderColor: severityCounts.low > 0 ? 'info.main' : 'divider',
                bgcolor: severityCounts.low > 0 ? 'info.50' : 'background.paper',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {severityCounts.low}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Low
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={2.4}>
            <Card
              variant="outlined"
              sx={{
                borderColor: 'success.main',
                bgcolor: 'success.50',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {severityCounts.acceptable}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Acceptable
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* 4/5ths Rule Info Alert */}
      <Alert severity="info" icon={<InfoIcon />}>
        <AlertTitle>Understanding the 4/5ths Rule</AlertTitle>
        <Typography variant="body2">
          The <strong>4/5ths rule</strong> is a guideline used by the EEOC to assess potential adverse impact.
          A selection rate for any demographic group that is less than <strong>80% (0.8)</strong> of the
          highest group's rate may indicate disparate impact. Values below this threshold are highlighted
          in color to indicate potential bias concerns.
        </Typography>
      </Alert>

      {/* Bar Chart */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Disparate Impact Ratios by Demographic
        </Typography>

        <Stack spacing={2} sx={{ mt: 3 }}>
          {metrics.map((metric, index) => {
            const severity = getSeverityLevel(metric.disparate_impact_ratio);
            const severityColor = getSeverityColor(metric.disparate_impact_ratio);
            const barColor = getBarColor(metric.disparate_impact_ratio);

            return (
              <Card
                key={`${metric.demographic_group}-${index}`}
                variant="outlined"
                sx={{
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateX(4px)',
                    boxShadow: 2,
                  },
                  borderLeft: 4,
                  borderLeftColor: `${severityColor}.main`,
                }}
              >
                <CardContent sx={{ py: 2 }}>
                  <Grid container spacing={2} alignItems="center">
                    {/* Demographic Info */}
                    <Grid item xs={12} sm={3.5}>
                      <Stack spacing={0.5}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Typography variant="subtitle1" fontWeight={600}>
                            {metric.demographic_group}
                          </Typography>
                          <Box sx={{ color: `${severityColor}.main` }}>
                            {getSeverityIcon(metric.disparate_impact_ratio)}
                          </Box>
                        </Box>
                        <Chip
                          label={metric.protected_attribute}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem', height: 20, width: 'fit-content' }}
                        />
                        {showDetails && (
                          <Typography variant="caption" color="text.secondary">
                            n = {metric.sample_size}
                          </Typography>
                        )}
                      </Stack>
                    </Grid>

                    {/* Bar Chart with Threshold Line */}
                    <Grid item xs={12} sm={6.5}>
                      <Tooltip
                        title={
                          <React.Fragment>
                            <Typography variant="body2" fontWeight={600}>
                              {metric.demographic_group} Details
                            </Typography>
                            <Divider sx={{ my: 0.5, bgcolor: 'white' }} />
                            <Typography variant="caption" display="block">
                              Disparate Impact: {toPercentage(metric.disparate_impact_ratio)}%
                            </Typography>
                            <Typography variant="caption" display="block">
                              Selection Rate: {toPercentage(metric.group_selection_rate)}%
                            </Typography>
                            <Typography variant="caption" display="block">
                              Overall Rate: {toPercentage(metric.overall_selection_rate)}%
                            </Typography>
                            <Typography variant="caption" display="block">
                              Parity Difference: {toPercentage(metric.statistical_parity_difference)}%
                            </Typography>
                            <Typography variant="caption" display="block">
                              Sample Size: {metric.sample_size}
                            </Typography>
                            {metric.recommendation && (
                              <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                                {metric.recommendation}
                              </Typography>
                            )}
                          </React.Fragment>
                        }
                        arrow
                      >
                        <Box>
                          {/* Disparate Impact Bar */}
                          <Box
                            sx={{
                              position: 'relative',
                              height: 32,
                              borderRadius: 1,
                              bgcolor: 'action.hover',
                              overflow: 'hidden',
                            }}
                          >
                            {/* Actual value bar */}
                            <Box
                              sx={{
                                position: 'absolute',
                                left: 0,
                                top: 0,
                                bottom: 0,
                                width: `${Math.min((metric.disparate_impact_ratio / maxRatio) * 100, 100)}%`,
                                bgcolor: barColor,
                                transition: 'width 0.5s ease-in-out',
                              }}
                            />

                            {/* 80% threshold line */}
                            <Box
                              sx={{
                                position: 'absolute',
                                left: `${Math.min((0.8 / maxRatio) * 100, 100)}%`,
                                top: 0,
                                bottom: 0,
                                width: 2,
                                bgcolor: 'black',
                                zIndex: 1,
                              }}
                            />

                            {/* Value text */}
                            <Box
                              sx={{
                                position: 'absolute',
                                left: `${Math.min((metric.disparate_impact_ratio / maxRatio) * 100, 100)}%`,
                                top: '50%',
                                transform: 'translate(-50%, -50%)',
                                px: 0.5,
                                bgcolor: 'background.paper',
                                borderRadius: 0.5,
                                zIndex: 2,
                              }}
                            >
                              <Typography
                                variant="caption"
                                fontWeight={700}
                                sx={{
                                  color: severityColor === 'success' ? 'success.main' : severityColor,
                                }}
                              >
                                {toPercentage(metric.disparate_impact_ratio)}%
                              </Typography>
                            </Box>
                          </Box>

                          {/* Legend */}
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
                              <Box sx={{ width: 12, height: 2, bgcolor: barColor }} />
                              <Typography variant="caption" color="text.secondary">
                                Actual ({toPercentage(metric.disparate_impact_ratio)}%)
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
                              <Box sx={{ width: 12, height: 2, bgcolor: 'black' }} />
                              <Typography variant="caption" color="text.secondary">
                                80% Threshold
                              </Typography>
                            </Box>
                          </Box>
                        </Box>
                      </Tooltip>
                    </Grid>

                    {/* Status Badge */}
                    <Grid item xs={12} sm={2}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Chip
                          label={severity === 'acceptable' ? 'Pass' : `${severity} severity`}
                          size="small"
                          color={severityColor}
                          variant={severity === 'acceptable' ? 'filled' : 'outlined'}
                          sx={{ fontWeight: 600, minWidth: 80 }}
                        />
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            );
          })}
        </Stack>

        {/* Legend */}
        <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Color Guide
          </Typography>
          <Grid container spacing={1}>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#388e3c' }} />
                <Typography variant="caption">≥ 80% Acceptable</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#1976d2' }} />
                <Typography variant="caption">75-79% Low Risk</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#fbc02d' }} />
                <Typography variant="caption">65-74% Medium</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#f57c00' }} />
                <Typography variant="caption">50-64% High</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#d32f2f' }} />
                <Typography variant="caption">&lt; 50% Critical</Typography>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    </Stack>
  );
};

export default BiasMetricsChart;
