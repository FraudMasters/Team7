import React, { useState, useEffect, useCallback } from 'react';
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
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  AttachMoney as SalaryIcon,
  FileDownload as FileDownloadIcon,
  BarChart as BarChartIcon,
} from '@mui/icons-material';

/**
 * Salary benchmark item interface from backend
 */
interface SalaryBenchmarkItem {
  role: string;
  location: string;
  salary_min: number;
  salary_median: number;
  salary_max: number;
  salary_p90?: number;
  currency: string;
  sample_size?: number;
  data_source?: string;
  effective_date?: string;
}

/**
 * Salary benchmark response from backend
 */
interface SalaryBenchmarkResponse {
  benchmarks: SalaryBenchmarkItem[];
  total_compared: number;
}

/**
 * SalaryBenchmarkChart Component Props
 */
interface SalaryBenchmarkChartProps {
  /** API endpoint URL for salary benchmarking */
  apiUrl?: string;
  /** Job role to benchmark */
  role?: string;
  /** Geographic location */
  location?: string;
  /** Experience level filter */
  experienceLevel?: string;
  /** Employment type filter */
  employmentType?: string;
  /** Industry filter */
  industry?: string;
  /** Maximum number of benchmarks to display */
  limit?: number;
}

/**
 * SalaryBenchmarkChart Component
 *
 * Displays salary benchmark data with:
 * - Role and location information
 * - Salary range (min, median, max, p90) as visual bars
 * - Sample size and data source
 * - Currency information
 * - Total benchmarks compared
 *
 * @example
 * ```tsx
 * <SalaryBenchmarkChart />
 * ```
 *
 * @example
 * ```tsx
 * <SalaryBenchmarkChart
 *   role="Senior React Developer"
 *   location="San Francisco, CA"
 *   experienceLevel="senior"
 *   limit={10}
 * />
 * ```
 */
const SalaryBenchmarkChart: React.FC<SalaryBenchmarkChartProps> = ({
  apiUrl = '/api/salary-benchmarking/benchmarks',
  role,
  location,
  experienceLevel,
  employmentType,
  industry,
  limit = 20,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [benchmarkData, setBenchmarkData] = useState<SalaryBenchmarkResponse | null>(null);

  /**
   * Fetch salary benchmark data from backend
   */
  const fetchSalaryBenchmarks = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: Record<string, string> = {};
      if (role) params.role = role;
      if (location) params.location = location;
      if (experienceLevel) params.experience_level = experienceLevel;
      if (employmentType) params.employment_type = employmentType;
      if (industry) params.industry = industry;
      if (limit) params.limit = limit.toString();

      const response = await axios.get<SalaryBenchmarkResponse>(apiUrl, { params });
      setBenchmarkData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load salary benchmark data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSalaryBenchmarks();
  }, [apiUrl, role, location, experienceLevel, employmentType, industry, limit]);

  /**
   * Format currency amount
   */
  const formatCurrency = useCallback((amount: number, currency: string = 'USD'): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  }, []);

  /**
   * Export salary benchmark data as CSV
   */
  const exportAsCSV = useCallback(() => {
    if (!benchmarkData || !benchmarkData.benchmarks || benchmarkData.benchmarks.length === 0) {
      return;
    }

    const headers = [
      'Rank',
      'Role',
      'Location',
      'Salary Min',
      'Salary Median',
      'Salary Max',
      'Salary P90',
      'Currency',
      'Sample Size',
      'Data Source',
    ];

    const rows = benchmarkData.benchmarks.map((benchmark, index) => [
      index + 1,
      `"${benchmark.role}"`,
      `"${benchmark.location}"`,
      benchmark.salary_min,
      benchmark.salary_median,
      benchmark.salary_max,
      benchmark.salary_p90 || 'N/A',
      benchmark.currency,
      benchmark.sample_size || 'N/A',
      `"${benchmark.data_source || 'N/A'}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `salary-benchmarks-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [benchmarkData]);

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
          Loading salary benchmark data...
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
          <Button color="inherit" onClick={fetchSalaryBenchmarks} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Salary Benchmarks</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!benchmarkData || benchmarkData.benchmarks.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>No Salary Benchmark Data</AlertTitle>
        No salary benchmark data found for the specified criteria. Try adjusting your filters or check back later.
      </Alert>
    );
  }

  // Get max salary for percentage calculations
  const maxSalary = Math.max(
    ...benchmarkData.benchmarks.map((b) => Math.max(b.salary_max, b.salary_p90 || b.salary_max))
  );

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SalaryIcon fontSize="large" color="primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Salary Benchmark Analytics
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Market salary data by role and location
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<FileDownloadIcon />}
              onClick={exportAsCSV}
              size="small"
              disabled={!benchmarkData || benchmarkData.benchmarks.length === 0}
            >
              Export CSV
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchSalaryBenchmarks}
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
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {benchmarkData.benchmarks.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Benchmarks
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {formatCurrency(
                    benchmarkData.benchmarks.reduce((sum, b) => sum + b.salary_median, 0) /
                      benchmarkData.benchmarks.length,
                    benchmarkData.benchmarks[0]?.currency || 'USD'
                  )}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Avg Median Salary
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" fontWeight={700}>
                  {formatCurrency(
                    Math.max(...benchmarkData.benchmarks.map((b) => b.salary_max)),
                    benchmarkData.benchmarks[0]?.currency || 'USD'
                  )}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Highest Max
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {benchmarkData.total_compared.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Data Points
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Benchmarks Chart */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Salary Ranges by Role and Location
        </Typography>

        <Stack spacing={2} sx={{ mt: 3 }}>
          {benchmarkData.benchmarks.map((benchmark, index) => (
            <Card
              key={`${benchmark.role}-${benchmark.location}-${index}`}
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
                  {/* Rank and Role/Location */}
                  <Grid item xs={12} sm={4}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={`#${index + 1}`}
                          size="small"
                          color={index < 3 ? 'primary' : 'default'}
                          sx={{
                            fontWeight: 700,
                            minWidth: 45,
                            bgcolor: index < 3 ? 'primary.main' : 'action.disabledBackground',
                          }}
                        />
                        <Typography variant="subtitle1" fontWeight={600}>
                          {benchmark.role}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 0.5 }}>
                        <Typography variant="body2" color="text.secondary">
                          {benchmark.location}
                        </Typography>
                        {benchmark.sample_size && (
                          <Chip
                            label={`n=${benchmark.sample_size}`}
                            size="small"
                            variant="outlined"
                            sx={{ height: 20, fontSize: '0.7rem' }}
                          />
                        )}
                      </Box>
                    </Box>
                  </Grid>

                  {/* Salary Range Bars */}
                  <Grid item xs={12} sm={5}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {/* Min to Median */}
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                          <Typography variant="caption" color="text.secondary">
                            Min - Median
                          </Typography>
                          <Typography variant="body2" fontWeight={600}>
                            {formatCurrency(benchmark.salary_min, benchmark.currency)} -{' '}
                            {formatCurrency(benchmark.salary_median, benchmark.currency)}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Box sx={{ flexGrow: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={(benchmark.salary_median / maxSalary) * 100}
                              sx={{
                                height: 8,
                                borderRadius: 1,
                                bgcolor: 'action.hover',
                                '& .MuiLinearProgress-bar': {
                                  bgcolor: 'info.main',
                                },
                              }}
                            />
                          </Box>
                        </Box>
                      </Box>

                      {/* Median to Max */}
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                          <Typography variant="caption" color="text.secondary">
                            Median - Max
                          </Typography>
                          <Typography variant="body2" fontWeight={600}>
                            {formatCurrency(benchmark.salary_max, benchmark.currency)}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Box sx={{ flexGrow: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={(benchmark.salary_max / maxSalary) * 100}
                              sx={{
                                height: 8,
                                borderRadius: 1,
                                bgcolor: 'action.hover',
                                '& .MuiLinearProgress-bar': {
                                  bgcolor: index < 3 ? 'primary.main' : 'primary.light',
                                },
                              }}
                            />
                          </Box>
                        </Box>
                      </Box>

                      {/* P90 (if available) */}
                      {benchmark.salary_p90 && (
                        <Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              Top 10% (P90)
                            </Typography>
                            <Typography variant="body2" fontWeight={600}>
                              {formatCurrency(benchmark.salary_p90, benchmark.currency)}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Box sx={{ flexGrow: 1 }}>
                              <LinearProgress
                                variant="determinate"
                                value={(benchmark.salary_p90 / maxSalary) * 100}
                                sx={{
                                  height: 8,
                                  borderRadius: 1,
                                  bgcolor: 'action.hover',
                                  '& .MuiLinearProgress-bar': {
                                    bgcolor: 'success.main',
                                  },
                                }}
                              />
                            </Box>
                          </Box>
                        </Box>
                      )}
                    </Box>
                  </Grid>

                  {/* Trend/Stats Indicator */}
                  <Grid item xs={12} sm={3}>
                    <Box
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'flex-end',
                        gap: 0.5,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <BarChartIcon fontSize="small" color="primary" />
                        <Typography variant="body2" fontWeight={600} color="primary.main">
                          {benchmark.currency}
                        </Typography>
                      </Box>
                      {benchmark.data_source && (
                        <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'right' }}>
                          {benchmark.data_source}
                        </Typography>
                      )}
                      {benchmark.effective_date && (
                        <Typography variant="caption" color="text.secondary">
                          {new Date(benchmark.effective_date).toLocaleDateString()}
                        </Typography>
                      )}
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          ))}
        </Stack>

        {benchmarkData.benchmarks.length >= limit && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Showing top {benchmarkData.benchmarks.length} benchmarks of{' '}
              {benchmarkData.total_compared.toLocaleString()} data points analyzed
            </Typography>
          </Box>
        )}
      </Paper>
    </Stack>
  );
};

export default SalaryBenchmarkChart;
