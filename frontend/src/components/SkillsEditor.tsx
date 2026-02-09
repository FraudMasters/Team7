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
  Grid,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { useTranslation } from 'react-i18next';
import { profilesClient } from '@/api/profiles';
import type {
  SkillItem,
  SkillCreate,
  SkillUpdate,
  ApiError,
  ProficiencyLevel,
} from '@/types/api';

/**
 * SkillsEditor Component Props
 */
interface SkillsEditorProps {
  /** Existing skill item to edit (optional) */
  skillItem?: SkillItem;
  /** Callback when skill is saved successfully */
  onSave?: (item: SkillItem) => void;
  /** Callback when form is cancelled */
  onCancel?: () => void;
  /** Whether the component is in read-only mode */
  readOnly?: boolean;
  /** Available skill suggestions for autocomplete */
  skillSuggestions?: string[];
}

/**
 * Form state interface
 */
interface FormState {
  name: string;
  category: string;
  proficiency_level: ProficiencyLevel;
  years_of_experience: string;
  description: string;
}

/**
 * Proficiency level options for the select dropdown
 */
const PROFICIENCY_LEVEL_OPTIONS: { value: ProficiencyLevel; label: string }[] = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
  { value: 'expert', label: 'Expert' },
];

/**
 * Default skill categories for suggestions
 */
const DEFAULT_CATEGORIES = [
  'Programming Languages',
  'Frameworks & Libraries',
  'Databases',
  'Cloud Platforms',
  'Tools & DevOps',
  'Design',
  'Soft Skills',
  'Languages',
  'Project Management',
  'Data Science',
  'Other',
];

/**
 * SkillsEditor Component
 *
 * Компонент формы для добавления и редактирования навыков:
 * - Поддерживает режимы создания и обновления
 * - Обрабатывает все поля навыков (название, категория, уровень владения, опыт, описание)
 * - Валидирует обязательные поля перед отправкой
 * - Использует автодополнение для выбора навыков
 * - Обрабатывает состояния загрузки и ошибок
 * - Уведомляет родительский компонент при успешном сохранении
 *
 * @example
 * ```tsx
 * // Добавление нового навыка
 * <SkillsEditor
 *   onSave={(item) => console.log('Saved:', item)}
 *   onCancel={() => console.log('Cancelled')}
 * />
 *
 * // Редактирование существующего навыка
 * <SkillsEditor
 *   skillItem={existingItem}
 *   onSave={(item) => console.log('Updated:', item)}
 *   onCancel={() => console.log('Cancelled')}
 * />
 *
 * // Режим только для чтения
 * <SkillsEditor
 *   skillItem={existingItem}
 *   readOnly
 * />
 * ```
 */
const SkillsEditor: React.FC<SkillsEditorProps> = ({
  skillItem,
  onSave,
  onCancel,
  readOnly = false,
  skillSuggestions = [],
}) => {
  const { t } = useTranslation();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<FormState>({
    name: skillItem?.name || '',
    category: skillItem?.category || '',
    proficiency_level: skillItem?.proficiency_level || 'intermediate',
    years_of_experience: skillItem?.years_of_experience?.toString() || '',
    description: skillItem?.description || '',
  });

  // Validation errors
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof FormState, string>>>({});

  /**
   * Update form data when skillItem changes externally
   */
  useEffect(() => {
    if (skillItem) {
      setFormData({
        name: skillItem.name,
        category: skillItem.category || '',
        proficiency_level: skillItem.proficiency_level,
        years_of_experience: skillItem.years_of_experience?.toString() || '',
        description: skillItem.description || '',
      });
    }
  }, [skillItem]);

  /**
   * Validate form fields
   */
  const validateForm = useCallback((): boolean => {
    const errors: Partial<Record<keyof FormState, string>> = {};

    if (!formData.name.trim()) {
      errors.name = 'Skill name is required';
    }

    if (!formData.category.trim()) {
      errors.category = 'Category is required';
    }

    if (formData.years_of_experience) {
      const years = parseFloat(formData.years_of_experience);
      if (isNaN(years) || years < 0 || years > 50) {
        errors.years_of_experience = 'Please enter a valid number between 0 and 50';
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
   * Handle proficiency level change
   */
  const handleProficiencyLevelChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value as ProficiencyLevel;
    setFormData((prev) => ({
      ...prev,
      proficiency_level: value,
    }));
  }, []);

  /**
   * Handle skill name change from autocomplete
   */
  const handleSkillNameChange = useCallback((_: React.SyntheticEvent, value: string[]) => {
    const name = value[0] || '';
    setFormData((prev) => ({
      ...prev,
      name,
    }));

    // Clear field error when user selects a skill
    if (fieldErrors.name && name) {
      setFieldErrors((prev) => ({
        ...prev,
        name: undefined,
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

      const submitData: SkillCreate | SkillUpdate = {
        name: formData.name.trim(),
        category: formData.category.trim() || undefined,
        proficiency_level: formData.proficiency_level,
        years_of_experience: formData.years_of_experience
          ? parseFloat(formData.years_of_experience)
          : undefined,
        description: formData.description.trim() || undefined,
      };

      let result: SkillItem;

      if (skillItem?.id) {
        // Update existing skill
        result = await profilesClient.updateSkill(skillItem.id, submitData);
      } else {
        // Create new skill
        result = await profilesClient.createSkill(submitData);
      }

      setSuccessMessage(skillItem?.id ? 'Skill updated successfully.' : 'Skill added successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);

      // Notify parent
      onSave?.(result);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to save skill. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [formData, validateForm, skillItem, onSave]);

  /**
   * Handle cancel action
   */
  const handleCancel = useCallback(() => {
    onCancel?.();
  }, [onCancel]);

  /**
   * Get proficiency level color
   */
  const getProficiencyColor = (level: ProficiencyLevel): 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' => {
    switch (level) {
      case 'beginner':
        return 'default';
      case 'intermediate':
        return 'info';
      case 'advanced':
        return 'primary';
      case 'expert':
        return 'success';
      default:
        return 'default';
    }
  };

  // Read-only mode display
  if (readOnly && skillItem) {
    return (
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack spacing={2}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box>
              <Typography variant="h6" fontWeight={600}>
                {skillItem.name}
              </Typography>
              {skillItem.category && (
                <Typography variant="body2" color="text.secondary">
                  {skillItem.category}
                </Typography>
              )}
            </Box>
            <Chip
              label={skillItem.proficiency_level}
              size="small"
              color={getProficiencyColor(skillItem.proficiency_level)}
              variant="filled"
            />
          </Box>

          {skillItem.years_of_experience && (
            <Stack direction="row" spacing={0.5} alignItems="center">
              <Icon name="clock" size={16} />
              <Typography variant="body2" color="text.secondary">
                {skillItem.years_of_experience} {skillItem.years_of_experience === 1 ? 'year' : 'years'} of experience
              </Typography>
            </Stack>
          )}

          {skillItem.description && (
            <>
              <Divider />
              <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-wrap' }}>
                {skillItem.description}
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
            {skillItem?.id ? 'Edit Skill' : 'Add Skill'}
          </Typography>
          {skillItem?.id && (
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
          {/* Skill Name with Autocomplete */}
          <TextField
            label="Skill Name"
            placeholder="e.g., Python, React, Project Management"
            value={formData.name}
            onChange={handleFieldChange('name')}
            error={!!fieldErrors.name}
            helperText={fieldErrors.name || 'Start typing to see suggestions...'}
            disabled={submitting || readOnly}
            fullWidth
            required
            size="small"
            list="skill-suggestions"
          />
          <datalist id="skill-suggestions">
            {skillSuggestions.map((skill) => (
              <option key={skill} value={skill} />
            ))}
          </datalist>

          {/* Category */}
          <TextField
            label="Category"
            placeholder="e.g., Programming Languages, Tools, Soft Skills"
            value={formData.category}
            onChange={handleFieldChange('category')}
            error={!!fieldErrors.category}
            helperText={fieldErrors.category}
            disabled={submitting || readOnly}
            fullWidth
            required
            size="small"
            list="category-suggestions"
          />
          <datalist id="category-suggestions">
            {DEFAULT_CATEGORIES.map((cat) => (
              <option key={cat} value={cat} />
            ))}
          </datalist>

          {/* Grid for Proficiency Level and Years of Experience */}
          <Grid container spacing={2}>
            {/* Proficiency Level */}
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small" disabled={submitting || readOnly}>
                <InputLabel>Proficiency Level</InputLabel>
                <Select
                  value={formData.proficiency_level}
                  onChange={handleProficiencyLevelChange}
                  label="Proficiency Level"
                >
                  {PROFICIENCY_LEVEL_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Years of Experience */}
            <Grid item xs={12} sm={6}>
              <TextField
                label="Years of Experience"
                type="number"
                placeholder="e.g., 3"
                value={formData.years_of_experience}
                onChange={handleFieldChange('years_of_experience')}
                error={!!fieldErrors.years_of_experience}
                helperText={fieldErrors.years_of_experience}
                disabled={submitting || readOnly}
                fullWidth
                size="small"
                inputProps={{ min: 0, max: 50, step: 0.1 }}
              />
            </Grid>
          </Grid>

          {/* Description */}
          <TextField
            multiline
            rows={3}
            label="Description"
            placeholder="Provide details about your experience with this skill..."
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
                submitting ? <CircularProgress size={16} /> : <Icon name={skillItem?.id ? 'save' : 'plus'} size={16} />
              }
              size="small"
            >
              {submitting ? 'Saving...' : skillItem?.id ? 'Update' : 'Add'}
            </Button>
          </Stack>
        )}
      </Stack>
    </Paper>
  );
};

export default SkillsEditor;
