/**
 * Страница бенчмаркинга зарплат
 *
 * Инструмент для сравнения зарплат с рыночными данными:
 * - Поиск по должности и локации
 * - Сравнение с конкурентами
 * - Исторические тренды зарплат
 * - Экспорт отчетов
 */

// Импорт хуков React
import { useState } from 'react';

// Импорт компонентов MUI
import {
  Box,
  Container,
  Typography,
  Paper,
  Stack,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Chip,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Snackbar,
  LinearProgress,
} from '@mui/material';

// Импорт иконок MUI
import {
  Search as SearchIcon,
  Download as DownloadIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Work as WorkIcon,
  LocationOn as LocationIcon,
  Error as ErrorIcon,
  ShowChart as ShowChartIcon,
  ArrowUpward as ArrowUpIcon,
  ArrowDownward as ArrowDownIcon,
} from '@mui/icons-material';

// Импорт API клиента
import { salaryBenchmarking } from '@/api/salaryBenchmarking';
import type { SalaryBenchmarkResponse, MarketTrendsResponse, ApiError } from '@/types/api';

/**
 * Страница бенчмаркинга зарплат
 */
export function SalaryBenchmarkingPage() {
  // Состояние поисковых параметров
  const [searchPosition, setSearchPosition] = useState('');
  const [searchLocation, setSearchLocation] = useState('');

  // Состояние загрузки
  const [loading, setLoading] = useState(false);

  // Состояние загрузки трендов
  const [trendsLoading, setTrendsLoading] = useState(false);

  // Состояние результатов поиска
  const [searchResults, setSearchResults] = useState<SalaryBenchmarkResponse[]>([]);

  // Состояние данных о трендах рынка
  const [marketTrends, setMarketTrends] = useState<MarketTrendsResponse | null>(null);

  // Состояние ошибки
  const [error, setError] = useState<string | null>(null);

  // Обработчик поиска
  const handleSearch = async () => {
    if (!searchPosition || !searchLocation) {
      return;
    }

    setLoading(true);
    setTrendsLoading(true);
    setError(null);

    try {
      // Fetch benchmarks and trends in parallel
      const [benchmarks, trends] = await Promise.all([
        salaryBenchmarking.getBenchmarks({
          role: searchPosition,
          location: searchLocation,
        }),
        salaryBenchmarking.getMarketTrends({
          role: searchPosition,
          location: searchLocation,
          period_type: 'quarterly',
          periods: 8,
        }).catch(() => null), // Gracefully handle trends failure
      ]);

      setSearchResults(benchmarks);
      setMarketTrends(trends);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to fetch salary benchmarks');
      setSearchResults([]);
      setMarketTrends(null);
    } finally {
      setLoading(false);
      setTrendsLoading(false);
    }
  };

  // Обработчик экспорта
  const handleExport = () => {
    if (searchResults.length === 0) {
      return;
    }

    // Create CSV content
    const headers = ['Position', 'Location', '25th Percentile', 'Median', '75th Percentile', '90th Percentile', 'Currency', 'Sample Size'];
    const rows = searchResults.map((result) => [
      result.role,
      result.location,
      result.salary_min,
      result.salary_median,
      result.salary_max,
      result.salary_p90 || '',
      result.currency,
      result.sample_size || '',
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.join(',')),
    ].join('\n');

    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `salary-benchmarks-${new Date().toISOString().split('T')[0]}.csv`);
    link.click();
    URL.revokeObjectURL(url);
  };

  // Обработчик закрытия уведомления об ошибке
  const handleCloseError = () => {
    setError(null);
  };

  // Обработчик нажатия Enter в поле ввода
  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && searchPosition && searchLocation) {
      handleSearch();
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      <Stack spacing={4}>
        {/* Заголовок страницы */}
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Salary Benchmarking
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Compare salaries against market data from multiple sources
          </Typography>
        </Box>

        {/* Форма поиска */}
        <Paper sx={{ p: 3 }}>
          <Grid container spacing={2} alignItems="flex-end">
            <Grid item xs={12} md={5}>
              <TextField
                fullWidth
                label="Position"
                placeholder="e.g., Senior React Developer"
                value={searchPosition}
                onChange={(e) => setSearchPosition(e.target.value)}
                onKeyPress={handleKeyPress}
                InputProps={{
                  startAdornment: <WorkIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            <Grid item xs={12} md={5}>
              <TextField
                fullWidth
                label="Location"
                placeholder="e.g., Remote, San Francisco"
                value={searchLocation}
                onChange={(e) => setSearchLocation(e.target.value)}
                onKeyPress={handleKeyPress}
                InputProps={{
                  startAdornment: <LocationIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                fullWidth
                variant="contained"
                size="large"
                startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
                onClick={handleSearch}
                disabled={!searchPosition || !searchLocation || loading}
              >
                Search
              </Button>
            </Grid>
          </Grid>
        </Paper>

        {/* Уведомление об ошибке */}
        <Snackbar
          open={!!error}
          autoHideDuration={6000}
          onClose={handleCloseError}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert severity="error" onClose={handleCloseError} icon={<ErrorIcon />}>
            {error}
          </Alert>
        </Snackbar>

        {/* Результаты поиска */}
        {!loading && searchResults.length === 0 && !error && (
          <Paper sx={{ p: 8, textAlign: 'center' }}>
            <SearchIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Search Salary Data
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Enter a position and location to see benchmark data
            </Typography>
          </Paper>
        )}

        {/* Состояние загрузки */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        )}

        {/* Отображение результатов */}
        {!loading && searchResults.length > 0 && (
          <>
            {/* Панель действий */}
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Typography variant="h6" fontWeight={600}>
                Found {searchResults.length} benchmark results
              </Typography>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={handleExport}
              >
                Export Data
              </Button>
            </Stack>

            {/* Карточки результатов */}
            <Grid container spacing={3}>
              {searchResults.map((result, index) => (
                <Grid item xs={12} md={6} lg={4} key={index}>
                  <Card>
                    <CardContent>
                      <Stack spacing={3}>
                        {/* Заголовок */}
                        <Box>
                          <Typography variant="h6" noWrap gutterBottom>
                            {result.role}
                          </Typography>
                          <Stack direction="row" spacing={1} alignItems="center">
                            <LocationIcon fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary">
                              {result.location}
                            </Typography>
                          </Stack>
                        </Box>

                        {/* Процентили */}
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>
                            Salary Percentiles (Annual)
                          </Typography>
                          <Stack spacing={1.5}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="caption" color="text.secondary">25th</Typography>
                              <Typography variant="body2" fontWeight={500}>
                                ${result.salary_min.toLocaleString()}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', bgcolor: 'grey.50', p: 1, borderRadius: 1 }}>
                              <Typography variant="caption" color="text.secondary">Median (50th)</Typography>
                              <Typography variant="body1" fontWeight={600} color="primary.main">
                                ${result.salary_median.toLocaleString()}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="caption" color="text.secondary">75th</Typography>
                              <Typography variant="body2" fontWeight={500}>
                                ${result.salary_max.toLocaleString()}
                              </Typography>
                            </Box>
                            {result.salary_p90 && (
                              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="caption" color="text.secondary">90th</Typography>
                                <Typography variant="body2" fontWeight={500}>
                                  ${result.salary_p90.toLocaleString()}
                                </Typography>
                              </Box>
                            )}
                          </Stack>
                        </Box>

                        {/* Метаданные */}
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                          {result.sample_size && (
                            <Chip
                              size="small"
                              label={`Sample: ${result.sample_size}`}
                              variant="outlined"
                            />
                          )}
                          {result.effective_date && (
                            <Chip
                              size="small"
                              icon={<TrendingUpIcon fontSize="small" />}
                              label={`Updated: ${new Date(result.effective_date).toLocaleDateString()}`}
                              variant="outlined"
                            />
                          )}
                        </Stack>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            {/* Таблица сравнения */}
            <Paper>
              <Box sx={{ p: 2 }}>
                <Typography variant="h6" fontWeight={600}>
                  Comparison Table
                </Typography>
              </Box>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Position</TableCell>
                      <TableCell>Location</TableCell>
                      <TableCell align="right">25th</TableCell>
                      <TableCell align="right">Median</TableCell>
                      <TableCell align="right">75th</TableCell>
                      <TableCell align="right">90th</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {searchResults.map((result, index) => (
                      <TableRow key={index}>
                        <TableCell>{result.role}</TableCell>
                        <TableCell>{result.location}</TableCell>
                        <TableCell align="right">${result.salary_min.toLocaleString()}</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 600, color: 'primary.main' }}>
                          ${result.salary_median.toLocaleString()}
                        </TableCell>
                        <TableCell align="right">${result.salary_max.toLocaleString()}</TableCell>
                        <TableCell align="right">
                          {result.salary_p90 ? `$${result.salary_p90.toLocaleString()}` : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>

            {/* Market Trends Section */}
            {marketTrends && marketTrends.trends.length > 0 && (
              <Paper sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ShowChartIcon color="primary" />
                    <Typography variant="h6" fontWeight={600}>
                      Market Trends
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {marketTrends.role} • {marketTrends.location}
                  </Typography>
                </Box>

                {/* Trend Summary Cards */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  {marketTrends.year_over_year_change !== undefined && (
                    <Grid item xs={6} md={3}>
                      <Card variant="outlined">
                        <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                          <Typography variant="caption" color="text.secondary" display="block">
                            Year-over-Year
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5, mt: 1 }}>
                            {marketTrends.year_over_year_change >= 0 ? (
                              <ArrowUpIcon fontSize="small" color="success" />
                            ) : (
                              <ArrowDownIcon fontSize="small" color="error" />
                            )}
                            <Typography
                              variant="h6"
                              fontWeight={700}
                              color={marketTrends.year_over_year_change >= 0 ? 'success.main' : 'error.main'}
                            >
                              {marketTrends.year_over_year_change >= 0 ? '+' : ''}
                              {marketTrends.year_over_year_change.toFixed(1)}%
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                  {marketTrends.quarter_over_quarter_change !== undefined && (
                    <Grid item xs={6} md={3}>
                      <Card variant="outlined">
                        <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                          <Typography variant="caption" color="text.secondary" display="block">
                            Quarter-over-Quarter
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5, mt: 1 }}>
                            {marketTrends.quarter_over_quarter_change >= 0 ? (
                              <ArrowUpIcon fontSize="small" color="success" />
                            ) : (
                              <ArrowDownIcon fontSize="small" color="error" />
                            )}
                            <Typography
                              variant="h6"
                              fontWeight={700}
                              color={marketTrends.quarter_over_quarter_change >= 0 ? 'success.main' : 'error.main'}
                            >
                              {marketTrends.quarter_over_quarter_change >= 0 ? '+' : ''}
                              {marketTrends.quarter_over_quarter_change.toFixed(1)}%
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                  <Grid item xs={6} md={3}>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                        <Typography variant="caption" color="text.secondary" display="block">
                          Latest Median
                        </Typography>
                        <Typography variant="h6" fontWeight={700} color="primary.main" sx={{ mt: 1 }}>
                          ${marketTrends.trends[marketTrends.trends.length - 1]?.salary_median.toLocaleString() || 'N/A'}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                        <Typography variant="caption" color="text.secondary" display="block">
                          Periods Analyzed
                        </Typography>
                        <Typography variant="h6" fontWeight={700} sx={{ mt: 1 }}>
                          {marketTrends.trends.length}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                {/* Trends Timeline */}
                <Typography variant="subtitle2" gutterBottom sx={{ mb: 2 }}>
                  Salary Trend Over Time ({marketTrends.period_type})
                </Typography>

                {/* Get max salary for percentage calculations */}
                {(() => {
                  const maxSalary = Math.max(...marketTrends.trends.map(t => t.salary_max));
                  const minSalary = Math.min(...marketTrends.trends.map(t => t.salary_min));
                  const range = maxSalary - minSalary;

                  return (
                    <Stack spacing={2}>
                      {marketTrends.trends.map((trend, index) => {
                        const isFirst = index === 0;
                        const isLast = index === marketTrends.trends.length - 1;
                        const prevTrend = index > 0 ? marketTrends.trends[index - 1] : null;
                        const changeFromPrev = prevTrend
                          ? ((trend.salary_median - prevTrend.salary_median) / prevTrend.salary_median) * 100
                          : 0;

                        return (
                          <Card
                            key={trend.period}
                            variant="outlined"
                            sx={{
                              transition: 'all 0.2s',
                              borderLeft: isLast ? '3px solid' : '1px solid',
                              borderLeftColor: isLast ? 'primary.main' : 'divider',
                              bgcolor: isLast ? 'action.hover' : 'background.paper',
                            }}
                          >
                            <CardContent sx={{ py: 1.5 }}>
                              <Grid container spacing={2} alignItems="center">
                                {/* Period */}
                                <Grid item xs={3} sm={2}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                    {isLast && <Chip label="Latest" size="small" color="primary" sx={{ height: 20, fontSize: '0.65rem' }} />}
                                    <Typography variant="body2" fontWeight={isLast ? 600 : 400}>
                                      {trend.period}
                                    </Typography>
                                  </Box>
                                </Grid>

                                {/* Salary Range Bars */}
                                <Grid item xs={6} sm={7}>
                                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                    {/* Visual bar showing salary range */}
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                      <Box sx={{ flexGrow: 1, position: 'relative' }}>
                                        <LinearProgress
                                          variant="determinate"
                                          value={(trend.salary_median / maxSalary) * 100}
                                          sx={{
                                            height: 10,
                                            borderRadius: 1,
                                            bgcolor: 'action.hover',
                                            '& .MuiLinearProgress-bar': {
                                              bgcolor: isLast ? 'primary.main' : 'primary.light',
                                              borderRadius: 1,
                                            },
                                          }}
                                        />
                                      </Box>
                                    </Box>
                                    {/* Salary values */}
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                      <Typography variant="caption" color="text.secondary">
                                        ${trend.salary_min.toLocaleString()}
                                      </Typography>
                                      <Typography variant="body2" fontWeight={600} color="primary.main">
                                        ${trend.salary_median.toLocaleString()}
                                      </Typography>
                                      <Typography variant="caption" color="text.secondary">
                                        ${trend.salary_max.toLocaleString()}
                                      </Typography>
                                    </Box>
                                  </Box>
                                </Grid>

                                {/* Change indicator */}
                                <Grid item xs={3} sm={3}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                                    {prevTrend && (
                                      <>
                                        {changeFromPrev >= 0 ? (
                                          <TrendingUpIcon fontSize="small" color="success" />
                                        ) : (
                                          <TrendingDownIcon fontSize="small" color="error" />
                                        )}
                                        <Typography
                                          variant="body2"
                                          fontWeight={600}
                                          color={changeFromPrev >= 0 ? 'success.main' : 'error.main'}
                                        >
                                          {changeFromPrev >= 0 ? '+' : ''}{changeFromPrev.toFixed(1)}%
                                        </Typography>
                                      </>
                                    )}
                                    {trend.sample_size && (
                                      <Chip
                                        label={`n=${trend.sample_size}`}
                                        size="small"
                                        variant="outlined"
                                        sx={{ height: 20, fontSize: '0.65rem', ml: 1 }}
                                      />
                                    )}
                                  </Box>
                                </Grid>
                              </Grid>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </Stack>
                  );
                })()}

                {marketTrends.data_source && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', textAlign: 'right' }}>
                    Data source: {marketTrends.data_source}
                    {marketTrends.last_updated && ` • Last updated: ${new Date(marketTrends.last_updated).toLocaleDateString()}`}
                  </Typography>
                )}
              </Paper>
            )}

            {/* Trends Loading State */}
            {trendsLoading && (
              <Paper sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2, py: 4 }}>
                  <CircularProgress size={24} />
                  <Typography color="text.secondary">Loading market trends...</Typography>
                </Box>
              </Paper>
            )}
          </>
        )}
      </Stack>
    </Container>
  );
}

export default SalaryBenchmarkingPage;
