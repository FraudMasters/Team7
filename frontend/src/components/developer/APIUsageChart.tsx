/**
 * API Usage Chart Component
 *
 * Displays API usage metrics with visual charts showing request counts
 * and response times over time.
 *
 * @module components/developer/APIUsageChart
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Stack,
  LinearProgress,
  Chip,
  Grid,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AccessTime as TimeIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import {
  RequestCountByTime,
  ResponseTimeMetrics,
  EndpointUsage,
  StatusCodeDistribution,
} from '@/api/analytics';

/**
 * Format date for display
 */
const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

/**
 * Format timestamp for display
 */
const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();

  if (isToday) {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};

/**
 * Format duration for display
 */
const formatDuration = (ms: number): string => {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  return `${(ms / 1000).toFixed(1)}s`;
};

/**
 * APIUsageChart Component Props
 */
interface APIUsageChartProps {
  /** Request count data by time */
  requestCounts: RequestCountByTime[];
  /** Response time metrics */
  responseTimes: ResponseTimeMetrics[];
  /** Top endpoints by usage */
  topEndpoints: EndpointUsage[];
  /** Status code distribution */
  statusCodes: StatusCodeDistribution[];
  /** Loading state */
  loading?: boolean;
}

/**
 * APIUsageChart Component
 *
 * Displays API usage metrics with visual charts:
 * - Request counts over time with success/error breakdown
 * - Response time metrics (average, p50, p95, p99)
 * - Top endpoints by usage
 * - Status code distribution
 *
 * @example
 * ```tsx
 * <APIUsageChart
 *   requestCounts={requestCounts}
 *   responseTimes={responseTimes}
 *   topEndpoints={topEndpoints}
 *   statusCodes={statusCodes}
 * />
 * ```
 */
const APIUsageChart: React.FC<APIUsageChartProps> = ({
  requestCounts,
  responseTimes,
  topEndpoints,
  statusCodes,
  loading = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Calculate max values for bar chart scaling
  const maxRequestCount = Math.max(...requestCounts.map((d) => d.count), 1);
  const maxResponseTime = Math.max(...responseTimes.map((d) => d.average_ms), 1);
  const maxEndpointCount = Math.max(...topEndpoints.map((e) => e.request_count), 1);

  // Get status code color
  const getStatusCodeColor = (code: number): 'success' | 'warning' | 'error' | 'default' => {
    if (code >= 200 && code < 300) return 'success';
    if (code >= 300 && code < 400) return 'default';
    if (code >= 400 && code < 500) return 'warning';
    return 'error';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <Stack alignItems="center" spacing={2}>
          <LinearProgress sx={{ width: '100%' }} />
          <Typography variant="body2" color="text.secondary">
            Loading API usage data...
          </Typography>
        </Stack>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Request Counts Over Time */}
      <Grid item xs={12} md={6}>
        <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <TrendingUpIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Request Volume
            </Typography>
          </Box>

          <Stack spacing={2}>
            {requestCounts.map((data, index) => {
              const successPercentage = data.count > 0 ? (data.success_count / data.count) * 100 : 0;
              const errorPercentage = data.count > 0 ? (data.error_count / data.count) * 100 : 0;

              return (
                <Box key={data.timestamp}>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 0.5,
                    }}
                  >
                    <Typography variant="caption" color="text.secondary">
                      {formatTimestamp(data.timestamp)}
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {data.count.toLocaleString()}
                    </Typography>
                  </Box>

                  {/* Stacked bar for success/error */}
                  <Box sx={{ display: 'flex', height: 24, borderRadius: 1, overflow: 'hidden' }}>
                    <Box
                      sx={{
                        width: `${successPercentage}%`,
                        bgcolor: 'success.main',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    />
                    <Box
                      sx={{
                        width: `${errorPercentage}%`,
                        bgcolor: 'error.main',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    />
                  </Box>

                  {/* Legend */}
                  <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                    <Chip
                      icon={<SuccessIcon fontSize="small" />}
                      label={`${data.success_count} success`}
                      size="small"
                      color="success"
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                    {data.error_count > 0 && (
                      <Chip
                        icon={<ErrorIcon fontSize="small" />}
                        label={`${data.error_count} errors`}
                        size="small"
                        color="error"
                        variant="outlined"
                        sx={{ height: 20, fontSize: '0.7rem' }}
                      />
                    )}
                  </Box>
                </Box>
              );
            })}
          </Stack>
        </Paper>
      </Grid>

      {/* Response Times */}
      <Grid item xs={12} md={6}>
        <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <TimeIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Response Times
            </Typography>
          </Box>

          <Stack spacing={2}>
            {responseTimes.map((data) => (
              <Box key={data.timestamp}>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 0.5,
                  }}
                >
                  <Typography variant="caption" color="text.secondary">
                    {formatTimestamp(data.timestamp)}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Typography variant="body2" fontWeight={600}>
                      {formatDuration(data.average_ms)}
                    </Typography>
                    <Chip
                      label={`p95: ${formatDuration(data.p95_ms)}`}
                      size="small"
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  </Box>
                </Box>

                <LinearProgress
                  variant="determinate"
                  value={(data.average_ms / maxResponseTime) * 100}
                  sx={{
                    height: 8,
                    borderRadius: 1,
                    bgcolor: 'action.hover',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: data.p95_ms < 500 ? 'success.main' : data.p95_ms < 1000 ? 'warning.main' : 'error.main',
                    },
                  }}
                />

                <Box sx={{ display: 'flex', gap: 2, mt: 0.5 }}>
                  <Typography variant="caption" color="text.secondary">
                    p50: {formatDuration(data.p50_ms)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    p99: {formatDuration(data.p99_ms)}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Stack>
        </Paper>
      </Grid>

      {/* Top Endpoints */}
      <Grid item xs={12} md={6}>
        <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <TrendingUpIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Top Endpoints
            </Typography>
          </Box>

          <Stack spacing={2}>
            {topEndpoints.map((endpoint) => (
              <Card
                key={`${endpoint.method}-${endpoint.endpoint}`}
                variant="outlined"
                sx={{
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 2,
                  },
                }}
              >
                <CardContent sx={{ py: 2, px: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography
                        variant="subtitle2"
                        fontWeight={600}
                        sx={{
                          fontFamily: 'monospace',
                          wordBreak: 'break-all',
                          color: 'primary.main',
                        }}
                      >
                        {endpoint.method} {endpoint.endpoint}
                      </Typography>
                    </Box>
                    <Chip
                      label={`${endpoint.request_count.toLocaleString()} requests`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                    <Chip
                      icon={<SuccessIcon fontSize="small" />}
                      label={`${endpoint.success_count}`}
                      size="small"
                      color="success"
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                    {endpoint.error_count > 0 && (
                      <Chip
                        icon={<ErrorIcon fontSize="small" />}
                        label={`${endpoint.error_count}`}
                        size="small"
                        color="error"
                        variant="outlined"
                        sx={{ height: 20, fontSize: '0.7rem' }}
                      />
                    )}
                    <Chip
                      label={`${endpoint.average_response_time_ms}ms avg`}
                      size="small"
                      color={endpoint.average_response_time_ms < 500 ? 'success' : 'warning'}
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  </Box>

                  <LinearProgress
                    variant="determinate"
                    value={(endpoint.request_count / maxEndpointCount) * 100}
                    sx={{
                      mt: 1.5,
                      height: 4,
                      borderRadius: 1,
                      bgcolor: 'action.hover',
                    }}
                  />
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Paper>
      </Grid>

      {/* Status Code Distribution */}
      <Grid item xs={12} md={6}>
        <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <WarningIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Status Codes
            </Typography>
          </Box>

          <Stack spacing={2}>
            {statusCodes.map((status) => (
              <Box key={status.status_code}>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 0.5,
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={status.status_code}
                      size="small"
                      color={getStatusCodeColor(status.status_code)}
                      sx={{ fontWeight: 600 }}
                    />
                    <Typography variant="body2" fontWeight={600}>
                      {status.count.toLocaleString()}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {status.percentage.toFixed(1)}%
                  </Typography>
                </Box>

                <LinearProgress
                  variant="determinate"
                  value={status.percentage}
                  sx={{
                    height: 8,
                    borderRadius: 1,
                    bgcolor: 'action.hover',
                    '& .MuiLinearProgress-bar': {
                      bgcolor:
                        status.status_code >= 200 && status.status_code < 300
                          ? 'success.main'
                          : status.status_code >= 400 && status.status_code < 500
                          ? 'warning.main'
                          : 'error.main',
                    },
                  }}
                />
              </Box>
            ))}
          </Stack>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default APIUsageChart;
