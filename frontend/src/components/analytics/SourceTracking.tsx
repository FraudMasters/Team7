import React, { useState, useEffect } from 'react';
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
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  AccessTime as ClockIcon,
  Business as SourceIcon,
} from '@mui/icons-material';

/**
 * Source tracking item interface from backend
 */
interface SourceTrackingItem {
  source_name: string;
  vacancy_count: number;
  percentage: number;
  average_time_to_fill: number;
}

/**
 * Source tracking response from backend
 */
interface SourceTrackingResponse {
  sources: SourceTrackingItem[];
  total_vacancies: number;
}

/**
 * SourceTracking Component Props
 */
interface SourceTrackingProps {
  /** API endpoint URL for source tracking analytics */
  apiUrl?: string;
  /** Optional date range filter */
  startDate?: string;
  /** Optional date range filter */
  endDate?: string;
}

/**
 * Get color for source based on index
 */
const getSourceColor = (index: number): string => {
  const colors = [
    '#3b82f6', // blue
    '#10b981', // green
    '#f59e0b', // amber
    '#ef4444', // red
    '#8b5cf6', // purple
    '#ec4899', // pink
    '#06b6d4', // cyan
    '#84cc16', // lime
  ];
  return colors[index % colors.length];
};

/**
 * SourceTracking Component
 *
 * Displays source tracking analytics including:
 * - Vacancies by source (job board, referral, etc.) with pie chart
 * - Percentage distribution of sources
 * - Average time-to-fill by source
 * - Total vacancies analyzed
 *
 * @example
 * ```tsx
 * <SourceTracking />
 * ```
 *
 * @example
 * ```tsx
 * <SourceTracking startDate="2024-01-01" endDate="2024-12-31" />
 * ```
 */
const SourceTracking: React.FC<SourceTrackingProps> = ({
  apiUrl = 'http://localhost:8000/api/analytics/source-tracking',
  startDate,
  endDate,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sourceData, setSourceData] = useState<SourceTrackingResponse | null>(null);

  /**
   * Fetch source tracking data from backend
   */
  const fetchSourceTracking = async () => {
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
        throw new Error(`Failed to fetch source tracking: ${response.statusText}`);
      }

      const result: SourceTrackingResponse = await response.json();
      setSourceData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load source tracking data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSourceTracking();
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
          Loading source tracking analytics...
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
          <Button color="inherit" onClick={fetchSourceTracking} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Source Tracking</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!sourceData || sourceData.sources.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>No Source Tracking Data</AlertTitle>
        No source tracking data found. Start creating job vacancies with source information to populate this chart.
      </Alert>
    );
  }

  // Calculate pie chart segments
  let currentPercentage = 0;
  const pieSegments = sourceData.sources.map((source, index) => {
    const percentage = source.percentage * 100;
    const start = currentPercentage;
    currentPercentage += percentage;
    const end = currentPercentage;
    return { ...source, start, end, color: getSourceColor(index) };
  });

  // Create conic gradient for pie chart
  const conicGradient = pieSegments
    .map((segment) => `${segment.color} ${segment.start}% ${segment.end}%`)
    .join(', ');

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SourceIcon fontSize="large" color="primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Source Tracking Analytics
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Vacancy distribution by source channel
              </Typography>
            </Box>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchSourceTracking} size="small">
            Refresh
          </Button>
        </Box>

        {/* Summary Stats */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {sourceData.sources.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Active Sources
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {sourceData.sources[0]?.vacancy_count || 0}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Top Source Count
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" fontWeight={700}>
                  {(sourceData.sources[0]?.percentage * 100).toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Highest Share
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {sourceData.total_vacancies.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Total Vacancies
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Pie Chart and Details */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Grid container spacing={4}>
          {/* Pie Chart */}
          <Grid item xs={12} md={5} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              Vacancy Distribution
            </Typography>
            <Box
              sx={{
                position: 'relative',
                width: 280,
                height: 280,
                mt: 2,
              }}
            >
              {/* Pie Chart */}
              <Box
                sx={{
                  width: '100%',
                  height: '100%',
                  borderRadius: '50%',
                  background: `conic-gradient(${conicGradient})`,
                  position: 'relative',
                  boxShadow: 3,
                }}
              />
              {/* Donut Hole */}
              <Box
                sx={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: 140,
                  height: 140,
                  borderRadius: '50%',
                  bgcolor: 'background.paper',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: 2,
                }}
              >
                <Typography variant="h4" fontWeight={700} color="primary.main">
                  {sourceData.total_vacancies.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Total Vacancies
                </Typography>
              </Box>
            </Box>
          </Grid>

          {/* Source Details */}
          <Grid item xs={12} md={7}>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              Source Breakdown
            </Typography>
            <Stack spacing={2} sx={{ mt: 3 }}>
              {pieSegments.map((source, index) => (
                <Card
                  key={source.source_name}
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
                      {/* Source Name and Color Indicator */}
                      <Grid item xs={12} sm={4}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                          <Box
                            sx={{
                              width: 16,
                              height: 16,
                              borderRadius: '50%',
                              bgcolor: source.color,
                              boxShadow: 1,
                            }}
                          />
                          <Typography variant="subtitle1" fontWeight={600}>
                            {source.source_name}
                          </Typography>
                        </Box>
                      </Grid>

                      {/* Percentage Bar */}
                      <Grid item xs={12} sm={4}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ flexGrow: 1 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">
                                Share
                              </Typography>
                              <Typography variant="body2" fontWeight={600}>
                                {source.vacancy_count.toLocaleString()} ({(source.percentage * 100).toFixed(1)}%)
                              </Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={source.percentage * 100}
                              sx={{
                                height: 8,
                                borderRadius: 1,
                                bgcolor: 'action.hover',
                                '& .MuiLinearProgress-bar': {
                                  bgcolor: source.color,
                                },
                              }}
                            />
                          </Box>
                        </Box>
                      </Grid>

                      {/* Time to Fill */}
                      <Grid item xs={12} sm={4}>
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'flex-end',
                            gap: 0.5,
                          }}
                        >
                          <ClockIcon
                            fontSize="small"
                            sx={{
                              color:
                                source.average_time_to_fill <= 30
                                  ? 'success.main'
                                  : source.average_time_to_fill <= 45
                                    ? 'warning.main'
                                    : 'error.main',
                            }}
                          />
                          <Typography
                            variant="body2"
                            fontWeight={600}
                            color={
                              source.average_time_to_fill <= 30
                                ? 'success.main'
                                : source.average_time_to_fill <= 45
                                  ? 'warning.main'
                                  : 'error.main'
                            }
                          >
                            {source.average_time_to_fill.toFixed(0)}d
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            avg fill time
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              ))}
            </Stack>
          </Grid>
        </Grid>
      </Paper>
    </Stack>
  );
};

export default SourceTracking;
