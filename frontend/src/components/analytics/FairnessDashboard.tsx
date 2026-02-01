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
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Balance as FairnessIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Analytics as MetricsIcon,
} from '@mui/icons-material';
import { fairness } from '@/api/fairness';
import type {
  FairnessSummary,
  FairnessAlert,
  FairnessMetric,
} from '@/types/api';

/**
 * FairnessDashboard Component Props
 */
interface FairnessDashboardProps {
  /** Optional date range filter */
  startDate?: string;
  /** Optional date range filter */
  endDate?: string;
  /** Number of days to look back for alerts */
  alertDays?: number;
}

/**
 * Get severity color for display
 */
function getSeverityColor(severity: string): 'success' | 'warning' | 'error' | 'info' {
  switch (severity.toLowerCase()) {
    case 'none':
    case 'low':
      return 'success';
    case 'medium':
      return 'warning';
    case 'high':
      return 'error';
    case 'critical':
      return 'error';
    default:
      return 'info';
  }
}

/**
 * Get severity icon
 */
function getSeverityIcon(severity: string) {
  switch (severity.toLowerCase()) {
    case 'none':
    case 'low':
      return <CheckIcon />;
    case 'medium':
      return <WarningIcon />;
    case 'high':
    case 'critical':
      return <ErrorIcon />;
    default:
      return <MetricsIcon />;
  }
}

/**
 * FairnessDashboard Component
 *
 * Displays fairness monitoring metrics including:
 * - Overall fairness summary (models monitored, issues detected)
 * - Recent fairness alerts with severity levels
 * - Key fairness metrics across protected attributes
 *
 * @example
 * ```tsx
 * <FairnessDashboard />
 * ```
 *
 * @example
 * ```tsx
 * <FairnessDashboard alertDays={7} />
 * ```
 */
const FairnessDashboard: React.FC<FairnessDashboardProps> = ({
  startDate,
  endDate,
  alertDays = 30,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<FairnessSummary | null>(null);
  const [alerts, setAlerts] = useState<FairnessAlert[]>([]);
  const [metrics, setMetrics] = useState<FairnessMetric[]>([]);

  /**
   * Fetch fairness data from backend
   */
  const fetchFairnessData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch summary, alerts, and metrics in parallel
      const [summaryResponse, alertsResponse, metricsResponse] = await Promise.all([
        fairness.getSummary(),
        fairness.getAlerts({ days: alertDays, limit: 10, acknowledged: false }),
        fairness.getMetrics({ limit: 20, is_acceptable: false }),
      ]);

      setSummary(summaryResponse);
      setAlerts(alertsResponse.alerts);
      setMetrics(metricsResponse.metrics);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load fairness data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFairnessData();
  }, [alertDays, startDate, endDate]);

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
          Loading fairness metrics...
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
          <Button color="inherit" onClick={fetchFairnessData} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Fairness Data</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!summary) {
    return null;
  }

  const hasIssues = summary.models_with_issues > 0;
  const scoreColor = summary.overall_fairness_score >= 0.8 ? 'success.main' : summary.overall_fairness_score >= 0.6 ? 'warning.main' : 'error.main';

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Fairness Monitoring Dashboard
          </Typography>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchFairnessData} size="small">
            Refresh
          </Button>
        </Box>

        <Grid container spacing={2}>
          {/* Overall Fairness Score Card */}
          <Grid item xs={12} sm={6} md={4}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: scoreColor,
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <FairnessIcon
                    fontSize="large"
                    sx={{ mr: 1, color: scoreColor }}
                  />
                  <Typography variant="h6" fontWeight={600}>
                    Overall Fairness
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Fairness Score
                  </Typography>
                  <Typography
                    variant="h4"
                    fontWeight={700}
                    color={scoreColor}
                  >
                    {(summary.overall_fairness_score * 100).toFixed(1)}%
                  </Typography>
                </Box>

                <Stack spacing={1}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Models Monitored
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {summary.total_models}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Models with Issues
                    </Typography>
                    <Typography
                      variant="body2"
                      fontWeight={600}
                      color={hasIssues ? 'warning.main' : 'success.main'}
                    >
                      {summary.models_with_issues}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Recent Alerts
                    </Typography>
                    <Typography
                      variant="body2"
                      fontWeight={600}
                      color={summary.recent_alerts > 0 ? 'error.main' : 'text.primary'}
                    >
                      {summary.recent_alerts}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {/* Protected Attributes Card */}
          <Grid item xs={12} sm={6} md={4}>
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
                  <MetricsIcon fontSize="large" sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6" fontWeight={600}>
                    Protected Attributes
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Attributes Analyzed
                  </Typography>
                  <Typography variant="h4" fontWeight={700} color="primary.main">
                    {summary.protected_attributes_analyzed.length}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {summary.protected_attributes_analyzed.map((attribute) => (
                    <Chip
                      key={attribute}
                      label={attribute}
                      size="small"
                      variant="outlined"
                      color="primary"
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Recent Alerts Card */}
          <Grid item xs={12} sm={6} md={4}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: alerts.length > 0 ? 'error.main' : 'success.main',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {alerts.length > 0 ? (
                    <ErrorIcon
                      fontSize="large"
                      sx={{ mr: 1, color: 'error.main' }}
                    />
                  ) : (
                    <CheckIcon
                      fontSize="large"
                      sx={{ mr: 1, color: 'success.main' }}
                    />
                  )}
                  <Typography variant="h6" fontWeight={600}>
                    Active Alerts
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Unacknowledged
                  </Typography>
                  <Typography
                    variant="h4"
                    fontWeight={700}
                    color={alerts.length > 0 ? 'error.main' : 'success.main'}
                  >
                    {alerts.length}
                  </Typography>
                </Box>

                <Stack spacing={1}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Critical
                    </Typography>
                    <Typography variant="body2" fontWeight={600} color="error.main">
                      {alerts.filter((a) => a.severity === 'critical').length}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      High
                    </Typography>
                    <Typography variant="body2" fontWeight={600} color="error.main">
                      {alerts.filter((a) => a.severity === 'high').length}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="text.secondary">
                      Medium
                    </Typography>
                    <Typography variant="body2" fontWeight={600} color="warning.main">
                      {alerts.filter((a) => a.severity === 'medium').length}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Recent Alerts Section */}
      {alerts.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Recent Fairness Alerts
          </Typography>
          <Stack spacing={2}>
            {alerts.slice(0, 5).map((alert) => (
              <Card
                key={alert.alert_id}
                variant="outlined"
                sx={{
                  borderColor: `${getSeverityColor(alert.severity)}.main`,
                  borderLeft: 4,
                  borderLeftColor: `${getSeverityColor(alert.severity)}.main`,
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
                    <Box sx={{ mr: 1, mt: 0.5, color: `${getSeverityColor(alert.severity)}.main` }}>
                      {getSeverityIcon(alert.severity)}
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                        <Typography variant="subtitle2" fontWeight={600}>
                          {alert.alert_type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                        </Typography>
                        <Chip
                          label={alert.severity.toUpperCase()}
                          size="small"
                          color={getSeverityColor(alert.severity)}
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {alert.description}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          Model: <strong>{alert.model_name}</strong>
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Attribute: <strong>{alert.protected_attribute}</strong>
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Value: <strong>{alert.current_value.toFixed(3)}</strong> (threshold: {alert.threshold_value.toFixed(3)})
                        </Typography>
                      </Box>
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="info.main">
                          💡 {alert.recommendation}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Paper>
      )}

      {/* Metrics Below Threshold Section */}
      {metrics.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Metrics Requiring Attention
          </Typography>
          <Stack spacing={2}>
            {metrics.slice(0, 5).map((metric) => (
              <Card
                key={metric.metric_id}
                variant="outlined"
                sx={{
                  borderColor: 'warning.main',
                  borderLeft: 4,
                  borderLeftColor: 'warning.main',
                }}
              >
                <CardContent sx={{ py: 1.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="subtitle2" fontWeight={600}>
                        {metric.metric_type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {metric.model_name} • {metric.protected_attribute}
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="body2" fontWeight={600} color="warning.main">
                        {metric.metric_value.toFixed(3)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Threshold: {metric.threshold.toFixed(3)}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Paper>
      )}

      {/* No Issues Message */}
      {alerts.length === 0 && metrics.length === 0 && (
        <Paper elevation={2} sx={{ p: 4, textAlign: 'center' }}>
          <CheckIcon sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            All Systems Fair
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No fairness issues detected across all monitored models and protected attributes.
          </Typography>
        </Paper>
      )}
    </Stack>
  );
};

export default FairnessDashboard;
