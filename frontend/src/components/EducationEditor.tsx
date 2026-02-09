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
  Chip,
  InputAdornment,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { useTranslation } from 'react-i18next';
import { profilesClient } from '@/api/profiles';
import type {
  EducationItem,
  EducationCreate,
  EducationUpdate,
  ApiError,
  DegreeType,
} from '@/types/api';

/**
 * EducationEditor Component Props
 */
interface EducationEditorProps {
  /** Existing education item to edit (optional) */
  educationItem?: EducationItem;
  /** Callback when education is saved successfully */
  onSave?: (item: EducationItem) => void;
  /** Callback when form is cancelled */
  onCancel?: () => void;
  /** Whether the component is in read-only mode */
  readOnly?: boolean;
  /** Resume ID for creating new education entries */
  resumeId?: string;
}

/**
 * Form state interface
 */
interface FormState {
  institution_name: string;
  degree: string;
  field_of_study: string;
  start_date: string;
  end_date: string;
  description: string;
  location: string;
  degree_type: DegreeType;
}

/**
 * Degree type options for the select dropdown
 */
const DEGREE_TYPE_OPTIONS: { value: DegreeType; label: string }[] = [
  { value: 'high_school', label: 'High School' },
  { value: 'associate', label: 'Associate Degree' },
  { value: 'bachelor', label: 'Bachelor\'s Degree' },
  { value: 'master', label: 'Master\'s Degree' },
  { value: 'doctorate', label: 'Doctorate' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'other', label: 'Other' },
];

/**
 * EducationEditor Component
 *
 * Form component for adding and editing education entries:
 * - Supports both create and update modes
 * - Handles all education fields (institution, degree, dates, etc.)
 * - Validates required fields before submission
 * - Handles loading and error states gracefully
 * - Notifies parent on successful save
 *
 * @example
 * ```tsx
 * // Adding new education
 * <EducationEditor
 *   onSave={(item) => console.log('Saved:', item)}
 *   onCancel={() => console.log('Cancelled')}
 * />
 *
 * // Editing existing education
 * <EducationEditor
 *   educationItem={existingItem}
 *   onSave={(item) => console.log('Updated:', item)}
 *   onCancel={() => console.log('Cancelled')}
 * />
 *
 * // Read-only view
 * <EducationEditor
 *   educationItem={existingItem}
 *   readOnly
 * />
 * ```
 */
const EducationEditor: React.FC<EducationEditorProps> = ({
  educationItem,
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
    institution_name: educationItem?.institution_name || '',
    degree: educationItem?.degree || '',
    field_of_study: educationItem?.field_of_study || '',
    start_date: educationItem?.start_date || '',
    end_date: educationItem?.end_date || '',
    description: educationItem?.description || '',
    location: educationItem?.location || '',
    degree_type: educationItem?.degree_type || 'bachelor',
  });

  // Validation errors
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof FormState, string>>>({});

  /**
   * Update form data when educationItem changes externally
   */
  useEffect(() => {
    if (educationItem) {
      setFormData({
        institution_name: educationItem.institution_name,
        degree: educationItem.degree,
        field_of_study: educationItem.field_of_study || '',
        start_date: educationItem.start_date,
        end_date: educationItem.end_date || '',
        description: educationItem.description || '',
        location: educationItem.location || '',
        degree_type: educationItem.degree_type,
      });
    }
  }, [educationItem]);

  /**
   * Validate form fields
   */
  const validateForm = useCallback((): boolean => {
    const errors: Partial<Record<keyof FormState, string>> = {};

    if (!formData.institution_name.trim()) {
      errors.institution_name = 'Institution name is required';
    }

    if (!formData.degree.trim()) {
      errors.degree = 'Degree is required';
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

    if (formData.end_date) {
      // Validate end date is after start date
      const startDate = new Date(formData.start_date);
      const endDate = new Date(formData.end_date);
      if (endDate <= startDate) {
        errors.end_date = 'End date must be after start date';
      }

      // Validate end date is not in the future
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (endDate > today) {
        errors.end_date = 'End date cannot be in the future';
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
      const value = event.target.value;

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
   * Handle degree type change
   */
  const handleDegreeTypeChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value as DegreeType;
    setFormData((prev) => ({
      ...prev,
      degree_type: value,
    }));
  }, []);

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

      const submitData: EducationCreate | EducationUpdate = {
        institution_name: formData.institution_name.trim(),
        degree: formData.degree.trim(),
        field_of_study: formData.field_of_study.trim() || undefined,
        start_date: formData.start_date,
        end_date: formData.end_date || undefined,
        description: formData.description.trim() || undefined,
        location: formData.location.trim() || undefined,
        degree_type: formData.degree_type,
      };

      let result: EducationItem;

      if (educationItem?.id) {
        // Update existing education
        result = await profilesClient.updateEducation(educationItem.id, submitData);
      } else {
        // Create new education
        result = await profilesClient.createEducation(submitData);
      }

      setSuccessMessage(educationItem?.id ? 'Education updated successfully.' : 'Education added successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);

      // Notify parent
      onSave?.(result);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to save education. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [formData, validateForm, educationItem, onSave]);

  /**
   * Handle cancel action
   */
  const handleCancel = useCallback(() => {
    onCancel?.();
  }, [onCancel]);

  // Read-only mode display
  if (readOnly && educationItem) {
    return (
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack spacing={2}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box>
              <Typography variant="h6" fontWeight={600}>
                {educationItem.degree}
              </Typography>
              <Typography variant="body1" color="primary">
                {educationItem.institution_name}
              </Typography>
            </Box>
            <Chip
              label={educationItem.degree_type.replace('_', ' ')}
              size="small"
              color="secondary"
              variant="outlined"
            />
          </Box>

          <Stack direction="row" spacing={2} flexWrap="wrap">
            <Stack direction="row" spacing={0.5} alignItems="center">
              <Icon name="calendar" size={16} />
              <Typography variant="body2" color="text.secondary">
                {educationItem.start_date} - {educationItem.end_date || 'Present'}
              </Typography>
            </Stack>
            {educationItem.location && (
              <Stack direction="row" spacing={0.5} alignItems="center">
                <Icon name="map-pin" size={16} />
                <Typography variant="body2" color="text.secondary">
                  {educationItem.location}
                </Typography>
              </Stack>
            )}
          </Stack>

          {educationItem.field_of_study && (
            <Typography variant="body2" color="text.secondary">
              Field of Study: {educationItem.field_of_study}
            </Typography>
          )}

          {educationItem.description && (
            <>
              <Divider />
              <Typography variant="body2" color="primary" sx={{ whiteSpace: 'pre-wrap' }}>
                {educationItem.description}
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
            {educationItem?.id ? 'Edit Education' : 'Add Education'}
          </Typography>
          {educationItem?.id && (
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
          {/* Institution Name */}
          <TextField
            label="Institution Name"
            placeholder="e.g., Massachusetts Institute of Technology"
            value={formData.institution_name}
            onChange={handleFieldChange('institution_name')}
            error={!!fieldErrors.institution_name}
            helperText={fieldErrors.institution_name}
            disabled={submitting || readOnly}
            fullWidth
            required
            size="small"
          />

          {/* Degree */}
          <TextField
            label="Degree"
            placeholder="e.g., Bachelor of Science"
            value={formData.degree}
            onChange={handleFieldChange('degree')}
            error={!!fieldErrors.degree}
            helperText={fieldErrors.degree}
            disabled={submitting || readOnly}
            fullWidth
            required
            size="small"
          />

          {/* Field of Study */}
          <TextField
            label="Field of Study"
            placeholder="e.g., Computer Science"
            value={formData.field_of_study}
            onChange={handleFieldChange('field_of_study')}
            disabled={submitting || readOnly}
            fullWidth
            size="small"
          />

          {/* Degree Type */}
          <FormControl fullWidth size="small" disabled={submitting || readOnly}>
            <InputLabel>Degree Type</InputLabel>
            <Select
              value={formData.degree_type}
              onChange={handleDegreeTypeChange}
              label="Degree Type"
            >
              {DEGREE_TYPE_OPTIONS.map((option) => (
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
              disabled={submitting || readOnly}
              fullWidth
              size="small"
              InputLabelProps={{ shrink: true }}
            />
          </Stack>

          {/* Location */}
          <TextField
            label="Location"
            placeholder="e.g., Cambridge, MA"
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
            placeholder="Describe your achievements, honors, thesis, or other notable details..."
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
                submitting ? <CircularProgress size={16} /> : <Icon name={educationItem?.id ? 'save' : 'plus'} size={16} />
              }
              size="small"
            >
              {submitting ? 'Saving...' : educationItem?.id ? 'Update' : 'Add'}
            </Button>
          </Stack>
        )}
      </Stack>
    </Paper>
  );
};

export default EducationEditor;
