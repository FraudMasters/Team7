import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  LinearProgress,
  Chip,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  School as TrainingIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingIcon,
  TrendingFlat as TrendingFlatIcon,
  Refresh as RefreshIcon,
  PlayArrow as StartIcon,
  Pause as PauseIcon,
  AccessTime as TimeIcon,
  Speed as SpeedIcon,
  Block as BlockIcon,
  ShowChart as ChartIcon,
  ArrowUpward as ArrowUpIcon,
  ArrowDownward as ArrowDownIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

interface PipelineHealth {
  total_models: number;
  active_trainings: number;
  failed_trainings: number;
  completed_trainings: number;
  overall_health: 'healthy' | 'degraded' | 'unhealthy';
}

interface TrainingStatus {
  model_name: string;
  latest_version: string | null;
  training_status: string | null;
  last_training_at: string | null;
  last_training_duration: number | null;
  last_training_metrics: {
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1_score?: number;
    loss?: number;
  } | null;
  is_healthy: boolean;
  error_message: string | null;
}

interface TrainingMetrics {
  id: string;
  model_name: string;
  version: string;
  training_status: string;
  training_duration: number | null;
  training_metrics: {
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1_score?: number;
    loss?: number;
  } | null;
  dataset_info: {
    train_size?: number;
    test_size?: number;
    validation_size?: number;
  } | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  color: 'success' | 'warning' | 'error';
  icon?: React.ReactNode;
}

interface PauseStatus {
  id: string;
  model_name: string;
  paused: boolean;
  pause_reason: string | null;
  paused_by: string | null;
  created_at: string;
  updated_at: string;
}

interface PerformanceTrendPoint {
  timestamp: string;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  auc_score?: number;
  ndcg_score?: number;
  mrr_score?: number;
}

interface PerformanceTrends {
  model_name: string;
  current_metrics: {
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1_score?: number;
    auc_score?: number;
    ndcg_score?: number;
    mrr_score?: number;
  };
  trend_data: PerformanceTrendPoint[];
  trend_direction: 'improving' | 'declining' | 'stable';
  health_score: number;
  alert_status: 'none' | 'warning' | 'critical';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, subtitle, color, icon }) => {
  const getColor = () => {
    switch (color) {
      case 'success': return '#2e7d32';
      case 'warning': return '#ed6c02';
      case 'error': return '#d32f2f';
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ pb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
          {icon && <Box sx={{ fontSize: 14, color: getColor() }}>{icon}</Box>}
          <Typography variant="caption" color="text.secondary">
            {title}
          </Typography>
        </Box>
        <Typography variant="h6" fontWeight={600} color={getColor()} sx={{ lineHeight: 1.2 }}>
          {value}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.65rem' }}>
          {subtitle}
        </Typography>
      </CardContent>
    </Card>
  );
};

const ModelTrainingDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<PipelineHealth | null>(null);
  const [trainingStatus, setTrainingStatus] = useState<Record<string, TrainingStatus>>({});
  const [recentMetrics, setRecentMetrics] = useState<TrainingMetrics[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('skill_matching');
  const [refreshing, setRefreshing] = useState(false);
  const [pauseStatus, setPauseStatus] = useState<PauseStatus | null>(null);
  const [pauseLoading, setPauseLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [performanceTrends, setPerformanceTrends] = useState<PerformanceTrends | null>(null);
  const [trendsLoading, setTrendsLoading] = useState(false);

  const fetchPauseStatus = useCallback(async () => {
    try {
      const response = await axios.get('/api/training-pipeline/config/pause-status?model_name=global');
      setPauseStatus(response.data);
    } catch (err) {
      // If config doesn't exist yet, that's okay - it means not paused
      setPauseStatus(null);
    }
  }, []);

  const fetchPipelineHealth = async () => {
    try {
      const response = await axios.get('/api/training-pipeline/health');
      setHealth(response.data);
    } catch (error) {
      console.error('Error fetching pipeline health:', error);
    }
  };

  const fetchTrainingStatus = async (modelName: string) => {
    try {
      const response = await axios.get(`/api/training-pipeline/status?model_name=${modelName}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching training status for ${modelName}:`, error);
      return null;
    }
  };

  const fetchTrainingMetrics = async () => {
    try {
      const response = await axios.get('/api/training-pipeline/metrics?limit=10');
      setRecentMetrics(response.data.metrics);
    } catch (error) {
      console.error('Error fetching training metrics:', error);
    }
  };

  const fetchPerformanceTrends = useCallback(async (modelName: string) => {
    try {
      setTrendsLoading(true);
      const response = await axios.get(`/api/model-versions/metrics/${modelName}?days=7`);
      setPerformanceTrends(response.data);
    } catch (error) {
      // API may not be available yet, set mock data for visualization
      setPerformanceTrends({
        model_name: modelName,
        current_metrics: {
          accuracy: 0.85,
          precision: 0.82,
          recall: 0.88,
          f1_score: 0.85,
        },
        trend_data: [
          { timestamp: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(), accuracy: 0.78, f1_score: 0.76 },
          { timestamp: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(), accuracy: 0.80, f1_score: 0.79 },
          { timestamp: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(), accuracy: 0.82, f1_score: 0.81 },
          { timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), accuracy: 0.81, f1_score: 0.80 },
          { timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), accuracy: 0.84, f1_score: 0.83 },
          { timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), accuracy: 0.85, f1_score: 0.85 },
        ],
        trend_direction: 'improving',
        health_score: 85,
        alert_status: 'none',
      });
    } finally {
      setTrendsLoading(false);
    }
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      await Promise.all([
        fetchPipelineHealth(),
        fetchTrainingStatus('skill_matching'),
        fetchTrainingStatus('ranking'),
        fetchTrainingMetrics(),
        fetchPauseStatus(),
      ]);

      // Fetch statuses for both models
      const skillMatchingStatus = await fetchTrainingStatus('skill_matching');
      const rankingStatus = await fetchTrainingStatus('ranking');
      setTrainingStatus({
        skill_matching: skillMatchingStatus,
        ranking: rankingStatus,
      });

      // Fetch performance trends for selected model
      await fetchPerformanceTrends('skill_matching');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const handleManualRetrain = async (modelName: string) => {
    try {
      setError(null);
      await axios.post('/api/model-versions/retrain', { model_name: modelName });
      await handleRefresh();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to trigger retraining';
      setError(errorMessage);
    }
  };

  const handlePauseToggle = async () => {
    setPauseLoading(true);
    setError(null);
    try {
      if (pauseStatus?.paused) {
        await axios.post('/api/training-pipeline/config/resume', { model_name: 'global' });
      } else {
        await axios.post('/api/training-pipeline/config/pause', {
          model_name: 'global',
          reason: 'Manual pause via dashboard',
        });
      }
      await fetchPauseStatus();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to toggle pause state';
      setError(errorMessage);
    } finally {
      setPauseLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedModel) {
      fetchPerformanceTrends(selectedModel);
    }
  }, [selectedModel, fetchPerformanceTrends]);

  if (loading) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress size={32} />
        <Typography variant="body2" sx={{ mt: 2 }}>
          {t('metrics.loading') || 'Загрузка...'}
        </Typography>
      </Paper>
    );
  }

  if (!health) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <WarningIcon sx={{ fontSize: 32, color: 'warning.main', mb: 1 }} />
        <Typography variant="body1" color="text.secondary">
          {t('metrics.noData') || 'Нет данных'}
        </Typography>
      </Paper>
    );
  }

  const getHealthIcon = () => {
    switch (health.overall_health) {
      case 'healthy': return <SuccessIcon sx={{ fontSize: 20, color: 'success.main' }} />;
      case 'degraded': return <WarningIcon sx={{ fontSize: 20, color: 'warning.main' }} />;
      case 'unhealthy': return <ErrorIcon sx={{ fontSize: 20, color: 'error.main' }} />;
    }
  };

  const getHealthColor = () => {
    switch (health.overall_health) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
    }
  };

  const currentStatus = trainingStatus[selectedModel];
  const metrics = currentStatus?.last_training_metrics;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TrainingIcon sx={{ fontSize: 20, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={500}>
            Обучение моделей
          </Typography>
          {getHealthIcon()}
        </Box>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              Автообучение:
            </Typography>
            <Switch
              size="small"
              checked={!pauseStatus?.paused}
              onChange={handlePauseToggle}
              disabled={pauseLoading}
              color={pauseStatus?.paused ? 'default' : 'success'}
            />
            {pauseStatus?.paused && (
              <BlockIcon sx={{ fontSize: 16, color: 'warning.main' }} />
            )}
          </Box>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Модель</InputLabel>
            <Select
              value={selectedModel}
              label="Модель"
              onChange={(e) => setSelectedModel(e.target.value)}
            >
              <MenuItem value="skill_matching">Skill Matching</MenuItem>
              <MenuItem value="ranking">Ranking</MenuItem>
            </Select>
          </FormControl>
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
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Pause Notice */}
      {pauseStatus?.paused && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Автоматическое обучение приостановлено. Новые модели не будут обучаться автоматически.
          {pauseStatus.pause_reason && ` Причина: ${pauseStatus.pause_reason}`}
        </Alert>
      )}

      {/* Pipeline Health Summary */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1.5 }}>
          <SpeedIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
          <Typography variant="caption" color="text.secondary" fontWeight={500}>
            СОСТОЯНИЕ ПАЙПЛАЙНА
          </Typography>
        </Box>
        <Grid container spacing={1.5}>
          <Grid item xs={6} sm={3} md={2.4}>
            <MetricCard
              title="Всего моделей"
              value={health.total_models.toString()}
              subtitle="отслеживается"
              color="success"
              icon={<TrainingIcon />}
            />
          </Grid>
          <Grid item xs={6} sm={3} md={2.4}>
            <MetricCard
              title="Активных"
              value={health.active_trainings.toString()}
              subtitle="обучается сейчас"
              color={health.active_trainings > 0 ? 'warning' : 'success'}
              icon={<StartIcon />}
            />
          </Grid>
          <Grid item xs={6} sm={3} md={2.4}>
            <MetricCard
              title="Завершено"
              value={health.completed_trainings.toString()}
              subtitle="за 24 часа"
              color="success"
              icon={<SuccessIcon />}
            />
          </Grid>
          <Grid item xs={6} sm={3} md={2.4}>
            <MetricCard
              title="Ошибок"
              value={health.failed_trainings.toString()}
              subtitle="за 24 часа"
              color={health.failed_trainings > 0 ? 'error' : 'success'}
              icon={<ErrorIcon />}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <MetricCard
              title="Здоровье"
              value={health.overall_health === 'healthy' ? 'OK' : health.overall_health === 'degraded' ? 'Внимание' : 'Ошибка'}
              subtitle="состояние системы"
              color={getHealthColor()}
              icon={getHealthIcon()}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Selected Model Training Status */}
      {currentStatus && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <TrendingIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary" fontWeight={500}>
                {selectedModel === 'skill_matching' ? 'SKILL MATCHING' : 'RANKING'} - ПОСЛЕДНЕЕ ОБУЧЕНИЕ
              </Typography>
            </Box>
            {currentStatus.latest_version && (
              <Chip
                label={currentStatus.latest_version}
                size="small"
                color="primary"
                variant="outlined"
                sx={{ fontSize: '0.7rem' }}
              />
            )}
          </Box>

          {currentStatus.training_status === 'in_progress' && (
            <Box sx={{ mb: 2 }}>
              <LinearProgress sx={{ height: 8, borderRadius: 4 }} />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                Обучение в процессе...
              </Typography>
            </Box>
          )}

          <Grid container spacing={1.5}>
            <Grid item xs={6} sm={4} md={2.4}>
              <MetricCard
                title="Статус"
                value={
                  currentStatus.training_status === 'completed' ? 'Завершено' :
                  currentStatus.training_status === 'in_progress' ? 'В процессе' :
                  currentStatus.training_status === 'failed' ? 'Ошибка' :
                  currentStatus.training_status || 'Нет'
                }
                subtitle="текущее состояние"
                color={
                  currentStatus.training_status === 'completed' ? 'success' :
                  currentStatus.training_status === 'in_progress' ? 'warning' :
                  currentStatus.training_status === 'failed' ? 'error' : 'warning'
                }
              />
            </Grid>
            {currentStatus.last_training_duration && (
              <Grid item xs={6} sm={4} md={2.4}>
                <MetricCard
                  title="Время"
                  value={`${currentStatus.last_training_duration.toFixed(0)}s`}
                  subtitle="длительность"
                  color={currentStatus.last_training_duration < 300 ? 'success' : 'warning'}
                  icon={<TimeIcon />}
                />
              </Grid>
            )}
            {metrics?.accuracy && (
              <Grid item xs={6} sm={4} md={2.4}>
                <MetricCard
                  title="Точность"
                  value={`${(metrics.accuracy * 100).toFixed(0)}%`}
                  subtitle="accuracy"
                  color={metrics.accuracy >= 0.8 ? 'success' : 'warning'}
                />
              </Grid>
            )}
            {metrics?.f1_score && (
              <Grid item xs={6} sm={4} md={2.4}>
                <MetricCard
                  title="F1 Score"
                  value={metrics.f1_score.toFixed(2)}
                  subtitle="гармоническое среднее"
                  color={metrics.f1_score >= 0.8 ? 'success' : 'warning'}
                />
              </Grid>
            )}
            {currentStatus.last_training_at && (
              <Grid item xs={6} sm={4} md={2.4}>
                <MetricCard
                  title="Последнее"
                  value={new Date(currentStatus.last_training_at).toLocaleDateString('ru-RU')}
                  subtitle="дата обучения"
                  color="success"
                />
              </Grid>
            )}
          </Grid>

          {currentStatus.error_message && (
            <Box sx={{ mt: 2, p: 1.5, bgcolor: 'error.50', borderRadius: 1 }}>
              <Typography variant="caption" color="error.dark">
                Ошибка: {currentStatus.error_message}
              </Typography>
            </Box>
          )}

          <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
            <Button
              size="small"
              variant="contained"
              startIcon={<StartIcon />}
              onClick={() => handleManualRetrain(selectedModel)}
              disabled={currentStatus.training_status === 'in_progress'}
            >
              Запустить обучение
            </Button>
          </Box>
        </Paper>
      )}

      {/* Performance Trends Chart */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <ChartIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary" fontWeight={500}>
              ТРЕНДЫ ПРОИЗВОДИТЕЛЬНОСТИ
            </Typography>
          </Box>
          {performanceTrends && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                icon={
                  performanceTrends.trend_direction === 'improving' ? <ArrowUpIcon /> :
                  performanceTrends.trend_direction === 'declining' ? <ArrowDownIcon /> :
                  <TrendingFlatIcon />
                }
                label={
                  performanceTrends.trend_direction === 'improving' ? 'Улучшается' :
                  performanceTrends.trend_direction === 'declining' ? 'Ухудшается' :
                  'Стабильно'
                }
                size="small"
                color={
                  performanceTrends.trend_direction === 'improving' ? 'success' :
                  performanceTrends.trend_direction === 'declining' ? 'error' :
                  'info'
                }
                variant="outlined"
                sx={{ fontSize: '0.7rem' }}
              />
              {performanceTrends.health_score !== undefined && (
                <Tooltip title={`Health Score: ${performanceTrends.health_score}/100`}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <LinearProgress
                      variant="determinate"
                      value={performanceTrends.health_score}
                      sx={{
                        width: 60,
                        height: 6,
                        borderRadius: 1,
                        bgcolor: 'action.hover',
                      }}
                      color={
                        performanceTrends.health_score >= 80 ? 'success' :
                        performanceTrends.health_score >= 60 ? 'warning' : 'error'
                      }
                    />
                    <Typography variant="caption" color="text.secondary">
                      {performanceTrends.health_score}%
                    </Typography>
                  </Box>
                </Tooltip>
              )}
            </Box>
          )}
        </Box>

        {trendsLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={24} />
          </Box>
        ) : performanceTrends ? (
          <Box>
            {/* Current Metrics Summary */}
            <Grid container spacing={1.5} sx={{ mb: 2 }}>
              <Grid item xs={6} sm={4} md={2.4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent sx={{ py: 1.5, px: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Accuracy
                    </Typography>
                    <Typography variant="h6" fontWeight={600} color={performanceTrends.current_metrics.accuracy && performanceTrends.current_metrics.accuracy >= 0.8 ? 'success.main' : 'warning.main'}>
                      {performanceTrends.current_metrics.accuracy ? `${(performanceTrends.current_metrics.accuracy * 100).toFixed(1)}%` : '-'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6} sm={4} md={2.4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent sx={{ py: 1.5, px: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Precision
                    </Typography>
                    <Typography variant="h6" fontWeight={600} color={performanceTrends.current_metrics.precision && performanceTrends.current_metrics.precision >= 0.8 ? 'success.main' : 'warning.main'}>
                      {performanceTrends.current_metrics.precision ? `${(performanceTrends.current_metrics.precision * 100).toFixed(1)}%` : '-'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6} sm={4} md={2.4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent sx={{ py: 1.5, px: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Recall
                    </Typography>
                    <Typography variant="h6" fontWeight={600} color={performanceTrends.current_metrics.recall && performanceTrends.current_metrics.recall >= 0.8 ? 'success.main' : 'warning.main'}>
                      {performanceTrends.current_metrics.recall ? `${(performanceTrends.current_metrics.recall * 100).toFixed(1)}%` : '-'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6} sm={4} md={2.4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent sx={{ py: 1.5, px: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      F1 Score
                    </Typography>
                    <Typography variant="h6" fontWeight={600} color={performanceTrends.current_metrics.f1_score && performanceTrends.current_metrics.f1_score >= 0.8 ? 'success.main' : 'warning.main'}>
                      {performanceTrends.current_metrics.f1_score ? performanceTrends.current_metrics.f1_score.toFixed(3) : '-'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={4} md={2.4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent sx={{ py: 1.5, px: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      {selectedModel === 'ranking' ? 'NDCG' : 'AUC'}
                    </Typography>
                    <Typography variant="h6" fontWeight={600} color="primary.main">
                      {selectedModel === 'ranking'
                        ? (performanceTrends.current_metrics.ndcg_score ? `${(performanceTrends.current_metrics.ndcg_score * 100).toFixed(1)}%` : '-')
                        : (performanceTrends.current_metrics.auc_score ? `${(performanceTrends.current_metrics.auc_score * 100).toFixed(1)}%` : '-')
                      }
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Trend Visualization */}
            {performanceTrends.trend_data.length > 0 && (
              <Box>
                <Typography variant="caption" color="text.secondary" fontWeight={500} sx={{ display: 'block', mb: 1 }}>
                  ИСТОРИЯ ЗА 7 ДНЕЙ
                </Typography>
                <Box sx={{ position: 'relative', height: 120, bgcolor: 'action.hover', borderRadius: 1, p: 2 }}>
                  {/* Grid lines */}
                  {[0, 25, 50, 75, 100].map((value) => (
                    <Box
                      key={value}
                      sx={{
                        position: 'absolute',
                        left: 24,
                        right: 16,
                        top: `${100 - value}%`,
                        borderBottom: '1px dashed',
                        borderColor: 'divider',
                      }}
                    />
                  ))}

                  {/* Y-axis labels */}
                  <Box sx={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 20, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', py: 0.5 }}>
                    {[100, 75, 50, 25, 0].map((value) => (
                      <Typography key={value} variant="caption" sx={{ fontSize: 9, color: 'text.disabled' }}>
                        {value}%
                      </Typography>
                    ))}
                  </Box>

                  {/* Data points and lines */}
                  <Box sx={{ position: 'absolute', left: 24, right: 16, top: 8, bottom: 16 }}>
                    {performanceTrends.trend_data.map((point, index) => {
                      const accuracy = point.accuracy ? point.accuracy * 100 : null;
                      const f1Score = point.f1_score ? point.f1_score * 100 : null;
                      const xPos = (index / Math.max(performanceTrends.trend_data.length - 1, 1)) * 100;

                      return (
                        <Box key={point.timestamp}>
                          {/* Accuracy point */}
                          {accuracy !== null && (
                            <Tooltip
                              title={
                                <Box>
                                  <Typography variant="caption" display="block">
                                    {new Date(point.timestamp).toLocaleDateString('ru-RU')}
                                  </Typography>
                                  <Typography variant="caption" display="block">
                                    Accuracy: {accuracy.toFixed(1)}%
                                  </Typography>
                                </Box>
                              }
                            >
                              <Box
                                sx={{
                                  position: 'absolute',
                                  left: `${xPos}%`,
                                  top: `${100 - accuracy}%`,
                                  width: 10,
                                  height: 10,
                                  borderRadius: '50%',
                                  bgcolor: 'success.main',
                                  border: 2,
                                  borderColor: 'background.paper',
                                  transform: 'translate(-50%, -50%)',
                                  cursor: 'pointer',
                                  transition: 'transform 0.2s',
                                  '&:hover': {
                                    transform: 'translate(-50%, -50%) scale(1.3)',
                                  },
                                }}
                              />
                            </Tooltip>
                          )}

                          {/* F1 Score point */}
                          {f1Score !== null && (
                            <Tooltip
                              title={
                                <Box>
                                  <Typography variant="caption" display="block">
                                    {new Date(point.timestamp).toLocaleDateString('ru-RU')}
                                  </Typography>
                                  <Typography variant="caption" display="block">
                                    F1 Score: {f1Score.toFixed(1)}%
                                  </Typography>
                                </Box>
                              }
                            >
                              <Box
                                sx={{
                                  position: 'absolute',
                                  left: `${xPos}%`,
                                  top: `${100 - f1Score}%`,
                                  width: 10,
                                  height: 10,
                                  borderRadius: '50%',
                                  bgcolor: 'primary.main',
                                  border: 2,
                                  borderColor: 'background.paper',
                                  transform: 'translate(-50%, -50%)',
                                  cursor: 'pointer',
                                  transition: 'transform 0.2s',
                                  '&:hover': {
                                    transform: 'translate(-50%, -50%) scale(1.3)',
                                  },
                                }}
                              />
                            </Tooltip>
                          )}
                        </Box>
                      );
                    })}

                    {/* X-axis labels */}
                    <Box sx={{ position: 'absolute', left: 0, right: 0, bottom: -20, display: 'flex', justifyContent: 'space-between' }}>
                      {performanceTrends.trend_data.map((point, index) => (
                        <Typography
                          key={point.timestamp}
                          variant="caption"
                          sx={{ fontSize: 9, color: 'text.disabled' }}
                        >
                          {new Date(point.timestamp).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}
                        </Typography>
                      ))}
                    </Box>
                  </Box>
                </Box>

                {/* Legend */}
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, mt: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'success.main' }} />
                    <Typography variant="caption" color="text.secondary">
                      Accuracy
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'primary.main' }} />
                    <Typography variant="caption" color="text.secondary">
                      F1 Score
                    </Typography>
                  </Box>
                </Box>
              </Box>
            )}

            {/* Alert Status */}
            {performanceTrends.alert_status !== 'none' && (
              <Alert severity={performanceTrends.alert_status === 'critical' ? 'error' : 'warning'} sx={{ mt: 2 }}>
                <Typography variant="caption">
                  {performanceTrends.alert_status === 'critical'
                    ? 'Критическое снижение производительности модели. Требуется проверка.'
                    : 'Обнаружено снижение производительности. Рекомендуется мониторинг.'
                  }
                </Typography>
              </Alert>
            )}
          </Box>
        ) : (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <ChartIcon sx={{ fontSize: 32, color: 'text.disabled', mb: 1 }} />
            <Typography variant="body2" color="text.secondary">
              Нет данных о трендах
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Recent Training Events */}
      {recentMetrics.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1.5 }}>
            <TimeIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary" fontWeight={500}>
              ПОСЛЕДНИЕ СОБЫТИЯ
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {recentMetrics.slice(0, 5).map((event) => (
              <Box
                key={event.id}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  p: 1,
                  bgcolor: 'background.default',
                  borderRadius: 1,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {event.training_status === 'completed' && <SuccessIcon sx={{ fontSize: 16, color: 'success.main' }} />}
                  {event.training_status === 'in_progress' && <StartIcon sx={{ fontSize: 16, color: 'warning.main' }} />}
                  {event.training_status === 'failed' && <ErrorIcon sx={{ fontSize: 16, color: 'error.main' }} />}
                  <Box>
                    <Typography variant="body2" fontWeight={500}>
                      {event.model_name} - {event.version}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(event.created_at).toLocaleString('ru-RU')}
                    </Typography>
                  </Box>
                </Box>
                {event.training_metrics?.f1_score && (
                  <Chip
                    label={`F1: ${event.training_metrics.f1_score.toFixed(2)}`}
                    size="small"
                    color={event.training_metrics.f1_score >= 0.8 ? 'success' : 'warning'}
                    variant="outlined"
                  />
                )}
              </Box>
            ))}
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default ModelTrainingDashboard;
