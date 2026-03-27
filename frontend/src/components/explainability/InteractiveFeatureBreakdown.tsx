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
  Analytics as AnalyticsIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';

/**
 * Sub-feature breakdown item for drill-down details
 */
export interface SubFeatureItem {
  /** Sub-feature label */
  label: string;
  /** Sub-feature value (0-1) */
  value: number;
  /** Optional description for tooltip */
  description?: string;
  /** Optional impact indicator (positive/negative) */
  impact?: 'positive' | 'negative' | 'neutral';
}

/**
 * Interactive feature item interface
 */
export interface InteractiveFeature {
  /** Feature name (e.g., "Technical Skills", "Work Experience") */
  name: string;
  /** Feature value score (0-1) */
  value: number;
  /** Weight assigned to this feature (0-1) */
  weight: number;
  /** Contribution to overall score (value * weight) */
  contribution: number;
  /** Optional category for grouping */
  category?: string;
  /** Optional description shown in tooltip */
  description?: string;
  /** Optional detailed breakdown for drill-down */
  breakdown?: SubFeatureItem[];
  /** Optional metadata shown on hover */
  metadata?: {
    /** Data source */
    source?: string;
    /** Last updated timestamp */
    lastUpdated?: string;
    /** Confidence level (0-1) */
    confidence?: number;
  };
}

/**
 * InteractiveFeatureBreakdown Component Props
 */
export interface InteractiveFeatureBreakdownProps {
  /** Array of features to display */
  features: InteractiveFeature[];
  /** Optional overall score for context */
  overallScore?: number;
  /** Optional title for the breakdown */
  title?: string;
  /** Optional description subtitle */
  description?: string;
  /** Whether to show hover details */
  showHoverDetails?: boolean;
  /** Whether features are expandable by default */
  defaultExpanded?: boolean;
  /** Optional callback when feature is clicked */
  onFeatureClick?: (feature: InteractiveFeature) => void;
}

/**
 * InteractiveFeatureBreakdown Component
 *
 * Displays an interactive breakdown of feature contributions with drill-down
 * capabilities and hover details. Each feature shows:
 * - Feature name with category chip
 * - Interactive progress bar with hover state
 * - Weight and contribution metrics
 * - Expandable detailed breakdown of sub-features
 * - Tooltips with metadata and descriptions
 *
 * @example
 * ```tsx
 * const features = [
 *   {
 *     name: 'Technical Skills',
 *     value: 0.85,
 *     weight: 0.4,
 *     contribution: 0.34,
 *     description: 'Programming languages and frameworks',
 *     breakdown: [
 *       { label: 'JavaScript', value: 0.9, impact: 'positive' },
 *       { label: 'React', value: 0.8, impact: 'positive' },
 *     ],
 *   },
 * ];
 * <InteractiveFeatureBreakdown features={features} />
 * ```
 *
 * @example
 * ```tsx
 * <InteractiveFeatureBreakdown
 *   features={features}
 *   title="Match Score Analysis"
 *   showHoverDetails={true}
 *   defaultExpanded={false}
 *   onFeatureClick={(feature) => console.log(feature)}
 * />
 * ```
 */
const InteractiveFeatureBreakdown: React.FC<InteractiveFeatureBreakdownProps> = ({
  features,
  overallScore,
  title = 'Interactive Feature Breakdown',
  description = 'Hover over features for details, click to drill down into sub-components',
  showHoverDetails = true,
  defaultExpanded = false,
  onFeatureClick,
}) => {
  /**
   * State for tracking expanded features
   */
  const [expandedFeatures, setExpandedFeatures] = useState<Set<string>>(
    defaultExpanded ? new Set(features.map((f) => f.name)) : new Set()
  );

  /**
   * State for tracking hovered feature
   */
  const [hoveredFeature, setHoveredFeature] = useState<string | null>(null);

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
  const getScoreColor = (
    score: number
  ): 'primary' | 'secondary' | 'info' | 'success' | 'warning' | 'error' => {
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
   * Get impact icon based on impact type
   */
  const getImpactIcon = (impact?: 'positive' | 'negative' | 'neutral') => {
    switch (impact) {
      case 'positive':
        return <TrendingUpIcon fontSize="small" color="success" />;
      case 'negative':
        return <TrendingDownIcon fontSize="small" color="error" />;
      default:
        return null;
    }
  };

  /**
   * Calculate total contribution from all features
   */
  const calculatedOverall = React.useMemo(
    () => features.reduce((sum, feature) => sum + feature.contribution, 0),
    [features]
  );

  /**
   * Handle feature click
   */
  const handleFeatureClick = (feature: InteractiveFeature, hasBreakdown: boolean) => {
    if (hasBreakdown) {
      toggleFeature(feature.name);
    }
    if (onFeatureClick) {
      onFeatureClick(feature);
    }
  };

  /**
   * Render individual feature row with drill-down and hover details
   */
  const FeatureRow: React.FC<{
    feature: InteractiveFeature;
    index: number;
  }> = ({ feature, index }) => {
    const isExpanded = expandedFeatures.has(feature.name);
    const isHovered = hoveredFeature === feature.name;
    const hasBreakdown = feature.breakdown && feature.breakdown.length > 0;

    return (
      <Card
        variant="outlined"
        sx={{
          mb: 2,
          transition: 'all 0.3s ease-in-out',
          transform: isHovered ? 'translateX(8px)' : 'translateX(0)',
          boxShadow: isHovered ? 3 : 0,
          borderColor: isHovered ? 'primary.main' : 'divider',
          cursor: hasBreakdown ? 'pointer' : 'default',
          '&:hover': {
            borderColor: 'primary.main',
          },
        }}
        onMouseEnter={() => setHoveredFeature(feature.name)}
        onMouseLeave={() => setHoveredFeature(null)}
        onClick={() => handleFeatureClick(feature, hasBreakdown)}
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
                    toggleFeature(feature.name);
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
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  <Typography variant="subtitle1" fontWeight={600}>
                    {feature.name}
                  </Typography>
                  {showHoverDetails && (
                    <Tooltip
                      title={
                        <Box>
                          {feature.description && (
                            <Typography variant="caption" display="block" sx={{ mb: 1 }}>
                              {feature.description}
                            </Typography>
                          )}
                          {feature.metadata && (
                            <>
                              {feature.metadata.source && (
                                <Typography variant="caption" display="block">
                                  <strong>Source:</strong> {feature.metadata.source}
                                </Typography>
                              )}
                              {feature.metadata.confidence !== undefined && (
                                <Typography variant="caption" display="block">
                                  <strong>Confidence:</strong> {toPercentage(feature.metadata.confidence)}%
                                </Typography>
                              )}
                              {feature.metadata.lastUpdated && (
                                <Typography variant="caption" display="block">
                                  <strong>Updated:</strong> {feature.metadata.lastUpdated}
                                </Typography>
                              )}
                            </>
                          )}
                          {!feature.description && !feature.metadata && (
                            <Typography variant="caption">
                              Contribution: {toPercentage(feature.contribution)}%
                            </Typography>
                          )}
                        </Box>
                      }
                      arrow
                      placement="top"
                    >
                      <InfoIcon
                        fontSize="small"
                        color="action"
                        sx={{ cursor: 'help', opacity: isHovered ? 1 : 0.7 }}
                      />
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
                  <Chip label={feature.category} size="small" variant="outlined" color="primary" />
                )}
              </Stack>
            </Grid>

            {/* Feature Value Bar with Hover Effect */}
            <Grid item xs={12} sm={5}>
              <Stack spacing={1}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    Feature Value
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {toPercentage(feature.value)}%
                  </Typography>
                </Box>
                <Tooltip
                  title={`Raw feature value: ${toPercentage(feature.value)}%`}
                  placement="top"
                  arrow
                >
                  <LinearProgress
                    variant="determinate"
                    value={toPercentage(feature.value)}
                    sx={{
                      height: isHovered ? 12 : 10,
                      borderRadius: 5,
                      backgroundColor: 'action.hover',
                      transition: 'height 0.2s ease-in-out',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: getProgressColor(feature.value),
                        transition: 'background-color 0.3s ease-in-out',
                      },
                    }}
                  />
                </Tooltip>
              </Stack>
            </Grid>

            {/* Weight and Contribution */}
            <Grid item xs={12} sm={hasBreakdown ? 4 : 4}>
              <Grid container spacing={1}>
                {/* Weight */}
                <Grid item xs={6}>
                  <Tooltip title="Algorithm-assigned importance weight" placement="top" arrow>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" fontWeight={700} color="text.secondary">
                        {toPercentage(feature.weight)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Weight
                      </Typography>
                    </Box>
                  </Tooltip>
                </Grid>
                {/* Contribution */}
                <Grid item xs={6}>
                  <Tooltip
                    title={`Contribution = Value (${toPercentage(feature.value)}%) × Weight (${toPercentage(feature.weight)}%)`}
                    placement="top"
                    arrow
                  >
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
                  </Tooltip>
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
                    <Tooltip
                      key={`${feature.name}-breakdown-${idx}`}
                      title={item.description || `${item.label}: ${toPercentage(item.value)}%`}
                      placement="left"
                      arrow
                    >
                      <Box
                        sx={{
                          p: 1.5,
                          borderRadius: 1,
                          backgroundColor: 'grey.50',
                          border: '1px solid',
                          borderColor: 'divider',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            backgroundColor: 'grey.100',
                            borderColor: 'primary.main',
                            transform: 'translateX(4px)',
                          },
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
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body2" fontWeight={600}>
                              {item.label}
                            </Typography>
                            {item.impact && getImpactIcon(item.impact)}
                          </Box>
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
                    </Tooltip>
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
          No feature data available
        </Typography>
      </Paper>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <AnalyticsIcon color="primary" />
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
                  <span key={f.name}>
                    {i > 0 && ' + '}
                    {toPercentage(f.contribution)}%
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
          Interactive Feature Analysis
        </Typography>
        {features.map((feature, index) => (
          <FeatureRow key={feature.name} feature={feature} index={index} />
        ))}
      </Stack>

      {/* Interactive Help */}
      {showHoverDetails && (
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'action.hover' }}>
          <Typography variant="caption" color="text.secondary">
            <strong>Interactive Features:</strong> Hover over any feature to see detailed information
            and metadata. Click on features with breakdown indicators to drill down into sub-components.
            Progress bars and metrics update dynamically to show how each feature contributes to the
            overall score.
          </Typography>
        </Paper>
      )}
    </Stack>
  );
};

export default InteractiveFeatureBreakdown;
