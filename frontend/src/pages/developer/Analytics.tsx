/**
 * API Usage Analytics Page
 *
 * Main page for viewing API usage analytics including request counts,
 * response times, endpoint usage, and error tracking.
 *
 * @module pages/developer/Analytics
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  Stack,
  Grid,
  Card,
  CardContent,
  Alert,
  AlertTitle,
  CircularProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  AccessTime as TimeIcon,
} from '@mui/icons-material';
import { analyticsClient } from '@/api/analytics';
import APIUsageChart from '@/components/developer/APIUsageChart';
import { DateRangeFilter, type DateRangeFilter as DateRangeFilterType } from '@/components/analytics/DateRangeFilter';

/**
 * Analytics Page Component
 *
 * Provides comprehensive API usage analytics:
 * - Request volume over time
 * - Response time metrics
 * - Endpoint usage statistics
 * - Status code distribution
 * - Error tracking
 *
 * @example
 * ```tsx
 * // Routed at /developer/analytics
 * import { Analytics } from '@/pages/developer/Analytics';
 * ```
 */
const Analytics: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<{
    summary: {
      total_requests: number;
      successful_requests: number;
      failed_requests: number;
      rate_limited_requests: number;
      average_response_time_ms: number;
      p95_response_time_ms: number;
      p99_response_time_ms: number;
      unique_endpoints: number;
    };
    requests_by_time: Array<{
      timestamp: string;
      count: number;
      success_count: number;
      error_count: number;
    }>;
    response_times: Array<{
      timestamp: string;
      average_ms: number;
      p50_ms: number;
      p95_ms: number;
      p99_ms: number;
    }>;
    top_endpoints: Array<{
      endpoint: string;
      method: string;
      request_count: number;
      success_count: number;
      error_count: number;
      average_response_time_ms: number;
      error_rate: number;
    }>;
    status_codes: Array<{
      status_code: number;
      count: number;
      percentage: number;
    }>;
  } | null>(null);

  const [dateRange, setDateRange] = useState<DateRangeFilterType>({
    preset: 'last_7_days',
    startDate: '',
    endDate: '',
  });

  /**
   * Fetch analytics data from backend
   */
  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await analyticsClient.getAPIUsageAnalytics(
        dateRange.startDate || undefined,
        dateRange.endDate || undefined,
        'day'
      );
      setAnalytics(data as any);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  }, [dateRange]);

  /**
   * Initial fetch on mount and when date range changes
   */
  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  /**
   * Handle date range change
   */
  const handleDateRangeChange = useCallback((newDateRange: DateRangeFilterType) => {
    setDateRange(newDateRange);
  }, []);

  /**
   * Handle refresh
   */
  const handleRefresh = useCallback(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 2 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            py: 12,
          }}
        >
          <CircularProgress size={60} sx={{ mb: 3 }} />
          <Typography variant="h6" color="text.secondary">
            Loading API usage analytics...
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This may take a few moments
          </Typography>
        </Box>
      </Container>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 2 }}>
        <Alert
          severity="error"
          action={
            <Button color="inherit" onClick={fetchAnalytics} startIcon={<RefreshIcon />}>
              Retry
            </Button>
          }
        >
          <AlertTitle>Failed to Load Analytics</AlertTitle>
          {error}
        </Alert>
      </Container>
    );
  }

  if (!analytics) {
    return null;
  }

  const successRate =
    analytics.summary.total_requests > 0
      ? (analytics.summary.successful_requests / analytics.summary.total_requests) * 100
      : 0;
  const errorRate =
    analytics.summary.total_requests > 0
      ? (analytics.summary.failed_requests / analytics.summary.total_requests) * 100
      : 0;

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            API Usage Analytics
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor your API usage, performance metrics, and error rates
          </Typography>
        </Box>
        <Button variant="outlined" startIcon={<RefreshIcon />} onClick={handleRefresh} size="large">
          Refresh
        </Button>
      </Stack>

      {/* Summary Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
              border: '1px solid',
              borderColor: 'primary.main',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                  }}
                >
                  <TimelineIcon />
                </Box>
                <Box>
                  <Typography variant="h5" fontWeight={700}>
                    {analytics.summary.total_requests.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Requests
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
              border: '1px solid',
              borderColor: 'success.main',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                  }}
                >
                  <SuccessIcon />
                </Box>
                <Box>
                  <Typography variant="h5" fontWeight={700}>
                    {successRate.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Success Rate
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%)',
              border: '1px solid',
              borderColor: 'warning.main',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                  }}
                >
                  <SpeedIcon />
                </Box>
                <Box>
                  <Typography variant="h5" fontWeight={700}>
                    {analytics.summary.average_response_time_ms}ms
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg Response Time
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%)',
              border: '1px solid',
              borderColor: 'error.main',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                  }}
                >
                  <ErrorIcon />
                </Box>
                <Box>
                  <Typography variant="h5" fontWeight={700}>
                    {analytics.summary.failed_requests.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Failed Requests
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <TimeIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  p95 Response Time
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="primary.main">
                {analytics.summary.p95_response_time_ms}ms
              </Typography>
              <Typography variant="body2" color="text.secondary">
                95% of requests complete within this time
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <SpeedIcon color="info" />
                <Typography variant="h6" fontWeight={600}>
                  p99 Response Time
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="info.main">
                {analytics.summary.p99_response_time_ms}ms
              </Typography>
              <Typography variant="body2" color="text.secondary">
                99% of requests complete within this time
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <TimelineIcon color="success" />
                <Typography variant="h6" fontWeight={600}>
                  Active Endpoints
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="success.main">
                {analytics.summary.unique_endpoints}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Number of unique API endpoints used
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Date Range Filter */}
      <Box sx={{ mb: 4 }}>
        <DateRangeFilter
          onDateRangeChange={handleDateRangeChange}
          onApply={handleDateRangeChange}
          initialDateRange={dateRange}
          label="Filter Analytics by Date Range"
        />
      </Box>

      {/* Getting Started Section */}
      <Paper sx={{ p: 3, mb: 4, border: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Understanding Your API Usage
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Monitor your API usage to optimize performance and identify issues. Track request volumes,
          response times, and error rates to ensure your integration runs smoothly.
        </Typography>

        <Stack direction="row" spacing={1} flexWrap="wrap">
          <Box
            component="span"
            sx={{
              px: 2,
              py: 1,
              borderRadius: 1,
              bgcolor: 'success.50',
              color: 'success.dark',
              fontSize: '0.875rem',
            }}
          >
            <strong>Success Rate:</strong> Percentage of requests that completed successfully
          </Box>
          <Box
            component="span"
            sx={{
              px: 2,
              py: 1,
              borderRadius: 1,
              bgcolor: 'warning.50',
              color: 'warning.dark',
              fontSize: '0.875rem',
            }}
          >
            <strong>p95/p99:</strong> Response time percentiles (95%/99% of requests)
          </Box>
        </Stack>
      </Paper>

      {/* Charts */}
      <APIUsageChart
        requestCounts={analytics.requests_by_time}
        responseTimes={analytics.response_times}
        topEndpoints={analytics.top_endpoints}
        statusCodes={analytics.status_codes}
      />

      {/* Alerts for rate limiting */}
      {analytics.summary.rate_limited_requests > 0 && (
        <Alert severity="warning" sx={{ mt: 4 }}>
          <AlertTitle>Rate Limiting Detected</AlertTitle>
          {analytics.summary.rate_limited_requests.toLocaleString()} requests were rate limited during
          this period. Consider upgrading your plan or optimizing your request patterns.
        </Alert>
      )}

      {/* Alerts for high error rate */}
      {errorRate > 5 && (
        <Alert severity="error" sx={{ mt: 4 }}>
          <AlertTitle>High Error Rate Detected</AlertTitle>
          Your error rate is {errorRate.toFixed(1)}%, which is above the recommended threshold of 5%.
          Review the error details below and check your integration for issues.
        </Alert>
      )}
    </Container>
  );
};

export default Analytics;
