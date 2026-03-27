// React хуки для управления состоянием
import React from 'react';
import { useTranslation } from 'react-i18next';
// Компоненты Material UI для создания интерфейса
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Stack,
  Chip,
  Tooltip,
  useTheme,
} from '@mui/material';
// Иконки Material UI
import {
  BarChart as BarChartIcon,
  Info as InfoIcon,
  TrendingUp as PositiveIcon,
  TrendingDown as NegativeIcon,
  Psychology as AIIcon,
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
 * Элемент важности фичи
 */
export interface FeatureImportanceItem {
  /** Название фичи (например, "Experience", "Skills", "Education") */
  feature_name: string;
  /** Вес важности фичи (0-1) */
  importance: number;
  /** Направление влияния на ранжирование */
  direction?: 'positive' | 'negative' | 'neutral';
  /** Описание фичи */
  description?: string;
  /** Категория фичи */
  category?: string;
}

/**
 * Свойства компонента FeatureImportanceChart
 */
export interface FeatureImportanceChartProps {
  /** Массив элементов важности фичей (будут показаны топ-5) */
  features: FeatureImportanceItem[];
  /** Заголовок графика */
  title?: string;
  /** Описание графика */
  description?: string;
  /** Максимальное количество фичей для отображения */
  maxFeatures?: number;
  /** Показывать ли детали в тултипах */
  showTooltips?: boolean;
}

/**
 * Форматирование процента для отображения
 */
const formatPercent = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Получить цвет для бара в зависимости от важности
 */
const getBarColor = (importance: number, theme: any): string => {
  if (importance >= 0.7) return theme.palette.success.main;
  if (importance >= 0.5) return theme.palette.primary.main;
  if (importance >= 0.3) return theme.palette.info.main;
  if (importance >= 0.15) return theme.palette.warning.main;
  return theme.palette.error.main;
};

/**
 * Получить иконку для направления влияния
 */
const getDirectionIcon = (direction?: string): React.ReactElement | null => {
  switch (direction) {
    case 'positive':
      return <PositiveIcon fontSize="small" color="success" />;
    case 'negative':
      return <NegativeIcon fontSize="small" color="error" />;
    default:
      return null;
  }
};

/**
 * Кастомный тултип для Recharts
 */
const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{
    payload: {
      feature_name: string;
      importance: number;
      description?: string;
      category?: string;
      direction?: string;
    };
  }>;
}> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <Paper
        elevation={3}
        sx={{
          p: 2,
          border: '1px solid',
          borderColor: 'divider',
          minWidth: 220,
          maxWidth: 320,
        }}
      >
        <Typography variant="subtitle1" fontWeight={700} gutterBottom>
          {data.feature_name}
        </Typography>
        {data.category && (
          <Chip
            label={data.category}
            size="small"
            variant="outlined"
            color="info"
            sx={{ mb: 1 }}
          />
        )}
        <Stack spacing={1}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Importance:
            </Typography>
            <Typography variant="body2" fontWeight={700} color="primary.main">
              {formatPercent(data.importance)}
            </Typography>
          </Box>
          {data.description && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
              {data.description}
            </Typography>
          )}
          {data.direction && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}>
              {getDirectionIcon(data.direction)}
              <Typography variant="caption" color="text.secondary">
                {data.direction === 'positive' ? 'Positive impact' : 'Negative impact'}
              </Typography>
            </Box>
          )}
        </Stack>
      </Paper>
    );
  }
  return null;
};

/**
 * Компонент FeatureImportanceChart
 *
 * Отображает важность топ-5 фичей в виде горизонтального барного графика.
 * Используется в dashboard прозрачности AI для показа факторов,
 * влияющих на ранжирование кандидатов.
 *
 * Включает:
 * - Горизонтальный bar chart с Recharts (топ-5 важных фичей)
 * - Цветовое кодирование баров по уровню важности
 * - Интерактивные тултипы с описаниями фичей
 * - Категории и направления влияния фичей
 *
 * @example
 * ```tsx
 * const features = [
 *   { feature_name: 'Years of Experience', importance: 0.85, description: 'Total years of work experience', direction: 'positive' },
 *   { feature_name: 'Technical Skills Match', importance: 0.72, description: 'Match between candidate skills and job requirements', direction: 'positive' },
 *   { feature_name: 'Education Level', importance: 0.60, description: 'Highest degree obtained', direction: 'positive' },
 *   { feature_name: 'Industry Experience', importance: 0.45, description: 'Experience in relevant industry', direction: 'positive' },
 *   { feature_name: 'Location Distance', importance: 0.30, description: 'Distance from job location', direction: 'negative' },
 * ];
 * <FeatureImportanceChart features={features} />
 * ```
 */
const FeatureImportanceChart: React.FC<FeatureImportanceChartProps> = ({
  features,
  title = 'Feature Importance',
  description = 'Top factors influencing candidate rankings',
  maxFeatures = 5,
  showTooltips = true,
}) => {
  const { t } = useTranslation();
  const theme = useTheme();

  /**
   * Подготовка данных: берём топ-N фичей по важности и сортируем по возрастанию для горизонтального графика
   */
  const chartData = React.useMemo(() => {
    if (!features || features.length === 0) return [];

    // Сортируем по убыванию важности и берём топ-N
    const topFeatures = [...features]
      .sort((a, b) => b.importance - a.importance)
      .slice(0, maxFeatures);

    // Для горизонтального графика сортируем по возрастанию (чтобы самые важные были сверху)
    return topFeatures.reverse().map((feature) => ({
      feature_name: feature.feature_name,
      importance: feature.importance,
      importancePercent: feature.importance * 100,
      description: feature.description,
      category: feature.category,
      direction: feature.direction,
      color: getBarColor(feature.importance, theme),
    }));
  }, [features, maxFeatures, theme]);

  /**
   * Render empty state
   */
  if (!features || features.length === 0) {
    return (
      <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
        <AIIcon sx={{ fontSize: 60, color: 'text.disabled', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          {t('confidence.featureImportance.noData', {
            defaultValue: 'No Feature Importance Data Available',
          })}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('confidence.featureImportance.noDataDescription', {
            defaultValue:
              'Feature importance data will appear after candidate rankings are generated with AI models.',
          })}
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 2.5,
          mb: 2,
          bgcolor: 'background.default',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          <BarChartIcon color="primary" />
          <Typography variant="h6" fontWeight={700}>
            {title}
          </Typography>
          {showTooltips && (
            <Tooltip
              title={t('confidence.featureImportance.tooltip', {
                defaultValue:
                  'Shows the relative importance of different features in the AI ranking algorithm. Hover over bars for detailed descriptions.',
              })}
              arrow
            >
              <InfoIcon fontSize="small" color="action" sx={{ cursor: 'help' }} />
            </Tooltip>
          )}
        </Box>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      </Paper>

      {/* Bar Chart */}
      <Card>
        <CardContent>
          <Box sx={{ width: '100%', height: Math.max(300, chartData.length * 60) }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis
                  type="number"
                  domain={[0, 100]}
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `${value}%`}
                  tickLine={false}
                  axisLine={{ stroke: '#e0e0e0' }}
                />
                <YAxis
                  type="category"
                  dataKey="feature_name"
                  tick={{ fontSize: 12 }}
                  width={150}
                  tickLine={false}
                  axisLine={{ stroke: '#e0e0e0' }}
                />
                {showTooltips && <RechartsTooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.05)' }} />}
                <Bar dataKey="importancePercent" radius={[0, 8, 8, 0]} barSize={30}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Box>

          {/* Legend/Info */}
          <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              {t('confidence.featureImportance.legend', {
                defaultValue: 'Understanding Feature Importance',
              })}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('confidence.featureImportance.legendDescription', {
                defaultValue:
                  'Feature importance indicates how much each factor contributes to the AI ranking decision. Higher values mean the feature has more influence on the final ranking score. Hover over bars to see detailed descriptions of each feature.',
              })}
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 2 }} flexWrap="wrap" useFlexGap>
              <Chip
                size="small"
                sx={{ bgcolor: theme.palette.success.main, color: 'white' }}
                label={`High (≥70%)`}
              />
              <Chip
                size="small"
                sx={{ bgcolor: theme.palette.primary.main, color: 'white' }}
                label="Medium (50-69%)"
              />
              <Chip
                size="small"
                sx={{ bgcolor: theme.palette.info.main, color: 'white' }}
                label="Moderate (30-49%)"
              />
              <Chip
                size="small"
                sx={{ bgcolor: theme.palette.warning.main, color: 'white' }}
                label="Low (15-29%)"
              />
              <Chip
                size="small"
                sx={{ bgcolor: theme.palette.error.main, color: 'white' }}
                label="Very Low (<15%)"
              />
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default FeatureImportanceChart;
