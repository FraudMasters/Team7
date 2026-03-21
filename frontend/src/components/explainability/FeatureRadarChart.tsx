// React hooks for state management and effects
import React, { useState, useEffect, useCallback } from 'react';
// HTTP client for API requests
import axios from 'axios';
// Material UI components for interface
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Button,
  Alert,
  AlertTitle,
  Stack,
  Chip,
  Tooltip,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
// Material UI icons
import {
  Refresh as RefreshIcon,
  RadarRounded as RadarIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Info as InfoIcon,
  TuneRounded as TuneIcon,
} from '@mui/icons-material';
// Recharts components for data visualization
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  Legend,
} from 'recharts';

/**
 * Individual feature data item
 * Matches backend FeatureImportanceItem schema
 */
interface FeatureItem {
  /** Feature name */
  feature_name: string;
  /** Feature importance score (0-1) */
  importance_score: number;
  /** Feature rank by importance */
  rank: number;
  /** Feature description */
  description: string;
  /** Feature category */
  category?: string;
}

/**
 * API response for feature importance
 */
interface FeatureImportanceResponse {
  /** Array of features with importance scores */
  features: FeatureItem[];
  /** Model version */
  model_version: string;
  /** Model type */
  model_type: string;
}

/**
 * Radar chart data point
 */
interface RadarDataPoint {
  /** Feature name (formatted) */
  feature: string;
  /** Original feature name */
  feature_name: string;
  /** Importance value (0-100) */
  value: number;
  /** Full mark (100) for radar chart scaling */
  fullMark: number;
  /** Feature description */
  description: string;
  /** Feature category */
  category?: string;
}

/**
 * FeatureRadarChart Component Props
 */
interface FeatureRadarChartProps {
  /** API endpoint URL for feature importance */
  apiUrl?: string;
  /** Optional start date filter */
  startDate?: string;
  /** Optional end date filter */
  endDate?: string;
  /** Maximum number of features to display */
  maxFeatures?: number;
  /** Display mode: 'importance' or 'normalized' */
  displayMode?: 'importance' | 'normalized';
}

/**
 * Format importance for display as percentage
 */
const formatImportance = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Format feature name for display
 */
const formatFeatureName = (name: string): string => {
  // Convert snake_case to readable format
  return name
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Shorten feature name for radar labels
 */
const shortenFeatureName = (name: string, maxLength: number = 20): string => {
  const formatted = formatFeatureName(name);
  if (formatted.length <= maxLength) return formatted;
  return formatted.substring(0, maxLength - 3) + '...';
};

/**
 * Custom tooltip for radar chart
 */
const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{
    payload: RadarDataPoint;
    value: number;
  }>;
}> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <Paper
        elevation={3}
        sx={{
          p: 1.5,
          border: '1px solid',
          borderColor: 'divider',
          maxWidth: 300,
        }}
      >
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          {formatFeatureName(data.feature_name)}
        </Typography>
        <Typography variant="body2" color="primary.main" fontWeight={600}>
          Importance: {data.value.toFixed(1)}%
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
          {data.description}
        </Typography>
        {data.category && (
          <Chip
            label={data.category}
            size="small"
            variant="outlined"
            sx={{ mt: 0.5, fontSize: '0.7rem', height: 20 }}
          />
        )}
      </Paper>
    );
  }
  return null;
};

/**
 * FeatureRadarChart Component
 *
 * Multi-dimensional visualization of feature importance using a radar chart.
 * Displays:
 * - Radar chart with all features positioned radially
 * - Interactive tooltips with feature descriptions
 * - Multiple display modes (raw importance vs. normalized)
 * - Model information and auto-refresh capability
 * - Summary statistics
 *
 * @example
 * ```tsx
 * <FeatureRadarChart />
 * ```
 *
 * @example
 * ```tsx
 * <FeatureRadarChart
 *   startDate="2024-01-01"
 *   endDate="2024-12-31"
 *   maxFeatures={8}
 *   displayMode="normalized"
 * />
 * ```
 */
const FeatureRadarChart: React.FC<FeatureRadarChartProps> = ({
  apiUrl = '/api/analytics/ai-explainability/feature-importance',
  startDate,
  endDate,
  maxFeatures = 8,
  displayMode: initialDisplayMode = 'importance',
}) => {
  // State for loading, error, data, and auto-refresh
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [featureData, setFeatureData] = useState<FeatureImportanceResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [displayMode, setDisplayMode] = useState<'importance' | 'normalized'>(initialDisplayMode);

  /**
   * Fetch feature importance data from backend
   */
  const fetchFeatureImportance = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params: Record<string, string> = {};
      if (startDate) {
        params.start_date = startDate;
      }
      if (endDate) {
        params.end_date = endDate;
      }
      if (maxFeatures) {
        params.limit = maxFeatures.toString();
      }

      const response = await axios.get<FeatureImportanceResponse>(apiUrl, { params });
      setFeatureData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load feature importance data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, startDate, endDate, maxFeatures]);

  /**
   * Initial fetch on mount and when dependencies change
   */
  useEffect(() => {
    fetchFeatureImportance();
  }, [fetchFeatureImportance]);

  /**
   * Auto-refresh every 60 seconds when enabled
   */
  useEffect(() => {
    if (!autoRefreshEnabled) {
      return;
    }

    const interval = setInterval(() => {
      fetchFeatureImportance();
    }, 60000); // 60 seconds

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, fetchFeatureImportance]);

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = () => {
    setAutoRefreshEnabled((prev) => !prev);
  };

  /**
   * Handle display mode change
   */
  const handleDisplayModeChange = (
    _event: React.MouseEvent<HTMLElement>,
    newMode: 'importance' | 'normalized' | null
  ) => {
    if (newMode !== null) {
      setDisplayMode(newMode);
    }
  };

  /**
   * Prepare radar chart data
   */
  const radarChartData = React.useMemo(() => {
    if (!featureData?.features) return [];

    const topFeatures = featureData.features
      .sort((a, b) => b.importance_score - a.importance_score)
      .slice(0, maxFeatures);

    // Calculate total for normalization
    const totalImportance = topFeatures.reduce((sum, f) => sum + f.importance_score, 0);

    return topFeatures.map((feature) => ({
      feature: shortenFeatureName(feature.feature_name),
      feature_name: feature.feature_name,
      value:
        displayMode === 'normalized'
          ? (feature.importance_score / totalImportance) * 100
          : feature.importance_score * 100,
      fullMark: 100,
      description: feature.description,
      category: feature.category,
    }));
  }, [featureData, maxFeatures, displayMode]);

  /**
   * Calculate summary statistics
   */
  const stats = React.useMemo(() => {
    if (!radarChartData.length) {
      return { max: 0, min: 0, avg: 0, total: 0 };
    }

    const values = radarChartData.map((d) => d.value);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const avg = values.reduce((sum, v) => sum + v, 0) / values.length;
    const total = values.reduce((sum, v) => sum + v, 0);

    return { max, min, avg, total };
  }, [radarChartData]);

  /**
   * Render loading state
   */
  if (loading && !featureData) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          Loading feature importance data...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          This may take a few moments
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" size="small" onClick={fetchFeatureImportance} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
        sx={{ mb: 3 }}
      >
        <AlertTitle>Error Loading Feature Importance</AlertTitle>
        {error}
      </Alert>
    );
  }

  /**
   * Render empty state
   */
  if (!featureData || !featureData.features || featureData.features.length === 0) {
    return (
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>No Feature Importance Data</AlertTitle>
        Feature importance data will be available after the ML model is trained. Train the ranking
        model to see which factors most influence candidate rankings.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 3,
          bgcolor: 'primary.main',
          color: 'white',
          borderRadius: 2,
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" fontWeight="bold" gutterBottom>
              Feature Radar Analysis
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Multi-dimensional visualization of feature importance
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
              <Chip
                label={`${radarChartData.length} features`}
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
              <Chip
                label={`Model: ${featureData.model_type || 'Random Forest'}`}
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
              {featureData.model_version && (
                <Chip
                  label={`v${featureData.model_version}`}
                  size="small"
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                />
              )}
            </Stack>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              size="small"
              onClick={toggleAutoRefresh}
              startIcon={autoRefreshEnabled ? <PauseIcon /> : <PlayIcon />}
              sx={{ borderColor: 'rgba(255,255,255,0.5)', color: 'white' }}
            >
              {autoRefreshEnabled ? 'Auto' : 'Paused'}
            </Button>
            <Button
              variant="outlined"
              size="small"
              onClick={fetchFeatureImportance}
              startIcon={<RefreshIcon />}
              sx={{ borderColor: 'rgba(255,255,255,0.5)', color: 'white' }}
            >
              Refresh
            </Button>
          </Stack>
        </Box>
      </Paper>

      {/* Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1 }}>
              <Typography variant="h4" color="primary.main" fontWeight={700}>
                {radarChartData.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Features Displayed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1 }}>
              <Typography variant="h4" color="success.main" fontWeight={700}>
                {stats.max.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Maximum Value
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1 }}>
              <Typography variant="h4" fontWeight={700}>
                {stats.avg.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Average Value
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1 }}>
              <Typography variant="h4" color="info.main" fontWeight={700}>
                {stats.min.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Minimum Value
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Radar Chart */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <RadarIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Multi-Dimensional Feature View
              </Typography>
            </Box>
            <Stack direction="row" spacing={2} alignItems="center">
              <Tooltip title="Toggle between raw importance and normalized values">
                <TuneIcon color="action" sx={{ cursor: 'help' }} />
              </Tooltip>
              <ToggleButtonGroup
                value={displayMode}
                exclusive
                onChange={handleDisplayModeChange}
                size="small"
              >
                <ToggleButton value="importance">
                  <Typography variant="caption">Raw</Typography>
                </ToggleButton>
                <ToggleButton value="normalized">
                  <Typography variant="caption">Normalized</Typography>
                </ToggleButton>
              </ToggleButtonGroup>
            </Stack>
          </Box>

          <Box sx={{ width: '100%', height: 500 }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarChartData}>
                <PolarGrid stroke="#d0d0d0" />
                <PolarAngleAxis
                  dataKey="feature"
                  tick={{ fill: '#666', fontSize: 12 }}
                  tickLine={false}
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 'auto']}
                  tick={{ fill: '#999', fontSize: 11 }}
                  tickFormatter={(value) => `${value}%`}
                />
                <RechartsTooltip content={<CustomTooltip />} />
                <Radar
                  name="Feature Importance"
                  dataKey="value"
                  stroke="#1976d2"
                  fill="#1976d2"
                  fillOpacity={0.4}
                  strokeWidth={2}
                />
                <Legend
                  wrapperStyle={{
                    paddingTop: '20px',
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </Box>

          {/* Feature Legend */}
          <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Feature Details
            </Typography>
            <Grid container spacing={1}>
              {radarChartData.map((feature, index) => (
                <Grid item xs={12} sm={6} md={3} key={feature.feature_name}>
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 1.5,
                      height: '100%',
                      borderLeft: 3,
                      borderLeftColor: index < 3 ? 'primary.main' : 'info.main',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                      <Chip
                        label={`#${index + 1}`}
                        size="small"
                        color={index < 3 ? 'primary' : 'default'}
                        sx={{ height: 18, fontSize: '0.65rem' }}
                      />
                      <Typography variant="caption" fontWeight={600}>
                        {feature.value.toFixed(1)}%
                      </Typography>
                    </Box>
                    <Typography variant="body2" fontWeight={600} gutterBottom>
                      {formatFeatureName(feature.feature_name)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                      {feature.description}
                    </Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Box>
        </CardContent>
      </Card>

      {/* Info Alert */}
      <Alert severity="info" sx={{ mt: 3 }} icon={<InfoIcon />}>
        <AlertTitle>Understanding the Radar Chart</AlertTitle>
        <Typography variant="body2">
          The radar chart provides a multi-dimensional view of feature importance. Each axis represents
          a different feature, and the distance from the center indicates the feature's importance.
          Features closer to the edge have higher importance. Toggle between <strong>Raw</strong> mode
          (shows actual importance percentages) and <strong>Normalized</strong> mode (shows relative
          importance as a proportion of total importance).
        </Typography>
      </Alert>
    </Box>
  );
};

export default FeatureRadarChart;
