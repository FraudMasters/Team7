// React хуки для управления состоянием и эффектами
import React, { useMemo } from 'react';
// Компоненты Material UI для создания интерфейса
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Stack,
  Chip,
  alpha,
} from '@mui/material';
// Иконки Material UI
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  ArrowForward as ArrowForwardIcon,
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
  Legend,
  Cell,
  LineChart,
  Line,
  Area,
  ComposedChart,
} from 'recharts';
import type { WhatIfAnalysisResponse } from '@/api/explainability';

/**
 * Свойства компонента ImpactVisualization
 */
interface ImpactVisualizationProps {
  /** Оригинальная оценка */
  originalScore: number;
  /** Результат what-if анализа */
  result: WhatIfAnalysisResponse | null;
  /** Оригинальный уровень рекомендации */
  originalRecommendation?: string;
  /** Показывать детальную визуализацию */
  showDetails?: boolean;
}

/**
 * Цвета для уровней рекомендации
 */
const RECOMMENDATION_COLORS: Record<string, string> = {
  excellent: '#2e7d32',
  good: '#1976d2',
  fair: '#ed6c02',
  poor: '#d32f2f',
};

/**
 * Форматирование процента для отображения
 */
const formatPercent = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Получить цвет для дельты
 */
const getDeltaColor = (delta: number): string => {
  if (delta > 0) return '#2e7d32'; // success
  if (delta < 0) return '#d32f2f'; // error
  return '#666'; // neutral
};

/**
 * Получить иконку для дельты
 */
const getDeltaIcon = (delta: number): React.ReactElement => {
  if (delta > 0.01) return <TrendingUpIcon fontSize="small" />;
  if (delta < -0.01) return <TrendingDownIcon fontSize="small" />;
  return <TrendingFlatIcon fontSize="small" />;
};

/**
 * Кастомный тултип для графика сравнения
 */
const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    payload: {
      name: string;
      before: number;
      after: number;
      delta: number;
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
          minWidth: 200,
        }}
      >
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          {data.name}
        </Typography>
        <Stack spacing={0.5}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Before:
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              {formatPercent(data.before)}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              After:
            </Typography>
            <Typography variant="body2" fontWeight={600} color="primary.main">
              {formatPercent(data.after)}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Change:
            </Typography>
            <Typography
              variant="body2"
              fontWeight={600}
              sx={{ color: getDeltaColor(data.delta) }}
            >
              {data.delta > 0 ? '+' : ''}
              {formatPercent(data.delta)}
            </Typography>
          </Box>
        </Stack>
      </Paper>
    );
  }
  return null;
};

/**
 * Компонент визуализации влияния изменений
 * Показывает before/after сравнение и дельту изменений
 */
export const ImpactVisualization: React.FC<ImpactVisualizationProps> = ({
  originalScore,
  result,
  originalRecommendation = 'fair',
  showDetails = true,
}) => {
  // Вычисление дельты оценки
  const scoreDelta = useMemo(() => {
    if (!result) return 0;
    return result.new_score - originalScore;
  }, [result, originalScore]);

  // Вычисление процентного изменения
  const scoreDeltaPercent = useMemo(() => {
    if (!result || originalScore === 0) return 0;
    return ((result.new_score - originalScore) / originalScore) * 100;
  }, [result, originalScore]);

  // Подготовка данных для графика сравнения
  const comparisonData = useMemo(() => {
    if (!result) return [];

    return [
      {
        name: 'Ranking Score',
        before: originalScore,
        after: result.new_score,
        delta: scoreDelta,
      },
    ];
  }, [result, originalScore, scoreDelta]);

  // Подготовка данных для визуализации дельты по компонентам
  const componentDeltas = useMemo(() => {
    if (!result || !result.feature_impacts) return [];

    return Object.entries(result.feature_impacts)
      .map(([feature_name, impact]) => ({
        name: feature_name.replace(/_/g, ' '),
        impact: impact,
        importance: Math.abs(impact), // Use absolute impact as importance
      }))
      .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
      .slice(0, 8); // Top 8 impacts
  }, [result]);

  if (!result) {
    return (
      <Card variant="outlined">
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body2" color="text.secondary">
            Run a what-if analysis to see impact visualization
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Before/After Comparison Cards */}
      <Grid container spacing={2}>
        {/* Before Card */}
        <Grid item xs={12} md={5}>
          <Card
            variant="outlined"
            sx={{
              bgcolor: alpha('#666', 0.05),
              borderColor: 'divider',
            }}
          >
            <CardContent>
              <Typography
                variant="overline"
                color="text.secondary"
                gutterBottom
                sx={{ display: 'block' }}
              >
                Before
              </Typography>
              <Typography variant="h3" fontWeight={700} gutterBottom>
                {formatPercent(originalScore)}
              </Typography>
              <Chip
                label={originalRecommendation}
                size="small"
                sx={{
                  bgcolor: alpha(
                    RECOMMENDATION_COLORS[originalRecommendation] || '#666',
                    0.1
                  ),
                  color: RECOMMENDATION_COLORS[originalRecommendation] || '#666',
                  fontWeight: 600,
                  textTransform: 'capitalize',
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Arrow */}
        <Grid
          item
          xs={12}
          md={2}
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <ArrowForwardIcon
              sx={{
                fontSize: 32,
                color: getDeltaColor(scoreDelta),
              }}
            />
            <Chip
              icon={getDeltaIcon(scoreDelta)}
              label={`${scoreDelta > 0 ? '+' : ''}${formatPercent(scoreDelta)}`}
              size="small"
              sx={{
                bgcolor: alpha(getDeltaColor(scoreDelta), 0.1),
                color: getDeltaColor(scoreDelta),
                fontWeight: 700,
              }}
            />
          </Box>
        </Grid>

        {/* After Card */}
        <Grid item xs={12} md={5}>
          <Card
            variant="outlined"
            sx={{
              bgcolor: alpha(getDeltaColor(scoreDelta), 0.05),
              borderColor: getDeltaColor(scoreDelta),
              borderWidth: 2,
            }}
          >
            <CardContent>
              <Typography
                variant="overline"
                color="text.secondary"
                gutterBottom
                sx={{ display: 'block' }}
              >
                After
              </Typography>
              <Typography
                variant="h3"
                fontWeight={700}
                gutterBottom
                sx={{ color: getDeltaColor(scoreDelta) }}
              >
                {formatPercent(result.new_score)}
              </Typography>
              <Chip
                label={result.new_recommendation}
                size="small"
                sx={{
                  bgcolor: alpha(
                    RECOMMENDATION_COLORS[result.new_recommendation] ||
                      '#666',
                    0.15
                  ),
                  color:
                    RECOMMENDATION_COLORS[result.new_recommendation] ||
                    '#666',
                  fontWeight: 600,
                  textTransform: 'capitalize',
                }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {showDetails && componentDeltas.length > 0 && (
        <>
          {/* Feature Impact Bar Chart */}
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom fontWeight={600}>
              Feature Impact on Score Change
            </Typography>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              How each adjusted feature affects the ranking score
            </Typography>
            <Box sx={{ width: '100%', height: 300, mt: 2 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={componentDeltas}
                  layout="horizontal"
                  margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis
                    type="number"
                    tickFormatter={(value) => formatPercent(value)}
                    domain={['auto', 'auto']}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={120}
                    tick={{ fontSize: 12 }}
                  />
                  <RechartsTooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <Paper
                            elevation={3}
                            sx={{
                              p: 1.5,
                              border: '1px solid',
                              borderColor: 'divider',
                            }}
                          >
                            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                              {data.name}
                            </Typography>
                            <Stack spacing={0.5}>
                              <Box
                                sx={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  gap: 2,
                                }}
                              >
                                <Typography variant="body2" color="text.secondary">
                                  Impact:
                                </Typography>
                                <Typography
                                  variant="body2"
                                  fontWeight={600}
                                  sx={{ color: getDeltaColor(data.impact) }}
                                >
                                  {data.impact > 0 ? '+' : ''}
                                  {formatPercent(data.impact)}
                                </Typography>
                              </Box>
                              <Box
                                sx={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  gap: 2,
                                }}
                              >
                                <Typography variant="body2" color="text.secondary">
                                  Importance:
                                </Typography>
                                <Typography variant="body2" fontWeight={600}>
                                  {formatPercent(data.importance)}
                                </Typography>
                              </Box>
                            </Stack>
                          </Paper>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                    {componentDeltas.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={getDeltaColor(entry.impact)}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>

          {/* Score Change Summary */}
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom fontWeight={600}>
              Overall Impact Summary
            </Typography>
            <Grid container spacing={2} sx={{ mt: 0.5 }}>
              <Grid item xs={12} sm={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary" gutterBottom>
                    Score Change
                  </Typography>
                  <Typography
                    variant="h4"
                    fontWeight={700}
                    sx={{ color: getDeltaColor(scoreDelta) }}
                  >
                    {scoreDelta > 0 ? '+' : ''}
                    {formatPercent(scoreDelta)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary" gutterBottom>
                    Percentage Change
                  </Typography>
                  <Typography
                    variant="h4"
                    fontWeight={700}
                    sx={{ color: getDeltaColor(scoreDelta) }}
                  >
                    {scoreDeltaPercent > 0 ? '+' : ''}
                    {scoreDeltaPercent.toFixed(1)}%
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary" gutterBottom>
                    Recommendation Change
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {originalRecommendation === result.new_recommendation
                      ? 'No Change'
                      : `${originalRecommendation} → ${result.new_recommendation}`}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </>
      )}
    </Stack>
  );
};

export default ImpactVisualization;
