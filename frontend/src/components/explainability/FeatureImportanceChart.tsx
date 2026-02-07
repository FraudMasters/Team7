import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Stack,
  LinearProgress,
  Card,
  CardContent,
  Grid,
  Chip,
  Tooltip,
  Collapse,
  IconButton,
  Divider,
} from '@mui/material';
import {
  BarChart as BarChartIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

/**
 * Feature importance item interface
 */
export interface FeatureImportanceItem {
  /** Feature name (e.g., "Experience", "Skills", "Education") */
  feature_name: string;
  /** Feature value score (0-1) */
  feature_value: number;
  /** Weight assigned to this feature (0-1) */
  weight: number;
  /** Contribution to overall score (feature_value * weight) */
  contribution: number;
  /** Optional description of what this feature represents */
  description?: string;
  /** Optional category for grouping features */
  category?: string;
  /** Optional detailed breakdown of sub-values for drill-down */
  breakdown?: Array<{
    label: string;
    value: number;
    description?: string;
  }>;
}

/**
 * FeatureImportanceChart Component Props
 */
export interface FeatureImportanceChartProps {
  /** Array of feature importance items to display */
  features: FeatureImportanceItem[];
  /** Optional overall score for context */
  overallScore?: number;
  /** Optional title for the chart */
  title?: string;
  /** Optional description subtitle */
  description?: string;
  /** Whether to show detailed tooltips */
  showDetails?: boolean;
}

/**
 * FeatureImportanceChart Component
 *
 * Displays a visual breakdown of feature contributions to an overall score.
 * Each feature shows:
 * - Feature name with optional category chip
 * - Raw feature value as a progress bar
 * - Algorithm weight percentage
 * - Contribution to the overall score
 *
 * @example
 * ```tsx
 * const features = [
 *   { feature_name: 'Experience', feature_value: 0.85, weight: 0.4, contribution: 0.34 },
 *   { feature_name: 'Skills', feature_value: 0.72, weight: 0.35, contribution: 0.252 },
 *   { feature_name: 'Education', feature_value: 0.60, weight: 0.25, contribution: 0.15 },
 * ];
 * <FeatureImportanceChart features={features} overallScore={0.742} />
 * ```
 *
 * @example
 * ```tsx
 * <FeatureImportanceChart
 *   features={features}
 *   title="Why This Candidate Ranked High"
 *   description="Feature contributions to the match score"
 *   showDetails={true}
 * />
 * ```
 */
const FeatureImportanceChart: React.FC<FeatureImportanceChartProps> = ({
  features,
  overallScore,
  title = 'Feature Importance',
  description = 'Visual breakdown of how each feature contributes to the overall score',
  showDetails = true,
}) => {
  /**
   * State for tracking expanded features
   */
  const [expandedFeatures, setExpandedFeatures] = useState<Set<string>>(new Set());

  /**
   * Toggle feature expansion
   */
  const toggleFeature = (featureName: string) => {
    setExpandedFeatures((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(featureName)) {
        newSet.delete(featureName);
      } else {
        newSet.add(featureName);
      }
      return newSet;
    });
  };

  /**
   * Convert decimal score to percentage
   */
  const toPercentage = (value: number): number => Math.round(value * 100);

  /**
   * Get color based on score value
   */
  const getScoreColor = (score: number): 'primary' | 'secondary' | 'info' | 'success' | 'warning' | 'error' => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'primary';
    if (score >= 0.4) return 'info';
    if (score >= 0.2) return 'warning';
    return 'error';
  };

  /**
   * Get color for progress bar based on score
   */
  const getProgressColor = (score: number): string => {
    if (score >= 0.8) return '#4caf50';
    if (score >= 0.6) return '#2196f3';
    if (score >= 0.4) return '#00bcd4';
    if (score >= 0.2) return '#ff9800';
    return '#f44336';
  };

  /**
   * Calculate total contribution from all features
   */
  const calculatedOverall = React.useMemo(
    () => features.reduce((sum, feature) => sum + feature.contribution, 0),
    [features]
  );

  /**
   * Render individual feature row with drill-down capability
   */
  const FeatureRow: React.FC<{
    feature: FeatureImportanceItem;
    index: number;
  }> = ({ feature, index }) => {
    const isExpanded = expandedFeatures.has(feature.feature_name);
    const hasBreakdown = feature.breakdown && feature.breakdown.length > 0;

    return (
      <Card
        variant="outlined"
        sx={{
          mb: 2,
          transition: 'transform 0.2s, box-shadow 0.2s',
          '&:hover': {
            transform: 'translateX(4px)',
            boxShadow: 2,
          },
          cursor: hasBreakdown ? 'pointer' : 'default',
        }}
        onClick={() => hasBreakdown && toggleFeature(feature.feature_name)}
      >
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            {/* Expand/Collapse Icon */}
            {hasBreakdown && (
              <Grid item xs={0.5}>
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleFeature(feature.feature_name);
                  }}
                  sx={{ p: 0.5 }}
                >
                  {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Grid>
            )}

            {/* Feature Name and Category */}
            <Grid item xs={12} sm={hasBreakdown ? 2.5 : 3}>
              <Stack spacing={1}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="subtitle1" fontWeight={600}>
                    {feature.feature_name}
                  </Typography>
                  {showDetails && (
                    <Tooltip title={feature.description || `Contribution: ${toPercentage(feature.contribution)}%`}>
                      <InfoIcon fontSize="small" color="action" sx={{ cursor: 'help' }} />
                    </Tooltip>
                  )}
                  {hasBreakdown && (
                    <Chip
                      label={`${feature.breakdown?.length} items`}
                      size="small"
                      variant="outlined"
                      color="info"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  )}
                </Box>
                {feature.category && (
                  <Chip
                    label={feature.category}
                    size="small"
                    variant="outlined"
                    color="info"
                  />
                )}
              </Stack>
            </Grid>

            {/* Feature Value Bar */}
            <Grid item xs={12} sm={5}>
              <Stack spacing={1}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    Feature Value
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {toPercentage(feature.feature_value)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={toPercentage(feature.feature_value)}
                  sx={{
                    height: 10,
                    borderRadius: 5,
                    backgroundColor: 'action.hover',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getProgressColor(feature.feature_value),
                    },
                  }}
                />
              </Stack>
            </Grid>

            {/* Weight and Contribution */}
            <Grid item xs={12} sm={hasBreakdown ? 4 : 4}>
              <Grid container spacing={1}>
                {/* Weight */}
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" fontWeight={700} color="text.secondary">
                      {toPercentage(feature.weight)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Weight
                    </Typography>
                  </Box>
                </Grid>
                {/* Contribution */}
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography
                      variant="h6"
                      fontWeight={700}
                      color={getScoreColor(feature.contribution)}
                    >
                      +{toPercentage(feature.contribution)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Contribution
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Grid>
          </Grid>

          {/* Detailed Breakdown */}
          {hasBreakdown && (
            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ pl: { xs: 0, sm: 1 } }}>
                <Typography
                  variant="subtitle2"
                  fontWeight={600}
                  color="text.secondary"
                  sx={{ mb: 1.5 }}
                >
                  Detailed Breakdown
                </Typography>
                <Stack spacing={1.5}>
                  {feature.breakdown!.map((item, idx) => (
                    <Box
                      key={`${feature.feature_name}-breakdown-${idx}`}
                      sx={{
                        p: 1.5,
                        borderRadius: 1,
                        backgroundColor: 'grey.50',
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          mb: 1,
                        }}
                      >
                        <Typography variant="body2" fontWeight={600}>
                          {item.label}
                        </Typography>
                        <Typography
                          variant="body2"
                          fontWeight={700}
                          color={getScoreColor(item.value)}
                        >
                          {toPercentage(item.value)}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={toPercentage(item.value)}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: 'action.hover',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: getProgressColor(item.value),
                          },
                        }}
                      />
                      {item.description && (
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{ display: 'block', mt: 0.5 }}
                        >
                          {item.description}
                        </Typography>
                      )}
                    </Box>
                  ))}
                </Stack>
              </Box>
            </Collapse>
          )}
        </CardContent>
      </Card>
    );
  };

  if (!features || features.length === 0) {
    return (
      <Paper elevation={1} sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No feature importance data available
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

      {/* Overall Score Summary */}
      <Paper
        elevation={2}
        sx={{
          p: 3,
          bgcolor: 'background.default',
          border: '2px solid',
          borderColor: 'divider',
        }}
      >
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Overall Score
            </Typography>
            <Typography variant="h3" fontWeight={700} color="primary.main">
              {toPercentage(overallScore !== undefined ? overallScore : calculatedOverall)}%
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Stack spacing={1}>
              <Typography variant="caption" color="text.secondary">
                Feature Breakdown Formula
              </Typography>
              <Typography variant="body2" fontWeight={500}>
                {features.map((f, i) => (
                  <span key={f.feature_name}>
                    {i > 0 && ' + '}
                    {toPercentage(f.contribution)}% ({f.feature_name})
                  </span>
                ))}
                {' = '}
                <strong>
                  {toPercentage(overallScore !== undefined ? overallScore : calculatedOverall)}%
                </strong>
              </Typography>
            </Stack>
          </Grid>
        </Grid>
      </Paper>

      {/* Feature Breakdown */}
      <Stack spacing={2}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Detailed Feature Breakdown
        </Typography>
        {features.map((feature, index) => (
          <FeatureRow key={feature.feature_name} feature={feature} index={index} />
        ))}
      </Stack>

      {/* Formula Explanation */}
      {showDetails && (
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'action.hover' }}>
          <Typography variant="caption" color="text.secondary">
            <strong>How it works:</strong> Each feature has a raw value (0-100%) and a weight
            representing its importance. The contribution is calculated as Feature Value × Weight,
            and all contributions are summed to get the overall score.
          </Typography>
        </Paper>
      )}
    </Stack>
  );
};

export default FeatureImportanceChart;
