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
  Chip,
  LinearProgress,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';

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
  const colors: string[] = [
    '#3b82f6', // blue
    '#10b981', // green
    '#f59e0b', // amber
    '#ef4444', // red
    '#8b5cf6', // purple
    '#ec4899', // pink
    '#06b6d4', // cyan
    '#84cc16', // lime
  ];
  return colors[Math.abs(index) % colors.length]!;
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
  apiUrl = '/api/analytics/source-tracking',
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

      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response = await axios.get<SourceTrackingResponse>(apiUrl, { params });
      setSourceData(response.data);
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
          Loading source tracking analytics...
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
          <Button color="inherit" onClick={fetchSourceTracking} startIcon={<Icon name="refresh" />}>
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
      <Paper elevation={2} css={{ padding: '24px' }}>
        <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <Box css={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Icon name="business" size={32} color="$primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Source Tracking Analytics
              </Typography>
              <Typography variant="body2" color="secondary">
                Vacancy distribution by source channel
              </Typography>
            </Box>
          </Box>
          <Button variant="outlined" startIcon={<Icon name="refresh" />} onClick={fetchSourceTracking} size="small">
            Refresh
          </Button>
        </Box>

        {/* Summary Stats */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent css={{ textAlign: 'center', padding: '8px' }}>
                <Typography variant="h4" color="$primary" fontWeight={700}>
                  {sourceData.sources.length}
                </Typography>
                <Typography variant="caption" color="secondary">
                  Active Sources
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent css={{ textAlign: 'center', padding: '8px' }}>
                <Typography variant="h4" color="$success" fontWeight={700}>
                  {sourceData.sources[0]?.vacancy_count || 0}
                </Typography>
                <Typography variant="caption" color="secondary">
                  Top Source Count
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent css={{ textAlign: 'center', padding: '8px' }}>
                <Typography variant="h4" fontWeight={700}>
                  {((sourceData.sources[0]?.percentage || 0) * 100).toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="secondary">
                  Highest Share
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent css={{ textAlign: 'center', padding: '8px' }}>
                <Typography variant="h4" color="$info" fontWeight={700}>
                  {sourceData.total_vacancies.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="secondary">
                  Total Vacancies
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Pie Chart and Details */}
      <Paper elevation={1} css={{ padding: '24px' }}>
        <Grid container spacing={4}>
          {/* Pie Chart */}
          <Grid item xs={12} md={5} css={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              Vacancy Distribution
            </Typography>
            <Box
              css={{
                position: 'relative',
                width: '280px',
                height: '280px',
                marginTop: '16px',
              }}
            >
              {/* Pie Chart */}
              <Box
                css={{
                  width: '100%',
                  height: '100%',
                  borderRadius: '50%',
                  background: `conic-gradient(${conicGradient})`,
                  position: 'relative',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                }}
              />
              {/* Donut Hole */}
              <Box
                css={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: '140px',
                  height: '140px',
                  borderRadius: '50%',
                  backgroundColor: '$background',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
                }}
              >
                <Typography variant="h4" fontWeight={700} color="$primary">
                  {sourceData.total_vacancies.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="secondary">
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
            <Stack spacing={2} css={{ marginTop: '24px' }}>
              {pieSegments.map((source, index) => (
                <Card
                  key={source.source_name}
                  variant="outlined"
                  css={{
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateX(4px)',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                    },
                  }}
                >
                  <CardContent css={{ padding: '16px' }}>
                    <Grid container spacing={2} alignItems="center">
                      {/* Source Name and Color Indicator */}
                      <Grid item xs={12} sm={4}>
                        <Box css={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <Box
                            css={{
                              width: '16px',
                              height: '16px',
                              borderRadius: '50%',
                              backgroundColor: source.color,
                              boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                            }}
                          />
                          <Typography variant="subtitle1" fontWeight={600}>
                            {source.source_name}
                          </Typography>
                        </Box>
                      </Grid>

                      {/* Percentage Bar */}
                      <Grid item xs={12} sm={4}>
                        <Box css={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Box css={{ flexGrow: 1 }}>
                            <Box css={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <Typography variant="caption" color="secondary">
                                Share
                              </Typography>
                              <Typography variant="body2" fontWeight={600}>
                                {source.vacancy_count.toLocaleString()} ({(source.percentage * 100).toFixed(1)}%)
                              </Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={source.percentage * 100}
                              css={{
                                height: '8px',
                                borderRadius: '4px',
                                backgroundColor: '$hover',
                                '& .MuiLinearProgress-bar': {
                                                  backgroundColor: source.color,
                                                },
                              }}
                            />
                          </Box>
                        </Box>
                      </Grid>

                      {/* Time to Fill */}
                      <Grid item xs={12} sm={4}>
                        <Box
                          css={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'flex-end',
                            gap: '4px',
                          }}
                        >
                          <Icon
                            name="clock"
                            size={16}
                            color={
                              source.average_time_to_fill <= 30
                                ? '$success'
                                : source.average_time_to_fill <= 45
                                  ? '$warning'
                                  : '$error'
                            }
                          />
                          <Typography
                            variant="body2"
                            fontWeight={600}
                            color={
                              source.average_time_to_fill <= 30
                                ? '$success'
                                : source.average_time_to_fill <= 45
                                  ? '$warning'
                                  : '$error'
                            }
                          >
                            {source.average_time_to_fill.toFixed(0)}d
                          </Typography>
                          <Typography variant="caption" color="secondary">
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
