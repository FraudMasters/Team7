// React хуки для управления состоянием и эффектами
import React, { useState, useEffect, useCallback } from 'react';
// Компоненты Material UI для создания интерфейса
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
  Chip,
  ToggleButton,
  ToggleButtonGroup,
  Divider,
} from '@mui/material';
// Иконки Material UI
import {
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  ShowChart as ChartIcon,
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
// API клиент для получения данных о fairness
import { fairness } from '@/api/fairness';
// Типы API для типизации данных
import type {
  FairnessTrendsResponse,
  FairnessTrendDataPoint,
} from '@/types/api';

/**
 * Свойства компонента FairnessTrendsChart
 * @description Определяет параметры для графика трендов fairness
 */
interface FairnessTrendsChartProps {
  /** Опциональный фильтр названия модели */
  modelName?: string;
  /** Опциональный фильтр версии модели */
  modelVersion?: string;
  /** Опциональный фильтр защищаемого атрибута */
  protectedAttribute?: string;
  /** Период по умолчанию */
  defaultPeriod?: '7d' | '30d' | '90d';
}

/**
 * Форматирование числа для отображения
 */
const formatNumber = (value: number): string => {
  return value.toFixed(3);
};

/**
 * Форматирование даты для графика
 */
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
};

/**
 * Получить цвет метрики на основе ее значения
 */
const getMetricColor = (metricName: string): string => {
  const colors: Record<string, string> = {
    disparate_impact_ratio: '#1976d2', // blue
    demographic_parity_diff: '#2e7d32', // green
    equal_opportunity_diff: '#ed6c02', // orange
    average_odds_diff: '#9c27b0', // purple
    theil_index: '#d32f2f', // red
  };
  return colors[metricName] || '#757575';
};

/**
 * Получить читаемое название метрики
 */
const getMetricLabel = (metricName: string): string => {
  const labels: Record<string, string> = {
    disparate_impact_ratio: 'Disparate Impact Ratio',
    demographic_parity_diff: 'Demographic Parity Diff',
    equal_opportunity_diff: 'Equal Opportunity Diff',
    average_odds_diff: 'Average Odds Diff',
    theil_index: 'Theil Index',
  };
  return labels[metricName] || metricName;
};

/**
 * Кастомный тултип для Recharts
 */
const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    payload: {
      formattedDate: string;
      sample_size: number;
    };
  }>;
}> = ({ active, payload }) => {
  if (active && payload && payload.length > 0) {
    const data = payload[0].payload;
    return (
      <Paper
        elevation={3}
        sx={{
          p: 1.5,
          border: '1px solid',
          borderColor: 'divider',
          minWidth: 200,
        }}
      >
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          {data.formattedDate}
        </Typography>
        <Stack spacing={0.5}>
          {payload.map((entry) => (
            <Box key={entry.name} sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                {entry.name}:
              </Typography>
              <Typography variant="body2" fontWeight={600} sx={{ color: entry.color }}>
                {entry.value !== null ? formatNumber(entry.value) : 'N/A'}
              </Typography>
            </Box>
          ))}
          <Divider sx={{ my: 0.5 }} />
          <Typography variant="caption" color="text.secondary">
            Sample size: {data.sample_size.toLocaleString()}
          </Typography>
        </Stack>
      </Paper>
    );
  }
  return null;
};

/**
 * Компонент FairnessTrendsChart
 *
 * Отображает тренды метрик fairness во времени включая:
 * - Time-series line chart с Recharts
 * - Disparate Impact Ratio
 * - Demographic Parity Difference
 * - Equal Opportunity Difference
 * - Average Odds Difference
 * - Theil Index
 * - Переключатель периода (7d, 30d, 90d)
 * - Интерактивные tooltips
 *
 * @example
 * ```tsx
 * <FairnessTrendsChart />
 * ```
 *
 * @example
 * ```tsx
 * <FairnessTrendsChart
 *   modelName="ranking"
 *   protectedAttribute="gender"
 *   defaultPeriod="30d"
 * />
 * ```
 */
const FairnessTrendsChart: React.FC<FairnessTrendsChartProps> = ({
  modelName,
  modelVersion,
  protectedAttribute,
  defaultPeriod = '30d',
}) => {
  // Состояния для загрузки, ошибки, данных и настроек
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trendsData, setTrendsData] = useState<FairnessTrendsResponse | null>(null);
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>(defaultPeriod);

  /**
   * Вычислить даты начала и конца на основе периода
   */
  const getDateRange = useCallback((selectedPeriod: '7d' | '30d' | '90d'): { start_date: string; end_date: string } => {
    const endDate = new Date();
    const startDate = new Date();

    switch (selectedPeriod) {
      case '7d':
        startDate.setDate(endDate.getDate() - 7);
        break;
      case '30d':
        startDate.setDate(endDate.getDate() - 30);
        break;
      case '90d':
        startDate.setDate(endDate.getDate() - 90);
        break;
    }

    return {
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
    };
  }, []);

  /**
   * Загрузка данных трендов fairness с бэкенда
   */
  const fetchTrends = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const dateRange = getDateRange(period);

      const response = await fairness.getTrends({
        start_date: dateRange.start_date,
        end_date: dateRange.end_date,
        model_name: modelName,
        model_version: modelVersion,
        protected_attribute: protectedAttribute,
      });

      setTrendsData(response);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load fairness trends data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [period, modelName, modelVersion, protectedAttribute, getDateRange]);

  /**
   * Initial fetch on mount and when dependencies change
   */
  useEffect(() => {
    fetchTrends();
  }, [fetchTrends]);

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
    if (!trendsData?.data_points || trendsData.data_points.length === 0) return [];

    return trendsData.data_points.map((point: FairnessTrendDataPoint) => ({
      formattedDate: formatDate(point.timestamp),
      date: point.timestamp,
      disparate_impact_ratio: point.disparate_impact_ratio,
      demographic_parity_diff: point.demographic_parity_diff,
      equal_opportunity_diff: point.equal_opportunity_diff,
      average_odds_diff: point.average_odds_diff,
      theil_index: point.theil_index,
      sample_size: point.sample_size,
    }));
  }, [trendsData]);

  /**
   * Вычисление средних значений метрик
   */
  const averages = React.useMemo(() => {
    if (!chartData || chartData.length === 0) {
      return {
        disparate_impact_ratio: 0,
        demographic_parity_diff: 0,
        equal_opportunity_diff: 0,
        average_odds_diff: 0,
        theil_index: 0,
      };
    }

    const sum = chartData.reduce(
      (acc, point) => ({
        disparate_impact_ratio: acc.disparate_impact_ratio + (point.disparate_impact_ratio || 0),
        demographic_parity_diff: acc.demographic_parity_diff + (point.demographic_parity_diff || 0),
        equal_opportunity_diff: acc.equal_opportunity_diff + (point.equal_opportunity_diff || 0),
        average_odds_diff: acc.average_odds_diff + (point.average_odds_diff || 0),
        theil_index: acc.theil_index + (point.theil_index || 0),
        count: acc.count + 1,
      }),
      {
        disparate_impact_ratio: 0,
        demographic_parity_diff: 0,
        equal_opportunity_diff: 0,
        average_odds_diff: 0,
        theil_index: 0,
        count: 0,
      }
    );

    return {
      disparate_impact_ratio: sum.disparate_impact_ratio / sum.count,
      demographic_parity_diff: sum.demographic_parity_diff / sum.count,
      equal_opportunity_diff: sum.equal_opportunity_diff / sum.count,
      average_odds_diff: sum.average_odds_diff / sum.count,
      theil_index: sum.theil_index / sum.count,
    };
  }, [chartData]);

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
          Loading fairness trends...
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
        <AlertTitle>Error Loading Fairness Trends</AlertTitle>
        {error}
      </Alert>
    );
  }

  /**
   * Render empty state
   */
  if (!trendsData || !trendsData.data_points || trendsData.data_points.length === 0) {
    return (
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>No Fairness Trends Data Available</AlertTitle>
        Fairness trends will appear after metrics have been collected over time. Process more
        candidates to generate fairness data.
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
              Fairness Metrics Trends
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Track fairness metrics evolution over time
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
              <Chip
                icon={<TimelineIcon />}
                label={`${chartData.length} data points`}
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', '& .MuiChip-icon': { color: 'white' } }}
              />
              {protectedAttribute && (
                <Chip
                  label={`Attribute: ${protectedAttribute}`}
                  size="small"
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                />
              )}
              {modelName && (
                <Chip
                  label={`Model: ${modelName}`}
                  size="small"
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                />
              )}
            </Stack>
          </Box>
          <Button
            variant="outlined"
            size="small"
            onClick={fetchTrends}
            startIcon={<RefreshIcon />}
            sx={{ borderColor: 'rgba(255,255,255,0.5)', color: 'white' }}
          >
            Refresh
          </Button>
        </Box>
      </Paper>

      {/* Period Selector */}
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

        <Typography variant="body2" color="text.secondary">
          {trendsData.start_date} to {trendsData.end_date}
        </Typography>
      </Box>

      {/* Fairness Metrics Line Chart */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <ChartIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Fairness Metrics Over Time
            </Typography>
          </Box>

          {chartData.length === 1 ? (
            // Single data point - show as info message
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Only one data point available. More data will appear over time.
              </Typography>
              <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: 2, flexWrap: 'wrap' }}>
                {chartData[0].disparate_impact_ratio !== null && (
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" color="primary.main" fontWeight={700}>
                      {formatNumber(chartData[0].disparate_impact_ratio)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Disparate Impact
                    </Typography>
                  </Box>
                )}
                {chartData[0].demographic_parity_diff !== null && (
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" color="success.main" fontWeight={700}>
                      {formatNumber(chartData[0].demographic_parity_diff)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Demographic Parity
                    </Typography>
                  </Box>
                )}
                {chartData[0].equal_opportunity_diff !== null && (
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" sx={{ color: '#ed6c02' }} fontWeight={700}>
                      {formatNumber(chartData[0].equal_opportunity_diff)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Equal Opportunity
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
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => formatNumber(value)}
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
                    dataKey="disparate_impact_ratio"
                    stroke={getMetricColor('disparate_impact_ratio')}
                    strokeWidth={2}
                    dot={{ fill: getMetricColor('disparate_impact_ratio'), strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, strokeWidth: 0 }}
                    name="Disparate Impact Ratio"
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="demographic_parity_diff"
                    stroke={getMetricColor('demographic_parity_diff')}
                    strokeWidth={2}
                    dot={{ fill: getMetricColor('demographic_parity_diff'), strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, strokeWidth: 0 }}
                    name="Demographic Parity Diff"
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="equal_opportunity_diff"
                    stroke={getMetricColor('equal_opportunity_diff')}
                    strokeWidth={2}
                    dot={{ fill: getMetricColor('equal_opportunity_diff'), strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, strokeWidth: 0 }}
                    name="Equal Opportunity Diff"
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="average_odds_diff"
                    stroke={getMetricColor('average_odds_diff')}
                    strokeWidth={2}
                    dot={{ fill: getMetricColor('average_odds_diff'), strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, strokeWidth: 0 }}
                    name="Average Odds Diff"
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="theil_index"
                    stroke={getMetricColor('theil_index')}
                    strokeWidth={2}
                    dot={{ fill: getMetricColor('theil_index'), strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6, strokeWidth: 0 }}
                    name="Theil Index"
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          )}

          {/* Metrics Explanation */}
          <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Average Values (Period)
            </Typography>
            <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
              <Chip
                icon={<TrendingUpIcon />}
                label={`Disparate Impact: ${formatNumber(averages.disparate_impact_ratio)}`}
                size="small"
                sx={{ bgcolor: 'background.paper' }}
              />
              <Chip
                icon={<TrendingUpIcon />}
                label={`Demographic Parity: ${formatNumber(averages.demographic_parity_diff)}`}
                size="small"
                sx={{ bgcolor: 'background.paper' }}
              />
              <Chip
                icon={<TrendingUpIcon />}
                label={`Equal Opportunity: ${formatNumber(averages.equal_opportunity_diff)}`}
                size="small"
                sx={{ bgcolor: 'background.paper' }}
              />
              <Chip
                icon={<TrendingDownIcon />}
                label={`Theil Index: ${formatNumber(averages.theil_index)}`}
                size="small"
                sx={{ bgcolor: 'background.paper' }}
              />
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default FairnessTrendsChart;
