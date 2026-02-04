import React, { useState, useEffect } from 'react';
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
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';

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
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<KeyMetricsResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

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
  }, [apiUrl, startDate, endDate]);

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
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        css={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '64px 0',
        }}
      >
        <CircularProgress size={60} css={{ marginBottom: '24px' }} />
        <Typography variant="h6" color="secondary">
          Loading key metrics...
        </Typography>
        <Typography variant="body2" color="secondary" css={{ marginTop: '8px' }}>
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
          <Button color="inherit" onClick={fetchMetrics} startIcon={<Icon name="refresh" />}>
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
      <Paper elevation={2} css={{ padding: '24px' }}>
        <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <Typography variant="h5" fontWeight={600}>
            Key Hiring Metrics
          </Typography>
          <Box css={{ display: 'flex', gap: '8px' }}>
            <Button
              variant={autoRefreshEnabled ? 'contained' : 'outlined'}
              startIcon={<Icon name={autoRefreshEnabled ? 'pause' : 'play-arrow'} />}
              onClick={toggleAutoRefresh}
              size="small"
              color={autoRefreshEnabled ? 'primary' : 'default'}
            >
              {autoRefreshEnabled ? 'Auto-refresh' : 'Paused'}
            </Button>
            <Button variant="outlined" startIcon={<Icon name="refresh" />} onClick={fetchMetrics} size="small">
              Refresh
            </Button>
          </Box>
        </Box>

        <Grid container spacing={2}>
          {/* Time-to-Hire Card */}
          <Grid item xs={12} sm={6} md={4}>
            <Card
              variant="outlined"
              css={{
                height: '100%',
                borderColor: metrics.time_to_hire.average_days <= 30 ? '$success' : '$warning',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                },
              }}
            >
              <CardContent>
                <Box css={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                  <Icon
                    name="clock"
                    size={24}
                    color={metrics.time_to_hire.average_days <= 30 ? '$success' : '$warning'}
                  />
                  <Typography variant="h6" fontWeight={600} css={{ marginLeft: '8px' }}>
                    Time-to-Hire
                  </Typography>
                </Box>

                <Box css={{ marginBottom: '16px' }}>
                  <Typography variant="caption" color="secondary">
                    Average
                  </Typography>
                  <Typography
                    variant="h4"
                    fontWeight={700}
                    color={metrics.time_to_hire.average_days <= 30 ? '$success' : '$warning'}
                  >
                    {metrics.time_to_hire.average_days.toFixed(1)}d
                  </Typography>
                </Box>

                <Stack spacing={1}>
                  <Box css={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="secondary">
                      Median
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {metrics.time_to_hire.median_days.toFixed(1)}d
                    </Typography>
                  </Box>
                  <Box css={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="secondary">
                      Range
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {metrics.time_to_hire.min_days}d - {metrics.time_to_hire.max_days}d
                    </Typography>
                  </Box>
                  <Box css={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="secondary">
                      25th-75th %
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {metrics.time_to_hire.percentile_25.toFixed(1)}d - {metrics.time_to_hire.percentile_75.toFixed(1)}d
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {/* Resumes Processed Card */}
          <Grid item xs={12} sm={6} md={4}>
            <Card
              variant="outlined"
              css={{
                height: '100%',
                borderColor: '$primary',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                },
              }}
            >
              <CardContent>
                <Box css={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                  <Icon name="description" size={24} color="$primary" />
                  <Typography variant="h6" fontWeight={600} css={{ marginLeft: '8px' }}>
                    Resumes Processed
                  </Typography>
                </Box>

                <Box css={{ marginBottom: '16px' }}>
                  <Typography variant="caption" color="secondary">
                    Total
                  </Typography>
                  <Typography variant="h4" fontWeight={700} color="$primary">
                    {metrics.resumes.total_processed.toLocaleString()}
                  </Typography>
                </Box>

                <Stack spacing={1}>
                  <Box css={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="secondary">
                      This Month
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {metrics.resumes.processed_this_month.toLocaleString()}
                    </Typography>
                  </Box>
                  <Box css={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="secondary">
                      This Week
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {metrics.resumes.processed_this_week.toLocaleString()}
                    </Typography>
                  </Box>
                  <Box css={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="secondary">
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
              css={{
                height: '100%',
                borderColor: metrics.match_rates.overall_match_rate >= 0.8 ? '$success' : '$warning',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                },
              }}
            >
              <CardContent>
                <Box css={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                  <Icon
                    name="trending-up"
                    size={24}
                    color={metrics.match_rates.overall_match_rate >= 0.8 ? '$success' : '$warning'}
                  />
                  <Typography variant="h6" fontWeight={600} css={{ marginLeft: '8px' }}>
                    Match Rates
                  </Typography>
                </Box>

                <Box css={{ marginBottom: '16px' }}>
                  <Typography variant="caption" color="secondary">
                    Overall
                  </Typography>
                  <Typography
                    variant="h4"
                    fontWeight={700}
                    color={metrics.match_rates.overall_match_rate >= 0.8 ? '$success' : '$warning'}
                  >
                    {(metrics.match_rates.overall_match_rate * 100).toFixed(1)}%
                  </Typography>
                </Box>

                <Stack spacing={1}>
                  <Box css={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="secondary">
                      Avg Confidence
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {(metrics.match_rates.average_confidence * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box css={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="secondary">
                      High Confidence
                    </Typography>
                    <Typography variant="body2" fontWeight={600} color="$success">
                      {metrics.match_rates.high_confidence_matches.toLocaleString()}
                    </Typography>
                  </Box>
                  <Box css={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="secondary">
                      Low Confidence
                    </Typography>
                    <Typography variant="body2" fontWeight={600} color="$warning">
                      {metrics.match_rates.low_confidence_matches.toLocaleString()}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
    </Stack>
  );
};

export default KeyMetrics;
