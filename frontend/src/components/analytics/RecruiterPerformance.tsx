import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Stack,
  Button,
  Avatar,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Person as PersonIcon,
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckIcon,
  Star as StarIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';

/**
 * Individual recruiter performance metrics
 */
interface RecruiterPerformanceItem {
  recruiter_id: string;
  recruiter_name: string;
  hires: number;
  interviews_conducted: number;
  resumes_processed: number;
  average_time_to_hire: number;
  offer_acceptance_rate: number;
  candidate_satisfaction_score: number;
}

/**
 * Recruiter performance response from backend
 */
interface RecruiterPerformanceResponse {
  recruiters: RecruiterPerformanceItem[];
  total_recruiters: number;
  period_start_date: string;
  period_end_date: string;
}

/**
 * RecruiterPerformance Component Props
 */
interface RecruiterPerformanceProps {
  /** API endpoint URL for fetching recruiter performance data */
  apiUrl?: string;
  /** Optional start date for filtering (ISO 8601 format) */
  startDate?: string;
  /** Optional end date for filtering (ISO 8601 format) */
  endDate?: string;
  /** Maximum number of recruiters to display */
  limit?: number;
}

/**
 * RecruiterPerformance Component
 *
 * Displays recruiter performance comparison in table format with:
 * - Hires, interviews conducted, resumes processed
 * - Average time-to-hire with color coding
 * - Offer acceptance rate with visual indicator
 * - Candidate satisfaction score with star rating
 * - Rank ordering by number of hires
 * - Performance insights and metrics
 *
 * @example
 * ```tsx
 * <RecruiterPerformance />
 * ```
 *
 * @example
 * ```tsx
 * <RecruiterPerformance
 *   startDate="2024-01-01"
 *   endDate="2024-12-31"
 *   limit={10}
 * />
 * ```
 */
const RecruiterPerformance: React.FC<RecruiterPerformanceProps> = ({
  apiUrl = 'http://localhost:8000/api/analytics',
  startDate,
  endDate,
  limit = 20,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RecruiterPerformanceResponse | null>(null);

  /**
   * Fetch recruiter performance data from backend
   */
  const fetchPerformance = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      params.append('limit', limit.toString());

      const response = await fetch(`${apiUrl}/recruiter-performance?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch recruiter performance: ${response.statusText}`);
      }

      const result: RecruiterPerformanceResponse = await response.json();
      setData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load recruiter performance data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPerformance();
  }, [startDate, endDate, limit]);

  /**
   * Get time-to-hire color configuration based on days
   */
  const getTimeToHireConfig = (days: number) => {
    if (days <= 30) {
      return {
        color: 'success' as const,
        label: 'Fast',
        bgColor: 'success.main',
      };
    }
    if (days <= 45) {
      return {
        color: 'warning' as const,
        label: 'Moderate',
        bgColor: 'warning.main',
      };
    }
    return {
      color: 'error' as const,
      label: 'Slow',
      bgColor: 'error.main',
    };
  };

  /**
   * Get offer acceptance rate color configuration
   */
  const getAcceptanceRateConfig = (rate: number) => {
    const percentage = rate * 100;
    if (percentage >= 90) {
      return {
        color: 'success' as const,
        label: 'Excellent',
      };
    }
    if (percentage >= 80) {
      return {
        color: 'warning' as const,
        label: 'Good',
      };
    }
    return {
      color: 'error' as const,
      label: 'Low',
    };
  };

  /**
   * Get satisfaction score color configuration
   */
  const getSatisfactionConfig = (score: number) => {
    if (score >= 4.5) {
      return {
        color: 'success' as const,
      };
    }
    if (score >= 4.0) {
      return {
        color: 'warning' as const,
      };
    }
    return {
      color: 'error' as const,
    };
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
          Loading recruiter performance...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Analyzing performance metrics across all recruiters
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
          <Button color="inherit" onClick={fetchPerformance} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <Typography variant="subtitle1" fontWeight={600}>
          Failed to Load Recruiter Performance
        </Typography>
        <Typography variant="body2">{error}</Typography>
      </Alert>
    );
  }

  /**
   * Render no data state
   */
  if (!data || !data.recruiters || data.recruiters.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" fontWeight={600}>
          No Recruiter Performance Data
        </Typography>
        <Typography variant="body2">
          No recruiter performance data found for the selected time period.
        </Typography>
      </Alert>
    );
  }

  // Calculate summary statistics
  const topPerformer = data.recruiters[0];
  const avgTimeToHire =
    data.recruiters.reduce((sum, r) => sum + r.average_time_to_hire, 0) /
    data.recruiters.length;
  const avgAcceptanceRate =
    data.recruiters.reduce((sum, r) => sum + r.offer_acceptance_rate, 0) /
    data.recruiters.length;
  const avgSatisfaction =
    data.recruiters.reduce((sum, r) => sum + r.candidate_satisfaction_score, 0) /
    data.recruiters.length;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h5" fontWeight={600}>
              Recruiter Performance Comparison
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Comparing <strong>{data.recruiters.length}</strong> recruiters •{' '}
              <strong>{data.total_recruiters}</strong> total recruiters in organization
            </Typography>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchPerformance} size="small">
            Refresh
          </Button>
        </Box>

        {/* Summary Statistics */}
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              bgcolor: 'success.50',
              px: 2,
              py: 1,
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'success.main',
            }}
          >
            <PersonIcon sx={{ fontSize: 24, color: 'success.main' }} />
            <Box>
              <Typography variant="caption" color="text.secondary">
                Top Performer
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {topPerformer?.recruiter_name || 'N/A'}
              </Typography>
            </Box>
          </Box>

          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              bgcolor: 'info.50',
              px: 2,
              py: 1,
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'info.main',
            }}
          >
            <ScheduleIcon sx={{ fontSize: 24, color: 'info.main' }} />
            <Box>
              <Typography variant="caption" color="text.secondary">
                Avg Time-to-Hire
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {avgTimeToHire.toFixed(1)} days
              </Typography>
            </Box>
          </Box>

          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              bgcolor: 'warning.50',
              px: 2,
              py: 1,
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'warning.main',
            }}
          >
            <CheckIcon sx={{ fontSize: 24, color: 'warning.main' }} />
            <Box>
              <Typography variant="caption" color="text.secondary">
                Avg Acceptance Rate
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {(avgAcceptanceRate * 100).toFixed(1)}%
              </Typography>
            </Box>
          </Box>

          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              bgcolor: 'secondary.50',
              px: 2,
              py: 1,
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'secondary.main',
            }}
          >
            <StarIcon sx={{ fontSize: 24, color: 'secondary.main' }} />
            <Box>
              <Typography variant="caption" color="text.secondary">
                Avg Satisfaction
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {avgSatisfaction.toFixed(1)} / 5.0
              </Typography>
            </Box>
          </Box>
        </Box>
      </Paper>

      {/* Performance Table */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Performance Metrics
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Comparing recruiter performance across key metrics (sorted by number of hires)
        </Typography>

        <TableContainer sx={{ maxHeight: 700, overflow: 'auto' }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell
                  sx={{
                    fontWeight: 700,
                    bgcolor: 'grey.100',
                    minWidth: 80,
                    position: 'sticky',
                    left: 0,
                    zIndex: 3,
                  }}
                >
                  Rank
                </TableCell>
                <TableCell
                  sx={{
                    fontWeight: 700,
                    bgcolor: 'grey.100',
                    minWidth: 200,
                    position: 'sticky',
                    left: 80,
                    zIndex: 3,
                  }}
                >
                  Recruiter
                </TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }} align="center">
                  Hires
                </TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }} align="center">
                  Interviews
                </TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }} align="center">
                  Resumes
                </TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }} align="center">
                  Avg Time-to-Hire
                </TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }} align="center">
                  Acceptance Rate
                </TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }} align="center">
                  Satisfaction
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.recruiters.map((recruiter, index) => {
                const timeConfig = getTimeToHireConfig(recruiter.average_time_to_hire);
                const acceptanceConfig = getAcceptanceRateConfig(recruiter.offer_acceptance_rate);
                const satisfactionConfig = getSatisfactionConfig(recruiter.candidate_satisfaction_score);

                return (
                  <TableRow
                    key={recruiter.recruiter_id}
                    sx={{
                      '&:nth-of-type(odd)': { bgcolor: 'action.hover' },
                      '&:hover': { bgcolor: 'action.selected' },
                    }}
                  >
                    <TableCell
                      sx={{
                        fontWeight: 700,
                        position: 'sticky',
                        left: 0,
                        bgcolor: 'background.paper',
                        zIndex: 2,
                      }}
                    >
                      <Chip
                        label={`#${index + 1}`}
                        size="small"
                        color={index < 3 ? 'primary' : 'default'}
                        sx={{ fontWeight: 700 }}
                      />
                    </TableCell>
                    <TableCell
                      sx={{
                        fontWeight: 600,
                        position: 'sticky',
                        left: 80,
                        bgcolor: 'background.paper',
                        zIndex: 2,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Avatar
                          sx={{
                            width: 32,
                            height: 32,
                            bgcolor: `primary.${index % 2 === 0 ? 'main' : 'light'}`,
                            fontSize: '0.875rem',
                          }}
                        >
                          {recruiter.recruiter_name
                            .split(' ')
                            .map((n) => n[0])
                            .join('')
                            .toUpperCase()}
                        </Avatar>
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {recruiter.recruiter_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {recruiter.recruiter_id}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Box
                        sx={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                        }}
                      >
                        <Typography variant="body1" fontWeight={700} color="primary.main">
                          {recruiter.hires}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 0.5,
                        }}
                      >
                        <TrendingUpIcon fontSize="small" color="action" />
                        <Typography variant="body2">{recruiter.interviews_conducted}</Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 0.5,
                        }}
                      >
                        <DescriptionIcon fontSize="small" color="action" />
                        <Typography variant="body2">{recruiter.resumes_processed}</Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={`${recruiter.average_time_to_hire.toFixed(1)} days`}
                        size="small"
                        color={timeConfig.color}
                        sx={{ fontWeight: 600 }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={`${(recruiter.offer_acceptance_rate * 100).toFixed(0)}%`}
                        size="small"
                        color={acceptanceConfig.color}
                        sx={{ fontWeight: 600 }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 0.5,
                        }}
                      >
                        <StarIcon
                          fontSize="small"
                          sx={{ color: satisfactionConfig.color + '.main' }}
                        />
                        <Typography variant="body2" fontWeight={600}>
                          {recruiter.candidate_satisfaction_score.toFixed(1)}
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Period Information */}
      <Typography variant="caption" color="text.secondary" align="center" display="block">
        Analysis period: <strong>{new Date(data.period_start_date).toLocaleDateString()}</strong> to{' '}
        <strong>{new Date(data.period_end_date).toLocaleDateString()}</strong>
      </Typography>
    </Stack>
  );
};

export default RecruiterPerformance;
