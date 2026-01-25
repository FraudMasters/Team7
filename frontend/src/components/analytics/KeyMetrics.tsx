import React, { useState, useEffect } from 'react';
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
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Schedule as TimeIcon,
  Description as ResumeIcon,
  TrendingUp as MatchIcon,
  AccessTime as ClockIcon,
} from '@mui/icons-material';

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
  apiUrl = 'http://localhost:8000/api/analytics/key-metrics',
  startDate,
  endDate,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<KeyMetricsResponse | null>(null);

  /**
   * Fetch key metrics from backend
   */
  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);

      // Build URL with query parameters
      const url = new URL(apiUrl);
      if (startDate) {
        url.searchParams.append('start_date', startDate);
      }
      if (endDate) {
        url.searchParams.append('end_date', endDate);
      }

      const response = await fetch(url.toString());

      if (!response.ok) {
        throw new Error(`Failed to fetch metrics: ${response.statusText}`);
      }

      const result: KeyMetricsResponse = await response.json();
      setMetrics(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load metrics data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, [apiUrl, startDate, endDate]);

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
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchMetrics} size="small">
            Refresh
          </Button>
        </Box>

        <Grid container spacing={2}>
          {/* Time-to-Hire Card */}
          <Grid item xs={12} sm={6} md={4}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: metrics.time_to_hire.average_days <= 30 ? 'success.main' : 'warning.main',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
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
              sx={{
                height: '100%',
                borderColor: metrics.match_rates.overall_match_rate >= 0.8 ? 'success.main' : 'warning.main',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
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
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
    </Stack>
  );
};

export default KeyMetrics;
