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
  Collapse,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  AccessTime as ClockIcon,
  Business as SourceIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  TrendingUp as TrendingIcon,
  Person as PersonIcon,
  CheckCircle as HiredIcon,
} from '@mui/icons-material';

/**
 * Stage distribution interface from backend
 */
interface StageDistribution {
  stage_name: string;
  count: number;
  percentage: number;
}

/**
 * Candidate source metrics interface from backend
 */
interface CandidateSourceMetrics {
  source: string;
  candidate_count: number;
  hired_count: number;
  conversion_rate: number;
  average_time_to_hire_days: number;
  stage_distribution: StageDistribution[];
}

/**
 * Candidate source attribution response from backend
 */
interface CandidateSourceAttributionResponse {
  sources: CandidateSourceMetrics[];
  total_candidates: number;
  date_range?: string;
}

/**
 * CandidateSourceAttribution Component Props
 */
interface CandidateSourceAttributionProps {
  /** API endpoint URL for candidate source attribution analytics */
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
 * Get color for stage based on percentage
 */
const getStageColor = (percentage: number): string => {
  if (percentage >= 0.4) return 'success.main';
  if (percentage >= 0.2) return 'primary.main';
  if (percentage >= 0.1) return 'warning.main';
  return 'text.secondary';
};

/**
 * CandidateSourceAttribution Component
 *
 * Displays candidate source attribution analytics including:
 * - Candidates by source (LinkedIn, referral, etc.)
 * - Conversion rates (hired/uploaded) per source
 * - Average time-to-hire by source
 * - Stage distribution for each source
 * - Total candidates analyzed
 *
 * @example
 * ```tsx
 * <CandidateSourceAttribution />
 * ```
 *
 * @example
 * ```tsx
 * <CandidateSourceAttribution startDate="2024-01-01" endDate="2024-12-31" />
 * ```
 */
const CandidateSourceAttribution: React.FC<CandidateSourceAttributionProps> = ({
  apiUrl = '/api/analytics/candidate-source-attribution',
  startDate,
  endDate,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sourceData, setSourceData] = useState<CandidateSourceAttributionResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());

  /**
   * Fetch candidate source attribution data from backend
   */
  const fetchSourceAttribution = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response = await axios.get<CandidateSourceAttributionResponse>(apiUrl, { params });
      setSourceData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load candidate source attribution data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSourceAttribution();
  }, [apiUrl, startDate, endDate]);

  /**
   * Auto-refresh every 60 seconds when enabled
   */
  useEffect(() => {
    if (!autoRefreshEnabled) {
      return;
    }

    const interval = setInterval(() => {
      fetchSourceAttribution();
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
   * Toggle source expansion for stage distribution
   */
  const toggleSourceExpansion = (source: string) => {
    setExpandedSources((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(source)) {
        newSet.delete(source);
      } else {
        newSet.add(source);
      }
      return newSet;
    });
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
          Loading candidate source attribution...
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
          <Button color="inherit" onClick={fetchSourceAttribution} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Candidate Source Attribution</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!sourceData || sourceData.sources.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>No Candidate Source Data</AlertTitle>
        No candidate source attribution data found. Start uploading resumes with source information to populate this analytics.
      </Alert>
    );
  }

  // Find best and worst performing sources
  const bestConversionSource = sourceData.sources.reduce((best, current) =>
    current.conversion_rate > best.conversion_rate ? current : best
  );
  const fastestSource = sourceData.sources.reduce((fastest, current) =>
    current.average_time_to_hire_days < fastest.average_time_to_hire_days ? current : fastest
  );

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SourceIcon fontSize="large" color="primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Candidate Source Attribution
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Candidate distribution and conversion metrics by source
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
              onClick={fetchSourceAttribution}
              size="small"
            >
              Refresh
            </Button>
          </Box>
        </Box>

        {/* Summary Stats */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <PersonIcon fontSize="large" color="primary" sx={{ mb: 1 }} />
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
                <PersonIcon fontSize="large" color="info.main" sx={{ mb: 1 }} />
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {sourceData.total_candidates.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Total Candidates
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <TrendingIcon fontSize="large" color="success.main" sx={{ mb: 1 }} />
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {(bestConversionSource.conversion_rate * 100).toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Best Conversion Rate
                </Typography>
                <Typography variant="caption" display="block" color="text.secondary">
                  ({bestConversionSource.source})
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <ClockIcon fontSize="large" color="warning.main" sx={{ mb: 1 }} />
                <Typography variant="h4" color="warning.main" fontWeight={700}>
                  {fastestSource.average_time_to_hire_days.toFixed(0)}d
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Fastest Hire
                </Typography>
                <Typography variant="caption" display="block" color="text.secondary">
                  ({fastestSource.source})
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Date Range Filter Display */}
        {sourceData.date_range && (
          <Box sx={{ mt: 2 }}>
            <Chip
              icon={<ClockIcon />}
              label={`Filtered: ${sourceData.date_range}`}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Box>
        )}
      </Paper>

      {/* Source Details */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Source Breakdown
        </Typography>
        <Stack spacing={2} sx={{ mt: 3 }}>
          {sourceData.sources.map((source, index) => (
            <Card
              key={source.source}
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
                {/* Source Header */}
                <Grid container spacing={2} alignItems="center">
                  {/* Source Name and Color Indicator */}
                  <Grid item xs={12} sm={3}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Box
                        sx={{
                          width: 16,
                          height: 16,
                          borderRadius: '50%',
                          bgcolor: getSourceColor(index),
                          boxShadow: 1,
                        }}
                      />
                      <Typography variant="subtitle1" fontWeight={600}>
                        {source.source}
                      </Typography>
                    </Box>
                  </Grid>

                  {/* Candidate Count and Hired Count */}
                  <Grid item xs={12} sm={3}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <PersonIcon fontSize="small" color="primary" />
                        <Typography variant="body2" fontWeight={600} color="primary.main">
                          {source.candidate_count}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <HiredIcon fontSize="small" color="success" />
                        <Typography variant="body2" fontWeight={600} color="success.main">
                          {source.hired_count}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>

                  {/* Conversion Rate */}
                  <Grid item xs={12} sm={3}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ flexGrow: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                          <Typography variant="caption" color="text.secondary">
                            Conversion
                          </Typography>
                          <Typography
                            variant="body2"
                            fontWeight={600}
                            color={
                              source.conversion_rate >= 0.15
                                ? 'success.main'
                                : source.conversion_rate >= 0.1
                                  ? 'warning.main'
                                  : 'error.main'
                            }
                          >
                            {(source.conversion_rate * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={source.conversion_rate * 100}
                          sx={{
                            height: 8,
                            borderRadius: 1,
                            bgcolor: 'action.hover',
                            '& .MuiLinearProgress-bar': {
                              bgcolor:
                                source.conversion_rate >= 0.15
                                  ? 'success.main'
                                  : source.conversion_rate >= 0.1
                                    ? 'warning.main'
                                    : 'error.main',
                            },
                          }}
                        />
                      </Box>
                    </Box>
                  </Grid>

                  {/* Time to Hire */}
                  <Grid item xs={12} sm={3}>
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
                            source.average_time_to_hire_days <= 30
                              ? 'success.main'
                              : source.average_time_to_hire_days <= 45
                                ? 'warning.main'
                                : 'error.main',
                        }}
                      />
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        color={
                          source.average_time_to_hire_days <= 30
                            ? 'success.main'
                            : source.average_time_to_hire_days <= 45
                              ? 'warning.main'
                              : 'error.main'
                        }
                      >
                        {source.average_time_to_hire_days.toFixed(0)}d
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        avg time-to-hire
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {/* Stage Distribution */}
                {source.stage_distribution && source.stage_distribution.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Button
                      size="small"
                      onClick={() => toggleSourceExpansion(source.source)}
                      sx={{ mb: 1 }}
                    >
                      {expandedSources.has(source.source) ? 'Hide' : 'Show'} Stage Distribution
                    </Button>
                    <Collapse in={expandedSources.has(source.source)}>
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                          Hiring Stage Breakdown
                        </Typography>
                        <Stack spacing={1}>
                          {source.stage_distribution.map((stage) => (
                            <Box key={stage.stage_name}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                                <Typography variant="caption" color="text.secondary">
                                  {stage.stage_name}
                                </Typography>
                                <Typography variant="caption" fontWeight={600}>
                                  {stage.count} ({(stage.percentage * 100).toFixed(1)}%)
                                </Typography>
                              </Box>
                              <LinearProgress
                                variant="determinate"
                                value={stage.percentage * 100}
                                sx={{
                                  height: 6,
                                  borderRadius: 1,
                                  bgcolor: 'action.hover',
                                  '& .MuiLinearProgress-bar': {
                                    bgcolor: getStageColor(stage.percentage),
                                  },
                                }}
                              />
                            </Box>
                          ))}
                        </Stack>
                      </Box>
                    </Collapse>
                  </Box>
                )}
              </CardContent>
            </Card>
          ))}
        </Stack>
      </Paper>
    </Stack>
  );
};

export default CandidateSourceAttribution;
