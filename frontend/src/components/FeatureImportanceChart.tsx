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
  IconButton,
  Collapse,
  LinearProgress,
} from '@mui/material';
import {
  BarChart as BarChartIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  BugReport as BiasIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import type { FeatureBiasSource } from '@/types/api';

/**
 * Feature Importance Chart Component Props
 */
export interface FeatureImportanceChartProps {
  /** Array of feature bias sources to visualize */
  biasSources: FeatureBiasSource[];
  /** Optional title for the chart */
  title?: string;
  /** Optional description subtitle */
  description?: string;
  /** Whether to show detailed tooltips */
  showDetails?: boolean;
  /** Maximum number of features to display */
  maxFeatures?: number;
}

/**
 * Get severity level based on bias indicator and correlation
 */
function getSeverityLevel(source: FeatureBiasSource): 'critical' | 'high' | 'medium' | 'low' {
  // Use the severity from the backend if available
  return source.severity;
}

/**
 * Get color based on severity
 */
function getSeverityColor(severity: 'critical' | 'high' | 'medium' | 'low'): 'error' | 'warning' | 'info' | 'success' {
  if (severity === 'critical') return 'error';
  if (severity === 'high') return 'error';
  if (severity === 'medium') return 'warning';
  return 'info';
}

/**
 * Get bar color for importance visualization
 */
function getBarColor(severity: 'critical' | 'high' | 'medium' | 'low'): string {
  if (severity === 'critical') return '#d32f2f'; // red
  if (severity === 'high') return '#f57c00'; // orange
  if (severity === 'medium') return '#fbc02d'; // yellow
  return '#1976d2'; // blue
}

/**
 * Get bias indicator icon
 */
function getBiasIndicatorIcon(indicator: string) {
  if (indicator === 'proxy') return <ErrorIcon fontSize="small" />;
  if (indicator === 'correlation_detected') return <WarningIcon fontSize="small" />;
  return <InfoIcon fontSize="small" />;
}

/**
 * Get bias indicator label
 */
function getBiasIndicatorLabel(indicator: string): string {
  if (indicator === 'proxy') return 'Proxy Feature';
  if (indicator === 'high_importance_correlation') return 'High Importance';
  if (indicator === 'correlation_detected') return 'Correlation Detected';
  return indicator.replace(/_/g, ' ');
}

/**
 * FeatureImportanceChart Component
 *
 * Visualizes feature importance with bias source indicators:
 * - Horizontal bar chart showing feature importance scores
 * - Bias source indicators on high-impact features
 * - Drill-down to feature details with expandable cards
 * - Color coding based on bias severity
 *
 * @example
 * ```tsx
 * const biasSources = [
 *   {
 *     feature_name: 'name',
 *     feature_label: 'Candidate Name',
 *     demographic_group: 'gender',
 *     bias_indicator: 'proxy',
 *     importance_score: 0.234,
 *     correlation_strength: 0.89,
 *     recommendation: 'Consider removing name-blind screening',
 *     severity: 'critical',
 *   },
 *   {
 *     feature_name: 'graduation_year',
 *     feature_label: 'Graduation Year',
 *     demographic_group: 'age_group',
 *     bias_indicator: 'proxy',
 *     importance_score: 0.156,
 *     correlation_strength: 0.76,
 *     recommendation: 'Use career stage instead of specific year',
 *     severity: 'high',
 *   },
 * ];
 * <FeatureImportanceChart biasSources={biasSources} />
 * ```
 */
const FeatureImportanceChart: React.FC<FeatureImportanceChartProps> = ({
  biasSources,
  title = 'Feature Importance Analysis',
  description = 'Identifies features that may introduce bias based on their correlation with demographic disparities',
  showDetails = true,
  maxFeatures = 10,
}) => {
  const [expandedFeatures, setExpandedFeatures] = React.useState<Set<number>>(new Set());

  /**
   * Toggle feature expansion for drill-down details
   */
  const toggleFeature = (index: number) => {
    setExpandedFeatures((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  /**
   * Calculate the maximum importance for chart scaling
   */
  const maxImportance = React.useMemo(
    () => Math.max(...biasSources.map((s) => s.importance_score), 0.1),
    [biasSources]
  );

  /**
   * Count sources by severity
   */
  const severityCounts = React.useMemo(() => {
    const counts = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
    };
    biasSources.forEach((source) => {
      counts[getSeverityLevel(source)]++;
    });
    return counts;
  }, [biasSources]);

  /**
   * Display only top N features
   */
  const displaySources = React.useMemo(
    () => biasSources.slice(0, maxFeatures),
    [biasSources, maxFeatures]
  );

  /**
   * Render empty state
   */
  if (!biasSources || biasSources.length === 0) {
    return (
      <Paper elevation={1} sx={{ p: 3, textAlign: 'center' }}>
        <BarChartIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="body2" color="text.secondary">
          No feature bias sources detected
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          All features appear to be fair across demographic groups
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
          <Grid item xs={6} sm={3}>
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
          <Grid item xs={6} sm={3}>
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
          <Grid item xs={6} sm={3}>
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
          <Grid item xs={6} sm={3}>
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
        </Grid>
      </Paper>

      {/* Info Alert */}
      <Alert severity="info" icon={<InfoIcon />}>
        <AlertTitle>Understanding Feature Bias Sources</AlertTitle>
        <Typography variant="body2">
          This chart identifies features that may introduce bias by correlating with demographic groups.
          <strong> Proxy features</strong> directly encode protected attributes (e.g., name implies gender).
          <strong> Correlation detected</strong> features show statistical relationships with demographic outcomes.
          High importance scores indicate features that significantly impact ranking decisions.
        </Typography>
      </Alert>

      {/* Feature Importance Chart */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            Feature Bias Sources
          </Typography>
          <Chip
            label={`Top ${displaySources.length} of ${biasSources.length}`}
            size="small"
            variant="outlined"
            color="primary"
          />
        </Box>

        <Stack spacing={2} sx={{ mt: 3 }}>
          {displaySources.map((source, index) => {
            const severity = getSeverityLevel(source);
            const severityColor = getSeverityColor(severity);
            const barColor = getBarColor(severity);
            const isExpanded = expandedFeatures.has(index);

            return (
              <Card
                key={`${source.feature_name}-${index}`}
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
                  {/* Main row - always visible */}
                  <Grid container spacing={2} alignItems="center">
                    {/* Feature Info */}
                    <Grid item xs={12} sm={4}>
                      <Stack spacing={0.5}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Typography variant="subtitle1" fontWeight={600}>
                            {source.feature_label}
                          </Typography>
                          <Box sx={{ color: `${severityColor}.main` }}>
                            {getBiasIndicatorIcon(source.bias_indicator)}
                          </Box>
                        </Box>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          <Chip
                            label={source.demographic_group}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                          />
                          <Chip
                            label={getBiasIndicatorLabel(source.bias_indicator)}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                          />
                        </Box>
                      </Stack>
                    </Grid>

                    {/* Importance Bar */}
                    <Grid item xs={12} sm={5}>
                      <Tooltip
                        title={
                          <React.Fragment>
                            <Typography variant="body2" fontWeight={600}>
                              {source.feature_label} Details
                            </Typography>
                            <Divider sx={{ my: 0.5, bgcolor: 'white' }} />
                            <Typography variant="caption" display="block">
                              Importance: {(source.importance_score * 100).toFixed(2)}%
                            </Typography>
                            <Typography variant="caption" display="block">
                              Correlation: {(source.correlation_strength * 100).toFixed(2)}%
                            </Typography>
                            <Typography variant="caption" display="block">
                              Feature: {source.feature_name}
                            </Typography>
                            <Typography variant="caption" display="block">
                              Demographic: {source.demographic_group}
                            </Typography>
                            {showDetails && (
                              <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                                {source.recommendation}
                              </Typography>
                            )}
                          </React.Fragment>
                        }
                        arrow
                      >
                        <Box>
                          {/* Importance Bar */}
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
                                width: `${Math.min((source.importance_score / maxImportance) * 100, 100)}%`,
                                bgcolor: barColor,
                                transition: 'width 0.5s ease-in-out',
                              }}
                            />

                            {/* Value text */}
                            <Box
                              sx={{
                                position: 'absolute',
                                left: `${Math.min((source.importance_score / maxImportance) * 100, 100)}%`,
                                top: '50%',
                                transform: 'translate(-50%, -50%)',
                                px: 0.5,
                                bgcolor: 'background.paper',
                                borderRadius: 0.5,
                                zIndex: 2,
                              }}
                            >
                              <Typography variant="caption" fontWeight={700} color="text.primary">
                                {(source.importance_score * 100).toFixed(1)}%
                              </Typography>
                            </Box>
                          </Box>

                          {/* Legend */}
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
                              <Box sx={{ width: 12, height: 2, bgcolor: barColor }} />
                              <Typography variant="caption" color="text.secondary">
                                Importance
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
                              <TrendingUpIcon sx={{ fontSize: 12, color: `${severityColor}.main` }} />
                              <Typography variant="caption" color="text.secondary">
                                Correlation: {(source.correlation_strength * 100).toFixed(1)}%
                              </Typography>
                            </Box>
                          </Box>
                        </Box>
                      </Tooltip>
                    </Grid>

                    {/* Severity Badge and Expand Button */}
                    <Grid item xs={12} sm={3}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                        <Chip
                          label={severity.toUpperCase()}
                          size="small"
                          color={severityColor}
                          variant={severity === 'low' ? 'outlined' : 'filled'}
                          sx={{ fontWeight: 600 }}
                        />
                        <IconButton
                          size="small"
                          onClick={() => toggleFeature(index)}
                          sx={{ ml: 0.5 }}
                          aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
                        >
                          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                      </Box>
                    </Grid>
                  </Grid>

                  {/* Expandable Details Section */}
                  <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                    <Divider sx={{ my: 2 }} />
                    <Stack spacing={2}>
                      {/* Feature Details */}
                      <Box>
                        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                          Feature Details
                        </Typography>
                        <Grid container spacing={1} sx={{ mt: 1 }}>
                          <Grid item xs={6} sm={3}>
                            <Typography variant="caption" color="text.secondary">
                              Feature Name
                            </Typography>
                            <Typography variant="body2" fontWeight={500}>
                              {source.feature_name}
                            </Typography>
                          </Grid>
                          <Grid item xs={6} sm={3}>
                            <Typography variant="caption" color="text.secondary">
                              Display Label
                            </Typography>
                            <Typography variant="body2" fontWeight={500}>
                              {source.feature_label}
                            </Typography>
                          </Grid>
                          <Grid item xs={6} sm={3}>
                            <Typography variant="caption" color="text.secondary">
                              Demographic
                            </Typography>
                            <Typography variant="body2" fontWeight={500}>
                              {source.demographic_group}
                            </Typography>
                          </Grid>
                          <Grid item xs={6} sm={3}>
                            <Typography variant="caption" color="text.secondary">
                              Bias Indicator
                            </Typography>
                            <Typography variant="body2" fontWeight={500}>
                              {getBiasIndicatorLabel(source.bias_indicator)}
                            </Typography>
                          </Grid>
                        </Grid>
                      </Box>

                      {/* Metrics */}
                      <Box>
                        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                          Metrics
                        </Typography>
                        <Stack spacing={1} sx={{ mt: 1 }}>
                          <Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">
                                Importance Score
                              </Typography>
                              <Typography variant="body2" fontWeight={600}>
                                {(source.importance_score * 100).toFixed(2)}%
                              </Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={source.importance_score * 100}
                              sx={{ height: 6, borderRadius: 1 }}
                              color={severityColor}
                            />
                          </Box>
                          <Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">
                                Correlation Strength
                              </Typography>
                              <Typography variant="body2" fontWeight={600}>
                                {(source.correlation_strength * 100).toFixed(2)}%
                              </Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={source.correlation_strength * 100}
                              sx={{ height: 6, borderRadius: 1 }}
                              color="info"
                            />
                          </Box>
                        </Stack>
                      </Box>

                      {/* Recommendation */}
                      {source.recommendation && (
                        <Alert severity={severity === 'critical' || severity === 'high' ? 'error' : severity === 'medium' ? 'warning' : 'info'} icon={<BiasIcon />}>
                          <AlertTitle sx={{ typography: 'subtitle2', fontWeight: 600 }}>
                            Recommendation
                          </AlertTitle>
                          <Typography variant="body2">{source.recommendation}</Typography>
                        </Alert>
                      )}
                    </Stack>
                  </Collapse>
                </CardContent>
              </Card>
            );
          })}
        </Stack>

        {/* Legend */}
        <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Bias Severity Guide
          </Typography>
          <Grid container spacing={1}>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#d32f2f' }} />
                <Typography variant="caption">Critical - Immediate action</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#f57c00' }} />
                <Typography variant="caption">High - Review needed</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#fbc02d' }} />
                <Typography variant="caption">Medium - Monitor</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#1976d2' }} />
                <Typography variant="caption">Low - Acceptable</Typography>
              </Box>
            </Grid>
          </Grid>
          <Divider sx={{ my: 1 }} />
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Bias Indicator Types
          </Typography>
          <Grid container spacing={1}>
            <Grid item xs={6} sm={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <ErrorIcon sx={{ fontSize: 14, color: 'error.main' }} />
                <Typography variant="caption">Proxy: Directly encodes demographic</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <WarningIcon sx={{ fontSize: 14, color: 'warning.main' }} />
                <Typography variant="caption">Correlation: Statistical relationship</Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <InfoIcon sx={{ fontSize: 14, color: 'info.main' }} />
                <Typography variant="caption">High Importance: Significant impact</Typography>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Paper>

      {/* Show more indicator if truncated */}
      {biasSources.length > maxFeatures && (
        <Box sx={{ textAlign: 'center', py: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Showing top {maxFeatures} of {biasSources.length} features
          </Typography>
        </Box>
      )}
    </Stack>
  );
};

export default FeatureImportanceChart;
