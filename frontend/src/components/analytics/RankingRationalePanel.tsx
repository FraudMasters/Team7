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
  LinearProgress,
  Chip,
  Divider,
  TextField,
  Autocomplete,
  ListItem,
  ListItemIcon,
  ListItemText,
  List,
  IconButton,
  Tooltip,
} from '@mui/material';
// Иконки Material UI
import {
  Refresh as RefreshIcon,
  Person as PersonIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  EmojiEvents as TrophyIcon,
  Stars as StarsIcon,
  Psychology as BrainIcon,
  Search as SearchIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  BarChart as BarChartIcon,
} from '@mui/icons-material';

/**
 * Детализация фактора ранжирования с бэкенда
 */
interface RankingFactorDetail {
  /** Название фактора */
  factor_name: string;
  /** Балл фактора */
  score: number;
  /** Вес фактора в модели */
  weight: number;
  /** Вклад в общий балл */
  contribution: number;
  /** Описание фактора */
  description: string;
  /** Сырое значение */
  raw_value?: number;
}

/**
 * Детализация совпадения навыков
 */
interface SkillsMatchDetail {
  /** Совпавшие навыки */
  matched_skills: string[];
  /** Отсутствующие навыки */
  missing_skills: string[];
  /** Дополнительные навыки */
  additional_skills: string[];
  /** Процент совпадения */
  match_percentage: number;
}

/**
 * Ответ API с обоснованием ранжирования кандидата
 */
interface RankingRationaleResponse {
  /** ID кандидата */
  candidate_id: string;
  /** ID вакансии */
  vacancy_id?: string;
  /** Балл ранжирования */
  rank_score: number;
  /** Позиция в рейтинге */
  rank_position?: number;
  /** Рекомендация */
  recommendation: 'excellent' | 'good' | 'maybe' | 'poor';
  /** Уверенность модели (0-1) */
  confidence: number;
  /** Версия модели */
  model_version: string;
  /** Тип модели */
  model_type: string;
  /** Факторы ранжирования */
  factors: RankingFactorDetail[];
  /** Совпадение навыков */
  skills_match?: SkillsMatchDetail;
  /** Текстовое описание (саммари) */
  summary: string;
  /** Сильные стороны кандидата */
  strengths: string[];
  /** Слабые стороны кандидата */
  weaknesses: string[];
  /** Время генерации */
  generated_at: string;
}

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
 * Свойства компонента RankingRationalePanel
 */
interface RankingRationalePanelProps {
  /** URL API endpoint для обоснования ранжирования */
  apiUrl?: string;
  /** ID кандидата для отображения (опционально) */
  candidateId?: string;
  /** Список кандидатов для выбора */
  candidates?: CandidateOption[];
  /** Callback при выборе кандидата */
  onCandidateSelect?: (candidateId: string) => void;
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
 * Получить цвет для вклада на основе значения contribution
 */
const getContributionColor = (contribution: number): 'success' | 'error' | 'warning' => {
  if (contribution > 0.05) return 'success';
  if (contribution < -0.05) return 'error';
  return 'warning';
};

/**
 * Определить тип влияния на основе contribution
 */
const getImpactType = (contribution: number): 'positive' | 'negative' | 'neutral' => {
  if (contribution > 0.05) return 'positive';
  if (contribution < -0.05) return 'negative';
  return 'neutral';
};

/**
 * Получить цвет для балла
 */
const getScoreColor = (score: number): 'success' | 'warning' | 'error' => {
  if (score >= 0.7) return 'success';
  if (score >= 0.5) return 'warning';
  return 'error';
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
 * Компонент RankingRationalePanel
 *
 * Отображает обоснование ранжирования кандидата включая:
 * - Нарративное описание почему кандидат получил такую позицию
 * - Вклады признаков (какие факторы повлияли на рейтинг)
 * - Сильные и слабые стороны кандидата
 * - Интервал уверенности предсказания
 * - Возможность выбора кандидата для анализа
 *
 * @example
 * ```tsx
 * <RankingRationalePanel candidateId="123" />
 * ```
 *
 * @example
 * ```tsx
 * <RankingRationalePanel
 *   candidates={candidatesList}
 *   onCandidateSelect={(id) => setSelectedId(id)}
 * />
 * ```
 */
const RankingRationalePanel: React.FC<RankingRationalePanelProps> = ({
  apiUrl = '/api/analytics/ai-explainability/ranking-rationale',
  candidateId,
  candidates = [],
  onCandidateSelect,
}) => {
  // Состояния для загрузки, ошибки, данных и автообновления
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rationale, setRationale] = useState<RankingRationaleResponse | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(
    candidateId || null
  );
  const [searchQuery, setSearchQuery] = useState('');

  /**
   * Установка выбранного кандидата при изменении prop
   */
  useEffect(() => {
    if (candidateId) {
      setSelectedCandidateId(candidateId);
    }
  }, [candidateId]);

  /**
   * Загрузка обоснования ранжирования с бэкенда
   */
  const fetchRationale = useCallback(async () => {
    if (!selectedCandidateId) {
      setRationale(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await axios.get<RankingRationaleResponse>(
        `${apiUrl}/${selectedCandidateId}`
      );
      setRationale(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load ranking rationale';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, selectedCandidateId]);

  /**
   * Initial fetch on mount and when candidate changes
   */
  useEffect(() => {
    fetchRationale();
  }, [fetchRationale]);

  /**
   * Auto-refresh every 60 seconds when enabled and candidate selected
   */
  useEffect(() => {
    if (!autoRefreshEnabled || !selectedCandidateId) {
      return;
    }

    const interval = setInterval(() => {
      fetchRationale();
    }, 60000); // 60 seconds

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, selectedCandidateId, fetchRationale]);

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = () => {
    setAutoRefreshEnabled((prev) => !prev);
  };

  /**
   * Handle candidate selection
   */
  const handleCandidateChange = (
    _event: React.SyntheticEvent,
    newValue: CandidateOption | null
  ) => {
    if (newValue) {
      setSelectedCandidateId(newValue.id);
      if (onCandidateSelect) {
        onCandidateSelect(newValue.id);
      }
    }
  };

  /**
   * Filter candidates for autocomplete
   */
  const filteredCandidates = candidates.filter(
    (candidate) =>
      candidate.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      candidate.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  /**
   * Сортировка факторов по величине вклада
   */
  const sortedFactors = React.useMemo(() => {
    if (!rationale?.factors) return [];
    return [...rationale.factors].sort(
      (a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)
    );
  }, [rationale?.factors]);

  /**
   * Render loading state
   */
  if (loading && !rationale) {
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
          Loading ranking rationale...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Analyzing candidate ranking factors
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
          <Button color="inherit" size="small" onClick={fetchRationale} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
        sx={{ mb: 3 }}
      >
        <AlertTitle>Error Loading Ranking Rationale</AlertTitle>
        {error}
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
              Candidate Ranking Rationale
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Explainable AI insights into why candidates received their ranking
            </Typography>
            {rationale && (
              <Chip
                icon={<PersonIcon />}
                label={`Position #${rationale.rank_position}`}
                size="small"
                sx={{ mt: 1, bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
            )}
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
              onClick={fetchRationale}
              startIcon={<RefreshIcon />}
              disabled={!selectedCandidateId}
              sx={{ borderColor: 'rgba(255,255,255,0.5)', color: 'white' }}
            >
              Refresh
            </Button>
          </Stack>
        </Box>
      </Paper>

      {/* Candidate Selection */}
      {candidates.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <SearchIcon color="action" />
              <Autocomplete
                id="candidate-select"
                options={filteredCandidates}
                getOptionLabel={(option) =>
                  `${option.name} (Rank #${option.position}, ${formatPercent(option.score)})`
                }
                onChange={handleCandidateChange}
                inputValue={searchQuery}
                onInputChange={(_event, newInputValue) => setSearchQuery(newInputValue)}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Select Candidate"
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
                      secondary={`Rank #${option.position} • Score: ${formatPercent(option.score)}`}
                    />
                  </li>
                )}
                sx={{ minWidth: 300, flexGrow: 1 }}
              />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* No candidate selected */}
      {!selectedCandidateId && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <AlertTitle>Select a Candidate</AlertTitle>
          {candidates.length > 0
            ? 'Use the search above to select a candidate and view their ranking rationale.'
            : 'No candidates available. Candidates will appear here after rankings are generated.'}
        </Alert>
      )}

      {/* Rationale Content */}
      {rationale && (
        <>
          {/* Summary Card */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Grid container spacing={3}>
                {/* Score and Position */}
                <Grid item xs={12} md={4}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 3,
                      bgcolor: 'grey.50',
                      borderRadius: 2,
                      textAlign: 'center',
                      height: '100%',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 1 }}>
                      <TrophyIcon
                        fontSize="large"
                        color={rationale.rank_position <= 3 ? 'warning' : 'action'}
                      />
                      <Typography variant="h2" fontWeight="bold" color="primary">
                        #{rationale.rank_position}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Ranking Position
                    </Typography>
                    <Divider sx={{ my: 2 }} />
                    <Typography
                      variant="h3"
                      fontWeight="bold"
                      color={getScoreColor(rationale.rank_score) + '.main'}
                    >
                      {formatPercent(rationale.rank_score)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Match Score
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="caption" color="text.secondary">
                        Confidence: {formatPercent(rationale.confidence)}
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>

                {/* Narrative */}
                <Grid item xs={12} md={8}>
                  <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <BrainIcon color="primary" />
                      <Typography variant="h6" fontWeight={600}>
                        AI Analysis Summary
                      </Typography>
                    </Box>
                    <Paper
                      elevation={0}
                      sx={{
                        p: 2,
                        bgcolor: 'grey.50',
                        borderRadius: 2,
                        flexGrow: 1,
                      }}
                    >
                      <Typography variant="body1" sx={{ lineHeight: 1.7 }}>
                        {rationale.summary}
                      </Typography>
                    </Paper>
                    {rationale.vacancy_title && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                        For position: {rationale.vacancy_title}
                      </Typography>
                    )}
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Strengths and Weaknesses */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            {/* Strengths */}
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <ThumbUpIcon color="success" />
                    <Typography variant="h6" fontWeight={600}>
                      Strengths
                    </Typography>
                  </Box>
                  {rationale.strengths && rationale.strengths.length > 0 ? (
                    <List dense disablePadding>
                      {rationale.strengths.map((strength, index) => (
                        <ListItem key={index} disableGutters>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <CheckCircleIcon fontSize="small" color="success" />
                          </ListItemIcon>
                          <ListItemText
                            primary={strength}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No specific strengths identified
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Weaknesses */}
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <ThumbDownIcon color="error" />
                    <Typography variant="h6" fontWeight={600}>
                      Areas for Improvement
                    </Typography>
                  </Box>
                  {rationale.weaknesses && rationale.weaknesses.length > 0 ? (
                    <List dense disablePadding>
                      {rationale.weaknesses.map((weakness, index) => (
                        <ListItem key={index} disableGutters>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <WarningIcon fontSize="small" color="warning" />
                          </ListItemIcon>
                          <ListItemText
                            primary={weakness}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No significant weaknesses identified
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Feature Contributions */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <BarChartIcon color="primary" />
                  <Typography variant="h6" fontWeight={600}>
                    Feature Contributions
                  </Typography>
                </Box>
                <Tooltip title="Shows how each factor contributed to the candidate's ranking score">
                  <IconButton size="small">
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>

              <Grid container spacing={2}>
                {sortedFactors.slice(0, 8).map((factor, index) => {
                  const impact = getImpactType(factor.contribution);
                  const contributionColor = getContributionColor(factor.contribution);
                  return (
                    <Grid item xs={12} sm={6} md={3} key={factor.factor_name}>
                      <Paper
                        elevation={0}
                        sx={{
                          p: 2,
                          bgcolor: 'grey.50',
                          borderRadius: 2,
                          borderLeft: 4,
                          borderLeftColor: contributionColor + '.main',
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          {impact === 'positive' ? (
                            <TrendingUpIcon fontSize="small" color="success" />
                          ) : impact === 'negative' ? (
                            <TrendingDownIcon fontSize="small" color="error" />
                          ) : (
                            <StarsIcon fontSize="small" color="warning" />
                          )}
                          <Typography variant="subtitle2" fontWeight={600}>
                            {formatFeatureName(factor.factor_name)}
                          </Typography>
                        </Box>
                        <Typography
                          variant="h5"
                          fontWeight="bold"
                          color={contributionColor + '.main'}
                        >
                          {factor.contribution < 0 ? '-' : '+'}
                          {formatPercent(Math.abs(factor.contribution))}
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={Math.abs(factor.contribution) * 500} // Scale for visibility
                          color={contributionColor}
                          sx={{ mt: 1, height: 6, borderRadius: 3 }}
                        />
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                          Score: {formatPercent(factor.score)}
                        </Typography>
                      </Paper>
                    </Grid>
                  );
                })}
              </Grid>

              {/* Remaining factors if more than 8 */}
              {sortedFactors.length > 8 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    + {sortedFactors.length - 8} more factors
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Confidence Explanation */}
          <Card sx={{ bgcolor: 'grey.50' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <InfoIcon color="info" />
                <Box>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    About This Rationale
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    This explanation shows how the ML model arrived at this candidate's ranking. The
                    feature contributions indicate which factors increased or decreased the match
                    score. The confidence ({formatPercent(rationale.confidence)}) reflects the model's
                    certainty in its prediction.
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
};

export default RankingRationalePanel;
