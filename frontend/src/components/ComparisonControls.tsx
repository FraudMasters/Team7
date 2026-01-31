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
  SelectChangeEvent,
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
  Download as DownloadIcon,
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
 * Individual skill match interface
 */
interface SkillMatch {
  skill: string;
  matched: boolean;
  highlight: 'green' | 'red';
}

/**
 * Individual resume comparison result
 */
interface ResumeComparisonResult {
  resume_id: string;
  match_percentage: number;
  matched_skills: SkillMatch[];
  missing_skills: SkillMatch[];
  experience_verification?: Array<{
    skill: string;
    total_months: number;
    required_months: number;
    meets_requirement: boolean;
  }>;
  overall_match: boolean;
}

/**
 * Comparison data interface
 */
interface ComparisonData {
  vacancy_id: string;
  comparisons: ResumeComparisonResult[];
  all_unique_skills: string[];
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
  /** Callback when export is clicked */
  onExport?: () => void;
  /** Comparison data for export */
  comparisonData?: ComparisonData | null;
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
  /** Show export button */
  showExport?: boolean;
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
 * - Export comparison data to Excel (CSV format)
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
 *   comparisonData={comparisonData}
 *   onExport={() => console.log('Export clicked')}
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
  onExport,
  comparisonData,
  initialFilters = { min_match_percentage: 0, max_match_percentage: 100 },
  initialSort = { field: 'match_percentage', order: 'desc' },
  maxResumes = 5,
  minResumes = 2,
  showSaveActions = true,
  showExport = true,
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
    (event: SelectChangeEvent<ComparisonSort['field']>) => {
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
    (event: SelectChangeEvent<ComparisonSort['order']>) => {
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
   * Handle export to Excel (CSV format)
   */
  const handleExport = useCallback(() => {
    // If custom export handler provided, use it
    if (onExport) {
      onExport();
      return;
    }

    // Default export implementation using comparison data
    if (!comparisonData || !comparisonData.comparisons || comparisonData.comparisons.length === 0) {
      return;
    }

    try {
      // Create CSV content
      const csvRows: string[] = [];

      // Add header with metadata
      csvRows.push(`Resume Comparison Report,Vacancy ID,${comparisonData.vacancy_id}`);
      csvRows.push(`Generated,${new Date().toLocaleString()}`);
      csvRows.push('');

      // Add summary section
      csvRows.push('SUMMARY');
      csvRows.push('Rank,Resume ID,Match %,Matched Skills,Missing Skills,Overall Match');

      const sortedComparisons = [...comparisonData.comparisons].sort(
        (a, b) => b.match_percentage - a.match_percentage
      );

      sortedComparisons.forEach((comparison, index) => {
        const matchedSkills = comparison.matched_skills.map((s) => s.skill).join('; ');
        const missingSkills = comparison.missing_skills.map((s) => s.skill).join('; ');
        csvRows.push(
          `${index + 1},"${comparison.resume_id}",${comparison.match_percentage.toFixed(1)}%,"${matchedSkills}","${missingSkills}","${comparison.overall_match ? 'Yes' : 'No'}"`
        );
      });

      csvRows.push('');

      // Add skills matrix
      csvRows.push('SKILLS MATRIX');
      const headerRow = ['Skill', ...sortedComparisons.map((c) => `"${c.resume_id} (${c.match_percentage.toFixed(0)}%)"`)];
      csvRows.push(headerRow.join(','));

      comparisonData.all_unique_skills.forEach((skill) => {
        const row = [`"${skill}"`];
        sortedComparisons.forEach((comparison) => {
          const hasSkill = comparison.matched_skills.some((s) => s.skill === skill);
          row.push(hasSkill ? '✓' : '✗');
        });
        csvRows.push(row.join(','));
      });

      csvRows.push('');

      // Add experience verification if available
      const hasExperienceData = sortedComparisons.some(
        (c) => c.experience_verification && c.experience_verification.length > 0
      );

      if (hasExperienceData) {
        csvRows.push('EXPERIENCE VERIFICATION');
        csvRows.push('Resume ID,Skill,Required Months,Total Months,Meets Requirement');

        sortedComparisons.forEach((comparison) => {
          if (comparison.experience_verification && comparison.experience_verification.length > 0) {
            comparison.experience_verification.forEach((exp) => {
              csvRows.push(
                `"${comparison.resume_id}","${exp.skill}",${exp.required_months},${exp.total_months},"${exp.meets_requirement ? 'Yes' : 'No'}"`
              );
            });
          }
        });
      }

      // Create blob and download
      const csvContent = csvRows.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);

      link.setAttribute('href', url);
      link.setAttribute(
        'download',
        `resume-comparison-${comparisonData.vacancy_id}-${new Date().getTime()}.csv`
      );
      link.style.visibility = 'hidden';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      // Silently handle export errors
      // In production, you might want to show a toast notification
    }
  }, [comparisonData, onExport]);

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
                if (value[0] !== undefined) handleFilterChange('min_match_percentage', value[0]);
                if (value[1] !== undefined) handleFilterChange('max_match_percentage', value[1]);
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

          {/* Export Button */}
          {showExport && (
            <Button
              fullWidth
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleExport}
              disabled={disabled || !isValidRange || (!comparisonData && !onExport)}
              color="info"
            >
              Export to Excel
            </Button>
          )}

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
