/**
 * Компонент аналитики поисковых запросов
 *
 * Отображает статистику по поисковым запросам включая популярные запросы,
 * запросы с нулевыми результатами и тренды поиска.
 */

// Импорт хуков React
import { useMemo } from 'react';

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
} from '@mui/material';

// Импорт иконок MUI
import {
  TrendingUp as TrendingUpIcon,
  SearchOff as SearchOffIcon,
  Insights as InsightsIcon,
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

/**
 * Интерфейс свойств компонента
 */
interface SearchAnalyticsProps {
  /**
   * Максимальное количество элементов для отображения
   */
  limit?: number;
}

/**
 * Компонент аналитики поисковых запросов
 *
 * Отображает три основных раздела:
 * 1. График трендов поисковых запросов
 * 2. Список популярных запросов
 * 3. Список запросов с нулевыми результатами
 */
export function SearchAnalytics({ limit = 10 }: SearchAnalyticsProps) {
  // Определяем, мобильное ли устройство
  const { isMobile } = useBreakpoints();

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
    </Stack>
  );
}

export default SearchAnalytics;
