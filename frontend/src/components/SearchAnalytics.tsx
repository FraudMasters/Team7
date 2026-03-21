/**
 * Компонент аналитики поисковых запросов
 *
 * Отображает статистику по поисковым запросам включая популярные запросы,
 * запросы с нулевыми результатами и тренды поиска.
 */

// Импорт хуков React
import { useMemo, useState } from 'react';

// Импорт компонентов MUI
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Chip,
  List,
  ListItem,
  ListItemText,
  Alert,
  CircularProgress,
  Paper,
  Divider,
  Slider,
  TextField,
  Button,
  IconButton,
} from '@mui/material';

// Импорт иконок MUI
import {
  TrendingUp as TrendingUpIcon,
  SearchOff as SearchOffIcon,
  Insights as InsightsIcon,
  Tune as TuneIcon,
  Save as SaveIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';

// Импорт компонентов Recharts
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';

// Импорт хуков React Query для управления данными
import { useQuery } from '@tanstack/react-query';

// Импорт API клиента для аналитики поиска
import { searchAnalyticsClient } from '../api/searchAnalytics';

// Импорт типов
import type {
  PopularSearchResponse,
  ZeroResultSearchResponse,
  SearchQueryResponse,
} from '../types/api';

// Импорт хука для определения размеров экрана
import { useBreakpoints } from '../hooks';

// Импорт утилит для работы с датами
import { format, parseISO } from 'date-fns';

// Импорт конфигурации
import { config } from '@/config';

/**
 * Интерфейс свойств компонента
 */
interface SearchAnalyticsProps {
  /**
   * Максимальное количество элементов для отображения
   */
  limit?: number;
  /**
   * Флаг администратора для отображения панели настройки релевантности
   */
  isAdmin?: boolean;
  /**
   * ID организации для настроек релевантности
   */
  organizationId?: string;
}

/**
 * Интерфейс настроек весов полей
 */
interface FieldWeights {
  skills: number;
  experience: number;
  education: number;
}

/**
 * Компонент аналитики поисковых запросов
 *
 * Отображает три основных раздела:
 * 1. График трендов поисковых запросов
 * 2. Список популярных запросов
 * 3. Список запросов с нулевыми результатами
 * 4. Панель настройки релевантности (только для администраторов)
 */
export function SearchAnalytics({ limit = 10, isAdmin = false, organizationId }: SearchAnalyticsProps) {
  // Определяем, мобильное ли устройство
  const { isMobile } = useBreakpoints();

  // Состояние для настройки весов полей
  const [fieldWeights, setFieldWeights] = useState<FieldWeights>({
    skills: 50,
    experience: 30,
    education: 20,
  });

  // Состояние для тестового запроса
  const [testQuery, setTestQuery] = useState('');
  const [testResults, setTestResults] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Загружаем популярные поиски
  const {
    data: popularSearchesData,
    isLoading: isLoadingPopular,
    error: popularError,
  } = useQuery({
    queryKey: ['search-analytics', 'popular', limit],
    queryFn: async () => {
      return await searchAnalyticsClient.getPopularSearches(limit);
    },
  });

  // Загружаем поиски с нулевыми результатами
  const {
    data: zeroResultsData,
    isLoading: isLoadingZeroResults,
    error: zeroResultsError,
  } = useQuery({
    queryKey: ['search-analytics', 'zero-results', limit],
    queryFn: async () => {
      return await searchAnalyticsClient.getZeroResultSearches(limit);
    },
  });

  // Загружаем недавние поиски для графика трендов
  const {
    data: recentSearchesData,
    isLoading: isLoadingRecent,
    error: recentError,
  } = useQuery({
    queryKey: ['search-analytics', 'recent', 50],
    queryFn: async () => {
      return await searchAnalyticsClient.getRecentSearches(50);
    },
  });

  // Получаем списки данных
  const popularSearches = popularSearchesData?.searches || [];
  const zeroResultSearches = zeroResultsData?.searches || [];
  const recentSearches = recentSearchesData?.searches || [];

  // Подготовка данных для графика трендов
  const trendData = useMemo(() => {
    // Группируем поиски по датам
    const searchesByDate = recentSearches.reduce(
      (acc, search) => {
        const date = format(parseISO(search.created_at), 'MMM dd');
        if (!acc[date]) {
          acc[date] = 0;
        }
        acc[date]++;
        return acc;
      },
      {} as Record<string, number>
    );

    // Преобразуем в массив для графика
    return Object.entries(searchesByDate)
      .map(([date, count]) => ({
        date,
        searches: count,
      }))
      .reverse()
      .slice(-14); // Последние 14 дней
  }, [recentSearches]);

  // Подготовка данных для графика популярных запросов
  const popularQueriesChartData = useMemo(() => {
    return popularSearches.slice(0, 5).map((search) => ({
      query: search.query.length > 20 ? search.query.substring(0, 20) + '...' : search.query,
      count: search.search_count,
    }));
  }, [popularSearches]);

  // Вычисляем общий вес
  const totalWeight = fieldWeights.skills + fieldWeights.experience + fieldWeights.education;

  // Проверяем валидность весов
  const isWeightsValid = Math.abs(totalWeight - 100) < 1;

  /**
   * Нормализовать веса к 100%
   */
  const normalizeWeights = () => {
    if (totalWeight === 0) return;

    const normalized = {
      skills: Math.round((fieldWeights.skills / totalWeight) * 100),
      experience: Math.round((fieldWeights.experience / totalWeight) * 100),
      education: Math.round((fieldWeights.education / totalWeight) * 100),
    };

    // Корректировка ошибок округления
    const normalizedTotal = normalized.skills + normalized.experience + normalized.education;
    if (normalizedTotal !== 100) {
      normalized.education += (100 - normalizedTotal);
    }

    setFieldWeights(normalized);
  };

  /**
   * Обработчик изменения веса поля
   */
  const handleWeightChange = (field: keyof FieldWeights, value: number) => {
    setFieldWeights((prev) => ({
      ...prev,
      [field]: value,
    }));
    setSaveSuccess(false);
  };

  /**
   * Тестирование запроса с текущими весами
   */
  const handleTestQuery = async () => {
    if (!testQuery.trim()) return;

    setIsTesting(true);
    setTestResults(null);

    try {
      // Симуляция API вызова
      // В реальном приложении здесь будет вызов API
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setTestResults(
        `Test results with weights - Skills: ${fieldWeights.skills}%, Experience: ${fieldWeights.experience}%, Education: ${fieldWeights.education}%`
      );
    } catch (error) {
      setTestResults('Error testing query');
    } finally {
      setIsTesting(false);
    }
  };

  /**
   * Сохранение настроек весов
   */
  const handleSaveWeights = async () => {
    if (!isWeightsValid) {
      normalizeWeights();
      return;
    }

    setIsSaving(true);
    setSaveSuccess(false);

    try {
      // Симуляция API вызова
      // В реальном приложении здесь будет вызов API для сохранения весов
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      // Обработка ошибки
    } finally {
      setIsSaving(false);
    }
  };

  // Проверяем состояние загрузки
  const isLoading = isLoadingPopular || isLoadingZeroResults || isLoadingRecent;

  // Проверяем наличие ошибок
  const hasError = popularError || zeroResultsError || recentError;

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    );
  }

  if (hasError) {
    return (
      <Alert severity="error">
        Failed to load search analytics. Please try again later.
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* График трендов поисковых запросов */}
      <Card>
        <CardContent>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
            <InsightsIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Search Trends
            </Typography>
          </Stack>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Number of searches over the last 14 days
          </Typography>
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={isMobile ? 250 : 300}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  style={{ fontSize: isMobile ? '10px' : '12px' }}
                />
                <YAxis style={{ fontSize: isMobile ? '10px' : '12px' }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="searches"
                  stroke="#1976d2"
                  strokeWidth={2}
                  dot={{ fill: '#1976d2' }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <Alert severity="info">No search data available yet</Alert>
          )}
        </CardContent>
      </Card>

      {/* Популярные запросы */}
      <Card>
        <CardContent>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
            <TrendingUpIcon color="success" />
            <Typography variant="h6" fontWeight={600}>
              Popular Queries
            </Typography>
          </Stack>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Most frequently searched queries
          </Typography>

          {/* График популярных запросов */}
          {popularQueriesChartData.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <ResponsiveContainer width="100%" height={isMobile ? 200 : 250}>
                <BarChart data={popularQueriesChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="query"
                    style={{ fontSize: isMobile ? '9px' : '11px' }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis style={{ fontSize: isMobile ? '10px' : '12px' }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#2e7d32" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          )}

          {/* Список популярных запросов */}
          {popularSearches.length > 0 ? (
            <List disablePadding>
              {popularSearches.map((search: PopularSearchResponse, index: number) => (
                <Box key={search.id}>
                  <ListItem
                    sx={{
                      px: 0,
                      flexDirection: isMobile ? 'column' : 'row',
                      alignItems: isMobile ? 'flex-start' : 'center',
                      gap: 1,
                    }}
                  >
                    <ListItemText
                      primary={
                        <Typography variant="body1" fontWeight={500}>
                          {search.query}
                        </Typography>
                      }
                      secondary={
                        <Typography variant="body2" color="text.secondary">
                          Last searched: {format(parseISO(search.last_searched_at), 'MMM dd, yyyy')}
                        </Typography>
                      }
                    />
                    <Stack direction="row" spacing={1} flexShrink={0}>
                      <Chip
                        label={`${search.search_count} searches`}
                        size="small"
                        color="success"
                        variant="outlined"
                      />
                      {search.avg_results_count !== null && search.avg_results_count !== undefined && (
                        <Chip
                          label={`~${Math.round(search.avg_results_count)} results`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Stack>
                  </ListItem>
                  {index < popularSearches.length - 1 && <Divider />}
                </Box>
              ))}
            </List>
          ) : (
            <Alert severity="info">No popular searches yet</Alert>
          )}
        </CardContent>
      </Card>

      {/* Запросы с нулевыми результатами */}
      <Card>
        <CardContent>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
            <SearchOffIcon color="warning" />
            <Typography variant="h6" fontWeight={600}>
              Zero-Result Queries
            </Typography>
          </Stack>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Searches that returned no results
          </Typography>
          {zeroResultSearches.length > 0 ? (
            <List disablePadding>
              {zeroResultSearches.map((search: ZeroResultSearchResponse, index: number) => (
                <Box key={search.id}>
                  <ListItem
                    sx={{
                      px: 0,
                      flexDirection: isMobile ? 'column' : 'row',
                      alignItems: isMobile ? 'flex-start' : 'center',
                      gap: 1,
                    }}
                  >
                    <ListItemText
                      primary={
                        <Typography variant="body1" fontWeight={500}>
                          {search.query}
                        </Typography>
                      }
                      secondary={
                        <Typography variant="body2" color="text.secondary">
                          {format(parseISO(search.created_at), 'MMM dd, yyyy HH:mm')}
                        </Typography>
                      }
                    />
                    {search.search_type && (
                      <Chip
                        label={search.search_type}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </ListItem>
                  {index < zeroResultSearches.length - 1 && <Divider />}
                </Box>
              ))}
            </List>
          ) : (
            <Alert severity="success">
              Great! All searches are returning results
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Панель настройки релевантности (только для администраторов) */}
      {isAdmin && (
        <Card>
          <CardContent>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
              <TuneIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Relevance Tuning
              </Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Adjust field weights to customize search relevance scoring
            </Typography>

            {/* Сообщение об успешном сохранении */}
            {saveSuccess && (
              <Alert severity="success" sx={{ mb: 2 }}>
                Field weights saved successfully!
              </Alert>
            )}

            {/* Слайдеры для настройки весов */}
            <Stack spacing={3} sx={{ mb: 3 }}>
              {/* Вес навыков */}
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Skills Weight
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {fieldWeights.skills}%
                  </Typography>
                </Box>
                <Slider
                  value={fieldWeights.skills}
                  onChange={(_, value) => handleWeightChange('skills', value as number)}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${value}%`}
                  sx={{ color: 'primary.main' }}
                />
                <Typography variant="caption" color="text.secondary">
                  Importance of matching required skills
                </Typography>
              </Box>

              {/* Вес опыта */}
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Experience Weight
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {fieldWeights.experience}%
                  </Typography>
                </Box>
                <Slider
                  value={fieldWeights.experience}
                  onChange={(_, value) => handleWeightChange('experience', value as number)}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${value}%`}
                  sx={{ color: 'secondary.main' }}
                />
                <Typography variant="caption" color="text.secondary">
                  Importance of years of experience
                </Typography>
              </Box>

              {/* Вес образования */}
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Education Weight
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {fieldWeights.education}%
                  </Typography>
                </Box>
                <Slider
                  value={fieldWeights.education}
                  onChange={(_, value) => handleWeightChange('education', value as number)}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${value}%`}
                  sx={{ color: 'info.main' }}
                />
                <Typography variant="caption" color="text.secondary">
                  Importance of educational background
                </Typography>
              </Box>
            </Stack>

            {/* Общий вес и валидация */}
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle2">Total Weight:</Typography>
                <Chip
                  label={`${totalWeight}%`}
                  color={isWeightsValid ? 'success' : 'warning'}
                  variant={isWeightsValid ? 'filled' : 'outlined'}
                  size="small"
                />
              </Box>
              {!isWeightsValid && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  Weights must sum to 100% (currently: {totalWeight}%)
                  <Button
                    size="small"
                    onClick={normalizeWeights}
                    sx={{ ml: 2 }}
                  >
                    Normalize
                  </Button>
                </Alert>
              )}
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Раздел тестирования запроса */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Test Query
              </Typography>
              <Stack direction={isMobile ? 'column' : 'row'} spacing={2} sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  placeholder="Enter search query to test..."
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                  size="small"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleTestQuery();
                    }
                  }}
                />
                <Button
                  variant="outlined"
                  startIcon={isTesting ? <CircularProgress size={16} /> : <PlayArrowIcon />}
                  onClick={handleTestQuery}
                  disabled={!testQuery.trim() || isTesting}
                  sx={{ minWidth: 100 }}
                >
                  {isTesting ? 'Testing...' : 'Test'}
                </Button>
              </Stack>
              {testResults && (
                <Alert severity="info" icon={<InsightsIcon />}>
                  {testResults}
                </Alert>
              )}
            </Box>

            {/* Кнопка сохранения */}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                startIcon={isSaving ? <CircularProgress size={16} /> : <SaveIcon />}
                onClick={handleSaveWeights}
                disabled={!isWeightsValid || isSaving}
              >
                {isSaving ? 'Saving...' : 'Save Weights'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Stack>
  );
}

export default SearchAnalytics;
