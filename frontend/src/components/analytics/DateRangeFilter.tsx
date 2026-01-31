import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Chip,
  Stack,
  Divider,
  Alert,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
  MenuItem,
} from '@mui/material';
import {
  DateRange as DateRangeIcon,
  RestartAlt as ResetIcon,
  Check as ApplyIcon,
} from '@mui/icons-material';

/**
 * Date range filter options
 */
export type DateRangePreset =
  | 'last_7_days'
  | 'last_30_days'
  | 'last_90_days'
  | 'this_month'
  | 'last_month'
  | 'this_year'
  | 'custom';

/**
 * Date range filter interface
 */
export interface DateRangeFilter {
  startDate: string;
  endDate: string;
  preset: DateRangePreset;
}

/**
 * DateRangeFilter Component Props
 */
interface DateRangeFilterProps {
  /** Callback when date range changes */
  onDateRangeChange?: (dateRange: DateRangeFilter) => void;
  /** Callback when apply is clicked */
  onApply?: (dateRange: DateRangeFilter) => void;
  /** Initial date range values */
  initialDateRange?: Partial<DateRangeFilter>;
  /** Show preset quick select buttons */
  showPresets?: boolean;
  /** Disabled state */
  disabled?: boolean;
  /** Custom label for the filter section */
  label?: string;
}

/**
 * Helper function to format date as ISO string (YYYY-MM-DD)
 */
const formatDateAsISO = (date: Date): string => {
  return date.toISOString().split('T')[0] || '';
};

/**
 * Helper function to get date range for preset
 */
const getDateRangeForPreset = (preset: DateRangePreset): { startDate: string; endDate: string } => {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  let startDate: Date;
  let endDate: Date = today;

  switch (preset) {
    case 'last_7_days':
      startDate = new Date(today);
      startDate.setDate(startDate.getDate() - 7);
      break;
    case 'last_30_days':
      startDate = new Date(today);
      startDate.setDate(startDate.getDate() - 30);
      break;
    case 'last_90_days':
      startDate = new Date(today);
      startDate.setDate(startDate.getDate() - 90);
      break;
    case 'this_month':
      startDate = new Date(today.getFullYear(), today.getMonth(), 1);
      break;
    case 'last_month':
      startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      endDate = new Date(today.getFullYear(), today.getMonth(), 0);
      break;
    case 'this_year':
      startDate = new Date(today.getFullYear(), 0, 1);
      break;
    case 'custom':
    default:
      startDate = new Date(today);
      startDate.setDate(startDate.getDate() - 30);
      break;
  }

  return {
    startDate: formatDateAsISO(startDate),
    endDate: formatDateAsISO(endDate),
  };
};

/**
 * DateRangeFilter Component
 *
 * Provides date range filtering for analytics with:
 * - Start and end date pickers
 * - Preset date ranges (Last 7/30/90 days, This/Last Month, This Year)
 * - Custom date range selection
 * - Apply button to trigger filter
 * - Reset to defaults
 * - Validation ensuring start date <= end date
 *
 * @example
 * ```tsx
 * <DateRangeFilter
 *   onDateRangeChange={(range) => console.log('Date range:', range)}
 *   onApply={(range) => console.log('Apply:', range)}
 * />
 * ```
 *
 * @example
 * ```tsx
 * <DateRangeFilter
 *   initialDateRange={{ preset: 'this_month' }}
 *   onDateRangeChange={(range) => fetchAnalytics(range)}
 *   showPresets={true}
 * />
 * ```
 */
const DateRangeFilter: React.FC<DateRangeFilterProps> = ({
  onDateRangeChange,
  onApply,
  initialDateRange = {},
  showPresets = true,
  disabled = false,
  label = 'Date Range Filter',
}) => {
  // Default date range is last 30 days
  const defaultPreset: DateRangePreset = initialDateRange.preset || 'last_30_days';
  const defaultRange = getDateRangeForPreset(defaultPreset);

  const [preset, setPreset] = useState<DateRangePreset>(defaultPreset);
  const [startDate, setStartDate] = useState<string>(
    initialDateRange.startDate || defaultRange.startDate
  );
  const [endDate, setEndDate] = useState<string>(initialDateRange.endDate || defaultRange.endDate);
  const [error, setError] = useState<string | null>(null);

  /**
   * Handle preset change
   */
  const handlePresetChange = useCallback(
    (event: SelectChangeEvent<DateRangePreset>) => {
      const newPreset = event.target.value as DateRangePreset;
      setPreset(newPreset);

      const range = getDateRangeForPreset(newPreset);
      setStartDate(range.startDate);
      setEndDate(range.endDate);
      setError(null);

      const newDateRange: DateRangeFilter = {
        preset: newPreset,
        startDate: range.startDate,
        endDate: range.endDate,
      };

      onDateRangeChange?.(newDateRange);
    },
    [onDateRangeChange]
  );

  /**
   * Handle start date change
   */
  const handleStartDateChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const newStartDate = event.target.value;
      setStartDate(newStartDate);

      // Switch to custom preset when manually changing dates
      if (preset !== 'custom') {
        setPreset('custom');
      }

      // Validate date range
      if (newStartDate && endDate && newStartDate > endDate) {
        setError('Start date must be before or equal to end date');
      } else {
        setError(null);
      }

      const newDateRange: DateRangeFilter = {
        preset: 'custom',
        startDate: newStartDate,
        endDate: endDate,
      };

      onDateRangeChange?.(newDateRange);
    },
    [preset, endDate, onDateRangeChange]
  );

  /**
   * Handle end date change
   */
  const handleEndDateChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const newEndDate = event.target.value;
      setEndDate(newEndDate);

      // Switch to custom preset when manually changing dates
      if (preset !== 'custom') {
        setPreset('custom');
      }

      // Validate date range
      if (startDate && newEndDate && startDate > newEndDate) {
        setError('End date must be after or equal to start date');
      } else {
        setError(null);
      }

      const newDateRange: DateRangeFilter = {
        preset: 'custom',
        startDate: startDate,
        endDate: newEndDate,
      };

      onDateRangeChange?.(newDateRange);
    },
    [preset, startDate, onDateRangeChange]
  );

  /**
   * Handle preset button click
   */
  const handlePresetClick = useCallback(
    (clickedPreset: DateRangePreset) => {
      setPreset(clickedPreset);

      const range = getDateRangeForPreset(clickedPreset);
      setStartDate(range.startDate);
      setEndDate(range.endDate);
      setError(null);

      const newDateRange: DateRangeFilter = {
        preset: clickedPreset,
        startDate: range.startDate,
        endDate: range.endDate,
      };

      onDateRangeChange?.(newDateRange);
      onApply?.(newDateRange);
    },
    [onDateRangeChange, onApply]
  );

  /**
   * Handle apply button click
   */
  const handleApply = useCallback(() => {
    if (error) {
      return;
    }

    const dateRange: DateRangeFilter = {
      preset,
      startDate,
      endDate,
    };

    onApply?.(dateRange);
  }, [preset, startDate, endDate, error, onApply]);

  /**
   * Handle reset
   */
  const handleReset = useCallback(() => {
    const resetPreset: DateRangePreset = 'last_30_days';
    const range = getDateRangeForPreset(resetPreset);

    setPreset(resetPreset);
    setStartDate(range.startDate);
    setEndDate(range.endDate);
    setError(null);

    const resetDateRange: DateRangeFilter = {
      preset: resetPreset,
      startDate: range.startDate,
      endDate: range.endDate,
    };

    onDateRangeChange?.(resetDateRange);
    onApply?.(resetDateRange);
  }, [onDateRangeChange, onApply]);

  // Update state when initialDateRange prop changes
  useEffect(() => {
    if (initialDateRange.preset) {
      setPreset(initialDateRange.preset);
      const range = getDateRangeForPreset(initialDateRange.preset);
      setStartDate(range.startDate);
      setEndDate(range.endDate);
    }
    if (initialDateRange.startDate) {
      setStartDate(initialDateRange.startDate);
    }
    if (initialDateRange.endDate) {
      setEndDate(initialDateRange.endDate);
    }
  }, [initialDateRange]);

  const isValidDateRange = startDate && endDate && startDate <= endDate;
  const hasError = !!error;

  // Format date for display
  const formatDateDisplay = (dateString: string): string => {
    if (!dateString) return 'Not set';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <Paper elevation={1} sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <DateRangeIcon sx={{ mr: 1, fontSize: 24, color: 'primary.main' }} />
        <Typography variant="h6" fontWeight={600}>
          {label}
        </Typography>
      </Box>
      <Divider sx={{ mb: 2 }} />

      <Stack spacing={3}>
        {/* Preset Quick Select */}
        {showPresets && (
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ mb: 1.5 }}>
              Quick Select:
            </Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} flexWrap="wrap" useFlexGap>
              <Button
                size="small"
                variant={preset === 'last_7_days' ? 'contained' : 'outlined'}
                onClick={() => handlePresetClick('last_7_days')}
                disabled={disabled}
              >
                Last 7 Days
              </Button>
              <Button
                size="small"
                variant={preset === 'last_30_days' ? 'contained' : 'outlined'}
                onClick={() => handlePresetClick('last_30_days')}
                disabled={disabled}
              >
                Last 30 Days
              </Button>
              <Button
                size="small"
                variant={preset === 'last_90_days' ? 'contained' : 'outlined'}
                onClick={() => handlePresetClick('last_90_days')}
                disabled={disabled}
              >
                Last 90 Days
              </Button>
              <Button
                size="small"
                variant={preset === 'this_month' ? 'contained' : 'outlined'}
                onClick={() => handlePresetClick('this_month')}
                disabled={disabled}
              >
                This Month
              </Button>
              <Button
                size="small"
                variant={preset === 'last_month' ? 'contained' : 'outlined'}
                onClick={() => handlePresetClick('last_month')}
                disabled={disabled}
              >
                Last Month
              </Button>
              <Button
                size="small"
                variant={preset === 'this_year' ? 'contained' : 'outlined'}
                onClick={() => handlePresetClick('this_year')}
                disabled={disabled}
              >
                This Year
              </Button>
            </Stack>
          </Box>
        )}

        {/* Custom Date Range */}
        <Box>
          <Typography variant="subtitle2" gutterBottom sx={{ mb: 1.5 }}>
            Custom Date Range:
          </Typography>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            {/* Preset Dropdown */}
            <FormControl size="small" sx={{ minWidth: 150 }} disabled={disabled}>
              <InputLabel>Preset</InputLabel>
              <Select value={preset} onChange={handlePresetChange} label="Preset">
                <MenuItem value="last_7_days">Last 7 Days</MenuItem>
                <MenuItem value="last_30_days">Last 30 Days</MenuItem>
                <MenuItem value="last_90_days">Last 90 Days</MenuItem>
                <MenuItem value="this_month">This Month</MenuItem>
                <MenuItem value="last_month">Last Month</MenuItem>
                <MenuItem value="this_year">This Year</MenuItem>
                <MenuItem value="custom">Custom</MenuItem>
              </Select>
            </FormControl>

            {/* Start Date */}
            <TextField
              type="date"
              label="Start Date"
              value={startDate}
              onChange={handleStartDateChange}
              size="small"
              disabled={disabled}
              InputLabelProps={{
                shrink: true,
              }}
              error={hasError}
            />

            {/* End Date */}
            <TextField
              type="date"
              label="End Date"
              value={endDate}
              onChange={handleEndDateChange}
              size="small"
              disabled={disabled}
              InputLabelProps={{
                shrink: true,
              }}
              error={hasError}
            />
          </Stack>
        </Box>

        {/* Error Message */}
        {hasError && (
          <Alert severity="error" variant="outlined">
            {error}
          </Alert>
        )}

        {/* Current Filter Display */}
        {isValidDateRange && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Active Filter:
            </Typography>
            <Chip
              icon={<DateRangeIcon fontSize="small" />}
              label={`${formatDateDisplay(startDate)} - ${formatDateDisplay(endDate)}`}
              color="primary"
              variant="outlined"
              size="medium"
            />
          </Box>
        )}

        {/* Action Buttons */}
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <Button
            fullWidth
            variant="contained"
            startIcon={<ApplyIcon />}
            onClick={handleApply}
            disabled={disabled || !isValidDateRange}
            color="primary"
          >
            Apply Filter
          </Button>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<ResetIcon />}
            onClick={handleReset}
            disabled={disabled}
            color="secondary"
          >
            Reset to Last 30 Days
          </Button>
        </Stack>

        {/* Info Alert */}
        <Alert severity="info" variant="outlined">
          <Typography variant="body2">
            <strong>Tip:</strong> Use quick select buttons for common date ranges or choose custom
            dates for more precise filtering. All analytics components will update to reflect the
            selected date range.
          </Typography>
        </Alert>
      </Stack>
    </Paper>
  );
};

export default DateRangeFilter;
