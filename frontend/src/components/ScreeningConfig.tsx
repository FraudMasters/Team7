import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  Divider,
  Stack,
  Chip,
  Autocomplete,
  FormControl,
  InputLabel,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { apiClient } from '@/api';
import type {
  ScreeningRule,
  ScreeningRuleCreate,
  ScreeningRuleUpdate,
} from '@/types/api';

/**
 * Validation error interface
 */
interface ValidationError {
  field: string;
  message: string;
}

/**
 * ScreeningConfig Component Props
 */
interface ScreeningConfigProps {
  /** Vacancy ID to configure screening for */
  vacancyId: string;
  /** Existing screening rule to edit (optional) */
  existingRule?: ScreeningRule;
  /** Callback when rule is saved successfully */
  onSaveSuccess?: (rule: ScreeningRule) => void;
  /** Disabled state */
  disabled?: boolean;
}

/**
 * ScreeningConfig Component
 *
 * Provides a form interface for configuring per-vacancy screening rules:
 * - Set minimum score thresholds (0-100)
 * - Configure must-have skills with autocomplete
 * - Set auto-reject thresholds
 * - Enable/disable auto-reject with notification
 * - Set high-priority thresholds
 * - Form validation ensures threshold relationships
 * - Visual feedback for save status and errors
 *
 * @example
 * ```tsx
 * <ScreeningConfig
 *   vacancyId="vacancy-123"
 *   onSaveSuccess={(rule) => console.log('Rule saved:', rule)}
 * />
 * ```
 */
const ScreeningConfig: React.FC<ScreeningConfigProps> = ({
  vacancyId,
  existingRule,
  onSaveSuccess,
  disabled = false,
}) => {
  const { t } = useTranslation();

  // Form state
  const [minScoreThreshold, setMinScoreThreshold] = useState<number>(
    existingRule?.min_score_threshold ?? 60
  );
  const [autoRejectThreshold, setAutoRejectThreshold] = useState<number>(
    existingRule?.auto_reject_threshold ?? 30
  );
  const [highPriorityThreshold, setHighPriorityThreshold] = useState<number>(
    existingRule?.high_priority_threshold ?? 80
  );
  const [autoRejectWithNotification, setAutoRejectWithNotification] = useState<boolean>(
    existingRule?.auto_reject_with_notification ?? false
  );
  const [mustHaveSkills, setMustHaveSkills] = useState<string[]>(
    existingRule?.must_have_skills ?? []
  );
  const [rulePriority, setRulePriority] = useState<number>(
    existingRule?.rule_priority ?? 0
  );

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);

  /**
   * Validate form inputs
   */
  const validateForm = useCallback((): boolean => {
    const errors: ValidationError[] = [];

    // Validate thresholds are within 0-100
    if (minScoreThreshold < 0 || minScoreThreshold > 100) {
      errors.push({
        field: 'minScoreThreshold',
        message: t('screeningConfig.validation.minScoreRange', { min: 0, max: 100 }),
      });
    }

    if (autoRejectThreshold < 0 || autoRejectThreshold > 100) {
      errors.push({
        field: 'autoRejectThreshold',
        message: t('screeningConfig.validation.autoRejectRange', { min: 0, max: 100 }),
      });
    }

    if (highPriorityThreshold < 0 || highPriorityThreshold > 100) {
      errors.push({
        field: 'highPriorityThreshold',
        message: t('screeningConfig.validation.highPriorityRange', { min: 0, max: 100 }),
      });
    }

    // Validate threshold relationships: high_priority >= min_score >= auto_reject
    if (highPriorityThreshold < minScoreThreshold) {
      errors.push({
        field: 'highPriorityThreshold',
        message: t('screeningConfig.validation.highPriorityMustBeGreater'),
      });
    }

    if (minScoreThreshold < autoRejectThreshold) {
      errors.push({
        field: 'minScoreThreshold',
        message: t('screeningConfig.validation.minScoreMustBeGreater'),
      });
    }

    // Validate rule priority
    if (rulePriority < 0) {
      errors.push({
        field: 'rulePriority',
        message: t('screeningConfig.validation.priorityMustBePositive'),
      });
    }

    setValidationErrors(errors);
    return errors.length === 0;
  }, [
    minScoreThreshold,
    autoRejectThreshold,
    highPriorityThreshold,
    rulePriority,
    t,
  ]);

  /**
   * Handle save button click
   */
  const handleSave = useCallback(async () => {
    if (disabled || isSaving) {
      return;
    }

    // Validate form
    if (!validateForm()) {
      setError(t('screeningConfig.errors.validationFailed'));
      return;
    }

    setIsSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const ruleData: ScreeningRuleCreate | ScreeningRuleUpdate = {
        min_score_threshold: minScoreThreshold,
        must_have_skills: mustHaveSkills,
        auto_reject_threshold: autoRejectThreshold,
        auto_reject_with_notification: autoRejectWithNotification,
        high_priority_threshold: highPriorityThreshold,
        rule_priority: rulePriority,
        is_active: true,
      };

      let savedRule: ScreeningRule;

      if (existingRule) {
        // Update existing rule
        const response = await apiClient.put<ScreeningRule>(
          `/api/screening/rules/${existingRule.id}`,
          ruleData
        );
        savedRule = response.data;
      } else {
        // Create new rule
        const createData: ScreeningRuleCreate = {
          ...ruleData,
          vacancy_id: vacancyId,
        } as ScreeningRuleCreate;
        const response = await apiClient.post<ScreeningRule>(
          '/api/screening/rules',
          createData
        );
        savedRule = response.data;
      }

      setSuccess(true);
      onSaveSuccess?.(savedRule);

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('screeningConfig.errors.saveFailed');
      setError(errorMessage);
    } finally {
      setIsSaving(false);
    }
  }, [
    disabled,
    isSaving,
    validateForm,
    existingRule,
    minScoreThreshold,
    mustHaveSkills,
    autoRejectThreshold,
    autoRejectWithNotification,
    highPriorityThreshold,
    rulePriority,
    vacancyId,
    onSaveSuccess,
    t,
  ]);

  /**
   * Handle threshold input change with validation
   */
  const handleThresholdChange = useCallback(
    (field: 'min' | 'autoReject' | 'highPriority', value: string) => {
      const numValue = parseFloat(value);

      // Clear validation errors for this field
      setValidationErrors((prev) => prev.filter((e) => e.field !== field));

      // Only update if value is a valid number or empty
      if (value === '' || (!isNaN(numValue) && numValue >= 0 && numValue <= 100)) {
        if (field === 'min') {
          setMinScoreThreshold(numValue || 0);
        } else if (field === 'autoReject') {
          setAutoRejectThreshold(numValue || 0);
        } else if (field === 'highPriority') {
          setHighPriorityThreshold(numValue || 0);
        }
      }
    },
    []
  );

  /**
   * Get error message for a specific field
   */
  const getFieldError = useCallback((field: string): string | undefined => {
    return validationErrors.find((e) => e.field === field)?.message;
  }, [validationErrors]);

  const hasValidationErrors = validationErrors.length > 0;
  const hasChanges = existingRule
    ? minScoreThreshold !== existingRule.min_score_threshold ||
      autoRejectThreshold !== existingRule.auto_reject_threshold ||
      highPriorityThreshold !== existingRule.high_priority_threshold ||
      autoRejectWithNotification !== existingRule.auto_reject_with_notification ||
      rulePriority !== existingRule.rule_priority ||
      JSON.stringify(mustHaveSkills.sort()) !== JSON.stringify(existingRule.must_have_skills.sort())
    : true;

  return (
    <Stack spacing={2}>
      {/* Header Section */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="h6" fontWeight={600}>
              {existingRule
                ? t('screeningConfig.editTitle')
                : t('screeningConfig.createTitle')}
            </Typography>
          </Box>
          <Chip
            label={existingRule ? t('screeningConfig.mode.edit') : t('screeningConfig.mode.create')}
            size="small"
            color={existingRule ? 'info' : 'success'}
            variant="outlined"
          />
        </Box>
        <Divider sx={{ mb: 2 }} />

        {/* Info Alert */}
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            {t('screeningConfig.infoText')}
          </Typography>
        </Alert>
      </Paper>

      {/* Threshold Configuration */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          {t('screeningConfig.thresholds.title')}
        </Typography>

        <Grid container spacing={3}>
          {/* Auto-Reject Threshold */}
          <Grid item xs={12} sm={4}>
            <TextField
              label={t('screeningConfig.thresholds.autoRejectLabel')}
              type="number"
              fullWidth
              size="small"
              value={autoRejectThreshold}
              onChange={(e) => handleThresholdChange('autoReject', e.target.value)}
              error={!!getFieldError('autoRejectThreshold')}
              helperText={
                getFieldError('autoRejectThreshold') ||
                t('screeningConfig.thresholds.autoRejectHelper')
              }
              disabled={disabled || isSaving}
              inputProps={{ min: 0, max: 100, step: 1 }}
            />
          </Grid>

          {/* Minimum Score Threshold */}
          <Grid item xs={12} sm={4}>
            <TextField
              label={t('screeningConfig.thresholds.minScoreLabel')}
              type="number"
              fullWidth
              size="small"
              value={minScoreThreshold}
              onChange={(e) => handleThresholdChange('min', e.target.value)}
              error={!!getFieldError('minScoreThreshold')}
              helperText={
                getFieldError('minScoreThreshold') ||
                t('screeningConfig.thresholds.minScoreHelper')
              }
              disabled={disabled || isSaving}
              inputProps={{ min: 0, max: 100, step: 1 }}
            />
          </Grid>

          {/* High Priority Threshold */}
          <Grid item xs={12} sm={4}>
            <TextField
              label={t('screeningConfig.thresholds.highPriorityLabel')}
              type="number"
              fullWidth
              size="small"
              value={highPriorityThreshold}
              onChange={(e) => handleThresholdChange('highPriority', e.target.value)}
              error={!!getFieldError('highPriorityThreshold')}
              helperText={
                getFieldError('highPriorityThreshold') ||
                t('screeningConfig.thresholds.highPriorityHelper')
              }
              disabled={disabled || isSaving}
              inputProps={{ min: 0, max: 100, step: 1 }}
            />
          </Grid>
        </Grid>

        {/* Validation Errors */}
        {hasValidationErrors && (
          <Alert severity="error" sx={{ mt: 2 }}>
            <Typography variant="body2" fontWeight={600}>
              {t('screeningConfig.validation.header')}:
            </Typography>
            <Box component="ul" sx={{ pl: 2, mt: 1, mb: 0 }}>
              {validationErrors.map((err, idx) => (
                <Typography component="li" variant="body2" key={idx}>
                  {err.message}
                </Typography>
              ))}
            </Box>
          </Alert>
        )}
      </Paper>

      {/* Must-Have Skills */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          {t('screeningConfig.skills.title')}
        </Typography>

        <Autocomplete
          multiple
          freeSolo
          options={[]}
          value={mustHaveSkills}
          onChange={(_event, newValue) => {
            setMustHaveSkills(newValue);
            setValidationErrors((prev) => prev.filter((e) => e.field !== 'mustHaveSkills'));
          }}
          renderTags={(value, getTagProps) =>
            value.map((option, index) => (
              <Chip
                label={option}
                {...getTagProps({ index })}
                key={option}
                size="small"
              />
            ))
          }
          renderInput={(params) => (
            <TextField
              {...params}
              variant="outlined"
              label={t('screeningConfig.skills.label')}
              placeholder={t('screeningConfig.skills.placeholder')}
              helperText={t('screeningConfig.skills.helper')}
              size="small"
            />
          )}
          disabled={disabled || isSaving}
        />
      </Paper>

      {/* Additional Settings */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          {t('screeningConfig.settings.title')}
        </Typography>

        <Stack spacing={2}>
          {/* Auto-Reject with Notification */}
          <FormControlLabel
            control={
              <Switch
                checked={autoRejectWithNotification}
                onChange={(e) => setAutoRejectWithNotification(e.target.checked)}
                disabled={disabled || isSaving}
                color="warning"
              />
            }
            label={
              <Box>
                <Typography variant="body2" fontWeight={500}>
                  {t('screeningConfig.settings.autoRejectLabel')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('screeningConfig.settings.autoRejectHelper')}
                </Typography>
              </Box>
            }
          />

          <Divider />

          {/* Rule Priority */}
          <TextField
            label={t('screeningConfig.settings.priorityLabel')}
            type="number"
            fullWidth
            size="small"
            value={rulePriority}
            onChange={(e) => {
              const value = parseFloat(e.target.value);
              setRulePriority(!isNaN(value) && value >= 0 ? value : 0);
              setValidationErrors((prev) => prev.filter((err) => err.field !== 'rulePriority'));
            }}
            error={!!getFieldError('rulePriority')}
            helperText={
              getFieldError('rulePriority') ||
              t('screeningConfig.settings.priorityHelper')
            }
            disabled={disabled || isSaving}
            inputProps={{ min: 0, step: 1 }}
          />
        </Stack>
      </Paper>

      {/* Success Alert */}
      <Alert
        severity="success"
        sx={{ display: success ? 'flex' : 'none' }}
      >
        <Typography variant="body2">
          {t('screeningConfig.success.saved')}
        </Typography>
      </Alert>

      {/* Error Alert */}
      <Alert
        severity="error"
        sx={{ display: error ? 'flex' : 'none' }}
      >
        <Typography variant="body2">{error}</Typography>
      </Alert>

      {/* Save Button */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={disabled || isSaving || !hasChanges}
          fullWidth
          size="large"
          startIcon={isSaving ? <CircularProgress size={20} /> : null}
          sx={{ height: 48 }}
        >
          {isSaving
            ? t('screeningConfig.buttons.saving')
            : existingRule
              ? t('screeningConfig.buttons.update')
              : t('screeningConfig.buttons.create')
          }
        </Button>
      </Paper>
    </Stack>
  );
};

export default ScreeningConfig;
