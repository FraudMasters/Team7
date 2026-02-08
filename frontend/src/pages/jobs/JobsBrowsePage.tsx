// Импорт хуков React для управления состоянием
import { useState, useEffect } from 'react';
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
} from '@mui/material';
// Импорт иконок из MUI
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
// Импорт кастомного хука для получения данных о вакансиях
import { useJobs } from '../../hooks/useJobs';
// Импорт компонента карточки вакансии
import { JobCard } from '../../components/jobs/JobCard';

// Основной компонент страницы просмотра вакансий
export function JobsBrowsePage() {
  // Состояние для текста поиска
  const [searchTerm, setSearchTerm] = useState('');
  // Состояние для фильтров вакансий
  const [filters, setFilters] = useState<{
    workFormat?: string; // Формат работы (удаленно/офис/гибрид)
    excludeSkills?: string[]; // Исключаемые навыки
  }>({});

  // Ключ localStorage для сохранения исключаемых навыков
  const EXCLUDED_SKILLS_STORAGE_KEY = 'excludedJobSkills';

  // Загрузка исключаемых навыков из localStorage при монтировании компонента
  useEffect(() => {
    try {
      const stored = localStorage.getItem(EXCLUDED_SKILLS_STORAGE_KEY);
      if (stored) {
        const excludedSkills = JSON.parse(stored) as string[];
        setFilters((prev) => ({ ...prev, excludeSkills: excludedSkills }));
      }
    } catch {
      // Игнорируем ошибки при чтении из localStorage
    }
  }, []);

  // Сохранение исключаемых навыков в localStorage при их изменении
  useEffect(() => {
    try {
      if (filters.excludeSkills && filters.excludeSkills.length > 0) {
        localStorage.setItem(EXCLUDED_SKILLS_STORAGE_KEY, JSON.stringify(filters.excludeSkills));
      } else {
        localStorage.removeItem(EXCLUDED_SKILLS_STORAGE_KEY);
      }
    } catch {
      // Игнорируем ошибки при записи в localStorage
    }
  }, [filters.excludeSkills]);

  // Получение данных о вакансиях с использованием кастомного хука
  const { data, isLoading, error } = useJobs();

  // Доступные опции навыков (в будущем могут быть получены из API)
  const skillOptions = [
    'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue.js',
    'Node.js', 'Django', 'Flask', 'Spring', 'AWS', 'Azure', 'Docker', 'Kubernetes',
    'SQL', 'PostgreSQL', 'MongoDB', 'Redis', 'GraphQL', 'REST', 'Git', 'CI/CD',
  ];

  // Фильтрация вакансий по поисковому запросу и выбранным фильтрам
  const filteredJobs = data?.vacancies.filter((job) => {
    // Проверка совпадения поискового запроса с названием или описанием вакансии
    const matchesSearch =
      searchTerm === '' ||
      job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.description.toLowerCase().includes(searchTerm.toLowerCase());

    // Проверка совпадения формата работы
    const matchesFormat = !filters.workFormat || job.work_format === filters.workFormat;

    // Проверка исключаемых навыков - вакансии, требующие эти навыки, исключаются
    const matchesExcludeSkills =
      !filters.excludeSkills ||
      filters.excludeSkills.length === 0 ||
      !filters.excludeSkills.some((skill) =>
        job.required_skills?.some((jobSkill: string) =>
          jobSkill.toLowerCase().includes(skill.toLowerCase())
        )
      );

    // Возвращаем вакансию, если она соответствует всем критериям
    return matchesSearch && matchesFormat && matchesExcludeSkills;
  }) ?? [];

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
          display: 'flex',
          gap: 2,         // Расстояние между элементами
          alignItems: 'center',
          flexWrap: 'wrap', // Перенос элементов на новую строку
        }}
      >
        {/* Поле поиска вакансий */}
        <TextField
          placeholder="Search jobs..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
          sx={{ flexGrow: 1, minWidth: 200 }}
        />
        {/* Выпадающий список для выбора формата работы */}
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Work Format</InputLabel>
          <Select
            value={filters.workFormat || ''}
            label="Work Format"
            onChange={(e) => setFilters({ ...filters, workFormat: e.target.value || undefined })}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="remote">Remote</MenuItem>
            <MenuItem value="office">Office</MenuItem>
            <MenuItem value="hybrid">Hybrid</MenuItem>
          </Select>
        </FormControl>
        {/* Автозаполнение для исключаемых навыков с кнопкой очистки */}
        <Stack direction="row" spacing={1} alignItems="center">
          <Autocomplete
            multiple
            options={skillOptions}
            value={filters.excludeSkills || []}
            onChange={(_, newValue) => setFilters({ ...filters, excludeSkills: newValue })}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip
                  variant="outlined"
                  label={option}
                  {...getTagProps({ index })}
                  key={option}
                />
              ))
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="Exclude Skills"
                placeholder="Select skills to exclude"
              />
            )}
            sx={{ minWidth: 250 }}
          />
          {filters.excludeSkills && filters.excludeSkills.length > 0 && (
            <Button
              variant="outlined"
              size="small"
              onClick={() => setFilters({ ...filters, excludeSkills: [] })}
              startIcon={<ClearIcon />}
            >
              Clear
            </Button>
          )}
        </Stack>
      </Paper>

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
        </Box>
      ) : filteredJobs.length === 0 ? (
        // Состояние отсутствия вакансий
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography color="text.secondary">No jobs found</Typography>
        </Box>
      ) : (
        // Сетка с карточками вакансий
        <Grid container spacing={2}>
          {filteredJobs.map((job) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={job.id}>
              <JobCard job={job} />
            </Grid>
          ))}
        </Grid>
      )}
    </Container>
  );
}
