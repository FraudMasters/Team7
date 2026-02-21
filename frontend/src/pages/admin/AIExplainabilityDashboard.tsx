// React хуки для управления состоянием
import React, { useState, useEffect, useCallback } from 'react';
// HTTP клиент для запросов к API
import axios from 'axios';
// Компоненты Material UI для создания интерфейса
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
  AlertTitle,
  Stack,
  Chip,
  Divider,
  ToggleButton,
  ToggleButtonGroup,
  TextField,
  Autocomplete,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
// Иконки Material UI
import {
  Refresh as RefreshIcon,
  Psychology as BrainIcon,
  Insights as InsightsIcon,
  BarChart as BarChartIcon,
  Person as PersonIcon,
  ShowChart as ChartIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Info as InfoIcon,
  EmojiEvents as TrophyIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
// Подкомпоненты дашборда
import ConfidenceScoreDisplay from '@components/analytics/ConfidenceScoreDisplay';
import FeatureImportanceChart from '@components/analytics/FeatureImportanceChart';
import RankingRationalePanel from '@components/analytics/RankingRationalePanel';
import PerformanceMetricsChart from '@components/analytics/PerformanceMetricsChart';

/**
 * Краткая информация о кандидате для списка
 */
interface CandidateOption {
  id: string;
  name: string;
  position: number;
  score: number;
}

/**
 * Ответ API со списком кандидатов
 */
interface CandidatesListResponse {
  candidates: CandidateOption[];
  total: number;
}

/**
 * Свойства компонента AIExplainabilityDashboard
 */
interface AIExplainabilityDashboardProps {
  /** Базовый URL API */
  apiBaseUrl?: string;
}

/**
 * Форматирование даты для отображения
 */
const formatDate = (date: Date): string => {
  return date.toISOString().split('T')[0];
};

/**
 * Получить дату N дней назад
 */
const getDateDaysAgo = (days: number): string => {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return formatDate(date);
};

/**
 * Компонент AIExplainabilityDashboard
 *
 * Главная страница дашборда объяснимости ИИ, объединяющая четыре секции:
 * 1. Модель уверенности (Confidence Score Display)
 * 2. Важность признаков (Feature Importance Chart)
 * 3. Обоснование ранжирования кандидата (Ranking Rationale Panel)
 * 4. Метрики производительности во времени (Performance Metrics Chart)
 *
 * @example
 * ```tsx
 * <AIExplainabilityDashboard />
 * ```
 *
 * @example
 * ```tsx
 * <AIExplainabilityDashboard apiBaseUrl="/api/analytics" />
 * ```
 */
const AIExplainabilityDashboard: React.FC<AIExplainabilityDashboardProps> = ({
  apiBaseUrl = '/api/analytics/ai-explainability',
}) => {
  // Состояния для фильтров и настроек
  const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d' | 'custom'>('30d');
  const [customStartDate, setCustomStartDate] = useState<string>(getDateDaysAgo(30));
  const [customEndDate, setCustomEndDate] = useState<string>(formatDate(new Date()));
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  // Состояния для списка кандидатов
  const [candidates, setCandidates] = useState<CandidateOption[]>([]);
  const [candidatesLoading, setCandidatesLoading] = useState(true);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);

  // Состояния для статуса загрузки
  const [globalLoading, setGlobalLoading] = useState(true);
  const [globalError, setGlobalError] = useState<string | null>(null);

  /**
   * Вычисляем startDate и endDate на основе выбранного периода
   */
  const getDateRangeValues = useCallback((): { startDate: string; endDate: string } => {
    if (dateRange === 'custom') {
      return { startDate: customStartDate, endDate: customEndDate };
    }
    const daysMap: Record<string, number> = {
      '7d': 7,
      '30d': 30,
      '90d': 90,
    };
    return {
      startDate: getDateDaysAgo(daysMap[dateRange]),
      endDate: formatDate(new Date()),
    };
  }, [dateRange, customStartDate, customEndDate]);

  const { startDate, endDate } = getDateRangeValues();

  /**
   * Загрузка списка кандидатов
   */
  const fetchCandidates = useCallback(async () => {
    try {
      setCandidatesLoading(true);
      // Используем endpoint для получения топ кандидатов
      const response = await axios.get<CandidatesListResponse>(
        `${apiBaseUrl}/top-candidates`,
        {
          params: {
            start_date: startDate,
            end_date: endDate,
            limit: 50,
          },
        }
      );
      setCandidates(response.data.candidates || []);

      // Автовыбор первого кандидата если нет выбранного
      if (!selectedCandidateId && response.data.candidates?.length > 0) {
        setSelectedCandidateId(response.data.candidates[0].id);
      }
    } catch (err) {
      // Если endpoint не существует, используем моковые данные
      setCandidates([]);
    } finally {
      setCandidatesLoading(false);
      setGlobalLoading(false);
    }
  }, [apiBaseUrl, startDate, endDate, selectedCandidateId]);

  /**
   * Initial fetch on mount
   */
  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = () => {
    setAutoRefreshEnabled((prev) => !prev);
  };

  /**
   * Handle date range preset change
   */
  const handleDateRangeChange = (
    _event: React.MouseEvent<HTMLElement>,
    newRange: '7d' | '30d' | '90d' | 'custom' | null
  ) => {
    if (newRange) {
      setDateRange(newRange);
    }
  };

  /**
   * Handle candidate selection
   */
  const handleCandidateSelect = (candidateId: string) => {
    setSelectedCandidateId(candidateId);
  };

  /**
   * Refresh all data
   */
  const refreshAll = () => {
    fetchCandidates();
    // Каждый подкомпонент имеет свой auto-refresh механизм
  };

  /**
   * Render global loading state
   */
  if (globalLoading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            py: 12,
          }}
        >
          <CircularProgress size={80} sx={{ mb: 4 }} />
          <Typography variant="h5" color="text.secondary" gutterBottom>
            Loading AI Explainability Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Initializing explainability components...
          </Typography>
        </Box>
      </Container>
    );
  }

  /**
   * Render global error state
   */
  if (globalError) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={refreshAll} startIcon={<RefreshIcon />}>
              Retry
            </Button>
          }
        >
          <AlertTitle>Error Loading Dashboard</AlertTitle>
          {globalError}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Main Header */}
      <Paper
        elevation={0}
        sx={{
          p: 4,
          mb: 4,
          background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
          color: 'white',
          borderRadius: 3,
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Box
                sx={{
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: 'rgba(255,255,255,0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <BrainIcon sx={{ fontSize: 32 }} />
              </Box>
              <Box>
                <Typography variant="h4" fontWeight={700}>
                  AI Explainability Dashboard
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  Transparency and insights into ML-powered candidate recommendations
                </Typography>
              </Box>
            </Box>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              <Chip
                icon={<InsightsIcon />}
                label="Explainable AI"
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
              <Chip
                icon={<BarChartIcon />}
                label="Feature Analysis"
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
              <Chip
                icon={<ChartIcon />}
                label="Performance Tracking"
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
              {autoRefreshEnabled ? 'Auto Refresh' : 'Paused'}
            </Button>
            <Button
              variant="outlined"
              size="small"
              onClick={refreshAll}
              startIcon={<RefreshIcon />}
              sx={{ borderColor: 'rgba(255,255,255,0.5)', color: 'white' }}
            >
              Refresh All
            </Button>
          </Stack>
        </Box>
      </Paper>

      {/* Date Range Filter Bar */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="subtitle1" fontWeight={600}>
                Date Range:
              </Typography>
              <ToggleButtonGroup
                value={dateRange}
                exclusive
                onChange={handleDateRangeChange}
                size="small"
                aria-label="date range selector"
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
                <ToggleButton value="custom" aria-label="custom range">
                  Custom
                </ToggleButton>
              </ToggleButtonGroup>
            </Box>

            {dateRange === 'custom' && (
              <Stack direction="row" spacing={2} alignItems="center">
                <TextField
                  label="Start Date"
                  type="date"
                  size="small"
                  value={customStartDate}
                  onChange={(e) => setCustomStartDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
                <Typography variant="body2" color="text.secondary">
                  to
                </Typography>
                <TextField
                  label="End Date"
                  type="date"
                  size="small"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Stack>
            )}

            <Chip
              label={`${startDate} to ${endDate}`}
              size="small"
              variant="outlined"
              icon={<SettingsIcon />}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Candidate Selection for Ranking Rationale */}
      {candidates.length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <PersonIcon color="action" />
              <Typography variant="subtitle1" fontWeight={600} sx={{ minWidth: 150 }}>
                Select Candidate:
              </Typography>
              <Autocomplete
                id="dashboard-candidate-select"
                options={candidates}
                value={candidates.find((c) => c.id === selectedCandidateId) || null}
                getOptionLabel={(option) =>
                  `${option.name} (Rank #${option.position}, ${(option.score * 100).toFixed(1)}%)`
                }
                onChange={(_event, newValue) => {
                  if (newValue) {
                    handleCandidateSelect(newValue.id);
                  }
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Select candidate for analysis"
                    variant="outlined"
                    size="small"
                    fullWidth
                  />
                )}
                renderOption={(props, option) => (
                  <li {...props} key={option.id}>
                    <ListItemIcon>
                      <TrophyIcon
                        color={
                          option.position === 1
                            ? 'warning'
                            : option.position <= 3
                              ? 'primary'
                              : 'action'
                        }
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={option.name}
                      secondary={`Rank #${option.position} • Score: ${(option.score * 100).toFixed(1)}%`}
                    />
                  </li>
                )}
                sx={{ minWidth: 400, flexGrow: 1 }}
                loading={candidatesLoading}
              />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Dashboard Sections Grid */}
      <Grid container spacing={4}>
        {/* Section 1: Model Confidence Scores */}
        <Grid item xs={12}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <BrainIcon color="primary" />
              <Typography variant="h5" fontWeight={700}>
                Model Confidence
              </Typography>
              <Chip label="Section 1" size="small" variant="outlined" />
            </Box>
            <ConfidenceScoreDisplay
              apiUrl={`${apiBaseUrl}/confidence`}
              startDate={startDate}
              endDate={endDate}
            />
          </Box>
        </Grid>

        {/* Section 2: Feature Importance Analysis */}
        <Grid item xs={12}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <BarChartIcon color="primary" />
              <Typography variant="h5" fontWeight={700}>
                Feature Importance
              </Typography>
              <Chip label="Section 2" size="small" variant="outlined" />
            </Box>
            <FeatureImportanceChart
              apiUrl={`${apiBaseUrl}/feature-importance`}
              startDate={startDate}
              endDate={endDate}
              maxFeatures={13}
            />
          </Box>
        </Grid>

        {/* Section 3: Candidate Ranking Rationale */}
        <Grid item xs={12}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <PersonIcon color="primary" />
              <Typography variant="h5" fontWeight={700}>
                Candidate Ranking Rationale
              </Typography>
              <Chip label="Section 3" size="small" variant="outlined" />
            </Box>
            <RankingRationalePanel
              apiUrl={`${apiBaseUrl}/ranking-rationale`}
              candidateId={selectedCandidateId || undefined}
              candidates={candidates}
              onCandidateSelect={handleCandidateSelect}
            />
          </Box>
        </Grid>

        {/* Section 4: Performance Metrics Over Time */}
        <Grid item xs={12}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <ChartIcon color="primary" />
              <Typography variant="h5" fontWeight={700}>
                Performance Metrics
              </Typography>
              <Chip label="Section 4" size="small" variant="outlined" />
            </Box>
            <PerformanceMetricsChart
              apiUrl={`${apiBaseUrl}/performance-trends`}
              defaultPeriod={dateRange === 'custom' ? '30d' : dateRange}
            />
          </Box>
        </Grid>
      </Grid>

      {/* Dashboard Footer Info */}
      <Card sx={{ mt: 4, bgcolor: 'grey.50' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <InfoIcon color="info" sx={{ mt: 0.5 }} />
            <Box>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                About the AI Explainability Dashboard
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                This dashboard provides transparency into the ML-powered candidate ranking system.
                It shows how confident the model is in its predictions, which factors influence
                rankings the most, detailed explanations for individual candidates, and how the
                model's performance changes over time.
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Confidence Scores
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Shows prediction certainty with uncertainty intervals
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Feature Importance
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Which factors most influence ranking decisions
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Ranking Rationale
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Human-readable explanations for candidate rankings
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Performance Trends
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Model accuracy and quality metrics over time
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
};

export default AIExplainabilityDashboard;
