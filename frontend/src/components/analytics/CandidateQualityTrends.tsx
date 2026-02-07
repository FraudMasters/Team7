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
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Star as StarIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
} from '@mui/icons-material';

/**
 * Ranking range metrics from backend
 */
interface RankingRangeMetrics {
  range_label: string;
  range_min: number;
  range_max: number;
  candidate_count: number;
  hired_count: number;
  conversion_rate: number;
}

/**
 * Candidate quality trends response from backend
 */
interface CandidateQualityTrendsResponse {
  ranking_ranges: RankingRangeMetrics[];
  total_candidates: number;
  overall_hire_rate: number;
}

/**
 * CandidateQualityTrends Component Props
 */
interface CandidateQualityTrendsProps {
  /** API endpoint URL for candidate quality trends */
  apiUrl?: string;
  /** Optional date range filter */
  startDate?: string;
  /** Optional date range filter */
  endDate?: string;
}

/**
 * Get color based on ranking range
 */
const getRangeColor = (rangeLabel: string): string => {
  if (rangeLabel === '80-100%') return 'success.main';
  if (rangeLabel === '60-80%') return 'primary.main';
  if (rangeLabel === '40-60%') return 'info.main';
  if (rangeLabel === '20-40%') return 'warning.main';
  return 'error.main';
};

/**
 * Get color based on conversion rate
 */
const getConversionColor = (rate: number): string => {
  if (rate >= 0.3) return 'success.main';
  if (rate >= 0.2) return 'warning.main';
  return 'error.main';
};

/**
 * Get description for ranking range
 */
const getRangeDescription = (rangeLabel: string): string => {
  const descriptions: Record<string, string> = {
    '80-100%': 'Excellent Match',
    '60-80%': 'Good Match',
    '40-60%': 'Moderate Match',
    '20-40%': 'Low Match',
    '0-20%': 'Poor Match',
  };
  return descriptions[rangeLabel] || rangeLabel;
};

/**
 * CandidateQualityTrends Component
 *
 * Displays correlation between match rankings and hiring outcomes including:
 * - Candidate distribution across ranking ranges
 * - Conversion rates for each ranking range
 * - Overall hire rate
 * - Visual representation of ranking effectiveness
 *
 * @example
 * ```tsx
 * <CandidateQualityTrends />
 * ```
 *
 * @example
 * ```tsx
 * <CandidateQualityTrends startDate="2024-01-01" endDate="2024-12-31" />
 * ```
 */
const CandidateQualityTrends: React.FC<CandidateQualityTrendsProps> = ({
  apiUrl = '/api/analytics/candidate-quality-trends',
  startDate,
  endDate,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [qualityData, setQualityData] = useState<CandidateQualityTrendsResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  /**
   * Fetch candidate quality trends from backend
   */
  const fetchQualityData = async () => {
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

      const response = await axios.get<CandidateQualityTrendsResponse>(apiUrl, { params });
      setQualityData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load candidate quality trends';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Initial fetch on mount and when date range changes
   */
  useEffect(() => {
    fetchQualityData();
  }, [apiUrl, startDate, endDate]);

  /**
   * Auto-refresh every 60 seconds when enabled
   */
  useEffect(() => {
    if (!autoRefreshEnabled) {
      return;
    }

    const interval = setInterval(() => {
      fetchQualityData();
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
          Loading candidate quality trends...
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
          <Button color="inherit" onClick={fetchQualityData} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Candidate Quality Trends</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!qualityData) {
    return null;
  }

  // Find the best performing range
  const bestRange = qualityData.ranking_ranges.reduce((best, current) =>
    current.conversion_rate > best.conversion_rate ? current : best
  );

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h5" fontWeight={600}>
              Candidate Quality Trends
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Correlation between match rankings and hiring outcomes
            </Typography>
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
              onClick={fetchQualityData}
              size="small"
            >
              Refresh
            </Button>
          </Box>
        </Box>

        {/* Overall Metrics */}
        <Box
          sx={{
            display: 'flex',
            gap: 3,
            mb: 4,
            flexWrap: 'wrap',
          }}
        >
          <Box sx={{ flex: '1 1 200px' }}>
            <Typography variant="caption" color="text.secondary">
              Total Candidates Analyzed
            </Typography>
            <Typography variant="h4" fontWeight={700} color="primary.main">
              {qualityData.total_candidates.toLocaleString()}
            </Typography>
          </Box>
          <Box sx={{ flex: '1 1 200px' }}>
            <Typography variant="caption" color="text.secondary">
              Overall Hire Rate
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography
                variant="h4"
                fontWeight={700}
                color={qualityData.overall_hire_rate >= 0.15 ? 'success.main' : 'warning.main'}
              >
                {(qualityData.overall_hire_rate * 100).toFixed(2)}%
              </Typography>
              {qualityData.overall_hire_rate >= 0.15 ? (
                <CheckIcon color="success" fontSize="small" />
              ) : (
                <WarningIcon color="warning" fontSize="small" />
              )}
            </Box>
          </Box>
          <Box sx={{ flex: '1 1 200px' }}>
            <Typography variant="caption" color="text.secondary">
              Best Performing Range
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="h4" fontWeight={700} color={getRangeColor(bestRange.range_label)}>
                {bestRange.range_label}
              </Typography>
              <StarIcon sx={{ color: getRangeColor(bestRange.range_label) }} fontSize="small" />
            </Box>
          </Box>
        </Box>

        {/* Ranking Ranges */}
        <Stack spacing={2}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Ranking Range Performance
          </Typography>

          {qualityData.ranking_ranges.map((range) => {
            const candidatePercentage =
              qualityData.total_candidates > 0
                ? range.candidate_count / qualityData.total_candidates
                : 0;

            return (
              <Card
                key={range.range_label}
                variant="outlined"
                sx={{
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateX(4px)',
                    boxShadow: 2,
                  },
                  borderColor: range.range_label === bestRange.range_label ? 'success.main' : 'divider',
                }}
              >
                <CardContent sx={{ py: 2 }}>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      mb: 1.5,
                    }}
                  >
                    {/* Range Label and Description */}
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {range.range_label}
                        </Typography>
                        <Chip
                          label={getRangeDescription(range.range_label)}
                          size="small"
                          color={range.range_label === '80-100%' ? 'success' : 'default'}
                          variant="outlined"
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                        {range.range_label === bestRange.range_label && (
                          <StarIcon color="success" fontSize="small" />
                        )}
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {range.candidate_count.toLocaleString()} candidates ({(candidatePercentage * 100).toFixed(1)}% of
                        total)
                      </Typography>
                    </Box>

                    {/* Hire Count and Conversion Rate */}
                    <Box sx={{ textAlign: 'right', minWidth: 150 }}>
                      <Typography variant="body2" color="text.secondary">
                        {range.hired_count} hired
                      </Typography>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'flex-end',
                          gap: 0.5,
                        }}
                      >
                        <Typography
                          variant="h5"
                          fontWeight={700}
                          color={getConversionColor(range.conversion_rate)}
                        >
                          {(range.conversion_rate * 100).toFixed(1)}%
                        </Typography>
                        <Chip
                          label="conversion"
                          size="small"
                          color={range.conversion_rate >= 0.3 ? 'success' : 'default'}
                          variant="outlined"
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      </Box>
                    </Box>
                  </Box>

                  {/* Conversion Rate Bar */}
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Conversion Rate
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {(range.conversion_rate * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={range.conversion_rate * 100}
                      sx={{
                        height: 12,
                        borderRadius: 1,
                        bgcolor: 'action.hover',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: getConversionColor(range.conversion_rate),
                        },
                      }}
                    />
                  </Box>

                  {/* Candidate Distribution Bar */}
                  <Box sx={{ mt: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Candidate Distribution
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {(candidatePercentage * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={candidatePercentage * 100}
                      sx={{
                        height: 8,
                        borderRadius: 1,
                        bgcolor: 'action.hover',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: getRangeColor(range.range_label),
                        },
                      }}
                    />
                  </Box>
                </CardContent>
              </Card>
            );
          })}
        </Stack>

        {/* Insights */}
        {qualityData.ranking_ranges.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Quality Insights
            </Typography>
            <Stack spacing={1}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <TrendingUpIcon color="info" fontSize="small" sx={{ mt: 0.2 }} />
                <Typography variant="body2" color="text.secondary">
                  <strong>Best Range:</strong> {bestRange.range_label} with {(bestRange.conversion_rate * 100).toFixed(1)}%
                  conversion rate ({bestRange.hired_count} hires from {bestRange.candidate_count} candidates)
                </Typography>
              </Box>

              {/* Check if higher rankings correlate with better outcomes */}
              {qualityData.ranking_ranges.length >= 2 && (
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                  {qualityData.ranking_ranges[0].conversion_rate >
                  qualityData.ranking_ranges[qualityData.ranking_ranges.length - 1].conversion_rate ? (
                    <CheckIcon color="success" fontSize="small" sx={{ mt: 0.2 }} />
                  ) : (
                    <WarningIcon color="warning" fontSize="small" sx={{ mt: 0.2 }} />
                  )}
                  <Typography variant="body2" color="text.secondary">
                    <strong>Correlation:</strong>{' '}
                    {qualityData.ranking_ranges[0].conversion_rate >
                    qualityData.ranking_ranges[qualityData.ranking_ranges.length - 1].conversion_rate
                      ? 'Higher match scores correlate with better hiring outcomes. The ranking algorithm is effective.'
                      : 'Consider reviewing the matching algorithm - higher scores should ideally lead to better outcomes.'}
                  </Typography>
                </Box>
              )}

              {/* Screening recommendation */}
              {qualityData.ranking_ranges.length >= 3 && (
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                  <StarIcon color="primary" fontSize="small" sx={{ mt: 0.2 }} />
                  <Typography variant="body2" color="text.secondary">
                    <strong>Screening Recommendation:</strong> Focus on candidates with scores above{' '}
                    {qualityData.ranking_ranges[2].range_min * 100}% for optimal results (average conversion:{' '}
                    {(
                      (qualityData.ranking_ranges[0].conversion_rate +
                        qualityData.ranking_ranges[1].conversion_rate +
                        qualityData.ranking_ranges[2].conversion_rate) /
                      3 *
                      100
                    ).toFixed(1)}
                    %)
                  </Typography>
                </Box>
              )}
            </Stack>
          </Box>
        )}
      </Paper>
    </Stack>
  );
};

export default CandidateQualityTrends;
