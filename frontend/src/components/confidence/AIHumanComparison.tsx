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
  Divider,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
} from '@mui/material';
// Иконки Material UI
import {
  Refresh as RefreshIcon,
  Psychology as AIIcon,
  Person as HumanIcon,
  CheckCircle as AgreeIcon,
  Cancel as DisagreeIcon,
  Timer as TimerIcon,
  TrendingUp as EfficiencyIcon,
  Lightbulb as RecommendationIcon,
  BarChart as CorrelationIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

/**
 * Метрики согласованности между AI и человеком
 */
interface AgreementMetrics {
  agreement_rate: number;
  total_comparisons: number;
  ai_correct_count: number;
  human_override_count: number;
  human_override_correct: number;
}

/**
 * Метрики эффективности AI
 */
interface EfficiencyMetrics {
  avg_time_saved_hours: number;
  total_time_saved_hours: number;
  automation_rate: number;
  manual_review_rate: number;
}

/**
 * Корреляция между уверенностью AI и точностью
 */
interface ConfidenceCorrelation {
  high_confidence_accuracy: number;
  medium_confidence_accuracy: number;
  low_confidence_accuracy: number;
  correlation_coefficient: number;
}

/**
 * Ответ API с метриками сравнения AI и человека
 */
interface AIHumanComparisonResponse {
  agreement: AgreementMetrics;
  efficiency: EfficiencyMetrics;
  confidence_correlation: ConfidenceCorrelation;
  recommendations: string[];
}

/**
 * Свойства компонента AIHumanComparison
 */
interface AIHumanComparisonProps {
  /** URL API endpoint для получения данных сравнения */
  apiUrl?: string;
  /** Опциональная начальная дата для фильтрации (формат ISO 8601) */
  startDate?: string;
  /** Опциональная конечная дата для фильтрации (формат ISO 8601) */
  endDate?: string;
  /** ID вакансии для фильтрации */
  vacancyId?: string;
  /** Включить автоматическое обновление данных */
  autoRefresh?: boolean;
}

/**
 * Форматирование процента для отображения
 */
const formatPercent = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Форматирование часов для отображения
 */
const formatHours = (hours: number): string => {
  if (hours < 1) {
    return `${Math.round(hours * 60)} мин`;
  }
  return `${hours.toFixed(1)} ч`;
};

/**
 * Получение конфигурации цвета для rate согласованности
 */
const getAgreementRateConfig = (rate: number) => {
  const percentage = rate * 100;
  if (percentage >= 85) {
    return {
      color: 'success' as const,
      label: 'Отлично',
      bgColor: 'success.main',
    };
  }
  if (percentage >= 70) {
    return {
      color: 'warning' as const,
      label: 'Хорошо',
      bgColor: 'warning.main',
    };
  }
  return {
    color: 'error' as const,
    label: 'Требует внимания',
    bgColor: 'error.main',
  };
};

/**
 * Компонент AIHumanComparison
 *
 * Отображает сравнение решений AI и человека-рекрутера:
 * - Процент согласованности между AI и рекрутером
 * - Метрики эффективности (экономия времени, автоматизация)
 * - Корреляция между уверенностью AI и точностью
 * - Случаи несогласия для ревью
 * - Рекомендации по оптимальному сотрудничеству AI-человек
 *
 * @example
 * ```tsx
 * <AIHumanComparison />
 * ```
 *
 * @example
 * ```tsx
 * <AIHumanComparison
 *   startDate="2024-01-01"
 *   endDate="2024-12-31"
 *   vacancyId="vacancy-uuid-123"
 * />
 * ```
 */
const AIHumanComparison: React.FC<AIHumanComparisonProps> = ({
  apiUrl = '/api/confidence-dashboard',
  startDate,
  endDate,
  vacancyId,
}) => {
  // Состояния для загрузки, ошибки и данных
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AIHumanComparisonResponse | null>(null);

  /**
   * Загрузка данных сравнения AI и человека с бэкенда
   */
  const fetchComparison = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (vacancyId) params.vacancy_id = vacancyId;

      const response = await axios.get<AIHumanComparisonResponse>(
        `${apiUrl}/ai-human-comparison`,
        { params }
      );
      setData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load AI-human comparison data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, startDate, endDate, vacancyId]);

  useEffect(() => {
    fetchComparison();
  }, [fetchComparison]);

  /**
   * Состояние загрузки
   */
  if (loading) {
    return (
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
          <Stack spacing={2} alignItems="center">
            <CircularProgress size={48} />
            <Typography variant="body2" color="text.secondary">
              Загрузка данных сравнения AI и рекрутеров...
            </Typography>
          </Stack>
        </Box>
      </Paper>
    );
  }

  /**
   * Состояние ошибки
   */
  if (error) {
    return (
      <Paper sx={{ p: 3 }}>
        <Alert severity="error">
          <AlertTitle>Ошибка загрузки данных</AlertTitle>
          {error}
          <Box mt={2}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchComparison}
              size="small"
            >
              Повторить попытку
            </Button>
          </Box>
        </Alert>
      </Paper>
    );
  }

  /**
   * Нет данных
   */
  if (!data) {
    return (
      <Paper sx={{ p: 3 }}>
        <Alert severity="info">
          <AlertTitle>Нет данных</AlertTitle>
          Данные сравнения AI и рекрутеров пока недоступны.
        </Alert>
      </Paper>
    );
  }

  const { agreement, efficiency, confidence_correlation, recommendations } = data;
  const agreementConfig = getAgreementRateConfig(agreement.agreement_rate);
  const disagreementCount = agreement.human_override_count;
  const disagreementRate = agreement.total_comparisons > 0
    ? (disagreementCount / agreement.total_comparisons)
    : 0;

  return (
    <Paper sx={{ p: 3 }}>
      {/* Заголовок */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 48,
              height: 48,
              borderRadius: '50%',
              bgcolor: 'primary.light',
              color: 'primary.contrastText',
            }}
          >
            <AIIcon />
          </Box>
          <Box>
            <Typography variant="h5" fontWeight="bold">
              AI vs Рекрутер
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Сравнение решений AI и рекрутеров
            </Typography>
          </Box>
        </Stack>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchComparison}
          size="small"
        >
          Обновить
        </Button>
      </Box>

      {/* Главная метрика согласованности */}
      <Card
        sx={{
          mb: 3,
          bgcolor: `${agreementConfig.bgColor}`,
          color: 'white',
        }}
      >
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <Stack spacing={1}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <AgreeIcon fontSize="large" />
                  <Typography variant="h3" fontWeight="bold">
                    {formatPercent(agreement.agreement_rate)}
                  </Typography>
                </Stack>
                <Typography variant="h6">Согласованность решений</Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  AI и рекрутеры соглашаются в {agreement.ai_correct_count} из{' '}
                  {agreement.total_comparisons} случаев
                </Typography>
              </Stack>
            </Grid>
            <Grid item xs={12} md={6}>
              <Stack spacing={1}>
                <Chip
                  label={agreementConfig.label}
                  size="small"
                  sx={{
                    alignSelf: 'flex-start',
                    bgcolor: 'rgba(255, 255, 255, 0.2)',
                    color: 'white',
                    fontWeight: 'bold',
                  }}
                />
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Всего сравнений: {agreement.total_comparisons}
                </Typography>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Метрики несогласия (disagreement cases) */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <DisagreeIcon color="warning" />
                  <Typography variant="h6" fontWeight="bold">
                    Случаи несогласия
                  </Typography>
                  <Tooltip title="Случаи, когда рекрутер изменил решение AI">
                    <InfoIcon fontSize="small" color="action" />
                  </Tooltip>
                </Stack>

                <Box>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2" color="text.secondary">
                      Переопределений рекрутером
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {disagreementCount} ({formatPercent(disagreementRate)})
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={disagreementRate * 100}
                    color="warning"
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>

                <Divider />

                <Stack spacing={1}>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2" color="text.secondary">
                      Переопределений было верно:
                    </Typography>
                    <Chip
                      label={`${agreement.human_override_correct} из ${agreement.human_override_count}`}
                      size="small"
                      color="success"
                    />
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2" color="text.secondary">
                      AI был прав:
                    </Typography>
                    <Chip
                      label={`${agreement.ai_correct_count} случаев`}
                      size="small"
                      color="primary"
                    />
                  </Box>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Метрики эффективности */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <EfficiencyIcon color="success" />
                  <Typography variant="h6" fontWeight="bold">
                    Эффективность AI
                  </Typography>
                </Stack>

                <Stack spacing={2}>
                  <Box>
                    <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                      <TimerIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">
                        Экономия времени
                      </Typography>
                    </Stack>
                    <Typography variant="h5" fontWeight="bold" color="success.main">
                      {formatHours(efficiency.avg_time_saved_hours)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      в среднем на ранжирование
                    </Typography>
                    <Typography variant="body2" color="text.secondary" mt={0.5}>
                      Всего сэкономлено: {formatHours(efficiency.total_time_saved_hours)}
                    </Typography>
                  </Box>

                  <Divider />

                  <Box>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2" color="text.secondary">
                        Автоматизация
                      </Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {formatPercent(efficiency.automation_rate)}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={efficiency.automation_rate * 100}
                      color="success"
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>

                  <Box>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2" color="text.secondary">
                        Требует ручного ревью
                      </Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {formatPercent(efficiency.manual_review_rate)}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={efficiency.manual_review_rate * 100}
                      color="warning"
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Корреляция уверенности и точности */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <CorrelationIcon color="primary" />
                  <Typography variant="h6" fontWeight="bold">
                    Корреляция уверенности и точности
                  </Typography>
                </Stack>

                <Stack spacing={2}>
                  <Box>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2" color="text.secondary">
                        Высокая уверенность (≥80%)
                      </Typography>
                      <Chip
                        label={formatPercent(confidence_correlation.high_confidence_accuracy)}
                        size="small"
                        color="success"
                      />
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={confidence_correlation.high_confidence_accuracy * 100}
                      color="success"
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>

                  <Box>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2" color="text.secondary">
                        Средняя уверенность (50-80%)
                      </Typography>
                      <Chip
                        label={formatPercent(confidence_correlation.medium_confidence_accuracy)}
                        size="small"
                        color="warning"
                      />
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={confidence_correlation.medium_confidence_accuracy * 100}
                      color="warning"
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>

                  <Box>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2" color="text.secondary">
                        Низкая уверенность (&lt;50%)
                      </Typography>
                      <Chip
                        label={formatPercent(confidence_correlation.low_confidence_accuracy)}
                        size="small"
                        color="error"
                      />
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={confidence_correlation.low_confidence_accuracy * 100}
                      color="error"
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>

                  <Divider />

                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Коэффициент корреляции
                    </Typography>
                    <Typography variant="h5" fontWeight="bold" color="primary.main">
                      {confidence_correlation.correlation_coefficient.toFixed(2)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {confidence_correlation.correlation_coefficient >= 0.8
                        ? 'Очень сильная корреляция'
                        : confidence_correlation.correlation_coefficient >= 0.6
                        ? 'Сильная корреляция'
                        : 'Умеренная корреляция'}
                    </Typography>
                  </Box>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Рекомендации */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <RecommendationIcon color="info" />
                  <Typography variant="h6" fontWeight="bold">
                    Рекомендации
                  </Typography>
                </Stack>

                <List dense>
                  {recommendations.map((recommendation, index) => (
                    <ListItem key={index} disablePadding sx={{ mb: 1 }}>
                      <ListItemIcon>
                        <Chip
                          label={index + 1}
                          size="small"
                          color="primary"
                          sx={{ width: 24, height: 24, fontSize: '0.75rem' }}
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={recommendation}
                        primaryTypographyProps={{
                          variant: 'body2',
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default AIHumanComparison;
