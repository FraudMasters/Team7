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
  Psychology as BrainIcon,
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
 * Точка данных о точности модели за период
 */
interface AccuracyDataPoint {
  /** Временная метка */
  timestamp: string;
  /** Точность модели (0-1) */
  accuracy: number;
  /** Количество предсказаний */
  prediction_count: number;
  /** Средний уровень уверенности */
  avg_confidence?: number;
}

/**
 * Ответ API с трендами точности модели
 */
interface ModelAccuracyTrendResponse {
  /** Выбранный период */
  period: string;
  /** Начальная дата */
  start_date: string;
  /** Конечная дата */
  end_date: string;
  /** Точки данных */
  data_points: AccuracyDataPoint[];
  /** Текущая точность */
  current_accuracy: number;
  /** Изменение точности в процентах */
  accuracy_change_pct: number;
  /** Направление тренда */
  trend_direction: 'improving' | 'stable' | 'declining';
  /** Общее количество предсказаний */
  total_predictions: number;
}

/**
 * Свойства компонента ModelAccuracyTrend
 */
interface ModelAccuracyTrendProps {
  /** URL API endpoint для трендов точности модели */
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
      prediction_count: number;
      avg_confidence?: number;
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
          {data.avg_confidence !== undefined && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Avg Confidence:
              </Typography>
              <Typography variant="body2" fontWeight={600} color="success.main">
                {formatPercent(data.avg_confidence)}
              </Typography>
            </Box>
          )}
          <Divider sx={{ my: 0.5 }} />
          <Typography variant="caption" color="text.secondary">
            {formatNumber(data.prediction_count)} predictions
          </Typography>
        </Stack>
      </Paper>
    );
  }
  return null;
};

/**
 * Компонент ModelAccuracyTrend
 *
 * Отображает тренды точности ML-модели во времени включая:
 * - Time-series line chart с Recharts (accuracy over time)
 * - Переключатель периода (7d, 30d, 90d)
 * - Индикатор направления тренда
 * - Агрегированные показатели за период
 * - Автообновление данных
 *
 * @example
 * ```tsx
 * <ModelAccuracyTrend />
 * ```
 *
 * @example
 * ```tsx
 * <ModelAccuracyTrend defaultPeriod="90d" />
 * ```
 */
const ModelAccuracyTrend: React.FC<ModelAccuracyTrendProps> = ({
  apiUrl = '/api/analytics/model-accuracy-trend',
  defaultPeriod = '30d',
}) => {
  // Состояния для загрузки, ошибки, данных и настроек
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trendData, setTrendData] = useState<ModelAccuracyTrendResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>(defaultPeriod);

  /**
   * Загрузка данных трендов точности модели с бэкенда
   */
  const fetchTrends = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get<ModelAccuracyTrendResponse>(apiUrl, {
        params: { period },
      });
      setTrendData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load model accuracy trend data';
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
    if (!trendData?.data_points) return [];

    return trendData.data_points.map((point) => ({
      formattedDate: new Date(point.timestamp).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      date: point.timestamp,
      accuracy: point.accuracy,
      accuracyPercent: point.accuracy * 100,
      prediction_count: point.prediction_count,
      avg_confidence: point.avg_confidence,
      avgConfidencePercent: point.avg_confidence ? point.avg_confidence * 100 : undefined,
    }));
  }, [trendData]);

  /**
   * Получить информацию о тренде
   */
  const trendInfo = trendData ? getTrendInfo(trendData.trend_direction) : null;

  /**
   * Render loading state
   */
  if (loading && !trendData) {
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
          Loading model accuracy trends...
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
        <AlertTitle>Error Loading Model Accuracy Trends</AlertTitle>
        {error}
      </Alert>
    );
  }

  /**
   * Render empty state
   */
  if (!trendData || !trendData.data_points || trendData.data_points.length === 0) {
    return (
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>No Accuracy Data Available</AlertTitle>
        Model accuracy trends will appear after the model has made predictions and received
        feedback. Collect more data by processing candidate rankings.
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
              Model Accuracy Trends
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Track AI model accuracy and performance over time
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
                label={`${formatNumber(trendData.total_predictions)} predictions`}
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
        <Grid item xs={12} sm={4}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
              <Typography variant="h4" color="primary.main" fontWeight={700}>
                {formatPercent(trendData.current_accuracy)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Current Accuracy
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
              <Typography
                variant="h4"
                fontWeight={700}
                color={trendData.accuracy_change_pct >= 0 ? 'success.main' : 'error.main'}
              >
                {trendData.accuracy_change_pct >= 0 ? '+' : ''}
                {trendData.accuracy_change_pct.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Accuracy Change
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
              <Typography variant="h4" color="secondary.main" fontWeight={700}>
                {chartData.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Data Points
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Model Accuracy Line Chart */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <ChartIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Accuracy Over Time
            </Typography>
          </Box>

          {chartData.length === 1 ? (
            // Single data point - show as info message with value visualization
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
                {chartData[0].avg_confidence !== undefined && (
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" color="success.main" fontWeight={700}>
                      {formatPercent(chartData[0].avg_confidence)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Avg Confidence
                    </Typography>
                  </Box>
                )}
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
                    strokeWidth={3}
                    dot={{ fill: '#1976d2', strokeWidth: 2, r: 5 }}
                    activeDot={{ r: 7, strokeWidth: 0 }}
                    name="Model Accuracy"
                  />
                  {chartData.some(d => d.avgConfidencePercent !== undefined) && (
                    <Line
                      type="monotone"
                      dataKey="avgConfidencePercent"
                      stroke="#2e7d32"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={{ fill: '#2e7d32', strokeWidth: 2, r: 4 }}
                      activeDot={{ r: 6, strokeWidth: 0 }}
                      name="Avg Confidence"
                    />
                  )}
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
              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <BrainIcon color="primary" fontSize="small" />
                  <Box>
                    <Typography variant="body2" fontWeight={600}>
                      Model Accuracy
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Percentage of correct predictions based on feedback
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TimelineIcon color="success" fontSize="small" />
                  <Box>
                    <Typography variant="body2" fontWeight={600}>
                      Avg Confidence
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Average confidence level of model predictions
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
            Accuracy Insights
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Chip
              icon={trendInfo?.icon as React.ReactElement}
              label={`Model accuracy is ${trendData.trend_direction}`}
              color={
                trendData.trend_direction === 'improving'
                  ? 'success'
                  : trendData.trend_direction === 'declining'
                  ? 'error'
                  : 'warning'
              }
              variant="outlined"
              size="small"
            />
            <Chip
              icon={<BrainIcon />}
              label={`Current accuracy: ${formatPercent(trendData.current_accuracy)}`}
              color="primary"
              variant="outlined"
              size="small"
            />
            {trendData.accuracy_change_pct !== 0 && (
              <Chip
                icon={
                  trendData.accuracy_change_pct > 0 ? (
                    <TrendingUpIcon />
                  ) : (
                    <TrendingDownIcon />
                  )
                }
                label={`${trendData.accuracy_change_pct > 0 ? '+' : ''}${trendData.accuracy_change_pct.toFixed(1)}% change this period`}
                color={trendData.accuracy_change_pct > 0 ? 'success' : 'error'}
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

export default ModelAccuracyTrend;
