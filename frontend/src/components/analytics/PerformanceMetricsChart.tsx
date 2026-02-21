// React хуки для управления состоянием и эффектами
import React, { useState, useEffect, useCallback } from 'react';
// HTTP клиент для запросов к API
import axios from 'axios';
// Компоненты Material UI для создания интерфейса
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
  ToggleButton,
  ToggleButtonGroup,
  Divider,
} from '@mui/material';
// Иконки Material UI
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  ShowChart as ChartIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
// Recharts компоненты для визуализации данных
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

/**
 * Метрика производительности за один период
 */
interface PerformanceMetricPoint {
  /** Время записи метрики */
  timestamp: string;
  /** Точность модели */
  accuracy?: number;
  /** Precision */
  precision?: number;
  /** Recall */
  recall?: number;
  /** F1-score */
  f1_score?: number;
  /** Размер выборки для расчета */
  sample_count: number;
}

/**
 * Тренд производительности модели
 */
interface ModelPerformanceTrend {
  /** Название модели */
  model_name: string;
  /** Версия модели */
  model_version: string;
  /** Текущая точность */
  current_accuracy: number;
  /** Текущий F1-score */
  current_f1_score: number;
  /** Направление тренда */
  trend_direction: 'improving' | 'stable' | 'declining';
  /** Изменение тренда в процентах */
  trend_change_pct: number;
  /** Точки данных */
  data_points: PerformanceMetricPoint[];
  /** Статус алерта */
  alert_status?: string | null;
}

/**
 * Ответ API трендов производительности с бэкенда
 */
interface PerformanceTrendsResponse {
  /** Выбранный период */
  period: string;
  /** Начальная дата */
  start_date: string;
  /** Конечная дата */
  end_date: string;
  /** Массив моделей с метриками */
  models: ModelPerformanceTrend[];
  /** Общее направление тренда */
  overall_trend: 'improving' | 'stable' | 'declining';
  /** Общее количество оценок */
  total_evaluations: number;
}

/**
 * Свойства компонента PerformanceMetricsChart
 */
interface PerformanceMetricsChartProps {
  /** URL API endpoint для трендов производительности */
  apiUrl?: string;
  /** Период по умолчанию */
  defaultPeriod?: '7d' | '30d' | '90d';
}

/**
 * Форматирование процента для отображения
 */
const formatPercent = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Форматирование числа с разделителями
 */
const formatNumber = (value: number): string => {
  return value.toLocaleString();
};

/**
 * Получить иконку и цвет для направления тренда
 */
const getTrendInfo = (
  direction: string
): { icon: React.ReactElement; color: string; label: string } => {
  switch (direction) {
    case 'improving':
      return {
        icon: <TrendingUpIcon />,
        color: 'success.main',
        label: 'Improving',
      };
    case 'declining':
      return {
        icon: <TrendingDownIcon />,
        color: 'error.main',
        label: 'Declining',
      };
    default:
      return {
        icon: <TrendingFlatIcon />,
        color: 'warning.main',
        label: 'Stable',
      };
  }
};

/**
 * Кастомный тултип для Recharts
 */
const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{
    payload: {
      formattedDate: string;
      accuracy: number;
      f1_score: number;
      ndcg_score: number;
      sample_size: number;
    };
  }>;
}> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <Paper
        elevation={3}
        sx={{
          p: 1.5,
          border: '1px solid',
          borderColor: 'divider',
          minWidth: 180,
        }}
      >
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          {data.formattedDate}
        </Typography>
        <Stack spacing={0.5}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">
              Accuracy:
            </Typography>
            <Typography variant="body2" fontWeight={600} color="primary.main">
              {formatPercent(data.accuracy)}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">
              F1 Score:
            </Typography>
            <Typography variant="body2" fontWeight={600} color="success.main">
              {formatPercent(data.f1_score)}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">
              NDCG:
            </Typography>
            <Typography variant="body2" fontWeight={600} color="secondary.main">
              {formatPercent(data.ndcg_score)}
            </Typography>
          </Box>
          <Divider sx={{ my: 0.5 }} />
          <Typography variant="caption" color="text.secondary">
            Sample size: {formatNumber(data.sample_size)}
          </Typography>
        </Stack>
      </Paper>
    );
  }
  return null;
};

/**
 * Компонент PerformanceMetricsChart
 *
 * Отображает тренды производительности ML-модели во времени включая:
 * - Time-series line chart с Recharts (accuracy, F1, NDCG)
 * - Переключатель периода (7d, 30d, 90d)
 * - Индикатор направления тренда
 * - Агрегированные показатели за период
 * - Автообновление данных
 *
 * @example
 * ```tsx
 * <PerformanceMetricsChart />
 * ```
 *
 * @example
 * ```tsx
 * <PerformanceMetricsChart defaultPeriod="90d" />
 * ```
 */
const PerformanceMetricsChart: React.FC<PerformanceMetricsChartProps> = ({
  apiUrl = '/api/analytics/ai-explainability/performance-trends',
  defaultPeriod = '30d',
}) => {
  // Состояния для загрузки, ошибки, данных и настроек
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trendsData, setTrendsData] = useState<PerformanceTrendsResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>(defaultPeriod);

  /**
   * Загрузка данных трендов производительности с бэкенда
   */
  const fetchTrends = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get<PerformanceTrendsResponse>(apiUrl, {
        params: { period },
      });
      setTrendsData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load performance trends data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, period]);

  /**
   * Initial fetch on mount and when period changes
   */
  useEffect(() => {
    fetchTrends();
  }, [fetchTrends]);

  /**
   * Auto-refresh every 60 seconds when enabled
   */
  useEffect(() => {
    if (!autoRefreshEnabled) {
      return;
    }

    const interval = setInterval(() => {
      fetchTrends();
    }, 60000); // 60 seconds

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, fetchTrends]);

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = () => {
    setAutoRefreshEnabled((prev) => !prev);
  };

  /**
   * Handle period change
   */
  const handlePeriodChange = (
    _event: React.MouseEvent<HTMLElement>,
    newPeriod: '7d' | '30d' | '90d' | null
  ) => {
    if (newPeriod) {
      setPeriod(newPeriod);
    }
  };

  /**
   * Подготовка данных для графика
   */
  const chartData = React.useMemo(() => {
    // Get first model's data points (or aggregate all models if needed)
    if (!trendsData?.models || trendsData.models.length === 0) return [];

    const primaryModel = trendsData.models[0];
    return primaryModel.data_points.map((point) => ({
      formattedDate: new Date(point.timestamp).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      date: point.timestamp,
      accuracy: point.accuracy || 0,
      f1_score: point.f1_score || 0,
      ndcg_score: point.precision || 0, // Use precision as proxy for NDCG
      sample_size: point.sample_count,
      accuracyPercent: (point.accuracy || 0) * 100,
      f1Percent: (point.f1_score || 0) * 100,
      ndcgPercent: (point.precision || 0) * 100,
    }));
  }, [trendsData]);

  /**
   * Получить информацию о тренде
   */
  const trendInfo = trendsData ? getTrendInfo(trendsData.overall_trend) : null;

  /**
   * Получить агрегированные данные из первой модели
   */
  const aggregates = React.useMemo(() => {
    if (!trendsData?.models || trendsData.models.length === 0) {
      return { avg_accuracy: 0, avg_f1: 0, accuracy_change_pct: 0, avg_ndcg: 0 };
    }
    const primaryModel = trendsData.models[0];
    return {
      avg_accuracy: primaryModel.current_accuracy,
      avg_f1: primaryModel.current_f1_score,
      accuracy_change_pct: primaryModel.trend_change_pct,
      avg_ndcg: primaryModel.current_f1_score, // Use F1 as approximation for NDCG
    };
  }, [trendsData]);

  /**
   * Render loading state
   */
  if (loading && !trendsData) {
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
          Loading performance metrics...
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
          <Button
            color="inherit"
            size="small"
            onClick={fetchTrends}
            startIcon={<RefreshIcon />}
          >
            Retry
          </Button>
        }
        sx={{ mb: 3 }}
      >
        <AlertTitle>Error Loading Performance Metrics</AlertTitle>
        {error}
      </Alert>
    );
  }

  /**
   * Render empty state
   */
  if (!trendsData || !trendsData.models || trendsData.models.length === 0 || chartData.length === 0) {
    return (
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>No Performance Data Available</AlertTitle>
        Performance metrics will appear after the model has been running for some time. Collect
        more data by processing candidate rankings.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 3,
          bgcolor: 'primary.main',
          color: 'white',
          borderRadius: 2,
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" fontWeight="bold" gutterBottom>
              Model Performance Trends
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Track ML model accuracy, F1 score, and ranking quality over time
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
              <Chip
                icon={trendInfo?.icon as React.ReactElement}
                label={trendInfo?.label}
                size="small"
                sx={{
                  bgcolor: 'rgba(255,255,255,0.2)',
                  color: 'white',
                  '& .MuiChip-icon': { color: 'white' },
                }}
              />
              <Chip
                label={`${chartData.length} data points`}
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
            </Stack>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              size="small"
              onClick={toggleAutoRefresh}
              startIcon={autoRefreshEnabled ? <PauseIcon /> : <PlayIcon />}
              sx={{ borderColor: 'rgba(255,255,255,0.5)', color: 'white' }}
            >
              {autoRefreshEnabled ? 'Auto' : 'Paused'}
            </Button>
            <Button
              variant="outlined"
              size="small"
              onClick={fetchTrends}
              startIcon={<RefreshIcon />}
              sx={{ borderColor: 'rgba(255,255,255,0.5)', color: 'white' }}
            >
              Refresh
            </Button>
          </Stack>
        </Box>
      </Paper>

      {/* Period Selector and Summary Stats */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <ToggleButtonGroup
          value={period}
          exclusive
          onChange={handlePeriodChange}
          size="small"
          aria-label="period selector"
        >
          <ToggleButton value="7d" aria-label="7 days">
            7 Days
          </ToggleButton>
          <ToggleButton value="30d" aria-label="30 days">
            30 Days
          </ToggleButton>
          <ToggleButton value="90d" aria-label="90 days">
            90 Days
          </ToggleButton>
        </ToggleButtonGroup>

        {/* Trend Indicator */}
        {trendInfo && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Trend:
            </Typography>
            <Chip
              icon={trendInfo.icon}
              label={trendInfo.label}
              size="small"
              sx={{
                bgcolor: trendInfo.color + '.lighter',
                color: trendInfo.color,
                '& .MuiChip-icon': { color: trendInfo.color },
              }}
            />
          </Box>
        )}
      </Box>

      {/* Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
              <Typography variant="h4" color="primary.main" fontWeight={700}>
                {formatPercent(aggregates.avg_accuracy)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg Accuracy
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
              <Typography variant="h4" color="success.main" fontWeight={700}>
                {formatPercent(aggregates.avg_f1)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg F1 Score
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
              <Typography
                variant="h4"
                fontWeight={700}
                color={aggregates.accuracy_change_pct >= 0 ? 'success.main' : 'error.main'}
              >
                {aggregates.accuracy_change_pct >= 0 ? '+' : ''}
                {aggregates.accuracy_change_pct.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Accuracy Change
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
              <Typography variant="h4" color="secondary.main" fontWeight={700}>
                {aggregates.avg_ndcg ? formatPercent(aggregates.avg_ndcg) : 'N/A'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg NDCG
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Metrics Line Chart */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <ChartIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Performance Over Time
            </Typography>
          </Box>

          {chartData.length === 1 ? (
            // Single data point - show as info message with dot visualization
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Only one data point available. More data will appear over time.
              </Typography>
              <Stack direction="row" spacing={3} justifyContent="center" sx={{ mt: 2 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h5" color="primary.main" fontWeight={700}>
                    {formatPercent(chartData[0].accuracy)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Accuracy
                  </Typography>
                </Box>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h5" color="success.main" fontWeight={700}>
                    {formatPercent(chartData[0].f1_score)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    F1 Score
                  </Typography>
                </Box>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h5" color="secondary.main" fontWeight={700}>
                    {formatPercent(chartData[0].ndcg_score)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    NDCG
                  </Typography>
                </Box>
              </Stack>
            </Box>
          ) : (
            <Box sx={{ width: '100%', height: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="formattedDate"
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    axisLine={{ stroke: '#e0e0e0' }}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `${value}%`}
                    tickLine={false}
                    axisLine={{ stroke: '#e0e0e0' }}
                  />
                  <RechartsTooltip content={<CustomTooltip />} />
                  <Legend
                    wrapperStyle={{ fontSize: '12px' }}
                    iconType="circle"
                    iconSize={10}
                  />
                  <Line
                    type="monotone"
                    dataKey="accuracyPercent"
                    stroke="#1976d2"
                    strokeWidth={2}
                    dot={{ fill: '#1976d2', strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, strokeWidth: 0 }}
                    name="Accuracy"
                  />
                  <Line
                    type="monotone"
                    dataKey="f1Percent"
                    stroke="#2e7d32"
                    strokeWidth={2}
                    dot={{ fill: '#2e7d32', strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, strokeWidth: 0 }}
                    name="F1 Score"
                  />
                  <Line
                    type="monotone"
                    dataKey="ndcgPercent"
                    stroke="#9c27b0"
                    strokeWidth={2}
                    dot={{ fill: '#9c27b0', strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, strokeWidth: 0 }}
                    name="NDCG Score"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          )}

          {/* Legend */}
          <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Metrics Explanation
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SpeedIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="body2" fontWeight={600}>
                      Accuracy
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Overall prediction correctness
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TimelineIcon color="success" fontSize="small" />
                  <Box>
                    <Typography variant="body2" fontWeight={600}>
                      F1 Score
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Balance of precision & recall
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ChartIcon color="secondary" fontSize="small" />
                  <Box>
                    <Typography variant="body2" fontWeight={600}>
                      NDCG Score
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Ranking quality measure
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </CardContent>
      </Card>

      {/* Insights Card */}
      <Card sx={{ mt: 3, bgcolor: 'grey.50' }}>
        <CardContent>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Performance Insights
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Chip
              icon={trendInfo?.icon as React.ReactElement}
              label={`Model performance is ${trendsData.overall_trend}`}
              color={trendsData.overall_trend === 'improving' ? 'success' : trendsData.overall_trend === 'declining' ? 'error' : 'warning'}
              variant="outlined"
              size="small"
            />
            <Chip
              icon={<SpeedIcon />}
              label={`Avg accuracy: ${formatPercent(aggregates.avg_accuracy)}`}
              color="primary"
              variant="outlined"
              size="small"
            />
            {aggregates.accuracy_change_pct !== 0 && (
              <Chip
                icon={aggregates.accuracy_change_pct > 0 ? <TrendingUpIcon /> : <TrendingDownIcon />}
                label={`${aggregates.accuracy_change_pct > 0 ? '+' : ''}${aggregates.accuracy_change_pct.toFixed(1)}% change this period`}
                color={aggregates.accuracy_change_pct > 0 ? 'success' : 'error'}
                variant="outlined"
                size="small"
              />
            )}
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
};

export default PerformanceMetricsChart;
