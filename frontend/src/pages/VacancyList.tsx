import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Chip,
  Stack,
  Grid2,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Collapse,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Work as WorkIcon,
  Search as SearchIcon,
  FilterList as FilterListIcon,
  ExpandMore as ExpandMoreIcon,
  Clear as ClearIcon,
  Save as SaveIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBoundary from '../components/ErrorBoundary';
import ErrorMessage, { ErrorType, ErrorAction } from '../components/ErrorMessage';
import useKeyboardNavigation from '../hooks/useKeyboardNavigation';
import { useInfiniteScroll } from '../hooks/useInfiniteScroll';

interface Vacancy {
  id: string;
  title: string;
  description: string;
  required_skills: string[];
  min_experience_months: number;
  additional_requirements: string[];
  industry?: string;
  work_format?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  english_level?: string;
  employment_type?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Paginated response from vacancies list endpoint
 * Matches backend VacancyListResponse model with total count
 */
interface VacancyListResponse {
  total: number;
  vacancies: Vacancy[];
}

// Zod validation schema for inline vacancy edit
const vacancyEditSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  required_skills: z.array(z.string()).min(1, 'At least one skill is required'),
  min_experience_months: z.number().min(0, 'Experience cannot be negative'),
  salary_min: z.number().nullable().optional(),
  salary_max: z.number().nullable().optional(),
  industry: z.string().optional(),
  work_format: z.string().optional(),
  location: z.string().optional(),
  english_level: z.string().optional(),
  employment_type: z.string().optional(),
}).refine((data) => {
  if (data.salary_min && data.salary_max && data.salary_min > data.salary_max) {
    return false;
  }
  return true;
}, {
  message: 'Minimum salary cannot be greater than maximum salary',
  path: ['salary_min'],
});

type VacancyEditFormData = z.infer<typeof vacancyEditSchema>;

const VacancyList: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [vacancies, setVacancies] = useState<Vacancy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | ErrorType | string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [vacancyToDelete, setVacancyToDelete] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVacancyIndex, setSelectedVacancyIndex] = useState<number>(-1);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Inline editing state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingVacancy, setEditingVacancy] = useState<Vacancy | null>(null);
  const [saveError, setSaveError] = useState<Error | ErrorType | string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Filter states
  const [workFormatFilter, setWorkFormatFilter] = useState<string>('all');
  const [locationFilter, setLocationFilter] = useState<string>('');
  const [dateFromFilter, setDateFromFilter] = useState<string>('');
  const [dateToFilter, setDateToFilter] = useState<string>('');
  const [filtersExpanded, setFiltersExpanded] = useState(false);

  // Pagination state
  const [skip, setSkip] = useState<number>(0);
  const [limit] = useState<number>(20);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);

  // Infinite scroll hook - disabled when filters are active
  const { ref: scrollRef, isNearBottom } = useInfiniteScroll({
    threshold: 200,
    enabled: !hasActiveFilters && hasMore && !loading && !loadingMore,
  });

  // Filter vacancies based on search query and filters
  const filteredVacancies = vacancies.filter((vacancy) => {
    // Search query filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const matchesSearch =
        vacancy.title.toLowerCase().includes(query) ||
        vacancy.description.toLowerCase().includes(query) ||
        vacancy.required_skills.some((skill) => skill.toLowerCase().includes(query)) ||
        vacancy.industry?.toLowerCase().includes(query) ||
        vacancy.location?.toLowerCase().includes(query);

      if (!matchesSearch) return false;
    }

    // Work format filter
    if (workFormatFilter !== 'all') {
      if (vacancy.work_format !== workFormatFilter) return false;
    }

    // Location filter
    if (locationFilter.trim()) {
      if (!vacancy.location?.toLowerCase().includes(locationFilter.toLowerCase())) {
        return false;
      }
    }

    // Date range filter
    if (dateFromFilter) {
      const vacancyDate = new Date(vacancy.created_at);
      const fromDate = new Date(dateFromFilter);
      if (vacancyDate < fromDate) return false;
    }

    if (dateToFilter) {
      const vacancyDate = new Date(vacancy.created_at);
      const toDate = new Date(dateToFilter);
      toDate.setHours(23, 59, 59, 999); // End of day
      if (vacancyDate > toDate) return false;
    }

    return true;
  });

  // Check if any filters are active
  const hasActiveFilters =
    workFormatFilter !== 'all' ||
    locationFilter.trim() !== '' ||
    dateFromFilter !== '' ||
    dateToFilter !== '';

  // Clear all filters
  const handleClearFilters = useCallback(() => {
    setWorkFormatFilter('all');
    setLocationFilter('');
    setDateFromFilter('');
    setDateToFilter('');
  }, []);

  /**
   * Keyboard navigation handlers
   */
  const handleNextVacancy = useCallback(() => {
    if (filteredVacancies.length > 0) {
      setSelectedVacancyIndex((prev) => {
        if (prev < filteredVacancies.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }
  }, [filteredVacancies.length]);

  const handlePreviousVacancy = useCallback(() => {
    if (filteredVacancies.length > 0) {
      setSelectedVacancyIndex((prev) => {
        if (prev > 0) {
          return prev - 1;
        }
        return prev;
      });
    }
  }, [filteredVacancies.length]);

  const handleViewVacancy = useCallback(() => {
    if (selectedVacancyIndex >= 0) {
      const selectedVacancy = filteredVacancies[selectedVacancyIndex];
      if (selectedVacancy) {
        navigate(`${selectedVacancy.id}`);
      }
    }
  }, [selectedVacancyIndex, filteredVacancies, navigate]);

  const handleClearSelection = useCallback(() => {
    setSelectedVacancyIndex(-1);
    setSearchQuery('');
  }, []);

  const handleCreateVacancy = useCallback(() => {
    navigate('/vacancies/create');
  }, [navigate]);

  const handleFocusSearch = useCallback(() => {
    searchInputRef.current?.focus();
  }, []);

  /**
   * Register keyboard shortcuts using useKeyboardNavigation hook
   * - Ctrl+N: Create new vacancy
   * - Ctrl+F: Focus search field
   * - Arrow Down/Right: Navigate to next vacancy
   * - Arrow Up/Left: Navigate to previous vacancy
   * - Enter: View selected vacancy details
   * - Escape: Clear selection or search
   */
  useKeyboardNavigation({
    shortcuts: [
      {
        id: 'createVacancy',
        key: 'n',
        modifiers: ['Ctrl'],
        handler: handleCreateVacancy,
        description: 'Create new vacancy',
        priority: 10,
        when: () => !deleteDialogOpen,
      },
      {
        id: 'focusSearch',
        key: 'f',
        modifiers: ['Ctrl'],
        handler: handleFocusSearch,
        description: 'Focus search field',
        priority: 10,
      },
      {
        id: 'nextVacancyDown',
        key: 'ArrowDown',
        handler: handleNextVacancy,
        description: 'Navigate to next vacancy',
        priority: 5,
        when: () => !deleteDialogOpen && filteredVacancies.length > 0,
      },
      {
        id: 'nextVacancyRight',
        key: 'ArrowRight',
        handler: handleNextVacancy,
        description: 'Navigate to next vacancy',
        priority: 5,
        when: () => {
          const target = document.activeElement as HTMLElement;
          return !deleteDialogOpen && filteredVacancies.length > 0 && target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA';
        },
      },
      {
        id: 'previousVacancyUp',
        key: 'ArrowUp',
        handler: handlePreviousVacancy,
        description: 'Navigate to previous vacancy',
        priority: 5,
        when: () => !deleteDialogOpen && filteredVacancies.length > 0,
      },
      {
        id: 'previousVacancyLeft',
        key: 'ArrowLeft',
        handler: handlePreviousVacancy,
        description: 'Navigate to previous vacancy',
        priority: 5,
        when: () => {
          const target = document.activeElement as HTMLElement;
          return !deleteDialogOpen && filteredVacancies.length > 0 && target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA';
        },
      },
      {
        id: 'viewVacancy',
        key: 'Enter',
        handler: handleViewVacancy,
        description: 'View selected vacancy details',
        priority: 5,
        when: () => !deleteDialogOpen && selectedVacancyIndex >= 0,
      },
      {
        id: 'clearSelection',
        key: 'Escape',
        handler: handleClearSelection,
        description: 'Clear selection or search',
        priority: 5,
        when: () => !deleteDialogOpen,
      },
    ],
  });

  // Reset selected index when filtered vacancies change
  useEffect(() => {
    setSelectedVacancyIndex((prev) => {
      if (prev >= filteredVacancies.length) {
        return Math.max(0, filteredVacancies.length - 1);
      }
      return prev;
    });
  }, [filteredVacancies.length]);

  // Trigger load more when user scrolls near bottom
  useEffect(() => {
    if (isNearBottom && !hasActiveFilters && hasMore && !loading && !loadingMore) {
      loadMore();
    }
  }, [isNearBottom, hasActiveFilters, hasMore, loading, loadingMore, loadMore]);

  useEffect(() => {
    fetchVacancies(0, limit);
  }, [limit]);

  /**
   * Fetch vacancies with pagination support
   * @param skip - Number of records to skip
   * @param limit - Maximum number of records to return
   * @param append - Whether to append results to existing vacancies (for load more)
   */
  const fetchVacancies = async (skip: number, limit: number, append: boolean = false) => {
    // Set appropriate loading state
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
      setError(null);
    }

    try {
      const response = await fetch(`/api/vacancies/?skip=${skip}&limit=${limit}`);

      if (!response.ok) {
        throw new Error('Failed to fetch vacancies');
      }

      const data: VacancyListResponse = await response.json();

      // Update vacancies list
      if (append) {
        setVacancies((prev) => [...prev, ...data.vacancies]);
      } else {
        setVacancies(data.vacancies);
      }

      // Update pagination state
      setSkip(skip + limit);
      setHasMore(skip + limit < data.total);
    } catch (err) {
      setError(err instanceof Error ? err : 'Failed to fetch vacancies');
    } finally {
      if (append) {
        setLoadingMore(false);
      } else {
        setLoading(false);
      }
    }
  };

  /**
   * Load more vacancies when scrolling near bottom
   */
  const loadMore = useCallback(() => {
    if (loadingMore || !hasMore || loading) {
      return;
    }
    fetchVacancies(skip, limit, true);
  }, [loadingMore, hasMore, loading, skip, limit]);

  const handleDeleteClick = (id: string) => {
    setVacancyToDelete(id);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!vacancyToDelete) return;

    try {
      const response = await fetch(`/api/vacancies/${vacancyToDelete}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete vacancy');
      }

      // Remove from list
      setVacancies(vacancies.filter((v) => v.id !== vacancyToDelete));
      setDeleteDialogOpen(false);
      setVacancyToDelete(null);
    } catch (err) {
      setError(err instanceof Error ? err : 'Failed to delete vacancy');
    }
  };

  // Inline edit handlers
  const handleEditClick = useCallback((vacancy: Vacancy) => {
    setEditingVacancy(vacancy);
    setEditDialogOpen(true);
    setSaveError(null);
  }, []);

  const handleEditDialogClose = useCallback(() => {
    setEditDialogOpen(false);
    setEditingVacancy(null);
    setSaveError(null);
    // Clear draft from localStorage
    try {
      localStorage.removeItem('vacancy-edit-draft');
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const handleSaveVacancy = async (data: VacancyEditFormData) => {
    if (!editingVacancy) return;

    setIsSaving(true);
    setSaveError(null);

    try {
      const response = await fetch(`/api/vacancies/${editingVacancy.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to update vacancy');
      }

      const updatedVacancy: Vacancy = await response.json();

      // Update vacancy in list without page reload
      setVacancies((prev) =>
        prev.map((v) => (v.id === updatedVacancy.id ? updatedVacancy : v))
      );

      // Clear draft from localStorage
      try {
        localStorage.removeItem('vacancy-edit-draft');
      } catch {
        // Ignore localStorage errors
      }

      handleEditDialogClose();
    } catch (err) {
      setSaveError(err instanceof Error ? err : 'Failed to update vacancy');
    } finally {
      setIsSaving(false);
    }
  };

  const formatSalary = (min?: number, max?: number) => {
    if (min && max) {
      return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    }
    if (min) {
      return t('vacancyList.salary.from', { amount: min.toLocaleString() });
    }
    if (max) {
      return t('vacancyList.salary.to', { amount: max.toLocaleString() });
    }
    return t('vacancyList.salary.notSpecified');
  };

  const formatExperience = (months: number) => {
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;

    if (years === 0) {
      return `${remainingMonths} мес.`;
    }
    if (remainingMonths === 0) {
      return `${years} ${getYearWord(years)}`;
    }
    return `${years} ${getYearWord(years)} ${remainingMonths} мес.`;
  };

  const getYearWord = (years: number) => {
    const lastTwo = years % 100;
    const lastOne = years % 10;

    if (lastTwo >= 11 && lastTwo <= 19) {
      return 'лет';
    }
    if (lastOne === 1) {
      return 'год';
    }
    if (lastOne >= 2 && lastOne <= 4) {
      return 'года';
    }
    return 'лет';
  };

  const handleError = useCallback((error: Error, errorInfo: React.ErrorInfo) => {
    console.error('ErrorBoundary caught an error in VacancyList:', error);
    console.error('Error Info:', errorInfo);
  }, []);

  // Inline edit form component
  const InlineEditForm: React.FC<{ vacancy: Vacancy }> = ({ vacancy }) => {
    // Load draft from localStorage on mount
    const [draftLoaded, setDraftLoaded] = useState(false);

    const {
      register,
      handleSubmit,
      control,
      watch,
      formState: { errors, isDirty },
      reset,
      setValue,
    } = useForm<VacancyEditFormData>({
      resolver: zodResolver(vacancyEditSchema),
      defaultValues: {
        title: vacancy.title,
        description: vacancy.description,
        required_skills: vacancy.required_skills,
        min_experience_months: vacancy.min_experience_months,
        salary_min: vacancy.salary_min || null,
        salary_max: vacancy.salary_max || null,
        industry: vacancy.industry || '',
        work_format: vacancy.work_format || '',
        location: vacancy.location || '',
        english_level: vacancy.english_level || '',
        employment_type: vacancy.employment_type || '',
      },
      mode: 'onBlur',
    });

    // Load draft from localStorage on mount
    useEffect(() => {
      if (!draftLoaded) {
        try {
          const draft = localStorage.getItem('vacancy-edit-draft');
          if (draft) {
            const draftData = JSON.parse(draft);
            if (draftData.vacancyId === vacancy.id) {
              // Restore draft values
              Object.keys(draftData).forEach((key) => {
                if (key !== 'vacancyId' && key in draftData) {
                  setValue(key as keyof VacancyEditFormData, draftData[key]);
                }
              });
            }
          }
        } catch {
          // Ignore localStorage errors
        }
        setDraftLoaded(true);
      }
    }, [draftLoaded, vacancy.id, setValue]);

    // Auto-save draft to localStorage when form is dirty
    useEffect(() => {
      if (isDirty && draftLoaded) {
        const formData = watch();
        try {
          localStorage.setItem(
            'vacancy-edit-draft',
            JSON.stringify({ ...formData, vacancyId: vacancy.id })
          );
        } catch {
          // Ignore localStorage errors
        }
      }
    }, [isDirty, watch, draftLoaded, vacancy.id]);

    const onSubmit = (data: VacancyEditFormData) => {
      handleSaveVacancy(data);
    };

    const onCancel = () => {
      reset(); // Restore original values
      handleEditDialogClose();
    };

    return (
      <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {saveError && (
          <ErrorMessage
            error={saveError}
            title="Failed to Save Vacancy"
            actions={[
              {
                label: 'Retry',
                onClick: () => {
                  setSaveError(null);
                  handleSubmit(onSubmit)();
                },
                primary: true,
              },
              {
                label: 'Cancel',
                onClick: () => setSaveError(null),
                variant: 'outlined',
              },
            ]}
          />
        )}

        {/* Title */}
        <TextField
          fullWidth
          label="Title"
          {...register('title')}
          error={!!errors.title}
          helperText={errors.title?.message}
          required
        />

        {/* Description */}
        <TextField
          fullWidth
          multiline
          rows={4}
          label="Description"
          {...register('description')}
          error={!!errors.description}
          helperText={errors.description?.message}
          required
        />

        {/* Skills */}
        <FormControl error={!!errors.required_skills}>
          <InputLabel>Required Skills (comma separated)</InputLabel>
          <Controller
            name="required_skills"
            control={control}
            render={({ field }) => (
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Required Skills (comma separated)"
                value={field.value.join(', ')}
                onChange={(e) => {
                  const skills = e.target.value
                    .split(',')
                    .map((s) => s.trim())
                    .filter(Boolean);
                  field.onChange(skills);
                }}
                error={!!errors.required_skills}
                helperText={errors.required_skills?.message || 'Separate multiple skills with commas'}
              />
            )}
          />
        </FormControl>

        {/* Grid for fields */}
        <Grid2 container spacing={2}>
          {/* Experience */}
          <Grid2 size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              type="number"
              label="Min Experience (months)"
              {...register('min_experience_months', { valueAsNumber: true })}
              error={!!errors.min_experience_months}
              helperText={errors.min_experience_months?.message}
              inputProps={{ min: 0 }}
            />
          </Grid2>

          {/* Salary Min */}
          <Grid2 size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              type="number"
              label="Salary Min"
              {...register('salary_min', { valueAsNumber: true })}
              error={!!errors.salary_min}
              helperText={errors.salary_min?.message}
              inputProps={{ min: 0 }}
            />
          </Grid2>

          {/* Salary Max */}
          <Grid2 size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              type="number"
              label="Salary Max"
              {...register('salary_max', { valueAsNumber: true })}
              error={!!errors.salary_max}
              helperText={errors.salary_max?.message}
              inputProps={{ min: 0 }}
            />
          </Grid2>

          {/* English Level */}
          <Grid2 size={{ xs: 12, sm: 6 }}>
            <FormControl fullWidth>
              <InputLabel>English Level</InputLabel>
              <Select label="English Level" {...register('english_level')}>
                <MenuItem value="">Not specified</MenuItem>
                <MenuItem value="A1">A1 - Beginner</MenuItem>
                <MenuItem value="A2">A2 - Elementary</MenuItem>
                <MenuItem value="B1">B1 - Intermediate</MenuItem>
                <MenuItem value="B2">B2 - Upper Intermediate</MenuItem>
                <MenuItem value="C1">C1 - Advanced</MenuItem>
                <MenuItem value="C2">C2 - Proficiency</MenuItem>
              </Select>
            </FormControl>
          </Grid2>

          {/* Industry */}
          <Grid2 size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Industry"
              {...register('industry')}
            />
          </Grid2>

          {/* Work Format */}
          <Grid2 size={{ xs: 12, sm: 6 }}>
            <FormControl fullWidth>
              <InputLabel>Work Format</InputLabel>
              <Select label="Work Format" {...register('work_format')}>
                <MenuItem value="">Not specified</MenuItem>
                <MenuItem value="remote">Remote</MenuItem>
                <MenuItem value="office">Office</MenuItem>
                <MenuItem value="hybrid">Hybrid</MenuItem>
              </Select>
            </FormControl>
          </Grid2>

          {/* Location */}
          <Grid2 size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Location"
              {...register('location')}
            />
          </Grid2>

          {/* Employment Type */}
          <Grid2 size={{ xs: 12, sm: 6 }}>
            <FormControl fullWidth>
              <InputLabel>Employment Type</InputLabel>
              <Select label="Employment Type" {...register('employment_type')}>
                <MenuItem value="">Not specified</MenuItem>
                <MenuItem value="full-time">Full-time</MenuItem>
                <MenuItem value="part-time">Part-time</MenuItem>
                <MenuItem value="contract">Contract</MenuItem>
                <MenuItem value="internship">Internship</MenuItem>
              </Select>
            </FormControl>
          </Grid2>
        </Grid2>

        {/* Form Actions */}
        <DialogActions sx={{ px: 0, mt: 2 }}>
          <Button
            onClick={onCancel}
            startIcon={<CloseIcon />}
            disabled={isSaving}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            startIcon={isSaving ? <CircularProgress size={20} /> : <SaveIcon />}
            disabled={isSaving || !isDirty}
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </Box>
    );
  };

  if (loading) {
    return (
      <ErrorBoundary onError={handleError}>
        <Box
          sx={{
            maxWidth: 1200,
            mx: 'auto',
            p: { xs: 2, sm: 3 },
            overflowX: 'hidden',
          }}
        >
        {/* Header Skeleton */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: { xs: 'flex-start', sm: 'center' },
            mb: 4,
            flexDirection: { xs: 'column', sm: 'row' },
            gap: { xs: 2, sm: 0 },
          }}
        >
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Typography variant="h4" component="h1" fontWeight={600} gutterBottom sx={{ color: 'text.primary' }}>
              {t('vacancyList.title')}
            </Typography>
          </Box>
        </Box>

        {/* Search Skeleton */}
        <Box sx={{ mb: 3 }}>
          <Box
            sx={{
              width: '100%',
              height: 56,
              bgcolor: 'action.hover',
              borderRadius: 2,
            }}
          />
        </Box>

        {/* Loading Message */}
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, textAlign: 'center' }}>
          Loading vacancies...
        </Typography>

        {/* Vacancy Cards Skeleton */}
        <LoadingSpinner variant="cards" count={6} />
        </Box>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary onError={handleError}>
      <Box
        sx={{
          maxWidth: 1200,
          mx: 'auto',
          p: { xs: 2, sm: 3 },
          overflowX: 'hidden',
        }}
      >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', sm: 'center' },
          mb: 4,
          flexDirection: { xs: 'column', sm: 'row' },
          gap: { xs: 2, sm: 0 },
        }}
      >
        <Box sx={{ minWidth: 0, flex: 1 }}>
          <Typography variant="h4" component="h1" fontWeight={600} gutterBottom>
            {t('vacancyList.title')}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('vacancyList.subtitle')}
          </Typography>
        </Box>
        <Button
          variant="contained"
          size="large"
          startIcon={<AddIcon />}
          onClick={() => navigate('/vacancies/create')}
          sx={{ minWidth: { xs: '100%', sm: 'auto' } }}
        >
          {t('vacancyList.createRequest')}
        </Button>
      </Box>

      {/* Search Field */}
      <Box sx={{ mb: 3, minWidth: 0 }}>
        <TextField
          inputRef={searchInputRef}
          fullWidth
          placeholder={t('vacancyList.searchPlaceholder') || 'Search vacancies...'}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="action" />
              </InputAdornment>
            ),
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
            },
          }}
        />
        {searchQuery && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            {t('vacancyList.results', { count: filteredVacancies.length })}
          </Typography>
        )}
      </Box>

      {/* Sticky Filter Bar */}
      <Box
        sx={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          bgcolor: 'background.default',
          mb: 3,
          transition: 'box-shadow 0.3s',
          py: 1,
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
        }}
      >
        <Accordion
          expanded={filtersExpanded}
          onChange={() => setFiltersExpanded(!filtersExpanded)}
          elevation={2}
          sx={{
            '&:before': {
              display: 'none',
            },
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{
              '& .MuiAccordionSummary-content': {
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FilterListIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Filters
              </Typography>
              {hasActiveFilters && (
                <Chip
                  label="Active"
                  color="primary"
                  size="small"
                  sx={{ ml: 1 }}
                />
              )}
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Stack spacing={3}>
              {/* Work Format Filter */}
              <Box>
                <Typography variant="subtitle2" gutterBottom sx={{ mb: 1.5 }}>
                  Work Format:
                </Typography>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} flexWrap="wrap" useFlexGap>
                  <Button
                    size="small"
                    variant={workFormatFilter === 'all' ? 'contained' : 'outlined'}
                    onClick={() => setWorkFormatFilter('all')}
                  >
                    All Formats
                  </Button>
                  <Button
                    size="small"
                    variant={workFormatFilter === 'remote' ? 'contained' : 'outlined'}
                    onClick={() => setWorkFormatFilter('remote')}
                  >
                    Remote
                  </Button>
                  <Button
                    size="small"
                    variant={workFormatFilter === 'office' ? 'contained' : 'outlined'}
                    onClick={() => setWorkFormatFilter('office')}
                  >
                    Office
                  </Button>
                  <Button
                    size="small"
                    variant={workFormatFilter === 'hybrid' ? 'contained' : 'outlined'}
                    onClick={() => setWorkFormatFilter('hybrid')}
                  >
                    Hybrid
                  </Button>
                </Stack>
              </Box>

              {/* Location Filter */}
              <Box>
                <Typography variant="subtitle2" gutterBottom sx={{ mb: 1.5 }}>
                  Location:
                </Typography>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Filter by location..."
                  value={locationFilter}
                  onChange={(e) => setLocationFilter(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon fontSize="small" />
                      </InputAdornment>
                    ),
                  }}
                />
              </Box>

              {/* Date Range Filter */}
              <Box>
                <Typography variant="subtitle2" gutterBottom sx={{ mb: 1.5 }}>
                  Date Range:
                </Typography>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                  <TextField
                    type="date"
                    label="From"
                    size="small"
                    value={dateFromFilter}
                    onChange={(e) => setDateFromFilter(e.target.value)}
                    InputLabelProps={{
                      shrink: true,
                    }}
                    sx={{ flex: 1 }}
                  />
                  <TextField
                    type="date"
                    label="To"
                    size="small"
                    value={dateToFilter}
                    onChange={(e) => setDateToFilter(e.target.value)}
                    InputLabelProps={{
                      shrink: true,
                    }}
                    sx={{ flex: 1 }}
                  />
                </Stack>
              </Box>

              {/* Filter Actions */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {t('vacancyList.results', { count: filteredVacancies.length })}
                </Typography>
                {hasActiveFilters && (
                  <Button
                    size="small"
                    startIcon={<ClearIcon />}
                    onClick={handleClearFilters}
                    color="secondary"
                  >
                    Clear All Filters
                  </Button>
                )}
              </Box>
            </Stack>
          </AccordionDetails>
        </Accordion>
      </Box>

      {/* Error Alert */}
      {error && (
        <ErrorMessage
          error={error}
          actions={[
            {
              label: 'Retry',
              onClick: () => {
                setError(null);
                fetchVacancies(0, limit);
              },
              primary: true,
            },
            {
              label: 'Dismiss',
              onClick: () => setError(null),
              variant: 'outlined',
            },
          ]}
        />
      )}

      {/* Vacancies List */}
      {filteredVacancies.length === 0 && searchQuery ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <SearchIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {t('vacancyList.noResults')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {t('vacancyList.tryDifferentSearch')}
          </Typography>
          <Button variant="outlined" onClick={() => setSearchQuery('')}>
            {t('vacancyList.clearSearch')}
          </Button>
        </Paper>
      ) : filteredVacancies.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <WorkIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {t('vacancyList.noActiveRequests')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {t('vacancyList.createFirstRequest')}
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/vacancies/create')}
          >
            {t('vacancyList.createRequest')}
          </Button>
        </Paper>
      ) : (
        <Box
          ref={scrollRef}
          sx={{
            maxHeight: '70vh',
            overflowY: 'auto',
            pr: 1,
            // Custom scrollbar styling for better UX
            '&::-webkit-scrollbar': {
              width: '8px',
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: 'background.paper',
              borderRadius: 1,
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: 'action.hover',
              borderRadius: 1,
              '&:hover': {
                backgroundColor: 'action.selected',
              },
            },
          }}
        >
          <Grid2
            container
            spacing={{ xs: 2, sm: 3 }}
            columns={{ xs: 1, sm: 2, md: 2, lg: 3 }}
          >
            {filteredVacancies.map((vacancy, index) => (
            <Grid2
              size={{ xs: 1, sm: 1, md: 1, lg: 1 }}
              key={vacancy.id}
              sx={{
                minWidth: 0,
              }}
            >
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  cursor: 'pointer',
                  position: 'relative',
                  outline: selectedVacancyIndex === index ? '3px solid' : 'none',
                  outlineColor: 'primary.main',
                  boxShadow: selectedVacancyIndex === index ? 8 : 1,
                  transform: selectedVacancyIndex === index ? 'translateY(-4px)' : 'none',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
                onClick={() => {
                  setSelectedVacancyIndex(index);
                  navigate(`${vacancy.id}`);
                }}
                tabIndex={0}
                aria-selected={selectedVacancyIndex === index}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  {/* Title */}
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    {vacancy.title}
                  </Typography>

                  {/* Salary */}
                  <Typography variant="body2" color="primary" fontWeight={500} sx={{ mb: 1 }}>
                    {formatSalary(vacancy.salary_min, vacancy.salary_max)}
                  </Typography>

                  {/* Experience */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      {t('vacancyList.experience')}:
                    </Typography>
                    <Typography variant="body2" fontWeight={500}>
                      {formatExperience(vacancy.min_experience_months)}
                    </Typography>
                  </Box>

                  {/* Skills */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                      {t('vacancyList.requiredSkills', { count: vacancy.required_skills.length })}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {vacancy.required_skills.slice(0, 4).map((skill) => (
                        <Chip key={skill} label={skill} size="small" variant="outlined" />
                      ))}
                      {vacancy.required_skills.length > 4 && (
                        <Chip
                          label={t('vacancyList.more', { count: vacancy.required_skills.length - 4 })}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </Box>

                  {/* Meta info */}
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {vacancy.employment_type && (
                      <Chip label={vacancy.employment_type} size="small" color="info" variant="outlined" />
                    )}
                    {vacancy.work_format && (
                      <Chip label={vacancy.work_format} size="small" color="success" variant="outlined" />
                    )}
                    {vacancy.english_level && (
                      <Chip label={`English: ${vacancy.english_level}`} size="small" />
                    )}
                  </Stack>
                </CardContent>

                <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                  <Button
                    size="small"
                    onClick={() => navigate(`${vacancy.id}`)}
                  >
                    {t('vacancyList.moreDetails')}
                  </Button>
                  <Box>
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditClick(vacancy);
                      }}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteClick(vacancy.id);
                      }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </CardActions>
              </Card>
            </Grid2>
          ))}
        </Grid2>

        {/* Loading more indicator */}
        {loadingMore && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
            <CircularProgress size={24} />
            <Typography variant="body2" color="text.secondary" sx={{ ml: 2 }}>
              Loading more vacancies...
            </Typography>
          </Box>
        )}

        {/* No more items indicator */}
        {!hasMore && vacancies.length > 0 && !hasActiveFilters && (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {t('vacancyList.allItemsLoaded') || 'All vacancies loaded'}
            </Typography>
          </Box>
        )}
        </Box>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => {
        setDeleteDialogOpen(false);
        setSelectedVacancyIndex(-1);
      }}>
        <DialogTitle>{t('vacancyList.deleteDialog.title')}</DialogTitle>
        <DialogContent>
          <Typography>
            {t('vacancyList.deleteDialog.message')}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setDeleteDialogOpen(false);
            setSelectedVacancyIndex(-1);
          }}>{t('common.cancel')}</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            {t('common.delete')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Inline Edit Dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={handleEditDialogClose}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { height: '80vh', maxHeight: 600 }
        }}
      >
        <DialogTitle>Edit Vacancy</DialogTitle>
        <DialogContent sx={{ pb: 0 }}>
          {editingVacancy && <InlineEditForm vacancy={editingVacancy} />}
        </DialogContent>
      </Dialog>
      </Box>
    </ErrorBoundary>
  );
};

export default VacancyList;
