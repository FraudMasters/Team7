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
  TrendingDown as TrendingDownIcon,
  CheckCircle as CheckIcon,
  Description as DescriptionIcon,
  Upload as UploadIcon,
  Person as PersonIcon,
  Work as WorkIcon,
  School as InterviewIcon,
  Celebration as HiredIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
} from '@mui/icons-material';

/**
 * Интерфейс этапа funnel с бэкенда
 */
interface FunnelStage {
  stage_name: string;
  count: number;
  conversion_rate: number;
}

/**
 * Ответ с метриками funnel с бэкенда
 */
interface FunnelMetricsResponse {
  stages: FunnelStage[];
  total_resumes: number;
  overall_hire_rate: number;
}

/**
 * Свойства компонента FunnelVisualization
 */
interface FunnelVisualizationProps {
  /** URL API endpoint для метрик funnel */
  apiUrl?: string;
  /** Опциональный фильтр начальной даты */
  startDate?: string;
  /** Опциональный фильтр конечной даты */
  endDate?: string;
}

/**
 * Форматирование имени этапа для отображения
 */
const formatStageName = (stageName: string): string => {
  const nameMap: Record<string, string> = {
    resumes_uploaded: 'Resumes Uploaded',
    resumes_processed: 'Resumes Processed',
    candidates_matched: 'Candidates Matched',
    candidates_shortlisted: 'Candidates Shortlisted',
    candidates_interviewed: 'Candidates Interviewed',
    candidates_hired: 'Candidates Hired',
  };
  return nameMap[stageName] || stageName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
};

/**
 * Получить иконку для этапа
 */
const getStageIcon = (stageName: string) => {
  const iconMap: Record<string, React.ReactElement> = {
    resumes_uploaded: <UploadIcon />,
    resumes_processed: <DescriptionIcon />,
    candidates_matched: <PersonIcon />,
    candidates_shortlisted: <WorkIcon />,
    candidates_interviewed: <InterviewIcon />,
    candidates_hired: <HiredIcon />,
  };
  return iconMap[stageName] || <CheckIcon />;
};

/**
 * Получить цвет для коэффициента конверсии
 */
const getConversionColor = (rate: number): string => {
  if (rate >= 0.7) return 'success.main';
  if (rate >= 0.5) return 'warning.main';
  return 'error.main';
};

/**
 * Компонент FunnelVisualization
 *
 * Отображает визуализацию recruitment funnel включая:
 * - Прогресс кандидатов через каждый этап пайплайна
 * - Коэффициенты конверсии между этапами
 * - Общий коэффициент найма
 * - Визуальное представление отсева кандидатов
 *
 * @example
 * ```tsx
 * <FunnelVisualization />
 * ```
 *
 * @example
 * ```tsx
 * <FunnelVisualization startDate="2024-01-01" endDate="2024-12-31" />
 * ```
 */
const FunnelVisualization: React.FC<FunnelVisualizationProps> = ({
  apiUrl = '/api/analytics/funnel',
  startDate,
  endDate,
}) => {
  // Состояния для загрузки, ошибки, данных funnel и автообновления
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [funnelData, setFunnelData] = useState<FunnelMetricsResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  /**
   * Загрузка метрик funnel с бэкенда
   */
  const fetchFunnelData = async () => {
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

      const response = await axios.get<FunnelMetricsResponse>(apiUrl, { params });
      setFunnelData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load funnel data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Initial fetch on mount and when date range changes
   */
  useEffect(() => {
    fetchFunnelData();
  }, [apiUrl, startDate, endDate]);

  /**
   * Auto-refresh every 60 seconds when enabled
   */
  useEffect(() => {
    if (!autoRefreshEnabled) {
      return;
    }

    const interval = setInterval(() => {
      fetchFunnelData();
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
          Loading funnel data...
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
          <Button color="inherit" onClick={fetchFunnelData} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Funnel Data</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!funnelData) {
    return null;
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h5" fontWeight={600}>
              Recruitment Funnel
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Track candidate progression through the hiring pipeline
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant={autoRefreshEnabled ? 'contained' : 'outlined'}
              startIcon={autoRefreshEnabled ? <PauseIcon /> : <PlayIcon />}
              onClick={toggleAutoRefresh}
              size="small"
              color={autoRefreshEnabled ? 'primary' : 'default'}
            >
              {autoRefreshEnabled ? 'Auto-refresh' : 'Paused'}
            </Button>
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchFunnelData} size="small">
              Refresh
            </Button>
          </Box>
        </Box>

        {/* Overall Metrics */}
        <Box
          sx={{
            display: 'flex',
            gap: 3,
            mb: 4,
            flexWrap: 'wrap',
          }}
        >
          <Box sx={{ flex: '1 1 200px' }}>
            <Typography variant="caption" color="text.secondary">
              Total Resumes Uploaded
            </Typography>
            <Typography variant="h4" fontWeight={700} color="primary.main">
              {funnelData.total_resumes.toLocaleString()}
            </Typography>
          </Box>
          <Box sx={{ flex: '1 1 200px' }}>
            <Typography variant="caption" color="text.secondary">
              Overall Hire Rate
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography
                variant="h4"
                fontWeight={700}
                color={funnelData.overall_hire_rate >= 0.05 ? 'success.main' : 'warning.main'}
              >
                {(funnelData.overall_hire_rate * 100).toFixed(2)}%
              </Typography>
              {funnelData.overall_hire_rate >= 0.05 ? (
                <CheckIcon color="success" fontSize="small" />
              ) : (
                <TrendingDownIcon color="warning" fontSize="small" />
              )}
            </Box>
          </Box>
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Funnel Stages */}
        <Stack spacing={2}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Pipeline Stages
          </Typography>

          {funnelData.stages.map((stage, index) => {
            const stageWidth = stage.count / funnelData.total_resumes;
            const previousStage = index > 0 ? funnelData.stages[index - 1] : null;
            const isLastStage = index === funnelData.stages.length - 1;

            return (
              <Card
                key={stage.stage_name}
                variant="outlined"
                sx={{
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateX(4px)',
                    boxShadow: 2,
                  },
                }}
              >
                <CardContent sx={{ py: 2 }}>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      mb: 1.5,
                    }}
                  >
                    {/* Stage Name and Icon */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flex: 1 }}>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: 36,
                          height: 36,
                          borderRadius: 1,
                          bgcolor: isLastStage ? 'success.light' : 'primary.light',
                          color: isLastStage ? 'success.dark' : 'primary.dark',
                        }}
                      >
                        {getStageIcon(stage.stage_name)}
                      </Box>
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {formatStageName(stage.stage_name)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Stage {index + 1} of {funnelData.stages.length}
                        </Typography>
                      </Box>
                    </Box>

                    {/* Count and Conversion Rate */}
                    <Box sx={{ textAlign: 'right', minWidth: 150 }}>
                      <Typography variant="h5" fontWeight={700} color="primary.main">
                        {stage.count.toLocaleString()}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                        {index === 0 ? (
                          <Chip
                            label="Starting Point"
                            size="small"
                            color="info"
                            variant="outlined"
                            sx={{ height: 20, fontSize: '0.7rem' }}
                          />
                        ) : (
                          <>
                            <Typography variant="caption" color="text.secondary">
                              {(stage.conversion_rate * 100).toFixed(1)}% conversion
                            </Typography>
                            <Chip
                              label={previousStage ? `-${((1 - stage.conversion_rate) * 100).toFixed(1)}%` : ''}
                              size="small"
                              color={stage.conversion_rate >= 0.5 ? 'success' : 'warning'}
                              variant="outlined"
                              sx={{ height: 20, fontSize: '0.7rem' }}
                            />
                          </>
                        )}
                      </Box>
                    </Box>
                  </Box>

                  {/* Visual Funnel Bar */}
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Stage Width: {(stageWidth * 100).toFixed(1)}% of total
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={stageWidth * 100}
                      sx={{
                        height: 12,
                        borderRadius: 1,
                        bgcolor: 'action.hover',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: isLastStage ? 'success.main' : getConversionColor(stage.conversion_rate),
                        },
                      }}
                    />
                  </Box>

                  {/* Drop-off Information (if not first stage) */}
                  {index > 0 && previousStage && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        {(previousStage.count - stage.count).toLocaleString()} candidates dropped from previous stage
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </Stack>

        {/* Insights */}
        {funnelData.stages.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Pipeline Insights
            </Typography>
            <Stack spacing={1}>
              {funnelData.stages.map((stage, index) => {
                if (index === 0) return null;

                const previousStage = funnelData.stages[index - 1];
                const dropOffRate = 1 - stage.conversion_rate;

                return (
                  dropOffRate > 0.3 && previousStage && (
                    <Typography key={stage.stage_name} variant="body2" color="text.secondary">
                      <strong>{formatStageName(stage.stage_name)}:</strong> {(dropOffRate * 100).toFixed(1)}% drop-off
                      from {formatStageName(previousStage.stage_name)}
                    </Typography>
                  )
                );
              })}
              {funnelData.stages.every((stage, index) => index === 0 || 1 - stage.conversion_rate <= 0.3) && (
                <Typography variant="body2" color="success.main">
                  <CheckIcon fontSize="inherit" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                  Pipeline shows healthy conversion rates across all stages
                </Typography>
              )}
            </Stack>
          </Box>
        )}
      </Paper>
    </Stack>
  );
};

export default FunnelVisualization;
