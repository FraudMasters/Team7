import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Button,
  Alert,
  AlertTitle,
  Stack,
  Grid,
  LinearProgress,
  Chip,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Insights as ForecastIcon,
  Schedule as TimeIcon,
  Business as DepartmentIcon,
  HealthAndSafety as HealthIcon,
  Lightbulb as RecommendationIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
} from '@mui/icons-material';

/**
 * Pipeline forecast metrics from backend
 */
interface PipelineForecast {
  period: string;
  expected_candidates: number;
  expected_hires: number;
  confidence_level: number;
}

/**
 * Hiring needs prediction metrics from backend
 */
interface HiringNeedsPrediction {
  department: string;
  open_positions: number;
  predicted_openings: number;
  priority_level: 'high' | 'medium' | 'low';
}

/**
 * Time-to-fill prediction metrics from backend
 */
interface TimeToFillPrediction {
  average_days: number;
  min_days: number;
  max_days: number;
  trend: 'improving' | 'stable' | 'worsening';
}

/**
 * Predictive analytics response from backend
 */
interface PredictiveAnalyticsResponse {
  pipeline_forecast: PipelineForecast[];
  hiring_needs: HiringNeedsPrediction[];
  time_to_fill_prediction: TimeToFillPrediction;
  pipeline_health_score: number;
  recommendations: string[];
}

/**
 * PredictiveAnalytics Component Props
 */
interface PredictiveAnalyticsProps {
  /** API endpoint URL for predictive analytics */
  apiUrl?: string;
  /** Forecast period: 'next_30_days', 'next_quarter', or 'next_semester' */
  forecastPeriod?: string;
  /** Optional department filter */
  department?: string;
  /** Optional refresh key to trigger manual refresh */
  refreshKey?: number;
}

/**
 * Format period for display
 */
const formatPeriod = (period: string): string => {
  const periodMap: Record<string, string> = {
    next_30_days: 'Next 30 Days',
    next_quarter: 'Next Quarter',
    next_semester: 'Next Semester',
  };
  return periodMap[period] || period.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
};

/**
 * Get priority color
 */
const getPriorityColor = (priority: string): string => {
  const colorMap: Record<string, string> = {
    high: 'error.main',
    medium: 'warning.main',
    low: 'success.main',
  };
  return colorMap[priority] || 'default';
};

/**
 * Get trend icon
 */
const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'improving':
      return <TrendingUpIcon fontSize="small" color="success" />;
    case 'worsening':
      return <TrendingDownIcon fontSize="small" color="error" />;
    default:
      return null;
  }
};

/**
 * PredictiveAnalytics Component
 *
 * Displays predictive analytics and forecasting including:
 * - Pipeline forecast for multiple time periods (expected candidates and hires)
 * - Hiring needs predictions by department with priority levels
 * - Time-to-fill projections with trend analysis
 * - Overall pipeline health score
 * - Actionable recommendations based on predictions
 *
 * @example
 * ```tsx
 * <PredictiveAnalytics />
 * ```
 *
 * @example
 * ```tsx
 * <PredictiveAnalytics forecastPeriod="next_quarter" department="Engineering" />
 * ```
 */
const PredictiveAnalytics: React.FC<PredictiveAnalyticsProps> = ({
  apiUrl = '/api/analytics/predictive',
  forecastPeriod = 'next_30_days',
  department,
  refreshKey,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [predictiveData, setPredictiveData] = useState<PredictiveAnalyticsResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  /**
   * Fetch predictive analytics from backend
   */
  const fetchPredictiveData = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: Record<string, string> = {
        forecast_period: forecastPeriod,
      };
      if (department) {
        params.department = department;
      }

      const response = await axios.get<PredictiveAnalyticsResponse>(apiUrl, { params });
      setPredictiveData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load predictive analytics';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Initial fetch on mount and when filters change
   */
  useEffect(() => {
    fetchPredictiveData();
  }, [apiUrl, forecastPeriod, department, refreshKey]);

  /**
   * Auto-refresh every 60 seconds when enabled
   */
  useEffect(() => {
    if (!autoRefreshEnabled) {
      return;
    }

    const interval = setInterval(() => {
      fetchPredictiveData();
    }, 60000); // 60 seconds

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, apiUrl, forecastPeriod, department]);

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = () => {
    setAutoRefreshEnabled((prev) => !prev);
  };

  /**
   * Render loading state
   */
  if (loading) {
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
          Loading predictive analytics...
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
          <Button color="inherit" onClick={fetchPredictiveData} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Predictive Analytics</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!predictiveData) {
    return null;
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ForecastIcon fontSize="large" color="primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Predictive Analytics
              </Typography>
              <Typography variant="body2" color="text.secondary">
                AI-powered forecasting and insights for your recruitment pipeline
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant={autoRefreshEnabled ? 'contained' : 'outlined'}
              startIcon={autoRefreshEnabled ? <PauseIcon /> : <PlayIcon />}
              onClick={toggleAutoRefresh}
              size="small"
              color={autoRefreshEnabled ? 'primary' : 'default'}
            >
              {autoRefreshEnabled ? 'Auto-refresh' : 'Paused'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchPredictiveData}
              size="small"
            >
              Refresh
            </Button>
          </Box>
        </Box>

        {/* Pipeline Health Score */}
        <Card
          variant="outlined"
          sx={{
            mb: 3,
            borderColor:
              predictiveData.pipeline_health_score >= 0.7
                ? 'success.main'
                : predictiveData.pipeline_health_score >= 0.5
                  ? 'warning.main'
                  : 'error.main',
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <HealthIcon
                  fontSize="large"
                  color={
                    predictiveData.pipeline_health_score >= 0.7
                      ? 'success'
                      : predictiveData.pipeline_health_score >= 0.5
                        ? 'warning'
                        : 'error'
                  }
                />
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    Pipeline Health Score
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Overall recruitment pipeline assessment
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ textAlign: 'right' }}>
                <Typography
                  variant="h3"
                  fontWeight={700}
                  color={
                    predictiveData.pipeline_health_score >= 0.7
                      ? 'success.main'
                      : predictiveData.pipeline_health_score >= 0.5
                        ? 'warning.main'
                        : 'error.main'
                  }
                >
                  {(predictiveData.pipeline_health_score * 100).toFixed(0)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {predictiveData.pipeline_health_score >= 0.7
                    ? 'Excellent'
                    : predictiveData.pipeline_health_score >= 0.5
                      ? 'Good'
                      : 'Needs Attention'}
                </Typography>
              </Box>
            </Box>
            <Box sx={{ mt: 2 }}>
              <LinearProgress
                variant="determinate"
                value={predictiveData.pipeline_health_score * 100}
                sx={{
                  height: 10,
                  borderRadius: 1,
                  bgcolor: 'action.hover',
                  '& .MuiLinearProgress-bar': {
                    bgcolor:
                      predictiveData.pipeline_health_score >= 0.7
                        ? 'success.main'
                        : predictiveData.pipeline_health_score >= 0.5
                          ? 'warning.main'
                          : 'error.main',
                  },
                }}
              />
            </Box>
          </CardContent>
        </Card>

        {/* Pipeline Forecast Cards */}
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Pipeline Forecast
        </Typography>
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {predictiveData.pipeline_forecast.map((forecast) => (
            <Grid item xs={12} sm={6} md={4} key={forecast.period}>
              <Card
                variant="outlined"
                sx={{
                  height: '100%',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <TimeIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="subtitle1" fontWeight={600}>
                      {formatPeriod(forecast.period)}
                    </Typography>
                  </Box>

                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Expected Candidates
                      </Typography>
                      <Typography variant="h5" fontWeight={700} color="primary.main">
                        {forecast.expected_candidates.toLocaleString()}
                      </Typography>
                    </Box>

                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Expected Hires
                      </Typography>
                      <Typography variant="h5" fontWeight={700} color="success.main">
                        {forecast.expected_hires.toLocaleString()}
                      </Typography>
                    </Box>

                    <Box>
                      <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                        Confidence Level
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ flexGrow: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={forecast.confidence_level * 100}
                            sx={{
                              height: 8,
                              borderRadius: 1,
                              bgcolor: 'action.hover',
                              '& .MuiLinearProgress-bar': {
                                bgcolor:
                                  forecast.confidence_level >= 0.7
                                    ? 'success.main'
                                    : forecast.confidence_level >= 0.5
                                      ? 'warning.main'
                                      : 'error.main',
                              },
                            }}
                          />
                        </Box>
                        <Typography variant="body2" fontWeight={600} sx={{ minWidth: 45 }}>
                          {(forecast.confidence_level * 100).toFixed(0)}%
                        </Typography>
                      </Box>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        <Divider sx={{ my: 3 }} />

        {/* Time-to-Fill Prediction */}
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Time-to-Fill Prediction
        </Typography>
        <Card
          variant="outlined"
          sx={{
            mb: 3,
            borderColor:
              predictiveData.time_to_fill_prediction.trend === 'improving'
                ? 'success.main'
                : predictiveData.time_to_fill_prediction.trend === 'worsening'
                  ? 'error.main'
                  : 'info.main',
          }}
        >
          <CardContent>
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={12} sm={6}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Average Time-to-Fill
                  </Typography>
                  <Typography variant="h4" fontWeight={700} color="primary.main">
                    {predictiveData.time_to_fill_prediction.average_days.toFixed(1)} days
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={2}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Min
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {predictiveData.time_to_fill_prediction.min_days}d
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={2}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Max
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {predictiveData.time_to_fill_prediction.max_days}d
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={2}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                  {getTrendIcon(predictiveData.time_to_fill_prediction.trend)}
                  <Typography
                    variant="body1"
                    fontWeight={600}
                    textTransform="capitalize"
                    color={
                      predictiveData.time_to_fill_prediction.trend === 'improving'
                        ? 'success.main'
                        : predictiveData.time_to_fill_prediction.trend === 'worsening'
                          ? 'error.main'
                          : 'text.primary'
                    }
                  >
                    {predictiveData.time_to_fill_prediction.trend}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Divider sx={{ my: 3 }} />

        {/* Hiring Needs by Department */}
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Hiring Needs Prediction
        </Typography>
        <Stack spacing={2} sx={{ mb: 3 }}>
          {predictiveData.hiring_needs.map((need) => (
            <Card
              key={need.department}
              variant="outlined"
              sx={{
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateX(4px)',
                  boxShadow: 2,
                },
              }}
            >
              <CardContent sx={{ py: 2 }}>
                <Grid container spacing={2} alignItems="center">
                  {/* Department Name */}
                  <Grid item xs={12} sm={4}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <DepartmentIcon fontSize="small" color="primary" />
                      <Typography variant="subtitle1" fontWeight={600}>
                        {need.department}
                      </Typography>
                    </Box>
                  </Grid>

                  {/* Open Positions */}
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Open Positions
                    </Typography>
                    <Typography variant="h6" fontWeight={700}>
                      {need.open_positions}
                    </Typography>
                  </Grid>

                  {/* Predicted Openings */}
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Predicted Additional
                    </Typography>
                    <Typography variant="h6" fontWeight={700} color="primary.main">
                      +{need.predicted_openings}
                    </Typography>
                  </Grid>

                  {/* Priority */}
                  <Grid item xs={12} sm={2}>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <Chip
                        label={need.priority_level.toUpperCase()}
                        size="small"
                        color={need.priority_level === 'high' ? 'error' : need.priority_level === 'medium' ? 'warning' : 'success'}
                        sx={{ fontWeight: 700 }}
                      />
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          ))}
        </Stack>

        <Divider sx={{ my: 3 }} />

        {/* Recommendations */}
        <Typography variant="h6" fontWeight={600} gutterBottom>
          AI-Generated Recommendations
        </Typography>
        <Card variant="outlined">
          <CardContent>
            <Stack spacing={2}>
              {predictiveData.recommendations.map((recommendation, index) => (
                <Box
                  key={index}
                  sx={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 2,
                    p: 2,
                    borderRadius: 1,
                    bgcolor: 'action.hover',
                  }}
                >
                  <RecommendationIcon color="primary" sx={{ mt: 0.5 }} />
                  <Typography variant="body2">{recommendation}</Typography>
                </Box>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Paper>
    </Stack>
  );
};

export default PredictiveAnalytics;
