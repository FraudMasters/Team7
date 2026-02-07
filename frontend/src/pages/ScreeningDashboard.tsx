import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Stack,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Visibility as VisibilityIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  ErrorOutline as ErrorOutlineIcon,
  Schedule as ScheduleIcon,
  AccessTime as AccessTimeIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import type { ScreeningMetricsResponse, ScreeningResultResponse } from '@/types/api';

/**
 * ScreeningDashboard Page
 *
 * Displays screening metrics and analytics including:
 * - Total candidates screened
 * - Auto-rejected count
 * - High priority count
 * - Review count
 * - Automation effectiveness (hours saved)
 * - Rejection reasons distribution
 * - Recent screening results
 */
const ScreeningDashboard: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<ScreeningMetricsResponse | null>(null);
  const [recentResults, setRecentResults] = useState<ScreeningResultResponse[]>([]);

  /**
   * Fetch screening metrics from backend
   */
  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get<ScreeningMetricsResponse>('/api/screening/metrics');
      setMetrics(response.data);

      // Fetch recent results
      const resultsResponse = await axios.get<{ results: ScreeningResultResponse[] }>('/api/screening/results', {
        params: { limit: 10 }
      });
      setRecentResults(resultsResponse.data.results);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load screening data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Initial fetch on mount
   */
  React.useEffect(() => {
    fetchMetrics();
  }, []);

  /**
   * Get tier chip color
   */
  const getTierColor = (tier: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (tier) {
      case 'HIGH_PRIORITY':
        return 'success';
      case 'REVIEW':
        return 'warning';
      case 'REJECT':
        return 'error';
      default:
        return 'default';
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
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
            Loading screening metrics...
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
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert
          severity="error"
          action={
            <Button color="inherit" onClick={fetchMetrics} startIcon={<RefreshIcon />}>
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      </Container>
    );
  }

  if (!metrics) {
    return null;
  }

  const { metrics: m } = metrics;

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" component="h1" fontWeight={700} gutterBottom>
            {t('screeningDashboard.title', 'Screening Dashboard')}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('screeningDashboard.subtitle', 'Monitor automated resume screening performance and metrics')}
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchMetrics}
        >
          Refresh
        </Button>
      </Box>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Total Screened */}
        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              borderLeft: 4,
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
                <VisibilityIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" fontWeight={600} color="text.secondary">
                  {t('screeningDashboard.metrics.totalScreened', 'Total Screened')}
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight={700} color="primary.main">
                {m.total_screened.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Candidates processed
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* High Priority */}
        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              borderLeft: 4,
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
                <CheckCircleIcon sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6" fontWeight={600} color="text.secondary">
                  {t('screeningDashboard.metrics.highPriority', 'High Priority')}
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight={700} color="success.main">
                {m.high_priority_count.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {m.total_screened > 0
                  ? `${((m.high_priority_count / m.total_screened) * 100).toFixed(1)}% of screened`
                  : '0% of screened'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Review Required */}
        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              borderLeft: 4,
              borderColor: 'warning.main',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 4,
              },
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ScheduleIcon sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6" fontWeight={600} color="text.secondary">
                  {t('screeningDashboard.metrics.reviewRequired', 'Review Required')}
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight={700} color="warning.main">
                {m.review_count.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {m.total_screened > 0
                  ? `${((m.review_count / m.total_screened) * 100).toFixed(1)}% of screened`
                  : '0% of screened'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Auto Rejected */}
        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              borderLeft: 4,
              borderColor: 'error.main',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 4,
              },
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ErrorOutlineIcon sx={{ mr: 1, color: 'error.main' }} />
                <Typography variant="h6" fontWeight={600} color="text.secondary">
                  {t('screeningDashboard.metrics.autoRejected', 'Auto Rejected')}
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight={700} color="error.main">
                {m.auto_rejected_count.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {m.total_screened > 0
                  ? `${((m.auto_rejected_count / m.total_screened) * 100).toFixed(1)}% of screened`
                  : '0% of screened'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Automation Effectiveness and Rejection Reasons */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Automation Effectiveness */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TrendingUpIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" fontWeight={600}>
                {t('screeningDashboard.automationEffectiveness.title', 'Automation Effectiveness')}
              </Typography>
            </Box>

            <Stack spacing={2}>
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {t('screeningDashboard.automationEffectiveness.hoursSaved', 'Time Saved')}
                </Typography>
                <Typography variant="h4" fontWeight={700} color="success.main">
                  {m.automation_effectiveness.manual_time_saved_hours.toFixed(1)}h
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  vs manual screening
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {t('screeningDashboard.automationEffectiveness.efficiency', 'Efficiency Gain')}
                </Typography>
                <Typography variant="h4" fontWeight={700} color="primary.main">
                  {m.automation_effectiveness.efficiency_percentage.toFixed(0)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  reduction in screening time
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {t('screeningDashboard.automationEffectiveness.avgTime', 'Avg. Screening Time')}
                </Typography>
                <Typography variant="h4" fontWeight={700} color="info.main">
                  {m.average_screening_time_seconds.toFixed(1)}s
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  per candidate
                </Typography>
              </Box>
            </Stack>
          </Paper>
        </Grid>

        {/* Rejection Reasons Distribution */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <ErrorOutlineIcon sx={{ mr: 1, color: 'error.main' }} />
              <Typography variant="h6" fontWeight={600}>
                {t('screeningDashboard.rejectionReasons.title', 'Rejection Reasons')}
              </Typography>
            </Box>

            {Object.keys(m.rejection_reasons).length > 0 ? (
              <Stack spacing={1.5}>
                {Object.entries(m.rejection_reasons)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 5)
                  .map(([reason, count]) => (
                    <Box key={reason}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="body2" fontWeight={500}>
                          {reason}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {count} ({m.auto_rejected_count > 0
                            ? ((count / m.auto_rejected_count) * 100).toFixed(0)
                            : 0}%)
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          width: '100%',
                          height: 8,
                          backgroundColor: 'action.hover',
                          borderRadius: 1,
                          overflow: 'hidden',
                        }}
                      >
                        <Box
                          sx={{
                            width: `${m.auto_rejected_count > 0
                              ? (count / m.auto_rejected_count) * 100
                              : 0}%`,
                            height: '100%',
                            backgroundColor: 'error.main',
                            transition: 'width 0.3s ease',
                          }}
                        />
                      </Box>
                    </Box>
                  ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                No rejection data available yet
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          {t('screeningDashboard.quickActions.title', 'Quick Actions')}
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            startIcon={<SettingsIcon />}
            onClick={() => navigate('/recruiter/vacancies')}
            color="primary"
          >
            {t('screeningDashboard.quickActions.configureRules', 'Configure Screening Rules')}
          </Button>
          <Button
            variant="outlined"
            startIcon={<VisibilityIcon />}
            onClick={() => navigate('/recruiter/candidates')}
            color="primary"
          >
            {t('screeningDashboard.quickActions.viewResults', 'View All Candidates')}
          </Button>
        </Stack>
      </Paper>

      {/* Recent Screening Results */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            {t('screeningDashboard.recentResults.title', 'Recent Screening Results')}
          </Typography>
          <Button
            size="small"
            onClick={() => navigate('/recruiter/candidates')}
            color="primary"
          >
            View All
          </Button>
        </Box>

        {recentResults.length > 0 ? (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t('screeningDashboard.recentResults.candidate', 'Candidate')}</TableCell>
                  <TableCell>{t('screeningDashboard.recentResults.vacancy', 'Vacancy')}</TableCell>
                  <TableCell>{t('screeningDashboard.recentResults.score', 'Score')}</TableCell>
                  <TableCell>{t('screeningDashboard.recentResults.tier', 'Tier')}</TableCell>
                  <TableCell>{t('screeningDashboard.recentResults.date', 'Date')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recentResults.map((result) => (
                  <TableRow key={result.id} hover>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight={500}>
                          {result.candidate_name || 'Unknown'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {result.filename || result.resume_id}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {result.vacancy_title || result.vacancy_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>
                        {result.score_applied.toFixed(1)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={result.tier.replace('_', ' ')}
                        size="small"
                        color={getTierColor(result.tier)}
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <AccessTimeIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                        <Typography variant="body2" color="text.secondary">
                          {new Date(result.screening_timestamp).toLocaleDateString()}
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {t('screeningDashboard.recentResults.noResults', 'No screening results yet')}
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Info Box */}
      <Box sx={{ mt: 4 }}>
        <Alert severity="info">
          <Typography variant="body2">
            <strong>{t('screeningDashboard.tip', 'Tip')}</strong>: {t('screeningDashboard.tipText',
              'Configure screening rules for each vacancy to automate candidate triage. ' +
              'High-priority candidates are flagged immediately for review, while unqualified candidates are auto-rejected.'
            )}
          </Typography>
        </Alert>
      </Box>
    </Container>
  );
};

export default ScreeningDashboard;
