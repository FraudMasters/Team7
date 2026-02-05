/**
 * Страница бенчмаркинга зарплат
 *
 * Инструмент для сравнения зарплат с рыночными данными:
 * - Поиск по должности и локации
 * - Сравнение с конкурентами
 * - Исторические тренды зарплат
 * - Экспорт отчетов
 */

// Импорт хука состояния React
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';

// Импорт иконок MUI
import {
  Search as SearchIcon,
  Download as DownloadIcon,
  TrendingUp as TrendingUpIcon,
  Work as WorkIcon,
  LocationOn as LocationIcon,
} from '@mui/icons-material';

// Интерфейс для данных бенчмарка
interface BenchmarkData {
  position: string;
  location: string;
  p25: number;
  p50: number;
  p75: number;
  p90: number;
  currency: string;
  sample_size: number;
  last_updated: string;
}

/**
 * Страница бенчмаркинга зарплат
 */
export function SalaryBenchmarkingPage() {
  // Состояние поисковых параметров
  const [searchPosition, setSearchPosition] = useState('');
  const [searchLocation, setSearchLocation] = useState('');

  // Состояние загрузки
  const [loading, setLoading] = useState(false);

  // Состояние результатов поиска
  const [searchResults, setSearchResults] = useState<BenchmarkData[]>([]);

  // Тестовые данные бенчмарка
  const mockResults: BenchmarkData[] = [
    {
      position: 'Senior React Developer',
      location: 'Remote, US',
      p25: 95000,
      p50: 115000,
      p75: 140000,
      p90: 165000,
      currency: 'USD',
      sample_size: 245,
      last_updated: '2025-01-15',
    },
    {
      position: 'Senior React Developer',
      location: 'San Francisco, CA',
      p25: 130000,
      p50: 155000,
      p75: 185000,
      p90: 220000,
      currency: 'USD',
      sample_size: 89,
      last_updated: '2025-01-15',
    },
    {
      position: 'Product Manager',
      location: 'Remote, US',
      p25: 105000,
      p50: 130000,
      p75: 160000,
      p90: 190000,
      currency: 'USD',
      sample_size: 178,
      last_updated: '2025-01-15',
    },
  ];

  // Обработчик поиска
  const handleSearch = () => {
    setLoading(true);
    // Имитация API вызова
    setTimeout(() => {
      setSearchResults(mockResults);
      setLoading(false);
    }, 1000);
  };

  // Обработчик экспорта
  const handleExport = () => {
    console.log('Exporting benchmark data...');
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
                disabled={!searchPosition || loading}
              >
                Search
              </Button>
            </Grid>
          </Grid>
        </Paper>

        {/* Результаты поиска */}
        {!loading && searchResults.length === 0 && (
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
                            {result.position}
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
                                ${result.p25.toLocaleString()}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', bgcolor: 'grey.50', p: 1, borderRadius: 1 }}>
                              <Typography variant="caption" color="text.secondary">Median (50th)</Typography>
                              <Typography variant="body1" fontWeight={600} color="primary.main">
                                ${result.p50.toLocaleString()}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="caption" color="text.secondary">75th</Typography>
                              <Typography variant="body2" fontWeight={500}>
                                ${result.p75.toLocaleString()}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="caption" color="text.secondary">90th</Typography>
                              <Typography variant="body2" fontWeight={500}>
                                ${result.p90.toLocaleString()}
                              </Typography>
                            </Box>
                          </Stack>
                        </Box>

                        {/* Метаданные */}
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                          <Chip
                            size="small"
                            label={`Sample: ${result.sample_size}`}
                            variant="outlined"
                          />
                          <Chip
                            size="small"
                            icon={<TrendingUpIcon fontSize="small" />}
                            label={`Updated: ${new Date(result.last_updated).toLocaleDateString()}`}
                            variant="outlined"
                          />
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
                        <TableCell>{result.position}</TableCell>
                        <TableCell>{result.location}</TableCell>
                        <TableCell align="right">${result.p25.toLocaleString()}</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 600, color: 'primary.main' }}>
                          ${result.p50.toLocaleString()}
                        </TableCell>
                        <TableCell align="right">${result.p75.toLocaleString()}</TableCell>
                        <TableCell align="right">${result.p90.toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </>
        )}
      </Stack>
    </Container>
  );
}

export default SalaryBenchmarkingPage;
