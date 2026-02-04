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
  Chip,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Balance as EquityIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  TrendUp as TrendUpIcon,
  TrendDown as TrendDownIcon,
  AttachMoney as SalaryIcon,
  People as CandidatesIcon,
  Insights as InsightsIcon,
} from '@mui/icons-material';
import { salaryBenchmarking } from '@/api/salaryBenchmarking';
import type {
  EquityAnalysisResponse,
  EquityDisparity,
} from '@/types/api';

/**
 * EquityAnalysisDashboard Component Props
 */
interface EquityAnalysisDashboardProps {
  /** Vacancy ID to analyze equity for */
  vacancyId: string;
  /** Whether to include demographic breakdowns */
  includeDemographics?: boolean;
  /** Pay gap threshold for alerts (0-1, e.g., 0.05 for 5%) */
  payGapThreshold?: number;
}

/**
 * Get disparity color based on pay gap
 */
function getDisparityColor(disparity: EquityDisparity): 'success' | 'warning' | 'error' {
  if (disparity.is_fair) {
    return 'success';
  }
  if (Math.abs(disparity.pay_gap) > 0.10) {
    return 'error';
  }
  return 'warning';
}

/**
 * Get disparity icon
 */
function getDisparityIcon(disparity: EquityDisparity) {
  if (disparity.is_fair) {
    return <CheckIcon />;
  }
  if (Math.abs(disparity.pay_gap) > 0.10) {
    return <ErrorIcon />;
  }
  return <WarningIcon />;
}

/**
 * Format pay gap as percentage
 */
function formatPayGap(payGap: number): string {
  const percentage = Math.abs(payGap * 100).toFixed(1);
  return payGap > 0 ? `+${percentage}%` : `-${percentage}%`;
}

/**
 * EquityAnalysisDashboard Component
 *
 * Displays internal pay equity analysis for a vacancy including:
 * - Overall salary statistics (mean, median, range)
 * - Total candidates analyzed
 * - Pay disparities across demographic groups
 * - Equity alerts and recommendations
 *
 * @example
 * ```tsx
 * <EquityAnalysisDashboard vacancyId="vacancy-123" />
 * ```
 *
 * @example
 * ```tsx
 * <EquityAnalysisDashboard
 *   vacancyId="vacancy-123"
 *   includeDemographics={true}
 *   payGapThreshold={0.05}
 * />
 * ```
 */
const EquityAnalysisDashboard: React.FC<EquityAnalysisDashboardProps> = ({
  vacancyId,
  includeDemographics = true,
  payGapThreshold = 0.05,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<EquityAnalysisResponse | null>(null);

  /**
   * Fetch equity analysis from backend
   */
  const fetchEquityAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await salaryBenchmarking.getEquityAnalysis({
        vacancy_id: vacancyId,
        include_demographics: includeDemographics,
        pay_gap_threshold: payGapThreshold,
      });

      setAnalysis(response);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load equity analysis';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEquityAnalysis();
  }, [vacancyId, includeDemographics, payGapThreshold]);

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
          Analyzing pay equity...
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
          <Button color="inherit" onClick={fetchEquityAnalysis} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Equity Analysis</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!analysis) {
    return null;
  }

  const hasDisparities = analysis.disparities.some((d) => !d.is_fair);
  const hasAlerts = analysis.alerts.length > 0;
  const equityScore = hasDisparities ? 'warning' : 'success';
  const equityColor = equityScore === 'success' ? 'success.main' : 'warning.main';

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Internal Equity Analysis
          </Typography>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchEquityAnalysis} size="small">
            Refresh
          </Button>
        </Box>

        <Grid container spacing={2}>
          {/* Role/Position Card */}
          <Grid item xs={12} sm={6} md={3}>
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
                  <InsightsIcon fontSize="large" sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6" fontWeight={600} noWrap>
                    Position
                  </Typography>
                </Box>

                <Box sx={{ mb: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Role
                  </Typography>
                  <Typography variant="body1" fontWeight={600}>
                    {analysis.role}
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Vacancy ID
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                    {analysis.vacancy_id.slice(0, 8)}...
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Candidates Analyzed Card */}
          <Grid item xs={12} sm={6} md={3}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: 'info.main',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CandidatesIcon fontSize="large" sx={{ mr: 1, color: 'info.main' }} />
                  <Typography variant="h6" fontWeight={600}>
                    Candidates
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Total Analyzed
                  </Typography>
                  <Typography variant="h4" fontWeight={700} color="info.main">
                    {analysis.total_candidates}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Mean Salary Card */}
          <Grid item xs={12} sm={6} md={3}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: 'success.main',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <SalaryIcon fontSize="large" sx={{ mr: 1, color: 'success.main' }} />
                  <Typography variant="h6" fontWeight={600}>
                    Mean Salary
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Average Compensation
                  </Typography>
                  <Typography variant="h4" fontWeight={700} color="success.main">
                    ${analysis.mean_salary.toLocaleString()}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Equity Status Card */}
          <Grid item xs={12} sm={6} md={3}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: equityColor,
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <EquityIcon
                    fontSize="large"
                    sx={{ mr: 1, color: equityColor }}
                  />
                  <Typography variant="h6" fontWeight={600}>
                    Equity Status
                  </Typography>
                </Box>

                <Box sx={{ mb: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Median Salary
                  </Typography>
                  <Typography variant="body1" fontWeight={600}>
                    ${analysis.median_salary.toLocaleString()}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="caption" color="text.secondary">
                    Range
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    ${analysis.salary_range.min.toLocaleString()} - ${analysis.salary_range.max.toLocaleString()}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Disparities Section */}
      {analysis.disparities.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Pay Equity Analysis by Group
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Comparison of mean salaries across different demographic groups. Pay gaps exceeding the threshold ({(payGapThreshold * 100).toFixed(0)}%) are flagged.
          </Typography>
          <Grid container spacing={2}>
            {analysis.disparities.map((disparity) => {
              const color = getDisparityColor(disparity);
              return (
                <Grid item xs={12} sm={6} md={4} key={disparity.group}>
                  <Card
                    variant="outlined"
                    sx={{
                      borderColor: `${color}.main`,
                      borderLeft: 4,
                      borderLeftColor: `${color}.main`,
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 3,
                      },
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Box sx={{ mr: 1, color: `${color}.main` }}>
                            {getDisparityIcon(disparity)}
                          </Box>
                          <Typography variant="subtitle2" fontWeight={600}>
                            {disparity.group}
                          </Typography>
                        </Box>
                        <Chip
                          label={disparity.is_fair ? 'EQUITABLE' : 'DISPARITY'}
                          size="small"
                          color={color}
                        />
                      </Box>

                      <Stack spacing={1}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" color="text.secondary">
                            Mean Salary
                          </Typography>
                          <Typography variant="body2" fontWeight={600}>
                            ${disparity.mean_salary.toLocaleString()}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" color="text.secondary">
                            Sample Size
                          </Typography>
                          <Typography variant="body2" fontWeight={600}>
                            {disparity.sample_size}
                          </Typography>
                        </Box>
                        <Divider sx={{ my: 0.5 }} />
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="caption" color="text.secondary">
                            Pay Gap
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            {disparity.pay_gap > 0 ? (
                              <TrendUpIcon fontSize="small" color="error" />
                            ) : disparity.pay_gap < 0 ? (
                              <TrendDownIcon fontSize="small" color="success" />
                            ) : null}
                            <Typography
                              variant="body2"
                              fontWeight={700}
                              color={disparity.pay_gap === 0 ? 'text.primary' : disparity.pay_gap > 0 ? 'error.main' : 'success.main'}
                            >
                              {formatPayGap(disparity.pay_gap)}
                            </Typography>
                          </Box>
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </Paper>
      )}

      {/* Alerts Section */}
      {hasAlerts && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ErrorIcon color="error" />
            Equity Alerts
          </Typography>
          <Stack spacing={2}>
            {analysis.alerts.map((alert, index) => (
              <Alert key={index} severity="warning" sx={{ py: 1 }}>
                <Typography variant="body2">{alert}</Typography>
              </Alert>
            ))}
          </Stack>
        </Paper>
      )}

      {/* Recommendations Section */}
      {analysis.recommendations.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CheckIcon color="info" />
            Recommendations
          </Typography>
          <Stack spacing={2}>
            {analysis.recommendations.map((recommendation, index) => (
              <Box
                key={index}
                sx={{
                  p: 2,
                  bgcolor: 'info.50',
                  borderRadius: 1,
                  borderLeft: 4,
                  borderLeftColor: 'info.main',
                }}
              >
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                  <Typography component="span" sx={{ color: 'info.main', fontWeight: 600 }}>
                    {index + 1}.
                  </Typography>
                  <Typography component="span">{recommendation}</Typography>
                </Typography>
              </Box>
            ))}
          </Stack>
        </Paper>
      )}

      {/* No Issues Message */}
      {!hasDisparities && !hasAlerts && (
        <Paper elevation={2} sx={{ p: 4, textAlign: 'center' }}>
          <CheckIcon sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Pay Equity Verified
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No significant pay disparities detected across all analyzed groups for this position.
            Compensation practices appear fair and equitable.
          </Typography>
        </Paper>
      )}
    </Stack>
  );
};

export default EquityAnalysisDashboard;
