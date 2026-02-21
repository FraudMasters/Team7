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
  Tooltip,
} from '@mui/material';
// Иконки Material UI
import {
  Refresh as RefreshIcon,
  BarChart as BarChartIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Info as InfoIcon,
  AutoGraph as AutoGraphIcon,
} from '@mui/icons-material';
// Recharts компоненты для визуализации данных
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

/**
 * Интерфейс отдельного признака (feature) с бэкенда
 * Matches backend FeatureImportanceItem schema
 */
interface FeatureItem {
  /** Название признака */
  feature_name: string;
  /** Важность признака (0-1) */
  importance_score: number;
  /** Ранг признака по важности */
  rank: number;
  /** Описание признака */
  description: string;
  /** Категория признака */
  category?: string;
}

/**
 * Ответ API о важности признаков с бэкенда
 */
interface FeatureImportanceResponse {
  /** Массив признаков с их важностью */
  features: FeatureItem[];
  /** Версия модели */
  model_version: string;
  /** Тип модели */
  model_type: string;
}

/**
 * Свойства компонента FeatureImportanceChart
 */
interface FeatureImportanceChartProps {
  /** URL API endpoint для важности признаков */
  apiUrl?: string;
  /** Опциональный фильтр начальной даты */
  startDate?: string;
  /** Опциональный фильтр конечной даты */
  endDate?: string;
  /** Максимальное количество признаков для отображения */
  maxFeatures?: number;
}

/**
 * Форматирование важности для отображения в процентах
 */
const formatImportance = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Получить цвет для признака на основе его важности
 */
const getBarColor = (importance: number, index: number): string => {
  // Цвета от наиболее важных к наименее важным
  const colors = [
    '#1976d2', // primary blue (самый важный)
    '#2196f3',
    '#03a9f4',
    '#00bcd4',
    '#009688',
    '#4caf50',
    '#8bc34a',
    '#cddc39',
    '#ffeb3b',
    '#ffc107',
    '#ff9800',
    '#ff5722',
    '#795548', // наименее важный
  ];

  if (importance >= 0.15) return colors[0];
  if (importance >= 0.12) return colors[1];
  if (importance >= 0.10) return colors[2];
  if (importance >= 0.08) return colors[3];
  if (importance >= 0.06) return colors[4];

  // Для остальных используем индекс для разнообразия
  return colors[Math.min(index, colors.length - 1)];
};

/**
 * Форматирование названия признака для отображения
 */
const formatFeatureName = (name: string): string => {
  // Преобразуем snake_case в читаемый формат
  return name
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Кастомный тултип для Recharts
 */
const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{
    payload: FeatureItem & { formattedName: string; importancePercent: number };
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
          maxWidth: 300,
        }}
      >
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          {data.formattedName}
        </Typography>
        <Typography variant="body2" color="primary.main" fontWeight={600}>
          Importance: {formatImportance(data.importance_score)}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
          {data.description}
        </Typography>
        {data.category && (
          <Chip
            label={data.category}
            size="small"
            variant="outlined"
            sx={{ mt: 0.5, fontSize: '0.7rem', height: 20 }}
          />
        )}
      </Paper>
    );
  }
  return null;
};

/**
 * Компонент FeatureImportanceChart
 *
 * Отображает важность признаков ML-модели включая:
 * - Горизонтальную гистограмму с Recharts BarChart
 * - Все 13 признаков отсортированных по важности
 * - Hover tooltips с описанием каждого признака
 * - Информацию о версии и типе модели
 * - Автообновление данных
 *
 * @example
 * ```tsx
 * <FeatureImportanceChart />
 * ```
 *
 * @example
 * ```tsx
 * <FeatureImportanceChart startDate="2024-01-01" endDate="2024-12-31" maxFeatures={10} />
 * ```
 */
const FeatureImportanceChart: React.FC<FeatureImportanceChartProps> = ({
  apiUrl = '/api/analytics/ai-explainability/feature-importance',
  startDate,
  endDate,
  maxFeatures = 13,
}) => {
  // Состояния для загрузки, ошибки, данных и автообновления
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [featureData, setFeatureData] = useState<FeatureImportanceResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  /**
   * Загрузка данных о важности признаков с бэкенда
   */
  const fetchFeatureImportance = useCallback(async () => {
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
      if (maxFeatures) {
        params.limit = maxFeatures.toString();
      }

      const response = await axios.get<FeatureImportanceResponse>(apiUrl, { params });
      setFeatureData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load feature importance data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, startDate, endDate, maxFeatures]);

  /**
   * Initial fetch on mount and when dependencies change
   */
  useEffect(() => {
    fetchFeatureImportance();
  }, [fetchFeatureImportance]);

  /**
   * Auto-refresh every 60 seconds when enabled
   */
  useEffect(() => {
    if (!autoRefreshEnabled) {
      return;
    }

    const interval = setInterval(() => {
      fetchFeatureImportance();
    }, 60000); // 60 seconds

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, fetchFeatureImportance]);

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = () => {
    setAutoRefreshEnabled((prev) => !prev);
  };

  /**
   * Подготовка данных для графика
   */
  const chartData = React.useMemo(() => {
    if (!featureData?.features) return [];

    return featureData.features
      .sort((a, b) => b.importance_score - a.importance_score) // Сортировка по убыванию важности
      .slice(0, maxFeatures)
      .map((feature, index) => ({
        ...feature,
        formattedName: formatFeatureName(feature.feature_name),
        importancePercent: feature.importance_score * 100,
        index,
      }));
  }, [featureData, maxFeatures]);

  /**
   * Вычисление общей важности для отображения
   */
  const totalImportance = React.useMemo(() => {
    if (!chartData.length) return 0;
    return chartData.reduce((sum, f) => sum + f.importance_score, 0);
  }, [chartData]);

  /**
   * Render loading state
   */
  if (loading && !featureData) {
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
          Loading feature importance data...
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
          <Button color="inherit" size="small" onClick={fetchFeatureImportance} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
        sx={{ mb: 3 }}
      >
        <AlertTitle>Error Loading Feature Importance</AlertTitle>
        {error}
      </Alert>
    );
  }

  /**
   * Render empty state
   */
  if (!featureData || !featureData.features || featureData.features.length === 0) {
    return (
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>No Feature Importance Data</AlertTitle>
        Feature importance data will be available after the ML model is trained. Train the ranking
        model to see which factors most influence candidate rankings.
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
              Feature Importance Analysis
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Which factors most influence the ML ranking model's decisions
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
              <Chip
                label={`${chartData.length} features`}
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
              <Chip
                label={`Model: ${featureData.model_type || 'Random Forest'}`}
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
              {featureData.model_version && (
                <Chip
                  label={`v${featureData.model_version}`}
                  size="small"
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                />
              )}
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
              onClick={fetchFeatureImportance}
              startIcon={<RefreshIcon />}
              sx={{ borderColor: 'rgba(255,255,255,0.5)', color: 'white' }}
            >
              Refresh
            </Button>
          </Stack>
        </Box>
      </Paper>

      {/* Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1 }}>
              <Typography variant="h4" color="primary.main" fontWeight={700}>
                {chartData.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Features Analyzed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1 }}>
              <Typography variant="h4" color="success.main" fontWeight={700}>
                {formatImportance(chartData[0]?.importance_score || 0)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Top Feature
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1 }}>
              <Typography variant="h4" fontWeight={700}>
                {formatImportance(chartData[Math.floor(chartData.length / 2)]?.importance_score || 0)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Median Importance
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 1 }}>
              <Typography variant="h4" color="info.main" fontWeight={700}>
                {formatImportance(totalImportance)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Weight
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Feature Importance Chart */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BarChartIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Feature Contributions to Ranking Score
              </Typography>
            </Box>
            <Tooltip title="Hover over bars to see detailed feature descriptions">
              <InfoIcon color="action" sx={{ cursor: 'help' }} />
            </Tooltip>
          </Box>

          <Box sx={{ width: '100%', height: Math.max(400, chartData.length * 35) }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                <XAxis
                  type="number"
                  domain={[0, 'auto']}
                  tickFormatter={(value) => `${(value).toFixed(0)}%`}
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  type="category"
                  dataKey="formattedName"
                  width={180}
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) =>
                    value.length > 20 ? `${value.substring(0, 18)}...` : value
                  }
                />
                <RechartsTooltip content={<CustomTooltip />} />
                <Bar dataKey="importancePercent" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getBarColor(entry.importance_score, index)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Box>

          {/* Legend */}
          <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Importance Legend
            </Typography>
            <Grid container spacing={1}>
              <Grid item xs={6} sm={3}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#1976d2' }} />
                  <Typography variant="caption">≥15% Very High</Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#03a9f4' }} />
                  <Typography variant="caption">10-15% High</Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#009688' }} />
                  <Typography variant="caption">6-10% Medium</Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#ff9800' }} />
                  <Typography variant="caption">&lt;6% Low</Typography>
                </Box>
              </Grid>
            </Grid>
          </Box>

          {/* Feature Details Table */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AutoGraphIcon fontSize="small" />
              Top Feature Descriptions
            </Typography>
            <Grid container spacing={1}>
              {chartData.slice(0, 5).map((feature, index) => (
                <Grid item xs={12} sm={6} md={2.4} key={feature.feature_name}>
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 1.5,
                      height: '100%',
                      borderLeft: 3,
                      borderLeftColor: getBarColor(feature.importance_score, index),
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                      <Chip
                        label={`#${index + 1}`}
                        size="small"
                        color={index < 3 ? 'primary' : 'default'}
                        sx={{ height: 18, fontSize: '0.65rem' }}
                      />
                      <Typography variant="caption" fontWeight={600}>
                        {formatImportance(feature.importance_score)}
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                      {feature.description}
                    </Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Box>
        </CardContent>
      </Card>

      {/* Info Alert */}
      <Alert severity="info" sx={{ mt: 3 }} icon={<InfoIcon />}>
        <AlertTitle>Understanding Feature Importance</AlertTitle>
        <Typography variant="body2">
          Feature importance indicates how much each factor contributes to the final ranking score.
          Higher importance means the feature has more influence on the model's decisions.
          The percentages shown are relative weights, not absolute contribution values.
        </Typography>
      </Alert>
    </Box>
  );
};

export default FeatureImportanceChart;
