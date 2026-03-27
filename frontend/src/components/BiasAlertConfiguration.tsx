import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  AlertTitle,
  Stack,
  Grid,
  Card,
  CardContent,
  CardActions,
  Switch,
  FormControlLabel,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Chip,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { biasAlertConfig } from '@/api/biasAlertConfig';
import type {
  BiasAlertConfig,
  BiasAlertConfigCreate,
  BiasAlertConfigUpdate,
} from '@/api/biasAlertConfig';

/**
 * BiasAlertConfiguration Component Props
 */
interface BiasAlertConfigurationProps {
  /** Optional organization ID for filtering */
  organizationId?: string;
}

/**
 * Get severity color based on level
 */
function getSeverityColor(severity: string): 'error' | 'warning' | 'info' | 'success' {
  switch (severity.toLowerCase()) {
    case 'critical':
      return 'error';
    case 'high':
      return 'error';
    case 'medium':
      return 'warning';
    case 'low':
      return 'info';
    default:
      return 'info';
  }
}

/**
 * Get severity icon
 */
function getSeverityIcon(severity: string) {
  switch (severity.toLowerCase()) {
    case 'critical':
      return <ErrorIcon fontSize="small" />;
    case 'high':
      return <WarningIcon fontSize="small" />;
    case 'medium':
      return <InfoIcon fontSize="small" />;
    case 'low':
      return <CheckIcon fontSize="small" />;
    default:
      return <InfoIcon fontSize="small" />;
  }
}

/**
 * Default form values for new configuration
 */
const DEFAULT_FORM_VALUES: BiasAlertConfigCreate = {
  alert_type: 'disparate_impact',
  metric_name: '',
  threshold_value: 0.8,
  comparison_operator: 'less_than',
  severity_level: 'medium',
  is_enabled: true,
  notification_enabled: true,
  alert_frequency: 'immediate',
  cooldown_period_hours: 24,
  auto_acknowledge: false,
};

/**
 * BiasAlertConfiguration Component
 *
 * Provides an admin interface for managing bias alert configurations.
 * Allows creating, editing, and deleting alert threshold settings.
 *
 * Features:
 * - List all bias alert configurations
 * - Create new configurations with customizable thresholds
 * - Edit existing configurations
 * - Enable/disable configurations
 * - Delete configurations
 * - Real-time validation
 *
 * @example
 * ```tsx
 * <BiasAlertConfiguration />
 * ```
 *
 * @example
 * ```tsx
 * <BiasAlertConfiguration organizationId="org-123" />
 * ```
 */
const BiasAlertConfiguration: React.FC<BiasAlertConfigurationProps> = ({
  organizationId,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [configs, setConfigs] = useState<BiasAlertConfig[]>([]);
  const [totalCount, setTotalCount] = useState(0);

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<BiasAlertConfig | null>(null);
  const [formValues, setFormValues] = useState<BiasAlertConfigCreate | BiasAlertConfigUpdate>(
    DEFAULT_FORM_VALUES
  );
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  /**
   * Fetch configurations from backend
   */
  const fetchConfigs = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await biasAlertConfig.getConfigs({
        organization_id: organizationId,
        limit: 100,
      });

      setConfigs(data.configs);
      setTotalCount(data.total_count);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load bias alert configurations';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, [organizationId]);

  /**
   * Validate form values
   */
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formValues.metric_name || formValues.metric_name.trim() === '') {
      errors.metric_name = 'Metric name is required';
    }

    if (
      formValues.threshold_value === undefined ||
      formValues.threshold_value < 0 ||
      formValues.threshold_value > 1
    ) {
      errors.threshold_value = 'Threshold must be between 0 and 1';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Handle opening create dialog
   */
  const handleCreate = () => {
    setEditingConfig(null);
    setFormValues(DEFAULT_FORM_VALUES);
    setFormErrors({});
    setDialogOpen(true);
  };

  /**
   * Handle opening edit dialog
   */
  const handleEdit = (config: BiasAlertConfig) => {
    setEditingConfig(config);
    setFormValues({
      alert_type: config.alert_type,
      metric_name: config.metric_name,
      threshold_value: config.threshold_value,
      comparison_operator: config.comparison_operator,
      severity_level: config.severity_level,
      is_enabled: config.is_enabled,
      notification_enabled: config.notification_enabled,
      notification_recipients: config.notification_recipients,
      demographic_groups: config.demographic_groups,
      applies_to_vacancies: config.applies_to_vacancies,
      alert_frequency: config.alert_frequency,
      cooldown_period_hours: config.cooldown_period_hours,
      auto_acknowledge: config.auto_acknowledge,
      description: config.description,
      mitigation_recommendations: config.mitigation_recommendations,
    });
    setFormErrors({});
    setDialogOpen(true);
  };

  /**
   * Handle save (create or update)
   */
  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      setSaving(true);
      setError(null);

      if (editingConfig) {
        await biasAlertConfig.updateConfig(editingConfig.id, formValues);
      } else {
        await biasAlertConfig.createConfig(formValues as BiasAlertConfigCreate);
      }

      setDialogOpen(false);
      await fetchConfigs();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to save configuration';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  /**
   * Handle delete
   */
  const handleDelete = async (configId: string) => {
    if (!confirm('Are you sure you want to delete this configuration?')) {
      return;
    }

    try {
      setError(null);
      await biasAlertConfig.deleteConfig(configId);
      await fetchConfigs();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to delete configuration';
      setError(errorMessage);
    }
  };

  /**
   * Handle toggle enabled status
   */
  const handleToggleEnabled = async (config: BiasAlertConfig) => {
    try {
      setError(null);
      await biasAlertConfig.updateConfig(config.id, {
        is_enabled: !config.is_enabled,
      });
      await fetchConfigs();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to update configuration';
      setError(errorMessage);
    }
  };

  /**
   * Handle close dialog
   */
  const handleCloseDialog = () => {
    if (!saving) {
      setDialogOpen(false);
      setEditingConfig(null);
      setFormValues(DEFAULT_FORM_VALUES);
      setFormErrors({});
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          Loading bias alert configurations...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Bias Alert Configuration
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage alert thresholds for bias detection metrics
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchConfigs}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
            New Configuration
          </Button>
        </Stack>
      </Stack>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          <AlertTitle>Error</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Configurations List */}
      {configs.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No configurations found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create your first bias alert configuration to get started
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
            Create Configuration
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {configs.map((config) => (
            <Grid item xs={12} md={6} lg={4} key={config.id}>
              <Card>
                <CardContent>
                  <Stack spacing={2}>
                    {/* Header */}
                    <Stack direction="row" justifyContent="space-between" alignItems="start">
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          {config.metric_name}
                        </Typography>
                        <Chip
                          label={config.alert_type.replace('_', ' ')}
                          size="small"
                          sx={{ textTransform: 'capitalize' }}
                        />
                      </Box>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config.is_enabled}
                            onChange={() => handleToggleEnabled(config)}
                            color="primary"
                          />
                        }
                        label=""
                      />
                    </Stack>

                    <Divider />

                    {/* Threshold */}
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Threshold
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {config.comparison_operator.replace('_', ' ')}{' '}
                        {(config.threshold_value * 100).toFixed(1)}%
                      </Typography>
                    </Box>

                    {/* Severity */}
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Severity
                      </Typography>
                      <Stack direction="row" spacing={1} alignItems="center">
                        {getSeverityIcon(config.severity_level)}
                        <Chip
                          label={config.severity_level}
                          size="small"
                          color={getSeverityColor(config.severity_level)}
                          sx={{ textTransform: 'capitalize' }}
                        />
                      </Stack>
                    </Box>

                    {/* Notification */}
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Notifications
                      </Typography>
                      <Typography variant="body2">
                        {config.notification_enabled ? 'Enabled' : 'Disabled'}
                        {config.notification_enabled && config.notification_recipients && (
                          <Typography variant="caption" display="block" color="text.secondary">
                            {config.notification_recipients.length} recipient(s)
                          </Typography>
                        )}
                      </Typography>
                    </Box>

                    {/* Description */}
                    {config.description && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Description
                        </Typography>
                        <Typography variant="body2">{config.description}</Typography>
                      </Box>
                    )}
                  </Stack>
                </CardContent>

                <CardActions sx={{ justifyContent: 'flex-end', px: 2, pb: 2 }}>
                  <Tooltip title="Edit configuration">
                    <IconButton size="small" onClick={() => handleEdit(config)}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete configuration">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDelete(config.id)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { minHeight: '600px' },
        }}
      >
        <DialogTitle>
          {editingConfig ? 'Edit Configuration' : 'Create New Configuration'}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 2 }}>
            {/* Alert Type */}
            <FormControl fullWidth>
              <InputLabel>Alert Type</InputLabel>
              <Select
                value={formValues.alert_type || 'disparate_impact'}
                onChange={(e) =>
                  setFormValues({ ...formValues, alert_type: e.target.value })
                }
                label="Alert Type"
              >
                <MenuItem value="disparate_impact">Disparate Impact</MenuItem>
                <MenuItem value="statistical_parity">Statistical Parity</MenuItem>
                <MenuItem value="sample_size">Sample Size</MenuItem>
              </Select>
            </FormControl>

            {/* Metric Name */}
            <TextField
              label="Metric Name"
              value={formValues.metric_name || ''}
              onChange={(e) => setFormValues({ ...formValues, metric_name: e.target.value })}
              error={!!formErrors.metric_name}
              helperText={formErrors.metric_name}
              fullWidth
              required
            />

            {/* Threshold Value */}
            <TextField
              label="Threshold Value"
              type="number"
              value={formValues.threshold_value ?? 0.8}
              onChange={(e) =>
                setFormValues({ ...formValues, threshold_value: parseFloat(e.target.value) })
              }
              error={!!formErrors.threshold_value}
              helperText={formErrors.threshold_value || 'Value between 0 and 1'}
              inputProps={{ min: 0, max: 1, step: 0.01 }}
              fullWidth
              required
            />

            {/* Comparison Operator */}
            <FormControl fullWidth>
              <InputLabel>Comparison Operator</InputLabel>
              <Select
                value={formValues.comparison_operator || 'less_than'}
                onChange={(e) =>
                  setFormValues({ ...formValues, comparison_operator: e.target.value })
                }
                label="Comparison Operator"
              >
                <MenuItem value="less_than">Less Than</MenuItem>
                <MenuItem value="greater_than">Greater Than</MenuItem>
                <MenuItem value="equals">Equals</MenuItem>
                <MenuItem value="not_equals">Not Equals</MenuItem>
              </Select>
            </FormControl>

            {/* Severity Level */}
            <FormControl fullWidth>
              <InputLabel>Severity Level</InputLabel>
              <Select
                value={formValues.severity_level || 'medium'}
                onChange={(e) =>
                  setFormValues({ ...formValues, severity_level: e.target.value })
                }
                label="Severity Level"
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
              </Select>
            </FormControl>

            {/* Alert Frequency */}
            <FormControl fullWidth>
              <InputLabel>Alert Frequency</InputLabel>
              <Select
                value={formValues.alert_frequency || 'immediate'}
                onChange={(e) =>
                  setFormValues({ ...formValues, alert_frequency: e.target.value })
                }
                label="Alert Frequency"
              >
                <MenuItem value="immediate">Immediate</MenuItem>
                <MenuItem value="daily">Daily</MenuItem>
                <MenuItem value="weekly">Weekly</MenuItem>
              </Select>
            </FormControl>

            {/* Cooldown Period */}
            <TextField
              label="Cooldown Period (hours)"
              type="number"
              value={formValues.cooldown_period_hours ?? 24}
              onChange={(e) =>
                setFormValues({
                  ...formValues,
                  cooldown_period_hours: parseInt(e.target.value),
                })
              }
              helperText="Hours before same alert can re-trigger"
              inputProps={{ min: 1 }}
              fullWidth
            />

            {/* Switches */}
            <Stack spacing={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formValues.is_enabled ?? true}
                    onChange={(e) =>
                      setFormValues({ ...formValues, is_enabled: e.target.checked })
                    }
                  />
                }
                label="Enabled"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formValues.notification_enabled ?? true}
                    onChange={(e) =>
                      setFormValues({ ...formValues, notification_enabled: e.target.checked })
                    }
                  />
                }
                label="Send Notifications"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formValues.auto_acknowledge ?? false}
                    onChange={(e) =>
                      setFormValues({ ...formValues, auto_acknowledge: e.target.checked })
                    }
                  />
                }
                label="Auto Acknowledge"
              />
            </Stack>

            {/* Description */}
            <TextField
              label="Description"
              value={formValues.description || ''}
              onChange={(e) =>
                setFormValues({ ...formValues, description: e.target.value })
              }
              multiline
              rows={2}
              fullWidth
            />

            {/* Mitigation Recommendations */}
            <TextField
              label="Mitigation Recommendations"
              value={formValues.mitigation_recommendations || ''}
              onChange={(e) =>
                setFormValues({
                  ...formValues,
                  mitigation_recommendations: e.target.value,
                })
              }
              multiline
              rows={3}
              fullWidth
              helperText="Suggested actions when this alert is triggered"
            />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button
            onClick={handleCloseDialog}
            disabled={saving}
            startIcon={<CancelIcon />}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
          >
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BiasAlertConfiguration;
