// React хуки для управления состоянием и эффектами
import React, { useState, useEffect } from 'react';
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
  LinearProgress,
  Chip,
  Divider,
} from '@mui/material';
// Иконки Material UI
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  EmojiEvents as TrophyIcon,
  Stars as StarsIcon,
  Psychology as BrainIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Assessment as ChartIcon,
} from '@mui/icons-material';

/**
 * Метрики конверсии обратной связи с бэкенда
 */
interface FeedbackConversionMetrics {
  total_recommendations: number;
  recommendations_with_feedback: number;
  feedback_rate: number;
  positive_feedback_count: number;
  negative_feedback_count: number;
  positive_feedback_rate: number;
}

/**
 * Метрики успеха top-N рекомендаций с бэкенда
 */
interface TopNRecommendationMetrics {
  top_1_success_rate: number;
  top_3_success_rate: number;
  top_5_success_rate: number;
  top_10_success_rate: number;
  top_1_hired_count: number;
  top_5_hired_count: number;
  top_10_hired_count: number;
  total_hires: number;
}

/**
 * Метрики распределения уверенности с бэкенда
 */
interface RankingConfidenceMetrics {
  high_confidence_count: number;
  medium_confidence_count: number;
  low_confidence_count: number;
  avg_confidence_score: number;
  confidence_accuracy_correlation?: number;
}

/**
 * Тренд производительности ранжирования
 */
interface RankingPerformanceTrend {
  period: string;
  success_rate: number;
  feedback_rate: number;
  avg_confidence: number;
  total_recommendations: number;
}

/**
 * Ответ с метриками точности ранжирования с бэкенда
 */
interface RankingMetricsResponse {
  feedback_conversion: FeedbackConversionMetrics;
  top_n_performance: TopNRecommendationMetrics;
  confidence_distribution: RankingConfidenceMetrics;
  trends?: RankingPerformanceTrend[];
  period_start?: string;
  period_end?: string;
  total_vacancies_analyzed: number;
}

/**
 * Свойства компонента RankingAccuracyMetrics
 */
interface RankingAccuracyMetricsProps {
  /** URL API endpoint для метрик ранжирования */
  apiUrl?: string;
  /** Опциональный фильтр начальной даты */
  startDate?: string;
  /** Опциональный фильтр конечной даты */
  endDate?: string;
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
 * Получить цвет для коэффициента успеха
 */
const getSuccessColor = (rate: number): 'success' | 'warning' | 'error' => {
  if (rate >= 0.7) return 'success';
  if (rate >= 0.5) return 'warning';
  return 'error';
};

/**
 * Получить цвет для уверенности
 */
const getConfidenceColor = (score: number): string => {
  if (score >= 0.8) return 'success.main';
  if (score >= 0.5) return 'warning.main';
  return 'error.main';
};

/**
 * Компонент RankingAccuracyMetrics
 *
 * Отображает метрики точности ML-рекомендаций включая:
 * - Коэффициенты конверсии обратной связи (положительная/отрицательная)
 * - Показатели успеха top-N рекомендаций (top-1, top-3, top-5, top-10)
 * - Распределение уверенности ранжирования
 * - Тренды производительности
 *
 * @example
 * ```tsx
 * <RankingAccuracyMetrics />
 * ```
 *
 * @example
 * ```tsx
 * <RankingAccuracyMetrics startDate="2024-01-01" endDate="2024-12-31" />
 * ```
 */
const RankingAccuracyMetrics: React.FC<RankingAccuracyMetricsProps> = ({
  apiUrl = '/api/analytics/ranking-accuracy',
  startDate,
  endDate,
}) => {
  // Состояния для загрузки, ошибки, метрик и автообновления
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<RankingMetricsResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  /**
   * Загрузка метрик ранжирования с бэкенда
   */
  const fetchMetrics = async () => {
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

      const response = await axios.get<RankingMetricsResponse>(apiUrl, { params });
      setMetrics(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load ranking metrics data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Initial fetch on mount and when date range changes
   */
  useEffect(() => {
    fetchMetrics();
  }, [apiUrl, startDate, endDate]);

  /**
   * Auto-refresh every 60 seconds when enabled
   */
  useEffect(() => {
    if (!autoRefreshEnabled) {
      return;
    }

    const interval = setInterval(() => {
      fetchMetrics();
    }, 60000); // 60 seconds

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, apiUrl, startDate, endDate]);

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = () => {
    setAutoRefreshEnabled((prev) => !prev);
  };

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
          Loading ranking accuracy metrics...
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
          <Button color="inherit" size="small" onClick={fetchMetrics} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
        sx={{ mb: 3 }}
      >
        <AlertTitle>Error Loading Ranking Metrics</AlertTitle>
        {error}
      </Alert>
    );
  }

  /**
   * Render empty state
   */
  if (!metrics) {
    return (
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>No Ranking Data Available</AlertTitle>
        No ranking accuracy metrics have been collected yet. Data will appear after candidates are
        ranked and feedback is received.
      </Alert>
    );
  }

  const { feedback_conversion, top_n_performance, confidence_distribution, total_vacancies_analyzed } =
    metrics;

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
              Ranking Accuracy Metrics
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              ML recommendation performance and feedback conversion analysis
            </Typography>
            <Chip
              label={`${formatNumber(total_vacancies_analyzed)} vacancies analyzed`}
              size="small"
              sx={{ mt: 1, bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
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
              onClick={fetchMetrics}
              startIcon={<RefreshIcon />}
              sx={{ borderColor: 'rgba(255,255,255,0.5)', color: 'white' }}
            >
              Refresh
            </Button>
          </Stack>
        </Box>
      </Paper>

      {/* Feedback Conversion Section */}
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <ChartIcon color="primary" />
        Feedback Conversion
      </Typography>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <Typography variant="h4" fontWeight="bold" color="primary">
                  {formatNumber(feedback_conversion.total_recommendations)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Recommendations
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <Typography variant="h4" fontWeight="bold" color="info.main">
                  {formatPercent(feedback_conversion.feedback_rate)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Feedback Rate
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ({formatNumber(feedback_conversion.recommendations_with_feedback)} responses)
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <Stack direction="row" spacing={1} justifyContent="center" alignItems="center">
                  <ThumbUpIcon color="success" />
                  <Typography variant="h5" fontWeight="bold" color="success.main">
                    {formatPercent(feedback_conversion.positive_feedback_rate)}
                  </Typography>
                </Stack>
                <Typography variant="body2" color="text.secondary">
                  Positive Feedback
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ({formatNumber(feedback_conversion.positive_feedback_count)} approvals)
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <Stack direction="row" spacing={1} justifyContent="center" alignItems="center">
                  <ThumbDownIcon color="error" />
                  <Typography variant="h5" fontWeight="bold" color="error.main">
                    {formatPercent(1 - feedback_conversion.positive_feedback_rate)}
                  </Typography>
                </Stack>
                <Typography variant="body2" color="text.secondary">
                  Negative Feedback
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ({formatNumber(feedback_conversion.negative_feedback_count)} rejections)
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Top-N Performance Section */}
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TrophyIcon color="primary" />
        Top-N Recommendation Success Rates
      </Typography>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            {/* Top-1 */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  bgcolor: 'grey.50',
                  borderRadius: 2,
                  textAlign: 'center',
                }}
              >
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Top 1 Candidate
                </Typography>
                <Typography
                  variant="h3"
                  fontWeight="bold"
                  color={getSuccessColor(top_n_performance.top_1_success_rate) + '.main'}
                >
                  {formatPercent(top_n_performance.top_1_success_rate)}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {formatNumber(top_n_performance.top_1_hired_count)} hired from top-1
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={top_n_performance.top_1_success_rate * 100}
                  color={getSuccessColor(top_n_performance.top_1_success_rate)}
                  sx={{ mt: 2, height: 8, borderRadius: 4 }}
                />
              </Paper>
            </Grid>

            {/* Top-3 */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  bgcolor: 'grey.50',
                  borderRadius: 2,
                  textAlign: 'center',
                }}
              >
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Top 3 Candidates
                </Typography>
                <Typography
                  variant="h3"
                  fontWeight="bold"
                  color={getSuccessColor(top_n_performance.top_3_success_rate) + '.main'}
                >
                  {formatPercent(top_n_performance.top_3_success_rate)}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Success within top 3
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={top_n_performance.top_3_success_rate * 100}
                  color={getSuccessColor(top_n_performance.top_3_success_rate)}
                  sx={{ mt: 2, height: 8, borderRadius: 4 }}
                />
              </Paper>
            </Grid>

            {/* Top-5 */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  bgcolor: 'grey.50',
                  borderRadius: 2,
                  textAlign: 'center',
                }}
              >
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Top 5 Candidates
                </Typography>
                <Typography
                  variant="h3"
                  fontWeight="bold"
                  color={getSuccessColor(top_n_performance.top_5_success_rate) + '.main'}
                >
                  {formatPercent(top_n_performance.top_5_success_rate)}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {formatNumber(top_n_performance.top_5_hired_count)} hired from top-5
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={top_n_performance.top_5_success_rate * 100}
                  color={getSuccessColor(top_n_performance.top_5_success_rate)}
                  sx={{ mt: 2, height: 8, borderRadius: 4 }}
                />
              </Paper>
            </Grid>

            {/* Top-10 */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  bgcolor: 'grey.50',
                  borderRadius: 2,
                  textAlign: 'center',
                }}
              >
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Top 10 Candidates
                </Typography>
                <Typography
                  variant="h3"
                  fontWeight="bold"
                  color={getSuccessColor(top_n_performance.top_10_success_rate) + '.main'}
                >
                  {formatPercent(top_n_performance.top_10_success_rate)}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {formatNumber(top_n_performance.top_10_hired_count)} hired from top-10
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={top_n_performance.top_10_success_rate * 100}
                  color={getSuccessColor(top_n_performance.top_10_success_rate)}
                  sx={{ mt: 2, height: 8, borderRadius: 4 }}
                />
              </Paper>
            </Grid>
          </Grid>

          {/* Total Hires Summary */}
          <Divider sx={{ my: 2 }} />
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Total hires in period:
            </Typography>
            <Chip
              icon={<StarsIcon />}
              label={formatNumber(top_n_performance.total_hires)}
              color="primary"
              variant="outlined"
            />
          </Box>
        </CardContent>
      </Card>

      {/* Confidence Distribution Section */}
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <BrainIcon color="primary" />
        Ranking Confidence Distribution
      </Typography>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            {/* Average Confidence */}
            <Grid item xs={12} md={4}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Average Confidence Score
                </Typography>
                <Typography
                  variant="h2"
                  fontWeight="bold"
                  sx={{ color: getConfidenceColor(confidence_distribution.avg_confidence_score) }}
                >
                  {formatPercent(confidence_distribution.avg_confidence_score)}
                </Typography>
                {confidence_distribution.confidence_accuracy_correlation !== undefined && (
                  <Typography variant="caption" color="text.secondary">
                    Correlation with success:{' '}
                    {(confidence_distribution.confidence_accuracy_correlation * 100).toFixed(0)}%
                  </Typography>
                )}
              </Box>
            </Grid>

            {/* Confidence Breakdown */}
            <Grid item xs={12} md={8}>
              <Box sx={{ p: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Confidence Level Breakdown
                </Typography>

                {/* High Confidence */}
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2">High Confidence (&gt;80%)</Typography>
                    <Typography variant="body2" fontWeight="bold" color="success.main">
                      {formatNumber(confidence_distribution.high_confidence_count)}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={
                      (confidence_distribution.high_confidence_count /
                        (confidence_distribution.high_confidence_count +
                          confidence_distribution.medium_confidence_count +
                          confidence_distribution.low_confidence_count)) *
                      100
                    }
                    color="success"
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>

                {/* Medium Confidence */}
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2">Medium Confidence (50-80%)</Typography>
                    <Typography variant="body2" fontWeight="bold" color="warning.main">
                      {formatNumber(confidence_distribution.medium_confidence_count)}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={
                      (confidence_distribution.medium_confidence_count /
                        (confidence_distribution.high_confidence_count +
                          confidence_distribution.medium_confidence_count +
                          confidence_distribution.low_confidence_count)) *
                      100
                    }
                    color="warning"
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>

                {/* Low Confidence */}
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2">Low Confidence (&lt;50%)</Typography>
                    <Typography variant="body2" fontWeight="bold" color="error.main">
                      {formatNumber(confidence_distribution.low_confidence_count)}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={
                      (confidence_distribution.low_confidence_count /
                        (confidence_distribution.high_confidence_count +
                          confidence_distribution.medium_confidence_count +
                          confidence_distribution.low_confidence_count)) *
                      100
                    }
                    color="error"
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Insights Card */}
      <Card sx={{ bgcolor: 'grey.50' }}>
        <CardContent>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Key Insights
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Chip
              icon={<TrendingUpIcon />}
              label={`Top-5 recommendation captures ${formatPercent(top_n_performance.top_5_success_rate)} of hires`}
              color="primary"
              variant="outlined"
              size="small"
            />
            <Chip
              icon={<ThumbUpIcon />}
              label={`${formatPercent(feedback_conversion.positive_feedback_rate)} positive feedback rate`}
              color="success"
              variant="outlined"
              size="small"
            />
            <Chip
              icon={<BrainIcon />}
              label={`Average confidence: ${formatPercent(confidence_distribution.avg_confidence_score)}`}
              color="info"
              variant="outlined"
              size="small"
            />
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
};

export default RankingAccuracyMetrics;
