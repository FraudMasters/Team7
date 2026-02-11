import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Chip,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  Collapse,
  Alert as MuiAlert,
  Badge,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  NotificationImportant as CriticalIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Refresh as RefreshIcon,
  CheckCircle as AcknowledgeIcon,
  Delete as DismissIcon,
  Notifications as AlertIcon,
  TrendingDown as DegradationIcon,
  Block as FailureIcon,
  ArrowBack as RollbackIcon,
  Science as CanaryIcon,
  Check as SuccessIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

interface ModelAlert {
  id: string;
  alert_type: string;
  model_name: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  details: Record<string, unknown> | null;
  alert_id: string;
  model_version_id: string | null;
  previous_version_id: string | null;
  status: 'pending' | 'sent' | 'failed' | 'acknowledged' | 'resolved';
  channels: string[] | null;
  sent_at: string | null;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  resolved_at: string | null;
  resolution_notes: string | null;
  created_at: string;
  updated_at: string;
}

interface AlertsSummary {
  total: number;
  pending: number;
  acknowledged: number;
  critical: number;
  error: number;
  warning: number;
  info: number;
}

interface ModelAlertsPanelProps {
  maxHeight?: number | string;
  showFilters?: boolean;
  modelFilter?: string;
}

const ModelAlertsPanel: React.FC<ModelAlertsPanelProps> = ({
  maxHeight = 600,
  showFilters = true,
  modelFilter,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<ModelAlert[]>([]);
  const [summary, setSummary] = useState<AlertsSummary | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedModel, setSelectedModel] = useState<string>(modelFilter || 'all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [expandedAlerts, setExpandedAlerts] = useState<Set<string>>(new Set());

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (selectedSeverity !== 'all') params.append('severity', selectedSeverity);
      if (selectedModel !== 'all') params.append('model_name', selectedModel);
      if (selectedStatus !== 'all') params.append('status', selectedStatus);
      params.append('limit', '50');

      const response = await axios.get(`/api/model-alerts?${params.toString()}`);
      setAlerts(response.data.alerts || []);
      setSummary(response.data.summary || null);
    } catch (err) {
      // If API is not available, show mock data for visualization
      setAlerts([
        {
          id: '1',
          alert_type: 'performance_degradation',
          model_name: 'skill_matching',
          severity: 'warning',
          title: 'Performance Degradation Detected',
          message: 'Model accuracy dropped by 5% in the last 24 hours. Current accuracy: 0.78, previous: 0.82.',
          details: { current_accuracy: 0.78, previous_accuracy: 0.82, drop_percentage: 5 },
          alert_id: 'skill_matching:performance_degradation:2024-01-15',
          model_version_id: 'v1.2.0',
          previous_version_id: 'v1.1.0',
          status: 'pending',
          channels: ['email', 'slack'],
          sent_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          acknowledged_at: null,
          acknowledged_by: null,
          resolved_at: null,
          resolution_notes: null,
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: '2',
          alert_type: 'training_failure',
          model_name: 'ranking',
          severity: 'error',
          title: 'Training Failed',
          message: 'Automated training failed: CUDA out of memory error. Manual intervention required.',
          details: { error: 'CUDA out of memory', retry_count: 3 },
          alert_id: 'ranking:training_failure:2024-01-15',
          model_version_id: null,
          previous_version_id: null,
          status: 'pending',
          channels: ['email'],
          sent_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
          acknowledged_at: null,
          acknowledged_by: null,
          resolved_at: null,
          resolution_notes: null,
          created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: '3',
          alert_type: 'feedback_threshold',
          model_name: 'skill_matching',
          severity: 'info',
          title: 'Feedback Threshold Reached',
          message: '1000 new feedback entries collected. Automatic retraining triggered.',
          details: { feedback_count: 1050, threshold: 1000 },
          alert_id: 'skill_matching:feedback_threshold:2024-01-14',
          model_version_id: 'v1.3.0',
          previous_version_id: 'v1.2.0',
          status: 'acknowledged',
          channels: ['email', 'slack'],
          sent_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          acknowledged_at: new Date(Date.now() - 23 * 60 * 60 * 1000).toISOString(),
          acknowledged_by: 'admin@example.com',
          resolved_at: null,
          resolution_notes: null,
          created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 23 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: '4',
          alert_type: 'canary_deployed',
          model_name: 'ranking',
          severity: 'info',
          title: 'Canary Deployment Started',
          message: 'New model version v2.0.0 deployed to 10% of traffic for A/B testing.',
          details: { canary_percentage: 10, canary_version: 'v2.0.0' },
          alert_id: 'ranking:canary_deployed:2024-01-13',
          model_version_id: 'v2.0.0',
          previous_version_id: 'v1.9.0',
          status: 'resolved',
          channels: ['slack'],
          sent_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
          acknowledged_at: new Date(Date.now() - 47 * 60 * 60 * 1000).toISOString(),
          acknowledged_by: 'devops@example.com',
          resolved_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          resolution_notes: 'Canary promoted to production after successful testing.',
          created_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        },
      ]);
      setSummary({
        total: 4,
        pending: 2,
        acknowledged: 1,
        critical: 0,
        error: 1,
        warning: 1,
        info: 2,
      });
    } finally {
      setLoading(false);
    }
  }, [selectedSeverity, selectedModel, selectedStatus]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAlerts();
    setRefreshing(false);
  };

  const handleAcknowledge = async (alertId: string) => {
    try {
      await axios.post(`/api/model-alerts/${alertId}/acknowledge`);
      await fetchAlerts();
    } catch (err) {
      // For demo, update locally
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId
            ? {
                ...alert,
                status: 'acknowledged' as const,
                acknowledged_at: new Date().toISOString(),
                acknowledged_by: 'current_user',
              }
            : alert
        )
      );
    }
  };

  const handleResolve = async (alertId: string) => {
    try {
      await axios.post(`/api/model-alerts/${alertId}/resolve`);
      await fetchAlerts();
    } catch (err) {
      // For demo, update locally
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId
            ? {
                ...alert,
                status: 'resolved' as const,
                resolved_at: new Date().toISOString(),
              }
            : alert
        )
      );
    }
  };

  const toggleAlertExpand = (alertId: string) => {
    setExpandedAlerts((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(alertId)) {
        newSet.delete(alertId);
      } else {
        newSet.add(alertId);
      }
      return newSet;
    });
  };

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <CriticalIcon sx={{ fontSize: 18, color: '#d32f2f' }} />;
      case 'error':
        return <ErrorIcon sx={{ fontSize: 18, color: '#d32f2f' }} />;
      case 'warning':
        return <WarningIcon sx={{ fontSize: 18, color: '#ed6c02' }} />;
      default:
        return <InfoIcon sx={{ fontSize: 18, color: '#0288d1' }} />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return '#d32f2f';
      case 'error':
        return '#d32f2f';
      case 'warning':
        return '#ed6c02';
      default:
        return '#0288d1';
    }
  };

  const getAlertTypeIcon = (alertType: string) => {
    switch (alertType) {
      case 'performance_degradation':
        return <DegradationIcon sx={{ fontSize: 16 }} />;
      case 'training_failure':
        return <FailureIcon sx={{ fontSize: 16 }} />;
      case 'rollback':
        return <RollbackIcon sx={{ fontSize: 16 }} />;
      case 'canary_deployed':
        return <CanaryIcon sx={{ fontSize: 16 }} />;
      case 'training_success':
        return <SuccessIcon sx={{ fontSize: 16 }} />;
      default:
        return <AlertIcon sx={{ fontSize: 16 }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'acknowledged':
        return 'info';
      case 'resolved':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  if (loading) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress size={32} />
        <Typography variant="body2" sx={{ mt: 2 }}>
          {t('alerts.loading') || 'Загрузка оповещений...'}
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Badge badgeContent={summary?.pending || 0} color="error" max={99}>
            <AlertIcon sx={{ fontSize: 20, color: 'primary.main' }} />
          </Badge>
          <Typography variant="h6" fontWeight={500}>
            Оповещения моделей
          </Typography>
        </Box>
        <Button
          size="small"
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={refreshing}
        >
          Обновить
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <MuiAlert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </MuiAlert>
      )}

      {/* Summary Cards */}
      {summary && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Grid container spacing={1.5}>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Всего
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {summary.total}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  <Typography variant="caption" color="warning.main">
                    Ожидают
                  </Typography>
                  <Typography variant="h6" fontWeight={600} color="warning.main">
                    {summary.pending}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  <Typography variant="caption" color="error.main">
                    Ошибки
                  </Typography>
                  <Typography variant="h6" fontWeight={600} color="error.main">
                    {summary.error + summary.critical}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  <Typography variant="caption" color="warning.main">
                    Предупрежд.
                  </Typography>
                  <Typography variant="h6" fontWeight={600} color="warning.main">
                    {summary.warning}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  <Typography variant="caption" color="info.main">
                    Информ.
                  </Typography>
                  <Typography variant="h6" fontWeight={600} color="info.main">
                    {summary.info}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  <Typography variant="caption" color="success.main">
                    Подтвержд.
                  </Typography>
                  <Typography variant="h6" fontWeight={600} color="success.main">
                    {summary.acknowledged}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Filters */}
      {showFilters && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={4}>
              <FormControl size="small" fullWidth>
                <InputLabel>Модель</InputLabel>
                <Select
                  value={selectedModel}
                  label="Модель"
                  onChange={(e) => setSelectedModel(e.target.value)}
                >
                  <MenuItem value="all">Все модели</MenuItem>
                  <MenuItem value="skill_matching">Skill Matching</MenuItem>
                  <MenuItem value="ranking">Ranking</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl size="small" fullWidth>
                <InputLabel>Важность</InputLabel>
                <Select
                  value={selectedSeverity}
                  label="Важность"
                  onChange={(e) => setSelectedSeverity(e.target.value)}
                >
                  <MenuItem value="all">Все</MenuItem>
                  <MenuItem value="critical">Критические</MenuItem>
                  <MenuItem value="error">Ошибки</MenuItem>
                  <MenuItem value="warning">Предупреждения</MenuItem>
                  <MenuItem value="info">Информационные</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl size="small" fullWidth>
                <InputLabel>Статус</InputLabel>
                <Select
                  value={selectedStatus}
                  label="Статус"
                  onChange={(e) => setSelectedStatus(e.target.value)}
                >
                  <MenuItem value="all">Все</MenuItem>
                  <MenuItem value="pending">Ожидают</MenuItem>
                  <MenuItem value="acknowledged">Подтвержденные</MenuItem>
                  <MenuItem value="resolved">Решенные</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Alerts List */}
      <Paper sx={{ p: 2, maxHeight, overflow: 'auto' }}>
        {alerts.length === 0 ? (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <AlertIcon sx={{ fontSize: 32, color: 'text.disabled', mb: 1 }} />
            <Typography variant="body2" color="text.secondary">
              Нет активных оповещений
            </Typography>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {alerts.map((alert) => (
              <Card
                key={alert.id}
                variant="outlined"
                sx={{
                  borderLeft: 4,
                  borderLeftColor: getSeverityColor(alert.severity),
                  opacity: alert.status === 'resolved' ? 0.7 : 1,
                }}
              >
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  {/* Alert Header */}
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, flex: 1 }}>
                      {getSeverityIcon(alert.severity)}
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                          <Typography variant="body2" fontWeight={500}>
                            {alert.title}
                          </Typography>
                          <Chip
                            icon={getAlertTypeIcon(alert.alert_type)}
                            label={alert.alert_type.replace(/_/g, ' ')}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.65rem', height: 20 }}
                          />
                          <Chip
                            label={alert.model_name}
                            size="small"
                            color="primary"
                            variant="outlined"
                            sx={{ fontSize: '0.65rem', height: 20 }}
                          />
                        </Box>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                          {formatTimeAgo(alert.created_at)}
                          {alert.model_version_id && ` · ${alert.model_version_id}`}
                        </Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Chip
                        label={alert.status}
                        size="small"
                        color={getStatusColor(alert.status)}
                        sx={{ fontSize: '0.65rem', height: 20 }}
                      />
                      <IconButton
                        size="small"
                        onClick={() => toggleAlertExpand(alert.id)}
                      >
                        {expandedAlerts.has(alert.id) ? (
                          <CollapseIcon fontSize="small" />
                        ) : (
                          <ExpandIcon fontSize="small" />
                        )}
                      </IconButton>
                    </Box>
                  </Box>

                  {/* Expanded Details */}
                  <Collapse in={expandedAlerts.has(alert.id)}>
                    <Box sx={{ mt: 1.5, pt: 1.5, borderTop: 1, borderColor: 'divider' }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                        {alert.message}
                      </Typography>

                      {alert.details && Object.keys(alert.details).length > 0 && (
                        <Box sx={{ mb: 1.5 }}>
                          <Typography variant="caption" color="text.secondary" fontWeight={500}>
                            Детали:
                          </Typography>
                          <Box component="pre" sx={{ fontSize: '0.7rem', m: 0, p: 1, bgcolor: 'action.hover', borderRadius: 1, overflow: 'auto' }}>
                            {JSON.stringify(alert.details, null, 2)}
                          </Box>
                        </Box>
                      )}

                      {alert.acknowledged_by && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                          Подтверждено: {alert.acknowledged_by} · {formatTimeAgo(alert.acknowledged_at!)}
                        </Typography>
                      )}

                      {alert.resolution_notes && (
                        <Typography variant="caption" color="success.main" sx={{ display: 'block', mb: 1 }}>
                          Примечание: {alert.resolution_notes}
                        </Typography>
                      )}

                      {alert.status !== 'resolved' && (
                        <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                          {alert.status === 'pending' && (
                            <Tooltip title="Подтвердить">
                              <Button
                                size="small"
                                variant="outlined"
                                startIcon={<AcknowledgeIcon />}
                                onClick={() => handleAcknowledge(alert.id)}
                              >
                                Подтвердить
                              </Button>
                            </Tooltip>
                          )}
                          <Tooltip title="Отметить как решенное">
                            <Button
                              size="small"
                              variant="contained"
                              color="success"
                              startIcon={<DismissIcon />}
                              onClick={() => handleResolve(alert.id)}
                            >
                              Решено
                            </Button>
                          </Tooltip>
                        </Box>
                      )}
                    </Box>
                  </Collapse>
                </CardContent>
              </Card>
            ))}
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default ModelAlertsPanel;
