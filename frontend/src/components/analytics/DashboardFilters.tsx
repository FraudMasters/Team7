// React хуки для управления состоянием и эффектами
import React, { useState, useCallback, useEffect } from 'react';
// Компоненты Material UI для создания интерфейса
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  Stack,
  Divider,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
} from '@mui/material';
// Иконки Material UI
import {
  FilterList as FilterIcon,
  RestartAlt as ResetIcon,
  Check as ApplyIcon,
  Person as PersonIcon,
  Work as WorkIcon,
} from '@mui/icons-material';
// Типы и интерфейсы
import DateRangeFilter, {
  DateRangeFilter as DateRangeFilterType,
  DateRangePreset,
} from './DateRangeFilter';
import axios from 'axios';

/**
 * Интерфейс опции рекрутера для фильтра
 */
export interface RecruiterOption {
  recruiter_id: string;
  recruiter_name: string;
}

/**
 * Интерфейс опции вакансии для фильтра
 */
export interface VacancyOption {
  uid: string;
  title: string;
  position: string;
}

/**
 * Полный интерфейс фильтров дашборда
 */
export interface DashboardFiltersState {
  dateRange: DateRangeFilterType;
  recruiterId: string | null;
  vacancyId: string | null;
}

/**
 * Свойства компонента DashboardFilters
 */
interface DashboardFiltersProps {
  /** Колбэк при изменении фильтров */
  onFiltersChange?: (filters: DashboardFiltersState) => void;
  /** Колбэк при нажатии кнопки применения */
  onApply?: (filters: DashboardFiltersState) => void;
  /** Начальные значения фильтров */
  initialFilters?: Partial<DashboardFiltersState>;
  /** Показывать фильтр по рекрутерам */
  showRecruiterFilter?: boolean;
  /** Показывать фильтр по вакансиям */
  showVacancyFilter?: boolean;
  /** Отключенное состояние */
  disabled?: boolean;
}

/**
 * Компонент DashboardFilters
 *
 * Предоставляет расширенную фильтрацию для аналитики с:
 * - Фильтрацией по диапазону дат (интеграция с DateRangeFilter)
 * - Фильтрацией по конкретному рекрутеру
 * - Фильтрацией по конкретной вакансии
 * - Кнопкой применения для запуска фильтрации
 * - Сбросом всех фильтров к значениям по умолчанию
 * - Отображением активных фильтров в виде чипов
 *
 * @example
 * ```tsx
 * <DashboardFilters
 *   onFiltersChange={(filters) => console.log('Filters:', filters)}
 *   onApply={(filters) => fetchAnalytics(filters)}
 *   showRecruiterFilter={true}
 *   showVacancyFilter={true}
 * />
 * ```
 */
const DashboardFilters: React.FC<DashboardFiltersProps> = ({
  onFiltersChange,
  onApply,
  initialFilters = {},
  showRecruiterFilter = true,
  showVacancyFilter = true,
  disabled = false,
}) => {
  // Состояние диапазона дат
  const [dateRange, setDateRange] = useState<DateRangeFilterType>(
    initialFilters.dateRange || {
      startDate: '',
      endDate: '',
      preset: 'last_30_days' as DateRangePreset,
    }
  );

  // Состояние фильтров рекрутера и вакансии
  const [recruiterId, setRecruiterId] = useState<string | null>(
    initialFilters.recruiterId || null
  );
  const [vacancyId, setVacancyId] = useState<string | null>(
    initialFilters.vacancyId || null
  );

  // Состояния для загрузки данных
  const [recruitersLoading, setRecruitersLoading] = useState(false);
  const [vacanciesLoading, setVacanciesLoading] = useState(false);
  const [recruiters, setRecruiters] = useState<RecruiterOption[]>([]);
  const [vacancies, setVacancies] = useState<VacancyOption[]>([]);

  /**
   * Загрузка списка рекрутеров
   */
  const fetchRecruiters = useCallback(async () => {
    if (!showRecruiterFilter) return;

    setRecruitersLoading(true);
    try {
      const response = await axios.get<{ recruiters: RecruiterOption[] }>(
        '/api/analytics/recruiter-performance',
        { params: { limit: 100 } }
      );

      const recruiterOptions = response.data.recruiters.map((r) => ({
        recruiter_id: r.recruiter_id,
        recruiter_name: r.recruiter_name,
      }));

      setRecruiters(recruiterOptions);
    } catch (err) {
      // Если ошибка загрузки, используем пустой список
      setRecruiters([]);
    } finally {
      setRecruitersLoading(false);
    }
  }, [showRecruiterFilter]);

  /**
   * Загрузка списка вакансий
   */
  const fetchVacancies = useCallback(async () => {
    if (!showVacancyFilter) return;

    setVacanciesLoading(true);
    try {
      const response = await axios.get<{ vacancies: VacancyOption[] }>(
        '/api/vacancies',
        { params: { limit: 100, active: true } }
      );

      setVacancies(response.data.vacancies || []);
    } catch (err) {
      // Если ошибка загрузки, используем пустой список
      setVacancies([]);
    } finally {
      setVacanciesLoading(false);
    }
  }, [showVacancyFilter]);

  // Загрузка данных при монтировании
  useEffect(() => {
    fetchRecruiters();
    fetchVacancies();
  }, [fetchRecruiters, fetchVacancies]);

  /**
   * Обработчик изменения диапазона дат
   */
  const handleDateRangeChange = useCallback(
    (newDateRange: DateRangeFilterType) => {
      setDateRange(newDateRange);
    },
    []
  );

  /**
   * Обработчик применения диапазона дат
   */
  const handleDateRangeApply = useCallback(
    (appliedDateRange: DateRangeFilterType) => {
      setDateRange(appliedDateRange);

      const filters: DashboardFiltersState = {
        dateRange: appliedDateRange,
        recruiterId,
        vacancyId,
      };

      onApply?.(filters);
    },
    [recruiterId, vacancyId, onApply]
  );

  /**
   * Обработчик изменения рекрутера
   */
  const handleRecruiterChange = useCallback(
    (event: React.ChangeEvent<{ value: unknown }>) => {
      const newRecruiterId = event.target.value as string | null;
      setRecruiterId(newRecruiterId);

      const filters: DashboardFiltersState = {
        dateRange,
        recruiterId: newRecruiterId,
        vacancyId,
      };

      onFiltersChange?.(filters);
    },
    [dateRange, vacancyId, onFiltersChange]
  );

  /**
   * Обработчик изменения вакансии
   */
  const handleVacancyChange = useCallback(
    (event: React.ChangeEvent<{ value: unknown }>) => {
      const newVacancyId = event.target.value as string | null;
      setVacancyId(newVacancyId);

      const filters: DashboardFiltersState = {
        dateRange,
        recruiterId,
        vacancyId: newVacancyId,
      };

      onFiltersChange?.(filters);
    },
    [dateRange, recruiterId, onFiltersChange]
  );

  /**
   * Обработчик применения всех фильтров
   */
  const handleApplyAll = useCallback(() => {
    const filters: DashboardFiltersState = {
      dateRange,
      recruiterId,
      vacancyId,
    };

    onApply?.(filters);
  }, [dateRange, recruiterId, vacancyId, onApply]);

  /**
   * Обработчик сброса всех фильтров
   */
  const handleResetAll = useCallback(() => {
    const defaultDateRange: DateRangeFilterType = {
      startDate: '',
      endDate: '',
      preset: 'last_30_days',
    };

    setDateRange(defaultDateRange);
    setRecruiterId(null);
    setVacancyId(null);

    const resetFilters: DashboardFiltersState = {
      dateRange: defaultDateRange,
      recruiterId: null,
      vacancyId: null,
    };

    onFiltersChange?.(resetFilters);
    onApply?.(resetFilters);
  }, [onFiltersChange, onApply]);

  /**
   * Получить название выбранного рекрутера
   */
  const getSelectedRecruiterName = (): string | null => {
    if (!recruiterId) return null;
    const recruiter = recruiters.find((r) => r.recruiter_id === recruiterId);
    return recruiter?.recruiter_name || null;
  };

  /**
   * Получить название выбранной вакансии
   */
  const getSelectedVacancyTitle = (): string | null => {
    if (!vacancyId) return null;
    const vacancy = vacancies.find((v) => v.uid === vacancyId);
    return vacancy?.title || vacancy?.position || null;
  };

  /**
   * Подсчет активных фильтров
   */
  const activeFiltersCount = [
    recruiterId ? 1 : 0,
    vacancyId ? 1 : 0,
  ].reduce((sum, count) => sum + count, 0);

  return (
    <Stack spacing={3}>
      {/* Date Range Filter */}
      <DateRangeFilter
        onDateRangeChange={handleDateRangeChange}
        onApply={handleDateRangeApply}
        initialDateRange={initialFilters.dateRange}
        showPresets={true}
        disabled={disabled}
        label="Date Range"
      />

      {/* Additional Filters */}
      {(showRecruiterFilter || showVacancyFilter) && (
        <Paper elevation={1} sx={{ p: 3 }}>
          {/* Заголовок фильтра с иконкой */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <FilterIcon sx={{ mr: 1, fontSize: 24, color: 'primary.main' }} />
            <Typography variant="h6" fontWeight={600}>
              Additional Filters
            </Typography>
            {activeFiltersCount > 0 && (
              <Chip
                label={`${activeFiltersCount} active`}
                size="small"
                color="primary"
                sx={{ ml: 2 }}
              />
            )}
          </Box>
          <Divider sx={{ mb: 2 }} />

          <Stack spacing={3}>
            {/* Recruiter Filter */}
            {showRecruiterFilter && (
              <Box>
                <Typography variant="subtitle2" gutterBottom sx={{ mb: 1.5, display: 'flex', alignItems: 'center' }}>
                  <PersonIcon sx={{ mr: 1, fontSize: 18 }} />
                  Filter by Recruiter
                </Typography>
                <FormControl fullWidth size="small" disabled={disabled || recruitersLoading}>
                  <InputLabel>Select Recruiter</InputLabel>
                  <Select
                    value={recruiterId || ''}
                    onChange={handleRecruiterChange}
                    label="Select Recruiter"
                    startAdornment={
                      recruitersLoading ? (
                        <CircularProgress size={16} sx={{ mr: 1 }} />
                      ) : null
                    }
                  >
                    <MenuItem value="">
                      <em>All Recruiters</em>
                    </MenuItem>
                    {recruiters.map((recruiter) => (
                      <MenuItem key={recruiter.recruiter_id} value={recruiter.recruiter_id}>
                        {recruiter.recruiter_name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
            )}

            {/* Vacancy Filter */}
            {showVacancyFilter && (
              <Box>
                <Typography variant="subtitle2" gutterBottom sx={{ mb: 1.5, display: 'flex', alignItems: 'center' }}>
                  <WorkIcon sx={{ mr: 1, fontSize: 18 }} />
                  Filter by Vacancy
                </Typography>
                <FormControl fullWidth size="small" disabled={disabled || vacanciesLoading}>
                  <InputLabel>Select Vacancy</InputLabel>
                  <Select
                    value={vacancyId || ''}
                    onChange={handleVacancyChange}
                    label="Select Vacancy"
                    startAdornment={
                      vacanciesLoading ? (
                        <CircularProgress size={16} sx={{ mr: 1 }} />
                      ) : null
                    }
                  >
                    <MenuItem value="">
                      <em>All Vacancies</em>
                    </MenuItem>
                    {vacancies.map((vacancy) => (
                      <MenuItem key={vacancy.uid} value={vacancy.uid}>
                        {vacancy.title || vacancy.position}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
            )}

            {/* Active Filters Display */}
            {activeFiltersCount > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Active Filters:
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {recruiterId && (
                    <Chip
                      icon={<PersonIcon fontSize="small" />}
                      label={`Recruiter: ${getSelectedRecruiterName() || recruiterId}`}
                      onDelete={() => {
                        setRecruiterId(null);
                        onFiltersChange?.({
                          dateRange,
                          recruiterId: null,
                          vacancyId,
                        });
                      }}
                      color="primary"
                      variant="outlined"
                      size="small"
                      disabled={disabled}
                    />
                  )}
                  {vacancyId && (
                    <Chip
                      icon={<WorkIcon fontSize="small" />}
                      label={`Vacancy: ${getSelectedVacancyTitle() || vacancyId}`}
                      onDelete={() => {
                        setVacancyId(null);
                        onFiltersChange?.({
                          dateRange,
                          recruiterId,
                          vacancyId: null,
                        });
                      }}
                      color="secondary"
                      variant="outlined"
                      size="small"
                      disabled={disabled}
                    />
                  )}
                </Stack>
              </Box>
            )}

            {/* Action Buttons */}
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <Button
                fullWidth
                variant="contained"
                startIcon={<ApplyIcon />}
                onClick={handleApplyAll}
                disabled={disabled}
                color="primary"
              >
                Apply All Filters
              </Button>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<ResetIcon />}
                onClick={handleResetAll}
                disabled={disabled}
                color="secondary"
              >
                Reset All Filters
              </Button>
            </Stack>

            {/* Information Alert */}
            <Alert severity="info" variant="outlined">
              <Typography variant="body2">
                <strong>Tip:</strong> Use additional filters to narrow down analytics data by
                specific recruiters or vacancies. Combine with date range filtering for more
                precise insights.
              </Typography>
            </Alert>
          </Stack>
        </Paper>
      )}
    </Stack>
  );
};

export default DashboardFilters;
