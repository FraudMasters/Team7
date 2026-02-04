import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
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
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Schedule as TimeIcon,
  Description as ResumeIcon,
  TrendingUp as MatchIcon,
  AccessTime as ClockIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  ErrorOutline as WarningIcon,
  OpenInNew as DrillDownIcon,
} from '@mui/icons-material';
import DrillDownModal, { AnomalyType } from './DrillDownModal';

/**
 * Time-to-hire metrics from backend
 */
interface TimeToHireMetrics {
  average_days: number;
  median_days: number;
  min_days: number;
  max_days: number;
  percentile_25: number;
  percentile_75: number;
}

/**
 * Resume processing metrics from backend
 */
interface ResumeMetrics {
  total_processed: number;
  processed_this_month: number;
  processed_this_week: number;
  processing_rate_avg: number;
}

/**
 * Match rate metrics from backend
 */
interface MatchRateMetrics {
  overall_match_rate: number;
  high_confidence_matches: number;
  low_confidence_matches: number;
  average_confidence: number;
}

/**
 * Key metrics response from backend
 */
interface KeyMetricsResponse {
  time_to_hire: TimeToHireMetrics;
  resumes: ResumeMetrics;
  match_rates: MatchRateMetrics;
}

/**
 * KeyMetrics Component Props
 */
interface KeyMetricsProps {
  /** API endpoint URL for key metrics */
  apiUrl?: string;
  /** Optional date range filter */
  startDate?: string;
  /** Optional date range filter */
  endDate?: string;
  /** Optional refresh key to trigger manual refresh */
  refreshKey?: number;
}

/**
 * KeyMetrics Component
 *
 * Displays key hiring metrics including:
 * - Time-to-hire statistics (average, median, min, max, percentiles)
 * - Resume processing metrics (total, monthly, weekly, processing rate)
 * - Match rates (overall, high/low confidence, average confidence)
 *
 * @example
 * ```tsx
 * <KeyMetrics />
 * ```
 *
 * @example
 * ```tsx
 * <KeyMetrics startDate="2024-01-01" endDate="2024-12-31" />
 * ```
 */
const KeyMetrics: React.FC<KeyMetricsProps> = ({
  apiUrl = '/api/analytics/key-metrics',
  startDate,
  endDate,
  refreshKey,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<KeyMetricsResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  // Drill-down modal state
  const [drillDownOpen, setDrillDownOpen] = useState(false);
  const [anomalyType, setAnomalyType] = useState<AnomalyType | null>(null);
  const [anomalyDescription, setAnomalyDescription] = useState<string | null>(null);

  /**
   * Fetch key metrics from backend
   */
  const fetchMetrics = async () => {
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

      const response = await axios.get<KeyMetricsResponse>(apiUrl, { params });
      setMetrics(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load metrics data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Initial fetch on mount and when date range changes
   */
  useEffect(() => {
    fetchMetrics();
  }, [apiUrl, startDate, endDate, refreshKey]);

  /**
   * Auto-refresh every 60 seconds when enabled
   */
  useEffect(() => {
    if (!autoRefreshEnabled) {
      return;
    }

    const interval = setInterval(() => {
      fetchMetrics();
    }, 60000); // 60 seconds

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, apiUrl, startDate, endDate]);

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = () => {
    setAutoRefreshEnabled((prev) => !prev);
  };

  /**
   * Handle opening drill-down modal for time-to-hire anomaly
   */
  const handleTimeToHireDrillDown = useCallback(() => {
    if (!metrics || metrics.time_to_hire.average_days <= 30) {
      return;
    }
    setAnomalyType('high_duration');
    setAnomalyDescription(
      `Time-to-hire is ${metrics.time_to_hire.average_days.toFixed(1)} days on average, ` +
      `which exceeds the 30-day target. Investigate which positions or stages are causing delays.`
    );
    setDrillDownOpen(true);
  }, [metrics]);

  /**
   * Handle opening drill-down modal for match rate anomaly
   */
  const handleMatchRateDrillDown = useCallback(() => {
    if (!metrics || metrics.match_rates.overall_match_rate >= 0.8) {
      return;
    }
    setAnomalyType('low_match_rate');
    setAnomalyDescription(
      `Overall match rate is ${(metrics.match_rates.overall_match_rate * 100).toFixed(1)}%, ` +
      `which is below the 80% target. Investigate quality of matches and low-confidence predictions.`
    );
    setDrillDownOpen(true);
  }, [metrics]);

  /**
   * Handle closing drill-down modal
   */
  const handleDrillDownClose = useCallback(() => {
    setDrillDownOpen(false);
    setAnomalyType(null);
    setAnomalyDescription(null);
  }, []);

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
          Loading key metrics...
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
          <Button color="inherit" onClick={fetchMetrics} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Metrics</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!metrics) {
    return null;
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Key Hiring Metrics
          </Typography>
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
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchMetrics} size="small">
              Refresh
            </Button>
          </Box>
        </Box>

        <Grid container spacing={2}>
          {/* Time-to-Hire Card */}
          <Grid item xs={12} sm={6} md={4}>
            <Card
              variant="outlined"
              onClick={handleTimeToHireDrillDown}
              sx={{
                height: '100%',
                borderColor: metrics.time_to_hire.average_days <= 30 ? 'success.main' : 'warning.main',
                transition: 'transform 0.2s, box-shadow 0.2s',
                cursor: metrics.time_to_hire.average_days > 30 ? 'pointer' : 'default',
                '&:hover': metrics.time_to_hire.average_days > 30 ? {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                } : {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <ClockIcon
                      fontSize="large"
                      sx={{
                        mr: 1,
                        color: metrics.time_to_hire.average_days <= 30 ? 'success.main' : 'warning.main',
                      }}
                    />
                    <Typography variant="h6" fontWeight={600}>
                      Time-to-Hire
                    </Typography>
                  </Box>
                  {metrics.time_to_hire.average_days > 30 && (
                    <Chip
                      icon={<WarningIcon fontSize="small" />}
                      label="Anomaly"
                      size="small"
                      color="warning"
                      sx={{ fontWeight: 600 }}
                    />
                  )}
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Average
                  </Typography>
                  <Typography
                    variant="h4"
                    fontWeight={700}
                    color={metrics.time_to_hire.average_days <= 30 ? 'success.main' : 'warning.main'}
                  >
                    {metrics.time_to_hire.average_days.toFixed(1)}d
                  </Typography>
                </Box>

                <Stack spacing={1}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Median
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {metrics.time_to_hire.median_days.toFixed(1)}d
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Range
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {metrics.time_to_hire.min_days}d - {metrics.time_to_hire.max_days}d
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      25th-75th %
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {metrics.time_to_hire.percentile_25.toFixed(1)}d - {metrics.time_to_hire.percentile_75.toFixed(1)}d
                    </Typography>
                  </Box>
                </Stack>
                {metrics.time_to_hire.average_days > 30 && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 2, pt: 1, borderTop: 1, borderColor: 'divider' }}>
                    <DrillDownIcon fontSize="small" color="warning" />
                    <Typography variant="caption" color="warning.main" fontWeight={600}>
                      Click to investigate
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Resumes Processed Card */}
          <Grid item xs={12} sm={6} md={4}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: 'primary.main',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <ResumeIcon fontSize="large" sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6" fontWeight={600}>
                    Resumes Processed
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Total
                  </Typography>
                  <Typography variant="h4" fontWeight={700} color="primary.main">
                    {metrics.resumes.total_processed.toLocaleString()}
                  </Typography>
                </Box>

                <Stack spacing={1}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      This Month
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {metrics.resumes.processed_this_month.toLocaleString()}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      This Week
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {metrics.resumes.processed_this_week.toLocaleString()}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Avg/Day
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {metrics.resumes.processing_rate_avg.toFixed(1)}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {/* Match Rates Card */}
          <Grid item xs={12} sm={6} md={4}>
            <Card
              variant="outlined"
              onClick={handleMatchRateDrillDown}
              sx={{
                height: '100%',
                borderColor: metrics.match_rates.overall_match_rate >= 0.8 ? 'success.main' : 'warning.main',
                transition: 'transform 0.2s, box-shadow 0.2s',
                cursor: metrics.match_rates.overall_match_rate < 0.8 ? 'pointer' : 'default',
                '&:hover': metrics.match_rates.overall_match_rate < 0.8 ? {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                } : {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <MatchIcon
                      fontSize="large"
                      sx={{
                        mr: 1,
                        color: metrics.match_rates.overall_match_rate >= 0.8 ? 'success.main' : 'warning.main',
                      }}
                    />
                    <Typography variant="h6" fontWeight={600}>
                      Match Rates
                    </Typography>
                  </Box>
                  {metrics.match_rates.overall_match_rate < 0.8 && (
                    <Chip
                      icon={<WarningIcon fontSize="small" />}
                      label="Anomaly"
                      size="small"
                      color="warning"
                      sx={{ fontWeight: 600 }}
                    />
                  )}
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Overall
                  </Typography>
                  <Typography
                    variant="h4"
                    fontWeight={700}
                    color={metrics.match_rates.overall_match_rate >= 0.8 ? 'success.main' : 'warning.main'}
                  >
                    {(metrics.match_rates.overall_match_rate * 100).toFixed(1)}%
                  </Typography>
                </Box>

                <Stack spacing={1}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Avg Confidence
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {(metrics.match_rates.average_confidence * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      High Confidence
                    </Typography>
                    <Typography variant="body2" fontWeight={600} color="success.main">
                      {metrics.match_rates.high_confidence_matches.toLocaleString()}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Low Confidence
                    </Typography>
                    <Typography variant="body2" fontWeight={600} color="warning.main">
                      {metrics.match_rates.low_confidence_matches.toLocaleString()}
                    </Typography>
                  </Box>
                </Stack>
                {metrics.match_rates.overall_match_rate < 0.8 && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 2, pt: 1, borderTop: 1, borderColor: 'divider' }}>
                    <DrillDownIcon fontSize="small" color="warning" />
                    <Typography variant="caption" color="warning.main" fontWeight={600}>
                      Click to investigate
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Drill-Down Modal */}
      {anomalyType && (
        <DrillDownModal
          open={drillDownOpen}
          onClose={handleDrillDownClose}
          anomalyType={anomalyType}
          anomalyDescription={anomalyDescription || undefined}
          startDate={startDate}
          endDate={endDate}
          metricName={anomalyType === 'high_duration' ? 'time_to_hire' : 'overall_match_rate'}
        />
      )}
    </Stack>
  );
};

export default KeyMetrics;
