import React, { useState, useCallback } from 'react';
import {
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Stack,
  Collapse,
  IconButton,
  Divider,
} from '@mui/material';
import {
  FilterList as FilterIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import type {
  QueuePriority,
  QueueStatus,
  CandidateQueueFilters,
} from '@/hooks/useCandidateQueue';

/**
 * Priority options with display labels
 */
const PRIORITY_OPTIONS: Array<{ value: QueuePriority; label: string; color: string }> = [
  { value: 'urgent', label: 'Urgent', color: 'error' },
  { value: 'high', label: 'High', color: 'warning' },
  { value: 'medium', label: 'Medium', color: 'info' },
  { value: 'low', label: 'Low', color: 'default' },
];

/**
 * Status options with display labels
 */
const STATUS_OPTIONS: Array<{ value: QueueStatus; label: string }> = [
  { value: 'pending', label: 'Pending' },
  { value: 'in_review', label: 'In Review' },
  { value: 'completed', label: 'Completed' },
  { value: 'skipped', label: 'Skipped' },
];

/**
 * Sort options for the queue
 */
const SORT_OPTIONS: Array<{ value: 'priority' | 'wait_time' | 'created_at'; label: string }> = [
  { value: 'priority', label: 'Priority' },
  { value: 'wait_time', label: 'Wait Time' },
  { value: 'created_at', label: 'Date Added' },
];

/**
 * Sort order options
 */
const SORT_ORDER_OPTIONS: Array<{ value: 'asc' | 'desc'; label: string }> = [
  { value: 'asc', label: 'Ascending' },
  { value: 'desc', label: 'Descending' },
];

/**
 * Props for QueueFilters component
 */
interface QueueFiltersProps {
  /**
   * Callback when filters change
   */
  onFiltersChange: (filters: CandidateQueueFilters) => void;
  /**
   * Current filters to display
   */
  filters?: CandidateQueueFilters;
  /**
   * Available vacancies for filtering
   */
  vacancies?: Array<{ id: string; title: string }>;
  /**
   * Available recruiters for assignment filtering
   */
  recruiters?: Array<{ id: string; name: string }>;
  /**
   * Whether the filters are loading
   */
  loading?: boolean;
  /**
   * Show the apply button (if false, filters auto-apply)
   */
  showApplyButton?: boolean;
  /**
   * Default expanded state
   */
  defaultExpanded?: boolean;
}

/**
 * Queue Filters Component
 *
 * Provides comprehensive filtering capabilities for the candidate review queue:
 * - Vacancy selection
 * - Status filtering
 * - Priority filtering
 * - Date range filtering (when candidates entered the queue)
 * - Sorting options
 *
 * @example
 * ```tsx
 * const [filters, setFilters] = useState<CandidateQueueFilters>({});
 *
 * <QueueFilters
 *   filters={filters}
 *   onFiltersChange={setFilters}
 *   vacancies={vacancies}
 *   defaultExpanded
 * />
 * ```
 */
const QueueFilters: React.FC<QueueFiltersProps> = ({
  onFiltersChange,
  filters = {},
  vacancies = [],
  recruiters = [],
  loading = false,
  showApplyButton = false,
  defaultExpanded = true,
}) => {
  const { t } = useTranslation();

  // UI state
  const [expanded, setExpanded] = useState(defaultExpanded);

  // Local filter state (for delayed application)
  const [localFilters, setLocalFilters] = useState<CandidateQueueFilters>(filters);

  /**
   * Update a single filter value
   */
  const updateFilter = useCallback(
    <K extends keyof CandidateQueueFilters>(key: K, value: CandidateQueueFilters[K]) => {
      const newFilters = { ...localFilters, [key]: value };
      setLocalFilters(newFilters);

      // Auto-apply if no apply button
      if (!showApplyButton) {
        onFiltersChange(newFilters);
      }
    },
    [localFilters, onFiltersChange, showApplyButton]
  );

  /**
   * Clear all filters
   */
  const clearFilters = useCallback(() => {
    const emptyFilters: CandidateQueueFilters = {};
    setLocalFilters(emptyFilters);
    onFiltersChange(emptyFilters);
  }, [onFiltersChange]);

  /**
   * Apply filters manually (when showApplyButton is true)
   */
  const applyFilters = useCallback(() => {
    onFiltersChange(localFilters);
  }, [localFilters, onFiltersChange]);

  /**
   * Count active filters
   */
  const activeFilterCount = Object.entries(localFilters).filter(([key, value]) => {
    if (key === 'skip' || key === 'limit') return false;
    return value !== undefined && value !== '' && value !== null;
  }).length;

  /**
   * Check if filters have changed from applied
   */
  const hasChanges = showApplyButton && JSON.stringify(localFilters) !== JSON.stringify(filters);

  return (
    <Paper sx={{ mb: 3 }}>
      {/* Header */}
      <Box
        sx={{
          px: 3,
          py: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Stack direction="row" spacing={2} alignItems="center">
          <FilterIcon color="primary" />
          <Typography variant="h6" fontWeight={600}>
            {t('queueFilters.title', 'Queue Filters')}
          </Typography>
          {activeFilterCount > 0 && (
            <Chip
              label={t('queueFilters.activeFilters', {
                count: activeFilterCount,
                defaultValue: `${activeFilterCount} filter${activeFilterCount > 1 ? 's' : ''}`,
              })}
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
        </Stack>
        <IconButton size="small">
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>

      <Divider />

      {/* Filters Content */}
      <Collapse in={expanded}>
        <Box sx={{ p: 3 }}>
          <Grid container spacing={3}>
            {/* Vacancy Filter */}
            {vacancies.length > 0 && (
              <Grid item xs={12} md={6} lg={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>{t('queueFilters.vacancy', 'Vacancy')}</InputLabel>
                  <Select
                    value={localFilters.vacancy_id || ''}
                    label={t('queueFilters.vacancy', 'Vacancy')}
                    onChange={(e) => updateFilter('vacancy_id', e.target.value || undefined)}
                    disabled={loading}
                  >
                    <MenuItem value="">
                      <em>{t('queueFilters.allVacancies', 'All Vacancies')}</em>
                    </MenuItem>
                    {vacancies.map((vacancy) => (
                      <MenuItem key={vacancy.id} value={vacancy.id}>
                        {vacancy.title}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            )}

            {/* Status Filter */}
            <Grid item xs={12} md={6} lg={4}>
              <FormControl fullWidth size="small">
                <InputLabel>{t('queueFilters.status', 'Status')}</InputLabel>
                <Select
                  value={localFilters.status || ''}
                  label={t('queueFilters.status', 'Status')}
                  onChange={(e) =>
                    updateFilter('status', (e.target.value as QueueStatus) || undefined)
                  }
                  disabled={loading}
                >
                  <MenuItem value="">
                    <em>{t('queueFilters.allStatuses', 'All Statuses')}</em>
                  </MenuItem>
                  {STATUS_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {t(`queueFilters.statusOptions.${option.value}`, option.label)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Priority Filter */}
            <Grid item xs={12} md={6} lg={4}>
              <FormControl fullWidth size="small">
                <InputLabel>{t('queueFilters.priority', 'Priority')}</InputLabel>
                <Select
                  value={localFilters.priority || ''}
                  label={t('queueFilters.priority', 'Priority')}
                  onChange={(e) =>
                    updateFilter('priority', (e.target.value as QueuePriority) || undefined)
                  }
                  disabled={loading}
                >
                  <MenuItem value="">
                    <em>{t('queueFilters.allPriorities', 'All Priorities')}</em>
                  </MenuItem>
                  {PRIORITY_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Chip
                          label=""
                          size="small"
                          color={option.color as 'error' | 'warning' | 'info' | 'default'}
                          sx={{ width: 8, height: 8, minWidth: 8 }}
                        />
                        {t(`queueFilters.priorityOptions.${option.value}`, option.label)}
                      </Stack>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Assigned Recruiter Filter */}
            {recruiters.length > 0 && (
              <Grid item xs={12} md={6} lg={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>{t('queueFilters.assignedRecruiter', 'Assigned Recruiter')}</InputLabel>
                  <Select
                    value={localFilters.assigned_recruiter_id || ''}
                    label={t('queueFilters.assignedRecruiter', 'Assigned Recruiter')}
                    onChange={(e) => updateFilter('assigned_recruiter_id', e.target.value || undefined)}
                    disabled={loading}
                  >
                    <MenuItem value="">
                      <em>{t('queueFilters.allRecruiters', 'All Recruiters')}</em>
                    </MenuItem>
                    {recruiters.map((recruiter) => (
                      <MenuItem key={recruiter.id} value={recruiter.id}>
                        {recruiter.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            )}

            {/* Date Range */}
            <Grid item xs={12} md={6} lg={4}>
              <Stack direction="row" spacing={2}>
                <TextField
                  fullWidth
                  size="small"
                  label={t('queueFilters.enteredAfter', 'Entered After')}
                  type="date"
                  value={localFilters.entered_after || ''}
                  onChange={(e) => updateFilter('entered_after', e.target.value || undefined)}
                  InputLabelProps={{ shrink: true }}
                  disabled={loading}
                />
                <TextField
                  fullWidth
                  size="small"
                  label={t('queueFilters.enteredBefore', 'Entered Before')}
                  type="date"
                  value={localFilters.entered_before || ''}
                  onChange={(e) => updateFilter('entered_before', e.target.value || undefined)}
                  InputLabelProps={{ shrink: true }}
                  disabled={loading}
                />
              </Stack>
            </Grid>

            {/* Sort By */}
            <Grid item xs={12} md={6} lg={4}>
              <Stack direction="row" spacing={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>{t('queueFilters.sortBy', 'Sort By')}</InputLabel>
                  <Select
                    value={localFilters.sort_by || 'priority'}
                    label={t('queueFilters.sortBy', 'Sort By')}
                    onChange={(e) =>
                      updateFilter(
                        'sort_by',
                        e.target.value as 'priority' | 'wait_time' | 'created_at'
                      )
                    }
                    disabled={loading}
                  >
                    {SORT_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {t(`queueFilters.sortOptions.${option.value}`, option.label)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl fullWidth size="small">
                  <InputLabel>{t('queueFilters.sortOrder', 'Order')}</InputLabel>
                  <Select
                    value={localFilters.sort_order || 'desc'}
                    label={t('queueFilters.sortOrder', 'Order')}
                    onChange={(e) => updateFilter('sort_order', e.target.value as 'asc' | 'desc')}
                    disabled={loading}
                  >
                    {SORT_ORDER_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {t(`queueFilters.sortOrderOptions.${option.value}`, option.label)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Stack>
            </Grid>

            {/* Action Buttons */}
            <Grid item xs={12}>
              <Stack direction="row" spacing={2} justifyContent="flex-end">
                <Button
                  variant="outlined"
                  onClick={clearFilters}
                  startIcon={<ClearIcon />}
                  disabled={loading || activeFilterCount === 0}
                >
                  {t('queueFilters.clear', 'Clear Filters')}
                </Button>
                {showApplyButton && (
                  <Button
                    variant="contained"
                    onClick={applyFilters}
                    disabled={loading || !hasChanges}
                  >
                    {t('queueFilters.apply', 'Apply Filters')}
                  </Button>
                )}
              </Stack>
            </Grid>
          </Grid>
        </Box>
      </Collapse>
    </Paper>
  );
};

export default QueueFilters;
