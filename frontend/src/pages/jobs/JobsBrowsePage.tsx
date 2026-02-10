// Импорт хуков React для управления состоянием
import { useState, useEffect, useCallback } from 'react';
// Импорт компонентов MUI для оформления интерфейса
import {
  Container,      // Контейнер для ограничения ширины содержимого
  Typography,     // Компонент для текста с различными стилями
  TextField,      // Поле ввода текста
  Stack,          // Контейнер для flexbox-расположения элементов
  Grid,           // Сетка для адаптивной верстки
  Paper,          // Контейнер с эффектом elevated (карточка)
  Chip,           // Метки/теги
  FormControl,    // Контейнер для элементов форм
  Select,         // Выпадающий список
  MenuItem,       // Пункт выпадающего списка
  InputLabel,     // Метка поля ввода
  CircularProgress, // Индикатор загрузки
  Box,            // Универсальный контейнер для верстки
  Autocomplete,   // Автозаполнение с выбором из списка
  Button,         // Кнопка
  createFilterOptions, // Функция для создания кастомного фильтра опций
} from '@mui/material';
// Импорт хука для интернационализации
import { useTranslation } from 'react-i18next';
// Импорт иконок из MUI
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  LocationOn,
  AttachMoney,
} from '@mui/icons-material';
// Импорт кастомного хука для поиска вакансий
import { useJobSearch } from '../../hooks/useJobSearch';
// Импорт компонента карточки вакансии
import { JobCard } from '../../components/jobs/JobCard';
// Импорт кастомного компонента Slider
import { Slider } from '../../components/ui';

// Основной компонент страницы просмотра вакансий
export function JobsBrowsePage() {
  // Хук для интернационализации
  const { t } = useTranslation();

  // Состояние для фильтров вакансий
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [filters, setFilters] = useState<{
    location?: string; // Локация вакансии
    salaryRange?: number[]; // Диапазон зарплаты [min, max]
    workFormat?: 'remote' | 'office' | 'hybrid'; // Формат работы
    employmentType?: 'full-time' | 'part-time' | 'contract'; // Тип занятости
  }>({});

  // Debounce для поискового запроса
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Опции локаций для автозаполнения
  const locationOptions = [
    'Remote', 'New York', 'San Francisco', 'Los Angeles', 'Chicago',
    'Boston', 'Seattle', 'Austin', 'Denver', 'Miami', 'Atlanta',
    'London', 'Paris', 'Berlin', 'Amsterdam', 'Barcelona', 'Rome',
    'Toronto', 'Vancouver', 'Sydney', 'Melbourne', 'Tokyo', 'Singapore',
    'Dubai', 'Tel Aviv', 'Bangalore', 'Mumbai', 'Sao Paulo',
  ];

  // Кастомный фильтр для case-insensitive поиска локаций
  const locationFilterOptions = createFilterOptions({
    matchFrom: 'any',
    limit: 100,
    stringify: (option: string) => option.toLowerCase(),
  });

  // Формирование параметров для запроса поиска
  const searchParams = useCallback(() => {
    const params: Record<string, any> = {
      query: debouncedQuery || null,
      limit: 100,
    };

    if (filters.location || filters.salaryRange || filters.workFormat || filters.employmentType) {
      params.filters = {};
      if (filters.location) params.filters.location = filters.location;
      if (filters.salaryRange) {
        params.filters.salary_min = filters.salaryRange[0];
        params.filters.salary_max = filters.salaryRange[1];
      }
      if (filters.workFormat) params.filters.work_format = filters.workFormat;
      if (filters.employmentType) params.filters.employment_type = filters.employmentType;
    }

    return params;
  }, [debouncedQuery, filters]);

  // Получение данных о вакансиях с использованием кастомного хука
  const { data, isLoading, error } = useJobSearch(searchParams());

  // Получаем результаты поиска из ответа API
  const searchResults = data?.results ?? [];
  const totalResults = data?.total ?? 0;

  // Очистка всех фильтров
  const handleClearFilters = useCallback(() => {
    setFilters({});
    setSearchQuery('');
  }, []);

  // Проверка, есть ли активные фильтры
  const hasActiveFilters = Object.keys(filters).length > 0 || searchQuery !== '';

  // Форматирование значения зарплаты для слайдера
  const formatSalary = useCallback((value: number) => {
    return `$${(value / 1000).toFixed(0)}k`;
  }, []);

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Заголовок страницы */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Find Your Next Job
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Discover opportunities matched to your skills
        </Typography>
      </Box>

      {/* Панель поиска и фильтров */}
      <Paper
        sx={{
          p: 2,           // Внутренний отступ
          mb: 4,          // Внешний отступ снизу
        }}
      >
        {/* Первая строка: поиск и кнопка очистки */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2, flexWrap: 'wrap' }}>
          {/* Поле поиска вакансий */}
          <TextField
            placeholder="Search jobs by title or keywords..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
            sx={{ flexGrow: 1, minWidth: 250 }}
          />
          {/* Кнопка очистки всех фильтров */}
          {hasActiveFilters && (
            <Button
              variant="outlined"
              size="small"
              onClick={handleClearFilters}
              startIcon={<ClearIcon />}
            >
              Clear All
            </Button>
          )}
        </Box>

        {/* Вторая строка: фильтры */}
        <Grid container spacing={2}>
          {/* Фильтр по локации */}
          <Grid item xs={12} sm={6} md={3}>
            <Autocomplete
              options={locationOptions}
              filterOptions={locationFilterOptions}
              value={filters.location || null}
              onChange={(_, newValue) => {
                setFilters({ ...filters, location: newValue || undefined });
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Location"
                  placeholder="Filter by location"
                  InputProps={{
                    ...params.InputProps,
                    startAdornment: (
                      <>
                        <LocationOn sx={{ mr: 1, color: 'text.secondary' }} />
                        {params.InputProps.startAdornment}
                      </>
                    ),
                  }}
                />
              )}
            />
          </Grid>

          {/* Фильтр по формату работы */}
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Work Format</InputLabel>
              <Select
                value={filters.workFormat || ''}
                label="Work Format"
                onChange={(e) => setFilters({ ...filters, workFormat: e.target.value as 'remote' | 'office' | 'hybrid' | undefined })}
              >
                <MenuItem value="">All Formats</MenuItem>
                <MenuItem value="remote">Remote</MenuItem>
                <MenuItem value="office">Office</MenuItem>
                <MenuItem value="hybrid">Hybrid</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Фильтр по типу занятости */}
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Employment Type</InputLabel>
              <Select
                value={filters.employmentType || ''}
                label="Employment Type"
                onChange={(e) => setFilters({ ...filters, employmentType: e.target.value as 'full-time' | 'part-time' | 'contract' | undefined })}
              >
                <MenuItem value="">All Types</MenuItem>
                <MenuItem value="full-time">Full-time</MenuItem>
                <MenuItem value="part-time">Part-time</MenuItem>
                <MenuItem value="contract">Contract</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Кнопка очистки фильтра занятости (если активен) */}
          <Grid item xs={12} sm={6} md={3}>
            {filters.employmentType && (
              <Button
                variant="outlined"
                size="small"
                onClick={() => setFilters({ ...filters, employmentType: undefined })}
                startIcon={<ClearIcon />}
                fullWidth
              >
                Clear Type
              </Button>
            )}
          </Grid>
        </Grid>

        {/* Третья строка: слайдер зарплаты */}
        <Box sx={{ mt: 2 }}>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
            <AttachMoney sx={{ color: 'text.secondary', fontSize: 20 }} />
            <Typography variant="body2" color="text.secondary">
              Salary Range
            </Typography>
            {filters.salaryRange && (
              <Chip
                label={`${formatSalary(filters.salaryRange[0])} - ${formatSalary(filters.salaryRange[1])}`}
                size="small"
                onDelete={() => setFilters({ ...filters, salaryRange: undefined })}
              />
            )}
          </Stack>
          <Slider
            range
            min={0}
            max={300000}
            step={5000}
            value={filters.salaryRange || [0, 300000]}
            onChange={(_, newValue) => {
              setFilters({ ...filters, salaryRange: newValue as number[] });
            }}
            valueLabelFormat={(value) => formatSalary(value)}
            valueLabelDisplay="auto"
            aria-label="Salary range filter"
          />
          <Stack direction="row" justifyContent="space-between" sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              ${((filters.salaryRange?.[0] ?? 0) / 1000).toFixed(0)}k
            </Typography>
            <Typography variant="caption" color="text.secondary">
              ${((filters.salaryRange?.[1] ?? 300000) / 1000).toFixed(0)}k
            </Typography>
          </Stack>
        </Box>
      </Paper>

      {/* Отображение количества результатов */}
      {!isLoading && !error && (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {totalResults} {totalResults === 1 ? 'job' : 'jobs'} found
            {hasActiveFilters && ' matching your filters'}
          </Typography>
        </Box>
      )}

      {/* Отображение состояния загрузки, ошибки или списка вакансий */}
      {isLoading ? (
        // Состояние загрузки данных
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        // Состояние ошибки при загрузке
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography color="error">Failed to load jobs</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Please try again later
          </Typography>
        </Box>
      ) : searchResults.length === 0 ? (
        // Состояние отсутствия вакансий после применения фильтров
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <FilterIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {hasActiveFilters ? 'No jobs match your filters' : 'No jobs available'}
          </Typography>
          {hasActiveFilters && (
            <Button
              variant="outlined"
              onClick={handleClearFilters}
              sx={{ mt: 2 }}
            >
              Clear Filters
            </Button>
          )}
        </Box>
      ) : (
        // Сетка с карточками вакансий
        <Grid container spacing={2}>
          {searchResults.map((job) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={job.id}>
              <JobCard job={job} />
            </Grid>
          ))}
        </Grid>
      )}
    </Container>
  );
}
