import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  CircularProgress,
  Alert,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Chip,
  InputAdornment,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { useTranslation } from 'react-i18next';
import { profilesClient } from '@/api/profiles';
import type {
  WorkHistoryItem,
  WorkHistoryCreate,
  WorkHistoryUpdate,
  ApiError,
  EmploymentType,
} from '@/types/api';

/**
 * WorkHistoryEditor Component Props
 */
interface WorkHistoryEditorProps {
  /** Existing work history item to edit (optional) */
  workHistoryItem?: WorkHistoryItem;
  /** Callback when work history is saved successfully */
  onSave?: (item: WorkHistoryItem) => void;
  /** Callback when form is cancelled */
  onCancel?: () => void;
  /** Whether the component is in read-only mode */
  readOnly?: boolean;
  /** Resume ID for creating new work history entries */
  resumeId?: string;
}

/**
 * Form state interface
 */
interface FormState {
  company_name: string;
  position_title: string;
  start_date: string;
  end_date: string;
  description: string;
  location: string;
  employment_type: EmploymentType;
  is_current: boolean;
}

/**
 * Employment type options for the select dropdown
 */
const EMPLOYMENT_TYPE_OPTIONS: { value: EmploymentType; label: string }[] = [
  { value: 'full_time', label: 'Full Time' },
  { value: 'part_time', label: 'Part Time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
  { value: 'freelance', label: 'Freelance' },
  { value: 'self_employed', label: 'Self Employed' },
];

/**
 * WorkHistoryEditor Component
 *
 * Form component for adding and editing work experience entries:
 * - Supports both create and update modes
 * - Handles all work history fields (company, position, dates, etc.)
 * - Validates required fields before submission
 * - Supports marking positions as "current" (no end date)
 * - Handles loading and error states gracefully
 * - Notifies parent on successful save
 *
 * @example
 * ```tsx
 * // Adding new work history
 * <WorkHistoryEditor
 *   onSave={(item) => console.log('Saved:', item)}
 *   onCancel={() => console.log('Cancelled')}
 * />
 *
 * // Editing existing work history
 * <WorkHistoryEditor
 *   workHistoryItem={existingItem}
 *   onSave={(item) => console.log('Updated:', item)}
 *   onCancel={() => console.log('Cancelled')}
 * />
 *
 * // Read-only view
 * <WorkHistoryEditor
 *   workHistoryItem={existingItem}
 *   readOnly
 * />
 * ```
 */
const WorkHistoryEditor: React.FC<WorkHistoryEditorProps> = ({
  workHistoryItem,
  onSave,
  onCancel,
  readOnly = false,
}) => {
  const { t } = useTranslation();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<FormState>({
    company_name: workHistoryItem?.company_name || '',
    position_title: workHistoryItem?.position_title || '',
    start_date: workHistoryItem?.start_date || '',
    end_date: workHistoryItem?.end_date || '',
    description: workHistoryItem?.description || '',
    location: workHistoryItem?.location || '',
    employment_type: workHistoryItem?.employment_type || 'full_time',
    is_current: !workHistoryItem?.end_date,
  });

  // Validation errors
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof FormState, string>>>({});

  /**
   * Update form data when workHistoryItem changes externally
   */
  useEffect(() => {
    if (workHistoryItem) {
      setFormData({
        company_name: workHistoryItem.company_name,
        position_title: workHistoryItem.position_title,
        start_date: workHistoryItem.start_date,
        end_date: workHistoryItem.end_date || '',
        description: workHistoryItem.description || '',
        location: workHistoryItem.location || '',
        employment_type: workHistoryItem.employment_type,
        is_current: !workHistoryItem.end_date,
      });
    }
  }, [workHistoryItem]);

  /**
   * Validate form fields
   */
  const validateForm = useCallback((): boolean => {
    const errors: Partial<Record<keyof FormState, string>> = {};

    if (!formData.company_name.trim()) {
      errors.company_name = 'Company name is required';
    }

    if (!formData.position_title.trim()) {
      errors.position_title = 'Position title is required';
    }

    if (!formData.start_date) {
      errors.start_date = 'Start date is required';
    } else {
      // Validate start date is not in the future
      const startDate = new Date(formData.start_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (startDate > today) {
        errors.start_date = 'Start date cannot be in the future';
      }
    }

    if (!formData.is_current) {
      if (!formData.end_date) {
        errors.end_date = 'End date is required when not current';
      } else {
        // Validate end date is after start date
        const startDate = new Date(formData.start_date);
        const endDate = new Date(formData.end_date);
        if (endDate <= startDate) {
          errors.end_date = 'End date must be after start date';
        }

        // Validate end date is not in the future (more than today)
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        if (endDate > today) {
          errors.end_date = 'End date cannot be in the future';
        }
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formData]);

  /**
   * Handle input field changes
   */
  const handleFieldChange = useCallback(
    (field: keyof FormState) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const value = event.target.type === 'checkbox'
        ? (event.target as HTMLInputElement).checked
        : event.target.value;

      setFormData((prev) => ({
        ...prev,
        [field]: value,
      }));

      // Clear field error when user starts typing
      if (fieldErrors[field]) {
        setFieldErrors((prev) => ({
          ...prev,
          [field]: undefined,
        }));
      }
    },
    [fieldErrors]
  );

  /**
   * Handle employment type change
   */
  const handleEmploymentTypeChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value as EmploymentType;
    setFormData((prev) => ({
      ...prev,
      employment_type: value,
    }));
  }, []);

  /**
   * Handle "is current" checkbox change
   */
  const handleIsCurrentChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const isCurrent = event.target.checked;
    setFormData((prev) => ({
      ...prev,
      is_current: isCurrent,
      end_date: isCurrent ? '' : prev.end_date,
    }));

    // Clear end_date error if marking as current
    if (isCurrent && fieldErrors.end_date) {
      setFieldErrors((prev) => ({
        ...prev,
        end_date: undefined,
      }));
    }
  }, [fieldErrors]);

  /**
   * Handle form submission
   */
  const handleSubmit = useCallback(async () => {
    // Validate form
    if (!validateForm()) {
      setError('Please fix the validation errors before submitting.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const submitData: WorkHistoryCreate | WorkHistoryUpdate = {
        company_name: formData.company_name.trim(),
        position_title: formData.position_title.trim(),
        start_date: formData.start_date,
        end_date: formData.is_current ? undefined : formData.end_date || undefined,
        description: formData.description.trim() || undefined,
        location: formData.location.trim() || undefined,
        employment_type: formData.employment_type,
      };

      let result: WorkHistoryItem;

      if (workHistoryItem?.id) {
        // Update existing work history
        result = await profilesClient.updateWorkHistory(workHistoryItem.id, submitData);
      } else {
        // Create new work history
        result = await profilesClient.createWorkHistory(submitData);
      }

      setSuccessMessage(workHistoryItem?.id ? 'Work history updated successfully.' : 'Work history added successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);

      // Notify parent
      onSave?.(result);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to save work history. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [formData, validateForm, workHistoryItem, onSave]);

  /**
   * Handle cancel action
   */
  const handleCancel = useCallback(() => {
    onCancel?.();
  }, [onCancel]);

  // Read-only mode display
  if (readOnly && workHistoryItem) {
    return (
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack spacing={2}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box>
              <Typography variant="h6" fontWeight={600}>
                {workHistoryItem.position_title}
              </Typography>
              <Typography variant="body1" color="primary">
                {workHistoryItem.company_name}
              </Typography>
            </Box>
            <Chip
              label={workHistoryItem.employment_type.replace('_', ' ')}
              size="small"
              color="secondary"
              variant="outlined"
            />
          </Box>

          <Stack direction="row" spacing={2} flexWrap="wrap">
            <Stack direction="row" spacing={0.5} alignItems="center">
              <Icon name="calendar" size={16} />
              <Typography variant="body2" color="text.secondary">
                {workHistoryItem.start_date} - {workHistoryItem.end_date || 'Present'}
              </Typography>
            </Stack>
            {workHistoryItem.location && (
              <Stack direction="row" spacing={0.5} alignItems="center">
                <Icon name="map-pin" size={16} />
                <Typography variant="body2" color="text.secondary">
                  {workHistoryItem.location}
                </Typography>
              </Stack>
            )}
          </Stack>

          {workHistoryItem.description && (
            <>
              <Divider />
              <Typography variant="body2" color="primary" sx={{ whiteSpace: 'pre-wrap' }}>
                {workHistoryItem.description}
              </Typography>
            </>
          )}
        </Stack>
      </Paper>
    );
  }

  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack spacing={2.5}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" fontWeight={600}>
            {workHistoryItem?.id ? 'Edit Work Experience' : 'Add Work Experience'}
          </Typography>
          {workHistoryItem?.id && (
            <Chip label="Editing" size="small" color="primary" variant="outlined" />
          )}
        </Box>

        <Divider />

        {/* Error Message */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Success Message */}
        {successMessage && (
          <Alert
            severity="success"
            icon={<Icon name="check-circle" size={20} />}
            onClose={() => setSuccessMessage(null)}
          >
            {successMessage}
          </Alert>
        )}

        {/* Form Fields */}
        <Stack spacing={2}>
          {/* Company Name */}
          <TextField
            label="Company Name"
            placeholder="e.g., Acme Corporation"
            value={formData.company_name}
            onChange={handleFieldChange('company_name')}
            error={!!fieldErrors.company_name}
            helperText={fieldErrors.company_name}
            disabled={submitting || readOnly}
            fullWidth
            required
            size="small"
          />

          {/* Position Title */}
          <TextField
            label="Position Title"
            placeholder="e.g., Senior Software Engineer"
            value={formData.position_title}
            onChange={handleFieldChange('position_title')}
            error={!!fieldErrors.position_title}
            helperText={fieldErrors.position_title}
            disabled={submitting || readOnly}
            fullWidth
            required
            size="small"
          />

          {/* Employment Type */}
          <FormControl fullWidth size="small" disabled={submitting || readOnly}>
            <InputLabel>Employment Type</InputLabel>
            <Select
              value={formData.employment_type}
              onChange={handleEmploymentTypeChange}
              label="Employment Type"
            >
              {EMPLOYMENT_TYPE_OPTIONS.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Dates Row */}
          <Stack direction="row" spacing={2}>
            {/* Start Date */}
            <TextField
              label="Start Date"
              type="date"
              value={formData.start_date}
              onChange={handleFieldChange('start_date')}
              error={!!fieldErrors.start_date}
              helperText={fieldErrors.start_date}
              disabled={submitting || readOnly}
              fullWidth
              required
              size="small"
              InputLabelProps={{ shrink: true }}
            />

            {/* End Date */}
            <TextField
              label="End Date"
              type="date"
              value={formData.end_date}
              onChange={handleFieldChange('end_date')}
              error={!!fieldErrors.end_date}
              helperText={fieldErrors.end_date}
              disabled={submitting || readOnly || formData.is_current}
              fullWidth
              required={!formData.is_current}
              size="small"
              InputLabelProps={{ shrink: true }}
            />
          </Stack>

          {/* Current Position Checkbox */}
          <FormControlLabel
            control={
              <Checkbox
                checked={formData.is_current}
                onChange={handleIsCurrentChange}
                disabled={submitting || readOnly}
                color="primary"
              />
            }
            label="I currently work here"
          />

          {/* Location */}
          <TextField
            label="Location"
            placeholder="e.g., San Francisco, CA or Remote"
            value={formData.location}
            onChange={handleFieldChange('location')}
            disabled={submitting || readOnly}
            fullWidth
            size="small"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Icon name="map-pin" size={18} />
                </InputAdornment>
              ),
            }}
          />

          {/* Description */}
          <TextField
            multiline
            rows={4}
            label="Description"
            placeholder="Describe your responsibilities, achievements, and impact in this role..."
            value={formData.description}
            onChange={handleFieldChange('description')}
            disabled={submitting || readOnly}
            fullWidth
            size="small"
          />
        </Stack>

        {/* Action Buttons */}
        {!readOnly && (
          <Stack direction="row" spacing={1.5} justifyContent="flex-end" sx={{ pt: 1 }}>
            <Button
              variant="outlined"
              onClick={handleCancel}
              disabled={submitting}
              size="small"
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={submitting}
              startIcon={
                submitting ? <CircularProgress size={16} /> : <Icon name={workHistoryItem?.id ? 'save' : 'plus'} size={16} />
              }
              size="small"
            >
              {submitting ? 'Saving...' : workHistoryItem?.id ? 'Update' : 'Add'}
            </Button>
          </Stack>
        )}
      </Stack>
    </Paper>
  );
};

export default WorkHistoryEditor;
