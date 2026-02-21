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
} from '@mui/material';
// Иконки Material UI
import {
  Refresh as RefreshIcon,
  Psychology as BrainIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  TrendingUp as TrendingUpIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

/**
 * Интервал уверенности с бэкенда
 */
interface ConfidenceInterval {
  lower: number;
  upper: number;
  confidence_level: number;
}

/**
 * Распределение уверенности с бэкенда
 */
interface ConfidenceDistribution {
  high_confidence_count: number;
  medium_confidence_count: number;
  low_confidence_count: number;
}

/**
 * Ответ API метрик уверенности с бэкенда
 */
interface ConfidenceMetricsResponse {
  average_confidence: number;
  confidence_interval: ConfidenceInterval;
  distribution: ConfidenceDistribution;
  confidence_accuracy_correlation: number;
}

/**
 * Свойства компонента ConfidenceScoreDisplay
 */
interface ConfidenceScoreDisplayProps {
  /** URL API endpoint для метрик уверенности */
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
 * Получить цвет для уверенности
 */
const getConfidenceColor = (score: number): 'success' | 'warning' | 'error' => {
  if (score >= 0.8) return 'success';
  if (score >= 0.5) return 'warning';
  return 'error';
};

/**
 * Получить цвет для уверенности в формате строки для sx prop
 */
const getConfidenceColorString = (score: number): string => {
  if (score >= 0.8) return 'success.main';
  if (score >= 0.5) return 'warning.main';
  return 'error.main';
};

/**
 * Компонент ConfidenceScoreDisplay
 *
 * Отображает метрики уверенности ML-модели включая:
 * - Среднюю уверенность с интервалом неопределенности
 * - Распределение уверенности по уровням (высокая/средняя/низкая)
 * - Корреляцию уверенности с точностью
 *
 * @example
 * ```tsx
 * <ConfidenceScoreDisplay />
 * ```
 *
 * @example
 * ```tsx
 * <ConfidenceScoreDisplay startDate="2024-01-01" endDate="2024-12-31" />
 * ```
 */
const ConfidenceScoreDisplay: React.FC<ConfidenceScoreDisplayProps> = ({
  apiUrl = '/api/analytics/ai-explainability/confidence',
  startDate,
  endDate,
}) => {
  // Состояния для загрузки, ошибки, метрик и автообновления
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<ConfidenceMetricsResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  /**
   * Загрузка метрик уверенности с бэкенда
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

      const response = await axios.get<ConfidenceMetricsResponse>(apiUrl, { params });
      setMetrics(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load confidence metrics data';
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
          Loading confidence metrics...
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
        <AlertTitle>Error Loading Confidence Metrics</AlertTitle>
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
        <AlertTitle>No Confidence Data Available</AlertTitle>
        Confidence metrics will appear after the ML model is trained and candidates are ranked.
      </Alert>
    );
  }

  const { average_confidence, confidence_interval, distribution, confidence_accuracy_correlation } =
    metrics;

  // Calculate total predictions for distribution percentages
  const totalPredictions =
    distribution.high_confidence_count +
    distribution.medium_confidence_count +
    distribution.low_confidence_count;

  // Calculate uncertainty interval display value
  const uncertaintyValue = (confidence_interval.upper - average_confidence) * 100;

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
              Model Confidence Scores
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              ML prediction confidence with uncertainty quantification
            </Typography>
            <Chip
              icon={<BrainIcon />}
              label={`Confidence Level: ${formatPercent(confidence_interval.confidence_level)}`}
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

      {/* Main Confidence Display */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            {/* Average Confidence with Uncertainty */}
            <Grid item xs={12} md={4}>
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  bgcolor: 'grey.50',
                  borderRadius: 2,
                  textAlign: 'center',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                }}
              >
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Average Confidence
                </Typography>
                <Typography
                  variant="h2"
                  fontWeight="bold"
                  sx={{ color: getConfidenceColorString(average_confidence) }}
                >
                  {formatPercent(average_confidence)}
                </Typography>
                <Typography variant="h6" color="text.secondary" sx={{ mt: 1 }}>
                  ± {uncertaintyValue.toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                  Range: {formatPercent(confidence_interval.lower)} -{' '}
                  {formatPercent(confidence_interval.upper)}
                </Typography>
              </Paper>
            </Grid>

            {/* Confidence Distribution */}
            <Grid item xs={12} md={8}>
              <Box sx={{ p: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Confidence Level Distribution
                </Typography>

                {/* High Confidence */}
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2">High Confidence (&gt;80%)</Typography>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography variant="body2" fontWeight="bold" color="success.main">
                        {formatNumber(distribution.high_confidence_count)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ({formatPercent(distribution.high_confidence_count / totalPredictions)})
                      </Typography>
                    </Stack>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={(distribution.high_confidence_count / totalPredictions) * 100}
                    color="success"
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>

                {/* Medium Confidence */}
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2">Medium Confidence (50-80%)</Typography>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography variant="body2" fontWeight="bold" color="warning.main">
                        {formatNumber(distribution.medium_confidence_count)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ({formatPercent(distribution.medium_confidence_count / totalPredictions)})
                      </Typography>
                    </Stack>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={(distribution.medium_confidence_count / totalPredictions) * 100}
                    color="warning"
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>

                {/* Low Confidence */}
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2">Low Confidence (&lt;50%)</Typography>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography variant="body2" fontWeight="bold" color="error.main">
                        {formatNumber(distribution.low_confidence_count)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ({formatPercent(distribution.low_confidence_count / totalPredictions)})
                      </Typography>
                    </Stack>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={(distribution.low_confidence_count / totalPredictions) * 100}
                    color="error"
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Accuracy Correlation */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <TrendingUpIcon
                  fontSize="large"
                  color={confidence_accuracy_correlation >= 0.5 ? 'success' : 'warning'}
                />
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Confidence-Accuracy Correlation
                  </Typography>
                  <Typography
                    variant="h4"
                    fontWeight="bold"
                    color={confidence_accuracy_correlation >= 0.5 ? 'success.main' : 'warning.main'}
                  >
                    {formatPercent(confidence_accuracy_correlation)}
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ textAlign: { xs: 'left', md: 'right' } }}>
                <Typography variant="body2" color="text.secondary">
                  Total Predictions Analyzed
                </Typography>
                <Typography variant="h5" fontWeight="bold" color="primary">
                  {formatNumber(totalPredictions)}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card sx={{ bgcolor: 'grey.50' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <InfoIcon color="info" />
            <Box>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                About Confidence Scores
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Confidence scores represent the model's certainty in its predictions. Higher
                confidence indicates more reliable recommendations. The uncertainty interval shows
                the range within which the true confidence likely falls (with{' '}
                {formatPercent(confidence_interval.confidence_level)} certainty).
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ConfidenceScoreDisplay;
