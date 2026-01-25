import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Stack,
  Divider,
  Alert,
} from '@mui/material';
import {
  FilterList as FilterIcon,
  Sort as SortIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
  RestartAlt as ResetIcon,
  Save as SaveIcon,
  Share as ShareIcon,
} from '@mui/icons-material';

/**
 * Filter settings interface
 */
interface ComparisonFilters {
  min_match_percentage: number;
  max_match_percentage: number;
}

/**
 * Sort settings interface
 */
interface ComparisonSort {
  field: 'created_at' | 'match_percentage' | 'name' | 'updated_at';
  order: 'asc' | 'desc';
}

/**
 * ComparisonControls Component Props
 */
interface ComparisonControlsProps {
  /** Array of resume IDs currently being compared */
  resumeIds: string[];
  /** Callback when resume IDs change */
  onResumeIdsChange?: (resumeIds: string[]) => void;
  /** Callback when filters change */
  onFiltersChange?: (filters: ComparisonFilters) => void;
  /** Callback when sort settings change */
  onSortChange?: (sort: ComparisonSort) => void;
  /** Callback when save is clicked */
  onSave?: () => void;
  /** Callback when share is clicked */
  onShare?: () => void;
  /** Initial filter values */
  initialFilters?: ComparisonFilters;
  /** Initial sort values */
  initialSort?: ComparisonSort;
  /** Maximum number of resumes allowed */
  maxResumes?: number;
  /** Minimum number of resumes required */
  minResumes?: number;
  /** Show save/share buttons */
  showSaveActions?: boolean;
  /** Disabled state */
  disabled?: boolean;
}

/**
 * ComparisonControls Component
 *
 * Provides controls for managing resume comparisons with:
 * - Add/remove resumes from comparison
 * - Filter by match percentage range
 * - Sort by different fields and orders
 * - Save and share comparison views
 * - Reset to defaults
 *
 * @example
 * ```tsx
 * <ComparisonControls
 *   resumeIds={['resume-1', 'resume-2']}
 *   onResumeIdsChange={(ids) => console.log('Resume IDs:', ids)}
 *   onFiltersChange={(filters) => console.log('Filters:', filters)}
 *   onSortChange={(sort) => console.log('Sort:', sort)}
 * />
 * ```
 */
const ComparisonControls: React.FC<ComparisonControlsProps> = ({
  resumeIds,
  onResumeIdsChange,
  onFiltersChange,
  onSortChange,
  onSave,
  onShare,
  initialFilters = { min_match_percentage: 0, max_match_percentage: 100 },
  initialSort = { field: 'match_percentage', order: 'desc' },
  maxResumes = 5,
  minResumes = 2,
  showSaveActions = true,
  disabled = false,
}) => {
  const [filters, setFilters] = useState<ComparisonFilters>(initialFilters);
  const [sort, setSort] = useState<ComparisonSort>(initialSort);
  const [newResumeId, setNewResumeId] = useState('');

  /**
   * Handle filter change
   */
  const handleFilterChange = useCallback(
    (field: keyof ComparisonFilters, value: number) => {
      const newFilters = { ...filters, [field]: value };

      // Ensure min doesn't exceed max
      if (field === 'min_match_percentage' && value > newFilters.max_match_percentage) {
        newFilters.max_match_percentage = value;
      } else if (field === 'max_match_percentage' && value < newFilters.min_match_percentage) {
        newFilters.min_match_percentage = value;
      }

      setFilters(newFilters);
      onFiltersChange?.(newFilters);
    },
    [filters, onFiltersChange]
  );

  /**
   * Handle sort field change
   */
  const handleSortFieldChange = useCallback(
    (event: React.ChangeEvent<{ value: unknown }>) => {
      const field = event.target.value as ComparisonSort['field'];
      const newSort = { ...sort, field };
      setSort(newSort);
      onSortChange?.(newSort);
    },
    [sort, onSortChange]
  );

  /**
   * Handle sort order change
   */
  const handleSortOrderChange = useCallback(
    (event: React.ChangeEvent<{ value: unknown }>) => {
      const order = event.target.value as ComparisonSort['order'];
      const newSort = { ...sort, order };
      setSort(newSort);
      onSortChange?.(newSort);
    },
    [sort, onSortChange]
  );

  /**
   * Handle add resume
   */
  const handleAddResume = useCallback(() => {
    if (!newResumeId.trim()) {
      return;
    }

    if (resumeIds.length >= maxResumes) {
      return;
    }

    if (resumeIds.includes(newResumeId.trim())) {
      return;
    }

    const updatedIds = [...resumeIds, newResumeId.trim()];
    onResumeIdsChange?.(updatedIds);
    setNewResumeId('');
  }, [newResumeId, resumeIds, maxResumes, onResumeIdsChange]);

  /**
   * Handle remove resume
   */
  const handleRemoveResume = useCallback(
    (resumeId: string) => {
      const updatedIds = resumeIds.filter((id) => id !== resumeId);
      onResumeIdsChange?.(updatedIds);
    },
    [resumeIds, onResumeIdsChange]
  );

  /**
   * Handle reset controls
   */
  const handleReset = useCallback(() => {
    const defaultFilters: ComparisonFilters = {
      min_match_percentage: 0,
      max_match_percentage: 100,
    };
    const defaultSort: ComparisonSort = {
      field: 'match_percentage',
      order: 'desc',
    };

    setFilters(defaultFilters);
    setSort(defaultSort);
    setNewResumeId('');

    onFiltersChange?.(defaultFilters);
    onSortChange?.(defaultSort);
  }, [onFiltersChange, onSortChange]);

  /**
   * Handle save comparison
   */
  const handleSave = useCallback(() => {
    onSave?.();
  }, [onSave]);

  /**
   * Handle share comparison
   */
  const handleShare = useCallback(() => {
    onShare?.();
  }, [onShare]);

  /**
   * Handle key press in resume ID input
   */
  const handleKeyPress = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'Enter') {
        handleAddResume();
      }
    },
    [handleAddResume]
  );

  // Update state when props change
  useEffect(() => {
    if (initialFilters) {
      setFilters(initialFilters);
    }
  }, [initialFilters]);

  useEffect(() => {
    if (initialSort) {
      setSort(initialSort);
    }
  }, [initialSort]);

  const isValidRange = resumeIds.length >= minResumes && resumeIds.length <= maxResumes;
  const canAddMore = resumeIds.length < maxResumes;

  return (
    <Stack spacing={2}>
      {/* Resume Management Section */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <FilterIcon sx={{ mr: 1, fontSize: 24, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Resume Selection
          </Typography>
        </Box>
        <Divider sx={{ mb: 2 }} />

        {/* Resume Count Info */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Selected Resumes: <strong>{resumeIds.length}</strong> / {maxResumes} (minimum {minResumes})
          </Typography>
          {!isValidRange && (
            <Alert severity="warning" sx={{ mt: 1 }}>
              {resumeIds.length < minResumes
                ? `At least ${minResumes} resume${minResumes > 1 ? 's are' : ' is'} required for comparison`
                : `Maximum ${maxResumes} resumes can be compared at once`}
            </Alert>
          )}
        </Box>

        {/* Resume List */}
        {resumeIds.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Current Resumes:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {resumeIds.map((resumeId) => (
                <Chip
                  key={resumeId}
                  label={resumeId}
                  size="medium"
                  onDelete={!disabled ? () => handleRemoveResume(resumeId) : undefined}
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        )}

        {/* Add Resume Input */}
        {!disabled && canAddMore && (
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <TextField
              fullWidth
              size="small"
              label="Add Resume ID"
              value={newResumeId}
              onChange={(e) => setNewResumeId(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter resume ID..."
              disabled={disabled}
            />
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleAddResume}
              disabled={!newResumeId.trim() || disabled}
            >
              Add
            </Button>
          </Box>
        )}
      </Paper>

      {/* Filters Section */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <FilterIcon sx={{ mr: 1, fontSize: 24, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Filters
          </Typography>
        </Box>
        <Divider sx={{ mb: 2 }} />

        {/* Match Percentage Range */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Match Percentage Range: {filters.min_match_percentage}% - {filters.max_match_percentage}%
          </Typography>
          <Box sx={{ px: 1 }}>
            <Slider
              value={[filters.min_match_percentage, filters.max_match_percentage]}
              onChange={(_event, newValue) => {
                const value = newValue as number[];
                handleFilterChange('min_match_percentage', value[0]);
                handleFilterChange('max_match_percentage', value[1]);
              }}
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${value}%`}
              min={0}
              max={100}
              step={5}
              marks={[
                { value: 0, label: '0%' },
                { value: 25, label: '25%' },
                { value: 50, label: '50%' },
                { value: 75, label: '75%' },
                { value: 100, label: '100%' },
              ]}
              disabled={disabled}
              sx={{
                '& .MuiSlider-thumb': {
                  '&:hover, &.Mui-focusVisible': {
                    boxShadow: '0 0 0 8px rgba(25, 118, 210, 0.16)',
                  },
                },
              }}
            />
          </Box>
        </Box>
      </Paper>

      {/* Sort Section */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <SortIcon sx={{ mr: 1, fontSize: 24, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Sorting
          </Typography>
        </Box>
        <Divider sx={{ mb: 2 }} />

        <Stack spacing={2} direction={{ xs: 'column', md: 'row' }}>
          {/* Sort Field */}
          <FormControl fullWidth size="small" disabled={disabled}>
            <InputLabel>Sort By</InputLabel>
            <Select
              value={sort.field}
              onChange={handleSortFieldChange}
              label="Sort By"
            >
              <MenuItem value="match_percentage">Match Percentage</MenuItem>
              <MenuItem value="created_at">Date Created</MenuItem>
              <MenuItem value="updated_at">Last Updated</MenuItem>
              <MenuItem value="name">Name</MenuItem>
            </Select>
          </FormControl>

          {/* Sort Order */}
          <FormControl fullWidth size="small" disabled={disabled}>
            <InputLabel>Order</InputLabel>
            <Select
              value={sort.order}
              onChange={handleSortOrderChange}
              label="Order"
            >
              <MenuItem value="desc">Descending</MenuItem>
              <MenuItem value="asc">Ascending</MenuItem>
            </Select>
          </FormControl>
        </Stack>

        {/* Active Sort Indicator */}
        <Box sx={{ mt: 2 }}>
          <Chip
            label={`Sorted by ${sort.field.replace('_', ' ')} (${sort.order})`}
            size="small"
            color="primary"
            variant="outlined"
          />
        </Box>
      </Paper>

      {/* Actions Section */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Stack spacing={2} direction={{ xs: 'column', md: 'row' }}>
          {/* Reset Button */}
          <Button
            fullWidth
            variant="outlined"
            startIcon={<ResetIcon />}
            onClick={handleReset}
            disabled={disabled}
          >
            Reset All
          </Button>

          {/* Save Button */}
          {showSaveActions && onSave && (
            <Button
              fullWidth
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              disabled={disabled || !isValidRange}
              color="primary"
            >
              Save Comparison
            </Button>
          )}

          {/* Share Button */}
          {showSaveActions && onShare && (
            <Button
              fullWidth
              variant="contained"
              startIcon={<ShareIcon />}
              onClick={handleShare}
              disabled={disabled || !isValidRange}
              color="secondary"
            >
              Share
            </Button>
          )}
        </Stack>
      </Paper>

      {/* Info Alert */}
      <Alert severity="info" variant="outlined">
        <Typography variant="body2">
          <strong>Tip:</strong> Select {minResumes}-{maxResumes} resumes to compare side-by-side. Use filters
          to narrow down results and sorting to rank candidates.
        </Typography>
      </Alert>
    </Stack>
  );
};

export default ComparisonControls;
